# AEO-9 v0.71 — full model results (all teams' view)

Complete tidy result set for the `aeo9_v0.71` run, for context alongside your
sector package. One row per data point; every row carries its unit.

Scenarios: AMS Target (ATS), Baseline (BAS), Regional Aspiration (RAS).
Regions: 10 ASEAN member states (Timor Leste excluded from the run).
Years: 2010, 2020, 2030, 2040, 2050, 2060.

## Files

| File | Rows | What |
|---|---|---|
| `aeo9_v0.71_demand_ALL_sectors_by_fuel.csv` | 62,940 | Final energy demand, EVERY sector (Industry, Transport, International Transport, Residential, Commercial, Agriculture and Others, Non Energy Fossil Fuels), leaf level, by fuel |
| `aeo9_v0.71_supply_power.csv` | 31,260 | Power sector: generation + installed capacity per technology |
| `aeo9_v0.71_resources_supply_exports.csv` | 13,680 | Resources: Primary Supply (≈ TPES) + energy Exports, by fuel |

## Units — read this first

| Data | Unit |
|---|---|
| Power generation | **TWh** |
| Power capacity | **GW** |
| Demand — combustion/thermal fuels | **PJ** |
| Demand — electricity | **GWh** (1 PJ = 277.778 GWh) |
| Resources — Primary Supply | **EJ** (Billion Gigajoules) |
| Resources — Exports | **PJ** (Million Gigajoules) |

The `unit` column states the unit on every row — never assume.

## Column notes
- **Demand** (`aeo9_v0.71_demand_ALL_sectors_by_fuel.csv`): `sector, layer, fuel,
  carrier, region, year, value, unit, value_pj, branch_leaf, branch_path`.
  `carrier` = electricity (GWh) or thermal (PJ); `value_pj` is the native PJ on
  every row for common-unit summing. `layer` = Historical (actuals) vs
  Projection (outlook) — temporally disjoint, so summing all leaves per
  region/year does not double-count. Rows are leaf-level; sum leaves for totals.
- **Power** (`aeo9_v0.71_supply_power.csv`): `variable` (Generation/Capacity),
  `scenario, region, year, value, unit, branch_leaf, branch_path`. The LEAP
  export `Total` row is excluded.
- **Resources** (`aeo9_v0.71_resources_supply_exports.csv`): `variable`
  (Primary Supply / Exports), `energy_class` (Primary/Secondary), `fuel,
  region, year, value, unit`.

Values are the model's outputs, not observed statistics.
