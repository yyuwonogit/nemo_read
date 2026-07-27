# BUILD NOTES — bioenergy liquid-biofuel-chain canonical delta, 2026-07-22

**Deliverable:** [bioenergy_delta_20260722.csv](bioenergy_delta_20260722.csv) — **539 rows**, 12 columns
(`ams, branch, variable, expression, unit, fuel, source, note, src_csv, domain, data_confidence, scenario`).
Built by [build_blend_delta_20260722.py](build_blend_delta_20260722.py) (deterministic, re-runnable).

**Nothing here has been injected.** No LEAP COM call, no `calculatescenario`. Files only.

| Group | Authored | Blocked |
|---|---|---|
| G1 Blending ceiling | **20** | 0 |
| G2 Indonesia bioethanol floor (R4) | **2** | 0 |
| G3 Uniform 2025 start (R5) | **27** | 0 (33 no-ops skipped, 2 deferred to G2) |
| G4 Refinery Maximum Capacity | **70** | 10 (Cellulosic Rice Straw) + 5 lite-panel families (R1) |
| G5 Build rate (refinery + blending) | **90** | 2 fossil blending pseudo-techs (open symmetry item) |
| G6 Kill every `Unlimited` in scope | **330** | Base Template + Timor Leste rows (out of scope by rule) |
| G7 Feedstock resources | **0** (confirmation only) | 0 — no gap found |
| **Total** | **539** | |

Companion audits (same folder):
`_audit_ceiling_vs_floor.csv` (720 cells) · `_audit_group3_before_after.csv` ·
`_audit_unlimited.csv` · `_audit_maxcap_vs_installed.csv` · `_run_gates.py`

---

## 0. Gate results (all three sealed pre-flight gates, run on the output CSV)

```
gate 1  find_region_lock_violations   (§A.21 node lock + §A.23 base-branch lock) -> 0 violations
gate 2  validate_canonical_csv_expressions (§A.15 Interp separator)              -> PASS
gate 3  find_zero_existing_capacity_conflicts (§11.2b EC-zero vs HP-non-zero)    -> 0 conflicts
```

Gate 1's zero is **non-vacuous**: injecting a synthetic
`Vietnam / Transformation\Centralized Electricity Generation\Processes\Solar PV_MYPE`
row into a copy of the file makes the checker return exactly 1 violation. The delta
genuinely contains no `_MY*`/`_ID*` variants and no locked base-branch rows — consistent
with the brief's §4.12 finding that neither the Blending nor the Bio Production tree is
node-decomposed.

Every `Interp(...)` in the file uses **comma list-separator, period decimal** (§A.15).
No `Unlimited` literal is authored anywhere in the file.

---

## 1. Region alias map (applied to every team input)

`Brunei Darussalam → Brunei`, `Lao PDR → Laos`, `Viet Nam → Vietnam`.
Applied to `blend_ceiling_ramp.csv` (60/200 rows), `blend_observed_panel.csv`,
`build_rate_limit.csv`, and `biomass_supply_cap_rows.csv`. Timor Leste and
`Base Template` are never emitted — inject with `--exclude-timor-leste` (§A.18).

---

## 2. GROUP 1 — Blending ceiling (20 rows)

Branch (canon-verified against `current_expressions_transformation_slice_4scenarios.csv`):

| fuel | branch | variable | unit | scenario |
|---|---|---|---|---|
| Biodiesel | `Transformation\Diesel Blending\Processes\Biodiesel` | `Maximum_Share_of_Production` | `%` | Regional Aspiration Scenario |
| Bioethanol | `Transformation\Gasoline Blending\Processes\Ethanol` | `Maximum_Share_of_Production` | `%` | Regional Aspiration Scenario |

Two underscores, no spaces. The sibling floor on the same branch is
`Minimum Share of Production` (spaces, unit `Percent`) — do not conflate them.
RAS only: canon carries the variable in ATS/BAS too but both are `Optimize = No`, so
the bound is inert there; canon has **no Current Accounts row** for this variable and we
do not create one.

### 2.1 The conversion — worked example

```
E(v) = v·E_bio / ( v·E_bio + (1−v)·E_fossil ) × 100      v = volume FRACTION
  biodiesel   E_bio = 38.997   E_fossil = 43.330
  bioethanol  E_bio = 26.744   E_fossil = 44.8
```

Malaysia biodiesel, 2050, team ceiling **50.0 volume %**:

```
v      = 50.0 / 100                          = 0.50
num    = 0.50 × 38.997                       = 19.4985
den    = 0.50 × 38.997 + 0.50 × 43.330       = 41.1635
E(v)   = 19.4985 / 41.1635 × 100             = 47.3684 energy %
```

