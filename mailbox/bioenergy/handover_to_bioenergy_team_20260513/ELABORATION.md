# Handover to bioenergy team — 2026-05-13

**From:** LEAP inject team (nemo_read / mailbox/bioenergy maintainers)
**To:** bioenergy CSV authoring team
**Re:** [leap_inject_team_request.md](leap_inject_team_request.md) — your asks A1, A2, A3

---

## What's in this folder

| File | Purpose | Maps to ask |
|---|---|---|
| [BIOENERGY_CSV_SPEC.md](BIOENERGY_CSV_SPEC.md) | Current operational spec (single-cap, dated 2026-04-29) | **A1** |
| [CSV_AUTHORING_GUIDE.md](CSV_AUTHORING_GUIDE.md) | Deep technical reference — column conventions, audit history, unit registry, anti-pattern table, §11.B Bucket B notes, §12 author-action markers | **A1** |
| [build_canonical.py](build_canonical.py) | Bioenergy adapter — contains the `LEAP_MISSING_BRANCHES` filter (lines 62-66) that gates the Bucket B rows | **A2** |
| [HANDOVER_v042_r2a_RAS_infeas_to_dev_team_20260512.md](HANDOVER_v042_r2a_RAS_infeas_to_dev_team_20260512.md) | What changed in LEAP during the v0.42 RAS infeasibility resolution (2026-05-12 / 05-13) — load-bearing for any new bioenergy authoring round | context |
| [fossil_data_push_20260513.zip](fossil_data_push_20260513.zip) | Latest fossil data push — 9 owner-format CSVs + canonical (229 data rows) + unit audit + build/inject scripts (15 files inside) | **A3** |
| [leap_inject_team_request.md](leap_inject_team_request.md) | Your original request, included for cross-reference | — |

---

## Point-by-point response

### A1 — Updated author guide for canonical-CSV creation

**Status: no change since the 2026-04-29 spec.**

The attached `BIOENERGY_CSV_SPEC.md` (dated **2026-04-29**) and
`CSV_AUTHORING_GUIDE.md` (dated **2026-04-29**, supply-basis convention
amended **2026-05-05** in §12.5 / §0) are the current operational truth.

Nothing has shifted on the inject side since the supply-basis amendment
(raw-crop tonnes for the 5 main crops — FFB, cane, fresh root, nuts-in-
shell, grain). Column schema, §8 anti-pattern table, unit-resolution
rules, §12.1 author-action markers, and the post-build audit target
(`27 match · 29 auto · 0 unresolved · 0 no_leap_unit` → ~580 canonical
rows) are unchanged.

**Action on your side:** build against these files as-is. If your last
build also produced 0 unresolved + 0 no_leap_unit, no re-emit needed.

---

### A2 — Bucket B branch status

**Status: still missing on the LEAP side, as far as we know.**

Authoritative source on our side is the `LEAP_MISSING_BRANCHES` constant
in [`mailbox/bioenergy/build_canonical.py:62-66`](../build_canonical.py),
which currently still filters all three:

```python
LEAP_MISSING_BRANCHES = {
    "Resources\\Primary\\Rice Straw",                                            # §11.B.4
    "Resources\\Primary\\Used Cooking Oil",                                      # §11.B.5
    "Transformation\\Bioethanol Production\\Processes\\Cellulosic Rice Straw",   # §11.B.1
}
```

