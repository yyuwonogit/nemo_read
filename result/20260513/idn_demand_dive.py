"""Indonesia electricity demand attribution.

Q1. What techs consume Central Electricity? Which has the 2035 step?
Q2. Is the 2035 peak-hour jump driven by demand-profile shape change
    (sharper peak) or by Unmet Load packing into a single timeslice?

Strategy:
  - Use InputActivityRatio (NEMO param) to find every Indonesia tech that
    inputs the Centralized Electricity Generation output fuel.
  - Pull their annual use via vusebytechnologyannual.
  - For peak-hour attribution, compare timeslice profiles of
    vrateofproduction (supply) and vrateofuse (demand) for Indonesia
    central electricity, in years 2030 / 2035 / 2040. If demand profile
    matches supply profile in shape, the peak is demand-driven. If supply
    has a much spikier profile than demand (i.e., Unmet Load packed into
    one hour while demand is flatter), it's a supply-side packing
    artifact.
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 26.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v044")
ELEC_FUEL = 'Electricity output from "Centralized Electricity Generation" [LEAP ID:1]'


def main() -> int:
    db = NemoDB(str(DB_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Q1: who consumes Central Electricity in Indonesia? ---
    # Use IAR to identify, then vusebytechnologyannual to get values.
    iar = db.query("SELECT r, t, f, m, y, val FROM InputActivityRatio")
    iar = decode_dims(iar, db)
    elec_consumers = iar[
        (iar["region_name"] == "Indonesia")
        & (iar["fuel_name"] == ELEC_FUEL)
        & (iar["val"] > 0)
    ]["t"].unique()
    print(f"Indonesia techs with IAR on Central Electricity: {len(elec_consumers)}")

    use_a = db.query("SELECT r, t, f, y, val FROM vusebytechnologyannual")
    use_a = decode_dims(use_a, db)
    idn_use = use_a[
        (use_a["region_name"] == "Indonesia")
        & (use_a["fuel_name"] == ELEC_FUEL)
        & (use_a["t"].isin(elec_consumers))
        & (use_a["val"] > 0)
    ].copy()

    piv = idn_use.pivot_table(
        index="tech_name", columns="y", values="val", aggfunc="sum", fill_value=0,
    )
    # Compute 2030 → 2035 step in absolute and ratio
    if "2030" in piv.columns and "2035" in piv.columns:
        piv["delta_2030_2035"] = piv["2035"] - piv["2030"]
        piv["ratio_2030_2035"] = piv["2035"] / piv["2030"].replace(0, pd.NA)
    piv = piv.sort_values("delta_2030_2035", ascending=False)
    print("\n=== Indonesia consumers of Central Electricity (PJ/yr) ===")
    with pd.option_context("display.width", 200, "display.float_format", "{:.1f}".format):
        print(piv.round(1).to_string())
    piv.to_csv(OUT_DIR / "idn_central_electricity_consumers.csv")

    # Total annual demand
    totals = idn_use.groupby("y")["val"].sum().sort_index()
    print("\n=== Indonesia central electricity TOTAL consumption (PJ/yr) ===")
    print(totals.round(0).to_string())
    if "2030" in totals and "2035" in totals:
        print(f"  2030->2035 step: +{totals['2035']-totals['2030']:.0f} PJ  "
              f"(ratio {totals['2035']/totals['2030']:.2f}x)")

    # --- Q2: timeslice shape of supply vs demand ---
    rop = db.query("SELECT r, l, f, y, val FROM vrateofproduction")
    rou = db.query("SELECT r, l, f, y, val FROM vrateofuse")
    rop = decode_dims(rop, db)
    rou = decode_dims(rou, db)

    rop_idn = rop[(rop["region_name"] == "Indonesia") & (rop["fuel_name"] == ELEC_FUEL)]
    rou_idn = rou[(rou["region_name"] == "Indonesia") & (rou["fuel_name"] == ELEC_FUEL)]

    years_of_interest = ["2030", "2035", "2040"]
    print("\n=== Indonesia central-electricity timeslice profiles ===")
    print("(rate = PJ/yr-equivalent for that timeslice if it ran at this rate; ")
    print("  GW-cont-equiv = rate / 31.536)")
    for y in years_of_interest:
        ts_sup = rop_idn[rop_idn["y"] == y].set_index("l")["val"].sort_values(ascending=False)
        ts_dem = rou_idn[rou_idn["y"] == y].set_index("l")["val"].sort_values(ascending=False)
        if ts_sup.empty:
            continue
        # Peak, avg, peak/avg ratio for supply
        annual_pj = (ts_sup * db.query(f"SELECT l, val FROM YearSplit WHERE y='{y}'").set_index("l")["val"]).sum()
        peak_sup = ts_sup.max()
        avg_sup = annual_pj / 8.76e-3 / 31.536  # PJ/yr → GW continuous
        print(f"\n  Year {y}:")
        print(f"    Supply: peak={peak_sup/31.536:.1f} GW, avg={avg_sup:.1f} GW, "
              f"peak/avg={peak_sup/31.536/avg_sup:.2f}x")
        if not ts_dem.empty:
            annual_pj_d = (ts_dem * db.query(f"SELECT l, val FROM YearSplit WHERE y='{y}'").set_index("l")["val"]).sum()
            peak_dem = ts_dem.max()
            avg_dem = annual_pj_d / 8.76e-3 / 31.536
            print(f"    Demand: peak={peak_dem/31.536:.1f} GW, avg={avg_dem:.1f} GW, "
                  f"peak/avg={peak_dem/31.536/avg_dem:.2f}x")
        print(f"    Top 3 timeslices (supply): "
              f"{[(l, round(v/31.536,1)) for l, v in ts_sup.head(3).items()]}")
        print(f"    Top 3 timeslices (demand): "
              f"{[(l, round(v/31.536,1)) for l, v in ts_dem.head(3).items()]}")
        # Histogram of how much supply concentrates in top-5 hrs vs bottom-half
        top5 = ts_sup.head(5).sum()
        rest = ts_sup.iloc[5:].sum()
        print(f"    Supply top-5 timeslices share of rate sum: "
              f"{top5/(top5+rest)*100:.1f}%  ({len(ts_sup)} timeslices total)")

    # Save per-timeslice CSV for offline plotting
    rop_idn[rop_idn["y"].isin(years_of_interest)].to_csv(
        OUT_DIR / "idn_supply_timeslice_2030_2035_2040.csv", index=False
    )
    rou_idn[rou_idn["y"].isin(years_of_interest)].to_csv(
        OUT_DIR / "idn_demand_timeslice_2030_2035_2040.csv", index=False
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
