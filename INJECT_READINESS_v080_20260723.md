# INJECT READINESS — v0.80 cycle, 2026-07-23

Canon: `aeo9_v0.80` (promoted 2026-07-23). LEAP is open and locked; nothing in
this report was verified against the live area. Every structural claim below
resolves against `LEAP structure/LEAP Input *.xlsx` (v0.80) and the staged CSVs
themselves.

---

## 1. VERDICT TABLE

| # | Payload | File | Rows | Scenarios (rows) | Verdict | Clearest reason |
|---|---|---|---:|---|---|---|
| 1 | COMMERCIAL | `inject/commercial/20260722/commercial_canonical_20260722.csv` | **626** | CA 124 / BAS 164 / ATS 164 / RAS 174 | **GO-WITH-FIXES** | All gates clean and all 626 triples resolve in v0.80 — but U2 was satisfied by **deleting** 120 rows, not authoring them. Needs your sign-off (O1). |
| 2 | TRANSPORT delta | `inject/transport/20260723/transport_delta_20260723.csv` | 291 | CA 135 / BAS 52 / ATS 52 / RAS 52 | **GO-WITH-FIXES** | Branch paths correct (160 bare `Key\…\Gasoline`), but the `fuel` metadata column still says `Blended Gasoline` on those 160 rows — payload no longer reproducible from its own fixed adapter (B2). |
| 3 | TRANSPORT audit | `inject/transport/20260721/transport_audit_corrections_20260721.csv` | 164 | CA 71 / BAS 31 / ATS 31 / RAS 31 | **GO** | Clean on every gate; 164/164 triples resolve. 40 of the CA rows (`First Sales Year`) are CA-only — contingent on the CA ruling (O2). |
| 4 | TRANSPORT hist | `inject/transport/20260721/historical_stock_patch_20260721.csv` | 160 | CA 160 | **GO** | Clean, 160/160 resolve. 100% Current Accounts — **this file ceases to exist** under a literal reading of U3 (O2). |
| 5 | BIOENERGY | `inject/bioenergy/20260722b/bioenergy_delta_20260722b.csv` | 114 | CA 1 / BAS 1 / ATS 1 / RAS 111 | **GO** | Clean on every gate; no open items. |
| 6 | POWER | `inject/power/20260722/batch2_ccs_retarget_20260722.csv` | 32 | RAS 32 | **GO** | Clean; the 16 Indonesia base-branch rows verified **legitimate** against the v0.80 Indonesia walk (178 base rows for both CCS families) — §A.23 does not fire. |
| | **TOTAL** | | **1,387** | CA 491 / BAS 248 / ATS 248 / RAS 400 | | |

**OVERALL: GO-WITH-FIXES — do not launch yet.** Nothing structural blocks the
inject (zero unresolved branch/variable/region triples across all 1,387 rows, so
no blind-mode hang risk), but three operator decisions and one metadata patch are
outstanding: the U2 delete-instead-of-replace sign-off, the Current Accounts scope
ruling (491 rows, 200 of them with no alternative home), the live `ActiveArea`
name for `--expect-area`, and the 160 stale `fuel` cells.

---

## 2. WHAT CHANGED FOR v0.80

The canon promotion moved `LEAP structure/` from `aeo9_v0.67` to `aeo9_v0.80`.
Four consequences landed on these payloads.

