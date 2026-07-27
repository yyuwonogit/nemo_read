# Commercial canonical — build notes, 2026-07-22

Builder: [build_commercial_canonical_20260722.py](build_commercial_canonical_20260722.py)
Output: [commercial_canonical_20260722.csv](commercial_canonical_20260722.csv) — **264 rows**

Ownership principle applied throughout: **we own STRUCTURE and UNITS, the team
owns CONTENT.** Every value below is the team's, taken as given — no rescaling,
no re-derivation, no "improvement". Our work was landing each value on a
canon-verified branch / variable / unit / region / scenario in valid LEAP syntax.

Cite-or-hedge (§A.14): the structure and units cited here come from
`inject/commercial/structure_handover_20260703/` (**v0.67-era**). The live area is
**v0.76+**. Structure is canon and stable by default (§2.6); **canon VALUES quoted
below may be stale** and are labelled as such where they matter.

---

## 0. Inputs actually consumed

| File | Group | Rows in | Rows out |
|---|---|---|---|
| `comm2/end_use_intensity.csv` | 1 | 50 | 50 |
| `comm/end_use_saturation.csv` | 2 | 60 | 60 |
| `comm/fuel_shares.csv` | 3 | 6,840 (= 10 reg × 3 scen × 38 yr × 6 leaf-slots) | 120 |
| — (canon shape) | 4 | — | 10 |
| — | 5 | — | **0 — not authored, see §5** |
| `comm2/building_type_intensity.csv` | 6 | 4 | 4 |
| `comm2/water_heating_solar_shares.csv` | 7 | 20 | 20 |
| | | | **264** |

v2 supersedes v1 for `end_use_intensity.csv`, `building_type_intensity.csv`,
`water_heating_solar_shares.csv`. v1 still governs `end_use_saturation.csv` and
`fuel_shares.csv`. `b7_fuel_share_disposition.csv` (v2, 38 leaves) was read as the
disposition map only — it tells us which 6 leaves are `authored-by-us`; no values.

Column set: the 11-column shape shared by residential/transport
(`ams,branch,variable,expression,unit,fuel,source,note,src_csv,data_confidence,scenario`).
`data_confidence = TEAM_AUTHORED` on every row — **no `PLACEHOLDER` anywhere** (§4.1).

---

## 1. Group 1 — B1 end-use intensity (50 rows)

- **Branch** `Demand\Commercial\Other Commercial\End Use Projection\<End Use>`
- **Variable** `Commercial Uncalibrated Energy Intensity`
- **Unit** `kWh/m2` — read from canon
  (`commercial_branch_variables_units.csv`), not assumed.
- **Value** the `uncal_intensity_bridge` column, per **R3** (CAL untouched; no row
  of this build addresses `Key\Cal\*`).
- **Lighting withdrawn by the team → 50 rows, not 60** (R10). Verified: the v2
  file contains no `lighting` rows.

**Scenario handling — what I found and what I did.** I checked the canon
4-scenario export for scenario variance on this variable:
`current_expressions_commercial_4scenarios.csv`, grouped by (branch, region) →
**61 groups, 0 varying**. B1 is scenario-invariant in canon, held identically in
Current Accounts, Baseline Simulation, AMS Target Scenario and Regional Aspiration
Scenario. I therefore emit these rows with **`scenario` blank**, which the
`CanonicalInjector` `_filter_rows_for_scenario` treats as "applies to every
scenario in the run" — i.e. the row is written once per scenario iterated,
reproducing canon's all-4 pattern without four near-duplicate CSV rows.
**Consequence for the operator: the inject must be run with all four scenarios
in `--scenarios` for this to land exactly as canon holds it.**
This follows **R9** (canon authors B1 in all 4; do not touch
`Demand\Commercial\Other Commercial\Historical`, and nothing here does).

Canon values are stale-able: e.g. canon v0.67 Brunei AC held
`119.40 ⟨comment⟩ BEI 2019`; the team's bridge value for the same cell is `66.33`.
That divergence is content and is the team's call.

