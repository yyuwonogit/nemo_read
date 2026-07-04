# Anomaly audit — your slice (Fossil supply fuels & reserves)

This is the **fossil-team slice of the full canon anomaly audit** run on
2026-07-04 over the live model (LEAP area `aeo9_v0.67_w_results`, four
scenarios: **Current Accounts, Baseline Simulation, AMS Target Scenario,
Regional Aspiration Scenario**). The master audit is a cross-sector list
of authoring defects; below are only the items that land on **branches
your team owns or authors** — the fossil supply fuels and reserves:
the 5 coals, Crude Oil, Natural Gas, Natural Gas Liquids, Nuclear, and
the refined/secondary petroleum products (Diesel, Gasoline, Kerosene,
Jet Kerosene, LPG, Residual Fuel Oil, Naphtha, Bitumen, Avgas, Ammonia,
etc.). Each item keeps the master audit's verbatim finding, its counts,
its **NEW/KNOWN** and **VERIFIED/SUSPICIOUS** tags, and (for Part B) its
🔴/🟡/🟢 grade — **nothing here is invented, re-counted, or re-tagged**.
Part A is authored-value anomalies (incorrect inputs); Part B is
empty-but-important gaps. These are **review requests, not fixes** —
your team is the one who can judge which are deliberate and supply the
correct national data. Where a defect actually lives in a branch your
sector merely *references* (owned by another team upstream), it carries
a **Cross-tree note** so you know it is not yours to author.

---

## Part A — Incorrectly inputted (anomalies in authored values)

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
- **KNOWN + NEW extent — comma-decimal arithmetic beyond the ledger.** Ledger
  #26 recorded 9 Philippines Natural Gas rows (`…*1,0551`). The class actually
  spans **8 more Philippine fuels** — Avgas `…/(159*44,8000*0,7300)`, Bitumen,
  Charcoal `…/28,8800`, Jet Kerosene, Kerosene, LPG, Naphtha, Residual Fuel
  Oil — comma-decimals inside parenthesised multiplication where they cannot be
  list separators. *58 rows total in scope, all Philippines. Resources.*
  Bonus suspicion: even de-comma'd, the NG `*1.0551` looks **inverted** (GJ↔MMBTU
  conversion should divide) — needs a human math check.
  - **Cross-tree note:** of the 8 secondary fuels above, **Charcoal** is a
    bioenergy-owned fuel (not in your fossil secondary-products list) — the
    Charcoal `…/28,8800` rows are the same defect class but that fuel is
    authored by the bioenergy team; the other 7 (Avgas, Bitumen, Jet Kerosene,
    Kerosene, LPG, Naphtha, Residual Fuel Oil) plus Natural Gas are yours.
    This finding is carried verbatim (spanning both teams).

### A7. Cross-region outliers / unit slips

- **NEW · SUSPICIOUS — NGL Brunei Additions to Reserves = 0.2237 bare "Metric
  Tonne"** (0.22 t as a national reserve is meaningless — lost its Billion-BOE
  scale tag). *4 rows. Resources.*

### A13. Naming / typos

- **KNOWN — `Metalurgical Coke`** (referenced by name in 48 Import Cost
  expressions — a rename must update them). Resources.
  - **Your slice:** `Resources\Secondary\Metalurgical Coke` is one of your
    secondary coal products (LEAP's misspelling — README §2 says author it
    verbatim). The master audit's A13 groups this with `Motorcyle` (transport)
    and a residential comment typo; only the Metalurgical Coke sub-item is
    yours, carried here verbatim with its KNOWN tag. If you ever correct the
    spelling, the 48 cross-fuel Import Cost expressions that cite it by name
    must be updated in the same edit or they break.

---

## Part B — Empty but important (graded)

### 🔴 RED — breaks the calc or actively distorts LP/results in the 4 scenarios now

