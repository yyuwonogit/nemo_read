"""
Tests for the new custom-constraint and slack-detection features, plus
regression tests for the two bugs found against NEMO_25.sqlite:

    * TransmissionModelingEnabled failing in get_parameter because the
      value column is `type`, not `val`.
    * ReserveMargin's xarray export silently shrinking to 10 regions
      when the DB has 11 but ReserveMargin only has data for 10.

Each regression is documented inline.
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tests.test_nemo_read import _build_synthetic_db             # reuse builder

from nemo_read import (
    NemoDB,
    detect_slack_technologies,
    get_custom_constraint,
    get_parameter,
    inspect_scenario,
    list_custom_constraints,
    parameter_to_dataarray,
    slack_technology_ids,
)


def _extend_db(path: Path) -> None:
    """Add to the base synthetic DB:
       - a __NEMOcc custom constraint table
       - a slack tech (Unserved)
       - a high-residual-capacity pseudo-tech
       - ReserveMargin data for only 1 of 2 regions
       - TransmissionModelingEnabled rows (value column = `type`)
    """
    con = sqlite3.connect(path)
    cur = con.cursor()

    # Add Unserved tech and a 10^12 pseudo-tech to TECHNOLOGY.
    cur.executemany(
        "INSERT OR IGNORE INTO TECHNOLOGY (val, desc) VALUES (?, ?)",
        [("Unserved", "Unserved"), ("P99999", "Fossil Liquid Supply")],
    )

    # High capital cost on Unserved (slack by cost).
    cur.execute("INSERT INTO CapitalCost (id, r, t, y, val) "
                "VALUES (9991, 'IDN', 'Unserved', '2024', 1000000.0)")

    # ResidualCapacity table + slack-high row.
    cur.execute(
        "CREATE TABLE IF NOT EXISTS ResidualCapacity "
        "(id INTEGER PRIMARY KEY, r TEXT, t TEXT, y TEXT, val REAL)"
    )
    cur.execute("INSERT INTO ResidualCapacity (id, r, t, y, val) "
                "VALUES (991, 'IDN', 'P99999', '2024', 1e12)")

    # Add ReserveMargin table + data for IDN only (skip MYS), no default.
    cur.execute(
        "CREATE TABLE ReserveMargin (id INTEGER PRIMARY KEY, r TEXT, "
        "f TEXT, y TEXT, val REAL)"
    )
    cur.execute("INSERT INTO ReserveMargin (id, r, f, y, val) "
                "VALUES (1, 'IDN', 'ELC', '2024', 1.15)")

    # ReserveMarginTagTechnology: tag at least one technology so the
    # reserve requirement is satisfiable.
    cur.execute(
        "CREATE TABLE ReserveMarginTagTechnology (id INTEGER PRIMARY KEY, "
        "r TEXT, t TEXT, f TEXT, y TEXT, val REAL)"
    )
    cur.execute("INSERT INTO ReserveMarginTagTechnology "
                "(id, r, t, f, y, val) "
                "VALUES (1, 'IDN', 'PWRSOL', 'ELC', '2024', 1.0)")

    # TransmissionModelingEnabled — value col is `type`, not `val`.
    cur.execute(
        "CREATE TABLE TransmissionModelingEnabled ("
        "id INTEGER PRIMARY KEY, r TEXT, f TEXT, y TEXT, type INTEGER DEFAULT 1)"
    )
    cur.execute("INSERT INTO TransmissionModelingEnabled (id, r, f, y, type) "
                "VALUES (1, 'IDN', 'ELC', '2024', 3)")

    # __NEMOcc custom constraint with the canonical (id, r, bid, eid, y, val) shape.
    cur.execute(
        'CREATE TABLE "RenewableTarget__NEMOcc" '
        "(id INTEGER PRIMARY KEY, r TEXT, bid TEXT, eid TEXT, y TEXT, val REAL)"
    )
    cur.executemany(
        'INSERT INTO "RenewableTarget__NEMOcc" (id, r, bid, eid, y, val) '
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "IDN", "1201", "-1", "2024", 0.25),
            (2, "IDN", "1201", "-1", "2025", 0.30),
            (3, "MYS", "1201", "-1", "2024", 0.20),
        ],
    )

    con.commit()
    con.close()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)                               # baseline DB
        _extend_db(path)                                        # feature coverage

        db = NemoDB(path)

        # --- Regression: TransmissionModelingEnabled (value column = `type`)
        tme = get_parameter(db, "TransmissionModelingEnabled")
        assert len(tme) >= 1
        assert "type" in tme.columns, f"cols={list(tme.columns)}"

        # --- Regression: ReserveMargin DataArray covers both regions
        # The DB has 2 regions (IDN, MYS) but only IDN has data. The
        # DataArray should still span 2 regions, with NaN for MYS.
        rm = parameter_to_dataarray(db, "ReserveMargin")
        assert "r" in rm.dims
        region_count = rm.sizes["r"]
        assert region_count == 2, f"expected 2 regions, got {region_count}"

        # --- Custom constraints
        cc = list_custom_constraints(db)
        assert "RenewableTarget" in set(cc["short_name"])
        assert cc.loc[cc["short_name"] == "RenewableTarget", "rows"].iloc[0] == 3

        full = get_custom_constraint(db, "RenewableTarget")
        assert set(full["r"]) == {"IDN", "MYS"}
        assert full["y"].dtype.name == "Int64"

        # Also accept the full suffixed name.
        also = get_custom_constraint(db, "RenewableTarget__NEMOcc")
        assert len(also) == 3

        # --- Slack detection
        slk = detect_slack_technologies(db)
        ids = set(slk["t"])
        assert "Unserved" in ids, f"Unserved not detected: {ids}"
        assert "P99999" in ids, f"P99999 not detected: {ids}"
        # reason column joins matched criteria
        unserved_reason = slk.loc[slk["t"] == "Unserved", "reason"].iloc[0]
        assert "capital_cost" in unserved_reason
        assert "name_match" in unserved_reason

        # slack_technology_ids is the convenience wrapper.
        assert set(slack_technology_ids(db)) == ids

        # --- inspect_scenario wires everything together
        ov = inspect_scenario(db)
        assert ov["calculation_state"] in ("pre-calculation", "post-calculation")
        assert not ov["custom_constraints"].empty
        assert not ov["slack_technologies"].empty
        # __NEMOcc tables should not appear in unknown_tables any more.
        assert "RenewableTarget__NEMOcc" not in ov["unknown_tables"]

        print("All extension tests passed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
