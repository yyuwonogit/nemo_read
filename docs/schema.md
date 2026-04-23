# NEMO v11 scenario database schema reference

Authoritative source: `NemoMod.jl/src/db_structure.jl` (master) and the official Variables documentation at https://sei-international.github.io/NemoMod.jl/stable/variables/.

This reference catalogues every table in a NEMO v11 scenario database, covers the column order NEMO actually creates, and notes version transitions relevant to LEAP installations in the field.

## Contents

- [Database-level tables](#database-level-tables)
- [Dimensions (sets)](#dimensions-sets)
- [Parameters (input tables)](#parameters-input-tables)
- [Result variables (output tables)](#result-variables-output-tables)
- [Custom constraints (`__NEMOcc` tables)](#custom-constraints-__nemocc-tables)
- [Slack technologies](#slack-technologies)
- [Data quirks and LEAP conventions](#data-quirks-and-leap-conventions)
- [Version history](#version-history)
- [Column abbreviation legend](#column-abbreviation-legend)

---

## Database-level tables

| Table | Purpose |
|---|---|
| `Version` | Single integer row indicating the NEMO data-dictionary version. v11 as of NEMO 2.1+. |
| `DefaultParams` | `(id, tablename, val)`. Registers a default numeric value for a parameter table. NEMO uses these defaults when materialising `<tablename>_def` views. |
| `nodalstorage`, `yearintervals` | Temporary working tables NEMO creates during a calculation and drops afterwards. Safe to ignore. |

`_def` views: for each parameter table that has a registered default, NEMO creates a view of the form `<ParameterName>_def` that left-joins the sparse parameter table against the Cartesian product of its dimension members and fills missing values with the default. The library uses these views when available and reconstructs them in Python otherwise.

---

## Dimensions (sets)

All dimension tables use `val` as the primary key unless noted. `desc` is an optional free-text description.

### Core sets

| Table | Columns | Notes |
|---|---|---|
| `REGION` | `val`, `desc` | Geographic region. |
| `REGIONGROUP` | `val`, `desc` | Group of regions for aggregate constraints (v9+). Populated via `RRGroup`. |
| `TECHNOLOGY` | `val`, `desc` | Technology entity. |
| `FUEL` | `val`, `desc` | Fuel or energy carrier. |
| `EMISSION` | `val`, `desc` | Emission species (CO2, CH4, etc.). |
| `MODE_OF_OPERATION` | `val`, `desc` | Operating mode identifier; stored as TEXT but often numeric-valued. |
| `STORAGE` | `val`, `desc`, `netzeroyear`, `netzerotg1`, `netzerotg2` | `netzero*` flags enforce charge/discharge balance at the given horizon (v2+). |
| `YEAR` | `val`, `desc` | Model year. Stored as TEXT despite being integer-valued; cast on read. |
| `TIMESLICE` | `val`, `desc` | Sub-annual slice label. |
| `TSGROUP1` | `name`, `desc`, `order`, `multiplier` | Upper time-slice group (e.g. season). `order` is unique and sets group sequence. `multiplier` scales effective weight. |
| `TSGROUP2` | `name`, `desc`, `order`, `multiplier` | Lower group (e.g. day type). |
| `NODE` | `val`, `desc`, `r` | Transmission node assigned to region `r`. |

### Mapping tables

| Table | Columns | Purpose |
|---|---|---|
| `LTsGroup` | `id`, `l`, `lorder`, `tg2`, `tg1` | Maps each `TIMESLICE.val` into its TSGROUP1 and TSGROUP2. `lorder` gives intra-year sequence. |
| `RRGroup` | `id`, `rg`, `r` | Many-to-many mapping of regions to region groups. |

### Hybrid dimension/parameter

| Table | Columns |
|---|---|
| `TransmissionLine` | `id`, `n1`, `n2`, `f`, `maxflow`, `reactance`, `yconstruction`, `capitalcost`, `fixedcost`, `variablecost`, `operationallife`, `efficiency`, `interestrate` |

`TransmissionLine` is indexed by `id` (TEXT, not integer) and other parameter tables reference it via `tr`. The cost and lifetime fields are exogenous per-line parameters; NEMO does not create a `_def` view for this table.

---

## Parameters (input tables)

Every parameter table has an `id INTEGER` surrogate key plus the dimension columns listed below and a `val REAL` column. Default values, where registered in `DefaultParams`, are surfaced through `<name>_def` views.

### Demand

| Parameter | Dimensions | Default typical | Unit | Description |
|---|---|---|---|---|
| `AccumulatedAnnualDemand` | `r, f, y` | 0 | energy | Demand satisfiable at any time in the year (no within-year profile). |
| `SpecifiedAnnualDemand` | `r, f, y` | 0 | energy | Annual demand that must follow `SpecifiedDemandProfile` within the year. |
| `SpecifiedDemandProfile` | `r, f, l, y` | 0 | fraction | Fraction of `SpecifiedAnnualDemand` in time slice `l`. Sums to 1 per `(r, f, y)`. |

### Time-slicing

| Parameter | Dimensions | Unit | Description |
|---|---|---|---|
| `YearSplit` | `l, y` | fraction | Fraction of the year occupied by time slice `l`. |

### Capacity and availability

| Parameter | Dimensions | Unit | Description |
|---|---|---|---|
| `AvailabilityFactor` | `r, t, l, y` | fraction | Capacity available in time slice. Renamed from `CapacityFactor` in v10. |
| `CapacityToActivityUnit` | `r, t` | energy/(capacity·year) | Annual energy output of a unit of capacity running at 100%. |
| `CapacityOfOneTechnologyUnit` | `r, t, y` | capacity | Discrete unit size; forces integer builds when non-zero. |

### Activity ratios

| Parameter | Dimensions | Unit | Description |
|---|---|---|---|
| `InputActivityRatio` | `r, t, f, m, y` | energy/energy | Fuel `f` consumed per unit nominal activity of `t` in mode `m`. |
| `OutputActivityRatio` | `r, t, f, m, y` | energy/energy | Fuel `f` produced per unit nominal activity. |
| `EmissionActivityRatio` | `r, t, e, m, y` | mass/energy | Emissions of `e` per unit nominal activity. |

Zero is the effective default for both activity ratios. NEMO skips generating the full-grid view when the default is zero as a performance optimisation, so reading via `_def` may return the sparse table directly.

### Costs

| Parameter | Dimensions | Unit | Description |
|---|---|---|---|
| `CapitalCost` | `r, t, y` | cost/capacity | Overnight capex per unit capacity. |
| `CapitalCostStorage` | `r, s, y` | cost/energy | Overnight capex per unit storage energy capacity. |
| `FixedCost` | `r, t, y` | cost/(capacity·year) | Fixed O&M per installed unit per year. |
| `VariableCost` | `r, t, m, y` | cost/energy | Variable O&M per unit activity. |
| `EmissionsPenalty` | `r, e, y` | cost/mass | Cost levied per unit emission. |
| `DiscountRate` | `r` | fraction | Region-level social discount rate. |
| `InterestRateTechnology` | `r, t, y` | fraction | Technology financing rate (v7+). |
| `InterestRateStorage` | `r, s, y` | fraction | Storage financing rate (v7+). |
| `DepreciationMethod` | `r` | code | 1 = sinking-fund; 2 = straight-line salvage. |

### Operational life

| Parameter | Dimensions | Unit |
|---|---|---|
| `OperationalLife` | `r, t` | year |
| `OperationalLifeStorage` | `r, s` | year |

### Capacity bounds

| Parameter | Dimensions |
|---|---|
| `ResidualCapacity` | `r, t, y` |
| `ResidualStorageCapacity` | `r, s, y` |
| `TotalAnnualMaxCapacity` | `r, t, y` |
| `TotalAnnualMinCapacity` | `r, t, y` |
| `TotalAnnualMaxCapacityStorage` | `r, s, y` |
| `TotalAnnualMinCapacityStorage` | `r, s, y` |
| `TotalAnnualMaxCapacityInvestment` | `r, t, y` |
| `TotalAnnualMinCapacityInvestment` | `r, t, y` |
| `TotalAnnualMaxCapacityInvestmentStorage` | `r, s, y` |
| `TotalAnnualMinCapacityInvestmentStorage` | `r, s, y` |

### Activity bounds

| Parameter | Dimensions |
|---|---|
| `TotalTechnologyAnnualActivityUpperLimit` | `r, t, y` |
| `TotalTechnologyAnnualActivityLowerLimit` | `r, t, y` |
| `TotalTechnologyModelPeriodActivityUpperLimit` | `r, t` |
| `TotalTechnologyModelPeriodActivityLowerLimit` | `r, t` |

### Renewable targets and minimum shares

| Parameter | Dimensions | Description |
|---|---|---|
| `REMinProductionTarget` | `r, f, y` | Fraction of fuel `f` production in region `r` year `y` that must come from renewable technologies. Fuel dimension added v8. |
| `REMinProductionTargetRG` | `rg, f, y` | Same but aggregated over a region group. |
| `RETagTechnology` | `r, t, y` | 1 if technology is renewable for RE accounting. |
| `MinShareProduction` | `r, t, f, y` | Minimum share of fuel `f` production that must come from `t` (v8+). |
| `MinimumUtilization` | `r, t, l, y` | Minimum utilisation of installed capacity per slice (v6+). |

### Reserve margin

| Parameter | Dimensions | Description |
|---|---|---|
| `ReserveMargin` | `r, f, y` | Required fractional reserve over peak demand for fuel `f`. Fuel dim added v10. |
| `ReserveMarginTagTechnology` | `r, t, f, y` | Fraction of technology capacity that contributes to the margin for fuel `f`. |

`ReserveMarginTagFuel` existed in v9 and earlier; it was removed in v10, with its behaviour encoded directly into the fuel-indexed `ReserveMargin`.

### Ramping

| Parameter | Dimensions | Description |
|---|---|---|
| `RampRate` | `r, t, y, l` | Maximum fractional change in output between adjacent time slices (v5+). |
| `RampingReset` | `r` | Flag controlling when ramping constraints reset. |

### Storage

| Parameter | Dimensions |
|---|---|
| `MinStorageCharge` | `r, s, y` |
| `StorageLevelStart` | `r, s` |
| `StorageMaxChargeRate` | `r, s` |
| `StorageMaxDischargeRate` | `r, s` |
| `StorageFullLoadHours` | `r, s, y` |
| `TechnologyFromStorage` | `r, t, s, m` |
| `TechnologyToStorage` | `r, t, s, m` |

### Emission limits

| Parameter | Dimensions |
|---|---|
| `AnnualEmissionLimit` | `r, e, y` |
| `AnnualExogenousEmission` | `r, e, y` |
| `ModelPeriodEmissionLimit` | `r, e` |
| `ModelPeriodExogenousEmission` | `r, e` |

### Trade and transmission

| Parameter | Dimensions | Description |
|---|---|---|
| `TradeRoute` | `r, rr, f, y` | 1 if fuel `f` can move from `r` to `rr` in year `y`. |
| `TransmissionModelingEnabled` | `r, f, y` (+ `type`) | Presence switches on nodal flow modelling; `type` selects linearisation. |
| `TransmissionCapacityToActivityUnit` | `r, f` | Conversion factor, analogous to `CapacityToActivityUnit`. |
| `TransmissionAvailabilityFactor` | `tr, l, y` | Per-slice availability of a line (v10+, default 1.0). |
| `MinAnnualTransmissionNodes` | `n1, n2, f, y` | Lower bound on annual inter-node flow (v11). |
| `MaxAnnualTransmissionNodes` | `n1, n2, f, y` | Upper bound on annual inter-node flow (v11). |

### Nodal distribution

| Parameter | Dimensions | Description |
|---|---|---|
| `NodalDistributionDemand` | `n, f, y` | Fraction of regional demand allocated to node. |
| `NodalDistributionTechnologyCapacity` | `n, t, y` | Fraction of regional capacity allocated to node. |
| `NodalDistributionStorageCapacity` | `n, s, y` | As above for storage. |

---

## Result variables (output tables)

Every result table is named `v*` and carries its dimension columns, a `val REAL`, and a `solvedtm TEXT` timestamp. NEMO appends rows on each solve; filter to the latest `solvedtm` for clean analysis. Only variables listed in `varstosave` (argument to `calculatescenario`) are present.

### Capacity

| Variable | Dimensions | Description | Unit |
|---|---|---|---|
| `vnewcapacity` | `r, t, y` | Endogenously built capacity in year `y`. | capacity |
| `vaccumulatednewcapacity` | `r, t, y` | Running sum of `vnewcapacity` subject to lifetime. | capacity |
| `vtotalcapacityannual` | `r, t, y` | `ResidualCapacity` + accumulated new within operational life. | capacity |
| `vnewstoragecapacity` | `r, s, y` | New endogenous storage energy capacity. | energy |
| `vaccumulatednewstoragecapacity` | `r, s, y` | | energy |
| `vtotalcapacityinreservemargin` | `r, f, y` | Capacity contributing to reserve margin for fuel `f`. | capacity |

### Activity (annual)

| Variable | Dimensions | Description | Unit |
|---|---|---|---|
| `vtotaltechnologyannualactivity` | `r, t, y` | Nominal annual activity of `t`. | energy |
| `vtotaltechnologymodelperiodactivity` | `r, t` | Activity summed over model horizon. | energy |
| `vtotalannualtechnologyactivitybymode` | `r, t, m, y` | As above, split by operating mode. | energy |
| `vproductionbytechnologyannual` | `r, t, f, y` | Annual production of `f` by `t`. | energy |
| `vusebytechnologyannual` | `r, t, f, y` | Annual use of `f` by `t`. | energy |
| `vproductionannualnn` | `r, f, y` | Non-nodal annual production of `f`. | energy |
| `vuseannualnn` | `r, f, y` | Non-nodal annual use of `f`. | energy |
| `vgenerationannualnn` | `r, f, y` | Production excluding storage discharge. | energy |
| `vregenerationannualnn` | `r, f, y` | Renewable generation (weighted by `RETagTechnology`). | energy |
| `vdemandnn` | `r, l, f, y` | Non-nodal demand in time slice. | energy |
| `vdemandannualnn` | `r, f, y` | Non-nodal annual demand. | energy |
| `vproductionannualnodal` | `n, f, y` | Nodal annual production. | energy |
| `vuseannualnodal` | `n, l, f, y` | Nodal annual use. | energy |
| `vgenerationannualnodal` | `n, f, y` | | energy |
| `vregenerationannualnodal` | `n, f, y` | | energy |

### Activity (time-sliced and rates)

Time-sliced activity variables have `l` in their dimensions. Rate variables have units of energy per year and must be multiplied by `YearSplit × 8760` to yield energy.

| Variable | Dimensions |
|---|---|
| `vproductionnn` | `r, l, f, y` |
| `vusenn` | `r, l, f, y` |
| `vproductionbytechnology` | `r, l, t, f, y` |
| `vusebytechnology` | `r, l, t, f, y` |
| `vrateofactivity` | `r, l, t, m, y` |
| `vrateoftotalactivity` | `r, t, l, y` |
| `vrateofproduction` | `r, l, f, y` |
| `vrateofuse` | `r, l, f, y` |
| `vrateofproductionbytechnologynn` | `r, l, t, f, y` |
| `vrateofusebytechnologynn` | `r, l, t, f, y` |
| `vrateofproductionbytechnologybymodenn` | `r, l, t, m, f, y` |
| `vrateofusebytechnologybymodenn` | `r, l, t, m, f, y` |
| `vrateofproductionnn` | `r, l, f, y` |
| `vrateofusenn` | `r, l, f, y` |
| `vproductionnodal` | `n, l, f, y` |
| `vusenodal` | `n, l, f, y` |
| `vrateofactivitynodal` | `n, l, t, m, y` |
| `vrateoftotalactivitynodal` | `n, t, l, y` |
| `vrateofproductionnodal` | `n, l, f, y` |
| `vrateofusenodal` | `n, l, f, y` |
| `vrateofproductionbytechnologynodal` | `n, l, t, f, y` |
| `vrateofusebytechnologynodal` | `n, l, t, f, y` |

### Emissions

| Variable | Dimensions | Unit |
|---|---|---|
| `vannualtechnologyemission` | `r, t, e, y` | mass |
| `vannualtechnologyemissionbymode` | `r, t, e, m, y` | mass |
| `vannualtechnologyemissionpenaltybyemission` | `r, t, e, y` | cost |
| `vannualtechnologyemissionspenalty` | `r, t, y` | cost |
| `vdiscountedtechnologyemissionspenalty` | `r, t, y` | cost |
| `vannualemissions` | `r, e, y` | mass |
| `vmodelperiodemissions` | `r, e` | mass |

`vannualemissions` includes `AnnualExogenousEmission` added directly to the region-year; technology-specific results do not.

### Costs

All cost variables carry the scenario cost unit. Discounted variants are discounted to the first year in YEAR using the region's `DiscountRate`.

| Variable | Dimensions |
|---|---|
| `vcapitalinvestment` | `r, t, y` |
| `vdiscountedcapitalinvestment` | `r, t, y` |
| `vcapitalinvestmentstorage` | `r, s, y` |
| `vdiscountedcapitalinvestmentstorage` | `r, s, y` |
| `vcapitalinvestmenttransmission` | `tr, y` |
| `vdiscountedcapitalinvestmenttransmission` | `tr, y` |
| `vfinancecost` | `r, t, y` |
| `vfinancecoststorage` | `r, s, y` |
| `vfinancecosttransmission` | `tr, y` |
| `voperatingcost` | `r, t, y` |
| `vdiscountedoperatingcost` | `r, t, y` |
| `voperatingcosttransmission` | `tr, y` |
| `vdiscountedoperatingcosttransmission` | `tr, y` |
| `vannualfixedoperatingcost` | `r, t, y` |
| `vannualvariableoperatingcost` | `r, t, y` |
| `vvariablecosttransmission` | `tr, y` |
| `vvariablecosttransmissionbyts` | `tr, l, f, y` |
| `vsalvagevalue` | `r, t, y` |
| `vsalvagevaluestorage` | `r, s, y` |
| `vsalvagevaluetransmission` | `tr, y` |
| `vdiscountedsalvagevalue` | `r, t, y` |
| `vdiscountedsalvagevaluestorage` | `r, s, y` |
| `vdiscountedsalvagevaluetransmission` | `tr, y` |
| `vtotaldiscountedcost` | `r, y` |
| `vmodelperiodcostbyregion` | `r` |

`vtotaldiscountedcost` is the per-(r,y) component of the objective function; summing over r and y gives the scalar that the solver minimised.

### Trade and transmission

| Variable | Dimensions |
|---|---|
| `vtradeannual` | `r, rr, f, y` |
| `vtrade` | `r, rr, l, f, y` |
| `vtransmissionbuilt` | `tr, y` |
| `vtransmissionexists` | `tr, y` |
| `vtransmissionbyline` | `tr, l, f, y` |
| `vtransmissionannual` | `n, f, y` |

### Storage

| Variable | Dimensions |
|---|---|
| `vstoragelevelyearstart` | `r, s, y` |
| `vstoragelevelyearfinish` | `r, s, y` |
| `vstoragelevelseasonstart` | `r, s, ls, y` |
| `vstorageleveldaytypestart` | `r, s, ls, ld, y` |
| `vstorageleveldaytypefinish` | `r, s, ls, ld, y` |
| `vstoragelevelts` | `r, s, l, y` |
| `vstoragelevelnodal` | `n, s, l, y` |

`ls` and `ld` refer to TSGROUP1 and TSGROUP2 members respectively in the seasonal/day-type storage variables.

---

## Custom constraints (`__NEMOcc` tables)

LEAP lets the modeller define custom NEMO constraints. Each one gets its own table in the scenario database with the name suffix `__NEMOcc`. The convention the library handles is:

| Column | Type | Meaning |
|---|---|---|
| `id` | INTEGER | surrogate row identifier |
| `r` | TEXT | region (or "All" / group label) |
| `bid` | TEXT | LEAP branch ID identifying the technology or fuel group the constraint applies to |
| `eid` | TEXT | secondary identifier; often `-1` as a "not applicable" sentinel |
| `y` | TEXT | year; may have finer resolution than the model's YEAR set (e.g. annual 2025–2060 when YEAR is sparse) |
| `val` | REAL | constraint value |

Typical examples encountered in the wild: `ASEANRenewableCapacityTarget__NEMOcc`, `AllRegionsGHGLimit__NEMOcc`, `RenewableCapacityTarget__NEMOcc`, `SingleRegionGHGLimit__NEMOcc`. The stock NEMO source does not fix these columns — the suffix is the reliable marker — so the library discovers them at runtime via `list_custom_constraints()` and reads them generically with `get_custom_constraint()`.

Because `bid` encodes LEAP's internal tree structure, joining a `__NEMOcc` table back to `TECHNOLOGY.val` requires the LEAP area file. The scenario database alone carries only the numeric IDs.

---

## Slack technologies

LEAP/NEMO scenarios almost always carry synthetic "unserved demand" or supply-side slack technologies so the optimiser can always find a feasible solution. These inflate summary statistics if not filtered out. Recognition heuristics, encoded in `nemo_read.detect_slack_technologies`:

| Signal | Threshold | Typical example |
|---|---|---|
| High residual capacity | `ResidualCapacity.val >= 1e11` | 10¹² capacity on synthetic supply techs for liquid fuels, coal, etc. |
| High capital cost | `CapitalCost.val >= 1e5` | 10⁶ on unserved-demand pseudo-processes |
| Name pattern match | case-insensitive `unserved`, `unmet` | `"Unserved"`, `"Unmet Load"`, `"Unmet Load_IDJW"` |

Thresholds are configurable. The library flags each match with a `reason` field so users can audit why a technology was classified as a slack.

---

## Data quirks and LEAP conventions

Edge cases that come up repeatedly in LEAP-generated databases and are worth knowing before you trust a query result.

### Boolean-ish parameters only store `1.0` when present

Three parameters are effectively boolean flags even though the column type is `REAL`:

- `TechnologyFromStorage` — flag for "this tech discharges from storage `s` in mode `m`"
- `TechnologyToStorage` — flag for "this tech charges into storage `s` in mode `m`"
- `RETagTechnology` — flag for "this tech counts as renewable for `RETagFuel`-like constraints"
- `ReserveMarginTagTechnology` — flag for "this tech contributes to reserve margin"

When populated, `val` is always `1.0` (and when absent, the default is `0.0`, meaning "not tagged"). Treat any row in these tables as a truthy flag and ignore the numeric value.

### `TransmissionModelingEnabled.type`

The value column is `type` (INTEGER), not `val`. NEMO uses it to select the transmission formulation per `(r, f, y)`:

| `type` | Formulation | Meaning |
|---|---|---|
| 1 | Pipeline flow | Simple flow conservation with efficiency |
| 2 | DC power flow | Linearised AC with reactance |
| 3 | Point-to-point | Explicit `MaxAnnualTransmissionNodes` / `MinAnnualTransmissionNodes` between nodes |

The library's `get_parameter("TransmissionModelingEnabled")` returns a DataFrame with columns `(r, f, y, type)` — note the last column name.

### Negative `EmissionsPenalty` and `EmissionActivityRatio` are legitimate

NEMO's documentation explicitly supports both:

- **`EmissionsPenalty < 0`**: subsidy for producing that pollutant. Used for carbon removal / sequestration incentives.
- **`EmissionActivityRatio < 0`**: the technology *sequesters* the pollutant per unit activity rather than emitting it.

In practice these appear together for CCS/BECCS/DAC configurations: emission species `E407` "Sequestered Carbon Dioxide" gets a negative activity ratio on the CCS technology and a negative penalty to reward the sequestration.

**Unbounded-profit risk**: per NEMO docs, when a technology can generate negative emissions of a pollutant with a negative penalty AND has no activity or capacity upper bound, the optimisation becomes unbounded (infinite profit from sequestration). The validator's `emissions` category warns about this; fix by adding `TotalAnnualMaxCapacity`, `TotalTechnologyAnnualActivityUpperLimit`, or equivalent.

### `lorder` is per-`(tg1, tg2)` group, not globally unique

`LTsGroup.lorder` ranges from 1 to N within each `(TSGROUP1, TSGROUP2)` combination, not across the full set of timeslices. A scenario with 2 seasons × 1 day-type × 24 hour-slices has `lorder` values 1..24 appearing twice (once per season), not 1..48. For chronological ordering in dispatch plots, sort by `(TSGROUP1.order, TSGROUP2.order, lorder)`. The library's `timeslices()` helper already does this and exposes `tg1_order` and `tg2_order` columns.

### Candidate transmission lines use `yconstruction > min(YEAR)`

A transmission line is a candidate investment (decision variable in NEMO) when its `yconstruction` exceeds the earliest modelled year, not the latest. `transmission_candidates(db)` implements the correct check.

### `MODE_OF_OPERATION` convention

LEAP's export always creates exactly two modes: `M1 = Generation`, `M2 = Storage`. Any custom-constraints script or analysis code that assumes "mode 1" means generation and "mode 2" means storage is relying on this LEAP convention, not a NEMO guarantee.

### Demand technology sub-classification

Demand technologies (IDs beginning with `D`) encode a `"Category:Fuel"` pattern in their `desc` field (e.g. `"Optimized Buses:Electricity"`). The categories are LEAP transport-sector groupings; splitting on the `:` gives the demand sector and the fuel/drivetrain choice.

### `DiscountRate` table is often empty

NEMO carries a region-level `DiscountRate` but LEAP typically leaves the table empty and relies on the `DefaultParams` fallback (usually 0.07). The library's default-overlay machinery returns the default correctly in this case; `list_populated_parameters(db)` will show `rows=0, default=0.07`.

### Unreferenced technologies

Per NEMO: "NEMO will not simulate activity for a (r, t, m, y) unless you define a corresponding non-zero `OutputActivityRatio` or `InputActivityRatio`." Technologies declared in `TECHNOLOGY` but never referenced by any parameter are dormant. Use `list_unused_technologies(db)` to find them.

Note: a technology referenced only by a `__NEMOcc.bid` still appears in `list_unused_technologies()` because the `bid` numeric value does not resolve to a technology ID without external (LEAP area) data.

---

## Version history

Each NEMO data-dictionary version bump reflects a schema change. Relevant transitions for LEAP users:

| Version | Changes |
|---|---|
| 2 | `STORAGE.netzeroyear`, `STORAGE.netzerotg1`, `STORAGE.netzerotg2` added. |
| 3 | `TransmissionLine.efficiency` added. |
| 4 | `TransmissionCapacityToActivityUnit.r` added (per-region conversion). |
| 5 | `RampRate`, `RampingReset` added. |
| 6 | `MinimumUtilization`, `DiscountRateStorage`, `DiscountRateTechnology`, `TransmissionLine.discountrate` added. |
| 7 | Discount rate parameters replaced by `InterestRateStorage`, `InterestRateTechnology`, `TransmissionLine.interestrate`. |
| 8 | `RETagFuel` removed. `REMinProductionTarget.f` added. `MinShareProduction` added. |
| 9 | `REGIONGROUP`, `RRGroup`, `REMinProductionTargetRG` added. |
| 10 | `ReserveMargin.f` and `ReserveMarginTagTechnology.f` added. `ReserveMarginTagFuel` removed. `AvailabilityFactor` (old) dropped. `CapacityFactor` renamed to `AvailabilityFactor`. `TransmissionAvailabilityFactor` added. |
| 11 | `MinAnnualTransmissionNodes`, `MaxAnnualTransmissionNodes` added. |

The v9 → v10 transition is the most disruptive for older scripts because the rename `CapacityFactor → AvailabilityFactor` breaks any code referencing the former name.

---

## Column abbreviation legend

| Abbreviation | Dimension table |
|---|---|
| `r` | `REGION` |
| `rr` | `REGION` (destination in trade) |
| `rg` | `REGIONGROUP` |
| `t` | `TECHNOLOGY` |
| `f` | `FUEL` |
| `e` | `EMISSION` |
| `m` | `MODE_OF_OPERATION` |
| `s` | `STORAGE` |
| `y` | `YEAR` |
| `l` | `TIMESLICE` |
| `n`, `n1`, `n2` | `NODE` |
| `tr` | `TransmissionLine` |
| `tg1` | `TSGROUP1` |
| `tg2` | `TSGROUP2` |

The mapping is exposed programmatically as `nemo_read.DIMENSION_ABBREVIATIONS`.