- **Ammonia RAS Import Cost = `0.001` overriding a real price.** *(KNOWN-adjacent
  · Resources)* CA/Baseline/ATS hold ~$1/kg (`(720+1400)/2*ConvUnits…`); RAS —
  the scenario whose imports the LP optimizes — holds `0.001 ? Placeholder
  cost`. Blast Furnace Gas 0.001 ×12 too. **Mechanism:** if any RAS tech
  consumes ammonia (H2-economy), the solver sources it via near-free imports
  instead of production, silently distorting the RAS energy balance and cost.

- **Zero-cost open supply/import routes.** *(KNOWN #24 · Resources)* In RAS,
  **191 (fuel,region) pairs have Maximum Production ≠ 0 with Production Cost =
  0** (incl. Nuclear at Unlimited + $0), and **95 pairs have open Maximum
  Imports with Import Cost = 0** (Refinery Feedstocks/Gas, Renewable Diesel,
  Arable/Perennial ×12). **Mechanism:** a cap-open, cost-zero route is a free
  lunch the LP exploits regardless of realism — the exact mechanism behind the
  2026-05-18 biodiesel-to-Timor-Leste and 2026-05-19 POME incidents.
  - **Your slice:** the fossil-owned pair inside this list is **Nuclear**
    (`Resources\Primary\Nuclear` at Maximum Production = Unlimited + Production
    Cost = 0, all scenarios — this is the same free-supply shape your README
    §7.7 asks you to rule on) and the **Refinery Feedstocks / Refinery Gas**
    open-import-at-zero-cost routes. **Cross-tree note:** the rest of this
    finding's pairs (Renewable Diesel, Arable/Perennial land pseudo-fuels, and
    the bulk of the 191/95) belong to bioenergy/power — carried verbatim here
    because the finding spans the whole Resources tree; only Nuclear + the
    refinery-feed import routes are yours.

### 🟡 YELLOW — placeholder/template values silently shaping results (wrong numbers, not broken mechanics)

**Resources (your fuels)**

- **Unlimited caps on Natural Gas + all 5 coals (12/12) in every scenario** —
  the fossil canonical authors costs but no caps → un-capped fossil supply (no
  depletion realism) and 1e12 LP-conditioning pollution.
- **Minimum Imports hold-last floors** — 95 RAS rows ending "2022, V>0" extend V
  as a forced import floor to 2060 (Singapore RFO 53,538 kTOE). Standing
  infeasibility/distortion risk as demand evolves.
