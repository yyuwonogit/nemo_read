# Changelog

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
