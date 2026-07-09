# AEO-9 v0.71 model results — machine-readable (2026-07-09)

Tidy (long-format) results from the `aeo9_v0.71` run, for distribution to all
sector teams. Two files, one row per data point — ready to pivot, filter, or
load into any tool. Source: `v_0.71 Power Result.xlsx` + `v_0.71 Demand
Result.xlsx`.

> **Note on versioning:** v0.70→v0.71 is a version-number bump only — no data
> edits. The content is the v0.69-cycle model as last run.

## Files

| File | Rows | What |
|---|---|---|
| `aeo9_v0.71_supply_power_tidy.csv` | 31,620 | Power sector: generation + installed capacity, per technology |
| `aeo9_v0.71_demand_by_fuel_tidy.csv` | 62,940 | Final energy demand, per fuel, at the finest (leaf) level |

Common to both: **3 scenarios** (AMS Target Scenario, Baseline Simulation,
Regional Aspiration Scenario), **10 countries** (Brunei … Vietnam; Timor
Leste excluded from the run), **6 milestone years** (2010, 2020, 2030, 2040,
2050, 2060).

## Units — read this first

| Data | Unit | Note |
|---|---|---|
| Power generation | **TWh** | (native "Thousand Gigawatt-Hours" = TWh, same number) |
| Power capacity | **GW** | (native "Thousand Megawatts" = GW, same number) |
| Demand — combustion/thermal fuels | **PJ** | (native "Million Gigajoules" = PJ, same number) |
| Demand — electricity | **GWh** | converted from PJ: **1 PJ = 277.778 GWh** |

The `unit` column states the unit on every row — never assume. (Per the
2026-07-09 request: demand is by fuel in a Joule unit, with any electricity
carrier expressed in GWh.)

## `aeo9_v0.71_supply_power_tidy.csv` columns
`domain, variable, scenario, region, year, value, unit, branch_leaf,
branch_path`
- `variable`: `Generation` (TWh) or `Capacity` (GW).
- `branch_leaf`: technology (Coal Subcritical, Solar PV, …); `branch_path` is
  the full LEAP path.

## `aeo9_v0.71_demand_by_fuel_tidy.csv` columns
`domain, scenario, sector, layer, fuel, carrier, region, year, value, unit,
value_pj, confident_carrier, branch_leaf, branch_path`
- `sector`: Industry, Transport, International Transport, Residential,
  Commercial, Agriculture and Others, Non Energy Fossil Fuels.
- `fuel`: the energy carrier — a named fuel (Natural Gas, Diesel, …) or
  `Electricity`.
- `carrier`: `electricity` (→ GWh) or `thermal` (→ PJ). How it's decided:
  a row is **electricity** if its fuel is Electricity, an electric device
  (LED, CFL, Heat Pump, Induction Electric, …), sits under an `Electricity`
  branch, or is an efficiency/stock class of an electric appliance (AC,
  refrigeration, washing machine, data-centre, …); otherwise **thermal**.
  `confident_carrier` is `True` on every row (no ambiguous cases remained).
- `value` is in `unit`; `value_pj` is the **native PJ value on every row**
  (kept for cross-checking and for summing electricity + thermal in a common
  energy unit).
- `layer`: `Historical` (actuals, carries 2010–2020) vs `Projection` (model
  output, carries 2025→2060). **They are temporally disjoint**, so summing
  all leaf rows for a sector/region/year is correct and does not
  double-count. To get just the model outlook, filter `layer = Projection`.
- Rows are **leaf-level** (finest grain). Sector/end-use subtotals are not
  included — sum the leaves (verified: leaf PJ sums exactly to the source
  sector totals).

## Handling notes
- Zeros are kept (complete grid — no missing-vs-zero ambiguity). Filter
  `value > 0` if you only want active rows.
- To total electricity across everything, sum `value_pj` where
  `carrier = electricity` (then ×277.778 for GWh), or sum `value` where
  `unit = GWh`.

Questions on the tidy format → reply to this thread.
