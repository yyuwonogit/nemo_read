# Residential Phase-2 — answers to your open questions (2026-07-16)

**From:** LEAP inject team (canon authority) · **To:** Residential subsector author
**Re:** `residential_leap_inject_20260715` · **Target area:** aeo9_v0.73

We hold the truth of the LEAP structure — branch paths, variables, units,
scenarios. We handed you that structure on **2026-07-04**
(`residential_canon_handover_20260704.zip`: the full tree, the
1,276-row branch×variable×units map, and the README that lists all 15 end
uses). Every question below is already answered by that canon; several are
re-asks of things we shipped you. **None of them require you to re-provide
data** — we resolve all of them on our side. Read this so the next drop stops
repeating the same structure mistakes.

---

## Your questions → the canon answers

**Q. "Confirm the AC parent branch name — `Air Conditioning`? `Cooling`?"**
`Demand\Residential\Projections\Air Conditioning_` — **with the trailing
underscore.** Not "Cooling", not the bare "Air Conditioning" (that's the OLD
share-based calibration tree, which stays ON and untouched). Fridge is
`Refrigeration_`.

**Q. "Build the 2-layer Size×Efficiency tree (structural-create on the LEAP side)."**
**No create — it already exists.** `Air Conditioning_\<Size>\<eff>` and
`Refrigeration_\<Size>\<eff>` (Size∈{Large,Medium,Small}, eff∈{High_eff,
Mid_eff,Low_eff}) are already in canon with the full device-stock panel. Your
`structure_request_AC_fridge_2layer` is stale — the tree you asked us to build
was built. It was in the package we sent you.

**Q. "Does the parent accept a units-per-HH activity > 100%? How is ownership handled?"**
Ownership lives in the **Keys**, not the demand tree:
`Key\Residential\Air Conditioning\Percent Ownership` (and `…\Refrigeration\…`).
Ownership is a **% of household saturation** (LEAP divides by 100), and your
values are **correct as authored — inject as-is, no scaling**:
- **AC** = `282` → 282% → **2.82 AC per household** (multi-unit; values > 100%
  are normal for AC). Your per-unit cost/intensity is correct.
- **Fridge** = `87.9` → 87.9% → 0.879 fridge/household.
Per-**device** service intensity sits on the size node (`Useful_EI\<Size>`,
TOE per device); LEAP computes `Households × saturation × size-share ×
eff-share × per-device intensity`. **Note:** the live model currently holds
AC ownership at `2.82` (= 2.82%, i.e. ~3 homes per 100 with AC) — a
pre-existing 100× error; this inject **corrects** it to `282`.

**Q. "Replace the GDP `Lookup` ownership with explicit per-AMS values, or keep the formula?"**
Explicit values, routed to `Key\Residential\<appliance>\Percent Ownership` —
they cleanly overwrite the Lookup. We do the routing.

**Q. "Electricity double-count — if LEAP prices electricity as a fuel, RAS `Demand Cost` capital-only?"**
Yes — **capital-only.** LEAP costs the electricity fuel on the supply side;
putting electricity O&M into demand-side cost double-counts. We drop
`om_electricity_usd`. In RAS the cost is authored as the **decomposed
primitives** (`Capital Cost` + `Lifetime` + `Interest Rate`), not a folded
`Demand Cost` — LEAP annualizes internally.

**Q. "AC activity-vs-stock calc-path; frozen vs drift?"**
**Frozen.** Efficiency improvement is the leaf-share shift toward High_eff with
`Useful_EI` held constant — that matches canon. (Ship the frozen file: the
drift file has a broken `Useful_EI` = 0.066 on Large, and useful energy must
not drift.)

**Q. "Cooking base-year calibration via an activity/demand-level Cal, not the stove-efficiency term."**
The base-year calibration is **not yours or ours to re-invent.** It already
lives on `Key\Cal\Residential\<fuel>` (per-fuel factors: Electricity, LPG,
Wood, Charcoal, …) and stays exactly as-is; your pure-physics stove
`Efficiency` sits on top of it. **Do not author a new base-year Cal scheme.**
Keep the prior appliances' convention.

---

## Two things to confirm (not blockers, no re-provide)

1. **Fridge variant** — we're shipping the frozen `fridge_leap_inject.csv`.
   Confirm that's canonical (not `_drift`).
2. **Deferrals** — we're **excluding** `lighting_kwh_hh.csv` (its Lamp/Tube
   efficiency tree does not exist in canon; it's a diagnostic, not an inject
   target) and leaving the Lighting `Other` arm + `BulbsPerHH`/`LightingHours`
   at LEAP default this pass. Confirm that's intended.

Everything else — branch paths, Keys routing, unit conversions, scenario/region
strings, cost decomposition — **we fix.** The corrections are in
`MD2_FIXLIST_residential_structure_20260716.md`.
