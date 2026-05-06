# Anomaly diagnostic — Power BAS + ATS results, v0.36

**Date: 2026-05-05**
**Source CSVs: `joined_BAS.csv` (10,328 rows) + `joined_ATS.csv` (11,000 rows)**
**SQLite: `infeas/NEMO_25 11.sqlite` (v0.36)**

Phase 1 of the cross-team fix workflow. Pure offline analysis from the
joined CSVs (Probe A × Probe B). No LEAP probe yet, no SQLite param read
yet.

Each anomaly carries a **Where to act** stamp specifying exactly the
LEAP UI surface the power team will touch (variable + branch + scenario
+ region), or whether it auto-resolves from a sibling fix, or whether
it needs a policy decision before any UI work. Action classes used:

  - **LEAP UI: edit expression** — change a numeric / formula in an
    existing input variable's Expression box.
  - **LEAP UI: add scenario branch** — add a scenario-specific override
    (e.g., ATS-only Capacity Additions) where currently the BAS
    expression is inherited verbatim.
  - **LEAP UI: add region scoping** — fix a branch whose region
    membership is mis-set (causing cross-AMS value leaks).
  - **LEAP UI: author missing data** — populate Existing Capacity /
    Historical Production for branches currently empty.
  - **Policy decision required** — human picks between named options
    before LEAP work starts.
  - **Auto-resolves with [Anomaly ID]** — no separate action; gets
    fixed when the linked anomaly's fix lands.
  - **DOCUMENT only** — likely-intended LEAP semantic; capture the
    behaviour in fix-spec but no LEAP edit.

---

## A1 — Thailand Module Energy Generation = −5.2241 × 10¹⁷ GJ (years 2025-2035)

### Evidence
| year | BAS Module | ATS Module | Process sum (BAS) |
|---|---|---|---|
| 2025 | **−5.2241 × 10¹⁷** | **−5.2241 × 10¹⁷** | 2.28 × 10¹⁰ |
| 2030 | **−5.2241 × 10¹⁷** | **−5.2241 × 10¹⁷** | 2.64 × 10¹⁰ |
| 2035 | **−5.2241 × 10¹⁷** | **−5.2241 × 10¹⁷** | 3.05 × 10¹⁰ |
| 2040 | 3.58 × 10¹⁰ | 3.33 × 10¹⁰ | 3.56 × 10¹⁰ |
| 2045+ | sane (~10⁸-10⁹) | sane (~10⁸-10⁹) | ~10⁸-10⁹ |

### Where to act
**LEAP UI: edit expression** — Module-level `Energy Generation`
expression on `Transformation\Centralized Electricity Generation`,
region=Thailand, scenarios=Current Accounts (and BAS+ATS if scenario-
specific overrides exist there). Fix the corrupt numeric in the
2025-2035 portion. Single expression edit if the value is held on
Current Accounts; up to 3 edits if BAS and ATS each carry a separate
override of the bug.

### Why
The exact same constant `−5.2241 × 10¹⁷` appears verbatim in **both
BAS and ATS** for **2025, 2030, 2035**. From 2040 onward, the Module
value matches the Process sum (≈ 3.5 × 10¹⁰).

