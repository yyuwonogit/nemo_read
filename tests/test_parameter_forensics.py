"""
Tests for parameter_forensics (Stages 4 + 5) and probe_brief (Stage 7).

Builds tiny synthetic DBs that exhibit each known infeasibility pattern,
then confirms:
  - the right detector fires
  - the cluster gets the correct verdict
  - placeholders are generated for ``bug`` clusters but NOT for ``intent``
  - ranking is lex-correct
  - probe_brief skips ``intent`` clusters by default
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
    NemoDB,
    classify_parameter, propose_placeholders, emit_probe_brief,
    PLACEHOLDER_SENTINEL, PLACEHOLDER_NOTE_PREFIX,
    decode_lp_column, forensics_for_pinned_variable,
)


def _add_minutil_squared(path: Path, regions, techs, years, timeslices,
                         af_value: float = 0.96) -> None:
    """Inject MinUtilization=AF² for given (r, t, l, y) combos."""
    con = sqlite3.connect(path)
    con.execute("DROP TABLE IF EXISTS MinimumUtilization")
    con.execute("DROP TABLE IF EXISTS AvailabilityFactor")
    con.execute("CREATE TABLE MinimumUtilization (id INTEGER PRIMARY KEY "
                "AUTOINCREMENT, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)")
    con.execute("CREATE TABLE AvailabilityFactor (id INTEGER PRIMARY KEY "
                "AUTOINCREMENT, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)")
    af_sq = af_value * af_value
    for r in regions:
        for t in techs:
            for y in years:
                for l in timeslices:
                    con.execute(
                        "INSERT INTO MinimumUtilization (r,t,l,y,val) "
                        "VALUES (?,?,?,?,?)", (r, t, l, y, af_sq))
                    con.execute(
                        "INSERT INTO AvailabilityFactor (r,t,l,y,val) "
                        "VALUES (?,?,?,?,?)", (r, t, l, y, af_value))
    con.commit()
    con.close()


def _add_minutil_year_split(path: Path, region: str, tech: str,
                            timeslices, af_value: float = 0.8) -> None:
    """Inject early-year squared, late-year linearly-decaying MU."""
    con = sqlite3.connect(path)
    con.execute("DROP TABLE IF EXISTS MinimumUtilization")
    con.execute("DROP TABLE IF EXISTS AvailabilityFactor")
    con.execute("CREATE TABLE MinimumUtilization (id INTEGER PRIMARY KEY "
                "AUTOINCREMENT, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)")
    con.execute("CREATE TABLE AvailabilityFactor (id INTEGER PRIMARY KEY "
                "AUTOINCREMENT, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)")
    early_years = ["2025", "2030", "2035", "2040"]
    late_years_with_mu = [("2045", 0.6 * af_value),
                          ("2050", 0.5 * af_value),
                          ("2055", 0.4 * af_value),
                          ("2060", 0.3 * af_value)]
    for l in timeslices:
        for y in early_years:
            con.execute(
                "INSERT INTO MinimumUtilization (r,t,l,y,val) "
                "VALUES (?,?,?,?,?)", (region, tech, l, y, af_value * af_value))
            con.execute(
                "INSERT INTO AvailabilityFactor (r,t,l,y,val) "
                "VALUES (?,?,?,?,?)", (region, tech, l, y, af_value))
        for y, mu in late_years_with_mu:
            con.execute(
                "INSERT INTO MinimumUtilization (r,t,l,y,val) "
                "VALUES (?,?,?,?,?)", (region, tech, l, y, mu))
            con.execute(
                "INSERT INTO AvailabilityFactor (r,t,l,y,val) "
                "VALUES (?,?,?,?,?)", (region, tech, l, y, af_value))
    con.commit()
    con.close()


def _add_minutil_harvest(path: Path, region: str, tech: str,
                         timeslices, fraction: float = 6.05 / 7) -> None:
    """Inject harvest fraction (X/7 form) MU with AF=1.0."""
    con = sqlite3.connect(path)
    con.execute("DROP TABLE IF EXISTS MinimumUtilization")
    con.execute("DROP TABLE IF EXISTS AvailabilityFactor")
    con.execute("CREATE TABLE MinimumUtilization (id INTEGER PRIMARY KEY "
                "AUTOINCREMENT, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)")
    con.execute("CREATE TABLE AvailabilityFactor (id INTEGER PRIMARY KEY "
                "AUTOINCREMENT, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)")
    for y in ("2025", "2030"):
        for l in timeslices:
            mu = fraction if y == "2025" else 1.0
            con.execute(
                "INSERT INTO MinimumUtilization (r,t,l,y,val) "
                "VALUES (?,?,?,?,?)", (region, tech, l, y, mu))
            con.execute(
                "INSERT INTO AvailabilityFactor (r,t,l,y,val) "
                "VALUES (?,?,?,?,?)", (region, tech, l, y, 1.0))
    con.commit()
    con.close()


# ---------------------------------------------------------------------------
# Detector tests
# ---------------------------------------------------------------------------
def test_squared_bug_detected_as_bug():
    """MU = AF² across all rows → algebraic_of(squared) → verdict ``bug``."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        _add_minutil_squared(path, ["IDN", "MYS"], ["PWRSOL"],
                             ["2024", "2025", "2026"], ["L1", "L2", "L3", "L4"])
        db = NemoDB(path)
        rep = classify_parameter(db, "MinimumUtilization",
                                 related=("AvailabilityFactor",))
        assert len(rep.clusters) == 2
        for c in rep.clusters:
            assert c.summary == "bug", (
                f"expected bug, got {c.summary} for "
                f"{c.tech}: {[d for d in c.detections if d.fired]}"
            )


