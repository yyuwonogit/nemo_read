# Bioenergy CSV — Author Spec (single-cap, dated 2026-04-29)

This is the **operational truth** for `bioenergy_leap_input.csv`. Every
authoring cycle starts here. If you find yourself doing something that
contradicts this file, **stop and ask** — don't infer scope from absence.

For the deep technical reference (column conventions, audit history,
unit-conversion registry), see [CSV_AUTHORING_GUIDE.md](CSV_AUTHORING_GUIDE.md).

---

## Quick reference card

| | Value |
|---|---|
| File you author | [bioenergy_leap_input.csv](bioenergy_leap_input.csv) |
| LEAP target area | `aeo9_v0.33_bak` |
| Design | **Single-cap** — `Resources\Primary\<X>:Maximum Production` is the only crop-supply cap. No land tier. |
| Distinct (branch, variable) pairs in source | **86 exactly** |
| → that inject to LEAP | **58** (the INJECT column in §6) |
| → filtered as LEAP-missing | **7** (LEAP doesn't have these branches yet — kept in source for forward compatibility) |
| → filtered as deferred | **21** (emission factors on Feedstock Fuels sub-branches + CO2 biogenic on Resources\Secondary\Biodiesel — see §5) |
| Source rows (incl. header) | **555** (1 header + 554 data) |
| Canonical rows after fan-out | **580** (after `build_canonical.py`) |
| Validation command | `python mailbox/bioenergy/run_workflow.py` |
| Target audit status | 27+ match · 29 auto-converted · **0 unresolved · 0 no_leap_unit** |

---

## 1. The authoring cycle

```
┌──────────────────────────────────────────────────────────────────────┐
│  1. RECEIVE     this spec + the current bioenergy_leap_input.csv     │
│  2. UPDATE      values inside the existing rows (don't add/remove)   │
│  3. VALIDATE    run python mailbox/bioenergy/run_workflow.py         │
│  4. CHECK       0 unresolved + 0 no_leap_unit in unit_audit.csv      │
│  5. SEND BACK   updated CSV + 1-line summary of what changed         │
└──────────────────────────────────────────────────────────────────────┘
```

**Default mental model:** the structure is locked. You are updating
*data values* only — `expression` (the `Interp(...)` numerics) and where
warranted, the `note` provenance. Branch paths, variable names, units,
and the set of rows are fixed by §6 below.

If you genuinely need to add a new (branch, variable) pair (e.g., a new
feedstock or a new variable LEAP exposes that wasn't audited before),
that's a structural change — coordinate first, don't just add the row.

---

## 2. What you can change without coordinating

| Column | Change freely? | Notes |
|---|---|---|
| `expression` | ✅ yes | The `Interp(year, value, ...)` numerics — your main job |
| `note` | ✅ yes | Free text. **Preserve `[2026-04-29 §12.1 author-action applied]` markers** if present (see §3) |
| `source` | ✅ yes | Update if you've drawn from a new source |
| `data_confidence` | ✅ yes | Reassess if numbers now have stronger backing |
| `domain` | ⚠️ rarely | Bioenergy-specific tag; usually preserved |
| `fuel` | ❌ no | Auto-extracted by the adapter; don't override |
| `unit` | ❌ no | Don't change without coordinating — see §4 (every unit in §6 has been probe-confirmed against LEAP) |
| `branch` | ❌ no | Don't rename, restructure, or relocate |
| `variable` | ❌ no | Variable names are LEAP-side identifiers; don't paraphrase |
| `ams` | ❌ no | Don't drop AMS rows (Singapore's `0` value is intentional and necessary) |

---

## 3. Don't undo prior fixes — preserved markers

Some rows carry a `[2026-04-29 §12.1 author-action applied]` tag in
their `note` column. These rows had their unit + expression fixed in a
prior cycle (Apr 29 2026) to match LEAP's expected unit. **Keep the unit
and the marker.** You may update the numeric `expression` if the data
itself revises, but don't revert the unit.

The 70 rows that carry this marker (7 distinct (branch, variable) pairs
× 10 AMS each):

| Branch | Variable | Locked unit |
|---|---|---|
| `Resources\Primary\Palm Oil` | Maximum Production | `Metric Tonne` |
| `Resources\Primary\Coconut Oil` | Maximum Production | `Metric Tonne` |
| `Resources\Primary\Sugarcane` | Maximum Production | `Metric Tonne` |
| `Resources\Primary\Cassava` | Maximum Production | `Metric Tonne` |
| `Resources\Primary\Corn` | Maximum Production | `Metric Tonne` |
| `Resources\Primary\Corn` | Production Cost | `2020 USD/Metric Tonne` |
| `Resources\Primary\Palm Oil Mill Effluent` | Production Cost | `2020 USD/Tonnes of Oil Equivalent` |

(LEAP-side: `Resources\Primary\Corn:Maximum Production` was also changed
in LEAP UI from `Gigajoule` → `Metric Tonne` in this cycle, so the unit
is now uniform across the 5 main crops.)

---

## 4. Unit policy — LEAP is authoritative

LEAP's `Variable.DataUnitText` per (branch, variable) is the single
source of truth. Every unit listed in §6 has been probe-confirmed
against `aeo9_v0.33_bak`.

**Three things you might be tempted to do — don't:**

1. **Don't change a unit** because "USD/t POME oil" reads more naturally
   to you than "2020 USD/Tonnes of Oil Equivalent". The §6 unit is what
   LEAP stores; if your source data is in a different unit, convert the
   *value*, keep the unit string.

2. **Don't drop a unit** to bare `2020 USD` or `USD` thinking LEAP will
   infer. LEAP always wants USD per *something*.

3. **Don't widen scope** ("CO2 (process)" sub-branches removed → also
   remove from parent processes). Filtering decisions live in
   [build_canonical.py](build_canonical.py) (`LEAP_MISSING_BRANCHES`,
   `_is_deferred`); read those constants to see what's filtered, don't
   over-extend.

