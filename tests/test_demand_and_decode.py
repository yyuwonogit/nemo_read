"""Tests for the 0.6.2 readability layer + demand reader + value lookups."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from nemo_read import (
    LeapAreaContext, NemoDB, decode_dims, read_demand,
)


FIXTURE = Path(__file__).parent / "fixtures" / "leap_export"


def _make_demand_db(path: Path) -> None:
    """Synthetic NEMO DB carrying a small SpecifiedAnnualDemand population."""
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("CREATE TABLE Version (version INTEGER PRIMARY KEY)")
    cur.execute("INSERT INTO Version (version) VALUES (11)")
    # DefaultParams is referenced by get_parameter for default-overlay logic.
    cur.execute(
        "CREATE TABLE DefaultParams (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "tablename TEXT, val REAL)"
    )
    cur.execute("CREATE TABLE REGION (val TEXT PRIMARY KEY, desc TEXT)")
    cur.execute("CREATE TABLE FUEL   (val TEXT PRIMARY KEY, desc TEXT)")
    cur.execute("CREATE TABLE YEAR   (val TEXT PRIMARY KEY, desc TEXT)")
    cur.executemany("INSERT INTO REGION VALUES (?, ?)",
                    [("R1", "Indonesia"), ("R2", "Malaysia")])
    cur.executemany("INSERT INTO FUEL VALUES (?, ?)",
                    [("F1", "Electricity [LEAP ID:1]"),
                     ("F2", "Natural Gas [LEAP ID:2]")])
    cur.executemany("INSERT INTO YEAR VALUES (?, ?)",
                    [("2025", ""), ("2030", "")])
    cur.execute(
        "CREATE TABLE SpecifiedAnnualDemand "
        "(id INTEGER PRIMARY KEY, r TEXT, f TEXT, y TEXT, val REAL)"
    )
    cur.execute(
        "CREATE TABLE AccumulatedAnnualDemand "
        "(id INTEGER PRIMARY KEY, r TEXT, f TEXT, y TEXT, val REAL)"
    )
    cur.executemany(
        "INSERT INTO SpecifiedAnnualDemand (r, f, y, val) VALUES (?, ?, ?, ?)",
        [("R1", "F1", "2025", 100.0), ("R1", "F1", "2030", 120.0),
         ("R2", "F1", "2025", 50.0)],
    )
    cur.executemany(
        "INSERT INTO AccumulatedAnnualDemand (r, f, y, val) VALUES (?, ?, ?, ?)",
        [("R1", "F2", "2025", 30.0)],
    )
    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# decode_dims — the readability rule
# ---------------------------------------------------------------------------
def test_decode_dims_attaches_region_and_fuel_names(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_demand_db(db_path)
    db = NemoDB(db_path)
    raw = db.query("SELECT r, f, y, val FROM SpecifiedAnnualDemand")
    decoded = decode_dims(raw, db)
    assert "region_name" in decoded.columns
    assert "fuel_name" in decoded.columns
    indo_rows = decoded[decoded["r"] == "R1"]
    assert (indo_rows["region_name"] == "Indonesia").all()
    elec = decoded[decoded["f"] == "F1"]
    assert elec["fuel_name"].iloc[0].startswith("Electricity")


def test_decode_dims_skips_unknown_dims(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_demand_db(db_path)
    db = NemoDB(db_path)
    df = pd.DataFrame({"foo": ["A", "B"], "val": [1.0, 2.0]})
    out = decode_dims(df, db)
    # No 'foo'-decoded column added (foo isn't a NEMO dim code)
    assert list(out.columns) == ["foo", "val"]


def test_decode_dims_handles_empty_input(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_demand_db(db_path)
    db = NemoDB(db_path)
    out = decode_dims(pd.DataFrame(), db)
    assert out.empty


# ---------------------------------------------------------------------------
# read_demand by fuel — purely SQLite-side
# ---------------------------------------------------------------------------
def test_read_demand_by_fuel_decoded_by_default(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_demand_db(db_path)
    db = NemoDB(db_path)
    df = read_demand(db)        # by="fuel" default, decode=True default
    assert "region_name" in df.columns
    assert "fuel_name" in df.columns
    assert "source" in df.columns
    # Three rows from Specified + one from Accumulated = 4 total
    assert len(df) == 4
    assert set(df["source"]) == {"SpecifiedAnnualDemand", "AccumulatedAnnualDemand"}


def test_read_demand_by_fuel_undecoded(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_demand_db(db_path)
    db = NemoDB(db_path)
    df = read_demand(db, decode=False)
    assert "region_name" not in df.columns
    assert "fuel_name" not in df.columns


def test_read_demand_by_fuel_filters(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_demand_db(db_path)
    db = NemoDB(db_path)
    only_sad = read_demand(db, include_accumulated=False)
    assert (only_sad["source"] == "SpecifiedAnnualDemand").all()
    only_aad = read_demand(db, include_specified=False)
    assert (only_aad["source"] == "AccumulatedAnnualDemand").all()


# ---------------------------------------------------------------------------
# read_demand by sector — needs LeapAreaContext + branch_values
# ---------------------------------------------------------------------------
def test_read_demand_by_sector_requires_context(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_demand_db(db_path)
    db = NemoDB(db_path)
    with pytest.raises(ValueError, match="requires a LeapAreaContext"):
        read_demand(db, by="sector")


def test_read_demand_by_sector_aggregates_correctly(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_demand_db(db_path)
    db = NemoDB(db_path)
    ctx = LeapAreaContext.from_export(FIXTURE)
    df = read_demand(db, by="sector", context=ctx)
    # Industry has 2 leaves (Cement Electric Kiln + Steel EAF), each 2 years
    # Residential has 1 leaf (Residential Cooking), 2 years
    assert {"sector", "subsector", "region_id", "year", "val"}.issubset(df.columns)
    industry = df[df["sector"] == "Industry"]
    assert len(industry) == 4   # 2 subsectors × 2 years
    # Industry 2025 total = 12.5 + 8.0 = 20.5 across two subsectors,
    # but we keep them broken out:
    cement_2025 = df[(df["sector"] == "Industry") & (df["subsector"] == "Cement") & (df["year"] == 2025)]
    assert cement_2025["val"].iloc[0] == 12.5
    residential = df[df["sector"] == "Residential"]
    assert len(residential) == 2
    # region_name attached when decode=True (default)
    assert "region_name" in df.columns
    # region_id=2 → 'Indonesia' per fixtures' regions.csv
    assert (df["region_name"] == "Indonesia").all()


def test_read_demand_invalid_by_raises():
    db = NemoDB.__new__(NemoDB)  # placeholder — won't be used
    with pytest.raises(ValueError, match="Unknown by="):
        read_demand(db, by="other")


# ---------------------------------------------------------------------------
# LeapAreaContext.variable_value lookup
# ---------------------------------------------------------------------------
def test_variable_value_specific_year_region_returns_float():
    ctx = LeapAreaContext.from_export(FIXTURE)
    v = ctx.variable_value(30001, "Final Energy Demand", year=2025, region_id=2)
    assert v == 12.5


def test_variable_value_unspecified_year_returns_series():
    ctx = LeapAreaContext.from_export(FIXTURE)
    s = ctx.variable_value(30001, "Final Energy Demand", region_id=2)
    assert hasattr(s, "__iter__")
    assert sorted(s.tolist()) == [12.5, 15.2]


def test_variable_value_unknown_returns_none():
    ctx = LeapAreaContext.from_export(FIXTURE)
    assert ctx.variable_value(999999, "Anything") is None


def test_branch_expressions_loaded():
    ctx = LeapAreaContext.from_export(FIXTURE)
    assert not ctx.branch_expressions.empty
    cap = ctx.branch_expressions[
        (ctx.branch_expressions["branch_id"] == 11942) &
        (ctx.branch_expressions["variable_name"] == "Capital Cost")
    ]
    assert len(cap) == 1
    assert "1200" in cap.iloc[0]["expression"]
