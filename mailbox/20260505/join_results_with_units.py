"""Join Probe A (results) with Probe B (units) into a single self-documenting CSV.

Step C of the lite results-harvest SOP (see RESULTS_HARVEST_SOP.md).

Inputs:
    --results PATH       Probe A output CSV (results_<scenario>_centralized.csv)
    --units   PATH       Probe B output CSV (units_<context>.csv)
    --out     PATH       Combined CSV destination

Output columns:
    ams, branch, branch_type, variable, year, value, unit, unit_source

Where ``unit_source`` is one of:
    direct   — unit came from Probe B for the same (branch, variable)
    inferred — unit came from the result-side inference table (for result
               variables with no write-side counterpart on the same branch)
    unknown  — no unit could be assigned

The inference table is curated empirically from AEO9_v0.36 inspection
(see RESULTS_HARVEST_SOP.md §"Inference table"). Override per-call with
--inference KEY=UNIT,KEY2=UNIT2.

Usage:
    python mailbox/20260505/join_results_with_units.py \\
        --results mailbox/20260505/results_BAS_centralized.csv \\
        --units mailbox/20260505/units_centralized.csv \\
        --out mailbox/20260505/joined_BAS.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Result-side variables whose units can be inferred from a known
# write-side companion. Keys are RESULT variable names (as they appear
# in Probe A), values are tuples (write_side_name, fallback_unit).
#
# At join time, we first try direct match (same name in Probe B); if
# that misses we look up the write_side_name in Probe B for the same
# branch; if THAT also misses we fall back to the literal fallback_unit.
INFERENCE_TABLE: dict[str, tuple[str, str]] = {
    # capacity-side results derive from Exogenous Capacity unit
    "Existing Capacity":           ("Exogenous Capacity", "Megawatt"),
    "Capacity Additions":          ("Exogenous Capacity", "Megawatt"),
    "Capacity Retirement":         ("Exogenous Capacity", "Megawatt"),
    "Capacity Added":              ("Exogenous Capacity", "Megawatt"),
    "Capacity Retired":            ("Exogenous Capacity", "Megawatt"),
    # power output (capacity-equivalent)
    "Power Generation":            ("",                  "Megawatt"),
    # energy outputs — area General Properties default; LEAP area
    # default for AEO9_v0.36 is Gigajoule. Override with --inference
    # if your area uses different default.
    "Energy Generation":           ("",                  "Gigajoule"),
    "Curtailed Energy Production": ("",                  "Gigajoule"),
    # cost-side results — derive from Capital Cost / Variable OM Cost
    # for the same branch; presented as USD aggregate
    "Costs of Production":         ("",                  "Thousand U.S. Dollar"),
    "Investment Costs":            ("Capital Cost",      "Thousand U.S. Dollar/Megawatt"),
    # emissions — varies by pollutant tagged on the branch; default to
    # CO2-equivalent metric tonnes which is the most common LEAP setting
    "Pollutant Loadings":          ("",                  "Metric Tonne CO2 Equivalent"),
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="join_results_with_units")
    p.add_argument("--results", required=True,
                   help="Probe A CSV (long format: ams, branch, branch_type, variable, year, value)")
    p.add_argument("--units", required=True,
                   help="Probe B CSV (long format: branch, branch_type, variable, unit)")
    p.add_argument("--out", required=True,
                   help="Combined CSV destination")
    p.add_argument("--inference", default="",
                   help="Override inference table: KEY=UNIT,KEY2=UNIT2 (replaces fallback only)")
    return p.parse_args(argv)


def load_units(path: Path) -> dict[tuple[str, str], str]:
    """Build {(branch, variable) → unit} from Probe B CSV."""
    out: dict[tuple[str, str], str] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["branch"], row["variable"])
            unit = row.get("unit", "").strip()
            if unit:
                out[key] = unit
    return out


def parse_inference_overrides(s: str) -> dict[str, str]:
    """Parse 'Key=Unit,Key2=Unit2' into {Key: Unit}."""
    out: dict[str, str] = {}
    for chunk in s.split(","):
        chunk = chunk.strip()
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def resolve_unit(
    branch: str,
    variable: str,
    units_idx: dict[tuple[str, str], str],
    inference_overrides: dict[str, str],
) -> tuple[str, str]:
    """Return (unit, source) for a (branch, variable).

    Source is one of: ``direct`` / ``inferred`` / ``unknown``.
    """
    # 1. direct match: same (branch, variable) in Probe B
    if (branch, variable) in units_idx:
        return units_idx[(branch, variable)], "direct"
    # 2. inferred via companion write-side variable on the same branch
    rule = INFERENCE_TABLE.get(variable)
    if rule:
        write_side, fallback = rule
        if write_side and (branch, write_side) in units_idx:
            return units_idx[(branch, write_side)], "inferred"
        # 3. inference table fallback (CLI override has priority)
        return inference_overrides.get(variable, fallback), "inferred"
    return "", "unknown"


def main(argv=None) -> int:
    args = parse_args(argv)
    results_path = Path(args.results)
    units_path = Path(args.units)
    out_path = Path(args.out)

    if not results_path.exists():
        print(f"ERROR: results CSV not found: {results_path}", file=sys.stderr)
        return 1
    if not units_path.exists():
        print(f"ERROR: units CSV not found: {units_path}", file=sys.stderr)
        return 1

    units_idx = load_units(units_path)
    inference_overrides = parse_inference_overrides(args.inference)
    print(f"[join] units index: {len(units_idx)} (branch, variable) pairs")

    fieldnames = ["ams", "branch", "branch_type", "variable",
                  "year", "value", "unit", "unit_source"]
    counts = {"direct": 0, "inferred": 0, "unknown": 0}
    n_rows = 0

    with results_path.open(encoding="utf-8") as fin, \
         out_path.open("w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            unit, source = resolve_unit(
                row["branch"], row["variable"], units_idx, inference_overrides,
            )
            counts[source] += 1
            writer.writerow({
                "ams":         row["ams"],
                "branch":      row["branch"],
                "branch_type": row["branch_type"],
                "variable":    row["variable"],
                "year":        row["year"],
                "value":       row["value"],
                "unit":        unit,
                "unit_source": source,
            })
            n_rows += 1

    print(f"[join] wrote {n_rows} rows to {out_path}")
    print(f"[join] unit source breakdown:")
    for src, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        pct = n / n_rows * 100 if n_rows else 0
        print(f"    {src:<10} {n:>6}  ({pct:5.1f}%)")

    if counts["unknown"] > 0:
        print()
        print("WARNING: some variables had no unit. Either extend "
              "INFERENCE_TABLE in this script or pass --inference KEY=UNIT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
