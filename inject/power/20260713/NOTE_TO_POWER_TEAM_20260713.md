# Power team — Existing Capacity zero-point fix (2026-07-13)

## What was changed in the model (hard edit in the engine, 2026-07-09)

In **Malaysia, Current Accounts**:
- `…\Processes\Diesel_MYPE : Existing Capacity` — removed the `2021, 0` point.
- `…\Processes\Biomass Other_MYSR : Existing Capacity` — removed the
  `2023, 0` and `2024, 0` points.

`existing_capacity_zero_fix_delta.csv` in this package is the exact post-edit
state of those two cells — **carry these forward**: your canonical's CA series
for these two branches must not re-introduce the zero points, or the next
inject reverts the fix and the calc breaks again.

## Why LEAP failed on them

Those branches have **non-zero Historical Production in the same years**
(Diesel_MYPE generated ~156 GWh in 2021; Biomass Other_MYSR ~85-90 GWh-scale
in 2023-24). LEAP refuses "output is non-zero but zero capacity is available"
— a plant cannot have produced electricity in a year its capacity is zero.
The zero points came from the capacity series; deleting them lets LEAP
interpolate across the gap (e.g. Diesel_MYPE 2020: 60.1 → 2022: 35.23).

## The better fix (yours to author, next revision)

Deleting the zeros is a patch, not data. For those years either:
- author the **real** installed capacity (the fleet clearly existed — it was
  generating), or
- if the capacity truly was retired, zero the **Historical Production** for
  those years instead (both can't be true at once).

## Guardrail added on our side

This class is now caught **before injection**: our pre-flight scans every
payload for `Existing Capacity = 0` in a year where the same branch's
`Historical Production` is non-zero, and refuses to inject it. So a future
payload with this pattern bounces back to you immediately with the exact
branch/year, instead of dying mid-calculation. (The same check found this
identical MYSR 2023/24 conflict already present in the May-07 archive
payloads — it's been latent since then.)
