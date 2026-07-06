"""Tripwire for CLAUDE.md §A.21 — sub-national process-node variants are
REGION-LOCKED: a `_MY*` node belongs only to Malaysia, a `_ID*` node only to
Indonesia. No inject CSV may author one in any other AMS.

Three layers:
  1. Unit tests of `find_region_lock_violations` (all three CSV shapes:
     long `ams`/`branch`, wide `region`/`node`, export-style
     `region`/`branch_path` incl. BOM'd `Branch Path` raw drops).
  2. Repo scan — every committed inject CSV must be region-lock clean,
     except the documented reference-dump/raw-drop exemptions below.
  3. Self-cleaning exemption ledger — an exemption whose file goes clean
     FAILS, forcing its retirement (exemptions can't rot silently).

History: before 2026-07-05 the checker only knew `node`/`branch` columns, so
export-style CSVs were skipped wholesale — 18,943 wrong-region rows across 5
files passed this tripwire unseen (structural-uniformity sweep finding).
"""
import csv
from pathlib import Path

import pytest

from nemo_read import find_region_lock_violations, NODE_REGION_LOCK

REPO = Path(__file__).resolve().parent.parent
INJECT = REPO / "inject"

# --- documented exemptions from the repo-scan (test_committed_inject_csvs...) ---
#
# (a) `current_expressions_*` reference dumps: region-deduplicated snapshots of
#     what the LIVE MODEL holds, shipped to teams as read-only evidence. Their
#     wrong-region `_MY*` rows document misfiled data inside the LEAP area
#     itself (tracked in CANON_ANOMALY_AUDIT); the dump must stay faithful to
#     the model, so it cannot be "cleaned" repo-side. Never an inject payload.
_EXEMPT_PREFIX = "current_expressions_"
#
# (b) Raw power-team drops (received archive, kept verbatim per §A.21 notes
#     convention). Their wrong-region rows are valueless inheritance phantoms
#     (zeros / one uniform structural formula); the *_canonical.csv siblings —
#     the actual inject payloads — are scanned and clean.
_EXEMPT_RAW_DROPS = {
    "inject/power/20260507/ats_cap_add.csv",
    "inject/power/20260507/ats_cap_ret.csv",
    "inject/power/20260507/ats_exo_formula.csv",
    "inject/power/20260507/bas_all_zero.csv",
}


def _is_exempt(csv_path: Path) -> bool:
    rel = csv_path.relative_to(REPO).as_posix()
    return csv_path.name.startswith(_EXEMPT_PREFIX) or rel in _EXEMPT_RAW_DROPS


def _write(tmp_path, header, rows):
    p = tmp_path / "c.csv"
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return p


def test_wide_format_flags_variant_in_wrong_country(tmp_path):
    p = _write(tmp_path, ["node", "region", "variable", "CA"], [
        ["Solar PV_MYPE", "Malaysia", "Capital Cost", "1"],   # ok
        ["Solar PV_MYPE", "Vietnam", "Capital Cost", "1"],    # violation
        ["Geothermal Flash_IDJW", "Indonesia", "Capital Cost", "1"],  # ok
        ["Geothermal Flash_IDJW", "Thailand", "Capital Cost", "1"],   # violation
        ["Solar CSP", "Vietnam", "Capital Cost", "1"],        # base node — ok
    ])
    v = find_region_lock_violations(p)
    assert len(v) == 2
    assert {(x[1], x[2]) for x in v} == {("Solar PV_MYPE", "Vietnam"),
                                         ("Geothermal Flash_IDJW", "Thailand")}


def test_long_format_ams_branch(tmp_path):
    bs = chr(92)
    p = _write(tmp_path, ["ams", "branch", "variable", "expression"], [
        ["Malaysia", f"Transformation{bs}...{bs}Processes{bs}Wind Onshore_MYSR", "Capital Cost", "1"],
        ["Laos", f"Transformation{bs}...{bs}Processes{bs}Wind Onshore_MYSR", "Capital Cost", "1"],  # violation
        ["Indonesia", f"Transformation{bs}...{bs}Processes{bs}Large Hydro_IDEast", "Capital Cost", "1"],
    ])
    v = find_region_lock_violations(p)
    assert len(v) == 1
    assert v[0][1] == "Wind Onshore_MYSR" and v[0][2] == "Laos" and v[0][3] == "Malaysia"


def test_sub_branch_variant_ancestor_is_caught(tmp_path):
    """A _MY* process node in an ANCESTOR position (feedstock/emission leaf row)
    must be caught, not just leaf-position process-node rows."""
    bs = chr(92)
    base = f"Transformation{bs}Centralized Electricity Generation{bs}Processes"
    p = _write(tmp_path, ["ams", "branch", "variable", "expression"], [
        ["Malaysia", f"{base}{bs}Coal Subcritical_MYPE{bs}Feedstock Fuels{bs}Coal Bituminous{bs}Carbon Dioxide", "Avg Environmental Loading", "95"],
        ["Vietnam", f"{base}{bs}Coal Subcritical_MYPE{bs}Feedstock Fuels{bs}Coal Bituminous{bs}Carbon Dioxide", "Avg Environmental Loading", "95"],  # violation
    ])
    v = find_region_lock_violations(p)
    assert len(v) == 1
    assert v[0][1] == "Coal Subcritical_MYPE" and v[0][2] == "Vietnam"


