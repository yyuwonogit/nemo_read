"""LEAP-export → canonical CSV adapter for the power domain.

Power-side authoring CSVs come from LEAP exports (or hand-edited copies)
in the LEAP-export column shape:

    Branch Path, Variable, Scenario, Region, Scale, Units, Per..., Expression

`inject_to_leap.py` reads the canonical schema:

    ams, branch, variable, expression, unit, fuel, source, note,
    src_csv, domain, data_confidence, unit_audit

This script renames columns, drops `Base Template` rows (LEAP placeholder
region — see CLAUDE.md §11.1), and writes one `<src>_canonical.csv` per
input CSV next to the source.

Usage:

    python mailbox/power/build_canonical.py \\
        mailbox/power/20260507/ats_exo_formula.csv \\
        mailbox/power/20260507/bas_all_zero.csv

By default, output is `<src_stem>_canonical.csv` in the same directory.
Pass --out-dir to override.

The adapter is intentionally thin: it does NOT do unit conversion (power
authoring stays in LEAP-native units) and does NOT compute expressions
(the input CSV is the source of truth). It only reshapes columns and
filters Base Template.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

# Canonical schema expected by mailbox/bioenergy/inject_to_leap.py.
CANONICAL_FIELDS = [
    "ams", "branch", "variable", "expression", "unit",
    "fuel", "source", "note", "src_csv", "domain",
    "data_confidence", "unit_audit",
]

# LEAP-export column names → canonical column names.
COLUMN_MAP = {
    "Branch Path": "branch",
    "Variable": "variable",
    "Region": "ams",
    "Expression": "expression",
    "Units": "unit",
}

DROP_REGION = "Base Template"

# Subnational branches end with _ID<X>... (Indonesia) or _MY<X>... (Malaysia)
# on the leaf segment. They must only appear under the matching country.
# Branches without a subnational tag are country-level and apply to any
# region (validity is up to the LEAP tree to decide).
_SUBNATIONAL_RE = re.compile(r"_(ID|MY)[A-Za-z]+$")
_TAG_TO_COUNTRY = {"ID": "Indonesia", "MY": "Malaysia"}

# Branches a LEAP export sometimes carries that don't exist in
# `aeo9_v0.38_yy`'s Centralized Electricity Generation tree. Solar PV
# Rooftop is a Distributed-only tech (lives under
# `Transformation\Distributed Electricity Generation\Processes\…`), but
# LEAP-export sometimes emits rows on the Centralized path. Pushing
# these is wrong — drop in the adapter.
DROP_OFFTREE_BRANCHES = {
    # Solar PV Rooftop is Distributed-only (lives under
    # `Transformation\Distributed Electricity Generation\…`).
    "Transformation\\Centralized Electricity Generation\\Processes\\Solar PV Rooftop",
    # Unmet Load is country-level only — no subnational variants exist
    # in `_yy` for Indonesia (confirmed 2026-05-07 via UI inspection).
    # WARNING: blind direct-lookup returned [OK] on these branches —
    # LEAP COM appears to silently accept phantom-branch writes.
    "Transformation\\Centralized Electricity Generation\\Processes\\Unmet Load_IDEast",
    "Transformation\\Centralized Electricity Generation\\Processes\\Unmet Load_IDJW",
    "Transformation\\Centralized Electricity Generation\\Processes\\Unmet Load_IDKA",
    "Transformation\\Centralized Electricity Generation\\Processes\\Unmet Load_IDSA",
    # Unmet Load also doesn't exist as a Malaysia subnational
    # (confirmed 2026-05-07 — same phantom-branch trap).
    "Transformation\\Centralized Electricity Generation\\Processes\\Unmet Load_MYPE",
    "Transformation\\Centralized Electricity Generation\\Processes\\Unmet Load_MYSB",
    "Transformation\\Centralized Electricity Generation\\Processes\\Unmet Load_MYSR",
    # Gas Engine has no Malaysia subnational variants in `_yy` (confirmed
    # 2026-05-07 via UI). Same phantom-branch warning as Unmet Load.
    "Transformation\\Centralized Electricity Generation\\Processes\\Gas Engine_MYPE",
    "Transformation\\Centralized Electricity Generation\\Processes\\Gas Engine_MYSB",
    "Transformation\\Centralized Electricity Generation\\Processes\\Gas Engine_MYSR",
}

# Region-specific drops: branches that are valid country-level for some
# AMS but absent from `_yy` for the listed AMS. Different from
# DROP_OFFTREE_BRANCHES (which drops a branch globally) — these survive
# for other regions but get filtered when paired with the listed AMS.
DROP_BRANCHES_PER_REGION: dict[str, set[str]] = {
    "Indonesia": {
        # Country-level Unmet Load doesn't exist under Indonesia in
        # `_yy` either (confirmed 2026-05-07). Pair with the Unmet
        # Load_IDxx subnational drops in DROP_OFFTREE_BRANCHES — net
        # effect: no Unmet Load row of any shape lands on Indonesia.
        "Transformation\\Centralized Electricity Generation\\Processes\\Unmet Load",
    },
    "Malaysia": {
        # Unmet Load on Centralized doesn't exist under Malaysia in
        # `_yy` (confirmed 2026-05-07). Other AMS keep it.
        "Transformation\\Centralized Electricity Generation\\Processes\\Unmet Load",
    },
}


def _subnational_country(branch: str) -> str | None:
    """Return the country a subnational branch belongs under, or None
    if the branch is country-level (no `_ID*` / `_MY*` leaf suffix)."""
    leaf = branch.rsplit("\\", 1)[-1]
    m = _SUBNATIONAL_RE.search(leaf)
    return _TAG_TO_COUNTRY[m.group(1)] if m else None


def _classify(variable: str, expression: str) -> tuple[str, str]:
    """Return (domain, note) for the canonical output.

    Domain is coarse — `power_<variable>` lower-snake — so the inject
    log groups cleanly. Note carries the authoring intent (formula vs
    zero-clamp vs literal) for future readers."""
    var_slug = variable.strip().lower().replace(" ", "_")
    domain = f"power_{var_slug}"
    expr = expression.strip()
    if expr == "0":
        note = f"Zero-clamp on {variable} (BAS standardisation)"
    elif "Existing Capacity" in expr and "Capacity Additions" in expr:
        note = f"Formula on {variable} (ATS standardisation: PDP = E + Add - Ret)"
    elif expr.startswith("Add("):
        note = f"Step-add trajectory on {variable} (per-year MW deltas)"
    elif expr.startswith("Interp("):
        note = f"Interpolated trajectory on {variable}"
    else:
        note = f"Literal value on {variable}"
    return domain, note


def _country_level_stem(branch: str) -> str | None:
    """If branch is country-level (no `_IDxx`/`_MYxx` suffix on the
    leaf), return its leaf as the canonical stem. Else return None."""
    if _subnational_country(branch) is not None:
        return None
    return branch.rsplit("\\", 1)[-1]


def _subnational_stems_per_country(rows: list[dict]) -> dict[str, set[str]]:
    """First-pass scan: derive {Indonesia: {tech_stems...}, Malaysia: {…}}
    where each set holds country-level tech names whose subnational
    variants appear in the input CSV. Used to enforce the mutual-
    exclusion rule: a tech is either country-level OR subnational for
    a given AMS, never both."""
    by_country: dict[str, set[str]] = {"Indonesia": set(), "Malaysia": set()}
    for row in rows:
        branch = (row.get("Branch Path") or "").strip()
        sub = _subnational_country(branch)
        if sub is None:
            continue
        leaf = branch.rsplit("\\", 1)[-1]
        # Strip the trailing `_IDxx` / `_MYxx` to get the country-level stem
        m = _SUBNATIONAL_RE.search(leaf)
        if m is None:
            continue
        stem = leaf[: m.start()]
        by_country[sub].add(stem)
    return by_country


def convert_one(src: Path, dst: Path) -> tuple[int, int, int, int, int]:
    """Convert one LEAP-export CSV to canonical.

    Returns ``(kept, dropped_base_template, dropped_subnational_mismatch,
    dropped_country_level_for_subonly_tech, dropped_offtree)``.
    """
    kept = 0
    dropped_base_template = 0
    dropped_subnational_mismatch = 0
    dropped_country_level_subonly = 0
    dropped_offtree = 0

    with src.open(encoding="utf-8-sig", newline="") as fin:
        reader = csv.DictReader(fin)
        # Sanity-check input columns.
        missing = [c for c in COLUMN_MAP if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(
                f"[ERROR] {src.name}: missing expected LEAP-export columns "
                f"{missing}. Got: {reader.fieldnames}")
        rows = list(reader)

    # First pass: which techs are subnational-only for Indonesia / Malaysia?
    sub_stems = _subnational_stems_per_country(rows)

    with dst.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()

        for row in rows:
            region = (row.get("Region") or "").strip()
            branch = (row.get("Branch Path") or "").strip()

            if region == DROP_REGION:
                dropped_base_template += 1
                continue

            # Off-tree branches: LEAP-export emits rows on branches that
            # don't actually exist in `aeo9_v0.38_yy`'s expected tree
            # (e.g. Solar PV Rooftop on Centralized — it's Distributed-only).
            if branch in DROP_OFFTREE_BRANCHES:
                dropped_offtree += 1
                continue

            # Region-specific off-tree drop (e.g. Unmet Load valid on most
            # AMS but absent under Malaysia in `_yy`).
            if branch in DROP_BRANCHES_PER_REGION.get(region, set()):
                dropped_offtree += 1
                continue

            # Subnational branches must only appear under their matching
            # country region. Indonesia/Malaysia carry both country-level
            # and subnational branches; non-ID/MY regions never carry
            # subnational branches.
            sub_country = _subnational_country(branch)
            if sub_country is not None and region != sub_country:
                dropped_subnational_mismatch += 1
                continue

            # Mutual-exclusion rule: if a tech is subnational for ID/MY,
            # the country-level branch for that tech does NOT exist for
            # that AMS in `aeo9_v0.38_yy`. Drop those wrong-shape rows.
            if sub_country is None and region in sub_stems:
                stem = _country_level_stem(branch)
                if stem in sub_stems[region]:
                    dropped_country_level_subonly += 1
                    continue

            variable = (row.get("Variable") or "").strip()
            expression = (row.get("Expression") or "").strip()
            domain, note = _classify(variable, expression)

            writer.writerow({
                "ams": region,
                "branch": branch,
                "variable": variable,
                "expression": expression,
                "unit": (row.get("Units") or "").strip(),
                "fuel": "",
                "source": src.name,
                "note": note,
                "src_csv": src.name,
                "domain": domain,
                "data_confidence": "High",
                "unit_audit": "passthrough — input unit preserved (no conversion)",
            })
            kept += 1

    return (kept, dropped_base_template, dropped_subnational_mismatch,
            dropped_country_level_subonly, dropped_offtree)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="power.build_canonical")
    p.add_argument("inputs", nargs="+", type=Path,
                   help="LEAP-export CSV(s) to convert")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="Output dir (default: alongside each input)")
    args = p.parse_args(argv)

    print(f"[build_canonical] {len(args.inputs)} input file(s)")
    total_kept = 0
    total_dropped_bt = 0
    total_dropped_sn = 0
    total_dropped_cs = 0
    total_dropped_ot = 0
    for src in args.inputs:
        if not src.exists():
            print(f"  [SKIP] {src} — file not found")
            continue
        out_dir = args.out_dir or src.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        dst = out_dir / f"{src.stem}_canonical.csv"
        kept, dropped_bt, dropped_sn, dropped_cs, dropped_ot = convert_one(src, dst)
        total_kept += kept
        total_dropped_bt += dropped_bt
        total_dropped_sn += dropped_sn
        total_dropped_cs += dropped_cs
        total_dropped_ot += dropped_ot
        print(f"  {src.name} -> {dst.name}  "
              f"({kept} kept, {dropped_bt} Base Template, "
              f"{dropped_sn} subnational-mismatch, "
              f"{dropped_cs} country-level-for-subnational-only-tech, "
              f"{dropped_ot} off-tree dropped)")
    print(f"[build_canonical] total: {total_kept} rows kept, "
          f"{total_dropped_bt} Base Template, "
          f"{total_dropped_sn} subnational-mismatch, "
          f"{total_dropped_cs} country-level-for-subonly-tech, "
          f"{total_dropped_ot} off-tree dropped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
