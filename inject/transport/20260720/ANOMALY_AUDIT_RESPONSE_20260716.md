# Transport — Response to the Canon-Handover Anomaly Audit (2026-07-16)

Our adjudication of every item in the LEAP inject team's
`ANOMALY_AUDIT_TRANSPORT_20260704.md` (delivered in
`.inbox/transport_canon_handover_20260704.zip`, unpacked to
[canon_handover_20260704/](canon_handover_20260704/)). This is the
data/modelling team's reply: each item is judged against **our current
repo** (four LEAP-input CSVs regenerated 2026-07-02, DESIGN.md v29,
plus our own `Analysis/input_anomaly_audit_2026-07-02.md`). Implied
fixes are **listed, not applied** — CSV regeneration and packaging are a
separate track, held per user direction.

**Method.** Each of 20 items was independently investigated against our
data and then adversarially verified by a second reviewer; 19 completed
both passes at high confidence with the verifier agreeing on ownership,
current status, and intended value. B6 (green cosmetic cluster) was
adjudicated directly. Evidence for each item is our own file + values,
cited inline.

---

## 1. Headline

- **Nothing in our current four CSVs reproduces the Part-A "wrong value"
  defects.** Every data-traceable Part-A item (A1, A4, A6a, A6b) is a
  **stale live-model paste** from our May-2026 drop or an **inject-side
  LEAP formula/plumbing** artifact. Our 2026-07-02 regeneration already
  cleaned the data-side root causes; re-pasting our current CSVs +
  re-deriving stock resolves them.
- **The single most consequential finding is an inverted framing on
  A5/§7.1.** The Indonesia Truck-Natural-Gas Fuel Economy of **5 is the
  correct value; the fleet-wide 12 is the actual defect.** Our
  benchmarked FE reference puts CNG trucks at ~5 MPGe; 12 MPGe (628
  MJ/100 km) is physically implausible for CNG and exactly equals the
  Hydrogen-truck value. Recommendation: set **5 uniformly across all 10
  AMS + Current Accounts** — do *not* revert Indonesia to 12.
- **Ownership split (20 items):** 14 inject-side / cross-tree (we flag,
  they act) · 4 ours-recommendation (we supply the value) · 1
  methodology decision for the modelling lead (B1 Road emissions) · 1
  green cosmetic cluster.
- **B1 Road tailpipe emissions is out of scope here** — handled outside
  this pipeline per modelling-lead direction (2026-07-16); no
  emission-factor set ships from this track. See §5.
- **Every other finding was treated this cycle** (§5–§6). The three
  sales/mileage CSVs are unchanged (they were clean); `starting_year_sales.csv`
  gained the 2024 `stock_count` column (README §7.6 — the `BaseYear_StockData`
  fix); a per-class survival profile (`survival_profile.csv`) was emitted; and
  every inject-side action is collected in `LEAP_action_items.md` §F.

---

## 2. Part A — "Incorrectly inputted" (our verdicts)

