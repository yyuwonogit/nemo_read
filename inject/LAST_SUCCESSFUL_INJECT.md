# Last successful inject — reference

> **Rolling pointer.** This file names the most recent inject that
> completed cleanly end-to-end. It is the gold-standard reference for
> the inject method until a newer successful inject replaces it.
> **When the next inject succeeds, update this file** (command, log,
> outcome, date) so it always points at the current known-good run.

---

## Current reference: transport, 2026-05-20

**Sector:** transport
**Area:** `aeo9_v0.47`
**Scope:** all 10 ASEAN AMS × 4 scenarios (Baseline / AMS Target /
Regional Aspiration / Current Accounts)
**Outcome:** 562 rows pushed, **40/40 per-scenario readbacks EXACT**
(0 NORMALISED, 0 FAIL), ~4m30s. Scenario-isolation confirmed by UI
eye-test across BAS/ATS/RAS/CA.

### Function used

- Class: `nemo_read.inject_base.CanonicalInjector` (method `.run()`),
  subclassed as `TransportInjector`
  ([inject/transport/inject_to_leap.py](transport/inject_to_leap.py))
- Method profile: **blind mode** (default-on) + `--fail-fast` +
  `--skip-dry-run`, multi-scenario in one COM session, per-scenario
  readback. Full method: [docs/inject_sop.md](../docs/inject_sop.md).

### Exact command

```
PYTHONPATH=. python inject/transport/inject_to_leap.py \
    --csv inject/transport/canonical_leap_inputs_remainder_patched_20260520.csv \
    --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario,Current Accounts" \
    --exclude-timor-leste \
    --expect-area "aeo9_v0.47" \
    --blind --fail-fast --skip-dry-run -y
```

(Note: `--blind` shown explicitly here for the historical record; it is
now DEFAULT ON, so future runs can omit it.)

### Reference log (keep)

[inject/transport/_inject_log_blind_all_ams_remainder_patched_20260520.txt](transport/_inject_log_blind_all_ams_remainder_patched_20260520.txt)

### Canonical injected

[inject/transport/canonical_leap_inputs_remainder_patched_20260520.csv](transport/canonical_leap_inputs_remainder_patched_20260520.csv)
(the 39 sales-share rows with CA→forward discontinuities re-expressed as
`Remainder(100)` — see
[author_handover_20260520/](transport/author_handover_20260520/) for the
data-quality detail handed to the author).

### Outstanding (does NOT block this being the reference)

- Sales-share CA-2024 → forward-2025 discontinuities are an authoring
  defect (interim-fixed with `Remainder(100)`); author to resolve in
  source `sales_mix.csv`.
- LEAP area was NOT saved after this inject pending the author's review.
