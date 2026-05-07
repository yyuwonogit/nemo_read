# Power inject plan — 2026-05-07 cycle

> **Status.** Multi-scenario inject of (a) the ATS / BAS power
> standardisation rows (`*_canonical.csv` from the 4 LEAP-export inputs)
> and (b) the Rev1 ID/MY EC + HP rows (`rev1_*_canonical.csv` from the
> year-wide LEAP-export). All rows have been canonicalised; this plan is
> the operator runbook to push them.

## Pre-flight (do once)

1. **Only one LEAP area open**: `aeo9_v0.38_yy`. CLAUDE.md §11.1
   multi-area trap fires hard if two areas with same scenario name are
   open — the inject silently writes to the wrong one. Close the others.
2. **First Simulation Year ≤ 2025** in Analysis → Basic Parameters.
   The `, FirstScenarioYear, 0` anchor in every `Interp(...)` is only
   meaningful when FirstScenarioYear is the year right after 2024
   (CLAUDE.md §11.2b — phantom HP-with-no-capacity trap).
3. **Echo back to the operator** before kicking off: area filename,
   First Simulation Year, only-one-area-open status.

## Inject order — six pushes

Each push is a single `run_workflow.py` invocation. Operator flips
`ActiveScenario` in the LEAP UI dropdown between pushes and reads the
dropdown text aloud (every misroute this session was caught by reading
the dropdown back). `--expect-scenario` makes the script abort on
drift, but reading aloud is the durable safeguard.

Set `<AREA>=aeo9_v0.38_yy`. All commands run from repo root,
`PYTHONPATH=$(pwd)`.

### 0. Finish current ATS power-standardisation push (in flight)

If still running in the background as of plan-time, let it finish.
Last failure was `Gas Turbine_MYPE . Capacity Additions = None` —
scenario-scoped variable trap (§11.2). Operator refreshed LEAP; re-run
should pass. Output: `_inject_log_ats_blind_<ts>.txt`. Expect 1364
rows pushed if all rows resolve. If it fails on a different
`var_not_found`, drop `--fail-fast` and capture skipped rows for
manual investigation.

### 1. CA: round1p5 already pushed earlier this session — skip re-push

`mailbox/20260505/inject_round1p5_CA.csv` (78 EC + 36 HP for non-ID/MY)
was re-injected with commas earlier (see read-back-one EXACT for
Brunei Coal IGCC EC + HP). No-op for this cycle.

### 2. CA: Rev1 ID/MY (126 rows = 63 EC + 63 HP)

UI scenario: **`Current Accounts`** (read dropdown back).

```
python mailbox/power/run_workflow.py `
    --csv mailbox/power/20260507/rev1_ca_canonical.csv `
    --expect-area aeo9_v0.38_yy `
    --expect-scenario "Current Accounts" `
    --dry-run
# Then drop --dry-run for real push.
```

Expected: 126 pushed, 0 branch_not_found. ID/MY rows hit subnational
branches like `Coal Subcritical_IDJW`, `Solar PV_MYPE`, etc. — these
are the branches the cache historically misses (lazy-loaded). Use
**default cache mode first**, not `--blind`. If cache reports false
misses, switch to `--blind --fail-fast` after verifying the missing
branches exist in the LEAP UI tree.

### 3. ATS: round1p5 + Rev1 HP

Two pushes back-to-back (or combine into one CSV first):

- `mailbox/20260505/inject_round1p5_ATS.csv` (55 rows, non-ID/MY HP) —
  already pushed earlier; **skip if already EXACT**.
- `mailbox/power/20260507/rev1_ats_canonical.csv` (63 rows, ID/MY HP).

UI scenario: **`AMS Target Scenario`**.

```
python mailbox/power/run_workflow.py `
    --csv mailbox/power/20260507/rev1_ats_canonical.csv `
    --expect-area aeo9_v0.38_yy `
    --expect-scenario "AMS Target Scenario" `
    --dry-run
```

Expected: 63 pushed.

### 4. BAS: round1p5 + Rev1 HP

Mirrors §3 but for Baseline Simulation:

- `mailbox/20260505/inject_round1p5_BAS.csv` — already pushed.
- `mailbox/power/20260507/rev1_bas_canonical.csv` (63 rows).

UI scenario: **`Baseline Simulation`**.

Expected: 63 pushed.

### 5. BAS: power standardisation (1549 rows)

`mailbox/power/20260507/bas_all_zero_canonical.csv` — Capacity
Additions / Retirement / Exogenous Capacity = 0 across all power
techs. Same scenario as §4 (Baseline Simulation), can be done in the
same UI session.

Expected: 1549 pushed.

## Read-back-one verify (after each push)

Script: [`mailbox/20260505/_probe_readback_one.py`](../../20260505/_probe_readback_one.py)
— now supports per-row region. Updated PROBES dict covers:

- CA: Brunei Coal IGCC EC + HP, Indonesia Coal Subcritical_IDJW EC,
  Malaysia Solar PV_MYPE HP
- ATS: Brunei Coal IGCC HP, Indonesia Gas Combined Cycle_IDJW HP
- BAS: Brunei Coal IGCC HP, Malaysia Large Hydro_MYSR HP

```
python mailbox/20260505/_probe_readback_one.py
```

Reads `ActiveScenario` from LEAP and runs every probe row defined for
it. **EXACT** = byte-perfect commas; **NORMALISED** = LEAP returned
period-list-sep, re-inject (separator-convention memory); **FAIL** =
real divergence, halt.

## calculatescenario + post-calc validation

Run from LEAP UI for each scenario that should produce a `.sqlite`:
**Current Accounts**, **AMS Target Scenario**, **Baseline Simulation**.
Tens of minutes per scenario. Drop the resulting `.sqlite` into
`infeas/` (or wherever the user prefers).

Per-sqlite checks (CLAUDE.md §4.1):
- `print_overview(db)` clean — no new validation issues vs the v0.36
  baseline.
- `check_scenario(db)` returns `ok()` (or strictly subset of prior
  issues; if not, see CLAUDE.md §8 — 11-stage infeasibility flow).
- Targeted symptom checks: ID/MY EC and HP values present and
  correctly anchored; ATS Exogenous Capacity formula evaluates
  correctly; BAS additions/retirements zero across the board.

## Pitfalls (already discovered in this cycle — do not repeat)

- **Phantom-branch trap.** `--blind` direct-lookup logged `[OK]` on
  branches that do NOT exist in the LEAP UI (`Unmet Load_ID*`,
  `Gas Engine_MY*`, `Solar PV Rooftop` on Centralized). LEAP COM
  silently created phantom branches or accepted writes to nowhere.
  These are now in `DROP_OFFTREE_BRANCHES` in `build_canonical.py` —
  the canonical CSVs no longer contain them. **Never run blind without
  `--fail-fast`** so a real failure terminates one row in.
- **Scenario-scoped variable trap (§11.2).** Some (branch, variable)
  pairs return `None` when looked up via COM despite the branch being
  visible. Last seen on `Gas Turbine_MYPE . Capacity Additions` in ATS.
  Refreshing LEAP (clicking into the branch in the UI) clears it.
  Pair `--fail-fast` with manual UI refresh; re-run.
- **Cache lazy-loading.** `LeapTreeCache` enumerates only branches
  LEAP has materialised in the current session. Different cache
  builds in the same area return different counts (4172 vs 5031 seen
  this cycle). Cache built under one ActiveRegion is byte-identical
  to cache built under another — region-INDEPENDENT, not
  region-filtered. So the `--blind` escape hatch is the workaround
  when cache misses; SOP is still cache-mode dry-run first.
- **Spontaneous `ActiveArea=''`.** Observed 4× this session. Mitigate
  by: only one area open + click into the area in the UI before
  starting + script's `--expect-area` lock aborts cleanly if it
  drifts mid-flight.
- **Scenario misroute (`Regional Aspiration Scenario test`).** 510
  rows pushed to wrong scenario earlier this session. Always read
  the dropdown text aloud before saying go; `--expect-scenario`
  catches it now too.
