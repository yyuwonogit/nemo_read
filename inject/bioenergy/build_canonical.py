"""
Build canonical CSV for the bioenergy input.

Reads:  inject/bioenergy/bioenergy_leap_input.csv  (CSV-owner format)
Writes: inject/bioenergy/canonical_leap_inputs.csv (package canonical format)

What this script does (full per-step list mirrors CSV_AUTHORING_GUIDE.md):

1. Column renames:
       Branch Path  -> branch
       Region       -> ams
       Units        -> unit
   (Variable, Expression, Source, Note kept as-is.)

2. Region name normalisation. The bioenergy CSV uses long-form country
   names; LEAP uses short-form. The adapter normalises:
       Brunei Darussalam -> Brunei
       Lao PDR           -> Laos
       Viet Nam          -> Vietnam

3. "All 10 AMS" scope expansion. Rows with Region="All 10 AMS" duplicate
   to one row per AMS (10 rows out per 1 row in).

4. Fuel context extraction from Note. Looks for "output_fuel=X" or
   "fuel=X" patterns; extracts X into the canonical `fuel` column for
   later fuel-specific unit-conversion lookups (e.g. coal LHV varies
   by sub-grade).

5. Preserves bioenergy-specific extras (Domain, Confidence) as
   `domain` and `data_confidence` columns. The audit/inject pipeline
   leaves these untouched.

Run:
    python inject/bioenergy/build_canonical.py

Output:
    inject/bioenergy/canonical_leap_inputs.csv
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

TOPIC_DIR = Path(__file__).resolve().parent
SOURCE_CSV = TOPIC_DIR / "bioenergy_leap_input.csv"
OUTPUT_CSV = TOPIC_DIR / "canonical_leap_inputs.csv"
HANDOFF_CSV = TOPIC_DIR / "bioenergy_maximum_capacity_handoff.csv"

# LEAP region names that exist in aeo9 (must match leap.Regions[].Name exactly).
ALL_10_AMS = [
    "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
    "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam",
]

# Branches that exist in the source CSV but are missing in LEAP
# (`aeo9_v0.33_bak` as of 2026-04-29). Rows on these branches are filtered
# out of `canonical_leap_inputs.csv` so the audit / injection pipeline
# doesn't trip on a `branch not in tree` mismatch. Once the LEAP-side
# branches are added (per CSV_AUTHORING_GUIDE §11.B), drop the
# corresponding entries from this set and re-run.
LEAP_MISSING_BRANCHES = {
    "Resources\\Primary\\Rice Straw",                                            # §11.B.4
    "Resources\\Primary\\Used Cooking Oil",                                      # §11.B.5
    "Transformation\\Bioethanol Production\\Processes\\Cellulosic Rice Straw",   # §11.B.1
}

# Deferred (branch, variable) patterns — variables that LEAP doesn't expose
# on the branch as currently authored. Out of scope for the current single-
# cap design (see CSV_AUTHORING_GUIDE §12.4). Filtered at build time so
# injection isn't blocked. Revisit once placement is resolved (likely move
# emission factors from Feedstock Fuels sub-branches onto parent Process
# branches, and move CO2 biogenic off Resources\Secondary\Biodiesel).
EMISSION_FACTOR_VARIABLES = {
    "CO2 (process)", "CH4 (process)", "N2O (process)",
    "NH3 (process)", "NOx (process)", "SO2 (process)",
    "NMVOC (process)", "CO2 biogenic",
}


def _is_deferred(branch: str, variable: str) -> bool:
    """Return True if this (branch, variable) pair is deferred per §12.4."""
    if variable in EMISSION_FACTOR_VARIABLES:
        # Emission factors authored on Feedstock Fuels sub-branches:
        # LEAP doesn't expose them there.
        if "\\Feedstock Fuels\\" in branch:
            return True
        # CO2 biogenic on the Biodiesel output-fuel resource: not exposed.
        if branch == "Resources\\Secondary\\Biodiesel" and variable == "CO2 biogenic":
            return True
    return False


# Note: a Maximum Capacity handoff filter was added 2026-05-05 when live
# COM probe of v0.36 returned None on the 7 bioenergy process branches. It
# turned out to be a transient LEAP-side issue (variable was hidden, not
# retired); LEAP team re-enabled the variable on 2026-05-05 and the filter
# was removed the same day. CSV_AUTHORING_GUIDE §13.2 records the cycle
# for posterity. If the variable goes missing again, restore the filter
# from git history (commit before 2026-05-05 inject).
PROCESS_MAX_CAPACITY_HANDOFF_BRANCHES: set[str] = set()


def _is_process_max_capacity_handoff(branch: str, variable: str) -> bool:
    return (variable == "Maximum Capacity"
            and branch in PROCESS_MAX_CAPACITY_HANDOFF_BRANCHES)

# Long-form -> LEAP short-form region names.
REGION_NORMALISE = {
    "Brunei Darussalam": "Brunei",
    "Lao PDR":           "Laos",
    "Viet Nam":          "Vietnam",
    # Already-correct names pass through unchanged.
}

# Match `output_fuel=X` or `fuel=X` (X = single token, no semicolon)
_FUEL_RE = re.compile(r"\b(?:output_)?fuel\s*=\s*([^;,\n]+)", re.IGNORECASE)

# Branch-path heuristics for output fuel. Used as fallback when the Note
# field doesn't carry an explicit `output_fuel=` token. Order matters —
# more specific patterns first.
_BRANCH_FUEL_RULES = [
    ("Biodiesel Production",  "Biodiesel"),
    ("Bioethanol Production", "Ethanol"),
]


def _normalise_region(value: str) -> str:
    return REGION_NORMALISE.get(value.strip(), value.strip())


def _extract_fuel(note: str, branch: str = "") -> str:
    """Extract output-fuel context.

    Preferred source: an explicit `output_fuel=X` (or `fuel=X`) token in
    the Note field. Fallback: infer from the branch path (e.g. anything
    under `Transformation\\Biodiesel Production\\...` is Biodiesel).
    """
    if isinstance(note, str):
        m = _FUEL_RE.search(note)
        if m:
            return m.group(1).strip()
    for needle, fuel in _BRANCH_FUEL_RULES:
        if needle in (branch or ""):
            return fuel
    return ""


def _expand_region(row: dict, region_key: str) -> list[dict]:
    """Yield one canonical row per (input row × AMS expansion)."""
    region = (row.get(region_key) or "").strip()
    if region == "All 10 AMS":
        return [{**row, region_key: ams} for ams in ALL_10_AMS]
    return [row]


# Column-name mapping: (canonical_key, [legacy_owner_key, ...]).
# build() picks the first key that's present in each input row, so the
# adapter handles both the original "owner format" CSV and the newer
# canonical-shape CSV (lowercase headers) the bioenergy team now ships.
_KEY_MAP = {
    "ams":             ["ams", "Region"],
    "branch":          ["branch", "Branch Path"],
    "variable":        ["variable", "Variable"],
    "expression":      ["expression", "Expression"],
    "unit":            ["unit", "Units"],
    "fuel":            ["fuel"],   # canonical-only — legacy reads from Note
    "source":          ["source", "Source"],
    "note":            ["note", "Note"],
    "domain":          ["domain", "Domain"],
    "data_confidence": ["data_confidence", "Confidence"],
}


def _pick(row: dict, canonical_key: str) -> str:
    for k in _KEY_MAP[canonical_key]:
        if k in row and row.get(k) not in (None, ""):
            return row[k]
    return ""


def build():
    with SOURCE_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        in_rows = list(reader)
    print(f"  read  {SOURCE_CSV.name}  ({len(in_rows)} input rows)")

    # Detect the region column once — either canonical "ams" or legacy "Region".
    region_key = "ams" if (in_rows and "ams" in in_rows[0]) else "Region"

    out_rows = []
    handoff_rows = []
    skipped_leap_missing: dict[str, int] = {}
    skipped_deferred: dict[tuple[str, str], int] = {}
    routed_handoff: dict[tuple[str, str], int] = {}
    for row in in_rows:
        for r in _expand_region(row, region_key):
            branch = _pick(r, "branch")
            variable = _pick(r, "variable")
            note   = _pick(r, "note")
            # Skip branches LEAP doesn't have yet (LEAP_MISSING_BRANCHES set).
            if branch in LEAP_MISSING_BRANCHES:
                skipped_leap_missing[branch] = skipped_leap_missing.get(branch, 0) + 1
                continue
            # Skip deferred (branch, variable) patterns (§12.4).
            if _is_deferred(branch, variable):
                key = (branch, variable)
                skipped_deferred[key] = skipped_deferred.get(key, 0) + 1
                continue
            # If the canonical 'fuel' column is empty (or absent), fall
            # back to extracting from Note / branch-path heuristic.
            fuel = _pick(r, "fuel") or _extract_fuel(note, branch)
            row_out = {
                "ams":             _normalise_region(_pick(r, "ams")),
                "branch":          branch,
                "variable":        _pick(r, "variable"),
                "expression":      _pick(r, "expression"),
                "unit":            _pick(r, "unit"),
                "fuel":            fuel,
                "source":          _pick(r, "source"),
                "note":            note,
                "src_csv":         SOURCE_CSV.name,
                # Bioenergy-specific extras (preserved for traceability):
                "domain":          _pick(r, "domain"),
                "data_confidence": _pick(r, "data_confidence"),
            }
            # Route Maximum Capacity rows on migrated process branches to
            # the LEAP-team handoff CSV (§13.3) instead of the inject
            # canonical. The standard injector would have logged them as
            # var_not_found on v0.36; this filter keeps the inject CSV
            # clean while preserving the values for the LEAP team.
            if _is_process_max_capacity_handoff(branch, variable):
                handoff_rows.append(row_out)
                routed_handoff[(branch, variable)] = (
                    routed_handoff.get((branch, variable), 0) + 1)
                continue
            out_rows.append(row_out)

    fieldnames = [
        "ams", "branch", "variable", "expression", "unit", "fuel",
        "source", "note", "src_csv", "domain", "data_confidence",
    ]
    # CLAUDE.md §A.15: normalise every Interp() to comma list-sep + period
    # decimal at write time. Defensive against future authors mis-typing
    # semicolons in raw inputs.
    from nemo_read._leap_com import normalize_interp
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in out_rows:
            r["expression"] = normalize_interp(r["expression"])
            writer.writerow(r)
    print(f"  wrote {OUTPUT_CSV.name}  ({len(out_rows)} rows)")

    # Emit the handoff CSV (Maximum Capacity rows on migrated process
    # branches). Same canonical schema as the inject CSV, but each row's
    # `note` column is prefixed with the migration context so the LEAP
    # team can re-route to Exogenous / Endogenous Capacity as appropriate.
    if handoff_rows:
        handoff_prefix = (
            "[2026-05-05 §13.3 LEAP-team handoff] "
            "Maximum Capacity variable retired on this Process branch in "
            "LEAP v0.36 (live COM probe confirms Variable=None). Original "
            "intent: refinery-fleet schedule. Likely v0.36 target: "
            "Exogenous Capacity (locked-in fleet) or Endogenous Capacity + "
            "ceiling (optimizer-picked, capped) — LEAP team to decide. "
            "Source unit `Million Tonnes/yr` of biofuel; existing v0.36 "
            "Exogenous Capacity rows on these branches use Interp(year, "
            "million_litres) * 10^6 * ConvFuelUnits(liter, gj, <fuel>); to "
            "splice with that style, multiply Mt by 1136 (biodiesel) or "
            "1267 (ethanol) to convert tonnes to litres. ORIGINAL NOTE: "
        )
        with HANDOFF_CSV.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in handoff_rows:
                rr = dict(r)
                rr["note"] = handoff_prefix + (r.get("note") or "")
                writer.writerow(rr)
        print(f"  wrote {HANDOFF_CSV.name}  ({len(handoff_rows)} rows)  "
              f"[hand to LEAP team — see §13.3]")

    # Quick summary
    from collections import Counter
    by_var = Counter(r["variable"] for r in out_rows)
    by_ams = Counter(r["ams"] for r in out_rows)
    print()
    print("Rows per variable:")
    for v, n in by_var.most_common():
        print(f"  {n:>4}  {v}")
    print()
    print(f"Rows per AMS: {dict(sorted(by_ams.items()))}")
    print()
    fuel_count = sum(1 for r in out_rows if r["fuel"])
    print(f"Rows with extracted fuel context: {fuel_count} / {len(out_rows)}")

    if skipped_leap_missing:
        total_skipped = sum(skipped_leap_missing.values())
        print()
        print(f"WARNING: filtered {total_skipped} rows on LEAP-missing branches "
              f"(see LEAP_MISSING_BRANCHES in {Path(__file__).name}):")
        for branch, n in sorted(skipped_leap_missing.items()):
            print(f"  {n:>4}  {branch}")
        print("Re-add these once the LEAP-side branches exist (guide §11.B).")

    if skipped_deferred:
        total_def = sum(skipped_deferred.values())
        print()
        print(f"WARNING: filtered {total_def} deferred rows "
              f"(see _is_deferred / §12.4 in CSV_AUTHORING_GUIDE.md):")
        for (branch, variable), n in sorted(skipped_deferred.items()):
            print(f"  {n:>4}  {branch}:{variable}")
        print("These are emission-factor / structural placement issues; "
              "deferred until §12.4 cluster is reopened.")

    if routed_handoff:
        total_h = sum(routed_handoff.values())
        print()
        print(f"NOTE: routed {total_h} rows to {HANDOFF_CSV.name} "
              f"(LEAP team handoff — see §13.3 in CSV_AUTHORING_GUIDE.md):")
        for (branch, variable), n in sorted(routed_handoff.items()):
            print(f"  {n:>4}  {branch}:{variable}")
        print("Maximum Capacity variable retired in LEAP v0.36. These "
              "rows preserve the refinery-fleet schedule for the LEAP "
              "team to inject into Exogenous Capacity or Endogenous "
              "Capacity (their call) on the v0.36 schema.")


if __name__ == "__main__":
    build()
