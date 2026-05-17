"""Build all supply-side digestion CSVs for v0.45 (NEMO_25 27.sqlite).

Produces 9 CSVs in mailbox/20260513/results_v045/:

  1. tech_capacity.csv          per (region, tech, year)
  2. fuel_balance.csv           per (region, fuel, year)
  3. trade_interregion.csv      per (origin, destination, fuel, year)
  4. transmission_internode.csv per (from_node, to_node, year)
  5. emissions_by_tech.csv      per (region, tech, emission, year)
  6. costs_by_tech.csv          per (region, tech, year)
  7. timeslice_profiles.csv     per (region, fuel, timeslice, year)
                                  — electricity output fuels only
  8. storage_operation.csv      per (region, storage_tech, timeslice, year)
  9. renewable_share.csv        per (region, year)
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 27.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v045")
ELEC_PREFIX = "Electricity output"


def clean_fuel_name(name: str) -> str:
    """Strip the verbose ' from "..." [LEAP ID:N]' suffix and the
    'output from'/'input to' prefix wrapping for human readability.
    """
    if not isinstance(name, str):
        return name
    # Take portion up to ' [LEAP ID'
    cut = name.split(' [LEAP ID')[0].strip()
    # Strip all surrounding/embedded quotes for readability
    cut = cut.replace('"', '')
    return cut


def main() -> int:
    db = NemoDB(str(DB_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"DB: {DB_PATH}  version={db.version}")

    # ============================================================
    # 1. tech_capacity.csv
    # ============================================================
    print("\n[1] tech_capacity.csv")
    oar = db.query("SELECT r, t, f, m, y, val FROM OutputActivityRatio WHERE val > 0")
    oar = decode_dims(oar, db)
    elec_oar = oar[oar["fuel_name"].str.startswith(ELEC_PREFIX, na=False)]
    power_techs = set(elec_oar["t"].unique())
    out_fuel_map = (
        elec_oar.groupby("t")["fuel_name"]
        .agg(lambda s: ", ".join(sorted(set(s))))
        .to_dict()
    )

    cap = db.query("SELECT r, t, y, val FROM vtotalcapacityannual")
    new = db.query("SELECT r, t, y, val FROM vnewcapacity")
    res = db.query("SELECT r, t, y, val FROM ResidualCapacity")
    pbta = db.query("SELECT r, t, f, y, val FROM vproductionbytechnologyannual")

    cap = decode_dims(cap, db).rename(columns={"val": "capacity_GW"})
    new = decode_dims(new, db).rename(columns={"val": "new_capacity_GW"})
    res = decode_dims(res, db).rename(columns={"val": "residual_GW"})
    pbta = decode_dims(pbta, db)

    # Filter to power-gen techs
    cap = cap[cap["t"].isin(power_techs)]
    new = new[new["t"].isin(power_techs)]
    res = res[res["t"].isin(power_techs)]
    prod = (
        pbta[pbta["t"].isin(power_techs)]
        .groupby(["r", "region_name", "t", "tech_name", "y"])["val"].sum()
        .reset_index().rename(columns={"val": "production_PJ"})
    )

    keys = ["r", "region_name", "t", "tech_name", "y"]
    tc = (
        cap[keys + ["capacity_GW"]]
        .merge(res[keys + ["residual_GW"]], on=keys, how="outer")
        .merge(new[keys + ["new_capacity_GW"]], on=keys, how="outer")
        .merge(prod[keys + ["production_PJ"]], on=keys, how="outer")
        .fillna({"capacity_GW": 0.0, "residual_GW": 0.0,
                 "new_capacity_GW": 0.0, "production_PJ": 0.0})
    )
    # Drop all-zero rows
    nz = (tc[["capacity_GW", "residual_GW", "new_capacity_GW", "production_PJ"]].sum(axis=1) != 0)
    tc = tc[nz].copy()
    tc["output_fuel"] = tc["t"].map(out_fuel_map).apply(clean_fuel_name)
    tc = tc[[
        "region_name", "tech_name", "output_fuel", "y",
        "capacity_GW", "residual_GW", "new_capacity_GW", "production_PJ",
    ]].rename(columns={"region_name": "region", "y": "year"})
    tc = tc.sort_values(["region", "tech_name", "year"]).reset_index(drop=True)
    p = OUT_DIR / "tech_capacity.csv"
    tc.to_csv(p, index=False, float_format="%.4f")
    print(f"  wrote {p}  rows={len(tc)}  techs={tc['tech_name'].nunique()}  regions={tc['region'].nunique()}")

    # ============================================================
    # 2. fuel_balance.csv
    # ============================================================
    print("\n[2] fuel_balance.csv")
    use_a = db.query("SELECT r, t, f, y, val FROM vusebytechnologyannual")
    use_a = decode_dims(use_a, db)
    fuel_prod = pbta.groupby(["r", "region_name", "f", "fuel_name", "y"])["val"].sum().reset_index().rename(columns={"val": "production_PJ"})
    fuel_use = use_a.groupby(["r", "region_name", "f", "fuel_name", "y"])["val"].sum().reset_index().rename(columns={"val": "use_PJ"})
    fb = (
        fuel_prod.merge(fuel_use,
                        on=["r", "region_name", "f", "fuel_name", "y"], how="outer")
        .fillna({"production_PJ": 0.0, "use_PJ": 0.0})
    )
    nz = (fb["production_PJ"] != 0) | (fb["use_PJ"] != 0)
    fb = fb[nz].copy()
    fb["fuel_name_clean"] = fb["fuel_name"].apply(clean_fuel_name)
    fb["net_PJ"] = fb["production_PJ"] - fb["use_PJ"]
    fb = fb[[
        "region_name", "fuel_name_clean", "fuel_name", "y",
        "production_PJ", "use_PJ", "net_PJ",
    ]].rename(columns={"region_name": "region", "fuel_name_clean": "fuel",
                       "fuel_name": "fuel_name_full", "y": "year"})
    fb = fb.sort_values(["region", "fuel", "year"]).reset_index(drop=True)
    p = OUT_DIR / "fuel_balance.csv"
    fb.to_csv(p, index=False, float_format="%.4f")
    print(f"  wrote {p}  rows={len(fb)}  fuels={fb['fuel'].nunique()}  regions={fb['region'].nunique()}")

    # ============================================================
    # 3. trade_interregion.csv
    # ============================================================
    print("\n[3] trade_interregion.csv")
    trade = db.query("SELECT r, rr, f, y, val FROM vtradeannual WHERE val != 0")
    trade = decode_dims(trade, db)
    # decode_dims handles 'r' and 'f' but not 'rr' — manual join
    regions = db.query("SELECT val, desc FROM REGION").rename(
        columns={"val": "rr", "desc": "destination_region"}
    )
    trade = trade.merge(regions, on="rr", how="left")
    trade["fuel"] = trade["fuel_name"].apply(clean_fuel_name)
    trade = trade[[
        "region_name", "destination_region", "fuel", "fuel_name", "y", "val",
    ]].rename(columns={
        "region_name": "origin_region", "fuel_name": "fuel_name_full",
        "y": "year", "val": "traded_PJ",
    })
    trade = trade.sort_values(["origin_region", "destination_region", "fuel", "year"]).reset_index(drop=True)
    p = OUT_DIR / "trade_interregion.csv"
    trade.to_csv(p, index=False, float_format="%.4f")
    print(f"  wrote {p}  rows={len(trade)}  region-pairs={trade.groupby(['origin_region','destination_region']).ngroups}  fuels={trade['fuel'].nunique()}")

    # ============================================================
    # 4. transmission_internode.csv
    # ============================================================
    print("\n[4] transmission_internode.csv")
    tlines = db.query("SELECT id, n1, n2, f, maxflow FROM TransmissionLine")
    tlines = tlines.rename(columns={"id": "tr"})
    tbl = db.query("SELECT tr, l, f, y, val FROM vtransmissionbyline WHERE val != 0")
    # Join to get node names + fuel name
    tbl = tbl.merge(tlines[["tr", "n1", "n2"]], on="tr", how="left")
    # Decode nodes manually (decode_dims uses 'n', not 'n1'/'n2')
    nodes = db.query("SELECT val, desc FROM NODE")
    n1m = nodes.rename(columns={"val": "n1", "desc": "from_node"})
    n2m = nodes.rename(columns={"val": "n2", "desc": "to_node"})
    tbl = tbl.merge(n1m, on="n1", how="left").merge(n2m, on="n2", how="left")
    tbl = decode_dims(tbl, db)
    tbl["fuel"] = tbl["fuel_name"].apply(clean_fuel_name)
    # Map node to region (rough): everything before the first space is the AMS prefix
    def node_region(s: str) -> str:
        if not isinstance(s, str): return ""
        parts = s.split()
        if not parts: return ""
        return parts[0]
    tbl["from_region"] = tbl["from_node"].apply(node_region)
    tbl["to_region"] = tbl["to_node"].apply(node_region)
    tbl["within_region"] = tbl["from_region"] == tbl["to_region"]
    # Aggregate to annual + peak
    annual = (
        tbl.groupby(["tr", "from_node", "to_node", "from_region", "to_region",
                     "within_region", "fuel", "fuel_name", "y"])
        .agg(annual_PJ=("val", lambda s: (s * 0).sum() + s.sum()),  # placeholder
             peak_rate=("val", "max"),
             min_rate=("val", "min"))
        .reset_index()
    )
    # Convert val (per-timeslice rate) → annual using YearSplit
    ys = db.query("SELECT l, y, val FROM YearSplit").rename(columns={"val": "ys"})
    tbl2 = tbl.merge(ys, on=["l", "y"], how="left")
    tbl2["energy_PJ"] = tbl2["val"] * tbl2["ys"]
    annual_real = (
        tbl2.groupby(["tr", "from_node", "to_node", "from_region", "to_region",
                      "within_region", "fuel", "fuel_name", "y"])
        .agg(annual_PJ=("energy_PJ", "sum"),
             peak_GW=("val", lambda s: s.max() / 31.536))
        .reset_index()
    )
    annual_real = annual_real.rename(columns={"y": "year"})
    annual_real = annual_real.sort_values(["from_region", "to_region", "from_node", "to_node", "year"]).reset_index(drop=True)
    p = OUT_DIR / "transmission_internode.csv"
    cols_out = ["from_region", "to_region", "within_region", "from_node", "to_node",
                "fuel", "year", "annual_PJ", "peak_GW", "fuel_name"]
    annual_real[cols_out].rename(columns={"fuel_name": "fuel_name_full"}).to_csv(p, index=False, float_format="%.4f")
    print(f"  wrote {p}  rows={len(annual_real)}  lines={annual_real['tr'].nunique()}")

    # ============================================================
    # 5. emissions_by_tech.csv
    # ============================================================
    print("\n[5] emissions_by_tech.csv")
    em = db.query("SELECT r, t, e, y, val FROM vannualtechnologyemission WHERE val != 0")
    em = decode_dims(em, db)
    em = em[["region_name", "tech_name", "emission_name", "y", "val"]].rename(
        columns={"region_name": "region", "y": "year", "val": "annual_tonnes"}
    )
    em = em.sort_values(["region", "tech_name", "emission_name", "year"]).reset_index(drop=True)
    p = OUT_DIR / "emissions_by_tech.csv"
    em.to_csv(p, index=False, float_format="%.4f")
    print(f"  wrote {p}  rows={len(em)}  emissions={em['emission_name'].nunique()}  techs={em['tech_name'].nunique()}")

    # ============================================================
    # 6. costs_by_tech.csv
    # ============================================================
    print("\n[6] costs_by_tech.csv")
    capex = db.query("SELECT r, t, y, val FROM vcapitalinvestment").rename(columns={"val": "capital_inv"})
    fixed = db.query("SELECT r, t, y, val FROM vannualfixedoperatingcost").rename(columns={"val": "fixed_OM"})
    var = db.query("SELECT r, t, y, val FROM vannualvariableoperatingcost").rename(columns={"val": "variable_OM"})
    dcapex = db.query("SELECT r, t, y, val FROM vdiscountedcapitalinvestment").rename(columns={"val": "disc_capex"})
    dopex = db.query("SELECT r, t, y, val FROM vdiscountedoperatingcost").rename(columns={"val": "disc_opex"})
    dsalv = db.query("SELECT r, t, y, val FROM vdiscountedsalvagevalue").rename(columns={"val": "disc_salvage"})
    costs = capex
    for other in (fixed, var, dcapex, dopex, dsalv):
        costs = costs.merge(other, on=["r", "t", "y"], how="outer")
    costs = costs.fillna(0.0)
    costs = decode_dims(costs, db)
    costs = costs[["region_name", "tech_name", "y", "capital_inv", "fixed_OM",
                   "variable_OM", "disc_capex", "disc_opex", "disc_salvage"]].rename(
        columns={"region_name": "region", "y": "year"}
    )
    # Drop all-zero rows
    cost_cols = ["capital_inv", "fixed_OM", "variable_OM", "disc_capex", "disc_opex", "disc_salvage"]
    nz = costs[cost_cols].abs().sum(axis=1) != 0
    costs = costs[nz].sort_values(["region", "tech_name", "year"]).reset_index(drop=True)
    p = OUT_DIR / "costs_by_tech.csv"
    costs.to_csv(p, index=False, float_format="%.4f")
    print(f"  wrote {p}  rows={len(costs)}  techs={costs['tech_name'].nunique()}")

    # ============================================================
    # 7. timeslice_profiles.csv — electricity output fuels
    # ============================================================
    print("\n[7] timeslice_profiles.csv (electricity fuels only)")
    elec_fuel_ids = set(
        elec_oar.merge(db.query("SELECT val as f, desc as fname FROM FUEL"),
                       on="f", how="left")["f"]
    )
    rop = db.query("SELECT r, l, f, y, val FROM vrateofproduction")
    rou = db.query("SELECT r, l, f, y, val FROM vrateofuse")
    rop = decode_dims(rop, db)
    rou = decode_dims(rou, db)
    # Filter to electricity output fuels
    rop = rop[rop["fuel_name"].str.startswith(ELEC_PREFIX, na=False)].copy()
    rou = rou[rou["fuel_name"].str.startswith(ELEC_PREFIX, na=False)].copy()
    # Timeslice descriptions
    tsd = db.query("SELECT val as l, desc FROM TIMESLICE")
    def split_ts(desc):
        if not isinstance(desc, str) or ":" not in desc:
            return ("?", -1)
        s, h = desc.split(":")
        return s.strip(), int(h.strip().replace("Hr", "").strip())
    tsd["season"], tsd["hour"] = zip(*tsd["desc"].apply(split_ts))
    rop = rop.merge(tsd[["l", "season", "hour"]], on="l", how="left")
    rou = rou.merge(tsd[["l", "season", "hour"]], on="l", how="left")
    rop["GW_continuous_equiv"] = rop["val"] / 31.536
    rou["GW_continuous_equiv"] = rou["val"] / 31.536
    sup = rop.rename(columns={"GW_continuous_equiv": "supply_GW"})[
        ["region_name", "fuel_name", "season", "hour", "y", "supply_GW"]]
    dem = rou.rename(columns={"GW_continuous_equiv": "demand_GW"})[
        ["region_name", "fuel_name", "season", "hour", "y", "demand_GW"]]
    ts_combo = sup.merge(dem, on=["region_name", "fuel_name", "season", "hour", "y"], how="outer").fillna(0.0)
    ts_combo["fuel"] = ts_combo["fuel_name"].apply(clean_fuel_name)
    ts_combo = ts_combo[["region_name", "fuel", "season", "hour", "y",
                          "supply_GW", "demand_GW", "fuel_name"]].rename(
        columns={"region_name": "region", "y": "year", "fuel_name": "fuel_name_full"}
    )
    ts_combo = ts_combo.sort_values(["region", "fuel", "year", "season", "hour"]).reset_index(drop=True)
    p = OUT_DIR / "timeslice_profiles.csv"
    ts_combo.to_csv(p, index=False, float_format="%.4f")
    print(f"  wrote {p}  rows={len(ts_combo)}  regions={ts_combo['region'].nunique()}")

    # ============================================================
    # 8. storage_operation.csv — battery + pumped hydro + CAES + flow battery
    # ============================================================
    print("\n[8] storage_operation.csv")
    storage_kws = ["battery", "batteries", "pumped", "caes", "vrb flow"]
    techs_all = db.query("SELECT val as t, desc as tech_name FROM TECHNOLOGY")
    storage_techs = techs_all[techs_all["tech_name"].str.lower().apply(
        lambda n: any(k in n for k in storage_kws)
    )]
    storage_tids = set(storage_techs["t"].tolist())
    # Get use (charge) + production (discharge) per timeslice for storage techs
    use_t = db.query("SELECT r, l, t, f, y, val FROM vusebytechnology")
    prod_t = db.query("SELECT r, l, t, f, y, val FROM vproductionbytechnology")
    use_t = use_t[use_t["t"].isin(storage_tids)]
    prod_t = prod_t[prod_t["t"].isin(storage_tids)]
    use_t = decode_dims(use_t, db).rename(columns={"val": "charge_PJ"})
    prod_t = decode_dims(prod_t, db).rename(columns={"val": "discharge_PJ"})
    use_t = use_t.merge(tsd[["l", "season", "hour"]], on="l", how="left")
    prod_t = prod_t.merge(tsd[["l", "season", "hour"]], on="l", how="left")
    # Reduce to one row per (r, t, season, hour, y) — sum across fuels
    use_g = use_t.groupby(["region_name", "tech_name", "season", "hour", "y"])["charge_PJ"].sum().reset_index()
    prod_g = prod_t.groupby(["region_name", "tech_name", "season", "hour", "y"])["discharge_PJ"].sum().reset_index()
    storage = use_g.merge(prod_g, on=["region_name", "tech_name", "season", "hour", "y"], how="outer").fillna(0.0)
    storage["net_PJ"] = storage["discharge_PJ"] - storage["charge_PJ"]
    storage = storage[(storage["charge_PJ"] != 0) | (storage["discharge_PJ"] != 0)]
    storage = storage[["region_name", "tech_name", "season", "hour", "y",
                       "charge_PJ", "discharge_PJ", "net_PJ"]].rename(
        columns={"region_name": "region", "y": "year"}
    )
    storage = storage.sort_values(["region", "tech_name", "year", "season", "hour"]).reset_index(drop=True)
    p = OUT_DIR / "storage_operation.csv"
    storage.to_csv(p, index=False, float_format="%.4f")
    print(f"  wrote {p}  rows={len(storage)}  storage_techs={storage['tech_name'].nunique()}")

    # ============================================================
    # 9. renewable_share.csv
    # ============================================================
    print("\n[9] renewable_share.csv")
    retag = db.query("SELECT r, t, y, val FROM RETagTechnology WHERE val != 0")
    re_tids_by_ry = (
        retag.groupby(["r", "y"])["t"].apply(set).to_dict()
    )
    # Production by tech on the central electricity bus
    elec_prod = pbta[pbta["fuel_name"].str.startswith(ELEC_PREFIX, na=False)].copy()
    rows = []
    for (r, y), g in elec_prod.groupby(["r", "y"]):
        total = g["val"].sum()
        re_set = re_tids_by_ry.get((r, y), set())
        re_prod = g[g["t"].isin(re_set)]["val"].sum()
        rows.append({"r": r, "year": y,
                     "total_elec_PJ": total,
                     "re_elec_PJ": re_prod,
                     "fossil_elec_PJ": total - re_prod,
                     "re_share_pct": (re_prod / total * 100) if total > 0 else 0.0})
    rs = pd.DataFrame(rows)
    rs = rs.merge(db.query("SELECT val as r, desc as region FROM REGION"), on="r", how="left")
    rs = rs[["region", "year", "total_elec_PJ", "re_elec_PJ", "fossil_elec_PJ", "re_share_pct"]]
    rs = rs.sort_values(["region", "year"]).reset_index(drop=True)
    p = OUT_DIR / "renewable_share.csv"
    rs.to_csv(p, index=False, float_format="%.4f")
    print(f"  wrote {p}  rows={len(rs)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
