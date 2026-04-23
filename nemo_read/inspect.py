"""
High-level inspection entry points for a quick scenario overview.

Typical use: `inspect_scenario(NemoDB("path.sqlite"))` returns a dict
with dimension sizes, populated parameters, saved results, validation
findings, custom constraints, and slack technologies. Intended as the
first thing you run when handed an unfamiliar scenario database.
"""

from __future__ import annotations
from typing import Any, Dict, List

import pandas as pd

from .db import NemoDB
from .schema import DIMENSIONS, PARAMETERS, RESULT_VARIABLES, TARGET_DB_VERSION
from .parameters import list_populated_parameters
from .variables import list_present_results
from .custom import list_custom_constraints, detect_slack_technologies
from .leap_conventions import LEAP_NEMO_UNITS
from .validate import validate_scenario
from .infeasibility import find_infeasibilities


def inspect_scenario(db: NemoDB, run_validation: bool = True) -> Dict[str, Any]:
    """Return a structured overview of a NEMO scenario database.

    Keys:
        path, version, version_mismatch, calculation_state, units,
        dimensions          : DataFrame of dim → member count
        parameters          : DataFrame from list_populated_parameters
        results             : DataFrame from list_present_results
        custom_constraints  : DataFrame from list_custom_constraints
        slack_technologies  : DataFrame from detect_slack_technologies
        unknown_tables      : tables present that this library does not recognise
                              (with ``__NEMOcc`` tables excluded since they
                              are now first-class)
        missing_dimensions  : expected dimension tables absent from the DB
        validation          : ValidationReport from validate_scenario,
                              or None if run_validation=False
        infeasibilities     : ValidationReport from find_infeasibilities,
                              or None if run_validation=False
    """
    overview: Dict[str, Any] = {
        "path": str(db.path),
        "version": db.version,
        "version_mismatch": db.version != TARGET_DB_VERSION,
        "units": dict(LEAP_NEMO_UNITS),  # defensive copy
    }

    # Dimension member counts.
    dim_rows: List[Dict[str, Any]] = []
    present_tables = set(db.list_tables())
    for name in DIMENSIONS:
        if name in present_tables:
            n = db.row_count(name)
            dim_rows.append({"dimension": name, "present": True, "members": n})
        else:
            dim_rows.append({"dimension": name, "present": False, "members": 0})
    overview["dimensions"] = pd.DataFrame(dim_rows)

    # Parameters populated in the DB.
    overview["parameters"] = list_populated_parameters(db)

    # Result tables (outputs) actually saved.
    results_df = list_present_results(db)
    overview["results"] = results_df

    # Calculation state.
    has_results = not results_df.empty and bool(results_df["rows"].sum())
    overview["calculation_state"] = "post-calculation" if has_results else "pre-calculation"

    # Custom constraints.
    overview["custom_constraints"] = list_custom_constraints(db)

    # Slack technologies.
    try:
        overview["slack_technologies"] = detect_slack_technologies(db)
    except Exception:
        overview["slack_technologies"] = pd.DataFrame(columns=["t", "desc", "reason"])

    # Unknown tables.
    known = set(DIMENSIONS) | set(PARAMETERS) | set(RESULT_VARIABLES) | {
        "Version", "DefaultParams", "nodalstorage", "yearintervals", "sqlite_sequence"
    }
    unknown = sorted(
        t for t in present_tables
        if t not in known
        and not t.startswith("v")
        and not t.endswith("__NEMOcc")
    )
    overview["unknown_tables"] = unknown

    overview["missing_dimensions"] = sorted(
        name for name in DIMENSIONS if name not in present_tables
    )

    # Validation and infeasibility checks.
    if run_validation:
        try:
            overview["validation"] = validate_scenario(db)
        except Exception as e:
            overview["validation"] = None
            overview["validation_error"] = repr(e)
        try:
            overview["infeasibilities"] = find_infeasibilities(db)
        except Exception as e:
            overview["infeasibilities"] = None
            overview["infeasibility_error"] = repr(e)
    else:
        overview["validation"] = None
        overview["infeasibilities"] = None

    return overview


def print_overview(db: NemoDB) -> None:
    """Human-readable summary to stdout. Intentionally simple; for richer
    reporting, consume `inspect_scenario()` directly and format as needed."""
    ov = inspect_scenario(db)
    print(f"NEMO scenario DB: {ov['path']}")
    print(f"  DB version: {ov['version']} "
          f"(library targets v{TARGET_DB_VERSION}"
          f"{', MISMATCH' if ov['version_mismatch'] else ''})")
    print(f"  State: {ov['calculation_state']}")
    print(f"  Units: energy={ov['units']['energy']}, "
          f"power={ov['units']['power']}, "
          f"cost={ov['units']['cost']}, emissions={ov['units']['emissions']}")

    dims = ov["dimensions"]
    present_dims = dims[dims["present"]]
    print(f"\nDimensions ({len(present_dims)}/{len(dims)} present):")
    for _, r in present_dims.iterrows():
        print(f"  {r['dimension']:<20s} {r['members']:>6d}")

    params = ov["parameters"]
    pop = params[params["rows"] > 0]
    print(f"\nParameters with data ({len(pop)}/{len(params)}):")
    for _, r in pop.iterrows():
        print(f"  {r['parameter']:<40s} rows={int(r['rows']):>7d}  "
              f"default={r['default']}")

    res = ov["results"]
    if res.empty:
        print("\nSaved result variables: none (pre-calculation database).")
    else:
        print(f"\nSaved result variables ({len(res)}):")
        for _, r in res.iterrows():
            flag = "" if r["known"] else "  [unknown]"
            print(f"  {r['variable']:<40s} rows={int(r['rows']):>7d}  "
                  f"dims={r['dims']}{flag}")

    cc = ov["custom_constraints"]
    if not cc.empty:
        print(f"\nCustom constraints ({len(cc)}):")
        for _, r in cc.iterrows():
            yr_range = ""
            if r["year_min"] is not None and r["year_max"] is not None:
                yr_range = f"  years={r['year_min']}-{r['year_max']}"
            print(f"  {r['short_name']:<40s} rows={int(r['rows']):>6d}{yr_range}")

    slk = ov["slack_technologies"]
    if not slk.empty:
        print(f"\nSlack technologies ({len(slk)}):")
        for _, r in slk.iterrows():
            desc = r["desc"] or ""
            print(f"  {r['t']:<15s} {desc:<25s}  [{r['reason']}]")

    vr = ov.get("validation")
    if vr is not None:
        errors = vr.errors()
        warnings = vr.warnings()
        if errors or warnings:
            print(f"\nValidation: {len(errors)} error(s), {len(warnings)} warning(s).")
            for i in vr.issues:
                flag = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(i.severity, "?")
                print(f"  {flag} [{i.category}] {i.table}: {i.message}")
        else:
            print("\nValidation: clean.")

    inf = ov.get("infeasibilities")
    if inf is not None:
        errors = inf.errors()
        warnings = inf.warnings()
        if errors or warnings:
            print(f"\nInfeasibility checks: {len(errors)} error(s), "
                  f"{len(warnings)} warning(s).")
            for i in inf.issues:
                flag = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(i.severity, "?")
                print(f"  {flag} [{i.category}] {i.table}: {i.message}")
        else:
            print("\nInfeasibility checks: clean.")

    if ov["unknown_tables"]:
        print("\nUnclassified tables:")
        for t in ov["unknown_tables"]:
            print(f"  {t}")