Check row: B7 → 6.3444 · B20 → 18.3673 · B50 → 47.3684 · E10 → 6.2203 · E20 → 12.9861.
These reproduce the reference table in the brief exactly.

**Provenance / staleness (§A.14).** `38.997 / 43.330 / 26.744 / 44.8` are read verbatim
off the canon `Minimum Share of Production` and `Process Share` expressions,
`inject/fossil/structure_handover_20260703/current_expressions_transformation_slice_4scenarios.csv`
lines 624 and 1980. That is a **v0.67 export**; live is v0.76+. The *structure* is canon
and stable; the *numeric LHVs inside the expression are expression content and may be
stale.* If the live area's Minimum Share of Production expression carries different
constants, this delta must be rebuilt with them — floor and ceiling must use the same
transform (§7.8 physics caveat: mass-basis LHVs on a volume fraction, deliberately NOT
corrected here, because correcting one side breaks floor/ceiling parity).

### 2.2 Resulting expression (Malaysia biodiesel shown in full)

```
Max(Minimum Share of Production, Interp(2025, 10.9312, 2026, 13.7056, 2027, 13.7056,
    2030, 13.7056, 2035, 18.3673, 2040, 27.8351, 2045, 37.5, 2050, 47.3684,
    2055, 47.3684, 2060, 47.3684))
```

Reference FIRST, `Interp()` LAST (R7 / §11.2e — a numeric first argument would be parsed
as a YEAR). All ten team anchors retained: dropping 2026/2027/2035/2045/2055 changes no
solved value today but would silently break under any future YEAR-set change.

### 2.3 Ceiling-below-floor cells — SURFACED, NOT BURIED

`_audit_ceiling_vs_floor.csv` evaluates every (region, fuel, year 2025–2060) cell under
the **R2 ramp reading** of `InterpFSY` (linear from (2024, 0) to the first anchor, flat
after the last).

**Against the PRE-delta canon floor: 61 inverted cells.**

| region / fuel | years | worst gap (energy-pp) |
|---|---|---|
| Indonesia / Bioethanol | 2025–2060 (36) | **24.395** |
| Malaysia / Biodiesel | 2028–2039 (12) | **14.129** |
| Thailand / Biodiesel | 2032–2037 (6) | 1.083 |
| Indonesia / Biodiesel | 2025 (1) | 5.727 |
| Laos / Biodiesel | 2025–2026 (2) | 1.503 |
| Laos / Bioethanol | 2025–2026 (2) | 1.002 |
| Vietnam / Biodiesel | 2025 (1) | 1.335 |
| Philippines / Biodiesel | 2025 (1) | 0.635 |

**Against the POST-delta floor (i.e. after G2 + G3 land): 27 inverted cells.**

| region / fuel | years | worst gap (energy-pp) |
|---|---|---|
| Malaysia / Biodiesel | 2026–2039 (14) | **14.129** |
| Thailand / Biodiesel | 2026–2037 (12) | 2.960 |
| Thailand / Bioethanol | 2026 (1) | 0.169 |

G2 clears Indonesia bioethanol entirely (36 → 0). G3 clears every 2025 start-year
artifact (Indonesia Bd, Philippines Bd, Vietnam Bd, Laos Bd/Be) but *widens* Malaysia and
Thailand biodiesel back to 2026, because pinning the 2025 anchor at the observed blend
raises the whole early ramp. The `Max()` wrapper handles all 27 — the injected ceiling is
never below the floor — but the model's effective ceiling in those cells is the **floor**,
not the team's wall. Those cells are where the team's physical objection and the canon
mandate genuinely disagree, and they are the shortlist for the next content round.

**Malaysia biodiesel is the largest surviving disagreement**: canon `InterpFSY(2030, 30)`
(B30 by 2030, National Energy Transition Roadmap) against a team wall of 15 vol% through
2030. That is a legal-instrument-vs-physics conflict, not a start-year artifact. It is
content, so it goes back to them — see §9.

---

## 3. GROUP 2 — Indonesia bioethanol floor lowered to the E20 wall (2 rows)

> ### ⚠ SCENARIO-NARRATIVE CHANGE, MADE ON EXPLICIT USER RULING R4
> This is not a data fix. It removes Indonesia's E50-by-2050 bioethanol pathway from the
> AEO-9 storyline. Anyone reading AEO-9 Indonesia ethanol results after this row lands is
> reading a different scenario than before.

| | |
|---|---|
| branch | `Key\Biofuel Blending Targets\Bioethanol` |
| variable | `Activity Level` — unit **`Volume %`**, **pass-through, NO energy conversion** |
| region | Indonesia |
| scenarios | AMS Target Scenario **+** Regional Aspiration Scenario (2 rows) |
| **before** | `InterpFSY(2025, 20, 2050, 50)` |
| **after** | `InterpFSY(2025, 0, 2050, 20)` |

