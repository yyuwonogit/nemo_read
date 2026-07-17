# DATA MANIFEST — aeo9 v0.75 Power Results (RAS)

Source: `NEMO_25 45.sqlite` (v0.75 RAS, 5-yearly, solved 2026-07-17) + the run's Excel export +
the interconnection **input** setup (`0.75 nodes.xlsx`, `0.75 lines.xlsx`).
Full `nemo_read` extraction of every populated result table.

**Two kinds of file:** `[INPUT]` = what you author (interconnection setup); everything else = **RESULT** read from the solved sqlite.
**Units:** energy = PJ · capacity = GW · emissions = tonnes. RAS only in the DB; nodes/lines input is RAS/optimization-cohort (BAS/ATS carry no lines or nodes, by design).

## Start here

| File | Contents | Columns | Rows |
|---|---|---|---|
| `DIGEST_v0.75.md` | **Read first.** Narrative digest of the v0.75 RAS result. | - | - |
| `README.md` | Package readme. | - | - |
| `DATA_MANIFEST.md` | This file — full contents index. | - | - |

## Workbook

| File | Contents | Columns | Rows |
|---|---|---|---|
| `v_0.75 Power Result.xlsx` | LEAP Excel export — Generation + Capacity for RAS/ATS/BAS (6 sheets). | sheets: RAS Cap, RAS Gen, ATS Cap, ATS Gen, BAS Cap, BAS Gen | 6 |

## INPUT — interconnection setup (nodes & lines you author)

| File | Contents | Columns | Rows |
|---|---|---|---|
| `SETUP_interconnection_topology.csv` | [INPUT] Interconnector network: 28 lines (from->to), the 8 NEW lines flagged, + authored config. All lines: exogenous capacity 0, max addition Unlimited, 100% efficiency, 30 yr, zero cost -> optimizer may build any corridor without limit. What actually builds/flows is in the RESULT files. | line_id, from_node, to_node, new_line, exogenous_capacity_MW, max_capacity_addition, efficiency_pct, availability_pct, lifetime_yr, construction_year, capital_cost, fixed_om, variable_om, interest_rate | 28 |
| `SETUP_nodal_distribution.csv` | [INPUT] How each country's generation splits across its transmission nodes (share %). Single-node countries=100%; Indonesia (4 sub-nodes) & Malaysia (3) split by trajectory. RAS/optimization cohort only. | region, transmission_node, is_subnode, share_pct_2025, share_pct_2030, share_pct_2040, share_pct_2050, share_pct_2060 | 18 |

## RESULT — generation & dispatch

| File | Contents | Columns | Rows |
|---|---|---|---|
| `RAS_generation_annual.csv` | Generation by technology x region x year (F31). PJ. | region, technology, year, generation_PJ | 1540 |
| `RAS_dispatch_by_timeslice.csv` | SUPPLY CURVE — generation by tech x region x timeslice x year. PJ. | region, technology, season, hour, year, generation_PJ | 54023 |

## RESULT — capacity

| File | Contents | Columns | Rows |
|---|---|---|---|
| `RAS_capacity_annual.csv` | Installed capacity by tech x region x year. GW. | region, technology, year, capacity_GW | 1659 |
| `RAS_new_capacity_annual.csv` | Capacity additions. GW. | region, technology, year, new_capacity_GW | 590 |
| `RAS_capacity_stack.csv` | Capacity by kind (residual vs new). GW. | region, technology, year, kind, capacity_GW | 2249 |

## RESULT — load

| File | Contents | Columns | Rows |
|---|---|---|---|
| `RAS_electricity_load_annual.csv` | Delivered load (F24) by region x year. PJ. | region, year, load_delivered_PJ | 80 |
| `RAS_load_by_timeslice.csv` | LOAD CURVE — delivered load by region x timeslice x year. PJ. | region, season, hour, year, load_delivered_PJ | 3812 |

## RESULT — interconnection (solved flows/build)

