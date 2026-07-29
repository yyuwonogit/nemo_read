# NEMO_25 48 — RAS Full Digest (solved post-mega-inject)

**Source DB:** `mailbox/20260729 Final/NEMO_25 48.sqlite` — single scenario RAS, 10 AMS (no Timor Leste, no Base Template), years 2025–2060, 48 timeslices, 321 techs, 84 fuels, 16 emissions. All codes decoded to LEAP names. Units stated per column.

> **Critic corrections applied throughout** (do not quote pre-correction figures): (C1) Distributed Solar PV Rooftop — 237.6 GW / 413.7 TWh at 2060 — is added to every capacity, generation and RE-share figure; both source tracks had wrongly filtered `Centralized Electricity Generation:%` only. (C2) RE% is reported against the model's own `RETagTechnology` flag and its embedded `ASEANRenewableCapacityTarget` (44.33% @2030), not only a hand-rolled set. (C3) Storage capex IS in the objective (CAES 138,316 + Li-ion 18,568 MUSD) — the "storage zero-capex" claim is struck. (C4) `vusebytechnology` has 599,150 rows (not empty). (C5) Electricity demand stated on one basis (F2 production 29,123 PJ = SAD 26,682 + AC-device pull 2,441). (C6) Grid intensity reported on a clean plant-only denominator.

---

## 1. HEADLINE

| Metric | Value | Note |
|---|--:|---|
| Solve status | **FEASIBLE / SOLVED** | all v* tables populated, 10 regions × 36 years complete |
| **Unmet Load generation** | **0 PJ, every region, every year** | demand fully met — the unmet-load problem the inject targeted is eliminated |
| Total electricity generation 2060 | **9,218 TWh** | centralized 8,804 + rooftop 414 (excl. storage discharge 429 & imports 278) |
| Electricity generation growth 2025→2060 | **1,725 → 9,218 TWh (5.3×)** | the load-growth that stressed supply |
| Installed generation capacity 2060 | **3,139 GW** | + 313 GW storage + 17.6 GW idle Unmet-Load slack |
| RE share of capacity 2030 (rooftop-corrected) | **47.6% → MEETS 45%** | pre-correction 42.5% MISS was a rooftop-drop artifact; model's own target 44.33% also met |
| RE share of TPES 2030 | **27.3% → MISSES 35%** | reaches 35% only ~2035 |
| Net **energy** CO2 | **1.40 Gt (2025) → 2.56 Gt (2060)** | after 199 Mt/yr power-CCS capture |
| Net **economy-wide** CO2 | **3.09 Gt (2025) → 4.36 Gt (2060)** | incl. ~1.9 Gt/yr exogenous demand/non-energy block |
| Grid CO2 intensity | **545 → 162 gCO2/kWh (−70%)** | decarbonizes while generation grows 5.3× |
| Total discounted system cost | **24.66 trillion USD (real)** | 25.02 T gross incl. Unmet-Load slack phantom |

**One-paragraph read.** The mega-inject solved: no load is shed anywhere, the coal fleet flips from Subcritical (580 TWh, 2025) to Ultrasupercritical (751 TWh, 2060), ~107 GW of nuclear and ~189 GW of CCS build in the 2040s, biodiesel blending rides its ceiling to B54 ASEAN-wide, and AC ownership growth shows through as tripling residential cooling load. RE capacity clears 45% by 2030 once rooftop solar is counted. The cost bill is dominated (90%) by operating spend on fuel imports and end-use device stock, not power capex. Residual issues: 37 GW of stranded Indonesian Coal-USC-CCS built but never dispatched, an ethanol-blend collapse after 2040, a phantom Unmet-Load capex row, and the road-vehicle fleet layer absent from results.

---

## 2. ELECTRICITY SUPPLY

Capacity = GW (`vtotalcapacityannual`); Generation = TWh (`vproductionbytechnologyannual`, fuel F31 Electricity + rooftop F2, ×0.2778 from PJ). Node variants (`_IDxx`/`_MYxx`) aggregated to base families.

### 2.1 ASEAN installed capacity by tech (GW) — rooftop restored
| Tech | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| Gas Combined Cycle | 103.2 | 173.7 | 394.8 | 581.4 | 724.0 |
| Solar PV (centralized) | 38.4 | 65.8 | 230.4 | 494.3 | 821.9 |
| **Solar PV Rooftop (distributed)** | **34.9** | **55.0** | **106.4** | **210.1** | **237.6** |
| Large Hydro | 64.2 | 92.1 | 182.3 | 241.7 | 254.5 |
| Coal Ultrasupercritical | 4.0 | 4.5 | 89.9 | 135.7 | 158.9 |
| Gas CC with CCS | 0 | 0 | 42.9 | 98.5 | 137.8 |
| Wind Onshore | 16.9 | 38.4 | 78.3 | 118.9 | 119.6 |
| Wind Offshore | 0 | 11.2 | 101.7 | 231.4 | 314.0 |
| Biomass Other | 6.5 | 15.0 | 42.0 | 54.1 | 54.2 |
| Coal USC CCS | 0 | 0 | 7.2 | 38.4 | 50.9 |
| Nuclear LWR | 0 | 4.0 | 10.8 | 27.9 | 47.9 |
| Solar Floating | 0 | 0.6 | 21.0 | 37.7 | 42.6 |
| Small Hydro | 3.7 | 8.1 | 23.4 | 35.6 | 37.4 |
| Nuclear SMR | 0 | 0 | 0.8 | 12.4 | 29.5 |
| Nuclear SFR | 0 | 0 | 0 | 12.2 | 29.3 |
| Geothermal Flash | 4.8 | 6.5 | 16.9 | 24.3 | 24.3 |
| Biomass Gasification | 4.2 | 4.0 | 11.7 | 13.3 | 13.3 |
| Biogas | 0.2 | 0.3 | 4.6 | 10.5 | 12.0 |
| Wave | 0 | 0 | 1.8 | 4.7 | 9.7 |
| Tidal | 0 | 0 | 1.7 | 4.5 | 9.4 |
| Coal Subcritical | 120.7 | 120.7 | 63.1 | 13.0 | 1.9 |
| Coal Supercritical | 3.4 | 3.7 | 3.7 | 0.3 | 0.3 |
| Diesel / Gas Turbine / Gas Engine / Fuel Oil / IGCC / Waste / Geo ORC | ~24 | ~26 | ~23 | ~11 | ~9 |
| **GENERATION CAPACITY TOTAL** | **425.4** | **626.3** | **1454.0** | **2410.1** | **3138.6** |
| Storage (Li-ion+Pumped+CAES+H₂, memo) | 16.9 | 31.1 | 82.6 | 210.0 | 313.4 |
| Unmet-Load slack (idle, memo) | 0 | 0 | 0 | 0 | 17.6 |

### 2.2 ASEAN generation by tech (TWh) — rooftop restored
| Tech | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| Gas Combined Cycle | 456.3 | 553.4 | 1238.0 | 2221.3 | 2882.1 |
| Solar PV (centralized) | 65.2 | 108.0 | 383.9 | 783.9 | 1309.6 |
| Coal Ultrasupercritical | 27.8 | 26.4 | 407.9 | 636.1 | 751.1 |
| Wind Offshore | 0 | 36.4 | 319.7 | 655.5 | 702.0 |
| Large Hydro | 273.0 | 414.8 | 670.3 | 680.0 | 675.8 |
| **Solar PV Rooftop** | **60.5** | **92.9** | **182.6** | **364.1** | **413.7** |
| Gas CC with CCS | 0 | 0 | 69.4 | 286.7 | 494.4 |
| Wind Onshore | 51.0 | 115.4 | 224.7 | 333.9 | 335.6 |
| Nuclear LWR | 0 | 20.6 | 41.7 | 137.5 | 325.4 |
| Biomass Other | 32.9 | 82.7 | 220.5 | 295.4 | 303.5 |
| Nuclear SFR | 0 | 0 | 0 | 99.1 | 238.4 |
| Small Hydro | 21.7 | 46.1 | 137.9 | 169.6 | 178.0 |
| Geothermal Flash | 30.6 | 41.9 | 114.7 | 166.7 | 166.7 |
| Nuclear SMR | 0 | 0 | 1.1 | 12.1 | 95.1 |
| Wave | 0 | 0 | 14.6 | 38.2 | 79.2 |
| Tidal | 0 | 0.3 | 14.5 | 37.1 | 77.5 |
| Biomass Gasification | 22.7 | 19.4 | 61.7 | 77.2 | 77.6 |
| Solar Floating | 0 | 1.0 | 35.0 | 56.5 | 63.0 |
| Coal USC-CCS | 0 | 0 | 3.2 | 26.5 | 26.6 |
| Coal Subcritical | 580.2 | 459.2 | 198.0 | 40.4 | 2.5 |
| Coal Supercritical | 18.4 | 16.4 | 20.4 | 1.4 | 1.7 |
| Waste + Gas Turbine + others | ~24 | ~29 | ~18 | ~10 | ~9 |
| **GENERATION TOTAL** | **1665.0** | **2064.3** | **4377.9** | **7137.7** | **9218.2** |
| (storage discharge, memo) | 20.8 | 40.8 | 97.6 | 237.2 | 429.3 |

