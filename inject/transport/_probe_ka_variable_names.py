"""Probe: enumerate Variable.Name on representative Key\\TransportDataStock leaves.

POPUP-SAFE — only reads `.Name` and `.BranchType` (no `.Expression`,
no `.DataUnitText`).

Background: build_canonical.py writes variable="Key Assumptions" on
all Key\\TransportDataStock\\... branches per user direction. Inject
dry-run reports 441 var_not_found — meaning the variable name we're
writing isn't what LEAP exposes via COM. Need to probe one branch to
see the actual COM Variable.Name list.

Confirms area lock to aeo9_v0.46 before reading anything (§A.9).
"""
from __future__ import annotations

from nemo_read._leap_com import dispatch_leap, LeapTreeCache


TARGETS = [
    "Key\\TransportDataStock\\Vehicle_Sales\\Bus",
    "Key\\TransportDataStock\\BaseYear_StockData\\Bus",
    "Key\\TransportDataStock\\Vehicles_Sales_Share\\Bus\\Gasoline",
]


def main() -> int:
    leap = dispatch_leap()
    area = leap.ActiveArea.Name
    print(f"[probe] ActiveArea: {area!r}")
    if area != "aeo9_v0.46":
        print(f"[probe] ABORT: expected 'aeo9_v0.46'")
        return 3

    cache = LeapTreeCache(leap=leap)
    print(f"[probe] cache: {len(cache.fullname_to_idx)} branches")

    for target in TARGETS:
        idx = cache.fullname_to_idx.get(target)
        if idx is None:
            print(f"\n[probe] {target}  -- NOT in cache")
            continue
        br = cache.branches.Item(idx)
        try:
            bt = int(br.BranchType)
        except Exception as exc:
            bt = f"?({exc})"
        try:
            n_vars = br.Variables.Count
        except Exception as exc:
            print(f"\n[probe] {target}  -- BranchType={bt}, Variables.Count err: {exc}")
            continue

        print(f"\n[probe] {target}")
        print(f"        BranchType={bt}, Variables.Count={n_vars}")
        for j in range(1, n_vars + 1):
            try:
                v = br.Variables.Item(j)
                nm = v.Name
            except Exception as exc:
                nm = f"<err: {exc}>"
            try:
                vid = int(v.ID)
            except Exception:
                vid = -1
            print(f"          {j:2d}. id={vid:>4} name={nm!r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
