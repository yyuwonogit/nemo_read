"""Probe LEAP for the two NEMO-team-reported infeasibilities.

Round 3: only .Expression reads, no .Value() (which fires LEAP modal
popups). Variable name corrected: 'Minimum Utilization' (not 'Minimum
Utilization Factor' as the team's report had it).
"""
from __future__ import annotations

from pathlib import Path

from nemo_read._leap_com import (
    dispatch_leap, iterate_variables_safe, safe_expression,
)


OUT = Path(__file__).parent / "_nemo_infeas_findings.txt"


def log(msg: str = "") -> None:
    print(msg, flush=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def read_expr(branch, varname: str) -> str:
    try:
        var = branch.Variable(varname)
    except Exception as e:
        return f"<no var: {e}>"
    if var is None:
        return "<None>"
    return safe_expression(var) or ""


def main() -> None:
    OUT.write_text("", encoding="utf-8")
    leap = dispatch_leap()
    log(f"=== ENV ===")
    log(f"Area:     {leap.ActiveArea.Name!r}")
    log(f"Scenario: {leap.ActiveScenario.Name!r}")
    log("")

    # =========================================================================
    # ISSUE 1 — Brunei solar Min Utilization (per region; expression-only read)
    # =========================================================================
    log("=" * 72)
    log("ISSUE 1 — Brunei solar Minimum Utilization (Expression read only)")
    log("=" * 72)
    SOLAR_BRANCHES = [
        r"Transformation\Centralized Electricity Generation\Processes\Solar PV",
        r"Transformation\Centralized Electricity Generation\Processes\Solar PV Rooftop",
        r"Transformation\Centralized Electricity Generation\Processes\Solar Floating",
    ]
    leap.ActiveRegion = "Brunei"
    log(f"ActiveRegion = {leap.ActiveRegion.Name!r}")
    log("")

    for branch_path in SOLAR_BRANCHES:
        log(f"--- {branch_path} ---")
        try:
            br = leap.Branches(branch_path)
        except Exception as e:
            log(f"  ERROR getting branch: {e}")
            continue

        # Read only the variables we care about, by exact name
        for vname in ("Minimum Utilization",
                      "Maximum Availability",
                      "Historical Capacity Factor"):
            expr = read_expr(br, vname)
            log(f"  {vname}.Expression = {expr[:200]!r}")
        log("")

    # If Min Utilization Expression references a YearlyShape, we want to
    # inspect that shape directly. Try common LEAP shape access patterns.
    log("--- exploring YearlyShape access (informational) ---")
    try:
        shapes_count = leap.Shapes.Count
        log(f"  leap.Shapes.Count = {shapes_count}")
        # Look for Brunei-relevant shapes
        for i in range(1, min(shapes_count + 1, 200)):
            try:
                s = leap.Shapes.Item(i)
                name = s.Name
                if "brunei" in name.lower() or "solar" in name.lower():
                    log(f"    shape #{i}: {name!r}")
            except Exception:
                continue
    except Exception as e:
        log(f"  leap.Shapes inaccessible: {e}")
    log("")

    # =========================================================================
    # ISSUE 2 — Demand branches for the 4 bioenergy fuels
    # =========================================================================
    log("=" * 72)
    log("ISSUE 2 — leftover Demand branches for bioenergy fuels")
    log("=" * 72)
    DEMAND_BRANCHES = [
        r"Demand\Non Energy Biomass\Palm Oil",
        r"Demand\Non Energy Biomass\Coconut Oil",
        r"Demand\Non Energy Biomass\Cassava",
        r"Demand\Non Energy Biomass\Sugarcane",
    ]
    AFFECTED = {
        "Palm Oil":    ["Cambodia", "Indonesia", "Malaysia", "Philippines", "Thailand", "Vietnam"],
        "Coconut Oil": ["Indonesia", "Malaysia", "Philippines", "Thailand", "Vietnam"],
        "Cassava":     ["Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar",
                        "Philippines", "Thailand", "Vietnam"],
        "Sugarcane":   ["Malaysia", "Myanmar", "Thailand", "Vietnam"],
    }

    for branch_path in DEMAND_BRANCHES:
        log(f"--- {branch_path} ---")
        try:
            br = leap.Branches(branch_path)
        except Exception as e:
            log(f"  ERROR getting branch: {e}")
            continue
        try:
            log(f"  ID: {br.ID}")
        except Exception:
            pass

        # Enumerate all vars first
        try:
            var_names = [n for _, n, _ in iterate_variables_safe(
                br, deadline_seconds=10.0, fetch_expression=False)]
            log(f"  variables ({len(var_names)}): {var_names}")
        except Exception as e:
            log(f"  iterate_variables_safe ERROR: {e}")
            var_names = []

        fuel = branch_path.split("\\")[-1]
        # Read demand-relevant vars per affected region
        for vname in ("Activity Level", "Energy Intensity",
                      "Total Annual Demand", "Final Energy Demand"):
            if var_names and vname not in var_names:
                continue
            log(f"  {vname}:")
            for region in AFFECTED.get(fuel, []):
                try:
                    leap.ActiveRegion = region
                except Exception as e:
                    log(f"    [{region:<14}] set ActiveRegion ERROR: {e}")
                    continue
                expr = read_expr(br, vname)
                log(f"    [{region:<14}] {expr!r}"[:160])
        log("")

    log("")
    log("=== DONE ===")


if __name__ == "__main__":
    main()
