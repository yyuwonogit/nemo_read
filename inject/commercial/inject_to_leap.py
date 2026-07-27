"""Commercial-domain LEAP injector — thin CanonicalInjector subclass.

All LEAP-side rules (Interp() separator §A.15, area/scenario lock §11.1,
safe_set_expression chokepoint, placeholder gate, Timor Leste decision
§A.18, region/node locks §A.21+§A.23, blind-mode default) come from
`nemo_read.inject_base`. This file owns only commercial-specific:

  - Default canonical CSV path
  - Sector name + mandatory --expect-area

Targets are `Demand\\Commercial\\Other Commercial\\End Use Projection\\...`
and `Key\\Commercial\\...` branches. Per docs/inject_sop.md, blind mode is
MANDATORY for Demand + KA branches (cached `branch.Variable()` writes
silently no-op there). Blind is default-on in the base framework; always
pair with --fail-fast so a missing FullName fails instead of hanging.

Usage (standard):
    python inject/commercial/inject_to_leap.py \\
        --scenarios "Current Accounts,Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" \\
        --expect-area "<area name>" \\
        --exclude-timor-leste \\
        --fail-fast --skip-dry-run -y
"""
from __future__ import annotations

from pathlib import Path

from nemo_read.inject_base import CanonicalInjector


DEFAULT_CSV = Path(__file__).parent / "canonical_leap_inputs.csv"


class CommercialInjector(CanonicalInjector):
    SECTOR_NAME = "commercial"
    DEFAULT_CSV = DEFAULT_CSV
    REQUIRE_EXPECT_AREA = True

    # Timor Leste is disabled in the LEAP calc (project_timor_leste_disabled);
    # the supplement ships zero saturation / zero intensity trajectories so an
    # --include-timor-leste run cannot inherit LEAP defaults (§A.18).


if __name__ == "__main__":
    raise SystemExit(CommercialInjector().run())