**Shape justification.** Two constraints had to be met at once:

1. **The endpoint must fall to the wall.** R4's whole point is that leaving the floor at
   E50 makes the `Max(Minimum Share of Production, …)` wrapper drag the ceiling back up to
   37.4 energy% (= E50) and void the wall. Endpoint 50 → **20**, the team's stated
   physical wall.
2. **The 2025 start must be the observed achieved blend (R5).** The team's own panel
   (`blend_observed_panel.csv`, USDA FAS GAIN ID2025-0029 T7) records **0.0 %
   ethanol blend in Indonesia in every year 2015–2025**. Start → **0**.

The canon's *ramp shape* (start 2025, endpoint 2050) is preserved verbatim; only the two
values move. That makes this exactly **one reversible edit per scenario** — revert by
restoring `InterpFSY(2025, 20, 2050, 50)`.

Interior check against the team's own wall (`_audit_ceiling_vs_floor.csv`):
2030 floor 4.0 vol% vs wall 15 ✔ · 2035 8.0 vs 20 ✔ · 2040 12.0 vs 20 ✔ ·
2045 16.0 vs 20 ✔ · **2050–2060 20.0 vs 20.0 — EQUAL**.

> **Flag:** from 2050 the floor equals the ceiling exactly, so `Max()` yields lb = ub and
> the variable is *pinned*. That is feasible but has zero slack; any downstream rounding
> in the LEAP→NEMO export could make it a hair infeasible. If that is unacceptable, the
> minimal alternative is to move the endpoint out to 2060 (`InterpFSY(2025, 0, 2060, 20)`),
> which keeps the wall as an asymptote instead of a touch point. Flagged, not decided.

Also note: the ATS row is authored even though ATS carries `Optimize = No` and the bound
is inert there. It is authored because `Activity Level` also drives `Process Share`
(canon: the same Möbius expression appears as `Process Share` in ATS/BAS/CA), which *does*
determine the blend in the non-optimised scenarios.

---

## 4. GROUP 3 — Uniform 2025 start across BAS / ATS / RAS (27 rows)

**Anchor rule adopted:** the 2025 anchor is the value the team already carries in
`blend_ceiling_ramp.csv` at year 2025 with `binding_reason = observed_achieved_floor` —
which is byte-identical to the observed-achieved figure in `blend_observed_panel.csv`.
Using the team's own 2025 ceiling row as the floor anchor is not a coincidence of
convenience: it makes floor = ceiling at 2025 by construction, so **the alignment cannot
introduce a 2025 inversion.** Verified: zero 2025 inversions post-delta.

| region | Biodiesel 2025 | provenance | Bioethanol 2025 | provenance |
|---|---|---|---|---|
| Brunei | 0 | **no observation** | 0 | **no observation** |
| Cambodia | 0 | **no observation** | 0 | **no observation** |
| Indonesia | 34.1 | achieved 2025, High | 0.0 | achieved 2025, High |
| Laos | 0 | **no observation** | 0 | **no observation** |
| Malaysia | 12.0 | achieved 2026, **Low** ⚠ | 0 | **no observation** |
| Myanmar | 0 | **no observation** | 0 | **no observation** |
| Philippines | 3.3 | achieved 2025, High | 10.1 | achieved 2025, Medium-High |
| Singapore | 0 | **no observation** | 0 | **no observation** |
| Thailand | 8.2 | achieved **2020** peak ⚠ | 13.7 | achieved **2019** peak ⚠ |
| Vietnam | 0 | achieved 2024 = 0.0, High | 1.5 | achieved 2024, Low-Medium |

**The eleven no-observation cells** — Brunei, Cambodia, Laos, Myanmar, Singapore
(both fuels) **plus Malaysia bioethanol** — I verified this list independently against
`blend_observed_panel.csv`; it matches the brief's §5.7 count exactly. **Value used: 0.**
Justification: none of the six has a biofuel blending instrument in force
(`canon_mandate_parsed.csv` shows scalar `0` for all of them in every scenario), so
"observed achieved blend" is genuinely zero, not merely unmeasured. Every one of these is
a **NO-OP** — the canon already reads 0 in all three scenarios — so they contribute
**zero rows** to the delta. Only Laos is different: canon carries `InterpFSY(2030, 10)` in
ATS/RAS, which under the R2 ramp reading evaluates to 1.667 vol% at 2025 despite Laos
having no instrument before 2030; inserting the explicit `(2025, 0)` anchor corrects that
and removes the two Laos 2025 inversions the team's check declared clean.

