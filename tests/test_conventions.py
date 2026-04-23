"""
Tests for the LEAP conventions module and the validation module.
"""
from __future__ import annotations

import sys
import sqlite3
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tests.test_nemo_read import _build_synthetic_db
from tests.test_extensions import _extend_db

from nemo_read import (
    NemoDB, LEAP_NEMO_UNITS, classify_technology_id, extract_leap_ids,
    units_for, validate_scenario, tsgroup_hours,
)
import pandas as pd


def test_leap_nemo_units_constants():
    # Units should include the documented LEAP-NEMO defaults.
    assert LEAP_NEMO_UNITS["energy"] == "PJ"
    assert LEAP_NEMO_UNITS["power"] == "GW"
    assert LEAP_NEMO_UNITS["cost"].startswith("million")
    assert LEAP_NEMO_UNITS["emissions"] == "t"


def test_units_for_common_entities():
    assert units_for("CapitalCost") == "million currency units"
    assert units_for("vannualemissions") == "t"
    assert units_for("vtotalcapacityannual") == "GW"
    assert units_for("vproductionbytechnologyannual") == "PJ"
    assert units_for("vrateofproduction") == "PJ/year"
    # Dimensionless things return None.
    assert units_for("AvailabilityFactor") is None
    assert units_for("RETagTechnology") is None


def test_classify_technology_id():
    assert classify_technology_id("D16677") == "demand"
    assert classify_technology_id("P16756") == "process"
    assert classify_technology_id("S13I") == "supply"
    assert classify_technology_id("Unserved") == "other"
    assert classify_technology_id("") == "other"


def test_extract_leap_ids():
    df = pd.DataFrame({
        "val": ["F1", "F2", "F3"],
        "desc": [
            "Useful demand for Trucks [LEAP ID:16575]",
            "Hydrogen input [LEAP ID:35]",
            "No id at all",
        ],
    })
    out = extract_leap_ids(df)
    assert list(out["leap_id"].fillna(-1).astype(int)) == [16575, 35, -1]


def _make_full_db(path: Path) -> None:
    _build_synthetic_db(path)
    _extend_db(path)


def test_validate_clean_db_passes():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _make_full_db(path)
        db = NemoDB(path)
        report = validate_scenario(db)
        # Base synthetic DB is clean except potentially for our injected
        # slack techs and __NEMOcc, which do not break referential integrity.
        # Allow warnings (e.g. missing profile for Unserved demand) but not errors.
        assert report.ok(), [i.message for i in report.errors()]


def test_validate_catches_orphan_reference():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _make_full_db(path)
        # Introduce a ResidualCapacity row with an unknown technology.
        con = sqlite3.connect(path)
        con.execute("INSERT INTO ResidualCapacity (id, r, t, y, val) "
                    "VALUES (99999, 'IDN', 'GHOST_TECH', '2024', 5.0)")
        con.commit()
        con.close()
        db = NemoDB(path)
        report = validate_scenario(db)
        assert not report.ok()
        # At least one error should mention GHOST_TECH or ResidualCapacity.
        error_messages = " ".join(i.message for i in report.errors())
        assert "GHOST_TECH" in error_messages or "ResidualCapacity" in " ".join(
            i.table for i in report.errors()
        )


def test_validate_catches_year_split_sum():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _make_full_db(path)
        # Corrupt YearSplit so it no longer sums to 1.0 for 2024.
        con = sqlite3.connect(path)
        con.execute("UPDATE YearSplit SET val = 0.5 WHERE y = '2024' AND id = 0")
        con.commit()
        con.close()
        db = NemoDB(path)
        report = validate_scenario(db)
        assert any(i.table == "YearSplit" for i in report.errors())


def test_tsgroup_hours():
    """The NEMO identity holds: sum of hours_yr across TSGROUP1 equals 8760."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _make_full_db(path)
        db = NemoDB(path)
        df = tsgroup_hours(db)
        assert "multiplier" in df.columns
        assert "hours_yr" in df.columns
        # Total hours across the year must equal 8760 for a consistent schema.
        total_hours = float(df["hours_yr"].sum())
        assert abs(total_hours - 8760.0) < 1e-6, f"got {total_hours}"


def test_timeslices_chronological_ordering():
    """timeslices() must sort by (tg1_order, tg2_order, lorder), not by
    lorder alone, to produce chronological dispatch ordering."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _make_full_db(path)
        db = NemoDB(path)
        from nemo_read import timeslices
        ts = timeslices(db)
        assert "tg1_order" in ts.columns
        assert "tg2_order" in ts.columns
        # Within each (tg1, tg2), lorder must be monotonically increasing.
        for (t1, t2), grp in ts.groupby(["tg1", "tg2"]):
            assert grp["lorder"].is_monotonic_increasing


