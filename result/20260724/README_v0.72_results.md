# aeo9 v0.72 — Demand results (harvest 2026-07-23)

Source drop: [mailbox/20260724/v_0.72 Demand Result.xlsx](../../mailbox/20260724/v_0.72%20Demand%20Result.xlsx)
Pipeline: [_tidy_results_v072.py](_tidy_results_v072.py) (adapted from
[result/20260709/_tidy_results.py](../20260709/_tidy_results.py))

Supersedes v0.71 as the latest demand harvest. **Demand only** — the v0.75 /
v0.76 drops in `outbox/20260717/` and `mailbox/20260722/` are power-side.

## What's in the source

| | |
|---|---|
| Sheets | `Demand BAS`, `Demand ATS`, `Demand RAS` |
| Variable | Final Energy Demand |
| Native unit | **Billion Gigajoules** (1 = 1000 PJ = 1 EJ) — v0.71 was Million Gigajoules |
| Regions | 10 AMS (no Timor Leste — disabled in calc) |
| Years | **2005–2060, every year** (v0.71 carried milestone years only) |
| Leaves | BAS 327, ATS 348, RAS 369 |

## Verification

Leaf sums reconcile **exactly** (< 1e-6 EJ) against each sheet's own `Total`
row, for all 3 scenarios × 4 sampled years. Asserted in the pipeline; it exits
non-zero on any mismatch or unclassified leaf. Every leaf classifies
confidently — zero unknown carriers.

## Two export quirks — read before using

### 1. Mixed export shape (handled)

`Demand BAS` and `Demand ATS` were exported with **flat full branch paths**;
`Demand RAS` with an **indented tree** (3 spaces per level). Different LEAP UI
export settings, same underlying grain. The pipeline parses both to full paths.

### 2. 100-character path truncation in the flat sheets (repaired)

LEAP clips the flat branch-path string at exactly 100 characters, mangling 12
deep Industry leaf labels per flat sheet:

```
...Direct Process Heating\Liquid FF\Residual Fue      -> ...\Residual Fuel Oil
...Indirect Process Heating\Others\Hard Coal Bri      -> ...\Hard Coal Briquettes
...Indirect Process Heating\Liquid FF\Residual        -> ...\Residual Fuel Oil   (99 chars — trailing space stripped)
```

**Values are unaffected — this is a label defect only.** Repaired against the
RAS tree roster (immune: each cell holds only the leaf name) by re-truncating
every long RAS path the same way to build the lookup key. 13 keys, all mutually
unique; zero ambiguous, zero unmatched — asserted. Repaired rows carry
`path_repaired=True`.

### 3. Sheet-shape asymmetry (NOT repairable — flagged in the data)

Five Industry branches are a **single leaf in BAS/ATS but split one level
deeper in RAS**. Two are harmless (single child, same grain):
`Cement Kiln Conventional\Electricity` and `EAF\Scrap` — both electricity.

The other three genuinely aggregate several fuels in BAS/ATS:

| Branch | RAS splits into | BAS 2060 | ATS 2060 |
|---|---|---|---|
| `Crude Steel\BOF\BF` | Coal Bituminous, Electricity, Metalurgical Coke, Natural Gas, Residual Fuel Oil | 7,769 PJ | 5,504 PJ |
| `Cement\Clinker\Cement Kiln Conventional\Heat` | Biomass, Coal Bituminous, Municipal Solid Waste, Natural Gas, Residual Fuel Oil | 7,514 PJ | 5,826 PJ |
| `Crude Steel\EAF\DRI` | Electricity, Natural Gas | 92 PJ | 60 PJ |

Those rows carry `carrier='mixed'`, `fuel_resolved=False`, and
`fuel='Unresolved (<route> route)'`. **31% of BAS and 30% of ATS 2060 Industry
demand is not fuel-attributed** (RAS: 0%).

