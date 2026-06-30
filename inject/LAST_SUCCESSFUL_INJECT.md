# Last successful inject — reference

> **Rolling pointer.** This file names the most recent inject that
> completed cleanly end-to-end. It is the gold-standard reference for
> the inject method until a newer successful inject replaces it.
> **When the next inject succeeds, update this file** (command, log,
> outcome, date) so it always points at the current known-good run.

---

## Current reference: residential AC + fridge — FULL inject, 2026-06-30, `aeo9_v0.64`

**Sectors:** residential — **Air Conditioning + Refrigeration**, full set
(Key drivers + leaf Efficiency + RAS device-stock block).
**Area:** `aeo9_v0.64`
**Scope:** 10 ASEAN AMS × 3 scenarios (Baseline Simulation / AMS Target
Scenario / Regional Aspiration Scenario).
**Outcome (each appliance):** BAS 250 + ATS 250 + RAS 790 = **1,290 writes**,
**30/30 readbacks EXACT** (0 NORMALISED, 0 FAIL), `=== DONE === (clean)`.
**2,580 writes total across both, 60/60 EXACT. User-confirmed.**

### What was authored (both AC + fridge)

- **Key tree** `Key\Residential\<App>\` (variable `Activity Level`, `Interp`):
  `Percent Ownership` (AC `units_per_hh_parent` units/HH; fridge
  `ownership_parent_pct` %), `Size_Share\<Size>`, `Efficiency_Share\<Size>_<Eff>`,
  `Useful_EI\<Size>`. Ownership + Useful_EI untagged (scenario-invariant);
  Size_Share + Efficiency_Share per-scenario.
- **Demand leaf** `Demand\Residential\Projections\<App>_\<Size>\<Eff_eff>`:
  - `Efficiency` ← `efficiency_pct` — **all scenarios** (untagged).
  - `Unit Capacity` ← `unit_capacity_kw` — **RAS-only**.
  - `Capital Cost` ← **`price_usd`** (full capital; LEAP annualizes by Lifetime,
    per LEAP doc) — RAS-only.
  - `Variable OM Cost` ← `om_electricity_usd` — RAS-only.
  - `Fixed OM Cost` ← `0` — RAS-only.
  - `Lifetime` ← **15 (AC) / 12 (fridge)** — RAS-only.
  - `Exogenous Devices` ← `<app>_exo_device.csv` × 1000, **2005→2060** retirement
    series — RAS-only.
  - `<App>` = `Air Conditioning` / `Refrigeration`.

The device-stock block is **RAS-only** (those vars don't exist under BAS/ATS),
so it's force-tagged RAS in the canonical; the scenario filter routes it to RAS
only. BAS/ATS therefore push Key + Efficiency (250); RAS pushes everything (790).

### >>> HOW TO REPEAT ON A NEW LEAP FILE <<<

The canonicals are area-independent — **only the target area changes.** To
repeat the exact success on a new `.leap` area:

1. Open ONLY the new area in LEAP; click into it (focused/active). Confirm its
   regional decimal = period. It MUST already have the `Air Conditioning_` /
   `Refrigeration_` 2-layer trees + `Key\Residential\{Air Conditioning,
   Refrigeration}` stores (same structure as `aeo9_v0.64`; the inject does NOT
   build branches).
2. Run (from `inject/residential/202060630/`):
   ```
   python build_canonical_full.py --appliance ac       # -> canonical_ac_full.csv (1030 rows)
   python build_canonical_full.py --appliance fridge    # -> canonical_fridge_full.csv (1030 rows)

   python ../20260625/inject_fridge_leap.py --csv canonical_ac_full.csv \
       --expect-area "<NEW AREA NAME>" \
       --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" --yes
   python ../20260625/inject_fridge_leap.py --csv canonical_fridge_full.csv \
       --expect-area "<NEW AREA NAME>" \
       --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" --yes
   ```
   (Rebuilding the canonical is optional if the source CSVs are unchanged — the
   existing `canonical_{ac,fridge}_full.csv` can be reused as-is.)
3. The dry-run gates each scenario (zero writes on any `branch_not_found` /
   `var_not_found`); confirm `1290 writes, 30 EXACT, DONE (clean)` per appliance.
4. **Save the new area** in LEAP.

> **Validated 2026-06-30:** this recipe was repeated clean to a second area,
> `aeo9_v0.65_beta1` — AC + fridge, 1290 writes/appliance, 60/60 EXACT, only
> `--expect-area` changed. The repeat is proven.

If the area name differs and the lock aborts (`ActiveArea is X, expected Y`),
just set `--expect-area` to X. If `ActiveArea` comes back `''` (the §11.1
spontaneous-blank), re-focus LEAP and rerun — the lock aborts with zero writes.

### Method / function used — NOTE: not the framework

Self-contained portable injector
[inject/residential/20260625/inject_fridge_leap.py](residential/20260625/inject_fridge_leap.py)
(pywin32 only, no `nemo_read` import). Reproduces inline: Interp comma/period
chokepoint, area lock, per-scenario set+verify, scenario-column filter,
per-region ActiveRegion, read-back EXACT. **Builds the FullName index ONCE**
(area-wide), then hang-safe blind writes (existence-check then
`leap.Branches(FullName)`). Dry → real → readback, all in ONE COM session.
Adapter: [inject/residential/202060630/build_canonical_full.py](residential/202060630/build_canonical_full.py)
(`--appliance ac|fridge`).

### Logs (this run)

[inject/residential/202060630/_inject_ac_full.log](residential/202060630/_inject_ac_full.log) ·
[inject/residential/202060630/_inject_fridge_full.log](residential/202060630/_inject_fridge_full.log)
(both 2712 lines, 1290 `[OK]` + 30 `[EXACT]`, zero failures).

### Truth references

[inject/residential/AC_ANATOMY.md](residential/AC_ANATOMY.md) ·
[inject/residential/FRIDGE_ANATOMY.md](residential/FRIDGE_ANATOMY.md).

### Outstanding (does NOT block this being the reference)

- **Save the LEAP area** to persist the writes.
- **AC `Energy Load Shape`** — upload the 10 `<Country>_AC_Cooling` named shapes
  to LEAP separately (not part of the inject), then the leaf references them.

---

*Previous reference: residential fridge Phase-1 Key + Phase-2 leaf
(Efficiency + Exo), 2026-06-25→29, `aeo9_v0.64(_w_result)` — superseded by this
full AC+fridge inject. Before that: transport, 2026-05-20, `aeo9_v0.47`.*
