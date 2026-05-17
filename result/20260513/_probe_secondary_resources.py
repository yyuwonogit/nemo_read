"""Quick read-only probe of Resources\\Secondary branch tree on the
currently-active LEAP area. Lists every branch + each branch's direct
children. No Expression reads, no DataUnitText reads — pure tree
enumeration (§A.4 safe).

Output:
  - prints ActiveArea.Name + ActiveScenario.Name BEFORE doing the walk
  - prints summary tree to stdout
  - saves full list to mailbox/20260513/_probe_secondary_resources_output.csv
"""
from __future__ import annotations
import csv
import sys
from pathlib import Path

from nemo_read._leap_com import dispatch_leap, LeapTreeCache

OUT = Path("mailbox/20260513/_probe_secondary_resources_output.csv")
TARGET_PREFIX = "Resources\\Secondary"


def main() -> int:
    leap = dispatch_leap()

    # §A.9: confirm state by reading & printing area + scenario FIRST
    try:
        area = leap.ActiveArea.Name
    except Exception as e:
        print(f"[FAIL] reading ActiveArea: {e}", file=sys.stderr)
        return 2
    try:
        scenario = leap.ActiveScenario.Name
    except Exception as e:
        scenario = f"<read failed: {e}>"
    print(f"ActiveArea.Name     = {area!r}")
    print(f"ActiveScenario.Name = {scenario!r}")
    print()
    if not area:
        print("[FAIL] ActiveArea name is blank (§11.1 spontaneous-blanking trap).",
              file=sys.stderr)
        return 3

    print("Building tree cache (this can take 130-165s on first build)...")
    cache = LeapTreeCache(leap)
    fullname_to_idx = cache.fullname_to_idx
    print(f"Cache built: {len(fullname_to_idx)} branches total")

    # Filter to Resources\Secondary subtree
    matches = []
    for fullname, idx in fullname_to_idx.items():
        if fullname.startswith(TARGET_PREFIX):
            try:
                branch = leap.Branches.Item(idx)
                btype = branch.BranchType
            except Exception as e:
                btype = f"<err: {e}>"
            matches.append({"fullname": fullname, "branch_type": btype, "idx": idx})

    print(f"\nBranches under {TARGET_PREFIX!r}: {len(matches)}")

    # Save full list
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fullname", "branch_type", "idx"])
        w.writeheader()
        for m in matches:
            w.writerow(m)
    print(f"Saved full list -> {OUT}")

    # Print tree structure: direct children of Resources\Secondary, then
    # each direct child's own children
    direct = sorted(
        [m for m in matches if m["fullname"].count("\\") == 2],
        key=lambda x: x["fullname"],
    )
    print(f"\n=== Direct children of Resources\\Secondary ({len(direct)}) ===")
    for parent in direct:
        pn = parent["fullname"]
        kids = sorted(
            [m for m in matches
             if m["fullname"].startswith(pn + "\\")
             and m["fullname"].count("\\") == 3],
            key=lambda x: x["fullname"],
        )
        leaf = pn.split("\\")[-1]
        print(f"  {leaf}  (BT={parent['branch_type']}, {len(kids)} children)")
        for k in kids:
            klef = k["fullname"].split("\\")[-1]
            print(f"      -> {klef}  (BT={k['branch_type']})")

    # Specifically check: do the 8 target Imports sub-branches exist?
    TARGETS = [
        "Resources\\Secondary\\Gasoline\\Gasoline Imports",
        "Resources\\Secondary\\Diesel\\Diesel Imports",
        "Resources\\Secondary\\Kerosene\\Kerosene Imports",
        "Resources\\Secondary\\Residual Fuel Oil\\Residual Fuel Oil Imports",
        "Resources\\Secondary\\Blended Gasoline\\Blended Gasoline Imports",
        "Resources\\Secondary\\Blended Diesel\\Blended Diesel Imports",
        "Resources\\Secondary\\Refinery Gas\\Refinery Gas Imports",
        "Resources\\Secondary\\Refinery Feedstocks\\Refinery Feedstocks Imports",
        # Also check the SIBLING pattern (not nested under parent fuel branch)
        "Resources\\Secondary\\Gasoline Imports",
        "Resources\\Secondary\\Diesel Imports",
        "Resources\\Secondary\\Kerosene Imports",
        "Resources\\Secondary\\Residual Fuel Oil Imports",
        "Resources\\Secondary\\Blended Gasoline Imports",
        "Resources\\Secondary\\Blended Diesel Imports",
        "Resources\\Secondary\\Refinery Gas Imports",
        "Resources\\Secondary\\Refinery Feedstocks Imports",
    ]
    print(f"\n=== Existence check on candidate inject branches ===")
    print(f"{'EXISTS?':10s} {'BRANCH FULLNAME'}")
    print("-" * 90)
    for t in TARGETS:
        exists = t in fullname_to_idx
        flag = "YES" if exists else "MISSING"
        print(f"{flag:10s} {t}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
