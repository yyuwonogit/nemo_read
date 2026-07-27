# Operator summary — bioenergy blend-ramp cycle, 2026-07-22

**Internal. Not for the bioenergy team.** For the team-facing package see
`README_bioenergy_reply_20260722.md` + `OUR_RULINGS_20260722.md` +
`CONTENT_ASKS_20260722.md` (zipped to `outbox/20260722/`).

**Nothing was injected. No COM, no `calculatescenario`.** Everything below is files.

---

## 1. What was built

### In `inject/bioenergy/20260722/`

| File | What |
|---|---|
| `bioenergy_delta_20260722.csv` | **539 rows**, 12 cols, canonical schema + `scenario`. The payload |
| `build_blend_delta_20260722.py` | Deterministic re-runnable builder |
| `BUILD_NOTES_20260722.md` | Every decision and every blocker, long form |
| `_audit_ceiling_vs_floor.csv` | 720 (region × fuel × year) cells, pre/post |
| `_audit_group3_before_after.csv` · `_audit_unlimited.csv` · `_audit_maxcap_vs_installed.csv` | Supporting audits |
| `_run_gates.py` | Gate harness — **see §4, gate 2 is defective** |
| the 3 team-facing docs | as above |

### In the repo (committed edits, separate from the payload)

- `inject/bioenergy/CSV_AUTHORING_GUIDE.md` §11.2 + §12.2 — false auto-unit-conversion
  claim retracted, dated. **Residual:** the §12 preamble (lines ~957 and ~979) still
  carries the same framing above the correction block. One-line follow-up if wanted.
- `outbox/20260721/bioenergy_ruling/RULINGS_20260721.md:180` — dated erratum on the
  Bagasse clone template (Bagasse `Maximum Production` is **Terawatt-hour**; correct
  template is `Resources\Primary\Palm Oil Mill Effluent`, `Metric Tonne`, identical
  15-variable panel). §6 left standing as issued.
- `nemo_read/schema.py` — `MaxShareProduction` parameter + `LEAP_SOURCE_MAP` entry.
- `nemo_read/infeasibility.py` — `_check_min_vs_max_share_production`, registered.
- `tests/test_infeasibility.py` — positive case, **negative control**, schema name pin.
  Fail-without / pass-with proven by deleting the registration line (1 failed → 14
  passed restored).
- `CHANGELOG.md` — `## [Unreleased]` Added / Fixed / Documented.

**Test suite:** 356 passed with `--ignore=tests/test_inject_base.py`. That one file
hangs at `TestTimorLesteSupplement::test_runtime_proceeds_with_exclude_flag`
(`test_inject_base.py:567`) on COM dispatch when LEAP is not running — **proven
pre-existing** by stashing all three source changes and re-running it in isolation.
356 + 62 = 418.

---

## 2. Row counts by group

| Group | Authored | Held / skipped |
|---|---|---|
| G1 Blending ceiling (`Maximum_Share_of_Production`, RAS only) | 20 | — |
| G2 Indonesia bioethanol floor (R4) | 2 | — |
| G3 Uniform 2025 start (R5) | 27 | 31 no-ops skipped, 2 → G2 |
| G4 Refinery `Maximum Capacity` | 70 | 10 Cellulosic Rice Straw (no branch), 5 lite-panel families (R1 scope) |
| G5 Build rate (`Maximum Capacity Addition`) | 90 (70 refinery + 20 blending) | 2 fossil blending legs — **open, see §3** |
| G6 De-sentinel every `Unlimited` | 330 | Base Template + Timor Leste only |
| G7 Feedstock resources | 0 | none needed — every cap already has its companion cost row in all 12 regions |
| **Total** | **539** | |

**Conversion verified independently, all 200 source cells**, Möbius form, 0 cells
matching a linear ×38.997. Reference: B7 6.3444 · B20 18.3673 · B50 47.3684 ·
E10 6.2203 · E20 12.9861. Canon's own **floor** expression carries the identical
transform, so floor/ceiling parity holds.

**Ceiling-below-floor cells:** 61 pre-delta → **27 post-delta** (independently
reproduced cell-for-cell). G2 clears Indonesia bioethanol entirely (36 → 0); G3 clears
every 2025 start-year artifact but widens Malaysia Bd (14 cells, worst 14.13 pp) and
Thailand Bd (12 cells, worst 2.96 pp) into 2026+. The R7 `Max()` wrapper makes
`ub ≥ lb` structurally true in all 720 cells regardless — the 27 are cells where the
wrapper is doing work, not cells that will fail.

---

## 3. BLOCKED — must be resolved before inject

### B1 — R6 is incomplete: 60 `Unlimited` cells survive, and the notes claim otherwise

`Unlimited` still stands on `Transformation\Diesel Blending\Processes\Diesel` and
`…\Gasoline Blending\Processes\Gasoline` for `Maximum Capacity`,
`Maximum Capacity Addition` and `Maximum Production` — RAS, 10 AMS each = **60 cells**,
inside the Blending module, which R1 puts in scope.

