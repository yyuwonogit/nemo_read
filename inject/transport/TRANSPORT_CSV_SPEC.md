# Transport CSV — Author Spec (dated 2026-05-19)

Operational truth for the four hand-authored CSVs the transport team
drops into `inject/transport/<YYYYMMDD>/`. The adapter at
[build_canonical.py](build_canonical.py) consumes these and produces
`canonical_leap_inputs.csv` for the standard `CanonicalInjector` push.

If you find yourself doing something that contradicts this file, **stop
and ask** — don't infer scope from absence.

For the deep technical reference (mapping logic, canonical schema,
filter rules, audit history), see
[CSV_AUTHORING_GUIDE.md](CSV_AUTHORING_GUIDE.md).

---

## Quick reference card

| | Value |
|---|---|
| Folder you drop data into | `inject/transport/<YYYYMMDD>/` |
| Files expected | `sales_mix.csv`, `sales_magnitude.csv`, `mileage_anchors.csv`, `starting_year_sales.csv` |
| LEAP target area | `aeo9_v0.46` |
| LEAP target branches | `Demand\Transport\Road\<Vehicle>\<Fuel>\<Fuel>` |
| Variables injected | `Sales`, `Mileage` |
| Scenarios injected | `Baseline Simulation`, `AMS Target Scenario`, `Regional Aspiration Scenario`, `Current Accounts` (historical) |
| Validation command | `python inject/transport/build_canonical.py` |
| Push command (dry-run) | `python inject/transport/inject_to_leap.py --dry-run-only --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario,Current Accounts" --expect-area "aeo9_v0.46" --exclude-timor-leste` |

---

## 1. The authoring cycle

```
1. RECEIVE   this spec + the LEAP area version (currently aeo9_v0.46)
2. AUTHOR    the four CSVs under inject/transport/<YYYYMMDD>/
3. VALIDATE  run python inject/transport/build_canonical.py
4. CHECK     no WARN about unmapped Country / vehicle_type / fuel_type;
             review the LEAP-availability filter WARN log
5. SEND BACK 1-line summary of what changed in this cycle
```

Structure note: we (the framework owners) own the LEAP branch taxonomy.
If your source CSV lists a (vehicle, fuel) combination LEAP doesn't
model, **our adapter will silently drop those rows + log them**. The
canonical LEAP branch map is in [build_canonical.py](build_canonical.py)
as `LEAP_AVAILABLE_FUELS_PER_VEHICLE`. Combinations dropped 2026-05-19:
`Motorcyle × Natural Gas`, `PassengerCar × Hydrogen`.

---

## 2. The four CSVs — schemas

### 2.1 `sales_mix.csv` — primary sales fan-out (Country × Year × VehicleType × FuelType × scenario)

| Column | Required | Notes |
|---|---|---|
| `Country` | ✅ | Source name; mapped to LEAP region (§3.1) |
| `ISO3` | ✅ | Informational; not consumed |
| `Year` | ✅ | Integer; spans historical + projection |
| `vehicle_type` | ✅ | One of `2W`, `Bus`, `LDV`, `Truck` (§3.2) |
| `fuel_type` | ✅ | One of `Electric`, `Gasoline`, `NaturalGas`, `Hydrogen`, `Hydrogen FCEV`, `HydrogenFCV`, `Diesel`, `HybridDiesel` (§3.3) |
| `scenario` | ✅ | One of `BAS`, `ATS`, `RAS`, `historical` (§3.4) |
| `count` | ✅ | Vehicle sales count for this row (integer) |
| `year_total` | optional | Informational; not consumed |
| `share_percent` | optional | Informational; not consumed |

### 2.2 `sales_magnitude.csv` — Country × Year × VehicleType totals

| Column | Required | Notes |
|---|---|---|
| `Country` | ✅ | Source name; mapped to LEAP region |
| `ISO3` | ✅ | Informational |
| `Year` | ✅ | Integer |
| `vehicle_type` | ✅ | One of `2W`, `Bus`, `LDV`, `Truck` |
| `sales_count` | ✅ | Total vehicles of this type sold in this country-year |
| `source_method` | optional | Free text (provenance) |

