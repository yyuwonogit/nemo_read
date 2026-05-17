"""Identify period-over-period capacity jumps in v0.44 results using
trajectory-relative metrics (no fixed GW thresholds), split between:

  (1) EXOGENOUS jumps — year-over-year deltas in `ResidualCapacity`
      (authored fleet evolution; positive delta = LEAP-authored addition,
      negative = retirement).
  (2) SOLVER jumps — anomalous years in `vnewcapacity` (optimizer's
      chosen additions).

For each (region, tech) trajectory of 8 model years, a positive period
is "anomalous" when EITHER:
  - pulse_ratio = delta_GW / median_positive_delta_in_same_trajectory >= 3
    AND delta_GW >= 0.25 * peak_delta_in_same_trajectory  (rules out tiny
    bumps that beat a near-zero median),
  OR
  - stock_multiplier = delta_GW / prior_stock_GW >= 3
    AND delta_GW >= 0.05 GW (>=50 MW, just to drop epsilon-scale noise).

Outputs into mailbox/20260513/results_v044/:
  - jumps_exogenous.csv
  - jumps_solver.csv
  - jumps_retirements.csv   (negative exo deltas, separately, sorted by
                              magnitude — physically meaningful too)
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd
from nemo_read import NemoDB, decode_dims

DB_PATH = Path("feas/NEMO_25 27.sqlite")
OUT_DIR = Path("mailbox/20260513/results_v045")

PULSE_RATIO_MIN = 3.0          # delta vs trajectory's median positive delta
PEAK_FRACTION_MIN = 0.25       # delta must be ≥ this fraction of trajectory peak
STOCK_MULTIPLIER_MIN = 3.0     # delta vs prior period stock
NOISE_FLOOR_GW = 0.05          # 50 MW — drop sub-floor noise


def is_supply_tech(name: str) -> bool:
    if not isinstance(name, str):
        return False
    kws = ["Imports", "Domestic Production", "Non Energy", "LNG",
           "Crude Oil", "Pipeline"]
    return any(k in name for k in kws)


def is_storage_tech(name: str) -> bool:
    if not isinstance(name, str):
        return False
    return any(k in name for k in ["Battery", "Batteries", "Pumped", "Storage"])


def is_unmet_load(name: str) -> bool:
    if not isinstance(name, str):
        return False
    return "Unmet Load" in name


def flag_trajectory(deltas: pd.Series, prior_stocks: pd.Series) -> pd.DataFrame:
    """Given a single (r, t) trajectory of positive deltas (indexed by year)
    plus the parallel prior-stock series, return a DataFrame of flagged
    rows with diagnostic columns. Empty if nothing flags."""
    pos = deltas[deltas > 0]
    if len(pos) == 0:
        return pd.DataFrame()
    median_pos = pos.median()
    peak_pos = pos.max()
    out_rows = []
    for y, d in deltas.items():
        if d <= NOISE_FLOOR_GW:
            continue
        prior = float(prior_stocks.loc[y]) if y in prior_stocks.index else 0.0
        pulse_ratio = (d / median_pos) if median_pos > 0 else float("inf")
        stock_mult = (d / prior) if prior > 0 else float("inf")
        peak_frac = d / peak_pos if peak_pos > 0 else 0.0
        pulse_flag = (
            pulse_ratio >= PULSE_RATIO_MIN
            and peak_frac >= PEAK_FRACTION_MIN
        )
        stock_flag = (stock_mult >= STOCK_MULTIPLIER_MIN)
        if pulse_flag or stock_flag:
            out_rows.append({
                "y": y,
                "delta_GW": d,
                "prior_stock_GW": prior,
                "traj_median_pos_delta_GW": median_pos,
                "traj_peak_delta_GW": peak_pos,
                "pulse_ratio": pulse_ratio,
                "stock_multiplier": stock_mult,
                "peak_fraction": peak_frac,
                "pulse_flag": pulse_flag,
                "stock_flag": stock_flag,
            })
    return pd.DataFrame(out_rows)


def main() -> int:
    if not DB_PATH.exists():
        print(f"[FAIL] {DB_PATH}", file=sys.stderr)
        return 1
    db = NemoDB(str(DB_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Exogenous side: ResidualCapacity parameter ---
    res = db.query('SELECT r, t, y, val FROM ResidualCapacity')
    res["y"] = res["y"].astype(int)
    # --- Solver side: vnewcapacity result ---
    new = db.query('SELECT r, t, y, val FROM vnewcapacity')
    new["y"] = new["y"].astype(int)

    # Build the full (r, t) universe from both sources, decode dims once
    pairs = pd.concat([
        res[["r", "t"]],
        new[["r", "t"]],
    ]).drop_duplicates().reset_index(drop=True)
    pairs = decode_dims(pairs, db)
    pairs = pairs[
        ~pairs["tech_name"].apply(is_unmet_load)
        & ~pairs["tech_name"].apply(is_storage_tech)
    ].copy()
    pairs["is_supply_tech"] = pairs["tech_name"].apply(is_supply_tech)

    years = sorted(db.query("SELECT val FROM YEAR")["val"].astype(int).tolist())
    year_pairs = [(years[i - 1], years[i]) for i in range(1, len(years))]

    # --- EXOGENOUS trajectories ---
    exo_rows = []
    ret_rows = []  # retirements: negative exo deltas
    for _, p in pairs.iterrows():
        r, t = p["r"], p["t"]
        sub = res[(res["r"] == r) & (res["t"] == t)]
        if sub.empty:
            continue
        traj = sub.set_index("y")["val"].reindex(years, fill_value=0.0)
        # period-over-period deltas (year y vs y-5)
        deltas = {}
        priors = {}
        for y_prev, y_cur in year_pairs:
            deltas[y_cur] = traj.loc[y_cur] - traj.loc[y_prev]
            priors[y_cur] = traj.loc[y_prev]
        delta_s = pd.Series(deltas)
        prior_s = pd.Series(priors)
        flagged = flag_trajectory(delta_s, prior_s)
        for _, row in flagged.iterrows():
            exo_rows.append({
                "r": r, "t": t,
                "region_name": p["region_name"],
                "tech_name": p["tech_name"],
                "is_supply_tech": p["is_supply_tech"],
                **row.to_dict(),
            })
        # Retirements: same-sign comparison
        for y_prev, y_cur in year_pairs:
            d = traj.loc[y_cur] - traj.loc[y_prev]
            if d < -NOISE_FLOOR_GW:
                ret_rows.append({
                    "r": r, "t": t,
                    "region_name": p["region_name"],
                    "tech_name": p["tech_name"],
                    "is_supply_tech": p["is_supply_tech"],
                    "y": y_cur, "delta_GW": d,
                    "prior_stock_GW": traj.loc[y_prev],
                    "this_stock_GW": traj.loc[y_cur],
                })

    exo_df = pd.DataFrame(exo_rows).sort_values(
        ["pulse_flag", "stock_flag", "delta_GW"], ascending=[False, False, False]
    )
    exo_df.to_csv(OUT_DIR / "jumps_exogenous.csv", index=False)
    print(f"[exogenous] flagged {len(exo_df)} rows  "
          f"(pulse={int(exo_df['pulse_flag'].sum()) if len(exo_df) else 0}, "
          f"stock={int(exo_df['stock_flag'].sum()) if len(exo_df) else 0})")

    ret_df = pd.DataFrame(ret_rows).sort_values("delta_GW")
    ret_df.to_csv(OUT_DIR / "jumps_retirements.csv", index=False)
    print(f"[retirements] {len(ret_df)} negative-delta rows")

    # --- SOLVER trajectories ---
    sol_rows = []
    for _, p in pairs.iterrows():
        r, t = p["r"], p["t"]
        sub = new[(new["r"] == r) & (new["t"] == t)]
        if sub.empty:
            continue
        traj = sub.set_index("y")["val"].reindex(years, fill_value=0.0)
        # vnewcapacity IS the delta — no subtraction needed
        delta_s = traj.copy()
        # Prior stock = ResidualCapacity at y_prev + sum of new in earlier years
        res_traj = (
            res[(res["r"] == r) & (res["t"] == t)]
            .set_index("y")["val"].reindex(years, fill_value=0.0)
        )
        cum_new = traj.cumsum().shift(1, fill_value=0.0)
        prior_stock = res_traj + cum_new  # rough; ignores retirements
        # Reindex priors to match the periods detected from delta_s
        prior_s = prior_stock.copy()
        flagged = flag_trajectory(delta_s, prior_s)
        for _, row in flagged.iterrows():
            sol_rows.append({
                "r": r, "t": t,
                "region_name": p["region_name"],
                "tech_name": p["tech_name"],
                "is_supply_tech": p["is_supply_tech"],
                **row.to_dict(),
            })

    sol_df = pd.DataFrame(sol_rows).sort_values(
        ["pulse_flag", "stock_flag", "delta_GW"], ascending=[False, False, False]
    )
    sol_df.to_csv(OUT_DIR / "jumps_solver.csv", index=False)
    print(f"[solver] flagged {len(sol_df)} rows  "
          f"(pulse={int(sol_df['pulse_flag'].sum()) if len(sol_df) else 0}, "
          f"stock={int(sol_df['stock_flag'].sum()) if len(sol_df) else 0})")

    # --- print top-of-list for each ---
    def show(df: pd.DataFrame, title: str, n: int = 15) -> None:
        if df.empty:
            print(f"\n[{title}] (empty)")
            return
        cols = ["region_name", "tech_name", "y", "delta_GW",
                "prior_stock_GW", "pulse_ratio", "stock_multiplier",
                "is_supply_tech"]
        print(f"\n[{title}] top {min(n, len(df))} (generation+supply combined):")
        with pd.option_context('display.width', 200, 'display.max_colwidth', 50,
                               'display.float_format', '{:.3g}'.format):
            print(df[cols].head(n).to_string(index=False))
        gen = df[~df["is_supply_tech"]]
        print(f"\n[{title}] top {min(n, len(gen))} GENERATION ONLY:")
        if gen.empty:
            print("  (none)")
        else:
            with pd.option_context('display.width', 200, 'display.max_colwidth', 50,
                                   'display.float_format', '{:.3g}'.format):
                print(gen[cols].head(n).to_string(index=False))

    show(exo_df, "EXOGENOUS jumps")
    show(sol_df, "SOLVER jumps")

    if not ret_df.empty:
        print("\n[retirements] top 10 by magnitude:")
        with pd.option_context('display.width', 200,
                               'display.float_format', '{:.3g}'.format):
            cols = ["region_name", "tech_name", "y", "delta_GW",
                    "prior_stock_GW", "this_stock_GW", "is_supply_tech"]
            print(ret_df[cols].head(10).to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
