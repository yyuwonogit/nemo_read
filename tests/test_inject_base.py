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

    PORTABLE CHOKEPOINT COPIES: a script whose documented contract is
    "runs with no nemo_read import" (handed to a team without the repo)
    may carry ONE inline copy of the chokepoint. It is exempted from the
    textual scan — but the companion test below pins its SHAPE by AST:
    exactly one `.Expression =` assignment, inside a function named
    `safe_set_expression`, guarded by normalize_interp +
    assert_interp_canonical calls. Any drift fails CI.
    """

    EXPRESSION_SETTER_RE = re.compile(r"\.Expression\s*=")
    SCAN_ROOTS = ("inject", "mailbox", "result")
    # rel-posix paths of documented portable chokepoint copies
    PORTABLE_CHOKEPOINT_COPIES = {
        "inject/residential/20260625/inject_fridge_leap.py",
        "mailbox/20260813/inject_higheff_patch.py",
    }

    def test_no_direct_expression_writes(self):
        violators = []
        for root in self.SCAN_ROOTS:
            root_path = REPO_ROOT / root
            if not root_path.exists():
                continue
            for py_file in root_path.rglob("*.py"):
                rel_posix = py_file.relative_to(REPO_ROOT).as_posix()
                if rel_posix in self.PORTABLE_CHOKEPOINT_COPIES:
                    continue  # shape-pinned by the companion test below
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

    @pytest.mark.parametrize("rel", sorted(PORTABLE_CHOKEPOINT_COPIES))
    def test_portable_chokepoint_copy_holds_its_shape(self, rel):
        """The exemption is pinned, not blind: the portable copy must hold
        EXACTLY one `.Expression =` assignment, inside `safe_set_expression`,
        with normalize_interp + assert_interp_canonical called in the same
        function body. Anything else fails — retire or fix the exemption."""
        import ast

        p = REPO_ROOT / rel
        assert p.exists(), f"portable copy gone — remove {rel} from the exemption set"
        tree = ast.parse(p.read_text(encoding="utf-8"))

        expr_assigns = []          # (inside_fn_name, lineno)
        fn_stack: list[str] = []

        class V(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                fn_stack.append(node.name)
                self.generic_visit(node)
                fn_stack.pop()

            def visit_Assign(self, node):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Attribute) and tgt.attr == "Expression":
                        expr_assigns.append(
                            (fn_stack[-1] if fn_stack else None, node.lineno))
                self.generic_visit(node)

        V().visit(tree)
        assert len(expr_assigns) == 1, (
            f"{rel}: expected exactly 1 `.Expression =` site, found "
            f"{[(f, ln) for f, ln in expr_assigns]}")
        fn_name, _ = expr_assigns[0]
        assert fn_name == "safe_set_expression", (
            f"{rel}: the write site must live inside safe_set_expression, "
            f"found it in {fn_name!r}")

        # the guarding calls must exist inside that same function
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "safe_set_expression")
        called = {n.func.id for n in ast.walk(fn)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert {"normalize_interp", "assert_interp_canonical"} <= called, (
            f"{rel}: safe_set_expression must call normalize_interp and "
            f"assert_interp_canonical before writing (found calls: {sorted(called)})")


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


class _RecordingStrictRegions:
    """Emulates LEAP: raises on a region name that doesn't exist (a group
    LABEL like power's 'Other' fires a LEAP error dialog), records calls."""

    KNOWN = {
        "Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar",
        "Philippines", "Singapore", "Thailand", "Timor Leste", "Vietnam",
        "Base Template",
    }

    def __init__(self):
        self.calls: list[str] = []

    def __call__(self, name):
        self.calls.append(name)
        if name not in self.KNOWN:
            raise RuntimeError(f"LEAP error: no region named {name!r}")
        return f"<region:{name}>"


