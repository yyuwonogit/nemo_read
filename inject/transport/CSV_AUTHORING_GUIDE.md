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

## Canon LEAP structure (aeo9_v0.67 exports, 2026-07-02)

The user-declared CANON for this domain's branch paths, variable
names, units, and scenario/region rosters is the "Export Expressions"
workbook set under `LEAP structure/`, digested in
[LEAP structure/LEAP_STRUCTURE_ANATOMY.md](../../LEAP%20structure/LEAP_STRUCTURE_ANATOMY.md)
(transport: §9; Key tree: §12; hygiene ledger: §14), with full branch
trees in `LEAP structure/trees/transport_tree.txt` +
`LEAP structure/trees/keys_tree.txt` and full-path domain slices
(branch × variable × units CSVs + the Key-tree transport slice) in
[structure_handover_20260703/](structure_handover_20260703/).
**Structure comes FROM canon** — refresh the availability map and
branch targets by grepping the trees/slices, not by COM probe and not
by trusting team CSVs or older guide text when they disagree.
Expression *values* are not canon — only structure.

### Domain digest

Tree split (anatomy §9.1) — the sector is methodologically two models:

| Subsector | Branches | Methodology |
|---|---|---|
| Domestic Air | 30 | intensity-per-GDP chain |
| Inland Waterways | 69 | intensity-per-GDP chain |
| Rail | 28 | intensity-per-GDP chain |
| Road | 37 | **vehicle stock-turnover** — this adapter's target |

Road runs depth-4 vehicle classes (Bus, `Motorcyle` [sic],
PassengerCar, Truck) → depth-5 fuel/powertrain branches carrying
`Stock` / `Sales` / `Scrappage` / `First Sales Year` → depth-6
same-named device leaves carrying `Fuel Economy` / `Mileage` /
`Device Share` etc.

**Two-tree naming matrix** (the load-bearing gotcha for this adapter —
the Demand tree and the Key tree disagree):

| | `Demand\Transport\Road` (Mileage + device vars) | `Key\TransportDataStock` (shares/sales/stock) |
|---|---|---|
| Motorcycle class name | `Motorcyle` [sic] | `Motorcycle` (correct) — except `Effective Operational_Stock\Motorcyle`, which carries the typo |
| Gasoline powertrain name | `Blended Gasoline` (there is NO plain `Gasoline` child under any Road vehicle) | `Gasoline` |
| PassengerCar × Hydrogen | absent | present (`Vehicle_Stock_Share` and `Vehicles_Sales_Share` both carry `PassengerCar\Hydrogen`) |

Demand Road fuel roster (16 depth-5 branches, anatomy §9.1): Bus and
Truck = {Blended Diesel, Blended Gasoline, Electricity, Hydrogen,
Natural Gas}; PassengerCar = same minus Hydrogen; Motorcyle =
{Blended Gasoline, Electricity}.

Canon facts the adapter/authors must respect:

- **CA-only variables** (anatomy §2.1): `Stock` (192 rows),
  `First Sales Year` (192), `Share_FossilFuels` (48) exist ONLY under
  Current Accounts. Don't author them into forward scenarios.
- **Units** (transport_rows.csv): `Sales` = `Vehicle`, `Mileage` =
  `Kilometer`, `Fuel Economy` = `MPG Gasoline US eq.` for ALL
  powertrains **including EV and H2** (anatomy §9.2); policy scenarios
  apply `Growth(Key\Annual EI Reduction\FuelEco…)` on top.
- **Stock authoring** (anatomy §9.2): `Data(…)` historical
  registration series for most regions; the Key-formula form
  `Vehicle_Stock_Share × BaseYear_StockData` for Base Template /
  Timor Leste (+ scattered single branches elsewhere).
- **Scenario blocs** (anatomy §2 / §9.4): {RAS ≡ LCO backup ≡ Set up ≡
  RE LTRM ×3}, {Baseline ≡ RAS test}; AMS Target sits 4 rows off RAS
  (SAF fuel-share edits); CNZ sits 130 rows off RAS.
