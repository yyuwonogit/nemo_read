# Fridge inject — authoring guideline (for the refrigeration author)

> **Single source of truth: [../FRIDGE_ANATOMY.md](../FRIDGE_ANATOMY.md).**
> This guideline only restates the CSV→LEAP contract for authors. If anything
> here ever disagrees with FRIDGE_ANATOMY.md, the anatomy wins.
>
> Target area: `aeo9_v0.64_w_result`. We author into the structure LEAP
> actually has — **not** the flat tree / device-stock leaves in older drafts.

---

## 1. Where the data lands (two trees)

```
Key\Residential\Refrigeration\           ← DATA STORE (Activity Level = Interp)
   Percent Ownership, Size_Share\*, Efficiency_Share\*, Useful_EI\*

Demand\Residential\Projections\Refrigeration_\<Size>\<Eff_eff>   ← references Key
   leaf inputs that exist here: Activity Level, Efficiency, Demand Cost
```

`<Size>` = `Large/Medium/Small`. Efficiency naming differs by tree: **Key** is
flat `Large_High` with short token `High/Mid/Low`; the **Demand** leaf is
nested `Large\High_eff` keeping `_eff`. The adapter translates — you keep the
CSV columns (`High_eff/Mid_eff/Low_eff`).

---

## 2. CSV column → LEAP slot (only what `aeo9_v0.64_w_result` actually has)

| CSV column | LEAP target | Units | Status |
|---|---|---|---|
| `ownership_parent_pct` | Key `Percent Ownership` | % | injected |
| `size_share_pct` | Key `Size_Share\<Size>` | % | injected |
| `eff_share_pct` | Key `Efficiency_Share\<Size>_<Eff>` | % | injected |
| `useful_energy_intensity_toe` | Key `Useful_EI\<Size>` | TOE/HH | injected |
| `efficiency_pct` | leaf `Efficiency` | % | **to inject** |
| `demand_cost_usd_per_hh` | leaf `Demand Cost` | 2020 USD/HH | **to inject** (scenario-specific) |

**Not authorable in this area** (the variables don't exist on the live leaf —
FRIDGE_ANATOMY.md §1.3a): `Unit Capacity`, `Exogenous Devices`, `Capital Cost`,
`Fixed OM Cost`, `Variable OM Cost`, `Lifetime`, `Maximum Devices`. The
columns `unit_capacity_kw` and `device_thousand` (and the device-stock /
RAS-optimisation block in the inbound mapping doc) therefore have **no slot
here** and are dropped. They belong to the §1.3b device-stock leaf variant,
which is a different area version.

> **Canon update 2026-07-03 — the paragraph above is superseded on the
> current area.** Per the canon structure export
> (`LEAP structure/LEAP_STRUCTURE_ANATOMY.md` §2.1 + §10.2, from
> `aeo9_v0.67_w_results` 2026-07-02), the live area now carries the full
> device-stock panel (`Unit Capacity`, `Exogenous Devices`, `Capital Cost`,
> `Fixed/Variable OM Cost`, `Lifetime`, `Maximum Devices`, …) on the
> `Refrigeration_` tiers — authorable, but **only in the 7 scenarios that
> host the panel** (Set up, CNZ, RAS, LCO backup, RE LTRM ×3); the rows do
> not exist in CA / Baseline Simulation / AMS Target Scenario / RAS test.
> See `../structure_handover_20260703/README_RESIDENTIAL_CANON_STRUCTURE.md`.

Informational / derived (never injected): `leaf_ownership_pct`, `kwh_unit`,
`crf`, `tariff_usd_per_kwh`, `om_electricity_usd`, `price_usd`,
`annualized_capital_usd`.

---

## 3. Authoring rules you must keep

1. **Shares sum to 100.** `size_share_pct` across the 3 sizes; `eff_share_pct`
   across the 3 eff tiers within each size. The adapter does not re-normalise.
2. **Scenario behaviour (auto-detected, you don't tag):**
   - `ownership_parent_pct`, `useful_energy_intensity_toe`, `efficiency_pct` —
     scenario-invariant → authored once, applied to all scenarios.
   - `size_share_pct`, `eff_share_pct` — differ by scenario → per scenario.
   - `demand_cost_usd_per_hh` — **BAS/ATS = annualised capital; RAS = capital +
     electricity O&M** → scenario-tagged.
3. **Full year range 2014→2060.** Author every year; the inject overwrites the
   whole trajectory.
4. **Period decimals, comma list-separators** (standard CSV; the adapter
   enforces the LEAP `Interp(2014, v, …)` form).
5. **10 ASEAN members, no Timor Leste.** Source-form country names
   (`Brunei Darussalam`, `Lao PDR`, `Viet Nam`); the adapter maps them.

---

## 4. How to run it (Windows, LEAP open on `aeo9_v0.64_w_result`)

```
# build the Key-tree canonical (Phase 1 — already injected 2026-06-25)
python build_canonical_fridge_keys.py
#    -> canonical_fridge.csv (400 Key-tree rows)

# inject — one COM session, 3 scenarios, dry-run first
python inject_fridge_leap.py \
    --csv canonical_fridge.csv \
    --expect-area "aeo9_v0.64_w_result" \
    --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario" \
    --yes
```

- Let the **dry run** happen on a first push (don't `--skip-dry-run`); it
  checks every path exists before any write (reports `branch_not_found`
  instead of hanging).
- Confirm readback prints `N EXACT, 0 NORMALISED, 0 FAIL` per scenario.
- Dependency: `pip install pywin32` (`requirements.txt`). The adapter needs
  only the standard library.

The leaf `Efficiency` + `Demand Cost` inject (the 20260629 update) is a
separate Phase-2 build, pending — see FRIDGE_ANATOMY.md §4.

## Data-quality flag

`ownership_parent_pct` has a ~97.6→89.0 step at 2022→2023 in the source CSV
(historical/projection seam). The inject renders it faithfully; confirm it's
intended.

## Naming quick-reference

| | CSV | Key tree | Demand tree |
|---|---|---|---|
| Size | `Small/Medium/Large` | `Large/Medium/Small` | `…\<Size>` |
| Efficiency | `High_eff/Mid_eff/Low_eff` | `High/Mid/Low` (in `<Size>_<Eff>`) | `…\<Size>\<Eff_eff>` |
| Scenario | `BAS/ATS/RAS` | `Baseline Simulation` / `AMS Target Scenario` / `Regional Aspiration Scenario` | same |
