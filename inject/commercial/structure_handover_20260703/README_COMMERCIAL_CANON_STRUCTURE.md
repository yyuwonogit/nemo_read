# Commercial — Canonical LEAP Structure Handover (2026-07-03)

For the commercial buildings data team. You don't need LEAP, our repo,
or any database to use this package — everything referenced here is a
plain text/CSV file sitting next to this README.

## 1. What this package is

This is the **canonical structure** of the LEAP trees your data feeds,
exported directly from the live model (LEAP area `aeo9_v0.67_w_results`)
on 2026-07-02. It is the ground truth for branch names, variable names,
and units. Your CSVs must line up with these structures **exactly** —
any branch spelling, end-use name, or variable name that doesn't exist
here gets filtered out by our import adapter and never reaches the model.

Files in this package:

| File | What it is |
|---|---|
| `commercial_tree.txt` | The full `Demand\Commercial` branch tree (426 branches), indented, with each branch's variables listed |
| `commercial_branch_variables_units.csv` | One row per (branch, variable): units, scale, per — the authoritative unit reference |
| `keys_slice_commercial.txt` | The commercial-relevant slice of the `Key\` assumptions tree (30 branches) — floor area, calibration factors, efficiency levers |
| `keys_slice_commercial_units.csv` | Units for that Key slice |
| `resources_slice_commercial_units.csv` | The 12 `Resources\` fuel branches whose consumer prices your sector's Baseline regressions reference (context only — see §6) |
| `current_expressions_commercial_4scenarios.csv` | **What is currently written in the model** for every `Demand\Commercial` branch — the live expressions, scoped to the 4 scenarios that matter (see §6b) |
| `current_expressions_keys_slice_4scenarios.csv` | Same, for the 30-branch Key slice |
| `current_expressions_resources_slice_4scenarios.csv` | Same, for the 12 Resources price branches |

How to read them: in the `.txt` trees, indentation = depth, and the
`[vars: ...]` suffix lists the variables carried on that branch. In the
CSVs, `branch_path` is the full LEAP path (backslash-separated), and
`units`/`scale`/`per` together give the unit (e.g. units=`kWh/m2`, or
units=`Tonnes of Oil Equivalent`, scale=`Thousand`, per=`Square Meter`).

## 2. Your tree in brief — floor area drives everything

`Demand\Commercial` is a floor-area-driven sector: the sector's
Activity Level is wired to `Key\Commercial\Gross Floor_Area
[Thousand m2]`, and everything below is shares of that area times an
energy intensity per m2. It splits into two sub-sectors:

| Sub-sector | Branches | Method |
|---|---|---|
| `Data_Center` | Colocation / Enterprise / Hyperscale | **authored `Total Energy` trajectories in GWh** — bypasses the floor-area chain entirely |
| `Other Commercial` | `Historical` (15 fuels) + `End Use Projection` (6 end uses) | floor area × intensity, with a hand-authored switch at 2025 |

**Data_Center** — each of the three classes holds a `Total Energy`
(GWh) time series per country. Trajectories are currently authored for
exactly six countries (Indonesia, Malaysia, Philippines, Singapore,
Thailand, Vietnam); the rest hold `0`. The same numbers appear in every
scenario — there is currently no policy lever on data-center demand
(see §7.5).

**Other Commercial** runs on two eras, switched by complementary Step
expressions: `Historical:Activity Level = Step(2005, 100, 2025, 0)`
and `End Use Projection:Activity Level = Step(2005, 0, 2025, 100)`.
Everything before 2025 comes from the `Historical` accounting subtree
(15 flat fuel branches — Electricity, Diesel, LPG, … including
Briquette, Ethanol and Gasoline which have no forward counterpart);
everything from 2025 on comes from the six end uses:

| End use | Technology / fuel leaves under it |
|---|---|
| Air Conditioning | Best Practice, Current Sales_Average, Current Stock_Average, Efficient (an efficiency-class stock split) |
| Cooking and Food Processing | 9 fuel technologies, incl. Induction Electric and Solar Heating |
| Lighting | Electricity → CFL / Fluorescent / Halogen / Incandescent / LED; Other → Kerosene and Candles, Solar Lighting |
| Other | 10 fuels |
| Refrigeration | Efficient / Existing |
| Water Heating | Existing, Heat Pump, Heat Pump Outside Air, Solar Heating |

Most of the tree's 426 branches (359 of them) are pollutant leaves
(CO2, CH4, N2O, NOx, PM2.5, …) hanging under the combustion fuels —
we maintain those emission factors; they're listed for completeness.

## 3. The variables you author

From `commercial_branch_variables_units.csv` (the full list is there;
this is the panel your data feeds). Three of the load-bearing variables
are **custom** — model-specific names you won't find in a LEAP textbook:

| Variable | Unit | Where | Notes |
|---|---|---|---|
| Commercial Uncalibrated Energy Intensity | kWh/m2 | the 6 end-use branches | **custom** — your raw energy-per-area estimate per end use, before calibration (see §6). Most rows are placeholders today (§7.1) |
| Commercial Fuel Share_ | % | technology/fuel leaves | **custom** — fuel split within an end use; mostly anchored by formula to 2022 history (see §6) |
| Commercial Cooking Efficiency_ | percent efficiency | Cooking fuel technologies | **custom** — device efficiency; policy scenarios divide it by an efficiency-improvement factor (see §6) |
| Activity Level | % Share / % Saturation of m2 | end uses + tech leaves | end-use saturation and technology shares; where the policy targets live (`InterpFSY` rows) |
| Fuel Share | % Share | the 15 `Historical` fuels | historical fuel split, year ≤ 2024 statistics |
| TotalEnergy | Thousand TOE | `Historical` node | **custom** — total historical commercial energy per country, `Interp(2005, …, 2024, …)` |
| UnscaledFuelShare | % | the 15 `Historical` fuels | **custom, Current Accounts only** — a helper snapshot of Fuel Share that the other scenarios renormalise against; don't author it directly |
| Total Energy | GWh | the 3 `Data_Center` classes | the authored data-center trajectories |
| Final Energy Intensity | kWh/m2, Thousand TOE/m2, Liter/m2 | tech/fuel leaves + Historical fuels | mostly formula-driven (calibration chain, §6) — check the units column per branch before sending numbers; three unit systems coexist |
| Load Shape | Percent | electric leaves | hourly load shapes — ours to maintain |

`Demand Cost` (all zeros) and `RefHH` (constant 1) also appear on all
67 non-pollutant branches — pure boilerplate, nothing to author. `Avg Environmental
Loading` is the emission-factor panel on the pollutant leaves — ours.

## 4. Expression conventions (non-negotiable)

Values enter LEAP as expressions. The house rules:

- **`Interp(year, value, year, value, ...)`** — COMMA between items,
  PERIOD as the decimal mark. `Interp(2025, 119.40, 2030, 115.2)` is
  right; semicolons or comma-decimals (`119,40`) are wrong and will be
  rejected before import.
- **`? comment` provenance** — anything after a `?` in an expression is
  a comment. We encourage these for source citations, e.g.
  `119.40 ? BEI 2019` or `161.5 ? SEI WS2 value set`. Name the actual
  source (ACE, ERIA, BEI, national statistics, journal DOI).
- **`Remainder(100)`** — the last sibling in any share partition closes
  the partition to 100%. Used on commercial share rows today; your
  shares for the other siblings must be authored so this stays
  meaningful.
- **`InterpFSY(year, value, ...)`** — like Interp but anchored at the
  first scenario year; the house style for policy targets. Live
  examples from your tree: `InterpFSY(2050, 20) ? ATS assumption` vs
  `InterpFSY(2050, 40) ? RAS assumption` on the same efficient-tech
  share.
- **`Step(...)` era switches are plumbing** — the paired
  `Step(2005, 100, 2025, 0)` / `Step(2005, 0, 2025, 100)` rows in §2
  are structural. Don't send replacements for them.
- **Never write the literal word `Unlimited`** in anything you author.
  It becomes a broken numeric sentinel downstream. If something needs a
  generous cap, use a large number.

## 5. Scenarios and regions — where your data lands

The model carries 11 scenarios, but for commercial they collapse into
a few real cases:

- **Current Accounts** — historical statistics (the `Historical`
  subtree, `TotalEnergy`, the CA-only `UnscaledFuelShare` helper).
- **Baseline Simulation** — no-policy projection. Differs from Current
  Accounts only inside `Historical`: the historical fuel intensities
  are re-authored as price/GDP regression shells (currently unfitted —
  §7.2) and the fuel shares are renormalised.
- **Six names, one expression set** — `Set up`, `LCO backup`,
  `AMS Target Scenario`, and the three `RE LTRM` scenarios are
  expression-identical in commercial (zero differences). Correcting
  AMS Target Scenario effectively corrects all six.
- **Regional Aspiration Scenario (RAS)** — the main policy projection:
  AMS Target plus stronger technology-share targets (the
  `? ATS assumption` → `? RAS assumption` InterpFSY pairs).
- **Carbon Neutrality_ Net Zero Scenario** — RAS plus deeper targets
  tagged `? CNS assumption` (e.g. Best Practice AC share
  `InterpFSY(2050, 90)`). Not in your review files; it inherits from
  the same rows you'll be reviewing.
- **Regional Aspiration Scenario test** — a stale frozen prototype;
  ignore it.

Regions: the 12 region slots are the 10 ASEAN member states plus
**Base Template** (a LEAP template holding default values — NOT a
country; you never author data for it) and **Timor Leste**. Timor Leste
currently holds template-grade defaults; if/when you have Timor Leste
data, send it as a **separate supplement file**, never mixed into the
main 10-country data.

## 6. KEY CONNECTIONS — the second tree your data feeds (important)

Your intensity data does NOT become final energy demand directly. It
runs through a calibration chain that lives partly in a separate
assumptions tree, `Key\`. Verbatim from the live model:

```
Air Conditioning\Current Stock_Average:Final Energy Intensity =
  Air Conditioning:Commercial Uncalibrated Energy Intensity[kWh/m2]
  * Key\Cal\Commercial\Electricity:Activity Level[Factor]
