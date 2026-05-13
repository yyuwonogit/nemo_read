# Bioenergy → LEAP inject team — open handoff requests

**Last updated: 2026-05-13**
**Status: awaiting reply on A1, A2, A3**

This is a relayable handoff note. It mirrors §A of `Bioenergy/NEXT_STAGE.md`.
Hand it to the LEAP inject team (or their Claude) as-is.

---

## Context

- The Bioenergy source CSV is finished on our side:
  `Bioenergy/LEAP Input/bioenergy_leap_input.csv` — currently
  **554 data rows / 86 (AMS, crop) pairs / 10 domains**, built against
  your `BIOENERGY_CSV_SPEC.md`. All **7** of our source-side audit
  gates pass.
- You pull that CSV and run `run_workflow.py` (the `build_canonical`
  step) to produce the canonical rows and inject into LEAP. Last
  expected target per spec §7: **~580 canonical rows**, audit
  `27 match · 29 auto · 0 unresolved · 0 no_leap_unit`.
- Reminder: **don't open `bioenergy_leap_input.csv` in Excel between
  handoffs** — an Excel-locale re-save corrupted comma-delimited
  `Interp(...)` expressions to period-delimited in a past round. Use a
  text editor or pandas.
- Three items below need your input before the next clean canonical
  build.

---

## A1 — Updated author guide for canonical-CSV creation

**What we need:** your latest `BIOENERGY_CSV_SPEC.md` (or its
successor), specifically any changes to:

- the column schema (canonical 11-column lowercase form),
- the §8 anti-pattern table,
- unit-resolution rules (`no_leap_unit` handling),
- the §12.1 author-action markers,
- the expected post-build audit counts.

**Why:** we build our source CSV against the spec you last handed
over. If it has moved (new required columns, changed unit handling,
tightened audit), we want to align upfront rather than ping-pong on
`unresolved` / `no_leap_unit` rows after your build.

**What changes on our side once we have it:** update our emitter
(`Bioenergy/LEAP Input/build_unified_input.py`), re-run, re-verify the
7 source-side gates, confirm canonical-build target counts still match.

**Smallest useful answer:** updated spec file, or "no change since vX".

---

## A2 — Updated branch-creation details for "Bucket B"

**The three branches** (drafted by us at
`Bioenergy/Paper/bucket_b_create_branches.yaml`, for you to run
through `create_missing_branches.py --dry-run`):

| Draft branch | Type | Role |
|---|---|---|
| `Rice Straw` | Primary Resource | 2G lignocellulosic feedstock |
| `Used Cooking Oil` / `UCO` | Primary Resource | waste feedstock |
| `Cellulosic Rice Straw` | Secondary biofuel process | 2G ethanol/diesel from rice straw |

**What we need:** (a) whether these are / will be created in LEAP, and
(b) the final branch paths plus any structural details (parent, units,
fuel basis) you settled on.

**Why:** our source CSV already carries rows for all three (kept for
forward-compat); our adapter filters them out at build time via a
`LEAP_MISSING_BRANCHES` constant in `build_unified_input.py`. Once the
branches exist in LEAP we just delete those three entries from the
constant — **no source-CSV change**, the rows are already there.

**What changes on our side once they exist:** drop the three entries
from `LEAP_MISSING_BRANCHES`, re-run, rows flow through.

**Smallest useful answer:** "created — paths X/Y/Z" or "will create —
here's the structure".

### A2-bonus — Cluster 3 placement decision (lower urgency, same pass)

We have `(process)` emission factors currently parked on
`\Feedstock Fuels\<crop>` and a `CO2 biogenic` flag on
`Resources\Secondary\Biodiesel`, both as placeholders pending your
call on the correct LEAP placement (we expect they should move to the
parent **Process** branches). If you can confirm the target placement
when you handle A2, we'll relocate them in the same change. Placeholder
values — IPCC 2006 + EMEP/EEA 2019 defaults — carry forward unchanged
either way; no re-sourcing at relocation time.

---

## A3 — Updated Fossils data details

**What we need:**

- (a) Are the Fossils v2 CSVs (V1–V11) still expected in the legacy
  9-column owner format, or do you want them migrated to the canonical
  11-column lowercase schema + single-cap pattern that Bioenergy now
  uses?
- (b) If migration is wanted: the canonical schema spec for Fossils,
  plus the list of LEAP branches / variables in scope.

**Why:** the plan is for Fossils — then Transport / Industry / Power /
Residential / Commercial — to inherit the canonical pattern as their
emitters mature. Fossils v2 (V1–V11) is the next candidate but is
still in the legacy owner format; we won't migrate it speculatively
without knowing your current expectations.

**What changes on our side once we have it:** if migration is
confirmed, we rewrite the Fossils LEAP-input emitter following the
pattern documented in `Bioenergy/DESIGN.md` §12.

**Smallest useful answer:** "keep legacy", or "migrate — here's the
schema + branch list".

---

## Summary — what we need back from you

| # | Ask | Smallest useful answer |
|---|---|---|
| **A1** | Latest canonical-CSV author guide | Updated `BIOENERGY_CSV_SPEC.md`, or "no change since vX" |
| **A2** | Bucket B branch status + final paths | "created — paths X/Y/Z" or "will create — here's the structure" (+ Cluster 3 placement if handy) |
| **A3** | Fossils canonical-migration intent | "keep legacy", or "migrate — here's the schema + branch list" |