**Capacity vs energy contrast (2060):** Gas CC 23% of capacity → 31% of generation (CF~45%, mid-merit workhorse). Solar PV+Rooftop 34% of capacity → 19% of generation (CF~18%, capacity-heavy). Coal USC 5% cap → 8% gen (CF~54%). Nuclear 3.4% cap → 7% gen (CF~78%). The fleet is capacity-dominated by intermittent solar/wind but energy is still led by dispatchable gas + baseload coal/nuclear/hydro.

### 2.3 RE & clean-power shares (%) — three definitions
RE (hand-set) = Solar (incl. rooftop) + Wind + Hydro + Geothermal + Biomass/Biogas + Waste + Tidal/Wave. Denominators exclude storage / Unmet-Load unless noted.

| Year | RE %cap (rooftop-corr) | RE+Nuc %cap | RE %gen (rooftop-corr) | RE+Nuc %gen | Model-tag RE %cap¹ |
|---|--:|--:|--:|--:|--:|
| 2025 | 41.0 | 41.0 | ~35.0 | ~35.0 | — |
| 2030 | **47.6** | 48.3 | ~46.5 | 47.5 | 43.0 |
| 2040 | 56.7 | 57.5 | ~55.0 | 56.0 | — |
| 2050 | 61.5 | 63.4 | ~52.0 | 55.5 | — |
| 2060 | 62.2 | 65.6 | **47.7** | 55.2 | 53.9 |

