# In-flight work — pick up here

> **Cross-session pickup note.** This file is what a fresh Claude
> session reads first (CLAUDE.md §0). It tells you what's pending
> across sessions. Update or empty it whenever a major piece of work
> completes.

## Status as of 2026-07-29 — aeo9_v0.82: RAS RESULT SOLVED + FULLY DIGESTED; still awaiting full v0.82 *input* export

> **▶ START A DISCUSSION OF THIS RESULT HERE (works on any machine after push):**
> Read **[result/20260729/NEMO_25_48_RAS_full_digest.md](result/20260729/NEMO_25_48_RAS_full_digest.md)**
> — the complete decoded digest of the solved RAS run. 11 sections: headline,
> electricity supply, storage/transmission/trade, demand, fuels & bioenergy blend,
> emissions, costs, APAEC targets, anomaly sweep, what-the-inject-achieved, and a
> **§11 Q&A springboard** (source DB path, 126-table roster, decode recipes,
> honest-answer caveats). Every figure carries its source table inline; critic
> corrections C1–C6 baked in. **The digest alone answers most questions.** For
> deeper slices, the source DB is `mailbox/20260729 Final/NEMO_25 48.sqlite`
> (271 MB, **NOT in git** — re-point if pruned/on another machine); §11.3 has the
> `NemoDB`/SQL decode recipes.

**Yearly RESULT half of Phase A/C — DONE.** The solved RAS calc (`NEMO_25 48.sqlite`)
was received 2026-07-29 and fully digested. Headline: **FEASIBLE, unmet load = 0
everywhere**; coal flips Subcritical→USC; ~107 GW nuclear + ~189 GW CCS build in the
2040s; biodiesel rides its ceiling to B54; RE clears 45% capacity by 2030
(rooftop-corrected); energy CO₂ 1.40→2.56 Gt after 199 Mt/yr CCS. Residual items for
next cycle: 37 GW stranded IDN Coal-USC-CCS (A1), Unmet-Load phantom capex (A2),
ethanol-blend late collapse, FAME 31.5× unit phantom in 6 small regions, road-vehicle
fleet layer absent from results. **Still pending: the full v0.82 INPUT export** (the
other half of Phase A — needed to confirm every injected expression landed vs canon).

**Mega-inject COMPLETE.** All 6 payloads (1,387 rows) injected into `aeo9_v0.81`
and readback EXACT (0 FAIL): transport hist 160 / audit 164 / delta 291 /
commercial 626 / bioenergy 114 / power 32. Canon promoted v0.67→v0.80→v0.81.
Area now at **v0.82** post-inject + the one manual patch fix.

**Patch fix (manual, applied in LEAP):** Indonesia
`Water Heating\Solar Heating : Activity Level` 30.71→29 — bug-7 share overshot
the family `Remainder(100)` (`Existing`→−0.71 at 2060), halting the calc. Watch
Thailand `Solar Heating`=3.39 (same class, marginal) if a re-calc trips there.

**Tooling shipped:** `inject/run_megainject.py` (single-session driver — one COM
dispatch for all payloads, fixes the §A.10 ActiveArea='' blank between separate
injector invocations); `leap_lock.py` (on/off toggle for the `.leap_lock` COM
interlock). Delta payloads + logs + progress trail committed (branch
`v080-canon-and-staged-injects`, commits 505899a + 88ce72a).

**NOW AWAITING (Phase A/C):** only the **full v0.82 input export** remains — the
**yearly result is IN and digested** (see the pointer at the top of this block).
On the input export's arrival: confirm every injected expression landed correctly
vs the refreshed canon (the result-side evaluation — unmet load falls, fleets retire
via stock-overflow, blend under the drifting ceiling, AC ownership reads 282,
coal/nuclear/RE/CCS movement — is already covered by the digest §10).

---

## Status as of 2026-07-14 (power v0.71 batch1b — INJECTED, results audit pending)

**Power batch1b delta injected clean into `aeo9_v0.71` on 2026-07-14.**
263 rows (262 delta + 1 stranded probe): RAS 202 / ATS 30 / BAS 30, all
pushed, 0 failed, every readback EXACT. Log:
`inject/power/20260713/_inject_log_20260714_batch1b.txt`.
**Results audit: scheduled 2026-07-15 — do NOT re-inject. Run
`calculatescenario`, then harvest + audit.**

