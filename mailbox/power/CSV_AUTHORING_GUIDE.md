# Power CSV — Authoring Guide

This document describes how power-domain authoring CSVs are shaped, what
the [`build_canonical.py`](build_canonical.py) adapter does to them, and
the canonical schema fed into `inject_to_leap.py`.

> **TL;DR.** Author CSVs in **LEAP-export shape** (the column headers
> LEAP uses when you export a branch via Tree → Export Variable). Drop
> them into `mailbox/power/<YYYYMMDD>/`. Run `build_canonical.py` over
> them. Inject the resulting `*_canonical.csv` with the standard
> [`mailbox/bioenergy/inject_to_leap.py`](../bioenergy/inject_to_leap.py)
> (the injector is domain-agnostic; only the CSV shape matters).

---

## 0. Scope — what this domain owns

Power-domain CSVs author **scenario-level overrides on
`Transformation\Centralized Electricity Generation\Processes\…` and
`…\Distributed Electricity Generation\Processes\…` branches**. Specific
authoring patterns currently in scope:

- **BAS standardisation** — clamp `Capacity Additions`,
  `Capacity Retirement`, and `Exogenous Capacity` to `0` for every
  power-tech branch in the Baseline Simulation scenario. The model
  treats BAS as "no policy interventions on the existing fleet",
  so additions/retirements/EC overrides must all be zero. Source
  `bas_all_zero.csv`-style files.
- **ATS Exogenous Capacity formula (PDP)** — set `Exogenous Capacity`
  in the AMS Target Scenario to the formula
  `Existing Capacity[MW] + Capacity Additions[MW] - Capacity Retirement[MW]`.
  This makes ATS Exogenous Capacity equal each AMS's Power Development
  Plan (PDP) — fleet held at Existing + planned Additions − planned
  Retirements. Source `ats_exo_formula.csv`-style files.
- **ATS Capacity Additions / Retirement trajectories** — author
  per-year MW deltas using LEAP's `Add(year, MW, year, MW, ...)`
  step-add syntax (one entry per year a delta occurs). Zero-rows where
  no addition / retirement is planned. The combination of these two
  trajectories with the formula above is what realises each AMS's PDP
  in ATS. Source `ats_cap_add.csv` / `ats_cap_ret.csv`-style files.

Background: see the "Ultimate fixing work" section in
[`mailbox/20260505/INJECTS_TO_REPLICATE.md`](../20260505/INJECTS_TO_REPLICATE.md)
for the original rationale.

### Per-AMS tree shape in `aeo9_v0.38_yy`

Three tree shapes coexist, and a given tech only ever appears under
one shape per AMS (mutual exclusion):

- **Indonesia** — mix of country-level branches AND subnational `_ID*`
  variants. Per tech, exactly one shape exists.
- **Malaysia** — same pattern with `_MY*` variants.
- **Other 9 AMS** (Brunei, Cambodia, Laos, Myanmar, Philippines,
  Singapore, Thailand, Timor Leste, Vietnam) — country-level branches
  only.

Subnational-only techs for Indonesia / Malaysia (live on `_ID*` /
`_MY*` branches; the country-level branch does not exist for these
techs in ID/MY): Biogas, Solar PV, Solar PV Rooftop, Wind Onshore,
Coal Subcritical, Diesel, Gas Combined Cycle, Gas Engine, Gas Turbine,
Geothermal Flash, Large Hydro, Small Hydro, Biomass Other, Unmet Load.

Country-level-only for Indonesia / Malaysia (no subnational variants
exist): Coal IGCC, Coal Supercritical, Coal Supercritical CCS, Coal
Ultrasupercritical (with and without CCS), Coal IGCC with CCS,
Bioenergy with CCS, Biomass Gasification, CAES, Direct Air Capture,
Fuel Oil, Gas Combined Cycle with CCS, Gas Steam.

The other 9 AMS carry every tech on the country-level branch — there
are no subnational variants outside ID/MY.