class TestGroupLabelNeverReachesLeapRegions:
    """Regression (2026-07-07): power's 3-cache group key 'Other' was passed
    verbatim to `leap.Regions()` at every group transition in
    `_execute_phase`, firing a LEAP error dialog each run. The framework
    must resolve a group label to a real member region before the COM call."""

    def _run_phase(self, groups):
        import argparse
        from collections import Counter

        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"

        leap = _StubLeap({"B1": _StubBranch({"V": "x"})})
        leap.Regions = _RecordingStrictRegions()
        args = argparse.Namespace(dry_run=True, fail_fast=False, blind=True)
        inj = Probe()
        counts, failures, committed = inj._execute_phase(
            leap, groups, caches={}, args=args, dry_run=True)
        return leap, counts

    def test_group_label_resolved_to_member_region(self):
        rows = [
            {"ams": "Brunei", "branch": "B1", "variable": "V",
             "expression": "x"},
            {"ams": "Vietnam", "branch": "B1", "variable": "V",
             "expression": "x"},
        ]
        leap, counts = self._run_phase({"Other": rows})
        assert "Other" not in leap.Regions.calls
        assert leap.Regions.calls[0] == "Brunei"  # first member, sorted
        assert counts["dry_run"] == 2

    def test_real_region_key_passed_through_unchanged(self):
        rows = [{"ams": "Cambodia", "branch": "B1", "variable": "V",
                 "expression": "x"}]
        leap, counts = self._run_phase({"Cambodia": rows})
        assert leap.Regions.calls[0] == "Cambodia"
        assert counts["dry_run"] == 1


# ---------------------------------------------------------------------------
# 7. compare_expressions semantics
# ---------------------------------------------------------------------------

class TestTimorLesteSupplement:
    """v0.7.0 — every inject MUST explicitly opt in or out of Timor Leste."""

    def test_runtime_refuses_without_tl_decision(self, tmp_path, capsys):
        """Injector exits non-zero if neither --include nor --exclude flag passed."""
        import csv as _csv

        class Probe(CanonicalInjector):
            SECTOR_NAME = "tl_test"
            DEFAULT_CSV = tmp_path / "main.csv"

        # Write a minimal valid main CSV
        p = tmp_path / "main.csv"
        with p.open("w", encoding="utf-8", newline="") as f:
            w = _csv.writer(f)
            w.writerow(["ams", "branch", "variable", "expression"])
            w.writerow(["Brunei", "X", "Y", "Interp(2025, 1.0)"])

        # No TL flag → must refuse
        rc = Probe().run(argv=[])
        assert rc == 8  # exit code 8 = TL decision missing

    def test_runtime_proceeds_with_exclude_flag(self, tmp_path):
        import csv as _csv

        class Probe(CanonicalInjector):
            SECTOR_NAME = "tl_test"
            DEFAULT_CSV = tmp_path / "main.csv"

        p = tmp_path / "main.csv"
        with p.open("w", encoding="utf-8", newline="") as f:
            w = _csv.writer(f)
            w.writerow(["ams", "branch", "variable", "expression"])
            w.writerow(["Brunei", "X", "Y", "Interp(2025, 1.0)"])

        # --exclude-timor-leste passes the TL check, but the inject still
        # fails downstream at LEAP COM dispatch (no LEAP). We're not
        # asserting exit 0 here — we're asserting exit != 8 (the TL gate
        # didn't trip).
        rc = Probe().run(argv=["--exclude-timor-leste"])
        assert rc != 8  # passed the TL gate

    def test_subclass_can_opt_out_entirely(self, tmp_path):
        """A subclass with TIMOR_LESTE_SUPPLEMENT_NOT_APPLICABLE=True
        bypasses the TL gate entirely."""
        import csv as _csv

        class OptOut(CanonicalInjector):
            SECTOR_NAME = "opt_out"
            DEFAULT_CSV = tmp_path / "m.csv"
            TIMOR_LESTE_SUPPLEMENT_NOT_APPLICABLE = True

        p = tmp_path / "m.csv"
        with p.open("w", encoding="utf-8", newline="") as f:
            w = _csv.writer(f)
            w.writerow(["ams", "branch", "variable", "expression"])
            w.writerow(["Brunei", "X", "Y", "Interp(2025, 1.0)"])

        rc = OptOut().run(argv=[])  # no TL flag, no error
        assert rc != 8

    def test_mutually_exclusive_flags(self, tmp_path):
        """--include-timor-leste and --exclude-timor-leste can't both be set."""
        import argparse

        class P(CanonicalInjector):
            SECTOR_NAME = "p"

        parser = P().build_arg_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--include-timor-leste", "--exclude-timor-leste"])

    def test_help_text_mentions_timor_leste(self):
        class P(CanonicalInjector):
            SECTOR_NAME = "p"
        parser = P().build_arg_parser()
        help_text = parser.format_help()
        assert "--include-timor-leste" in help_text
        assert "--exclude-timor-leste" in help_text


