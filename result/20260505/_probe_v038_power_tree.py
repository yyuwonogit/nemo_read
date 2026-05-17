"""Probe v0.38 LEAP area to enumerate power-tree children and diff
against expected branches from inject_round1p5_{CA,ATS,BAS}.csv.

Pure read; no scenario flip; safe to run while LEAP is open on
aeo9_v0.38. Writes:
  _v038_power_tree_actual.txt    — every branch under the two power parents
  _v038_power_tree_diff.csv      — expected vs found + suggested match
"""
from __future__ import annotations

import csv
import difflib
from pathlib import Path

from nemo_read._leap_com import LeapTreeCache, dispatch_leap

HERE = Path(__file__).parent
CSVS = [
    HERE / "inject_round1p5_CA.csv",
    HERE / "inject_round1p5_ATS.csv",
    HERE / "inject_round1p5_BAS.csv",
]
PARENTS = [
    r"Transformation\Centralized Electricity Generation\Processes",
    r"Transformation\Distributed Electricity Generation\Processes",
]
OUT_TREE = HERE / "_v038_power_tree_actual.txt"
OUT_DIFF = HERE / "_v038_power_tree_diff.csv"


def expected_branches() -> set[str]:
    expected: set[str] = set()
    for c in CSVS:
        with c.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                expected.add(row["branch"])
    return expected


def main() -> int:
    leap = dispatch_leap()
    print(f"[probe] ActiveArea: {leap.ActiveArea.Name!r}")
    if leap.ActiveArea.Name != "aeo9_v0.38":
        print(f"  WARNING: expected aeo9_v0.38, got {leap.ActiveArea.Name!r}")

    print(f"[probe] building branch index ...")
    cache = LeapTreeCache(leap=leap)
    all_paths = set(cache.fullname_to_idx)
    print(f"[probe] indexed {len(all_paths)} branches "
          f"(under ActiveRegion={leap.ActiveRegion.Name!r})")

    # All descendants under each parent
    actual: dict[str, list[str]] = {}
    for parent in PARENTS:
        prefix = parent + "\\"
        kids = sorted(p for p in all_paths if p.startswith(prefix))
        actual[parent] = kids
        print(f"\n[{parent}]  {len(kids)} descendant branches")
        for k in kids[:40]:
            print(f"  {k.removeprefix(prefix)}")
        if len(kids) > 40:
            print(f"  ... +{len(kids) - 40} more")

    with OUT_TREE.open("w", encoding="utf-8") as f:
        for parent, kids in actual.items():
            f.write(f"== {parent} ==\n")
            for k in kids:
                f.write(f"{k}\n")
            f.write("\n")
    print(f"\n[probe] full tree saved -> {OUT_TREE}")

    # Diff: which CSV-expected branches are missing from v0.38, and best guess
    expected = expected_branches()
    pool = {p for p in all_paths
            if any(p.startswith(par + "\\") for par in PARENTS)}
    rows = []
    for exp in sorted(expected):
        found = exp in all_paths
        suggestion = ""
        if not found:
            # Match on the leaf (last segment); look for same-leaf in pool
            leaf = exp.rsplit("\\", 1)[-1]
            same_leaf = [p for p in pool if p.endswith("\\" + leaf)]
            if same_leaf:
                suggestion = same_leaf[0]
            else:
                # Fallback: closest leaf match within pool
                pool_leaves = {p.rsplit("\\", 1)[-1]: p for p in pool}
                close = difflib.get_close_matches(leaf, list(pool_leaves), n=1)
                if close:
                    suggestion = pool_leaves[close[0]] + f"  (leaf-match: {close[0]!r})"
        rows.append({
            "expected_branch": exp,
            "found_in_v038": "Y" if found else "N",
            "suggestion": suggestion,
        })

    with OUT_DIFF.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["expected_branch", "found_in_v038", "suggestion"])
        w.writeheader()
        w.writerows(rows)

    n_found = sum(1 for r in rows if r["found_in_v038"] == "Y")
    n_missing = len(rows) - n_found
    n_with_suggestion = sum(1 for r in rows if r["found_in_v038"] == "N" and r["suggestion"])
    print(f"\n[probe] diff: {len(rows)} expected, "
          f"{n_found} found, {n_missing} missing "
          f"({n_with_suggestion} with suggestion)")
    print(f"[probe] diff saved -> {OUT_DIFF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
