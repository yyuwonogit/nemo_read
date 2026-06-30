# AC LEAP Input — within-tier efficiency drift variant

**Last updated: 2026-06-24.** Documents `ac_leap_inject_drift.csv` (built by
`Residential/AC/build_ac_leap_inject_drift.py`) — the AC analogue of the Fridge
drift variant. Adds a **within-tier efficiency-improvement lever** (each
Size×Efficiency cell's intensity improves over time) on top of the composition
lever. The frozen baseline `ac_leap_inject.csv` is **unchanged** — pick one at
paste time. The two-lever logic, double-count avoidance, and useful-energy
encoding are identical to the fridge variant — see
[`fridge_leap_drift_method.md`](fridge_leap_drift_method.md) for the full
derivation; this doc records the AC-specific parameters and numbers.

## Two levers, no double count (recap)

`I(t) = Σ s_cell(t)·i_cell(t)` — composition `s` (eff_share, unchanged) × technology
`i` (the new drift). No double count because the frozen build froze `i` (carried
zero tech gain), so the drift adds the previously-absent part. Guardrails: fit each
lever to its own observable; relative terciles; LMDI conservation audit; RAS
composition saturates at 100% High_eff by 2035 so post-2035 only drift acts.

## Encoding (useful-energy, ultimate-frontier anchor)

```
final_kwh(cell, year, scen)   = kwh_unit_2024(cell) × (1 − rate[scen])^max(0, year−2025)
Useful Energy Intensity(size) = kwh_unit_2024(High_eff, size) × DF_ULT   (constant per size)
Efficiency(cell, year, scen)  = Useful_EI(size) / final_kwh   → ≤100%, =100% only RAS @2060
Demand Cost O&M (RAS)         = tariff × final_kwh (drifted; per unit)
```

DF_ULT = RAS drift factor at 2060 = (1−0.025)^35 = **0.412** (the ultimate modelled
frontier; "100% efficiency" = RAS best at 2060).

## Drift rates — AC (higher than Fridge)

ASEAN room-AC MEPS ratchet hard: the harmonised CSPF target rises ~3.08 (2020) →
3.7 (2023) → 6.09 (2030) (ASEAN SHINE / LBNL 2021), plus the fixed→inverter
transition — so within-tier AC efficiency improves faster than fridge. Set in
`DRIFT_RATE`; the key reviewable assumption.

| Scenario | Drift rate | Rationale | Cumulative by 2060 (35 yr) |
|----------|-----------|-----------|----------------------------|
| BAS | **0.5%/yr** | autonomous technology only | −16% |
| ATS | **1.5%/yr** | national MEPS + inverter shift | −41% |
| RAS | **2.5%/yr** | aggressive harmonised CSPF push | −59% |

(Fridge used 0.5 / 1.0 / 2.0%/yr; AC is one notch higher on ATS/RAS for the CSPF
ratchet. Still gentler than treating AC's near-doubling CSPF target literally.)

## What changed vs the frozen AC inject

| | Frozen (`ac_leap_inject.csv`) | Drift (`ac_leap_inject_drift.csv`) |
|---|---|---|
| Cell intensity | `kwh_unit` frozen | `final_kwh_unit` drifts down (+ `kwh_unit_2024` kept) |
| Efficiency | frozen (High=100%) | ramps; 100% only at RAS 2060 High_eff |
| Useful EI | per-size 2024 High_eff | per-size 2024 High_eff × DF_ULT (lower) |
| Demand Cost O&M | tariff × `kwh_unit` | tariff × `final_kwh_unit` (drifted) |
| Activity (units/HH, shares) | — | identical (Option A) |
| New columns | — | `drift_rate_pct_yr`, `drift_factor`, `kwh_unit_2024`, `final_kwh_unit` |

## Worked example — Indonesia, Small, High_eff

| Year | final_kwh (BAS/ATS/RAS) | Efficiency % (BAS/ATS/RAS) |
|------|--------------------------|-----------------------------|
| 2024 | 783 / 783 / 783 | 41.2 / 41.2 / 41.2 |
| 2035 | 744 / 673 / 608 | 43.3 / 48.0 / 53.1 |
| 2060 | 657 / 461 / 323 | 49.1 / 70.0 / 100.0 |

(Frozen baseline held all at 783 kWh and 100% efficiency.)

## Status

Parallel variant; baseline frozen file unchanged. Drift rates are documented
assumptions for expert review. Use this file for the within-tier improvement story,
the frozen file for the conservative baseline.
