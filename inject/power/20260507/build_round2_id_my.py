"""Round 2 ID/MY subnational EC + HP inject builder.

Reads the Rev1 wide CSV (one row per (subnational branch, variable)
with year columns 2005-2024) and emits canonical inject rows in the
round-1.5 anchor pattern:

    Interp(2005, V, 2006, V, ..., 2024, V, FirstScenarioYear, 0)

Outputs:

  1. `inject_round2_id_my_CA.csv`  — 63 EC + 63 HP rows (Current Accounts)
  2. `inject_round2_id_my_ATS.csv` — 63 HP rows (AMS Target Scenario)
  3. `inject_round2_id_my_BAS.csv` — 63 HP rows (Baseline Simulation)

Then merges each chunk into the matching round-1.5 file
(`inject_round1p5_<SCN>.csv`) after creating a `.bak_pre_20260507`
backup of the pre-merge state. Chunk files are kept for audit.

Usage:
    python mailbox/power/20260507/build_round2_id_my.py
"""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

REV1 = Path("mailbox/power/20260507/"
            "Transformation_ Input LEAP_ID_MY_Nodes Rev1 "
            "(Existing Cap, Historical Prod).csv")
OUT_DIR = Path("mailbox/power/20260507")
ROUND1P5_DIR = Path("mailbox/20260505")

YEAR_COLS = [str(y) for y in range(2005, 2025)]

CANONICAL_FIELDS = [
    "ams", "branch", "variable", "expression", "unit",
    "fuel", "source", "note", "src_csv", "domain", "data_confidence",
]

SOURCE_TAG = ("Transformation_ Input LEAP_ID_MY_Nodes Rev1.csv "
              "(round 2 ID/MY subnational, 2026-05-07)")
SRC_CSV_TAG = "Transformation_ Input LEAP_ID_MY_Nodes Rev1.csv"
NOTE_TAG = ("Round 2 — ID/MY subnational EC+HP from Rev1 LEAP-export, "
            "anchor with FirstScenarioYear=0")


def _fmt_value(v) -> str:
    """Format a numeric value to LEAP-friendly text (period decimal, no
    trailing zeros). Empty / None / non-numeric → empty string."""
    if v is None or v == "":
        return ""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return ""
    s = f"{f:.6f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _fmt_interp(year_to_val: dict[int, str]) -> str:
    """Build Interp(2005, v, ..., 2024, v, FirstScenarioYear, 0)."""
    parts = []
    for y in sorted(year_to_val):
        parts.append(f"{y}, {year_to_val[y]}")
    parts.append("FirstScenarioYear, 0")
    return f"Interp({', '.join(parts)})"


def _domain_for(variable: str) -> str:
    if variable == "Existing Capacity":
        return "power_existing_capacity"
    if variable == "Historical Production":
        return "power_historical_production"
    return f"power_{variable.strip().lower().replace(' ', '_')}"


def build_rows() -> tuple[list[dict], list[dict]]:
    """Return (ec_rows, hp_rows) — canonical inject rows."""
    ec_rows: list[dict] = []
    hp_rows: list[dict] = []

    with REV1.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            branch = (row.get("Branch Path") or "").strip()
            variable = (row.get("Variable") or "").strip()
            region = (row.get("Region") or "").strip()
            unit = (row.get("Unit") or "").strip()
            if unit == "MW":
                unit = "Megawatt"  # match round-1.5 unit-string convention
            if not branch or not variable:
                continue

            year_to_val: dict[int, str] = {}
            for y_col in YEAR_COLS:
                cell = row.get(y_col)
                v = _fmt_value(cell)
                if v == "":
                    continue
                year_to_val[int(y_col)] = v
            if not year_to_val:
                continue

            expr = _fmt_interp(year_to_val)
            canonical = {
                "ams": region,
                "branch": branch,
                "variable": variable,
                "expression": expr,
                "unit": unit,
                "fuel": "",
                "source": SOURCE_TAG,
                "note": NOTE_TAG,
                "src_csv": SRC_CSV_TAG,
                "domain": _domain_for(variable),
                "data_confidence": "High",
            }

            if variable == "Existing Capacity":
                ec_rows.append(canonical)
            elif variable == "Historical Production":
                hp_rows.append(canonical)
            else:
                # Unexpected variable — keep in HP bucket conservatively
                # so it gets attention via the row count.
                hp_rows.append(canonical)
    return ec_rows, hp_rows


def write_chunk(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
        w.writeheader()
        w.writerows(rows)


def append_to_round1p5(target: Path, rows: list[dict]) -> None:
    """Append rows to an existing round-1.5 inject file. Header is
    skipped (file already has one). Backup with .bak_pre_20260507
    suffix is created on first call only."""
    bak = target.with_suffix(target.suffix + ".bak_pre_20260507")
    if not bak.exists():
        shutil.copy2(target, bak)
        print(f"  backup: {bak.name}")

    with target.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
        w.writerows(rows)


def main() -> int:
    if not REV1.exists():
        raise SystemExit(f"[ERROR] Rev1 input not found: {REV1}")

    print(f"[round2] reading {REV1.name}")
    ec_rows, hp_rows = build_rows()
    print(f"[round2] parsed {len(ec_rows)} EC + {len(hp_rows)} HP "
          f"canonical rows")

    # Sanity-check region split
    by_region_ec: dict[str, int] = {}
    for r in ec_rows:
        by_region_ec[r["ams"]] = by_region_ec.get(r["ams"], 0) + 1
    by_region_hp: dict[str, int] = {}
    for r in hp_rows:
        by_region_hp[r["ams"]] = by_region_hp.get(r["ams"], 0) + 1
    print(f"[round2] EC by region: {by_region_ec}")
    print(f"[round2] HP by region: {by_region_hp}")

    # 1. Audit chunk files
    ca_chunk = OUT_DIR / "inject_round2_id_my_CA.csv"
    ats_chunk = OUT_DIR / "inject_round2_id_my_ATS.csv"
    bas_chunk = OUT_DIR / "inject_round2_id_my_BAS.csv"
    write_chunk(ca_chunk, ec_rows + hp_rows)
    write_chunk(ats_chunk, hp_rows)
    write_chunk(bas_chunk, hp_rows)
    print(f"[round2] wrote audit chunks:")
    print(f"  {ca_chunk.name}  ({len(ec_rows) + len(hp_rows)} rows)")
    print(f"  {ats_chunk.name}  ({len(hp_rows)} rows)")
    print(f"  {bas_chunk.name}  ({len(hp_rows)} rows)")

    # 2. Merge into round-1.5 files (with backup)
    print(f"[round2] merging into round-1.5 files (with backup):")
    append_to_round1p5(ROUND1P5_DIR / "inject_round1p5_CA.csv",
                       ec_rows + hp_rows)
    append_to_round1p5(ROUND1P5_DIR / "inject_round1p5_ATS.csv",
                       hp_rows)
    append_to_round1p5(ROUND1P5_DIR / "inject_round1p5_BAS.csv",
                       hp_rows)

    print(f"[round2] done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