For values that need unit conversion to fit LEAP, the auto-conversion
registry handles 29 of the current pairs (LHV-based etc.) — those
appear as `mismatch` with a proposed factor in the audit, which is
**fine**. Don't try to "fix" them.

---

## 5. Filters in `build_canonical.py` — what gets dropped at build time

Two filter sets in the adapter. **Both are documented; if they catch
your row, that's the design, not a bug.**

### 5.1 `LEAP_MISSING_BRANCHES` (7 distinct pairs / ~70 rows post-fan-out)

Branches that exist in the source CSV but don't yet exist in the LEAP
tree. Source keeps them so when LEAP is updated, the data is ready.

| Branch | Why kept in source |
|---|---|
| `Resources\Primary\Rice Straw` | Branch creation pending in LEAP (§11.B.4 of the old guide) |
| `Resources\Primary\Used Cooking Oil` | Branch creation pending in LEAP (§11.B.5) |
| `Transformation\Bioethanol Production\Processes\Cellulosic Rice Straw` | Process creation pending in LEAP (§11.B.1) |

When LEAP's tree gets these branches added, drop the corresponding
entries from `LEAP_MISSING_BRANCHES` in `build_canonical.py` and re-run.

### 5.2 `_is_deferred()` (21 distinct pairs / ~210 rows post-fan-out)

(branch, variable) patterns LEAP doesn't expose on the branch as
authored — likely the variables belong on a different branch. Held
back until the placement question is resolved.

| Pattern | Reason |
|---|---|
| 7 emission-factor variables (`CO2 (process)`, `CH4 (process)`, `N2O (process)`, `NH3 (process)`, `NOx (process)`, `SO2 (process)`, `NMVOC (process)`) on `\Feedstock Fuels\<crop>` sub-branches | LEAP doesn't expose emission factors on Feedstock Fuels sub-branches. They probably belong on the parent Process branch — but that needs probe confirmation before relocating. |
| `CO2 biogenic` on `Resources\Secondary\Biodiesel` | LEAP doesn't expose this variable on the Secondary Resource. Probably belongs on the producer Process. |

These rows stay in the source CSV — when the placement is resolved,
move them to the correct branches and remove from `_is_deferred`.

---

## 6. The full (branch, variable) matrix — source of truth

