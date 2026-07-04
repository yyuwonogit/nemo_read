# Anomaly audit — your slice (Fossil supply fuels & reserves)

This is the **fossil-team slice of the full canon anomaly audit** run on
2026-07-04 over the live model (LEAP area `aeo9_v0.67_w_results`, four
scenarios: **Current Accounts, Baseline Simulation, AMS Target Scenario,
Regional Aspiration Scenario**). The master audit is a cross-sector list
of authoring defects; below are only the items that land on **branches
your team owns or authors** — the fossil supply fuels and reserves:
the 5 coals, Crude Oil, Natural Gas, Natural Gas Liquids, Nuclear, and
the refined/secondary petroleum products (Diesel, Gasoline, Kerosene,
Jet Kerosene, LPG, Residual Fuel Oil, Naphtha, Bitumen, Avgas, Ammonia,
etc.). Each item keeps the master audit's verbatim finding, its counts,
its **NEW/KNOWN** and **VERIFIED/SUSPICIOUS** tags, and (for Part B) its
🔴/🟡/🟢 grade — **nothing here is invented, re-counted, or re-tagged**.
Part A is authored-value anomalies (incorrect inputs); Part B is
empty-but-important gaps. These are **review requests, not fixes** —
your team is the one who can judge which are deliberate and supply the
correct national data. Where a defect actually lives in a branch your
sector merely *references* (owned by another team upstream), it carries
a **Cross-tree note** so you know it is not yours to author.

---

## Part A — Incorrectly inputted (anomalies in authored values)

### A2. Region permutation (one country's data/comment landed on another)

- **NEW · VERIFIED — Crude Oil `Additions to Reserves` is region-scrambled in
  Baseline + AMS Target.** RAS holds the 10 values correctly aligned; Baseline
  and ATS hold them shuffled, and the source comments prove it: Malaysia gets
  Indonesia's value + "SKK Migas" (Indonesia's regulator), Philippines gets
  Malaysia's "PETRONAS Activity Outlook", Laos gets Thailand's "DMF Thailand",
  Indonesia (a major producer) gets "0 ? No commercial production", Myanmar
  gets Laos's "Landlocked no upstream". Extending the check to all fuels:
  **Crude Oil is the only permuted fuel** — the other comment-region hits (RFO
  "Derived from SG CIF crude" ×22, Gasoline "Platts FOB Singapore") are
  legitimate benchmark citations. *18 rows. Resources.* (This is the defect the
  fossil guide §7.3 flagged; now proven via the comments.)

### A3. Separator / decimal-locale violations (§A.15 / §A.20)

- **NEW · VERIFIED — semicolon-form `Data()` in live code.** The same
  Baseline+ATS Crude Oil ATR layer is committed as `Data(2024; 1.1)` — the
  forbidden semicolon list-separator, in the area itself. The RAS copy uses
  correct commas → the two layers came in through different authoring paths.
  *20 rows. Resources.*
- **KNOWN + NEW extent — comma-decimal arithmetic beyond the ledger.** Ledger
  #26 recorded 9 Philippines Natural Gas rows (`…*1,0551`). The class actually
  spans **8 more Philippine fuels** — Avgas `…/(159*44,8000*0,7300)`, Bitumen,
  Charcoal `…/28,8800`, Jet Kerosene, Kerosene, LPG, Naphtha, Residual Fuel
  Oil — comma-decimals inside parenthesised multiplication where they cannot be
  list separators. *58 rows total in scope, all Philippines. Resources.*
  Bonus suspicion: even de-comma'd, the NG `*1.0551` looks **inverted** (GJ↔MMBTU
  conversion should divide) — needs a human math check.
  - **Cross-tree note:** of the 8 secondary fuels above, **Charcoal** is a
    bioenergy-owned fuel (not in your fossil secondary-products list) — the
    Charcoal `…/28,8800` rows are the same defect class but that fuel is
    authored by the bioenergy team; the other 7 (Avgas, Bitumen, Jet Kerosene,
    Kerosene, LPG, Naphtha, Residual Fuel Oil) plus Natural Gas are yours.
    This finding is carried verbatim (spanning both teams).