**Two anchors carry provenance caveats we do NOT hide:**
* **Malaysia biodiesel 12.0** is a **2026-dated, Low-confidence, explicitly-constructed
  estimate** ("national volume-weighted avg NOT published") shipped by the team as a 2025
  anchor. Used because it is the only Malaysian achieved figure that exists, and because
  using it keeps floor = ceiling at 2025. Confidence on those rows: Medium (should arguably
  be Low).
* **Thailand 8.2 / 13.7** are the 2020 and 2019 **peaks**, not 2025 values (2024 actuals
  are 6.8 and 11.3). This is the team's stated peak rule; `binding_reason` should read
  `peak_observed_floor`, not `observed_achieved_floor` — a labelling defect already on the
  sendback list.

### Mechanics — what actually changed

The rewrite **sets or inserts the 2025 anchor and preserves every other anchor verbatim**;
post-2025 trajectories diverge by scenario exactly as they did before. Full before/after
for all 60 (region × fuel × scenario) cells is in `_audit_group3_before_after.csv`.
27 AUTHORED, 31 NO-OP (skipped — the delta doctrine says push only what changes),
2 DEFERRED-TO-G2.

Representative rows:

| region / fuel / scenario | before | after |
|---|---|---|
| Indonesia / Bd / RAS | `InterpFSY(2023, 35, 2025, 40, 2050, 50)` | `InterpFSY(2023, 35, 2025, 34.1, 2050, 50)` |
| Indonesia / Bd / BAS | `0` | `InterpFSY(2025, 34.1)` |
| Malaysia / Bd / ATS | `InterpFSY(2030, 30)` | `InterpFSY(2025, 12, 2030, 30)` |
| Philippines / Bd / BAS | `InterpFSY(2025, 2.5%)` | `InterpFSY(2025, 3.3)` |
| Thailand / Be / RAS | `InterpFSY(2050, 20)` | `InterpFSY(2025, 13.7, 2050, 20)` |
| Vietnam / Be / ATS | `Interp(2023,0, 2050, 20)` | `Interp(2023, 0, 2025, 1.5, 2050, 20)` |
| Laos / Bd / RAS | `InterpFSY(2030, 10)` | `InterpFSY(2025, 0, 2030, 10)` |

**Consequences that are real and deliberate.**
* BAS stops being "zero blend everywhere except Philippines 2.5%". Under R5 it becomes
  *frozen at the observed 2025 blend* — Indonesia B34.1, Malaysia B12, Thailand B8.2/E13.7,
  Philippines B3.3/E10.1, Vietnam E1.5, held flat. That is a materially different BAS
  narrative and materially more biofuel demand in the baseline. It is what R5 asks for.
* `Philippines / Bd / BAS` also fixes a latent defect: the canon expression was
  `InterpFSY(2025, 2.5%)` — a **stray `%` inside the argument list**. The new form drops it.
* Indonesia biodiesel now reads 35 (2023) → 34.1 (2025), a slight decline. The pre-2025
  anchors are historical *mandate* values while 2025 is now an *achieved* value; the mixed
  basis is preserved rather than silently rebased, because rewriting the historical anchors
  is outside R5's scope.

---

## 5. GROUP 4 — Refinery Maximum Capacity, re-wrapped (70 rows)

Source: the 70 rows accepted in `outbox/20260721/bioenergy_ruling/row_disposition_20260721.csv`
("INJECT — after scenario tag"), values from `biomass_supply_cap_rows.csv` inside
`mailbox/20260721/bioenergy_biomass_cap_handover_20260721.zip`. 7 processes × 10 AMS.

Re-authored under R7:

```
Max(Exogenous Capacity, Interp(2025, 623.952, 2030, 916.4295, …, 2060, 2534.805))
```
(Indonesia FAME Biodiesel shown.) Reference FIRST, `Interp()` LAST. This is the standard
resolution for LEAP's *"Maximum capacity constraint is less than exogenous capacity"* halt:
the committed fleet is always allowed and the cap binds optimiser builds only.

Values are the team's, **native unit, pass-through** — biodiesel `Million Gigajoules/Year`,
ethanol `Million Tonne Coal Equiv/Year`, both canon-confirmed. The adapter does not convert;
`unit_conversions._REGISTRY` is reference-only (the standing guide error).
Scenario tag: **RAS only** (canon carries `Maximum Capacity` in no other scenario).

