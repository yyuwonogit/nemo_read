# Bioenergy CSV — Authoring Guide

This document describes every transformation the
[build_canonical.py](build_canonical.py) adapter applies to
[bioenergy_leap_input.csv](bioenergy_leap_input.csv) before the row is fed
into the `nemo_read` LEAP-injection pipeline.

If you (the CSV owner) author future inputs **already in the canonical
shape described in §2**, the adapter step becomes a pass-through and you
remove an entire layer of human error. If you prefer to keep the current
"owner format" shape, the adapter will keep doing its job — just match the
column names and conventions in §1 exactly.

> **TL;DR for fastest hand-off:** copy the column headers and values
> exactly from the **Canonical schema** table in §2 below, expand
> "All 10 AMS" rows yourself, use short LEAP region names (Brunei, Laos,
> Vietnam — not Brunei Darussalam, Lao PDR, Viet Nam), and put the output
> fuel into its own `fuel` column rather than embedding it in `note`.

---

## 0. Scope — single-cap design (current truth, dated 2026-04-29)

The bioenergy model uses a **single-cap design**:
`Resources\Primary\<Crop>:Maximum Production` is the sole crop-supply cap.
This is the current truth and what every CSV authored against this guide
should produce.

**Out of scope (not authored, not injected):**
- `Resources\Primary\Arable` and `Resources\Primary\Perennial` (land caps)
- `Transformation\<Crop> Cultivation\Processes\<Crop> Cultivation` and any
  `\Feedstock Fuels\<Perennial|Arable>` sub-branches under them
- `Maximum Capacity` and `Variable OM Cost` rows on Cultivation processes
  (these have been relocated to `Resources\Primary\<Crop>:Maximum Production`
  and `Resources\Primary\<Crop>:Production Cost` respectively)
- `Co-product Credit (audit)` rows — not a real LEAP variable

The land-cap tier was previously explored as a complementary second cap
but is shelved indefinitely. Future revisions of this guide may
reintroduce it; until then, treat anything in §11 referencing
Arable / Perennial / Cultivation as **historical audit record**, not
authoring spec.

> **Note on LEAP-side land branches:** The LEAP area
> (`aeo9_v0.33_bak` at the time of writing) may still contain residual
> Cultivation / Arable / Perennial branches as orphans. That's fine —
> the canonical CSV doesn't reference them, so injection ignores them
> and model behaviour is unaffected. They can be deleted in LEAP for
> visual cleanliness whenever convenient; doing so is not required for
> correctness.

**What every new CSV should include** (per the guide below):
- `Transformation\Biodiesel Production\Processes\<X>` rows
- `Transformation\Bioethanol Production\Processes\<X>` rows
- `Resources\Primary\<feedstock>` rows for all 9 bioenergy feedstocks
  (Palm Oil, Coconut Oil, Sugarcane, Cassava, Corn, Molasses, Palm Oil
  Mill Effluent, Rice Straw, Used Cooking Oil) — each carrying
  `Maximum Production`, `Production Cost`, plus the per-feedstock
  variables from §5
- `Resources\Secondary\<output fuel>` rows (Biodiesel, Ethanol, Methanol)

> **LEAP-side gap (build-time filter, dated 2026-04-29):**
> `Resources\Primary\Rice Straw` and `Resources\Primary\Used Cooking Oil`
> branches do not yet exist in LEAP (`aeo9_v0.33_bak`). Until they're
> added (per §11.B.4 / §11.B.5), `build_canonical.py` filters their
> rows out of `canonical_leap_inputs.csv` and reports the skip count.
> The source `bioenergy_leap_input.csv` keeps these rows as-is — once
> the LEAP branches exist, drop the `LEAP_MISSING_BRANCHES` constant in
> the adapter and re-run.

---

## 1. Current "owner format" — what the CSV looks like today

The current bioenergy CSV uses these 9 columns (header row exact case):

| Column        | Required | Example                                             |
|---------------|----------|-----------------------------------------------------|
| `Branch Path` | yes      | `Transformation\Biodiesel Production\Processes\FAME Biodiesel` |
| `Variable`    | yes      | `Capital Cost`                                      |
| `Region`      | yes      | `All 10 AMS`, or one of the LEAP region names       |
| `Units`       | yes      | `USD/GJ`                                            |
| `Expression`  | yes      | `Interp(2025, 3.2422, 2030, 3.0833, ...)`           |
| `Domain`      | optional | `processing_cost`                                   |
| `Source`      | optional | `processing_cost_anchors.csv (cost_generator.py)`   |
| `Confidence`  | optional | `Medium` / `Medium-High` / `High` / `Low`           |
| `Note`        | optional | free text; may contain `output_fuel=Biodiesel` token|

Notes on each:

- **`Branch Path`** — backslash-separated LEAP tree path. Must match a
  real branch in the target LEAP area exactly (case-insensitive). Do not
  prefix with a leading backslash.
- **`Variable`** — must match a LEAP variable name exactly (e.g.
  `Capital Cost`, `Variable OM Cost`, `Maximum Capacity`). The pipeline
  refuses unknown variable names rather than guessing.
- **`Region`** — either the literal string `All 10 AMS` (which the
  adapter will fan out to 10 rows), or one of the long-form names listed
  in §3. Long-form names get normalised to LEAP short-form before
  injection.
- **`Units`** — the unit your value is in *as authored*. The pipeline
  later runs a unit audit against LEAP and applies a conversion factor if
  LEAP expects a different unit (e.g. `USD/GJ` → LEAP-native cost units).
  Authoring in any sensible unit is fine — the audit will catch it.
- **`Expression`** — a LEAP expression. Most rows use `Interp(year, val,
  year, val, ...)`. Constants are also allowed (e.g. just `0.95`). When
  the expression contains commas, the field **must be wrapped in double
  quotes** to satisfy CSV parsing.
- **`Domain` / `Source` / `Confidence`** — provenance fields. They flow
  through to the canonical output as `domain` and `data_confidence`
  columns and are never modified by the pipeline.
- **`Note`** — free text. The adapter scans it for an
  `output_fuel=<token>` or `fuel=<token>` substring and lifts that into
  a dedicated `fuel` column (used downstream for fuel-specific unit
  conversions; see §6).

---

## 2. Canonical schema — what the pipeline actually consumes

After the adapter runs, the file
[canonical_leap_inputs.csv](canonical_leap_inputs.csv) has these 11
columns (lowercase, fixed order):

