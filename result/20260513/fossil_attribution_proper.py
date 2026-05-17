"""Rigorous attribution of fossil-fuel jumps to their authored demand
anchor. Per (region, fuel_product), find the SAD/AAD trajectory for the
end-use sink — not just the same fuel name. Then compare end-use SAD
ratio to observed production/use ratios to determine: authored vs solver.

Outputs:
  - petroleum_demand_trajectories.csv — every (region, petroleum-product
    end-use fuel) and its full SAD trajectory + YoY ratios
  - all_fossil_demand_trajectories.csv — same for all fossil products
  - solver_only_fossil_jumps.csv — jumps NOT explained by authored demand
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 27.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v045")

PETROLEUM_PRODUCTS = [
    "Gasoline", "Diesel", "Blended Diesel", "Jet Kerosene", "Kerosene",
    "Naphtha", "LPG", "Crude Oil", "Residual Fuel Oil", "Bitumen",
    "Avgas", "Petroleum Coke", "Lubricants", "Refinery Gas", "Oil",
]
ALL_FOSSIL = PETROLEUM_PRODUCTS + ["Coal", "Natural Gas", "LNG"]


def categorize_fuel(name: str) -> str:
    """Return the petroleum/fossil product family this fuel belongs to,
    based on its leading word(s) — before 'output from' / 'input to'."""
    if not isinstance(name, str): return "?"
    head = name.split(" output from")[0].split(" input to")[0].strip()
    head = head.replace('"', '').strip()
    return head  # e.g., "Gasoline", "Diesel", "Blended Diesel", "Natural Gas"


def main() -> int:
    db = NemoDB(str(DB_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- 1. Pull every SAD and AAD row, decode, categorize ----------
    sad = db.query("SELECT r, f, y, val FROM SpecifiedAnnualDemand WHERE val > 0")
    aad = db.query("SELECT r, f, y, val FROM AccumulatedAnnualDemand WHERE val > 0")
    sad = decode_dims(sad, db)
    aad = decode_dims(aad, db)
    for d, src in ((sad, "SAD"), (aad, "AAD")):
        d["family"] = d["fuel_name"].apply(categorize_fuel)
        d["year"] = d["y"].astype(int)
    combined = pd.concat([
        sad.assign(source="SAD")[["region_name", "family", "fuel_name", "year", "val", "source"]],
        aad.assign(source="AAD")[["region_name", "family", "fuel_name", "year", "val", "source"]],
    ], ignore_index=True)
    combined = combined.rename(columns={"region_name": "region", "val": "demand_PJ"})

    # Roll up by family per region per year (in case multiple fuels in same family)
    fam_demand = (
        combined.groupby(["region", "family", "year"])["demand_PJ"].sum().reset_index()
        .sort_values(["region", "family", "year"])
    )
    fam_demand["prev_PJ"] = fam_demand.groupby(["region", "family"])["demand_PJ"].shift(1)
    fam_demand["YoY_ratio"] = fam_demand["demand_PJ"] / fam_demand["prev_PJ"].replace(0, pd.NA)

    # ---------- 2. Petroleum products: show full trajectories per region ----------
    pet_fam = fam_demand[fam_demand["family"].isin(PETROLEUM_PRODUCTS)].copy()
    pet_fam.to_csv(OUT_DIR / "petroleum_demand_trajectories.csv", index=False)

    # Pivot wide for human reading: region x family vs year
    print("\n=== PETROLEUM-PRODUCT authored demand trajectories (PJ/yr) per region ===")
    for region in sorted(pet_fam["region"].unique()):
        sub = pet_fam[pet_fam["region"] == region]
        piv = sub.pivot_table(index="family", columns="year", values="demand_PJ",
                              aggfunc="sum", fill_value=0)
        if piv.empty: continue
        rpiv = sub.pivot_table(index="family", columns="year", values="YoY_ratio",
                               aggfunc="mean", fill_value=float("nan"))
        # Annotate peak year per family
        peaks = piv.idxmax(axis=1)
        print(f"\n--- {region} ---  (values in PJ/yr; peak_year shown)")
        # Only show families that actually have demand in this region
        present = piv[(piv != 0).any(axis=1)]
        if present.empty: continue
        present["peak_year"] = peaks
        with pd.option_context("display.width", 200,
                               "display.float_format", "{:.0f}".format):
            print(present.to_string())

    # ---------- 3. All-fossil family demand summary, per region ----------
    print("\n\n=== ALL-FOSSIL authored demand: peak year per (region, family), with PJ at 2025 / peak / 2060 ===")
    rows = []
    foss = fam_demand[fam_demand["family"].isin(ALL_FOSSIL)]
    for (region, family), g in foss.groupby(["region", "family"]):
        yrs = g.set_index("year")["demand_PJ"]
        if yrs.sum() < 1: continue
        peak_y = int(yrs.idxmax())
        rows.append({
            "region": region, "family": family,
            "pj_2025": yrs.get(2025, 0.0),
            "peak_year": peak_y,
            "pj_peak": yrs.loc[peak_y],
            "pj_2060": yrs.get(2060, 0.0),
            "ratio_peak_vs_2025": (yrs.loc[peak_y] / yrs.get(2025, 0.0)) if yrs.get(2025, 0) > 0 else float("inf"),
            "ratio_2060_vs_peak": (yrs.get(2060, 0.0) / yrs.loc[peak_y]) if yrs.loc[peak_y] > 0 else 0.0,
        })
    summary = pd.DataFrame(rows).sort_values(["region", "family"])
    summary.to_csv(OUT_DIR / "all_fossil_demand_summary.csv", index=False)
    with pd.option_context("display.width", 200, "display.float_format", "{:.1f}".format):
        print(summary.to_string(index=False))

    # ---------- 4. Solver-only jumps: production jumps with no authored anchor in family ----------
    fb = pd.read_csv(OUT_DIR / "fuel_balance.csv")
    fb["family"] = fb["fuel"].apply(categorize_fuel)
    fb["year"] = fb["year"].astype(int)
    fb["is_fossil_family"] = fb["family"].isin(ALL_FOSSIL)
    foss_fb = fb[fb["is_fossil_family"] & (fb["production_PJ"] > 0)].sort_values(
        ["region", "fuel", "year"]
    )
    foss_fb["prev_prod"] = foss_fb.groupby(["region", "fuel"])["production_PJ"].shift(1)
    foss_fb["ratio_prod"] = foss_fb["production_PJ"] / foss_fb["prev_prod"].replace(0, pd.NA)
    big_prod = foss_fb[
        ((foss_fb["ratio_prod"] >= 1.5) | (foss_fb["ratio_prod"] <= 0.5))
        & (abs(foss_fb["production_PJ"] - foss_fb["prev_prod"]) >= 1.0)
    ].copy()

    # Attach family demand YoY ratio for same (region, family, year)
    big_prod = big_prod.merge(
        fam_demand[["region", "family", "year", "demand_PJ", "prev_PJ", "YoY_ratio"]]
        .rename(columns={"demand_PJ": "demand_PJ_this", "prev_PJ": "demand_PJ_prev",
                         "YoY_ratio": "demand_YoY_ratio"}),
        on=["region", "family", "year"], how="left",
    )

    def attribute(row):
        rd = row["demand_YoY_ratio"]
        rp = row["ratio_prod"]
        if pd.isna(rd): return "SOLVER (no family SAD/AAD found)"
        if pd.isna(rp): return "?"
        # If demand ratio is within ±20% of production ratio → authored explains it
        if 0.85 * rp <= rd <= 1.15 * rp:
            return "AUTHORED (demand step matches production step)"
        # If demand smoother than production
        if abs(rd - 1) < abs(rp - 1) * 0.7:
            return "SOLVER (demand smoother than production)"
        return "MIXED"

    big_prod["attribution"] = big_prod.apply(attribute, axis=1)
    big_prod = big_prod[[
        "region", "fuel", "family", "year", "prev_prod", "production_PJ",
        "ratio_prod", "demand_PJ_prev", "demand_PJ_this", "demand_YoY_ratio",
        "attribution",
    ]].sort_values(["region", "fuel", "year"])
    big_prod.to_csv(OUT_DIR / "fossil_production_jumps_attributed.csv", index=False)

    print("\n\n=== Fossil production jumps with attribution to family-level authored demand ===")
    print("(authored ratio computed by summing SAD+AAD across all fuels in same family)")
    user_regs = ["Brunei", "Cambodia", "Myanmar", "Singapore", "Timor Leste"]
    pet_users = big_prod[
        big_prod["family"].isin(PETROLEUM_PRODUCTS) & big_prod["region"].isin(user_regs)
    ]
    print("\n--- Petroleum jumps in user's named regions ---")
    with pd.option_context("display.width", 240,
                           "display.float_format", "{:.2f}".format):
        print(pet_users.to_string(index=False))

    print("\n--- Non-attributed (SOLVER-only) jumps across all AMS ---")
    solver_only = big_prod[big_prod["attribution"].str.startswith("SOLVER", na=False)]
    with pd.option_context("display.width", 240,
                           "display.float_format", "{:.2f}".format):
        print(solver_only.to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
