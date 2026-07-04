# LEAP structure canon — pipeline SOP

> How the canonical LEAP structure (`LEAP structure/`, CLAUDE.md §2.6) was
> built, verified, and turned into team handovers — and the recipe for
> repeating any part of it (a new tree export, a new area version, a new
> team package). Established 2026-07-02/03 across the six-export canon
> cycle. Scripts referenced here are committed in
> [LEAP structure/tools/](../LEAP%20structure/tools/) (each has its I/O
> paths defined at the top — point them at the current session's scratch
> or a work dir before running; they are pure-offline, no LEAP COM).

## 0. The one-paragraph version

The user exports each LEAP tree with LEAP's **Export Expressions** (single
`Export` sheet, Ver 2 format) into `LEAP structure/LEAP Input <Tree>.xlsx`.
We stream-convert every workbook to flat CSVs offline, derive digest
artifacts (branch trees, variable/unit inventories, scenario-variation
matrices), run a **multi-agent analyst → adversarial-verifier Workflow**
over the digests, fold the corrected findings into
[LEAP_STRUCTURE_ANATOMY.md](../LEAP%20structure/LEAP_STRUCTURE_ANATOMY.md),
sweep the repo/memories for contradictions (canon supremacy), then cut
**mechanically connection-audited team slices** and ship per-team handover
packages. No step touches LEAP COM.

## 1. Step-by-step

