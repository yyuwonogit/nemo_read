"""Probe the EXACT 'Activity shares under Large sum to 0.0%' issue.

Read-only. Area-locked to aeo9_v0.74. For Brunei, across Current Accounts /
Baseline / AMS Target / Regional Aspiration, reads Variable.Expression on:
  - the 3 AC Large efficiency leaves (Demand tree, Activity Level)
  - the 3 AC Large efficiency-share keys (Key tree, Activity Level)
evaluates each Interp at 2025 offline, and sums the three shares per scenario.

Purpose: prove whether the base-year eff-share sum is 0 because Current
Accounts holds 0 (the CA-column hole) and/or Baseline's override failed to
land. Pure Expression reads (input-side vars) — no result-side reads, no
DataUnitText, no calc. Restores the original ActiveScenario at the end.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root -> import nemo_read

from nemo_read._leap_com import dispatch_leap, safe_expression
from nemo_read._heartbeat import HeartbeatLogger

EXPECT_AREA = "aeo9_v0.74"
REGION = "Brunei"
SCENARIOS = [
    "Current Accounts",
    "Baseline Simulation",
    "AMS Target Scenario",
    "Regional Aspiration Scenario",
]
KEY = r"Key\Residential\Air Conditioning\Efficiency_Share"
LEAF = r"Demand\Residential\Projections\Air Conditioning_\Large"
TARGETS = [
    ("leaf High_eff", LEAF + r"\High_eff", "Activity Level"),
    ("leaf Mid_eff", LEAF + r"\Mid_eff", "Activity Level"),
    ("leaf Low_eff", LEAF + r"\Low_eff", "Activity Level"),
    ("key Large_High", KEY + r"\Large_High", "Activity Level"),
    ("key Large_Mid", KEY + r"\Large_Mid", "Activity Level"),
    ("key Large_Low", KEY + r"\Large_Low", "Activity Level"),
]


def p(*a):
    print(*a, flush=True)


def interp_at(expr, year):
    """Value of an Interp(...) at `year` (linear). Non-Interp -> float or None."""
    if expr is None:
        return None
    s = str(expr).strip()
    m = re.match(r"\s*Interp\((.*)\)\s*$", s, flags=re.IGNORECASE)
    if not m:
        try:
            return float(s)
        except Exception:
            return None
    toks = [t.strip() for t in m.group(1).split(",")]
    nums = []
    for t in toks:
        try:
            nums.append(float(t))
        except Exception:
            nums.append(None)  # FirstScenarioYear etc.
    pts = [(y, v) for y, v in zip(nums[0::2], nums[1::2]) if y is not None and v is not None]
    if not pts:
        return None
    pts.sort()
    if year <= pts[0][0]:
        return pts[0][1]
    if year >= pts[-1][0]:
        return pts[-1][1]
    for (y0, v0), (y1, v1) in zip(pts, pts[1:]):
        if y0 <= year <= y1:
            return v0 + (year - y0) / (y1 - y0) * (v1 - v0)
    return None


def read_expr(leap, fullname, varname):
    try:
        branch = leap.Branches(fullname)
    except Exception as e:  # noqa: BLE001
        return None, f"lookup-error:{e}"
    if branch is None:
        return None, "branch-not-found"
    try:
        vc = branch.Variables.Count
    except Exception as e:  # noqa: BLE001
        return None, f"varcount-error:{e}"
    for j in range(1, vc + 1):
        try:
            v = branch.Variables.Item(j)
            if v.Name == varname:
                return safe_expression(v), "ok"  # first occurrence = input variant (§11.2)
        except Exception:  # noqa: BLE001
            continue
    return None, "variable-not-found"


def main() -> int:
    hb = HeartbeatLogger("probe_ac_effshare", progress_dir=Path(__file__).parent)
    leap = dispatch_leap()

    area = leap.ActiveArea.Name
    p(f"[probe] ActiveArea = {area!r} (expect {EXPECT_AREA!r})")
    if area != EXPECT_AREA:
        p("  ERROR: area mismatch — aborting, no reads performed.")
        hb.finish({"aborted": "area-mismatch", "area": area})
        return 3

    orig_scen = leap.ActiveScenario.Name
    p(f"[probe] original ActiveScenario = {orig_scen!r}")

    results = {}
    try:
        for scen in SCENARIOS:
            try:
                leap.ActiveScenario = leap.Scenarios(scen)
            except Exception as e:  # noqa: BLE001
                p(f"[probe] cannot set scenario {scen!r}: {e}")
                continue
            a2 = leap.ActiveArea.Name
            if a2 != EXPECT_AREA:  # §11.1 multi-area hop guard
                p(f"  ERROR: area hopped to {a2!r} after setting {scen!r} — aborting.")
                hb.finish({"aborted": "area-hop", "area": a2})
                return 3
            got = leap.ActiveScenario.Name
            leap.ActiveRegion = leap.Regions(REGION)
            hb.tick(scenario=got, region=REGION)
            p(f"\n=== scenario={got!r}  region={REGION} ===")
            for label, fn, var in TARGETS:
                expr, status = read_expr(leap, fn, var)
                v = interp_at(expr, 2025)
                short = expr if (expr is None or len(str(expr)) <= 74) else str(expr)[:71] + "..."
                p(f"  {label:15s} [{status:16s}] @2025={v}  expr={short!r}")
                results[(got, label)] = (status, expr, v)
            ks = [results[(got, l)][2] for l in ("key Large_High", "key Large_Mid", "key Large_Low")]
            if all(x is not None for x in ks):
                p(f"  --> KEY shares @2025 sum = {sum(ks):.6f}   (LEAP needs 100)")
            else:
                p(f"  --> KEY shares @2025 sum = INCOMPLETE {ks}")
    finally:
        try:
            leap.ActiveScenario = leap.Scenarios(orig_scen)
            p(f"\n[probe] restored ActiveScenario -> {leap.ActiveScenario.Name!r}")
        except Exception as e:  # noqa: BLE001
            p(f"[probe] WARN: could not restore scenario {orig_scen!r}: {e}")

    hb.finish({"scenarios_read": len(SCENARIOS)})
    p("\n[probe] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
