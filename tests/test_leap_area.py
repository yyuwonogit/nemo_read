"""Tests for the LEAP-area pairing layer added in 0.6.0."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from nemo_read import (
    CustomConstraintsDoc, LEAP_BRANCH_TYPES, LEAP_SOURCE_MAP, LeapAreaContext,
    LeapSource, leap_source, read_custom_constraints, read_nemo_cfg,
    resolve_leap_ids, where_in_leap,
)


FIXTURE = Path(__file__).parent / "fixtures" / "leap_export"


# ---------------------------------------------------------------------------
# read_nemo_cfg
# ---------------------------------------------------------------------------
def test_read_nemo_cfg_extracts_varstosave():
    cfg = read_nemo_cfg(FIXTURE / "nemo.cfg")
    assert cfg["calculatescenarioargs"]["varstosave"] == [
        "vtotalcapacityannual", "vannualemissions", "vnewcapacity"
    ]
    assert cfg["solver"]["parameters"].startswith("CPXPARAM_MIP_Tolerances_MIPGap")


# ---------------------------------------------------------------------------
# read_custom_constraints
# ---------------------------------------------------------------------------
def test_read_custom_constraints_parses_functions_and_tables():
    doc = read_custom_constraints(FIXTURE / "customconstraints.txt")
    assert isinstance(doc, CustomConstraintsDoc)
    assert "build_test_constraint" in doc.functions
    assert "TestTarget__NEMOcc" in doc.nemocc_tables


def test_read_custom_constraints_extracts_pollutant_eid_map():
    doc = read_custom_constraints(FIXTURE / "customconstraints.txt")
    # Comments like "# CO2" next to E2 should yield CO2 -> 2
    assert doc.pollutant_to_eid.get("CO2") == 2
    assert doc.pollutant_to_eid.get("CH4") == 4
    # Reverse map auto-populated in __post_init__
    assert doc.eid_to_pollutant.get(2) == "CO2"


# ---------------------------------------------------------------------------
# LeapAreaContext.from_export
# ---------------------------------------------------------------------------
def test_context_from_export_loads_all_csvs():
    ctx = LeapAreaContext.from_export(FIXTURE)
    assert len(ctx.branches) == 23
    assert len(ctx.fuels) == 3
    assert len(ctx.regions) == 2
    assert len(ctx.timeslices) == 3
    assert len(ctx.scenarios) == 2
    assert len(ctx.tags) == 2
    assert len(ctx.units) == 2
    assert len(ctx.nemocc_sources) == 1


def test_context_varstosave_shortcut():
    ctx = LeapAreaContext.from_export(FIXTURE)
    assert ctx.varstosave == [
        "vtotalcapacityannual", "vannualemissions", "vnewcapacity"
    ]


def test_context_branch_lookups():
    ctx = LeapAreaContext.from_export(FIXTURE)
    assert ctx.branch_full_name(11942) == \
        r"Transformation\Centralized Electricity Generation\Processes\Pumped Hydro"
    assert ctx.branch_full_name(999999) is None
    row = ctx.branch_by_id(11942)
    assert row["branch_type"] == 3
    assert row["name"] == "Pumped Hydro"
    assert ctx.fuel_name(1) == "Electricity"
    assert ctx.fuel_name(999) is None
    assert ctx.region_name(2) == "Indonesia"


def test_context_nemocc_source_lookup():
    ctx = LeapAreaContext.from_export(FIXTURE)
    info = ctx.nemocc_source_for("ASEANRenewableCapacityTarget__NEMOcc")
    assert info is not None
    assert info["branch_id"] == 1201
    assert ctx.nemocc_source_for("NonExistent__NEMOcc") is None


# ---------------------------------------------------------------------------
# LeapAreaContext.discover
# ---------------------------------------------------------------------------
def test_discover_finds_adjacent_export(tmp_path):
    sqlite_path = tmp_path / "scenario.sqlite"
    sqlite_path.write_bytes(b"")                  # placeholder file
    export_dir = tmp_path / "scenario.leap_export"
    export_dir.mkdir()
    # Copy fixture branches.csv so discover() considers it valid
    (export_dir / "branches.csv").write_text(
        (FIXTURE / "branches.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    class _DB:
        path = str(sqlite_path)

    ctx = LeapAreaContext.discover(_DB())
    assert ctx is not None
    assert len(ctx.branches) == 23


def test_discover_returns_none_when_missing(tmp_path):
    sqlite_path = tmp_path / "scenario.sqlite"
    sqlite_path.write_bytes(b"")

    class _DB:
        path = str(sqlite_path)

    assert LeapAreaContext.discover(_DB()) is None


# ---------------------------------------------------------------------------
# where_in_leap — the core traceback helper
# ---------------------------------------------------------------------------
def test_where_in_leap_tech_scoped_parameter():
    ctx = LeapAreaContext.from_export(FIXTURE)
    hint = where_in_leap(
        "CapitalCost", {"r": "R1", "t": "P11942", "y": "2030"}, ctx
    )
    assert hint is not None
    assert hint["variable_name"] == "Capital Cost"
    assert hint["branch_id"] == 11942
    assert "Pumped Hydro" in hint["branch_full_name"]
    assert hint["confidence"] == "confirmed"


def test_where_in_leap_process_node_resolves_subregion():
    ctx = LeapAreaContext.from_export(FIXTURE)
    hint = where_in_leap(
        "NodalDistributionTechnologyCapacity",
        {"n": "Indonesia Jamali", "t": "P11942", "y": "2030"},
        ctx,
    )
    assert hint is not None
    assert hint["branch_id"] == 20107
    assert hint["variable_name"] == "Nodal Distribution"
    # Same variable feeds the storage-side table
    hint2 = where_in_leap(
        "NodalDistributionStorageCapacity",
        {"n": "Indonesia Sumatra", "s": "P11942", "y": "2030"},
        ctx,
    )
    assert hint2["branch_id"] == 20108


def test_where_in_leap_returns_none_for_result_variable():
    ctx = LeapAreaContext.from_export(FIXTURE)
    hint = where_in_leap(
        "vtotalcapacityannual",
        {"r": "R1", "t": "P11942", "y": "2030"},
        ctx,
    )
    assert hint is None


def test_where_in_leap_returns_none_for_unknown_table():
    ctx = LeapAreaContext.from_export(FIXTURE)
    assert where_in_leap("NonExistentTable", {}, ctx) is None


def test_where_in_leap_unknown_tech_still_returns_hint_with_none_branch():
    ctx = LeapAreaContext.from_export(FIXTURE)
    hint = where_in_leap(
        "CapitalCost", {"r": "R1", "t": "P999999", "y": "2030"}, ctx
    )
    # Table is mapped, the tech prefix decoded to ID 999999, but that branch
    # doesn't exist in the fixture tree — full_name resolves to None.
    assert hint is not None
    assert hint["branch_full_name"] is None
    # branch_id carries the prefix-decoded value even when unresolved, so the
    # caller can see what the row claimed vs what the tree contains.
    assert hint["branch_id"] == 999999


def test_where_in_leap_method_on_context():
    ctx = LeapAreaContext.from_export(FIXTURE)
    hint = ctx.where_in_leap("OperationalLife", {"r": "R1", "t": "P11942"})
    assert hint["variable_name"] == "Lifetime"


# ---------------------------------------------------------------------------
# LEAP_SOURCE_MAP / LeapSource sanity
# ---------------------------------------------------------------------------
def test_leap_source_map_covers_key_parameters():
    must_have = [
        "CapitalCost", "FixedCost", "VariableCost", "OperationalLife",
        "AvailabilityFactor", "ResidualCapacity",
        "NodalDistributionTechnologyCapacity",
        "NodalDistributionStorageCapacity",
        "ReserveMargin", "MinStorageCharge",
    ]
    for name in must_have:
        assert name in LEAP_SOURCE_MAP, f"{name} missing from LEAP_SOURCE_MAP"
        src = LEAP_SOURCE_MAP[name]
        assert isinstance(src, LeapSource)
        assert src.variable
        assert src.branch_type_name


def test_leap_source_helper_returns_none_for_result_vars():
    assert leap_source("vtotalcapacityannual") is None
    assert leap_source("CapitalCost") is not None


def test_leap_branch_types_includes_known_codes():
    # Codes confirmed from probe against AEO9
    assert LEAP_BRANCH_TYPES[3] == "Transformation Process"
    assert LEAP_BRANCH_TYPES[4] == "Demand Technology"
    assert LEAP_BRANCH_TYPES[57] == "Process Node"
    assert LEAP_BRANCH_TYPES[56] == "Transmission Nodes"


# ---------------------------------------------------------------------------
# resolve_leap_ids
# ---------------------------------------------------------------------------
def test_resolve_leap_ids_joins_tech_column():
    ctx = LeapAreaContext.from_export(FIXTURE)
    df = pd.DataFrame({
        "t":   ["P11942", "P16756", "P999999"],
        "val": [1.0,      2.0,      3.0],
    })
    out = resolve_leap_ids(df, ctx, branch_id_col=None, fuel_leap_id_col=None)
    assert "tech_branch_full_name" in out.columns
    assert "Pumped Hydro" in out.loc[0, "tech_branch_full_name"]
    assert "Solar PV Rooftop" in out.loc[1, "tech_branch_full_name"]
    assert pd.isna(out.loc[2, "tech_branch_full_name"])


def test_resolve_leap_ids_joins_fuel_leap_id():
    ctx = LeapAreaContext.from_export(FIXTURE)
    df = pd.DataFrame({"leap_id": [1, 2, 999]})
    out = resolve_leap_ids(df, ctx, branch_id_col=None, tech_col=None)
    assert out.loc[0, "fuel_name"] == "Electricity"
    assert out.loc[1, "fuel_name"] == "Natural Gas"
    assert pd.isna(out.loc[2, "fuel_name"])