**What batch1b did** (RAS unless noted):
- Coal flip: retire all remaining subcritical to ~0 by 2060 + kill the
  supercritical pipeline (ATS/PDP untouched).
- USC + USC-CCS reactivated (`MaxCap` → `Max(Exogenous, 20000)`).
- Nuclear → ~100 GW ASEAN across the 6 willing AMS (LWR/SFR/SMR).
- Biomass biophysical caps: RAS `Maximum Capacity`; ATS/BAS
  `Endogenous Capacity = 0`.
- VOLL 20,000 USD/MWh on `Unmet Load : Variable OM Cost`, flat, all 10
  AMS + all 3 scenarios (8 copper-plate on base `Unmet Load`, IDN on its
  4 `_ID*` nodes, MY on its 3 `_MY*` nodes — no other region has nodes;
  `Fixed OM` stays 500).
- RE/storage `Maximum Capacity Addition` × `Interp(2025 1×, 2040 3×, 2060 8×)`.
- Stranded-cost probe (`Coal Subcritical_IDJW : Stranded Cost`) — inert.

Review bundle for the power team: `outbox/20260714/
power_batch1b_review_20260714.zip` (validated delta + realigned stranded +
review note). Team digested, no reship. The two "structural-create" asks
(Thai Nuclear SMR, copper-plate Unmet Load) were **refused** — canon §A.22
proved both branches already exist; the inject landed on them EXACT, live-
confirming it. Open: copper-plate Unmet Load / Thai Nuclear SMR hidden-flag
is settled by the calc (no verified COM helper for branch-visibility).

## What's pending — pick up in this order

### 0. MEGA INJECT PROJECT → aeo9_v0.76+ — 3-PHASE SEQUENCE (user-gated, do in order)
User directive, restated 2026-07-22: **(A) input and result collection from the
latest run, FULL PANEL → (B) mega inject, adjusted deeper from the newest input
values → (C) re-run LEAP.** Each phase gates the next. Do not inject before A.

**PHASE A — FULL-PANEL INPUT + RESULT COLLECTION (user provides).** A fresh
export of the live area covering **both** sides: the complete input/expression
set AND the current results, across the full panel (all sectors, all regions,
the 11-scenario roster — not the 4-scenario canon slice). On arrival:
**re-validate ALL staged payloads against it, and re-tune values against the
newest inputs** — Phase B is not a replay of what is staged today, it is those
payloads *adjusted* to the refreshed baseline. This also closes every standing
asterisk: the 2 CCS `_IDSA` node creates, the commercial live reads (Cal,
Lighting borrow), and the v0.67→v0.76 canon drift (9 versions, currently
unread). The fresh export becomes the new canon baseline **and** the pre-inject
result baseline for C.

