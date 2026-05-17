"""Identify unnatural year-over-year jumps in fossil fuel use & production
across all AMS in v0.45. Cross-references against authored
SpecifiedAnnualDemand / AccumulatedAnnualDemand to attribute each jump to
either:
  (a) AUTHORED-side step (input data has the jump → authoring bug)
  (b) SOLVER-side step (input smooth, production response jumps → derived
      from blend mandate, substitution, fleet retirement, etc.)
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 27.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v045")

# Fuel-name keywords that mark a fuel as fossil-derived
FOSSIL_KW = [
    "gasoline", "diesel", "kerosene", "jet", "naphtha", "lpg",
    "crude oil", "fuel oil", "bitumen", "avgas", "petroleum coke",
    "lubricants", "refinery gas", "oil output",
    "coal", "natural gas", "lng",
]
PETROLEUM_KW = [  # narrower — what user called "petroleum products"
    "gasoline", "diesel", "kerosene", "jet", "naphtha", "lpg",
    "crude oil", "fuel oil", "bitumen", "avgas", "petroleum coke",
    "lubricants", "refinery gas",
]

JUMP_RATIO_THRESHOLD = 1.5   # >50% step in one 5y window
DROP_RATIO_THRESHOLD = 0.5   # ≤50% drop in one 5y window
NOISE_FLOOR_PJ = 1.0          # ignore tiny absolute changes


def is_fossil(fuel: str) -> bool:
    f = (fuel or "").lower()
    if "biomass" in f or "biogas" in f or "biodiesel" in f or "bioethanol" in f:
        return False
    if "saf" in f or "sustainable aviation" in f:
        return False
    if "hvo" in f or "renewable diesel" in f:
        return False
    return any(k in f for k in FOSSIL_KW)


def is_petroleum(fuel: str) -> bool:
    f = (fuel or "").lower()
    if "bio" in f or "saf" in f or "hvo" in f or "renewable" in f:
        return False
    return any(k in f for k in PETROLEUM_KW)


def detect_jumps(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Per (region, fuel), compute year-over-year deltas and flag jumps."""
    df = df.sort_values(["region", "fuel", "year"]).copy()
    df["prev_val"] = df.groupby(["region", "fuel"])[value_col].shift(1)
    df["prev_year"] = df.groupby(["region", "fuel"])["year"].shift(1)
    df["delta"] = df[value_col] - df["prev_val"]
    df["ratio"] = df[value_col] / df["prev_val"].replace(0, pd.NA)
    df = df.dropna(subset=["prev_val"])
    flagged = df[
        ((df["ratio"] >= JUMP_RATIO_THRESHOLD) | (df["ratio"] <= DROP_RATIO_THRESHOLD))
        & (df["delta"].abs() >= NOISE_FLOOR_PJ)
    ].copy()
    return flagged


