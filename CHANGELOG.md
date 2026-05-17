# Changelog

## [Unreleased] — Workstream 2: repo reorg `mailbox/` → `mailbox/` + `inject/` + `result/` (2026-05-17)

### Changed — breaking (layout)
- **Top-level structure** split into three single-purpose directories:
  - `mailbox/` is now a **pure inbox** — sector teams drop files here;
    cleaned at every stage commit after relevant files are routed
  - `inject/` is the **outbox to LEAP** — `bioenergy/`, `fossil/`,
    `power/` sector pipelines (was `mailbox/bioenergy/` etc.)
  - `result/` is the **outbox from LEAP** — harvest-cycle outputs
    by date (was `mailbox/<YYYYMMDD>/`)
- `infeas/` unchanged (separate scratch space for diagnostic .sqlite)
- New [MAILBOX_ROUTING.md](MAILBOX_ROUTING.md) at repo root documents
  the inbox→inject/result routing ritual and clone-then-sweep flow.

### Migration notes
- All 3 sector folders moved via `git mv` (preserves blame history):
  `mailbox/bioenergy` → `inject/bioenergy`,
  `mailbox/fossil` → `inject/fossil`,
  `mailbox/power` → `inject/power`.
- Date folders moved: `mailbox/20260505` → `result/20260505`,
  `mailbox/20260513` → `result/20260513`.
