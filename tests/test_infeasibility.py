"""
Tests for the infeasibility analyser and the three bug fixes from pass 4:

    * dump_to_csv with a list of table names
    * dump_to_parquet with an include parameter
    * year-filter dtype coercion (str vs int)
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tests.test_nemo_read import _build_synthetic_db
from tests.test_extensions import _extend_db

from nemo_read import (
    NemoDB, check_scenario, dump_to_csv, dump_to_parquet,
    find_infeasibilities, get_parameter, ValidationReport,
)


def _full_db(path: Path) -> None:
    _build_synthetic_db(path)
    _extend_db(path)


# ---------------------------------------------------------------------------
# Bug fixes
# ---------------------------------------------------------------------------
def test_dump_to_csv_with_list():
    """include=[table names] should write only those files."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        db = NemoDB(path)
        out = Path(tmp) / "csv"
        written = dump_to_csv(db, out, include=["REGION", "YEAR"])
        assert set(written) == {"REGION", "YEAR"}
        files = [f.name for f in out.iterdir()]
        assert "dim_REGION.csv" in files
        assert "dim_YEAR.csv" in files
        assert len(files) == 2


def test_dump_to_csv_unknown_raises():
    """Unknown table names in include should raise KeyError."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        db = NemoDB(path)
        try:
            dump_to_csv(db, Path(tmp) / "csv",
                        include=["REGION", "NoSuchTable"])
        except KeyError:
            return  # expected
        raise AssertionError("expected KeyError for unknown include entry")


def test_dump_to_parquet_with_include():
    """dump_to_parquet must support include, symmetric with dump_to_csv."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        db = NemoDB(path)
        out = Path(tmp) / "out.parquet"
        p = dump_to_parquet(db, out, include=["REGION", "YEAR"])
        assert p.exists()
        assert p.stat().st_size > 0


def test_year_filter_accepts_string():
    """Year filter should work whether the user passes int or str values."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        db = NemoDB(path)
        cc_int = get_parameter(db, "CapitalCost",
                               apply_filters={"y": [2024]})
        cc_str = get_parameter(db, "CapitalCost",
                               apply_filters={"y": ["2024"]})
        assert len(cc_int) == len(cc_str), (
            f"int filter: {len(cc_int)} rows, "
            f"str filter: {len(cc_str)} rows — must agree"
        )
        # And both should return some rows (synthetic DB has CapitalCost for 2024).
        assert len(cc_int) > 0


# ---------------------------------------------------------------------------
# Infeasibility tool
# ---------------------------------------------------------------------------
def test_find_infeasibilities_clean_db():
    """A well-formed synthetic DB should produce no errors."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        db = NemoDB(path)
        rep = find_infeasibilities(db)
        assert rep.ok(), [i.message for i in rep.errors()]


