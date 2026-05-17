"""Pytest tripwire — every public class/function in `nemo_read/` MUST
be re-exported in `nemo_read/__init__.py`'s `__all__`.

Established 2026-05-17 after I shipped `CanonicalInjector`,
`CanonicalProber`, and `HeartbeatLogger` in their respective modules
but forgot to re-export them at the top level. CLAUDE.md §14 + §15.1
both stated the rule; both were advisory; the user caught the
omission at install time. Per §A.7, that's a destructive failure
mode and gets a tripwire — not just a stricter prose rule.

This test enforces:

  For every `nemo_read/<module>.py` (NOT `__init__.py`, NOT
  `__pycache__`), AST-walk the module. For each top-level `class` or
  `def` whose name does NOT start with `_`, assert the name is in
  `nemo_read.__all__`.

Rationale: leading `_` = internal-by-convention. Anything without `_`
is meant to be a public API surface — and the entire point of
`__all__` is to declare the public surface. If you defined `class
Foo:` in `nemo_read/bar.py` and didn't re-export it, either:
  (a) you forgot — fix `__init__.py`, or
  (b) it's not meant to be public — rename to `_Foo`.

Both fixes are cheap; the bug they prevent (shipping a class users
think they can `from nemo_read import Foo`) is not.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

import nemo_read


REPO_ROOT = Path(__file__).resolve().parents[1]
NEMO_READ_DIR = REPO_ROOT / "nemo_read"

# Modules that begin with `_` are conventionally internal — by default
# we DON'T require their classes/functions in __all__. But some of
# them intentionally house public-API names (`_leap_com.py`,
# `_heartbeat.py` after 2026-05-17). For those, list them here so the
# check still runs.
INTERNAL_MODULES_WITH_PUBLIC_API = {
    "_leap_com",   # safe_set_expression, normalize_interp, compare_expressions,
                   # validate_canonical_csv_expressions, assert_interp_canonical,
                   # InterpSeparatorError
    "_heartbeat",  # HeartbeatLogger, read_progress
}

# Names defined at module level that ARE intentionally NOT in
# nemo_read.__all__, despite not having a leading underscore. Two
# legitimate cases:
#
#   (a) CLI entry points referenced from pyproject.toml's
#       [project.scripts] (e.g., `cli_main`). These get installed as
#       console scripts; users invoke them as commands, not as
#       `from nemo_read import cli_main`.
#
#   (b) **TODO: pre-2026-05-17 technical debt.** The block below
#       enumerates classes/functions that EXIST in module files but
#       were never wired into __init__.py. They should be triaged:
#       either (i) added to __all__ if genuinely public, or (ii)
#       renamed with a leading `_` if internal. Tracked in the same
#       commit that introduced the tripwire — see CLAUDE.md §14.
#
# The tripwire actively prevents NEW gaps in (a) and (b). It does NOT
# block on draining the existing debt; future cleanup can shrink this
# whitelist incrementally.
INTENTIONALLY_PRIVATE_NAMES_BY_MODULE: dict[str, set[str]] = {
    "nemo_read/_leap_com.py": {
        # TODO triage: these are LEAP COM primitives. Many already
        # imported via the long form by inject_base/probe_base, so
        # they're effectively public — promoting to __all__ is the
        # right move on next visit.
        "dispatch_leap", "LeapTreeCache", "with_com_retry",
        "safe_expression", "safe_value", "iterate_variables_safe",
        "visible_false",
    },
    "nemo_read/leap_branch_inspect.py": {
        "list_branch_variables",  # TODO triage
        "cli_main",                # case (a) — CLI entry point
    },
    "nemo_read/leap_export.py": {
        # TODO triage: most are export helpers. Some (run_export,
        # ExportStats) are likely public; CLI helpers may stay private.
        "ExportStats", "export_branches", "export_fuels", "export_regions",
        "export_timeslices", "export_scenarios", "export_tags",
        "export_units", "export_nemocc_sources", "export_expressions",
        "export_branch_values", "copy_working_files",
        "find_scenario_database", "resolve_output_dir", "write_manifest",
        "run_export",
        "cli_main",  # case (a) — CLI entry point
    },
    "nemo_read/leap_units.py": {
        # TODO triage: probe_base.py imports safe_data_unit_text from
        # here — that one's clearly public. Others may follow.
        "safe_data_unit_text", "safe_data_unit_id",
        "probe_units_for_pairs", "probe_units_all_input_vars",
        "write_units_csv", "write_tree_paths_csv",
        "cli_main",  # case (a) — CLI entry point
    },
    "nemo_read/scaffold.py": {
        "cli_main",  # case (a) — CLI entry point
    },
    "nemo_read/schema.py": {
        # TODO triage: dataclass definitions. May warrant public for
        # type-hint use, or may stay as schema-internal.
        "Dimension", "Parameter", "ResultVariable",
        "parameter_has_value_col",
    },
    "nemo_read/unit_conversions.py": {
        "normalise_unit",  # TODO triage: utility function, likely public.
    },
}


def _collect_public_names(module_path: Path) -> list[tuple[str, int]]:
    """Return list of (name, lineno) for every top-level public class
    or function in the given module. 'Public' = name doesn't start
    with `_`."""
    source = module_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"Could not parse {module_path}: {e}")
    out: list[tuple[str, int]] = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                out.append((node.name, node.lineno))
    return out


def _discover_modules() -> list[Path]:
    """Every `.py` file directly under nemo_read/ (no subpackages)."""
    out = []
    for p in NEMO_READ_DIR.iterdir():
        if p.suffix != ".py":
            continue
        if p.name == "__init__.py":
            continue
        out.append(p)
    return sorted(out)


def _module_should_be_checked(module_path: Path) -> bool:
    stem = module_path.stem
    if not stem.startswith("_"):
        return True
    return stem in INTERNAL_MODULES_WITH_PUBLIC_API


@pytest.mark.parametrize(
    "module_path",
    [m for m in _discover_modules() if _module_should_be_checked(m)],
    ids=lambda p: p.name,
)
def test_module_public_api_in_all(module_path: Path):
    """Every top-level public class/function MUST be in nemo_read.__all__.

    Failure modes this catches:
      1. New class/function added to a module but forgotten in __init__.py.
      2. Class renamed in source but not updated in __init__.py.
      3. Returning class that had been removed but is still in __init__.py
         (not this test — see `test_no_dangling_names_in_all` below).
    """
    public_names = _collect_public_names(module_path)
    if not public_names:
        pytest.skip(f"{module_path.name} has no public names to check")

    exported = set(nemo_read.__all__)
    rel = str(module_path.relative_to(REPO_ROOT)).replace("\\", "/")
    intentional_private = INTENTIONALLY_PRIVATE_NAMES_BY_MODULE.get(rel, set())

    missing = [
        (name, lineno) for name, lineno in public_names
        if name not in exported and name not in intentional_private
    ]
    assert not missing, (
        f"\n{rel} defines {len(missing)} public name(s) NOT in "
        f"nemo_read.__all__:\n"
        + "\n".join(f"  - {name} (line {lineno})" for name, lineno in missing)
        + f"\n\nFix (CLAUDE.md §14 step 3):\n"
        + f"  1. In nemo_read/__init__.py, add the import:\n"
        + f"       from .{module_path.stem} import {', '.join(n for n, _ in missing)}\n"
        + f"  2. Add the names to the __all__ list at the bottom of __init__.py.\n"
        + f"\nIf any of these are intentionally private despite the public\n"
        + f"naming, either rename with a leading `_` OR add to\n"
        + f"INTENTIONALLY_PRIVATE_NAMES_BY_MODULE in this test (with a\n"
        + f"justification comment)."
    )


def test_no_dangling_names_in_all():
    """Every name in nemo_read.__all__ must actually resolve to an object.

    Catches: a name removed from a module but left behind in __all__
    (the opposite direction of test_module_public_api_in_all).
    """
    missing = [name for name in nemo_read.__all__
               if not hasattr(nemo_read, name)]
    assert not missing, (
        f"nemo_read.__all__ contains {len(missing)} name(s) that don't "
        f"resolve to actual objects: {missing}\n"
        f"Either re-add the import in __init__.py or remove the entry."
    )


def test_all_is_a_list_of_strings():
    """Sanity check on the __all__ shape itself."""
    assert isinstance(nemo_read.__all__, list)
    assert all(isinstance(n, str) for n in nemo_read.__all__)
    # Detect duplicate entries
    dupes = [n for n in nemo_read.__all__
             if nemo_read.__all__.count(n) > 1]
    assert not dupes, f"Duplicate names in __all__: {set(dupes)}"
