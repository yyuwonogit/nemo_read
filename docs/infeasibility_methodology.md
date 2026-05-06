# Infeasibility resolution — the 11-stage methodology

The standing process for going from "the solver said something broke" to
"a real fix is in LEAP and the model solves" without rabbit-chase
trial-and-error.

The principle: **exhaust the SQLite + solver report first, leave the
minimum residual question for a precision LEAP probe, and propose a
testable placeholder before any real fix is designed**. Every stage has
a defined exit criterion and a tool that owns it.

## Pipeline diagram

```
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 1   PRE-FLIGHT                                    │
            │   tool: validate_scenario + find_infeasibilities        │
            │         → check_scenario                                │
            │   catches: schema, bound inversions, MU>AF, MinShare>1, │
            │            demand-no-supply, reserve gaps, storage      │
            │            gaps, CCS unbounded                          │
            │   outcome: clean → Stage 2.   issue → fix in LEAP       │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 2   SOLVER RUN                                    │
            │   LEAP/NEMO → calculatescenario → CPLEX/Cbc/Gurobi      │
            │   outcomes: optimal | infeasible | numerical | timeout  │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 3   POST-MORTEM TRIAGE                            │
            │   tool: decode_lp_column(db, N)                         │
            │   "Infeasible column 'x435004'" →                       │
            │     vaccumulatednewcapacity[r=R19, t=P16166, y=2025]    │
            │   knows WHICH variable; doesn't know WHY                │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 4   PATTERN FORENSICS                             │
            │   tool: forensics_for_pinned_variable                   │
            │         classify_parameter                              │
            │   for each parameter touching the pinned variable, run  │
            │   detector battery on every (r, t) cluster:             │
            │     • algebraic_of(other_param)                         │
            │     • broadcast_across_regions                          │
            │     • year_split                                        │
            │     • small_denom_fraction                              │
            │     • varies_per_timeslice_only                         │
            │   verdict per cluster: bug / intent / unknown / empty   │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 5   PLACEHOLDER SYNTHESIS                         │
            │   tool: propose_placeholders(report)                    │
            │   for each bug/unknown cluster, emit a CSV-row override │
            │   that slackens the suspected constraint;               │
            │   ranked LEX by (blast_radius, -confidence, reverse).   │
            │   each row tagged data_confidence=PLACEHOLDER.          │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 6   DIAGNOSTIC TEST CYCLE                         │
            │   tool: inject_to_leap.py --placeholder-mode  +  re-run │
            │         Stage 2                                         │
            │   user applies top-ranked placeholder → re-runs LEAP    │
            │     (a) solves       → CAUSE CONFIRMED → Stage 9        │
            │     (b) same xN inf  → wrong cluster, try next          │
            │     (c) new xN inf   → cause confirmed; new column      │
            │                        starts its own Stage 3 loop      │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 7   PROBE BRIEF                                   │
            │   tool: emit_probe_brief(report)                        │
            │   only when Stage 6 doesn't converge OR user wants to   │
            │   understand the LEAP-side mechanism before writing the │
            │   real fix.  Output: minimum (branch, variable) read    │
            │   list with hypothesis + on_confirm + on_refute per     │
            │   item.                                                 │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 8   LEAP COM PROBING                              │
            │   tool: nemo_read._leap_com (existing)                  │
            │   human + LEAP open; execute brief; annotate answers.   │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 9   REAL-FIX DESIGN                               │
            │   informed by Stages 4 + 6 + 8.  Decision tree:         │
            │     bug + tech-broadcast scope → fix at template branch │
            │     bug + per-region scope     → per-region rows        │
            │     intent (decay/harvest)     → DO NOT TOUCH; preserve │
            │   output: canonical patch CSV (real, not placeholder)   │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 10  PATCH INJECTION                               │
            │   tool: mailbox/.../inject_to_leap.py                   │
            │   pushes via LEAP COM; refuses placeholder rows without │
            │   --placeholder-mode flag.                              │
            └─────────────────────────────────────────────────────────┘
                                     ↓
            ┌─────────────────────────────────────────────────────────┐
            │ Stage 11  VERIFICATION                                  │
            │   re-export DB, re-run Stage 1 + Stage 2.  If a NEW xN  │
            │   surfaces, the next bottleneck is now visible — start  │
            │   another Stage 3 loop.                                 │
            └─────────────────────────────────────────────────────────┘
```

## Stage-by-stage tools

