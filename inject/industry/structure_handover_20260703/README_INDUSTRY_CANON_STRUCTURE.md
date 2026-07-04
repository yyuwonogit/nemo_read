# Industry — Canonical LEAP Structure Handover (2026-07-03)

For the industry sector data team. You don't need LEAP, our repo, or any
database to use this package — everything referenced here is a plain
text/CSV file sitting next to this README.

## 1. What this package is

This is the **canonical structure** of the LEAP trees your data feeds,
exported directly from the live model (LEAP area `aeo9_v0.67_w_results`)
on 2026-07-02. It is the ground truth for branch names, variable names,
and units. Your CSVs must line up with these structures **exactly** —
any subsector, process/technology node, fuel branch, branch spelling, or
variable name that doesn't exist here gets filtered out by our import
adapter and never reaches the model.

A warning about scale up front: Industry is the **deepest and widest
tree in the whole model — 5,859 branches, 10 levels deep, 1,008,012 rows**
— but it carries only **10 distinct variables**. It is huge because the
same handful of variables is repeated across thousands of pollutant
leaves and process nodes, not because there are thousands of things to
author. The panel you actually author (§3) is small.

Files in this package:

| File | What it is |
|---|---|
| `industry_tree.txt` | The full `Demand\Industry` branch tree (5,859 branches), indented, with each branch's variables listed |
| `industry_branch_variables_units.csv` | One row per (branch, variable): units, scale, per — the authoritative unit reference |
| `keys_slice_industry.txt` | The industry-relevant slice of the `Key\` assumptions tree (117 branches: `Key\Industry\*` + the `Key\Macroeconomic` and `Key\Energy Access` drivers you depend on) — where your intensity, share, and calibration data actually lands |
| `keys_slice_industry_units.csv` | Units for that Key slice |
| `resources_slice_industry_units.csv` | The `Resources\` supply/price slice for the 15 fuels industry consumes/prices (context: where coal, gas, oil products, electricity, biomass etc. are supplied and priced) |
| `current_expressions_industry_4scenarios.csv` | **What is currently written in the model** for every `Demand\Industry` branch — the live expressions, scoped to the 4 scenarios that matter (see §6b) |
| `current_expressions_keys_slice_4scenarios.csv` | Same, for the industry Key slice (`Key\Industry\Intensity`, `Subsector_share`, `Cal`, Steel/Cement RAS Measures, plus the macro drivers) |
| `current_expressions_resources_slice_4scenarios.csv` | Same, for the 15 Resources fuels above (context only — you don't author these) |

How to read them: in the `.txt` trees, indentation = depth, and the
`[vars: ...]` suffix lists the variables carried on that branch. In the
CSVs, `branch_path` is the full LEAP path (backslash-separated),
`units`/`scale`/`per` together give the unit (e.g. units=`GJ`, or
units=`Metric Tonne`, scale=`Thousand`).

## 2. Your tree in brief — Historical accounting + a projection engine

`Demand\Industry` splits at level 3 into a **`Historical`** accounting
subtree and a **`Projection`** subtree, hand-switched at 2025 by a pair
of complementary `Step()` activity switches (the `Historical` node runs
`Step(2005, 100, 2025, 0)`, the `Projection` node runs
`Step(2005, 0, 2025, 100)`). Everything year ≤ 2024 comes from
`Historical`; everything from 2025 onward comes from `Projection`.

- **`Historical`** — 28 flat fuel-accounting branches (Bagasse, Biodiesel,
  Biogas, Bitumen, Brown Coal Briquettes, the coals, Diesel, Electricity,
  Natural Gas, …), each carrying a `Final Energy Intensity` + `Fuel Share`
  + the custom `TotalEnergy` calibration total, with 12–13 pollutant
  leaves under each combustible fuel.
- **`Projection`** splits again into **`End Use`** (the real demand
  engine) and **`Electricity Appliances`** (a parallel accounting tree,
  §6 note).

### 2.1 The 10 End Use subsectors

`Projection\End Use` holds ten subsectors:

**Cement · Chemical · Construction · Food Beverages and Tobacco · Iron and
Steel · Mining · Other Industry · Other Non Metallic Minerals · Pulp and
Paper · Textile and Leather.**

**Eight of the ten** use a uniform generic pattern:

```
<Subsector>\Direct Process Heating \{Electricity | Liquid FF | Others}\<fuel leaves>
<Subsector>\Indirect Process Heating\{Electricity | Liquid FF | Others}\<fuel leaves>
```

Each `<carrier group>` (Electricity / Liquid FF / Others) carries an
`Activity Level` + `Final Energy Intensity`; the fuel leaves below carry
`Final Energy Intensity` + `Fuel Share`.

**Two subsectors get bespoke physical-production chains** (this is where
industry is unlike the other demand sectors — activity is in physical
tonnes, not energy):

**Cement** — a clinker chain, four kiln technologies:

```
Cement\Clinker\{Cement Kiln CCS | Cement Kiln Conventional |
                Oxyfuel Biomass CCS | Oxyfuel Gas CCS}
   \Electricity\Electricity
   \Heat\{Biomass | Coal Bituminous | Municipal Solid Waste |
          Natural Gas | Residual Fuel Oil}
   \Non Energy\Non Energy
