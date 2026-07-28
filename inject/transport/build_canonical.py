"""Transport-domain adapter: source CSVs -> canonical_leap_inputs.csv.

Reads the 4 author CSVs from `inject/transport/<YYYYMMDD>/`:
  - sales_magnitude.csv     (Country x Year x vehicle_type -> sales count)
  - sales_mix.csv           (Country x Year x vehicle_type x fuel_type x
                              scenario -> count + share_%)
  - mileage_anchors.csv     (Country x vehicle_type -> annual mileage)
  - starting_year_sales.csv (Country x vehicle_type x fuel_type -> 2024
                              anchor with provenance)

Routes them to FOUR LEAP branch families (taxonomy confirmed
2026-05-19 against aeo9_v0.46):

  1. Key Assumptions\TransportDataStock\Vehicle_Sales\<Vehicle>
        <- sales_magnitude.csv (absolute sales count per vehicle x year)
        variable = "Key Assumptions"; one row per (ams, vehicle).

  2. Key Assumptions\TransportDataStock\BaseYear_StockData\<Vehicle>
        <- starting_year_sales.csv (2024 base-year stock anchor,
        aggregated across fuels to per-vehicle total)
        variable = "Key Assumptions"; one row per (ams, vehicle).

  3. Key Assumptions\TransportDataStock\Vehicles_Sales_Share\
                                       <Vehicle>\<Fuel>
        <- sales_mix.csv share_percent
        variable = "Key Assumptions"; one row per (ams, vehicle, fuel,
        scenario) carrying the share trajectory.

  4. Demand\Transport\Road\<Vehicle-typo>\<Fuel>\<Fuel> : Mileage
        <- mileage_anchors.csv (km/vehicle/year, replicated across
        all LEAP-available fuel leaves per vehicle).

Note the vehicle-name typo asymmetry:
  - Key Assumptions tree uses `Motorcycle` (correctly spelled)
  - Demand\Transport\Road uses `Motorcyle` (LEAP's typo)
The adapter encodes both via VEHICLE_TYPE_MAP_KA and
VEHICLE_TYPE_MAP_DEMAND so the rule is auditable, not in operator
memory.

Same shape for the gasoline fuel name (verified against the v0.80
`LEAP structure/LEAP Input Keys.xlsx`, 2026-07-23):
  - Key Assumptions tree uses bare `Gasoline`
  - Demand\Transport\Road uses `Blended Gasoline`
The split is intentional and the area calculates fine — do NOT
harmonise. Encoded via FUEL_TYPE_MAP_KA / FUEL_TYPE_MAP_DEMAND.

Vehicle_Stock_Share + Effective Operational_Stock are deliberately
NOT authored — those branches are owned outside this pipeline (user
decision 2026-05-19).

Per CLAUDE.md SA.15: every Interp() built here uses comma list-sep +
period decimal. Defensive normaliser at write time catches drift.

Per CLAUDE.md SA.18: Timor Leste is NOT in source data; the framework
requires explicit --exclude-timor-leste at inject time.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import pandas as pd

from nemo_read._leap_com import normalize_interp


# ---------------------------------------------------------------------------
# Mappings (caller-overridable in code; never in operator's head)
# ---------------------------------------------------------------------------

# Demand\Transport\Road uses the typo (LEAP's own authoring)
VEHICLE_TYPE_MAP_DEMAND = {
    "2W": "Motorcyle",        # LEAP typo on Demand\Transport\Road tree
    "Bus": "Bus",
    "LDV": "PassengerCar",
    "Truck": "Truck",
}

# Key Assumptions\TransportDataStock uses the correctly-spelled form
VEHICLE_TYPE_MAP_KA = {
    "2W": "Motorcycle",       # corrected spelling on Key Assumptions tree
    "Bus": "Bus",
    "LDV": "PassengerCar",
    "Truck": "Truck",
}

# KEY-SIDE fuel names (`Key\TransportDataStock\...`). The Key tree uses BARE
# `Gasoline`; the Demand tree uses `Blended Gasoline`. The split is
# INTENTIONAL and the area calculates fine — do NOT harmonise (CLAUDE.md
# §2.6, anatomy v0.80 version block, verified against
# `LEAP structure/LEAP Input Keys.xlsx` 2026-07-23: all 10 Key gasoline
# nodes are bare `Gasoline`, zero `Blended Gasoline` anywhere under `Key\`).
# The 2026-07-20 "renamed on BOTH trees" note was wrong — it came from a
# verbal description, not an export. A `Key\...\Blended Gasoline` row HANGS
# blind mode rather than erroring (§11.1, §A.20).
FUEL_TYPE_MAP_KA = {
    "Electric": "Electricity",
    "Gasoline": "Gasoline",
    "NaturalGas": "Natural Gas",
    "Hydrogen": "Hydrogen",
    "Hydrogen FCEV": "Hydrogen",
    "HydrogenFCV": "Hydrogen",
    "Diesel": "Blended Diesel",
    "HybridDiesel": "Blended Diesel",
}

# DEMAND-SIDE fuel names (`Demand\Transport\Road\...`): identical except
# gasoline. Not consumed today — Mileage rows take fuels straight from
# DEMAND_AVAILABLE_FUELS_PER_VEHICLE — present so a future Demand-side
# family cannot pick up the Key-side spelling by accident.
FUEL_TYPE_MAP_DEMAND = {**FUEL_TYPE_MAP_KA, "Gasoline": "Blended Gasoline"}

# Source-CSV Country -> LEAP region name
COUNTRY_MAP = {
    "Brunei Darussalam": "Brunei",
    "Cambodia": "Cambodia",
    "Indonesia": "Indonesia",
    "Lao PDR": "Laos",
    "Malaysia": "Malaysia",
    "Myanmar": "Myanmar",
    "Philippines": "Philippines",
    "Singapore": "Singapore",
    "Thailand": "Thailand",
    "Viet Nam": "Vietnam",
}

# Source scenario -> LEAP scenario name
SCENARIO_MAP = {
    "BAS": "Baseline Simulation",
    "ATS": "AMS Target Scenario",
    "RAS": "Regional Aspiration Scenario",
    "historical": "Current Accounts",
}

# Year boundary - historical scenario rows write to Current Accounts;
# BAS/ATS/RAS write from 2025 onward.
HISTORICAL_YEAR_END = 2024
PROJECTION_YEAR_START = 2025

# LEAP branch availability per (vehicle, fuel) under
# `Demand\Transport\Road\<Vehicle>\<Fuel>\<Fuel>` (the Mileage leaves).
# Note PassengerCar has NO Hydrogen child on this tree.
DEMAND_AVAILABLE_FUELS_PER_VEHICLE = {
    "Bus":          {"Blended Diesel", "Electricity", "Blended Gasoline",
                     "Hydrogen", "Natural Gas"},
    "Motorcyle":    {"Electricity", "Blended Gasoline"},  # NO NG/Hydrogen/Diesel
    "PassengerCar": {"Blended Diesel", "Electricity", "Blended Gasoline",
                     "Natural Gas"},                # NO Hydrogen
    "Truck":        {"Blended Diesel", "Electricity", "Blended Gasoline",
                     "Hydrogen", "Natural Gas"},
}

# Key Assumptions\TransportDataStock\Vehicles_Sales_Share availability.
# PassengerCar DOES carry Hydrogen here (unlike Demand\Transport\Road).
# Motorcycle (correct spelling) on KA tree.
# Key-side gasoline is BARE `Gasoline` (see FUEL_TYPE_MAP_KA). This set and
# FUEL_TYPE_MAP_KA must agree — if one says `Gasoline` and the other says
# `Blended Gasoline`, the availability filter below silently drops all 160
# gasoline sales-share rows with a WARN instead of failing.
KA_SALES_SHARE_FUELS_PER_VEHICLE = {
    "Bus":          {"Blended Diesel", "Electricity", "Gasoline",
                     "Hydrogen", "Natural Gas"},
    "Motorcycle":   {"Electricity", "Gasoline"},
    "PassengerCar": {"Blended Diesel", "Electricity", "Gasoline",
                     "Hydrogen", "Natural Gas"},     # has Hydrogen
    "Truck":        {"Blended Diesel", "Electricity", "Gasoline",
                     "Hydrogen", "Natural Gas"},
}


HERE = Path(__file__).parent
INPUT_DIR = HERE / "20260720"
OUTPUT_CSV = HERE / "canonical_leap_inputs.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _interp_from_pairs(pairs: list[tuple[int, float]]) -> str:
    """Build Interp(year, value, year, value, ...) - SA.15 comma + period."""
    if not pairs:
        return ""
    pairs = sorted(pairs, key=lambda p: p[0])
    parts = []
    for y, v in pairs:
        parts.append(str(int(y)))
        parts.append(f"{v:g}")
    return f"Interp({', '.join(parts)})"


# ---------------------------------------------------------------------------
# Per-source transformers (loaders)
# ---------------------------------------------------------------------------

def _load_sales_mix(path: Path) -> pd.DataFrame:
    """Sales mix (share+count by vehicle x fuel x scenario x year)."""
    df = pd.read_csv(path)
    unknown = set(df["vehicle_type"].unique()) - set(VEHICLE_TYPE_MAP_KA)
    if unknown:
        print(f"  WARN sales_mix: unknown vehicle_type(s): {unknown} - dropped")
        df = df[df["vehicle_type"].isin(VEHICLE_TYPE_MAP_KA)]
    unknown = set(df["fuel_type"].unique()) - set(FUEL_TYPE_MAP_KA)
    if unknown:
        print(f"  WARN sales_mix: unknown fuel_type(s): {unknown} - dropped")
        df = df[df["fuel_type"].isin(FUEL_TYPE_MAP_KA)]
    unknown = set(df["Country"].unique()) - set(COUNTRY_MAP)
    if unknown:
        print(f"  WARN sales_mix: unknown Country(s): {unknown} - dropped")
        df = df[df["Country"].isin(COUNTRY_MAP)]
    unknown = set(df["scenario"].unique()) - set(SCENARIO_MAP)
    if unknown:
        print(f"  WARN sales_mix: unknown scenario(s): {unknown} - dropped")
        df = df[df["scenario"].isin(SCENARIO_MAP)]

    df = df.copy()
    df["ams"] = df["Country"].map(COUNTRY_MAP)
    df["leap_vehicle_ka"] = df["vehicle_type"].map(VEHICLE_TYPE_MAP_KA)
    df["leap_fuel"] = df["fuel_type"].map(FUEL_TYPE_MAP_KA)
    df["leap_scenario"] = df["scenario"].map(SCENARIO_MAP)
    return df


def _load_sales_magnitude(path: Path) -> pd.DataFrame:
    """Absolute sales count by Country x Year x vehicle_type (no scenario, no fuel)."""
    df = pd.read_csv(path)
    df = df[df["Country"].isin(COUNTRY_MAP)]
    df = df[df["vehicle_type"].isin(VEHICLE_TYPE_MAP_KA)]
    df = df.copy()
    df["ams"] = df["Country"].map(COUNTRY_MAP)
    df["leap_vehicle_ka"] = df["vehicle_type"].map(VEHICLE_TYPE_MAP_KA)
    return df[["ams", "leap_vehicle_ka", "Year", "sales_count"]]


def _load_starting_year_sales(path: Path) -> pd.DataFrame:
    """2024 base-year anchor (by Country x vehicle x fuel).

    Carries `sales_count` (per-fuel sales) and, from the 2026-07-20 drop
    onward, `stock_count` — the 2024 FLEET STOCK per (Country, vehicle),
    repeated across that vehicle's fuel rows. Take stock ONCE per
    (ams, vehicle); never sum it across fuels.
    """
    df = pd.read_csv(path)
    df = df[df["Country"].isin(COUNTRY_MAP)]
    df = df[df["vehicle_type"].isin(VEHICLE_TYPE_MAP_KA)]
    df = df.copy()
    df["ams"] = df["Country"].map(COUNTRY_MAP)
    df["leap_vehicle_ka"] = df["vehicle_type"].map(VEHICLE_TYPE_MAP_KA)
    cols = ["ams", "leap_vehicle_ka", "Year", "sales_count"]
    if "stock_count" in df.columns:
        cols.append("stock_count")
    return df[cols]


def _load_mileage(path: Path) -> pd.DataFrame:
    """Mileage per (Country, vehicle_type)."""
    df = pd.read_csv(path)
    df = df[df["Country"].isin(COUNTRY_MAP)]
    df = df[df["vehicle_type"].isin(VEHICLE_TYPE_MAP_DEMAND)]
    df = df.copy()
    df["ams"] = df["Country"].map(COUNTRY_MAP)
    df["leap_vehicle_demand"] = df["vehicle_type"].map(VEHICLE_TYPE_MAP_DEMAND)
    return df[["ams", "leap_vehicle_demand",
               "mileage_km_per_year", "source", "confidence"]]


# ---------------------------------------------------------------------------
# Build canonical rows - one per branch family
# ---------------------------------------------------------------------------

def _build_vehicle_sales_rows(sales_mag: pd.DataFrame) -> list[dict]:
    """Rows for `Key\\TransportDataStock\\Vehicle_Sales\\<Vehicle>`.

    Source has no scenario or fuel axis - one Interp() per
    (ams, vehicle) carrying the absolute count trajectory. Routes to
    Current Accounts (LEAP scenario inheritance carries it through)."""
    rows = []
    grouped = sales_mag.groupby(["ams", "leap_vehicle_ka"])
    for (ams, vt), sub in grouped:
        pairs = list(zip(sub["Year"].astype(int),
                         sub["sales_count"].astype(float)))
        expr = _interp_from_pairs(pairs)
        if not expr:
            continue
        rows.append({
            "ams": ams,
            "branch": f"Key\\TransportDataStock\\"
                      f"Vehicle_Sales\\{vt}",
            "variable": "Activity Level",
            "expression": normalize_interp(expr),
            "unit": "",
            "fuel": "",
            "source": "sales_magnitude.csv (Transport pipeline 2026-05-19)",
            "note": "absolute sales count (all fuels combined)",
            "src_csv": "sales_magnitude.csv",
            "data_confidence": "Medium",
            "scenario": "Current Accounts",
        })
    return rows


def _build_baseyear_stock_rows(start_year: pd.DataFrame) -> list[dict]:
    """Rows for `Key\\TransportDataStock\\BaseYear_StockData\\
    <Vehicle>`.

    Source has fuel-level rows; we aggregate to per-vehicle total
    since the BaseYear_StockData branch has no fuel sub-tree.
    Single-year anchor (typically 2024) becomes a flat Interp(year, val).

    DATA-SHAPE FIX — RESOLVED 2026-07-20.
      BaseYear_StockData wants the FLEET STOCK at the year before the
      first modelling year (2024 vehicles on the road), NOT the sum of
      2024 sales counts. The old implementation summed `sales_count`,
      giving a per-vehicle ANNUAL SALES figure 30-100x smaller than the
      fleet (LEAP held Brunei Bus 2300; we authored 61).

      The 2026-07-20 transport drop ships `stock_count` — the real 2024
      fleet stock per (Country, vehicle), REPEATED across that vehicle's
      fuel rows. We therefore take it ONCE per (ams, vehicle, Year) and
      never sum it. Sanity anchors from the drop README: BRN Bus 2,188 /
      CAM Bus 65,996 / IDN Bus 298,260.
    """
    rows = []
    if "stock_count" not in start_year.columns:
        raise ValueError(
            "starting_year_sales.csv has no `stock_count` column. Refusing "
            "to fall back to the sales-sum, which is 30-100x too small for "
            "BaseYear_StockData (see docstring). Supply the 2026-07-20 drop "
            "or pass --skip-families BaseYear_StockData."
        )
    g = start_year.groupby(["ams", "leap_vehicle_ka", "Year"])["stock_count"]
    spread = (g.max() - g.min()).abs()
    if (spread > 1e-6).any():
        bad = spread[spread > 1e-6].index.tolist()[:3]
        print(f"  [WARN] stock_count differs across fuel rows for {bad} — "
              f"expected one repeated per-vehicle value; taking max.")
    agg = g.max().reset_index()
    grouped = agg.groupby(["ams", "leap_vehicle_ka"])
    for (ams, vt), sub in grouped:
        pairs = list(zip(sub["Year"].astype(int),
                         sub["stock_count"].astype(float)))
        expr = _interp_from_pairs(pairs)
        if not expr:
            continue
        rows.append({
            "ams": ams,
            "branch": f"Key\\TransportDataStock\\"
                      f"BaseYear_StockData\\{vt}",
            "variable": "Activity Level",
            "expression": normalize_interp(expr),
            "unit": "",
            "fuel": "",
            "source": "starting_year_sales.csv (Transport pipeline 2026-05-19)",
            "note": "base-year stock anchor (sum across fuels)",
            "src_csv": "starting_year_sales.csv",
            "data_confidence": "Medium",
            "scenario": "Current Accounts",
        })
    return rows


def _build_sales_share_rows(sales_mix: pd.DataFrame) -> list[dict]:
    """Rows for `Key\\TransportDataStock\\Vehicles_Sales_Share\\
    <Vehicle>\\<Fuel>` - share_percent trajectory per
    (ams, vehicle, fuel, scenario)."""
    df = sales_mix.copy()

    # KA Sales_Share availability filter (this tree HAS PassengerCar\Hydrogen)
    pre = len(df)
    mask = df.apply(
        lambda r: r["leap_fuel"] in KA_SALES_SHARE_FUELS_PER_VEHICLE.get(
            r["leap_vehicle_ka"], set()),
        axis=1,
    )
    dropped = df[~mask]
    if len(dropped):
        combos = (dropped[["leap_vehicle_ka", "leap_fuel"]]
                  .drop_duplicates()
                  .sort_values(["leap_vehicle_ka", "leap_fuel"]))
        print(f"  WARN sales_share: dropped {pre - mask.sum()} rows for "
              f"(vehicle, fuel) combinations not in KA Sales_Share taxonomy:")
        for _, r in combos.iterrows():
            print(f"    {r['leap_vehicle_ka']} x {r['leap_fuel']}")
    df = df[mask]

    # Year-based scenario remap: Year <= 2024 -> Current Accounts
    is_hist = df["Year"] <= HISTORICAL_YEAR_END
    df.loc[is_hist, "leap_scenario"] = SCENARIO_MAP["historical"]

    # Re-aggregate share_percent after the historical override and the
    # fuel-collapse (Hydrogen FCEV + HydrogenFCV both map to Hydrogen
    # -> sum the shares; Diesel + HybridDiesel -> Blended Diesel)
    agg = (df.groupby(
        ["ams", "leap_vehicle_ka", "leap_fuel", "leap_scenario", "Year"],
        as_index=False
    )["share_percent"].sum())

    rows = []
    grouped = agg.groupby(["ams", "leap_vehicle_ka", "leap_fuel",
                           "leap_scenario"])
    for (ams, vt, ft, scen), sub in grouped:
        pairs = list(zip(sub["Year"].astype(int),
                         sub["share_percent"].astype(float)))
        expr = _interp_from_pairs(pairs)
        if not expr:
            continue
        rows.append({
            "ams": ams,
            "branch": f"Key\\TransportDataStock\\"
                      f"Vehicles_Sales_Share\\{vt}\\{ft}",
            "variable": "Activity Level",
            "expression": normalize_interp(expr),
            "unit": "",
            "fuel": ft,
            "source": "sales_mix.csv (Transport pipeline 2026-05-19)",
            "note": f"sales share_percent, scenario={scen}",
            "src_csv": "sales_mix.csv",
            "data_confidence": "Medium",
            "scenario": scen,
        })
    return rows


def _build_mileage_rows(mileage: pd.DataFrame) -> list[dict]:
    """Rows for `Demand\\Transport\\Road\\<Vehicle-typo>\\<Fuel>\\<Fuel>`
    on the `Mileage` variable. Replicate the per-vehicle km/year across
    all LEAP-available Demand-tree fuel leaves for that vehicle."""
    rows = []
    for _, r in mileage.iterrows():
        ams = r["ams"]
        vt = r["leap_vehicle_demand"]
        km = float(r["mileage_km_per_year"])
        source = str(r["source"])
        confidence = str(r["confidence"])
        expr = _interp_from_pairs([
            (2025, km), (2030, km), (2035, km), (2040, km),
            (2045, km), (2050, km), (2055, km), (2060, km),
        ])
        for ft in DEMAND_AVAILABLE_FUELS_PER_VEHICLE.get(vt, set()):
            rows.append({
                "ams": ams,
                "branch": f"Demand\\Transport\\Road\\{vt}\\{ft}\\{ft}",
                "variable": "Mileage",
                "expression": normalize_interp(expr),
                "unit": "Kilometer",
                "fuel": ft,
                "source": source,
                "note": f"mileage vehicle-wide; confidence={confidence}",
                "src_csv": "mileage_anchors.csv",
                "data_confidence": "Medium" if confidence != "low" else "Low",
                "scenario": "Current Accounts",
            })
    return rows


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(skip_families: set[str] | None = None):
    skip = set(skip_families or set())
    print(f"[transport adapter] reading from {INPUT_DIR}/")
    if skip:
        print(f"[transport adapter] SKIPPING families: {sorted(skip)}")

    sales_mix = _load_sales_mix(INPUT_DIR / "sales_mix.csv")
    print(f"  sales_mix rows: {len(sales_mix)}")

    sales_mag = _load_sales_magnitude(INPUT_DIR / "sales_magnitude.csv")
    print(f"  sales_magnitude rows: {len(sales_mag)}")

    start_year = _load_starting_year_sales(
        INPUT_DIR / "starting_year_sales.csv")
    print(f"  starting_year_sales rows: {len(start_year)}")

    mileage = _load_mileage(INPUT_DIR / "mileage_anchors.csv")
    print(f"  mileage rows: {len(mileage)}")

    rows = []
    if "Vehicle_Sales" not in skip:
        rows.extend(_build_vehicle_sales_rows(sales_mag))
    if "BaseYear_StockData" not in skip:
        rows.extend(_build_baseyear_stock_rows(start_year))
    if "Vehicles_Sales_Share" not in skip:
        rows.extend(_build_sales_share_rows(sales_mix))
    if "Mileage" not in skip:
        rows.extend(_build_mileage_rows(mileage))

    # Sort so Key\ rows are pushed BEFORE Demand\ rows within each AMS
    # group. If the KA variable lookup ever fails again, the dry-run
    # will surface it within the first ~5 rows of region 1 instead of
    # after walking ~16 Mileage rows first.
    def _sort_key(r):
        is_demand = 1 if r["branch"].startswith("Demand\\") else 0
        return (r["ams"], is_demand, r["branch"], r.get("scenario", ""))
    rows.sort(key=_sort_key)

    fieldnames = ["ams", "branch", "variable", "expression", "unit",
                  "fuel", "source", "note", "src_csv",
                  "data_confidence", "scenario"]
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            r["expression"] = normalize_interp(r.get("expression", ""))
            writer.writerow(r)

    print(f"\n[transport adapter] wrote {OUTPUT_CSV.name}  ({len(rows)} rows)")
    by_var = defaultdict(int)
    by_scenario = defaultdict(int)
    by_ams = defaultdict(int)
    by_family = defaultdict(int)
    for r in rows:
        by_var[r["variable"]] += 1
        by_scenario[r["scenario"]] += 1
        by_ams[r["ams"]] += 1
        # branch family = first 4 segments
        family = "\\".join(r["branch"].split("\\")[:4])
        by_family[family] += 1
    print(f"\n  Rows per variable: {dict(by_var)}")
    print(f"  Rows per scenario: {dict(by_scenario)}")
    print(f"  Rows per AMS: {dict(by_ams)}")
    print(f"  Rows per branch family:")
    for fam, n in sorted(by_family.items()):
        print(f"    {n:4d}  {fam}")


def _parse_args():
    p = argparse.ArgumentParser(
        description="Transport adapter: source CSVs -> canonical_leap_inputs.csv")
    p.add_argument(
        "--skip-families", default="",
        help="Comma-separated list of branch families to skip. Options: "
             "Vehicle_Sales, BaseYear_StockData, Vehicles_Sales_Share, "
             "Mileage. Example: --skip-families BaseYear_StockData")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    skip = {s.strip() for s in args.skip_families.split(",") if s.strip()}
    build(skip_families=skip)
