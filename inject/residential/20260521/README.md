# Residential inject handover — 2026-05-21

From: AEO-9 Residential modelling team → LEAP inject team.
LEAP area reference: `aeo9_v0.46`.

This bundle contains **(1)** the ready-to-paste **Lighting** inject and
**(2)** a **structure-create request for AC + Refrigeration**. Fridge/AC
data CSVs are NOT in this bundle yet — they wait on the structure
rebuild described below.

---

## 1. `lighting/` — ready to paste

LEAP Lighting branch is a five-technology stack
(`Demand\Residential\Projections\Lighting\Electricity\<Tech>`).

**PASTE TARGETS:**

- `lighting_tech_shares.csv` — per-tech `Activity Level` (% of grid-lit
  households). Columns: Country, Year, Scenario, Tech, share_percent,
  source. 5,400 rows (10 AMS × 36 yr 2025–2060 × 3 scen × 5 tech). The
  5 Tech rows per (Country, Year, Scenario) sum to 100. Filter by
  Scenario, then map each Tech → its `…\Electricity\<Tech>` leaf
  `Activity Level`.
- `lighting_bulb_wattage.csv` — per-tech `Bulb Wattage` (W). Columns:
  Country, Tech, watts, source. 50 rows (10 AMS × 5 tech). LED = per-AMS
  catalogue median (7–13 W; LEAP default is 7.2 W if you prefer);
  Incandescent 60 / Halogen 42 / CFL 14 / Fluorescent 32 W.

**DO NOT paste** — `Final Energy Intensity` (LEAP formula),
`BulbsPerHH` / `LightingHours` (keep LEAP defaults 7 / 6 h this cycle),
the `Other` arm (Kerosene+Candles, Solar — deferred).

**PROVENANCE (reference only, do not paste):**

- `lighting_tech_mix_2023.csv` — the 2023 base-year tech mix the
  trajectory evolves from (U4E-triangulated placeholder, refresh pending).
- `*.txt` — method sidecars (sources, scenario windows, validation).

Scenario strings are plain `BAS` / `ATS` / `RAS`.

---

## 2. `ac_fridge/` — structure-create request (action needed before data)

- `structure_request_AC_fridge_2layer_20260521.md` — please build the
  **2-layer** nested tree (Size → Low/Mid/High efficiency, 9 leaves) for
  **both Refrigeration and AC**, per the variable mapping inside. This
  replaces the flat 3-tier placeholder seen in the 2026-05-20
  refrigeration handover. Once built, re-issue the AC + Refrigeration
  handovers and we will ship the per-leaf data CSVs.

**Open item for you:** confirm the AC parent branch name
(`…\Projections\Air Conditioning`? `Cooling`?).

---

## Country names

Source-CSV form (e.g. `Brunei Darussalam`, `Lao PDR`, `Viet Nam`) — map
to LEAP region names on your side.
