"""Build the inject-patch CSV for the 2026-04-30 hot-fix cycle.

Combined scope:
  - Issue 5 — Max Capacity expressions on 7 biodiesel/bioethanol processes,
    curve-preserving Add (deltas) across 11 regions = 77 rows.
  - Issue 1 — Brunei solar Minimum Utilization, set to 0 to remove the
    must-run constraint on variable renewables = 3 rows.

NOT in this patch:
  - Issue 2 — leftover Demand branches under
    `Demand\\Non Energy Biomass\\{Palm Oil,Coconut Oil,Cassava,Sugarcane}`.
    Cannot be fixed via Variable expressions (canonical inject only
    writes values, can't delete branches). User will manually delete
    these 4 branches in the LEAP UI before next NEMO export.

80 rows total.
"""
from __future__ import annotations

import csv
from pathlib import Path

SRC = Path(__file__).parent / "bioenergy_leap_input.csv"
OUT = Path(__file__).parent / "canonical_patch_2026_04_30.csv"

PROCESSES = [
    r"Transformation\Biodiesel Production\Processes\FAME Biodiesel",
    r"Transformation\Biodiesel Production\Processes\CME Biodiesel",
    r"Transformation\Biodiesel Production\Processes\POME Biodiesel",
    r"Transformation\Bioethanol Production\Processes\Corn Ethanol",
    r"Transformation\Bioethanol Production\Processes\Cassava",
    r"Transformation\Bioethanol Production\Processes\Sugarcane",
    r"Transformation\Bioethanol Production\Processes\Molasses",
]

OUTPUT_FUELS = {
    r"Transformation\Biodiesel Production\Processes\FAME Biodiesel":  "Biodiesel",
    r"Transformation\Biodiesel Production\Processes\CME Biodiesel":   "Biodiesel",
    r"Transformation\Biodiesel Production\Processes\POME Biodiesel":  "Biodiesel",
    r"Transformation\Bioethanol Production\Processes\Corn Ethanol":   "Ethanol",
    r"Transformation\Bioethanol Production\Processes\Cassava":        "Ethanol",
    r"Transformation\Bioethanol Production\Processes\Sugarcane":      "Ethanol",
    r"Transformation\Bioethanol Production\Processes\Molasses":       "Ethanol",
}

ASEAN_10 = [
    "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia",
    "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam",
]
ALL_11 = ASEAN_10 + ["Timor Leste"]

ZERO_ADD = (
    "Add(2025, 0, 2030, 0, 2035, 0, 2040, 0, 2045, 0, 2050, 0, 2055, 0, 2060, 0)"
)

FIELDS = [
    "ams", "branch", "variable", "expression", "unit",
    "fuel", "source", "note", "src_csv", "domain", "data_confidence",
]


