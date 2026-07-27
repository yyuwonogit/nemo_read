# INJECT READINESS — bioenergy delta 20260722b

**Payload:** `inject/bioenergy/20260722b/bioenergy_delta_20260722b.csv` — 114 rows
**Builder:** `build_bio_delta_20260722b.py` · **Notes:** `BUILD_NOTES_20260722b.md`
**Supersedes:** `inject/bioenergy/20260722/` (539 rows, marked KNOWN-BAD — do not push)

---

## 1. STATUS

**NEEDS FIX** — the delta is structurally clean and all four gates pass, but the
ceiling authoring does not achieve B3: 16 of the 38 ceiling==floor cells end up pinned
anyway, because omitting an anchor inside or after an authored series still resolves
(via interpolation/hold + the `Max(Minimum Share of Production, …)` guard) to exactly
the floor.

---

## 2. WHAT CHANGED vs `inject/bioenergy/20260722/`

| | superseded delta (539 rows) | this delta (114 rows) |
|---|---|---|
| Refinery `Maximum Capacity` | 70 rows rewritten `Max(Exogenous Capacity, Interp(...))` | **0 rows — refused. Canon `Add()` untouched.** |
| Upper-bound sentinels | 120 rows `Unlimited` → `10^10` | none authored |
| `Exogenous Capacity` in Current Accounts | 40 rows | none (RAS/ATS/BAS only) |
| Fossil blending legs | 80 rows (`Diesel Blending\Diesel`, `Gasoline Blending\Gasoline`) | none |
| `Key\Biofuel Blending Targets` writes | 29 rows | none |
| Mandate | ceiling-shaped | floor on all 200 cells + ceiling on 162 |

**What the old delta would have done if injected.** Its 70 `Maximum Capacity` rows read
canon's `Add(...)` as an absolute level. Canon Indonesia FAME RAS is
`Add(2025, 16, 2030, 7.5, … 2060, 4)` — 65 Million GJ/Yr of *cumulative additions* on top
of ~636.5 already standing (`Exogenous Capacity`, 2023). Injected as a level cap of ~624
falling out of the Add() stream, the model would have been instructed to scrap on the
order of 90% of the Indonesian biodiesel fleet. Philippines FAME was worse: a level of
`0.0` across all anchors against a standing fleet. Add the `10^10` sentinel (≥10⁹ breaches
CPLEX tolerance, §A.11) and 40 Current-Accounts `Exogenous Capacity` rewrites and the
run would have been unrecoverable without a rollback.

**The A9 ruling is withdrawn.** The bioenergy team were right: `Add()` is cumulative
additions. This delta preserves it — and asserts the real invariant instead
(**0 negative `Add()` arguments** across all canon refinery rows, verified twice
independently), which makes cap-below-fleet structurally unreachable and means
**no `Max(Exogenous Capacity, N)` guard is authored here.** That power idiom applies only
to level-semantics variables.

---

## 3. ROW COUNTS

114 rows. Scenario split: RAS 111 · ATS 1 · BAS 1 · CA 1. The CA row is the
Philippines FAME Exogenous Capacity fix (canon authors that variable per-scenario,
so the multiplier defect exists in Current Accounts too). No CNZ, no
Timor Leste, no Base Template.

| Branch | Variable | Unit | Scenario | Rows |
|---|---|---|---|---:|
| `Transformation\Diesel Blending\Processes\Biodiesel` | Minimum Share of Production | Percent | RAS | 10 |
| `Transformation\Gasoline Blending\Processes\Ethanol` | Minimum Share of Production | Percent | RAS | 10 |
| `Transformation\Diesel Blending\Processes\Biodiesel` | Maximum_Share_of_Production | % | RAS | 9 |
| `Transformation\Gasoline Blending\Processes\Ethanol` | Maximum_Share_of_Production | % | RAS | 10 |
| `Transformation\Biodiesel Production\Processes\FAME Biodiesel` | Maximum Capacity Addition | Million Gigajoules/Year | RAS | 10 |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel` | Maximum Capacity Addition | Million Gigajoules/Year | RAS | 10 |
| `Transformation\Biodiesel Production\Processes\POME Biodiesel` | Maximum Capacity Addition | Million Gigajoules/Year | RAS | 10 |
| `Transformation\Bioethanol Production\Processes\Cassava` | Maximum Capacity Addition | Million Tonne Coal Equiv/Year | RAS | 10 |
| `Transformation\Bioethanol Production\Processes\Corn Ethanol` | Maximum Capacity Addition | Million Tonne Coal Equiv/Year | RAS | 10 |
| `Transformation\Bioethanol Production\Processes\Molasses` | Maximum Capacity Addition | Million Tonne Coal Equiv/Year | RAS | 10 |
| `Transformation\Bioethanol Production\Processes\Sugarcane` | Maximum Capacity Addition | Million Tonne Coal Equiv/Year | RAS | 10 |
| `Transformation\Biodiesel Production\Processes\FAME Biodiesel` | Exogenous Capacity | Million Gigajoules/Year | RAS | 1 |
| `Transformation\Biodiesel Production\Processes\FAME Biodiesel` | Exogenous Capacity | Million Gigajoules/Year | ATS | 1 |
| `Transformation\Biodiesel Production\Processes\FAME Biodiesel` | Exogenous Capacity | Million Gigajoules/Year | BAS | 1 |

Ceiling is 9 Biodiesel series not 10 because Indonesia/Biodiesel is pinned on 10 of 10
anchors → whole series unauthored (canon's default `100` stands). The two share variables
carry different unit strings in canon (`Percent` vs `%`) — that asymmetry is canon's, not
a typo.

---

## 4. THE INJECT COMMAND — do not run until §1 clears

```
python inject/bioenergy/inject_to_leap.py \
  --csv inject/bioenergy/20260722b/bioenergy_delta_20260722b.csv \
  --scenarios "Current Accounts,Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" \
  --expect-area <LIVE_AREA_NAME> \
  --exclude-timor-leste \
  --fail-fast \
  --skip-dry-run \
  -y
