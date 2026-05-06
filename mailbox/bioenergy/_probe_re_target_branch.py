"""Enumerate User Variables on Key\\Region Group RE Targets\\ASEAN
All Regions Electricity to find where RenewableCapacityTarget and
ASEANRenewableCapacityTarget user variables are stored."""
from pathlib import Path

from nemo_read._leap_com import (
    dispatch_leap, iterate_variables_safe, safe_expression,
)


OUT = Path(__file__).parent / "_re_target_branch_findings.txt"


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
        r"Key\Region Group RE Targets",
        r"Key\Region Group RE Targets\ASEAN All Regions Electricity",
    ]

    regions = [r.Name for r in leap.Regions]

    for path in BRANCHES:
        log(f"\n--- {path} ---")
        try:
            br = leap.Branches(path)
            log(f"  ID: {br.ID}")
            log(f"  FullName: {br.FullName!r}")
        except Exception as e:
            log(f"  NOT FOUND: {e}")
            continue

        # Enumerate ALL variables (user variables included)
        try:
            var_names = [n for _, n, _ in iterate_variables_safe(
                br, deadline_seconds=15.0, fetch_expression=False)]
            log(f"  variables ({len(var_names)}):")
            for v in var_names:
                log(f"    - {v}")
        except Exception as e:
            log(f"  iterate_variables_safe ERROR: {e}")
            var_names = []

        # For RE-target-related vars, read expression per region
        for vname in var_names:
            if any(kw in vname.lower() for kw in ("target", "capacity", "renewable", "share")):
                log(f"\n  {vname} per region:")
                for region in regions:
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
