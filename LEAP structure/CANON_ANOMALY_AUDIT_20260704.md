# Canon anomaly audit — `aeo9_v0.67_w_results`

> Full-corpus anomaly sweep over all seven canon exports (the six Demand/
> Key/Resources trees in Parts A–B, plus the `Transformation\` tree added
> 2026-07-04 in **Part C**), scoped to the four scenarios that matter
> (**Current Accounts, Baseline Simulation, AMS Target Scenario, Regional
> Aspiration Scenario**). Generated 2026-07-04 by running systematic
> detectors over the flat digests (offline; no LEAP COM). Two parts, as
> requested: **(a) incorrectly inputted** — anomalies in what is authored;
> **(b) empty but important** — missing/placeholder values, graded
> 🔴 red / 🟡 yellow / 🟢 green. Every item flags **NEW** vs **KNOWN** (already
> in the anatomy §14/§15 hygiene ledger) and **VERIFIED DEFECT** vs
> **SUSPICIOUS — needs human judgment**. Counts are rows in the 4 scenarios.
>
> Methodology note: transport / residential / resources came from the
> multi-agent hunt (self-verified, ledger-cross-checked); keys / commercial /
> industry were detected directly in this session after the agent run hit
> model limits; Transformation (Part C) from a 3-domain hunt + verifiers.
> Where an item says "needs a LEAP UI check" it cannot be settled from the
> export alone.

---

## Part A — Incorrectly inputted (anomalies in authored values)

### A1. Wrong cross-reference / copy-paste of the wrong branch

- **NEW · VERIFIED — Truck Natural Gas *Sales* cites the *Electricity*
  sales-share key.** `Demand\Transport\Road\Truck\Natural Gas:Sales` =
  `…Vehicles_Sales_Share\Truck\`**`Electricity`**`:Activity Level / 100 *
  …Vehicle_Sales\Truck`. The correct `…\Truck\Natural Gas` share exists and
  is all-zero; the cited Electricity share ramps 0→28 % by 2060 (RAS). Result:
  a **phantom NG-truck fleet duplicating the EV-truck fleet** (truck sales
  partition sums to ~128 % in RAS), burning gas at the defective 5 MPG (A5).
  Only Truck\Natural Gas is permuted; all sibling classes cite their own fuel.
  *48 rows in scope (132 whole-export). Transport.*

### A2. Region permutation (one country's data/comment landed on another)

- **NEW · VERIFIED — Crude Oil `Additions to Reserves` is region-scrambled in
  Baseline + AMS Target.** RAS holds the 10 values correctly aligned; Baseline
  and ATS hold them shuffled, and the source comments prove it: Malaysia gets
  Indonesia's value + "SKK Migas" (Indonesia's regulator), Philippines gets
  Malaysia's "PETRONAS Activity Outlook", Laos gets Thailand's "DMF Thailand",
  Indonesia (a major producer) gets "0 ? No commercial production", Myanmar
  gets Laos's "Landlocked no upstream". Extending the check to all fuels:
  **Crude Oil is the only permuted fuel** — the other comment-region hits (RFO
  "Derived from SG CIF crude" ×22, Gasoline "Platts FOB Singapore") are
  legitimate benchmark citations. *18 rows. Resources.* (This is the defect the
  fossil guide §7.3 flagged; now proven via the comments.)

### A3. Separator / decimal-locale violations (§A.15 / §A.20)

- **NEW · VERIFIED — semicolon-form `Data()` in live code.** The same
  Baseline+ATS Crude Oil ATR layer is committed as `Data(2024; 1.1)` — the
  forbidden semicolon list-separator, in the area itself. The RAS copy uses
  correct commas → the two layers came in through different authoring paths.
  *20 rows. Resources.*
- **NEW · VERIFIED — full European-locale expression.** Philippines Electricity
  Other Consumer Price (RAS) = `LinForecast(2005; 31,29; 2006; 31,29; …)` —
  semicolon separators **and** comma decimals. Siblings use the correct
  period-decimal form. *1 row. Resources.*
- **KNOWN + NEW extent — comma-decimal arithmetic beyond the ledger.** Ledger
  #26 recorded 9 Philippines Natural Gas rows (`…*1,0551`). The class actually
  spans **8 more Philippine fuels** — Avgas `…/(159*44,8000*0,7300)`, Bitumen,
  Charcoal `…/28,8800`, Jet Kerosene, Kerosene, LPG, Naphtha, Residual Fuel
  Oil — comma-decimals inside parenthesised multiplication where they cannot be
  list separators. *58 rows total in scope, all Philippines. Resources.*
  Bonus suspicion: even de-comma'd, the NG `*1.0551` looks **inverted** (GJ↔MMBTU
  conversion should divide) — needs a human math check.

### A4. Duplicate branch / parallel-tree double count

- **NEW · VERIFIED — two branches share the path
  `…Historical\Charcoal\Carbon Monoxide`.** branch_id 8996 = `189` kg/**tonne**,
  branch_id 9008 = `26` kg/**TJ**. Both live in all 4 scenarios × all regions →
  **charcoal CO emissions computed twice**, on two different bases. The only
  duplicate-named pollutant leaf in the sector. *96 rows. Residential.*
- **NEW · VERIFIED (expression-level) — old and new appliance trees both
  active.** `Refrigeration` (old, share-based) and `Refrigeration_` (new,
  device-stock) both carry non-zero saturation **and** non-zero intensity in
  Baseline/ATS/RAS, while the new tree is inert in CA (Useful_EI = 0). So
  projection scenarios carry ~double the fridge (and AC) electricity relative
  to the calibrated CA basis. Magnitude needs a results harvest; simultaneous
  activation is verified. *178 rows + AC analogue 78. Residential.* (Confirms
  anatomy §10.5's previously-"unverified" exposure.)
- **NEW · VERIFIED — CA Road Stock series pasted across vehicle classes.** The
  same historical `Data()` series is byte-identical on Bus, PassengerCar and
  Truck for a given (region, fuel); summing 2024 stock across powertrains gives
  bus fleets **26–177× larger** than the Key `BaseYear_StockData` (Indonesia
  74×, Malaysia 166×, Philippines 177×). The series look like all-class fuel
  totals reused per class. *106 rows / 32 (region,fuel) groups. Transport.*

### A5. CA → forward-scenario discontinuities (level jumps at the 2024/25 seam)

- **KNOWN · VERIFIED — Truck NG Fuel Economy 12 → 5, Indonesia only**, in all
  forward scenarios (the sole per-region override in the FE panel); compounds
  the phantom-fleet defect (A1). *10 rows. Transport.*
- **NEW · VERIFIED — fridge ownership collapses 2022→2023.**
  `Key\Residential\Refrigeration\Percent Ownership` splices two sources inside
  one Interp: Philippines 88 → 50 (−38 pp), Indonesia 97.6 → 89, Vietnam 100 →
  80.5 — a physically impossible one-year drop in **9 of 11 countries**, and it
  drives the whole `Refrigeration_` device-stock saturation. *36 rows.
  Residential/Keys.*
- **NEW · SUSPICIOUS — AC Useful Energy Intensity switches basis at the seam.**
  CA holds country-study `<coef>*!EER` formulas, projections hold unrelated
  constants: Thailand ~13,062 → 616 kWh/hh (21×), Cambodia 7×, Philippines 5×,
  Myanmar jumps up 4.6×. **7 of 12 regions shift >3×.** *48 rows. Residential.*
- **NEW · SUSPICIOUS — lighting tech-shares re-classified at the seam.** CA has
  Fluorescent = Halogen = 0 with CFL = Remainder(100); every projection restarts
  Fluorescent at 8–20 and Halogen at 2–4 in 2025 → the lamp mix (and thus
  lighting intensity) jumps up to ~22 pp in one year. *68 rows. Residential.*

### A6. Within-series data corruption

- **NEW · VERIFIED — Indonesia 2015 Stock is exactly /129.4 of its neighbours**
  in 5 independent series simultaneously (identical divisor ⇒ systematic source
  slip, not noise). *5 series. Transport.*
- **NEW · SUSPICIOUS — mid-series level shifts (source splices)** ≥5× in CA
  Stock: Thailand Blended Gasoline 382 → 196,447 (514×), Malaysia Electricity
  25 → 4,777 (191×), etc. *17 series. Transport.*

### A7. Cross-region outliers / unit slips

- **NEW · SUSPICIOUS — Brunei Biomass Maximum Production = 8,773 TWh**, ~1,600×
  the sibling median and larger than all-ASEAN primary energy — near-certain
  unit slip (GWh/TJ intended). **Propagates**: Brunei Bagasse & Wood caps are
  authored as `Biomass:Maximum Production[TWh]`. *12 rows. Resources.*
- **NEW · SUSPICIOUS — NGL Brunei Additions to Reserves = 0.2237 bare "Metric
  Tonne"** (0.22 t as a national reserve is meaningless — lost its Billion-BOE
  scale tag). *4 rows. Resources.*
- **NEW · SUSPICIOUS — residential intensity outliers:** Vietnam Clothes Dryer
  3.1 vs sibling 585 (189× low), Myanmar Water Heating 0.6 vs 116 (193× low),
  Malaysia Cooking NG 0.1 vs 25 — per-owning-household vs per-household basis
  slips. *10 rows. Residential.*

### A8. Dangling references / corrupted tokens

- **KNOWN · VERIFIED — `!Missing Branch` + `Bad Scenario [2]` templates are LIVE
  in AMS Target Scenario.** Industry Historical-fuel FEI carries
  `InterpFSY(!Missing Branch (ID=3477)!, ScenarioValue(Bad Scenario [2], …))`
  and `Interp(!Missing Branch (ID=3465)!, …)`. *140 + 19 rows. Industry.*
- **KNOWN · VERIFIED — commercial `!Missing Branch (ID=1687/825)`** on
  Historical Ethanol/Biodiesel FEI regression shells (Baseline). *72 rows.
  Commercial.*
- **KNOWN · VERIFIED — `Bad Unit [777518900/777691684]`** on Cement Clinker
  technology FEI, **240 rows in every one of the 4 scenarios (960 in scope)**.
  Industry.

### A9. Single-region formula deviations (stray edits)

- **NEW · SUSPICIOUS — Philippines aviation FEI carries a trailing `1%` growth
  arg** (`Interp(2021, Value(2019)*80%, 2022, Value(2019), 1%)`) on Jet Kerosene
  **and** SAF → +1 %/yr forever (+46 % by 2060); every other region holds flat.
  *20 rows (6 in scope). Transport.*
- **NEW · SUSPICIOUS — Brunei PassengerCar Blended Diesel Mileage Correction
  Factor = `Interp(2024,1,2030,0.9)`** while 764 of 768 rows are the constant 1
  — a lone uncommented deviation (looks like a forgotten test edit). *4 rows.
  Transport.*
- **NEW · SUSPICIOUS — PassengerCar First Sales Year = `2024`** on all four
  powertrains while every Bus/Motorcyle/Truck powertrain uses `BaseYear` — an
  unexplained per-class methodology split affecting stock-turnover vintaging.
  *48 rows. Transport.*

### A10. Solver output written into inputs / sentinel literals

- **KNOWN — NEMO/CPLEX `Data(…) ?Optimized on 07/02/2026 (NEMO/CPLEX)`
  writebacks** on Refrigeration_/AC_ tier Activity Levels (RAS) — authored input
  and solver output conflated. *180 rows. Residential.*
- **KNOWN — literal `Unlimited`** on Maximum Devices / Maximum Device Additions
  (device twin of the §A.11 1e12 trap). *432 rows. Residential.*

### A11. CR artifacts inside live code

- **KNOWN — `_x000D_` before the `?`** in 334 residential live expressions
  (lighting formula, AC Lookup arg lists) and 10 transport IW FEI `If()`
  formulas. *Residential 334, Transport 10.*

### A12. Comment hygiene hiding data problems

- **KNOWN — transport SAF:** Indonesia comment says "only available in AREC and
  ASER" yet the mandate is authored across the RAS bloc; Thailand carries a
  superseded expression inside a `??` double-comment (the version ATS actually
  uses) → the two scenarios silently swapped provenance. *Transport.*
- **KNOWN — residential `~`-dialect dead equations inside live Lookup**, the
  undocumented `×2` AC multiplier, and 3 inconsistent ownership methods across
  countries. *61 rows. Residential.*
- **KNOWN — resources `?~Former expression:` reverted caps** (RAS less
  constrained than ATS on Thailand Biomass), `~`-dialect ×101, `_x000D_` in
  comments ×32. *Resources.*

### A13. Naming / typos

- **KNOWN — `Motorcyle`** (demand) vs `Motorcycle` (Key) — name-based joins
  break. Transport. · **KNOWN — `Metalurgical Coke`** (referenced by name in 48
  Import Cost expressions — a rename must update them). Resources. · **NEW —
  `? ACE defult`** comment typo hides 16 Water Heating placeholder rows from
  "default" greps. Residential.

### A14. Other structural

- **KNOWN — `Demand\Transport_` underscore self-references** in TotShare_AltFuels
  / Share_FossilFuels (96 rows) — resolves in-LEAP but breaks offline joins.
- **NEW · SUSPICIOUS — `!EER` (leading-bang deactivation-convention name) is
  live and load-bearing** in the AC efficiency chain (192 rows) — a future
  cleanup that deactivates it would zero AC efficiency.
- **KNOWN — dollar-vintage mismatches:** transport Rail "2020 USD" denominator
  vs `GDP[Million 2021 USD]`; resources 1,320 "U.S. Dollar" vintage-less rows;
  residential Variable OM Cost per-energy (canon) vs per-device-year (authored).

---

## Part B — Empty but important (graded)

### 🔴 RED — breaks the calc or actively distorts LP/results in the 4 scenarios now

1. **Road transport has ZERO emission leaves.** *(KNOWN · Transport)* The entire
   `Road` subtree — the bulk of transport energy, 4 vehicle classes × 11 regions
   — carries **no pollutant Loadings** in any scenario, while Air/IW/Rail carry
   full 12–13-species sets. **Mechanism:** all road CO2/CH4/N2O never enters
   emissions results, so every GHG target, externality cost, and net-zero
   measure evaluated on transport sees only Air+IW+Rail — transport emissions
   are structurally under-reported **now**.
2. **Zero-cost open supply/import routes.** *(KNOWN #24 · Resources)* In RAS,
   **191 (fuel,region) pairs have Maximum Production ≠ 0 with Production Cost =
   0** (incl. Nuclear at Unlimited + $0), and **95 pairs have open Maximum
   Imports with Import Cost = 0** (Refinery Feedstocks/Gas, Renewable Diesel,
   Arable/Perennial ×12). **Mechanism:** a cap-open, cost-zero route is a free
   lunch the LP exploits regardless of realism — the exact mechanism behind the
   2026-05-18 biodiesel-to-Timor-Leste and 2026-05-19 POME incidents.
3. **Ammonia RAS Import Cost = `0.001` overriding a real price.** *(KNOWN-adjacent
   · Resources)* CA/Baseline/ATS hold ~$1/kg (`(720+1400)/2*ConvUnits…`); RAS —
   the scenario whose imports the LP optimizes — holds `0.001 ? Placeholder
   cost`. Blast Furnace Gas 0.001 ×12 too. **Mechanism:** if any RAS tech
   consumes ammonia (H2-economy), the solver sources it via near-free imports
   instead of production, silently distorting the RAS energy balance and cost.

### 🟡 YELLOW — placeholder/template values silently shaping results (wrong numbers, not broken mechanics)

**Transport**
- **Scrappage panel is entirely boilerplate** (Scrappage 0, Max/Frac 100 on all
  16 powertrains × 12 regions) — if no survival profile is set elsewhere, fleets
  never retire: old vintages persist to 2060, EV stock share is diluted vs sales
  share, fuel demand biased up / electrification down. *Needs a LEAP UI check.*
- **Fuel Economy is a region-uniform template** (identical MPG in all 11
  countries; the only per-region value is the defective Indonesia Truck NG). New-
  vehicle efficiency genuinely differs by country — silently flattened.
- **SAF Final Energy Intensity evaluates to 0** in every scenario (SAF
  TotalEnergyTran = 0). If Domestic Air uses the per-fuel-intensity method, the
  flagship SAF blend mandate (Indonesia 50 % by 2060) delivers **zero SAF
  demand**; if the category-FEI × Fuel-Share method drives, it's inert. *One
  LEAP UI methodology check settles it — scenario-defining if the first.*
- **SAF CO2 accounted as fossil** (`0.207*71.5`, no biogenic leaf) while
  Biodiesel is 0 fossil / 100 % biogenic — two biofuels, two accounting bases in
  one sector; skews aviation emissions in RAS 2060.

**Residential**
- **Useful_EI = 0 in CA** on all 6 device-stock size classes while non-zero in
  projections → the CA calibration attributes all historical fridge/AC
  electricity to the old trees; switching the new tree on without retiring the
  old is the double-count (A4) — the 2024→2025 electricity step is an artifact.
- **Device Demand Cost = 0 on 5,100 of 5,280 rows**; the only non-zero values
  (Refrigeration_ in Baseline/ATS) are region-uniform 280.45 — two disjoint
  costing systems (Demand Cost vs Capital Cost) for the same appliances; note
  Low_eff priced *above* Mid_eff.
- **248 placeholder-confession intensities** ("585 ? ACE default", "? ACE
  Placeholder when no data", "assumed valuie") driving end-use electricity in
  every scenario, mostly identical across countries.
- **Template-uniform Useful_EI** — 6 ASEAN-wide constants for appliance unit
  energy (climate-driven for AC) → inter-country demand differentiation comes
  only from ownership, not intensity.
- **AC new-tree Percent Ownership = 0 in CA** (uncalibrated addition stacked on
  the still-active old AC tree — same double-count, smaller).

**Resources**
- **Consumer prices ~95 % zero** on the branches demand regressions reference
  (1,130 of 1,188 cells; Bagasse/coals/NG/MSW Industrial price 44/44 zero).
  **Mechanism:** the Exp/Ln price-elasticity shells evaluate `Ln(0)` → undefined
  or garbage, so fuel-switching response is silently priced at zero. (Same class
  hits industry's referenced prices.)
- **Unlimited caps on Natural Gas + all 5 coals (12/12) in every scenario** —
  the fossil canonical authors costs but no caps → un-capped fossil supply (no
  depletion realism) and 1e12 LP-conditioning pollution.
- **Minimum Imports hold-last floors** — 95 RAS rows ending "2022, V>0" extend V
  as a forced import floor to 2060 (Singapore RFO 53,538 kTOE). Standing
  infeasibility/distortion risk as demand evolves.
- **`Unlimited ? tbc` placeholder caps** survive on Biomass/Geothermal/Large
  Hydro/MSW (37 rows) → un-capped renewable supply in the very RAS scenario
  whose RE targets those caps should bind.
- **NEW — Electricity Import Cost = flat `100`** (2020 USD/MWh) in all 12 regions
  × 4 scenarios — the only price for cross-border power trade, a placeholder;
  RAS/CNZ enable the full trade route set, so the build-vs-import decision runs
  on a round template number.
- **NEW — Production Cost = `0.001` template** on the 7 variable renewables +
  Geothermal-class (all scenarios) and the crops/Molasses/MSW (CA/Baseline/ATS
  only — RAS has real injected costs). For crops this means the three
  non-optimized scenarios value feedstock at ~$0 → cross-scenario biofuel cost
  results are not comparable.
- **Arable/Perennial land pseudo-fuels** carry Maximum Imports = Unlimited at
  Import Cost 0 (RAS), and Perennial's cap is mis-tagged "Cubic Meter" vs
  Arable's "Thousand GJ" — free unlimited "land imports" if a trade route is ever
  enabled; the unit drift also breaks the GJ/ha anchor.

**Keys**
- **NEW — every transmission interconnector has Variable OM Cost = 0** (all
  1,008 `Key\Transmission\Lines\*` rows). Zero variable cost to move electricity
  across borders biases the LP toward trade; relevant once RAS/CNZ enable the
  grid.

**Industry**
- **"Fill in historical data here" stubs** — `0 * Key\Macroeconomic\
  Manufacturing Fraction…? Fill in historical data here` (214 rows) — zero-valued
  FEI awaiting data; plus 643 unfitted regression shells (coefficients = 1) and
  528 `?placeholder` CCS sequestration ramps, all live in the 4 scenarios.

### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

- **Transport:** Inland Waterways Kerosene zero pollutants (marginal — only
  Indonesia's tiny declining barge use); Demand Cost / Average Mileage / Final
  On-Road result-vars all constant-0 (dead plumbing); Timor Leste + Base Template
  mileage "ACE default" (TL disabled in calc).
- **Residential:** TotalEnergyRes all-zero series (55 rows — genuinely unused
  fuels, matches published balances); all-zero share partitions (Base Template +
  Timor Leste only).
- **Resources:** all-zero series on *closed* routes (cost 0 paired with cap 0 —
  unreachable today, but a tripwire target: reopening a cap without its cost row
  recreates the RED #2 exploit); "U.S. Dollar" vintage-less units (mostly on
  zero cells).

---

## Highest-leverage fixes (if triaging)

1. Fix the **Truck-NG sales key** (A1) — one-character branch swap kills a
   phantom fleet distorting RAS gas demand.
2. Decide **road transport emissions** (🔴 B1) — the single largest results gap.
3. Sweep the **zero-cost open routes** (🔴 B2) — standing LP-exploit class with a
   documented incident history.
4. De-scramble the **Crude Oil reserves permutation** (A2) and re-author the
   **semicolon/comma-decimal Philippines rows** (A3) — both are committed
   authoring errors with clear correct values.
5. Resolve the **SAF-FEI-evaluates-to-zero** ambiguity (🟡) — a LEAP UI check
   that determines whether the flagship SAF policy does anything at all.

---

## Part C — Transformation anomalies (`Transformation\` tree)

> The **seventh and largest canon export** (`LEAP Input Transformation.xlsx` —
> 1,593 branches, the `Resources → Transformation → Demand` hub, anatomy §14),
> swept over the **same four scenarios** (Current Accounts, Baseline Simulation,
> AMS Target Scenario, Regional Aspiration Scenario) across its three owners —
> **power** (Centralized/Distributed/ETD, 1,100 branches), **fossil**
> (mining/refining/blending, 168 branches) and **bioenergy** (H2/biofuel
> converters, 325 branches). Findings come from the per-owner hunt, then a
> second verifier pass; **where the verifier issued a PARTIAL/REFUTED correction
> the corrected count is used here, not the original**. One scenario fact governs
> the whole grading: among the four scopes **only RAS is NEMO/CPLEX-optimized**
> (Baseline + AMS Target carry `Optimize='No'`, Current Accounts is pure
> accounting), so every "the LP exploits this" mechanism lands in RAS — and RAS
> is a *solved* (`_w_results`) area, so it also carries the solver's own capacity
> decisions stamped back into the authoring layer. Tags mirror Parts A/B: **NEW**
> vs **KNOWN** (already in the anatomy §14 ledger, esp. #33/#34/#35), **VERIFIED**
> vs **SUSPICIOUS — needs human judgment**. Counts are rows in the 4 scenarios.

### Part C · A — Incorrectly inputted (anomalies in authored values)

#### C-A1. Solver output written back into authored input cells (input/output conflation)

- **KNOWN · VERIFIED — power `Optimized New Capacity` holds CPLEX build stamped
  `?Optimized on 07/02/2026 11:41 (NEMO/CPLEX)`.** 379 rows read `0 ?Optimized…`
  and 47 read `Data(2040, 160529) ?Optimized…`. This is a solved area with
  endogenous capacity-expansion written into the authoring layer; re-injecting
  these cells would overwrite solver decisions, and any consumer reading them as
  pure inputs conflates exogenous authoring with endogenous results. (The
  identical 426 also exist in Carbon Neutrality, out of scope; power total across
  both optimization scenarios = 852.) Anatomy §14 §1.1 documents the idiom;
  ledger #8 is the residential analogue. *426 rows, RAS. Power.*
- **KNOWN · VERIFIED — bioenergy `Optimized New Capacity` same writeback**, on all
  24 bio conversion processes × 12 regions (23 carry a non-zero `Data(…)` series,
  e.g. SAF/HVO Renewable Diesel Indonesia = `Data(2030, 11424.48, 2040,
  67293.74, 2050, 198133.2, 2060, 244866.9) ?Optimized…`). Documented in §14 §1.1
  / §14 §4 as the supply-side face of the same artefact. *288 rows, RAS.
  Bioenergy.*
- **KNOWN · VERIFIED (NOT conflated) — fossil writeback lives on the *right*
  variable.** `Optimized New Capacity` carries 247 `?Optimized…` rows (RAS), while
  the 6 Cambodia/Laos Oil Refining `Exogenous Capacity = Data(2024, 0, …, 2060, 0)
  ? IEA Oil Info 2024` rows are *authored* explicit zeros (non-refiners), not
  solver writeback. Input `Exogenous Capacity` is untouched by CPLEX — no
  conflation in fossil. *253 rows (247 + 6), RAS. Fossil.*

#### C-A2. Dangling references / corrupted tokens

- **NEW · SUSPICIOUS — power `ScenarioValue(Bad Scenario [2])` dangling scenario
  reference inside `Endogenous Capacity`.** The intended capacity-additions-ramp
  logic (clean-coal / geothermal / biomass / hydro build) resolves against a
  deleted/renamed scenario, e.g. `Step(2020, 0, 2026, ScenarioValue(Bad Scenario
  [2])*50%)` and `Interp(2020, ScenarioValue(Bad Scenario [2]), 2025,
  ScenarioValue(Bad Scenario [2]) * Key\Capacity Additions Multiplier\Biomass:
  Activity Level[factor], …)`. **AMS Target Scenario only**; regions Philippines
  8 / Vietnam 5 / Thailand 4 / Indonesia 3; techs Coal Ultrasupercritical(+CCS),
  Coal Subcritical_MYPE/_MYSR, Biomass Gasification, Biomass Other_MYPE/_MYSB/
  _MYSR, Large Hydro_MYSB/_MYSR, Geothermal Flash. **RED if LEAP errors on the
  dangling ref (breaks the AMS Target calc); YELLOW if it silently evaluates 0
  (the endogenous build is zeroed)** — graded SUSPICIOUS in Part C · B pending a
  LEAP UI check. Distinct from ledger #2 (a separate 19-row Industry AMS Target
  instance); this 20-row power occurrence is not in the ledger. *20 rows, AMS
  Target. Power.*
- **KNOWN · VERIFIED (clean sweep) — the fossil tree is broken-token clean.** A
  negative-result scan for `!Missing Branch` / `Bad Scenario` / `Bad Unit` /
  `#REF` across expression **and** unit columns returned 0 in fossil (contrast
  the Industry/Commercial hits in Part A · A8). *0 rows. Fossil.*