```

Blind mode is the default and is correct here (§A.20). `--fail-fast` is mandatory with
blind — a missing FullName hangs otherwise. `--exclude-timor-leste` is explicit per §A.18
and matches the payload (zero TL rows). `--expect-area` must be the exact live area name
read back at §A.9 confirmation — the canon reference is v0.67, live is v0.76+, so do not
hardcode a guess. No `--ignore-units` needed: the LEAP-native refusal only fires on the
filename `canonical_leap_inputs.csv`.

---

## 5. PRE-INJECT CHECKLIST

**§A.9 — confirm with the user before any COM contact:**
- [ ] `leap.ActiveArea.Name` read back and matches `--expect-area` exactly (not `''` — the
      §11.1 spontaneous-blanking trap).
- [ ] Only the target area open in LEAP; nothing else mid-flight.
- [ ] LEAP → Settings → Regional decimal separator is `.` (period). Comma-decimal makes
      every readback ambiguous (§A.20 #3; injector exits 11).
- [ ] The three target scenarios exist under this area under exactly these names.

**Live reads canon cannot settle (v0.67 canon vs v0.76+ live):**
- [ ] **The one-cell `Maximum_Share_of_Production` test.** Canon shows the variable on the
      branch, but canon cannot prove the live area still exposes it *or* that LEAP→NEMO
      exports it as `MaxShareProduction`. Push **one** ceiling row, read it back, then
      confirm the parameter appears in the post-calc SQLite. If it does not export, the 19
      ceiling rows are inert and the whole ceiling group should be held, not shipped.
- [ ] Canon's refinery `Maximum Capacity` is still `Add()` in the live area (spot-read
      Indonesia FAME RAS). B1/B2 rest on this; a v0.68–v0.76 rewrite to level semantics
      would invalidate the "no guard needed" ruling.
- [ ] Philippines FAME `Exogenous Capacity` still reads the bare, multiplier-less form
      before the B4 fix overwrites it — and its three siblings still carry
      `* 10^6 * ConvFuelUnits(liter, gj, biodiesel)`.
- [ ] `Maximum Capacity Addition` is exposed on all 7 refineries in RAS in the live area
      (canon says yes; 70 of 114 rows depend on it).
- [ ] The two share-variable unit strings live (`Percent` / `%`) match what we ship.

**Post-inject, before `calculatescenario`:**
- [ ] Per-scenario readback: **N EXACT, 0 NORMALISED, 0 FAIL.** `normalize_interp` changed
      0 of 112 expressions and all rows are pure ASCII, so anything other than EXACT is a
      real problem, not a formatting artifact.
- [ ] UI eye-test on one multi-scenario branch (Philippines FAME `Exogenous Capacity`,
      which is the only variable written in all three scenarios).

---

## 6. WHAT WE OWE THE TEAM

Their four asks:

1. **A9 — withdrawn; they were right.** `Maximum Capacity` is cumulative additions via
   `Add()`, not a level. Our previous delta got this wrong and has been marked
   KNOWN-BAD. Corollary they need for the next drop: **re-ship `Maximum Capacity` in
   `Add()` form** — all 80 rows in `bioenergy_leap_input.csv` arrived as `Interp()`
   levels and were refused, so that group is simply absent from this inject.
2. **Philippines FAME `Exogenous Capacity` — fixed.** The bare
   `Interp(2015, 204, …, 2023, 225)` now carries the sibling multiplier
   `* 10^6 * ConvFuelUnits(liter, gj, biodiesel)`, byte-mirroring Thailand/Indonesia/
   Malaysia including the trailing source annotation. Flag to them that their
   `build_rate_limit.csv` `installed_2023 = 225.0` for that cell inherited the same
   defect; we re-based it to 7.7214 (29.1× correction), which drops it to the
   `one_train_floor`.
3. **The evaluated canon floor series** — `_audit_floor_mobius.csv` (200 cells,
   volume % → energy % under the Möbius transform, both fuels) plus
   `_audit_ceiling_authored.csv` (162) and `_audit_ceiling_skipped_pins.csv` (38). Send
   with the correction that their `canon_mandate_vol_pct` misreads Indonesia Bioethanol:
   canon is `InterpFSY(2025, 20, 2050, 50)`, they read it as reaching 20 at 2050. Their
   own `canon_mandate_parsed.csv` records the correct endpoint (50) — the two files
   contradict each other. **We authored their values as given**, so the understatement is
   carried through; corrected, their floor exceeds their own ceiling at 2050/2055/2060,
   which is a hard inversion they must resolve.
   Also: the prose says 45 pinned cells, the CSVs say 38 (CSVs govern); and
   `p4_pending_branch_creates.csv` under-lists 10 `Cellulosic Rice Straw : Maximum
   Capacity` rows that exist in the input file (our builder keys on branch path, so
   nothing leaked, but their file is wrong).
4. **Post-inject deliverables** — after `calculatescenario` on the injected area:
   - the **fuel `EnergyContent` export** from the post-calc NEMO SQLite for Biodiesel,
     Ethanol, Diesel, Gasoline and both blended fuels, with LEAP names attached. This is
     what unblocks their R1 gate: it lets them check the engine's own energy densities
     against the Möbius constants they specified (biodiesel 38.997/43.330, bioethanol
     26.744/44.8) and confirm the volume→energy conversion is parity-preserving in the
     live model rather than on paper.
   - readback log (EXACT counts per scenario) so they can see exactly which of their cells
     landed;
   - blend-share results on both blending processes, so they can see whether the optimiser
     actually sits above the floor where we left it free — the direct test of B3.

---

## 7. STILL DEFERRED

The **51 `p4_pending_branch_creates` rows** stay out (B6): `Resources\Primary\Rice Straw`,
`Resources\Primary\Used Cooking Oil`, and
`Transformation\Bioethanol Production\Processes\Cellulosic Rice Straw` do not exist in
canon. Note the real count of affected rows in the input file is **61**, not 51 — the
extra 10 are `Cellulosic Rice Straw : Maximum Capacity`, missing from their pending list.

**What unblocks them:** structure is ours (§A.23), so this is a branch-creation decision,
not a data question. Required before they can ship: agreement that the three branches
should exist, then creation in LEAP (Base Template + each region), then a fresh
Export-Expressions walk to re-canon the tree, then the rows can be authored against
verified paths and units. Not a same-cycle item.

Also out of scope this cycle by ruling: the 5 lite-panel `Maximum Production` rows
(Charcoal\All Biomass, Anaerobic Digestion, Methanol ×2, Ammonia) present in their input
file, filtered out under the R1 narrowing.

---

## 8. OPEN QUESTIONS — all three change what we do

1. **The B3 ceiling fix — blocking.** 16 of the 38 pinned cells resolve to exactly the
   floor despite carrying no anchor, because they sit inside or after an authored series.
   Worst case is Thailand/Bioethanol, pinned across the entire forward horizon 2027–2060
   (series stops at 2026 = 9.530643, held below a 12.986054 floor). Also Malaysia/
   Biodiesel 2026 + 2030 (interior anchors) and Indonesia + Vietnam Bioethanol 2050/2055/
   2060 (zero-slope tails). Fix: author an explicitly free value (canon default `100`) at
   the trailing and interior pinned years rather than relying on omission — and correct
   `BUILD_NOTES_20260722b.md` §"Partially-pinned series", which currently asserts these
   years are "never pinned from above", the opposite of what the expressions evaluate to.
   **Confirm the fix direction before rebuilding**: author `100` at those years, or
   accept the pin.

2. **Philippines FAME `installed_2023` override — needs authorisation.** We changed a team
   content value (225.0 → 7.7214) on a unit-consistency argument that follows from B4. It
   flips that row from 45.0 to the `one_train_floor` 5.8495. It is the only number in the
   delta that does not trace to a team source value. Approve, or ship their 225.0 and let
   the B4 fix and the build-rate seed disagree.

3. **The frozen build-rate rule — needs sign-off.** Their rule is
   `MaxCapAdd(y) = max(one_train_floor, alpha × installed(y-1))`, which is recursive and
   compounds. We froze `installed(y)` at the canon 2023 `Exogenous Capacity`, giving a
   constant allowance (Indonesia FAME stays 127.3037 Mn GJ/yr to 2060 instead of
   compounding). That is a reinterpretation of their **method**, not just their numbers,
   and it under-permits. 60 of 70 rows are unaffected (greenfield, `installed_2023 = 0`
   → the floor); only 4 rows are genuinely sensitive. Approve the freeze, or send the
   rule back to them for a non-recursive restatement.

Separately, hedged and not action-changing: the Philippines expression carries canon's
trailing `?` source annotation byte-identically to its siblings. Mirroring it is right,
but whether that `?` is the live character or an export artifact cannot be settled from
files — it will show up in the readback either way.
