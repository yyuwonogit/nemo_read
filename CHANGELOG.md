# Changelog

## [0.6.2] — Comprehensive single-shot LEAP probe + readability rule

### Added
- **Comprehensive export by default.** `nemo_read-leap-export` now captures
  input-variable expressions and demand-leaf numeric values in addition to
  the structural CSVs already produced in 0.6.0/0.6.1. Two new files in
  every export directory:
  - `branch_variable_expressions.csv` — `(branch_id, variable_name, scenario_name, expression)`
    for every input variable on every branch (active scenario).
  - `branch_variable_values.csv` — `(branch_id, variable_name, scenario_id, scenario_name, region_id, year, value)`
    for demand-tree leaves' `Final Energy Demand` and `Activity Level`
    by default. Sufficient to reconstruct demand-by-sector entirely
    offline.
- New CLI flags on `nemo_read-leap-export`:
  - `--no-expressions` to opt out of the expression dump
  - `--values-scope=demand-leaves|all-input-vars|none` to control value capture
- **`read_demand(db, *, by="fuel"|"sector", context=None, decode=True)`** —
  high-level demand reader. `by="fuel"` works against the SQLite alone;
  `by="sector"` joins LEAP-tree demand-leaf values to produce sector ×
  subsector × region × year breakdowns offline.
- **`decode_dims(df, db)`** — package-wide readability helper. Attaches
  `region_name` / `fuel_name` / `tech_name` / `emission_name` / etc.
  columns to any DataFrame carrying NEMO dim codes. New rule: any reader
  producing analysis output decodes by default; pass `decode=False` for raw
  codes when you're doing your own joins.
- `LeapAreaContext.variable_value(branch_id, variable_name, year=None,
  region_id=None, scenario_name=None)` — typed lookup against
  `branch_values`; returns scalar / Series / None.
- `safe_value(variable, year, region_id)` in `_leap_com.py` — defensive
  wrapper around `Variable.Value()` mirroring `safe_expression`.
- `iterate_variables_safe(branch, deadline_seconds=...)` per-branch
  wallclock cap to escape stuck COM calls without hanging the whole walk.
- 13 new unit tests in `tests/test_demand_and_decode.py` covering the
  readability layer, demand reader (both `by="fuel"` and `by="sector"`
  paths), and `LeapAreaContext.variable_value`.

