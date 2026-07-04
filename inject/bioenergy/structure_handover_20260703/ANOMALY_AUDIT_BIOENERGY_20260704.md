# Anomaly audit — bioenergy slice (`aeo9_v0.67_w_results`)

This is **your team's slice of the full canon anomaly audit** (`CANON_ANOMALY_AUDIT_20260704.md`, generated 2026-07-04 by an offline sweep over the four scenarios that matter — Current Accounts, Baseline Simulation, AMS Target Scenario, Regional Aspiration Scenario). It carries over, verbatim and unchanged, only the findings that touch branches **bioenergy owns or authors**: the supply fuels under `Resources\Primary\` and `Resources\Secondary\` (the five CSV crops — Cassava, Coconut Oil, Corn, Palm Oil, Sugarcane — plus Molasses, Palm Oil Mill Effluent, Bagasse, Wood, Biomass, and the Arable/Perennial land pseudo-fuels) and the two Key drivers wired to your sector (`Key\Optimized Trade`, `Key\Biofuel Blending Targets`). We have **not** changed any counts, tags, or grades, and we have **not** added new findings. Each item keeps its **NEW/KNOWN** and **VERIFIED/SUSPICIOUS** flags; Part-B items keep their 🔴/🟡/🟢 grade. Coal/oil/gas/NGL/nuclear/refined-product items are the fossil team's and renewable-power caps are the power team's — those were deliberately left out (see the exclusion note at the end). You are the right people to **judge and fix** the items below; where something is clearly deliberate design (Arable/Perennial), we flag it as such. "Cross-tree note" lines mark defects that live in a Key/Resources branch your sector merely references, so you know they are upstream of you and owned elsewhere.

---

## Part A — Incorrectly inputted (anomalies in authored values)

### A7. Cross-region outliers / unit slips

- **NEW · SUSPICIOUS — Brunei Biomass Maximum Production = 8,773 TWh**, ~1,600× the sibling median and larger than all-ASEAN primary energy — near-certain unit slip (GWh/TJ intended). **Propagates**: Brunei Bagasse & Wood caps are authored as `Biomass:Maximum Production[TWh]`. *12 rows. Resources.*

### A12. Comment hygiene hiding data problems

- **KNOWN — resources `?~Former expression:` reverted caps** (RAS less constrained than ATS on **Thailand Biomass**), `~`-dialect ×101, `_x000D_` in comments ×32. *Resources.*
  > Bioenergy-relevant slice: the reverted-cap case explicitly named here is **Thailand Biomass**, one of your Primary fuels — RAS ends up *less* constrained than ATS. The `~`-dialect (×101) and `_x000D_`-in-comment (×32) counts are the whole Resources tree, not bioenergy-only.

---

## Part B — Empty but important (graded)

### 🔴 RED — breaks the calc or actively distorts LP/results in the 4 scenarios now

