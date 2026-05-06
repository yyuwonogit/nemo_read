"""Targeted probe — issues 1-5 (2026-04-29). Skips the LeapTreeCache
fullname-build step (slow + hung once) by relying on the already-saved
`tree_paths.csv` to confirm path existence offline, then calling
`leap.Branches(<fullname>)` directly only for verified paths.

Writes findings to _team_issues_findings.txt as it goes.
"""
from __future__ import annotations

import csv
from pathlib import Path

from nemo_read._leap_com import dispatch_leap, safe_expression


OUT = Path(__file__).parent / "_team_issues_findings.txt"
TREE_PATHS_CSV = (Path.home()
                  / "Documents/LEAP Areas/aeo9_v0.33_bak"
                  / "NEMO_25.leap_export/tree_paths.csv")


def log(msg: str = "") -> None:
    print(msg, flush=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


def main() -> None:
    OUT.write_text("", encoding="utf-8")

    leap = dispatch_leap()
    area = leap.ActiveArea.Name
    log("=== ENV ===")
    log(f"Area:     {area!r}")
    log(f"Scenario: {leap.ActiveScenario.Name!r}")

    # Load known paths from prior probe — avoid the slow fresh-cache build.
    if not TREE_PATHS_CSV.exists():
        log(f"\nERROR: {TREE_PATHS_CSV} not found — run nemo_read-leap-units once first")
        return
    with TREE_PATHS_CSV.open(encoding="utf-8") as f:
        known_paths = {row["branch_full_name"] for row in csv.DictReader(f)}
    log(f"\nknown paths from cache: {len(known_paths)}")

    # Region list (faster than full Branches iter)
    regions = []
    for r in leap.Regions:
        regions.append(r.Name)
    log(f"regions: {regions}")

    def get_branch(fullname: str):
        """Return live LEAP branch for a known-existing path. None if not in tree."""
        if fullname not in known_paths:
            return None
        try:
            return leap.Branches(fullname)
        except Exception as e:
            log(f"  Branches({fullname!r}) failed: {e}")
            return None

    def expr_per_region(branch, varname: str, label: str) -> None:
        """Read varname.Expression per region; one log line each."""
        for region in regions:
            try:
                leap.ActiveRegion = region
                var = branch.Variable(varname)
                expr = safe_expression(var) or ""
            except Exception as e:
                expr = f"<err: {e}>"
            log(f"    [{region:<14}] {label:<30}  {expr!r}")

    # ============================================================
    # ISSUE 1: CME / Coconut Oil emission factors — current LEAP state
    # ============================================================
    log("")
    log("=== ISSUE 1: CME / Coconut Oil emission factors (per region) ===")
    issue1_path = (r"Transformation\Biodiesel Production\Processes"
                   r"\CME Biodiesel\Feedstock Fuels\Coconut Oil")
    branch = get_branch(issue1_path)
    if branch is None:
        log(f"  NOT IN TREE: {issue1_path}")
    else:
        for vname in ("CO2 (process)", "CH4 (process)", "N2O (process)",
                      "NH3 (process)", "NOx (process)", "SO2 (process)",
                      "NMVOC (process)"):
            expr_per_region(branch, vname, vname)

    # ============================================================
    # ISSUE 2: Corn Ethanol Feedstock Fuel Shares (sum to 100%?)
    # ============================================================
    log("")
    log("=== ISSUE 2: Corn Ethanol Feedstock Fuel Shares ===")
    parent_path = (r"Transformation\Bioethanol Production\Processes"
                   r"\Corn Ethanol\Feedstock Fuels")
    # Find children of parent_path in known_paths
    prefix = parent_path + "\\"
    children = [p for p in known_paths
                if p.startswith(prefix) and p.count("\\") == parent_path.count("\\") + 1]
    log(f"  {len(children)} children of {parent_path}:")
    for ch_path in sorted(children):
        leaf = ch_path.split("\\")[-1]
        ch = get_branch(ch_path)
        if ch is None:
            continue
        expr_per_region(ch, "Feedstock Fuel Share", f"{leaf} Share")

    # ============================================================
    # ISSUE 3: Corn Ethanol Fuel Cost (per region)
    # ============================================================
    log("")
    log("=== ISSUE 3: Corn Ethanol\\Feedstock Fuels\\Corn Fuel Cost ===")
    issue3_path = (r"Transformation\Bioethanol Production\Processes"
                   r"\Corn Ethanol\Feedstock Fuels\Corn")
    branch = get_branch(issue3_path)
    if branch is None:
        log(f"  NOT IN TREE: {issue3_path}")
    else:
        expr_per_region(branch, "Fuel Cost", "Fuel Cost")

    # ============================================================
    # ISSUE 4: FAME Biodiesel Capital Cost (per region)
    # ============================================================
    log("")
    log("=== ISSUE 4: FAME Biodiesel Capital Cost ===")
    issue4_path = (r"Transformation\Biodiesel Production\Processes\FAME Biodiesel")
    branch = get_branch(issue4_path)
    if branch is None:
        log(f"  NOT IN TREE: {issue4_path}")
    else:
        expr_per_region(branch, "Capital Cost", "Capital Cost")

    # ============================================================
    # ISSUE 5: Maximum Capacity expressions (Interp -> Add)
    # ============================================================
    log("")
    log("=== ISSUE 5: Maximum Capacity expressions on biodiesel/bioethanol ===")
    issue5_branches = [
        r"Transformation\Biodiesel Production\Processes\FAME Biodiesel",
        r"Transformation\Biodiesel Production\Processes\CME Biodiesel",
        r"Transformation\Biodiesel Production\Processes\POME Biodiesel",
        r"Transformation\Bioethanol Production\Processes\Corn Ethanol",
        r"Transformation\Bioethanol Production\Processes\Cassava",
        r"Transformation\Bioethanol Production\Processes\Sugarcane",
        r"Transformation\Bioethanol Production\Processes\Molasses",
    ]
    for path in issue5_branches:
        leaf = path.split("\\")[-1]
        log(f"  --- {leaf} ---")
        branch = get_branch(path)
        if branch is None:
            log(f"    NOT IN TREE")
            continue
        for region in regions:
            try:
                leap.ActiveRegion = region
                var = branch.Variable("Maximum Capacity")
                expr = safe_expression(var) or ""
            except Exception as e:
                expr = f"<err: {e}>"
            tag = ""
            if isinstance(expr, str):
                if expr.startswith("Interp"):
                    tag = "  <- INTERP"
                elif expr.startswith("Add"):
                    tag = "  (Add already)"
            log(f"    [{region:<14}] {expr!r}{tag}")

    log("")
    log("=== DONE ===")


if __name__ == "__main__":
    main()
