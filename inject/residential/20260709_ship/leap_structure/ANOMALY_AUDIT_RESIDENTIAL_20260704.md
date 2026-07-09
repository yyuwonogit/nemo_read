# Anomaly audit — Residential team slice (`aeo9_v0.67_w_results`)

This is **your team's slice** of the full-corpus canon anomaly audit run on
2026-07-04 over the live model area `aeo9_v0.67_w_results` (four scenarios:
Current Accounts, Baseline Simulation, AMS Target Scenario, Regional
Aspiration Scenario). The master audit swept every sector for authoring
defects; below are only the items that touch branches **your team owns or
authors** — the whole `Demand\Residential` export (Historical + Projections,
both old and new appliance trees, Lighting, pollutant leaves) plus the
`Key\Residential\*` appliance drivers (Percent Ownership, Size/Efficiency
shares, Useful_EI) that your demand branches read from. Each finding keeps
its original wording, row counts, **NEW/KNOWN** and **VERIFIED/SUSPICIOUS**
tags, and (in Part B) its 🔴/🟡/🟢 grade — nothing here is re-scored or
re-counted. **Your job is to judge each one and fix or rule on it**; several
are "review requests, not blame" that only your team can settle (is the
old/new tree double-count real, is the AC `×2` intentional, etc.). Part A is
incorrectly-authored values grouped by anomaly class; Part B is
empty/placeholder-but-important, graded by severity. A couple of items are
driven by your data but physically live in a shared `Key\` branch — those
carry a **cross-tree note** so you know they are upstream of the demand tree
but still yours to author.

---

## Part A — Incorrectly inputted (anomalies in authored values)

### A4. Duplicate branch / parallel-tree double count

- **NEW · VERIFIED — two branches share the path
  `…Historical\Charcoal\Carbon Monoxide`.** branch_id 8996 = `189` kg/**tonne**,
  branch_id 9008 = `26` kg/**TJ**. Both live in all 4 scenarios × all regions →
  **charcoal CO emissions computed twice**, on two different bases. The only
  duplicate-named pollutant leaf in the sector. *96 rows. Residential.*
- **NEW · VERIFIED (expression-level) — old and new appliance trees both
  active.** `Refrigeration` (old, share-based) and `Refrigeration_` (new,
  device-stock) both carry non-zero saturation **and** non-zero intensity in
  Baseline/ATS/RAS, while the new tree is inert in CA (Useful_EI = 0). So
  projection scenarios carry ~double the fridge (and AC) electricity relative
  to the calibrated CA basis. Magnitude needs a results harvest; simultaneous
  activation is verified. *178 rows + AC analogue 78. Residential.* (Confirms
  anatomy §10.5's previously-"unverified" exposure.)

### A5. CA → forward-scenario discontinuities (level jumps at the 2024/25 seam)

- **NEW · VERIFIED — fridge ownership collapses 2022→2023.**
  `Key\Residential\Refrigeration\Percent Ownership` splices two sources inside
  one Interp: Philippines 88 → 50 (−38 pp), Indonesia 97.6 → 89, Vietnam 100 →
  80.5 — a physically impossible one-year drop in **9 of 11 countries**, and it
  drives the whole `Refrigeration_` device-stock saturation. *36 rows.
  Residential/Keys.*
  **Cross-tree note:** the defective series physically lives in the shared Key
  tree at `Key\Residential\Refrigeration\Percent Ownership` (branch_id 29116),
  not in the `Demand\Residential` demand tree — but it is a residential-authored
  appliance driver (§6 of your README: "this is where your ownership/share data
  actually lives"), so the fix is yours to make in the Key slice.
- **NEW · SUSPICIOUS — AC Useful Energy Intensity switches basis at the seam.**
  CA holds country-study `<coef>*!EER` formulas, projections hold unrelated
  constants: Thailand ~13,062 → 616 kWh/hh (21×), Cambodia 7×, Philippines 5×,
  Myanmar jumps up 4.6×. **7 of 12 regions shift >3×.** *48 rows. Residential.*
- **NEW · SUSPICIOUS — lighting tech-shares re-classified at the seam.** CA has
  Fluorescent = Halogen = 0 with CFL = Remainder(100); every projection restarts
  Fluorescent at 8–20 and Halogen at 2–4 in 2025 → the lamp mix (and thus
  lighting intensity) jumps up to ~22 pp in one year. *68 rows. Residential.*

### A7. Cross-region outliers / unit slips

- **NEW · SUSPICIOUS — residential intensity outliers:** Vietnam Clothes Dryer
  3.1 vs sibling 585 (189× low), Myanmar Water Heating 0.6 vs 116 (193× low),
  Malaysia Cooking NG 0.1 vs 25 — per-owning-household vs per-household basis
  slips. *10 rows. Residential.*

### A10. Solver output written into inputs / sentinel literals

- **KNOWN — NEMO/CPLEX `Data(…) ?Optimized on 07/02/2026 (NEMO/CPLEX)`
  writebacks** on Refrigeration_/AC_ tier Activity Levels (RAS) — authored input
  and solver output conflated. *180 rows. Residential.*
- **KNOWN — literal `Unlimited`** on Maximum Devices / Maximum Device Additions
  (device twin of the §A.11 1e12 trap). *432 rows. Residential.*

### A11. CR artifacts inside live code

- **KNOWN — `_x000D_` before the `?`** in 334 residential live expressions
  (lighting formula, AC Lookup arg lists) and 10 transport IW FEI `If()`
  formulas. *Residential 334, Transport 10.*

### A12. Comment hygiene hiding data problems

- **KNOWN — residential `~`-dialect dead equations inside live Lookup**, the
  undocumented `×2` AC multiplier, and 3 inconsistent ownership methods across
  countries. *61 rows. Residential.*

### A13. Naming / typos

- **NEW — `? ACE defult` comment typo hides 16 Water Heating placeholder rows
  from "default" greps.** Residential.
  *(From the master audit's A13 combined line, which also lists transport
  `Motorcyle` and resources `Metalurgical Coke` — those two belong to other
  teams; only the `ACE defult` typo is residential's.)*

### A14. Other structural

- **NEW · SUSPICIOUS — `!EER` (leading-bang deactivation-convention name) is
  live and load-bearing** in the AC efficiency chain (192 rows) — a future
  cleanup that deactivates it would zero AC efficiency.
- **KNOWN — dollar-vintage mismatches:** … residential Variable OM Cost
  per-energy (canon) vs per-device-year (authored).
  *(This is one bullet from the master audit's cross-sector A14 dollar-vintage
  line, which also covers transport Rail "2020 USD" and resources vintage-less
  rows — only the residential Variable OM Cost basis mismatch is yours.)*

---

## Part B — Empty but important (graded)

*(No residential items fall in 🔴 RED — the three RED findings are Road
transport emissions and two Resources supply-route items, all owned by other
teams.)*

### 🟡 YELLOW — placeholder/template values silently shaping results (wrong numbers, not broken mechanics)

- **Useful_EI = 0 in CA** on all 6 device-stock size classes while non-zero in
  projections → the CA calibration attributes all historical fridge/AC
  electricity to the old trees; switching the new tree on without retiring the
  old is the double-count (A4) — the 2024→2025 electricity step is an artifact.
- **Device Demand Cost = 0 on 5,100 of 5,280 rows**; the only non-zero values
  (Refrigeration_ in Baseline/ATS) are region-uniform 280.45 — two disjoint
  costing systems (Demand Cost vs Capital Cost) for the same appliances; note
  Low_eff priced *above* Mid_eff.
- **248 placeholder-confession intensities** ("585 ? ACE default", "? ACE
  Placeholder when no data", "assumed valuie") driving end-use electricity in
  every scenario, mostly identical across countries.
- **Template-uniform Useful_EI** — 6 ASEAN-wide constants for appliance unit
  energy (climate-driven for AC) → inter-country demand differentiation comes
  only from ownership, not intensity.
- **AC new-tree Percent Ownership = 0 in CA** (uncalibrated addition stacked on
  the still-active old AC tree — same double-count, smaller).
  **Cross-tree note:** this Percent Ownership driver lives in the shared Key
  tree (`Key\Residential\Air Conditioning\Percent Ownership`), same as the
  fridge ownership item in A5 — residential-authored, upstream of the demand
  branches.

### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

- **TotalEnergyRes all-zero series** (55 rows — genuinely unused fuels, matches
  published balances).
- **All-zero share partitions** (Base Template + Timor Leste only).

---

## Highest-leverage for your team (if triaging)

1. **Rule on the old/new appliance-tree double-count** (A4 + the 🟡 CA
   Useful_EI=0 / AC Percent Ownership=0 items) — this is the largest results
   distortion in your slice: projection scenarios carry ~double fridge/AC
   electricity vs the CA basis. Deciding whether to zero the old trees' ownership
   going forward is the single highest-value call only your team can make.
2. **De-splice the fridge Percent Ownership 2022→2023 collapse** (A5) — a
   physically impossible one-year ownership drop in 9 of 11 countries that drives
   the whole `Refrigeration_` saturation; the correct source values are a
   re-author in the Key slice.
3. **Settle the AC UEI basis switch and lighting tech-share reclassification**
   (A5, both SUSPICIOUS) — each is a >3× / ~22 pp one-year jump at the 2024/25
   seam that flags a per-household vs per-owning-household basis slip or a
   provenance swap; both need your judgment before the numbers can be trusted.
4. **Fix the duplicate `Charcoal\Carbon Monoxide` leaf** (A4) — a clean,
   verified defect: two branches on one path compute charcoal CO twice on
   different unit bases; pick the correct basis and retire the other.
5. **Clean the mechanical artifacts** (A10 Unlimited device sentinels + NEMO/CPLEX
   writebacks, A11 `_x000D_`, A13 `ACE defult` typo, A14 `!EER` load-bearing
   name) — low-judgment hygiene, but the `!EER` and `Unlimited` items are
   landmines that would zero AC efficiency / detonate the 1e12 trap if a future
   cleanup touches them blindly.
