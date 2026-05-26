"""Probe: enumerate Variables + DataUnitText on Residential lighting,
air conditioning, and refrigeration leaves.

POPUP-SAFE — reads only .Name, .ID, .BranchType on Variables.
DataUnitText is attempted only on branches with BT in {3, 50}
per CLAUDE.md §11.2 to avoid the result-side modal-popup trap.

Outputs a CSV at inject/residential/_residential_branch_map.csv
for direct use as the next sector's authoring spec.

Per CLAUDE.md §A.9: confirms area = aeo9_v0.46 before any reads.
"""
from __future__ import annotations

import csv
from pathlib import Path

from nemo_read._leap_com import dispatch_leap, LeapTreeCache
from nemo_read.leap_conventions import LEAP_BRANCH_TYPES


PREFIX = "Demand\\Residential\\Projections"

# Branches to probe. Each entry is the path under PREFIX. We include
# parent folders + their leaves; both the folder branch and the leaves
# may carry authorable variables.
TARGETS = [
    # Lighting
    "Lighting",
    "Lighting\\Electricity",
    "Lighting\\Electricity\\Incandescent",
    "Lighting\\Electricity\\CFL",
    "Lighting\\Electricity\\Fluorescent",
    "Lighting\\Electricity\\Halogen",
    "Lighting\\Electricity\\LED",
    "Lighting\\Other",
    "Lighting\\Other\\Kerosene and Candles",
    "Lighting\\Other\\Solar Lighting",
    # Air Conditioning
    "Air Conditioning",
    "Air Conditioning\\Current_Stock Average",
    "Air Conditioning\\Current_Sales Average",
    "Air Conditioning\\Efficient",
    "Air Conditioning\\Best Practice",
    # Refrigeration
    "Refrigeration",
    "Refrigeration\\High",
    "Refrigeration\\Medium",
    "Refrigeration\\Low",
]

OUT_CSV = Path(__file__).parent / "_residential_branch_map.csv"


def _safe_unit_text(var, allow: bool) -> tuple[str, bool]:
    """Return (unit, attempted). Attempt DataUnitText only if allow=True
    (i.e. branch type is in {3, 50}). Catch any COM error and return."""
    if not allow:
        return ("", False)
    try:
        raw = var.DataUnitText
        return ("" if raw is None else str(raw), True)
    except Exception as exc:
        return (f"<err: {exc}>", True)


def main() -> int:
    leap = dispatch_leap()
    area = leap.ActiveArea.Name
    print(f"[probe] ActiveArea: {area!r}")
    if area != "aeo9_v0.46":
        print(f"[probe] ABORT: expected 'aeo9_v0.46'")
        return 3
    scen = leap.ActiveScenario.Name
    region = leap.ActiveRegion.Name
    print(f"[probe] ActiveScenario: {scen!r}")
    print(f"[probe] ActiveRegion: {region!r}")
    print(f"[probe] (probe is structural; scenario/region just for record)\n")

    cache = LeapTreeCache(leap=leap)
    print(f"[probe] cache: {len(cache.fullname_to_idx)} branches")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "branch", "branch_type", "branch_type_label",
            "n_variables",
            "variable_index", "variable", "variable_id",
            "unit", "unit_attempted",
        ])
        writer.writeheader()

        for short in TARGETS:
            full = f"{PREFIX}\\{short}"
            print(f"\n[probe] {full}")
            idx = cache.fullname_to_idx.get(full)
            if idx is None:
                print(f"  NOT in cache — skipping")
                writer.writerow({
                    "branch": full,
                    "branch_type": "",
                    "branch_type_label": "NOT_IN_CACHE",
                    "n_variables": 0,
                    "variable_index": "", "variable": "",
                    "variable_id": "", "unit": "", "unit_attempted": False,
                })
                continue

            br = cache.branches.Item(idx)
            try:
                bt = int(br.BranchType)
            except Exception as exc:
                bt = -1
                print(f"  BranchType read error: {exc}")
            bt_label = LEAP_BRANCH_TYPES.get(bt, str(bt))
            print(f"  BranchType: {bt} ({bt_label})")

            try:
                n_vars = br.Variables.Count
            except Exception as exc:
                print(f"  Variables.Count error: {exc}")
                continue
            print(f"  Variables.Count: {n_vars}")

            # Unit reads allowed only on BT={3, 50} per §11.2
            allow_unit = bt in (3, 50)

            for j in range(1, n_vars + 1):
                try:
                    v = br.Variables.Item(j)
                except Exception as exc:
                    print(f"    {j:2d}. <Variables.Item err: {exc}>")
                    continue
                try:
                    vname = v.Name
                except Exception as exc:
                    vname = f"<err: {exc}>"
                try:
                    vid = int(v.ID)
                except Exception:
                    vid = -1
                unit_str, unit_attempted = _safe_unit_text(v, allow_unit)
                marker = "U" if allow_unit else "-"
                print(f"    {j:2d}. [{marker}] id={vid:>4} {vname!r}"
                      f" unit={unit_str!r}")

                writer.writerow({
                    "branch": full,
                    "branch_type": bt,
                    "branch_type_label": bt_label,
                    "n_variables": n_vars,
                    "variable_index": j,
                    "variable": vname,
                    "variable_id": vid,
                    "unit": unit_str,
                    "unit_attempted": unit_attempted,
                })

    print(f"\n[probe] DONE. CSV: {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
