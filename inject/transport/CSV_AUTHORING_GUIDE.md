# Transport CSV — Authoring Guide

Deep technical reference for the transport adapter
([build_canonical.py](build_canonical.py)). The owner-facing spec lives
in [TRANSPORT_CSV_SPEC.md](TRANSPORT_CSV_SPEC.md); start there if
you're the transport team. This guide is for the framework owner
maintaining the adapter and the injector.

---

## 0. Where this fits

The transport pipeline is structured as a **dated source-data drop +
deterministic adapter**, not as a hand-edited canonical (like
bioenergy). The transport team's authoring lives in their tooling; we
receive the four CSVs in `inject/transport/<YYYYMMDD>/` and the
adapter mechanically produces the canonical.

```
inject/transport/
├── 20260519/                       ← latest data drop (read-only inputs)
│   ├── sales_mix.csv
│   ├── sales_magnitude.csv
│   ├── mileage_anchors.csv
│   └── starting_year_sales.csv
├── build_canonical.py              ← this guide
├── canonical_leap_inputs.csv       ← deterministic output
├── inject_to_leap.py               ← thin CanonicalInjector subclass
├── timor_leste_supplement.csv      ← §A.18 stub (TL disabled)
├── TRANSPORT_CSV_SPEC.md           ← author-facing spec
└── CSV_AUTHORING_GUIDE.md          ← this file
```

To roll the next drop forward, create `inject/transport/<NEWDATE>/`
and update `INPUT_DIR` in [build_canonical.py](build_canonical.py) (or
add a CLI flag — see §6 below).

---

## 1. Canonical schema produced

The output `canonical_leap_inputs.csv` has the standard
`CanonicalInjector` schema (matches bioenergy / fossil / power):

```
ams, branch, variable, expression, unit, fuel, source, note,
src_csv, data_confidence, scenario
```

One row per `(ams, branch, variable, scenario)` tuple. The adapter
emits two variable families:

- **`Sales`** — one row per `(ams, vehicle, fuel, scenario)`. The
  `expression` is an `Interp(year, value, ...)` series across all
  Years present in `sales_mix.csv` for that group.
- **`Mileage`** — one row per `(ams, vehicle, fuel)` replicated across
  every LEAP-available fuel under the vehicle. Flat `Interp()` 2025–
  2060 holding the anchor value. Scenario tag is `Current Accounts`
  (mileage is treated as structural input, not scenario-differentiated
  in this cycle).

---

## 2. Adapter behaviour — mappings (encoded as module constants)

All four mappings are module-level dicts in
[build_canonical.py](build_canonical.py) so the rule is auditable, not
in operator's head:

| Constant | Maps |
|---|---|
| `VEHICLE_TYPE_MAP` | source vehicle code → LEAP branch segment |
| `FUEL_TYPE_MAP` | source fuel label → LEAP fuel name |
| `COUNTRY_MAP` | source Country → LEAP region |
| `SCENARIO_MAP` | source scenario tag → LEAP scenario name |

When the source CSV contains a value not in the map, the adapter
prints a `WARN` and drops those rows. No silent acceptance.

### 2.1 Hybrid/Hydrogen collapse

Two source fuels collapse to one LEAP fuel:
- `Hydrogen FCEV` + `HydrogenFCV` → `Hydrogen`
- `Diesel` + `HybridDiesel` → `Blended Diesel`

The collapse happens *after* the mapping and *before* the groupby. The
`Sales` `count` values are summed across collapsed source rows.
**Result:** hybrid-diesel vehicles contribute their full count to
`Blended Diesel`. If the next cycle separates hybrid-diesel into a
dedicated track, both the source schema and the LEAP branch taxonomy
need to change together.

### 2.2 Year-based scenario remap

Any row with `Year <= 2024` has its `leap_scenario` overridden to
`Current Accounts`, regardless of the source `scenario` label. This
is the LEAP convention for the `aeo9_v0.46` version — historical data
lives in CA only.

---

## 3. The LEAP-availability filter (canonical taxonomy is authoritative)

The adapter rejects (vehicle, fuel) combinations that don't exist as
LEAP branches. The map lives in `LEAP_AVAILABLE_FUELS_PER_VEHICLE`
and was derived from the 2026-05-19 Phase 1 mapping run on
`aeo9_v0.46`:

```python
LEAP_AVAILABLE_FUELS_PER_VEHICLE = {
    "Bus": {"Blended Diesel", "Electricity", "Gasoline",
            "Hydrogen", "Natural Gas"},
    "Motorcyle": {"Electricity", "Gasoline"},
    "PassengerCar": {"Blended Diesel", "Electricity", "Gasoline",
                     "Natural Gas"},
    "Truck": {"Blended Diesel", "Electricity", "Gasoline",
              "Hydrogen", "Natural Gas"},
}
```

