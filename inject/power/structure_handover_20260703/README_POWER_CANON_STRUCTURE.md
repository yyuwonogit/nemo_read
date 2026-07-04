# Power — Canonical LEAP Structure Handover (2026-07-03)

For the power data team. You don't need LEAP, our repo, or any database
to use this package — everything referenced here is a plain text/CSV
file sitting next to this README.

> **READ THIS FIRST — your main tree is not in this package.** The
> `Transformation` electricity-generation tree (the power plants, their
> capacities, costs, efficiencies) has **not yet been exported** from
> the live model; its export is pending and will follow as a separate
> "Transformation slice" drop. What this package ships is the two trees
> your sector ALREADY wires into — the `Key\` assumptions tree (dispatch
> levers, transmission lines, lead times, job factors) and the
> `Resources\` fuel-supply tree (renewable potentials, fuel caps and
> costs). Both are exported directly from the live model. See §2 for
> what the follow-up Transformation drop will contain.

## 1. What this package is

This is the **canonical structure** of the power-relevant slices of the
LEAP model, exported directly from the live area `aeo9_v0.67_w_results`
on 2026-07-02. It is the ground truth for branch names, variable names,
and units in these two trees. Anything you send us must line up with
these structures exactly — spellings included (even the wrong ones, see
§7).

Files in this package:

| File | What it is |
|---|---|
| `keys_slice_power.txt` | The power-relevant slice of the `Key\` assumptions tree (129 branches), indented, with each branch's variables listed |
| `keys_slice_power_units.csv` | One row per (branch, variable) in that slice: units, scale, per — the authoritative unit reference |
| `resources_tree.txt` | The full `Resources\` fuel-supply tree (62 fuels: 29 Primary, 33 Secondary) with each fuel's variable panel |
| `resources_slice_power_units.csv` | Units for the Resources variables, per fuel |
| `current_expressions_keys_slice_4scenarios.csv` | **What is currently written in the model** for every branch in the power Key slice — the live expressions, scoped to the 4 scenarios that matter (see §6b) |
| `current_expressions_resources_4scenarios.csv` | Same, for the full Resources tree |

How to read them: in `keys_slice_power.txt`, each line shows the
branch's full LEAP path in square brackets and its variables after
`vars:`. `resources_tree.txt` is a flat list of the 62 fuel names with
their variable panels — it does not show the `Primary`/`Secondary`
split, so take each fuel's full path from the `branch_path` column of
`resources_slice_power_units.csv`. In the CSVs, `branch_path` is the
full LEAP path (backslash-separated), and `units`/`scale`/`per`
together give the unit (e.g. units=`MW`, or units=`2020 USD`, per=`t`).

## 2. Your trees in brief — and the one that follows later

**Pending: the Transformation slice.** The follow-up drop will cover
`Transformation\Centralized Electricity Generation` (and the
distributed-generation counterpart) — the process branches where each
power technology carries its plant-level data: exogenous/existing
capacity, capacity limits, capital and O&M costs, lifetime, process
efficiency, availability, and dispatch floors. (That list comes from
our injection records for this model, not from an export — treat exact
branch and variable names as to-be-confirmed until the slice arrives.)
Two Transformation branch names ARE already confirmed, because the live
Resources tree quotes them by formula: `Transformation\Centralized
Electricity Generation\Processes\Geothermal Flash_IDJW` (Indonesia) and
`...\Processes\Geothermal Flash` (Philippines) — see §6.

What IS in this package:

**The Key slice (129 branches)** — the assumption tree your sector's
levers live in:

| Group | Branches | What it holds |
|---|---|---|
| `Key\Capacity Additions Multiplier` | 11 | Per-technology build-rate multipliers: Solar, Wind, Hydro, Biomass, Geothermal, each with an `_EndYear` twin, plus `Fossil Fuel Dispatch Reduction`. Per-country factors in RAS (e.g. Solar: Brunei 5, Malaysia 4, Indonesia 1). The dispatch-reduction lever is live in RAS: `Interp(2023, 100%, 2030, 80%)` |
| `Key\Modeling Assumptions` | 16 | Construction lead times per technology in years (Coal 4, BECCS 10, Batteries 1, Biogas 3, …) + `Incumbent Generator DIspatch Phaseout` (50 years, all scenarios — note the capital "DI", §7) |
| `Key\Transmission` | 42 | 21 `Lines\<A>_<B>_{E,F,C}` interconnectors, each with a 13-variable panel (Activity Level, From/To Node, Maximum Flow in MW, Capital / Fixed OM / Variable OM Cost, Interest Rate, Lifetime, Efficiency, Fuel, plus two deactivated variables exported with a `!` prefix: `!Reactance`, `!Construction Year`); 10 `Nodes\<country>`; 10 `Demand Distribution\<country>`; 1 `Transmission Enabled\Electricity_`. Sub-national node names (P. Malaysia, Sarawak, Sabah, Sumatra, Kalimantan) appear only inside line names here |
| `Key\Job creations` | 22 | Employment factors for Solar/Wind/Hydro/Geothermal: EF_Construction / EF_Manufacturing (Job-Years), EF_OM (Jobs/MW), declining factors for CAPEX/OPEX, plus Local Manufacturing and Regionality Factor |
| `Key\Emission Externality Costs` | 9 | $ per unit pollutant for 9 species; e.g. Carbon Dioxide = `89.2` 2020 USD/t in all 4 scenarios |
| `Key\Cal\Transformation` | 13 | Our internal calibration factors for generation/refining (biomass_eff, Geothermal, Hydropower, Ngas_cc, Oil refining, …) — listed for completeness, ours to maintain |
| `Key\Annual EI Reduction` | 13 | Demand-side energy-intensity policy levers (shared with other sectors; shapes the electricity demand your plants must meet) |
| `Key\Region Group RE Targets` | 1 | `ASEAN All Regions Electricity` — a 4-variable renewable-target stub, every expression `0` (§7) |
| `Key\End_cap multip` | 2 | `RE_Fraction` (per-country, e.g. Cambodia 0.88, Indonesia 0.69) + `Total_` |

**The Resources tree (62 fuels)** — completely flat: every branch is
`Resources\Primary\<Fuel>` or `Resources\Secondary\<Fuel>`, no children,
and every fuel carries the same core panel (Maximum/Minimum Production,
Import/Export series, Production Cost, Import Cost, consumer prices).
For power, the load-bearing part is `Maximum Production` on the
renewable primaries — that is where resource potential caps live.

## 3. The variables you author

In the Key slice, almost every branch carries exactly ONE variable,
`Activity Level`, and the **unit does the typing** (factor, years, %,
MW, Jobs/MW, 2020 USD/t…) — check `keys_slice_power_units.csv` before
reading any number. The exceptions all sit in Transmission and the
RE-target stub: each Line carries the 13-variable panel listed in §2;
each `Nodes\<country>` adds `Region_`, each `Demand
Distribution\<country>` adds `Fuel_` + `Node_`, and `Transmission
Enabled\Electricity_` adds `Fuel___` + `Transmission Modeling Type`
(all region/fuel ID plumbing — ours to maintain, don't author it); the
Region Group RE Targets stub carries 4 variables (§7.4).

In Resources, the panel that matters to power:

| Variable | Unit | Notes |
|---|---|---|
| Maximum Production | **Terawatt-hour** on the 8 renewable/biomass primaries: Bagasse, Biomass, Geothermal, Large Hydro, Small Hydro, Solar, Wind, Wood | The renewable resource potential cap per country (e.g. Indonesia Solar `2311.3 ? National Grand Energy Strategy 2020-2024`) |
| Maximum Production | Gigajoule on Natural Gas, the 5 coals, Nuclear, and all 33 Secondary fuels; Petajoule on Crude Oil; Metric Tonne on the bio-crops | Fossil fuel supply context — currently uncapped (§6, §7) |
| Production Cost / Import Cost | various $ per unit | Every open supply route needs a companion cost — a cap with no cost lets the optimizer treat that supply as free (a real bug class we have already been burned by) |

Plant-level variables (capacity, plant costs, efficiency, availability)
are Transformation-side and arrive with the pending slice.

## 4. Expression conventions (non-negotiable)

Values enter LEAP as expressions. The house rules:

- **`Interp(year, value, year, value, ...)`** — COMMA between items,
  PERIOD as the decimal mark. `Interp(2023, 100, 2030, 80)` is right;
  semicolons or comma-decimals (`3,2422`) are wrong and will be
  rejected before import.
- **`? comment` provenance** — anything after a `?` in an expression is
  a comment. We encourage these for source citations; the live model
  already does this, e.g. Philippines Solar cap
  `3129 ? SRE RE potential database; based on 1910 GW and 18.7%
  capacity factor`. Name the actual source (IRENA, USAID-NREL, national
  ministry, grid operator plan).
- **Never write the literal word `Unlimited`** in anything you author.
  It becomes a broken numeric sentinel downstream — catastrophic on
  minimum/floor-type variables, and even on maximum-type variables it
  degrades the optimizer. If something needs a generous cap, use a
  large number.
- **Every supply cap you propose should come with a cost.** If you send
  us a Maximum Production series for a fuel, send the matching
  Production Cost (and Import Cost if importable) in the same drop.
- Deactivated variables export with a `!` prefix (`!Reactance`,
  `!Construction Year`) — they exist in the tree but LEAP ignores them.

## 5. Scenarios and regions — where your data lands

The model carries 11 scenarios; the 4 in your expression files are the
ones that matter (the other 7 are copies, derivatives, or internal
plumbing):

- **Current Accounts** — historical statistics (year ≤ 2024).
- **Baseline Simulation** — no-policy projection.
- **AMS Target Scenario (ATS)** — member-state targets.
- **Regional Aspiration Scenario (RAS)** — the main policy projection,
  and the scenario the optimizer actually runs. Power levers mostly
  differentiate here (e.g. Fossil Fuel Dispatch Reduction is `0`
  everywhere except RAS).

Regions: the 12 region slots are the 10 ASEAN member states plus
**Base Template** (a LEAP template holding default values — NOT a
country; you never author data for it) and **Timor Leste**. Timor Leste
currently holds template-grade defaults and is switched out of the
calculation; if/when you have Timor Leste data, send it as a
**separate supplement file**, never mixed into the main 10-country
data.

## 6. KEY CONNECTIONS — how the three trees wire together

Your sector sits at the junction of all three trees:

1. **Resources → Transformation (live, quoted verbatim from the
   model).** Indonesia's and the Philippines' geothermal resource caps
   are not plain numbers — they are formulas that read the
   Transformation tree. Indonesia, RAS:

   ```
   Resources\Primary\Geothermal:Maximum Production =
     23 * Transformation\Centralized Electricity Generation\Processes\
     Geothermal Flash_IDJW:Maximum Availability/100 * 8760
     / (Transformation\...\Geothermal Flash_IDJW:Process Efficiency/100)
     / 1000
     ? Ministry of Energy and Mineral Resources, Directorate General RE
       (23 GW of potential capacity)
   ```

   Philippines, RAS: `4*8760*60.96%/1000/(Transformation\Centralized
   Electricity Generation\Processes\Geothermal Flash:Process
   Efficiency/100) ? IRENA 2022`. Practical consequence: if you revise
   geothermal availability or efficiency on the Transformation side,
   these two countries' resource caps move automatically.

2. **Key → Transformation.** The Capacity Additions Multipliers, Lead
   Times, and the Incumbent Generator DIspatch Phaseout knob are
   consumed by Transformation-side formulas (per our operating records;
   the consuming expressions themselves arrive with the pending slice).

3. **Resources as fuel supply.** Natural Gas and all five coal types
   currently have `Maximum Production = Unlimited` in every country and
   every scenario (e.g. `Resources\Primary\Natural Gas` RAS: `Unlimited`
   for all 12 regions) — fossil fuel supply to power plants is
   effectively uncapped; only prices constrain it. The renewables are
   the opposite: capped per country in TWh with cited sources.

## 6b. What is currently written in the model — for your review

The two `current_expressions_*_4scenarios.csv` files are a full dump of
the expressions **currently authored in the live model** for these
trees, so your team can judge what to keep, correct, or replace.

- **Scope: four scenarios only** — Current Accounts, Baseline
  Simulation, AMS Target Scenario, Regional Aspiration Scenario. The
  other seven are copies/derivatives/plumbing — corrections to these
  four propagate.
- **Reading the region column**: `ALL (12 regions)` means every country
  currently holds the same expression (a template value — often exactly
  the thing worth replacing with country data, e.g. every Lead Time is
  currently one number for all of ASEAN). A named country means that
  row is country-specific.
- Columns: `branch_path, variable, scenario, region, expression, units,
  scale, per`. Expressions may carry `? comments` citing their source —
  that tells you where the current number came from. `? tbc` means the
  original author flagged it as unconfirmed.
- What we'd like back: for any row where you have better data, a note
  with the branch path, scenario, country, your proposed value/series,
  and the source. Highest-value targets: `ALL`-region rows holding
  round placeholder numbers, and every row whose comment says `tbc`.

## 7. Known issues in your trees — we'd like your input

Review requests, not blame — most of these predate everyone involved:

1. **`Incumbent Generator DIspatch Phaseout` — capital "DI" is the real
   spelling** in the model (`Key\Modeling Assumptions\Incumbent
   Generator DIspatch Phaseout`, 50 years in all scenarios). We keep the
   typo because path lookups are case-sensitive; don't "correct" it in
   anything you send, and don't let your tooling normalise it.
2. **Transmission `!Construction Year`** is deactivated on every line
   and holds `2020 ? to be confirmed after removing C` on
   `P.Malaysia_Singapore_E`; three other lines (`Vietnam_Cambodia_E`,
   `Laos_Cambodia_F`, `Laos_Myanmar_F`) carry similar
   "awaiting confirmation" comments, and the remaining 17 hold bare
   years between 2020 and 2040. Can you confirm actual commissioning
   years for the 21 interconnectors?
3. **Transmission `Lifetime_` = `80 ? too long for a lifetime? 5 Years
   is common contract`** — the model itself questions this value. What
   lifetime should interconnector economics use: asset life (~40–80y)
   or contract length (~5y)?
4. **`Key\Region Group RE Targets\ASEAN All Regions Electricity` is an
   all-zero stub** — all 4 variables are `0` in all scenarios: the
   region-wide RE-target machinery exists but is disabled. Is that
   intended, or should an ASEAN-level RE share target be active in RAS?
5. **Fossil supply is uncapped** (§6, point 3): Natural Gas and all five coals
   are `Unlimited` in every country and scenario. If your team holds
   national production/import capacity data, we'd rather cap these with
   numbers + costs than leave the sentinel in place.
6. **Unmet Load pricing convention** (operational knowledge from our
   infeasibility work — probe-derived, NOT part of the canon exports in
   this package): the model keeps `Unmet Load_*` slack processes in
   Centralized Electricity Generation, which must stay visible and
   carry positive Variable OM Cost + Fixed OM Cost (typically 500,
   including the node-specific Indonesia/Malaysia variants) so that
   unmet electricity demand becomes an expensive result instead of a
   solver failure. When the Transformation slice arrives, please review
   these branches with us rather than zeroing or hiding them.

## 8. What to send back, and in what shape

CSV or spreadsheet, one row per (country, branch/quantity, year or
series), using the branch paths as they appear in
`keys_slice_power.txt` / `resources_tree.txt`. Specifically useful:

1. **Renewable potential revisions** — country × fuel (Solar, Wind,
   Geothermal, Large/Small Hydro, Biomass, …) × TWh cap, with source.
2. **Fossil supply caps + costs** — if you want §7.5 fixed: country ×
   fuel × Maximum Production series AND the companion Production
   Cost / Import Cost series (never a cap without a cost).
3. **Transmission line data** — Maximum Flow (MW), costs, efficiency,
   lifetime, construction year per interconnector (§7.2–7.3).
4. **Lead times and multipliers** — country-specific values for any
   `ALL (12 regions)` template row you can improve.
5. **Answers to the §7 questions**, referenced by branch path.

Every row should carry a source/provenance column. Year ≤ 2024 is
treated as historical (Current Accounts); projections should say which
scenario they belong in (BAS/ATS/RAS). Timor Leste rows go in a
separate supplement file.

Questions → yudiandra.y@gmail.com. Please reference branch paths as
they appear in the `.txt` trees when reporting structure issues.
