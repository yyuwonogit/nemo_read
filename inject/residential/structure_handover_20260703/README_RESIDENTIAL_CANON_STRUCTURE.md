# Residential team — canonical LEAP structure handover (2026-07-03)

## 1. What this package is

This folder is the **authoritative map of the LEAP structure your data feeds
into**, exported directly from the live model area `aeo9_v0.67_w_results` on
2026-07-02. It is self-contained: you do not need LEAP, our repository, or
any database to use it — everything is plain text and CSV.

Why it matters: when you send us data, our import adapter matches your rows
against these **exact** branch paths, variable names, and units. Anything
that doesn't match — a misspelled branch, a variable that doesn't exist on
that branch, a unit LEAP doesn't carry there — is **filtered out and never
reaches the model**. This package lets you author against reality instead of
guessing.

Files in this package:

| File | What it is |
|---|---|
| `residential_tree.txt` | The full residential demand tree — 530 branches, one per line, indented by depth. Each line shows the branch name and the list of variables that exist on it. |
| `residential_branch_variables_units.csv` | Flat list: one row per (branch path, variable) with its `units`, `scale`, `per` columns — 1,276 rows. This is the file to validate your CSVs against. |
| `keys_slice_residential.txt` | The slice of the shared "Key Assumptions" tree that residential expressions read from (137 branches, same line format as the tree file). |
| `keys_slice_residential_units.csv` | Units for that Key slice, same columns as the branch/variable CSV. |
| `current_expressions_residential_4scenarios.csv` | **What is currently written in the model** for every residential branch — the live expressions, scoped to the 4 scenarios that matter (see §6b). |
| `current_expressions_keys_slice_4scenarios.csv` | Same, for the residential Key slice (appliance ownership/size/efficiency drivers, demographics, calibration factors). |
| `README_RESIDENTIAL_CANON_STRUCTURE.md` | This guide. |

## 2. Your tree in brief

The sector root is `Demand\Residential`. Its activity driver is national
household count, pulled from the shared assumptions tree:
`Demand\Residential:Activity Level = Key\Demographic\Households[Thousand household]`.

Below the root the tree splits into two eras:

- **`Historical`** (169 branches): 14 fuel-accounting branches (Bagasse,
  Biogas, Charcoal, … Wood), each carrying Activity Level + Final Energy
  Intensity, most with 12–13 pollutant child leaves. This side is switched
  OFF from 2025 by a `Step(2005, 100, 2025, 0)` expression.
- **`Projections`** (360 branches): switched ON from 2025 by the mirror
  `Step(2005, 0, 2025, 100)`. It holds **15 end uses**: Air Conditioning,
  **Air Conditioning_**, Clothes Dryer, Computer and Laptop, Cooking, Fan,
  Iron, Lighting, Other, Refrigeration, **Refrigeration_**, Rice Cooker, TV,
  Washing Machine, Water Heating.

Note the two **paired trees**: `Air Conditioning` vs `Air Conditioning_` and
`Refrigeration` vs `Refrigeration_` (trailing underscore). The underscore
versions are the new device-stock rebuilds you have been authoring (Size ×
Efficiency tiers); the old share-based trees still exist alongside them —
see §7, we need your input there.

How to read the files: in `residential_tree.txt`, indentation = depth, and
the `[vars: …]` suffix lists every variable present on that branch. To get
the full LEAP path of a line, walk up the indentation
(e.g. `Demand\Residential\Projections\Refrigeration_\Large\High_eff`). The
CSV gives the same information flat, one (branch, variable) per row, plus
units.

## 3. The variables you author, with units

Drawn from `residential_branch_variables_units.csv` (all counts are branches
carrying the variable):