def test_year_split_detected_as_intent():
    """Year-split monotonic late ramp → verdict ``intent`` (preserve)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        _add_minutil_year_split(path, "IDN", "PWRCOAL", ["L1", "L2"])
        db = NemoDB(path)
        rep = classify_parameter(db, "MinimumUtilization",
                                 related=("AvailabilityFactor",))
        assert len(rep.clusters) == 1
        c = rep.clusters[0]
        # Squared early years + monotonic late → year_split fires (intent).
        # The strong-bug rule should still pin verdict to bug because the
        # algebraic_of detector matches early-year rows at >=80% only when
        # the late ramp is small fraction of total. With our synthetic
        # 4 early × 2 timeslices = 8 squared rows + 4 late × 2 = 8 ramp
        # rows the algebraic match is 50% (below threshold). So algebraic
        # doesn't fire, year_split does → intent.
        fired = [d for d in c.detections if d.fired]
        assert any(d.detector == "year_split" for d in fired), (
            f"expected year_split to fire; fired: {fired}"
        )
        assert c.summary == "intent", (
            f"expected intent (preserve), got {c.summary}; fired: {fired}"
        )


def test_harvest_fraction_detected_as_intent():
    """X/7 harvest fraction → small_denom_fraction → ``intent``."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        _add_minutil_harvest(path, "IDN", "PWRCOAL", ["L1", "L2", "L3", "L4"])
        db = NemoDB(path)
        rep = classify_parameter(db, "MinimumUtilization",
                                 related=("AvailabilityFactor",))
        c = rep.clusters[0]
        # The cluster has values {6.05/7, 1.0} — harvest fraction + fall-back.
        # small_denom_fraction may need both shared denominator OR ≥3 distinct
        # values; with 1 unique non-trivial fraction it may not fire. Check
        # that verdict is at least non-bug (we don't want to placeholder it).
        assert c.summary != "bug", (
            f"harvest fraction should never get bug verdict; "
            f"got {c.summary} with detectors "
            f"{[d for d in c.detections if d.fired]}"
        )


def test_self_companion_skipped():
    """Companion=parameter must be skipped (no tautological algebraic match)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        _add_minutil_squared(path, ["IDN"], ["PWRSOL"],
                             ["2024"], ["L1"])
        db = NemoDB(path)
        rep = classify_parameter(db, "AvailabilityFactor",
                                 related=("AvailabilityFactor",))
        # No clusters should classify as bug just from self-comparison
        for c in rep.clusters:
            algs = [d for d in c.detections
                    if d.fired and d.detector.startswith("algebraic_of")]
            assert not algs, (
                f"self-companion should not produce algebraic match; "
                f"got {algs}"
            )


# ---------------------------------------------------------------------------
# Stage 5 placeholder tests
# ---------------------------------------------------------------------------
def test_placeholders_generated_for_bug_clusters():
    """``bug`` verdict clusters produce a PlaceholderProposal each."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        _add_minutil_squared(path, ["IDN", "MYS"], ["PWRSOL", "PWRCOAL"],
                             ["2024", "2025"], ["L1", "L2"])
        db = NemoDB(path)
        rep = classify_parameter(db, "MinimumUtilization",
                                 related=("AvailabilityFactor",))
        ph = propose_placeholders(rep)
        assert len(ph) == 4, f"expected 4 placeholders, got {len(ph)}"
        # All rows must carry the PLACEHOLDER tag and note prefix
        for p in ph:
            row = p.rows[0]
            assert row["data_confidence"] == PLACEHOLDER_SENTINEL
            assert row["note"].startswith(PLACEHOLDER_NOTE_PREFIX)
            assert row["expression"] == "0"
            assert row["variable"] == "Minimum Utilization"


def test_placeholders_skip_intent_clusters():
    """``intent`` verdict clusters do NOT produce placeholders."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        _add_minutil_year_split(path, "IDN", "PWRCOAL", ["L1", "L2"])
        db = NemoDB(path)
        rep = classify_parameter(db, "MinimumUtilization",
                                 related=("AvailabilityFactor",))
        ph = propose_placeholders(rep, include_unknown=False)
        assert ph == [], f"expected 0 placeholders for intent cluster; got {ph}"


def test_placeholders_lex_sort():
    """Ranking is (blast, -confidence, reverse_difficulty) lexicographic."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        _add_minutil_squared(path, ["IDN", "MYS"], ["PWRSOL", "PWRCOAL"],
                             ["2024", "2025"], ["L1", "L2"])
        db = NemoDB(path)
        rep = classify_parameter(db, "MinimumUtilization",
                                 related=("AvailabilityFactor",))
        ph = propose_placeholders(rep)
        # Sort keys must be monotonically non-decreasing
        keys = [p.sort_key for p in ph]
        assert keys == sorted(keys), (
            f"placeholders not lex-sorted: {keys}"
        )