**Currently the adapter consumes `sales_mix.csv` for the actual Sales
injection** (since it already has the (vehicle, fuel, scenario) split).
`sales_magnitude.csv` is kept as a cross-check artifact.

### 2.3 `mileage_anchors.csv` — Country × VehicleType annual mileage

| Column | Required | Notes |
|---|---|---|
| `Country` | ✅ | Source name; mapped to LEAP region |
| `vehicle_type` | ✅ | One of `2W`, `Bus`, `LDV`, `Truck` |
| `mileage_km_per_year` | ✅ | Float; km/vehicle/year |
| `confidence` | ✅ | `high` / `medium` / `low` |
| `observed_year` | optional | Anchor year |
| `source` | ✅ | Free text (provenance) — written into canonical `source` column |
| `source_url` | optional | URL |
| `leap_default_km_per_year` | optional | What LEAP currently has; informational |

One mileage value applies vehicle-wide — the adapter replicates it
across all fuel leaves of that vehicle in LEAP (intersected with the
LEAP-availability map).

### 2.4 `starting_year_sales.csv` — 2024 baseline anchors

| Column | Required | Notes |
|---|---|---|
| `Country` | ✅ | Source name |
| `ISO3` | ✅ | Informational |
| `vehicle_type` | ✅ | One of `2W`, `Bus`, `LDV`, `Truck` |
| `fuel_type` | ✅ | Source-side label (see §3.3) |
| `Year` | ✅ | Typically 2024 |
| `sales_count` | ✅ | Integer — but see ⚠️ DATA-SHAPE FIX NEEDED below |
| `sales_total_year` | optional | Informational |
| `share_percent` | optional | Informational |
| `provenance_note` | ✅ | Free text |

Used by the adapter for historical anchors that feed `Current Accounts`
(pre-2025). The actual injection uses `sales_mix.csv` rows where
`Year <= 2024`; `starting_year_sales.csv` is the audit-trail companion.

> **⚠️ DATA-SHAPE FIX NEEDED — confirmed 2026-05-19**
>
> `BaseYear_StockData` on LEAP's `Key\TransportDataStock\…` tree
> wants the **fleet stock at the year before the first modelling
> year** (i.e. 2024 vehicles on the road), **NOT the count of vehicles
> sold in 2024.** The 2026-05-19 inject committed sales counts by
> mistake — values came out 30-100× too small (e.g. Brunei Bus
> readback expected `61` from our sales sum, LEAP had `2300` for the
> actual stock).
>
> **Next data drop should add a `stock_count` column** (or a separate
> `baseyear_stock.csv` file) giving the 2024 fleet stock per
> `(Country, vehicle_type)` — aggregated across fuels since the LEAP
> branch is per-vehicle, no fuel sub-tree. Either:
>
> ```
> Country, vehicle_type, Year, stock_count, source
> Brunei Darussalam, Bus, 2024, 2300, <source>
> ```
>
> When that drop lands, the adapter's `_build_baseyear_stock_rows`
> will read the new column instead of summing `sales_count`.

---

## 3. Name mappings (encoded in the adapter — don't author against LEAP names directly)

### 3.1 Country → LEAP region

| Source `Country` | LEAP region |
|---|---|
| Brunei Darussalam | Brunei |
| Cambodia | Cambodia |
| Indonesia | Indonesia |
| Lao PDR | Laos |
| Malaysia | Malaysia |
| Myanmar | Myanmar |
| Philippines | Philippines |
| Singapore | Singapore |
| Thailand | Thailand |
| Viet Nam | Vietnam |

Timor Leste is intentionally absent from the source data (TL is
disabled in LEAP calc per operational state 2026-05-18).

### 3.2 `vehicle_type` → LEAP branch segment

