# Fridge LEAP Input — within-tier efficiency drift variant

**Last updated: 2026-06-24.** This documents `fridge_leap_inject_drift.csv`
(built by `Fridge/build_fridge_leap_inject_drift.py`) — a **parallel variant**
of the frozen baseline inject that adds a **within-tier efficiency-improvement
lever**: each Size×Efficiency cell's intensity *also* improves over time
(technology + MEPS), not just the household mix shifting toward High_eff.

The frozen baseline (`fridge_leap_inject.csv` / `build_fridge_leap_inject.py`)
is **unchanged** — this is an additional file, chosen at paste time. Companions:
[`fridge_leap_input_mapping.md`](fridge_leap_input_mapping.md),
[`fridge_leap_rowwise_method.md`](fridge_leap_rowwise_method.md). Motivation +
real-world evidence: `Fridge/Analysis/assumptions_for_review.md` §3.

## Why this variant exists

The frozen baseline holds every cell's kWh constant 2014→2060 — a deliberate
*frozen-efficiency counterfactual*. Real-world evidence (sourced + dual-verified,
2026-06-24) says appliance tiers do **not** stay flat: the new-fridge frontier
fell ~2–4%/yr in the US/EU **despite larger units**, MEPS floors ratchet (~−30%
per US step), and tier definitions rebase (EU 2021 A+++→~B/C). So a fixed-kWh tier
increasingly overstates new-stock energy from ~2040 on. This variant turns that
improvement on.

## Two levers, and how the double count is avoided

Fleet intensity per owning household is:

```
I(t) = Σ_cells  s_cell(t) · i_cell(t)
```

| Lever | Symbol | Carries | Source in this build |
|-------|--------|---------|----------------------|
| **Composition** | `s_cell(t)` | households migrating toward High_eff | `eff_share_pct` — **unchanged** from the frozen build |
| **Technology** | `i_cell(t)` | each tier's own kWh falling | the **new drift** applied here |

These are physically distinct (how *many* buy the good tier vs how *good* that
tier is) and multiply legitimately. **There is no double count** because the
frozen build froze `i_cell` — its composition trajectories carried **zero**
technology improvement, so this drift adds the part that was previously absent,
it doesn't re-count an existing gain.

Guardrails that keep it clean:
1. Each lever is fit to its **own observable** — composition to the sales-mix
   shift, technology to within-tier UEC decline. Neither absorbs the other's signal.
2. Tiers are **relative** terciles ("top third of the market"), so within-tier
   drift = "the top third got better" and composition = "more buy into the top
   third" — orthogonal.
3. **Conservation audit:** an LMDI decomposition of modelled ΔI into composition
   vs intensity components should match each lever's calibration source.
4. **Saturation regime:** composition is bounded [0,100%]; in RAS it saturates at
   100% High_eff by 2035, so post-2035 improvement comes **only** from drift — the
   levers occupy non-overlapping regimes there.

**Do not** re-fit the `eff_share` curves to a *total* fleet-UEC target while drift
is on without first removing drift's contribution — that would reintroduce the
double count.

## How the drift is encoded (useful-energy, ultimate-frontier anchor)

```
final_kwh(cell, year, scen) = kwh_unit_2024(cell) × drift_factor(scen, year)
drift_factor(scen, year)    = (1 − rate[scen]) ^ max(0, year − 2025)     # ≤2024 → 1.0
Useful Energy Intensity(size) = kwh_unit_2024(High_eff, size) × DF_ULT     # constant per size
Efficiency(cell, year, scen) = Useful_EI(size) / final_kwh(cell, year, scen)
```

- **DF_ULT** = the most-aggressive (RAS) drift factor at 2060 = the *ultimate
  modelled frontier*. So **100% efficiency = RAS best at 2060**; everything else
  is <100%, measuring distance to that frontier.
- **Useful Energy Intensity stays one value per size** (scenario- and
  year-invariant) — the cooling *service*. All scenario+time variation lives in
  **Efficiency**, which ramps upward as `final_kwh` falls.
- LEAP recomputes `Final = Useful ÷ Efficiency = final_kwh` by construction
  (validated in the builder to 1e-6).
- **Demand Cost O&M (RAS)** uses the **drifted** `final_kwh` (`tariff × final_kwh`),
  so a more efficient future fridge correctly costs less to run.

## Drift rates — the key reviewable assumption

Per-scenario annual within-tier kWh decline. Evidence basis: active-market
frontier ~2–4%/yr (US/EU); ASEAN's near-regional-best High_eff slower but with
MEPS catch-up headroom. Set in `DRIFT_RATE` at the top of the builder.

| Scenario | Drift rate | Rationale | Cumulative by 2060 (35 yr) |
|----------|-----------|-----------|----------------------------|
| BAS | **0.5%/yr** | autonomous technology only, no strong policy | −16% |
| ATS | **1.0%/yr** | national MEPS/labelling tightening | −30% |
| RAS | **2.0%/yr** | aggressive harmonised MEPS, frontier push | −51% |

These are deliberately gentler than the US 3–3.5%/yr fleet rate because (a) our
tier is the *already-efficient* High_eff segment and (b) it stacks on the
composition lever. They are the primary knob — change `DRIFT_RATE` and rerun.

## What changed vs the frozen inject

| | Frozen (`fridge_leap_inject.csv`) | Drift (`fridge_leap_inject_drift.csv`) |
|---|---|---|
| Cell intensity | `kwh_unit` frozen 2014→2060 | `final_kwh_unit` drifts down (new col); `kwh_unit_2024` kept for reference |
| Efficiency | frozen per cell (High=100%) | ramps per year+scenario; 100% only at RAS 2060 High_eff |
| Useful Energy Intensity | per-size = 2024 High_eff kWh | per-size = 2024 High_eff × DF_ULT (lower; ultimate frontier) |
| Demand Cost O&M | `tariff × kwh_unit` (frozen) | `tariff × final_kwh_unit` (drifted) |
| Composition (ownership/size/eff shares) | — | **identical** |
| Unit Capacity (kW, RAS) | `unit_capacity_kw` = kwh_high÷8760 | **identical & fixed** — service capacity doesn't drift, only the electricity to deliver it (via Efficiency) |
| New columns | — | `drift_rate_pct_yr`, `drift_factor`, `kwh_unit_2024`, `final_kwh_unit` |

## Worked example — Indonesia, Small, High_eff

| Year | final_kwh (BAS/ATS/RAS) | Efficiency % (BAS/ATS/RAS) |
|------|--------------------------|-----------------------------|
| 2024 | 305 / 305 / 305 | 49.3 / 49.3 / 49.3 |
| 2035 | 290 / 276 / 249 | 51.8 / 54.5 / 60.3 |
| 2060 | 256 / 215 / 151 | 58.8 / 70.1 / 100.0 |

(Frozen baseline held all of these at 305 kWh and 100% efficiency.)

## Status

Parallel variant; baseline frozen file unchanged. Drift rates are documented
assumptions for expert review, not yet sign-off. Use this file when you want the
within-tier improvement story; use the frozen file for the conservative /
counterfactual baseline.