class TestTimorLesteSupplementFiles:
    """v0.7.0 — every domain MUST ship a timor_leste_supplement.csv next
    to its main canonical (§A.18 CI tripwire)."""

    DOMAINS_REQUIRING_SUPPLEMENT = [
        ("inject/bioenergy/canonical_leap_inputs.csv",
         "inject/bioenergy/timor_leste_supplement.csv"),
        ("inject/fossil/canonical_leap_inputs.csv",
         "inject/fossil/timor_leste_supplement.csv"),
    ]

    @pytest.mark.parametrize("main_csv,supplement_csv",
                             DOMAINS_REQUIRING_SUPPLEMENT)
    def test_supplement_exists(self, main_csv, supplement_csv):
        from pathlib import Path
        main = REPO_ROOT / main_csv
        supplement = REPO_ROOT / supplement_csv
        if not main.exists():
            pytest.skip(f"{main_csv} not present; skip supplement check")
        assert supplement.exists(), (
            f"Missing required supplement: {supplement_csv}\n"
            f"Every domain with a canonical_leap_inputs.csv must ship a\n"
            f"sibling timor_leste_supplement.csv per CLAUDE.md §A.18. "
            f"It can be near-empty (header + a few rows) but must exist."
        )

    @pytest.mark.parametrize("main_csv,supplement_csv",
                             DOMAINS_REQUIRING_SUPPLEMENT)
    def test_supplement_only_has_timor_leste_rows(self, main_csv,
                                                   supplement_csv):
        from pathlib import Path
        import csv as _csv
        supplement = REPO_ROOT / supplement_csv
        if not supplement.exists():
            pytest.skip(f"{supplement_csv} not present")
        with supplement.open("r", encoding="utf-8", newline="") as f:
            reader = _csv.DictReader(f)
            non_tl = [r for r in reader if r.get("ams") != "Timor Leste"]
        assert not non_tl, (
            f"{supplement_csv} contains {len(non_tl)} non-Timor-Leste row(s). "
            f"The supplement file must contain ONLY ams='Timor Leste' rows; "
            f"all other AMS belong in the main canonical."
        )

    @pytest.mark.parametrize("main_csv,supplement_csv",
                             DOMAINS_REQUIRING_SUPPLEMENT)
    def test_main_canonical_has_no_timor_leste_rows(self, main_csv,
                                                     supplement_csv):
        """Main canonical and supplement must be disjoint on ams=Timor Leste."""
        from pathlib import Path
        import csv as _csv
        main = REPO_ROOT / main_csv
        if not main.exists():
            pytest.skip(f"{main_csv} not present")
        with main.open("r", encoding="utf-8", newline="") as f:
            reader = _csv.DictReader(f)
            tl_in_main = [r for r in reader if r.get("ams") == "Timor Leste"]
        assert not tl_in_main, (
            f"{main_csv} has {len(tl_in_main)} Timor Leste row(s). "
            f"Move them to {supplement_csv} — main canonical must NOT "
            f"contain ams='Timor Leste' rows (§A.18)."
        )


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