| Column            | Source                                | Notes                          |
|-------------------|---------------------------------------|--------------------------------|
| `ams`             | `Region` (normalised)                 | LEAP short-form name (§3)      |
| `branch`          | `Branch Path` (verbatim)              | Backslash-separated            |
| `variable`        | `Variable` (verbatim)                 | Exact LEAP variable name       |
| `expression`      | `Expression` (verbatim)               | LEAP expression, quote if comma|
| `unit`            | `Units` (verbatim)                    | Author-side unit               |
| `fuel`            | extracted from `Note` (§6)            | `Biodiesel`, `Ethanol`, etc.   |
| `source`          | `Source` (verbatim)                   | Provenance string              |
| `note`            | `Note` (verbatim, full text retained) | Free text                      |
| `src_csv`         | filename of the source CSV            | Auto-set by the adapter        |
| `domain`          | `Domain` (verbatim)                   | Bioenergy-specific extra       |
| `data_confidence` | `Confidence` (verbatim)               | Bioenergy-specific extra       |

If your next CSV uses **these column names and conventions directly**, the
adapter becomes a 1:1 rename + pass-through and the only thing you still
need to do at the source is **AMS expansion** (§4) and **region
normalisation** (§3). Or skip both by writing canonical rows directly.

---

## 3. Region name normalisation

LEAP uses short-form names. The current CSV uses long-form names for
three countries; the adapter rewrites them as follows:

| In the CSV (`Region`) | After normalisation (`ams`) |
|-----------------------|-----------------------------|
| `Brunei Darussalam`   | `Brunei`                    |
| `Lao PDR`             | `Laos`                      |
| `Viet Nam`            | `Vietnam`                   |
| `Brunei`              | `Brunei` (unchanged)        |
| `Cambodia`            | `Cambodia` (unchanged)      |
| `Indonesia`           | `Indonesia` (unchanged)     |
| `Malaysia`            | `Malaysia` (unchanged)      |
| `Myanmar`             | `Myanmar` (unchanged)       |
| `Philippines`         | `Philippines` (unchanged)   |
| `Singapore`           | `Singapore` (unchanged)     |
| `Thailand`            | `Thailand` (unchanged)      |

> **For new CSVs**: please use the short-form names directly. The
> adapter only normalises the three problem cases above — any other
> long-form name (e.g. `Republic of the Union of Myanmar`) will be passed
> through verbatim and then *fail* the LEAP branch lookup.

---

## 4. "All 10 AMS" expansion

Rows with `Region = All 10 AMS` are fanned out to **10 rows**, one per
AMS, in this exact order:

```
Brunei, Cambodia, Indonesia, Laos, Malaysia,
Myanmar, Philippines, Singapore, Thailand, Vietnam
```

All other columns are copied verbatim into each fan-out row.

Net effect on the current bioenergy CSV: **599 input rows → 950 canonical
rows.** The 95 rows-per-AMS in the output reflect this fan-out plus the
already-per-AMS rows like `Variable OM Cost`.

> **For new CSVs**: if your data is genuinely region-agnostic, keep using
> `All 10 AMS` and let the adapter expand it. If your data already varies
> per AMS (as the wage-scaled `Variable OM Cost` rows do), write one row
> per AMS at the source — do not use `All 10 AMS` for those.

---

## 5. Variables in the bioenergy CSV (and where they go in LEAP)

Updated 2026-04-29 to match LEAP-side reality (verified by per-branch
COM probes against `aeo9_v0.33_bak`). Counts are post-fan-out (canonical
rows), grouped by the kind of LEAP branch they target.

> **Where this section was wrong before 2026-04-29:** earlier wording put
> `Area Harvested` / `Crop Yield` / `Production Cost` under a "Crop
> cultivation" group and `Maximum Capacity` under "Resources". LEAP
> probes show the opposite — see the *(probe-confirmed)* annotations
> below. The canonical CSV has always placed them on the LEAP-correct
> branches; only this section was misaligned.

**Transformation processes** (`Transformation\Biodiesel Production\...`,
`Transformation\Bioethanol Production\...`):

- `Capital Cost` — `USD/GJ`
- `Variable OM Cost` — `USD/GJ` (already per-AMS in source; no fan-out)
- `Maximum Capacity` — `Million Tonnes/yr` (probe-confirmed: lives on the
  Process branch, not on Resources)
- 7 emission factor variables (see *Emission factors* block below)

**Resources\Primary\\<Feedstock\>** — one branch per feedstock; the spec
applies uniformly to all 9 (Palm Oil, Coconut Oil, Sugarcane, Cassava,
Corn, Molasses, Palm Oil Mill Effluent, Rice Straw, Used Cooking Oil):

- `Maximum Production` — `Million Tonnes/yr` (sole crop-supply cap;
  probe-confirmed input variable)
- `Production Cost` — `USD/t <feedstock-specific>` (`USD/t grain`,
  `USD/t cane`, `USD/t POME wet`, `USD/t molasses`, `USD/t fresh root`,
  `USD/t nuts-in-shell`, `USD/t FFB`, `USD/t rice straw dry`, `USD/t UCO`)
- `Import Cost` — `USD/t <feedstock-specific>`
- `Area Harvested` — `Thousand ha` (probe-confirmed: input variable on
  the Resource branch; only meaningful for the 5 main crops, optional
  for byproducts)
- `Crop Yield` — `t/ha` (same — 5 main crops)

**Resources\Secondary\\<Output\>** (Biodiesel, Ethanol, Methanol):

- `Import Cost` — `2020 USD/Liter` for Ethanol/Biodiesel,
  `2020 USD/Metric Tonne` for Methanol
- `Fuel Cost` — author-side cost unit (with feedstock-specific LHV
  conversion at audit time per §11.2)

**Emission factors** (per-process, 7 species):

- `CO2 Emission Factor (Non Biogenic)` — `t/TJ`
- `CO2 Emission Factor (Biogenic)` — `t/TJ`
- `CH4 Emission Factor` — `kg/TJ`
- `N2O Emission Factor` — `kg/TJ`
- `NH3 Emission Factor` — `kg/TJ`
- `NOx Emission Factor` — `kg/TJ`
- `SO2 Emission Factor` — `kg/TJ`
- `NMVOC Emission Factor` — `kg/TJ`

> The exact LEAP-native unit for each variable is determined per-row by
> the `nemo_read-leap-units` probe (see workflow docs in
> [run_workflow.py](run_workflow.py)). Wherever your authored unit
> differs from LEAP's, the audit step proposes a conversion factor or
> flags the row as `MISMATCH unresolved` for you to override.