```

The CCS/Oxyfuel kilns carry `Sequestered Carbon Dioxide` pollutant leaves
(a negative loading — see §7).

**Iron and Steel** — steelmaking routes:

```
Iron and Steel\Crude Steel\BOF\{BF | BF CCS}\<fuel leaves>
Iron and Steel\Crude Steel\EAF\{Scrap | DRI | DRI H2}\<fuel leaves>
Iron and Steel\Casting\<fuel leaves>
Iron and Steel\Hot Rolling\<fuel leaves>
```

BOF (Basic Oxygen Furnace) runs the blast-furnace routes `BF` and
`BF CCS`; EAF (Electric Arc Furnace) runs `Scrap`, `DRI`
(direct-reduced iron) and `DRI H2` (hydrogen-DRI). These map one-to-one
onto the `Key\Industry\Intensity\Iron and Steel\...` and Steel RAS
Measures branches (§6).

### 2.2 Electricity Appliances (parallel tree — read, don't author twice)

`Projection\Electricity Appliances` is a **parallel accounting tree**,
not a second demand engine. Each `<subsector>\Electricity` leaf carries a
custom `Total Energy` reading that pulls the End Use **result** back out
via `Key\Industry\Appliances_share\<subsector>` — its job is to attach
hourly load shapes to the electric share of demand. Do not author fresh
demand here; if you have appliance-share data it goes into
`Key\Industry\Appliances_share`, not into a duplicate demand series.

## 3. The variables you author

Only 10 variables exist in this whole tree. From
`industry_branch_variables_units.csv` (the full list is there; this is
the panel your data actually feeds):

| Variable | Unit(s) | Where | Notes |
|---|---|---|---|
| Final Energy Intensity | Thousand TOE (Historical); GJ/USD, GJ/tonne (Projection) | fuel leaves + carrier-group nodes | the core intensity number; in Projection it is a product of a `Key\Industry\Intensity` trajectory × a `Key\Industry\Cal` factor (§6) |
| Fuel Share | % Share | fuel leaves | must sum to 100 across sibling fuels under a carrier group / kiln heat node; last sibling usually `Remainder(100)` |
| Activity Level | Million 2021 USD (GDP-driven subsectors); Million/Thousand Metric Tonne (Cement, Iron and Steel physical activity); % Share / Saturation (tech-share nodes) | category + process nodes | subsector activity, technology shares |
| Avg Environmental Loading | kg/TJ, t/TJ, kg/t, kg/kg | pollutant leaves | emission factors (§7) — 5,259 of the 5,859 branches are pollutant leaves |
| Total Energy | GJ | Electricity Appliances leaves | result-feedback for load shapes (§2.2) — do not hand-author |
| TotalEnergy | Thousand TOE | `Historical` root | historical total-FEC calibration series per region |
| UnscaledFuelShare | % | `Historical` fuel leaves (CA-only) | a fuel-share helper; **dead machinery** in industry — nothing references it, ships for parity with commercial |
| Fuel Share, FEI (Historical) | as above | Historical fuel leaves | parked historical consumption; inert from 2025 (Historical activity is `Step()`'d to 0) |
| Load Shape | Percent | 16 electric fuel leaves | `YearlyShape(<Country>_Hourly)` |
| Demand Cost | 2020 USD | every category/tech branch | **constant 0 boilerplate everywhere** — carries no information |
| RefHH | Ref/hh | every category/tech branch | constant 1 boilerplate — carries no information |

The two you will spend nearly all your effort on are **Final Energy
Intensity** (via the Key intensity trajectories, §6) and **Activity
Level / Fuel Share** on the Cement and Iron-and-Steel physical chains.

## 4. Expression conventions (non-negotiable)

Values enter LEAP as expressions. The house rules:

- **`Interp(year, value, year, value, ...)`** — COMMA between items,
  PERIOD as the decimal mark. `Interp(2025, 3.2422, 2030, 3.0833)` is
  right; semicolons or comma-decimals (`3,2422`) are wrong and will be
  rejected before import. (`Data(year, value, ...)` is the equivalent
  year-pair form used heavily in Historical series — same comma/period
  rule.)
- **`InterpFSY(year, value, ...)`** — like Interp but anchored at the
  first scenario year; the house style for policy targets. The Steel/
  Cement RAS Measures use it, e.g. `Oxyfuel Gas CCS =
  InterpFSY(2030, 0, 2035, 0.5, 2040, 3, 2045, 8, 2050, 13, 2055, 17,
  2060, 20)`.
- **`Remainder(100)`** — the last sibling in any share partition (last
  fuel under a kiln Heat node, last technology under a route) closes the
  partition to 100 %. Your other siblings must be authored so this is
  meaningful.
- **`GrowthAs(driver)`** — the industry activity switch. In every
  projection scenario, subsector activity is authored as
  `GrowthAs(Key\Macroeconomic\Real GDP Industry)` — activity grows in
  lockstep with the industrial GDP driver. This is the industry-specific
  idiom (1,440 rows); it does not appear in the other demand sectors.
- **`? comment` provenance** — anything after a `?` in an expression is a
  comment. We encourage these for source citations, e.g.
  `94.6 ?a` or `... ? source: ERIA 2022`. Name the actual source (ERIA,
  IEEJ, national statistics, ministry decree number). **Do not** hide a
  placeholder confession in a comment and leave it live (§7).
- **Never write the literal word `Unlimited`** in anything you author. It
  becomes a broken numeric sentinel downstream. If something needs a
  generous cap, use a large number. (The Key and Demand-Industry trees
  are clean of `Unlimited` today — keep them that way.)

## 5. Scenarios and regions — where your data lands

The model carries 11 scenarios, but for industry they collapse into a
few real cases (verified by our divergence analysis):

- **Current Accounts (CA)** — historical statistics (everything year ≤
  2024). Carries the CA-only calibration rows (`UnscaledFuelShare` on 27
  of the 28 Historical fuels). Base-year and historical data lands here.
- **Baseline Simulation** — no-policy projection; closest to CA. In
  industry it re-authors Historical FEI as price/GDP regression shells
  (see §7 — most are unfitted).
- **Regional Aspiration Scenario (RAS)** — the main policy projection and
  the scenario the solver optimizes. In industry, `Set up`, `LCO backup`,
  and the three `RE LTRM` scenarios are **expression-identical to the
  Set-up bloc**, and **`Carbon Neutrality / Net Zero` is expression-
  identical to RAS** in the demand-industry tree (0 differing rows). So a
  correction you make to RAS propagates widely.
- **AMS Target Scenario (ATS)** — policy-bloc anchor; a small number of
  rows differ from the Set-up bloc.

The decarbonization content (Steel/Cement RAS Measures, CCS ramps) lives
in **RAS and Carbon Neutrality** only.

Regions: the 12 region slots are the 10 ASEAN member states plus **Base
Template** (a LEAP template holding default values — NOT a country; you
never author data for it) and **Timor Leste**. Timor Leste currently
holds template-grade defaults and is disabled in the calc; if/when you
have Timor Leste data, send it as a **separate supplement file**, never
mixed into the main 10-country data.

**Regional authoring reality:** the industry projection engine is
authored **once for all 12 regions** — 98.9 % of (branch, variable)
combinations are region-uniform. Genuine per-country data lives almost
entirely in: Historical fuel shares and totals, Cement and Iron-and-Steel
**physical activity** (per-country tonnes), and load shapes. If you have
country-specific intensities or tech shares, that is exactly the
high-value data the template is currently missing.

## 6. KEY CONNECTIONS — the second tree your data feeds (important)

Your intensity and share data does NOT go directly onto the
`Demand\Industry` branches. It lands in a separate assumptions tree,
`Key\Industry`, and the Demand branches *pull from it by formula*.
Verbatim shape from the live model:

```
Projection\End Use\Chemical\Direct Process Heating\Electricity:Final Energy Intensity =
  Key\Industry\Intensity\Chemical\Direct Process Heating\Electricity:Activity Level[GJ/USD]
  * Key\Industry\Cal\Electricity:Activity Level[Fraction]
