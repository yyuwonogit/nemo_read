# Refrigeration (fridge) — full anatomy: Demand tree + Key tree

> Complete dictionary of the residential **fridge** structure in LEAP area
> `aeo9_v0.64_w_result`. Built from direct UI inspection + COM probes
> 2026-06-24 → 2026-06-27. Marks **[seen]** (read directly) vs **[derived]**
> (from reference strings / CSV analysis). Companion to the cycle structure
> note [20260624/REFRIGERATION_STRUCTURE.md](20260624/REFRIGERATION_STRUCTURE.md)
> and the author contract
> [20260625/FRIDGE_AUTHOR_GUIDELINE.md](20260625/FRIDGE_AUTHOR_GUIDELINE.md).

---

## 0. Model in one breath

A LEAP **useful-energy + 2-layer (Size × Efficiency)** residential demand
structure. The numbers live in a **Key Assumptions store**; the **Demand
tree** references it and turns useful energy into final energy per device
tier.

```
TWO TREES

Key\Residential\Refrigeration\            ← DATA STORE (Activity Level = Interp)
   Percent Ownership, Size_Share\*, Efficiency_Share\*, Useful_EI\*

Demand\Residential\Projections\Refrigeration_\<Size>\<Eff_eff>   ← references Key
   parent → ownership ;  size → size-share + useful-EI ;  leaf → device tier
```

Dimension split (verified against `fridge_leap_inject.csv`):

| Quantity | Regional? | Scenario? | Time |
|---|---|---|---|
| ownership | regional | invariant | trajectory |
| size share | regional | **invariant** (≤0.02 pp drift = renorm noise) | trajectory |
| efficiency share | regional | **varies** (the lever) | trajectory |
| useful intensity | **global** | invariant | flat |
| efficiency, unit capacity, capital | **global** | invariant | flat/trajectory |

---

## 1. Demand tree — `Demand\Residential\Projections\Refrigeration_`

`Refrigeration_` (trailing underscore) is the **new** 2-layer tree. The old
flat `Refrigeration` (High/Medium/Low) is a separate **legacy** sibling —
leave it alone.

```
Refrigeration_                      (BT=1, parent / ownership)
├── Large                           (BT=1, size category)
│   ├── High_eff                    (BT=4, device technology leaf)
│   ├── Mid_eff
│   └── Low_eff
├── Medium  → High_eff / Mid_eff / Low_eff
└── Small   → High_eff / Mid_eff / Low_eff
```

### 1.1 Parent `Refrigeration_` — variables  [seen]

| Variable | Expression / value | Units | Role |
|---|---|---|---|
| Total Activity | `<Calculated>` | | result |
| **Activity Level** | `Key\Residential\Refrigeration\Percent Ownership[%]` | Percent | **input (reference)** — ownership rate |
| Total Final Energy Consumption | `<Calculated>` | | result |
| Demand Cost | `0` | 2020 USD per Household | input (placeholder) |
| RefHH | `1` | Ref/hh | input (reference HH = 1) |
| End Year Penetration | *(blank)* | % | unused |

### 1.2 Size node `…\<Size>` (Large/Medium/Small) — variables  [seen]

| Variable | Expression / value | Units | Role |
|---|---|---|---|
| Total Activity | `<Calculated>` | | result |
| **Activity Level** | `Key\Residential\Refrigeration\Size_Share\<Size>[%]` | Percent | **input (reference)** — size share |
| **Useful Energy Intensity** | `Key\Residential\Refrigeration\Useful_EI\<Size>:Activity Level[Tonnes of Oil Equivalent]` | TOE per Household | **input (reference)** — service demand |
| Optimize Devices | `Yes` | | setting |
| Total Final Energy Consumption | `<Calculated>` | | result |
| Load Shape | `ShapeFlat` *(inherited)* | Percent | input (default) |
| RefHH | `1` | Ref/hh | input |

### 1.3 Device leaf `…\<Size>\<Eff_eff>` (High_eff/Mid_eff/Low_eff)

⚠ **Two different leaf variable sets observed — they don't match.** The
**live** area `aeo9_v0.64_w_result` (COM-probed) has a *simpler* set; an
**earlier screenshot** showed a *device-stock* set (almost certainly a
different area version / demand method). The live set is what an inject here
must target.

#### 1.3a Live leaf — `aeo9_v0.64_w_result`  [seen — 22 variable names via COM]

