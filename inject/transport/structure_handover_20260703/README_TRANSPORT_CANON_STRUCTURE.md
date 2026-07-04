# Transport — Canonical LEAP Structure Handover (2026-07-03)

For the transport data team. You don't need LEAP, our repo, or any
database to use this package — everything referenced here is a plain
text/CSV file sitting next to this README.

## 1. What this package is

This is the **canonical structure** of the LEAP trees your data feeds,
exported directly from the live model (LEAP area `aeo9_v0.67_w_results`)
on 2026-07-02. It is the ground truth for branch names, variable names,
and units. Your CSVs must line up with these structures **exactly** —
any (vehicle, fuel) combination, branch spelling, or variable name that
doesn't exist here gets filtered out by our import adapter and never
reaches the model.

Files in this package:

| File | What it is |
|---|---|
| `transport_tree.txt` | The full `Demand\Transport` branch tree (165 branches), indented, with each branch's variables listed |
| `transport_branch_variables_units.csv` | One row per (branch, variable): units, scale, per — the authoritative unit reference |
| `keys_slice_transport.txt` | The transport-relevant slice of the `Key\` assumptions tree (150 branches) — where your sales/stock data actually lands |
| `keys_slice_transport_units.csv` | Units for that Key slice |
| `resources_branch_variables_units.csv` | The `Resources\` fuel supply/price tree (context: where Blended Diesel, Blended Gasoline, Jet Kerosene, Sustainable Aviation Fuel, Hydrogen etc. are supplied and priced) |
| `current_expressions_transport_4scenarios.csv` | **What is currently written in the model** for every `Demand\Transport` branch — the live expressions, scoped to the 4 scenarios that matter (see §6b) |
| `current_expressions_keys_slice_4scenarios.csv` | Same, for the transport Key slice (`Key\TransportDataStock`, vehicle data, EV charging costs, …) |

How to read them: in the `.txt` trees, indentation = depth, and the
`[vars: ...]` suffix lists the variables carried on that branch. In the
CSVs, `branch_path` is the full LEAP path (backslash-separated),
`units`/`scale`/`per` together give the unit (e.g. units=`Vehicle`, or
units=`Tonnes of Oil Equivalent`, scale=`Thousand`, per=`U.S. Dollar`).

## 2. Your tree in brief — two methodologies, one sector

`Demand\Transport` splits into four subsectors with two different
modelling methods:

| Subsector | Branches | Method |
|---|---|---|
| Domestic Air | 30 | energy intensity per GDP |
| Inland Waterways | 69 | energy intensity per GDP |
| Rail | 28 | energy intensity per GDP |
| Road | 37 | **vehicle stock-turnover** (fleet model) |

**Air / Inland Waterways / Rail** — the subsector branch carries
`Activity Level` (wired to GDP) and an aggregate `Final Energy
Intensity`; each fuel branch under it carries its own Final Energy
Intensity and `Fuel Share`; under the combustion fuels sit pollutant
leaves (9 of the 15 fuel branches, 12–13 species each: CO2, CH4, N2O,
NOx, PM2.5, black carbon, …; Electricity, Hydrogen Fuel Cell and
Aviation Gasoline carry none).

**Road** — a fleet model, three levels deep:

```
Road\<VehicleClass>\<Fuel>          Stock / Sales / Scrappage / First Sales Year
Road\<VehicleClass>\<Fuel>\<Fuel>   Fuel Economy / Mileage / Device Share
```

The four vehicle classes and their fuel branches in the current model:

| Vehicle class | Fuel branches |
|---|---|
| Bus | Blended Diesel, Blended Gasoline, Electricity, Hydrogen, Natural Gas |
| `Motorcyle` (LEAP's spelling — see §7) | Blended Gasoline, Electricity |
| PassengerCar | Blended Diesel, Blended Gasoline, Electricity, Natural Gas |
| Truck | Blended Diesel, Blended Gasoline, Electricity, Hydrogen, Natural Gas |

Note the gasoline branch is **Blended Gasoline** (not "Gasoline") —
the model blends ethanol upstream, so road gasoline demand is for the
blended product. Same logic for Blended Diesel.

## 3. The variables you author

From `transport_branch_variables_units.csv` (the full list is there;
this is the panel your data feeds):

| Variable | Unit | Where | Notes |
|---|---|---|---|
| Sales | Vehicle | Road, fuel level | new registrations per year, split by fuel |
| Stock | Vehicle | Road, fuel level | fleet on the road — **historical accounts only** (see §5) |
| First Sales Year | Years | Road, fuel level | historical accounts only |
| Scrappage | Vehicle | Road, fuel level | mostly boilerplate 0 |
| Max Scrappage Fraction / Fraction of Scrapped Replaced | % | Road, fuel level | boilerplate 100 |
| Fuel Economy | MPG Gasoline US eq. | Road, device level | **all powertrains, including electric and hydrogen**, are authored in gasoline-equivalent MPG |
| Mileage | Kilometer | Road, device level | annual km per vehicle, flat per country |
| Device Share | Share (%) | Road, device level | |
| Final Energy Intensity | Tonnes of Oil Equivalent per U.S. Dollar (Rail: per 2020 USD) | Air/Waterways/Rail | energy per unit GDP |
| Fuel Share | Share (%) | Air/Waterways/Rail fuel branches | must sum to 100 across sibling fuels |
| Activity Level | Million U.S. Dollar (Rail: Million 2020 USD); Saturation % on Rail fuel branches | subsector level (+ Rail fuels) | wired to GDP |
| TotalEnergyTran | Thousand TOE | calibration helper | historical energy totals |

## 4. Expression conventions (non-negotiable)

Values enter LEAP as expressions. The house rules:

- **`Interp(year, value, year, value, ...)`** — COMMA between items,
  PERIOD as the decimal mark. `Interp(2025, 3.2422, 2030, 3.0833)` is
  right; semicolons or comma-decimals (`3,2422`) are wrong and will be
  rejected before import.
- **`? comment` provenance** — anything after a `?` in an expression is
  a comment. We encourage these for source citations, e.g.
  `20230 ? source: 2022 ERIA Analysis of Future Mobility Fuel Scenarios
  Phase II`. Name the actual source (ERIA, IEEJ, national statistics,
  ministry decree number).
- **`Remainder(100)`** — the last sibling in any share partition (e.g.
  the last Fuel Share under Domestic Air) closes the partition to 100%.
  Your shares for the other siblings must be authored so this is
  meaningful; the model currently uses this on 92 transport Fuel Share
  rows.
- **`InterpFSY(year, value, ...)`** — like Interp but anchored at the
  first scenario year; the house style for policy targets. Example from
  the live model: Indonesia's SAF blending mandate is
  `InterpFSY(2026, 1, 2060, 50)` (1% by 2026, 50% by 2060, per
  Ministerial Decree No. 8/2023).
- **Never write the literal word `Unlimited`** in anything you author.
  It becomes a broken numeric sentinel downstream. If something needs a
  generous cap, use a large number.

## 5. Scenarios and regions — where your data lands

The model carries 11 scenarios, but for transport they collapse into a
few real cases:

- **Current Accounts** — historical statistics (everything year ≤ 2024).
  Three variables exist ONLY here: `Stock` (192 rows), `First Sales
  Year` (192), `Share_FossilFuels` (48). Base-year fleet data always
  lands in Current Accounts.
- **Regional Aspiration Scenario (RAS)** — the main policy projection.
  In transport, `Set up`, `LCO backup` and the three `RE LTRM` scenarios
  are expression-identical to RAS.
- **Baseline Simulation** — no-policy projection (identical to
  `Regional Aspiration Scenario test`).
- **AMS Target Scenario** — only 4 transport rows differ from RAS (all
  SAF-related: Indonesia drops the SAF mandate; Thailand and Malaysia
  keep it with altered trajectories).
- **Carbon Neutrality / Net Zero** — RAS plus net-zero measures (130
  transport rows differ: aviation fuel shares and efficiency wired to
  `Key\Net Zero Measures\Transport\Aviation`).

Regions: the 12 region slots are the 10 ASEAN member states plus
**Base Template** (a LEAP template holding default values — NOT a
country; you never author data for it) and **Timor Leste**. Timor Leste
currently holds template-grade defaults; if/when you have Timor Leste
data, send it as a **separate supplement file**, never mixed into the
main 10-country data.

Policy scenarios improve Road fuel economy by applying
`Growth(Key\Annual EI Reduction\FuelEco)` on top of your base values —
you author the base year economy; the annual % improvement is a
separate policy lever.

## 6. KEY CONNECTIONS — the second tree your data feeds (important)

Your vehicle sales and stock data does NOT go directly into
`Demand\Transport\Road`. It lands in a separate assumptions tree,
`Key\TransportDataStock`, and the Road branches *pull from it by
formula*. Verbatim from the live model:

```
Road\PassengerCar\Blended Diesel:Sales =
  Key\TransportDataStock\Vehicles_Sales_Share\PassengerCar\Blended Diesel:Activity Level[%]
  / 100 *
  Key\TransportDataStock\Vehicle_Sales\PassengerCar:Activity Level[Vehicle]
