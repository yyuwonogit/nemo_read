# Transport — LEAP Action Items

**Date:** 2026-05-20
**Prepared by:** YY
**Model file (target):** `aeo9_v0.47_transport` (verified by the 2026-05-20 inject pass that landed the 562-row canonical at `Transport/Inject/canonical_leap_inputs_remainder_patched_20260520.csv`)
**Driver script (interactive, generic):** `Transport/LEAP Input/input_to_LEAP_v2.py`
**Production inject path (post-framework-fix):** `nemo_read/inject_base.py::CanonicalInjector` invoked in `--blind` mode per `Transport/Inject/TRANSPORT_INJECT_SOP.md`. The interactive driver above remains as a manual-fallback path.

This note lists everything the inject team needs to paste into LEAP for
the Transport sector. All source-of-truth artefacts live in
`Transport/LEAP Input/`. The Transport pipeline ships deterministic
projections; LEAP owns stock turnover, survival, fuel-economy lookup
and mileage at the variable level. Our job is to populate the inputs.

## 0. Master action table

| # | What | Source artefact | LEAP variable | Scope | Detail in |
|---|---|---|---|---|---|
| V1 | Sales fuel-share by scenario | `sales_mix.csv` | Sales Share (Vehicles_Sales_Share leaves) | 3 scenarios × 4 vehicle classes × 10 AMS × {2–5 fuels} × 2000–2060 | §A1 |
| V2 | Sales magnitude (vehicle-class totals) | `sales_magnitude.csv` | Vehicle Sales (per-class total) | 4 vehicle classes × 10 AMS × 2000–2060 | §A2 |
| V3 | Base-year fuel-mix anchor | `starting_year_sales.csv` | Sales Share base-year override | 102 rows; 4 vehicle classes × 10 AMS (SGP Truck absent — see §C2) | §A3 |
| V4 | Per-AMS 2020 mileage anchors | `LEAP Input/mileage_anchors.csv` | Mileage | 40 values (4 vehicle classes × 10 AMS), held flat 2005–2060 | §A4 |
| F1 | PPV CNG fuel-economy fix | (LEAP edit-in-place) | Fuel Economy | 30 → 26 MPGe on PPV CNG | §B1 |
| F2 | ERIA 2022 Phase II citation cleanup | (LEAP edit-in-place) | Mileage citation field | Cars + Motorcycles only (5 ASEAN + India); retire Bus + Truck attribution | §B2 |
| X1 | Stock fuel-share (cross-check only, NOT a paste) | `stock_by_fuel.csv` | Vehicle_Stock_Share (LEAP-computed internally) | 3 scenarios × 4 vehicle classes × 10 AMS × {2–5 fuels} × 2005–2060 | §E1 |

**Three Transport scenarios mirror the AEO-9 taxonomy:** BAS (trend
continuation), ATS (AMS on-the-books policy), RAS (regional aspirational,
IEA APS/NZE + BNEF NZS upper cases). All three are baked into V1 via the
`scenario` column. BAS ≤ ATS ≤ RAS holds by construction (cumulative
scenario-floor chain, v20 of `Sales/run_sales_mix.py`).

**Why only sales gets pasted.** Per `STOCK_SALES_ARCHITECTURE.md` §3,
LEAP owns stock turnover and survival internally; LEAP derives stock
per (region × vehicle × fuel × year) from sales magnitude × LEAP's
survival kernel. Our `stock_by_fuel.csv` is a visualisation /
cross-check artefact for the wedge viewers and post-run validation, not
a paste target. See §E1 for the cross-check protocol.

## 1. Required alias maps (apply at every paste)

The Transport pipeline uses ASEAN-harmonised vocabulary; LEAP uses its
own. The inject team supplies these mappings via `input_to_LEAP_v2.py`
interactive prompts. They are stable across all five value pastes.

| CSV column | CSV value | LEAP identifier |
|---|---|---|
| `Country` | Brunei Darussalam | Brunei |
| `Country` | Cambodia | Cambodia |
| `Country` | Indonesia | Indonesia |
| `Country` | Lao PDR | Laos |
| `Country` | Malaysia | Malaysia |
| `Country` | Myanmar | Myanmar |
| `Country` | Philippines | Philippines |
| `Country` | Singapore | Singapore |
| `Country` | Thailand | Thailand |
| `Country` | Viet Nam | Vietnam |
| `vehicle_type` | LDV | PassengerCar |
| `vehicle_type` | 2W | Motorcyle *(note the LEAP-side typo: missing the 'c' in 'Motorcycle'. The Demand-tree branches under `Demand\Transport\Road\Motorcyle\*` carry this spelling; the alias must reproduce it exactly or the inject will silently miss the branch. Key-tree `Vehicles_Sales_Share\Motorcycle\*` spells it correctly — both targets must be handled, see §A1.)* |
| `vehicle_type` | Bus | Bus |
| `vehicle_type` | Truck | Truck |
| `fuel_type` | Gasoline | Gasoline |
| `fuel_type` | Electric | Electricity |
| `fuel_type` | HybridDiesel | Blended Diesel |
| `fuel_type` | NaturalGas | Natural Gas |
| `fuel_type` | Hydrogen | Hydrogen |