**Why this lives in the adapter, not as runtime data:** our canonical
LEAP branch taxonomy is the source of truth (see Cross-Domain Learnings
§9). The sector team's source CSV is the *proposal*. When the source
includes a (vehicle, fuel) combination LEAP doesn't model, we filter
toward LEAP and log the dropped signatures. The next probe of a new
LEAP version refreshes this map.

Dropped 2026-05-19: `Motorcyle × Natural Gas`, `PassengerCar × Hydrogen`.

**When LEAP adds a new tech** (e.g. Motorcyle gets a Hydrogen child
in `aeo9_v0.47`): re-run the Phase 1 mapping probe, update the dict
in this file, and re-run the adapter. The filter is a one-line edit;
the burden is the COM probe to verify.

---

## 4. Mileage replication

A single mileage value per `(country, vehicle)` is replicated across
all fuel leaves under that vehicle. The replication set is the
intersection of:

1. The fuels observed in `sales_mix.csv` for that vehicle, and
2. The LEAP-available fuels per `LEAP_AVAILABLE_FUELS_PER_VEHICLE`.

Intersection (not union) — same reasoning as §3. Mileage rows for
fuels LEAP doesn't model never get emitted.

The mileage `expression` is a flat `Interp(2025, V, 2030, V, ..., 2060, V)`
holding the anchor value through the projection horizon. If the
authoring team gives us a projection (vehicle-electric mileage rises
because EVs are operated longer; diesel mileage falls because fleets
turn over), this is the place to author the trajectory — but currently
the source `mileage_anchors.csv` has no Year axis, so flat is what
falls out.

---

## 4b. Open data-shape issue: `BaseYear_StockData` (confirmed 2026-05-19)

The 2026-05-19 inject committed all 601 rows cleanly via COM, but
the post-inject readback caught a **semantic mismatch on
`BaseYear_StockData`**:

| | Brunei Bus | Cambodia Bus | Indonesia Bus | … |
|---|---|---|---|---|
| Expected (we wrote)   | `Interp(2024, 61)`   | `Interp(2024, 2405)`  | `Interp(2024, 9087)`   | … |
| Actual (LEAP held)    | `2300`               | `69600`               | `273800`               | … |

The actuals are 30-100× larger and are bare numbers (not `Interp()`
expressions), consistent with `BaseYear_StockData` storing the
**2024 fleet stock** — the number of vehicles on the road in the
year before the first modelling year — rather than annual sales.

**Current adapter behaviour** (`_build_baseyear_stock_rows`):
sums `starting_year_sales.csv:sales_count` across fuels per
`(ams, vehicle)`. This produces the **annual sales** total, not
the **fleet stock**. Structurally correct, numerically too small.

**Fix path:**
1. Source team adds a `stock_count` column to `starting_year_sales.csv`
   (or ships a separate `baseyear_stock.csv`) with the actual fleet
   stock at year-end 2024, per `(Country, vehicle_type)`.
2. Adapter's `_build_baseyear_stock_rows` swaps from summing
   `sales_count` to reading `stock_count` directly.
3. Re-run the inject for `BaseYear_StockData` rows only (single-row-
   family filter in the next cycle).

Until that drop arrives, the BaseYear_StockData branches in LEAP
have either:
  - Vietnam: our (wrong) sales-sum value (it didn't have prior data
    that survived our overwrite)
  - All other AMS: the pre-existing fleet stock values (our writes
    didn't replace what was already there — Brunei still shows 2300,
    Cambodia 69600, etc.)

For the OTHER three branch families (`Vehicle_Sales`,
`Vehicles_Sales_Share`, `Mileage`), all 9 readback samples passed —
those semantics are correct.

---

## 4c. MANDATORY: CA-2024 → forward-2025 continuity check (added 2026-05-20)

For every time-series share variable, the **last historical year in
Current Accounts (2024)** must connect smoothly to the **first
projection year (2025)** in each forward scenario (Baseline / AMS
Target / Regional Aspiration). A share that reads (say) 70% in CA-2024
must not jump to 100% in 2025 — there is no physical event in a single
year to justify that.

**Why this is an author responsibility, not an inject responsibility.**
The inject framework writes exactly what the canonical says, byte-exact
(verified by readback). A 2024→2025 discontinuity is therefore always
a *data-authoring* defect that the inject faithfully reproduces. It will
not be caught by the readback (which only checks write fidelity) — it
must be caught here, at authoring time.

