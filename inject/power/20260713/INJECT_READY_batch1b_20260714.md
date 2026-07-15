# batch-1b — inject-ready staging (2026-07-14)

Power batch-1b send-back, structure-validated and staged for inject against
`aeo9 v0.71`. **Not yet injected** — awaits the §2.5/§A.9 area/scenario
confirmation and two Power-team acknowledgements (see the review bundle
`outbox/20260714/`).

## Files staged here

| File | Rows | Scenarios | Preflight |
|---|---|---|---|
| `power_batch1b_delta_20260713.csv` | 262 | RAS 202 / ATS 30 / BAS 30 | region-lock 0, Interp 0, §11.2b 0 — clean |
| `stranded_cost_test_row_REALIGNED_20260714.csv` | 1 | RAS only | region-lock 0, Interp 0, §11.2b 0 — clean; realigned from the 10-field original |

## Delta doctrine
Delta-only push — only these rows inject; the 4 MaxCap wrappers
(`inject/power/20260709_ship/inject_files/04_our_maxcap_wrapper_patch.csv`)
are NOT in the payload and stay as injected (0 collision confirmed). The
262-row delta does not touch our 2026-07-13 Existing-Capacity zero-point fix
(0 Existing Capacity / Historical Production / Current Accounts rows).

## Run recipe (after area confirmation)
- Blind mode (default) + `--fail-fast`; **`--exclude-timor-leste`** (user
  gate 2026-07-14; TL disabled in calc).
- Main delta: `--scenarios "Regional Aspiration Scenario,AMS Target Scenario,Baseline Simulation"`.
- Stranded probe: its own run, `--scenarios "Regional Aspiration Scenario"`
  (RAS-only, optimization-inert).
- Post-inject: per-scenario readback `N EXACT, 0 NORMALISED, 0 FAIL`; expect
  batch-1 values (not LEAP defaults) on the 11 rows the send-back mislabels
  as "structural-create".

## Sanctioned content changes in this payload
- VOLL: Unmet Load `Variable OM Cost` 500 → 20,000 (all AMS + ID/MY nodes,
  RAS/ATS/BAS); `Fixed OM Cost` stays 500. User-approved 2026-07-14. The
  standing "Unmet Load = 500" pricing text (CLAUDE.md §11.4c) updates only
  **after** the solve validates.
- Nuclear ceilings raised to ~100 GW ASEAN; RAS coal retirement + USC/USC-CCS
  reactivation; biomass biophysical caps; RE build-rate 1×/3×/8× ramp.

## Structural corrections routed back to Power (do NOT execute as work-ordered)
- No branch creation: base `Nuclear SMR` and base `Unmet Load` are
  region-invariant and already exist; the flagged rows inject onto them.
  Residual = live-area unhide/Node-wiring check at inject.