def test_find_infeasibilities_bound_inversion():
    """Min > Max on capacity bounds must produce a bound_inversion error."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        con = sqlite3.connect(path)
        # Create tables if missing, insert conflicting bounds.
        con.execute("""
            CREATE TABLE IF NOT EXISTS TotalAnnualMinCapacity
            (id INTEGER PRIMARY KEY, r TEXT, t TEXT, y TEXT, val REAL)
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS TotalAnnualMaxCapacity
            (id INTEGER PRIMARY KEY, r TEXT, t TEXT, y TEXT, val REAL)
        """)
        con.execute(
            "INSERT INTO TotalAnnualMinCapacity (id, r, t, y, val) "
            "VALUES (1, 'IDN', 'PWRCOAL', '2024', 100.0)"
        )
        con.execute(
            "INSERT INTO TotalAnnualMaxCapacity (id, r, t, y, val) "
            "VALUES (1, 'IDN', 'PWRCOAL', '2024', 50.0)"
        )
        con.commit()
        con.close()
        db = NemoDB(path)
        rep = find_infeasibilities(db)
        categories = [i.category for i in rep.errors()]
        assert "bound_inversion" in categories, (
            f"expected bound_inversion error, got: {categories}"
        )


def test_find_infeasibilities_emission_excess():
    """Exogenous emissions > AnnualEmissionLimit is infeasible per NEMO docs."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        con = sqlite3.connect(path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS AnnualExogenousEmission
            (id INTEGER PRIMARY KEY, r TEXT, e TEXT, y TEXT, val REAL)
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS AnnualEmissionLimit
            (id INTEGER PRIMARY KEY, r TEXT, e TEXT, y TEXT, val REAL)
        """)
        con.execute(
            "INSERT INTO AnnualExogenousEmission (id, r, e, y, val) "
            "VALUES (1, 'IDN', 'CO2', '2024', 1000000.0)"
        )
        con.execute(
            "INSERT INTO AnnualEmissionLimit (id, r, e, y, val) "
            "VALUES (1, 'IDN', 'CO2', '2024', 500000.0)"
        )
        con.commit()
        con.close()
        db = NemoDB(path)
        rep = find_infeasibilities(db)
        categories = [i.category for i in rep.errors()]
        assert "emission_limit" in categories


def test_find_infeasibilities_min_util_over_availability():
    """MinimumUtilization > AvailabilityFactor is infeasible for that
    (r, t, l, y). Mirrors the real pattern found in the SE Asia DB."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        con = sqlite3.connect(path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS MinimumUtilization
            (id INTEGER PRIMARY KEY, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS AvailabilityFactor
            (id INTEGER PRIMARY KEY, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)
        """)
        # Solar: MinUtil > 0 at a nighttime slice where AF = 0
        con.execute(
            "INSERT INTO MinimumUtilization (id, r, t, l, y, val) "
            "VALUES (1, 'IDN', 'PWRSOL', 'L1', '2024', 0.001)"
        )
        con.execute(
            "INSERT INTO AvailabilityFactor (id, r, t, l, y, val) "
            "VALUES (1, 'IDN', 'PWRSOL', 'L1', '2024', 0.0)"
        )
        con.commit()
        con.close()
        db = NemoDB(path)
        rep = find_infeasibilities(db)
        categories = [i.category for i in rep.errors()]
        assert "utilization" in categories


def test_find_infeasibilities_min_share_sum():
    """Sum of MinShareProduction > 1.0 makes the production mix infeasible."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        con = sqlite3.connect(path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS MinShareProduction
            (id INTEGER PRIMARY KEY, r TEXT, t TEXT, f TEXT, y TEXT, val REAL)
        """)
        con.execute(
            "INSERT INTO MinShareProduction (id, r, t, f, y, val) "
            "VALUES (1, 'IDN', 'PWRCOAL', 'ELC', '2024', 0.6)"
        )
        con.execute(
            "INSERT INTO MinShareProduction (id, r, t, f, y, val) "
            "VALUES (2, 'IDN', 'PWRSOL', 'ELC', '2024', 0.6)"
        )  # Sum = 1.2 > 1.0
        con.commit()
        con.close()
        db = NemoDB(path)
        rep = find_infeasibilities(db)
        categories = [i.category for i in rep.errors()]
        assert "share_constraints" in categories


def test_check_scenario_dedup():
    """check_scenario merges validate + find_infeasibilities and dedupes
    overlapping findings (e.g. both include the MinStorageCharge check)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        db = NemoDB(path)
        # Clean DB should merge without duplicating known info/warning
        # categories.
        rep = check_scenario(db)
        assert isinstance(rep, ValidationReport)
        # Identical (severity, category, table, message) tuples must appear
        # at most once.
        keys = [(i.severity, i.category, i.table, i.message) for i in rep.issues]
        assert len(keys) == len(set(keys))


def test_validation_report_extend():
    """ValidationReport.extend merges another report in-place."""
    from nemo_read import validate_scenario
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _full_db(path)
        db = NemoDB(path)
        a = validate_scenario(db)
        b = find_infeasibilities(db)
        start_len = len(a.issues)
        a.extend(b)
        assert len(a.issues) == start_len + len(b.issues)


def main() -> int:
    test_dump_to_csv_with_list()
    test_dump_to_csv_unknown_raises()
    test_dump_to_parquet_with_include()
    test_year_filter_accepts_string()
    test_find_infeasibilities_clean_db()
    test_find_infeasibilities_bound_inversion()
    test_find_infeasibilities_emission_excess()
    test_find_infeasibilities_min_util_over_availability()
    test_find_infeasibilities_min_share_sum()
    test_check_scenario_dedup()
    test_validation_report_extend()
    print("All infeasibility and bug-fix tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
