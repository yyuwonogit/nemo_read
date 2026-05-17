"""Read calculated-scenario results from a LEAP area via COM.

Use this when the .leap area has a calc done and you want the LEAP-side
result values (Outputs, Inputs, Total Capacity, etc.) without going
through the NEMO SQLite. For SQLite-side results, just use
``nemo_read.get_result(NemoDB(...), 'vtotalcapacityannual')`` instead —
no LEAP install needed.

Output: one CSV with columns
    ams, branch, branch_type, variable, year, value
written to ``mailbox/20260505/results_<scenario>_<timestamp>.csv``.

The probe is defensive against the two LEAP COM traps:
  - never touches ``Variable.Expression`` on result variables (modal popup)
  - never touches ``Variable.DataUnitText``  (same)
  - sets ``leap.ActiveRegion`` once per region, not once per call
  - per-branch deadline so one stuck branch can't hang the whole walk

Usage (LEAP must be open with the area loaded — open it manually first
because dispatching to a closed instance silently misbehaves):

    cd c:\\Users\\ThinkPad\\Desktop\\Py YY\\NEMO_read
    python mailbox/20260505/probe_leap_results.py \\
        --area "AEO9_v0.36"  \\
        --scenario "Regional Aspiration Scenario"

Common flags:
    --variables "Outputs,Inputs,Total Capacity,Final Energy Demand"
    --years 2025,2030,2040,2050
    --regions Indonesia,Thailand           (default: all regions in area)
    --branch-prefix "Transformation"        (limit walk to a subtree)
    --branch-types 3,4                      (3=Transformation Process, 4=Demand Tech)
    --max-branches 200                      (smoke-test limit)
    --include-units                         (read .Unit.Name; usually safe)
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

# Ensure prints are unbuffered so progress is visible in real time even
# when stdout is redirected to a file (the default Bash background mode
# in this harness).
os.environ.setdefault("PYTHONUNBUFFERED", "1")
sys.stdout.reconfigure(line_buffering=True)

# Reuse the package's defensive COM helpers
from nemo_read._leap_com import (
    LeapTreeCache, dispatch_leap, iterate_variables_safe, safe_value,
)
from nemo_read.leap_conventions import LEAP_BRANCH_TYPES


# Standard LEAP result variable names for Transformation Processes
# (verified against AEO9_v0.36 Centralized Electricity Generation,
# May 2026). LEAP names the result-side variables differently from
# their input-side counterparts (e.g. result-side "Energy Generation"
# vs input-side "Outputs by Output Fuel"). Pass --variables to override.
DEFAULT_RESULT_VARS = (
    "Energy Generation",            # output by fuel, energy units (PJ)
    "Power Generation",             # output by fuel, power units (MW)
    "Existing Capacity",            # total installed (residual + new)
    "Capacity Additions",           # new builds in year
    "Capacity Retirement",          # retired in year
    "Costs of Production",          # total cost
    "Curtailed Energy Production",  # spilled output
    "Pollutant Loadings",           # emissions
)

# Default branch-type filter — types where results live.
DEFAULT_BRANCH_TYPES = (
    2,    # Transformation Module
    3,    # Transformation Process
    4,    # Demand Technology
    34,   # Environmental Effect
    50,   # Transformation Branch
)


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="probe_leap_results")
    p.add_argument("--area", help="Expected ActiveArea name; aborts if mismatched")
    p.add_argument("--scenario", help="Set ActiveScenario before reading")
    p.add_argument("--variables", default=",".join(DEFAULT_RESULT_VARS),
                   help="Comma-separated LEAP variable names to read")
    p.add_argument("--years", help="Comma-separated years (default: all years in area)")
    p.add_argument("--regions", help="Comma-separated region names (default: all)")
    p.add_argument("--branch-prefix",
                   help="Only branches whose FullName starts with this string")
    p.add_argument("--branch-types", default=",".join(str(t) for t in DEFAULT_BRANCH_TYPES),
                   help="Comma-separated BranchType integers (default: result-bearing)")
    p.add_argument("--max-branches", type=int, default=0,
                   help="Smoke-test cap (0 = unlimited)")
    p.add_argument("--include-units", action="store_true",
                   help="Read Variable.Unit.Name (usually safe; skip if popups appear)")
    p.add_argument("--skip-zeros", action="store_true",
                   help="Drop rows where value == 0. Cuts CSV size 5-10x for "
                        "result-variable scans (most year×branch×region combos "
                        "are zero for any given tech).")
    p.add_argument("--per-branch-deadline", type=float, default=20.0,
                   help="Seconds before bailing on one branch's variable iteration")
    p.add_argument("--out",
                   help="Output CSV path (default: results_<scenario>_<ts>.csv)")
    p.add_argument("--no-scenario-switch", action="store_true",
                   help="Don't set ActiveScenario via COM. Use this when "
                        "LEAP has multiple areas open and switching by name "
                        "would jump to the wrong area. Set the scenario in "
                        "the LEAP UI manually first, then run with this flag.")
    p.add_argument("--no-area-lock", action="store_true",
                   help="Disable abort-if-area-changes guard (not recommended).")
    return p.parse_args(argv)


def _split_csv_arg(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def _safe_unit(variable) -> str:
    """Read .Unit.Name defensively — never .DataUnitText."""
    try:
        u = variable.Unit
        return str(u.Name) if u is not None else ""
    except Exception:
        return ""


def main(argv=None) -> int:
    args = parse_args(argv)

    leap = dispatch_leap()
    initial_area = leap.ActiveArea.Name
    print(f"[probe] ActiveArea (start): {initial_area!r}")
    if args.area and initial_area != args.area:
        print(f"ERROR: ActiveArea is {initial_area!r}, expected {args.area!r}. "
              f"Open the right area in LEAP UI first.", file=sys.stderr)
        return 2

    if args.scenario and not args.no_scenario_switch:
        try:
            leap.ActiveScenario = args.scenario
            print(f"[probe] ActiveScenario set → {leap.ActiveScenario.Name!r}")
            after_area = leap.ActiveArea.Name
            if not args.no_area_lock and after_area != initial_area:
                print(f"ERROR: setting ActiveScenario={args.scenario!r} caused "
                      f"LEAP to switch areas: was {initial_area!r}, now "
                      f"{after_area!r}. Close other open areas in LEAP UI "
                      f"(keep only the target area), set the scenario "
                      f"manually in the UI, and re-run with "
                      f"--no-scenario-switch.", file=sys.stderr)
                return 3
        except Exception as exc:
            print(f"ERROR: cannot set scenario {args.scenario!r}: {exc}",
                  file=sys.stderr)
            return 2
    elif args.no_scenario_switch:
        print(f"[probe] --no-scenario-switch: using current ActiveScenario")
    print(f"[probe] ActiveScenario: {leap.ActiveScenario.Name!r}")

    # Resolve year list
    if args.years:
        years = [int(y) for y in _split_csv_arg(args.years)]
    else:
        try:
            years = [int(leap.BaseYear) + i
                     for i in range(int(leap.EndYear) - int(leap.BaseYear) + 1)]
        except Exception:
            print(f"ERROR: cannot enumerate years; pass --years explicitly.",
                  file=sys.stderr)
            return 2
    print(f"[probe] Years:          {years[0]}..{years[-1]} ({len(years)})")

    # Resolve region list
    if args.regions:
        regions = _split_csv_arg(args.regions)
    else:
        try:
            regions = [r.Name for r in leap.Regions]
        except Exception:
            print(f"ERROR: cannot enumerate regions.", file=sys.stderr)
            return 2
    print(f"[probe] Regions:        {regions}")

    target_vars = _split_csv_arg(args.variables)
    type_filter = {int(t) for t in _split_csv_arg(args.branch_types)}
    print(f"[probe] Result vars:    {target_vars}")
    print(f"[probe] Branch types:   {sorted(type_filter)} "
          f"({[LEAP_BRANCH_TYPES.get(t,'?') for t in sorted(type_filter)]})")

    # Build branch index (reuse cache if export ran earlier)
    cache_file = Path(leap.ActiveArea.Directory) / "NEMO_25.leap_export" / ".tree_cache.json"
    cache = LeapTreeCache(leap=leap,
                          cache_file=cache_file if cache_file.exists() else None)
    print(f"[probe] Branches indexed: {len(cache.fullname_to_idx)}")

    # Filter branches
    branches_iter: list[tuple[int, str]] = []
    for fn, idx in cache.fullname_to_idx.items():
        if args.branch_prefix and not fn.startswith(args.branch_prefix):
            continue
        try:
            br = cache.branches.Item(idx)
            bt = int(br.BranchType)
        except Exception:
            continue
        if type_filter and bt not in type_filter:
            continue
        branches_iter.append((idx, fn, bt))
    if args.max_branches > 0:
        branches_iter = branches_iter[: args.max_branches]
    print(f"[probe] Branches to walk: {len(branches_iter)}")

    out_path = Path(args.out) if args.out else (
        Path(__file__).parent
        / f"results_{leap.ActiveScenario.Name.replace(' ', '_')}"
        f"_{datetime.now():%Y%m%d_%H%M%S}.csv"
    )

    # Walk: for each region (set globally), iterate branches × target vars × years
    n_rows = 0
    n_branches_with_data = 0
    fieldnames = ["ams", "branch", "branch_type", "variable", "year", "value"]
    if args.include_units:
        fieldnames.append("unit")

    started = time.perf_counter()
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for region in regions:
            try:
                leap.ActiveRegion = region
            except Exception as exc:
                print(f"  [region={region}] cannot set: {exc}; skipping")
                continue
            print(f"  [region={region}] walking {len(branches_iter)} branches...")
            r_started = time.perf_counter()
            r_rows = 0

            for idx, fn, bt in branches_iter:
                try:
                    br = cache.branches.Item(idx)
                except Exception:
                    continue

                # Enumerate variable names safely (no .Expression)
                names: list[str] = []
                try:
                    for _, name, _ in iterate_variables_safe(
                        br, deadline_seconds=args.per_branch_deadline,
                        fetch_expression=False,
                    ):
                        if name:
                            names.append(name)
                except Exception:
                    continue

                # Match against requested result variables
                hits = [n for n in names if n in target_vars]
                if not hits:
                    continue

                branch_had_data = False
                for vname in hits:
                    try:
                        var = br.Variable(vname)
                    except Exception:
                        continue
                    if var is None:
                        continue
                    unit = _safe_unit(var) if args.include_units else None

                    for y in years:
                        v = safe_value(var, y)
                        if v is None:
                            continue
                        if args.skip_zeros and v == 0:
                            continue
                        row = {
                            "ams": region,
                            "branch": fn,
                            "branch_type": LEAP_BRANCH_TYPES.get(bt, str(bt)),
                            "variable": vname,
                            "year": y,
                            "value": v,
                        }
                        if args.include_units:
                            row["unit"] = unit
                        w.writerow(row)
                        n_rows += 1
                        r_rows += 1
                        branch_had_data = True
                if branch_had_data:
                    n_branches_with_data += 1

            elapsed = time.perf_counter() - r_started
            print(f"    {region}: {r_rows} value rows in {elapsed:.1f}s")

    elapsed = time.perf_counter() - started
    print()
    print(f"[probe] DONE in {elapsed:.1f}s")
    print(f"[probe] {n_rows} value rows from {n_branches_with_data} branches "
          f"with at least one populated cell")
    print(f"[probe] CSV: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