86 distinct pairs total. Each row in this table corresponds to either
1 source row (`All 10 AMS` aggregate) or 10 source rows (per-AMS),
indicated in the **Per-AMS?** column.

### 6.1 Resources\Primary tier (33 pairs · 7 inject-ready feedstocks + 2 LEAP-missing)

| Branch | Variable | Unit | Per-AMS? | Status |
|---|---|---|---|---|
| `Resources\Primary\Cassava` | `Area Harvested` | `Thousand ha` | 10 AMS | INJECT |
| `Resources\Primary\Cassava` | `Crop Yield` | `t/ha` | 10 AMS | INJECT |
| `Resources\Primary\Cassava` | `Import Cost` | `USD/t fresh root` | 10 AMS | INJECT |
| `Resources\Primary\Cassava` | `Maximum Production` | `Metric Tonne` | 10 AMS | INJECT |
| `Resources\Primary\Cassava` | `Production Cost` | `USD/t fresh root` | 10 AMS | INJECT |
| `Resources\Primary\Coconut Oil` | `Area Harvested` | `Thousand ha` | 10 AMS | INJECT |
| `Resources\Primary\Coconut Oil` | `Crop Yield` | `t/ha` | 10 AMS | INJECT |
| `Resources\Primary\Coconut Oil` | `Import Cost` | `USD/t nuts-in-shell` | 10 AMS | INJECT |
| `Resources\Primary\Coconut Oil` | `Maximum Production` | `Metric Tonne` | 10 AMS | INJECT |
| `Resources\Primary\Coconut Oil` | `Production Cost` | `USD/t nuts-in-shell` | 10 AMS | INJECT |
| `Resources\Primary\Corn` | `Area Harvested` | `Thousand ha` | 10 AMS | INJECT |
| `Resources\Primary\Corn` | `Crop Yield` | `t/ha` | 10 AMS | INJECT |
| `Resources\Primary\Corn` | `Import Cost` | `USD/t grain` | 10 AMS | INJECT |
| `Resources\Primary\Corn` | `Maximum Production` | `Metric Tonne` | 10 AMS | INJECT |
| `Resources\Primary\Corn` | `Production Cost` | `2020 USD/Metric Tonne` | 10 AMS | INJECT |
| `Resources\Primary\Molasses` | `Maximum Production` | `Tonne` | 10 AMS | INJECT |
| `Resources\Primary\Molasses` | `Production Cost` | `USD/t molasses` | 10 AMS | INJECT |
| `Resources\Primary\Palm Oil` | `Area Harvested` | `Thousand ha` | 10 AMS | INJECT |
| `Resources\Primary\Palm Oil` | `Crop Yield` | `t/ha` | 10 AMS | INJECT |
| `Resources\Primary\Palm Oil` | `Import Cost` | `USD/t FFB` | 10 AMS | INJECT |
| `Resources\Primary\Palm Oil` | `Maximum Production` | `Metric Tonne` | 10 AMS | INJECT |
| `Resources\Primary\Palm Oil` | `Production Cost` | `USD/t FFB` | 10 AMS | INJECT |
| `Resources\Primary\Palm Oil Mill Effluent` | `Maximum Production` | `Tonne` | 10 AMS | INJECT |
| `Resources\Primary\Palm Oil Mill Effluent` | `Production Cost` | `2020 USD/Tonnes of Oil Equivalent` | 10 AMS | INJECT |
| `Resources\Primary\Rice Straw` | `Maximum Production` | `Tonne` | 10 AMS | FILTER:LEAP-missing |
| `Resources\Primary\Rice Straw` | `Production Cost` | `USD/t rice straw dry` | 10 AMS | FILTER:LEAP-missing |
| `Resources\Primary\Sugarcane` | `Area Harvested` | `Thousand ha` | 10 AMS | INJECT |
| `Resources\Primary\Sugarcane` | `Crop Yield` | `t/ha` | 10 AMS | INJECT |
| `Resources\Primary\Sugarcane` | `Import Cost` | `USD/t cane` | 10 AMS | INJECT |
| `Resources\Primary\Sugarcane` | `Maximum Production` | `Metric Tonne` | 10 AMS | INJECT |
| `Resources\Primary\Sugarcane` | `Production Cost` | `USD/t cane` | 10 AMS | INJECT |
| `Resources\Primary\Used Cooking Oil` | `Maximum Production` | `Tonne` | 10 AMS | FILTER:LEAP-missing |
| `Resources\Primary\Used Cooking Oil` | `Production Cost` | `USD/t UCO` | 10 AMS | FILTER:LEAP-missing |

