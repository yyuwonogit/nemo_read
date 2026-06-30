# Fridge LEAP Input — row-by-row method

**Last updated: 2026-06-24.** This walks through every row of the
refrigeration team's mapping workbook
(`Residential/Fridge/Raw/refrigerator_leap_input_mapping.xlsx`, sheet
`Sheet1`, 14 variable-rows) and states exactly how we treat it: the
formula/method, the column it lands in, which scenarios it applies to,
and its status. All values live in one file —
`fridge_leap_inject.csv` (12,690 rows = 10 AMS × 47 yr × 9 Size×Efficiency
cells × 3 scenarios). Builder: `Fridge/build_fridge_leap_inject.py`
(+ `.txt` sidecar). Companion: [`fridge_leap_input_mapping.md`](fridge_leap_input_mapping.md).

Shared constants: discount rate **r = 9%** (ADB social rate, 2017),
lifetime **n = 12 yr**, **CRF = r(1+r)ⁿ/((1+r)ⁿ−1) = 0.1397**,
**TOE = kWh / 11630**. `kwh_unit(High_eff, size)` is the most-efficient
cell of each size and serves as the useful-energy reference.

> **Two variants exist.** This doc describes the **frozen baseline**
> (`fridge_leap_inject.csv`), where Efficiency (row 4) and Useful Energy
> Intensity (row 6) are constant over time. A parallel **within-tier
> efficiency-drift variant** (`fridge_leap_inject_drift.csv`) makes each tier's
> kWh improve over time — it changes **row 4** (Efficiency ramps toward 100%),
> **row 6** (Useful EI re-anchored to the ultimate frontier), and **row 3's O&M**
> (uses the drifted kWh); rows 1, 2, 5 and 7–14 are identical. Full method:
> [`fridge_leap_drift_method.md`](fridge_leap_drift_method.md).

## Summary — the 14 workbook rows

| # | Scenario | Variable | Workbook said | Our treatment | Inject column | Status |
|---|----------|----------|---------------|---------------|---------------|--------|
| 1 | All | Activity Level (%) | `ownership_pct` | Parent/size/leaf share decomposition (+ flat) | `ownership_parent_pct`, `size_share_pct`, `eff_share_pct`, `leaf_ownership_pct` | ✅ filled |
| 2 | BAS, ATS | Demand Cost (USD/HH) | `AnnualizedCost(price_usd × decay, life)` | Annualised capital only (decay already in CSV) | `demand_cost_usd_per_hh` (=`annualized_capital_usd`) | ✅ filled |
| 3 | RAS | Demand Cost (USD/HH) | `AnnualizedCost(Capital, Life, Rate, O&M)` | Annualised capital + electricity O&M | `demand_cost_usd_per_hh` (= capital + `om_electricity_usd`) | ✅ filled |
| 4 | All | Efficiency (%) | `kwh_unit / kwh_unit(High_eff)` | **Inverted** → `kwh_high / kwh_cell` (High_eff = 100%) | `efficiency_pct` | ✅ filled (corrected) |
| 5 | All | Load Shape | *(blank)* | Leave at LEAP default (flat) | — | ⬜ default |
| 6 | All | Useful Energy Intensity (TOE/HH) | `convert kwh_unit → TOE` | **Per-size High_eff reference** → TOE (not per-cell) | `useful_energy_intensity_toe` | ✅ filled (corrected) |
| 7 | RAS | Maximum Availability (%) | *(blank)* | Leave blank/unconstrained | — | ⬜ blank by design |
| 8 | RAS | Maximum Device Additions | *(blank)* | Leave blank/unconstrained | — | ⬜ blank by design |
| 9 | RAS | Maximum Devices | *(blank)* | Leave blank/unconstrained | — | ⬜ blank by design |
| 10 | RAS | Minimum Device Additions | *(blank)* | Leave blank/unconstrained | — | ⬜ blank by design |
| 11 | RAS | Minimum Devices | *(blank)* | Leave blank/unconstrained | — | ⬜ blank by design |
| 12 | RAS | Minimum Share (%) | *(blank)* | Leave blank/unconstrained | — | ⬜ blank by design |
| 13 | RAS | Minimum Utilization (%) | *(blank)* | Leave blank/unconstrained | — | ⬜ blank by design |
| 14 | RAS | Unit Capacity (kW) | **`unit_capacity_kw` = kwh_high(size) ÷ 8760** (per-size service power; RAS only) | `unit_capacity_kw` | ✅ filled (2026-06-25) |

