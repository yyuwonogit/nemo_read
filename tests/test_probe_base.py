"""Tests for the standardised probe framework + heartbeat utility.

Pins:
1. Sealed methods of `CanonicalProber` can't be overridden
2. `_read_unit_text` enforces §11.2 BT={3,50} restriction
3. HeartbeatLogger writes progress JSON + emits structured stdout
4. Default scope hooks return expected shapes
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from nemo_read._heartbeat import HeartbeatLogger, read_progress
from nemo_read.probe_base import (
    CanonicalProber,
    DEFAULT_RESULT_VARS,
    DEFAULT_INPUT_VARS,
    DEFAULT_RESULT_BRANCH_TYPES,
    DEFAULT_UNIT_BRANCH_TYPES,
    ProberSealError,
)


# ---------------------------------------------------------------------------
# 1. Seal enforcement
# ---------------------------------------------------------------------------

class TestProberSealEnforcement:
    def test_valid_subclass_allowed(self):
        class Valid(CanonicalProber):
            PROBE_NAME = "valid"
        assert Valid().PROBE_NAME == "valid"

    @pytest.mark.parametrize("sealed", [
        "_assert_area_lock",
        "_assert_scenario_lock",
        "_read_value",
        "_read_unit_text",
    ])
    def test_sealed_override_rejected(self, sealed):
        with pytest.raises(ProberSealError) as exc:
            ns = {
                "PROBE_NAME": "bad",
                sealed: lambda self, *a, **k: None,
            }
            type("Bad_" + sealed, (CanonicalProber,), ns)
        assert sealed in str(exc.value)


# ---------------------------------------------------------------------------
# 2. §11.2 BT={3,50} enforcement
# ---------------------------------------------------------------------------

class _StubVar:
    def __init__(self):
        self.DataUnitText = "Gigajoule"


class TestUnitReadBranchTypeGuard:
    def test_safe_branch_types_read(self):
        class Probe(CanonicalProber):
            PROBE_NAME = "p"

        inj = Probe()
        # Without a real LEAP, monkey-patch the safe_data_unit_text
        # import inside _read_unit_text by stubbing the import path.
        # The check we care about is: BT not in UNIT_BRANCH_TYPES → "".
        assert inj._read_unit_text(_StubVar(), branch_type=2) == ""
        assert inj._read_unit_text(_StubVar(), branch_type=4) == ""
        assert inj._read_unit_text(_StubVar(), branch_type=34) == ""

    def test_explicit_subset_respected(self):
        """A subclass can NARROW the unit BT set but not bypass the guard."""
        class NarrowProbe(CanonicalProber):
            PROBE_NAME = "narrow"
            UNIT_BRANCH_TYPES = frozenset({50})

        inj = NarrowProbe()
        # BT=3 is now also blocked
        assert inj._read_unit_text(_StubVar(), branch_type=3) == ""


# ---------------------------------------------------------------------------
# 3. HeartbeatLogger behaviour
# ---------------------------------------------------------------------------

class TestHeartbeatLogger:
    def test_progress_file_created(self, tmp_path: Path):
        hb = HeartbeatLogger("op_test", progress_dir=tmp_path,
                             interval_seconds=0.01)
        assert hb.progress_path.exists()
        state = read_progress(hb.progress_path)
        assert state["op"] == "op_test"
        assert state["started"] is not None

    def test_tick_updates_state(self, tmp_path: Path):
        hb = HeartbeatLogger("op_test", progress_dir=tmp_path,
                             interval_seconds=10.0)  # throttle out heartbeats
        hb.tick(scenario="RAS", region="Brunei", rows_written=42)
        state = read_progress(hb.progress_path)
        assert state["current"]["scenario"] == "RAS"
        assert state["current"]["region"] == "Brunei"
        assert state["rows_total"] == 42

    def test_finish_writes_summary(self, tmp_path: Path):
        hb = HeartbeatLogger("op_test", progress_dir=tmp_path,
                             interval_seconds=10.0)
        hb.tick(rows_written=99)
        hb.finish({"total": 99})
        state = read_progress(hb.progress_path)
        assert state["finished"] is not None
        assert state["summary"]["total"] == 99
        assert "elapsed_seconds" in state

    def test_throttled_heartbeats(self, tmp_path: Path, capsys):
        """After the first tick emits, subsequent ticks within `interval`
        are throttled to stdout but JSON updates every tick."""
        hb = HeartbeatLogger("op_test", progress_dir=tmp_path,
                             interval_seconds=10.0)
        capsys.readouterr()
        hb.tick(rows_written=10)  # first tick: emits immediately
        first = capsys.readouterr().out
        assert "[HB t=" in first
        # Subsequent ticks within 10s: throttled (no new stdout line)
        for i in range(2, 6):
            hb.tick(rows_written=i * 10)
        suppressed = capsys.readouterr().out
        assert "[HB t=" not in suppressed
        # But JSON tracks the latest state
        state = read_progress(hb.progress_path)
        assert state["rows_total"] == 50

    def test_force_heartbeat_emits_now(self, tmp_path: Path, capsys):
        hb = HeartbeatLogger("op_test", progress_dir=tmp_path,
                             interval_seconds=10.0)
        capsys.readouterr()
        hb.tick(rows_written=100)
        hb.force_heartbeat()
        out = capsys.readouterr().out
        assert "[HB t=" in out
        assert "rows_written=100" in out

    def test_read_progress_missing_returns_none(self, tmp_path: Path):
        assert read_progress(tmp_path / "nonexistent.json") is None


# ---------------------------------------------------------------------------
# 4. Default scope hooks
# ---------------------------------------------------------------------------

class TestDefaultHooks:
    def test_default_result_vars(self):
        class P(CanonicalProber):
            PROBE_NAME = "p"
        assert P().result_variables() == DEFAULT_RESULT_VARS

    def test_default_input_vars(self):
        class P(CanonicalProber):
            PROBE_NAME = "p"
        assert P().input_variables() == DEFAULT_INPUT_VARS

    def test_default_result_branch_types_include_module_demand(self):
        """§7.3 — Probe A walks broader branch types than Probe B."""
        class P(CanonicalProber):
            PROBE_NAME = "p"
        bts = P().result_branch_types()
        assert {2, 3, 4, 34, 50}.issubset(bts)

    def test_default_unit_branch_types_only_safe(self):
        """§11.2 — Probe B restricted to {3, 50} popup-safe branch types."""
        class P(CanonicalProber):
            PROBE_NAME = "p"
        bts = P().unit_branch_types()
        assert bts == frozenset({3, 50})

    def test_default_years_are_model_milestones(self):
        """§7.3 — restrict years to 2025-2060 step 5; pre-model years
        inflate CSV ~7×."""
        class P(CanonicalProber):
            PROBE_NAME = "p"
        years = P().years()
        assert min(years) == 2025
        assert max(years) == 2060
        assert 2024 not in years  # pre-model excluded

    def test_subclass_overrides_via_class_attr(self):
        class CustomProbe(CanonicalProber):
            PROBE_NAME = "custom"
            RESULT_VARS = ("Energy Generation",)  # narrowed
            DEFAULT_YEARS = (2030, 2050)

        inj = CustomProbe()
        assert inj.result_variables() == ("Energy Generation",)
        assert inj.years() == [2030, 2050]


# ---------------------------------------------------------------------------
# 5. CLI parser shape
# ---------------------------------------------------------------------------

class TestProberCliParser:
    def test_has_warm_com_flags(self):
        class P(CanonicalProber):
            PROBE_NAME = "p"
        parser = P().build_arg_parser()
        help_text = parser.format_help()
        for flag in ("--scenarios", "--skip-units", "--skip-results",
                     "--heartbeat-interval", "--expect-area",
                     "--branch-prefix", "--skip-zeros", "--out-dir"):
            assert flag in help_text, f"missing {flag}"

    def test_scenarios_resolution_default_to_current(self):
        class P(CanonicalProber):
            PROBE_NAME = "p"
        parser = P().build_arg_parser()
        ns = parser.parse_args([])
        assert ns.scenarios == ""  # empty → use current ActiveScenario

    def test_variable_override_flags(self):
        """v0.6.10 — per-sector variable lists must be overridable."""
        class P(CanonicalProber):
            PROBE_NAME = "p"
        parser = P().build_arg_parser()
        ns = parser.parse_args([
            "--result-vars", "Final Energy Demand,Activity Level",
            "--input-vars", "Capital Cost",
        ])
        assert ns.result_vars == "Final Energy Demand,Activity Level"
        assert ns.input_vars == "Capital Cost"
        assert ns.all_vars is False
        assert ns.all_input_vars is False

    def test_all_vars_flag_disables_filter(self):
        class P(CanonicalProber):
            PROBE_NAME = "p"
        parser = P().build_arg_parser()
        ns = parser.parse_args(["--all-vars", "--all-input-vars"])
        assert ns.all_vars is True
        assert ns.all_input_vars is True

    def test_v0612_emission_and_projection_flags(self):
        """v0.6.12 — emission + projection auto-skip flags must exist."""
        class P(CanonicalProber):
            PROBE_NAME = "p"
        parser = P().build_arg_parser()
        ns = parser.parse_args([])
        assert ns.include_emissions is False
        assert ns.include_projection_layers is False
        ns = parser.parse_args([
            "--include-emissions",
            "--include-projection-layers",
        ])
        assert ns.include_emissions is True
        assert ns.include_projection_layers is True


# ---------------------------------------------------------------------------
# 6. v0.6.12 — emission + projection auto-skip defaults
# ---------------------------------------------------------------------------

class TestProjectionBranchDetection:
    """The `<Sector>_` projection-layer pattern is detected via a path
    segment ending with single trailing underscore."""

    def test_industry_underscore_detected(self):
        from nemo_read.probe_base import CanonicalProber

        class P(CanonicalProber):
            PROBE_NAME = "p"
        assert P()._is_projection_branch(
            "Demand\\Industry_\\Projection\\Chemical") is True

    def test_transport_underscore_detected(self):
        from nemo_read.probe_base import CanonicalProber

        class P(CanonicalProber):
            PROBE_NAME = "p"
        assert P()._is_projection_branch("Demand\\Transport_\\Road") is True

    def test_main_sector_not_flagged(self):
        from nemo_read.probe_base import CanonicalProber

        class P(CanonicalProber):
            PROBE_NAME = "p"
        assert P()._is_projection_branch(
            "Demand\\Industry\\End Use\\Iron and Steel") is False
        assert P()._is_projection_branch(
            "Demand\\Residential\\Lighting") is False

    def test_naked_underscore_segment_not_flagged(self):
        """A segment that's JUST `_` (no name) shouldn't trigger — only
        named-sector_ patterns do."""
        from nemo_read.probe_base import CanonicalProber

        class P(CanonicalProber):
            PROBE_NAME = "p"
        # Path with literal lone "_" segment (unusual but possible)
        assert P()._is_projection_branch("Demand\\_\\foo") is False


class TestEmissionExcludeDefault:
    def test_seven_emission_vars_in_default_exclude(self):
        from nemo_read.probe_base import DEFAULT_EMISSION_VARS_EXCLUDE

        # All 7 variables we identified from the 2026-05-18 probe
        expected = {
            "Avg Environmental Loading",
            "Pollutant Loadings",
            "One_Hundred Year GWP Direct and Indirect Allocated to Demands",
            "One_Hundred Year GWP Indirect Allocated to Demands",
            "One_Hundred Year GWP Direct At Point of Emissions",
            "Twenty Year GWP Direct At Point of Emissions",
            "Five_Hundred Year GWP Direct At Point of Emissions",
        }
        assert DEFAULT_EMISSION_VARS_EXCLUDE == expected

    def test_subclass_can_override_exclude(self):
        from nemo_read.probe_base import CanonicalProber

        class NoExclusion(CanonicalProber):
            PROBE_NAME = "no_excl"
            EMISSION_VARS_EXCLUDE = frozenset()

        p = NoExclusion()
        assert len(p.EMISSION_VARS_EXCLUDE) == 0

    def test_skip_projection_class_attr_overridable(self):
        from nemo_read.probe_base import CanonicalProber

        class KeepProjection(CanonicalProber):
            PROBE_NAME = "keep_proj"
            SKIP_PROJECTION_LAYERS = False

        assert KeepProjection.SKIP_PROJECTION_LAYERS is False
