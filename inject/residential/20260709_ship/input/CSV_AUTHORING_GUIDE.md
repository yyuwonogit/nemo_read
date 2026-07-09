# Residential CSV — Authoring Guide

Unified authoring reference for the residential domain — lighting +
the Air Conditioning / Refrigeration device-stock pipelines, and the
frame every future residential end use (Cooking, TV, Fan, …) must fit.
This guide **unifies** the per-appliance documents; it does not replace
them as deep dives:

| Document | What it stays authoritative for |
|---|---|
| [AC_ANATOMY.md](AC_ANATOMY.md) | AC structure detail, derived relationships, constants, inject history |
| [FRIDGE_ANATOMY.md](FRIDGE_ANATOMY.md) | Fridge structure detail, Key-node values, leaf variants history |
| [20260625/FRIDGE_AUTHOR_GUIDELINE.md](20260625/FRIDGE_AUTHOR_GUIDELINE.md) | The author-facing fridge CSV contract (Phase 1/2 cycles) |
| [202060630/ac/ac_leap_input_mapping.md](202060630/ac/ac_leap_input_mapping.md) + [202060630/fridge/fridge_leap_input_mapping.md](202060630/fridge/fridge_leap_input_mapping.md) | Column-by-column source mapping for the 2026-06-30 full inject |
| [structure_handover_20260703/README_RESIDENTIAL_CANON_STRUCTURE.md](structure_handover_20260703/README_RESIDENTIAL_CANON_STRUCTURE.md) | The team-facing canon package (what we sent the residential team) |

**Truth hierarchy** (CLAUDE.md §2.6 canon supremacy): the
`LEAP structure/` canon exports from `aeo9_v0.67_w_results`
(2026-07-02) outrank every document above for branch paths, variable
names, units, and scenario/region rosters. Where a per-appliance doc
and canon disagree, canon wins — the known disagreements are flagged
inline in §3 and §7 below. Expression *values* are not canon — only
structure.

---

## 0. Status + scope

**Current LEAP area:** `aeo9_v0.67_w_results` (the area the canon
structure exports were taken from). Note
[inject_to_leap.py](inject_to_leap.py) still carries
`EXPECT_AREA = "aeo9_v0.46"` from the lighting cycle — stale; update
and re-confirm with the user (§A.9) before the next framework push.

**What has landed** (all user-confirmed clean):

| Cycle | Target | Area | Rows |
|---|---|---|---|
| 2026-05-21 lighting | `Demand\Residential\Projections\Lighting\Electricity\<Tech>` — Activity Level + Bulb Wattage | `aeo9_v0.46` | 200-row canonical |
| 2026-06-25 fridge Phase 1 | `Key\Residential\Refrigeration\*` drivers | `aeo9_v0.64_w_result` | 400 rows, 480 writes |
| 2026-06-29 fridge Phase 2 | `Refrigeration_` leaf `Efficiency` | `aeo9_v0.64` | 180-row canonical |
| 2026-06-30 FULL AC + fridge | Key drivers + leaf Efficiency + RAS device-stock block | `aeo9_v0.64` | 2 × 1,030 rows, 2,580 writes, 60/60 EXACT |

The 2026-06-30 run is the current gold-standard recipe — see
[../LAST_SUCCESSFUL_INJECT.md](../LAST_SUCCESSFUL_INJECT.md) for the
repeat-on-a-new-area procedure. The canonicals are area-independent;
only the target area (and its structure prerequisites) changes.

