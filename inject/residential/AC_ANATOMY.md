# Air Conditioning (AC) — full anatomy: Demand tree + Key tree

> **CONFIRMED 2026-06-30.** Structure COM-probed against `aeo9_v0.64`
> ([`202060630/_probe_ac_structure.py`](202060630/_probe_ac_structure.py));
> parent/size reference wiring user-confirmed "wired like fridge". AC **mirrors
> the verified fridge structure** ([FRIDGE_ANATOMY.md](FRIDGE_ANATOMY.md)) — this
> doc records the AC specifics + the one place the live structure overrides the
> author's mapping (cost). Tags: **[seen]** probed directly · **[user-confirmed]**
> · **[inject-CSV]** from `ac_leap_inject.csv` / mapping docs · **[derived]** computed.
>
> Sources: [`ac_leap_input_mapping.md`](202060630/ac/ac_leap_input_mapping.md),
> [`ac/`](202060630/ac/) CSVs, [`LoadShape/`](202060630/ac/LoadShape/).

---

## 0. Model in one breath

Same **useful-energy + 2-layer (Size × Efficiency)** device-stock demand shape as
fridge, with deliberate departures: parent driver = **units per household**
(Option A `stock_per_hh`, can exceed 100%), lifetime **15 yr** (not 12), costs
**per unit (device)**, and a **real per-country cooling load shape** (fridge is flat).

```
TWO TREES  [seen]

Key\Residential\Air Conditioning\        ← DATA STORE (Activity Level = Interp)
   Percent Ownership, Size_Share\*, Efficiency_Share\*, Useful_EI\*

Demand\Residential\Projections\Air Conditioning_\<Size>\<Eff_eff>  ← references Key
   parent → units/HH ; size → size-share + useful-EI ; leaf → device tier
```

**AC parent = `Air Conditioning_`** (trailing underscore) [seen] — the **only**
AC inject target. (A legacy flat `Air Conditioning` sibling exists in the tree;
we never inject to it — ignore.) The **Key store exists** and is named
`Key\Residential\Air Conditioning` (no underscore), a 16-node mirror of fridge [seen].

Dimension split (verified against `ac_leap_inject.csv`):

| Quantity | Regional? | Scenario? | Time | Source |
|---|---|---|---|---|
| units per HH (parent) | regional | **invariant** | trajectory | [inject-CSV] |
| size share | regional | **invariant** (≤0.024 pp drift = renorm noise) | trajectory | [inject-CSV] |
| efficiency share | regional | **varies** (the only lever, ±3–4 pp BAS→RAS) | trajectory | [inject-CSV] |
| useful intensity | **global** | invariant | flat | [inject-CSV] |
| efficiency | **global** | invariant | flat | [inject-CSV] |
| unit capacity | **per country×size** ⚠ | RAS only | flat | [inject-CSV] |
| capital / variable-OM cost | global / regional (O&M tariff) | optimiser uses in RAS | trajectory | [inject-CSV] |
| exogenous devices | regional | invariant | series 2005–2060 | [inject-CSV] |

The only genuine per-scenario lever is the **efficiency-tier share**
(`eff_share_pct`). One real difference from fridge: AC **unit capacity is per
country×size** (FLEH differs by country) — fridge used one global value per size.

---

## 1. Demand tree — `Demand\Residential\Projections\Air Conditioning_`  [seen]

```
Air Conditioning_                   (parent / units-per-HH)
├── Large   → High_eff / Mid_eff / Low_eff   (device leaves; sizes are BTU/h bands, eff = CSPF bands)
├── Medium  → High_eff / Mid_eff / Low_eff
└── Small   → High_eff / Mid_eff / Low_eff
```
`High_eff` = most efficient = **lowest** kWh/unit.

### 1.1 Parent `Air Conditioning_` — [user-confirmed wired like fridge]

- **`Activity Level`** → references `Key\Residential\Air Conditioning\Percent Ownership[%]`.
  ⚠ The Key node is named **`Percent Ownership`** (reused from fridge) but the AC
  value is **units per HH** (`units_per_hh_parent` = penetration × intensity) and
  **may exceed 100%** (SGP ≈3.07 = "307%", VNM ≈1.79, IDN ≈1.51, KHM ≈0.31 @2050
  RAS — multiple ACs per household). So **AC ownership = units/HH authored into
  `Percent Ownership`**; "Percent" is just the scale label.
