# Answers to power-team questions — v0.69 RAS results package (2026-07-07)

Concise answers, each verified against the solved DB (`NEMO_25 41.sqlite`),
the canon tree, and our inject layers. Where we cannot prove something
offline, we say so.

---

## 1. Unmet-load unit — you were right, our header was wrong

The result CSVs' energy values are **PJ**, not GWh. Calibration proof:
Coal Subcritical_IDJW holds 38.3 GW (max possible 1,208 PJ/yr); its
recorded 2050 production is 772.1 → CF 0.64 (plausible). Read as GWh that
would be CF 0.06% (absurd). Your ×3.6 observation is exactly TWh→PJ.

**Indonesia East 2060 unmet = 2,370 PJ = 658 TWh.** Neither of your two
candidates — it is the big one. Corrected unmet table:

| Node | 2040 | 2050 | 2060 (TWh) |
|---|---|---|---|
| Indonesia East | 90 | 375 | **658** |
| Indonesia Sumatra | 8 | 159 | **388** |
| Indonesia Kalimantan | 76 | 218 | **362** |
| Malaysia Sarawak | 45 | 66 | **69** |
| Malaysia Peninsular | – | 11 | 10 |

This upgrades the unmet finding from footnote to **first-order problem**:
the outer-Indonesia nodes are short by hundreds of TWh. Your node work is
the right priority. Cross-checked against the LEAP xlsx to the decimal:
its generation sheet shows `Unmet Load_IDEast 2060 = 658.42` (TWh) =
sqlite `2,370.3 PJ ÷ 3.6`. (v2 result extracts carry per-column unit
stamps; apologies for the mislabel.)

**One more dimension the xlsx adds — unmet CAPACITY (GW, 2060):**
`Unmet Load_IDJW` = **287.6 GW**, IDEast = 102.9 GW. Jamali's unmet
*energy* is small (7 TWh) but its unmet *capacity* is the largest in the
model — a peak/reserve-margin shortfall, not an energy shortfall. Plan the
node work on both axes: energy for the outer islands, peak capacity for
Jamali.

## 2. Duplicate Biomass Gasification — it's the HYDROGEN module

Two distinct branches share the leaf name:

- `Transformation\Centralized Electricity Generation\Processes\Biomass Gasification`
  (NEMO P2731, produces Electricity) — **your branch; only 7.1 GW built.**
- `Transformation\Hydrogen Production for Energy Use\Processes\Biomass Gasification`
  (NEMO P14988, produces Hydrogen) — **the optimizer builds 400.6 GW here.**

Your costs/caps bind only the first. **Do not merge** — different modules,
different products. To contain it: author delta rows (Capital/O&M cost +
Maximum Capacity) on the Hydrogen-module branch path above. Siblings in the
same module you may want to cap in the same pass: SMR, SMR with CCS, Coal
Gasification (±CCS), Biomass Gasification with CCS, PEM Electrolysis.
Hydrogen wiring: H2 Fuel Cell consumes fuel `Hydrogen` produced by those
processes. A `Hydrogen` branch exists in the Resources tree, but we have
not verified any Import/Production Cost is authored on it — as it stands,
hydrogen's price is purely feedstock + process cost in the H2 module.

## 3. H2 Fuel Cell — the area's inherited parameters (never authored by you)

From the export (uniform across regions, Indonesia shown):
- **Capital Cost:** 1,635.9 (2025) → 1,333.8 (2030) → 1,214.1 (2040) → 1,094.4 (2050+) thousand USD/MW
- **Efficiency:** 50% (IAR Hydrogen = 2.0 per unit output, OAR Electricity = 1.0)
- **Lifetime:** 10 years
These are v0.67 modeller defaults. Cheap capex + short lifetime + 50%
efficiency is why the LP over-builds it (188 GW Indonesia). Cost review =
same pass as #2.

## 4. Stranded Cost — NEMO never sees it

Verified: **no stranded-cost table exists in the NEMO export at all.** The
variable is LEAP-side accounting only; the zeros are inert for
optimization. Its LEAP semantics (per what quantity) we have NOT verified —
if you intend to use it, author one test value on one branch and we read
the LEAP cost report after the next calc; do not author fleet-wide on an
unverified unit basis.

## 5. Must-run in optimized RAS = Minimum Utilization (Dispatch Rule verified inert)

We checked **both** levers:

- **Dispatch Rule** exists and is authored — `MeritOrderDispatch` on the
  generation fleet (plus `FullCapacity` on some techs) — but **only in
  CA / Baseline / ATS. RAS carries zero Dispatch Rule rows, and no
  dispatch-rule table exists in the NEMO export at all.** It is LEAP's
  simulation-dispatch knob; in an optimized scenario NEMO owns dispatch
  and never sees it.
- **Minimum Utilization** → NEMO `MinimumUtilization`, enforced by the
  `MinimumTechnologyUtilization` constraint (visible in your solver log).
  The RAS export carries 12,240 non-zero MU rows on power techs (e.g.
  Cambodia Coal Subcritical 0.569, Brunei Gas Turbine 0.415) — the
  historical-CF `Min(..., Maximum Availability)` floors = take-or-pay.

