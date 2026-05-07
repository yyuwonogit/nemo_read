# Injects to replicate on a new LEAP file

All injects landed on `aeo9_v0.36` (lineage-inherited from v0.33).
**Re-validated on `aeo9_v0.38` 2026-05-06 — 896/896 rows pushed
cleanly across all 5 blocks** (logs in this folder, prefix
`_inject_log_*.txt` and `_dryrun_*.txt`). Power-tree compatibility
between v0.36 and v0.38 confirmed via
[`_probe_v038_power_tree.py`](_probe_v038_power_tree.py) — all 18
expected `Transformation\Centralized Electricity Generation\Processes`
paths present, no CSV retargeting required.

In execution order. **Round 1 EC (78 rows) is fully superseded by
Round 1.5 CA** — skipped from the replication list since 1.5 CA writes
the same 78 EC rows + anchor + 36 HP rows in one push.

| # | CSV | Rows | Scenario | What it does |
|---|---|---|---|---|
| 1 | [`mailbox/bioenergy/canonical_leap_native.csv`](../bioenergy/canonical_leap_native.csv) | 580 | Regional Aspiration Scenario | Full bioenergy domain baseline — Capital Cost, Variable OM Cost, Maximum Capacity, Maximum Production, Production Cost, Import Cost, Area Harvested, Crop Yield, Fuel Cost across Biodiesel + Bioethanol processes + `Resources\Primary` feedstocks |
| 2 | [`mailbox/bioenergy/canonical_patch_2026_04_30.csv`](../bioenergy/canonical_patch_2026_04_30.csv) | 92 | Regional Aspiration Scenario | Patch over (1): 77 × Maximum Capacity (curve-preserving Add deltas), 3 × Minimum Utilization=0 (Solar PV/Rooftop/Floating), 12 × Externality Cost=0 (Sequestered CO₂) |
| 3 | [`inject_round1p5_CA.csv`](inject_round1p5_CA.csv) | 114 | Current Accounts | 78 × Existing Capacity + 36 × Historical Production for 8 non-ID/MY AMS, all with `, FirstScenarioYear, 0` anchor |
| 4 | [`inject_round1p5_ATS.csv`](inject_round1p5_ATS.csv) | 55 | AMS Target Scenario | Historical Production with anchor for non-ID/MY AMS (BAS/ATS hold their own HP overrides — don't auto-inherit from CA) |
| 5 | [`inject_round1p5_BAS.csv`](inject_round1p5_BAS.csv) | 55 | Baseline Simulation | HP with anchor — same content as ATS but in BAS scenario |
| **Total** | | **896** | 3 scenarios | |

## Replication on a new LEAP file (5 injects in this order)

```bash
# Pre-flight: open new LEAP area, confirm only one area is active.
# Confirm Analysis → Basic Parameters → First Simulation Year ≤ 2025.
# For each step: in LEAP UI, set the named scenario in the dropdown manually,
# then run with --dry-run first.

# Note: pass --expect-area <area name> on every call so the area-lock
# catches LEAP COM state drift between invocations (observed 3× in the
# v0.38 cycle; see CLAUDE.md §11.1 "Spontaneous ActiveArea=''"). Also
# add --already-converted to skip the canonical_leap_native.csv name
# check when pushing other CSVs in this folder.

# 1. Full bioenergy domain → set scenario "Regional Aspiration Scenario"
python mailbox/bioenergy/inject_to_leap.py \
    --csv mailbox/bioenergy/canonical_leap_native.csv \
    --no-scenario-switch --expect-area <area_name>
# expect: 580 rows pushed

# 2. Bioenergy patch (Issues 1, 5, 6) → still in "Regional Aspiration Scenario"
python mailbox/bioenergy/inject_to_leap.py \
    --csv mailbox/bioenergy/canonical_patch_2026_04_30.csv \
    --no-scenario-switch
# expect: 92 rows pushed

# 3. Power EC + HP → switch UI scenario to "Current Accounts"
python mailbox/bioenergy/inject_to_leap.py \
    --csv mailbox/20260505/inject_round1p5_CA.csv \
    --no-scenario-switch
# expect: 114 rows pushed

# 4. Power HP → switch UI scenario to "AMS Target Scenario"
python mailbox/bioenergy/inject_to_leap.py \
    --csv mailbox/20260505/inject_round1p5_ATS.csv \
    --no-scenario-switch
# expect: 55 rows pushed

# 5. Power HP → switch UI scenario to "Baseline Simulation"
python mailbox/bioenergy/inject_to_leap.py \
    --csv mailbox/20260505/inject_round1p5_BAS.csv \
    --no-scenario-switch
# expect: 55 rows pushed
```

## Ultimate fixing work

- Standardise all AMS exogenous capacity in BAS and ATS
- **BAS**: Exogenous Capacity, Capacity Additions, Capacity Retirement all = 0
- **ATS**: Exogenous Capacity = Existing + Addition + Retirement
  - Any positive delta = Addition
  - Any negative delta = Retirement
  - Exogenous Capacity in ATS = PDP (Power Development Plan)