| # | Item | Ownership | In our current data? | Our verdict (one line) |
|---|---|---|---|---|
| **A1** | Truck NG `Sales` cites the Electricity sales-share key | inject-side (LEAP formula) | Never — we don't author the Sales formula | Confirmed defect; our `sales_mix.csv` already carries **distinct** Truck NG and Truck Electric shares. Re-point the formula **and** re-paste our current NG shares. |
| **A4** | CA Road `Stock` pasted across vehicle classes (26–177×) | inject-side (LEAP derives Stock) | Never — Stock is not a paste target (LEAP_action_items §X1) | Stale/foreign paste. Our `stock_by_fuel.csv` is provably **class-distinct** (0 non-zero byte-identical Bus/LDV/Truck cells). Let LEAP re-derive stock from our sales × survival. |
| **A5** | Truck NG Fuel Economy 12→5, Indonesia only | ours-recommendation (FE is LEAP-authored) | Never — FE not in our four CSVs | **Framing inverted: 5 is right, 12 is the defect.** `fuelecon_sanity_ref_fe.csv`: Truck NG = 5 MPGe ≈ 1508 MJ/100 km (benchmark-central). Set **5 fleet-wide + CA**. |
| **A6a** | Indonesia 2015 Stock = 1/129.4 of neighbours (5 series) | inject-side (CA Stock paste) | Never — our source stock is smooth | `Projection_Stock_IDN.json` 2014→2015→2016 ratios 0.93–1.02, no divot. Single-cell paste slip on the LEAP side; re-paste from our clean data. |
| **A6b** | Mid-series ≥5× splices (THA Gasoline 514×, MYS Electric 191×) | inject-side (CA Stock paste) | Never in current data (mechanism fixed 2026-07-02) | No fossil splice exists in our data; every ≥5× step is a genuine **EV ramp off a near-zero base**. The named splices (382→196,447; 25→4,777) appear nowhere in our current CSVs. |
| **A9a** | Philippines aviation FEI trailing +1%/yr | inject-side (Domestic Air) | Never — outside Road scope | Not ours; no aviation FEI in any of our CSVs. If the aviation owner acts, strip the trailing `1%` growth arg so PHL holds flat like every region. |
| **A9b** | Brunei PassengerCar Diesel `Mileage Correction Factor` = Interp(2024,1,2030,0.9) | inject-side (LEAP variable) | Never — we don't author this variable | Stray/forgotten test edit. Our only BRN correction is `active_fleet_correction.csv` LDV = **1.00** (high conf). Revert the 4 BRN rows to constant 1. |
| **A9c** | PassengerCar `First Sales Year` = 2024 vs BaseYear elsewhere | inject-side (CA-only vintaging) | Never — we don't author First Sales Year | Cosmetic literal-vs-symbolic split; base year **is** 2024, so both resolve identically → zero numerical effect. Harmonise to `BaseYear` for tidiness. |
| **A11** | CR `_x000D_` in Inland Waterways FEI `If()` (10 rows) | inject-side (IW FEI) | Never — our 5 CSVs are CRLF-clean, 0 embedded CR | Excel Alt+Enter baked into IW FEI text. Our authored files carry no stray CR / `_x000D_` on either count. |
| **A12** | SAF Indonesia/Thailand comment-provenance swap | inject-side (Domestic Air SAF) | Never — outside Road scope | Real annotation defect on the SAF Fuel-Share branch; aviation team's to fix. `POLICY_LANDSCAPE.md` holds no SAF content and cannot arbitrate it. |
| **A13** | `Motorcyle` (Demand) vs `Motorcycle` (Key) name split | inject-side (LEAP naming) | Never — we author the neutral token `2W` | We are fully insulated; the adapter owns the `2W → Motorcyle` translation. We must **not** start writing either LEAP spelling into our CSVs. |
| **A14** | `Demand\Transport_` underscore self-refs + Rail dollar-vintage | inject-side (Key/plumbing) | Never — our CSVs carry no branch paths / no USD basis | Both are LEAP-side. Our Road-scope, currency-free count/share/km/stock CSVs reference neither a `Transport_` path nor any dollar vintage. Handover already assigns the underscore to the inject team. |

## 3. Part B — "Empty but important" (our verdicts)

