r"""Targeted AC probe: enumerate the `Air Conditioning_` parent + a size node
(the two levels not covered by _probe_ac_structure.py). Direct lookup of
known-existing FullNames (no index rebuild). Names only; area-locked."""
import os
from pathlib import Path

import win32com.client


def _assert_leap_unlocked():
    """Refuse to attach to LEAP while the user holds the .leap_lock interlock."""
    env = os.environ.get("NEMO_READ_LEAP_LOCK", "").strip()
    if env:
        if env.lower() in {"1", "true", "yes", "on"}:
            raise SystemExit("LEAP COM BLOCKED — $NEMO_READ_LEAP_LOCK is set.")
        if Path(env).exists():
            raise SystemExit(f"LEAP COM BLOCKED — lock file {env}")
    here = Path(__file__).resolve()
    for d in (here.parent, *here.parents):
        lock = d / ".leap_lock"
        if lock.exists():
            raise SystemExit(
                f"LEAP COM BLOCKED — lock file {lock}\n"
                "The user is working in LEAP. Delete the lock only on their explicit say-so."
            )


EXPECT = "aeo9_v0.64"
_assert_leap_unlocked()
leap = win32com.client.Dispatch("LEAP.LEAPApplication")
area = leap.ActiveArea.Name
print("ActiveArea:", repr(area), "| Scenario:", repr(leap.ActiveScenario.Name))
if area != EXPECT:
    raise SystemExit(f"ABORT: area {area!r} != {EXPECT!r} — re-focus LEAP.")

for path in [
    "Demand\\Residential\\Projections\\Air Conditioning_",
    "Demand\\Residential\\Projections\\Air Conditioning_\\Large",
]:
    try:
        b = leap.Branches(path)
    except Exception as e:
        print(f"\n=== {path} ===  LOOKUP ERR: {e}")
        continue
    print(f"\n=== {path} ===")
    for j in range(1, b.Variables.Count + 1):
        try:
            print(f"  {j:2d}: {b.Variables.Item(j).Name!r}")
        except Exception as e:
            print(f"  {j:2d}: ERR {e}")
print("\n=== done ===")
