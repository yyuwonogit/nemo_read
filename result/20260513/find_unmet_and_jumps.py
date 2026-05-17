"""Identify (1) Unmet Load dispatch and (2) physically implausible capacity
jumps from v0.43 results (feas/NEMO_25 24.sqlite).

Outputs into mailbox/20260513/results_v043/:
  - unmet_load_annual.csv      — every (region, tech, year) with Unmet Load
                                  production > 0, PJ + GW
  - capacity_jumps.csv         — every (region, tech, year) where new
                                  capacity exceeds tech-category absolute
                                  threshold OR > 5x prior stock
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 27.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v045")

# Absolute 5-year build-rate thresholds, in GW per (AMS, tech, milestone year)
THRESHOLDS_GW = {
    "Nuclear": 2.0,
    "Coal": 15.0,
    "CCGT": 15.0,
    "OCGT": 15.0,
    "Gas": 15.0,
    "Large Hydro": 5.0,
    "Geothermal": 2.0,
    "Solar PV": 50.0,
    "Solar": 50.0,
    "Wind Offshore": 10.0,
    "Wind Onshore": 30.0,
    "Wind": 30.0,
    "Biomass": 5.0,
    "Waste": 5.0,
}
DEFAULT_THRESHOLD_GW = 20.0  # fallback for unclassified power techs
STOCK_MULTIPLIER = 5.0


def categorise(tech_name: str) -> tuple[str, float]:
    """Return (category, threshold_GW). First key in THRESHOLDS_GW whose
    substring appears in tech_name wins; longer keys first."""
    if not isinstance(tech_name, str):
        return ("Unclassified", DEFAULT_THRESHOLD_GW)
    name = tech_name
    # Prefer longer, more-specific keys
    for key in sorted(THRESHOLDS_GW.keys(), key=len, reverse=True):
        if key in name:
            return (key, THRESHOLDS_GW[key])
    return ("Unclassified", DEFAULT_THRESHOLD_GW)


def main() -> int:
    if not DB_PATH.exists():
        print(f"[FAIL] {DB_PATH} not found", file=sys.stderr)
        return 1
    db = NemoDB(str(DB_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- 1. Unmet Load annual ----------
    prod = db.query('SELECT * FROM vproductionbytechnologyannual')
    cap = db.query('SELECT * FROM vtotalcapacityannual')
    prod = decode_dims(prod, db)
    cap = decode_dims(cap, db)

    unmet_prod = prod[
        prod["tech_name"].str.contains("Unmet Load", case=False, na=False)
        & (prod["val"] > 0)
    ].copy()
    unmet_prod = unmet_prod.rename(columns={"val": "unmet_production_PJ"})
    unmet_cap = cap[
        cap["tech_name"].str.contains("Unmet Load", case=False, na=False)
        & (cap["val"] > 0)
    ].copy()
    unmet_cap = unmet_cap.rename(columns={"val": "unmet_capacity_GW"})

    # Join on (r, t, y)
    keys = ["r", "t", "y", "region_name", "tech_name"]
    out_unmet = unmet_prod[keys + ["unmet_production_PJ"]].merge(
        unmet_cap[keys + ["unmet_capacity_GW"]],
        on=keys,
        how="outer",
    ).fillna({"unmet_production_PJ": 0.0, "unmet_capacity_GW": 0.0})
    out_unmet = out_unmet.sort_values(
        ["unmet_production_PJ", "region_name", "y"],
        ascending=[False, True, True],
    )
    p = OUT_DIR / "unmet_load_annual.csv"
    out_unmet.to_csv(p, index=False)
    print(f"[unmet] wrote {p}  rows={len(out_unmet)}")
    print(f"[unmet] total unmet production across model run: "
          f"{out_unmet['unmet_production_PJ'].sum():.2f} PJ")
    if len(out_unmet) > 0:
        agg_by_amy = (
            out_unmet.groupby(["region_name", "y"])["unmet_production_PJ"]
            .sum().reset_index()
            .sort_values("unmet_production_PJ", ascending=False)
        )
        print("\n[unmet] top 15 (region, year) by total unmet PJ:")
        print(agg_by_amy.head(15).to_string(index=False))

    # ---------- 2. Capacity jumps ----------
    newcap = db.query('SELECT * FROM vnewcapacity')
    newcap = decode_dims(newcap, db)

    # Drop Unmet Load + storage techs from the jump check
    newcap = newcap[
        ~newcap["tech_name"].str.contains("Unmet Load", case=False, na=False)
    ].copy()
    storage_keywords = ["Battery", "Batteries", "Pumped", "Storage"]
    sk_mask = newcap["tech_name"].fillna("").apply(
        lambda n: any(k in n for k in storage_keywords)
    )
    newcap = newcap[~sk_mask].copy()

    # Prior stock = total capacity at year y-5 (or 0 if no prior milestone)
    cap_all = cap.copy()
    cap_all["y_int"] = cap_all["y"].astype(int)
    newcap["y_int"] = newcap["y"].astype(int)
    cap_lookup = cap_all.set_index(["r", "t", "y_int"])["val"]

    def prior_stock(row) -> float:
        yprev = row["y_int"] - 5
        try:
            return float(cap_lookup.loc[(row["r"], row["t"], yprev)])
        except KeyError:
            return 0.0

    newcap["prior_stock_GW"] = newcap.apply(prior_stock, axis=1)
    newcap["new_GW"] = newcap["val"]
    newcap[["category", "threshold_GW"]] = newcap["tech_name"].apply(
        lambda n: pd.Series(categorise(n))
    )
    newcap["absolute_flag"] = newcap["new_GW"] > newcap["threshold_GW"]
    newcap["multiplier"] = newcap.apply(
        lambda r: (r["new_GW"] / r["prior_stock_GW"])
        if r["prior_stock_GW"] > 0 else float("inf"),
        axis=1,
    )
    # Stock flag: only meaningful when there IS a prior stock to multiply
    # against, AND the absolute new_GW is non-trivial (>1 GW).
    newcap["stock_flag"] = (
        (newcap["prior_stock_GW"] > 0)
        & (newcap["multiplier"] > STOCK_MULTIPLIER)
        & (newcap["new_GW"] > 1.0)
    )
    flagged = newcap[
        (newcap["absolute_flag"]) | (newcap["stock_flag"])
    ].copy()
    flagged = flagged[
        ["r", "region_name", "t", "tech_name", "category",
         "y", "new_GW", "prior_stock_GW", "multiplier",
         "threshold_GW", "absolute_flag", "stock_flag"]
    ].sort_values(
        ["absolute_flag", "stock_flag", "new_GW"],
        ascending=[False, False, False],
    )
    p = OUT_DIR / "capacity_jumps.csv"
    flagged.to_csv(p, index=False)
    print(f"\n[jumps] wrote {p}  rows={len(flagged)}")
    print(f"[jumps] absolute-threshold flags: "
          f"{int(flagged['absolute_flag'].sum())}")
    print(f"[jumps] stock-multiplier flags:   "
          f"{int(flagged['stock_flag'].sum())}")
    if len(flagged) > 0:
        print("\n[jumps] top 20 by new_GW:")
        cols = ["region_name", "tech_name", "category", "y",
                "new_GW", "prior_stock_GW", "multiplier", "threshold_GW"]
        print(flagged[cols].head(20).to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