- **Consumer prices ~95 % zero** on the branches demand regressions reference
  (1,130 of 1,188 cells; Bagasse/coals/NG/MSW Industrial price 44/44 zero).
  **Mechanism:** the Exp/Ln price-elasticity shells evaluate `Ln(0)` → undefined
  or garbage, so fuel-switching response is silently priced at zero. (Same class
  hits industry's referenced prices.)
  - **Cross-tree note:** these Consumer Price cells live on your Resources fuels
    (coals, NG among them), but they are **read by the demand sectors' price
    regressions** (industry, etc.) — the price you author here is upstream of
    their fuel-switching response. Bagasse/MSW inside the same 44/44 count are
    bioenergy/power fuels; the coal + NG cells are yours.

**Resources (referenced by your sector but owned elsewhere — cross-tree)**

- **NEW — Electricity Import Cost = flat `100`** (2020 USD/MWh) in all 12 regions
  × 4 scenarios — the only price for cross-border power trade, a placeholder;
  RAS/CNZ enable the full trade route set, so the build-vs-import decision runs
  on a round template number.
  - **Cross-tree note:** `Resources\Secondary\Electricity` is a **power-team**
    fuel, not yours — listed only so you know the number your refined-fuel and
    gas supply competes against in the trade/dispatch decision is a placeholder.
- **`Unlimited ? tbc` placeholder caps** survive on Biomass/Geothermal/Large
  Hydro/MSW (37 rows) → un-capped renewable supply in the very RAS scenario
  whose RE targets those caps should bind.
  - **Cross-tree note:** Biomass/Geothermal/Large Hydro/MSW are
    **bioenergy/power** primary fuels — carried here only because it is the same
    `Unlimited`-cap class as your NG+coals item above (same §4/§A.11 sentinel
    risk); the fix is theirs to author, not yours.

### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

- **Resources:** all-zero series on *closed* routes (cost 0 paired with cap 0 —
  unreachable today, but a tripwire target: reopening a cap without its cost row
  recreates the RED #2 exploit); "U.S. Dollar" vintage-less units (mostly on
  zero cells).
  - **Your slice:** many of the closed-route zero pairs are your refined
    products (e.g. Diesel/Gasoline/Kerosene/LPG/RFO Maximum Production = 0 in
    RAS, deliberately fed by refinery Transformation instead — see README §7.4).
    They are green **only while both cap and cost stay zero**: if you ever open a
    product cap, author its cost in the same edit or you recreate the 🔴
    zero-cost-open-route exploit.

---

## Highest-leverage for your team

1. **De-scramble the Crude Oil `Additions to Reserves` permutation (A2)** —
   Baseline + ATS hold the 10 country values shuffled (Malaysia has Indonesia's
   SKK-Migas number, etc.); RAS is already correctly aligned, so the correct
   values are in-model to copy. *18 rows, clear correct target.*
2. **Re-author the semicolon / comma-decimal Philippines rows (A3)** — the
   `Data(2024; 1.1)` crude ATR (20 rows) and the `*1,0551` / `44,8000` /
   Philippine consumer-price comma-decimals (58 rows) are committed
   locale-violations with defined correct forms; also settle the suspected
   inverted `*1.0551` GJ↔MMBTU factor with a human math check.
3. **Kill the Ammonia RAS Import Cost `0.001` placeholder (🔴)** — restore the
   real ~$1/kg price CA/Baseline/ATS already hold, so any H2-economy ammonia use
   in RAS doesn't source near-free imports; same for Blast Furnace Gas 0.001.
4. **Send defensible caps for NG + the 5 coals (🟡 Unlimited caps)** — the
   single highest-value gap: `Maximum Production = Unlimited` on Natural Gas and
   all 5 coal grades in every region/scenario means uncapped (and, where
   Production Cost = 0, free) fossil supply plus 1e12 LP pollution. `0` caps for
   genuine non-producers fix supply realism and the sentinel at once.
5. **Rule on Nuclear (🔴 zero-cost route) and the NGL Brunei bare-tonne reserve
   (A7)** — decide whether Nuclear should stay Unlimited + $0 (or carry a finite
   Production Cost), and restore the Billion-BOE scale tag lost on NGL Brunei's
   `Data(2019, 0.2237)` Additions to Reserves.
6. **Review the Minimum Imports hold-last floors (🟡)** — annotate which of the
   95 RAS floors (e.g. Singapore RFO 53,538 kTOE, Singapore/Thailand Crude Oil)
   are deliberate refinery-feed floors vs stale historical series that should
   stop binding after 2022.

---

## Transformation anomalies

Same audit, second tree. The 2026-07-04 hunt has now been extended from
`Resources\` (above) to the **`Transformation\` conversion tree** —
same live model (LEAP area `aeo9_v0.67_w_results`), same four scenarios
(**Current Accounts, Baseline Simulation, AMS Target Scenario, Regional
Aspiration Scenario**). The findings below land on the **15 fossil-owned
Transformation groups** (168 branches per canon §14): the two full
conversion plants **Oil Refining\All Refineries** and **Gas
Processing\Natural Gas**; the five coal-production groups (Anthracite,
Bituminous, Lignite, Sub Bituminous, Unspecified); **Crude Oil
Production**, **Natural Gas Production**, **LNG Regasification**,
**Natural Gas Transmission and Distribution**; the two blending
pseudo-tech groups **Diesel Blending** + **Gasoline Blending**;
**Gasoline Distribution and Handling**; and **Energy Sector Own Use**.

Canon reference: **anatomy §14 §1.3 (fossil owner) + ledger #34.** Same
house rules as the Resources audit above — verbatim findings, cited
counts, **NEW/KNOWN** and **VERIFIED/SUSPICIOUS** tags, 🔴/🟡/🟢 grades,
nothing invented. Every count below is the **verifier-confirmed** figure;
three findings whose original count field was arithmetically off carry a
`(verifier-corrected …)` note. Part A is authored-value anomalies; Part B
is empty-but-important gaps. Structure is canon; the *expressions* here are
what your team is being asked to judge.

### Part A — Incorrectly inputted (Transformation)

#### TA1. `Unlimited` on capacity upper-bounds (canon under-scoped)

- **NEW · VERIFIED — Maximum Capacity = `Unlimited` on the two full-plant
  processes.** `Transformation\Oil Refining\Processes\All Refineries`
  (units Thousand Gigajoules/Year) and `Transformation\Gas
  Processing\Processes\Natural Gas` (units Thousand Tonnes Oil
  Equiv/Year) both carry `Maximum Capacity = Unlimited` in the Regional
  Aspiration Scenario — so the optimizer can build unbounded
  refinery / gas-processing capacity (upper-bound 1e12 sentinel).
  **Canon under-scoped:** anatomy §14 §1.3 documents RAS `Maximum
  Capacity = Unlimited` only for the four blending pseudo-techs; these
  two real full-plant processes also carry it and are genuinely absent
  from canon. Compounded by `Fixed OM Cost = 0` on the same two plants
  (TB3 below). *24 rows (2 procs × 12 regions × RAS only). Transformation.*
  All 72 fossil `Maximum Capacity` rows live in RAS: these 24 + the 48
  on the four blending pseudo-techs.

#### TA2. Cross-region cost-representation inconsistency

- **NEW · SUSPICIOUS — Oil Refining capital cost authored under two
  incompatible conventions.** On `Oil Refining\Processes\All
  Refineries`, 8 of 12 regions use `Capital Cost = Mean(2.6, 3.05)*…`
  (coefficient 2.825); **Indonesia** uses `Mean(0.53, 1.62)` (1.075,
  ~2.6× cheaper) and **Malaysia** `Mean(0.87, 0.96)` (0.915, ~3× cheaper)
  — the two largest refiners cheapest — while **Singapore** and
  **Thailand** author `Capital Cost = "0 ? All costs in Variable OM
  Cost"` and instead carry an inflated `Variable OM Cost` lead
  coefficient (Singapore 18.17, Thailand 22.70 vs the 0.425
  `Mean(0.34, 0.51)` baseline the other 10 regions use — ~43–53×). The
  convention is **self-consistent per region** (the SG/TH comment is
  truthful), but any per-region total-cost comparison must reconcile
  both conventions, and whether Indonesia/Malaysia's ~3× cheaper capex
  is intended needs a human ruling. *16 rows (SG/TH Capital Cost 8 +
  SG/TH Variable OM Cost 8, all 4 scenarios). Transformation.*

#### TA3. Physical-bound violation (efficiency > 100%)

- **NEW · VERIFIED — Vietnam Oil Refining `Process Efficiency` hits
  101.91% at year 2017** — thermodynamically impossible for crude
  refining. Full expression:
  `Interp(2005, 100.00, 2009, 76.83, …, 2017, 101.91, 2018, 86.73, …)
  * Key\Cal\Transformation\Oil refining:Activity Level[Factor]`. A
  single historical-calibration data point overshoots 100%; it is the
  **only** fossil Process Efficiency point in (100.5, 300) — all other
  fossil PE values are the scalar set {0, 100} or Interp maxima ≤100.
  Low LP impact (historical year × a Cal factor) but a data-quality
  blip. *4 rows (1 distinct expression × 4 scenarios). Transformation.*

#### TA4. Embedded control-character / token hygiene

- **NEW · SUSPICIOUS — literal `_x000D_` carriage-return escape tokens
  embedded inside live expression strings**, leaked from the source
  XLSX multi-line cells. On the **Gasoline Distribution and
  Handling** `Avg Environmental Loading` (TVP evaporative-loss)
  formula the token sits **mid-formula** (char ~44, before the first
  `?` comment marker at char ~105:
  `…668/0.739/1000_x000D_\n+ ((9*Gasoline:TVP…`) — genuinely inside the
  load-bearing emission expression; on the two NG-Losses cells (Thailand
  NG Production Losses, Myanmar NG T&D Losses) it sits in the comment
  tail. Likely an export-digest artifact (CR in a wrapped cell) rather
  than a LEAP-side parse break, but the mid-formula placement should be
  **confirmed benign in the live area**. *56 rows (48 Gasoline
  Distribution + 4 Thailand NG Production Losses + 4 Myanmar NG T&D
  Losses). Transformation.*

#### TA5. Separator / no-space Interp style (cosmetic, NOT a §A.15 violation)

- **NEW · VERIFIED cosmetic — no-space Interp list style**
  `Interp(2007,8.5,2008,9.48,…)` deviating from the canon / §A.15
  comma-space form. The decimal mark is a **period** (not
  comma-decimal), so this is **not** a §A.15 decimal violation and not
  a semicolon-list-separator violation (0 of those across the fossil
  tree) — purely a sibling-style inconsistency. Confined to
  **Indonesia Oil Refining `Output Share`** (Naphtha / Jet Kerosene /
  Kerosene / etc., 32 rows) and **Brunei Natural Gas `Exogenous
  Capacity` + `Historical Production`** (7 rows). *39 rows.
  Transformation.* **(verifier-corrected scope: the 7 Brunei rows are
  under `Transformation\Gas Processing\Processes\Natural Gas`, NOT the
  distinct `Natural Gas Production` group the original finding named —
  count 39 unchanged, branch attribution corrected.)*

- **NEW · VERIFIED clean (false-positive pre-empt) — semicolons in 18
  fossil expressions are ALL inside the free-text `?`-comment tail**
  (citation-source separators), never inside an `Interp()` / `Data()`
  argument list — so there is **no §A.15 semicolon-list-separator
  violation** in the fossil Transformation domain. All 18 are Oil
  Refining `Exogenous Capacity` historical series (e.g.
  `…~ ? Historical Production converted to GJ/Year;  Hengyi press + EI
  SR 2024` — the `;` separates two citations after the `?`). A
  parenthesis-depth scan of every Interp/Data call found 0 semicolons
  inside argument lists. *18 rows. Verified not a defect.*

#### TA6. Sibling-variant inconsistency (feedstock cost wiring)

- **NEW · SUSPICIOUS — `Feedstock Fuel Cost` wiring differs across the
  five coal-production siblings.** `Sub Bituminous Coal Production`
  wires `Fuel Cost = Resources\Primary\Coal Sub bituminous:Production
  Cost` (branch-ref) in **all 12 regions** (48 rows), whereas
  Bituminous / Lignite / Unspecified Coal Production wire the
  equivalent ref only for **Indonesia** (4 rows each), Anthracite wires
  **none**, and Oil Refining's Natural Gas feedstock cost is wired only
  for Indonesia (4). Likely reflects which grade each country actually
  produces, but the asymmetry reads as inconsistent authoring — needs a
  production-geography vs authoring-gap ruling. *64 nonzero rows
  (Sub Bituminous 48 + Bituminous 4 + Lignite 4 + Unspecified 4 + Oil
  Refining Natural Gas 4; Anthracite 0); 800 of 864 Fuel Cost rows are
  `0`. Transformation.* **(verifier-corrected count: 64 nonzero, not
  the original "60" — the original summed only the four coal grades
  48+4+4+4 and dropped the 4 Oil Refining Natural Gas rows it described
  in prose. `800/864 = 64 nonzero` was internally consistent all along.)*

#### TA7. Solver-writeback `Data()` series (VERIFIED not conflated)

- **KNOWN · VERIFIED clean — solved-area `Data()` series present but on
  the correct variables — no input/output conflation.** `Optimized New
  Capacity` carries CPLEX endogenous results stamped `?Optimized on
  07/02/2026 (NEMO/CPLEX)` in **RAS only** (247 rows, 100% on the
  endogenous `Optimized New Capacity` variable) — confirming RAS is the
  sole NEMO/CPLEX-solved scenario of the four (Baseline + AMS Target
  carry `Optimize = No`, Current Accounts is pure accounting). The 6
  Cambodia/Laos Oil Refining `Exogenous Capacity` rows
  (`Data(2024, 0, …, 2060, 0) ? IEA Oil Info 2024`) are **authored
  explicit zeros** (non-refiners), not solver writeback. The solver
  output lives only on the endogenous variable; input `Exogenous
  Capacity` is untouched by CPLEX. *253 rows (247 + 6). Transformation.
  Already in canon (§14, ledger).*

#### TA8. Negative-result clean sweep (VERIFIED — nothing found)

- **NEW · VERIFIED — the rest of the fossil Transformation tree is
  token / separator / bounds clean.** Across the ~22,944 in-scope
  fossil rows: broken tokens (`!Missing Branch` / `Bad Scenario` /
  `Bad Unit` / `#REF`) = **0** (expression AND units columns); the bare
  **§11.2c must-run trap** (`Minimum Utilization = "Maximum
  Availability"`) = **0** (all 288 fossil MU rows are `0`, incl. the 192
  blending rows; `Maximum Availability` value set = {`100`}); `Maximum
  Availability` > 100 = **0**; `Process Efficiency` > 100 = only the
  Vietnam case (TA3); leading-negative values = **0**; Carbon Dioxide
  (non-biogenic) emission factors on combustion leaves = **480/480
  nonzero** (e.g. Crude Oil `73.3 ?a`, LNG `56.1 ?a`). *0 defects.
  Transformation.* Note the coal-mining groups expose **only** a
  Methane emission leaf (no CO2 leaf) — see TB4.

### Part B — Empty but important (Transformation, graded)

#### 🔴 RED — breaks the calc or actively distorts the LP now

- **KNOWN · VERIFIED DEFECT — Blending pseudo-tech `Exogenous Capacity`
  = `Unlimited` (units Megawatt) → §A.11 1e12 forced FLOOR.** All four
  biofuel-mandate blending processes — `Transformation\Diesel
  Blending\Processes\{Biodiesel, Diesel}` and `Transformation\Gasoline
  Blending\Processes\{Ethanol, Gasoline}` — author `Exogenous Capacity =
  Unlimited` in a nonsensical unit (Megawatt on a fuel-passthrough
  blender). `Exogenous Capacity` maps to NEMO `ResidualCapacity`, and
  the LEAP→NEMO export turns the literal `Unlimited` into a `1.0e+12`
  **forced lower-bound floor** — the §A.11 landmine, the exact
  2026-05-12 aeo9_v0.42 p9 shape. 1e12 MW of forced residual blending
  capacity enters the LP basis as a hard floor and, per §A.11, the 10¹²
  sentinel breaches CPLEX's ~10⁹ conditioning tolerance even when
  non-binding. Present in all 4 in-scope scenarios (48 each), but only
  RAS is NEMO/CPLEX-optimized among them (Baseline + AMS Target carry
  `Optimize = No`, CA is pure accounting) — so the LP distortion lands
  in RAS. *192 rows (4 procs × 12 regions × 4 scenarios). Transformation.
  Already in canon: ledger #34 + §14 §1.3 (528 rows = 4×12×11; the 192
  is the 4-scenario in-scope subset).*
  - **CAVEAT worth surfacing to a human:** canon ledger #34 and project
    memory (`project_aeo9_v042_RAS_resolved`) both record this **exact**
    shape was judged a **red herring** in the 2026-05-12 aeo9_v0.42
    probe and never remediated — i.e. empirically it did **not** break
    that solve. So "breaks the calc now" is the in-principle §A.11
    mechanism, **not** an observed break. It survives unchanged in
    aeo9_v0.67; the RED grade is the structurally-defensible §A.11
    priority, with the empirical red-herring history attached.

