# To the power team — automatic plant additions ("Endogenous Capacity") need your decision (2026-07-07)

## The concern, in one paragraph

In Baseline and AMS Target, LEAP adds capacity **by itself** whenever the
system runs short — the "Endogenous Capacity" variable per plant says how
big a block LEAP may drop in, from which year. Today those standing
permissions include **subcritical coal and diesel with no end year** — so
after your scheduled additions run out, the model can keep filling any gap
with the dirtiest, least-efficient options indefinitely. Our policy
position (LEAP side): **no technically-worse plant should enter the system
after the scheduled additions**. The structure facts below are ours to
give; the values are yours to decide.

## What is authored right now (read from the live v0.69 model)

662 plant×country slots carry the variable; **127 are non-zero**. The ones
that clash with the no-bad-plants position:

| Plant | Where it can auto-enter (block size, MW) | End year |
|---|---|---|
| **Coal Subcritical** | Cambodia 200, Vietnam 200, Philippines 200, Thailand 100, Laos 100, Myanmar 150, Indonesia 150 on each of the 4 sub-grids, Malaysia 100 on _MYPE and _MYSR | **none — runs to 2060** |
| **Diesel** | Indonesia 64 on all 4 sub-grids, Vietnam 25, Cambodia 27, Philippines 10, Thailand 7, Singapore 7.13, Myanmar 4, Brunei 5, Malaysia 10 on all 3 sub-grids | none |
| **Fuel Oil** | Cambodia 10, Singapore 5 | none |
| Gas Turbine / Gas Engine (open cycle) | Indonesia 70 / 42 per sub-grid, Myanmar 100 / 140, Brunei 20, Singapore 14 | none |

(The rest of the 127 are gas-combined-cycle, CCS variants, hydro, solar,
wind, biomass — the "acceptable" end of the list.)

## The structure facts you need before deciding

1. **You cannot cap these plants in Baseline / AMS Target with Maximum
   Capacity** — that variable physically exists only in the seven
   optimization scenarios (Set up, RAS, CNZ, LCO backup, RE LTRM ×3). In
   Baseline/ATS the ONLY lever on automatic entry is the Endogenous
   Capacity expression itself.
2. **The AMS Target rows already use a central knob**: most healthy rows
   read `Step(<year>, 0, <later year>, <share> * Key\End_cap
   multip\Total_:Activity Level)` — a per-technology share times one
   central multiplier. Editing shares there re-shapes the whole
   auto-build mix in one place.
3. **A time-boxed permission is one expression**: e.g.
   `Step(2023, 200, 2035, 0)` allows the block until 2035 and nothing
   after. This is the natural way to say "coal may fill gaps only until
   the scheduled build-out is complete".
4. **14 of the AMS Target rows are broken today** and must be re-authored
   in any case: they reference a deleted scenario
   (`ScenarioValue(Bad Scenario [2])`) — Philippines (Coal Subcritical,
   Large Hydro, Geothermal Flash, Solar PV, Wind Onshore, Biomass Other),
   Thailand (Coal Subcritical, Coal Ultrasupercritical ± CCS), Vietnam
   (Solar PV, Wind Onshore, Large Hydro, Biomass Other), Indonesia
   (Biomass Gasification). Whatever you decide on the bad-plant question,
   these 14 need new expressions — one pass can fix both.

## What we ask of you

For each row in the coal/diesel/fuel-oil table above, decide one of:
- **keep** (with a written justification),
- **time-box** (`Step(<from>, <size>, <until>, 0)` — give us the until-year),
- **zero it** (no automatic entry; gaps then fall to gas/renewables or,
  if nothing can build, to Unmet Load, which is priced and visible).

And re-author the 14 broken rows while you're in there. Send the values
in the usual send-back format; we inject.
