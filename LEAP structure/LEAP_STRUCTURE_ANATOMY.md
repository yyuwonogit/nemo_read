# LEAP Demand-Tree Anatomy — `aeo9_v0.67_w_results`

> **What this is.** A structural digest of the six export workbooks in this
> folder — `LEAP Input {Commercial, Transport, Residential, Industry}.xlsx`
> (the `Demand\` subtrees), `LEAP Input Keys.xlsx` (the `Key\` assumption
> tree), and `LEAP Input Resources.xlsx` (the `Resources\` supply tree) — all
> exported from LEAP area **`aeo9_v0.67_w_results`**. Generated 2026-07-02 by
> converting all 1,858,572 export rows to flat CSVs offline and analysing
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
(12/13), Demographic (7/8), Macroeconomic (10/17), Energy Access (2/2).
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

## 14. Data-hygiene ledger

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
| 32 | `Key\Optimized Trade` master switch: all 495 routes ON only in RAS+CNZ, OFF in the other 9 scenarios — while RE LTRM / AMS Target carry biofuel blend targets with routes disabled (§A.12 watch; hypothesis, Transformation wiring not visible) | Keys | 5,940 rows/scenario |

---

## Appendix — full branch trees

Machine-generated, one line per branch with its attached variables:

- [trees/commercial_tree.txt](trees/commercial_tree.txt) — 426 branches
- [trees/transport_tree.txt](trees/transport_tree.txt) — 165 branches
- [trees/residential_tree.txt](trees/residential_tree.txt) — 530 branches
- [trees/industry_tree.txt](trees/industry_tree.txt) — 5,859 branches
- [trees/keys_tree.txt](trees/keys_tree.txt) — 1,064 branches (`Key\`)
- [trees/resources_tree.txt](trees/resources_tree.txt) — 62 branches (`Resources\`)

These are the authoritative branch-path lists for authoring inject CSVs
against the `Demand\`, `Key\`, and `Resources\` trees of
`aeo9_v0.67_w_results` (per CLAUDE.md §A.20, Demand/KA-tree injects are
blind-mode mandatory).