#### 🟡 YELLOW — template/placeholder values silently shaping results

- **KNOWN · VERIFIED DEFECT (benign upper-bound) — `Maximum Production`
  = `Unlimited` (units Gigajoule) on every fossil process in RAS.** Coal
  mines (5 grades), Crude Oil, Natural Gas Production, LNG
  Regasification, NG T&D, Gas Processing, Oil Refining, the 5 Energy
  Sector Own Use processes, Gasoline Distribution, and both blending
  groups — 252 rows, all literal `Unlimited`, RAS only (the accounting
  scenarios carry no `Maximum Production` rows). Un-caps every fossil
  supply/conversion route in the LP and adds 10¹²-scale coefficients
  that degrade CPLEX conditioning; also risks the §A.11 silent-parse
  failure that exports as missing/zero for some AMS. Because fossil
  supply **cost** is authored on the Resources tree (not here), an
  un-capped Transformation route is bounded only by whatever Resources
  caps + costs exist — **ties directly to Resources ledger #24** (the
  zero-cost open-route gap in the RED item above). *252 rows (21 fossil
  process nodes × 12 regions). Transformation. Already in canon: §14
  §1.3 + ledger #34.*

- **NEW · SUSPICIOUS — `Fixed OM Cost` = 0 on the only two
  capacity-planned fossil conversion plants** (`Oil Refining\All
  Refineries`, `Gas Processing\Natural Gas`), in every region and
  scenario — even though these two are the archetype that carries the
  full capacity-planning panel. Their `Capital Cost` is nonzero (96/96)
  and `Variable OM Cost` nonzero, but the fixed component is uniformly
  zero. Combined with RAS `Maximum Capacity = Unlimited` (TA1), the RAS
  optimizer prices new refinery / gas-processing capacity on
  capital + VOM only — understating the fixed carrying cost of domestic
  conversion versus imports. *96 rows (2 procs × 12 regions ×
  4 scenarios). Transformation.*

