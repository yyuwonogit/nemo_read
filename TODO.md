# In-flight work — pick up here

> **Cross-session pickup note.** This file is what a fresh Claude
> session reads first (CLAUDE.md §0). It tells you what's pending
> across sessions. Update or empty it whenever a major piece of work
> completes.

## Status as of 2026-05-17

**Workstream 1 — Standardised inject + probe framework: DONE.**
- [nemo_read/inject_base.py](nemo_read/inject_base.py) ships `CanonicalInjector` (sealed primitives + open hooks; warm-COM dry-run → confirm → real → readback in one Python invocation; multi-scenario via `--scenarios`)
- [nemo_read/probe_base.py](nemo_read/probe_base.py) ships `CanonicalProber` (sealed BT={3,50} unit-read guard; Probe A per scenario + Probe B once per area, one COM session)
- [nemo_read/_heartbeat.py](nemo_read/_heartbeat.py) ships the universal heartbeat + `_progress_*.json` convention for any LEAP COM op > 60s (CLAUDE.md §A.16)
- All 3 existing injectors (bioenergy / fossil / power) migrated to thin `CanonicalInjector` subclasses
- 166 tests passing; CI scan refuses any `Variable.Expression =` write outside the sealed chokepoint

**Workstream 1.5 — `Interp(...)` separator enforcement (§A.15): DONE.**
- 3-layer defence (adapter normaliser + injector chokepoint + pre-flight CSV scan); readback verify hard-fails on NORMALISED matches.

## What's pending — pick up in this order

### 1. Full-area probe of `aeo9_v0.45` (when user signals)

User intends to run a **full-area probe** of the next LEAP version
(`aeo9_v0.45` — to be confirmed by user) covering:
- Multiple scenarios (likely BAS + ATS + RAS + CA, confirm with user)
- The **entire area** (not just Centralized Electricity Generation
  like the 2026-05-05 cycle)
- Both input + result sides (one CanonicalProber.run() handles both)
- Branch + unit + value reads in one COM session

**Trigger:** when the user opens a new Claude session, asks "what to
do now?", "wazzup", or any session-status query — propose this as the
next concrete action. Do NOT start without explicit go-ahead.

**Setup recipe** (when user says go):
1. Confirm with user (§A.9): exact area filename + scenario list +
   any scope narrowing (full area or a subtree?)
2. Drop a `result/<YYYYMMDD>/probe_aeo9_v0.45.py` (~10-line subclass
   of `CanonicalProber` — see CLAUDE.md §7.1 template)
3. Launch via `Bash run_in_background=True`:
   ```
   python result/<date>/probe_aeo9_v0.45.py \
       --scenarios "BAS,ATS,RAS,CA" \
       --expect-area "aeo9_v0.45" \
       --out-dir result/<date>/
   ```
4. Monitor via the harness `Monitor` tool on the background shell, or
   `cat _progress_*.json` on demand
5. Expected wall-clock: ~50 min/scenario × N + ~4 min for units + cache
   build (~3 min once). For 4 scenarios on full area, budget 3-4 hours.

**Pitfalls already enforced by the framework:**
- `Base Template` region excluded automatically
- `--years` defaults to 2025-2060 step 5 (pitfall #6 — pre-model years
  inflate CSV ~7×)
- `--skip-zeros` default ON
- BT={3,50} restriction for unit reads (§11.2; sealed)
- safe_value / safe_data_unit_text on every read

### 2. Workstream 2 — repo reorg `mailbox/` → `mailbox/` + `inject/` + `result/`

After the v0.45 probe lands (or sooner if user prioritises). Plan:
1. `mkdir inject/ result/` at repo root
2. `git mv inject/bioenergy/` → `inject/bioenergy/`, same for `fossil/`, `power/`
3. `git mv result/20260505/` → `result/20260505/`, same for `20260513/`
   (with the inject-probe split flagged per-file — `_probe_v038_power_tree.py`,
   `_probe_readback_one.py` are inject-side scratch, ask first)
4. Update path references in CLAUDE.md, FLOWS.md, pyproject.toml, scripts
5. Add `MAILBOX_ROUTING.md` at repo root explaining the inbox→inject/result
   flow + clone-then-sweep ritual
6. `infeas/` and `mailbox/` (now pure inbox) stay put
7. Run pytest after each major move

### 3. (deferred from earlier session, lower priority)
- v0.38 cycle: §1-3 of previous TODO.md (read-back-one verify per
  scenario, then calculatescenario, then post-calc validate). Stale
  if a newer LEAP version is now in use; check with user before
  re-attempting.

## When in doubt
- Re-read [CLAUDE.md §A](CLAUDE.md) hard rules
- [docs/FLOWS.md](docs/FLOWS.md) for the standardised inject / probe / infeas flows
- Memory: `MEMORY.md` for user preferences + project context
