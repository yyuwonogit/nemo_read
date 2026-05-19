"""Diagnostic: do KA-branch writes via Variable.Expression actually take?

Test plan (single COM session, popup-safe — only reads .Expression
on Activity Level which is input-side per our earlier probe):

1. Confirm area = aeo9_v0.46
2. Pick target: Brunei, Key\\TransportDataStock\\Vehicle_Sales\\Bus,
   variable 'Activity Level', scenario 'Baseline Simulation'
3. Read current expression (baseline)
4. Write 'Interp(2025, 99999)' via safe_set_expression
5. Read back immediately
6. Compare — does the write match? If readback == 99999, writes
   take. If readback unchanged from baseline, writes are silently
   rejected on KA branches.
7. ALSO test on a working branch (Demand\\Transport\\Road\\Bus\\
   Gasoline\\Gasoline 'Mileage') for sanity baseline.

Hands user the data to make a structural call before we burn another
2 hours.
"""
from __future__ import annotations

from nemo_read._leap_com import (
    dispatch_leap, LeapTreeCache, safe_set_expression,
)


TESTS = [
    {
        "label": "KA branch (Activity Level on Key\\TransportDataStock)",
        "branch_path": "Key\\TransportDataStock\\Vehicle_Sales\\Bus",
        "variable": "Activity Level",
        "test_value": "Interp(2025, 99999)",
    },
    {
        "label": "Demand-side baseline (Mileage on Demand\\Transport\\Road)",
        "branch_path": "Demand\\Transport\\Road\\Bus\\Gasoline\\Gasoline",
        "variable": "Mileage",
        "test_value": "Interp(2025, 88888)",
    },
]
REGION = "Brunei"
SCENARIO = "Baseline Simulation"


def _safe_read_expression(var) -> str:
    """Read Variable.Expression; catch COM errors that fire on result-side."""
    try:
        raw = var.Expression
        return "" if raw is None else str(raw)
    except Exception as exc:
        return f"<read err: {exc}>"


def main() -> int:
    leap = dispatch_leap()
    area = leap.ActiveArea.Name
    print(f"[probe] ActiveArea: {area!r}")
    if area != "aeo9_v0.46":
        print(f"[probe] ABORT: expected 'aeo9_v0.46'")
        return 3

    try:
        leap.ActiveScenario = leap.Scenarios(SCENARIO)
    except Exception as exc:
        print(f"[probe] ABORT: could not set ActiveScenario={SCENARIO!r}: {exc}")
        return 4
    try:
        leap.ActiveRegion = leap.Regions(REGION)
    except Exception as exc:
        print(f"[probe] ABORT: could not set ActiveRegion={REGION!r}: {exc}")
        return 4
    print(f"[probe] ActiveScenario: {leap.ActiveScenario.Name!r}")
    print(f"[probe] ActiveRegion:   {leap.ActiveRegion.Name!r}")

    cache = LeapTreeCache(leap=leap)
    print(f"[probe] cache: {len(cache.fullname_to_idx)} branches\n")

    for t in TESTS:
        print("=" * 70)
        print(f"TEST: {t['label']}")
        print(f"  branch:   {t['branch_path']}")
        print(f"  variable: {t['variable']!r}")
        print(f"  scenario: {SCENARIO!r} / region: {REGION!r}")

        idx = cache.fullname_to_idx.get(t["branch_path"])
        if idx is None:
            print(f"  ABORT: branch not in cache")
            continue
        br = cache.branches.Item(idx)
        try:
            bt = int(br.BranchType)
        except Exception as exc:
            bt = f"?({exc})"
        print(f"  BranchType: {bt}")

        var = br.Variable(t["variable"])
        if var is None:
            print(f"  ABORT: variable not found on branch")
            continue
        try:
            vid = int(var.ID)
        except Exception:
            vid = -1
        print(f"  Variable.ID: {vid}")

        before = _safe_read_expression(var)
        print(f"\n  BEFORE write (current expression):")
        print(f"    {before if len(before) <= 250 else before[:247] + '...'}")

        print(f"\n  WRITING: {t['test_value']!r}")
        try:
            committed = safe_set_expression(var, t["test_value"])
            print(f"  safe_set_expression returned: {committed!r}")
        except Exception as exc:
            print(f"  WRITE FAILED with exception: {exc}")
            continue

        after = _safe_read_expression(var)
        print(f"\n  AFTER write (readback expression):")
        print(f"    {after if len(after) <= 250 else after[:247] + '...'}")

        match_test = t["test_value"] == after
        match_normalised = t["test_value"].replace(", ", ",") == after.replace(", ", ",")
        if match_test or match_normalised:
            print(f"\n  RESULT: WRITE TOOK (readback matches test value)")
        elif after == before:
            print(f"\n  RESULT: WRITE SILENTLY REJECTED "
                  f"(readback == before, unchanged)")
        else:
            print(f"\n  RESULT: WRITE TRANSFORMED "
                  f"(readback != before AND != test value)")
        print()

    print("=" * 70)
    print("[probe] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
