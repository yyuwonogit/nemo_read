# Standardised flows

Three established operations in this repo, each with a canonical
step-by-step shape. New sessions should read this before starting any
of these tasks; deviations from the shape need a reason.

| Flow | When | Reference |
|---|---|---|
| **Inject** | Sector team drops authoring data → flows upstream into LEAP | §1 below + CLAUDE.md §4, §5.1 |
| **Results harvest** | Read calculated result numbers out of a `.leap` area | §2 below + CLAUDE.md §7 + [result/20260505/RESULTS_HARVEST_SOP.md](../result/20260505/RESULTS_HARVEST_SOP.md) |
| **Infeasibility triage** | Solver returned INFEASIBLE | §3 below + CLAUDE.md §8 + [docs/infeasibility_methodology.md](infeasibility_methodology.md) |

All three start the same way: **mailbox is the inbox**. User drops the
artifact under `mailbox/<YYYYMMDD>/`; we route a clone to where it
belongs; originals are swept at the next stage commit.

---

## 1. Inject flow — CSV authoring → LEAP

```
0. SECTOR TEAM DROP          → mailbox/<YYYYMMDD>/<raw files>
                                (new sector's first CSV, updated authored CSV, or
                                raw data needing adapter work — all land in mailbox
                                first regardless of type)

1. CONFIRM LEAP TARGET       → §2.5 + §A.9
                                ASK USER: area filename + scenario + .sqlite path.
                                Read it back. No step past here without explicit yes.

2. ANALYSE + REVIEW          → §A.13 (hypothesis discipline) + §A.14 (cite or hedge)
                                - Domain known or new?
                                - Shape vs §2.3 mapping + the domain's
                                  CSV_AUTHORING_GUIDE.md
                                - Red flags: Interp separators, unit basis, branch
                                  paths, duplicate rows
                                - State findings as hypotheses, cite each source

3. FIX                        → §A.2 (narrow scope)
                                Touch only the named items. Don't iterate on failing
                                COM probes (§A.3).

4. ROUTE FILES                → Clone (not move) mailbox/<date>/ → inject/<domain>/
                                Originals stay in mailbox until stage-commit sweep.

5. ADAPTER WORK               → New sector: write build_canonical.py +
                                  CanonicalInjector subclass (CLAUDE.md §5.1) +
                                  CSV_AUTHORING_GUIDE.md (§6.1), seeded with
                                  applicable Cross-Domain Learnings (§6.3).
                                Existing sector: update adapter only if behaviour
                                  needs to change. Update guide if convention
                                  changed.

6. BUILD CANONICAL            → python inject/<domain>/build_canonical.py
                                Produces canonical_leap_inputs.csv with Interp()
                                auto-normalised at write time (§A.15 Layer 1).

7. RE-CONFIRM LEAP STATE      → §A.9 — restate area + scenario, explicit yes.
                                Don't skip even if step 1 was minutes ago.

8. WARM-COM INJECT CYCLE      → python inject/<domain>/inject_to_leap.py \
                                     --expect-area <name> \
                                     --scenarios "RAS,CA,ATS,BAS" \
                                     [--yes]    # skip interactive prompts
                                
                                Framework runs ALL of these in ONE COM session
                                (CLAUDE.md §A.10):
                                
                                  a. dispatch_leap → area lock
                                  b. for each scenario:
                                     - set ActiveScenario + verify drift
                                     - build tree cache (reused across phases)
                                     - DRY-RUN phase (forbidden-Interp scan,
                                       LEAP-native unit gate, placeholder gate,
                                       per-row preview). Any failure → STOP
                                       this scenario, move to next.
                                     - CONFIRM prompt (skipped if --yes)
                                     - REAL INJECT phase (sealed
                                       _set_expression chokepoint normalises
                                       every write). 
                                     - READBACK VERIFY phase (1 sample row
                                       per region by default). NORMALISED
                                       match = HARD FAIL (§A.15).
                                
                                Flags:
                                  --dry-run-only      stop after dry-run
                                  --yes               skip confirmation
                                  --no-readback       skip readback (NOT SOP)
                                  --scenarios X,Y,Z   loop multi-scenario in one
                                                      COM session
                                  --readback-rows-per-region N
                                
                                §11.1 caveat: dry-run branch_not_found ≠ real
                                miss for some sectors. Investigate before
                                aborting the cycle.

9. CALCULATESCENARIO          → Manual LEAP UI run. Tens of minutes per scenario.
                                User triggers, we wait.

10. POST-CALC VALIDATE        → §4.1
                                - print_overview(db) clean
                                - check_scenario(db) → ok() or strict subset
                                - Targeted symptom verified gone

11. UPDATE AUTHORING ARTIFACTS → §6.1 + §6.2
                                 Update CSV_AUTHORING_GUIDE.md if anything
                                 learned. Run cross-domain protocol — does the
                                 lesson apply elsewhere? CHANGELOG bullet.

12. END-OF-TASK CHECKLIST     → §15.1
```

