# Power team — RAS v0.69 results + final cap corrections (2026-07-07)

## What happened, in one paragraph

Your 9,534-row sendback was cleaned to 9,337 rows, injected into `aeo9_v0.69`
(all 4 scenarios, readback-verified: 40 EXACT / 0 FAIL), and the **Regional
Aspiration Scenario now SOLVES**. Getting there required one correction
cycle: four of your absolute Maximum Capacity numbers collided with the
capacity-additions trajectories already in the area, and LEAP refused to
calculate. We fixed those four cells (details below — they are also in this
package as a 4-row CSV) and the run completed. This package holds the full
power-sector results of that successful run.

## Files in this package

| File | What it is |
|---|---|
| `capacity_by_region_tech_year_GW.csv` | Total installed capacity, every generation tech × region × milestone year (2025/30/40/50/60) |
| `optimizer_new_builds_GW.csv` | Capacity the optimizer chose to BUILD (beyond your exogenous fleet) |
| `generation_by_region_tech_year.csv` | Annual production per tech (incl. output fuel) |
| `unmet_load_dispatch.csv` | Where demand could NOT be met by real supply (see finding 2) |
| `costs_fixed_om_by_region_tech.csv` | Annual fixed O&M by tech — supports the cost review in finding 3 |
| `maxcap_fix_delta_4rows.csv` | THE 4 CORRECTED Maximum Capacity cells — carry these into your next revision |
| `power_sendback_canonical_FINAL.csv` | The full 9,337-row payload as injected, incl. the 4 fixes — your new baseline |
| `v_0.69 RAS Power Result.xlsx` | LEAP-side result export of the same run |

## The 4 corrections (KEEP these — do not overwrite)

Your absolute caps were lower than the exogenous fleet the area already
carries in RAS. The standard LEAP resolution keeps your researched cap AND
lets the committed fleet through:

| Region | Branch | Was | Now (in LEAP + canonical) |
|---|---|---|---|
| Cambodia | Wind Onshore | `1500.0` | `Max(Exogenous Capacity[MW], 1500.0) ? IES/ADB citation` |
| Philippines | Small Hydro | `1874.0` | `Max(Exogenous Capacity[MW], 1874.0) ? PH DOE citation` |
| Vietnam | Wind Onshore | `24000.0` | `Max(Exogenous Capacity[MW], 24000.0) ? World Bank citation` |
| Malaysia | Large Hydro_MYPE | `3100.0` | `Max(Exogenous Capacity[MW], 3100.0) ? IRENA citation` |

**Authoring rule for any future Max()/Min():** put the reference FIRST,
number LAST — `Max(Exogenous Capacity[MW], 1500.0)`. The reverse order makes
LEAP read the number as a YEAR and the calculation fails.

Note on Large Hydro_MYPE: the fleet trajectory (3,190 → 3,495 MW) exceeds
the IRENA 3,100 cap — the modeller's freeze-at-fleet reading and your cap
are now reconciled by the Max() form. Vietnam Wind Onshore deserves your
review: your 24 GW cap vs the ~77 GW additions trajectory in the area tell
two different build stories — the wrapper unblocks the run, but the numbers
should converge in your next revision.

## Findings from the results (in priority order)

1. **Your data behaved.** Fleet trajectories carried into results 1:1; the
   deactivation caps (cap=0 techs) held — the optimizer built nothing there.
2. **Unmet load fires at five nodes** — Indonesia East (2,370 GWh by 2060),
   Indonesia Sumatra (1,398), Indonesia Kalimantan (1,305), and Malaysia
   Sarawak persistently from 2030 (77 → 249 GWh). Jamali is fine. This means
   node-level supply or transmission is short there. This is the top
   content item for your next revision: node capacity, additions, or
   transmission limits for those five nodes.
3. **Biomass Gasification and H2 Fuel Cell look like runaway backstops** —
   the optimizer builds 346 GW of Biomass Gasification in Indonesia alone
   (416 GW ASEAN-wide by 2060) and 188 GW of H2 Fuel Cell in Indonesia.
   Please sanity-check the capital/O&M cost rows for those two families —
   if the costs are right, this is the model's story; if not, they are
   underpriced.

## Going forward — delta payloads only

From the next cycle on, send (and we inject) **only the rows you actually
changed**, not the full dataset. `maxcap_fix_delta_4rows.csv` in this
package is the template: same columns as the canonical, containing only
edited rows. The full canonical in this package is your baseline to diff
against.

If any number here conflicts with newer data you hold, tell us — don't
silently overwrite in either direction.