- `RefHH` = 1 (reference-household denominator) — confirmed on the leaf; LEAP-side
  reference var, not authored by us.

  (The `Air Conditioning_` parent variable enumeration blanked during probing;
  `RefHH` is confirmed on the **leaf**, and the parent→Key reference wiring is
  user-confirmed.)

### 1.2 Size node `…\<Size>` — [user-confirmed wired like fridge]

- **`Activity Level`** → `Key\…\Air Conditioning\Size_Share\<Size>[%]` (size share, Σ=100).
- **`Useful Energy Intensity`** → `Key\…\Air Conditioning\Useful_EI\<Size>:Activity Level[TOE]` (per size).
- `Load Shape` → per-country `<Country>_AC_Cooling` (CDD-derived 2-season × 24 h;
  **uploaded to LEAP separately, NOT in the inject**).

### 1.3 Device leaf `…\<Size>\<Eff_eff>` — device-stock leaf  [seen]

Full 35-var device-stock set (same family as fridge §1.3b). Authorable inputs:

| Variable | Fill (AC) | Units | Scenario |
|---|---|---|---|
| **Activity Level** | `eff_share_pct` (within-size eff mix; via Key Efficiency_Share / NEMO-optimized) | % | **per scenario** (lever) |
| **Efficiency** | `efficiency_pct` (High_eff=100%, Mid/Low <100%) | % | all (frozen) |
| **Exogenous Devices** | `ac_exo_device.csv` × 1000 | Device | **2005→2060 series**, RAS-only |
| **Unit Capacity** | `ac_cooling_unit_capacity.csv` = kwh_high(size) ÷ FLEH(country) | kW | **RAS-only**, per Country×Size |
| **Capital Cost** | `annualized_capital_usd` (= price × CRF(9%,15)) *or* `price_usd` (basis Q) | USD/unit | all |
| **Variable OM Cost** | `om_electricity_usd` (= tariff × kwh_unit) | USD/unit | all |
| `Fixed OM Cost` | `0` | USD/unit | all |
| `Lifetime` | `15` | Years | all |
| `Energy Load Shape` | named `<Country>_AC_Cooling` | | all — **separate upload** |
| Interest Rate / Min·Max Devices / Additions / Max Availability / Min Util / Min Share | RAS optimisation block — **blank/unconstrained** | | RAS |

Results (never written): Total Activity, Total Final Energy Consumption,
Final/Useful Energy Demand, Demand Coproduction, Demand Devices, Investment Costs,
Primary Energy Requirements, GWP×4, Gross Energy Consumption, Pollutant Loadings,
Social Costs, Power Load Shape.

> ⚠ **Cost correction — probe overrides the author's mapping.** The author's
> `ac_leap_input_mapping.md` routes cost to **`Demand Cost`**, but the live
> device-stock leaf has **NO `Demand Cost`** — it has `Capital Cost` +
> `Fixed OM Cost` + `Variable OM Cost` [seen]. So author **`Capital Cost` ←
> capital** and **`Variable OM Cost` ← O&M** (`Fixed OM` = 0); the device-stock
> optimiser combines them with Lifetime + Interest Rate in RAS. (Same trap fridge
> had — `Demand Cost` is the simple-leaf concept, not the device-stock leaf.)

---

## 2. Key tree — `Key\Residential\Air Conditioning`  [seen]

Exact 16-node mirror of fridge. Value on `Activity Level`, `Interp(...)`.

```
Key\Residential\Air Conditioning\
├── Percent Ownership                          (1)  ← units_per_hh_parent (units/HH; >100% allowed)
├── Size_Share\        Large | Medium | Small  (3)  ← size_share_pct
├── Efficiency_Share\  <Size>_<Eff> (FLAT, 9)  (9)  ← eff_share_pct (the per-scenario lever)
└── Useful_EI\         Large | Medium | Small  (3)  ← useful_energy_intensity_toe (TOE/unit)
```

The `Efficiency_Share` leaves seen: `Large_High/Large_Low/Large_Mid`,
`Medium_*`, `Small_*` (flat, short `High/Mid/Low`).

---