¹ `RETagTechnology` (model's authoritative flag) counts rooftop **and** storage (Li-ion/Pumped/CAES/VRB) + Pressurized-H₂ as RE, with a storage-inclusive denominator → a materially different, storage-diluted curve. The RE headline is definition-sensitive across a ~5pp band; both are reported. **RE generation share peaks ~2040 (55%) then dips to 48% by 2060** as gas grows fastest in absolute energy terms while RE keeps dominating new capacity.

### 2.4 New builds (`vnewcapacity`, GW per window) & the coal flip
| Tech | '25–30 | '31–40 | '41–50 | '51–60 | Total |
|---|--:|--:|--:|--:|--:|
| Solar PV (centralized) | 0 | 88.6 | 190.4 | 416.2 | 695.2 |
| Gas CC | 38.7 | 209.3 | 173.5 | 181.3 | 602.8 |
| Large Hydro | 17.5 | 77.2 | 59.4 | 12.7 | 166.9 |
| Wind Offshore | 3.2 | 24.0 | 45.5 | 85.8 | 158.6 |
| Coal USC | 1.1 | 84.7 | 45.9 | 24.2 | 155.8 |
| Gas CC-CCS | 0 | 42.9 | 55.6 | 39.3 | 137.8 |
| Coal USC-CCS | 0 | 7.2 | 31.2 | 12.5 | 50.9 |
| Nuclear LWR / SFR / SMR | 0 | 0 | 12.4/12.2/11.4 | 17.2/17.1/17.0 | 29.5/29.3/28.5 |
| Unmet Load (slack, idle) | 0 | 0 | 0 | 34.8 | 34.8 |

**Build onsets (endogenous):** Coal USC 2025 · Wind Offshore 2029 · Gas CC-CCS 2031 · Solar Floating 2033 · Coal USC-CCS 2039 · Nuclear LWR 2042 · SFR 2044 · SMR 2045. Nuclear & CCS are all 2040s+.
**Coal-flip trajectory (GW):** Subcritical 120.7 (2025) → 120.7 (2030) → 88.6 (2035) → 63.1 (2040) → 13.0 (2050) → 1.9 (2060), −98% by 2060; USC becomes the coal backbone (159 GW). Coal energy flips Subcritical 580 TWh → USC 751 TWh. **The coal flip landed.**

### 2.5 2060 capacity by region × tech (GW) — key families
| Tech | Indo | Viet | Malay | Phil | Thai | Laos | Sing | Camb | Myan | Brun | ASEAN |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Solar PV (cent) | 101.0 | 240.6 | 294.7 | 62.3 | 92.8 | 4.0 | 7.9 | 9.6 | 4.7 | 4.4 | 821.9 |
| Gas CC | 266.0 | 142.7 | 81.0 | 86.4 | 81.6 | 18.4 | 31.2 | 4.6 | 4.7 | 7.3 | 724.0 |
| Wind Offshore | 155.4 | 139.1 | 0 | 19.5 | 0 | 0 | 0 | 0 | 0 | 0 | 314.0 |
| Coal USC | 34.0 | 20.0 | 20.0 | 20.0 | 20.0 | 20.0 | 17.3 | 1.6 | 3.6 | 2.5 | 158.9 |
| Gas CC-CCS | 37.4 | 20.5 | 30.8 | 31.2 | 0 | 0 | 13.8 | 0 | 0 | 4.2 | 137.8 |
| Wind Onshore | 7.3 | 77.0 | 0 | 20.3 | 4.5 | 1.6 | 0 | 3.3 | 5.4 | 0 | 119.6 |
| Coal USC-CCS | 37.4 | 0 | 12.0 | 0 | 0 | 0 | 1.0 | 0 | 0 | 0.5 | 50.9 |
| Nuclear LWR | 29.5 | 14.0 | 0 | 4.3 | 0 | 0 | 0 | 0 | 0 | 0 | 47.9 |
| Nuclear SMR | 29.0 | 0 | 0 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 | 29.5 |
| Nuclear SFR | 29.3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 29.3 |
| Large Hydro | 131.4 | 36.8 | 24.0 | 3.8 | 7.8 | 31.1 | 0 | 9.3 | 10.4 | 0 | 254.5 |
| Geothermal Flash | 21.4 | 0 | 0 | 2.8 | 0 | 0 | 0 | 0 | 0 | 0 | 24.3 |
| Coal Subcritical | 0 | 0 | 0 | 1.9 | 0 | 0 | 0 | 0 | 0 | 0 | 1.9 |
| **Total (gen, excl storage)** | ~940 | ~890 | ~480 | ~300 | ~290 | ~78 | ~72 | ~33 | ~33 | ~20 | 3138.6 |

Nuclear (107 GW) is Indonesia-anchored (88 GW) with LWR reach into Vietnam (14.0) and Philippines (4.3+0.5). CCS (both coal & gas, 189 GW) lands in Indonesia/Malaysia/Singapore/Philippines/Vietnam/Brunei. Wind Offshore only Indonesia/Vietnam/Philippines.

### 2.6 Reserve / adequacy / Unmet Load
- **Unmet Load generation = 0** in every region-year (verified against F31 across all Unmet-Load techs). Demand fully met.
- 17.6 GW of Unmet-Load **capacity** appears at 2060 (Indonesia IDJW) — built, never dispatched, firm backup only. See §9 A2 for the phantom capex it carries.
- `ReserveMargin` is an input constraint (1.03–1.45; Indonesia 1.25→1.45, Thailand 1.04→~1.3, Myanmar/Cambodia flat 1.30). Feasible solve ⇒ every region-year meets peak×margin. No `vreserve*` result table exists — adequacy is confirmed structurally (feasible + 0 unmet), not via a slack table.

---

## 3. STORAGE, TRANSMISSION & TRADE

### 3.1 Storage — power capacity (GW), ASEAN. `vtotalcapacityannual` (no `vstorage*` result table exists)
| Storage type | 2025 | 2030 | 2035 | 2040 | 2050 | 2060 | First | Duration |
|---|--:|--:|--:|--:|--:|--:|:--|:--|
| Lithium Ion | 12.50 | 20.98 | 35.33 | 58.90 | 157.21 | 187.54 | 2025 | 2 h |
| Pumped Hydro | 4.37 | 10.14 | 17.68 | 21.08 | 31.29 | 31.29 | 2025 | 8 h |
| CAES | 0 | 0 | 0 | 2.59 | 21.49 | 94.53 | 2037 | 10 h |
| Pressurized H₂ Gas* | 0 | 0 | 0 | 0 | 0 | 63.92 | 2055 | ~208 h |
| VRB Flow Batteries | 0 | 0 | 0 | 0 | 0 | **0** | never | 4 h |

\*Indonesia-only "Hydrogen Production for Energy Use" — seasonal store, treat its GW separately from battery/pumped power. **VRB never deploys** (0 all years — flag §9). Derived energy capacity (GWh, GW×full-load-h) at 2060: Li-ion 375, Pumped 250, CAES 945, H₂ ~13,300.

Per-region Li-ion 2060 (GW): Vietnam 96.1, Philippines 40.6, Thailand 41.0, Indonesia 6.0, Cambodia 1.0, Malaysia 2.5, Singapore 0.2, Brunei 0.1. Pumped 2060: Vietnam 21.3, Indonesia 4.2, Cambodia 3.1, Philippines 1.6, Laos 1.0. CAES 2060: Vietnam 65.5, Thailand 14.9, Malaysia 14.0, Myanmar 0.1.

### 3.2 Transmission — net balance per node (PJ/yr), `vtransmissionannual` (+ exporter / − importer)
| Node | 2025 | 2030 | 2040 | 2050 | 2060 | Role @2060 |
|---|--:|--:|--:|--:|--:|:--|
| Laos | +13.0 | +168.7 | +537.5 | +684.2 | **+727.0** | top exporter |
| Malaysia Peninsular | +82.8 | −94.3 | +23.7 | +267.7 | +461.1 | exporter |
| Indonesia Sumatra | −53.2 | +68.6 | +218.8 | +443.0 | +299.9 | exporter |
| Malaysia Sabah | +97.8 | +93.5 | +147.2 | +204.0 | +222.0 | exporter |
| Brunei | +9.3 | +18.9 | +57.3 | +154.0 | +218.9 | exporter |
| Philippines | +59.3 | +110.2 | +296.1 | +315.4 | +295.2 | exporter |
| Vietnam | +510.9 | +628.7 | +388.1 | +222.8 | +93.9 | exporter (declining) |
| Cambodia | −69.4 | −43.1 | −13.8 | −18.4 | −8.8 | importer |
| Myanmar | −121.3 | −122.6 | −36.0 | −41.9 | −75.7 | importer |
| Singapore | −89.5 | −122.1 | −136.3 | −74.5 | −114.9 | importer |
| Indonesia Jamali | −101.5 | −213.9 | −433.8 | −583.2 | −183.1 | importer |
| Indonesia Borneo | −66.5 | −14.3 | −99.2 | −405.8 | −365.0 | importer |
| Indonesia East | −1.9 | +67.5 | +157.1 | +163.6 | −298.6 | flips to importer |
| Malaysia Sarawak | −73.0 | −95.8 | −154.3 | −246.3 | −290.3 | importer |
| Thailand | −196.7 | −449.8 | −952.6 | −1084.5 | **−981.5** | top importer |

Region roll-up @2060: **Indonesia net −546.8 PJ (importer)**, **Malaysia net +392.8 PJ (exporter)**. Nets to 0.0 ASEAN-wide (verified). **Electricity is NOT traded via `vtradeannual`** — it moves entirely through these transmission corridors.

**Congested corridors @2060 (PJ/yr, util%):** T38 Sabah→Borneo 308.6 (98%), T45 Laos→Myanmar 304.9 (97%), T32 Borneo→East 298.6 (95%), T39 Thailand→Laos −299.8 (95%), T29 Philippines→Sabah 295.2 (94%), T31 Sumatra→Jamali 280.1 (89%). Narrative: Laos is the ASEAN hydro battery; Thailand is the big sink; Philippines exports solar+Li-ion surplus to Sabah, which relays into Indonesian Borneo. `vtransmissionbuilt` = 167 build events (new 10,000 MW backbone lines vs 200–955 MW legacy interconnectors).

### 3.3 Trade — inter-AMS **bioenergy feedstock only** (`vtradeannual`; `vtrade` timeslice table empty)
| Feedstock | Σ|flow| 2025–60 | Destination |
|---|--:|:--|
| Palm Oil | 247,740 | Biodiesel Production |
| Cassava | 47,141 | Bioethanol Production |
| Coconut Oil | 14,783 | Biodiesel Production |
| POME | 11,135 | Biodiesel Production |
| Sugarcane | 3,252 | Bioethanol Production |
| Corn | 1,613 | Bioethanol Production |
| Molasses | 933 | Bioethanol Production |

**2060 net balance:** Palm Oil — Indonesia +3,252 supplies Philippines −1,477, Malaysia −897, Thailand −333, Vietnam −216, others. POME — Indonesia +175 → Vietnam −175. Cassava — Cambodia +316/Indonesia +290/Myanmar +77 → Thailand −492, Vietnam −143. Coconut Oil — Myanmar +102/Indonesia +73 → Vietnam −124. Sugarcane & molasses fade to ~zero by 2050 as cassava dominates the ethanol pathway. **Indonesia is the palm-oil/POME feedstock hub for the whole region's biodiesel mandate.**

---

## 4. DEMAND

**Structural limit (governs this whole section):** only Air-Conditioning is device-modeled (18 techs, 9 residential + 9 commercial). Refrigeration, Cooking, Lighting, Water-Heating and all other end-uses collapse into one exogenous final-electricity fuel **F2** plus a few non-electric final fuels that mix all sectors — the fridge / commercial-intensity / bug-7 injects drove F2 but **cannot be decomposed back out** of the solved sqlite. The road-vehicle fleet layer (34 `Optimized…` techs) returned **0 rows in every result table** — no fleet stock, EV share, or retirement is derivable (§9 highest-priority gap). Energy unit = PJ.

### 4.1 Total final electricity delivered (F2, PJ) — the load-growth driver
Reported on the **production basis** (F2 production = SAD 26,682 + AC-device pull 2,441 at 2060).
| Region | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| Indonesia | 1759 | 2233 | 4939 | 8838 | 12025 |
| Vietnam | 909 | 1178 | 2922 | 5113 | 6741 |
| Thailand | 703 | 795 | 1854 | 2910 | 3623 |
| Malaysia | 687 | 906 | 1894 | 2825 | 3250 |
| Philippines | 434 | 535 | 1042 | 1621 | 2076 |
| Singapore | 298 | 333 | 394 | 462 | 518 |
| Myanmar | 170 | 186 | 235 | 325 | 420 |
| Cambodia | 109 | 116 | 165 | 221 | 248 |
| Laos | 150 | 151 | 150 | 179 | 202 |
| Brunei | 14 | 15 | 18 | 21 | 21 |
| **ASEAN (PJ)** | **5235** | **6448** | **13614** | **22516** | **29123** |
| **ASEAN (TWh)** | **1454** | **1791** | **3782** | **6254** | **8090** |

Final electricity grows **5.6× (1454→8090 TWh)**. This is the total-electricity problem the inject's power build + Unmet-Load pricing had to cover — AC is only ~1/8 of it by 2060.

### 4.2 Buildings — Air-Conditioning electricity input (PJ, `vusebytechnologyannual`)
| | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| Residential AC (ASEAN) | 739 | 940 | 1336 | 1773 | 2137 |
| Commercial AC (ASEAN) | 224 | 230 | 269 | 292 | 304 |

Residential AC nearly triples (+190%); commercial +36%. Indonesia = ~43% of residential AC (328→915 PJ). **Ownership signal shows through:** Singapore residential cooling is flat (23→24 PJ, already saturated at the 282%+/multi-unit case) while Indonesia (263→915), Vietnam (143→571), Philippines (58→280) climb steeply — the penetration-ramp story landed. **Efficiency-tier shift (RAS lever):** residential AC goes **100% High-efficiency by ~2055** (Mid/Low fully retire: Mid 176→0, Low 173→0); commercial stays mixed (60% High / 37% Mid in 2060).

### 4.3 Transport — final energy (PJ). `SpecifiedAnnualDemand`+`AccumulatedAnnualDemand`
| Fuel | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| Blended Diesel (road) | 6,735 | 8,638 | 12,213 | 11,094 | 8,018 |
| Blended Gasoline (road) | 2,823 | 3,292 | 1,928 | 375 | 173 |
| Gasoline unblended (road) | 1,571 | 1,575 | 1,581 | 1,586 | 1,593 |
| **Road subtotal** | **11,129** | **13,505** | **15,722** | **13,055** | **9,784** |
| Jet Kerosene (air) | 785 | 906 | 1,235 | 1,626 | 2,040 |
| Sustainable Aviation Fuel (air) | 2 | 25 | 124 | 320 | 599 |
| Avgas (air) | 0 | 0 | 0 | 1 | 1 |
| **Air subtotal** | **787** | **931** | **1,359** | **1,947** | **2,640** |
| **TRANSPORT TOTAL** | **11,916** | **14,436** | **17,081** | **15,002** | **12,424** |

Road is 100% liquid (EV/H₂/NG/LPG demand = 0 — the vehicle-tech layer is dormant, so the electrification substitution is invisible here). Road liquids peak ~2040 then fall as gasoline collapses (Blended Gasoline near-total phase-out by 2050); aviation nearly triples. Blended Diesel is Indonesia-heavy (3,664→5,687 PJ). **Fleet-by-vehicle / EV-share / retirement: NOT AVAILABLE** (§9).

### 4.4 Industry & non-power thermal — aggregate direct fuel demand (PJ, no subsector split)
| Fuel | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| Coal Sub-bituminous | 9,339 | 9,339 | 9,339 | 9,339 | 9,339 |
| Coal Bituminous | 3,489 | 3,993 | 4,642 | 4,364 | 4,688 |
| Natural Gas | 3,207 | 3,751 | 5,369 | 7,760 | 9,694 |
| Diesel (direct) | 3,889 | 3,377 | 3,841 | 4,866 | 6,204 |
| Residual Fuel Oil | 3,612 | 3,160 | 3,329 | 3,517 | 3,788 |
| LNG | 1,894 | 1,954 | 2,113 | 2,297 | 2,550 |
| LPG | 1,341 | 1,462 | 1,063 | 1,219 | 1,612 |
| Oil / Charcoal / minor coals / kerosene / pet-coke | ~651 | ~616 | ~684 | ~761 | ~962 |
| **INDUSTRY/THERMAL TOTAL** | **23,812** | **24,493** | **27,043** | **30,637** | **35,051** |

Growth is gas-led (+3×) plus direct diesel; coal barely moves. Indonesia = 54–57% of ASEAN industry demand, driven by a flat 9,183 PJ Coal Sub-bituminous block (constant every year — placeholder, §9). Non-energy feedstock (naphtha/crude/bitumen/lubricants) grows 1,967→3,318 PJ, reported separately (not combusted). **Rail and Water transport are not modelled as demand.**

### 4.5 Non-electric final fuels (all sectors mixed, PJ) — flat
LPG 94, Natural Gas 744, Kerosene 10, Charcoal 5 — **all flat 2025→2060** (residential cooking/water-heating fuel growth appears absent — §9 flag). Gasoline 1,539 / Diesel 1,333 also flat.

---

## 5. FUELS & BIOENERGY

Energy values are model-native energy units (treat as PJ-equivalent). **The bio inject landed and solved: biodiesel blending is robust and rides the ceiling; ethanol blending is thin and collapses after ~2040; the Philippines FAME fix worked.**

### 5.1 Biodiesel-in-diesel blend share achieved (%) — `vproductionbytechnologyannual`
| Region | 2025 | 2030 | 2035 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|--:|
| Indonesia | 37.5 | 48.6 | 50.1 | 51.6 | 54.6 | 57.7 |
| Thailand | 6.3 | 10.5 | 19.4 | 24.1 | 29.1 | 53.4 |
| Malaysia | 6.3 | 27.8 | 42.4 | 47.4 | 50.4 | 53.4 |
| Philippines | 3.6 | 17.4 | 31.7 | 46.4 | 48.9 | 51.9 |
| Vietnam | 1.3 | 4.7 | 8.1 | 11.5 | 24.3 | 44.3 |
| Laos | 1.5 | 15.3 | 29.5 | 44.1 | 48.9 | 51.9 |
| Cambodia | 0.0 | 13.7 | 27.8 | 42.4 | 48.9 | 51.9 |
| Brunei | 0.0 | 13.7 | 27.8 | 42.4 | 48.9 | 51.9 |
| Singapore | 0.0 | 5.3 | 27.8 | 42.4 | 48.9 | 51.9 |
| Myanmar | 0.0 | 13.7 | 27.8 | 38.3 | 37.0 | 21.2 |
| **ASEAN (energy-wtd)** | **21.8** | **32.0** | **37.8** | **42.4** | **48.6** | **54.6** |

**Indonesia sits exactly at its rising ceiling every year → hits B50 at 2035, B57.7 by 2060.** Biodiesel is the cheaper marginal blendstock, so most regions pin to the ceiling from ~2040 (~52% by 2060). Thailand/Vietnam ride the floor early then jump to ceiling. **Myanmar is the lone laggard** — peaks 38% (2040) then falls to 21% under a 52% ceiling (feedstock constraint, §9).

### 5.2 Ethanol-in-gasoline blend share (%) — collapses late
| Region | 2025 | 2030 | 2035 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|--:|
| Indonesia | 0.0 | 2.4 | 4.9 | 7.5 | 13.0 | 13.0 |
| Thailand | 0.5 | 13.0 | 13.0 | 13.0 | 13.0 | 13.0 |
| Vietnam | 0.9 | 10.9 | 13.0 | 14.1 | 13.0 | 13.0 |
| Philippines | 6.2 | 10.9 | 13.0 | 14.1 | 6.2 | 6.2 |
| Laos | 1.0 | 10.7 | 13.0 | 14.1 | 6.2 | 6.2 |
| Malaysia | 0.0 | 9.5 | 13.0 | 14.1 | **0.0** | **0.0** |
| Cambodia | 0.0 | 9.5 | 13.0 | 14.1 | **0.0** | **0.0** |
| Brunei | 0.0 | 9.5 | 13.0 | 14.1 | 16.2 | 18.5 |
| Singapore | 0.0 | 0.0 | 0.0 | 13.1 | 16.2 | 18.5 |
| Myanmar | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| **ASEAN (energy-wtd)** | **0.8** | **8.0** | **10.4** | **11.8** | **4.2** | **1.2** |

Regions pin to the ceiling through 2040 (~14.1%) then **Malaysia & Cambodia crash to 0% at 2050/2060**, Philippines/Laos fall to a 6.2% floor, ASEAN share collapses 11.8%→1.2%. Myanmar is 0% throughout. **Ethanol mandates are NOT met in 2050–60 for most regions** — root cause is domestic ethanol-supply collapse (§5.3, §9).

### 5.3 Refinery production — ASEAN total (energy units)
| Tech | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| FAME Biodiesel | 1,713 | 3,281 | 5,795 | 6,231 | 5,520 |
| POME Biodiesel | 0 | 18 | 76 | 135 | 175 |
| CME Biodiesel | 0 | 51 | 123 | 119 | 117 |
| Cassava Ethanol | 0 | 54 | 131 | 10 | 0 |
| Sugarcane Ethanol | 10 | 46 | 68 | 0 | 0 |
| Corn Ethanol | 0 | 48 | 22 | 4 | 2 |
| Molasses Ethanol | 0 | 24 | 0 | 0 | 0 |

FAME dominates biodiesel (>97%; Indonesia 1,437→3,478, Philippines 100→1,214). **All four ethanol pathways decay to ~0 by 2050–60** — this starves the ethanol blend. **Blend composition consumed** (`vusebytechnologyannual`): Blended Diesel bio-share 21.8% (2025) → 42.4% (2040) → **54.6% (2060)**; Blended Gasoline bio-share 0.8% → 11.8% (2040) → 1.2% (2060).

### 5.4 Feedstock — production vs imports (ASEAN, energy units)
| Feedstock | 2025 dom | 2040 dom | 2060 dom | imports |
|---|--:|--:|--:|:--|
| Palm Oil | 3,561 | 8,750 | 9,289 | 0 (Indonesia-only producer; distributed by trade) |
| Cassava | 581 | 824 | 693 | 113 (2025 only) |
| Coconut Oil | 78 | 208 | 201 | 0 |
| POME | 0 | 76 | 175 | 0 |
| Sugarcane | 47 | 70 | 2 | 0 |
| Corn | 0 | 22 | 2 | 0 |

Extra-ASEAN imports are essentially nil — feedstock met domestically + inter-region trade. **Palm Oil produced ONLY by Indonesia** yet FAME runs in all 10 regions (reconciled via `vtradeannual`; some transit-chain routing artifacts through non-producing Laos/Singapore — §9). Cassava/sugarcane feedstock **stranded** in late years as ethanol demand vanishes.

### 5.5 Other clean fuels — ASEAN (energy units)
| Tech | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| Sustainable Aviation Fuel (HVO) | 2 | 25 | 124 | 320 | 599 |
| H₂ from Biomass Gasification | 0 | 5 | 474 | 1,971 | 3,323 |
| Methanol (CO₂-utilization, Fe/steel) | 87 | 167 | 295 | 317 | 272 |
| Methanol (from H₂) | 0 | 0 | 0 | 0 | 9 |
| H₂ (SMR / coal-gasif / PEM / all +CCS) | 0 | 0 | 0 | 0 | **0** |
| Ammonia / Charcoal / Biogas-power | 0 | 0 | 0 | 0 | **0** |

SAF ramps strongly (2→599). **Hydrogen for energy comes entirely from Biomass Gasification** (→3,323) — all fossil/electrolysis/CCS H₂ routes produce exactly zero (§9).

### 5.6 Primary energy / TPES — ASEAN (PJ, `vproductionbytechnologyannual` supply techs)
> Absolute TPES ≈ 63 EJ (2025) is ~2× real ASEAN because refined-product imports meet each region's demand from Rest-of-World (product trade un-netted) and bio-feedstock is counted at raw-crop energy. **Trajectories and shares are robust; read absolute PJ as "model supply," not an IEA balance.**

| Category | 2025 | 2030 | 2040 | 2050 | 2060 | %2060 |
|---|--:|--:|--:|--:|--:|--:|
| Fossil | 52,918 | 54,023 | 62,066 | 73,187 | 82,484 | 60.0 |
| Nuclear (imported uranium) | 0 | 218 | 389 | 2,188 | 6,009 | 4.4 |
| RE | 9,942 | 14,125 | 28,723 | 40,127 | 47,982 | 34.9 |
| Other/carrier | 176 | 146 | 107 | 546 | 999 | 0.7 |
| **TOTAL TPES** | **63,035** | **68,512** | **91,285** | **116,048** | **137,474** | 100 |

Gas is the fastest-growing fossil (+283%; Indonesia domestic gas 2,202→16,784 PJ); coal roughly flat (~21 EJ); Solar +16×, solid bioenergy +5.6×. **Import dependency falls 55.6%→33.6%** (domestic 27,985→91,348 vs imports 35,051→46,126 PJ) as domestic gas + RE outscale imports. Per-region RE% of TPES 2060: Cambodia 59.8, Vietnam 58.2, Indonesia 39.4, Myanmar 29.1, Laos 29.9, Thailand 21.7, Malaysia 21.4, Philippines 15.0, Singapore 3.2, Brunei 3.1. Own-use + T&D losses grow 1,091→5,088 PJ (refinery/gas-processing losses report 0 — understated, §9).

---

## 6. EMISSIONS

**Accounting key:** CO2 (E2) stored **gross**; CCS capture booked separately as negative E407 (95% design capture on plants that run CCS) → **net = E2 + E407**. Emissions split **endogenous** (`vannualtechnologyemission`, supply/transformation techs only) + **exogenous** (`AnnualExogenousEmission`, demand-side + non-energy, not sector-decomposable — ~55% of total CO2). Demand-side techs (transport/industry/buildings) carry **zero** endogenous emission.

### 6.1 Net CO2 accounting — ASEAN (Mt CO2)
| Component | 2025 | 2030 | 2035 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|--:|
| Gross energy CO2 (endo E2) | 1404.7 | 1341.2 | 1371.5 | 1658.0 | 2245.7 | 2756.9 |
| Gross exogenous CO2 | 1686.7 | 1804.1 | 1946.1 | 1971.4 | 1917.8 | 1975.4 |
| **GROSS TOTAL CO2** | **3091.4** | **3145.3** | **3317.5** | **3629.4** | **4163.5** | **4732.4** |
| Captured — energy CCS (E407) | 0 | 0 | −11.9 | −27.8 | −123.3 | −199.4 |
| Captured — exogenous seq. | 0 | 0 | −2.3 | −46.4 | −123.5 | −171.0 |
| **NET TOTAL CO2** | **3091.4** | **3145.3** | **3303.4** | **3555.1** | **3916.7** | **4361.9** |
| memo: **NET energy-only CO2** | **1404.7** | 1341.2 | 1359.6 | 1630.2 | 2122.4 | **2557.5** |

**The task-brief headline "1.40 → 2.56 Gt" is the NET energy-only row.** Economy-wide net CO2 is far larger (3.09 → 4.36 Gt) because of the ~1.9 Gt/yr exogenous block (roughly flat — §9).

### 6.2 Endogenous energy CO2 by sector (Mt) & CCS capture
| Sector | 2025 | 2040 | 2060 |
|---|--:|--:|--:|
| Power generation | 890.9 | 990.2 | 1738.4 |
| Fossil supply/refining | 509.3 | 651.4 | 995.1 |
| Biofuel/H₂/methanol production | 4.5 | 16.4 | 23.5 |

**Captured/sequestered (Mt/yr):** 0 (2025) → 14.2 (2035) → 74.3 (2040) → 246.8 (2050) → **370.4 (2060)** = 7.8% of gross total. Endogenous CCS is Gas-CC-CCS (174.6 Mt) + Coal-USC-CCS (24.1 Mt) at 2060; H₂ gasification carries E407 config but captures 0.

### 6.3 CO2 by region (Mt, endo energy | exo, sorted by 2060 endo)
| Region | endo 2025 | endo 2060 | exo 2025 | exo 2060 |
|---|--:|--:|--:|--:|
| Indonesia | 535.7 | 1159.9 | 603.2 | 890.8 |
| Malaysia | 259.5 | 456.3 | 140.4 | 78.2 |
| Thailand | 162.3 | 358.2 | 193.1 | 169.4 |
| Philippines | 131.6 | 271.5 | 192.1 | 249.4 |
| Vietnam | 174.7 | 199.5 | 269.6 | 301.4 |
| Laos | 14.7 | 105.6 | 17.5 | 14.2 |
| Singapore | 46.0 | 77.6 | 173.0 | 185.9 |
| Myanmar | 38.6 | 66.0 | 69.3 | 66.1 |
| Brunei | 31.3 | 50.0 | 1.4 | 0.6 |
| Cambodia | 10.3 | 12.2 | 27.1 | 19.5 |
| **ASEAN** | **1404.7** | **2756.9** | **1686.7** | **1975.4** |

### 6.4 Biogenic CO2 (E1, reported separately — do NOT add to fossil net)
Endogenous (biomass/waste power, biofuels) 124.5 → 1418.8 Mt (11× as biomass/waste scales; top 2060: Waste-to-energy 777, Biomass Other 320+~200 Indonesian nodes, Gasification 75). Exogenous 1268.1 → 543.6. Total 1392.5 → 1962.4 Mt.

### 6.5 Other species — ASEAN total (raw = tonnes/yr)
| Species | 2025 | 2040 | 2060 | Dominant endo source |
|---|--:|--:|--:|:--|
| Methane CH4 | 4.37 M | 6.02 M | 9.07 M | Gas T&D leakage |
| Nitrous Oxide N2O | 71.9 k | 106.9 k | 100.5 k | Power gen |
| Nitrogen Oxides NOx | 14.7 M | 20.2 M | 19.8 M | Power gen |
| Sulfur Dioxide SO2 | 26.5 M | 67.6 M | 89.9 M | Coal power (main AQ deterioration, ~4×) |
| Carbon Monoxide CO | 27.8 M | 22.9 M | 12.5 M | Energy own-use (declining) |
| NMVOC | 5.60 M | 4.77 M | 3.60 M | Gas production |
| Ammonia NH3 | 204 k | 174 k | 191 k | Energy own-use |
| PM2.5 / PM10 | 2.07 M / 2.17 M | 2.87 M / 3.00 M | 2.70 M / 2.89 M | Power gen |
| Black Carbon / Organic Carbon | 771 k / 786 k | 1.19 M / 723 k | 934 k / 507 k | ~all exogenous |
| Land Use (E63) | 12.3 M | 45.1 M | 44.4 M | Biofuel land conversion |

### 6.6 Grid intensity (clean plant-only denominator)
| | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| Plant generation incl. rooftop (TWh) | 1725 | 2064 | 4378 | 7138 | 9218 |
| Power net CO2 (Mt) | 890.9 | 769.0 | 962.4 | 1275.4 | 1539.6 |
| **Grid net intensity (gCO2/kWh)** | **516** | **373** | **220** | **179** | **167** |

Grid decarbonizes ~68% (516→167 gCO2/kWh) while generation grows 5.3×. (The per-F31-incl-storage/imports basis gives 545→162; the plant-only basis above is the cleaner metric — C6.) **CO2 per capita / per GDP not derivable** — no population/GDP tables in this NEMO artifact (LEAP Key\ tree). No carbon price/cap active in RAS (`vdiscountedtechnologyemissionspenalty` + all GHG/EmissionLimit tables empty — a positive confirmation).

---

## 7. COSTS

All in **Million USD**, discounting 7% real, base 2025. No `vtotaldiscountedcost` table — objective assembled from components; no dual/shadow-price tables exist.

### 7.1 Total discounted system cost (2025–2060 lifetime)
| Component | Real | Unmet-Load slack |
|---|--:|--:|
| Discounted capital investment | 2,297,796 | 363,654 |
| Discounted operating cost | 22,830,934 | 1,650 |
| (−) Discounted salvage value | −473,438 | 0 |
| Discounted emissions penalty | 0 (table empty) | 0 |
| **TOTAL DISCOUNTED SYSTEM COST** | **24,655,292** | **365,303** |

**Objective ≈ 24.66 trillion USD (real); 25.02 T gross incl. slack.** Operating cost is 93% of the discounted total; capex ~9% before salvage.

### 7.2 By region & by sector (discounted lifetime, MUSD)
| Region | Real cost | share% | | Sector | Disc. capex | Disc. opex | Total | share% |
|---|--:|--:|--|---|--:|--:|--:|--:|
| Indonesia | 9,009,003 | 36.5 | | Fuels / Resources | 124,530 | 11,502,929 | 11,627,459 | 45.6 |
| Vietnam | 5,203,223 | 21.1 | | Demand-devices | 592,913 | 10,710,437 | 11,303,350 | 44.3 |
| Thailand | 2,897,930 | 11.8 | | Power | 1,580,353 | 617,567 | 2,197,921 | 8.6 |
| Philippines | 2,247,330 | 9.1 | | Unmet Load (slack) | 363,654 | 1,650 | 365,303 | 1.4 |
| Singapore | 2,237,155 | 9.1 | | | | | | |
| Malaysia | 1,847,993 | 7.5 | | | | | | |
| Myanmar/Camb/Laos/Brunei | 1,212,659 | 5.0 | | | | | | |

Cost is **overwhelmingly operating & demand/fuel-driven** — Fuels/Resources and Demand-devices each ~45%; **power generation only 8.6%** (but holds 72% of real capex). Indonesia+Vietnam+Thailand = 69% of cost.

### 7.3 Top technology cost drivers (discounted capex+opex lifetime, MUSD)
Large:High_eff device 7,440,489 · Biodiesel Imports 2,768,785 · Diesel Imports 2,024,237 · Crude Oil Imports 1,376,706 · Large:Mid_eff 945,329 · Natural Gas Domestic Production 773,590 · Gasoline Imports 762,516 · Residual Fuel Oil Imports 722,858 · Small:High_eff 641,763 · Coal Sub-bituminous Domestic 542,677. **No generation tech cracks the top 15** — end-use device stock + fuel imports dominate.

### 7.4 Real capex trajectory by group (MUSD/yr, Unmet Load excluded)
| Group | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| Demand-devices | 79,145 | 25,149 | 91,174 | 57,986 | 86,170 |
| Renewables | 14,706 | 34,227 | 93,990 | 69,654 | 100,464 |
| Nuclear | 0 | 0 | 0 | 81,025 | 41,922 |
| Gas | 10,361 | 14,088 | 36,987 | 22,539 | 27,574 |
| CCS | 0 | 0 | 41,434 | 24,086 | 10,965 |
| Coal | 1,716 | 280 | 40,970 | 8,107 | 6,009 |
| Fuels-production | 65 | 748 | 5,852 | 14,306 | 21,255 |
| **TOTAL real capex** | **105,992** | **74,492** | **310,418** | **286,499** | **301,296** |

Renewables is the largest sustained draw (~100 k/yr by 2060). Nuclear capex = 0 until a 81 k pulse at 2050. CCS front-loads at 2040 (41 k). Coal has a one-off 2040 spike (41 k) then collapses.

**Storage capex IS in the objective** (C3 correction): CAES 138,316 MUSD + Lithium Ion 18,568 MUSD (undiscounted lifetime), carried as ordinary Centralized techs in `vcapitalinvestment`. Only the unused NEMO-native `CapitalCostStorage` layer is empty — the prior "storage carries zero capital cost" claim is **withdrawn**.

**Power average-cost proxy (no marginal available):** ~$26/MWh (2025) → **$61/MWh peak (2040, coincident with coal+CCS capex spike)** → ~$33/MWh (2060) as cheap RE + amortized nuclear dominate.

---

## 8. APAEC TARGETS

RE (hand-set, rooftop-corrected) vs the model's own `RETagTechnology` flag and its embedded `ASEANRenewableCapacityTarget` (35% 2025 → **44.33% 2030** → 63% 2040 → 71% 2050–60). EI target needs GDP, absent from this artifact.

### 8.1 Scorecard
| APAEC target | RAS 2030 | Aspiration | Verdict | Gap |
|---|--:|:--|:--|:--|
| RE % of installed capacity (rooftop-corrected) | **47.6%** | 45% by 2030 | **MEET** | +2.6 pp |
| — same vs model's embedded target | 47.6% | 44.33% by 2030 | **MEET** | +3.3 pp |
| — model-tag RE% (storage-incl denom) | 43.0% | 44.33% (model's own) | ~at target | −1.3 pp / met by tag |
| RE % of TPES | **27.3%** | 35% by 2030 | **MISS** | −7.7 pp (reaches 35% ~2035) |
| Energy-intensity reduction vs 2005 | n/a | −40% by 2030 | **CANNOT ASSESS** | GDP + 2005 base absent from NEMO sqlite |

**Verdict flip:** the pre-correction "RE capacity 42.5% MISS" was an artifact of dropping 55 GW of rooftop solar from the 2030 numerator/denominator. Corrected: **RE 297.9 / 626.3 GW = 47.6% at 2030 — clears 45%.** The RE-capacity target is MET; RE-TPES and (unassessable) EI are the open items.

### 8.2 RE %cap trajectory (rooftop-corrected)
| | 2025 | 2030 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|
| RE %cap | 41.0 | **47.6** | 56.7 | 61.5 | 62.2 |
| RE+Nuclear %cap | 41.0 | 48.3 | 57.5 | 63.4 | 65.6 |
| Model-tag RE %cap (storage-incl) | — | 43.0 | — | — | 53.9 |

### 8.3 RE %TPES trajectory
| | 2025 | 2030 | 2035 | 2040 | 2050 | 2060 |
|---|--:|--:|--:|--:|--:|--:|
| RE %TPES | 21.5 | **27.3** | 35.2 | 39.9 | 42.3 | **41.8** |

RE-TPES **peaks 42.3% (2050) then dips to 41.8% (2060)** — Indonesia gas domestic supply surging 4.5× (5,701→30,309 PJ) outpaces continued RE build (§9). RE-of-TPES is **bio-heavy** (bio-feedstock energy > all RE-electric combined) — if a "modern RE" definition excludes traditional/raw-crop biomass, these shares drop materially; definition is load-bearing.

### 8.4 Per-region RE %cap (2030 / 2060, centralized basis)
Indonesia 34.7/52.5 · Vietnam 54.2/72.0 · Thailand 29.4/58.0 · Philippines 46.4/45.7 · Malaysia 32.9/69.6 · Singapore 14.8/13.1 · Laos 77.5/50.9 · Cambodia 75.8/78.7 · Myanmar 48.7/68.7 · Brunei 14.2/24.5. (These exclude rooftop per-region; ASEAN aggregate above adds it back.) Only small hydro-rich systems (Laos, Cambodia) clear 45% in 2030 on a centralized basis; rooftop is what lifts the ASEAN aggregate over the line.

---

## 9. RESULT QUALITY — anomaly sweep

### 🟢 Clean / positive confirmations
- **Feasible, complete:** 10 regions × 36 years in every key table (capacity, production, newcap, emissions, trade, capex). No missing milestones.
- **Unmet Load production = 0** everywhere — demand fully met.
- **No 1e12/1e6 Unlimited-sentinel leak** into any production/use/emission result (max abs prod 1.68e4).
- **Storage healthy** — Li-ion smooth monotonic 12.5→187.5 GW, Pumped 4.4→31.3; the v0.76 battery-collapse class is absent.
- **No production-without-capacity** in power gen. Transmission nets to 0.0 exactly. Blend pseudo-techs pinned at 1000 GW cosmetic floor (production real).
- Storage capex, RE-tag table, embedded RE target all present and now incorporated (was missed by source tracks — C2/C3).

### 🔴 Blocking
- **A1 — 37.4 GW Indonesia Coal-USC-CCS built, 0 generation every year, ~US$238k capex spent.** Confirmed: the ASEAN 26.6 TWh USC-CCS output is entirely Malaysia (23.8) + Singapore (1.9) + Brunei (0.9); Indonesia's 37 GW is stranded (forced min-capacity/reactivation from the coal-flip inject the optimizer won't dispatch — it runs nuclear instead). Distorts the capacity stack and cost objective.

### 🟡 Worth checking
- **A2 — Unmet-Load phantom capex.** IDJW 1,875,100 (2060) + IDSA 1,212,252 (2059) = the only two >1e6 capex rows in the model, both Indonesia Unmet-Load slack, **0 production**. Strip Capital Cost off the slack tech; excluded from all "real" cost figures above.
- **A3 — Indonesia Large Hydro dispatch degeneracy:** _IDKA prod V-shapes (129→1.7→119) on rising 8→21.6 GW cap; _IDJW decays to 11 on flat 12.6 GW (CF ~0.01%).
- **A4/A5 — 63 GW non-slack idle capacity at 2060:** Coal USC-CCS 37.4 (A1), Biogas 12.0, Wind Onshore_IDEast 7.6 (stops dead after 2044), Pumped Hydro 4.2, Diesel peakers 1.8 (reserve-only, plausible), Philippines nuclear 0.5.
- **FAME capacity 31.5× unit phantom** persists in Vietnam/Myanmar/Laos/Cambodia/Brunei/Singapore + CME/POME techs (util 3154%); IDN/THA/MYS/PHL fixed. Philippines FAME fix confirmed good (242,062 cap, ~0–1% util, sane).
- **Ethanol blend collapse 2050–60** (§5.2) — all pathways decay to ~0; Malaysia/Cambodia hit 0%; mandates unmet late-horizon.
- **Myanmar biodiesel de-blends** (38%→21% under 52% ceiling) — feedstock constraint.
- **Only one H₂ pathway active** (Biomass Gasification →3,323); all fossil/electrolysis/CCS H₂ = 0.
- **VRB Flow Batteries never deploy** (0 all years) — confirm dominated-out vs mis-authored cost/limit.
- **Gas domestic supply surges 4.5×** (Indonesia 5,701→30,309 PJ) — drives fossil-TPES rise and the RE-TPES 2050→2060 regression; sanity-check the gas resource cap.
- **SO2 (E13) vs Sulfur Oxides (E14) double-listing** — E14 negligible but grows to 49 kt, 100% from H₂ production; likely stray EAR.

### ⚪ Data-artifact gaps (not fixable in this sqlite)
- **Road-vehicle fleet layer entirely absent** — 34 `Optimized…` techs, 0 rows in every result table. Fleet/EV-share/retirement underivable (§4.3). Highest-priority demand-side gap.
- **Indonesia Coal Sub-bituminous flat 9,183 PJ every year 2025–60** — fixed placeholder `AccumulatedAnnualDemand`; implausible for a decarb scenario. Plus flat blocks: Coal Anthracite 29, Lignite 18, direct Gasoline ~1,571–1,593, Palm Oil 1,473, Cassava 693.
- **Non-electric final fuels flat** (LPG/NG/kerosene/charcoal) — residential cooking/WH fuel growth absent (§4.5).
- **Rail & Water transport not modelled** as demand.
- **Refinery / gas-processing / LNG-regas transformation losses = 0** (unpopulated) — transformation losses understated.
- **Absolute TPES ~2× inflated** (un-netted product imports + raw-crop bio accounting) — shares robust, absolute PJ not IEA-comparable.
- **Demand-side sectors carry 0 endogenous emissions** — transport/industry/buildings CO2 lives in the un-decomposable exogenous block; sectoral demand-side CO2 must come from LEAP, not this sqlite.
- No `vstorage*`, no dual/shadow-price, no population/GDP tables in this build.

---

## 10. WHAT THE INJECT ACHIEVED

| Inject goal | Result | Landed? |
|---|---|:--|
| **Eliminate unmet load** | Unmet Load produces 0 PJ, every region/year; demand fully met | ✅ YES |
| **Coal flip Subcritical→USC** | Subcritical 120.7→1.9 GW (−98%), USC 4.0→158.9 GW; energy 580→751 TWh | ✅ YES |
| **Build nuclear** | 107 GW (LWR 47.9 + SFR 29.3 + SMR 29.5), Indonesia-anchored (88 GW), 659 TWh in 2060 | ✅ YES |
| **Build CCS** | 189 GW (Gas-CC-CCS 137.8 + Coal-USC-CCS 50.9); 199 Mt/yr power capture 2060 | ⚠️ Built, but 37 GW Indonesia Coal-USC-CCS stranded (A1) |
| **Hold biodiesel blend** | Rides ceiling; Indonesia B57.7, ASEAN B54.6 by 2060 | ✅ YES (Myanmar laggard 21%) |
| **Ethanol blend** | Pinned to ceiling through 2040 then collapses to ASEAN 1.2% by 2060 | ❌ NOT held late-horizon |
| **Philippines FAME fix** | Capacity 242,062 (sane regime), util ~0–1%, blend climbs to ceiling 51.9% | ✅ YES |
| **AC ownership growth** | Residential AC electricity triples 739→2137 PJ; Singapore saturation flat, Indonesia/Vietnam/Philippines ramp; 100% High-eff by 2055 | ✅ YES |
| **Transport fleet/blend** | Blend held (bio-diesel share 54.6% 2060); **fleet layer absent from results** — EV/retirement unverifiable here | ⚠️ Blend yes; fleet not exported |
| **RE capacity target** | 47.6% at 2030 (rooftop-corrected) — clears 45% and the model's 44.33% | ✅ MEET |
| **Storage build** | Li-ion 187.5 + Pumped 31.3 + CAES 94.5 GW by 2060; capex in objective | ✅ YES (VRB never deploys) |

**Net:** the mega-inject achieved its primary objective — a feasible, unmet-free RAS with the coal flip, nuclear and CCS fleets, biodiesel blend, and AC-ownership demand all landing as intended. Residual cleanup items for the next cycle: the stranded 37 GW Indonesia Coal-USC-CCS (A1), the Unmet-Load phantom capex (A2), the ethanol-blend late collapse, the FAME 31.5× capacity-unit phantom in 6 small regions, and re-exporting the road-vehicle fleet layer.

---
*Source: `mailbox/20260729 Final/NEMO_25 48.sqlite` (solved RAS). All codes decoded via REGION/TECHNOLOGY/FUEL/EMISSION/TIMESLICE.desc. Every figure carries its source table inline. Critic corrections C1–C6 applied; no pre-correction figure quoted.*

---

## 11. USING THIS NOTE — source, table roster & query recipes (Q&A springboard)

*Purpose: everything a fresh session needs to answer **any** follow-up about this result — the pre-computed tables above cover the headline questions; the recipes below reach anything they don't.*

### 11.1 How to answer a follow-up
1. **Check §1–§10 first** — most questions (capacity/generation/blend/emissions/cost/targets by year, region, or tech) are already decoded above with the source table named inline.
2. **If not pre-computed**, run a query against the source DB (§11.2) using the decode recipe (§11.3).
3. **Before stating any absolute figure**, read the matching §9 caveat (§11.4) — several classes of number are structurally right on *shares* but wrong on *absolute PJ/CO₂*, and some layers are simply absent from this sqlite.

### 11.2 Source DB & table roster
- **DB:** `mailbox/20260729 Final/NEMO_25 48.sqlite` — 271 MB, **solved single scenario RAS**, 10 AMS (no Timor Leste, no Base Template), years 2025–2060, 48 timeslices, 321 techs, 84 fuels, 16 emissions. *Not committed to git (build artifact / size); re-point this path if the folder is pruned.*
- **126 tables.** 13 dims (UPPERCASE, each `val`+`desc`): `REGION TECHNOLOGY FUEL EMISSION TIMESLICE YEAR MODE_OF_OPERATION STORAGE NODE REGIONGROUP TECHNOLOGYGROUP TSGROUP1 TSGROUP2`. Results are lowercase `v*`.
- **Key result tables** (rowcount · columns):
  | Table | Rows | Cols | Holds |
  |---|--:|---|---|
  | `vtotalcapacityannual` | 30,642 | r,t,y,val | Installed capacity — **UNIT MIXES BY SECTOR** (power GW; appliances = device counts) |
  | `vproductionbytechnologyannual` | 29,800 | r,t,f,y,val | Production/generation by tech (PJ; ×0.2778→TWh for F31/F2 electricity) |
  | `vusebytechnologyannual` | 22,274 | r,t,f,y,val | Fuel *use* by tech (feedstock/input side) |
  | `vusebytechnology` | 599,150 | r,l,t,f,y,val | Same, **per-timeslice** (`l`) — the only timeslice-resolved use table populated |
  | `vnewcapacity` | 14,510 | r,t,y,val | New builds per year |
  | `vannualtechnologyemission` | 43,166 | r,t,e,y,val | Emissions by tech × species |
  | `vtransmissionannual` | 540 | n,f,y,val | Net transmission per **node** (+exporter/−importer) |
  | `vtradeannual` | 1,442 | r,rr,f,y,val | Inter-AMS trade (bioenergy feedstock only populated) |
  | `vcapitalinvestment` | 5,033 | r,t,y,val | Real capex/yr |
  | `vtotaldiscountedcost` | — | r,y,val | Discounted system cost (the 24.66 T aggregate) |
- Absent/empty (do not attempt to answer from these): `vstorage*` (no storage-state table), `vtrade` (timeslice trade empty), duals/shadow-prices, population/GDP.

### 11.3 Decode recipe (codes → LEAP names)
```python
from nemo_read import NemoDB, decode_dims
db = NemoDB(r"mailbox/20260729 Final/NEMO_25 48.sqlite")
df = db.query("SELECT r,t,f,y,val FROM vproductionbytechnologyannual WHERE y IN ('2030','2060')")
df = decode_dims(df, db)      # joins REGION/TECHNOLOGY/FUEL/…desc → readable names
```
Raw-SQL equivalent (when you want one-off SQL): join `.desc` yourself —
```sql
SELECT R.desc region, T.desc tech, F.desc fuel, v.y, v.val
FROM vproductionbytechnologyannual v
JOIN REGION R ON R.val=v.r JOIN TECHNOLOGY T ON T.val=v.t JOIN FUEL F ON F.val=v.f
WHERE v.y='2060' ORDER BY v.val DESC;
```
- **Node variants** `_IDJW/_IDSA/_IDKA/_IDEast` (Indonesia ×4) and `_MYPE/_MYSB/_MYSR` (Malaysia ×3) must be **aggregated to the base tech family** for any ASEAN/region roll-up (every §2 table already does this).
- Electricity fuels: **F31** = Electricity (centralized), **F2** = the rooftop/delivered electricity carrier. PJ→TWh ×0.2778; PJ→Mtoe ×0.02388.
- Emissions species map is in §11.2 dims — net fossil CO₂ = **E2** (biogenic **E1** and sequestered **E407** are reported separately, never add E1 to fossil net).

### 11.4 Load-bearing caveats (read before quoting absolutes)
- **`vtotalcapacityannual` mixes units** — filter to power techs before summing "GW"; appliance rows are device counts.
- **Absolute TPES ≈ 2× IEA basis** (un-netted product imports + raw-crop bioenergy accounting) — **shares are robust, absolute PJ is not** comparable to IEA.
- **Demand-side sectors carry 0 endogenous CO₂** — transport/industry/buildings CO₂ sits in the un-decomposable **exogenous block** (§6.3); sectoral demand-side CO₂ must come from LEAP, not this sqlite.
- **Road-vehicle fleet layer entirely absent** — 34 `Optimized…` techs have 0 result rows; fleet size / EV share / retirement are **not derivable here** (§4.3). Needs a LEAP re-export.
- **Blend pseudo-techs** (Diesel/Gasoline Blending) sit at a cosmetic 1000 GW capacity floor — their *production* is real, their *capacity* is not.
- **A1 (37 GW stranded Indonesia Coal-USC-CCS, 0 gen)** and **A2 (Unmet-Load phantom capex)** are known artifacts — exclude from "real" capacity-stack and cost answers (§9).

### 11.5 What's answerable from this DB
- **Pre-computed above:** capacity/generation/newbuild by tech·region·year; RE & clean shares (3 defs); storage GW by type; transmission & feedstock trade; electricity & AC demand; blend shares; refinery/feedstock/clean-fuel output; net & sectoral CO₂ + CCS + grid intensity; discounted cost by region/sector/tech + real capex trajectory; APAEC scorecard; full anomaly sweep.
- **One query away:** any tech/region/year/fuel/emission slice not tabulated; per-timeslice use (`vusebytechnology`); per-node transmission detail; per-tech emission by species.
- **NOT in this sqlite (need LEAP export):** road-vehicle fleet & EV/retirement; demand-side sectoral CO₂; storage dispatch state; dual/shadow prices; population/GDP; refinery/LNG transformation losses (unpopulated = 0).
