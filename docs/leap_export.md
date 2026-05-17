# LEAP area pairing

`nemo_read` can pair a NEMO SQLite scenario database with a **LEAP area export** — a directory of plain CSV/TOML/text files dumped once from a running LEAP instance. After pairing, every row in every parameter table can be traced to its LEAP UI location, without LEAP or pywin32 being installed on the analysis machine.

## Why

A scenario SQLite alone tells you *what* NEMO computed, but not *where* in LEAP the inputs came from. Knowing "the value 0.503 in `NodalDistributionStorageCapacity` came from this specific Process Node branch's `Nodal Distribution` variable" turns debugging from archaeology into a direct click.

## Usage

### Step 1 — export the LEAP area (once per area, Windows only)

Install with the `leap` extra:

```bash
pip install 'nemo_read[leap]'
```

With LEAP running and your area loaded (File → Open Area), run:

```bash
nemo_read-leap-export
```

Defaults:
- `--area` — current `ActiveArea`.
- `--output` — `<scenario_db_stem>.leap_export/` next to the .sqlite (e.g. `C:/Users/you/Documents/LEAP Areas/aeo9_v0.32/NEMO_25.leap_export/`).
- `--include-expressions` — off. Enable to dump every branch-variable's expression (slow; adds minutes).

First run takes ~3 minutes on a 5k-branch area (the COM walk is the bottleneck). The id/fullname map is cached to `.tree_cache.json` in the output directory; subsequent runs are fast.

### Step 2 — load the context alongside a NemoDB (any platform)

```python
from nemo_read import NemoDB, LeapAreaContext, print_overview

db = NemoDB("NEMO_25.sqlite")
ctx = LeapAreaContext.discover(db)          # finds the adjacent export/
# or:
# ctx = LeapAreaContext.from_export("path/to/NEMO_25.leap_export")

print_overview(db, context=ctx)
```

### Step 3 — trace any row back to LEAP

```python
from nemo_read import where_in_leap

hint = where_in_leap(
    "NodalDistributionTechnologyCapacity",
    {"n": "Indonesia Jamali", "t": "P11942", "y": "2030"},
    ctx,
)
print(hint["ui_path_hint"])
# -> Transformation\Centralized Electricity Generation\Processes\Pumped Hydro\Transmission Nodes\Indonesia Jamali
#    -> Variable: 'Nodal Distribution'
```

Covers 59 of 64 NEMO parameters directly. Returns `None` for result variables (`v*` tables) and dimensions — those don't have a single LEAP UI entry.

## Output-directory contents

```
NEMO_25.leap_export/
├── manifest.json                # area, timestamp, stats, format version
├── branches.csv                 # full tree: id, name, full_name, parent_id, parent_name,
│                                #   branch_type, branch_type_name, level, notes
├── fuels.csv                    # id, name        (joins to [LEAP ID:N] in FUEL.desc)
├── regions.csv                  # id, name
├── timeslices.csv               # id, name, hours
├── scenarios.csv                # id, name, results_shown, last_calculated
├── tags.csv                     # id, name        (LEAP branch-tag catalog)
├── units.csv                    # id, name        (unit + currency catalog)
├── nemocc_sources.csv           # *__NEMOcc table -> defining branch + expression head
├── nemo.cfg                     # verbatim from WorkingDirectory (TOML)
├── customconstraints.txt        # verbatim (Julia source)
├── beforescenariocalc.txt       # if present
├── afterscenariocalc.txt        # if present
├── .tree_cache.json             # internal map cache for fast re-exports
└── branch_variable_expressions.csv   # only when --include-expressions
```

## Decoding the files