> **Production Cost trajectory convention (updated 2026-04-29):** All
> `Production Cost` rows — main crops **and** residue/byproduct resources
> (Molasses, POME, Rice Straw, UCO) — share the same per-year trajectory
> pattern (~23% real-cost rise over 2025–2060, ≈ 0.6 %/yr nominal).
> Author confirmed residue costs adopt the same escalation as the other
> fuels. Any flat-valued residue rows still in source (e.g.,
> `Interp(2025, 80.0, ..., 2060, 80.0)` for Molasses) are placeholder and
> will be replaced with escalating series in the next author iteration.

### 6.2 Resources\Secondary tier (4 pairs · 3 output fuels + 1 deferred)

| Branch | Variable | Unit | Per-AMS? | Status |
|---|---|---|---|---|
| `Resources\Secondary\Biodiesel` | `CO2 biogenic` | `t/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Resources\Secondary\Biodiesel` | `Import Cost` | `2020 USD/Liter` | 10 AMS | INJECT |
| `Resources\Secondary\Ethanol` | `Import Cost` | `2020 USD/Liter` | 10 AMS | INJECT |
| `Resources\Secondary\Methanol` | `Import Cost` | `2020 USD/Metric Tonne` | 10 AMS | INJECT |

### 6.3 Biodiesel Production · Processes (parent · 9 pairs · 3 processes × 3 vars)

| Branch | Variable | Unit | Per-AMS? | Status |
|---|---|---|---|---|
| `Transformation\Biodiesel Production\Processes\CME Biodiesel` | `Capital Cost` | `USD/GJ` | All 10 AMS | INJECT |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel` | `Maximum Capacity` | `Million Tonnes/yr` | 10 AMS | INJECT |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel` | `Variable OM Cost` | `USD/GJ` | 10 AMS | INJECT |
| `Transformation\Biodiesel Production\Processes\FAME Biodiesel` | `Capital Cost` | `USD/GJ` | All 10 AMS | INJECT |
| `Transformation\Biodiesel Production\Processes\FAME Biodiesel` | `Maximum Capacity` | `Million Tonnes/yr` | 10 AMS | INJECT |
| `Transformation\Biodiesel Production\Processes\FAME Biodiesel` | `Variable OM Cost` | `USD/GJ` | 10 AMS | INJECT |
| `Transformation\Biodiesel Production\Processes\POME Biodiesel` | `Capital Cost` | `USD/GJ` | All 10 AMS | INJECT |
| `Transformation\Biodiesel Production\Processes\POME Biodiesel` | `Maximum Capacity` | `Million Tonnes/yr` | 10 AMS | INJECT |
| `Transformation\Biodiesel Production\Processes\POME Biodiesel` | `Variable OM Cost` | `USD/GJ` | 10 AMS | INJECT |

### 6.4 Biodiesel Production · Feedstock Fuels (sub-branch · 8 pairs · 2 inject + 6 deferred)