#### C-A3. Placeholder-comment confessions surviving into live scenarios

- **NEW · VERIFIED — power ASEAN-Power-Grid interconnector `Capital Cost = 315 ?
  Placeholder cost`** on 6 Sarawak/Sabah/Thailand lines (Sarawak_to_Brunei_8a,
  Sarawak_to_Peninsular_3, Sarawak_to_Borneo_6, Thailand_to_Peninsular Malaysia_2,
  Sarawak_to_Sabah_8b, East Sabah_to_Borneo_15) — a confessed guess driving RAS
  interconnector build economics. 42 rows across all 7 optimization scenarios;
  only RAS in scope. *6 rows, RAS. Power.*
- **NEW · VERIFIED — power Wind Offshore `Maximum Availability = 44 ? Placeholder
  from NREL ATB 2023 - average for all wind classes (moderate)`** applied
  uniformly to every region, including those with no offshore-wind resource — a
  placeholder capacity factor shaping Wind Offshore output/economics. *48 rows
  (12 regions × 4 scenarios). Power.*
- **NEW · VERIFIED — bioenergy Cassava and Molasses bioethanol carry no real
  cost.** Both `Capital Cost` and `Variable OM Cost` are authored as a branch-ref
  to Sugarcane's cost tagged `? Placeholder pending data for this process`
  (`Sugarcane:Variable OM Cost[2020 USD/GJ] ? Placeholder pending data…`). By
  scenario: CA 48 / Baseline 48 / AMS Target 48 / RAS 8. Caveat: in RAS the
  placeholder survives only in the two disabled regions (Base Template + Timor
  Leste), and CA/Baseline/AMS are accounting runs — so live LP exposure across
  the four scopes is minimal; a data-hygiene confession regardless. *152 rows.
  Bioenergy.*

