# Anomaly audit — your slice (Key\ assumptions tree)

This is the **Keys / central-assumptions team's slice** of the full-corpus
canon anomaly audit (`CANON_ANOMALY_AUDIT_20260704.md`, generated 2026-07-04
over the six canon exports of LEAP area `aeo9_v0.67_w_results`, scoped to the
four scenarios that matter: **Current Accounts, Baseline Simulation, AMS
Target Scenario, Regional Aspiration Scenario**). It contains only the items
that touch branches your team owns or authors inside the `Key\` tree — plus a
set of clearly-marked **cross-tree notes** for defects that *live in your
branches but break a downstream demand sector*, and for upstream defects that
your branches merely reference. Everything is carried over faithfully from the
master audit (verbatim finding text, counts, `NEW`/`KNOWN`,
`VERIFIED`/`SUSPICIOUS`, and the 🔴/🟡/🟢 grade); nothing here is a new finding
we invented. **Your job is to judge each item and fix or rule on it** — you own
the assumptions layer, so you're the adjudicator for the whole `Key\` tree even
where the *symptom* surfaces in another sector's numbers. Items sourced from
your own handover §7 known-issues (rather than the master audit's detectors)
are labelled `[from handover §7]` so you can tell the two provenance streams
apart. Counts are rows in the 4 scenarios.

---

## Part A — Incorrectly inputted (anomalies in authored values)

### A5. CA → forward-scenario discontinuities (level jumps at the 2024/25 seam)

- **NEW · VERIFIED — fridge ownership collapses 2022→2023.**
  `Key\Residential\Refrigeration\Percent Ownership` splices two sources inside
  one Interp: Philippines 88 → 50 (−38 pp), Indonesia 97.6 → 89, Vietnam 100 →
  80.5 — a physically impossible one-year drop in **9 of 11 countries**, and it
  drives the whole `Refrigeration_` device-stock saturation. *36 rows.
  Residential/Keys.*
  → **Owned here, breaks downstream.** The branch is in your tree
  (`Key\Residential\Refrigeration\Percent Ownership`, branch_id 29116). It is
  the *driver* behind the residential team's `Refrigeration_` device-stock
  double-count (their A4). Re-author the ownership Interp so the two source
  segments join continuously, and the downstream fridge-electricity artifact
  clears with it.

### A13. Naming / typos

- **KNOWN — `Motorcyle`** (demand) vs `Motorcycle` (Key) — name-based joins
  break. Transport.
  → **Owned here, breaks downstream.** The name split is *your* spelling: in
  `Key\TransportDataStock`, `BaseYear_StockData\Motorcycle` is spelled
  correctly while `Effective Operational_Stock\Motorcyle` (branch_id 16776) is
  missing the second `c`. The transport demand tree keys against one form,
  breaking the offline join. Adjudicate the canonical spelling and queue a
  coordinated rename with the transport team (per handover §7.2, renames need a
  consumer sweep).

### A9. Single-region formula deviations (stray edits) — *cross-tree note only*

- **NEW · SUSPICIOUS — PassengerCar First Sales Year = `2024`** on all four
  powertrains while every Bus/Motorcyle/Truck powertrain uses `BaseYear` — an
  unexplained per-class methodology split affecting stock-turnover vintaging.
  *48 rows. Transport.*
  → **Cross-tree note:** this deviation is authored on the transport *demand*
  branches, not in `Key\`, so it is the transport team's to fix — but it uses
  the `Motorcyle` [sic] spelling in its own description and interacts with your
  `Key\TransportDataStock` vintaging, so it is listed here for awareness only.
  Owned by transport.

---

## Part B — Empty but important (graded)

### 🔴 RED — breaks the calc or actively distorts LP/results in the 4 scenarios now

*No RED item is owned inside the `Key\` tree.* Two RED items are **upstream of
you / downstream of you** and are flagged as cross-tree notes below so you know
they touch your layer:

- **Cross-tree note (owned here, breaks downstream) — Consumer prices ~95 %
  zero → `Ln(0)` exposure.** Master audit RED-adjacent (graded 🟡 in the master,
  see Part B YELLOW below) but called out here because the master audit says
  the price-elasticity shells *reference* branches whose macro drivers you own.
  See the YELLOW "Consumer prices" item.
- **Cross-tree note (upstream, owned elsewhere) — Zero-cost open supply/import
  routes** *(KNOWN #24 · Resources)* and **Ammonia RAS Import Cost = `0.001`**
  *(KNOWN-adjacent · Resources)*: these are `Resources\` defects, not `Key\`.
  They become live only when `Key\Optimized Trade\*:Activity Level` flips to `1`
  (RAS + Carbon Neutrality). You own the trade master switch; the cost/cap
  defects the switch exposes are Resources'. Coordinate the enable-order with
  the resources team so trade doesn't open onto a free-lunch route.

### 🟡 YELLOW — placeholder/template values silently shaping results (wrong numbers, not broken mechanics)

**Keys (owned here)**

- **NEW — every transmission interconnector has Variable OM Cost = 0** (all
  1,008 `Key\Transmission\Lines\*` rows). Zero variable cost to move electricity
  across borders biases the LP toward trade; relevant once RAS/CNZ enable the
  grid.
  → Directly yours. The `Variable OM Cost_` variable is authored `0` on every
  `Key\Transmission\Lines\<A>_<B>_{E,F,C}` panel. Set a defensible non-zero
  per-MWh wheeling cost before RAS/CNZ trade is scored.

**Cross-tree note (owned here, breaks downstream) — Consumer prices ~95 % zero**

- **Consumer prices ~95 % zero** on the branches demand regressions reference
  (1,130 of 1,188 cells; Bagasse/coals/NG/MSW Industrial price 44/44 zero).
  **Mechanism:** the Exp/Ln price-elasticity shells evaluate `Ln(0)` → undefined
  or garbage, so fuel-switching response is silently priced at zero. (Same class
  hits industry's referenced prices.) *Resources.*
  → The empty price *cells* are on `Resources\` branches (owned by resources),
  but the **macro drivers feeding the demand price-elasticity regressions live
  in your `Key\Macroeconomic\*` tree** — the regressions that go `Ln(0)` are
  fed by your GDP / GDP-per-capita / fraction-in-GDP series. Any zero (or
  missing) driver you author propagates into the same undefined-log exposure
  downstream. Confirm your macro series are non-zero across the regression years
  and coordinate with resources on the price cells.

**Cross-tree note (owned here, referenced by industry) — "Fill in historical
data here" macro stubs**

- **"Fill in historical data here" stubs** — `0 * Key\Macroeconomic\
  Manufacturing Fraction…? Fill in historical data here` (214 rows) — zero-valued
  FEI awaiting data; plus 643 unfitted regression shells (coefficients = 1) and
  528 `?placeholder` CCS sequestration ramps, all live in the 4 scenarios.
  *Industry.*
  → The master audit tags the 214-row FEI stub as Industry, but the multiplier
  it zeroes out is **your branch** `Key\Macroeconomic\Manufacturing Fraction in
  Industry`. Industry's FEI evaluates to zero because it multiplies against
  your still-empty macro fraction. Populate the `Key\Macroeconomic` fraction
  series and the downstream `0 * …` industry stub comes alive. Owned here for
  the driver; the FEI shell itself is industry's.

### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

*No `Key\`-owned item appears in the master audit's GREEN list.* (The GREEN
entries are all Transport / Residential / Resources plumbing.)

---

## Additional Key\-owned issues carried from your structure handover §7

These are keys-scope defects named in the task and documented in your own
handover `README_KEYS_CANON_STRUCTURE.md` §7 known-issues. They are **not** in
the master audit's automated detector output (the audit's keys pass ran into
model limits — see its methodology note), so they carry no master-audit
count/tag; each is labelled `[from handover §7]`. They are yours to adjudicate.

- **Household Size "placeholder based on discussion"** `[from handover §7.7]` —
  `Key\Demographic\Household Size` for **Myanmar** (AMS Target + RAS) =
  `Interp(2040, 4) ? placeholder based on discussion`. Every other AMS carries a
  real historical series (Timor Leste flat `5.28`; Base Template template `4`).
  Can Myanmar be sourced?
- **`!Construction Year` "to be confirmed"** `[from handover §7.6]` — the
  deactivated `!Construction Year` on the 21 `Key\Transmission\Lines\*` panels
  carries values like `2040 ? awaiting confirmation after adding`. Intentionally
  retired, or awaiting data? (Same panel: `!Reactance` deactivated on all 21.)
- **Historical PPV / vehicle-data "Fill in" stubs** `[from handover §7]` —
  `Key\Transport vehicle data_` / `Key\TransportDataStock` passenger-car number
  series carry author confessions (`ppv constant`, "use interpolation to fill in
  missing data 2019-2022", "use updates on the number of passenger car from
  ASEANStat / NSTDA Study to reflect actual condition"). Zero/placeholder
  vehicle stock awaiting real data. 16 "Fill in" rows in the 4-scenario dump.
- **Single-point `Interp` constants** `[from handover §7]` — many
  `Key\Cal\*` calibration factors are authored as a lone-anchor Interp, e.g.
  `Key\Cal\Residential\Biogas` = `Interp(2024, 15.5445597766)` (Cambodia) /
  `Interp(2024, 0.189919389851)` (Indonesia). A single-point Interp holds the
  constant flat forever — confirm that is intended vs a truncated series.
- **The `DIspatch` spelling trap** `[from handover §7.2]` — capital-"DI" typo in
  `Key\Modeling Assumptions\Incumbent Generator DIspatch Phaseout` (branch_id
  14452). Case-sensitive path lookups miss it; Transformation Minimum
  Utilization formulas are believed to consume it (*pending Transformation
  export* to confirm). Rule "keep as-is (documented casing)" or "queue a
  coordinated rename once consumers are confirmed." (Same class: `Metalurgical
  Coke` [sic] on `Key\Cal\Industry` + two `Key\Industry\Intensity` steel leaves.)
- **`Key\Temp` scratch branch carrying live scenario signal** `[from handover
  §7.1]` — one branch, units literally `temp`, holding unit-conversion
  arithmetic (`ConvFuelUnits(gal gas eq, kg, natural gas) * ConvUnits(km,
  mile)`; Indonesia holds `ConvFuelUnits(liter, gj, biodiesel)`) — and it is the
  single cell distinguishing RE Coupling from Shared Energy Resources. Is
  anything downstream reading it? Can it be frozen or renamed to something
  self-describing?
- **Stale `Key\Residential\AC\{a,b}` comment citations** `[from handover §7.3]`
  — 232 residential rows cite `Key\Residential\AC\{a,b}` inside `?` comments
  preserving a retired AEO7 regression; the branches do **not** exist in the
  area and the live expressions are GDP-per-capita `Lookup` curves. No model
  breakage, but the comments now mislead readers. Confirm the branches are
  permanently retired; on your yes, the comment cleanup goes to the residential
  team.

---

## Highest-leverage for your team

1. **Fix the fridge-ownership 2022→2023 collapse** (A5) —
   `Key\Residential\Refrigeration\Percent Ownership`. One re-authored Interp in
   your tree clears a downstream residential double-count driver in 9 of 11
   countries.
2. **Resolve the `Motorcyle`/`Motorcycle` name split** (A13) in
   `Key\TransportDataStock` — adjudicate the canonical spelling and run the
   coordinated transport-consumer rename so name-based joins stop breaking.
3. **Price the transmission interconnectors** (🟡 Keys) — set a non-zero
   `Variable OM Cost_` on all 1,008 `Key\Transmission\Lines\*` rows before
   RAS/CNZ scores cross-border grid trade on a $0 wheeling cost.
4. **Populate the `Key\Macroeconomic` drivers** — the empty
   `Manufacturing Fraction in Industry` (and its siblings) both zero out the
   industry FEI stub (214 rows) and feed the demand-side price-elasticity
   regressions exposed to `Ln(0)`. Filling your macro series fixes two
   downstream sectors at once.
5. **Adjudicate the standing placeholders** (Household Size Myanmar,
   Transmission `!Construction Year` / `Lifetime_ 80`, single-point Cal Interps,
   PPV "Fill in" vehicle stubs) and the two rename/scratch traps (`DIspatch`
   typo, `Key\Temp`) — each is a one-line ruling that closes an open Key issue.
