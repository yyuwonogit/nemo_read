# Power batch-1 changelog — RAS v0.69 delta send-back (2026-07-08)

Delta-only payload against the injected baseline
`power_sendback_canonical_FINAL.csv` (9,337 rows). Two delta files:
`power_batch1_delta_20260708.csv` (326 rows, RAS) and
`power_batch1b_endogenous_ATS_BAS_delta_20260708.csv` (48 rows, AMS Target +
Baseline Simulation). Plus three separate CSVs (stranded-cost probe, run-2
dispatch reversal, WP-F gas proposal). Every row validated through
`build_delta_payload.py --check` (exit 0); all Capacity Retirement proven
non-negative 2024-2060. One section per authoring action below.

---

## WP-A — Delta emitter / validator (infrastructure)
**One line:** built a reusable delta emitter/validator so every payload row is
checked against the canon before ship.

| Item | Value |
|---|---|
| Files | `Power/Analysis/build_delta_payload.py` (+ `test_delta_payload.py`) |
| Enforces | per-variable units; region-lock; MaxCap/MCA only in RAS; Endogenous never in RAS; no Unmet-Load / _MYKA; Max() reference-first; no dup keys |
| Test | baseline round-trips to 0 delta; synthetic bad-delta caught; exit 0 |

**Method:** delta = rows whose expression value-part differs from canon (source
annotation ignored, so citation churn creates no spurious delta). Key =
(ams, branch, variable, scenario). Fail-loud on any violation.

## WP-D coal — RAS gradual coal phase-down (5 rows, Capacity Retirement)
**One line:** phase the subcritical coal fleet toward ~0 by 2060 with ~10% left
at 2050, oldest/dirtiest first, off the exogenous fleet.

| ams | branch | old → new | shape |
|---|---|---|---|
| Indonesia | Coal Subcritical_IDEast/_IDJW/_IDKA/_IDSA | 0 → Add(...) | 90% retired by 2050, remainder to ~0 by 2060 |
| Malaysia | Coal Ultrasupercritical | merge +1000 MW (Manjung 4) into kept PDP row @2060 | — |

**Method:** pool = exogenous Existing(2024) + committed Additions; aggressive
30-yr subcritical life → phase-out from 2031. Indonesia supercritical SKIPPED
(fleet endogenous/~0). Coal IGCC treated as cleaner (not retired here). Sources:
GEM Global Coal Plant Tracker / Boom & Bust Coal 2024-25; IEEFA; IEA SEA Energy
Outlook 2024. Non-negativity verified (worst −0.002 MW, RAS Max(...,0) clamps).

## WP-D gas/oil — RAS gas/oil phase-down (11 rows, Capacity Retirement)
**One line:** retire the existing Diesel / Fuel Oil / Gas Turbine-Engine-Steam
fleet on the same 10%-at-2050, ~0-at-2060 shape (Gas Combined Cycle excluded).

| Group | Rows | Content |
|---|---|---|
| Lock already-declining | 6 | 4 Indonesia Diesel nodes + PH Diesel + KH Fuel Oil |
| New | 2 | Myanmar Diesel 181 MW, Vietnam Diesel 178 MW residual |
| Deficit-node paired | 3 | Gas Engine_IDEast/_IDSA/_IDKA (ship WITH the WP-K supply raises) |

**Method:** RAS Exogenous = Max(Existing+Add−Ret,0) so Retirement is the sole
decline lever; ages oil/diesel 25 yr, gas 30 yr (Statista lifetimes). Total
6,783 MW (~6,454 net-new). Verified no negative exogenous. NOTE to LEAP:
clear any pre-existing `Interp(2035,0,2040,N)` retirement cliff on these nodes
before applying so the intended 10%@2050 shape materialises.

## WP-E — Dirty-fossil freeze + escape-valve closure (187 rows)
**One line:** freeze new tier-1/2 dirty fossil, cap the plain-gas / biomass
escape valves, and cost the un-costed national branches.

| Block | Rows | Content |
|---|---|---|
| Tier-1/2 freeze (RAS) | 140 | Coal Sub/Super, Diesel, Fuel Oil, Gas Steam/Turbine/Engine → Maximum Capacity = Exogenous Capacity[MW], MCA = 0 |
| Plain Gas CC | 7 | capped-but-expandable: MCA at national gas build rate, NO stock ceiling |
| Biomass Other | 12 | Maximum Capacity ceilings at biophysical potential (Thailand ~8 GW) |
| Cost blocks | 28 | Capital + Fixed OM + Variable OM + Efficiency for un-costed national Large Hydro / Diesel / Coal Subcritical |

