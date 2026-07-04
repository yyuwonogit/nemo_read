# Anomaly audit — Industry slice (`aeo9_v0.67_w_results`)

This is the **industry slice** of a full-corpus anomaly sweep we ran over
the whole model on 2026-07-04 (all six canon exports, scoped to the four
scenarios that matter: **Current Accounts, Baseline Simulation, AMS Target
Scenario, Regional Aspiration Scenario**). We have pulled out only the
items that touch your sector — the `Demand\Industry` tree, its
`Key\Industry` drivers, and the two upstream trees your formulas reach
into (Resources consumer prices, `Key\Macroeconomic`). Everything below is
copied faithfully from the master audit: verbatim finding text, counts,
and grades are unchanged. **Your job with this file is to judge and fix**
— for each item, tell us whether the current value is intended (and cite a
source) or wrong (and give us the correction). Every item carries two tags:
**NEW** vs **KNOWN** (already in our hygiene ledger) and **VERIFIED
DEFECT** vs **SUSPICIOUS — needs human judgment**. Counts are rows in the 4
in-scope scenarios unless stated. Items marked "needs a LEAP UI check"
cannot be settled from the export alone.

---

## Part A — Incorrectly inputted (anomalies in authored values)

These are things that are authored **wrong** — corrupted tokens, dangling
references, broken templates that are live in the model right now.

### A8. Dangling references / corrupted tokens

- **KNOWN · VERIFIED — `!Missing Branch` + `Bad Scenario [2]` templates are
  LIVE in AMS Target Scenario.** Industry Historical-fuel FEI carries
  `InterpFSY(!Missing Branch (ID=3477)!, ScenarioValue(Bad Scenario [2],
  …))` and `Interp(!Missing Branch (ID=3465)!, …)`. *140 + 19 rows.
  Industry.*

- **KNOWN · VERIFIED — `Bad Unit [777518900/777691684]`** on Cement Clinker
  technology FEI, **240 rows in every one of the 4 scenarios (960 in
  scope)**. Industry.

  *(Slice note, not part of the master finding: the corrupted unit tag
  sits on `Final Energy Intensity` of the Cement Clinker **Heat** fuel
  leaves — Coal Bituminous, Biomass, Municipal Solid Waste, Natural Gas,
  Residual Fuel Oil — under each of the four kiln technologies. We need the
  intended unit to re-tag them.)*

*(For completeness: the master audit's A8 also lists a commercial-sector
`!Missing Branch (ID=1687/825)` item on Historical Ethanol/Biodiesel FEI
regression shells — that one is the commercial team's, not yours, and is
excluded here.)*

### A5. CA → forward-scenario discontinuities

The master audit's A5 (level jumps at the 2024/25 seam) lists transport and
residential items only. **No verified industry A5 item** — the industry
Historical/Projection split is a clean `Step()` switch, and the broken
EI-reduction template (A8) is likely inert because Historical activity is
`Step()`'d to 0 after 2025.

### A13. Naming / typos (industry-adjacent)

- **KNOWN — `Metalurgical Coke`** (referenced by name in 48 Import Cost
  expressions — a rename must update them). *Resources.* This is an
  upstream (Resources) name, but it is also the fuel name used inside your
  `Key\Industry\Intensity\Iron and Steel\Crude Steel\BOF\BF\Metalurgical
  Coke` branches — if the misspelling is ever corrected, both trees must
  change together. Flagged for cross-tree awareness.

---

## Part B — Empty but important (graded 🔴 / 🟡 / 🟢)

These are values that are **missing, zero, or placeholder** — not corrupted
tokens, but numbers that silently shape or break results. Graded by how
much damage they do in the 4 scenarios right now.

### 🔴 RED — breaks the calc or actively distorts LP/results now

The master audit's three RED items are Road-transport emissions, zero-cost
open supply routes, and the Ammonia RAS import price — **none are inside
the `Demand\Industry` tree**. But two of them reach into trees your
formulas depend on, so they are your problem by reference:

