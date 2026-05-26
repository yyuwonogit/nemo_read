# Residential Refrigeration — Authoring Spec for Appliances Team

> Branch taxonomy, variables, units, and current-value patterns for
> the Residential Refrigeration sub-tree on LEAP area `aeo9_v0.46`.
> Captured 2026-05-20 via direct LEAP UI inspection. **What the
> team needs to send us per cycle is in §4.**

---

## 1. Branch taxonomy

```
Demand\Residential\Projections\Refrigeration                      ← Demand Category (BT=1)
├── High                                                          ← Demand Technology (BT=4)
├── Medium                                                        ← Demand Technology (BT=4)
└── Low                                                           ← Demand Technology (BT=4)
```

3 tech leaves (High/Medium/Low) that partition households into
3 segments — Activity Levels across the 3 tiers sum to 100% per
(region, year), confirmed via 2005 Indonesia values
(47.7 + 29.9 + 22.4 = 100.0).

**The High/Medium/Low naming is unresolved** — see §5 question 1.

---

## 2. Variables per branch level

### 2.1 At `…\Refrigeration` (parent fuel-group node)

Household-wide refrigeration penetration, GDP-modulated.

| Variable | Unit | Authored as | What it means |
|---|---|---|---|
| `Activity Level` | Percent | `Lookup(Linear, Key\Macroeconomic\Real GDP Per Capita[2017 USD / person], Value(…, LastHistoricalYear), Value(LastHistoricalYear), 10000, 60, 30000, 95, 80000, 95)` | Fridge ownership rate per household, scaled to GDP. Piecewise-linear: 60% at $10k GDP per capita → 95% at $30k+ (caps at 95%) |
| `Demand Cost` | 2020 USD per Household | `0` (flat) | Annualised refrigeration cost per household (placeholder) |
| `Share_of_Industry` | Fraction | `0` (flat) | Industry-share allocation (residential is fully residential) |
| `End Year Penetration` | % | `0` (flat) | End-year ownership cap (alternative to the GDP Lookup; currently unused — see §3) |

### 2.2 At `…\Refrigeration\<Tier>` (High / Medium / Low leaves)

Per-tier household segmentation and energy intensity. The Activity
Levels across tiers should sum to ~100% per (region, year).

| Variable | Unit | Authored as | What it means |
|---|---|---|---|
| `Activity Level` | Percent | `Interp(2023, V₁, 2024, V₂)` | Share of households in this tier. Only 2 anchor years (2023, 2024); LEAP extrapolates after that — see §5 q2 |
| `Final Energy Intensity` | kWh per Household | `Data(2023, V, 2024, V, …, 2060, V)` (flat per-year list) | Calibrated annual electricity consumption per household at this tier |
| `Uncalibrated Final Intensity` | kwh/hh (alias for kWh/Household) | Single value (e.g. `557.089991745`) | Lab-spec intensity before LEAP applies calibration multiplier |
| `Demand Cost` | 2020 USD per Household | `0` (flat) | Per-tier annualised cost (placeholder) |
| `Share_of_Industry` | Fraction | `0` (flat) | Industry-share allocation |

**Current Indonesia values (2005, BAS):**

| Tier | Activity Level | Final Energy Intensity | Uncalibrated Final Intensity |
|---|---|---|---|
| High | 47.7% | 550.879 kWh/HH (flat 2023→2060) | 557.090 kwh/hh |
| Medium | 29.9% | 411.575 kWh/HH (flat 2023→2060) | 449.791 kwh/hh |
| Low | 22.4% | 648.852 kWh/HH (flat 2023→2060) | 608.896 kwh/hh |

Note the calibrated FEI does **NOT** order monotonically with tier
name — Low (648.85) > High (550.88) > Medium (411.58). This is an
open question (§5 q1).

---

## 3. `Activity Level` vs `End Year Penetration`

At the parent fridge node, LEAP exposes two ways to author ownership:

- **`Activity Level`** — full-trajectory expression (currently the
  GDP-Lookup formula). Drives per-year ownership rate.
- **`End Year Penetration`** — single end-year anchor (currently `0`,
  unused). LEAP would interpolate/extrapolate from a base year to
  this anchor if set.