**Post-Lane-A (2026-05-20) note on fuel-label consolidation.** The
orchestrator no longer emits `Diesel`, `HydrogenFCV`, or `Hydrogen FCEV`
as CSV values. Lane A's Phase A normalises HybridDiesel as the single
diesel label and Hydrogen as the single hydrogen label across all
CSVs, so the alias map above is a one-to-one map (no consolidations
required at paste time). The historical `Diesel`/`HydrogenFCV`/`Hydrogen
FCEV` rows visible in pre-Lane-A `sales_mix.csv` / `stock_by_fuel.csv`
/ `starting_year_sales.csv` snapshots are now retired upstream. See §C1.

## A. Bulk value pastes

### A1. Sales fuel-share by scenario — `sales_mix.csv`

- **Source:** `Transport/LEAP Input/sales_mix.csv` (10,144 rows including 1,804 historical rows; 8,340 scenario rows).
- **Primary write target — Key tree (confirmed by 2026-05-20 inject canonical):** `Key\TransportDataStock\Vehicles_Sales_Share\<vehicle>\<fuel>`. The canonical's `Vehicles_Sales_Share` rows (362 rows out of 562) all land here under variable **Activity Level** (LEAP's name for the shares value on this branch). Per branch JSON `leap_branch_regions_collection_20260107_141354.json` there are 16 level-5 leaves.
- **Demand-tree linkage (no separate write needed):** the parallel Demand-tree branches `Demand\Transport\Road\<vehicle>\<fuel>` carry their own Sales-Share variable, but in the verified inject pattern LEAP reads those from the Key-tree value via standard reference linking. The 160 Demand-tree rows present in the 2026-05-20 canonical write **Mileage only**, never Sales Share. Do not duplicate Sales-Share writes onto the Demand tree — it will not change behaviour and risks last-writer-wins corruption.
- **Variable:** Activity Level (this is LEAP's label for Sales Share on the `Vehicles_Sales_Share` leaves; verified by `--blind` mode readback during the 2026-05-20 inject).
- **Scenario column:** the canonical carries a per-row `scenario` column. The framework filter at `nemo_read/inject_base.py::_filter_rows_for_scenario` separates BAS / ATS / RAS / Current Accounts so all three forward scenarios + the CA historical authoring run in one COM session. Run `input_to_LEAP_v2.py` three times only as a fallback for the legacy interactive path; the production path is the blind injector.
- **Year range:** 2000–2060.
- **Historical rows** (`scenario == historical`): authored into the Current Accounts scenario via the canonical builder. These rows MUST include explicit zero shares for any (vehicle × fuel) pair that exists in the LEAP demand tree but is absent from the per-AMS `fuel_summary_*.csv` source data. The pre-Lane-A canonical silently omitted these, which is the root cause of the IDN Bus/Truck Gasoline historical-stock anomaly documented in `Transport/Inject/INVESTIGATION_idn_hdv_gasoline_routing.md`. Post-Lane-A regen, verify the canonical Bus Gasoline + Truck Gasoline rows are present for BRN, IDN, LAO, VNM (Bus) and BRN, IDN, KHM, LAO, VNM (Truck).

### A2. Sales magnitude (vehicle-class totals) — `sales_magnitude.csv`

- **Source:** `Transport/LEAP Input/sales_magnitude.csv` (2,111 rows; deterministic, no scenario column — written to Current Accounts only).
- **Target (confirmed by 2026-05-20 inject canonical):** `Key\TransportDataStock\Vehicle_Sales\<vehicle>` — 40 rows (4 vehicle classes × 10 AMS) under variable **Activity Level**. The earlier hedge that this might sit on a separate Demand-tree branch is resolved: the verified path is the Key tree under the `Vehicle_Sales` (singular, not `Vehicles_Sales_Share`) sibling node. Verified by `--blind` readback during the 2026-05-20 inject pass.
- **Variable:** Activity Level (LEAP's label for the sales-magnitude value on this branch; CSV reports `sales_count` in absolute units, NOT thousand units — verify in the LEAP variable definition before paste and convert if LEAP expects thousands).
- **Key columns:** `Country, vehicle_type`; year column `Year`; value column `sales_count`.
- **Year range:** 2000–2060.
- **Provenance:** `source_method` column documents derivation per row (observed / stock_flow_gompertz / stock_flow_fe_ols / stock_flow_fe_ols_with_peer_floor) — informational, not load-bearing in LEAP.
- **Known issue post-2026-05-20 cycle:** the 2W rows show a ~10× spike at exactly 2025 across every AMS (root cause: cohort-initialisation gap from late `fuel_summary_motorcycle.csv` cutoffs; see `Transport/Inject/INVESTIGATION_2w_2025_spike.md`). Lane A's Phase B fix in the same cycle re-derives pre-cutoff sales from the Gompertz stock and should collapse 2025 2W sales to ~1.0–2.5× the 2024 level. Verify before locking the run.

### A3. Base-year fuel-mix anchor — `starting_year_sales.csv`

- **Source:** `Transport/LEAP Input/starting_year_sales.csv` (102 rows; 4 vehicle classes × 10 AMS at Year=2024; SGP Truck absent — see §C2).
- **Target:** Sales Share at base year on the same Vehicles_Sales_Share level-5 leaves as V1.
- **Variable:** Sales Share (base-year override).
- **Key columns:** `Country, vehicle_type, fuel_type`; value column `share_percent`; Year fixed at 2024.
- **Purpose:** locks the 2024 starting point used by LEAP's projection mechanics before scenario growth takes over. Each row carries a `provenance_note` documenting source-data tier (A / B / C) and any caveat.

### A4. Per-AMS 2020 mileage anchors — `mileage_anchors.csv`

- **Source:** `Transport/LEAP Input/mileage_anchors.csv` (40 rows; 4 vehicle classes × 10 AMS).
- **Schema (matches V1–V3 convention):** `Country` (full ASEAN names), `vehicle_type` (LDV / 2W / Bus / Truck), `mileage_km_per_year` (the value to paste), `confidence` (`source_confirmed_external` / `socioecon_predicted` / `hdv_socioecon_predicted`), `observed_year`, `source`, `source_url`, `leap_default_km_per_year` (informational — the prior LEAP global). Standard alias maps from §1 apply (Country → LEAP region name; `LDV` → `PassengerCar`; `2W` → `Motorcycle`).
- **Producer:** `Analysis/extract_mileage_anchors.py` reads `Analysis/mileage_sanity_ref_ams.csv` (the diagnostic-rich calibration surface) and emits this slim LEAP-ready file. Re-run after any mileage-calibration update.
- **Target (confirmed by 2026-05-20 inject canonical):** `Demand\Transport\Road\<vehicle>\<fuel>\<fuel>` — 160 rows in the canonical (4 vehicle classes × 5 fuels × 10 AMS minus a handful of missing-branch combinations, including Motorcycle Natural Gas which LEAP does not carry). Mileage is held flat 2025–2060 per row. The mileage value is vehicle-wide, identical across all fuels for a given (vehicle × AMS) pair; it gets written once per fuel sub-branch to populate every Demand-tree leaf the model exposes.
- **Variable:** Mileage (km/year or mi/year — confirm LEAP unit and convert if needed; CSV is in km/year).
- **What this replaces:** LEAP's four flat global defaults (LDV 32560 / 2W 28680 / Bus 32190 / Truck 24140; `leap_default_km_per_year` column preserves these per row for spot-checking). The anchors are held flat 2005–2060 once transcribed — no time-varying trajectory.
- **Why flat-anchor and not trajectory:** see retirement note in `Transport/Analysis/mileage_sanity_notes_ams.md` (commit `d73e1ca2`). Energy-demand growth across the AEO-9 horizon is dominated by stock growth and fuel-mix shift, not per-vehicle activity intensity, so holding mileage flat is the standard energy-modelling treatment.
- **Confidence mix:** 15 source_confirmed_external (LTA Singapore 2018, ERIA Phase II 2022 Table 3.6 for IDN+VNM Cars+Motorcycles, MIROS Malaysia 2020, Metro Manila 2020, plus the IDN/VNM truck and bus VKT anchors landed in commits `ec52d183` / `2bce5f94`); 14 hdv_socioecon_predicted (HDV driver-based fit, log-VKT ~ log GDP_pc + log veh_per_1000_capita); 11 socioecon_predicted (LDV/2W socioecon two-indicator OLS, log-VKT ~ log GDP_pc + urban_share). All 40 cells carry a non-null value — do not fall back to LEAP globals.

## B. LEAP-COM-session fixes (no CSV paste needed)

### B1. PPV CNG fuel-economy fix

- **What:** change Fuel Economy on PPV CNG from `30 MPGe` to `26 MPGe`.
- **Where:** Demand tree under the PPV (pickup / passenger-van) class with CNG fuel.
- **Why:** the 30 MPGe value was unverified internal default and overstates CNG efficiency for the PPV duty cycle. 26 MPGe aligns with US EPA fuel-economy data on dedicated-CNG light-truck duty (corroborated against the per-AMS FE panel in `Analysis/fuelecon_mileage_sanity_report.md`).
- **Source:** queued from Wave A close-out 2026-04-27 (see `Transport/Changelog/2026-04-27_sanity_close.md`).

### B2. ERIA 2022 Phase II citation cleanup

- **What:** edit the Mileage variable citation/source field, do not change values (V5 supersedes values).
- **Where:** anywhere LEAP cites "ERIA 2022 Phase II" against Mileage.
- **Edit:**
  - Cars and Motorcycles: keep the ERIA Phase II attribution **but scope-correct** — note that ERIA Phase II covers 5 ASEAN countries plus India (Indonesia, Malaysia, Philippines, Thailand, Viet Nam — Brunei, Cambodia, Lao PDR, Myanmar, Singapore not covered). Thailand-default fall-through applies for non-source countries in the ERIA methodology.
  - Bus and Truck: **retire** the ERIA Phase II attribution entirely. ERIA Phase II scope is cars and motorcycles only; the prior LEAP attribution for Bus/Truck is unsupported by the source.
- **Replacement citation for Bus/Truck:** the country-specific anchors documented per row in `Analysis/mileage_sanity_ref_ams.csv` (varies by AMS: LTA Singapore 2018 d_bdc4c6434e47b055de4b5f2fde10c1af, MIROS MRR 359 PUSPAKOM for MYS goods, GSO Vietnam bus-VKT, Pongthanaisawan & Sorapipatana 2007 for THA, IPCC AR6 WG3 Ch.10 + IEA GEVO 2025 regional inference for data-gap AMS).
- **Note on legacy LEAP MMR 12,904 / LAO 6,205 ERIA attributions:** these are unsupported (Myanmar and Lao PDR are outside ERIA Phase II scope) and should be retired in this same pass.

## C. Known gaps and naming inconsistencies (flag during paste)

### C1. Fuel-name normalisation (status: resolved upstream post-Lane-A)

Pre-Lane-A, the Transport orchestrator emitted more fuel-type labels
than LEAP needed (`Diesel` as a duplicate of `HybridDiesel` from the
HDV multi-fuel chain; `HydrogenFCV` and `Hydrogen FCEV` as zero-count
placeholders alongside `Hydrogen`). Lane A's Phase A consolidates the
fuel-type label set upstream: the orchestrator now uses `HybridDiesel`
as the single diesel label across `sales_mix.csv`, `stock_by_fuel.csv`,
and `starting_year_sales.csv`, and uses `Hydrogen` as the single
hydrogen label. The alias map in §1 carries a single one-to-one
mapping for each (`HybridDiesel → Blended Diesel`, `Hydrogen →
Hydrogen`), and no collapse logic is needed at paste time.

Verification step before the next inject: confirm
`Transport/LEAP Input/sales_mix.csv` and `stock_by_fuel.csv` no longer
contain rows with `fuel_type in {Diesel, HydrogenFCV, Hydrogen FCEV}`.
A simple `df.fuel_type.unique()` check should return only the six
canonical labels from §1.

### C2. SGP Truck — starting-year row absent

`starting_year_sales.csv` has no Singapore Truck row because the underlying `Sales/SGP/fuel_summary_truck.csv` is a placeholder series (`count=1` for every year 2006–2025; reclassified as whole-series Tier C in §4 of `Transport/NEXT_STAGE.md`). For the base-year fuel-mix paste, fall back to a regional-peer assumption (Singapore goods-vehicle fleet at base year ≈ 100% Blended Diesel is a defensible placeholder) and note the override. Data.gov.sg 2018+ goods-vehicle pull is queued in NEXT_STAGE to lift this to Tier A/B in a follow-up.

### C3. Demand-tree write-path requirement (`--blind` mode mandatory)

The 2026-05-20 inject pass surfaced a hard requirement: the framework's
cached `branch.Variable(...)` write path silently no-ops on
`Key\TransportDataStock\...` and `Demand\Transport\...` branches —
the inject logs `[OK]` but nothing persists in the LEAP file. The
working invocation profile is **blind mode** (`--blind` flag), which
re-resolves each branch via direct `leap.Branches(FullName)` and
writes correctly. The legacy cached path remains usable only for
`Demand\Industry\...` and other branches not under the two trees
listed above.

Knock-on implication for `input_to_LEAP_v2.py`: if the legacy
interactive driver is invoked as a fallback for the production
blind-injector path, verify that each Vehicles_Sales_Share leaf
actually carries the post-paste expression by opening the leaf in the
LEAP UI before locking the run. The driver does not currently emit
the "silently no-oped" warning, and a partial-paste outcome would
look successful in the driver log.

See `Transport/Inject/TRANSPORT_INJECT_SOP.md` for the full blind-mode
invocation profile and the three guardrails the inject framework
enforces post-2026-05-20 (scenario-column filter, decimal-separator
regional guard, per-scenario readback).

### C4. SGP LDV 2024 starting-year provenance flag

Singapore LDV 2024 carries an LTA-data flag: the LTA first-registration count appears to include re-registrations, producing a 2× of normalised LTA monthly first-registration aggregates. Flagged in the `provenance_note` for the inject team to spot-check during paste; not a blocker.

## D. Verification (post-paste, before locking the scenario run)

| # | Check | Expected result |
|---|---|---|
| V-1 | Sum of fuel shares per (region × vehicle × scenario × year) on Vehicles_Sales_Share | 100% (or `100 ± 0.01`) |
| V-2 | BAS ≤ ATS ≤ RAS for Electric share on Vehicles_Sales_Share at 2030, 2040, 2060 | Holds for every (region × vehicle) |
| V-3 | Sales magnitude monotonic-ish for LDV, 2W across all AMS (no sudden zero years) | Holds; PHL 2W 2025 spike is documented and acceptable |
| V-4 | Mileage values match the per-AMS anchors at 2020, 2030, 2060 | Flat-anchor: 2020 = 2030 = 2060 per AMS × class |
| V-5 | RAS Electric share saturation at locked target years (SGP 2033, MYS/THA 2035, IDN/VNM 2038, PHL/BRN 2040, KHM/LAO/MMR 2042 for LDV; 2W leads by 2–3 yrs) | Reaches 100% within ±1 year on Vehicles_Sales_Share |
| V-6 | Tier-1 Truck RAS at 2060 (SGP/MYS/THA) | 40% Electric + 8% Hydrogen + 52% Blended Diesel (Wave A close-out verification) |
| V-7 | LEAP-computed Vehicle_Stock_Share vs our `stock_by_fuel.csv` at 2030, 2050 | Within ±5 pp per fuel-share; large divergence flags a survival-kernel mismatch (we assume the LEAP 26-yr generic; see §E1) |

If any check fails, do not lock the run — flag back to the Transport
modelling track; the source CSVs are read-only from the inject side per
the multi-instance protocol in `CLAUDE.md`.

## E. Optional cross-check (informational only)

### E1. Stock fuel-share cross-check — `stock_by_fuel.csv`

- **Source:** `Transport/LEAP Input/stock_by_fuel.csv` (18,734 rows across BAS/ATS/RAS, 4 vehicle classes × 10 AMS × 2005–2060).
- **Where it would map:** `Key Assumptions\TransportDataStock\Vehicle_Stock_Share\<vehicle>\<fuel>` (16 level-5 leaves, per branch JSON `leap_branch_regions_collection_20260107_110605.json`).
- **Why this is NOT a paste:** per `Transport/STOCK_SALES_ARCHITECTURE.md` §3, LEAP derives stock per (vehicle × fuel × year) from sales magnitude × LEAP's survival kernel. Pasting our pre-computed stock shares would override LEAP's survival logic and double-count the stock-flow identity.
- **What to do instead:** after the scenario run, export LEAP's computed Vehicle_Stock_Share values and compare against `stock_by_fuel.csv` at a few spot years (2030, 2050) per V-7 above. Our stock-by-fuel is computed via Weibull-convolved sales integration against a 26-yr generic survival kernel (the placeholder used in `ev_adoption_base.py`); large divergence between ours and LEAP's likely reflects a different survival-kernel assumption on the LEAP side, which is fine but worth documenting.
- **Use of this artefact in the Transport repo:** drives the wedge viewers `STOCK_WEDGES.jsx` and `POLICY_WEDGES.jsx`, plus the post-run sanity sheets `Analysis/sanity_hdv_projection.py` and `Analysis/sanity_ldv_2w_projection.py`.
