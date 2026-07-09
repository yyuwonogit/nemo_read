# Batch-1 intake validation — power team delta (2026-07-08)

Received `mailbox/power_batch1_delta_20260708.zip`, routed here. Validated
against OUR gates (structure = ours; content = theirs, §A.23). **Overall:
accept, inject-ready except one held row. Not injected yet — batches with
the team's next round + our dispatch delta (user directive).**

## Gate results (nemo_read gates, not the team's own validator)

| File | Rows | Region/base lock §A.21/23 | Separator §A.15 | Max() trap §11.2e | Neg add/ret | Unlimited | Verdict |
|---|---|---|---|---|---|---|---|
| power_batch1_delta | 326 | 0 | 0 | 0* | 0 | 0 | **CLEAN** |
| power_batch1b_endogenous | 48 | 0 | 0 | 0 | 0 | 0 | **CLEAN** |
| wpj_run2_dispatch_reversal | 18 | 0 | 0 | 0 | 0 | 0 | **CLEAN** |
| wpf_gas_ceiling (fossil team) | 10 | 0 | 0 | 0 | 0 | 0 | **route to fossil** |
| stranded_cost_test_row | 1 | 0 | 0 | 0 | 0 | 0 | **HOLD — see below** |

\* 18 `Min(60, Maximum Availability)` rows are the §11.2c availability must-run
floors (60 = CF%, not a year) — the calc-proven safe form, NOT the §11.2e trap.

## Delta hygiene (verified true deltas, not full re-sends)
- main: 94 CHANGED + 232 NEW-KEY vs the shipped baseline, **0 same-value** rows.
- batch1b: 48 NEW-KEY (Endogenous Capacity in ATS/BAS — never RAS, correct).
- run2: 18 NEW-KEY (MU restore). Scenario routing correct throughout
  (MaxCap/MCA only in RAS; Endogenous only ATS/BAS).

## Two structural flags — both RESOLVED as valid (§A.22 region-invariance)
54 (main) + 19 (batch1b) rows author capacity vars on copper-plate base
branches absent from our region-scoped extracts (e.g. `Singapore Coal
Subcritical: Maximum Capacity`, `Cambodia Coal Subcritical: Endogenous
Capacity`). **Not structure errors:** `Maximum Capacity / MCA / Endogenous
Capacity / Capital Cost` are all confirmed on the `Coal Subcritical_ID*`,
`Diesel_ID*`, `Gas Combined Cycle_ID*` variants in canon; structure is
region-invariant (§A.22), so the slot exists on the base tech too — the team
is populating a cap that was simply never authored before (extract emits only
populated rows = a lower bound). Definitive confirmation is the blind inject's
fail-fast, which resolves each branch+var against live LEAP.

## HOLD — `stranded_cost_test_row.csv` (do NOT inject as-is)
Row authors `Coal Subcritical_IDJW | **Capital Cost** = 614,245,472 | unit
"U.S. Dollar"`. Problems:
1. The `variable` is **Capital Cost, not Stranded Cost** — Capital Cost is
   NOT optimization-inert (it drives investment); their "inert probe" premise
   fails for this variable.
2. Unit `U.S. Dollar` (absolute) contradicts Capital Cost's canon unit
   `thousand USD/MW`. Injected, it sets IDJW capital cost to 6.1e8
   thousand-USD/MW — poisons a live Indonesia coal node and the next calc.
