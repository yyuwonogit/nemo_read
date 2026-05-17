"""Pytest tripwires that move CLAUDE.md prose rules INTO CI.

Established 2026-05-17 after two separate failures in the same session
(§A.15 fossil Interp leak + §14 forgotten re-exports) revealed that
rules-as-prose are systematically violated whenever author attention
narrows. Per CLAUDE.md §A.7, destructive failure modes warrant
hardening in code, not just stricter prose.

This file is the catch-all for CLAUDE.md rules that:
  (a) have clear mechanical violation criteria
  (b) don't already have their own dedicated test module

Rules that DO have dedicated tests:
  - §A.15 Interp() separator     → tests/test_interp_separator.py
  - §5.1   CanonicalInjector seal → tests/test_inject_base.py
  - §7.1   CanonicalProber seal   → tests/test_probe_base.py
  - §14    Public API in __all__  → tests/test_public_api_completeness.py
  - §11.2  BT={3,50} unit guard   → tests/test_probe_base.py

This file adds:
  - §10.2  Version sync (pyproject.toml ↔ nemo_read.__version__)
  - §A.11  `Unlimited` on lower-bound variables in canonical CSVs

The remaining §A rules (A.1, A.2, A.3, A.5, A.6, A.9, A.13, A.14) are
judgment-based and cannot be CI-enforced. Those stay as prose, but
are surfaced in CLAUDE.md §A loaded into every session.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

import nemo_read


REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# §10.2 — Version must match in both places (pyproject.toml + __init__.py)
# ---------------------------------------------------------------------------

def test_version_sync_between_pyproject_and_init():
    """CLAUDE.md §10.2: `pyproject.toml` and `nemo_read/__init__.py`
    MUST agree on the version string.

    Drift between the two is a real release bug — `pip install` reads
    pyproject.toml's version while `import nemo_read; nemo_read.__version__`
    reads __init__.py. Users get conflicting answers when they ask
    "what version is this?"
    """
    with (REPO_ROOT / "pyproject.toml").open("rb") as f:
        toml = tomllib.load(f)
    py_version = toml["project"]["version"]
    init_version = nemo_read.__version__
    assert py_version == init_version, (
        f"Version mismatch (CLAUDE.md §10.2):\n"
        f"  pyproject.toml          → {py_version!r}\n"
        f"  nemo_read.__version__   → {init_version!r}\n"
        f"Both files must be bumped together. The Step 3 of CLAUDE.md\n"
        f"§10.3 release flow is the canonical place to do this in sync."
    )


# ---------------------------------------------------------------------------
# §A.11 — `Unlimited` string on LOWER-BOUND LEAP variables is a landmine
# ---------------------------------------------------------------------------

# Variables that LEAP→NEMO export translates as LOWER BOUNDS. Authoring
# `Unlimited` on any of these becomes the 1.0e+12 sentinel in NEMO,
# which the LP must satisfy — catastrophic infeasibility (§A.11).
LOWER_BOUND_LEAP_VARS = frozenset({
    # NEMO-side ResidualCapacity comes from LEAP Exogenous Capacity
    "Exogenous Capacity",
    # Other lower-bound-like authoring patterns:
    "Minimum Capacity",
    "Minimum Production",
    # NEMO TotalTechnologyAnnualActivityLowerLimit comes from this
    # (via MU×ResCap×C2A indirection, but `Unlimited` directly is
    # equally bad)
    "Activity Lower Limit",
})


def _scan_csv_for_unlimited_on_lower_bound(csv_path: Path) -> list[tuple[int, str, str]]:
    """Return (row_index, variable, expression) for any row in `csv_path`
    that authors `"Unlimited"` (case-insensitive) on a LOWER_BOUND_LEAP_VARS
    variable."""
    import csv as _csv
    violations: list[tuple[int, str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = _csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            var = (row.get("variable") or "").strip()
            expr = (row.get("expression") or "").strip()
            if var not in LOWER_BOUND_LEAP_VARS:
                continue
            # Match "Unlimited" as a standalone token; allow it inside
            # Interp() or as a bare value.
            if re.search(r"\bUnlimited\b", expr, flags=re.IGNORECASE):
                violations.append((i, var, expr))
    return violations


def _discover_canonical_csvs() -> list[Path]:
    """Every committed `canonical_leap_*.csv` under inject/."""
    inject = REPO_ROOT / "inject"
    if not inject.exists():
        return []
    return sorted(inject.rglob("canonical_leap_*.csv"))


@pytest.mark.parametrize(
    "csv_path",
    _discover_canonical_csvs(),
    ids=lambda p: str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
)
def test_no_unlimited_on_lower_bound_variables(csv_path: Path):
    """CLAUDE.md §A.11: authoring `Unlimited` on any LOWER_BOUND
    variable becomes the 1.0e+12 sentinel in NEMO and is a confirmed
    LP-infeasibility cause (2026-05-12, p9 incident).

    NEVER reflexively zero an existing `Unlimited` either — use a
    finite numeric (~100,000 for headroom on upper-bound vars; 0 only
    when you can prove the lower bound isn't load-bearing).
    """
    violations = _scan_csv_for_unlimited_on_lower_bound(csv_path)
    rel = str(csv_path.relative_to(REPO_ROOT)).replace("\\", "/")
    assert not violations, (
        f"\n{rel} authors 'Unlimited' on lower-bound LEAP variable(s) "
        f"(CLAUDE.md §A.11):\n"
        + "\n".join(
            f"  row {i}: variable={v!r} → {expr[:80]}..."
            for i, v, expr in violations[:5]
        )
        + (f"\n  (+{len(violations)-5} more)" if len(violations) > 5 else "")
        + "\n\nFix:\n"
        + "  - Replace 'Unlimited' with 0 ONLY if you've verified the tech\n"
        + "    has alternate capacity sources (non-zero CapCost or non-NULL\n"
        + "    MaxCap). Burned 2026-05-12 (p9): EC=0 on 4 Blending techs\n"
        + "    sent infeasibility 24k → 4.6M (190× worse).\n"
        + "  - SAFER: use a generous finite numeric (e.g. 100000) — large\n"
        + "    enough not to bind, finite enough not to pollute LP basis.\n"
    )


