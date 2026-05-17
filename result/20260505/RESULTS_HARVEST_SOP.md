# Results-harvest SOP — the lite three-step process

Pass-through document for the CLAUDE.md creator instance.

This is the established **lite** procedure for pulling LEAP-side
calculated results out of a calculated `.leap` area when the analyst
just needs results (not a full LEAP-side dump). The full read+write
workflow lives in [`nemo_read-leap-export`](../../nemo_read/leap_export.py)
and is documented in [`BROCHURE.md`](../../BROCHURE.md); use that when
the question is broader than "I want the results of this run."

The three steps run in fixed order: **A → B → C**.

```
   ┌─ Step A ────────────────────────────────────────────────────────┐
   │  probe_leap_results.py — read RESULT-side values via COM        │
   │  per scenario × per region × per year. Slow (~50 min/scenario   │
   │  on AEO9-sized areas).                                          │
   │  Output: results_<scenario>_<context>.csv                       │
   │    columns: ams, branch, branch_type, variable, year, value     │
   └─────────────────────────────────────────────────────────────────┘
                                  ↓
   ┌─ Step B ────────────────────────────────────────────────────────┐
   │  probe_leap_units.py — read INPUT-side units via COM            │
   │  once per area (scenario- and region-agnostic). Fast (~4 min).  │
   │  Output: units_<context>.csv                                    │
   │    columns: branch, branch_type, variable, unit                 │
   └─────────────────────────────────────────────────────────────────┘
                                  ↓
   ┌─ Step C ────────────────────────────────────────────────────────┐
   │  join_results_with_units.py — merge A + B → annotated CSV.      │
   │  Pure offline (no LEAP). Result variables get units from a      │
   │  curated INFERENCE_TABLE because they share no names with input │
   │  variables.                                                     │
   │  Output: joined_<scenario>_<context>.csv                        │
   │    columns: ams, branch, branch_type, variable, year, value,    │
   │             unit, unit_source                                   │
   └─────────────────────────────────────────────────────────────────┘
```

Why two probes instead of one? Because LEAP COM exposes units only on
the **input-side** of variables, never on the result side. Reading
`Variable.DataUnitText` on a result-side variable fires LEAP's
"Data units are not available for result variables" modal. The split
isolates the value-reading loop (which uses safe per-region/year
iteration) from the unit-reading loop (which uses safe index-based
first-occurrence on a curated input-only target list).

---

## Step A — probe_leap_results.py (read-side values)

### Command

```bash
python mailbox/<YYYYMMDD>/probe_leap_results.py \
    --scenario "BAS" \
    --branch-prefix "Transformation\\Centralized Electricity Generation" \
    --regions "Brunei,Cambodia,Indonesia,Laos,Malaysia,Myanmar,Philippines,Singapore,Thailand,Vietnam,Timor Leste" \
    --years 2025,2030,2035,2040,2045,2050,2055,2060 \
    --skip-zeros \
    --out mailbox/<YYYYMMDD>/results_BAS_centralized.csv
```

### Default result variables (verified against AEO9_v0.36 May 2026)
- `Energy Generation` (output, energy units)
- `Power Generation` (output, power units)
- `Existing Capacity` (total installed capacity)
- `Capacity Additions` (new builds in year)
- `Capacity Retirement` (retired in year)
- `Costs of Production` (total cost)
- `Curtailed Energy Production` (spilled output)
- `Pollutant Loadings` (emissions)

### Defaults — branch types
`{2, 3, 4, 34, 50}` (Module, Process, Demand Tech, Effect, Transformation
Branch). Wider than Probe B because result variables can live on more
branch types — Module-level aggregates, etc.

### Defaults — regions
**Always exclude `Base Template`** — it's a LEAP placeholder, not a real
region. The `--regions` flag should list the 11 ASEAN countries
explicitly.

