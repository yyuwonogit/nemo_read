# AC — LEAP Input Mapping (filled)

**Last updated: 2026-06-24.** AC uses the **same 14-variable mapping** as the
Fridge workbook (`Residential/Fridge/Raw/refrigerator_leap_input_mapping.xlsx`) —
no separate AC workbook landed; per user steer 2026-06-24 the AC inject reuses the
Fridge structure and shared inputs. Inject CSV: `ac_leap_inject.csv` (12,690 rows).
Builder: `Residential/AC/build_ac_leap_inject.py` (+ `.txt` sidecar). Row-by-row:
[`ac_leap_rowwise_method.md`](ac_leap_rowwise_method.md). Drift variant:
[`ac_leap_drift_method.md`](ac_leap_drift_method.md). Pairs with
[`structure_request_AC_fridge_2layer_20260521.md`](structure_request_AC_fridge_2layer_20260521.md).

## Tree (built LEAP-side, Option A)

```
Demand\Residential\Projections\Air Conditioning   (parent — confirm exact branch name)
├── Small / Medium / Large                          (size nodes; BTU/h bands)
│   └── High_eff / Mid_eff / Low_eff                (efficiency leaves, 9 total; CSPF bands)
```

## What differs from Fridge

| | Fridge | AC |
|---|---|---|
| Lifetime | 12 yr → CRF 0.140 | **15 yr → CRF 0.124** (IEA 2018 / JICA 2020) |
| Units per HH | ~1 (used ownership%) | **1.2–3.4** (`intensity`) → parent Activity Level = **`stock_per_hh`** (units/HH = penetration × intensity), **Option A** |
| Demand Cost / FEI basis | per household | **per unit (device)** |
| kWh magnitude | 305–760 | **783–3,523** (1,600 op-h/yr, CSPF bands) → O&M dominates RAS lifecycle cost more |
| Tariffs, discount rate | — | **shared** (same `electricity_tariffs.csv`, 9% rate) |

## Variable map

| LEAP level | LEAP variable | Scenario | Value (column in `ac_leap_inject.csv`) | Notes |
|---|---|---|---|---|
| Parent | Activity Level | All | `units_per_hh_parent` (= `stock_per_hh`) | **Option A**: units per HH (saturation × intensity). May exceed 100% (SGP ≈2.8–3.0). Scenario-invariant. |
| Size node | Activity Level (%) | All | `size_share_pct` | Σ stock-share of the 3 eff cells, renorm 100% across sizes. Scenario-invariant. |
| Eff leaf | Activity Level (%) | **Per scenario** | `eff_share_pct` | Within-size efficiency mix — the only per-scenario lever. Sums to 100% within a size. |
| Eff leaf | Efficiency (%) | All | `efficiency_pct` = kwh(High_eff,size)/kwh(cell) | High_eff = 100%, others <100%. Frozen across years/scenarios. |
| Eff leaf | Useful Energy Intensity (TOE/unit) | All | `useful_energy_intensity_toe` = kwh(High_eff,size)/11630 | Constant within a size. LEAP: Final = Useful ÷ Efficiency = kwh_unit. |
| Eff leaf | Demand Cost (2020 USD/unit) | BAS, ATS | `annualized_capital_usd` = price_usd × CRF(9%,15) | Capital only. |
| Eff leaf | Demand Cost (2020 USD/unit) | RAS | `demand_cost_usd_per_unit` = capital + `om_electricity_usd` | O&M = tariff × kwh_unit; RAS = optimisation. |
| Branch/leaf | Energy Load Shape | All | per-country named shape `<Country>_AC_Cooling` | **Built 2026-06-29; uploaded to LEAP SEPARATELY — NOT in the inject.** CDD-derived 2-season × 24 h cooling profile (`AC/LoadShape/`, 10 named shapes). The inject's Unit Capacity is consistent with it. |
| Eff leaf | Unit Capacity (kW) | **RAS** | `unit_capacity_kw` = kwh_high(size) ÷ FLEH | **Filled 2026-06-30.** Per Country×Size (FLEH from each country's cooling shape, ~3,330–4,610 h); same across eff tiers, fixed over years; RAS (optimised) leaf only (blank BAS/ATS). Makes LEAP device count = stock. |
| Eff leaf | **Exogenous Devices** (Device) | All | `device_thousand` (× 1000 → Device), every year 2005–2060, from `ac_exo_device.csv` | **Added 2026-06-30.** Existing AC fleet only, Weibull retirement (k=3, mean **15 yr**), NO additions — LEAP optimises additions. 2025 fleet (= our AC projection, ASEAN 97,820 k) frozen, retired to ~0 by ~2055. Mirrors Fridge. |
| Eff leaf | RAS optimisation block (rest) | RAS | — | Max Availability, Max/Min Devices/Additions, Min Share, Min Utilization: **blank/unconstrained** (same as Fridge). |

Reference columns also emitted for the alternative Option B (penetration% +
separate intensity): `penetration_pct`, `intensity`, `leaf_units_per_hh`.

## Constants

| Constant | Value | Source |
|---|---|---|
| Discount rate (real) | 9% | ADB, *Guidelines for the Economic Analysis of Projects* (2017) |
| Lifetime | 15 yr | IEA (2018) *Future of Cooling*; JICA (2020) — data_sources.md §2.5 |
| CRF | 0.1241 | r(1+r)ⁿ/((1+r)ⁿ−1), r=0.09, n=15 |
| TOE/kWh | 1/11630 | 1 toe = 11.63 MWh (IEA) |

## Efficiency + Useful Energy Intensity (computed)

| Size | Useful EI (TOE/unit) | High_eff | Mid_eff | Low_eff |
|---|---|---|---|---|
| Small | 0.06729 (←782.6 kWh) | 100.0% | 81.9% | 64.5% |
| Medium | 0.09773 (←1,136.6 kWh) | 100.0% | 75.0% | 51.1% |
| Large | 0.16034 (←1,864.7 kWh) | 100.0% | 72.3% | 52.9% |

## Decision on the books

**Units-per-household = Option A** (`stock_per_hh` as the parent driver), chosen
2026-06-24. Reversible to Option B (parent = `penetration_pct` + a separate
`intensity` device-multiplier) — both give identical energy; the reference columns
for B are already in the CSV. **Open confirm at paste:** if LEAP prices electricity
as a fuel separately, RAS must use Demand Cost only (avoid double count).
