# Residential Lighting — Authoring Spec for Appliances Team

> Branch taxonomy, variables, units, and current-value patterns for
> the Residential Lighting sub-tree on LEAP area `aeo9_v0.46`.
> Captured 2026-05-20 via direct LEAP UI inspection + COM probe of
> the branch hierarchy. **What the team needs to send us per cycle
> is in §4.**

---

## 1. Branch taxonomy

The Lighting sub-tree under `Demand\Residential\Projections\Lighting\`
has two parallel arms, one per fuel grouping:

```
Demand\Residential\Projections\Lighting                           ← Demand Category (BT=1)
├── Electricity                                                   ← Demand Category (BT=1)
│   ├── Incandescent                                              ← Demand Technology (BT=4)
│   ├── CFL                                                       ← Demand Technology (BT=4)
│   ├── Fluorescent                                               ← Demand Technology (BT=4)
│   ├── Halogen                                                   ← Demand Technology (BT=4)
│   └── LED                                                       ← Demand Technology (BT=4)
└── Other                                                         ← Demand Category (BT=1)
    ├── Kerosene and Candles                                      ← Demand Technology (BT=4)
    └── Solar Lighting                                             ← Demand Technology (BT=4)
```

(BT = LEAP BranchType. BT=1 holds aggregator / fuel-group settings;
BT=4 holds per-tech inputs.)

---

## 2. Variables per branch level

The LEAP UI exposes ~5 input-side variables per level (the rest are
calculated results, GWP allocations, load shapes, etc. — not author-
relevant and excluded here). Same shape across all 5 Electricity
sub-techs; the `Other` arm follows the same pattern.

### 2.1 At `…\Lighting\Electricity` (parent fuel-group node)

These authoring inputs apply once at the fuel-group level and feed
the per-tech intensity formulas below.

| Variable | Unit | Authored as | What it means |
|---|---|---|---|
| `Activity Level` | Percent | Formula: `Key\Energy Access\Electrification Rate[%]` | Share of households served by grid electricity for lighting |
| `Demand Cost` | 2020 USD per Household | `0` (flat) | Annualised cost of lighting service per household (currently 0 — placeholder for cost-side modelling) |
| `Share_of_Industry` | Fraction | `0` (flat) | Industry-share allocation (currently zero — residential is fully residential) |
| `BulbsPerHH` | Bulbs | `7` (flat) | Number of light bulbs per household (Indonesia value shown — verify per-AMS) |
| `LightingHours` | Hours | `6 * (1 - Key\Net Zero Measures\Residential\Gamification\Energy Savings:Activity Level[%]/100 * Key…)` | Daily lighting hours, modulated by a Net Zero Measures gamification trigger |

### 2.2 At `…\Lighting\Electricity\<Tech>` (per-tech leaf)

These per-tech inputs distinguish each lighting technology.

| Variable | Unit | Authored as | What it means |
|---|---|---|---|
| `Activity Level` | Percent | Single value per tech (e.g. LED `52`) | This tech's share of electricity-lit households. Sums across all 5 techs should ≈ 100% for a given (region, year) |
| `Bulb Wattage` | Watts | Single value per tech (e.g. LED `7.2`) | Average wattage of a bulb of this technology |
| `Final Energy Intensity` | kWh per Household | Formula: `Electricity:BulbsPerHH[Bulbs] *~ Bulb Wattage[Watts] *~(Electricity:LightingHours[Hours] * 365) ~* Key\Cal\Residential\Electricity:Activity Level[Factor] /1000` | Derived per-household kWh — combines parent's BulbsPerHH × LightingHours × 365 days × tech's Bulb Wattage × a calibration factor / 1000. Authored as expression; LEAP computes it. |
| `Demand Cost` | 2020 USD per Household | `0` (flat) | Per-tech annualised cost (currently 0) |
| `Share_of_Industry` | Fraction | `0` (flat) | Industry-share (residential = 0) |

### 2.3 At `…\Lighting\Other\<Tech>` (Kerosene and Candles, Solar Lighting)

Structure expected to mirror §2.2 but per-tech variables differ
(no `Bulb Wattage`; alternative intensity drivers). Pending UI capture.

---

## 3. Same-name-different-semantics gotcha

`Activity Level` appears at THREE distinct semantic levels:

| Where | Semantics | Unit |
|---|---|---|
| `…\Lighting\Electricity` (fuel-group node) | Electrification rate — share of households on grid | Percent |
| `…\Lighting\Electricity\<Tech>` (tech leaf) | Tech share — % of grid-lit households using this tech | Percent |
| `Key\Cal\Residential\Electricity:Activity Level[Factor]` (calibration) | Calibration multiplier in the intensity formula | Factor (dimensionless) |

Don't confuse them when sending data. Tech-leaf Activity Levels should
sum to ~100% across the 5 Electricity techs per (region, year).

---

## 4. What the team needs to send us

### 4.1 Required data per (AMS, year)

| Branch | Variable | Per-AMS? | Per-year? | Suggested CSV column |
|---|---|---|---|---|
| `…\Lighting\Electricity` | `BulbsPerHH` | yes | yes (trajectory) | `bulbs_per_household` |
| `…\Lighting\Electricity` | `LightingHours` | yes | maybe | `daily_lighting_hours` (or keep formula) |
| `…\Lighting\Electricity\Incandescent` | `Activity Level` | yes | yes | `tech_share_incandescent_percent` |
| `…\Lighting\Electricity\CFL` | `Activity Level` | yes | yes | `tech_share_cfl_percent` |
| `…\Lighting\Electricity\Fluorescent` | `Activity Level` | yes | yes | `tech_share_fluorescent_percent` |
| `…\Lighting\Electricity\Halogen` | `Activity Level` | yes | yes | `tech_share_halogen_percent` |
| `…\Lighting\Electricity\LED` | `Activity Level` | yes | yes | `tech_share_led_percent` |
| `…\Lighting\Electricity\<each>` | `Bulb Wattage` | maybe | maybe | `bulb_wattage_<tech>_watts` |
| `…\Lighting\Other\Kerosene and Candles` | TBD per §2.3 | TBD | TBD | (pending) |
| `…\Lighting\Other\Solar Lighting` | TBD per §2.3 | TBD | TBD | (pending) |

### 4.2 What you DON'T need to send

- `Activity Level` at `…\Lighting\Electricity` (the electrification
  rate) — already authored as a formula referencing
  `Key\Energy Access\Electrification Rate`. If the rate needs to
  change, that's a separate Energy Access authoring task, not
  Lighting.
- `Final Energy Intensity` — authored as a formula; LEAP computes
  from the inputs you DO send (BulbsPerHH × LightingHours × Bulb
  Wattage × calibration).
- `Demand Cost` and `Share_of_Industry` — currently 0 placeholders;
  only send if your team is taking on cost-side modelling.
- Any `<Calculated>` / GWP / Load Shape / Pollutant Loadings variables
  — those are computed by LEAP from upstream inputs.

### 4.3 Suggested data-drop shape

```
inject/residential/<YYYYMMDD>/lighting/
├── bulbs_per_household.csv
│   Country, Year, BulbsPerHH
├── lighting_hours.csv
│   Country, Year, DailyLightingHours
├── lighting_tech_shares.csv
│   Country, Year, Tech (one of: Incandescent, CFL, Fluorescent, Halogen, LED), share_percent
├── bulb_wattage.csv (only if differs from defaults)
│   Country, Tech, watts
└── other_lighting.csv (Kerosene+Candles, Solar Lighting — TBD)
    Country, Year, Tech, ...
