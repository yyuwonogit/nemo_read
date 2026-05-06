# nemo_read

**Decode LEAP/NEMO scenario SQLite databases — and pair them with a one-shot LEAP export so every analytical question works offline.**

## Why

A NEMO scenario `.sqlite` carries the numbers but loses the LEAP-side context — sectors, branch hierarchy, custom-constraint sources, formula expressions. `nemo_read` recovers all of it in a way that survives without LEAP installed.

## Infeasibility resolution pipeline (the 11-stage methodology)

When CPLEX/Cbc/Gurobi reports `Infeasible column 'xN'` (or any other dead
end), `nemo_read` ships the full sequenced process:

```
1  PRE-FLIGHT          validate_scenario, find_infeasibilities
2  SOLVER RUN          (LEAP/NEMO/CPLEX)
3  POST-MORTEM TRIAGE  decode_lp_column        ← xN → vfamily[r,t,y]
4  PATTERN FORENSICS   classify_parameter      ← bug vs intent per (r,t)
5  PLACEHOLDER         propose_placeholders    ← ranked diagnostic patches
6  DIAGNOSTIC TEST     inject_to_leap.py --placeholder-mode + re-run
                              ┌─ solves          → cause CONFIRMED → Stage 9
                              ├─ same xN         → wrong cluster, try next
                              └─ new xN          → cause confirmed; new loop
7  PROBE BRIEF         emit_probe_brief        ← only if Stage 6 stuck
8  LEAP COM PROBING    nemo_read._leap_com
9  REAL-FIX DESIGN     (manual, informed by 4+6+8)
10 PATCH INJECTION     inject_to_leap.py        (refuses placeholder rows
                                                without --placeholder-mode)
11 VERIFICATION        loop back to Stage 1
```

The principle: **exhaust the SQLite + solver report before any LEAP probe;
propose a testable placeholder before any real fix is committed**. Three
mechanically distinct outcomes per placeholder run turn debugging into
hypothesis testing. Every stage has a tool and an exit criterion.

Detector battery in Stage 4 (each (r, t) cluster):
`algebraic_of(other)`, `broadcast_across_regions`, `year_split`,
`small_denom_fraction`, `varies_per_timeslice_only`. Verdict per cluster:
`bug` / `intent` / `unknown`. Stage 5 emits placeholders only for `bug`
and `unknown`, ranked lex by `(blast_radius, -confidence, reverse_difficulty)`
so the smallest, most-confident, most-reversible test runs first.

Worked example end-to-end in [docs/infeasibility_methodology.md](docs/infeasibility_methodology.md).

## Architecture in one diagram

```
   Windows (LEAP installed, run once)         Any OS (analysis side)
   ┌──────────────────────────────────┐       ┌─────────────────────────────┐
   │  nemo_read-leap-export           │  ──►  │  NemoDB("scenario.sqlite")  │
   │  (Python + pywin32 + LEAP COM)   │       │  LeapAreaContext.discover() │
   │                                  │       │                             │
   │  Walks the LEAP area, dumps:     │       │  Now you can:               │
   │  - branches.csv (full tree)      │       │  - read_demand by sector    │
   │  - branch_variable_values.csv    │       │  - where_in_leap any row    │
   │  - fuels/regions/timeslices/...  │       │  - trace_result with bound  │
   │  - nemo.cfg, customconstraints   │       │  - trace_cost decomposition │
   └──────────────────────────────────┘       └─────────────────────────────┘
                                                            ▲
                                                            │
                                              from any platform, any time
```

## Install

```bash
pip install nemo_read              # core (any OS, no LEAP)
pip install 'nemo_read[leap]'      # adds pywin32 for the exporter (Windows only)
```

## The flow

```bash
# 1. Once per area (Windows + LEAP open):
nemo_read-leap-export --scenario "Regional Aspiration Scenario"

# 2. Forever after, anywhere:
python -c "
from nemo_read import NemoDB, LeapAreaContext, read_demand
db = NemoDB('NEMO_25.sqlite')
ctx = LeapAreaContext.discover(db)
print(read_demand(db, by='sector', context=ctx).head())
"
```