**Hedge (§A.14).** I wrote the reference **bare** — `Max(Exogenous Capacity, …)` — not
`Max(Exogenous Capacity[Million Gigajoules/Year], …)`. Canon's calc-proven unit-tagged form
is `Max(Exogenous Capacity[MW], 1874.0)`; there is no canon precedent for a `[…]` token
containing spaces and a slash, and I will not fabricate one. Canon also uses bare
same-branch references freely (`Min(10.92, Maximum Availability)`, §11.2c). **If LEAP
rejects the bare form at inject, add the tag then — do not guess now.**

**Blocked:**
* **Cellulosic Rice Straw ×10 — NOT AUTHORED.** Branch does not exist
  (`row_disposition_20260721.csv`: *HOLD — pending structural create*). The modelling lead
  creates it manually mirroring the Cassava sibling; the team's values are accepted and
  should not be resent. Re-run this builder afterwards to pick them up.
* **5 lite-panel processes — NOT AUTHORED** (All Biomass, Anaerobic Digestion, CO2
  Utilization for Iron and Steel, Production from Hydrogen, Hydrogen). Excluded entirely by
  user ruling **R1**.

### 5.1 ⚠ Finding: the team's per-process capacity allocation contradicts canon's

`_audit_maxcap_vs_installed.csv`. The team allocated `Maximum Capacity` across processes by
**feedstock availability**; canon allocates installed capacity across the same processes by
**share of historical production**. They disagree, and in three cases the team's 2025 level
cap sits **below the existing fleet canon already carries**:

| region / process | team MaxCap 2025 | canon-implied installed 2023 | unit |
|---|---|---|---|
| Philippines / FAME Biodiesel | **0** | 15.599 | Million Gigajoules/Year |
| Thailand / Molasses | **0** | 1.075 | Million Tonne Coal Equiv/Year |
| Philippines / Molasses | 0.365 | 0.469 | Million Tonne Coal Equiv/Year |

Mirror-image cases exist too (Philippines CME Biodiesel: cap 19.5 → 78.0 against canon
share 0.0). The `Max(Exogenous Capacity, …)` wrapper means **the inject will not halt and
the fleet will not be stranded** — but a cap authored below the fleet it is supposed to cap
is a dead letter, and the underlying allocation disagreement is real. This is **content**,
so it goes back to the team (§9), not fixed here.

---

## 6. GROUP 5 — Build-rate limit (90 rows: 70 refinery + 20 blending)

`Maximum Capacity Addition`, RAS only. Source `build_rate_limit.csv` (20 national rows).
All three of the brief's blockers were solvable; **nothing in Part C is blocked.**

### (a) `installed(y−1)` is endogenous → pre-solved OFFLINE

The team's rule reads its own optimisation result. Unrolled deterministically, per process:

```
inst(fy−1) = installed_2023(national) × canon_share(process)
for y in 2025…2060:
    add(y) = 0                                   if y < first_feasible_year
           = MAX(one_train_floor, α × inst(y−1)) otherwise
    add(y) = min( add(y), max(0, MaxCap(y) − inst(y−1)) )       ← see (d)
    inst(y) = inst(y−1) + add(y)
```
with α = 0.2/yr, `one_train_floor` = 0.15 Mt/yr, `first_feasible_year` 2026 (brownfield) /
2028 (greenfield), all straight off `build_rate_limit.csv`. The result is emitted as an
explicit **36-anchor yearly `Interp(2025, …, 2060, …)`** — yearly because the underlying
path is geometric and 5-year anchors would linearise it wrongly.

**Extension I had to make, and its basis.** `first_feasible_year` is supplied *nationally*,
but the team defines it from the `basis` column: brownfield 2026 because *"an existing site
can be debottlenecked / a train added on the same permit"*, greenfield 2028 because of the
*"~3 yr FID → design → construction → commissioning"* lead. A process with **zero installed
base in that region has no existing site**, so it is greenfield by the team's own
definition regardless of the national label. Rule applied:
`fy(process) = national fy if installed(process) > 0 else max(national fy, 2028)`.
This is the team's definition applied consistently, not a new rule.

### (b) numeric-first `MAX()` → eliminated, not worked around

The team's `MAX(one_train_floor, α × installed)` transcribes to `Max(0.15, …)` — a numeric
first argument, which LEAP parses as a **YEAR** (`Invalid value parameter for year 0`, §11.2e).
Because the recursion is pre-solved (a), the `MAX()` is evaluated in Python and the emitted
expression is a **pure-numeric `Interp()` with no function call at all**. §11.2e cannot fire.

### (c) national Mt/yr → per-process — CANON's allocation rule, not an invented one

Canon already ships the idiom, on `Exogenous Capacity`, with canon's own comment
*"production capacity distributed between fuels according to shares of historical production"*:

```
Interp(<national>) * 10^6 * ConvFuelUnits(liter, gj, ethanol)
    * Interp(<per-feedstock historical production>)
    / Interp(<total historical production>)
```

