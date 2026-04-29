"""
Capture LEAP variable units (the per-variable display unit set in the LEAP UI)
from a live LEAP COM session.

LEAP exposes the unit string via ``Variable.DataUnitText`` (early-binding
introspection finds it; the more obvious ``Variable.Unit`` is an
AttributeError). This module wraps that read defensively, walks every
branch's variables, and writes a ``branch_variable_units.csv`` that
``LeapAreaContext`` then loads alongside the other export CSVs.

CLI:
    nemo_read-leap-units                       # all input vars on every branch
    nemo_read-leap-units --canonical mailbox/canonical_leap_inputs.csv
                                                # only the (branch, variable) pairs in that csv
    nemo_read-leap-units --output ./units.csv  # alternate output location

Pair with :func:`nemo_read.leap_area.audit_canonical_units` to compare
user-documented units against the LEAP-side reality before injection.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from . import __version__
from ._leap_com import (
    LeapTreeCache, dispatch_leap, iterate_variables_safe, with_com_retry,
)


def safe_data_unit_text(variable) -> str | None:
    """Return ``variable.DataUnitText`` or None.

    LEAP's COM exposes the displayed unit string via ``DataUnitText``
    (alongside ``DataUnitID`` for the integer code). Wrapped in a defensive
    try/except so result variables that raise on the read return None
    rather than propagate.
    """
    try:
        v = variable.DataUnitText
    except Exception:
        return None
    return str(v) if v is not None else None


def safe_data_unit_id(variable) -> int | None:
    try:
        v = variable.DataUnitID
    except Exception:
        return None
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def probe_units_for_pairs(
    cache: LeapTreeCache,
    pairs: list[tuple[int, str]],   # [(branch_id, variable_name), ...]
    log=print,
) -> list[dict]:
    """Probe DataUnitText on a specific list of (branch_id, variable_name)
    pairs. Use this when you know exactly which units you need (e.g. a
    canonical injection CSV)."""
    rows = []
    for i, (bid, vname) in enumerate(pairs, start=1):
        idx = cache.id_to_idx.get(bid)
        if idx is None:
            rows.append({
                "branch_id": bid, "branch_full_name": "",
                "variable_name": vname,
                "data_unit_text": "<branch not found>",
                "data_unit_id": "",
            })
            continue
        def _scan(_idx=idx, _bid=bid, _vname=vname):
            branch = cache.branches.Item(_idx)
            try:
                full = branch.FullName
            except Exception:
                full = ""
            try:
                var = branch.Variable(_vname)
            except Exception:
                var = None
            unit = safe_data_unit_text(var) if var is not None else None
            uid = safe_data_unit_id(var) if var is not None else None
            rows.append({
                "branch_id": _bid,
                "branch_full_name": full,
                "variable_name": _vname,
                "data_unit_text": unit if unit is not None else "<no unit>",
                "data_unit_id": uid if uid is not None else "",
            })
        try:
            with_com_retry(_scan, retries=2)
        except Exception:
            rows.append({
                "branch_id": bid, "branch_full_name": "",
                "variable_name": vname,
                "data_unit_text": "<com_error>",
                "data_unit_id": "",
            })
        if i % 25 == 0:
            log(f"[leap-units]   probed {i}/{len(pairs)} pairs")
    return rows


def probe_units_all_input_vars(
    cache: LeapTreeCache,
    log=print,
    progress_every: int = 200,
) -> list[dict]:
    """Walk every branch, probe DataUnitText on every variable.

    Slow on large areas (~20-40 min for AEO9-sized trees, ~100k Variable
    handles touched). Use ``probe_units_for_pairs`` when you only need
    units for a specific injection set.
    """
    branches = cache.branches
    cnt = branches.Count
    rows = []
    log(f"[leap-units]   walking {cnt} branches for variable units")
    for i in range(1, cnt + 1):
        try:
            b = branches.Item(i)
            bid = b.ID
            full = b.FullName
        except Exception:
            continue
        # Names-only first (no .Expression to avoid result-var modal popups)
        var_names = [name for _, name, _ in iterate_variables_safe(
            b, deadline_seconds=15.0, fetch_expression=False,
        ) if name]
        for name in var_names:
            try:
                var = b.Variable(name)
            except Exception:
                continue
            if var is None:
                continue
            unit = safe_data_unit_text(var)
            uid = safe_data_unit_id(var)
            if unit is None and uid is None:
                # Skip rows that yielded no signal at all (typically result vars)
                continue
            rows.append({
                "branch_id": bid,
                "branch_full_name": full,
                "variable_name": name,
                "data_unit_text": unit if unit is not None else "",
                "data_unit_id": uid if uid is not None else "",
            })
        if i % progress_every == 0:
            log(f"[leap-units]   {i}/{cnt} branches scanned, "
                f"{len(rows)} units captured")
    return rows


def write_units_csv(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "branch_id", "branch_full_name", "variable_name",
            "data_unit_text", "data_unit_id",
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def write_tree_paths_csv(cache: LeapTreeCache, out_path: Path) -> int:
    """Write every branch FullName known to the cache to a single-column CSV.

    Used by :func:`nemo_read.leap_area.audit_canonical_units` to suggest
    closest-match branches for canonical rows whose ``branch`` doesn't
    exist in the LEAP tree. Cheap (~one second after the cache is built).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fullnames = sorted(cache.fullname_to_idx.keys())
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["branch_full_name"])
        for fn in fullnames:
            writer.writerow([fn])
    return len(fullnames)