## Dimensionality — how each value varies (incl. cross-AMS)

Whether a value is **unique per AMS** or **the same for all 10 AMS**, plus how it
moves across year / scenario / the 9 Size×Efficiency cells. `price_usd` and
`kwh_unit` are **regionally pooled** Euromonitor cell values applied to all 10
AMS, so the only per-country cost driver is the electricity tariff in the RAS
O&M; otherwise the entire per-AMS story lives in the **Activity Level**.

| # | Variable | Inject column | Across AMS | Across Year | Across Scenario | Across Size×Eff cell | Distinct values |
|---|----------|---------------|-----------|-------------|-----------------|----------------------|-----------------|
| 1a | Activity Level — parent (ownership) | `ownership_parent_pct` | **Unique per AMS** | Yes | No (invariant) | No (parent) | per AMS × year |
| 1b | Activity Level — size node | `size_share_pct` | **Unique per AMS** | Yes | No (invariant) | by Size only | per AMS × year × size |
| 1c | Activity Level — efficiency leaf | `eff_share_pct` | **Unique per AMS** | Yes | **Yes (the lever)** | by cell | per AMS × year × scenario × cell |
| 2 | Demand Cost (BAS, ATS) | `demand_cost_usd_per_hh` | **Same for all AMS** (pooled price) | Yes (premium decay) | Yes (BAS −2%/yr vs ATS −3%/yr) | by cell | per year × scenario × cell |
| 3 | Demand Cost (RAS) | `demand_cost_usd_per_hh` | **Unique per AMS** (electricity tariff in O&M) | Yes (capital decay) | RAS only | by cell | per AMS × year × cell |
| 4 | Efficiency | `efficiency_pct` | **Same for all AMS** (pooled kWh) | No (frozen) | No | by cell | 9 cells (7 unique: High=100%) |
| 5 | Load Shape | — | Same for all (LEAP default) | — | — | — | 1 (flat) |
| 6 | Useful Energy Intensity | `useful_energy_intensity_toe` | **Same for all AMS** (pooled kWh) | No (frozen) | No | by Size only | 3 (one per size) |
| 14 Unit Capacity (kW) | `unit_capacity_kw` | **Same for all AMS** (pooled kWh) | No (fixed) | RAS only | by Size only | 3 (per size) |
| 7–13 RAS optimisation vars | — | N/A (blank by design) | — | — | — | 0 |

**Reading it:** only **Activity Level** (all three levels) and the **RAS Demand
Cost** differ by country. **Efficiency**, **Useful Energy Intensity**, and the
**BAS/ATS Demand Cost** are identical across all 10 AMS — so at paste time those
three can be entered once and copied to every region; ownership/size/efficiency
shares and the RAS lifecycle cost must be pasted per AMS.

---

## Row 1 — Activity Level (All scenarios)

**Workbook:** Percent, "Share of Household", `[constant]`, source `ownership_pct`.

**Treatment.** The 2-layer tree multiplies Activity Levels down (parent →
size → leaf), so we decompose the per-cell ownership into the three tree
levels using **stock shares** (installed base, `stock_pct` — not sales,
which are zero in early years):

- **Parent** (`Refrigeration`) `Activity Level` = `ownership_parent_pct`
  = `total_ownership_pct` (% of all households owning a fridge). Scenario-invariant.
