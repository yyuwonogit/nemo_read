# Bioenergy handover — our rulings + one new ask

**From:** AEO-9 LEAP modelling / canon team · **To:** Bioenergy team · **Date:** 2026-07-21
**Re:** `bioenergy_biomass_cap_handover_20260721.zip` (89-row cap payload + 6 asks)
**Target area:** live `aeo9_v0.75+` · **Scenario set: BAS / ATS / RAS only.**

We have adjudicated every item in your bundle against canon. **Most of your
payload is inject-ready.** This note tells you what we accepted, what we
corrected, what we are doing ourselves, and the one thing we need back from you
before the inject.

## Contents

| File | Role |
|---|---|
| `RULINGS_20260721.md` | Item-by-item verdict on your 6 asks, 4 scenario questions, and 3 delivered fixes. |
| `ASK_blending_ramp_20260721.md` | **NEW ASK — the one thing we need from you.** Defensible per-country blend ramp. |
| `row_disposition_20260721.csv` | Per-row disposition of all 89 payload rows. |

## Bottom line on your payload

| | Rows | |
|---|---|---|
| **Inject now** | **79** | 70 refinery `Maximum Capacity` + 4 import-valve + 5 lite-panel caps. |
| **Hold** | **10** | `Cellulosic Rice Straw` — the branch does not exist yet. Our modelling lead creates it manually before inject. **Values accepted; do not resend.** |

**No payload reship is required.** Two adjustments are ours, not yours:
we tag the scenario column (it is empty on all 89 rows) and we scope
`Maximum Imports` to RAS.

## Three corrections to your framing

1. **"Add `Variable OM Cost` to 5 lite-panel processes"** — two of them
   (`Charcoal\All Biomass`, `Domestic Biogas\Anaerobic Digestion`) **already
   carry `Variable OM Cost`** in canon. They need *values*, not the variable.
   We will add the genuinely-missing variables ourselves.
2. **"Shortfalls become silent unbounded imports because imports are
   unpriced"** — `Import Cost` **is** authored on every bio branch in all
   scenarios (2020 USD/Metric Tonne). The two-family import design is
   intentional, not a defect. Details in `RULINGS`, ask 5.
3. **"Caps must be sized for BAS/ATS too or we risk infeasibility"** — the
   caps **bind in RAS only**. BAS and ATS are accounting scenarios; authoring
   caps there is cosmetic and carries **no infeasibility risk**. Do not spend
   effort sizing them.

## Structure is ours; content is yours

Three of your asks were requests for us to change branch structure. That is
our call and we are handling it — you do not need to do anything:

- **We create** `Rice Straw`, `Used Cooking Oil` (Resources leaves) and
  `Cellulosic Rice Straw` (process, mirroring the Cassava sibling).
- **We add** `Capital Cost` to all 5 lite-panel processes and
  `Variable OM Cost` to the 3 that genuinely lack it.
- **We scope** `Maximum Imports` to the optimisation scenario at inject time.

**You supply values only.** Please do not author branch paths, variables or
units into future payloads — send values against the paths we publish.

## One count to reconcile

Your README cites **61 blocked rows**; the CSV we received has **89 rows, of
which 10 are blocked**. We believe your 61 spans the wider S1/S2 payload rather
than this file. Confirm so we know nothing is sitting unshipped on your side.

## What we owe you (after the inject + solve, not before)

1. Demand export (per-AMS, per-branch, BAS+ATS+RAS) incl. Biomass/Wood, to 2060.
2. Fuel `EnergyContent` export (Palm, Coconut, Sugarcane, Cassava, **Corn**) —
   this settles your ask 1b **and** ask 8 in one delivery.
3. The free deficit check on Bagasse/Biomass `Maximum Imports = 0`.
4. Fresh RAS run + the true input expression set.

## What we need from you now

**One deliverable: the blend ramp.** See `ASK_blending_ramp_20260721.md`.
It is the only thing gating a defensible RAS biofuel result, and it is
squarely in your domain.