The constant `5.2241` doesn't decode to a known sentinel
(`INT64_MIN/1e18 = −9.22`; `−2⁶³` doesn't match either). It's almost
certainly a corrupt explicit Module-level expression — likely an
`Interp(2025, X, 2040, 0, ...)` where `X` was typo'd in scientific
notation (e.g., `5.2241e+17` instead of `5.2241e+10` or similar).

### Phase 2 probe target
- Branch: `Transformation\Centralized Electricity Generation` (Module, BT=2)
- Variable: `Energy Generation` (Module-level expression — IF one exists)
- Region: Thailand
- Scenarios: Current Accounts, BAS, ATS

### Hypothesis to test in Phase 4
After fix, Thailand 2025-2035 Module Energy Generation should equal the
Process sum (≈ 2.3-3.1 × 10¹⁰ GJ). If post-fix values still differ from
Process sum but are no longer −5.2 × 10¹⁷, root cause is Module-level
roll-up logic (see A2) — a separate fix.

---

## A2 + A3 — Module ≠ sum-of-Processes for any AMS; Indonesia 110× ratio

### Evidence
| ams (BAS, year=2025) | Module EG | Proc Sum | ratio |
|---|---|---|---|
| Brunei | 2.36e+8 | 2.32e+8 | 1.02 |
| Vietnam | 6.18e+8 | 5.51e+8 | 1.12 |
| Timor Leste | 2.13e+6 | 1.78e+6 | 1.20 |
| Singapore | 2.45e+8 | 1.93e+8 | 1.27 |
| Laos | 4.40e+7 | 3.43e+7 | 1.28 |
| Myanmar | 4.47e+7 | 3.38e+7 | 1.32 |
| Cambodia | 3.45e+6 | 2.60e+6 | 1.33 |
| Philippines | 2.17e+8 | 1.56e+8 | 1.39 |
| **Malaysia** | **2.68e+10** | **1.29e+10** | **2.09** |
| **Indonesia** | **2.99e+11** | **2.72e+9** | **110.17** |
| Thailand | (A1 corrupted) | 2.28e+10 | n/a |

ATS shows the same pattern with slightly different magnitudes (Indonesia
117×, Malaysia 2.14×).

### Where to act
Split into two distinct actions:

- **A2 (most AMS, 1.0-1.4× ratios): DOCUMENT only.** Likely an
  intended LEAP semantic (Module-level Energy Generation is its own
  expression, not auto-rolled-up from Processes). Capture the 20-30%
  overcount in fix-spec but no LEAP edit; confirm in Phase 2.
- **A3 (Indonesia 110× = 297× too high): LEAP UI: edit expression**
  on `Transformation\Centralized Electricity Generation` Module-level
  `Energy Generation`, region=Indonesia. Phase 2 needs to identify
  whether the Module reads from a separate corrupt expression (similar
  to A1) or from a leaked Demand-side aggregate.
- **Malaysia (2.09× ratio): LEAP UI: edit expression** likely too —
  more modest fix; could be a single-branch double-counting cleanup
  rather than a corrupt constant.

### Why
- Indonesia: Module = 299e9 GJ ≈ 83,000 TWh; Process sum = 2.7e9 GJ ≈
  760 TWh; Indonesia's actual 2024 demand ≈ 310 TWh. Module value is
  ~270× larger than physical reality.
- The IN-file's "double-counting" hypothesis (root vs `_IDxx`) at most
  explains a 2× overcount, **not 110×**. So Indonesia Module is
  either reading from a separate top-level expression that includes
  Demand-side values mistakenly, OR affected by the same kind of
  corrupt-constant bug as Thailand A1 (different magnitude).
- Malaysia 2.09× is the suspicious "double-counting" candidate. With
  no node-split structure in v0.36 yet, the 2× could reflect a single
  Malaysia branch counted twice under different scopes.

### Phase 2 probe targets
- Branch: `Transformation\Centralized Electricity Generation` (Module)
- Variable: `Energy Generation`
- Regions: Indonesia, Malaysia (priority); all others (confirmation)
- Scenarios: Current Accounts, BAS, ATS

### Hypothesis to test in Phase 4
After fix, Indonesia Module Energy Generation in BAS-2025 should drop
from 299×10⁹ GJ to within [2.5, 4.0]×10⁹ GJ (matching Process sum).
Malaysia Module 2025 should drop from 2.68×10¹⁰ to ≤ 1.5×10¹⁰. If
either stays elevated, look for a top-level Demand-side leak instead.

---

## A4 — Cross-AMS attribution leak (verified REAL)

### Evidence
**Solar PV_IDSA** (Indonesia Sumatera grid branch) appears under three
ams in joined_BAS.csv with **distinct, non-zero values**:

| ams | year=2025 value | unit | should be |
|---|---|---|---|
| Indonesia | 6.51 × 10⁶ | GJ | this region's value (correct) |
| **Malaysia** | **94.0 × 10⁶** | GJ | **0** (foreign branch) |
| **Thailand** | **142.0 × 10⁶** | GJ | **0** (foreign branch) |

Compare against `Coal Subcritical_IDSA` which behaves correctly (only
appears under ams=Indonesia, value 3.84M).

Compare against `Tidal` (tech-template, expected per-region values) —
all 11 regions have distinct non-zero values, which is correct.

ATS shows similar leak: `Solar PV_IDSA` → Malaysia 96.5M, Thailand
148.6M.

### Where to act
**LEAP UI: add region scoping** on each leaking _IDxx branch — set
the branch's region membership to Indonesia-only (and any specific
node it represents). Currently the affected branches have no
region-scoping filter; they need either a Region.Add() property set
to Indonesia, or to be moved under a region-scoped parent branch in
the LEAP tree.

