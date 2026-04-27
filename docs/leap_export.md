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
