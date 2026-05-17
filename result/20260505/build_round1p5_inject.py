"""Build round 1.5 inject CSVs — patches A, B, C from the Wind Onshore probe.

Three patches:
  A. Anchor HP for non-ID/MY in BAS + ATS where missing
     (canonical: HP must drop to 0 at FirstScenarioYear so projection-side
     can't see leaked historical production)
  B. Anchor our injected CA EC from round 1
     (housekeeping — append `, FirstScenarioYear, 0` to round-1 expressions)
  C. Populate HP for techs that don't have it yet
     (HP from xlsx Input_to_LEAP sheet, written to CA so BAS/ATS inherit
     plus also explicitly to BAS/ATS since LEAP convention here copies HP
     across scenarios)

Source: mailbox/existing_cap_historical_prod.xlsx, sheet "Input_to_LEAP"
        (already pre-formatted with Country / Variable / Unit / Branch Path /
         year columns 2005-2024)

Output: 3 CSVs to inject sequentially with --scenario flag:
  inject_round1p5_CA.csv     → run with --scenario "Current Accounts"
  inject_round1p5_BAS.csv    → run with --scenario "Baseline Simulation"  (LEAP scenario name for "BAS")
  inject_round1p5_ATS.csv    → run with --scenario "AMS Target Scenario"  (LEAP scenario name for "ATS")

Anchor convention: every Interp ends with `, FirstScenarioYear, 0`.
Source-of-truth tag: data_confidence=High; note=round 1.5 anchor patch.
"""
from __future__ import annotations
import csv
import warnings
from pathlib import Path
from collections import defaultdict
import pandas as pd

warnings.filterwarnings("ignore")

XLSX = Path(r"mailbox/existing_cap_historical_prod.xlsx")
OUT_DIR = Path(r"mailbox/20260505")

NON_IDMY_COUNTRIES = ("Brunei", "Cambodia", "Laos", "Myanmar", "Philippines",
                      "Singapore", "Thailand", "Vietnam")
PROCESSES_PREFIX = r"Transformation\Centralized Electricity Generation\Processes"
YEARS = list(range(2005, 2025))


def load_input_to_leap() -> list[dict]:
    """Read the Input_to_LEAP sheet, return list of row dicts:
    {country, variable, unit, branch, year_values: {year: MW/GWh}}.
    Already in LEAP-std names + branch paths — no Mapping translation.
    """
    df = pd.read_excel(XLSX, sheet_name="Input_to_LEAP")
    out = []
    for _, row in df.iterrows():
        country = row.get("Country")
        if not isinstance(country, str) or country.strip() not in NON_IDMY_COUNTRIES:
            continue
        branch = row.get("Branch Path")
        if not isinstance(branch, str) or not branch.startswith(PROCESSES_PREFIX):
            continue
        variable = row.get("Variable")
        unit = row.get("Unit")
        year_values: dict[int, float] = {}
        for y in YEARS:
            v = row.get(y)
            if pd.notna(v):
                try: year_values[y] = float(v)
                except (TypeError, ValueError): pass
        if not year_values:
            continue
        out.append({
            "country": country.strip(),
            "variable": variable.strip() if isinstance(variable, str) else "",
            "unit": unit.strip() if isinstance(unit, str) else "",
            "branch": branch.strip(),
            "year_values": year_values,
        })
    return out


def fmt_interp_with_anchor(year_val: dict[int, float]) -> str:
    """Build Interp(2005, V05, ..., 2024, V24, FirstScenarioYear, 0)."""
    parts = []
    for y in sorted(year_val):
        s = f"{year_val[y]:.6f}".rstrip("0").rstrip(".")
        if not s: s = "0"
        parts.append(f"{y}, {s}")
    parts.append("FirstScenarioYear, 0")
    return f"Interp({', '.join(parts)})"


def make_row(country, branch, variable, expression, unit, note) -> dict:
    return {
        "ams": country,
        "branch": branch,
        "variable": variable,
        "expression": expression,
        "unit": unit,
        "fuel": "",
        "source": "existing_cap_historical_prod.xlsx Input_to_LEAP sheet (round 1.5 anchor patch)",
        "note": note,
        "src_csv": "existing_cap_historical_prod.xlsx",
        "domain": "power_existing_capacity",
        "data_confidence": "High",
    }


def main():
    rows = load_input_to_leap()
    print(f"Loaded {len(rows)} (country, variable, branch) entries from Input_to_LEAP")

    # Categorize
    ec_rows = [r for r in rows if r["variable"] == "Existing Capacity"]
    hp_rows = [r for r in rows if r["variable"] == "Historical Production"]
    print(f"  EC entries: {len(ec_rows)}  HP entries: {len(hp_rows)}")
    print(f"  Distinct countries: {sorted({r['country'] for r in rows})}")

    # ---------- CA patch (B + C combined): re-anchored EC + new HP with anchor
    ca_rows = []
    for r in ec_rows:
        ca_rows.append(make_row(
            r["country"], r["branch"], "Existing Capacity",
            fmt_interp_with_anchor(r["year_values"]),
            "Megawatt",  # canonicalize unit name
            "Round 1.5 patch B — re-anchor EC with FirstScenarioYear=0 (overrides round 1)",
        ))
    for r in hp_rows:
        ca_rows.append(make_row(
            r["country"], r["branch"], "Historical Production",
            fmt_interp_with_anchor(r["year_values"]),
            "Gigawatt-Hour",  # canonicalize unit name (xlsx says GWh)
            "Round 1.5 patch C — populate HP with anchor at FirstScenarioYear=0",
        ))
    ca_path = OUT_DIR / "inject_round1p5_CA.csv"
    write_csv(ca_path, ca_rows)
    print(f"\n  CA inject: {len(ca_rows)} rows  →  {ca_path}")

    # ---------- BAS patch (A): HP with anchor, no EC (Value(2024) handles inheritance)
    bas_rows = []
    for r in hp_rows:
        bas_rows.append(make_row(
            r["country"], r["branch"], "Historical Production",
            fmt_interp_with_anchor(r["year_values"]),
            "Gigawatt-Hour",
            "Round 1.5 patch A — HP with FirstScenarioYear=0 anchor for BAS scenario",
        ))
    bas_path = OUT_DIR / "inject_round1p5_BAS.csv"
    write_csv(bas_path, bas_rows)
    print(f"  BAS inject: {len(bas_rows)} rows  →  {bas_path}")

    # ---------- ATS patch (A): HP with anchor
    ats_rows = []
    for r in hp_rows:
        ats_rows.append(make_row(
            r["country"], r["branch"], "Historical Production",
            fmt_interp_with_anchor(r["year_values"]),
            "Gigawatt-Hour",
            "Round 1.5 patch A — HP with FirstScenarioYear=0 anchor for ATS scenario",
        ))
    ats_path = OUT_DIR / "inject_round1p5_ATS.csv"
    write_csv(ats_path, ats_rows)
    print(f"  ATS inject: {len(ats_rows)} rows  →  {ats_path}")

    # Summary by country/variable
    print(f"\n  per-country breakdown:")
    by_cv = defaultdict(int)
    for r in rows:
        by_cv[(r["country"], r["variable"])] += 1
    for c in sorted({r["country"] for r in rows}):
        ec_n = by_cv.get((c, "Existing Capacity"), 0)
        hp_n = by_cv.get((c, "Historical Production"), 0)
        print(f"    {c:<14} EC={ec_n:>3}  HP={hp_n:>3}")


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = ["ams","branch","variable","expression","unit","fuel",
              "source","note","src_csv","domain","data_confidence"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
