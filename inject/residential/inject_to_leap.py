"""Residential-domain LEAP injector — thin CanonicalInjector subclass.

All LEAP-side rules (Interp() separator §A.15, area/scenario lock §11.1,
safe_set_expression chokepoint, placeholder gate, Timor Leste decision
§A.18, blind-mode default §inject_sop.md) come from
`nemo_read.inject_base`. This file owns only residential-specific:

  - Default canonical CSV path
  - Sector name + expected area

Writes to Demand\\Residential\\Projections\\... — DEMAND branches.
Per inject SOP: blind mode is MANDATORY for Demand writes (cached
writes silently no-op on these branch types). Blind is default-on
in the base framework; pair with --fail-fast as always.

Usage (standard):
    python inject/residential/inject_to_leap.py \\
        --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" \\
        --expect-area "aeo9_v0.46" \\
        --exclude-timor-leste \\
        --fail-fast --skip-dry-run -y
"""
from __future__ import annotations

from pathlib import Path

from nemo_read.inject_base import CanonicalInjector


DEFAULT_CSV = Path(__file__).parent / "canonical_leap_inputs.csv"


class ResidentialInjector(CanonicalInjector):
    SECTOR_NAME = "residential"
    DEFAULT_CSV = DEFAULT_CSV
    EXPECT_AREA = "aeo9_v0.46"

    # Residential writes to Demand\Residential\... — Demand branches.
    # Cached writes silently no-op on these (transport cycle 2026-05-20
    # confirmed). Blind mode is mandatory; the base framework has it
    # default-on as of 2026-05-20.


if __name__ == "__main__":
    raise SystemExit(ResidentialInjector().run())
