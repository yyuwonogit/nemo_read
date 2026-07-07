# LEAP Structure Anatomy — `aeo9_v0.67_w_results`

> **What this is.** A structural digest of the seven export workbooks in this
> folder — `LEAP Input {Commercial, Transport, Residential, Industry}.xlsx`
> (the `Demand\` subtrees), `LEAP Input Keys.xlsx` (the `Key\` assumption
> tree), `LEAP Input Resources.xlsx` (the `Resources\` supply tree), and
> `LEAP Input Transformation.xlsx` (the `Transformation\` conversion tree —
> power generation, refining, biofuel/clean-fuel production, blending) — all
> exported from LEAP area **`aeo9_v0.67_w_results`**. Generated 2026-07-02/04
> by converting all 2,435,820 export rows to flat CSVs offline and analysing
> them (no LEAP COM was touched). Every quantitative claim was produced by a
> query against the export data and independently re-verified by a second
> pass; claims that could not be verified are marked as inference. Full
> branch trees (one indented line per branch, with the variables attached to
> it) are in [trees/](trees/).
>
> **Why it matters for this repo.** These are the same `Demand\` (and, via
> expression references, `Key\`) branches that CanonicalInjector targets —
> KA/Demand branches, blind-mode mandatory per CLAUDE.md §A.20. The branch
> paths, variable names, units, and expression idioms below are the authoring
> vocabulary for any future demand-side inject.
>
> **Canon status (user directive 2026-07-02, CLAUDE.md §2.6).** This
> structure is CANON and the default for all future LEAP area versions:
> branch paths, variable attachment, units, and the scenario/region rosters
> are assumed stable; **expression content is not canon** and may differ per
> version and scenario. A future export whose *structure* deviates is an
> anomaly to flag, not a silent re-derivation.

Sector sizes at a glance:

| Export | Rows | Branches | Max depth | Variables | Scenarios | Regions |
|---|---|---|---|---|---|---|
| Commercial | 89,940 | 426 | 8 | 13 | 11 | 12 |
| Transport | 60,096 | 165 | 6 | 24 | 11 | 12 |
| Residential | 146,544 | 530 | 7 | 35 | 11 | 12 |
| Industry | 1,008,012 | 5,859 | 10 | 10 | 11 | 12 |
| Keys (`Key\`) | 440,220 | 1,064 | 8 | 26 | 11 | 12 |
| Resources | 113,760 | 62 | 3 | 20 | 11 | 12 |
| Transformation | 577,248 | 1,593 | 7 | 80 | 11 | 12 |

One row = one (branch, variable, scenario, region). The row space is sparse —
each branch carries only its own variable set (commercial has 695
(branch, variable) combos, not 426×13) — but every existing combo is
materialised for all 11 scenarios × 12 regions, so most rows are 11
near-duplicates: LEAP lists inherited (not re-authored) expressions under
every scenario.

---

## 1. The export format ("Export Expressions", Ver 2)

Each workbook is a single sheet named **`Export`**, identical layout in all
four files:

- **Row 1** — area stamp: `E1="Area:"`, `F1="aeo9_v0.67_w_results"`,
  `G1="Ver:"`, `H1="2"`. **Row 2** — blank. **Row 3** — header.
  **Row 4** — first data row.
- **Columns A–L**: `BranchID, VariableID, ScenarioID, RegionID, Branch Path,
  Variable, Scenario, Region, Scale, Units, Per..., Expression`. Column M is
  blank.
- **Columns N–U**: `Level 1 … Level 7, Level 8...` — the Branch Path split on
  `\`. The last column is literally headed `Level 8...`: for branches deeper
  than 8 levels (industry only) it holds the **joined remainder** of the path
  (a depth-9 branch shows e.g. `Gasoline\Ammonia` in that single cell). A
  naive Level-column parser therefore under-splits 4,932 industry branches —
  parse `Branch Path`, not the Level columns. No data exists beyond column U.
- Units live in three columns: `Scale` (Thousand, Million, %…), `Units`, and
  `Per...` (the denominator). All three must be read together — e.g. Activity
  Level `Share | % | of Square Meter`.

---

## 2. Scenario roster and bloc structure

Identical IDs and names in all four sectors (verified by ID→name map
comparison):

| ID | Scenario | Role (from divergence data, not folklore) |
|---|---|---|
| 1 | Current Accounts | Historical accounts. Carries extra CA-only calibration rows in every sector (§2.1). |
| 18 | Baseline Simulation | Closest to CA everywhere: 30 comm / 23 trans / 70 res / 33 ind diverging (branch,variable) combos. |
| 11 | Set up | Member of the six-name policy bloc (below). |
| 20 | AMS Target Scenario | Policy-bloc anchor; residential RE-LTRM rows pull `ScenarioValue(AMS Target Scenario)`. |
| 26 | LCO backup | Expression-identical to the policy bloc in the demand sectors and Resources — but in the Key tree it sits **273 cells off Set up** (Annual EI Reduction 132, Capacity Additions Multiplier 129, Clean Cooking 12): the "backup" carries its own driver settings (§12.4). |
| 27/28/29 | RE LTRM ASEAN Policy Aligned / RE Coupling / Shared Energy Resources | **Byte-identical to each other in all four demand sectors** (0 differing rows) — but the triplet IS differentiated upstream: 12 cells apart in the Key tree (2030 biofuel-blend points + faster industry-EI decline in Coupling/Shared, §12.4) and 7 cells in Resources (Ethanol Import Cost tariff variants, §13.5). |
| 25 | Regional Aspiration Scenario | One of the two most-edited: 72 / 33 / 105 / 91 combos diverge from CA. |
| 12 | Carbon Neutrality_ Net Zero Scenario | The other most-edited (72 / 42 / 106 / 91); layers Net Zero Measures on top of RAS. |
| 30 | Regional Aspiration Scenario test | A diverged RAS variant (45 / 23 / 78 / 63) — mostly frozen numeric snapshots of formula expressions (see per-sector notes). Appears to be a stale prototype, not a live copy. |

**Bloc structure.** The 10 projection scenarios collapse into a small number
of expression-equivalence classes per sector:

- **Commercial**: `Set up = LCO backup = AMS Target = RE LTRM ×3` (0 pairwise
  diffs — six names, one expression set); RAS and CNZ layer targets on top;
  `RAS test` diverges from RAS by 366 cells; Baseline differs from CA by 360
  cells (all in `Historical`).
- **Transport**: `RAS = LCO backup = Set up = RE LTRM ×3` (0 diffs);
  `Baseline = RAS test` (0 diffs); AMS Target sits 4 rows off RAS; CNZ 130
  rows off RAS.
- **Residential**: only the RE LTRM triplet collapses (0 diffs). `Set up`,
  `LCO backup`, `RAS test` all genuinely diverge (1,446 / 1,417 / 608
  (branch,variable,region) expressions off RAS respectively).
- **Industry**: `Set up = LCO backup = RE LTRM ×3` (0 diffs) and
  `Carbon Neutrality = Regional Aspiration Scenario` (0 diffs); `RAS test`
  is the most divergent scenario vs CA (756 keys).

Treating the area as having 11 distinct demand-side policy states is wrong;
depending on sector it has 4–7.

### 2.1 Scenario-scoped rows (row-count fingerprints)

CA carries extra rows in every sector, and they are exactly the
calibration/base-year variables:

| Sector | CA rows | Other scenarios | CA-only content |
|---|---|---|---|
| Commercial | 8,340 | 8,160 | `UnscaledFuelShare` on the 15 Historical fuels (15 combos × 12 regions = 180 rows) |
| Transport | 5,856 | 5,424 | `Stock` (16 combos), `First Sales Year` (16), `Share_FossilFuels` (4) — base-year stock data |
| Industry | 91,932 | 91,608 | `UnscaledFuelShare` on 27 of 28 Historical fuels (324 rows; `Solar Heating` lacks it) |
| Residential | 12,168 | 11,472 or **14,280** | three-way split, below |
| Keys | 40,020 | 40,020 | none — perfectly rectangular, zero scenario-scoped rows (§12) |
| Resources | 10,440 | 10,332 | the **variable set itself splits by scenario**: 4 accounting scenarios (CA, Baseline, AMS Target, RAS test) carry `Imports` + `Cost of Unmet Requirements`; the 7 optimization scenarios carry `Minimum Imports` + `Maximum Imports` instead; CA adds `Base Year Reserves` (§13.5) |

Residential splits three ways: 11,472 rows (Baseline, AMS Target, RAS test),
12,168 (CA), **14,280** (Set up, CNZ, RAS, LCO backup, RE LTRM ×3). The
seven 14,280-row scenarios carry 262 extra (branch,variable) combos — 258
of them the entire **device-stock economics panel** (`Capital Cost`, `Fixed/Variable OM
Cost`, `Lifetime`, `Interest Rate`, `Exogenous/Minimum/Maximum Devices`,
`Maximum/Minimum Device Additions`, `Unit Capacity`, `Minimum Share`,
`Minimum Utilization`, `Maximum Availability`, `Optimize Devices`) on the
`Air Conditioning_` and `Refrigeration_` tiers (129 combos each). Those
variables **do not exist as rows** under CA, Baseline Simulation, AMS Target,
or RAS test. Directly relevant to the residential AC + fridge device-stock
inject work: an inject targeting those variables only lands in the 7
scenarios that host them.

---

## 3. Region roster

Identical across all four sectors. IDs are sparse and non-contiguous
(consistent with regions deleted earlier in the area's history — inference):

| ID | Region | | ID | Region |
|---|---|---|---|---|
| 1 | Indonesia | | 15 | Brunei |
| 6 | Cambodia | | 16 | Singapore |
| 7 | **Base Template** (LEAP pseudo-region, not a country) | | 17 | Malaysia |
| 11 | Thailand | | 19 | Philippines |
| 12 | Myanmar | | 20 | Timor Leste |
| 13 | Laos | | 14 | Vietnam |

IDs 2–5, 8–10, 18 are absent. Every region has an identical row count within
a sector (7,495 each in commercial … 84,001 each in industry): the export
materialises all 12 region slots for every row, so regional differences live
purely in the Expression column.

**Timor Leste** is fully populated row-wise but holds template-grade content
throughout: `ShapeFlat` load shapes (no `Timor Leste_Hourly` shape exists in
the YearlyShape roster), template-default mileage/intensity values, and
Key-formula stock instead of registration data. Same for Base Template.
Demand-side TL rows exist but are not researched values (relevant to the
§A.18 Timor Leste policy).

---

## 4. `Key\` driver architecture (the de-facto exogenous tree)

> **Ground truth now available.** The full `Key\` tree was exported on
> 2026-07-02 (`LEAP Input Keys.xlsx`) and is documented in §12. Resolution
> check: of the 275 distinct (branch, variable) references the four demand
> sectors make into `Key\`/`Resources\`, **273 resolve** in the exports; the
> 2 misses (`Key\Residential\AC\a`/`b`) are comment-only citations of a
> retired equation, not live references (§12.6). This section keeps the
> demand-side consumption view; §12 has the tree itself.

Union across the four demand sectors: **241 distinct `Key\` paths** in
11 top-level groups. Reference occurrences (rows containing the pattern) per
sector:

| Key group (distinct paths) | comm | trans | res | ind |
|---|---|---|---|---|
| `Key\Industry\…` (112: Intensity 84, Appliances_share, Subsector_share, Cal, Steel/Cement RAS Measures) | 0 | 0 | 0 | 22,208 |
| `Key\Cal\…` (25: Cal\Commercial 12 fuels, Cal\Residential 13 — per-fuel calibration factors) | 3,168 | 0 | 5,350 | 0 |
| `Key\TransportDataStock\…` (39: Vehicle_Sales, Vehicles_Sales_Share, Vehicle_Stock_Share, BaseYear_StockData) | 0 | 4,362 | 0 | 0 |
| `Key\Macroeconomic\…` (5: Real GDP Service / Real GDP Industry / Real GDP Per Capita / Gross Fixed Capital Formation / Manufacturing Fraction in Industry) | 1,660 | 0 | 1,272 | 3,989 |
| `Key\Residential\…` (30: Refrigeration / Air Conditioning stock trees, AC a/b coefficients) | 0 | 0 | 3,268 | 0 |
| `Key\Energy Access\…` (2: Electrification Rate, Clean Cooking Access) | 0 | 0 | 264 | 2,232 |
| `Key\Net Zero Measures\…` (13: Residential 9, Transport\Aviation 4) | 264 | 48 | 1,640 | 0 |
| `Key\Annual EI Reduction\…` (2: EI_Improvement_RAS_2, FuelEco) | 864 | 672 | 0 | 0 |
| `Key\Demographic\…` (2: Households, Household Size) | 0 | 0 | 396 | 0 |
| `Key\Commercial\Gross Floor_Area` (1) | 264 | 0 | 0 | 0 |
| `Key\Residential end use data_\…` (10: historical appliance counts) | 0 | 0 | 228 | 0 |

Pattern: **Macroeconomic + Energy Access + Demographic are the shared
exogenous spine** (the only groups consumed by more than one sector); each
sector then owns one private subtree (`Industry\Intensity`,
`TransportDataStock`, `Residential\<appliance>`, `Commercial\Gross
Floor_Area`) plus `Cal\<sector>` calibration factors and
`Net Zero Measures\<sector>` policy levers. A change to a shared macro driver
propagates to up to three sectors; Cal-factor and NZ-measure edits stay
sector-local.

Transport additionally references GDP as the bare, non-Key-prefixed
`GDP[Million 2021 USD]` (396 rows) — same driver family, different citation
form. Note the dollar-vintage drift: activity units say "Million 2020 USD"
while expressions cite `[Million 2021 USD]`.

---

## 5. Shared expression idioms

Rows containing each pattern (verbatim example from the data):

| Idiom | comm | trans | res | ind | Example |
|---|---|---|---|---|---|
| `Interp(` | 555 | 2,080 | 6,687 | 3,728 | `Interp(2005, 434.57, 2006, 383.148, …, 2017, 23.461)` |
| `InterpFSY(` | 1,102 | 27 | 1,603 | 76 | `InterpFSY(2050, 20) ? ATS assumption` |
| `Step(` | 264 | 0 | 264 | 264 | `Step(2005, 100, 2025, 0)` — era switch, §5.1 |
| `Growth(` | 72 | 3,072 | 2,371 | 162 | `Growth(Key\Annual EI Reduction\FuelEco:Activity Level[%]) ? 1.5-5% acceptable fuel economy improvement range for AMS` |
| `GrowthAs(` | 0 | 0 | 0 | 1,440 | `GrowthAs(Key\Macroeconomic\Real GDP Industry)` |
| `Remainder(100)` | 1,049 | 92 | 2,577 | 658 | share closure on the last sibling of a % partition |
| `YearlyShape(` | 2,376 | 770 | 3,960 | 4,070 | `YearlyShape(Indonesia_Hourly)` on Load Shape |
| `ScenarioValue(` | 912 | 12 | 230 | 19 | `ScenarioValue(Baseline Simulation) / Key\Annual EI Reduction\EI_Improvement_RAS_2:Activity Level[Factor]` |
| `Value(` | 2,492 | 298 | 650 | 19 | `Value(Demand\Commercial\Other Commercial\Historical\Electricity:Fuel Share[% Share],  2022)` |
| `Exp(…Ln(…))` regression | 1,660 | 0 | 0 | 2,232 | see §5.2 — mostly unfitted templates |
| `Data(` | 0 | 112 | 791 | 18,480 | `Data(2005,100,2006,100,…)` — year-pair alternative to Interp |
| `If(` | 0 | 22 | 24 | 24 | transport aviation CNZ switch |
| `?` inline comment | 48,525 | 14,051 | 56,586 | 369,429 | `20230 ? source: 2022 ERIA Analysis of Future Mobility Fuel Scenarios Phase II` |

The `?` comment idiom doubles as the model's provenance layer: source
citations (ERIA, ENERGY STAR, World Bank, IEEJ, BEI), assumption tags
(`? ATS assumption`, `? RAS assumption`, `? CNS assumption`), and placeholder
confessions (`? ACE temp value`, `?placeholder`, `? Fill in historical data
here`). Emission factors carry bare single-letter footnotes (`?a ?b ?c ?d`)
with **no legend anywhere in the export**.

### 5.1 The Historical / Projection era switch

Commercial, residential and industry pair a `Historical` accounting subtree
with a projection subtree, hand-switched at 2025 via complementary Activity
Level Steps: the kill-switch `Step(2005, 100, 2025, 0)` on the Historical
node (132 rows per sector) mirrored by `Step(2005, 0, 2025, 100)` on the
projection node (another 132 rows; the 264 totals above are the two
combined). Naming is inconsistent — commercial `End Use Projection`,
residential `Projections`, industry `Projection\End Use` — any generic
tree-walker must treat these as synonyms. Transport has no such split (it is
a stock-turnover model).

### 5.2 Calibration architecture (rhymes, but differs per sector)

- **Commercial fuel-share renormalisation** (commercial **only** — see
  hygiene note on industry): CA holds raw history (`Fuel Share =
  Interp(<historical %>)`) plus a CA-only helper `UnscaledFuelShare = Fuel
  Share[% Share]`; all 10 non-CA scenarios re-author
  `Fuel Share = 100 * UnscaledFuelShare[%]/ Total(UnscaledFuelShare[%])`
  (1,800 rows = 15 branches × 10 scenarios × 12 regions). Industry ships the
  CA-only `UnscaledFuelShare` helper (324 rows) but **zero** of its 1,008,012
  expressions reference it — dead machinery.
- **Transport** derives shares from energy totals instead:
  `TotalEnergyTran[Thousand TOE]*100/Total(TotalEnergyTran[Thousand TOE])`.
- **Intensity calibration factors**: commercial and residential multiply
  uncalibrated intensities by `Key\Cal\<Sector>\<Fuel>:Activity
  Level[Factor]` (3,168 and 5,350 referencing rows); industry's analogue is
  `Key\Industry\Cal\{Electricity, Liquid FF, Others, Cement, Iron and Steel,
  Total_}` (10,132 rows).
- **Historical intensity as data identity**: `Final Energy Intensity =
  TotalEnergy[Thousand TOE] / Total Activity[<activity unit>]` with the
  sector-suffixed custom total (`TotalEnergy` / `TotalEnergyRes` /
  `TotalEnergyTran` — same idiom, three names; greps must cover all three).
- **Unfitted econometric shells**: commercial (1,660 rows) and industry
  (2,232 rows) carry `Exp(1 * Ln(<consumer price>) + 1 * Ln(<GDP driver>) +
  1) * 1 ? Coefficients and intercept in exp() must be determined via
  regression…` — in industry 2,192 of them have every coefficient still at
  the placeholder value 1 (40 rows on 4 Historical fuel branches, e.g.
  `Historical\Diesel` `Exp(-0.61704*Ln(…)+0.79827*Ln(…)…)`, carry fitted
  coefficients but still bear the regression comment).

### 5.3 YearlyShape roster

16 shapes: `<Country>_Hourly` for exactly the 10 ASEAN member states (no
Timor Leste shape), `DC_Normal` (data centers), `AC_Residential_R1_Equatorial`
/ `R2_Continental` / `R3_Transitional` (AC climate zones — R1 = Brunei,
Indonesia, Malaysia, Singapore; R2 = Cambodia, Laos, Myanmar, Thailand; R3 =
Philippines, Vietnam), `Four_Wheel_S1` / `Two_Wheel_S1` (EV charging shapes).
Base Template and Timor Leste always fall back to `ShapeFlat`.

---

## 6. Effects layer (`Avg Environmental Loading`)

Pollutant leaves sit under fuel branches and carry only `Avg Environmental
Loading`. They dominate the exports: 359/426 commercial branches, 109/165
transport, 414/530 residential, 5,259/5,859 industry.

**Roster** — 13 pollutants, same names in all four sectors: Carbon Dioxide,
Carbon Dioxide Biogenic, Carbon Monoxide, Methane, Nitrous Oxide, Nitrogen
Oxides, Non Methane Volatile Organic Compounds, Sulfur Dioxide, Particulates
PM10, Particulates PM2pt5, Black Carbon, Organic Carbon, Ammonia — plus a
14th, **Sequestered Carbon Dioxide, industry only** (1,452 rows under CCS
process fuel leaves), authored as a *negative* loading with a capture-rate
ramp: `-107 * Interp(2030,0.8,2045,0.9,2055,0.95) ?placeholder` (80→95%).

**Units** are heterogeneous by design: dominant `Kilogramme per Terajoule`
(561,660 of industry's 694,188 effect rows); the CO2 family predominantly —
not exclusively — uses `Metric Tonne per Terajoule` (commercial plain-CO2
rows split 2,244 MT/TJ + 1,056 kg/TJ + 132 MT/MT; industry plain CO2 36,432
MT/TJ + 14,520 kg/TJ); process/mass-basis factors use `Kilogramme per Metric
Tonne`; SO2 uses LEAP's fuel-property formula in kg/kg —
`SulfurContent*(SO2/S)` (dominant form) or
`SulfurContent*(1-SulfurRetention)*(SO2/S)` / `*2` variants — referencing
fuel properties defined outside these exports. Oil-product CO2 uses
`20 * FractionOxidized * (CO2/C)`.

**Biogenic convention**: combustible fuel leaves carry both CO2 leaves;
biofuels put the factor on `Carbon Dioxide Biogenic` with plain CO2 = 0 (or
no plain-CO2 leaf), fossil fuels author `Biogenic = 0` explicitly. Per-fuel
factor values match across sectors where the same fuel appears (e.g.
Biodiesel Biogenic 74.1 in both commercial and transport) — the EF tables
appear copy-pasted from one source library.

Coverage varies by fuel: e.g. residential `Historical\Electricity` and
`Historical\Solar Heating` have no pollutant children; the other 12
Historical fuels have 13 each except Bagasse and Natural Gas with 12. In
commercial, the reduced 7-species set applies only to the End Use Projection
kerosene leaves — `Historical\Kerosene` and `Kerosene and Candles` carry the
full 13.

**Transport gap**: the `Road` subtree has **zero** pollutant leaves, while
Air / Inland Waterways / Rail carry full 12–13-pollutant sets. Road tailpipe
emissions are either computed elsewhere or missing — worth verifying before
any emissions accounting that uses this export.

---

## 7. Naming conventions

- **User-defined variables are no-space CamelCase**: `RefHH`, `TotalEnergy` /
  `TotalEnergyRes` / `TotalEnergyTran`, `UnscaledFuelShare`, `BulbsPerHH`,
  `FanHH`, `TVHH`, `ACHH`, `LightingHours`, `TotShare_AltFuels`,
  `Share_FossilFuels`.
- **`RefHH`** (unit `Ref/hh`, constant 1) is boilerplate on every
  category/technology branch — 8,844 / 7,392 / 15,312 / 79,200 rows on 67 /
  56 / 116 / 600 branches (comm/trans/res/ind). It never carries information;
  neither does `Demand Cost`, which is a constant 0 on ~100% of its rows in
  every sector (the one exception: 270 residential Refrigeration_ Interp
  rows in exactly 3 scenarios — Baseline, AMS Target, RAS test).
- **Trailing underscore = collision-avoidance rename** against an existing
  LEAP name — on variables (`Commercial Fuel Share_`, `Commercial Cooking
  Efficiency_`) and branches (`Air Conditioning_`, `Refrigeration_` — the
  residential device-stock twins of the share-based `Air Conditioning` /
  `Refrigeration`; also `Key\Industry\Cal\Total_`, `Key\Residential end use
  data_`).
- One variable has a leading bang: residential `!EER` (Btu/Wh AC efficiency,
  referenced as `0.7*Current_Sales Average:!EER[Btu/Wh]`) — a path-matching
  hazard for tooling.
- Efficiency-tier leaf suffixes recur: `Low_eff / Mid_eff / High_eff`,
  `Best Practice`, `Current Sales_Average`, `Current Stock_Average`, size
  tiers `Small / Medium / Large`.
- 180 transport rows self-reference `Demand\Transport_\Inland Waterways\…`
  (trailing underscore on the sector root) while every exported branch path
  roots at `Demand\Transport`. Nothing is flagged `!Missing Branch!`, so the
  reference resolves — consistent with the live LEAP branch being named
  `Transport_` and the export label being cleaned (unverifiable offline;
  check in the LEAP UI before relying on either name for injects).

---

## 8. Commercial

89,940 rows across 426 branches / 13 variables (695 (branch,variable)
combos). Activity driver: gross floor area.

### 8.1 Tree shape

Max depth 8. Depth census: L2=1, L3=2, L4=5, L5=21, L6=196, L7=188, L8=13.

| Level | Meaning | Example |
|---|---|---|
| 2 | Sector root | `Demand\Commercial` (Activity Level = `Key\Commercial\Gross Floor_Area[Thousand m2]`) |
| 3 | Sub-sector split | `Data_Center`, `Other Commercial` |
| 4 | DC classes / era split | `Data_Center\{Colocation, Enterprise, Hyperscale}`; `Other Commercial\{End Use Projection, Historical}` |
| 5 | End uses (6) + Historical fuels (15) | `…\End Use Projection\Air Conditioning`; `…\Historical\Electricity` |
| 6 | Tech/fuel leaves + pollutants under Historical fuels | `…\Air Conditioning\Best Practice`; `…\Historical\Wood\Methane` |
| 7–8 | Lighting tech sub-leaves + pollutant leaves under end-use fuels | `…\Lighting\Electricity\LED`; `…\Lighting\Other\Kerosene and Candles\Ammonia` |

Branch typology: 359 pollutant leaves, 52 technology/fuel leaves (Final
Energy Intensity + a fuel-share variable, Load Shape on electric ones), 12
category branches (Activity Level without FEI), 3 data-center leaves
(`Total Energy` GWh + Load Shape, no activity×intensity chain).

The six end uses under `Other Commercial\End Use Projection`: **Air
Conditioning** (Best Practice / Current Sales_Average / Current
Stock_Average / Efficient — efficiency-class stock split), **Cooking and
Food Processing** (9 fuel techs incl. Induction Electric and — taxonomically
odd — Solar Heating), **Lighting** (Electricity → CFL / Fluorescent /
Halogen / Incandescent / LED; Other → Kerosene and Candles, Solar Lighting),
**Other** (10 fuels), **Refrigeration** (Efficient / Existing), **Water
Heating** (Existing / Heat Pump / Heat Pump Outside Air / Solar Heating).
`Other Commercial\Historical` holds 15 flat fuel branches, including
Briquette, Ethanol, Gasoline which have no forward counterpart.

### 8.2 Variables

| Variable | Rows | Branches | Units (top) | Kind | Dominant idiom |
|---|---|---|---|---|---|
| Avg Environmental Loading | 47,388 | 359 | kg/TJ; kg/t; t/TJ; kg/kg | built-in | numeric EF + `?a`/`?b` tag; SO2 `SulfurContent*(SO2/S)` |
| Demand Cost | 8,844 | 67 | 2020 USD/m2 | built-in | **all 8,844 rows are `0`** |
| RefHH | 8,844 | 67 | Ref/hh | custom | all rows `1` |
| Final Energy Intensity | 6,864 | 52 | kWh/m2 (4,620); Thousand TOE/m2 (2,112); Liter/m2 (132) | built-in | Cal-factor product (3,432); Exp/Ln shells (1,660) |
| Activity Level | 6,468 | 49 | % Share of m2 (5,016); % Saturation of m2 (1,056) | built-in | `0` / `InterpFSY` targets / `Remainder(100)` / `Step()` |
| Commercial Fuel Share_ | 4,092 | 31 | % | **custom** | `Value(…\Historical\<Fuel>:Fuel Share[% Share], 2022)` anchor (2,452) |
| Load Shape | 2,772 | 21 | Percent | built-in | `YearlyShape(<Country>_Hourly / AC_Residential_R# / DC_Normal)` (2,376); `ShapeFlat` (396) |
| Fuel Share | 1,980 | 15 | % Share | built-in | CA: historical Interp; non-CA: `100 * UnscaledFuelShare[%]/ Total(UnscaledFuelShare[%])` (1,800) |
| Commercial Cooking Efficiency_ | 1,188 | 9 | prcnt eff | **custom** | `ScenarioValue(Baseline Simulation) / Key\Annual EI Reduction\EI_Improvement_RAS_2:Activity Level[Factor]` (864) |
| Commercial Uncalibrated Energy Intensity | 792 | 6 | kWh/m2 | **custom** | flat constants — 630 rows tagged `? ACE temp value`; 72 `Growth()` rows, all in RAS test (`-1.2%` ×39, `-1.5%` ×11, `-5%` ×11, `-3%` ×11) |
| Total Energy | 396 | 3 | GWh | built-in (inference) | data-center Interp trajectories or 0 |
| UnscaledFuelShare | 180 | 15 | % | **custom** | `Fuel Share[% Share]` snapshot, CA-only |
| TotalEnergy | 132 | 1 | Thousand TOE | **custom** | historical `Interp(2005..2024)` per region |

### 8.3 Demand arithmetic (verbatim expressions, Indonesia/CA unless noted)

1. Sector activity: `Demand\Commercial:Activity Level` =
   `Key\Commercial\Gross Floor_Area[Thousand m2]`.
2. Era switch: `End Use Projection:Activity Level` = `Step(2005, 0, 2025,
   100)` mirrored by `Historical:Activity Level` = `Step(2005, 100, 2025, 0)`.
3. Historical intensity is a data identity: `Historical:Final Energy
   Intensity` = `TotalEnergy[Thousand TOE] / Total Activity[m2]`, split per
   fuel by `Historical\Electricity:Fuel Share` = `Interp(2005,54.675, …,
   2024,83.1388068388)`.
4. Forward intensity is calibrated per fuel: `Air Conditioning\Current
   Stock_Average:Final Energy Intensity` = `Air Conditioning:Commercial
   Uncalibrated Energy Intensity[kWh/m2] * Key\Cal\Commercial\Electricity:
   Activity Level[Factor]` (3,036 FEI rows across 12 `Key\Cal\Commercial\
   <Fuel>` factors).
5. Forward fuel shares anchor to the last historical year: `Cooking and Food
   Processing\LPG:Commercial Fuel Share_` = `Value(Demand\Commercial\Other
   Commercial\Historical\LPG:Fuel Share[% Share],  2022) / 100`.
6. Baseline Simulation re-authors Historical FEI as unfitted Exp/Ln
   price-GDP elasticity shells (see §5.2).

**Data centers bypass the chain**: `Data_Center:Activity Level` = `0`
everywhere; each class holds an authored `Total Energy` trajectory, authored
for exactly 6 regions (Indonesia, Malaysia, Philippines, Singapore, Thailand,
Vietnam), `0` for the rest, **identical in every scenario** — no policy lever
touches data-center demand.

### 8.4 Scenario logic

78 of 695 combos (11.2%) diverge across scenarios. Layers: Baseline vs CA =
360 cells, all in `Historical` (the regression swap + fuel-share
renormalisation); the six-clone policy bloc adds tech-share targets +
efficiency machinery (259 cells vs Baseline); RAS vs bloc = 166 cells, 100%
Activity Level (`InterpFSY(2050, 20) ? ATS assumption` → `InterpFSY(2050,
40) ? RAS assumption`); CNZ vs RAS = 92 cells, 100% Activity Level (e.g.
Best Practice `InterpFSY(2050, 90) ? CNS assumption`). The efficiency knob:
864 rows of `ScenarioValue(Baseline Simulation) / Key\Annual EI Reduction\
EI_Improvement_RAS_2:Activity Level[Factor]` on `Commercial Cooking
Efficiency_` — one Key branch divides baseline efficiency across 8 policy
scenarios. RAS test diverges from RAS by 366 cells (pre-computed numeric AC
stock-rollover S-curves, `Growth()` intensities, zeroed cooking
efficiencies) — a frozen earlier prototype.

### 8.5 Regional pattern

Heavily template-uniform: 582/695 combos have one expression across all
regions **in Current Accounts** (a strict all-scenario check gives 570 — 12
combos are region-uniform in CA but carry per-region overrides in non-CA
scenarios). Fully-regional combos are dominated by Load Shape (country hourly
shapes, AC climate zones). Country-cited overrides are sparse: `Commercial
Uncalibrated Energy Intensity` has real sourced values only for Brunei
(`119.40 ? BEI 2019`), Laos (ERIA), Malaysia (journal refs), Thailand
(`161.5 ? SEI WS2 value set`) — the other regions sit on the
`200 ? ACE temp value` template default.

---

## 9. Transport

60,096 rows across 165 branches / 24 variables (488 combos). The sector is
methodologically split in two.

### 9.1 Tree shape

Max depth 6. Four subsectors at depth 3:

| Subsector | Branches | Methodology |
|---|---|---|
| Domestic Air | 30 | intensity-per-GDP (fuels: Aviation Gasoline, Electricity, Hydrogen Fuel Cell, Jet Kerosene, SAF) |
| Inland Waterways | 69 | intensity-per-GDP (Biodiesel, Diesel, Electricity, Gasoline, Hydrogen Fuel Cell, Kerosene, Residual Fuel Oil) |
| Rail | 28 | intensity-per-GDP (Biodiesel, Diesel, Electricity; per-fuel Activity Level = 100 Saturation) |
| Road | 37 | **vehicle stock-turnover** (LEAP Transport analysis) |

- **Air / Waterways / Rail**: depth-3 category holds `Activity Level` (= GDP)
  + aggregate `Final Energy Intensity`; depth-4 fuel leaves carry FEI + Fuel
  Share; under them sit 109 pollutant leaves (12–13 species each).
- **Road**: depth-4 vehicle classes (Bus, `Motorcyle` [sic], PassengerCar,
  Truck) → depth-5 fuel/powertrain branches (16: Blended Diesel, Blended
  Gasoline, Electricity, Hydrogen, Natural Gas per class) carrying `Stock` /
  `Sales` / `Scrappage` / `First Sales Year` → depth-6 same-named device
  leaves carrying `Fuel Economy`, `Mileage`, `Device Share` etc. **Road has
  zero pollutant effect leaves in this export.**

### 9.2 Variables (the stock-model panel)

Beyond the §5 shared set: `Sales` (2,112 rows — every row the Key product
below), `Stock` / `First Sales Year` (192 rows each, CA-only), `Fuel Economy`
(2,112 — authored in `MPG Gasoline US eq.` for ALL powertrains including EV
and H2), `Mileage` (2,112 — flat per-region `Interp(2025, X, …, 2060, X)`
km), `Scrappage` / `Max Scrappage Fraction` / `Fraction of Scrapped Replaced`
(boilerplate 0/100/100), correction-factor and on-road variants (constants),
and user-defined helpers `TotalEnergyTran` (calibration total),
`TotShare_AltFuels`, `Share_FossilFuels` (CA-only).

Stock authoring: `Data(…)` historical registration series (112 rows), Key
stock-share formula (69 rows), constant `0` (11 rows). The Key-formula form
(`Vehicle_Stock_Share × BaseYear_StockData`) is used bare by Base Template
and Timor Leste, wrapped as `Interp(2005,0,2024, Key\…)` by Singapore, and
appears in scattered single branches of most other regions (Brunei 5, Laos 3,
Philippines 3, others 1–2).

### 9.3 Demand arithmetic

**(a) Intensity chain (Air/IW/Rail)** — CA reproduces statistics exactly,
scenarios freeze the endpoint:

- `Domestic Air:Activity Level` = `GDP[Million 2021 USD]`
- `Inland Waterways\Diesel:Final Energy Intensity` =
  `TotalEnergyTran[TOE]/Total Activity[USD]`
- `…\Diesel:TotalEnergyTran` = `Interp(2005, 26.33, …, 2022, 1.77)` →
  non-CA scenarios: `Growth(0)`
- `…\Diesel:Fuel Share` =
  `TotalEnergyTran[Thousand TOE]*100/Total(TotalEnergyTran[Thousand TOE])`

**(b) Stock-turnover chain (Road)** — fleet driven entirely by the
`Key\TransportDataStock` exogenous tree:

- `Road\Bus\Blended Diesel:Sales` = `Key\TransportDataStock\
  Vehicles_Sales_Share\Bus\Blended Diesel:Activity Level[%] / 100 *
  Key\TransportDataStock\Vehicle_Sales\Bus:Activity Level[Vehicle]`
- `Road\Bus\Blended Diesel:Stock` (CA, Indonesia) =
  `Data(2005,354061.579499, …, 2024,486074.791645)`
- Device energy = Stock × Mileage ÷ Fuel Economy; policy scenarios apply
  `Growth(Key\Annual EI Reduction\FuelEco:Activity Level[%])`.

### 9.4 Scenario logic

42 of 488 combos (8.6%) diverge. Equivalence classes: {Baseline ≡ RAS test},
{RAS ≡ LCO backup ≡ Set up ≡ RE LTRM ×3}, {AMS Target}, {CNZ}. AMS Target
sits 4 rows off RAS: Indonesia drops the SAF mandate (SAF Fuel Share → `0`,
Jet Kerosene → `100`), while Thailand and Malaysia keep SAF with altered
trajectories (Thailand `Interp(2024, 0, 2037, 12.43)`, Malaysia
`InterpFSY(2050, 47)`). CNZ sits 130 rows off RAS — aviation fuel shares
wired to `Key\Net Zero Measures\Transport\Aviation\*`, Domestic Air FEI =
`If(Year>2022, Growth(Key\…Aviation_efficiency:Activity Level[AGR]),
ScenarioValue(Regional Aspiration Scenario))`.

The SAF mandate is per-country policy authoring in the RAS bloc: Indonesia
`InterpFSY(2026, 1, 2060, 50)` (Ministerial Decree No. 8/2023 comment),
Malaysia `InterpFSY(2030, 15, 2050, 47)` (NETR), Thailand `InterpFSY(2026,
1, 2036, 8)` (AEDP); the other regions stay 0.

### 9.5 Regional pattern

431/488 combos (88%) region-uniform. 30 combos fully per-region (11 distinct
variants): `Mileage` 16, `Stock` 9, `Load Shape` 5. Two further `Motorcyle`
Stock combos reach 10 variants; 27 combos sit in between (mostly
`TotalEnergyTran`/FEI series that exist only for fuel-using regions). Base
Template and Timor Leste consistently hold template defaults (Mileage
`20000 ? IEEJ (2017), AEO7` vs per-country values like Indonesia 34,439 km).

---

## 10. Residential

146,544 rows across 530 branches / 35 variables (1,275 combos) — the most
variable-rich sector. Activity driver: households.

### 10.1 Tree shape

Max depth 7. Level 3 is the era split (`Historical` / `Projections`, Step
switch at 2025). `Historical` = 169 branches: 14 fuel-accounting branches
(Bagasse … Wood), each with Activity Level + FEI + custom `TotalEnergyRes`;
12 of the 14 have 12–13 pollutant children (Electricity and Solar Heating
have none; Bagasse and Natural Gas have 12, the rest 13). `Projections` =
360 branches: **15 end uses** — Air Conditioning, **Air Conditioning_**,
Clothes Dryer, Computer and Laptop, Cooking, Fan, Iron, Lighting, Other,
Refrigeration, **Refrigeration_**, Rice Cooker, TV, Washing Machine, Water
Heating. The trailing-underscore pairs are **parallel device-stock rebuilds**
of the share-based originals (see §10.5).

Category branches carry Activity Level as `Saturation %of Household`
(ownership) or `Share %of Household` (partitions closed by
`Remainder(100)` — 2,565 AL rows); 414 of 530 branches (78%) are pollutant
leaves (54,780 rows — 37% of the sector's export).

### 10.2 Variables

Built-ins as per §5, plus: `Efficiency` (4,620 rows — cooking/device tiers,
often `56*Key\Cal\Residential\LPG:Activity Level[Factor]`-style products that
silently absorb the calibration scaler, so the displayed % is not physical
efficiency), `Useful Energy Intensity` (1,188 — authored in 4 different
units across 9 branches: TOE / GJ / MJ / kWh per household), `End Year
Penetration` (1,980 — GDP-per-capita `Lookup` only on Air Conditioning), and
the **device-stock panel** on the 18 `AC_`/`Refrigeration_` `*_eff` tiers
(1,512 rows per variable; `Maximum Devices` and `Maximum Device Additions`
are the literal string `Unlimited`; `Interest Rate` is the bare symbol
`DiscountRate`; dominant `Lifetime` is **10** — 960 of 1,512 rows — with 12
on 372 Refrigeration_ rows and 15 on 180 AC_ rows, 60 per size class). `Optimize Devices`
sits on the 6 size-class parent branches (504 rows), split `Yes` 252 /
`No` 252.

Custom variables: `RefHH`, `Uncalibrated Final Intensity` (2,904, kWh/hh),
`TotalEnergyRes` (168, CA-only), `!EER` (528), `ACHH`, `TVHH`, `FanHH`,
`BulbsPerHH`, `LightingHours`, `Bulb Wattage`, `Residential Uncalibrated
Energy Intensity`.

Load Shape: 3,520 rows of `YearlyShape(<Country>_Hourly)`, 440 rows of the
three AC climate-zone shapes, 792 `ShapeFlat`.

### 10.3 Demand arithmetic (verbatim)

1. Root: `Demand\Residential:Activity Level` =
   `Key\Demographic\Households[Thousand household]`.
2. Historical calibration: `Historical\Electricity:Final Energy Intensity` =
   `TotalEnergyRes[TOE]/Total Activity[Household]`; scenarios: `Growth(0)`.
3. Useful-energy cooking: `Cooking\Clean:Activity Level` =
   `Key\Energy Access\Clean Cooking Access[%]`; UEI = `2.5 * Key\Demographic\
   Household Size:Activity Level[people/HH]*365 * 0.56 * Key\Cal\Residential\
   Cook and Light Non Elec:Activity Level[Factor]? … (World Energy Council
   WEC, 1999)`; leaf Efficiency = `56*Key\Cal\Residential\LPG:Activity
   Level[Factor] ? Malla & Timilsina; 2014 (World Bank)`.
4. Engineering bottom-up lighting: `Lighting\Electricity\LED:Final Energy
   Intensity` = `Electricity:BulbsPerHH[Bulbs] * Bulb Wattage[Watts] *
   (Electricity:LightingHours[Hours] * 365) * Key\Cal\Residential\
   Electricity:Activity Level[Factor] /1000`.
5. Device-stock chain (`Refrigeration_`, RAS): parent AL =
   `Key\Residential\Refrigeration\Percent Ownership[%]`; size AL =
   `Key\Residential\Refrigeration\Size_Share\Large[%]`; UEI from
   `Key\Residential\Refrigeration\Useful_EI\Large`; tier AL =
   `Data(2025, 50.31766, …, 2060, 100) ?Optimized on 07/02/2026 11:41
   (NEMO/CPLEX)` — **solver output written back into the authored
   expression** (360 such rows, RAS + CNZ only).
6. Net-Zero measure stack (AC, RAS): UEI = `ScenarioValue(AMS Target
   Scenario)* (1 - Key\Net Zero Measures\Residential\Reflective Coatings Cool
   Roofs\Energy Savings…) * (1 - …Programmable Thermostats…) * (1 -
   …Gamification…) * (1 - …Building Orientation\Cooling Energy Savings…)`.

The `Key\Cal\Residential\<Fuel>:Activity Level[Factor]` multiplier appears in
5,218 rows — threaded through nearly every intensity expression.

### 10.4 Scenario logic

225 of 1,275 combos (17.6%) diverge from CA; divergence concentrates in
`Refrigeration_` (78 combos) and `Air Conditioning_` (66). Mechanisms:
re-anchor + target (`InterpFSY(2024, ScenarioValue(Baseline Simulation),
2050, 50)`), `ScenarioValueOf(…, Baseline Simulation, 2024)` seeding of
Minimum Share (252 rows), Net-Zero multiplier stacks, NEMO/CPLEX `Data(…)`
writebacks, `Growth(0)` freezes. Scenario-scoped structure is the dominant
anatomy fact — see §2.1. Note the mirror image: 24 `Demand Cost` combos
exist **only** in the 4 scenarios *without* the device-stock panel — two
disjoint costing systems for the same appliances.

### 10.5 The paired old/new appliance trees (load-bearing quirk)

`Air Conditioning` vs `Air Conditioning_` and `Refrigeration` vs
`Refrigeration_` run in parallel: the old share-based trees keep non-zero
intensity in every projection scenario (e.g. `Refrigeration\High`
Uncalibrated Final Intensity = `557.089991745`), while the new device-stock
trees are active in 7 scenarios. Whether double counting is avoided depends
on the `Key\Residential\…\Percent Ownership` driver values, which live
outside this export — **unverified**; check the Key tree before trusting
residential totals.

---

## 11. Industry

1,008,012 rows across 5,859 branches — the deepest (10 levels) and widest
tree, but only 10 variables: a huge, homogeneous structure.

### 11.1 Tree shape

Level 3 splits `Historical` / `Projection` (Step switch at 2025, §5.1).
Level 4: 28 Historical fuel branches + `Projection\End Use` +
`Projection\Electricity Appliances`.

| Depth | Count | Content |
|---|---|---|
| 5 | 350 | 331 Historical pollutant leaves + 10 End Use subsectors + 9 Electricity Appliances subsectors |
| 6 | 29 | process nodes (`Cement\Clinker`, `<subsector>\Direct/Indirect Process Heating`, `Iron and Steel\Casting/Crude Steel/Hot Rolling`) + 9 EA `Electricity` leaves |
| 7 | 59 | technology nodes (`Cement Kiln CCS/Conventional`, `Oxyfuel Biomass/Gas CCS`, `BOF`, `EAF`) or carrier groups (`Electricity`, `Liquid FF`, `Others`) |
| 8 | 456 | 400 fuel leaves (16 with Load Shape) + 12 cement-technology Activity+FEI nodes + 5 steel-route nodes (`BF`, `BF CCS`, `DRI`, `DRI H2`, `Scrap`) + 39 pollutant leaves |
| 9 | 4,635 | 4,592 pollutant leaves + 43 deep fuel leaves (cement/steel chains) |
| 10 | 297 | pollutant leaves only (Cement 163, Iron and Steel 134) |

**End Use subsectors (10)**: Cement, Chemical, Construction, Food Beverages
and Tobacco, Iron and Steel, Mining, Other Industry, Other Non Metallic
Minerals, Pulp and Paper, Textile and Leather. All except Cement and Iron
and Steel use the uniform `Direct/Indirect Process Heating` ×
`Electricity`/`Liquid FF`/`Others` pattern. Cement gets a physical-production
chain (`Cement\Clinker\<4 kiln techs>\Heat|Electricity|Non Energy\<fuel>`);
Iron and Steel gets `Crude Steel\BOF{BF, BF CCS} | EAF{Scrap, DRI, DRI H2}`
plus `Casting` and `Hot Rolling`. Deepest representative path:
`Demand\Industry\Projection\End Use\Cement\Clinker\Cement Kiln CCS\Heat\Coal
Bituminous\Sequestered Carbon Dioxide`.

**Electricity Appliances** (9 subsectors) is a parallel accounting tree:
each `<subsector>\Electricity` leaf carries a custom `Total Energy` reading
back the End Use **result**: `Key\Industry\Appliances_share\Iron and Steel:
Activity Level[Fraction] * Demand\Industry\Projection\End Use\Iron and
Steel:Final Energy Demand[GJ]` — apparently to attach hourly load shapes to
the electric-appliance share of demand. A result-feedback idiom that could
create calculation-order sensitivity.

Branch typology: 5,259 pollutant leaves, 448 fuel leaves (FEI + Fuel Share),
89 carrier-group intensity branches (AL + FEI, no Fuel Share), 54 category
branches, 9 `Total Energy` leaves.

### 11.2 Demand arithmetic

**Historical (2005–2024)**: `Historical:Final Energy Intensity` =
`TotalEnergy[Thousand TOE]` (per-region Interp of total industry FEC); the
28 fuel children split it via per-region `Fuel Share` Interp series. The
per-fuel FEI series on fuel branches (Thousand TOE) look like parked
consumption data, not an operative intensity; scenario overrides on them
(the broken templates below) are likely inert because Historical activity is
Step()'d to 0 from 2025.

**Projection (2025+)**:
1. `Projection\End Use:Activity Level` = `Key\Macroeconomic\Real GDP
   Industry[Million 2021 USD]`.
2. Subsector share (CA): `Key\Industry\Subsector_share\Chemical[Share] *
   Key\Macroeconomic\Real GDP Industry[Million 2021 USD]`; Iron and Steel
   and Cement instead use physical activity (per-country `Interp` in Million
   / Thousand Metric Tonne).
3. Technology shares: `EAF:Activity Level = Remainder(100)`; RAS/CNZ e.g.
   `DRI H2 = (100-Scrap[% Share])*Key\Industry\Steel RAS Measures\EAF\
   Hydrogen Adoption Rate[% Share]/100`.
4. Carrier-group intensity: `Final Energy Intensity = Key\Industry\Intensity\
   Chemical\Direct Process Heating\Electricity:Activity Level[GJ/USD] *
   Key\Industry\Cal\Electricity:Activity Level[Fraction]` — exogenous Key
   trajectory × calibration anchor. Cement analogue is per-tonne.
5. Fuel split at leaves: constants, Interp trajectories, or
   `Remainder(100)` closure (e.g. cement kiln Heat: Biomass 6.71 / Natural
   Gas 18.25 / MSW 1.53 / RFO 3.56 / Coal Bituminous `Remainder(100)`).
6. Emissions: constant factors (`94.6 ?a` t CO2/TJ on Coal Bituminous); CCS
   branches carry negative `Sequestered Carbon Dioxide` with the
   `-112 * Interp(2030,0.8,2045,0.9,2055,0.95) ?placeholder` capture ramp.

### 11.3 Scenario logic

97 of 7,661 combos diverge (FEI 67, Activity Level 19, Fuel Share 10,
TotalEnergy 1). Bloc structure per §2. Mechanisms:

- **Activity switch**: CA's statistical Interp / `Subsector_share × GDP` is
  replaced in every non-CA scenario by `GrowthAs(Key\Macroeconomic\Real GDP
  Industry)` (1,440 rows).
- **Decarbonization measures (CNZ + RAS only)**: tech shares from
  `Key\Industry\Steel RAS Measures\…` and `Cement RAS Measures\…` (e.g.
  `Oxyfuel Gas CCS = InterpFSY(2030,0,2035,0.5,2040,3,2045,8,2050,13,
  2055,17,2060,20)`), plus cement heat fuel-share trajectories eroding the
  coal `Remainder(100)`.
- **Broken EI-reduction template**: 10 non-CA scenarios hold
  `InterpFSY(!Missing Branch (ID=3477)!, ScenarioValue(Bad Scenario [2],
  !Missing Branch (ID=3477)!) * (1-(!Missing Branch (ID=3478)!/100)))
  ? Reduction in energy consumption relative to BAU` — a
  ScenarioValue(BAU)×(1−reduction%) idiom whose branch AND scenario
  references all dangle.
- **RAS test = frozen snapshots with a live multiplier**: all 360 diverging
  DPH/IPH FEI keys in RAS test hold `Interp(<frozen numerics>) *
  Key\Industry\Cal\Total_:Activity Level[Fraction]` — region-uniform numeric
  snapshots that still retain the Cal-tree multiplier. **Singapore** holds
  such frozen numerics in 9 of the 10 non-CA scenarios (40 DPH/IPH branches
  each; 30 in RAS test) — Baseline Simulation retains the CA Key formula for
  Singapore — making it the only region where the LTRM family diverges on
  DPH/IPH intensities.

### 11.4 Regional pattern

98.9% of combos (7,579/7,661) region-uniform — the projection engine
(intensities, tech shares, measures) is authored once for all 12 regions.
Only 41 combos vary in all 11 real regions: 37 Load Shape + `Historical:
TotalEnergy` + `Historical\Diesel:Fuel Share` + `Historical\Electricity:
Fuel Share` + `End Use\Cement:Activity Level`. Genuine per-country data
lives almost exclusively in Historical fuel shares/totals, cement/steel
physical activity, and load shapes.

---

## 12. The `Key\` assumption tree

`LEAP Input Keys.xlsx` — 440,220 rows, 1,064 branches, 26 variables, max
depth 8. Same 11-scenario / 12-region roster. Unlike every demand sector the
export is **perfectly rectangular**: 3,335 (branch, variable) combos × 12
regions × 11 scenarios, zero scenario-scoped rows — no CA-extra calibration
fingerprint; scenario differentiation lives purely in the Expression column.
Structural caveat: only variable-carrying branches export (depth census
{2:1, 3:607, 4:252, 5:117, 6:64, 8:23} — depth-8 leaves with no depth-7 rows,
so pure container nodes are absent; inference from the gap).

### 12.1 Tree shape — 25 top-level groups in three strata

| Stratum | Group (branches / rows) | What it holds |
|---|---|---|
| **NEMO plumbing** (538 br, 370,260 rows = 84.1%) | `Optimized Trade` (495 / 326,700) | 55 region-pairs (C(11,2) over 10 AMS + Timor Leste) × 9 feedstock fuels (Ethanol, Biodiesel, Coconut Oil, Palm Oil, Palm Oil Mill Effluent, Cassava, Molasses, Sugarcane, Corn) — exactly the §A.12 trade-route fuel list. 5-variable panel per branch. |
| | `Transmission` (42 / 43,032) | 21 `Lines\<A>_<B>_{E,F,C}` interconnectors (13-variable panel: From/To Node, Maximum Flow MW, Capital/Fixed/Variable OM Cost, Lifetime, Efficiency, plus deactivated `!Reactance`, `!Construction Year`), 10 `Nodes\<AMS>`, 10 `Demand Distribution\<AMS>`, 1 `Transmission Enabled\Electricity_`. Sub-national node names (P. Malaysia, Sarawak, Sabah, Sumatra, Kalimantan) appear only here. |
| | `Region Group RE Targets` (1 / 528) | 4-variable stub, every expression `0` — RE-target plumbing present but disabled. |
| **Sector data trees** (450 br) | `Industry` (113) | `Intensity` 84 leaves (fuel-level GJ/USD & GJ/t trajectories incl. BF/BF CCS/DRI/EAF steel routes), `Subsector_share` 9, `Appliances_share` 8, `Cal` 6, `Steel/Cement RAS Measures` 6. |
| | `Cal` (76) | Per-fuel calibration factors: `Industry` 27, `Commercial` 13, `Residential` 13, **`Transformation` 13, `Transport` 10** — the latter two invisible to the demand exports. |
| | `Residential end use data_` (54) | 9 appliances × {Historical <X>, a, b, c, number of appliances, year_} regression-coefficient + historical-count panels. |
| | `TransportDataStock` (47) | `Vehicle_Stock_Share` 17, `Vehicles_Sales_Share` 17, `Vehicle_Sales` 4, `BaseYear_StockData` 4, `Effective Operational_Stock` 4, `Year_` 1. |
| | `Residential` (32) | AC + Refrigeration driver trees: `Percent Ownership`, `Size_Share`, `Efficiency_Share`, `Useful_EI`. |
| | `Transport vehicle data_` (28), `Other Transport` (23 — EV charging-infrastructure cost stack for AC L1/L2/DC), `Macroeconomic` (17), `Commercial` (13), `Demographic` (8), `ValueAdded` (4), `Energy Access` (2), `Lighting_data` (2) | Exogenous spine + sector data. |
| | `Job creations` (22), `Emission Externality Costs` (9) | Results-side factors: jobs/MW + declining factors for Solar/Wind/Hydro/Geothermal; $/kg externality prices for 9 pollutants. |
| **Policy levers** (≈75 br) | `Net Zero Measures` (31: Transport 12, Industry 10, Residential 9), `Annual EI Reduction` (13), `Capacity Additions Multiplier` (11), `Biofuel Blending Targets` (2), `End_cap multip` (2), `Modeling Assumptions` (16: technology Lead Times + `Incumbent Generator DIspatch Phaseout` [sic]) | The scenario-differentiation layer (§12.4). |
| **Scratch** | `Temp` (1 / 132) | Unit-conversion scratch, units literally `temp` — and scenario-divergent (§12.7). |

### 12.2 Variables — 26, but really 1 + plumbing

`Activity Level` is the only "assumption" variable: 140,448 rows on **all
1,064 branches**. The other 25 exist solely on plumbing meta-trees: the
4-column trade panel (`Trade Region 1/2`, `Trade LEAP Fuel`, `Trade_NEMO
Fuel` — 65,340 rows each on the 495 Optimized Trade branches), 12 extra
transmission-line variables (2,772 rows each on 21 Lines), `Region_` /
`Node_` / `Fuel_` on Nodes/Demand Distribution, `Unscaled VAShare` (528 rows
/ 4 ValueAdded branches), and 5 singleton config variables (`Fuel___`,
`Transmission Modeling Type`, `Region Group Set`, `Region Group Set Element`,
`Fuel_RE Target`) — 1 + 4 + 12 + 3 + 1 + 5 = 26. Panel census: 522 branches
carry exactly 1 variable, 495 carry 5, 21 carry 13, 26 carry 2–4.

A Key branch is the inverse of a demand-tech branch: demand branches carry
fat variable panels; Key branches carry one `Activity Level` whose **unit
does the typing** (`%`, `GJ/USD`, `coeff`, `Vehicle`, `fraction`, `1 or 0`,
`ID`…). 62.9% of all rows (276,804) are ID-typed plumbing (`RegionID()` /
`FuelID()` / `BranchID()` — 132,000 / 69,564 / 6,864 rows). Activity Level
expression classes: `0` 74,905; `1` 20,846; `Interp` 14,505; other constants
14,485; `Growth` 5,962; `Data` 2,582; `RegionValue` 847; `Mean` 506;
`PrevYearValue` 440; `If` 319; `ScenarioValue` 288.

### 12.3 Consumption map — three quarters of the tree is invisible to the six exports

The four demand sectors cite 241 distinct `Key\` branches, 239 of which
exist here (the 2 misses are comment-only, §12.6), with 51,917
reference-rows: Industry 112 branches / 22,208 refs, Cal 25 / 8,518,
Macroeconomic 5 / 6,921, TransportDataStock 39 / 4,362, Residential 28 /
3,036, Energy Access 2 / 2,496, Net Zero Measures 13 / 1,952, Annual EI
Reduction 2 / 1,536, Demographic 2 / 396, Commercial 1 / 264, Residential
end use data_ 10 / 228. Internal Key→Key references add 38 distinct paths
(16,142 occurrences — the industry-EI engine `Growth(Key\Annual EI
Reduction\Industry…)` alone is 5,952 rows). The Resources export contains
**zero** `Key\` references.

Net: **271 of 1,064 branches (25.5%) are referenced somewhere in the six
exports; 793 (74.5%) are not.** The unreferenced census is dominated by
branches consumed outside the exported trees (Transformation processes,
results screens, plug-ins — labelled inference): Optimized Trade 495,
Transmission 32, Cal\Transformation 13 + Cal\Transport 10 + Cal\Industry 27,
Transport vehicle data_ 28, Job creations 22, Modeling Assumptions 16 (the
`Incumbent Generator DIspatch Phaseout` knob is consumed by Transformation
Minimum Utilization formulas per CLAUDE.md §11.2c), Capacity Additions
Multiplier 11, Emission Externality Costs 9, Other Transport 17, Net Zero
Measures 17, Residential end use data_ 44. Caveat: reference extraction
scans full expression text including `?` comments, so "referenced" is an
upper bound on live consumption (proven by §12.6).

### 12.4 Scenario logic — the RE LTRM triplet differs HERE

694 of 3,335 combos (20.8%) carry ≥2 distinct expressions across scenarios.
Divergence-from-CA: CNZ 694 combos, RAS 671, LCO backup 171, RE LTRM ×3 /
Set up 169, AMS Target 167, Baseline / RAS test 70. Full 11×11 pairwise diff
matrix over the 40,020 (branch, variable, region) cells:

- **`Set up` ≡ `RE LTRM Policy Aligned`** (0 diffs). The demand-side
  six-name bloc breaks apart here: AMS Target sits 86 cells off Set up,
  **LCO backup 273 off** (Annual EI Reduction 132, Capacity Additions
  Multiplier 129, Clean Cooking 12).
- **The RE LTRM triplet is NOT identical** — the first divergence found in
  any of the six exports: Policy Aligned vs RE Coupling 11 cells, vs Shared
  Energy Resources 12, Coupling vs Shared 1. The differing cells:
  (a) `Key\Biofuel Blending Targets\{Biodiesel, Bioethanol}` for
  Indonesia/Philippines/Thailand/Vietnam — Coupling/Shared insert a 2030
  intermediate blend point absent from Policy Aligned (e.g. Indonesia
  Biodiesel `InterpFSY(2023, 35, 2025, 40, 2050, 50)` → `…2030, 45…`, tagged
  `MRK Comment: 2030 is assumption set by the modeller`); (b) `Key\Annual EI
  Reduction\Industry` for Indonesia/Thailand/Vietnam (−0.01 or 0 → −0.015);
  (c) the single Coupling-vs-Shared diff is the scratch branch `Key\Temp`.
- **`Baseline Simulation` ≡ `RAS test`** (0 diffs); both sit 661 cells off
  CA (Residential 320, TransportDataStock 213, ValueAdded 84).
- **RAS and CNZ are the outliers**: 7,794 / 8,057 cells off CA, only 303
  apart from each other (Net Zero Measures 265 + EI Improvement_RAS 12 +
  Clean Cooking 12 + Biofuel Blending 13 + Modeling Assumptions 1) —
  confirming CNZ = RAS + Net-Zero-Measures overlay.
- **`Key\Optimized Trade\*:Activity Level` is a per-scenario master switch:
  `1` in RAS and CNZ only, `0` in the other nine scenarios** (5,940 rows
  each; all 495 routes flip as one block). Given §A.12 (blend mandates need
  trade routes), note the RE LTRM triplet and AMS Target carry non-zero
  biofuel blend targets with trade routes disabled — whether that is an
  infeasibility risk depends on Transformation-side wiring not visible in
  these exports (hypothesis, not verified).

### 12.5 Regional pattern

91.5% of combos (3,053/3,335) are region-invariant in every scenario.
Genuinely per-region trees: Cal (65/76 combos vary), TransportDataStock
(40/47), Residential (32/32), Transport vehicle data_ (23/28), Commercial
(12/13), Demographic (6/8 — was 7/8 until `Households` went region-uniform
`Population / Household Size` in v0.69_beta, 2026-07-06), Macroeconomic
(10/17), Energy Access (2/2).
Fully 12-way differentiated: Population, Urbanization Rate, Average Income,
GDP sector fractions, commercial energy-per-area, vehicle sales/stock
shares. The policy-lever and plumbing layers are template-uniform (Optimized
Trade, Job creations, Emission Externality Costs: **zero** regional
variation). `RegionValue()` borrowing (847 rows) marks data-poor regions:
Cambodia and Vietnam (132 rows each), Philippines 121, Laos 99. Timor Leste
is better-authored here than on the demand side — real `Interp` series for
Population, GDP PPP, Electrification Rate; TL diverges from Base Template in
~56 CA combos (vs Indonesia's ~161), spread across TransportDataStock 21,
Commercial 11, Macroeconomic 8, Residential end use data_ 6, Demographic 5,
Energy Access 2, Lighting_data 2, Industry 1.

### 12.6 The missing `Key\Residential\AC\{a,b}` — solved: comment-only citations

No branch under `Key\Residential\AC` exists in this export. The 116
residential rows citing each of `\AC\a` and `\AC\b` are all on ONE branch —
`Demand\Residential\Projections\Air Conditioning:Activity Level` — and in
**all 116 rows the citation sits after the `?`**, inside the comment: the
live expression is a `Lookup(Linear, ~Key\Macroeconomic\Real GDP Per
Capita…)` curve; the comment preserves the retired AEO7 regression
`(GDP/cap × b[coeff]) + a[coeff]`. Comment text is never resolved by LEAP,
which is why no `!Missing Branch!` marker appears. Conclusion: **not a
dangling live reference and not a partial-export artifact — a stale
provenance comment naming branches that don't exist in the area** (whether
they once existed cannot be determined offline). Note the near-namesake
panels `Key\Residential end use data_\AC\{a,b}` DO exist in this export but
are themselves **entirely uncited** — residential's 132 live references to
that subtree hit `\AC\number of appliances` (120 rows) and `\AC\Historical
AC` (12 rows) only.

### 12.7 Quirks & hygiene

Clean on the big hazards: **0** `!Missing Branch`, **0** `Bad Scenario`,
**0** `Bad Unit`, **0** `Unlimited` anywhere in the Key tree. The rest:
`_x000D_` CR artifacts (583 rows on 17 branches); placeholder confessions
(`Household Size` = `Interp(2040, 4) ? placeholder based on discussion`;
Transmission Lifetime `80 ? too long for a lifetime?`); deactivated
variables exported with `!` prefix (`!Reactance`, `!Construction Year`,
2,772 rows each); the `Key\Temp` scratch branch carrying live scenario
signal (§12.4); naming hazards (17 trailing-`_` branches, 42 single-letter
`a`/`b`/`c` leaves, colliding near-duplicates `Key\Residential` vs
`Key\Residential end use data_` and `Key\Cal\Industry` [27 br] vs
`Key\Industry\Cal` [6 br]); typos `Incumbent Generator DIspatch Phaseout`
(capital "DI" — case-sensitive FullName lookups miss) and `Metalurgical
Coke`; unit-vocabulary drift (`Fraction`/`fraction`/`Factor`/`factor`,
`years`/`year`/`yr`); a second comment dialect `~~MRK Comment:~…` on the
RE-Coupling/Shared biofuel rows.

**Inject-relevance (§A.20):** this is the KA tree where blind mode is
mandatory. Rectangularity means every (branch, variable) exists in all 11
scenarios — a canonical without a `scenario` column hits all of them; the
Optimized Trade master switch and the policy-lever groups are exactly where
per-scenario filter-routing matters.

---

## 13. The `Resources\` supply tree

`LEAP Input Resources.xlsx` — 113,760 rows, 62 branches, 20 variables. This
is the tree the repo's `inject/bioenergy` and `inject/fossil` domains author
into, and where the §A.11 `Unlimited → 1e12` landmines live.

### 13.1 Tree shape — a completely flat, fully-materialised grid

Every branch is a depth-3 leaf (`Resources\Primary\<Fuel>` or
`Resources\Secondary\<Fuel>`); no branch has children. Every fuel carries
the same 15-variable base panel, materialised for all 12 regions.

**Primary (29 fuels)** by panel variant:

| Panel | Fuels |
|---|---|
| 18 vars (base + `Base Year Reserves`, `Additions to Reserves`, `Export Load Shape`) | Coal Anthracite, Coal Bituminous, Coal Lignite, Coal Sub bituminous, Coal Unspecified, Crude Oil, Natural Gas, Natural Gas Liquids |
| 17 (base + reserves pair, no Export Load Shape) | Nuclear |
| 17 (base + `Area Harvested`, `Crop Yield`) | Cassava, Coconut Oil, Corn, Palm Oil, Sugarcane |
| base 15 | Arable, Perennial (the §2.4 land-as-fuel pair), Bagasse, Biomass, Molasses, Palm Oil Mill Effluent, Municipal Solid Waste, Wood, Geothermal, Large Hydro, Small Hydro, Solar, Wind, Tidal, Wave |

**Secondary (33 fuels):** 28 carry 16 vars (base + `Export Load Shape`); 5
carry the base 15 (Blast Furnace Gas, CNG, Coke Oven Gas, Hard Coal
Briquettes, `Metalurgical Coke` [sic]). Roster: Ammonia, Avgas, Biodiesel,
Biomethane, Bitumen, Blast Furnace Gas, Blended Diesel, Blended Gasoline,
CNG, Charcoal, Coke Oven Gas, Diesel, Domestic Biogas, Electricity, Ethanol,
Gasoline, Hard Coal Briquettes, Hydrogen, Jet Kerosene, Kerosene, LNG, LPG,
Lubricants, Metalurgical Coke, Methanol, Naphtha, Oil, Petroleum Coke,
Refinery Feedstocks, Refinery Gas, Renewable Diesel, Residual Fuel Oil,
Sustainable Aviation Fuel.

### 13.2 Variables — 20, in four functional classes

| Class | Variable | Reality in this area |
|---|---|---|
| Supply caps (upper) | `Maximum Production` | The §A.11 headline (§13.3). Units per fuel: Gigajoule 44 (incl. Arable, at `Thousand` scale), TWh 8 (renewables/biomass), Metric Tonne 7 (5 crops + Molasses + POME — raw-crop-tonnes convention), PJ 1 (Crude Oil), Thousand TOE 1 (Municipal Solid Waste), Cubic Meter 1 (Perennial) |
| Supply caps (upper) | `Maximum Imports` | Exists only in the 7 optimization-bloc scenarios (§13.5). `Unlimited` on 42 fuels × 12 regions; all-zero on 13 non-tradables; `Max(<floor>, Maximum Production[Tonne]/1000)` on 6 fuels (the 4 traded crops + Biomass and Wood, 24 rows each); Domestic Biogas carries 7 non-zero historical Interp rows |
| Lower bounds | `Minimum Production` | Literal `0` in all 8,184 rows — clean |
| Lower bounds | `Minimum Imports` | Optimization bloc only. `0` in 4,410 rows; 798 rows carry historical Interp trajectories — 665 end `…, 2022, V` with V>0 (§13.6) |
| Accounting | `Unmet Requirements` = `MeetWithImports` (all 8,184); `Export Load Shape` = `ShapeFlat` (all 4,752); `Imports`/`Exports` historical series; `Cost of Unmet Requirements` = `0` (all 2,976) |
| Costs | `Production Cost`, `Import Cost`, `Export Benefit`, 4 Consumer Prices (§13.4) |
| Reserves | `Base Year Reserves` (CA-only, 9 fossil branches, all `0`), `Additions to Reserves` (293 non-zero Data() rows, EIA/national statistics) |
| Crop physicals | `Area Harvested` (Thousand ha), `Crop Yield` (t/ha) on the 5 crop branches |

Derivation idioms on `Maximum Production`: `Area Harvested[Thousand ha] *
1000 * Crop Yield[t/ha]` (448 rows — the 4 CSV-authored crops across
regions); cross-branch pulls (`Biomass:Maximum Production[TWh]` on Bagasse
and Wood, `Large Hydro:… *10%` on Small Hydro, Sugarcane-ratio on Molasses —
326 rows); Indonesia + Philippines Geothermal derived from `Transformation\
Centralized Electricity Generation\Processes\Geothermal Flash_*:Maximum
Availability` (18 rows).

### 13.3 The §A.11 Unlimited audit (headline)

**9,199 rows evaluate to literal `Unlimited`** after stripping `?`-comments
(9,051 bare + 148 commented like `Unlimited ? tbc`). Split: **5,671 on
`Maximum Production`, 3,528 on `Maximum Imports` — zero on any lower-bound
variable.** `Minimum Production` is literally `0` everywhere and `Minimum
Imports` never carries it. Every Unlimited in this tree is the benign-ish
upper-bound flavour of §A.11 (silent-parse / LP-conditioning risk, not a
forced 1e12 floor).

**Current Accounts:** 44 of 62 fuels are Unlimited in all 12 regions — 13
Primary (all 5 coals, Crude Oil, Natural Gas, NGL, Nuclear, Corn, MSW,
Tidal, Wave) + 31 of 33 Secondary. Only 7 fuels carry zero Unlimited in CA:
Cassava, Coconut Oil, Palm Oil, Sugarcane, Small Hydro, and Secondary
Diesel + Kerosene (authored `0`).

**Regional Aspiration Scenario (the optimized target): 505 Unlimited
`Maximum Production` rows remain.** 39 fuels still Unlimited in all 12
regions — **including `Resources\Primary\Natural Gas` and all five coals**,
plus Nuclear, NGL, MSW, Tidal, Wave and 28 Secondary pseudo-fuels
(Biodiesel, Ethanol, Blended Diesel/Gasoline, Hydrogen, LNG, Ammonia,
SAF, …). Fuels with ZERO Unlimited in RAS (9): Cassava, Coconut Oil, Palm
Oil, Sugarcane, and Secondary Diesel/Gasoline/Kerosene/LPG/Residual Fuel
Oil. Partials where mostly `Base Template` + `Timor Leste` remain Unlimited:
Crude Oil, Corn, Molasses, POME, Arable, Perennial, Solar, Wind, Large
Hydro (2 rows each), Biomass (9), Wood (5), Geothermal (3), Small
Hydro/Bagasse (1).

**Cross-reference with the repo canonicals** (read-only): the export matches
what `inject/bioenergy` + `inject/fossil` author, byte-exact where checked —
`Resources\Primary\Palm Oil:Maximum Production` (Indonesia, RAS) and
`Resources\Primary\Crude Oil:Maximum Production` (Indonesia, RAS, PJ) are
identical to their canonical rows. The canonicals author `Maximum
Production` on 13 fuels; of those, Corn, Molasses, POME and Crude Oil each
retain 2 Unlimited RAS rows (Base Template + Timor Leste), so the
RAS zero-Unlimited list is the 9 fuels above. **The fossil canonical
authors coal/NG costs but no `Maximum Production`** — which is why Natural
Gas and the coals are still Unlimited 12/12 in every scenario. Timor Leste
(§A.18): the four crops are zeroed via `Area Harvested = 0 × Crop Yield =
0` in RAS, but **Corn, Crude Oil and Natural Gas remain Unlimited for Timor
Leste in RAS** — moot while TL is disabled in the calc, a live §A.18 item if
re-enabled.

### 13.4 Cost layer

- **Production Cost** (8,184 rows): 2,114 literal `0`; the rest Interp
  trajectories, `Data()`, `Import Cost[…]` aliases (crude netback idiom),
  `ConvUnits` forms. Per-units vary by fuel (USD/Tonne, USD/bbl, USD/GJ,
  USD/MMBTU, USD/Liter); 1,320 rows use plain `U.S. Dollar` with no
  2020-USD base-year tag (1,056 per Metric Tonne + 264 per Million BTU) —
  unit-hygiene drift.
- **Import Cost** — the richest variable: ~2,820 pure-Interp cores (3,646
  Interp-prefixed), 810 `ConvUnits(<yr> usd, 2020 usd)` deflator chains, 143
  `RegionValue(<AMS>)` mirrors on the 4 crop fuels in 6 importing AMS —
  anchors split RegionValue(Thailand) 76 / Indonesia 38 / Malaysia 20 /
  Laos 9 — 662 cross-branch refs (e.g. `Coal Bituminous:Import Cost[2020
  USD/Tonne]`), and **312 rows of `0.001`** (Cassava, Ammonia, Blast Furnace
  Gas, Coke Oven Gas, Methanol) — near-zero placeholder pricing.
- **The §A.14(iii) 1.5899× mystery is resolved by this export**: fossil
  canonical Singapore Gasoline Import Cost `Interp(2024, 46.5, …)` in
  USD/100L displays here as `Interp(2024, 73.9304, …)` with `per=Barrel` —
  exactly ×1.5899 (158.99 L/bbl). Same trajectory, unit-converted on export;
  the inject landed correctly.
- **POME Import Cost** — the 2026-05-19 "final unlock" — is present in the
  area (`Interp(2025, 0.306, …, 2060, 0.377269)` 2020 USD/kg, RAS) but is
  **not in `inject/bioenergy/canonical_leap_inputs.csv`** (POME has only
  Maximum Production + Production Cost there) — the fix lives in the area
  outside the canonical: repo/area drift.
- **Companion-cost audit (POME lesson)**: in RAS, **191 of 744 (fuel,
  region) pairs have an open production route (`Maximum Production ≠ 0`)
  with `Production Cost = 0`** — 15 fuels, dominated by Secondary
  pseudo-fuels whose real cost sits on the Transformation process (probably
  intentional) — but Nuclear (Unlimited + $0) is the same shape that routed
  biodiesel to Timor Leste. Likewise **95 pairs have an open import route
  with `Import Cost = 0`**, including Arable/Perennial and Refinery
  Feedstocks/Refinery Gas/Renewable Diesel ×12.
- **Consumer Prices** (4 variants × 8,184 rows): 98.4% zero — 508 non-zero
  rows confined to Cambodia, Indonesia, Philippines, Thailand, mostly
  historical series ending 2017–2022. The demand-sector regressions
  reference Commercial/Industrial Consumer Price on 17 distinct Resources
  branches (27 refs, all resolve) — but for most referenced fuel/region
  pairs the price resolves to `0`. The demand-side `!Missing Branch`
  breakage (Ethanol/Biodiesel/Brown Coal Briquettes price refs) points at
  *demand-tree* Historical price branches, not these: `Resources\Secondary\
  Ethanol`/`Biodiesel` exist here (prices all 0), and Brown Coal Briquettes
  is not among the 62 Resources fuels at all.

### 13.5 Scenario + regional pattern

**The scenario axis splits the variable set** — unique among the six
exports: the 4 accounting scenarios (CA, Baseline, AMS Target, RAS test)
carry `Imports` + `Cost of Unmet Requirements`; the 7 optimization scenarios
(Set up, CNZ, LCO backup, RAS, RE LTRM ×3) instead carry `Minimum Imports` +
`Maximum Imports`. The Exports comment states the design: `0 ? NEMO
simulates exports in optimized scenarios`.

Expression blocs (pairwise byte-diffs on shared cells): `CNZ = RAS` (0
diffs); `Set up = LCO backup = RE LTRM Policy Aligned` (0); `Baseline = RAS
test` (0); AMS Target 6 cells off Baseline. RAS/CNZ differ from the Set-up
bloc by **553 cells** — Import Cost 193, Production Cost 136, Maximum
Production 105 on the crop + fossil branches: exactly the repo's inject
payload landing in RAS+CNZ only. **The RE LTRM triplet differentiates here
by 7 cells**: `Resources\Secondary\Ethanol:Import Cost`, where Policy
Aligned carries country-specific tariff multipliers/adders (`* 1.35`
Cambodia, `* 1.05` Laos/Myanmar, `* 1.01` Philippines, OECD-FAO adders for
Malaysia/Thailand/Vietnam) vs the flat CSIRO world price in RE Coupling =
Shared Energy Resources.

Scenario churn is low overall (102 of 994 combos diverge anywhere).
Regionally 817/994 combos are template-uniform; the most per-country
variables are `Area Harvested` (mean 9.0 distinct regions), `Crop Yield`
(8.2), `Import Cost` (4.0) — i.e. the inject-authored crop and fuel-price
layers.

### 13.6 Quirks & hygiene

1. **No Unlimited on lower bounds** — the critical §A.11 check: clean (§13.3).
2. **Minimum Imports hold-last floors**: 665 rows (95 fuel×region pairs × 7
   optimization scenarios) end `…, 2022, V` with V>0 — up to 53,538 kTOE
   (Singapore Residual Fuel Oil), 50,160 (Singapore Crude Oil), 47,230
   (Thailand Crude Oil). Under Interp hold-last-value these extend as forced
   import floors into projection years — plausibly intentional
   (refinery-hub feed) but the one live lower-bound-with-value class in the
   tree. No MinImports>0 with MaxImports=0 contradiction exists (0 cases).
3. **Arable/Perennial land-as-fuel** (intentional per §2.4 — not a bug):
   Arable cap `Interp(2025, 17782.90, 2060, 17782.90)` Thousand GJ
   (Indonesia; the 1 GJ/ha anchor ≈ 17.78 M ha) — but **Perennial's cap is
   unit-tagged `Cubic Meter`** (unit drift on the same anchor), and both
   carry `Maximum Imports = Unlimited` × 12 at `Import Cost = 0` in
   optimization scenarios — unlimited free "land imports" if trade routes
   for these pseudo-fuels are ever enabled (§A.12 watch-item; whether they
   flow to NEMO depends on `Key\Optimized Trade` config).
4. **Placeholders**: 95 `? tbc` + 50 `?~Former expression: …` comments, all
   on `Maximum Production` — the Former-expression rows record numeric caps
   (IRENA/ADB/CREZ) deliberately reverted to Unlimited.
5. **Comma-decimal committed expressions**: 30 rows `Production
   Cost[USD/MMBTU]*1,0551` (Philippines Natural Gas consumer prices) — a
   §A.15/§A.20 decimal ambiguity in committed authoring.
6. `_x000D_` CR artifacts: 82 rows (mostly Additions to Reserves notes).
7. `Metalurgical Coke` branch-name misspelling (author verbatim).
8. **0 `!Missing Branch` refs** in resources — the dangling-price breakage
   is entirely demand-side.
9. Raw-crop-tonnes convention confirmed: all 5 crops + Molasses + POME cap
   in Metric Tonne; no fuel has mixed MaxProd units across regions.

---

## 14. The `Transformation\` conversion tree

`LEAP Input Transformation.xlsx` — **577,248 rows, 1,593 branches, 80
variables, max depth 7.** Same 11-scenario / 12-region roster as the other
exports. This is the **hub tree** of the whole area: `Resources →
Transformation → fuels/electricity → Demand`. Every generator, refinery,
mine, blending pseudo-tech and biofuel converter lives here; the tree pulls
feedstocks and cost signals up from `Resources\`, takes its policy levers and
its transmission-node binding from `Key\`, and emits the secondary fuels and
electricity the four demand sectors consume. It is the single largest export
by row count and the only one that references *both* of the other two
input-side trees. Structure is canon (§2.6); expression content is not.

---

### 1. Tree shape

**Depth census** (branches only carry-through when they hold ≥1 variable, so
the pure `Processes\` / `Output Fuels\` container nodes do not export — same
convention as the Key tree §12): `{L2: 28, L3: 1, L4: 163, L5: 4, L6: 431,
L7: 966}` = 1,593. The lone L3 branch is `Transformation\Centralized
Electricity Generation\Transmission Lines`; the four L5 branches are the crop
biofuel `Output Fuels\<Product>\Land Use` leaves (§1.3). The 966 L7 leaves are
the emission-factor (`Avg Environmental Loading`) pollutant leaves.

**Sub-branch anatomy census** (whole tree, from `transformation_branches.csv`):

| Kind | Count | Where |
|---|---|---|
| Feedstock pollutant leaf (L7) | 939 | `Processes\<tech>\Feedstock Fuels\<fuel>\<pollutant>` |
| Transmission Node leaf | 248 | `Processes\<tech>\Transmission Nodes\<node>` (Centralized only) |
| Feedstock fuel leaf (L6) | 173 | `Processes\<tech>\Feedstock Fuels\<fuel>` |
| **Process node (L4)** | **108** | `Processes\<tech>` — power 63, fossil 21, bioenergy 24 |
| Output fuel leaf (L4) | 42 | `<Group>\Output Fuels\<fuel>` — **module-level, a sibling of `Processes`, not a per-process child** |
| L2 group root | 28 | `Transformation\<Group>` |
| Auxiliary pollutant leaf (L7) | 27 | `Processes\<tech>\Auxiliary Fuels\<fuel>\<pollutant>` |
| Auxiliary fuel leaf (L6) | 14 | `Processes\<tech>\Auxiliary Fuels\<fuel>` |
| Transmission Lines container/leaf | 10 | `Centralized…\Transmission Lines\<line>` (intra-fleet DC/AC lines, distinct from `Key\Transmission\Lines`) |
| Output Fuel Land Use (L5) | 4 | crop biofuel land-footprint (§1.3) |

**Process skeleton.** A module is `Transformation\<Group>\{Output
Fuels\<fuel>[\Land Use], Processes\<tech>}`; a process nests
`Processes\<tech>\{Feedstock Fuels\<fuel>\<pollutant>, Auxiliary
Fuels\<fuel>\<pollutant>, Transmission Nodes\<node>}`. Emission factors hang
on the pollutant leaves under Feedstock/Auxiliary Fuels; the yield split and
land footprint hang on the module-level Output Fuels.

**The 28 level-2 groups by owner** (branch counts from
`transformation_summary.json`; owner sum = 1,593):

| Owner | Groups (branches) | Σ br |
|---|---|---|
| **Power** (3 groups) | Centralized Electricity Generation **2,175** (was 1,093 pre-Indonesia-merge); Distributed Electricity Generation 4; Electricity Transmission and Distribution 3 | **2,182** |
| **Fossil** (15 groups) | Energy Sector Own Use 59; Oil Refining 29; Gas Processing 12; Crude Oil Production 7; Natural Gas Production 7; LNG Regasification 7; Natural Gas Transmission and Distribution 6; Diesel Blending 6; Gasoline Blending 6; Gasoline Distribution and Handling 4; five coal-production groups (Anthracite / Bituminous / Lignite / Sub Bituminous / Unspecified) × 5 = 25 | 168 |
| **Bioenergy** (10 groups) | Hydrogen Production for Energy Use 138; Biodiesel Production 40; Bioethanol Production 31; Charcoal Production 27; Renewable Diesel Production 21; Sustainable Aviation Fuel Production 21; Biomethane Production 20; Methanol Production for Energy Use 12; Domestic Biogas Production 10; Ammonia Production for Energy Use 5 | 325 |

The Centralized fleet is 69% of the tree. Its **61 process nodes** (60 at the
41-var storage-capable panel + 1 at 36 vars) span the full generation stack —
coal (Subcritical/Supercritical/Ultrasupercritical ± CCS, IGCC ± CCS), gas
(Combined Cycle ± CCS, Turbine, Engine, Steam), Fuel Oil/Diesel, nuclear
(LWR/SFR/SMR), geothermal (Flash/ORC), hydro (Large/Pumped), variable
renewables (Solar PV/CSP/Floating, Wind On/Offshore, Tidal, Wave), bioenergy
(Biomass Gasification, Bioenergy with CCS, Biogas, Waste), H2 Fuel Cell,
Direct Air Capture, four storage techs, and the `Unmet Load_*` slack processes
(§11.4). **Load-bearing structural caveat — sub-national node decomposition is
real for BOTH Malaysia and Indonesia.** Several generation families carry
sub-national node variants **in addition to their un-suffixed base branch**
(CORRECTION 2026-07-06 — an earlier version said "no base branch"; wrong.
Base branches exist for every family and hold the copper-plate regions'
fleets; see the §11.1 caveat below for the evidence):
  - **Malaysia — 3 nodes** (`_MYPE` Peninsular / `_MYSB` Sabah / `_MYSR`
    Sarawak): 33 process nodes across 11 families (Biomass Other, Coal
    Subcritical, Diesel, Gas Combined Cycle, Gas Turbine, Large Hydro, Nuclear
    LWR/SFR/SMR, Solar PV, Unmet Load, Wind Onshore).
  - **Indonesia — 4 nodes** (`_IDJW` Jawa-Madura-Bali / `_IDSA` Sumatra /
    `_IDKA` Kalimantan / `_IDEast` Eastern): 51 process nodes across 13
    families (Biogas [3 — no Eastern], Biomass Other, Coal Subcritical, Diesel,
    Gas Combined Cycle, Gas Engine, Gas Turbine, Geothermal Flash, Large Hydro,
    Small Hydro, Solar PV, Unmet Load, Wind Onshore). Wired to 4 sub-national
    grids + aggregate (`Transmission Nodes\{Indonesia, Indonesia Jamali,
    Indonesia Sumatra, Indonesia Borneo, Indonesia East}`).

> **CORRECTION 2026-07-04.** The original `LEAP Input Transformation.xlsx`
> export was **region-scoped**: it surfaced only Malaysia's `_MY*` node
> variants and Malaysia transmission nodes, so a prior version of this doc
> wrongly stated Indonesia's `_IDxx` were "referenced but not materialised as
> separate branches." **They ARE real branches** — verified as `col E`
> branch_paths (`…\Processes\Solar PV_IDJW`, etc.), not expression references.
> They live in Indonesia's region tree, which the Malaysia-context export did
> not walk (the §11.1 region-scoped branch-visibility effect — real, not an
> artefact to wave away). The canon transformation tree now **merges the
> dedicated `LEAP Input Transformation Indonesia.xlsx` export** (2026 Indonesia
> branches → 1082 new), bringing the merged Centralized process-node roster
> from 61 to **115** (61 + 51 Indonesia `_ID*` + 3 base `Nuclear LWR/SFR/SMR`
> that only the Indonesia export surfaced — Malaysia's export carried Nuclear
> solely as `_MY*`). **Confirmed by user 2026-07-04:** only Indonesia (4) and
> Malaysia (3) are node-decomposed; the other 8 ASEAN regions are single
> copper-plate nodes — so the power tree is now complete for node structure.
> (The region-scoped-export lesson still applies to future area versions.)

The three sibling owner writeups (verified, verifier-corrected) fold in below.

---

#### 1.1 Power owner — the Centralized Electricity Generation fleet

`Transformation\Centralized Electricity Generation` is the single largest
module in the Transformation export. In the original Malaysia-scoped export it
held **1,093 branches** with **61 process nodes**; after merging the Indonesia
export (2026-07-04) it held **2,175 branches** with **115 process nodes**
(61 + 51 Indonesia `_ID*` + 3 base `Nuclear LWR/SFR/SMR`); after the base-branch
correction (2026-07-06, Singapore v0.68 evidence — §11.1 caveat) it holds
**2,184 branches** with **124 process nodes** (+9 un-suffixed base branches:
Coal Subcritical, Diesel, Gas Combined Cycle, Large/Small Hydro, Solar PV,
Wind Onshore, Biomass Other, Unmet Load; whole sector 2,675 → **2,684**).

> **MERGED COUNTS (2026-07-04, authoritative — supersede any pre-merge figure
> below).** Whole Transformation sector: **2,675 branches** (was 1,593).
> Centralized Electricity Generation: **2,175 branches**, **115 process nodes**,
> **439,176 expression rows** (was 1,093 / 61 / 396,228). Sub-branch rows:
> `Feedstock Fuels` **144,121** (was 129,768); `Transmission Nodes` /
> `Nodal Distribution` **23,597** (was 20,832); `Avg Environmental Loading`
> **97,735** (was 87,780). Per-process-panel core variables no longer follow a
> single clean `nodes × 11 × 12` product — the Indonesia `_ID*` nodes exist in
> one region (Indonesia) under an 11-scenario roster that DIFFERS from the canon
> 11 (it includes scratch scenarios `LCO backup`, `Regional Aspiration Scenario
> test`, `Set up`, `Carbon Neutrality_ Net Zero`, 3× `RE LTRM …`). Representative
> merged per-variable counts: `Capital Cost` 9,715, `Node` 8,910,
> `Minimum Utilization` 8,910, `Maximum Availability` 8,910. **Any inline
> `8,052` / `20,832` / `129,768` / `396,228` figure further down this section is
> the pre-merge Malaysia-scoped-export baseline — read it as such.**

> **§11.1 region-scoped-export caveat — READ THIS.** LEAP "Export Expressions"
> is **region-scoped for region-specific branches.** Sub-national process-node
> variants (`Solar PV_MYPE`, `Solar PV_IDJW`, …) live in a *specific region's*
> tree, and an export only walks the variants visible in the context it was run
> from. The original `LEAP Input Transformation.xlsx` was run in a
> Malaysia/Base-Template context, so it materialised **only** Malaysia's
> `_MYPE/_MYSB/_MYSR` variants and Malaysia transmission nodes — it did **not**
> contain Indonesia's `_IDxx` variants (which is why an earlier version of this
> doc wrongly called them "referenced but not materialised"). The dedicated
> `LEAP Input Transformation Indonesia.xlsx` export surfaced them, and the canon
> tree now merges both.
>
> **CORRECTION 2026-07-06 — base branches EXIST for decomposed families.**
> An earlier version of this caveat said "no un-suffixed base branch — only
> the node variants exist". That was the same region-scoped-export artefact
> striking a third time: the `mailbox/20260607/` Singapore v0.68 update
> carries real BranchIDs with Singapore's actual fleet on the un-suffixed
> base branches (`Gas Combined Cycle` 10,114.71 MW and `Solar PV` 1,211.18 MW
> in 2024, plus zeros on the other ten). Branch structure is region-invariant
> (user-established, CLAUDE.md §A.22): every branch exists in every region;
> copper-plate regions hold their fleets on the base branches, Malaysia /
> Indonesia hold theirs on the `_MY*` / `_ID*` variants. The 9 base branches
> the exports had hidden (Coal Subcritical, Diesel, Gas Combined Cycle,
> Large/Small Hydro, Solar PV, Wind Onshore, Biomass Other, Unmet Load) are
> now in the canon tree with their observed variables; per-country slice
> exports (in progress 2026-07-06) will fill their full rosters. Beware:
> the region-values sitting on `_MY*`/`_ID*` paths for OTHER regions are
> node-creation copy-residue, not the base-branch truth (`Solar PV_MYPE`
> says Singapore = 0; the real base `Solar PV` Singapore is 1,211 MW).
> **Confirmed by user 2026-07-04:** only Indonesia + Malaysia are
> node-decomposed; the other 8 ASEAN regions are single copper-plate nodes. (The
> region-scoped-export caveat still applies to future area versions.)

**Malaysia roster — 33 process nodes across 11 families** (`_MYPE`/`_MYSB`/`_MYSR`; the original 61, 39 families):

| Category | Families (materialized process nodes) |
|---|---|
| **Coal thermal** | Coal Subcritical (`_MYPE`,`_MYSR` — no `_MYSB`), Coal Supercritical, Coal Ultrasupercritical, Coal IGCC; **+CCS**: Coal Supercritical CCS, Coal Ultrasupercritical CCS, Coal IGCC with CCS |
| **Gas thermal** | Gas Combined Cycle (`_MYPE`/`_MYSB`/`_MYSR`), Gas Combined Cycle with CCS, Gas Turbine (base + `_MYPE`), Gas Engine, Gas Steam |
| **Oil / diesel** | Diesel (`_MYPE`/`_MYSB`/`_MYSR`), Fuel Oil |
| **Nuclear** | Nuclear LWR, Nuclear SFR, Nuclear SMR — each as `_MYPE`/`_MYSB`/`_MYSR` (9 nodes) |
| **Variable renewables** | Solar PV (`_MY*`), Solar CSP, Solar Floating, Wind Onshore (`_MY*`), Wind Offshore, Tidal, Wave |
| **Firm / dispatchable renewables** | Large Hydro (`_MY*`), Geothermal Flash, Geothermal ORC, Biogas, Biomass Gasification, Biomass Other (`_MY*`), Bioenergy with CCS, Waste |
| **Storage** | Lithium Ion Batteries, VRB Flow Batteries, Pumped Hydro, CAES |
| **Other / slack / CDR** | H2 Fuel Cell, Direct Air Capture, Unmet Load (`_MYPE`/`_MYSB`/`_MYSR` slack) |

Malaysia's decomposition is **asymmetric**: some families are `_MY*`-only (Solar PV, Wind Onshore, Large Hydro, Nuclear ×3, Diesel, Gas Combined Cycle, Biomass Other, Unmet Load), Coal Subcritical is `_MYPE`+`_MYSR` (no `_MYSB`), Gas Turbine has **both** a base node and `_MYPE`, and the remaining families are base-only.

**Indonesia roster — 51 process nodes across 13 families** (`_IDJW` Jawa-Madura-Bali / `_IDSA` Sumatra / `_IDKA` Kalimantan / `_IDEast` Eastern; from `LEAP Input Transformation Indonesia.xlsx`, merged 2026-07-04):

| Decomposed family | Indonesia nodes |
|---|---|
| Biogas | `_IDJW`/`_IDKA`/`_IDSA` (3 — **no `_IDEast`**) |
| Biomass Other, Coal Subcritical, Diesel, Gas Combined Cycle, Gas Engine, Gas Turbine, Geothermal Flash, Large Hydro, Small Hydro, Solar PV, Unmet Load, Wind Onshore | each `_IDJW`/`_IDSA`/`_IDKA`/`_IDEast` (4) |

Indonesia's decomposition set differs from Malaysia's: Indonesia decomposes **Biogas, Gas Engine, Geothermal Flash, Small Hydro** (Malaysia does not), and does **not** decompose Nuclear (Malaysia does ×3). Each Indonesia generator is nodally wired to `Transmission Nodes\{Indonesia, Indonesia Jamali (=IDJW), Indonesia Sumatra (=IDSA), Indonesia Borneo (=IDKA), Indonesia East (=IDEast)}` — 4 sub-national grids + aggregate, mirroring Malaysia's Peninsular/Sabah/Sarawak + aggregate. So nodal decomposition is **NOT Malaysia-only** (correcting the earlier claim below in §Nodal wiring); it is confirmed for Malaysia (3) and Indonesia (4), and the other 8 ASEAN are single copper-plate nodes (user-confirmed 2026-07-04).

> **Region-lock (CANON, user 2026-07-05; CLAUDE.md §A.21).** A `_MY*` node
> exists **only** in Malaysia; a `_ID*` node **only** in Indonesia. LEAP's
> inheritance tree replicates the `_MY*` branches into every region's view, but
> they are `Node=0` (unwired) outside Malaysia — so a value authored for e.g.
> `Solar PV_MYPE` in Vietnam, or `Large Hydro_IDJW` in Thailand, is a **data
> error**, not real data. Inject files must carry `_MY*` rows only for `ams =
> Malaysia` and `_ID*` rows only for `ams = Indonesia`; base (un-suffixed) nodes
> are region-general and legitimately appear everywhere. Enforced by
> `nemo_read.find_region_lock_violations` + `tests/test_region_lock.py`.

**Process variable panel.** Each generator node carries a full LEAP process panel — 41 distinct variables in the union, ~31 populated for a typical thermal node. Every core variable is present at **61 nodes × 11 scenarios × 12 regions = 8,052 rows**. Sub-branch anatomy is limited to **`Feedstock Fuels\<fuel>`** (129,768 rows; each fuel carries `Feedstock Fuel Share`, `Fuel Cost`, `Fuel Source`, plus emission-species children) and **`Transmission Nodes\<node>`** (20,496 rows, `Nodal Distribution`). There are **no per-process `Auxiliary Fuels` or `Output Fuels` buckets** — electricity output attaches once at module level, and combustion emission factors (`Avg Environmental Loading`, 87,780 rows across 665 emission leaves) hang off the `Feedstock Fuels` sub-branches.

| LEAP variable | NEMO param (§2.3) | Units (scale \| unit \| per) | Verbatim example |
|---|---|---|---|
| `Capital Cost` | `CapitalCost` | Thousand \| USD \| MW | `Interp(2020, 1814, 2030, 1776) ? Vietnam PDP8` (Coal Supercritical, RAS) |
| `Fixed OM Cost` | `FixedCost` | Thousand \| USD \| MW | `Interp(2020, 32.2, 2030, 31.50)` |
| `Variable OM Cost` | `VariableCost` | USD \| MWh | `500` (Unmet Load); `0` (Solar PV_MYPE) |
| `Lifetime` | `OperationalLife` | Years | `40` (Coal Supercritical) |
| `Exogenous Capacity` | `ResidualCapacity` | MW | `Existing Capacity[MW] + Capacity Additions[MW]` |
| `Maximum Availability` | `AvailabilityFactor` | Percent | `61 ? NREL ATB 2023` (Solar CSP); `95` (Nuclear LWR) |
| `Minimum Utilization` | `MinimumUtilization` | Percent | see dispatch discipline below |
| `Capacity Credit` | `ReserveMarginTagTechnology` | Percent | see reserve-margin below |
| `Optimized New Capacity` | endogenous NEMO build | MW | `Data(2050, 96627.3, 2060, 119320.3) ?Optimized on 07/02/2026 (NEMO/CPLEX)` |

`Optimized New Capacity` rows carry **solver-written** `Data(...)` series stamped `?Optimized on 07/02/2026 11:41 (NEMO/CPLEX)` — this is a *solved* area recording CPLEX's endogenous capacity-expansion decisions. `Exogenous Capacity` (= NEMO `ResidualCapacity`) is the building-block sum `Existing Capacity + Capacity Additions`.

**Dispatch discipline — the §11.2c must-run check (load-bearing).** `Minimum Utilization` (8,052 rows) splits three ways:
- **Curtailable variable renewables (`MU = 0`)** in Current Accounts, Baseline, and AMS Target — every VRE process (132 rows each) is `0`, the §11.2c-correct shape. No trap in those three.
- **Incumbent must-run phaseout (guarded `Min()`):** 2,620 rows use `Min(Interp(FirstScenarioYear, Value(Historical Capacity Factor, LastHistoricalYear), FSY + Key\Modeling Assumptions\Incumbent Generator DIspatch Phaseout:Activity Level, 0), Maximum Availability)` across 35 incumbent families; **2,522 reference the `Incumbent Generator DIspatch Phaseout` key** (capital "DI"). The outer `Min(…, Maximum Availability)` is the §11.2c guard.
- **⚠ Bare `Minimum Utilization = Maximum Availability` (the §11.2c TRAP) — 494 rows** (474 variable renewables + 20 Biogas/Waste/Large Hydro_MYSB/MYSR). **Absent in CA/Baseline/AMS Target; present in RAS + every RE-policy scenario.** RAS: 27 trap rows — `Wind Onshore_MYPE`/`_MYSB` in 11 of 12 regions (all except Malaysia, which reads `0`); `Wind Onshore_MYSR` is `0` (sibling inconsistency). Set up / LCO backup / RE LTRM ×3: full 12-region trap on Solar CSP/Floating, Tidal, Wave, Wind Offshore, Wind Onshore. **Hypothesis, not proven (§A.13):** may not bind if those `_MY*` branches carry zero capacity outside Malaysia — verify against `Exogenous Capacity`/`Optimized New Capacity` before treating as a live infeasibility root cause. But this is exactly the §11.2c authoring pattern and should be scrubbed to `0` or a `Min(...,Maximum Availability)` guard in the affected scenarios.

**Unmet Load slack (§11.4).** The **18 Unmet Load branches** (3 slack nodes `_MYPE`/`_MYSB`/`_MYSR` × {process + `Feedstock Fuels\Non Energy` + 4 `Transmission Nodes`}) are unhidden and **priced**: `Variable OM Cost = 500` + `Fixed OM Cost = 500` (+ deterrent `Capital Cost = 100000`) on all 396 rows — unmet demand resolves as expensive slack, not LP-infeasible. (Only Malaysia `_MY*` slack materialized here; other AMS carry it on their own regional branches per §11.1.)

**Capacity Credit / reserve-margin tagging (`ReserveMarginTagTechnology`, from CA/Indonesia):** storage & CDR = 0 (CAES, Li-Ion, VRB, Pumped Hydro, DAC, H2 Fuel Cell); firm thermal explicit % (Coal Subcritical 92.50, Coal Supercritical 81.23, Gas CC 85, Gas Turbine/Steam 92, Diesel/Fuel Oil 50.67); branch-ref inheritance (Coal IGCC/Ultrasupercritical → Coal Supercritical; Gas Engine → Gas Turbine); `= Maximum Availability` on all Nuclear, Biogas, Biomass, Geothermal, Waste, Solar CSP, Tidal, Wave, Large Hydro_MYSB/MYSR **and Unmet Load**. Variable-renewable credits are mixed and worth flagging: Wind Offshore `20`, Solar Floating `18.61`, but `Solar PV_MY* = 100`, `Wind Onshore_MYSR = 100`, `Large Hydro_MYPE = 100`, `Gas Turbine_MYPE = 100` — these read as LEAP defaults on un-authored inheritance copies (same six carry `Capital Cost = 0`), not deliberate firm-capacity credits (hedged pending a per-region probe).

Representative paths: `…\Processes\Coal Supercritical\Feedstock Fuels\Coal Bituminous\Carbon Dioxide` (emission factor); `…\Processes\Solar PV_MYPE\Transmission Nodes\Malaysia Sarawak` (Nodal Distribution); `…\Processes\Unmet Load_MYSR` (Variable OM Cost = 500); module-level constraint hosts on the CEG root: `RenewableCapacityTarget__NEMOcc`, `ASEANRenewableCapacityTarget__NEMOcc`, `Planning Reserve Margin`, `PRM for Simulated Scenarios`.

#### 1.2 Power owner — the grid layer: distributed generation, T&D, storage & the nodal network

The central thermal-and-renewable fleet is described above (Centralized
Electricity Generation, 61 processes). This subsection covers the rest of the
electricity system: the **behind-the-meter fleet** (`Distributed Electricity
Generation`, 4 branches), the **grid itself** (`Electricity Transmission and
Distribution`, 3 branches), the **energy-storage fleet** (5 techs), and the
**sub-national nodal wiring** binding every generator to the ASEAN Power Grid
modelled in `Key\Transmission`. The wiring is carried by three cross-cutting
variables — `Node` (8,052 rows), `Nodal Distribution` (20,832 rows), and the
storage/dispatch panel (`Full Load Hours`, `Minimum Charge`, storage-carryover
flags, `Merit Order`, `Dispatch Rule`) — plus the module-level grid knobs
`Planning Reserve Margin`, `Peak Load Ratio`, `Module Costs`, `Renewable
Target`.

##### Tree shape

| Branch | Depth | Shape |
|---|---|---|
| `…\Distributed Electricity Generation` | 2 (module) | one process: `…\Processes\Solar PV Rooftop` (33 vars) → `…\Feedstock Fuels\Solar`; output leaf `…\Output Fuels\Electricity` |
| `…\Electricity Transmission and Distribution` | 2 (module) | one process: `…\Processes\Electricity` (8 vars) → `…\Feedstock Fuels\Electricity`. No pollutant leaves |
| Storage fleet | L4 under `Centralized…\Processes` | `Pumped Hydro`, `CAES`, `Lithium Ion Batteries`, `VRB Flow Batteries`; plus `Pressurized H2 Gas` under `Hydrogen Production for Energy Use\Processes` |
| Nodal decomposition | L4 + L6 | `Centralized…\Transmission Nodes\{Malaysia, Malaysia Peninsular, Malaysia Sabah, Malaysia Sarawak}` (4 module-level) + the same 4 node leaves repeated under 61 Centralized processes = **248** `Transmission Nodes` branches, each carrying only `Nodal Distribution` |

`Natural Gas Transmission and Distribution` (6 branches, 1 process `Natural
Gas` with 3 pollutant leaves) mirrors the ETD shape on the gas side but sits
outside the electricity grid.

##### The nodal wiring — how generation reaches `Key\Transmission`

Every Centralized generator is bound to a transmission node by its **`Node`**
variable (units `ID`, 8,052 rows across 61 process branches). The value is a
branch pointer: `Node = BranchID(Key\Transmission\Nodes\Malaysia:Activity
Level[NA])`. This is the most-referenced Key link out of Transformation —
`Malaysia` 605, every other ASEAN country 561, the top rows of the export's
`top_key_refs`. Of the 8,052 `Node` rows, 5,654 are wired `BranchID(...)` and
2,398 are `0`: **Base Template and Timor Leste carry Node=0 for all 61
processes** (unwired — consistent with Timor Leste disabled from calc), and
each real region zeroes the ~110 process rows for techs it does not host (the
`_MYxx` sub-node techs are Node=0 everywhere but Malaysia). Per-region
BranchID-assigned/total: Base Template 0/671, Timor Leste 0/671, Malaysia
605/671, all nine other ASEAN 561/671 (671 = 61 branches × 11 scenarios).

The target `Key\Transmission` tree is a compact NEMO transmission network:
**10 country Nodes** (`Region_ = RegionID(<country>)` + `Activity Level = 0
? existence required`; **no Timor Leste node**); **21 Lines**
(`Lines\<Corridor>_<E|F|C>` with `From Node`/`To Node` = `BranchID(…Nodes\…)`,
`Maximum Flow` MW, `Capital Cost_`, `Efficiency_`, `Lifetime_`, plus
deactivated `!Reactance`/`!Construction Year`); **10 Demand Distribution**
branches routing 100% of each country's electricity demand to its single
national node (`Node_`, `Fuel_ = FuelID(electricity)`, `Activity Level = 1`).
Verbatim CA capacities: `P.Malaysia_Singapore_E` 1050, `P. Malaysia_Sumatra_F`
2000, `Sumatra_Singapore_F` 1200, `Thailand_Myanmar_F` 1250, `Thailand_Laos_E`
700 (+`_F` 600), `Laos_Vietnam_E` 570, `Thailand_Cambodia_F` 770,
`Sarawak_Brunei_C` 100 MW. The `_E`/`_F` suffix splits existing vs.
future/planned corridors.

##### Sub-national balancing — Malaysia AND Indonesia (not Malaysia-only)

> **CORRECTED 2026-07-04.** The figures in this paragraph are from the
> Malaysia-scoped main export and describe **Malaysia's** nodal balancing. They
> are **not** the whole story: the Indonesia export (merged 2026-07-04) shows
> Indonesia is **also** sub-nationally balanced across 4 grids (`Indonesia
> Jamali`, `Indonesia Sumatra`, `Indonesia Borneo`, `Indonesia East`) +
> aggregate, via its own `_ID*` process nodes and `Transmission Nodes\Indonesia*`
> leaves. The `20,832 rows / 248 branches` / `609 non-zero` counts predate the
> merge and cover Malaysia only — the merged `Nodal Distribution`/`Transmission
> Nodes` total is **23,597** rows. **Confirmed by user 2026-07-04: only
> Indonesia + Malaysia carry a nodal split; the other 8 ASEAN systems ARE single
> copper-plate nodes.**

**`Nodal Distribution`** (Malaysia-scoped export: `Percent`, 20,832 rows / 248
branches) splits a process's generation across sub-national nodes. In the
Malaysia export, 20,223 of 20,832 rows are `0`; every one of the 609 non-zero
rows sits in the Malaysia region (Peninsular 322, Sabah 140, aggregate Malaysia
84, Sarawak 63), splitting output across its three non-synchronous grids:
`Malaysia Peninsular ≈ Interp(2020, 87.15, …, 2024, 80.75)`, `Malaysia Sabah ≈
Interp(2020, 12.85, …, 2024, 19.25)` (complementary), with Sarawak and the
aggregate carrying the remainder / `100`. **Indonesia carries the analogous
split across its 4 grids** (surfaced only by the dedicated Indonesia export).

##### Storage fleet

Five processes are true energy storage, identified by a non-zero **`Full Load
Hours`** (units `Hours` — the energy-to-power duration ratio):

| Tech | Full Load Hours | Module | Seasonal carryover |
|---|---|---|---|
| CAES | `10 ? DEA Technology Catalogue` | Centralized | Yes |
| Pumped Hydro | `8 ? Electrochemical Energy Storage…` | Centralized | Yes |
| VRB Flow Batteries | `4 ? DEA Technology Catalogue` | Centralized | No |
| Lithium Ion Batteries | `2` | Centralized | No |
| Pressurized H2 Gas | `16.7 / Interp(2019, 0.1, …, 2050, 0.08) ? DEA Energy Storage 2025` | Hydrogen Production | (H2 chain) |

The four Centralized storage techs share a uniform signature: `Dispatchable =
Yes`, `Dispatch Rule = PercentShare`, `Merit Order = 1`, `Minimum Charge = 0`,
`Starting Charge = 0`, `Hourly Storage Carryover = Yes`, `Annual Storage
Carryover = No`. Duration class is encoded in the carryover flags:
**long-duration** Pumped Hydro + CAES set `Seasonal Storage Carryover = Yes`;
**short-duration** Li-Ion + VRB set it `No`. The full storage panel is attached
to **69 process branches** (61 Centralized + 8 Hydrogen-production) but is
inert (`Full Load Hours = 0`) on the 64 non-storage techs — LEAP hangs the
panel on every dispatchable process and only the 5 real storage techs populate
it. Dispatch across the Centralized fleet resolves to three `Dispatch Rule`
values: `MeritOrderDispatch` (1,968 rows — merit-order thermal), `PercentShare`
(616 — storage/share-dispatched), `FullCapacity` (344 — run-at-availability
baseload/VRE); `Merit Order` is mostly `1` (2,256), with `2`/`3`/`4` loading
tiers and `<parent>:Merit Order` branch-refs on `_MYxx` variants.

##### Module-level grid knobs

- **`Planning Reserve Margin`** — Centralized = `PRM for Simulated
  Scenarios[percent]`, a reference to a **user-defined local variable** on the
  module holding a per-region PRM trajectory, **identical across all 11
  scenarios**, sourced from national plans: Indonesia `Interp(2023, 17, 2024,
  20, …, 2036, 42) ? RUPTL 2021-2030`; **Cambodia `25 ? AEO6 assumption`**;
  Brunei `Interp(2023, 21.00, …, 2027, 25.00) ? assumed value`; distinct forms
  for Philippines (`Philippine Energy Plan 2020-2040`), Singapore (`Electricity
  Market Outlook 2023`), Myanmar (`30 ? Myanmar PDP`). Distributed PRM = `0`.
  *(Corrected: `25 ? AEO6` is Cambodia's, not Brunei's.)*
- **`Peak Load Ratio`** — Centralized = `PeakLoadRatioFromYearlyShape
  (<Country>_Hourly)` for 9 of 10 ASEAN countries. **Myanmar** falls back to
  flat `100` (no `Myanmar_Hourly` shape), as do Base Template and Timor Leste.
  Distributed = flat `100`.
- **`Renewable Target`** — `0` in every region and every policy-bloc scenario
  (module-level RE-target knob unused; renewable ambition is enforced via blend
  mandates + per-tech shares + the `__NEMOcc` custom constraints).

##### T&D losses; distributed rooftop bypass

The single ETD process `Electricity` carries per-region grid **`Losses`**
(units `Percent`): Vietnam `≈11%`, Myanmar `≈27%` declining, Cambodia rising
to `27%`, Brunei/Philippines `≈9-12%`. **Indonesia, Singapore, Timor Leste and
Base Template carry Losses = 0** (Indonesia zero despite being the largest
system); Laos/Malaysia/Thailand are single-point `Interp(2022, 10.55)` /
`Interp(2022, 4.48)` / `Interp(2022, 11.389)` constants dressed as time series.
`Maximum Production = Unlimited` (the §A.11 upper-bound 1e12 sentinel),
`Lifetime = 30`. **Distributed** holds exactly one process, **Solar PV
Rooftop**, deliberately *not* nodally wired (**no `Node` variable, no
`Transmission Nodes` children**): behind-the-meter, `Dispatch Rule =
FullCapacity`, `Maximum Availability = YearlyShape(<Country>_Solar
Availability)`, `Minimum Utilization = 0` (fully curtailable per §11.2c),
`Capacity Credit = 18.61 ? last historical availability`, `Exogenous Capacity =
Existing Capacity[MW] + Capacity Additions[MW]`, with `Usage Rule =
DomesticPriority`, `Surplus Rule = SurplusExported`, `Shortfall Rule =
RequirementsRemainUnmet` on its output.

##### Scenario & regional pattern (grid layer)

Almost entirely scenario-invariant: of the 350 (branch, variable) combos in
Distributed / ETD / Pumped Hydro / Transmission Nodes, only **13 diverge**
across scenarios (those 13 carry 2 or 3 distinct expressions — *not* 1), and
`Nodal Distribution` carries a **single distinct expression across the 7
scenarios it appears in** (`n_distinct_expr = 1`). Regional variation is
concentrated exactly where physics demands it — per-country PRM, per-country
hourly-shape Peak Load Ratios, per-country ETD losses, the Malaysia-only nodal
split — while the storage-fleet dispatch panel and interconnector topology are
template-uniform. *(Corrected: the earlier claim that the 13 diverging combos
"carry a single distinct expression" was self-contradictory; `n_distinct = 1`
describes only the 248 scenario-flat Nodal Distribution combos.)*

---

#### 1.3 Fossil owner — Oil Refining, coal/oil/gas production, blending & ESO

**Group inventory:** Oil Refining 29 (crude → 14 refined products,
multi-output); the five coal-production groups (`All Mines`, 5 br each); Crude
Oil Production 7; Natural Gas Production 7; Gas Processing 12 (raw NG →
LPG/NGL/Oil/…, full plant); LNG Regasification 7; Natural Gas T&D 6; Diesel
Blending / Gasoline Blending 6 each (biofuel-mandate pseudo-techs); Gasoline
Distribution and Handling 4 (evaporative-loss handling); Energy Sector Own Use
59 (refinery/LNG/power self-consumption + emissions).

##### Three process archetypes

| Archetype | n-vars | Carries | Members |
|---|---|---|---|
| **Full capacity-planning plant** | 29 | Exogenous Capacity + Capital + Fixed/Variable OM + Maximum Availability + Capacity Credit + Merit Order + … | `Oil Refining\…\All Refineries`, `Gas Processing\…\Natural Gas` |
| **Zero-cost blending pseudo-tech** | 23 | Exogenous Capacity + Maximum Availability + share-of-production vars, **no** Capital/Fixed/Variable OM Cost | `Diesel Blending\{Biodiesel, Diesel}`, `Gasoline Blending\{Ethanol, Gasoline}` |
| **Simple conversion/extraction** | 8–10 | Dispatch Rule, Lifetime, Losses / Process Efficiency, Maximum Production, share pair, Variable OM Cost — **no Exogenous Capacity, no Capital Cost** | coal `All Mines`, Crude Oil / NG Production, LNG Regas, NG T&D, ESO, Gasoline Distribution |

##### Exogenous Capacity, and the RAS/CNZ inject

Only the two full-plant processes and the blending pseudo-techs carry
`Exogenous Capacity` (= `ResidualCapacity`). **The refinery unit is `Thousand
Gigajoules/Year`** (`scale=Thousand`, `units=Gigajoules/Year`; 132 rows = 12
regions × 11 scenarios) — Indonesia CA `Interp(2005, 1675956.78, …)`; **RAS +
CNZ only** carry the forward capacity-expansion inject `Interp(2024,
2.4426e+06, 2026, 2.6549e+06, 2030, 2.6549e+06, …)` (≈2,443 → 2,655 PJ/yr,
byte-identical between RAS and CNZ). `Gas Processing\…\Natural Gas` capacity is
in **`Thousand Tonnes Oil Equiv/Year`**. Refinery `Maximum Availability = 100`,
`Lifetime = 30`.

##### Costs live on Resources; Transformation caps at Unlimited

Extraction/T&D/ESO processes carry **`Variable OM Cost = 0` and `Maximum
Production = Unlimited`** — the fossil supply *cost* is authored entirely on
the `Resources\` tree (Import/Production Cost), the mirror of §13.4's
costs-without-caps gap. Feedstock `Fuel Cost = 0` too (`Fuel Source =
SourceBelow`). **The two full-plant processes are the exceptions that carry
real conversion cost** *(corrected — it is NOT only Gas Processing)*:

- `Gas Processing\…\Natural Gas:Variable OM Cost` = `1.72 * ConvUnits(2023
  usd, 2020 usd) * ConvFuelUnits(toe, mmbtu, natural gas) / (Process
  Efficiency/100)` [2020 USD/TOE] (Indonesia; 1.25 elsewhere); 132/132 rows
  non-zero.
- `Oil Refining\…\All Refineries:Variable OM Cost` = `Mean(0.34, 0.51) *
  ConvUnits(2018 usd, 2020 usd) * ConvFuelUnits(toe, barrel, crude oil) /
  (Process Efficiency/100)` [per TOE], 132/132 non-zero; its `Capital Cost`
  uses `Mean(0.53, 1.62) …` [per Gigajoules/Year] — Indonesia `Mean(0.53,
  1.62)` vs Base Template `Mean(2.6, 3.05)`. *(Corrected: `Mean(0.53, 1.62)`
  is the Capital-Cost coefficient, not the VOM coefficient.)*

Across the tree **all 9,072 `Maximum Production` rows are literally `Unlimited`
(Gigajoule)** — 108 processes × 12 regions × the 7 optimization scenarios — the
benign §A.11 upper-bound flavour (silent-parse / LP-conditioning risk, not a
forced floor).

##### Output Fuels — the refinery yield split

The refinery distributes throughput via `Output Fuels\<fuel>:Output Share`
across **14 refined products** (Avgas, Bitumen, Diesel, Gasoline, Jet Kerosene,
Kerosene, LPG, Lubricants, Naphtha, Oil, Petroleum Coke, Refinery Feedstocks,
Refinery Gas, Residual Fuel Oil), with Gasoline tagged `Remainder(100)`. Yields
constant across CA and RAS (Indonesia): `Diesel = Interp(2007, 28.49, …,
33.98)`, `Kerosene = Interp(…)` declining, `Jet Kerosene = Interp(…)` rising,
`Avgas/Bitumen/Petroleum Coke/Refinery Feedstocks/Refinery Gas = 0`. Gas
Processing Indonesia: `LPG = 100`, `Oil = Remainder(100)`, rest `0 ? EBT`.
*(Corrected: the refinery has 14 Output Fuels leaves, not 7 — the "7" was a
truncated audit sample.)*

##### Feedstock, emissions, own-use

`Feedstock Fuel Share` sets the input mix (refinery crude `Interp(2005, 99.2,
…, 2017, 97.6)`; single-feedstock = `100`). Mining/extraction emission factors
hang on `Feedstock Fuels\<fuel>\<pollutant>:Avg Environmental Loading` — e.g.
`Crude Oil Production\…\Crude Oil\Carbon Dioxide = 4.67 ?a` [kg/TOE]; coal-mine
`Methane = 0 ? no indigenous production`. **Energy Sector Own Use** uses the
`\Processes\` wrapper (hidden by the collapsed tree-view — real path
`…\Energy Sector Own Use\Processes\Crude Oil\…`, not `…\Energy Sector Own
Use\Crude Oil`) and carries the widest pollutant panels (12 species: Ammonia,
Black Carbon, CO2, CO, CH4, NOx, N2O, NMVOC, Organic Carbon, PM10, PM2pt5,
SO2); its Electricity own-use has ~30% losses (`Interp(2005, 0, …, 2007,
29.97, …)`). Electricity-T&D **`Losses`** are non-zero on **88 of 132 rows** (8
regions × 11 scenarios — Brunei, Cambodia, Laos, Malaysia, Myanmar,
Philippines, Thailand, Vietnam; Indonesia/Singapore/Timor Leste/Base Template
all-zero). *(Corrected: 88 non-zero / 132 total, not "99 rows".)*

##### The blending pseudo-tech mechanism (Min/Max Share of Production)

`Diesel Blending` and `Gasoline Blending` each host two zero-cost processes
(`Biodiesel`+`Diesel`, `Ethanol`+`Gasoline`) feeding one `Output Fuels\Blended
Diesel|Blended Gasoline` (`Output Share = 100`). The split is
**scenario-mode-switched**: **accounting** scenarios (CA, Baseline, AMS Target,
RAS test) simulate via `Process Share` (renewable = computed share, fossil =
`Remainder(100)`; 96 branch-ref rows); **optimization** scenarios (Set up, CNZ,
LCO backup, RAS, RE LTRM ×3) enforce a `Minimum Share of Production` floor (168
branch-ref rows) with `Maximum_Share_of_Production = 100` and fossil Min Share
= `0`. The share expression converts a **volumetric** blend mandate into an
**energy-basis** floor, verbatim (Indonesia biodiesel, RAS):

```
Key\Biofuel Blending Targets\Biodiesel:Activity Level[Volume %]/100 * 38.997
  ~/~ (…/100 * 38.997 ~+ (1 - …/100) * 43.330) ~* 100
  ? Energy contents taken from Fuels database
```

i.e. `v·E_bio / (v·E_bio + (1−v)·E_fossil) · 100`, energy densities biodiesel
`38.997` / fossil diesel `43.330`, ethanol `26.744` / gasoline `44.8`. The
driver is `Key\Biofuel Blending Targets\{Biodiesel, Bioethanol}:Activity
Level`. `Minimum Utilization = 0` on all four. **§A.11 lower-bound landmine —
present in canon:** all four blending processes carry `Exogenous Capacity =
Unlimited` (`Megawatt`) — **528 rows** (4 × 12 × 11). Since Exogenous Capacity
= `ResidualCapacity`, LEAP→NEMO export turns each into a `1.0e+12` forced
floor. This is the exact shape flagged in §A.11 / the 2026-05-12 aeo9_v0.42
investigation (there judged a red herring, never remediated); it survives
unchanged in aeo9_v0.67. In RAS the blending processes additionally show
`Maximum Capacity = Unlimited` (upper-bound flavour).

The `Gasoline Distribution and Handling` module implements an evaporative-loss
model via three custom vars — `Annual Avg Reid Vapour Pressure` (80 kPa),
`Annual Avg Ambient Temp` (`15 ? Fill in country-specific value`), and `TVP`
(true vapour pressure, a closed-form function of the two) — the only place
these three variables appear.

---

#### 1.4 Bioenergy owner — clean-fuel & biofuel conversion

The ten clean-fuel/biofuel conversion sectors (Hydrogen 138, Biodiesel 40,
Bioethanol 31, Charcoal 27, Renewable Diesel 21, SAF 21, Biomethane 20,
Methanol 12, Domestic Biogas 10, Ammonia 5 = **325 branches / 112,164 rows**)
are the conversion stage of the hub: each takes a Resources feedstock and emits
a Resources secondary fuel.

##### Two process families

There are **24 conversion processes**, splitting into two variable-panel
families:

| Family | Count | Panel | Members |
|---|---|---|---|
| **Full-panel** (capacity-planned) | 17 | 29-var (`Exogenous Capacity`, Capital/Fixed/Variable OM, Lifetime, Maximum Availability, Minimum Utilization, Capacity Credit, Maximum Capacity(+Addition), Process Efficiency, Process Share…) | Biodiesel (CME/FAME/POME), Bioethanol (Cassava/Corn/Molasses/Sugarcane), Renewable Diesel (HVO), SAF (HVO), all 8 Hydrogen |
| **Lite-panel** (share-dispatched, no fleet) | 7 | 9–10 vars (`Dispatch Rule`, Lifetime, Max/Min Production, Max/Min Share of Production, Optimized New Capacity, Process Efficiency, Process Share, ±VOM) — **no Exogenous Capacity, no Capital Cost** | Ammonia (`Hydrogen`), Biomethane (2 AD variants), Charcoal (All Biomass), Domestic Biogas (Anaerobic Digestion), Methanol (CO2 Utilization / from Hydrogen) |

The 8 **Hydrogen** processes carry an extended **35-var panel** adding a storage
sub-panel (`Full Load Hours`, `Minimum/Starting Charge`, `Annual/Seasonal/
Hourly Storage Carryover`) — modelled as dispatchable storage-capable
generators. `Pressurized H2 Gas` carries the full storage panel but **zero
feedstock/auxiliary fuels** (an H2 compression/storage pseudo-process). Biofuel
capacity is energy-flow, not electrical: FAME Biodiesel `Exogenous Capacity` in
**Million GJ/Year**, `Capital Cost` in **2020 USD/(GJ/Year)** — distinct from
the power tree's MW / Thousand USD/MW.

##### Feedstock → product map

| Sector | Process | Feedstock fuel(s) | Auxiliary fuel(s) |
|---|---|---|---|
| Biodiesel | CME | Coconut Oil | Electricity, Methanol |
| Biodiesel | FAME | Palm Oil (95.99%) + Methanol (rem.) | Biodiesel, Electricity, Natural Gas |
| Biodiesel | POME | Palm Oil Mill Effluent | — |
| Bioethanol | Cassava / Corn / Molasses / Sugarcane | same-named crop | — |
| Renewable Diesel | HVO | Palm Oil (95.67%) + Hydrogen (rem.) | Biodiesel, Electricity |
| SAF | **HVO Renewable Diesel** | Palm Oil + Hydrogen | Biodiesel, Electricity |
| Biomethane | AD w/ Methanation / w/ Upgrading | Biomass | Hydrogen / Electricity |
| Domestic Biogas | Anaerobic Digestion | Biomass | — |
| Charcoal | All Biomass | Biomass + Wood | — |
| Hydrogen | Biomass Gasification (±CCS) | Biomass (rem.) + Electricity + Natural Gas | — |
| Hydrogen | Coal Gasification (±CCS) | Coal grade (one active/region) + Electricity | — |
| Hydrogen | PEM Electrolysis | Electricity | — |
| Hydrogen | SMR (±CCS) | Natural Gas (rem.) + Electricity | — |
| Methanol | CO2 Utilization for Iron and Steel | Blast Furnace Gas + Coke Oven Gas | Electricity |
| Methanol | Production from Hydrogen | Hydrogen | Electricity |
| Ammonia | **Hydrogen** | Hydrogen | Electricity |

##### Conversion arithmetic

**`Feedstock Fuel Share`** uses an explicit-primary + `Remainder(100)`
idiom: single-feed = `100`; FAME Palm Oil `95.99` / Methanol `Remainder(100)`;
HVO Palm Oil `95.67` / Hydrogen `Remainder(100)`; Biomass Gasification Biomass
`Remainder(100)` with Electricity/Natural Gas GREET mass ratios; **Coal
Gasification routes exactly one coal grade per region** (Indonesia Lignite
`Remainder(100)`, other three grades `0`). **`Process Efficiency`** mixes three
idioms: sourced constants (CME `95`, FAME `78.9 ? GREET1`, HVO `52.1 ? GREET1`,
SMR `71.8`, SMR-CCS `65.7`, Coal Gas `58.9`), GREET mass-balance ratios
(Biomass Gasification `1000000/(2198017+51874+13304+94280)*100`), and
unit-physics chains (Domestic Biogas via `ConvFuelUnits(…) *
Key\Cal\Transformation\domestic_biogas:Activity Level[factor]`; Molasses via a
liter→GJ ethanol chain). **Passthrough** processes (POME, Cassava, Sugarcane,
Charcoal All Biomass) author `100` — real conversion loss lives in the Land
Use yield / Resources crop yield, not here. Only the 3 Hydrogen calibration
knobs and Domestic Biogas reach into `Key\Cal\Transformation\*`.

##### The `Land Use` sub-branch (crop biofuels)

Exactly **4 sectors** carry `…\Output Fuels\<Product>\Land Use` — Biodiesel,
Bioethanol, Renewable Diesel, SAF (gas/hydrogen/charcoal have none). It holds
`CropYield` [tonne/ha], `BioProdYield` [litre/tonne], and `Avg Environmental
Loading` [Hectare/Gigajoule] = land intensity `1 / (CropYield · BioProdYield ·
ConvFuelUnits(Liter, GJ, <fuel>))`. `CropYield` is regionalised: oil-palm
`17.8 ? Indonesia`, `20.6 ? Malaysia`, `(20.6+17.8)/2` (=19.2) for the other
10; `BioProdYield = 230`. **SAF is a derived piggyback**: its `CropYield`/
`BioProdYield = 0` and its Land Use `Avg Environmental Loading` = a branch-ref
to `Renewable Diesel Production\Output Fuels\Renewable Diesel\Land Use:Avg
Environmental Loading[ha/GJ]` — SAF shares the HVO pathway.

##### Emissions (incl. biogenic & sequestered CO2)

`Avg Environmental Loading` is the domain's largest variable (29,700 rows).
Combustion-heavy **Charcoal** carries the full 11-species set including
**Organic Carbon** — which appears on only 2 leaves in the whole domain, **both
in Charcoal** (Biomass + Wood). Hydrogen Biomass Gasification's Biomass
feedstock carries 10 species (Black Carbon + PM10/PM2pt5 but **no Organic
Carbon**); coal-grade feedstocks carry 5. *(Corrected: Hydrogen gasification
does NOT carry the full 11-species set; only Charcoal does.)* Fossil-feedstock
CO2 scales with process efficiency and is sequestered under CCS: `SMR with
CCS\…\Natural Gas\Carbon Dioxide = 82467 * …Process Efficiency/100` [g/MMBTU],
paired `Sequestered Carbon Dioxide = -82467 * 95% * …/100` (negative, 95%
capture). **8 Sequestered CO2 leaves** exist, all in Hydrogen (7) + Methanol
(1). Biogenic CO2 is tracked on a **separate** `Carbon Dioxide Biogenic` leaf
(5 total): FAME aux Biodiesel `79.6` [t/TJ], Charcoal Biomass `542 ?a`
[kg/tonne] — tagging is **not uniform**: crop-feedstock combustion CO2 is filed
under fossil `Carbon Dioxide` (FAME Palm Oil `3.16 ?bioenergydat`, near-zero).

##### Costing

Feedstock `Fuel Cost` is `0` in 3,715 of 5,016 rows (crops — costed on
`Resources\Primary\<Crop>`). Of the 1,301 non-zero feedstock costs: **1,188 are
branch-refs to `Resources\Secondary\{Electricity (792), Hydrogen (264),
Methanol (132)}:Production Cost`; the remaining 113 = 102 `Interp(...)` constant
cost trajectories + 11 `Resources\Primary\Biomass:Production Cost` refs.**
*(Corrected: 792+264+132 = 1,188, not 1,301.)* Auxiliary electricity pulls the
same Electricity Production Cost (660 rows). Full-panel biofuel processes author
their own `Capital Cost` (FAME `Interp(2025, 5.3074, …, 2060, 4.1052)`) and
inherit VOM cross-region (`RegionValue(Malaysia)` for Indonesia). `Maximum
Availability = 100` on the 9 liquid-biofuel processes (all 1,188 rows).
**`Minimum Utilization` is *not* uniformly 0**: 50 of 2,244 process-level MU
rows are non-zero — 5 liquid-biofuel processes (FAME, Molasses, Sugarcane, CME,
Cassava) carry `Interp(2023, X, 2030, 100)` must-run ramps in the 5
optimization scenarios Set up / LCO backup / RE LTRM ×3, for
Indonesia/Malaysia/Philippines/Thailand; MU=0 holds in CA/Baseline/AMS/RAS/RAS
test/CNZ. *(Corrected from "MU=0 on all biofuel processes".)*

> **Boundary note.** These ten sectors *produce* the fuel; **zero** domain rows
> reference `Key\Biofuel Blending Targets`. The B/E blend mandate is applied
> downstream on the fossil-owner `Diesel/Gasoline Blending` pseudo-techs (§1.2),
> consistent with §11.4 and the connection audit.

---

### 2. Variable inventory — the 80-variable process panel

80 variables (full roster in `transformation_variables.csv`). The heavy hitters
are emissions (`Avg Environmental Loading` 128,040 rows / 970 branches — the
single biggest variable in any export) and fuel routing (`Fuel Cost` 23,232,
`Feedstock Fuel Share` 22,836, `Fuel Source` 15,708, `Nodal Distribution`
20,832). The §2.3 NEMO↔LEAP process-panel mapping, verified against this export:

| NEMO side | LEAP variable (rows / branches, top units) | Class |
|---|---|---|
| `ResidualCapacity` | **Exogenous Capacity** (11,220 / 85; MW, Million/Thousand GJ/Yr, Tonne Coal/Oil Equiv/Yr) | capacity |
| — (LEAP fleet building blocks feeding Exogenous Capacity) | Existing Capacity, Capacity Additions, Capacity Retirement (8,052 each; MW), Endogenous Capacity (4,080), Real Investment Cost (8,052; Million USD), Historical Capacity Factor (8,052), Historical Production (3,888; GWh / Thousand TOE) | capacity |
| `TotalAnnualMaxCapacity` | **Maximum Capacity** (7,140 / 85; MW etc.); Minimum Capacity, Maximum/Minimum Capacity Addition (7,140 each); Optimized New Capacity (9,072); Use Addition Size (2,016) | capacity |
| `CapitalCost` | **Capital Cost** (11,448 / 90; Thousand USD/MW, USD/(GJ/Yr), USD/Tonne-Coal/Oil-Equiv/Yr) | cost |
| `VariableCost` (process) | **Variable OM Cost** (14,088 / 110; USD/MWh, USD/TOE, USD/GJ) | cost |
| `VariableCost` (feedstock) | **Fuel Cost** on `Feedstock Fuels\<fuel>` (23,232 / 176) | cost |
| `FixedCost` | **Fixed OM Cost** (11,448 / 90) | cost |
| `InterestRateTechnology` | **Interest Rate** (11,976 / 94; mostly `DiscountRate`) | cost |
| — (CCS custom costs) | CCS VOM / CCS Capital / CCS FOM (1,584 each / 12; USD/MWh & Thousand USD/MW, refs `Coal Supercritical CCS:Process Efficiency`) | cost |
| — (zeroed accounting) | Stranded Cost, Salvage Value, Module Costs (all literal 0); Output Price (5,016, ~all 0) | cost |
| `OperationalLife` | **Lifetime** (13,908 / 117; Years) | dispatch |
| `AvailabilityFactor` | **Maximum Availability** (11,220 / 85; Percent) | dispatch |
| `MinimumUtilization` | **Minimum Utilization** (11,220 / 85; Percent) — 1:1 | dispatch |
| `ReserveMarginTagTechnology` | **Capacity Credit** (11,220 / 85; Percent) | dispatch |
| — (dispatch controls) | Dispatch Rule (4,800), Merit Order (4,080), Dispatchable (1,020), First Simulation Year (4,080), Priority Output (672) | dispatch |
| — (storage panel) | Full Load Hours, Minimum Charge (9,108 each), Starting Charge (828), Annual/Seasonal/Hourly Storage Carryover (828 each) | dispatch |
| `Input/OutputActivityRatio` | **Process Efficiency** (12,408 / 94; Percent) | conversion |
| — (fuel routing) | Feedstock Fuel Share (22,836), Fuel Source (15,708; SourceBelow / SourceModule), Auxiliary Fuel Use (1,848), Output Share (4,200), Losses (1,848) | conversion |
| `TotalTechnologyAnnualActivityUpperLimit` | **Maximum Production** (9,072 / 108; Gigajoule; **all `Unlimited`**) | production |
| — (activity bounds/shares) | Minimum Production (9,072, all 0), Maximum_Share_of_Production (12,960, all 100), Minimum Share of Production (9,072), Process Share (4,752), Renewable Qualified (7,140), Renewable Target (924, all 0), Optimize (864), Import/Export Target (2,016 each, ~all 0) | production |
| `EmissionActivityRatio` | **Avg Environmental Loading** (128,040 / 970) on Feedstock/Auxiliary pollutant leaves (kg/TJ, g/MMBTU, t/TJ, ha/GJ) — CO2, CH4, N2O, NOx, SO2, NH3, Black/Organic Carbon, PM10/PM2.5, "Carbon Dioxide Biogenic", "Sequestered Carbon Dioxide" | emission |
| — (grid / nodal) | Node (8,052 / 61; ID), Nodal Distribution (20,832 / 248; Percent), Peak Load Ratio (1,452), Planning Reserve Margin (1,404), PRM for Simulated Scenarios (132; local var), Shortfall/Surplus/Usage Rule (1,392 each) | grid |
| — (intra-fleet transmission lines, 9 br) | Transmission_Line_ID, Transmission Efficiency/Capacity/Availability, Construction Year, Maximum_Capacity_Addition, Simulation Type (`NetworkSimulation(Pipeline)`) | grid |
| — (bioenergy land) | CropYield, BioProdYield (528 each / 4) | land |
| — (gasoline evaporative) | Annual Avg Reid Vapour Pressure, Annual Avg Ambient Temp, TVP (132 each / 1) | conversion |
| — (NEMO custom constraints) | ASEANRenewableCapacityTarget__NEMOcc, RenewableCapacityTarget__NEMOcc (120 each / 1) | production |

**Panel note.** `Exogenous Capacity` / `Maximum Availability` / `Minimum
Utilization` / `Capacity Credit` each sit on 85 branches; the storage panel on
69; `Node` on 61 (the Centralized fleet); `Maximum Production` / `Minimum
Production` / `Optimized New Capacity` on 108 (every process). Cost/capacity
variables are near-fully-populated on the full-panel plants and sparse-to-absent
on the lite/extraction techs (§1). The `__NEMOcc` custom-constraint variables
(RE capacity targets) are the tree's only `__NEMOcc` presence — the §8-retired
`__NEMOcc` diagnostic angle, real data that must be preserved.

---

### 3. Connection map (CONFIRMED cross-tree edges, from the audit)

This tree is the hub; the audit resolved every cross-tree edge as CONFIRMED.

- **Transformation ← Resources (feedstock/cost pulls): 14,311 reference-rows.**
  *(Verified: rows-query count = 14,311, matching the summary's per-target
  occurrence sum exactly.)* Feedstock and auxiliary fuels and their `Fuel Cost`
  pull from `Resources\Primary\*` and `Resources\Secondary\*`: Natural Gas
  1,463, Electricity 1,452, Biomass 1,199, Coal Sub bituminous 1,188, Nuclear
  1,188, the other coals 1,056–1,067, Hydrogen 792, Ammonia 660, Bagasse 660,
  Biodiesel/Diesel 396 each, Methanol 264, Residual Fuel Oil / Biomethane /
  MSW 132 each. This is how the conversion stage inherits the §13.4 Resources
  cost layer instead of re-authoring it.
- **Transformation ← Key: 12,650 reference-occurrences across 11,778 rows.**
  *(Verified: 11,778 distinct rows carry ≥1 `Key\` reference; the 12,650 total
  is the audit's occurrence count — rows reference multiple Key branches.)* Top
  edges: **`Key\Modeling Assumptions\Incumbent Generator DIspatch Phaseout`
  2,522** — the §11.2c incumbent must-run phaseout knob, consumed inside
  `Minimum Utilization = Min(Interp(FirstScenarioYear, Value(Historical
  Capacity Factor…), FirstScenarioYear + …DIspatch Phaseout:Activity
  Level[years], 0), Maximum Availability)`; `Capacity Additions Multiplier\
  Fossil Fuel Dispatch Reduction` 672; **the `Key\Transmission\Nodes\<Country>`
  binding** (Malaysia 605, each other ASEAN 561 — the `Node` BranchID edges);
  **`Key\Biofuel Blending Targets\{Biodiesel, Bioethanol}` 396 each** (the blend
  mandate → energy-share floor on the Blending pseudo-techs); the 13
  `Key\Cal\Transformation\*` per-conversion calibration factors (biomass_eff
  308, Coal_sub_eff 275, Hydropower 264, Ngas_cc 231, domestic_biogas 132,
  Geothermal 121, LNG_regas 121, Biogas_eff 110, waste_eff 110, Oil refining 99,
  Gas processing 99); and `Key\Modeling Assumptions\* Lead Time` construction
  lead-times embedded in capacity-addition Interp formulas (Coal 279, Nuclear
  210, Gas 101, Oil 99, Solar PV 86…). The Node + Biofuel-Blending edges are
  exactly the §11.4 policy-feasibility couplings (nodal binding + blend
  mandate).
- **Resources ← Transformation (the one back-edge into Resources): the
  geothermal capacity-factor loop.** Indonesia + Philippines `Resources\Primary\
  Geothermal:Maximum Production` is derived from `Transformation\Centralized
  Electricity Generation\Processes\Geothermal Flash[_IDJW]:Maximum Availability`
  (audit: 18 rows; occurrences `Geothermal Flash_IDJW` 22 + `Geothermal Flash`
  7 = 29). This is the sole place Resources reads back from Transformation, and
  the reference to `_IDJW` is the evidence that region-scoped `_IDxx` node
  variants exist beyond the exported branch view (§1).
- **Demand sectors connect via shared FUELS, not references.** The four demand
  exports contain **zero** Transformation branch references (as the Resources
  export contains zero Key references, §13). The chain `Resources →
  Transformation → fuels/electricity → Demand` is a NEMO commodity-balance
  connection — Transformation's `Output Fuels` become the secondary fuels the
  demand sectors consume — resolved at solve time, not by LEAP expression
  wiring.

---

### 4. Scenario logic

Eleven scenarios in the standard roster (CA=1, Set up=11, CNZ=12, Baseline=18,
AMS Target=20, RAS=25, LCO backup=26, RE LTRM ×3 = 27/28/29, RAS test=30). Two
live axes, both shared with the Resources tree (§13.5):

1. **The accounting↔optimization variable-set switch.** The 4 accounting
   scenarios (CA, Baseline, AMS Target, RAS test) carry the LEAP-simulation
   panel — `Process Share`, `Dispatch Rule`, `Merit Order`, `Historical
   Production`, storage-carryover flags, `First Simulation Year`,
   `Shortfall/Surplus/Usage Rule`, `Endogenous Capacity`, `Import/Export
   Target`. The 7 optimization scenarios (Set up, CNZ, LCO backup, RAS, RE LTRM
   ×3) carry the NEMO panel — `Maximum/Minimum Production`, `Maximum/Minimum
   Capacity(+Addition)`, `Optimized New Capacity`, `Minimum Share of
   Production`, `Fuel Source`, `Output Share`, `Renewable Qualified`. **`Process
   Share` (accounting) and `Minimum Share of Production` (optimization) never
   coexist** on a branch; `Maximum_Share_of_Production = 100` appears in every
   scenario except CA; `Maximum Production = Unlimited` and `Fuel Source` exist
   only in the 7 optimization scenarios (invisible in accounting runs).
2. **The RAS+CNZ inject.** The refinery capacity-expansion `Exogenous Capacity`
   (§1.2) and the biofuel blend floors land forward in **RAS + CNZ only**
   (`CNZ = RAS` byte-for-byte); the other 9 scenarios keep historical series.

Expression blocs match the rest of the area: `CNZ = RAS`, `Baseline = RAS
test`, `Set up = LCO backup = RE LTRM Policy Aligned` on the shared cells;
`Regional Aspiration Scenario test` (id 30) is the stale accounting-mode
prototype (= Baseline). Scenario churn is low per owner — grid layer 13 of 350
combos diverge, bioenergy 87 of 1,098 (~7.9%), fossil largely invariant outside
the mode switch + RAS/CNZ inject. NEMO/CPLEX solver output is written back into
`Optimized New Capacity` expressions (`?Optimized on 07/02/2026 11:41
(NEMO/CPLEX)`) in the optimization scenarios — the §14-ledger artefact, here on
the supply side.

---

### 5. Regional / nodal pattern

Twelve regions; **Base Template and Timor Leste are special** — both fully
unwired from the grid (`Node = 0` for all 61 Centralized processes), Timor
Leste with no `Key\Transmission\Nodes\Timor Leste` at all (consistent with TL
disabled from calc). Regional variation is concentrated where physics demands
it and template-uniform elsewhere:

- **Sub-national nodal decomposition — Malaysia (3) AND Indonesia (4).**
  Malaysia: 248 `Transmission Nodes` sub-branches naming its three
  non-synchronous grids (Peninsular/Sabah/Sarawak) + aggregate. Indonesia
  (merged 2026-07-04): its own `Transmission Nodes\{Indonesia, Indonesia
  Jamali, Indonesia Sumatra, Indonesia Borneo, Indonesia East}` across its
  `_ID*` process nodes. **Confirmed by user 2026-07-04: only Indonesia + Malaysia
  carry nodal decomposition; the other 8 ASEAN systems ARE single copper-plate
  nodes.** (The Malaysia-scoped main export couldn't see other regions' variants,
  so this was verified by the user rather than derived from the export.)
- **`_MYxx` / `_IDxx` process variants — BOTH are real materialised branches.**
  Malaysia `_MYPE/_MYSB/_MYSR` (33 nodes, 11 families) came from the main
  export; Indonesia `_IDJW/_IDSA/_IDKA/_IDEast` (51 nodes, 13 families) came
  from `LEAP Input Transformation Indonesia.xlsx` and are now merged into the
  canon tree. Every decomposed family ALSO has an un-suffixed base branch
  holding the copper-plate regions' fleets (CORRECTION 2026-07-06 — earlier
  "neither has a base branch" text was a region-scoped-export artefact; see
  §11.1 caveat). (Earlier text calling Indonesia's `_IDxx` "referenced but
  absent from the exported branch view" was wrong — the same artefact, fixed
  2026-07-04.) CLAUDE.md §A.12's `IDJW/IDSA/IDKA/IDEast` + `MYPE/MYSB/MYSR`
  node sets are correct and now backed by canon.
- **Per-country physical layers:** PRM trajectories (national capacity plans —
  RUPTL, PEP, EMO, PDP, AEO6), Peak Load Ratios (from `<Country>_Hourly`
  shapes; Myanmar + Base Template + Timor Leste fall back to flat 100), ETD loss
  curves (Indonesia/Singapore = 0).
- **Bioenergy crop layer:** `CropYield`/`BioProdYield` regionalised to real
  agronomy (oil-palm Indonesia 17.8, Malaysia 20.6, others 19.2); Coal
  Gasification routes each region's local coal grade. Process efficiencies and
  emission factors are one expression across all 12 regions; feedstock costs
  vary only through the Resources references they inherit.
- **Fossil:** the refinery Capital Cost is the main per-region divergence
  (Indonesia `Mean(0.53,1.62)` vs Base Template `Mean(2.6,3.05)`); everything
  else is template-uniform outside the RAS/CNZ inject.

---

### 6. Drivers

Transformation is driven almost entirely from `Key\`, with a few local knobs:

- **`Key\Modeling Assumptions\Incumbent Generator DIspatch Phaseout`** (note
  the capital "DI" — canon-verified, case-sensitive) — the single centralized
  incumbent-must-run phaseout knob, consumed by 2,522 `Minimum Utilization`
  formulas (§11.2c pattern 3); change its `Activity Level[years]` and every
  incumbent generator re-shapes together.
- **`Key\Transmission\Nodes\<Country>`** — the nodal binding target of every
  generator's `Node` variable; wires the fleet to the ASEAN Power Grid.
- **`Key\Biofuel Blending Targets\{Biodiesel, Bioethanol}`** — the volumetric
  blend mandate the Blending pseudo-techs convert to energy-share floors.
- **`Key\Cal\Transformation\*`** (13 factors: biomass_eff, Coal_sub_eff,
  Hydropower, Ngas_cc, Geothermal, LNG_regas, domestic_biogas, Biogas_eff,
  waste_eff, `Oil refining`, `Gas processing`, oil_eff, Natgas_losses) — the
  per-conversion calibration layer (invisible to the demand exports, §12.2).
- **`Key\Modeling Assumptions\* Lead Time`** — construction lead times embedded
  in `Capacity Additions` Interp formulas (`Interp(BaseYear, 0, 2023+1, 200,
  2023 + Key\Modeling Assumptions\Coal Lead Time:Activity Level, 220)`).
- **`Key\Capacity Additions Multiplier\Fossil Fuel Dispatch Reduction`** (672)
  and **`Key\End_cap multip\{Total_, RE_Fraction}`** — endogenous
  capacity-fraction levers on `Endogenous Capacity`.
- **`PRM for Simulated Scenarios`** — the module-local Planning-Reserve-Margin
  variable (a two-hop indirection; §1.1) — and `DiscountRate` on Interest Rate.

---

### 7. Quirks & hygiene (merged, verifier-corrected)

**Structural / region-scoping**

1. **Sub-national decomposition — `_MYxx` (Malaysia) AND `_IDxx` (Indonesia),
   surfaced by SEPARATE region-scoped exports.** Malaysia decomposes 11 families
   into `_MYPE/_MYSB/_MYSR` (33 nodes); Indonesia decomposes 13 families into
   `_IDJW/_IDSA/_IDKA/_IDEast` (51 nodes). Every decomposed family also keeps
   its un-suffixed base branch for the copper-plate regions (CORRECTION
   2026-07-06, §11.1 caveat — earlier "no base branch" text was an export
   artefact). **The main `LEAP Input Transformation.xlsx` export was
   region-scoped and contained ONLY Malaysia's variants** — Indonesia's were
   added by merging `LEAP Input Transformation Indonesia.xlsx` (2026-07-04).
   Centralized roster = **124 process nodes** (61 + 51 `_ID*` + 3 base
   Nuclear the Indonesia export surfaced + 9 base branches restored
   2026-07-06). **Confirmed by user 2026-07-04: only
   Indonesia + Malaysia are node-decomposed; the other 8 ASEAN regions are
   single copper-plate nodes.** **Methodology lesson (still applies to future
   areas):** to capture a region's node decomposition you must export from that
   region's context — a single export can't prove absence.
2. **Nodal decomposition is Malaysia + Indonesia** (Malaysia: 248 Transmission
   Nodes, 97% zero in the Malaysia export; Indonesia: its own `Transmission
   Nodes\Indonesia*` set across 4 grids). The `Key\Transmission` node set has
   10 country nodes (no sub-national node) yet Lines carry finer corridor names
   (P.Malaysia_Sumatra, Sarawak_Kalimantan) — line geography is finer than the
   Key-tree node set, but the generation tree IS sub-nationally decomposed for
   Malaysia and Indonesia.
3. **Timor Leste + Base Template are entirely unwired** (Node=0 across all 61
   processes); no `Key\Transmission\Nodes\Timor Leste` at all.
4. **Distributed rooftop solar bypasses transmission** — no `Node`, no
   `Transmission Nodes` children, `Dispatch Rule = FullCapacity`; never enters
   the nodal LP.
5. **Energy Sector Own Use hides its `\Processes\` wrapper** in the collapsed
   tree-view — the real path is `…\Energy Sector Own Use\Processes\<fuel>\…`; a
   naive path guess misses.
6. **Output Fuels is module-level** (a sibling of `Processes`), not a per-process
   child — 42 leaves across 28 modules, with the 4 crop-biofuel Output Fuels
   carrying a `Land Use` grandchild.

**§A.11 landmines (all present in canon)**

7. **Blending pseudo-tech `Exogenous Capacity = Unlimited`** — 528 rows (4
   techs × 12 × 11), the lower-bound `1.0e+12` forced-floor landmine,
   unremediated since the 2026-05-12 aeo9_v0.42 investigation and still present
   in aeo9_v0.67. In RAS they also show `Maximum Capacity = Unlimited`.
8. **Every process-level `Maximum Production = Unlimited`** — 9,072 rows
   (Gigajoule), the benign upper-bound sentinel on 100% of production techs
   (pollutes LP conditioning per §A.11). Plus ETD `Maximum Production =
   Unlimited` on the transmission process.
9. **Fossil supply carries caps but no costs** (`Maximum Production=Unlimited`,
   `Variable OM=0` on extraction) — the mirror of the Resources costs-without-
   caps gap (§13.4). The two full-plant processes (Gas Processing **and** Oil
   Refining All Refineries) are the exceptions that carry real conversion cost
   *(corrected — not Gas Processing alone; the LP does have a cost signal on the
   refinery route)*.

**Dead weight / unused knobs**

10. **Storage/dispatch panel is inert on 64 of 69 techs** (`Full Load Hours=0`);
    only the 5 real storage techs use it.
11. **Renewable Target = 0** on both electricity modules in every region/scenario
    — authored but unused (RE ambition enforced elsewhere).
12. **Planning Reserve Margin is a two-hop indirection** (`PRM for Simulated
    Scenarios[percent]` → a module-local variable), scenario-invariant across
    all 11 scenarios.
13. **Myanmar Peak Load Ratio silently falls back to flat 100** (missing
    `Myanmar_Hourly` shape) while the other nine derive from
    `PeakLoadRatioFromYearlyShape`.
14. **ETD Losses = 0 for Indonesia, Singapore, Timor Leste, Base Template**
    (Indonesia zero despite being the largest system); Laos/Malaysia/Thailand
    losses are single-point `Interp(2022, X)` constants dressed as time series;
    non-zero on 88 of 132 rows *(corrected from "99 rows")*.

**Naming / modelling oddities**

15. **SAF piggybacks on Renewable Diesel** — its only process is literally
    `HVO Renewable Diesel`, `CropYield=BioProdYield=0`, land-footprint EF
    branch-refs the RD Land Use.
16. **Ammonia's process is named `Hydrogen`** (after its feedstock, not its
    product) — a process→feedstock naming inversion.
17. **`Pressurized H2 Gas`** carries the full 35-var storage panel but zero
    feedstock/aux fuels — an H2 compression/storage pseudo-process, not a
    converter. (Note: this is the 5th storage tech, living under Hydrogen
    Production, not the electricity fleet — a grep for storage under Centralized
    alone misses it.)
18. **Self-referential module loop:** FAME Biodiesel + HVO Renewable Diesel
    consume Biodiesel as an auxiliary fuel via `Fuel Source =
    SourceModule(Biodiesel Production)` (84 rows) — all other feedstocks draw
    `SourceBelow` from Resources.
19. **Two capacity ontologies:** biofuel full-panel processes dimensioned in
    Million GJ/Year with Capital Cost in 2020 USD/(GJ/Year), vs the power tree's
    MW / Thousand USD/MW; and within the refinery, mixed physical bases
    (Exogenous Capacity in Thousand GJ/Yr, Historical Production in Thousand
    TOE, Capital Cost per GJ/Yr, Variable OM per TOE).
20. **Passthrough `Process Efficiency = 100`** on POME, Cassava, Sugarcane,
    Charcoal All Biomass — real loss pushed into the Land Use / crop-yield layer,
    so 100% here does not mean lossless.
21. **Blend energy-density literals** (`38.997/43.330` diesel, `26.744/44.8`
    ethanol/gasoline) are bare constants in the share expression with only a
    `? Energy contents taken from Fuels database` comment — no cited source; must
    stay in sync with the Fuels DB.

**Emissions tagging**

22. **`Minimum Utilization` is not uniformly 0** on biofuel processes — 50 of
    2,244 process-level rows carry `Interp(2023, X, 2030, 100)` must-run ramps
    (FAME/Molasses/Sugarcane/CME/Cassava, in Set up/LCO/RE LTRM ×3, for
    ID/MY/PH/TH) *(corrected)*.
23. **Biogenic-CO2 tagging is inconsistent:** crop-feedstock combustion CO2 is
    filed under fossil `Carbon Dioxide` (FAME Palm Oil 3.16, near-zero) while
    auxiliary Biodiesel/Charcoal biomass carry a separate `Carbon Dioxide
    Biogenic` leaf (5 leaves total vs 26 fossil-CO2 leaves).
24. **Organic Carbon appears on only 2 leaves, both in Charcoal** — Hydrogen
    Biomass Gasification carries 10 species (no Organic Carbon), not the full 11
    *(corrected — only Charcoal is 11-species)*.

**Attribution / hygiene**

25. **PRM `25 ? AEO6 assumption` belongs to Cambodia, not Brunei** *(corrected)*;
    Brunei's PRM is `Interp(2023, 21.00, …, 2027, 25.00) ? assumed value`.
26. **The 13 scenario-diverging grid combos carry 2 or 3 distinct expressions,
    not 1** *(corrected)*; `n_distinct_expr = 1` describes only the 248
    scenario-flat Nodal Distribution combos.
27. **`_x000D_` Excel carriage-return artefacts** inside comment strings (PRM
    provenance, Process Efficiency notes) — the same hygiene defect catalogued
    for the demand sectors (§14).
28. **`__NEMOcc` custom-constraint vars** (ASEANRenewableCapacityTarget,
    RenewableCapacityTarget — 120 rows each) are the only `__NEMOcc` presence in
    the tree; real RE-capacity-target data to preserve, not a diagnostic angle
    (§8-retired).

---

## 15. Data-hygiene ledger

Defects and oddities that any consumer of this area should know about,
ordered roughly by blast radius:

| # | Issue | Where | Size |
|---|---|---|---|
| 1 | `!Missing Branch (ID=…)!` dangling references | Industry FEI (IDs 3465/3466/3467, 3477/3478, 905, 825, 1687); Commercial FEI (IDs 1687, 825 — `Historical\Ethanol`/`Biodiesel` price branches) | 392 ind + 240 comm rows; 0 in transport/residential |
| 2 | `ScenarioValue(Bad Scenario [2], …)` dangling scenario reference | Industry AMS Target EI-reduction template | 19 rows |
| 3 | `Bad Unit [777518900]` / `[777691684]` corrupted unit strings | Industry FEI on the 20 Cement Clinker kiln-technology leaves | 2,640 rows |
| 4 | Unfitted Exp/Ln regression shells (`coefficients … must be determined via regression`, all coefficients = 1) | Commercial (1,620 all-1 + 40 fitted-but-commented: Electricity×Cambodia/Indonesia, LPG×Cambodia, Kerosene×Indonesia) + Industry (2,192 all-1 + 40 fitted-but-commented on 4 Historical fuels) | 3,892 flagged rows |
| 5 | `? ACE temp value` / placeholder intensities surviving into every substantive scenario | Commercial CUEI + end-use saturations (1,332 rows; only Brunei/Laos/Malaysia/Thailand carry cited overrides); residential `200 ?ACE Placeholder when no data`, `10 ? placeholder 14 IIEC`, `? uncalibrated assumed valuie` [sic] | ~1,400+ rows |
| 6 | `0 * Key\Macroeconomic\Manufacturing Fraction in Industry… ? Fill in historical data here` zero-stubs | Industry CA FEI | 213 rows |
| 7 | CCS sequestration factors tagged `?placeholder` (capture ramp 80→95%) | Industry Sequestered Carbon Dioxide leaves | 1,452 rows |
| 8 | NEMO/CPLEX solver output written back into authored expressions (`?Optimized on 07/02/2026 11:41 (NEMO/CPLEX)`) | Residential AC_/Refrigeration_ tier Activity Levels, RAS + CNZ | 360 rows |
| 9 | Scenario clones — six names / one expression set (per-sector membership in §2) + stale `Regional Aspiration Scenario test` prototype | all sectors | — |
| 10 | `Unlimited` literal on `Maximum Devices` / `Maximum Device Additions` | Residential device-stock tiers (demand-side device vars; distinct from the supply-side §A.11 1e12 trap, but the same export sentinel applies) | 1,512 rows × 2 vars |
| 11 | Road subtree has zero pollutant effect leaves (Air/IW/Rail have full sets) | Transport | — |
| 12 | `Motorcyle` misspelling on the 5 Road branches while `Key\TransportDataStock` spells `Motorcycle` correctly — the two trees disagree on the class name | Transport | 5 branches / 270 driver rows |
| 13 | `Demand\Transport_` (underscore) self-references vs exported `Demand\Transport` paths | Transport `TotShare_AltFuels`/`Share_FossilFuels` | 180 rows |
| 14 | `_x000D_` Excel carriage-return artifacts inside expressions | Commercial (280), Residential (1,263), Transport (10 FEI rows) | ~1,550 rows |
| 15 | Truck Natural Gas Fuel Economy discontinuity: CA=12 vs 5 in all 10 scenarios — Indonesia only, looks like an authoring slip | Transport | 10 rows |
| 16 | Unit drift within single variables: FEI in 3 unit systems (commercial kWh/m2 + Thousand TOE/m2 + Liter/m2; industry GJ/USD + GJ/t + kWh/t + Bad Unit); Demand Cost `2020 USD` vs `U.S. Dollar` vs per=`No data`; transport dollar vintages 2020 vs 2021 | all sectors | — |
| 17 | `Demand Cost` authored everywhere but ≈100% zeros; `RefHH` constant 1 everywhere — pure boilerplate | all sectors | ~106,000 + ~111,000 rows |
| 18 | Empty-leaf-name branch `Demand\Commercial\Data_Center\` (trailing backslash) | Commercial workbook tail | 1 branch |
| 19 | EF footnote letters `?a ?b ?c ?d` with no legend in any export | all sectors | ~370k+ rows carry `?` comments |
| 20 | Comment/authoring contradictions: SAF comment says "only available in AREC and ASER" but the expression is authored in 4 more scenarios; Thailand SAF carries a superseded expression inside a `??` comment; residential AC ownership has an undocumented `×2` multiplier with a dead alternative equation embedded in the comment | Transport, Residential | — |
| 21 | `Key\Industry\Cement RAS Measures\Clinker Fraction` is load-bearing in Current Accounts — "RAS Measures" keys are not RAS-only | Industry | — |
| 22 | Laos AC/Refrigeration saturations are single-point `Interp(2017, 50.84)` — constants dressed as time series | Commercial | 2 combos |
| 23 | 9,199 `Unlimited` rows on Resources upper bounds (5,671 Maximum Production + 3,528 Maximum Imports; zero on lower bounds). In RAS, Natural Gas + all 5 coals still Unlimited 12/12 — the fossil canonical authors costs but no caps (§13.3) | Resources | 9,199 rows |
| 24 | Zero-cost open supply/import routes (POME-lesson shape): 191 (fuel,region) pairs with MaxProd≠0 & Production Cost=0 (incl. Nuclear at Unlimited+$0); 95 pairs with open imports & Import Cost=0; 312 `0.001` placeholder Import Cost rows | Resources | ~600 pairs/rows |
| 25 | POME Import Cost exists in the area (RAS) but not in the bioenergy canonical — repo/area drift on the 2026-05-19 final-unlock fix | Resources vs `inject/bioenergy` | 1 variable |
| 26 | Comma-decimal committed expressions `*1,0551` (Philippines NG consumer prices) — §A.15/§A.20 decimal ambiguity in live authoring | Resources | 30 rows |
| 27 | `Minimum Imports` hold-last floors: historical Interp ending `2022, V>0` extends as a forced import floor into projection years (Singapore RFO 53,538 kTOE, …) | Resources, 7 optimization scenarios | 665 rows |
| 28 | `Key\Temp` scratch branch (units `temp`) carries live scenario signal — it is the only RE-Coupling-vs-Shared diff in the Key tree | Keys | 132 rows |
| 29 | Stale comment-only citations: `Key\Residential\AC\a`/`b` named in 232 residential rows but exist nowhere; the real `Key\Residential end use data_\AC\{a,b}` panels exist but are entirely uncited (§12.6) | Keys / Residential | 232 rows |
| 30 | Case/spelling hazards in Key paths: `Incumbent Generator DIspatch Phaseout` (capital "DI"), colliding near-duplicates `Key\Cal\Industry` (27 br) vs `Key\Industry\Cal` (6 br), deactivated `!Reactance`/`!Construction Year` variables, `Fraction`/`fraction`/`Factor`/`factor` unit drift | Keys | — |
| 31 | Perennial land cap unit-tagged `Cubic Meter` while Arable uses Thousand GJ (drift on the §2.4 1 GJ/ha anchor); both have Maximum Imports=Unlimited @ Import Cost 0 in optimization scenarios — free "land imports" if trade routes ever cover them | Resources | 2 branches |
| 32 | `Key\Optimized Trade` master switch: all 495 routes ON only in RAS+CNZ, OFF in the other 9 scenarios — while RE LTRM / AMS Target carry biofuel blend targets with routes disabled (§A.12 watch) | Keys | 5,940 rows/scenario |
| 33 | §11.2c must-run trap LIVE: 494 rows author bare `Minimum Utilization = Maximum Availability` on variable renewables (27 in RAS: Wind Onshore_MYPE/MYSB in 11 of 12 regions except Malaysia; full-12-region in RE-policy scenarios). Absent in CA/Baseline/AMS Target. Hedged pending capacity check (§14 §1.1) | Transformation (power) | 494 rows |
| 34 | Blending pseudo-techs (Gasoline/Diesel Blending) carry `Exogenous Capacity = Unlimited` → §A.11 1e12 forced floor (the 2026-05-12 p9 shape); + all-`Unlimited` `Maximum Production` on many Transformation processes | Transformation (fossil) | see §14 |
| 35 | Six power tech node-variants (Solar PV_MY*, Gas Turbine_MYPE, Large Hydro_MYPE, Wind Onshore_MYSR) show `Capital Cost = 0` + `Capacity Credit = 100` across regions — LEAP defaults on un-authored `_MY*` inheritance copies (§11.1 exported-view), real regional data not surfaced | Transformation (power) | — |

---

## Appendix — full branch trees

Machine-generated, one line per branch with its attached variables:

- [trees/commercial_tree.txt](trees/commercial_tree.txt) — 426 branches
- [trees/transport_tree.txt](trees/transport_tree.txt) — 165 branches
- [trees/residential_tree.txt](trees/residential_tree.txt) — 530 branches
- [trees/industry_tree.txt](trees/industry_tree.txt) — 5,859 branches
- [trees/keys_tree.txt](trees/keys_tree.txt) — 1,064 branches (`Key\`)
- [trees/resources_tree.txt](trees/resources_tree.txt) — 62 branches (`Resources\`)
- [trees/transformation_tree.txt](trees/transformation_tree.txt) — 1,593 branches (`Transformation\`)

These are the authoritative branch-path lists for authoring inject CSVs
against the `Demand\`, `Key\`, `Resources\`, and `Transformation\` trees of
`aeo9_v0.67_w_results` (per CLAUDE.md §A.20, Demand/KA-tree injects are
blind-mode mandatory).
