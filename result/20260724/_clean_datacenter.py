"""Human-readable Data Center views from the machine tidy slice.

Drops every column that carries no information for this slice. In
aeo9_v0.72_datacenter.csv, 11 of 18 columns are single-valued
(domain/sector/subsector/layer/fuel/carrier/unit/confident_carrier/
fuel_resolved/path_repaired, plus branch_path which is branch_leaf with a
constant prefix), and the scenario axis is a fourth: BAS/ATS/RAS are
bit-identical here, so carrying it triples the rows for zero information.
Both facts are asserted, not assumed — if a future vintage differentiates
by scenario this script fails rather than silently dropping real data.
"""
import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent
SRC = OUT / "aeo9_v0.72_datacenter.csv"
TYPES = ["Hyperscale", "Colocation", "Enterprise"]

rows = list(csv.DictReader(SRC.open(encoding="utf-8")))

CONSTANT = ["domain", "sector", "subsector", "layer", "fuel", "carrier", "unit",
            "confident_carrier", "fuel_resolved", "path_repaired"]
for col in CONSTANT:
    vals = {r[col] for r in rows}
    assert len(vals) == 1, f"{col} is not constant ({len(vals)} values) — do not drop"

PREFIX = "Demand" + chr(92) + "Commercial" + chr(92) + "Data_Center" + chr(92)
for r in rows:                     # branch_path adds nothing over branch_leaf
    assert r["branch_path"] == PREFIX + r["branch_leaf"], f"unexpected path {r['branch_path']}"

by_scen = {}
for r in rows:
    by_scen.setdefault(r["scenario_code"], {})[
        (r["region"], r["branch_leaf"], int(r["year"]))] = float(r["value"])
base = by_scen["BAS"]
for code, d in by_scen.items():
    assert d.keys() == base.keys(), f"{code} covers different keys than BAS"
    assert all(d[k] == base[k] for k in base), f"{code} differs from BAS — keep scenario"
print(f"asserted: {len(CONSTANT)} constant columns + branch_path redundant, "
      f"{len(by_scen)} scenarios bit-identical ({len(base)} cells each)")

regions = sorted({rg for rg, _, _ in base})
years = sorted({y for _, _, y in base})

# The tidy source drops zero rows (skip-zeros, §7.4), so the region x type x
# year grid has holes — a human table wants an explicit 0, not a blank.
def twh(rg, ty, y):
    return round(base.get((rg, ty, y), 0.0) / 1000, 3)

filled = len(regions) * len(TYPES) * len(years) - len(base)
print(f"grid holes filled with explicit 0: {filled} of "
      f"{len(regions)*len(TYPES)*len(years)} cells")

# ---- 1. tidy long: one row per region x type x year ----------------------
long_path = OUT / "aeo9_v0.72_datacenter_clean.csv"
with long_path.open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["region", "data_center_type", "year", "twh"])
    for rg in regions:
        for ty in TYPES:
            for y in years:
                w.writerow([rg, ty, y, twh(rg, ty, y)])
print(f"{long_path.name}  ->  {len(regions)*len(TYPES)*len(years):,} rows")

# ---- 2. wide table: years across, ASEAN roll-ups at the bottom -----------
wide_path = OUT / "aeo9_v0.72_datacenter_table.csv"
with wide_path.open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["region", "data_center_type"] + [str(y) for y in years])
    for rg in regions:
        for ty in TYPES:
            w.writerow([rg, ty] + [twh(rg, ty, y) for y in years])
        w.writerow([rg, "TOTAL"] +
                   [round(sum(twh(rg, t, y) for t in TYPES), 3) for y in years])
    for ty in TYPES:
        w.writerow(["ASEAN", ty] +
                   [round(sum(twh(rg, ty, y) for rg in regions), 3) for y in years])
    w.writerow(["ASEAN", "TOTAL"] +
               [round(sum(twh(rg, t, y) for rg in regions for t in TYPES), 3)
                for y in years])
print(f"{wide_path.name}  ->  {len(regions)*(len(TYPES)+1)+len(TYPES)+1} rows x {len(years)} years")
print("units: TWh (electricity). Regions with zero demand in every year are absent: "
      "Brunei, Cambodia, Laos, Myanmar.")
