# Key\ Assumptions — Canonical LEAP Structure Handover (2026-07-03)

For the central assumptions / modeling team. You don't need our repo or
any database to use this package — everything referenced here is a plain
text/CSV file sitting next to this README. Since your team owns the
cross-cutting layer, this README is a bit more technical than the sector
handovers, but it is still self-contained.

## 1. What this package is

This is the **canonical structure** of the `Key\` assumptions tree,
exported directly from the live model (LEAP area `aeo9_v0.67_w_results`)
on 2026-07-02. It is the ground truth for branch names, variable names,
and units: 1,064 branches, 26 variables, 3,335 (branch, variable)
combinations, across 11 scenarios × 12 region slots.

Files in this package:

| File | What it is |
|---|---|
| `keys_tree.txt` | The `Key\` branch tree (1,064 variable-carrying branches), indented by depth, with each branch's variables listed. **Caveat:** the export only emits branches that carry variables, so pure container nodes (the group headers like `Annual EI Reduction`) do not appear as their own lines — use the CSVs' full `branch_path` column for orientation. |
| `keys_branch_variables_units.csv` | One row per (branch, variable): units, scale, per — the authoritative unit reference (3,335 rows) |
| `current_expressions_keys_4scenarios.csv` | **What is currently written in the model** for every `Key\` branch — the live expressions, scoped to the 4 scenarios that matter (24,142 rows; see §6b) |
| `README_KEYS_CANON_STRUCTURE.md` | This guide. |

How to read them: in the `.txt` tree, indentation = depth and the
`[vars: ...]` suffix lists the variables on that branch. In the CSVs,
`branch_path` is the full LEAP path (backslash-separated) and
`units`/`scale`/`per` together give the unit.

## 2. The tree in brief — three strata, 25 top-level groups

The `Key\` tree is not one thing. Its 1,064 branches split into three
strata with very different owners and change cadences:

| Stratum | Share | Groups |
|---|---|---|
| **NEMO plumbing** | 538 branches, 84.1% of all rows | `Optimized Trade` (495 branches: 55 region-pairs × 9 biofuel feedstock fuels — Ethanol, Biodiesel, Coconut Oil, Palm Oil, Palm Oil Mill Effluent, Cassava, Molasses, Sugarcane, Corn), `Transmission` (42: 21 interconnector `Lines\<A>_<B>_{E,F,C}` with a 13-variable panel, plus `Nodes`, `Demand Distribution`, `Transmission Enabled`), `Region Group RE Targets` (1 branch, 4-variable stub, every expression `0` — present but disabled) |
| **Sector data trees** | 450 branches | `Industry` (113), `Cal` (76 — per-fuel calibration factors incl. `Cal\Transformation` 13 and `Cal\Transport` 10, which no demand export cites), `Residential end use data_` (54), `TransportDataStock` (47), `Residential` (32), `Transport vehicle data_` (28), `Other Transport` (23 — EV charging cost stack), `Job creations` (22), `Macroeconomic` (17), `Commercial` (13), `Emission Externality Costs` (9), `Demographic` (8), `ValueAdded` (4), `Energy Access` (2), `Lighting_data` (2) |
| **Policy levers** | 75 branches | `Net Zero Measures` (31: Transport 12, Industry 10, Residential 9), `Modeling Assumptions` (16: technology lead times + the incumbent-dispatch phaseout knob), `Annual EI Reduction` (13), `Capacity Additions Multiplier` (11), `Biofuel Blending Targets` (2), `End_cap multip` (2) |

Plus one scratch node: `Key\Temp` (1 branch, units literally `temp`) —
see §7.1, it is not as inert as it looks.

The sub-national electricity node names (P. Malaysia, Sarawak, Sabah,
Sumatra, Kalimantan) appear only inside `Transmission`.

## 3. The variables you author — really one, plus plumbing panels

`Activity Level` is the only true assumption variable: it exists on all
1,064 branches, and **the unit does the typing**. Where a demand-sector
branch carries a fat panel of named variables, a Key branch carries one
`Activity Level` whose unit declares its meaning: `%`, `GJ/USD`,
`coeff`, `Vehicle`, `people/HH`, `1 or 0` (the Optimized Trade
switches), `ID`, `million $/PJ`, `Job-Years`, and so on. Always read
the unit from `keys_branch_variables_units.csv` before touching a value.

The other 25 variables are structural plumbing on two meta-trees only:

- **Optimized Trade panel** (495 branches × 5 vars): `Activity Level`
  (the on/off switch) + `Trade Region 1` / `Trade Region 2` /
  `Trade LEAP Fuel` / `Trade_NEMO Fuel` (ID-typed route definitions).
- **Transmission Lines panel** (21 branches × 13 vars): `From Node` /
  `To Node`, `Maximum Flow` (MW), `Capital Cost_` / `Fixed OM Cost_` /
  `Variable OM Cost_`, `Lifetime_`, `Efficiency_`, `Interest Rate_`,
  `Fuel__`, plus two deactivated variables exported with a `!` prefix
  (`!Reactance`, `!Construction Year` — see §7.6).
- Singleton config: `Region_`/`Node_`/`Fuel_` on Nodes and Demand
  Distribution, `Unscaled VAShare` on ValueAdded, and 5 one-off config
  variables (`Transmission Modeling Type`, `Region Group Set`, …).

62.9% of all exported rows are ID-typed plumbing (`RegionID()` /
`FuelID()` / `BranchID()`) — machine-written, not assumptions.

## 4. Expression conventions (non-negotiable)

- **`Interp(year, value, year, value, ...)`** — COMMA between items,
  PERIOD as the decimal mark. `Interp(2025, 3.2422, 2030, 3.0833)` is
  right; semicolons or comma-decimals (`3,2422`) are wrong and will be
  rejected before import.
- **`InterpFSY(year, value, ...)`** — Interp anchored at the first
  scenario year; the house style for policy targets. Live example:
  Indonesia's biodiesel blend target is
  `InterpFSY(2023, 35, 2025, 40, 2050, 50)`.
- **`? comment` provenance** — anything after `?` is a comment; the
  model's de-facto provenance layer. Please keep citing sources
  (workshop names, decree numbers, dataset vintages) and please keep
  writing placeholder confessions — §7.7/§7.8 exist because past
  authors did.
- **`Growth(...)` / `RegionValue(...)` / `ScenarioValue(...)`** — the
  cross-reference idioms sector trees use to pull from `Key\`. If you
  rename a Key branch, every consumer formula breaks silently in the
  scenario views; tell us before renaming anything.
- **Never write the literal word `Unlimited`** in anything you author —
  it becomes a broken numeric sentinel (1e12) in the downstream NEMO
  export. If something needs a generous cap, use a large number.

## 5. Scenarios and regions — where the signal actually lives

The Key export is **perfectly rectangular**: every (branch, variable)
exists in all 11 scenarios and all 12 region slots; differentiation
lives purely in the expression text. For the record, the 11 scenarios
are: Current Accounts, Baseline Simulation, Set up, AMS Target
Scenario, LCO backup, the three RE LTRM scenarios (RE LTRM ASEAN
Policy Aligned / RE LTRM ASEAN RE Coupling / RE LTRM ASEAN Shared
Energy Resources), Regional Aspiration Scenario, Carbon Neutrality_
Net Zero Scenario, and Regional Aspiration Scenario test. The scenario
logic in headline form:

- **`Key\Optimized Trade\*:Activity Level` is a per-scenario master
  switch: `1` in Regional Aspiration Scenario and Carbon Neutrality
  only, `0` in the other nine scenarios** — all 495 routes flip as one
  block. Note the scenarios that carry non-zero biofuel blend targets
  with trade disabled (AMS Target, the RE LTRM triplet): whether that
  is an infeasibility risk depends on Transformation-side wiring —
  *pending Transformation export*, we cannot verify it offline.
- **`LCO backup` is NOT a copy here.** In every demand sector it is
  expression-identical to the `Set up` bloc; in the Key tree it sits
  **273 cells off Set up** (Annual EI Reduction 132, Capacity Additions
  Multiplier 129, Clean Cooking 12). The "backup" carries its own
  driver settings.
- **The RE LTRM triplet differs by exactly 12 cells in the Key tree.**
  The four demand sectors keep the triplet byte-identical; the only
  other differentiation in the six exports is 7 cells on
  `Resources\Secondary\Ethanol:Import Cost` (country tariff variants,
  documented in the Resources canon). The 12 Key cells:
  (a) 8 cells on `Key\Biofuel Blending Targets\
  {Biodiesel, Bioethanol}` for Indonesia / Philippines / Thailand /
  Vietnam — RE Coupling and Shared Energy Resources insert a 2030
  intermediate blend point absent from Policy Aligned (e.g. Indonesia
  Biodiesel `InterpFSY(2023, 35, 2025, 40, 2050, 50)` gains
  `2030, 45`, tagged `MRK Comment: 2030 is assumption set by the
  modeller`); (b) 3 cells on `Key\Annual EI Reduction\Industry` for
  Indonesia / Thailand / Vietnam (−0.01 or 0 → −0.015 in
  Coupling/Shared); (c) 1 cell on the `Key\Temp` scratch branch — the
  single Coupling-vs-Shared difference (§7.1).
- **`Baseline Simulation` ≡ `Regional Aspiration Scenario test`**
  (zero differing cells). And Carbon Neutrality = RAS + the
  `Net Zero Measures` overlay (only 303 cells apart).

Regions: the 12 slots are the 10 ASEAN member states plus **Base
Template** (a LEAP template pseudo-region, not a country) and **Timor
Leste**. 91.5% of (branch, variable) combos are region-invariant in
every scenario; the genuinely per-region trees are `Cal`,
`TransportDataStock`, `Residential`, `Transport vehicle data_`,
`Commercial`, `Demographic`, `Macroeconomic`, `Energy Access`.
`RegionValue()` borrowing (847 rows) marks the data-poor countries —
Cambodia and Vietnam (132 rows each), Philippines (121), Laos (99),
e.g. `Key\Commercial\Energy consumption per area\Hospital` Vietnam =
`RegionValue(Laos) ? assumed similar to Singapore` (note the comment
contradicts the formula — worth a look). Timor Leste data goes in a
**separate supplement file** if you ever author it, never mixed into
the main 10-country set.

## 6. Who consumes this tree — the connection map

Of the 1,064 branches, **271 (25.5%) are referenced somewhere in the
six exported trees** (four demand sectors + Key-internal + Resources):
the four demand sectors cite 241 distinct Key branches — 239 of which
exist in the area; the 2 misses are the comment-only
`Key\Residential\AC\{a,b}` (§7.3) — with 51,917
referencing rows (Industry 112 branches, Cal 25, Macroeconomic 5,
TransportDataStock 39, Residential 28, Energy Access 2, Net Zero
Measures 13, Annual EI Reduction 2, Demographic 2, Commercial 1,
Residential end use data_ 10), and Key→Key internal references add 38
paths (the industry-EI engine `Growth(Key\Annual EI Reduction\
Industry…)` alone is 5,952 rows). The Resources export contains zero
`Key\` references.

The remaining 793 branches (74.5%) are not cited by any exported tree.
Most are consumed elsewhere — Transformation processes, results
screens, and plug-ins (labelled inference: Optimized Trade 495,
Transmission 32, `Cal\Transformation` 13, `Cal\Transport` 10,
`Cal\Industry` 27, `Transport vehicle data_` 28, `Job creations` 22,
`Modeling Assumptions` 16, `Capacity Additions Multiplier` 11,
`Emission Externality Costs` 9, and parts of Other Transport, Net Zero
Measures, Residential end use data_). **The Transformation tree is not
yet exported**, so we cannot yet show you which of these are live
there — a follow-up package will close that gap. Until then, treat
"unreferenced in the six exports" as an upper bound on retirement
candidates, not proof of death.

## 6b. What is currently written in the model — for your review

`current_expressions_keys_4scenarios.csv` is a full dump of the
expressions currently authored in the live model for **every** Key
branch — the extract covers the FULL tree, all three strata.

- **Scope: four scenarios only** — `Current Accounts` (historical),
  `Baseline Simulation`, `AMS Target Scenario` (ATS), `Regional
  Aspiration Scenario` (RAS). The other seven scenarios are copies,
  derivatives, or internal plumbing; corrections you make to these
  four propagate. (Two caveats: the 12 RE-LTRM-differentiating
  cells in §5 live outside these four scenarios — they are enumerated
  in full in §5 so nothing is hidden — and `LCO backup` holds its own
  values on 273 cells (§5), so corrections touching Annual EI
  Reduction, Capacity Additions Multiplier, or Clean Cooking should
  be double-checked against that scenario too.)
- **Reading the region column**: `ALL (12 regions)` means every region
  slot currently holds the same expression (a template value — often
  exactly the thing worth replacing with country data). A named
  country means that row is country-specific. This dedup is why the
  file is 24,142 rows instead of 160,080 (3,335 combos × 4 scenarios ×
  12 regions).
- Columns: `branch_path, variable, scenario, region, expression,
  units, scale, per`. Expressions carry their `? comments`, so the
  provenance (and the confessions) come with them. One reading note:
  the literal token `_x000D_` inside some comments (692 rows in this
  file) is a carriage-return artifact of the export — read it as a
  line break, and feel free to strip it in anything you send back.
- What we'd like back: for any row where you have better data or know
  the intent, a note with branch path, scenario, region, proposed
  value/series, and source. Rows marked `ALL (12 regions)` holding
  round placeholder numbers are the highest-value targets.

## 7. Known issues — review requests, not blame

1. **`Key\Temp` is scratch carrying live scenario signal.** One
   branch, units literally `temp`, holding unit-conversion arithmetic
   (`ConvFuelUnits(gal gas eq, kg, natural gas) * ConvUnits(km, mile)`;
   Indonesia holds `ConvFuelUnits(liter, gj, biodiesel)`) — and it is
   the single cell distinguishing RE Coupling from Shared Energy
   Resources. Is anything downstream reading it? Can it be frozen or
   renamed to something self-describing?
2. **`Incumbent Generator DIspatch Phaseout` typo** (capital "DI") in
   `Key\Modeling Assumptions`. Case-sensitive path lookups miss it. We
   believe Transformation Minimum Utilization formulas consume it
   (*pending Transformation export* to confirm) — renaming needs a
   coordinated consumer sweep. Same class: `Metalurgical Coke` [sic]
   on 3 branches (`Key\Cal\Industry` + two `Key\Industry\Intensity`
   steel-route leaves). **Ask: rule "keep as-is (we document the exact
   casing)" or "queue a coordinated rename once the Transformation
   export confirms the consumers" — per typo.**
3. **Stale `Key\Residential\AC\{a,b}` citations.** 232 residential
   rows cite these branches — but only inside `?` comments preserving
   a retired AEO7 regression; the branches do not exist in the area
   and the live expressions are GDP-per-capita `Lookup` curves. No
   model breakage, but the comments now mislead readers. **Ask:
   confirm the branches are permanently retired (never to be
   recreated); on your yes, we take the comment cleanup to the
   residential team ourselves.**
4. **Near-duplicate trees.** `Key\Cal\Industry` (27 branches) vs
   `Key\Industry\Cal` (6) are distinct calibration panels with
   colliding names; likewise `Key\Residential` (32, live AC/fridge
   drivers) vs `Key\Residential end use data_` (54, regression panels).
   Which of each pair is authoritative going forward?
5. **Unit-vocabulary drift.** `Fraction` (45 rows) / `fraction` (49) /
   `Factor` (56) / `factor` (15), and `years`/`year`/`yr`, coexist in
   the unit column. Harmless to LEAP, hostile to any tooling that
   groups by unit. **Ask: pick the winning spelling per concept (one
   line each) and we normalise the rest in a single hygiene pass.**
6. **Deactivated `!Reactance` / `!Construction Year`** on all 21
   Transmission lines. Intentionally retired, or awaiting data?
7. **Placeholder confession — Household Size.** Myanmar's
   `Key\Demographic\Household Size` (AMS Target + RAS) is
   `Interp(2040, 4) ? placeholder based on discussion`. Every other
   AMS carries a real historical series (Timor Leste holds a flat
   `5.28`; Base Template a template `4`). Can Myanmar be sourced?
8. **Placeholder confession — Transmission Lifetime.**
   `Key\Transmission\Lines\P.Malaysia_Singapore_E:Lifetime_` is
   `80 ? too long for a lifetime? 5 Years is common contract` in all
   four scenarios. The author's own doubt is still in the model —
   please adjudicate (and check the other 20 lines' `80`s while at it).

And three questions only your team can answer:

- **Ownership**: for each top-level group in §2, who maintains it?
  We want a name (team or person) per group so future data drops and
  fix requests route correctly — especially the plumbing stratum
  (Optimized Trade, Transmission) vs the sector data trees.
- **Are the uncited regression panels retired?** The a/b/c coefficient
  panels under `Key\Residential end use data_` and `Key\Transport
  vehicle data_` are (almost) entirely uncited by the exported trees —
  e.g. `Residential end use data_\AC\{a,b}` exist but have zero live
  references. If they are AEO7/AEO8 leftovers, we'd like to mark them
  frozen; if something outside the six exports reads them, tell us what.
- **Is the RE LTRM 12-cell differentiation complete or a work in
  progress?** Within the Key tree the three RE LTRM scenarios differ
  only by the 12 cells listed in §5 (blend-point inserts +
  industry-EI decline + the Temp scratch cell); the only other
  differentiation in the six exports is 7 Ethanol Import Cost cells
  in Resources. Is that the intended full extent of the
  differentiation, or is more authoring still queued?

## 8. What to send back, and in what shape

- **Corrections to current values**: a CSV or plain list with
  `branch_path, variable, scenario, region, proposed_expression,
  source`. Use branch paths exactly as they appear in
  `current_expressions_keys_4scenarios.csv`; expressions in the §4
  conventions (comma-separated Interp, period decimals, `? source`
  comment).
- **Answers to §7**: even one-line rulings ("Temp is dead, freeze
  it" / "80-year lifetime stands because X") close issues.
- **The ownership map** (§7, first question) — a simple two-column
  list, group → owner.
- **Timor Leste**: if you author real Timor Leste values for any
  group, send them as a separate supplement file, never mixed into
  the main set.

Questions → yudiandra.y@gmail.com. Please reference branch paths as
they appear in the CSVs when reporting structure issues.

---
*Exported from LEAP area `aeo9_v0.67_w_results`, "Export Expressions"
workbooks, 2026-07-02. Package assembled 2026-07-03.*
