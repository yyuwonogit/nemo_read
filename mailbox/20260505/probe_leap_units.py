"""Probe B (write-side units) — companion to probe_leap_results.py.

Purpose:
    LEAP result variables (Energy Generation, Power Generation, Existing
    Capacity, etc.) DO NOT carry their own unit metadata in the COM API
    — `Variable.Unit` raises AttributeError on them. The unit they
    return at read time depends on the area's General Properties default
    OR an explicit unit string passed to ``Variable.Value(year, unit)``.

    However, the corresponding INPUT-SIDE variables on the same branches
    DO expose `Variable.Unit.Name` reliably. So this probe walks the
    same branches as probe_leap_results.py and reads the units of a
    standard set of input variables. The resulting catalog lets the
    analyst infer the unit context for the results CSV by joining on
    (branch).

    Mapping at analysis time:
      Probe B input variable     → applies to Probe A result variable
      ---------------------      → ------------------------------------
      Maximum Capacity            → Existing Capacity, Capacity Additions,
                                    Capacity Retirement
      Capital Cost                → Costs of Production (cost denominator)
      Variable OM Cost            → secondary cost reference
      Lifetime                    → (years; reference)
      Maximum Availability        → (fraction/%; reference)
      Process Efficiency          → (fraction/%; reference)

    Some Probe A variables have no direct write-side equivalent on the
    same branch (Energy Generation, Power Generation, Pollutant
    Loadings, Curtailed Energy Production). For those the LEAP area's
    General Properties default applies; document separately.

SOP placement (lite version):
    Step A   probe_leap_results.py — per scenario × per region × per year
                                     (slow, ~50 min/scenario)
    Step B   probe_leap_units.py   — once per area, scenario-agnostic,
                                     region-agnostic (~5 min)
    Step C   join Step A's CSV with Step B's CSV on `branch` to attach
             unit context.

    The full read+write plan (nemo_read-leap-export, see BROCHURE.md)
    captures everything in one shot. This A+B pair is the lite,
    targeted version for when only the results question is asked.

Default input variables (verified against AEO9_v0.36 Centralized
Electricity Generation, May 2026):
    Maximum Capacity, Capital Cost, Variable OM Cost, Fixed OM Cost,
    Lifetime, Maximum Availability, Minimum Utilization,
    Process Efficiency, Exogenous Capacity, Capacity Credit

Usage:
    python mailbox/20260505/probe_leap_units.py \\
        --branch-prefix "Transformation\\Centralized Electricity Generation" \\
        --out mailbox/20260505/units_centralized.csv

Output CSV columns:
    branch, branch_type, variable, unit
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONUNBUFFERED", "1")
sys.stdout.reconfigure(line_buffering=True)

from nemo_read._leap_com import (
    LeapTreeCache, dispatch_leap, iterate_variables_safe,
)
from nemo_read.leap_conventions import LEAP_BRANCH_TYPES
from nemo_read.leap_units import safe_data_unit_text, safe_data_unit_id


# Default INPUT (write-side) variables to capture units for. These are
# the variables on Transformation Process branches whose units inform
# how to read the result-side outputs.
DEFAULT_INPUT_VARS = (
    "Maximum Capacity",         # → cap units for Existing/Additions/Retirement
    "Minimum Capacity",
    "Capital Cost",             # → cost units for Costs of Production
    "Variable OM Cost",
    "Fixed OM Cost",
    "Lifetime",
    "Maximum Availability",
    "Minimum Utilization",
    "Process Efficiency",
    "Exogenous Capacity",
    "Capacity Credit",
    "Interest Rate",
)

# Branch types where INPUT variables with reliable units live. Restricted
# narrower than the values probe's default because Module-level (BT=2),
# Effect (BT=34), etc. branches expose target variable names ONLY as
# result aggregates — calling DataUnitText on those fires the
# "Data units are not available for result variables" modal. BT=3
# (Transformation Process) and BT=50 (Transformation Branch) are the
# only types that reliably carry input-side variables.
DEFAULT_BRANCH_TYPES = (3, 50)


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="probe_leap_units")
    p.add_argument("--area",
                   help="Expected ActiveArea name; aborts if mismatched")
    p.add_argument("--variables", default=",".join(DEFAULT_INPUT_VARS),
                   help="Comma-separated INPUT variable names (write-side)")
    p.add_argument("--branch-prefix",
                   help="Only branches whose FullName starts with this string")
    p.add_argument("--branch-types",
                   default=",".join(str(t) for t in DEFAULT_BRANCH_TYPES),
                   help="Comma-separated BranchType integers")
    p.add_argument("--max-branches", type=int, default=0,
                   help="Smoke-test cap (0 = unlimited)")
    p.add_argument("--per-branch-deadline", type=float, default=15.0,
                   help="Seconds before bailing on one branch's variable iteration")
    p.add_argument("--out", required=True,
                   help="Output CSV path (e.g. mailbox/.../units_<context>.csv)")
    return p.parse_args(argv)


def _safe_unit(variable) -> str:
    """Read ``Variable.DataUnitText`` (the canonical LEAP unit string).

    Uses :func:`nemo_read.leap_units.safe_data_unit_text` which wraps the
    read defensively. ``.Unit.Name`` does NOT work in this LEAP COM
    version (returns empty for both input and result variables); only
    ``.DataUnitText`` is reliable.

    Note: ``DataUnitText`` may fire a "Unrecognized unit" / similar
    modal popup on some result variables. The defensive wrapper catches
    the exception path; if a popup appears, dismiss it manually — the
    COM call still returns and the probe continues.
    """
    return safe_data_unit_text(variable) or ""


def main(argv=None) -> int:
    args = parse_args(argv)
    leap = dispatch_leap()
    area = leap.ActiveArea.Name
    print(f"[unitsB] ActiveArea:     {area!r}")
    if args.area and area != args.area:
        print(f"ERROR: ActiveArea is {area!r}, expected {args.area!r}.",
              file=sys.stderr)
        return 2
    print(f"[unitsB] ActiveScenario: {leap.ActiveScenario.Name!r} "
          f"(units are scenario-agnostic; using whatever's active)")

    # Set ActiveRegion to the first available; some COM properties need it
    # to resolve, but units themselves are region-agnostic.
    try:
        first_region = next(iter(leap.Regions)).Name
        leap.ActiveRegion = first_region
        print(f"[unitsB] ActiveRegion:   {first_region!r} (arbitrary)")
    except Exception as exc:
        print(f"ERROR: cannot set ActiveRegion: {exc}", file=sys.stderr)
        return 2

    target_vars = [v.strip() for v in args.variables.split(",") if v.strip()]
    type_filter = {int(t) for t in args.branch_types.split(",") if t.strip()}
    print(f"[unitsB] Input variables: {target_vars}")
    print(f"[unitsB] Branch types:    {sorted(type_filter)}")

    cache_file = (Path(leap.ActiveArea.Directory)
                  / "NEMO_25.leap_export" / ".tree_cache.json")
    cache = LeapTreeCache(leap=leap,
                          cache_file=cache_file if cache_file.exists() else None)
    print(f"[unitsB] Branches indexed: {len(cache.fullname_to_idx)}")

    branches_iter: list[tuple[int, str, int]] = []
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
    print(f"[unitsB] Branches to walk: {len(branches_iter)}")

    out_path = Path(args.out)
    started = time.perf_counter()
    n_pairs = 0
    n_branches_with_hits = 0
    empty_units_seen = 0
    target_set = set(target_vars)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["branch", "branch_type",
                                           "variable", "unit"])
        w.writeheader()

        for idx, fn, bt in branches_iter:
            try:
                br = cache.branches.Item(idx)
                vc = br.Variables.Count
            except Exception:
                continue

            # Walk by INDEX and capture only the FIRST occurrence of each
            # target name. This avoids the "Data units are not available
            # for result variables" modal popup that LEAP fires when
            # DataUnitText is called on a result-side variable.
            #
            # The variable list in LEAP COM is ordered: input vars first
            # (indexes 1..N_input), then result vars (indexes N_input+1..).
            # Duplicates like 'Maximum Availability' appear in both
            # sections; first-occurrence guarantees we fetch the input
            # variant. Result-only names (Energy Generation, Power
            # Generation, etc.) aren't in our curated target list, so
            # they're never touched.
            seen_names: set = set()
            branch_emitted = False
            for j in range(1, vc + 1):
                try:
                    v = br.Variables.Item(j)
                    name = v.Name
                except Exception:
                    continue
                if not name or name in seen_names or name not in target_set:
                    seen_names.add(name)
                    continue
                seen_names.add(name)

                unit = _safe_unit(v)
                if not unit:
                    empty_units_seen += 1
                w.writerow({
                    "branch": fn,
                    "branch_type": LEAP_BRANCH_TYPES.get(bt, str(bt)),
                    "variable": name,
                    "unit": unit,
                })
                n_pairs += 1
                branch_emitted = True

            if branch_emitted:
                n_branches_with_hits += 1

    elapsed = time.perf_counter() - started
    print()
    print(f"[unitsB] DONE in {elapsed:.1f}s")
    print(f"[unitsB] {n_pairs} (branch, variable) pairs from "
          f"{n_branches_with_hits} branches "
          f"({empty_units_seen} with empty unit)")
    print(f"[unitsB] CSV: {out_path}")
    if empty_units_seen > 0 and empty_units_seen >= n_pairs * 0.5:
        print()
        print("WARNING: more than half of pairs have empty unit. Either:")
        print("  - the variables in --variables are result-side (no .Unit attr)")
        print("  - the branches don't expose those variables on this LEAP version")
        print("  Discover the right names with nemo_read-list-branch-vars.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
