# Standard inject method (established 2026-05-20)

The blind-mode `CanonicalInjector` flow, validated end-to-end on the
transport sector (10 ASEAN AMS × 4 scenarios, 562 rows, 40/40 EXACT
readbacks, 4m30s). This is now the **standard inject method** for any
sector whose canonical carries a per-row `scenario` column and/or writes
to `Key\` (KA / Key Assumptions) or `Demand\` branches.

## The function

- Framework base class: `nemo_read.inject_base.CanonicalInjector` (method `.run()`)
- Per-sector subclass: e.g. `TransportInjector` in `inject/transport/inject_to_leap.py`
- Winning invocation profile: **blind mode** (`--blind`)

## The command

```
PYTHONPATH=. python inject/<sector>/inject_to_leap.py \
    --csv inject/<sector>/<canonical>.csv \
    --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario,Current Accounts" \
    --exclude-timor-leste \
    --expect-area "<area name>" \
    --blind --fail-fast --skip-dry-run -y
```

## Why each flag

| Flag | Why |
|---|---|
| `--blind` | **Required for KA + Demand branches.** The cached `branch.Variable(...)` path silently no-ops writes on `Key\TransportDataStock\...` and `Demand\Transport\...` branches — the inject reports `[OK]` but nothing persists. Blind mode re-resolves each branch via direct `leap.Branches(FullName)`, which writes correctly. Also ~50× faster (skips the ~160s tree-cache build). |
| `--fail-fast` | Pairs with `--blind` — aborts on first branch-not-found instead of hanging on a bad FullName (§11.1). |
| `--skip-dry-run` | Skips the ~25-min/scenario dry-run once the canonical's structure is known-good. |
| `--scenarios "A,B,C,D"` | All scenarios in ONE COM session (§A.10). The framework filters each iteration to that scenario's tagged rows (see "scenario column" below). |
| `--exclude-timor-leste` | Mandatory §A.18 decision. Transport excludes TL (disabled until further notice). |
| `--expect-area` | §A.9 area lock — aborts if `ActiveArea.Name` doesn't match. Overrides the class-level `EXPECT_AREA` default. |
| `-y` | Non-interactive; skips the dry-run→real confirmation prompt. |

## Three guardrails the framework now enforces (all added 2026-05-20)

1. **Scenario-column filter** ([inject_base.py](../../nemo_read/inject_base.py) `_filter_rows_for_scenario`).
   Canonicals with a per-row `scenario` column ship one row per
   (branch, ams, scenario). The framework filters each scenario
   iteration to its own tagged rows (plus untagged rows, which apply to
   all). Without this, every scenario got ALL scenario-tagged rows →
   last-writer-wins corruption on shared branches. Watch for the log
   line `scenario-column filter: N -> M rows`.

2. **Decimal-separator regional guard** ([_leap_com.py](../../nemo_read/_leap_com.py) `assert_leap_decimal_is_period`).
   Refuses to start (exit 11) if LEAP's regional decimal is comma, not
   period. Comma-decimal storage makes Interp() round-trips ambiguous
   and breaks readback verification. **Set LEAP → Settings → Regional →
   decimal separator = '.' (period) before injecting.** (May emit a WARN
   "could not verify" if the sample finds no decimal-bearing Interp —
   safe to proceed.)

3. **Per-scenario readback** (Phase 4, always on unless `--no-readback`).
   Reads one row per region back via COM and compares to the authored
   expression. Must report `N EXACT, 0 NORMALISED, 0 FAIL` per scenario.

## Verification checklist (don't declare success until all hold)

- [ ] Every scenario: `Readback summary: N EXACT, 0 NORMALISED, 0 FAIL`
- [ ] `scenario-column filter` row counts match per-scenario expectations
- [ ] UI eye-test: open a multi-scenario branch, confirm each scenario
      shows ITS OWN expression (not the same one repeated)
- [ ] **CA-2024 vs forward-2025 continuity** — for time-series share
      data, the last CA historical year must connect smoothly to the
      first projection year. Run `_check_ca_to_fwd_continuity.py`;
      anything > 1% jump is an authoring issue, not an inject issue.
      (See `author_handover_20260520/` for the 2026-05-20 example.)
- [ ] Don't save the LEAP area until the continuity check is clean OR
      the author has confirmed the discontinuities are intended.

## Known pitfalls hit during the 2026-05-19/20 transport cycle

| Symptom | Cause | Fix |
|---|---|---|
| Inject `[OK]` but values don't persist in UI | Cached path no-ops KA/Demand writes | `--blind` |
| Readback FAIL with comma decimals (`32,6709`) but values look right | LEAP regional decimal = comma | Flip LEAP regional to period |
| All scenarios show the same expression | Scenario-column filter missing (pre-fix) | Fixed in framework 2026-05-20 |
| Inject dies mid-region after minutes | Cached tree-build slowness + COM bloat | `--blind` (no cache) |
| Sales share jumps 30% at 2024→2025 | Author renormalised forward to narrower fuel set | `Remainder(100)` interim; author re-authors `sales_mix.csv` |