**Warm-COM rule** (CLAUDE.md §A.10): step 8 is one Python invocation,
not three. Restarting between dry-run and real-inject practically
means closing and re-opening LEAP — cache rebuild costs ~160s and
risks the spontaneous-blanking trap (§11.1). The framework keeps the
COM session alive across all phases and across all scenarios. Don't
fragment.

**Critical rules to remember during inject flow:**
- §A.15 — `Interp(...)` separator is enforced at 3 layers, all wired into
  the framework. Don't bypass.
- §A.9 — re-confirm area + scenario before EVERY COM operation. Even
  diagnostic probes.
- §A.10 — batch related COM operations into ONE Python invocation
  whenever possible. Cache reuse + state stability.
- §A.11 — never author `Unlimited` on lower-bound LEAP variables; on
  upper-bound vars prefer finite numerics.
- §A.13 — hypothesis discipline. Test smallest falsifier first. Don't
  claim "cause confirmed" without proof.

---

## 2. Results harvest flow — `.leap` → analysis CSVs

```
0. SECTOR TEAM DROP          → mailbox/<YYYYMMDD>/<area>.leap
                                (or post-calc .sqlite if results already exist)

1. CONFIRM LEAP TARGET       → §2.5 — area + scenario(s) to walk + region scope
                                + year scope

2. ROUTE                      → Clone mailbox/<date>/<area>.leap to
                                result/<YYYYMMDD>/

3. WRITE PROBE SUBCLASS       → result/<YYYYMMDD>/probe_<name>.py:
                                  from nemo_read.probe_base import CanonicalProber
                                  class MyProbe(CanonicalProber):
                                      PROBE_NAME = "my_full_area"
                                      EXPECT_AREA = "aeo9_v0.42_r1e"
                                      REQUIRE_EXPECT_AREA = True
                                      # Override scope hooks if needed
                                  if __name__ == "__main__":
                                      raise SystemExit(MyProbe().run())

4. WARM-COM PROBE CYCLE       → Launch in background via Bash run_in_background=True:
                                  python result/<date>/probe_<name>.py \
                                      --scenarios "BAS,ATS,RAS,CA" \
                                      --expect-area "aeo9_v0.42_r1e" \
                                      --out-dir result/<date>/
                                
                                Framework runs ALL of these in ONE COM session
                                (CLAUDE.md §A.10):
                                  a. dispatch_leap → area lock
                                  b. tree cache built once (~3 min, reused)
                                  c. for each scenario:
                                     - set+verify ActiveScenario (drift check)
                                     - Probe A: results per region × year
                                       (~50 min/scenario, popup-safe reads)
                                  d. Probe B: units once for the area (~4 min,
                                     BT={3,50} enforced by sealed _read_unit_text)
                                  e. final summary + heartbeat finish
                                
                                Background convention (§A.16):
                                  - Heartbeat stdout every 30s:
                                    [HB t=14:23:01 scenario=BAS region=Indonesia
                                       rows_written=4523 elapsed=27m04s]
                                  - Progress JSON file:
                                    _progress_<probe_name>_<ts>.json
                                  - Monitor: harness `Monitor` tool on the
                                    background shell, OR cat the JSON on demand
                                
                                Pitfalls already enforced by the framework:
                                  - 'Base Template' region excluded automatically
                                  - --years default = model milestones (2025-2060/5)
                                  - --skip-zeros default ON (cuts CSV ~10×)
                                  - BT={3,50} restriction for unit reads (§11.2)
                                  - safe_value / safe_data_unit_text everywhere

5. OFFLINE JOIN (optional)    → python join_results_with_units.py — ~5 sec
                                Output: joined_<scenario>.csv

6. CARRY FORWARD              → §7.5 SOP discoverability
                                Update RESULTS_HARVEST_SOP.md if new pitfalls
                                surfaced. Hoist load-bearing ones into CLAUDE.md
                                §11. Link from §9 docs map.

7. END-OF-TASK                → §15
```

**Why one invocation, not separate A + B + C runs:** CLAUDE.md §A.10.
Each Python exit kills the COM dispatch handle; reconnecting practically
means closing and re-opening LEAP. The framework keeps `dispatch_leap`
alive across all phases and scenarios. Tree cache built once (~3 min)
and reused. For a full-area probe of 4 scenarios:
  - **Old pattern:** 4× Probe A invocations + 1× Probe B + 4× Step C =
    9 separate Python runs, 9 COM dispatches, 4-5× tree cache rebuilds
  - **New pattern:** ONE Python invocation, ONE COM dispatch, ONE tree
    cache build, all phases warm