# ---------------------------------------------------------------------------
# 8. Scenario-column row filter (§A.X — added 2026-05-20)
# ---------------------------------------------------------------------------

class TestFilterRowsForScenario:
    """A canonical that carries a per-row `scenario` column ships one row
    per (branch, ams, scenario). The framework must filter to the current
    scenario before pushing — otherwise every scenario iteration writes
    ALL scenario-tagged rows into ActiveScenario (last-writer-wins
    corruption on shared branches).

    Pre-fix bug: transport canonical 2026-05-19 had 4 scenario-tagged
    rows per shared branch; all 4 wrote under every scenario, so e.g.
    Current Accounts ended up holding RAS values.

    Untagged rows (no `scenario` column at all, or empty value) MUST
    pass through to every scenario — that's bioenergy/fossil/power's
    LEAP-scenario-inheritance semantics.
    """

    def test_untagged_rows_pass_through(self):
        rows = [
            {"ams": "Brunei", "branch": "B", "variable": "V"},  # no scenario key
            {"ams": "Brunei", "branch": "B", "variable": "V", "scenario": ""},
            {"ams": "Brunei", "branch": "B", "variable": "V", "scenario": "   "},
        ]
        out = CanonicalInjector._filter_rows_for_scenario(rows, "Baseline Simulation")
        assert len(out) == 3, "untagged/empty/whitespace rows must pass through"

    def test_tagged_rows_filtered_by_scenario(self):
        rows = [
            {"ams": "Brunei", "branch": "B", "variable": "V",
             "scenario": "Baseline Simulation", "expression": "BAS_EXPR"},
            {"ams": "Brunei", "branch": "B", "variable": "V",
             "scenario": "AMS Target Scenario", "expression": "ATS_EXPR"},
            {"ams": "Brunei", "branch": "B", "variable": "V",
             "scenario": "Current Accounts", "expression": "CA_EXPR"},
            {"ams": "Brunei", "branch": "B", "variable": "V",
             "scenario": "Regional Aspiration Scenario", "expression": "RAS_EXPR"},
        ]
        out = CanonicalInjector._filter_rows_for_scenario(rows, "Baseline Simulation")
        assert len(out) == 1
        assert out[0]["expression"] == "BAS_EXPR"

    def test_mixed_tagged_and_untagged(self):
        rows = [
            {"ams": "Brunei", "branch": "B1", "variable": "V"},                 # untagged
            {"ams": "Brunei", "branch": "B2", "variable": "V", "scenario": ""},  # empty
            {"ams": "Brunei", "branch": "B3", "variable": "V",
             "scenario": "Baseline Simulation"},                                # match
            {"ams": "Brunei", "branch": "B4", "variable": "V",
             "scenario": "Current Accounts"},                                   # no match
        ]
        out = CanonicalInjector._filter_rows_for_scenario(rows, "Baseline Simulation")
        assert {r["branch"] for r in out} == {"B1", "B2", "B3"}

    def test_no_scenario_matches_returns_empty(self):
        rows = [
            {"ams": "Brunei", "branch": "B", "variable": "V",
             "scenario": "Current Accounts"},
            {"ams": "Brunei", "branch": "B", "variable": "V",
             "scenario": "AMS Target Scenario"},
        ]
        out = CanonicalInjector._filter_rows_for_scenario(rows, "Baseline Simulation")
        assert out == []

    def test_preserves_row_order(self):
        rows = [
            {"branch": "first", "scenario": "X"},
            {"branch": "second"},
            {"branch": "third", "scenario": "X"},
            {"branch": "fourth", "scenario": "Y"},  # filtered out
            {"branch": "fifth"},
        ]
        out = CanonicalInjector._filter_rows_for_scenario(rows, "X")
        assert [r["branch"] for r in out] == ["first", "second", "third", "fifth"]

    def test_bioenergy_canonical_no_scenario_column_unaffected(self, tmp_path):
        """End-to-end: a bioenergy-shape canonical (no scenario column)
        must have every row pass through for any scenario name."""
        import csv as _csv
        rows = []
        with (tmp_path / "bio.csv").open("w", encoding="utf-8", newline="") as f:
            w = _csv.writer(f)
            w.writerow(["ams", "branch", "variable", "expression"])
            for ams in ("Brunei", "Cambodia", "Indonesia"):
                w.writerow([ams, "X", "Y", "Interp(2025, 1.0)"])
        with (tmp_path / "bio.csv").open("r", encoding="utf-8") as f:
            rows = list(_csv.DictReader(f))
        out = CanonicalInjector._filter_rows_for_scenario(rows, "any_scenario_name")
        assert len(out) == 3


