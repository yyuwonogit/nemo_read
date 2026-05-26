# AC + Refrigeration — 2-layer structure request to the LEAP team

> **Outgoing request** (inverse of the 2026-05-20 handovers). Drafted
> 2026-05-21. The 2026-05-20 `REFRIGERATION_TEAM_HANDOVER` captured a
> **flat 3-tier** Refrigeration tree (`High / Medium / Low`, one level)
> whose segmentation the handover itself flagged as unresolved (its §5
> q1). Our AC + Fridge models are **2-layer** (Size × Efficiency, 9
> cells). Per the modelling-team decision (Option A, 2026-05-21) we are
> **keeping the 2-layer design** and asking the LEAP team to build the
> nested structure so our existing inject lands 1:1 with no information
> loss. New AC + Fridge handovers will be re-issued after the structure
> is updated; CSV reshaping waits for those.

---

## 1. Target tree (build this for BOTH appliances)

```
Demand\Residential\Projections\Refrigeration            (BT=1  parent)
├── Small                                                (BT=1  size category)
│   ├── Low                                              (BT=4  efficiency leaf)
│   ├── Medium                                           (BT=4)
│   └── High                                             (BT=4)
├── Medium                                               (BT=1  size category)
│   ├── Low / Medium / High                              (BT=4)
└── Large                                                (BT=1  size category)
    └── Low / Medium / High                              (BT=4)
```

- **9 efficiency leaves per appliance** (3 sizes × 3 efficiency tiers).
- Same shape for AC under its parent — **please confirm the AC parent
  branch name** (`…\Projections\Air Conditioning`? `…\Cooling`?); the
  variable mapping below is identical.
- This is a **structural-create on the LEAP side** (new size category
  level + efficiency leaves). The flat `High/Medium/Low` legacy tier set
  is an AEO-8-era placeholder and can be replaced by this nesting.

### Naming polarity — important

The inner tier is **efficiency**, so `High` = **most efficient = LOWEST
kWh/HH** (opposite polarity to a size-based "High = biggest"). To avoid
confusion with the size layer, we recommend labelling the leaves
`High_eff / Mid_eff / Low_eff` (or `Efficient / Standard / Basic`). The
size categories are `Small / Medium / Large`.

---

## 2. Variables per level — mapped to our existing CSV columns

Our data already exists in `Residential/LEAP Input/{ac,fridge}_sales_projection.csv`
(9 cells × 10 AMS × 47 yr × 3 scenarios). Mapping:

| LEAP level | LEAP variable | Unit | Our source column | Notes |
|---|---|---|---|---|
| **Parent** (`Refrigeration` / AC) | `Activity Level` | % | Fridge `total_ownership_pct`; AC `penetration_pct` | Ownership rate per HH. Per AMS, per year. **Scenario-invariant** (verified). Replaces the GDP-`Lookup` formula with explicit per-AMS values — OR keep the formula and we only refresh the Macro GDP forecast (your call). |
| **Size category** (`Small/Medium/Large`) | `Activity Level` | % | Σ `stock_pct` over the 3 efficiency cells of that size, renormalised to 100 % across the 3 sizes | Share of fridge-/AC-owning households whose unit is this size. **Sums to 100 % across the 3 sizes. Scenario-invariant** (verified: IDN 2040 Large/Med/Small = 20.2/30.8/49.1 identical across BAS/ATS/RAS). |
| **Efficiency leaf** (`Low/Mid/High`) | `Activity Level` | % | `stock_pct(cell)` ÷ Σ`stock_pct(size)` × 100 | Within-size efficiency mix. **Sums to 100 % within each size. Scenario-SPECIFIC** — this is the only level that differs by BAS/ATS/RAS (the efficiency lever; e.g. IDN Small High_eff 35.8 % BAS → 89.7 % RAS at 2040). |
| **Efficiency leaf** | `Final Energy Intensity` | kWh / Household | `kwh_unit(cell)` | Per-unit annual electricity for that (size, eff) cell. **Flat 2023→2060** — `kwh_unit` is frozen per cell in our model; the efficiency story lives in the leaf-share shift, not in FEI. |
| **Efficiency leaf** | `Uncalibrated Final Intensity` | kWh / Household | `kwh_unit(cell)` | = FEI. We carry no separate lab-vs-calibrated split, so calibration factor = 1.0. (Resolves handover q4: ratios are 1.0 by construction.) |
| any | `Demand Cost`, `Share_of_Industry` | — | — | Leave at `0` placeholders. |
| parent | `End Year Penetration` | — | — | Leave unused — we author the trajectory via `Activity Level`. |