Use the full `nemo_read-leap-export` CLI instead when you need
**input-side data** beyond units, a **self-contained area dump** for
analysts without LEAP, or analysis beyond "what came out of this run".

---

## 3. Infeasibility triage flow — solver said INFEASIBLE

```
0. SOLVER SAID INFEASIBLE    → User reports xN/cN column-or-row index, calc year,
                                scenario name

1. PRE-FLIGHT                 → validate_scenario + find_infeasibilities +
                                check_scenario on the .sqlite.
                                Includes the general (r, f, y) fuel mass-balance
                                audit. Names contributing techs on both sides
                                of every imbalance.

2. (SOLVER RUN — already happened by the time we triage)

3. POST-MORTEM TRIAGE         → xN → decode_lp_column → vfamily[r, t, y]
                                cN → no offline row decoder; Stage 1's mass-
                                     balance output names the techs

4. PATTERN FORENSICS          → classify_parameter / forensics_for_pinned_variable
                                Each cluster classified bug / intent / unknown.

5. PLACEHOLDER PROPOSAL       → propose_placeholders, ranked
                                (blast_radius, −confidence, reverse-difficulty)

6. DIAGNOSTIC TEST            → inject_to_leap.py --placeholder-mode
                                ├─ solves           → cause CONFIRMED → Stage 9
                                ├─ same symptom     → wrong cluster, try next
                                └─ new symptom      → new loop on the new symptom

7. PROBE BRIEF                → emit_probe_brief — minimum LEAP COM read list
                                (Only if Stage 6 doesn't converge.)

8. LEAP COM PROBING           → Execute brief. Alternatives/parallel:
                                - Read existing inject files in inject/<domain>/
                                  (most variables already authored there)
                                - Read cached branch dumps
                                  (mailbox/<date>/_cache_dump_*.txt)
                                - Ask the relevant domain team in parallel

9. REAL-FIX DESIGN            → Manual, informed by Stages 4 + 6 + 8.
                                Bug + tech-broadcast scope → template branch
                                Bug + per-region scope     → per-region rows
                                Intent (decay/harvest)     → DO NOT TOUCH

10. PATCH INJECTION            → inject_to_leap.py — placeholder gate refuses
                                Stage-5 rows without --placeholder-mode.

11. VERIFICATION               → Loop back to Stage 1.
```

**Stage 1 gotcha (§A.12):** if `find_infeasibilities` returns clean
but solver still INFEASIBLE, **check Unmet Load slack
visibility/cost + inter-region trade routes for `MinShareProduction`
feedstock fuels BEFORE proposing another placeholder.** That's where
the 2026-05-13 RAS infeasibility was hiding. Two upstream classes
the Stage-1 detector doesn't currently catch:
1. `Transformation\Centralized Electricity Generation\Processes\
   Unmet Load_*` must be unhidden in Base Template + each region,
   with Variable OM Cost + Fixed OM Cost set.
2. `Key\Optimized Trade` enabled for any feedstock fuel referenced
   by a `MinShareProduction` row in a region with zero local
   capacity. Add trade routes per-region AND enable in active
   scenario.

**Retired diagnostic angles (do not propose):**
- LP file dumps (`writelpfile=true`) — never worked on this stack
- Custom-constraint tables (`__NEMOcc_*`) — never been the root cause
  on this codebase. (Other policy constraints CAN bind — see §A.12 —
  but that's `MinShareProduction` + trade routes, NOT `__NEMOcc_*`.)

---

## Cross-cutting rules (apply to all three flows)

These live at the top of CLAUDE.md (§A) for full visibility. Listed
here for quick reference:

- **§A.1** — never invent workflow steps from training data
- **§A.2** — narrow-interpret scope on every cleanup/removal instruction
- **§A.3** — don't iterate on failing LEAP COM probes
- **§A.5** — sweep broadly before drilling on infeasibilities
- **§A.6** — don't narrate plans; act
- **§A.9** — confirm LEAP state with user before any COM probe or inject
- **§A.10** — batch related LEAP COM operations into ONE Python invocation
  (`CanonicalInjector` + `CanonicalProber` enforce this for inject + probe)
- **§A.13** — hypothesis discipline (state, falsify, revert, never "confirmed" without proof)
- **§A.14** — cite the source for every LEAP/NEMO state claim, or hedge
- **§A.15** — Interp() must use comma list-sep + period decimal; framework enforces
- **§A.16** — long-running LEAP COM ops (>60s) run in background with
  heartbeat stdout + `_progress_*.json` file; both inject and probe
  frameworks wire this in automatically

All flows end with §15.1 (end-of-task checklist).
