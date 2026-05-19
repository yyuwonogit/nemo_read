# In-flight work — pick up here

> **Cross-session pickup note.** This file is what a fresh Claude
> session reads first (CLAUDE.md §0). It tells you what's pending
> across sessions. Update or empty it whenever a major piece of work
> completes.

## Status as of 2026-05-19

**Done 2026-05-18 / 19:**
- **Bioenergy fully resolved.** The 8-biomass-items gap (Wood, Charcoal,
  Bagasse, MSW, Biogas, Other Biomass, Efficient Wood, generic Biomass)
  closed. Final unlock was authoring **POME Import Cost** — that was
  the remaining hole letting Brunei pull POME at LEAP-default ≈ 0 cost.
  Verified clean by user against the LEAP UI biodiesel-production table.
  No more Timor-Leste-style or Brunei-style routing leakage on
  bioenergy supply.

**Done since 2026-05-17:**
- Workstream 1 (`CanonicalInjector` + `CanonicalProber` frameworks)
- Workstream 1.5 (`Interp()` separator §A.15 enforcement — 3-layer)
- Workstream 2 (repo reorg: `mailbox/` + `inject/` + `result/`)
- v0.6.9 — public API re-exports (CanonicalInjector / CanonicalProber
  / HeartbeatLogger discoverable at top level)
- v0.6.10 — flexible variable filters (--all-vars / --result-vars)
- v0.6.11 — inner-loop heartbeat tick (mid-region progress visible)
- v0.6.12 — emission vars + projection layers auto-skip default
- v0.7.0 — Timor Leste supplement mandatory (§A.18; mutually-
  exclusive --include-timor-leste / --exclude-timor-leste flags)

**First real full-area probe done:**
- aeo9_v0.45 RAS scenario, Indonesia, Demand subtree, `--all-vars`
- 4h06m wall-clock, 33,116 rows, 1944 branches, 50 distinct variables
- Output: `output/probe/demand_indonesia/results_Regional_Aspiration_Scenario.csv`

**Operational state (as of 2026-05-18):**
- Timor Leste DISABLED from LEAP calc by user. Don't fret about TL
  §A.11 leakage. Use `--exclude-timor-leste` on all injects until
  user re-enables. See
  [`memory/project_timor_leste_disabled.md`](../../memory/project_timor_leste_disabled.md).

## What's pending — pick up in this order

### 1. Transport sector inject — NEW DOMAIN (in-scope as of 2026-05-19)

**Scope (user-confirmed 2026-05-19):**
- LEAP area: **`aeo9_v0.46`** (note: bumped from v0.45 to v0.46 between
  bioenergy-fix landing and transport scope confirmation)
- Sector: **Demand side ONLY** — `Demand\Transport\...` subtree
  - Vehicle stocks, fuel shares, activity levels, fuel economy
  - NO transformation-side (no vehicle production etc.)
- Scenarios: **BAS, ATS, RAS** (all 3 in one warm-COM session via
  `--scenarios "BAS,ATS,RAS"`)
- Timor Leste: **excluded** (operational state, per
  `memory/project_timor_leste_disabled.md`); use
  `--exclude-timor-leste` flag

**Pending: input data from user.**
- User will drop the transport CSV in `mailbox/<YYYYMMDD>/`
- User will signal explicitly when it's there ("not yet")
- Do NOT pre-create files in mailbox/; just inspect when user signals

**Pre-inject work to do BEFORE user drops the CSV (optional, can start now):**
- Probe v0.46 LEAP area's Demand\Transport subtree for ALL 3 scenarios
  via `CanonicalProber` with `--all-vars` to discover:
  - What transport-related variable names LEAP v0.46 exposes
    (Activity Level, FuelEconomy, Vehicle Distance, Device Stocks, etc.
    — confirmed from the prior v0.45 Indonesia/Demand probe)
  - What branch shape transport has (sub-modes: Road, Rail, Air,
    Marine, Domestic / International splits)
  - What's there for ASEAN-10 vs what's missing
- Use the v0.6.12 defaults (emission auto-skip + projection-layer skip);
  per the bioenergy-resolved memory, also watch for **pair-completeness:**
  every Maximum Production / Maximum Capacity must have a companion
  Production Cost / Variable OM Cost or the LP routes via cost ≈ 0
- §A.9 confirmation needed before launching: confirm LEAP UI has
  `aeo9_v0.46` loaded as ActiveArea + appropriate scenario in dropdown

**Once input arrives + probe results land — standard new-domain workflow:**
- Per CLAUDE.md §5 + §5.1, scaffold `inject/transport/`:
  - `transport_leap_input.csv` (user-authored, dropped via mailbox)
  - `build_canonical.py` (adapter → canonical_leap_inputs.csv)
  - `inject_to_leap.py` (CanonicalInjector subclass)
  - `timor_leste_supplement.csv` (per §A.18 mandatory; seed zeros)
  - `TRANSPORT_CSV_SPEC.md` + `CSV_AUTHORING_GUIDE.md`
- Standard inject cycle (per docs/FLOWS.md §1):
  dry-run → confirm → real inject → readback → recalc → re-probe