- **Hygiene flags** (anatomy §14): Road has **zero** pollutant effect
  leaves while Air/IW/Rail carry 12–13 species each (#11);
  Truck Natural Gas `Fuel Economy` reads CA=12 vs 5 in all 10
  projection scenarios — Indonesia only, likely authoring slip (#15);
  `Demand\Transport_` (underscore) self-references appear in 180
  `TotShare_AltFuels`/`Share_FossilFuels` rows (#13).

### Key\ / Resources\ structures this domain connects to

The team's sales/stock data lands in **`Key\TransportDataStock`**
(47 branches, anatomy §12.1) — a KA tree, so **blind-mode inject is
mandatory** (§A.20; the Demand-tree Mileage targets are equally
blind-mandatory):

| Subtree | Branches | Holds |
|---|---|---|
| `Vehicle_Stock_Share` | 17 | stock share % per vehicle × fuel |
| `Vehicles_Sales_Share` | 17 | sales share % per vehicle × fuel (adapter target) |
| `Vehicle_Sales` | 4 | total sales per vehicle (adapter target) |
| `BaseYear_StockData` | 4 | 2024 fleet stock per vehicle (adapter target, §4b) |
| `Effective Operational_Stock` | 4 | note the `Motorcyle` typo here |
| `Year_` | 1 | `Year_\Age` |

Adjacent transport Key trees (anatomy §12.1): `Key\Transport vehicle
data_` (28 — a/b/c regression-coefficient + `Historical
Bus/Freight/Motorcycle/PPV/Taxi` panels); `Key\Other Transport` (23 —
EV charging-infrastructure cost stack for AC Level 1 / AC Level 2 /
DC Fast Charger); `Key\Net Zero Measures\Transport` (12 — the CNZ
overlay); `Key\Cal\Transport` (10 — invisible to the demand exports,
consumed elsewhere).

`Resources\`: transport authors **nothing** there. The connection to
fuel supply (Blended Gasoline / Blended Diesel feedstocks, blend
mandates) runs through Transformation and the §A.12 trade-route fuel
list, which is not visible in the demand exports (inference).

---

## 1. Canonical schema produced

The output `canonical_leap_inputs.csv` has the standard
`CanonicalInjector` schema (matches bioenergy / fossil / power):

```
ams, branch, variable, expression, unit, fuel, source, note,
src_csv, data_confidence, scenario
```

One row per `(ams, branch, variable, scenario)` tuple. The adapter
emits four row families (canon-corrected 2026-07-03 — the sales-side
rows land on `Key\TransportDataStock\…` as **`Activity Level`**, the
only assumption variable on Key branches per anatomy §12.2; the
demand-tree `Sales` variable holds LEAP-side formulas wired to these
Key branches — `Vehicles_Sales_Share × Vehicle_Sales`, anatomy §9.3 —
and is not written by this adapter):

- **`Vehicles_Sales_Share`** — `Activity Level` on
  `Key\TransportDataStock\Vehicles_Sales_Share\<Vehicle>\<Fuel>`, one
  row per `(ams, vehicle, fuel, scenario)`. The `expression` is an
  `Interp(year, value, ...)` series across all Years present in
  `sales_mix.csv` for that group.
- **`Vehicle_Sales`** — `Activity Level` on
  `Key\TransportDataStock\Vehicle_Sales\<Vehicle>`, per-vehicle totals.
- **`BaseYear_StockData`** — `Activity Level` on
  `Key\TransportDataStock\BaseYear_StockData\<Vehicle>` (see §4b).
- **`Mileage`** — on the `Demand\Transport\Road\<Vehicle>\<Fuel>\<Fuel>`
  device leaves, one row per `(ams, vehicle, fuel)` replicated across
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
toward LEAP and log the dropped signatures. Refreshing this map no
longer needs a COM probe (canon-corrected 2026-07-03): grep
`LEAP structure/trees/transport_tree.txt` (Demand tree) and
[structure_handover_20260703/keys_slice_transport.txt](structure_handover_20260703/keys_slice_transport.txt)
(Key tree — `keys_tree.txt` lists only variable-carrying branches
without container names, so `TransportDataStock` is not greppable
there) and read the fuel children directly.

Dropped 2026-05-19: `Motorcyle × Natural Gas`, `PassengerCar × Hydrogen`.

> **Canon correction 2026-07-03** (from the `aeo9_v0.67_w_results`
> structure export, `LEAP structure/trees/transport_tree.txt`): the
> Demand-tree Road fuel branches are named `Blended Gasoline`, not
> `Gasoline`. Canon fuel children — Bus/Truck `{Blended Diesel,
> Blended Gasoline, Electricity, Hydrogen, Natural Gas}`, PassengerCar
> `{Blended Diesel, Blended Gasoline, Electricity, Natural Gas}`,
> Motorcyle `{Blended Gasoline, Electricity}`. The dict above (and
> [build_canonical.py](build_canonical.py)) still carries the
> v0.46-era `"Gasoline"` — update it before the next Demand-tree
> Sales/Mileage push, or blind-mode writes to
> `Road\<Vehicle>\Gasoline\…` will target a FullName that no longer
> exists. **RETRACTED 2026-07-23 (v0.80 Keys export).** An earlier edit today
> claimed the rename applied to **both** trees. It does not. The v0.80 Keys
> export (`LEAP structure/LEAP Input Keys.xlsx`, 2026-07-23) shows all 10 Key
> gasoline nodes are bare `Gasoline` —
> `Key\TransportDataStock\{Vehicle_Stock_Share,Vehicles_Sales_Share}\{Bus,
> Motorcycle,PassengerCar,Truck}\Gasoline` plus `Key\Cal\{Transport,Industry}\
> Gasoline` — and **zero** `Blended Gasoline` nodes exist anywhere under `Key\`.
> The v0.80 Transport `Sales`/`Stock` expressions cite `Key\…\Gasoline` and the
> area calculates fine, which is the proof the split is intentional. **The
> matrix at §0 is correct: Demand = `Blended Gasoline`, Key = `Gasoline`; do not
> harmonise them.** An inject row targeting `Key\…\Blended Gasoline` is a defect
> — blind mode HANGS on it rather than erroring (§11.1, §A.20).
>
> Root cause of the bad edit: canon was patched from a *verbal description* of a
> rename before the export existed, which made 160 broken payload rows validate
> (see [20260723/GASOLINE_BRANCH_FIX_NOTES_20260723.md](20260723/GASOLINE_BRANCH_FIX_NOTES_20260723.md)).
> The "a file the user hands over is canon" freshness rule applies to **files**,
> not to descriptions of files.
>
> Adapter status 2026-07-23: [build_canonical.py](build_canonical.py) now
> encodes the split as `FUEL_TYPE_MAP_KA` (bare `Gasoline`, consumed by the
> Key-side sales-share family) and `FUEL_TYPE_MAP_DEMAND` (`Blended Gasoline`),
> with `KA_SALES_SHARE_FUELS_PER_VEHICLE` switched to bare `Gasoline` to match.
> `DEMAND_AVAILABLE_FUELS_PER_VEHICLE` keeps `Blended Gasoline` — correct as-is.

**When LEAP adds a new tech** (e.g. Motorcyle gets a Hydrogen child
in a future area version): re-check the canon trees (or request a
fresh Export Expressions drop if canon predates the area version),
update the dict in this file, and re-run the adapter. The filter is a
one-line edit; verification is a grep of the canon trees, not a COM
probe (canon-corrected 2026-07-03).

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

Canon-corrected 2026-07-03: this is no longer a hypothesis. The
aeo9_v0.67 canon (anatomy §9.2) shows the demand-tree `Stock`
Key-formula form is `Vehicle_Stock_Share × BaseYear_StockData` —
a percentage share times this branch. That only yields a fleet if
`BaseYear_StockData` holds the **total fleet stock**, settling the
semantics.

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
- `EXPECT_AREA = "aeo9_v0.46"` — stale (canon-corrected 2026-07-03):
  the current area is `aeo9_v0.67_w_results`, the version the canon
  structure exports were taken from. Update `EXPECT_AREA` (here and in
  [inject_to_leap.py](inject_to_leap.py)) and re-confirm with the user
  (§A.9) before the next push.

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

- **2026-07-03 — from canon (`LEAP structure/`, aeo9_v0.67 exports):
  the Export Expressions workbooks are the top of the truth hierarchy —
  branch paths, variables, units, and scenario/region rosters come from
  canon, not from COM probes, team CSVs, or older guide text.**
  This domain: applied — the availability-map refresh procedure now
  greps the canon trees instead of re-running the Phase 1 COM probe;
  the Demand-vs-Key naming split (`Blended Gasoline`/`Motorcyle` [sic]
  in `Demand\Transport\Road` vs `Gasoline`/`Motorcycle` in
  `Key\TransportDataStock`), the CA-only variable roster (`Stock`,
  `First Sales Year`, `Share_FossilFuels`), the `MPG Gasoline US eq.`
  Fuel Economy unit, and the `BaseYear_StockData` fleet-stock semantics
  were all settled from canon (see "Canon LEAP structure" section
  above). See `LEAP structure/LEAP_STRUCTURE_ANATOMY.md` §9 + §12.

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
