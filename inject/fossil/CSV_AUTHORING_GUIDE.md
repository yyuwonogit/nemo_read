# Fossil CSV — Authoring Guide

This document describes the contract between the nine hand-authored
fossil CSVs in this folder and the
[build_canonical.py](build_canonical.py) adapter that consolidates them
into [canonical_leap_inputs.csv](canonical_leap_inputs.csv) for the
`nemo_read` LEAP-injection pipeline. It is the fossil counterpart of
[inject/bioenergy/CSV_AUTHORING_GUIDE.md](../bioenergy/CSV_AUTHORING_GUIDE.md)
— both domains author into the same flat `Resources\` supply tree and
share the same injector framework, so the two guides deliberately rhyme.

> **TL;DR for fastest hand-off:** keep the per-file column shapes in §2
> exactly; use LEAP short-form region names (Brunei, Laos, Vietnam);
> write every `Interp(...)` — and every `Data(...)` — with **comma
> list-separator + period decimal** (§5); never author the literal word
> `Unlimited`; put Timor Leste rows in
> [timor_leste_supplement.csv](timor_leste_supplement.csv), never in the
> main CSVs (§6).

---

## 0. Status and scope (first edition, 2026-07-03)

The fossil pipeline has been live since the 2026-05 cycles (adapter +
canonical + `CanonicalInjector` subclass + unit audit + Timor Leste
supplement) but shipped **without an authoring guide** — a §6.1 debt
this document closes. It is written against:

- the adapter as of this commit ([build_canonical.py](build_canonical.py)),
- the committed canonical (**229 rows**: Import Cost 90, Maximum
  Production 60, Production Cost 50, Additions to Reserves 10,
  Exogenous Capacity 10, Export Benefit 9 — across 10 `Resources\`
  branches + 1 `Transformation\` branch),
- the **canon** LEAP structure exports of `aeo9_v0.67_w_results` (§1).

**What this domain authors today:**

| Layer | Branches | Variables |
|---|---|---|
| Coal supply costs | `Resources\Primary\Coal Bituminous`, `Coal Sub bituminous`, `Coal Lignite` | Import Cost, Production Cost |
| Gas supply costs | `Resources\Primary\Natural Gas` | Import Cost, Production Cost |
| Crude supply | `Resources\Primary\Crude Oil` | Maximum Production, Production Cost, Import Cost, Additions to Reserves, Export Benefit |
| Petroleum products | `Resources\Secondary\Gasoline`, `Diesel`, `Kerosene`, `Residual Fuel Oil` | Import Cost, Maximum Production (=0), Export Benefit |
| LPG | `Resources\Secondary\LPG` | Maximum Production (=0) only |
| Refining | `Transformation\Oil Refining\Processes\All Refineries` | Exogenous Capacity (§8 — Transformation now canon §14; id 2544 confirmed) |

**Where it lands:** the inject payload lives in **Regional Aspiration
Scenario (RAS)** and Carbon Neutrality_ Net Zero Scenario (CNZ) — canon
anatomy §13.5 measures RAS/CNZ vs the untouched Set-up bloc at exactly
553 differing cells (Import Cost 193, Production Cost 136, Maximum
Production 105 across the crop + fossil branches).

**Known NOT-authored (deliberate or gap — see §3):**
- `Maximum Production` for Natural Gas and **all five coals** — still
  `Unlimited` in every scenario, all 12 regions (the §3 headline gap).
- Any cost rows for `Coal Anthracite` and `Coal Unspecified` —
  [coal_supply_costs.csv](coal_supply_costs.csv) covers only the three
  traded/mined grades above.
- Everything under `Transformation\` except the single refinery
  Exogenous Capacity trajectory (§8).

---

## 1. Canon LEAP structure (aeo9_v0.67 exports, 2026-07-02)

The user-declared **canon** for LEAP structure is
[LEAP structure/LEAP_STRUCTURE_ANATOMY.md](../../LEAP%20structure/LEAP_STRUCTURE_ANATOMY.md)
(this domain: chapter §13, the `Resources\` supply tree) plus the branch
trees under `LEAP structure/trees/`, digested from the six "Export
Expressions" workbooks of the operating area `aeo9_v0.67_w_results`.
Per CLAUDE.md §2.6, **branch paths, variable names, units, and
scenario/region rosters come from canon — do not re-derive them by
probing or by convention.** Expression *values* are not canon; author
those per this guide. All facts below were re-verified 2026-07-03
against the fossil slice digest — both files ship in this folder under
[structure_handover_20260703/](structure_handover_20260703/):
[resources_slice_fossil_units.csv](structure_handover_20260703/resources_slice_fossil_units.csv)
(per-(fuel, variable) units/scale/per) and
[current_expressions_resources_4scenarios.csv](structure_handover_20260703/current_expressions_resources_4scenarios.csv)
(the 4-scenario expressions export), both derived from
`LEAP structure/LEAP Input Resources.xlsx`. That folder is also the
team-facing handover package
([README_FOSSIL_CANON_STRUCTURE.md](structure_handover_20260703/README_FOSSIL_CANON_STRUCTURE.md))
— its §7 known-issues list is the external-team mirror of §3/§7 here;
keep the two in sync when either side closes an item.

### 1.1 Tree shape (anatomy §13.1)

All 62 `Resources\` branches are **flat depth-3 leaves** (29
`Resources\Primary\<Fuel>`, 33 `Resources\Secondary\<Fuel>`); no branch
has children. Every fuel carries a base 15-variable panel for all 12
region slots. The fossil panel variants:

| Panel | Fuels |
|---|---|
| **18 vars** — base 15 + `Base Year Reserves` + `Additions to Reserves` + `Export Load Shape` | the 8 hydrocarbon primaries: Coal Anthracite, Coal Bituminous, Coal Lignite, Coal Sub bituminous, Coal Unspecified, Crude Oil, Natural Gas, Natural Gas Liquids |
| **17 vars** — base 15 + reserves pair, **no** Export Load Shape | Nuclear |
| **16 vars** — base 15 + `Export Load Shape` | 28 of 33 Secondary fuels, incl. this domain's Gasoline, Diesel, Kerosene, LPG, Residual Fuel Oil |

There are **no** `<Fuel> Imports` sub-branches anywhere in
`Resources\Secondary` — imports are the `Maximum Imports` / `Minimum
Imports` / `Import Cost` variables on the flat leaf itself. (This is
the canon correction of the 2026-05-13 §A.14(i) wrong-claim.)

### 1.2 Units on this domain's branches — verified per fuel

From `resources_slice_fossil_units.csv` (LEAP's `units` / `scale` /
`per` verbatim), 2026-07-03:

**`Maximum Production`** — energy units throughout; **Metric Tonne on
none of the fossil fuels** (the tonne-cap convention is bioenergy-only):

| Branch | LEAP unit |
|---|---|
| `Resources\Primary\Crude Oil` | **Petajoule** (the only PJ cap in the tree) |
| All 5 coals, Natural Gas, Natural Gas Liquids, Nuclear | Gigajoule |
| Secondary Gasoline, Diesel, Kerosene, LPG, Residual Fuel Oil | Gigajoule |

**Costs** (per-unit denominators differ per fuel — this drives every
conversion in §2.4):

| Branch | Import Cost | Production Cost |
|---|---|---|
| Coal Anthracite / Bituminous / Lignite / Unspecified | 2020 USD / Metric Tonne | U.S. Dollar / Metric Tonne |
| Coal Sub bituminous | 2020 USD / Metric Tonne | 2020 USD / Metric Tonne |
| Crude Oil | 2020 USD / **Barrel** | 2020 USD / Barrel |
| Natural Gas | 2020 USD / **Million BTU** | U.S. Dollar / Million BTU |
| Natural Gas Liquids | 2020 USD / Million BTU | 2020 USD / Million BTU |
| Gasoline / Diesel / Kerosene / Residual Fuel Oil (Secondary) | 2020 USD / **Barrel** | 2020 USD / Barrel |
| LPG (Secondary) | 2020 USD / Million BTU | U.S. Dollar / Million BTU |
| Nuclear | 2020 USD / Megawatt-Hour | 2020 USD / Gigajoule |

Note the `U.S. Dollar` vs `2020 USD` tag drift on several Production
Cost slots — canon anatomy §13.4 flags 1,320 such untagged rows as
unit-hygiene drift. Keep authoring in **real 2020 USD** and record the
basis in your `basis`/`source` columns; the tag drift is LEAP-side.

**Reserves pair** (the 18/17-var panels only): `Base Year Reserves` and
`Additions to Reserves` share a unit per fuel — coals **Thousand Metric
Tonne**, Crude Oil **Billion Barrel of Oil Equivalent** (repo authors
"Gbbl" — audit status `match`), Natural Gas **Trillion Cubic Meter**,
NGL Metric Tonne, Nuclear Gigajoule.

**Export Benefit**: U.S. Dollar or 2020 USD per Metric Tonne on most
fuels (Natural Gas: per Cubic Meter). The repo authors Export Benefit
as a formula referencing `Import Cost` (§2.3), so the unit is inherited
— audit status `formula_reference`.

### 1.3 Scenario split and region roster (anatomy §13.5, §3)

The Resources variable set **splits by scenario bloc**: the 4
accounting scenarios (Current Accounts, Baseline Simulation, AMS Target
Scenario, Regional Aspiration Scenario test) carry `Imports` + `Cost of
Unmet Requirements`; the 7 optimization scenarios (Set up, CNZ, LCO
backup, RAS, RE LTRM ×3) instead carry `Minimum Imports` + `Maximum
Imports`. Don't author an import-cap row into an accounting scenario or
vice versa. The 4-scenario review scope for current-state files is
Current Accounts / Baseline Simulation / AMS Target Scenario / RAS —
the other 7 are copies/derivatives/plumbing (anatomy §13.5: on
Resources cells `CNZ = RAS`, `Baseline = RAS test`, `Set up = LCO
backup = RE LTRM Policy Aligned`; corrections to the 4 propagate).

Reading the expressions export: region-uniform expressions are deduped
into a single **`ALL (12 regions)`** row (one template value filling
every region slot); a named region means that row is region-specific.
The §3 fossil `Unlimited` caps are `ALL (12 regions)` template rows —
one export row, 12 region slots in LEAP.

One optimization-bloc landmine the repo does *not* author but the §3
caps work must review: canon flags **665 `Minimum Imports` rows (95
fuel×region pairs × 7 optimization scenarios) ending `…, 2022, V` with
V>0** — Interp hold-last-value extends these as forced import floors
into every projection year (largest: Singapore Residual Fuel Oil
53,538 kTOE, Singapore Crude Oil 50,160, Thailand Crude Oil 47,230 —
anatomy §13.6.2; plausibly intentional refinery-hub feed, unreviewed).
Authoring a `Maximum Production` cap on a fuel that also carries a
forced import floor changes what the LP can reach — check the floor
list for your fuel before capping.

Regions: 12 slots — 10 AMS + **Timor Leste** (separate supplement, §6)
+ **Base Template** (LEAP's internal template; never author data for
it, never include it in `--regions` lists).

### 1.4 Key-tree connections — none for fossil fuels

`Key\Optimized Trade` covers exactly 9 feedstock fuels (Ethanol,
Biodiesel, Coconut Oil, Palm Oil, Palm Oil Mill Effluent, Cassava,
Molasses, Sugarcane, Corn — canon anatomy §12.1). **No fossil fuel has
an optimized trade route.** Inference (not canon-verified beyond the
route roster): inter-region fossil supply is expected to flow through
the `Import Cost` / `Maximum Imports` variables rather than pairwise
trade routes — if a future cycle caps fossil `Maximum Production`
(§3), verify import routes remain open enough to absorb the shift
before recalculating.

---

## 2. Input CSV shapes and how the adapter transforms them

### 2.1 Canonical schema (adapter output)

One row = one (region, branch, variable) assignment. 9 columns, fixed
order:

```
ams, branch, variable, expression, unit, fuel, source, note, src_csv
```

`unit` is the **author-side** unit (from each CSV's `basis` column or
hardcoded per transformer); conversion to LEAP-native happens later
(§2.4). `src_csv` records provenance (which of the 9 files the row came
from). Unlike bioenergy there are no `domain` / `data_confidence`
columns — confidence lives inside per-file columns
([crude_production_cost.csv](crude_production_cost.csv) has
`confidence`, `range_low`, `range_high`).

### 2.2 Region scoping — the `scope` keyword system

Fossil does not use bioenergy's `All 10 AMS` literal. Instead the
scope-keyed CSVs accept, in their `scope` / `ams` column:

| Keyword | Expands to |
|---|---|
| `all_10_AMS` (or `all`) | the 10 AMS in fixed order: Brunei, Cambodia, Indonesia, Laos, Malaysia, Myanmar, Philippines, Singapore, Thailand, Vietnam |
| `producing_AMS` | the per-fuel producing cohort (below) |
| `non_producing_AMS` | the 10-AMS complement of the producing cohort |
| a single AMS name (one of the 10 above) | that region only — any other LEAP region name (incl. `Timor Leste`, `Base Template`) raises `ValueError` |

Producing cohorts (hardcoded `PRODUCING_AMS` in
[build_canonical.py](build_canonical.py) — update there AND here if the
cohort changes):

| Fuel | Producing AMS |
|---|---|
| Coal Bituminous | Indonesia, Vietnam |
| Coal Sub bituminous | Indonesia, Vietnam |
| Coal Lignite | Indonesia, Thailand, Vietnam |
| Natural Gas | Brunei, Indonesia, Malaysia, Myanmar, Thailand, Vietnam |

Anything else in the scope column raises `ValueError` at build time —
misspellings fail loudly, not silently. Note Timor Leste is **not** in
any cohort; its rows travel only in the supplement (§6).

The established pattern for costs: `Import Cost` on `all_10_AMS`;
`Production Cost` split into a real trajectory for `producing_AMS` and
an explicit `Interp(2024, 0, 2060, 0)` for `non_producing_AMS` — closed
routes are zeroed *explicitly*, never left to LEAP defaults.

### 2.3 The 9 raw CSVs and their transformers

| CSV | Rows | Shape | Transformer behaviour |
|---|---|---|---|
| [coal_supply_costs.csv](coal_supply_costs.csv) | 9 | `fuel, branch, variable, scope, leap_expression, basis, source, note` | scope fan-out; expression verbatim; unit ← `basis`; note gets `[scope=…]` prefix. 3 coals × (Import all-10 + Production producing + Production non-producing) → 60 canonical rows |
| [gas_supply_costs.csv](gas_supply_costs.csv) | 3 | same | same; → 20 rows (Import ×10, Production ×6 producing + ×4 zeroed non-producing) |
| [import_cost_trajectory.csv](import_cost_trajectory.csv) | 5 | `ams, fuel, branch, variable, leap_expression, basis, source, note` | scope fan-out on `ams`; → 50 rows. Crude Oil in USD/bbl; Gasoline/Diesel/Kerosene/RFO in **USD/100L** (converted ×1.5899 at audit time, §4) |
| [export_benefit.csv](export_benefit.csv) | 9 | `ams, branch, variable, expression, basis, source, note` | per-named-AMS, verbatim; fuel inferred from branch leaf; unit = "(formula refers to Import Cost; unit inherited)". Expressions are cross-variable formulas, e.g. `Import Cost[2020 USD/bbl] * 0.97` |
| [secondary_max_production.csv](secondary_max_production.csv) | 5 | `ams, branch, variable, expression, rationale, note` | fan-out; unit hardcoded `PJ/year`; → 50 rows of `Maximum Production = 0` on Gasoline/Diesel/Kerosene/LPG/RFO — refinery is the sole producer, Secondary caps must be 0 so LEAP can't conjure product from nowhere |
| [crude_oil_max_production.csv](crude_oil_max_production.csv) | 80 | per-(ams, year) long format: `ams, year, production_kbpd, production_pj_per_yr, decline_pct_per_yr, …, source_basis, note` | **grouped per AMS** into one `Interp(year, value, …)` from the `production_pj_per_yr` column (pairs sorted by year); unit `PJ/year`; → 10 rows. First non-empty note/source per AMS wins |
| [crude_production_cost.csv](crude_production_cost.csv) | 50 | per-(ams, year): `ams, year, usd_per_bbl, basis, range_low, range_high, confidence, primary_source, note` | grouped per AMS into Interp from `usd_per_bbl`; unit `USD/bbl real 2020 USD`; → 10 rows |
| [additions_to_reserves.csv](additions_to_reserves.csv) | 10 | `ams, branch, variable, year_anchor, expression, source, note` | verbatim per AMS; unit hardcoded `Gbbl`, fuel `Crude Oil`; → 10 rows. **Currently authored `Data(2024; 1.1)` with semicolons — see §5 and §7** |
| [refinery_exogenous_capacity.csv](refinery_exogenous_capacity.csv) | 63 | per-(ams, year): `ams, year, capacity_kbpd, capacity_pj_per_yr, step_change_note, source` | grouped per AMS into Interp from `capacity_pj_per_yr`; branch hardcoded `Transformation\Oil Refining\Processes\All Refineries`; → 10 rows (§8) |

Every expression is passed through
`nemo_read._leap_com.normalize_interp` as it is written to the
canonical (§A.15 Layer 1) — but note that helper normalises **only
`Interp(...)` substrings** (§5).

What the adapter does **not** do (same philosophy as bioenergy §8): no
unit conversion (that's the workflow's audit step), no branch/variable
existence validation (the injector's tree lookup catches those), no
de-duplication, no sorting beyond the per-AMS Interp grouping.

### 2.4 The fixed workflow and the unit audit

```
python inject/fossil/run_workflow.py
```

1. `build_canonical` → [canonical_leap_inputs.csv](canonical_leap_inputs.csv)
2. probe LEAP units (skippable with `--skip-probe` when the cached
   units file exists — and for `Resources\` branches the canon §1.2
   table is now authoritative anyway; the probe remains necessary for
   the `Transformation\` refinery branch, §8)
3. `audit_canonical_units` → [unit_audit.csv](unit_audit.csv)
4. `apply_audit_conversions` → [canonical_leap_native.csv](canonical_leap_native.csv)

The audit currently resolves every pair. The conversion table
(from [unit_audit.csv](unit_audit.csv), factors applied at step 4):

| Author unit | LEAP unit | Factor | ★ | Basis |
|---|---|---|---|---|
| USD/GJ (Coal Bituminous costs) | 2020 USD/Metric Tonne | 25.8 | 3 | IPCC 2019 NCV 25.8 GJ/t; ±10% regional |
| USD/GJ (Coal Sub bituminous) | 2020 USD/Metric Tonne | 18.9 | 3 | IPCC NCV 18.9 GJ/t (HBA-typical) |
| USD/GJ (Coal Lignite) | 2020 USD/Metric Tonne | 11.9 | 2 | IPCC NCV 11.9 GJ/t; **high variance 7–15** — per-AMS override recommended (Mae Moh ≈ 9.7, Sumatran ≈ 11.5) |
| USD/GJ (Natural Gas costs) | 2020 USD/Million BTU | 1.05506 | 5 | ISO: 1 GJ = 0.94782 MMBtu |
| USD/100L (product Import Cost) | 2020 USD/Barrel | 1.5899 | 5 | NIST: 1 US bbl = 158.987 L (§4) |
| PJ/year (Secondary Maximum Production) | Gigajoule | 1,000,000 | 5 | SI (rows are 0, factor moot but kept) |
| PJ/year (Crude Oil Maximum Production) | Petajoule | — | | `match`, no conversion |
| USD/bbl (Crude costs) | 2020 USD/Barrel | — | | `match` |
| Gbbl (Additions to Reserves) | Billion Barrel of Oil Equivalent | — | | `match` |
| PJ/year (Refinery Exogenous Capacity) | Thousand Gigajoules/Year | 1,000 | 5 | LEAP UI displays TJ/year (§8) |

Per-row overrides (e.g. pinning Sumatran lignite LHV for Indonesia
only) go in the `OVERRIDES` dict at the top of
[run_workflow.py](run_workflow.py), keyed `(branch, variable[, ams])`.

### 2.5 Injection

[inject_to_leap.py](inject_to_leap.py) is a thin
`CanonicalInjector` subclass (§5.1 framework — sealed
`_set_expression`, area/scenario lock, §A.15 pre-flight, blind mode
default-ON per §A.20, heartbeat per §A.16). Fossil-specific behaviour:

- **LEAP-native gate**: it *refuses* to push
  `canonical_leap_inputs.csv` (source units) when
  `canonical_leap_native.csv` exists — push the native CSV, or pass
  `--ignore-units` / `--already-converted` deliberately.
- `--filter-fuel <name>` — scope a push to one fuel.
- `--skip-tbd` (default ON) — drops rows whose branch starts `TBD\`.
- **`--include-timor-leste` or `--exclude-timor-leste` is REQUIRED**
  (§A.18; exit 8 without one) — see §6.
- §A.9 still applies: confirm area + scenario with the user before any
  run, including `--dry-run`.

Resource branches are known to write correctly both cached and blind
(§A.20 — the silent no-op class hit KA/Demand branches, not
`Resources\`); keep the blind default and always pair with
`--fail-fast`.

---

## 3. THE GAP — fossil authors costs but no caps (§A.11 exposure)

The canon audit (anatomy §13.3) exposed the domain's headline hole:

> **The fossil canonical authors coal/NG costs but no `Maximum
> Production`** — which is why Natural Gas and the coals are still
> Unlimited 12/12 in every scenario.

Verified 2026-07-03 in the 4-scenario expressions export: `Maximum
Production` on `Resources\Primary\Natural Gas` and all five
`Resources\Primary\Coal *` branches is the literal `Unlimited` in
Current Accounts, Baseline Simulation, AMS Target Scenario AND RAS, as
a single `ALL (12 regions)` template row each. Area-wide, RAS retains
**505** Unlimited `Maximum Production` rows; the fossil primaries are
the largest single block a domain team could close.

Why it matters (§A.11, upper-bound flavour): `Unlimited` exports to
NEMO as the `1.0e+12` sentinel — or, for some AMS, silently parses to
missing/zero. Even when it "works", a 10¹² coefficient next to
normal-scale rows breaches CPLEX's ~10⁹ conditioning tolerance and
pollutes the LP basis. And an uncapped zero-or-cheap supply route is
exactly the shape that once routed all biodiesel production to Timor
Leste (§A.18 burn record).

This is the **inverse of the POME lesson**: bioenergy had caps missing
their companion costs; fossil has costs missing their caps. The cost
layer already exists ([coal_supply_costs.csv](coal_supply_costs.csv),
[gas_supply_costs.csv](gas_supply_costs.csv)), so closing the gap is a
caps-only authoring exercise.

**Recommended next-cycle work (in priority order):**

1. Author `Maximum Production` for Natural Gas and the five coals —
   per-AMS trajectories for the producing cohorts (from national
   production statistics / reserves, same sourcing style as
   [crude_oil_max_production.csv](crude_oil_max_production.csv)),
   explicit `0` for non-producers. Follow the crude template: a
   long-format per-(ams, year) CSV that the adapter groups into
   Interp. Units: **Gigajoule** on all six branches (§1.2) — author in
   PJ/year and let the audit convert, mirroring the Secondary rows.
2. Where a cap is genuinely not meant to bind, use a **generous
   numeric** (e.g. 10–100× the largest plausible annual production, in
   the cap's unit) — never leave/write the literal `Unlimited`.
3. `Coal Anthracite` and `Coal Unspecified` currently have **neither
   costs nor caps** from this domain. Decide: either author both
   layers, or confirm the fuels are inert in the calc and record that
   decision here.
4. Keep the cost↔cap pairing rule: any branch that gets a non-zero cap
   must already have (or receive) its `Production Cost` /
   `Import Cost` rows in the same canonical — companion-cost rule,
   §9.

Reference model: `Resources\Primary\Crude Oil` is already done right —
10 per-AMS declining trajectories in RAS (and the Data() twins in the
accounting scenarios), with only `Base Template` + `Timor Leste`
remaining Unlimited (a §6 watch-item, moot while TL is disabled).

---

## 4. Resolved: the Singapore Gasoline ×1.5899 "mystery" (§A.14 iii)

Closed by canon. The 2026-05-13 investigation left an unverified
hypothesis that the 1.5899× factor between the LEAP-displayed Gasoline
Import Cost and our canonical was "the same trajectory in different
units". The canon export settles it (anatomy §13.4):

> fossil canonical Singapore Gasoline Import Cost `Interp(2024, 46.5,
> …)` in USD/100L displays as `Interp(2024, 73.9304, …)` with
> `per=Barrel` — exactly ×1.5899 (158.99 L/bbl). Same trajectory,
> unit-converted on export; **the inject landed correctly.**

The factor is the [unit_audit.csv](unit_audit.csv) row
`USD/100L real 2020 USD → 2020 USD/Barrel, 1.5899, ★5 (NIST Handbook
44: 1 US bbl = 158.987 L)`, applied by workflow step 4 to the four
product Import Cost trajectories. Nothing to fix; recorded here so no
future session re-opens the "inject silently failed" theory.

---

## 5. Interp separator — fossil was THE §A.15 incident domain

**Read this before touching any expression column.**

On 2026-05-17 this domain shipped ~300 canonical rows in the forbidden
`Interp(...; ...; ...)` semicolon form. The wrong form leaked in twice
over: raw input CSVs authored with semicolons, AND a hardcoded
`"; ".join(...)` in this folder's `build_canonical.py` (then at line
74). The user caught it at inject time; the incident created the
three-layer enforcement stack that now guards **every** domain:

1. **Layer 1 — write-time normalisation**: `build()` passes every
   expression through `nemo_read._leap_com.normalize_interp` before
   writing the canonical; `build_interp()` emits comma+period natively.
2. **Layer 2 — framework chokepoint**: the sealed `_set_expression` in
   `CanonicalInjector` routes through `safe_set_expression`;
   `assert_interp_canonical` raises on any semicolon Interp reaching
   the COM layer.
3. **Layer 3 — pre-flight + CI**: `validate_canonical_csv_expressions`
   refuses to start on a bad CSV, and
   [tests/test_interp_separator.py](../../tests/test_interp_separator.py)
   scans every committed canonical.

The only accepted form, everywhere, always:

```
Interp(2025, 3.2422, 2030, 3.0833, ...)
```

comma between arguments, period for decimals. LEAP's own regional
decimal must be `.` (§A.20 — the dispatch guard exits 11 on comma).

**Known residual gap — `Data(...)` is NOT normalised.**
`normalize_interp` rewrites only `Interp(` substrings
([_leap_com.py:204-218](../../nemo_read/_leap_com.py#L204));
[additions_to_reserves.csv](additions_to_reserves.csv) authors
`Data(2024; 1.1)` and those semicolons flow verbatim into the committed
canonical. The RAS layer in the canon export reads back as
`Data(2024, 1.1)` (comma), so the current values landed — but the
stale accounting-scenario layers still show semicolon forms (§7.3), and
the enforcement stack would not catch a future bad Data() row.
**Author rule: use comma+period inside `Data(...)` too.** Open item for
the framework: extend `normalize_interp`/`assert_interp_canonical` to
`Data(` (with its §A.17 tripwire) — until then this prose rule is the
only guard, so treat it as load-bearing.

Also inherited from bioenergy §13.1 (same risk shape here): **never
re-save these CSVs from Excel under a comma-decimal locale** — it
silently corrupts expression separators. Edit in a text editor.

---

## 6. Timor Leste supplement (§A.18)

[timor_leste_supplement.csv](timor_leste_supplement.csv) exists (27
rows, canonical 9-column schema, seeded 2026-05-18) and carries **only**
`ams='Timor Leste'` rows — zero-supply / zero-cost defaults for every
fossil variable the main canonical authors, each tagged
`[Timor Leste supplement seed] zero-supply default; edit if TL actually
produces this.`

Rules (framework-enforced, CI tripwires in
[tests/test_inject_base.py](../../tests/test_inject_base.py)):

- The main canonical must contain **no** Timor Leste rows; the
  supplement must contain **only** Timor Leste rows.
- Every inject run must pass `--include-timor-leste` or
  `--exclude-timor-leste` — the injector refuses to start otherwise
  (exit 8). No default, ever.
- Operational state: TL is currently **disabled in the LEAP calc**
  (user, 2026-05-18) — runs use `--exclude-timor-leste` until further
  notice.
- **Live §A.18 watch-item from canon** (anatomy §13.3): `Crude Oil`
  (and Natural Gas, and Corn) remain `Unlimited` for Timor Leste in
  RAS. If TL is ever re-enabled, push the supplement (and extend it
  with the §3 caps) in the same cycle, or TL becomes the free-supply
  region again — that is exactly how the §A.18 rule was born
  (biodiesel routing to TL, 2026-05-18). TL has real offshore
  hydrocarbons (Bayu-Undan legacy, Greater Sunrise): if a research
  cycle models them, replace the zero seeds with real trajectories
  rather than deleting rows.

---

## 7. The reserves layer

### 7.1 Base Year Reserves — all zero, Current Accounts only

Canon (anatomy §13.2, verified in the 4-scenario export): `Base Year
Reserves` exists on the 9 reserve-bearing branches (8 hydrocarbon
primaries + Nuclear), appears **only in Current Accounts**, and is `0`
on every one. The repo does not author it. If a future cycle wants
LEAP-side reserve depletion accounting, this plus §7.2 is the pair to
fill — coordinate first; it is not needed for the NEMO optimization.

### 7.2 Additions to Reserves — the 293-row EIA layer vs the repo's 10 rows

Area-wide, canon counts **293 non-zero `Data()` rows** on `Additions to
Reserves`, sourced from EIA / national statistics (coal rows like
Vietnam Coal Anthracite `Data(2021, 3359996.97)` in Thousand Metric
Tonne, with `_x000D_` note artifacts — anatomy §13.6.6). That bulk is
**legacy in-LEAP authoring, not repo-authored** — treat it as canon
state and do not overwrite it blindly.

The repo authors only the **Crude Oil** slice:
[additions_to_reserves.csv](additions_to_reserves.csv), 10 per-AMS
`Data(2024, <Gbbl>)` anchors (Brunei 1.1, Cambodia 0, Indonesia 2.25,
Laos 0, Malaysia 2.7, Myanmar 0.07, Philippines 0.1, Singapore 0,
Thailand 0.3, Vietnam 4.4 — EI Statistical Review 2024 + national
sources; the Vietnam 4.4 is flagged in its own note as possibly
overstated, expert review pending).

### 7.3 Discovered 2026-07-03: a stale, region-scrambled layer in Baseline + ATS

Comparing the authored CSV against the 4-scenario export for
`Resources\Primary\Crude Oil:Additions to Reserves`:

- **RAS matches the authored CSV exactly, per region, in comma form**
  (`Data(2024, 1.1)` Brunei, …, `Data(2024, 4.4)` Vietnam) — the
  current inject layer, correct.
- **Current Accounts holds the pre-inject historical layer**
  (`Data(2019,4.17)` Indonesia, `Data(2022, 1) ? temp` Brunei/Myanmar)
  — expected; CA was never a fossil inject target.
- **Baseline Simulation and AMS Target Scenario hold a stale
  semicolon-form layer whose (value, source-comment) pairs sit in the
  WRONG region slots.** Examples (export, verbatim): Indonesia holds
  `Data(2024; 0) ? No commercial production` (the authored *Cambodia*
  row) while its authored value is 2.25; Laos holds `Data(2024; 0.3)
  ? … DMF Thailand` (the authored *Thailand* row); Singapore holds
  `Data(2024; 4.4) ? … OPEC ASB` (the authored *Vietnam* row);
  Malaysia holds the authored Indonesia row; Philippines the authored
  Malaysia row. Every one of the 10 authored rows is present, but only
  Brunei sits in its own slot.

The permutation-across-regions signature matches the §A.19
ActiveRegion-drift class (writes landing under whatever region was
active, not the row's `ams`) — **hypothesis, not proven**: it is
consistent with an early fossil push (pre-§A.19 framework fix,
semicolon era — the fossil inject log for that cycle is missing) into
Baseline/ATS. What is *fact* from the export: Baseline/ATS disagree
per-region with the authored CSV; RAS agrees.

**Action for the next fossil cycle:** decide whether Baseline / AMS
Target should carry this variable at all; if yes, re-inject the
corrected layer into those scenarios (one CanonicalInjector run with
`--scenarios`, §A.10); if no, clear the stale rows in LEAP. Either
way, verify with a per-scenario readback. Until then, do not trust
Baseline/ATS `Additions to Reserves` values for Crude Oil.

---

## 8. Refinery / extraction processes — **Transformation now CANON (§14)**

The `Transformation\` tree was exported and digested 2026-07-04 — it is
now the seventh canon export (anatomy §14, tree
[LEAP structure/trees/transformation_tree.txt]). The fossil-owned slice
(Oil Refining + the 5 coal-production groups + Crude Oil / Natural Gas
Production + Gas Processing + LNG Regasification + NG T&D + Diesel/
Gasoline Blending + Gasoline Distribution + Energy Sector Own Use — 168
branches) ships in this domain's handover package as
`transformation_slice_tree.txt` +
`transformation_slice_branch_variables_units.csv` +
`current_expressions_transformation_slice_4scenarios.csv`.

**`All Refineries` CONFIRMED against canon:** id 2544 resolves exactly
to `Transformation\Oil Refining\Processes\All Refineries` (the blind
authoring was correct), with `Output Fuels\{Avgas, Bitumen, Diesel,
Gasoline, Jet Kerosene, Kerosene, LPG, …}` present. The
`Exogenous Capacity` unit displaying as `Thousand Gigajoules/Year` and
the ×1000 PJ/year factor ([unit_audit.csv](unit_audit.csv)) stand.

**The freeze is lifted** — process-side fossil authoring may now extend
against the canon slice: refinery `Process Efficiency` / output shares /
OM costs / `Maximum Availability`, the coal/crude/gas production
processes, LNG regas, gas processing, and the blending pseudo-techs.
Author branch paths / variable names / units from the Transformation
slice, not from convention (§A.1). Watch-items from the anomaly audit
(see this package's audit slice): the blending pseudo-techs carry
`Exogenous Capacity = Unlimited` (§A.11 1e12 forced-floor risk) and many
Transformation processes carry all-`Unlimited` `Maximum Production`.

---

## 9. Cross-Domain Learnings

Per CLAUDE.md §6.3 — one bullet per imported/exported lesson; audit by
grepping the date across the other guides.

- 2026-07-03 — from the LEAP-structure canon (`LEAP structure/
  LEAP_STRUCTURE_ANATOMY.md`, aeo9_v0.67 exports): canon outranks every
  other source for branch paths, variables, units, scenario/region
  rosters (CLAUDE.md §2.6). This domain: applied — §1 unit table
  settled per fuel (Crude Oil cap is PJ; coals/NG caps are GJ; no
  fossil tonne-caps), §3 costs-without-caps gap exposed and scheduled,
  §4 ×1.5899 §A.14(iii) claim closed, §7.3 stale Baseline/ATS reserves
  layer discovered. See the bioenergy guide's canon section for the
  sibling treatment.
- 2026-05-05 — from bioenergy (§12.5 supply-basis burn): a supply cap
  and its companion cost rows on the same branch must share the same
  physical basis. This domain: **confirmed aligned** — crude cap
  (PJ/year → Petajoule) vs crude costs (USD/bbl → per Barrel) are
  different but unambiguous dimensions with `match` audit status; the
  coal USD/GJ→USD/tonne conversions pin the basis per IPCC NCV with the
  lignite factor flagged ★2 for per-AMS override. No raw-vs-extracted
  ambiguity exists for fossil commodities.
- 2026-05-17 — from **this domain** (the §A.15 origin incident):
  Interp() separator is comma+period only, enforced by the three-layer
  stack. Exported to every domain. This domain: applied, with the
  residual `Data(...)` normalisation gap documented in §5 (open
  framework item).
- 2026-05-18 — from the biodiesel-routing-to-Timor-Leste incident
  (§A.18): every domain ships a TL supplement and every inject
  explicitly includes or excludes it. This domain: applied
  ([timor_leste_supplement.csv](timor_leste_supplement.csv), 27 rows);
  live watch-item — TL Crude Oil + Natural Gas still Unlimited in RAS
  if TL is re-enabled (§6).
- 2026-05-19 — from bioenergy (POME Import Cost final unlock): every
  open supply route needs a companion cost row in the same canonical.
  This domain: the *inverse* gap — costs exist but caps don't (§3);
  LPG confirmed priced (historical Import Cost trajectories in all 4
  scenarios) so the authored `Maximum Production = 0` does not strand
  demand.
- 2026-05-19 — from transport (§A.19 ActiveRegion drift): per-region
  writes can land in the wrong region slot without the framework's
  per-group ActiveRegion re-set. This domain: **suspected historical
  artifact found** — the region-scrambled Baseline/ATS Additions to
  Reserves layer (§7.3, hypothesis); the framework floor-fix protects
  all current runs; outstanding cleanup scheduled.
- 2026-05-20 — from transport (§A.20 blind-mode standard): blind
  injects are the default for all sectors; `Resources\` branches write
  correctly cached or blind. This domain: applied — keep default blind
  + `--fail-fast`; no KA/Demand branches in the fossil canonical.

---

*First edition, generated 2026-07-03 against the canon
`aeo9_v0.67_w_results` structure exports (anatomy §13 + the fossil
slice digests) and the adapter/injector as of this commit. The
committed canonical is 229 rows in source units; push
`canonical_leap_native.csv` per §2.5. If you change
[build_canonical.py](build_canonical.py), the producing cohorts, the
conversion registry, or close any §3/§5/§7 open item, update this guide
in the same commit (CLAUDE.md §6.1).*
