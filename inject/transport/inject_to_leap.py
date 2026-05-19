"""Transport-domain LEAP injector — thin CanonicalInjector subclass.

All LEAP-side rules (Interp() separator §A.15, area/scenario lock §11.1,
safe_set_expression chokepoint, placeholder gate, Timor Leste decision
§A.18) come from `nemo_read.inject_base`. This file owns only
transport-specific:

  - Default canonical CSV path
  - Sector name + expected area

Usage:
    python inject/transport/inject_to_leap.py --dry-run-only \\
        --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario,Current Accounts" \\
        --expect-area "aeo9_v0.46" \\
        --exclude-timor-leste
"""
from __future__ import annotations

from pathlib import Path

from nemo_read.inject_base import CanonicalInjector


DEFAULT_CSV = Path(__file__).parent / "canonical_leap_inputs.csv"


class TransportInjector(CanonicalInjector):
    SECTOR_NAME = "transport"
    DEFAULT_CSV = DEFAULT_CSV
    EXPECT_AREA = "aeo9_v0.46"

    # Per project_timor_leste_disabled.md — TL excluded from LEAP calc
    # until further notice; the supplement CSV is a stub for now.
    # (Framework still enforces --include-timor-leste / --exclude-timor-leste
    # decision per §A.18.)


if __name__ == "__main__":
    raise SystemExit(TransportInjector().run())
