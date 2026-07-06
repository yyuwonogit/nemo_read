# Outbox — team canon handover packages (2026-07-04)

Ship-ready zip per sector team, built from the canon of LEAP area
`aeo9_v0.67_w_results` (7 exports: 4 Demand sectors + `Key\` + `Resources\` +
`Transformation\`). Each zip is self-contained — a team can use it without
LEAP, this repo, or any database.

Regenerate with `LEAP structure/tools/` + the per-team slice scripts; see
[docs/leap_structure_canon_sop.md](../docs/leap_structure_canon_sop.md).

## What each zip contains

Every zip has, at its root, that team's `structure_handover_20260703/`
package — plain-language **README**, the branch **tree(s)**,
**branch×variable×units** CSVs, the connected **`Key\`/`Resources\`/
`Transformation\` slices**, **4-scenario current-expression** dumps (Current
Accounts / Baseline / AMS Target / RAS), and the team's **anomaly-audit
slice** — plus a `guides/` subfolder with the team's authoring guide(s)/specs
where they exist.

| Zip | Tree(s) the team owns | Guides bundled |
|---|---|---|
| `bioenergy_canon_handover_20260704.zip` | `Resources\` (crops/biofuels) + `Transformation\` biofuel/clean-fuel production (325 br) | CSV_AUTHORING_GUIDE + BIOENERGY_CSV_SPEC |
| `transport_canon_handover_20260704.zip` | `Demand\Transport` + `Key\TransportDataStock` | CSV_AUTHORING_GUIDE + TRANSPORT_CSV_SPEC + INJECT_SOP |
| `residential_canon_handover_20260704.zip` | `Demand\Residential` + appliance `Key\` drivers | CSV_AUTHORING_GUIDE + AC/FRIDGE anatomy + FRIDGE_AUTHOR_GUIDELINE |
| `commercial_canon_handover_20260704.zip` | `Demand\Commercial` | — |
| `keys_canon_handover_20260704.zip` | the full `Key\` assumption tree | — |
| `fossil_canon_handover_20260704.zip` | `Resources\` (coal/oil/gas) + `Transformation\` refining/production/blending (168 br) | CSV_AUTHORING_GUIDE |
| `power_canon_handover_20260704.zip` | `Transformation\` Centralized/Distributed generation + grid + storage (1,100 br) | CSV_AUTHORING_GUIDE |
| `industry_canon_handover_20260704.zip` | `Demand\Industry` | — |

8 team groups over 7 export trees — `Resources\` feeds bioenergy + fossil, and
`Transformation\` feeds power + fossil + bioenergy, so two trees are shared.

## Highest-severity items flagged in the audit slices (🔴)

- **Transport:** Road subtree has zero emission leaves (road emissions
  under-reported); Truck-NG *Sales* cites the *Electricity* sales-share key
  (phantom fleet).
- **Resources:** zero-cost open supply/import routes (LP free-lunch); Ammonia
  RAS import cost `0.001` override.
- **Transformation (power):** Capital Cost=0 + OM=0 + `Maximum Capacity
  Addition=Unlimited` on 6 Malaysia `_MY*` generators → free unlimited build
  (160 GW built in RAS).
- **Transformation (fossil):** blending pseudo-techs `Exogenous
  Capacity=Unlimited` → §A.11 1e12 forced floor.
- **Transformation (power) — coverage gap:** the slice was exported from the
  Malaysia + Indonesia contexts only, so the 8 copper-plate countries' base
  generation nodes (Solar PV, Wind, Large/Small Hydro, Gas Combined Cycle,
  Diesel, Coal Subcritical, Biomass Other, Unmet Load) are not yet materialised
  in it — awaiting per-country confirmation / re-export from the power team
  (power README §7.7). Absence from the export ≠ absence in the model.
