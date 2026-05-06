"""Probe LEAP to find where the 'Sequestered Carbon Dioxide' emission
penalty (E407 in NEMO) is configured. Write findings to disk."""
from pathlib import Path
import csv

from nemo_read._leap_com import (
    dispatch_leap, iterate_variables_safe, safe_expression,
)


OUT = Path(__file__).parent / "_e407_penalty_findings.txt"
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

    # === Step 1: enumerate Effects (LEAP's emissions list) ===
    log("=== STEP 1: LEAP Effects (emissions) — looking for Sequestered ===")
    try:
        effects = leap.Effects
        cnt = effects.Count
        log(f"  leap.Effects.Count = {cnt}")
        for i in range(1, cnt + 1):
            try:
                e = effects.Item(i)
                name = e.Name
                if "sequester" in name.lower() or "co2" in name.lower():
                    log(f"    #{i}  ID={getattr(e, 'ID', '?')}  Name={name!r}")
            except Exception as ex:
                continue
    except Exception as e:
        log(f"  leap.Effects inaccessible: {e}")
    log("")

    # === Step 2: search tree paths for "Sequestered" / "Carbon" branches ===
    log("=== STEP 2: tree paths matching 'Sequestered' or carbon-penalty patterns ===")
    if TREE_PATHS.exists():
        with TREE_PATHS.open(encoding="utf-8") as f:
            paths = [r["branch_full_name"] for r in csv.DictReader(f)]
        log(f"  tree_paths.csv: {len(paths)} branches")

        keywords = ("sequester", "carbon", "co2", "emission", "penalty", "effects")
        for kw in keywords:
            matches = sorted({p for p in paths if kw in p.lower()})
            if matches and len(matches) <= 50:
                log(f"  -- containing {kw!r} ({len(matches)} hits) --")
                for m in matches[:30]:
                    log(f"    {m}")
            elif matches:
                log(f"  -- containing {kw!r}: {len(matches)} hits (too many to list) --")
    log("")

    # === Step 3: try common LEAP locations for emission penalty ===
    log("=== STEP 3: probing common LEAP branches for E407 penalty ===")
    CANDIDATES = [
        r"Key Assumptions\Carbon Penalty",
        r"Key Assumptions\Emissions Penalty",
        r"Key Assumptions",
        r"Demand\Effects",
        r"Transformation\Effects",
    ]
    for path in CANDIDATES:
        try:
            br = leap.Branches(path)
        except Exception as e:
            log(f"  {path}  -> NOT FOUND: {e}")
            continue
        try:
            kids = br.Branches
            n = kids.Count
            log(f"  {path}  -> exists, {n} child branches")
            for i in range(1, min(n + 1, 30)):
                try:
                    child = kids.Item(i)
                    log(f"    child: {child.FullName!r}")
                except Exception:
                    continue
        except Exception as e:
            log(f"  {path}  -> Branches inaccessible: {e}")
    log("")

    # === Step 4: enumerate top-level branches (root) to find Effects ===
    log("=== STEP 4: top-level branches under root ===")
    try:
        for i in range(1, leap.Branches.Count + 1):
            try:
                b = leap.Branches.Item(i)
                if b.Parent is None or b.Parent.FullName == "":
                    log(f"  top-level: {b.FullName!r}")
            except Exception:
                continue
    except Exception as e:
        log(f"  enumeration error: {e}")
    log("")

    log("=== DONE ===")


if __name__ == "__main__":
    main()
