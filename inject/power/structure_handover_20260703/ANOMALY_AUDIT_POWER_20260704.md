# Canon anomaly audit — POWER slice (`aeo9_v0.67_w_results`)

This file is **your team's slice of the full cross-sector anomaly audit**
(`CANON_ANOMALY_AUDIT_20260704.md`, generated 2026-07-04 by running detectors
over the flat canon exports for the four scenarios that matter — Current
Accounts, Baseline Simulation, AMS Target Scenario, Regional Aspiration
Scenario). We have pulled out only the items that touch branches **power
generation owns or authors** — i.e. your `Key\` power levers (Capacity
Additions Multipliers, Modeling Assumptions / lead times, Transmission lines,
Region Group RE Targets) and the `Resources\` fuels your plants consume
(renewable potential caps and their costs, Electricity import price). The
findings below are **verbatim from the master audit** — counts, `NEW`/`KNOWN`
tags, `VERIFIED`/`SUSPICIOUS` tags, and the 🔴/🟡/🟢 grades are unchanged. We
have added nothing and dropped no tags. Please **judge each item and fix or
confirm** the ones that are yours; where a defect actually lives in a shared
`Resources\` or `Key\` branch that other sectors also depend on, we flag it
with a **cross-tree note** so you know it is upstream context, owned/coordinated
elsewhere. A short "highest-leverage for your team" list is at the end.

> Note on the Transformation slice: the deepest power items (plant capacity,
> plant costs, efficiency, availability, dispatch floors, Unmet Load pricing)
> live on the `Transformation\Centralized Electricity Generation` tree. That
> tree **has now been exported and audited** — see the
> **§"Transformation anomalies" section at the end of this file** (findings
> T1–T11) for the graded results. Two Transformation
> branches also surface indirectly in Part B below because the
> Indonesia/Philippines geothermal resource caps read them by formula
> (§ cross-tree, Part B).

---

## Part A — Incorrectly inputted (anomalies in authored values)

### A7. Cross-region outliers / unit slips

- **NEW · SUSPICIOUS — Brunei Biomass Maximum Production = 8,773 TWh**, ~1,600×
  the sibling median and larger than all-ASEAN primary energy — near-certain
  unit slip (GWh/TJ intended). **Propagates**: Brunei Bagasse & Wood caps are
  authored as `Biomass:Maximum Production[TWh]`. *12 rows. Resources.*
  → Your item: this is a renewable resource **Maximum Production** cap on
  `Resources\Primary\Biomass` (and its Bagasse/Wood dependants) — squarely in
  the renewable-potential caps you own. A Brunei biomass potential of 8,773 TWh
  is not physical; please re-derive the intended value/unit and re-author the
  cap (and the two Brunei caps that reference it).

---

## Part B — Empty but important (graded)

### 🔴 RED — breaks the calc or actively distorts LP/results in the 4 scenarios now

2. **Zero-cost open supply/import routes.** *(KNOWN #24 · Resources)* In RAS,
   **191 (fuel,region) pairs have Maximum Production ≠ 0 with Production Cost =
   0** (incl. Nuclear at Unlimited + $0), and **95 pairs have open Maximum
   Imports with Import Cost = 0** (Refinery Feedstocks/Gas, Renewable Diesel,
   Arable/Perennial ×12). **Mechanism:** a cap-open, cost-zero route is a free
   lunch the LP exploits regardless of realism — the exact mechanism behind the
   2026-05-18 biodiesel-to-Timor-Leste and 2026-05-19 POME incidents.
   → **Your slice of this class:** `Resources\Primary\Nuclear` (Unlimited cap at
   $0 Production Cost) is a fuel your generation tree consumes, and any renewable
   primary whose cap is open while its Production Cost reads 0 falls in this trap
   (see the 🟡 `0.001` renewable-cost item below, which is the same failure shape
   one order of magnitude off zero). **Cross-tree note:** this is a
   **Resources-wide** class spanning crop and fossil fuels owned by
   bioenergy/fossil — the full 191/95-pair sweep is coordinated across those
   teams; power's responsibility is the renewable + Nuclear rows it consumes.

### 🟡 YELLOW — placeholder/template values silently shaping results (wrong numbers, not broken mechanics)

**Resources — renewable/fuel caps and prices you own or consume**

- **`Unlimited ? tbc` placeholder caps** survive on Biomass/Geothermal/Large
  Hydro/MSW (37 rows) → un-capped renewable supply in the very RAS scenario
  whose RE targets those caps should bind.
  → Your item: these are `Resources\Primary\{Biomass, Geothermal, Large Hydro,
  Municipal Solid Waste}` **Maximum Production** caps — the renewable-potential
  caps you author. `Unlimited` becomes a broken numeric sentinel downstream
  (never keep the literal word); replace each with a cited numeric TWh cap.

- **NEW — Electricity Import Cost = flat `100`** (2020 USD/MWh) in all 12 regions
  × 4 scenarios — the only price for cross-border power trade, a placeholder;
  RAS/CNZ enable the full trade route set, so the build-vs-import decision runs
  on a round template number.
  → Your item: `Resources\Secondary\Electricity:Import Cost`. Since the
  cross-border grid comes on in RAS/CNZ, this single round number directly
  drives the model's build-plant-vs-import-power choice. Please replace the flat
  100 with per-region, per-scenario import prices (with source).

- **NEW — Production Cost = `0.001` template** on the 7 variable renewables +
  Geothermal-class (all scenarios) and the crops/Molasses/MSW (CA/Baseline/ATS
  only — RAS has real injected costs). For crops this means the three
  non-optimized scenarios value feedstock at ~$0 → cross-scenario biofuel cost
  results are not comparable.
  → Your item: the **7 variable renewables + Geothermal-class** Production Cost
  = `0.001` is the renewable-cost convention on your resource fuels — the
  companion cost that keeps a capped renewable from being treated as free (the
  near-zero cousin of RED #2). Confirm whether `0.001` is the intended
  "effectively-free renewable resource" convention or should carry a real
  levelised resource cost. **Cross-tree note:** the crops/Molasses portion of
  this same finding is bioenergy-owned — not power's to fix.

- **Unlimited caps on Natural Gas + all 5 coals (12/12) in every scenario** —
  the fossil canonical authors costs but no caps → un-capped fossil supply (no
  depletion realism) and 1e12 LP-conditioning pollution.
  → **Cross-tree note:** these are the fossil fuels your power plants burn, but
  the `Resources\Primary\{Natural Gas, coals}` **Maximum Production** caps are
  **owned by the fossil team**. Flagged here because your handover README §7.5
  asks you for national production/import capacity data to replace the
  `Unlimited` sentinel with numeric caps + costs — coordinate with fossil.

**Keys — your power levers**

- **NEW — every transmission interconnector has Variable OM Cost = 0** (all
  1,008 `Key\Transmission\Lines\*` rows). Zero variable cost to move electricity
  across borders biases the LP toward trade; relevant once RAS/CNZ enable the
  grid.
  → Your item: the 21 `Key\Transmission\Lines\<A>_<B>_{E,F,C}` interconnectors
  each carry `Variable OM Cost_ = 0`. With the grid enabled in RAS/CNZ, a
  zero variable cost to wheel power across borders makes trade look artificially
  cheap against building generation. Please author a per-line Variable OM Cost
  (with source).

### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

- **Resources:** all-zero series on *closed* routes (cost 0 paired with cap 0 —
  unreachable today, but a tripwire target: reopening a cap without its cost row
  recreates the RED #2 exploit); "U.S. Dollar" vintage-less units (mostly on
  zero cells).
  → Your slice of this: the same closed-route pattern on your renewable
  primaries — a `Resources\Primary\{renewable}` fuel whose `Maximum Production`
  cap is 0 with `Production Cost` 0 is inert today, but it is the exact tripwire
  behind RED #2 above: if you ever reopen one of these caps without authoring its
  companion cost, you recreate the zero-cost open-route exploit. Grade is GREEN
  only while the route stays closed. **Cross-tree note:** this is a
  Resources-wide grading that also covers crop/fossil fuels owned by
  bioenergy/fossil.

---

## Additional power `Key\` open questions carried from your handover README §7

These three were named for your slice but are **not detector findings in the
master audit** — they come from your own handover README §7 (known issues in
your trees). They are listed here as context so nothing in your scope is lost;
they carry no audit `NEW/VERIFIED` tag or row count because they are review
questions, not detected anomalies:

- **`Incumbent Generator DIspatch Phaseout` — the capital "DI" spelling.**
  `Key\Modeling Assumptions\Incumbent Generator DIspatch Phaseout` (50 years,
  all scenarios). The typo is the **real** path in the model and lookups are
  case-sensitive — do **not** "correct" it in anything you send and don't let
  tooling normalise it. (Handover README §7.1.)
- **`Key\Capacity Additions Multiplier` per-technology build-rate levers**
  (Solar, Wind, Hydro, Biomass, Geothermal, each with an `_EndYear` twin, plus
  `Fossil Fuel Dispatch Reduction`). Per-country factors are live in RAS; review
  whether the multipliers and their end-year twins reflect current policy.
  (Handover README §2 / §7.)
- **`Key\Region Group RE Targets\ASEAN All Regions Electricity` is an all-zero
  stub** — all 4 variables (`Activity Level`, `Fuel_RE Target`,
  `Region Group Set`, `Region Group Set Element`) are `0` in all scenarios: the
  region-wide RE-target machinery exists but is disabled. Is that intended, or
  should an ASEAN-level RE share target be active in RAS? (Handover README §7.4.)

---

## Cross-tree note — geothermal caps read the Transformation tree

The Indonesia and Philippines `Resources\Primary\Geothermal:Maximum Production`
caps are **not plain numbers** — they are formulas that read
`Transformation\Centralized Electricity Generation\Processes\Geothermal
Flash_IDJW:Maximum Availability` / `Process Efficiency` (Indonesia) and
`...\Geothermal Flash:Process Efficiency` (Philippines). So those two countries'
renewable caps move automatically if geothermal availability/efficiency changes
on the Transformation side. Those Transformation-side inputs are now exported
and audited in this package — review the Geothermal Flash / Geothermal
Flash_IDJW availability and efficiency expressions in
`current_expressions_transformation_slice_4scenarios.csv` (and the graded
"Transformation anomalies" section below) alongside these two caps.

---

## Highest-leverage for your team

1. **Fix the Brunei Biomass Maximum Production = 8,773 TWh unit slip** (Part A7)
   — it is ~1,600× the sibling median and drags the Brunei Bagasse & Wood caps
   with it; a clear authoring error with a recoverable correct value.
2. **Replace the flat `100` Electricity Import Cost** (🟡) — it is the *only*
   price on cross-border power trade and directly sets build-vs-import once the
   grid switches on in RAS/CNZ.
3. **Retire the `Unlimited ? tbc` renewable caps** on Biomass/Geothermal/Large
   Hydro/MSW (37 rows, 🟡) — un-capped renewable supply in the exact RAS scenario
   whose RE targets those caps are meant to bind.
4. **Price the transmission interconnectors** (🟡 Keys) — all 1,008
   `Key\Transmission\Lines\*` rows have Variable OM Cost = 0, biasing the LP
   toward trade.
5. **Confirm the `0.001` renewable Production-Cost convention** (🟡) and sweep
   your slice of the **zero-cost open routes** class (🔴 #2, esp. Nuclear at
   Unlimited + $0) — the standing LP-exploit class with a documented incident
   history.

---

## Transformation anomalies

> **The Transformation slice has now been exported and audited.** The
> `Transformation\Centralized Electricity Generation` (+ Distributed) tree —
> the core generation tree the top of this file flagged — landed on 2026-07-04 as
> the three new files in this folder (`transformation_slice_tree.txt`, 1,100
> branches; `transformation_slice_branch_variables_units.csv`;
> `current_expressions_transformation_slice_4scenarios.csv`). This is **the
> core of your fleet** — every plant's capacity, cost, efficiency, availability
> and dispatch floor. It was anomaly-hunted over the same four scenarios
> (Current Accounts, Baseline Simulation, AMS Target Scenario, Regional
> Aspiration Scenario) and every finding below was re-run by an **independent
> verifier pass** — all counts here are the verifier's confirmed counts. Tags:
> `NEW`/`KNOWN` (KNOWN = already in the canon hygiene ledger §15, with the entry
> number), `VERIFIED`/`SUSPICIOUS` (SUSPICIOUS = existence confirmed but the
> grade turns on a judgment/LEAP-evaluation you must make), 🔴/🟡/🟢 grade.

### 🔴 RED — actively distorts the RAS LP result now

**T1. Free, unlimited, zero-cost capacity on six Malaysia `_MY*` generators —
the 160 GW phantom gas-turbine build.** *(KNOWN #35, sharpened to RED · VERIFIED)*
The six sub-national default copies **Gas Turbine_MYPE, Large Hydro_MYPE, Solar
PV_MYPE, Solar PV_MYSB, Solar PV_MYSR, Wind Onshore_MYSR** inherit LEAP's
zero-cost defaults on the authoring layer and were never overwritten with real
regional data. In RAS the NEMO/CPLEX solve exploited them directly:

- **Capital Cost = 0, Fixed OM Cost = 0, Variable OM Cost = 0** — free to build,
  free to keep, free to run; only fuel is costed. *Counts (4 scen × 12 reg):
  Capital Cost = 0 on 288/288 rows, Fixed OM Cost = 0 on 288/288, Variable OM
  Cost = 0 on 284/288* (the 4 non-zero are Solar PV_MYPE/_MYSB/_MYSR + Large
  Hydro_MYPE).
- **Maximum Capacity Addition = `Unlimited`** on exactly these zero-cost techs —
  the annual build cap is removed, so the LP can add unbounded capacity at zero
  investment cost. *(NEW · VERIFIED — 70 rows, RAS only: Gas Turbine_MYPE 12,
  Solar PV_MYSR 12, Large Hydro_MYPE 12, Wind Onshore_MYSR 12, Solar PV_MYPE 11,
  Solar PV_MYSB 11 — pairs 1:1 with the six zero-cost techs.)* This is the
  enabler that turned the zero-cost default into a real build.
- **Result, verbatim from the solved area:** Gas Turbine_MYPE Malaysia RAS
  `Optimized New Capacity = Data(2040, 160529) ?Optimized on 07/02/2026 11:41
  (NEMO/CPLEX)` — **160,529 MW** of free gas turbines for Malaysia, whose peak
  demand is ~20 GW; and Wind Onshore_MYSR Malaysia RAS `Data(2040, 19163.34)`.
  *(Precision note from the verifier: 160,529 MW is the largest genuine
  **generator** build in the RAS solution — the next real generators are Lithium
  Ion Batteries 119,320 MW and H2 Fuel Cell 59,804 MW; larger `Optimized New
  Capacity` numbers exist only on the ETD pass-through "Electricity" process,
  which is not a generator.)*

Two authoring gaps **compound** T1 on the same six techs (each is 🟡 in
isolation but multiplies the exploit):

- **Capacity Credit = 100** (LEAP default) on the same copies — full firm-capacity
  credit, so these free plants satisfy the Planning Reserve Margin at 100 % of
  nameplate, including the intermittent Solar PV_MY* and Wind Onshore_MYSR.
  *(KNOWN #35 · VERIFIED — 276/288 rows = 100; the other 12 are Solar PV_MY* at
  `18.8737644659 ? AEO7`. Correctly-authored VRE elsewhere: Wind Offshore = 20,
  Solar Floating = 18.61.)*
- **Process Efficiency = 100 on Gas Turbine_MYPE** — a gas turbine converting
  fuel to electricity with zero thermodynamic loss. It is the **only** combustion
  `_MY*` tech left at 100 %; the base Gas Turbine reads
  `33 ? Technology data Indonesian power sector`, Gas Combined Cycle_MYPE ≈ 42–60 %,
  Diesel_MYPE ≈ 45–47 %. At 100 % the 160 GW build burns ~1/3 the gas a real
  33–39 % turbine would, so its only genuine cost (fuel) is understated ~3×,
  and power-sector gas demand + CO₂ are understated in RAS. *(NEW · VERIFIED —
  48 rows; not separately in the ledger, which covers only Capital Cost /
  Capacity Credit.)*

**Fix:** author real Capital Cost + Fixed/Variable OM Cost, a finite Maximum
Capacity Addition, a realistic Capacity Credit, and (for Gas Turbine_MYPE) a
realistic Process Efficiency on all six `_MY*` techs — or retire the inheritance
copies so Malaysia's real branch governs. This is the single highest-leverage
correction in the slice: it collapses Malaysia's optimal capacity mix and system
cost today.

### 🔴 / 🟡 SUSPICIOUS — grade depends on how LEAP evaluates a dangling reference

**T2. `ScenarioValue(Bad Scenario [2])` dangling scenario reference in
`Endogenous Capacity`.** *(NEW · SUSPICIOUS — 20 rows, AMS Target Scenario only)*
Authored capacity-additions-ramp logic (clean-coal / geothermal / biomass /
hydro build ramps) resolves a `ScenarioValue(...)` against a scenario that no
longer exists. Verbatim: `Step(2020,0,2026,ScenarioValue(Bad Scenario [2])*50%)
? Clean coal utilization by 20% in 2036` and
`Interp(2020, ScenarioValue(Bad Scenario [2]), 2025, ScenarioValue(Bad Scenario
[2]) * Key\Capacity Additions Multiplier\Biomass:Activity Level[factor], 2050,
...)`. Confirmed 20 power rows, 100 % in AMS Target, 100 % on `Endogenous
Capacity`; regions **Philippines 8 / Vietnam 5 / Thailand 4 / Indonesia 3**;
techs Coal Ultrasupercritical (+CCS), Coal Subcritical_MYPE/_MYSR, Biomass
Gasification, Biomass Other_MYPE/_MYSB/_MYSR, Large Hydro_MYSB/_MYSR, Geothermal
Flash. **Grade hinges on your judgment: 🔴 if LEAP errors on the dangling ref
(breaks the AMS Target calc), 🟡 if it silently evaluates to 0 (the intended
endogenous build is zeroed).** `NEW` for power — canon ledger #2 records a
*distinct* 19-row instance in Industry AMS Target (an EI-reduction template);
this is a separate power occurrence not previously in the ledger.

### 🟡 YELLOW — authored hazards + placeholder/template values shaping results

**T3. §11.2c must-run trap — AUTHORED but VERIFIED INERT (downgraded from 🔴).**
*(KNOWN #33 · VERIFIED)* Bare `Minimum Utilization = Maximum Availability` (no
`Min()` guard) on variable-renewable process branches — the classic §11.2c
must-run authoring hazard. **28 rows, RAS only** (absent in CA / Baseline / AMS
Target): Wind Onshore_MYPE + Wind Onshore_MYSB replicated into the 11 non-Malaysia
regions (22 rows), plus Solar CSP, Solar Floating, Tidal, Wave, Wind Offshore
(Centralized) + Solar PV Rooftop (Distributed) in Base Template (6 rows).
**Currently inert:** every trap branch has zero effective capacity — the 22 Wind
Onshore inheritance copies read `Exogenous Capacity = 0`, `Node = 0`,
`Optimized New Capacity = 0`, and in Malaysia itself the same techs read
`Minimum Utilization = 0`; the decisive check is `Optimized New Capacity = 0` on
all 28 branches (the solver built nothing on them). A zero-capacity must-run
constraint binds nothing and cannot infeasible the solve — so this is an
**authored hazard that is currently harmless; it would bite the instant any of
these `_MY*`/Base-Template branches is given capacity.** *(Reconciliation: ledger
#33 records 27 for RAS; the +1 here is Distributed Solar PV Rooftop (Base
Template), which #33 omits. Verifier precision note: the 6 Base Template techs
carry a formula `Existing Capacity + Capacity Additions` rather than a literal
`0`, but Capacity Additions = 0 and Base Template is a non-calculated placeholder
region, so effective capacity is still 0 — conclusion unchanged.)*

**T4. Sibling-variant inconsistency across `_MYPE` / `_MYSB` / `_MYSR`.**
*(KNOWN #35 · SUSPICIOUS — divergence-span descriptor "12", not a defect-row
tally)* Within a Malaysia sub-national family the three `_MY*` variants carry
divergent authoring for the same (region, scenario, variable). Verified verbatim:
(a) RAS Indonesia Wind Onshore `Minimum Utilization`: _MYPE = `Maximum
Availability`, _MYSB = `Maximum Availability`, _MYSR = `0`; (b) RAS Malaysia
Solar PV `Maximum Capacity Addition`: _MYSR = `Unlimited` vs _MYPE/_MYSB =
`Interp(BaseYear, 0, 2021, 1000*20%, ...)`; (c) RAS Indonesia Large Hydro_MYPE =
Capital Cost 0 / Capacity Credit 100 / Efficiency 100 / Maximum Availability 100
(all defaults) vs _MYSB/_MYSR carrying real cost (`Interp(... 2200 ...)`),
`Capacity Credit = Maximum Availability`, efficiency `100*Key\Cal...\Hydropower`,
availability `51.77 ? last historical`. The `_MYSR` free-build copy is the one
that actually got built (T1). Needs human judgment: decide which sibling is
authoritative per (tech, variable) and align the family.

**T5. Solver output written back into authored input cells (input/output
conflation).** *(KNOWN — §1.1 idiom / ledger #8 analogue · VERIFIED)*
`Optimized New Capacity` input cells hold NEMO/CPLEX solver output stamped
`?Optimized on 07/02/2026 11:41 (NEMO/CPLEX)` — this is a solved (`_w_results`)
area with endogenous build written back into the authoring layer. **426 rows,
RAS** (379 `0 ?Optimized...` + 47 `Data(...) ?Optimized...`). Re-injecting or
re-authoring these cells would overwrite solver decisions; any consumer reading
them as pure inputs conflates exogenous authoring with endogenous results. *(The
identical 426 also exist in Carbon Neutrality, out of the 4-scenario scope —
power total across both optimization scenarios = 852.)* Treat `Optimized New
Capacity` as read-only solver output, not an authoring target.

**T6. Confessed placeholder — ASEAN Power Grid transmission Capital Cost.**
*(NEW · VERIFIED — 6 lines, RAS)* Interconnector `Capital Cost` authored as the
self-confessed `315 ? Placeholder cost` on **Sarawak_to_Brunei_8a,
Sarawak_to_Peninsular_3, Sarawak_to_Borneo_6, Thailand_to_Peninsular Malaysia_2,
Sarawak_to_Sabah_8b, East Sabah_to_Borneo_15** (Malaysia 5 / Thailand 1). A
guessed transmission investment cost driving RAS interconnector build economics.
*(Across all 7 optimization/policy-bloc scenarios this is 42 rows; only RAS is in
scope here.)*

**T7. Confessed placeholder — Wind Offshore Maximum Availability.**
*(NEW · VERIFIED — 48 rows, 12 regions × 4 scenarios)* `Wind
Offshore:Maximum Availability = 44 ? Placeholder from NREL ATB 2023 - average for
all wind classes (moderate)` applied uniformly to every region, including those
with no offshore-wind resource assessment — a placeholder capacity factor
shaping Wind Offshore output and economics. Single distinct expression; replace
with per-region assessed capacity factors.

**T8. Electricity T&D Losses = 0 on Indonesia and Singapore.**
*(KNOWN — §14 quirk #14 · VERIFIED)* `Electricity Transmission and
Distribution\Processes\Electricity:Losses = 0` — lossless T&D on the largest
ASEAN grid (Indonesia) and Singapore. **16 rows across Indonesia / Singapore /
Base Template / Timor Leste (4 each); 8 load-bearing** (Indonesia + Singapore ×
4 scenarios; Base Template + Timor Leste are non-calculated). Contrast:
Vietnam ≈ 11 %, Myanmar ≈ 27 % declining, Cambodia rising to 27 %. Lossless
delivery understates the generation and installed capacity needed to meet
Indonesia's demand in every scenario.

### 🟢 GREEN — benign, disabled, or cosmetic

**T9. `Maximum Production = Unlimited` on 63 power processes — benign
upper-bound flavour.** *(KNOWN #34 / #23 / §1.1 · VERIFIED)* 756 rows, RAS
(63 processes × 12 regions, present only in the optimization/policy scenarios),
including the ETD "Electricity" pass-through node where `Unlimited` is
appropriate. **Critically: this is the benign upper-bound sentinel, NOT the
catastrophic lower-bound forced-floor trap.** Cross-checked: `Exogenous Capacity`
containing `Unlimited` = **0 rows in the entire power domain** — the §A.11 1e12
`ResidualCapacity` floor (ledger #34's fossil-blending shape) is **absent in
power**. Only the benign upper-bound sentinel + its LP-conditioning noise
remains; supply on the coal/gas processes stays bounded via capacity caps
elsewhere.

**T10. `Renewable Target = 0` — inert module-level RE knob.**
*(KNOWN — §1.2 · VERIFIED)* The module-level renewable-target lever is `0` in
every row it appears (24 rows across the 2 electricity modules × 12 regions;
within the 4-scenario scope it exists only in RAS). RE ambition is enforced
instead via biofuel blend mandates, per-tech Minimum Share of Production, and the
`ASEANRenewableCapacityTarget` / `RenewableCapacityTarget` `__NEMOcc` custom
constraints. Benign, but a silent no-op if a future author relies on this knob.

**T11. `_x000D_` Excel carriage-return artifacts in comment strings.**
*(KNOWN #14 / quirk #27 · VERIFIED)* 2,994 power rows carry `_x000D_` literal
carriage-returns inside the post-`?` provenance-comment portion of cost/efficiency
expressions (Capital Cost 708, CCS VOM 576, CCS Capital 576, Fixed OM Cost 328,
CCS FOM 288, Variable OM Cost 280, Process Efficiency 108, Maximum Availability
77, + ~53 others). Cosmetic — sits in the comment, does not corrupt the numeric
expression — but pollutes any downstream text parse of the provenance notes.
*(Full-roster power total = 8,302 rows.)*

### Cross-tree note — fossil blending Exogenous Capacity = `Unlimited` (upstream, fossil-owned)

Not a power finding, but the reason power's own tree is clean of the dangerous
sentinel is worth stating so it does not get conflated: the four **biofuel-mandate
blending pseudo-techs (Gasoline / Diesel Blending)** carry `Exogenous Capacity =
Unlimited` (unit Megawatt) on the **fossil** side of the Transformation tree.
Because `Unlimited` exports to the `1.0e+12` sentinel, on a lower-bound variable
like `Exogenous Capacity` → `ResidualCapacity` this becomes a **forced 1e12
floor** — the §A.11 lower-bound trap, the exact 2026-05-12 p9 shape. *(KNOWN
ledger #34 · fossil-owned.)* Power's `Exogenous Capacity` has zero `Unlimited`
rows (verified, see T9), so this floor does **not** exist on any power branch —
but the fossil blending floor sits in the same solved LP, so coordinate with the
fossil team before the next recalc.

### Highest-leverage for the Transformation slice

1. **Fix the six free-build `_MY*` generators (T1).** Real costs + finite
   Maximum Capacity Addition + realistic Capacity Credit + Gas Turbine_MYPE
   efficiency. This is the largest single distortion in the RAS solution —
   160,529 MW of phantom free gas turbines for a ~20 GW-peak grid.
2. **Resolve the `Bad Scenario [2]` dangling ref (T2)** — confirm whether AMS
   Target errors or silently zeroes the endogenous build ramps on those 20 rows;
   the grade (🔴 vs 🟡) and whether AMS Target is even calculable depend on it.
3. **Align the `_MYPE` / `_MYSB` / `_MYSR` siblings (T4)** — decide the
   authoritative variant per (tech, variable); T1 is a symptom of this.
4. **Replace the confessed placeholders (T6 `315`, T7 `44`)** — both carry `?
   Placeholder` in the live expression and drive RAS interconnector / offshore-wind
   economics.
5. **Author non-zero T&D Losses for Indonesia and Singapore (T8).**

Leave alone (verified benign): the inert must-run trap (T3, until capacity is
ever added), the benign `Maximum Production = Unlimited` (T9), the inert
`Renewable Target` (T10), and the cosmetic `_x000D_` artifacts (T11). Treat
`Optimized New Capacity` (T5) as read-only solver output, not an authoring
target.
