r"""FULL residential inject adapter (AC or fridge) -> one combined canonical.

SELF-CONTAINED, stdlib only. Truth: ../AC_ANATOMY.md / ../FRIDGE_ANATOMY.md.
Usage: python build_canonical_full.py --appliance {ac|fridge}

Emits the FULL confirmed set:

  KEY  Key\Residential\<App>\  (Activity Level, Interp)
    Percent Ownership   <- parent col (AC units_per_hh_parent / fridge ownership_parent_pct)
    Size_Share\<Size>   <- size_share_pct
    Efficiency_Share\<Size>_<Eff> <- eff_share_pct
    Useful_EI\<Size>    <- useful_energy_intensity_toe   [TOE]

  LEAF  Demand\Residential\Projections\<App>_\<Size>\<Eff_eff>
    Efficiency        <- efficiency_pct                  [%, ALL scenarios]
    Unit Capacity     <- unit_capacity_kw                [kW, RAS-only]
    Capital Cost      <- price_usd  (full; LEAP annualizes by Lifetime)  [RAS-only]
    Variable OM Cost  <- om_electricity_usd              [RAS-only]
    Fixed OM Cost     <- 0                               [RAS-only]
    Lifetime          <- 15 (AC) / 12 (fridge)           [Years, RAS-only]
    Exogenous Devices <- <app>_exo_device.csv x1000      [Device, 2005-2060 series, RAS-only]

Scenario tagging: Key Percent Ownership + Useful_EI + leaf Efficiency are
scenario-invariant -> untagged (apply to all). Size_Share + Efficiency_Share
auto-tag per scenario. The device-stock leaf block (Unit Capacity, Capital,
Var/Fixed OM, Lifetime, Exo) is RAS-only -> force-tagged RAS so a single
3-scenario run routes them to RAS only (BAS/ATS get Key + Efficiency).
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent

APP = {
    "ac": dict(
        src=HERE / "ac" / "ac_leap_inject.csv",
        exo=HERE / "ac" / "ac_exo_device.csv",
        key="Key\\Residential\\Air Conditioning",
        demand="Demand\\Residential\\Projections\\Air Conditioning_",
        parent_col="units_per_hh_parent",
        lifetime="15",
    ),
    "fridge": dict(
        src=HERE / "fridge" / "fridge_leap_inject.csv",
        exo=HERE / "fridge" / "fridge_exo_device.csv",
        key="Key\\Residential\\Refrigeration",
        demand="Demand\\Residential\\Projections\\Refrigeration_",
        parent_col="ownership_parent_pct",
        lifetime="12",
    ),
}

COUNTRY_MAP = {
    "Brunei Darussalam": "Brunei", "Cambodia": "Cambodia", "Indonesia": "Indonesia",
    "Lao PDR": "Laos", "Malaysia": "Malaysia", "Myanmar": "Myanmar",
    "Philippines": "Philippines", "Singapore": "Singapore", "Thailand": "Thailand",
    "Viet Nam": "Vietnam",
}
SCENARIO_MAP = {"BAS": "Baseline Simulation", "ATS": "AMS Target Scenario",
                "RAS": "Regional Aspiration Scenario"}
RAS_NAME = "Regional Aspiration Scenario"
EFF_SHORT = {"High_eff": "High", "Mid_eff": "Mid", "Low_eff": "Low"}
PERCENT, TOE, ACTIVITY = "Percent", "Tonnes of Oil Equivalent", "Activity Level"

_INTERP_RE = re.compile(r"Interp\(([^)]*)\)", re.IGNORECASE)


def normalize_interp(expr):
    if not isinstance(expr, str):
        return expr
    return _INTERP_RE.sub(lambda m: f"Interp({m.group(1).replace('; ', ', ').replace(';', ',')})", expr)


def _fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _num(v):
    s = f"{float(v):.6f}".rstrip("0").rstrip(".")
    return s if s and s != "-0" else "0"


def _interp(pairs):
    pairs = sorted(pairs, key=lambda p: p[0])
    rounded = {round(_fnum(v), 9) for _, v in pairs if _fnum(v) is not None}
    if len(rounded) == 1:
        y, v = pairs[0]
        return f"Interp({int(y)}, {v})"
    return "Interp(" + ", ".join(f"{int(y)}, {v}" for y, v in pairs) + ")"


def _fp(pairs):
    return tuple((int(y), round(_fnum(v), 9)) for y, v in sorted(pairs))


def _row(ams, branch, variable, unit, expr, scenario, note):
    return {"ams": ams, "branch": branch, "variable": variable, "expression": expr,
            "unit": unit, "scenario": scenario, "source": "author CSV 2026-06-30",
            "note": note}


def build(appliance, start_year, end_year, out):
    cfg = APP[appliance]
    KEY, DEM = cfg["key"], cfg["demand"]
    rows = list(csv.DictReader(cfg["src"].open(encoding="utf-8-sig", newline="")))
    print(f"[{appliance}] reading {cfg['src'].name}: {len(rows)} rows")

    out_rows = []

    # ---- auto-tagged set: Key + leaf Efficiency -----------------------------
    auto = defaultdict(lambda: defaultdict(dict))  # (br,var,unit,ams)->scen->yr->val

    def add(br, var, unit, ams, scen, yr, val):
        if val is None or str(val).strip() == "":
            return
        auto[(br, var, unit, ams)][scen][int(yr)] = str(val).strip()

    dropped = set()
    for r in rows:
        ams = COUNTRY_MAP.get(r["Country"])
        if ams is None:
            dropped.add(r["Country"]); continue
        scen = SCENARIO_MAP.get(r["Scenario"])
        if scen is None:
            continue
        yr = int(r["Year"])
        if not (start_year <= yr <= end_year):
            continue
        size = r["Size_group"]
        eff = EFF_SHORT.get(r["Efficiency_level"], r["Efficiency_level"])
        leaf = f"{DEM}\\{size}\\{r['Efficiency_level']}"
        add(f"{KEY}\\Percent Ownership", ACTIVITY, PERCENT, ams, scen, yr, r.get(cfg["parent_col"]))
        add(f"{KEY}\\Size_Share\\{size}", ACTIVITY, PERCENT, ams, scen, yr, r.get("size_share_pct"))
        add(f"{KEY}\\Efficiency_Share\\{size}_{eff}", ACTIVITY, PERCENT, ams, scen, yr, r.get("eff_share_pct"))
        add(f"{KEY}\\Useful_EI\\{size}", ACTIVITY, TOE, ams, scen, yr, r.get("useful_energy_intensity_toe"))
        add(leaf, "Efficiency", PERCENT, ams, scen, yr, r.get("efficiency_pct"))
    if dropped:
        print(f"[{appliance}] WARN dropped: {sorted(dropped)}")

    all_scen = set(SCENARIO_MAP.values())
    n_unt = n_tag = 0
    for (br, var, unit, ams), per in auto.items():
        trajs = {s: sorted(d.items()) for s, d in per.items()}
        inv = set(trajs) == all_scen and len({_fp(p) for p in trajs.values()}) == 1
        if inv:
            out_rows.append(_row(ams, br, var, unit, _interp(trajs[next(iter(trajs))]), "", "driver"))
            n_unt += 1
        else:
            for s, p in trajs.items():
                out_rows.append(_row(ams, br, var, unit, _interp(p), s, "driver"))
                n_tag += 1

    # ---- RAS-only device-stock leaf block (read from RAS rows) --------------
    rascol = defaultdict(list)  # (leaf,ams,var,unit)->[(yr,val)]
    cells = set()  # (leaf, ams)
    for r in rows:
        if r["Scenario"] != "RAS":
            continue
        ams = COUNTRY_MAP.get(r["Country"])
        if ams is None:
            continue
        yr = int(r["Year"])
        if not (start_year <= yr <= end_year):
            continue
        leaf = f"{DEM}\\{r['Size_group']}\\{r['Efficiency_level']}"
        cells.add((leaf, ams))
        for var, unit, col in [("Unit Capacity", "kW", "unit_capacity_kw"),
                               ("Capital Cost", "USD", "price_usd"),
                               ("Variable OM Cost", "USD", "om_electricity_usd")]:
            v = (r.get(col) or "").strip()
            if v:
                rascol[(leaf, ams, var, unit)].append((yr, v))
    n_ras = 0
    for (leaf, ams, var, unit), pairs in rascol.items():
        out_rows.append(_row(ams, leaf, var, unit, _interp(pairs), RAS_NAME, "RAS device-stock"))
        n_ras += 1
    # Fixed OM = 0 and Lifetime = constant, per cell, RAS-only
    for (leaf, ams) in sorted(cells):
        out_rows.append(_row(ams, leaf, "Fixed OM Cost", "USD", "0", RAS_NAME, "RAS device-stock"))
        out_rows.append(_row(ams, leaf, "Lifetime", "Years", cfg["lifetime"], RAS_NAME, "RAS device-stock"))
        n_ras += 2

    # ---- Exogenous Devices: 2005-2060 series, RAS-only ----------------------
    dnum = list(csv.DictReader(cfg["exo"].open(encoding="utf-8-sig", newline="")))
    dev = defaultdict(list)
    for r in dnum:
        ams = COUNTRY_MAP.get(r["Country"])
        if ams is None:
            continue
        d = _fnum(r.get("device_thousand"))
        if d is None:
            continue
        leaf = f"{DEM}\\{r['Size_group']}\\{r['Efficiency_level']}"
        dev[(leaf, ams)].append((int(r["Year"]), _num(d * 1000.0)))
    n_exo = 0
    for (leaf, ams), pairs in dev.items():
        out_rows.append(_row(ams, leaf, "Exogenous Devices", "Device", _interp(pairs), RAS_NAME, "RAS exo series"))
        n_exo += 1
    print(f"[{appliance}] exo from {cfg['exo'].name}: {len(dnum)} rows")

    out_rows.sort(key=lambda r: (r["ams"], r["variable"],
                                 (0, r["scenario"]) if r["scenario"] else (1, ""), r["branch"]))
    fields = ["ams", "branch", "variable", "expression", "unit", "scenario", "source", "note"]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in out_rows:
            r["expression"] = normalize_interp(r["expression"])
            w.writerow(r)

    by_var = defaultdict(int)
    for r in out_rows:
        by_var[r["variable"]] += 1
    print(f"\n[{appliance}] wrote {out.name}  ({len(out_rows)} rows)")
    print(f"  driver untagged: {n_unt}, tagged: {n_tag} | RAS device-stock: {n_ras} | exo: {n_exo}")
    print(f"  rows per variable: {dict(by_var)}")


def _args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--appliance", required=True, choices=["ac", "fridge"])
    p.add_argument("--out")
    p.add_argument("--start-year", type=int, default=2014)
    p.add_argument("--end-year", type=int, default=2060)
    return p.parse_args()


if __name__ == "__main__":
    a = _args()
    out = Path(a.out) if a.out else HERE / f"canonical_{a.appliance}_full.csv"
    build(a.appliance, a.start_year, a.end_year, out)
