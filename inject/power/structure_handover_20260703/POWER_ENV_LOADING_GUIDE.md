# Power team — Environmental Loading (emission factor) authoring guide

**What this is:** where the pollutant emission factors for the power generation
fleet live, how they're structured, and how to author them across the four
scenarios. Canon-verified 2026-07-05 against `LEAP Input Transformation.xlsx`
(+ Indonesia). Companion data: **`power_env_loading_4scenarios.csv`** (4,417
rows, region-lock clean).

---

## 1. Where the emission factor lives

The emission factor is **NOT** on the process node. It hangs off the **feedstock
fuel**, one leaf per pollutant species:

```
Transformation\Centralized Electricity Generation\Processes\<Tech>\Feedstock Fuels\<Fuel>\<Pollutant>
        → variable:  Avg Environmental Loading
```

Example (verbatim canon):
`…\Processes\Coal Supercritical\Feedstock Fuels\Coal Bituminous\Carbon Dioxide:Avg Environmental Loading` = `94.6` (Metric Tonne / TJ).

**The variable is `Avg Environmental Loading`** — not `<Pollutant> (process)`.
The pollutant is the branch NAME; the factor is the variable ON it.

> **Power has NO `Auxiliary Fuels`.** Unlike bioenergy production processes
> (which put emissions on `Auxiliary Fuels\…`), every power emission factor is
> under **`Feedstock Fuels`**. Don't look for an Auxiliary Fuels bucket — there
> isn't one in Centralized Electricity Generation.

## 2. The 9 pollutant species

Each combustion fuel carries up to 9 pollutant leaves:

| Pollutant | Typical unit |
|---|---|
| Carbon Dioxide | **Metric Tonne / TJ** |
| Carbon Dioxide Biogenic | Metric Tonne / TJ |
| Methane | **Kilogramme / TJ** |
| Nitrous Oxide | Kilogramme / TJ |
| Nitrogen Oxides | Kilogramme / TJ |
| Sulfur Dioxide | Kilogramme / TJ |
| Carbon Monoxide | Kilogramme / TJ |
| Non Methane Volatile Organic Compounds | Kilogramme / TJ |
| Ammonia | Kilogramme / TJ |

CO₂ is authored in **tonnes/TJ**; the rest in **kg/TJ**. (The value is per unit
of *fuel energy input*, so the actual per-MWh emissions = factor ÷ Process
Efficiency.)

## 3. Which nodes have emissions — only combustion techs (54 nodes)

Emission factors exist only where a fuel is burned: coal (Subcritical /
Supercritical / Ultrasupercritical / IGCC, ± CCS), gas (Combined Cycle / Turbine
/ Engine / Steam, ± CCS), Diesel / Fuel Oil, Biomass / Biogas / Bioenergy with
CCS / Waste, and the sub-national `_MY*` / `_ID*` variants of these. **Variable
renewables (Solar, Wind, Hydro, Geothermal, storage) have no feedstock
combustion → no emission leaves** — don't add them there.

## 4. Scenario behaviour — CA / BAS / ATS / RAS

**Emission factors are scenario-INVARIANT.** They are physical constants of the
fuel, so the value is the **same in all four scenarios** (verified: CA = BAS =
ATS = RAS for every row). Author the factor once and keep it identical across
scenarios; a value that *differs* between scenarios is almost certainly an
authoring error (unless you are deliberately modelling a fuel-quality change).

The companion CSV gives you all four scenario columns side-by-side so you can
spot any accidental drift.

## 5. Region-lock (MANDATORY — CLAUDE.md §A.21)

- A `_MY*` node (and everything under it, including its emission leaves) is
  **Malaysia only**; a `_ID*` node is **Indonesia only**. Never author an
  emission factor for `Coal Subcritical_MYPE\…\Carbon Dioxide` in Vietnam.
- Base (un-suffixed) techs (e.g. `Coal Supercritical`) are region-general and
  carry emission factors in every AMS + `Base Template` (the inheritance
  default layer).
- The shipped CSV is already region-lock clean. Before handing anything back,
  run:
  `python -c "from nemo_read import find_region_lock_violations as f; print(f('yourfile.csv'))"`
  (empty list = clean).

## 6. The data file

`power_env_loading_4scenarios.csv` — columns:
`node, feedstock_fuel, pollutant, region, branch, variable, unit, CA, BAS, ATS, RAS`.
The `branch` column is the full inject path (ready for the canonical format if
you author changes). 4,417 rows = 54 nodes × their fuels × 9 pollutants ×
regions (region-lock applied).
