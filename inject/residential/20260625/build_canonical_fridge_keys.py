r"""Phase-1 fridge adapter — source CSV -> canonical targeting the KEY tree.

SELF-CONTAINED. Standard library only. Safe to copy out of the repo with
`fridge_leap_inject.csv` and run anywhere with Python 3.8+.

Single source of truth for the fridge structure: ../FRIDGE_ANATOMY.md.

Builds the canonical for the FOUR demand-driver Key Assumption branches that
the `Refrigeration_` demand tree references. The Phase-2 leaf inject (the leaf
`Efficiency` + `Demand Cost` variables — the only leaf inputs that exist in
`aeo9_v0.64_w_result`, per FRIDGE_ANATOMY.md §1.3a) is built separately. The
device-stock leaf variables (Unit Capacity / Exogenous Devices / Capital / OM
/ Lifetime) do NOT exist in this area and are never authored.

------------------------------------------------------------------------------
KEY TREE (data store) — what this script authors
------------------------------------------------------------------------------
  Key\Residential\Refrigeration\
  ├── Percent Ownership                  ← ownership_parent_pct        [%]
  ├── Size_Share\<Size>                  ← size_share_pct              [%]
  ├── Efficiency_Share\<Size>_<Eff>      ← eff_share_pct               [%]
  └── Useful_EI\<Size>                   ← useful_energy_intensity_toe [TOE/HH]

  <Size> = Large | Medium | Small           (CSV Size_group, identity)
  <Eff>  = High | Mid | Low                  (CSV Efficiency_level High_eff/Mid_eff/Low_eff
                                              with the "_eff" suffix dropped)
  Every node's value lives on the `Activity Level` variable, as Interp(...).

Scenario tagging is AUTO-DETECTED: a node whose trajectory is identical across
BAS/ATS/RAS is emitted ONCE untagged (the injector applies it to every
scenario); a node that differs is emitted once per scenario, tagged with the
LEAP scenario name. In this data: Percent Ownership + Useful_EI come out
untagged; Size_Share + Efficiency_Share come out scenario-tagged.

Year range: the FULL 2014->2060 span from the CSV (NOT 2025+), so the whole
trajectory is overwritten cleanly.

Useful_EI is flat across years -> collapsed to a single Interp(2014, v) anchor.

Original CSV value strings are preserved verbatim in the expressions (full
precision, period decimal) — no float round-trip.
------------------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_SRC = HERE / "fridge_leap_inject.csv"
DEFAULT_OUT = HERE / "canonical_fridge.csv"

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
EFF_SHORT = {"High_eff": "High", "Mid_eff": "Mid", "Low_eff": "Low"}

# VERIFY this prefix against the live area on the first dry-run. The reference
# strings we saw used `Key\Residential\Refrigeration\...`.
KEY_BASE = "Key\\Residential\\Refrigeration"

PERCENT = "Percent"
TOE = "Tonnes of Oil Equivalent"
ACTIVITY = "Activity Level"

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


def _interp(pairs):
    """pairs: list of (year:int, value_str). Collapse flat -> single anchor."""
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
    print(f"[fridge-keys] reading {src.name}: {len(rows)} rows")

    # target[(branch, unit, ams)][leap_scenario][year] = original value string
    target = defaultdict(lambda: defaultdict(dict))

    def add(branch, unit, ams, scen, year, value_str):
        if value_str is None or str(value_str).strip() == "":
            return
        target[(branch, unit, ams)][scen][int(year)] = str(value_str).strip()

    dropped = set()
    for r in rows:
        ams = COUNTRY_MAP.get(r["Country"])
        if ams is None:
            dropped.add(r["Country"]); continue
        scen = SCENARIO_MAP.get(r["Scenario"])
        if scen is None:
            continue
        year = int(r["Year"])
        if year < start_year or year > end_year:
            continue
        size = r["Size_group"]
        eff = EFF_SHORT.get(r["Efficiency_level"], r["Efficiency_level"])

        add(f"{KEY_BASE}\\Percent Ownership", PERCENT, ams, scen, year,
            r.get("ownership_parent_pct"))
        add(f"{KEY_BASE}\\Size_Share\\{size}", PERCENT, ams, scen, year,
            r.get("size_share_pct"))
        add(f"{KEY_BASE}\\Efficiency_Share\\{size}_{eff}", PERCENT, ams, scen,
            year, r.get("eff_share_pct"))
        add(f"{KEY_BASE}\\Useful_EI\\{size}", TOE, ams, scen, year,
            r.get("useful_energy_intensity_toe"))
    if dropped:
        print(f"[fridge-keys] WARN dropped unknown countries: {sorted(dropped)}")

    out_rows = []
    n_unt = n_tag = 0
    all_scen = set(SCENARIO_MAP.values())
    for (branch, unit, ams), per_scen in target.items():
        trajs = {s: sorted(d.items()) for s, d in per_scen.items()}
        fps = {s: _fingerprint(p) for s, p in trajs.items()}
        invariant = set(trajs) == all_scen and len(set(fps.values())) == 1
        if invariant:
            any_scen = next(iter(trajs))
            out_rows.append(_row(ams, branch, unit, _interp(trajs[any_scen]), ""))
            n_unt += 1
        else:
            for scen, pairs in trajs.items():
                out_rows.append(_row(ams, branch, unit, _interp(pairs), scen))
                n_tag += 1

    out_rows.sort(key=lambda r: (r["ams"],
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

    by_branch = defaultdict(int)
    for r in out_rows:
        leaf = r["branch"].split("\\")[3] if len(r["branch"].split("\\")) > 3 else r["branch"]
        by_branch[leaf] += 1
    print(f"\n[fridge-keys] wrote {out.name}  ({len(out_rows)} rows)")
    print(f"  Key-tree drivers — untagged: {n_unt}, scenario-tagged: {n_tag}")
    print(f"  rows per family: {dict(by_branch)}")
    print(f"  year window: {start_year}-{end_year}")


def _row(ams, branch, unit, expr, scenario):
    return {
        "ams": ams, "branch": branch, "variable": ACTIVITY,
        "expression": expr, "unit": unit, "scenario": scenario,
        "source": "Fridge author CSV 2026-06-25",
        "note": "Phase-1 Key-tree driver",
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
