# Residential Phase-2 — LEAP structure fix-list (2026-07-16)

**From:** LEAP inject team (we hold canon) · **To:** Residential subsector author

We validated every row of your drop against the canon we shipped you on
2026-07-04. Three of your files are **clean**; the AC/Fridge/Lighting files
were handed over as raw wide tables with the structure bindings we already
gave you left unresolved. **We are fixing all of it on our side for this
inject** — this list is so the next drop is authored against the structure
correctly, not re-guessed a third time.

## File status

| File | Status |
|---|---|
| `appliance_efficiency_paste.csv` | ✅ clean — inject as-is |
| `cooking_canonical_input.csv` | ✅ clean — inject as-is |
| `cooking_stove_characteristics.csv` | ✅ clean — inject as-is |
| `cooking_leap_inject.csv` | ⛔ superseded by `cooking_canonical_input.csv` — dropped |
| `ac_leap_inject.csv` (+ `ac_exo_device.csv`) | 🔧 wide → we map (ship frozen, not `_drift`) |
| `fridge_leap_inject.csv` (+ `fridge_exo_device.csv`) | 🔧 wide → we map |
| `lighting_tech_shares.csv` + `lighting_bulb_wattage.csv` | 🔧 wide → we map |
| `lighting_kwh_hh.csv` | ⛔ excluded — no canon target (Lamp/Tube tree doesn't exist) |

## Cross-cutting (all three wide files)

1. **No LEAP branch column.** They're analytical tables (Country × Year ×
   Scenario × Size × eff). LEAP inject needs long rows of
   `(branch_path, variable, ams, scenario, expression, unit)`. We pivot each
   load-bearing column onto its canon branch + variable and build one
   `Interp(year, value, …)` per (branch, variable, region, scenario).
2. **Region names.** `Brunei Darussalam → Brunei`, `Lao PDR → Laos`,
   `Viet Nam → Vietnam` (the other 7 already match). LEAP matches region
   names exactly; the long forms resolve to no branch.
3. **Scenario names.** `BAS → Baseline Simulation`, `ATS → AMS Target
   Scenario`, `RAS → Regional Aspiration Scenario`.
4. **Device-panel scoping (AC + Fridge only).** `Capital Cost`, `Unit
   Capacity`, `Exogenous Devices`, `Lifetime`, `Interest Rate` (and the rest
   of the optimizer panel) exist in only the 7 optimization scenarios — of
   your three, **only RAS hosts them.** Do not emit them in Baseline /
   AMS Target. (Lighting is exempt — its `Activity Level` + `Bulb Wattage`
   are all-scenario.)

## AC / Fridge — target structure and the specific errors

