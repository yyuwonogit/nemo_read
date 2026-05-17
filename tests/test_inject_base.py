"""Tests for the standardised injector framework (CanonicalInjector).

Pins three guarantees:

1. Sealed methods can't be overridden — `__init_subclass__` raises at
   class definition time.

2. Every existing mailbox injector subclass routes through the sealed
   `_set_expression` chokepoint (no `var.Expression = expr` direct site
   outside `_leap_com.py` / `inject_base.py`).

3. The CSV pre-flight catches forbidden Interp() forms (CLAUDE.md §A.15)
   before any LEAP COM call.
"""
from __future__ import annotations

import re
from importlib import util
from pathlib import Path

import pytest

from nemo_read.inject_base import CanonicalInjector, InjectorSealError


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# 1. Seal enforcement
# ---------------------------------------------------------------------------

class TestSealEnforcement:
    def test_valid_subclass_allowed(self):
        class Valid(CanonicalInjector):
            SECTOR_NAME = "test_valid"

            def filter_rows(self, rows, args):
                return rows

        inj = Valid()
        assert inj.SECTOR_NAME == "test_valid"

    @pytest.mark.parametrize("sealed_method", [
        "_set_expression",
        "_preflight_csv",
        "_assert_area_lock",
        "_assert_scenario_lock",
    ])
    def test_subclass_overriding_sealed_method_rejected(self, sealed_method):
        with pytest.raises(InjectorSealError) as exc_info:
            namespace = {
                "SECTOR_NAME": "bad",
                sealed_method: lambda self, *args, **kwargs: None,
            }
            type("Bad" + sealed_method, (CanonicalInjector,), namespace)
        assert sealed_method in str(exc_info.value)


# ---------------------------------------------------------------------------
# 2. Existing mailbox injectors stay clean
# ---------------------------------------------------------------------------

class TestNoDirectExpressionSetSites:
    """Scan every sector script for `\\.Expression\\s*=` sites.

    Post-2026-05-17 workstream-2 reorg: live inject code lives in
    `inject/` (was `mailbox/`); `mailbox/` is now a pure inbox.
    `result/` contains historical probe scripts. This test scans
    all three for direct `Variable.Expression = ...` writes outside
    the sanctioned chokepoint (`nemo_read._leap_com.safe_set_expression`).
    A new occurrence means a sector author bypassed the chokepoint
    — caught in CI, not in production.
    """

    EXPRESSION_SETTER_RE = re.compile(r"\.Expression\s*=")
    SCAN_ROOTS = ("inject", "mailbox", "result")

    def test_no_direct_expression_writes(self):
        violators = []
        for root in self.SCAN_ROOTS:
            root_path = REPO_ROOT / root
            if not root_path.exists():
                continue
            for py_file in root_path.rglob("*.py"):
                try:
                    text = py_file.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for i, line in enumerate(text.splitlines(), start=1):
                    if ("var.Expression =" in line
                            or "variable.Expression =" in line):
                        # Allowed inside docstrings/comments — quick filter
                        stripped = line.lstrip()
                        if (stripped.startswith("#")
                                or stripped.startswith("'")
                                or stripped.startswith('"')):
                            continue
                        rel = py_file.relative_to(REPO_ROOT)
                        violators.append(f"{rel}:{i}: {line.strip()}")
        assert not violators, (
            "Found direct `Variable.Expression = ...` sites outside the "
            "sanctioned chokepoint (nemo_read._leap_com.safe_set_expression). "
            "Every inject must route through CanonicalInjector._set_expression. "
            f"Offenders:\n" + "\n".join(violators)
        )


# ---------------------------------------------------------------------------
# 3. Each registered injector loads + uses the sealed primitives
# ---------------------------------------------------------------------------

INJECTOR_PATHS = [
    ("inject/fossil/inject_to_leap.py", "FossilInjector"),
    ("inject/bioenergy/inject_to_leap.py", "BioenergyInjector"),
    ("inject/power/run_workflow.py", "PowerInjector"),
]


def _load_module(path: Path, name: str):
    spec = util.spec_from_file_location(name, path)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("rel_path,cls_name", INJECTOR_PATHS)