```

So: you author the **uncalibrated** intensity per end use; a per-fuel
calibration factor in `Key\Cal\Commercial\<Fuel>` (12 fuels) scales it
so the modelled total matches the historical statistics. The factors
are ours to maintain — but they're only as good as your uncalibrated
values and the `TotalEnergy` history they're calibrated against.

Two more formula patterns you'll see everywhere in the review files:

- **2022 anchors**: forward fuel shares pull the last historical year,
  e.g. `Value(Demand\Commercial\Other Commercial\Historical\LPG:
  Fuel Share[% Share], 2022) / 100`. If your historical fuel shares
  change, the projections move with them automatically.
- **The efficiency knob**: policy-scenario cooking efficiency is
  `ScenarioValue(Baseline Simulation) / Key\Annual EI Reduction\
  EI_Improvement_RAS_2:Activity Level[Factor]` — one Key branch drives
  the efficiency improvement across all policy scenarios at once.

The 30-branch Key slice in this package was mechanically extracted
from the live commercial expressions — every branch in it is actually
referenced by (or feeds) your tree:

| Key sub-tree | Branches | Holds |
|---|---|---|
| `Key\Commercial\Gross Floor_Area` | 1 | the sector activity driver (Thousand m2) |
| `Key\Commercial\Share_ of Buildings\…` + `Energy consumption per area\…` (Hospital/Hotel/Office/Others/Retailer) + `Average Energy Intensity` + `Commercial Energy Consumption` | 12 | building-type floor-area shares and kWh/m2 benchmarks behind the floor-area estimate |
| `Key\Cal\Commercial\<Fuel>` | 12 | the per-fuel calibration factors from the chain above |
| `Key\Annual EI Reduction\EI_Improvement_RAS_2` | 1 | the policy efficiency-improvement factor |
| `Key\Macroeconomic\Real GDP Service` | 1 | GDP driver used by the Baseline regressions |
| `Key\Cal\Residential\Cook and Light Non Elec` + `Key\Net Zero Measures\Residential\Building Orientation\{Lighting Energy Savings, Share_Households}` | 3 | **borrowed residential branches** — see below |

**Why residential branches are in a commercial package**: the
commercial `Lighting\Other\Kerosene and Candles` intensity is authored
against residential machinery, verbatim:

```
1 * 52 * Key\Cal\Residential\Cook and Light Non Elec:Activity Level[Factor]
  * (1 - Key\Net Zero Measures\Residential\Building Orientation\Lighting
  Energy Savings:Activity Level/100 * …\Share_Households:Activity Level/100)
  ? Assume 1 liter per week (Energypedia - gives 4hrs/day lighting)