## 3. Cross-reference — Demand → Key  [seen + user-confirmed]

| Demand branch · variable | references Key node |
|---|---|
| `Air Conditioning_` · Activity Level | `Percent Ownership` |
| `Air Conditioning_\<Size>` · Activity Level | `Size_Share\<Size>` |
| `Air Conditioning_\<Size>` · Useful Energy Intensity | `Useful_EI\<Size>` (`:Activity Level`) |
| `Air Conditioning_\<Size>\<Eff_eff>` · Activity Level | `Efficiency_Share\<Size>_<Eff>` (NEMO may optimize in RAS) |

---

## 4. CSV column → slot (inject targets)  [inject-CSV]

Inject file: [`202060630/ac/ac_leap_inject.csv`](202060630/ac/ac_leap_inject.csv)
— 12,690 rows (10 AMS × 9 cells × 3 scn × 47 yr).

| CSV column | LEAP target | Units | Scenario | Match |
|---|---|---|---|---|
| `units_per_hh_parent` | Key `Percent Ownership` | Units/HH | all | ✅ |
| `size_share_pct` | Key `Size_Share\<Size>` | % | all | ✅ |
| `eff_share_pct` | Key `Efficiency_Share\<Size>_<Eff>` | % | per scenario | ✅ |
| `efficiency_pct` | leaf `Efficiency` | % | all | ✅ |
| `useful_energy_intensity_toe` | Key `Useful_EI\<Size>` | TOE/unit | all | ✅ |
| `unit_capacity_kw` | leaf `Unit Capacity` | kW | RAS only | ✅ |
| `ac_exo_device.csv` ×1000 (2005-2060) | leaf `Exogenous Devices` | Device | RAS | ✅ |
| `annualized_capital_usd` | leaf **`Capital Cost`** | USD/unit | all | ⚠ author said `Demand Cost` (absent) |
| `om_electricity_usd` | leaf **`Variable OM Cost`** | USD/unit | all | ⚠ author folded into `Demand Cost` |
| `<Country>_AC_Cooling` shapes | leaf `Energy Load Shape` | | all | ✅ separate upload |
| `penetration_pct`, `intensity`, `leaf_units_per_hh` | — (Option-B reference) | — | — | not injected |
| `kwh_unit`, `crf`, `tariff_usd_per_kwh`, `price_usd`, `demand_cost_usd_per_unit` | — | — | — | derived/intermediate |

`unit_capacity_kw` confirmed RAS-only (4,230 RAS rows populated; BAS+ATS blank).

---

## 5. Derived relationships (verified against inject)  [derived]

- `kwh_unit = useful_energy_intensity_toe × 11630 ÷ (efficiency_pct/100)` (1 TOE = 11630 kWh).
- `unit_capacity_kw(country,size) = kwh_high_eff(size) ÷ FLEH(country)` — per
  country×size, same across the 3 eff tiers, fixed over years. FLEH = full-load
  equivalent cooling hours from each country's shape (3,332 IDN → 4,610 THA).
  Check: Brunei Large = 1864.7 ÷ 3583.7 = 0.5203 kW; IDN Large = 1864.7 ÷ 3331.8 = 0.5597. ✓
- AC per-unit kWh (High_eff) Small 782.6 / Medium 1,136.6 / Large 1,864.7 — ~3–5×
  a fridge, so the RAS O&M term dominates lifecycle cost.
- **RAS cost penalises inefficient cells** (capital + O&M): IDN Small 2050 RAS
  High_eff 136.5 < Mid 141.5 < Low 166.6 USD/unit → optimiser favours High_eff;
  capital-only (BAS/ATS) has the opposite order, so the efficiency push is RAS-specific.

### Efficiency + Useful EI (per size)  [inject-CSV]

| Size | Useful EI (TOE/unit) | ← kWh (High_eff) | High_eff | Mid_eff | Low_eff |
|---|---|---|---|---|---|
| Small | 0.06729 | 782.6 | 100.0% | 81.9% | 64.5% |
| Medium | 0.09773 | 1,136.6 | 100.0% | 75.0% | 51.1% |
| Large | 0.16034 | 1,864.7 | 100.0% | 72.3% | 52.9% |

---

## 6. Constants — AC vs fridge

