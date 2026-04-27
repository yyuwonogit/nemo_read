"""Tests for result-side traceback helpers (0.6.1)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from nemo_read import (
    BOUND_ABSENT, BOUND_FREE, BOUND_HIT_LOWER, BOUND_HIT_UPPER,
    BoundCheck, CostBreakdown, LeapAreaContext, NemoDB, RESULT_DEPENDENCIES,
    ResultDependency, ResultTrace, result_dependency,
    trace_cost, trace_result,
)


FIXTURE = Path(__file__).parent / "fixtures" / "leap_export"


def _make_synthetic_db(path: Path) -> None:
    """Minimal NEMO-shaped DB covering the rows the trace helpers read.

    Just enough for trace_result / trace_cost to have something to consume;
    not a full NEMO schema.
    """
    con = sqlite3.connect(path)
    cur = con.cursor()

    cur.execute("CREATE TABLE Version (version INTEGER PRIMARY KEY)")
    cur.execute("INSERT INTO Version (version) VALUES (11)")

    # Parameters used as inputs or bounds
    cur.execute("CREATE TABLE CapitalCost (id INTEGER PRIMARY KEY, r TEXT, t TEXT, y TEXT, val REAL)")
    cur.execute("CREATE TABLE ResidualCapacity (id INTEGER PRIMARY KEY, r TEXT, t TEXT, y TEXT, val REAL)")
    cur.execute("CREATE TABLE OperationalLife (id INTEGER PRIMARY KEY, r TEXT, t TEXT, val REAL)")
    cur.execute("CREATE TABLE TotalAnnualMaxCapacity (id INTEGER PRIMARY KEY, r TEXT, t TEXT, y TEXT, val REAL)")
    cur.execute("CREATE TABLE TotalAnnualMinCapacity (id INTEGER PRIMARY KEY, r TEXT, t TEXT, y TEXT, val REAL)")

    # Rows
    cur.executemany(
        "INSERT INTO CapitalCost (r, t, y, val) VALUES (?, ?, ?, ?)",
        [("R1", "P11942", "2030", 1200.0)],
    )
    cur.executemany(
        "INSERT INTO ResidualCapacity (r, t, y, val) VALUES (?, ?, ?, ?)",
        [("R1", "P11942", "2030", 2.0)],
    )
    cur.executemany(
        "INSERT INTO OperationalLife (r, t, val) VALUES (?, ?, ?)",
        [("R1", "P11942", 50.0)],
    )
    cur.executemany(
        "INSERT INTO TotalAnnualMaxCapacity (r, t, y, val) VALUES (?, ?, ?, ?)",
        [("R1", "P11942", "2030", 10.0)],
    )
    cur.executemany(
        "INSERT INTO TotalAnnualMinCapacity (r, t, y, val) VALUES (?, ?, ?, ?)",
        [("R1", "P11942", "2030", 1.0)],
    )

    # Result variable tables
    for name in [
        "vnewcapacity", "vtotalcapacityannual",
        "vtotaldiscountedcost", "vdiscountedcapitalinvestment",
        "vdiscountedoperatingcost", "vdiscountedtechnologyemissionspenalty",
        "vdiscountedsalvagevalue", "vfinancecost",
    ]:
        cur.execute(
            f"CREATE TABLE {name} (id INTEGER PRIMARY KEY, "
            f"r TEXT, t TEXT, y TEXT, val REAL, solvedtm TEXT)"
        )

    # vtotalcapacityannual hits the upper bound (10.0)
    cur.execute(
        "INSERT INTO vtotalcapacityannual (r, t, y, val, solvedtm) VALUES (?, ?, ?, ?, ?)",
        ("R1", "P11942", "2030", 10.0, "2026-04-23 12:00:00"),
    )
    cur.execute(
        "INSERT INTO vnewcapacity (r, t, y, val, solvedtm) VALUES (?, ?, ?, ?, ?)",
        ("R1", "P11942", "2030", 8.0, "2026-04-23 12:00:00"),
    )
    # Cost-stream breakdown
    cur.execute(
        "INSERT INTO vtotaldiscountedcost (r, y, val, solvedtm) VALUES (?, ?, ?, ?)",
        ("R1", "2030", 10000.0, "2026-04-23 12:00:00"),
    )
    for table, v in [
        ("vdiscountedcapitalinvestment", 6000.0),
        ("vdiscountedoperatingcost", 3000.0),
        ("vdiscountedtechnologyemissionspenalty", 2000.0),
        ("vdiscountedsalvagevalue", 1000.0),
        ("vfinancecost", 0.0),
    ]:
        cur.execute(
            f"INSERT INTO {table} (r, t, y, val, solvedtm) VALUES (?, ?, ?, ?, ?)",
            ("R1", "P11942", "2030", v, "2026-04-23 12:00:00"),
        )

    # vtotaldiscountedcost table structure needs to accept rows without `t`,
    # but we cheated above. Adjust schema — drop and recreate with proper shape.
    cur.execute("DROP TABLE vtotaldiscountedcost")
    cur.execute(
        "CREATE TABLE vtotaldiscountedcost (id INTEGER PRIMARY KEY, "
        "r TEXT, y TEXT, val REAL, solvedtm TEXT)"
    )
    cur.execute(
        "INSERT INTO vtotaldiscountedcost (r, y, val, solvedtm) VALUES (?, ?, ?, ?)",
        ("R1", "2030", 10000.0, "2026-04-23 12:00:00"),
    )

    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# RESULT_DEPENDENCIES sanity
# ---------------------------------------------------------------------------
def test_result_dependencies_has_key_entries():
    must_have = [
        "vtotalcapacityannual", "vnewcapacity", "vannualemissions",
        "vtotaldiscountedcost", "vproductionbytechnologyannual",
        "vrateofactivity", "vcapitalinvestment",
    ]
    for name in must_have:
        assert name in RESULT_DEPENDENCIES, f"{name} missing"
        dep = RESULT_DEPENDENCIES[name]
        assert isinstance(dep, ResultDependency)


def test_result_dependency_lookup():
    dep = result_dependency("vtotalcapacityannual")
    assert dep is not None
    assert "ResidualCapacity" in dep.inputs
    assert "vaccumulatednewcapacity" in dep.upstream_results
    assert "TotalAnnualMaxCapacity" in dep.upper_bounds


def test_result_dependency_unknown_returns_none():
    assert result_dependency("not_a_real_table") is None


# ---------------------------------------------------------------------------
# trace_result
# ---------------------------------------------------------------------------
def test_trace_result_detects_upper_bound(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_synthetic_db(db_path)
    db = NemoDB(db_path)

    trace = trace_result(
        db, "vtotalcapacityannual",
        {"r": "R1", "t": "P11942", "y": "2030"},
    )
    assert isinstance(trace, ResultTrace)
    assert trace.value == 10.0
    assert trace.bound is not None
    assert trace.bound.state == BOUND_HIT_UPPER
    assert trace.bound.bound_table == "TotalAnnualMaxCapacity"
    assert trace.bound.bound_value == 10.0


def test_trace_result_with_context_adds_ui_hints(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_synthetic_db(db_path)
    db = NemoDB(db_path)
    ctx = LeapAreaContext.from_export(FIXTURE)

    trace = trace_result(
        db, "vtotalcapacityannual",
        {"r": "R1", "t": "P11942", "y": "2030"},
        context=ctx,
    )
    # ResidualCapacity is listed as an input; it should carry a UI hint.
    residual = [t for t in trace.contributing_inputs if t.parameter == "ResidualCapacity"]
    assert residual and residual[0].row_value == 2.0
    assert residual[0].leap_ui_hint is not None
    assert "Pumped Hydro" in residual[0].leap_ui_hint


def test_trace_result_returns_empty_for_unknown_table(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_synthetic_db(db_path)
    db = NemoDB(db_path)
    trace = trace_result(db, "not_a_real_table", {"r": "R1"})
    assert trace.dependency is None
    assert trace.contributing_inputs == []


def test_trace_result_upstream_results_list(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_synthetic_db(db_path)
    db = NemoDB(db_path)
    trace = trace_result(
        db, "vtotalcapacityannual",
        {"r": "R1", "t": "P11942", "y": "2030"},
    )
    assert "vaccumulatednewcapacity" in trace.upstream_results


# ---------------------------------------------------------------------------
# trace_cost
# ---------------------------------------------------------------------------
def test_trace_cost_decomposes_total(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_synthetic_db(db_path)
    db = NemoDB(db_path)

    cost = trace_cost(db, region="R1", year=2030)
    assert isinstance(cost, CostBreakdown)
    assert cost.total == 10000.0
    # Capital investment 6000 + operating 3000 + emissions 2000 - salvage 1000 = 10000
    assert cost.streams["capital_investment_tech"] == 6000.0
    assert cost.streams["operating_cost_tech"] == 3000.0
    assert cost.streams["emissions_penalty"] == 2000.0
    assert cost.streams["salvage_value_tech"] == 1000.0
    # Reconstruction should match the total within float tolerance
    assert cost.reconstructed is not None
    assert abs(cost.reconstructed - cost.total) < 1e-6


def test_trace_cost_to_dataframe(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_synthetic_db(db_path)
    db = NemoDB(db_path)
    cost = trace_cost(db, "R1", 2030)
    df = cost.to_dataframe()
    # Salvage shows negative signed value
    salvage_row = df[df["stream"] == "salvage_value_tech"]
    assert len(salvage_row) == 1
    assert salvage_row.iloc[0]["sign"] == "-"
    assert salvage_row.iloc[0]["signed"] == -1000.0


def test_trace_cost_zero_when_region_absent(tmp_path):
    db_path = tmp_path / "syn.sqlite"
    _make_synthetic_db(db_path)
    db = NemoDB(db_path)
    cost = trace_cost(db, "DoesNotExist", 2030)
    assert cost.total == 0.0
    assert all(v == 0.0 for v in cost.streams.values())