**The 2026-05-20 incident.** The first full transport inject surfaced
**13 (AMS, vehicle\fuel) combinations** where the dominant fuel's share
jumped upward at 2024→2025 — worst cases Myanmar/Vietnam Bus & Truck
Blended Diesel at ~+30 points. Root-cause hypothesis: the forward
`sales_mix.csv` was renormalised to 100% across a *narrower* fuel set
than CA history carried (minor historical fuels like LPG/CNG dropped
out of the forward set, so the dominant fuel absorbed their share — but
only from 2025 on, producing the step).

Interim fix applied to the LEAP area: the 39 forward rows (13 combos ×
3 scenarios) were re-expressed as **`Remainder(100)`** so the dominant
fuel becomes the residual of 100% after the other modelled shares,
self-consistently tracking them with no hard-coded jump. CA historical
rows were left untouched. See
`author_handover_20260520/README_TRANSPORT_AUTHOR_FIXES.md` and the
full mismatch CSV for the reference list.

**Author action required each cycle:**
1. Run the continuity checker after `build_canonical.py`:
   `python inject/transport/_check_ca_to_fwd_continuity.py`
   (flags any CA-2024 vs forward-2025 jump > 1% relative).
2. For each flagged combo, decide:
   - the dominant fuel should be `Remainder(100)` (residual modelling), OR
   - `sales_mix.csv` should be re-authored so the 2025 starting share
     equals the CA-2024 share and diverges smoothly from there.
3. Re-check until the script reports `CLEAN: no discontinuities found`.

**This check is now in the §10 validation checklist — do not skip it.**

---

## 5. Interp() expression form (§A.15 compliance)

Every `Interp(...)` produced by this adapter uses **comma list-sep,
period decimal**:

```
Interp(2025, 100.5, 2030, 120.0, 2035, 135.3)
```

Built via `_interp_from_pairs()` and defensively normalised at write
time via `normalize_interp()` from `nemo_read._leap_com`. The
[tests/test_interp_separator.py](../../tests/test_interp_separator.py)
CI tripwire scans every committed canonical CSV — if the wrong form
ever lands in transport's canonical, that test fails.

---

## 6. Running the adapter

```bash
python inject/transport/build_canonical.py
```

No CLI flags currently. The input directory is hardcoded to
`inject/transport/20260519/` at module load. When you roll a new
drop, edit `INPUT_DIR = HERE / "20260519"` near the top of
[build_canonical.py](build_canonical.py).

The adapter prints:
1. The 4 source-CSV row counts.
2. `WARN` lines for any unmapped Country / vehicle_type / fuel_type /
   scenario values.
3. The observed fuels per vehicle (from sales_mix).
4. `WARN sales: dropped N rows for (vehicle, fuel) combinations not
   in LEAP taxonomy:` — followed by the specific combos.
5. Output row count + per-variable / per-scenario / per-AMS breakdown.

A typical run on the 2026-05-19 drop:
```
[transport adapter] reading from inject/transport/20260519/
  sales_mix rows after mapping+collapse: 10144
  mileage rows: 40
    Bus: fuels = ['Blended Diesel', 'Electricity', 'Gasoline', 'Hydrogen', 'Natural Gas']
    Motorcyle: fuels = ['Electricity', 'Gasoline', 'Natural Gas']
    PassengerCar: fuels = ['Blended Diesel', 'Electricity', 'Gasoline', 'Hydrogen', 'Natural Gas']
    Truck: fuels = ['Blended Diesel', 'Electricity', 'Gasoline', 'Hydrogen', 'Natural Gas']
  WARN sales: dropped 40 rows for (vehicle, fuel) combinations not in LEAP taxonomy:
    Motorcyle x Natural Gas
    PassengerCar x Hydrogen
[transport adapter] wrote canonical_leap_inputs.csv  (520 rows)
  Rows per variable: {'Sales': 360, 'Mileage': 160}
  Rows per scenario: {'AMS Target Scenario': 80, 'Baseline Simulation': 79,
                      'Current Accounts': 264, 'Regional Aspiration Scenario': 97}
  Rows per AMS: {Brunei: 52, Cambodia: 53, Indonesia: 53, Laos: 49,
                 Malaysia: 56, Myanmar: 51, Philippines: 51, Singapore: 52,
                 Thailand: 55, Vietnam: 48}
```

---

## 7. Injection (the `inject_to_leap.py` subclass)

`TransportInjector` is a minimal `CanonicalInjector` subclass — see
[inject_to_leap.py](inject_to_leap.py). All the LEAP-side rules
(Interp separator §A.15, area/scenario lock §11.1, `safe_set_expression`
chokepoint, placeholder gate, Timor Leste decision §A.18) come from
the framework. The subclass owns only:
- `SECTOR_NAME = "transport"`
- `DEFAULT_CSV = ...`
- `EXPECT_AREA = "aeo9_v0.46"`