| File | Contents | Columns | Rows |
|---|---|---|---|
| `RAS_interconnection_lines_definition.csv` | [RESULT] Solved line ratings from the DB (from/to, maxflow, efficiency, cost, build year). | line, from_node, to_node, fuel, maxflow_MW, efficiency, capital_cost, fixed_cost, variable_cost, operational_life, year_construction | 28 |
| `RAS_interconnection_line_available_by_year.csv` | [RESULT] Line availability per year. | line, from_node, to_node, year, exists(1=available) | 224 |
| `RAS_interconnection_line_built_by_year.csv` | [RESULT] Endogenous line builds per year. | line, from_node, to_node, year, built | 155 |
| `RAS_interconnection_net_by_node_annual.csv` | [RESULT] Net exchange per node x year (+export/-import). PJ. | node, region, year, net_transmission_PJ(+export/-import) | 120 |
| `RAS_interconnection_by_line_annual.csv` | [RESULT] Directional flow per line x year. PJ. | line, from_node, to_node, year, flow_annual_PJ(+ = from->to), maxflow_MW | 224 |
| `RAS_interconnection_by_line_timeslice.csv` | [RESULT] Line flow per timeslice x year (MW + PJ). | line, from_node, to_node, season, hour, year, flow_MW, energy_PJ | 10752 |
| `RAS_trade_annual.csv` | [RESULT] All-commodity inter-region trade. | from_region, to_region, commodity, year, traded | 395 |

## RESULT — fuel use

| File | Contents | Columns | Rows |
|---|---|---|---|
| `RAS_fuel_use_by_power_tech_annual.csv` | Fuel input consumed by each power tech. PJ. | region, technology, input_fuel, year, use_PJ | 1057 |
| `RAS_fuel_use_rate_by_timeslice.csv` | Fuel use rate by fuel x timeslice x year. | region, fuel, season, hour, year, use_rate | 12623 |
| `RAS_production_rate_by_fuel_timeslice.csv` | Production rate by fuel x timeslice x year. | region, fuel, season, hour, year, prod_rate | 13336 |

## RESULT — emissions

| File | Contents | Columns | Rows |
|---|---|---|---|
| `RAS_power_co2_emissions_annual.csv` | Power CO2 by region x year. tonnes. | region, year, co2_tonnes | 80 |
| `RAS_emissions_by_tech_all_species_annual.csv` | All 13 pollutant species by tech x region x year. tonnes. | region, technology, pollutant, year, value_tonnes | 6556 |
| `RAS_emissions_by_region_all_species_annual.csv` | All species by region x year. tonnes. | region, pollutant, year, value_tonnes | 1113 |

## RESULT — cost

| File | Contents | Columns | Rows |
|---|---|---|---|
| `RAS_power_costs_annual.csv` | Undiscounted cost: capital + fixed OM + variable OM. | region, technology, year, capital_investment, fixed_om, variable_om | 1659 |
| `RAS_power_costs_discounted.csv` | Discounted cost: capital + operating + salvage. | region, technology, year, disc_capital, disc_operating, disc_salvage_value | 1709 |

## Reference

| File | Contents | Columns | Rows |
|---|---|---|---|
| `RAS_timeslice_definition.csv` | 48 timeslices — season, hour, hours, yearsplit. | timeslice, season, hour, year, hours, yearsplit_fraction | 384 |
| `RAS_power_technology_reference.csv` | Power tech list + Unmet-Load slack flag. | tech_id, technology, is_unmet_load_slack | 125 |

## Comparison v0.74 vs v0.75

| File | Contents | Columns | Rows |
|---|---|---|---|
| `COMPARE_system_totals_42_vs_45.csv` | v0.74 vs v0.75 system totals. | metric, year, v0.74_run42, v0.75_run45, delta, delta_pct | 64 |
| `COMPARE_generation_and_trade_by_region.csv` | Per-region generation + net trade, both runs. | region, year, gen_v0.74_PJ, gen_v0.75_PJ, gen_delta_PJ, net_trade_v0.74_PJ, net_trade_v0.75_PJ | 80 |


**Total: 32 files.** Generated 2026-07-17.