def main() -> None:
    src_rows = list(csv.DictReader(SRC.open(encoding="utf-8")))

    # Build a lookup of (ams, branch) -> source row, scoped to Max Cap on
    # the 7 processes. Source CSV already carries curve-preserving Add.
    src_lookup: dict[tuple[str, str], dict] = {}
    for r in src_rows:
        if r["variable"] != "Maximum Capacity":
            continue
        if r["branch"] not in PROCESSES:
            continue
        src_lookup[(r["ams"], r["branch"])] = r

    patch_rows = []
    missing_asean = []
    for branch in PROCESSES:
        for ams in ALL_11:
            if ams == "Timor Leste":
                expression = ZERO_ADD
                src_meta = {}
                note = (
                    "Issue 5 Timor-Leste — author left at 'Unlimited' / "
                    "'RegionValue(...)' default. Bounding at 0 (no Timor "
                    "Leste biofuel production assumed)."
                )
                source_field = "patch 2026-04-30"
                domain = "max_capacity"
                conf = "High"
            else:
                src = src_lookup.get((ams, branch))
                if src is None:
                    missing_asean.append((ams, branch))
                    continue
                expression = src["expression"]
                note = (
                    "Issue 5 fix — curve-preserving Add (deltas) "
                    "overwriting team's mechanical Interp->Add rename "
                    "(absolute values). Reconstructs the same capacity "
                    "schedule at every milestone year using incremental "
                    "additions (the conventional LEAP Add() semantic)."
                )
                source_field = src.get("source", "") or "patch 2026-04-30"
                domain = src.get("domain", "") or "max_capacity"
                conf = src.get("data_confidence", "") or "Medium"

            patch_rows.append({
                "ams": ams,
                "branch": branch,
                "variable": "Maximum Capacity",
                "expression": expression,
                "unit": "Million Tonnes/yr",
                "fuel": OUTPUT_FUELS[branch],
                "source": source_field,
                "note": note,
                "src_csv": "canonical_patch_2026_04_30.csv",
                "domain": domain,
                "data_confidence": conf,
            })

    # ----- Issue 6: Sequestered CO2 externality cost = 0 -----
    # NEMO post-patch sqlite analysis (2026-04-30) showed CCS unbounded-
    # profit risk: 4 CCS techs (SMR with CCS, Coal Gasification w/ CCS,
    # Biomass Gasification w/ CCS, Production from Hydrogen) carry massive
    # negative EmissionActivityRatio for E407 (Sequestered CO2) plus a
    # tiny negative EmissionsPenalty, with no capacity / activity upper
    # bound. CPLEX flags this as INFEASIBLE (column 'x435004').
    #
    # The penalty's source: `Effects\Sequestered Carbon Dioxide` ->
    # `Externality Cost` = `-13.59 * ConvUnits(2023 usd, 2020 usd) ?
    # Chmielniak et al. (2024)` — a sequestration reward configured by
    # the team. Clearing to 0 removes the unbounded incentive.
    EFFECT_PATH = r"Effects\Sequestered Carbon Dioxide"
    for ams in ["Base Template"] + ALL_11:
        patch_rows.append({
            "ams": ams,
            "branch": EFFECT_PATH,
            "variable": "Externality Cost",
            "expression": "0",
            "unit": "",
            "fuel": "",
            "source": "patch 2026-04-30",
            "note": "Issue 6 (NEMO infeas, post-Issue-1 surface) — clear "
                    "negative externality cost on Sequestered CO2 to remove "
                    "CCS unbounded-profit direction. Was: -13.59 * "
                    "ConvUnits(2023 usd, 2020 usd) per Chmielniak et al. "
                    "(2024). Re-introduce later once Max Cap bounds are "
                    "set on the 4 CCS techs (SMR/Coal Gas/Biomass Gas/"
                    "Hydrogen Methanol).",
            "src_csv": "canonical_patch_2026_04_30.csv",
            "domain": "externality_cost",
            "data_confidence": "High",
        })

    # ----- Issue 1: Brunei solar Minimum Utilization = 0 -----
    # Probe (2026-04-30) showed each of the 3 Brunei solar Process branches
    # has `Minimum Utilization.Expression = 'Maximum Availability'`, which
    # forces must-run dispatch. Variable renewables should be curtailable —
    # clear the must-run by setting Minimum Utilization to 0.
    SOLAR_BRANCHES = [
        r"Transformation\Centralized Electricity Generation\Processes\Solar PV",
        # Solar PV Rooftop lives under Distributed Electricity Generation
        # (rooftop = distributed). Team's report listed it under Centralized
        # — that's the LEAP-wrong path; tree_paths.csv confirms Distributed.
        r"Transformation\Distributed Electricity Generation\Processes\Solar PV Rooftop",
        r"Transformation\Centralized Electricity Generation\Processes\Solar Floating",
    ]
    for branch in SOLAR_BRANCHES:
        patch_rows.append({
            "ams": "Brunei",
            "branch": branch,
            "variable": "Minimum Utilization",
            "expression": "0",
            "unit": "",
            "fuel": "Electricity",
            "source": "patch 2026-04-30",
            "note": "Issue 1 (NEMO infeas) — Min Utilization was bound to "
                    "Maximum Availability (must-run constraint). Variable "
                    "renewables should be curtailable; clear to 0. The "
                    "Brunei_Solar Availability YearlyShape carries floating-"
                    "point leak (~7e-5) at Wet:Hr 7 / Dry:Hr 7 that NEMO "
                    "exports as MinimumUtilization > AvailabilityFactor.",
            "src_csv": "canonical_patch_2026_04_30.csv",
            "domain": "min_utilization",
            "data_confidence": "High",
        })

    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(patch_rows)

    print(f"wrote {OUT.name}  ({len(patch_rows)} rows)")
    print()
    from collections import Counter
    by_region = Counter(r["ams"] for r in patch_rows)
    by_branch = Counter(r["branch"].split("\\")[-1] for r in patch_rows)
    print(f"by region: {dict(sorted(by_region.items()))}")
    print(f"by branch: {dict(by_branch)}")
    if missing_asean:
        print()
        print(f"WARNING — {len(missing_asean)} ASEAN rows not found in source CSV:")
        for ams, b in missing_asean:
            print(f"  {ams:<14}  {b}")


if __name__ == "__main__":
    main()
