# Session notes — Power-sector inject cycle (2026-05-05)

Compact handoff doc. State of play, what's pending, where to pick up.

## What landed in LEAP

| Round | Variable | Scenario | Rows | Status |
|---|---|---|---|---|
| 1 | Existing Capacity | Current Accounts | 78 | ✓ pushed clean, verify-one OK on Vietnam Coal Sub |
| 1.5 | EC re-anchored + HP populated (with `FirstScenarioYear, 0`) | Current Accounts | 114 | ✓ pushed clean |
| 1.5 | HP anchored | ATS (`AMS Target Scenario`) | 55 | ✓ pushed clean |
| 1.5 | HP anchored | BAS (`Baseline Simulation`) | 55 | ✓ pushed clean |
| **Total** | | | **302** | all verified at year-level |

8 non-ID/MY AMS covered: Brunei, Cambodia, Laos, Myanmar, Philippines,
Singapore, Thailand, Vietnam. Source-of-truth: `Input_to_LEAP` sheet
of `mailbox/existing_cap_historical_prod.xlsx`.

## Pending — round 2 (ID + MY)

NOT done in this session. The round 2 design (deferred):

- **Indonesia root-level branches**: zero out EC + HP in CA per
  node-only policy. Then audit/redistribute country totals across the
  35 existing `_IDxx` node branches (IDEast, IDJW, IDKA, IDSA).
- **Malaysia root-level branches**: zero out EC + HP in CA. Malaysia
  HAS node branches: 30 of them across `_MYPE` (Peninsular), `_MYSB`
  (Sabah), `_MYSR` (Sarawak) — they exist but currently have all
  zero values. Audit + populate per-node from xlsx country totals.

Audit data already produced in `audit_country_totals.csv`. Worst
deltas:
- Indonesia Coal Subcritical: xlsx 50,930 MW vs current node sum
  242,516 MW — nodes have **4.8× too much** somewhere
- Indonesia Gas CC: xlsx 18,798 vs node sum 5,398 — nodes 71% short
- Indonesia Gas Turbine: xlsx 4,478 vs node sum 6 — essentially empty
- Most Malaysia node techs: xlsx N MW vs 0 in current state

## Open tickets (follow-ups for next session)

1. **Round 2 ID + MY inject** (described above)
2. **Thailand Wind Onshore infeasibility resolved** by setting
   `Analysis → Basic Parameters → First Simulation Year = 2025`
   (per LEAP forum thread 3958 — see `reference_first_scenario_year_trap.md`
   in memory). If similar errors surface on other techs, same fix.
3. **Anomaly diagnostic doc** at `diagnostic_anomalies.md` lists 5
   real bugs + 2 structural concerns. The non-ID/MY ones not yet
   patched:
   - **A1** Thailand Module Energy Generation = −5.22e17 GJ (years
     2025-2035) — need LEAP UI edit on Module-level expression
   - **A2/A3** Indonesia Module 110× Process sum — needs investigation
     into Module-level expression source
   - **A4** Cross-AMS leak — `_IDxx` branches showing values under
     non-ID/MY AMS rows. Real bug. Fix on Indonesia side (region
     scoping).
4. **RAS scenario row infeasibility** (`Infeasible row 'c13011817'`)
   completely parked. Resume only after BAS+ATS clean.

## How to inject in this multi-area state

LEAP has multiple areas open (`aeo9_v0.36` + others). The standard
`--scenario` flag triggers area-flip via COM. Use:

```bash
# In LEAP UI: ensure aeo9_v0.36 active, set target scenario in dropdown
python mailbox/bioenergy/inject_to_leap.py \
    --csv <path> \
    --no-scenario-switch \
    --dry-run
```

Then drop `--dry-run` for real push. Switch scenario in LEAP UI manually
between scenarios (BAS → ATS → CA), re-running the same flag pattern.
Documented in CLAUDE.md §11.1 "multi-area recovery recipe".

## Files in this folder

```
mailbox/20260505/
├── aeo9_v0.36.leap                    LEAP area file (input from Power team)
├── probe_leap_results.py              Probe A: result values
├── probe_leap_units.py                Probe B: input-side units
├── join_results_with_units.py         Probe C: offline join
├── RESULTS_HARVEST_SOP.md             SOP for the A→B→C pipeline
├── diagnostic_anomalies.md            7 anomalies + Where-to-act
├── build_existing_cap_inject.py       Round 1 generator (EC for 8 non-ID/MY)
├── build_round1p5_inject.py           Round 1.5 generator (HP + re-anchor)
├── inject_existing_capacity_round1_other_AMS.csv  78 rows pushed
├── inject_round1p5_CA.csv             114 rows pushed (CA)
├── inject_round1p5_ATS.csv            55 rows pushed (ATS)
├── inject_round1p5_BAS.csv            55 rows pushed (BAS)
├── audit_country_totals.csv           xlsx truth vs current LEAP per (country, tech)
├── results_BAS_centralized.csv        Probe A output
├── results_ATS_centralized.csv        Probe A output
├── units_centralized.csv              Probe B output
├── joined_BAS.csv                     Probe C output (BAS)
└── joined_ATS.csv                     Probe C output (ATS)
```
