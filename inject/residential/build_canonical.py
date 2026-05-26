"""Residential-domain adapter: source CSVs -> canonical_leap_inputs.csv.

For the 2026-05-21 cycle: LIGHTING ONLY. AC + Refrigeration are
deferred pending the 2-layer structure build (see
`inject/residential/20260521/ac_fridge/structure_request_AC_fridge_2layer_20260521.md`).

Reads from `inject/residential/<YYYYMMDD>/lighting/`:
  - lighting_tech_shares.csv   (Country x Year x Scenario x Tech -> share_percent)
  - lighting_bulb_wattage.csv  (Country x Tech -> watts)

Routes them to LEAP branch families on aeo9_v0.46 (probed 2026-05-20):

  1. Demand\\Residential\\Projections\\Lighting\\Electricity\\<Tech>
     : variable "Activity Level"
        <- lighting_tech_shares.csv share_percent
        One row per (ams, tech, scenario) with multi-year Interp 2025-2060.
        Scenario-tagged (BAS/ATS/RAS each have their own row set).

  2. Demand\\Residential\\Projections\\Lighting\\Electricity\\<Tech>
     : variable "Bulb Wattage"
        <- lighting_bulb_wattage.csv watts
        One row per (ams, tech), scenario-untagged
        (applies across all scenarios via the framework's scenario-column filter).

Per team direction:
  - DO NOT inject Final Energy Intensity (LEAP-side formula)
  - DO NOT inject BulbsPerHH or LightingHours (keep LEAP defaults: 7 / 6)
  - DO NOT inject the `\\Lighting\\Other` arm yet (Kerosene+Candles, Solar)

CSV scenario strings (BAS/ATS/RAS) map to full LEAP scenario names.
Country names use source-CSV form (Brunei Darussalam, Lao PDR, Viet Nam).

Per CLAUDE.md SA.15: every Interp() uses comma list-sep + period decimal.
Per CLAUDE.md SA.18: Timor Leste not in source data; --exclude-timor-leste
required at inject time.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import pandas as pd

from nemo_read._leap_com import normalize_interp


# ---------------------------------------------------------------------------
# Mappings
# ---------------------------------------------------------------------------

# Source-CSV Country -> LEAP region name (same as transport, single source
# of truth would be nicer but each sector currently encodes its own)
COUNTRY_MAP = {
    "Brunei Darussalam": "Brunei",
    "Cambodia": "Cambodia",
    "Indonesia": "Indonesia",
    "Lao PDR": "Laos",
    "Malaysia": "Malaysia",
    "Myanmar": "Myanmar",
    "Philippines": "Philippines",
    "Singapore": "Singapore",
    "Thailand": "Thailand",
    "Viet Nam": "Vietnam",
}

# Source scenario -> LEAP scenario name
SCENARIO_MAP = {
    "BAS": "Baseline Simulation",
    "ATS": "AMS Target Scenario",
    "RAS": "Regional Aspiration Scenario",
}

# Source Tech -> LEAP branch segment (verified identical 2026-05-20 probe)
LIGHTING_TECH = {"Incandescent", "CFL", "Fluorescent", "Halogen", "LED"}


HERE = Path(__file__).parent
INPUT_DIR = HERE / "20260521" / "lighting"
OUTPUT_CSV = HERE / "canonical_leap_inputs.csv"

LIGHTING_BRANCH = "Demand\\Residential\\Projections\\Lighting\\Electricity"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _interp_from_pairs(pairs: list[tuple[int, float]]) -> str:
    if not pairs:
        return ""
    pairs = sorted(pairs, key=lambda p: p[0])
    parts = []
    for y, v in pairs:
        parts.append(str(int(y)))
        parts.append(f"{v:g}")
    return f"Interp({', '.join(parts)})"


# ---------------------------------------------------------------------------
# Per-source transformers
# ---------------------------------------------------------------------------

def _load_tech_shares(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    unknown = set(df["Country"].unique()) - set(COUNTRY_MAP)
    if unknown:
        print(f"  WARN tech_shares: unknown Country: {unknown} - dropped")
        df = df[df["Country"].isin(COUNTRY_MAP)]
    unknown = set(df["Tech"].unique()) - LIGHTING_TECH
    if unknown:
        print(f"  WARN tech_shares: unknown Tech: {unknown} - dropped")
        df = df[df["Tech"].isin(LIGHTING_TECH)]
    unknown = set(df["Scenario"].unique()) - set(SCENARIO_MAP)
    if unknown:
        print(f"  WARN tech_shares: unknown Scenario: {unknown} - dropped")
        df = df[df["Scenario"].isin(SCENARIO_MAP)]
    df = df.copy()
    df["ams"] = df["Country"].map(COUNTRY_MAP)
    df["leap_scenario"] = df["Scenario"].map(SCENARIO_MAP)
    return df


def _load_bulb_wattage(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["Country"].isin(COUNTRY_MAP)]
    df = df[df["Tech"].isin(LIGHTING_TECH)]
    df = df.copy()
    df["ams"] = df["Country"].map(COUNTRY_MAP)
    return df[["ams", "Tech", "watts", "source"]]


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

def _build_activity_level_rows(shares: pd.DataFrame) -> list[dict]:
    """One row per (ams, tech, scenario) with multi-year Interp."""
    rows = []
    grouped = shares.groupby(["ams", "Tech", "leap_scenario"])
    for (ams, tech, scen), sub in grouped:
        pairs = list(zip(sub["Year"].astype(int),
                         sub["share_percent"].astype(float)))
        # Validate per-(ams,year,scenario) sum = 100 happens at parent
        # group level; not enforced here (the team's CSV is verified).
        expr = _interp_from_pairs(pairs)
        if not expr:
            continue
        rows.append({
            "ams": ams,
            "branch": f"{LIGHTING_BRANCH}\\{tech}",
            "variable": "Activity Level",
            "expression": normalize_interp(expr),
            "unit": "Percent",
            "fuel": "",
            "source": "Residential team handover 2026-05-21",
            "note": f"tech share within electricity-lit households, "
                    f"scenario={scen}",
            "src_csv": "lighting_tech_shares.csv",
            "data_confidence": "Medium",
            "scenario": scen,
        })
    return rows


def _build_bulb_wattage_rows(watt: pd.DataFrame) -> list[dict]:
    """One row per (ams, tech). Scenario column LEFT EMPTY -> framework's
    scenario-column filter applies it to every scenario iteration (the
    untagged-rows-go-to-all-scenarios semantics, since wattage is
    scenario-invariant per team)."""
    rows = []
    for _, r in watt.iterrows():
        ams = r["ams"]
        tech = r["Tech"]
        w = float(r["watts"])
        rows.append({
            "ams": ams,
            "branch": f"{LIGHTING_BRANCH}\\{tech}",
            "variable": "Bulb Wattage",
            "expression": normalize_interp(f"Interp(2025, {w:g})"),
            "unit": "Watts",
            "fuel": "",
            "source": str(r.get("source", "Residential team handover 2026-05-21")),
            "note": "scenario-invariant; applies to all scenarios",
            "src_csv": "lighting_bulb_wattage.csv",
            "data_confidence": "Medium",
            "scenario": "",   # untagged -> applies across all scenarios
        })
    return rows


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(include_families: set[str] | None = None):
    inc = set(include_families or {"tech_shares", "bulb_wattage"})
    print(f"[residential adapter] reading from {INPUT_DIR}/")
    print(f"[residential adapter] including: {sorted(inc)}")

    shares = _load_tech_shares(INPUT_DIR / "lighting_tech_shares.csv")
    print(f"  tech_shares rows: {len(shares)}")
    watt = _load_bulb_wattage(INPUT_DIR / "lighting_bulb_wattage.csv")
    print(f"  bulb_wattage rows: {len(watt)}")

    rows = []
    if "tech_shares" in inc:
        rows.extend(_build_activity_level_rows(shares))
    if "bulb_wattage" in inc:
        rows.extend(_build_bulb_wattage_rows(watt))

    # Sort: scenario-tagged rows first (Activity Level), then untagged
    # (Bulb Wattage). Within scenario, sort by ams + branch for stable
    # output ordering.
    def _sort_key(r):
        scen_key = (0, r["scenario"]) if r["scenario"] else (1, "")
        return (r["ams"], scen_key, r["branch"], r["variable"])
    rows.sort(key=_sort_key)

    fieldnames = ["ams", "branch", "variable", "expression", "unit",
                  "fuel", "source", "note", "src_csv",
                  "data_confidence", "scenario"]
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            r["expression"] = normalize_interp(r.get("expression", ""))
            writer.writerow(r)

    print(f"\n[residential adapter] wrote {OUTPUT_CSV.name}  ({len(rows)} rows)")
    by_var = defaultdict(int)
    by_scenario = defaultdict(int)
    by_ams = defaultdict(int)
    for r in rows:
        by_var[r["variable"]] += 1
        by_scenario[r["scenario"] or "<untagged>"] += 1
        by_ams[r["ams"]] += 1
    print(f"\n  Rows per variable:  {dict(by_var)}")
    print(f"  Rows per scenario:  {dict(by_scenario)}")
    print(f"  Rows per AMS:       {dict(by_ams)}")


def _parse_args():
    p = argparse.ArgumentParser(
        description="Residential adapter (Lighting only for 2026-05-21)")
    p.add_argument(
        "--include-families", default="tech_shares,bulb_wattage",
        help="Comma-separated list of families to include. "
             "Options: tech_shares, bulb_wattage. "
             "Default: both.")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    inc = {s.strip() for s in args.include_families.split(",") if s.strip()}
    build(include_families=inc)
