# Canon anomaly audit — `aeo9_v0.67_w_results`

> Full-corpus anomaly sweep over all six canon exports, scoped to the four
> scenarios that matter (**Current Accounts, Baseline Simulation, AMS Target
> Scenario, Regional Aspiration Scenario**). Generated 2026-07-04 by running
> systematic detectors over the flat digests (offline; no LEAP COM). Two
> parts, as requested: **(a) incorrectly inputted** — anomalies in what is
> authored; **(b) empty but important** — missing/placeholder values, graded
> 🔴 red / 🟡 yellow / 🟢 green. Every item flags **NEW** vs **KNOWN** (already
> in the anatomy §14 hygiene ledger) and **VERIFIED DEFECT** vs
> **SUSPICIOUS — needs human judgment**. Counts are rows in the 4 scenarios.
>
> Methodology note: transport / residential / resources came from the
> multi-agent hunt (self-verified, ledger-cross-checked); keys / commercial /
> industry were detected directly in this session after the agent run hit
> model limits. Where an item says "needs a LEAP UI check" it cannot be
> settled from the export alone.

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
