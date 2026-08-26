# Residential AC + Fridge — High_eff patch rev 6 (2026-08-18)

Fixes the ACT tier-flip the last inject (your inject-ready 2026-08-14 file =
rev 3) produced: its Variable OM rate was flat across tiers, and since the
rate is charged on device OUTPUT — identical for all tiers by construction —
every tier paid the same electricity bill, the comparison collapsed to
capital cost, and the optimizer bought Low/Mid everywhere (High won 0/60
cells; the ACFRIDGE results). Rev 5 restores tier-true running costs and adds
the MEPS-2030 step: **by 2030 High_eff is the definitive unit to purchase.**

## THE INJECT: `higheff_patch_delta_r3_to_r5.csv` — 720 rows, nothing else

Verified row-by-row against your inject-ready file: these are the ONLY rows
whose values change. Everything else in the model is already correct — do
not re-paste anything beyond these.

| Variable | Scenario | Rows | Change |
|---|---|---|---|
| `Efficiency` | ASEAN Coordinated Transition, **High_eff leaves only** (2 appliances × 3 sizes × 10 AMS) | 60 | gradual ramp → **turnover STAIRCASE**: MEPS-2030 binds new sales, and the High-tier fleet average climbs in flat plateaus as the pre-2030 stock retires on our documented Weibull survival — fridge 49.31 → 55.44 (2030) / 70.27 (2035) / 87.85 (2040) / 97.89 (2045) / 100 (2050); AC 83.91 → 85.99 / 90.26 / 94.77 / 98.11 / 100. Piecewise-constant (plateau hold-points), no single-year fleet-wide jump, no retroactive upgrade of pre-2030 units |
| `Variable OM Cost` | ASEAN Coordinated Transition, all 18 leaves × 10 AMS | 180 | flat tariff rate → **tier-differentiated**: rate = tariff ÷ (tier Efficiency/100), USD/GJ of output. Low/Mid plain constants; High_eff a 4-point step to plain tariff at 2030. Per device-year this equals tariff × the tier's actual final kWh — restoring the per-device dollars of the pre-patch runs that correctly bought High_eff (e.g. IDN fridge Large 50.37/61.11/76.77 USD/yr), with honest magnitude and the 2030 step |
| `Exogenous Devices` | ASEAN Coordinated Transition, all 18 leaves × 10 AMS | 180 | v0.92 stored form `Interp(…) / 10^6`, AND the **fridge fleet re-based to the one-home-one-fridge law**: each country rescaled so exo 2024 = households × Percent Ownership exactly (Thailand ×0.6515, Viet Nam ×0.8348, Lao PDR ×1.4992, Brunei ×1.3417, Cambodia ×1.1743, …; ASEAN 2024 143.3 → 130.7 M). Weibull shape and size × tier mix preserved; the old country split inherited from a stale LEAP export violated the ownership inputs (THA 1.53 fridges/HH). AC unchanged (already 0.95–1.01 vs ownership; multiple ownership by design) |
| `Minimum Utilization` | ASEAN Coordinated Transition, the 12 leaves currently at 0 (AC Large/Medium, fridge Medium/Small) × 10 AMS | 120 | 0 → **100** (plain integer, Percent — the v0.92 stored form). One device serves one duty at full rated output: stops the optimizer idling cheap-sticker tiers (the last run held Low/Mid fridges at 2–40 % utilization, so device shares were dispatch shares, not market shares). Extends the 100 already pinned on AC Small + fridge Large to every leaf |
| `Unit Capacity` | ASEAN Coordinated Transition, all 18 leaves × 10 AMS | 180 | **restored to the v0.92 stored form**: `(re-anchored kW) * 10^6` — the LEAP-device basis your own area uses uniformly (exo `/ 10^6`, Capital Cost `* 10^6`, Unit Capacity `* 10^6` on all 180 real-country rows). The 2026-08-14 plain-kW strip left capacity 10⁶× off-basis against Capital Cost and exo — a mixed device basis under which capex swamps O&M and the min-sticker tier always wins. Values unchanged from the last inject (same re-anchored kW); only the basis coefficient is restored |

