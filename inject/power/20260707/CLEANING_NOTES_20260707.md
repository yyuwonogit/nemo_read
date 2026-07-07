# Cleaning notes — power_sendback_20260707.zip -> power_sendback_cleaned.csv (2026-07-07)

Source: mailbox/20260707/power_sendback_20260707.zip (9,534 rows) — the power
team's response to our v0.69 reconciliation package. Supersedes the earlier
cleaning of power_sendback_20260706.zip (9,450 rows -> 9,332 kept); that zip
reached this repo by miscommunication and was one revision stale. The team
never saw our first cleaning, so the structural drops below re-apply.

Kept: 9421. Dropped: 113. Re-imposed (LEAP-team truth held): 3.

## Dropped (same structural rules as the first cleaning, checked against canon)

- 78 rows — ghost-branch Small Hydro_MY* (Malaysia has no Small Hydro)
- 15 rows — Maximum Capacity slot does not exist in Current Accounts /
  Baseline Simulation / AMS Target Scenario (5 each)
- 15 rows — Maximum Capacity Addition slot does not exist in those same
  three scenarios (5 each)
- 5 rows — Endogenous Capacity slot does not exist in RAS

(The first cleaning's fifth class — 5 stale v0.67 values — is gone: the 0707
zip carries the v0.69-corrected expressions on all five keys.)

## Re-imposed per LEAP-team decision (2026-07-07) — we hold the truth

The 0707 zip switched three Malaysia RAS `Maximum Capacity` rows to the
modeller's freeze-at-existing-fleet expressions (`Exogenous Capacity[MW]`).
The LEAP-team decision keeps the IRENA resource-potential caps; restored
verbatim from the first cleaning:

- Solar PV_MYPE: `324482.9` (IRENA Malaysia Energy Transition Outlook 2023)
- Solar PV_MYSB: `12517.1` (same source)
- Large Hydro_MYPE: `3100.0` (same source)

The power team's own RECONCILIATION_HANDLING_20260707.md flags exactly these
as a divergence awaiting arbitration and keeps their sourced values "ready to
re-adopt" — this decision IS the arbitration answer; communicate it back in
the next send so their register closes.

## Adopted from the 0707 zip (improvements over the first cleaning)

- +84 Singapore rows: the base-branch fleet newly readable in v0.69 (real
  Gas Combined Cycle 10,114.71 MW and Solar PV 1,211.18 MW in 2024, explicit
  zeros on ten others) + the standard Exogenous Capacity formula quartet on
  9 branches that previously had none.
- The 3 Singapore Current Accounts Existing Capacity corrections (Fuel Oil
  2023=763.6/2024=13.60, Gas Turbine 180/260, Waste 393/345.20) now carried
  in-file instead of dropped-as-stale.
- Solar PV_MYPE/_MYSB Capacity Additions (RAS) as the v0.69 `Interp(2030,…)`
  cumulative trajectories (arithmetically identical to the team's earlier
  `Add(2031,…)` schedules, which remain in Baseline/ATS).
- `Exogenous Capacity` unit label normalised to `Megawatt` on all rows —
  canon: LEAP's unit string is PER-VARIABLE, verified against the canon
  slice + v0.68/v0.69 harvests: Existing Capacity / Capacity Additions /
  Capacity Retirement = `MW`; Exogenous / Endogenous / Maximum Capacity /
  Maximum Capacity Addition = `Megawatt`.
- Trailing `~~~~~~~` artifact stripped from Indonesia Coal Supercritical
  Existing Capacity (would fail a strict expression parse).
- 27 Malaysia main-node deactivation rows re-sourced to cite the Malaysia
  decomposition rule (were copy-pasted Indonesia citations).

## Carried over from the first cleaning (still true in this file)

- MY base Gas Turbine RAS cap `Exogenous Capacity[MW]` (we modified 0 -> this
  on 2026-07-07; the team's 0707 zip independently adopted the same).
- Solar PV_MYSR Maximum Capacity (RAS) = 20,000 MW (LEAP-team decision
  2026-07-07; the 0707 zip adopted it, adding `? Placeholder, pending
  re-source`).
- Cap-vs-fleet validation: no new numeric caps entered vs the validated
  first cleaning (the only new rows are Singapore fleet/exogenous rows and
  formula caps), so the 2026-07-07 full-Interp-evaluation result — zero caps
  below a real fleet — carries over.

## Validation on the rebuilt files

- Region-lock: 0 violations on both cleaned + canonical (find_region_lock_violations).
- Interp separator pre-flight: 0 bad rows on the canonical.
- pytest test_region_lock + test_interp_separator: pass (sole failure is the
  pre-existing, documented inject/power/20260608/patched_targets.csv item).
