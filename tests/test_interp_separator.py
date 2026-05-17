"""Regression tests for CLAUDE.md §A.15 — LEAP Interp() must commit
with comma list-separator + period decimal on this engine.

Burned 2026-05-17: rule had existed since 2026-05-07 but the fossil
domain shipped a canonical CSV in `Interp(...; ...; ...)` form
because no central enforcement existed. These tests pin the chokepoint.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from nemo_read._leap_com import (
    InterpSeparatorError,
    assert_interp_canonical,
    normalize_interp,
    validate_canonical_csv_expressions,
)


class TestNormalizeInterp:
    def test_correct_form_unchanged(self):
        e = "Interp(2025, 3.2422, 2030, 3.0833, 2035, 2.9322)"
        assert normalize_interp(e) == e

    def test_semicolon_with_space_fixed(self):
        got = normalize_interp("Interp(2025; 3.2; 2030; 3.0)")
        assert got == "Interp(2025, 3.2, 2030, 3.0)"

    def test_semicolon_no_space_fixed(self):
        got = normalize_interp("Interp(2025;3.2;2030;3.0)")
        assert got == "Interp(2025,3.2,2030,3.0)"

    def test_multiple_interps_in_one_expression(self):
        e = "Min(Interp(2025; 0.5; 2030; 0.7), Interp(2030; 0.8; 2040; 0.9))"
        got = normalize_interp(e)
        assert got == "Min(Interp(2025, 0.5, 2030, 0.7), Interp(2030, 0.8, 2040, 0.9))"

    def test_non_interp_text_untouched(self):
        e = "If(year > 2030; 1.0; 0.5)"  # semicolons outside Interp left alone
        assert normalize_interp(e) == e

    def test_non_string_passes_through(self):
        assert normalize_interp(None) is None
        assert normalize_interp(42) == 42
        assert normalize_interp(3.14) == 3.14


class TestAssertInterpCanonical:
    def test_correct_form_passes(self):
        assert_interp_canonical("Interp(2025, 3.2, 2030, 3.0)")

    def test_semicolon_form_raises(self):
        with pytest.raises(InterpSeparatorError):
            assert_interp_canonical("Interp(2025; 3.2; 2030; 3.0)")

    def test_mixed_semicolon_anywhere_inside_interp_raises(self):
        with pytest.raises(InterpSeparatorError):
            assert_interp_canonical("Interp(2025, 3.2; 2030, 3.0)")

    def test_non_string_silent(self):
        assert_interp_canonical(None)
        assert_interp_canonical(42)


class TestCsvValidation:
    def test_clean_csv_returns_empty(self, tmp_path: Path):
        p = tmp_path / "clean.csv"
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ams", "expression"])
            w.writerow(["Brunei", "Interp(2025, 1.0, 2030, 2.0)"])
            w.writerow(["Cambodia", "Interp(2025, 1.5, 2030, 2.5)"])
        assert validate_canonical_csv_expressions(p) == []

    def test_violation_caught(self, tmp_path: Path):
        p = tmp_path / "bad.csv"
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ams", "expression"])
            w.writerow(["Brunei", "Interp(2025, 1.0, 2030, 2.0)"])  # ok
            w.writerow(["Cambodia", "Interp(2025; 1.5; 2030; 2.5)"])  # bad
        violations = validate_canonical_csv_expressions(p)
        assert len(violations) == 1
        assert violations[0][0] == 3  # row 3 (header=1, brunei=2, cambodia=3)


class TestCanonicalCsvsOnDisk:
    """Smoke test — the canonical CSVs currently committed must be clean.

    Anyone editing a canonical CSV and reintroducing the semicolon form
    breaks this test.
    """

    @pytest.mark.parametrize(
        "csv_path",
        [
            "inject/fossil/canonical_leap_inputs.csv",
            "inject/fossil/canonical_leap_native.csv",
            "inject/bioenergy/canonical_leap_inputs.csv",
        ],
    )
    def test_canonical_csv_has_no_semicolon_interps(self, csv_path: str):
        p = Path(csv_path)
        if not p.exists():
            pytest.skip(f"{csv_path} not present")
        violations = validate_canonical_csv_expressions(p)
        assert violations == [], (
            f"{csv_path} has {len(violations)} forbidden Interp() row(s) "
            f"with ';' list-separator (CLAUDE.md §A.15). First: "
            f"row {violations[0][0]}: {violations[0][1][:80]}..."
        )
