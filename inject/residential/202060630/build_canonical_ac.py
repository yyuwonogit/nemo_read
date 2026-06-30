r"""AC adapter — source CSVs -> ONE combined canonical (fridge-mirrored set).

SELF-CONTAINED. Standard library only. Python 3.8+.
Truth: ../AC_ANATOMY.md (mirrors ../FRIDGE_ANATOMY.md).

Emits the same variable set we injected to fridge, repointed to AC:

  KEY tree  Key\Residential\Air Conditioning\        (Activity Level, Interp)
    Percent Ownership            <- units_per_hh_parent  (units/HH, may exceed 100%)
    Size_Share\<Size>            <- size_share_pct
    Efficiency_Share\<Size>_<Eff> <- eff_share_pct       (per-scenario lever)
    Useful_EI\<Size>             <- useful_energy_intensity_toe  (TOE/unit)

  DEMAND leaf  Demand\Residential\Projections\Air Conditioning_\<Size>\<Eff_eff>
    Efficiency        <- efficiency_pct            (all scenarios, flat -> untagged)
    Exogenous Devices <- ac_exo_device.csv x1000   (TIME SERIES 2005-2060, RAS-only)

Exogenous Devices is force-tagged RAS (device-stock vars are RAS-scoped); the
injector's scenario filter then routes it ONLY to RAS, so BAS/ATS push just
Key + Efficiency (no var_not_found refusal). Everything else is auto-tagged by
scenario-invariance. Cost / Unit Capacity / load shapes are NOT in this pass
(the device-economics layer — see AC_ANATOMY.md §1.3/§8).
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_SRC = HERE / "ac" / "ac_leap_inject.csv"
DEFAULT_DEVICE = HERE / "ac" / "ac_exo_device.csv"
DEFAULT_OUT = HERE / "canonical_ac.csv"

COUNTRY_MAP = {
    "Brunei Darussalam": "Brunei", "Cambodia": "Cambodia", "Indonesia": "Indonesia",
    "Lao PDR": "Laos", "Malaysia": "Malaysia", "Myanmar": "Myanmar",
    "Philippines": "Philippines", "Singapore": "Singapore", "Thailand": "Thailand",
    "Viet Nam": "Vietnam",
}
SCENARIO_MAP = {
    "BAS": "Baseline Simulation",
    "ATS": "AMS Target Scenario",
    "RAS": "Regional Aspiration Scenario",
}
RAS_NAME = "Regional Aspiration Scenario"
EFF_SHORT = {"High_eff": "High", "Mid_eff": "Mid", "Low_eff": "Low"}

KEY_BASE = "Key\\Residential\\Air Conditioning"
DEMAND_BASE = "Demand\\Residential\\Projections\\Air Conditioning_"

PERCENT = "Percent"
TOE = "Tonnes of Oil Equivalent"
ACTIVITY = "Activity Level"

_INTERP_RE = re.compile(r"Interp\(([^)]*)\)", re.IGNORECASE)


def normalize_interp(expr):
    if not isinstance(expr, str):
        return expr

    def _fix(m):
        return f"Interp({m.group(1).replace('; ', ', ').replace(';', ',')})"

    return _INTERP_RE.sub(_fix, expr)


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


def _fingerprint(pairs):
    return tuple((int(y), round(_fnum(v), 9)) for y, v in sorted(pairs))


def _row(ams, branch, variable, unit, expr, scenario, note):
    return {"ams": ams, "branch": branch, "variable": variable,
            "expression": expr, "unit": unit, "scenario": scenario,
            "source": "AC author CSV 2026-06-30", "note": note}


def build(src, device_src, out, start_year, end_year):
    rows = list(csv.DictReader(src.open(encoding="utf-8-sig", newline="")))
    print(f"[ac] reading {src.name}: {len(rows)} rows")

    # auto-tag targets: tgt[(branch, variable, unit, ams)][scen][year] = value_str
    tgt = defaultdict(lambda: defaultdict(dict))

    def add(branch, variable, unit, ams, scen, year, value_str):
        if value_str is None or str(value_str).strip() == "":
            return
        tgt[(branch, variable, unit, ams)][scen][int(year)] = str(value_str).strip()

    dropped = set()
    for r in rows:
        ams = COUNTRY_MAP.get(r["Country"])
        if ams is None:
            dropped.add(r["Country"]); continue
        scen = SCENARIO_MAP.get(r["Scenario"])
        if scen is None:
            continue
        year = int(r["Year"])
        if not (start_year <= year <= end_year):
            continue
        size = r["Size_group"]
        eff = EFF_SHORT.get(r["Efficiency_level"], r["Efficiency_level"])
        leaf = f"{DEMAND_BASE}\\{size}\\{r['Efficiency_level']}"

        add(f"{KEY_BASE}\\Percent Ownership", ACTIVITY, PERCENT, ams, scen, year,
            r.get("units_per_hh_parent"))
        add(f"{KEY_BASE}\\Size_Share\\{size}", ACTIVITY, PERCENT, ams, scen, year,
            r.get("size_share_pct"))
        add(f"{KEY_BASE}\\Efficiency_Share\\{size}_{eff}", ACTIVITY, PERCENT, ams,
            scen, year, r.get("eff_share_pct"))
        add(f"{KEY_BASE}\\Useful_EI\\{size}", ACTIVITY, TOE, ams, scen, year,
            r.get("useful_energy_intensity_toe"))
        add(leaf, "Efficiency", PERCENT, ams, scen, year, r.get("efficiency_pct"))
    if dropped:
        print(f"[ac] WARN dropped unknown countries: {sorted(dropped)}")

    out_rows = []
    n_unt = n_tag = 0
    all_scen = set(SCENARIO_MAP.values())
    for (branch, variable, unit, ams), per_scen in tgt.items():
        trajs = {s: sorted(d.items()) for s, d in per_scen.items()}
        fps = {s: _fingerprint(p) for s, p in trajs.items()}
        invariant = set(trajs) == all_scen and len(set(fps.values())) == 1
        if invariant:
            out_rows.append(_row(ams, branch, variable, unit,
                                 _interp(trajs[next(iter(trajs))]), "",
                                 "AC Key/leaf driver"))
            n_unt += 1
        else:
            for scen, pairs in trajs.items():
                out_rows.append(_row(ams, branch, variable, unit,
                                     _interp(pairs), scen, "AC Key/leaf driver"))
                n_tag += 1

    # Exogenous Devices: TIME SERIES from ac_exo_device.csv, force-tagged RAS
    dnum = list(csv.DictReader(device_src.open(encoding="utf-8-sig", newline="")))
    dev = defaultdict(list)
    for r in dnum:
        ams = COUNTRY_MAP.get(r["Country"])
        if ams is None:
            continue
        d = _fnum(r.get("device_thousand"))
        if d is None:
            continue
        leaf = f"{DEMAND_BASE}\\{r['Size_group']}\\{r['Efficiency_level']}"
        dev[(leaf, ams)].append((int(r["Year"]), _num(d * 1000.0)))
    n_dev = 0
    for (leaf, ams), pairs in dev.items():
        out_rows.append(_row(ams, leaf, "Exogenous Devices", "Device",
                             _interp(pairs), RAS_NAME, "AC exo (RAS-only series)"))
        n_dev += 1
    print(f"[ac] device series from {device_src.name}: {len(dnum)} rows")

    out_rows.sort(key=lambda r: (r["ams"], r["variable"],
                                 (0, r["scenario"]) if r["scenario"] else (1, ""),
                                 r["branch"]))
    fields = ["ams", "branch", "variable", "expression", "unit", "scenario",
              "source", "note"]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in out_rows:
            r["expression"] = normalize_interp(r["expression"])
            w.writerow(r)

    by_var = defaultdict(int)
    for r in out_rows:
        by_var[r["variable"]] += 1
    print(f"\n[ac] wrote {out.name}  ({len(out_rows)} rows)")
    print(f"  Key/Efficiency — untagged: {n_unt}, scenario-tagged: {n_tag}")
    print(f"  Exogenous Devices (RAS-tagged time series): {n_dev}")
    print(f"  rows per variable: {dict(by_var)}")


def _args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", default=str(DEFAULT_SRC))
    p.add_argument("--device-src", default=str(DEFAULT_DEVICE))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--start-year", type=int, default=2014)
    p.add_argument("--end-year", type=int, default=2060)
    return p.parse_args()


if __name__ == "__main__":
    a = _args()
    build(Path(a.src), Path(a.device_src), Path(a.out), a.start_year, a.end_year)
