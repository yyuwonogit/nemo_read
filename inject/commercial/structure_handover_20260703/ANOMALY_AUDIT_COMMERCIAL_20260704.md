# Commercial — Anomaly audit (your slice) — 2026-07-04

This file is the **commercial-buildings slice** of a model-wide anomaly
audit run over the live LEAP area `aeo9_v0.67_w_results` (the master
audit is `CANON_ANOMALY_AUDIT_20260704.md`, covering all six sectors —
transport, residential, resources, keys, commercial, industry). We have
pulled out **only the findings that touch branches your team owns or
authors** in `Demand\Commercial`, plus the upstream branches your
expressions merely *reference* (flagged as **cross-tree notes** — those
are owned by another team, but you should know they sit under you). Every
item keeps its original tags: **NEW** vs **KNOWN** (already logged in the
model anatomy hygiene ledger), **VERIFIED DEFECT** vs **SUSPICIOUS —
needs human judgment**, and — for the "empty but important" Part B — the
🔴/🟡/🟢 grade. Counts are rows across the four scenarios that matter
(**Current Accounts, Baseline Simulation, AMS Target Scenario, Regional
Aspiration Scenario**). These are the audit's findings, not new work
items — your job is to **judge each one and decide the fix**; you don't
need LEAP or our repo to do that. Where the master audit only names a
finding under another sector but your regressions depend on it, we say so
in a cross-tree note so you don't chase a fix that isn't yours to make.

---

## Part A — Incorrectly inputted (anomalies in authored values)

### A8. Dangling references / corrupted tokens

- **KNOWN · VERIFIED — commercial `!Missing Branch (ID=1687/825)`** on
  Historical Ethanol/Biodiesel FEI regression shells (Baseline). *72 rows.
  Commercial.*

  What this means for you: the `Final Energy Intensity` regression shells
  on `Demand\Commercial\Other Commercial\Historical\Ethanol` and
  `…\Historical\Biodiesel` (in Baseline Simulation) are of the form
  `Exp(1 * Ln(<fuel price>) + 1 * Ln(Key\Macroeconomic\Real GDP
  Service:Activity Level) + 1) * 1`, but the `<fuel price>` operand
  points at branches that no longer exist — LEAP renders them as
  `!Missing Branch (ID=1687)!` (Ethanol) and `!Missing Branch (ID=825)!`
  (Biodiesel). The `Ln()` of a dangling reference cannot evaluate, so
  these shells produce no usable Ethanol/Biodiesel commercial intensity.
  They need re-pointing to a real consumer-price series, or replacing
  with plain authored trajectories. (These are the same shells called
  out as issue 3 in your structure-handover README §7.3.)

> Note — the "coefficients must be determined via regression"
> placeholder-1 regression shells and the `? ACE temp value`
> template intensities described in your README §7.1–§7.2 are the
> substrate these A8 rows sit on, but the master audit logs only the
> dangling-reference token above as a distinct commercial Part-A
> defect. We have not manufactured separate audit findings for the
> unfitted-coefficient or temp-value placeholders — those remain the
> open data requests in your README, not audit-verified defects.

---

## Part B — Empty but important (graded)

### 🟡 YELLOW — placeholder/template values silently shaping results (wrong numbers, not broken mechanics)

- **Consumer prices ~95 % zero** on the branches demand regressions
  reference (1,130 of 1,188 cells; Bagasse/coals/NG/MSW Industrial price
  44/44 zero). **Mechanism:** the Exp/Ln price-elasticity shells evaluate
  `Ln(0)` → undefined or garbage, so fuel-switching response is silently
  priced at zero. (Same class hits industry's referenced prices.)
  *(graded 🟡 · Resources-owned — cross-tree.)*

  **CROSS-TREE NOTE:** these price branches live in the `Resources` tree
  and are **owned by the resources team, not commercial** — you don't
  author them. They matter to you because your Baseline `Historical`
  regression shells (the `Exp(1*Ln(<price>) + 1*Ln(GDP) + 1)` form,
  including the A8 Ethanol/Biodiesel rows) feed their `Commercial
  Consumer Price` into the `Ln()`. When that price resolves to zero,
  `Ln(0)` breaks the regression regardless of whether you fit the
  coefficients. So even after the A8 missing-branch tokens are
  re-pointed, the price series they point at must be non-zero for the
  regressions to mean anything. Raise this with the resources team; the
  fix is upstream of you.

---

## Highest-leverage for your team

1. **Re-point (or replace) the A8 `!Missing Branch (ID=1687/825)`
   Ethanol/Biodiesel regression shells** — the only VERIFIED authoring
   defect the audit pins on commercial. Decide between re-pointing to a
   real price series or dropping the regression form for plain
   trajectories (this is your README issue 3).
2. **Escalate the zero consumer-price series (🟡, cross-tree) to
   resources** — fixing your regression shells is wasted effort while
   the referenced prices `Ln(0)`. This is the gate on whether *any* of
   your Baseline `Historical` price/GDP regressions produce sane numbers.

---

## Cross-tree notes — defects/dependencies owned elsewhere

- **Referenced Resources consumer prices** (the `Ln(0)` 🟡 item above):
  the 12 `Resources\…:Commercial Consumer Price` branches your Baseline
  regressions read are **owned by the resources team**. Most currently
  resolve to zero; that's a resources-side fix, upstream of your
  regression shells.
- **Borrowed residential Key branches** (Kerosene-and-Candles lighting
  wiring): your `Demand\Commercial\Other Commercial\End Use
  Projection\Lighting\Other\Kerosene and Candles:Final Energy Intensity`
  is authored verbatim against residential machinery —
  `Key\Cal\Residential\Cook and Light Non Elec`,
  `Key\Net Zero Measures\Residential\Building Orientation\Lighting
  Energy Savings`, and `…\Building Orientation\Share_Households`. Those
  three Key branches are **owned by the residential / keys teams**, not
  commercial, even though your Lighting intensity depends on them. The
  master audit does not flag a defect on these specific borrowed
  branches; this note exists so you know the dependency is upstream and
  not yours to re-author (per your README §6, if you replace the
  kerosene-lighting assumption with real data this borrowed wiring can
  be retired — coordinate with those teams).