```

They appear in your slice because your tree genuinely depends on them.
If you replace the kerosene-lighting assumption with real data, this
borrowed wiring can be retired — tell us if you'd rather own it.

**Resources context**: `resources_slice_commercial_units.csv` lists the
12 fuel branches (Biomass, Coal Unspecified, Crude Oil, Natural Gas,
Wood, Charcoal, Diesel, Electricity, Gasoline, Kerosene, LPG, Residual
Fuel Oil) whose `Commercial Consumer Price` your Baseline regression
shells reference. You don't author them — but be aware that **most of
these price series currently resolve to zero** (non-zero values are
confined to Cambodia, Indonesia, Philippines and Thailand, with the
historical series ending 2017 or aliased to Wood's production cost),
which matters for §7.2. The supply side of your fuels
(power plants, refineries) lives in the model's Transformation tree,
which is **not yet exported — pending Transformation export**; a
supply-side slice will follow in a later package.

## 6b. What is currently written in the model — for your review

The three `current_expressions_*_4scenarios.csv` files are a full dump
of the expressions **currently authored in the live model** for your
branches, so your team can judge what to keep, correct, or replace.

- **Scope: four scenarios only** — `Current Accounts` (historical),
  `Baseline Simulation`, `AMS Target Scenario` (ATS), `Regional
  Aspiration Scenario` (RAS). The other seven scenarios are copies,
  derivatives, or internal plumbing (§5) — ignore them; any correction
  you make to these four propagates.
- **Reading the region column**: `ALL (12 regions)` means every country
  currently holds the same expression (a template value — often exactly
  the thing worth replacing with country data). A named country means
  that row is country-specific. Commercial is heavily template-uniform
  today: most combinations hold one expression across all countries.
- Columns: `branch_path, variable, scenario, region, expression, units,
  scale, per`. Expressions may carry `? comments` citing their source —
  that tells you where the current number came from.
- What we'd like back: for any row where you have better data, a note
  with the branch path, scenario, country, your proposed value/series,
  and the source. Template rows (`ALL`) holding round placeholder
  numbers are the highest-value targets.

## 7. Known issues in your tree — we'd like your input

Review requests, not blame — some of these predate everyone involved:

1. **`? ACE temp value` placeholder intensities.** Model-wide, 630 of
   the 792 `Commercial Uncalibrated Energy Intensity` rows are flat
   constants tagged `? ACE temp value` (in your 4-scenario review file
   the tag appears on 428 rows — 208 on this intensity variable, the
   other 220 on end-use saturation `Activity Level` rows). Only four
   countries have sourced values:
   Brunei (`119.40 ? BEI 2019`), Laos (ERIA), Malaysia (journal
   reference), Thailand (`161.5 ? SEI WS2 value set`) — the other six
   sit on the template default. **This is the single highest-value
   data request: end-use energy intensities (kWh/m2) for the remaining
   countries**, with sources.
2. **1,660 unfitted regression shells.** The Baseline `Historical`
   intensities are authored as `Exp(1 * Ln(<fuel price>) + 1 *
   Ln(<GDP>) + 1) * 1` with a comment saying the coefficients "must be
   determined via regression" — the coefficients are still the
   placeholder 1 on all but 12 of the 201 comment-tagged rows in your
   review file (1,620 of 1,660 model-wide; the exceptions — Electricity
   for Cambodia and Indonesia, LPG for Cambodia, Kerosene for Indonesia
   — carry fitted coefficients but keep the comment). Can
   your team fit these price/GDP elasticities per fuel and country, or
   should we drop the regression form and author plain trajectories?
   Note the price inputs are mostly zeros today (§6), so fitting also
   needs a view on the price series.
3. **Broken price references.** The Ethanol and Biodiesel `Historical`
   regression shells reference branches that no longer exist — they
   render as `!Missing Branch (ID=1687)!` / `(ID=825)!` (6 rows in
   your review file; 240 raw rows model-wide). They need re-pointing
   to a real price series or replacing along with issue 2.
4. **Laos single-point time series.** Laos Air Conditioning saturation
   is `Interp(2017, 50.84)` and Refrigeration `Interp(2017, 11.18)` —
   one 2017 point dressed as a series, held flat forever. Do you have
   Laos saturation trajectories (or even a second year)?
5. **Data_Center covers only 6 countries, with no scenario variation.**
   Brunei, Cambodia, Laos, Myanmar (and Timor Leste) hold `0` in every
   scenario, and the six authored trajectories are identical in every
   scenario — no policy case for data-center growth or efficiency. Is
   zero right for the missing countries, and should the policy
   scenarios differ?
6. **Artifact branch `Data_Center\` (trailing backslash).** The raw
   model export carries one branch under Data_Center with an empty
   name. We've cleaned it out of this package's files; flagging it so
   you know the live model still holds it — we'll ask for it to be
   deleted unless it corresponds to a fourth data-center class you
   expect.

## 8. What to send back, and in what shape

Plain CSVs, using YOUR source-side names (we do all mapping to LEAP
names; never hand-build LEAP branch paths):

1. `end_use_intensity.csv` — Country × end use (Air Conditioning /
   Cooking and Food Processing / Lighting / Other / Refrigeration /
   Water Heating) × year × kWh/m2, replacing the §7.1 placeholders.
2. `end_use_saturation.csv` — Country × end use × year × % of floor
   area served (fixes §7.4 too).
3. `fuel_shares.csv` — Country × end use × fuel/technology × year × %
   (historical years ≤ 2024 update `Historical`; later years update
   the projection shares).
4. `data_center_energy.csv` — Country × class (Colocation / Enterprise
   / Hyperscale) × year × GWh, including the currently-zero countries
   if non-zero (§7.5), and per-scenario variants if you have them.
5. `floor_area.csv` — Country × year × total gross floor area
   (thousand m2), plus building-type shares if available — this drives
   the whole sector.

Every row should carry a source/provenance column. Anything with
Year ≤ 2024 is treated as historical. Timor Leste rows, if any, go in
a separate supplement file. Combinations the model doesn't have
branches for will be dropped with a log entry — if you believe the
model SHOULD cover them (a new end use, a new data-center class), say
so explicitly in your cover note and we'll raise it as a
model-structure request instead.

Questions → yudiandra.y@gmail.com. Please reference branch paths as
they appear in `commercial_tree.txt` when reporting structure issues.
