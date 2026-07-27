"""Build the commercial canonical inject payload (2026-07-22 cycle).

Ownership: the sector team owns CONTENT (values, sources, method); we own
STRUCTURE and UNITS. Every value below is taken from the team payload as
given -- no rescaling, no re-derivation.

Inputs
  comm2/ (v2, supersedes v1 where present)
    end_use_intensity.csv          Group 1  (Lighting withdrawn -> 50 rows)
    building_type_intensity.csv    Group 6
    water_heating_solar_shares.csv Group 7
  comm/  (v1, still governs)
    end_use_saturation.csv         Group 2  (60 rows, incl. Lighting)
    fuel_shares.csv                Group 3  (6,840 rows)

Outputs
  commercial_canonical_20260722.csv
  (BUILD_NOTES_20260722.md is written by hand alongside)
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRATCH = Path(
    r"C:\Users\ThinkPad\AppData\Local\Temp\claude"
    r"\c--Users-ThinkPad-Desktop-Py-YY-NEMO-read"
    r"\e5eed2c4-745e-4bab-a4ab-809cea7b2258\scratchpad"
)
COMM1 = SCRATCH / "comm"
COMM2 = SCRATCH / "comm2"
CANON_DIR = REPO / "inject/commercial/structure_handover_20260703"
CANON_VARS = CANON_DIR / "commercial_branch_variables_units.csv"
CANON_KEYS = CANON_DIR / "keys_slice_commercial_units.csv"

OUT_CSV = HERE / "commercial_canonical_20260722.csv"

COLUMNS = [
    "ams",
    "branch",
    "variable",
    "expression",
    "unit",
    "fuel",
    "source",
    "note",
    "src_csv",
    "data_confidence",
    "scenario",
]

EUP = r"Demand\Commercial\Other Commercial\End Use Projection"

REGION_ALIAS = {
    "Brunei Darussalam": "Brunei",
    "Lao PDR": "Laos",
    "Viet Nam": "Vietnam",
}
SCENARIO_ALIAS = {
    "Baseline": "Baseline Simulation",
    "AMS Target": "AMS Target Scenario",
    "Regional Aspiration": "Regional Aspiration Scenario",
}
END_USE_CANON = {
    "air_conditioning": "Air Conditioning",
    "cooking": "Cooking and Food Processing",
    "lighting": "Lighting",
    "other": "Other",
    "refrigeration": "Refrigeration",
    "water_heating": "Water Heating",
}

# Remainder(100) closes each family and MOVES BY SCENARIO (canon-verified,
# current_expressions_commercial_4scenarios.csv). The designated leaf is
# DROPPED from the write set for that scenario -- never overwritten.
REMAINDER_LEAF = {
    ("Air Conditioning", "Current Accounts"): "Current Stock_Average",
    ("Air Conditioning", "Baseline Simulation"): "Current Stock_Average",
    ("Air Conditioning", "AMS Target Scenario"): "Current Sales_Average",
    ("Air Conditioning", "Regional Aspiration Scenario"): "Efficient",
    ("Refrigeration", "Current Accounts"): "Existing",
    ("Refrigeration", "Baseline Simulation"): "Existing",
    ("Refrigeration", "AMS Target Scenario"): "Existing",
    ("Refrigeration", "Regional Aspiration Scenario"): "Existing",
}

ASEAN10 = {
    "Brunei",
    "Cambodia",
    "Indonesia",
    "Laos",
    "Malaysia",
    "Myanmar",
    "Philippines",
    "Singapore",
    "Thailand",
    "Vietnam",
}


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def num(value) -> str:
    """Format a number for a LEAP expression: period decimal, no exponent."""
    f = float(value)
    if f == int(f):
        return str(int(f))
    s = f"{f:.10f}".rstrip("0").rstrip(".")
    return s


def region_of(row_country: str) -> str:
    return REGION_ALIAS.get(row_country, row_country)


# --------------------------------------------------------------------------
# canon unit lookup -- units are OURS, read from the structure handover
# --------------------------------------------------------------------------
_canon_units: dict[tuple[str, str], str] = {}
for _src in (CANON_VARS, CANON_KEYS):
    for r in read_csv(_src):
        _canon_units[(r["branch_path"], r["variable"])] = r["units"]


def canon_unit(branch: str, variable: str) -> str:
    key = (branch, variable)
    if key not in _canon_units:
        raise SystemExit(f"canon has no ({branch!r}, {variable!r})")
    return _canon_units[key]


def canon_has(branch: str, variable: str) -> bool:
    return (branch, variable) in _canon_units


rows_out: list[dict] = []
stats: dict[str, int] = defaultdict(int)


def emit(group, ams, branch, variable, expression, source, note, src_csv, scenario=""):
    assert canon_has(branch, variable), f"NOT IN CANON: {branch} :: {variable}"
    assert ams in ASEAN10, f"region out of scope: {ams}"
    rows_out.append(
        {
            "ams": ams,
            "branch": branch,
            "variable": variable,
            "expression": expression,
            "unit": canon_unit(branch, variable),
            "fuel": "",
            "source": source,
            "note": note,
            "src_csv": src_csv,
            "data_confidence": "TEAM_AUTHORED",
            "scenario": scenario,
        }
    )
    stats[group] += 1


# ==========================================================================
# GROUP 1 -- B1 end-use intensity  ->  Commercial Uncalibrated Energy Intensity
#   value column = uncal_intensity_bridge  (R3: CAL untouched)
#   scenario = "" (all): canon holds this identically in all 4 scenarios
#   (61 groups, 0 varying -- verified against the 4-scenario export).
# ==========================================================================
for r in read_csv(COMM2 / "end_use_intensity.csv"):
    ams = region_of(r["Country"])
    eu = END_USE_CANON[r["end_use"]]
    emit(
        "G1_intensity",
        ams,
        rf"{EUP}\{eu}",
        "Commercial Uncalibrated Energy Intensity",
        num(r["uncal_intensity_bridge"]),
        r["source"],
        f"B1 uncal intensity bridge (team); source_tier={r['source_tier']}; "
        f"refresh_needed={r['refresh_needed']}; CAL untouched (R3)",
        "comm2/end_use_intensity.csv",
    )

# ==========================================================================
# GROUP 2 -- B3 end-use saturation  ->  Activity Level (end-use level)
#   LITERAL PERCENT (CLAUDE.md s11.2f): never divided by 100.
#   scenario = "" (all): canon 73 groups, 0 varying.
# ==========================================================================
for r in read_csv(COMM1 / "end_use_saturation.csv"):
    ams = region_of(r["Country"])
    eu = END_USE_CANON[r["end_use"]]
    emit(
        "G2_saturation",
        ams,
        rf"{EUP}\{eu}",
        "Activity Level",
        num(r["saturation_pct"]),
        r["source"],
        f"B3 saturation, literal percent (s11.2f); anchor_basis={r['anchor_basis']}; "
        f"source_tier={r['source_tier']}; refresh_needed={r['refresh_needed']}",
        "comm/end_use_saturation.csv",
    )

# ==========================================================================
# GROUP 3 -- B7 tech shares  ->  LEAF-level Activity Level (R1)
#   Six authored leaves only. Constant series collapse to a scalar.
#   The scenario's Remainder(100) leaf is DROPPED, never overwritten.
# ==========================================================================
series: dict[tuple, list[tuple[int, str]]] = defaultdict(list)
meta: dict[tuple, dict] = {}
for r in read_csv(COMM1 / "fuel_shares.csv"):
    key = (
        region_of(r["Country"]),
        END_USE_CANON[r["end_use"]],
        r["tech_leaf"],
        SCENARIO_ALIAS[r["scenario"]],
    )
    series[key].append((int(r["Year"]), r["share_pct"]))
    meta[key] = r

dropped: list[tuple] = []
g3_scalar = g3_interp = 0
for key in sorted(series):
    ams, eu, leaf, scen = key
    if REMAINDER_LEAF.get((eu, scen)) == leaf:
        dropped.append(key)
        continue
    pts = sorted(series[key])
    vals = [num(v) for _, v in pts]
    if len(set(vals)) == 1:
        expr = vals[0]
        g3_scalar += 1
    else:
        expr = "Interp(" + ", ".join(f"{y}, {v}" for (y, _), v in zip(pts, vals)) + ")"
        g3_interp += 1
    m = meta[key]
    emit(
        "G3_shares",
        ams,
        rf"{EUP}\{eu}\{leaf}",
        "Activity Level",
        expr,
        m["source"],
        f"B7 tech share on leaf Activity Level (R1; CFS_ is inert); "
        f"curve={m['curve']}; source_tier={m['source_tier']}; "
        f"Remainder(100) leaf for this scenario = {REMAINDER_LEAF[(eu, scen)]} (not written)",
        "comm/fuel_shares.csv",
        scenario=scen,
    )

# ==========================================================================
# GROUP 4 -- Refrigeration\Efficient : Final Energy Intensity
#   Canon shape (v0.67): '0.7 * Existing:Final Energy Intensity[kWh]'.
#   Only the coefficient changes -> 0.604 (R4).
#   Scenario-invariant in canon (identical in all 4) -> scenario = "".
# ==========================================================================
REFRIG_EFF = rf"{EUP}\Refrigeration\Efficient"
for ams in sorted(ASEAN10):
    emit(
        "G4_refrig_ratio",
        ams,
        REFRIG_EFF,
        "Final Energy Intensity",
        "0.604 * Existing:Final Energy Intensity[kWh]",
        "team: efficient_existing_ratio = 0.604 (fuel_shares.csv)",
        "R4: canon shape '0.7 * Existing:Final Energy Intensity[kWh]' preserved "
        "verbatim; coefficient 0.7 -> 0.604 only",
        "comm/fuel_shares.csv",
    )

# ==========================================================================
# GROUP 5 -- AC borrow re-point: NOT AUTHORED. See BUILD_NOTES section 5.
#   Route (i) requires a per-tier 'Useful Energy Intensity' on
#   Demand\Residential\Projections\Air Conditioning_. That variable does not
#   exist on that branch, and UEI on the size parents is tier-invariant, so
#   no ratio is constructible from verifiable paths. Rows left OUT per brief.
# ==========================================================================

# ==========================================================================
# GROUP 6 -- building-type controls -> Key\Commercial\Energy consumption per area
#   Canon holds these identically in all 4 scenarios -> scenario = "".
# ==========================================================================
for r in read_csv(COMM2 / "building_type_intensity.csv"):
    ams = region_of(r["Country"])
    branch = rf"Key\Commercial\Energy consumption per area\{r['building_type']}"
    emit(
        "G6_building_type",
        ams,
        branch,
        "Activity Level",
        num(r["kwh_m2"]),
        r["source"],
        "R6: building-type control (NOT Average Energy Intensity, which is a "
        "composite SUM(share x intensity))",
        "comm2/building_type_intensity.csv",
    )

# ==========================================================================
# GROUP 7 -- bug 7: Water Heating\Solar Heating : Activity Level, per region,
#   scenario-tagged: Regional Aspiration Scenario AND
#   Carbon Neutrality_ Net Zero Scenario. Values are percents, as given.
# ==========================================================================
SOLAR = rf"{EUP}\Water Heating\Solar Heating"
for r in read_csv(COMM2 / "water_heating_solar_shares.csv"):
    ams = region_of(r["Country"])
    scen = SCENARIO_ALIAS.get(r["scenario"], r["scenario"])
    emit(
        "G7_bug7_solar",
        ams,
        SOLAR,
        "Activity Level",
        num(r["activity_level_pct"]),
        r["source"],
        "R7: replaces the uniform '2' that RAS-level authoring imposed over the "
        "per-region values; literal percent (s11.2f)",
        "comm2/water_heating_solar_shares.csv",
        scenario=scen,
    )


# --------------------------------------------------------------------------
with open(OUT_CSV, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLUMNS)
    w.writeheader()
    w.writerows(rows_out)

print(f"wrote {OUT_CSV}  ({len(rows_out)} rows)")
for k in sorted(stats):
    print(f"  {k:22s} {stats[k]:5d}")
print(f"  G3 scalar-collapsed series : {g3_scalar}")
print(f"  G3 Interp() series         : {g3_interp}")
print(f"  G3 Remainder rows dropped  : {len(dropped)}")
bykey = defaultdict(int)
for ams, eu, leaf, scen in dropped:
    bykey[(eu, leaf, scen)] += 1
for k in sorted(bykey):
    print(f"    DROP {k[0]}\\{k[1]:22s} | {k[2]:30s} | {bykey[k]} regions")

# --------------------------------------------------------------------------
# sealed gates
# --------------------------------------------------------------------------
sys.path.insert(0, str(REPO))
from nemo_read import (  # noqa: E402
    find_region_lock_violations,
    find_zero_existing_capacity_conflicts,
    validate_canonical_csv_expressions,
)

print("\n--- sealed gates on the output CSV")
for name, fn in [
    ("find_region_lock_violations", find_region_lock_violations),
    ("find_zero_existing_capacity_conflicts", find_zero_existing_capacity_conflicts),
    ("validate_canonical_csv_expressions", validate_canonical_csv_expressions),
]:
    try:
        res = fn(OUT_CSV)
    except Exception as exc:  # noqa: BLE001
        print(f"  {name}: RAISED {type(exc).__name__}: {exc}")
        continue
    n = len(res) if res is not None else 0
    print(f"  {name}: {n} violation(s)" + (f" -> {res[:5]}" if n else " [PASS]"))
