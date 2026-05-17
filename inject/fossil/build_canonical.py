"""
Consolidate the 9 mailbox CSVs into one canonical, COM-injection-ready CSV
that matches the LEAP variable dictionary at unit level.

Canonical schema (one row = one (region, branch, variable) assignment):

    ams                 specific country (Brunei, Indonesia, ...)
    branch              LEAP FullName (e.g. "Resources\\Primary\\Crude Oil")
    variable            LEAP variable name as it appears in the Analysis pane
                          (e.g. "Import Cost", "Production Cost",
                          "Maximum Production", "Exogenous Capacity",
                          "Additions to Reserves", "Export Benefit")
    expression          LEAP expression string (Interp / Data / formula / scalar)
    unit                data unit per the source CSV's `basis` column
                          (USD/GJ real 2020 USD, USD/bbl real 2020 USD,
                          USD/100L real 2020 USD, PJ/year, Gbbl, etc.)
    fuel                fuel context if relevant (Crude Oil, Natural Gas, ...)
    source              citation
    note                free text
    src_csv             provenance — which mailbox file the row came from

Run:
    python mailbox/build_canonical.py
Output: mailbox/canonical_leap_inputs.csv
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

# CLAUDE.md §A.15: single source of truth for Interp() separator
# normalisation. `_normalize_interp` is re-exported here so existing
# call-sites and `run_workflow.py` keep working.
from nemo_read._leap_com import normalize_interp as _normalize_interp

MAILBOX = Path(__file__).parent

# ---------------------------------------------------------------------------
# AMS cohort definitions (LEAP region names — must match leap.Regions[].Name)
# ---------------------------------------------------------------------------
ALL_10_AMS = [
    "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
    "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam",
]

# Per-fuel "producing" cohorts derived from the source CSV notes.
PRODUCING_AMS = {
    "Coal Bituminous":     ["Indonesia", "Vietnam"],
    "Coal Sub bituminous": ["Indonesia", "Vietnam"],
    "Coal Lignite":        ["Indonesia", "Thailand", "Vietnam"],
    "Natural Gas":         ["Brunei", "Indonesia", "Malaysia", "Myanmar",
                            "Thailand", "Vietnam"],
}


def non_producing(fuel: str) -> list[str]:
    return [a for a in ALL_10_AMS if a not in PRODUCING_AMS.get(fuel, [])]


def expand_scope(scope: str, fuel: str) -> list[str]:
    if scope in ("all_10_AMS", "all"):
        return list(ALL_10_AMS)
    if scope == "producing_AMS":
        return list(PRODUCING_AMS.get(fuel, []))
    if scope == "non_producing_AMS":
        return non_producing(fuel)
    if scope in ALL_10_AMS:
        return [scope]
    raise ValueError(f"Unknown scope {scope!r} (fuel={fuel!r})")


# ---------------------------------------------------------------------------
# Interp builder for raw-data CSVs
# ---------------------------------------------------------------------------
def build_interp(year_value_pairs: list[tuple[int, float]]) -> str:
    """Build a LEAP Interp(year1, val1, year2, val2, ...) expression string.

    Comma list-separator + period decimal is the only form this engine
    accepts (see CLAUDE.md §A.15). Do not switch to semicolons.
    """
    pairs = sorted(year_value_pairs, key=lambda yv: yv[0])
    inner = ", ".join(f"{y}, {v:g}" for y, v in pairs)
    return f"Interp({inner})"


# ---------------------------------------------------------------------------
# Per-CSV transformers — each yields canonical-row dicts
# ---------------------------------------------------------------------------
def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def from_additions_to_reserves(path: Path):
    for r in _read_csv(path):
        yield {
            "ams":        r["ams"],
            "branch":     r["branch"],
            "variable":   r["variable"],
            "expression": r["expression"],
            "unit":       "Gbbl",
            "fuel":       "Crude Oil",
            "source":     r.get("source", ""),
            "note":       r.get("note", ""),
            "src_csv":    path.name,
        }


def from_supply_costs(path: Path):
    """Coal/Gas — scope-keyed Import Cost / Production Cost rows."""
    for r in _read_csv(path):
        fuel = r["fuel"]
        for ams in expand_scope(r["scope"], fuel):
            yield {
                "ams":        ams,
                "branch":     r["branch"],
                "variable":   r["variable"],
                "expression": r["leap_expression"],
                "unit":       r.get("basis", ""),
                "fuel":       fuel,
                "source":     r.get("source", ""),
                "note":       f"[scope={r['scope']}] {r.get('note', '')}".strip(),
                "src_csv":    path.name,
            }


def from_import_cost_trajectory(path: Path):
    for r in _read_csv(path):
        fuel = r["fuel"]
        for ams in expand_scope(r["ams"], fuel):
            yield {
                "ams":        ams,
                "branch":     r["branch"],
                "variable":   r["variable"],
                "expression": r["leap_expression"],
                "unit":       r.get("basis", ""),
                "fuel":       fuel,
                "source":     r.get("source", ""),
                "note":       r.get("note", ""),
                "src_csv":    path.name,
            }


def from_export_benefit(path: Path):
    for r in _read_csv(path):
        # branch tells us the fuel context (Crude Oil / Gasoline / Diesel ...)
        fuel = r["branch"].split("\\")[-1]
        yield {
            "ams":        r["ams"],
            "branch":     r["branch"],
            "variable":   r["variable"],
            "expression": r["expression"],
            "unit":       "(formula refers to Import Cost; unit inherited)",
            "fuel":       fuel,
            "source":     r.get("source", ""),
            "note":       r.get("note", ""),
            "src_csv":    path.name,
        }


def from_secondary_max_production(path: Path):
    for r in _read_csv(path):
        for ams in expand_scope(r["ams"], r["branch"].split("\\")[-1]):
            yield {
                "ams":        ams,
                "branch":     r["branch"],
                "variable":   r["variable"],
                "expression": r["expression"],
                "unit":       "PJ/year",
                "fuel":       r["branch"].split("\\")[-1],
                "source":     r.get("rationale", ""),
                "note":       r.get("note", ""),
                "src_csv":    path.name,
            }


def from_crude_oil_max_production(path: Path):
    """Per-(ams, year) → Interp expression on Crude Oil 'Maximum Production'."""
    grouped = defaultdict(list)        # ams -> [(year, value)]
    notes = {}
    sources = {}
    for r in _read_csv(path):
        ams = r["ams"]
        try:
            y = int(r["year"])
            v = float(r["production_pj_per_yr"])
        except (TypeError, ValueError):
            continue
        grouped[ams].append((y, v))
        if r.get("note") and ams not in notes:
            notes[ams] = r["note"]
        if r.get("source_basis") and ams not in sources:
            sources[ams] = r["source_basis"]
    for ams, pairs in grouped.items():
        yield {
            "ams":        ams,
            "branch":     "Resources\\Primary\\Crude Oil",
            "variable":   "Maximum Production",
            "expression": build_interp(pairs),
            "unit":       "PJ/year",
            "fuel":       "Crude Oil",
            "source":     sources.get(ams, ""),
            "note":       notes.get(ams, ""),
            "src_csv":    path.name,
        }


def from_crude_production_cost(path: Path):
    """Per-(ams, year) → Interp on Crude Oil 'Production Cost'."""
    grouped = defaultdict(list)
    notes = {}
    sources = {}
    for r in _read_csv(path):
        ams = r["ams"]
        try:
            y = int(r["year"])
            v = float(r["usd_per_bbl"])
        except (TypeError, ValueError):
            continue
        grouped[ams].append((y, v))
        if r.get("note") and ams not in notes:
            notes[ams] = r["note"]
        if r.get("primary_source") and ams not in sources:
            sources[ams] = r["primary_source"]
    for ams, pairs in grouped.items():
        yield {
            "ams":        ams,
            "branch":     "Resources\\Primary\\Crude Oil",
            "variable":   "Production Cost",
            "expression": build_interp(pairs),
            "unit":       "USD/bbl real 2020 USD",
            "fuel":       "Crude Oil",
            "source":     sources.get(ams, ""),
            "note":       notes.get(ams, ""),
            "src_csv":    path.name,
        }


def from_refinery_exogenous_capacity(path: Path):
    """Per-(ams, year) → Interp on Refinery 'Exogenous Capacity'.

    Branch confirmed in AEO9: a single aggregated Transformation Process
    (id=2544) at ``Transformation\\Oil Refining\\Processes\\All Refineries``.
    Per-AMS scoping happens at injection time via leap.ActiveRegion, same
    as every other Resource-branch variable.
    """
    grouped = defaultdict(list)
    notes = {}
    sources = {}
    for r in _read_csv(path):
        ams = r["ams"]
        try:
            y = int(r["year"])
            v = float(r["capacity_pj_per_yr"])
        except (TypeError, ValueError):
            continue
        grouped[ams].append((y, v))
        if r.get("step_change_note") and ams not in notes:
            notes[ams] = r["step_change_note"]
        if r.get("source") and ams not in sources:
            sources[ams] = r["source"]
    for ams, pairs in grouped.items():
        yield {
            "ams":        ams,
            "branch":     "Transformation\\Oil Refining\\Processes\\All Refineries",
            "variable":   "Exogenous Capacity",
            "expression": build_interp(pairs),
            "unit":       "PJ/year",
            "fuel":       "Refinery",
            "source":     sources.get(ams, ""),
            "note":       (notes.get(ams, "") + " || NOTE: LEAP UI displays "
                           "this in 'Thousand Gigajoules/Year' (= TJ/year); "
                           "factor 1000 applied").strip(" |"),
            "src_csv":    path.name,
        }


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
TRANSFORMERS = [
    ("additions_to_reserves.csv",     from_additions_to_reserves),
    ("coal_supply_costs.csv",         from_supply_costs),
    ("gas_supply_costs.csv",          from_supply_costs),
    ("import_cost_trajectory.csv",    from_import_cost_trajectory),
    ("export_benefit.csv",            from_export_benefit),
    ("secondary_max_production.csv",  from_secondary_max_production),
    ("crude_oil_max_production.csv",  from_crude_oil_max_production),
    ("crude_production_cost.csv",     from_crude_production_cost),
    ("refinery_exogenous_capacity.csv", from_refinery_exogenous_capacity),
]


def build():
    rows = []
    for fname, fn in TRANSFORMERS:
        path = MAILBOX / fname
        if not path.exists():
            print(f"  SKIP missing {fname}")
            continue
        before = len(rows)
        rows.extend(fn(path))
        print(f"  +{len(rows) - before:>3} rows from {fname}")

    out = MAILBOX / "canonical_leap_inputs.csv"
    fieldnames = ["ams", "branch", "variable", "expression", "unit", "fuel",
                  "source", "note", "src_csv"]
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            r["expression"] = _normalize_interp(r["expression"])
            writer.writerow(r)
    print(f"\nWrote {out}  ({len(rows)} rows)")
    # Quick sanity summary
    by_var = defaultdict(int)
    by_branch = defaultdict(int)
    for r in rows:
        by_var[r["variable"]] += 1
        by_branch[r["branch"]] += 1
    print("\nRows per variable:")
    for v, n in sorted(by_var.items(), key=lambda x: -x[1]):
        print(f"  {n:>4}  {v}")
    print("\nRows per branch:")
    for b, n in sorted(by_branch.items(), key=lambda x: -x[1]):
        print(f"  {n:>4}  {b}")


if __name__ == "__main__":
    build()
