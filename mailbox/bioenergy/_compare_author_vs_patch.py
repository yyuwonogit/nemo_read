"""Compare the new LEAP area's author-applied fixes vs our patch CSV.

Probes the same 5 issues against `aeo9_v0.33_yy_rev1` and writes a
side-by-side findings file. Uses the locally-cached tree_paths.csv if
present (and the area path matches), else falls back to a fresh probe.
"""
from __future__ import annotations

import csv
from pathlib import Path

from nemo_read._leap_com import dispatch_leap, safe_expression


OUT = Path(__file__).parent / "_author_vs_patch_findings.txt"
PATCH_CSV = Path(__file__).parent / "canonical_patch_2026_04_30.csv"


def log(msg: str = "") -> None:
    print(msg, flush=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")


TARGET_SCENARIO = "Regional Aspiration Scenario"
TARGET_AREA = "aeo9_v0.33_yy_rev1"


def main() -> None:
    OUT.write_text("", encoding="utf-8")
    leap = dispatch_leap()
    area_before = leap.ActiveArea.Name
    scenario_before = leap.ActiveScenario.Name
    log(f"=== ENV (before scenario switch) ===")
    log(f"Area:     {area_before!r}")
    log(f"Scenario: {scenario_before!r}")

    # Switch to RAS, then verify area didn't drift (Gotcha #1 in BROCHURE).
    if scenario_before != TARGET_SCENARIO:
        try:
            leap.ActiveScenario = TARGET_SCENARIO
        except Exception as e:
            log(f"FATAL: could not set ActiveScenario={TARGET_SCENARIO!r}: {e}")
            return
        area_after = leap.ActiveArea.Name
        scenario_after = leap.ActiveScenario.Name
        if area_after != area_before:
            log(f"FATAL: scenario switch JUMPED area "
                f"({area_before!r} -> {area_after!r}). Aborting.")
            return
        if area_after != TARGET_AREA:
            log(f"WARNING: ActiveArea is {area_after!r}, expected "
                f"{TARGET_AREA!r}. Continuing anyway.")
        log(f"\n=== ENV (after scenario switch) ===")
        log(f"Area:     {area_after!r}")
        log(f"Scenario: {scenario_after!r}")
    log("")

    # Build set of regions
    regions = [r.Name for r in leap.Regions]
    log(f"regions ({len(regions)}): {regions}")
    log("")

    # Load patch CSV — used as the "expected" reference
    expected: dict[tuple[str, str, str], dict] = {}
    with PATCH_CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            expected[(r["ams"], r["branch"], r["variable"])] = r
    log(f"patch CSV: {len(expected)} expected (region, branch, variable) entries")
    log("")

    def read_expr(branch_path: str, varname: str, region: str) -> str:
        try:
            leap.ActiveRegion = region
            br = leap.Branches(branch_path)
            var = br.Variable(varname)
            return safe_expression(var) or ""
        except Exception as e:
            return f"<err: {e}>"

    def compare(ams: str, branch: str, variable: str) -> tuple[str, str, str]:
        """Return (author_expr, patch_expr, verdict)."""
        author_expr = read_expr(branch, variable, ams)
        patch_row = expected.get((ams, branch, variable))
        patch_expr = patch_row["expression"] if patch_row else "<not in patch>"
        # Verdict
        if patch_expr == "<not in patch>":
            verdict = "patch silent"
        elif author_expr.strip() == patch_expr.strip():
            verdict = "MATCH"
        elif (author_expr.replace(",", "").replace(" ", "").lower()
              == patch_expr.replace(",", "").replace(" ", "").lower()):
            verdict = "match (whitespace)"
        else:
            verdict = "DIFFER"
        return author_expr, patch_expr, verdict

    # ----------- Issue 2 — Corn Ethanol Feedstock Fuel Share -----------
    log("=== ISSUE 2: Corn Ethanol Feedstock Fuel Share ===")
    branch = (r"Transformation\Bioethanol Production\Processes"
              r"\Corn Ethanol\Feedstock Fuels\Corn")
    for region in regions:
        a, p, v = compare(region, branch, "Feedstock Fuel Share")
        log(f"  [{region:<14}] author={a!r:<25} patch={p!r:<8}  {v}")

    # ----------- Issue 3 — Corn Ethanol Fuel Cost -----------
    log("")
    log("=== ISSUE 3: Corn Ethanol Fuel Cost ===")
    for region in regions:
        a, p, v = compare(region, branch, "Fuel Cost")
        log(f"  [{region:<14}]")
        log(f"     author = {a!r}")
        log(f"     patch  = {p!r}")
        log(f"     -> {v}")

    # ----------- Issue 4 — FAME Capital Cost -----------
    log("")
    log("=== ISSUE 4: FAME Biodiesel Capital Cost ===")
    fame = r"Transformation\Biodiesel Production\Processes\FAME Biodiesel"
    for region in regions:
        a, p, v = compare(region, fame, "Capital Cost")
        log(f"  [{region:<14}]")
        log(f"     author = {a!r}")
        log(f"     patch  = {p!r}")
        log(f"     -> {v}")

    # ----------- Issue 5 — biodiesel/bioethanol Max Cap (Interp -> Add) -----------
    log("")
    log("=== ISSUE 5: Maximum Capacity (Interp -> Add) ===")
    log("Patch silent here — the Interp->Add change is in source CSV, not patch.")
    log("Reporting current LEAP form for awareness.")
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
        for region in regions:
            expr = read_expr(path, "Maximum Capacity", region)
            tag = ""
            if isinstance(expr, str):
                if expr.startswith("Interp"):
                    tag = " <- still INTERP"
                elif expr.startswith("Add"):
                    tag = " (Add — author patched)"
                elif expr in ("Unlimited", "RegionValue") or expr.startswith("RegionValue"):
                    tag = " (LEAP default / RegionValue)"
            log(f"    [{region:<14}] {expr!r}{tag}")

    # ----------- Issue 1 — CME / Coconut Oil emission factors -----------
    log("")
    log("=== ISSUE 1: CME / Coconut Oil emission factors ===")
    log("Patch silent here — Issue 1 deferred pending team clarification.")
    log("Reporting current LEAP state for awareness.")
    coco = (r"Transformation\Biodiesel Production\Processes"
            r"\CME Biodiesel\Feedstock Fuels\Coconut Oil")
    for vname in ("CO2 (process)", "CH4 (process)", "N2O (process)",
                  "NH3 (process)", "NOx (process)", "SO2 (process)",
                  "NMVOC (process)"):
        log(f"  --- {vname} ---")
        for region in regions:
            expr = read_expr(coco, vname, region)
            log(f"    [{region:<14}] {expr!r}")

    log("")
    log("=== DONE ===")


if __name__ == "__main__":
    main()