- **`branches.csv`** — every branch with parent linkage. Join on `id` for `bid` lookups, or match tech values `P<id>`/`D<id>`/`S<id>` on the numeric suffix.
- **`nemo.cfg`** — TOML. Read with `read_nemo_cfg(path)`. Useful keys: `calculatescenarioargs.varstosave`, `solver.parameters`.
- **`customconstraints.txt`** — Julia source. Parse with `read_custom_constraints(path)` to get function names, `*__NEMOcc` table references, and the pollutant → eid map (e.g. `CO2=E2, CH4=E4, N2O=E8`).
- **`nemocc_sources.csv`** — matches each `*__NEMOcc` table name in the SQLite back to the LEAP branch that defines its input values.

## Limitations

- Windows-only exporter (pywin32 requirement). The consumption side works on any OS.
- LEAP must be running with the target area loaded. Setting `leap.ActiveArea` only switches between already-open areas; it cannot open a new area — use the LEAP UI.
- Per-scenario expression overrides aren't captured by default (one active scenario only). Use `--include-expressions` with scenarios loaded one at a time if you need per-scenario overrides.
- `RampRate`, `TradeRoute`, `REGIONGROUP`/`RRGroup` mappings are marked `unknown` in `LEAP_SOURCE_MAP` — AEO9-style areas don't exercise them. They resolve to the generic `Branch (type …)` hint until a follow-up probe nails them down.

## How the tricky bits work

Two COM behaviours would have hung or broken the exporter:

1. **`leap.Branches("non-existent FullName")` hangs LEAP forever.** The exporter never calls `Branches(str)` — it uses a pre-built `id → positional-index` map from `_leap_com.LeapTreeCache` for all lookups.
2. **`variable.Expression` on some result variables raises a modal LEAP dialog.** Every access goes through `safe_expression()` which catches `pywintypes.com_error` and `AttributeError`, returning `None` instead.

Both are fully handled — see `nemo_read/_leap_com.py`.

---

## Author-iteration workflow (recurring CSV authoring cycles)

When a domain has its own bioenergy/fossil-style mailbox (per-domain `build_canonical.py` + `run_workflow.py` + `inject_to_leap.py`), the package supports a recurring iteration pattern. Captured here so it generalises beyond bioenergy — see [inject/bioenergy/BIOENERGY_CSV_SPEC.md](../inject/bioenergy/BIOENERGY_CSV_SPEC.md) for a worked example.

**The cycle:**

```
build_canonical.py  →  audit (probe + audit_canonical_units)  →  unresolved?
                                                                   │
                                            ┌──────────────────────┴───────────────────────┐
                                            │                                              │
                                       no   │                                              │   yes (per-row)
                                            ▼                                              ▼
                              apply_audit_conversions                       fix at source CSV (author-action)
                              → canonical_leap_native.csv                   tag note with [date §X author-action applied]
                                            │                                              │
                                            └──────────────────────┬───────────────────────┘
                                                                   ▼
                                                              re-audit
                                                       (target: 0 unresolved + 0 no_leap_unit)
                                                                   │
                                                                   ▼
                                                           inject_to_leap.py (--dry-run, then for-real)
```

**Three mechanics that make the cycle stable:**

1. **`audit_canonical_units` returns one of four statuses per (branch, variable) pair**: `match` (canonical unit ≡ LEAP unit, no action), `mismatch` with a `proposed_factor` (registry handles auto-conversion at inject time), `mismatch` with no factor (author-action — fix at source), or `no_leap_unit` (branch missing from LEAP tree — exclude or create branch). Author-action mismatches are the only ones that block injection.

2. **Source-side note markers preserve traceability across iterations.** When the author fixes a row at source per `audit_canonical_units`'s guidance, the convention is to prepend a `[YYYY-MM-DD §section author-action applied]` token to the row's `note` column. Reviewers can grep the source CSV to find the cycle's manual fixes; subsequent iterations preserve the marker so units don't accidentally drift back. Used in `inject/bioenergy/CSV_AUTHORING_GUIDE.md §12.1` to track 7 cycle-1 fixes across 70 rows.

