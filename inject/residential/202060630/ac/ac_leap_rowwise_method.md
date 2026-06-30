# AC LEAP Input — row-by-row method

**Last updated: 2026-06-24.** Walks every row of the shared 14-row mapping
(same workbook as Fridge: `Residential/Fridge/Raw/refrigerator_leap_input_mapping.xlsx`)
as applied to air conditioners, and states how we treat it: formula, inject column,
scenario applicability, status. All values live in one file —
`ac_leap_inject.csv` (12,690 rows). Builder: `Residential/AC/build_ac_leap_inject.py`.
Companion: [`ac_leap_input_mapping.md`](ac_leap_input_mapping.md).

Shared constants: r = 9% (ADB social rate), lifetime **n = 15 yr** (AC), **CRF =
0.1241**, TOE = kWh/11630. Tariffs + discount rate are **shared** with Fridge.

> **AC vs Fridge.** Same structure, three differences: (1) lifetime 15 yr not 12;
> (2) **units per household** — AC owning-HH hold 1.2–3.4 units, so the parent
> Activity Level is `stock_per_hh` (Option A), not a plain ownership %; (3) Demand
> Cost / FEI are **per unit (device)**, not per household.

> **Two variants exist.** This describes the **frozen baseline** (`ac_leap_inject.csv`).
> A parallel **within-tier drift variant** (`ac_leap_inject_drift.csv`) changes
> row 4 (Efficiency ramps), row 6 (Useful EI re-anchored to the ultimate frontier),
> and row 3's O&M (drifted kWh); rows 1, 2, 5, 7–14 identical. See
> [`ac_leap_drift_method.md`](ac_leap_drift_method.md).

## Summary — the 14 workbook rows

| # | Scenario | Variable | Our treatment | Inject column | Status |
|---|----------|----------|---------------|---------------|--------|
| 1 | All | Activity Level | **Option A**: parent = units/HH (`stock_per_hh`); + size/leaf decomposition | `units_per_hh_parent`, `size_share_pct`, `eff_share_pct`, `leaf_units_per_hh` (+ `penetration_pct`, `intensity` for Option B) | ✅ filled |
| 2 | BAS, ATS | Demand Cost (USD/unit) | annualised capital only, CRF(9%,15) | `demand_cost_usd_per_unit` (=`annualized_capital_usd`) | ✅ filled |
| 3 | RAS | Demand Cost (USD/unit) | annualised capital + electricity O&M | `demand_cost_usd_per_unit` (= capital + `om_electricity_usd`) | ✅ filled |
| 4 | All | Efficiency (%) | `kwh(High_eff,size)/kwh(cell)` → High_eff = 100% | `efficiency_pct` | ✅ filled |
| 5 | All | Load Shape | LEAP default (flat); cooling daily/seasonal profile is a v2 refinement | — | ⬜ default |
| 6 | All | Useful Energy Intensity (TOE/unit) | per-size High_eff reference → TOE | `useful_energy_intensity_toe` | ✅ filled |
| 7–14 | RAS | optimisation/device vars (Max Availability, Unit Capacity, Max/Min Devices/Additions, Min Share, Min Utilization) | blank/unconstrained (same as Fridge) | — | ⬜ blank by design |

## Dimensionality — cross-AMS and other variation

`price_usd` and `kwh_unit` are **regionally pooled** (identical across all 10 AMS).
So only the activity terms and the RAS Demand Cost differ by country.

| Variable | Inject column | Across AMS | Across Year | Across Scenario | Across cell |
|---|---|---|---|---|---|
| Activity Level — parent (units/HH) | `units_per_hh_parent` | **Unique per AMS** | Yes (saturation + intensity grow) | No | No (parent) |
| Activity Level — size | `size_share_pct` | **Unique per AMS** | Yes | No | by Size |
| Activity Level — eff leaf | `eff_share_pct` | **Unique per AMS** | Yes | **Yes (lever)** | by cell |
| Demand Cost (BAS/ATS) | `demand_cost_usd_per_unit` | **Same for all AMS** (pooled price) | Yes (decay) | Yes | by cell |
| Demand Cost (RAS) | `demand_cost_usd_per_unit` | **Unique per AMS** (tariff in O&M) | Yes | RAS only | by cell |
| Efficiency | `efficiency_pct` | **Same for all AMS** | No (frozen) | No | 9 cells (7 unique) |
| Useful Energy Intensity | `useful_energy_intensity_toe` | **Same for all AMS** | No (frozen) | No | 3 (per size) |
| Load Shape / rows 7–14 | — | — | — | — | — |

**Paste implication:** Efficiency, Useful EI, and BAS/ATS Demand Cost can be entered
once and copied to every region; the units/HH activity (all three levels) and the
RAS Demand Cost go in per AMS.

## Per-row detail

**Row 1 — Activity Level.** AC owning-households hold multiple units, so the parent
driver is `units_per_hh_parent` = `stock_per_hh` = penetration% × intensity (units
per HH; e.g. SGP ≈2.8–3.0, IDN ≈0.5–1.1). Size and efficiency shares come from
`stock_pct` (installed base). `eff_share_pct` is the per-scenario lever. Reference
cols `penetration_pct` + `intensity` + `leaf_units_per_hh` support Option B.

**Row 2 — Demand Cost (BAS/ATS).** `price_usd × CRF`, CRF = 0.1241 (9%, 15 yr).
`price_usd` is already scenario/year premium-decayed in the source CSV (used directly).

**Row 3 — Demand Cost (RAS).** capital + `om_electricity_usd` (= shared tariff ×
`kwh_unit`). Because AC kWh is 3–5× a fridge's, the O&M term is large and the RAS
optimiser strongly favours efficient cells (RAS Low_eff Demand Cost > High_eff).

**Row 4 — Efficiency.** `kwh(High_eff,size)/kwh(cell)` → High_eff 100%; Small 81.9/64.5%,
Medium 75.0/51.1%, Large 72.3/52.9% (Mid/Low). Frozen (kwh frozen).

**Row 5 — Load Shape.** LEAP default. AC has a strong daily/seasonal cooling profile;
a real load shape is a worthwhile v2 refinement (more so than for fridge).

**Row 6 — Useful Energy Intensity.** per-size High_eff kWh → TOE (Small 0.06729,
Medium 0.09773, Large 0.16034), constant within a size. Final = Useful ÷ Efficiency.

**Rows 7–14 — RAS optimisation/device.** Blank/unconstrained; RAS driven by Demand
Cost alone (same decision as Fridge, user 2026-06-24). v2 lever if bounds wanted.