| Stage | Tool | Module |
|---|---|---|
| 1 | `validate_scenario`, `find_infeasibilities`, `check_scenario` | `nemo_read.validate`, `nemo_read.infeasibility` |
| 2 | LEAP/NEMO `calculatescenario` | (external) |
| 3 | `decode_lp_column`, `enumerate_dense_blocks` | `nemo_read.lp_column_decode` |
| 4 | `classify_parameter`, `forensics_for_pinned_variable` | `nemo_read.parameter_forensics` |
| 5 | `propose_placeholders` | `nemo_read.parameter_forensics` |
| 6 | `inject_to_leap.py --placeholder-mode` | `mailbox/.../inject_to_leap.py` |
| 7 | `emit_probe_brief` | `nemo_read.probe_brief` |
| 8 | `dispatch_leap`, `LeapTreeCache`, `safe_expression` | `nemo_read._leap_com` |
| 9 | (manual — informed by all of the above) | — |
| 10 | `inject_to_leap.py` (without placeholder flag) | `mailbox/.../inject_to_leap.py` |
| 11 | re-run Stage 1 | — |

## The placeholder loop in detail

Stage 5's output looks like this (one CSV row per cluster):

```
ams                    Indonesia
branch                 Transformation\Centralized Electricity Generation\Processes\Tidal
variable               Minimum Utilization
expression             0
data_confidence        PLACEHOLDER
note                   PLACEHOLDER (Stage 5 diagnostic): override
                       MinimumUtilization to 0 for (R1, P14432); tests
                       whether this cluster pins the infeasibility.
```

paired with a real-fix prompt:

> Real fix: in LEAP, inspect the `Minimum Utilization` expression on
> `Tidal` (and any parent process branch). It almost certainly contains
> a `=Maximum Availability ^ 2` (or equivalent) formula — replace with
> an explicit numeric value reflecting actual minimum dispatch policy,
> or remove entirely if no minimum is intended.

The user injects (Stage 6), re-runs (Stage 2), and reads the outcome:

| Outcome | Meaning | Next |
|---|---|---|
| Solves | this cluster was the binder | go to Stage 9, write real fix |
| Same `xN` infeasible | wrong cluster | try next-ranked placeholder |
| New `xN` infeasible | this cluster WAS the binder | start a new Stage-3 loop on the new column |

Three mechanically distinct outcomes, each informative — no rabbit-chase.

## Worked example: x435004 (AEO9 RAS, 2026-04-30)

CPLEX presolve aborted with `Infeasible column 'x435004'`. Stage 1
came up clean (no row-local violations).

**Stage 3** decoded `x435004` → `vaccumulatednewcapacity[r=R19,
t=P16166, y=2025]` = Philippines / Sugarcane / 2025.

**Stage 4** ran forensics on the candidate parameters. Of the 7 reports:
- `MinimumUtilization`: 121 bug clusters (squared bug across renewables) +
  53 intent clusters (year-split phase-out, harvest fractions)
- `AvailabilityFactor`: 3267 clusters; the parameter under inspection
  itself shows no bug (the squaring happens AT MU, not in AF)
- `ResidualCapacity`: 200 clusters mostly intent

The `(R19, P16166)` cluster came back as **intent** (small_denom_fraction
fired on `0.864 ≈ 6.05/7`). So MU is *not* the binder for this column —
the placeholder loop should test the *companion* (ResidualCapacity)
instead.

**Stage 5** ranked placeholders: the squared-bug renewables clusters
take the top slots (highest confidence, smallest blast). For the
specific x435004 column, the bridging suggestion is to override
`ResidualCapacity` for Sugarcane R19 — the 1.34M figure is the suspect,
not the MU.

**Diagnosis**: this is the rare case where Stage 5 alone tells you the
placeholder for MU wouldn't work — the cluster verdict says "intent",
so don't placeholder MU. The forensic report's real-fix prompt (for
small_denom_fraction) explicitly says:

> Real fix: the values are clean N/D fractions (likely operating-days/week).
> This is probably modeller intent. Audit the COMPANION variable instead:
> check ResidualCapacity units (often the real bug) and confirm downstream
> demand sinks exist for the output fuel.

That's the right surgical instruction without ever needing a LEAP probe.

## When to skip stages

- **Skip Stage 7-8** if Stage 6 converges (placeholder works → cause
  confirmed → write real fix from the prompt). The probe brief is for
  stuck cases.
- **Skip Stage 4-7** for trivial single-row violations that Stage 1
  already caught with a clear message (e.g. `MinShareProduction` summing
  to 1.2; just fix the row).
- **Always run Stage 11** even after small fixes — multi-bottleneck
  models surface the next constraint as a new `xN` once the current
  one is resolved.

## Anti-patterns this methodology eliminates

1. **"Try setting X=0 and see what happens"** — replaced by ranked
   placeholders with explicit hypothesis-test semantics.
2. **"Read every LEAP expression for any variable that might be related"**
   — replaced by Stage 7's targeted brief (typically 3–5 reads).
3. **"Set MU=0 everywhere"** — Stage 4's intent-vs-bug classification
   would have flagged the bioenergy harvest cluster as `intent`, sparing
   a destructive blanket fix.
4. **"Patch the SQLite directly"** — handled at the `inject_to_leap.py`
   layer; placeholders go through LEAP COM, never bypass it.
5. **"Did my fix actually solve THIS column or did the model find a
   different problem?"** — Stage 6's three-outcome semantics make this
   a binary determination from each test run.
