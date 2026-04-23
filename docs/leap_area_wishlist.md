# LEAP area wishlist

**Status**: Open. Continue in VS Code / GitHub.

This file lists everything the skill cannot decode from the SQLite scenario database alone and needs from the LEAP Areas folder to complete. Items are grouped by priority and cross-referenced to the library code that will consume each output.

## Background

The NEMO SQLite file gives us numbers. LEAP branch structure, Julia custom-constraint scripts, and NEMO runtime configuration live outside the SQLite in the LEAP Areas folder. Without those, the library can compute quantities (capacity by year, emissions, cost) but cannot write narrative (country names, sectoral context, constraint meaning).

Three gaps remain in the decoded picture:

1. `__NEMOcc.bid` values are opaque numeric references to LEAP branches.
2. 257 of 291 technology descriptions are bare — no sector or parent context.
3. NEMO runtime configuration (`nemo.cfg`, `customconstraints.txt`) is not in the SQLite.

Everything else the library already decodes: time-slicing math, LEAP-NEMO units, technology kind prefixes (D/P/S), fuel LEAP IDs, slack detection, storage cycle semantics, sequestration emissions, candidate vs existing transmission, nodal distribution, validation against NEMO infeasibility patterns.

## Wishlist

| # | Item | Priority | What it unblocks | Suggested format |
|---|---|---|---|---|
| 1 | **Branch tree export** — every LEAP branch with `ID`, `Name`, `FullName`, `ParentID`, `BranchType` (Demand / Transformation / Resource / etc.) | Blocker | Resolves all `__NEMOcc.bid` references. Joins SQLite rows back to the LEAP hierarchy. Foundation for items 2, 5, 6, 8 | CSV, one row per branch; include all branches, not just technologies |
| 2 | **Technology ID → branch FullName mapping** | Blocker | Turns 257 bare descriptions like `"Solar PV Rooftop"` into `"Transformation\Centralized Electricity Generation\Solar PV Rooftop"`. Needed for every publication table and narrative sentence | CSV: `tech_id` (e.g. `P16756`) → `branch_id`, `full_name`. If the numeric suffix of P/D-prefixed IDs equals the LEAP branch ID, confirm that as a rule and item 2 collapses into item 1 |
| 3 | **`nemo.cfg` / `nemo.toml`** | Blocker | Tells the skill what `varstosave`, `calcyears`, `continuoustransmission`, `forcemip`, solver parameters are in effect. Controls what appears in the `v*` result tables after calculation | The actual file from the LEAP Areas folder. If absent, confirm so defaults apply |
| 4 | **`customconstraints.txt`** | Blocker | Interprets what the four `__NEMOcc` tables actually compute. `bid=1201` means what in the Julia code? Is `eid=-1` a sentinel or a real reference? What units does `val` carry for each constraint? | The Julia source file from the LEAP Areas folder |
| 5 | **Fuel branch metadata** | High | Trace fuel chains from production through transformation to demand; write narrative about energy flows. The library already extracts all 77 fuel LEAP IDs from descriptions | CSV: `leap_id` → `branch_name`, `full_name`, `branch_type` (supply / transformation-output / demand) |
| 6 | **Demand driver expressions** for the 34 "Optimized" demand technologies | High | Understand the 5 transport categories × drivetrains. `D16677: Optimized_Trucks_and_Other:Hydrogen ICE` — what's the underlying activity driver (vehicle-km, tonne-km, passenger-km)? | Either the activity expressions exported from LEAP, or branch-level metadata identifying the driver variable per category |
| 7 | **ASEAN region-group definition** | Medium | Clarify how `ASEANRenewableCapacityTarget__NEMOcc` aggregates across countries when `REGIONGROUP` and `RRGroup` tables are empty in the SQLite | Likely visible inside `customconstraints.txt` (item 4); if hardcoded there, document it |
| 8 | **Residual capacity provenance** | Medium | Document residual capacity assumptions in papers; tie numbers to historical build-outs and source citations | Branch-level export: vintages, source references, text annotations on residual capacity expressions |
| 9 | **4 Indonesian liquid-fuel slacks** (P19874, P19878, P19882, P19886, each ResidualCapacity 10¹² in R1 only) | Medium | Confirm intent: unlimited-supply pseudo-processes for Indonesian oil products, or data-entry artefacts? | A look at the parent branch of these four technologies in the LEAP tree, plus the modeller's notes |
| 10 | **Biofuel feedstock demand semantics** | Medium | Validator flagged 184 `(r, f, y)` combos with `SpecifiedAnnualDemand > 0` but no `SpecifiedDemandProfile` — all F29 (palm oil), F31 (coconut oil), F34 (cassava), F36 (sugarcane). Should these use `AccumulatedAnnualDemand` semantics instead? | Confirmation of intent from whoever built the area |
| 11 | **CCS unbounded-profit risk review** | Review | Infeasibility tool flagged 44 `(r, t, e)` combos where negative `EmissionActivityRatio` (sequestration) × negative `EmissionsPenalty` (subsidy) have no activity/capacity upper bound. NEMO can become unbounded | Confirm that missing bounds are intentional or add `TotalAnnualMaxCapacity` / `TotalTechnologyAnnualActivityUpperLimit` to the relevant CCS techs |
| 12 | **MinimumUtilization > AvailabilityFactor solar bug** | **Review (critical, blocks solve)** | Infeasibility tool found 48 `(r, t, l, y)` combos where 3 solar technologies in R15 have tiny non-zero `MinimumUtilization` (~7×10⁻⁵) at nighttime timeslices (L7, L31) where `AvailabilityFactor = 0`. Guaranteed solver failure | Fix in LEAP: set `MinimumUtilization = 0` at these timeslices for P16756, P2847, P4240 in R15, or raise `AvailabilityFactor` to match |
| 13 | **51 dormant technologies** | Review | Mostly demand-side (`Optimized Private Passenger Vehicles:*`). Per NEMO docs, technologies without any parameter reference are never simulated | Confirm they are intentionally dormant, or that they're missing CapitalCost / OAR / IAR values that should be populated |
| 14 | **Depreciation method per region** | Review | Default is 1 (sinking fund); 2 would mean straight-line. Impacts salvage values | Confirm the scenario uses sinking fund consistently |
| 15 | **`__NEMOcc.eid = -1` sentinel meaning** | Clarification | All 4 custom-constraint tables use `eid = -1` throughout. "Not applicable" sentinel, or real reference? | Answerable from item 4 |
| 16 | **`bid = 1201` identity** | Clarification | Single bid value across 396 rows in each of the ASEAN and Renewable target tables. Likely the renewable technology group branch in LEAP | Answerable from item 1 |
| 17 | **yconstruction = 2020 vs 2040 split** | Clarification | 18 lines with 2020 (pre-horizon existing), 2 with 2040 (candidates). Historical-build convention, or have other years been rounded? | Check the LEAP transmission branch expressions |
| 18 | **Sub-regional node mapping** | Nice-to-have | N1-N19 exist; 16 of 18 get nodal distribution entries. N2 and N10 are unassigned — likely the Indonesia and Malaysia "parent" nodes that get split into sub-national. Confirm and add geographic labels | CSV: node ID → sub-region name (IDJW, IDKA, IDSA, IDEast, MYSB, MYPE, MYSR, etc.) with latitude/longitude if available |
| 19 | **Region country-code mapping** | Nice-to-have | R1-R20 have descriptive names like `"Indonesia"`, `"Malaysia"` but confirmation of ISO 3166 alignment for cross-referencing external datasets (IEA, IRENA, WB) | Quick CSV: `r` → ISO-3 code |
| 20 | **Previously solved `_startvals` databases** | Nice-to-have | If the scenario was warm-started via `startvalsdbpath`, knowing the source is useful for result reproducibility | Path or filename if applicable |