## 2. Group 2 — B3 end-use saturation (60 rows)

- **Branch** same end-use level. **Variable** `Activity Level`.
- **Unit** `Saturation` (scale `%`, per `of Square Meter`) — canon.
- **Value** `saturation_pct`, **as a LITERAL PERCENT — not divided by 100**
  (§11.2f; the residential AC `282 → 2.82` burn). Verified against canon, which
  holds e.g. Brunei AC `80` and Laos AC `Interp(2017, 50.84)` — percent-scale.
- Lighting **is** included here (60 rows), per **R10**.
- Same scenario finding as Group 1: canon **73 groups, 0 varying** → `scenario`
  blank.

## 3. Group 3 — B7 tech shares (120 rows)

- **Landed on the LEAF `Activity Level`, per R1** — *not* `Commercial Fuel Share_`.
  Settled ruling, not revisited.
- **Branch** `…\End Use Projection\<End Use>\<Leaf>`; **unit** `Share` (%, of
  Square Meter) — canon.
- 10 regions × 3 scenarios × 6 leaf-slots = 180 candidate series; each series is
  38 annual anchors 2023–2060.
- **Constant series collapsed to a scalar: 40 of 120 written series.**
  Remaining **80 written as `Interp(2023, v, 2024, v, …, 2060, v)`**, comma
  separators, period decimals (§A.15). Verified: 0 semicolons, 0 comma-decimals.
- Scenario aliases applied: `Baseline → Baseline Simulation`,
  `AMS Target → AMS Target Scenario`,
  `Regional Aspiration → Regional Aspiration Scenario`. These rows are
  **scenario-tagged**, so `_filter_rows_for_scenario` routes each to its own
  scenario only (§A.20 last-writer-wins protection).
- The payload has **no Current Accounts** shares — CA is therefore untouched by
  Group 3 and keeps its canon authoring.

### Remainder(100) drops — 60 rows saved

Canon-verified from `current_expressions_commercial_4scenarios.csv`
(`Activity Level` on the AC / Refrigeration leaves). The Remainder leaf closes the
family and **moves by scenario**; writing a value over it would break the closure.
Dropped from the write set (never overwritten):

| End use | Leaf dropped | Scenario | Regions | Rows |
|---|---|---|---|---|
| Air Conditioning | `Current Sales_Average` | AMS Target Scenario | 10 | 10 |
| Air Conditioning | `Current Stock_Average` | Baseline Simulation | 10 | 10 |
| Air Conditioning | `Efficient` | Regional Aspiration Scenario | 10 | 10 |
| Refrigeration | `Existing` | AMS Target Scenario | 10 | 10 |
| Refrigeration | `Existing` | Baseline Simulation | 10 | 10 |
| Refrigeration | `Existing` | Regional Aspiration Scenario | 10 | 10 |
| | | | **total** | **60** |

180 candidate − 60 dropped = **120 written**. The 4th canon pair
(AC `Current Stock_Average` in Current Accounts; Refrigeration `Existing` in
Current Accounts) never arises — the payload has no CA shares.

## 4. Group 4 — Refrigeration efficiency ratio (10 rows)

- **Branch** `…\End Use Projection\Refrigeration\Efficient`,
  **variable** `Final Energy Intensity`, **unit** `Kilowatt-Hour` (per Square Meter)
  — canon.
- Canon expression read verbatim first, identical in all 4 scenarios and all
  regions: `0.7 * Existing:Final Energy Intensity[kWh]`.
- Authored the **same shape with the coefficient only changed to 0.604** (**R4**;
  the team's `efficient_existing_ratio` column in `fuel_shares.csv` carries exactly
  `0.604`):
  `0.604 * Existing:Final Energy Intensity[kWh]`
- Scenario blank (canon holds it identically in all 4). One row per ASEAN-10 region.

## 5. Group 5 — AC borrow re-point: **NOT AUTHORED** (0 rows)

**Verdict: cannot be authored from verifiable paths. Rows left out, per the brief's
"if a referenced path cannot be verified, leave those rows OUT — do not invent".**

