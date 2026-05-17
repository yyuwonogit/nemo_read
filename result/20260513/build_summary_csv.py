"""Build a single readable CSV of (region, entity, year, metrics) covering
all power-generation technologies and all active fuels — using LEAP names
throughout, no NEMO codes.

Power-gen tech filter: techs with an OAR row outputting to a fuel whose
name contains "Electricity".

Output: mailbox/20260513/results_v045/summary_region_tech_fuel.csv
Columns: region, entity_type, entity_name, category, year,
         capacity_GW, new_capacity_GW, production_PJ, use_PJ
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 27.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v045")
ELEC_PREFIX = "Electricity output"  # only actual electricity output fuels


def tech_category(name: str) -> str:
    n = (name or "").lower()
    if "unmet load" in n: return "Unmet Load (slack)"
    if "solar pv rooftop" in n: return "Solar PV Rooftop"
    if "solar pv" in n or "solar floating" in n: return "Solar PV"
    if "solar csp" in n: return "Solar CSP"
    if "wind onshore" in n: return "Wind Onshore"
    if "wind offshore" in n: return "Wind Offshore"
    if "small hydro" in n: return "Small Hydro"
    if "large hydro" in n: return "Large Hydro"
    if "pumped" in n: return "Pumped Hydro Storage"
    if "geothermal flash" in n: return "Geothermal Flash"
    if "geothermal orc" in n: return "Geothermal ORC"
    if "geothermal" in n: return "Geothermal (other)"
    if "nuclear lwr" in n: return "Nuclear LWR"
    if "nuclear sfr" in n: return "Nuclear SFR"
    if "nuclear smr" in n: return "Nuclear SMR"
    if "biomass gasification with ccs" in n: return "Biomass Gasification (with CCS)"
    if "biomass gasification" in n: return "Biomass Gasification"
    if "biomass other" in n: return "Biomass Other"
    if "biogas" in n: return "Biogas"
    if "municipal solid waste" in n or " msw" in n: return "MSW"
    if "waste" in n: return "Waste-to-Energy"
    if "coal ultrasupercritical" in n or "coal ultra supercritical" in n: return "Coal Ultrasupercritical"
    if "coal supercritical ccs" in n or "coal supercritical with ccs" in n: return "Coal Supercritical (with CCS)"
    if "coal supercritical" in n: return "Coal Supercritical"
    if "coal subcritical" in n: return "Coal Subcritical"
    if "coal gasification with ccs" in n: return "Coal Gasification (with CCS)"
    if "coal gasification" in n: return "Coal Gasification"
    if "igcc" in n: return "Coal IGCC"
    if "gas combined cycle with ccs" in n: return "Gas CCGT (with CCS)"
    if "gas combined cycle" in n: return "Gas CCGT"
    if "gas turbine" in n: return "Gas Open-Cycle Turbine"
    if "gas engine" in n: return "Gas Engine"
    if "gas steam" in n: return "Gas Steam"
    if "tidal" in n: return "Tidal"
    if "wave" in n: return "Wave"
    if "lithium" in n or "battery" in n or "batteries" in n: return "Battery Storage"
    if "vrb flow" in n: return "VRB Flow Battery"
    if "caes" in n: return "CAES"
    if "h2 fuel cell" in n: return "H2 Fuel Cell"
    if "pem electrolysis" in n: return "PEM Electrolysis"
    if "anaerobic digestion" in n: return "Anaerobic Digestion (biogas)"
    if name == "Electricity": return "Electricity T&D"
    if "smr" == n.strip() or "smr with ccs" in n: return "SMR (Steam Methane Reforming, H2)"
    if "hydrogen" in n: return "Hydrogen"
    if "diesel" in n: return "Diesel (oil-fired)"
    if "fuel oil" in n: return "Fuel Oil"
    return "Other power"


def fuel_category(name: str) -> str:
    n = (name or "").lower()
    if "electricity output" in n:
        if "centralized electricity generation" in n: return "Electricity (central bus)"
        if "transmission and distribution" in n: return "Electricity (post-T&D)"
        if "energy sector own use" in n: return "Electricity (post-ESOU end-use)"
        return "Electricity (other)"
    if "natural gas" in n: return "Natural Gas"
    if "lng" in n: return "LNG"
    if "lpg" in n: return "LPG"
    if "coal bituminous" in n: return "Coal Bituminous"
    if "coal sub bituminous" in n: return "Coal Sub-Bituminous"
    if "coal lignite" in n: return "Coal Lignite"
    if "crude oil" in n: return "Crude Oil"
    if "diesel output" in n or "blended diesel" in n: return "Diesel"
    if "gasoline" in n: return "Gasoline"
    if "jet kerosene" in n or "kerosene" in n: return "Kerosene/Jet"
    if "residual fuel oil" in n: return "Residual Fuel Oil"
    if "biodiesel" in n: return "Biodiesel"
    if "bioethanol" in n or "ethanol" in n: return "Bioethanol"
    if "sustainable aviation fuel" in n or "saf" in n: return "Sustainable Aviation Fuel"
    if "biomass" in n: return "Biomass"
    if "biogas" in n or "biomethane" in n: return "Biogas/Biomethane"
    if "palm oil" in n: return "Palm Oil"
    if "coconut oil" in n: return "Coconut Oil"
    if "cassava" in n: return "Cassava"
    if "molasses" in n or "sugarcane" in n: return "Sugarcane/Molasses"
    if "corn" in n: return "Corn"
    if "pome" in n: return "POME"
    if "solar input" in n: return "Solar resource"
    if "wind input" in n: return "Wind resource"
    if "geothermal input" in n: return "Geothermal resource"
    if "hydro input" in n: return "Hydro resource"
    if "tidal input" in n: return "Tidal resource"
    if "wave input" in n: return "Wave resource"
    if "nuclear input" in n: return "Nuclear fuel"
    if "ammonia" in n: return "Ammonia"
    if "hydrogen" in n: return "Hydrogen"
    if "municipal solid waste" in n or "msw" in n: return "MSW"
    if "non energy" in n: return "Non Energy (slack input)"
    if "domestic biogas" in n: return "Domestic Biogas"
    return "Other fuel"


def main() -> int:
    db = NemoDB(str(DB_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Identify power-gen techs: any tech with an OAR row outputting to a
    # fuel whose decoded name contains "Electricity".
    oar = db.query("SELECT r, t, f, m, y, val FROM OutputActivityRatio WHERE val > 0")
    oar = decode_dims(oar, db)
    elec_oar = oar[oar["fuel_name"].str.startswith(ELEC_PREFIX, na=False)]
    power_techs = set(elec_oar["t"].unique())
    print(f"Power-gen tech IDs (OAR to an electricity fuel): {len(power_techs)}")

    # --- TECH SECTION ---
    cap = db.query("SELECT r, t, y, val FROM vtotalcapacityannual")
    new = db.query("SELECT r, t, y, val FROM vnewcapacity")
    pbta = db.query("SELECT r, t, f, y, val FROM vproductionbytechnologyannual")
    cap = decode_dims(cap, db)
    new = decode_dims(new, db)
    pbta = decode_dims(pbta, db)

    cap = cap[cap["t"].isin(power_techs)].copy()
    new = new[new["t"].isin(power_techs)].copy()

    # Total annual production per (region, tech, year) summing across all output fuels
    # (most techs have one output fuel, some have two for storage in/out)
    pbta_t = pbta[pbta["t"].isin(power_techs)].copy()
    prod_tech = (
        pbta_t.groupby(["r", "region_name", "t", "tech_name", "y"])["val"].sum()
        .reset_index()
        .rename(columns={"val": "production_PJ"})
    )
    cap = cap.rename(columns={"val": "capacity_GW"})
    new = new.rename(columns={"val": "new_capacity_GW"})

    tech_keys = ["r", "region_name", "t", "tech_name", "y"]
    tech_df = cap[tech_keys + ["capacity_GW"]].merge(
        new[tech_keys + ["new_capacity_GW"]], on=tech_keys, how="outer",
    ).merge(
        prod_tech[tech_keys + ["production_PJ"]], on=tech_keys, how="outer",
    )
    tech_df = tech_df.fillna({"capacity_GW": 0.0, "new_capacity_GW": 0.0, "production_PJ": 0.0})
    # Drop rows with all zeros (cleaner CSV)
    nz = (tech_df["capacity_GW"] != 0) | (tech_df["new_capacity_GW"] != 0) | (tech_df["production_PJ"] != 0)
    tech_df = tech_df[nz].copy()
    tech_df["entity_type"] = "Technology"
    tech_df["entity_name"] = tech_df["tech_name"]
    tech_df["category"] = tech_df["tech_name"].apply(tech_category)
    out_fuel_map = (
        elec_oar.groupby("t")["fuel_name"]
        .agg(lambda s: ", ".join(sorted(set(s))))
        .to_dict()
    )
    tech_df["primary_output_fuel"] = tech_df["t"].map(out_fuel_map)
    tech_df["use_PJ"] = pd.NA

    # --- FUEL SECTION ---
    use_a = db.query("SELECT r, t, f, y, val FROM vusebytechnologyannual")
    use_a = decode_dims(use_a, db)
    fuel_prod = pbta.groupby(["r", "region_name", "f", "fuel_name", "y"])["val"].sum().reset_index().rename(columns={"val": "production_PJ"})
    fuel_use = use_a.groupby(["r", "region_name", "f", "fuel_name", "y"])["val"].sum().reset_index().rename(columns={"val": "use_PJ"})
    fuel_df = fuel_prod.merge(fuel_use, on=["r", "region_name", "f", "fuel_name", "y"], how="outer")
    fuel_df = fuel_df.fillna({"production_PJ": 0.0, "use_PJ": 0.0})
    nz_f = (fuel_df["production_PJ"] != 0) | (fuel_df["use_PJ"] != 0)
    fuel_df = fuel_df[nz_f].copy()
    fuel_df["entity_type"] = "Fuel"
    fuel_df["entity_name"] = fuel_df["fuel_name"]
    fuel_df["category"] = fuel_df["fuel_name"].apply(fuel_category)
    fuel_df["capacity_GW"] = pd.NA
    fuel_df["new_capacity_GW"] = pd.NA
    fuel_df["primary_output_fuel"] = pd.NA

    # --- Combine ---
    cols = [
        "entity_type", "region_name", "entity_name", "category", "y",
        "capacity_GW", "new_capacity_GW", "production_PJ", "use_PJ",
        "primary_output_fuel",
    ]
    combined = pd.concat([tech_df[cols], fuel_df[cols]], ignore_index=True)
    combined = combined.rename(columns={"region_name": "region", "y": "year"})
    combined = combined.sort_values(
        ["entity_type", "region", "category", "entity_name", "year"]
    ).reset_index(drop=True)

    out_path = OUT_DIR / "summary_region_tech_fuel.csv"
    combined.to_csv(out_path, index=False, float_format="%.4f")
    print(f"\nWrote {out_path}")
    print(f"  total rows: {len(combined)}")
    print(f"  tech rows: {(combined['entity_type']=='Technology').sum()}  "
          f"unique techs: {combined.loc[combined['entity_type']=='Technology','entity_name'].nunique()}")
    print(f"  fuel rows: {(combined['entity_type']=='Fuel').sum()}  "
          f"unique fuels: {combined.loc[combined['entity_type']=='Fuel','entity_name'].nunique()}")

    # Quick category breakdown
    print("\n=== Power-gen tech categories present ===")
    print(combined[combined["entity_type"] == "Technology"]
          .groupby(["category"])["entity_name"].nunique().sort_values(ascending=False).to_string())
    print("\n=== Fuel categories present ===")
    print(combined[combined["entity_type"] == "Fuel"]
          .groupby(["category"])["entity_name"].nunique().sort_values(ascending=False).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