2. **Zero-cost open supply/import routes.** *(KNOWN #24 · Resources)* In RAS, **191 (fuel,region) pairs have Maximum Production ≠ 0 with Production Cost = 0** (incl. Nuclear at Unlimited + $0), and **95 pairs have open Maximum Imports with Import Cost = 0** (Refinery Feedstocks/Gas, Renewable Diesel, Arable/Perennial ×12). **Mechanism:** a cap-open, cost-zero route is a free lunch the LP exploits regardless of realism — the exact mechanism behind the 2026-05-18 biodiesel-to-Timor-Leste and 2026-05-19 POME incidents.
   > This RED class spans several sectors' fuels (Nuclear and Refinery Feedstocks/Gas belong to fossil/power). The bioenergy-owned members are the ones to judge/fix on your side: the **Arable/Perennial ×12** open-import pairs, plus the open-production biofuels/crops that carry this shape (per your handover README §7.1: Secondary Biodiesel, Ethanol, Domestic Biogas, Renewable Diesel, Sustainable Aviation Fuel across all 12 regions; Corn and POME on Base Template + Timor Leste; Cassava among the `0.001`-placeholder import prices). The named incident history (biodiesel-to-Timor-Leste, POME) is on your fuels — this is the single most consequential class for bioenergy.

### 🟡 YELLOW — placeholder/template values silently shaping results (wrong numbers, not broken mechanics)

**Resources**

- **Consumer prices ~95 % zero** on the branches demand regressions reference (1,130 of 1,188 cells; **Bagasse**/coals/NG/MSW Industrial price 44/44 zero). **Mechanism:** the Exp/Ln price-elasticity shells evaluate `Ln(0)` → undefined or garbage, so fuel-switching response is silently priced at zero. (Same class hits industry's referenced prices.)
  > Bioenergy-owned member of this class: **Bagasse** Industrial Consumer Price (44/44 zero). The coals/NG/MSW members of the same 44/44 count are fossil/power/industry, not yours.

- **`Unlimited ? tbc` placeholder caps** survive on **Biomass**/Geothermal/Large Hydro/MSW (37 rows) → un-capped renewable supply in the very RAS scenario whose RE targets those caps should bind.
  > Bioenergy-owned member: **Biomass** (a Primary fuel you own). Geothermal / Large Hydro / MSW in the same 37-row group are power's renewable-generation caps — see the cross-tree note below.

- **NEW — Production Cost = `0.001` template** on the 7 variable renewables + Geothermal-class (all scenarios) and the **crops/Molasses**/MSW (CA/Baseline/ATS only — RAS has real injected costs). For crops this means the three non-optimized scenarios value feedstock at ~$0 → cross-scenario biofuel cost results are not comparable.
  > Bioenergy-owned members: the **crops and Molasses** carrying `Production Cost = 0.001` in Current Accounts / Baseline / AMS Target (RAS already holds your real injected costs). The 7 variable renewables + Geothermal-class in the same bullet are power's; MSW is not yours.

- **Arable/Perennial land pseudo-fuels** carry Maximum Imports = Unlimited at Import Cost 0 (RAS), and Perennial's cap is mis-tagged "Cubic Meter" vs Arable's "Thousand GJ" — free unlimited "land imports" if a trade route is ever enabled; the unit drift also breaks the GJ/ha anchor.
  > Fully bioenergy-owned. Note this is the *land-as-fuel* design (1 GJ ≈ 1 ha anchor) — the anchor itself is intentional; the flagged defects are the **Import Cost = 0 open route** and the **Perennial "Cubic Meter" unit-tag drift**, not the double-cap design.

### 🟢 GREEN — cosmetic, disabled plumbing, or plausibly-intentional zeros

- **Resources:** all-zero series on *closed* routes (cost 0 paired with cap 0 — unreachable today, but a tripwire target: reopening a cap without its cost row recreates the RED #2 exploit); "U.S. Dollar" vintage-less units (mostly on zero cells).
  > Applies to your closed-route fuel/region cells too: harmless *while* the cap is 0, but any future cap-reopen without a paired cost row re-arms the 🔴 B2 free-lunch class. Treat as a standing tripwire whenever you open a new production/import route.

---

## Cross-tree notes (defects upstream of you, owned elsewhere)

- **🔴 B2 — non-bioenergy members of the zero-cost-route class.** Nuclear (Unlimited + $0), Refinery Feedstocks / Gas, and the other non-feedstock fuels inside the 191 production / 95 import pairs are **fossil/power**. Your slice is only the Arable/Perennial ×12 imports and your open-route biofuels/crops (above).
- **🟡 `Unlimited ? tbc` renewable caps — Geothermal / Large Hydro / MSW** (part of the 37-row group) are **power**'s renewable-generation caps. Only Biomass in that group is yours.
- **🟡 Production Cost = 0.001 — the 7 variable renewables + Geothermal-class** portion of that bullet is **power**'s; only the crops/Molasses portion is yours.
- **🟡 Consumer-price `Ln(0)` class — coals / Natural Gas** members are **fossil**; MSW Industrial is **power/industry**. Only Bagasse is yours.
- **`Key\Optimized Trade` (495 routes) and `Key\Biofuel Blending Targets`** are the Key drivers your sector wires into. The master audit does not raise a *standalone* defect on these Key branches, but they are the enabling mechanism for the 🔴 B2 exploit on your feedstocks: a blend mandate with an open, zero-cost import route lets the LP source the whole region's feedstock through the free route. When you fix a zero-cost route on a traded feedstock (Biodiesel, Cassava, Coconut Oil, Corn, Ethanol, Molasses, Palm Oil, POME, Sugarcane), check the matching trade-route switch state (on in RAS/CNZ only). This is your tree, flagged here for completeness — no new finding is being asserted.

---

## Highest-leverage fixes for your team

1. **Brunei Biomass 8,773 TWh unit slip (A7).** Near-certain GWh/TJ→TWh slip; it propagates into Brunei Bagasse and Wood, which are authored *as* `Biomass:Maximum Production[TWh]`. One correction cascades to three of your fuels. *12 rows, SUSPICIOUS — confirm the intended unit/magnitude.*
2. **Zero-cost open routes on your feedstocks (🔴 B2).** The documented free-lunch class with real incident history on your fuels (biodiesel-to-Timor-Leste, POME). Confirm each open-production biofuel/crop either has its cost on the production process (fine) or needs a Production Cost / Import Cost trajectory; replace the Cassava `0.001` import-cost placeholder.
3. **Arable/Perennial open "land imports" + Perennial unit-tag drift (🟡).** Close the Import Cost = 0 open route and fix Perennial's "Cubic Meter" tag back onto the Thousand-GJ / GJ-per-ha anchor — without touching the intentional double-cap design.
4. **Crop / Molasses `Production Cost = 0.001` template in CA / Baseline / ATS (🟡).** RAS already holds your real injected costs; bring the three accounting scenarios into line so cross-scenario biofuel cost comparisons are valid.
5. **Thailand Biomass reverted cap (A12) and Bagasse zero Industrial Consumer Price (🟡).** Confirm RAS should not be *less* constrained than ATS on Thailand Biomass, and price Bagasse so its elasticity shell doesn't evaluate `Ln(0)`.