- Live path references updated in CLAUDE.md, docs/FLOWS.md,
  docs/leap_export.md, CHANGELOG.md, tests/, and the moved
  inject/*/inject_to_leap.py + build_canonical.py docstrings/examples.
- Injector scripts use `Path(__file__).parent / "canonical_leap_inputs.csv"`,
  so no code changes needed — they follow the move automatically.

### Documented
- CLAUDE.md §3 — new layout box + reference to MAILBOX_ROUTING.md
- docs/FLOWS.md — all three flows already used `mailbox/<date>/` for
  drops; updated to use `result/<date>/` for harvest outputs and
  `inject/<domain>/` for inject targets.

---

## [Unreleased] — Cross-team Power-sector inject cycle (result/20260505)

End-to-end cycle handing off non-ID/MY power-sector input fixes to a
team that doesn't run our tooling (LEAP UI only, no COM, no SQLite).
Validated against `aeo9_v0.36`. Two-round inject (1 + 1.5) totaling
**302 expressions** pushed across Current Accounts + BAS + ATS for 8
non-ID/MY AMS, all aligned to authoritative xlsx truth
(`mailbox/existing_cap_historical_prod.xlsx`).

### Mailbox artifacts ([result/20260505/](result/20260505/))
- `probe_leap_results.py` / `probe_leap_units.py` — Probe A + B
  (results-harvest SOP); `join_results_with_units.py` Step C
- `RESULTS_HARVEST_SOP.md` — full A→B→C SOP with 9-pitfall postmortem
- `diagnostic_anomalies.md` — 7 anomalies catalogued from joined CSVs
  (5 real bugs + 2 structural concerns), each tagged with concrete
  "Where to act" (LEAP UI edit / authoring / structural / auto-resolve)
- `build_existing_cap_inject.py` + `build_round1p5_inject.py` —
  generators that translate xlsx truth → canonical inject CSVs
- Round 1: `inject_existing_capacity_round1_other_AMS.csv` (78 rows,
  EC for 8 non-ID/MY AMS in CA — verified via read-back-one)
- Round 1.5: 3 CSVs (CA 114 + ATS 55 + BAS 55) anchoring HP and
  re-anchoring EC with `, FirstScenarioYear, 0` per LEAP convention

### Documented (CLAUDE.md)
- **§4.1 verification checklist** gained `Read-back-one verify`
  bullet — lightweight sub-second COM read of one branch's expression
  diffed against the inject CSV row, runs between push and re-calc.
  Catches injector misroutes (wrong scenario / wrong path resolution)
  before the 30-min calc round-trip wastes time.
- **§11.1 Multi-area recovery recipe** — the
  manual-UI + `--no-scenario-switch` workflow for sessions where
  `--scenario` flips area repeatedly.
- **§11.2b FirstScenarioYear anchor trap** —
  `Interp(..., 2024, V, FirstScenarioYear, 0)` linearly interpolates
  between last named year and FirstScenarioYear, creating phantom
  HP-with-no-capacity errors when First Simulation Year > 2025.
  Canonical fix order documented.
- **§11.1 Dry-run cache trap** — `inject_to_leap.py --dry-run` skips
  per-AMS `ActiveRegion` set, so `LeapTreeCache` is built under
  whatever region is active at start. False `branch_not_found` errors
  appear for branches only exposed under specific regions; the real
  push finds them. Mitigation: probe with `ActiveRegion` set to a
  region that exposes the full tree before declaring structural
  mismatch.
- **§11.1 Branch-visibility flux** — cache size varies by hundreds of
  branches between runs based on `ActiveRegion` at cache-build time
  (5031 ↔ 4157 observed in same area/scenario). Don't treat cache
  count as a stable invariant.
- **§11.1 Spontaneous `ActiveArea=''`** — between back-to-back inject
  calls, COM state can blank `ActiveArea` and report a placeholder or
  cross-area scenario name (`'Bad Scenario [1]'`, `'Accelerated NZE
  with CCS'`). Area-lock catches it; recovery is mechanical (re-verify
  UI, retry).

### Validated against `aeo9_v0.38` (2026-05-06)
- All 5 inject blocks from
  [result/20260505/INJECTS_TO_REPLICATE.md](result/20260505/INJECTS_TO_REPLICATE.md)
  re-pushed cleanly to a fresh AEO9 v0.38 area: **896/896 rows** across
  4 scenarios (RAS 672, CA 114, ATS 55, BAS 55). Exposed and documented
  the dry-run cache trap, branch-visibility flux, and spontaneous
  ActiveArea blank above. v0.38's `Transformation\Centralized
  Electricity Generation\Processes` tree confirmed structurally
  identical to v0.36's at the 18 expected paths via
  [result/20260505/_probe_v038_power_tree.py](result/20260505/_probe_v038_power_tree.py)
  — no CSV retargeting needed.

### Memory updates
- `feedback_cross_team_handover.md` — when downstream team (Power)
  can't operate our tooling, we do all diagnosis + COM-inject what we
  can, then hand them plain-text FIXSPEC with concrete current→change
  expressions. Distinct from bioenergy/fossil where we own the chain.
- `reference_first_scenario_year_trap.md` — the LEAP-side anchor trap
  for future infeasibility chases.

### Power authoring domain + ID/MY subnational round 2 — validated against `aeo9_v0.38_yy` (2026-05-07)

New mailbox domain [`inject/power/`](inject/power/) for power-sector
scenario-level overrides. Adapter pipeline produces canonical CSVs
from two input shapes (LEAP-export wide-by-row, year-wide pivot);
3-cache driver pushes them under the per-AMS tree shape of
`aeo9_v0.38_yy` (Indonesia/Malaysia carry both country-level and
subnational `_IDxx`/`_MYxx`; other 9 AMS country-level only).

Round 2 ID/MY EC + HP merged in-place into round 1.5 inject CSVs
(`result/20260505/inject_round1p5_{CA,ATS,BAS}.csv` now 240 / 118 /
118 = 1148 rows total). Power standardisation pushed independently.

#### Added
- [`build_canonical.py`](inject/power/build_canonical.py) — LEAP-
  export → canonical schema adapter. Filters: Base Template,
  subnational-mismatch (`_IDxx` only with Indonesia, `_MYxx` only
  with Malaysia), country-level-for-subnational-only-tech (per-AMS
  mutual exclusion when both shapes appear in input), `DROP_OFFTREE_BRANCHES`
  (global), `DROP_BRANCHES_PER_REGION` (region-specific).
- [`build_canonical_yearwide.py`](inject/power/build_canonical_yearwide.py)
  — wide-pivot → `Interp(year, value, …, FirstScenarioYear, 0)`
  converter. Splits by variable into per-scenario canonical CSVs
  (EC → CA only; HP → CA + ATS + BAS).
- [`run_workflow.py`](inject/power/run_workflow.py) — 3-cache
  region-grouped inject driver. `--blind` escape hatch for cache
  lazy-load false-misses; `--fail-fast` to bound hang risk in blind
  mode; `--expect-area` / `--expect-scenario` locks against drift.
- [`CSV_AUTHORING_GUIDE.md`](inject/power/CSV_AUTHORING_GUIDE.md)
  — per-AMS tree shape reference + 4 adapter filter rules + 3
  expression shapes (literal / `Interp` / `Add` / cross-variable
  formula) + pitfalls + cross-domain learnings (CLAUDE.md §6.3).
- [`result/20260505/_probe_readback_one.py`](result/20260505/_probe_readback_one.py)
  — auto-detects ActiveScenario, runs PROBES dict, per-row
  ActiveRegion + blind direct lookup (no 5-min cache build). EXACT /
  NORMALISED / FAIL semantics.
- Round 2 audit chunks
  ([`inject/power/20260507/inject_round2_id_my_*.csv`](inject/power/20260507/))
  alongside the Rev1 source — usable as standalone CA / ATS / BAS
  pushes if round 1.5 already landed.

#### Documented (CLAUDE.md §11)
- **Phantom-branch trap** — `--blind`'s direct
  `leap.Branches(FullName)` returns a Branch object and accepts
  `Variable.Expression` writes on FullNames that don't exist in the
  area's UI tree. Inject log shows `[OK]`; read-back finds the value
  wrote to nowhere or to a phantom node. Mitigation:
  `DROP_OFFTREE_BRANCHES` (`Solar PV Rooftop` on Centralized,
  `Unmet Load_IDxx`/`_MYxx`, `Gas Engine_MY*`) +
  `DROP_BRANCHES_PER_REGION` (Indonesia/Malaysia × `Unmet Load`)
  in `build_canonical.py` + UI sample-verify post-push.
- **LEAP cache lazy-loading** — `leap.Branches.Count` enumeration is
  region-INDEPENDENT (verified: 3 caches built under
  Brunei/Indonesia/Malaysia byte-identical) but content varies
  session-to-session as LEAP materialises subtrees. Cache count
  fluctuated 4172↔5031 across same-area, same-scenario, same-Python
  sessions. The `--blind` escape hatch is the workaround.
- **Per-AMS tree shape** — Indonesia and Malaysia mix country-level
  + subnational. Subnational-only techs in ID/MY: Biogas, Solar PV,
  Solar PV Rooftop, Wind Onshore, Coal Subcritical, Diesel, Gas
  Combined Cycle, Gas Engine, Gas Turbine, Geothermal Flash, Large
  Hydro, Small Hydro, Biomass Other, Unmet Load. Country-level-only
  in ID/MY: Coal IGCC (with/without CCS), Coal Supercritical (with/
  without CCS), Coal Ultrasupercritical (with/without CCS), Bioenergy
  with CCS, Biomass Gasification, CAES, Direct Air Capture, Fuel Oil,
  Gas Combined Cycle with CCS, Gas Steam.
- **Off-tree branches in this area:** `Solar PV Rooftop` is
  Distributed-only (never on Centralized);
  `Unmet Load_IDxx`/`Unmet Load_MYxx`/`Gas Engine_MY*` don't exist;
  country-level `Unmet Load` doesn't exist under Indonesia or
  Malaysia.

#### Validated against `aeo9_v0.38_yy` (2026-05-07)
- ATS combined power standardisation: 1364 rows pushed (EC formula
  + per-year `Add(...)` Cap Add / Cap Ret deltas).
- BAS power standardisation: 1477 rows (Cap Add / Cap Ret / EC = 0
  across all power techs).
- Rev1 ID/MY round 2: 126 CA (63 EC + 63 HP) + 63 ATS HP + 63 BAS HP.
- Bioenergy + round 1.5 re-validated EXACT after separator-form fix
  (re-injected with comma-list-sep + period-decimal across all 4
  scenarios, save+reload survives).

#### Memory updates
- `reference_leap_separator_convention.md` — period-list-sep on
  read-back = inject committed wrong format, not cosmetic display
  quirk (Windows + LEAP both configured for comma-list / period-
  decimal on this engine). Re-inject fixes; save+reload preserves.

### aeo9_v0.42 RAS infeasibility resolved (2026-05-13)

Resolved a multi-week INFEASIBLE on `aeo9_v0.42` RAS via three
upstream fixes that none of our detectors caught: Unmet Load slack
visibility/cost, Optimized Trade plug-in installation, and per-fuel
inter-region trade routes for biofuel feedstocks. Earlier diagnostic
angles (4 Blending pseudo-techs with `Exogenous Capacity = Unlimited`
→ ResCap=1e12, RMTag=1 on non-power techs, biogenic CO2 EAR ~10⁷)
were real data quality issues but not the structural cause.

#### Documented (CLAUDE.md)
- **§A.11 hard rule** — `Unlimited` string is a landmine. LEAP→NEMO
  export converts literal `"Unlimited"` to `1.0e+12` regardless of
  variable. Catastrophic on lower-bound variables (becomes a forced
  1e12 floor in `ResidualCapacity`); benign-but-conditioning-toxic
  on upper bounds. NEVER reflexively zero an existing 1e12 sentinel
  on zero-cost pseudo-techs — burned 2026-05-12 (p9 EC=0 sent
  infeasibility 24k → 4.6M, 190× worse).
- **§A.12 hard rule** — Stage 1 audit clean ≠ structurally feasible.
  When `find_infeasibilities` returns 0 but solver still INFEASIBLE,
  audit Unmet Load slack visibility/cost AND inter-region trade
  routes for `MinShareProduction` feedstocks BEFORE proposing
  another placeholder.
- **§A.13 hard rule** — Hypothesis discipline: state hypothesis as
  "not proven", push smallest falsifying test, revert if worse,
  never double-down. Captured after burning twice on 2026-05-12.
- **§11.2d** — Operational signatures of the 1e12 `Unlimited` trap
  (grep `ResidualCapacity` for `val = 1.000e+12`; dual perturbation
  spikes to 10¹⁸-10²⁵).
- **§11.4** — Policy-constraint feasibility tied set: blend mandates
  + Unmet Load slack visibility + inter-region trade routes. None
  caught by `find_infeasibilities`. Full fix log from 2026-05-13.
- **§8 methodology** — Stage 1 description extended to point at
  §A.12 / §11.4 audits before extending the detector. Custom-
  constraint retirement gained a caveat distinguishing `__NEMOcc_*`
  tables (still retired) from `MinShareProduction` policy mandates
  (can cause infeasibility via missing trade routes).
- **§15.2.1 router pattern** — formalized the CLAUDE.md → memory
  redirect convention. Only `CLAUDE.md` and `MEMORY.md` are
  auto-loaded; individual memory files require topic-match-driven
  Read. CLAUDE.md must include explicit `See also: memory/X.md`
  pointers where long-form burn-log detail lives. Soft duplication
  between CLAUDE.md (rule) and memory (context) is intentional.

#### Memory updates
- `project_aeo9_v042_RAS_resolved.md` — current state of v0.42 RAS,
  what's load-bearing, what was reverted (p9).
- `feedback_hypothesis_discipline.md` — 2× burn record from
  2026-05-12; "hypothesis-not-proven" framing.
- `feedback_stage1_clean_not_enough.md` — audit Unmet Load + trade
  routes when static checks pass but solver still INFEASIBLE.
- `reference_unlimited_1e12_trap.md` — full operational detail on
  the `Unlimited` → 1e12 export translation.
- `MEMORY.md` index updated.

#### Mailbox cleanup (inject/bioenergy/)
- Removed 88 scratch files (`_probe_*`, `_probed_*`, `_audit_*`,
  `_audited_*`, `_scan_*`, `_scanned_*`, `_diag_*`, `_diagnosed_*`,
  `_check_*`, `_checked_*`, `_push_and_verify_*`, all
  `_inject_log_*`, all `_*findings*`, old patch backups, failed p9
  trio). Kept 21 durable artifacts: placeholder p1-p8 CSVs,
  HANDOVER doc, FIXSPEC doc, authoring guides, current canonical +
  unit audit + adapter pipeline.
- [`inject/bioenergy/HANDOVER_v042_r2a_RAS_infeas_to_dev_team_20260512.md`](inject/bioenergy/HANDOVER_v042_r2a_RAS_infeas_to_dev_team_20260512.md)
  — numbered-changelog handover doc covering all changes applied
  (1-16) + status (resolved by items 9-16) + files-not-to-touch.

## [0.6.7] — 11-stage infeasibility methodology with placeholder loop

Closes the loop between "the solver said something broke" and "real fix
landed in LEAP" without rabbit-chase trial-and-error. Adds Stages 4 and
5 (pattern forensics + ranked diagnostic placeholders) plus Stage 7
(minimum LEAP COM probe brief) on top of the Stage 3 LP-column decoder
shipped in 0.6.6, and gates the existing inject pipeline so diagnostic
placeholders can never be mistaken for real fixes.

The principle: exhaust the SQLite + solver report first; reduce the
residual question to the smallest possible LEAP probe; propose a
testable placeholder before any real fix is committed. Three
mechanically distinct outcomes per placeholder run (solves / same column
infeasible / new column infeasible) turn each iteration into a binary
hypothesis test.

### Added
- **`nemo_read.parameter_forensics`** ([nemo_read/parameter_forensics.py](nemo_read/parameter_forensics.py))
  — Stages 4 + 5.
  - `classify_parameter(db, parameter, related=("AvailabilityFactor",))`
    runs a five-detector battery on every `(r, t)` cluster of the
    parameter:
    - `algebraic_of(other)` — fits `MU = AF`, `MU = AF²`,
      `MU = 1 − AF`; ≥80% match fires.
    - `broadcast_across_regions` — same value-set across 3+ regions ⇒
      tech-template scope.
    - `year_split` — clean year boundary with monotonic late-year
      sequence; *ignores* AF-driven year variation (computes ratio
      against companion to avoid false positives).
    - `small_denom_fraction` — values cleanly fit `N/D` for
      `D ∈ {7, 10, 12, 13, 14, 24, 30, 52, 365}`.
    - `varies_per_timeslice_only` — load-shape-driven values.
  - Verdict per cluster: `bug` / `intent` / `unknown` / `empty`. A
    high-confidence (≥0.85) bug detector trumps intent flags so the
    squared-bug signal isn't buried by year_split firing on the same
    rows.
  - `forensics_for_pinned_variable(db, column_identity)` bridges Stage
    3 → Stage 4: looks up the candidate parameters that constrain the
    pinned variable (via `VARIABLE_TO_CANDIDATE_PARAMS`) and runs
    `classify_parameter` on each.
  - `propose_placeholders(report, max_per_report=25)` — Stage 5.
    Generates one CSV-row override per `bug` (and optionally `unknown`)
    cluster, ranked **lexicographically by `(blast_radius, -confidence,
    reverse_difficulty)`** so the smallest, most-confident,
    most-reversible test is first. Each row is tagged
    `data_confidence=PLACEHOLDER` and carries a real-fix prompt
    derived from the detected pattern.
- **`nemo_read.probe_brief`** ([nemo_read/probe_brief.py](nemo_read/probe_brief.py))
  — Stage 7. `emit_probe_brief(*reports)` compresses any residual
  `unknown` clusters (and optionally `bug` clusters when the user wants
  ground-truth before writing the real fix) into a minimum
  `(branch, variable)` LEAP COM read list, each annotated with
  hypothesis + on_confirm + on_refute. Typical brief is 3–5 reads;
  total COM time < 30s.
- **Stage-6 placeholder gate in `inject_to_leap.py`** — the existing
  injector now refuses to push rows tagged with the PLACEHOLDER
  sentinel unless `--placeholder-mode` is set. Auto-detects placeholder
  rows (via `data_confidence` column or the `PLACEHOLDER (Stage 5...)`
  note prefix), prints a clear refusal message with the offending rows
  on stderr, exits 4. Both auto-detection and the explicit flag are
  required — belt-and-braces against accidentally injecting diagnostic
  values as real fixes.
- **Stage-1 placeholder leakage check** in `validate_scenario` —
  warns if the scenario name carries a `_placeholder` suffix, catching
  cases where a placeholder run's DB is mistakenly fed to a production
  analysis.
- **Tests** ([tests/test_parameter_forensics.py](tests/test_parameter_forensics.py))
  — 11 tests covering each detector firing on the right pattern, the
  intent-vs-bug verdict logic, placeholder generation skipping intent
  clusters, lex sorting of proposals, the Stage 3 → 4 bridge, probe
  brief emission, and the inject-side placeholder split helper.

### Documented
- **[docs/infeasibility_methodology.md](docs/infeasibility_methodology.md)**
  — full 11-stage pipeline diagram, stage-by-stage tool table, the
  placeholder-loop three-outcome semantics, the worked x435004 →
  R19/Sugarcane/2025 example showing the methodology in action, when to
  skip stages, and the anti-patterns this methodology eliminates.
- **README** + **BROCHURE** — added the 11-stage pipeline diagram and
  the philosophical statement: "exhaust SQLite + solver report first;
  reduce the residual question to the smallest possible LEAP probe;
  propose a testable placeholder before any real fix is committed".
  Quick-tour code snippet shows Stages 3 → 4 → 5 → 7 in five lines.
- **[CLAUDE.md](CLAUDE.md)** — operator brief at the repo root, auto-loaded
  into every Claude Code session in this project. Captures the five
  hard rules (never patch SQLite directly; LEAP names not NEMO IDs;
  dual NEMO+LEAP terminology; bioenergy land-resource pattern; confirm
  target before reading or writing), the three workflow lanes (mailbox
  authoring → §4, results harvest → §7, 11-stage infeasibility → §8),
  the LEAP COM gotchas hoisted from session-level discoveries (§11),
  and — the linchpin — the §15 improvement loop with end-of-task
  checklist + routing table for where each kind of learning lives
  (CLAUDE.md / docs / authoring guides / per-cycle SOPs / memory /
  tests / CHANGELOG). Per §15.4: *the next session should never
  re-discover something this session already learned.*
Ran the full pipeline against the same `infeas/NEMO_25 10.sqlite` that
surfaced the original `Infeasible column 'x435004'` from 0.6.6:
- Stage 3 decoded x435004 → `vaccumulatednewcapacity[R19, P16166, 2025]`
  (Philippines / Sugarcane / 2025) ✓
- Stage 4 classified MinimumUtilization's 179 clusters as
  121 bug / 53 intent / 5 unknown — caught the squared-bug pattern
  across renewables (Tidal, Wave, Wind Offshore, Solar CSP, etc.)
  while preserving the year-split phase-out ramps and bioenergy
  harvest fractions ✓
- Stage 5 ranked placeholders top-down by smallest blast first; all
  high-confidence squared-bug clusters surfaced ahead of weaker
  signals ✓
- The R19 Sugarcane cluster came back as **intent** (small_denom_fraction
  matched 6.05/7), so MU is correctly *not* placeholdered there;
  the real-fix prompt redirects to the companion `ResidualCapacity`
  audit (units off — likely tonnes not GW) ✓

## [0.6.6] — Offline LP-column decoder for solver infeasibilities

Records the technique that resolved CPLEX `Infeasible column 'x435004'`
on AEO9/RAS without rerunning Julia: walk NemoMod's variable-creation
order from `scenario_calculation.jl`, apply Julia's column-major
(leftmost-fastest) iteration, and translate `xN` back to
`(variable_family, r, t, ..., y)` from the scenario SQLite alone.

Now part of the package's standing toolkit alongside `validate_scenario`
and `find_infeasibilities` — the static checks tell you what's wrong in
a single row, the LP-column decoder tells you which corner of the data
the solver is choking on when the contradiction is multi-constraint.

### Added
- **`nemo_read.lp_column_decode`** ([nemo_read/lp_column_decode.py](nemo_read/lp_column_decode.py)) —
  new module with the post-mortem decoder.
  - `decode_lp_column(db, column, *, varstosave=..., calcyears=...,
    forcemip=...)` → `ColumnIdentity` mapping a 1-indexed `xN` to its
    JuMP variable identity. Decodes the **dense prefix**:
    `vrateofdemandnn` (optional), `vdemandnn`, `vdemandannualnn`, the 18
    storage variables, `vnumberofnewtechnologyunits` (optional),
    `vnewcapacity`, `vaccumulatednewcapacity`, `vtotalcapacityannual`.
    Past `vtotalcapacityannual` the variables become sparse
    (`keydicts_threaded`-restricted) and aren't decodable from SQLite
    alone — the decoder reports `dense=False` with the residual offset
    rather than guessing.
  - `enumerate_dense_blocks(db, ...)` → DataFrame layout (variable, axes,
    size, start, end columns). Useful for sanity-checking the offsets
    against an LP-file dump or for spotting which family contains a
    given column range.
  - Conditional gates honoured: `vrateofdemandnn` ⇐ `varstosave`;
    `vnumberofnewtechnologyunits` ⇐ `varstosave`, nonzero
    `CapacityOfOneTechnologyUnit`, or `forcemip=True`. `calcyears`
    filters the YEAR axis when the cfg restricted years.
  - Best-effort axis descriptions: REGION/TECHNOLOGY/FUEL/EMISSION/STORAGE
    `desc` columns are joined in so output is human-readable
    (`R19`→`Philippines`, `P16166`→`Sugarcane`).
- **Tests** ([tests/test_lp_column_decode.py](tests/test_lp_column_decode.py)) —
  layout sizes; first/last/interior column decode; conditional gates
  (vrateofdemandnn, vnumberofnewtechnologyunits); past-the-prefix safety;
  invalid-column ValueError; calcyears filter.

### Documented
- **[nemo_read/infeasibility.py](nemo_read/infeasibility.py) module
  docstring** now points at `decode_lp_column` for the post-mortem case
  (when static checks are clean but the solver still reports a column
  index). Static = "what's wrong in one row"; decoder = "which row the
  multi-constraint chain pinned the contradiction on".

### Worked example (AEO9 RAS, 2026-04-30)
CPLEX presolve aborted with `Infeasible column 'x435004'`. Static
`find_infeasibilities` came up clean. Running the decoder against the
scenario SQLite returned
`vaccumulatednewcapacity[r=R19, t=P16166, y=2025]` —
**Philippines / Sugarcane / 2025**. Inspecting the surrounding data
revealed the chain: `MinimumUtilization=1.0` from 2030+ on a 1.34 GW
ResidualCapacity Sugarcane plant, output fuel `F15` (Ethanol) with zero
demand and only one downstream consumer — forced production exceeds
absorbable use, presolve walks back through the energy balance into
`vaccumulatednewcapacity ≥ 0` and reports the column.

## [0.6.5] — Bioenergy single-cap design + author-iteration workflow

End-to-end mailbox cycle validated against `aeo9_v0.33_bak` — bioenergy
(580 rows) and fossil (229 rows) injected clean, **0 unresolved + 0
no_leap_unit** in the audit. Folds the recurring-cycle patterns into
the package and records the bioenergy domain's single-cap migration.

### Added
- **`nemo_read-list-branch-vars` CLI** ([nemo_read/leap_branch_inspect.py](nemo_read/leap_branch_inspect.py)) —
  on-demand single-branch variable enumeration via existing
  `dispatch_leap` + `LeapTreeCache` + `iterate_variables_safe(fetch_expression=False)`.
  Names-only probe (no `.Expression` or `.DataUnitText` touch), so no
  result-variable modal popups can fire. Targeted alternative to
  `--all` for "what variables does this specific branch expose?"
  questions; ~15 sec on AEO9-sized trees vs 20–40 min for a full walk.
  Fallback hints when the requested FullName isn't found.
- **POME-oil LHV registry entry** in
  [nemo_read/unit_conversions.py](nemo_read/unit_conversions.py) —
  `(USD/t POME oil → USD/Tonnes of Oil Equivalent)` factor 0.8718, ★★
  confidence (LHV ≈ 36.5 GJ/t per Lam et al. 2009 / Sukiran et al.
  2017 mid-range; empirically confirmed by the AEO9 bioenergy author
  2026-04-29). Distinct from the existing `usd/t pome wet → usd/tonne`
  entry — POME-oil is the recovered oil fraction, ~36 GJ/t; POME-wet
  is the dilute effluent stream, ~1 GJ/t.

### Documented (new sections in [docs/leap_export.md](docs/leap_export.md))
- **Author-iteration workflow** — the recurring
  build_canonical → audit → unresolved → fix-at-source → re-audit →
  inject loop, with the `[YYYY-MM-DD §section author-action applied]`
  note-marker convention for cross-iteration traceability and the
  spec-vs-reference doc split (operational `*_SPEC.md` for the
  per-cycle truth, deep `*_GUIDE.md` for the technical reference).
- **Build-adapter filter pattern** — `LEAP_MISSING_BRANCHES` +
  `_is_deferred()` idiom for keeping rows in source CSV when the
  LEAP-side branch is pending or the (branch, variable) placement is
  deferred. Lets data be preserved for forward compatibility while
  unblocking the audit/inject pipeline. Worked example in
  [inject/bioenergy/build_canonical.py](inject/bioenergy/build_canonical.py).
- **Single-branch variable enumeration** — `nemo_read-list-branch-vars`
  reference, with positioning vs `nemo_read-leap-units --all`.

### Bioenergy domain — single-cap migration (mailbox-side, but worth recording)
- Two-tier (Cultivation Processes + `Resources\Primary\Arable|Perennial`
  land caps) shelved in favour of single-cap design — only
  `Resources\Primary\<Crop>:Maximum Production` caps the chain. Removed
  the entire 145-row land tier; relocated 50 `Cultivation\Maximum
  Capacity` values → `Resources\Primary\<Crop>:Maximum Production` and
  50 `Cultivation\Variable OM Cost` → `Resources\Primary\<Crop>:Production
  Cost`. 7 cycle-1 unit fixes applied (5 main-crop MaxProd × 1e6 to
  Metric Tonne; Corn ProdCost to USD/Metric Tonne after a mid-cycle
  LEAP-side unit shift; POME ProdCost converted via the new POME-oil
  LHV entry). Captured in
  [inject/bioenergy/BIOENERGY_CSV_SPEC.md](inject/bioenergy/BIOENERGY_CSV_SPEC.md)
  as the operational spec.

### Recurring gotchas (re-confirmed; both already covered in BROCHURE.md)
- **`Variable.DataUnitText` on result variables fires a modal LEAP
  dialog.** New `leap_branch_inspect` avoids this by walking
  names-only. Don't paper over it with `is_result_variable` or
  similar guards — the existing `safe_expression`/`safe_value`
  pattern is the documented fallback.
- **ActiveArea drifts between subprocess invocations.** Hit twice this
  session (LEAP closed the area; LEAP UI refocused away from the
  target). The injector's `--expect-area` check correctly aborts; the
  fix is a click in the LEAP UI to refocus, then retry.

## [0.6.4] — Defensive defaults from real-session learnings

After validating the audit→inject pipeline end-to-end against `aeo9_v0.32`
(458 successful pushes across Current Accounts + RAS), this release folds
the lessons into safer defaults.

### Changed (behaviour)
- **Injector now auto-locks to ActiveArea at script start.** When LEAP has
  multiple areas open and a cross-area scenario-name collision occurs
  (e.g. setting `ActiveScenario = "Current Accounts"` flips LEAP to a
  different area that also has that scenario), the injector aborts before
  any push. Previously this required passing `--expect-area NAME`
  explicitly. Disable via `--no-area-lock` if you really intend to allow
  area shifts during a run.
- **Tree-cache now keyed on area name only** with ±5 tolerance on
  `Branches.Count`. LEAP's count occasionally fluctuates by 1 between
  calls; the prior exact-equality check forced an unnecessary 3-minute
  rebuild on every reconnect.
- **`mailbox/run_workflow.py`** now emits the recommended inject command
  with `--no-scenario-switch` and `--expect-area "<ActiveArea>"`
  pre-populated, nudging users toward the safe pattern.

### Added
- `--no-area-lock` flag on `inject_to_leap.py` for the rare case where
  area-switching is intentional.
- `BROCHURE.md` "Gotchas (real-session learnings)" section covering the
  multi-area-open issue, cosmetic popups, branch count fluctuation, and
  result-variable Expression modals.

### Notes
- All 0.6.3 functionality is preserved; only default behaviour and UX
  changed. No new dependencies, no public API breakage.

## [0.6.3] — LEAP-side unit audit + defensible conversion proposals

### Added
- **`nemo_read/leap_units.py`** + **`nemo_read-leap-units` CLI** —
  separate probe that captures `Variable.DataUnitText` per (branch,
  variable) pair via LEAP COM and writes `branch_variable_units.csv`
  into the export directory. Two scopes:
  - `--canonical FILE` — only the pairs in the supplied CSV (fast, seconds)
  - `--all` (default) — every input variable on every branch (~20–40 min)
  Discovered via early-binding introspection: LEAP exposes the unit
  string via `DataUnitText` (the more obvious `Unit` is AttributeError).
- **`LeapAreaContext.branch_units`** field — auto-loads
  `branch_variable_units.csv` when `LeapAreaContext.from_export()` runs.
- **`audit_canonical_units(canonical_df, ctx, propose=True)`** — extended
  to add `proposed_factor`, `confidence_stars`, `conversion_source`,
  `conversion_caveat` columns when status is `mismatch`. Also detects
  `[unit]`-specifier formula expressions (e.g.
  `Import Cost[2020 USD/bbl] * 0.97`) and marks them
  `formula_reference` rather than mismatch.
- **`nemo_read/unit_conversions.py`** — defensible conversion registry
  (`UNIT_CONVERSIONS`) with citations and 5★ confidence ratings.
  Covers SI/NIST/ISO conversions (PJ↔GJ, BTU↔J, bbl↔L), IPCC default
  coal LHVs (bituminous 25.8, sub-bit 18.9, lignite 11.9 GJ/t), and
  crude oil API gravity. New `propose_conversion(from, to, fuel)` and
  `list_known_conversions()` public functions.
- **`apply_audit_conversions(canonical_df, audit_df, overrides=None)`** —
  produces a sibling DataFrame with values rewritten in LEAP-native
  units. Accepts per-row overrides keyed by `(branch, variable)` or
  `(branch, variable, ams)`. Unresolved mismatches (no proposal AND no
  override) are flagged in a new `unit_audit` column.
- **`mailbox/run_workflow.py`** — fixed 4-step pipeline (build canonical
  → probe units → audit → apply conversions). `--skip-probe` reuses
  the latest cached units file.
- **`mailbox/inject_to_leap.py`** — refuses to push `canonical_leap_inputs.csv`
  (source units) when `canonical_leap_native.csv` (LEAP units) exists.
  Override with `--ignore-units` or `--already-converted`.
- **`docs/unit_conversions.md`** — full reference table with citations,
  rubric, and override syntax.
- 11 new tests in `test_unit_conversions.py`. Full suite: 77 passing.

### Validated end-to-end
Against AEO9 RAS (`aeo9_v0.32 4` area) with 9 mailbox source CSVs:
- 27 unique (branch, variable) pairs probed for units
- 4 match, 5 formula_reference, 18 mismatch — all 18 with auto-proposals
- 229 canonical rows → 180 converted to LEAP-native units, 0 unresolved
- Injector accepts the LEAP-native CSV in dry-run mode

## [0.6.2] — Comprehensive single-shot LEAP probe + readability rule

### Added
- **Comprehensive export by default.** `nemo_read-leap-export` now captures
  input-variable expressions and demand-leaf numeric values in addition to
  the structural CSVs already produced in 0.6.0/0.6.1. Two new files in
  every export directory:
  - `branch_variable_expressions.csv` — `(branch_id, variable_name, scenario_name, expression)`
    for every input variable on every branch (active scenario).
  - `branch_variable_values.csv` — `(branch_id, variable_name, scenario_id, scenario_name, region_id, year, value)`
    for demand-tree leaves' `Final Energy Demand` and `Activity Level`
    by default. Sufficient to reconstruct demand-by-sector entirely
    offline.
- New CLI flags on `nemo_read-leap-export`:
  - `--no-expressions` to opt out of the expression dump
  - `--values-scope=demand-leaves|all-input-vars|none` to control value capture
- **`read_demand(db, *, by="fuel"|"sector", context=None, decode=True)`** —
  high-level demand reader. `by="fuel"` works against the SQLite alone;
  `by="sector"` joins LEAP-tree demand-leaf values to produce sector ×
  subsector × region × year breakdowns offline.
- **`decode_dims(df, db)`** — package-wide readability helper. Attaches
  `region_name` / `fuel_name` / `tech_name` / `emission_name` / etc.
  columns to any DataFrame carrying NEMO dim codes. New rule: any reader
  producing analysis output decodes by default; pass `decode=False` for raw
  codes when you're doing your own joins.
- `LeapAreaContext.variable_value(branch_id, variable_name, year=None,
  region_id=None, scenario_name=None)` — typed lookup against
  `branch_values`; returns scalar / Series / None.
- `safe_value(variable, year, region_id)` in `_leap_com.py` — defensive
  wrapper around `Variable.Value()` mirroring `safe_expression`.
- `iterate_variables_safe(branch, deadline_seconds=...)` per-branch
  wallclock cap to escape stuck COM calls without hanging the whole walk.
- 13 new unit tests in `tests/test_demand_and_decode.py` covering the
  readability layer, demand reader (both `by="fuel"` and `by="sector"`
  paths), and `LeapAreaContext.variable_value`.

### Fixed
- **`CostBreakdown.print()`** now reports the reconstructed sum even when
  `vtotaldiscountedcost` is zero/missing in the SQLite (e.g. when the
  variable wasn't in `varstosave`), with a clear hint about the cause.
- **Per-branch wallclock deadline** (15 s) on the nemocc/expressions/values
  walks. Prior behaviour: a single slow branch would hang the whole walk
  for hours. Now: stuck branches log a skip and the walk continues.

### Notes
- First export with the new defaults is slower (~30–60 min for an
  AEO9-sized area, dominated by demand-leaf value capture). Subsequent
  exports reuse the cached id-map JSON and re-run incrementally.
- For exhaustive captures across all branches' input variables, opt in
  with `--values-scope=all-input-vars` (~1 hour territory).

### Patches landed in this release after first build
- **Region scoping fix** for `Variable.Value()`. LEAP's COM treats the
  second positional arg of `Value(year, ...)` as a **unit** (string),
  not a region. Passing region IDs there fires "Unrecognized unit"
  modal dialogs in LEAP. The export now sets `leap.ActiveRegion = name`
  in an outer loop (12 sets total per area) before calling
  `var.Value(year)`. ~10,000× fewer global setter writes than the
  per-call alternative.
- **Names-only first pass on Variable scans.** The nemocc and expressions
  walks no longer touch `.Expression` on every variable up front (which
  fires modal dialogs on result variables). They iterate names first
  with `iterate_variables_safe(..., fetch_expression=False)`, then
  re-fetch only the matching variables.
- **`--scenario NAME` CLI flag.** Switch LEAP's ActiveScenario before
  the values walk so demand/value rows are captured for the right
  scenario without manual COM calls. Validates the scenario exists.
- **`docs/cookbook.md`** new section "Demand by sector" covering the
  end-to-end recipe (LEAP-area export + offline `read_demand`).
- **End-to-end validation** completed against AEO9 RAS: 82,080 value
  rows captured across 647 demand leaves × 9 years × 12 regions, then
  decoded into a 3996-row sector × subsector × region × year frame.

## [0.6.1] — Result-side traceback (NemoMod.jl slice A+B+C)

### Added
- `RESULT_DEPENDENCIES` in `nemo_read/schema.py` — for every NEMO result
  variable (59 entries), a `ResultDependency` dataclass listing the input
  parameters, upstream result variables, and upper/lower bounds that appear
  in its defining JuMP constraint or objective term. Sourced from NemoMod.jl
  for NEMO data-dictionary v11.
- `nemo_read/trace.py` with two user-facing helpers:
  - `trace_result(db, table, row, context=None)` — return a `ResultTrace`
    with contributing inputs (each carrying a LEAP UI hint when `context`
    is supplied), upstream results, and a `BoundCheck` flagging whether the
    row's value is hitting an upper bound, lower bound, or freely
    optimised.
  - `trace_cost(db, region, year)` — decompose `vtotaldiscountedcost` for
    one `(r, y)` into its cost streams (capital investment, operating cost,
    emissions penalty, salvage, financing — split across tech/storage/
    transmission). Returns a `CostBreakdown` with a `to_dataframe()` view
    that orders streams by absolute contribution.
- Constants `BOUND_HIT_UPPER`, `BOUND_HIT_LOWER`, `BOUND_FREE`,
  `BOUND_ABSENT`, `BOUND_UNKNOWN` for checking `trace.bound.state`.
- `tests/test_trace.py` — 10 tests against a synthetic NEMO-shaped SQLite:
  binding-bound detection, context-enriched input hints, cost-stream
  reconstruction matching total, sign conventions.

### Notes
- The ancestry data is static (encoded once from the Julia source). It does
  not compute shadow prices or run sensitivity analysis — those would need
  a solver re-run.
- `trace_cost` reports reconstructed sums so you can spot when cost streams
  don't fully sum to `vtotaldiscountedcost` (e.g. a result table missing
  from the SQLite because of a `varstosave` gap).

## [0.6.0] — LEAP-area pairing for complete SQLite decoding

### Added
- `nemo_read-leap-export` CLI (Windows-only, optional `[leap]` extra requiring pywin32).
  Run once per area with LEAP open to dump branches, fuels, regions, timeslices,
  scenarios, tags, units, nemo.cfg, customconstraints.txt, and `*__NEMOcc` sources
  into a directory adjacent to the scenario sqlite.
- `LeapAreaContext` (pure-Python, all platforms) loads that directory and exposes
  decoded LEAP metadata alongside the NEMO SQLite. `LeapAreaContext.discover(db)`
  auto-finds the adjacent `*.leap_export/` directory.
- `read_nemo_cfg()` — TOML parser for LEAP's nemo.cfg.
- `read_custom_constraints()` — static analysis of customconstraints.txt, extracts
  function names, `*__NEMOcc` table references, and pollutant → eid map.
- `LEAP_BRANCH_TYPES` — integer-code → name map (36 codes) enumerated against AEO9.
- `LEAP_SOURCE_MAP` + `LeapSource` + `where_in_leap(table, row, context)` — for any
  parameter-table row, return the LEAP branch + Variable + UI navigation hint that
  populates it. Covers 59 of 64 NEMO parameters.
- `resolve_leap_ids(df, context, ...)` — join any DataFrame with branch IDs /
  technology IDs / fuel LEAP IDs to full LEAP branch/fuel names.
- Internal `nemo_read/_leap_com.py` with `LeapTreeCache` (id/fullname-map safe
  lookup to avoid the `leap.Branches("nonexistent")` hang) and
  `safe_expression()` (try/except around the result-variable modal popup).
  Map persisted to JSON on first build; subsequent runs load instantly.
- `print_overview(db, context=ctx)`, `inspect_scenario(db, context=ctx)`,
  `validate_scenario(db, context=ctx)`, and `check_scenario(db, context=ctx)`
  all accept an optional `LeapAreaContext`. When supplied, the overview
  prepends a LEAP-area section and the validator adds a `varstosave`
  coverage check that warns when variables listed in `nemo.cfg` are missing
  from the populated v* tables.
- `tests/test_leap_area.py` with 20 unit tests covering nemo.cfg parsing,
  customconstraints extraction, `LeapAreaContext` load/discover, and the
  full `where_in_leap()` matrix across tech / process-node / module /
  result-variable cases. Full suite: 43 passing.

### Fixed
- (none — purely additive release)

## [0.5.0] — first PyPI release

### Added
- Top-level README, LICENSE (Apache-2.0), and `docs/leap_area_wishlist.md` documenting the open decoding backlog that requires LEAP Areas folder access.
- `infeasibility.py` module with `find_infeasibilities()` and `check_scenario()`.
- Static checks for: bound inversions, exogenous emissions exceeding limits, `MinShareProduction` sum > 1.0, `MinimumUtilization` > `AvailabilityFactor`, `MinStorageCharge` > `StorageLevelStart`, reserve margin without tagged technology, demand for fuels without a producer, storage without charge/discharge path, CCS unbounded-profit risk.
- `ValidationReport.extend()` for merging reports.
- `inspect_scenario()` now returns both `validation` and `infeasibilities` keys; `print_overview()` shows each as a separate section.
- Test suite `test_infeasibility.py` with eleven assertions.

### Fixed
- `dump_to_csv()` and `dump_to_parquet()` now accept either preset strings or iterables of specific table names. Previously silently wrote zero files when passed a list.
- Year filter in `get_parameter()` now works whether the user passes integers or strings; previously `{"y": ["2025"]}` returned zero rows because of a dtype mismatch.

## [0.4.0]

### Added
- `validate.py` module with `validate_scenario()` returning a `ValidationReport`.
- Checks: schema version, referential integrity on every populated parameter, `YearSplit` sums, `SpecifiedDemandProfile` sums, `NODE.r → REGION`, `TransmissionLine` endpoints, demand without profile, `MinStorageCharge` infeasibility, CCS unbounded-profit, negative emission rate info.
- `leap_conventions.py` module exposing `LEAP_NEMO_UNITS`, `units_for()`, `extract_leap_ids()`, `fuels_with_leap_ids()`, `classify_technology_id()`, `technology_kinds()`.
- `tsgroup_hours()` using the full NEMO identity (slices × `TSGROUP2.multiplier` × `TSGROUP1.multiplier` = 8760) instead of an ad-hoc representative-week formula.
- `transmission_candidates()` using `yconstruction > min(YEAR)` for correct candidate detection.
- `list_unused_technologies()` for dormant-technology discovery.
- `references/conventions_and_validation.md`.

### Fixed
- `timeslices()` now sorts by `(tg1_order, tg2_order, lorder)` instead of `lorder` alone. Previous ordering interleaved seasons and produced wrong chronological ordering for dispatch plots.

## [0.3.0]

### Added
- `custom.py` module with `list_custom_constraints()`, `get_custom_constraint()`, `detect_slack_technologies()`, `slack_technology_ids()`.
- Calculation state banner (`pre-calculation` / `post-calculation`) in `print_overview()`.
- Classified `__NEMOcc` tables as first-class (no longer flagged as unknown).

### Fixed
- `get_parameter("TransmissionModelingEnabled")` no longer fails. Previously the overlay logic hardcoded `val` as the value column, breaking for the one parameter that uses `type` instead.
- `parameter_to_dataarray()` now preserves the full dimension grid when a parameter has NaN default (e.g. `ReserveMargin`). Previously silently shrank the cube to only dimensions with stored data.
- `list_present_results()` no longer crashes on a pre-calculation database with no `v*` tables.

## [0.2.0]

### Added
- Project-package scaffolder (`nemo_read-scaffold` CLI).
- Parquet export.

## [0.1.0]

### Added
- Initial library: `NemoDB`, dimension readers, parameter reader with default overlay, result variable reader with `solvedtm` filter, xarray export, CSV export, `inspect_scenario()`.