# ---------------------------------------------------------------------------
# 9. Decimal-separator regional classifier (§A.15 reinforcement, 2026-05-20)
# ---------------------------------------------------------------------------

class TestClassifyDecimalSeparator:
    """Pure-function classifier for LEAP regional decimal detection.
    The COM-touching `verify_leap_decimal_is_period` builds on top of
    this and isn't unit-testable without LEAP, but the classifier itself
    is fully testable.

    Discovered 2026-05-20: this LEAP install's regional decimal can
    differ from Windows en-US assumption. Comma-decimal storage produces
    ambiguous Interp() round-trips that `compare_expressions` can't
    classify (returns FAIL even when values are correct).
    """

    def test_period_decimal_simple(self):
        from nemo_read._leap_com import classify_decimal_separator
        assert classify_decimal_separator("Interp(2025, 1.5, 2030, 2.0)") == "period"

    def test_comma_decimal_simple(self):
        from nemo_read._leap_com import classify_decimal_separator
        assert classify_decimal_separator("Interp(2025, 1,5, 2030, 2,0)") == "comma"

    def test_period_decimal_real_world(self):
        from nemo_read._leap_com import classify_decimal_separator
        # Actual transport KA Activity Level expression we wrote (period decimal)
        assert classify_decimal_separator(
            "Interp(2006, 50, 2007, 32.6709, 2008, 33.651, 2009, 34.6605, "
            "2010, 35.7004, 2011, 36.7714)"
        ) == "period"

    def test_comma_decimal_real_world(self):
        from nemo_read._leap_com import classify_decimal_separator
        # Actual transport KA Activity Level read-back under comma-decimal regional
        assert classify_decimal_separator(
            "Interp(2006, 50, 2007, 32,6709, 2008, 33,651, 2009, 34,6605, "
            "2010, 35,7004, 2011, 36,7714)"
        ) == "comma"

    def test_integer_only_returns_unknown(self):
        from nemo_read._leap_com import classify_decimal_separator
        # No decimal evidence either way → can't determine
        assert classify_decimal_separator(
            "Interp(2025, 50, 2030, 60, 2035, 70)"
        ) == "unknown"

    def test_empty_returns_unknown(self):
        from nemo_read._leap_com import classify_decimal_separator
        assert classify_decimal_separator("") == "unknown"
        assert classify_decimal_separator(None) == "unknown"

    def test_no_interp_returns_unknown(self):
        from nemo_read._leap_com import classify_decimal_separator
        assert classify_decimal_separator("Step(2025, 1.5)") == "unknown"

    def test_too_few_tokens_returns_unknown(self):
        from nemo_read._leap_com import classify_decimal_separator
        # Need at least 2 year-value pairs (4 tokens) to confidently classify
        assert classify_decimal_separator("Interp(2025, 1.5)") == "unknown"

    def test_period_decimal_negative_values(self):
        from nemo_read._leap_com import classify_decimal_separator
        assert classify_decimal_separator(
            "Interp(2025, -1.5, 2030, -2.7, 2035, 3.1)"
        ) == "period"


