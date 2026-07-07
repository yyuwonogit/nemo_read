# Reconciliation instruction — power team update × the v0.68/v0.69 modeller edits (2026-07-06)

**Your update stays intact.** Nothing in it has been found wrong. An
independent modeller update landed in the meantime (areas
`aeo9_v0.68_w_annual_results` and `aeo9_v0.69`), and we have diffed it
exhaustively against the v0.67 canon. The unique authored delta is **small
and exact** — this note lists every cell of it. Fold in exactly these; keep
everything else of yours as-is.

The machine-readable delta is the sibling file
[`v068_unique_edits_52rows.csv`](v068_unique_edits_52rows.csv) (52 rows —
the complete modeller edit set; everything else in v0.69 verified
byte-identical to v0.67, see §4).

---

## 1. MUST ADOPT — Singapore Current Accounts `Existing Capacity` (3 corrections)

The v0.67 area had Singapore's 2023–24 fleet zeroed on these three. v0.68
restores real values. If your update carries Singapore CA Existing Capacity
for these processes, use exactly these expressions (only the 2023/2024
points changed; everything earlier is untouched):

- `Processes\Fuel Oil`:
  `Interp(2005, 4640, 2006, 4405, 2007, 4420, 2008, 4440, 2009, 3950, 2010, 3148, 2011, 3148, 2012, 2555, 2013, 2555, 2014, 2555, 2015, 2555, 2016, 2555, 2017, 2555, 2018, 2554.6, 2019, 1363.6, 2020, 763.6, 2021, 763.6, 2022, 763.6, 2023, 763.6, 2024, 13.60, FirstScenarioYear, 0)`
- `Processes\Gas Turbine`:
  `Interp(2005, 287, 2006, 305, 2007, 315, 2008, 323, 2009, 408, 2010, 370, 2011, 285, 2012, 180, 2013, 180, 2014, 180, 2015, 180, 2016, 180, 2017, 180, 2018, 180, 2019, 180, 2020, 180, 2021, 180, 2022, 180, 2023, 180, 2024, 260, FirstScenarioYear, 0)`
- `Processes\Waste`:
  `Interp(2005, 305.8, 2006, 305.8, 2007, 305.8, 2008, 305.8, 2009, 256.8, 2010, 256.8, 2011, 256.8, 2012, 256.8, 2013, 256.8, 2014, 256.8, 2015, 256.8, 2016, 256.8, 2017, 256.8, 2018, 256.8, 2019, 256.8, 2020, 256.8, 2021, 256.8, 2022, 393, 2023, 393, 2024, 345.20, FirstScenarioYear, 0)`

## 2. MUST ADOPT — Singapore fleet on the un-suffixed BASE branches (12 values)

These live on branches the earlier handovers could not see (§3). Treat the
v0.68 values as canon:

- `Processes\Gas Combined Cycle` — Singapore's main fleet:
  `Interp(2005, 4534, 2006, 4534, 2007, 5024, 2008, 5035, 2009, 5414, 2010, 6154, 2011, 6223, 2012, 7818, 2013, 9430, 2014, 9892, 2015, 10356, 2016, 10356, 2017, 10508, 2018, 10501.3, 2019, 10501.3, 2020, 10501.3, 2021, 10501.3, 2022, 10501.3, 2023, 10516.7, 2024, 10114.71, FirstScenarioYear, 0)`
- `Processes\Solar PV`:
  `Interp(2005, 0, 2006, 0, 2007, 0, 2008, 0.3, 2009, 1.5, 2010, 2.9, 2011, 4.6, 2012, 7.7, 2013, 11.8, 2014, 25.3, 2015, 45.7, 2016, 95.69, 2017, 114.96, 2018, 161.54, 2019, 271.58, 2020, 332, 2021, 486.50, 2022, 633.13, 2023, 918.49, 2024, 1211.18, FirstScenarioYear, 0)`