3. **Spec-vs-reference doc split.** Each mailbox can carry two complementary docs: a deep technical reference (`CSV_AUTHORING_GUIDE.md`-style — column conventions, audit registry, branch-creation templates) and an operational spec (`*_SPEC.md`-style — the per-cycle truth: row-count expectations, exact (branch, variable) matrix, do-not-modify rules, anti-patterns). The reference is the textbook; the spec is the operational checklist the author opens first.

---

## Build-adapter filter pattern (rows-in-source / not-yet-in-LEAP)

When the source CSV authors rows that LEAP doesn't expose yet — either branches that need to be created later, or variables on the wrong branch pending placement clarification — the build adapter filters them at canonical-build time so the audit and injection don't trip. The pattern, used in [inject/bioenergy/build_canonical.py](../inject/bioenergy/build_canonical.py):

```python
# Branches that exist in the source CSV but are missing in LEAP.
# Once the LEAP-side branches are added, drop these entries.
LEAP_MISSING_BRANCHES = {
    "Resources\\Primary\\Rice Straw",
    "Resources\\Primary\\Used Cooking Oil",
    # ...
}

# (branch, variable) patterns LEAP doesn't expose on the branch as
# authored. Held back until placement is resolved.
EMISSION_FACTOR_VARIABLES = {"CO2 (process)", "CH4 (process)", ...}

def _is_deferred(branch: str, variable: str) -> bool:
    if variable in EMISSION_FACTOR_VARIABLES and "\\Feedstock Fuels\\" in branch:
        return True
    # ... other deferred (branch, variable) patterns
    return False

# In the row loop:
if branch in LEAP_MISSING_BRANCHES:
    skipped_leap_missing[branch] += 1
    continue
if _is_deferred(branch, variable):
    skipped_deferred[(branch, variable)] += 1
    continue
```

**Why a build-adapter filter and not a source edit:** keeping the rows in source means data is preserved for the day the LEAP-side branch is added (no re-derivation needed). The filter is the gate; once `LEAP_MISSING_BRANCHES` shrinks (or `_is_deferred` returns False for a previously-deferred pattern), the rows flow through to canonical and inject automatically.

**Print a WARNING summary at end of `build_canonical.py`** so the author can see exactly which rows got filtered and why:

```
WARNING: filtered 70 rows on LEAP-missing branches:
    20  Resources\Primary\Rice Straw
    20  Resources\Primary\Used Cooking Oil
    30  Transformation\Bioethanol Production\Processes\Cellulosic Rice Straw

WARNING: filtered 210 deferred rows:
    10  Resources\Secondary\Biodiesel:CO2 biogenic
    10  ...\CME Biodiesel\Feedstock Fuels\Coconut Oil:CH4 (process)
    ...
```

---

## Single-branch variable enumeration (`nemo_read-list-branch-vars`)

For "what variables does this specific LEAP branch expose?" questions — the leaner Cultivation Process subtype (~30 vars) vs a regular Biofuel Production process (44 vars) is a real example — use the focused CLI:

```bash
nemo_read-list-branch-vars "Transformation\\Palm Oil Cultivation\\Processes\\Palm Oil Cultivation"
```

Connects to the running LEAP via existing `dispatch_leap`, builds the `LeapTreeCache`, looks up the branch by FullName, and dumps variable names via `iterate_variables_safe(fetch_expression=False)` — names only, no `.Expression` or `.DataUnitText` access, so no result-variable modal popups can fire from the probe at all. ~15 sec on an AEO9-sized tree (cache build dominates).

If the FullName doesn't match an existing branch, the CLI prints similar branches as fallback hints (e.g., requesting `…\Cellulosic Rice Straw` would suggest the existing `…\Corn Ethanol`-style siblings). Useful for catching pathing typos without a full tree walk.

This is the targeted alternative to `nemo_read-leap-units --all` (~20–40 min, walks every branch). Reach for `--all` only when you need DataUnitText for every (branch, variable) pair across the tree; reach for `nemo_read-list-branch-vars` when you have one specific branch in mind.
