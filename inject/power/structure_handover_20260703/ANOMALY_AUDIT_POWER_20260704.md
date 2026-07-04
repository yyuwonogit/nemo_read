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

> Note on the Transformation slice: several of the deepest power items
> (plant capacity, plant costs, efficiency, availability, dispatch floors,
> Unmet Load pricing) live on the `Transformation\Centralized Electricity
> Generation` tree, which has **not yet been exported** — those are **pending
> that export** and are therefore NOT audited here yet. Two Transformation
> branches already surface indirectly below because the Indonesia/Philippines
> geothermal resource caps read them by formula (§ cross-tree, Part B).

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

## Cross-tree note — geothermal caps read the Transformation tree (pending export)

The Indonesia and Philippines `Resources\Primary\Geothermal:Maximum Production`
caps are **not plain numbers** — they are formulas that read
`Transformation\Centralized Electricity Generation\Processes\Geothermal
Flash_IDJW:Maximum Availability` / `Process Efficiency` (Indonesia) and
`...\Geothermal Flash:Process Efficiency` (Philippines). So those two countries'
renewable caps move automatically if geothermal availability/efficiency changes
on the Transformation side. The Transformation-side inputs those formulas depend
on are **pending the Transformation slice export** and are **not audited in this
file yet** — revisit once that slice arrives.

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
