"""Focused probe: enumerate variables on Effects\Sequestered Carbon Dioxide
and Key\Emission Externality Costs\Carbon Dioxide to find where the
penalty / externality cost is set."""
from pathlib import Path

from nemo_read._leap_com import (
    dispatch_leap, iterate_variables_safe, safe_expression,
)


OUT = Path(__file__).parent / "_e407_penalty_findings.txt"


def log(msg: str = "") -> None:
    print(msg, flush=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main() -> None:
    leap = dispatch_leap()
    log("")
    log("=" * 72)
    log("STEP 5 — focused probe of candidate branches")
    log("=" * 72)
    log(f"Area:     {leap.ActiveArea.Name!r}")
    log(f"Scenario: {leap.ActiveScenario.Name!r}")

    CANDIDATES = [
        r"Effects\Sequestered Carbon Dioxide",
        r"Effects\Carbon Dioxide",
        r"Key\Emission Externality Costs\Carbon Dioxide",
        r"Key\Emission Externality Costs",
    ]

    regions = [r.Name for r in leap.Regions]

    for path in CANDIDATES:
        log(f"\n--- {path} ---")
        try:
            br = leap.Branches(path)
        except Exception as e:
            log(f"  NOT FOUND: {e}")
            continue
        try:
            log(f"  ID: {br.ID}")
            log(f"  FullName: {br.FullName!r}")
        except Exception:
            pass

        # Enumerate variables
        try:
            var_names = [n for _, n, _ in iterate_variables_safe(
                br, deadline_seconds=15.0, fetch_expression=False)]
            log(f"  variables ({len(var_names)}):")
            for v in var_names:
                log(f"    - {v}")
        except Exception as e:
            log(f"  iterate_variables_safe ERROR: {e}")
            var_names = []

        # For each cost/externality-looking variable, read .Expression per region
        cost_vars = [v for v in var_names if any(
            tok in v.lower() for tok in (
                "cost", "penalty", "externality", "tax", "value"
            ))]
        if cost_vars:
            log(f"  -- cost/penalty-like variables: {cost_vars} --")
        for vname in cost_vars:
            log(f"  {vname} per region:")
            for region in regions[:6]:  # first 6 regions only
                try:
                    leap.ActiveRegion = region
                    var = br.Variable(vname)
                    expr = safe_expression(var) or ""
                    log(f"    [{region:<14}] {expr!r}"[:160])
                except Exception as e:
                    log(f"    [{region:<14}] ERROR {e}")

    log("")
    log("=== DONE ===")


if __name__ == "__main__":
    main()