---

## 6. Fuel-context extraction from `Note`

Many rows embed the *output fuel* of a process inside the free-text
`Note` column, e.g.:

> `Harmonised across AMS (equipment is globally traded); output_fuel=Biodiesel`

The adapter scans every `Note` value with this regex:

```python
re.compile(r"\b(?:output_)?fuel\s*=\s*([^;,\n]+)", re.IGNORECASE)
```

Matched tokens (case-insensitive, stops at the first `;`, `,`, or
newline) are lifted into a dedicated `fuel` column on the canonical
output. In the current CSV this populates **190 of 950 canonical rows**.

The `fuel` column is used downstream to:

- pick fuel-specific LHV constants when converting between mass and
  energy units (e.g. `USD/t Ethanol` vs `USD/GJ` needs the ethanol LHV,
  not a generic biomass LHV);
- enable per-fuel auditing (`audit_canonical_units` can join against
  fuel-property tables to validate emission-factor magnitudes).

> **For new CSVs**: please write a top-level `fuel` column directly
> rather than embedding `output_fuel=...` inside `note`. Both styles
> work, but an explicit column is far easier to validate.

The recognised forms are:

| Pattern in `Note`        | Extracted `fuel` |
|--------------------------|------------------|
| `output_fuel=Biodiesel`  | `Biodiesel`      |
| `output_fuel=Ethanol`    | `Ethanol`        |
| `fuel=Biogas`            | `Biogas`         |
| `Fuel = Wood Pellets`    | `Wood Pellets`   |

Anything else in `Note` is preserved verbatim — extraction is read-only.

---

## 7. Confidence levels

The `Confidence` column is opaque to the pipeline; it flows through into
`data_confidence` for traceability. The current CSV uses four discrete
values (counts in the 599-row source):

| Confidence  | Rows | Typical meaning                                   |
|-------------|------|---------------------------------------------------|
| `High`      |   71 | Calibrated against a measured per-AMS dataset     |
| `Medium-High`|  77 | Modelled with cross-validated assumptions         |
| `Medium`    |  288 | Engineering estimate / TEA-literature blend       |
| `Low`       |   63 | Single-source or analyst extrapolation            |

> The injector and audit do not currently filter on confidence, but the
> column is available for downstream reporting (e.g. weighting RAS
> backstop strength by data confidence).

---

## 8. What the adapter does **not** do

To set expectations correctly: the adapter is intentionally minimal.
These transformations are *not* applied — if you need any of them, do
them upstream in your authoring pipeline:

- **Unit conversion.** Author-side units are preserved verbatim in
  `unit`. The conversion happens later in
  [run_workflow.py](run_workflow.py) step 4 (`apply_audit_conversions`).
- **Expression rewriting.** `Expression` flows through unchanged; we do
  not normalise `Interp` arguments, fix typos, or sort year-value pairs.
- **Branch validation.** The adapter does not check whether
  `Branch Path` actually exists in LEAP. That happens in the injector
  (`inject_to_leap.py`) when it looks the branch up in the live tree.
- **Variable validation.** Same — unknown variable names are caught in
  the injector, not here.
- **De-duplication.** If the source CSV has two rows with the same
  `(branch, variable, region)` triple, both will be carried into the
  canonical CSV and the injector will overwrite the earlier write.

---

## 9. Authoring template — preferred shape for the next CSV

If you want to skip the adapter entirely, write your next CSV with
**these column headers and these conventions**:

```
ams,branch,variable,expression,unit,fuel,source,note,domain,data_confidence
```

Per-row rules:

- `ams` — one of the 10 LEAP short-form names (§3). One row per AMS;
  no `All 10 AMS` shorthand.
- `branch` — exact backslash-separated LEAP branch path.
- `variable` — exact LEAP variable name.
- `expression` — LEAP expression, double-quoted if it contains a comma.
- `unit` — your author-side unit string.
- `fuel` — output fuel name (e.g. `Biodiesel`), or empty.
- `source`, `note`, `domain`, `data_confidence` — provenance, free text.

A canonical-shape CSV can be dropped straight into the workflow by
renaming it to `canonical_leap_inputs.csv` (or by skipping
`build_canonical.py` in `run_workflow.py`).

---

## 10. Verifying your CSV against LEAP

After authoring, run:

```
python mailbox/bioenergy/run_workflow.py
```

This will (1) call the adapter to produce
[canonical_leap_inputs.csv](canonical_leap_inputs.csv), (2) probe LEAP
for the per-branch units, (3) audit the canonical rows against LEAP, and
(4) emit `canonical_leap_native.csv` ready for injection. Any rows that
the audit cannot auto-convert will appear with `unit_audit` starting
`MISMATCH unresolved` in the native CSV — those need a manual factor in
the `OVERRIDES` dict at the top of `run_workflow.py`.

---

---

## 11. Unit-audit outcomes against `aeo9_v0.33_bak`