### Fixed
- **`CostBreakdown.print()`** now reports the reconstructed sum even when
  `vtotaldiscountedcost` is zero/missing in the SQLite (e.g. when the
  variable wasn't in `varstosave`), with a clear hint about the cause.
- **Per-branch wallclock deadline** (15 s) on the nemocc/expressions/values
  walks. Prior behaviour: a single slow branch would hang the whole walk
  for hours. Now: stuck branches log a skip and the walk continues.

### Notes
- First export with the new defaults is slower (~30–60 min for an
  AEO9-sized area, dominated by demand-leaf value capture). Subsequent
  exports reuse the cached id-map JSON and re-run incrementally.
- For exhaustive captures across all branches' input variables, opt in
  with `--values-scope=all-input-vars` (~1 hour territory).

### Patches landed in this release after first build
- **Region scoping fix** for `Variable.Value()`. LEAP's COM treats the
  second positional arg of `Value(year, ...)` as a **unit** (string),
  not a region. Passing region IDs there fires "Unrecognized unit"
  modal dialogs in LEAP. The export now sets `leap.ActiveRegion = name`
  in an outer loop (12 sets total per area) before calling
  `var.Value(year)`. ~10,000× fewer global setter writes than the
  per-call alternative.
- **Names-only first pass on Variable scans.** The nemocc and expressions
  walks no longer touch `.Expression` on every variable up front (which
  fires modal dialogs on result variables). They iterate names first
  with `iterate_variables_safe(..., fetch_expression=False)`, then
  re-fetch only the matching variables.
- **`--scenario NAME` CLI flag.** Switch LEAP's ActiveScenario before
  the values walk so demand/value rows are captured for the right
  scenario without manual COM calls. Validates the scenario exists.
- **`docs/cookbook.md`** new section "Demand by sector" covering the
  end-to-end recipe (LEAP-area export + offline `read_demand`).
- **End-to-end validation** completed against AEO9 RAS: 82,080 value
  rows captured across 647 demand leaves × 9 years × 12 regions, then
  decoded into a 3996-row sector × subsector × region × year frame.

## [0.6.1] — Result-side traceback (NemoMod.jl slice A+B+C)

### Added
- `RESULT_DEPENDENCIES` in `nemo_read/schema.py` — for every NEMO result
  variable (59 entries), a `ResultDependency` dataclass listing the input
  parameters, upstream result variables, and upper/lower bounds that appear
  in its defining JuMP constraint or objective term. Sourced from NemoMod.jl
  for NEMO data-dictionary v11.
- `nemo_read/trace.py` with two user-facing helpers:
  - `trace_result(db, table, row, context=None)` — return a `ResultTrace`
    with contributing inputs (each carrying a LEAP UI hint when `context`
    is supplied), upstream results, and a `BoundCheck` flagging whether the
    row's value is hitting an upper bound, lower bound, or freely
    optimised.
  - `trace_cost(db, region, year)` — decompose `vtotaldiscountedcost` for
    one `(r, y)` into its cost streams (capital investment, operating cost,
    emissions penalty, salvage, financing — split across tech/storage/
    transmission). Returns a `CostBreakdown` with a `to_dataframe()` view
    that orders streams by absolute contribution.
- Constants `BOUND_HIT_UPPER`, `BOUND_HIT_LOWER`, `BOUND_FREE`,
  `BOUND_ABSENT`, `BOUND_UNKNOWN` for checking `trace.bound.state`.
- `tests/test_trace.py` — 10 tests against a synthetic NEMO-shaped SQLite:
  binding-bound detection, context-enriched input hints, cost-stream
  reconstruction matching total, sign conventions.

### Notes
- The ancestry data is static (encoded once from the Julia source). It does
  not compute shadow prices or run sensitivity analysis — those would need
  a solver re-run.
- `trace_cost` reports reconstructed sums so you can spot when cost streams
  don't fully sum to `vtotaldiscountedcost` (e.g. a result table missing
  from the SQLite because of a `varstosave` gap).

## [0.6.0] — LEAP-area pairing for complete SQLite decoding

### Added
- `nemo_read-leap-export` CLI (Windows-only, optional `[leap]` extra requiring pywin32).
  Run once per area with LEAP open to dump branches, fuels, regions, timeslices,
  scenarios, tags, units, nemo.cfg, customconstraints.txt, and `*__NEMOcc` sources
  into a directory adjacent to the scenario sqlite.
- `LeapAreaContext` (pure-Python, all platforms) loads that directory and exposes
  decoded LEAP metadata alongside the NEMO SQLite. `LeapAreaContext.discover(db)`
  auto-finds the adjacent `*.leap_export/` directory.
- `read_nemo_cfg()` — TOML parser for LEAP's nemo.cfg.
- `read_custom_constraints()` — static analysis of customconstraints.txt, extracts
  function names, `*__NEMOcc` table references, and pollutant → eid map.
- `LEAP_BRANCH_TYPES` — integer-code → name map (36 codes) enumerated against AEO9.
- `LEAP_SOURCE_MAP` + `LeapSource` + `where_in_leap(table, row, context)` — for any
  parameter-table row, return the LEAP branch + Variable + UI navigation hint that
  populates it. Covers 59 of 64 NEMO parameters.
- `resolve_leap_ids(df, context, ...)` — join any DataFrame with branch IDs /
  technology IDs / fuel LEAP IDs to full LEAP branch/fuel names.
- Internal `nemo_read/_leap_com.py` with `LeapTreeCache` (id/fullname-map safe
  lookup to avoid the `leap.Branches("nonexistent")` hang) and
  `safe_expression()` (try/except around the result-variable modal popup).
  Map persisted to JSON on first build; subsequent runs load instantly.
