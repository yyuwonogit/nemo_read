# Region-lock cleanup (CLAUDE.md §A.21) — fix_exogenous_capacity.csv

Removed **330** rows authoring a region-locked node-variant in the wrong AMS. A `_MY*` node exists only in Malaysia, a `_ID*` node only in Indonesia; a value elsewhere is a data error (the branch is inert there, Node=0).

Kept 395 rows. Original backed up as `fix_exogenous_capacity.csv.bak_pre_regionlock`.

| node | wrong region | belongs to |
|---|---|---|
| Biomass Other_MYPE | Brunei | Malaysia |
| Biomass Other_MYPE | Cambodia | Malaysia |
| Biomass Other_MYPE | Indonesia | Malaysia |
| Biomass Other_MYPE | Laos | Malaysia |
| Biomass Other_MYPE | Myanmar | Malaysia |
| Biomass Other_MYPE | Philippines | Malaysia |
| Biomass Other_MYPE | Singapore | Malaysia |
| Biomass Other_MYPE | Thailand | Malaysia |
| Biomass Other_MYPE | Timor Leste | Malaysia |
| Biomass Other_MYPE | Vietnam | Malaysia |
| Biomass Other_MYSB | Brunei | Malaysia |
| Biomass Other_MYSB | Cambodia | Malaysia |
| Biomass Other_MYSB | Indonesia | Malaysia |
| Biomass Other_MYSB | Laos | Malaysia |
| Biomass Other_MYSB | Myanmar | Malaysia |
| Biomass Other_MYSB | Philippines | Malaysia |
| Biomass Other_MYSB | Singapore | Malaysia |
| Biomass Other_MYSB | Thailand | Malaysia |
| Biomass Other_MYSB | Timor Leste | Malaysia |
| Biomass Other_MYSB | Vietnam | Malaysia |
| Biomass Other_MYSR | Brunei | Malaysia |
| Biomass Other_MYSR | Cambodia | Malaysia |
| Biomass Other_MYSR | Indonesia | Malaysia |
| Biomass Other_MYSR | Laos | Malaysia |
| Biomass Other_MYSR | Myanmar | Malaysia |
| Biomass Other_MYSR | Philippines | Malaysia |
| Biomass Other_MYSR | Singapore | Malaysia |
| Biomass Other_MYSR | Thailand | Malaysia |
| Biomass Other_MYSR | Timor Leste | Malaysia |
| Biomass Other_MYSR | Vietnam | Malaysia |
| Coal Subcritical_MYPE | Brunei | Malaysia |
| Coal Subcritical_MYPE | Cambodia | Malaysia |
| Coal Subcritical_MYPE | Indonesia | Malaysia |
| Coal Subcritical_MYPE | Laos | Malaysia |
| Coal Subcritical_MYPE | Myanmar | Malaysia |
| Coal Subcritical_MYPE | Philippines | Malaysia |
| Coal Subcritical_MYPE | Singapore | Malaysia |
| Coal Subcritical_MYPE | Thailand | Malaysia |
| Coal Subcritical_MYPE | Timor Leste | Malaysia |
| Coal Subcritical_MYPE | Vietnam | Malaysia |
| Coal Subcritical_MYSR | Brunei | Malaysia |
| Coal Subcritical_MYSR | Cambodia | Malaysia |
| Coal Subcritical_MYSR | Indonesia | Malaysia |
| Coal Subcritical_MYSR | Laos | Malaysia |
| Coal Subcritical_MYSR | Myanmar | Malaysia |
| Coal Subcritical_MYSR | Philippines | Malaysia |
| Coal Subcritical_MYSR | Singapore | Malaysia |
| Coal Subcritical_MYSR | Thailand | Malaysia |
| Coal Subcritical_MYSR | Timor Leste | Malaysia |
| Coal Subcritical_MYSR | Vietnam | Malaysia |
| Diesel_MYPE | Brunei | Malaysia |
| Diesel_MYPE | Cambodia | Malaysia |
| Diesel_MYPE | Indonesia | Malaysia |
| Diesel_MYPE | Laos | Malaysia |
| Diesel_MYPE | Myanmar | Malaysia |
| Diesel_MYPE | Philippines | Malaysia |
| Diesel_MYPE | Singapore | Malaysia |
| Diesel_MYPE | Thailand | Malaysia |
| Diesel_MYPE | Timor Leste | Malaysia |
| Diesel_MYPE | Vietnam | Malaysia |
| Diesel_MYSB | Brunei | Malaysia |
| Diesel_MYSB | Cambodia | Malaysia |
| Diesel_MYSB | Indonesia | Malaysia |
| Diesel_MYSB | Laos | Malaysia |
| Diesel_MYSB | Myanmar | Malaysia |
| Diesel_MYSB | Philippines | Malaysia |
| Diesel_MYSB | Singapore | Malaysia |
| Diesel_MYSB | Thailand | Malaysia |
| Diesel_MYSB | Timor Leste | Malaysia |
| Diesel_MYSB | Vietnam | Malaysia |
| Diesel_MYSR | Brunei | Malaysia |
| Diesel_MYSR | Cambodia | Malaysia |
| Diesel_MYSR | Indonesia | Malaysia |
| Diesel_MYSR | Laos | Malaysia |
| Diesel_MYSR | Myanmar | Malaysia |
| Diesel_MYSR | Philippines | Malaysia |
| Diesel_MYSR | Singapore | Malaysia |
| Diesel_MYSR | Thailand | Malaysia |
| Diesel_MYSR | Timor Leste | Malaysia |
| Diesel_MYSR | Vietnam | Malaysia |
| Gas Combined Cycle_MYPE | Brunei | Malaysia |
| Gas Combined Cycle_MYPE | Cambodia | Malaysia |
| Gas Combined Cycle_MYPE | Indonesia | Malaysia |
| Gas Combined Cycle_MYPE | Laos | Malaysia |
| Gas Combined Cycle_MYPE | Myanmar | Malaysia |
| Gas Combined Cycle_MYPE | Philippines | Malaysia |
| Gas Combined Cycle_MYPE | Singapore | Malaysia |
| Gas Combined Cycle_MYPE | Thailand | Malaysia |
| Gas Combined Cycle_MYPE | Timor Leste | Malaysia |
| Gas Combined Cycle_MYPE | Vietnam | Malaysia |
| Gas Combined Cycle_MYSB | Brunei | Malaysia |
| Gas Combined Cycle_MYSB | Cambodia | Malaysia |
| Gas Combined Cycle_MYSB | Indonesia | Malaysia |
| Gas Combined Cycle_MYSB | Laos | Malaysia |
| Gas Combined Cycle_MYSB | Myanmar | Malaysia |
| Gas Combined Cycle_MYSB | Philippines | Malaysia |
| Gas Combined Cycle_MYSB | Singapore | Malaysia |
| Gas Combined Cycle_MYSB | Thailand | Malaysia |
| Gas Combined Cycle_MYSB | Timor Leste | Malaysia |
| Gas Combined Cycle_MYSB | Vietnam | Malaysia |
| Gas Combined Cycle_MYSR | Brunei | Malaysia |
| Gas Combined Cycle_MYSR | Cambodia | Malaysia |
| Gas Combined Cycle_MYSR | Indonesia | Malaysia |
| Gas Combined Cycle_MYSR | Laos | Malaysia |
| Gas Combined Cycle_MYSR | Myanmar | Malaysia |
| Gas Combined Cycle_MYSR | Philippines | Malaysia |
| Gas Combined Cycle_MYSR | Singapore | Malaysia |
| Gas Combined Cycle_MYSR | Thailand | Malaysia |
| Gas Combined Cycle_MYSR | Timor Leste | Malaysia |
| Gas Combined Cycle_MYSR | Vietnam | Malaysia |
| Gas Turbine_MYPE | Brunei | Malaysia |
| Gas Turbine_MYPE | Cambodia | Malaysia |
| Gas Turbine_MYPE | Indonesia | Malaysia |
| Gas Turbine_MYPE | Laos | Malaysia |
| Gas Turbine_MYPE | Myanmar | Malaysia |
| Gas Turbine_MYPE | Philippines | Malaysia |
| Gas Turbine_MYPE | Singapore | Malaysia |
| Gas Turbine_MYPE | Thailand | Malaysia |
| Gas Turbine_MYPE | Timor Leste | Malaysia |
| Gas Turbine_MYPE | Vietnam | Malaysia |
| Large Hydro_MYPE | Brunei | Malaysia |
| Large Hydro_MYPE | Cambodia | Malaysia |
| Large Hydro_MYPE | Indonesia | Malaysia |
| Large Hydro_MYPE | Laos | Malaysia |
| Large Hydro_MYPE | Myanmar | Malaysia |
| Large Hydro_MYPE | Philippines | Malaysia |
| Large Hydro_MYPE | Singapore | Malaysia |
| Large Hydro_MYPE | Thailand | Malaysia |
| Large Hydro_MYPE | Timor Leste | Malaysia |
| Large Hydro_MYPE | Vietnam | Malaysia |
| Large Hydro_MYSB | Brunei | Malaysia |
| Large Hydro_MYSB | Cambodia | Malaysia |
| Large Hydro_MYSB | Indonesia | Malaysia |
| Large Hydro_MYSB | Laos | Malaysia |
| Large Hydro_MYSB | Myanmar | Malaysia |
| Large Hydro_MYSB | Philippines | Malaysia |
| Large Hydro_MYSB | Singapore | Malaysia |
| Large Hydro_MYSB | Thailand | Malaysia |
| Large Hydro_MYSB | Timor Leste | Malaysia |
| Large Hydro_MYSB | Vietnam | Malaysia |
| Large Hydro_MYSR | Brunei | Malaysia |
| Large Hydro_MYSR | Cambodia | Malaysia |
| Large Hydro_MYSR | Indonesia | Malaysia |
| Large Hydro_MYSR | Laos | Malaysia |
| Large Hydro_MYSR | Myanmar | Malaysia |
| Large Hydro_MYSR | Philippines | Malaysia |
| Large Hydro_MYSR | Singapore | Malaysia |
| Large Hydro_MYSR | Thailand | Malaysia |
| Large Hydro_MYSR | Timor Leste | Malaysia |
| Large Hydro_MYSR | Vietnam | Malaysia |
| Nuclear LWR_MYPE | Brunei | Malaysia |
| Nuclear LWR_MYPE | Cambodia | Malaysia |
| Nuclear LWR_MYPE | Indonesia | Malaysia |
| Nuclear LWR_MYPE | Laos | Malaysia |
| Nuclear LWR_MYPE | Myanmar | Malaysia |
| Nuclear LWR_MYPE | Philippines | Malaysia |
| Nuclear LWR_MYPE | Singapore | Malaysia |
| Nuclear LWR_MYPE | Thailand | Malaysia |
| Nuclear LWR_MYPE | Timor Leste | Malaysia |
| Nuclear LWR_MYPE | Vietnam | Malaysia |
| Nuclear LWR_MYSB | Brunei | Malaysia |
| Nuclear LWR_MYSB | Cambodia | Malaysia |
| Nuclear LWR_MYSB | Indonesia | Malaysia |
| Nuclear LWR_MYSB | Laos | Malaysia |
| Nuclear LWR_MYSB | Myanmar | Malaysia |
| Nuclear LWR_MYSB | Philippines | Malaysia |
| Nuclear LWR_MYSB | Singapore | Malaysia |
| Nuclear LWR_MYSB | Thailand | Malaysia |
| Nuclear LWR_MYSB | Timor Leste | Malaysia |
| Nuclear LWR_MYSB | Vietnam | Malaysia |
| Nuclear LWR_MYSR | Brunei | Malaysia |
| Nuclear LWR_MYSR | Cambodia | Malaysia |
| Nuclear LWR_MYSR | Indonesia | Malaysia |
| Nuclear LWR_MYSR | Laos | Malaysia |
| Nuclear LWR_MYSR | Myanmar | Malaysia |
| Nuclear LWR_MYSR | Philippines | Malaysia |
| Nuclear LWR_MYSR | Singapore | Malaysia |
| Nuclear LWR_MYSR | Thailand | Malaysia |
| Nuclear LWR_MYSR | Timor Leste | Malaysia |
| Nuclear LWR_MYSR | Vietnam | Malaysia |
| Nuclear SFR_MYPE | Brunei | Malaysia |
| Nuclear SFR_MYPE | Cambodia | Malaysia |
| Nuclear SFR_MYPE | Indonesia | Malaysia |
| Nuclear SFR_MYPE | Laos | Malaysia |
| Nuclear SFR_MYPE | Myanmar | Malaysia |
| Nuclear SFR_MYPE | Philippines | Malaysia |
| Nuclear SFR_MYPE | Singapore | Malaysia |
| Nuclear SFR_MYPE | Thailand | Malaysia |
| Nuclear SFR_MYPE | Timor Leste | Malaysia |
| Nuclear SFR_MYPE | Vietnam | Malaysia |
| Nuclear SFR_MYSB | Brunei | Malaysia |
| Nuclear SFR_MYSB | Cambodia | Malaysia |
| Nuclear SFR_MYSB | Indonesia | Malaysia |
| Nuclear SFR_MYSB | Laos | Malaysia |
| Nuclear SFR_MYSB | Myanmar | Malaysia |
| Nuclear SFR_MYSB | Philippines | Malaysia |
| Nuclear SFR_MYSB | Singapore | Malaysia |
| Nuclear SFR_MYSB | Thailand | Malaysia |
| Nuclear SFR_MYSB | Timor Leste | Malaysia |
| Nuclear SFR_MYSB | Vietnam | Malaysia |
| Nuclear SFR_MYSR | Brunei | Malaysia |
| Nuclear SFR_MYSR | Cambodia | Malaysia |
| Nuclear SFR_MYSR | Indonesia | Malaysia |
| Nuclear SFR_MYSR | Laos | Malaysia |
| Nuclear SFR_MYSR | Myanmar | Malaysia |
| Nuclear SFR_MYSR | Philippines | Malaysia |
| Nuclear SFR_MYSR | Singapore | Malaysia |
| Nuclear SFR_MYSR | Thailand | Malaysia |
| Nuclear SFR_MYSR | Timor Leste | Malaysia |
| Nuclear SFR_MYSR | Vietnam | Malaysia |
| Nuclear SMR_MYPE | Brunei | Malaysia |
| Nuclear SMR_MYPE | Cambodia | Malaysia |
| Nuclear SMR_MYPE | Indonesia | Malaysia |
| Nuclear SMR_MYPE | Laos | Malaysia |
| Nuclear SMR_MYPE | Myanmar | Malaysia |
| Nuclear SMR_MYPE | Philippines | Malaysia |
| Nuclear SMR_MYPE | Singapore | Malaysia |
| Nuclear SMR_MYPE | Thailand | Malaysia |
| Nuclear SMR_MYPE | Timor Leste | Malaysia |
| Nuclear SMR_MYPE | Vietnam | Malaysia |
| Nuclear SMR_MYSB | Brunei | Malaysia |
| Nuclear SMR_MYSB | Cambodia | Malaysia |
| Nuclear SMR_MYSB | Indonesia | Malaysia |
| Nuclear SMR_MYSB | Laos | Malaysia |
| Nuclear SMR_MYSB | Myanmar | Malaysia |
| Nuclear SMR_MYSB | Philippines | Malaysia |
| Nuclear SMR_MYSB | Singapore | Malaysia |
| Nuclear SMR_MYSB | Thailand | Malaysia |
| Nuclear SMR_MYSB | Timor Leste | Malaysia |
| Nuclear SMR_MYSB | Vietnam | Malaysia |
| Nuclear SMR_MYSR | Brunei | Malaysia |
| Nuclear SMR_MYSR | Cambodia | Malaysia |
| Nuclear SMR_MYSR | Indonesia | Malaysia |
| Nuclear SMR_MYSR | Laos | Malaysia |
| Nuclear SMR_MYSR | Myanmar | Malaysia |
| Nuclear SMR_MYSR | Philippines | Malaysia |
| Nuclear SMR_MYSR | Singapore | Malaysia |
| Nuclear SMR_MYSR | Thailand | Malaysia |
| Nuclear SMR_MYSR | Timor Leste | Malaysia |
| Nuclear SMR_MYSR | Vietnam | Malaysia |
| Solar PV_MYPE | Brunei | Malaysia |
| Solar PV_MYPE | Cambodia | Malaysia |
| Solar PV_MYPE | Indonesia | Malaysia |
| Solar PV_MYPE | Laos | Malaysia |
| Solar PV_MYPE | Myanmar | Malaysia |
| Solar PV_MYPE | Philippines | Malaysia |
| Solar PV_MYPE | Singapore | Malaysia |
| Solar PV_MYPE | Thailand | Malaysia |
| Solar PV_MYPE | Timor Leste | Malaysia |
| Solar PV_MYPE | Vietnam | Malaysia |
| Solar PV_MYSB | Brunei | Malaysia |
| Solar PV_MYSB | Cambodia | Malaysia |
| Solar PV_MYSB | Indonesia | Malaysia |
| Solar PV_MYSB | Laos | Malaysia |
| Solar PV_MYSB | Myanmar | Malaysia |
| Solar PV_MYSB | Philippines | Malaysia |
| Solar PV_MYSB | Singapore | Malaysia |
| Solar PV_MYSB | Thailand | Malaysia |
| Solar PV_MYSB | Timor Leste | Malaysia |
| Solar PV_MYSB | Vietnam | Malaysia |
| Solar PV_MYSR | Brunei | Malaysia |
| Solar PV_MYSR | Cambodia | Malaysia |
| Solar PV_MYSR | Indonesia | Malaysia |
| Solar PV_MYSR | Laos | Malaysia |
| Solar PV_MYSR | Myanmar | Malaysia |
| Solar PV_MYSR | Philippines | Malaysia |
| Solar PV_MYSR | Singapore | Malaysia |
| Solar PV_MYSR | Thailand | Malaysia |
| Solar PV_MYSR | Timor Leste | Malaysia |
| Solar PV_MYSR | Vietnam | Malaysia |
| Unmet Load_MYPE | Brunei | Malaysia |
| Unmet Load_MYPE | Cambodia | Malaysia |
| Unmet Load_MYPE | Indonesia | Malaysia |
| Unmet Load_MYPE | Laos | Malaysia |
| Unmet Load_MYPE | Myanmar | Malaysia |
| Unmet Load_MYPE | Philippines | Malaysia |
| Unmet Load_MYPE | Singapore | Malaysia |
| Unmet Load_MYPE | Thailand | Malaysia |
| Unmet Load_MYPE | Timor Leste | Malaysia |
| Unmet Load_MYPE | Vietnam | Malaysia |
| Unmet Load_MYSB | Brunei | Malaysia |
| Unmet Load_MYSB | Cambodia | Malaysia |
| Unmet Load_MYSB | Indonesia | Malaysia |
| Unmet Load_MYSB | Laos | Malaysia |
| Unmet Load_MYSB | Myanmar | Malaysia |
| Unmet Load_MYSB | Philippines | Malaysia |
| Unmet Load_MYSB | Singapore | Malaysia |
| Unmet Load_MYSB | Thailand | Malaysia |
| Unmet Load_MYSB | Timor Leste | Malaysia |
| Unmet Load_MYSB | Vietnam | Malaysia |
| Unmet Load_MYSR | Brunei | Malaysia |
| Unmet Load_MYSR | Cambodia | Malaysia |
| Unmet Load_MYSR | Indonesia | Malaysia |
| Unmet Load_MYSR | Laos | Malaysia |
| Unmet Load_MYSR | Myanmar | Malaysia |
| Unmet Load_MYSR | Philippines | Malaysia |
| Unmet Load_MYSR | Singapore | Malaysia |
| Unmet Load_MYSR | Thailand | Malaysia |
| Unmet Load_MYSR | Timor Leste | Malaysia |
| Unmet Load_MYSR | Vietnam | Malaysia |
| Wind Onshore_MYPE | Brunei | Malaysia |
| Wind Onshore_MYPE | Cambodia | Malaysia |
| Wind Onshore_MYPE | Indonesia | Malaysia |
| Wind Onshore_MYPE | Laos | Malaysia |
| Wind Onshore_MYPE | Myanmar | Malaysia |
| Wind Onshore_MYPE | Philippines | Malaysia |
| Wind Onshore_MYPE | Singapore | Malaysia |
| Wind Onshore_MYPE | Thailand | Malaysia |
| Wind Onshore_MYPE | Timor Leste | Malaysia |
| Wind Onshore_MYPE | Vietnam | Malaysia |
| Wind Onshore_MYSB | Brunei | Malaysia |
| Wind Onshore_MYSB | Cambodia | Malaysia |
| Wind Onshore_MYSB | Indonesia | Malaysia |
| Wind Onshore_MYSB | Laos | Malaysia |
| Wind Onshore_MYSB | Myanmar | Malaysia |
| Wind Onshore_MYSB | Philippines | Malaysia |
| Wind Onshore_MYSB | Singapore | Malaysia |
| Wind Onshore_MYSB | Thailand | Malaysia |
| Wind Onshore_MYSB | Timor Leste | Malaysia |
| Wind Onshore_MYSB | Vietnam | Malaysia |
| Wind Onshore_MYSR | Brunei | Malaysia |
| Wind Onshore_MYSR | Cambodia | Malaysia |
| Wind Onshore_MYSR | Indonesia | Malaysia |
| Wind Onshore_MYSR | Laos | Malaysia |
| Wind Onshore_MYSR | Myanmar | Malaysia |
| Wind Onshore_MYSR | Philippines | Malaysia |
| Wind Onshore_MYSR | Singapore | Malaysia |
| Wind Onshore_MYSR | Thailand | Malaysia |
| Wind Onshore_MYSR | Timor Leste | Malaysia |
| Wind Onshore_MYSR | Vietnam | Malaysia |

---

## Second pass — 2026-07-07 (§A.23 base-branch authoring lock)

4 further rows removed from `fix_exogenous_capacity.csv` (395 → 391):
Indonesia × Exogenous Capacity on base `Biogas` / `Gas Engine` /
`Gas Turbine` / `Geothermal Flash`. Indonesia's fleet for these families
lives only on the `_ID*` nodes (raw Indonesia Export-Expressions walk has
zero base rows; LEAP live-refused base writes 2026-07-07). Backup:
`fix_exogenous_capacity.csv.bak_pre_basebranch_20260707`. Full record:
[inject/power/20260707/BASE_BRANCH_REMOVED_NOTES_20260707.md](../../20260707/BASE_BRANCH_REMOVED_NOTES_20260707.md).
