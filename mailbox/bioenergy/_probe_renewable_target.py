"""Find the LEAP branches that define the
RenewableCapacityTarget__NEMOcc and ASEANRenewableCapacityTarget__NEMOcc
NEMOcc tables. These come from LEAP User Variables — locate them so the
user can set values to 0 directly via the LEAP UI."""
from pathlib import Path
import csv

from nemo_read._leap_com import (
    dispatch_leap, iterate_variables_safe, safe_expression,
)


OUT = Path(__file__).parent / "_renewable_target_findings.txt"
TREE_PATHS = (Path.home()
              / "Documents/LEAP Areas/aeo9_v0.33_yy_rev1"
              / "NEMO_25.leap_export/tree_paths.csv")


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

    # 1. Search tree paths for "Renewable" / "Target" / "RE Capacity"
    log("=" * 72)
    log("STEP 1: tree paths matching Renewable / Target")
    log("=" * 72)
    if TREE_PATHS.exists():
        with TREE_PATHS.open(encoding="utf-8") as f:
            paths = [r["branch_full_name"] for r in csv.DictReader(f)]
        log(f"  total tree paths: {len(paths)}")
        for kw in ("renewable capacity target", "ASEAN", "RE Target",
                   "Renewable Target", "Capacity Target"):
            matches = sorted({p for p in paths if kw.lower() in p.lower()})
            if matches:
                log(f"\n  -- containing {kw!r} ({len(matches)}) --")
                for m in matches[:30]:
                    log(f"    {m}")
    else:
        log(f"  tree_paths.csv not found at {TREE_PATHS}")
    log("")

    # 2. Common LEAP locations for User Variables
    log("=" * 72)
    log("STEP 2: probe candidate Key/Other branches")
    log("=" * 72)
    CANDIDATES = [
        r"Key",
        r"Key\Renewable Energy",
        r"Key\Net Zero Measures",
        r"Key\Targets",
        r"Key\Renewable Capacity Target",
        r"Key\ASEAN Renewable Capacity Target",
    ]
    for path in CANDIDATES:
        try:
            br = leap.Branches(path)
            log(f"\n  {path}  -> exists (ID={br.ID})")
            try:
                kids = br.Branches
                n = kids.Count
                log(f"    {n} children")
                for i in range(1, min(n + 1, 50)):
                    try:
                        c = kids.Item(i)
                        cname = c.FullName
                        log(f"      child: {cname}")
                    except Exception:
                        continue
            except Exception as e:
                log(f"    Branches inaccessible: {e}")
        except Exception as e:
            log(f"  {path}  NOT FOUND: {e}")

    # 3. Read nemocc_sources.csv if it's been exported
    log("")
    log("=" * 72)
    log("STEP 3: nemocc_sources.csv (if exported)")
    log("=" * 72)
    nsrc = (Path.home() / "Documents/LEAP Areas/aeo9_v0.33_yy_rev1"
            / "NEMO_25.leap_export/nemocc_sources.csv")
    if nsrc.exists():
        with nsrc.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if "Renewable" in row.get("table_name", "") or "ASEAN" in row.get("table_name", ""):
                    log(f"  {row}")
    else:
        log(f"  not found: {nsrc}")

    # 4. Find LEAP UserVariables programmatically
    log("")
    log("=" * 72)
    log("STEP 4: LEAP User Variables list")
    log("=" * 72)
    try:
        uvars = leap.UserVariables
        cnt = uvars.Count
        log(f"  leap.UserVariables.Count = {cnt}")
        for i in range(1, cnt + 1):
            try:
                uv = uvars.Item(i)
                name = uv.Name
                # Most LEAP UserVariables have these properties
                try:
                    branch_full = uv.Branch.FullName
                except Exception:
                    branch_full = "<no Branch>"
                log(f"    #{i}  Name={name!r}  Branch={branch_full!r}")
            except Exception as ex:
                log(f"    #{i}  ERR: {ex}")
    except Exception as e:
        log(f"  leap.UserVariables not exposed via COM: {e}")

    log("")
    log("=== DONE ===")


if __name__ == "__main__":
    main()