I extracted the numerator/denominator `Interp()` pair from every canon RAS
`Exogenous Capacity` expression on the 7 processes and evaluated it at **2023** (canon's
last anchor). Where a process carries a non-zero expression with no allocation factor the
share is 1.0; where it carries `0` the share is 0.0. **Every family sums to exactly 1.00000**
— the canon invariant the brief names:

| region / family | shares (canon, 2023) |
|---|---|
| Indonesia / Biodiesel | FAME **1.0**, CME 0.0, POME 0.0 |
| Malaysia / Biodiesel | FAME **1.0**, CME 0.0, POME 0.0 |
| Philippines / Biodiesel | FAME **1.0**, CME 0.0, POME 0.0 |
| Thailand / Biodiesel | FAME **1.0**, CME 0.0, POME 0.0 |
| Indonesia / Bioethanol | Molasses **1.0**, Cassava 0.0, Corn 0.0, Sugarcane 0.0 |
| Philippines / Bioethanol | Molasses **0.85736**, Sugarcane **0.14264**, Cassava 0.0, Corn 0.0 |
| Thailand / Bioethanol | Molasses **0.78511**, Cassava **0.15804**, Sugarcane **0.05685**, Corn 0.0 |
| all other AMS | 0.0 on every process (no canon basis — see below) |

A **share of 0 does not mean the process can never be built.** It means the α×installed
*brownfield* term is 0; the `one_train_floor` term survives, because a single train is a
physical plant size, not a share of anything. So a zero-share process gets a greenfield
0.15 Mt/yr entitlement from 2028 — subject to (d). The six AMS with no canon basis at all
(Brunei, Cambodia, Laos, Myanmar, Singapore, Vietnam) fall out of the same arithmetic with
no special-casing.

### (d) the collision with the 70 accepted Maximum Capacity rows — RESOLVED

The brief (§7.4) flagged that a level cap and a rate cap on the same branch either
over-determine or make one a dead letter. Left alone, the compounding α term is also
absurd: Indonesia FAME would be permitted **1,300 Mt/yr of additions in 2060** (0.2 × 1.2³⁴
× 13.05), i.e. the rate cap becomes non-binding after ~2040 and buys nothing.

**Fix:** the unroll is clamped each year against the Group-4 accepted `Maximum Capacity`
trajectory — `add(y) ≤ max(0, MaxCap(y) − inst(y−1))`. The two caps now describe the same
path instead of contradicting it, and the clamp is not a new number: it is the level cap we
already accepted. Every Group-5 row's `note` field records how many of its 36 years were
clamped (typically 32–35). Indonesia FAME goes from a runaway geometric series to
`… 2026, 101.78, 2027, 122.14, 2028, 66.61, 2029→, 58.50 …` (Million GJ/Yr), tracking the
team's own level trajectory.

Consequence worth stating plainly: where the team set `Maximum Capacity = 0` (Brunei FAME,
Thailand Molasses, Philippines FAME …), the clamped build rate is **0 in every year**. That
is arithmetically correct — you cannot build into a zero cap — but it means those rows are
carrying the team's level decision, not a rate decision. See §5.1.

### Blending build rate (20 rows)

`Diesel Blending\Processes\Biodiesel` and `Gasoline Blending\Processes\Ethanol`,
`Maximum Capacity Addition` = **10000** Megawatt (was `Unlimited`), 10 AMS, RAS.
10,000 MW/yr = 10 % of the 100,000 MW level cap set in §7, i.e. the whole blending terminal
fleet can be rebuilt in ten years. Blending is a pass-through pseudo-tech
(`Process Efficiency = 100`); the cap exists to close the free-unbounded-build exploit
(R6), not to bind.

> **BLOCKED / OPEN SYMMETRY ITEM.** `Diesel Blending\Processes\Diesel` and
> `Gasoline Blending\Processes\Gasoline` still read `Maximum Capacity Addition = Unlimited`.
> The task scoped this row group to the two biofuel processes, and §A.2 says I author
> exactly that scope. But rate-limiting the biofuel leg of a `PercentShare`-dispatched
> module while leaving the fossil leg unlimited **biases the blend split toward fossil**.
> This needs a ruling before inject. Same shape as the Exogenous Capacity decision in §7,
> where the user's own wording ("the 4 blending pseudo-techs") settled it the other way.

---

## 7. GROUP 6 — Every remaining `Unlimited` in scope (330 rows)

Full inventory in `_audit_unlimited.csv` (branch, variable, unit, scenario, region, bound
direction, disposition). Summary:

