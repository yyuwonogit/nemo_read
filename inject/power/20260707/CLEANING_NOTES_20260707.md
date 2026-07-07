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

---

## Post-inject calc fixes — 2026-07-07 (MaxCap-vs-ExoCap accounting)

The RAS calc failed on `Maximum capacity constraint is less than exogenous
capacity`. Full offline accounting (all techs x 10 AMS, RAS-effective,
layered over v0.67 raw + our 20260507 injects + v0.68/69 edits + this
payload; scripts `_probe_maxcap_accounting*.py`) found **4 violations** —
the payload's numeric caps colliding with additions/fleet the area already
carried (3 from our own 20260507 ATS additions inherited into RAS; 1 where
the existing fleet itself exceeds the cap):

| Region | Branch | Cap | ExoCap peak | Fixed expression (applied in UI + this CSV) |
|---|---|---|---|---|
| Cambodia | Wind Onshore | 1,500 | 3,349 | `Max(Exogenous Capacity[MW], 1500.0) ? IES/ADB` |
| Philippines | Small Hydro | 1,874 | 5,052 | `Max(Exogenous Capacity[MW], 1874.0) ? PH DOE` |
| Vietnam | Wind Onshore | 24,000 | 80,970 | `Max(Exogenous Capacity[MW], 24000.0) ? World Bank` |
| Malaysia | Large Hydro_MYPE | 3,100 | 3,495 | `Max(Exogenous Capacity[MW], 3100.0) ? IRENA` |

User applied the 4 expressions manually in the LEAP UI (2026-07-07); this
CSV (+ the cleaned sibling) updated to match — repo now mirrors the area.

**Note for the power team:** Large Hydro_MYPE confirms the modeller's
freeze-at-fleet instinct — the MYPE fleet trajectory (3,190 -> 3,495 MW)
exceeds the IRENA 3,100 cap; the Max() wrapper reconciles both readings.
Vietnam Wind Onshore's 24 GW cap vs the 81 GW additions trajectory in the
area (our 20260507 ATS layer) deserves a content review — the wrapper
unblocks the calc but the two numbers tell different build stories.

**LEAP syntax trap (cost one calc cycle):** `Max(1874.0, Exogenous
Capacity[MW])` FAILS — a numeric FIRST argument is parsed as a (year,
value) pair list ("Invalid value parameter ... for year 1874"). Reference
first, numeric second is the calc-proven form everywhere in this area.