| Source | LEAP | Notes |
|---|---|---|
| `2W` | `Motorcyle` | LEAP's typo, preserved verbatim |
| `Bus` | `Bus` | |
| `LDV` | `PassengerCar` | |
| `Truck` | `Truck` | |

### 3.3 `fuel_type` → LEAP fuel name (Hybrid/Hydrogen collapse)

| Source | LEAP | Notes |
|---|---|---|
| `Electric` | `Electricity` | |
| `Gasoline` | `Gasoline` | |
| `NaturalGas` | `Natural Gas` | |
| `Hydrogen` | `Hydrogen` | |
| `Hydrogen FCEV` | `Hydrogen` | collapsed |
| `HydrogenFCV` | `Hydrogen` | collapsed |
| `Diesel` | `Blended Diesel` | |
| `HybridDiesel` | `Blended Diesel` | collapsed — hybrid diesel routes to the Blended Diesel branch |

When two source fuels collapse to one LEAP fuel (`Hydrogen` ← Hydrogen
FCEV + HydrogenFCV, `Blended Diesel` ← Diesel + HybridDiesel), the
adapter **sums** the counts.

### 3.4 `scenario` → LEAP scenario name

| Source | LEAP scenario |
|---|---|
| `BAS` | Baseline Simulation |
| `ATS` | AMS Target Scenario |
| `RAS` | Regional Aspiration Scenario |
| `historical` | Current Accounts |

**Year-based scenario remap:** any row with `Year <= 2024` is forced
to `Current Accounts` regardless of its source `scenario` label —
historical data lives only in CA on this LEAP version.

---

## 4. LEAP-availability filter (we own the taxonomy)

The adapter rejects (vehicle, fuel) combinations that don't exist as
LEAP branches in `aeo9_v0.46`. The canonical map:

| Vehicle | Available fuels (LEAP) |
|---|---|
| Bus | Blended Diesel, Electricity, Gasoline, Hydrogen, Natural Gas |
| Motorcyle | Electricity, Gasoline |
| PassengerCar | Blended Diesel, Electricity, Gasoline, Natural Gas |
| Truck | Blended Diesel, Electricity, Gasoline, Hydrogen, Natural Gas |

Rows dropped 2026-05-19: `Motorcyle × Natural Gas`,
`PassengerCar × Hydrogen`. If your source data needs these
combinations, they belong as LEAP-side authoring requests to extend
the branch taxonomy — not as silent additions to source CSVs.

---

## 5. What the adapter produces

[canonical_leap_inputs.csv](canonical_leap_inputs.csv) — 520 rows as of
2026-05-19, in the standard `CanonicalInjector` schema:

| Column | Source |
|---|---|
| `ams` | mapped Country |
| `branch` | `Demand\Transport\Road\<Vehicle>\<Fuel>\<Fuel>` |
| `variable` | `Sales` or `Mileage` |
| `expression` | `Interp(year, value, ...)` — comma list-sep, period decimal (§A.15) |
| `unit` | `""` for Sales (LEAP-native gate resolves); `Kilometer` for Mileage |
| `fuel` | LEAP fuel name |
| `source` | provenance |
| `note` | per-row note (scenario, confidence) |
| `src_csv` | `sales_mix.csv` or `mileage_anchors.csv` |
| `data_confidence` | per-row |
| `scenario` | LEAP scenario name |

Row counts by variable / scenario / AMS are printed at the end of
`build_canonical.py` for cycle audit.

---

## 6. Don't undo prior decisions

| Decision | Rationale |
|---|---|
| `2W` → `Motorcyle` (typo) | LEAP authors named it that way; we mirror exactly |
| `HybridDiesel` → `Blended Diesel` | We have no separate hybrid track in LEAP; the diesel fraction routes to the blended diesel branch |
| Year ≤ 2024 → Current Accounts | Historical data lives in CA only on `aeo9_v0.46` |
| Timor Leste absent | Operational state 2026-05-18; revisit when TL is re-enabled |
| LEAP-availability filter | Canonical taxonomy authority — we correct toward LEAP, not toward the source CSV |