- `0` on the other ten: Coal Subcritical, Diesel, Nuclear LWR/SMR/SFR,
  Large Hydro, Small Hydro, Wind Onshore, Biomass Other, Unmet Load.

## 3. STRUCTURE — base branches exist; author per-country data on them

The earlier "no un-suffixed base branch for decomposed families" statement
(our 2026-07-05 correction note and the canon anatomy) was **wrong** — an
artifact of region-scoped exports. Confirmed by the v0.68 Singapore rows
(real BranchIDs) and a full v0.69 Brunei slice (all base branches with the
complete 41-variable panel):

- **Every family has its base branch.** The Centralized roster is **124
  process nodes**: base branches + Malaysia's 33 `_MY*` + Indonesia's 51
  `_ID*`.
- **Copper-plate AMS (the 9 besides MY/ID) hold their fleets on the BASE
  branches.** So: Singapore's CCGT belongs on `Processes\Gas Combined
  Cycle`, Brunei's gas turbines on `Processes\Gas Turbine` — never on any
  `_MY*`/`_ID*` node.
- **Your exogenous-capacity edits**: author copper-plate AMS rows on the
  base branch; `_MY*` rows only for Malaysia; `_ID*` only for Indonesia
  (the region-lock rule from the 2026-07-05 note still applies and is
  CI-enforced on our side).
- **Fill the technology data completely**: for these base branches we so
  far hold only `Existing Capacity` (Singapore) — the full panel (Capital
  Cost, OM, Lifetime, Process Efficiency, Maximum Availability, …) needs
  your per-country values wherever your update has them.
- **Do NOT trust values you may see on `_MY*`/`_ID*` nodes for other
  regions** — they are node-creation copy-residue (e.g. `Solar PV_MYPE`
  says Singapore = 0; the real base-branch value is 1,211 MW in 2024).

## 4. Set-up rows → RAS (12 rows, Malaysia/Indonesia technology edits)

The v0.68 file authors these in the `Set up` scenario. **Canon decision
(2026-07-06): they belong in RAS.** Adopt the values; author them in RAS:

| Branch | Variable | Region | Expression |
|---|---|---|---|
| `Gas Turbine` + `Gas Turbine_MYPE` | Maximum Capacity | Malaysia | `Exogenous Capacity[MW]` |
| `Solar PV_MYPE` | Capacity Additions | Malaysia | `Interp(2030,6400,2040,24688.26,2050,52119.66)` |
| `Solar PV_MYSB` | Capacity Additions | Malaysia | `Interp(2030,599.34,2040,2311.74,2050,4880.34)` |
| `Solar PV_MYSR` | Capacity Additions | Malaysia | `0` |
| `Geothermal ORC` | Maximum Capacity | Indonesia | `Exogenous Capacity[MW] + 0.1*3170` |
| `Geothermal Flash_IDJW` | Maximum Capacity | Indonesia | `Exogenous Capacity[MW] + 0.9*1855` |
| `Geothermal Flash_IDSA` | Maximum Capacity | Indonesia | `Exogenous Capacity[MW] + 0.9*1169` |
| `Geothermal Flash_IDKA` | Maximum Capacity | Indonesia | `Exogenous Capacity[MW]` |
| `Geothermal Flash_IDEast` | Maximum Capacity | Indonesia | `Exogenous Capacity[MW] + 0.9*300` |
| `Coal Supercritical\Feedstock Fuels\Biomass` | Feedstock Fuel Share | Indonesia | `Interp(2060, 10)` (10% co-firing by 2060) |
| `Coal Supercritical\Feedstock Fuels\Ammonia` | Feedstock Fuel Share | Indonesia | `Interp(2060, 10)` |

The 10% co-firing share is slated for **universal adoption in RAS** — if
your update already covers co-firing, reconcile to this value unless you
hold newer agreed numbers (then tell us).

> **STATUS UPDATE (2026-07-06, from the v0.69 Indonesia slice): the
> Indonesia-side rows above are ALREADY authored in RAS (and Carbon
> Neutrality) in v0.69** — Set up, RAS, and CNZ all hold the same
> expressions. Two things you must be aware of:
>
> 1. **The 10% placeholder REPLACED the detailed co-firing trajectories
>    that RAS used to hold** — e.g. Ammonia previously ramped
>    `Interp(2046, 0, … 2060, 43.94)` (43.94% by 2060) and Biomass
>    `Interp(2029, 0, … )`; both are now flat `Interp(2060, 10)` in RAS
>    and CNZ, on Coal Supercritical ± CCS AND all four Coal
>    Subcritical_ID* nodes. **The detailed curves survive only in AMS
>    Target Scenario.** If your update assumed the old RAS co-firing
>    levels, re-check anything downstream of them.
> 2. The geothermal caps in RAS also changed vs v0.67: the proven
>    potential is now derated ×0.9 (`+1855` → `+0.9*1855` etc.) and
>    ORC went from `1000000` to `Exogenous Capacity[MW] + 0.1*3170`.
>
> **STATUS UPDATE 2 (2026-07-06, from the v0.69 Malaysia slice): the
> Malaysia-side rows are ALSO already in RAS** — and v0.69 carries FIVE
> more Malaysia RAS edits the v0.68 file didn't list. The complete
> Malaysia+Indonesia RAS delta (25 rows) is in the sibling file
> [`v069_ras_edits_myid_25rows.csv`](v069_ras_edits_myid_25rows.csv).
> The five extras, all Malaysia / RAS / `Maximum Capacity`:
>
> | Branch | old (v0.67) | new (v0.69) |
> |---|---|---|
> | `Gas Turbine` (base) | `1000000` | `Exogenous Capacity[MW]` |
> | `Gas Engine` (base) | `0` | `Exogenous Capacity[MW]` |
> | `Gas Steam` (base) | `0` | `Exogenous Capacity[MW]` |
> | `Gas Turbine_MYPE` | `Unlimited` | `Exogenous Capacity[MW]` |
> | `Large Hydro_MYPE` | `Unlimited` | `Exogenous Capacity[MW]` |
>
> (plus `Solar PV_MYPE/_MYSB` MaxCap: the `+ 1965*1000*80%` headroom was
> moved into a comment — cap is now the exogenous fleet only; and their
> `Capacity Additions` switched from the `Add(2031, …)` annual schedule
> to the `Interp(2030, …)` trajectories of §4's table.)
>
> Two of the anomaly audit's four free-build nodes are thereby CLOSED
> (Gas Turbine_MYPE, Large Hydro_MYPE — the MaxCap ceiling now binds).
> **Solar PV_MYSR and Wind Onshore_MYSR remain fully uncapped at Capital
> Cost = 0** (`Maximum Capacity` + `Maximum Capacity Addition` both
> `Unlimited`) — these two REDs are still open and remain yours to fix.

## 5. What you do NOT need to change

Everything else. Verified against v0.67 canon — **all ten country slices
of `aeo9_v0.69` were harvested and diffed** (2026-07-06):

- Brunei, Cambodia, Laos, Myanmar, Philippines, Singapore, Thailand,
  Vietnam: **zero** authored differences each (≈10k comparable cells per
  country, line-ending-normalised).
- Malaysia: 9 authored RAS edits (§4 status update — all adopted as canon).
- Indonesia: 16 authored RAS edits (§4 status update — all adopted as
  canon).
- So the complete v0.69-vs-v0.67 authored delta = the 52-row v0.68 file
  + the 25-row Malaysia/Indonesia RAS file. Nothing else moved.
- Ignore `Optimized New Capacity` cells reading `? Optimization did not
  run correctly.` in v0.69 — those are LEAP result stamps (RAS optimization
  wasn't run on that copy), regenerated on the next calculatescenario. Not
  authored data, not part of the delta.
- Timor Leste's slice was not exported (not received 2026-07-06); its
  values are unverified against v0.69 but no signal suggests edits there.