Consequence: **`aeo9_v0.72_demand_by_fuel.csv` is not like-for-like across
scenarios inside Industry.** Sector, subsector, region and total rollups are
unaffected. For reference, RAS's own split of the same routes in 2030 — where
all three scenarios carry near-identical volume (BF: BAS 1,394 / ATS 1,317 /
RAS 1,312 PJ), which is what confirms these are the same routes at different
reporting depth — is ~92% thermal: BF is 68% metallurgical coke and only 9%
electricity; DRI 96% natural gas; Cement Kiln Heat 0% electricity. So the
unresolved bucket is overwhelmingly thermal, and the electrification gap
between RAS and BAS/ATS is mostly real rather than an artifact (re-attributing
at RAS 2030 proportions would move BAS 2060 electricity share ~15.3% → ~16.3%,
against RAS's 34.2%).

**Cause not established.** Most likely the BAS/ATS sheets were exported with
the tree collapsed at those nodes, but that is a hypothesis — it has not been
verified against the live area (§A.13/§A.14). **To settle it, re-export BAS and
ATS in the same indented-tree form as RAS.** That would remove quirks 1, 2 and
3 in one step, since the tree form is immune to all three.

## Outputs

| File | Grain | Rows |
|---|---|---|
| `aeo9_v0.72_demand_tidy.csv` | leaf × scenario × region × year (zeros dropped, §7.4) | 244,045 |
| `aeo9_v0.72_demand_by_sector.csv` | scenario × sector × region × year | 11,190 |
| `aeo9_v0.72_demand_by_subsector.csv` | + subsector | 22,443 |
| `aeo9_v0.72_demand_by_fuel.csv` | scenario × fuel × carrier × region × year | 31,937 |
| `aeo9_v0.72_demand_by_carrier.csv` | scenario × carrier × region × year | 3,864 |
| `aeo9_v0.72_datacenter.csv` | the `Commercial\Data_Center` slice | 1,590 |
| `aeo9_v0.72_datacenter_clean.csv` | human/tidy: region × type × year × TWh | 684 |
| `aeo9_v0.72_datacenter_table.csv` | human/wide: years across, TOTAL roll-ups | 28 |

Units: `value_pj` (native, on every row) plus `value` in **GWh for electricity
carriers, PJ for thermal**, per the v0.71 convention. Rollups carry `value_pj`
and `value_twh`.

## Headline numbers

ASEAN final energy demand, EJ:

| Scenario | 2020 | 2030 | 2040 | 2050 | 2060 |
|---|---|---|---|---|---|
| BAS | 22.17 | 40.10 | 72.56 | 102.51 | 127.96 |
| ATS | 22.17 | 38.36 | 62.64 | 80.70 | 93.94 |
| RAS | 22.17 | 35.31 | 53.52 | 67.99 | 80.64 |

2060 vs BAS: ATS −26.6%, RAS −37.0%. Electricity share of final demand 2060:
BAS 15.3%, ATS 17.4%, RAS 34.2% (see quirk 3 caveat above).

## Data Center

`Demand\Commercial\Data_Center\{Colocation, Enterprise, Hyperscale}` —
**identical in all three scenarios, and unchanged from v0.71.** Starts 2023;
zero in Brunei, Cambodia, Laos, Myanmar throughout.

ASEAN, TWh: 19.7 (2023) → 46.5 (2025) → 113.4 (2030) → 295.6 (2040) → 526.5
(2050) → 815.6 (2060). Hyperscale 61% of the 2060 total, Colocation 38%,
Enterprise 0.2%. Rises from 18.6% of ASEAN commercial-sector demand in 2030 to
32.2% in 2060.

Clean views: [_clean_datacenter.py](_clean_datacenter.py) writes the two human
files. It drops the 10 single-valued columns, `branch_path` (redundant with
`branch_leaf` under a constant prefix) and the scenario axis — **all three
scenarios are bit-identical here** (asserted, max delta exactly 0.0, no key
missing from any scenario), so carrying it tripled the rows for no
information. Zero-valued cells dropped upstream by skip-zeros are re-filled
explicitly (154 of 684). If a future vintage differentiates Data Center by
scenario, the assertions fail rather than silently discarding it.

Authoring shapes worth a look before these numbers are quoted — all are
properties of the input trajectories, not solver behaviour:

- **Thailand and Vietnam have zero Hyperscale in every year**; their entire
  build (100.4 and 96.1 TWh by 2060) sits in Colocation. Vietnam and Malaysia
  likewise have zero Enterprise throughout.
- **Singapore Colocation peaks in 2030 (10.8 TWh) then declines to 4.5 TWh by
  2060** — the only declining series in the set, consistent with a moratorium
  assumption, with Hyperscale carrying its modest growth instead.
- **Indonesia Colocation plateaus around 2050** (71.1 → 70.1 TWh to 2060) while
  its Hyperscale keeps compounding to 266 TWh.
- **Discontinuity at 2030→2031:** Enterprise steps 0.73 → 0.80 TWh and regional
  growth rates shift — a seam between two authored trajectory segments.
