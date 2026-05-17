# CLAUDE.md — guidance for Claude Code in this repo

> **Status.** This file is the operating brief for any Claude Code (or
> other agentic LLM) session working inside `nemo_read`. If something here
> conflicts with what the user just said, **the user wins** — update this
> file (or flag the conflict) rather than ignoring them. This file is a
> live document; see §15 for how it stays current.

---

## 0. STOP — READ §A FIRST, EVERY SESSION

These are HARD rules. Violating any of them has wasted the user's time
catastrophically in past sessions. They override anything else in this
file and override your training-data instincts. **You must update §A
whenever you discover a new destructive failure mode** — memory is not
durable enough; the failure has to land here, in this file, in the same
task as the discovery.

---

## §A. Reality-grounding hard rules (anti-hallucination)

**A.1 — Never invent workflow steps from training data.**
If you cannot grep-confirm a feature, command, flag, file, or
diagnostic path exists in *this* repo's code or docs, **it does not
exist**. Do not propose it. Do not claim it works. Ask the user before
asserting it. Burned 2026-05-11: I proposed `writelpfile=true` as a
CPLEX diagnostic step — was a hallucination from training (CPLEX/Julia
textbook content), never existed in this NemoMod build, wasted hours
of past sessions chasing it. Documented retirement list in §8.

**A.2 — Narrow-interpret scope on every cleanup/removal/change instruction.**
When the user names items to remove or change, the scope is **exactly
those items**. Not adjacent things that look fragile. Not items I just
experienced a failure with. Not the "broader cleanup the user probably
wants." If the user says X and Y, touch X and Y — nothing else. If you
think more should change, **stop and ask**, quoting the user's exact
words first. Burned 2026-05-11: user said "LP file + custom constraints
never work, why still in workflow"; I retired LP file, custom
constraints, **plus** probe brief and LEAP COM probing stages — neither
of those last two was in the user's message. The user described this
as "inventing things... destructive."

**A.3 — Don't iterate on failing LEAP COM probes.**
Each `LeapTreeCache` rebuild costs ~160s. Many failures are popup-modal
traps (§11.2) that stay on screen. If a probe fails, **stop**. Don't
write a "fixed" version and re-run it. Use cached dumps
(`mailbox/<domain>/<date>/_cache_dump_*.txt`), existing canonical
CSVs, prior inject logs, or **ask the user** what variable name /
branch path to use. Burned 2026-05-11: probed FAME branch, hit the
"Expressions are not used for result variables" popup, then queued a
second probe before the user stopped me.

**A.4 — NEVER read `Variable.Expression` or `Variable.DataUnitText`
on result-side variables.** Hard repeat of §11.2 because I keep
violating it. The COM call raises a modal popup ("Expressions are not
used for result variables") that stays on screen even when the error
is caught. Use `Variable.Name` only when enumerating; for value reads,
restrict to input-side variables on branch types `{3, 50}` and walk by
positional index (`Variables.Item(j)`), not by name lookup.

**A.5 — Don't depth-first chase the first quantitative anomaly.**
When triaging an infeasibility or any open-ended diagnosis, sweep
broadly first — run *every* applicable static check, list *every*
candidate bind, **then** drill. Burned 2026-05-11: spotted 190
suspicious `ActivityLowerLimit` rows on import techs, spent multiple
SQL probes chasing them before the user redirected me to bioenergy —
where the real bind (FAME × palm oil, 1034× shortfall) would have
appeared in the broad sweep on iteration one.

**A.6 — Don't narrate plans. Act.**
No numbered "Concrete plan:" lists, no "Let me X, then Y, then Z"
preambles, no recap tables when the user is asking you to act. State
the action in one sentence, then do it. Save structured write-ups for
when the user asks for one. Burned repeatedly 2026-05-11; user:
*"stfu why are you keep on talking in useless jargon."*

**A.7 — When you learn a new destructive failure mode, add it HERE
in §A, in the same task.**
Memories get ignored under load (proven by the fact that I had three
relevant memories on 2026-05-11 and violated all of them). The §A
list must grow with every destructive lesson. Do not bury new
destructive rules in `MEMORY.md` and call it done.

**A.8 — Don't edit CLAUDE.md, `docs/**/*.md`, or the methodology
files beyond what the user named.** These are durable artifacts. Mass
restructures wasted user time when I did them unprompted. If you're
adding to §A under rule A.7, that's allowed. Any other CLAUDE.md edit:
quote the user's exact words authorizing it before editing.

**A.9 — ALWAYS confirm LEAP state with the user before any COM probe
or inject.** This includes `--dry-run`. Spell out:
  1. Expected area (`leap.ActiveArea.Name` — confirm it matches what
     the script will `--expect-area`).
  2. Expected scenario (in the LEAP UI dropdown — confirm it matches
     RAS/CA/ATS/BAS or whatever the task targets).
  3. That the user has nothing else mid-flight in LEAP that the probe
     could interrupt.
Read the area name back to the user before launching: *"About to run
probe X against area Y, scenario Z. OK to proceed?"* — wait for an
explicit yes. Burned 2026-05-11: launched the bioenergy-infeas probe
without asking; LEAP's `ActiveArea.Name` came back as `''` (the §11.1
spontaneous-blanking trap), and the resulting probe output is now
ambiguous about which area state was queried. The user called this
out: *"hey remember everytime you are about to probe, you have to
confirm with me first whether the leap is ready and the scenario is
right first."* This rule overrides convenience — even short
diagnostic probes get the confirmation step.

**A.10 — Batch related LEAP COM operations into ONE Python invocation
once state is confirmed.** When you have to inject + verify, inject +
probe, multiple probes, or any other set of operations needing the
same area/scenario state, write them as a single Python script (or
chain them through the same `dispatch_leap()` session) and run that
once. Don't fragment across multiple `python ...py` invocations.

Why this matters:
  1. `leap.ActiveArea.Name` spontaneously blanks between Python
     invocations (the §11.1 trap — observed 3× on 2026-05-06 and
     once on 2026-05-11). One invocation = one stable state, locked
     and confirmed once.
  2. `LeapTreeCache` rebuild costs ~130–165 seconds each time.
     Reusing it across operations in the same script saves that.
  3. §A.9 confirmation is durable for the duration of one Python
     run; rebuilding it each call wastes user time.

Burned and learned 2026-05-11: pushing the FAME `Minimum Utilization=0`
placeholder and then probing `DataUnitText` on the same branches were
done as two consecutive Python runs the first time (placeholder push
succeeded, but the unit probe immediately afterward came up with
`ActiveArea.Name = ''` — the spontaneous-blanking trap fired in the
gap). Doing the *same* two operations as ONE Python invocation later
that day (placeholder p2 + unit probe) ran cleanly: ActiveArea stayed
locked to `'aeo9_v0.42_r1a'` throughout, cache was warm for the probe
(10s instead of 165s), zero drift. User locked it in as SOP: *"when
we do inject and probe we keep it running for multiple process, that
way area and scenario in leap wont wane or drift. we manage to both
inject and probe without any area or scenario issue, we have to
remember it and keep on doing it that way."*

How to apply:
  - **The `CanonicalInjector` framework enforces this for every inject.**
    Default flow: `dispatch_leap` once → area lock → for each scenario:
    set+verify → dry-run → confirm → real inject → readback. ALL in one
    Python invocation. See §5.1 + [docs/FLOWS.md §1](docs/FLOWS.md).
  - **The `CanonicalProber` framework enforces this for every probe.**
    Default flow: `dispatch_leap` once → area lock → tree cache built
    once → for each scenario: Probe A (results) → Probe B (units, once
    for the area). ALL in one Python invocation. See §7.1 +
    [docs/FLOWS.md §2](docs/FLOWS.md).
  - For multi-scenario operations, pass `--scenarios "RAS,CA,ATS,BAS"`
    to the inject or probe CLI — the framework loops scenarios in the
    same COM session. Don't run the script N times.
  - For one-off custom probes outside the framework: list every
    operation you'll need (inject A, probe B, inject C, read D) and
    write them as ONE script under `mailbox/<domain>/_probe_*.py`.
    Confirm state once at the top (§A.9), build the cache once, run
    every operation against the warm cache. Don't fragment across
    multiple `python …` invocations — each restart loses cache warmth
    (~160s rebuild) and risks the spontaneous-blanking trap (§11.1).
  - **Long-running ops (>60s) MUST use the heartbeat convention** (see
    A.16 below). Inject + probe frameworks already wire it in.
  - The injector accepts multiple rows in one CSV — use one CSV with
    everything, not multiple injections with multiple CSVs.

**A.16 — Long-running LEAP COM operations run in the background with
heartbeat + progress-JSON monitoring.** Any COM operation expected to
exceed ~60 seconds (multi-scenario inject, full-area probe, large
results harvest) is run via `Bash run_in_background=True` and reports
progress through the standardised heartbeat convention
([`nemo_read._heartbeat.HeartbeatLogger`](nemo_read/_heartbeat.py)).
Both channels run in parallel:

  - **Heartbeat stdout** — structured line every ~30s:
    `[HB t=14:23:01 scenario=BAS region=Indonesia rows_written=4523
    elapsed=27m04s]`. Monitor via the harness `Monitor` tool (streams
    stdout lines as notifications) or `tail -f` on a captured log.
  - **Progress JSON file** — `_progress_<op>_<ts>.json` updated on
    every tick. Read on demand:
    `python -c "from nemo_read._heartbeat import read_progress;
    import json; print(json.dumps(read_progress('path'), indent=2))"`.
    Contains scenario, region, rows_written, elapsed, last_heartbeat.

Both `CanonicalInjector.run()` and `CanonicalProber.run()` wire the
heartbeat in automatically — subclasses don't need to do anything.
For custom one-off COM scripts, instantiate `HeartbeatLogger` at the
top and call `.tick(**context)` whenever progress changes.

How to apply:
  - Launch any inject or probe that's expected to exceed 60s via
    `Bash run_in_background=True`. Avoid blocking the foreground.
  - When checking status: read the `_progress_*.json` file (cheap,
    at-rest) OR use the `Monitor` tool on the background shell ID
    (streams new heartbeats as they arrive).
  - Don't poll in a sleep loop — the heartbeat is the polling mechanism;
    you only need to check when the user asks or when the op completes.
  - On completion: the heartbeat emits `[HB-DONE ...]` to stdout AND
    writes a "finished" timestamp + summary to the JSON. The harness
    Bash background notifies on process exit.

**A.17 — Every mechanically-enforceable rule in CLAUDE.md MUST have
a pytest tripwire. Prose-only rules are systematically violated.**

This rule about rules. Established 2026-05-17 after two separate
prose-only-rule failures hit in the same session:
  - §A.15 Interp() separator: documented since 2026-05-07 as prose.
    Fossil canonical shipped `Interp(...; ...; ...)` anyway. User
    caught it at inject time. Tripwire: `tests/test_interp_separator.py`.
  - §14 public API re-export: documented since the package's start
    as prose. `CanonicalInjector`, `CanonicalProber`, `HeartbeatLogger`
    shipped without `__all__` entries. User caught it at install time.
    Tripwire: `tests/test_public_api_completeness.py`.

The pattern is identical:
  - Author focused on building the thing
  - Author satisfies the build-side test (the class works)
  - Author forgets the ritual that makes the thing usable downstream
  - Rule existed in prose; author didn't run the §15.1 end-of-task
    checklist explicitly; bug ships.

The cure is mechanical CI enforcement, not stricter prose.

