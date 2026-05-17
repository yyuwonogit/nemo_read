"""Find where the LEAP 'Imports' techs actually live (probe A) and what
LEAP variables are exposed on the Resource branches we care about
(probe C). All in ONE invocation per §A.10. Read-only — Variable.Name
only, never .Expression or .DataUnitText (§A.4 safe).

Expected area: 'aeo9_v0.44_re_ssn_rev1'
Expected scenario: 'Regional Aspiration Scenario'
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

from nemo_read._leap_com import dispatch_leap, LeapTreeCache

EXPECTED_AREA = "aeo9_v0.44_re_ssn_rev1"
OUT_A = Path("mailbox/20260513/_probe_imports_locations.csv")
OUT_C = Path("mailbox/20260513/_probe_resource_branch_variables.csv")

# Probe C targets: the 4 we know map correctly, the 1 broken Primary, +
# the 4 broken Secondary, + 1 unauthored Secondary for comparison
PROBE_C_BRANCHES = [
    "Resources\\Primary\\Crude Oil",          # works -> S73I VC>0
    "Resources\\Primary\\Coal Bituminous",    # works
    "Resources\\Primary\\Coal Sub bituminous", # works
    "Resources\\Primary\\Coal Lignite",        # BROKEN -> S77I VC=0
    "Resources\\Primary\\Natural Gas",         # check
    "Resources\\Secondary\\Gasoline",          # BROKEN -> S59I VC=0
    "Resources\\Secondary\\Diesel",            # BROKEN -> S16I VC=0
    "Resources\\Secondary\\Kerosene",          # BROKEN -> S63I VC=0
    "Resources\\Secondary\\Residual Fuel Oil", # BROKEN -> S46I VC=0
    "Resources\\Secondary\\Naphtha",           # unauthored, control
    "Resources\\Secondary\\LNG",               # has VC>0 (S20I)
    "Resources\\Secondary\\LPG",               # check
]


def main() -> int:
    leap = dispatch_leap()
    try:
        area = leap.ActiveArea.Name
    except Exception as e:
        print(f"[FAIL] ActiveArea read: {e}", file=sys.stderr)
        return 2
    try:
        scenario = leap.ActiveScenario.Name
    except Exception as e:
        scenario = f"<err: {e}>"
    print(f"ActiveArea.Name     = {area!r}")
    print(f"ActiveScenario.Name = {scenario!r}")
    if not area:
        print("[FAIL] ActiveArea blank (§11.1 trap)", file=sys.stderr)
        return 3
    if area != EXPECTED_AREA:
        print(f"[WARN] Area is {area!r}, expected {EXPECTED_AREA!r}")
        # don't abort — user said area might have aeo9_ prefix variation

    print("\nBuilding tree cache...")
    cache = LeapTreeCache(leap)
    fullname_to_idx = cache.fullname_to_idx
    print(f"Cache built: {len(fullname_to_idx)} branches total")

    # ----- PROBE A: find every Transformation branch containing 'Imports' -----
    print("\n========== PROBE A — Imports techs in Transformation tree ==========")
    imports_hits = []
    for fullname, idx in fullname_to_idx.items():
        if not fullname.startswith("Transformation\\"):
            continue
        if "imports" not in fullname.lower():
            continue
        try:
            branch = leap.Branches.Item(idx)
            btype = branch.BranchType
        except Exception as e:
            btype = f"<err: {e}>"
        imports_hits.append({"fullname": fullname, "branch_type": btype, "idx": idx})

    imports_hits.sort(key=lambda r: r["fullname"])
    OUT_A.parent.mkdir(parents=True, exist_ok=True)
    with OUT_A.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fullname", "branch_type", "idx"])
        w.writeheader()
        for r in imports_hits:
            w.writerow(r)
    print(f"Found {len(imports_hits)} branches under Transformation\\ "
          f"containing 'Imports' (case-insensitive)")
    print(f"Saved -> {OUT_A}")
    # Show grouped by parent
    seen_parents = set()
    for hit in imports_hits:
        parts = hit["fullname"].split("\\")
        # Print first 3 levels
        if len(parts) >= 2:
            parent_path = "\\".join(parts[:3])
            if parent_path not in seen_parents:
                seen_parents.add(parent_path)
                # find all kids of this parent
                kids = [h for h in imports_hits
                        if h["fullname"].startswith(parent_path + "\\")
                        and h["fullname"].count("\\") == parent_path.count("\\") + 1]
                print(f"\n  {parent_path}  ({len(kids)} direct kids w/ 'Imports' in path)")
                for k in kids[:8]:
                    short = k["fullname"][len(parent_path) + 1:]
                    print(f"      -> {short}  BT={k['branch_type']}")
                if len(kids) > 8:
                    print(f"      ... +{len(kids) - 8} more")

    # Also list all unique top-level 'Transformation\X' parents that contain Imports somewhere
    print("\nUnique Transformation paths (first 3 levels) holding 'Imports' branches:")
    for parent in sorted(seen_parents):
        n_total = sum(1 for h in imports_hits if h["fullname"].startswith(parent))
        print(f"  {parent}  ({n_total} hits total in subtree)")

    # ----- PROBE C: enumerate variables on key Resource branches -----
    print("\n\n========== PROBE C — Variables exposed on Resource branches ==========")
    print("(Variable.Name only — safe per §A.4)")
    rows_c = []
    for path in PROBE_C_BRANCHES:
        idx = fullname_to_idx.get(path)
        if idx is None:
            print(f"\n  {path}: NOT FOUND in cache")
            rows_c.append({"branch": path, "var_name": "<branch not found>",
                           "var_index": -1, "var_value": ""})
            continue
        try:
            branch = leap.Branches.Item(idx)
            btype = branch.BranchType
            vcount = branch.Variables.Count
        except Exception as e:
            print(f"\n  {path}: error reading Variables — {e}")
            continue
        print(f"\n  {path}  (BT={btype}, {vcount} variables)")
        # Iterate by positional index (§11.2 safe)
        for vi in range(1, vcount + 1):
            try:
                var = branch.Variables.Item(vi)
                vname = var.Name
            except Exception as e:
                vname = f"<err: {e}>"
            print(f"      [{vi:2d}] {vname}")
            rows_c.append({"branch": path, "var_name": vname,
                           "var_index": vi, "var_value": ""})

    with OUT_C.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["branch", "var_name", "var_index", "var_value"])
        w.writeheader()
        for r in rows_c:
            w.writerow(r)
    print(f"\nSaved -> {OUT_C}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
