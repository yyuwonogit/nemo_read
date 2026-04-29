"""
Build canonical CSV for the bioenergy input.

Reads:  mailbox/bioenergy/bioenergy_leap_input.csv  (CSV-owner format)
Writes: mailbox/bioenergy/canonical_leap_inputs.csv (package canonical format)

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
    python mailbox/bioenergy/build_canonical.py

Output:
    mailbox/bioenergy/canonical_leap_inputs.csv
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

TOPIC_DIR = Path(__file__).resolve().parent
SOURCE_CSV = TOPIC_DIR / "bioenergy_leap_input.csv"
OUTPUT_CSV = TOPIC_DIR / "canonical_leap_inputs.csv"

# LEAP region names that exist in aeo9 (must match leap.Regions[].Name exactly).
ALL_10_AMS = [
    "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
    "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam",
]

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
    for row in in_rows:
        for r in _expand_region(row, region_key):
            branch = _pick(r, "branch")
            note   = _pick(r, "note")
            # If the canonical 'fuel' column is empty (or absent), fall
            # back to extracting from Note / branch-path heuristic.
            fuel = _pick(r, "fuel") or _extract_fuel(note, branch)
            out_rows.append({
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
            })

    fieldnames = [
        "ams", "branch", "variable", "expression", "unit", "fuel",
        "source", "note", "src_csv", "domain", "data_confidence",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in out_rows:
            writer.writerow(r)
    print(f"  wrote {OUTPUT_CSV.name}  ({len(out_rows)} rows)")

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


if __name__ == "__main__":
    build()