> **Historical note (2026-04-29):** §11 records audit findings from a
> canonical state that still included the land-cap tier (Cultivation
> Processes, Arable, Perennial). Under the current single-cap design
> (§0), all bucket-A rows below referencing `Bioenergy Land\`,
> `Crop Cultivation\`, or per-crop `Cultivation\Auxiliary Fuels\` are
> **out of scope** — they no longer appear in the canonical and the
> path-rebase actions for them no longer apply. Bucket-B items (B.1–B.5)
> and §11.2 unit conversions remain authoritative for the remaining
> Resource + Process tier.

Running `nemo_read-leap-units --canonical` followed by
`audit_canonical_units` against `aeo9_v0.33_bak` produced 95 distinct
`(branch, variable)` pairs. The breakdown:

| Status         | Count | Meaning                                                   |
|----------------|-------|-----------------------------------------------------------|
| `match`        |   18  | Author unit ≡ LEAP unit, no conversion needed             |
| `mismatch`     |   25  | Different unit, conversion factor proposed (see §11.2)    |
| `likely_match` |    3  | Token-overlap match, **needs author review** (§11.3)      |
| `no_leap_unit` |   49  | Branch missing in the LEAP area (§11.1)                   |

**Zero unresolved mismatches** — every dimensional difference between
the author's units and LEAP's units now has a published conversion
factor in `nemo_read.unit_conversions._REGISTRY`.

### 11.1 Branches not found in `aeo9_v0.33_bak` (20 distinct paths)

The audit ran against a full `tree_paths.csv` probe (5,298 LEAP branches
in `aeo9_v0.33_bak`) and split the 20 distinct missing branches into
**three buckets** based on the smart-analysis layer
(`suggest_closest_branches` + `infer_fuel_from_consumers`):

#### A. **CSV-side path errors** — branch DOES exist in LEAP under a different name (15 branches)

These are not "missing branches" — they're authoring errors. The
**Action** column gives the exact path the canonical CSV should use.

| Canonical path                                                                                 | LEAP-side actual path                                                                          | Detection            | Action — replace canonical path with                                                |
|------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|----------------------|--------------------------------------------------------------------------------------|
| `Resources\Primary\POME`                                                                       | `Resources\Primary\Palm Oil Mill Effluent`                                                     | acronym_expansion    | `Resources\Primary\Palm Oil Mill Effluent`                                          |
| `Resources\Primary\Bioenergy Land\Arable`                                                      | `Resources\Primary\Arable`                                                                     | same_leaf            | `Resources\Primary\Arable` (drop the `Bioenergy Land\` middle level)                |
| `Resources\Primary\Bioenergy Land\Perennial`                                                   | `Resources\Primary\Perennial`                                                                  | same_leaf            | `Resources\Primary\Perennial` (drop the `Bioenergy Land\` middle level)             |
| `Transformation\Crop Cultivation\Processes\Palm Oil Cultivation`                               | `Transformation\Palm Oil Cultivation` (each crop is its own top-level Tech)                     | manual verification  | `Transformation\Palm Oil Cultivation`                                               |
| `Transformation\Crop Cultivation\Processes\Coconut Cultivation`                                | `Transformation\Coconut Cultivation`                                                            | manual verification  | `Transformation\Coconut Cultivation`                                                |
| `Transformation\Crop Cultivation\Processes\Sugarcane Cultivation`                              | `Transformation\Sugarcane Cultivation`                                                          | manual verification  | `Transformation\Sugarcane Cultivation`                                              |
| `Transformation\Crop Cultivation\Processes\Cassava Cultivation`                                | `Transformation\Cassava Cultivation`                                                            | manual verification  | `Transformation\Cassava Cultivation`                                                |
| `Transformation\Crop Cultivation\Processes\Corn Cultivation`                                   | `Transformation\Corn Cultivation`                                                               | manual verification  | `Transformation\Corn Cultivation`                                                   |
| `…\Palm Oil Cultivation\Auxiliary Fuels\Bioenergy Land - Perennial`                            | `Transformation\Palm Oil Cultivation\Auxiliary Fuels\Perennial`                                 | manual verification  | drop `Bioenergy Land - ` prefix on the leaf; rebase under per-crop top-level Tech    |
| `…\Coconut Cultivation\Auxiliary Fuels\Bioenergy Land - Perennial`                             | `Transformation\Coconut Cultivation\Auxiliary Fuels\Perennial`                                  | manual verification  | same                                                                                 |
| `…\Sugarcane Cultivation\Auxiliary Fuels\Bioenergy Land - Arable`                              | `Transformation\Sugarcane Cultivation\Auxiliary Fuels\Arable`                                   | manual verification  | same                                                                                 |
| `…\Cassava Cultivation\Auxiliary Fuels\Bioenergy Land - Arable`                                | `Transformation\Cassava Cultivation\Auxiliary Fuels\Arable`                                     | manual verification  | same                                                                                 |
| `…\Corn Cultivation\Auxiliary Fuels\Bioenergy Land - Arable`                                   | `Transformation\Corn Cultivation\Auxiliary Fuels\Arable`                                        | manual verification  | same                                                                                 |
| `Transformation\Biodiesel Production\Processes\FAME Biodiesel\Auxiliary Fuels\Biodiesel`       | `Resources\Secondary\Biodiesel`                                                                | same_leaf            | `Resources\Secondary\Biodiesel` (the canonical row points to a non-existent auxiliary; the actual fuel resource is in Secondary) |
| `Transformation\Biodiesel Production\Processes\CME Biodiesel\Feedstock Fuels\Coconut Oil`      | `Resources\Primary\Coconut Oil` (the same resource Palm Oil already uses)                      | same_leaf            | likely a missing LEAP-side branch — the parent `…\CME Biodiesel\Feedstock Fuels\` exists but lacks a `Coconut Oil` child; **add in LEAP**     |

> **Three distinct patterns** in bucket A:
>
> 1. **Acronym contraction** — author abbreviated a long LEAP name
>    (`POME` for `Palm Oil Mill Effluent`).
> 2. **Path-structure drift** — author inserted an intermediate level
>    (`Bioenergy Land\`) or used a hyphenated leaf (`Bioenergy Land -
>    Arable`) where LEAP keeps the leaf bare.
> 3. **Wrong containing folder** — author placed each crop under a
>    shared `Crop Cultivation_\Processes\` parent, but LEAP actually
>    keeps each cultivation as its own top-level Tech under
>    `Transformation\` (verified manually in LEAP, 2026-04-29). The
>    earlier `path_fuzzy` suggestion pointing to `Crop Cultivation_`
>    was a false trail — that subtree exists in LEAP but isn't where
>    the cultivation processes live.

#### B. **Truly LEAP-missing** — branch is absent; CSV owner fills the template, we create via COM (5 branches)

The pipeline can create these in LEAP automatically via the COM API
(`Branches.Add()` / `Fuels.Add()`) once the CSV owner supplies the
required metadata. The dry-run/apply two-step lives in
`create_missing_branches()` (see §11.7 for the runner).

For each truly-missing branch below, **fill the placeholder fields and
send back to the pipeline owner.** Any blank field will block creation
of that one branch (other branches still proceed).

##### B.1 — `Transformation\Bioethanol Production\Processes\Cellulosic Rice Straw`

```yaml
parent_path:    Transformation\Bioethanol Production\Processes
leaf_name:      Cellulosic Rice Straw
branch_type:    Process                       # fixed — sibling of Corn Ethanol etc.
output_fuel:    Ethanol                       # fixed — bioethanol process
feedstock_fuel: <FILL: Resources\Primary\Rice Straw>   # depends on B.4
process_lifetime_yr:  <FILL: e.g. 25>
first_year_active:    <FILL: e.g. 2030 — when commercialisation expected>
notes:                <optional free text>
```

Sibling reference rows that already work (copy variable structure from
these): `Corn Ethanol`, `Cassava`, `Molasses` under
`Bioethanol Production\Processes\`.

##### B.2 — `…\Sugarcane\Feedstock Fuels\Sugarcane`

Full path: `Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels\Sugarcane`

```yaml
parent_path:    Transformation\Bioethanol Production\Processes\Sugarcane\Feedstock Fuels
leaf_name:      Sugarcane
branch_type:    Feedstock Fuel               # fixed — fuel-reference node
fuel_reference: Resources\Primary\Sugarcane  # already exists in LEAP
fuel_share:     <FILL: e.g. 1.0 (100% sugarcane) or fraction if blended>
efficiency:     <FILL: e.g. 0.45 — process conversion efficiency, optional>
notes:          <optional>
```

##### B.3 — `…\Cassava\Feedstock Fuels\Cassava`

Full path: `Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels\Cassava`

```yaml
parent_path:    Transformation\Bioethanol Production\Processes\Cassava\Feedstock Fuels
leaf_name:      Cassava
branch_type:    Feedstock Fuel
fuel_reference: Resources\Primary\Cassava    # already exists in LEAP
fuel_share:     <FILL: e.g. 1.0>
efficiency:     <FILL: optional>
notes:          <optional>
```

##### B.4 — `Resources\Primary\Rice Straw`

```yaml
parent_path:    Resources\Primary
leaf_name:      Rice Straw
branch_type:    Primary Resource
fuel_name:      Rice Straw                   # also added to global Fuels list
                                             # if not already present
