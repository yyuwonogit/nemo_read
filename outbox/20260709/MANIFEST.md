# Outbox — 2026-07-09 (AEO-9 v0.71 cycle)

Team delivery packages built from the **v0.71** model run (batch-1 injected,
model solved). All results are v0.71; non-power inputs unchanged since v0.67.

Each per-team zip follows the 5-part shape:
`RESULTS · input/ · leap_structure/ · connected_drivers/ · full_results/ · READ_ME_FIRST`.

| Zip | For | Contents / results |
|---|---|---|
| `power_v071_postinject_20260709.zip` | Power | Post-inject confirmation + power results + the exact inject files + OPEN_ITEMS |
| `residential_v071_results_20260709.zip` | Residential | Demand-by-fuel + connected activity drivers (households/pop/GDP) + input + structure |
| `industry_v071_results_20260709.zip` | Industry | Industry demand by fuel (34,260 rows) + drivers + input + structure |
| `commercial_v071_results_20260709.zip` | Commercial | Commercial demand by fuel (6,840) + drivers + input + structure |
| `transport_v071_results_20260709.zip` | Transport | Transport + Int'l Transport demand (5,220) + drivers + input + structure |
| `fossil_v071_results_20260709.zip` | Fossil | Resources supply/exports — fossil fuels (7,860) + input + structure |
| `bioenergy_v071_results_20260709.zip` | Bioenergy | Resources supply/exports — crops+biofuels (3,840) + drivers + input + structure |
| `keys_v071_results_20260709.zip` | Keys | Key driver expressions (households/population/GDP) + structure |
| `aeo9_v0.71_results_for_teams_20260709.zip` | All teams | The tidy machine-readable result CSVs (supply power + demand by fuel) |

**Common `full_results/`** (in every per-team zip): demand for all sectors,
power generation/capacity, resources supply/exports — units stamped per row.

Provenance: `mailbox/20260709/v_0.71 {Power,Demand,Resources} Result.xlsx`.
Build pipeline: `result/20260709/_tidy_results.py` + `_package_teams.py`.
Adversarially verified (6-agent workflow): all complete, correct sector
mapping, 0 data defects.