class TestZeroExistingCapacityVsHistoricalProduction:
    """§11.2b tripwire — Existing Capacity = 0 in a year where Historical
    Production is non-zero halts the LEAP calc. Burn: 2026-07-09, Malaysia
    Diesel_MYPE (2021) + Biomass Other_MYSR (2023/24); modeller hand-deleted
    the zero points in the engine."""

    def _write(self, tmp_path, rows):
        import csv as _csv
        p = tmp_path / "c.csv"
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = _csv.writer(fh)
            w.writerow(["ams", "branch", "variable", "expression", "scenario"])
            w.writerows(rows)
        return p

    def test_exact_burn_case_is_flagged(self, tmp_path):
        from nemo_read import find_zero_existing_capacity_conflicts as f
        bs = chr(92)
        b = f"Transformation{bs}Centralized Electricity Generation{bs}Processes{bs}Diesel_MYPE"
        p = self._write(tmp_path, [
            ["Malaysia", b, "Existing Capacity",
             "Interp(2020, 60.1, 2021, 0, 2022, 35.23, FirstScenarioYear, 0)",
             "Current Accounts"],
            ["Malaysia", b, "Historical Production",
             "Interp(2020, 185.2, 2021, 155.8, 2022, 190.0)",
             "Current Accounts"],
        ])
        v = f(p)
        assert len(v) == 1
        assert v[0][1] == "Malaysia" and v[0][2] == "Diesel_MYPE" and v[0][3] == 2021

    def test_zero_hp_at_zero_year_is_clean(self, tmp_path):
        from nemo_read import find_zero_existing_capacity_conflicts as f
        p = self._write(tmp_path, [
            ["Malaysia", "T\P\X", "Existing Capacity",
             "Interp(2020, 60, 2021, 0)", "Current Accounts"],
            ["Malaysia", "T\P\X", "Historical Production",
             "Interp(2020, 100, 2021, 0)", "Current Accounts"],
        ])
        assert f(p) == []

    def test_no_hp_row_is_unknown_not_conflict(self, tmp_path):
        from nemo_read import find_zero_existing_capacity_conflicts as f
        p = self._write(tmp_path, [
            ["Malaysia", "T\P\X", "Existing Capacity",
             "Interp(2020, 60, 2021, 0)", "Current Accounts"],
        ])
        assert f(p) == []

    def test_firstscenarioyear_tail_not_flagged(self, tmp_path):
        from nemo_read import find_zero_existing_capacity_conflicts as f
        p = self._write(tmp_path, [
            ["Malaysia", "T\P\X", "Existing Capacity",
             "Interp(2020, 60, 2024, 50, FirstScenarioYear, 0)", "Current Accounts"],
            ["Malaysia", "T\P\X", "Historical Production",
             "Interp(2020, 100, 2024, 90)", "Current Accounts"],
        ])
        assert f(p) == []

    def test_hp_interpolated_between_points_is_caught(self, tmp_path):
        from nemo_read import find_zero_existing_capacity_conflicts as f
        p = self._write(tmp_path, [
            ["Malaysia", "T\P\X", "Existing Capacity",
             "Interp(2020, 60, 2023, 0)", "Current Accounts"],
            ["Malaysia", "T\P\X", "Historical Production",
             "Interp(2020, 100, 2024, 60)", "Current Accounts"],  # 2023 ~ 70 by interp
        ])
        v = f(p)
        assert len(v) == 1 and v[0][3] == 2023

    def test_preflight_reports_conflict(self, tmp_path):
        from nemo_read.inject_base import CanonicalInjector
        class Probe(CanonicalInjector):
            SECTOR_NAME = "probe"
        p = self._write(tmp_path, [
            ["Malaysia", "T\P\X", "Existing Capacity",
             "Interp(2020, 60, 2021, 0)", "Current Accounts"],
            ["Malaysia", "T\P\X", "Historical Production",
             "Interp(2020, 100, 2022, 100)", "Current Accounts"],
        ])
        errs = Probe()._preflight_csv(p)
        assert any("11.2b" in e for e in errs)