| Variable | Where | Units (as LEAP stores them) |
|---|---|---|
| Activity Level | 116 branches | `Thousand Household` at the root; `Saturation (% of Household)` on ownership branches; `Share (% of Household)` on partition branches |
| Final Energy Intensity | 97 branches | varies by end use: Tonnes of Oil Equivalent / Kilowatt-Hour / Megajoule / Gigajoule / Liter, all per Household |
| Useful Energy Intensity | 9 branches | Kilowatt-Hour, Tonnes of Oil Equivalent, Megajoule or Gigajoule per Household — **4 different unit systems in play; always check the CSV for the branch you are filling** |
| Efficiency | 35 branches | `Efficiency (%)` |
| End Year Penetration | 15 branches | `%` |
| Capital Cost | 18 device-stock tiers | U.S. Dollar (per device) |
| Unit Capacity | 18 device-stock tiers | Kilowatt |
| Exogenous Devices | 18 device-stock tiers | Device |
| Demand Cost | 116 branches | `2020 USD` per Household on 114 of the 116 branches; the remaining two carry plain `U.S. Dollar` — unit vintage is inconsistent in the area itself |
| Bulb Wattage / BulbsPerHH / LightingHours | Lighting branches | Watts / Bulbs / Hours (custom lighting bottom-up variables) |
| Load Shape | 36 branches | `YearlyShape(<Country>_Hourly)`; AC uses three climate-zone shapes |

The device-stock economics panel on the `Air Conditioning_` /
`Refrigeration_` tiers is larger than this table (Fixed/Variable OM Cost,
Lifetime, Interest Rate, Minimum/Maximum Devices, Device Additions, Minimum
Share, Minimum Utilization, Maximum Availability, Optimize Devices) — every
one of those is listed per-branch in the CSV. **Critical scoping fact for
your AC/fridge work: that panel exists in only 7 of the model's 11
scenarios** (Set up, Carbon Neutrality_ Net Zero, Regional Aspiration, LCO
backup, and the three RE LTRM scenarios). In Current Accounts, Baseline
Simulation, AMS Target Scenario and Regional Aspiration Scenario test the
rows for those variables simply don't exist — data you author for the panel
can only land in the 7 hosting scenarios.

Current panel contents you may want to know before proposing values:
Lifetime is 10 years on 960 of the 1,512 tier rows, 12 on the 372
Refrigeration_ rows (Large 252, Medium 60, Small 60), and 15 on the 180
Air Conditioning_ rows (60 per size class); Interest Rate is the model-wide symbol
`DiscountRate`; `Optimize Devices` sits on the 6 size-class parent branches
(504 rows, currently half `Yes` / half `No`).

## 4. Expression conventions (non-negotiable)

1. **Time series** are `Interp(year, value, year, value, …)` with **comma**
   between items and **period** as the decimal mark:
   `Interp(2025, 3.2422, 2030, 3.0833)`. Never semicolons, never comma
   decimals — those forms are rejected before import.
2. **Source citations are encouraged** using LEAP's `?` comment idiom:
   everything after a `?` is a free-text comment, e.g.
   `Interp(2025, 40) ? source: ERIA 2022 outlook`. Please name the actual
   source (institution, year, document) — the model's provenance layer is
   built from these comments.
3. **Share partitions must close at 100.** LEAP convention is that the LAST
   sibling of a percent partition carries `Remainder(100)` instead of its
   own series. If you author all siblings explicitly, they must sum to 100
   in every year — we do not re-normalise.
4. **Policy targets** (e.g. "reach X% by 2050") use
   `InterpFSY(2050, X)` — interpolation anchored at the first scenario year.
5. **Never author the literal word `Unlimited`.** The model's export layer
   converts it to 1,000,000,000,000 — harmless-looking on a cap, actively
   destructive elsewhere. If a bound is meant to be non-binding, use a
   generous finite number instead. (You will see `Unlimited` in the existing
   device-stock rows — see §7; do not copy that pattern.)

## 5. Scenarios, regions, and where your data lands

**Scenarios** (11 total): Current Accounts (the historical accounts),
Baseline Simulation, Set up, AMS Target Scenario, LCO backup, three RE LTRM
scenarios (RE LTRM ASEAN Policy Aligned / RE LTRM ASEAN RE Coupling /
RE LTRM ASEAN Shared Energy Resources),
Regional Aspiration Scenario, Carbon Neutrality_ Net Zero Scenario, and
Regional Aspiration Scenario test. In residential the three RE LTRM
scenarios are expression-identical to each other; the others genuinely
differ. When you tag data with a scenario, use the exact names above (in
your CSVs the short codes BAS / ATS / RAS we've used before still map to
Baseline Simulation / AMS Target Scenario / Regional Aspiration Scenario).

