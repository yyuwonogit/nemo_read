# Handoff — bioenergy land-modeling refactor

**Purpose:** carry conversation state across devices. Future Claude on the other device: read this first, then optionally `mailbox/bioenergy/bioenergy_leap_input.csv` and `nemo_read/unit_conversions.py` for current state.

**Date of handoff:** 2026-04-29.

**Branch:** `main`. Branch state pre-handoff committed in this same commit (mailbox reorg + nemo_read updates + this doc).

---

## Where the conversation left off

Mid-design for the **bioenergy cultivation tier refactor** in the LEAP→NEMO workflow. Two outside agents are participating:

- **Me (this Claude):** design / structural reasoning, memory keeper.
- **Probe agent:** has reverse-engineered LEAP's variable / unit structure. Their LEAP-structure intel is authoritative; their design opinions are not.

Latest exchange identified one real conflict between probe and our design (Aux vs Feedstock for land binding) and produced a unified to-do list. **Three blocking decisions remain (A1, A2, A3 below) before any CSV editing starts.**

---

## Locked design decisions

(Mirrors `~/.claude/projects/c--Users-ThinkPad-Desktop-Py-YY-NEMO-read/memory/bioenergy_land_modeling.md` from this device — duplicated here for cross-device readability since auto-memory is per-machine.)

### Two-tier bioenergy structure
- **Tier 1 — Processing:** `Biodiesel Production\Processes\FAME Biodiesel`, etc. Input: Palm Oil. Output: Biodiesel.
- **Tier 2 — Cultivation:** `…\Palm Oil Cultivation` (and Coconut, Sugarcane, Cassava, Corn equivalents). Input: Perennial / Arable. Output: the feedstock crop.
- Chain: `Perennial → [Cultivation] → Palm Oil → [Biodiesel] → Biodiesel`.

### Cultivation output = the feedstock fuel
Palm Oil Cultivation outputs **Palm Oil** (same commodity Biodiesel consumes — closes the chain). Same logic per crop.

### The unit-yield trick (1 GJ/ha anchor)
LEAP's Cultivation Process has all variables in energy units (TOE / GJ / Percent). To represent shared land budgets without bias:

- `Resources\Primary\Perennial` and `Resources\Primary\Arable` carry unit `Thousand GJ`, with the numeric value equal to thousand ha (notional 1 GJ/ha anchor).
- Each cultivation process's land-binding ratio is `GJ-land per GJ-output`, numerically equal to real ha/GJ for that crop (`1 / yield_crop_GJ_per_ha`).
- LP constraint reduces to `Σ ha_used ≤ ha_available` because the notional yield cancels — no inter-crop bias.
- Anchor is *not* a real crop's yield — yield-improvement scenarios touch only the affected crop's ratio.

### Double-cap (intentional, with guardrail)
Each cultivation chain is bounded by **two independent caps from independent empirical sources**:

1. **Land cap** — `Resources\Primary\Perennial` / `Arable` Maximum Production (shared, FAOSTAT permanent-cropland / arable area).
2. **Yield cap** — `Resources\Primary\<Crop Oil>` Maximum Production (independent forecast — MPOB / FAOSTAT trend / national plan; **never** derived from `land × yield`).

Cultivation process itself carries **no Maximum Production / Maximum Capacity**. Whichever cap binds first is diagnostic (land-limited vs yield-limited).

### Land-binding variable on Cultivation — UNRESOLVED
- **My pick:** Aux Fuel — variable `Auxiliary Fuel Use` (TOE/TOE, dimensionless). Native fit for `1/yield_crop`.
- **Probe pick:** Feedstock Fuel — variable `Feedstock Fuel Share` with `1/yield_crop` as expression value.
- **Risk on Feedstock:** `Feedstock Fuel Share` is conventionally a 0–1 fraction summing to 1.0 across feedstocks; LEAP may interpret 0.00769 as "0.769% share" and silently underbalance.
- **Risk on Aux:** Cultivation may need a Feedstock Fuel for LEAP's energy-balance accounting; using Aux only might leave the process without a declared energy input.
- **User has not yet ruled.**

### Result-reading (nemo_read side)
NEMO's Perennial / Arable demand is numerically already in ha — only the unit label needs swapping. Implementation: `LAND_PROXY_FUELS = {"Perennial", "Arable"}` registry that:
- audit pipeline treats as terminal (no GJ↔ha conversion ever proposed);
- result reader uses to relabel column from "GJ" to "thousand ha" in output frames.

### Cleanup implied
Existing `Perennial`-as-Aux-Fuel rows directly on FAME-palm and CME-coconut Biodiesel (currently in `mailbox/bioenergy/bioenergy_leap_input.csv` around lines 251–260) come **out** when the Cultivation tier is live — otherwise land is consumed twice.

### Documentation discipline
- Every Perennial / Arable row's `note` column carries: *"unit is GJ-equivalent at notional 1 GJ/ha; numerically equal to thousand ha"*.
- Every yield-cap row's `note` column carries the **independent source** provenance (e.g., *"MPOB 2024 outlook trend extrapolation; not derived from land budget"*) — this is what makes the double-cap auditable.

