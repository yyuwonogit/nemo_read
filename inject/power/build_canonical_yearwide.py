"""Year-wide LEAP-export → canonical adapter for the power domain.

Input shape (one row per branch+variable+region, columns are years):

    Branch Path, Variable, Region, Unit, 2005, 2006, ..., 2024

Output shape: canonical schema (same as `build_canonical.py` produces),
with `expression` set to::

    Interp(2005, V05, 2006, V06, ..., 2024, V24, FirstScenarioYear, 0)

The trailing `FirstScenarioYear, 0` anchor matches the established
round1p5 pattern (re-inject CSV files in result/20260505/).

This adapter writes **per-scenario** canonical CSVs. Variable scoping:

- `Existing Capacity` rows → Current Accounts (CA) only.
- `Historical Production` rows → CA, ATS, BAS (HP doesn't auto-inherit
  across scenarios; each scenario carries its own HP override).

Filters (same as build_canonical.py):
- Drop `Base Template`.
- Drop subnational-mismatch (`_IDxx` paired with non-Indonesia, etc.).
- Drop country-level-for-subnational-only-tech rows (per-AMS mutual
  exclusion).
- Drop off-tree branches in `DROP_OFFTREE_BRANCHES`.

Usage:
    python inject/power/build_canonical_yearwide.py \\
        --csv "inject/power/20260507/<wide_csv>" \\
        --out-dir inject/power/20260507/ \\
        --tag rev1
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

# Reuse filters/schema from the regular adapter so behaviour stays in sync.
from build_canonical import (  # type: ignore[import-not-found]
    CANONICAL_FIELDS,
    DROP_REGION,
    DROP_OFFTREE_BRANCHES,
    DROP_BRANCHES_PER_REGION,
    _classify,
    _country_level_stem,
    _subnational_country,
    _SUBNATIONAL_RE,
)

# Variable → which scenarios should receive that row.
VAR_TO_SCENARIOS: dict[str, list[str]] = {
    "Existing Capacity": ["CA"],
    "Historical Production": ["CA", "ATS", "BAS"],
}
SCENARIO_FULL_NAME = {
    "CA": "Current Accounts",
    "ATS": "AMS Target Scenario",
    "BAS": "Baseline Simulation",
}


def _build_interp(years: list[int], values: list[str]) -> str:
    """Build a comma-list-sep `Interp(...)` expression with the
    FirstScenarioYear=0 anchor. Period-decimal numerals come from the
    source CSV unchanged. Empty / blank values are kept as 0."""
    parts: list[str] = []
    for y, v in zip(years, values):
        v = (v or "").strip()
        if v == "" or v.lower() == "nan":
            v = "0"
        parts.append(f"{y}, {v}")
    parts.append("FirstScenarioYear, 0")
    return f"Interp({', '.join(parts)})"


def _stems_for_subnational_filter(rows: list[dict]) -> dict[str, set[str]]:
    """Mirror build_canonical.py logic: derive {Indonesia: stems, Malaysia: stems}
    from rows where branch has subnational suffix and is NOT off-tree."""
    by_country: dict[str, set[str]] = {"Indonesia": set(), "Malaysia": set()}
    for row in rows:
        branch = (row.get("Branch Path") or "").strip()
        if branch in DROP_OFFTREE_BRANCHES:
            continue
        sub = _subnational_country(branch)
        if sub is None:
            continue
        leaf = branch.rsplit("\\", 1)[-1]
        m = _SUBNATIONAL_RE.search(leaf)
        if m is None:
            continue
        stem = leaf[: m.start()]
        by_country[sub].add(stem)
    return by_country


def _read_wide(src: Path) -> tuple[list[dict], list[int]]:
    with src.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames or []
    year_cols = [c for c in fields if c.strip().isdigit()]
    years = [int(c.strip()) for c in year_cols]
    return rows, years


def _expand_row(row: dict, years: list[int],
                sub_stems: dict[str, set[str]]) -> dict | None:
    """Apply filters + build Interp expression. Return canonical row dict,
    or None if filtered out."""
    region = (row.get("Region") or "").strip()
    branch = (row.get("Branch Path") or "").strip()
    variable = (row.get("Variable") or "").strip()
    unit = (row.get("Unit") or "").strip()

    if region == DROP_REGION:
        return None
    if branch in DROP_OFFTREE_BRANCHES:
        return None
    if branch in DROP_BRANCHES_PER_REGION.get(region, set()):
        return None  # region-specific off-tree
    sub_country = _subnational_country(branch)
    if sub_country is not None and region != sub_country:
        return None  # subnational-mismatch
    if sub_country is None and region in sub_stems:
        stem = _country_level_stem(branch)
        if stem in sub_stems[region]:
            return None  # country-level-for-subonly-tech

    values = [str(row.get(str(y), "")).strip() for y in years]
    expression = _build_interp(years, values)
    domain, note = _classify(variable, expression)
    note += " | sourced from year-wide Rev1 input"

    return {
        "ams": region,
        "branch": branch,
        "variable": variable,
        "expression": expression,
        "unit": unit,
        "fuel": "",
        "source": row.get("__src", ""),
        "note": note,
        "src_csv": row.get("__src", ""),
        "domain": domain,
        "data_confidence": "High",
        "unit_audit": "passthrough — input unit preserved (no conversion)",
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="power.build_canonical_yearwide")
    p.add_argument("--csv", required=True, type=Path,
                   help="Year-wide LEAP-export CSV")
    p.add_argument("--out-dir", required=True, type=Path,
                   help="Output dir for per-scenario canonical CSVs")
    p.add_argument("--tag", default="yw",
                   help="Filename prefix tag (e.g. 'rev1')")
    args = p.parse_args(argv)

    if not args.csv.exists():
        print(f"[ERROR] {args.csv} not found")
        return 2

    rows, years = _read_wide(args.csv)
    src_name = args.csv.name
    for r in rows:
        r["__src"] = src_name
    print(f"[yearwide] {len(rows)} rows queued from {src_name}; "
          f"years span {min(years)}-{max(years)}")

    sub_stems = _stems_for_subnational_filter(rows)
    print(f"[yearwide] subnational stems derived: "
          f"Indonesia={len(sub_stems['Indonesia'])}, "
          f"Malaysia={len(sub_stems['Malaysia'])}")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    canonical_rows: list[dict] = []
    dropped = 0
    for r in rows:
        out = _expand_row(r, years, sub_stems)
        if out is None:
            dropped += 1
            continue
        canonical_rows.append(out)
    print(f"[yearwide] {len(canonical_rows)} rows kept after filters "
          f"({dropped} dropped)")

    by_scenario: dict[str, list[dict]] = defaultdict(list)
    for r in canonical_rows:
        scenarios = VAR_TO_SCENARIOS.get(r["variable"], [])
        if not scenarios:
            print(f"  [WARN] variable {r['variable']!r} has no scenario "
                  f"mapping — skipped")
            continue
        for s in scenarios:
            by_scenario[s].append(r)

    for scn_short, rows_for_scn in sorted(by_scenario.items()):
        out = args.out_dir / f"{args.tag}_{scn_short.lower()}_canonical.csv"
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
            w.writeheader()
            for r in rows_for_scn:
                # Strip the per-row __src helper field if present
                clean = {k: r.get(k, "") for k in CANONICAL_FIELDS}
                w.writerow(clean)
        print(f"  -> {out.name} ({len(rows_for_scn)} rows for "
              f"{SCENARIO_FULL_NAME[scn_short]!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
