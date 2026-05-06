# CLAUDE.md — guidance for Claude Code in this repo

> **Status.** This file is the operating brief for any Claude Code (or
> other agentic LLM) session working inside `nemo_read`. If something here
> conflicts with what the user just said, **the user wins** — update this
> file (or flag the conflict) rather than ignoring them. This file is a
> live document; see §15 for how it stays current.

---

## 0. Starting cold? Read in this order

A fresh session, in 60 seconds:

1. **§2 — Hard rules.** Five standing rules. Don't violate them.
2. **§3 — Repo layout.** Two halves: `nemo_read/` (library) +
   `mailbox/` (authoring pipeline + dated drops).
3. Pick the workflow that matches the task:
   - **§4 — Mailbox workflow** (CSV → inject upstream into LEAP)
   - **§7 — Results harvest SOP** (read calculated results out of LEAP)
   - **§8 — 11-stage infeasibility methodology** (solver said it broke)
4. **§15 — End-of-task checklist.** Run through this before saying "done."

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
can both follow. Starter mapping (extend as needed):

| NEMO side | LEAP side |
|---|---|
| `SpecifiedAnnualDemand` + `SpecifiedDemandProfile` | Demand branch annual value + Load Shape |
| `AvailabilityFactor` | `Maximum Availability` on the process |
| `MinimumUtilization` | `Minimum Availability` (or capacity-factor floor) |
| `CapitalCost` | `Capital Cost` on the process |
| `ResidualCapacity` | `Exogenous Capacity` |
| `TotalAnnualMaxCapacity` / `…MinCapacity` | `Maximum Capacity` / `Minimum Capacity` |
| `EmissionActivityRatio` | Pollutant intensity on Environmental Loadings |
| `__NEMOcc_*` tables | Custom Constraint host branches + `customconstraints.txt` |

### 2.4 Bioenergy: land-resource modelling pattern
Perennial / Arable land are intentionally modelled as **GJ-equivalent
Primary fuels with a 1 GJ/ha anchor**, producing a deliberate
**double-cap** (land cap + per-crop yield projection). This is *not* a
modelling bug to be "cleaned up." If a fix you're proposing collapses
that double-cap, escalate to the user before changing it.

