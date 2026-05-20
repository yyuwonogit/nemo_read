# Transport sector — author fixes needed (2026-05-20)

Handover from the inject cycle that pushed the transport canonical into
`aeo9_v0.47` (10 ASEAN AMS × 4 scenarios, 562 rows). The inject mechanism
itself is now working end-to-end (see `TRANSPORT_INJECT_SOP.md` in the
parent folder). This package documents a **data-quality issue in the
authored sales-share series** that the inject surfaced — it needs the
transport author's review.

---

## 1. The problem — sales-share discontinuity at the 2024→2025 boundary

For sales-share variables (`Key\TransportDataStock\Vehicles_Sales_Share\
<vehicle>\<fuel>`, variable `Activity Level`), the **last historical year
in Current Accounts (2024)** does not connect smoothly to the **first
projection year (2025)** in the forward scenarios (Baseline / AMS Target /
Regional Aspiration).

The share jumps discontinuously. Example — Myanmar Bus Blended Diesel:

| Year | Scenario | Share % |
|---|---|---|
| 2024 | Current Accounts | **68.87** |
| 2025 | Baseline / AMS Target / RAS | **98.56** |

A ~30-point jump in a single year, with no physical event to justify it.
The model would read this as the diesel share of new bus sales
near-instantly leaping from ~69% to ~99% in 2025.

## 2. Full list

See `ca_2024_vs_fwd_2025_mismatches.csv` (this folder). **13 unique
(AMS, branch, variable) combinations**, each appearing 3× (once per
forward scenario, all with the identical 2025 starting value):

| AMS | Vehicle\Fuel | CA 2024 | fwd 2025 | Jump |
|---|---|---|---|---|
| Myanmar | Bus\Blended Diesel | 68.87 | 98.56 | +30.1% |
| Myanmar | Truck\Blended Diesel | 69.99 | 100.00 | +30.0% |
| Vietnam | Bus\Blended Diesel | 70.00 | 100.00 | +30.0% |
| Thailand | Bus\Blended Diesel | 55.54 | 74.55 | +25.5% |
| Myanmar | PassengerCar\Gasoline | 40.05 | 49.99 | +19.9% |
| Cambodia | PassengerCar\Gasoline | 53.89 | 65.39 | +17.6% |
| Malaysia | Truck\Blended Diesel | 82.43 | 100.00 | +17.6% |
| Thailand | Truck\Blended Diesel | 88.78 | 100.00 | +11.2% |
| Indonesia | Bus\Blended Diesel | 91.13 | 97.80 | +6.8% |
| Cambodia | Motorcycle\Gasoline | 94.71 | 100.00 | +5.3% |
| Cambodia | Bus\Blended Diesel | 94.72 | 99.71 | +5.0% |
| Malaysia | Bus\Blended Diesel | 75.05 | 78.27 | +4.1% |
| Philippines | Truck\Blended Diesel | 98.80 | 100.00 | +1.2% |

## 3. Likely root cause (hypothesis — please confirm)

Direction is **always upward** (forward starts higher than CA ends), and
the affected fuels are always the *dominant* fuel for that vehicle (diesel
for bus/truck, gasoline for car/motorcycle). This is the signature of a
**renormalisation mismatch**:

- **Forward `sales_mix.csv`** appears renormalised so the modelled fuels
  sum to 100% — but across a *narrower* fuel set than history carried.
- **CA historical** carries raw shares including fuels that are absent /
  retired in the forward fuel set (e.g. a small LPG or CNG share that
  isn't modelled forward), so the dominant fuel's raw historical share is
  lower than its renormalised forward share.

When the minor historical fuels drop out, the dominant fuel "absorbs"
their share — but only starting in 2025, producing the step.

Please verify against the raw `sales_mix.csv` build inputs and
`build_unified_input.py` (the residue/sales-mix loader).

## 4. Interim fix already applied to the LEAP area

To keep the inject moving, the **39 forward-scenario rows** (the 13 combos
× BAS/ATS/RAS) were re-expressed as **`Remainder(100)`** instead of the
discontinuous `Interp(...)`. This makes the dominant fuel the residual of
100% after the *other* modelled fuel shares — so it self-consistently
tracks whatever the minor shares do, no hard-coded jump.

- CA (historical) rows were **left untouched** — they remain the raw
  historical Interp series.
- The patched canonical is
  `inject/transport/canonical_leap_inputs_remainder_patched_20260520.csv`.

**This is an interim modelling choice, not necessarily the right answer.**
The author should decide whether:
  (a) `Remainder(100)` is the correct long-run representation (dominant
      fuel = residual), OR
  (b) the forward `sales_mix.csv` should instead be re-authored so the
      2025 starting share equals the CA 2024 share and diverges smoothly
      from there.

## 5. How to re-check after fixing

Run the continuity checker against any updated canonical:

```
python check_ca_to_fwd_continuity.py
```

(Point it at the canonical path inside the script if you relocate it.)
A clean canonical reports `CLEAN: no discontinuities found`. Anything
> 1% relative jump between CA-2024 and forward-2025 is flagged.

## 6. Files in this package

| File | What it is |
|---|---|
| `README_TRANSPORT_AUTHOR_FIXES.md` | this file |
| `ca_2024_vs_fwd_2025_mismatches.csv` | full 39-row list of discontinuities |
| `check_ca_to_fwd_continuity.py` | re-runnable diagnostic script |
