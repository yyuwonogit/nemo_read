# Injects to replicate on a new LEAP file

All injects landed on `aeo9_v0.36` (lineage-inherited from v0.33).
**Re-validated on `aeo9_v0.38` 2026-05-06 — 896/896 rows pushed
cleanly across all 5 blocks** (logs in this folder, prefix
`_inject_log_*.txt` and `_dryrun_*.txt`). Power-tree compatibility
between v0.36 and v0.38 confirmed via
[`_probe_v038_power_tree.py`](_probe_v038_power_tree.py) — all 18
expected `Transformation\Centralized Electricity Generation\Processes`
paths present, no CSV retargeting required.

**Round 2 ID/MY merged 2026-05-07** (`aeo9_v0.38_yy` cycle) — 126 EC
+ 126 HP rows on Indonesia / Malaysia subnational `_IDxx` / `_MYxx`
nodes appended in-place to the round-1.5 inject CSVs. Source: Rev1
LEAP-export drop in [`mailbox/power/20260507/`](../power/20260507/).
Build script: [`build_round2_id_my.py`](../power/20260507/build_round2_id_my.py).
Pre-merge state preserved as `*.bak_pre_20260507`. Audit chunks:
`inject_round2_id_my_{CA,ATS,BAS}.csv` next to the source. **Push
target switched from `inject_to_leap.py` to
[`run_workflow.py`](../power/run_workflow.py)** for the power injects
(steps 3-5) — the 3-cache region grouping is required to resolve
`_IDxx` / `_MYxx` branches under cache region-filtering on
`aeo9_v0.38_yy` (see [power/CSV_AUTHORING_GUIDE.md §5](../power/CSV_AUTHORING_GUIDE.md)).

In execution order. **Round 1 EC (78 rows) is fully superseded by
Round 1.5 CA** — skipped from the replication list since 1.5 CA writes
the same 78 EC rows + anchor + 36 HP rows in one push.

| # | CSV | Rows | Scenario | What it does |
|---|---|---|---|---|
| 1 | [`mailbox/bioenergy/canonical_leap_native.csv`](../bioenergy/canonical_leap_native.csv) | 580 | Regional Aspiration Scenario | Full bioenergy domain baseline — Capital Cost, Variable OM Cost, Maximum Capacity, Maximum Production, Production Cost, Import Cost, Area Harvested, Crop Yield, Fuel Cost across Biodiesel + Bioethanol processes + `Resources\Primary` feedstocks |
| 2 | [`mailbox/bioenergy/canonical_patch_2026_04_30.csv`](../bioenergy/canonical_patch_2026_04_30.csv) | 92 | Regional Aspiration Scenario | Patch over (1): 77 × Maximum Capacity (curve-preserving Add deltas), 3 × Minimum Utilization=0 (Solar PV/Rooftop/Floating), 12 × Externality Cost=0 (Sequestered CO₂) |
| 3 | [`inject_round1p5_CA.csv`](inject_round1p5_CA.csv) | 240 | Current Accounts | Round 1.5 (114: 78 EC + 36 HP for 8 non-ID/MY AMS) **+ Round 2 (126: 63 EC + 63 HP for ID/MY subnational nodes)**, all with `, FirstScenarioYear, 0` anchor |
| 4 | [`inject_round1p5_ATS.csv`](inject_round1p5_ATS.csv) | 118 | AMS Target Scenario | Round 1.5 (55 HP for non-ID/MY) **+ Round 2 (63 HP for ID/MY subnational nodes)**. BAS/ATS hold their own HP overrides — don't auto-inherit from CA |
| 5 | [`inject_round1p5_BAS.csv`](inject_round1p5_BAS.csv) | 118 | Baseline Simulation | HP with anchor — same content as ATS but in BAS scenario |
| **Total** | | **1148** | 3 scenarios | |

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
#    Use run_workflow.py (3-cache region grouping) — required for ID/MY
#    subnational rows under aeo9_v0.38_yy cache region-filtering.
python mailbox/power/run_workflow.py \
    --csv mailbox/20260505/inject_round1p5_CA.csv \
    --expect-area aeo9_v0.38_yy \
    --expect-scenario "Current Accounts"
# expect: 240 rows pushed (114 round 1.5 non-ID/MY + 126 round 2 ID/MY)

# 4. Power HP → switch UI scenario to "AMS Target Scenario"
python mailbox/power/run_workflow.py \
    --csv mailbox/20260505/inject_round1p5_ATS.csv \
    --expect-area aeo9_v0.38_yy \
    --expect-scenario "AMS Target Scenario"
# expect: 118 rows pushed (55 round 1.5 + 63 round 2)

# 5. Power HP → switch UI scenario to "Baseline Simulation"
python mailbox/power/run_workflow.py \
    --csv mailbox/20260505/inject_round1p5_BAS.csv \
    --expect-area aeo9_v0.38_yy \
    --expect-scenario "Baseline Simulation"
# expect: 118 rows pushed (55 round 1.5 + 63 round 2)
```

## Ultimate fixing work

- Standardise all AMS exogenous capacity in BAS and ATS
- **BAS**: Exogenous Capacity, Capacity Additions, Capacity Retirement all = 0
- **ATS**: Exogenous Capacity = Existing + Addition + Retirement
  - Any positive delta = Addition
  - Any negative delta = Retirement
  - Exogenous Capacity in ATS = PDP (Power Development Plan)
