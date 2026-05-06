"""Verify our 2026-04-30 patches actually landed in LEAP."""
from pathlib import Path

from nemo_read._leap_com import dispatch_leap, safe_expression


OUT = Path(__file__).parent / "_verify_patch_findings.txt"


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

    # ----- Issue 1 verification: Brunei solar Min Util = 0 -----
    log("=== ISSUE 1 verify: Brunei solar Minimum Utilization ===")
    leap.ActiveRegion = "Brunei"
    log(f"ActiveRegion = {leap.ActiveRegion.Name!r}")
    SOLAR = [
        r"Transformation\Centralized Electricity Generation\Processes\Solar PV",
        r"Transformation\Distributed Electricity Generation\Processes\Solar PV Rooftop",
        r"Transformation\Centralized Electricity Generation\Processes\Solar Floating",
    ]
    for path in SOLAR:
        try:
            br = leap.Branches(path)
            var = br.Variable("Minimum Utilization")
            expr = safe_expression(var) or ""
        except Exception as e:
            expr = f"<err: {e}>"
        log(f"  {path}")
        log(f"    Minimum Utilization = {expr!r}")
    log("")

    # ----- Issue 2 verification: Demand branches gone? -----
    log("=== ISSUE 2 verify: 4 Demand branches gone? ===")
    DEMAND = [
        r"Demand\Non Energy Biomass\Palm Oil",
        r"Demand\Non Energy Biomass\Coconut Oil",
        r"Demand\Non Energy Biomass\Cassava",
        r"Demand\Non Energy Biomass\Sugarcane",
    ]
    for path in DEMAND:
        try:
            br = leap.Branches(path)
            try:
                bid = br.ID
                fname = br.FullName
                log(f"  STILL EXISTS: {path}  (ID={bid}, FullName={fname!r})")
            except Exception:
                log(f"  ambiguous: {path}  -> branch object returned but ID/FullName unreadable")
        except Exception as e:
            log(f"  GONE (good): {path}  -> {e}")
    log("")

    # ----- Issue 5 spot-check: a few Add expressions -----
    log("=== ISSUE 5 spot-check: a few Max Cap Add expressions ===")
    for region, branch_path, expected_starts in [
        ("Indonesia",  r"Transformation\Biodiesel Production\Processes\FAME Biodiesel", "Add(2025, 16"),
        ("Thailand",   r"Transformation\Bioethanol Production\Processes\Cassava",       "Add(2025, 1.2"),
        ("Timor Leste",r"Transformation\Biodiesel Production\Processes\FAME Biodiesel", "Add(2025, 0"),
    ]:
        try:
            leap.ActiveRegion = region
            br = leap.Branches(branch_path)
            var = br.Variable("Maximum Capacity")
            expr = safe_expression(var) or ""
        except Exception as e:
            expr = f"<err: {e}>"
        ok = "OK" if expr.startswith(expected_starts) else "MISMATCH"
        log(f"  [{region:<12}] {branch_path.split(chr(92))[-1]:<22} {ok}  expr={expr[:80]!r}")

    log("")
    log("=== DONE ===")


if __name__ == "__main__":
    main()
