"""Build TPES of Renewable Energy for ASEAN from fuel_balance.csv.

TPES (Total Primary Energy Supply) for RE = primary energy input from
renewable resources to the energy system. Counts primary RE fuels
only — no double-counting of secondary biofuels (Biodiesel, Ethanol,
SAF, HVO) which are derived from primary biomass already counted.

ASEAN = the 10 AMS member states. Timor Leste shown separately.
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path

CSV = Path("mailbox/20260513/results_v045/fuel_balance.csv")
OUT = Path("mailbox/20260513/results_v045/tpes_re_asean.csv")

ASEAN_10 = ["Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
            "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam"]
ASEAN_11 = ASEAN_10 + ["Timor Leste"]
PJ_PER_MTOE = 41.868  # IEA standard: 1 toe = 41.868 GJ

# Primary RE fuel name keywords (the fuel-side identification)
# Each entry is matched as a substring against the cleaned fuel name.
RE_PRIMARY_KEYWORDS = [
    "Solar input to",            # primary solar resource into power
    "Wind input to",             # primary wind resource
    "Geothermal input to",       # primary geothermal heat
    "Tidal input to",            # primary tidal
    "Wave input to",             # primary wave
    "Large Hydro input to",      # primary hydro
    "Small Hydro input to",      # primary small hydro
    "Biomass input to",          # primary biomass (woodchip, straw, etc.)
    "Biomethane input to",       # primary biogas to grid
    "Municipal Solid Waste input to",  # MSW (biogenic fraction; here counted in full)
    "Domestic Biogas output from",     # domestic biogas (cooking/heating)
    # Primary biomass crops / feedstocks
    "Cassava input to",
    "Sugarcane input to",
    "Molasses input to",
    "Corn input to",
    "Coconut Oil input to",
    "Palm Oil input to",
    "Palm Oil Mill Effluent input to",
    "Bagasse input to",
    "Wood input to",
    "Charcoal input to",
]


def is_re_primary(fuel: str) -> bool:
    if not isinstance(fuel, str):
        return False
    return any(kw in fuel for kw in RE_PRIMARY_KEYWORDS)


def main() -> int:
    fb = pd.read_csv(CSV)
    fb["is_re_primary"] = fb["fuel_name_full"].apply(is_re_primary)
    re_rows = fb[fb["is_re_primary"]].copy()
    # Production_PJ is the "supply" side of the fuel = primary energy flow in
    re_rows["tpes_PJ"] = re_rows["production_PJ"]
    re_rows["tpes_MTOE"] = re_rows["tpes_PJ"] / PJ_PER_MTOE
    re_rows["in_asean"] = re_rows["region"].isin(ASEAN_11)

    # Per-region annual TPES-RE in MTOE
    per_region_year = re_rows.pivot_table(
        index="region", columns="year", values="tpes_MTOE", aggfunc="sum", fill_value=0
    )
    per_region_year = per_region_year.reindex(ASEAN_11).fillna(0)
    # ASEAN-11 total (incl Timor Leste)
    asean_total = per_region_year.loc[ASEAN_11].sum().to_frame("ASEAN (incl. Timor Leste) total").T
    per_region_year = pd.concat([per_region_year, asean_total])
    per_region_year.index.name = "region"
    per_region_year.to_csv(OUT, float_format="%.3f")

    print("=== TPES of RE in ASEAN (MTOE/yr), v0.45 RAS ===")
    with pd.option_context("display.float_format", "{:.2f}".format):
        print(per_region_year.round(2).to_string())
    print()

    # Per-fuel breakdown across ASEAN-11 (incl. Timor Leste)
    print("\n=== ASEAN (incl. Timor Leste) TPES-RE by source category (MTOE/yr) ===")
    re_rows["fuel_category"] = re_rows["fuel_name_full"].apply(
        lambda s: next((kw.split(" input to")[0].split(" output from")[0]
                        for kw in RE_PRIMARY_KEYWORDS if kw in s), "Other")
    )
    asean_only = re_rows[re_rows["in_asean"]]
    by_cat = asean_only.pivot_table(
        index="fuel_category", columns="year", values="tpes_MTOE",
        aggfunc="sum", fill_value=0
    )
    by_cat["total_2025_2060"] = by_cat.sum(axis=1)
    by_cat = by_cat.sort_values("total_2025_2060", ascending=False)
    with pd.option_context("display.float_format", "{:.2f}".format):
        print(by_cat.round(2).to_string())

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