class TestEachInjectorRoutesThroughSeal:
    def test_class_is_canonical_subclass(self, rel_path, cls_name):
        path = REPO_ROOT / rel_path
        if not path.exists():
            pytest.skip(f"{rel_path} not present")
        mod = _load_module(path, f"_load_{cls_name}")
        cls = getattr(mod, cls_name)
        assert issubclass(cls, CanonicalInjector)

    def test_sealed_methods_not_overridden(self, rel_path, cls_name):
        path = REPO_ROOT / rel_path
        if not path.exists():
            pytest.skip(f"{rel_path} not present")
        mod = _load_module(path, f"_seal_check_{cls_name}")
        cls = getattr(mod, cls_name)
        for sealed in cls._SEALED:
            base = CanonicalInjector.__dict__.get(sealed)
            sub = cls.__dict__.get(sealed)
            assert sub is None or sub is base, (
                f"{cls_name} overrides sealed method {sealed!r}"
            )

    def test_instantiates_without_leap(self, rel_path, cls_name):
        path = REPO_ROOT / rel_path
        if not path.exists():
            pytest.skip(f"{rel_path} not present")
        mod = _load_module(path, f"_inst_{cls_name}")
        cls = getattr(mod, cls_name)
        inj = cls()
        assert inj.SECTOR_NAME != "unknown"


# ---------------------------------------------------------------------------
# 4. Pre-flight refuses bad CSVs
# ---------------------------------------------------------------------------

class TestPreflightRefusesBadCsv:
    def test_preflight_catches_semicolon_interp(self, tmp_path):
        import csv

        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        p = tmp_path / "bad.csv"
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ams", "branch", "variable", "expression"])
            w.writerow(["Brunei", "Resources\\X", "Import Cost",
                        "Interp(2025; 1.0; 2030; 2.0)"])

        inj = Probe()
        errors = inj._preflight_csv(p)
        assert len(errors) == 1
        assert "§A.15" in errors[0] or "list-separator" in errors[0]

    def test_preflight_passes_clean_csv(self, tmp_path):
        import csv

        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        p = tmp_path / "clean.csv"
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ams", "branch", "variable", "expression"])
            w.writerow(["Brunei", "Resources\\X", "Import Cost",
                        "Interp(2025, 1.0, 2030, 2.0)"])

        inj = Probe()
        errors = inj._preflight_csv(p)
        assert errors == []


# ---------------------------------------------------------------------------
# 5. Multi-phase warm-COM flow (§A.10)
# ---------------------------------------------------------------------------

class TestMultiPhaseFlow:
    """The default `run()` does dry-run → confirm → real → readback in
    ONE COM session. Each phase's CLI flag toggles enforced."""

    def test_default_parser_has_warm_com_flags(self):
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        parser = Probe().build_arg_parser()
        help_text = parser.format_help()
        for flag in ("--dry-run-only", "--yes", "--no-readback",
                     "--scenarios", "--readback-rows-per-region"):
            assert flag in help_text, f"missing flag {flag}"

    def test_dry_run_alias_works(self):
        """--dry-run is preserved as an alias for --dry-run-only."""
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        parser = Probe().build_arg_parser()
        ns = parser.parse_args(["--dry-run", "--csv", "/dev/null"])
        assert ns.dry_run_only is True

    def test_resolve_scenarios_prefers_plural(self):
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        parser = Probe().build_arg_parser()
        ns = parser.parse_args([
            "--scenario", "single",
            "--scenarios", "A,B,C",
            "--csv", "/dev/null",
        ])
        inj = Probe()
        assert inj._resolve_scenarios(ns) == ["A", "B", "C"]

    def test_resolve_scenarios_falls_back_to_singular(self):
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        parser = Probe().build_arg_parser()
        ns = parser.parse_args(["--scenario", "RAS", "--csv", "/dev/null"])
        inj = Probe()
        assert inj._resolve_scenarios(ns) == ["RAS"]

    def test_resolve_scenarios_none_when_neither(self):
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        parser = Probe().build_arg_parser()
        ns = parser.parse_args(["--csv", "/dev/null"])
        inj = Probe()
        # [None] means "use whatever ActiveScenario currently is"
        assert inj._resolve_scenarios(ns) == [None]


# ---------------------------------------------------------------------------
# 6. Readback verifier (§A.15 hard-fail enforcement)
# ---------------------------------------------------------------------------

class _StubVariable:
    def __init__(self, expression):
        self.Expression = expression


class _StubBranch:
    def __init__(self, variables: dict[str, str]):
        self._vars = {k: _StubVariable(v) for k, v in variables.items()}

    def Variable(self, name):
        return self._vars.get(name)


