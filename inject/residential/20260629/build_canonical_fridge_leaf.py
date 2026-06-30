r"""Phase-2 fridge adapter — source CSV -> canonical for the DEMAND-LEAF inputs.

SELF-CONTAINED. Standard library only. Python 3.8+.
Single source of truth for the fridge structure: ../FRIDGE_ANATOMY.md.

Target area `aeo9_v0.64` carries the DEVICE-STOCK leaf (FRIDGE_ANATOMY.md
§1.3b). Authorable leaf inputs there: `Efficiency` and `Exogenous Devices`.
(Demand Cost belongs to the OTHER leaf variant in `aeo9_v0.64_w_result`
§1.3a — do NOT author it here.)

  | LEAP variable     | source                          | transform           | tagging  |
  |-------------------|---------------------------------|---------------------|----------|
  | Efficiency        | fridge_leap_inject.efficiency_pct | as-is, flat       | untagged |
  | Exogenous Devices | fridge_device_numbers.csv (2005-2025 series) | x1000 -> Device, TIME SERIES | untagged |

Exogenous Devices is a TIME SERIES (the back-cast device fleet 2005-2025 from
fridge_device_numbers.csv), NOT a single 2025 anchor. It is RAS-scoped on the
device-stock leaf, so inject under RAS only.

Eff leaf naming is the Demand-tree form: nested `<Size>\<Eff_eff>`, keeping the
`_eff` suffix (High_eff / Mid_eff / Low_eff).

Both targets are scenario-invariant -> emitted untagged (apply to all
scenarios). Original CSV value strings preserved verbatim for Efficiency;
Exogenous Devices is device_thousand x 1000 at 2025 only.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_SRC = HERE / "fridge_leap_inject.csv"
DEFAULT_OUT = HERE / "canonical_fridge_leaf.csv"

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

DEMAND_BASE = "Demand\\Residential\\Projections\\Refrigeration_"
DEVICE_SRC = HERE / "fridge_device_numbers.csv"   # back-cast 2005-2025 series

_INTERP_RE = re.compile(r"Interp\(([^)]*)\)", re.IGNORECASE)


def normalize_interp(expr: str) -> str:
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


def build(src, out, start_year, end_year):
    rows = list(csv.DictReader(src.open(encoding="utf-8-sig", newline="")))
    print(f"[fridge-leaf] reading {src.name}: {len(rows)} rows")

    # Efficiency: eff[(branch, ams)][scen][year] = value string (from inject CSV)
    eff = defaultdict(lambda: defaultdict(dict))
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
        leaf = f"{DEMAND_BASE}\\{r['Size_group']}\\{r['Efficiency_level']}"
        v = r.get("efficiency_pct")
        if v is not None and str(v).strip() != "":
            eff[(leaf, ams)][scen][year] = str(v).strip()

    # Exogenous Devices: TIME SERIES from fridge_device_numbers.csv (scenario-less,
    # 2005-2025). dev[(branch, ams)] = list of (year, value_str x1000)
    dev = defaultdict(list)
    dnum = list(csv.DictReader(DEVICE_SRC.open(encoding="utf-8-sig", newline="")))
    for r in dnum:
        ams = COUNTRY_MAP.get(r["Country"])
        if ams is None:
            continue
        d = _fnum(r.get("device_thousand"))
        if d is None:
            continue
        leaf = f"{DEMAND_BASE}\\{r['Size_group']}\\{r['Efficiency_level']}"
        dev[(leaf, ams)].append((int(r["Year"]), _num(d * 1000.0)))
    if dropped:
        print(f"[fridge-leaf] WARN dropped unknown countries: {sorted(dropped)}")
    print(f"[fridge-leaf] device series from {DEVICE_SRC.name}: {len(dnum)} rows")

    out_rows = []
    all_scen = set(SCENARIO_MAP.values())

    # Efficiency rows (auto-tag; expected untagged + flat)
    n_eff = 0
    for (branch, ams), per_scen in eff.items():
        trajs = {s: sorted(d.items()) for s, d in per_scen.items()}
        fps = {s: _fingerprint(p) for s, p in trajs.items()}
        invariant = set(trajs) == all_scen and len(set(fps.values())) == 1
        if invariant:
            out_rows.append(_row(ams, branch, "Efficiency", "Percent",
                                 _interp(trajs[next(iter(trajs))]), ""))
            n_eff += 1
        else:
            for scen, pairs in trajs.items():
                out_rows.append(_row(ams, branch, "Efficiency", "Percent",
                                     _interp(pairs), scen))
                n_eff += 1

    # Exogenous Devices rows (TIME SERIES 2005-2025, untagged)
    n_dev = 0
    for (branch, ams), pairs in dev.items():
        out_rows.append(_row(ams, branch, "Exogenous Devices", "Device",
                             _interp(pairs), ""))
        n_dev += 1

    out_rows.sort(key=lambda r: (r["ams"], r["variable"], r["branch"]))

    fields = ["ams", "branch", "variable", "expression", "unit", "scenario",
              "source", "note"]
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in out_rows:
            r["expression"] = normalize_interp(r["expression"])
            w.writerow(r)

    print(f"\n[fridge-leaf] wrote {out.name}  ({len(out_rows)} rows)")
    print(f"  Efficiency rows: {n_eff}   Exogenous Devices rows: {n_dev}")


def _row(ams, branch, var, unit, expr, scenario):
    return {
        "ams": ams, "branch": branch, "variable": var,
        "expression": expr, "unit": unit, "scenario": scenario,
        "source": "Fridge author CSV 2026-06-29",
        "note": "Phase-2 Demand-leaf input (device-stock leaf)",
    }


def _args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", default=str(DEFAULT_SRC))
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--start-year", type=int, default=2014)
    p.add_argument("--end-year", type=int, default=2060)
    return p.parse_args()


if __name__ == "__main__":
    a = _args()
    build(Path(a.src), Path(a.out), a.start_year, a.end_year)
