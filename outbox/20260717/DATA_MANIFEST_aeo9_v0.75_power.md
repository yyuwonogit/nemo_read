# DATA MANIFEST — aeo9_v0.75 Power Results (RAS)

Zip: `aeo9_v0.75_Power_Results_20260717.zip` · Source: `NEMO_25 45.sqlite`
(v0.75 Regional Aspiration, 5-yearly 2025-2060, solved 2026-07-17) + its Excel export.
Full `nemo_read` extraction of every populated result table + interconnection infrastructure.

**Units:** energy = PJ (workbook label 'Million Gigajoules') · capacity = GW ('Thousand MW') · emissions = tonnes.
**Scope:** RAS only (one scenario in the DB); the workbook also carries the run's ATS/BAS Gen+Cap.

| File | Contents | Columns | Rows |
|---|---|---|---|
| `DIGEST_v0.75.md` | **Read first.** Narrative digest of the v0.75 RAS result: generation mix, interconnection change, feasibility flag. | - | - |
| `README.md` | Package readme (grouped file index + units). | - | - |
| `v_0.75 Power Result.xlsx` | LEAP Excel export — Generation + Capacity for RAS/ATS/BAS (6 sheets). Verified 1:1 with the DB. | sheets: RAS Cap, RAS Gen, ATS Cap, ATS Gen, BAS Cap, BAS Gen | 6 |
| `RAS_generation_annual.csv` | Generation by technology x region x year (electricity out, fuel F31). PJ. | region, technology, year, generation_PJ | 1540 |
| `RAS_dispatch_by_timeslice.csv` | SUPPLY CURVE — generation by technology x region x timeslice (Wet/Dry x Hr 1-24) x year. PJ. | region, technology, season, hour, year, generation_PJ | 54023 |
| `RAS_capacity_annual.csv` | Installed capacity by technology x region x year. GW. | region, technology, year, capacity_GW | 1659 |
| `RAS_new_capacity_annual.csv` | Capacity additions by technology x region x year. GW. | region, technology, year, new_capacity_GW | 590 |
| `RAS_capacity_stack.csv` | Capacity split by kind (residual vs newly-built) x technology x region x year. GW. | region, technology, year, kind, capacity_GW | 2249 |
| `RAS_electricity_load_annual.csv` | Delivered electricity (load, T&D output F24) by region x year. PJ. | region, year, load_delivered_PJ | 80 |
| `RAS_load_by_timeslice.csv` | LOAD CURVE — delivered electricity by region x timeslice x year. PJ. | region, season, hour, year, load_delivered_PJ | 3812 |
| `RAS_interconnection_lines_definition.csv` | INTERCONNECTION CAPACITY — all 28 lines: from/to node, MW rating (maxflow), efficiency, capital/fixed/variable cost, life, construction year. | line, from_node, to_node, fuel, maxflow_MW, efficiency, capital_cost, fixed_cost, variable_cost, operational_life, year_construction | 28 |
| `RAS_interconnection_line_available_by_year.csv` | Which interconnector lines are available each year (exists=1). | line, from_node, to_node, year, exists(1=available) | 224 |
| `RAS_interconnection_line_built_by_year.csv` | Endogenous interconnector builds per year. | line, from_node, to_node, year, built | 155 |
| `RAS_interconnection_net_by_node_annual.csv` | Net cross-border exchange per node x year. + = net export, - = net import. PJ. | node, region, year, net_transmission_PJ(+export/-import) | 120 |
| `RAS_interconnection_by_line_annual.csv` | Directional flow per interconnector line x year. + = from_node -> to_node. PJ. | line, from_node, to_node, year, flow_annual_PJ(+ = from->to), maxflow_MW | 224 |
| `RAS_interconnection_by_line_timeslice.csv` | Interconnector flow per line x timeslice x year — flow_MW (power) + energy_PJ. For utilisation/peak analysis. | line, from_node, to_node, season, hour, year, flow_MW, energy_PJ | 10752 |
| `RAS_trade_annual.csv` | All-commodity inter-region trade (bioenergy feedstocks/fuels etc.) — from_region x to_region x commodity x year. | from_region, to_region, commodity, year, traded | 395 |
| `RAS_fuel_use_by_power_tech_annual.csv` | Fuel INPUT consumed by each power technology (coal, gas, etc.) x region x year. PJ. | region, technology, input_fuel, year, use_PJ | 1057 |
| `RAS_fuel_use_rate_by_timeslice.csv` | Fuel use RATE by fuel x region x timeslice x year. | region, fuel, season, hour, year, use_rate | 12623 |
| `RAS_production_rate_by_fuel_timeslice.csv` | Production RATE by fuel x region x timeslice x year. | region, fuel, season, hour, year, prod_rate | 13336 |
| `RAS_power_co2_emissions_annual.csv` | Power-sector CO2 by region x year. tonnes. | region, year, co2_tonnes | 80 |
| `RAS_emissions_by_tech_all_species_annual.csv` | ALL 13 pollutant species (CO2, CH4, N2O, SO2, NOx, PM10/2.5, BC, NH3, CO, NMVOC, ...) by technology x region x year. tonnes. | region, technology, pollutant, year, value_tonnes | 6556 |
| `RAS_emissions_by_region_all_species_annual.csv` | All pollutant species by region x year (regional totals). tonnes. | region, pollutant, year, value_tonnes | 1113 |
| `RAS_power_costs_annual.csv` | Undiscounted cost by technology x region x year: capital investment + fixed OM + variable OM. | region, technology, year, capital_investment, fixed_om, variable_om | 1659 |
| `RAS_power_costs_discounted.csv` | Discounted cost by technology x region x year: capital + operating + salvage value. | region, technology, year, disc_capital, disc_operating, disc_salvage_value | 1709 |
| `RAS_timeslice_definition.csv` | The 48 representative timeslices — season, hour, hours-per-year, yearsplit fraction. Key for every *_by_timeslice / *_rate_* file. | timeslice, season, hour, year, hours, yearsplit_fraction | 384 |
| `RAS_power_technology_reference.csv` | Power technology list: id, LEAP name, and whether it is an Unmet-Load slack pseudo-tech. | tech_id, technology, is_unmet_load_slack | 125 |
| `COMPARE_system_totals_42_vs_45.csv` | System totals v0.74(run42) vs v0.75(run45): load, generation, capacity, cross-border, unmet load, CapEx, OM, CO2 — per year + delta. | metric, year, v0.74_run42, v0.75_run45, delta, delta_pct | 64 |
| `COMPARE_generation_and_trade_by_region.csv` | Per-region generation and net trade, both runs, per year. | region, year, gen_v0.74_PJ, gen_v0.75_PJ, gen_delta_PJ, net_trade_v0.74_PJ, net_trade_v0.75_PJ | 80 |

**Total: 29 files.** Generated 2026-07-17.