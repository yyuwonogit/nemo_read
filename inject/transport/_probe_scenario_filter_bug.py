"""Probe: confirm/refute the scenario-column filter hypothesis.

Hypothesis: `CanonicalInjector._run_scenario_cycle` does NOT filter the
`rows` list by the row's `scenario` column. The transport canonical has
4 rows per branch+ams (one per scenario tag). For each of the 4 scenario
iterations in the inject's --scenarios loop, ALL 4 scenario-tagged rows
get pushed -> each branch is written 4 times per scenario, last writer
wins -> the value sitting in LEAP after the inject is whichever
scenario's row appeared LAST in CSV row order, regardless of which
ActiveScenario the inject loop thought it was writing to.

This probe reads ONE branch under all 4 scenarios and compares against
the canonical's 4 distinct expressions for that branch. If the
hypothesis is right, all 4 scenarios will show the SAME expression
(the last-in-CSV one). If the hypothesis is wrong, each scenario
shows its own canonical-tagged expression.

Target row: Brunei | Key\\TransportDataStock\\Vehicles_Sales_Share\\Bus\\Blended Diesel | Activity Level
Canonical CSV row order for this branch (from lines 6-9):
  L6: AMS Target Scenario           Interp(2025, 88.5246, ..., 2060, 70)
  L7: Baseline Simulation           Interp(2025, 88.5246, ..., 2060, 70)   [same as L6]
  L8: Current Accounts              Interp(2006, 100, ..., 2024, 88.5246)
  L9: Regional Aspiration Scenario  Interp(2025, 88.5246, ..., 2060, 52)   [LAST in CSV order]

Hypothesis prediction: all 4 ActiveScenarios show the L9 (RAS) expression
because it's the last row in CSV iteration order for this branch.

Falsification: each scenario shows its own L6/L7/L8/L9 expression.

Read-only probe -- no writes. Safe to run any time the area is open.
Per A.10: ONE Python invocation; cache built once; 4 scenarios x 1 read
each in the same COM session.
"""
from __future__ import annotations

import sys

from nemo_read._leap_com import dispatch_leap, LeapTreeCache, safe_expression


EXPECT_AREA = "aeo9_v0.47"
REGION = "Brunei"
BRANCH = "Key\\TransportDataStock\\Vehicles_Sales_Share\\Bus\\Blended Diesel"
VARIABLE = "Activity Level"
SCENARIOS = [
    "Baseline Simulation",
    "AMS Target Scenario",
    "Regional Aspiration Scenario",
    "Current Accounts",
]


def _short(expr: str, n: int = 90) -> str:
    return expr if len(expr) <= n else expr[:n - 3] + "..."


def main() -> int:
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    leap = dispatch_leap()
    area = leap.ActiveArea.Name
    print(f"[probe] ActiveArea (locked): {area!r}")
    if area != EXPECT_AREA:
        print(f"[probe] ABORT: expected {EXPECT_AREA!r}, got {area!r}")
        return 3

    try:
        leap.ActiveRegion = leap.Regions(REGION)
    except Exception as exc:
        print(f"[probe] ABORT: could not set ActiveRegion={REGION!r}: {exc}")
        return 4
    print(f"[probe] ActiveRegion: {leap.ActiveRegion.Name!r}")

    cache = LeapTreeCache(leap=leap)
    idx = cache.fullname_to_idx.get(BRANCH)
    if idx is None:
        print(f"[probe] ABORT: branch not in cache: {BRANCH}")
        return 5
    branch = cache.branches.Item(idx)
    var = branch.Variable(VARIABLE)
    if var is None:
        print(f"[probe] ABORT: variable not found: {VARIABLE!r}")
        return 6

    results: dict[str, str] = {}
    for scenario in SCENARIOS:
        try:
            leap.ActiveScenario = leap.Scenarios(scenario)
        except Exception as exc:
            print(f"[probe] ABORT: could not set ActiveScenario={scenario!r}: {exc}")
            return 7
        if leap.ActiveArea.Name != EXPECT_AREA:
            print(f"[probe] ABORT: area drifted after scenario set to {leap.ActiveArea.Name!r}")
            return 8
        actual_scen = leap.ActiveScenario.Name
        try:
            expr = safe_expression(var)
        except Exception as exc:
            expr = f"<read error: {exc}>"
        results[scenario] = expr
        print(f"\n[probe] scenario={actual_scen!r}")
        print(f"        expression: {_short(expr)}")

    print("\n" + "=" * 72)
    print("VERDICT")
    print("=" * 72)
    unique = set(results.values())
    if len(unique) == 1:
        print("ALL 4 scenarios returned the SAME expression.")
        print("-> Hypothesis CONFIRMED: scenario-column filter is missing.")
        print("   Last-write-wins; whichever CSV row order put it there.")
    else:
        print(f"{len(unique)} distinct expressions across 4 scenarios.")
        print("-> Hypothesis REFUTED or partial: scenario filtering may be")
        print("   working (or partially working).")
        print("\nPer-scenario expression (first 90 chars):")
        for s, e in results.items():
            print(f"  {s!r:<35} -> {_short(e)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
