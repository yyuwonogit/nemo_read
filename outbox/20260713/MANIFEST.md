# Outbox — 2026-07-13 (engine hard-edit capture)

Two hard edits were made directly in the LEAP engine on 2026-07-09 (during
the v0.71 cycle). This drop captures them as deltas + routes the follow-ups.

| Zip | For | Contents |
|---|---|---|
| `power_existing_capacity_fix_20260713.zip` | Power | The 2 post-edit Existing Capacity cells (Diesel_MYPE 2021 / Biomass Other_MYSR 2023-24 zero-points removed, Malaysia CA) + note: carry forward, author real capacity or zero the HP. LEAP halts on EC=0 with HP!=0 (§11.2b). |
| `bioenergy_biomass_imports_task_20260713.zip` | Bioenergy | Record of the `Resources\Primary\Biomass:Maximum Imports = Max(5000000, Maximum Production[GJ])` Base-Template/RAS edit (Myanmar infeasibility fix) + TASK: unit-basis check (Tonne/1000 -> GJ change), run the full supply-adequacy sweep, regionalize the blanket. |

Repo-side in the same change: the two power cells applied to the baseline
canonicals (delta doctrine — baseline mirrors the area); §11.2b pre-flight
tripwire added (`find_zero_existing_capacity_conflicts`, sealed pre-flight +
CI tests) so the EC-zero-vs-HP class aborts before inject from now on.