**Out of scope (do NOT author from this domain):**
- `Resources\Primary\…` rows (those belong to bioenergy / fossil /
  uranium).
- Any branch under `Demand\…` (demand-side authoring is a separate
  domain not yet built).
- `Capital Cost`, `Variable OM Cost`, `Maximum Availability`, lifetime,
  efficiency — those are already authored elsewhere (look at the
  v0.36 → v0.38 baseline) and changing them is a model-architecture
  decision, not power-supply standardisation.
- The `Base Template` region — it's a LEAP placeholder, not a real
  region. The adapter drops these rows automatically; do not try to
  push them.
- `Solar PV Rooftop` on
  `Transformation\Centralized Electricity Generation\Processes\…` —
  this tech is **Distributed-only** (lives under
  `Transformation\Distributed Electricity Generation\Processes\Solar PV Rooftop`)
  and was never on the Centralized tree in this area. LEAP-export
  CSVs sometimes emit rows on the Centralized path; the adapter
  drops them via the off-tree filter (§4). Confirmed 2026-05-07
  during the ATS combined inject — pushing to the Centralized path
  silently created spurious values in some regions and triggered
  a LEAP error in others.
- `Unmet Load` on Centralized — country-level branch exists for
  every AMS **except Indonesia and Malaysia** (where it's absent in
  `_yy`). No `_ID*` or `_MY*` subnational variants exist for Unmet
  Load anywhere either. The adapter drops Indonesia × `Unmet Load`
  and Malaysia × `Unmet Load` (region-specific filter, §4) and all
  `Unmet Load_IDxx` / `Unmet Load_MYxx` branches (off-tree).
  Confirmed 2026-05-07.
- `Gas Engine` on Centralized — no Malaysia subnational variants
  (`_MYxx`) exist in `_yy`; the adapter drops them (off-tree).
  Confirmed 2026-05-07.

---

## 1. Owner format — what the input CSV looks like

Files dropped into `mailbox/power/<YYYYMMDD>/` use **the LEAP-export
column shape**:

| Column        | Required | Example value |
|---------------|----------|---------------|
| `Branch Path` | yes      | `Transformation\Centralized Electricity Generation\Processes\Coal IGCC` |
| `Variable`    | yes      | `Exogenous Capacity` |
| `Scenario`    | yes (informational) | `AMS Target Scenario` |
| `Region`      | yes      | `Brunei` (or `Indonesia`, `Malaysia`, …) |
| `Scale`       | optional | usually empty |
| `Units`       | yes      | `Megawatt` / `MW` |
| `Per...`      | optional | usually empty |
| `Expression`  | yes      | `0` or `Existing Capacity[MW] + Capacity Additions[MW] - Capacity Retirement[MW]` |

Notes:
- **`Scenario` is informational** — `inject_to_leap.py` uses
  LEAP's `ActiveScenario` (set manually in the UI), not the CSV's
  `Scenario` column. The column is kept for human auditability and
  to make the CSV self-documenting. **One CSV should target one
  scenario** to make this safe (the adapter does not enforce this; it
  trusts the author).
- **One CSV per scenario** — bundle all `AMS Target Scenario` rows
  into one file (e.g. `ats_exo_formula.csv`) and all
  `Baseline Simulation` rows into another (`bas_all_zero.csv`). Don't
  mix scenarios in one file — there's no scenario-aware filter on
  the inject side, so you'd have to flip the UI scenario mid-push.
- **Region uses short LEAP names** — `Brunei`, `Laos`, `Vietnam`,
  not `Brunei Darussalam`, `Lao PDR`, `Viet Nam`. `Base Template` is
  always dropped by the adapter.