Push command:
```bash
python inject/transport/inject_to_leap.py \
    --dry-run-only \
    --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario,Current Accounts" \
    --expect-area "aeo9_v0.46" \
    --exclude-timor-leste
```

The `--exclude-timor-leste` flag is required by §A.18 (the framework
asserts the operator made an explicit decision either way). Currently
TL is disabled in LEAP calc (operational state 2026-05-18), so this is
the correct flag.

---

## 8. Timor Leste supplement (§A.18 stub)

[timor_leste_supplement.csv](timor_leste_supplement.csv) exists with
just the header row. When TL is re-enabled in LEAP calc, populate this
file with TL-specific rows (TL has different sales mix + mileage
patterns from the rest of ASEAN that may not be in the main
`sales_mix.csv`). The injector framework reads it when called with
`--include-timor-leste`.

The source `sales_mix.csv` does not contain TL rows in any case
(the transport team's source data is restricted to the 10 ASEAN
members where transport-pipeline data is available).

---

## 9. Cross-Domain Learnings

- **2026-05-19 — from this domain: canonical LEAP branch taxonomy is
  authoritative; correct sector teams against it, not the other way
  around.** When a source CSV has (key1, key2, ...) combinations the
  LEAP area doesn't model, the adapter filters and logs the dropped
  signatures. Our COM-probed branch map is truth.
  This domain: applied via `LEAP_AVAILABLE_FUELS_PER_VEHICLE` filter.
  Other domains should: derive an analogous availability map from a
  Phase-1 mapping probe of the target area and filter early in
  `build_canonical.py`. Especially load-bearing for any domain where
  the source team operates a generic enumeration of options that may
  exceed what LEAP actually models. See
  `memory/feedback_canonical_taxonomy_authority.md`.

- **2026-04-29 — from bioenergy: supply cap and per-unit cost row on
  the same branch must share the same physical basis.** Bioenergy
  uses raw-crop tonnes (FFB / cane / fresh root / grain / nuts-in-shell)
  for both `Maximum Production` and `Production Cost` on
  `Resources\Primary\<Crop>`.
  This domain: confirmed not applicable. Transport authors `Sales`
  (vehicle count, no per-unit cost row in this cycle) and `Mileage`
  (km/vehicle/year, no per-unit cost row). When per-unit cost rows
  enter the transport authoring scope (e.g. fuel cost per km), they'll
  need basis-aligned with the activity they cost.
  See `inject/bioenergy/CSV_AUTHORING_GUIDE.md §12.5`.

- **2026-05-19 — from bioenergy: every supply cap needs a companion
  cost row authored in the same canonical, else the LP routes via the
  unauthored cost ≈ 0 region.** (POME Import Cost was the bioenergy
  final unlock 2026-05-19.)
  This domain: not yet applicable. Transport currently authors
  activity-side (`Sales`, `Mileage`) not supply-side caps/costs.
  Will become applicable if/when transport authors process costs
  (Capital Cost, Variable OM Cost) for vehicle techs.
  See `memory/project_bioenergy_resolved_pome_import_cost.md`.

- **2026-05-17 — from fossil: §A.15 Interp() separator (comma
  list-sep + period decimal) is enforced via 3-layer defense.**
  This domain: applied via `normalize_interp()` calls at row
  construction time and at write time. `tests/test_interp_separator.py`
  scans the committed canonical CSV.

---

## 10. Validation checklist

Before declaring a transport push successful (CLAUDE.md §4.1):

- [ ] `python inject/transport/build_canonical.py` ran clean
- [ ] No `WARN` for unmapped categorical values that the team
      intended to be present (a known drop like
      `Motorcyle × Natural Gas` is fine; an unknown vehicle_type code
      is not)
- [ ] LEAP-availability filter WARN lines match what the team expects
- [ ] `python -m pytest tests/test_interp_separator.py` clean
- [ ] `python -m pytest tests/test_inject_base.py` clean (validates
      TransportInjector subclass shape)
- [ ] Dry-run inject completes without `[FAIL]` lines
- [ ] Read-back-one verify on one representative `(ams, vehicle, fuel,
      scenario)` row after real push
- [ ] **CA-2024 → forward-2025 continuity (§4c)** —
      `python inject/transport/_check_ca_to_fwd_continuity.py` reports
      `CLEAN`, OR every flagged jump has been author-confirmed as
      intended (e.g. resolved via `Remainder(100)`)
- [ ] No placeholder rows in the canonical (transport doesn't author
      Stage-5 placeholders — they belong to infeasibility triage, not
      data authoring)