Their intent (probe the LEAP cost-report unit basis) is fine, but the vehicle
is wrong. **Question back:** did you mean the `Stranded Cost` variable (which
IS inert / never reaches NEMO, per our QA answer #4)? If yes, re-author on
`Stranded Cost`; if you truly need a Capital-Cost read, do it on a throwaway
scratch branch, never a live fleet node.

## Actions taken
- **WO-A1 DONE:** stripped the 6 Unmet Load processes (12 rows, ATS+BAS) from
  our held `dispatch_rule_fullcapacity_delta.csv` (448 → 436). Their catch was
  correct — our MeritOrderDispatch→FullCapacity filter had swept them in;
  flipping Unmet Load to FullCapacity would dispatch phantom unserved energy.
  Backup: `.bak_pre_unmet_exclude_20260708`.

## Open asks triaged (from WORK_ORDER)
- **Ours (LEAP inject side):**
  - A1 Unmet Load exclusion — DONE.
  - A2 Indonesia diesel/gas retirement-cliff overwrite — handled by idempotent
    inject IF their Capacity Retirement rows cover the same keys; verify at
    joint-inject (flag if any old `Interp(2035,0,…)` key is left uncovered).
  - C5 v2 results re-export (unit stamps / IDs / module filter / IDKA-2060) —
    on our TODO, deliver with next results harvest.
- **Modeller / not us:** C3 Hydrogen-module branch export, C4 transmission
  topology, D6 retirement copy-paste cleanup on the live model, D7 co-firing
  placeholder preservation (inject writes, never prunes — confirmed safe).
- **Fossil team:** `wpf_gas_ceiling_proposal_*` — route, not a power inject.
- **Acknowledged:** B — the 8 deliberate sourced supersessions (Malaysia IRENA
  Solar/Hydro caps, Indonesia MEMR geothermal 5460/9370/180) are present and
  will be kept; Malaysia IRENA-caps arbitration confirmed (we already applied
  the Max() wrapper on Large Hydro_MYPE).

## Follow-up checks (2026-07-08, post-intake)

### Q1 — Stranded Cost input location (settles the held row)
`Stranded Cost` IS a real variable on **every Centralized generation process
branch** (452 occurrences in canon), unit **`U.S. Dollar`** (absolute, no
scale/per), currently all `0`. So the team's probe value (614M, unit
`U.S. Dollar`) has the CORRECT unit for Stranded Cost — they just wrote it to
the wrong `variable` column (`Capital Cost`). **Fix = one column edit:**
`variable: Capital Cost → Stranded Cost`, same branch
(`Coal Subcritical_IDJW`), same value/unit. Then it is inert (never reaches
NEMO), unit-correct, and safe to inject as the probe. Ball back to them to
confirm before we author it.

### Q2 — Negative Exogenous Capacity sweep, ATS + BAS (all techs × 10 regions)
RAS Exo is guarded `Max(…, 0)`; ATS/BAS Exo is the **bare**
`Existing + Additions − Retirement` — so it CAN go negative. Swept the fully
layered state (raw v0.67 + injected baseline + batch-1 + batch-1b):
`_probe_negative_exo_atsbas.py`. Result: **7 negatives, all ATS, 0 in BAS.**

| Scen | Region | Tech | First <0 | Min (MW) |
|---|---|---|---|---|
| ATS | Indonesia | Gas Turbine_IDEast | 2023 | −3,984 |
| ATS | Indonesia | Gas Turbine_IDJW | 2046 | −756 |
| ATS | Indonesia | Gas Turbine_IDKA | 2023 | −3,888 |
| ATS | Indonesia | Gas Turbine_IDSA | 2025 | −2,997 |
| ATS | Malaysia | Coal Subcritical_MYPE | 2036 | −62 |
| ATS | Malaysia | Coal Subcritical_MYSR | 2030 | −8,710 |
| ATS | Malaysia | Fuel Oil | 2025 | −63 |

**Provenance: NOT introduced by batch-1** — the batch touches none of these
techs' Exo building blocks in ATS/BAS. They are **pre-existing in the injected
baseline** (the team's OWN prior v0.69 sendback): a large `Capacity Retirement`
schedule (e.g. Gas Turbine_IDEast `Add(2023, 515.1, 2024, 422.8, …)`) against a
bare `Existing = Value(2024)` (~344 MW) — retiring more than exists. This is
exactly the "pre-existing gas/diesel retirement cliff" the WO item A.2 flags.
Dormant so far because our solved run was RAS-only; **it WILL break/corrupt the
moment ATS is calculated** — which batch-1b (ATS/BAS endogenous) + the dispatch
experiment intend to do.

**FIX APPLIED (user directive 2026-07-08 — "simple accounting, make it 0"):**
`exo_negative_fix_ats_delta.csv` — 7 rows, ATS Exogenous Capacity for the 7
affected techs rewritten from the bare `Existing + Additions − Retirement` to
`Max(Existing Capacity[MW] + Capacity Additions[MW] − Capacity Retirement[MW],
0)`. This is the accounting floor: where retirement exceeded the fleet, Exo
clamps to exactly 0 (never negative) — identical NEMO ResidualCapacity to a
retirement-schedule cap, but robust and matching the RAS idiom. Verified: the
negative sweep re-run with the fix layered returns **0 negatives** (was 7;
OK 1466 → 1473). Gate-clean (region-lock 0, separator 0). Joins the joint
inject. BAS untouched (0 negatives there); the InterpFSY-form direct Exo
authorings (114, unrelated to the retirement-cliff class) are offline-
unevaluable but cannot go negative via this mechanism.

## Next step
When the team signals the batch is final (and the fossil team's gas ceiling +
any batch-2 rows arrive), merge: `power_batch1_delta` + `power_batch1b` +
`wpj_run2` (per experiment design) + our 436-row dispatch delta → one inject
against `aeo9_v0.69`, blind + fail-fast, readback-verify, recalc. Hold the
stranded-cost row pending their clarification.