**Gasoline split — SETTLED, and it retired a false alarm.** The `Key\` tree uses
bare `Gasoline`; the Demand tree uses `Blended Gasoline`. Verified in
`LEAP Input Keys.xlsx`: 10 bare Key gasoline nodes, **zero** `Blended Gasoline`
anywhere under `Key\`. The split is intentional and the area calculates. The
2026-07-20 note claiming the rename hit *both* trees came from a verbal
description, not an export, and it had propagated into `build_canonical.py`, the
transport authoring guide, `TODO.md`, and a handover already shipped to the
transport team. The staged delta's 160 Key rows were corrected to bare `Gasoline`
and the adapter was fixed this turn (`FUEL_TYPE_MAP` → `FUEL_TYPE_MAP_KA` with
`"Gasoline": "Gasoline"`, plus the matching `KA_SALES_SHARE_FUELS_PER_VEHICLE`
entries — an atomic pair; Edit A without Edit B would have silently dropped all
160 rows through the availability filter). Adapter **not re-run** (delta doctrine).

**Nine residential branches deleted.** `Projections\Air Conditioning\{Best
Practice, Current_Sales Average, Current_Stock Average, Efficient}` and
`Projections\Refrigeration\{High, Low, Medium}` are gone, along with their bare
parents; only the underscore trees survive. **Impact on payloads: none** — no
staged row targets a deleted branch (0 `Demand\Residential\…` references in the
commercial payload; grep clean across all six). Impact on docs: the residential
authoring guide's §6.3 "off-limits pending the double-count question" is now
**resolved by deletion** and was updated this turn.

**`!EER` relocated to Commercial — and this reversed the AC work.** v0.80 adds
`!EER[Btu/Wh]` to commercial's own four AC tiers (288 cells) and, in the same
move, rewrote `Final Energy Intensity` on the three non-anchor tiers to the
sibling-local ratio form, identical in all 72 cells each:

```
Current Stock_Average:!EER[Btu/Wh] / !EER[Btu/Wh] * Current Stock_Average:Final Energy Intensity[kWh]
```

The staged payload's 120 static-ratio rows (`0.55 / 0.70 / 0.90 * Current
Stock_Average:Final Energy Intensity[kWh]`) would have **overwritten correct
canon with a materially wrong approximation** — canon-implied `Current
Sales_Average` is algebraically exactly **0.70** in every region (staged said
0.90, a 29% overstatement everywhere); `Best Practice` canon is 0.24–0.43
(staged 0.55, wiping out roughly half the efficiency gain). So the correct
execution of U2 was **0 rows authored, 120 rows deleted**. See O1.

**Scenario roster 11 → 6.** Survivors: `Current Accounts`, `Set up`,
`Carbon Neutrality_ Net Zero Scenario`, `Baseline Simulation`, `AMS Target
Scenario`, `Regional Aspiration Scenario`. **Zero payload rows target a deleted
scenario.** No payload writes `Set up` (0 rows), so "nothing else" is already
satisfied there. The 10 CNZ rows in the commercial payload were dropped —
independently re-verified as byte-identical to their RAS twins, so nothing in
scope was lost. Current Accounts was **kept and flagged**, not dropped (O2).

---

## 3. THE INJECT COMMAND SEQUENCE

Standard flags on every run: blind mode is default-on (do **not** pass
`--no-blind` — all six payloads are `Demand\` / `Key\` / Transformation targets),
always paired with `--fail-fast` so a missing FullName errors instead of hanging.
`--exclude-timor-leste` on every run (TL disabled in the calc). `--expect-area`
is mandatory on every injector — **substitute the confirmed live area name for
`<AREA>`; do not guess it** (O3).

Put `Current Accounts` **first** in every `--scenarios` list: the framework loops
scenarios in the order given, and CA is the inheritance parent.

```bash
# 1. TRANSPORT — historical CA Stock series (base year, must precede forward work)
python inject/transport/inject_to_leap.py \
  --csv inject/transport/20260721/historical_stock_patch_20260721.csv \
  --scenarios "Current Accounts" \
  --expect-area "<AREA>" --exclude-timor-leste --fail-fast --skip-dry-run -y

# 2. TRANSPORT — audit corrections
python inject/transport/inject_to_leap.py \
  --csv inject/transport/20260721/transport_audit_corrections_20260721.csv \
  --scenarios "Current Accounts,Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" \
  --expect-area "<AREA>" --exclude-timor-leste --fail-fast --skip-dry-run -y

# 3. TRANSPORT — v0.80 delta (Key tree; 160 bare-Gasoline rows)
python inject/transport/inject_to_leap.py \
  --csv inject/transport/20260723/transport_delta_20260723.csv \
  --scenarios "Current Accounts,Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" \
  --expect-area "<AREA>" --exclude-timor-leste --fail-fast --skip-dry-run -y

# 4. COMMERCIAL
python inject/commercial/inject_to_leap.py \
  --csv inject/commercial/20260722/commercial_canonical_20260722.csv \
  --scenarios "Current Accounts,Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" \
  --expect-area "<AREA>" --exclude-timor-leste --fail-fast --skip-dry-run -y

