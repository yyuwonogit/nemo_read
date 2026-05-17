"""(1) Peak electricity load per AMS per year, year-over-year jumps.
(2) Installed-capacity dips (residual + solver) on power-gen tech —
    any year-over-year decrease in vtotalcapacityannual.

Outputs into mailbox/20260513/results_v044/:
  - peak_load_by_country.csv   one row per (region, year)
  - capacity_dips.csv           one row per (region, tech, year) with dip
  - capacity_trajectory_shape.csv  smoothness metric per (region, tech)
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 27.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v045")

ELEC_FUEL = 'Electricity output from "Centralized Electricity Generation" [LEAP ID:1]'
NOISE_DIP_GW = 0.05  # 50 MW — drop sub-floor noise


def is_supply_tech(name: str) -> bool:
    kws = ["Imports", "Domestic Production", "Non Energy", "LNG",
           "Crude Oil", "Pipeline"]
    return any(k in name for k in kws)


def is_storage(name: str) -> bool:
    return any(k in name for k in ["Battery", "Batteries", "Pumped", "Storage"])


def is_unmet(name: str) -> bool:
    return "Unmet Load" in name


def categorize(name: str) -> str:
    if not isinstance(name, str): return "Unknown"
    n = name.lower()
    if "unmet load" in n: return "Unmet Load"
    if "solar pv" in n or "solar floating" in n: return "Solar PV"
    if "solar csp" in n: return "Solar CSP"
    if "wind onshore" in n: return "Wind Onshore"
    if "wind offshore" in n: return "Wind Offshore"
    if "small hydro" in n: return "Small Hydro"
    if "hydro" in n: return "Large Hydro"
    if "geothermal" in n: return "Geothermal"
    if "nuclear" in n: return "Nuclear"
    if "biomass" in n or "biogas" in n or "msw" in n or "waste" in n: return "Biomass/Waste"
    if "coal" in n or "igcc" in n or "cfb" in n or "subcrit" in n or "supercrit" in n: return "Coal"
    if "ccgt" in n or "ocgt" in n or "gas turbine" in n or "gas combined" in n or "gas engine" in n: return "Gas"
    if "diesel" in n: return "Diesel"
    if "fuel oil" in n: return "Fuel Oil"
    if "tidal" in n or "wave" in n: return "Marine"
    return "Other"


def is_renewable(cat: str) -> bool:
    return cat in {
        "Solar PV", "Solar CSP", "Wind Onshore", "Wind Offshore",
        "Small Hydro", "Large Hydro", "Geothermal", "Biomass/Waste",
        "Nuclear", "Marine",
    }


def main() -> int:
    if not DB_PATH.exists():
        print(f"[FAIL] {DB_PATH}", file=sys.stderr)
        return 1
    db = NemoDB(str(DB_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- 1. Peak electricity load per AMS per year ----------
    rop = db.query('SELECT r, l, f, y, val FROM vrateofproduction')
    rop = decode_dims(rop, db)
    elec = rop[rop["fuel_name"] == ELEC_FUEL].copy()
    # Peak = max over timeslices (l) per (r, y)
    peak = (
        elec.groupby(["r", "region_name", "y"])
        .agg(peak_rate_PJ_yr=("val", "max"),
             peak_ts=("val", "idxmax"))
        .reset_index()
    )
    # also pull the timeslice description for the peak row
    peak["l"] = peak["peak_ts"].apply(lambda i: elec.loc[i, "l"])
    peak["timeslice_name"] = peak["peak_ts"].apply(
        lambda i: elec.loc[i, "timeslice_name"] if "timeslice_name" in elec.columns else ""
    )
    peak = peak.drop(columns=["peak_ts"])
    # Convert rate (PJ/yr if run flat) to "continuous GW equivalent": GW = PJ/yr / 31.536
    peak["peak_GW_equiv"] = peak["peak_rate_PJ_yr"] / 31.536
    peak["y_int"] = peak["y"].astype(int)
    peak = peak.sort_values(["region_name", "y_int"]).reset_index(drop=True)
    # YoY delta and ratio per region
    peak["prev_peak_GW"] = peak.groupby("region_name")["peak_GW_equiv"].shift(1)
    peak["delta_GW"] = peak["peak_GW_equiv"] - peak["prev_peak_GW"]
    peak["growth_ratio"] = peak["peak_GW_equiv"] / peak["prev_peak_GW"]
    peak.to_csv(OUT_DIR / "peak_load_by_country.csv", index=False)
    print(f"[peak] wrote peak_load_by_country.csv  rows={len(peak)}")

    # Show table
    pivot_pk = peak.pivot_table(index="region_name", columns="y", values="peak_GW_equiv")
    print("\n=== Peak load (GW continuous-equivalent) per (region, year) ===")
    with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
        print(pivot_pk.round(2).to_string())

    # YoY ratio table
    pivot_r = peak.pivot_table(index="region_name", columns="y", values="growth_ratio")
    print("\n=== YoY peak-load growth ratio (peak[y] / peak[y-5]) ===")
    with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
        print(pivot_r.round(2).to_string())

    # Flag "jumps" — growth ratio > 1.5 (50% step in 5 years = ~8.5%/yr; >50% is sudden)
    jumps = peak[(peak["growth_ratio"] > 1.5) | (peak["growth_ratio"] < 0.8)].copy()
    if not jumps.empty:
        print(f"\n=== Peak-load year-over-year jumps (>1.5x OR <0.8x) — {len(jumps)} rows ===")
        with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
            print(jumps[["region_name", "y", "prev_peak_GW", "peak_GW_equiv",
                         "delta_GW", "growth_ratio", "timeslice_name"]].to_string(index=False))

    # ---------- 2. Installed capacity dips on power-gen tech ----------
    cap = db.query('SELECT r, t, y, val FROM vtotalcapacityannual')
    cap = decode_dims(cap, db)
    cap = cap[
        ~cap["tech_name"].apply(is_unmet)
        & ~cap["tech_name"].apply(is_storage)
        & ~cap["tech_name"].apply(is_supply_tech)
    ].copy()
    cap["cat"] = cap["tech_name"].apply(categorize)
    cap["renew"] = cap["cat"].apply(is_renewable)
    cap["y_int"] = cap["y"].astype(int)
    cap = cap.sort_values(["r", "t", "y_int"]).reset_index(drop=True)
    cap["prev_GW"] = cap.groupby(["r", "t"])["val"].shift(1)
    cap["delta_GW"] = cap["val"] - cap["prev_GW"]

    dips = cap[(cap["delta_GW"] < -NOISE_DIP_GW)].copy()
    dips["dip_GW"] = -dips["delta_GW"]
    dips = dips[[
        "r", "region_name", "t", "tech_name", "cat", "renew",
        "y", "prev_GW", "val", "delta_GW", "dip_GW",
    ]].rename(columns={"val": "this_GW"})
    dips = dips.sort_values(["renew", "dip_GW"], ascending=[False, False])
    dips.to_csv(OUT_DIR / "capacity_dips.csv", index=False)
    print(f"\n[dips] wrote capacity_dips.csv  rows={len(dips)}")
    print(f"[dips] renewable/clean-tech dips: {int(dips['renew'].sum())}")
    print(f"[dips] fossil/diesel dips:       {int((~dips['renew']).sum())}")

    if not dips.empty:
        renew_dips = dips[dips["renew"]]
        if not renew_dips.empty:
            print(f"\n=== Renewable/clean-tech DIPS (most suspect — long-lifetime techs shouldn't dip) ===")
            with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
                print(renew_dips[["region_name", "tech_name", "cat", "y",
                                   "prev_GW", "this_GW", "dip_GW"]].head(30).to_string(index=False))
        foss_dips = dips[~dips["renew"]]
        if not foss_dips.empty:
            print(f"\n=== Fossil/diesel DIPS (often intentional phaseout, but check magnitudes) ===")
            with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
                print(foss_dips[["region_name", "tech_name", "cat", "y",
                                  "prev_GW", "this_GW", "dip_GW"]].head(20).to_string(index=False))

    # ---------- 3. Trajectory smoothness score ----------
    # For each (r, t) trajectory with peak > 0.05 GW, compute:
    #   - n_dips (count of negative period deltas)
    #   - max positive delta vs median positive delta (pulse score)
    #   - overall non-monotonicity flag
    rows = []
    for (r, t), g in cap.groupby(["r", "t"]):
        traj = g.sort_values("y_int")["val"].to_numpy()
        if traj.max() < NOISE_DIP_GW:
            continue
        diffs = traj[1:] - traj[:-1]
        pos = diffs[diffs > 0]
        neg = diffs[diffs < -NOISE_DIP_GW]
        pulse = (pos.max() / pd.Series(pos).median()) if len(pos) >= 2 else float("nan")
        rows.append({
            "r": g["r"].iloc[0], "t": t,
            "region_name": g["region_name"].iloc[0],
            "tech_name": g["tech_name"].iloc[0],
            "cat": g["cat"].iloc[0],
            "renew": g["renew"].iloc[0],
            "peak_GW": traj.max(),
            "first_GW": traj[0],
            "last_GW": traj[-1],
            "n_dips": int((diffs < -NOISE_DIP_GW).sum()),
            "biggest_dip_GW": float(neg.min()) if neg.size else 0.0,
            "biggest_pos_delta_GW": float(pos.max()) if pos.size else 0.0,
            "pulse_ratio": pulse,
            "monotone_increasing": bool((diffs >= -NOISE_DIP_GW).all()),
        })
    shape = pd.DataFrame(rows).sort_values(
        ["renew", "n_dips", "biggest_dip_GW"],
        ascending=[False, False, True],
    )
    shape.to_csv(OUT_DIR / "capacity_trajectory_shape.csv", index=False)
    print(f"\n[shape] wrote capacity_trajectory_shape.csv  rows={len(shape)}")
    nm = shape[~shape["monotone_increasing"]]
    print(f"[shape] non-monotone trajectories: {len(nm)}  "
          f"(renewable: {int(nm['renew'].sum())}, fossil: {int((~nm['renew']).sum())})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