### 5.1 The full canon expression, verbatim

From `current_expressions_commercial_4scenarios.csv`, `Final Energy Intensity`,
identical across **all 4 scenarios** and `ALL (12 regions)`:

- `…\Air Conditioning\Best Practice`
  `Demand\Residential\Projections\Air Conditioning\Current_Stock Average:!EER[Btu/Wh] / Demand\Residential\Projections\Air Conditioning\Best Practice:!EER[Btu/Wh] * Current Stock_Average:Final Energy Intensity[kWh]`
- `…\Air Conditioning\Current Sales_Average`
  `Demand\Residential\Projections\Air Conditioning\Current_Stock Average:!EER[Btu/Wh] / Demand\Residential\Projections\Air Conditioning\Current_Sales Average:!EER[Btu/Wh] * Current Stock_Average:Final Energy Intensity[kWh]`
- `…\Air Conditioning\Efficient`
  `Demand\Residential\Projections\Air Conditioning\Current_Stock Average:!EER[Btu/Wh] / Demand\Residential\Projections\Air Conditioning\Efficient:!EER[Btu/Wh] * Current Stock_Average:Final Energy Intensity[kWh]`

(The 4th leaf, `Current Stock_Average`, does not borrow — it is
`Air Conditioning:Commercial Uncalibrated Energy Intensity[kWh/m2] * Key\Cal\Commercial\Electricity:Activity Level[Factor]`.
It is CAL-touching and out of scope under R3; not authored.)

Ratio shape: `<stock EER> / <tier EER> * Current Stock_Average:Final Energy Intensity[kWh]`.

### 5.2 What route (i) needs, and what actually exists

R5 specifies: re-point onto **the parent-level `Useful Energy Intensity` on
`Demand\Residential\Projections\Air Conditioning_`**, preserving the ratio shape,
with tier mapping Best Practice→`High_eff`, Efficient→`Mid_eff`,
Current Sales_Average and Current Stock_Average→the stock-weighted parent.

Checked against `inject/residential/structure_handover_20260703/residential_branch_variables_units.csv`:

| Path needed by route (i) | Exists? |
|---|---|
| `Demand\Residential\Projections\Air Conditioning_` : `Useful Energy Intensity` | **NO** — that branch carries only `Activity Level`, `Demand Cost`, `End Year Penetration`, `RefHH` |
| `Demand\Residential\Projections\Air Conditioning_\{Large,Medium,Small}` : `Useful Energy Intensity` | YES |
| `Demand\Residential\Projections\Air Conditioning_\<Size>\{High_eff,Mid_eff,Low_eff}` : `Useful Energy Intensity` | **NO** — tiers carry `Efficiency`, `Final Energy Intensity`, device/cost vars; no UEI |

So there is **no per-tier UEI anywhere in the rebuilt tree**, and no UEI on the
`Air Conditioning_` parent itself. The only UEI that exists is size-level and
**tier-invariant** — `current_expressions_residential_4scenarios.csv` shows
`Air Conditioning_\Large:Useful Energy Intensity =
Key\Residential\Air Conditioning\Useful_EI\Large:Activity Level[Tonnes of Oil Equivalent]`
(same shape for Medium/Small). A ratio of UEI between two tiers is identically 1
by construction; a ratio between two *sizes* is not the tier mapping R5 asks for.

Tier differentiation in the rebuilt tree lives in **`Efficiency` (%)** on
`Air Conditioning_\<Size>\<Tier>` — e.g. Brunei Large: `High_eff Interp(2014, 100.0)`,
`Mid_eff Interp(2014, 72.32565355674502)`, `Low_eff Interp(2014, 52.93533185715097)`.
Building the ratio out of `Efficiency` would be a **different route**, and one that
also has to pick a size (or a size-weighting) that nobody has specified. Choosing
that is authoring content, which is not ours to do. Not done.

### 5.3 A hedge the team should see — RESOLVED 2026-07-23 (v0.80 canon)