**In scope of this guide:** the three authored end uses (Lighting,
Air Conditioning_, Refrigeration_) plus the canon frame for the other
12 projection end uses (not yet authored by us). **Out of scope:**
supply-side data (residential authors nothing under `Resources\`), and
anything in `Transformation\` — **pending Transformation export**: the
Transformation tree is not yet in canon, so the electricity-supply
side of residential demand (and the fuel-pricing wiring behind the
double-count question in §7.6) cannot be verified offline yet.

**Timor Leste (§A.18):** [timor_leste_supplement.csv](timor_leste_supplement.csv)
is a header-only stub — no researched TL rows exist in this domain.
Canon (anatomy §3) shows TL demand-side rows are template-grade
(`ShapeFlat`, no `Timor Leste_Hourly` shape exists). TL is currently
excluded from LEAP calc (operational state 2026-05-18); every inject
run passes `--exclude-timor-leste` until that changes. TL data, when
it arrives, goes in the supplement — never in the main canonical.

---

## 1. Canon LEAP structure (aeo9_v0.67 exports, 2026-07-02)

Source: [LEAP structure/LEAP_STRUCTURE_ANATOMY.md](../../LEAP%20structure/LEAP_STRUCTURE_ANATOMY.md)
§10 (residential), §12 (Key tree), §14 (hygiene ledger); full tree in
`LEAP structure/trees/residential_tree.txt`; domain slices in
[structure_handover_20260703/](structure_handover_20260703/).
Refresh branch targets by grepping these files, not by COM probe.

**The sector in numbers** (anatomy §10): 146,544 export rows across
**530 branches** / 35 variables (1,275 combos) — the most
variable-rich demand sector. Activity driver: households
(`Demand\Residential:Activity Level =
Key\Demographic\Households[Thousand household]`).

**The era split** (anatomy §10.1): level 3 splits into
- **`Historical`** — 169 branches: 14 fuel-accounting branches
  (Bagasse … Wood), each Activity Level + Final Energy Intensity +
  custom `TotalEnergyRes` (CA-only), most with 12–13 pollutant
  children. Switched OFF from 2025 by `Step(2005, 100, 2025, 0)`.
- **`Projections`** — 360 branches, switched ON by the mirror
  `Step(2005, 0, 2025, 100)`. Holds the **15 end uses**: Air
  Conditioning, **Air Conditioning_**, Clothes Dryer, Computer and
  Laptop, Cooking, Fan, Iron, Lighting, Other, Refrigeration,
  **Refrigeration_**, Rice Cooker, TV, Washing Machine, Water Heating.

All projection-side authoring goes under `Projections`; never author
new data into `Historical` branches without an explicit calibration
task.

**The paired device-stock trees** (anatomy §10.5 — the load-bearing
quirk): `Air Conditioning` vs `Air Conditioning_` and `Refrigeration`
vs `Refrigeration_` (trailing underscore) run in **parallel**. The
underscore trees are the 2-layer device-stock rebuilds we author
(§10.1 canon shape, verified against the tree file):

```
Demand\Residential\Projections\<App>_          parent: ownership / units-per-HH
├── Large   → High_eff / Mid_eff / Low_eff     size node: Size_Share + Useful_EI
├── Medium  → High_eff / Mid_eff / Low_eff       + Optimize Devices + Load Shape
└── Small   → High_eff / Mid_eff / Low_eff     tier leaf: device-stock panel
```

The 18 `*_eff` tier leaves carry the full device-stock panel
(canon tree line for `Refrigeration_\Large\High_eff`): Activity
Level, Capital Cost, Demand Cost, Efficiency, Exogenous Devices,
Final Energy Intensity, Fixed OM Cost, Interest Rate, Lifetime,
Maximum Availability, Maximum/Minimum Device Additions,
Maximum/Minimum Devices, Minimum Share, Minimum Utilization, RefHH,
Unit Capacity, Variable OM Cost. `Optimize Devices` sits on the 6
size-class parents (currently split `Yes` 252 / `No` 252 rows).
**The panel is scenario-scoped — see §4 before authoring anything on
these leaves.** The OLD share-based trees are off-limits (§6.3).

**Lighting** (the third authored end use, canon tree lines 348–370):
`Lighting\Electricity\{CFL, Fluorescent, Halogen, Incandescent, LED}`
each carry Activity Level, Bulb Wattage, Demand Cost, Final Energy
Intensity, Load Shape, RefHH; the `Electricity` node carries
`BulbsPerHH` + `LightingHours`; a parallel `Lighting\Other` arm
(Kerosene and Candles + Solar Lighting) exists and is NOT authored by
us (team direction 2026-05-21). Final Energy Intensity on the bulb
leaves is a LEAP-side bottom-up formula (anatomy §10.3:
`BulbsPerHH × Bulb Wattage × LightingHours × 365 ×
Key\Cal\Residential\Electricity[Factor] / 1000`) — never overwrite it.

**Regions** (anatomy §3): 12 slots — 10 ASEAN members + Timor Leste +
`Base Template`. Base Template is a LEAP pseudo-region, never author
to it. **Scenarios**: 11 total, but the current-state review scope is
4 — Current Accounts / Baseline Simulation / AMS Target Scenario /
Regional Aspiration Scenario; the other 7 are copies, derivatives, or
plumbing (§4). In residential, only the RE LTRM triplet is
expression-identical; `Set up`, `LCO backup`, and `RAS test` all
genuinely diverge (anatomy §2) — don't assume the transport-style
six-name bloc here.

---

## 2. Canonical CSV schema

Two canonical shapes are in live use in this domain. Both are
comma-separated, UTF-8, one row per (ams, branch, variable
[, scenario]) with a complete `Interp(...)` trajectory in
`expression`.

### 2.1 Domain-standard schema (lighting; the framework injector)

`canonical_leap_inputs.csv` at the domain root — the standard
`CanonicalInjector` schema shared with bioenergy/fossil/power/transport:

```
ams, branch, variable, expression, unit, fuel, source, note,
src_csv, data_confidence, scenario
```

Produced by [build_canonical.py](build_canonical.py) (lighting only:
`lighting_tech_shares.csv` → Activity Level per scenario,
`lighting_bulb_wattage.csv` → Bulb Wattage untagged). Injected by
[inject_to_leap.py](inject_to_leap.py) (`ResidentialInjector`,
framework subclass — Interp preflight, area/scenario lock,
placeholder gate, §A.18 TL flag all inherited).

### 2.2 Appliance schema (AC + fridge pipelines)

`canonical_{ac,fridge}_full.csv` under [202060630/](202060630/) — the
8-column subset the appliance cycles ship:

```
ams, branch, variable, expression, unit, scenario, source, note
```

Produced by [202060630/build_canonical_full.py](202060630/build_canonical_full.py)
(`--appliance {ac|fridge}`) from the author drop
(`ac_leap_inject.csv` / `fridge_leap_inject.csv`, long format:
`Country, Year, Scenario, Size_group, Efficiency_level, <quantity
columns>`) plus the exogenous-fleet file (`<app>_exo_device.csv`,
`device_thousand` × 1000 → Device). Injected by the self-contained
[20260625/inject_fridge_leap.py](20260625/inject_fridge_leap.py)
(stdlib + pywin32 — shipped to the author team; it does blind
`leap.Branches(FullName)` writes guarded by an up-front FullName
index, sets ActiveRegion per region group, and scenario-filters rows
exactly like the framework).

For new end uses, prefer the §2.1 full schema + a thin
`CanonicalInjector` subclass (CLAUDE.md §5.1); the 8-column form
remains valid for the appliance cycles because their injector already
enforces the same rules.

### 2.3 What lands where (the unified slot map)

| Quantity (author column) | LEAP target | Variable | Scenario handling |
|---|---|---|---|
| `ownership_parent_pct` (fridge) / `units_per_hh_parent` (AC — may exceed 100) | `Key\Residential\<App>\Percent Ownership` | Activity Level | untagged (invariant) |
| `size_share_pct` (Σ=100 across sizes) | `Key\…\Size_Share\<Size>` | Activity Level | auto: per-scenario if trajectories differ |
| `eff_share_pct` (Σ=100 within size — **the lever**) | `Key\…\Efficiency_Share\<Size>_<Eff>` | Activity Level | per-scenario |
| `useful_energy_intensity_toe` | `Key\…\Useful_EI\<Size>` | Activity Level | untagged |
| `efficiency_pct` (High_eff=100) | tier leaf | Efficiency | untagged (all scenarios) |
| `unit_capacity_kw` | tier leaf | Unit Capacity | RAS-only (§4) |
| `price_usd` (FULL capital — LEAP annualizes by Lifetime) | tier leaf | Capital Cost | RAS-only |
| `om_electricity_usd` (⚠ basis — see §3) | tier leaf | Variable OM Cost | RAS-only |
| `0` / `15` (AC) / `12` (fridge) | tier leaf | Fixed OM Cost / Lifetime | RAS-only |
| `<app>_exo_device.csv` × 1000, 2005–2060 | tier leaf | Exogenous Devices | RAS-only |
| `share_percent` (lighting tech mix) | `Lighting\Electricity\<Tech>` | Activity Level | per-scenario |
| `watts` (lighting) | `Lighting\Electricity\<Tech>` | Bulb Wattage | untagged |
| `<Country>_AC_Cooling` load shapes | tier leaf Energy Load Shape | — | **separate LEAP upload, never in the inject** |

### 2.4 Naming maps (source → LEAP)

| | Source CSV | Key tree | Demand tree |
|---|---|---|---|
| Country | `Brunei Darussalam`, `Lao PDR`, `Viet Nam`, … | `Brunei`, `Laos`, `Vietnam`, … | same |
| Scenario | `BAS` / `ATS` / `RAS` | `Baseline Simulation` / `AMS Target Scenario` / `Regional Aspiration Scenario` | same |
| Size | `Small/Medium/Large` | `Size_Share\<Size>` | `…\<Size>` (nested) |
| Efficiency | `High_eff/Mid_eff/Low_eff` | flat `<Size>_<Eff>` with short `High/Mid/Low` | nested `…\<Size>\<Eff_eff>` keeping `_eff` |

### 2.5 Expression + inject rules (non-negotiable)

- **`Interp(year, value, …)` with comma list-separator + period
  decimal only** (§A.15). All adapters call `normalize_interp()`;
  `tests/test_interp_separator.py` scans committed canonicals.
  Confirm LEAP → Settings → Regional decimal = `.` before any push
  (the framework asserts this, exit 11).
- **Blind mode is MANDATORY** (§A.20): every residential target is a
  `Demand\…` or `Key\…` branch — cached `branch.Variable()` writes
  **silently no-op** on both. Blind is default-on in the framework;
  always pair with `--fail-fast` (blind hangs on a missing FullName).
- **Full-trajectory overwrite:** the inject replaces the whole
  expression, so author every year you intend (2014→2060 for
  device-stock work, 2025→2060 for projection-only data). Gaps become
  interpolation artifacts.
- **Shares close at 100.** The adapters do not re-normalise. Canon
  partitions are closed by `Remainder(100)` on the last sibling; if
  you author all siblings explicitly they must sum to 100 every year.
- **Readback target:** `N EXACT, 0 NORMALISED, 0 FAIL` per scenario,
  plus a UI eye-test on one multi-scenario branch.

---

## 3. Unit conventions (canon)

Source: `residential_branch_variables_units.csv` (1,276 rows —
identical copies in [structure_handover_20260703/](structure_handover_20260703/)
and the team-artifacts drop). **Always check the row for the exact
branch you are filling** — residential runs four different intensity
unit systems side by side.

| Variable | Branches | Canon units (units / scale / per) |
|---|---|---|
| Activity Level | 116 | `Household` (Thousand) at the root; `Saturation % of Household` on 34 ownership branches; `Share % of Household` on 81 partition branches |
| Final Energy Intensity | 97 | `Tonnes of Oil Equivalent` (55), `Kilowatt-Hour` (39), `Gigajoule` (1), `Megajoule` (1), `Liter` (1) — all per Household |
| Useful Energy Intensity | 9 | AC_/Refrigeration_ sizes: `Tonnes of Oil Equivalent` per Household (6); old `Air Conditioning`: `Kilowatt-Hour`; `Cooking\Clean`: `Megajoule`; `Cooking\Traditional`: `Gigajoule` |
| Efficiency | 35 | `Efficiency (%)` |
| End Year Penetration | 15 | `%` |
| Capital Cost | 18 tiers | `U.S. Dollar` (per device implied — no `per` column value) |
| Unit Capacity | 18 tiers | `Kilowatt` |
| Exogenous / Maximum Devices | 18 tiers each | `Device` |
| Fixed OM Cost | 18 tiers | `U.S. Dollar` |
| Variable OM Cost | 18 tiers | **`U.S. Dollar per Gigajoule`** on 15 tiers; **`U.S. Dollar per Kilowatt-Hour`** on the 3 `Refrigeration_\Large` tiers — ⚠ see conflict note below |
| Lifetime | 18 tiers | `Years` |
| Demand Cost | 116 | `2020 USD per Household` (114); 1 × plain `U.S. Dollar` (root), 1 × `U.S. Dollar per Household` — vintage drift is in the area itself (ledger #16) |
| Bulb Wattage | 5 lighting techs | `Watts` |
| Load Shape | 36 | `YearlyShape(<Country>_Hourly)`; AC uses three climate-zone shapes |

Key-slice units (`keys_slice_residential_units.csv`, 115 rows):
`Key\Residential` = `%` on 26 branches + `Tonnes of Oil Equivalent`
on the 6 `Useful_EI` leaves; `Key\Cal\Residential` = `Factor`;
`Key\Demographic\Households` = Thousand household, `Household Size` =
people/HH; `Key\Energy Access` + `Key\Net Zero Measures\Residential`
= `%`; `Key\Residential end use data_` = `coeff` (27), `# of units`
(9), `pcnt of HH` (9), `yr` (9); `Key\Macroeconomic\Real GDP Per
Capita` = `2021 USD / person`.

> ⚠ **Canon-vs-authored conflict — Variable OM Cost basis.** The
> per-appliance docs (AC_ANATOMY §4, mapping docs) treat
> `Variable OM Cost` as **USD per unit per year**
> (`om_electricity_usd` = tariff × kWh/unit), and that is what the
> 2026-06-30 inject pushed. Canon says LEAP stores the variable as
> **USD per Gigajoule** (15 tiers) / **USD per Kilowatt-Hour**
> (3 tiers). Canon wins on what the unit IS; whether the authored
> values must be re-based to per-energy is an open review item for
> the next appliance cycle — it interacts with the electricity
> double-count question (§7.6). Do not copy the per-unit basis into
> new authoring without resolving this.

---

## 4. Scenario scoping — the 7-of-11 device-stock panel

The single most important scoping fact in this domain (anatomy §2.1):
residential row counts split three ways by scenario —

| Rows/scenario | Scenarios | What they carry |
|---|---|---|
| 12,168 | Current Accounts | + CA-only calibration (`TotalEnergyRes` etc.) |
| 11,472 | Baseline Simulation, AMS Target Scenario, RAS test | **NO device-stock economics panel** |
| **14,280** | Set up, Carbon Neutrality_ Net Zero, **Regional Aspiration Scenario**, LCO backup, RE LTRM ×3 | + the full 258-combo device-stock panel |

The panel (`Capital Cost`, `Fixed/Variable OM Cost`, `Lifetime`,
`Interest Rate`, `Exogenous/Minimum/Maximum Devices`,
`Maximum/Minimum Device Additions`, `Unit Capacity`, `Minimum Share`,
`Minimum Utilization`, `Maximum Availability`, `Optimize Devices`) on
the `Air Conditioning_` / `Refrigeration_` tiers **exists only in
those 7 scenarios**. In Current Accounts, Baseline Simulation, AMS
Target Scenario, and Regional Aspiration Scenario test the rows
simply don't exist — device-stock data can only land in the 7 hosting
scenarios. Of the 4-scenario current-state scope, **RAS is the only
one that hosts the panel**, which is why the appliance pipelines
force-tag the whole block `Regional Aspiration Scenario`.

Mirror image (anatomy §10.4): 24 `Demand Cost` combos exist **only**
in the 4 scenarios *without* the panel — two disjoint costing systems
for the same appliances. Don't author both for the same scenario.

**Per-row `scenario` column + filter-routing (§A.20)** is how this is
enforced mechanically: the injector loops scenarios in ONE COM session
and pushes each row only into its tagged scenario; **untagged rows
(empty `scenario`) are pushed into every scenario iterated** —
correct for scenario-invariant drivers (ownership, Useful_EI, leaf
Efficiency), wrong for anything panel-scoped. Rules:

1. Device-stock panel rows: always tag with a hosting scenario
   (in practice `Regional Aspiration Scenario`). Never leave untagged
   — an untagged panel row aimed at Baseline/ATS targets variables
   whose rows don't exist there.
2. Per-scenario levers (`eff_share_pct`, lighting tech shares): one
   row per scenario, tagged with the full LEAP scenario name.
3. Scenario-invariant drivers: single untagged row.
4. `build_canonical_full.py` automates 1–3 (auto-detects invariance
   by comparing trajectories across scenarios, force-tags the RAS
   block); don't hand-edit its output tagging.

---

## 5. Key connections (what residential wires into)

Residential is a **two-tree sector**: the Demand tree computes; the
`Key\` tree stores. Both are blind-mandatory inject targets (§A.20).
Canon slice: `keys_slice_residential.txt` +
`keys_slice_residential_units.csv` in
[structure_handover_20260703/](structure_handover_20260703/).

| Key structure (branches) | Role |
|---|---|
| `Key\Residential` (32) | **The AC + Refrigeration driver store** — `Percent Ownership`, `Size_Share\*`, `Efficiency_Share\*` (flat `<Size>_<Eff>`), `Useful_EI\*` per appliance, 16 nodes each. The Demand tiers reference these; our data lives here. Value always on `Activity Level`, as `Interp(...)`. |
| `Key\Residential end use data_` (54) | 9 appliances × {Historical count, a, b, c, number of appliances, year_}. Live expressions cite only `\AC\number of appliances` (120 rows) and `\AC\Historical AC` (12 rows); the a/b/c regression panels — and every non-AC appliance's panel — are cited by **no live expression** (anatomy §12.6) — do not wire new authoring to them without a team decision. |
| `Key\Cal\Residential` (13) | Per-fuel calibration factors multiplied through **5,218 residential intensity rows** (anatomy §10.3). **Never author these** — and know that displayed `Efficiency` on cooking/device tiers silently absorbs them (e.g. `56*Key\Cal\Residential\LPG:Activity Level[Factor]`), so a displayed % is not physical efficiency. |
| `Key\Demographic` (8) | `Households` drives the sector root; `Household Size` feeds cooking useful energy. |
| `Key\Energy Access` (2) | `Clean Cooking Access` drives the Cooking Clean/Traditional split. |
| `Key\Net Zero Measures\Residential` (9) | CNZ-scenario `(1 − saving × share)` multiplier stacks on intensities (Reflective Coatings Cool Roofs, Programmable Thermostats, Gamification, Building Orientation, …). |
| `Key\Macroeconomic` | `Real GDP Per Capita [2021 USD/person]` drives the OLD share-based appliance saturations via `Lookup` curves (old `Air Conditioning`, `Refrigeration`, `Washing Machine`, `Water Heating`, `Computer and Laptop` Activity Levels + AC End Year Penetration). The underscore-tree drivers we author (`Key\Residential\*\Percent Ownership`) carry **no** GDP link — plain `Interp` trajectories (canon Key export: zero Lookup/GDP refs under `Key\Residential\`). |
| `Key\Lighting_data` (2) | Lighting data store (Lamp / hours). |

Demand→Key reference wiring for the device-stock trees (verified,
FRIDGE_ANATOMY §3 / AC_ANATOMY §3): parent Activity Level →
`Percent Ownership`; size Activity Level → `Size_Share\<Size>`; size
Useful Energy Intensity → `Useful_EI\<Size>:Activity Level[TOE]`;
tier Activity Level ← `Efficiency_Share\<Size>_<Eff>` exogenously
(NEMO may optimize it in RAS/CNZ — see §6.1).

**Resources / Transformation:** residential authors nothing
supply-side. Electricity, LPG, kerosene, biomass etc. balance against
supply through Transformation — **pending Transformation export**;
the wiring is not verifiable offline yet.

---

## 6. Off-limits list

6.1 **Solver-writeback rows — the 360 tier Activity Levels tagged
`?Optimized on 07/02/2026 … (NEMO/CPLEX)`** (RAS + CNZ, anatomy §10.3
item 5, ledger #8). These are optimisation *outputs* frozen into the
input slot (`Data(2025, 50.31766, …) ?Optimized …`). Do not treat
them as authored data, do not propagate them into canonicals, and do
not overwrite them casually — a fresh tier-share inject WILL replace
them, which is only correct if the team has confirmed that intent
(canon README §7 item 3 has that confirmation request outstanding).

6.2 **`Unlimited` literals on `Maximum Devices` / `Maximum Device
Additions`** — the literal string sits on all device-stock tier rows
(1,512 rows × 2 variables, ledger #10). **Do not copy the pattern**
into any new authoring: the export layer converts the literal to
1.0e+12 (§A.11 sentinel — here on demand-side device vars rather than
supply bounds, but the same export translation applies). If a cap is
meant to be non-binding, author a generous finite number; never
author `Unlimited` on any lower-bound-flavoured variable (Minimum
Devices/Additions) at all — use 0 or a justified finite floor.

6.3 **The OLD share-based `Air Conditioning` and `Refrigeration`
trees** — off-limits pending the double-count question (§7.6). They
still carry non-zero intensities in every projection scenario while
the underscore trees run in parallel in 7 scenarios. Do not author
into them, and do not zero them out either, until the residential
team answers the canon README §7 item 1 review request.

6.4 **LEAP-side formulas we must not overwrite:** lighting leaf
`Final Energy Intensity` (bottom-up formula, §1); Demand-tier
references into `Key\Residential` (overwrite the Key node, not the
reference); the era-switch `Step()` expressions on
`Historical`/`Projections`.

6.5 **`Key\Cal\Residential\*` calibration factors** (§5) and the
uncited `Key\Residential end use data_` a/b/c panels (§5, §7.1).

6.6 **`Base Template` region** (never author) and **result variables**
(never read `.Expression`/`.DataUnitText` on them — §11.2 modal trap;
the tier leaves carry many: Demand Devices, Investment Costs, Final/
Useful Energy Demand, …).

---

## 7. Known hygiene (in-area defects to keep in view)

From the canon hygiene ledger (anatomy §14) + per-appliance history —
these are *in the area*, not in our pipelines; know them so you don't
"fix" them by accident or trust them as data:

1. **Stale `Key\Residential\AC\{a,b}` comment citations** — 232 rows
   name branches that exist nowhere; all are comment-only (`? …`)
   provenance on the old `Air Conditioning:Activity Level` Lookup
   (anatomy §12.6, ledger #29). Not a dangling live reference; do not
   "repair" by creating the branches. The near-namesake
   `Key\Residential end use data_\AC\{a,b}` panels exist but are
   uncited.
2. **`_x000D_` Excel carriage-return artifacts** — 1,263 residential
   rows carry them inside expressions (ledger #14). Cosmetic in LEAP,
   but they break naive string-equality readbacks; the injectors'
   comparison already normalises.
3. **Placeholder confessions** surviving into substantive scenarios
   (ledger #5): `200 ?ACE Placeholder when no data`,
   `10 ? placeholder 14 IIEC`, `? uncalibrated assumed valuie` [sic].
   These are the highest-value replacement targets when the team
   sends researched data.
4. **AC ownership `×2` multiplier** with a dead alternative equation
   embedded only in the comment (ledger #20) — undocumented doubling
   on the old-tree ownership Lookup; confirmation requested from the
   team (canon README §7 item 5).
5. **Lifetime spread** on the device-stock tiers: 10 years on 960 of
   1,512 rows, 12 on 372 `Refrigeration_` rows, 15 on 180
   `Air Conditioning_` rows — while our authored constants are
   fridge=12 / AC=15 across the board. Reconcile before the next
   panel push (canon README §7 item 6).
6. **Electricity double-count risk (open):** RAS charges appliance
   electricity via `Variable OM Cost` (tariff × kWh) while LEAP may
   also price electricity as a fuel — flagged at the 2026-06-30
   inject (AC_ANATOMY "Still open") and compounded by the §3 unit
   conflict and the parallel old-tree intensities (§6.3). **Pending
   Transformation export** — the fuel-pricing side can't be checked
   offline; resolve before the next cost-layer authoring cycle.
7. **Fridge ownership seam:** the source `ownership_parent_pct` steps
   ~97.6 → 89.0 at 2022→2023 (historical/projection seam,
   FRIDGE_AUTHOR_GUIDELINE data-quality flag). The inject renders it
   faithfully — an authoring-side check, same class as transport's
   CA-2024→2025 continuity rule.
8. **`Demand Cost` boilerplate:** authored everywhere,
   ≈100% zeros (ledger #17), with unit-vintage drift (§3). The 24
   non-panel-scenario Demand Cost combos (§4) are the only live use.
9. **AC `Energy Load Shape` upload still open:** the 10
   `<Country>_AC_Cooling` named shapes are a separate LEAP upload,
   not an inject (AC_ANATOMY §8) — not yet confirmed done on the
   v0.67 line.

---

## 8. Cross-Domain Learnings

- 2026-07-03 — from the LEAP-structure canon
  (`LEAP structure/LEAP_STRUCTURE_ANATOMY.md`, aeo9_v0.67 exports):
  **canon outranks every other document** for branch paths, variables,
  units, and scenario/region rosters — probes and team CSVs are
  fallbacks, not truth. This domain: applied — this guide's §1/§3–§5
  are canon-sourced; the 7-of-11 device-stock scenario scoping
  superseded the v0.64-era "two leaf variants in two areas" model
  (canon-update notes already placed in FRIDGE_ANATOMY §1.3 and
  FRIDGE_AUTHOR_GUIDELINE §2); the Variable OM Cost per-energy unit
  conflict (§3) was surfaced by canon and is flagged, not silently
  "fixed". See the bioenergy + transport guides' 2026-07-03 entries
  for the original.
- 2026-05-19 — from transport: **canonical LEAP branch taxonomy is
  authoritative; filter sector-team combos toward LEAP and log the
  drops.** This domain: applied — the lighting adapter routes only
  the five probed `Lighting\Electricity\<Tech>` leaves and skips the
  `Lighting\Other` arm; the appliance adapters emit only tree-existing
  tiers; refresh availability by grepping
  `LEAP structure/trees/residential_tree.txt`, not by COM probe. See
  `inject/transport/CSV_AUTHORING_GUIDE.md §3`.
- 2026-04-29 — from bioenergy: **a cap/cost (or driver/cost) pair on
  the same branch must share the same physical basis.** This domain:
  **outstanding** — canon stores tier `Variable OM Cost` per-energy
  (USD/GJ, USD/kWh) while the authored values are per-device-year
  (§3); basis must be reconciled next appliance cycle. See
  `inject/bioenergy/CSV_AUTHORING_GUIDE.md`.
- 2026-05-19 — from bioenergy (POME lesson): **every supply cap needs
  a companion cost row, else the LP routes through the unauthored
  cost ≈ 0 path.** This domain: adapted, demand-side analogue — a
  device-stock tier that the RAS optimiser can pick needs its FULL
  economics panel authored together (Capital + Fixed/Variable OM +
  Lifetime + Unit Capacity), which the 2026-06-30 full inject did as
  one block; never author a tier's capacity without its costs. See
  `memory/project_bioenergy_resolved_pome_import_cost.md`.
- 2026-05-17 — from fossil: **§A.15 Interp() comma+period enforced in
  layers.** This domain: applied — `normalize_interp()` in both
  adapters + framework preflight + `tests/test_interp_separator.py`.
- 2026-05-20 — from transport: **cached writes silently no-op on
  `Key\` and `Demand\` branches; blind mode is mandatory; per-row
  scenario filter-routing prevents last-writer-wins corruption
  (§A.20).** This domain: applied and load-bearing — residential is
  the pure KA+Demand sector; both injectors write blind, and the §4
  scenario tagging exists precisely because of the filter-routing
  rule. See `docs/inject_sop.md`.
- 2026-05-20 — from transport (§4c): **era-seam continuity is an
  authoring responsibility; the inject faithfully reproduces
  discontinuities.** This domain: **outstanding** — the fridge
  ownership 2022→2023 step (§7.7) is flagged but unresolved; any new
  end-use trajectory must be checked across its historical/projection
  seam before the push.

---

## 9. Validation checklist (per residential push)

- [ ] Target confirmed with the user: area (`aeo9_v0.67_w_results`
      line), scenario set, `--exclude-timor-leste` (§A.9 / §A.18)
- [ ] Adapter ran clean; row counts per variable/scenario match the
      §2.3 slot map expectations
- [ ] Branch paths grep-confirmed against
      `LEAP structure/trees/residential_tree.txt` (new targets only)
- [ ] No device-stock panel row untagged or tagged to a non-hosting
      scenario (§4)
- [ ] Shares sum to 100 within every partition, every year
- [ ] Era-seam continuity checked on any new trajectory (§8, last item)
- [ ] Units checked against `residential_branch_variables_units.csv`
      for every (branch, variable) being filled (§3)
- [ ] No `Unlimited` literal anywhere in the canonical (§6.2)
- [ ] `python -m pytest tests/test_interp_separator.py
      tests/test_inject_base.py` clean
- [ ] Inject run blind + `--fail-fast`; readback
      `N EXACT, 0 NORMALISED, 0 FAIL` per scenario + UI eye-test
- [ ] [../LAST_SUCCESSFUL_INJECT.md](../LAST_SUCCESSFUL_INJECT.md)
      updated if this run supersedes the 2026-06-30 reference

---

*Unified 2026-07-03 from AC_ANATOMY.md, FRIDGE_ANATOMY.md, the
2026-06-25/29/30 cycle docs, and the `aeo9_v0.67_w_results` canon
exports (`LEAP structure/`, digested in LEAP_STRUCTURE_ANATOMY.md §10,
§12, §14). Canon wins on structure; the anatomy docs stay the
per-appliance deep dives. If you change an adapter, a canonical
schema, or a unit convention, update this guide in the same commit
(CLAUDE.md §6.1).*