> Two of those asterisks are now CLOSED by the v0.80 canon promotion
> (2026-07-23), no live read needed:
> - **Gasoline naming — SETTLED, not a rename.** `Key\` uses bare `Gasoline`,
>   the Demand tree uses `Blended Gasoline`; the split is intentional and the
>   area calculates. Payloads and `inject/transport/build_canonical.py` both
>   corrected. Do not harmonise.
> - **Commercial `!EER`** — v0.80 relocated it onto commercial's own four AC
>   tiers and re-pointed `Final Energy Intensity` at the local sibling. The
>   residential borrow path is dead along with the 9 deleted residential legacy
>   branches. Our 120 route-C static-ratio rows were dropped as redundant (and
>   materially wrong: canon-implied ratios are 0.70 / 0.43-0.65 / 0.24-0.43,
>   not the staged 0.90 / 0.70 / 0.55).

**PHASE B — MEGA INJECT.** §A.9-confirm the area; **re-ask the user what's
already hand-injected** (power non-nuclear P1–P4; are the P4 CCS branches
created yet?) before any run. Then inject the staged mix, each via its sector
injector (blind, `--fail-fast`, `--exclude-timor-leste`):

**(a) Transport (2026-07-21) — 1,204 rows, all canon-clean, ours to inject
via `TransportInjector` (blind, Key+Demand branches):**
- `inject/transport/canonical_leap_inputs.csv` — 880 data rows.
- `inject/transport/20260721/transport_audit_corrections_20260721.csv` — 164
  correction rows (F1/F3/A1/A9b/A9c).
- `inject/transport/20260721/historical_stock_patch_20260721.csv` — **160 rows,
  `Stock` Data() 2005-2024, Current Accounts, absolute Vehicle**; the team's
  hard historical-fleet input, **replaces the corrupted CA Stock series (closes
  A4/A6a/A6b)**. Reconciles to V5 `BaseYear_StockData` at 2024 (ratio 1.000);
  scenario-invariant historical (CA inherited). Confirmed canon-side: `Stock`
  under Current Accounts is the right slot (181 CA Stock rows exist) and doesn't
  collide with forward overflow (2024 seam = V5). Region-lock/interp/§11.2b 0.
- Gasoline naming SETTLED 2026-07-23 against the v0.80 Keys export: `Key\` =
  bare `Gasoline`, Demand = `Blended Gasoline`, intentional split, do not
  harmonise. (Supersedes the earlier "FIXED both trees, v0.75" note, which was
  wrong — it came from a verbal description, not an export.) 160 Key rows in
  the delta were rewritten to bare `Gasoline`; the adapter now encodes both
  maps. **Erratum owed to the transport team** —
  `outbox/20260721/TRANSPORT_HANDOVER_fixes_and_canon_20260721.md` told them
  "`Blended Gasoline` on BOTH trees … do not write `Gasoline`", which will
  mis-name their next Key-side drop. Team learned §2/§3 (adopted canon
  roster, withdrew V6 + the "fleets never retire" framing). Handover shipped:
  `outbox/20260721/transport_handover_20260721.zip`.
- BONUS / LATER (no aviation team exists): **B4 (SAF FEI evaluates to 0)** —
  the IDN SAF mandate (1→50% by 2060) delivers ZERO SAF demand, a
  scenario-defining error. Hand it back to the TRANSPORT team as a bonus
  fix-list item for the NEXT audit cycle (not this inject; not aviation).

**(b) Power batch2 (2026-07-21, DRAFT)** — `inject/power/20260721/
batch2_unmet_nuclear_inject_20260721.csv`, 55 rows, RAS only. Indonesia
unmet-elimination + nuclear. **User is hand-injecting the NON-NUCLEAR part
(P1/P2a/P2b/P4, 46 rows); treat as done-injected BUT RE-ASK the user to
confirm before our run — do NOT assume.** Nuclear (P5, 9 rows: VNM/PHL
must-run + IDN 90% availability derate, all on base Nuclear LWR/SFR/SMR) is
OURS to inject.
- **P4 RETARGETED 2026-07-22 → `inject/power/20260722/batch2_ccs_retarget_20260722.csv`
  (32 rows, supersedes the P4 block in the batch2 CSV).** User ruling: the CCS
  capacity previously assigned to **IDJW moves to the NON-NODAL base branches**;
  **IDSA stays nodal**. So:
    `Gas Combined Cycle with CCS`        8 rows — exists in canon, injectable now
    `Coal Ultrasupercritical CCS`        8 rows — exists in canon, injectable now
    `Gas Combined Cycle with CCS_IDSA`   8 rows — CREATE
    `Coal Ultrasupercritical CCS_IDSA`   8 rows — CREATE
  **Branch creates drop 4 → 2**; 16 of 32 rows are injectable immediately.
  Gates clean (region-lock `[]`, interp `[]`). §A.23 checked: Indonesia is NOT
  locked out of either base branch — CCS was never node-decomposed (the locked
  Indonesia list is Biogas/Biomass Other/Coal Subcritical/Diesel/Gas Combined
  Cycle/Gas Engine/Gas Turbine/Geothermal Flash/Large+Small Hydro/Solar PV/
  Unmet Load/Wind Onshore). v0.76 result corroborates: base `Gas Combined Cycle
  with CCS` already carries Indonesia 45,000 MW, base `Coal Ultrasupercritical
  CCS` 20,000 MW.
  **Intentional §A.23 exception to record:** once `_IDSA` exists the CCS family
  is *partially* node-decomposed while the base still carries Indonesia values —
  normally the shape §A.23 rejects. Deliberate (Jamali national, Sumatra nodal).
  Do not let a future session "fix" it.
- ~~**P4 (32 rows) targets 4 to-be-created node branches — KEEP THE ROWS.**~~ (superseded above)
  `Gas Combined Cycle with CCS_IDSA/_IDJW` + `Coal Ultrasupercritical
  CCS_IDSA/_IDJW` don't exist in the current export (CCS families are
  Indonesia base-only, not node-decomposed) — but the **LEAP team is creating
  them manually**, so they'll exist on the live area by our inject time. Do
  NOT strip these rows; they're pending-create, not invalid. **Hard sequencing
  rule (§A.20/§11.1): blind mode HANGS on a missing FullName — before injecting
  the P4 rows, confirm with the user that the 4 CCS node branches have been
  created in the live area.** After the create, canon needs re-export from
  v0.75 to include them.
- P1/P2a/P2b (14 rows, Gas CC_ID* / Hydro_ID* / Biomass_ID*) + P5 (9) are on
  existing branches — injectable by us now. Region-lock 0, interp 0, §11.2e 0.

**PHASE C — EVALUATE INPUT + RESULT.** Post-inject: per-scenario readback
`N EXACT / 0 NORMALISED / 0 FAIL`; then `calculatescenario`; harvest; and
evaluate both sides — (input) everything landed correctly vs the refreshed
canon; (result) did the fixes work: Indonesia unmet load falls, transport
fleet retires via stock-overflow, residential AC ownership reads 282, coal/
nuclear/RE move as intended. Compare against the Phase-A pre-inject baseline.

### 0a. ALL FIVE SECTOR PAYLOADS BUILT — staged for the mega inject (Phase B)
Every payload below is canon-clean and inject-ready EXCEPT where noted. All were
validated against v0.67 canon; **Phase A (full-panel v0.76 export) re-validates
them before any push.**

| Sector | File | Rows | Ready? |
|---|---|---|---|
| Commercial | `inject/commercial/20260722/commercial_canonical_20260722.csv` | 636 | ✓ (AC re-point = 0 rows, user A/B/C pending) |
| Transport | `inject/transport/canonical_leap_inputs.csv` + 2× 20260721 | 1,204 | ✓ |
| Power b2 | `inject/power/20260722/batch2_ccs_retarget_20260722.csv` | 32 | 16 now / 16 after 2 _IDSA creates |
| Bioenergy | `inject/bioenergy/20260722b/bioenergy_delta_20260722b.csv` | 114 | ✓ |
| Residential | (injected v0.73 2026-07-16) | 5,371 | done |

**Commercial domain stood up** 2026-07-22: `inject/commercial/inject_to_leap.py`
(CanonicalInjector subclass) + `timor_leste_supplement.csv`. pytest 239 passed.
Open: AC re-point 0 rows — route (i) impossible (no UEI on the rebuilt AC tree);
recommend route C `0.55 * Current Stock_Average:Final Energy Intensity[kWh]`.
Blank-scenario rows expanded to explicit 4-scenario tags (do not inherit blanks).

**Bioenergy delta 20260722b (114 rows) — the corrected one; supersedes 20260722/
(SUPERSEDED.md).** Built from the team's 2026-07-22 return. Contents:
- FLOOR (mandate) forced on all 20 series, `Minimum Share of Production`, RAS.
- CEILING drift: the B50/E20 wall is SOFT — once reached, ceiling drifts +0.3 pp/yr
  (~1/10 the demonstrated max ramp) to B60/E30 by 2060, giving the optimiser a
  growing band above the mandate. `Max(Minimum Share of Production, Interp(...))`,
  20 series incl. Indonesia Biodiesel. Möbius volume→energy on both bounds.
- `Add()` PRESERVED on refinery `Maximum Capacity` (the fix vs the superseded delta,
  which rewrote it to a level and would have scrapped ~90% of Indonesia's fleet).
  Real invariant here: Add() args never negative (0 found), NOT the power Max guard.
- Philippines FAME `Exogenous Capacity` multiplier defect FIXED, all 4 scenarios
  incl. Current Accounts (a units defect = ours, no ask; 29× phantom-plant floor).
- Build-rate `Maximum Capacity Addition` unrolled offline to explicit Interp;
  Philippines seed re-based 225→7.72 (inherited the same defect).
- OUT: 51 pending-create rows (Rice Straw/UCO/Cellulosic Rice Straw don't exist yet),
  5 lite-panel processes, CNZ.
- **Max safeguard note (canon fact):** the power `Max(Exogenous Capacity, N)` idiom
  lives on `Maximum Imports` in the bio chain (85 canon rows,
  `Max(<numeric>, Maximum Production[Tonne]/1000)`) — floors the import valve against
  domestic production. Same intent as power's fleet floor. NOT on refinery Max Capacity.

**Back to bio team (structure only, next contact):** their Indonesia Bioethanol
`canon_mandate_parsed` misreads `InterpFSY(2025,20,2050,50)` (floor would exceed their
own ceiling at 2050+); 45-vs-38 pinned-cell prose/CSV conflict; `Maximum Capacity`
must ship in `Add()` form. We owe post-solve: demand export, fuel EnergyContent
(unblocks their R1 gate), Bagasse/Biomass deficit check, evaluated canon floor series.

### 0b. Bioenergy — ruling reply SHIPPED 2026-07-21; awaiting their blend ramp
Reply package: `outbox/20260721/bioenergy_ruling_reply_20260721.zip`
(README + RULINGS + **ASK_blending_ramp** + 89-row disposition CSV).
**Payload verdict: 79 of 89 rows inject-ready; 10 held** (`Cellulosic Rice
Straw`, pending the manual create). No reship asked of them. Scenario column
is empty on all 89 — **we** tag it and scope `Maximum Imports` to RAS.

**Structural creates the user does MANUALLY before inject** — `Rice Straw` +
`Used Cooking Oil` (flat depth-3 `Resources\Primary` leaves mirroring
`Bagasse`), `Cellulosic Rice Straw` (process mirroring the `Cassava` sibling).

**THE OPEN ASK — biofuel blend ramp (canon finding 2026-07-21).** Both
`Diesel Blending` and `Gasoline Blending` are *optimised* modules, and on the
bio processes (`Biodiesel`, `Ethanol`):
- `Minimum Share of Production` ← `Key\Biofuel Blending Targets\<Fuel>:
  Activity Level[Volume %]/100 * 38.997` (biodiesel) / `* 26.744` (ethanol) —
  the mandate floor, enforced.
- **`Maximum_Share_of_Production` = flat `100`** (note the UNDERSCORES; the
  floor variable uses spaces) and **`Maximum Capacity Addition` = `Unlimited`**
  → **no ceiling, no rate limit: RAS can jump a country to any blend share in
  one year.** No blend wall, no infrastructure lag.
- Mandate floors are mostly un-evidenced single endpoints (Malaysia
  `InterpFSY(2030, 30)` ⇒ 6 pp/yr vs Indonesia's observed ~2–3 pp/yr).
  **Indonesia `InterpFSY(2023, 35, 2025, 40, 2050, 50)` is the only real
  observed curve** — the benchmark we asked them to use.
- Asked for: per-AMS max blend-share trajectory 2025→2060 in **volume %**
  (we do the energy conversion with the same idiom), binding reason incl.
  the **technical blend wall** (E10 non-flex-fuel; B7/B10/B20 engine compat),
  re-shaped floors, and optionally a finite annual build rate.

Post-inject/solve we owe them: demand export, fuel `EnergyContent` export
(settles ask 1b + ask 8), the Bagasse/Biomass deficit check, fresh RAS run +
true input expression set. Open confirm from them: Brunei fix GJ-vs-TJ basis
(0.01 vs 2.44 TWh) and the 61-vs-89 blocked-row count mismatch. Verify their
"v0.71 already fixed Biomass `[Tonne]/1000`" claim against the Phase-A export
— our v0.67 canon still shows the bug.

### 0c. Commercial — reply SHIPPED 2026-07-22; canonical build in progress
Drop: `mailbox/20260722/commercial_leap_sendback_20260721.zip` (7 files, their
own 44/44 canon self-audit). Reply: `outbox/20260722/commercial_reply_20260722.zip`.

**STRUCTURAL RULINGS WE MADE (canon, not negotiable):**
- **Shares land on leaf `Activity Level`, NOT `Commercial Fuel Share_`.** CFS_ is
  an inert sentinel (canon annotates it `0 ? Only used for water heating, cooking,
  other`); full-corpus scan of all 8 raw workbooks = **2,493,853 rows, ZERO
  expression-side references**, vs control `Commercial Cooking Efficiency_` = 924.
  **This retires 7 of their 9 reported bugs** — the missing `/100` asymmetry is
  real but nothing reads those cells. Only **bug 7 is live** (Water Heating
  `Solar Heating` uniform `2` overriding sourced ID 30.71 / TH 3.39) and it is in
  **RAS *and* Carbon Neutrality_ Net Zero** (team flagged RAS only).
- **Path prefix:** `Demand\Commercial\Other Commercial\End Use Projection\`.
  `Activity Level` means saturation at end-use level, tech share at leaf level.
  Lighting is 3 deep. `Remainder(100)` closes each family and **moves by scenario**
  (AC: Current Stock_Average CA/BAS, Current Sales_Average ATS, Efficient RAS).
- **Commercial has its OWN `Historical` branch** (sibling of `End Use Projection`)
  → CA is not the home for this payload. B1 is scenario-invariant (61 groups, 0
  varying) and canon authors it in all 4.
- **Cal untouched** (user). Use `uncal_intensity_bridge`; migrate to
  `uncal_intensity_kwh_m2` only when the user does cal. **Thailand is coupled** —
  its `Key\Cal\Commercial\Electricity = 0.41165` was fitted to the OLD floor area,
  so the `.350` fix + cal + TH B1 move together or not at all.
- **Refrigeration ratio = 0.604** (their CSV governs over their prose 0.60).
- **AC borrow: re-point, route (i)** — parent-level `Useful Energy Intensity`
  ratio on `Air Conditioning_` (no size assumption). `!EER` does not exist in the
  rebuilt tree; `Efficiency` does, but only at `<Size>\<Eff>` leaf level.
  **No interaction with our v0.73 residential inject** — P2 wrote 0 rows to
  `Projections\Air Conditioning\` and contains 0 occurrences of `EER`.
- **Building control is a COMPOSITE** — their re-sourced values belong in
  `Key\Commercial\Energy consumption per area\<Type>`, NOT `Average Energy
  Intensity` (which = Σ share × intensity and recomputes itself).

**OURS TO FIX, no resend:** 4 alias maps (regions; scenarios; `cooking`→`Cooking
and Food Processing` snake_case, NOT title-casable; disposition join on the
(end_use, tech_leaf) PAIR), all `Interp()` authoring (payload is pure values),
`Remainder(100)` closure (drop the designated leaf from the write set), and the
60 constant-Baseline series (delta doctrine).

**BLOCKER — `inject/commercial/` is not a domain yet:** no canonical, no
`timor_leste_supplement.csv`, no `CanonicalInjector` subclass. §A.18 fails CI
without the supplement. Stand it up before the first delta. Blind mode MANDATORY
(all targets are `Demand\` / `Key\`). Scenario roster is **11**, not 4.

**AWAITING FROM THEM (content):** per-building-type controls (their Singapore
282.89 vs model 214 — B1 is `split% × control ÷ saturation` against a control we
don't hold), Thailand `Retailer` = 350, the 10 inert Lighting B1 rows (re-wire or
withdraw), bug 7 values, AC class→efficiency tier (4 classes vs 3 tiers),
`!Missing Branch (ID=1687/825)` repoint target.

### 1. Residential Phase-2 inject — INJECTED into aeo9_v0.73 (2026-07-16) ✓
**Landed clean: 5,371 writes across CA/BAS/ATS/RAS, 0 failed, 10 EXACT/0/0
per scenario. AC ownership corrected 2.82→282 (verified EXACT). Do NOT
re-inject.** Log: `inject/residential/20260716/_inject_log_20260716.txt`.
Next: `calculatescenario` on v0.73 → results audit. Details below (build +
rulings retained for reference):
Drop `mailbox/20260716/residential_leap_inject_20260715.zip` (AC/Fridge/
Lighting/Cooking/9-appliances) validated against canon + converted to a
clean canonical: **`inject/residential/20260716/residential_canonical_20260716.csv`**
(3,721 rows). Canon-clean: region-lock 0, interp 0, 0 branches/pairs
outside canon, 0 dup keys. Builder: `build_residential_canonical.py`.
Author corrections shipped: `outbox/20260716/MD1_ANSWERS…md` + `MD2_FIXLIST…md`.
Key rulings: AC=`Air Conditioning_` (underscore, exists — no create);
ownership/shares/UEI → `Key\Residential\<Appliance>\…`; ownership injected
AS-IS as a percent incl. AC >100% (see [[reference_percent_ownership_saturation]]
— corrects the live model's 2.82 bug); RAS-only device panel; FEI never
pasted (LEAP-derived); frozen AC variant; `lighting_kwh_hh` excluded.
**To inject:** §A.9-confirm `aeo9_v0.73` open + idle, then
`ResidentialInjector` (blind default — writes Demand + Key branches, blind
MANDATORY; `--fail-fast --exclude-timor-leste --expect-area aeo9_v0.73 -y`)
→ per-scenario readback EXACT. Two author confirms outstanding (fridge
frozen-vs-drift, lighting_kwh_hh/Other deferrals) — non-blocking.

### 1b. Power FullCapacity dispatch delta — STILL HELD (not in batch1b)
`inject/power/20260707/dispatch_rule_fullcapacity_delta.csv` (448 rows,
ATS+BAS, MeritOrderDispatch → FullCapacity; lock-clean) was NOT part of
batch1b. WP-J run-2 (dispatch reversal) is **ON HOLD** per the batch1b
work order — keep run-1 must-run floors; the team signals after digesting
the batch1b results. Do not inject the dispatch delta alone.

### 2. Power team's own content follow-ups (in the shipped README/answers)
These are THEIR authoring calls — we consult, don't author unprompted:
- **5-node unmet load** (top priority): Indonesia East 658 / Sumatra 388
  / Kalimantan 362 TWh (energy) + **Jamali 287.6 GW peak-slack**
  (reserve). Node capacity / additions / transmission limits.
- **Biomass Gasification 400 GW + H2 Fuel Cell 188 GW runaways** — cost
  review on the Hydrogen-module branches (P14988 etc.), not the power
  branch. Is hydrogen priced in Resources?
- VN Nuclear (economics) + GCC-CCS (dual H2+NG input wiring) dead fleets.
- 3 orphan vars to re-author per `_ID*` node (Capacity Retirement /
  Endogenous Capacity / Maximum Capacity) — see
  `BASE_BRANCH_REMOVED_NOTES_20260707.md`.

### 3. v2 results package (promised to the team)
Regenerate result extracts with: NEMO tech-ID + LEAP branch-path columns,
module filter (drop the 1e12 Diesel-Blending sentinels from power views),
per-column unit stamps, explicit zeros for the 61 suppressed 2025 rows,
xlsx tab-name fix (A1 titles are correct; tabs are swapped), and resolve
the Large Hydro_IDKA 2060 zero-production-with-capacity anomaly.

### 4. Deferred enforcement (our side, optional)
- **Cross-inject consistency pre-flight gate** — formalize the MaxCap-
  vs-ExoCap accounting script (`_probe_maxcap_accounting_v3.py`) into a
  `CanonicalInjector` pre-flight validator + tripwire, so a numeric cap
  that undershoots the layered exogenous fleet aborts before inject (§A.17
  — currently the only mechanically-enforceable rule from this cycle not
  yet a gate). Also: scan Capacity Additions for negative entries (the PH
  Wind Offshore −19 GW vintage-hack class).

### 5. Housekeeping (low priority)
- Working tree has stale untracked strays predating this cycle:
  `grep.exe.stackdump` (junk), `mailbox/results_*.csv` + `mailbox/units.csv`
  (May 18), `output/`, `result/20260701/`. `feas/` holds the solved DB
  (gitignored `.sqlite`). Prune when convenient.
- CHANGELOG has several stacked `[Unreleased]` blocks since v0.7.0 — a
  release cut is arguably overdue (nemo_read library gained public API:
  `BASE_BRANCH_NODE_ONLY`, region-lock, variable_classifier exports).

## When in doubt
- Re-read [CLAUDE.md §A](CLAUDE.md) hard rules (now through §A.23).
- [docs/FLOWS.md](docs/FLOWS.md) for inject / probe / infeas flows.
- Memory: `MEMORY.md` — esp. delta-inject doctrine + node region-locks.