The current LEAP authoring uses Activity Level (the formula). Don't
author both — one or the other.

---

## 4. What the team needs to send us

### 4.1 Required data per (AMS, year)

| Branch | Variable | Per-AMS? | Per-year? | Suggested CSV column |
|---|---|---|---|---|
| `…\Refrigeration` | `Activity Level` | yes | yes (trajectory OR formula reference) | `fridge_ownership_rate_percent` |
| `…\Refrigeration\High` | `Activity Level` | yes | yes | `tier_share_high_percent` |
| `…\Refrigeration\Medium` | `Activity Level` | yes | yes | `tier_share_medium_percent` |
| `…\Refrigeration\Low` | `Activity Level` | yes | yes | `tier_share_low_percent` |
| `…\Refrigeration\High` | `Final Energy Intensity` | yes | maybe (currently flat) | `fei_high_kwh_per_hh` |
| `…\Refrigeration\Medium` | `Final Energy Intensity` | yes | maybe | `fei_medium_kwh_per_hh` |
| `…\Refrigeration\Low` | `Final Energy Intensity` | yes | maybe | `fei_low_kwh_per_hh` |
| `…\Refrigeration\<each>` | `Uncalibrated Final Intensity` | yes | no (single value) | `uncalibrated_intensity_<tier>_kwh_per_hh` |

### 4.2 What you DON'T need to send

- `End Year Penetration` — alternative to Activity Level; not in use.
- `Demand Cost` and `Share_of_Industry` — currently 0 placeholders.
- Any `<Calculated>` / GWP / Load Shape variables — LEAP computes
  from your inputs.
- The `Activity Level` formula at parent level — if your data is in
  ownership-rate-per-AMS form, we can replace the GDP-Lookup formula
  with explicit values. If you'd rather keep the GDP-scaled formula,
  no data needed here (just update the Macroeconomic GDP forecast).

### 4.3 Suggested data-drop shape

```
inject/residential/<YYYYMMDD>/refrigeration/
├── fridge_ownership.csv
│   Country, Year, ownership_rate_percent
├── fridge_tier_shares.csv
│   Country, Year, Tier (one of: High, Medium, Low), share_percent
├── fridge_intensity.csv
│   Country, Year, Tier, fei_kwh_per_hh, uncalibrated_intensity_kwh_per_hh
```

Country names = source-CSV form (e.g. `Brunei Darussalam`, `Lao PDR`,
`Viet Nam`); we handle the mapping to LEAP region names.

---

## 5. Open questions for the team

1. **What do High / Medium / Low actually segment?** Energy
   intensities don't order monotonically (Low > High > Medium in
   kWh/hh), so it's not pure efficiency tiers. Income brackets?
   Fridge size/age cohorts? Brand or feature tiers? Please clarify
   the segmentation criterion so we know how to author per-AMS.

2. **Activity Level trajectory anchors** — current authoring uses
   only 2023+2024 in the `Interp()`, leaving years 2025–2060 to LEAP's
   default extrapolation (likely constant). Do you have a real
   trajectory through 2060, or should we keep the 2-year anchor
   pattern?

3. **Final Energy Intensity dynamics** — currently flat at one value
   from 2023 to 2060. Do efficiency improvements over the projection
   horizon (e.g. minimum-efficiency standards tightening) need to be
   reflected? If yes, what's the trajectory?

4. **Uncalibrated vs Calibrated intensity** — the calibration ratio
   appears to be ~0.99 (550.88 / 557.09) for High and ~0.91 (411.58
   / 449.79) for Medium — inconsistent. Should this be normalized,
   or does the inconsistency reflect real calibration-data
   differences per tier? Where do the uncalibrated lab values come
   from?

5. **Unit alias inconsistency** — LEAP shows `kWh per Household`
   on calibrated intensity and `kwh/hh` on uncalibrated. We'll
   normalize to `kWh per Household` in the canonical. Confirm OK.

6. **Time horizon + region coverage** — confirm projection year
   range you can supply (2025–2060) and which AMS you have data for.

---

## 6. Versioning

This handover reflects LEAP area `aeo9_v0.46` as of 2026-05-20.
If the area version bumps, re-probe the branch taxonomy before
sending data — LEAP authors sometimes add/remove tiers between
versions.