**Ownership / size / efficiency / useful-EI belong in the KEYS**, not raw on
the demand tree — the demand-tree Activity Levels already reference them:
- `Key\Residential\<Air Conditioning|Refrigeration>\Percent Ownership`
  — %-of-household saturation, injected **as-is** (LEAP /100): AC `282`
  = 282% = 2.82 units/HH; Fridge `87.9` = 87.9% = 0.879/HH. **No scaling.**
  (The live model's AC `2.82` is a pre-existing 100× error this corrects.)
- `…\Size_Share\<Large|Medium|Small>` ← `size_share_pct` (scenario-invariant).
- `…\Efficiency_Share\<Size>_<High|Mid|Low>` ← `eff_share_pct` (**per-scenario**;
  note the key uses `Large_High`, not `Large_High_eff`).
- `…\Useful_EI\<Size>` ← `useful_energy_intensity_toe` (TOE, per size).

Specific structure errors we corrected:
- **`Useful Energy Intensity` was placed on the leaf** — canon slot is the
  **size node** (`…\<Size>`), one value per size. Moved up.
- **`Uncalibrated Final Intensity`** was mapped onto the `_` device-stock
  leaves — that variable **only exists on the OLD trees**. Dropped from the
  paste.
- **`Final Energy Intensity` must not be pasted** in BAS/ATS/RAS — LEAP
  derives it (`= Useful EI ÷ Efficiency`); it's authored only in Current
  Accounts. Your `kwh_unit` is a diagnostic (and kWh, not the canon TOE).
- **RAS cost decomposed, not folded:** `Capital Cost = price_usd`,
  `Lifetime` (15 AC / 12 fridge), `Interest Rate` = `DiscountRate`; drop the
  folded `Demand Cost`/O&M in RAS. BAS/ATS get the simple `Demand Cost` only.
- **`Exogenous Devices` scale:** `device_thousand` is thousands → **×1000**
  to `Device`, RAS-only.
- **Fridge specifically:** you populated `Capital Cost` in BAS/ATS — that
  panel is RAS-only; we drop the BAS/ATS capital rows.
- **Branch prefix:** `Air Conditioning_` / `Refrigeration_` (trailing
  underscore). Never write the no-underscore trees.
- **Device ceilings** (`Maximum Devices` / `Maximum Device Additions`): left
  blank → LEAP default (unlimited). Intentional; not authored.

## Lighting

- Target `Demand\Residential\Projections\Lighting\Electricity\<Tech>`
  (Incandescent/CFL/Fluorescent/Halogen/LED — all 5 in canon).
- `share_percent` → per-tech `Activity Level [%]`; `watts` → `Bulb Wattage
  [Watts]`.
- **Do NOT author `Final Energy Intensity`** — it's a LEAP formula driven by
  the `Bulb Wattage` we author. `BulbsPerHH`/`LightingHours` stay at parent
  defaults.

---

## ⚠ CALC-BLOCKING (found + fixed after the inject) — mix shares must total 100 in EVERY scenario, Current Accounts included

The Phase-2 drop injected clean, but the calc then halted:

> Error: Activity shares under branch "Large" sum to 0.0%
> `Air Conditioning_\Large\High_eff` · Activity Level · Baseline Simulation · 2025 · Brunei

**Why.** Every Size split and every Efficiency split (and every cooking-fuel and
lighting-tech split) is a **% Share** group — the immediate siblings must total
100 in every scenario. The model guarantees that by leaving exactly **one member
as `Remainder(100)`** — an auto-fill that evaluates to "100 − the others." On the
AC/Fridge efficiency leaves that member was `Low_eff`.

Wiring each efficiency leaf to its `Efficiency_Share` key (so the mix is driven
from the Keys) removed that auto-fill. That is safe **only where the key carries a
real mix** — but the **AC `Efficiency_Share` keys were `0` in Current Accounts**
(you authored BAS / ATS / RAS, never Current Accounts). LEAP reads every
scenario's base year (2025) **from Current Accounts**, so all three tiers read 0
→ sum 0 → halt. It surfaces under "Baseline" because Baseline's base year is read
from Current Accounts. **Fridge was spared** — its Current-Accounts efficiency
keys already held real per-region values that total 100.

**Fixed in aeo9_v0.74** (`residential_sharefix_patch_20260716.csv`, 94 rows):
- **90 rows** — AC `Efficiency_Share` keys authored in **Current Accounts** = the
  Baseline reference mix (10 regions × 3 sizes × 3 tiers). Probe-confirmed:
  Current Accounts went **0 → 100** in every scenario. Fridge left untouched.
- **4 rows** — restored `Remainder(100)` on the three cooking cells that totalled
  **100.1** with no auto-fill member (Cambodia Clean → LPG, Vietnam Traditional →
  Wood, Malaysia Traditional → Kerosene).

**Standing rules for your next drop:**
1. **Current Accounts is a scenario.** Author the base-year mix there too — not
   only BAS / ATS / RAS. A mix left at 0 in Current Accounts halts the calc; `0`
   is not "unset / default", it is a hard stop.
2. **Keep exactly one `Remainder(100)` member per mix group.** It is the model's
   auto-balance. If instead you author every member explicitly, they must total
   **exactly 100 to the decimal** in every scenario — a 100.1 from rounding will
   halt LEAP. Prefer the Remainder.
3. Applies to every split: Size, Efficiency, cooking fuel (Clean + Traditional),
   lighting tech.

---

The re-mistakes here — asking us to build a tree we already gave you,
guessing the AC parent name, misplacing `Useful Energy Intensity`, mapping a
variable that only lives on the old tree — are all resolvable from the
2026-07-04 canon package. Author against that map next cycle and these stop
recurring. Questions → us; the structure is ours to hold.