- **Indonesia & Malaysia subnational variants** — when a tech is split
  by subnational geography (e.g. `Coal Subcritical_IDJW`,
  `Biomass Other_MYSB`), the `Region` column still uses the
  country-level name (`Indonesia`, `Malaysia`) and the subnational
  identifier rides on the `Branch Path` instead. The injector
  resolves the branch by FullName, so this works as-is. Indonesia and
  Malaysia each carry **both country-level and subnational** branches
  in `aeo9_v0.38_yy` — techs with no subnational tagging live on
  the country-level branch, techs with subnational tagging live on
  the `_IDxx` / `_MYxx` branch. Other AMS only have country-level
  branches.

- **LEAP-export tools broadcast subnational rows to every region.**
  When a CSV is exported with all regions enabled, the output pairs
  every subnational branch (`Solar PV_IDJW`, `Coal Subcritical_MYSB`,
  `Biogas_MYPE`, …) with **every region**, not just Indonesia /
  Malaysia. The adapter is *expected* to drop a large fraction of
  these rows: (a) the subnational-mismatch rule keeps `_ID*` only
  when `Region == Indonesia` and `_MY*` only when `Region == Malaysia`;
  (b) the mutual-exclusion rule drops country-level rows for ID/MY
  whenever that tech has subnational variants in the same input CSV
  (per the per-AMS tree shape in §0). Both filters fire on every real
  LEAP-export drop — large drop counts in the §4 summary are normal,
  not a sign the input is wrong.
- **`Expression` accepts literals, LEAP formulas, and time-series
  functions.** Three shapes seen so far in this domain:
  1. Literal — `0`, `254`, `1500.5`
  2. Cross-variable formula — `Existing Capacity[MW] + Capacity Additions[MW] - Capacity Retirement[MW]`
  3. `Add(year, MW, year, MW, ...)` — step-add per-year capacity
     deltas (one entry per year a delta occurs). LEAP also supports
     `Interp(year, value, year, value, ...)` for piecewise-linear
     interpolation. Use **comma list-sep + period decimal** for both
     (see §5 pitfall on separator format).
  Pick the shape that matches the modelling intent: `Add()` for
  capacity deltas accumulated over time, `Interp()` for stocks /
  values that interpolate between named years, `0` for hard-clamps,
  cross-variable formula for derived series.

---

## 2. Canonical schema — what `build_canonical.py` produces

For each input `<src>.csv` the adapter writes
`<src>_canonical.csv` (alongside the source by default) with these
columns, matching what
[`mailbox/bioenergy/inject_to_leap.py`](../bioenergy/inject_to_leap.py)
reads:

| Column            | Source                          | Notes |
|-------------------|---------------------------------|-------|
| `ams`             | `Region`                        | LEAP region short name |
| `branch`          | `Branch Path`                   | passthrough, exact LEAP FullName |
| `variable`        | `Variable`                      | passthrough |
| `expression`      | `Expression`                    | passthrough |
| `unit`            | `Units`                         | passthrough |
| `fuel`            | (empty)                         | power doesn't tag fuels here |
| `source`          | input filename                  | provenance |
| `note`            | derived (`_classify`)           | `Zero-clamp on …` / `Formula on …` / `Literal value on …` |
| `src_csv`         | input filename                  | provenance |
| `domain`          | `power_<variable_slug>`         | e.g. `power_exogenous_capacity` |
| `data_confidence` | `High`                          | standardisation rules are deterministic |
| `unit_audit`      | passthrough — input unit preserved | adapter does **no** unit conversion |

The adapter does **not**:
- Convert units. The author writes LEAP-native units; the adapter trusts that.
- Compute or rewrite expressions. The CSV is the source of truth.
- Deduplicate rows. If the input has duplicates, they survive.

The adapter **does**:
- Drop every `Base Template` row (LEAP placeholder region).
- Drop **subnational-mismatch rows**: any branch whose leaf segment
  ends with `_ID<X>` (Indonesia subnational) is kept only when
  `Region == Indonesia`; same for `_MY<X>` and Malaysia. Non-ID/MY
  regions never carry subnational branches.
