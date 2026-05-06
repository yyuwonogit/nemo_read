"""Pull current Feedstock Fuel Share state for every biofuel process's
Feedstock Fuels children × every LEAP region. Writes a CSV the team can
review to decide what 100% rule to apply.

Run with LEAP open on aeo9_v0.33_bak.
"""
from __future__ import annotations

import csv
from pathlib import Path

from nemo_read._leap_com import dispatch_leap, safe_expression


OUT_CSV = Path(__file__).parent / "feedstock_share_state.csv"
TREE_PATHS_CSV = (Path.home() / "Documents/LEAP Areas/aeo9_v0.33_bak"
                  / "NEMO_25.leap_export/tree_paths.csv")

PROCESSES = [
    r"Transformation\Biodiesel Production\Processes\FAME Biodiesel",
    r"Transformation\Biodiesel Production\Processes\CME Biodiesel",
    r"Transformation\Biodiesel Production\Processes\POME Biodiesel",
    r"Transformation\Bioethanol Production\Processes\Corn Ethanol",
    r"Transformation\Bioethanol Production\Processes\Cassava",
    r"Transformation\Bioethanol Production\Processes\Sugarcane",
    r"Transformation\Bioethanol Production\Processes\Molasses",
]


def main() -> None:
    leap = dispatch_leap()
    print(f"Area:     {leap.ActiveArea.Name!r}")

    with TREE_PATHS_CSV.open(encoding="utf-8") as f:
        known = {row["branch_full_name"] for row in csv.DictReader(f)}
    regions = [r.Name for r in leap.Regions]

    rows = []
    for process in PROCESSES:
        feedstock_parent = process + "\\Feedstock Fuels"
        prefix = feedstock_parent + "\\"
        children = sorted(p for p in known
                          if p.startswith(prefix)
                          and p.count("\\") == feedstock_parent.count("\\") + 1)
        process_leaf = process.split("\\")[-1]
        if not children:
            print(f"  {process_leaf}: no Feedstock Fuels children in tree")
            continue
        print(f"  {process_leaf}: {len(children)} feedstock(s) — "
              f"{[c.split(chr(92))[-1] for c in children]}")

        for ch_path in children:
            try:
                ch = leap.Branches(ch_path)
            except Exception as e:
                print(f"    skip {ch_path}: {e}")
                continue
            feedstock_leaf = ch_path.split("\\")[-1]
            for region in regions:
                try:
                    leap.ActiveRegion = region
                    var = ch.Variable("Feedstock Fuel Share")
                    expr = safe_expression(var) or ""
                except Exception as e:
                    expr = f"<err: {e}>"
                rows.append({
                    "process": process_leaf,
                    "feedstock": feedstock_leaf,
                    "region": region,
                    "current_share": expr,
                    "branch_path": ch_path,
                })

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "process", "feedstock", "region", "current_share", "branch_path",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwrote {OUT_CSV}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