### Probe-confirmed LEAP-side facts
- **Cultivation Process is a leaner LEAP subtype:** 30 variables vs. 44 on Biofuel processes. All in energy units (TOE / GJ / Percent).
- **Cultivation does NOT expose `Maximum Capacity`** — only `Maximum Production` (Gigajoule). Canonical's 50 `Maximum Capacity` Cultivation rows must be **deleted** (per our design — cap relocates to Resources, doesn't stay on Cultivation).
- **`Co-product Credit (audit)`** is not a LEAP variable. Its 20 canonical rows must be removed from LEAP-injection canonical (sidecar source CSV is fine if traceability is wanted).
- **Aux Fuel variable:** `Auxiliary Fuel Use`, unit `TOE/TOE` — dimensionless energy ratio.
- **Feedstock Fuel variables:** `Feedstock Fuel Share` (Percent / 0–1 fraction) and `Fuel Cost` (USD/GJ).
- **Output Fuel variables:** `Output Share` (% Share), `Output Price` (USD/kWh — odd default; not relevant since cultivation output is consumed by another LEAP process).

### Wiring summary (palm example)
```
Resources\Primary\Perennial (cap: kha-as-kGJ, shared)
   └─→ consumed by: Palm Oil Cultivation as <Aux OR Feedstock — A1 unresolved>
                    (TOE/TOE = 1/yield_palm_GJ_per_ha; e.g. 1/130 ≈ 0.00769)
                      └─→ output: Palm Oil
                                    └─ Resources\Primary\Palm Oil Maximum Production (yield-projection cap)
                                    └─→ consumed by: FAME / CME Biodiesel
                                                       └─→ output: Biodiesel
```

---

## Open blocking questions

| ID | Question | What's needed |
|---|---|---|
| **A1** | Aux Fuel vs Feedstock Fuel for land binding on Cultivation? | User design call. My read: Aux. Probe's: Feedstock. Both have risks listed above. |
| **A2** | Yield-cap values for the 50 new `Resources\Primary\<Crop Oil>` MaxProd rows | User to provide independent-forecast values OR confirm existing canonical Million-Tonnes/yr values aren't derived from `land × yield` so they can be relocated. |
| **A3** | Confirm delete of 20 Co-product Credit (audit) rows from canonical | Cheap confirm; sidecar source CSV is fine if audit traceability needed. |

---

## Pending actions (ordered, dependency-aware)

### B — `nemo_read` package (no LEAP dependencies, can start anytime)

| # | Item | File |
|---|---|---|
| B1 | Add `LAND_PROXY_FUELS = {"Perennial", "Arable"}` constant; audit must never propose GJ↔ha conversion for these (terminal, full-confidence) | `nemo_read/unit_conversions.py` |
| B2 | Audit-pipeline guard: skip conversion proposals when fuel ∈ LAND_PROXY_FUELS | `nemo_read/leap_area.py` (`audit_canonical_units`) |
| B3 | Add `USD/t [crop] → USD/TOE` registry entries for cultivation Variable OM Cost: palm FFB, cane, cassava fresh root, corn grain, coconut nuts-in-shell. Factor = `LHV_GJ_per_t / 41.868` | `nemo_read/unit_conversions.py` |
| B4 | Result-reader relabel: Perennial / Arable column from `GJ` → `thousand ha` on output frames | `nemo_read/leap_units.py` (or wherever results are read) |

### C — Canonical CSV (depends on A)

| # | Item | Rows |
|---|---|---|
| C1 | Delete `Co-product Credit (audit)` rows | 20 |
| C2 | Delete `Maximum Capacity` rows on the 5 Cultivation processes | 50 |
| C3 | Add `Resources\Primary\<Crop Oil>` Maximum Production rows × 10 AMS × 5 crops | 50 (new) |
| C4 | Update Land MaxProd rows: unit `Thousand ha` → `Thousand GJ`; append note text | 20 |
| C5 | Update 5 land-binding rows on Cultivation per A1 outcome (variable name + expression `1 / Resources\Primary\<Crop>:Crop Yield` + unit) | 5 |
| C6 | Add note-column independent-source provenance text to every yield-cap row | 50 |
| C7 | Remove existing `Perennial`-as-Aux-Fuel rows on FAME-palm / CME-coconut Biodiesel | check via grep on `bioenergy_leap_input.csv` |

### D — Build adapter + documentation

| # | Item |
|---|---|
| D1 | `mailbox/build_canonical.py` (or successor in `mailbox/bioenergy/`) — confirm pass-through of new schema |
| D2 | Update guide §11 — two-tier structure, GJ-equivalent trick, double-cap rationale, note discipline |

---

## File pointers

- **Canonical bioenergy CSV (input to LEAP):** `mailbox/bioenergy/bioenergy_leap_input.csv` (currently 366 KB; existing Perennial-as-Aux on FAME/CME around lines 251–260; existing Perennial cap rows around lines 251–260 with unit `Thousand ha`).
- **nemo_read unit conversions:** `nemo_read/unit_conversions.py` — registry of `(from_unit, to_unit, fuel) → ConversionProposal`. Has FFB / cane / cassava root LHV entries already.
- **nemo_read audit pipeline:** `nemo_read/leap_area.py` (`audit_canonical_units` + `apply_audit_conversions`).
- **Recent commits show the audit pipeline lineage:** `0d6f804` (0.6.4 defensive defaults), `157e739` (0.6.3 LEAP-side unit audit).

## Cross-device note
This handoff doc is in the repo so it travels via git. The local auto-memory at `~/.claude/projects/c--Users-ThinkPad-Desktop-Py-YY-NEMO-read/memory/bioenergy_land_modeling.md` is **per-machine** and won't be on the other device — its content is duplicated above for that reason. On the other device, future Claude can rebuild auto-memory from this doc if useful.