### 1b. (RESOLVED 2026-05-19) ~~Extend bioenergy canonical for 8 missing biomass items~~

**Why this matters NOW.** With Timor Leste disabled, the §A.11 1e12
Unlimited trap shifted the LP's preferred "free supply" region to
**Brunei** (or whoever's next alphabetically). The user verified in
LEAP UI that biomass-production redirection is now landing on Brunei.

**Root cause.** Our bioenergy canonical authors 7 primary crops +
3 secondary fuels (Palm Oil, POME, Coconut Oil, Sugarcane, Cassava,
Corn, Molasses; Biodiesel, Ethanol, Methanol). But the v0.45 LEAP
area has 8 ADDITIONAL biomass items as branches that we never
authored:

  1. Wood
  2. Efficient Wood
  3. Charcoal
  4. Biomass (generic)
  5. Other Biomass
  6. Bagasse
  7. Municipal Solid Waste
  8. Biogas

For each of these × all 11 AMS, LEAP defaults apply:
`Maximum Production = Unlimited` (→ 1e12 in NEMO via §A.11) +
`Production Cost ≈ 0`. LP routes biomass-power demand to the
cheapest "free unlimited" source — currently Brunei.

**Work to do (~176 new rows + adapter extension):**

a) **Research per-AMS values** for each of the 8 items:
   - `Maximum Production`: 0 for AMS where this isn't produced;
     finite trajectory where it is (e.g. Indonesia has substantial
     POME-adjacent biomass, Malaysia has Bagasse from sugar mills,
     Thailand has rice husk / Bagasse, etc.)
   - `Production Cost` (or `Import Cost` for traded fuels):
     market-derived per-tonne or per-GJ figure with citation
   - `Maximum Imports` / `Export Benefit` if relevant
   - Unit choice per CLAUDE.md §2.4 — for biomass that maps cleanly
     to LEAP's GJ-equivalent Primary fuel pattern, use that anchor

b) **Add source CSVs under `inject/bioenergy/`:**
   - Likely one per item or one combined `solid_biomass_supply.csv`
   - Match the existing `bioenergy_leap_input.csv` column shape
     (region, branch, variable, expression, unit, fuel, source, note)

c) **Extend `inject/bioenergy/build_canonical.py`** to register the
   new source CSV(s), broadcasting across AMS via the existing
   `ALL_10_AMS` machinery (NOT adding Timor Leste rows since TL is
   disabled — TL goes into `timor_leste_supplement.csv` per §A.18).

d) **Run `python inject/bioenergy/build_canonical.py`** to regenerate
   `canonical_leap_inputs.csv`. The `_normalize_interp` adapter
   normaliser + the §A.15 pre-flight scan will catch any Interp()
   separator issues.

e) **Inject + recalc + verify:**
   - `python inject/bioenergy/inject_to_leap.py --scenarios "RAS" --expect-area "aeo9_v0.45" --exclude-timor-leste` (per §A.18 mandatory choice)
   - `calculatescenario` in LEAP UI for RAS
   - Re-probe Indonesia Demand to verify Brunei is no longer the leak
     point. Same probe command:
     ```
     python .\dist\probe_v045.py --scenarios "RAS" --expect-area "aeo9_v0.45" --branch-prefix "Demand\" --regions "Indonesia" --all-vars --out-dir ".\output\probe\demand_indonesia_v2"
     ```

**Stop-gap option (if real values aren't researched yet):**
   Author all 8 × 11 AMS with `Maximum Production = 0` and arbitrary
   non-zero `Production Cost` as a temporary zero-supply patch. Stops
   the §A.11 leak but loses any actual biomass-power dispatch in the
   model. Per the 2026-05-18 conversation, the user marked this as
   IN SCOPE, so the real fix (researched values) is preferred over
   the stop-gap.

**Reference for the bioenergy team:**
   [`inject/bioenergy/CSV_AUTHORING_GUIDE.md`](inject/bioenergy/CSV_AUTHORING_GUIDE.md)
   — convention for column shapes, units, off-limits patterns.

### 2. (Carry-over from previous session) Other LEAP-area probes

If the user wants to expand probe coverage from Indonesia/Demand:

- **All 11 AMS, Demand subtree, RAS** — ~24h wall-clock with v0.6.12
  defaults (emissions + projection layers auto-skipped). Already
  produces useful data.
- **Indonesia, Transformation subtree, RAS** — to validate
  Transformation-side variable naming for the eventual
  per-sector probe configs.
- **Other scenarios (BAS, ATS, CA)** for Indonesia/Demand — gives
  scenario comparison once a single scenario is fully working.

Hold until user signals priority.

### 3. (Deferred from earlier sessions, lower priority)

- v0.38 cycle read-back-one verify / calc / post-calc validate.
  Likely stale now that v0.45 is in use.

## When in doubt
- Re-read [CLAUDE.md §A](CLAUDE.md) hard rules
- [docs/FLOWS.md](docs/FLOWS.md) for the standardised inject /
  probe / infeas flows
- Memory: `MEMORY.md` for user preferences + project context