# 5. BIOENERGY
python inject/bioenergy/inject_to_leap.py \
  --csv inject/bioenergy/20260722b/bioenergy_delta_20260722b.csv \
  --scenarios "Current Accounts,Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" \
  --expect-area "<AREA>" --exclude-timor-leste --fail-fast --skip-dry-run -y

# 6. POWER — RAS only
python inject/power/run_workflow.py \
  --csv inject/power/20260722/batch2_ccs_retarget_20260722.csv \
  --scenarios "Regional Aspiration Scenario" \
  --expect-area "<AREA>" --exclude-timor-leste --fail-fast --skip-dry-run -y
```

**Order dependencies.** There are **zero cross-file key collisions** across the
six payloads, so no run can overwrite another's cells — order is advisory, not
load-bearing. Two soft preferences: (a) run the three transport files in the
order above, so the historical CA `Stock` series lands before the forward
fleet/sales anchors that read off the same base year; (b) power last — it is
RAS-only, 32 rows, and independent of everything else. Each command is one COM
session (§A.10); do not fragment a payload across invocations.

If the CA ruling (O2) comes back "drop CA": command 1 disappears entirely, and
`Current Accounts,` comes out of the `--scenarios` list on commands 2–5.

---

## 4. OPEN ITEMS

### BLOCKING

**B1 — U2 was satisfied by deletion, not replacement. Needs your explicit
acceptance.** You instructed "replace these with the !EER RATIO form"; what
happened was 0 rows authored and 120 deleted. The justification is verified —
v0.80 already carries the exact sibling-local ratio form on all 72 cells of each
of the three non-anchor tiers, so authoring would have been an idempotent no-op
at best and a regression to wrong static ratios at worst. But "delete instead of
replace" is a different end state from what you asked for.
**Fix:** accept as-is (recommended — the end state matches U2's intent), or
instruct authoring anyway.

**B2 — 160 stale `fuel` metadata cells; payload no longer reproducible from its
own adapter.** In `inject/transport/20260723/transport_delta_20260723.csv` (and
in the baseline `inject/transport/canonical_leap_inputs.csv`), the `fuel` column
still reads `Blended Gasoline` on the 160 Key rows whose `branch` was correctly
fixed to bare `Gasoline`. **Not a hang risk** — `inject_base` builds the FullName
solely from `row['branch']` and the transport injector defines no
`--filter-fuel`. But the fixed adapter now emits `fuel=Gasoline`, so any future
diff-based or fuel-scoped verification will mis-report, and the earlier "0
violations in any live or staged payload" scan claim is false as written (a
line-level scan hits 320 live rows).
**Fix:** patch the 160 `fuel` cells `Blended Gasoline` → `Gasoline` in both
files (branch column already correct; back up first), **or** record the
divergence explicitly in `GASOLINE_BRANCH_FIX_NOTES_20260723.md`. The patch is
preferable — it restores adapter/payload agreement.

**B3 — `--expect-area` value is unknown.** Every injector sets
`REQUIRE_EXPECT_AREA = True`; the run cannot start without it. Canon is
`aeo9_v0.80` but that is the *export* name; the last recorded inject targeted
`aeo9_v0.73` and `TODO.md` references `aeo9_v0.76`.
**Fix:** read `leap.ActiveArea.Name` off the LEAP title bar and substitute for
`<AREA>` in §3. **Deferred: requires live-area read.**

**B4 — Current Accounts scope ruling.** See O2 below; 491 rows and one entire
file hang on it.

### WARNINGS

**W1 — the earlier report's arithmetic was stale.** "Ship 1,507 of 1,517" and
"CA 521 rows" were pre-drop figures that forgot the 120 route-C deletions. The
correct numbers, recomputed from the files, are in §1: **1,387 shipped, 491 CA,
125 (not 155) commercial+bioenergy CA rows that are exact duplicates of forward
twins.** The structural argument is unaffected; the numbers were not.
**Fix:** already corrected here; use these figures.

**W2 — §A.17 tripwire not written.** The gasoline split has now broken twice.
The gate that would stop a third: assert across `inject/transport/**/*.csv` that
no row whose `branch` starts with `Key\` contains `Blended Gasoline`, and no row
whose `branch` starts with `Demand\Transport\Road` contains a bare `\Gasoline\`
segment. Not written this session because validating a new pytest file requires
running pytest, which is prohibited while LEAP is open
(`tests/test_inject_base.py` reaches `dispatch_leap()`).
**Fix:** write it in the next session, before the transport team's next drop.

**W3 — transport-team erratum owed.**
`outbox/20260721/TRANSPORT_HANDOVER_fixes_and_canon_20260721.md` — already
shipped — tells the team `Blended Gasoline` is the token on **both** trees and
"do not write `Gasoline`." Their next drop will be wrong on 160 rows. A repo edit
cannot unsend it. Logged in `TODO.md`.
**Fix:** erratum in the next transport handover.

**W4 — `result/20260709/_package_teams.py` ships stale structure.** It copies the
v0.67 `structure_handover_20260703/` slices verbatim into outbound team packages.
Any package built today hands a sector team v0.67 structure as "current state" —
including nine residential branches that no longer exist.
**Fix:** regenerate the slices (§6) before building any team package. Flagged,
not fixed, per §A.2.

**W5 — content notes for the commercial team (not blocking, not ours to
change).** Thailand's AC tiers are near-degenerate in v0.80: Best Practice EER
`19` sits barely above Efficient `18.8`, collapsing the two tiers to ratios
0.4266 vs 0.4312 (~1% apart) where every other region shows ~2× separation;
Thailand is also the only region off the `26.9` ENERGY STAR figure. Vietnam's
Efficient (`5.3*3.413` = 18.09) exceeds every other region's. Both are expression
content (§2.6) — flagging only.

---

## 5. STILL REQUIRES A LIVE READ

| # | Deferred read | What it decides |
|---|---|---|
| L1 | `leap.ActiveArea.Name` | The `--expect-area` value. **Blocks every command in §3** (B3). |
| L2 | Has the live area drifted from the 2026-07-23 v0.80 export? | Whether the structural clearances in §1 still hold. Every check above resolves against workbooks, not the running area; a same-day UI edit would not appear. |
| L3 | Does BAS/ATS/RAS hold the corrected commercial AC `Final Energy Intensity` string **explicitly**, or inherit it from CA? | Export Expressions materialises all 72 cells identically and cannot distinguish authored from inherited. Immaterial to shipping (the effective expression is correct either way) — but it is the crux of the CA-drop question (O2). |
| L4 | Live scenario parent chain — which of the six v0.80 scenarios inherit from Current Accounts | Fully costs the CA-drop option beyond the row-level duplicate analysis. |
| L5 | Post-inject readback: `N EXACT / 0 NORMALISED / 0 FAIL` per scenario + a UI eye-test on a multi-scenario branch (§A.20) | Whether the inject actually landed. Cannot run while the interlock holds. |
| L6 | v0.80 node rosters vs `NODE_REGION_LOCK` / `BASE_BRANCH_NODE_ONLY` (`nemo_read/inject_base.py`) | Whether the **sealed** region-lock gate is stale in general. Settled for this ship — the only node-touching payload is power, verified clean against the v0.80 Indonesia walk — but a full re-derivation is outstanding and affects future power/bioenergy cycles. |

---

## 6. STALE CANON SLICES

**`inject/<sector>/structure_handover_20260703/*.csv` are v0.67. Canon is v0.80.
They have not been regenerated.** Every pre-inject gate and audit run before
today resolved against those files.

**What this does NOT affect: the inject itself.** The sealed `_preflight_csv`
(`nemo_read/inject_base.py:343-391`) calls exactly three checkers —
`validate_canonical_csv_expressions`, `find_zero_existing_capacity_conflicts`,
`find_region_lock_violations` — and **none of them opens a file other than
`csv_path`**. The region-lock checker resolves against module-level frozen dicts,
not the slices. Subclass `extra_csv_validators()` adds nothing that reads them
(fossil/bioenergy check only for a sibling `canonical_leap_native.csv`;
transport, commercial, power, residential add none). An inject cannot pass or
fail because of a stale slice.

**What this DOES affect:** (a) our offline audit surface — the branch-path /
variable / unit checks, the `!EER` question, the gasoline gate were all resolved
against v0.67 material and had to be re-resolved against the v0.80 workbooks this
cycle; (b) outbound team packages, via `result/20260709/_package_teams.py` (W4);
(c) `phase0_connection_audit.py:164` reads
`inject/<team>/structure_handover_20260703/keys_slice_<team>.txt` as its diff
baseline — the one place the old slices are consumed by code, and exactly the
right comparison for a v0.67→v0.80 delta report.

**Remediation** — a 4-script offline chain (no COM; safe with LEAP open). All
four scripts hardcode a scratch dir belonging to a dead session, now empty;
**repoint the path constant in each before running**:

1. `python "LEAP structure/tools/digest_leap_structure.py"` (edit `OUT`, line 11)
2. `python "LEAP structure/tools/tree_and_scenario.py"` (edit `DIG`, line 13)
3. `python "LEAP structure/tools/gen_current_state.py"` (edit `DIG`, line 11)
4. `python "LEAP structure/tools/phase0_connection_audit.py"` (edit `DIG`, line 12)

Then **manually copy** `<scratch>/team_artifacts/<team>/*` into a **new**
`inject/<team>/structure_handover_20260723/`. No tool does this copy. Do **not**
overwrite the `_20260703` directory — it is the only v0.67 reference the gap
audit has. The scripts' 4-scenario scope (CA / BAS / ATS / RAS) is already a
subset of the surviving six; no edit needed, and it keeps CA in.

Out of scope this cycle — flagged, not done.

---

## 7. OPEN QUESTIONS FOR THE OPERATOR

**O1 — Accept the AC re-link as a deletion (120 rows removed, 0 authored)?**
v0.80 already carries the exact `!EER` sibling-ratio form you asked us to
author, on all 72 cells of each non-anchor tier. Authoring would have been a
no-op; the staged static ratios it would have replaced were wrong (`Current
Sales_Average` is algebraically exactly 0.70 everywhere, staged 0.90; `Best
Practice` canon 0.24–0.43, staged 0.55). **Cost of accepting: zero — the model is
already correct.** Cost of insisting on authoring: we overwrite correct canon
with a cruder region-flat approximation. **Recommend: accept.**

**O2 — Current Accounts: keep (recommended) or drop?** U3 said "BAS ATS RAS,
nothing else"; the anatomy records your same-day written scope as *"what matters
for us **still** CA BAS ATS RAS."* We kept CA and are surfacing the cost rather
than deleting silently.

Dropping CA costs **491 rows**, in three distinct ways:

- **200 rows have no other home.** `Stock` and `First Sales Year` are
  structurally CA-only (anatomy §9.2 + the v0.80 fingerprint table — the delta,
  not baseline prose). `historical_stock_patch_20260721.csv` **becomes empty**
  (all 160 die), reopening transport audits A4/A6a/A6b and leaving the corrupted
  live CA `Stock` series in place; audit A9c (40 `First Sales Year` rows) dies
  with it. There is no BAS/ATS/RAS slot to re-target these into.
- **83 transport-delta rows** are 2005–2024 base-year fleet and sales-magnitude
  anchors with no forward twin; a further **52** CA rows carry genuinely
  different historical expressions from their forward twins (verified split:
  83 no-twin / 52 twin-differs / 0 twin-identical).
- **125 commercial + bioenergy CA rows** are exact duplicates of forward twins,
  so no forward cell is lost — but dropping them forks the CA→2025 seam,
  including the Philippines FAME `Exogenous Capacity`
  `* 10^6 * ConvFuelUnits(…)` fix, which would leave base-year Philippine
  biodiesel capacity off by six orders of magnitude on the exact branch being
  repaired.

CA is the inheritance parent of BAS/ATS/RAS, not a competing fourth scenario.
Treating the new phrasing as a CA deletion requires assuming a silent same-day
reversal of a written directive. **Recommend: keep. Ship 1,387 of 1,387.**

**O3 — What is the live area name for `--expect-area`?** Canon is `aeo9_v0.80`;
the last inject targeted `aeo9_v0.73`; `TODO.md` cites `aeo9_v0.76`. One word
from the LEAP title bar unblocks §3. **Blocking.**

**O4 — Patch the 160 `fuel` metadata cells, or record the divergence?** (B2.)
Not a hang risk either way. Patching restores adapter/payload agreement and
keeps future diff-based verification honest; recording is faster. **Recommend:
patch.**

---

*Not a green light. Four items (B1–B4 / O1–O4) are answerable in minutes; nothing
structural stands in the way once they are.*