| # | Variable | Role (input vs result) |
|---|---|---|
| 1 | Demand Cost | input (cost/HH) |
| 2 | Total Final Energy Consumption | result |
| 3 | Total Activity | result |
| 4 | **Efficiency** | **input** ← `efficiency_pct` |
| 5 | **Activity Level** | **input** ← efficiency-tier share (Data; was NEMO `?Optimized`) |
| 6 | RefHH | input (=1) |
| 7 | Final Energy Demand | result |
| 8 | Useful Energy Demand | result |
| 9 | Demand Coproduction | result |
| 10 | Primary Energy Requirements Allocated to Demands | result |
| 11 | Demand Devices | result (device count) |
| 12 | Investment Costs | result |
| 13 | Power Load Shape | input/inherited |
| 14 | Energy Load Shape | input/inherited |
| 15–20 | One/Twenty/Five-Hundred Year GWP (Direct/Indirect …) | result |
| 17 | Gross Energy Consumption | result |
| 21 | Pollutant Loadings | result |
| 22 | Social Costs | result |

Authorable inputs on the live leaf: **`Activity Level`** (eff-tier share),
**`Efficiency`**, **`Demand Cost`**. **No** `Unit Capacity` / `Capital Cost`
/ `Fixed OM Cost` / `Variable OM Cost` / `Lifetime` / `Exogenous Devices` /
`Maximum Devices` exist here.

#### 1.3b Earlier screenshot leaf — device-stock variant (NOT in the live area)  [seen]

| Variable | Expression (example, Large/High_eff) | Units |
|---|---|---|
| Activity Level | `Data(2025,100,…,2060,100) ?Optimized (NEMO/CPLEX)` | Percent |
| Efficiency | `Interp(2014,100,…)` | Percent |
| Lifetime | `12` | Years |
| Minimum Devices / Maximum Devices | `0` / `Unlimited` | Device |
| Minimum / Maximum Device Additions | `0` / `Unlimited` | Device |
| Exogenous Devices | `0` | Device |
| Unit Capacity | `Interp(2014,0.056929224,…)` | kW |
| Minimum Share | `0` | Percent |
| Maximum Availability / Minimum Utilization | `100` / `0` | |
| Capital Cost | `Interp(2014,280.446452338,…)` | USD/… |
| Fixed OM Cost | `Interp(2014,50.4697,…)` | USD/… |
| Variable OM Cost | `0` | USD/… |
| Interest Rate | `DiscountRate` | Percent |
| RefHH | `1` | Ref/hh |

> The 2026-06-25 inject's `Fixed OM Cost = 0` correction (to overwrite the
> author's mis-entry — the ~50.47 belongs in Variable OM) **could not be
> applied** in `aeo9_v0.64_w_result` because the variable is absent there.
> Resolve which area/version actually carries the device-stock leaves.

---

## 2. Key tree — `Key\Residential\Refrigeration`  [seen]

Every node stores its value on the **`Activity Level`** variable as
`Interp(year, value, …)`. **16 nodes per region.**

```
Key\Residential\Refrigeration\
├── Percent Ownership                                   (1)
├── Size_Share\        Large | Medium | Small           (3)
├── Efficiency_Share\  <Size>_<Eff>  (FLAT, 9 nodes)    (9)
│      Large_Low  Large_Mid  Large_High
│      Medium_Low Medium_Mid Medium_High
│      Small_Low  Small_Mid  Small_High
└── Useful_EI\        Large | Medium | Small            (3)
```

### 2.1 `Percent Ownership`

- Fill: `ownership_parent_pct` · Units: % · **regional, scenario-invariant** · trajectory.
- Example (Indonesia): `Interp(2014, 97.39, …, 2022, 97.59, 2023, 89.0, …, 2025, 89.2, 2030, 90.35, 2040, 92.71, 2050, 95.53, 2060, 98.36)`.
- ⚠ Source CSV has a ~97.6→89.0 step at 2022→2023 (historical/projection seam — confirm intended).

### 2.2 `Size_Share\<Size>`

- Fill: `size_share_pct` · Units: % · **regional, scenario-invariant** (BAS≈ATS≈RAS to ≤0.02 pp — renorm noise, not a lever; verified 2026-06-30 across all 20260624/25/29/30 inject drops) · **Σ = 100 across the 3 sizes**.
- Example (one region, 2005-extrapolated): Large 5.3, Medium 3.1, Small 91.6.
- Households shift Small→Larger over time.

### 2.3 `Efficiency_Share\<Size>_<Eff>` (flat, 9 nodes)

- Fill: `eff_share_pct` · Units: % · **regional, scenario-tagged (the lever)** · **Σ = 100 within each size**.
- Naming: short eff token `High/Mid/Low`, joined `<Size>_<Eff>` (e.g. `Large_High`).
- Example (RAS, ~2005): Large 17.2/32.6/49.4, Medium 17.4/32.6/50.0, Small 56.6/11.6/31.8 (Low/Mid/High). Large skews High-eff; Small skews Low-eff.

### 2.4 `Useful_EI\<Size>`

