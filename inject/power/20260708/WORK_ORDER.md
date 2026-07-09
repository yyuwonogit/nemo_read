# Power batch-1 work order — to the LEAP injection team (2026-07-08)

This ships with the batch-1 delta payload (`power_batch1_delta_20260708.csv`,
326 RAS rows) + the batch-1b endogenous delta
(`power_batch1b_endogenous_ATS_BAS_delta_20260708.csv`, 48 ATS/BAS rows) + the
three separate CSVs + the changelog. **Delta-only — inject only these rows,
diffed against `power_sendback_canonical_FINAL.csv`. Do not full-inject.**

## A. Actions we need from you before / during injection

1. **Exclude the six Unmet Load slack processes** from your held
   `dispatch_rule_fullcapacity_delta.csv` before injecting it — flipping
   `Unmet Load_IDEast/_IDJW/_IDKA/_IDSA/_MYPE/_MYSB` to FullCapacity would
   dispatch phantom unserved energy in the simulation scenarios. Keep the rest
   of that delta as authored.
2. **Clear the pre-existing gas/diesel retirement cliff** — our WP-D-gas
   `Add()` schedules REPLACE the crude `Interp(2035,0,2040,N)` retirement on the
   Indonesia diesel / gas-engine nodes. Remove that inherited cliff before
   applying, or the intended 10%-at-2050 shape will not materialise.

## B. Deliberate sourced supersessions — agree, don't silently revert

Per your own reconcile note ("if any value conflicts with numbers you hold,
tell us"), these 8 cells overwrite a modeller value **on purpose** because we
lead with actual data + latest sources. Please keep ours:

| Region | Branch / variable (RAS Maximum Capacity) | Ours | Source |
|---|---|---|---|
| Malaysia | Solar PV_MYPE | 324,482.9 | IRENA Malaysia ETO 2023 |
| Malaysia | Solar PV_MYSB | 12,517.1 | IRENA Malaysia ETO 2023 |
| Malaysia | Large Hydro_MYPE | Max(Exogenous Capacity[MW], 3100.0) | IRENA |
| Indonesia | Geothermal Flash_IDEast | 5,460 | MEMR / DG EBTKE 2021 |
| Indonesia | Geothermal Flash_IDSA | 9,370 | MEMR / DG EBTKE 2021 |
| Indonesia | Geothermal Flash_IDKA | 180 | MEMR / DG EBTKE 2021 |

(Do not re-inject the derated `Exogenous + 0.9×potential` geothermal caps on
top.) Also please **acknowledge the Malaysia IRENA-caps arbitration** you
already made (Solar PV_MYPE / _MYSB, Large Hydro_MYPE) so the divergence
register closes.

## C. Deliverables we need back (unblock batch-2)

3. **Hydrogen-Production module branch export** — exact branch strings + the
   cost unit basis (per kW-H2 LHV vs per kg/day vs per GJ) for Biomass
   Gasification P14988 + siblings. Our H2 Fuel Cell cap (WP-H) contains the
   SINK; the SOURCE cap is blocked until this lands.
4. **Inter-node transmission topology** — the interconnector/link capacities and
   whether the optimizer may expand them, for the deficit nodes (IDEast/IDSA/
   IDKA/MYSR and the Jamali peak). It decides whether import can relieve the
   nodes vs node-local build.
5. A **unit-stamped, branch-ID-keyed** results re-export for the next run (the
   v2 export you flagged): module filter, correct xlsx sheet names, explicit
   2025 zeros, the missing Large Hydro_IDKA 2060 row.

## D. Canon cleanups to flag (our rows stay valid after fix)

6. **Retirement copy-paste**: `Coal Subcritical_MYPE` ≡ `_MYSR` (byte-identical
   schedules) and `Gas Turbine_ID*` ×4 identical — a pre-existing canon copy
   residue, not ours (our Indonesia retirement is per-node distinct). Worth
   cleaning on the live model.
7. Confirm the Indonesia coal co-firing `Interp(2060,10)` Feedstock-Fuel-Share
   placeholders are **not** dropped by the clean (inject writes, doesn't prune).
8. **Stranded Cost** unit semantics: read the value in `stranded_cost_test_row.csv`
   from your cost report and tell us the basis (absolute USD? per MW?) so we can
   author the fleet-wide table in batch-2. It is optimization-inert.
9. Minor: CCS-coal NOx source choice (canon EMEP 18.1 vs DEA 263 g/GJ — defensible,
   informational); the Thailand ±4,450 MW hydro bookkeeping pair nets to zero.

## E. Read-me on this run (what to expect)

- **Unmet load will RISE** in run-1 — we capped the H2 Fuel Cell escape valve
  (~978 TWh of fake free generation removed), so the real deficit becomes
  visible. This is intended; we shave it over cycles.
- **New unabated Coal USC / IGCC (non-CCS) is uncapped in RAS by design** — watch
  for a new-coal build; if it balloons we revisit next cycle.
- **Gas supply stays uncapped in the inject** until the fossil team applies the
  WP-F proposal (Resources column).
- **Batch-1b (ATS/BAS endogenous)** stops after-policy auto-build of worse coal /
  diesel / fuel oil; USC/IGCC/CCS stay open everywhere by our decision. 5
  Philippines knob rows carry a NEEDS-CONFIRM (kick-in year derived).