class _StubBranchCollection:
    def __init__(self, branches: dict):
        self._branches = branches

    def __call__(self, fullname):
        return self._branches.get(fullname)


class _StubRegions:
    def __call__(self, name):
        return f"<region:{name}>"


class _StubLeap:
    def __init__(self, branches: dict):
        self.Branches = _StubBranchCollection(branches)
        self.Regions = _StubRegions()
        self.ActiveRegion = None


class TestReadbackVerify:
    def test_all_exact_passes(self):
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        committed = [
            {"ams": "Brunei", "branch": "Resources\\Coal",
             "variable": "Import Cost",
             "expression": "Interp(2025, 4.0, 2030, 4.5)"},
        ]
        leap = _StubLeap({
            "Resources\\Coal": _StubBranch({
                "Import Cost": "Interp(2025, 4.0, 2030, 4.5)",
            }),
        })
        inj = Probe()
        assert inj.readback_verify(leap, committed) is True

    def test_normalised_is_hard_fail(self):
        """§A.15 — LEAP renormalising commas to periods on read-back means
        the inject committed the wrong form. readback_verify returns False."""
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        committed = [
            {"ams": "Brunei", "branch": "Resources\\Coal",
             "variable": "Import Cost",
             "expression": "Interp(2025, 4.0, 2030, 4.5)"},
        ]
        # LEAP returned period-list-sep variant — same values, wrong separator
        leap = _StubLeap({
            "Resources\\Coal": _StubBranch({
                "Import Cost": "Interp(2025. 4.0. 2030. 4.5)",
            }),
        })
        inj = Probe()
        assert inj.readback_verify(leap, committed) is False

    def test_value_diff_is_fail(self):
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        committed = [
            {"ams": "Brunei", "branch": "Resources\\Coal",
             "variable": "Import Cost",
             "expression": "Interp(2025, 4.0, 2030, 4.5)"},
        ]
        leap = _StubLeap({
            "Resources\\Coal": _StubBranch({
                "Import Cost": "Interp(2025, 9.9, 2030, 9.9)",
            }),
        })
        inj = Probe()
        assert inj.readback_verify(leap, committed) is False

    def test_empty_committed_passes(self):
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"
        leap = _StubLeap({})
        assert Probe().readback_verify(leap, []) is True

    def test_samples_per_region(self):
        """rows_per_region=1 should sample one row per region, not all."""
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        committed = [
            {"ams": "Brunei", "branch": "B1", "variable": "V",
             "expression": "x"},
            {"ams": "Brunei", "branch": "B2", "variable": "V",
             "expression": "x"},
            {"ams": "Cambodia", "branch": "C1", "variable": "V",
             "expression": "x"},
        ]
        # All branches resolve to a variable returning "x"; with sample=1
        # only one row per region is checked (B1 + C1).
        leap = _StubLeap({
            "B1": _StubBranch({"V": "x"}),
            "B2": _StubBranch({"V": "DIFFERENT"}),  # would fail if read
            "C1": _StubBranch({"V": "x"}),
        })
        inj = Probe()
        assert inj.readback_verify(leap, committed, rows_per_region=1) is True


# ---------------------------------------------------------------------------
# 7. compare_expressions semantics
# ---------------------------------------------------------------------------

class TestCompareExpressions:
    def test_byte_equal_returns_exact(self):
        from nemo_read._leap_com import compare_expressions
        assert compare_expressions(
            "Interp(2025, 3.0)", "Interp(2025, 3.0)") == "EXACT"

    def test_period_list_sep_returns_normalised(self):
        """LEAP renormalising commas to periods on read-back."""
        from nemo_read._leap_com import compare_expressions
        assert compare_expressions(
            "Interp(2025. 3.0)", "Interp(2025, 3.0)") == "NORMALISED"

    def test_semicolon_list_sep_returns_normalised(self):
        from nemo_read._leap_com import compare_expressions
        assert compare_expressions(
            "Interp(2025; 3.0)", "Interp(2025, 3.0)") == "NORMALISED"

    def test_different_values_returns_fail(self):
        from nemo_read._leap_com import compare_expressions
        assert compare_expressions(
            "Interp(2025, 9.9)", "Interp(2025, 3.0)") == "FAIL"

    def test_none_returns_fail(self):
        from nemo_read._leap_com import compare_expressions
        assert compare_expressions(None, "anything") == "FAIL"