`BUILD_NOTES` §7 asserts "no `Unlimited` left on any in-scope branch for any of the 10
AMS in any scenario." **That is false**, and it contradicts the notes' own §9 row 4.

Worse, the treatment is **asymmetric**: the delta *does* author
`Exogenous Capacity = 100000` on those same two fossil legs (40 rows, all 4 scenarios).
So the fossil leg is in scope for the lower bound and out of scope for all three upper
bounds — the biofuel leg gets a 100000 level cap, a 10000/yr rate cap and a 1e+10
production cap while the fossil leg races it unbounded in a PercentShare-dispatched
module. **Net bias toward fossil.**

**Decision needed:** author the 60 cells, or delete the false summary sentence and accept
the asymmetry knowingly. Do not inject with both standing.

### B2 — 70 `Maximum Capacity` rows silently switch `Add()` → `Interp()`

Every canon expression for `Maximum Capacity` on the 7 refinery branches is `Add(…)`,
`RegionValue(…)` or `Unlimited`. **Zero use `Interp()`.** Canon Indonesia FAME is
`Add(2025, 16, 2030, 7.5, 2035, 7.5, …)`; the delta writes
`Max(Exogenous Capacity, Interp(2025, 623.952, …, 2060, 2534.805))`.

Canon's `Add()` magnitudes (16, 7.5) are two orders below the same branch's
`Exogenous Capacity` (~614 Million GJ/Yr for Indonesia FAME) — **so `Add()` cannot be an
absolute level; it must be increments over a base.** Replacing it with an absolute
`Interp()` changes what the variable *means*.

Structure is ours to decide, but this has to be decided **explicitly and verified against
the live area**, not slipped in. `BUILD_NOTES` §5 discloses the bare-vs-unit-tagged
reference uncertainty and says nothing about this.

### B3 — `_run_gates.py` gate 2 is vacuous

`nemo_read._leap_com.validate_canonical_csv_expressions` **returns** a list of violations
(`_leap_com.py:441`); it never raises. The script wraps it in try/except and prints
`PASS` whenever no exception fires — it would print PASS on a fully
semicolon-contaminated CSV.

**The data is genuinely clean** (0 semicolons in the `expression` column across 539 rows;
the 209 semicolon hits are in `source`/`note` prose, which the validator does not read).
So this is a harness defect, not a data defect — but `BUILD_NOTES` §0 presents its output
as a passed gate. Fix the harness to check the returned list, then re-run.

---

## 4. Gate results (as run)

| Gate | Result |
|---|---|
| `find_region_lock_violations` | **0** — non-vacuous (a synthetic `Solar PV_MYPE`-in-Vietnam row makes it return 1) |
| `validate_canonical_csv_expressions` | reported PASS — **see B3, the harness is defective; the underlying data is clean on direct inspection** |
| `find_zero_existing_capacity_conflicts` | **0** |
| Region aliasing | 0 hits for `Brunei Darussalam` / `Lao PDR` / `Viet Nam` / `Timor Leste` / `Base Template` anywhere in 12 columns |
| Variable spelling | 20 × `Maximum_Share_of_Production`, 0 × spaced form; 40 × `Minimum Share of Production`, 0 × underscored form |
| Scenario tagging | 0 untagged rows; all 20 ceilings RAS-only; 0 ceilings in Current Accounts; the 50 CA rows are `Exogenous Capacity` (40) + Corn `Maximum Production` (10), both legitimate |
| `Max()`/`Min()` argument order | 0 numeric-first sites (bracket-depth parse of all 539 expressions, not a regex) |
| `Unlimited` in `expression` | 0 (the 350 hits are note/source prose) |
| Duplicates / placeholders / stray ` ? ` tails | 0 / 0 / 0 |
| Branch + variable + unit triples | all verified literally against canon (63,096 bio/blending rows extracted) |

---

## 5. Pre-inject checklist

Run in this order. **Do not skip step 1 — it can make the entire ceiling deliverable
moot.**

- [ ] **1. THE ONE-CELL EXPORT TEST — run before anything else.**
      `MaxShareProduction` exists in the live NEMO build **with 0 rows**;
      `MinShareProduction` has 85. An empty table proves NemoMod *declares* it. It does
      **not** prove LEAP's exporter ever *writes* it.
      **Test:** author exactly one `Maximum_Share_of_Production` cell — Philippines
      Biodiesel 2025, energy value `2.980`, smallest gap in the set (0.635 pp), one
      region-year, trivially reversible. Export. Then:
      `SELECT * FROM MaxShareProduction;`
      - Row lands beside `MinShareProduction = 0.036145` → mechanism confirmed, proceed.
      - **Table still empty → the whole ceiling is a no-op**, infeasibility risk is zero,
        and this cycle's priority order changes completely. Do not spend a solve to find
        this out, and **do not run the 539-row payload to find it out either.**
- [ ] **2. Resolve B1, B2, B3** (§3). B2 in particular needs a live-area read.
- [ ] **3. §A.9 state confirmation** — read `leap.ActiveArea.Name` back to the user;
      confirm area, scenario, and that nothing else is mid-flight.