def main() -> int:
    db = NemoDB(str(DB_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fb = pd.read_csv(OUT_DIR / "fuel_balance.csv")
    fb["is_fossil"] = fb["fuel"].apply(is_fossil)
    fb["is_petroleum"] = fb["fuel"].apply(is_petroleum)

    # --- 1. Production-side jumps on fossil fuels ---
    foss_prod = fb[fb["is_fossil"] & (fb["production_PJ"] > 0)].copy()
    prod_jumps = detect_jumps(foss_prod, "production_PJ")
    prod_jumps = prod_jumps.rename(columns={
        "production_PJ": "this_PJ", "prev_val": "prev_PJ",
        "ratio": "ratio_prod", "delta": "delta_PJ_prod",
    })
    prod_jumps["jump_kind"] = "PRODUCTION"
    prod_jumps = prod_jumps[
        ["region", "fuel", "year", "prev_year", "prev_PJ", "this_PJ",
         "delta_PJ_prod", "ratio_prod", "is_petroleum", "jump_kind"]
    ]
    print(f"[fossil prod jumps] {len(prod_jumps)} rows flagged")

    # --- 2. Use-side jumps on fossil fuels ---
    foss_use = fb[fb["is_fossil"] & (fb["use_PJ"] > 0)].copy()
    use_jumps = detect_jumps(foss_use, "use_PJ")
    use_jumps = use_jumps.rename(columns={
        "use_PJ": "this_PJ", "prev_val": "prev_PJ",
        "ratio": "ratio_use", "delta": "delta_PJ_use",
    })
    use_jumps["jump_kind"] = "USE"
    use_jumps = use_jumps[
        ["region", "fuel", "year", "prev_year", "prev_PJ", "this_PJ",
         "delta_PJ_use", "ratio_use", "is_petroleum", "jump_kind"]
    ]
    print(f"[fossil use jumps]  {len(use_jumps)} rows flagged")

    # --- 3. Cross-reference against authored SpecifiedAnnualDemand ---
    sad = db.query("SELECT r, f, y, val FROM SpecifiedAnnualDemand WHERE val > 0")
    aad = db.query("SELECT r, f, y, val FROM AccumulatedAnnualDemand WHERE val > 0")
    sad = decode_dims(sad, db)
    aad = decode_dims(aad, db)
    sad["fuel_clean"] = sad["fuel_name"].apply(lambda s: s.split(' [LEAP ID')[0].strip().replace('"', ''))
    aad["fuel_clean"] = aad["fuel_name"].apply(lambda s: s.split(' [LEAP ID')[0].strip().replace('"', ''))

    sad_long = sad[["region_name", "fuel_clean", "y", "val"]].rename(
        columns={"region_name": "region", "fuel_clean": "fuel", "y": "year", "val": "SAD_PJ"}
    )
    aad_long = aad[["region_name", "fuel_clean", "y", "val"]].rename(
        columns={"region_name": "region", "fuel_clean": "fuel", "y": "year", "val": "AAD_PJ"}
    )
    sad_long["year"] = sad_long["year"].astype(int)
    aad_long["year"] = aad_long["year"].astype(int)

    # Per (region, fuel) get SAD trajectory and compute YoY ratio
    def author_ratio(df: pd.DataFrame, col: str) -> pd.DataFrame:
        df = df.sort_values(["region", "fuel", "year"]).copy()
        df[f"prev_{col}"] = df.groupby(["region", "fuel"])[col].shift(1)
        df[f"ratio_{col}"] = df[col] / df[f"prev_{col}"].replace(0, pd.NA)
        return df

    sad_long = author_ratio(sad_long, "SAD_PJ")
    aad_long = author_ratio(aad_long, "AAD_PJ")

    # --- 4. Merge: for each USE-side jump, check whether authored side jumped too
    use_jumps["year"] = use_jumps["year"].astype(int)
    enriched = use_jumps.merge(
        sad_long[["region", "fuel", "year", "SAD_PJ", "prev_SAD_PJ", "ratio_SAD_PJ"]],
        on=["region", "fuel", "year"], how="left",
    ).merge(
        aad_long[["region", "fuel", "year", "AAD_PJ", "prev_AAD_PJ", "ratio_AAD_PJ"]],
        on=["region", "fuel", "year"], how="left",
    )

    # Attribution: AUTHORED if ratio_SAD_PJ or ratio_AAD_PJ matches use ratio
    # within tolerance; SOLVER otherwise
    def attribute(row):
        rs = row.get("ratio_SAD_PJ")
        ra = row.get("ratio_AAD_PJ")
        ru = row.get("ratio_use")
        for r_auth in (rs, ra):
            if pd.notna(r_auth) and pd.notna(ru):
                if 0.8 * ru <= r_auth <= 1.2 * ru:
                    return "AUTHORED"
        if (pd.notna(rs) or pd.notna(ra)) and pd.notna(ru):
            return "SOLVER (authored is smoother)"
        if pd.isna(rs) and pd.isna(ra):
            return "SOLVER (no direct SAD/AAD anchor)"
        return "MIXED"

    enriched["attribution"] = enriched.apply(attribute, axis=1)

    # Save full results
    enriched = enriched.sort_values(
        ["is_petroleum", "region", "fuel", "year"],
        ascending=[False, True, True, True],
    )
    enriched.to_csv(OUT_DIR / "fossil_jumps_attributed.csv", index=False)
    print(f"\nSaved fossil_jumps_attributed.csv  rows={len(enriched)}")

    # --- 5. Headline tables ---
    user_regions = ["Brunei", "Cambodia", "Myanmar", "Singapore", "Timor Leste"]
    print(f"\n=== USE-side petroleum-product jumps in user's named regions ===")
    pet_user = enriched[
        enriched["is_petroleum"]
        & enriched["region"].isin(user_regions)
    ].sort_values(["region", "fuel", "year"])
    if pet_user.empty:
        print("  (none flagged)")
    else:
        cols = ["region", "fuel", "year", "prev_PJ", "this_PJ", "ratio_use",
                "prev_SAD_PJ", "SAD_PJ", "ratio_SAD_PJ", "attribution"]
        with pd.option_context("display.width", 220, "display.max_colwidth", 50,
                               "display.float_format", "{:.2f}".format):
            print(pet_user[cols].to_string(index=False))

    print(f"\n=== All other USE-side petroleum jumps (regions NOT in user's list) ===")
    pet_other = enriched[
        enriched["is_petroleum"]
        & ~enriched["region"].isin(user_regions)
    ].sort_values(["region", "fuel", "year"])
    if pet_other.empty:
        print("  (none)")
    else:
        cols = ["region", "fuel", "year", "prev_PJ", "this_PJ", "ratio_use",
                "ratio_SAD_PJ", "attribution"]
        with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
            print(pet_other[cols].head(40).to_string(index=False))

    print(f"\n=== Non-petroleum fossil USE-side jumps (Coal, Natural Gas, LNG) ===")
    coal_gas = enriched[~enriched["is_petroleum"]].sort_values(
        ["region", "fuel", "year"]
    )
    if coal_gas.empty:
        print("  (none)")
    else:
        cols = ["region", "fuel", "year", "prev_PJ", "this_PJ", "ratio_use",
                "ratio_SAD_PJ", "attribution"]
        with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
            print(coal_gas[cols].head(40).to_string(index=False))

    # Also surface production-side jumps for completeness
    print(f"\n=== Production-side fossil jumps (top 30 by magnitude) ===")
    prod_jumps_sorted = prod_jumps.sort_values(
        "delta_PJ_prod", key=lambda s: s.abs(), ascending=False
    )
    cols = ["region", "fuel", "year", "prev_PJ", "this_PJ", "delta_PJ_prod",
            "ratio_prod", "is_petroleum"]
    with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
        print(prod_jumps_sorted[cols].head(30).to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