| # | Item | Grade | Ownership | Our verdict (one line) |
|---|---|---|---|---|
| **B1** | Road has **zero** emission leaves | 🔴 RED | mixed / **decision** | Real, live gap; structural build is inject/central. We recommend **IPCC 2006 Tier 1 fuel-based** CO₂/CH₄/N₂O leaves (per-fuel, region-uniform, biofuel fractions biogenic-zero, none on Electricity/Hydrogen). **Needs your call — §5.** |
| **B2** | Scrappage panel all boilerplate (fleets never retire) | 🟡 | ours-recommendation | Material for us: our V2 sales are back-derived on per-class **Weibull kernels**; §C5's "LEAP stock ≈ on-road fleet" holds only if LEAP retires vehicles. Recommend LEAP populate its survival profile from our kernels (LDV 15.5/3.0, 2W 12.0/2.5, Bus/Truck 18.0/3.5). |
| **B3** | Fuel Economy is a region-uniform template | 🟡 | ours-recommendation | **Intended, not a defect.** Our FE benchmarks are ASEAN-regional (15/16 within range); country variation is routed through per-AMS `mileage_anchors.csv` + active-fleet, which §6.3 confirms yields economically-ordered energy. Keep uniform; the only per-region FE (IDN Truck NG) should be removed per A5. |
| **B4** | SAF Final Energy Intensity evaluates to 0 | 🟡 | inject-side (Domestic Air) | Aviation methodology issue (SAF FEI anchored to `Value(2019)=0`). Outside Road scope; we hold no aviation input. Direction: re-anchor SAF FEI to the Jet Kerosene level so the blend ramp yields real SAF energy. |
| **B5** | SAF CO₂ accounted as fossil (`0.207*71.5`) | 🟡 | inject-side (emission leaf) | Valid asymmetry (Biodiesel is 100% biogenic; SAF is fossil). Aviation/emissions team's to fix. We concur with the direction: **SAF CO₂ should be biogenic like Biodiesel** — the B1 recommendation applies the same rule to road biofuel fractions. |
| **B6** | Green cluster (IW Kerosene 0 pollutants; dead result-vars; TL/Base Template mileage) | 🟢 | inject-side cosmetic | All cosmetic/intentional. Confirmed **our five deliverables carry zero Timor Leste / Base Template rows** (exactly the 10 ASEAN members) — TL exclusion is correct and deliberate. |

---

## 4. Direct answers to the README's review questions (§7)

- **§7.1 — Truck NG FE 12 vs 5 (Indonesia).** **5 is the defensible
  value; 12 is the slip.** Set 5 MPGe (~1508 MJ/100 km) **uniformly**
  across all 10 AMS and Current Accounts. Do not keep 12 anywhere; the
  fleet-wide 12 equals the Hydrogen-truck FE and is implausibly
  efficient for CNG. (Source: `Analysis/fuelecon_sanity_ref_fe.csv`;
  NREL CNG HDV + ICCT 2022.)
- **§7.2 — Road tailpipe emissions.** **Out of scope for this track** —
  being handled outside this pipeline per modelling-lead direction
  (2026-07-16). For the record, our recommendation was: IPCC 2006 Tier 1
  **fuel-based** factors via LEAP's built-in TED (per-fuel, region-uniform),
  mirroring the Air/IW/Rail per-fuel Loading structure; biofuel fractions
  biogenic CO₂; no tailpipe leaf on Electricity/Hydrogen. No factor set
  ships from this track.
- **§7.3 — Motorcyle/Motorcycle spelling split (= A13).** No action on
  our side; our CSVs use the neutral `2W` token and the adapter owns the
  `2W → Motorcyle` mapping (and the Key-side `Motorcycle`). We must not
  write either LEAP spelling into our source CSVs.
- **§7.4 — Blended Gasoline / Gasoline fuel-name split.** Same insulation
  as §7.3: our CSVs carry neutral source fuels (`Gasoline`, `HybridDiesel`),
  and the adapter maps them (`Gasoline → Blended Gasoline` on the Demand
  tree, `Gasoline` on the Key share tree). **Heads-up for the inject side:**
  your own `CSV_AUTHORING_GUIDE §3` flags that the adapter's
  `LEAP_AVAILABLE_FUELS_PER_VEHICLE` still uses the old `Gasoline` name and
  must be renamed to `Blended Gasoline` before the next Demand-tree push,
  or blind-mode writes will target a FullName that no longer exists.
- **§7.5 — Orphan hydrogen PassengerCar slot.** Keep it **zero** (or
  drop the branch). No scenario in our design puts H2 into passenger
  cars — `ev_policy_targets.csv` and `RAS_JUSTIFICATION.md` confine H2
  to long-haul truck / intercity bus. Our `sales_mix.csv` emits zero
  LDV×Hydrogen rows. The adapter's existing drop of PassengerCar×Hydrogen
  is correct.