```

Country names should use the **source-CSV form** (e.g. `Brunei
Darussalam`, `Lao PDR`, `Viet Nam`) — we map them to LEAP region
names on our side (see [TRANSPORT_CSV_SPEC.md §3.1](../transport/TRANSPORT_CSV_SPEC.md)
for the established country mapping; same applies here).

---

## 5. Open questions for the team

1. **`LightingHours` formula vs flat value** — currently the LEAP
   expression bakes in a Net Zero Measures gamification dependency.
   Do you want to author flat hours (we replace the formula) OR keep
   the formula and only author the base hours (we re-build the
   expression with your numbers)?

2. **`BulbsPerHH` per-AMS data** — the current Indonesia value is 7
   (flat). Do you have per-country and/or per-year trajectories?

3. **`Bulb Wattage` per-tech** — LED is 7.2W in the LEAP authoring;
   the other 4 techs likely have different values (Incandescent ~60W
   etc.). Do you want to author region-specific wattages, or accept
   LEAP's existing per-tech defaults?

4. **`…\Lighting\Other\<Tech>`** — please confirm the variables you
   author for Kerosene+Candles and Solar Lighting (we'll add to §2.3
   once captured).

5. **Time horizon** — confirm projection-year coverage you can supply
   (e.g. 2025–2060, anchored to 2024 baseline).

---

## 6. Branch + variable map (raw COM probe output)

For reference: full COM-probed Variables list per branch is in
[_residential_branch_map.csv](_residential_branch_map.csv). That CSV
includes the ~23 LEAP-internal variables per branch, of which only
the ~5 listed above are authoring-relevant. The rest are calculated
results.

---

## 7. Versioning

This handover reflects LEAP area `aeo9_v0.46` as of 2026-05-20.
If the area version bumps (v0.47 etc.), re-probe and re-confirm
the branch structure before sending data — LEAP authors sometimes
add/remove techs or rename branches between versions.