```

So you need BOTH structures — that is why this package contains the
Key slice files. `Key\TransportDataStock` has 47 branches:

| Sub-tree | Branches | Unit | Holds |
|---|---|---|---|
| `Vehicles_Sales_Share\<Vehicle>\<Fuel>` | 17 | % | fuel split of new sales |
| `Vehicle_Stock_Share\<Vehicle>\<Fuel>` | 17 | % | fuel split of the fleet |
| `Vehicle_Sales\<Vehicle>` | 4 | Vehicle | total sales per class per year |
| `BaseYear_StockData\<Vehicle>` | 4 | Vehicle | **fleet on the road in 2024** — NOT vehicles sold in 2024 (a past data drop confused these; a real fleet is typically an order of magnitude larger than one year's sales, yet the values currently in these slots are about the same size as the annual sales series) |
| `Effective Operational_Stock\<Vehicle>` | 4 | Vehicle | |
| `Year_\Age` | 1 | Year | |

The rest of the Key slice, for context:

- `Key\Transport vehicle data_` (28 branches) — historical vehicle
  counts plus a/b/c regression coefficients per class.
- `Key\Other Transport` (23) — EV charging infrastructure cost stack
  (CAPEX, chargers-per-EV, fixed O&M, lifetime) for AC Level 1,
  AC Level 2, and DC Fast Charger.
- `Key\Net Zero Measures\Transport` (12) — the net-zero levers
  (aviation efficiency, electric taxiing, cold ironing, electric
  taxis) used by the Carbon Neutrality scenario.
- `Key\Cal\Transport` (10) — internal calibration factors (ours to
  maintain, listed for completeness).
- `Key\Macroeconomic` (17) + `Key\Annual EI Reduction` (13) — GDP
  drivers and the fuel-economy improvement lever mentioned in §5.

**Resources context**: `resources_branch_variables_units.csv` shows
the supply side of every fuel your sector consumes (Blended Diesel,
Blended Gasoline, Jet Kerosene, Sustainable Aviation Fuel, Hydrogen,
Electricity, Natural Gas, …) — production/import caps and costs. You
don't author it, but it tells you which fuels the model can actually
supply.

## 6b. What is currently written in the model — for your review

The two `current_expressions_*_4scenarios.csv` files are a full dump of
the expressions **currently authored in the live model** for your
branches, so your team can judge what to keep, correct, or replace.

- **Scope: four scenarios only** — `Current Accounts` (historical),
  `Baseline Simulation`, `AMS Target Scenario` (ATS), `Regional
  Aspiration Scenario` (RAS). The other seven scenarios are copies,
  derivatives, or internal plumbing — ignore them; any correction you
  make to these four propagates.
- **Reading the region column**: `ALL (12 regions)` means every country
  currently holds the same expression (a template value — often exactly
  the thing worth replacing with country data). A named country means
  that row is country-specific.
- Columns: `branch_path, variable, scenario, region, expression, units,
  scale, per`. Expressions may carry `? comments` citing their source —
  that tells you where the current number came from.
- What we'd like back: for any row where you have better data, a note
  with the branch path, scenario, country, your proposed value/series,
  and the source. Template rows (`ALL`) holding round placeholder
  numbers are the highest-value targets.

## 7. Known issues in your tree — we'd like your input

Review requests, not blame — some of these predate everyone involved:

1. **Truck Natural Gas fuel economy discontinuity (Indonesia only).**
   Historical accounts say 12 MPG-equivalent; all 10 projection
   scenarios say 5. Every other country holds 12 throughout. Is 5 an
   intended assumption or a slip? Which value should projections carry?
2. **Road has zero pollutant leaves.** Air, Inland Waterways and Rail
   each carry 12–13 emission species per combustion fuel; Road carries
   none.
   Should Road tailpipe emission factors exist, and can you supply or
   recommend a factor set (e.g. per vehicle-km or per unit fuel)?
3. **Spelling split between the two trees.** The Demand tree spells the
   class `Motorcyle`; `Key\TransportDataStock` spells it `Motorcycle`
   (correctly) — except `Effective Operational_Stock\Motorcyle`, which
   uses the typo inside the Key tree too. We map both automatically,
   but flag it so nothing in your tooling assumes one spelling.
4. **Fuel-name split between the two trees.** Demand Road branches say
   `Blended Gasoline` / `Blended Diesel`; the Key share trees say plain
   `Gasoline` alongside `Blended Diesel`. Again handled by our mapping;
   just don't hand-build LEAP paths.
5. **Orphan hydrogen share slots.** `Key\TransportDataStock\
   Vehicle_Stock_Share\PassengerCar\Hydrogen` and its
   `Vehicles_Sales_Share` twin both exist, but the Demand tree has no
   PassengerCar hydrogen branch — a share can be authored that no
   fleet model consumes. Do you foresee hydrogen passenger
   cars, or should the slot stay zero?
6. **Base-year stock vs sales.** Per the table in §6: we need the 2024
   fleet stock per (country, vehicle class), aggregated across fuels.
   Please include a `stock_count` per country and class in the next
   drop.
7. **SAF mandates are per-country policy rows** — Indonesia
   `InterpFSY(2026, 1, 2060, 50)`, Malaysia `InterpFSY(2030, 15, 2050,
   47)`, Thailand `InterpFSY(2026, 1, 2036, 8)`; all other countries 0.
   If your national data suggests different trajectories, send sources.
8. (Internal, FYI) 180 rows of alternative-fuel-share bookkeeping
   reference a `Demand\Transport_` path (trailing underscore) that
   doesn't match the exported tree name — we're chasing that on our
   side; no action needed from you.

## 8. What to send back, and in what shape

Same delivery shape as your previous drops — four CSVs, using YOUR
source-side names (we do all mapping to LEAP names; never hand-build
LEAP branch paths):

1. `sales_mix.csv` — Country × Year × vehicle_type (`2W`/`Bus`/`LDV`/
   `Truck`) × fuel_type × scenario (`BAS`/`ATS`/`RAS`/`historical`) ×
   count.
2. `sales_magnitude.csv` — Country × Year × vehicle_type total sales.
3. `mileage_anchors.csv` — Country × vehicle_type annual km, with
   `confidence` and `source` columns.
4. `starting_year_sales.csv` — 2024 baseline anchors, **now extended
   with the 2024 `stock_count` per (Country, vehicle_type)** (§7.6).

Every row should carry a source/provenance column. Anything with
Year ≤ 2024 is treated as historical. Combinations the model doesn't
have branches for (e.g. motorcycle × natural gas, passenger car ×
hydrogen) will be dropped with a log entry — if you believe the model
SHOULD cover them, say so explicitly in your cover note and we'll
raise it as a model-structure request instead.

Questions → yudiandra.y@gmail.com. Please reference branch paths as
they appear in `transport_tree.txt` when reporting structure issues.