def test_transmission_candidates_uses_min_year():
    """Candidates are lines with yconstruction > min(YEAR), not > max."""
    from nemo_read import transmission_candidates
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _make_full_db(path)
        # Add a candidate line with yconstruction within the model horizon.
        con = sqlite3.connect(path)
        # Ensure TransmissionLine table exists with the right schema.
        con.execute("""CREATE TABLE IF NOT EXISTS TransmissionLine (
            id TEXT PRIMARY KEY, n1 TEXT, n2 TEXT, f TEXT,
            maxflow REAL, reactance REAL, yconstruction REAL,
            capitalcost REAL, fixedcost REAL, variablecost REAL,
            operationallife INTEGER, efficiency REAL, interestrate REAL
        )""")
        # Insert one existing (yconstruction = earliest year) and one candidate.
        con.execute("INSERT INTO NODE (val, desc, r) VALUES ('NA', 'A', 'IDN')")
        con.execute("INSERT INTO NODE (val, desc, r) VALUES ('NB', 'B', 'MYS')")
        con.execute(
            "INSERT INTO TransmissionLine (id, n1, n2, f, yconstruction) "
            "VALUES (?, ?, ?, ?, ?)",
            ("TL_exist", "NA", "NB", "ELC", 2024.0),  # first model year
        )
        con.execute(
            "INSERT INTO TransmissionLine (id, n1, n2, f, yconstruction) "
            "VALUES (?, ?, ?, ?, ?)",
            ("TL_cand", "NA", "NB", "ELC", 2025.0),  # mid-horizon candidate
        )
        con.commit()
        con.close()
        db = NemoDB(path)
        cand = transmission_candidates(db)
        ids = set(cand["id"])
        assert "TL_cand" in ids
        assert "TL_exist" not in ids


def test_list_unused_technologies():
    from nemo_read import list_unused_technologies
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _make_full_db(path)
        # Insert an orphan tech (no parameter references it).
        con = sqlite3.connect(path)
        con.execute(
            "INSERT INTO TECHNOLOGY (val, desc) VALUES ('ORPHAN', 'Never used')"
        )
        con.commit()
        con.close()
        db = NemoDB(path)
        unused = list_unused_technologies(db)
        assert "ORPHAN" in set(unused["val"])


def test_validator_catches_unbounded_ccs():
    """Negative EmissionActivityRatio + negative EmissionsPenalty with no
    activity bound should raise a warning about unbounded profit."""
    from nemo_read import validate_scenario
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _make_full_db(path)
        con = sqlite3.connect(path)
        # Ensure the needed tables exist.
        con.execute("CREATE TABLE IF NOT EXISTS EMISSION "
                    "(val TEXT PRIMARY KEY, desc TEXT)")
        con.execute("CREATE TABLE IF NOT EXISTS EmissionActivityRatio ("
                    "id INTEGER PRIMARY KEY, r TEXT, t TEXT, e TEXT, "
                    "m TEXT, y TEXT, val REAL)")
        con.execute("CREATE TABLE IF NOT EXISTS EmissionsPenalty ("
                    "id INTEGER PRIMARY KEY, r TEXT, e TEXT, y TEXT, val REAL)")
        # Populate
        con.execute("INSERT OR IGNORE INTO EMISSION (val, desc) "
                    "VALUES ('CO2_seq', 'Sequestered CO2')")
        con.execute("INSERT OR IGNORE INTO TECHNOLOGY (val, desc) "
                    "VALUES ('CCS_TECH', 'CCS')")
        con.execute("INSERT INTO EmissionActivityRatio "
                    "(id, r, t, e, m, y, val) "
                    "VALUES (9991, 'IDN', 'CCS_TECH', 'CO2_seq', '1', '2024', -1.0)")
        con.execute("INSERT INTO EmissionsPenalty (id, r, e, y, val) "
                    "VALUES (9991, 'IDN', 'CO2_seq', '2024', -50.0)")
        con.commit()
        con.close()
        db = NemoDB(path)
        report = validate_scenario(db)
        found = any(i.category == "emissions"
                    and "unbounded" in i.message.lower()
                    for i in report.warnings())
        assert found, (
            f"expected unbounded-CCS warning, got: "
            f"{[(i.category, i.message) for i in report.issues]}"
        )


def main() -> int:
    test_leap_nemo_units_constants()
    test_units_for_common_entities()
    test_classify_technology_id()
    test_extract_leap_ids()
    test_validate_clean_db_passes()
    test_validate_catches_orphan_reference()
    test_validate_catches_year_split_sum()
    test_tsgroup_hours()
    test_timeslices_chronological_ordering()
    test_transmission_candidates_uses_min_year()
    test_list_unused_technologies()
    test_validator_catches_unbounded_ccs()
    print("All conventions and validation tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
