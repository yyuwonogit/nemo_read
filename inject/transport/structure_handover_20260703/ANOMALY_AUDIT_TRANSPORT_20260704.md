# Transport — Anomaly Audit (your slice) — 2026-07-04

This is the **transport slice of the full cross-sector canon anomaly audit**
run on the live LEAP model (`aeo9_v0.67_w_results`, 2026-07-04) over the four
scenarios that matter — **Current Accounts, Baseline Simulation, AMS Target
Scenario, Regional Aspiration Scenario**. Every item below is a defect the
sweep found in **branches your team owns or authors** (the whole
`Demand\Transport` export, plus the transport-facing SAF/aviation policy rows).
It is split into **Part A — incorrectly inputted** (something authored is
wrong) and **Part B — empty but important** (missing/placeholder values, graded
🔴 red / 🟡 yellow / 🟢 green). Each item is tagged **NEW** vs **KNOWN** (already
on our hygiene ledger) and **VERIFIED DEFECT** vs **SUSPICIOUS — needs human
judgment**; counts are rows in the four scenarios. You know this data better
than the detector does — please **judge each item and fix the ones that are
real**; the SUSPICIOUS ones especially need your call. A few defects sit in a
`Key\…` or `Resources\…` tree that your Road formulas merely *pull from* — those
are flagged with a **cross-tree note** so you know they're upstream of you and
owned by another team.

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
  - **Cross-tree note:** the sales-share values themselves live in
    `Key\TransportDataStock\Vehicles_Sales_Share\Truck\…` (owned by the
    keys/central team). The **defect here is on your Road Sales formula**,
    which references the wrong sibling key; the keys owned by the central team
    are fine.

### A4. Duplicate branch / parallel-tree double count

- **NEW · VERIFIED — CA Road Stock series pasted across vehicle classes.** The
  same historical `Data()` series is byte-identical on Bus, PassengerCar and
  Truck for a given (region, fuel); summing 2024 stock across powertrains gives
  bus fleets **26–177× larger** than the Key `BaseYear_StockData` (Indonesia
  74×, Malaysia 166×, Philippines 177×). The series look like all-class fuel
  totals reused per class. *106 rows / 32 (region,fuel) groups. Transport.*
  - **Cross-tree note:** the reference fleet magnitude this is compared against,
    `Key\TransportDataStock\BaseYear_StockData\<Vehicle>` ("fleet on the road in
    2024"), is owned by the keys/central team. That Key slot has its **own**
    stock-vs-sales seam (values sized like one year's sales rather than a full
    fleet — see §6/§7.6 of your structure handover) — a fridge-style
    stock-vs-sales seam that is upstream of your Road Stock and owned there.

### A5. CA → forward-scenario discontinuities (level jumps at the 2024/25 seam)

- **KNOWN · VERIFIED — Truck NG Fuel Economy 12 → 5, Indonesia only**, in all
  forward scenarios (the sole per-region override in the FE panel); compounds
  the phantom-fleet defect (A1). *10 rows. Transport.*

### A6. Within-series data corruption

- **NEW · VERIFIED — Indonesia 2015 Stock is exactly /129.4 of its neighbours**
  in 5 independent series simultaneously (identical divisor ⇒ systematic source
  slip, not noise). *5 series. Transport.*
- **NEW · SUSPICIOUS — mid-series level shifts (source splices)** ≥5× in CA
  Stock: Thailand Blended Gasoline 382 → 196,447 (514×), Malaysia Electricity
  25 → 4,777 (191×), etc. *17 series. Transport.*

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

### A11. CR artifacts inside live code

- **KNOWN — `_x000D_` before the `?`** in transport IW (Inland Waterways) FEI
  `If()` formulas. *Transport 10.* (Same class hits residential; that portion is
  in the residential slice — 334 rows there.)

### A12. Comment hygiene hiding data problems

- **KNOWN — transport SAF:** Indonesia comment says "only available in AREC and
  ASER" yet the mandate is authored across the RAS bloc; Thailand carries a
  superseded expression inside a `??` double-comment (the version ATS actually
  uses) → the two scenarios silently swapped provenance. *Transport.*

### A13. Naming / typos

- **KNOWN — `Motorcyle`** (demand) vs `Motorcycle` (Key) — name-based joins
  break. Transport.
  - **Cross-tree note:** this is a two-tree name split. Your `Demand\Transport`
    tree spells the class `Motorcyle` (the typo); `Key\TransportDataStock`
    spells it `Motorcycle` — except `Effective Operational_Stock\Motorcyle`,
    which carries the typo *inside* the Key tree too. The Key-side spelling is
    owned by the keys/central team; flagged here because the mismatch is
    upstream of your Road formulas' name-based joins.

### A14. Other structural

- **KNOWN — `Demand\Transport_` underscore self-references** in TotShare_AltFuels
  / Share_FossilFuels (96 rows) — resolves in-LEAP but breaks offline joins.
- **KNOWN — dollar-vintage mismatches:** transport Rail "2020 USD" denominator
  vs `GDP[Million 2021 USD]`. *(This is the transport portion of the wider
  dollar-vintage item; resources and residential carry their own.)*

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

### 🟡 YELLOW — placeholder/template values silently shaping results (wrong numbers, not broken mechanics)

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

### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

- **Inland Waterways Kerosene zero pollutants** (marginal — only Indonesia's tiny
  declining barge use).
- **Demand Cost / Average Mileage / Final On-Road result-vars all constant-0**
  (dead plumbing).
- **Timor Leste + Base Template mileage "ACE default"** (TL disabled in calc).

---

## Highest-leverage for your team

1. **Fix the Truck-NG Sales key (A1)** — a one-character branch swap
   (`Electricity` → `Natural Gas` on `Road\Truck\Natural Gas:Sales`) kills a
   phantom NG-truck fleet that is currently distorting RAS gas demand; it also
   compounds with the 5-MPG defect (A5), so fixing both cleans one story.
2. **Decide Road transport emissions (🔴 B1)** — the single largest results gap
   in your sector: supply or recommend a tailpipe emission-factor set so road
   CO2/CH4/N2O actually reach the emissions results and GHG/net-zero measures.
3. **Resolve the SAF-FEI-evaluates-to-zero ambiguity (🟡)** — one LEAP UI
   methodology check decides whether the flagship SAF mandate (Indonesia 50 % by
   2060) does anything at all; also settle SAF CO2 fossil-vs-biogenic accounting.
4. **De-corrupt the CA Stock series** — the Indonesia 2015 /129.4 slip (A6,
   VERIFIED) and the mid-series ≥5× splices (A6, SUSPICIOUS), plus the
   class-pasted CA Road Stock (A4) that inflates fleets 26–177×.
5. **Adjudicate the stray single-region edits (A9)** — Truck-NG 12→5 Indonesia
   (A5), Philippines aviation +1 % tail, Brunei Mileage Correction one-off,
   PassengerCar First Sales Year = 2024 — each is one country/class out of line;
   tell us the intended value.

---

*Cross-tree reminder:* the items marked **cross-tree note** (Truck sales-share
key values, `BaseYear_StockData` stock-vs-sales seam, the `Motorcyle`/
`Motorcycle` name split) live in `Key\TransportDataStock` and are **owned by the
keys/central team** — your Road branches only reference them. Flagged so you know
they're upstream; the central team has the matching items in their own slice.
