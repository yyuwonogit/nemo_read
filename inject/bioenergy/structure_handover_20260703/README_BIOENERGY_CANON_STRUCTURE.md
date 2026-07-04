# Bioenergy Team — Canonical LEAP Structure Package (2026-07-03)

## 1. What this package is

This is the **canonical structure** of the LEAP supply tree your data feeds,
exported directly from the working model (`aeo9_v0.67_w_results`) on
2026-07-02. Everything in here comes from the model itself, not from
documentation or memory — treat it as the ground truth for branch names,
variable names, and units.

**Why you're getting it:** the CSVs you send us are pushed into LEAP by an
automated pipeline. That pipeline only accepts rows whose branch path,
variable name, and unit match the model **exactly** — anything else is
filtered out and never reaches LEAP. This package lets you check your rows
against the real structure before sending, without needing LEAP or any of
our tooling. Plain text and CSV only; opens in Excel or any editor.

Files in this package:

| File | What it is |
|---|---|
| `resources_tree.txt` | The full `Resources\` branch list — one line per fuel branch, with every variable that exists on it. 62 branches. |
| `resources_branch_variables_units.csv` | The same 62 branches flattened to one row per (branch, variable) with the exact `units`, `scale`, and `per` LEAP holds. **This is your unit reference.** |
| `keys_slice_bioenergy.txt` | The two `Key\` assumption structures wired to bioenergy: `Key\Biofuel Blending Targets` and `Key\Optimized Trade` (495 trade-route branches). |
| `keys_slice_bioenergy_units.csv` | Units for those Key branches (blend targets are `Volume %`; trade routes are on/off switches plus ID plumbing). |
| `current_expressions_resources_4scenarios.csv` | **What is currently written in the model** for every Resources branch — the live expressions, scoped to the 4 scenarios that matter (see the "Current model contents" section below). |
| `current_expressions_keys_slice_4scenarios.csv` | Same, for the bioenergy Key slice (blend targets + trade routes). |

## 2. Your tree in brief

Everything you author lives under `Resources\Primary\<Fuel>` and
`Resources\Secondary\<Fuel>` (plus the biodiesel/bioethanol production
processes under `Transformation\`, which keep their existing CSV shape).

The Resources tree is **completely flat**: all 62 branches are leaves
exactly three levels deep (`Resources\Primary\Palm Oil`,
`Resources\Secondary\Ethanol`, …). No branch has children. There are 29
Primary fuels and 33 Secondary fuels, and every fuel carries the same base
set of ~15 variables, materialised for all 12 region slots.

The five CSV-authored crops — **Cassava, Coconut Oil, Corn, Palm Oil,
Sugarcane** — carry two extra variables: `Area Harvested` and `Crop Yield`.
In the model, the production cap on four of them (Cassava, Coconut Oil,
Palm Oil, Sugarcane) is derived from them:

```
Maximum Production = Area Harvested[Thousand ha] * 1000 * Crop Yield[t/ha]
```

That formula appears on 448 rows across regions and scenarios — so when you
update those four crops, the primary numbers to get right are Area
Harvested and Crop Yield; the cap follows. **Corn is the exception**: it
carries the two variables too, but its cap is authored directly as tonne
trajectories per country — update Corn's `Maximum Production` itself.

**Raw-crop tonnes convention (confirmed in the model):** all 5 crops plus
Molasses and Palm Oil Mill Effluent (POME) have `Maximum Production` in
**Metric Tonne**, and no fuel mixes cap units across regions. Crop tonnes
mean the raw harvested product — fresh fruit bunches for Palm Oil, cane for
Sugarcane, fresh root for Cassava, nuts-in-shell for Coconut Oil, grain for
Corn — **not** the extracted oil/sugar.

One spelling trap: the coke branch is spelled `Resources\Secondary\
Metalurgical Coke` in the model — single "l". Match it verbatim; a
corrected spelling will not resolve.

## 3. The variables you author (units as LEAP holds them)

From `resources_branch_variables_units.csv` (units / scale / "per" columns
shown exactly as the model stores them):

| Branch | Variable | Units | Scale | Per |
|---|---|---|---|---|
| Primary crops (Cassava, Coconut Oil, Corn, Palm Oil, Sugarcane) | Area Harvested | ha | Thousand | |
| Primary crops (same 5) | Crop Yield | t/ha | | |
| 5 crops + Molasses + POME | Maximum Production | Metric Tonne | | |
| 5 crops + Molasses | Production Cost | 2020 USD | | Metric Tonne |
| POME | Production Cost | 2020 USD | | Tonnes of Oil Equivalent |
| Cassava, Coconut Oil, Palm Oil, Sugarcane, Molasses | Import Cost | 2020 USD | | Metric Tonne |
| POME | Import Cost | 2020 USD | | Kilogramme |
| Corn | Import Cost | 2020 USD | | Tonnes of Coal Equivalent |
| Secondary Biodiesel, Ethanol | Maximum Production | Gigajoule | | |
| Secondary Biodiesel, Ethanol | Production Cost / Import Cost | 2020 USD | | Liter |
| Secondary Methanol | Import Cost | 2020 USD | | Metric Tonne |

Costs are in constant **2020 USD** wherever a vintage is tagged. If your
source is in another year's dollars or another physical unit, say so in the
note/source column — we convert on our side — but the row you author should
target the LEAP unit above.

Two variables you will see in the files but should NOT author values for:
`Minimum Production` (held at 0 everywhere) and `Minimum Imports` (managed
centrally — it acts as a forced import floor and is easy to break).

## 4. Expression conventions

Your trajectories are written as LEAP expressions. The rules:

1. **`Interp(year, value, year, value, ...)` — comma between items, period
   for decimals. No exceptions.** `Interp(2025, 3.2422, 2030, 3.0833)` is
   right; `Interp(2025; 3,2422; ...)` (semicolons or comma decimals) will be
   rejected before it ever reaches LEAP.
2. **`?` comments for source citations — encouraged.** Anything after a `?`
   in an expression is a comment LEAP ignores, and the model uses this as
   its provenance layer, e.g. `40 ? 1st 1o1 Country Consultation Workshop
   for RE LTRM: Indonesia`. Please cite your source name (ERIA, OECD-FAO,
   national statistics, …) after a `?` where you can.
3. **`Remainder(100)`** — where a set of sibling shares must sum to 100%,
   the model closes the partition by putting `Remainder(100)` on the *last*
   sibling. Rare in the Resources tree, but if you author any share split,
   follow that pattern.
4. **`InterpFSY(...)`** is the idiom for policy targets (it starts
   interpolating at the first scenario year). The biofuel blend mandates use
   it, e.g. Indonesia Biodiesel `InterpFSY(2023, 35, 2025, 40, 2050, 50)`.
5. **Never write the literal word `Unlimited`** in anything you author.
   The model export translates it to 10^12, which at best un-caps the fuel
   silently and at worst breaks the optimisation. If a cap is genuinely not
   binding, use a generous round number (e.g. 10000 or 100000 in the cap's
   unit) instead.
6. **Every cap needs a companion cost.** Any fuel/region with an open
   production route (`Maximum Production` non-zero) must also have a real
   `Production Cost`; any open import route needs an `Import Cost`. A cap
   with a zero cost tells the optimiser "free energy here" and it will
   route the whole region's supply through it (this has actually happened —
   see §7).

## 5. Scenarios and regions — where your data lands

The model has 11 scenarios. Your authored data (caps, costs, crop physicals)
lands in **Regional Aspiration Scenario (RAS)** and **Carbon Neutrality_
Net Zero Scenario (CNZ)** — in the current model those two scenarios differ
from the untouched baseline bloc by exactly the 553 cells our inject
delivered (largest chunks: Import Cost 193, Production Cost 136, Maximum
Production 105). You do not need to author per-scenario variants unless we
ask.

One structural quirk worth knowing: the Resources tree changes its variable
set by scenario. The 7 optimisation scenarios (RAS, CNZ, Set up, LCO
backup, RE LTRM ×3) carry `Minimum Imports` + `Maximum Imports`; the 4
accounting scenarios (Current Accounts, Baseline Simulation, AMS Target,
RAS test) instead carry `Imports` + `Cost of Unmet Requirements`. So if a
variable seems "missing", it may simply live in the other scenario family.

Regions: 12 slots — the 10 ASEAN member states, **Timor Leste**, and
**Base Template**. Base Template is LEAP's internal template, not a
country; never author data for it. Timor Leste is currently switched off in
the model calculation, and its rows travel in a **separate supplement
file** (`timor_leste_supplement.csv`), not in your main CSV — keep it that
way. Crop data is genuinely per-country (Area Harvested varies across ~9 of
the 12 region slots on average), so please keep authoring crops
country-by-country rather than one regional value.

## 6. Key-tree connections — the structures your sector wires into

Two `Key\` assumption structures drive bioenergy, both included in this
package (`keys_slice_bioenergy.txt` + `keys_slice_bioenergy_units.csv`):

**`Key\Biofuel Blending Targets`** — two branches, `Biodiesel` and
`Bioethanol`, each holding a blend-mandate trajectory (`Activity Level`, in
Volume %) per country per scenario. Example: Indonesia Biodiesel is
`InterpFSY(2023, 35, 2025, 40, 2050, 50)` in RAS (the B35→B40→B50 path).
Note for anyone comparing scenarios: the three RE LTRM scenarios differ
*here* — RE Coupling and Shared Energy Resources insert a 2030 intermediate
blend point (e.g. Indonesia `..., 2030, 45, ...`) that Policy Aligned does
not carry.

**`Key\Optimized Trade`** — 495 branches: 55 country-pairs × 9 traded
feedstock fuels (Biodiesel, Cassava, Coconut Oil, Corn, Ethanol, Molasses,
Palm Oil, Palm Oil Mill Effluent, Sugarcane). Each branch is a trade route:
`Activity Level` is the on/off switch (1 or 0) and the other four variables
are region/fuel ID plumbing. **The master switch is on (1) in RAS and CNZ
only, and off (0) in the other nine scenarios** — all 495 routes flip as
one block. This matters to you because blend mandates without import routes
for the feedstock can make the model unsolvable: a country mandated to
blend biodiesel but with no palm oil of its own must be able to import it.

Practical upshot: if you propose adding a traded feedstock or changing
which countries produce a crop, tell us — the trade-route table may need to
change with it.

## 6b. What is currently written in the model — for your review

The two `current_expressions_*_4scenarios.csv` files dump the expressions
**currently authored in the live model** for your branches, so you can
judge what to keep, correct, or replace.

- **Scope: four scenarios only** — `Current Accounts` (historical),
  `Baseline Simulation`, `AMS Target Scenario` (ATS), `Regional Aspiration
  Scenario` (RAS). The other seven scenarios are copies, derivatives, or
  internal plumbing — ignore them.
- **Region column**: `ALL (12 regions)` = every country holds the same
  expression (a template value — often the thing most worth replacing
  with country data). A named country = country-specific authoring.
- Columns: `branch_path, variable, scenario, region, expression, units,
  scale, per`. `? comments` inside expressions cite the current source.
- High-value review targets for bioenergy specifically: rows where
  `Maximum Production = Unlimited` on fuels you own; the `0.001`
  placeholder Import Costs (Cassava among them); `Production Cost = 0` on
  fuels with open production; and any `ALL`-region crop trajectory that
  should differ by country.
- What to send back: branch path + scenario + country + proposed
  value/series + source, for any row you can improve.

## 7. Known issues in your tree — we'd like your input

These came out of the structure audit. None of them are blamed on anyone —
some are deliberate design, some are placeholders that predate your data —
but you are the right people to judge the ones on bioenergy fuels.

1. **Zero-cost open production routes (191 fuel/region pairs in RAS).**
   These are fuels a region may produce (cap not zero — usually
   `Unlimited`) at a Production Cost of 0, i.e. free supply. The
   bioenergy-relevant ones: Secondary **Biodiesel, Ethanol, Domestic
   Biogas, Renewable Diesel, Sustainable Aviation Fuel** (all 12 regions
   each), **Corn** and **POME** (Base Template + Timor Leste), Charcoal (1
   region). For the secondary biofuels this is probably fine — their real
   cost sits on the production processes — but please confirm that reading
   for each fuel you own, or give us a Production Cost trajectory where it
   is not fine. (For context: an identical shape once routed all biodiesel
   production to Timor Leste, because it was the one region with free
   unlimited supply.) There are also 95 open-import pairs with Import Cost
   = 0, and 312 rows priced at a `0.001` placeholder (Cassava among them,
   with Ammonia, Blast Furnace Gas, Coke Oven Gas, Methanol) — real Cassava
   import prices welcome.
2. **POME Import Cost — please confirm the values.** The model currently
   holds a POME Import Cost in RAS (e.g. `Interp(2025, 0.306, ..., 2060,
   0.377269)` in 2020 USD per kilogramme) that was applied directly in LEAP
   during last cycle's fix and never made it back into the authored CSV. We
   want to bring it into your CSV next cycle so it survives future rebuilds.
   Please review those values (your CSV currently has POME Maximum
   Production + Production Cost only) and send back a confirmed or
   corrected trajectory.
3. **`Unlimited` caps still standing.** The model has 9,199 `Unlimited`
   rows, all on upper bounds (5,671 Maximum Production + 3,528 Maximum
   Imports; none on lower bounds, which is the dangerous kind). In RAS, 505
   Unlimited production caps remain. Thanks to your data, the fuels fully
   cleaned in RAS include all four cap-authored crops (Cassava, Coconut
   Oil, Palm Oil, Sugarcane); Corn, Molasses and POME are down to 2
   leftover rows each (Base Template + Timor Leste only). The remaining
   bulk is fossil/other-team territory (Natural Gas and all five coals are
   still Unlimited in all 12 regions) — nothing for you to fix, just so you
   know the audit sees your fuels as in good shape.
4. **Arable / Perennial land pseudo-fuels.** These two Primary branches
   model land as a fuel (1 GJ ≈ 1 ha anchor) — deliberate design, do not
   "fix". Two structural notes we are tracking: Perennial's cap is
   unit-tagged Cubic Meter while Arable's is Thousand Gigajoule (a unit-tag
   drift on the same anchor), and both carry `Maximum Imports = Unlimited`
   at Import Cost 0 in the optimisation scenarios — meaning free "land
   imports" if trade routes ever covered them. If you have a view on what
   these caps should be, we'll take it; otherwise we handle it.

## 7b. Coming next: the Transformation slice

The biodiesel / bioethanol / biogas **production processes** your feedstocks
feed (under LEAP's `Transformation\` tree) are not in this package yet — that
tree's export is in progress. You'll receive a follow-up drop with the same
file shapes (tree + branch×variable×units + current expressions, same four
scenarios) covering your conversion processes. Until then, keep authoring
Transformation-side data (process efficiencies, capacities) in the existing
CSV shape you've been using — nothing changes there.

## 8. What to send back, and in what shape

Same cycle as always — your working file is `bioenergy_leap_input.csv` with
its existing columns:

```
ams, branch, variable, expression, unit, fuel, source, note, src_csv, domain, data_confidence
```

- **Update values inside existing rows** (`expression`, and `source` /
  `note` / `data_confidence` where warranted). The structure — branch
  paths, variable names, units, the set of rows — is locked; check any new
  row idea against `resources_tree.txt` and
  `resources_branch_variables_units.csv` first, and coordinate with us
  before adding it.
- **Branch paths, variables, units exactly as in this package.** Backslash
  separators, exact spelling (including `Metalurgical Coke`), exact case.
- **Expressions per §4**: `Interp(year, value, ...)` with commas + periods,
  `?` source comments encouraged, no `Unlimited`, every cap accompanied by
  its cost row.
- **Timor Leste rows go in the separate supplement file**, never in the
  main CSV.
- You don't need to run anything — send the updated CSV (plus the
  supplement if TL changed) with a one-line summary of what changed, and we
  run the validation and the LEAP push. You'll get back a per-row report of
  anything that didn't match.

Specific asks for this cycle, in priority order:
1. POME Import Cost trajectory — confirm/correct (§7.2).
2. The zero-cost production routes on your fuels — confirm intentional or
   supply costs (§7.1).
3. Cassava Import Cost — replace the 0.001 placeholder (§7.1).

Questions or anything that looks wrong in this package: reply to the
modelling team — if your data disagrees with a *structure* fact in here,
the model export wins, but tell us anyway so we can check whether the model
itself needs fixing.
