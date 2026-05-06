# LEAP-team Power Issues — v0.35 → v0.36 Handover

**Date received: 2026-05-05**
**Branch: `20260505_Power_YY`**
**LEAP model versions: v0.35 (broken) → v0.36 (interim workaround applied)**

---

## Source files

- [`Power/Raw/joined_ATS.csv`](../Raw/joined_ATS.csv) — ATS scenario results
- [`Power/Raw/joined_BAS.csv`](../Raw/joined_BAS.csv) — BAS scenario results

---

## Reported issues — INDONESIA

**Double-counting on each node-specific power plant.** Indonesia
runs a 4-grid split (IDJW, IDKA, IDSA, IDEast) but the affected plant
families ALSO have non-node-specific (root-level Indonesia) versions
that are summed alongside the node-specific ones — double-counting
the same physical capacity.

**Affected plant families (7):**
- Biomass
- Biogas
- Coal SubC
- Diesel
- NatGas CC (Combined Cycle)
- Gas Turbine
- Gas Engine

**Two remediation options proposed by author:**
1. **Option A** — distinguish each node in projection AND backcast to
   historical (per-node from day 0).
2. **Option B** — keep non-node-specific plants available only in
   historical, set to zero in projection (so only node-specific plants
   contribute from 2025+).

---

## Reported issues — MALAYSIA

1. **Overestimated projection of Solar in Peninsular** — check the
   data to confirm it represents Peninsular Solar properly.
2. **Proper distribution of NatGas CC across the 3 Malaysian nodes**
   (Peninsular, Sabah, Sarawak) — current distribution may not match
   real grid layout.
3. **Existing Capacity + Historical Production expressions** — review
   for both above issues.

---

## LEAP team's v0.35 → v0.36 workaround

> "I downloaded v.0.35 and tried to calculate the BAS and ATS scenarios.
> LEAP returned errors because in some years, several Centralized
> Electricity Generation processes in Indonesia had Historical
> Production but no Exogenous Capacity. To move forward, I updated
> these processes' Existing Capacity, recording what I did in the
> change log. I made as minimal an intervention as I could to get the
> model to run, which ended up being the following:
>
> - In **Current Accounts**, the processes' Interp expressions for
>   Existing Capacity reduced their capacity to 0 in 2022. I removed
>   this part of the expressions so the 2021 capacity would persist
>   in 2022-2024 (when there was Historical Production but no
>   Exogenous Capacity).
>
> - To ensure the processes had no capacity in projection scenarios
>   (consistent with their original Interp expressions in Current
>   Accounts), I set their expressions for Existing Capacity in BAS
>   to 0.
>
> This allowed the model to calculate the BAS and ATS in all years.
> However, the results may not be what you intend. Much of the
> Existing Capacity in Indonesia goes offline in 2025, so electricity
> generation drops sharply. Probably you'll want to revisit the
> Existing Capacity for these processes in Current Accounts and BAS
> to get the simulation you're looking for.
>
> With my changes, the model is now at v.0.36. It's checked in and
> ready for your use tomorrow."

**Implication:** v0.36 currently has Indonesia capacity dropping to 0
in 2025 for the affected processes. We need to author proper Existing
Capacity values for both Current Accounts (historical) and BAS
(projection) — Option A or B above will determine HOW.

---

## Anomalies surfaced from author's own digest of `joined_*.csv`

1. **Thailand Module Energy Generation = −5.2 × 10¹⁷ GJ in 2025** —
   single corrupt row at the parent `Centralized Electricity
   Generation` Module level (Process sum is positive). Likely a bad
   coefficient on a Thailand Module-level expression.
2. **Module ≠ sum-of-Processes** for any AMS — the parent Module
   value isn't a roll-up of children. May be reading from a different
   formula (e.g. demand-side input) or a parallel branch.
3. **Indonesia Module Energy Generation = 401 × 10⁹ GJ ≈ 111,000 TWh**
   — physically impossible (Indonesia's actual 2024 demand: ~310 TWh).
   Indicates either Indonesia regional rows leaking up multiple
   levels, or the double-counting cited above magnified at Module
   level.
4. **Cross-AMS attribution bug**: Thailand result rows include
   branches with `_IDSA` suffix (Indonesia Sumatra grid). Either AMS
   label is wrong on those rows or Indonesia regional branches are
   leaking into Thailand's roll-up.
5. **Coal Supercritical = ~1.81 × 10¹⁰ GJ in BOTH ATS and BAS 2050**
   — looks indistinguishable on the headline coal fuel; ATS may not
   be differentiating from BAS as intended.
