# v0.75 Power-Sector LEAP Input Export — Final Audit

## 1. Verdict

**Structurally complete but not error-free.** Every one of the 84 process techs is present in all 12 regions with full core-variable coverage, and the dangerous classes (§A.11 lower-bound `Unlimited`, §A.15 Interp separators, negative costs, duplicate keys) are clean — but there is **1 hard error** (Gas Turbine_MYSR has no emissions loading and no grid wiring) plus a set of authoring gaps, region-lock leaks, and unit/naming inconsistencies to review. No findings were refuted.

---

## 2. What is complete & clean

- **Tech × region coverage:** 0 missing (tech, region) cells across 84 techs × 12 regions; all 24 `_ID*` / 19 `_MY*` node variants present in every region.
- **Process Efficiency** (11,088 rows): 0 blank, 0 zero, 0 out-of-range; thermal effs plausible (Coal Sub 33–36, Gas CC 40–60, Nuclear 34–42, Waste 28–33).
- **Maximum Availability:** 0 rows outside [0,100]. **Capital/FOM/VOM negatives:** 0. **Duplicate (branch,var,scenario,region) keys:** 0.
- **§A.15 Interp separators clean:** 0 semicolons inside Interp bodies (all 8,086 semicolon hits were in `?` inline comments).
- **§A.11 lower-bound landmine ABSENT:** zero `Unlimited` on Exogenous Capacity / Existing Capacity / Minimum Capacity; zero literal ≥1e11 numbers anywhere. All `Unlimited` usage is on upper-bound caps only (conditioning risk, not a forced 1e12 floor).
- **Node variable:** all `BranchID(...)` references or `0` (unwired) — as expected, never a 0/1 flag.
- **Nodal Distribution group sums:** 100 for present techs, 0 for absent — correct.
- **Output Fuels + top-level branches:** uniform coverage across all 12 regions (Output Fuels 456 rows @ 38/region; root branch 972 rows @ 81/region).
- **Optimize-vs-simulate variable split is legitimate:** 7 optimization scenarios omit 11 optimizer-bound vars; 4 non-opt scenarios omit 6 simulation-mode vars. Baseline / AMS Target / RAS-test are variable-set-identical. DAC zero-capex/FOM is intentional (all costs expressed as VOM).

---

## 3. Flags to review (ranked)

### ERROR

**E1 — Gas Turbine_MYSR has ZERO emissions loading and ZERO nodal wiring** · count **3,096**
Of 84 techs, Gas Turbine_MYSR (Sarawak) is the *only* combustion tech missing `Avg Environmental Loading` and the *only* tech missing `Nodal Distribution` entirely. Siblings each carry 1,584 emission + 1,512 nodal rows (Gas Turbine, _MYPE, _MYSB all 7,308 rows); MYSR = 4,157 rows with 0 emission + 0 nodal. Natural gas burned at this node produces no CO2/pollutant loading in any scenario and the node is unattached to a transmission node in the 7 optimization scenarios.
→ *Author `Avg Environmental Loading` (12 species) + `Nodal Distribution` for Gas Turbine_MYSR to match _MYPE/_MYSB, or confirm the Sarawak node is intentionally emission-exempt/copper-plate.*

### POSSIBLE GAP

**PG1 — CCS cost variables on only 2 of 6 CCS techs** · count **3,168**
Dedicated `CCS Capital/FOM/VOM` (1,584 rows each) exist only on Coal Supercritical CCS + Coal Ultrasupercritical CCS. The other 4 (Bioenergy w/CCS, Coal IGCC w/CCS, Gas CC w/CCS, DAC) bake CCS cost into an elevated flat Capital Cost (IGCC-CCS `Interp(2023,4770,…)` vs base IGCC `Interp(2023,2730,…)`). **No CCS cost is actually missing** — this is a bottom-up vs top-down method inconsistency, not a value gap.
→ *Reframe as a method-consistency question for the power team; no infeasibility/missing-value risk.*

**PG2 — Wind Onshore_MYSR is an unpopulated defaults stub** · count **132**
In home region Malaysia it carries LEAP defaults — Node=0, MaxCapAdd=0, Maximum Availability=100 (not a ~30–40% wind CF), Capacity Credit=100 — while siblings are populated (MYPE CC=37, MYSB CC=36.8, Node=BranchID). Inert (Node=0 + MaxCapAdd=0).
→ *Decide if Sarawak onshore wind is modeled; if disabled, set CC / Max Availability to 0, not the 100 default.*