### A7. Cross-region outliers / unit slips

- **NEW · SUSPICIOUS — NGL Brunei Additions to Reserves = 0.2237 bare "Metric
  Tonne"** (0.22 t as a national reserve is meaningless — lost its Billion-BOE
  scale tag). *4 rows. Resources.*

### A13. Naming / typos

- **KNOWN — `Metalurgical Coke`** (referenced by name in 48 Import Cost
  expressions — a rename must update them). Resources.
  - **Your slice:** `Resources\Secondary\Metalurgical Coke` is one of your
    secondary coal products (LEAP's misspelling — README §2 says author it
    verbatim). The master audit's A13 groups this with `Motorcyle` (transport)
    and a residential comment typo; only the Metalurgical Coke sub-item is
    yours, carried here verbatim with its KNOWN tag. If you ever correct the
    spelling, the 48 cross-fuel Import Cost expressions that cite it by name
    must be updated in the same edit or they break.

---

## Part B — Empty but important (graded)

### 🔴 RED — breaks the calc or actively distorts LP/results in the 4 scenarios now

- **Ammonia RAS Import Cost = `0.001` overriding a real price.** *(KNOWN-adjacent
  · Resources)* CA/Baseline/ATS hold ~$1/kg (`(720+1400)/2*ConvUnits…`); RAS —
  the scenario whose imports the LP optimizes — holds `0.001 ? Placeholder
  cost`. Blast Furnace Gas 0.001 ×12 too. **Mechanism:** if any RAS tech
  consumes ammonia (H2-economy), the solver sources it via near-free imports
  instead of production, silently distorting the RAS energy balance and cost.

- **Zero-cost open supply/import routes.** *(KNOWN #24 · Resources)* In RAS,
  **191 (fuel,region) pairs have Maximum Production ≠ 0 with Production Cost =
  0** (incl. Nuclear at Unlimited + $0), and **95 pairs have open Maximum
  Imports with Import Cost = 0** (Refinery Feedstocks/Gas, Renewable Diesel,
  Arable/Perennial ×12). **Mechanism:** a cap-open, cost-zero route is a free
  lunch the LP exploits regardless of realism — the exact mechanism behind the
  2026-05-18 biodiesel-to-Timor-Leste and 2026-05-19 POME incidents.
  - **Your slice:** the fossil-owned pair inside this list is **Nuclear**
    (`Resources\Primary\Nuclear` at Maximum Production = Unlimited + Production
    Cost = 0, all scenarios — this is the same free-supply shape your README
    §7.7 asks you to rule on) and the **Refinery Feedstocks / Refinery Gas**
    open-import-at-zero-cost routes. **Cross-tree note:** the rest of this
    finding's pairs (Renewable Diesel, Arable/Perennial land pseudo-fuels, and
    the bulk of the 191/95) belong to bioenergy/power — carried verbatim here
    because the finding spans the whole Resources tree; only Nuclear + the
    refinery-feed import routes are yours.

### 🟡 YELLOW — placeholder/template values silently shaping results (wrong numbers, not broken mechanics)

**Resources (your fuels)**

- **Unlimited caps on Natural Gas + all 5 coals (12/12) in every scenario** —
  the fossil canonical authors costs but no caps → un-capped fossil supply (no
  depletion realism) and 1e12 LP-conditioning pollution.
- **Minimum Imports hold-last floors** — 95 RAS rows ending "2022, V>0" extend V
  as a forced import floor to 2060 (Singapore RFO 53,538 kTOE). Standing
  infeasibility/distortion risk as demand evolves.
