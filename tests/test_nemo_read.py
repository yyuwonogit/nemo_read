"""
Smoke test: build a minimal NEMO-shaped SQLite database from scratch and
run the library against it. Verifies the schema encoding, parameter
default reconstruction, result reading, and xarray export paths.

Not an exhaustive unit-test suite; enough to catch gross breakage.

Run:
    python -m tests.test_nemo_read
"""

from __future__ import annotations
import os                                                     # fs
import sqlite3                                                # build synthetic DB
import sys                                                    # path fix for local run
import tempfile                                               # temp db location
from pathlib import Path

# Make the scripts directory importable when running as a plain script.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                          # add scripts/

import numpy as np                                            # data
import pandas as pd                                           # data

from nemo_read import (
    NemoDB, inspect_scenario, print_overview,
    regions, fuels, technologies, years, timeslices,
    get_parameter, get_parameter_raw, list_populated_parameters,
    get_result, list_present_results, capacity_stack,
    year_split, weighted_by_yearsplit,
    parameter_to_dataarray, result_to_dataarray,
    DIMENSIONS, PARAMETERS, RESULT_VARIABLES, TARGET_DB_VERSION,
)


def _build_synthetic_db(path: Path) -> None:
    """Create a minimal scenario DB matching NEMO v11 structure."""
    con = sqlite3.connect(path)                               # open rw
    cur = con.cursor()                                        # helper

    # Version
    cur.execute("CREATE TABLE Version (version INTEGER PRIMARY KEY)")
    cur.execute("INSERT INTO Version VALUES (?)", (TARGET_DB_VERSION,))

    # DefaultParams
    cur.execute(
        "CREATE TABLE DefaultParams (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "tablename TEXT NOT NULL, val REAL NOT NULL)"
    )
    cur.execute("CREATE UNIQUE INDEX DefaultParams_tablename_unique "
                "ON DefaultParams(tablename)")
    # Register a default for CapitalCost
    cur.execute("INSERT INTO DefaultParams (tablename, val) VALUES (?, ?)",
                ("CapitalCost", 1000.0))

    # Dimensions
    cur.execute("CREATE TABLE REGION (val TEXT PRIMARY KEY, desc TEXT)")
    cur.executemany("INSERT INTO REGION VALUES (?, ?)",
                    [("IDN", "Indonesia"), ("MYS", "Malaysia")])

    cur.execute("CREATE TABLE FUEL (val TEXT PRIMARY KEY, desc TEXT)")
    cur.executemany("INSERT INTO FUEL VALUES (?, ?)",
                    [("ELC", "Electricity"), ("COA", "Coal")])

    cur.execute("CREATE TABLE TECHNOLOGY (val TEXT PRIMARY KEY, desc TEXT)")
    cur.executemany("INSERT INTO TECHNOLOGY VALUES (?, ?)",
                    [("PWRCOAL", "Coal power"), ("PWRSOL", "Solar PV")])

    cur.execute("CREATE TABLE EMISSION (val TEXT PRIMARY KEY, desc TEXT)")
    cur.execute("INSERT INTO EMISSION VALUES (?, ?)", ("CO2", "Carbon dioxide"))

    cur.execute("CREATE TABLE MODE_OF_OPERATION (val TEXT PRIMARY KEY, desc TEXT)")
    cur.execute("INSERT INTO MODE_OF_OPERATION VALUES (?, ?)", ("1", "mode 1"))

    cur.execute(
        "CREATE TABLE STORAGE (val TEXT PRIMARY KEY, desc TEXT, "
        "netzeroyear INTEGER NOT NULL DEFAULT 1, "
        "netzerotg1 INTEGER NOT NULL DEFAULT 0, "
        "netzerotg2 INTEGER NOT NULL DEFAULT 0)"
    )

    cur.execute("CREATE TABLE REGIONGROUP (val TEXT PRIMARY KEY, desc TEXT)")

    cur.execute("CREATE TABLE YEAR (val TEXT PRIMARY KEY, desc TEXT)")
    cur.executemany("INSERT INTO YEAR VALUES (?, ?)",
                    [(str(y), None) for y in (2024, 2025, 2026)])

    cur.execute("CREATE TABLE TIMESLICE (val TEXT PRIMARY KEY, desc TEXT)")
    cur.executemany("INSERT INTO TIMESLICE VALUES (?, ?)",
                    [(f"L{i}", None) for i in range(1, 5)])

    cur.execute(
        "CREATE TABLE TSGROUP1 (name TEXT PRIMARY KEY, desc TEXT, "
        "\"order\" INTEGER NOT NULL UNIQUE, multiplier REAL NOT NULL DEFAULT 1)"
    )
    # Annual group: 4 slices × 1 day-type mult × tg1 mult must equal 8760.
    # With 4 slices and tg2.multiplier=1, tg1.multiplier = 2190.
    cur.execute('INSERT INTO TSGROUP1 VALUES ("Annual", NULL, 1, 2190.0)')

    cur.execute(
        "CREATE TABLE TSGROUP2 (name TEXT PRIMARY KEY, desc TEXT, "
        "\"order\" INTEGER NOT NULL UNIQUE, multiplier REAL NOT NULL DEFAULT 1)"
    )
    cur.execute('INSERT INTO TSGROUP2 VALUES ("Day", NULL, 1, 1.0)')

    cur.execute(
        "CREATE TABLE LTsGroup (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "l TEXT UNIQUE, lorder INTEGER, tg2 TEXT, tg1 TEXT)"
    )
    cur.executemany(
        "INSERT INTO LTsGroup (l, lorder, tg2, tg1) VALUES (?, ?, ?, ?)",
        [(f"L{i}", i, "Day", "Annual") for i in range(1, 5)]
    )

    cur.execute("CREATE TABLE NODE (val TEXT PRIMARY KEY, desc TEXT, r TEXT)")

    # Parameters: YearSplit, CapitalCost, SpecifiedAnnualDemand
    cur.execute(
        "CREATE TABLE YearSplit (id INTEGER PRIMARY KEY, l TEXT, y TEXT, val REAL)"
    )
    cur.executemany(
        "INSERT INTO YearSplit (id, l, y, val) VALUES (?, ?, ?, ?)",
        [(idx, f"L{(idx % 4) + 1}", str(2024 + (idx // 4)), 0.25)
         for idx in range(12)]
    )

    cur.execute(
        "CREATE TABLE CapitalCost (id INTEGER PRIMARY KEY, r TEXT, t TEXT, "
        "y TEXT, val REAL)"
    )
    # Only one row stored; the rest should come via default overlay (1000).
    cur.execute("INSERT INTO CapitalCost (id, r, t, y, val) VALUES (1, 'IDN', 'PWRSOL', '2024', 750.0)")

    cur.execute(
        "CREATE TABLE SpecifiedAnnualDemand (id INTEGER PRIMARY KEY, r TEXT, "
        "f TEXT, y TEXT, val REAL)"
    )
    cur.executemany(
        "INSERT INTO SpecifiedAnnualDemand (id, r, f, y, val) VALUES (?, ?, ?, ?, ?)",
        [(1, "IDN", "ELC", "2024", 300.0), (2, "IDN", "ELC", "2025", 315.0),
         (3, "MYS", "ELC", "2024", 150.0), (4, "MYS", "ELC", "2025", 160.0)]
    )

    # A result table with two solves
    cur.execute(
        "CREATE TABLE vnewcapacity (r TEXT, t TEXT, y TEXT, val REAL, solvedtm TEXT)"
    )
    cur.executemany(
        "INSERT INTO vnewcapacity VALUES (?, ?, ?, ?, ?)",
        [
            ("IDN", "PWRSOL", "2024", 2.5, "2026-01-01 10:00:00"),
            ("IDN", "PWRSOL", "2025", 3.0, "2026-01-01 10:00:00"),
            ("MYS", "PWRSOL", "2024", 1.0, "2026-01-01 10:00:00"),
            # Later solve
            ("IDN", "PWRSOL", "2024", 2.8, "2026-02-15 11:00:00"),
            ("IDN", "PWRSOL", "2025", 3.3, "2026-02-15 11:00:00"),
        ]
    )

    con.commit()                                              # persist
    con.close()                                               # close handle


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:                # temp workspace
        db_path = Path(tmp) / "scenario.sqlite"               # path
        _build_synthetic_db(db_path)                          # populate

        # Open read-only via our wrapper.
        db = NemoDB(db_path)                                  # constructor also checks version
        assert db.version == TARGET_DB_VERSION, f"version {db.version}"

        # Dimensions.
        r = regions(db); assert set(r["val"]) == {"IDN", "MYS"}
        f_ = fuels(db); assert "ELC" in set(f_["val"])
        t = technologies(db); assert "PWRSOL" in set(t["val"])
        y = years(db); assert y["val"].dtype.name == "Int64"
        ts = timeslices(db); assert len(ts) == 4 and "lorder" in ts.columns

        # Parameter raw vs defaults: CapitalCost has 1 stored row, default 1000.
        raw = get_parameter_raw(db, "CapitalCost")
        assert len(raw) == 1 and float(raw["val"].iloc[0]) == 750.0
        with_def = get_parameter(db, "CapitalCost")
        # Grid = 2 regions × 2 techs × 3 years = 12 rows.
        assert len(with_def) == 12, len(with_def)
        # The stored (IDN, PWRSOL, 2024) row retains 750.0 after overlay.
        subset = with_def[(with_def["r"] == "IDN") & (with_def["t"] == "PWRSOL") & (with_def["y"] == 2024)]
        assert float(subset["val"].iloc[0]) == 750.0
        # All others = 1000 default.
        others = with_def[~((with_def["r"] == "IDN") & (with_def["t"] == "PWRSOL") & (with_def["y"] == 2024))]
        assert (others["val"] == 1000.0).all()

        # YearSplit + timeslice helpers
        ys = year_split(db)
        assert "hours" in ys.columns and np.isclose(ys["hours"].iloc[0], 0.25 * 8760)

        # Results: latest solve gets picked up by default.
        latest = get_result(db, "vnewcapacity")                # should filter to 2026-02-15
        assert len(latest) == 2, len(latest)
        explicit = get_result(db, "vnewcapacity", solvedtm="2026-01-01 10:00:00")
        assert len(explicit) == 3

        # Capacity stack: only vnewcapacity is present but function still works.
        stk = capacity_stack(db)
        assert "kind" in stk.columns and (stk["kind"] == "new").all()

        # Inspect scenario.
        ov = inspect_scenario(db)
        assert ov["version"] == TARGET_DB_VERSION
        assert not ov["version_mismatch"]
        assert "vnewcapacity" in set(ov["results"]["variable"])

        # xarray exports.
        da_par = parameter_to_dataarray(db, "CapitalCost")
        assert tuple(da_par.dims) == ("r", "t", "y")
        assert da_par.shape == (2, 2, 3)
        # IDN/PWRSOL/2024 should be 750.
        assert float(da_par.sel(r="IDN", t="PWRSOL", y=2024)) == 750.0

        da_res = result_to_dataarray(db, "vnewcapacity")
        assert "r" in da_res.dims and "t" in da_res.dims and "y" in da_res.dims

        # Pretty print for a manual eyeball.
        print("─" * 60)
        print_overview(db)
        print("─" * 60)
        print("All assertions passed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