## Capabilities

### Reading the SQLite alone (no LEAP)
- 14 dimensions, 64 parameters, 88 result variables — full schema metadata in `nemo_read.schema`
- `get_parameter` reconstructs the default-overlay even on pre-calculation databases
- `get_result` filters latest `solvedtm` automatically; `solvedtm_values()` lets you walk history
- xarray cubes, CSV / Parquet bulk export
- Time-slice expansion (YearSplit × 8760), aggregation to TSGROUP1/2
- Validation suite: referential integrity, YearSplit sums, demand-profile coverage, CCS unbounded-profit risk, etc.
- Static infeasibility detector: bound inversions, MinimumUtilization > AvailabilityFactor, reserve-margin gaps
- **11-stage infeasibility-resolution methodology** — pre-flight checks → solver run → LP-column triage (`decode_lp_column`) → pattern forensics with bug-vs-intent classification (`classify_parameter`) → ranked diagnostic placeholders (`propose_placeholders`) → diagnostic test cycle → minimum LEAP COM probe brief (`emit_probe_brief`) → real-fix design → injection (`inject_to_leap.py --placeholder-mode` gate). Three mechanically distinct outcomes per placeholder run turn debugging into hypothesis testing — no rabbit-chase. See [docs/infeasibility_methodology.md](docs/infeasibility_methodology.md).

### Reading the LEAP area (one-shot probe, then forever offline)

The `nemo_read-leap-export` CLI walks the entire LEAP area through the COM API and writes a self-contained directory of plain CSV / TOML / text files next to your scenario `.sqlite`. After this runs once, the LEAP application doesn't need to be open (or even installed) on any machine that consumes the data.

**Captured by default** (~30–60 min one-time on an AEO9-sized area):

| File | Contents | Scale |
|---|---|---|
| `branches.csv` | **Every branch in the LEAP tree** — id, Name, FullName, parent_id, parent_name, BranchType (37-code map), level, **Notes** (provenance text) | All 5066 branches in AEO9: every Demand sector & subsector & technology, every Transformation Module & Process & Process Node, every Resource, Key Assumption, Transmission Line, Environmental Effect, Custom Constraint host |
| `branch_variable_values.csv` | Numeric `Value()` readings for demand-tree leaves' `Final Energy Demand` and `Activity Level`, all years × all regions × active scenario | ~80,000 rows on AEO9 — sufficient to reconstruct demand-by-sector entirely offline |
| `fuels.csv`, `regions.csv`, `timeslices.csv`, `tags.csv`, `units.csv`, `scenarios.csv` | Top-level LEAP catalogues with IDs and names | 66 fuels, 12 regions, 48 timeslices, 26 tags, 203 units, 11 scenarios in AEO9 |
| `nemocc_sources.csv` | Every `*__NEMOcc` user variable mapped to the LEAP branch that defines it | Resolves the bid → branch link in `__NEMOcc` SQLite tables |
| `nemo.cfg` | Verbatim TOML — `varstosave`, solver params, includes | Plain copy from LEAP's WorkingDirectory |
| `customconstraints.txt` | Verbatim Julia source | Parsed by `read_custom_constraints()` for function names, NEMOcc table refs, and pollutant→eid map |
| `manifest.json` | Export metadata — area, scenario, base/end years, format version, stats | For reproducibility |

**Optional broader captures** (opt-in CLI flags):

- `--include-expressions` — every input variable's `Expression` string (LEAP-side formulas like `Interp(2025, 35, 2040, 63, ...) ? RAS assumption`) for the active scenario across every branch
- `--values-scope=all-input-vars` — `Value()` capture extended beyond demand leaves to every input variable on every branch (~1 hour territory, generates large CSVs)

**Defensive infrastructure that makes the walk reliable**:

- `LeapTreeCache` builds `id → positional-index` and `FullName → positional-index` maps once, then caches to JSON. Avoids the LEAP COM hang where `Branches("non-existent")` blocks indefinitely.
- `safe_expression()` and `safe_value()` swallow the modal "Expressions are not used for result variables" / "Unrecognized unit" dialogs LEAP fires on certain reads.
- 15-second per-branch deadline so a single stuck branch can't hang the whole export.
- Region scoping uses `leap.ActiveRegion` global setter in an outer loop — 12 sets per area instead of thousands.
- Persistent JSON cache means re-runs (after structural area changes) skip the slow id-map build and reuse it incrementally.

### Pairing the two
- `where_in_leap(table, row, context)` — any parameter row → branch FullName + LEAP UI variable name + UI navigation hint. Covers 59 of 64 NEMO parameters.
- `read_demand(db, by="sector", context=ctx)` — sector × subsector × region × year breakdown without LEAP
- `trace_result(db, table, row, context)` — for any result row, list contributing inputs (each with LEAP UI hint) + binding-constraint detection (hit upper / floored / freely optimised)
- `trace_cost(db, region, year)` — decompose `vtotaldiscountedcost` into capex / opex / emissions-penalty / salvage / financing streams, by tech/storage/transmission
- `decode_dims(df, db)` — package-wide rule: any DataFrame with NEMO codes (r, f, t, e, s, l, n) gets human names attached

### Other utilities
- `nemo_read-scaffold` CLI — generates a `src`-layout project package wrapping the reader for a research repo (registry, loaders, Parquet cache, CLI, tests)
- `nemo_read-list-branch-vars` CLI (since 0.6.5) — single-branch variable enumeration via COM (names-only, no result-var modal popups). Targeted alternative to `nemo_read-leap-units --all` when you want to see what variables one specific branch type exposes.
- `slack_technology_ids()` — auto-detects "Unserved" / "Unmet Load" pseudo-processes
- `units_for(variable_name)` — labels every parameter and result with its LEAP-NEMO unit (PJ / GW / M$ / t)

## Status — v0.6.5

- 66 unit tests passing
- End-to-end validated against multiple AEO9 scenarios — `aeo9_v0.32` (458 rows, 0.6.4) and `aeo9_v0.33_bak` (809 rows across bioenergy + fossil mailboxes, 0.6.5) — with 0 unresolved unit mismatches at injection time
- Documented author-iteration workflow + build-adapter filter pattern in [docs/leap_export.md](docs/leap_export.md) for recurring per-domain CSV authoring cycles
- Repository: https://github.com/yyuwonogit/nemo_read
- Wheel + sdist built; PyPI publication pending

## Gotchas (real-session learnings)

- **Multi-area open**: when LEAP has more than one area open, setting `leap.ActiveScenario` over COM can jump to a different open area if it has a scenario with the same name. The injector auto-locks to the ActiveArea at start (since 0.6.4) and aborts if it shifts. **Best practice: keep only the target area open during a push.**
- **Cosmetic LEAP popups**: setting an Expression on a branch where the variable isn't visible for a particular region (e.g. Cambodia → Refinery Capacity) triggers an informational LEAP popup. The COM call still succeeds; just dismiss the dialog. The script reports `[OK]` either way.
- **Branch count fluctuates by ±1**: LEAP's `Branches.Count` can vary between calls. The tree-cache (since 0.6.4) tolerates ±5 to avoid unnecessary 3-minute rebuilds.
- **Result-variable Expression access fires modals**: reading `Variable.Expression` on a *result* variable triggers a "Expressions are not used for result variables" dialog. The package uses a names-first iteration pattern to avoid touching `.Expression` on result variables. If you see one, the script's still alive — dismiss it.

## More

- **Cookbook**: `docs/cookbook.md` — 17 recipes, from first-look inventory to demand-by-sector
- **LEAP export reference**: `docs/leap_export.md` — the export directory format + pairing convention
- **Unit conversions**: `docs/unit_conversions.md` — defensible conversion factors with citations + 5★ confidence rubric
- **Schema**: `nemo_read.PARAMETERS`, `nemo_read.RESULT_VARIABLES`, `nemo_read.LEAP_SOURCE_MAP`
- **Wishlist + open work**: `docs/leap_area_wishlist.md`