- **Consumer prices ~95 % zero** on the branches demand regressions reference
  (1,130 of 1,188 cells; Bagasse/coals/NG/MSW Industrial price 44/44 zero).
  **Mechanism:** the Exp/Ln price-elasticity shells evaluate `Ln(0)` → undefined
  or garbage, so fuel-switching response is silently priced at zero. (Same class
  hits industry's referenced prices.)
  - **Cross-tree note:** these Consumer Price cells live on your Resources fuels
    (coals, NG among them), but they are **read by the demand sectors' price
    regressions** (industry, etc.) — the price you author here is upstream of
    their fuel-switching response. Bagasse/MSW inside the same 44/44 count are
    bioenergy/power fuels; the coal + NG cells are yours.

**Resources (referenced by your sector but owned elsewhere — cross-tree)**

- **NEW — Electricity Import Cost = flat `100`** (2020 USD/MWh) in all 12 regions
  × 4 scenarios — the only price for cross-border power trade, a placeholder;
  RAS/CNZ enable the full trade route set, so the build-vs-import decision runs
  on a round template number.
  - **Cross-tree note:** `Resources\Secondary\Electricity` is a **power-team**
    fuel, not yours — listed only so you know the number your refined-fuel and
    gas supply competes against in the trade/dispatch decision is a placeholder.
- **`Unlimited ? tbc` placeholder caps** survive on Biomass/Geothermal/Large
  Hydro/MSW (37 rows) → un-capped renewable supply in the very RAS scenario
  whose RE targets those caps should bind.
  - **Cross-tree note:** Biomass/Geothermal/Large Hydro/MSW are
    **bioenergy/power** primary fuels — carried here only because it is the same
    `Unlimited`-cap class as your NG+coals item above (same §4/§A.11 sentinel
    risk); the fix is theirs to author, not yours.

### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

- **Resources:** all-zero series on *closed* routes (cost 0 paired with cap 0 —
  unreachable today, but a tripwire target: reopening a cap without its cost row
  recreates the RED #2 exploit); "U.S. Dollar" vintage-less units (mostly on
  zero cells).
  - **Your slice:** many of the closed-route zero pairs are your refined
    products (e.g. Diesel/Gasoline/Kerosene/LPG/RFO Maximum Production = 0 in
    RAS, deliberately fed by refinery Transformation instead — see README §7.4).
    They are green **only while both cap and cost stay zero**: if you ever open a
    product cap, author its cost in the same edit or you recreate the 🔴
    zero-cost-open-route exploit.

---

## Highest-leverage for your team

1. **De-scramble the Crude Oil `Additions to Reserves` permutation (A2)** —
   Baseline + ATS hold the 10 country values shuffled (Malaysia has Indonesia's
   SKK-Migas number, etc.); RAS is already correctly aligned, so the correct
   values are in-model to copy. *18 rows, clear correct target.*
2. **Re-author the semicolon / comma-decimal Philippines rows (A3)** — the
   `Data(2024; 1.1)` crude ATR (20 rows) and the `*1,0551` / `44,8000` /
   Philippine consumer-price comma-decimals (58 rows) are committed
   locale-violations with defined correct forms; also settle the suspected
   inverted `*1.0551` GJ↔MMBTU factor with a human math check.
3. **Kill the Ammonia RAS Import Cost `0.001` placeholder (🔴)** — restore the
   real ~$1/kg price CA/Baseline/ATS already hold, so any H2-economy ammonia use
   in RAS doesn't source near-free imports; same for Blast Furnace Gas 0.001.
4. **Send defensible caps for NG + the 5 coals (🟡 Unlimited caps)** — the
   single highest-value gap: `Maximum Production = Unlimited` on Natural Gas and
   all 5 coal grades in every region/scenario means uncapped (and, where
   Production Cost = 0, free) fossil supply plus 1e12 LP pollution. `0` caps for
   genuine non-producers fix supply realism and the sentinel at once.
5. **Rule on Nuclear (🔴 zero-cost route) and the NGL Brunei bare-tonne reserve
   (A7)** — decide whether Nuclear should stay Unlimited + $0 (or carry a finite
   Production Cost), and restore the Billion-BOE scale tag lost on NGL Brunei's
   `Data(2019, 0.2237)` Additions to Reserves.
6. **Review the Minimum Imports hold-last floors (🟡)** — annotate which of the
   95 RAS floors (e.g. Singapore RFO 53,538 kTOE, Singapore/Thailand Crude Oil)
   are deliberate refinery-feed floors vs stale historical series that should
   stop binding after 2022.
