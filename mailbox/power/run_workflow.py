"""Power inject driver — 3-cache region-grouped variant.

Splits a canonical CSV (as produced by build_canonical.py) into three
region groups and pushes each group under its own freshly-rebuilt tree
cache:

    Indonesia rows      → cache built under ActiveRegion=Indonesia
    Malaysia rows       → cache built under ActiveRegion=Malaysia
    All other AMS rows  → cache built under ActiveRegion=<first non-ID/MY ams>

Why three caches: in `aeo9_v0.38_yy`, `leap.Branches.Count` enumeration
is region-filtered. Indonesia and Malaysia each have a unique tree
shape (mix of country-level + subnational); the other nine AMS share
the country-level-only shape. A cache built under one region of a
group is valid for all rows in that group; a cache built under
Indonesia (say) does NOT see Malaysia's `_MY*` branches or country-
level branches that Indonesia replaces with subnationals.

Cost vs single-cache: 3 cache builds (~9 min) instead of 1 (~3 min),
but with full branch coverage. Cost vs per-region rebuild: 9 min vs
33 min (3× fewer cache builds).

Usage:
    python mailbox/power/run_workflow.py \\
        --csv mailbox/power/20260507/ats_combined_canonical.csv \\
        --expect-area aeo9_v0.38_yy \\
        --expect-scenario "AMS Target Scenario"

Flags:
- ``--expect-area`` / ``--expect-scenario`` — abort on area or scenario
  drift. Always pass them.
- ``--dry-run`` — preview which rows would push without touching state.
- ``--fail-fast`` — exit non-zero on the first inject failure.
  Recommended for re-injects of validated CSVs.
- ``--blind`` — escape hatch (NOT SOP). Skip the tree cache entirely
  and look up each branch via direct ``leap.Branches(FullName)``. Use
  only when the cache is reporting false misses on branches verified
  to exist in the LEAP UI (lazy-loaded subtree COM doesn't enumerate).
  Pair with ``--fail-fast`` so a wrong FullName hangs only one row
  before we ctrl-C and investigate.

Adds the safety flag `--expect-scenario` (not present in
inject_to_leap.py yet) to abort if the active scenario doesn't match —
prevents the misroute trap that bit us 2026-05-07.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from nemo_read._leap_com import LeapTreeCache, dispatch_leap, safe_expression


# Region groups for cache build. Keys are group names; values are the
# regions that belong to each group. The first region in each group's
# list is used as the "cache build region" — its tree shape must
# represent the group.
GROUPS: dict[str, list[str]] = {
    "Indonesia": ["Indonesia"],
    "Malaysia": ["Malaysia"],
    "Other": [
        "Brunei", "Cambodia", "Laos", "Myanmar", "Philippines",
        "Singapore", "Thailand", "Timor Leste", "Vietnam",
    ],
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="power.run_workflow")
    p.add_argument("--csv", required=True, type=Path,
                   help="Canonical CSV produced by build_canonical.py")
    p.add_argument("--expect-area", required=True,
                   help="Abort if leap.ActiveArea.Name doesn't match this")
    p.add_argument("--expect-scenario",
                   help="Abort if leap.ActiveScenario.Name doesn't match this. "
                        "Strongly recommended to prevent scenario misroutes.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would be set; don't touch LEAP state")
    p.add_argument("--blind", action="store_true",
                   help="ESCAPE HATCH (not SOP) — use when the LEAP tree "
                        "cache is reporting false misses on branches you've "
                        "verified exist in the UI (lazy-loaded subtrees that "
                        "COM won't enumerate). Skips the tree cache entirely "
                        "and looks up each branch via direct "
                        "`leap.Branches(FullName)` calls. Risk: a missing or "
                        "misspelled FullName hangs LEAP COM indefinitely "
                        "(CLAUDE.md §11.1) — you'll need to ctrl-C kill the "
                        "script. Pair with --fail-fast to abort on the first "
                        "real LEAP error so a hang stays bounded to one row.")
    p.add_argument("--fail-fast", action="store_true",
                   help="Exit non-zero on the first inject failure instead "
                        "of logging it and continuing. Counts as a failure: "
                        "var_lookup_failed, var_not_found, set_failed, "
                        "branch_not_found. Recommended when re-injecting a "
                        "previously-validated CSV (no new failure modes "
                        "expected) and especially when paired with --blind.")
    return p.parse_args(argv)


def _group_for_region(region: str) -> str | None:
    for group_name, members in GROUPS.items():
        if region in members:
            return group_name
    return None


class FailFast(RuntimeError):
    """Raised inside _push_group when --fail-fast is set and an inject
    row failed. Caught by main() to surface a non-zero exit code without
    further row processing."""


def _push_group(leap, group_name: str, group_rows: list[dict],
                dry_run: bool, blind: bool, fail_fast: bool) -> Counter:
    """Push all rows belonging to one region group.

    With ``blind=False`` (default), builds a tree cache once for the
    group and looks up branches via positional index. With
    ``blind=True``, skips the cache entirely and directly calls
    ``leap.Branches(FullName)`` per row — faster (no 3-min cache build)
    but hangs if any FullName doesn't exist in the area.
    """
    counts: Counter = Counter()
    if not group_rows:
        return counts

    def _fail(reason: str) -> None:
        if fail_fast:
            raise FailFast(reason)

    print(f"\n=== Group {group_name!r}: {len(group_rows)} rows ===")

    fullname_to_idx: dict[str, int] | None = None
    if not blind:
        # Cache-build region = first region in the group with rows.
        cache_region = next(
            (r for r in GROUPS[group_name]
             if any(row["ams"] == r for row in group_rows)),
            GROUPS[group_name][0],
        )
        print(f"  (cache built under {cache_region!r})")
        leap.ActiveRegion = cache_region
        t0 = time.perf_counter()
        cache = LeapTreeCache(leap=leap)
        fullname_to_idx = cache.fullname_to_idx
        print(f"  cache: {len(fullname_to_idx)} branches indexed "
              f"({time.perf_counter() - t0:.1f}s)")
    else:
        print(f"  (blind mode — direct Branches(FullName) lookup)")

    rows_by_region: dict[str, list[dict]] = defaultdict(list)
    for row in group_rows:
        rows_by_region[row["ams"]].append(row)

    for region in sorted(rows_by_region):
        region_rows = rows_by_region[region]
        leap.ActiveRegion = region
        print(f"  [region={region!r}] {len(region_rows)} rows")

        for row in region_rows:
            branch_path = row["branch"]
            var_name = row["variable"]
            expr = row["expression"]

            try:
                if blind:
                    # Direct FullName lookup. Hangs if branch missing.
                    branch = leap.Branches(branch_path)
                else:
                    idx = fullname_to_idx.get(branch_path)
                    if idx is None:
                        counts["branch_not_found"] += 1
                        print(f"     [SKIP] {branch_path} -> branch not in cache")
                        _fail(f"branch_not_found: {branch_path}")
                        continue
                    branch = leap.Branches.Item(idx)
                if branch is None:
                    counts["branch_not_found"] += 1
                    print(f"     [SKIP] {branch_path} -> Branches() returned None")
                    _fail(f"branch_not_found: {branch_path}")
                    continue
                var = branch.Variable(var_name)
            except FailFast:
                raise
            except Exception as exc:
                counts["var_lookup_failed"] += 1
                print(f"     [ERR] {branch_path} . {var_name!r}: {exc}")
                _fail(f"var_lookup_failed: {branch_path} . {var_name!r}: {exc}")
                continue
            if var is None:
                counts["var_not_found"] += 1
                print(f"     [SKIP] {branch_path} . {var_name!r} = None")
                _fail(f"var_not_found: {branch_path} . {var_name!r}")
                continue

            if dry_run:
                preview = expr if len(expr) <= 70 else expr[:67] + "..."
                print(f"     [DRY] {branch_path} . {var_name!r} = {preview}")
                counts["dry_run"] += 1
                continue

            try:
                var.Expression = expr
                counts["pushed"] += 1
                preview = expr if len(expr) <= 60 else expr[:57] + "..."
                print(f"     [OK]  {branch_path} . {var_name!r} = {preview}")
            except Exception as exc:
                counts["set_failed"] += 1
                print(f"     [ERR] {branch_path} . {var_name!r}: {exc}")
                _fail(f"set_failed: {branch_path} . {var_name!r}: {exc}")
    return counts


def main(argv=None) -> int:
    args = parse_args(argv)

    if not args.csv.exists():
        print(f"[ERROR] CSV not found: {args.csv}")
        return 2

    leap = dispatch_leap()
    area_name = leap.ActiveArea.Name
    if area_name != args.expect_area:
        print(f"[ERROR] Active area is {area_name!r}, expected "
              f"{args.expect_area!r}. Aborting.")
        return 3

    scen_name = leap.ActiveScenario.Name
    print(f"[run] Active area:     {area_name!r}")
    print(f"[run] Active scenario: {scen_name!r}")
    if args.expect_scenario and scen_name != args.expect_scenario:
        print(f"[ERROR] Active scenario is {scen_name!r}, expected "
              f"{args.expect_scenario!r}. Aborting.")
        return 4

    with args.csv.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    print(f"[run] {len(rows)} rows queued from {args.csv.name}")
    if args.dry_run:
        print(f"[run] DRY RUN — LEAP state will not be modified")

    grouped: dict[str, list[dict]] = defaultdict(list)
    unknown: list[dict] = []
    for row in rows:
        g = _group_for_region(row["ams"])
        if g is None:
            unknown.append(row)
        else:
            grouped[g].append(row)
    if unknown:
        print(f"[WARN] {len(unknown)} rows have unknown ams "
              f"(not in any group): "
              f"{sorted({r['ams'] for r in unknown})[:5]}")

    total_counts: Counter = Counter()
    aborted = False
    for group_name in ["Other", "Indonesia", "Malaysia"]:
        # Other first (non-ID/MY tree shape), then ID, then MY. Ordering
        # is mostly cosmetic — caches don't share state across groups.
        try:
            group_counts = _push_group(leap, group_name,
                                       grouped.get(group_name, []),
                                       args.dry_run, args.blind,
                                       args.fail_fast)
            total_counts.update(group_counts)
        except FailFast as e:
            print(f"\n[run] FAIL-FAST aborted on first failure: {e}")
            aborted = True
            break

    print()
    print(f"[run] Summary: {dict(total_counts)}")
    if aborted:
        return 1
    if "branch_not_found" in total_counts or "set_failed" in total_counts \
            or "var_not_found" in total_counts \
            or "var_lookup_failed" in total_counts:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
