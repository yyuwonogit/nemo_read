# Transport — reply to your 2026-07-21 handover (fixes + canon + §4 questions)

**From:** AEO-9 Transport data team (we hold the context) · **To:** LEAP inject team (you hold the canon)
**Re:** `TRANSPORT_HANDOVER_fixes_and_canon_20260721` · **Area:** aeo9_v0.75

Thanks — the drop injected clean (880 rows) and your 164-row correction delta
is verified on our side (F1 40 / F3 40 / A9c 40 / A1 40 / A9b 4, all matching
what we asked). Below: acknowledgements on canon (§2/§3 — your call, accepted),
our answers to your §4 needed/not-needed questions (our call, context), two
context positions we've now settled internally, and one new deliverable
(`historical_stock_patch_20260721.csv`).

## §1 corrections — confirmed received, nothing to re-send

V5 base-stock consumed correctly (anchors match: BRN Bus 2,188 / CAM 65,996 /
IDN 298,260), F1/F3 FE, A1 phantom-fleet re-point, A9b/A9c all landed. Good.

## §2 canon roster — accepted, and we were already insulated

Agreed and adopted: when we **name** a LEAP class/fuel we'll use the canon
token (`Bus`, `PassengerCar`, `Truck`, `Motorcyle`; `Blended Gasoline`,
`Blended Diesel`, `Electricity`, `Natural Gas`, `Hydrogen`). Note our five data
CSVs already ship neutral **source** tokens (`2W`/`LDV`/`Bus`/`Truck`,
`Gasoline`/`HybridDiesel`/…) that your remap handles — the only off-roster slip
was the free-text **"PPV CNG"** label in our F1 action item, which has no LEAP
home. Corrected: it is `PassengerCar Natural Gas`. Good to hear **`Blended
Gasoline` is now settled on BOTH trees in v0.75** — that closes our earlier §7.4
flag (your adapter's stale `Gasoline` availability-map entry).

## §3 survival profile — you're right, we withdraw V6 and the B2 framing

Accepted in full — this is your canon call and our B2 assumption was wrong.
We now understand LEAP retires via **stock-overflow** (base-year `Stock` +
`Sales`, scrap whatever exceeds the Stock trajectory; `Scrappage = 0` = "no
*extra* forced scrappage", not "no retirement"), and that the road panel has
**no survival/vintage/lifetime paste target** — so `survival_profile.csv` (V6)
was never injectable. **We withdraw V6 and retract the B2 "fleets never retire"
framing.** We'll keep sending **V2 (sales magnitude) + V5 (base-year stock)** and
let LEAP's turnover do the rest.

One context note (not a pushback): our per-class Weibull kernels
(`weibull_survival.py`) stay as an **internal** artefact — they are how our V2
sales are back-derived from our Gompertz/FE-OLS stock trajectory. LEAP's
*forward* stock stays yours (overflow, probabilistic); we treat your forward
Stock-by-fuel as **review-only** and will not try to replicate it — so there is
**no V-7 reconciliation** and no ±5 pp / ±10% gate to clear. See position 2.

## §4 — needed / not-needed (our context calls)

| Item | Owner | Needed for results? | Our reasoning |
|---|---|---|---|
| **A11** IW CR `_x000D_` | IW-FEI author (not us) | **Not needed** | Cosmetic; Inland Waterways is a marginal mode (your own note: "Indonesia's tiny declining barge use"). No result moves. Clean it if trivial, otherwise ignore. |
| **A14** `Transport_` underscore | central/keys (not us) | **Not needed** | Resolves in-LEAP (your words); only offline joins break. No result impact. |
| **A14** Rail $-vintage (2020 vs 2021 USD) | Rail/keys author (not us) | **Minor — worth a cheap fix, not by us** | A real unit inconsistency that mis-scales Rail energy-intensity-per-GDP by ~the CPI delta, but Rail is a small ASEAN mode so it's second-order. Fix if cheap; not blocking. |
| **A9a** PHL aviation FEI +1% tail | **aviation team** | Their call | Owner confirmed = aviation. We hold no aviation-intensity view. Single-region stray edit; strip if they agree. |
| **A12 / B4 / B5** SAF provenance / **FEI=0** / CO₂ basis | **aviation/emissions team** | **B4 is important — flag to them** | Owner confirmed = aviation. Of these, **B4 (SAF FEI evaluates to 0)** is the consequential one: if the per-fuel-intensity method drives Domestic Air, the flagship Indonesia SAF mandate (1→50% by 2060) delivers **zero SAF demand** — a scenario-defining error. Not ours to fix, but please make sure the aviation team drives it. A12/B5 are lower-stakes provenance/accounting cleanups. |
| **P1** SAF mandate trajectories | **aviation team** | Not ours | We hold no national SAF/aviation blend data; POLICY_LANDSCAPE.md is road-only. Their rows to maintain. |
| **B1** Road tailpipe emissions | **handled outside this pipeline** (our lead's decision) | **Needed, being driven elsewhere** | Road CO₂/CH₄/N₂O are structurally under-reported without it (the 🔴 item), so it *is* needed for the full transport GHG story — but per our modelling lead it is being handled outside this data-inject track, not by us and not in this cycle. Please treat B1 as owned externally, not dropped. |
| **A4 / A6** CA Road Stock paste | **shared — you stop the *forward* paste, we own the *historical* one** | **Forward: done. Historical: we now ship it clean** | Forward stock: correct, overflow from V5+V2 means the class-paste inflation (A4) and IDN-2015 ÷129.4 + splice corruption (A6) cannot recur. Historical window (2005–2024): that fleet is **our hard input** — not overflow-derived — so we're shipping it clean as `historical_stock_patch_20260721.csv` to **replace** the corrupted live CA Stock series. See position 1. |

## Two positions we've now settled (our lead's ruling)

These were open questions in our draft; our modelling lead has now closed them,
so we state them as positions rather than asking:

1. **Historical stock (2005–2024) is OUR hard input — we author it, please
   paste it.** The historical road fleet is our number to set (this is the
   context call our lead has now settled): it is authored by us and pinned, and
   is scenario-invariant (**Current Accounts = ATS = BAS = RAS** on those
   years). We're shipping it as **`historical_stock_patch_20260721.csv`** (160
   rows = 10 AMS × 16 canon vehicle×fuel, `Stock` Data() series 2005–2024,
   `Current Accounts`, canon tokens, absolute Vehicle). It lands on the same
   `Demand\…\Road\<Vehicle>\<Fuel>:Stock` slots that already carry per-AMS CA
   Data() series in your model — **20 of these 160 series already start at 2005
   today** — so it drops into the existing pattern; **please paste it to replace
   the corrupted live CA Stock series** (the A4 class-paste / A6 IDN-2015 ÷129.4
   splice), which fully closes A4 / A6a / A6b. One thing for you to confirm on
   the canon side: that `Stock` under Current Accounts is the intended target
   for our historical paste and it won't collide with how your forward
   stock-overflow initialises — you own that mechanic; we just need the
   historical years to read our values. The patch is clean, class-distinct, and
   2024 is anchored to published national totals (and reconciles exactly to the
   V5 base-year fleet we already shipped).

2. **Forward stock is yours (overflow, probabilistic) — review-only, no
   reconciliation.** We will **not** replicate LEAP's forward Stock-by-fuel. It
   arrives probabilistically from V5 base-year + V2 sales via overflow; we'll
   read the full result later purely for review, **not** to match it against our
   modelled trajectory. So the earlier V-7 cross-check is **withdrawn** — no
   shared spot-year Stock dump needed, no ±5 pp / ±10% gate. Our Gompertz/FE-OLS
   stock stays internal (it only exists to back-derive V2 sales).

Everything else is settled our side. Questions → yudiandra.y@gmail.com.
