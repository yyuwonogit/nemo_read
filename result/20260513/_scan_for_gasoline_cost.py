"""Scan every NEMO parameter table for values near the LEAP-stored
Gasoline Import Cost anchor points (Singapore). Goal: find whether
that LEAP value lands somewhere in NEMO other than VariableCost.

Per §A.14: quote query results, don't infer.
"""
from __future__ import annotations
import sqlite3
import sys

DB = "feas/NEMO_25 27.sqlite"

# LEAP Import Cost for Singapore Gasoline at the 8 NEMO model years
# (2025-2060). 2024 omitted since NEMO model starts at 2025.
ANCHORS = {
    2025: 66.9348,
    2030: 103.979,
    2035: 109.067,
    2040: 114.95,
    2045: 120.037,
    2050: 125.92,
    2055: 131.962,
    2060: 138.957,
}

# Search ranges:
#   - raw value ±0.5%
#   - common LEAP→NEMO unit conversions:
#     /5.7 (GJ/bbl roughly), /5.4, /6.0, /5.0
#     x0.948 (HHV/LHV factor observed on LNG)
#     x1000 (USD vs M$ unit shift)
CONVERSIONS = {
    "raw":          lambda v: v,
    "/5.7":         lambda v: v / 5.7,
    "/5.4":         lambda v: v / 5.4,
    "/6.0":         lambda v: v / 6.0,
    "/5.0":         lambda v: v / 5.0,
    "x0.948":       lambda v: v * 0.948,
    "/5.7x0.948":   lambda v: v / 5.7 * 0.948,
    "/5.4x0.948":   lambda v: v / 5.4 * 0.948,
    "x1.058":       lambda v: v * 1.058,
}


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # Find every table that has a `val` column
    rows = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    candidate_tables = []
    for (name,) in rows:
        cols = [r[1] for r in cur.execute(f'PRAGMA table_info("{name}")').fetchall()]
        if "val" in cols:
            candidate_tables.append((name, cols))

    print(f"Tables with a 'val' column: {len(candidate_tables)}")

    # For each anchor year, find any (table, row) where val falls within
    # ±0.5% of any of the conversion-adjusted target values
    tol_pct = 0.005
    by_year_hits = {}
    for year, leap_val in ANCHORS.items():
        targets = {label: f(leap_val) for label, f in CONVERSIONS.items()}
        hits = []
        for tbl, cols in candidate_tables:
            has_r = "r" in cols
            has_y = "y" in cols
            select_cols = ", ".join(f'"{c}"' for c in cols)
            # Build WHERE clauses for each target value
            for label, tgt in targets.items():
                if tgt == 0:
                    continue
                lo = tgt * (1 - tol_pct)
                hi = tgt * (1 + tol_pct)
                # Restrict to Singapore (R16) where 'r' column exists; restrict
                # to year=str(year) where 'y' column exists
                conds = [f'"val" BETWEEN {lo} AND {hi}']
                if has_r:
                    conds.append("\"r\"='R16'")
                if has_y:
                    conds.append(f"\"y\"='{year}'")
                sql = (
                    f'SELECT {select_cols} FROM "{tbl}" WHERE '
                    + " AND ".join(conds) + " LIMIT 5"
                )
                try:
                    found = cur.execute(sql).fetchall()
                except Exception as e:
                    continue
                if found:
                    for row in found:
                        hits.append((tbl, label, tgt, dict(zip(cols, row))))
        by_year_hits[year] = hits
        print(f"\n=== Year {year} (LEAP value {leap_val}) — {len(hits)} hits across {len(candidate_tables)} tables ===")
        # Group by table
        from collections import Counter
        ctr = Counter(h[0] for h in hits)
        for tbl, n in ctr.most_common():
            print(f"  {tbl}: {n} hit(s)")
        # Show first few hits per table
        seen = set()
        for tbl, label, tgt, row in hits:
            key = tbl
            if key in seen: continue
            seen.add(key)
            print(f"    {tbl}  via {label}  target~{tgt:.4f}  row={row}")

    print("\n\n=== Summary: which tables had hits for ALL 8 anchor years (most likely match) ===")
    from collections import Counter
    table_year_set = {}
    for year, hits in by_year_hits.items():
        for tbl, label, tgt, row in hits:
            table_year_set.setdefault(tbl, set()).add(year)
    for tbl, years in sorted(table_year_set.items(), key=lambda x: -len(x[1])):
        print(f"  {tbl}: matched {len(years)}/8 years  ({sorted(years)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
