# In-flight work — pick up here

> **Cross-session pickup note.** This file is what a fresh Claude
> session reads first (CLAUDE.md §0). It tells you what's pending
> across sessions. Update or empty it whenever a major piece of work
> completes.

## Status as of 2026-07-07 (power v0.69 RAS cycle — SOLVED + shipped)

**The power sector's RAS run solves and results are shipped to the team.**
Latest commit `629ae2f`; repo in sync with origin/main.

**Done this cycle (2026-07-04 → 07-07):**
- Power team's v0.69 sendback cleaned (9,534 → 9,337) and injected into
  `aeo9_v0.69`, all 4 scenarios, readback 40 EXACT / 0 FAIL.
- **§A.23 base-branch authoring lock** shipped — `BASE_BRANCH_NODE_ONLY`
  + class-2 check in `find_region_lock_violations`, sealed pre-flight +
  CI tripwires. Caught/removed 84 Indonesia base-branch rows (Biogas /
  Gas Engine / Gas Turbine / Geothermal Flash — Indonesia authors on
  `_ID*` nodes only) that had triggered the live "no branch … in
  Indonesia" inject error.
- Framework fixes: group-label `'Other'` no longer leaks to
  `leap.Regions()`; region-major row sort + ActiveRegion read-before-set
  = 21× inject speedup (~260 rows/min).
- **4 RAS MaxCap-vs-ExoCap violations** found via offline accounting
  (`inject/power/20260707/_probe_maxcap_accounting*.py`) and fixed with
  `Max(Exogenous Capacity[MW], <cap>)` — Cambodia Wind Onshore, PH Small
  Hydro, Vietnam Wind Onshore, Malaysia Large Hydro_MYPE. RAS now solves
  (`feas/NEMO_25 41.sqlite`). §11.2e documents the Max() numeric-first
  year-parse trap.
- **Delta-payload doctrine** adopted (CLAUDE.md §4): from now on inject
  ONLY edited rows; canonical stays as the baseline mirror.
- Power team Q&A (9 questions) answered + shipped.

**SHIP-READY in `outbox/` (send to power team — user's channel, not auto):**
- `power_qa_answers_20260707.zip` — the 9 answers + `dispatch_rule_
  fullcapacity_delta.csv` + cleaning/base-branch notes.
- `power_results_ras_v069_20260707_r2.zip` — result CSVs (unit-verified
  PJ/GW/MUSD), the 4-row MaxCap fix delta, the 9,337-row canonical
  baseline, LEAP xlsx. (The non-r2 zip is superseded — do NOT send it.)

## What's pending — pick up in this order

### 1. Joint power inject — NEXT cycle, waiting on the team's edits
The **FullCapacity dispatch delta is authored but NOT injected**:
`inject/power/20260707/dispatch_rule_fullcapacity_delta.csv` (448 rows,
ATS+BAS, MeritOrderDispatch → FullCapacity; lock-clean). Per user: it
goes in ONE batch alongside the power team's next round of edits — do
not inject it alone. When the team drops their deltas (they were told
to send deltas, not full files):
- Merge their delta + our dispatch delta into one canonical.
- §A.9 confirm `aeo9_v0.69` open + idle, then inject (blind, fail-fast).
- Recalc RAS (+ ATS/BAS if they want the dispatch experiment measured),
  re-harvest, verify.

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