| # | branch(es) | variable | bound | canon value | replacement | rows |
|---|---|---|---|---|---|---|
| 1 | 4 blending pseudo-techs (Biodiesel, Ethanol, Diesel, Gasoline) | `Exogenous Capacity` | **LOWER** → NEMO `ResidualCapacity` | `Unlimited` (all 4 scenarios, ALL 12 regions) | **`100000`** MW | **160** |
| 2 | 2 biofuel blending pseudo-techs | `Maximum Capacity` | UPPER | `Unlimited` (RAS) | `Max(Exogenous Capacity[MW], 100000)` | 20 |
| 3 | 2 biofuel blending pseudo-techs | `Maximum Capacity Addition` | UPPER | `Unlimited` (RAS) | `10000` MW — §6 | *(counted in G5)* |
| 4 | 7 refineries + 2 biofuel blending | `Maximum Production` | UPPER | `Unlimited` (RAS, Gigajoule) | **`10^10`** GJ | 90 |
| 5 | 7 refineries | `Maximum Capacity Addition` | UPPER | `Unlimited` (RAS) | build-rate `Interp()` — §6 | *(counted in G5)* |
| 6 | `Resources\Primary\{Corn, Molasses, Palm Oil Mill Effluent}` | `Maximum Imports` | UPPER | `Unlimited` (RAS, Gigajoule) | **`10^10`** GJ | 30 |
| 7 | `Resources\Primary\Corn` | `Maximum Production` | UPPER | `Unlimited` (ATS/BAS/CA, ALL 12) | the region's **own canon RAS expression** | 30 |
| 8 | 4 refineries | `Maximum Capacity` | UPPER | `Unlimited` — **Base Template only** | **not authored** — out of scope | 0 |
| 9 | `Resources\Primary\{Molasses, POME}` | `Maximum Production` | UPPER | `Unlimited` — **Base Template + Timor Leste only** | **not authored** — out of scope | 0 |

**Row 1 is the one to read carefully.** `Exogenous Capacity` is a **LOWER** bound: it
exports to NEMO as `ResidualCapacity`, and `Unlimited` becomes `1.0e+12` — a *forced floor*
of 10¹² that NEMO must carry in the LP basis. It is replaced with **`100000`, never `0`**.
On 2026-05-12 setting `EC = 0` on these exact four pseudo-techs took primal infeasibility
from 24 k to 4.6 M — **190× worse** (the p9 burn, CLAUDE.md §A.11). All four pseudo-techs
move together, in all four scenarios: an asymmetric change would distort the module's
`PercentShare` dispatch. The user's own R6 wording names "the 4 blending pseudo-techs", which
is why the fossil legs are in scope here and (per §6) unresolved for the rate cap.

