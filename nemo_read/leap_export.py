"""
Export LEAP area metadata to a directory of plain files that
:class:`~nemo_read.leap_area.LeapAreaContext` can load on any platform.

Run once per area with LEAP open and the target area loaded:

.. code-block:: bash

    nemo_read-leap-export [--area NAME] [--output DIR] [--include-expressions]

Output directory contains:

- ``manifest.json`` — export metadata (area, timestamp, counts, format version)
- ``branches.csv`` — full LEAP tree (id, name, full_name, parent_id,
  parent_name, branch_type, branch_type_name, level, notes)
- ``fuels.csv`` — LEAP fuel ID → name
- ``regions.csv`` — LEAP region ID → name
- ``timeslices.csv`` — TimeSlice ID, name, hours
- ``scenarios.csv`` — scenario catalog (id, name, results_shown, last_calculated)
- ``tags.csv`` — tag catalog
- ``units.csv`` — unit catalog
- ``nemocc_sources.csv`` — ``*__NEMOcc`` variable → (branch_id, expression_head)
- ``nemo.cfg`` — verbatim copy from LEAP's WorkingDirectory
- ``customconstraints.txt`` — verbatim
- ``beforescenariocalc.txt`` / ``afterscenariocalc.txt`` — if present
- ``branch_variable_expressions.csv`` — only when ``--include-expressions`` set
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import __version__
from ._leap_com import (
    LeapTreeCache,
    dispatch_leap,
    iterate_variables_safe,
    safe_expression,
    safe_value,
    with_com_retry,
)

# Per-branch wallclock cap so a single slow branch can't hang the whole walk.
# Empirically observed >30s lockups in nemocc scans on AEO9.
_BRANCH_DEADLINE_SECONDS = 15.0

FORMAT_VERSION = 1

# BranchType codes that commonly host `*__NEMOcc` user variables.
# Module (2) is the canonical location; the others are superset safeguards.
# Derived from the probe walks in PHASE_A findings §3.
_NEMOCC_HOST_BRANCH_TYPES = frozenset({
    2,    # Transformation Module — canonical
    3,    # Transformation Process (rare, but some users add NEMOcc here)
    5,    # Transformation Process Category
    8,    # Key Assumptions Branch (root)
    9,    # Key Assumption Category
    10,   # Key Assumption
    14,   # Demand Branch (root)
    50,   # Transformation Branch (root)
})


@dataclass
class ExportStats:
    branches: int = 0
    fuels: int = 0
    regions: int = 0
    timeslices: int = 0
    scenarios: int = 0
    tags: int = 0
    units: int = 0
    nemocc_vars: int = 0
    expressions: int = 0
    value_rows: int = 0
    files_copied: list[str] = field(default_factory=list)


def _safe_attr(obj, name: str, default=None):
    try:
        return getattr(obj, name)
    except Exception:
        return default


def _safe_parent(branch) -> tuple[int | None, str | None]:
    try:
        parent = branch.Parent
    except Exception:
        return None, None
    if parent is None:
        return None, None
    return _safe_attr(parent, "ID"), _safe_attr(parent, "Name")


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def export_branches(cache: LeapTreeCache, out_dir: Path, stats: ExportStats,
                    log=print, progress_every: int = 500) -> None:
    branches = cache.branches
    cnt = branches.Count
    rows = []
    for i in range(1, cnt + 1):
        try:
            b = branches.Item(i)
        except Exception:
            continue
        pid, pname = _safe_parent(b)
        rows.append({
            "id": _safe_attr(b, "ID"),
            "name": _safe_attr(b, "Name"),
            "full_name": _safe_attr(b, "FullName"),
            "parent_id": pid,
            "parent_name": pname,
            "branch_type": _safe_attr(b, "BranchType"),
            "branch_type_name": _safe_attr(b, "BranchTypeName"),
            "level": _safe_attr(b, "Level"),
            "notes": _safe_attr(b, "Notes", "") or "",
        })
        if progress_every and i % progress_every == 0:
            log(f"[leap-export]   branches: {i}/{cnt} attributes read")
    _write_csv(out_dir / "branches.csv", rows,
               ["id", "name", "full_name", "parent_id", "parent_name",
                "branch_type", "branch_type_name", "level", "notes"])
    stats.branches = len(rows)


def _export_collection(leap, coll_attr: str, out_path: Path, extra_fields: list[str] | None = None) -> int:
    try:
        coll = getattr(leap, coll_attr)
        cnt = coll.Count
    except Exception:
        return 0
    fieldnames = ["id", "name"] + (extra_fields or [])
    rows = []
    for i in range(1, cnt + 1):
        try:
            item = coll.Item(i)
        except Exception:
            continue
        row = {"id": _safe_attr(item, "ID"), "name": _safe_attr(item, "Name")}
        for field_name in extra_fields or []:
            row[field_name] = _safe_attr(item, field_name.title().replace("_", ""))
        rows.append(row)
    _write_csv(out_path, rows, fieldnames)
    return len(rows)


def export_fuels(leap, out_dir: Path, stats: ExportStats) -> None:
    stats.fuels = _export_collection(leap, "Fuels", out_dir / "fuels.csv")


def export_regions(leap, out_dir: Path, stats: ExportStats) -> None:
    stats.regions = _export_collection(leap, "Regions", out_dir / "regions.csv")


def export_timeslices(leap, out_dir: Path, stats: ExportStats) -> None:
    try:
        coll = leap.TimeSlices
        cnt = coll.Count
    except Exception:
        stats.timeslices = 0
        return
    rows = []
    for i in range(1, cnt + 1):
        try:
            t = coll.Item(i)
        except Exception:
            continue
        rows.append({
            "id": _safe_attr(t, "ID"),
            "name": _safe_attr(t, "Name"),
            "hours": _safe_attr(t, "Hours"),
        })
    _write_csv(out_dir / "timeslices.csv", rows, ["id", "name", "hours"])
    stats.timeslices = len(rows)


def export_scenarios(leap, out_dir: Path, stats: ExportStats) -> None:
    try:
        coll = leap.Scenarios
        cnt = coll.Count
    except Exception:
        stats.scenarios = 0
        return
    rows = []
    for i in range(1, cnt + 1):
        try:
            s = coll.Item(i)
        except Exception:
            continue
        lc = _safe_attr(s, "LastCalculated")
        rows.append({
            "id": _safe_attr(s, "ID"),
            "name": _safe_attr(s, "Name"),
            "results_shown": _safe_attr(s, "ResultsShown"),
            "last_calculated": str(lc) if lc is not None else "",
        })
    _write_csv(out_dir / "scenarios.csv", rows,
               ["id", "name", "results_shown", "last_calculated"])
    stats.scenarios = len(rows)


def export_tags(leap, out_dir: Path, stats: ExportStats) -> None:
    stats.tags = _export_collection(leap, "Tags", out_dir / "tags.csv")


def export_units(leap, out_dir: Path, stats: ExportStats) -> None:
    stats.units = _export_collection(leap, "Units", out_dir / "units.csv")


def export_nemocc_sources(cache: LeapTreeCache, out_dir: Path, stats: ExportStats,
                          log=print) -> None:
    """Walk branches likely to host ``*__NEMOcc`` variables, record their sources.

    Restricts iteration to the branch types enumerated in
    :data:`_NEMOCC_HOST_BRANCH_TYPES` (typically ~200 branches out of 5000+).
    Scanning all 5k branches × ~50 vars each triggers LEAP's RPC server to
    drop the connection intermittently; this targeted scan avoids that
    entirely and runs in seconds instead of minutes.
    """
    # Load the already-written branches.csv — faster than re-walking COM
    # just to find the branch-type filter targets.
    import csv as _csv
    branches_csv = out_dir / "branches.csv"
    targets: list[tuple[int, int, str]] = []  # (idx, branch_id, branch_full_name)
    if branches_csv.exists():
        with branches_csv.open(encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                try:
                    bt = int(row["branch_type"]) if row["branch_type"] else -1
                    bid = int(row["id"]) if row["id"] else None
                except (TypeError, ValueError):
                    continue
                if bt not in _NEMOCC_HOST_BRANCH_TYPES or bid is None:
                    continue
                idx = cache.id_to_idx.get(bid)
                if idx is None:
                    continue
                targets.append((idx, bid, row["full_name"]))

    log(f"[leap-export]   scanning {len(targets)} candidate host branches")
    rows: list[dict] = []
    scanned = 0
    for idx, bid, bfull in targets:
        def _scan(_idx=idx, _bid=bid, _bfull=bfull):
            branch = cache.branches.Item(_idx)
            # First pass: just names (no .Expression access — that can fire a
            # LEAP modal on result variables and block until user dismiss).
            nemocc_names = []
            for _, name, _ in iterate_variables_safe(
                branch, deadline_seconds=_BRANCH_DEADLINE_SECONDS,
                fetch_expression=False,
            ):
                if name and name.endswith("__NEMOcc"):
                    nemocc_names.append(name)
            # Second pass: only fetch Expression on the (rare) NEMOcc hits.
            for name in nemocc_names:
                try:
                    var = branch.Variable(name)
                    expr = safe_expression(var) if var is not None else None
                except Exception:
                    expr = None
                head = ""
                if isinstance(expr, str):
                    head = expr[:200].replace("\n", " ")
                rows.append({
                    "table_name": name,
                    "branch_id": _bid,
                    "branch_full_name": _bfull,
                    "expression_head": head,
                })
        try:
            with_com_retry(_scan, retries=2)
        except Exception:
            # Non-fatal: log the branch but keep going.
            rows.append({
                "table_name": "__SCAN_ERROR__",
                "branch_id": bid,
                "branch_full_name": bfull,
                "expression_head": "com_error during scan",
            })
        scanned += 1
        if scanned % 50 == 0:
            log(f"[leap-export]   nemocc scan: {scanned}/{len(targets)} branches")
    _write_csv(out_dir / "nemocc_sources.csv", rows,
               ["table_name", "branch_id", "branch_full_name", "expression_head"])
    stats.nemocc_vars = sum(1 for r in rows if r["table_name"] != "__SCAN_ERROR__")


def export_expressions(cache: LeapTreeCache, out_dir: Path, stats: ExportStats,
                       log=print) -> None:
    """Dump Variable.Expression for every input variable on every branch.

    Captures only variables where Expression is a string (input variables).
    Result variables (Expression=None or COM error) are silently skipped.
    Active scenario only — call with --all-scenarios to extend.
    """
    leap = cache.leap
    scenario_name = ""
    try:
        scenario_name = leap.ActiveScenario.Name
    except Exception:
        pass
    branches = cache.branches
    cnt = branches.Count
    rows = []
    log(f"[leap-export]   walking {cnt} branches for input expressions "
        f"(active scenario: {scenario_name!r})")
    for i in range(1, cnt + 1):
        try:
            b = branches.Item(i)
        except Exception:
            continue
        try:
            bid = b.ID
        except Exception:
            continue
        # Names-only first pass; second pass calls safe_expression only on
        # variables we want. Avoids touching .Expression on result variables
        # (which can fire a modal LEAP dialog and block COM).
        names = [name for _, name, _ in iterate_variables_safe(
            b, deadline_seconds=_BRANCH_DEADLINE_SECONDS, fetch_expression=False,
        ) if name]
        for name in names:
            try:
                var = b.Variable(name)
            except Exception:
                continue
            if var is None:
                continue
            expr = safe_expression(var)
            if expr is None or not isinstance(expr, str):
                continue
            rows.append({
                "branch_id": bid,
                "variable_name": name,
                "scenario_name": scenario_name,
                "expression": expr,
            })
        if i % 500 == 0:
            log(f"[leap-export]   expressions: {i}/{cnt} branches scanned "
                f"({len(rows)} input vars so far)")
    _write_csv(out_dir / "branch_variable_expressions.csv", rows,
               ["branch_id", "variable_name", "scenario_name", "expression"])
    stats.expressions = len(rows)


def export_branch_values(
    cache: LeapTreeCache,
    out_dir: Path,
    stats: ExportStats,
    *,
    scope: str = "demand-leaves",
    log=print,
) -> None:
    """Dump Variable.Value() for selected branches, years, and regions.

    The ``scope`` controls which branches and variables get probed:

    - ``"demand-leaves"`` (default) — every leaf demand-tech branch (BT=4)
      under the LEAP ``Demand`` subtree, capturing ``Final Energy Demand``
      and ``Activity Level``. Sufficient to reconstruct demand-by-sector
      offline. ~5–15 min for AEO9-sized areas.
    - ``"all-input-vars"`` — every branch's every input-variable, all years
      × all regions. Multiplier is large; ~30–60+ min on a 5k-branch tree.

    Active scenario only. Use the ``--all-scenarios`` CLI flag to repeat
    across every scenario.
    """
    leap = cache.leap
    try:
        scenario = leap.ActiveScenario
        scenario_id = int(scenario.ID)
        scenario_name = str(scenario.Name)
    except Exception:
        scenario_id, scenario_name = -1, ""
    base = int(getattr(leap, "BaseYear", 0) or 0)
    end = int(getattr(leap, "EndYear", 0) or 0)
    fsy = int(getattr(leap, "FirstScenarioYear", base) or base)
    years_full = list(range(base, end + 1)) if base and end else []
    # For demand reporting we typically only need decade markers + scenario years
    years_subset = sorted(set([base] + list(range(fsy, end + 1, 5))))[:20] if years_full else []

    # Region (id, name) pairs from regions.csv. We iterate by NAME because
    # leap.ActiveRegion expects the name string; the id is kept for output.
    import csv as _csv
    region_pairs: list[tuple[int, str]] = []
    rcsv = out_dir / "regions.csv"
    if rcsv.exists():
        with rcsv.open(encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                try:
                    rid = int(row["id"])
                except (TypeError, ValueError):
                    continue
                rname = row.get("name") or ""
                if rname:
                    region_pairs.append((rid, rname))

    # Pick targets based on scope
    branches_csv = out_dir / "branches.csv"
    targets: list[tuple[int, int, str]] = []  # (idx, branch_id, full_name)
    if scope == "demand-leaves":
        target_var_names = {"Final Energy Demand", "Activity Level"}
        if branches_csv.exists():
            with branches_csv.open(encoding="utf-8") as f:
                for row in _csv.DictReader(f):
                    try:
                        bt = int(row["branch_type"]) if row["branch_type"] else -1
                        bid = int(row["id"]) if row["id"] else None
                    except (TypeError, ValueError):
                        continue
                    if bid is None:
                        continue
                    full = row.get("full_name") or ""
                    if not full.startswith("Demand"):
                        continue
                    if bt != 4:           # leaf demand technology
                        continue
                    idx = cache.id_to_idx.get(bid)
                    if idx is None:
                        continue
                    targets.append((idx, bid, full))
    elif scope == "all-input-vars":
        target_var_names = None  # capture every input var on every branch
        for bid, idx in cache.id_to_idx.items():
            targets.append((idx, bid, ""))
    else:
        log(f"[leap-export]   unknown values scope {scope!r}, skipping")
        return

    log(f"[leap-export]   walking {len(targets)} branches × "
        f"{len(years_subset)} years × {len(region_pairs)} regions for values "
        f"(scope={scope!r})")
    rows = []

    # Outer loop: regions. leap.ActiveRegion is GLOBAL state — setting it once
    # per region (12x) is much cheaper than per-call (~140k times) and avoids
    # passing region as a positional arg to Value() (LEAP treats arg 2 as unit,
    # not region — produces "Unrecognized unit" modal popups).
    for rid, rname in region_pairs:
        try:
            leap.ActiveRegion = rname
        except Exception as exc:
            log(f"[leap-export]   could not set ActiveRegion={rname!r}: {exc}")
            continue
        scanned = 0
        for idx, bid, full in targets:
            def _scan(_idx=idx, _bid=bid, _rid=rid):
                branch = cache.branches.Item(_idx)
                # Names-only iteration: never touch .Expression here. Value()
                # is safe for both input and result vars (returns the computed
                # number); .Expression on a result var fires a LEAP modal.
                for _, name, _ in iterate_variables_safe(
                    branch, deadline_seconds=_BRANCH_DEADLINE_SECONDS,
                    fetch_expression=False,
                ):
                    if not name:
                        continue
                    if target_var_names is not None and name not in target_var_names:
                        continue
                    try:
                        var = branch.Variable(name)
                    except Exception:
                        continue
                    if var is None:
                        continue
                    for y in years_subset:
                        v = safe_value(var, y)
                        if v is None:
                            continue
                        rows.append({
                            "branch_id": _bid,
                            "variable_name": name,
                            "scenario_id": scenario_id,
                            "scenario_name": scenario_name,
                            "region_id": _rid,
                            "year": y,
                            "value": v,
                        })
            try:
                with_com_retry(_scan, retries=2)
            except Exception:
                pass
            scanned += 1
            if scanned % 100 == 0:
                log(f"[leap-export]   values: region={rname!r} "
                    f"{scanned}/{len(targets)} branches scanned, "
                    f"{len(rows)} total rows")
        log(f"[leap-export]   values: region={rname!r} done "
            f"({len(rows)} rows so far)")
    _write_csv(out_dir / "branch_variable_values.csv", rows,
               ["branch_id", "variable_name", "scenario_id", "scenario_name",
                "region_id", "year", "value"])
    stats.value_rows = len(rows)


def copy_working_files(leap, out_dir: Path, stats: ExportStats) -> None:
    """Copy nemo.cfg, customconstraints.txt, before/after Julia scripts verbatim."""
    try:
        wd = Path(leap.WorkingDirectory)
    except Exception:
        return
    if not wd.exists():
        return
    for fname in ("nemo.cfg", "customconstraints.txt",
                  "beforescenariocalc.txt", "afterscenariocalc.txt"):
        src = wd / fname
        if src.exists():
            dst = out_dir / fname
            shutil.copy2(src, dst)
            stats.files_copied.append(fname)


def find_scenario_database(leap) -> Path | None:
    """Glob the area directory for a NEMO scenario sqlite."""
    try:
        area_dir = Path(leap.ActiveArea.Directory)
    except Exception:
        return None
    if not area_dir.exists():
        return None
    candidates = sorted(area_dir.glob("*.sqlite"), key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0] if candidates else None


def resolve_output_dir(leap, user_supplied: str | None) -> Path:
    if user_supplied:
        return Path(user_supplied)
    # Default: next to the scenario sqlite, named <stem>.leap_export/
    scenario_db = find_scenario_database(leap)
    if scenario_db is not None:
        return scenario_db.with_suffix(".leap_export")
    # Fallback: area_directory / leap_export/
    try:
        area_dir = Path(leap.ActiveArea.Directory)
        return area_dir / "leap_export"
    except Exception:
        return Path.cwd() / "leap_export"


def write_manifest(leap, out_dir: Path, stats: ExportStats,
                   include_expressions: bool) -> None:
    scenario_db = find_scenario_database(leap)
    manifest = {
        "format_version": FORMAT_VERSION,
        "nemo_read_version": __version__,
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "area": _safe_attr(leap.ActiveArea, "Name"),
        "area_directory": str(_safe_attr(leap.ActiveArea, "Directory", "")),
        "working_directory": str(_safe_attr(leap, "WorkingDirectory", "")),
        "active_scenario": _safe_attr(leap.ActiveScenario, "Name"),
        "base_year": _safe_attr(leap, "BaseYear"),
        "first_scenario_year": _safe_attr(leap, "FirstScenarioYear"),
        "end_year": _safe_attr(leap, "EndYear"),
        "scenario_database": str(scenario_db) if scenario_db else None,
        "include_expressions": include_expressions,
        "stats": asdict(stats),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )


def run_export(
    area: str | None = None,
    output: str | None = None,
    include_expressions: bool = False,
    values_scope: str | None = "demand-leaves",
    scenario: str | None = None,
    log=print,
) -> Path:
    """Programmatic entry point. Returns the output directory path.

    Default capture (0.6.2+): branch tree, dimension catalogues, NEMOcc
    sources, demand-leaf values (sufficient for offline sector breakdowns).

    ``include_expressions=True`` adds the input-variable Expression dump
    for the active scenario. Captures LEAP-side formulas but can fire
    modal "Expressions are not used for result variables" dialogs in
    LEAP — Python catches the COM error after each dismiss but the
    blocking dialog is intrusive to a working LEAP user. Use the
    ``--include-expressions`` CLI flag when you actually need them.
    """
    leap = dispatch_leap()

    if area is not None:
        try:
            current = leap.ActiveArea.Name
        except Exception:
            current = None
        if current != area:
            try:
                leap.ActiveArea = area
            except Exception as exc:
                raise RuntimeError(
                    f"Could not switch LEAP to area {area!r}: {exc}. "
                    f"Open it manually via File → Open Area."
                )

    area_name = leap.ActiveArea.Name
    log(f"[leap-export] Active area: {area_name!r}")

    if scenario is not None:
        try:
            current = leap.ActiveScenario.Name
        except Exception:
            current = None
        if current != scenario:
            try:
                leap.ActiveScenario = scenario
                log(f"[leap-export] Switched ActiveScenario {current!r} -> "
                    f"{leap.ActiveScenario.Name!r}")
            except Exception as exc:
                raise RuntimeError(
                    f"Could not switch scenario to {scenario!r}: {exc}. "
                    f"Open the scenario in LEAP first or pick a valid name."
                )
    log(f"[leap-export] Active scenario: {leap.ActiveScenario.Name!r}")

    out_dir = resolve_output_dir(leap, output)
    out_dir.mkdir(parents=True, exist_ok=True)
    log(f"[leap-export] Output directory: {out_dir}")

    cache = LeapTreeCache(leap=leap, cache_file=out_dir / ".tree_cache.json")

    stats = ExportStats()

    log("[leap-export] Building branch id->idx map (may take minutes on first run)...")
    _ = cache.id_to_idx
    log(f"[leap-export]   {len(cache.id_to_idx)} branches indexed "
        f"({cache._build_errors} errors)")

    log("[leap-export] Writing branches.csv...")
    export_branches(cache, out_dir, stats, log=log)

    log("[leap-export] Writing fuels/regions/timeslices/scenarios/tags/units CSVs...")
    export_fuels(leap, out_dir, stats)
    export_regions(leap, out_dir, stats)
    export_timeslices(leap, out_dir, stats)
    export_scenarios(leap, out_dir, stats)
    export_tags(leap, out_dir, stats)
    export_units(leap, out_dir, stats)

    log("[leap-export] Scanning for *__NEMOcc variables...")
    export_nemocc_sources(cache, out_dir, stats, log=log)

    if include_expressions:
        log("[leap-export] Dumping input-variable expressions (active scenario)...")
        export_expressions(cache, out_dir, stats, log=log)

    if values_scope:
        log(f"[leap-export] Dumping branch values (scope={values_scope!r})...")
        export_branch_values(cache, out_dir, stats, scope=values_scope, log=log)

    log("[leap-export] Copying nemo.cfg / customconstraints.txt etc...")
    copy_working_files(leap, out_dir, stats)

    write_manifest(leap, out_dir, stats, include_expressions)

    log(f"[leap-export] Done: {stats.branches} branches, {stats.fuels} fuels, "
        f"{stats.regions} regions, {stats.timeslices} timeslices, "
        f"{stats.scenarios} scenarios, {stats.tags} tags, {stats.units} units, "
        f"{stats.nemocc_vars} NEMOcc vars, {stats.expressions} expressions, "
        f"{stats.value_rows} value rows.")
    log(f"[leap-export] Files copied: {stats.files_copied}")
    return out_dir


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nemo_read-leap-export",
        description="Export LEAP area metadata to a directory for offline decoding.",
    )
    parser.add_argument(
        "--area",
        help="LEAP area name to export (default: current ActiveArea)",
    )
    parser.add_argument(
        "--output",
        help="Output directory (default: <scenario_db_stem>.leap_export/ next to the .sqlite)",
    )
    parser.add_argument(
        "--include-expressions", dest="include_expressions",
        action="store_true", default=False,
        help="Also dump LEAP input-variable Expression strings for the "
             "active scenario. Off by default because .Expression access "
             "on result variables can fire modal LEAP dialogs that block "
             "COM until the user clicks OK. Enable when you need formulas.",
    )
    parser.add_argument(
        "--values-scope", choices=("demand-leaves", "all-input-vars", "none"),
        default="demand-leaves",
        help="Branches/variables to capture numeric Value() for. "
             "'demand-leaves' (default) is sufficient for offline sector "
             "breakdown. 'all-input-vars' is exhaustive but slow. "
             "'none' skips value capture entirely.",
    )
    parser.add_argument(
        "--scenario",
        help="LEAP scenario to capture values from (default: current "
             "ActiveScenario). The scenario must already exist in the area; "
             "this switches LEAP's ActiveScenario before the values walk.",
    )
    args = parser.parse_args(argv)
    values_scope = None if args.values_scope == "none" else args.values_scope

    try:
        run_export(
            area=args.area,
            output=args.output,
            include_expressions=args.include_expressions,
            values_scope=values_scope,
            scenario=args.scenario,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