- **NEW · SUSPICIOUS — Coal-mine `Methane` emission factor = plain,
  uncommented `0` on Sub Bituminous Coal Production** across all 12
  regions × 4 scenarios, whereas the four sibling coal grades
  (Anthracite / Bituminous / Lignite / Unspecified) carry the real IPCC
  coal-mine-methane factor `12.06 ?a) … IPCC (2006) … (Tier 1)` where
  the grade is produced and the *commented* `0 ? No indigenous
  production …` where it is not. Methane is the **only** GHG species
  modeled on coal-mining branches (no CO2 leaf). Sub Bituminous is the
  actively-produced grade region-wide (it alone wires Fuel Cost →
  Resources Production Cost in all 12 regions — see TA6 — and is
  Indonesia's dominant thermal coal), so a **plain** zero with no "no
  indigenous production" comment reads as a forgotten / un-authored leaf
  rather than an intentional zero, and understates coal-mining CH4
  (high-GWP) in every scenario's emissions accounting. Understatement is
  concrete chiefly for genuine producers (Indonesia dominant);
  non-producer regions' zero is defensible — hence YELLOW, not a
  calc-breaker. *48 rows. Transformation.*

- **KNOWN · VERIFIED DEFECT (placeholder) — `Annual Avg Ambient Temp` =
  `15 ? Fill in country-specific value`** — a template-uniform
  placeholder identical across all 12 regions (including equatorial
  ASEAN, where mean ambient temp is ~27–28 °C). It is one of three
  custom variables (with `Annual Avg Reid Vapour Pressure` and `TVP`)
  driving the `Gasoline Distribution and Handling` evaporative-loss
  model; TVP is a closed-form function of ambient temperature, so a
  15 °C placeholder well below tropical temperatures understates TVP and
  hence the gasoline-handling evaporative VOC/loss emission factor for
  every ASEAN country. Explicit placeholder confession. *48 rows (12
  regions × 4 scenarios, 1 distinct expression). Transformation. Already
  in canon: §14 §1.3.*

#### 🟢 GREEN — empty by design / plausibly-intentional zeros

- **KNOWN · VERIFIED (intentional design, cross-tree dependency) —
  `Variable OM Cost` = 0 combined with `Maximum Production = Unlimited`
  on all extraction / T&D / own-use fossil processes** (the 5 coal All
  Mines, Crude Oil Production, Natural Gas Production, LNG
  Regasification, NG T&D, Gasoline Distribution, and all 5 Energy Sector
  Own Use processes; Feedstock Fuel Cost = 0 too, Fuel Source =
  SourceBelow). **By design** (canon §14 §1.3): fossil supply **cost**
  is authored entirely on the Resources tree (Production/Import Cost),
  so the Transformation conversion node is a zero-cost passthrough.
  Benign in isolation, but it means the LP's entire fossil-supply price
  signal is load-bearing on the Resources side being correctly authored
  — **directly coupled to Resources ledger #24** (191 fuel/region pairs
  with MaxProd ≠ 0 and Production Cost = 0). If any of those Resources
  routes is uncosted, the zero-cost Transformation route makes it a free
  supply path the LP will exploit. *720 of 816 fossil Variable OM Cost
  rows are `0`; the only 96 nonzero are the two full plants.
  Transformation.*

