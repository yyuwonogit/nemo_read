# Bioenergy team — task update (2026-07-13)

## What happened

During the v0.71 run a **hard edit was made directly in the LEAP engine** to
clear an infeasibility (insufficient Biomass supply in Myanmar):

> In **Base Template**, scenario **RAS**:
> `Resources\Primary\Biomass : Maximum Imports = Max(5000000, Maximum Production[GJ])`
> (replaces the previous `Max(5000000, Maximum Production[Tonne]/1000)`)

The record of this edit is `biomass_max_imports_engine_edit.csv` in this
package. It is the current engine state — treat it as the baseline for this
cell until you supersede it.

## Your tasks

1. **Adopt or supersede the edit — your call, but explicitly.** The edit is a
   region-wide blanket (Base Template inherits to all 12 regions) made to
   unblock one region (Myanmar). If you keep it, fold it into your canonical.
   If you replace it, send a delta.

2. **Check the unit basis (flagged, not verified by us).** The edit changed
   the reference from `Maximum Production[Tonne]/1000` to
   `Maximum Production[GJ]`. Confirm: (a) what unit `Maximum Imports` itself
   carries on this branch, (b) that `5000000` and `Maximum Production[GJ]`
   are on the same basis inside the Max(). If the old `/1000` was a real
   unit conversion, the new form may be off by orders of magnitude in one
   direction — please verify against your supply numbers.

3. **RUN THE SUPPLY-ADEQUACY SWEEP (the main task).** Myanmar biomass is one
   instance of a general class: a region with forced demand for a feedstock
   and insufficient local supply + import ceiling. Rather than fixing these
   one at a time as calc failures, sweep ALL bio feedstocks × all 10 regions
   × milestone years: forced demand (incl. blend-mandate pull) vs
   max supply (Maximum Production + Maximum Imports + trade routes). For
   every (region, feedstock, year) where demand can exceed supply, author a
   deliberate regional cap/cost — then **replace the Base-Template blanket
   with per-region values** so one region's fix doesn't silently re-route
   supply through every other region (the known "free-supply region"
   failure mode).

4. **Authoring rule going forward: reference first, numeric last** in
   Max()/Min() — `Max(Maximum Production[GJ], 5000000)`. A numeric first
   argument can be parsed by LEAP as a YEAR (this exact class cost the
   power team a calc cycle). The current engine cell survives as-is; flip
   the order whenever you next touch it.

## Why this matters

Import ceilings are supply-side load-bearing: too tight → infeasible calc
(what happened); too loose via a blanket → the optimizer quietly sources
"free" biomass anywhere, corrupting the supply story everywhere. Deliberate
per-region values are the only stable state.
