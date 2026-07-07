# Outbox — team canon handover packages (2026-07-04)

## power_cleaning_audit_20260707.zip (2026-07-07)

For the power team, closing the loop on their `power_sendback_20260707.zip`:
`CLEANING_NOTES_20260707.md` (the row-by-row cleaning record for the 9,421-row
inject payload, including the arbitration answer their divergence register
asked for — the LEAP team keeps the IRENA resource-potential caps on Solar
PV_MYPE / _MYSB / Large Hydro_MYPE over the modeller's freeze-at-fleet, plus
the per-variable `MW`/`Megawatt` unit canon), `NOTE_TO_POWER_TEAM_ENDOGENOUS_
20260707.md` (the automatic-plant-additions decision request: coal/diesel
standing permissions with no end year, the 14 broken `Bad Scenario [2]` rows,
keep / time-box / zero menu), and `power_audit_results_observations_20260707.md`
(the audit observations updated with the status-after-inject table — T1 /
slide-18 / SOLAR-MY / storage BLD-RATE solved; Capacity Credit, wind
availability, T2, T6/T7/T8 not — and the 7-item anomaly pass for their eyes).
Source dir: `inject/power/20260707/`.

## power_v069_reconciliation_20260707.zip (2026-07-07)

For the power team, alongside their update-in-preparation: the complete,
country-by-country-verified list of what changed in the LEAP area between
v0.67 and v0.69, with the instruction for keeping their update intact while
taking these changes on board. Contents: `README_READ_FIRST.md` (start
here), the full reconciliation instruction
(`RECONCILE_V069_TO_POWER_TEAM_20260706.md`), and two CSVs holding every
changed value (the modeller's 52-row edit file + the 25 Malaysia/Indonesia
RAS changes found in the v0.69 exports). Also states the two still-broken
plants (`Solar PV_MYSR`, `Wind Onshore_MYSR`: no cap, zero cost) and that
Timor Leste is the one unchecked country. Source dir:
`inject/power/structure_handover_20260706/`.

---

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
- **Transformation (power) — coverage gap: RESOLVED 2026-07-06.** Per-country
  v0.69 exports for all countries except Timor Leste confirmed the plain
  (un-suffixed) generation branches exist everywhere with the full variable
  panel, holding each single-grid country's plant data. The canon tree and
  records now include them; see `power_v069_reconciliation_20260707.zip`.

## power_results_ras_v069_20260707.zip (2026-07-07)

For the power team: full power-sector results of the SOLVED `aeo9_v0.69` RAS
run (their 9,337-row sendback injected + 4 Maximum Capacity corrections that
unblocked the calc). Contents: 5 result CSVs from `feas/NEMO_25 41.sqlite`
(capacity / new builds / generation / unmet-load dispatch / fixed O&M),
`maxcap_fix_delta_4rows.csv` (the corrections to carry forward — also the
TEMPLATE for the new delta-payload convention), the final 9,337-row
canonical as baseline, the LEAP-side xlsx result export, and
`README_POWER_RESULTS_20260707.md` (findings: 5-node unmet load, biomass-
gasification/H2 cost review ask, Max() reference-first authoring rule).
Source dir: `inject/power/20260707/ship_results_20260707/`.

## power_qa_answers_20260707.zip (2026-07-07)

Answers to the power team's 9 advancing questions (`ANSWERS_POWER_TEAM_QA_
20260707.md` + the two cleaning-notes attachments). Load-bearing corrections
inside: result-CSV energy unit is PJ not GWh (Indonesia East 2060 unmet =
2,370 PJ = 658 TWh — first-order node problem, not a footnote); the 400-GW
Biomass Gasification runaway is the HYDROGEN-module branch (P14988), not the
power branch; H2 Fuel Cell inherits 50%-eff/10-yr/falling-capex area
defaults; Stranded Cost never reaches NEMO; must-run in RAS = Minimum
Utilization (12,240 rows, cleanly reversible); VN dead fleets lack nothing —
economics (Nuclear) + dual H2+NG input wiring (GCC-CCS); PH Wind Offshore
ATS confirmed clean; ghost _MYKA branches confirmed (zero data, flagged for
modeller deletion); v2 results package promised with IDs/unit-stamps/module
filter.

## power_results_ras_v069_20260707_r2.zip (2026-07-07, supersedes the non-r2)

Same results package with the unit corrections from the QA round: energy
columns stamped PJ (the original mislabeled unmet as GWh — 278x
understatement), unmet CSV carries an explicit TWh column, fixed-OM stamped
MUSD (verified: 38.3 GW x 51.14 MUSD/GW = 1,957), README finding 2
corrected (658/388/362 TWh outer-Indonesia + Jamali 287.6 GW peak-slack
axis, xlsx tab-swap warning). Send r2; the original stays for the record.