**Verdict (updated per decision 2026-07-07): two-part setup.**
1. **ATS + BAS flip to full dispatch** — MeritOrderDispatch allows partial
   dispatch of the marginal plant; per decision, every generation process
   currently on `MeritOrderDispatch` in ATS/BAS becomes **`FullCapacity`**
   (the string the area already uses on e.g. PH Wind Offshore). Delta
   payload: `dispatch_rule_fullcapacity_delta.csv` (in this package) — 448
   rows (224 ATS + 224 BAS, 75 process families × regions; the 124 slots
   already FullCapacity untouched; CA untouched).
   **STATUS: authored, NOT yet injected** — it goes into the area in one
   batch together with your next round of edits, so send your deltas and
   we push everything in a single cycle. Until then the area's ATS/BAS
   still dispatch merit-order.
2. **RAS keeps Minimum Utilization as the only dispatch lever** — Dispatch
   Rule remains inert there (zero rows, no NEMO table); the MU experiment
   proceeds as reversible delta rows.

**Reversibility for run 2: clean.** MU is per-tech data, not structure.
Delta rows setting `Minimum Utilization = 0` (or a different floor) flip
the experiment; the original expressions are preserved in the baseline
dumps for exact restore. Never author bare `Maximum Availability` as MU —
keep any floor wrapped in `Min(..., Maximum Availability)`.

## 6. Dead fleets — nothing is missing; the causes are economics and wiring

- **Vietnam Nuclear LWR (14 GW, zero generation):** all parameters present
  and sane — IAR Nuclear 2.5 (40% eff), OAR 1.0, availability rows,
  Variable OM 1.42, and both supply routes exist (`Nuclear Domestic
  Production` + `Nuclear Imports`, with cost rows). Nothing to add — it
  simply never wins dispatch. Check the nuclear fuel price and compare
  against the (currently underpriced) H2/biomass backstops from #2/#3; fix
  those first and nuclear likely starts running.
- **Vietnam GCC-CCS (10 GW at 2060, zero generation):** parameters present,
  but its input wiring requires **BOTH Hydrogen (0.974) AND Natural Gas
  (0.968) simultaneously** per unit of output. If this plant is meant to
  burn gas with CCS (not H2 co-firing), the Hydrogen co-input is a data
  error on the Feedstock Fuels sub-branches — your call to fix; that dual
  burden plus CCS cost is why it idles.

## 7. PH Wind Offshore — the rogue value FOUND, already purged, ATS clean

The "illogical 2040 retirement" was never in `Capacity Retirement` (0 in
all scenarios, all layers). It hid in the v0.67 **RAS `Capacity
Additions`** expression as a **negative addition**:

```
Add(..., 2039, 2000, 2040, -19000, 2041, 21000, ...)
```

−19 GW "added" in 2040, +21 GW in 2041 — vintage bookkeeping, in a
corrupted cell that even contained TWO concatenated Add() expressions with
an embedded line break. **Your sendback replaced that expression with the
clean series, our inject landed it, and the solved DB proves it**: PH Wind
Offshore capacity = 5.3 GW (2040) → 19.5 GW (2050), exactly the cumulative
of the clean `Add(2028, 2000, …, 2050, 300)` — no dip, no spike. ATS was
always clean (no negatives in its series, retirement 0). Nothing left to
remove; keep the clean series in future revisions.

## 8. Export hygiene — all accepted, v2 package will fix

| Item | Status |
|---|---|
| Branch-ID column | v2 adds NEMO tech ID + LEAP branch path |
| Module filter | v2 keys by tech ID scoped to the generation modules — the 1e12 "Diesel" rows are the *Diesel Blending* pseudo-tech (name collision, known §A.11 sentinel, deliberately untouched), they disappear from power views |
| Unit stamps | v2 stamps every column (energy = PJ, capacity = GW); see #1 |
| Swapped xlsx sheet names | **Confirmed** — the TAB names are swapped; the in-sheet titles (cell A1) are correct: tab "Generation" holds *Capacity* (GW), tab "Capacity" holds *Outputs* (TWh). Trust the A1 titles until v2 renames the tabs |
| Ghost `_MYKA` branches | Confirmed real in the area: `Geothermal Flash_MYKA` + `Large Hydro_MYKA` exist as branches with ZERO data anywhere (no exogenous rows, no results). Not canon (Malaysia = PE/SB/SR only). Flagged to the modeller for deletion; do not author to them |
| 61 missing 2025 generation rows | NEMO saves only non-zero values — those techs produce 0 in 2025 (mostly fleets that start later). Not data loss; v2 emits explicit zeros |
| Large Hydro_IDKA 2060 row | Capacity exists (2.356 GW in 2060) but production saves no 2060 row — i.e. recorded output 0. Given the MU floors on hydro that is genuinely odd, not just save-suppression; we are investigating and it ships in v2 either way |

## 9. Cleaning log — pointers (informational)

- **197 dropped** = 113 structural (non-existent `Small Hydro_MY*`, wrong-
  scenario Maximum Capacity / Endogenous Capacity slots, 5 stale v0.67
  values) itemized in `CLEANING_NOTES_20260707.md`, **plus 84** Indonesia
  base-branch rows (fleet vars on `Biogas`/`Gas Engine`/`Gas Turbine`/
  `Geothermal Flash` — Indonesia authors on `_ID*` nodes only) itemized in
  `BASE_BRANCH_REMOVED_NOTES_20260707.md` (attached; includes the 3
  variables you must re-author per node if the data is real).
- **84 added** = the Singapore base-branch fleet rows — those came from
  *your own* `power_sendback_20260707.zip` (the +84 delta vs your 20260706
  version); we added nothing of our own.

---
*Reminder from the results README: future cycles are delta-payloads only —
send just the rows you change, against the `power_sendback_canonical_FINAL.csv`
baseline.*