```

So the number you research (the intensity trajectory) goes into
`Key\Industry\Intensity\...`, and it is multiplied at the Demand branch by
a `Key\Industry\Cal\...` **calibration factor** (the idiom that ties the
projection back to the calibrated historical base year). This
**Intensity × Cal** calibration idiom is the single most important thing
to understand about authoring industry — you author the physical
trajectory, we (or you) maintain the Cal anchor.

`keys_slice_industry.txt` carries the 117 Key branches you touch:

| Sub-tree | Branches | Holds |
|---|---|---|
| `Key\Industry\Intensity\<subsector>\...` | 84 | fuel-level intensity trajectories (GJ/USD and GJ/tonne), including the BF / BF CCS / DRI / DRI H2 / Scrap steel routes and the 4 cement kiln techs |
| `Key\Industry\Subsector_share\<subsector>` | 9 | how industrial GDP splits across the subsectors |
| `Key\Industry\Appliances_share\<subsector>` | 8 | electric-appliance share feeding the Electricity Appliances tree (§2.2) |
| `Key\Industry\Cal\{Electricity, Liquid FF, Others, Cement, Iron and Steel, Total_}` | 6 | the calibration factors in the Intensity × Cal idiom |
| `Key\Industry\Steel RAS Measures\...` | 4 | decarbonization levers (BOF_share, EAF hydrogen adoption rate, …) — RAS/CNZ only |
| `Key\Industry\Cement RAS Measures\...` | 2 | CCS Adoption, Clinker Fraction — RAS/CNZ only |

Plus the **shared exogenous spine** your sector depends on (also in the
slice):

| Branch | Role |
|---|---|
| `Key\Macroeconomic\Real GDP Industry` | THE activity driver — every subsector's `GrowthAs()` and `Subsector_share × GDP` is wired to this |
| `Key\Macroeconomic\Gross Fixed Capital Formation` | investment driver referenced by industry FEI regressions |
| `Key\Macroeconomic\Manufacturing Fraction in Industry` | manufacturing split; referenced by the "Fill in historical data here" stubs (§7) |
| `Key\Energy Access\Electrification Rate` | referenced across industry electricity intensities |

**Resources context**: `resources_slice_industry_units.csv` shows the
supply/price side of the 15 fuels your sector consumes (the coals,
Natural Gas, Diesel, Gasoline, Kerosene, LPG, Residual Fuel Oil,
Electricity, Bagasse, Biomass, Wood, Municipal Solid Waste). You don't
author it, but it tells you which fuels the model can actually supply —
and it is where the **consumer-price** values your FEI regression shells
reference live (a cross-tree issue flagged in the anomaly audit).

### Boundary note — Transformation-side is pending export

This handover covers the `Demand\Industry` tree, its `Key\Industry`
drivers, and the Resources price context. It does **not** cover the
Transformation side (the conversion/process supply that actually
produces steel, clinker, hydrogen, etc. as commodities). Any
process-authoring that belongs on Transformation branches is a **pending
Transformation export** — flag it in your cover note and we will route
it separately once that export exists. Don't try to hand-build
Transformation paths from this package.

## 6b. What is currently written in the model — for your review

The three `current_expressions_*_4scenarios.csv` files are a full dump of
the expressions **currently authored in the live model** for your
branches, so your team can judge what to keep, correct, or replace.

- **Scope: four scenarios only** — `Current Accounts` (historical),
  `Baseline Simulation`, `AMS Target Scenario` (ATS), `Regional
  Aspiration Scenario` (RAS). The other seven scenarios are copies,
  derivatives, or internal plumbing (in industry, Set up / LCO backup /
  RE LTRM ×3 equal the bloc, and Carbon Neutrality equals RAS) — ignore
  them; any correction you make to these four propagates to their clones.
- **Reading the region column**: `ALL (12 regions)` means every country
  currently holds the same expression (a template value — often exactly
  the thing worth replacing with country data). A named country means
  that row is country-specific. In this dump, roughly 30,000 of ~35,000
  industry rows are `ALL (12 regions)` — the sector is overwhelmingly
  templated, so most of the review targets are the `ALL` rows.
- Columns: `branch_path, variable, scenario, region, expression, units,
  scale, per`. Expressions may carry `? comments` citing their source —
  that tells you where the current number came from.
- What we'd like back: for any row where you have better data, a note
  with the branch path, scenario, country, your proposed value/series,
  and the source. Template rows (`ALL`) holding round placeholder numbers,
  `? Fill in historical data here` stubs, and unfitted regression shells
  are the highest-value targets (§7).

## 7. Known issues in your tree — we'd like your input

Review requests, not blame — most of these predate everyone involved.
The full, faithful list (with counts and severity grades) is in the
companion file `ANOMALY_AUDIT_INDUSTRY_20260704.md`; this is the short
version of what needs your data specifically:

1. **`Bad Unit` on Cement Clinker Heat FEI.** The `Final Energy Intensity`
   on the Cement Clinker Heat fuel leaves (Coal Bituminous, Biomass, MSW,
   Natural Gas, RFO under each kiln) carries a corrupted unit tag —
   `Bad Unit [777518900]` / `Bad Unit [777691684]` — in every scenario
   (240 rows/scenario, 960 in the 4-scenario scope). We need the intended
   unit (GJ per tonne clinker?) so we can re-tag these. Please confirm.
2. **"Fill in historical data here" stubs.** 214 rows read
   `0 * Key\Macroeconomic\Manufacturing Fraction… ? Fill in historical
   data here` — zero-valued FEI awaiting real data. Which subsectors/
   fuels do these cover, and can you supply the historical FEC?
3. **Unfitted regression shells.** 643 rows carry
   `Exp(1*Ln(<price>) + 1*Ln(<GDP driver>) + 1) ? … determined via
   regression` with every coefficient still at the placeholder `1` — the
   econometric price/GDP intensity model was never fitted. If your team
   fits these, send coefficients per subsector/fuel; otherwise these
   evaluate to garbage.
4. **CCS Sequestered-CO2 ramps are placeholders.** 528 rows carry
   `-<factor> * Interp(2030, 0.8, 2045, 0.9, 2055, 0.95) ?placeholder`
   capture ramps (80→95 %). Are those capture-rate trajectories your
   assumption, or should they be replaced?
5. **`!Missing Branch` + `Bad Scenario [2]` in the EI-reduction template.**
   The industry Historical-fuel FEI EI-reduction template resolves
   dangling branch and scenario references (`InterpFSY(!Missing Branch
   (ID=3477)!, ScenarioValue(Bad Scenario [2], …))`), live in AMS Target
   (140 + 19 rows). Likely inert (Historical activity is `Step()`'d to 0
   after 2025) but it should be repaired or removed; tell us if it was
   meant to carry a real BAU-reduction number.
6. **Demand Cost = 0 everywhere.** 28,800 rows of `Demand Cost` are the
   constant `0` boilerplate. If industry demand should carry a cost, this
   is where it would go — currently it carries nothing.
7. **Consumer-price exposure (upstream).** The FEI regression shells (item
   3) reference Resources consumer prices that are ~95 % zero (Bagasse,
   the coals, Natural Gas, MSW Industrial Consumer Price all read 0/44).
   `Ln(0)` is undefined, so fuel-switching response is silently priced at
   zero. **These prices live in the Resources tree, owned by the fossil/
   central team** — flag them there; we note it here because it directly
   breaks your regressions.

## 8. What to send back, and in what shape

Same delivery shape as your previous drops — CSVs using YOUR source-side
names (we do all mapping to LEAP names; never hand-build LEAP branch
paths). At minimum:

1. `intensity.csv` — Country × Year × subsector × process
   (Direct/Indirect Process Heating) × carrier (Electricity/Liquid FF/
   Others) × fuel × intensity value, with `unit` and `source`. This feeds
   `Key\Industry\Intensity`.
2. `subsector_share.csv` — Country × Year × subsector share of industrial
   GDP (feeds `Key\Industry\Subsector_share`).
3. `cement_steel_physical.csv` — Country × Year physical production
   (clinker tonnes, crude-steel tonnes) and the technology/route shares
   (kiln mix, BOF vs EAF vs DRI vs DRI H2), with `source`. This is the
   per-country data the template most lacks.
4. `fuel_shares.csv` — Country × Year × (carrier group or kiln Heat node)
   × fuel share, summing to 100 per node.
5. Any fitted **regression coefficients** for the Exp/Ln FEI shells (item
   §7.3), per subsector/fuel, if your team fits them.

Every row should carry a source/provenance column. Anything with Year ≤
2024 is treated as historical (lands in Current Accounts). Combinations
the model doesn't have branches for will be dropped with a log entry — if
you believe the model SHOULD cover a subsector/route/fuel it doesn't,
say so explicitly in your cover note and we'll raise it as a
model-structure request instead. Transformation-side process authoring
(§6 boundary note) is pending a separate export — flag it, don't force it
into these files.

Questions → yudiandra.y@gmail.com. Please reference branch paths as they
appear in `industry_tree.txt` when reporting structure issues.