- Drop **country-level-for-subnational-only-tech rows** (the
  mutual-exclusion rule): for Indonesia and Malaysia, when a tech
  appears anywhere in the input CSV under a `_ID*` / `_MY*` leaf
  (e.g. `Coal Subcritical_IDJW`, `Biogas_MYPE`), the country-level
  branch for that tech (`Coal Subcritical`, `Biogas`) is *also*
  dropped from ID/MY rows — because that country-level branch does
  not exist for ID/MY in `aeo9_v0.38_yy` (see §0). Country-level
  branches still survive for any tech that has *no* subnational
  variants in the source CSV.
- Drop **off-tree rows** — branches that LEAP-export emits on a path
  that doesn't exist in this area's tree at all. Currently one entry:
  `Transformation\Centralized Electricity Generation\Processes\Solar PV Rooftop`
  (Solar PV Rooftop is Distributed-only — see §0). Add new entries to
  `DROP_OFFTREE_BRANCHES` in `build_canonical.py` when more are
  discovered.
- Rename columns to canonical lowercase (LEAP-export → injector schema).
- Stamp `domain`, `note`, `data_confidence`, and `unit_audit` per row.

All four drop counts are reported by the adapter at the end of the
run, so you can sanity-check what was filtered:

```
ats_cap_add.csv -> ats_cap_add_canonical.csv  (502 kept, 128 Base Template, 870 subnational-mismatch, 26 country-level-for-subnational-only-tech, 11 off-tree dropped)
```

Big subnational-mismatch counts (≫ ~10% of input) are **expected** on
LEAP-export CSVs that broadcast subnational branches to every region;
not a sign of a bug. The country-level-for-subonly-tech count is
proportional to how many subnational-tagged techs are in the source —
also expected to be nonzero on a broadcast export. Nearly-zero counts
are fine when the input was hand-curated. A nonzero subnational-mismatch
on a hand-curated input is a warning sign that the author included a
wrong-region row.

---

## 3. End-to-end workflow

```bash
# 0. Drop the LEAP-export-shape CSV(s) into a dated folder
ls mailbox/power/20260507/
# ats_exo_formula.csv  bas_all_zero.csv

# 1. Convert to canonical form
python mailbox/power/build_canonical.py \
    mailbox/power/20260507/ats_exo_formula.csv \
    mailbox/power/20260507/bas_all_zero.csv
# -> ats_exo_formula_canonical.csv, bas_all_zero_canonical.csv

# 2. Set ActiveScenario in LEAP UI (read it back to confirm before injecting)
#    -- AMS Target Scenario for ATS file, Baseline Simulation for BAS file.

# 3. Dry-run inject (always)
python mailbox/power/run_workflow.py \
    --csv mailbox/power/20260507/ats_exo_formula_canonical.csv \
    --expect-area aeo9_v0.38_yy \
    --expect-scenario "AMS Target Scenario" \
    --dry-run

# 4. Real inject
python mailbox/power/run_workflow.py \
    --csv mailbox/power/20260507/ats_exo_formula_canonical.csv \
    --expect-area aeo9_v0.38_yy \
    --expect-scenario "AMS Target Scenario"

# 5. Read-back-one verify (CLAUDE.md §4.1) on at least one row per
#    scenario via mailbox/20260505/_probe_readback_one.py — extend
#    PROBES dict if a new variable shape needs verifying.

# 6. Repeat 2–5 for the BAS file (flip UI to Baseline Simulation
#    first; pass --expect-scenario "Baseline Simulation").

# 7. Bundle calculatescenario for affected scenarios in LEAP UI.
```

