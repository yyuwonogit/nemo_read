"""Fossil-domain LEAP injector — thin subclass of CanonicalInjector.

All LEAP-side rules (Interp() separator enforcement, area/scenario
lock, safe_set_expression chokepoint, placeholder gate) come from
nemo_read.inject_base. This file owns only fossil-specific concerns:

  - LEAP-native unit gate (refuse to push source-unit canonical when
    converted version exists)
  - Fuel-column filtering
  - TBD-branch skipping (default on)

Usage:
    python inject/fossil/inject_to_leap.py --dry-run
    python inject/fossil/inject_to_leap.py --scenario "Regional Aspiration Scenario"
"""
from __future__ import annotations

import argparse
from pathlib import Path

from nemo_read.inject_base import CanonicalInjector


DEFAULT_CSV = Path(__file__).parent / "canonical_leap_inputs.csv"


def _validate_leap_native(csv_path: Path) -> list[str]:
    """Refuse the source-unit canonical when canonical_leap_native.csv exists."""
    name = csv_path.name
    if name == "canonical_leap_native.csv":
        return []
    native = csv_path.parent / "canonical_leap_native.csv"
    if name == "canonical_leap_inputs.csv" and native.exists():
        return [
            f"{name} is in source units. The fixed workflow expects you "
            f"to push canonical_leap_native.csv (produced by "
            f"inject/fossil/run_workflow.py step 4). Pass "
            f"--csv {native} or, if you really mean to push source "
            f"units, --ignore-units."
        ]
    return []


class FossilInjector(CanonicalInjector):
    SECTOR_NAME = "fossil"
    DEFAULT_CSV = DEFAULT_CSV

    def extra_cli_args(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--filter-fuel", default="",
                            help="Only rows whose 'fuel' column matches")
        parser.add_argument(
            "--skip-tbd", action="store_true", default=True,
            help="Skip rows whose branch starts with 'TBD\\\\' (default ON)")
        parser.add_argument("--no-skip-tbd", dest="skip_tbd",
                            action="store_false",
                            help="Push TBD-branch rows anyway")
        parser.add_argument(
            "--ignore-units", action="store_true",
            help="Skip the LEAP-native unit refusal")
        parser.add_argument(
            "--already-converted", action="store_true",
            help="Bypass the 'use canonical_leap_native.csv' check")

    def extra_csv_validators(self) -> list:
        if self._args.ignore_units or self._args.already_converted:
            return []
        return [_validate_leap_native]

    def filter_rows(self, rows, args):
        fuel_filter = args.filter_fuel.strip()
        out = []
        for r in rows:
            if fuel_filter and r.get("fuel") != fuel_filter:
                continue
            if args.skip_tbd and r.get("branch", "").startswith("TBD\\"):
                continue
            out.append(r)
        return out


if __name__ == "__main__":
    raise SystemExit(FossilInjector().run())
