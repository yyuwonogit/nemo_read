# Commercial inject readiness — 2026-07-22

Payload: [commercial_canonical_20260722.csv](commercial_canonical_20260722.csv) (264 rows)
Build record: [BUILD_NOTES_20260722.md](BUILD_NOTES_20260722.md)

---

## 1. STATUS

**INJECT READY** — all 264 rows independently recomputed from the team payloads with
**0 value-fidelity errors**, all `(branch, variable, unit)` triples resolve byte-exact
against canon, and all three sealed gates pass with a live negative control.

Group 5 (AC borrow re-point) ships **0 rows** — the R5 route is not constructible; that is
an open item (§7), not a blocker on the 264 rows.

---

## 2. ROW COUNTS

| Group | Branch (leaf shown; prefix `Demand\Commercial\Other Commercial\End Use Projection\`) | Variable | Unit | Scenario | Rows |
|---|---|---|---|---|---|
| G1 B1 intensity | `<End Use>` (5 end uses × 10 AMS) | Commercial Uncalibrated Energy Intensity | kWh/m2 | *(blank = all)* | 50 |
| G2 B3 saturation | `<End Use>` (6 end uses × 10 AMS) | Activity Level | Saturation | *(blank = all)* | 60 |
| G3 B7 shares | `<End Use>\<Leaf>` | Activity Level | Share | Baseline Simulation | 40 |
| G3 B7 shares | `<End Use>\<Leaf>` | Activity Level | Share | AMS Target Scenario | 40 |
| G3 B7 shares | `<End Use>\<Leaf>` | Activity Level | Share | Regional Aspiration Scenario | 40 |
| G4 Refrig ratio | `Refrigeration\Efficient` | Final Energy Intensity | Kilowatt-Hour | *(blank = all)* | 10 |
| G6 building type | `Key\Commercial\Energy consumption per area\<Type>` | Activity Level | kWh/sqm | *(blank = all)* | 4 |
| G7 bug-7 | `Water Heating\Solar Heating` | Activity Level | Share | Regional Aspiration Scenario | 10 |
| G7 bug-7 | `Water Heating\Solar Heating` | Activity Level | Share | Carbon Neutrality_ Net Zero Scenario | 10 |
| | | | | **Total** | **264** |

Scenario split: 124 blank (apply to all) · 50 RAS · 40 AMS Target · 40 Baseline · 10 CN Net Zero.
Regions: 10 ASEAN (no Timor Leste, no Base Template). Thailand present: 27 rows.

**Remainder(100) drops — 60 series deliberately NOT written** (180 candidates − 60 = 120):
AC `Current Stock_Average` in Baseline · AC `Current Sales_Average` in AMS Target ·
AC `Efficient` in RAS · Refrigeration `Existing` in all three — 10 regions each.
Do not "restore" these; overwriting them would break family closure.

---

## 3. THE INJECT COMMAND — do not run yet

Stage A (the standard 4-scenario roster, 254 rows in scope):

```
python inject/commercial/inject_to_leap.py \
  --csv inject/commercial/20260722/commercial_canonical_20260722.csv \
  --scenarios "Current Accounts,Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" \
  --expect-area "<AREA NAME — confirm with user>" \
  --exclude-timor-leste \
  --fail-fast \
  --skip-dry-run -y
```

Stage B (the 10 `Carbon Neutrality_ Net Zero Scenario` bug-7 rows only — see §7 O2):

```
python inject/commercial/inject_to_leap.py \
  --csv inject/commercial/20260722/commercial_canonical_20260722.csv \
  --scenarios "Carbon Neutrality_ Net Zero Scenario" \
  --filter-variable "Activity Level" \
  --expect-area "<AREA NAME>" \
  --exclude-timor-leste --fail-fast --skip-dry-run -y
```

Blind mode is the inherited default and is **mandatory** here (every target is `Demand\`
or `Key\` — cached writes silently no-op, §A.20). `--fail-fast` is required with blind
mode: a non-existent FullName blocks indefinitely instead of erroring (§11.1).
`--exclude-timor-leste` is the explicit §A.18 choice — TL is off in LEAP calc and the
12-row supplement stays unpushed.

---

## 4. PRE-INJECT CHECKLIST

- [ ] **§A.9 confirmation, read back to the user before launch:** area name (must equal
      `--expect-area`), scenario currently in the LEAP dropdown, and that nothing else is
      mid-flight in LEAP.
- [ ] **LEAP → Settings → Regional → decimal separator = `.` (period).** Comma-decimal
      makes Interp round-trips ambiguous and fails readback even on correct values
      (§A.20.3). Injector exits 11 if it detects comma.
- [x] ~~**Live read #1 — `!EER` survival.**~~ **CLOSED 2026-07-23 by the v0.80 canon
      promotion — no live read needed.** v0.80 *deleted* the four residential
      `Projections\Air Conditioning\<tier>` branches and *added* `!EER[Btu/Wh]` on
      commercial's own four AC tiers (288 rows = 4 tiers × 6 scen × 12 reg), rewriting
      `Final Energy Intensity` on the three non-anchor tiers to the sibling-local form
      `Current Stock_Average:!EER[Btu/Wh] / !EER[Btu/Wh] * Current Stock_Average:Final
      Energy Intensity[kWh]`. The borrow is fixed in-model; Group 5 is a no-op and its
      120 route-C rows were dropped from the payload (see §7 O1).
- [ ] **Live read #2 — building-type baselines.** Canon Singapore is Office 185 / Hotel 218
      / Retailer 326 and Thailand Retailer `.350` at **v0.67**; live is v0.76+. Confirm the
      four target cells still hold the stale values before overwriting (§7 O3).
- [ ] **Live read #3 — Remainder(100) leaf placement.** The drop map was derived from the
      v0.67 4-scenario export. Confirm the designated Remainder leaf per scenario is still
      `Remainder(100)` in live before pushing; if a Remainder moved, the drop map moves with it.
- [ ] **Order:** Stage A, verify readback, then Stage B. Not one combined push.
- [ ] **Post-inject:** per-scenario readback must be `N EXACT, 0 NORMALISED, 0 FAIL`
      (delta payload — verify exhaustively, not sampled), plus a UI eye-test on one
      multi-scenario branch (e.g. Thailand `Refrigeration\Efficient`).

---

## 5. THAILAND

In scope, in the main canonical, 27 rows. Both halves of the coupled change ship together:
the team's B1 values were computed against the corrected control (106 → 197 kWh/m2), and
the `.350 → 350` Retailer fix is in the same payload. Input side is internally consistent
on landing.

**Flag:** Thailand's calibration factor was fitted to the **old** (typo'd `.350`) floor-area
control. When this lands, Thailand's *calibrated* demand shifts even though every input is
correct. That is the user's deferred cal work — not a blocker, not ours to fix (R3: CAL
untouched, no `Key\Cal\*` authoring). Expect the shift; do not treat it as an inject defect.

---

## 6. NOT AUTHORED — and why

| Not authored | Why |
|---|---|
| **23 canon-retained leaves** | Team disposition = retain. Their live expressions stand. |
| **7 Lighting residential borrows** | Retained by the team. (Note: v2 `b7_fuel_share_disposition.csv` lists **5**, not 7 — no output effect either way, 0 rows.) |
| **Group 5 — AC borrow re-point (3 leaves)** | R5's route is not constructible: `Demand\Residential\Projections\Air Conditioning_` has no `Useful Energy Intensity` variable, and where UEI does exist (size parents) it is tier-invariant, so the ratio is identically 1. Building it from `Efficiency` instead requires choosing a size/weighting = **content**, not ours. Canon expressions for all 3 leaves recorded verbatim in BUILD_NOTES §5.1. |
| **AC `Current Stock_Average:Final Energy Intensity`** | CAL-touching. R3 — CAL untouched. |
| **Lighting B1 intensity (10 rows)** | Withdrawn by the team in v2 (R10). B1 = 50 rows, not 60. Lighting B3 saturation **is** authored (10 rows) — correct, R10 only withdraws B1. |
| **`Key\Cal\*`** | R3 — never authored. |
| **`Demand\Commercial\Other Commercial\Historical`** | R9 — B1 is scenario-invariant; canon authors it in all 4 scenarios; Historical is not an authoring slot. |
| **Data_Center** | Out of payload scope. |
| **`Commercial Fuel Share_` (8 non-live CFS_ bugs)** | R1 — CFS_ is inert. Canon annotates it "Only used for water heating, cooking, other" and a 2,493,853-row corpus scan found zero expression-side references. Shares land on leaf `Activity Level`. Fixing an unreferenced variable changes nothing. |
| **26 other canon-retained leaves, Base Template, Timor Leste** | Out of scope / §A.18 exclusion. |

---

## 7. OPEN QUESTIONS

**O1 — Does `!EER` survive? — ANSWERED 2026-07-23 (v0.80 canon). Group 5 DROPPED.**
Both prior positions were half-right. R5 was right that the *residential* `!EER` is gone —
v0.80 deleted `Demand\Residential\Projections\Air Conditioning\{Best Practice,
Current_Sales Average, Current_Stock Average, Efficient}` outright (9 legacy residential
branches removed; only the `Air Conditioning_` / `Refrigeration_` trees survive). Canon
v0.67 was right that the variable existed — it was simply *relocated*: v0.80 adds
`!EER[Btu/Wh]` to commercial's **own** four AC tiers under
`Demand\Commercial\Other Commercial\End Use Projection\Air Conditioning\`, carrying real
per-region efficiency data (`10.6`, `11.58 ? EEP2015`, `2.7*3.413 ? assume by country`,
`26.9 ? ENERGY STAR (2023)`, `0.7*Current Sales_Average:!EER[Btu/Wh]`).

v0.80 also rewrote `Final Energy Intensity` on the three non-anchor tiers to the
sibling-local form (identical string, 72 rows each = 6 scenarios × 12 regions):

```
Current Stock_Average:!EER[Btu/Wh] / !EER[Btu/Wh] * Current Stock_Average:Final Energy Intensity[kWh]
```

Note the tier's own EER is a **bare self-reference** `!EER[Btu/Wh]` with no branch prefix.
The cross-sector dependency is gone; the model is already correct.

**Action taken:** the 120 route-C static-ratio rows (`0.55 / 0.70 / 0.90 * Current
Stock_Average:Final Energy Intensity[kWh]`, `src_csv=route_C_numeric_ratio`) were
**removed** from the payload — authoring them would overwrite correct canon with a cruder
and materially wrong approximation. Canon-implied ratios: `Current Sales_Average` is
structurally exactly **0.70** in every region (it is the algebraic inverse of
`Stock !EER = 0.7 × Sales !EER`) vs the staged 0.90 (+29% too high); `Efficient` 0.43–0.65
vs staged 0.70; `Best Practice` 0.24–0.38 (Thailand 0.43) vs staged 0.55 (+50–130%, wiping
out roughly half the best-practice efficiency gain). The staged statics were also
region-flat, discarding real per-country EER spread (Singapore 14.68 vs Cambodia 10.0).
The anchor tier `Current Stock_Average` was never authored — CAL-touching, out of scope
under R3. Payload 756 → 636 on this change.

Two data flags for the commercial team, neither blocking: **Thailand is near-degenerate**
— Best Practice EER `19` sits barely above Efficient `18.8`, so the tiers collapse to
0.4266 vs 0.4312 (~1% apart) where every other region shows ~2× separation; Thailand is
also the only region off the `26.9` ENERGY STAR figure. And **Vietnam's Efficient
(`5.3*3.413` = 18.09) exceeds every other region's**, possibly a units slip in the author
data. Both are expression content (§2.6) — flagging only.

*Hedge (§A.14):* Export Expressions does not distinguish an authored per-scenario
expression from one inherited from Current Accounts, so I cannot say from the workbook
whether BAS/ATS/RAS hold the FEI string explicitly or inherit it. Immaterial here — the
*effective* expression is correct in all three, so there is nothing to author either way.
Confirming authored-vs-inherited is **deferred: requires live-area read**.

**O2 — Push order for `Carbon Neutrality_ Net Zero Scenario`.**
The name is a valid canon scenario (roster ID 12) but sits outside the commercial 4-scenario
export, so the 124 blank-scenario rows were never proved invariant there. Pushing CN in the
same invocation would write those 124 rows into a scenario canon does not cover.
Recommendation: Stage A (4 scenarios) then Stage B (CN, bug-7 rows only). *Confirm.*

**O3 — Singapore Office = 218 is canon's Singapore *Hotel* value.**
Canon v0.67: Office 185 / Hotel 218 / Retailer 326. Team payload: 218 / 292 / 405. The Office
figure matching canon's Hotel figure smells like an upstream row transposition — but this is
**content**, so the file lands their numbers as given. One question back to the team before
push; no file change either way. *Changes what we do: only if they confirm a transposition.*

Nothing else. Value fidelity, path validity, unit correctness, region/scenario scoping,
Interp syntax, and all three gates are settled — those are not open.

---

*Files only. No LEAP COM touched, nothing injected.*
