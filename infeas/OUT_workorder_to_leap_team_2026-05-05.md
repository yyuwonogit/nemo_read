# Work Order — Power Sector LEAP-input Fix Cycle

**Date: 2026-05-05**
**Branch: `20260505_Power_YY`**
**To: LEAP-injection team**
**From: YY (Power-sector author)**

## Purpose

This is the data we need from LEAP-side to author input fixes for the
issues raised in your `v0.35 → v0.36` handover plus a few structural
anomalies surfaced from the joined ATS/BAS result CSVs you sent. The
joined result CSVs alone are insufficient — they only cover 2025–2060
(no Current Accounts visibility), they show post-optimisation values
not input expressions, and they may be aggregating across branches in
ways that mask root-level structural problems.

For each request below we state:
- **From LEAP probe** — what we need read from the LEAP-side area
  (`aeo9_v0.36`) via COM (Branch Path, Variable, Region, Scenario,
  Expression text, `Variable.DataUnitText`).
- **From NEMO sqlite** — what we need from the NEMO results database
  (the sqlite the optimisation writes to before LEAP roll-up).
- **Why** — which issue this resolves.

Deliver as a single zipped folder dropped in `.mailbox/` containing
one CSV per request below (named per the heading), or attach as
appropriate.

---

## Request 1 — Indonesia ROOT-level (non-node-specific) branches for the 7 affected families

**Issue resolved:** Double-counting between Indonesia node-specific
(`_IDxx`) plants and root-level non-node-specific plants for Biomass,
Biogas, Coal Subcritical, Diesel, Gas Combined Cycle, Gas Turbine,
Gas Engine. Cannot determine from joined CSVs because v0.36 already
zeroed root-level Existing Capacity in BAS.

### From LEAP probe (`probe_indonesia_root_level.csv`)

For each branch path that matches the ROOT-level pattern (i.e., NO
`_IDxx` suffix) under `Transformation\Centralized Electricity Generation
\Processes\<plant>` for the 7 families:

| Column | Description |
|---|---|
| `branch_path` | Full LEAP path |
| `variable` | Variable name (Existing Capacity, Historical Production, Maximum Capacity, Capacity Additions, Capacity Retirement) |
| `region` | LEAP region (Indonesia) |
| `scenario` | One of: Current Accounts, BAS, ATS |
| `expression` | Raw `Interp(...)` or constant text — verbatim from LEAP |
| `unit` | `Variable.DataUnitText` for that (branch, variable) pair |

Family list: Biomass, Biomass Gasification, Biomass Other, Biogas,
Coal Subcritical, Diesel, Gas Combined Cycle, Gas Turbine, Gas Engine.

### From NEMO sqlite (optional confirmatory)

For Indonesia root-level branches in those 7 families:
- Pre-optimisation `vproductionbytechnologyannual` (or equivalent)
  showing Historical Production input for years 2010–2024
- Post-optimisation Production for 2025+ — to confirm whether
  root-level branches are actually contributing or fully zeroed

---

## Request 2 — Indonesia v0.36 workaround scope

**Issue resolved:** "Several Centralized Electricity Generation
processes in Indonesia had Historical Production but no Exogenous
Capacity" (your handover note). Need the explicit list to author
proper Existing Capacity expressions for both Current Accounts and
BAS.

### From LEAP probe (`probe_indonesia_v035_workaround.csv`)

The change-log you mentioned in your handover. Exact format flexible,
but minimally:

| Column | Description |
|---|---|
| `branch_path` | Full LEAP path of each affected process |
| `original_expression_current_accounts` | The Current Accounts Existing Capacity Interp BEFORE you removed the "drop to 0 in 2022" portion |
| `current_expression_current_accounts` | The Current Accounts expression NOW (post-fix) |
| `current_expression_BAS` | The BAS Existing Capacity expression NOW (you set to 0) |
| `historical_production_2022` | The Historical Production value for 2022 |
| `historical_production_2023` | Same for 2023 |
| `historical_production_2024` | Same for 2024 |
| `notes` | Any context on why each process needed the patch |

### From NEMO sqlite

- Per-process Production for 2022–2024 from `vproductionbytechnologyannual`
  (input side, not solver output) to confirm the Historical Production
  values that triggered the infeasibility.

---

## Request 3 — Malaysia: which branches actually exist, and their full input expressions

**Issue resolved:** Malaysia's joined CSV shows essentially no Existing
Capacity (`Coal Ultrasupercritical` 3,395 MW is the only non-zero
branch). Cross-AMS attribution leak (e.g., `Solar PV_IDSA` appearing
under `ams=Malaysia`) is masking what's really there. Need to know
whether Malaysia is genuinely under-modelled or whether the joined
CSV's pivot is hiding things.