**Use `run_workflow.py`, not `mailbox/bioenergy/inject_to_leap.py`,
for power CSVs.** In `aeo9_v0.38_yy` the LEAP COM tree enumeration
(`leap.Branches.Count`) is filtered by `ActiveRegion` — a single tree
cache built under one region cannot see the branches valid under
another. `run_workflow.py` builds three caches (Indonesia / Malaysia /
Other) matching the §0 tree shapes and dispatches each row to the
appropriate cache; `inject_to_leap.py` builds one cache and would
silently miss subnational branches outside its build region. The
bioenergy injector is still correct for bioenergy / fossil supply
trees (they're not region-filtered in the same way) — the
substitution is power-specific.

`run_workflow.py` also enforces `--expect-scenario`, which aborts if
`leap.ActiveScenario.Name` doesn't match the value passed in. Use it
on every run; it prevents the misroute trap (CLAUDE.md §11.1) where
`ActiveScenario` silently switches between back-to-back invocations.

---

## 4. Adapter behaviour — what the rename/filter actually does

`build_canonical.py` reads a LEAP-export CSV row by row, drops Base
Template rows, and writes a canonical row using the column map in §2.
A small `_classify(variable, expression)` helper picks a `domain` slug
and a human-readable `note`:

| Expression shape | `domain` (example) | `note` |
|---|---|---|
| `0` | `power_capacity_retirement` | `Zero-clamp on Capacity Retirement (BAS standardisation)` |
| `Existing Capacity[MW] + Capacity Additions[MW] - Capacity Retirement[MW]` | `power_exogenous_capacity` | `Formula on Exogenous Capacity (ATS standardisation: PDP = E + Add - Ret)` |
| `Add(2026, 10, 2027, 8, …)` | `power_capacity_additions` | `Step-add trajectory on Capacity Additions (per-year MW deltas)` |
| `Interp(2025, 254, …)` | `power_<var>` | `Interpolated trajectory on <variable>` |
| anything else | `power_<var>` | `Literal value on <variable>` |

The classifier is **string-pattern based**, so wording changes (e.g.
adding a space) might fall through to the generic `Literal value` note.
That's fine — it's not load-bearing for injection, only for human
auditability.

---

## 5. Pitfalls

- **Separator convention on this engine**
  ([reference memory](../../../../../.claude/projects/c--Users-ThinkPad-Desktop-Py-YY-NEMO-read/memory/reference_leap_separator_convention.md)).
  `Interp(...)` and `Add(...)` literals must use **comma
  list-separator + period decimal**: `Interp(2025, 254, 2030, 280)`,
  `Add(2026, 10, 2027, 8.5)`. A read-back showing period-list-sep
  means the inject committed wrong (NOT a cosmetic display issue) —
  re-inject. Confirmed 2026-05-07 across 4 scenarios.

- **`Base Template` rows are placeholders, not real regions.** The
  adapter drops them. Per CLAUDE.md §11.1, never include them in any
  `--regions` list or treat them as injectable. If you see them
  surviving the adapter, the column-name mapping in §2 broke (probably
  the input CSV used `region` lowercase instead of `Region`).

- **Scenario column is informational.** Flipping `ActiveScenario` is
  the operator's job (LEAP UI dropdown), and the inject runs against
  whatever's active at script start. **One CSV per scenario** keeps
  this safe.

- **Scenario-scoped variable trap (CLAUDE.md §11.2).**
  `branch.Variable("X")` returning `None` doesn't always mean "the
  variable was retired" — some variables are exposed only under
  certain scenarios, and visibility can flicker if LEAP's COM is in
  a transient error state. If a whole batch fails with `var_not_found`,
  refresh LEAP (click into the area, dismiss any error dialogs) before
  retrying. Confirmed during the v0.38 cycle 2026-05-07 — `Historical
  Production` returned None on ATS until LEAP was refreshed.

- **`--already-converted` flag** must be passed to
  `inject_to_leap.py` for power CSVs (canonical or not). The injector
  has a default refusal aimed at bioenergy's "use the LEAP-native
  variant" check, which doesn't apply here.

- **Subnational regions are real.** The region of a subnational
  branch (`Coal Subcritical_IDJW`) is still the country (`Indonesia`)
  in LEAP. Don't try to invent `IDJW` as a separate region in the
  CSV — that name doesn't exist in LEAP's region list and the
  injector will skip the row.

- **Cache region-filtering on `aeo9_v0.38_yy`.** `leap.Branches.Count`
  enumeration is filtered by `ActiveRegion`: a tree cache built under
  `ActiveRegion=Indonesia` does not see Malaysia's `_MY*` branches,
  and vice versa. The other 9 AMS share a country-level-only tree
  shape that is again distinct from Indonesia's and Malaysia's.
  Symptom of using the wrong cache: misleading `branch not in cache`
  / `branch_not_found` skip lines for branches that genuinely exist
  and would resolve fine if the cache had been built under the right
  region. Fix: use [`run_workflow.py`](run_workflow.py) (the canonical
  power inject driver — see §3), which builds three caches —
  Indonesia / Malaysia / Other — and dispatches each row to the
  appropriate cache. Confirmed 2026-05-07 against `aeo9_v0.38_yy`.

- **Expressions that reference other variables can be brittle.** The
  ATS formula
  `Existing Capacity[MW] + Capacity Additions[MW] - Capacity Retirement[MW]`
  works because all three referenced variables exist on the same
  branch in the same scenario. If you author a similar formula on a
  branch where one of the variables is missing or scoped to a
  different scenario, LEAP will store the formula but evaluate it as
  zero (or error) at calc time. Test with a single dry-run row first
  when introducing a new formula shape.

---

## 6. Cross-Domain Learnings

This section captures lessons that originated in another mailbox domain
but apply (or might apply) here. Per CLAUDE.md §6.3, every `CSV_AUTHORING_GUIDE.md`
maintains one of these.

- **2026-05-05 — from bioenergy:** Supply caps and per-unit cost rows
  on the same branch must share the same physical basis (raw-crop
  tonnes, not extracted-product tonnes).
  This domain: **not applicable** — power doesn't author supply caps.
  Capacity (MW) and energy (GWh) units are unambiguous and don't have
  a "raw vs processed" basis problem. See
  [bioenergy/CSV_AUTHORING_GUIDE.md §0](../bioenergy/CSV_AUTHORING_GUIDE.md)
  for the original.

- **2026-05-07 — from results-harvest cycle:** Always exclude
  `Base Template` from any region list — it's a LEAP placeholder.
  This domain: **applied** — `build_canonical.py` filters it out
  unconditionally (see §2). See
  [mailbox/20260505/RESULTS_HARVEST_SOP.md](../20260505/RESULTS_HARVEST_SOP.md).

- **2026-05-07 — from v0.38 inject cycle (this domain):** LEAP COM
  read-back returns `Interp` arguments separated by `". "` instead of
  `", "` when the expression was committed in some non-current state
  (e.g. last-cycle inject under a different engine, or
  pre-load-from-disk). Fresh COM-set commits the `, ` form correctly,
  and save+reload preserves it. **Operational rule:** every cycle's
  inject must end with a read-back-one verify; if the result is
  "NORMALISED" rather than "EXACT", re-inject. See
  [mailbox/20260505/_probe_readback_one.py](../20260505/_probe_readback_one.py)
  for the pattern.
  Other domains: **applies to bioenergy, fossil** — any domain
  injecting `Interp(...)` literals via the COM `Variable.Expression`
  setter.

- **2026-05-07 — from v0.38 power inject cycle (this domain):**
  `leap.Branches.Count` enumeration is region-filtered on
  `aeo9_v0.38_yy`-style areas, where Indonesia and Malaysia carry a
  mix of country-level + subnational (`_ID*` / `_MY*`) branches and
  the other 9 AMS are country-level-only. A single tree cache built
  under one `ActiveRegion` cannot represent all three shapes — rows
  for branches outside that region's view will be reported as
  `branch_not_found` even though they exist and would resolve under
  the correct region. Mitigation pattern: build one cache per
  region-shape group and dispatch rows by group — see
  [`run_workflow.py`](run_workflow.py) (Indonesia / Malaysia / Other,
  3 caches total).
  Other domains: **applies to bioenergy, fossil** if either domain
  ever injects onto subnational `_ID*` / `_MY*` branches in this
  area; today neither does (both target `Resources\Primary\…`,
  which is country-level), so the bioenergy `inject_to_leap.py`
  single-cache build is still correct for those domains. Re-evaluate
  if a domain starts authoring subnational supply-side rows.

- **2026-05-12 — Variable-renewable `Min Utilization = Maximum Availability`
  is forbidden** (also see CLAUDE.md §11.2c). For every variable-renewable
  process branch — Solar PV, Solar PV Rooftop, Solar Floating, **Solar CSP**,
  Wind Onshore, Wind Offshore, Tidal, Wave, Small Hydro, plus all
  subregional node variants (`_IDJW`, `_IDSA`, `_IDKA`, `_IDEast`,
  `_MYPE`, `_MYSB`, `_MYSR`) — **the `Minimum Utilization` expression
  must be `0`**, not the
  bare `Maximum Availability`. The bare-`Maximum Availability` pattern
  forces must-run at the full AF profile with no curtailment slack, which
  is (a) physically wrong for variable renewables and (b) infeasible in
  NEMO whenever the AF YearlyShape carries even a ~10⁻⁵ floating-point
  leak at some timeslice (creates `MU > AF`, primal infeas).

  If you want a soft must-run floor on a baseload-ish or
  incumbent-dispatch tech (biomass, large hydro, geothermal), use one of
  the safe patterns — all wrapped in `Min(..., Maximum Availability)` so
  the outer `Min()` guards against MU > AF:

  | Pattern | Use when | Example |
  |---|---|---|
  | `Min(<constant>, Maximum Availability)` | Static floor at a chosen capacity-factor | Vietnam Biomass Other: `Min(10.92, Maximum Availability)` |
  | `Min(Value(Historical Capacity Factor[percentage], LastHistoricalYear), Maximum Availability)` | Static floor at the tech's actual measured historical CF | Use when you want hydro / biomass to keep running at its historical CF indefinitely |
  | `Min(Interp(FirstScenarioYear, Value(Historical Capacity Factor[percentage], LastHistoricalYear), FirstScenarioYear + Key\Modeling Assumptions\Incumbent Generator Dispatch Phaseout:Activity Level[years], 0), Maximum Availability)` | Phaseout trajectory: historical CF → 0 over the configured phaseout horizon | Malaysia subregional Biomass Other (`_MYPE`, `_MYSB`, `_MYSR`) and Large Hydro `_MY*` (set 2026-05-12) |

  The phaseout-trajectory pattern centralizes the phaseout horizon under
  `Key\Modeling Assumptions\Incumbent Generator Dispatch Phaseout:Activity
  Level` so one knob drives every incumbent must-run together. Apply it
  to any tech whose dispatch should phase out on the same schedule;
  apply the static-floor or historical-CF-floor patterns to techs whose
  must-run is permanent.

  Confirmed 2026-04-30 against Brunei Solar PV (root cause of that cycle's
  RAS infeas) and re-confirmed 2026-05-11/12 against `aeo9_v0.42_r1e`
  where the same pattern existed on every AMS × 7 VRE tech families plus
  all subregional Indonesia / Malaysia node variants. Cleared via
  placeholders p4 + p5 + p6 (~100 rows) plus manual user cleanup on
  branches that didn't propagate via COM.

  Other domains: **applies to bioenergy** if any biofuel-process branch
  is ever authored with `Min Util = Max Availability`; the existing
  Min(10.92, …) pattern on Biomass Other is the safe template.
  **Does not apply to fossil** (thermal baseload MUs are intentional
  must-run anchors per modeller decision).
