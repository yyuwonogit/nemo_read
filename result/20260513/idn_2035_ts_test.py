"""Test: in Indonesia 2035, does Unmet Load have a 'distinct supply curve'
that drives the peak, while real demand stays flat?

Plus: where does the 1,828 PJ overproduction go? Candidates: storage
charging, inter-region transmission, or sub-region node demand fed
outside the central commodity balance.
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 26.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v044")
ELEC = 'Electricity output from "Centralized Electricity Generation" [LEAP ID:1]'


def main() -> int:
    db = NemoDB(str(DB_PATH))
    Y = "2035"

    # Year split (timeslice widths)
    ys = db.query(f"SELECT l, val FROM YearSplit WHERE y='{Y}'").set_index("l")["val"]

    # Per-tech production by timeslice for Indonesia 2035 on central elec bus
    pbt = db.query(f"SELECT r, l, t, f, y, val FROM vproductionbytechnology "
                   f"WHERE r='R1' AND y='{Y}'")
    pbt = decode_dims(pbt, db)
    pbt_elec = pbt[pbt["fuel_name"] == ELEC].copy()

    def bucket(name: str) -> str:
        if "Unmet Load" in name: return "Unmet Load (slack)"
        n = name.lower()
        if "coal" in n: return "Coal"
        if "gas" in n: return "Gas"
        if "battery" in n or "batteries" in n: return "Battery (discharge)"
        if "pumped" in n: return "Pumped Hydro (discharge)"
        return "Other real"

    pbt_elec["bucket"] = pbt_elec["tech_name"].apply(bucket)
    sup_ts = (
        pbt_elec.groupby(["l", "bucket"])["val"].sum()
        .unstack("bucket").fillna(0.0)
    )
    # Convert PJ-per-timeslice to continuous-GW: PJ / (yearsplit * 8760 hr) / 3.6e-3
    hours = ys * 8760
    sup_gw = sup_ts.div(hours, axis=0) / 3.6e-3

    # Use by tech (per timeslice) on central elec bus — this is the demand-side
    ubt = db.query(f"SELECT r, l, t, f, y, val FROM vusebytechnology "
                   f"WHERE r='R1' AND y='{Y}'")
    ubt = decode_dims(ubt, db)
    ubt_elec = ubt[ubt["fuel_name"] == ELEC].copy()

    def dbucket(name: str) -> str:
        n = (name or "").lower()
        if "electricity" == n: return "Electricity T&D (end-use)"
        if "battery" in n or "batteries" in n: return "Battery (charge)"
        if "pumped" in n: return "Pumped Hydro (charge)"
        if "electrolysis" in n: return "PEM Electrolysis"
        return f"Other ({name})"

    ubt_elec["bucket"] = ubt_elec["tech_name"].apply(dbucket)
    dem_ts = (
        ubt_elec.groupby(["l", "bucket"])["val"].sum()
        .unstack("bucket").fillna(0.0)
    )
    dem_gw = dem_ts.div(hours, axis=0) / 3.6e-3

    # Combine into one wide table per timeslice
    sup_gw.columns = [f"SUP: {c}" for c in sup_gw.columns]
    dem_gw.columns = [f"DEM: {c}" for c in dem_gw.columns]
    combo = pd.concat([sup_gw, dem_gw], axis=1).fillna(0.0)
    combo["SUP_total_GW"] = sup_gw.sum(axis=1)
    combo["DEM_total_GW"] = dem_gw.sum(axis=1)
    combo["GAP_GW"] = combo["SUP_total_GW"] - combo["DEM_total_GW"]
    combo["YearSplit_hr"] = hours
    # Sort by supply-total descending to see peak first
    combo_sorted = combo.sort_values("SUP_total_GW", ascending=False)
    combo_sorted.to_csv(OUT_DIR / "idn_2035_ts_supply_demand.csv")
    print("=== Indonesia 2035 — per-timeslice supply mix vs demand mix (continuous GW) ===")
    print("(showing top-5 supply timeslices + bottom-5 supply timeslices)")
    keep_cols = [c for c in combo_sorted.columns
                 if c.startswith("SUP:") or c.startswith("DEM:")
                 or c in ("SUP_total_GW", "DEM_total_GW", "GAP_GW")]
    with pd.option_context("display.width", 220, "display.max_columns", 20,
                           "display.float_format", "{:.1f}".format):
        print("\n--- Top 5 supply timeslices ---")
        print(combo_sorted[keep_cols].head(5).round(1).to_string())
        print("\n--- Bottom 5 supply timeslices ---")
        print(combo_sorted[keep_cols].tail(5).round(1).to_string())

    # Peak/avg ratio per stream
    print("\n=== Peak/avg ratio by stream (GW peak / GW continuous-avg) ===")
    for col in sup_gw.columns:
        peak = sup_gw[col].max()
        annual_PJ = (combo[col] * 3.6e-3 * hours).sum()
        cont_GW = annual_PJ / (8760 * 3.6e-3)
        if cont_GW > 0:
            print(f"  {col:40s} peak={peak:.1f} GW  cont={cont_GW:.1f} GW  ratio={peak/cont_GW:.2f}x")
    for col in dem_gw.columns:
        peak = dem_gw[col].max()
        annual_PJ = (combo[col] * 3.6e-3 * hours).sum()
        cont_GW = annual_PJ / (8760 * 3.6e-3)
        if cont_GW > 0:
            print(f"  {col:40s} peak={peak:.1f} GW  cont={cont_GW:.1f} GW  ratio={peak/cont_GW:.2f}x")

    # Where does the 1828 PJ gap go? Check transmission + look for nodal demand
    trans = db.query(f"SELECT n1, n2, l, y, val FROM vtransmissionbyline "
                     f"WHERE y='{Y}'")
    if not trans.empty:
        # Identify Indonesia nodes (N13-N16)
        nodes = db.query("SELECT val, desc FROM NODE")
        idn_nodes = nodes[nodes["desc"].str.startswith("Indonesia", na=False)]["val"].tolist()
        print(f"\n=== Inter-node transmission involving Indonesia nodes ({idn_nodes}), 2035 ===")
        trans_idn = trans[trans["n1"].isin(idn_nodes) | trans["n2"].isin(idn_nodes)]
        if trans_idn.empty:
            print("  (no transmission rows involving Indonesia nodes)")
        else:
            trans_sum = trans_idn.groupby(["n1", "n2"])["val"].sum().sort_values(ascending=False)
            print(trans_sum.head(10).to_string())

    # Nodal demand at Indonesia nodes
    ndd = db.query("SELECT n, f, y, val FROM NodalDistributionDemand")
    ndd = decode_dims(ndd, db)
    if not ndd.empty:
        idn_ndd = ndd[ndd["node_name"].str.startswith("Indonesia", na=False)
                      & (ndd["y"] == Y)]
        if not idn_ndd.empty:
            print(f"\n=== Indonesia NodalDistributionDemand in 2035 ===")
            print(idn_ndd[["node_name", "fuel_name", "val"]].to_string(index=False))
        else:
            print(f"\n(no NodalDistributionDemand rows for Indonesia 2035)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
