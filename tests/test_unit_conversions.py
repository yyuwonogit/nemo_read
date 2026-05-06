"""Tests for nemo_read.unit_conversions and the audit→apply pipeline."""
from __future__ import annotations

import pandas as pd
import pytest

from nemo_read import (
    ConversionProposal, propose_conversion, list_known_conversions,
    apply_audit_conversions,
)


# ---------------------------------------------------------------------------
# Conversion registry lookups
# ---------------------------------------------------------------------------
def test_propose_si_pj_per_year_to_thousand_gj_per_year():
    p = propose_conversion("PJ/year", "Thousand Gigajoules/Year")
    assert p is not None
    assert p.factor == 1000.0
    assert p.confidence_stars == 5


def test_propose_usd_per_100l_to_usd_per_barrel():
    p = propose_conversion("USD/100L real 2020 USD", "2020 USD/Barrel")
    assert p is not None
    assert abs(p.factor - 1.5899) < 1e-4
    assert p.confidence_stars == 5


def test_propose_usd_per_gj_to_usd_per_mmbtu():
    p = propose_conversion("USD/GJ real 2020 USD", "U.S. Dollar/Million BTU")
    assert p is not None
    assert abs(p.factor - 1.05506) < 1e-5


def test_propose_coal_lhv_fuel_specific():
    p_bit = propose_conversion("USD/GJ real 2020 USD", "U.S. Dollar/Metric Tonne",
                               fuel="Coal Bituminous")
    assert p_bit.factor == 25.8
    assert p_bit.confidence_stars == 3
    p_lig = propose_conversion("USD/GJ real 2020 USD", "U.S. Dollar/Metric Tonne",
                               fuel="Coal Lignite")
    assert p_lig.factor == 11.9
    assert p_lig.confidence_stars == 2  # lignite is lower confidence
    assert p_bit.factor != p_lig.factor


def test_propose_unknown_returns_none():
    assert propose_conversion("foo", "bar") is None


def test_list_known_conversions_includes_si_entries():
    entries = list_known_conversions()
    keys = [k for k, _ in entries]
    assert any("pj/year" in k[0] and "tgj/year" in k[1] for k in keys)


# ---------------------------------------------------------------------------
# apply_audit_conversions
# ---------------------------------------------------------------------------
def _audit_row(branch, variable, your_unit, leap_unit, status,
               factor=float("nan"), stars=0, source="", caveat=""):
    return {
        "branch": branch, "variable": variable,
        "your_unit": your_unit, "leap_unit": leap_unit,
        "status": status,
        "proposed_factor": factor,
        "confidence_stars": stars,
        "conversion_source": source,
        "conversion_caveat": caveat,
    }


def test_apply_rewrites_interp_with_proposed_factor():
    # Pipeline standard: comma between (year, value) pairs, period decimal.
    canonical = pd.DataFrame([{
        "ams": "Indonesia",
        "branch": "Resources\\Primary\\Coal Bituminous",
        "variable": "Production Cost",
        "expression": "Interp(2024, 3.5, 2025, 3.5, 2030, 4.0)",
        "unit": "USD/GJ real 2020 USD",
        "fuel": "Coal Bituminous",
    }])
    audit = pd.DataFrame([_audit_row(
        "Resources\\Primary\\Coal Bituminous", "Production Cost",
        "USD/GJ real 2020 USD", "U.S. Dollar/Metric Tonne",
        "mismatch", factor=25.8, stars=3, source="IPCC",
    )])
    out = apply_audit_conversions(canonical, audit)
    expr = out.iloc[0]["expression"]
    # 3.5 × 25.8 = 90.3 ; 4.0 × 25.8 = 103.2
    assert "90.3" in expr
    assert "103.2" in expr
    assert "Interp" in expr
    # Output must remain comma-form (the only pipeline standard)
    assert ";" not in expr
    assert out.iloc[0]["unit"] == "U.S. Dollar/Metric Tonne"
    assert out.iloc[0]["unit_audit"].startswith("factor=25.8")


def test_apply_leaves_match_rows_alone():
    canonical = pd.DataFrame([{
        "ams": "Indonesia",
        "branch": "Resources\\Primary\\Crude Oil",
        "variable": "Production Cost",
        "expression": "Interp(2025, 30, 2030, 30)",
        "unit": "USD/bbl real 2020 USD",
        "fuel": "Crude Oil",
    }])
    audit = pd.DataFrame([_audit_row(
        "Resources\\Primary\\Crude Oil", "Production Cost",
        "USD/bbl real 2020 USD", "2020 USD/Barrel", "match",
    )])
    out = apply_audit_conversions(canonical, audit)
    assert out.iloc[0]["expression"] == "Interp(2025, 30, 2030, 30)"
    assert out.iloc[0]["unit_audit"] == ""