- **Size node** (`Small/Medium/Large`) `Activity Level` = `size_share_pct`
  = Σ`stock_pct` over the 3 efficiency cells of that size, renormalised to
  100% across the three sizes. Scenario-invariant.
- **Efficiency leaf** `Activity Level` = `eff_share_pct` = `stock_pct(cell)` ÷
  Σ`stock_pct(size)` × 100. Sums to 100% within each size. **This is the only
  per-scenario level** — it is where BAS/ATS/RAS differ (the efficiency lever).

We also emit `leaf_ownership_pct` = the raw per-cell `ownership_pct` (% of all
households on that exact cell), so if the LEAP tree instead wants a flat
per-leaf "% of households" the value is already there. `leaf_ownership_pct` ≈
`ownership_parent_pct × size_share_pct × eff_share_pct` (the product of the
three levels).

---

## Row 2 — Demand Cost, BAS + ATS

**Workbook:** 2020 USD per Household, `AnnualizedCost(price_usd × decay_factor, lifetime)`;
note "lifespan = 12; decay BAS 2%/yr, ATS 3%/yr".

**Treatment.** Capital cost only (no running cost), annualised:

```
demand_cost_usd_per_hh = price_usd × CRF        (CRF = 0.1397 at r=9%, n=12)
```

The premium-decay is **already applied** to `price_usd` in
`fridge_sales_projection.csv` (BAS −2%/yr, ATS −3%/yr), so we do **not**
multiply by a decay factor again — the workbook's `× decay_factor` is redundant
here. Column: `annualized_capital_usd` (= `demand_cost_usd_per_hh` for BAS/ATS).

---

## Row 3 — Demand Cost, RAS

**Workbook:** 2020 USD per Household, `AnnualizedCost(Capital Cost, Life, Rate, O&M Cost)`;
the inputs were blank.

**Treatment.** RAS is the **optimisation** scenario (RASv2 in docs, "RAS" string
in CSV/LEAP per DESIGN.md §2.2), so its Demand Cost carries the full lifecycle
cost — annualised capital **plus** the annual electricity running cost — so the
LEAP optimiser trades a higher purchase price against lower electricity use and
prefers efficient cells:

```
om_electricity_usd     = tariff(Country) × kwh_unit(cell)     (annual USD/HH)
demand_cost_usd_per_hh = price_usd × CRF + om_electricity_usd
```

Inputs we supplied for the workbook's blanks: **Capital** = `price_usd`;
**Life** = 12 yr; **Rate** = 9% (ADB social discount rate, 2017 — see
data_sources.md §3.6); **O&M** = electricity = per-AMS 2020 tariff (USD/kWh,
sourced + dual-verified, `Raw/electricity_tariffs.csv`) × per-cell `kwh_unit`.
Columns: `tariff_usd_per_kwh`, `om_electricity_usd`, `annualized_capital_usd`,
`demand_cost_usd_per_hh`.