| Constant | AC | Fridge | Source |
|---|---|---|---|
| Lifetime | **15 yr** | 12 yr | IEA 2018 *Future of Cooling* / JICA 2020 |
| CRF (9%) | **0.1241** | 0.140 | r(1+r)ⁿ/((1+r)ⁿ−1) |
| Discount rate | 9% | 9% | ADB 2017 |
| TOE→kWh | 11630 | 11630 | IEA |
| Parent driver | **units/HH** (Option A) | ownership % | user decision 2026-06-24 |
| Cost basis | **per unit** | per HH | mapping |
| Cost slot (device-stock leaf) | **Capital Cost + Variable OM** | Capital Cost + Variable OM | probe 2026-06-30 |
| Load shape | **per-country `<Country>_AC_Cooling`** | flat | LoadShape build 2026-06-29 |
| Exo retirement | Weibull k=3, mean 15 yr | mean 12 yr | mapping |

---

## 7. Naming maps

| | CSV | Key tree | Demand tree |
|---|---|---|---|
| Size | `Small/Medium/Large` | `Large/Medium/Small` | `…\<Size>` (nested) |
| Efficiency | `High_eff/Mid_eff/Low_eff` | `High/Mid/Low` (flat `<Size>_<Eff>`) | `…\<Size>\<Eff_eff>` (keeps `_eff`) |
| Scenario | `BAS/ATS/RAS` | `Baseline Simulation` / `AMS Target Scenario` / `Regional Aspiration Scenario` | same |
| Country | `Brunei Darussalam`, `Lao PDR`, `Viet Nam`, … | `Brunei`, `Laos`, `Vietnam`, … | same |

---

## 8. Inject plan — DONE 2026-06-30 (mirrors fridge — reuse adapters, repointed)

- **Key drivers** (from `ac_leap_inject.csv`): `Percent Ownership` / `Size_Share` /
  `Efficiency_Share` / `Useful_EI` → `Key\Residential\Air Conditioning\…`.
- **Leaf** (`Air Conditioning_\<Size>\<Eff_eff>`): `Efficiency` (all scenarios) +
  `Exogenous Devices` (RAS, 2005-2060 from `ac_exo_device.csv`)
  [+ `Unit Capacity`, `Capital Cost`, `Variable OM Cost` for the cost/optimisation layer].
- **Load shapes:** upload the 10 `<Country>_AC_Cooling` named shapes to LEAP
  separately; the leaf `Energy Load Shape` then references them.
- Reuse `inject_fridge_leap.py` + adapters repointed to the AC paths/columns.

---

## 9. Provenance & verification status

| Element | How verified |
|---|---|
| Demand `Air Conditioning_` 2-layer subtree; flat `Air Conditioning` legacy | COM probe 2026-06-30 |
| Key tree `Key\Residential\Air Conditioning` (16 nodes) | COM probe 2026-06-30 |
| Device leaf 35-var device-stock set; cost = Capital + Var-OM (no Demand Cost) | COM probe 2026-06-30 (RAS) |
| Parent/size reference wiring (→ Key tree) | user-confirmed 2026-06-30 |
| Column values (Useful EI, Efficiency, FLEH unit-cap, exo, costs) | `ac_leap_input_mapping.md` + `ac/` CSVs |

**DONE 2026-06-30:** FULL AC inject into `aeo9_v0.64` — Key drivers + leaf
`Efficiency` (all scenarios) + RAS device-stock block (`Unit Capacity`,
`Capital Cost`=`price_usd`, `Variable OM Cost`, `Fixed OM Cost`=0, `Lifetime`=15,
`Exogenous Devices` 2005-2060). BAS 250 + ATS 250 + RAS 790 = **1290 writes,
30/30 EXACT, clean, user-confirmed**. Capital basis resolved = `price_usd` (LEAP
annualizes by Lifetime, per LEAP doc). Repeatable to a new area — see
[../LAST_SUCCESSFUL_INJECT.md](../LAST_SUCCESSFUL_INJECT.md).

**Still open:** AC `Energy Load Shape` upload (10 `<Country>_AC_Cooling` named
shapes — separate from the inject); electricity double-count check (if LEAP
prices electricity as a fuel separately, RAS shouldn't also charge it via
Variable OM). Option A (units/HH) is the injected choice.
