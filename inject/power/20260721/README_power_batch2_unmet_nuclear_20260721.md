# Power — batch-2 DRAFT inject: unmet-elimination + nuclear fixes (2026-07-21)

**Status: DRAFT for review — not gated.** Sized off the v0.75 RAS results.
Scenario: Regional Aspiration Scenario only.

`batch2_unmet_nuclear_inject_20260721.csv` — 55 rows, standard schema
(`ams, branch, variable, expression, unit, fuel, source, note, src_csv,
data_confidence, scenario`).

## Why this batch

v0.75 RAS 2060 carries **1,826 TWh of unmet load, 99.4% Indonesian**
(IDEast 685, IDSA 601, IDJW 327, IDKA 201 TWh). A verified constraint
discrimination found the binding wall is an **absolute-capacity lock**,
not build rate: firm dispatchable techs at the Indonesian nodes are
authored `Maximum Capacity = Exogenous Capacity[MW]` → zero endogenous
headroom (86.6% of the deficit). Build rate binds at only IDKA (13.4%);
interconnection ~19% (handled separately). The proof: `Gas Combined
Cycle_IDEast` carries a live 2,000 MW/yr build rate and builds 0 MW for
30 years because its ceiling forbids it. Separately, 18.8 GW of nuclear
(VNM 14, PHL 4.8) sits idle on economics while Indonesia's nuclear is
pinned at a nameplate-availability artifact (93% CF = mean of 95/93/91).

## The edits (55 rows, by lever)

| Point | Rows | Edit |
|---|---|---|
| **P1** Gas CC 60%-capture | 5 | Break `=Exogenous` lock; `Maximum Capacity = Max(Exogenous Capacity[MW], X)` sized to capture 60% of each node's 2060 unmet at 0.85 CF. IDEast 56,280 / IDSA 51,400 / IDJW 46,820 / IDKA 16,440 MW (+ MCA 3000/2500 where the 60% is otherwise unreachable). Only Gas CC touched — coal/diesel/gas-engine/gas-turbine left locked. |
| **P2a** exhaust resource caps | 5 | Raise `Maximum Capacity Addition` on rate-bound techs (Large Hydro_IDKA 442→800; Small Hydro_IDKA 125→300, _IDSA 125→200; Biomass_IDSA 238→500, _IDJW 238→400 MW/yr) so they fill their existing ceilings by 2060. |
| **P2b** hydro potential | 4 | Raise Large Hydro `Maximum Capacity` to **2× today** for the two famine nodes (IDEast 32,980→65,960; IDSA 15,600→31,200 MW) + MCA to build it (2000/1000). User decision 2026-07-21. |
| **P4** node CCS | 32 | Create Gas-CC-CCS and USC-CCS at IDSA + IDJW, **50/50** of the P1 gas addition (IDSA 24,220 MW each; IDJW 13,170 MW each) + MCA + 6 template params each (copied from the national Gas-CC-CCS / USC-CCS branches — the LEAP team creates the branch and pastes). Clean-firm option for the two RE-exhausted nodes. |
| **P5** nuclear | 9 | **VNM**: un-inert the dead ceiling — `Nuclear LWR Maximum Capacity = Max(Exogenous Capacity[MW], 24800)` (old `Max(Exo, 8267)` was inert since exo LWR=14,000 > 8,267 → 0 headroom); freeze SFR/SMR at fleet to avoid additive over-cap; `Minimum Utilization = 70` must-run. **PHL**: `Minimum Utilization = 70` must-run (LWR + SMR). **IDN**: `Maximum Availability = 90` on LWR/SFR/SMR (derate from the 95/93/91 nameplate). |

Ceilings are permissive (the optimiser picks). At IDSA/IDJW both
unabated gas (P1, 60%) and CCS (P4, 60%) are offered — in RAS the clean
CCS should win.

## NOT in this CSV — needs a decision / another team

1. **Transmission ramp (point 3).** Lines are `Key\Transmission\Lines\<name>`,
   but the throttle is not a clean variable: `Maximum_Capacity_Addition`
   (underscored user-var) already reads `Unlimited`, yet effective line
   capacity grows only ~1%/yr (stuck at 35.6% of nameplate) — likely a
   bug. LEAP team: confirm the binding variable, lift to ~0.05/yr or
   remove the throttle.
2. **PHL nuclear cost region-parameterisation.** We used a must-run floor
   (guaranteed) rather than inventing PH cost numbers. Cleaner economics
   fix: region-source PHL Nuclear Var/Fixed OM from PH DOE PEP, replacing
   the inherited Vietnam template.
3. **Malaysia nuclear generation-without-fuel** (v0.75 audit): 27 TWh of
   MY nuclear with no fuel input — a `_MY*` node fuel-wiring defect (same
   family as the audit's `Gas Turbine_MYSR` ERROR). Separate wiring fix.

## Flags on the numbers (reviewer decisions)

- **Nuclear must-run is a policy choice.** It forces VNM/PHL nuclear to
  run even where uneconomic — useful (built fleet no longer stranded,
  lower emissions there) but VNM/PHL have **no unmet**, so it does not
  help the Indonesian deficit. Alternative: drop the must-run and rely on
  the gas cap (WP-F, fossil team).
- **Gas is large.** P1 = ~146 GW of new unabated gas across the 4 nodes
  (~430 TWh/yr) — a real RAS emissions bulge. P4 CCS is what keeps it
  defensible; if you want clean-firm to lead, cap the unabated gas lower
  at IDSA/IDJW.

Prepared by the AEO-9 Power modelling track. Sizing rule:
`GW = share × node-2060-unmet-TWh / (8.76 × CF)`, CF 0.85 firm / 0.55 hydro.
