"""Probe the 4 leftover Demand branches RIGHT NOW (post user 'hide').
Check Activity Level + Energy Load Shape per region."""
from pathlib import Path
from nemo_read._leap_com import (
    dispatch_leap, iterate_variables_safe, safe_expression,
)


OUT = Path(__file__).parent / "_demand_branches_now.txt"


def log(msg: str = "") -> None:
    print(msg, flush=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main() -> None:
    OUT.write_text("", encoding="utf-8")
    leap = dispatch_leap()
    log(f"=== ENV ===")
    log(f"Area:     {leap.ActiveArea.Name!r}")
    log(f"Scenario: {leap.ActiveScenario.Name!r}")
    log("")

    BRANCHES = [
        (r"Demand\Non Energy Biomass\Palm Oil",
         ["Cambodia", "Indonesia", "Malaysia", "Philippines", "Thailand", "Vietnam"]),
        (r"Demand\Non Energy Biomass\Coconut Oil",
         ["Indonesia", "Malaysia", "Philippines", "Thailand", "Vietnam"]),
        (r"Demand\Non Energy Biomass\Cassava",
         ["Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar",
          "Philippines", "Thailand", "Vietnam"]),
        (r"Demand\Non Energy Biomass\Sugarcane",
         ["Malaysia", "Myanmar", "Thailand", "Vietnam"]),
    ]

    for path, regions in BRANCHES:
        log(f"\n--- {path} ---")
        try:
            br = leap.Branches(path)
            log(f"  ID: {br.ID}")
            log(f"  FullName: {br.FullName!r}")
        except Exception as e:
            log(f"  NOT FOUND: {e}")
            continue

        # Read each interesting variable per region
        for varname in ("Activity Level", "Energy Load Shape", "Power Load Shape",
                        "Final Energy Intensity"):
            log(f"  {varname}:")
            for region in regions:
                try:
                    leap.ActiveRegion = region
                    var = br.Variable(varname)
                    expr = safe_expression(var) or ""
                    log(f"    [{region:<14}] {expr!r}"[:160])
                except Exception as e:
                    log(f"    [{region:<14}] ERROR {e}")

    log("")
    log("=== DONE ===")


if __name__ == "__main__":
    main()