### Defaults — years
`2025,2030,2035,2040,2045,2050,2055,2060`. The LEAP area's BaseYear may
be 2005 or earlier; pre-model years are zero-padded and inflate the CSV
~7× without adding signal. Restrict explicitly.

### Defaults — `--skip-zeros`
Recommended on for results scans. Most (year × branch × region) cells
are zero for any one tech (e.g., Indonesia Tidal in 2025); skipping cuts
the CSV ~10× without losing meaning.

### Pacing
- Probe overhead before first row (LEAP COM init + branch tree build):
  **~3 min**.
- Per-region cost: ~5 min average (variable-enumeration overhead
  dominates over cell reads).
- Total for 11 regions: **~50 min** per scenario.

### Multi-area trap (CRITICAL)
LEAP can have **multiple areas open simultaneously**. Setting
`leap.ActiveScenario = "BAS"` may cause LEAP to switch to a DIFFERENT
area if a scenario named "BAS" exists in another open area. The
symptom: `Branches indexed: <very different number>` and `Branches to
walk: 0` after prefix filter.

The probe has an area-lock guard: it records the initial area name and
aborts with exit code 3 if the area changes. Two recovery paths:
- **(a)** in LEAP UI, close all areas except the target. Re-run normally.
- **(b)** in LEAP UI, manually switch the dropdown to the right area
  + scenario, then re-run with `--no-scenario-switch`.

---

## Step B — probe_leap_units.py (write-side units)

### Command

```bash
python mailbox/<YYYYMMDD>/probe_leap_units.py \
    --branch-prefix "Transformation\\Centralized Electricity Generation" \
    --out mailbox/<YYYYMMDD>/units_centralized.csv
```

No `--scenario` or `--regions` — **units are scenario- and
region-agnostic** in LEAP COM. The probe sets `ActiveRegion` to the
first available region just so `Variable.DataUnitText` resolves; the
unit string is the same regardless.

### Default INPUT variables (curated, popup-safe)
`Maximum Capacity, Minimum Capacity, Capital Cost, Variable OM Cost,
Fixed OM Cost, Lifetime, Maximum Availability, Minimum Utilization,
Process Efficiency, Exogenous Capacity, Capacity Credit, Interest Rate`

### Defaults — branch types
`{3, 50}` only — **narrower** than Probe A. Reason: BT=2 (Module),
BT=4 (Demand Tech), BT=34 (Effect) expose target variable names ONLY
as result aggregates on those branches. Calling `DataUnitText` on
those fires the popup. Restricting to BT=3 (Transformation Process)
and BT=50 (Transformation Branch) — the only types with reliable
input-side variables — eliminates popups entirely.

