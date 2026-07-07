# Power Audit: Result observations (slides 9–20)

## UPDATE 2026-07-07 — status after your cleaned sendback (the inject payload)

Your consolidated sendback (`power_sendback_20260707.zip`, reconciled against
the v0.69 modeller delta) was cleaned into a 9,421-row inject payload — the
row-by-row cleaning record is `CLEANING_NOTES_20260707.md` in this package,
including the three Malaysia RAS `Maximum Capacity` rows where the LEAP team's
arbitration keeps your IRENA resource-potential caps over the modeller's
freeze-at-existing-fleet expressions (your divergence register §4 — this is
the answer it asked for). Checked against the audit items above and below:

| Audit item | Status after inject |
|---|---|
| T1 free-build `_MY*` generators (costs, efficiency, build limits, caps) | **SOLVED** — verified row-by-row; one exception below (Capacity Credit) |
| Slide 18: Malaysia Gas Turbine no-ceiling | **SOLVED** (RAS cap = existing fleet `Exogenous Capacity[MW]`, real costs, 1,400 MW/yr addition limit on `Gas Turbine_MYPE`, base-branch addition limit 0) |
| SOLAR-MY: 94 GW solar built free, then curtailed | **SOLVED** (real capital cost `Interp(2023, 960, 2030, 670, 2050, 480)` thousand USD/MW) |
| BLD-RATE: lumpy storage builds | **SOLVED for storage** (Thailand 2,000 / Vietnam 4,000 MW/yr addition limits). Vietnam's 2025 "spike" turned out to be your own authored PDP8 build (Lithium Ion 10,460 + Pumped Hydro 4,370 MW = the exact 14.8 GW in the results) — intended input, not a bug |
| Capacity Credit = 100 | **NOT solved** — the sendback carries no Capacity Credit rows (verified: 0 rows) |
| T2 `Bad Scenario [2]` refs (14 live) | **NOT solved** → folded into `NOTE_TO_POWER_TEAM_ENDOGENOUS_20260707.md` (in this package) — re-author them in the same endogenous pass |
| CF-01: wind runs baseload | **NOT solved** — no wind availability shipped (the payload's only `Maximum Availability` rows are `Gas Turbine_MYPE`, Lithium Ion Batteries, Pumped Hydro) |
| T6/T7/T8 + import cost (transmission capital, Wind Offshore availability 44, IDN/SG losses = 0, flat 100 import price) | **NOT solved** — parked PENDING per LEAP-team call; carry to the next power cycle |
| Nuclear fuel free + uncapped; Brunei biomass 8,773 TWh | **Not power's tree** — these live on `Resources\` branches → routed to the fossil / bioenergy teams |

Of the five highest-leverage input fixes listed at the end of this document:
**#1 lands with this inject** (minus the capacity-credit component), **#2 is
yours** via the endogenous note, **#3 mostly lands**, **#4 and #5 stay
pending** per the LEAP-team call.

### Anomaly pass — 7 items for your eyes (2026-07-07)

From the payload + live-model history check (every `Interp` series evaluated
year-by-year; real-world booms like Vietnam solar 2018–21 and Indonesia coal
ramps check out):

1. **Thailand Large Hydro: +4,451 MW in 2019, −4,450 MW in 2023** —
   symmetric appear/disappear, classic bookkeeping-error signature.
2. **Thailand fleets vanishing to 0 mid-history**: Biomass Other −2,120 MW
   (2020), Pumped Hydro −1,000 MW (2023 — Lam Ta Khong still operates in
   reality), Waste −658 MW (2023).
3. **Myanmar Gas Engine −822 MW → 0 (2020)**; `Biomass Other_MYPE` 852→32 MW
   (2010); `Biomass Other_IDSA` 1→1,531 MW (2018) — step artifacts worth a
   source check.
4. **Identical retirement series copy-pasted across sibling nodes**: all four
   `Gas Turbine_ID*` retire the same absolute series (601→62 MW each —
   national total ×4?); `Coal Subcritical_MYPE` ≡ `_MYSR` (both 210→1,474 MW
   at 2030). If national totals were duplicated per node instead of split,
   retirements double/quadruple count.
5. **Result-spike mystery solved**: Vietnam's "14.8 GW storage in 2025"
   result = exactly the authored additions (PDP8 policy-year build) —
   input-driven, not solver free-build.
6. **`Wind Onshore_MY*` locked at zero build in RAS** (your Maximum Capacity
   Addition = 0 on all 3 nodes + fleet 0): no Malaysian onshore wind can ever
   be built. Plausibly intended (poor resource) — please confirm.
7. **Capacity Credit = 100 is not reshipped** (no Capacity Credit rows in the
   sendback) — the T1/CF-01 capacity-credit component stays open.

Everything below this line is the original 2026-07-07 observation set the
table above refers to.

---

## Data tasks (your side) for the expanded audit

Data the expanded audit needs, and where it already sits in the current pack. The five new flags are all derivable from data already present; the genuinely new items are the transformation "total potential" (D2) and the optional fidelity inputs (D5, D6, D7).

| # | Data item | Needed by | Status in current pack |
|---|---|---|---|
| D1 | Transformation inputs per technology branch: MaxCapacity, ResidualCapacity (`04`); MinimumUtilization, AvailabilityFactor (`20`); efficiency / activity ratio (`18`); emission factor (`17`) | UI U3 | present; confirm completeness for every branch |
| D2 | Total potential / max deployable per technology and region, if distinct from MaxCapacity | UI U3 | not in the files read; supply, or confirm it equals MaxCapacity (see question) |
| D3 | Build rate (CapacityAdded by technology and year) | BLD-RATE | present (`01`) |
| D4 | Capacity by fuel family and year | RE-DILUTE | present (`01`) |
| D5 | Retirement series (CapacityRetired), plus the authored retirement schedule if you want a result-vs-input fidelity check | RET-COV | result present (`01`); input schedule not in the files read |
| D6 | Vintage Added/Retired data to test whether PH 2040 and TH/VNM blocks are bookkeeping | RET-COV, BLD-RATE cause | REC-01 exists; confirm it covers these cases |
| D7 | Timeslice dispatch, extra years beyond 2030 / 2040 / 2050 / 2060 if you want the inter-year shape comparison | TS-2030-MY | 2030 present (`02`); more years optional |
| D8 | Solar capacity and generation by year | SOLAR-MY | present (`01`) |

---

**Framing.** The task is to make the audit JSON honest to the model result. No model input is changed here. For each observation the question is: (a) does the dashboard show the model output faithfully, and (b) which features of the model output the audit should surface. All numbers below are computed from the RAS result files (capacity/generation `01`, timeslice `02`, bounds `04`, availability/min-utilisation `20`); the arithmetic is shown. A flag here describes what the model produced and is surfaced for review; it is not a claim that the model is faulty. The result-side sections come first; an input-side root-cause section (from the LEAP canon) is added at the end, mapping each observation to what should be changed in the model input.

## Summary

| Slide | Observation | Overlap with current audit | Verdict |
|---|---|---|---|
| 9, 12, 14 | RE share falling (LA, MY, PH, TH) | POL-03, EMI-06, EMI-07 | faithful; flag the dilution mechanism (new) |
| 10 | LA retires nothing after 2016 | none | faithful; flag retirement-coverage gap (new) |
| 11 | PH capacity dip 2040 | REC-01 candidate | faithful; 19 GW wind-offshore single-year retire (new) |
| 13 | TH storage spike in one year | none | faithful; flag lumpy build, no build-rate limit (new) |
| 15 | TH, ID net importers 2060 | F-09, F-10, F-01, F-03 | covered; cross-reference only |
| 16 | VNM wind/storage build spike | CF-03, CAP-04 | faithful; same build-rate flag (new) |
| 17 | ID unmet load vs new plant | LOL-1, F-01 | covered; cross-reference only |
| 18 | MY Gas Turbine ceiling | COST-01, CAP-02 | covered; input is Unlimited (see input-side section) |
| 19 | MY 2030 dispatch drop | none | faithful; flag 2030 timeslice shape (new) |
| 20 | MY solar barely used | CF-01 (wind side) | faithful; solar curtailed, strong observation (new) |

## Cross-cutting pattern

In Laos, Malaysia, Philippines and Thailand the RE *share* falls or stalls because gas capacity grows faster than renewable capacity, and in Malaysia solar is built but not dispatched while wind and gas run flat. The model expands fossil capacity alongside renewables rather than displacing it, consistent with renewables entering as additions to the mix (Hagens, 2020). The flags below describe this honestly through the model's own output; none of them propose changing the input.

---

## RE-share decline: slides 9, 12, 14

RE capacity share = renewable installed capacity ÷ total installed capacity (Unmet Load excluded). Peak-to-end and the dominant capacity changes:

| Country | Peak | End (2060) | Drop | Largest capacity changes peak→end (GW) |
|---|---|---|---|---|
| Laos | 100% (2005) | 55% | 45 pp | Hydro +19.7, **Gas +16.0**, **Coal +4.3**, Solar +2.0 |
| Malaysia | 20% (2039) | 13% | 7 pp | **Gas +89.8**, Solar +76.2, Wind +9.6 |
| Philippines | 71% (2036) | 61% | 10 pp | **Gas +66.7**, Wind +40.3, Storage +20.7, Solar +17.4 |
| Thailand | 58% (2054) | 57% | 1 pp | **Gas +24.8**, Solar +14.0, Storage +9.3 |

The share falls because the fossil term grows faster than the renewable term, not because renewable capacity shrinks. Two transients sit on top of the trend:

- **Philippines 2040 dip** (slide 11): total capacity 93.6 GW (2039) → 80.2 GW (2040) → 106.2 GW (2041). The 2040 retirement is **Wind Offshore 19.0 GW** in a single year, with no Philippine retirements after 2040.
- **Thailand 2038–2040 dip** (slide 14): share 38.5% (2037) → 36.1% (2039), then recovery. Over 2037→2040 gas adds 12.4 GW while solar adds 2.8 GW; renewables catch up after 2041 (RE capacity 50.6 → 77.2 GW by 2042).

The **Laos** case is the sharpest: a fleet that is 100% hydro in 2005 takes on 16.0 GW gas and 4.3 GW coal by 2060. A hydro-rich system building this much thermal is worth flagging on its own.

**Audit action.** New flag describing the dilution per country (RE capacity rising, gas rising faster). The dashboard's RE-share metric already shows it; the flag makes the mechanism explicit. Overlaps: POL-03 (MY target miss), EMI-06 (TH), EMI-07 (PH).

## Retirement fidelity: slide 10 (and 11)

Years in which the result records `CapacityRetired > 0`, per country:

| Country | Retire-years | Span | Total retired (GW) |
|---|---|---|---|
| Indonesia | 38 | 2006–2060 | 1661.9 |
| Malaysia | 32 | 2006–2060 | 129.5 |
| Thailand | 31 | 2006–2060 | 108.8 |
| Vietnam | 27 | 2006–2060 | 17.8 |
| Myanmar | 22 | 2006–2060 | 16.5 |
| Singapore | 15 | 2006–2059 | 18.4 |
| Philippines | 22 | 2006–**2040** | 26.5 |
| Cambodia | 19 | 2009–**2040** | 1.2 |
| Brunei | 10 | 2006–2040 | ~0.0 |
| **Laos** | **1** | **2016 only** | **~0.0** |

Two observations in the result:

1. **Laos retires essentially nothing** across 2005–2060 (one 2016 entry, rounding to zero GW). Brunei is the same.
2. **Cambodia, Philippines and Brunei stop retiring after 2040**, while Indonesia, Malaysia, Thailand, Myanmar, Vietnam and Singapore run retirements out to 2059–2060.

You said the retirement schedule is authored, so the check is whether the result follows it. The result shows no retirement for Laos and a 2040 cutoff for three countries. That is what the audit surfaces (no claim about the input).

**Audit action.** New flag: retirement-coverage gaps (Laos and Brunei near-zero; CB/PH/BN cutoff at 2040). Fold the Philippine 19 GW wind-offshore single-year retirement (slide 11) into the same flag, or keep it separate. Overlap: REC-01 is a candidate mechanism (vintage Added/Retired bookkeeping) and should be checked against it.

## Single-year build blocks: slides 13, 16

The model adds large capacity in single years because no build-rate limit is present in the inputs. This is not something we cap here; we flag the magnitude so a reviewer can judge plausibility.

| Country | Family | Largest single-year additions (GW) |
|---|---|---|
| Thailand | Storage | 19.3 (2054), 18.3 (2053), 17.4 (2044), 16.5 (2043) |
| Vietnam | Wind | 17.5 (2030), 12.2 (2042), 10.0 (2041) |
| Vietnam | Storage | 14.8 (2025), 8.0 (2046–2048) |

Vietnam's 2025 storage (14.8 GW) and 2030 wind (17.5 GW) line up with policy-target years. Thailand's storage arrives in repeated ~16–19 GW annual blocks late in the horizon.

**Audit action.** New flag: lumpy single-year additions (≥ a threshold to be set) with no build-rate constraint in the model. Overlaps: CF-03 (VN/ID firm capacity built but never dispatched), CAP-04 (VN un-noded gas 160–164 GW).

## Net importers in 2060: slide 15

Thailand and Indonesia are net electricity importers in 2060 (net-positions view). This is already covered: F-09 (Thailand is a pure net importer, zero gross exports), F-10 (import-dependent set), and for Indonesia F-01/F-03 (bound by local firm capacity and the Sumatra interconnector). Indonesia importing in 2060 is the trade-side face of LOL-1.

**Audit action.** Cross-reference only; no new flag.

## Indonesia unmet load: slide 17

Covered by LOL-1 (loss-of-load reaches 15.8% by 2060, dominated by local firm-capacity exhaustion) and F-01 (the unmet load is bound by local firm capacity, not by interconnection). The "why is no new plant built" question is answered by LOL-1: firm capacity at the binding nodes is exhausted and cannot expand there, so load goes unserved rather than imported.

**Audit action.** Cross-reference only. The MaxCapacity overlay already in the dashboard supports this; optionally surface which IDEast firm technologies are pinned.

## Malaysia Gas Turbine ceiling: slide 18

The MaxCapacity bound for Malaysia Gas Turbine in `04` is a single value, **1000 GW**, flat across all 36 years, set at national level. That is effectively no ceiling, and the technology overbuilds to ~190 GW (flag COST-01); the demand driver is CAP-02 (Malaysia demand roughly doubles 2027→2028). There is no 20 GW value anywhere in `04`; per your instruction the "20k" input question is set aside.

**Audit action.** Flag the ceiling as effectively absent (1000 GW). What to do about it is post-audit. Overlaps: COST-01, CAP-02.

**Input canon (v0.67).** The LEAP input carries no 1000 GW value: Gas Turbine_MYPE reads Maximum Capacity = Unlimited and Maximum Capacity Addition = Unlimited, both on an un-overwritten ALL-region template copy, together with Capital / Fixed / Variable OM = 0, Capacity Credit = 100 and Process Efficiency = 100 (verified in the expression CSV). The unbounded build is the annual Maximum Capacity Addition = Unlimited. See the input-side section for the full root-cause map.

## Malaysia 2030 dispatch drop: slide 19

Per-timeslice total dispatched power (sum of technologies), 48 slices:

| Year | Min (GW) | Max (GW) | Mean (GW) | Slices below 60% of max |
|---|---|---|---|---|
| 2030 | 49.5 | 122.6 | 116.4 | 4 (orders 13, 24, 28, 30) |
| 2060 | 183.4 | 229.7 | 217.9 | 0 |

In the low 2030 slices the Gas Turbine output falls (102 → 30 GW) while wind, combined-cycle and coal stay flat; no Unmet Load is present. The 2060 shape is smooth. So 2030 carries four low-load timeslices that 2060 does not, and gas throttles to follow them.

**Audit action.** New flag: 2030 has low-load timeslices absent in 2060 (possible inter-year demand-shape difference). Reported as an observation; no claim that it is an error.

## Malaysia solar barely used: slide 20

Capacity, generation and implied capacity factor (CF = generation ÷ (capacity × 8760 h)):

| Family | 2030 cap (GW) | 2030 gen (GWh) | 2030 CF | 2060 cap (GW) | 2060 gen (GWh) | 2060 CF |
|---|---|---|---|---|---|---|
| Solar | 0.0 | 0 | – | 94.2 | 4 797 | **0.006** |
| Wind | 11.4 | 96 255 | 0.97 | 41.4 | 315 513 | 0.87 |
| Gas | 116.5 | 876 590 | 0.86 | 209.8 | 1 563 683 | 0.85 |
| Coal | 14.2 | 37 079 | 0.30 | 15.6 | 17 591 | 0.13 |

A 94.2 GW solar fleet generates 4 797 GWh in 2060, a capacity factor of 0.6%, i.e. it runs at well under 1% of nameplate. In the same year and system wind runs at 0.87 and gas at 0.85. Wind running near baseload (CF 0.87–0.97) is the no-availability-factor problem already flagged for Sarawak wind (CF-01), here visible for Malaysian wind in aggregate. Solar sits last in the dispatch and is effectively not used.

**Audit action.** New flag: Malaysia solar 94 GW at CF 0.006 while wind (no availability profile) and gas run flat. Links to CF-01 (wind side). Strong, faithful observation.

---

## Proposed new flags (to add to the JSON)

| ID (proposed) | Scope | One-line |
|---|---|---|
| RE-DILUTE | LA, MY, PH, TH | RE share falls as gas capacity grows faster than renewables (LA −45, PH −10, MY −7, TH −1 pp) |
| RET-COV | LA, BN, KH, PH | retirement coverage gaps: Laos/Brunei ~0 GW; CB/PH/BN none after 2040; PH 19 GW offshore wind retires in 2040 |
| BLD-RATE | TH, VNM | lumpy single-year builds, no build-rate limit (TH storage ≤19.3 GW/yr; VNM wind 17.5 GW 2030, storage 14.8 GW 2025) |
| TS-2030-MY | Malaysia | 2030 has 4 low-load timeslices absent in 2060; gas throttles 102→30 GW |
| SOLAR-MY | Malaysia | 94 GW solar generates 4 797 GWh (CF 0.006), effectively curtailed; wind/gas run baseload |

Cross-references (already covered, no new flag): slide 15 → F-09/F-10/F-01/F-03; slide 17 → LOL-1/F-01; slide 18 → COST-01/CAP-02.

## Open question for you

The Philippine 2040 dip and the Thailand/Vietnam build blocks could be genuine end-of-life and policy-driven builds, or vintage bookkeeping (REC-01). Do you want me to test them against REC-01 before these become flags, or flag them as observed and leave the cause open?

## Input-side root causes and fixes needed (LEAP canon v0.67, 2026-07-04)

The sections above are the result side (what the model produced). The LEAP input canon (`aeo9_v0.67_w_results`, exported 2026-07-02 to -04) and its power-slice anomaly audit now let us trace the input causes. Values below are read from `current_expressions_transformation_slice_4scenarios.csv` and the resources/keys expression files, or taken from the anomaly-audit doc's verifier-confirmed counts. This section names what should be changed; it proposes no numeric values. Every checked item is still open in the canon (no value fix has landed).

### Root causes behind our observations

| Result observation | Input root cause (verified) | What should be changed | Grade |
|---|---|---|---|
| COST-01 / MY Gas Turbine overbuild / "1000 GW effectively no ceiling" (slide 18) | Gas Turbine_MYPE, RAS, un-overwritten ALL-region template: Capital / Fixed / Variable OM = 0; Maximum Capacity = Unlimited; Maximum Capacity Addition = Unlimited; Capacity Credit = 100; Process Efficiency = 100; Maximum Availability = 100 | author real plant costs, a finite Maximum Capacity Addition, a realistic Capacity Credit and Process Efficiency, or retire the inheritance copy so Malaysia's real branch governs | 🔴 T1 |
| CF-01 / MYSR wind runs baseload | Wind Onshore_MYSR, RAS: Maximum Availability = 100 (LEAP default), Minimum Utilization = 0, Capital Cost = 0, Capacity Credit = 100 | author a real wind availability profile and cost; this is the default availability, not the must-run trap (T3, verified inert) | 🔴/🟡 |
| SOLAR-MY / MY solar built but curtailed (slide 20) | Solar PV_MY*, RAS: Capital Cost = 0 (free build); Maximum Availability follows a real solar shape | author a real Solar PV_MY* capital cost so the free over-build stops; the low CF is curtailment of the over-build, not an availability error | 🔴 T1 |
| Net importers / trade looks cheap (slides 15, 18) | Electricity Import Cost = 100 flat (all 12 regions); interconnector Variable OM = 0 ("Included in the FOM"); ASEAN-grid transmission Capital Cost = 315 placeholder (6 lines) | replace the flat import price with per-region, per-scenario prices; confirm the interconnector cost convention; replace the placeholder transmission capital costs | 🟡 T6 |
| BLD-RATE / lumpy builds | Maximum Capacity Addition = Unlimited on the free-build techs; `Key\Capacity Additions Multiplier` per-tech levers | set finite annual addition caps; review the multipliers and their end-year twins | consequence |
| LOL-1 / DH-01 Indonesia unmet | not among the graded input anomalies; nearest context is Indonesia T&D Losses = 0 (below) | inspect the IDEast firm-plant caps separately | n/a |

### Sharper source than the result data gave

- **MY gas-turbine overbuild** was read as a 1000 GW ceiling in the result export. The input carries no 1000 GW value: both Maximum Capacity and Maximum Capacity Addition read Unlimited on the un-overwritten Gas Turbine_MYPE template copy. The unbounded build comes from the annual Maximum Capacity Addition = Unlimited; the understated running cost from Process Efficiency = 100 (a lossless gas turbine, so its fuel cost is understated by roughly a factor of three). The 1000 GW in `04` and the Unlimited in the canon need reconciling against what the solver used.
- **MYSR wind baseload** is the default Maximum Availability = 100 with Minimum Utilization = 0, not the must-run trap. The must-run trap (T3) is authored on variable-renewable branches, but the verifier confirms every trap branch has zero capacity, so it is inert.
- **MY solar curtailment** is over-build of a free fleet (Capital Cost = 0), not a broken availability profile.

### New observations from the canon (not in the result-side list)

| Finding | Verified where | Why it matters | Grade |
|---|---|---|---|
| Indonesia and Singapore Electricity T&D Losses = 0 (all other countries 4–27%) | expression CSV | understates the generation and installed capacity Indonesia and Singapore need in every scenario | 🟡 T8 |
| Electricity Import Cost = 100 flat, all 12 regions | expression CSV | the only price on cross-border power; sets the build-vs-import choice once the grid is enabled | 🟡 |
| Interconnector Variable OM = 0 on all 21 lines, comment "Included in the FOM" | expression CSV | biases the LP toward trade; the comment says it is intentional, so confirm rather than assume a defect | note |
| `ScenarioValue(Bad Scenario [2])` dangling reference in Endogenous Capacity, AMS Target only, 20 rows | audit doc | the endogenous build ramps resolve against a scenario that no longer exists; either errors the AMS Target calc or zeroes the ramps | 🔴/🟡 T2 |
| Wind Offshore Maximum Availability = 44 placeholder, all 12 regions | audit doc | a uniform placeholder capacity factor shaping offshore-wind output and economics | 🟡 T7 |
| ASEAN-grid transmission Capital Cost = 315 placeholder, 6 lines | audit doc | a guessed transmission investment cost driving RAS interconnector build economics | 🟡 T6 |
| Unlimited renewable potential caps on Biomass / Geothermal / Large Hydro / MSW, 37 rows | audit doc | un-capped renewable supply in the RAS scenario whose RE targets those caps should bind | 🟡 |
| Nuclear Maximum Production = Unlimited at $0 Production Cost | audit doc | a cap-open, cost-zero fuel route the LP treats as free | 🔴 |
| Brunei Biomass Maximum Production = 8,773 TWh | audit doc | roughly 1,600× the sibling median, a near-certain unit slip that drags the Brunei Bagasse and Wood caps | 🔴 |

The T&D-loss, import-cost, and interconnector-VOM rows were read directly from the expression CSVs; the rest are from the anomaly-audit doc's verifier-confirmed counts.

### Highest-leverage input fixes (from the audit doc)

1. The six free-build `_MY*` generators (T1), the single largest distortion in the RAS solution.
2. The `Bad Scenario [2]` dangling reference (T2), which decides whether AMS Target is calculable.
3. Align the `_MYPE` / `_MYSB` / `_MYSR` sibling variants (T4); T1 is a symptom.
4. The confessed placeholders: transmission capital cost 315 (T6) and Wind Offshore availability 44 (T7).
5. Non-zero T&D losses for Indonesia and Singapore (T8).

Leave alone (verified benign): the inert must-run trap (T3), the benign Maximum Production = Unlimited upper-bound sentinel (T9), the inert Renewable Target knob (T10), and the cosmetic `_x000D_` comment artifacts (T11).

## Reference

Hagens, N. J. (2020). Economics for the future: Beyond the superorganism. *Ecological Economics, 169*, 106520.

Power canon handover (2026-07-04). LEAP `aeo9_v0.67_w_results` structure exports and power-slice anomaly audit (`ANOMALY_AUDIT_POWER_20260704.md`; `current_expressions_transformation_slice_4scenarios.csv`).