**Explicitly unchanged — skip (already correct in the model):** Efficiency in
CA/BAS/ATS (comparative gradual series), ACT Low/Mid Efficiency (same
constants you hold), Useful_EI keys, Capital Cost, Lifetime, Interest Rate,
Minimum/Maximum Share panels and the 60 Minimum Utilization rows already at 100 (AC Small, fridge Large).
The pairing law is untouched (Useful_EI anchor unchanged → capacity valid;
utilization stays exactly 100 %).

## Units & coefficient audit (per your 2026-08-14 rulings — checked, not assumed)

The delta contains **only scale-free variables**, so none of the unit/coef
adjustments made since the pre-patch state can bite it:

- `Efficiency` is a percentage — independent of device-unit size, energy
  unit, and the `10^6` device-conditioning coefficient.
- `Variable OM Cost` is USD per GJ **of energy** — also independent of the
  device-unit convention: whether "one device" is 1 or 10^6 actual units,
  rate × that device's output reproduces tariff × its final kWh identically
  (1000/3.6 × 0.0036 = 1 exactly; verified to 3e-7 against the analytic
  tables). All 240 expressions are final plain numbers / plain Interp — no
  scalers, no arithmetic idioms, values authored in the stored units.
- **Guiding principle: the v0.92 export defines every stored unit and
  coefficient convention.** Its ACT device panel is uniformly on the
  LEAP-device basis (1 LEAP device = 10^6 actual): `Exogenous Devices`
  `/ 10^6`, `Unit Capacity` `* 10^6`, `Capital Cost` `* 10^6` — verified on
  all 180 real-country rows of each. The delta conforms: Efficiency (%) and
  Variable OM (USD/GJ) are scale-free; Unit Capacity is authored verbatim in
  the v0.92 `* 10^6` form. Capital Cost is untouched
 ; Capital Cost stays in its v0.92 `* 10^6` form.

## Why steps, not ramps

Piecewise-constant coefficients for the LP: two clean regimes (pre-2030
market economics, post-2030 MEPS) with wide margins in both — no creeping
year-on-year crossovers, no near-degenerate bases. Narrative: harmonised
MEPS in force 2030 binds NEW SALES; the fleet average follows stock turnover
(no retroactive retrofit of installed units). Intertemporally High_eff wins
the purchase from 2030 (e.g. Indonesia fridge Large: $212 discounted lifetime
savings vs $156 capital premium at r = 9 %).

## What to expect on the rerun

Additions flip to High_eff from 2030: simulated with the v0.92 ACT capital
costs at r = 9 %, High is strictly cheapest in 22/30 fridge and 27/30 AC
country x size cells from 2030 (24/30 and 28/30 by 2060). Remaining cells
are the low-tariff ones (Brunei foremost; Lao PDR and Malaysia fridge
Medium/Small-class cells; Malaysia AC Small) where the O&M gap does not
repay the capital premium. Energy bends visibly at 2030.

## Package contents

| File | Role |
|---|---|
| `higheff_patch_delta_r3_to_r5.csv` | **THE INJECT** (720 rows) |
| `higheff_patch_canonical.csv` | full 1,500-row source-of-record (delta ⊂ this; do NOT paste in full — 1,260 rows are no-ops you already hold) |
| `ac_cost_patch.csv`, `fridge_cost_patch.csv` | wide analytic tables (kWh, tariffs, per-device costs) for verification |
| `ac_exo_device.csv`, `fridge_exo_device.csv` | exo reference (unchanged since 2026-07-15) |
| `apply_higheff_kwh_drift_method.txt` | method + full revision post-mortems (addenda 1–6 + correction) |
| `README_PATCH_20260813.md` | this guide |

Questions → residential modelling team. Builders:
`Residential/build_higheff_patch_paste.py` (canonical + step design),
delta derived by value-diff against your inject-ready 2026-08-14 file.
