r"""Targeted AC probe: enumerate the `Air Conditioning_` parent + a size node
(the two levels not covered by _probe_ac_structure.py). Direct lookup of
known-existing FullNames (no index rebuild). Names only; area-locked."""
import win32com.client

EXPECT = "aeo9_v0.64"
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
