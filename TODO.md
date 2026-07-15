# In-flight work — pick up here

> **Cross-session pickup note.** This file is what a fresh Claude
> session reads first (CLAUDE.md §0). It tells you what's pending
> across sessions. Update or empty it whenever a major piece of work
> completes.

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
