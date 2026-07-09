# Power send-back authoring guide (for the LEAP injection team)

**Version 1 · 2026-07-04 · baselined on canon `aeo9_v0.67_w_results`**

This is how the Power sector formats data it sends back for injection into LEAP.
It mirrors the canon's own `CSV_AUTHORING_GUIDE.md` so every row we hand over lines
up with the live structure exactly, spellings included. Power authors the two generation modules,
`Transformation\Centralized Electricity Generation` and `Transformation\Distributed
Electricity Generation` (Solar PV Rooftop); other trees come from other teams.

## 1. File schema

One row per (branch, variable, scenario, region, value or series). Columns:

| Column | Meaning |
|---|---|
| `branch_path` | Full LEAP path, backslash-separated, exactly as in `transformation_slice_tree.txt`. |
| `variable` | Variable name exactly as exported, including any intentional typo or `!` prefix. |
| `scenario` | One of the four (see §3). |
| `region` | LEAP short region name (see §2). |
| `expression` | The LEAP expression (see §4). |
| `units`, `scale`, `per` | Copied from the canon unit slice for that branch×variable; do not invent units. |
| `source` | Provenance for every row: document, year, URL where available. |

## 2. Region naming (short-name exception)

Use LEAP's short region strings, because LEAP matches region names exactly:

- `Brunei` (not Brunei Darussalam), `Laos` (not Lao PDR), `Vietnam` (not Viet Nam).
  The other seven match the usual names.
- Sub-national variants keep the country in `region` and carry the `_IDxx` / `_MYxx`
  tag on the `branch_path` (e.g. `Gas Turbine_MYPE`).
- **Timor Leste** ships in a separate supplement file, never mixed into the
  10-country main data. It is switched out of the calculation.
- **Base Template** is a LEAP template, not a country. Never author data for it.

## 3. Scenarios

Four scenarios carry authored data; corrections to these propagate. Route each row
to the right one per its meaning:

- **Current Accounts** — current situation and historical actuals (year ≤ 2024).
- **Baseline Simulation** — business as usual, today's trajectory only.
- **AMS Target Scenario** — ASEAN member-state stated policy, held true to it.
- **Regional Aspiration Scenario** — improvement beyond policy toward a more
  sustainable system; the optimisation run.

## 4. Expression house-rules (non-negotiable)

- **`Interp(year, value, year, value, …)`** — COMMA between items, PERIOD as the
  decimal mark. `Interp(2023, 100, 2030, 80)` is right; semicolons or comma-decimals
  are rejected before import.
- **`? comment` provenance** — anything after `?` is a comment; use it to cite the
  source. `? tbc` means unconfirmed.
- **Never write the literal word `Unlimited`.** It becomes a broken sentinel
  downstream. If a generous cap is needed, use a large number.
- **Every supply cap ships with its cost.** (For Power this applies to feedstock
  and any Centralized-side cost; Resources-tree caps and their costs are the fossil
  team's.)
- **Deactivated variables keep the `!` prefix** (`!Reactance`, `!Construction
  Year`); do not author or normalise them.
- **Preserve the intentional typo** `Incumbent Generator DIspatch Phaseout` (capital
  "DI"); path lookups are case-sensitive.

## 5. Do not touch

- **`Unmet Load_*` slack processes** — keep them visible with positive Variable OM
  and Fixed OM (exactly 500 each, all 12 regions, all scenarios) so unmet demand is
  an expensive result rather than a solver failure. Do not zero or hide them. This is
  the safety net that lets the optimisation solve; it is eliminated only in the final
  iteration, once everything else is fixed.
- **`Optimized New Capacity`** — solver output, read-only; never re-author.
- **Verified-benign items** — the inert must-run trap (T3), the benign upper-bound
  Unlimited sentinel (T9), the inert Renewable Target knob (T10), and the cosmetic
  `_x000D_` comment artifacts (T11). Leave them; do not "fix" them.

## 6. Worked example row

```
branch_path,variable,scenario,region,expression,units,scale,per,source
Transformation\Centralized Electricity Generation\Processes\Gas Turbine_MYPE,Process Efficiency,Regional Aspiration Scenario,Malaysia,Interp(2025, 38, 2060, 42),Percent,,,"Danish Energy Agency, Technology Data for the Indonesian Power Sector 2024"
```

## 7. What we send, in priority order

1. The six Malaysia `_MY*` free-build generators (real costs, finite Maximum
   Capacity Addition, realistic Capacity Credit and Process Efficiency).
2. The confessed placeholders in our slice (Wind Offshore availability, in-module
   transmission capital cost).
3. Electricity Import Cost, per region and scenario.
4. Documentation of the `Bad Scenario [2]` dangling reference (issue + plan; not a
   value this cycle).

Questions → yudiandra.y@gmail.com. Reference branch paths as they appear in the
canon `.txt` trees when reporting structure issues.