~~R5 states "'!EER' does not exist in the rebuilt tree". I could not verify that
either way from files.~~ The v0.80 canon promotion settles it offline; **no live
read is needed.**

`!EER` was **relocated, not deleted.** v0.80 removed the residential
`Demand\Residential\Projections\Air Conditioning\<tier>` branches entirely (part
of 9 deleted residential legacy branches) and added `!EER[Btu/Wh]` to
commercial's **own** four AC tiers under
`Demand\Commercial\Other Commercial\End Use Projection\Air Conditioning\`
(288 rows = 4 tiers × 6 scenarios × 12 regions), with real per-region data.
The three §5.1 expressions quoted above are therefore **historical** — v0.80
already rewrote all three to the sibling-local form, identical string, 72 rows
each:

```
Current Stock_Average:!EER[Btu/Wh] / !EER[Btu/Wh] * Current Stock_Average:Final Energy Intensity[kWh]
```

The tier's own EER is a **bare self-reference** `!EER[Btu/Wh]` (no branch
prefix); the sibling uses the bare leaf name `Current Stock_Average:`, matching
the refrigeration idiom `0.7 * Existing:Final Energy Intensity[kWh]`. Anyone
reconstructing this expression from the natural shape would write the tier
prefix and be wrong.

**Consequence for this build:** Group 5 is a no-op. The 120 route-C static-ratio
rows were removed from `commercial_canonical_20260722.csv` (756 → 636 with the
CNZ drop) rather than pushed — pushing them would overwrite correct canon with a
static approximation whose ratios are materially wrong (canon-implied 0.70 /
0.43–0.65 / 0.24–0.43 vs the staged 0.90 / 0.70 / 0.55). Full numbers per region
in [INJECT_READINESS_20260722.md](INJECT_READINESS_20260722.md) §7 O1.

Nothing is owed back to the team on this item.

## 6. Group 6 — building-type controls (4 rows)

- **Branch** `Key\Commercial\Energy consumption per area\<Type>`, **variable**
  `Activity Level`, **unit** `kWh/sqm` — read from `keys_slice_commercial_units.csv`.
  Per **R6** these do **not** go to `Key\Commercial\Average Energy Intensity`,
  which is a composite `SUM(share × intensity)`.
- Rows: Singapore Office `218`, Hotel `292`, Retailer `405`; Thailand Retailer `350`.
- Canon (v0.67, **stale-able**) held Singapore Office `185` / Hotel `218` /
  Retailer `326`, and Thailand Retailer `.350 ⟨comment⟩ energy consumed per area` —
  the decimal typo. Both halves of the Thailand fix are in this build (see §8).
- Scenario blank: canon holds these identically in all 4 exported scenarios
  (checked per-region in `current_expressions_keys_slice_4scenarios.csv`).

## 7. Group 7 — bug 7, solar water heating (20 rows)

- **Branch** `…\End Use Projection\Water Heating\Solar Heating`, **variable**
  `Activity Level`, **unit** `Share` — canon.
- Scenario-tagged per **R7**: 10 rows in `Regional Aspiration Scenario`, 10 in
  `Carbon Neutrality_ Net Zero Scenario`.
- Values as given, literal percents: Indonesia `30.71`, Thailand `3.39`, the other
  eight `0`.
- **The bug is visible in canon and the fix is confirmed by it.** In v0.67 the
  per-region values are already correct in Current Accounts / Baseline Simulation /
  AMS Target Scenario (Indonesia `30.71 ⟨comment⟩ EBT 2022`, Thailand
  `3.39 ⟨comment⟩ EBT 2022`, others `0`), but **Regional Aspiration Scenario carries
  a single `2` at `ALL (12 regions)` scope**, which overrides all of them. Writing
  the per-region values into RAS is exactly the right repair.
- **Operator note:** `Carbon Neutrality_ Net Zero Scenario` is in the canon
  11-scenario roster but was **not** in the 4-scenario export, so I could not
  verify its current expression. Those 10 rows are authored on structure, hedged on
  state. They will only land if that scenario is included in `--scenarios`, which
  the standard 4-scenario invocation does **not** do — see §9.

## 8. Thailand (R8) — in scope, in the main canonical, no parked file

Thailand is authored normally throughout. Both halves of the coupled change ship
here together:
- the team computed Thailand's B1 against the **corrected** control
  (`106 → 197 kWh/m²`), and
- the `.350 → 350` Retailer fix is in `building_type_intensity.csv` (Group 6).

Injecting them in the same push leaves Thailand internally consistent **on the
input side**.

**Residual, flagged and not fixed here:** Thailand's calibration factor was fitted
against the OLD (typo'd) floor-area/intensity control, so calibrated demand will
shift when this lands. That is the user's deferred cal work under R3 (CAL
untouched) — **not a blocker for this inject, but it must be re-fitted before the
Thailand results are read as final.**

## 9. Operator notes for the inject

- **Blind mode is mandatory and is the inherited default** — every target is
  `Demand\` or `Key\` (§A.20). Pair with `--fail-fast` (blind hangs on a missing
  FullName, §11.1). Branch paths in the CSV are byte-exact copies of canon
  `branch_path` strings.
- 124 rows carry a **blank `scenario`** (Groups 1, 2, 4, 6) and are written once per
  iterated scenario; 140 rows are scenario-tagged (Groups 3, 7).
- The standard 4-scenario invocation does **not** include
  `Carbon Neutrality_ Net Zero Scenario`. To land Group 7 in full:

```
python inject/commercial/inject_to_leap.py \
  --csv inject/commercial/20260722/commercial_canonical_20260722.csv \
  --scenarios "Current Accounts,Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario,Carbon Neutrality_ Net Zero Scenario" \
  --expect-area "<area>" --exclude-timor-leste --fail-fast --skip-dry-run -y