**PG3 — Storage-operation variables materialize only in Current Accounts** · count **5**
`Starting Charge`, `Annual/Hourly/Seasonal Storage Carryover`, and `Dispatchable` appear only in Current Accounts (1,008 rows) while `Minimum Charge` appears in all 11 scenarios. The 4 storage techs (CAES, Li-Ion, Pumped Hydro, VRB Flow) dispatch in the 7 optimization scenarios, yet these behavior vars never export there.
→ *Verify storage techs inherit Dispatchable/carryover into the optimization scenarios before relying on storage-dispatch results.*

**PG4 — Timor Leste Solar PV capacity credit left at default 100%** · count **11**
Base Solar PV Capacity Credit is 100 (firm) in Timor Leste across all 11 scenarios vs 16–21% properly overridden in the 10 real ASEAN regions. TL Node=0 (unwired) though MaxCapAdd=20000 and Max Availability=17.7 are set — a partially-authored tech that kept the LEAP default.
→ *Set TL Solar PV CC to ~18–21% (or 0 if not modeled); confirm Node=0 is intended.*

### WARNING

**W1 — §11.2c must-run: Minimum Utilization = bare `Maximum Availability` on variable renewables** · count **1,427** (1,412 pure VRE + 15 non-VRE baseload)
On Solar PV/Rooftop/Floating/CSP, Wind Onshore/Offshore, Tidal, Wave, Small Hydro (+ `_ID*`/`_MY*` variants). Bare `Maximum Availability` forces must-run at the AF profile → per-timeslice primal-infeasibility risk (esp. FP AF leaks). All 1,412 VRE rows sit in the 7 optimization scenarios (RAS=136); zero in the 4 non-opt scenarios.
→ *Set Minimum Utilization=0 for curtailable VRE, or wrap `Min(<floor>, Maximum Availability)` for soft must-run.*

**W2 — §A.11 `Unlimited` on upper-bound caps** · count **10,412**
`Maximum Production` (7,056) + `Maximum Capacity Addition` (1,698) + `Maximum Capacity` (1,658). Exports to NEMO as 1e12, polluting CPLEX conditioning (tol ~1e9) even when non-binding. This is the milder upper-bound case; lower-bound vars are clean.
→ *Prefer a generous finite numeric (e.g. 100,000) over the literal `Unlimited`.*

**W3 — §A.21 region-lock leak: Malaysia gas-node fleet authored inside Indonesia** · count **14**
Gas Engine_MYPE/MYSB/MYSR and Gas Turbine_MYSB/MYSR carry evaluated-nonzero Existing Capacity inside Indonesia (peaking 3,218.87 MW and 5,348.44 MW) — these `_MY*` nodes should be zero/absent outside Malaysia. Capacity Additions leaks = 0.
→ *Strip the Indonesia Existing Capacity values from the `_MY*` gas nodes; run `find_region_lock_violations` on the payload.*

**W4 — Waste CO2 emission factors declared in Kilogramme while 9 other techs use Metric Tonne** · count **264**
Waste is the only tech whose CO2 + CO2 Biogenic `Avg Environmental Loading` leaves carry `Kilogramme`; identical values elsewhere use `Metric Tonne` (CO2 Biogenic = 91.7 on both) → a 1000× discrepancy. Waste fossil CO2 = 0 makes that half inert (but incineration normally emits fossil CO2 from plastics).
→ *Set Waste CO2/CO2 Biogenic unit to Metric Tonne (or ÷1000 the 91.7 if Kilogramme intended); re-examine fossil CO2=0.*

**W5 — Emission leaf literally named `Truck`** · count **132**
Only non-standard pollutant-species leaf in the entire `Avg Environmental Loading` set (the 14 legit species are named). Lives on `…\Coal Ultrasupercritical CCS\Feedstock Fuels\Coal Anthracite\Truck`, expr `7.2 * ConvFuelUnits(kg, TJ, coal anthracite) ? EMEP/EEA Guidebook 2019 Table 6-1`.
→ *Confirm the intended species behind the 7.2 factor and rename/re-home the leaf; verify no aggregation drops/double-counts it.*

**W6 — Gas Turbine_MYSR natural-gas fuel wiring missing in the two under-filled RE LTRM scenarios** · count **55**
Root cause of the two short scenario row counts (RE Coupling −19, Shared Energy Resources −36). `Feedstock Fuel Share` / `Fuel Cost` / `Fuel Source` on Gas Turbine_MYSR\Natural Gas are absent in all 12 regions for Shared Energy Resources (36) and in 6–7 of 12 for RE Coupling (19).
→ *Backfill those three vars on Gas Turbine_MYSR's Natural Gas feedstock for both scenarios.*

