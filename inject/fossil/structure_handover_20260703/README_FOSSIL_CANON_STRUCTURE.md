# Fossil Energy — Canonical LEAP Structure Handover (2026-07-03)

For the fossil-fuels data team. You don't need LEAP, our repo, or any
database to use this package — everything referenced here is a plain
text/CSV file sitting next to this README.

## 1. What this package is

This is the **canonical structure** of the LEAP supply tree your data
feeds, exported directly from the live model (LEAP area
`aeo9_v0.67_w_results`) on 2026-07-02. It is the ground truth for
branch names, variable names, and units. Your CSVs must line up with
these structures **exactly** — any fuel spelling, variable name, or
unit that doesn't exist here gets filtered out by our import adapter
and never reaches the model.

Files in this package:

| File | What it is |
|---|---|
| `resources_tree.txt` | The full `Resources\` branch tree (62 fuels: 29 Primary + 33 Secondary), with each fuel's variables listed |
| `resources_slice_fossil_units.csv` | One row per (fuel, variable): units, scale, per — the authoritative unit reference. Covers the whole Resources tree; your fossil fuels are a subset of it |
| `current_expressions_resources_4scenarios.csv` | **What is currently written in the model** for every Resources fuel — the live expressions, scoped to the 4 scenarios that matter (see §6b) |

How to read them: the `.txt` tree is a flat list — one line per fuel,
with the `[vars: ...]` suffix listing the variables carried on that
fuel. The tree file itself does not mark which fuels are Primary vs
Secondary; read that off the `branch_path` column in the CSVs (your
fossil fuels' assignments are also in the §2 table). In the CSVs,
`branch_path` is the full LEAP path (backslash-separated), and
`units`/`scale`/`per` together give the unit (e.g. units=`Metric
Tonne`, scale=`Thousand`; or units=`2020 USD`, per=`Barrel`).

One boundary to know up front: this package covers the **Resources
tree only** — the supply caps, reserves, and cost/price layer. The
`Transformation` tree (refineries, extraction/processing plants, power
plants) has **not yet been exported** — anywhere this README says
"pending Transformation export", that content will come in a follow-up
package. Do not guess Transformation branch names in your files.

## 2. Your tree in brief — a flat grid of fuels

`Resources\` is completely flat: every fuel is a single leaf under
`Resources\Primary\` or `Resources\Secondary\`, with no children. Each
fuel carries the same base panel of 15 variables, and a few fuel
families add extras. The fossil view:

| Group | Fuels | Variable panel |
|---|---|---|
| Primary hydrocarbons (8) | Coal Anthracite, Coal Bituminous, Coal Lignite, Coal Sub bituminous, Coal Unspecified, Crude Oil, Natural Gas, Natural Gas Liquids | base 15 + `Base Year Reserves` + `Additions to Reserves` + `Export Load Shape` (18) |
| Nuclear (1) | Nuclear | base 15 + the reserves pair, no Export Load Shape (17) |
| Secondary petroleum/coal products (~20) | Avgas, Bitumen, Blast Furnace Gas, CNG, Coke Oven Gas, Diesel, Gasoline, Hard Coal Briquettes, Jet Kerosene, Kerosene, LNG, LPG, Lubricants, `Metalurgical Coke` (LEAP's spelling — author it verbatim), Naphtha, Oil, Petroleum Coke, Refinery Feedstocks, Refinery Gas, Residual Fuel Oil | base 15; most add `Export Load Shape` (16). The 5 without it: Blast Furnace Gas, CNG, Coke Oven Gas, Hard Coal Briquettes, Metalurgical Coke |

The other fuels in the tree (crops, biofuels, renewables, the blended
road fuels) belong to the bioenergy and power teams — they're in the
files for context, not for you to author.

Note the road-fuel split: plain `Gasoline` / `Diesel` are YOUR refined
products; `Blended Gasoline` / `Blended Diesel` are the downstream
ethanol/biodiesel blends owned by the bioenergy side. Demand sectors
consume the blended products; your fuels feed the blend.

## 3. The variables you author

The base 15-variable panel, plus the fossil extras (full unit detail
per fuel in `resources_slice_fossil_units.csv`):

| Variable | What it is | Notes |
|---|---|---|
| Maximum Production | national production cap per year | **the headline gap — see §7.1.** Units: Petajoule for Crude Oil; Gigajoule for the 5 coals, Natural Gas, NGL, Nuclear and the Secondary products |
| Minimum Production | production floor | currently literal `0` everywhere — keep it that way unless you have a defensible floor |
| Maximum Imports / Minimum Imports | import cap / floor, used by the optimized scenarios | Minimum Imports carries historical series that act as forced floors — see §7.2 |
| Production Cost | cost per unit produced | e.g. USD per Metric Tonne (coals), 2020 USD per Barrel (Crude Oil), USD per MMBTU (gas) — check the units CSV per fuel, the per-unit differs |
| Import Cost | cost per unit imported | 2020 USD per Metric Tonne (coals) / Barrel (oil products); the gas family (Natural Gas, NGL, LNG, CNG, LPG) is per MMBTU — check the units CSV per fuel |
| Export Benefit | revenue per unit exported | |
| Imports / Exports | historical trade series (accounting) | mostly Thousand Tonnes of Oil Equivalent; Nuclear and the 5 products without Export Load Shape are in Gigajoule (as is Coal Sub bituminous's Exports) — check the units CSV per fuel |
| Base Year Reserves | proven reserves at base year | currently all zero — see §7.3 |
| Additions to Reserves | reserve additions by year | `Data(year, value)` point series — see §7.3 |
| Residential / Commercial / Industrial / Other Consumer Price | end-user prices by sector | 2011 USD / GJ; mostly zero except a few countries' historical series |
| Unmet Requirements / Cost of Unmet Requirements / Export Load Shape | model plumbing | ours to maintain; listed so the files make sense |

## 4. Expression conventions (non-negotiable)

Values enter LEAP as expressions. The house rules:

- **`Interp(year, value, year, value, ...)`** — COMMA between items,
  PERIOD as the decimal mark. `Interp(2025, 53538.23, 2030, 51000)` is
  right; semicolons or comma-decimals (`53538,23`) are wrong and will
  be rejected before import. (The model currently contains a few
  comma-decimal rows — see §7.5 — which is exactly why we now enforce
  this.)
- **`? comment` provenance** — anything after a `?` in an expression
  is a comment. We encourage these for source citations, e.g.
  `Data(2025, 30, ...) ? Malampaya condensate deep-water proxy; EIA
  Philippines country profile` (a live row in the model). Name the
  actual source (EIA, national statistics office, ministry, company
  annual report).
- **`Data(year, value, ...)`** — point values with no interpolation
  between them; the established form for reserve additions and other
  observation-style data.
- **Never write the literal word `Unlimited`** in anything you author.
  It becomes a broken numeric sentinel downstream. If a cap genuinely
  needs to be non-binding, use a generous finite number in the fuel's
  own unit.
- State your unit basis explicitly in your files (tonnes vs TOE vs GJ
  vs barrels, and which dollar vintage). We convert to the LEAP unit
  in the units CSV; ambiguous units are the single biggest source of
  rework.

## 5. Scenarios and regions — where your data lands

The model carries 11 scenarios, but only 4 matter for review (the
other 7 are copies, derivatives, or internal plumbing):

- **Current Accounts** — historical statistics (the accounting base).
  `Base Year Reserves` exists only here.
- **Baseline Simulation** — no-policy projection.
- **AMS Target Scenario (ATS)** — member-state targets.
- **Regional Aspiration Scenario (RAS)** — the main optimized policy
  case. This is the scenario NEMO (the optimizer) actually solves, so
  caps and costs here carry the most weight. RAS is also the only one
  of the four that carries `Maximum Imports` / `Minimum Imports` —
  those variables exist only in the optimized scenario family, while
  the accounting scenarios carry the historical `Imports` series
  instead.

Regions: the 12 region slots are the 10 ASEAN member states plus
**Base Template** (a LEAP template holding default values — NOT a
country; you never author data for it) and **Timor Leste**. Timor
Leste currently holds template-grade defaults and is switched off in
the model calculation; if/when you have Timor Leste data, send it as a
**separate supplement file**, never mixed into the main 10-country
data.

## 6. Key-tree connections — none (audited, not omitted)

Other sector packages ship a slice of the `Key\` assumptions tree
because their demand branches pull values from it by formula. Yours
does not, deliberately: we mechanically audited every expression on
the fossil Resources fuels and found **zero references to the `Key\`
tree** — no fossil supply cap, cost, or price is driven by a Key
assumption. What your fuels DO connect to:

- **Demand sectors** reference some of your Consumer Price variables
  (e.g. industry regressions read `Industrial Consumer Price` on coal
  and gas) — mostly resolving to zero today, see §7.6.
- **Transformation** (refineries turning Crude Oil into Diesel,
  Gasoline, Kerosene, LPG, Residual Fuel Oil; extraction processes;
  power plants burning your fuels) — *pending Transformation export*;
  the process-level detail will come in a follow-up package.
- A handful of cross-fuel pulls inside Resources itself (e.g. some
  Import Cost rows reference `Coal Bituminous:Import Cost[2020
  USD/Tonne]` from another coal grade).

## 6b. What is currently written in the model — for your review

`current_expressions_resources_4scenarios.csv` is a full dump of the
expressions **currently authored in the live model** for every
Resources fuel, so your team can judge what to keep, correct, or
replace.

- **Scope: four scenarios only** — Current Accounts, Baseline
  Simulation, AMS Target Scenario, Regional Aspiration Scenario. Any
  correction you make to these four propagates to the derivative
  scenarios.
- **Reading the region column**: `ALL (12 regions)` means every
  country currently holds the same expression (a template value —
  often exactly the thing worth replacing with country data). A named
  country means that row is country-specific.
- Columns: `branch_path, variable, scenario, region, expression,
  units, scale, per`. Expressions may carry `? comments` citing their
  source — that tells you where the current number came from. (Some
  comments contain `_x000D_` artifacts — an export leftover, ignore.)
- What we'd like back: for any row where you have better data, a note
  with the branch path, scenario, country, your proposed value/series,
  and the source. Rows marked `ALL (12 regions)` holding `Unlimited`
  or `0` are the highest-value targets.

## 7. Known issues in your fuels — we'd like your input

Review requests, not blame — some of these predate everyone involved:

1. **THE HEADLINE: Natural Gas and all 5 coals have `Maximum
   Production = Unlimited` in all 12 regions, in every scenario.**
   Verbatim from the extract: `Resources\Primary\Natural Gas, Maximum
   Production, Regional Aspiration Scenario, ALL (12 regions),
   Unlimited` — and the same for Coal Anthracite / Bituminous /
   Lignite / Sub bituminous / Unspecified. Your team's data currently
   sets production and import **costs** for these fuels but no
   **caps**, so the optimizer treats every country as able to produce
   unlimited gas and coal domestically, limited only by cost. Worse,
   for several non-producing countries that cost is an authored zero —
   e.g. Singapore Natural Gas and most countries' Coal Bituminous hold
   `Production Cost = Interp(2024, 0, 2060, 0)` — making the supply
   unlimited AND free. A `0` cap for genuine non-producers fixes both
   at once. Besides
   being unrealistic (Singapore does not mine coal), the literal
   `Unlimited` is the broken sentinel from §4. **This is the single
   most valuable thing you can send: defensible national production
   caps/trajectories (or a documented "effectively uncapped, use
   value X") per country for Natural Gas and each coal grade, with
   sources.** Crude Oil already has authored caps (Petajoule) — the
   same treatment is what we need for gas and coal (Gigajoule).
2. **`Minimum Imports` historical floors that never end.** 95
   fuel-region pairs (665 rows across the full optimized scenario
   family; the RAS slice in your extract shows the 95) carry
   historical import series ending at a positive 2022 value — e.g.
   Singapore Residual Fuel Oil ends `2022, 53538.23` (Thousand TOE),
   Singapore Crude Oil `2022, 50159.96`, Thailand Crude Oil `2022,
   47230`. LEAP holds the last value forward, so these act as
   **forced import floors of that size in every projection year to
   2060**. For a refinery hub like Singapore a crude-import floor may
   be intended — but please review the list: which of these are
   deliberate refinery-feed floors, and which are just historical
   series that should stop binding after 2022? To pull the list
   yourself: filter the extract to `variable = Minimum Imports` (all
   such rows sit in the Regional Aspiration Scenario) and keep the
   rows whose series ends at a positive 2022 value — 95 of the 304
   rows; the rest are literal `0` or end at zero and don't bind.
3. **Reserves accounting is inconsistent.** `Base Year Reserves` is
   authored `0` for all 9 reserve-carrying fuels in all 12 regions
   (Current Accounts), while `Additions to Reserves` carries real
   point data — e.g. Vietnam Coal Anthracite `Data(2021, 3359996.97)`
   (Thousand Metric Tonnes), Indonesia Crude Oil `Data(2019, 4.17)`
   (Billion Barrels of Oil Equivalent). Starting from zero proven
   reserves and adding one year's estimate is unlikely to be the
   intent. Can you reconcile: supply base-year proven reserves per
   (country, fuel), or confirm the reserves panel is not meant to be
   load-bearing?
4. **Refined products are capped at zero in RAS — confirm intent.**
   In the Regional Aspiration Scenario, `Maximum Production` on
   Secondary Diesel, Gasoline, Kerosene, LPG and Residual Fuel Oil is
   authored `0` for all countries. This is deliberate on our side:
   refined-product supply is meant to come from refinery processes in
   the Transformation tree (fed by your Crude Oil), not from a
   free-standing cap on the product fuel. Please confirm your data
   model agrees — i.e. send refinery capacities/yields when the
   Transformation package arrives (*pending Transformation export*),
   and do NOT send production caps for these five products.
5. **Comma-decimal expressions on Philippines gas prices.** 9 rows in
   the extract read `Production Cost[USD/MMBTU]*1,0551` (Philippines
   Natural Gas Industrial / Residential / Other Consumer Price, in
   ATS, Baseline and RAS). `1,0551` uses a comma as the decimal mark —
   ambiguous under the §4 convention (is it 1.0551, presumably an
   MMBTU→GJ-ish factor, or 10,551?). If these rows are yours, please
   confirm the intended factor; we will re-author with a period.
   (Separately, 20 rows on Crude Oil `Additions to Reserves` in ATS
   and Baseline use a semicolon as the list separator — `Data(2024;
   1.1)` for Brunei, etc. Those are single-point values, so
   unambiguous — we will re-author them with commas ourselves; noted
   here only so they don't puzzle you when reviewing §7.3.)
6. **Consumer prices are mostly zero.** The four Consumer Price
   variables are ~98% zero across the tree; the non-zero rows are
   confined to Cambodia, Indonesia, Philippines and Thailand and
   end in 2017 or 2020. Demand-sector price elasticity reads these
   cells, so a zero price means "no price signal". If you hold
   end-user coal/gas/product price series for the other countries,
   they are welcome (2011 USD / GJ, or tell us your unit and we
   convert).
7. **Nuclear is an unlimited free supply in every region.**
   `Resources\Primary\Nuclear` holds `Maximum Production = Unlimited`
   AND `Production Cost = 0` in all 12 regions in all four scenarios
   (plus `Maximum Imports = Unlimited` in RAS — though its Import
   Cost does carry a real historical series). That is exactly the
   free-energy shape that has mis-routed the optimizer before. It may
   be deliberate — nuclear fuel-cycle costs may be intended to sit on
   the power-plant processes instead (*pending Transformation export*,
   so we can't confirm yet) — but please tell us: should Nuclear
   production stay effectively uncapped, and if so, what Production
   Cost should accompany it? Any finite answer beats the current
   `Unlimited` + `0`.

## 8. What to send back, and in what shape

CSV per topic, using YOUR source-side names (we do all mapping to
LEAP names; never hand-build LEAP branch paths):

1. `fossil_production_caps.csv` — Country × fuel (NG + 5 coal grades,
   plus Crude Oil revisions if any) × year-series of maximum
   production, with `unit`, `source`, `confidence` columns (§7.1).
2. `import_floor_review.csv` — the §7.2 list annotated: Country ×
   fuel × `keep_floor`/`drop_after_2022`/`replace_with` + rationale.
3. `reserves.csv` — Country × fuel base-year proven reserves +
   any reserve-addition series, with units and source (§7.3).
4. `consumer_prices.csv` — optional, Country × fuel × sector ×
   year-series (§7.6).

Two things need only a line in your cover note, no CSV: the §7.4
confirmation (no production caps for the five refined products) and
the §7.7 Nuclear ruling.

Every row should carry a source/provenance column. Anything with
year ≤ 2024 is treated as historical (Current Accounts); projection
values land in the scenario you name (`BAS`/`ATS`/`RAS`). Timor Leste
rows, if any, go in a separate supplement file. Fuels or combinations
the model doesn't have branches for will be dropped with a log entry —
if you believe the model SHOULD cover them, say so explicitly in your
cover note and we'll raise it as a model-structure request instead.

Questions → yudiandra.y@gmail.com. Please reference fuel and variable
names as they appear in `resources_tree.txt` when reporting structure
issues.