**Regions** (12 slots): Brunei, Cambodia, Indonesia, Laos, Malaysia,
Myanmar, Philippines, Singapore, Thailand, Vietnam, Timor Leste — plus
**Base Template**, which is a LEAP template placeholder, **not a country**;
never author data for it.

**Timor Leste** is special: its rows in the model are template-grade, not
researched values, and it is currently excluded from model runs. If you have
Timor Leste data, put it in a **separate supplement file** (same columns,
Timor Leste rows only), never mixed into the main CSV — our pipeline
requires the split.

## 6. Key and Resources connections (what your sector wires into)

Residential expressions constantly read from the shared `Key\` assumptions
tree. The slice files in this package (`keys_slice_residential.txt` +
`keys_slice_residential_units.csv`) contain exactly the Key structures your
sector touches:

| Key structure (branches) | Role in residential |
|---|---|
| `Key\Residential` (32) | The AC + Refrigeration driver store: `Percent Ownership`, `Size_Share\*`, `Efficiency_Share\*`, `Useful_EI\*` per appliance. **This is where your ownership/share/intensity data actually lives** — the demand-tree branches just reference it. Useful_EI is stored in Tonnes of Oil Equivalent. |
| `Key\Residential end use data_` (54) | 9 appliances × {Historical count, a, b, c, number of appliances, year_} panels. Live expressions cite only two of these branches: `\AC\number of appliances` (120 rows) and `\AC\Historical AC` (12 rows) — no other appliance's panel, and none of the a/b/c regression panels, is read by any live expression (see §7). |
| `Key\Cal\Residential` (13) | Per-fuel calibration factors, multiplied through 5,218 residential intensity rows. Do not touch these; know they exist — displayed "Efficiency" values on cooking/device tiers silently absorb them, so a displayed % is not physical efficiency. |
| `Key\Demographic` (8) | `Households` drives the sector root; `Household Size` feeds cooking useful energy. |
| `Key\Energy Access` (2) | `Clean Cooking Access` drives the Cooking Clean/Traditional split. |
| `Key\Net Zero Measures\Residential` (9) | Net-zero measure levers (Reflective Coatings Cool Roofs, Programmable Thermostats, Gamification, Building Orientation…) applied as `(1 - saving × share)` multiplier stacks on intensities in the net-zero scenario. |
| `Key\Macroeconomic` (17 in slice) | `Real GDP Per Capita` drives the OLD share-based appliance saturations (old Air Conditioning, old Refrigeration, Washing Machine, Water Heating, Computer and Laptop) via `Lookup` curves. The new `Key\Residential\*\Percent Ownership` drivers you author are plain `Interp` series — no GDP reference. |
| `Key\Lighting_data` (2) | Lighting sector data store. |

**Resources connection:** residential does not author supply-side data. Your
fuels (electricity, LPG, kerosene, biomass, charcoal…) are balanced against
the `Resources\` supply tree by the optimisation — nothing for you to fill
there, but a fuel name in your data must match the model's fuel roster, so
flag any fuel you need that you don't see in the tree file.

## 6b. What is currently written in the model — for your review

The two `current_expressions_*_4scenarios.csv` files dump the expressions
**currently authored in the live model** for your branches, so you can
judge what to keep, correct, or replace.

- **Scope: four scenarios only** — `Current Accounts` (historical),
  `Baseline Simulation`, `AMS Target Scenario` (ATS), `Regional Aspiration
  Scenario` (RAS). The other seven scenarios are copies, derivatives, or
  internal plumbing — ignore them. (Note for AC/fridge work: the
  device-stock economics panel does not exist in Baseline/ATS rows at all —
  see §5 — so you will only find those variables under scenarios outside
  this file's scope plus RAS; RAS is the one to review.)
- **Region column**: `ALL (12 regions)` = every country holds the same
  expression (a template value — often the thing most worth replacing with
  country data). A named country = country-specific authoring.
- Columns: `branch_path, variable, scenario, region, expression, units,
  scale, per`. `? comments` inside expressions cite the current source —
  including placeholder confessions like `? ACE Placeholder when no data`
  and `? placeholder 14 IIEC`, which are your highest-value review targets.
- What to send back: branch path + scenario + country + proposed
  value/series + source, for any row you can improve.

## 7. Known issues in your tree — we'd like your input

Review requests, not blame — these are things the structure export surfaced
that only your team can rule on:

1. **Old vs new appliance trees (double counting?).** The old share-based
   `Air Conditioning` and `Refrigeration` trees still carry **non-zero
   intensities in every projection scenario** (e.g. `Refrigeration\High`
   uncalibrated intensity = 557.09 kWh/HH) while the new `Air Conditioning_`
   / `Refrigeration_` device-stock trees run in parallel in 7 scenarios.
   Whether households are double-counted depends on the
   `Key\Residential\…\Percent Ownership` driver values splitting them
   cleanly. **How is double counting neutralised, and should the old trees'
   ownership be zeroed going forward?**
2. **`Unlimited` on device caps.** `Maximum Devices` and `Maximum Device
   Additions` are the literal string `Unlimited` on all 3,024 device-stock
   tier rows. Per §4 rule 5 we'd like finite ceilings — do you have
   defensible maximum-stock / maximum-sales figures per size class?
3. **Solver output frozen inside authored data.** 360 tier Activity Level
   rows (Regional Aspiration + Carbon Neutrality scenarios) currently hold
   `Data(…) ?Optimized on 07/02/2026 (NEMO/CPLEX)` — optimisation results
   written back into the input slot. If you send fresh tier-share data, it
   will overwrite these; confirm that is intended.
4. **Orphaned regression panels.** The `Key\Residential end use data_`
   a/b/c coefficient panels for all 9 appliances exist but are cited by no
   live expression. Meanwhile the Air Conditioning ownership expression's
   comment cites `Key\Residential\AC\a` and `\b` — branches that **do not
   exist** (a leftover note from a retired AEO7 equation; the live formula
   is a GDP-per-capita Lookup). Should the a/b/c panels be deleted, or is a
   regression re-fit planned that would use them?
5. **AC ownership `×2` multiplier.** The live AC ownership Lookup ends in
   `*2` with an alternative equation embedded only in the comment — please
   confirm the doubling is intentional and document its source.
6. **Lifetime spread.** 10 vs 12 vs 15 years across tiers (§3). If your
   market data supports different lifetimes per size class, send them —
   otherwise we keep the current values.

## 8. What to send back, and in what shape

Residential has **no single unified authoring spec yet** — this README plus
the per-appliance guides we've already exchanged (the fridge authoring
guideline, the AC mapping) are the current authoring contract. Until a
unified spec ships, follow this:

- **One CSV per topic** (e.g. `fridge_ownership.csv`,
  `ac_efficiency_shares.csv`), columns:
  `Country, Year, Scenario, <quantity columns with units in the header>`.
  Long (one year per row) or wide (years as columns) both work — say which.
- **Country names** in your usual source form (`Brunei Darussalam`,
  `Lao PDR`, `Viet Nam` are fine — we map them). 10 ASEAN members in the
  main file; **Timor Leste in a separate `*_timor_leste.csv` supplement**
  (§5).
- **Scenario tags**: BAS / ATS / RAS codes or full names from §5. Leave the
  scenario column empty for scenario-invariant data. Remember §3: device-
  stock economics can only land in the 7 hosting scenarios.
- **Shares must sum to 100** within each partition, every year (§4 rule 3).
- **Units**: state the unit in the column header, and check it against
  `residential_branch_variables_units.csv` for the branch you are filling —
  especially intensities (§3's four unit systems).
- **Sources**: a source column (institution, year, title) per row or per
  block. We turn these into the `?` citations in the model.
- **Full year coverage** for trajectories (2014→2060 for the device-stock
  work, 2025→2060 for projection-only data) — imports overwrite the whole
  trajectory, so gaps become interpolation artifacts.

Questions, or a branch/variable you need that isn't in these files: reply to
the modelling team — if it isn't in this package, it doesn't exist in the
area yet, and structure changes have to go through us.

---
*Exported from LEAP area `aeo9_v0.67_w_results`, "Export Expressions" workbooks,
2026-07-02. Package assembled 2026-07-03.*
