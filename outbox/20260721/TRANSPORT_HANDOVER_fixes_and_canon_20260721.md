# Transport — what we fixed for you + how to author against canon (2026-07-21)

**From:** LEAP inject team (we hold the canon structure) · **To:** Transport team
**Re:** your `transport_leap_input_20260720` drop · **Target area:** aeo9_v0.75

Your five data CSVs were clean and injected as-is (880 canonical rows, no
canon-faithful combo dropped). This note covers the **corrections we applied on
your behalf**, and — more importantly — **how to author so we stop re-running
the same fixes every cycle**. Two of these have now recurred across drops; the
goal of §2 and §3 is that they never come back.

---

## 1. Corrections we applied for you (164-row delta, all canon-validated)

You don't need to re-send anything — these are done on our side:

| Item | Fix | Where it landed |
|---|---|---|
| **V5 base stock** | Consumed your new `stock_count` (once per vehicle, not summed) — the 30–100× base-stock error is gone | `Key\…\BaseYear_StockData\<Veh>` (matches your anchors: BRN Bus 2,188 / CAM 65,996 / IDN 298,260) |
| **F1** PPV CNG FE 30→26 | Applied to `PassengerCar\Natural Gas` (see §2 — there is no "PPV" branch); also satisfies your B3 optional NG lift | `Demand\…\PassengerCar\Natural Gas\Natural Gas : Fuel Economy` |
| **F3** Truck NG FE 12→5 | Set 5 fleet-wide + Current Accounts | `Demand\…\Truck\Natural Gas\Natural Gas : Fuel Economy` |
| **F2** ERIA citation cleanup | Handled automatically — our V4 Mileage re-inject overwrites the old ERIA provenance | Mileage rows |
| **A1** Truck NG phantom-fleet | Re-pointed the `Sales` formula from the Truck-**Electricity** share key to the Truck-**Natural Gas** key | `Demand\…\Truck\Natural Gas : Sales` |
| **A9b** BRN mileage-correction | Reverted the stray `Interp(2024,1,2030,0.9)` to constant `1` | `…\PassengerCar\Blended Diesel\Blended Diesel : Mileage Correction Factor` |
| **A9c** First Sales Year | Harmonised `2024` → `BaseYear` (cosmetic) | `…\PassengerCar\<fuel> : First Sales Year` |
| **A7** LDV × Hydrogen | Nothing to do — your CSVs emit zero, so the slot stays zero | — |
| **V6 survival curve** | **Discarded** — see §3 | — |

---

## 2. Author against the canon roster — the remap is ours, but the NAMES must be canon

We run the alias remap for you (`LDV → PassengerCar`, `2W → Motorcyle`,
`Gasoline → Blended Gasoline`, etc.) — that is our job and stays our job. But
when you **name a LEAP class or fuel** anywhere we read it (a paste target, an
audit item like "PPV CNG", a disposition), use the **exact canon token**.
Every off-roster name forces us to guess a remap or silently drop a row.

**Road vehicles — there are exactly four. Nothing else exists in LEAP:**
`Bus`, `PassengerCar`, `Truck`, and `Motorcyle` (LEAP's own misspelling on the
Demand tree; `Motorcycle` on the Key tree — we handle both).
- **There is no `PPV` class, no `LDV` class, no `2W` class in LEAP.** `LDV`/`2W`
  are fine as *your source tokens* (we map them), but "PPV CNG" in F1 had **no
  LEAP home** — we mapped it to `PassengerCar\Natural Gas` because that's the
  only CNG branch. If a value is really pickup-only, LEAP can't hold it
  separately; it lands on `PassengerCar`. Name it `PassengerCar` next time.

**Fuels — there are exactly five, and the gasoline/diesel ones are *Blended*:**
`Blended Gasoline`, `Blended Diesel`, `Electricity`, `Natural Gas`, `Hydrogen`.
- **`Blended Gasoline` is now the fuel token on BOTH trees (Demand and Keys) in
  v0.75 — settled.** Do not write `Gasoline`, `Diesel`, `CNG`, or `Hybrid`.
- Per-vehicle availability differs and is real: `Motorcyle` carries only
  `Electricity` + `Blended Gasoline`; `PassengerCar` carries no `Hydrogen` on
  the Demand tree (but does on the Keys sales-share tree). Don't author a fuel a
  vehicle doesn't have — it has no branch.

If you author to these tokens, nothing needs remapping and nothing is dropped.

---

## 3. How LEAP retires fleets — please stop shipping survival profiles

`survival_profile.csv` (V6) and audit B2 assumed LEAP needs a survival kernel or
"fleets never retire." **That is not how this model works, and it caused us to
nearly block your inject.** The truth:

- LEAP retires via **stock-overflow**: the road branches carry a specified
  `Stock` trajectory, and LEAP scraps whatever accumulated `Sales` would push the
  fleet above it. **`Scrappage = 0` is not "no retirement"** — it means "no
  *extra* forced scrappage on top of the overflow."
- The road panel (`Demand\…\<Veh>\<Fuel>`) has **no survival / vintage / age /
  lifetime variable** — so a per-age Weibull curve has **no paste target** and
  cannot be injected.
- What LEAP needs from you, you already give: **base-year stock (V5) + sales
  magnitude (V2)**. LEAP's internal turnover does the rest. No survival file, no
  scrappage-panel edit.

So: keep sending V2 + V5; drop V6 and the B2 framing.

---

## 4. What's out of this inject — do you consider it necessary?

We did **not** inject the items below. You flagged them as not-your-data, and
we agree they don't belong in a transport-fleet paste — but you own the call on
whether they matter for your results. **Tell us needed / not-needed:**

- **A11** — `_x000D_` CR artifacts on the 10 Inland Waterways FEI `If()`
  expressions. Cosmetic; IW branch. Needed?
- **A14** — `Demand\Transport_\…` underscore self-references + the Rail
  Activity-Level dollar-vintage vs the GDP driver. Central/keys plumbing. Needed?
- **A9a, A12, B4, B5, P1, B1** — aviation FEI tail, SAF provenance / FEI=0 /
  CO₂-basis, SAF mandates, road tailpipe emissions. These are the
  **aviation/emissions team's**, not ours or yours. Confirm that's the right
  owner, or flag if you need them driven.
- **A5/A6** — you asked us to stop pasting CA Road Stock and let LEAP derive.
  We already don't paste a Stock series; LEAP derives forward stock from V5+V2
  via the §3 overflow. So this is effectively done — flag if you meant something
  more.

Everything data-side is settled. Questions → yudiandra.y@gmail.com.
