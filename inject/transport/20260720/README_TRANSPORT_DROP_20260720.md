# Transport → LEAP inject team — data drop, 2026-07-20

Reply to your **Canonical Structure Handover** of 2026-07-04
(`transport_canon_handover_20260704.zip`). This drop contains the
refreshed source CSVs plus our adjudication of every item in your
transport anomaly audit.

## 1. What's in this zip

| File | Role | Notes |
|---|---|---|
| `ANOMALY_AUDIT_RESPONSE_20260716.md` | **Our reply to your anomaly audit** | All 20 items (Part A A1-A14 + Part B B1-B6) adjudicated, plus direct answers to README §7.1-§7.8 |
| `LEAP_action_items.md` | **Paste plan / authoring guide** | Master table (V1-V6, F1-F3, X1), alias maps, per-paste detail, verification battery, and §F = the inject-side dispositions checklist from the audit |
| `sales_mix.csv` | **V1** sales fuel-share by scenario | → `Key\TransportDataStock\Vehicles_Sales_Share\<Vehicle>\<Fuel>` (Activity Level) |
| `sales_magnitude.csv` | **V2** sales magnitude per vehicle class | → `Key\TransportDataStock\Vehicle_Sales\<Vehicle>` (Activity Level) |
| `starting_year_sales.csv` | **V3** base-year fuel mix **+ V5 base-year stock** | now carries the new `stock_count` column — see §2 |
| `mileage_anchors.csv` | **V4** per-AMS mileage anchors | → `Demand\...\<Vehicle>\<Fuel>\<Fuel>:Mileage`, flat 2005-2060 |
| `survival_profile.csv` | **V6 (new)** per-class survival curve | handoff aid for your scrappage panel — see §2 |
| `stock_by_fuel.csv` | **X1** stock fuel-share | cross-check reference only, **NOT a paste target** (you derive stock) |

## 2. What's new since the last drop

- **`stock_count` added to `starting_year_sales.csv`** — answers README §7.6 /
  SPEC §4b. The 2024 **fleet stock** per (Country, vehicle_type), aggregated
  across fuels. This replaces the sales-sum that made `BaseYear_StockData`
  30-100× too small. **It is a per-vehicle value repeated across that
  vehicle's fuel rows — take it once per (ams, vehicle); do NOT sum.**
  Sanity: BRN Bus 2,188 vs the 2,300 you hold; CAM Bus 65,996 vs 69,600;
  IDN Bus 298,260 vs 273,800.
- **`survival_profile.csv` (new)** — per-class Weibull survival curve
  (LDV λ=15.5 k=3.0, 2W λ=12.0 k=2.5, Bus/Truck λ=18.0 k=3.5; mean lives
  13.8 / 10.6 / 16.2 yr), ages 0-40. Addresses audit **B2**: your Scrappage
  panel is boilerplate (Scrappage 0 / Max Frac 100), so fleets never retire.
  Translate `surviving_fraction` into your survival/scrappage input.
- **F3 — Truck Natural Gas Fuel Economy: set 5 MPGe fleet-wide.** This
  answers README §7.1 and **inverts its framing**: 5 is correct, the
  fleet-wide 12 is the defect (12 MPGe = 628 MJ/100 km equals your
  Truck *Hydrogen* value and is implausible for CNG, which is less
  efficient than diesel at 7 MPGe). Apply 5 across all regions **and**
  Current Accounts — do not revert Indonesia to 12.

## 3. Please re-paste V1 and V2 (not just Cambodia)

The sales were re-derived this cycle, so **the historical (2005-2024)
shape of `sales_mix.csv` and `sales_magnitude.csv` changed for every
AMS**, not only the cells noted below. Two reasons:

1. **Historical smoothing.** Our stock paths are now monotone-smoothed
   over 2005-2024, which removed single-year jumps/dips that the
   stock-flow identity was passing into the derived sales. Audit result:
   sales single-year anomalies **82 → 21** (AMS-total now **0**), stock
   **0** at both total and per-vehicle level. The 2024 anchors and the
   2024→2025 seam are unchanged.
2. **Cambodia LDV base-stock re-anchor** (see §4).

Scenario invariance still holds exactly (total stock and total sales are
identical across BAS/ATS/RAS to machine precision; only the fuel mix
differs), and BAS ≥ ATS ≥ RAS holds for ICE stock and sales.

## 4. Cambodia LDV base stock re-anchored 92k → 697k

Our starting-stock exam found KHM LDV at only **1.7× its annual sales**
(peers run 10-29×). A socio-economic cross-check confirmed it: KHM at
**5.4 LDV/1000** sat *below* poorer, crisis-hit Myanmar (10.5) and far
below the next income tier (Laos 23.6). MPWT reports **7,563,395 vehicles
registered since 1990** (~13% cars) ⇒ **~500-900k passenger cars**. Root
cause: the ASEAN-Stat passenger-car panel misses Cambodia's large
used-import fleet.

Re-anchored to **697,112 (40.7/1000, stock/sales 12.7×)**. KHM LDV **sales
are unchanged at 54,692** (still the published MPWT 2024 registrations).
Treat the level as a documented data judgment — the published fleet is
fuzzy within ~500-900k.

## 5. Known caveats shipping with this drop

- **Road tailpipe emissions (audit B1, 🔴) are out of scope for this
  track** — being handled outside this pipeline. No emission-factor set
  ships from us. (Our recommendation, for the record, was IPCC 2006
  Tier 1 **fuel-based** factors via LEAP's TED, per-fuel and
  region-uniform, biofuel fractions biogenic-zero.)
- **21 residual single-year sales moves** remain, all accepted: sub-1k
  micro-fleets (BRN 2W 167/yr, BRN Truck 388/yr — swings of tens of
  vehicles) and the MMR Truck 2028/29 post-crisis projection kink.
- **Soft base-year anchors** (documented, not blockers): LAO LDV,
  BRN LDV (medium confidence), SGP 2W (unanchored by a guard),
  SGP Truck (Tier-C placeholder series).
- **Your adapter still maps `Gasoline`** — per your own
  `CSV_AUTHORING_GUIDE §3`, `LEAP_AVAILABLE_FUELS_PER_VEHICLE` must be
  renamed to `Blended Gasoline` before the next Demand-tree push, or
  blind-mode writes will target a FullName that no longer exists. Our
  CSVs use neutral source tokens, so we're insulated either way.
- **Confirm the target area** — you report the live area is now
  `aeo9_v0.67_w_results`; the inject SOP's `EXPECT_AREA` is stale at
  `aeo9_v0.46`.

## 6. Everything else from your audit

`ANOMALY_AUDIT_RESPONSE_20260716.md` has the per-item verdicts. Headline:
**no change was warranted in our four source CSVs** — every Part-A data
defect traced to a stale live-model paste or an inject-side LEAP
formula/plumbing artifact. The actions that fall to your side are
collected as a checklist in `LEAP_action_items.md §F` (re-point the
Truck-NG Sales formula, re-derive CA Stock rather than paste, revert the
BRN mileage-correction and PHL aviation FEI, harmonise PassengerCar
First Sales Year, strip the IW CR artifacts, fix the SAF provenance +
CO₂ basis).

Questions → yudiandra.y@gmail.com
