r"""One-shot AC structure probe (read-only) for aeo9_v0.64.

Confirms whether AC mirrors the fridge structure BEFORE we build/inject:
  - Demand AC parent name (`Air Conditioning` vs `Air Conditioning_` vs `Cooling`)
  - the 2-layer Size x Efficiency subtree
  - a Key tree under Key\Residential (Percent Ownership/Size_Share/
    Efficiency_Share/Useful_EI equivalents)
  - the AC device leaf variable set (names only) UNDER RAS (device-stock vars
    are RAS-scoped)

Safe: reads FullName + Variable.Name only — never .Expression/.DataUnitText
(result-var modal trap). Area-locked; aborts on drift/blank. ONE COM session.
"""
import win32com.client

EXPECT = "aeo9_v0.64"
leap = win32com.client.Dispatch("LEAP.LEAPApplication")
area = leap.ActiveArea.Name
print("ActiveArea:", repr(area), "| ActiveScenario:", repr(leap.ActiveScenario.Name))
if area != EXPECT:
    raise SystemExit(f"ABORT: area is {area!r}, expected {EXPECT!r} — re-focus LEAP and rerun.")

try:
    leap.ActiveScenario = leap.Scenarios("Regional Aspiration Scenario")
    print("set scenario -> 'Regional Aspiration Scenario'")
except Exception as e:
    print("WARN could not set RAS:", e)
if leap.ActiveArea.Name != EXPECT:
    raise SystemExit(f"ABORT: area drifted to {leap.ActiveArea.Name!r} after scenario set.")

branches = leap.Branches
n = branches.Count
print(f"Branches.Count = {n}  (collecting FullNames, ~1-3 min)...")
names = []
for i in range(1, n + 1):
    try:
        names.append(branches.Item(i).FullName)
    except Exception:
        pass
print(f"collected {len(names)} fullnames\n")

def hits(prefix, kw=("Air", "Cool", "Conditioning")):
    return sorted(fn for fn in names if fn.startswith(prefix)
                  and any(k in fn[len(prefix):] for k in kw))

# 1. Demand AC subtree
dp = "Demand\\Residential\\Projections\\"
ac_dem = hits(dp)
print("=== Demand AC branches ===")
for fn in ac_dem[:80]:
    print("  ", fn)
if not ac_dem:
    print("  (NONE — Projections children:)")
    kids = sorted({dp + fn[len(dp):].split("\\")[0] for fn in names if fn.startswith(dp)})
    for k in kids:
        print("   ", k)

# 2. Key AC subtree
kr = "Key\\Residential\\"
ac_key = hits(kr)
print("\n=== Key AC branches ===")
for fn in ac_key[:80]:
    print("  ", fn)
if not ac_key:
    print("  (NONE — Key\\Residential children:)")
    kids = sorted({kr + fn[len(kr):].split("\\")[0] for fn in names if fn.startswith(kr)})
    for k in kids:
        print("   ", k)

# 3. AC leaf variable names (under RAS)
leaf = next((fn for fn in ac_dem if fn.endswith("Large\\High_eff")), None)
if leaf:
    print(f"\n=== AC leaf variables (names only): {leaf} ===")
    b = leap.Branches(leaf)
    for j in range(1, b.Variables.Count + 1):
        try:
            print(f"  {j:2d}: {b.Variables.Item(j).Name!r}")
        except Exception as e:
            print(f"  {j:2d}: ERR {e}")
else:
    print("\n=== no '<AC>\\Large\\High_eff' leaf found ===")

# 4. AC parent variable names (ownership level)
parent = None
for fn in ac_dem:
    rest = fn[len(dp):]
    if "\\" not in rest:   # direct child of Projections = the AC parent
        parent = fn
        break
if parent:
    print(f"\n=== AC parent variables (names only): {parent} ===")
    b = leap.Branches(parent)
    for j in range(1, b.Variables.Count + 1):
        try:
            print(f"  {j:2d}: {b.Variables.Item(j).Name!r}")
        except Exception as e:
            print(f"  {j:2d}: ERR {e}")
print("\n=== probe done ===")