- **NEW · VERIFIED (empty by design) — module-level fossil grid/market
  knobs uniformly zero.** `Module Costs` (624 rows), `Output Price`
  (1,344 rows: 1,340 `0` + 4 `Remainder(100)`), `Import Target` (1,080),
  `Export Target` (1,080), `Renewable Qualified` (72, RAS) — all `0`
  across fossil groups. Confirms the fossil supply/conversion tree
  **exposes but does not use** these levers: no per-fuel output pricing,
  no import/export targets, and fossil techs are (correctly) not
  renewable-qualified. Recorded as an **empty-by-design inventory** so a
  future author does not mistake the empty panels for missing data —
  renewable ambition and trade are enforced elsewhere (blend
  mandates + `__NEMOcc` constraints + `Key\Optimized Trade`). *4,200
  rows total, of which 4,196 are `0` (the 4 non-zero are Output Price
  `Remainder(100)`). Transformation.* **(verifier-corrected count: 4,200
  rows / 4,196 zero — the original headline "3,600" was an arithmetic
  error; the component counts 624+1,344+1,080+1,080+72 = 4,200 were all
  correct.)*

### Highest-leverage for your team (Transformation)

1. **Kill the blending `Exogenous Capacity = Unlimited` (🔴)** — replace
   the literal `Unlimited` (Megawatt) on the four Diesel/Gasoline
   Blending processes with `0` (or a finite floor if one is genuinely
   needed): the §A.11 1e12 forced-floor landmine, live in RAS. Attach
   the red-herring caveat when you rule on it (it did not break the
   2026-05-12 solve).