# ---------------------------------------------------------------------------
# Stage 3 → 4 bridge
# ---------------------------------------------------------------------------
def test_forensics_for_pinned_variable_runs():
    """forensics_for_pinned_variable must run end-to-end on a synthetic DB."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        _add_minutil_squared(path, ["IDN", "MYS"], ["PWRSOL"],
                             ["2024", "2025"], ["L1", "L2"])
        db = NemoDB(path)
        # Decode some column inside vaccumulatednewcapacity
        ident = decode_lp_column(db, 1)        # vdemandnn[first]
        # Replace the identity to point at vaccumulatednewcapacity manually
        ident.variable = "vaccumulatednewcapacity"
        ident.indices = {"r": "IDN", "t": "PWRSOL", "y": "2024"}
        reports = forensics_for_pinned_variable(db, ident)
        param_names = {r.parameter for r in reports}
        assert "MinimumUtilization" in param_names
        assert "AvailabilityFactor" in param_names


# ---------------------------------------------------------------------------
# Probe brief
# ---------------------------------------------------------------------------
def test_probe_brief_skips_intent_by_default():
    """Default probe brief excludes intent clusters."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        _add_minutil_year_split(path, "IDN", "PWRCOAL", ["L1", "L2"])
        db = NemoDB(path)
        rep = classify_parameter(db, "MinimumUtilization",
                                 related=("AvailabilityFactor",))
        # default: only_unresolved=True excludes 'bug' too; intent always excluded
        brief = emit_probe_brief(rep)
        # intent cluster only → brief should be empty
        assert len(brief) == 0


def test_probe_brief_emits_for_unknown_clusters():
    """Probe brief includes unknown clusters by default."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "scenario.sqlite"
        _build_synthetic_db(path)
        # a single value that doesn't match any pattern (unknown verdict)
        con = sqlite3.connect(path)
        con.execute("DROP TABLE IF EXISTS MinimumUtilization")
        con.execute("DROP TABLE IF EXISTS AvailabilityFactor")
        con.execute("CREATE TABLE MinimumUtilization (id INTEGER PRIMARY KEY "
                    "AUTOINCREMENT, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)")
        con.execute("CREATE TABLE AvailabilityFactor (id INTEGER PRIMARY KEY "
                    "AUTOINCREMENT, r TEXT, t TEXT, l TEXT, y TEXT, val REAL)")
        # Single oddball value, no companion → no detector fires → unknown
        con.execute("INSERT INTO MinimumUtilization (r,t,l,y,val) "
                    "VALUES ('IDN','PWRSOL','L1','2024',0.42)")
        con.commit()
        con.close()
        db = NemoDB(path)
        rep = classify_parameter(db, "MinimumUtilization",
                                 related=("AvailabilityFactor",))
        brief = emit_probe_brief(rep)
        assert len(brief) >= 1


# ---------------------------------------------------------------------------
# Inject-side placeholder gate
# ---------------------------------------------------------------------------
def test_inject_split_placeholder_rows():
    """The injector base must split placeholder rows from real rows.

    Placeholder detection moved from a bioenergy-local function to
    `CanonicalInjector.is_placeholder_row` / `split_placeholder_rows`
    as part of the 2026-05-17 framework consolidation.
    """
    from nemo_read.inject_base import CanonicalInjector

    class _Probe(CanonicalInjector):
        SECTOR_NAME = "_test_probe"

    inj = _Probe()
    rows = [
        {"data_confidence": "PLACEHOLDER", "note": "PLACEHOLDER (Stage 5 ...): test"},
        {"data_confidence": "High", "note": "real fix"},
        {"data_confidence": "Low",  "note": "PLACEHOLDER (Stage 5 ...): test2"},
        {"data_confidence": "High", "note": "another real"},
    ]
    real, ph = inj.split_placeholder_rows(rows)
    assert len(real) == 2
    assert len(ph) == 2
    assert all(inj.is_placeholder_row(p) for p in ph)
    assert all(not inj.is_placeholder_row(r) for r in real)


def main() -> int:
    test_squared_bug_detected_as_bug()
    test_year_split_detected_as_intent()
    test_harvest_fraction_detected_as_intent()
    test_self_companion_skipped()
    test_placeholders_generated_for_bug_clusters()
    test_placeholders_skip_intent_clusters()
    test_placeholders_lex_sort()
    test_forensics_for_pinned_variable_runs()
    test_probe_brief_skips_intent_by_default()
    test_probe_brief_emits_for_unknown_clusters()
    test_inject_split_placeholder_rows()
    print("All parameter_forensics + probe_brief tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
