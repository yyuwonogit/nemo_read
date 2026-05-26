# Transport author handoff — 2026-05-21

Follow-up to the 2026-05-20 inject team handover at
`canonical_leap_inputs_remainder_patched_20260520.csv` +
`README_TRANSPORT_AUTHOR_FIXES.md` + `ca_2024_vs_fwd_2025_mismatches.csv`.

The structural authoring fixes recommended in your README §3 (renormalisation
mismatch hypothesis) plus four downstream issues are now resolved on the
authoring side. The interim `Remainder(100)` patches you applied can be
retired in the next inject pass and replaced with the regenerated CSVs in
this zip.

## What changed on our side

1. **Fuel-set alignment with the LEAP demand tree.** `VEHICLE_CONFIGS` in
   our orchestrator was carrying a narrower fuel set than LEAP exposes
   for Bus + Truck + Car. We folded HybridDiesel + NaturalGas + Gasoline +
   Hydrogen into each HDV class and added passive-carrier treatment so
   non-EV-policy fuels ride forward at their historical share rather
   than being absorbed by the dominant fuel via the `prepare_base_counts`
   residual-fold path. Closes the 13 share-discontinuity cells you
   flagged at 0.000000 pp drift across the 2024->2025 seam.

2. **Sales magnitude is now fully stock-flow-derived.** The orchestrator
   back-derives the entire cohort ledger (2005-2060) from the inverse
   stock-flow identity against the Gompertz / FE-OLS target stock. Our
   fuel_summary reported wholesales under-state the implied annual
   sales the stock trajectory requires by 30-40%, producing a 5x-90x
   sales spike at projection-start on the prior method. Net effect:
   sales_magnitude is smooth 2005-2060 end-to-end; 2W 2024->2025
   ratio now 1.00-1.40x across all AMS (was up to 75x).

3. **Silent-omission gap closed.** We now emit explicit zero rows for
   fuels in the LEAP demand tree that are absent from our source (e.g.
   IDN Bus Gasoline, IDN Truck Gasoline) AND for entire pre-cutoff
   year ranges (e.g. THA LDV Electric pre-2018, IDN HDV pre-2019).
   Without these rows, your canonical builder dropped the (vehicle x
   fuel x year) combinations and LEAP retained pre-existing template
   defaults — visible to the modelling author as "weirdly high"
   historical gasoline-Bus + gasoline-Truck stocks for Indonesia, and
   "empty years" in TH + VN LDV historical. Affected zero-fill sweep:
   Bus Gasoline for BRN / IDN / LAO / VNM; Truck Gasoline for BRN /
   IDN / KHM / LAO / VNM; LDV Electric pre-EV-open years for every AMS;
   plus a sweep of Bus / Truck Natural Gas / Hydrogen historical
   wherever source data is absent.

## Result: uniform data lengths

- Historical year span: 2005-2024 uniform across every (Country x
  vehicle) combination. MYS LDV uniquely extends back to 2000 because
  its source goes further; otherwise all AMS start at 2005.
- Projection year span: 2025-2060 uniform across every (Country x
  vehicle x fuel x scenario) cell.
- All (Country x vehicle x fuel x scenario x year) cells populated
  with explicit values. No NaN cells, no silently-omitted rows.

## What's in this zip

| File | Purpose |
|---|---|
| `sales_mix.csv` | Sales fuel-share by scenario, 20,500 rows. **V1** paste target for `Key\TransportDataStock\Vehicles_Sales_Share\<vehicle>\<fuel>` and `Demand\Transport\Road\<vehicle>\<fuel>\<fuel>`. |
| `sales_magnitude.csv` | Sales magnitude per (Country x vehicle x year), 2,245 rows. **V2** paste target for `Key\TransportDataStock\Vehicle_Sales\<vehicle>`. |
| `starting_year_sales.csv` | Base-year fuel-mix anchor at Year=2024, 160 rows. **V3** paste target. |
| `mileage_anchors.csv` | Per-AMS 2020 mileage anchors, 40 rows. **V4** paste target. Held flat 2005-2060. |
| `stock_by_fuel.csv` | Cross-check artefact only, NOT a paste target. LEAP derives stock from sales x survival internally; this is for your post-paste V-7 verification at 2030 / 2050. |
| `LEAP_action_items.md` | Updated paste plan with alias maps + known gaps + verification battery. Note the `Motorcyle` (LEAP typo) alias for 2W. |
| `HANDOFF_README_20260521.md` | This file. |

## Recommended re-inject sequence

1. Replace your interim `Remainder(100)` patches on the 13 cells with
   the regenerated `sales_mix.csv` rows. The dominant fuel now self-
   consistently tracks alongside the passive carriers at their real
   historical shares (e.g. IDN Bus 2025 BAS = HybridDiesel 91.13% +
   NaturalGas 6.67% + Electric 2.20% rather than HybridDiesel 97.80%
   + Electric 2.20%).

2. Apply the four V1-V4 pastes per `LEAP_action_items.md` §A. The
   Hydrogen variants (HydrogenFCV / Hydrogen FCEV) no longer appear as
   CSV values — single `Hydrogen` string everywhere on our side.

3. Re-run `check_ca_to_fwd_continuity.py` (the version from the
   2026-05-20 handover, in `Transport/Inject/`) against the new
   canonical built from these CSVs. Expectation: CLEAN.

4. Spot-check IDN Bus + IDN Truck Gasoline historical in LEAP after
   the paste. Expected: explicit zero stock 2005-2024, no pre-existing
   template default surviving.

## Deferred items (do not block inject)

- IDN LDV + VNM LDV 2005 Gompertz overshoots. Refits scoped for a
  Wave C follow-up cycle. Current values are usable; the overshoot is
  visible in stock_by_fuel.csv but does not affect the share-continuity
  or sales-magnitude smoothness you cared about.

- F1 (PPV CNG fuel economy 30 -> 26 MPGe) and F2 (ERIA 2022 Phase II
  citation cleanup) — in-place LEAP edits during your COM session per
  `LEAP_action_items.md` §B. Unchanged from prior handover.

## Commit reference

This handoff corresponds to commits `baae1501` (Lane A code fix +
regenerated CSVs) and `3b836bae` (Lane B investigations + paste plan
refresh) on branch `20260421_Transport_YY`, pushed 2026-05-21.
