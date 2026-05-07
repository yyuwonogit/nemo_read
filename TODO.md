# In-flight work — pick up here

> **Cross-session pickup note.** Started 2026-05-06; user is continuing
> in another engine. Read this before doing anything else. Delete (or
> empty) once §1-3 are complete.

## Where we are

Re-validated the [`mailbox/20260505/INJECTS_TO_REPLICATE.md`](mailbox/20260505/INJECTS_TO_REPLICATE.md)
inject queue on a fresh `aeo9_v0.38` LEAP area. **896/896 rows pushed
clean** across 4 scenarios (RAS 672, CA 114, ATS 55, BAS 55). Logs in
[`mailbox/20260505/_inject_log_*.txt`](mailbox/20260505/) and
[`mailbox/bioenergy/_inject_log_*.txt`](mailbox/bioenergy/).

Power-tree compatibility v0.36 → v0.38 confirmed via
[`mailbox/20260505/_probe_v038_power_tree.py`](mailbox/20260505/_probe_v038_power_tree.py)
— all 18 expected branches present, no CSV retargeting needed.

CLAUDE.md §11.1 + CHANGELOG already updated with three new LEAP COM
findings discovered during this cycle (dry-run cache trap,
branch-visibility flux, spontaneous `ActiveArea=''`).

## Not done — pick up in this order

### 1. Read-back-one verify per scenario (CLAUDE.md §4.1)
Lightweight post-push sanity check: for each scenario, read
`Variable.Expression` via COM on one representative row, diff against
the inject CSV's `expression` field byte-exact. Catches injector
misroutes before the 30-min calculatescenario round-trip.

Suggested probe rows (`Brunei` for all):
| Scenario | Branch | Variable |
|---|---|---|
| RAS | `Transformation\Biodiesel Production\Processes\FAME Biodiesel` | `Capital Cost` |
| CA  | `Transformation\Centralized Electricity Generation\Processes\Coal IGCC` | `Existing Capacity` |
| ATS | `Transformation\Centralized Electricity Generation\Processes\Coal IGCC` | `Historical Production` |
| BAS | `Transformation\Centralized Electricity Generation\Processes\Coal IGCC` | `Historical Production` |

User has to flip UI scenario between calls (per the §11.1
multi-area recipe). ~70s cache rebuild × 4 = ~5 min total.

### 2. `calculatescenario` (LEAP UI, heavy step)
Run from LEAP UI for each scenario that should produce a `.sqlite`:
RAS, CA, ATS, BAS. Tens of minutes per scenario. Drop the resulting
`.sqlite` into `infeas/` (or wherever the user prefers) for §3.

### 3. Post-calc validation (per CLAUDE.md §4.1)
For each fresh `.sqlite`:
- `print_overview(db)` — no new validation issues vs. v0.36 baseline
- `check_scenario(db)` — returns `ok()` (or *strictly subset* of prior
  issues; if not, see CLAUDE.md §8 for the 11-stage infeasibility flow)

### 4. Deferred power-domain authoring work
From [`INJECTS_TO_REPLICATE.md` lines 57-64](mailbox/20260505/INJECTS_TO_REPLICATE.md)
"Ultimate fixing work" — *not* blocking the v0.38 baseline, separate
authoring task:
- **BAS** standardisation: Exogenous Capacity, Capacity Additions,
  Capacity Retirement all = 0 across all AMS
- **ATS** standardisation: Exogenous Capacity = Existing + Addition +
  Retirement (positive deltas → Addition, negative → Retirement;
  Exogenous Capacity in ATS = PDP)

### 5. Possible v0.6.8 release
Only after §1-3 pass. Bump in [`pyproject.toml`](pyproject.toml) and
[`nemo_read/__init__.py`](nemo_read/__init__.py); CHANGELOG bullets
already accumulated under `[Unreleased]`.

## Cleanup at next pass

[`mailbox/20260505/_build_RAS_combined.py`](mailbox/20260505/_build_RAS_combined.py)
and `_inject_RAS_combined.csv` are an abandoned merge experiment from
the start of this session (decided to push 5 blocks separately
instead). Per CLAUDE.md §12.3 they can be deleted at the next cleanup
pass — kept for now as breadcrumb.

## Traps to remember (already in CLAUDE.md §11.1, repeated for emphasis)

- **Always pass `--expect-area aeo9_v0.38`** on every `inject_to_leap.py`
  call — `ActiveArea` blanks spontaneously between Python invocations
  (3× this session).
- **`PYTHONPATH=$(pwd)`** before invoking the injector if `nemo_read`
  isn't installed in the active Python env.
- **Dry-run `branch_not_found` is unreliable** — false positives when
  ActiveRegion at cache-build time doesn't expose all branches. Run
  `_probe_v038_power_tree.py` (or similar) under a region that should
  see the full tree before declaring real structural mismatch.
- **User must flip UI scenario** between scenario blocks; the script
  uses `--no-scenario-switch` and reads whatever's active.