- Fill: `useful_energy_intensity_toe` · Units: **Tonnes of Oil Equivalent** (per HH) · **global, scenario-invariant, flat in time**.
- Values (all 10 AMS identical): Large `0.0428804815133276`, Medium `0.0391143594153052`, Small `0.0262424763542562`.

---

## 3. Cross-reference — Demand → Key

| Demand branch · variable | references Key node |
|---|---|
| `Refrigeration_` · Activity Level | `Percent Ownership` |
| `Refrigeration_\<Size>` · Activity Level | `Size_Share\<Size>` |
| `Refrigeration_\<Size>` · Useful Energy Intensity | `Useful_EI\<Size>` (`:Activity Level`) |
| `Refrigeration_\<Size>\<Eff_eff>` · Activity Level | efficiency-tier share (← `Efficiency_Share\<Size>_<Eff>` exogenously; the leaf value can be NEMO-optimized) |

---

## 4. CSV column → slot (inject targets)

| CSV column | Target | Units | Status |
|---|---|---|---|
| `ownership_parent_pct` | Key `Percent Ownership` | % | **injected** (2026-06-25) |
| `size_share_pct` | Key `Size_Share\<Size>` | % | **injected** |
| `eff_share_pct` | Key `Efficiency_Share\<Size>_<Eff>` | % | **injected** |
| `useful_energy_intensity_toe` | Key `Useful_EI\<Size>` | TOE/HH | **injected** |
| `efficiency_pct` | leaf `Efficiency` | % | Phase 2 (exists on live leaf) |
| `unit_capacity_kw` (Large 0.056929224 / Med 0.051929224 / Small 0.034840183) | leaf `Unit Capacity` | kW | Phase 2 — **var absent in live area** |
| `device_thousand` (2025 only) | leaf `Exogenous Devices` | Device (×1000?) | Phase 2 — **var absent in live area** |
| `price_usd` / `annualized_capital_usd` | leaf `Capital Cost` or `Demand Cost` | USD | Phase 2 — basis Q |
| *(≈50.47, not a column)* | leaf `Variable OM Cost` | USD | Phase 2 — needs column |
| *(LEAP=12, not a column)* | leaf `Lifetime` | Years | Phase 2 — needs column |
| `leaf_ownership_pct`, `kwh_unit`, `crf`, `tariff_usd_per_kwh`, `om_electricity_usd`, `demand_cost_usd_per_hh` | — | — | informational / derived |

---

## 5. Derived relationships (verified)

- `kwh_unit = useful_energy_intensity_toe × 11630 ÷ (efficiency_pct / 100)`  (1 TOE = 11630 kWh).
- `unit_capacity_kw` = that size's **High_eff** `kwh_unit ÷ 8760` — per-size rated capacity (same for all 3 eff tiers); the tier's extra final energy comes from `Efficiency`.
- Useful service is constant per size; efficiency tier sets final-energy draw.

---

## 6. Naming maps

| | CSV | Key tree | Demand tree |
|---|---|---|---|
| Size | `Small/Medium/Large` | `Large/Medium/Small` | `…\<Size>` (nested) |
| Efficiency | `High_eff/Mid_eff/Low_eff` | `High/Mid/Low` (in flat `<Size>_<Eff>`) | `…\<Size>\<Eff_eff>` (nested, keeps `_eff`) |
| Scenario | `BAS/ATS/RAS` | `Baseline Simulation` / `AMS Target Scenario` / `Regional Aspiration Scenario` | same |
| Country | `Brunei Darussalam`, `Lao PDR`, `Viet Nam`, … | `Brunei`, `Laos`, `Vietnam`, … | same |

CSV eff → Key suffix: `High_eff→High`, `Mid_eff→Mid`, `Low_eff→Low`.

---

## 7. Provenance & verification status

| Element | How verified |
|---|---|
| Tree shapes (Demand + Key, 16 Key nodes) | LEAP UI screenshots, 2026-06-24/25 |
| Parent / size variable lists + references | UI screenshots |
| Key node values (ownership / size / eff / useful) | UI screenshots + `fridge_leap_inject.csv` analysis |
| Live leaf 22-variable set | COM probe of `Refrigeration_\Large\High_eff`, 2026-06-25 |
| Dimension split, derived relationships | data analysis over `fridge_leap_inject.csv` |
| Key paths + scenario names resolve | inject dry-run (160 rows × 3 scenarios clean), 2026-06-25 |
| Inject landed | 480 writes, 10/10 readbacks EXACT per scenario, user-confirmed |

**Not yet verified:** live-leaf input *expressions/values* (only names probed —
do not read `.Expression` on the result-side vars; they fire the LEAP modal);
the device-stock leaf area/version; AC (Air Conditioning) entirely.