| Branch | Variable | Unit | Per-AMS? | Status |
|---|---|---|---|---|
| `Transformation\Biodiesel Production\Processes\CME Biodiesel\Feedstock Fuels\Coconut Oil` | `CH4 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel\Feedstock Fuels\Coconut Oil` | `CO2 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel\Feedstock Fuels\Coconut Oil` | `Fuel Cost` | `USD/t nuts-in-shell` | All 10 AMS | INJECT |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel\Feedstock Fuels\Coconut Oil` | `N2O (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel\Feedstock Fuels\Coconut Oil` | `NH3 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel\Feedstock Fuels\Coconut Oil` | `NOx (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel\Feedstock Fuels\Coconut Oil` | `SO2 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Biodiesel Production\Processes\FAME Biodiesel\Feedstock Fuels\Palm Oil` | `Fuel Cost` | `USD/t FFB` | All 10 AMS | INJECT |

> **Note:** POME Biodiesel currently has no Feedstock Fuels sub-branch
> entries in source — it consumes `Palm Oil Mill Effluent` from the
> Resource tier directly, no per-process Fuel Cost row needed.

### 6.5 Bioethanol Production · Processes (parent · 15 pairs · 4 inject-ready + 1 LEAP-missing × 3 vars each)

| Branch | Variable | Unit | Per-AMS? | Status |
|---|---|---|---|---|
| `Transformation\Bioethanol Production\Processes\Cassava` | `Capital Cost` | `USD/GJ` | All 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Cassava` | `Maximum Capacity` | `Million Tonnes/yr` | 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Cassava` | `Variable OM Cost` | `USD/GJ` | 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Cellulosic Rice Straw` | `Capital Cost` | `USD/GJ` | All 10 AMS | FILTER:LEAP-missing |
| `Transformation\Bioethanol Production\Processes\Cellulosic Rice Straw` | `Maximum Capacity` | `Million Tonnes/yr` | 10 AMS | FILTER:LEAP-missing |
| `Transformation\Bioethanol Production\Processes\Cellulosic Rice Straw` | `Variable OM Cost` | `USD/GJ` | 10 AMS | FILTER:LEAP-missing |
| `Transformation\Bioethanol Production\Processes\Corn Ethanol` | `Capital Cost` | `USD/GJ` | All 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Corn Ethanol` | `Maximum Capacity` | `Million Tonnes/yr` | 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Corn Ethanol` | `Variable OM Cost` | `USD/GJ` | 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Molasses` | `Capital Cost` | `USD/GJ` | All 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Molasses` | `Maximum Capacity` | `Million Tonnes/yr` | 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Molasses` | `Variable OM Cost` | `USD/GJ` | 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Sugarcane` | `Capital Cost` | `USD/GJ` | All 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Sugarcane` | `Maximum Capacity` | `Million Tonnes/yr` | 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Sugarcane` | `Variable OM Cost` | `USD/GJ` | 10 AMS | INJECT |

### 6.6 Bioethanol Production · Feedstock Fuels (sub-branch · 17 pairs · 3 inject + 14 deferred)

| Branch | Variable | Unit | Per-AMS? | Status |
|---|---|---|---|---|
| `Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels\Cassava` | `CH4 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels\Cassava` | `CO2 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels\Cassava` | `Fuel Cost` | `USD/t fresh root` | All 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels\Cassava` | `N2O (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels\Cassava` | `NH3 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels\Cassava` | `NMVOC (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels\Cassava` | `NOx (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels\Cassava` | `SO2 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Corn Ethanol\Feedstock Fuels\Corn` | `Fuel Cost` | `USD/t grain` | All 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels\Sugarcane` | `CH4 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels\Sugarcane` | `CO2 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels\Sugarcane` | `Fuel Cost` | `USD/t cane` | All 10 AMS | INJECT |
| `Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels\Sugarcane` | `N2O (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels\Sugarcane` | `NH3 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels\Sugarcane` | `NMVOC (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels\Sugarcane` | `NOx (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |
| `Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels\Sugarcane` | `SO2 (process)` | `kg/TJ` | All 10 AMS | FILTER:deferred-§12.4 |

> **Note:** Molasses and Cellulosic Rice Straw bioethanol processes
> currently have no Feedstock Fuels sub-branch entries in source.
> Molasses presumably consumes `Resources\Primary\Molasses` directly.

---

## 7. Validation procedure

Run from the repo root:

```bash
python mailbox/bioenergy/run_workflow.py
```

This will:
1. Build canonical from source (filters applied) → `canonical_leap_inputs.csv`
2. Probe LEAP for the `(branch, variable)` units of every canonical row
3. Audit canonical units vs LEAP units → `unit_audit.csv`
4. Apply auto-conversions → `canonical_leap_native.csv` (the LEAP-injection-ready file)

### What success looks like

```
[step 3] audit canonical vs LEAP units
   wrote mailbox\bioenergy\unit_audit.csv  (58 rows; {'mismatch': 31, 'match': 27})
   WARNING: 0 mismatches have NO proposed factor
[step 4] apply conversions -> canonical_leap_native.csv
   wrote mailbox\bioenergy\canonical_leap_native.csv  (580 rows; ~290 converted, 0 unresolved)
```

**Key indicators:**
- `unit_audit.csv` has **58 rows total** — matches §6's INJECT count
- **0 unresolved** mismatches (every difference has a registered factor)
- **0 no_leap_unit** (no rows pointing at LEAP branches that don't exist)
- `WARNING` lines from `build_canonical.py` only mention the documented filter sets (LEAP-missing 7 pairs, deferred 21 pairs)

### What failure looks like, and how to read it

| Symptom | Likely cause | Fix |
|---|---|---|
| `no_leap_unit > 0` | A new (branch, variable) pair was added that LEAP doesn't expose | Coordinate before adding new pairs |
| `mismatch with no proposed_factor > 0` | A unit was changed to one not in the registry | Revert the unit, or coordinate adding registry support |
| Canonical row count ≠ 580 | Rows were added/removed, or AMS expansion broke | Diff against the prior `bioenergy_leap_input.csv` to find the structural change |
| Unexpected `WARNING: filtered N rows...` line | A row matched `LEAP_MISSING_BRANCHES` or `_is_deferred` you didn't expect | Read the WARNING list — it names exactly which (branch, variable) pairs got caught |

---

## 8. Anti-patterns — common mistakes to avoid

1. **Removing rows because the audit shows `mismatch`.** A `mismatch`
   with a proposed factor is **fine** — the registry handles it
   automatically at injection time. Removing the row leaves LEAP without
   the input value entirely.

2. **Removing rows because emission factors on Feedstock Fuels are
   "deferred".** The deferral is scoped to **emission factors on
   Feedstock Fuels sub-branches only** (see §5.2). Other variables on
   Feedstock Fuels (`Fuel Cost`) and emission factors on parent Process
   branches stay. *(This was the over-removal pattern in the 2026-04-29
   author iteration — please don't repeat.)*

3. **Inferring scope from absence.** This spec is the positive scope.
   If something isn't listed in §6, that doesn't mean "remove it" — it
   means "ask, because we may have missed documenting it."

4. **Changing units without coordinating.** Every unit in §6 is
   probe-confirmed. Swapping `Metric Tonne` for `Tonne` (or any unit
   change) breaks the audit's match unless the new unit is also in the
   registry. Run the workflow to verify before sending back.

5. **Bare currency unit.** Don't author `2020 USD` alone; LEAP wants
   USD per *something* (`/Liter`, `/Metric Tonne`, etc.).

---

## 9. Open author-action items

**0 remaining** as of 2026-04-29 (post Corn LEAP-side unit harmonization).

All 7 author-action unit fixes are applied to source and locked via §3
preserved markers. The audit should report 0 unresolved + 0 no_leap_unit
once the LEAP-side `Resources\Primary\Corn:Maximum Production` UI change
to `Metric Tonne` lands (sibling-harmonization with the other 4 main
crops).

When the next item arises, it gets listed here with an explicit
conversion specification.

---

## 10. Where to look for deeper detail

- [CSV_AUTHORING_GUIDE.md §0](CSV_AUTHORING_GUIDE.md) — scope statement (single-cap)
- [CSV_AUTHORING_GUIDE.md §11.2](CSV_AUTHORING_GUIDE.md) — full unit-conversion factor table (29 auto-conversions)
- [CSV_AUTHORING_GUIDE.md §12.1](CSV_AUTHORING_GUIDE.md) — historical record of the §12.1 author-action fixes applied 2026-04-29
- [CSV_AUTHORING_GUIDE.md §12.4](CSV_AUTHORING_GUIDE.md) — deferral rationale for emission factors on Feedstock Fuels sub-branches
- [build_canonical.py](build_canonical.py) — see `LEAP_MISSING_BRANCHES` and `_is_deferred()` to see exactly what gets filtered at build time
- [unit_audit.csv](unit_audit.csv) — the live audit snapshot, regenerated each `run_workflow.py` run