**Use STOCK shares, not sales** — `Activity Level` is a "% of
households" (installed-base) concept, so the size + efficiency shares
come from `stock_pct`, not `sales_pct`. FEI is per installed household.

### Energy chain (sanity)

```
leaf energy = Households × ownership% × size% × eff_share% × FEI
```

Cross-check: our per-cell `ownership_pct` already equals
`ownership% × size% × eff_share%` (a % of all households), so
`leaf energy = Households × (ownership_pct / 100) × kwh_unit`.

---

## 3. Scenario handling (BAS / ATS / RAS)

Single-lever architecture (DESIGN.md §2.2): RAS-vs-ATS divergence is the
**efficiency-mix acceleration only**.

- **Paste once (common to all 3 scenarios):** parent `Activity Level`
  (ownership) + the 3 size-node `Activity Level`s + all 9 leaf
  `Final Energy Intensity` / `Uncalibrated` values.
- **Paste per LEAP scenario:** only the 9 efficiency-leaf
  `Activity Level`s (the within-size Low/Mid/High mix).

CSV scenario string is plain `RAS` (not `RASv1`) per DESIGN.md §2.2.

---

## 4. Answers to the handover's open questions (refrigeration §5)

1. **What do the tiers segment?** → **Two layers now**: Size
   (Small/Medium/Large) as the household segment, Low/Mid/High
   **efficiency** nested within. The legacy flat non-monotonic FEI was
   an income-style placeholder; under the 2-layer build, FEI orders
   monotonically within each size (High_eff < Mid_eff < Low_eff).
2. **Activity Level trajectory anchors** → we supply a **full 2025–2060
   trajectory** per leaf, not a 2-year `Interp`. (Ownership + size
   shares effectively flat; efficiency-leaf shares evolve.)
3. **FEI dynamics** → **flat per leaf** (kwh_unit frozen); efficiency
   improvement shows as the leaf-share shift toward High_eff, not as FEI
   decline. (Can revisit if you want MEPS-driven FEI decline too.)
4. **Uncalibrated vs calibrated** → equal (factor 1.0); no separate lab
   source on our side.
5. **Unit alias** → normalise to `kWh per Household`. OK.
6. **Horizon + coverage** → 2025–2060, all 10 AMS.

---

## 5. Next steps

1. LEAP team builds the nested tree above for Refrigeration **and** AC
   (confirm AC parent branch name).
2. Re-probe + re-issue the AC + Refrigeration handovers reflecting the
   updated structure.
3. We then emit per-variable / per-leaf inject CSVs from the existing
   9-cell `{ac,fridge}_sales_projection.csv` (or keep the wide CSV plus
   this mapping — your preference).
4. Lighting is **not** affected — its LEAP tree is a genuine
   5-technology stack (not our design); already remapped 2026-05-20 to
   `lighting_tech_shares.csv` + `lighting_bulb_wattage.csv`.

---

## 6. Inject bundle status (for the eventual zip to the LEAP team)

| Subsector | Deliverable(s) | Status |
|---|---|---|
| Lighting | `lighting_tech_shares.csv`, `lighting_bulb_wattage.csv` | **Ready** (remapped 2026-05-20) |
| AC | `ac_sales_projection.csv` (9-cell, 2-layer) | **Pending** structure build + new handover, then per-leaf emit |
| Fridge | `fridge_sales_projection.csv` (9-cell, 2-layer) | **Pending** structure build + new handover, then per-leaf emit |