Scope: ~10-30 branches across the 7 affected families (Phase 2 audit
will produce the exact list). NOT all _IDxx branches are affected
(Coal Subcritical_IDSA scopes correctly, so the fix is per-branch,
not blanket).

### Why
The `_IDSA` branches are NOT respecting region scope. `Solar PV_IDSA`
returns the LARGEST value in foreign-region context (Thailand 142M ≫
Indonesia 6.5M). This is not a probe artifact —
`safe_value(branch.Variable("Energy Generation"), 2025)` after
`leap.ActiveRegion = "Thailand"` is returning a real number that's
distinct from Indonesia's read.

Most likely root cause: the `Solar PV_IDSA` branch in v0.36 was
authored without proper region-scoping (no Region.Add() or equivalent
filter), so when LEAP evaluates `Energy Generation` in any
ActiveRegion context, it returns a value derived from the
Centralized-Elec-Gen-wide aggregate visible to that region.

Scope: 259 Thailand + 183 ATS rows in joined_BAS show this pattern.
First 10 distinct branch suffixes: Biogas_IDJW, Biogas_IDKA,
Biogas_IDSA, Biomass Other_IDEast, Biomass Other_IDJW, Biomass
Other_IDKA, Biomass Other_IDSA, Coal Subcritical_IDEast, Coal
Subcritical_IDJW, Coal Subcritical_IDKA. The leak is not limited to
Solar PV — it affects most _IDxx branches, but Coal Subcritical_IDSA
(checked above) doesn't exhibit it. Inconsistent across the family —
needs branch-by-branch audit in Phase 2.

### Phase 2 probe targets
For each _IDxx branch identified as leaking (filter joined_BAS.csv for
ams != Indonesia AND value != 0 AND branch contains _ID):
- Read region-scoping property if accessible via COM
- Read `Variable.Expression` to see if it has explicit region filter
- Compare with non-leaking branches like Coal Subcritical_IDSA

### Hypothesis to test in Phase 4
After fix, every _IDxx branch should have value = 0 (or no row) under
all foreign-ams entries. If any non-Indonesia row for an _IDxx branch
still returns non-zero, the region scoping fix didn't take.

---

## A5 — Coal Supercritical 2050: BAS = ATS at TOTAL only, not per-region

### Evidence

| ams | BAS Coal Super 2050 (GJ) | ATS Coal Super 2050 (GJ) | delta | pct |
|---|---|---|---|---|
| Brunei | 3.16e+5 | 1.11e+5 | −2.06e+5 | −65% |
| Cambodia | 1.62e+6 | 8.55e+5 | −7.69e+5 | −47% |
| **Indonesia** | 5.72e+6 | **1.69e+7** | **+1.12e+7** | **+195%** |
| Laos | 7.10e+6 | 6.87e+6 | −2.25e+5 | −3% |
| Malaysia | 1.81e+10 | 1.81e+10 | +3,038 | 0.0% |
| Myanmar | 3.34e+6 | 3.76e+6 | +4.19e+5 | +13% |
| Philippines | 1.41e+7 | 1.69e+6 | −1.24e+7 | −88% |
| Singapore | 1.33e+7 | 8.72e+6 | −4.61e+6 | −35% |
| Thailand | 3.47e+7 | 4.60e+7 | +1.14e+7 | +33% |
| Vietnam | 2.55e+7 | 2.53e+6 | −2.30e+7 | −90% |
| **TOTAL** | **1.8159e+10** | **1.8141e+10** | −1.83e+7 | **−0.1%** |

### Where to act
**LEAP UI: add scenario branch** — author an ATS-specific override on
`Transformation\Centralized Electricity Generation\Processes\Coal
Supercritical`, region=Malaysia, scenario=ATS. Variables to differentiate:
typically `Capacity Additions` and/or `Capacity Retirement` to express
the decarbonisation lever in ATS. Phase 2 needs to confirm whether the
current ATS expression is verbatim-identical to BAS (case 2 below) or
intentionally same (case 1).