*Confirm at paste:* if LEAP prices electricity as a fuel separately, RAS must use
Demand Cost only (don't also charge electricity as a fuel → double count).

---

## Row 4 — Efficiency (All scenarios)

**Workbook:** Percent, `kwh_unit / kwh_unit(High_eff)`, "Assume high_eff as the
most efficient tier (100% efficiency)".

**Treatment — corrected.** As written the expression gives **>100%** for less
efficient tiers (e.g. Small Low = 519/305 = 152%), which is invalid in LEAP and
contradicts its own note. We invert it so the most efficient cell is 100%:

```
efficiency_pct = kwh_unit(High_eff, size) / kwh_unit(cell) × 100
```

Worked (Small, kwh_high = 305.2): High_eff 100.0%, Mid_eff 305.2/353.5 = 86.3%,
Low_eff 305.2/518.6 = 58.9%. Frozen across years and scenarios (kwh_unit is
frozen per cell). Column: `efficiency_pct`. The efficiency *improvement* over
time lives in the Row-1 leaf-share shift toward High_eff, not in this number.

---

## Row 5 — Load Shape (All scenarios)

**Workbook:** blank.

**Treatment.** Left at the LEAP default (flat). Household refrigeration runs
roughly 24/7, so a flat shape is acceptable for this pass; revisit only if a
regional daily profile is wanted. No column.

---

## Row 6 — Useful Energy Intensity (All scenarios)

**Workbook:** TOE per Household, `[constant]`, "Convert kwh_unit into TOE".

**Treatment — corrected.** In LEAP's useful-energy method,
`Final = Useful Energy Intensity ÷ Efficiency`. If Useful were the per-cell
`kwh_unit` (which is *final* energy) **and** Efficiency ≠ 100%, the final energy
would be double-counted. The useful cooling **service depends only on size**, not
on the efficiency tier, so Useful Energy Intensity is keyed to the size's
High_eff reference:

```
useful_energy_intensity_toe = kwh_unit(High_eff, size) / 11630      (constant within a size)
```

Then LEAP recomputes `Final = Useful ÷ Efficiency = kwh_unit(High_eff)/(kwh_high/kwh_cell) =
kwh_unit(cell)`, reproducing the model exactly. Worked (Small): 305.2/11630 =
**0.026242 TOE/HH**, identical on all three Small leaves. Column:
`useful_energy_intensity_toe`.

---

## Row 14 — Unit Capacity (kW)  ✅ filled

**Workbook:** Unit Capacity, Kilowatt, RAS. **LEAP doc:** "capacity of each
individual device in power units (kW or BTU/Hour) … used [on optimised branches]
to calculate the number of devices from energy demand, load shape and unit
capacity." So it sizes the device fleet — it does **not** change energy.

**Treatment — `unit_capacity_kw` = kwh_high(size) ÷ 8760.** It's the **service
capacity** per device (= useful power), so it is the **same across the three
efficiency tiers** of a size — a High/Mid/Low fridge of the same size delivers the
same cold-storage service; the tier difference is electricity, which lives in Row 4
(Efficiency), not here. Fridge runs **24/7 with a ~flat aggregate load**, so the
flat default Load Shape applies and Unit Capacity = average power = annual kWh ÷
8760. Values: **Small 0.035 / Medium 0.052 / Large 0.057 kW** (≈35/52/57 W —
consistent with real fridge average draw). **Fixed over years** (the service does
not drift; only the electricity to deliver it does — so identical in the drift
variant). **RAS branches only** (LEAP exposes it only on optimised branches);
blank for BAS/ATS. With this, LEAP's reported Demand Devices = the physical stock.

## Rows 7–13 — RAS optimisation / device variables (blank)

**Workbook:** Maximum Availability (%), Maximum/Minimum Devices, Maximum/Minimum
Device Additions, Minimum Share (%), Minimum Utilization (%) — RAS-only, all blank.

**Treatment — left blank/unconstrained by design** (user decision 2026-06-24).
RAS runs as an **unconstrained** optimisation driven by the Row-3 Demand Cost
(annualised capital + electricity O&M) plus the Row-14 Unit Capacity; the optimiser
is free to choose the efficiency mix that minimises lifecycle cost without
device-count, availability, or utilisation limits. They become a v2 lever if we
later want to bound the optimiser (e.g. a Minimum Share floor for the efficient tier).

---

## Where each value comes from

| Source | Feeds |
|--------|-------|
| `fridge_sales_projection.csv` (`stock_pct`, `ownership_pct`, `total_ownership_pct`, `kwh_unit`, `price_usd`) | Rows 1, 2, 3, 4, 6 |
| `Raw/electricity_tariffs.csv` (per-AMS 2020 USD/kWh) | Row 3 (O&M) |
| Constants r=9% / n=12 / TOE=1/11630 / hours=8760 | Rows 2, 3, 6, 14 |
| `kwh_high(size)` ÷ 8760 (service power) | Row 14 (Unit Capacity, RAS only) |
| LEAP defaults | Row 5 |
| — (blank by design) | Rows 7–13 |