**Method:** escape-valve sizing from solved v0.69; costs from DEA Indonesia 2024;
caps from `build_rate_caps.csv` / `hard_total_caps.csv` + national biomass plans
(Thailand AEDP, PDP8, PH NREP). **All CCS-tagged processes left UNCAPPED**
(user). DAC + deactivation caps left untouched (pending). USC/IGCC (non-CCS)
left capped-but-expandable — deliberate, see watch-items.

## WP-F — Natural-gas supply ceiling (10-row PROPOSAL, fossil team)
**One line:** propose a regional gas envelope so the optimizer can't treat gas
as infinite (Resources column = fossil team's to author).

| Item | Value |
|---|---|
| Envelope | 1.2 × (ASEAN total 2023 production), split uniform across the region |
| Shape / scenario | flat, RAS-only |
| Companions | reprice non-producer gas Production Cost off 0; commission a Hydrogen price; add ID + MY Maximum Production to the binding list |

**Method:** EI Statistical Review 2024 (2023 production), 38.2 PJ/bcm. Verified
2060 demand = 479.5 bcm = 2.44× production, so the 1.2× envelope binds. NOT a
capacity-injection — a hand-off; ships as its own CSV + memo.

## WP-G — Nuclear headroom (20 rows)
**One line:** open aggressive per-AMS nuclear ceilings at full per-tech build
rate so nuclear can grow once the backstop is repriced.

| ams | Maximum Capacity (spread across LWR/SFR/SMR) | MCA per tech |
|---|---|---|
| Indonesia | 44 GW total (14.67 GW/tech) | 2000 MW/yr (=baseline, no-op) |
| Vietnam | 20 GW (2060 stretch), 6.67/tech | 1500 MW/yr |
| Philippines | 7 GW (2060 stretch), 2.33/tech | 800 MW/yr |
| Brunei, Laos | template MCA zeroed | 0 |

**Method:** ceilings spread across techs to SUM to the AMS total; full build
rate per tech (user). Singapore deferred. Sources: PDP8 rev (Decision
768/QĐ-TTg 2025), Indonesia RUKN, PH DOE Roadmap, DEA costs. Caveat: caps
alone won't dispatch nuclear — depends on WP-H repricing the backstop.

## WP-H — H2-chain containment (20 rows, caps only)
**One line:** cap the H2 Fuel Cell escape valve at verified per-AMS build rates
(the source cap on the hydrogen module is deferred to batch-2).

| ams | H2 Fuel Cell MCA (MW/yr) | Maximum Capacity |
|---|---|---|
| ID 150 / MY 300 / SG 500 / TH 100 / VN 100 / PH 50 / BN 50 | — | Max(Exogenous Capacity[MW], 36×MCA) |
| KH / LA / MM | 0 | 0 |

**Method:** MCA = 1000 × verified hydrogen build rate (`caps_research_verified.csv`);
H2FC kept on the LEAP area-default cost (higher than DEA, containment-consistent).
Removes ~978 TWh of 2060 generation — see watch-items (surfaces as unmet). The
GCC hydrogen co-fire leak is closed by WP-L (VN CCS → 100% gas), the only active
RAS co-fire path.

## WP-I — Stranded cost (1-row SEPARATE probe)
**One line:** one Stranded Cost value to let the LEAP team confirm the variable's
unit semantics from the cost report (optimization-inert).

| Item | Value |
|---|---|
| Row | Coal Subcritical (tier-1) Stranded Cost, unit `U.S. Dollar` |
| Note | fails --check by design (non-canonical unit IS the probe); ships as its own CSV; fleet-wide methodology deferred to batch-2 |

## WP-J — RAS contractual-dispatch experiment (18 rows + 18-row run-2 reversal)
**One line:** run-1 raises Minimum Utilization must-run floors on the contract-
tied fossil fleet; run-2 reverses them — the cost-of-take-or-pay narrative.

| Floors (Min(floor, Maximum Availability)) | Level |
|---|---|
| Coal (6 nodes) | 60% (IEA "Enhancing Indonesia's Power System") |
| Gas CC 7 / Gas Engine 4 / Gas Turbine 1 | 50 / 40 / 25 % |

**Method:** floors authored where RAS Historical Capacity Factor = literal 0 (the
deficit nodes). NOT an unmet-reduction lever (at 2060 peak-unmet the fleet
already runs at its ceiling); it is the contractual-cost experiment. Run-2
reversal is a byte-clean restore, shipped separately.

## WP-K1 — Outer-Indonesia clean-firm caps (35 rows)
**One line:** raise outer-Indonesia geothermal ceilings and make hydro
availability honest (65%).

| Change | Value |
|---|---|
| Geothermal Flash Maximum Capacity | IDEast 5460, IDSA 9370, IDKA 180 MW (MEMR/DG EBTKE 2021) |
| Hydro Maximum Availability | 65% (Large + Small), all 4 scenarios |

**Method:** national hydro Resource ceiling HELD (node hydro raises inert this
cycle); refuted Wind Onshore_IDEast floor dropped. The availability derate
tightens firm energy (unmet up at those nodes — honest, tracked).

## WP-K2 — Node cap re-sourcing (3 rows)
**One line:** raise Sarawak hydro and Vietnam onshore wind to their real
technical potential.

| Change | Value |
|---|---|
| Large Hydro_MYSR Maximum Capacity | 10 → 20 GW (Sarawak Energy 2024, 52 sites) |
| Wind Onshore Vietnam Maximum Capacity | 24 → 217 GW (VER Aug 2020) |
| Cambodia Solar PV | 40 → 44 GW (provenance-only, IEEFA) |

**Method:** node firm/storage structural creates HELD (Jamali peak deferred);
Sarawak solar 20 GW proxy kept.

## WP-L — Vietnam Gas-CC-with-CCS wiring fix (4 rows, Feedstock Fuel Share)
**One line:** un-idle Vietnam's gas-CCS by removing the erroneous hydrogen
co-feedstock.

| Change | Scope |
|---|---|
| Natural Gas share → 100, Hydrogen → 0 | RAS + AMS Target |

**Method:** the plant required both H2 and gas per unit output (10 GW built, 0
generation); set to pure gas-with-CCS like the other 9 AMS. Base-branch question
closed no-action (the 84 removed Indonesia base rows were deactivation zeros).

## WP-M — Node build-rate harmonisation (26 rows, Maximum Capacity Addition)
**One line:** give every Indonesia/Malaysia sub-node the same per-technology
build rate (the country-wide max), for the clean techs.

| Example | old → new (MW/yr) |
|---|---|
| Large Hydro all ID nodes | Kalimantan 43.8 → 442.1 (+ IDEast, IDSA lifted) |
| Solar PV / Geothermal / Wind at outer nodes | lifted to the ID max; Kalimantan wind 0 → 148.7, geo 0 → 318.7 |

**Method:** per-country per-tech max across nodes (user rule). Clean techs only
(dirty fossil frozen by WP-E). Fixes the 2023-rate split that starved the outer
nodes.

## Batch-1b — Endogenous-capacity decision table (48 rows, ATS/BAS)
**One line:** stop the model auto-building worse tech (subcritical + supercritical
coal, diesel, fuel oil) after policy end in the non-optimized scenarios — the
only lever that reaches AMS Target + Baseline.

| Decision | Rows | Content |
|---|---|---|
| time-box | 22 | Coal Subcritical, Diesel — Step() to zero by policy-end year |
| zero | 14 | PH/MMR coal, diesel/fuel-oil after-policy backfill |
| knob re-author | 10 | RE central-knob shares (PH ×5 flagged NEEDS-CONFIRM, VN ×4, IDN Biomass Gasification) |
| new Coal Supercritical (ATS) | 2 | Indonesia, Laos → 0 (close the after-policy SC hole to match the RAS freeze) |

**Method (from the parallel reconciliation session, adopted with user rulings):**
"worse" = operating CO2 intensity (fuel EF ÷ efficiency); policy end = last
positive scheduled Addition year. **User rulings 2026-07-08:** CCS uncapped in
ATS/BAS (dropped the Thailand USC-CCS zero); USC aligned OPEN (dropped the
Thailand USC zero); Coal Supercritical added ATS-strict. Fixes: PH-diesel-ATS
inverted window → 0; 6 _MY* Bad-Scenario copy rows excluded. Coherent ladder:
ATS bans new subcritical + supercritical beyond PDP; USC/IGCC/CCS open
everywhere.

---

## Watch-items shipped with this payload (for the run, and confirmations to the LEAP team)
1. **Unmet load will RISE** — the H2 cap strips ~978 TWh of fake free generation;
   Indonesia's real deficit becomes visible (may ~double). Honest baseline for
   the unmet tracker; not a regression.
2. **New unabated Coal USC / IGCC (non-CCS) left uncapped in RAS** — deliberate
   (cleaner transition); watch for a new-coal escape in run-1.
3. **Gas supply uncapped in the inject** until the fossil team applies the WP-F
   proposal.
4. **5 Philippines endo knob rows** carry a NEEDS-CONFIRM flag (kick-in year
   derived, not read from a live PDP).

Confirmation asks are in the accompanying work-order memo.