- [ ] **4. `--exclude-timor-leste`** (mandatory flag; TL disabled in calc).
      `Base Template` excluded.
- [ ] **5. LEAP regional decimal = period** (§A.20 gate, exit 11 on comma).
- [ ] **6. Blind mode + `--fail-fast`.** G2 targets `Key\Biofuel Blending Targets\…` —
      a `Key\` branch, so **blind is mandatory**; cached writes silently no-op there.
- [ ] **7. Push the `Exogenous Capacity` 1e12 → 100000 rows ALONE, with their own
      `calculatescenario`, before anything else rides on them.** Same family as the
      2026-05-12 p9 burn (EC=0 on the 4 blending pseudo-techs → infeasibility 24k → 4.6M,
      190× worse). Hypothesis, not proven, that finite-large is safe. Isolate it.
- [ ] **8. Explicit user sign-off on the R4 Indonesia row** —
      `InterpFSY(2025, 20, 2050, 50)` → `InterpFSY(2025, 0, 2050, 20)`. Highest
      narrative impact in the delta. Note floor = ceiling exactly from 2050 (zero
      slack); alternative is moving the endpoint to 2060.
- [ ] **9. Exhaustive readback** — delta doctrine means 539 rows, so verify every one,
      not a sample. Target `N EXACT, 0 NORMALISED, 0 FAIL` per scenario, plus a UI
      eye-test on a multi-scenario branch.

---

## 6. Open items needing a live-area read

Batch these into **one** COM session (§A.10) once state is confirmed. Estimated ~2 min
warm.

| # | Read | Decides |
|---|---|---|
| 1 | `MaxShareProduction` export test (above) | whether the ceiling exists at all |
| 2 | `First Simulation Year` | the R2 ramp anchor — 2024 literal vs 2025-with-historical-point |
| 3 | Canon `Add()` vs absolute `Interp()` semantics on the 7 refinery `Maximum Capacity` branches | **B2** |
| 4 | Whether a `[…]` unit token containing spaces and a slash is accepted in a `Max()` reference | G4 uses a **bare** `Max(Exogenous Capacity, Interp(…))`, no unit tag, because no canon precedent exists. If LEAP rejects it, add the tag from the live area's own unit string at inject time |
| 5 | `Key\Optimized Trade` roster for Biodiesel + Ethanol, enabled-in-RAS | **Laos.** Canon keeps B10/E10 floors while the delta sets Laos biodiesel `Maximum Capacity Addition` to 0 in every year and `Maximum Capacity` to `Max(EC=0, 0)`. Laos must then meet a hard floor from 2030 with zero domestic capability — satisfiable **only** through Optimized Trade, last verified at v0.42. This is the §11.4(b) infeasibility class and the delta tightens it |
| 6 | Live `Maximum Capacity Addition` on the 7 production processes | Part C collision with the 70 already-accepted `Maximum Capacity` rows |
| 7 | Both `Key\Biofuel Blending Targets` branches, live | every canon value cited here is v0.67 (3 versions stale) or a v0.69-era sqlite |

---

## 7. Non-blocking, but travel with the file

1. **Corn Ethanol is permanently foreclosed in all 10 AMS**, as are all 7 refineries in
   Brunei. The per-cell arithmetic is documented in `BUILD_NOTES`; the **aggregate** never
   is. Someone will notice.
2. **A false per-row note.** The 7 BAS Group-3 rows carry
   `"Post-2025 trajectory PRESERVED verbatim. Was: 0"`. Those series were zero in *every*
   year and now hold the 2025 anchor flat to 2060. §4 of the notes says this correctly —
   but the **row note is what lands in the inject log**. Fix before push.
3. **R5's literal wording was not followed for three anchors** — Thailand Bd 8.2
   (achieved 6.8), Thailand Be 13.7 (achieved 11.3), Malaysia Bd 12.0 (2026-dated, Low
   confidence). Disclosed with warnings in the notes; these follow the team's peak rule,
   which is defensible. **User should confirm rather than have it inferred.**
4. **13 cells where floor equals ceiling to floating point** — Philippines Bd 2025,
   Thailand Bd 2025, Indonesia Bd 2050–2060. Zero optimiser slack on a share variable.
5. **G5's 2 fossil blending legs** left unauthored on the build rate — the symmetry
   question in B1, same root.
6. **CHANGELOG has two `## [Unreleased]` headings** (new 2026-07-22 + pre-existing
   2026-07-13). Merge at release.
7. **Erratum line-range imprecision** — cites Bagasse canon "lines 125-136 and 137-144";
   actual block is 125-172, 48 rows, 48/48 `Terawatt-hour`. Understates the evidence;
   harmless.

---

## 8. Sent to the team

`outbox/20260722/bioenergy_reply_20260722.zip` — three files only:
`README_bioenergy_reply_20260722.md`, `OUR_RULINGS_20260722.md`,
`CONTENT_ASKS_20260722.md`. No payload CSVs, no audits, no build notes.

Nine content asks. Two of our own errors owned explicitly (the ×38.997 conversion
instruction; the authoring guide's false auto-conversion claim). Their method is not
challenged anywhere in the package.