#### C-A4. Sibling-variant inconsistency (`_MY*` / twin processes authored differently)

- **KNOWN · SUSPICIOUS — Malaysia `_MYPE`/`_MYSB`/`_MYSR` variants diverge on the
  same (region, scenario, variable).** Wind Onshore: `_MYPE`/`_MYSB` carry the
  bare-MU must-run trap + real Capital Cost, while `_MYSR` carries MU=0 +
  Capital Cost=0 + `Maximum Capacity Addition=Unlimited` (the free-build copy that
  actually got built). Large Hydro: `_MYPE` is the zero-cost / Capacity-Credit-100
  / Efficiency-100 default while `_MYSB`/`_MYSR` carry real cost, availability and
  efficiency. Also Nuclear SFR/SMR and Solar PV `Maximum Capacity Addition`. The
  stated **count 12 is a divergence-span descriptor (12 regions × 4 scenarios for
  the Large Hydro / Wind Onshore variables), not a defect-row tally.** Rooted in
  the §11.1 Malaysia-scoped export view (§14 §1.1). Canon ledger #35. *≈12
  regions × 4 scen. Power.* **AUDITED 2026-07-04:** Indonesia's 51 `_IDJW/_IDSA/
  _IDKA/_IDEast` process nodes (merged from `LEAP Input Transformation
  Indonesia.xlsx`) were anomaly-audited — see **Part D** below. The predicted
  zero-cost / free-build defects DID materialise (Geothermal Flash / Large Hydro
  / Small Hydro Capital Cost=0). This audit also extended the Malaysia set:
  the fully-uncapped + Capital Cost=0 nodes are **4**, not 2 — add **Solar
  PV_MYSR** and **Wind Onshore_MYSR** to Gas Turbine_MYPE + Large Hydro_MYPE.
- **NEW · VERIFIED (latent) — bioenergy HVO Renewable Diesel twin is free under one
  module, costed under the other.** The byte-identical process carries full
  `Capital Cost` under Sustainable Aviation Fuel Production but `Capital Cost=0`
  AND `Variable OM Cost=0` under Renewable Diesel Production in 11 of 12 regions
  (only Indonesia authored) — 44 + 44 rows. HVO RD is capacity-planned and builds
  only from optimization, so $0 capex makes new Renewable Diesel capacity free to
  the LP in real regions (Malaysia/Thailand/Vietnam/Philippines). Latent: the
  RD-module `Optimized New Capacity=0` everywhere in the current RAS solution, so
  not yet exploited, but the cost landscape is distorted. *88 rows. Bioenergy.*

#### C-A5. Cross-region cost-representation inconsistency / outlier

- **NEW · SUSPICIOUS — fossil Oil Refining capital cost authored under two
  incompatible conventions.** 8 regions use `Capital Cost = Mean(2.6, 3.05)*…`
  (coef 2.825); Indonesia `Mean(0.53, 1.62)` (1.075, ~2.6× cheaper) and Malaysia
  `Mean(0.87, 0.96)` (0.915, ~3× cheaper) — the two largest refiners cheapest —
  while Singapore and Thailand author `Capital Cost = 0 ? All costs in Variable OM
  Cost` and instead carry an inflated VOM lead-coefficient (Singapore 18.17,
  Thailand 22.70 vs the 0.425 = `Mean(0.34, 0.51)` baseline, ~43–53×). Each
  convention is self-consistent per region (comment truthful), but any per-region
  total-cost comparison must reconcile both, and the 3×-cheaper Indonesia/Malaysia
  capex needs a human intent check. *16 rows (8 Capital Cost + 8 VOM), all 4
  scenarios. Fossil.*

#### C-A6. Physical-bound violation (efficiency > 100 %)

- **NEW · VERIFIED — fossil Vietnam Oil Refining `Process Efficiency` overshoots
  100 % at 2017** (`Interp(2005, 100.00, …, 2017, 101.91, 2018, 86.73, …) *
  Key\Cal\Transformation\Oil refining:Activity Level[Factor]`) — thermodynamically
  impossible for crude refining, the only fossil Process-Efficiency point in
  (100.5, 300). Low LP impact (historical year × a Cal factor) but a data-quality
  blip. *4 rows (1 expression × 4 scenarios). Fossil.*

#### C-A7. Emission-factor inconsistency

- **NEW · SUSPICIOUS — bioenergy Biomass Gasification with CCS over-credits
  sequestration and books it on a fossil feedstock.** Gross feedstock CO2 is
  zeroed (`0 * …:Process Efficiency/100`) on **both** the Biomass and the (fossil)
  Natural Gas leaves, then a flat `Sequestered Carbon Dioxide = -203882 *
  …:Process Efficiency/100` is booked — **66.2×** the non-CCS twin's gross biomass
  CO2 (3,079.624), and authored unlike the fossil-CCS siblings which keep gross
  and subtract 95 % (SMR-CCS −82467×95 %, Coal-Gas-CCS −151157.9×95 %). Applying
  −203882 to the **fossil Natural Gas** leaf turns fossil gas use into apparent
  net carbon removal — the real red flag; could be intentional BECCS
  net-negative accounting, so human review is needed. *192 rows (96 CO2 + 96
  Sequestered CO2). Bioenergy.*
- **NEW · SUSPICIOUS — bioenergy `Methane = 0` on three crop feedstock leaves that
  carry an authored CO2 factor** (CME Biodiesel\Coconut Oil, Bioethanol\Cassava,
  Bioethanol\Sugarcane) — `Avg Environmental Loading = 0` on `…\Methane` while the
  same-branch Carbon Dioxide is non-zero (e.g. 24.95). These are the only
  `Methane==0` feedstock leaves in bioenergy in scope; plausibly deliberate
  (minor agricultural CH4) but inconsistent across crops. *144 rows (48 each).
  Bioenergy.*

#### C-A8. Sibling-wiring asymmetry (feedstock cost wiring)

- **NEW · SUSPICIOUS — fossil Feedstock `Fuel Cost` wiring differs across the coal
  grades.** Sub Bituminous Coal Production wires `Fuel Cost = Resources\Primary\
  Coal Sub bituminous:Production Cost` in all 12 regions (48 rows); Bituminous /
  Lignite / Unspecified wire it Indonesia-only (4 each), Anthracite none, and Oil
  Refining's Natural Gas feedstock cost is Indonesia-only (4). **Verifier
  correction: the true nonzero count is 64, not the 60 originally stated** (the
  original dropped the 4 Oil Refining Natural Gas rows); 800/864 `Fuel Cost` rows
  are `0`. Likely tracks which grade each country actually produces, but the
  asymmetry reads as inconsistent authoring. *64 rows. Fossil.*

#### C-A9. Separator / style inconsistency (period decimals preserved — NOT §A.15 defects)

- **NEW · VERIFIED (cosmetic) — fossil no-space `Interp()` list style**,
  `Interp(2007,8.5,2008,9.48,…)` deviating from the canon comma-space form.
  Decimals are periods, so **not** a §A.15 decimal violation — cosmetic. **Verifier
  correction to scope label:** the 7 Brunei rows are under `Transformation\Gas
  Processing\Processes\Natural Gas` (4 Exogenous Capacity + 3 Historical
  Production), *not* the "Natural Gas Production" group the finding named; the
  other 32 are Indonesia Oil Refining Output Share. Count 39 is correct. *39 rows.
  Fossil.*
- **NEW · VERIFIED (clean) — fossil semicolons are all in the `?`-comment tail.**
  The 18 fossil expressions containing `;` (all Oil Refining Exogenous Capacity)
  place every semicolon *after* the `?` comment marker as a citation separator; a
  parenthesis-depth scan found 0 inside any Interp/Data argument list — no §A.15
  separator violation. *18 rows (clean). Fossil.* (The bioenergy tree is likewise
  clean: 88 bio rows with `;` all sit in the trailing `?` citation comment, 0
  inside an Interp arg list.)

#### C-A10. Zero-cost open feedstock route (POME-lesson shape)

- **NEW · VERIFIED (cross-tree; low LP impact now) — bioenergy Corn Ethanol
  feedstock is free AND unlimited in 3 of 4 scenarios.** `Resources\Primary\Corn:
  Production Cost = 0` and `Maximum Production = Unlimited` in Current Accounts,
  Baseline and AMS Target (12 regions each) — Corn is the **only** bioethanol crop
  left at literal 0, while Cassava/Coconut Oil/Molasses/Palm Oil/Sugarcane all
  carry the guard `0.001 ? Very small cost to avoid arbitrary production in
  optimization`. RAS fixes it (real Interp cost + capped Maximum Production).
  Because the three free+unlimited scenarios are accounting runs (no LP) and RAS
  is repaired, live exploitation is minimal — but it is the same POME-lesson class
  as ledger #24 (Corn/guard-omission not separately named there). *72 rows (36
  Production Cost=0 + 36 Maximum Production=Unlimited across CA/Baseline/AMS ×12).
  Bioenergy/Resources.*

#### C-A11. `_x000D_` carriage-return artifacts inside live code (cosmetic)

- **KNOWN · VERIFIED — power `_x000D_` CR artifacts** in the post-`?` provenance
  comment portions of cost/efficiency expressions (Capital Cost 708, CCS VOM 576,
  CCS Capital 576, Fixed OM 328, CCS FOM 288, Variable OM 280, Process Efficiency
  108, Maximum Availability 77, plus ~53 others). Cosmetic — in the comment, does
  not corrupt the numeric expression. Full-roster power total = 8,302. Ledger #14
  / quirk #27. *2,994 rows. Power.*
- **NEW · VERIFIED (load-bearing placement) — fossil `_x000D_` mid-formula.** On
  the 48 Gasoline Distribution and Handling `Avg Environmental Loading`
  evaporative-loss rows the `_x000D_` sits **inside** the load-bearing TVP formula
  (char 44, before the first `?` at char 105: `…668/0.739/1000_x000D_\n+ ((9*
  Gasoline:TVP…`); the other 8 (Myanmar NG T&D + Thailand NG Production Losses)
  are in the comment tail. Likely an export-digest artifact but should be
  confirmed benign in the live area given the placement. *56 rows. Fossil.*
- **NEW · VERIFIED (cosmetic) — bioenergy `_x000D_` in `Process Efficiency`**
  (Anaerobic Digestion + FAME Biodiesel). A hygiene defect the original bio hunt
  **missed**; ledger #14 records `_x000D_` only for Commercial/Residential/
  Transport, not Transformation. 143 rows across all scenarios, 52 in the 4-scope.
  *52 rows (143 all-scenario). Bioenergy.*

---

### Part C · B — Empty but important (graded)

#### 🔴 RED — actively distorts the RAS LP / results now

1. **Free, unlimited firm capacity on six Malaysia `_MY*` generators.** *(KNOWN
   #35, sharpened · VERIFIED · Power)* `Capital Cost = 0` **and** `Fixed OM Cost =
   0` **and** `Variable OM Cost = 0` on Gas Turbine_MYPE, Large Hydro_MYPE, Solar
   PV_MYPE/_MYSB/_MYSR and Wind Onshore_MYSR (LEAP default-inheritance on
   un-authored `_MY*` copies): 288/288 CapCost=0, 288/288 FOM=0, 284/288 VOM=0.
   Combined with `Capacity Credit = 100` (276 rows) and `Maximum Capacity Addition
   = Unlimited` (70 rows, Part C · A) the generator is **free to build, free to
   keep, free to run, credited fully firm, and uncapped**. **Mechanism, directly
   verified in the solve:** RAS `Optimized New Capacity` built **160,529 MW of Gas
   Turbine_MYPE (Malaysia, 2040)** — against Malaysia's ~20 GW peak demand — plus
   19,163 MW of Wind Onshore_MYSR, at zero investment/O&M cost, collapsing
   Malaysia's optimal capacity mix and system cost. *(Correction to the original
   framing: this is the largest genuine **generator** build, not the largest build
   overall — the ETD pass-through `Electricity` node carries larger `Optimized New
   Capacity`: Indonesia 507,671, Vietnam 227,642, Malaysia 169,110 MW.)* Ledger #35
   logged CapCost=0/Cap-Credit-100 as a benign export-view artefact; the
   solver-build evidence sharpens it to a live RED exploit. *288 rows (+70 Max Cap
   Addition, +276 Cap Credit), RAS. Power.*
2. **Blending pseudo-techs carry `Exogenous Capacity = Unlimited` (units
   Megawatt).** *(KNOWN #34 · VERIFIED · Fossil)* On all four biofuel-mandate
   blenders — `Diesel Blending\Processes\{Biodiesel, Diesel}` and `Gasoline
   Blending\Processes\{Ethanol, Gasoline}`. `Exogenous Capacity` maps to NEMO
   `ResidualCapacity`, and LEAP→NEMO export turns the literal `Unlimited` into a
   **1.0e+12 forced FLOOR** (§A.11 lower-bound landmine, the 2026-05-12 p9 shape) —
   1e12 MW of forced residual blending capacity enters the LP basis as a hard
   floor and breaches CPLEX's ~1e9 conditioning tolerance even when non-binding;
   also a nonsensical MW capacity on a fuel-passthrough blender. Lands in RAS (the
   only optimized scope). **Faithful caveat:** canon ledger #34 **and** project
   memory (`project_aeo9_v042_RAS_resolved`) both record this exact shape was
   judged a **red herring** in the 2026-05-12 aeo9_v0.42 probe and never
   remediated — i.e. empirically it did not break that solve, so "breaks the calc
   now" is the in-principle §A.11 mechanism, not an observed break. It survives
   unchanged in aeo9_v0.67. *192 rows (4 procs × 12 regions × 4 scen; 48 in RAS).
   Fossil.*

- **SUSPICIOUS (RED-or-YELLOW) — AMS Target `ScenarioValue(Bad Scenario [2])`
  dangling ref** (20 rows, Part C · A2). RED if LEAP errors on the dangling
  scenario, YELLOW if it silently evaluates 0 and merely zeroes the intended
  endogenous build. One LEAP UI check settles it.

#### 🟡 YELLOW — placeholder/template/default values silently shaping results

- **§11.2c must-run trap authored but VERIFIED INERT (downgraded from RED).**
  *(KNOWN #33 · Power)* 28 RAS rows author the bare `Minimum Utilization =
  Maximum Availability` must-run hazard on variable renewables — 22 Wind
  Onshore_MYPE/_MYSB across the 11 non-Malaysia regions + 6 Base Template (Solar
  CSP / Solar Floating / Tidal / Wave / Wind Offshore + Distributed Solar PV
  Rooftop). **Caveat / why not RED:** every trap branch has `Optimized New
  Capacity = 0`, and effective capacity is 0 (the 22 Wind Onshore inheritance
  copies read `Exogenous Capacity=0` / Node=0; the 6 Base Template techs carry an
  `Existing Capacity + Capacity Additions` formula that evaluates to 0 in a
  non-calculated placeholder region) — so the constraint **binds nothing and
  cannot infeasible the solve today**. It is an authored hazard that *would* bite
  if any of those `_MY*` branches ever receive capacity. Absent in CA/Baseline/AMS
  Target. Reconciles canon #33's RAS 27 (+1 Distributed Solar PV Rooftop). *28
  rows, RAS. Power.*
- **Capacity Credit = 100 on the same `_MY*` default copies** — 276 of 288 rows
  (the other 12 = Solar PV_MY* at `18.8737644659 ? AEO7`). Intermittent Solar/Wind
  crediting as fully firm against the Planning Reserve Margin; compounds RED #1.
  Contrast correctly-authored VRE credits (Wind Offshore 20, Solar Floating 18.61).
  Ledger #35. *276 rows. Power.*
- **Process Efficiency = 100 on Gas Turbine_MYPE** — the only combustion `_MY*`
  tech left lossless (base Gas Turbine = `Interp(2021, 33, 2030, 36, 2040, 39)`,
  Gas Combined Cycle_MY* ≈ 42–60 %, Diesel_MY* ≈ 45–47 %). At 100 % the 160 GW
  free build burns ~⅓ the gas a real 33–39 % turbine would, understating its only
  genuine cost (fuel) ~3× and understating power-sector gas demand + CO2 in RAS.
  Not in the ledger. *48 rows. Power.*
- **Electricity T&D Losses = 0 on Indonesia and Singapore** — lossless
  transmission on the single largest ASEAN grid; understates the generation and
  installed capacity needed to serve demand in every scenario. Contrast Vietnam
  ≈11 %, Myanmar ≈27 %. 16 rows across Indonesia/Singapore/Base Template/Timor
  Leste; **8 are load-bearing** (Indonesia + Singapore × 4 scen; Base Template +
  TL are non-calculated). Quirk #14. *16 rows (8 load-bearing). Power.*
- **Maximum Production = Unlimited on all fossil processes in RAS** — the benign
  §A.11 **upper-bound** 1e12 sentinel un-caps every fossil supply/conversion route
  and degrades CPLEX conditioning (not a forced floor). Ties to Resources ledger
  #24: fossil supply *cost* is authored on the Resources tree, so an un-capped
  Transformation route is bounded only by whatever Resources caps + costs exist.
  §14 §1.3 / ledger #34. *252 rows (21 proc nodes × 12 regions), RAS. Fossil.*
- **SUSPICIOUS — Fixed OM Cost = 0 on the only two capacity-planned fossil plants**
  (Oil Refining\All Refineries, Gas Processing\Natural Gas) in every region and
  scenario, though these are the archetype that canon says carries the full
  capacity-planning panel. Combined with RAS `Maximum Capacity=Unlimited` (Part C ·
  A1/INC-1) the RAS optimizer prices new refinery/gas-processing capacity on
  capital + VOM only, understating the fixed carrying cost of domestic conversion
  vs imports. Not explicitly flagged as always-zero in canon. *96 rows. Fossil.*
- **SUSPICIOUS — coal-mine Methane EF = plain uncommented `0` on Sub Bituminous
  Coal Production** across all 12 regions × 4 scenarios, while the four sibling
  grades carry the real `12.06 ?a) … IPCC (2006) … Tier 1` where produced or a
  *commented* `0 ? No indigenous production…` where not. Sub-bituminous is the
  actively-produced grade region-wide (it alone wires Fuel Cost→Resources in all
  12 regions; Indonesia's dominant thermal coal). The plain zero reads as a
  forgotten leaf and understates coal-mine CH4 (high-GWP) — chiefly for genuine
  producers. Methane is the only GHG species on coal-mine branches (no CO2 leaf).
  Not specifically in canon. *48 rows. Fossil.*
- **Annual Avg Ambient Temp = `15 ? Fill in country-specific value`** — a
  template-uniform placeholder across all 12 regions including equatorial ASEAN
  (~27–28 °C), driving the Gasoline Distribution TVP evaporative-loss model. A
  15 °C value well below tropical ambient understates TVP and hence the
  gasoline-handling evaporative-loss emission factor for every AMS. §14 §1.3
  (verbatim). *48 rows. Fossil.*
- **Variable OM Cost = 0 on the 6 capacity-planned Hydrogen plants** (SMR / SMR
  with CCS, Coal Gasification ±CCS, Biomass Gasification ±CCS) — these carry
  Capital + feedstock cost but zero per-unit operating cost, understating marginal
  H2 cost and biasing dispatch/build toward them vs PEM Electrolysis (which pays
  for electricity). **Mechanism is LIVE, not latent:** in RAS SMR builds in 4
  regions and Biomass Gasification in 2 (PEM in 3), so the zero VOM understates an
  exercised route. *288 rows. Bioenergy.*
- **Fixed OM Cost = 0 across all 9 liquid-biofuel plants** (CME/FAME/POME
  Biodiesel, Cassava/Corn/Molasses/Sugarcane Ethanol, HVO Renewable Diesel + HVO
  SAF) in every region and scenario — systematically understates annual carrying
  cost, making biofuels look cheaper to keep operating than reality. HVO
  contributes 96 (RD 48 + SAF 48). *432 rows. Bioenergy.*
- **Biofuel feedstock effectively free** — 1,337 of 1,824 in-scope feedstock
  `Fuel Cost` rows = 0 (cost deferred to Resources), and the Resources crops they
  defer to carry only `0.001 ? Very small cost…` (Palm Oil/Coconut Oil/Cassava/
  Molasses/Sugarcane) with Corn at literal 0 — the exact POME-lesson exposure
  (every supply cap needs a real companion cost). All-scenario figure 3,715/5,016
  matches §14 §1.4. Caveat: in RAS the deferred Resources cost is real (Interp)
  for the 10 real regions, so the near-free values dominate the accounting
  scenarios rather than RAS. Ledger #24. *1,337 rows. Bioenergy.*
- **Lite-panel conversion is free AND uncapped** — Charcoal (All Biomass),
  Domestic Biogas (Anaerobic Digestion), Methanol (CO2 Utilization for Iron and
  Steel + Production from Hydrogen) and Ammonia (Hydrogen) have **no** Capital Cost
  variable, VOM = 0 or absent, and Maximum Production = Unlimited — the only brake
  is feedstock cost/supply, so the LP can convert at zero process cost and distort
  the merit order. (Correctly excludes the two Biomethane AD variants, which carry
  non-zero VOM.) *5 processes. Bioenergy.*

#### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

- **Power Maximum Production = Unlimited on 63 processes (756 rows, RAS)** — the
  benign upper-bound sentinel only. **Critical cross-check confirmed: `Exogenous
  Capacity` containing `Unlimited` = 0 rows in the entire power domain** — the
  catastrophic §A.11 lower-bound forced-floor flavour (ledger #34's fossil-blending
  shape) is **ABSENT in power**; only LP-conditioning noise + an appropriate
  pass-through Unlimited on ETD Electricity remain. Ledger #34 / §1.1. *756 rows,
  RAS. Power.*
- **Power Renewable Target = 0** — the module-level RE-target knob is inert; RE
  ambition is enforced via blend mandates, per-tech Minimum Share of Production and
  the `__NEMOcc` RenewableCapacityTarget constraints. Within the 4-scope only RAS
  actually materializes the variable. §1.2. *24 rows, RAS. Power.*
- **Fossil Variable OM Cost = 0 + Maximum Production = Unlimited on all extraction /
  T&D / own-use processes** (5 coal All Mines, Crude Oil, NG Production, LNG Regas,
  NG T&D, Gasoline Distribution, 5 ESO) — **intentional by design** (§14 §1.3:
  fossil supply cost lives on Resources; the Transformation node is a zero-cost
  passthrough). Benign in isolation but the whole fossil price signal is
  load-bearing on Resources being correctly authored — directly coupled to
  Resources ledger #24. 720 of 816 VOM rows are 0; only the two full plants carry
  non-zero VOM. *720 rows. Fossil.*
- **Fossil module-level grid/market knobs uniformly zero** — Module Costs 624,
  Output Price 1,344 (1,340 zero + 4 `Remainder(100)`), Import Target 1,080, Export
  Target 1,080, Renewable Qualified 72 (RAS). **Verifier correction: the aggregate
  is 4,200 rows (4,196 zero), not the 3,600 originally stated** — an
  empty-by-design inventory so a future author does not mistake the empty panels
  for missing data (trade + RE ambition are enforced elsewhere). *4,200 rows
  (4,196 zero). Fossil.*
- **Bioenergy template-uniform FAME Biodiesel Capital Cost** — one identical
  `Interp(2025, 3.2422, … 2060, 2.2807)` across all 10 real AMS (Base Template &
  Timor Leste = 0); plausibly an intentional single assumption, but the export
  carries no regional capex signal for these plants. *10 regions. Bioenergy.*
- **Bioenergy zeroed accounting block** — Salvage Value, Stranded Cost, Module
  Costs and Output Price are literal 0 on 100 % of bio rows (816 + 816 + 384 +
  384). Cosmetic for a levelised-cost read; removes salvage/stranded terms from any
  total-system-cost or asset-stranding analysis. *2,400 rows. Bioenergy.*
- **`_x000D_` CR artifacts (all three owners)** — cosmetic where they sit in the
  post-`?` comment (Part C · A11); the one placement worth a live-area confirm is
  the 48 fossil Gasoline Distribution rows where the token is mid-formula.
- **Clean sweeps** — the fossil tree carries **0** broken tokens, **0** bare-MU
  §11.2c traps (all 288 fossil MU = 0, MaxAvail all 100), **0** Maximum
  Availability > 100, and 480/480 non-zero combustion CO2 EF leaves; the bioenergy
  tree carries **0** `Exogenous Capacity=Unlimited` and **0** bare-MU traps — so no
  RED §A.11/§11.2c finding was fabricated for either domain.

---

### Highest-leverage fixes for Transformation

1. **Author real cost + build caps on the six Malaysia `_MY*` generators**
   (🔴 C-B1) — the LP demonstrably built 160.5 GW of free Gas Turbine_MYPE against
   Malaysia's ~20 GW peak; fixing Capital/Fixed/Variable OM + `Maximum Capacity
   Addition` on Gas Turbine_MYPE, Large Hydro_MYPE, Solar PV_MY*, Wind Onshore_MYSR
   is the single biggest RAS distortion.
2. **Replace the 4 blending pseudo-techs' `Exogenous Capacity=Unlimited` (MW) with
   a finite value** (🔴 C-B2) — per §A.11 use finite-but-large, **never 0** (the
   failed 2026-05-12 p9). Historically judged a red herring, but it pollutes CPLEX
   conditioning and is the textbook lower-bound landmine.
3. **Settle the AMS Target `ScenarioValue(Bad Scenario [2])` dangling ref** (20
   rows) — one LEAP UI check decides RED (calc error) vs YELLOW (endogenous build
   silently zeroed).
4. **Fix the Biomass Gasification with CCS `-203882` sequestration on the fossil
   Natural Gas leaf** — as authored it turns fossil gas use into apparent carbon
   removal (66× the non-CCS biomass gross).
5. **Correct the Vietnam Oil Refining 101.91 % efficiency point** and re-author the
   two full-plant `Maximum Capacity=Unlimited` + `Fixed OM=0` rows (fossil INC-1 +
   EBI-3) — committed authoring errors with clear intended forms.

---

## Part D — Indonesia sub-national node audit (`_IDJW/_IDSA/_IDKA/_IDEast`)

> Added 2026-07-04 after the Indonesia transmission detail was merged into canon
> (51 `_ID*` process nodes across 13 families; see anatomy §1.1). Method:
> mechanical detection over the Indonesia node panel (4 canonical scenarios) →
> 6-class adversarial-verification workflow (13 agents) → source reconciliation.
> One workflow verdict ("Maximum Production=Unlimited is a phantom") was **wrong**
> — it read an incomplete pivot; the variable IS present (357 panel rows,
> confirmed against source). Corrected below. Scope: Indonesia `_ID*` power nodes
> (Malaysia items surfaced incidentally are flagged *[MY, out of scope]*).

### D1. Confirmed DEFECTS (ranked)

- **🔴 VERIFIED DEFECT · HIGH — Capital Cost = 0 on Geothermal Flash / Large
  Hydro / Small Hydro `_ID*` (12 nodes × 4 scen = 48 cells).** Capital-intensive
  firm renewables authored with `Capital Cost="0"` (explicit literal, all
  scenarios) → the LP builds new capacity **free** up to the finite
  `Maximum Capacity` headroom, crowding out priced options and understating
  system cost. **Isolated to exactly these 3 families** — every other `_ID*`
  family carries a real Danish-Energy `Interp(...)` capex (Solar PV
  `Interp(2022,960,…)`, Coal `Interp(2022,1880,…)`, Gas CC `Interp(2022,1080,…)`),
  which rules out an area-wide zero-cost convention and confirms an
  inheritance-copy/authoring gap. Headroom is real (Large Hydro RAS
  `Maximum Capacity` = 32980 / 4820+ExoCap / 21600 / 15600 MW; Small Hydro 2500 /
  3050 / 8100 / 5730). **Exception:** `Geothermal Flash_IDKA` has
  `Maximum Capacity = Exogenous Capacity[MW]` (no headroom) → inert, no free
  build. **Fix:** author real regional Capital Cost on all 12 nodes (mirror
  Malaysia `_MYSB` `Interp(2020,1500…)` or the Indonesia Technology
  Roadmap/Danish Energy 2024 capex). If an exogenous-only fleet is intended,
  set `Maximum Capacity Addition = 0` so the LP cannot free-build above the
  existing fleet.
- **🟡 VERIFIED DEFECT · MEDIUM — `Maximum Capacity Addition = "Unlimited"` on
  Large Hydro + Small Hydro `_ID*` (8 nodes, RAS).** The only genuine
  `Unlimited` in the Indonesia canon. `→ 1e12` per-year addition sentinel
  (§A.11 upper-bound); total build is still bounded by the finite
  `Maximum Capacity`, so this is mainly (a) the compounding half of the
  Capital-Cost=0 free-build (all headroom can arrive in year 1 at zero cost)
  and (b) CPLEX conditioning noise — **not** an independent unbounded-build
  hole. **Fix:** replace with a finite lead-time-gated ramp (port Malaysia
  `_MYSB` `Interp(BaseYear,0,2023,…,Key\Modeling Assumptions\Large Hydro Lead
  Time:Activity Level,…)`) or a generous finite numeric; do in the same pass as
  the capex fix.

### D2. Checked and CLEARED — intended / false-positive (do NOT re-flag)

- **`Maximum Production = "Unlimited"` (51 nodes) — INTENDED, benign §A.11
  idiom, low.** Real (357 panel rows; the workflow's "phantom" verdict was a
  pivot artifact and is rejected). Removes only the activity cap; the binding
  constraint is `Maximum Capacity × Availability`, which is finite. 1e12 adds
  conditioning noise only. Optional hygiene: swap for a generous finite numeric.
- **`Variable OM Cost = 0` (60 flags: Geothermal / Large Hydro / Small Hydro /
  Solar PV) — FALSE POSITIVE.** Physically correct for zero-fuel renewables;
  VOM feeds per-MWh dispatch cost, not the build. Every one of the 60 lands on a
  non-fuel tech; every fuel-burner (Coal, Gas, Diesel, Biomass, Biogas) carries a
  real non-zero VOM. Detector should exempt non-fuel families.
- **`Capacity Credit = 100` on Small Hydro `_ID*` (16) — FALSE POSITIVE for the
  derate tripwire.** These nodes author `Maximum Availability = 100` flat (not a
  YearlyShape), so CC=100 is internally consistent with a firm treatment — not
  the "derate a variable renewable" defect. (The genuinely-variable Solar PV
  `18.61` and Wind `20` are correctly derated.) Caveat: flat-100 availability +
  Capital Cost=0 reads as an un-authored placeholder — already captured by the
  D1 capex defect; decide run-of-river-vs-reservoir when authoring real data.
- **§11.2c must-run trap — ABSENT (clean).** All variable renewables
  (Solar PV / Wind Onshore / Small Hydro `_ID*`) author `Minimum Utilization = 0`
  (fully curtailable). Incumbent thermals correctly use the sanctioned
  `Min(…, Maximum Availability)` phaseout wrapper. `MU > AF` count = 0.
- **Unmet Load `_ID*` — INTENDED, correct slack (§11.4c).** Priced
  (`Capital Cost=100000`, `Variable OM Cost=500`), unbounded supply as intended →
  unserved energy resolves as expensive slack, not INFEASIBLE.

### D3. Canon-hygiene notes

- **Biogas has only 3 nodes** (`_IDJW/_IDKA/_IDSA`, no `_IDEast`) — every other
  family has all 4. Confirm with the Indonesia team: resource-driven omission
  (biogas feedstock concentrated in western Indonesia) or an authoring gap.
- **The Indonesia export carries a non-canonical scenario roster** — 11
  scenarios including scratch/duplicate ones (`LCO backup`, `Regional Aspiration
  Scenario test`, `Set up`, `Carbon Neutrality_ Net Zero Scenario`, 3×
  `RE LTRM ASEAN …`) alongside the canonical 4. Confirmed against the source
  panel. The Indonesia area state differs from the 11-scenario canon roster
  (IDs 1–30) — reconcile before treating Indonesia expression VALUES as canon.

### D4. Malaysia items surfaced incidentally *[MY, out of scope — confirm before touching]*

- **Extends ledger #35:** the fully-uncapped (`Maximum Production` +
  `Maximum Capacity` + `Maximum Capacity Addition` all `Unlimited`) **+ Capital
  Cost=0** set is **4 nodes**, not 2 — **Gas Turbine_MYPE, Large Hydro_MYPE,
  Solar PV_MYSR, Wind Onshore_MYSR** (the latter two match the trap catalogue's
  named `_MY*` zero-cost list). These are the real free-unbounded-build risks on
  the Malaysia side. The other 29 `_MY*` `Maximum Production=Unlimited` nodes are
  low-severity (finite `Maximum Capacity` backstop → conditioning only).

## Part E — 2026-07-06 addendum: v0.68 update file (`mailbox/20260607/`) + canon designations

Source: `LEAP Input Transformation (Updated Expression Only).xlsx`
(`aeo9_v0.68_w_annual_results`, 52 rows) — an independent modeller update,
to be re-reviewed against the power team update. Verified findings:

- **Singapore CA `Existing Capacity` refresh (40 rows, base branches).**
  3 confirmed corrections vs canon (Fuel Oil / Gas Turbine / Waste — the
  2023–24 zeros replaced with real fleet values: 763.6→13.60 / 180→260 /
  393→345.20 MW); 25 rows byte-identical; 12 rows on base branches canon
  had never captured (region-scoped-export blind spot — now restored to the
  tree, anatomy §11.1-caveat CORRECTION 2026-07-06). Folded into
  `inject/power/structure_handover_20260703/current_expressions_transformation_slice_4scenarios.csv`.
- **12 `Set up` rows — technology-specific MY/ID edits, zero Singapore.**
  Gas Turbine + Gas Turbine_MYPE `Maximum Capacity = Exogenous Capacity[MW]`
  (bounds the ledger #35 Gas Turbine_MYPE free-build headroom — Capital
  Cost=0 itself still open); Geothermal ORC + Flash_IDJW/_IDSA/_IDKA/_IDEast
  `Maximum Capacity = ExoCap + 0.9×proven potential` (bounds Part D
  free-build direction); Solar PV_MYPE/_MYSB `Capacity Additions`
  trajectories (+ _MYSR = 0); Coal Supercritical co-firing
  `Feedstock Fuel Share = Interp(2060, 10) ? Placeholder` on Biomass +
  Ammonia (Indonesia).
- **CANON DESIGNATION (user, 2026-07-06): these Set-up authorings belong in
  RAS.** The 10% co-firing share is to be universally adopted **in RAS, not
  Set up**. In v0.68 they sit in `Set up` — at the power-team review,
  verify the move to RAS happened (or route it as an inject). Do NOT record
  them in the 4-scenario current-state extracts until they are actually
  authored in RAS.
- **RAS-move VERIFIED for Indonesia (2026-07-06, v0.69 Indonesia slice):**
  the geothermal caps (×0.9 derating; ORC `1000000` → `ExoCap + 0.1*3170`)
  and the 10% co-firing placeholder are authored in **Set up + RAS + CNZ**
  in v0.69. The placeholder REPLACED the detailed RAS co-firing
  trajectories (Ammonia formerly ramped to 43.94% by 2060; Biomass ramped
  from 2029) on Coal Supercritical ± CCS and all four Coal Subcritical_ID*
  nodes — the detailed curves survive only in AMS Target. All 16 RAS
  changes folded into the canon current-state extracts (per-country
  harvest, user go-ahead). Malaysia-side rows (GT MaxCap, Solar PV_MY*
  CapAdd) pending the Malaysia slice.
- **RAS-move VERIFIED for Malaysia too (2026-07-06, v0.69 Malaysia
  slice), + 5 extra RAS edits beyond the v0.68 list**: Gas Turbine base
  `1000000`→`ExoCap`, Gas Engine/Gas Steam base `0`→`ExoCap`,
  Gas Turbine_MYPE + Large Hydro_MYPE `Unlimited`→`ExoCap` (a §A.11
  upper-bound sentinel retired), Solar PV_MYPE/_MYSB MaxCap headroom
  `+1965*1000*80%` demoted to a comment. All 9 folded into the power
  slice extract (2 required ALL-row repartition — Malaysia diverges).
  **Ledger #35 / Part C free-build status: Gas Turbine_MYPE and
  Large Hydro_MYPE CLOSED (MaxCap ceiling binds); Solar PV_MYSR and
  Wind Onshore_MYSR STILL OPEN** (MaxCap + MaxCapAddition `Unlimited`,
  Capital Cost 0).
- **Full v0.69 harvest complete (2026-07-06) minus Timor Leste**: the 8
  copper-plate slices (BN/KH/LA/MM/PH/SG/TH/VN) each diffed ZERO authored
  edits vs v0.67; MY 9 + ID 16 as above. Complete v0.69-vs-v0.67 authored
  delta = the 52-row v0.68 file + the 25 MY/ID RAS rows.
- **Open item:** untracked `inject/power/20260608/patched_targets.csv`
  carries 47 region-lock hits, all `_ID*`/`_MY*` rows in **Base Template**
  (template-broadcast semantics vs §A.21 — decide at the power-team review).
- **PENDING (user, 2026-07-07 — no agenda to author now):** three items the
  power team promised but did not include in `power_sendback_20260706.zip`:
  (1) Electricity Import Cost per region/scenario (the flat-100 placeholder
  stands), (2) the Wind Offshore availability placeholder fix, (3) the
  in-module transmission capital cost. Carry to the next power cycle.
- **RESOLVED (user, 2026-07-07):** `Solar PV_MYSR` Maximum Capacity set to
  20,000 MW (20 GW) in the cleaned sendback — supersedes the team's 0,
  which conflicted with their own 200 MW/yr addition limit. With the
  team's real costs + finite addition limit + this cap, the last two
  free-build REDs (Solar PV_MYSR, Wind Onshore_MYSR) close on inject.
- **Anomaly pass on the inject payload + live-model histories
  (2026-07-07, every Interp series evaluated year-by-year).** Real-world
  booms (Vietnam solar 2018–21, Indonesia coal ramps) check out.
  SUSPICIOUS — for the power team:
    1. **Thailand Large Hydro: +4,451 MW in 2019, −4,450 MW in 2023** —
       symmetric appear/disappear, classic bookkeeping-error signature.
    2. **Thailand fleets vanishing to 0 mid-history**: Biomass Other
       −2,120 MW (2020), Pumped Hydro −1,000 MW (2023 — Lam Ta Khong
       still operates in reality), Waste −658 MW (2023).
    3. **Myanmar Gas Engine −822 MW → 0 (2020)**; `Biomass Other_MYPE`
       852→32 MW (2010); `Biomass Other_IDSA` 1→1,531 MW (2018) — step
       artifacts worth a source check.
    4. **Identical retirement series copy-pasted across sibling nodes**:
       all four `Gas Turbine_ID*` retire the same absolute series
       (601→62 MW each — national total ×4?); `Coal Subcritical_MYPE` ≡
       `_MYSR` (both 210→1,474 MW at 2030). If national totals were
       duplicated per node instead of split, retirements double/quadruple
       count.
    5. **Result-spike mystery solved**: Vietnam's "14.8 GW storage in
       2025" result = exactly the authored additions (LIB 10,460 +
       Pumped Hydro 4,370 MW, PDP8 policy-year build) — input-driven,
       not solver free-build.
    6. **Wind Onshore_MY* locked at zero build in RAS** (team's Maximum
       Capacity Addition = 0 on all 3 nodes + fleet 0): no Malaysian
       onshore wind can ever be built. Plausibly intended (poor
       resource) — confirm with the team.
    7. **Capacity Credit = 100 is NOT reshipped** (sendback carries no
       Capacity Credit rows) — the T1/CF-01 capacity-credit component
       stays open.