How to apply:
  - **When proposing a new rule that has clear mechanical violation
    criteria** (e.g., "every X must have Y", "no Z anywhere outside
    W"), write the pytest tripwire in the SAME change that adds the
    prose rule. Never ship a mechanically-enforceable rule as prose
    only.
  - **When discovering a new violation of an existing prose rule**,
    add the tripwire in the same fix. Per §A.7, the destructive
    failure mode gets documented; per §A.17, it also gets enforced.
  - **Judgment-based rules** (§A.1, §A.2, §A.3, §A.5, §A.6, §A.9,
    §A.13, §A.14) cannot be CI-enforced. Those stay as prose —
    accepted residual risk.
  - **The existing tripwire roster** (as of 2026-05-17):
      `tests/test_interp_separator.py`       — §A.15 separator
      `tests/test_inject_base.py`            — §5.1 seal + chokepoint
      `tests/test_probe_base.py`             — §7.1 seal + BT={3,50}
      `tests/test_public_api_completeness.py` — §14 __all__ completeness
      `tests/test_claude_md_rules_enforced.py` — §10.2 version sync,
                                                §A.11 Unlimited-on-LB
  - **When adding a NEW rule** to this §A list that's mechanically
    enforceable, either extend an existing tripwire file or add a
    new one. Don't merge the rule prose without the test.

See also: `tests/test_claude_md_rules_enforced.py` docstring for the
audit of which §A rules have CI vs which are judgment-only.

**A.11 — `Unlimited` string in LEAP authoring is a landmine. LEAP→NEMO
export translates the literal `"Unlimited"` to `1.0e+12` regardless of
which variable.** Two failure modes, BOTH catastrophic:

  1. **Upper-bound variables** (`Maximum Production`, `Maximum Capacity`,
     `Maximum Imports`): some AMS export the cap as missing/zero
     instead of 1e12 (silent parse failure), leaving the supply chain
     UN-CAPPED → infeasibility from the other direction. Confirmed
     2026-05-12: `Maximum Production = Unlimited` on `Resources\Primary\
     Biomass`/`Wood` for 8 of 11 AMS exported broken; 3 AMS with
     numeric caps exported clean. p8 fix: replace with numeric 10000.
  2. **Lower-bound variables** (`Exogenous Capacity` → NEMO
     `ResidualCapacity`): 1e12 becomes a FORCED FLOOR. NEMO must
     carry 10¹² of that variable in the LP basis. Confirmed 2026-05-12:
     4 Blending pseudo-techs (Gasoline/Ethanol/Diesel/Biodiesel
     Blending) had `Exogenous Capacity = Unlimited` → ResCap=1e12 PJ.

Hard rules:
  - Never author `Unlimited` on any lower-bound variable. Use 0 if no
    floor needed, finite numeric if a floor is needed.
  - On upper-bound variables: prefer a generous numeric (10,000 or
    100,000) over `Unlimited`. The 1e12 sentinel pollutes LP
    conditioning (CPLEX tolerance ~10⁹) even when it "works".
  - **NEVER reflexively zero an existing `Unlimited`→1e12 sentinel
    on a lower-bound variable** without verifying the tech has
    alternate capacity sources (non-zero CapCost or non-NULL MaxCap).
    Burned 2026-05-12: p9 set EC=0 on the 4 Blending techs (all
    zero-cost, NULL MaxCap) → primal infeasibility went 24k → 4.6M
    (190× worse). Use finite-but-large (~100,000 PJ) instead.
  - Audit `Resources\Primary\*` and `Resources\Secondary\*` for
    `Maximum Production = Unlimited` before any major recalc cycle.

See also: `memory/reference_unlimited_1e12_trap.md` for the full
operational signatures + grep recipes.

**A.12 — Stage 1 audit clean ≠ structurally feasible. Always check
Unmet Load slack visibility AND inter-region trade routes for any
custom-constraint-mandated feedstocks BEFORE proposing another
placeholder.** When `find_infeasibilities` returns clean but solver
still INFEASIBLE, the bind is in a class our detector doesn't cover.
The two most common (load-bearing) classes:

  (a) **Unmet Load slack visibility and cost.** `Transformation\
      Centralized Electricity Generation\Processes\Unmet Load_*`
      branches must be UNHIDDEN in Base Template + each region, AND
      have `Variable OM Cost` + `Fixed OM Cost` set (typical 500).
      Without this, any unmet electricity demand → INFEASIBLE
      instead of solved-with-high-cost. Node-specific variants exist
      for sub-region-decomposed AMS (Indonesia IDJW/IDSA/IDKA/IDEast,
      Malaysia MYPE/MYSB/MYSR) — all must be unhidden + priced.
  (b) **Inter-region trade routes for fuels referenced by
      `MinShareProduction` blend mandates.** When a region has B47/E37
      blend mandates but zero local feedstock capacity (Indonesia
      Sugarcane=0, Vietnam/Laos/Timor Leste Palm Oil=0, etc.), the
      model needs `Key\Optimized Trade` enabled for the feedstock fuels
      (Ethanol, Biodiesel, Coconut Oil, Palm Oil, POME, Cassava,
      Molasses, Sugarcane, Corn) to import from surplus AMS. Trade
      routes must be added per-region AND enabled in the active
      scenario.

Resolved 2026-05-13 on `aeo9_v0.42` RAS: the 24k residual primal
infeasibility cleared after (a) + (b) plus the Optimized Trade plug-in
+ removing the legacy `add_trade_routes` function from the
before-scenario script. Previous diagnostic angles (4 Blending 1e12
ResCap, RMTag on non-power techs, biogenic CO2 EAR 4e7 magnitudes)
were real data quality issues but NOT the structural cause.

How to apply:
  - When `find_infeasibilities` returns clean and solver is still
    INFEASIBLE: STOP. Do not write another placeholder. Audit:
      1. Every Unmet Load branch in Centralized Electricity
         Generation — unhidden? Variable OM Cost set? Fixed OM Cost
         set? Node-specific variants present for IDxx/MYxx?
      2. For each `MinShareProduction` row, name the feedstock fuel
         (via the constrained tech's IAR). Confirm `Key\Optimized
         Trade` is enabled for that fuel and that all regions with
         the mandate have trade routes configured.
  - Only after these come back clean: move to Stage 1 detector
    extension (storage chain, per-mode balance, per-timeslice balance).

See also: `memory/feedback_stage1_clean_not_enough.md` and
`memory/project_aeo9_v042_RAS_resolved.md` for the burn record.

**A.13 — Hypothesis discipline. State hypothesis, propose smallest
falsifying test, await result. NEVER claim "found the cause" without
proof from a successful test.** Burned multiple times 2026-05-12:

  - Claimed F26 AAD source = Other Biomass cooking Remainder → user
    moved Remainder to Wood → infeasibility 24k → 1.27M (53× worse).
  - Claimed 1e12 ResCap on Blending was the bind → pushed p9 EC=0 →
    infeasibility 24k → 4.6M (190× worse).

The pattern: data anomaly visible in SQLite → plausible mechanism
story → declared "the cause" → injected fix → made worse. Each test
disproved the hypothesis, but the over-statement misled the user.

How to apply:
  1. Frame: "hypothesis, not proven" — quote the anomaly, name the
     mechanism, but do not say "this is the bind" or "found it".
  2. Before pushing any fix: write the smallest, most reversible test
     that would FALSIFY the hypothesis. Push that, then wait.
  3. If the test makes things worse: hypothesis was wrong. Revert.
     Move to next candidate. Do not double down with another fix in
     the same direction.
  4. If the test partially improves: hypothesis was partial. Don't
     claim it's "the" cause — there's more.
  5. The most expensive mistake is confident wrongness. Better to
     under-claim and over-test than the reverse.

This is on top of §A.5 (sweep broadly before drilling) — A.5 is
about scope, A.13 is about discipline once a candidate is in view.

See also: `memory/feedback_hypothesis_discipline.md` for the full
2026-05-12 burn record (Wood reroute + p9 EC=0).

**A.14 — Cite the source for every LEAP/NEMO state claim, or hedge.**
Before asserting "X is set to Y", "X is missing", "X exists where I
expect it", "the inject did/did not land", or any other factual claim
about LEAP authoring or NEMO export contents, the claim must cite the
*direct* data source backing it:
  - NEMO-side claim → quote the SQLite SELECT row (or row absence) on
    the exact table/parameter being claimed about.
  - LEAP-side claim → quote a COM-probe read of `Variable.Expression`
    (or the user's eye-test read of the LEAP UI cell).
  - Mailbox/canonical claim → quote the actual row from the CSV (or
    its absence in a grep).

**CLAUDE.md mapping tables (§2.3), naming-convention patterns
(`S{NN}I = Imports`), and architectural mental models are STARTING
HYPOTHESES, never facts about a specific area.** If the claim cannot
cite a direct query result, the claim MUST be hedged ("hypothesis,
not yet verified" / "extrapolated from §2.3, would need to probe").
Never present an extrapolation in the same register as a verified fact.

Burned 2026-05-13 (the same petroleum-import-cost investigation), in
sequence — each claim sounded plausible from CLAUDE.md + convention,
each was wrong:
  (i) "petroleum Import Cost rows need `\<Fuel> Imports` suffix in the
      LEAP path" → COM probe found those sub-branches do not exist
      anywhere in `Resources\Secondary` — all 33 secondary fuels are
      flat BT=15 leaves with zero children;
  (ii) "the inject silently failed to push our fossil canonical for
       Singapore Gasoline Import Cost" → user's eye-test of the LEAP
       UI cell showed an `Interp(...)` expression IS authored on
       `Resources\Secondary\Gasoline:Import Cost`;
  (iii) "the 1.5899× factor between LEAP-displayed value and our
        canonical proves the same trajectory in different units" →
        also extrapolation; cannot be confirmed without reading the
        variable's `DataUnit` setting (USD/bbl vs USD/100L).

Each "wrong-but-plausible" claim cost the user time and trust.

How to apply: when an answer feels obvious from CLAUDE.md mapping,
**stop and ask "what query would prove this?"** — then either run it,
or hedge the answer. The phrasing of an unverified claim should make
the unverified-ness load-bearing, not buried in a clause.

See also: `memory/feedback_cite_or_hedge.md` for the full burn-log
detail.

**A.15 — LEAP `Interp(...)` expressions: comma list-separator + period
decimal is the ONLY accepted form on this engine. No exceptions, no
domain-specific variants.** The canonical form for every authored
expression — in raw input CSVs, canonical CSVs, and anything injected
via `inject_to_leap.py` / `Variable.Expression`:

```
Interp(2025, 3.2422, 2030, 3.0833, ...)
       ^^^^                              comma between args
            ^                            period for decimal
```

Both this Windows install (`Get-Culture` → en-US) and LEAP's own
regional setting use comma-as-list, period-as-decimal. Any other
form is wrong, regardless of how plausible it looks:
  - `Interp(2025; 3.2422; ...)` (semicolon list-sep) — wrong
  - `Interp(2025; 3,2422; ...)` (semicolon + comma decimal) — wrong
  - `Interp(2025. 3.2422. ...)` (period list-sep on read-back) —
    indicates the inject committed wrong, not a display quirk

Burned 2026-05-17: the bioenergy canonical correctly used commas, but
the fossil canonical (`inject/fossil/canonical_leap_inputs.csv` +
`canonical_leap_native.csv`, plus 3 raw input CSVs feeding them) had
~300 `Interp(...; ...; ...)` rows on semicolon list-sep. The wrong
form had leaked in via
[`inject/fossil/build_canonical.py:74`](inject/fossil/build_canonical.py#L74)'s
hardcoded `"; ".join(...)` AND raw-author CSVs (`coal_supply_costs.csv`
etc.) authored that way. The fossil inject log was missing, so it's
unknown whether the bad form ever committed cleanly — the user
called it out before another push could happen. *"why you have
varying rules? ... we cant possibly keep on making the same
mistake."*

How to apply — there is now a three-layer enforcement stack. If you
are adding a new mailbox domain or touching any inject path, **route
through it**; do not invent a parallel path.

  **Layer 1 — Adapter normalisation (write-time).** Every domain's
  `build_canonical.py` (and `run_workflow.py` step 4 where it exists)
  must call `nemo_read._leap_com.normalize_interp(expr)` on the
  `expression` column before writing the canonical CSV. Fossil,
  bioenergy, and power adapters all do this as of 2026-05-17.
  Catches mis-typed semicolons in raw input CSVs.

  **Layer 2 — `CanonicalInjector` framework + universal chokepoint.**
  Every sector's injector MUST subclass
  `nemo_read.inject_base.CanonicalInjector` (see §5.1). The framework
  owns `_set_expression` as a sealed method that routes through
  `safe_set_expression`. Subclasses cannot override sealed methods
  — `__init_subclass__` raises `InjectorSealError` at class
  definition. The `tests/test_inject_base.py` CI scan rejects any
  `var.Expression = expr` site under `mailbox/**/*.py`. Bioenergy /
  fossil / power are all thin subclasses (~50 lines each) of the
  framework as of 2026-05-17. **A new domain that writes a
  hand-rolled injector instead of subclassing — or that adds a
  `Variable.Expression =` write anywhere in `mailbox/` — fails CI.**

  **Layer 3 — Pre-flight CSV scan.** Every injector calls
  `validate_canonical_csv_expressions(csv_path)` at startup and
  refuses to proceed (non-zero exit) if any row contains a
  forbidden Interp() form. Catches batch problems before any COM
  state is touched.

  **Plus: post-inject readback.** Run
  [`result/20260505/_probe_readback_one.py`](result/20260505/_probe_readback_one.py)
  after every push. NORMALISED matches (commas got renormalised to
  periods on read-back) are now a HARD FAIL — exit code 1, do NOT
  proceed to `calculatescenario`.

  **Plus: pytest regression**
  ([`tests/test_interp_separator.py`](tests/test_interp_separator.py))
  pins all of the above plus a smoke test that scans every committed
  canonical CSV — re-introducing the wrong form anywhere fails CI.

If you find yourself writing code that bypasses any of these layers
because "it's just a quick fix" — stop. The fossil-domain incident
happened because the rule was documented but unenforced. Defense in
depth is the entire point.

See also: `memory/reference_leap_separator_convention.md` for the
full origin (2026-05-07 v0.38 read-back discovery + 2026-05-17
fossil burn).

---

## §0. Starting cold? Read in this order

A fresh session, in 60 seconds:

0. **§A above — Reality-grounding hard rules.** READ FIRST. EVERY SESSION.
1. **`TODO.md` at the repo root, if present.** Cross-session pickup
   note: where the previous session left off and what's not done yet.
   Read it before forming a plan; it tells you the in-flight cycle's
   state without needing to grep logs. (Harmless if absent.)
2. **§2 — Hard rules (modeling).** Five modeling-specific standing
   rules. Don't violate them.
3. **§3 — Repo layout.** Two halves: `nemo_read/` (library) +
   `mailbox/` (authoring pipeline + dated drops).
4. Pick the workflow that matches the task:
   - **§4 — Mailbox workflow** (CSV → inject upstream into LEAP)
   - **§7 — Results harvest SOP** (read calculated results out of LEAP)
   - **§8 — 11-stage infeasibility methodology** (solver said it broke)
5. **§15 — End-of-task checklist.** Run through this before saying "done."

Then: skim `MEMORY.md` (auto-loaded) for user preferences, glance at
`CHANGELOG.md`'s most recent section to know what just shipped, and
proceed.

---

## 1. What this repo is

`nemo_read` is a Python library + CLI suite that **reads, decodes, and
analyses LEAP-generated NEMO scenario SQLite databases**, and **authors
patches that flow upstream into LEAP** (never down into the .sqlite).

Two halves:

1. **Reader / analyser** — `nemo_read/` package. Pure-Python, runs anywhere.
   Targets NEMO data-dictionary v11 (LEAP 2024+, NemoMod 2.0+); reads v9/v10
   with graceful degradation.
2. **Mailbox / authoring pipeline** — `mailbox/<domain>/` (currently
   `bioenergy/` and `fossil/`). Each domain has a hand-authored CSV
   (`*_leap_input.csv`), a `build_canonical.py` adapter that normalises it
   to `canonical_leap_inputs.csv`, and `inject_to_leap.py` which pushes the
   canonical rows through LEAP's COM API.

Read [README.md](README.md) and [BROCHURE.md](BROCHURE.md) for the public
pitch; this file is for the operator inside the repo.

---

## 2. Hard rules — read these before doing anything

These mirror standing memories the user has set. Treat them as binding.

### 2.1 Never patch the NEMO SQLite directly
The `.sqlite` is a **build artifact** of LEAP's `calculatescenario`.
Editing it with raw SQL is forbidden, even when "just to test." All fixes
flow upstream:

```
hand-authored CSV  →  build_canonical.py  →  canonical CSV
                                                  ↓
                                          inject_to_leap.py
                                                  ↓
                                              LEAP (COM)
                                                  ↓
                                       calculatescenario
                                                  ↓
                                          new .sqlite
```

If you're tempted to write `UPDATE SpecifiedAnnualDemand SET val = ...`,
stop. Author a row in the relevant mailbox CSV instead, or — for
diagnostic-only experiments — generate a Stage-5 placeholder row (see §8).

### 2.2 Use LEAP names in user-facing answers, not NEMO IDs
NEMO uses opaque codes: `R19`, `P16166`, `L_AnnualTimeSlice`, `F123`.
LEAP uses human names: `Philippines`, `Sugarcane`, `Annual`, `Diesel`.

- **Inside SQL snippets and code:** raw IDs are fine.
- **In prose, tables, summaries, error explanations:** always translate
  back via `REGION.desc`, `TECHNOLOGY.desc`, `FUEL.desc`,
  `TIMESLICE.desc` (or use `decode_dims(df, db)` which does the join for
  every standard dim column).

### 2.3 Answer in *both* NEMO and LEAP terminology
When prose touches a NEMO parameter or table, pair it with the LEAP-side
equivalent so the modeller (LEAP-native) and the analyst (NEMO-native)
can both follow.

**Mapping verified against the AEO9 LEAP version (2026-05-11)** — every
LEAP variable name below has been grepped out of active
`mailbox/<domain>/canonical_leap_inputs.csv` files and is known to
inject cleanly. This table is the canonical reference for new injects;
do not invent names. (User instruction 2026-05-11: *"match the claude
md with the canonical insert. bcs this leap version is what we are
going to use."*)

**Process branches** (`Transformation\<Sector>\Processes\<Tech>`):

| NEMO side | LEAP side (verified) |
|---|---|
| `ResidualCapacity` | `Exogenous Capacity` (the year-by-year exogenous fleet that flows through to NEMO) |
| `CapitalCost` | `Capital Cost` |
| `VariableCost` (on process) | `Variable OM Cost` |
| `VariableCost` (on Feedstock Fuels sub-branch) | `Fuel Cost` (on `…\Processes\<Tech>\Feedstock Fuels\<Fuel>`) |
| `FixedCost` | `Fixed OM Cost` |
| `OperationalLife` | `Lifetime` |
| `InterestRateTechnology` | `Interest Rate` |
| `AvailabilityFactor` | `Maximum Availability` |
| `MinimumUtilization` | `Minimum Utilization` (1:1) |
| `TotalAnnualMaxCapacity` | `Maximum Capacity` |
| `InputActivityRatio` | `Process Efficiency` (input side) |
| `OutputActivityRatio` | `Process Efficiency` (output side) |
| `EmissionActivityRatio` | `<Pollutant> (process)` on `…\Processes\<Tech>\Auxiliary Fuels\<F>\<Pollutant>` (CO2, CH4, N2O, NOx, SO2, NH3, NMVOC, "CO2 biogenic") |
| `ReserveMarginTagTechnology` | `Capacity Credit` |
| (LEAP-internal building blocks that don't directly map but inform `Exogenous Capacity`): | `Existing Capacity`, `Capacity Additions`, `Capacity Retirement`, `Historical Production` |
| (LEAP result variables — never read `.Expression` on these; §11.2): | `Energy Generation`, `Power Generation`, `Capacity Added`, `Curtailed Energy Production`, `Pollutant Loadings`, `Costs of Production`, `Inputs` |

**Resource branches** (`Resources\Primary\<Crop>` and
`Resources\Secondary\<Fuel>`):

| NEMO side | LEAP side (verified) |
|---|---|
| `TotalTechnologyAnnualActivityUpperLimit` (on `S{NN}D` Domestic Production tech) | `Maximum Production` on `Resources\Primary\<Crop>` (raw-crop tonnes per §2.4) |
| `TotalTechnologyAnnualActivityUpperLimit` (on `S{NN}I` Imports tech) | `Maximum Production` on `Resources\Secondary\<Fuel> Imports` (or equivalent imports sub-branch — verify per-fuel) |
| `VariableCost` (on `S{NN}D`) | `Production Cost` on `Resources\Primary\<Crop>` |
| `VariableCost` (on `S{NN}I`) | `Import Cost` on `Resources\Primary\<Crop>` or `Resources\Secondary\<Fuel> Imports` |
| (LEAP land-cap building blocks — not directly NEMO-mapped, see §2.4): | `Area Harvested`, `Crop Yield`, `Additions to Reserves`, `Export Benefit` |

**Demand and effects branches:**

| NEMO side | LEAP side (verified) |
|---|---|
| `SpecifiedAnnualDemand` + `SpecifiedDemandProfile` | Demand branch annual value + Load Shape |
| `EmissionsPenalty` (negative on sequestered emissions) | `Externality Cost` on `Effects\Sequestered Carbon Dioxide` |
| `__NEMOcc_*` tables | Custom Constraint host branches + `customconstraints.txt` |

**When the canonical doesn't have what you need:** the only durable
truths are this table + the unique-variable list in the canonical
CSVs. If you suspect a different LEAP variable name applies to your
target, grep across `mailbox/**/canonical_leap_inputs.csv` first; only
COM-probe if grep returns nothing. Adding a new mapping entry: confirm
the LEAP name by reading at least one canonical row that uses it, then
add the entry here with the verification date.

### 2.4 Bioenergy: land-resource modelling pattern
Perennial / Arable land are intentionally modelled as **GJ-equivalent
Primary fuels with a 1 GJ/ha anchor**, producing a deliberate
**double-cap** (land cap + per-crop yield projection). This is *not* a
modelling bug to be "cleaned up." If a fix you're proposing collapses
that double-cap, escalate to the user before changing it.

Single-cap design (current truth, see
[inject/bioenergy/CSV_AUTHORING_GUIDE.md](inject/bioenergy/CSV_AUTHORING_GUIDE.md)
§0): `Resources\Primary\<Crop>:Maximum Production` is the **sole**
crop-supply cap, authored in **raw-crop tonnes** (FFB / cane / fresh root /
nuts-in-shell / grain), not extracted-product tonnes. Off-limits in this
domain: `Resources\Primary\Arable|Perennial`, every Cultivation-process
`Maximum Capacity` / `Variable OM Cost` row, and "Co-product Credit
(audit)" rows.

### 2.5 Confirm the target LEAP area / scenario / .sqlite before reading or writing

Multiple LEAP areas and scenarios coexist on disk — across `infeas/`,
`mailbox/<YYYYMMDD>/`, dated drops, sibling repos. Operating on the
wrong one wastes a `calculatescenario` cycle (tens of minutes) at best
and corrupts the wrong area at worst. **Confirm with the user before**:

| Operation | What to confirm |
|---|---|
| `inject_to_leap.py` — *any* mode, including `--dry-run` | LEAP area filename + `ActiveScenario` name + that the area is currently open in LEAP |
| `inject_to_leap.py --placeholder-mode` | Same as above + that the user knows this is a Stage-6 diagnostic, not a real fix (§8) |
| `nemo_read-leap-export` | LEAP area filename + which scenario(s) to walk |
| Results-harvest probes (`probe_leap_results.py`, `probe_leap_units.py`) (§7) | LEAP area filename + scenario name + branch-prefix scope |
| `NemoDB("...")` for non-trivial analysis | Which `.sqlite` — full path, since there are typically several plausible candidates (e.g. `infeas/NEMO_25 10.sqlite`, `mailbox/<date>/aeo9_v0.36.leap`-derived export, etc.) |
| Triggering `calculatescenario` over COM | Which scenario to run — never assume the active one |

Skip the confirmation only when the user has explicitly named the target
file/area/scenario within the current session **and** no plausible
context-switch has happened since. Defaults to ask. The injector's
ActiveArea-lock (§11) is a backstop, not a substitute for asking.

The format to use when asking:

> Before I run this, confirm:
> - LEAP area: `<filename or "AEO9 v0.36">`
> - Scenario: `<scenario name>`
> - Target .sqlite (for SQL reads): `<full path>`

If the user has named these in the current session, echo them back in
your "about to run" line so they can correct you in one word if you've
drifted.

---

## 3. Repository layout (operator view)

> **Quick reference for the three standardised flows** (inject /
> results harvest / infeasibility triage):
> [docs/FLOWS.md](docs/FLOWS.md). New sessions should skim this
> doc once before doing any flow-shaped work — saves re-deriving
> the canonical step sequence.


```
nemo_read/
├── pyproject.toml                  setuptools, version, scripts, extras
├── README.md / BROCHURE.md         public-facing
├── CHANGELOG.md                    keep current — used as release notes
├── CLAUDE.md (this file)           operator brief — keep current (§15)
├── nemo_read/                      library source (flat layout, no src/)
│   ├── __init__.py                 public API surface — keep __all__ accurate
│   ├── db.py                       NemoDB connection wrapper
│   ├── schema.py                   frozen NEMO v11 schema metadata
│   ├── dimensions.py / parameters.py / variables.py
│   ├── timeslice.py / export.py / custom.py
│   ├── leap_conventions.py         units, ID extraction, D/P/S classifier
│   ├── leap_area.py                LEAP-export-directory consumer
│   ├── leap_export.py              the COM-walking exporter (Windows only)
│   ├── leap_branch_inspect.py / leap_units.py    CLI helpers
│   ├── _leap_com.py                COM dispatch + LeapTreeCache + safe_*()
│   ├── validate.py                 structural + invariant checks (Stage 1)
│   ├── infeasibility.py            static infeasibility detector (Stage 1)
│   ├── lp_column_decode.py         Stage 3 — xN → (var, r, t, y)
│   ├── parameter_forensics.py      Stages 4 + 5 — detectors + placeholders
│   ├── probe_brief.py              Stage 7 — minimum LEAP COM probe brief
│   ├── trace.py                    cost / result decomposition + bound check
│   ├── unit_conversions.py         defensible factors with citations
│   ├── inspect.py                  print_overview, inspect_scenario
│   └── scaffold.py                 nemo_read-scaffold CLI
├── mailbox/                        pure INBOX — sector teams drop files here.
│                                   Cleaned at every stage commit after files
│                                   are routed. See MAILBOX_ROUTING.md.
├── inject/                         OUTBOX → LEAP. One subdir per sector.
│   ├── bioenergy/                  domain — see CSV_AUTHORING_GUIDE.md
│   ├── fossil/                     domain — coal/gas/oil supply + cost rows
│   └── power/                      domain — electricity generation tech rows
├── result/                         OUTBOX ← LEAP. One subdir per harvest cycle.
│   └── <YYYYMMDD>/                 probes + result CSVs + joined CSVs + SOP
├── tests/                          pytest suites — keep green
├── docs/                           topic references (see §9)
└── infeas/                         scratch DBs for live infeasibility runs
```

The inbox → inject/result routing ritual is documented in
[MAILBOX_ROUTING.md](MAILBOX_ROUTING.md). Established 2026-05-17
(workstream 2 reorg) so the previous overloaded `mailbox/`
(authoring + harvest + raw drops all mixed) becomes three
single-purpose directories with clear lifecycles.


Convention note: this repo follows the **tyuwono PyPI template** —
flat layout (package directory at root, *no* `src/`), `pyproject.toml`
with setuptools, Apache-2.0, tag-driven publishing via GitHub Actions
trusted publishing. Sibling repos look the same; reuse the pattern.

---

## 4. The mailbox / authoring workflow (write-side: CSV → LEAP)

> **Canonical step-by-step:** [docs/FLOWS.md §1](docs/FLOWS.md).
> This section retains the prose rationale; the doc has the numbered
> sequence with cross-references.

When the user asks you to "fix the bioenergy CSV" or "add a new fossil
import-cost trajectory," this is the loop:

0. **Confirm the target** — area, scenario, and `.sqlite` (§2.5).
   Don't skip; this is the front-line check against operating on the
   wrong file.
1. **Author or edit the input CSV** under the right domain
   (`inject/bioenergy/bioenergy_leap_input.csv`,
   `inject/fossil/<topic>.csv`, etc.). Match the column conventions in
   the domain's `CSV_AUTHORING_GUIDE.md` / `<DOMAIN>_CSV_SPEC.md`
   exactly. Before a structural rewrite, snapshot a backup as
   `<filename>.bak_pre_<YYYYMMDD>` so a later cycle can diff.
2. **Run `build_canonical.py`** in that domain to normalise the input
   into `canonical_leap_inputs.csv` (region expansion, unit alignment,
   audit-only filtering).
3. **Dry-run the injector first** — every time:
   ```
   python mailbox/<domain>/inject_to_leap.py --dry-run
   ```
   Don't drop `--dry-run` until the user has eyeballed the diff.
4. **Push for real** with the actual run, scoping with `--filter-ams`,
   `--filter-variable`, `--filter-fuel`, `--scenario` as needed. Capture
   the run log (`_inject_log_<YYYYMMDD>.txt` is the established prefix).
5. **Re-run `calculatescenario` in LEAP** to produce a fresh `.sqlite`,
   drop it into `infeas/`, then **verify** (§4.1).
6. **Reflect cross-domain** (§6) — does what you just learned apply to
   any other domain's authoring guide?

### 4.1 Verification — what "it worked" actually means

Don't declare a mailbox push successful until all of these hold:

- [ ] **Injector summary clean.** No `[FAIL]` lines; per-row outcome
      counts match what the canonical CSV's row count predicts.
- [ ] **Read-back-one verify** (lightweight, sub-second). Pick one
      representative branch from the inject CSV, set `ActiveScenario` +
      `ActiveRegion` to match the inject target, read
      `Variable.Expression` via COM, diff against the row's `expression`
      field. Should be byte-exact. Catches injector misroutes (wrong
      scenario, wrong branch path resolution, scenario inheritance not
      doing what you expect) before the much heavier post-calc
      verification suite below. One COM read per push, ~0.5s — no
      reason to skip.
- [ ] **`print_overview(db)` runs clean** on the post-calc `.sqlite`
      with no new validation issues compared to the previous baseline.
- [ ] **`check_scenario(db)` returns `ok()`** — or, if it doesn't, the
      remaining issues are *strictly a subset* of the issues that
      existed before this push.
- [ ] **The targeted symptom is gone.** If this push was meant to clear
      `Infeasible column 'xN'`, decode the new failing column (if any)
      and confirm it's a different cluster — not the same one with a
      slightly different value. If it solves, even better.
- [ ] **No placeholder rows leaked into the final push.** Re-grep the
      canonical CSV for `PLACEHOLDER` and the injector log for
      `--placeholder-mode`. Stage-6 diagnostic rows should never end up
      in a Stage-10 real-fix run.

If any check fails, this is *not* a successful push — even if the
solver eventually solved. Roll back, learn, retry.

### 4.2 Naming conventions inside a mailbox domain

- `_*.py` and `_*.txt` — scratch probes & findings. Lifecycle in §12.
- `*.bak_pre_<YYYYMMDD>` — backup of an authored CSV before a structural
  rewrite. Keep until the new shape has been validated end-to-end, then
  the user may prune.
- `_inject_log_<YYYYMMDD>[_v<N>].txt` — captured stdout/stderr from a
  real injection run. Useful retroactively when a downstream issue
  appears days later.
- `<YYYYMMDD>/` (top-level under `mailbox/` or under a domain) — dated
  incoming drops from the user (raw LEAP exports, result CSVs, fresh
  authoring drafts). Treat as read-only inputs — never edit in place.

---

## 5. Adding a new mailbox domain

When a new sector needs its own authoring pipeline (say,
`mailbox/electricity/`), match the established shape so all domains stay
operable from the same mental model:

```
mailbox/<domain>/
├── <DOMAIN>_CSV_SPEC.md          owner-facing spec (column shapes)
├── CSV_AUTHORING_GUIDE.md        adapter behaviour + canonical schema +
│                                 Cross-Domain Learnings section (§6.3)
├── <domain>_leap_input.csv       hand-authored input (owner format)
├── build_canonical.py            adapter → canonical_leap_inputs.csv
├── canonical_leap_inputs.csv     output: ready for injection
├── canonical_leap_native.csv     parallel canonical in NEMO-native units
├── inject_to_leap.py             thin CanonicalInjector subclass (see §5.1)
├── run_workflow.py               one-shot driver: build → dry-run → push
└── unit_audit.csv                per-row unit-conversion audit trail
```

### 5.1 The injector MUST subclass `nemo_read.inject_base.CanonicalInjector`

Established 2026-05-17 after the fossil-domain Interp() separator
incident proved that one injector per sector with copy-pasted COM
code is a recipe for the same bug to leak in every new sector.
`CanonicalInjector` is the standardised framework: every LEAP-side
rule (Interp separator §A.15, area/scenario lock §11.1+§A.9,
placeholder gate, `safe_set_expression` chokepoint, CSV pre-flight)
lives in the base class. Each sector contributes only the
domain-unique pieces via narrow override hooks.

**Minimum viable subclass** (~10 lines of sector code, everything else
inherited):

```python
from nemo_read.inject_base import CanonicalInjector

class MySectorInjector(CanonicalInjector):
    SECTOR_NAME = "mysector"
    DEFAULT_CSV = Path(__file__).parent / "canonical_leap_inputs.csv"
    REQUIRE_EXPECT_AREA = True  # if §A.9 area-confirmation is mandatory

    def filter_rows(self, rows, args):
        return [r for r in rows if not r["branch"].startswith("TBD\\\\")]

if __name__ == "__main__":
    raise SystemExit(MySectorInjector().run())
```

**The framework owns** (sealed — subclass override raises
`InjectorSealError` at class definition):
- `_set_expression` — the only sanctioned `Variable.Expression =` site
- `_preflight_csv` — Interp() scan + extra validators
- `_assert_area_lock` / `_assert_scenario_lock` — drift detection
- (placeholder gate logic in `run()`)

**The subclass overrides** (open hooks):
- `filter_rows(rows, args)` — sector row filtering
- `extra_cli_args(parser)` — sector CLI flags
- `extra_csv_validators()` — extra pre-flight checks
- `group_by_region(rows)` — region iteration strategy
- `cache_for_region(leap, region)` — tree-cache strategy
- `before_push_row(leap, row, args)` — per-row pre-hook
- `post_push_verify(committed, leap)` — readback hook
- `is_placeholder_row(row)` — sector-specific placeholder detection

**Reference subclasses to copy from:**
- [bioenergy](inject/bioenergy/inject_to_leap.py) — simplest (default
  per-AMS region grouping)
- [fossil](inject/fossil/inject_to_leap.py) — adds LEAP-native unit
  gate via extra_csv_validators
- [power](inject/power/run_workflow.py) — overrides group_by_region
  for 3-cache pattern, before_push_row for per-row ActiveRegion

**Never** write `var.Expression = expr` directly in a sector script —
the pytest regression
[tests/test_inject_base.py](tests/test_inject_base.py) scans every
`mailbox/**/*.py` file for that pattern and fails CI if found
outside the sanctioned chokepoint.

**Existing scratch utilities** (`run_workflow.py` step 4 conversion,
ad-hoc probes) may still talk to LEAP COM directly — they're not
inject paths. But anything that ends with a `Variable.Expression`
write goes through the framework.

---

## 6. Authoring guides — maintenance & cross-domain learning

Each mailbox domain ships a `CSV_AUTHORING_GUIDE.md` (and often a
`<DOMAIN>_CSV_SPEC.md`). These are the contract between the human author
and the `build_canonical.py` adapter. They drift out of sync the moment
adapter behaviour changes — and a stale guide is worse than no guide.

### 6.1 When you MUST update the relevant `CSV_AUTHORING_GUIDE.md`

In the **same change** as the code/data shift:

- Adapter (`build_canonical.py`) changes its transformation logic.
- A canonical-schema column is added / removed / renamed.
- A unit convention changes (e.g., bioenergy's switch to raw-crop tonnes
  from extracted-product tonnes).
- A previously-allowed pattern is now forbidden — extend the
  "Out of scope" / off-limits branch list.
- A real failure mode was learned — record it inline near the section
  it relates to, with a date and one-line "what went wrong, what fixed
  it." (See bioenergy guide §0's "supply-basis convention" note for the
  established shape.)
- A new domain-specific terminology rule emerges that affects
  user-facing answers (extend §2.3's mapping table here AND in the
  guide).

If the adapter behaviour ships without the guide update, the next
author silently produces wrong CSVs. The guide update is not optional.

### 6.2 Cross-domain learning protocol

Authoring guides are not independent — the lessons rhyme. Bioenergy and
fossil both author supply-side rows on `Resources\Primary\…` branches;
both run through identical injector machinery; both are vulnerable to
the same classes of mistake (unit-basis mismatch, region-name
inconsistency, placeholder leakage, branch-path typos that resolve to
the wrong tree node).

Whenever a lesson lands in one domain, classify it before stopping:

| Lesson scope | Action |
|---|---|
| **Domain-specific** (e.g. "FFB vs palm oil basis" — only meaningful for crops) | Document only in that domain's guide. Note in CHANGELOG `### Documented`. |
| **Systemic principle** (e.g. "any supply cap and its companion per-unit cost row must share the same physical basis on the same branch") | Document the principle in **every** domain's guide; in each, state whether this domain has the same risk shape, has confirmed it doesn't, or has outstanding work. |
| **Adapter / injector behaviour** (e.g. "build_canonical now drops rows whose `unit` is empty") | Document in CLAUDE.md §4 + the affected domain guide(s). CHANGELOG `### Changed`. |
| **LEAP/NEMO behaviour** (e.g. "ActiveScenario set hops to a different open area") | CLAUDE.md §11 + the affected docs (e.g. `docs/leap_integration.md`). Not domain-specific. |

Concrete worked example:

> **Lesson** (bioenergy, 2026-05-05): "raw-crop tonnes, not
> extracted-product tonnes — palm cap was 5× too small at B40 demand."
> **Generalisation:** "supply cap and its per-unit cost row on the same
> branch must share the same physical basis."
> **Cross-domain check:** scan `inject/fossil/crude_oil_max_production.csv`
> vs `inject/fossil/crude_production_cost.csv` — both per-tonne crude;
> aligned. `coal_supply_costs.csv` vs reserves — confirm
> per-tonne-coal alignment.
> **Outcome:** record cross-check + result in **both** guides under
> "Cross-Domain Learnings" (§6.3). If either side has a mismatch, fix
> it in the same change.

The point is not to add work — it's to make the next session find what
this session already proved, without grep-archaeology.

### 6.3 Each guide carries a Cross-Domain Learnings section

Append (or maintain) a `## Cross-Domain Learnings` section near the
bottom of each `CSV_AUTHORING_GUIDE.md`. Each entry is one bullet:

```
- YYYY-MM-DD — from <source domain>: <one-line principle>.
  This domain: <applied / confirmed not applicable / outstanding>.
  See <source guide §X> for the original.
```

Two purposes: (1) the next reader of *this* guide sees what was learned
elsewhere; (2) the next reader of the source guide can audit which
domains actually picked up the lesson by grepping for the date.

When you write a new guide for a new domain (§5), seed the
Cross-Domain Learnings section by reviewing the existing domains'
sections — copy any lesson you can verify still applies.

---

## 7. Results harvest — the lite three-step SOP (read-side: LEAP → CSV)

> **Canonical step-by-step:** [docs/FLOWS.md §2](docs/FLOWS.md).

When the analyst just wants the **calculated result numbers** out of a
`.leap` area (not a full read+write area dump), use the established
A → B → C pipeline. **Canonical reference, with command lines, defaults,
and a 9-pitfall postmortem:**
[result/20260505/RESULTS_HARVEST_SOP.md](result/20260505/RESULTS_HARVEST_SOP.md).
**Read it before starting any new harvest cycle.** It's faster than
re-discovering the same dead ends.

```
A  RESULT VALUES   probe_leap_results.py     ~50 min/scenario
B  INPUT UNITS     probe_leap_units.py        ~4 min/area (once)
C  OFFLINE JOIN    join_results_with_units.py ~5 sec
                                          → joined_<scenario>.csv
```

Why two probes instead of one: **LEAP COM exposes units only on the
input side of variables.** Reading `Variable.DataUnitText` on a
result-side variable fires LEAP's "Data units are not available for
result variables" modal. The split isolates value-reading (Probe A,
broad branch types `{2,3,4,34,50}`, all regions × years) from
unit-reading (Probe B, narrow branch types `{3, 50}`,
scenario-/region-agnostic). Step C merges offline.

### 7.1 The probe MUST subclass `nemo_read.probe_base.CanonicalProber`

Established 2026-05-17. Same justification as §5.1 for injectors:
the prior pattern was per-cycle copy-pasted ~300-line probe scripts
under `mailbox/<date>/`. Pitfalls (§7.3 + §11.2) were documented but
unenforced — a new probe author could miss the BT={3,50} restriction,
the multi-area trap, the heartbeat convention, etc.
`CanonicalProber` seals those concerns.

**Minimum viable subclass** (everything else inherited):

```python
from nemo_read.probe_base import CanonicalProber

class FullAreaProbe(CanonicalProber):
    PROBE_NAME = "aeo9_full_area_20260517"
    EXPECT_AREA = "aeo9_v0.42_r1e"
    REQUIRE_EXPECT_AREA = True
    # BRANCH_PREFIX = ""  # default: whole area
    # Override RESULT_VARS / INPUT_VARS / DEFAULT_YEARS as needed

if __name__ == "__main__":
    raise SystemExit(FullAreaProbe().run())
```

**The framework owns** (sealed):
- `_assert_area_lock` / `_assert_scenario_lock` — drift detection
- `_read_value` — safe value read (catches popups)
- `_read_unit_text` — `DataUnitText` with BT={3,50} guard (§11.2
  enforced; subclass cannot bypass)
- Heartbeat + progress-JSON wiring throughout

**The subclass overrides** (open hooks):
- `result_variables()`, `input_variables()` — target variable names
- `result_branch_types()`, `unit_branch_types()` — BT filter
- `regions()`, `years()`, `branch_prefixes()` — scope
- `extra_cli_args(parser)` — sector CLI flags

**Default `run()`** does in ONE COM session:
1. `dispatch_leap` → area lock
2. Build tree cache once (reused everywhere)
3. For each scenario: set+verify → Probe A (results per region)
4. Probe B once for the area (units, scenario-agnostic)
5. Final summary + heartbeat finish

**Background convention** (A.16): all probe runs use the heartbeat
logger automatically. Launch via `Bash run_in_background=True`,
monitor via the harness `Monitor` tool or the `_progress_*.json`
file. Don't run probes in the foreground.

### 7.2 When NOT to use this SOP

Use the full [`nemo_read-leap-export`](nemo_read/leap_export.py) CLI
(plus `LeapAreaContext.discover()`) instead when:

- You need **input-side data** (input variable values, expressions,
  formulas) in addition to results.
- You need a **self-contained area dump** that other analysts can use
  without LEAP installed.
- The analysis question goes beyond "what came out of this run."

The A → B → C pipeline is the **focused, fast** counterpart for "I just
want the result numbers, properly unit-annotated."

### 7.3 Each cycle's artifacts live in `mailbox/<YYYYMMDD>/`

The probe + join scripts are **templates** — copy and adapt per cycle.
The dated folder holds:

```
mailbox/<YYYYMMDD>/
├── <area>.leap                    LEAP area file (user-supplied)
├── probe_leap_results.py          Step A
├── probe_leap_units.py            Step B
├── join_results_with_units.py     Step C
├── RESULTS_HARVEST_SOP.md         this cycle's SOP (carry forward
│                                   when forking a new cycle)
├── results_<scenario>_<scope>.csv  Step A output (per scenario)
├── units_<scope>.csv              Step B output (one per area)
└── joined_<scenario>.csv          Step C output (per scenario)
```

Keep this shape so the next cycle is mechanical.

### 7.4 Pitfalls — DON'T repeat (full list in the SOP doc)

The most load-bearing pitfalls are also hoisted into §11 (LEAP COM
gotchas), so they surface during routine COM work even when you're not
reading the SOP. Summary:

- `Variable.DataUnitText` is the unit attribute — `Variable.Unit.Name`
  silently returns empty.
- **Never call `DataUnitText` on result variables** — it raises a modal
  popup that stays on screen even when the COM error is caught.
- Some variable names exist on **both input and result sides** (e.g.,
  `Maximum Availability`). Walk by `Variables.Item(j)` index and take
  first occurrence — `branch.Variable(name)` returns either variant
  nondeterministically.
- Probe B (units) restricts to branch types `{3, 50}` because BT={2,4,
  34} expose target names *only* as result aggregates → fires popups.
- **Always exclude `Base Template`** from `--regions` lists — it's a
  LEAP placeholder, not a real region.
- Restrict `--years` to model milestones (e.g., 2025-2060) — including
  pre-model years inflates CSVs ~7× with zeros.
- `--skip-zeros` cuts result CSVs ~10× without information loss.
- Stdout buffering under Bash background mode is unreliable — monitor
  progress via `wc -l <output.csv>`, not script stdout.
- Multi-area trap: `ActiveScenario` set may switch areas if a same-named
  scenario exists elsewhere. Probes carry an area-lock guard (exit 3
  if the area changes mid-run); use `--no-scenario-switch` if user is
  driving the dropdown manually.

### 7.5 SOP discoverability — the meta-rule

When a recurring procedure earns its own SOP / how-to / pitfalls
postmortem (like `RESULTS_HARVEST_SOP.md`), **CLAUDE.md must reference
it** so a fresh session finds it without grep. The reference goes in
the relevant workflow section (§4 / §7 / §8 / etc.) AND in the docs
map (§9). If the SOP also surfaces LEAP/NEMO behavioural pitfalls,
hoist the load-bearing ones into §11 so they pop up during routine
COM work, not only during the procedure's own cycle.

The point of this rule is the user's directive: **never repeat the
same mistake twice.** A SOP that exists but isn't linked from
CLAUDE.md is one Claude session away from being forgotten.

---

## 8. The 11-stage infeasibility methodology (revised 2026-05-11)

> **Canonical step-by-step:** [docs/FLOWS.md §3](docs/FLOWS.md).
> The 11-stage details below remain authoritative for stage exit
> criteria and rationale.

The **only three sources of information** we use:

> **(i) Solver error log**     `cN` vs `xN`, calc years, presolve status.
> **(ii) NEMO sqlite**         All parameter tables, dimensions, descriptions.
> **(iii) LEAP COM probe**     Targeted reads of `Variable.Expression` (or
>                              equivalent via cached dumps / inject files /
>                              asking the modelling team in parallel).

We **never re-run `calculatescenario`** just to get more years or more
detail — the calc is the expensive end of the loop. The two cheap sources
(error log + sqlite) must narrow the LEAP-side probe down to a small,
targeted set of reads. If the probe still isn't small after the cheap
sources, the static check library has a gap — fix the gap (write a new
detector in `infeasibility.py`) before moving on.

The pipeline:

```
1  PRE-FLIGHT          validate_scenario + find_infeasibilities → check_scenario
                       Includes a GENERAL (r, f, y) fuel mass-balance audit:
                       forced_demand (SpecifiedAnnualDemand + AccumulatedAnnualDemand
                       + Σ MU×ResCap×C2A×IAR + Σ ActivityLowerLimit×IAR over
                       consumer techs) vs max_supply (Σ max_activity×OAR over
                       producer techs, with slack/uncapped producers as +∞).
                       Output names contributing consumer + producer techs per
                       (r, f, y) — these are the LEAP branches to probe next.

2  SOLVER RUN          (LEAP / NEMO / CPLEX) — already happened by the time
                       we're diagnosing.

3  POST-MORTEM TRIAGE  xN → decode_lp_column(db, N) → vfamily[r,t,y]
                       cN → no offline row decoder; rely on Stage 1's
                            mass-balance output. The (r, f, y) triples
                            already pinpoint the bind.

4  PATTERN FORENSICS   classify_parameter / forensics_for_pinned_variable
                       → bug / intent / unknown per cluster. For cN cases
                       the mass-balance output names the techs — pattern-
                       classify them and pick the most-likely-bug one.

5  PLACEHOLDER         propose_placeholders → ranked diagnostic patches.
                       Lex order: (blast_radius, −confidence, reverse).

6  DIAGNOSTIC TEST     inject_to_leap.py --placeholder-mode
                          ├─ solves         → cause CONFIRMED → Stage 9
                          ├─ same xN/cN     → wrong cluster, try next
                          └─ new xN/cN      → cause confirmed; new loop

7  PROBE BRIEF         emit_probe_brief → minimum LEAP COM read list
                       (only when Stage 6 doesn't converge or you want to
                       confirm the LEAP-side mechanism before real-fix.)
                       The probe is THIS NARROW because Stage 1's mass-
                       balance already named the branches.

8  LEAP COM PROBING    nemo_read._leap_com — execute the brief.
                       Mind the popup-modal traps (§11.2). ALTERNATIVES /
                       PARALLEL to live COM probing (any of these is fine
                       and often faster):
                         - Read existing inject files in `mailbox/<domain>/`
                           — most variables we'd probe have already been
                           authored there with the LEAP-side expressions.
                         - Read cached branch dumps
                           (`mailbox/<domain>/<date>/_cache_dump_*.txt`).
                         - Ask the relevant team (bioenergy / fossil /
                           power) for the expressions while we probe.
                       Whichever path delivers the expressions first wins.

9  REAL-FIX DESIGN     Manual, informed by 4 + 6 + 8.
                          bug + tech-broadcast scope → fix at template branch
                          bug + per-region scope     → per-region rows
                          intent (decay/harvest)     → DO NOT TOUCH; preserve
                       If the calc only ran 2 years (e.g. 2025, 2050) but
                       the LEAP expressions span 2025-2060: evaluate each
                       Interp/Step expression offline at each model year,
                       re-do the mass balance per (r, f, y) per year, and
                       report all bind years without a recalc.

10 PATCH INJECTION     inject_to_leap.py (placeholder gate refuses
                       Stage-5 rows without --placeholder-mode flag).

11 VERIFICATION        Loop back to Stage 1.
```

**Why this is the surefire narrowing:**

- The fuel mass-balance audit at Stage 1 subsumes every known
  shape-specific check (MU×ResCap, demand-without-supply,
  ActivityLowerLimit-without-build-path) into ONE algorithm over
  (r, f, y). No library of detectors to grow per shape — one detector
  that aggregates all forced demand vs all supply per fuel-year.
- The output names contributing techs on both sides of the imbalance, so
  Stage 7's probe list writes itself: the LEAP branches to read are
  exactly the consumer + producer techs the audit named.
- If Stage 1 returns clean but the solver still infeasibles: the bind is
  in a chain class our audit doesn't reach. **Before extending the
  detector, check the two upstream classes from §A.12 + §11.4** —
  Unmet Load slack visibility/cost and inter-region trade routes for
  feedstock fuels referenced by `MinShareProduction` blend mandates.
  These were the actual root cause on 2026-05-13 (aeo9_v0.42 RAS, 24k
  residual cleared by enabling Unmet Load + Optimized Trade plug-in).
  Only after those audits come back clean: extend `infeasibility.py`
  for storage chain, per-mode balance, per-timeslice balance. The
  library closes its own gaps over time.

**Retired diagnostic angles (do not propose):**

- **LP file dumps / `writelpfile=true` / `writelpsolution=true` /
  `nemo.cfg` LP-output options.** This was never real on this user's
  NemoMod + Julia + CPLEX build — no LP file is produced regardless of
  the args you pass. Past sessions wasted hours on this. The offline
  `decode_lp_column` works from SQLite alone; that is the only
  column-index decoder available, and there is no offline row (cN)
  decoder.
- **Custom-constraint table inspection as a "what's causing the bind"
  angle.** The `__NEMOcc_*` tables (RenewableCapacityTarget,
  ASEANRenewableCapacityTarget, GHG limits, etc.) are real data and
  must be preserved during real-fix design, but in practice they have
  *never been the root cause* of an infeasibility we've diagnosed.
  **CAVEAT (2026-05-13):** other policy-mandate parameters that are
  NOT in the `__NEMOcc_*` tables CAN cause infeasibility —
  specifically `MinShareProduction` blend mandates interacting with
  missing inter-region trade routes for feedstock fuels (see §A.12
  and §11.4). The retirement here applies only to the `__NEMOcc_*`
  tables, not to all policy constraints.
  Don't start there. Don't waste a Stage-4 cycle picking through them
  hoping to find the bind — go straight to MinUtil×ResCap, bound
  inversions, fuel-balance chains.

**Things you must preserve:**

- **The placeholder gate.** `inject_to_leap.py` *refuses* to push a row
  tagged `data_confidence=PLACEHOLDER` (or carrying the
  `PLACEHOLDER (Stage 5...)` note prefix) unless `--placeholder-mode` is
  on. Don't strip the sentinel to "make it inject" — that's the bug the
  gate exists to prevent.
- **Lex ordering of placeholders.** `propose_placeholders` ranks
  `(blast_radius, −confidence, reverse_difficulty)`. Smallest, most
  confident, most reversible test runs first. If you re-rank, justify it.

Worked example + stage-by-stage exit criteria in
[docs/infeasibility_methodology.md](docs/infeasibility_methodology.md).

---

## 9. Where the docs live

| File | When you need it |
|---|---|
| [docs/FLOWS.md](docs/FLOWS.md) | canonical step-by-step for inject / results harvest / infeasibility triage — quick reference for the three established flows |
| [docs/infeasibility_methodology.md](docs/infeasibility_methodology.md) | infeasibility pipeline + worked x435004 example + revised cN path (see §8) |
| [docs/schema.md](docs/schema.md) | NEMO v11 column reference |
| [docs/cookbook.md](docs/cookbook.md) | analysis recipes (capacity stack, demand by sector, …) |
| [docs/leap_integration.md](docs/leap_integration.md) | LEAP COM API + `_def` view semantics |
| [docs/leap_export.md](docs/leap_export.md) | `nemo_read-leap-export` directory format + author-iteration workflow |
| [docs/conventions_and_validation.md](docs/conventions_and_validation.md) | units, IDs, validation, infeasibility |
| [docs/unit_conversions.md](docs/unit_conversions.md) | defensible conversion factors with citations + 5★ confidence rubric |
| [docs/scaffolding.md](docs/scaffolding.md) | the `nemo_read-scaffold` CLI |
| [docs/leap_area_wishlist.md](docs/leap_area_wishlist.md) | open-work backlog |
| [inject/bioenergy/CSV_AUTHORING_GUIDE.md](inject/bioenergy/CSV_AUTHORING_GUIDE.md) | bioenergy mailbox column conventions |
| [inject/bioenergy/BIOENERGY_CSV_SPEC.md](inject/bioenergy/BIOENERGY_CSV_SPEC.md) | bioenergy spec (single-cap design) |
| [result/20260505/RESULTS_HARVEST_SOP.md](result/20260505/RESULTS_HARVEST_SOP.md) | results-harvest A→B→C SOP + 9-pitfall postmortem (carry forward to next cycle) |

When you write a new doc, put it in `docs/` and link it from README's
"Repository layout" section. When you write a new per-cycle SOP (like
`RESULTS_HARVEST_SOP.md`), keep it in the cycle's `mailbox/<date>/`
folder but **link it here** so future sessions discover it.

---

## 10. Testing & releases

### 10.1 Tests

- Test runner: `python -m pytest`. Suites live in `tests/` and run
  ~hundreds of assertions against synthetic + real-derived fixtures.
- **Don't merge work that breaks tests.** If you genuinely need to
  change a fixture's expectations, explain why in the test
  docstring/comment.
- **Every bug fix gets a regression test.** The test should fail before
  the fix and pass after — not just exercise the new code path.
- **New public function ⇒ at least one unit test** in the matching
  `tests/test_<module>.py`. Synthetic fixtures preferred; pull from
  real-scenario data only when the behaviour can't be reproduced
  synthetically.
- **Promoted probes (§12).** When a `_probe_*.py` reveals behaviour
  worth pinning, the *behaviour* moves into a real test in `tests/` —
  not a copy of the probe script.

### 10.2 Versioning

- Version bumps live in **two places** that must stay in sync:
  `pyproject.toml` (`version = "..."`) and `nemo_read/__init__.py`
  (`__version__ = "..."`).
- Semver, loosely: minor for new public API, patch for fixes / docs /
  internal refactors. We're pre-1.0; breaking changes are allowed in
  minor bumps but should be flagged in CHANGELOG with `### Changed —
  breaking:` and a migration note.

### 10.3 Release flow

A release is triggered when (a) the user says so, or (b) a milestone
landed and the user has accepted the work. Routine task completion is
**not** automatically a release.

When a release is called:
1. Confirm tests pass (`python -m pytest`).
2. Confirm `CHANGELOG.md` has a section for the new version with the
   accumulated bullets (see §15.2 routing).
3. Bump the version in both files (§10.2).
4. Single commit: `<X.Y.Z> — <one-line theme>` matching the existing
   `0.6.5 — bioenergy single-cap migration + author-iteration workflow`
   shape.
5. Tag (`git tag vX.Y.Z`) and push tag — GitHub Actions trusted-
   publishing handles PyPI.

### 10.4 WIP commits during in-flight refactors

Multi-day structural work (visible in history as e.g.
`321d1be WIP — split mailbox into bioenergy/ + fossil/ domains`) may
land as `WIP — <theme>` commits before being squared up at release. Use
sparingly; squash or fold into a clean release commit when the work is
done. Don't WIP-commit broken code without a note in the message
saying what's broken.

---

## 11. LEAP COM gotchas (operational reality)

When working with `nemo_read-leap-export`, `inject_to_leap.py`, or any
results-harvest probe (§7):

### 11.1 Area / scenario state
- **Keep only the target LEAP area open during a push.** Setting
  `leap.ActiveScenario` over COM can hop to a different open area if it
  has a same-named scenario. The injector locks to ActiveArea on start
  and aborts if it shifts (≥0.6.4); the results-harvest probes carry an
  identical area-lock with exit code 3.
- **Multi-area recovery recipe** — when the user has multiple LEAP
  areas open and the trap fires repeatedly across a multi-step session
  (each `--scenario` flag flips area), stop chasing it via COM and
  switch to **manual UI scenario set + `--no-scenario-switch`**:
    1. User sets target area + scenario in LEAP UI dropdown manually.
    2. Confirm by reading `leap.ActiveArea.Name` once before push.
    3. Run injector with `--no-scenario-switch` flag; it uses
       whatever's active without invoking the COM scenario-set call.
    4. For multi-scenario runs (BAS then ATS), repeat: user flips
       scenario in UI between each push, runs `--no-scenario-switch`
       again. Slower but reliable when the multi-area state can't be
       cleaned up easily.
- **`Branches.Count` fluctuates by ±1.** The tree cache tolerates ±5 to
  avoid spurious 3-minute rebuilds. Don't tighten the tolerance.
- **`Branches("non-existent")` blocks indefinitely.** Always go through
  `LeapTreeCache` (id-map / FullName-map → positional index) — never
  raw lookup by string on the COM object.
- **Region scoping is `leap.ActiveRegion` in an outer loop**, not
  per-row. 12 sets per area instead of thousands.
- **`Base Template` is not a real region.** It appears in
  `leap.Regions` enumeration but is a LEAP placeholder. Always exclude
  from `--regions` lists in any probe or export.
- **Dry-run cache trap — `inject_to_leap.py --dry-run` skips the
  per-AMS `ActiveRegion` set** (gated on `not args.dry_run` at
  [inject_to_leap.py:272](inject/bioenergy/inject_to_leap.py#L272)).
  The `LeapTreeCache` is built before the AMS loop using whatever
  `ActiveRegion` is active at script start. Branches that are only
  exposed under specific regions return false `branch_not_found` in
  dry-run, even though the real push (which sets ActiveRegion per-AMS)
  finds them. Confirmed 2026-05-06 against `aeo9_v0.38`: a CA dry-run
  reported 98/114 `branch_not_found` for power-tree branches; the same
  rows pushed 114/114 cleanly under real-run. **Mitigation:** when
  dry-run reports `branch_not_found` for branches you expect to exist,
  before declaring real structural mismatch run a probe (e.g.
  [result/20260505/_probe_v038_power_tree.py](result/20260505/_probe_v038_power_tree.py))
  with `ActiveRegion` set to a region that should expose the full
  tree, and diff `cache.fullname_to_idx` against expected paths.
- **Branch-visibility flux 5031 ↔ 4157.** Same area, same scenario,
  but cache size differs by ~870 branches between consecutive runs
  based on `ActiveRegion` at cache-build time. The ±5 cache tolerance
  in `LeapTreeCache` is for `Branches.Count` micro-fluctuation; it
  does not catch the region-scope-dependent visibility delta. Don't
  treat cache count as a stable invariant of the area.
- **Spontaneous `ActiveArea=''` between Python invocations.** Even with
  `--no-scenario-switch` and only the target area open, COM state can
  spontaneously go bad between back-to-back inject calls — `ActiveArea`
  blanks, `ActiveScenario` shows a placeholder name like
  `'Bad Scenario [1]'` or a scenario from a *different* area like
  `'Accelerated NZE with CCS'`. Observed 3× in one session against
  `aeo9_v0.38`. Area-lock catches it (no writes happen); user
  re-verifies UI state and retries. Trying to chase a root cause
  through COM is not productive — the recovery is mechanical, not
  diagnostic.

### 11.2 Variables and units (hoisted from §7's pitfalls)
- **`Variable.DataUnitText` is the unit attribute.** `Variable.Unit.Name`
  silently returns empty for both input and result variables on the
  AEO9-era LEAP version. Use
  `from nemo_read.leap_units import safe_data_unit_text` rather than
  rolling your own; the helper also catches the modal-popup exception.
- **NEVER call `DataUnitText` (or any `.Expression` read) on result
  variables.** LEAP raises a "Data units are not available for result
  variables" / "Expressions are not used for result variables" modal
  *as the COM error*. The defensive helper catches the error but the
  popup stays on screen until manually dismissed. The fix: don't touch
  these attributes on result-side variables in the first place.
- **Variable name collision (input + result variant).** Some target
  names (e.g. `Maximum Availability`) appear on **both sides** of a
  branch — `branch.Variable(name)` returns either variant
  nondeterministically. Walk by index (`branch.Variables.Item(j)`) and
  take **first occurrence**. Input variables come first in COM
  iteration order, so first-occurrence guarantees the input variant.
- **Restrict branch types per intent.** Reading **input units** → use
  `{3, 50}` only (Transformation Process + Transformation Branch are
  the only types with reliable input-side variables). Reading
  **result values** → wider set `{2, 3, 4, 34, 50}` is fine because
  result aggregates legitimately live on Module/Demand-Tech/Effect
  branches. Crossing these wires fires popups.
- **Variables can be scenario-scoped.** `branch.Variable("X")` returning
  `None` does not prove `X` was retired — LEAP exposes some variables
  only under specific scenarios (e.g. `Maximum Capacity` on the AEO9
  bioenergy process branches in v0.36 is exposed under the RAS scenario
  but not under Mitigation / Current Accounts / etc.). Before treating
  a missing variable as a schema migration: **switch ActiveScenario to
  RAS (or whatever scenario the variable is meant to live in) and re-
  probe**. Schema migrations affect all scenarios; scenario-scoped
  variables only the relevant ones. Confirmed 2026-05-05 against
  `aeo9_v0.36` — bioenergy team had to clarify after a defensive
  handoff filter went up.

### 11.2b Historical Production / FirstScenarioYear anchor trap
The common LEAP idiom `Interp(..., 2024, V, FirstScenarioYear, 0)`
for "value applies historically, drops to 0 in projection" has a
SUBTLE BUG: it linearly interpolates between the last named year and
FirstScenarioYear. If `Analysis → Basic Parameters → First Simulation
Year` > 2025 (or whatever your first projection year is), the
interpolation creates phantom HP values in the gap years — combined
with `Existing Capacity = 0` in those years, LEAP halts with errors
like *"Output in timeslice 0 is non-zero (NNN GJ) but zero capacity
is available."*

**Canonical fix order** (per LEAP forum thread 3958):
1. Confirm `First Simulation Year` is ≤ the year you intend
   projection to start. From that year onward HP is ignored.
2. Verify Exogenous Capacity for the affected (region, tech) is
   non-zero in the gap year — should hold the installed fleet.
3. Check Lifetime — short lifetime + clustered historical additions
   means fleet retires en masse; stretch lifetime or add a vintage.
4. The `, FirstScenarioYear, 0` tail is only safe if FirstScenarioYear
   is THE YEAR IMMEDIATELY AFTER the last historical data point. If
   not, drop the tail and rely on First Simulation Year, OR use
   `Step()` instead of `Interp()` (no inter-year interpolation).

Confirmed 2026-05-05 — Thailand Wind Onshore in BAS hit this on a
Round 1.5 patch cycle. Resolution was `First Simulation Year = 2025`.

### 11.2c Variable-renewable `Min Utilization = Maximum Availability` trap
For variable-renewable tech (Solar PV, Solar PV Rooftop, Solar Floating,
Solar CSP, Wind Onshore, Wind Offshore, Tidal, Wave, Small Hydro and all
subregional `_IDxx` / `_MYxx` node variants), authoring
`Minimum Utilization = Maximum Availability` (the formula
`Maximum Availability` directly, without a `Min()` cap) creates a
**must-run on the full AvailabilityFactor profile** — meaning the plant is forced to produce at AF in every
timeslice with no curtailment slack. Two failure modes:

1. **Physical infeasibility.** Solar / Wind / Tidal / Wave inherently
   produce surplus at certain timeslices (sunny noon, windy nights).
   With MU=AF the surplus has nowhere to go and the LP primal-infeasibles
   on per-timeslice fuel balance.
2. **Floating-point precision trap.** Even when MU = AF "exactly" in
   LEAP, the AvailabilityFactor YearlyShape can carry tiny precision
   leaks (~10⁻⁵ at specific timeslices). NEMO export rounds inconsistently,
   producing MU > AF in some timeslice — instant primal infeas.
   Static `MU > AF` check catches large leaks; small leaks sneak through.

**Authoring rules:**
- For variable renewables — **set `Minimum Utilization = 0`**. The plant
  is fully curtailable; dispatch is driven by demand pull (blend mandates,
  RE targets, electricity demand) and economics. This is the physically
  realistic shape.
- If you want a soft must-run signal on a baseload-ish or
  incumbent-dispatch tech (Biomass, Large Hydro, Geothermal, etc.), use
  one of three `Min(..., Maximum Availability)` patterns — the outer
  `Min()` guards against MU > AF regardless of FP precision in AF:
  1. **Static constant floor:** `Min(10.92, Maximum Availability)` —
     used on Vietnam Biomass Other. Picks a fixed capacity-factor floor.
  2. **Historical-CF static floor:** `Min(Value(Historical Capacity
     Factor[percentage], LastHistoricalYear), Maximum Availability)` —
     keeps the tech running at its measured historical CF indefinitely
     (no phaseout).
  3. **Phaseout trajectory:** `Min(Interp(FirstScenarioYear,
     Value(Historical Capacity Factor[percentage], LastHistoricalYear),
     FirstScenarioYear + Key\Modeling Assumptions\Incumbent Generator
     Dispatch Phaseout:Activity Level[years], 0), Maximum Availability)`
     — ramps historical CF down to 0 over the configured phaseout
     horizon. Used on Malaysia subregional Biomass Other and Large Hydro
     `_MY*` (set 2026-05-12). One centralized knob drives every
     incumbent must-run together — change the Modeling Assumptions
     `Activity Level[years]` value and every tech using this pattern
     re-shapes simultaneously.
- Never write the bare `Maximum Availability` as the MU expression on
  any process branch.

**Cross-tech checklist:** when you find this pattern on one tech, scan
the LEAP file for the same authoring on every variable-renewable
process branch — including the subregional `_IDxx` and `_MYxx` node
variants and the `Rooftop`/`Floating` Solar variants.

Confirmed 2026-04-30 — Brunei Solar PV / Solar PV Rooftop / Solar
Floating tripped this with the AF YearlyShape's ~7×10⁻⁵ leak at Wet:Hr 7
/ Dry:Hr 7. Patch set MU=0.
Re-confirmed 2026-05-11 / 2026-05-12 on `aeo9_v0.42_r1e` RAS — the same
pattern existed on every AMS for 8 variable-renewable tech families
(Solar PV / Rooftop / Floating / **CSP**, Wind Onshore / Offshore, Tidal,
Wave, Small Hydro) plus all subregional node variants. Cleared via
placeholders p4 / p5 / p6 (~100 rows total) plus user manual cleanup of
Solar CSP and Wind Onshore (which the placeholders missed). **Always
search the full Centralized + Distributed Electricity Generation tree
for any tech where `Minimum Utilization` evaluates to `Maximum
Availability` — the placeholder lists don't enumerate all tech families
that may be authored this way; user discovery is the ground truth.**

### 11.2d "Unlimited" string export translation (the 1e12 trap)
Authoring `Variable.Expression = "Unlimited"` (the literal string) in
LEAP is parsed by LEAP→NEMO export as the `1.0e+12` numeric sentinel,
regardless of which variable. See §A.11 for the full rule and burn
record. Operational signatures:
  - In `ResidualCapacity` (or any export-bound lower-bound table):
    rows with `val = 1.000e+12` are the smoking gun. Grep the SQLite
    for these before any structural diagnosis on an INFEASIBLE.
  - In `TotalTechnologyAnnualActivityUpperLimit` /
    `TotalAnnualMaxCapacity`: silently exports as missing/zero for
    some AMS (~broken parse), un-capping the variable.
  - In the CPLEX dual basis: ratios of 10¹² between an `Unlimited`-
    sourced row and a normal-scale row produce dual perturbation
    objective spikes to 10¹⁸-10²⁵ (observed 3.35×10¹⁸ on 2026-05-12).
  - LP coefficient ratio ≥ 10⁹ breaches CPLEX's typical numerical
    tolerance — even when the constraint is non-binding, it floods
    the basis with precision noise.

### 11.4 Policy-constraint feasibility (blend mandates + Unmet Load + trade routes)
A tied set — all three must be configured together for any model
that uses biofuel blend mandates. None of these are caught by
`find_infeasibilities`; they have to be checked manually before
triaging an INFEASIBLE that survives Stage 1.

**(a) `MinShareProduction` blend mandates.** Rows like
`(R1, P19886 Biodiesel, F5 Blended Diesel, 2050, 0.474)` require
Biodiesel to be ≥47.4% of Blended Diesel production. Required
upstream feedstock = mandate × demand × IAR; reaches hundreds of PJ
in growth scenarios. Trace via:
  - For each MSP row, look up the constrained tech's IAR — those
    are the upstream feedstock fuel IDs.
  - The mandate is enforced even when local feedstock production
    capacity is zero, so the model needs an import path.

**(b) Inter-region trade routes for the feedstock fuels.** If a
region has zero local feedstock capacity (Indonesia Sugarcane=0,
Vietnam/Laos/Timor Leste Palm Oil=0, etc.), the model needs
`Key\Optimized Trade` enabled for the feedstock fuel to import from
surplus AMS. Trade routes must be added per-region AND enabled in
the active scenario. Setup requires the Optimized Trade plug-in;
the legacy `add_trade_routes` before-scenario script function
must be REMOVED if the plug-in is in use.

**(c) Unmet Load slack visibility and cost.** `Transformation\
Centralized Electricity Generation\Processes\Unmet Load_*` branches
must be UNHIDDEN in Base Template + each region, AND have positive
`Variable OM Cost` + `Fixed OM Cost` (typical 500). Without slack,
any unmet electricity demand → INFEASIBLE instead of solved-with-
high-cost. Node-specific variants (Unmet Load_MYSR, Unmet Load_IDJW,
etc.) exist for sub-region-decomposed AMS and must each be unhidden
+ priced. Parameters on the node-specific variants live in CA, Set
Up, and Base Template — all three must be consistent.

Confirmed 2026-05-13 against `aeo9_v0.42` RAS: 24k residual primal
infeasibility cleared after enabling (a) + (b) + (c) — specifically:
  - Unhid all branches in `Transformation\Centralized Electricity
    Generation\Processes\` in Base Template.
  - In CA + Base Template, set Variable OM Cost + Fixed OM Cost = 500
    on all Unmet Load processes.
  - Unhid node-specific Unmet Load_* in Indonesia + Malaysia;
    non-node-specific in other regions.
  - Corrected parameters in CA, Set up, Base Template, and Malaysia
    for `Unmet Load_MYSR`.
  - Added Optimized Trade plug-in. Removed legacy `add_trade_routes`
    from before-scenario script.
  - Added trade routes in `Key\Optimized Trade` for Ethanol,
    Biodiesel, Coconut Oil, Palm Oil, POME, Cassava, Molasses,
    Sugarcane, Corn. Enabled in RAS.

See also: `memory/project_aeo9_v042_RAS_resolved.md` for the full
sequence and `inject/bioenergy/HANDOVER_v042_r2a_RAS_infeas_to_dev_team_20260512.md`
for the dev-team handover.

### 11.3 Cosmetic-but-visible
- **Modal popups are cosmetic, not failures.** "variable not visible
  for region X" / various other dialogs fire even when the underlying
  COM call succeeded. The package's `safe_*()` helpers swallow the
  errors — if you see a popup in the UI, dismiss it; the script logs
  `[OK]`. (See §11.2 for the popups you can *prevent* by not reading
  the wrong attributes in the first place.)
- **Year scoping.** Probes that don't restrict `--years` to model
  milestones (e.g. 2025-2060) zero-pad pre-model years (BaseYear..2024)
  and inflate output ~7×. Restrict explicitly.
- **Stdout buffering under Bash background.** Python prints don't flush
  reliably even with `PYTHONUNBUFFERED=1` and `line_buffering=True`.
  When monitoring a long probe, watch the output CSV's row count
  (`wc -l <file>`), not the script's stdout.

---

## 12. Probes, findings & the scratch graveyard

The `mailbox/<domain>/_*.py` and `_*_findings.txt` files are real
diagnostic work, not garbage. They are the breadcrumb trail of how a
problem was reasoned through. Their lifecycle:

### 12.1 Naming
- `_probe_<topic>.py` — short, single-purpose script that asks LEAP or
  NEMO one question (e.g. `_probe_e407_penalty.py`,
  `_probe_renewable_target.py`).
- `_<topic>_findings.txt` — the captured output / interpretation.
- `_<topic>.py` (without `probe_`) — task-specific scratch that built
  something rather than asked something (e.g.
  `_build_patch_2026_04_30.py`, `_compare_author_vs_patch.py`).
- The `_` prefix is the marker: "this is scratch; not a public artifact."

### 12.2 What to do with them at task end

When a probe is finished, classify:

| If the finding is… | Then… |
|---|---|
| A reusable behavioural truth about LEAP/NEMO | Promote to `docs/<topic>.md` (or §11 of this file) and add a regression test if testable. The probe script can stay as breadcrumb but the *knowledge* now lives somewhere indexed. |
| A repeating procedure with discovered pitfalls | Write a per-cycle SOP doc (like `RESULTS_HARVEST_SOP.md`); reference from CLAUDE.md §7-style section + §9 docs map (§7.4 meta-rule). |
| A one-off answer that won't repeat | Leave the `_<topic>_findings.txt` in place as the historical answer. No promotion needed. |
| A new public capability worth shipping | Refactor into `nemo_read/<module>.py`, add to `__all__`, write tests, CHANGELOG bullet. The probe is now obsolete; delete it. |
| A lesson that may apply to other mailbox domains | Run the §6.2 cross-domain protocol; record in **every** affected domain's Cross-Domain Learnings section. |
| Outdated by a later cycle | Either delete or move to `mailbox/<domain>/<YYYYMMDD>/` as a dated archive. Don't leave a stale finding contradicting current truth. |

### 12.3 Don't accumulate without classifying

A repo full of `_*` files where nothing has been promoted is a sign the
loop is broken. At end-of-task (§15), do a quick `_*` audit on the
domain you touched.

---

## 13. House style — code & prose

- Edit existing files; create new ones only when the task genuinely
  needs one. Especially do **not** create `*.md` planning/decision
  files unless the user explicitly asks.
- Default to **no comments**. Add a comment only when the *why* is
  non-obvious (a hidden constraint, an LEAP-COM workaround, a
  reversed-because-of-incident-X rule). Don't restate what the code does.
- Don't add backwards-compat shims for code paths nothing in this repo
  calls. Simple deletion is preferred over `_unused = old_name`.
- Public API changes go through `nemo_read/__init__.py` `__all__` —
  keep the export list aligned with what's actually re-exported.
- When citing a file, use markdown link form `[filename](path)` or
  `[filename:line](path#Lline)` — not backticks.
- Docstrings: one-line summary; expand only when the function has
  non-obvious invariants or LEAP-COM behaviour. Keep them honest —
  prefer "raises if X" over an essay on usage.

---

## 14. Adding a new public function — the standard recipe

When the user asks for a new analysis primitive (e.g. "give me a helper
that computes X"), follow this sequence so it lands cleanly:

1. **Pick the right module.** New analysis on existing tables → extend
   the matching reader (`parameters.py`, `variables.py`, `dimensions.py`).
   New cross-cutting capability → new file in `nemo_read/`. New LEAP-COM
   behaviour → goes in `_leap_com.py` or `leap_export.py`.
2. **Implement with the established signatures.** First arg `db: NemoDB`
   for SQLite-side functions; return `pd.DataFrame` with named columns
   (not positional tuples). Use `decode_dims(df, db)` if codes leak into
   the output.
3. **Re-export.** Add to the relevant import block + `__all__` in
   `nemo_read/__init__.py`. **Enforced by
   [tests/test_public_api_completeness.py](tests/test_public_api_completeness.py)
   per §A.17** — every top-level class/function in `nemo_read/*.py`
   whose name doesn't start with `_` MUST appear in `nemo_read.__all__`.
   If a name should NOT be public, prefix it with `_`. The tripwire
   fails CI on omission.
4. **Test.** Add a unit test in `tests/test_<module>.py` with a synthetic
   fixture. Real-scenario data is the fallback, not the default.
5. **Document.** Touch the matching `docs/<topic>.md` if the function is
   user-visible. Add a one-line docstring at minimum.
6. **CHANGELOG.** `### Added` bullet for the next release section,
   naming the function and the user-visible benefit.
7. **End-of-task checklist (§15).**

---

## 15. The improvement loop — definition of done

This is the linchpin: every task ends here. **A task is not "done" until
the loop is closed**, regardless of whether the code change is small.

### 15.1 End-of-task checklist

Run through this before saying "done" to the user. Items marked
**[CI]** are now enforced by pytest tripwires (§A.17) — running
`python -m pytest` clean is sufficient to verify them. Items
without **[CI]** are judgment-based — actually walk through them.

- [ ] **[CI] Tests.** `python -m pytest` clean (or new test added for the new
      behaviour / regression).
- [ ] **[CI] `__all__` synced** if any public symbol was added/renamed/removed.
      Enforced by
      [tests/test_public_api_completeness.py](tests/test_public_api_completeness.py).
- [ ] **[CI] Version sync** — `pyproject.toml` and
      `nemo_read/__init__.py` agree. Enforced by
      [tests/test_claude_md_rules_enforced.py](tests/test_claude_md_rules_enforced.py).
- [ ] **Version bump?** If this is a release-worthy change, both
      `pyproject.toml` and `nemo_read/__init__.py` updated (the CI
      check above only catches DRIFT, not "should-have-bumped").
- [ ] **CHANGELOG bullet** added in the appropriate section
      (`### Added` / `### Changed` / `### Fixed` / `### Documented` /
      `### Validated against …`). Bullet explains the *why*, not just
      the *what*.
- [ ] **Docs touched** if user-visible behaviour changed (matching
      `docs/*.md` or this file's relevant section).
- [ ] **Authoring guide(s) touched** if the change affects any
      `mailbox/<domain>/CSV_AUTHORING_GUIDE.md` (§6.1) — adapter
      behaviour, canonical schema, unit convention, off-limits list,
      newly learned failure mode.
- [ ] **Cross-domain protocol run** (§6.2) if the lesson is systemic.
      Every affected domain's "Cross-Domain Learnings" section updated.
- [ ] **SOP doc updated or referenced** (§7.4) if the task touched a
      recurring procedure (results harvest, leap-export, etc.). New
      SOP linked from §9 docs map; new pitfalls hoisted into §11.
- [ ] **CLAUDE.md updated** if the task corrected guidance previously
      stated here, **and** the correction was validated (§15.3).
- [ ] **Memory updated** if a user preference / project context fact /
      external reference changed (memory types in §15.2).
- [ ] **Mailbox `_*` audit** done for any domain you touched (§12.3).
- [ ] **Stale memory cleanup** — if you noticed a memory contradicted
      by current code while working, fix or delete it.
- [ ] **No placeholder rows committed** to canonical CSVs / no Stage-5
      sentinel in real-fix injection runs (§4.1).
- [ ] **Target was confirmed** before any inject / SQL read / probe
      happened (§2.5).

### 15.2 Where does this learning go? — routing table

Every learning has a single right home. Use this table; don't double-park.

| You learned… | Where it goes | Why |
|---|---|---|
| A new fact about how LEAP/NEMO behaves (e.g. a new modal popup, a new COM quirk) | `docs/leap_integration.md` or §11 of this file + CHANGELOG `### Documented` | Operational truth, future sessions need it before reading code. |
| A new repo convention (file naming, mailbox layout, CSV column rule) | This file (relevant §) + CHANGELOG `### Documented` | Convention guidance is operator-level. |
| A new rule for a single domain's CSV authoring | That domain's `CSV_AUTHORING_GUIDE.md` (§6.1) + CHANGELOG `### Documented` | Domain-specific authoring contract. |
| A systemic principle that applies across mailbox domains | **Every** domain's `CSV_AUTHORING_GUIDE.md` "Cross-Domain Learnings" section (§6.2-6.3) + CHANGELOG `### Documented` | Cross-domain lessons must rhyme to be findable. |
| **A repeating procedure with newly-discovered pitfalls (an SOP)** | **Per-cycle SOP file in `mailbox/<YYYYMMDD>/<NAME>_SOP.md` if cycle-specific, OR `docs/<topic>.md` if permanent. Link from CLAUDE.md §7-style workflow section AND §9 docs map. Hoist load-bearing pitfalls into §11. (§7.4 meta-rule.)** | **Never repeat the same mistake twice. SOPs that aren't linked from CLAUDE.md are one session away from being forgotten.** |
| A bug fix in nemo_read code | `tests/` regression test + CHANGELOG `### Fixed` | Code is authoritative; the test pins it. |
| A new public function | §14 recipe (touches `__all__`, docs, tests, CHANGELOG) | Public API must be discoverable. |
| A user preference about how they want answers (terminology, terseness, format) | New `feedback_*.md` memory + index in `MEMORY.md` | Personal to this user; persists across sessions. |
| A project state fact (deadline, who's doing what, why a rewrite is happening) | New `project_*.md` memory with **Why** and **How to apply** lines | Decays fast; memory's home for ephemeral context. |
| A pointer to an external system (Linear board, Grafana dashboard, Slack channel) | New `reference_*.md` memory | Lookup, not behaviour. |
| A user role / responsibility / expertise area | `user_*.md` memory | Tailors how to communicate. |
| A scenario validation result (e.g. "tested against AEO9 v0.36, 0 failures") | CHANGELOG `### Validated against …` | Public history of what's been proven. |
| A modelling decision and its rationale (e.g. why double-cap is intentional) | This file's §2 (hard rule) **and** the matching domain doc | Hard rules need maximum visibility. |
| Scratch reasoning that won't repeat | `_<topic>_findings.txt` in the relevant mailbox domain | Breadcrumb only; not promoted. |

If a learning fits two rows, write it once in the more durable home and
link from the other.

### 15.2.1 The CLAUDE.md → memory router pattern (auto-load reality)

Only **two** files are auto-loaded into every Claude session:
1. `CLAUDE.md` — full content.
2. `memory/MEMORY.md` — full content (the one-line index).

Individual memory files (`memory/reference_*.md`, `memory/feedback_*.md`,
`memory/project_*.md`, `memory/user_*.md`) are **NOT** auto-loaded —
their full content only enters context when a Claude instance explicitly
Reads them, triggered by a topic-match against the MEMORY.md description.

This means CLAUDE.md is the **router**: a new Claude in a fresh session
will see only what's directly in CLAUDE.md + MEMORY.md's one-line
descriptions. To pull deeper context, CLAUDE.md must contain explicit
pointers like `See also: memory/<filename>.md for <what's in it>`.

**Rules:**
- When you add a hard rule to §A or a trap to §11 that has long-form
  burn-log detail in a memory file, append a `See also: memory/X.md`
  line at the end of that section. Don't make the next Claude
  archaeology the connection from MEMORY.md descriptions alone.
- Soft duplication between CLAUDE.md (the rule) and memory (the
  long-form context) is **intentional and OK**. The rule must be in
  CLAUDE.md to be auto-loaded; the long form lives in memory so it
  doesn't bloat the auto-load context.
- MEMORY.md descriptions must be keyword-rich (specific terms like
  "1e12 export sentinel", "Unmet Load + trade routes", "hypothesis
  discipline") so topic-match triggers reliably.
- If a rule has NO long-form memory file, that's fine — CLAUDE.md
  alone is sufficient. Add the memory file only when the burn-log
  detail is too verbose to inline.
- If a rule moves entirely from CLAUDE.md to a memory file, replace
  the CLAUDE.md content with at minimum a one-line summary + the
  `See also:` pointer. Never silently delete from CLAUDE.md.

Established 2026-05-13 after user pointed out that individual memory
files were orphaned from the auto-load entry point: *"claude md
shouldve been able to detect and redirect for more details thru those
other files."*

### 15.3 The CLAUDE.md update test

Update CLAUDE.md *only* when:
1. A piece of guidance in this file turned out to be wrong, incomplete,
   or out-of-date, **and**
2. The corrected approach was actually validated (tests passed,
   injection ran, the user accepted it).

If the fix didn't work, leave CLAUDE.md alone — don't codify a guess.
If the fix is one-off / unproven / about to be rolled back, leave
CLAUDE.md alone.

The diagnostic question: *"if a future Claude session followed
CLAUDE.md literally, would they make the mistake I just had to fix?"*
If yes, patch the file in the same change as the fix. If no, the
learning probably belongs in §15.2's other rows.

### 15.4 Why this matters

**The next session should never re-discover something this session
already learned.** That's the operating principle. Memory holds
preferences and project context; CLAUDE.md holds operating guidance;
authoring guides hold the human↔adapter contract per domain;
per-cycle SOPs hold the recipe + pitfalls for recurring procedures;
docs hold reference material; CHANGELOG holds public history; tests
pin behaviour; the code is the source of truth. All of it needs to
stay current — that's the cost of the package being a real artifact
other people consume.

---

## 16. When in doubt

- Re-read this file's §2 (hard rules) — including §2.5 (confirm target).
- Check [docs/infeasibility_methodology.md](docs/infeasibility_methodology.md)
  for the diagnostic flow.
- Check the relevant mailbox `CSV_AUTHORING_GUIDE.md` for column
  conventions, AND its "Cross-Domain Learnings" section for prior art.
- Check the latest per-cycle SOP in `mailbox/<YYYYMMDD>/` if your task
  is a recurring procedure (results harvest, etc.).
- If a memory and the current code disagree, **the code wins** — update
  or remove the stale memory in the same task (§15.1).
- Ask the user before doing anything destructive (force-pushes, deleting
  authored CSVs, dropping `infeas/` fixtures, rewriting CHANGELOG history,
  removing `*.bak_pre_*` backups before validation, deleting `_*` probe
  scripts that aren't superseded).
- Ask the user to confirm the LEAP area / scenario / `.sqlite` before any
  inject, COM walk, probe, or non-trivial SQL read (§2.5).

---

*This file is the operator's brief; it must stay current to be useful.
The §15 loop is what keeps it that way. If a section grows past two
screens, that's a hint the content belongs in `docs/` instead — link
from here, don't duplicate.*
