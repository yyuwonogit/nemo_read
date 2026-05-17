"""Indonesia electricity demand timeslice curve, 2035 and 2050.

Shows continuous-GW for every timeslice, ordered Wet/Dry × Hour, on
three demand fuels: central bus, T&D output, end-use SAD-anchored fuel.

ASCII chart in terminal + CSV in mailbox/20260513/results_v044/.
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 26.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v044")

FUELS = {
    "central_bus": 'Electricity output from "Centralized Electricity Generation" [LEAP ID:1]',
    "td_output":   'Electricity output from "Electricity Transmission and Distribution" [LEAP ID:1]',
    "esou_demand": 'Electricity output from "Energy Sector Own Use" [LEAP ID:1]',
}


def parse_ts(desc: str) -> tuple[str, int]:
    """Parse 'Wet: Hr 1' or 'Dry: Hr 14' into (season, hour)."""
    if not isinstance(desc, str) or ":" not in desc:
        return ("?", -1)
    season, hr = desc.split(":")
    return season.strip(), int(hr.strip().replace("Hr", "").strip())


def main() -> int:
    db = NemoDB(str(DB_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Timeslice descriptions
    ts = db.query("SELECT val, desc FROM TIMESLICE")
    ts["season"], ts["hour"] = zip(*ts["desc"].apply(parse_ts))
    ts = ts.set_index("val")

    rou = db.query("SELECT r, l, f, y, val FROM vrateofuse WHERE r='R1'")
    rou = decode_dims(rou, db)

    rows = []
    for label, fuel_name in FUELS.items():
        for y in ("2035", "2050"):
            sub = rou[(rou["fuel_name"] == fuel_name) & (rou["y"] == y)]
            if sub.empty:
                continue
            s = sub.set_index("l")["val"]  # rate in PJ/yr-flat-equiv
            for l in s.index:
                rows.append({
                    "fuel": label,
                    "year": y,
                    "l": l,
                    "season": ts.loc[l, "season"] if l in ts.index else "?",
                    "hour": ts.loc[l, "hour"] if l in ts.index else -1,
                    "rate_PJ_yr": s[l],
                    "GW_continuous_equiv": s[l] / 31.536,
                })

    df = pd.DataFrame(rows)
    df = df.sort_values(["fuel", "year", "season", "hour"])
    df.to_csv(OUT_DIR / "idn_demand_curve_ts.csv", index=False)
    print(f"Saved {OUT_DIR / 'idn_demand_curve_ts.csv'}\n")

    # ASCII charts
    for fuel_label in FUELS:
        for y in ("2035", "2050"):
            sub = df[(df["fuel"] == fuel_label) & (df["year"] == y)].copy()
            if sub.empty:
                continue
            piv = (
                sub.pivot_table(index="hour", columns="season",
                                values="GW_continuous_equiv", aggfunc="sum")
                .sort_index()
            )
            print(f"=== {fuel_label}  year={y}  (GW continuous-equivalent) ===")
            with pd.option_context("display.float_format", "{:.2f}".format):
                print(piv.round(2).to_string())
            print(f"  peak: {piv.max().max():.2f} GW   min: {piv.min().min():.2f} GW   "
                  f"peak/min: {piv.max().max()/piv.min().min():.2f}x\n")

            # ASCII bar chart, Wet season first then Dry
            maxv = piv.max().max()
            bar_w = 60
            for season in ("Wet", "Dry"):
                if season not in piv.columns:
                    continue
                print(f"  {season}:")
                for hr in piv.index:
                    v = piv.loc[hr, season]
                    n = int(round(v / maxv * bar_w)) if maxv > 0 else 0
                    print(f"   Hr {hr:02d} | {'#'*n}{' '*(bar_w-n)} {v:6.1f} GW")
                print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
