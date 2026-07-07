# Base-branch rows removed (§A.23 authoring lock) — 2026-07-07

## What happened

The 9,421-row sendback payload failed at inject: LEAP refused writes with
**"there is no branch Biogas / Geothermal Flash in Indonesia"**. Root cause:
84 rows authored Indonesia fleet data on the **un-suffixed base branches** of
node-decomposed families. Indonesia's raw Export-Expressions walk
(`LEAP Input Transformation Indonesia.xlsx`, 58,033 branch cells) contains
**zero** base-branch rows for these families — Indonesia's fleet lives
exclusively on the `_ID*` node variants. The base branch exists in the global
tree (§A.22) but is not an authoring slot in Indonesia's region view.

Principle (user directive 2026-07-07): **we hold the truth of the LEAP
structure (branches, variables, units); technical teams hold authority over
content only.** Structure-invalid rows are removed, not negotiated.

## Removed — 84 rows from both `power_sendback_canonical.csv` (9,421 → 9,337)
## and `power_sendback_cleaned.csv` (9,421 → 9,337)

21 rows each on 4 Indonesia base branches under
`Transformation\Centralized Electricity Generation\Processes\`:

| Base branch | Indonesia's real slots | Removed variables (rows) |
|---|---|---|
| Biogas | `Biogas_IDJW/_IDKA/_IDSA` (3 nodes — no IDEast) | Capacity Additions (4), Capacity Retirement (4), Endogenous Capacity (3), Existing Capacity (4), Exogenous Capacity (4), Maximum Capacity (1), Maximum Capacity Addition (1) |
| Gas Engine | `Gas Engine_IDEast/_IDJW/_IDKA/_IDSA` | same 21-row pattern |
| Gas Turbine | `Gas Turbine_IDEast/_IDJW/_IDKA/_IDSA` | same 21-row pattern |
| Geothermal Flash | `Geothermal Flash_IDEast/_IDJW/_IDKA/_IDSA` | same 21-row pattern |

Backups: `*.bak_pre_basebranch_20260707` beside each file.

Also cleaned in the same pass:
- `inject/power/20260705/exo_capacity_canonical.csv` — 16 rows (same 4
  families × Exogenous Capacity × 4 scenarios), 1,580 → 1,564.
- `inject/power/20260507/from PowerTeam/fix_exogenous_capacity.csv` — 4 rows
  (same 4 families × Exogenous Capacity), 395 → 391. Second cleaning pass on
  this archive (first was the §A.21 node-lock pass, 2026-07-05).

## ACTION REQUIRED — power team (data question, yours to answer)

Three of the removed variables exist **only** on the (invalid) base rows and
on **no `_ID*` node row** in the payload:

- `Capacity Retirement` (4 rows/family)
- `Endogenous Capacity` (3 rows/family)
- `Maximum Capacity` (1 row/family, RAS)

If that data is real, re-author it **per node** (`_IDJW/_IDSA/_IDKA/_IDEast`;
Biogas has no `_IDEast`) with a nodal split of your choosing. The other four
variables (Existing/Exogenous Capacity, Capacity Additions, Maximum Capacity
Addition) already have node-level rows in the payload — the base rows were
redundant aggregates and their removal loses nothing that survives export.

## What was NOT removed (checked and valid)

- Malaysia rows on base `Gas Turbine` (21) — Malaysia's own walk carries the
  base branch (only the `_MYPE` node splits out). Valid slot.
- All copper-plate-region rows on base `Solar PV` / `Wind Onshore` /
  `Small Hydro` / `Large Hydro` / nuclear / etc. (v0.68/v0.69 base-branch
  additions; the nine countries author on base per the reconciliation
  README).
- All `_ID*` / `_MY*` node rows — region-lock clean (0 violations).

## Enforcement added in the same change

`nemo_read.BASE_BRANCH_NODE_ONLY` + class-2 check in
`find_region_lock_violations` (CLAUDE.md §A.23): any future payload row
authoring a locked base branch for Indonesia/Malaysia now aborts the inject
at pre-flight and fails CI (`tests/test_region_lock.py`).