If it's case 1 (intended), no LEAP edit; just **DOCUMENT** in the fix-
spec why ATS doesn't differentiate this tech for Malaysia.

### Why
The IN file claim "≈ 1.81 × 10¹⁰ GJ in BOTH ATS and BAS" only looks at
TOTAL — which IS coincidentally similar. Per-region:

- Indonesia DOES shift dramatically (+195% in ATS)
- Vietnam DOES shift (−90%)
- Philippines (−88%), Cambodia (−47%), Brunei (−65%) all reflect ATS
  putting LESS Coal Supercritical in those countries
- Malaysia is the dominant total contributor at 1.81 × 10¹⁰ GJ — and
  in Malaysia the BAS-vs-ATS delta IS essentially zero (3,038 GJ out
  of 1.8e+10).

So ATS IS steering Coal Super differently per-region — but Malaysia
(where Coal Super is the biggest absolute number) shows no
differentiation. The real question: why doesn't ATS reduce Malaysia
Coal Supercritical (where it's >99% of the total)?

Two possibilities:
1. Malaysia's Coal Supercritical is the same in BAS and ATS by design
   (no decarbonisation policy on this tech in ATS for Malaysia).
2. Malaysia ATS expressions are silently identical to BAS for this tech
   (missing scenario differentiation).

### Phase 2 probe target
- Branch: `Transformation\Centralized Electricity Generation\Processes\Coal Supercritical`
- Variable: `Existing Capacity`, `Maximum Capacity`, `Capacity Additions`,
  `Capacity Retirement`
- Region: Malaysia
- Scenarios: BAS, ATS — read both expressions, diff them. If identical
  → confirms case 2.

### Hypothesis to test in Phase 4
If ATS adds a decarbonisation lever for Malaysia Coal Super:
- Malaysia Coal Super 2050 ATS Energy Generation should drop to ≤
  1.5 × 10¹⁰ GJ (≥17% reduction)
- Total BAS = ATS coincidence breaks; ATS total drops by 1-3 × 10⁹

---

## A6 — Indonesia 7-family root vs _IDxx (LEAP team's structural concern)

### Evidence
For all 7 affected families (Biomass, Biomass Other, Biogas, Coal
Subcritical, Diesel, Gas Combined Cycle, Gas Turbine, Gas Engine) in
Indonesia BAS:

| family | root EG 2025 | root EG 2030 | root EG 2050 | _IDxx EG 2025 |
|---|---|---|---|---|
| Biomass | 0 | 0 | 0 | 0 |
| Biomass Other | 0 | 0 | 0 | 3.24e+6 |
| Biogas | 0 | 0 | 0 | 0 |
| Coal Subcritical | 0 | 0 | 0 | 1.11e+7 |
| Diesel | 0 | 0 | 0 | 2.28e+9 |
| Gas Combined Cycle | 0 | 0 | 0 | 1.11e+8 |
| Gas Turbine | 0 | 0 | 0 | 2.29e+8 |
| Gas Engine | 0 | 0 | 0 | 2.27e+7 |

ATS pattern is similar with similar magnitudes.

### Where to act
**Policy decision required** first (Option A or B per IN file), THEN
**LEAP UI: author missing data**:

- **Option A** (per-node from day 0): edit Existing Capacity +
  Historical Production on the 8 `_IDxx` branches (per family per
  node) for Current Accounts to carry the 2010-2024 historical data.
  Root branches stay 0 throughout. ~32 expression edits (8 families ×
  4 nodes × 1 variable, plus historical production).
- **Option B** (root in historical, zero in projection): edit Existing
  Capacity on the 8 root-level branches in Current Accounts to carry
  2010-2024 historical data, then drop to 0 from 2025. _IDxx branches
  unchanged. ~8 expression edits.

Current state IS Option B's projection half (root = 0 in 2025+) — but
the historical half hasn't been authored, so 2010-2024 is missing
entirely from Indonesia for these families.

### Why
The IN file documents that LEAP team set root-level Existing Capacity
to 0 in BAS for these processes — exactly the resulting CSV pattern.
The remaining decision is **where the historical 2010-2024 data
should live** (root or per-node), and that's the modeller's choice
per the IN file's stated alternatives.

### Phase 2 probe targets
For each of the 8 root-level branches:
- Branch: `Transformation\Centralized Electricity Generation\Processes\<family>`
  (no _IDxx suffix)
- Variable: `Existing Capacity`, `Historical Production`,
  `Capacity Additions`, `Capacity Retirement`
- Region: Indonesia
- Scenarios: Current Accounts (HISTORICAL ← key gap), BAS, ATS

### Hypothesis to test in Phase 4
After applying Option A or B (depending on policy decision):
- **Option A** (split historical to nodes from day 0): root branches stay
  0 in projection AND in historical. _IDxx branches should now have
  Historical Production / Existing Capacity values for 2010-2024 in
  Current Accounts.
- **Option B** (root in historical, zero in projection): root branches
  carry historical 2010-2024 values in Current Accounts, then drop to 0
  from 2025+. _IDxx branches contribute only from 2025+ (already the
  case).

---

## A7 — Malaysia coverage: only 1 branch carries Existing Capacity

### Evidence
- Malaysia has **57 distinct Process branches** under Centralized
  Electricity Generation in BAS (59 in ATS)
- Of those, **ONLY ONE** has non-zero Existing Capacity in any year:
  `Coal Ultrasupercritical` at max EC = 3,395 MW

That's structurally impossible — Malaysia's actual 2024 generation
fleet includes ~30+ techs across coal, gas, hydro, biomass, solar.

### Where to act
**LEAP UI: author missing data** — populate Existing Capacity (and
Historical Production for 2010-2024) on the ~56 currently-empty
Malaysia Process branches under `Transformation\Centralized
Electricity Generation\Processes\`. Variables to author per branch:
`Existing Capacity` (Current Accounts), `Historical Production`
(2010-2024), and Maximum Capacity / Capacity Additions for projection.

Significant data-entry effort (~56 branches × 3-5 variables per
branch). Phase 2 will produce the exact branch list and identify which
already have Maximum Capacity but missing Existing Capacity (smaller
fix) vs branches that are entirely empty (larger fix).

### Why
Either:
1. Most Malaysia branches genuinely have 0 Existing Capacity in v0.36
   (i.e., the area is severely under-modeled for Malaysia), OR
2. Malaysia branches carry their Existing Capacity under a different
   variable name than what Probe A captured (less likely — we read 8
   standard variables), OR
3. Malaysia branches' Existing Capacity expressions ARE non-zero but
   `Variable.Value(year)` returns 0 due to a region-scoping issue
   (similar mechanism to A4 cross-AMS leak, but in reverse — branch
   exists only as Indonesia/Thailand-scoped).

The cross-AMS leak (A4) shows that several "Solar PV_IDSA" type
branches DO appear under ams=Malaysia with non-zero `Energy Generation`
values. But those are the leaked Indonesia branches — not real Malaysia
capacity. Real Malaysia branches (e.g., `Coal Subcritical` no suffix,
`Solar PV` no suffix) likely have 0 Existing Capacity because v0.36
hasn't yet authored Malaysia historical data.

### Phase 2 probe targets
- All 57 Malaysia Process branches under Centralized Electricity Gen
- Variable: `Existing Capacity`, `Historical Production`,
  `Maximum Capacity`, `Capacity Additions`, `Capacity Retirement`
- Region: Malaysia
- Scenarios: Current Accounts, BAS, ATS

### Hypothesis to test in Phase 4
After fix:
- Malaysia should have ≥10 branches with non-zero Existing Capacity in
  2020-2025
- Total Malaysia generation in joined_BAS for 2025 should rise from
  current 1.29 × 10¹⁰ GJ (Process sum) to a value consistent with
  Malaysia's actual 2024 power demand × ~1.15 reserve factor

---

## A7b — Malaysia Solar overestimate (linked to A4)

### Evidence
Malaysia 2050 ALL-Solar BAS = 1.19 × 10⁸ GJ ≈ **33 TWh**. ATS = 43 TWh.
Of that:
- Real Malaysia branches: `Solar CSP` 0.86M GJ, `Solar Floating` 0.83M GJ
  (both ≈ 0.5 TWh combined — tiny)
- **`Solar PV_IDSA`**: 117M GJ in BAS / 153M in ATS — 99% of the total

### Where to act
**Auto-resolves with A4** — no separate LEAP edit. The "Malaysia
Solar overestimate" the IN file flagged is precisely the cross-AMS
leak: `Solar PV_IDSA` (Indonesia Sumatera) is leaking into Malaysia
at high values. Once A4's region-scoping fix lands on the leaking
_IDxx branches, the leaked values disappear and A7b's Malaysia Solar
total drops to its real value (~0.5 TWh from Solar CSP + Solar
Floating combined).

### Hypothesis to test in Phase 4
After A4 fix, Malaysia Solar 2050 should drop to ~0.5 TWh combined
(Solar CSP + Solar Floating only), because the leaked IDSA value
disappears.

---

## Summary table — where each fix lives

| ID | Description | Where to act | Effort | Phase 2 needed |
|---|---|---|---|---|
| A1 | Thailand Module EG = −5.2e17 (2025-2035) | LEAP UI: edit expression (Thailand Module Energy Generation) | 1-3 expression edits | YES — read Module expression text |
| A2 | Module 1.0-1.4× Process for most AMS | DOCUMENT only (likely intended LEAP semantic) | none | YES — confirm semantic |
| A3 | Indonesia Module 110× Process sum | LEAP UI: edit expression OR locate the leak source | 1-N edits TBD | YES — read Module expression + trace any Demand-side reference |
| A4 | _IDxx cross-AMS leak | LEAP UI: add region scoping on each leaking branch | ~10-30 branch-level region settings | YES — read region-scoping attribute branch by branch |
| A5 | Coal Super Malaysia BAS≡ATS | LEAP UI: add scenario branch (ATS-specific) on Malaysia Coal Super, OR DOCUMENT if intended | 1 scenario override | YES — diff BAS vs ATS expressions |
| A6 | Indonesia 7-family historical missing | Policy decision (Option A or B), then LEAP UI: author missing data | A: ~32 edits / B: ~8 edits | YES — read Current Accounts expressions |
| A7 | Malaysia coverage = 1 of 57 branches | LEAP UI: author missing data on ~56 Malaysia branches | LARGE (~56 branches × 3-5 vars) | YES — full Malaysia audit |
| A7b | Malaysia Solar 33-43 TWh inflation | Auto-resolves with A4 | none | NO |

---

## Phase 2 probe scope (consolidated)

Distinct (branch, variable, region, scenario) tuples to read:

| Branch pattern | Variables | Regions | Scenarios |
|---|---|---|---|
| `Transformation\Centralized Electricity Generation` (Module) | Energy Generation, Costs of Production | Indonesia, Malaysia, Thailand | Current Accounts, BAS, ATS |
| `…\Processes\<7-family>` (root, Indonesia) | Existing Capacity, Historical Production, Maximum Capacity, Capacity Additions, Capacity Retirement | Indonesia | Current Accounts, BAS, ATS |
| `…\Processes\<7-family>_IDxx` (Indonesia node-specific) | Same | Indonesia | Current Accounts, BAS, ATS |
| `…\Processes\Coal Supercritical` | Existing Capacity, Maximum Capacity, Capacity Additions, Capacity Retirement | Malaysia | BAS, ATS |
| `…\Processes\<every Malaysia branch>` (~57) | Existing Capacity, Historical Production, Maximum Capacity, Capacity Additions, Capacity Retirement | Malaysia | Current Accounts, BAS, ATS |
| `…\Processes\Solar PV_IDSA` (and other leaking _IDxx) | Region-scoping attribute (if available via COM); Existing Capacity expression | (every region the branch leaks to) | Current Accounts, BAS, ATS |

Estimated Phase 2 probe runtime: **~15-20 min** for the targeted
branches (~150 (branch, variable, scenario) reads × ~3 sec each).

---

## What we still don't know (gaps for Phase 2 to close)

1. The actual LEAP-side expression for Thailand Module Energy Generation
   in 2025-2035 (the −5.2e17 source).
2. Whether Indonesia Module reads from a separate top-level expression
   or computes via roll-up from a different source than Processes.
3. Whether `Solar PV_IDSA` (and similar) has a Region.Add or filter
   property at the branch-definition level that's been mis-set.
4. The current Existing Capacity expressions for Malaysia's 56 "empty"
   branches.
5. The Coal Supercritical Malaysia expression in BAS vs ATS — are they
   verbatim identical strings, or different but evaluating to the same
   number?
6. The Indonesia Current Accounts (2010-2024) historical data shape —
   is it on root, on _IDxx, or missing entirely?

Phase 2 probe should close all six.