### Defensive technique — index-based first-occurrence
LEAP COM iterates variables in a known order: input vars at indexes
1..N_input, result vars at N_input+1..end. Some variable names appear
on **both sides** (e.g. `Maximum Availability` at index #5 = input
80.0%, AND at index #37 = result 0%). Naive `branch.Variable("Maximum
Availability")` may return either variant.

The probe walks variables by INDEX using `branch.Variables.Item(j)` and
takes the **first occurrence** of each target name. Because input vars
come first, first-occurrence guarantees we hit the input variant. Result-
only variable names (Energy Generation etc.) are not in the curated
target list, so they're never touched.

### Output
~830 (branch, variable, unit) rows for AEO9_v0.36 Centralized Elec
Gen — 83 process branches × ~10 vars each. Captured units example:

```
Capacity Credit            Percent
Capital Cost               Thousand U.S. Dollar/Megawatt
Exogenous Capacity         Megawatt
Fixed OM Cost              Thousand U.S. Dollar/Megawatt
Interest Rate              Percent
Lifetime                   Years
Maximum Availability       Percent
Minimum Utilization        Percent
Process Efficiency         Percent
Variable OM Cost           U.S. Dollar/Megawatt-Hour
```

### Pacing
- Probe overhead: ~3 min (same COM init as Probe A).
- Walk: ~1 sec/branch.
- Total for ~80 branches: **~4 min**.

### Multi-area trap
Same as Probe A. The probe inherits whatever area is currently active.
If the area changed between Probe A and Probe B (e.g., the user
clicked around in LEAP UI), Probe B may target the wrong area. The
probe prints `[unitsB] ActiveArea: '<name>'` at start; verify it
matches the area used for Probe A.

---

## Step C — join_results_with_units.py (offline merge)

### Command

```bash
python mailbox/<YYYYMMDD>/join_results_with_units.py \
    --results mailbox/<YYYYMMDD>/results_BAS_centralized.csv \
    --units   mailbox/<YYYYMMDD>/units_centralized.csv \
    --out     mailbox/<YYYYMMDD>/joined_BAS.csv
```

Repeat per scenario (BAS, ATS, etc.); the same units file serves all
scenarios because units are scenario-agnostic.

### Output schema
```
ams, branch, branch_type, variable, year, value, unit, unit_source
```

### `unit_source` values
- **`direct`** — same `(branch, variable)` exists in Probe B output
  (rare; only happens when Probe A and Probe B targeted the same
  variable name, which is the case for variables like `Existing
  Capacity` that exist on both sides).
- **`inferred`** — the variable is a result-side name not present in
  Probe B; unit was resolved via the inference table either by
  companion-variable lookup on the same branch or via a fallback
  literal.
- **`unknown`** — no rule matched; unit column is empty. Triggers a
  warning in the join script's stdout. Fix by extending
  `INFERENCE_TABLE` in the script or passing `--inference KEY=UNIT`.

### Inference table (current)
Curated empirically from AEO9_v0.36 inspection. Each entry maps a
result-variable name to `(write_side_companion_name, fallback_unit)`:

| Result variable | Write-side companion | Fallback unit |
|---|---|---|
| Existing Capacity | Exogenous Capacity | Megawatt |
| Capacity Additions | Exogenous Capacity | Megawatt |
| Capacity Retirement | Exogenous Capacity | Megawatt |
| Capacity Added | Exogenous Capacity | Megawatt |
| Capacity Retired | Exogenous Capacity | Megawatt |
| Power Generation | (none) | Megawatt |
| Energy Generation | (none) | Gigajoule (LEAP area default) |
| Curtailed Energy Production | (none) | Gigajoule |
| Costs of Production | (none) | Thousand U.S. Dollar |
| Investment Costs | Capital Cost | Thousand U.S. Dollar/Megawatt |
| Pollutant Loadings | (none) | Metric Tonne CO2 Equivalent |

### Override at the CLI

```bash
--inference "Energy Generation=PJ,Pollutant Loadings=t SO2"
```

Use this when the area's General Properties default differs from the
curated fallback (e.g., a different LEAP area uses TWh as the energy
default).

### Pacing
~5 sec for 11K rows. Pure offline.

---

## Pitfalls encountered while building this SOP (don't repeat)

1. **First attempt used `Variable.Unit.Name`** — silently returns empty
   for both input and result variables on this LEAP version. Ate ~30
   min of confusion before discovering `Variable.DataUnitText` is the
   real attribute (already documented in
   [`nemo_read/leap_units.py`](../../nemo_read/leap_units.py); future
   probes should `from nemo_read.leap_units import safe_data_unit_text`
   directly rather than rolling their own).

2. **First attempt fired modal popups on every result variable** even
   though `safe_data_unit_text` catches the exception. The exception
   IS the popup — LEAP raises the dialog AND the COM error in the same
   action. The defensive helper catches the error but the popup stays
   on screen until manually dismissed. The fix: never call
   `DataUnitText` on result variables in the first place.

3. **First popup-safe attempt used `branch.Variable(name)`** to fetch
   variables by name, hoping LEAP would return the input variant. It
   doesn't — LEAP can return either variant nondeterministically.
   Fixed by walking with `branch.Variables.Item(j)` and taking
   first-occurrence-only.

4. **Even with first-occurrence, BT=2 (Module) branches fired popups**
   because some target variable names exist ONLY as result aggregates
   on Module branches — there is no input variant to be "first." Fixed
   by restricting Probe B's branch types to `{3, 50}`.

5. **Probe A initially used wrong default variable names** (`Outputs`,
   `Total Capacity`, `Capacity Added`, etc.). LEAP's actual result
   variable names in this area are `Energy Generation`, `Existing
   Capacity`, `Capacity Additions`. First scan returned mostly zeros;
   second scan with corrected names returned real data. Discovery via
   one-shot enumeration on a sample branch (Coal Supercritical) was
   the unlock.

6. **`--years` defaulting to all years (BaseYear..EndYear)** padded
   ~85% of the CSV with zero rows for pre-model years (2005-2024).
   Restrict to the 8 model milestones (2025-2060) explicitly.

7. **`Base Template` region** is a LEAP placeholder that appears in
   `leap.Regions` enumeration but isn't a real ASEAN region. Always
   exclude from `--regions`.

8. **Output buffering with stdout-to-file**: Python prints don't flush
   when stdout is captured by Bash background mode. The probe sets
   `os.environ["PYTHONUNBUFFERED"] = "1"` and
   `sys.stdout.reconfigure(line_buffering=True)` but neither fully
   solves it under Bash redirection. CSV file growth is the more
   reliable progress signal — monitor the CSV row count via
   `wc -l`, not the probe stdout.

9. **Multi-area trap at scenario-switch time** is by far the most
   time-consuming failure mode. Every probe run should be preceded by
   confirming LEAP UI shows the right area + scenario, OR running
   with `--no-scenario-switch` and letting the user set the dropdown
   manually.

---

## File locations

All artifacts land in `mailbox/<YYYYMMDD>/`:

```
mailbox/20260505/
├── aeo9_v0.36.leap                     # the LEAP area file (input, user-supplied)
├── probe_leap_results.py               # Step A
├── probe_leap_units.py                 # Step B
├── join_results_with_units.py          # Step C
├── RESULTS_HARVEST_SOP.md              # this file
├── results_BAS_centralized.csv         # Step A output (BAS)
├── results_ATS_centralized.csv         # Step A output (ATS)
├── units_centralized.csv               # Step B output (one per area)
├── joined_BAS.csv                      # Step C output (BAS)
└── joined_ATS.csv                      # Step C output (ATS)
```

The probe and join scripts in `mailbox/<date>/` are the canonical
templates. Copy + adapt for each new harvest cycle.

---

## When NOT to use this SOP

Use the full [`nemo_read-leap-export`](../../nemo_read/leap_export.py)
CLI (and `LeapAreaContext.discover()`) instead when:

- You need write-side data (input variable values, expressions, formulas)
  in addition to results.
- You need a self-contained area dump that other analysts can use
  without LEAP installed.
- The analysis question goes beyond "what came out of this run."
- You want CSV + JSON + tags + units + branches + nemo.cfg +
  customconstraints in one shot.

This A → B → C pipeline is the **focused, fast** counterpart for
"I just want the result numbers, properly unit-annotated."

---

## End-state of the May 2026 cycle

After running this SOP against `aeo9_v0.36.leap` (Centralized
Electricity Generation, BAS + ATS):

| Artifact | Rows | Size |
|---|---|---|
| `results_BAS_centralized.csv` | 10,328 | 1.55 MB |
| `results_ATS_centralized.csv` | 11,000 | 1.65 MB |
| `units_centralized.csv` | 830 | ~70 KB |
| `joined_BAS.csv` | 10,328 | ~1.7 MB |
| `joined_ATS.csv` | 11,000 | ~1.8 MB |

All `joined_*.csv` rows have a `unit` populated; 100% via the inference
table (no `unknown`). Wall-clock totals: Probe A ~50 min × 2
scenarios + Probe B ~4 min + Step C ~5 sec = **~105 min for the full
cycle**.