> **Hypothesis, not proven (§A.13).** 1e12 → 100000 on a lower bound is a *large* change to
> the LP basis and it is the same family of edit that blew up in p9. It is directionally
> right (it removes a 10¹² coefficient that breaches CPLEX's ~10⁹ conditioning tolerance),
> but it has not been solve-tested. **Recommend pushing rows 1–2 as their own reversible
> delta and running one `calculatescenario` before anything else in this file goes in.**

**`10^10` as the finite GJ sentinel** (rows 4, 6): 10¹⁰ GJ = 10,000 PJ ≈ a third of total
ASEAN primary energy supply — generous enough to be non-binding against any plausible
national biofuel output, yet 100× below the 1.0e+12 export sentinel that pollutes CPLEX
conditioning (§11.2d). `10^n` is a canon-proven expression form (canon uses `* 10^6`
throughout the Exogenous Capacity expressions). Capacity remains the real bind.

**Row 7 invents nothing.** Corn `Maximum Production` is `Unlimited` in ATS/BAS/CA while RAS
already carries a finite per-region cap. Physical crop-supply potential is scenario-invariant,
so the minimal canon-derived fix is to mirror each region's own RAS expression into the other
three scenarios. Confidence Medium, and the value is v0.67 canon — **stale-labelled**.

**Rows 8–9 are deliberately unauthored.** Their only `Unlimited` occurrences are on
`Base Template` (a LEAP placeholder, not a real region — §11.1 exclude-always) and
`Timor Leste` (disabled in the calc; `--exclude-timor-leste`). They remain in
`_audit_unlimited.csv` so the record is complete.

**Result: after this delta there is no `Unlimited` left on any in-scope branch for any of
the 10 AMS in any scenario.**

---

## 8. GROUP 7 — Feedstock resources (0 rows — nothing missing)

Checked all 7 primary feedstocks for the 2026-05-19 POME-Import-Cost failure mode (a supply
cap without its companion cost row routes the LP through the unpriced region):

| feedstock | Maximum Production | Production Cost | Maximum Imports | Import Cost | verdict |
|---|---|---|---|---|---|
| Palm Oil | ALL (12) | ALL (12) | 10/10 | 10/10 | OK |
| Palm Oil Mill Effluent | 10/10 | 10/10 | ALL (12) | ALL (12) | OK |
| Coconut Oil | ALL (12) | ALL (12) | 10/10 | 10/10 | OK |
| Cassava | ALL (12) | ALL (12) | 10/10 | 10/10 | OK |
| Corn | ALL (12) | ALL (12) | ALL (12) | 10/10 | OK |
| Molasses | 10/10 | ALL (12) | ALL (12) | 10/10 | OK |
| Sugarcane | ALL (12) | 10/10 | 10/10 | 10/10 | OK |

**Every cap has its companion cost row, in every region.** No gap, so — per the delta
doctrine — **zero rows authored.** The only feedstock defects found are the `Unlimited`
entries, handled in Group 6 rows 6–7 and 9.

Out of scope by rule and therefore *not* re-audited: `Resources\Primary\{Arable, Perennial}`
and the Cultivation-process rows (CLAUDE.md §2.4 off-limits list).

---

## 9. What could NOT be authored — consolidated

| # | Item | Group | Reason |
|---|---|---|---|
| 1 | Cellulosic Rice Straw `Maximum Capacity` ×10 | G4 | **Branch does not exist.** Structural create is ours (modelling lead, mirror the Cassava sibling). Values accepted, do not resend. Re-run this builder after the create. |
| 2 | Cellulosic Rice Straw `Maximum Capacity Addition` ×1 family | G5 | Same — no branch to allocate onto. |
| 3 | 5 lite-panel processes (Charcoal\All Biomass, Domestic Biogas\Anaerobic Digestion, Methanol ×2, Ammonia) | G4/G6 | **Excluded entirely by user ruling R1.** |
| 4 | Fossil blending legs' `Maximum Capacity Addition` / `Maximum Capacity` / `Maximum Production` | G5/G6 | Task scoped the rate cap to the 2 biofuel processes (§A.2). Leaving the fossil legs unlimited biases a `PercentShare` module. **Needs a ruling.** |
| 5 | `Unlimited` on Base Template (4 refineries, `Maximum Capacity`) | G6 | Base Template is not a real region (§11.1). |
| 6 | `Unlimited` on Timor Leste (Molasses / POME `Maximum Production`) | G6 | TL disabled in calc; `--exclude-timor-leste` (§A.18). |
| 7 | Malaysia Bd (14 cells) / Thailand Bd (12) / Thailand Be (1) residual ceiling-below-floor | G1 | The `Max()` wrapper makes them safe to inject, but the *disagreement* is content. Goes back to the team. |
| 8 | Per-process capacity allocation conflict (§5.1, 3 regions) | G4 | Content. Goes back to the team. |
| 9 | Brunei biomass 0.01 TWh | — | Out of scope (this delta is the liquid chain only); still unresolved at 244× spread. |

---

## 10. Before inject — required checks

1. **§A.9 confirm with the user**: LEAP area name, scenario, nothing else mid-flight.
2. **Blind mode is MANDATORY** — 29 rows target `Key\…` branches. Cached
   `branch.Variable()` writes silently no-op on `Key\` and `Demand\` branches (§A.20).
   `--blind --fail-fast`.
3. **`--exclude-timor-leste`** (§A.18).
4. **LEAP → Settings → Regional → decimal separator must be `.`** before injecting (§A.20).
5. **Split the push.** Recommended order, each with its own readback:
   **(i)** G6 rows 1–2 (the 1e12 → 100000 `Exogenous Capacity` change) **alone**, then one
   `calculatescenario` — this is the p9-burn family and must be falsified before anything
   rides on it; **(ii)** G1 + G2 + G3 (the blend semantics); **(iii)** G4 + G5 + the rest
   of G6.
6. **Readback must be N EXACT / 0 NORMALISED / 0 FAIL** per scenario, plus a UI eye-test on
   one multi-scenario branch (`Key\Biofuel Blending Targets\Biodiesel`, Indonesia).
7. **The `Max(Exogenous Capacity, …)` bare-reference form (§5) is the one syntactic
   uncertainty in this file.** If it fails, the fix is a unit tag, applied at inject time
   with the live area's own unit string — not guessed here.
8. **Open gap the brief flagged and this delta does not settle:** is
   `Maximum_Share_of_Production` even *exported*? `MaxShareProduction` exists in the live
   NEMO build with **0 rows**. If LEAP never emits it, all 20 Group-1 rows are inert. The
   one-cell falsifying test in the brief (§2 step 1) is still the cheapest thing to run,
   and it should run before the 20-row push.