| # | Step | Who | Tool / output |
|---|---|---|---|
| 1 | **Export** a tree from LEAP (Export Expressions) | user | `LEAP structure/LEAP Input <Tree>.xlsx` — one `Export` sheet; row 1 area stamp, row 3 header, cols A–L data, N–U Level split |
| 2 | **Digest** to flat CSVs + summaries | script | [tools/digest_leap_structure.py](../LEAP%20structure/tools/digest_leap_structure.py) → `<sector>_rows.csv` (branch_id…expression), `_branches.csv`, `_variables.csv`, `_summary.json`. Streams via openpyxl read_only (1M-row Industry ≈ 4 min); run in background with progress prints |
| 3 | **Tree + scenario-variation artifacts** | script | [tools/tree_and_scenario.py](../LEAP%20structure/tools/tree_and_scenario.py) → `<sector>_tree.txt` (indented, vars per branch), `_scenario_variation.csv` (per (branch,variable): scenario divergence, scenario-scoped rows, regional variation) |
| 4 | **Reference resolution** across trees | script | [tools/resolve_refs.py](../LEAP%20structure/tools/resolve_refs.py) → `ref_resolution.csv`: every `Key\`/`Resources\` reference in demand expressions vs the exported branches (OK / BRANCH_MISSING / VAR_MISSING) |
| 5 | **Verified analysis** | Workflow | One analyst agent per export + one adversarial fact-checker per analyst (re-runs every count; corrections applied before anything ships). Schema-forced structured output: markdown chapter + key_facts(claim, evidence) + quirks |
| 6 | **Canon doc + trees** | operator | Fold corrected chapters into `LEAP_STRUCTURE_ANATOMY.md`; copy `_tree.txt` files to `LEAP structure/trees/`; spot-check 2–3 corrected numbers against raw rows yourself |
| 7 | **Supremacy sweep** | operator | Grep CLAUDE.md / memories / guides for structural claims contradicting the new canon; fix each citing canon (§2.6). Examples fixed 2026-07-02: §2.3 `<Fuel> Imports` sub-branches (don't exist), §11.2c `DIspatch` spelling, Motorcyle fuel children |
| 8 | **Connection audit + team slices** | script | [tools/phase0_connection_audit.py](../LEAP%20structure/tools/phase0_connection_audit.py) → per-team slice lists (owner groups ∪ live-code references), slice trees + units CSVs, gap audit of shipped packages |
| 9 | **Current-state extracts** | script | [tools/gen_current_state.py](../LEAP%20structure/tools/gen_current_state.py) → `current_expressions_*_4scenarios.csv`: what is authored NOW, scoped to CA / Baseline Simulation / AMS Target / RAS, region-deduplicated (`ALL (12 regions)` rows = template values) |
| 10 | **Team packages + guides** | Workflow | Author → adversarial verifier → completeness critic per artifact (pipelined, no barriers). Packages at `inject/<team>/structure_handover_<YYYYMMDD>/`; house README template = the transport package README |
| 11 | **Bookkeeping** | operator | CHANGELOG bullets, CLAUDE.md §9 docs-map rows, Cross-Domain Learnings entries, memory updates, this SOP |

## 2. The package file-group roster (user-confirmed 2026-07-03)

Every team package ships the same seven groups:

1. **Team README guide** — plain-language: tree anatomy, variables+units,
   expression rules, scenario/region scoping, known issues as review
   requests, what to send back.
2. **Own branch tree** (`*_tree.txt`).
3. **Branch × variable × units CSV** — the validation reference.
4. **Connected `Key\` slice** (tree + units) — mechanically derived, see §3.
5. **Connected `Resources\` slice** where the sector wires into it.
6. **Connected `Transformation\` slice** — pending that tree's export.
7. **Current model contents** — the 4-scenario extracts (group 9 above).

Teams: bioenergy, transport, residential (shipped 2026-07-03 AM),
commercial, keys (central assumptions team), fossil, power (shipped
2026-07-03 PM; Transformation slices to follow).

## 3. Load-bearing lessons (do not re-learn these)

- **Strip `?` comments before extracting references.** Expressions carry
  retired equations inside comments; `Key\Residential\AC\a`/`b` are cited
  in 232 residential rows but only ever after the `?` — they don't exist
  as branches and no `!Missing Branch!` fires because LEAP never resolves
  comment text. Live-code = `expression.split('?')[0]`.
- **The `Level 8...` export column concatenates deeper path segments.**
  A depth-9 branch shows `Gasoline\Ammonia` in one cell. Parse
  `Branch Path`, never the Level columns (4,932 industry branches would
  under-split).
- **Scenario-scoped rows are structure.** Row-count deltas between
  scenarios locate CA-only calibration variables (UnscaledFuelShare,
  Stock…) and the residential 7-scenario device-stock panel. Diff the
  per-scenario row counts before assuming rectangularity; only the Key
  tree is perfectly rectangular.
- **Region dedup makes extracts reviewable.** Collapsing region-uniform
  (branch, variable, scenario) cells to one `ALL (12 regions)` row shrinks
  extracts ~6× and makes template values (the prime review targets)
  self-identifying.
- **Adversarial verification pays.** Across the canon cycle the fact-check
  passes corrected ~15% of first-pass claims (wrong counts, mis-attributed
  splits, over-generalisations like "all on the macro spine"). Never ship
  an analyst's numbers unverified; spot-check a couple of the corrections
  yourself on top.
- **Scenario "names" lie; diff expressions.** Six scenario names collapse
  to one expression set in some sectors while "backup"/"test" scenarios
  genuinely diverge elsewhere (LCO backup is 273 cells off Set up in the
  Key tree). The 4-scenario review scope (CA/Baseline/ATS/RAS) is a user
  decision recorded 2026-07-03.
- **Owner groups alone under-slice; live refs alone miss ownership.**
  Commercial's slice needs the borrowed residential branches (live refs);
  transport's needs all of TransportDataStock even where not yet
  referenced (ownership). Union both.
- **Fossil ↔ Key: zero connections** (mechanically verified) — absence of
  a slice file can be a verified fact; say so in the README rather than
  leaving the team to wonder.

## 4. Next-cycle recipes

**A new tree export lands (e.g. Transformation):** run steps 2–6 for it
(digest → trees → analyst+verifier Workflow → new anatomy chapter), then
step 8 to regenerate slices for the teams that connect to it
(power/fossil/bioenergy), patch their packages + guides, CHANGELOG. It is
a canon *extension*, not a contradiction — §2.6's anomaly rule applies to
changes in already-canonical trees only.

**A new area version (v0.68+):** re-export, re-digest, then **diff
structure against canon** (branch sets, variable panels, units, rosters)
before anything else. Structure unchanged → refresh expression-level
artifacts (current-state extracts) and carry on; structure changed →
STOP and flag to the user per §2.6 — never silently re-derive canon.

**A new team package:** add the team's owner groups to
`phase0_connection_audit.py`, run steps 8–9, then a three-stage
author→verify→critic Workflow item using the transport README as the
template. Confirm the file-group roster with the user first (§2).