## Shipping tranches

- **Tranche 1 (3 files)** — items 1, 3, 4. Unblocks every narrative query and the custom-constraint interpretation.
- **Tranche 2 (1-2 files)** — items 2, 5, 6. Makes output publication-ready with full hierarchy labels.
- **Tranche 3 (review with LEAP modeller, no export needed)** — items 11, 12, 13. Item 12 currently blocks a successful solve of the scenario.
- **Tranche 4 (implicit from 1 and 4)** — items 7, 15, 16.
- **Optional** — items 8, 9, 10, 14, 17, 18, 19, 20.

## Follow-up work once Tranche 1 lands

Planned additions to the library:

- **`leap_area.py`** — reads the three files (`nemo.cfg`, branch tree CSV, `customconstraints.txt`). Returns a typed `LeapAreaContext` object.
- **`resolve_leap_ids(df, context)`** — joins any DataFrame with a `bid`, `t`, `f`, or `leap_id` column to LEAP branch full-names from the context. Works on parameter rows, `__NEMOcc` rows, and result rows alike.
- **Custom constraint interpreter** — parses the Julia source for each `__NEMOcc` table and reports each constraint's formulation in plain language (domain, units, direction, binding condition).
- **Overview enrichment** — `print_overview(db, context=leap_ctx)` adds branch full-names and constraint descriptions to every section.
- **Config-aware result expectations** — compare `varstosave` from `nemo.cfg` against the result tables present in the DB after calculation; flag a mismatch (e.g. if LEAP was supposed to save `vtransmissionbyline` but the table is empty).

## Notes for the VS Code / GitHub continuation

- The library's public API is stable. New helpers from the LEAP-area module should compose with existing functions, not replace them.
- `ValidationReport` is the shared result type; any new check should emit `ValidationIssue` entries with severity `error` / `warning` / `info` so `check_scenario()` can merge findings.
- Testing: synthetic DB in `tests/test_nemo_read.py` and extension DB in `tests/test_extensions.py` should be extended with sample LEAP-area fixtures (a minimal branch CSV and a short `nemo.cfg`) so the new module has first-class test coverage.
- The scaffolder's vendor list in `scripts/nemo_read/scaffold.py` must include `leap_area.py` once it exists, otherwise scaffolded projects won't get the helper.