- **§7.6 — Base-year stock (`stock_count`). DONE this cycle.** Added a
  2024 `stock_count` per (Country, vehicle_type) to
  `starting_year_sales.csv`, aggregated across fuels from our stock model.
  Validated against LEAP's held values (BRN Bus 2,188 vs 2,300; CAM Bus
  65,996 vs 69,600; IDN Bus 298,260 vs 273,800 — all within ~5–9%, a
  fleet-stock not a sales magnitude). See `LEAP_action_items.md` §A5 / paste
  V5. The value is per-vehicle (repeated across fuel rows) — take once per
  (ams, vehicle), do not sum.
- **§7.7 — SAF mandate trajectories.** Nothing to contribute. SAF is
  aviation policy, outside our Road scope; our only blend-mandate
  content is **road** biodiesel (B40/B20/B10). The
  Indonesia/Malaysia/Thailand `InterpFSY` rows stay the aviation team's.
- **§7.8 — `Demand\Transport_` underscore self-refs (= A14, FYI).**
  Internal to the inject team, as the handover states. Confirmed nothing
  in our five CSVs references a `Transport_` path — no action from us.

---

## 5. Dispositions actioned this cycle + the one out-of-scope item

**B1 — Road tailpipe emissions: OUT OF SCOPE here.** Per modelling-lead
direction (2026-07-16) this is being handled outside this pipeline, so
no emission-factor set is shipped from the transport-data track this
cycle. (For the record, had it been in scope, our recommendation was
IPCC 2006 Tier 1 fuel-based factors via LEAP's TED, per-fuel and
region-uniform, biofuel fractions biogenic-zero.)

Every other finding was treated. The two recommendations that produced
artefacts on our side:

- **A5 / B3 → F3.** Truck NG FE set to **5 MPGe fleet-wide** as a new
  LEAP action item (`LEAP_action_items.md` §B3/F3); FE otherwise kept
  region-uniform (the lone IDN Truck-NG override is removed by making
  F3 uniform).
- **B2 → V6.** Per-age survival profile emitted to
  `LEAP Input/survival_profile.csv` (`Analysis/emit_survival_profile.py`)
  so the inject team can replace the never-retire scrappage panel with
  our per-class Weibull kernels (`LEAP_action_items.md` §A6).

---

## 6. What changed on our side (this cycle)

- **The three sales/mileage CSVs** (`sales_mix`, `sales_magnitude`,
  `mileage_anchors`): **no change** — every Part-A data defect is a stale
  live-model paste or inject-side artifact, not a flaw in our data.
- **`starting_year_sales.csv`: added the 2024 `stock_count` column**
  (README §7.6 / SPEC §4b — the `BaseYear_StockData` fleet-vs-sales fix).
  Per (Country, vehicle_type), aggregated across fuels from our stock
  model, repeated across the vehicle's fuel rows. Validated against LEAP's
  held values (BRN Bus 2,188 vs 2,300; IDN Bus 298,260 vs 273,800).
  Producer: `Analysis/extract_starting_year_sales.py`. → paste V5.
- **`survival_profile.csv`: new** per-class Weibull survival table
  (B2 aid). → paste V6.
- **`LEAP Input/LEAP_action_items.md`: updated** — new V5/V6 pastes, F3
  (Truck NG FE 12→5), and a full **§F dispositions checklist** of the
  inject-side actions from this adjudication.
- **Inject/central-side actions (they apply, not us):** the full list is
  in `LEAP_action_items.md` §F — re-point the Truck-NG Sales formula +
  re-paste our NG shares (A1); re-derive CA Stock rather than paste
  (A4/A6a/A6b); revert BRN mileage-correction (A9b) and PHL aviation FEI
  (A9a); F3 fleet-wide (A5); harmonise PassengerCar First Sales Year
  (A9c); strip IW CR artifacts (A11); fix SAF provenance + CO₂ basis
  (A12/B4/B5); populate the survival panel from V6 (B2).

*Prepared by the AEO-9 Transport data team. Questions →
yudiandra.y@gmail.com. Structure references use the branch names in
`canon_handover_20260704/transport_tree.txt`.*
