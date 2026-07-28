# Branch-name correction — `transport_delta_20260723.csv` (2026-07-23)

**160 of 291 rows** were rewritten:

```
Key\TransportDataStock\Vehicles_Sales_Share\{Bus,Motorcycle,PassengerCar,Truck}\Blended Gasoline
  ->  Key\TransportDataStock\Vehicles_Sales_Share\{Bus,Motorcycle,PassengerCar,Truck}\Gasoline
```

40 rows per vehicle class. Backup of the original:
`transport_delta_20260723.csv.bak_pre_gasoline_fix_20260723`.

## Why

**The two trees use different names for gasoline, and both are correct.**

| tree | node name |
|---|---|
| `Key\TransportDataStock\…` | **`Gasoline`** |
| `Demand\Transport\Road\<Veh>\` | **`Blended Gasoline`** |

Verified against the real `aeo9_v0.80` Keys export
(`LEAP structure/LEAP Input Keys.xlsx`, 2026-07-23): **all 10** gasoline nodes
in the Key tree are bare `Gasoline` — the 8 under
`{Vehicle_Stock_Share, Vehicles_Sales_Share}\{Bus, Motorcycle, PassengerCar,
Truck}`, plus `Key\Cal\Transport\Gasoline` and `Key\Cal\Industry\Gasoline`.
Zero `Blended Gasoline` nodes exist anywhere in `Key\`.

The v0.80 Transport export's own `Sales` / `Stock` expressions reference
`Key\…\Gasoline` (288 + 12 rows) and resolve correctly — **the area
calculates fine in v0.80**, which is the positive proof the split naming is
intentional rather than a half-finished rename.

`Blended Diesel` is spelled identically on both sides; only gasoline diverges.

The delta author applied the Demand-side name to Key-side paths. Under blind
mode (mandatory for `Key\` branches, §A.20) a non-existent FullName **hangs**
rather than erroring (§11.1), so this would have stalled the inject partway
through Brunei rather than failing cleanly.

## Process failure worth recording

This defect was caught on the first pre-flight, then **wrongly cleared**: the
Keys structure reference was patched from a verbal description of a rename
before the actual export existed, which made the broken rows validate. The
real export contradicted it.

**Rule (now in CLAUDE.md §2.6 and the anatomy version block): never patch
canon from a verbal note about structure — wait for the export.** The
freshness rule ("a file the user hands over is canon") applies to *files*, not
to descriptions of files.

## Verification after fix

- 0 remaining `Key\` rows containing `Blended Gasoline`
- Full pre-flight re-run against v0.80 Transport + real v0.80 Keys: all
  three transport payloads clean — every branch path, variable-on-branch and
  unit resolves; §A.15, §A.21/§A.23, §11.2b, §11.2e pass; 0 cross-payload
  collisions.

## Still outstanding → CLOSED 2026-07-23 (adapter)

The payloads were fixed above, but the *generator* of those payloads was not:
[../build_canonical.py](../build_canonical.py) still emitted `Blended Gasoline`
on the Key side, so re-running the adapter would have regenerated
`canonical_leap_inputs.csv` with 160 broken `Key\…\Blended Gasoline` rows.

Applied 2026-07-23 (backup `build_canonical.py.bak_pre_v080_gasoline_split_fix`):

- `FUEL_TYPE_MAP` → `FUEL_TYPE_MAP_KA` with `"Gasoline": "Gasoline"`, plus a
  derived `FUEL_TYPE_MAP_DEMAND` (`Blended Gasoline`) for future Demand-side
  families. Call sites in `_load_sales_mix` retargeted.
- `KA_SALES_SHARE_FUELS_PER_VEHICLE`: all four `Blended Gasoline` entries →
  `Gasoline`. `DEMAND_AVAILABLE_FUELS_PER_VEHICLE` deliberately untouched.

**These two edits are atomic.** Shipping the map fix without the availability
set makes the filter drop all 160 gasoline sales-share rows with a WARN and
write a silently short canonical.

The adapter was **not re-run** — the staged delta is hand-verified correct and
re-running would churn 880 rows for no gain (delta-payload doctrine, §4).

Suggested §A.17 tripwire (not yet written): scan `inject/transport/**/*.csv`
and assert no `branch` starting `Key\` contains `Blended Gasoline`, and no
`branch` starting `Demand\Transport\Road` contains a bare `\Gasoline\` segment.