Single-cap design (current truth, see
[mailbox/bioenergy/CSV_AUTHORING_GUIDE.md](mailbox/bioenergy/CSV_AUTHORING_GUIDE.md)
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
├── mailbox/
│   ├── bioenergy/                  domain — see CSV_AUTHORING_GUIDE.md
│   ├── fossil/                     domain — coal/gas/oil supply + cost rows
│   └── <YYYYMMDD>/                 dated drops + per-cycle SOPs (§7)
├── tests/                          pytest suites — keep green
├── docs/                           topic references (see §9)
└── infeas/                         scratch DBs for live infeasibility runs
```

Convention note: this repo follows the **tyuwono PyPI template** —
flat layout (package directory at root, *no* `src/`), `pyproject.toml`
with setuptools, Apache-2.0, tag-driven publishing via GitHub Actions
trusted publishing. Sibling repos look the same; reuse the pattern.

---

## 4. The mailbox / authoring workflow (write-side: CSV → LEAP)

When the user asks you to "fix the bioenergy CSV" or "add a new fossil
import-cost trajectory," this is the loop:

0. **Confirm the target** — area, scenario, and `.sqlite` (§2.5).
   Don't skip; this is the front-line check against operating on the
   wrong file.
1. **Author or edit the input CSV** under the right domain
   (`mailbox/bioenergy/bioenergy_leap_input.csv`,
   `mailbox/fossil/<topic>.csv`, etc.). Match the column conventions in
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
├── inject_to_leap.py             COM injection (re-uses _leap_com)
├── run_workflow.py               one-shot driver: build → dry-run → push
└── unit_audit.csv                per-row unit-conversion audit trail
```

The injector itself should be a thin wrapper around
`nemo_read._leap_com.LeapTreeCache + dispatch_leap` — copy from
`mailbox/bioenergy/inject_to_leap.py` and adjust filters. Don't
re-implement COM defensiveness; the package already owns it.

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
> **Cross-domain check:** scan `mailbox/fossil/crude_oil_max_production.csv`
> vs `mailbox/fossil/crude_production_cost.csv` — both per-tonne crude;
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

When the analyst just wants the **calculated result numbers** out of a
`.leap` area (not a full read+write area dump), use the established
A → B → C pipeline. **Canonical reference, with command lines, defaults,
and a 9-pitfall postmortem:**
[mailbox/20260505/RESULTS_HARVEST_SOP.md](mailbox/20260505/RESULTS_HARVEST_SOP.md).
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

### 7.1 When NOT to use this SOP

Use the full [`nemo_read-leap-export`](nemo_read/leap_export.py) CLI
(plus `LeapAreaContext.discover()`) instead when:

- You need **input-side data** (input variable values, expressions,
  formulas) in addition to results.
- You need a **self-contained area dump** that other analysts can use
  without LEAP installed.
- The analysis question goes beyond "what came out of this run."

The A → B → C pipeline is the **focused, fast** counterpart for "I just
want the result numbers, properly unit-annotated."

### 7.2 Each cycle's artifacts live in `mailbox/<YYYYMMDD>/`

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

### 7.3 Pitfalls — DON'T repeat (full list in the SOP doc)

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

### 7.4 SOP discoverability — the meta-rule

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

## 8. The 11-stage infeasibility methodology

Centerpiece of the package since 0.6.6/0.6.7. When the solver reports
`Infeasible column 'xN'`, follow this sequence — don't skip stages:

```
1  PRE-FLIGHT          validate_scenario + find_infeasibilities → check_scenario
2  SOLVER RUN          (LEAP / NEMO / CPLEX)
3  POST-MORTEM TRIAGE  decode_lp_column(db, N)        → vfamily[r,t,y]
4  PATTERN FORENSICS   classify_parameter             → bug / intent / unknown
5  PLACEHOLDER         propose_placeholders           → ranked diagnostic patches
6  DIAGNOSTIC TEST     inject_to_leap.py --placeholder-mode
                          ├─ solves         → cause CONFIRMED → Stage 9
                          ├─ same xN        → wrong cluster, try next
                          └─ new xN         → cause confirmed; new loop
7  PROBE BRIEF         emit_probe_brief               → minimum LEAP COM read list
8  LEAP COM PROBING    nemo_read._leap_com
9  REAL-FIX DESIGN     manual, informed by 4 + 6 + 8
10 PATCH INJECTION     inject_to_leap.py              (placeholder gate refuses
                                                       Stage-5 rows without flag)
11 VERIFICATION        loop back to Stage 1
```

Two things you must preserve:

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
| [docs/infeasibility_methodology.md](docs/infeasibility_methodology.md) | full 11-stage pipeline + worked x435004 example |
| [docs/schema.md](docs/schema.md) | NEMO v11 column reference |
| [docs/cookbook.md](docs/cookbook.md) | analysis recipes (capacity stack, demand by sector, …) |
| [docs/leap_integration.md](docs/leap_integration.md) | LEAP COM API + `_def` view semantics |
| [docs/leap_export.md](docs/leap_export.md) | `nemo_read-leap-export` directory format + author-iteration workflow |
| [docs/conventions_and_validation.md](docs/conventions_and_validation.md) | units, IDs, validation, infeasibility |
| [docs/unit_conversions.md](docs/unit_conversions.md) | defensible conversion factors with citations + 5★ confidence rubric |
| [docs/scaffolding.md](docs/scaffolding.md) | the `nemo_read-scaffold` CLI |
| [docs/leap_area_wishlist.md](docs/leap_area_wishlist.md) | open-work backlog |
| [mailbox/bioenergy/CSV_AUTHORING_GUIDE.md](mailbox/bioenergy/CSV_AUTHORING_GUIDE.md) | bioenergy mailbox column conventions |
| [mailbox/bioenergy/BIOENERGY_CSV_SPEC.md](mailbox/bioenergy/BIOENERGY_CSV_SPEC.md) | bioenergy spec (single-cap design) |
| [mailbox/20260505/RESULTS_HARVEST_SOP.md](mailbox/20260505/RESULTS_HARVEST_SOP.md) | results-harvest A→B→C SOP + 9-pitfall postmortem (carry forward to next cycle) |

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
   `nemo_read/__init__.py`.
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

Run through this before saying "done" to the user:

- [ ] **Tests.** `python -m pytest` clean (or new test added for the new
      behaviour / regression).
- [ ] **`__all__` synced** if any public symbol was added/renamed/removed.
- [ ] **Version bump?** If this is a release-worthy change, both
      `pyproject.toml` and `nemo_read/__init__.py` updated.
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
