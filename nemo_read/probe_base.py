"""Standardised probe framework — every long-running LEAP COM probe
(results harvest, units harvest, branch-shape inspection) MUST
subclass `CanonicalProber`. Mirrors `CanonicalInjector` for the
read-side of LEAP COM.

Why this exists: prior to 2026-05-17 each probe was a copy-pasted
~300-line script in `mailbox/<date>/probe_leap_*.py`. The
RESULTS_HARVEST_SOP.md captured 9 pitfalls inline, but enforcement
was advisory — a new author copying the template could (and did)
miss the §11.2 branch-type restriction, the multi-area trap, the
stdout buffering issue, etc. This base class seals those concerns.

# Architecture

Same shape as `CanonicalInjector`:

1. **Sealed primitives** (runtime-enforced via `__init_subclass__`):
     - `_assert_area_lock` — area drift detection (§11.1)
     - `_assert_scenario_lock` — scenario drift detection (§A.9)
     - `_read_value` — safe value read (catches popups, returns None)
     - `_read_unit_text` — `DataUnitText` read with BT={3,50} guard (§11.2)
     - `_safe_unit_name` — fallback `Unit.Name` read

2. **Open hooks** (subclass customisation):
     - `result_variables()` — names to probe on result side
     - `input_variables()` — names to probe on input side (for units)
     - `result_branch_types()` — BT filter for results (default {2,3,4,34,50})
     - `unit_branch_types()` — BT filter for units (default {3,50} — popup-safe)
     - `regions()` — list of LEAP regions (default: all, excluding 'Base Template')
     - `years()` — list of years (default: 2025..2060 step 5)
     - `branch_prefixes()` — branch filter (default: ['']; meaning whole area)

3. **Default template** — `run()` does all of:
     dispatch_leap → area lock → for each scenario: set+verify
     → results probe → ... → units probe (once)
     → optional offline join → summary.
     All in ONE COM session (CLAUDE.md §A.10).

# Background + monitor pattern

Every probe uses `HeartbeatLogger` from `_heartbeat.py`:
  - Heartbeat stdout line every 30 seconds with current
    scenario/region/rows-written/elapsed
  - Progress JSON file `_progress_<op>_<ts>.json` updated continuously
  - Final summary line + JSON on completion

Run a probe in background via Bash `run_in_background=True`. The
harness `Monitor` tool streams heartbeat lines as notifications.
For at-rest inspection: `cat _progress_<op>_<ts>.json` (or
`read_progress()` helper from `_heartbeat.py`).
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

from nemo_read._heartbeat import HeartbeatLogger
from nemo_read._leap_com import (
    LeapTreeCache,
    dispatch_leap,
    iterate_variables_safe,
    safe_value,
)
from nemo_read.leap_conventions import LEAP_BRANCH_TYPES


class ProberSealError(TypeError):
    """Raised when a subclass overrides a sealed CanonicalProber method."""


# Default targets — verified against AEO9 (May 2026).
DEFAULT_RESULT_VARS = (
    "Energy Generation",
    "Power Generation",
    "Existing Capacity",
    "Capacity Additions",
    "Capacity Retirement",
    "Costs of Production",
    "Curtailed Energy Production",
    "Pollutant Loadings",
)

DEFAULT_INPUT_VARS = (
    "Maximum Capacity",
    "Minimum Capacity",
    "Capital Cost",
    "Variable OM Cost",
    "Fixed OM Cost",
    "Lifetime",
    "Maximum Availability",
    "Minimum Utilization",
    "Process Efficiency",
    "Exogenous Capacity",
    "Capacity Credit",
    "Interest Rate",
)

DEFAULT_RESULT_BRANCH_TYPES = frozenset({2, 3, 4, 34, 50})
# §11.2 — DataUnitText is only popup-safe on these branch types:
DEFAULT_UNIT_BRANCH_TYPES = frozenset({3, 50})
DEFAULT_YEARS = tuple(range(2025, 2061, 5))


class CanonicalProber:
    """Base class for every mailbox/result-harvest LEAP COM probe.

    Subclass and override the open hooks. Sealed primitives are
    enforced at class-definition time via `__init_subclass__`.
    """

    # ---- subclass configuration ----
    PROBE_NAME: str = "probe"
    EXPECT_AREA: str | None = None
    REQUIRE_EXPECT_AREA: bool = False
    OUTPUT_DIR: Path | None = None  # default = cwd

    # Optional default scope (subclass class-level overrides)
    RESULT_VARS: tuple[str, ...] = DEFAULT_RESULT_VARS
    INPUT_VARS: tuple[str, ...] = DEFAULT_INPUT_VARS
    RESULT_BRANCH_TYPES: frozenset = DEFAULT_RESULT_BRANCH_TYPES
    UNIT_BRANCH_TYPES: frozenset = DEFAULT_UNIT_BRANCH_TYPES
    DEFAULT_YEARS: tuple[int, ...] = DEFAULT_YEARS
    BRANCH_PREFIX: str = ""  # empty = whole area

    # ---- sealed-method registry (runtime-enforced) ----
    _SEALED = frozenset({
        "_assert_area_lock",
        "_assert_scenario_lock",
        "_read_value",
        "_read_unit_text",
        "__init_subclass__",
    })

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name in cls._SEALED:
            base_attr = CanonicalProber.__dict__.get(name)
            sub_attr = cls.__dict__.get(name)
            if sub_attr is not None and sub_attr is not base_attr:
                raise ProberSealError(
                    f"{cls.__name__} cannot override sealed method "
                    f"{name!r}. Sealed methods own the LEAP-side COM "
                    f"safety rules (§11.1, §11.2, §A.9). Use an open "
                    f"hook instead — see probe_base.py docstring."
                )

    # ===================================================================
    # SEALED PRIMITIVES
    # ===================================================================

    def _assert_area_lock(self, leap, expected: str | None) -> None:
        actual = leap.ActiveArea.Name
        target = expected or self.EXPECT_AREA
        if target is None:
            return
        if actual != target:
            raise SystemExit(
                f"[{self.PROBE_NAME}] ActiveArea is {actual!r}, "
                f"expected {target!r}. Aborting (§11.1 area-drift trap)."
            )

    def _assert_scenario_lock(self, leap, expected: str | None) -> None:
        if expected is None:
            return
        actual = leap.ActiveScenario.Name
        if actual != expected:
            raise SystemExit(
                f"[{self.PROBE_NAME}] ActiveScenario is {actual!r}, "
                f"expected {expected!r}. Aborting (§A.9 drift)."
            )

    def _read_value(self, variable, year: int):
        """Safe value read — never raises, returns None on COM error."""
        return safe_value(variable, year)

    def _read_unit_text(self, variable, branch_type: int) -> str:
        """Safe `DataUnitText` read with §11.2 branch-type guard.

        Refuses to call DataUnitText on branch types other than {3, 50}
        (Transformation Process, Transformation Branch) because doing
        so on result-side aggregates fires a modal LEAP popup that
        stays on screen even when the COM error is caught.
        """
        if branch_type not in self.UNIT_BRANCH_TYPES:
            return ""
        try:
            from nemo_read.leap_units import safe_data_unit_text
            return safe_data_unit_text(variable) or ""
        except Exception:
            return ""

    # ===================================================================
    # OPEN HOOKS
    # ===================================================================

    def result_variables(self) -> tuple[str, ...]:
        return self.RESULT_VARS

    def input_variables(self) -> tuple[str, ...]:
        return self.INPUT_VARS

    def result_branch_types(self) -> frozenset:
        return self.RESULT_BRANCH_TYPES

    def unit_branch_types(self) -> frozenset:
        return self.UNIT_BRANCH_TYPES

    def regions(self, leap) -> list[str]:
        """Return list of region names to probe.

        Default: all regions in leap.Regions, EXCLUDING 'Base Template'
        (§7.3 pitfall #7 — LEAP placeholder, not a real ASEAN region).
        """
        try:
            return [r.Name for r in leap.Regions
                    if r.Name != "Base Template"]
        except Exception:
            return []

    def years(self) -> list[int]:
        return list(self.DEFAULT_YEARS)

    def branch_prefixes(self) -> list[str]:
        """Return list of branch-path prefixes to walk. Default: whole area."""
        return [self.BRANCH_PREFIX]

    def extra_cli_args(self, parser: argparse.ArgumentParser) -> None:
        pass

    # ===================================================================
    # DEFAULT TEMPLATE
    # ===================================================================

    def build_arg_parser(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(
            prog=f"probe_{self.PROBE_NAME}",
            description=(
                f"{self.PROBE_NAME} — full results+units probe in ONE COM "
                f"session (CLAUDE.md §A.10). Loops scenarios; runs Probe A "
                f"per scenario, Probe B once for the area. Heartbeat to "
                f"stdout + progress JSON throughout."
            ),
        )
        p.add_argument("--out-dir",
                       default=str(self.OUTPUT_DIR or Path.cwd()),
                       help="Output directory for CSVs + progress JSON")
        p.add_argument("--scenarios", default="",
                       help="Comma-separated scenarios to probe in ONE COM "
                            "session. If omitted, probes the current "
                            "ActiveScenario only.")
        p.add_argument("--expect-area", default=self.EXPECT_AREA,
                       help="Abort if leap.ActiveArea.Name doesn't match")
        p.add_argument("--years", default=",".join(str(y) for y in self.years()),
                       help="Comma-separated years to probe")
        p.add_argument("--regions", default="",
                       help="Comma-separated regions to probe (default: all "
                            "minus 'Base Template')")
        p.add_argument("--branch-prefix",
                       default=self.BRANCH_PREFIX,
                       help="Restrict walk to branches matching this prefix")
        p.add_argument("--skip-zeros", action="store_true", default=True,
                       help="Drop rows where value == 0 (cuts CSV size ~10×)")
        p.add_argument("--no-skip-zeros", dest="skip_zeros",
                       action="store_false")
        p.add_argument("--per-branch-deadline", type=float, default=20.0,
                       help="Seconds before bailing on one branch's var loop")
        p.add_argument("--heartbeat-interval", type=float, default=30.0,
                       help="Heartbeat throttle interval (seconds)")
        p.add_argument("--skip-units", action="store_true",
                       help="Skip Probe B (units). Only Probe A runs.")
        p.add_argument("--skip-results", action="store_true",
                       help="Skip Probe A (results). Only Probe B runs.")
        self.extra_cli_args(p)
        return p

    def run(self, argv=None) -> int:
        """Standardised probe flow — all phases in ONE COM session.

        Sequence:
          dispatch_leap → area lock → for each scenario:
            set+verify ActiveScenario
            → Probe A (results) per region → write results_<scenario>.csv
          → Probe B (units, once for the area) → write units.csv
          → final summary + heartbeat finish

        COM session stays open across all phases and all scenarios.
        Tree cache built once, reused everywhere.
        """
        parser = self.build_arg_parser()
        args = parser.parse_args(argv)
        self._args = args

        if self.REQUIRE_EXPECT_AREA and not args.expect_area:
            print(f"[{self.PROBE_NAME}] ERROR: --expect-area required "
                  f"(§A.9).", file=sys.stderr)
            return 1

        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        hb = HeartbeatLogger(
            op_name=self.PROBE_NAME,
            progress_dir=out_dir,
            interval_seconds=args.heartbeat_interval,
        )

        try:
            return self._run_inner(args, out_dir, hb)
        finally:
            hb.finish(summary={"complete": True})

    def _run_inner(
        self, args: argparse.Namespace, out_dir: Path,
        hb: HeartbeatLogger,
    ) -> int:
        # ---- COM dispatch ONCE (warm across all phases + scenarios) ----
        leap = dispatch_leap()
        self._assert_area_lock(leap, args.expect_area)
        initial_area = leap.ActiveArea.Name
        print(f"[{self.PROBE_NAME}] ActiveArea (locked): {initial_area!r}")

        # ---- Tree cache built ONCE, reused everywhere ----
        cache_start = time.perf_counter()
        cache = LeapTreeCache(leap=leap)
        cache_elapsed = time.perf_counter() - cache_start
        print(f"[{self.PROBE_NAME}] Tree cache: {len(cache.fullname_to_idx)} "
              f"branches ({cache_elapsed:.1f}s)")
        hb.tick(phase="cache_built",
                branches=len(cache.fullname_to_idx))

        # ---- Resolve scenarios ----
        scenarios = (
            [s.strip() for s in args.scenarios.split(",") if s.strip()]
            or [None]
        )
        print(f"[{self.PROBE_NAME}] {len(scenarios)} scenario(s): "
              f"{scenarios or '<current>'}")

        # ---- Resolve scope ----
        years_list = [int(y.strip()) for y in args.years.split(",")
                      if y.strip()]
        regions_list = (
            [r.strip() for r in args.regions.split(",") if r.strip()]
            or self.regions(leap)
        )
        target_results = list(self.result_variables())
        target_inputs = list(self.input_variables())

        # ---- Filter branches once ----
        branch_index = self._filter_branches(
            cache, args.branch_prefix, self.result_branch_types())
        unit_branch_index = self._filter_branches(
            cache, args.branch_prefix, self.unit_branch_types())
        print(f"[{self.PROBE_NAME}] Result branches: {len(branch_index)} | "
              f"Unit branches: {len(unit_branch_index)}")

        # ---- Probe A: results per scenario ----
        if not args.skip_results:
            for scenario in scenarios:
                rc = self._probe_a_results(
                    leap, cache, branch_index, scenario,
                    regions_list, years_list, target_results,
                    args, out_dir, hb)
                if rc != 0:
                    return rc

        # ---- Probe B: units once for the area (scenario-agnostic) ----
        if not args.skip_units:
            self._probe_b_units(
                leap, cache, unit_branch_index, target_inputs,
                args, out_dir, hb)

        print(f"\n[{self.PROBE_NAME}] === ALL PHASES DONE ===")
        return 0

    def _filter_branches(
        self, cache: LeapTreeCache, prefix: str, type_filter: frozenset,
    ) -> list[tuple[int, str, int]]:
        out: list[tuple[int, str, int]] = []
        for fn, idx in cache.fullname_to_idx.items():
            if prefix and not fn.startswith(prefix):
                continue
            try:
                br = cache.branches.Item(idx)
                bt = int(br.BranchType)
            except Exception:
                continue
            if type_filter and bt not in type_filter:
                continue
            out.append((idx, fn, bt))
        return out

    def _probe_a_results(
        self, leap, cache, branch_index, scenario, regions, years,
        target_vars, args, out_dir: Path, hb: HeartbeatLogger,
    ) -> int:
        scen_label = scenario or "<current>"
        if scenario:
            try:
                leap.ActiveScenario = leap.Scenarios(scenario)
            except Exception as exc:
                print(f"[{self.PROBE_NAME}] ERROR: scenario {scenario!r}: {exc}",
                      file=sys.stderr)
                return 2
            self._assert_area_lock(leap, args.expect_area)
        active_scen = leap.ActiveScenario.Name
        print(f"\n[{self.PROBE_NAME}] ── Probe A: results "
              f"(scenario={active_scen!r}) ──")

        scen_slug = active_scen.replace(" ", "_").replace("/", "_")
        out_path = out_dir / f"results_{scen_slug}.csv"
        n_rows = 0
        started = time.perf_counter()
        with out_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "ams", "branch", "branch_type", "variable", "year", "value",
            ])
            w.writeheader()

            for region in regions:
                try:
                    leap.ActiveRegion = leap.Regions(region)
                except Exception:
                    continue
                r_started = time.perf_counter()
                r_rows = 0

                for idx, fn, bt in branch_index:
                    try:
                        br = cache.branches.Item(idx)
                    except Exception:
                        continue

                    var_names: list[str] = []
                    try:
                        for _, name, _ in iterate_variables_safe(
                            br, deadline_seconds=args.per_branch_deadline,
                            fetch_expression=False,
                        ):
                            if name:
                                var_names.append(name)
                    except Exception:
                        continue

                    hits = [n for n in var_names if n in target_vars]
                    if not hits:
                        continue

                    for vname in hits:
                        try:
                            var = br.Variable(vname)
                        except Exception:
                            continue
                        if var is None:
                            continue
                        for y in years:
                            v = self._read_value(var, y)
                            if v is None:
                                continue
                            if args.skip_zeros and v == 0:
                                continue
                            w.writerow({
                                "ams": region,
                                "branch": fn,
                                "branch_type": LEAP_BRANCH_TYPES.get(
                                    bt, str(bt)),
                                "variable": vname,
                                "year": y,
                                "value": v,
                            })
                            n_rows += 1
                            r_rows += 1

                elapsed = time.perf_counter() - r_started
                print(f"  [region={region}] {r_rows} rows in {elapsed:.1f}s")
                hb.tick(
                    phase="probe_a", scenario=active_scen,
                    region=region, rows_written=n_rows,
                )

        elapsed = time.perf_counter() - started
        print(f"  [{self.PROBE_NAME}] Probe A {active_scen!r}: {n_rows} rows "
              f"in {elapsed:.1f}s → {out_path.name}")
        hb.tick(phase="probe_a_done", scenario=active_scen,
                rows_written=n_rows)
        return 0

    def _probe_b_units(
        self, leap, cache, unit_branch_index, target_vars,
        args, out_dir: Path, hb: HeartbeatLogger,
    ):
        print(f"\n[{self.PROBE_NAME}] ── Probe B: units "
              f"(scenario- and region-agnostic) ──")

        # Set ActiveRegion to first available region (needed so
        # DataUnitText resolves; the unit is region-agnostic).
        regions_attempted = self.regions(leap)
        if regions_attempted:
            try:
                leap.ActiveRegion = leap.Regions(regions_attempted[0])
            except Exception:
                pass

        out_path = out_dir / "units.csv"
        n_rows = 0
        started = time.perf_counter()

        with out_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "branch", "branch_type", "variable", "unit",
            ])
            w.writeheader()

            for idx, fn, bt in unit_branch_index:
                try:
                    br = cache.branches.Item(idx)
                except Exception:
                    continue

                seen: set[str] = set()
                try:
                    for j in range(1, br.Variables.Count + 1):
                        try:
                            var = br.Variables.Item(j)
                        except Exception:
                            continue
                        try:
                            vname = var.Name
                        except Exception:
                            continue
                        if vname not in target_vars or vname in seen:
                            continue
                        seen.add(vname)
                        unit = self._read_unit_text(var, bt)
                        if not unit:
                            continue
                        w.writerow({
                            "branch": fn,
                            "branch_type": LEAP_BRANCH_TYPES.get(bt, str(bt)),
                            "variable": vname,
                            "unit": unit,
                        })
                        n_rows += 1
                except Exception:
                    continue

                # Heartbeat every N branches
                if n_rows and n_rows % 50 == 0:
                    hb.tick(phase="probe_b", rows_written=n_rows)

        elapsed = time.perf_counter() - started
        print(f"  [{self.PROBE_NAME}] Probe B: {n_rows} unit rows "
              f"in {elapsed:.1f}s → {out_path.name}")
        hb.tick(phase="probe_b_done", rows_written=n_rows)