- **Zero consumer prices break your FEI regressions (upstream, Resources).**
  The master audit's 🟡 Resources item — *"Consumer prices ~95 % zero on
  the branches demand regressions reference (1,130 of 1,188 cells;
  Bagasse/coals/NG/MSW Industrial price 44/44 zero). Mechanism: the Exp/Ln
  price-elasticity shells evaluate `Ln(0)` → undefined or garbage, so
  fuel-switching response is silently priced at zero. (Same class hits
  industry's referenced prices.)"* — is the mechanism that renders your 643
  unfitted regression shells (below) meaningless even once fitted.
  **Cross-tree: these prices live in the Resources tree, owned by the
  fossil/central team.** Flag them there.

### 🟡 YELLOW — placeholder/template values silently shaping results

**Industry** (verbatim from the master audit):

- **"Fill in historical data here" stubs** — `0 * Key\Macroeconomic\
  Manufacturing Fraction…? Fill in historical data here` (214 rows) —
  zero-valued FEI awaiting data; plus 643 unfitted regression shells
  (coefficients = 1) and 528 `?placeholder` CCS sequestration ramps, all
  live in the 4 scenarios.

Broken out, so your team can divide the work:

| Item | Rows (4-scenario scope) | What it is | What we need |
|---|---|---|---|
| `? Fill in historical data here` stubs | 214 | FEI authored as `0 × Manufacturing Fraction` awaiting real historical FEC | the historical FEC per subsector/fuel |
| Unfitted Exp/Ln regression shells | 643 | `Exp(1*Ln(price)+1*Ln(GDP driver)+1)` — every coefficient still the placeholder `1` | fitted coefficients per subsector/fuel, or a decision to drop the econometric method |
| `?placeholder` CCS Sequestered-CO2 ramps | 528 | negative loading `-<factor>*Interp(2030,0.8,2045,0.9,2055,0.95) ?placeholder` (80→95 % capture) | confirm or replace the capture-rate trajectories |

- **Demand Cost = 0 boilerplate.** 28,800 rows of the `Demand Cost`
  variable are the constant `0` across every category and technology
  branch — the same information-free boilerplate the audit flags in every
  sector. If industry demand should carry a cost, this is the empty slot;
  today it carries nothing.

### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

The master audit's GREEN list names transport, residential and resources
items only — **no industry-specific GREEN entry**. The nearest industry
relatives (all benign, listed here so you don't chase them):

- `RefHH = 1` and `Demand Cost = 0` boilerplate on every branch — dead
  plumbing, carries no information (Demand Cost is also flagged 🟡 above as
  an *empty-but-fillable* slot; as-is it is harmless).
- The CA-only `UnscaledFuelShare` helper on the Historical fuels — present
  for parity with the commercial sector but **nothing in industry's
  1,008,012 expressions references it** (dead machinery, not a defect).
- Base Template and Timor Leste rows throughout — template-grade defaults;
  Timor Leste is disabled in the calc.

---

## Highest-leverage fixes for your team (if triaging)

Ordered by impact-per-effort on the industry results specifically:

1. **Re-tag the Cement Clinker Heat FEI `Bad Unit` (A8, 960 rows).** A
   corrupted unit on a core intensity variable in every scenario — a
   confirmed defect with a single correct answer once you tell us the
   intended unit.
2. **Fill the 214 "Fill in historical data here" FEI stubs (🟡).** These
   are zero right now, so those subsector/fuel intensities contribute
   nothing to demand — the single biggest block of missing industry data.
3. **Fit or retire the 643 regression shells (🟡)** — and note they are
   downstream of the **upstream zero-consumer-price** problem (🔴/Resources
   cross-tree): fitting them is wasted effort until the fossil/central team
   populates the Resources consumer prices your `Ln()` terms read.
4. **Confirm or replace the 528 CCS capture-rate ramps (🟡)** — they are
   `?placeholder` today and directly set the sequestered-CO2 credit in RAS
   and Carbon Neutrality.
5. **Repair or remove the `!Missing Branch`/`Bad Scenario [2]`
   EI-reduction template (A8, 159 rows).** Likely inert, but it is a
   dangling-reference defect that should not ship; tell us if it was meant
   to carry a real BAU-reduction number.

**Cross-tree reminder:** two things your formulas depend on are NOT owned
by the industry team — the **zero Resources consumer prices** (fossil/
central) and the **`Key\Macroeconomic\Real GDP Industry`** activity driver.
If the industry results look wrong and none of the items above explain it,
the cause may be upstream in those two trees. Flag them to the owning teams
rather than editing around them.

Questions → yudiandra.y@gmail.com.