```

  Note that adding the 5th scenario also means the 124 blank-scenario rows are
  written into it. Canon only proves those are invariant across the **four**
  exported scenarios — if Carbon Neutrality is meant to differ on B1/B3/building
  types, run the 4-scenario push first and a Group-7-only push second.
- `--exclude-timor-leste` is correct: TL is off in LEAP calc (project memory), and
  the sibling `timor_leste_supplement.csv` holds its zero rows separately (§A.18).
- Verify readback per scenario as `N EXACT, 0 NORMALISED, 0 FAIL` before
  `calculatescenario`.

## 10. Not authored (deliberately)

- The 23 canon-retained leaves; the 7 Lighting borrow leaves; `Key\Cal\*`;
  `Demand\Commercial\Other Commercial\Historical`; `Data_Center`; the 8 non-live
  `Commercial Fuel Share_` "bugs".
- `Commercial Fuel Share_` on any branch (R1 — inert; canon annotates it
  "0 ⟨comment⟩ Only used for water heating, cooking, other", and a full-corpus scan
  found zero expression-side references).
- Group 5 (see §5).
- Lighting B1 (withdrawn by the team, R10).

## 11. Gate results

Run at the end of the builder, against the emitted CSV:

| Gate | Result |
|---|---|
| `nemo_read.find_region_lock_violations` | **0 violations — PASS** |
| `nemo_read.find_zero_existing_capacity_conflicts` | **0 violations — PASS** |
| `nemo_read.validate_canonical_csv_expressions` | **0 violations — PASS** |

Plus builder-internal assertions, all passing on every one of the 264 rows:
- every `(branch, variable)` pair exists in the canon unit tables
  (`commercial_branch_variables_units.csv` + `keys_slice_commercial_units.csv`) —
  a typo'd path or an invented variable aborts the build;
- every `ams` is one of the ASEAN-10 (no Timor Leste, no Base Template);
- `unit` is copied from canon, never hand-typed.

Post-build fidelity checks (§A.14 — these were run, not assumed):
- **value fidelity: 0 mismatches.** Every numeric token in every emitted
  expression (excluding Interp year anchors and the R4 coefficient) round-trips to
  a value present in a team source CSV. Nothing was rescaled or re-derived.
- **separator check: 0 semicolons, 0 comma-decimals** (§A.15).