- `print_overview(db, context=ctx)`, `inspect_scenario(db, context=ctx)`,
  `validate_scenario(db, context=ctx)`, and `check_scenario(db, context=ctx)`
  all accept an optional `LeapAreaContext`. When supplied, the overview
  prepends a LEAP-area section and the validator adds a `varstosave`
  coverage check that warns when variables listed in `nemo.cfg` are missing
  from the populated v* tables.
- `tests/test_leap_area.py` with 20 unit tests covering nemo.cfg parsing,
  customconstraints extraction, `LeapAreaContext` load/discover, and the
  full `where_in_leap()` matrix across tech / process-node / module /
  result-variable cases. Full suite: 43 passing.

### Fixed
- (none — purely additive release)

## [0.5.0] — first PyPI release

### Added
- Top-level README, LICENSE (Apache-2.0), and `docs/leap_area_wishlist.md` documenting the open decoding backlog that requires LEAP Areas folder access.
- `infeasibility.py` module with `find_infeasibilities()` and `check_scenario()`.
- Static checks for: bound inversions, exogenous emissions exceeding limits, `MinShareProduction` sum > 1.0, `MinimumUtilization` > `AvailabilityFactor`, `MinStorageCharge` > `StorageLevelStart`, reserve margin without tagged technology, demand for fuels without a producer, storage without charge/discharge path, CCS unbounded-profit risk.
- `ValidationReport.extend()` for merging reports.
- `inspect_scenario()` now returns both `validation` and `infeasibilities` keys; `print_overview()` shows each as a separate section.
- Test suite `test_infeasibility.py` with eleven assertions.

### Fixed
- `dump_to_csv()` and `dump_to_parquet()` now accept either preset strings or iterables of specific table names. Previously silently wrote zero files when passed a list.
- Year filter in `get_parameter()` now works whether the user passes integers or strings; previously `{"y": ["2025"]}` returned zero rows because of a dtype mismatch.

## [0.4.0]

### Added
- `validate.py` module with `validate_scenario()` returning a `ValidationReport`.
- Checks: schema version, referential integrity on every populated parameter, `YearSplit` sums, `SpecifiedDemandProfile` sums, `NODE.r → REGION`, `TransmissionLine` endpoints, demand without profile, `MinStorageCharge` infeasibility, CCS unbounded-profit, negative emission rate info.
- `leap_conventions.py` module exposing `LEAP_NEMO_UNITS`, `units_for()`, `extract_leap_ids()`, `fuels_with_leap_ids()`, `classify_technology_id()`, `technology_kinds()`.
- `tsgroup_hours()` using the full NEMO identity (slices × `TSGROUP2.multiplier` × `TSGROUP1.multiplier` = 8760) instead of an ad-hoc representative-week formula.
- `transmission_candidates()` using `yconstruction > min(YEAR)` for correct candidate detection.
- `list_unused_technologies()` for dormant-technology discovery.
- `references/conventions_and_validation.md`.

### Fixed
- `timeslices()` now sorts by `(tg1_order, tg2_order, lorder)` instead of `lorder` alone. Previous ordering interleaved seasons and produced wrong chronological ordering for dispatch plots.

## [0.3.0]

### Added
- `custom.py` module with `list_custom_constraints()`, `get_custom_constraint()`, `detect_slack_technologies()`, `slack_technology_ids()`.
- Calculation state banner (`pre-calculation` / `post-calculation`) in `print_overview()`.
- Classified `__NEMOcc` tables as first-class (no longer flagged as unknown).

### Fixed
- `get_parameter("TransmissionModelingEnabled")` no longer fails. Previously the overlay logic hardcoded `val` as the value column, breaking for the one parameter that uses `type` instead.
- `parameter_to_dataarray()` now preserves the full dimension grid when a parameter has NaN default (e.g. `ReserveMargin`). Previously silently shrank the cube to only dimensions with stored data.
- `list_present_results()` no longer crashes on a pre-calculation database with no `v*` tables.

## [0.2.0]

### Added
- Project-package scaffolder (`nemo_read-scaffold` CLI).
- Parquet export.

## [0.1.0]

### Added
- Initial library: `NemoDB`, dimension readers, parameter reader with default overlay, result variable reader with `solvedtm` filter, xarray export, CSV export, `inspect_scenario()`.