fuel_units:     <FILL: e.g. tonne — mass-based for biomass>
lhv_gj_per_t:   <FILL: e.g. 12.5 — needed for any USD/t↔USD/GJ conversions>
import_allowed: <FILL: yes/no>
export_allowed: <FILL: yes/no>
default_supply_curve: <FILL: empty or "Interp(2025, 0, 2030, 5, …)" Mt/yr>
notes:          <optional>
```

##### B.5 — `Resources\Primary\Used Cooking Oil`

```yaml
parent_path:    Resources\Primary
leaf_name:      Used Cooking Oil
branch_type:    Primary Resource
fuel_name:      Used Cooking Oil             # also added to global Fuels list
fuel_units:     <FILL: e.g. tonne>
lhv_gj_per_t:   <FILL: e.g. 37 — UCO LHV is close to refined oils>
import_allowed: <FILL: yes/no>
export_allowed: <FILL: yes/no>
default_supply_curve: <FILL: empty or e.g. Mt/yr per AMS>
notes:          <optional>
```

##### Field reference

| Field                 | Used by                  | What it maps to in LEAP                            |
|-----------------------|--------------------------|----------------------------------------------------|
| `parent_path`         | all                      | The existing branch under which the new node attaches; verified before creation |
| `leaf_name`           | all                      | The new node's `Name`                              |
| `branch_type`         | all                      | LEAP `BranchType` integer (lookup: Process=23, Primary Resource=12, Feedstock Fuel=58 — package handles the mapping) |
| `output_fuel`         | Process                  | The fuel produced by the process (must already exist in `Resources\Secondary\` or be created) |
| `feedstock_fuel`      | Process                  | Optional — the input fuel reference; auto-creates the `\Feedstock Fuels\X` child |
| `fuel_reference`      | Feedstock Fuel           | Existing fuel branch path the reference points at  |
| `fuel_share`          | Feedstock Fuel           | LEAP variable: process feedstock fuel share        |
| `efficiency`          | Feedstock Fuel / Process | Optional initial value for `Process Efficiency`    |
| `process_lifetime_yr` | Process                  | LEAP variable: `Lifetime`                          |
| `first_year_active`   | Process                  | LEAP variable: `First Year`                        |
| `fuel_name`           | Primary Resource         | Name added to LEAP global `Fuels` list             |
| `fuel_units`          | Primary Resource         | LEAP fuel unit (`tonne`, `GJ`, `bbl`, etc.)        |
| `lhv_gj_per_t`        | Primary Resource         | LHV in GJ/tonne — also added to `nemo_read.unit_conversions` for USD/t↔USD/GJ |
| `import_allowed`      | Primary Resource         | Sets the `Import Cost` branch eligibility          |
| `export_allowed`      | Primary Resource         | Sets the `Export Cost` branch eligibility          |
| `default_supply_curve`| Primary Resource         | Initial `Maximum Production` Interp expression     |

#### C. **Consumer-process inference** (3 confirmations of bucket A above)

The `infer_fuel_from_consumers()` analysis cross-checked bucket A
findings by walking `…\Processes\<X>\Feedstock Fuels\<Y>` paths to
recover the LEAP-side fuel name. All three hits agreed with the
acronym/same-leaf detections:

| Missing canonical path                       | Inferred LEAP-side fuel name | Found in (consumer process)                                                            |
|---------------------------------------------|------------------------------|----------------------------------------------------------------------------------------|
| `Resources\Primary\POME`                    | `Palm Oil Mill Effluent`     | `Transformation\Biodiesel Production\Processes\POME Biodiesel\Feedstock Fuels\…`      |
| `Resources\Primary\Bioenergy Land\Arable`   | `Arable`                     | `Transformation\Cassava Cultivation\Processes\Cassava Cultivation\Feedstock Fuels\…`  |
| `Resources\Primary\Bioenergy Land\Perennial`| `Perennial`                  | `Transformation\Coconut Cultivation\Processes\Coconut Cultivation\Feedstock Fuels\…`  |

> **Operational summary:**
> Of 20 "missing" branches, **15 are CSV-side path errors fixable now**
> (bucket A) and **5 need LEAP-side additions** (bucket B). After
> applying bucket A fixes, the no_leap_unit count drops from 49 to ~10
> rows and the path mappings are deterministic — no fuzzy matching
> required at injection time.

### 11.2 Mismatch families and the conversions now applied

The 25 mismatches collapse to **15 distinct unit-pair families**, each
covered by an entry in `nemo_read.unit_conversions._REGISTRY` (added in
this audit cycle).

| Variable           | Author unit            | LEAP unit                                  | Factor    | ★ | Why                                                |
|--------------------|------------------------|--------------------------------------------|-----------|---|----------------------------------------------------|
| Capital Cost       | `USD/GJ`               | `2020 USD/Gigajoules/Year`                 | `1.0`     | 3 | LEAP capital-cost convention; `/Year` is annual capacity, not duration |
| Capital Cost       | `USD/GJ`               | `2020 USD/Tonne Coal Equiv/Year`           | `29.3076` | 4 | 1 TCE = 29.3076 GJ (IEA); same `/Year` convention  |
| Import Cost        | `USD/t fresh root`     | `2020 USD/Metric Tonne`                    | `1.0`     | 5 | Same physical tonne; commodity tag is descriptive  |
| Import Cost        | `USD/t nuts-in-shell`  | `2020 USD/Metric Tonne`                    | `1.0`     | 5 | Same physical tonne; commodity tag is descriptive  |
| Import Cost        | `USD/t FFB`            | `2020 USD/Metric Tonne`                    | `1.0`     | 5 | Same physical tonne; commodity tag is descriptive  |
| Import Cost        | `USD/t cane`           | `2020 USD/Metric Tonne`                    | `1.0`     | 5 | Same physical tonne; commodity tag is descriptive  |
| Production Cost    | `USD/t molasses`       | `2020 USD/Metric Tonne`                    | `1.0`     | 5 | Same physical tonne; commodity tag is descriptive  |
| Import Cost        | `USD/t grain`          | `2020 USD/Tonnes of Coal Equivalent`       | `2.0074`  | 3 | Corn grain LHV 14.6 GJ/t (IPCC) → 29.3076/14.6     |
| Fuel Cost          | `USD/t grain`          | `U.S. Dollar/Tonnes of Coal Equivalent`    | `2.0074`  | 3 | Corn grain LHV 14.6 GJ/t (IPCC) → 29.3076/14.6     |
| Fuel Cost          | `USD/t FFB`            | `U.S. Dollar/Gigajoule`                    | `0.1667`  | 2 | Palm FFB LHV ≈ 6 GJ/t wet basis (MPOB/IRENA)       |
| Fuel Cost          | `USD/t nuts-in-shell`  | `U.S. Dollar/Gigajoule`                    | `0.0741`  | 2 | Coconut nuts LHV ≈ 13.5 GJ/t (FAO)                 |
| Fuel Cost          | `USD/t cane`           | `U.S. Dollar/Gigajoule`                    | `0.1333`  | 2 | Sugarcane wet LHV ≈ 7.5 GJ/t (FAO bagasse-blend)   |
| Fuel Cost          | `USD/t fresh root`     | `U.S. Dollar/Gigajoule`                    | `0.2857`  | 2 | Cassava fresh root LHV ≈ 3.5 GJ/t (IRENA)          |
| Maximum Capacity   | `Million Tonnes/yr`    | `Million Gigajoules/Year`                  | `37.0`    | 4 | Biodiesel (FAME) LHV 37 GJ/t (IPCC default)        |
| Maximum Capacity   | `Million Tonnes/yr`    | `Million Tonne Coal Equiv/Year`            | `0.9144`  | 4 | Ethanol LHV 26.8 GJ/t / TCE 29.3076 = 0.9144       |

Confidence stars (rubric in `nemo_read/unit_conversions.py`):

> ★★★★★ exact SI/NIST/ISO definition  · ★★★★ international standard,
> negligible variance  · ★★★ published default with material variance
> (~±10%)  · ★★ regional/proxy default, significant variance (~±25%)
> · ★ best-guess

The ★★ Fuel Cost rows for FFB / nuts-in-shell / cane / fresh root carry
the most uncertainty — see `caveat` field in the audit output for the
expected variance band per feedstock.

### 11.3 `likely_match` rows that need author review (3 rows)

These rows resolved as token-overlap matches but the unit dimensionality
**does not actually match** — the author wrote a unit with no
denominator where LEAP expects a per-unit price:

| Branch                            | Variable    | Author unit | LEAP unit               |
|-----------------------------------|-------------|-------------|-------------------------|
| `Resources\Secondary\Ethanol`     | Import Cost | `2020 USD`  | `2020 USD/Liter`        |
| `Resources\Secondary\Biodiesel`   | Import Cost | `2020 USD`  | `2020 USD/Liter`        |
| `Resources\Secondary\Methanol`    | Import Cost | `2020 USD`  | `2020 USD/Metric Tonne` |

**Action for the CSV owner:** check whether the `Expression` values on
these 3 rows are already in the LEAP-expected unit (USD/L for ethanol &
biodiesel, USD/t for methanol) and update the `Units` column to match.
If the values are actually USD-only (totals or aggregates), they should
not live in a per-unit `Import Cost` field at all — the row needs to be
reformulated.

### 11.4 New behaviour: branch-path fuel inference

`build_canonical.py` was updated during this audit cycle to extract
output-fuel context from the **branch path** when the `Note` field does
not contain an explicit `output_fuel=...` token. The rules are:

| If the branch contains       | `fuel` is set to |
|------------------------------|------------------|
| `Biodiesel Production`       | `Biodiesel`      |
| `Bioethanol Production`      | `Ethanol`        |

Effect: `Maximum Capacity` rows (which lack `output_fuel=` in their
Note) now resolve to the 4★ fuel-specific conversion proposals rather
than the 1★ unit-pair fallback. Total rows with a populated `fuel`
column climbed from **190 → 530 of 950**.

The explicit `output_fuel=` token in `Note` always wins over the
branch-path heuristic, so authors retain full control.

### 11.5 How the smart-analysis layer works (for future audits)

`audit_canonical_units` exposes two columns on `no_leap_unit` rows:

**`branch_suggestion`** — up to 3 closest LEAP branches with reason
tags, ranked by detection strength:

- `(sibling)` — same parent path, fuzzy leaf-name match
- `(same_leaf)` — different parent, identical leaf name
- `(restructured)` — same root segment + same leaf, different
  intermediate path (catches `A\B\C\Leaf` → `A\Leaf`)
- `(acronym_expansion)` — leaf is an initial-letter acronym of an
  existing LEAP leaf (catches `POME` → `Palm Oil Mill Effluent`,
  `UCO` → `Used Cooking Oil`, `FFB` → `Fresh Fruit Bunches`)
- `(path_fuzzy)` — full-path Levenshtein last resort (catches typos
  and `Crop Cultivation` vs `Crop Cultivation_`)

**`consumer_fuel_hint`** — for missing `Resources\Primary\X` and
`Resources\Secondary\X` rows, walks `…\Processes\<X>\Feedstock Fuels\<Y>`
paths to discover the LEAP-side fuel name `<Y>` from a consumer process
that names itself after the missing fuel. Independent confirmation of
acronym/same-leaf hits from above.

The richness of suggestions depends on the LEAP-side **path universe**
the audit can see:

- **Best**: re-run `nemo_read-leap-units --canonical canonical_leap_inputs.csv`
  with the target area open; the probe writes a new `tree_paths.csv`
  containing every branch in the LEAP tree (~5,000+ paths in an
  AEO9-sized area). All five reason types fire.
- **Fallback**: when `tree_paths.csv` is absent, the audit falls back to
  `branch_variable_units.csv`'s `branch_full_name` column (~67 paths).
  Suggestions degrade — only `(sibling)`/`(same_leaf)` fire reliably,
  and `(acronym_expansion)` won't find expansions for fuels that were
  never probed.

### 11.6 Missing-fuel detection in the audit

`audit_canonical_units` now adds a `fuel_advice` column. It fires when
a row's mismatch resolves via a fuel-agnostic fallback registry entry
*and* a higher-confidence fuel-keyed alternative exists for the same
unit pair. The advice text names the eligible fuels:

> `add output_fuel context to lift confidence (known: biodiesel)`

For the **current bioenergy canonical**, the column is empty for every
row — the branch-path inference in `build_canonical.py` (§11.4)
already populates `fuel` correctly for all rows whose unit pair has
a fuel-keyed entry. **Validation:** running the audit with `fuel`
forced to empty produces 7 fuel_advice rows (the 6 process Maximum
Capacity rows + 1 — biodiesel/ethanol), all flagged with confidence=1
and pointed at the correct alternative.

Cases where fuel_advice would surface in future CSVs:

1. A new process whose Note doesn't include `output_fuel=...` and
   whose branch path doesn't match the `Biodiesel Production` /
   `Bioethanol Production` heuristics in `_extract_fuel`. Fix: add an
   explicit `output_fuel=X` token in Note.
2. A new fuel that isn't yet registered. Fix: extend `_BRANCH_FUEL_RULES`
   in `build_canonical.py` *and* add a fuel-keyed registry entry in
   `nemo_read.unit_conversions`.

### 11.7 Author-then-create workflow (for the truly-missing branches)

The full sequence to take this audit from "20 issues found" to "0
issues, all rows injected" is:

**Step 1 — Apply bucket A path fixes in the source CSV** (you, the
CSV owner). The 15 corrections in §11.1 are pure string replacements
in `bioenergy_leap_input.csv`:

```
Resources\Primary\POME                                              → Resources\Primary\Palm Oil Mill Effluent
Resources\Primary\Bioenergy Land\Arable                             → Resources\Primary\Arable
Resources\Primary\Bioenergy Land\Perennial                          → Resources\Primary\Perennial
Transformation\Crop Cultivation\…                                   → Transformation\Crop Cultivation_\…       (add underscore)
…\Auxiliary Fuels\Bioenergy Land - Arable                           → …\Auxiliary Fuels\Arable                  (drop prefix)
…\Auxiliary Fuels\Bioenergy Land - Perennial                        → …\Auxiliary Fuels\Perennial               (drop prefix)
…\FAME Biodiesel\Auxiliary Fuels\Biodiesel                          → Resources\Secondary\Biodiesel
```

After step 1, re-run the workflow:

```
python mailbox/bioenergy/run_workflow.py
```

The audit should drop from 49 → ~10 no_leap_unit rows (only the
bucket B truly-missing branches remain).

**Step 2 — Fill bucket B creation templates** (you, the CSV owner).
Send back the 5 filled YAML blocks from §11.1 (B.1–B.5). Each block
takes ~1 minute to fill.

**Step 3 — We run `create_missing_branches()` via LEAP COM**
(pipeline owner). The runner does:

1. **Dry-run pass** — prints exactly what would be created (parent
   path → child + branch_type + initial values), no LEAP write.
2. You confirm the dry-run output looks right.
3. **Apply pass** — calls `Branches.Add()` and (where needed)
   `Fuels.Add()` for each entry. Save LEAP after, verify the new
   branches appear in the tree.
4. Re-probe + re-audit. Now `no_leap_unit` should be 0 and the
   workflow can inject all rows.

**Why two passes:** branch creation is structural (persisted to disk)
and irreversible without manual cleanup in the LEAP UI. The dry-run
gate protects against typos in `parent_path` or wrong `branch_type`
values that would leave orphan nodes.

**Why fuel-then-resource ordering:** for each bucket B Primary
Resource, the global Fuels list entry is created first (`Fuels.Add()`),
then the resource branch is created and bound to that fuel. If the
fuel already exists in LEAP, the runner skips the `Fuels.Add()` step.

> **Status today:** the runner is not yet built — this guide is the
> spec. When you return the filled bucket B blocks, the next session
> turns them into a runnable
> `python mailbox/bioenergy/create_missing_branches.py --dry-run`,
> reviews the output with you, then applies.

### 11.8 What this means for future bioenergy CSVs (general guidance)

When you author the next revision, you can drop most adapter
intervention by following these rules:

1. **Use LEAP-native units directly when feasible.** Capital Cost,
   Maximum Capacity, and Fuel Cost on the bioethanol/biodiesel processes
   want energy-based units; converting at source removes one star of
   uncertainty per row.
2. **Or keep your current units** — every commodity-tagged tonne unit
   (`USD/t FFB`, `USD/t fresh root`, etc.) is now in the conversion
   registry, so the audit will resolve them automatically.
3. **For new feedstocks not yet in the registry**, send the LHV (GJ/t)
   alongside the new CSV so we can extend the registry before injection.
4. **Add `output_fuel=` explicitly in the `Note`** for any process row
   whose output isn't biodiesel or ethanol (e.g. methanol, biogas,
   wood-pellets) — the branch-path heuristic only handles those two
   cases.
5. **Don't author bare `2020 USD` units** on a price column — LEAP
   always expects USD per *something*.

After step 1–5, re-running `python mailbox/bioenergy/run_workflow.py`
should show every row in `match` or auto-resolved `mismatch` status.

---

## 12. Unit reconciliation — what LEAP expects (authoritative, dated 2026-04-29)

LEAP is the single source of truth for units. Every (branch, variable)
combination in canonical has a `Variable.DataUnitText` exposed via
COM — that's what the row's value gets stored as at injection time.
The `audit_canonical_units` step reads that text per pair and compares
against your authored unit. Anything that doesn't match LEAP needs to
be either (a) auto-converted by `nemo_read.unit_conversions._REGISTRY`,
(b) fixed by the author at the source, or (c) excluded.

This section organises the audit's findings by **author action**.
Re-run `python mailbox/bioenergy/run_workflow.py` after authoring to
regenerate [unit_audit.csv](unit_audit.csv) — that file is the
up-to-the-minute snapshot; this section is the human-facing summary.

### 12.1 Author-action required (0 remaining — all 7 applied)

> **Status (final, 2026-04-29):** All 7 originally-flagged mismatches
> have been applied directly to [bioenergy_leap_input.csv](bioenergy_leap_input.csv).
> Each affected row carries a `[2026-04-29 §12.1 author-action applied]`
> marker in its `note` column for traceability (70 rows total — 7
> distinct (branch, variable) pairs × 10 AMS each).

| # | Branch | Variable | Final unit | Conversion applied |
|---|---|---|---|---|
| 1 | `Resources\Primary\Palm Oil` | Maximum Production | `Metric Tonne` | × 1e6 (was `Million Tonnes/yr`) |
| 2 | `Resources\Primary\Coconut Oil` | Maximum Production | `Metric Tonne` | × 1e6 |
| 3 | `Resources\Primary\Sugarcane` | Maximum Production | `Metric Tonne` | × 1e6 |
| 4 | `Resources\Primary\Cassava` | Maximum Production | `Metric Tonne` | × 1e6 |
| 5 | `Resources\Primary\Corn` | Maximum Production | `Metric Tonne` | × 1e6 (after LEAP-side unit corrected from `Gigajoule` to `Metric Tonne` to eliminate the Corn anomaly) |
| 6 | `Resources\Primary\Corn` | Production Cost | `2020 USD/Metric Tonne` | LEAP-side unit shifted Kilogramme → Metric Tonne mid-cycle; final values in USD/t magnitudes |
| 7 | `Resources\Primary\Palm Oil Mill Effluent` | Production Cost | `2020 USD/Tonnes of Oil Equivalent` | × `(POME-oil LHV / 41.868)` ≈ × 0.872 (POME-oil LHV ≈ 36.5 GJ/t per author derivation) |

§12.1 is closed. Future unit-mismatch flags from `audit_canonical_units`
that don't have a registered conversion factor list themselves here for
the next author-action cycle.

### 12.2 Auto-handled mismatches (29 distinct, ~290 rows after AMS expansion)

These mismatches **don't need author action** — the audit pipeline
applies the conversion factor automatically at inject time via
[nemo_read/unit_conversions.py](../../nemo_read/unit_conversions.py)
`_REGISTRY`. But if you want a `match`-only canonical (zero conversions
applied), update the source to use LEAP-native units directly.

Reference table (full list in §11.2; key entries reproduced here):

| Variable | Author unit | LEAP unit | Auto-factor | Notes |
|---|---|---|---|---|
| Capital Cost (Biodiesel) | `USD/GJ` | `2020 USD/Gigajoules/Year` | 1.0 | LEAP `/Year` = annual capacity, not duration |
| Capital Cost (Bioethanol) | `USD/GJ` | `2020 USD/Tonne Coal Equiv/Year` | 29.3076 | TCE = 29.3076 GJ |
| Maximum Capacity (Biodiesel) | `Million Tonnes/yr` | `Million Gigajoules/Year` | 37.0 | Biodiesel LHV 37 GJ/t |
| Maximum Capacity (Bioethanol) | `Million Tonnes/yr` | `Million Tonne Coal Equiv/Year` | 0.9144 | Ethanol LHV 26.8 / TCE 29.3076 |
| Production Cost (5 crops) | `USD/t <feedstock>` | `2020 USD/Metric Tonne` | 1.0 | Same physical tonne; commodity tag is descriptive only |
| Import Cost (4 crops) | `USD/t <feedstock>` | `2020 USD/Metric Tonne` | 1.0 | Same |
| Import Cost (Corn) | `USD/t grain` | `2020 USD/Tonnes of Coal Equivalent` | 2.0074 | Corn LHV 14.6 GJ/t / TCE 29.3076 |
| Fuel Cost (per crop) | `USD/t <feedstock>` | `U.S. Dollar/Gigajoule` | crop-specific (LHV) | Per-crop LHV — see §11.2 |

### 12.3 Branches to exclude from authoring (LEAP-missing, build-time skipped)

These branches don't exist in LEAP (`aeo9_v0.33_bak` as of 2026-04-29).
Until they're created (per §11.B templates), the author should **not
include them in the next CSV** — and `build_canonical.py` filters them
defensively via the `LEAP_MISSING_BRANCHES` constant.

| Branch | Where to create in LEAP | Filter section |
|---|---|---|
| `Resources\Primary\Rice Straw` | §11.B.4 — Primary Resource template | `LEAP_MISSING_BRANCHES` |
| `Resources\Primary\Used Cooking Oil` | §11.B.5 — Primary Resource template | `LEAP_MISSING_BRANCHES` |
| `Transformation\Bioethanol Production\Processes\Cellulosic Rice Straw` | §11.B.1 — Process template | `LEAP_MISSING_BRANCHES` |

When the LEAP branches are created, drop the corresponding entries from
`LEAP_MISSING_BRANCHES` in [build_canonical.py](build_canonical.py)
and re-run.

### 12.4 Variables deferred — out of scope this cycle (cluster 3)

These (branch, variable) patterns appear in the source CSV but LEAP
doesn't expose the variable on that branch. They're filtered at build
time via `_is_deferred()` in [build_canonical.py](build_canonical.py)
and held until the placement is corrected. **Don't include these in the
next CSV** without first deciding where they should live in LEAP.

| Pattern | Distinct rows × 10 AMS | Issue | Suggested resolution (deferred) |
|---|---|---|---|
| Emission factors (`CO2 (process)`, `CH4 (process)`, `N2O (process)`, `NH3 (process)`, `NOx (process)`, `SO2 (process)`, `NMVOC (process)`) on `\Feedstock Fuels\<crop>` sub-branches | 20 × 10 = 200 | LEAP doesn't expose emission-factor variables on `Feedstock Fuels` sub-branches | Move to parent Process branch (`…\<X> Biodiesel` or `…\<X> Ethanol`) where LEAP exposes per-process emission factors |
| `CO2 biogenic` on `Resources\Secondary\Biodiesel` | 1 × 10 = 10 | LEAP doesn't expose `CO2 biogenic` on a Secondary Resource | Likely belongs on the producing Process branch (FAME / CME / POME Biodiesel); confirm with LEAP UI inspection before relocating |

When the cluster is reopened: probe the candidate target branches first
(via `python mailbox/bioenergy/_list_branch_vars.py "<target branch>"`)
to confirm they expose the emission-factor variables, then relocate the
authoring and remove the deferred filter.

---

*Generated to mirror the behaviour of `build_canonical.py` and the
audit cycle as of nemo_read 0.6.4 against `aeo9_v0.33_bak`. If you
change the adapter or extend the conversion registry, please update
this guide in the same commit.*