def _load_canonical_pairs(canon_csv: Path) -> list[tuple[int, str]]:
    """Read mailbox canonical CSV; return unique (branch_id, variable) pairs.

    Branch IDs are looked up by FullName via the live LeapTreeCache when
    the canonical CSV doesn't already carry an id column. Caller
    handles the lookup."""
    import pandas as pd
    df = pd.read_csv(canon_csv)
    if "branch" not in df.columns or "variable" not in df.columns:
        raise ValueError(
            f"{canon_csv} missing required columns 'branch' and 'variable'"
        )
    return list({(row["branch"], row["variable"]) for _, row in df.iterrows()})


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nemo_read-leap-units",
        description=(
            "Capture LEAP variable units (DataUnitText) per (branch, variable) "
            "pair and write a CSV that LeapAreaContext loads alongside the "
            "main export CSVs."
        ),
    )
    parser.add_argument(
        "--scenario",
        help="Set leap.ActiveScenario before probing (units may be "
             "scenario-independent in most builds, but set explicitly for "
             "reproducibility).",
    )
    parser.add_argument(
        "--canonical",
        help="Probe only the (branch, variable) pairs found in this CSV "
             "(must have 'branch' and 'variable' columns). Faster than --all.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Walk every branch's input variables. Slow (~20-40 min on "
             "AEO9-sized trees). Default behaviour when --canonical is omitted.",
    )
    parser.add_argument(
        "--output",
        help="Output CSV path. Default: <ActiveArea.Directory>/"
             "NEMO_25.leap_export/branch_variable_units.csv",
    )
    args = parser.parse_args(argv)

    leap = dispatch_leap()
    print(f"[leap-units] Active area:     {leap.ActiveArea.Name!r}")
    print(f"[leap-units] Active scenario: {leap.ActiveScenario.Name!r}")
    if args.scenario and leap.ActiveScenario.Name != args.scenario:
        try:
            leap.ActiveScenario = args.scenario
            print(f"[leap-units] switched ActiveScenario -> "
                  f"{leap.ActiveScenario.Name!r}")
        except Exception as exc:
            print(f"ERROR: could not switch scenario: {exc}", file=sys.stderr)
            return 2

    out_path = Path(args.output) if args.output else (
        Path(leap.ActiveArea.Directory) / "NEMO_25.leap_export"
        / "branch_variable_units.csv"
    )
    cache_file = (Path(leap.ActiveArea.Directory)
                  / "NEMO_25.leap_export" / ".tree_cache.json")
    cache = LeapTreeCache(leap=leap,
                          cache_file=cache_file if cache_file.exists() else None)
    print(f"[leap-units] building branch maps ...")
    t0 = time.perf_counter()
    _ = cache.fullname_to_idx
    print(f"[leap-units]   {len(cache.fullname_to_idx)} branches indexed "
          f"({time.perf_counter()-t0:.1f}s)")

    if args.canonical:
        canon = Path(args.canonical)
        if not canon.exists():
            print(f"ERROR: --canonical CSV not found: {canon}", file=sys.stderr)
            return 1
        # Resolve (branch_fullname, variable) → (branch_id, variable)
        fullname_pairs = _load_canonical_pairs(canon)
        bid_pairs = []
        for (full, vname) in fullname_pairs:
            idx = cache.fullname_to_idx.get(full)
            if idx is None:
                print(f"  warn: branch not in tree, skipping: {full}")
                continue
            try:
                bid = cache.branches.Item(idx).ID
            except Exception:
                continue
            bid_pairs.append((bid, vname))
        print(f"[leap-units] probing {len(bid_pairs)} canonical pairs")
        rows = probe_units_for_pairs(cache, bid_pairs, log=print)
    else:
        # --all (default when --canonical not supplied)
        print("[leap-units] no --canonical CSV — walking ALL input variables")
        print("[leap-units] (may take 20-40 min on AEO9-sized trees)")
        rows = probe_units_all_input_vars(cache, log=print)

    write_units_csv(rows, out_path)
    print(f"\n[leap-units] wrote {out_path}  ({len(rows)} unit rows)")

    # Also persist the full tree-path list so offline audit/fuzzy-match
    # can suggest closest branches without needing a live LEAP session.
    tree_path_csv = out_path.parent / "tree_paths.csv"
    n = write_tree_paths_csv(cache, tree_path_csv)
    print(f"[leap-units] wrote {tree_path_csv}  ({n} branch paths)")
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