### From LEAP probe (`probe_malaysia_branches.csv`)

For every branch path under `Transformation\Centralized Electricity
Generation\Processes\` that resolves to Malaysia (i.e., the LEAP-side
`Region.Name` resolves to Malaysia, not just appearing in a Malaysia
result row):

| Column | Description |
|---|---|
| `branch_path` | Full LEAP path |
| `variable` | All variables (8 expected: Capacity Additions/Retirement, Existing Capacity, Maximum Capacity, Historical Production, Capacity Factor, Process Cost, Process Maximum Production) |
| `region` | LEAP region (Malaysia) |
| `scenario` | Current Accounts, BAS, ATS |
| `expression` | Raw expression text |
| `unit` | `Variable.DataUnitText` |

**Filter request:** please clarify in a `notes` column whether the
branch is intended as a Malaysia-specific node or a global default
that Malaysia inherits.

### From NEMO sqlite (`nemo_malaysia_capacity_export.csv`)

Pre-solver capacity vector for Malaysia from
`vrescapacityresult` (or equivalent existing capacity table) for
2010–2024 (Historical) — so we can see what NEMO sees as Malaysia's
existing fleet vs what LEAP exposes via Existing Capacity.

---

## Request 4 — Malaysia node-split assessment

**Issue resolved:** Your note implies splitting Malaysia into
Peninsular / Sabah / Sarawak nodes (3 grids) like Indonesia is split
into 4. Need to know whether this split structure exists in v0.36 or
needs to be created.

### From LEAP probe (`probe_malaysia_node_branches.csv`)

| Column | Description |
|---|---|
| `branch_path` | Any branch path containing `_MY` suffix or `Peninsular`, `Sabah`, `Sarawak` substring |
| `variable` | All variables |
| `expression` | Raw expression |
| `unit` | DataUnitText |
| `node_intent` | If branch was created with a node intent, name the node (Peninsular / Sabah / Sarawak); else "unknown" |

If no node-split branches exist, answer "no node-split branches
found" — that confirms a structural-create round will be needed
before we can author per-node values.

### From NEMO sqlite

- If NEMO has a region/zone split for Malaysia, list the zones and
  their per-technology capacity. Otherwise confirm "Malaysia is single
  region in NEMO".

---

## Request 5 — Solar PV input expressions (Malaysia + Indonesia + ASEAN-wide)

**Issue resolved:** "Overestimated projection of Solar in Peninsular"
— need to see the input expression that drives Solar PV growth so we
can identify whether the overestimate is in Capacity Additions limit,
Maximum Capacity expression, capacity factor, or the dispatch logic.

### From LEAP probe (`probe_solar_pv_inputs.csv`)

For every branch path containing `Solar PV` (any region, any node
suffix):

| Column | Description |
|---|---|
| `branch_path` | Full path |
| `region` | LEAP region |
| `variable` | Capacity Additions, Maximum Capacity, Existing Capacity, Capacity Factor, Process Cost, Pollutant Loadings |
| `scenario` | Current Accounts, BAS, ATS |
| `expression` | Raw expression text |
| `unit` | DataUnitText |

### From NEMO sqlite (`nemo_solar_pv_capacity_trajectory.csv`)

For Solar PV branches under each region:
- `vresnewbuiltcapacity` per year 2025–2060 (decadal OK)
- Compare against the `Capacity Additions` result we already have

This lets us see if the optimiser is over-building Solar PV vs the
input cap, which would point to a Maximum Capacity ceiling being
mis-set vs the optimiser hitting a corner solution.

---

## Request 6 — Thailand Module-level Energy Generation expression

**Issue resolved:** Thailand `Centralized Electricity Generation`
Module-level Energy Generation = −5.2 × 10¹⁷ GJ in 2025 (joined ATS
CSV). Process-sum is positive (~2 × 10¹⁰ GJ ≈ 5,700 TWh). Module value
is corrupt.

### From LEAP probe (`probe_thailand_module_expression.csv`)

| Column | Description |
|---|---|
| `branch_path` | `Transformation\Centralized Electricity Generation` (Module level) |
| `variable` | All variables on this Module branch (Costs of Production, Energy Generation, Power Generation, Curtailed Energy Production, Pollutant Loadings) |
| `region` | Thailand |
| `scenario` | Current Accounts, BAS, ATS |
| `expression` | Raw expression — especially anything in 2025 |
| `unit` | DataUnitText |

If the Module is supposed to be a roll-up (sum of children), confirm
whether LEAP computes that automatically or expects an explicit
expression.

---

## Request 7 — Module vs Process roll-up logic + cross-AMS leak

**Issue resolved:** Joined CSV shows that Module-level Energy
Generation does NOT equal the sum of Process-level Energy Generation
for any AMS. Indonesia Module is 401 × 10⁹ GJ (≈ 111,000 TWh —
physically impossible) vs Process sum 3.4 × 10⁹ GJ (≈ 947 TWh —
order-of-magnitude correct).

Also, Indonesia branches with `_IDxx` suffix appear under
`ams=Malaysia` etc. in the joined CSVs — need to confirm whether
this is a real LEAP-side mis-attribution or just a roll-up artifact
of how the joined CSV is built.

### From LEAP probe + NEMO sqlite — small clarifying note (no CSV needed)

Please answer in your reply (1-2 sentences each):

1. Does LEAP compute Module-level Energy Generation as a sum of
   children, or does it require an explicit expression? Does Module
   value get summed across all AMS or only the AMS named in the row?

2. In the joined CSV, when a row has `ams=Malaysia` and a branch like
   `Solar PV_IDSA`, is this:
   (a) A real LEAP-side row where the branch is registered as
       Malaysia-region (a true mis-attribution), OR
   (b) An artifact of how the joined CSV pivots region × branch (i.e.,
       Malaysia row has 0 value for branches that don't apply, but
       still gets listed)?

3. What's the difference between Module-level Energy Generation =
   401 × 10⁹ GJ and Process-sum = 3.4 × 10⁹ GJ for Indonesia 2025?
   Where do the extra 397 GJ × 10⁹ come from?

---

## Request 8 — Scenario differentiation diagnostic for Coal Supercritical

**Issue resolved:** Coal Supercritical 2050 Energy Generation is
≈ 1.81 × 10¹⁰ GJ in BOTH ATS and BAS — looks indistinguishable on
the dominant fuel.

### From LEAP probe (`probe_scenario_diff_coal.csv`)

For `Transformation\Centralized Electricity Generation\Processes\Coal
Supercritical` and `Coal Supercritical CCS`:

| Column | Description |
|---|---|
| `branch_path` | Full path |
| `variable` | Capacity Additions, Maximum Capacity, Capacity Retirement, Existing Capacity |
| `region` | All regions |
| `scenario` | Current Accounts, BAS, ATS |
| `expression` | Raw expression — specifically looking for whether ATS has any decarbonisation lever (capacity cap, retirement schedule, cost penalty) different from BAS |

If ATS expressions are identical to BAS for these branches, that's
the answer — ATS isn't actually steering the dispatch differently
for coal, and we'd need to add scenario-specific expressions.

### From NEMO sqlite

Confirm whether NEMO is reading distinct scenario inputs for Coal
Supercritical or treating them as identical.

---

## Request 9 — Per-variable unit probe (replace `inferred` with `probed`)

**Issue resolved:** All 11,000 rows in joined CSVs have
`unit_source = inferred`. We need probed units to be confident in any
numerical comparison or cross-sector consistency check.

### From LEAP probe (`probe_units_per_variable.csv`)

For all 8 variables (Capacity Additions, Capacity Retirement, Costs
of Production, Curtailed Energy Production, Energy Generation,
Existing Capacity, Pollutant Loadings, Power Generation):

| Column | Description |
|---|---|
| `variable` | Variable name |
| `branch_sample` | One representative branch path (any) |
| `data_unit_text` | The probed `Variable.DataUnitText` value |
| `consistent_across_branches` | TRUE if all branches return the same unit, FALSE if any branch differs |
| `branches_with_different_units` | List any (branch, unit) outliers |

This catches edge-case branches where LEAP stores a different unit
than the family default (e.g., a single Solar PV branch in TJ instead
of GJ, etc.).

---

## Summary table — what each issue needs

| # | Issue | LEAP probe | NEMO sqlite |
|---|---|:---:|:---:|
| 1 | Indonesia root-level branches | ✓ | optional |
| 2 | Indonesia v0.36 workaround scope | ✓ | ✓ |
| 3 | Malaysia branches that exist + expressions | ✓ | ✓ |
| 4 | Malaysia node-split assessment | ✓ | ✓ |
| 5 | Solar PV input expressions (overestimation diag) | ✓ | ✓ |
| 6 | Thailand Module Energy Generation expression | ✓ | – |
| 7 | Module vs Process roll-up logic + cross-AMS leak | – | – (Q&A) |
| 8 | Scenario differentiation for Coal Supercritical | ✓ | ✓ |
| 9 | Per-variable unit probe | ✓ | – |

---

## Format for delivery

Drop a zipped folder at `.mailbox/power_workorder_response_<date>.zip`
containing the 7 CSVs (one per request 1-6, 8, 9 — request 7 is just
Q&A in the cover note). Each CSV uses the column schema specified
above.

If any column is hard to extract or expensive to compute, say so in
the cover note — we can iterate.