These are still being filtered out at canonical-build time — meaning
the inject team hasn't been notified that LEAP carries the branches
yet. If they have been created since, send us:
- the final branch paths (exact LEAP `\`-delimited form),
- parent / unit / fuel-basis details,

and we'll drop the entries from the set in the same change. The source
CSV rows are already present (per §11.B of `CSV_AUTHORING_GUIDE.md`),
so no source-CSV edit is needed once the filter is lifted.

#### A2-bonus — Cluster 3 placement

**Pending — needs your call.** We currently park `(process)` emission
factors on `\Feedstock Fuels\<crop>` and `CO2 biogenic` on
`Resources\Secondary\Biodiesel` as placeholders, with the expectation
they should move to the parent Process branches. We have not yet
relocated. If you confirm target placement when you handle A2, we
relocate in the same change. Placeholder values (IPCC 2006 + EMEP/EEA
2019 defaults) carry forward unchanged.

---

### A3 — Fossils canonical-migration intent + latest fossil data push

**Status: still in legacy 9-column owner format on our side; migration
decision pending. Latest push packaged as
[fossil_data_push_20260513.zip](fossil_data_push_20260513.zip).**

The zip is a direct snapshot of `mailbox/fossil/` as of 2026-05-13 —
what currently flows into LEAP for the v0.42 cycle. Contents (15 files):

- **9 owner-format source CSVs** — `crude_oil_max_production.csv`,
  `crude_production_cost.csv`, `export_benefit.csv`,
  `refinery_exogenous_capacity.csv`, `import_cost_trajectory.csv`,
  `gas_supply_costs.csv`, `secondary_max_production.csv`,
  `additions_to_reserves.csv`, `coal_supply_costs.csv`.
- **3 scripts** — `build_canonical.py` (adapter, legacy → canonical),
  `inject_to_leap.py` (LEAP COM injector), `run_workflow.py`
  (one-shot driver).
- **3 build outputs** — `canonical_leap_inputs.csv` (**229 data rows**),
  `canonical_leap_native.csv` (parallel canonical in NEMO-native units),
  `unit_audit.csv` (27 rows of per-row unit-conversion audit).

This matches HANDOVER item 4: "Fossil cost input — 229 rows for all
AMS in Resources and Refinery branches".

We have **no recorded decision yet** on whether to migrate fossils to
the canonical 11-column lowercase + single-cap pattern. The default
working assumption is "keep legacy" until someone authorises the
migration, since fossils v2 (V1–V11) work is already in flight on the
owner format and migration would mean rewriting the fossil emitter on
your side and our `build_canonical.py` on this side.

**Action needed from you:** confirm intent — keep legacy, or migrate.
If migrate, propose schema + branch list and we'll align. Use the
files in [fossil/](fossil/) as the reference baseline for that
decision.

---

## Context — what changed in LEAP since your last build (read-me)

The 2026-05-12 / 05-13 cycle resolved a 24k-row primal infeasibility on
`aeo9_v0.42` RAS. Most of the cumulative changes are non-bioenergy
(Unmet Load slack, Optimized Trade plug-in, VRE Min Utilization sweep)
but a few **directly touch bioenergy-authored branches** — call them
out before your next emit:

- **`Biomass` + `Wood` `Maximum Production = 10000`** on 8 AMS that
  previously carried `Unlimited` (the literal string). LEAP→NEMO export
  silently dropped the cap for those AMS, leaving an uncapped supply
  chain. The finite-numeric replacement is what your next emit should
  preserve.
- **`Biomass` + `Wood` `Maximum Imports`** extended across all 11 AMS
  (Base Template wasn't inheriting properly).
- **Bioenergy `Minimum Utilization = 0`** plus cost + structure inputs
  injected across all 11 AMS (FAME, CME, POME, HVO, Sugarcane,
  Cassava, Molasses, Corn Ethanol, SAF) — these are the rows your
  spec already produces; flagging in case your next round overwrites.

Full sequence: see [HANDOVER_v042_r2a_RAS_infeas_to_dev_team_20260512.md](HANDOVER_v042_r2a_RAS_infeas_to_dev_team_20260512.md).

### Authoring landmine — `"Unlimited"` string

A new hard rule for any future bioenergy authoring: **never author the
literal `Unlimited` string on a lower-bound variable** (Exogenous
Capacity, ResidualCapacity equivalents), and **avoid it on upper-bound
variables too** — LEAP→NEMO export converts `Unlimited` to `1.0e+12`,
which either silently un-caps the variable (some AMS) or pollutes LP
conditioning past CPLEX tolerance (~10⁹). Use a finite numeric
(10000–100000) for upper bounds, 0 for lower bounds with no floor.

---

## Summary table — what we need back

| # | Smallest useful answer |
|---|---|
| **A1** | "Looks good, building against attached spec." or specific divergence. |
| **A2** | "Created — paths X/Y/Z (+ parent/unit/fuel-basis)" or "still queued — ETA". Plus Cluster 3 placement decision if handy. |
| **A3** | "Keep legacy" or "Migrate — here's the schema + branch list". |

— LEAP inject team