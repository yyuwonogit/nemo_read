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
| LEAP target area | `aeo9_v0.36` (was `aeo9_v0.33_bak` for the cycle-1 audit) |
| Design | **Single-cap** — `Resources\Primary\<X>:Maximum Production` is the only crop-supply cap. No land tier. |
| Distinct (branch, variable) pairs in source | **86 exactly** |
| → that inject to LEAP | **58** (the INJECT column in §6) |
| → filtered as LEAP-missing | **7** (LEAP doesn't have these branches yet — kept in source for forward compatibility) |
| → filtered as deferred | **21** (emission factors on Feedstock Fuels sub-branches + CO2 biogenic on Resources\Secondary\Biodiesel — see §5) |
| Source rows (incl. header) | **555** (1 header + 554 data) |
| Canonical rows after fan-out | **580** (after `build_canonical.py`) |
| Validation command | `python inject/bioenergy/run_workflow.py` |
| Target audit status | 27+ match · 29 auto-converted · **0 unresolved · 0 no_leap_unit** |

---

## 1. The authoring cycle

```
┌──────────────────────────────────────────────────────────────────────┐
│  1. RECEIVE     this spec + the current bioenergy_leap_input.csv     │
│  2. UPDATE      values inside the existing rows (don't add/remove)   │
│  3. VALIDATE    run python inject/bioenergy/run_workflow.py         │
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
× 10 AMS each), with the **physical basis** the value must be in
(amended 2026-05-05 — see [CSV_AUTHORING_GUIDE.md §12.5](CSV_AUTHORING_GUIDE.md)):

| Branch | Variable | Locked unit | Locked physical basis |
|---|---|---|---|
| `Resources\Primary\Palm Oil` | Maximum Production | `Metric Tonne` | tonnes of **FFB** (raw crop), not extracted palm oil |
| `Resources\Primary\Coconut Oil` | Maximum Production | `Metric Tonne` | tonnes of **nuts-in-shell** (raw crop) |
| `Resources\Primary\Sugarcane` | Maximum Production | `Metric Tonne` | tonnes of **cane** (raw crop), not raw sugar |
| `Resources\Primary\Cassava` | Maximum Production | `Metric Tonne` | tonnes of **fresh root** (raw crop) |
| `Resources\Primary\Corn` | Maximum Production | `Metric Tonne` | tonnes of **grain** (raw crop) |
| `Resources\Primary\Corn` | Production Cost | `2020 USD/Metric Tonne` | per-tonne of grain |
| `Resources\Primary\Palm Oil Mill Effluent` | Production Cost | `2020 USD/Tonnes of Oil Equivalent` | per-TOE of POME oil (LHV-converted from USD/t POME oil) |

(LEAP-side: `Resources\Primary\Corn:Maximum Production` was also changed
in LEAP UI from `Gigajoule` → `Metric Tonne` in this cycle, so the unit
is now uniform across the 5 main crops.)

> **Why the basis matters even though the unit string is identical:**
> the cap and the cost row on the same branch must refer to the same
> physical quantity. `Production Cost` is `USD/t FFB` so the cap must
> be tonnes of FFB. Authoring the cap in tonnes of *extracted* palm oil
> (which is what LEAP rolls into ~5× of FFB tonnage) silently
> under-states the cap by the oil-extraction-rate factor. This is the
> defect the 2026-05-05 author iteration corrected — see §9 entry.

---

## 4. Unit policy — LEAP is authoritative

LEAP's `Variable.DataUnitText` per (branch, variable) is the single
source of truth. Every unit listed in §6 was probe-confirmed against
`aeo9_v0.33_bak` in cycle 1, and re-verified against the current
inject target `aeo9_v0.36` in cycle 2 — all 58 inject (branch, variable)
unit strings are byte-identical between the two areas, so the canonical
file works against either without rebuild.

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

### 5.3 `PROCESS_MAX_CAPACITY_HANDOFF_BRANCHES` — closed (kept as empty set, see §9 Cycle 3)

Briefly active 2026-05-05 when v0.36 returned `Variable("Maximum Capacity") = None`
on the 7 bioenergy process branches. Turned out to be transient — `Maximum
Capacity` only appears under the RAS scenario in v0.36, not when the active
scenario is something else. With RAS active the variable is exposed normally,
and the 70 rows pushed clean. The set in `build_canonical.py` is now empty;
the filter machinery is left in place so it can be re-armed if a similar
v-version-bump issue recurs. See [§9 Cycle 3](#9-open-author-action-items)
and [CSV_AUTHORING_GUIDE.md §13.2](CSV_AUTHORING_GUIDE.md).

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
python inject/bioenergy/run_workflow.py
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

## 9. Open author-action items / cycle log

**0 remaining** as of 2026-05-05 (post supply-cap basis correction).

Each row below records a closed author-action cycle. New cycles get
appended; nothing is rewritten in place.

### Cycle 1 — 2026-04-29: §12.1 unit-string fixes (closed)

7 distinct (branch, variable) pairs × 10 AMS = 70 rows had their
**unit string** corrected (e.g. `Million Tonnes/yr` → `Metric Tonne`
for the 5 main crops' `Maximum Production`; `2020 USD/Kilogramme` →
`2020 USD/Metric Tonne` for Corn `Production Cost`; POME `Production
Cost` LHV-converted to `2020 USD/Tonnes of Oil Equivalent`). Locked via
§3 preserved markers. Closed once the LEAP-side
`Resources\Primary\Corn:Maximum Production` UI change to `Metric Tonne`
landed (sibling-harmonization with the other 4 main crops).

### Cycle 2 — 2026-05-05: §12.5 supply-cap basis correction + inject target migration to `aeo9_v0.36` (closed)

LEAP target area for inject moved from `aeo9_v0.33_bak` → `aeo9_v0.36`.
Verified: all 58 inject (branch, variable) unit strings match between
v0.33_yy_rev1 and v0.36 cached probes; the 3 `LEAP_MISSING_BRANCHES`
(Rice Straw, Used Cooking Oil, Cellulosic Rice Straw) are still missing
in v0.36. The canonical_leap_native.csv built in this cycle works
against v0.36 without rebuild.



Six LEAP v0.34 RAS infeasibilities (Indonesia / Malaysia / Thailand
palm, Philippines / Thailand sugarcane, Thailand cassava, all years
2030–2060) were caused by `Maximum Production` rows authored in
**extracted-product tonnes** (palm oil, raw sugar) when the
`Production Cost` / `Import Cost` rows on the same branch are in
**raw-crop tonnes** (FFB, cane). LEAP read both as `Metric Tonne` and
the cap landed ~5× too small for palm and ~9× too small for sugarcane.

Closed by:
1. Re-emitting the `Maximum Production` Interp expressions in raw-crop
   tonnes from the upstream `Geospatial Bioenergy pipeline 01-10`
   panel. Indonesia palm 2025 lifts from ~19 Mt → ~248 Mt (above
   B40's ~92 Mt requirement).
2. Treating extra-ASEAN crop exports as redirectable to biofuel
   (closes Malaysia palm and Thailand cassava 2030 residual
   tightness).
3. Annotating §3 of this spec with the **locked physical basis** per
   branch so a future author can't fall into the same trap.

Net effect on source CSV: same 554-row schema, same 86 (branch,
variable) pairs, same units on the LEAP side. Only `Maximum
Production` numeric values changed (36 rows = 6 crops × ~6 AMS with
non-zero production). `Maximum Capacity` rows were also re-emitted in
`Interp(cumulative)` form rather than `Add(delta)` form (same
milestone-year schedule, different inter-milestone behaviour — see
[CSV_AUTHORING_GUIDE.md §13.2](CSV_AUTHORING_GUIDE.md)). `Production
Cost` numeric values unchanged; only the per-row note text was rewritten
to remove a stale `/1000 to convert USD/t grain → USD/Kilogramme`
comment that no longer applies after the LEAP-side unit shift back to
`USD/Metric Tonne`.

> **Stale note marker on Maximum Production rows (acknowledged):** all
> 70 `Resources\Primary\<Crop>:Maximum Production` rows still carry
> the legacy note text `Maximum Production filtered out — moved to
> Cultivation Process Maximum Capacity (refactor 2026-04-21)` from
> Cycle 0. Under the current single-cap design (§0) and after the
> Cycle 2 raw-crop-basis fix this text is **historically incorrect**:
> Maximum Production is the *primary* cap, not a "filtered out"
> redundancy. The note will be rewritten by the upstream emitter on
> the next regen; until then, treat it as historical noise — what
> matters now is the locked basis in §3.

### Cycle 3 — 2026-05-05: Maximum Capacity inject (closed same-day)

Live COM probe of `aeo9_v0.36` initially returned `Variable("Maximum Capacity") = None`
on all 7 bioenergy process branches, looking like the variable had been
retired in favour of the Exogenous / Endogenous Capacity split. Acted
defensively: added `PROCESS_MAX_CAPACITY_HANDOFF_BRANCHES` +
`_is_process_max_capacity_handoff()` to [build_canonical.py](build_canonical.py),
routed the 70 rows (7 branches × 10 AMS) to
[bioenergy_maximum_capacity_handoff.csv](bioenergy_maximum_capacity_handoff.csv)
with the migration-context note prefix, and pushed the remaining 510 rows
clean against v0.36 RAS.

Bioenergy team then clarified: in v0.36 `Maximum Capacity` only appears
under the RAS scenario, not under any other active scenario — the probe
had run with a non-RAS scenario active so the variable looked retired.
With RAS active the variable was exposed normally. Removed the handoff
filter (the set is now empty in `build_canonical.py`; machinery kept for
re-arm), regenerated → 580 rows in [canonical_leap_native.csv](canonical_leap_native.csv),
re-injected with `--filter-variable "Maximum Capacity"` → 70/70 pushed
clean to RAS the same day.

[bioenergy_maximum_capacity_handoff.csv](bioenergy_maximum_capacity_handoff.csv)
is left in place as the cycle artefact (historical reference, not
actionable). Lesson preserved in [CSV_AUTHORING_GUIDE.md §13.2](CSV_AUTHORING_GUIDE.md):
LEAP variables can be scenario-scoped, so a `Variable() = None` on one
scenario doesn't prove retirement — confirm against RAS (or whatever
scenario the variable is meant to live in) before treating it as a
schema change.

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