**W7 — `_MYKA` is a 4th, undocumented Malaysia node suffix** · count **8** (distinct node suffixes)
Malaysia carries {MYPE, MYSB, MYSR, **MYKA**}, not the documented 3. `_MYKA` appears only on Geothermal Flash + Large Hydro (10,128 rows), region-locked clean to Malaysia (`Large Hydro_MYKA` Exogenous Capacity = `Historical Production[GWh]/(Capacity Credit)`). Per-family node coverage is inconsistent (Geo/Large Hydro use {MYKA,MYPE}; Gas/Solar/Wind use {MYPE,MYSB,MYSR}; Small Hydro has no MY decomposition). Likely a Sabah/Sarawak mislabel — cannot prove typo vs intent from the CSV, and it holds real data so cannot be dropped blindly.
→ *Flag `_MYKA` to the power team; update the CLAUDE.md canon (Malaysia = 3 nodes) to the actual {MYPE,MYSB,MYSR,MYKA}.*

**W8 — Four Malaysia node variants lack the entire historical-fleet quintet** · count **4**
Geothermal Flash_MYKA, Geothermal Flash_MYPE, Large Hydro_MYKA, Unmet Load_MYSR each miss all five of `Existing Capacity`, `Capacity Additions`, `Capacity Retirement`, `Real Investment Cost`, `Historical Capacity Factor` — vars that 80 of 84 techs carry. Internally inconsistent within family (their `_ID*` siblings + base all have the quintet).
→ *Confirm these 4 sub-nodes are genuinely new-build-only; if any is a real existing site, the missing Existing Capacity/HCF drops its fleet from accounting.*

### MINOR

**M1 — Feedstock Fuel Share (a %) and Fuel Source (a selector) labeled with USD units** · count **25,883**
Share values are clearly percents (`0`, `100`, `Remainder(100)`, `Interp(2015,0,2019,70)`) yet Units = `U.S. Dollar` / `2020 USD`; Fuel Source holds `SourceBelow`-type selectors also labeled USD. Export inheriting the Feedstock-Fuels branch cost unit onto child vars — harmless if downstream ignores it, a landmine for exact-unit-string logic.
→ *Treat the Units column as unreliable for Feedstock Fuel Share / Fuel Source.*

**M2 — Three inconsistent USD spellings for the same cost vars** · count **11,268**
Fuel Cost & Fuel Source use `U.S. Dollar` / `2020 USD` / `2020 U.S. Dollar` (the last: 132 Nuclear SFR feedstock rows). Same real unit, three literal strings — exact-string matching would treat them as three units.
→ *Normalize to a single canonical spelling.*

**M3 — Dead `_MYKA` node stubs carry `Unlimited` MaxCapAdd with zero capex** · count **264**
Geothermal Flash_MYKA + Large Hydro_MYKA: Node=0 in all 12 regions, zero Existing Capacity and Capital Cost everywhere, yet MaxCapAdd=`Unlimited` (→1e12) + Capital Cost=0 in Malaysia = a latent free-unlimited-build combination, inert only because Node=0.
→ *Remove the non-canonical `_MYKA` branches, or replace `Unlimited` with a finite cap + real capex before wiring the node.*

**M4 — §11.2e Max(numeric-first) on Solar PV_MYSR Historical Production** · count **4**
`Max(0, Smooth(2005,0,…2024,0))` in the 4 non-opt scenarios — numeric-first Max is the year-misparse antipattern, but inert (inner Smooth is all zeros). The other 2,421 `Max(` rows use the safe numeric-last form.
→ *Rewrite as `Max(Smooth(…), 0)`; low priority.*

**M5 — Share var naming asymmetry (`Maximum_Share_of_Production` vs `Minimum Share of Production`)** · count **2**
Underscore-named `Maximum_Share_of_Production` (10,080 rows, 10 scenarios) vs space-named `Minimum Share of Production` (7,056 rows, 7 opt scenarios). Inconsistent naming (a grep trap like the `DIspatch` capitalization case) plus asymmetric scenario coverage.
→ *Flag the underscore name; ensure injectors/probes match the exact literal; confirm the coverage asymmetry is intentional.*

---

*Refuted items: none — all 23 findings resolved as CONFIRMED, NEW, or clean/NA. Duplicate pairs were merged (F1↔mu-equals-max-availability into W1; F2↔unlimited-upper-bound-systemic into W2; F5↔max-numeric-first-hp into M4).*