"""
Tests for the offline LP-column decoder.

Covers:
    * Layout sizes match the variable-axis sizes for each family.
    * Single-column decode matches a hand calculation at the
      first column, the last column, and an interior column of a
      known variable family.
    * Conditional gates: vrateofdemandnn (varstosave-driven),
      vnumberofnewtechnologyunits (CapacityOfOneTechnologyUnit-driven).
    * Past-the-dense-prefix columns return ``dense=False`` rather
      than crashing.
    * Negative or zero column raises ValueError.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tests.test_nemo_read import _build_synthetic_db

from nemo_read import (
    NemoDB, decode_lp_column, enumerate_dense_blocks,
    NEMO_DEFAULT_VARSTOSAVE,
)


def test_layout_sizes_synthetic():
    """Synthetic DB has R=2, T=2, F=2, S=0, L=4, Y=3 — verify the sizes
    are products of those axis lengths."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        db = NemoDB(path)
        layout = enumerate_dense_blocks(db)
        sizes = dict(zip(layout["variable"], layout["size"]))
        # vdemandnn[r,l,f,y]    = 2*4*2*3 = 48
        # vdemandannualnn[r,f,y] = 2*2*3   = 12
        assert sizes["vdemandnn"] == 48
        assert sizes["vdemandannualnn"] == 12
        # |S|=0 ⇒ every storage variable has size 0
        assert sizes["vstorageleveltsendnn"] == 0
        assert sizes["vnewstoragecapacity"] == 0
        # vnewcapacity[r,t,y]   = 2*2*3   = 12
        assert sizes["vnewcapacity"] == 12
        assert sizes["vaccumulatednewcapacity"] == 12
        assert sizes["vtotalcapacityannual"] == 12


def test_decode_first_column():
    """Column 1 should be vdemandnn at the leftmost element of every
    axis. Synthetic FUEL is {'COA','ELC'} (lex by PK) so f[0]='COA';
    REGION is {'IDN','MYS'} so r[0]='IDN'."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        db = NemoDB(path)
        result = decode_lp_column(db, 1)
        assert result.variable == "vdemandnn"
        assert result.offset == 1
        assert result.dense is True
        # leftmost-fastest: first index in every axis
        assert result.indices["r"] == "IDN"
        assert result.indices["l"] == "L1"
        assert result.indices["f"] == "COA"
        assert result.indices["y"] == "2024"


def test_decode_last_column_of_block():
    """vdemandnn ends at column 48; last column = (last in every axis).
    R=2 (MYS), L=4 (L4), F=2 (ELC), Y=3 (2026)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        db = NemoDB(path)
        result = decode_lp_column(db, 48)
        assert result.variable == "vdemandnn"
        assert result.offset == 48
        assert result.indices["r"] == "MYS"
        assert result.indices["l"] == "L4"
        assert result.indices["f"] == "ELC"
        assert result.indices["y"] == "2026"


def test_decode_interior_capacity_column():
    """Column 73 = first column of vaccumulatednewcapacity in synthetic
    layout (vdemandnn 1..48, vdemandannualnn 49..60, storage 0..0,
    vnewcapacity 61..72, vaccumulatednewcapacity 73..84). First column =
    (IDN, PWRCOAL, 2024)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        db = NemoDB(path)
        result = decode_lp_column(db, 73)
        assert result.variable == "vaccumulatednewcapacity"
        assert result.offset == 1
        assert result.indices == {"r": "IDN", "t": "PWRCOAL", "y": "2024"}
        # descriptions populated for r and t since they have desc columns
        assert result.descriptions.get("IDN") == "Indonesia"
        assert result.descriptions.get("PWRCOAL") == "Coal power"


def test_decode_with_vrateofdemandnn_in_varstosave():
    """If 'vrateofdemandnn' is in varstosave, it's created BEFORE
    vdemandnn and shifts every later column by R*L*F*Y."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        db = NemoDB(path)
        vts = list(NEMO_DEFAULT_VARSTOSAVE) + ["vrateofdemandnn"]
        layout = enumerate_dense_blocks(db, varstosave=vts)
        first = layout.iloc[0]
        assert first["variable"] == "vrateofdemandnn"
        assert first["start"] == 1
        # vrateofdemandnn = R*L*F*Y = 48 columns; vdemandnn now starts at 49
        assert int(first["end"]) == 48
        vdemand_row = layout[layout["variable"] == "vdemandnn"].iloc[0]
        assert int(vdemand_row["start"]) == 49


def test_decode_with_capacityofonetechnologyunit():
    """If CapacityOfOneTechnologyUnit has a nonzero row,
    vnumberofnewtechnologyunits gets created (line 551) and pushes
    later capacity columns down by R*T*Y."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        # Create the table and inject a nonzero row
        con = sqlite3.connect(path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS CapacityOfOneTechnologyUnit
            (id INTEGER PRIMARY KEY, r TEXT, t TEXT, y TEXT, val REAL)
        """)
        con.execute(
            "INSERT INTO CapacityOfOneTechnologyUnit (r, t, y, val) "
            "VALUES ('IDN', 'PWRSOL', '2024', 0.5)"
        )
        con.commit()
        con.close()

        db = NemoDB(path)
        layout = enumerate_dense_blocks(db)
        names = layout["variable"].tolist()
        assert "vnumberofnewtechnologyunits" in names
        # vnewcapacity must come AFTER vnumberofnewtechnologyunits
        idx_n = names.index("vnumberofnewtechnologyunits")
        idx_new = names.index("vnewcapacity")
        assert idx_n < idx_new


def test_decode_past_dense_prefix():
    """Columns beyond vtotalcapacityannual aren't decodable from SQLite
    alone — should return dense=False with the residual offset."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        db = NemoDB(path)
        layout = enumerate_dense_blocks(db)
        last = int(layout["end"].max())          # last dense column
        result = decode_lp_column(db, last + 100)
        assert result.dense is False
        assert result.indices == {}
        assert result.offset == 100              # offset past dense end


def test_decode_invalid_column_raises():
    """column < 1 must raise ValueError."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        db = NemoDB(path)
        for bad in (0, -1, -100):
            try:
                decode_lp_column(db, bad)
            except ValueError:
                continue
            raise AssertionError(f"expected ValueError for column={bad}")


def test_decode_calcyears_filter_shrinks_year_axis():
    """Passing calcyears must limit the YEAR axis used for axis sizing."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        db = NemoDB(path)
        # Without filter: vdemandnn = 48
        full = enumerate_dense_blocks(db)
        size_full = int(full[full["variable"] == "vdemandnn"]["size"].iloc[0])
        # With a 1-year filter: 2*4*2*1 = 16
        narrow = enumerate_dense_blocks(db, calcyears=["2024"])
        size_narrow = int(
            narrow[narrow["variable"] == "vdemandnn"]["size"].iloc[0]
        )
        assert size_full == 48
        assert size_narrow == 16


def main() -> int:
    test_layout_sizes_synthetic()
    test_decode_first_column()
    test_decode_last_column_of_block()
    test_decode_interior_capacity_column()
    test_decode_with_vrateofdemandnn_in_varstosave()
    test_decode_with_capacityofonetechnologyunit()
    test_decode_past_dense_prefix()
    test_decode_invalid_column_raises()
    test_decode_calcyears_filter_shrinks_year_axis()
    print("All LP-column decoder tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
