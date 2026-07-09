# Batch-1 delta payload — RAS v0.69 (2026-07-08)

Delta-only send-back to the LEAP injection team: **only the rows we changed**,
diffed against the injected baseline
`Power/Raw/results_v069/power_sendback_canonical_FINAL.csv`. Do NOT full-inject.

| File | Rows | What |
|---|---|---|
| `power_batch1_delta_20260708.csv` | 326 | The main payload. Validates clean through `Power/Analysis/build_delta_payload.py --check` (units, region-lock, Max() reference-first, no collisions); every Capacity Retirement row proven non-negative 2024-2060. |
| `stranded_cost_test_row.csv` | 1 | WP-I unit-semantics probe (one Stranded Cost value, unit `U.S. Dollar`). Fails the validator **by design** — the non-canonical unit IS the probe. Never fold into the main payload. |
| `wpj_run2_dispatch_reversal.csv` | 18 | Run-2 of the contractual-dispatch experiment: byte-clean restore of the original Minimum Utilization expressions. Ship separately; run-1 (the 18 must-run floors) is in the main payload. |
| `wpf_gas_ceiling_proposal_fossil_team.csv` + `wpf_gas_ceiling_memo.txt` | 10 | Gas-supply ceiling PROPOSAL for the fossil team (Resources column). NOT a batch-1 capacity injection — a hand-off. |

## What batch-1 does (authored to the gate decisions in `Power/Analysis/GATE_DECISIONS_batch1_20260708.md`)
Coal + gas/oil phase-down toward ~0 by 2060 (10% at 2050, off exogenous); tier-1/2
dirty-fossil freeze; H2 Fuel Cell escape valve capped; nuclear headroom opened at
full per-tech build rate; node build-rate harmonisation + geothermal / Sarawak hydro /
Vietnam wind raises; hydro availability derated to 65%; Vietnam gas-CCS un-idled.
Plain gas and all CCS stay expandable (user calls).

## Known items for the run (deliberate, watch in results)
- **Unmet load will RISE** — capping the H2 valve exposes Indonesia's real deficit; honest baseline for the unmet tracker to shave over cycles.
- **New unabated Coal USC / IGCC (non-CCS) left uncapped** — deliberate user call; watch for a new-coal escape in run-1.
- **Gas supply uncapped in the inject** until the fossil team applies the WP-F proposal.

## Work-order asks accompanying this payload
Exclude the six Unmet Load slack processes from the held dispatch delta; acknowledge
the Malaysia IRENA-caps arbitration; deliver the Hydrogen-module branch export (to close
the H2 source in batch-2); supply the inter-node transmission topology.