def test_clean_csv_no_violations(tmp_path):
    p = _write(tmp_path, ["node", "region", "variable", "CA"], [
        ["Solar PV_MYPE", "Malaysia", "Capital Cost", "1"],
        ["Coal Supercritical", "Vietnam", "Capital Cost", "1"],
    ])
    assert find_region_lock_violations(p) == []


def test_lock_map_is_the_canon_set():
    homes = set(NODE_REGION_LOCK.values())
    assert homes == {"Malaysia", "Indonesia"}


def test_export_style_branch_path_is_scanned(tmp_path):
    """Regression for the 2026-07-05 blind spot: export-style CSVs
    (`branch_path` column) were skipped entirely (nc=None -> [])."""
    bs = chr(92)
    base = f"Transformation{bs}Centralized Electricity Generation{bs}Processes"
    p = _write(tmp_path, ["branch_path", "variable", "scenario", "region", "expression"], [
        [f"{base}{bs}Biomass Other_MYPE", "Capacity Additions", "RAS", "Vietnam", "Interp(2023,175)"],   # violation
        [f"{base}{bs}Biomass Other_MYPE", "Capacity Additions", "RAS", "Malaysia", "Add(2026,11)"],      # ok (home)
        [f"{base}{bs}Solar PV_IDJW", "Capital Cost", "RAS", "Indonesia", "1"],                            # ok (home)
        [f"{base}{bs}Coal Supercritical", "Capital Cost", "RAS", "Vietnam", "1"],                         # base node — ok
    ])
    v = find_region_lock_violations(p)
    assert len(v) == 1
    assert v[0][1] == "Biomass Other_MYPE" and v[0][2] == "Vietnam" and v[0][3] == "Malaysia"


def test_raw_drop_header_with_bom_is_scanned(tmp_path):
    """Raw team drops use `Branch Path`/`Region` headers AND a UTF-8 BOM; the
    BOM used to mangle the first fieldname and skip the file."""
    bs = chr(92)
    p = tmp_path / "raw.csv"
    with open(p, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["Branch Path", "Region", "Expression"])
        w.writerow([f"Transformation{bs}...{bs}Processes{bs}Large Hydro_IDEast", "Thailand", "0"])
    v = find_region_lock_violations(p)
    assert len(v) == 1
    assert v[0][1] == "Large Hydro_IDEast" and v[0][2] == "Thailand" and v[0][3] == "Indonesia"


def test_all_regions_dedup_bucket_is_skipped(tmp_path):
    """`ALL (N regions)` rows are the region-deduplicated inheritance default
    in reference dumps — uniform structure, not a per-country authoring."""
    bs = chr(92)
    p = _write(tmp_path, ["branch_path", "variable", "scenario", "region", "expression"], [
        [f"T{bs}Processes{bs}Solar PV_MYPE", "Lifetime", "CA", "ALL (12 regions)", "25"],  # skipped
        [f"T{bs}Processes{bs}Solar PV_MYPE", "Lifetime", "CA", "Laos", "25"],              # violation
    ])
    v = find_region_lock_violations(p)
    assert len(v) == 1 and v[0][2] == "Laos"


@pytest.mark.parametrize(
    "csv_path",
    sorted(p for p in INJECT.rglob("*.csv") if not _is_exempt(p)),
    ids=lambda p: str(p.relative_to(REPO)),
)
def test_committed_inject_csvs_are_region_lock_clean(csv_path):
    """Every non-exempt inject CSV must be region-lock clean (§A.21). Incoming
    team drops with wrong-region node-variant rows must be cleaned before
    commit."""
    v = find_region_lock_violations(csv_path)
    assert not v, (
        f"{len(v)} region-lock violation(s) in {csv_path.relative_to(REPO)} "
        f"(e.g. row {v[0][0]}: {v[0][1]} in {v[0][2]}, belongs to {v[0][3]}). "
        f"Remove wrong-AMS node-variant rows; see the notes convention in §A.21."
    )


@pytest.mark.parametrize("rel", sorted(_EXEMPT_RAW_DROPS))
def test_exempt_raw_drops_still_dirty_else_retire_exemption(rel):
    """Self-cleaning ledger: every explicit exemption must (a) still exist and
    (b) still contain violations. The moment a file is cleaned or removed,
    this fails — retire its exemption instead of letting it rot."""
    p = REPO / rel
    assert p.exists(), f"exempt file gone — remove {rel} from _EXEMPT_RAW_DROPS"
    assert find_region_lock_violations(p), (
        f"{rel} is now region-lock clean — remove it from _EXEMPT_RAW_DROPS"
    )
