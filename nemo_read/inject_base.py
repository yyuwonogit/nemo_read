"""Standardised injector framework — every mailbox-domain LEAP injector
must subclass `CanonicalInjector`. The framework owns every LEAP-side
rule that has burned us before (CLAUDE.md §A.15, §11.1, §11.2, §A.9,
§A.10, etc.). Each sector contributes only the domain-unique pieces
via narrow override hooks.

Why this exists: prior to 2026-05-17 each sector had its own injector
script with copy-pasted COM code. The Interp() separator bug in fossil
(CLAUDE.md §A.15) was possible because every injector had its own
`var.Expression = expr` site and no enforced chokepoint. This module
seals the chokepoints so the next sector can't repeat that mistake.

# Architecture

Three categories of method:

1. **Sealed primitives** (runtime-enforced) — subclasses cannot
   override these. Any attempt raises TypeError at class definition.
   These are the bug-prevention surfaces:
     - `_set_expression()` — the only sanctioned `Variable.Expression =`
     - `_preflight_csv()` — the Interp-separator + placeholder scan
     - `_assert_area_lock()` — area drift detection (§11.1)
     - `_assert_scenario_lock()` — scenario drift detection (§A.9)

2. **Open hooks** — designed for subclass customisation. Default
   implementations match the most-common shape; override only for
   genuine sector variation.
     - `filter_rows(rows, args)` — domain row filtering
     - `group_by_region(rows)` — region iteration strategy
     - `extra_csv_validators()` — additional pre-flight checks
     - `extra_cli_args(parser)` — sector-specific CLI flags
     - `is_placeholder_row(row)` — placeholder detection (Stage 5)

3. **Default template** — `run()` orchestrates the standard loop.
   A subclass can override `run()` entirely if its flow is unusual
   (e.g. power's 3-cache grouping needs custom cache rebuilds), but
   it MUST still call the sealed primitives. The pytest regression
   in `test_inject_base.py` scans for any `\\.Expression\\s*=` site
   outside this module — a subclass that writes Expression directly
   fails CI.

# Minimum viable subclass

    from nemo_read.inject_base import CanonicalInjector

    class MySectorInjector(CanonicalInjector):
        SECTOR_NAME = "mysector"
        DEFAULT_CSV = Path(__file__).parent / "canonical_leap_inputs.csv"

        def filter_rows(self, rows, args):
            return [r for r in rows if not r["branch"].startswith("TBD\\\\")]

    if __name__ == "__main__":
        raise SystemExit(MySectorInjector().run())

That's ~10 lines of sector-specific code; everything else (CSV
pre-flight, area lock, COM safe-set, dry-run, placeholder gate,
readback hook, summary) comes free.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from nemo_read._heartbeat import HeartbeatLogger
from nemo_read._leap_com import (
    LeapTreeCache,
    LeapRegionalDecimalError,
    assert_leap_decimal_is_period,
    compare_expressions,
    dispatch_leap,
    safe_expression,
    safe_set_expression,
    validate_canonical_csv_expressions,
)


_PLACEHOLDER_NOTE_PREFIX = "PLACEHOLDER (Stage 5"

# Sub-national process-node variants are REGION-LOCKED (CLAUDE.md §A.21, canon
# anatomy §1.1): a `_MY*` node exists only in Malaysia, a `_ID*` node only in
# Indonesia. Authoring a value for one in any other AMS is a data error — the
# branch is inert there (Node=0 everywhere but its home region).
NODE_REGION_LOCK = {
    re.compile(r"_MY(PE|SB|SR)$"): "Malaysia",
    re.compile(r"_ID(JW|SA|KA|East)$"): "Indonesia",
}

# §A.23 — the complement of the node lock: for a node-decomposed family, the
# UN-SUFFIXED base branch is NOT an authoring slot in the decomposed home
# region. The base branch exists in the global tree (§A.22 — structure is
# region-invariant) but the home region's fleet lives exclusively on its
# node variants; LEAP refuses a base-branch write under that region's view
# ("no branch X in <region>" — live-confirmed 2026-07-07 on Biogas +
# Geothermal Flash in Indonesia, aeo9_v0.69 sendback inject).
# Derivation (2026-07-07): family has `_ID*`/`_MY*` variants in its home
# region's own Export-Expressions walk (LEAP Input Transformation
# [Indonesia].xlsx, aeo9_v0.67) AND the base branch is absent from that same
# walk. Malaysia keeps base `Gas Turbine` (present in its walk — only the
# MYPE node splits out), hence it is NOT in the Malaysia set.
_CEGEN_PROCESSES = (
    "Centralized Electricity Generation" + chr(92) + "Processes" + chr(92)
)
BASE_BRANCH_NODE_ONLY = {
    "Indonesia": frozenset({
        "Biogas", "Biomass Other", "Coal Subcritical", "Diesel",
        "Gas Combined Cycle", "Gas Engine", "Gas Turbine",
        "Geothermal Flash", "Large Hydro", "Small Hydro", "Solar PV",
        "Unmet Load", "Wind Onshore",
    }),
    "Malaysia": frozenset({
        "Biomass Other", "Coal Subcritical", "Diesel", "Gas Combined Cycle",
        "Large Hydro", "Nuclear LWR", "Nuclear SFR", "Nuclear SMR",
        "Solar PV", "Unmet Load", "Wind Onshore",
    }),
}
_REGION_COLS = ("region", "ams", "Region", "AMS")
# Third shape added 2026-07-05: export-style dumps and raw team drops carry the
# full path in `branch_path` / `Branch Path`. Before that, such files were
# silently SKIPPED (nc=None -> []) — 18,943 wrong-region rows across 5 files
# passed the CI tripwire unseen (structural-uniformity sweep finding).
_NODE_COLS = ("node", "branch", "branch_path", "Node", "Branch", "Branch Path")
# Region-deduplicated reference dumps collapse region-uniform rows to
# "ALL (12 regions)". Such a row is the un-overridden inheritance default, not
# a per-country authoring — the misfiled-data signal is SPECIFIC wrong-region
# rows. ALL-rows are therefore skipped, not flagged.
_ALL_REGIONS_RE = re.compile(r"^ALL\s*\(")


def find_region_lock_violations(csv_path) -> list[tuple[int, str, str, str]]:
    """Rows violating the §A.21 node lock OR the §A.23 base-branch lock.

    Class 1 (§A.21): a region-locked node-variant authored in the wrong AMS.
    Scans EVERY component of the branch/node path — a `_MY*`/`_ID*` variant
    is region-locked whether it is the leaf (process-node row) or an
    ancestor (e.g. `…\\Processes\\Coal Subcritical_MYPE\\Feedstock Fuels\\
    Coal Bituminous\\Carbon Dioxide`, a sub-branch row).

    Class 2 (§A.23): the UN-SUFFIXED base branch of a node-decomposed family
    authored FOR the decomposed home region itself (e.g. an Indonesia row on
    `…Centralized Electricity Generation\\Processes\\Biogas` — Indonesia's
    fleet lives only on `Biogas_ID*`; LEAP refuses the base write). Anchored
    to the Centralized-generation Processes path (path shapes) or the bare
    node name (wide shape) so fuel branches sharing the name (`Resources\\
    …\\Diesel`) are NOT flagged. Rows already scoped to a node variant are
    exempt from class 2 (their sub-branches may legitimately repeat the
    family name, e.g. `Small Hydro_IDJW\\Feedstock Fuels\\Small Hydro`).

    Handles all three inject/handover CSV shapes: long (`ams`/`branch`), wide
    (`region`/`node`), and export-style (`region`/`branch_path`, incl. the
    `Branch Path` header raw team drops use; BOM-tolerant). Rows whose region
    is the dedup bucket `ALL (N regions)` are skipped (uniform inheritance
    default, not a per-country authoring). Returns (row_number, matched_name,
    region, home_or_correct_target) per violating row; empty list = clean.
    """
    bs = chr(92)
    # utf-8-sig: raw team drops ship with a UTF-8 BOM that would otherwise
    # mangle the first fieldname ("\\ufeffBranch Path") and skip the file.
    with open(csv_path, encoding="utf-8-sig") as fh:
        rdr = csv.DictReader(fh)
        hdr = rdr.fieldnames or []
        rc = next((c for c in _REGION_COLS if c in hdr), None)
        nc = next((c for c in _NODE_COLS if c in hdr), None)
        if not rc or not nc:
            return []
        wide = nc in ("node", "Node")
        out: list[tuple[int, str, str, str]] = []
        for i, row in enumerate(rdr, start=2):  # header is row 1
            region = (row.get(rc) or "").strip()
            if _ALL_REGIONS_RE.match(region):
                continue
            path = (row.get(nc) or "").strip()
            variant_scoped = False
            for comp in path.split(bs):
                comp = comp.strip()
                hit = next((home for pat, home in NODE_REGION_LOCK.items()
                            if pat.search(comp)), None)
                if hit is not None:
                    variant_scoped = True
                    if region != hit:
                        out.append((i, comp, region, hit))
                    break  # one variant component per path
            if variant_scoped:
                continue
            locked = BASE_BRANCH_NODE_ONLY.get(region)
            if not locked:
                continue
            if wide:
                base = path
            else:
                k = path.find(_CEGEN_PROCESSES)
                if k < 0:
                    continue
                base = path[k + len(_CEGEN_PROCESSES):].split(bs)[0].strip()
            if base in locked:
                suffix = "_ID*" if region == "Indonesia" else "_MY*"
                out.append((i, base, region, f"{base}{suffix} nodes"))
    return out


_YEARVAL_RE = re.compile(r"\b(19\d\d|20\d\d)\s*,\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")


def _year_pairs(expr: str) -> list[tuple[int, float]]:
    """Explicit (year, value) pairs in an expression's comment-stripped body.
    Symbolic anchors (`FirstScenarioYear, 0`) are naturally excluded."""
    return [(int(y), float(v))
            for y, v in _YEARVAL_RE.findall(expr.split("?", 1)[0])]


def find_zero_existing_capacity_conflicts(csv_path) -> list[tuple[int, str, str, int, float]]:
    """§11.2b tripwire: `Existing Capacity = 0` in a year where the same
    branch's `Historical Production` is non-zero.

    LEAP halts the calc on this combination ("Output in timeslice N is
    non-zero but zero capacity is available") — burned 2026-05-05 (Thailand
    Wind Onshore) and again 2026-07-09 (Malaysia Diesel_MYPE 2021, Biomass
    Other_MYSR 2023-24; modeller had to hand-delete the zero points in the
    engine). Flags DEFINITE conflicts only: both variables present in the
    same CSV for the same (region, branch, scenario), EC has an explicit
    year→0 point, and HP linearly interpolated at that year exceeds 1e-6.
    EC-zero years with no HP row in the payload are NOT flagged (unknown is
    not a conflict). Returns (ec_row_number, region, branch_leaf, year,
    hp_value_at_year); empty list = clean.
    """
    bs = chr(92)
    with open(csv_path, encoding="utf-8-sig") as fh:
        rdr = csv.DictReader(fh)
        hdr = rdr.fieldnames or []
        rc = next((c for c in _REGION_COLS if c in hdr), None)
        nc = next((c for c in _NODE_COLS if c in hdr), None)
        vc = next((c for c in ("variable", "Variable") if c in hdr), None)
        ec_col = next((c for c in ("expression", "Expression") if c in hdr), None)
        sc = next((c for c in ("scenario", "Scenario") if c in hdr), None)
        if not (rc and nc and vc and ec_col):
            return []
        ec, hp = {}, {}
        for i, row in enumerate(rdr, start=2):
            var = (row.get(vc) or "").strip()
            if var not in ("Existing Capacity", "Historical Production"):
                continue
            lf = (row.get(nc) or "").rstrip(bs).split(bs)[-1].strip()
            key = ((row.get(rc) or "").strip(), lf,
                   (row.get(sc) or "").strip() if sc else "")
            pairs = _year_pairs(row.get(ec_col) or "")
            if not pairs:
                continue
            (ec if var == "Existing Capacity" else hp)[key] = (i, pairs)
    def hp_at(pairs, y):
        if y <= pairs[0][0]:
            return pairs[0][1] if y == pairs[0][0] else None
        if y >= pairs[-1][0]:
            return pairs[-1][1]
        for (y1, v1), (y2, v2) in zip(pairs, pairs[1:]):
            if y1 <= y <= y2:
                return v1 + (v2 - v1) * (y - y1) / (y2 - y1)
        return None
    out = []
    for key, (row_no, pairs) in ec.items():
        if key not in hp:
            continue
        _, hpp = hp[key]
        for y, v in pairs:
            if v == 0:
                h = hp_at(sorted(hpp), y)
                if h is not None and h > 1e-6:
                    out.append((row_no, key[0], key[1], y, round(h, 3)))
    return out


class InjectorSealError(TypeError):
    """Raised at class definition when a subclass overrides a sealed method."""


class CanonicalInjector:
    """Base class for every mailbox-domain LEAP injector.

    Subclass and override the open hooks. The sealed primitives are
    enforced at class-definition time via `__init_subclass__`.
    """

    # ---- subclass configuration (override as class attributes) ----
    SECTOR_NAME: str = "unknown"
    DEFAULT_CSV: Path | None = None
    EXPECT_AREA: str | None = None  # if set, run() refuses to start unless ActiveArea matches
    REQUIRE_EXPECT_AREA: bool = False  # if True, --expect-area is mandatory

    # v0.7.0 — Timor Leste supplement CSV (§A.18).
    # Path to a sibling CSV containing ONLY Timor Leste rows (same schema
    # as the main canonical). Loaded and concatenated when
    # --include-timor-leste is passed; ignored on --exclude-timor-leste.
    # Default location: <main canonical dir>/timor_leste_supplement.csv.
    # Subclass can override to a custom path. Per the §A.18 CI tripwire,
    # this file MUST exist (or the subclass MUST set
    # TIMOR_LESTE_SUPPLEMENT_NOT_APPLICABLE = True to opt out).
    TIMOR_LESTE_SUPPLEMENT: Path | None = None
    TIMOR_LESTE_SUPPLEMENT_NOT_APPLICABLE: bool = False

    # ---- sealed-method registry (runtime-enforced) ----
    _SEALED = frozenset({
        "_set_expression",
        "_preflight_csv",
        "_assert_area_lock",
        "_assert_scenario_lock",
        "__init_subclass__",
    })

    def __init_subclass__(cls, **kwargs):
        """Reject any subclass that overrides a sealed method."""
        super().__init_subclass__(**kwargs)
        for name in cls._SEALED:
            base_attr = CanonicalInjector.__dict__.get(name)
            sub_attr = cls.__dict__.get(name)
            if sub_attr is not None and sub_attr is not base_attr:
                raise InjectorSealError(
                    f"{cls.__name__} cannot override sealed method "
                    f"{name!r}. These methods own the LEAP-side bug-"
                    f"prevention rules (CLAUDE.md §A.15, §11.1, §A.9). "
                    f"Use an open hook instead — see inject_base.py "
                    f"docstring for the list."
                )

    # ===================================================================
    # SEALED PRIMITIVES — do not override
    # ===================================================================

    def _set_expression(self, variable, expr: str) -> str:
        """The sole sanctioned site for writing `Variable.Expression`.

        Routes through `safe_set_expression` which normalises the
        Interp separator (§A.15) and asserts canonical form before
        the COM write. Returns the actually-committed expression.
        """
        return safe_set_expression(variable, expr)

    def _preflight_csv(self, csv_path: Path) -> list[str]:
        """Pre-flight scan — refuses to start the run if any forbidden
        Interp() form is present. Subclasses can add additional
        validators via `extra_csv_validators()`.

        Returns a list of human-readable error strings; empty list means
        the CSV is clean.
        """
        errors: list[str] = []

        # §A.15 — forbidden semicolon Interp() form
        violations = validate_canonical_csv_expressions(csv_path)
        if violations:
            errors.append(
                f"{len(violations)} row(s) contain Interp() with forbidden "
                f"';' list-separator (CLAUDE.md §A.15). First: row "
                f"{violations[0][0]}: {violations[0][1][:90]}..."
            )

        # §11.2b — Existing Capacity zero-year vs non-zero Historical Production
        zc = find_zero_existing_capacity_conflicts(csv_path)
        if zc:
            errors.append(
                f"{len(zc)} Existing-Capacity zero-year(s) conflict with "
                f"non-zero Historical Production (§11.2b — LEAP halts the "
                f"calc on this). First: row {zc[0][0]}: {zc[0][2]} in "
                f"{zc[0][1]}, year {zc[0][3]} (HP={zc[0][4]}). Remove the "
                f"zero point or author real capacity/zero the HP."
            )

        # §A.21 node lock + §A.23 base-branch lock
        rl = find_region_lock_violations(csv_path)
        if rl:
            errors.append(
                f"{len(rl)} row(s) violate the region/node authoring locks "
                f"(CLAUDE.md §A.21 node-variant-in-wrong-AMS or §A.23 "
                f"base-branch-in-decomposed-home-region). First: row "
                f"{rl[0][0]}: {rl[0][1]} in {rl[0][2]} (belongs only to "
                f"{rl[0][3]}). Remove these rows from the canonical (see "
                f"find_region_lock_violations)."
            )

        # Subclass-contributed validators
        for validator in self.extra_csv_validators():
            sub_errors = validator(csv_path)
            if sub_errors:
                errors.extend(sub_errors)

        return errors

    def _assert_area_lock(self, leap, expected: str | None) -> None:
        """Abort if `leap.ActiveArea.Name` doesn't match `expected`.

        Catches the §11.1 multi-area trap where ActiveScenario set
        flips areas. Always pass `--expect-area` from CLI; if EXPECT_AREA
        is also set at class level, both must agree.
        """
        actual = leap.ActiveArea.Name
        target = expected or self.EXPECT_AREA
        if target is None:
            return  # subclass opted out — fine, just no enforcement
        if actual != target:
            raise SystemExit(
                f"[{self.SECTOR_NAME}] ActiveArea is {actual!r}, expected "
                f"{target!r}. Aborting (§11.1 area-drift trap). Confirm "
                f"the right area is open in LEAP and re-run."
            )

    def _assert_scenario_lock(self, leap, expected: str | None) -> None:
        """Abort if `leap.ActiveScenario.Name` doesn't match `expected`.

        Per §A.9 — every COM operation must confirm scenario state.
        """
        if expected is None:
            return
        actual = leap.ActiveScenario.Name
        if actual != expected:
            raise SystemExit(
                f"[{self.SECTOR_NAME}] ActiveScenario is {actual!r}, "
                f"expected {expected!r}. Aborting (§A.9 scenario-drift)."
            )

    # ===================================================================
    # OPEN HOOKS — override these in subclasses
    # ===================================================================

    def filter_rows(self, rows: list[dict], args: argparse.Namespace) -> list[dict]:
        """Domain-specific row filtering. Default: no filter."""
        return rows

    def group_by_region(self, rows: list[dict]) -> dict[str, list[dict]]:
        """Group rows by LEAP region for the ActiveRegion loop.

        Default: group by `row["ams"]` column (one ActiveRegion set
        per AMS). Power overrides this for its 3-cache grouping.
        """
        grouped: dict[str, list[dict]] = {}
        for r in rows:
            grouped.setdefault(r["ams"], []).append(r)
        return grouped

    def extra_csv_validators(self) -> list:
        """Return a list of additional pre-flight CSV validators.

        Each validator is a callable `(csv_path: Path) -> list[str]`
        that returns human-readable error strings (empty = pass).
        Default: no extra validators.
        """
        return []

    def extra_cli_args(self, parser: argparse.ArgumentParser) -> None:
        """Subclass hook to add sector-specific CLI flags."""
        pass

    def is_placeholder_row(self, row: dict) -> bool:
        """Detect Stage-5 diagnostic placeholder rows.

        Default: matches if `row.get("note", "")` starts with the
        canonical sentinel prefix OR `data_confidence == "PLACEHOLDER"`.
        Subclasses can override for sector-specific patterns.
        """
        note = row.get("note") or ""
        confidence = row.get("data_confidence") or ""
        return (
            note.startswith(_PLACEHOLDER_NOTE_PREFIX)
            or confidence.strip().upper() == "PLACEHOLDER"
        )

    def cache_for_region(self, leap, region: str) -> LeapTreeCache | None:
        """Build a tree cache scoped to the given region.

        Default: sets `leap.ActiveRegion` to the named region, builds
        a fresh `LeapTreeCache`. Subclasses can override to reuse
        caches across region groups (power's 3-cache pattern).

        Returns None under `--blind` (the universal escape hatch) so
        the per-row push falls back to direct `leap.Branches(FullName)`
        lookup. Blind mode is REQUIRED for KA + Demand branches whose
        cached writes silently no-op (transport, 2026-05-20).
        """
        if getattr(self._args, "blind", False):
            return None
        if region:
            leap.ActiveRegion = leap.Regions(region)
        return LeapTreeCache(leap=leap)

    def before_push_row(self, leap, row: dict, args: argparse.Namespace) -> None:
        """Per-row hook fired just before COM lookup/write.

        Default: no-op. Power overrides this to set `leap.ActiveRegion`
        to the row's `ams` (because power groups rows by cache-region,
        not by row-region).
        """
        pass

    def post_push_verify(self, committed_rows: list[dict], leap) -> None:
        """Hook for sector-specific post-push verification. Default: no-op."""
        pass

    # ===================================================================
    # DEFAULT TEMPLATE — subclasses can override but must still call
    # the sealed primitives. The pytest regression scans for any
    # `\\.Expression\\s*=` outside _set_expression.
    # ===================================================================

    def build_arg_parser(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(
            prog=f"inject_{self.SECTOR_NAME}",
            description=(
                "Default flow: dry-run → confirm → real inject → readback, "
                "all in ONE COM session (CLAUDE.md §A.10). Use --dry-run-only "
                "to stop after dry-run; --yes to skip confirm; --no-readback "
                "to skip readback; --scenarios X,Y,Z to loop multiple scenarios "
                "in the same session."
            ),
        )
        default_csv = str(self.DEFAULT_CSV) if self.DEFAULT_CSV else None
        p.add_argument("--csv", default=default_csv,
                       help="Canonical CSV to inject")
        p.add_argument("--dry-run-only", "--dry-run", action="store_true",
                       help="Run only the dry-run phase, then exit. "
                            "Does NOT proceed to real inject.")
        p.add_argument("--skip-dry-run", action="store_true",
                       help="Skip Phase 1 dry-run entirely; go straight "
                            "to real inject. Use only after a prior run "
                            "has verified the same canonical's structural "
                            "validity. Saves ~25 min/scenario.")
        p.add_argument("--yes", "-y", action="store_true",
                       help="Skip the confirmation prompt between dry-run "
                            "and real inject. Required for non-interactive "
                            "runs. The dry-run still happens.")
        p.add_argument("--no-readback", action="store_true",
                       help="Skip the post-inject readback verification.")
        p.add_argument("--readback-rows-per-region", type=int, default=1,
                       help="How many representative rows to readback per "
                            "region after real inject (default 1).")
        p.add_argument("--scenario",
                       help="Single scenario to inject into. Equivalent to "
                            "--scenarios X.")
        p.add_argument("--scenarios", default="",
                       help="Comma-separated list of scenarios to loop "
                            "through IN THE SAME COM SESSION. Each scenario "
                            "gets its own dry-run → confirm → real → "
                            "readback cycle without disconnecting from "
                            "LEAP between scenarios.")
        p.add_argument("--expect-area", default=self.EXPECT_AREA,
                       help="Abort if leap.ActiveArea.Name doesn't match")
        p.add_argument("--expect-scenario",
                       help="Abort if leap.ActiveScenario.Name doesn't match")
        p.add_argument("--no-scenario-switch", action="store_true",
                       help="Don't touch ActiveScenario (use UI state)")
        # Blind mode is the STANDARD method (DEFAULT ON as of 2026-05-20)
        # — promoted to the base framework after the transport cycle proved
        # it, not a power-only special case. See the inject SOP
        # (docs/inject_sop.md) for the branch-structure decision matrix:
        # KA (`Key\...`) + Demand (`Demand\...`) branches REQUIRE blind —
        # the cached branch.Variable() path silently no-ops writes there.
        # Resources/Transformation/Process branches work cached or blind
        # (blind ~50x faster, no cache build). Opt out with --no-blind for
        # the rare case you need the tree cache (e.g. debugging a
        # branch_not_found that blind would hang on).
        p.add_argument("--blind", dest="blind", action="store_true",
                       default=True,
                       help="(DEFAULT ON) Skip the tree cache; look up each "
                            "branch via direct leap.Branches(FullName). "
                            "REQUIRED for KA + Demand branches (cached "
                            "writes silently no-op there). Hangs if a "
                            "FullName doesn't exist — ALWAYS pair with "
                            "--fail-fast.")
        p.add_argument("--no-blind", dest="blind", action="store_false",
                       help="Opt OUT of blind mode — build + use the tree "
                            "cache. Cleanly reports branch_not_found instead "
                            "of hanging, but cached writes SILENTLY NO-OP on "
                            "KA/Demand branches. Use only for "
                            "Resource/Process sectors when debugging.")
        p.add_argument("--placeholder-mode", action="store_true",
                       help="Allow Stage-5 placeholder rows through")
        p.add_argument("--fail-fast", action="store_true",
                       help="Exit non-zero on the first inject failure")
        p.add_argument("--filter-ams", default="",
                       help="Only push rows for these comma-separated AMS")
        p.add_argument("--filter-variable", default="",
                       help="Only push rows for this LEAP variable")
        # v0.7.0 — mandatory Timor Leste decision (CLAUDE.md §A.18).
        # One of these flags MUST be passed; injector refuses to start
        # otherwise. Forces explicit opt-in/opt-out of the 11th ASEAN
        # cohort member to prevent §A.11 1e12 Unlimited leakage.
        tl_group = p.add_mutually_exclusive_group()
        tl_group.add_argument(
            "--include-timor-leste", action="store_true",
            help="Include Timor Leste rows from "
                 "`timor_leste_supplement.csv` alongside the main "
                 "canonical. REQUIRED to inject without §A.11 1e12 "
                 "Unlimited leakage on Timor Leste's LEAP defaults.")
        tl_group.add_argument(
            "--exclude-timor-leste", action="store_true",
            help="Explicitly inject WITHOUT Timor Leste — main canonical "
                 "only. Use this when you've verified Timor Leste data "
                 "isn't needed for this run (e.g. ASEAN-10 study). "
                 "WARNING: §A.11 1e12 trap still applies to unauthored "
                 "Timor Leste regions in the LEAP area; this flag does "
                 "NOT make them safe — it just says you intentionally "
                 "chose not to push corrections.")
        self.extra_cli_args(p)
        return p

    def load_csv(self, csv_path: Path) -> list[dict]:
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    def apply_universal_filters(
        self, rows: list[dict], args: argparse.Namespace
    ) -> list[dict]:
        ams_filter = {a.strip() for a in args.filter_ams.split(",") if a.strip()}
        var_filter = args.filter_variable.strip()
        out = []
        for r in rows:
            if ams_filter and r.get("ams") not in ams_filter:
                continue
            if var_filter and r.get("variable") != var_filter:
                continue
            out.append(r)
        return out

    @staticmethod
    def _filter_rows_for_scenario(
        rows: list[dict], scenario_name: str,
    ) -> list[dict]:
        """Keep rows whose `scenario` column matches `scenario_name`
        OR is empty/missing (= applies to every scenario, the
        bioenergy/fossil/power semantics where one row inherits via
        LEAP's scenario inheritance).

        Added 2026-05-20 after the transport inject revealed that
        multi-scenario-tagged canonicals (one row per branch+ams+scenario)
        had ALL their rows pushed under every scenario iteration —
        last-writer-wins corruption on shared branches. Bioenergy/fossil
        canonicals have no `scenario` column at all, so every row passes
        through unchanged (the .get default is empty string).
        """
        out: list[dict] = []
        for r in rows:
            tag = (r.get("scenario") or "").strip()
            if not tag or tag == scenario_name:
                out.append(r)
        return out

    def split_placeholder_rows(
        self, rows: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        real, placeholder = [], []
        for r in rows:
            (placeholder if self.is_placeholder_row(r) else real).append(r)
        return real, placeholder

    def run(self, argv=None) -> int:
        """Standardised inject flow — ALL COM operations in ONE invocation
        (CLAUDE.md §A.10). Sequence:

            dispatch_leap (once)
            → area lock
            → for each scenario in --scenarios:
                  set ActiveScenario (verify drift)
                  → build region caches (reused across phases)
                  → DRY-RUN phase
                  → confirmation prompt (skipped if --yes)
                  → REAL INJECT phase
                  → READBACK verify (skipped if --no-readback)

        COM session stays open across all phases. The tree cache built
        in the dry-run is the same cache used by real-inject and
        readback. No restarts, no LEAP re-opens.

        Override only if your sector needs a fundamentally different
        control flow (e.g. power's 3-cache region grouping)."""
        # Windows-safe stdout/stderr: this framework prints box-drawing
        # chars and §A.x section markers (non-ASCII) which crash under
        # CP1252 on default Windows consoles. Reconfigure to UTF-8 once
        # here so every phase print() works regardless of locale.
        for _stream in (sys.stdout, sys.stderr):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, Exception):
                pass

        parser = self.build_arg_parser()
        args = parser.parse_args(argv)
        self._args = args

        if self.REQUIRE_EXPECT_AREA and not args.expect_area:
            print(f"[{self.SECTOR_NAME}] ERROR: --expect-area is required "
                  f"for this sector (CLAUDE.md §A.9).", file=sys.stderr)
            return 1

        # ---- v0.7.0 — Timor Leste decision (CLAUDE.md §A.18) ----
        if not self.TIMOR_LESTE_SUPPLEMENT_NOT_APPLICABLE:
            if not (args.include_timor_leste or args.exclude_timor_leste):
                print(
                    f"[{self.SECTOR_NAME}] REFUSED: must explicitly choose "
                    f"Timor Leste inclusion (CLAUDE.md §A.18).\n"
                    f"  Pass --include-timor-leste to push the supplement "
                    f"file alongside the main canonical,\n"
                    f"  OR --exclude-timor-leste to inject without Timor "
                    f"Leste (main canonical only).\n"
                    f"  Without one of these flags, the inject would "
                    f"silently miss Timor Leste's authoring and leave "
                    f"LEAP defaults (§A.11 1e12 Unlimited trap) in place.",
                    file=sys.stderr)
                return 8

        csv_path = Path(args.csv) if args.csv else self.DEFAULT_CSV
        if csv_path is None or not csv_path.exists():
            print(f"[{self.SECTOR_NAME}] ERROR: CSV not found: {csv_path}",
                  file=sys.stderr)
            return 1

        # ---- Pre-flight (sealed) ----
        errors = self._preflight_csv(csv_path)
        if errors:
            print(f"[{self.SECTOR_NAME}] REFUSED: pre-flight failed",
                  file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 2

        # ---- Load + filter ----
        rows = self.load_csv(csv_path)
        # v0.7.0 — merge Timor Leste supplement if --include-timor-leste
        if args.include_timor_leste and not self.TIMOR_LESTE_SUPPLEMENT_NOT_APPLICABLE:
            tl_path = self.TIMOR_LESTE_SUPPLEMENT
            if tl_path is None:
                tl_path = csv_path.parent / "timor_leste_supplement.csv"
            if not tl_path.exists():
                print(f"[{self.SECTOR_NAME}] REFUSED: --include-timor-leste "
                      f"passed but supplement not found at {tl_path}",
                      file=sys.stderr)
                return 9
            tl_rows = self.load_csv(tl_path)
            non_tl = [r for r in tl_rows if r.get("ams") != "Timor Leste"]
            if non_tl:
                print(f"[{self.SECTOR_NAME}] REFUSED: supplement {tl_path.name} "
                      f"contains {len(non_tl)} non-Timor-Leste row(s). The "
                      f"supplement must contain ONLY ams='Timor Leste' rows.",
                      file=sys.stderr)
                return 10
            rows.extend(tl_rows)
            print(f"[{self.SECTOR_NAME}] Merged {len(tl_rows)} Timor Leste "
                  f"row(s) from {tl_path.name} (§A.18 include)")
        elif args.exclude_timor_leste:
            # Defensive: warn if main canonical accidentally has TL rows
            tl_in_main = [r for r in rows if r.get("ams") == "Timor Leste"]
            if tl_in_main:
                print(f"[{self.SECTOR_NAME}] WARN: --exclude-timor-leste set "
                      f"but main canonical has {len(tl_in_main)} Timor Leste "
                      f"row(s). They will be SKIPPED. Move them to the "
                      f"supplement file if intended.")
                rows = [r for r in rows if r.get("ams") != "Timor Leste"]

        rows = self.apply_universal_filters(rows, args)
        rows = self.filter_rows(rows, args)
        if not rows:
            print(f"[{self.SECTOR_NAME}] no rows match filters; nothing to do.")
            return 0

        # ---- Placeholder gate ----
        real_rows, placeholders = self.split_placeholder_rows(rows)
        if placeholders and not args.placeholder_mode:
            print(f"[{self.SECTOR_NAME}] REFUSED: {len(placeholders)} "
                  f"placeholder row(s) present. Pass --placeholder-mode "
                  f"if this is a Stage-6 diagnostic run, or strip the "
                  f"placeholders from the canonical CSV.",
                  file=sys.stderr)
            return 3
        rows_to_push = placeholders if args.placeholder_mode else real_rows

        # ---- Resolve scenario list (multi-scenario in ONE COM session) ----
        scenario_list = self._resolve_scenarios(args)

        # ---- Heartbeat: §A.16 progress channel for long-running runs ----
        # Progress JSON lands next to the canonical CSV. The op_name
        # encodes sector + verb so multiple sectors don't collide.
        self._hb = HeartbeatLogger(
            op_name=f"inject_{self.SECTOR_NAME}",
            progress_dir=Path(csv_path).parent,
            interval_seconds=10.0,  # tighter than the 30s default so
            # stalls are visible faster (was throttling stdout to the
            # point the operator couldn't distinguish slow from hung)
        )

        # ---- COM dispatch ONCE (warm session across all phases) ----
        leap = dispatch_leap()
        self._assert_area_lock(leap, args.expect_area)
        initial_area = leap.ActiveArea.Name
        print(f"[{self.SECTOR_NAME}] ActiveArea (locked): {initial_area!r}")
        # CLAUDE.md §A.15 — hard guard: refuse to push if LEAP regional
        # decimal separator is comma. Comma-decimal storage produces
        # ambiguous Interp() round-trips that compare_expressions cannot
        # classify. Discovered 2026-05-20 (transport KA readback FAIL
        # was actually correct values stored under comma-decimal regional).
        try:
            assert_leap_decimal_is_period(leap, sector_label=self.SECTOR_NAME)
        except LeapRegionalDecimalError as exc:
            print(str(exc), file=sys.stderr)
            return 11
        print(f"[{self.SECTOR_NAME}] Will process {len(scenario_list)} "
              f"scenario(s) in ONE COM session: {scenario_list or '<current>'}")
        self._hb.tick(stage="com_dispatched", area=initial_area,
                      scenarios_total=len(scenario_list))

        any_failed = False
        scenarios_processed = 0
        try:
            for idx, scenario in enumerate(scenario_list, start=1):
                self._hb.tick(stage="scenario_start",
                              scenario=scenario or "<current>",
                              scenario_idx=f"{idx}/{len(scenario_list)}")
                rc = self._run_scenario_cycle(
                    leap, scenario, rows_to_push, args, csv_path)
                scenarios_processed = idx
                if rc != 0:
                    any_failed = True
                    if args.fail_fast:
                        print(f"[{self.SECTOR_NAME}] --fail-fast: aborting "
                              f"remaining scenarios.")
                        break

            print(f"\n[{self.SECTOR_NAME}] === ALL SCENARIOS DONE ===")
            return 1 if any_failed else 0
        finally:
            self._hb.finish({"any_failed": any_failed,
                             "scenarios_processed": scenarios_processed})

    def _resolve_scenarios(self, args) -> list[str | None]:
        """Build the ordered scenario list for this run.

        Precedence: --scenarios > --scenario > [None] (use current
        ActiveScenario, don't touch it).
        """
        if args.scenarios:
            return [s.strip() for s in args.scenarios.split(",") if s.strip()]
        if args.scenario:
            return [args.scenario]
        return [None]

    def _run_scenario_cycle(
        self, leap, scenario: str | None, rows: list[dict],
        args: argparse.Namespace, csv_path: Path,
    ) -> int:
        """One scenario's full cycle: set+lock → dry → confirm → real → readback.

        All within the already-warm COM session. Returns 0 on success,
        non-zero on any failure (CSV pre-flight failures, dry-run
        failures, user-declined confirmation, real-inject failures, or
        readback failures).
        """
        scen_label = scenario or "<current scenario>"
        print(f"\n[{self.SECTOR_NAME}] ╔═══ SCENARIO: {scen_label!r} ═══")

        # ---- Set + lock scenario ----
        if scenario and not args.no_scenario_switch:
            try:
                leap.ActiveScenario = leap.Scenarios(scenario)
            except Exception as exc:
                print(f"  ERROR: could not switch to scenario "
                      f"{scenario!r}: {exc}", file=sys.stderr)
                return 4
            # Re-verify area didn't drift after scenario set (§11.1 trap)
            self._assert_area_lock(leap, args.expect_area)
        if args.expect_scenario:
            self._assert_scenario_lock(leap, args.expect_scenario)
        actual_scen = leap.ActiveScenario.Name
        print(f"  ActiveScenario: {actual_scen!r}")

        # ---- Scenario-column row filter ----
        before_n = len(rows)
        rows = self._filter_rows_for_scenario(rows, actual_scen)
        if before_n != len(rows):
            print(f"  scenario-column filter: {before_n} -> {len(rows)} "
                  f"rows (kept untagged + scenario={actual_scen!r})")

        # ---- Build region caches ONCE; reused across dry + real phases ----
        groups = self.group_by_region(rows)
        print(f"  {len(rows)} rows across {len(groups)} region group(s)")
        caches: dict[str, LeapTreeCache | None] = {}
        for region in groups:
            caches[region] = self.cache_for_region(leap, region)

        # ---- Phase 1: DRY RUN (skippable via --skip-dry-run) ----
        if args.skip_dry_run:
            print(f"\n[{self.SECTOR_NAME}] ── Phase 1: DRY RUN — SKIPPED "
                  f"(per --skip-dry-run) ──")
            self._maybe_tick(stage="dry_run_skipped", scenario=scen_label)
            dry_counts, dry_failures = Counter(), []
        else:
            print(f"\n[{self.SECTOR_NAME}] ── Phase 1: DRY RUN ──")
            self._maybe_tick(stage="dry_run_start",
                             scenario=scen_label, regions=len(groups))
            dry_counts, dry_failures, _ = self._execute_phase(
                leap, groups, caches, args, dry_run=True)
            self._maybe_tick(stage="dry_run_done", scenario=scen_label,
                             dry_pushed=dry_counts.get("dry_run", 0),
                             dry_skipped=(
                                 dry_counts.get("branch_not_found", 0)
                                 + dry_counts.get("var_not_found", 0)
                                 + dry_counts.get("row_invalid", 0)))
        self._print_phase_summary("dry-run", dry_counts, dry_failures)
        dry_blocking = (
            dry_failures
            or dry_counts.get("branch_not_found", 0)
            or dry_counts.get("var_not_found", 0)
            or dry_counts.get("row_invalid", 0)
        )
        if dry_blocking:
            print(f"\n[{self.SECTOR_NAME}] DRY-RUN HAS FAILURES — refusing "
                  f"to proceed to real inject for scenario {scen_label!r}.")
            return 5

        if args.dry_run_only:
            print(f"\n[{self.SECTOR_NAME}] --dry-run-only: stopping after "
                  f"dry-run phase.")
            return 0

        # ---- Phase 2: CONFIRM ----
        if not args.yes:
            ok = self._prompt_yes_no(
                f"\n[{self.SECTOR_NAME}] Dry-run clean for {scen_label!r}. "
                f"Proceed with REAL inject? [y/N] ")
            if not ok:
                print(f"[{self.SECTOR_NAME}] User declined. Skipping real "
                      f"inject for {scen_label!r}. COM session stays open "
                      f"for other scenarios.")
                return 6

        # ---- Phase 3: REAL INJECT (warm cache from dry-run is reused) ----
        print(f"\n[{self.SECTOR_NAME}] ── Phase 3: REAL INJECT ──")
        self._maybe_tick(stage="real_inject_start", scenario=scen_label)
        real_counts, real_failures, committed = self._execute_phase(
            leap, groups, caches, args, dry_run=False)
        self._maybe_tick(stage="real_inject_done", scenario=scen_label,
                         pushed=real_counts.get("pushed", 0),
                         failed=len(real_failures))
        self._print_phase_summary("real-inject", real_counts, real_failures)
        self.post_push_verify(committed, leap)

        # ---- Phase 4: READBACK (warm session — no cache rebuild) ----
        if not args.no_readback and committed:
            print(f"\n[{self.SECTOR_NAME}] ── Phase 4: READBACK VERIFY ──")
            readback_ok = self.readback_verify(
                leap, committed,
                rows_per_region=args.readback_rows_per_region)
            if not readback_ok:
                print(f"[{self.SECTOR_NAME}] READBACK FAILED for "
                      f"{scen_label!r} (§A.15). Inject committed but "
                      f"verification did not pass.")
                return 7

        return 1 if real_failures else 0

    def _execute_phase(
        self, leap, groups: dict[str, list[dict]],
        caches: dict[str, LeapTreeCache | None],
        args: argparse.Namespace, dry_run: bool,
    ) -> tuple[Counter, list[tuple], list[dict]]:
        """Run one phase (dry or real) of the per-region inject loop.

        Returns (counts, failures, committed). The caches dict is shared
        with other phases — built once at scenario-cycle start, reused
        here verbatim. No COM disconnect or LEAP re-open between phases.
        """
        counts: Counter = Counter()
        failures: list = []
        committed: list[dict] = []
        # Snapshot dry_run on a shallow-copied args so _push_one sees it
        import copy as _copy
        phase_args = _copy.copy(args)
        phase_args.dry_run = dry_run
        for region_idx, (region, group_rows) in enumerate(groups.items(),
                                                          start=1):
            print(f"  --- region {region!r} ({len(group_rows)} rows) ---")
            # CRITICAL: set ActiveRegion at each region transition.
            # `cache_for_region` sets it during cache build, but after
            # the build loop the cache map is complete and ActiveRegion
            # is whatever the LAST built region was. Without this
            # re-set, every row's `var.Expression =` write goes to the
            # wrong region's slot — silent data corruption. Power
            # historically guarded this via a per-row `before_push_row`
            # override; making it default-on means every sector is
            # safe. See CLAUDE.md §A on "ActiveRegion drift in inject".
            #
            # A subclass's group key may be a GROUP LABEL, not a real
            # LEAP region (power's 3-cache 'Other' = the copper-plate
            # batch). Passing the label to `leap.Regions()` raises a
            # LEAP-side error dialog every run. Resolve to a real
            # region first: the key itself when it matches a row's ams
            # (default per-AMS grouping), else the group's first row
            # ams; per-row `before_push_row` hooks refine further.
            if region:
                row_regions = {(r.get("ams") or "").strip()
                               for r in group_rows}
                row_regions.discard("")
                target = (region if region in row_regions
                          else next(iter(sorted(row_regions)), None))
                if target:
                    try:
                        leap.ActiveRegion = leap.Regions(target)
                    except Exception as exc:
                        print(f"    WARN: could not set "
                              f"ActiveRegion={target!r}: {exc}")
            self._maybe_tick(
                stage=("dry_region" if dry_run else "real_region"),
                region=region,
                region_idx=f"{region_idx}/{len(groups)}",
                rows_in_region=len(group_rows),
                rows_written=len(committed),
            )
            cache = caches.get(region)
            for row_idx, r in enumerate(group_rows, start=1):
                self._push_one(leap, cache, r, phase_args,
                               counts, failures, committed)
                # Tick every 10 rows so a slow scenario still flows
                # and JSON state advances granularly enough that the
                # operator can see whether we're moving or stalled.
                if row_idx % 10 == 0:
                    self._maybe_tick(
                        stage=("dry_pushing" if dry_run else "real_pushing"),
                        region=region,
                        row_in_region=f"{row_idx}/{len(group_rows)}",
                        rows_written=len(committed),
                    )
        return counts, failures, committed

    def _print_phase_summary(
        self, phase_name: str, counts: Counter, failures: list,
    ) -> None:
        print(f"  [{phase_name}] {dict(counts)}")
        if failures:
            print(f"  [{phase_name}] {len(failures)} failure(s):")
            for r, msg in failures[:5]:
                print(f"    - {r.get('ams','?')} | {r.get('branch','?')} "
                      f". {r.get('variable','?')}: {msg}")

    def _maybe_tick(self, **context) -> None:
        """Tick the heartbeat if one is attached (set by run()).

        Subclasses that override `run()` and skip the HeartbeatLogger
        setup still inherit `_run_scenario_cycle` / `_execute_phase` —
        this no-op guard lets the ticks live in the hot path without
        forcing every caller to set up the logger.
        """
        hb = getattr(self, "_hb", None)
        if hb is not None:
            hb.tick(**context)

    def _prompt_yes_no(self, message: str) -> bool:
        """Ask the user; return True only on explicit 'y' / 'yes'.

        Non-interactive runs (no TTY): return False (safe default).
        """
        if not sys.stdin.isatty():
            print(f"{message} [non-interactive — defaulting NO; pass --yes "
                  f"to auto-proceed]")
            return False
        try:
            answer = input(message).strip().lower()
        except EOFError:
            return False
        return answer in ("y", "yes")

    def readback_verify(
        self, leap, committed: list[dict], rows_per_region: int = 1,
    ) -> bool:
        """Post-inject read-back on a representative sample.

        Picks the first `rows_per_region` rows from each region of
        `committed`, reads `Variable.Expression` back via COM, and
        compares against the row's authored expression. Same COM
        session as the inject — no cache rebuild, no LEAP re-open.

        NORMALISED matches (LEAP renormalised commas to periods on
        read-back, §A.15) are HARD FAIL — not soft pass.

        Returns True if every sample is EXACT, False on any
        NORMALISED or FAIL result.
        """
        if not committed:
            return True

        by_region: dict[str, list[dict]] = {}
        for row in committed:
            by_region.setdefault(row.get("ams", "?"), []).append(row)

        samples: list[dict] = []
        for region, rows in by_region.items():
            samples.extend(rows[:rows_per_region])

        print(f"  Verifying {len(samples)} representative row(s) "
              f"({rows_per_region} per region × {len(by_region)} region(s))")

        n_exact = n_norm = n_fail = 0
        for row in samples:
            ams = row.get("ams")
            branch_path = row.get("branch", "")
            var_name = row.get("variable", "")
            expected = row.get("expression", "")
            try:
                if ams:
                    leap.ActiveRegion = leap.Regions(ams)
                branch = leap.Branches(branch_path)
                if branch is None:
                    print(f"  [FAIL] {ams}|{branch_path}: branch is None")
                    n_fail += 1
                    continue
                var = branch.Variable(var_name)
                if var is None:
                    print(f"  [FAIL] {ams}|{branch_path}.{var_name}: var None")
                    n_fail += 1
                    continue
                actual = safe_expression(var)
            except Exception as exc:
                print(f"  [FAIL] {ams}|{branch_path}.{var_name}: {exc}")
                n_fail += 1
                continue

            verdict = compare_expressions(actual, expected)
            if verdict == "EXACT":
                n_exact += 1
                print(f"  [EXACT] {ams}|{var_name} on {branch_path}")
            elif verdict == "NORMALISED":
                # §A.15: hard fail. Inject committed wrong separator form.
                n_norm += 1
                print(f"  [NORM-FAIL] {ams}|{var_name} on {branch_path} — "
                      f"LEAP renormalised separator (§A.15 violation). "
                      f"actual={actual!r}")
            else:
                n_fail += 1
                print(f"  [FAIL] {ams}|{var_name} on {branch_path}")
                print(f"         actual:   {actual!r}")
                print(f"         expected: {expected!r}")

        print(f"  Readback summary: {n_exact} EXACT, {n_norm} NORMALISED, "
              f"{n_fail} FAIL")
        return n_norm == 0 and n_fail == 0

    def _push_one(
        self, leap, cache: LeapTreeCache, row: dict,
        args: argparse.Namespace, counts: Counter,
        failures: list, committed: list,
    ) -> None:
        # Per-row pre-hook (e.g. set ActiveRegion to row's ams)
        self.before_push_row(leap, row, args)

        branch_path = row.get("branch", "")
        var_name = row.get("variable", "")
        expr = row.get("expression", "")

        def _maybe_fail(reason: str) -> None:
            if args.fail_fast:
                raise SystemExit(
                    f"[{self.SECTOR_NAME}] FAIL-FAST: {reason}")

        if not branch_path or not var_name or expr == "":
            failures.append((row, "row missing branch/variable/expression"))
            counts["row_invalid"] += 1
            _maybe_fail(f"row_invalid for {row.get('ams','?')}")
            return

        try:
            idx = cache.fullname_to_idx.get(branch_path) if cache else None
        except Exception as exc:
            failures.append((row, f"cache lookup error: {exc}"))
            counts["cache_error"] += 1
            _maybe_fail(f"cache_error: {exc}")
            return
        if idx is None and cache is not None:
            counts["branch_not_found"] += 1
            print(f"     [SKIP] {branch_path}  — not in tree cache")
            _maybe_fail(f"branch_not_found: {branch_path}")
            return

        try:
            if cache is not None:
                branch = cache.branches.Item(idx)
            else:
                # Blind mode: direct FullName lookup (§11.1 — can hang)
                branch = leap.Branches(branch_path)
        except Exception as exc:
            failures.append((row, f"branch fetch error: {exc}"))
            counts["branch_error"] += 1
            _maybe_fail(f"branch_error: {exc}")
            return

        try:
            var = branch.Variable(var_name)
        except Exception as exc:
            failures.append((row, f"var lookup error: {exc}"))
            counts["var_lookup_failed"] += 1
            _maybe_fail(f"var_lookup_failed: {exc}")
            return
        if var is None:
            counts["var_not_found"] += 1
            print(f"     [SKIP] {branch_path} . {var_name!r} = None")
            _maybe_fail(f"var_not_found: {branch_path} . {var_name!r}")
            return

        if args.dry_run:
            preview = expr if len(expr) <= 70 else expr[:67] + "..."
            print(f"     [DRY] {branch_path} . {var_name!r} = {preview}")
            counts["dry_run"] += 1
            return

        try:
            actually_committed = self._set_expression(var, expr)
            counts["pushed"] += 1
            committed.append(row)
            preview = (actually_committed if len(actually_committed) <= 60
                       else actually_committed[:57] + "...")
            print(f"     [OK]  {branch_path} . {var_name!r} = {preview}")
        except Exception as exc:
            failures.append((row, f"Expression set failed: {exc}"))
            counts["set_failed"] += 1
            print(f"     [ERR] {branch_path} . {var_name!r}: {exc}")
            _maybe_fail(f"set_failed: {branch_path} . {var_name!r}")

