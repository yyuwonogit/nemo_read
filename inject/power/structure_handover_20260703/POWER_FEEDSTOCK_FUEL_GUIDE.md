# Power team — Feedstock Fuel parameter authoring guide

**What this is:** the input parameters on each power process's feedstock fuel(s)
— fuel mix share, fuel cost, and fuel source — how they're structured, and how
to author them across the four scenarios. Canon-verified 2026-07-05. Companion
data: **`power_feedstock_fuel_4scenarios.csv`** (2,427 rows, region-lock clean).

---

## 1. Where feedstock fuel parameters live

Each burning process has one or more feedstock fuels; the fuel-level parameters
sit on:

```
Transformation\Centralized Electricity Generation\Processes\<Tech>\Feedstock Fuels\<Fuel>
        → variables:  Feedstock Fuel Share ,  Fuel Cost ,  Fuel Source
```

(The pollutant leaves — `…\<Fuel>\<Pollutant>:Avg Environmental Loading` — hang
one level below; those are covered in `POWER_ENV_LOADING_GUIDE.md`.)

The **23 feedstock fuels** seen in the power tree: Coal Anthracite / Bituminous /
Lignite / Sub bituminous / Unspecified, Natural Gas, Diesel, Residual Fuel Oil,
Biomass, Bagasse, Biomethane, Municipal Solid Waste, Hydrogen, Ammonia,
Geothermal, Solar, Wind, Tidal, Wave, Large/Small Hydro, Nuclear, Non Energy.

## 2. The three parameters

### 2.1 `Feedstock Fuel Share` — the fuel mix (a percentage)
The share (%) of this fuel in the process's total energy input. Single-fuel
techs use **`Remainder(100)`** (= "whatever is left = 100%"). **Co-firing** techs
split the share across fuels — **104 (node, region) combinations carry >1
feedstock fuel** (e.g. `Biomass Other_IDEast` co-fires `Bagasse` + `Biomass`).
For co-firing, the shares across a node's fuels must sum to 100 (one fuel
usually carries `Remainder(100)`, the others carry explicit percentages).

### 2.2 `Fuel Cost` — mostly a reference into the Resources tree
The per-unit cost of the fuel. In the power tree this is usually a **reference
to the supply tree**, not a hard number:
`Fuel Cost = Resources\Primary\Biomass:Production Cost[USD…]`.
So the fuel price is owned by the **Resources** team; the power process just
points at it. Exceptions carry a literal (e.g. `Direct Air Capture\Non Energy` =
`0 ? Do not include fuel cost here…`). **Before changing a Fuel Cost, check
whether it's a Resources reference — if so, the fix belongs in Resources, not
here.**

### 2.3 `Fuel Source` — where the fuel is drawn from
A source selector; the canon value is **`SourceBelow`** (use the source/price
defined on the branch below, i.e. the Resources link). Usually leave as-is
unless you're re-pointing a fuel's supply.

> **Unit-label caveat:** the `unit` column on these three variables shows
> `2020 USD` / `U.S. Dollar` in the export — that's a LEAP metadata quirk on the
> fuel branch, not the true unit (Share is a %, Source is a selector). Trust the
> *expression*, not the unit label.

## 3. Scenario behaviour — CA / BAS / ATS / RAS

Unlike emission factors (which are constant), feedstock **shares and costs CAN
vary by scenario** — a decarbonisation scenario may raise a biomass co-firing
share or re-point a fuel. The companion CSV shows all four scenario columns so
you can author/inspect the per-scenario values. Where a cell is blank in
CA/BAS/ATS but set in RAS, that's the usual "forward change authored in the
scenario, base inherited from Current Accounts" pattern — not necessarily a gap.

## 4. Region-lock (MANDATORY — CLAUDE.md §A.21)

- `_MY*` fuels → **Malaysia only**; `_ID*` fuels → **Indonesia only**. A feedstock
  row under `Coal Subcritical_MYPE` in Thailand is a data error.
- Base techs carry feedstock params in every AMS + `Base Template` (the default
  layer most regions inherit from).
- Shipped CSV is region-lock clean. Verify anything you author with
  `nemo_read.find_region_lock_violations` before handoff.

## 5. The data file

`power_feedstock_fuel_4scenarios.csv` — columns:
`node, feedstock_fuel, region, branch, variable, unit, CA, BAS, ATS, RAS`.
2,427 rows across the 3 variables × combustion nodes × fuels × regions
(region-lock applied). The `branch` column is the full inject path.

---

**See also:** `POWER_ENV_LOADING_GUIDE.md` (the pollutant leaves below these
fuels), `README_POWER_CANON_STRUCTURE.md` (full power tree), CLAUDE.md §2.3
(NEMO↔LEAP variable mapping, corrected 2026-07-05 for the emission/feedstock
buckets).