2. **Cap and cost the two full plants (🟡 / TA1 / TB3)** — decide the
   real `Maximum Capacity` for `Oil Refining\All Refineries` and `Gas
   Processing\Natural Gas` (both currently `Unlimited` in RAS) and give
   them a non-zero `Fixed OM Cost`; today the RAS optimizer builds
   unbounded conversion capacity priced on capital + VOM only.
3. **Fix the Vietnam Oil Refining 101.91% efficiency point (TA3)** — a
   single 2017 calibration point overshoots the thermodynamic 100%
   ceiling; clamp it to ≤100.
4. **Wire Sub Bituminous coal-mine Methane (🟡 / TB4)** — the actively
   produced grade carries a plain uncommented `0` where its four
   siblings carry the IPCC `12.06` factor; supply the real coal-mine CH4
   factor for genuine producers (Indonesia first).
5. **Populate `Annual Avg Ambient Temp` (🟡 / TB5)** — replace the
   `15 ? Fill in country-specific value` placeholder with per-country
   tropical ambient temperatures so the gasoline evaporative-loss model
   stops understating VOC emissions.
6. **Rule on the cost-convention split and the coal Fuel Cost asymmetry
   (TA2 / TA6)** — confirm whether Singapore/Thailand's fold-everything-
   into-VOM refinery costing and the Sub-Bituminous-only Fuel Cost wiring
   are intended or authoring gaps.
