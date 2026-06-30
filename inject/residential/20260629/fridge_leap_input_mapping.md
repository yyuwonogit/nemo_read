# Fridge — LEAP Input Mapping (filled)

**Last updated: 2026-06-24.** Supersedes the draft suggestion in
`Residential/Fridge/Raw/refrigerator_leap_input_mapping.xlsx` (the
refrigeration team's inbound spec). This doc records the agreed,
corrected variable→value mapping for the 2-layer Size × Efficiency
Fridge tree, the useful-energy method, the Demand Cost, and the RASv2
optimisation decision. Inject CSV: `fridge_leap_inject.csv`
(12,690 rows). Builder: `Residential/Fridge/build_fridge_leap_inject.py`
(+ `.txt` sidecar). Pairs with
[`structure_request_AC_fridge_2layer_20260521.md`](structure_request_AC_fridge_2layer_20260521.md).
For the line-by-line method keyed to each workbook row, see
[`fridge_leap_rowwise_method.md`](fridge_leap_rowwise_method.md). For the optional
within-tier efficiency-drift variant (`fridge_leap_inject_drift.csv`), see
[`fridge_leap_drift_method.md`](fridge_leap_drift_method.md).

## Tree (built LEAP-side, Option A)

```
Demand\Residential\Projections\Refrigeration   (parent)
├── Small / Medium / Large                      (size nodes)
│   └── High_eff / Mid_eff / Low_eff            (efficiency leaves, 9 total)
```

## Variable map

| LEAP level | LEAP variable | Scenario | Value (source column in `fridge_leap_inject.csv`) | Notes |
|---|---|---|---|---|
| Parent | Activity Level (%) | All | `ownership_parent_pct` (= `total_ownership_pct`) | Ownership per HH. Scenario-invariant. |
| Size node | Activity Level (%) | All | `size_share_pct` | Σ stock-share of the 3 eff cells, renorm 100% across sizes. Scenario-invariant. |
| Eff leaf | Activity Level (%) | **Per scenario** | `eff_share_pct` | Within-size efficiency mix. **The only per-scenario lever.** Sums to 100% within a size. |
| Eff leaf | Efficiency (%) | All | `efficiency_pct` = kwh(High_eff,size)/kwh(cell) | High_eff = 100%, others <100%. Frozen across years/scenarios. |
| Eff leaf | Useful Energy Intensity (TOE/HH) | All | `useful_energy_intensity_toe` = kwh(High_eff,size)/11630 | Constant **within a size**. LEAP recomputes Final = Useful ÷ Efficiency = kwh_unit(cell). |
| Eff leaf | Demand Cost (2020 USD/HH) | BAS, ATS | `demand_cost_usd_per_hh` = `annualized_capital_usd` | AnnualizedCost(price_usd, life=12, rate=9%). Capital only. |
| Eff leaf | Demand Cost (2020 USD/HH) | RAS | `demand_cost_usd_per_hh` = capital + `om_electricity_usd` | AnnualizedCost(capital, 12, 9%, O&M); O&M = tariff × kwh_unit. |
| Eff leaf | Load Shape | All | — | Left at LEAP default (flat) — appropriate for fridge (24/7, ~flat aggregate load). |
| Eff leaf | Unit Capacity (kW) | **RAS** | `unit_capacity_kw` = kwh_high(size) ÷ 8760 | **Filled 2026-06-25.** Service capacity per device = useful power; Small 0.035 / Medium 0.052 / Large 0.057 kW. Same across the 3 efficiency tiers; fixed over years; **RAS (optimised) branches only** (blank for BAS/ATS). |
| Eff leaf | RAS optimisation block (rest) | RAS | — | Max Availability, Max/Min Devices, Max/Min Device Additions, Min Share, Min Utilization: **blank/unconstrained** (optimiser driven by Demand Cost + Unit Capacity). |
| Eff leaf | **Exogenous Devices** (Device) | All | `device_thousand` (× 1000 → Device) = LEAP RAS Demand Devices export | **Re-based 2026-06-29, base year 2025 only** (other years blank). Target slot is the leaf **`Exogenous Devices`** variable (FRIDGE_ANATOMY.md §4); the inbound `Demand Devices.xlsx` is the LEAP *result* export fed back as the exogenous input. Sourced directly from `Raw/demand_devices_ras_2025.csv` so the count matches LEAP; **ASEAN total 146,579 k**. Identical across BAS/ATS/RAS (scenario-invariant physical fleet; within-size split is the RAS-optimised one). `device_thousand` is in thousands → multiply by 1000 for the `Device`-unit slot. Ownership backed out from the fleet. Back-cast 2005–2025 in `fridge_device_numbers.csv`. Target slot `Exogenous Devices` is on the device-stock leaf (FRIDGE_ANATOMY.md §1.3b). |

## Corrections to the draft workbook

1. **Efficiency polarity** — workbook had `kwh_unit / kwh_unit(High_eff)` (gives >100% for worse tiers, invalid). Corrected to `kwh_unit(High_eff) / kwh_unit` so High_eff = 100%.
2. **Useful Energy Intensity** — workbook had per-cell `kwh_unit → TOE` (that is *final* energy; combined with Efficiency ≠100% it double-counts). Corrected to the per-size High_eff reference, constant within a size.
3. **Capital cost** — `price_usd` is already scenario/year premium-decayed in the source CSV, so the workbook's extra `× decay_factor` is not re-applied.

## Constants

| Constant | Value | Source |
|---|---|---|
| Discount rate (real) | 9% | ADB, *Guidelines for the Economic Analysis of Projects* (2017) |
| Lifetime | 12 yr | IEA (2021) *Cooling Emissions and Policy Synthesis*; DESIGN.md §4 |
| CRF | 0.1397 | r(1+r)ⁿ / ((1+r)ⁿ−1), r=0.09, n=12 |
| TOE/kWh | 1/11630 | 1 toe = 11.63 MWh (IEA) |

## Scenarios

- **BAS / ATS** — exogenous: paste parent + size Activity Levels once, the 9 leaf Efficiency + Useful Energy Intensity once, and the 9 per-scenario leaf Activity Levels (efficiency mix). Demand Cost = annualised capital (informational).
- **RAS (RASv2 in docs)** — optimisation: same parent/size/leaf intensity inputs; the leaf Activity Levels still supply the share *starting point*, but the optimiser minimises Demand Cost (annualised capital + electricity O&M) across the 3 efficiency leaves per size. Device/constraint variables blank this pass. CSV/LEAP scenario string stays plain `RAS` per DESIGN.md §2.2.

**Open confirm at paste:** if LEAP prices electricity as a fuel separately, ensure RAS does not also charge it via O&M (avoid double count).