def test_apply_overrides_take_precedence():
    canonical = pd.DataFrame([{
        "ams": "Indonesia",
        "branch": "Resources\\Primary\\Coal Lignite",
        "variable": "Production Cost",
        "expression": "Interp(2024, 2.0, 2025, 2.0)",
        "unit": "USD/GJ real 2020 USD",
        "fuel": "Coal Lignite",
    }])
    audit = pd.DataFrame([_audit_row(
        "Resources\\Primary\\Coal Lignite", "Production Cost",
        "USD/GJ real 2020 USD", "U.S. Dollar/Metric Tonne",
        "mismatch", factor=11.9, stars=2,  # default
    )])
    overrides = {
        ("Resources\\Primary\\Coal Lignite", "Production Cost", "Indonesia"): {
            "factor": 11.5,
            "source": "PT Bukit Asam regional Sumatran lignite contracts",
            "confidence_stars": 4,
        },
    }
    out = apply_audit_conversions(canonical, audit, overrides=overrides)
    expr = out.iloc[0]["expression"]
    # 2.0 × 11.5 = 23
    assert "23" in expr
    assert ";" not in expr
    assert "11.5" in out.iloc[0]["unit_audit"]
    assert "PT Bukit Asam" in out.iloc[0]["unit_audit"]


def test_apply_unresolved_mismatch_marks_row():
    canonical = pd.DataFrame([{
        "ams": "Indonesia",
        "branch": "Resources\\Primary\\Mystery Fuel",
        "variable": "Capital Cost",
        "expression": "Interp(2024, 100)",
        "unit": "MysteryUnit",
        "fuel": "Mystery",
    }])
    audit = pd.DataFrame([_audit_row(
        "Resources\\Primary\\Mystery Fuel", "Capital Cost",
        "MysteryUnit", "OtherUnit", "mismatch",
        factor=float("nan"), stars=0,
    )])
    out = apply_audit_conversions(canonical, audit)
    assert out.iloc[0]["expression"] == "Interp(2024, 100)"   # unchanged
    assert out.iloc[0]["unit_audit"].startswith("MISMATCH unresolved")


def test_apply_data_call_rewrite():
    canonical = pd.DataFrame([{
        "ams": "Indonesia",
        "branch": "Resources\\Primary\\Crude Oil",
        "variable": "Additions to Reserves",
        "expression": "Data(2024, 2.25)",
        "unit": "Gbbl",
        "fuel": "Crude Oil",
    }])
    # Pretend a unit conversion is needed (factor 2 just to test the rewrite)
    audit = pd.DataFrame([_audit_row(
        "Resources\\Primary\\Crude Oil", "Additions to Reserves",
        "Gbbl", "OtherReservesUnit", "mismatch",
        factor=2.0, stars=5, source="test",
    )])
    out = apply_audit_conversions(canonical, audit)
    assert out.iloc[0]["expression"] == "Data(2024, 4.5)"   # 2.25 × 2 = 4.5


def test_apply_rewrites_realistic_bioenergy_max_capacity():
    # Real-world shape: bioenergy Maximum Capacity in Million Tonnes/yr →
    # LEAP-side Million Gigajoules/Year (Biodiesel LHV factor 37). All 8
    # milestone-year values must be multiplied; comma-form preserved.
    canonical = pd.DataFrame([{
        "ams": "Indonesia",
        "branch": "Transformation\\Biodiesel Production\\Processes\\FAME Biodiesel",
        "variable": "Maximum Capacity",
        "expression": "Interp(2025, 16.0, 2030, 23.5, 2035, 31.0, 2040, 38.5, "
                      "2045, 46.0, 2050, 53.5, 2055, 61.0, 2060, 65.0)",
        "unit": "Million Tonnes/yr",
        "fuel": "Biodiesel",
    }])
    audit = pd.DataFrame([_audit_row(
        "Transformation\\Biodiesel Production\\Processes\\FAME Biodiesel",
        "Maximum Capacity",
        "Million Tonnes/yr", "Million Gigajoules/Year",
        "mismatch", factor=37.0, stars=4, source="IPCC FAME LHV",
    )])
    out = apply_audit_conversions(canonical, audit)
    expr = out.iloc[0]["expression"]
    # Spot-check all 8 milestone values
    assert "592" in expr      # 16.0  × 37
    assert "869.5" in expr    # 23.5  × 37
    assert "1147" in expr     # 31.0  × 37
    assert "1424.5" in expr   # 38.5  × 37
    assert "1702" in expr     # 46.0  × 37
    assert "1979.5" in expr   # 53.5  × 37
    assert "2257" in expr     # 61.0  × 37
    assert "2405" in expr     # 65.0  × 37
    # Years pass through unchanged
    assert "2025" in expr and "2060" in expr
    # Comma-form only — never any semicolons in our pipeline output
    assert ";" not in expr
    assert out.iloc[0]["unit"] == "Million Gigajoules/Year"
