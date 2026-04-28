"""
Inject mailbox/canonical_leap_inputs.csv into LEAP via COM.

Reads the canonical CSV produced by build_canonical.py and pushes each row
to LEAP by setting the Variable's Expression on the resolved branch under
the right ActiveRegion. Uses nemo_read's defensive helpers (LeapTreeCache
+ safe lookups).

Usage (from repo root, with LEAP open and the target area loaded):

    # Always do --dry-run first to see what would change.
    python mailbox/inject_to_leap.py --dry-run

    # When you're satisfied, drop --dry-run to actually push.
    python mailbox/inject_to_leap.py

Optional filters / flags:
    --scenario "Regional Aspiration Scenario"   # set ActiveScenario first
    --filter-ams Indonesia,Malaysia              # only those AMS
    --filter-variable "Import Cost"              # only this LEAP variable
    --filter-fuel "Crude Oil"                    # only rows tagged with this fuel
    --skip-tbd                                   # skip rows whose branch starts with TBD\\
    --csv path/to/other.csv                      # use an alternate canonical CSV

The script logs per-row outcome and prints a summary at the end. Rows with
``TBD\\`` branches are skipped by default (with a warning).
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import Counter
from pathlib import Path

# Reuse the package's defensive COM helpers
from nemo_read._leap_com import LeapTreeCache, dispatch_leap


DEFAULT_CSV = Path(__file__).parent / "canonical_leap_inputs.csv"


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="inject_to_leap")
    p.add_argument("--csv", default=str(DEFAULT_CSV),
                   help="Canonical CSV to inject (default: mailbox/canonical_leap_inputs.csv)")
    p.add_argument("--scenario", help="Set leap.ActiveScenario before pushing")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would be set; don't touch LEAP state")
    p.add_argument("--filter-ams", default="",
                   help="Comma-separated AMS names; only those rows are pushed")
    p.add_argument("--filter-variable", default="",
                   help="Only rows whose 'variable' column matches")
    p.add_argument("--filter-fuel", default="",
                   help="Only rows whose 'fuel' column matches")
    p.add_argument("--skip-tbd", action="store_true", default=True,
                   help="Skip rows whose branch starts with 'TBD\\' (default ON)")
    p.add_argument("--no-skip-tbd", dest="skip_tbd", action="store_false",
                   help="Push TBD-branch rows anyway (will likely fail lookup)")
    p.add_argument("--ignore-units", action="store_true",
                   help="Skip the unit-mismatch refusal. Use only when you've "
                        "manually verified the CSV is in LEAP-native units.")
    p.add_argument("--already-converted", action="store_true",
                   help="Mark the CSV as already converted to LEAP-native units. "
                        "Bypasses the 'use canonical_leap_native.csv' check.")
    return p.parse_args(argv)


def _check_csv_is_native(csv_path: Path, args) -> None:
    """Refuse to push the source-unit canonical when LEAP-native exists."""
    if args.ignore_units or args.already_converted:
        return
    name = csv_path.name
    native = csv_path.parent / "canonical_leap_native.csv"
    if name == "canonical_leap_native.csv":
        return
    if name == "canonical_leap_inputs.csv" and native.exists():
        raise SystemExit(
            f"REFUSED: {name} is in source units. The fixed workflow expects "
            f"you to push canonical_leap_native.csv (produced by "
            f"mailbox/run_workflow.py step 4). Pass --csv {native} or, if you "
            f"really mean to push source units, --ignore-units."
        )


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def filter_rows(rows: list[dict], args) -> list[dict]:
    out = []
    ams_filter = {a.strip() for a in args.filter_ams.split(",") if a.strip()}
    var_filter = args.filter_variable.strip()
    fuel_filter = args.filter_fuel.strip()
    for r in rows:
        if ams_filter and r["ams"] not in ams_filter:
            continue
        if var_filter and r["variable"] != var_filter:
            continue
        if fuel_filter and r["fuel"] != fuel_filter:
            continue
        if args.skip_tbd and r["branch"].startswith("TBD\\"):
            continue
        out.append(r)
    return out


def main(argv=None) -> int:
    args = parse_args(argv)
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 1

    _check_csv_is_native(csv_path, args)

    rows = load_rows(csv_path)
    rows = filter_rows(rows, args)
    if not rows:
        print("No rows match filters; nothing to do.")
        return 0

    print(f"[inject] {len(rows)} rows queued from {csv_path.name}")
    if args.dry_run:
        print("[inject] DRY RUN — LEAP state will not be modified")

    leap = dispatch_leap()
    print(f"[inject] Active area:     {leap.ActiveArea.Name!r}")
    print(f"[inject] Active scenario: {leap.ActiveScenario.Name!r}")

    if args.scenario and leap.ActiveScenario.Name != args.scenario:
        if not args.dry_run:
            try:
                leap.ActiveScenario = args.scenario
                print(f"[inject] switched ActiveScenario -> "
                      f"{leap.ActiveScenario.Name!r}")
            except Exception as exc:
                print(f"ERROR: could not switch scenario to {args.scenario!r}: {exc}",
                      file=sys.stderr)
                return 2
        else:
            print(f"[inject] (dry-run) would switch ActiveScenario -> "
                  f"{args.scenario!r}")

    # Build branch index. Reuses any cache file the export wrote earlier.
    cache_file = (Path(leap.ActiveArea.Directory)
                  / "NEMO_25.leap_export" / ".tree_cache.json")
    cache = LeapTreeCache(leap=leap,
                          cache_file=cache_file if cache_file.exists() else None)
    print(f"[inject] building branch maps ...")
    t0 = time.perf_counter()
    fullname_to_idx = cache.fullname_to_idx
    print(f"[inject]   {len(fullname_to_idx)} branches indexed "
          f"({time.perf_counter()-t0:.1f}s)")

    # Group rows by AMS so we set ActiveRegion once per cohort.
    rows_by_ams: dict[str, list[dict]] = {}
    for r in rows:
        rows_by_ams.setdefault(r["ams"], []).append(r)

    counts = Counter()
    failures: list[tuple[dict, str]] = []
    for ams, ams_rows in sorted(rows_by_ams.items()):
        # Set ActiveRegion (skip in dry-run)
        if not args.dry_run:
            try:
                leap.ActiveRegion = ams
            except Exception as exc:
                print(f"  [region={ams!r}] ERROR: cannot set ActiveRegion: {exc}")
                for r in ams_rows:
                    failures.append((r, f"ActiveRegion set failed: {exc}"))
                    counts["failed"] += 1
                continue
        print(f"  [region={ams!r}] {len(ams_rows)} rows")

        for r in ams_rows:
            branch_path = r["branch"]
            var_name = r["variable"]
            expr = r["expression"]
            idx = fullname_to_idx.get(branch_path)
            if idx is None:
                failures.append((r, f"branch not found: {branch_path}"))
                counts["branch_not_found"] += 1
                print(f"     [SKIP] {branch_path} -> branch not in tree")
                continue
            try:
                branch = cache.branches.Item(idx)
                var = branch.Variable(var_name)
            except Exception as exc:
                failures.append((r, f"variable lookup failed: {exc}"))
                counts["var_not_found"] += 1
                print(f"     [SKIP] {branch_path} -> Variable({var_name!r}) "
                      f"failed: {exc}")
                continue
            if var is None:
                failures.append((r, f"Variable({var_name!r}) returned None"))
                counts["var_not_found"] += 1
                print(f"     [SKIP] {branch_path} -> Variable({var_name!r}) "
                      f"= None (variable doesn't exist on this branch)")
                continue

            if args.dry_run:
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
                failures.append((r, f"Expression set failed: {exc}"))
                counts["set_failed"] += 1
                print(f"     [ERR] {branch_path} . {var_name!r}: {exc}")

    print()
    print(f"[inject] Summary: {dict(counts)}")
    if failures:
        print(f"[inject] {len(failures)} failures (showing first 10):")
        for r, msg in failures[:10]:
            print(f"  {r['ams']:<12} {r['branch']:<55} {r['variable']:<25} -> {msg}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
