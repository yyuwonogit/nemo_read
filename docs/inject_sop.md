# Inject SOP — the standard `CanonicalInjector` method (all sectors)

Established 2026-05-20, generalised from the transport cycle. This is
the standard inject method for **every** `CanonicalInjector` subclass
(bioenergy, fossil, power, transport, and any future sector). The only
thing that varies per sector is **branch structure** — which determines
whether blind mode is mandatory or merely recommended (see the decision
matrix below).

See also: [docs/FLOWS.md §1](FLOWS.md) for the numbered step sequence,
CLAUDE.md §4 (mailbox workflow) and §5.1 (subclass contract).

---

## The function

- Base framework class: `nemo_read.inject_base.CanonicalInjector`, method `.run()`
- Per-sector subclass: `BioenergyInjector`, `FossilInjector`,
  `PowerInjector`, `TransportInjector`, …
- Standard invocation profile: **blind mode** (`--blind --fail-fast`)

## The standard command

```
PYTHONPATH=. python inject/<sector>/inject_to_leap.py \
    --csv inject/<sector>/<canonical>.csv \
    --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario,Current Accounts" \
    --include-timor-leste | --exclude-timor-leste \
    --expect-area "<area name>" \
    --fail-fast --skip-dry-run -y
```

- **Blind mode is DEFAULT ON** (as of 2026-05-20) — no `--blind` flag
  needed. Opt out with `--no-blind` only when you specifically need the
  tree cache (e.g. debugging a `branch_not_found` that blind would hang
  on). `--fail-fast` is still strongly recommended so a bad FullName
  aborts instead of hanging.
- `--scenarios` optional — omit for a single-scenario or current-scenario
  push. One of `--include/--exclude-timor-leste` is mandatory per §A.18.

## Why each flag

| Flag | Why |
|---|---|
| `--blind` (DEFAULT ON) | Skip the tree cache; resolve each branch via direct `leap.Branches(FullName)`. **Mandatory for KA/Demand branches** (cached writes silently no-op there). ~50× faster everywhere (no ~160s cache build). Default-on in the base framework as of 2026-05-20 — every subclass. Opt out with `--no-blind`. |
| `--no-blind` | Opt out of blind — build + use the tree cache. Cleanly reports `branch_not_found` instead of hanging, but cached writes SILENTLY NO-OP on KA/Demand. Only for Resource/Process sectors when debugging. |
| `--fail-fast` | Strongly recommended (blind is default). Direct FullName lookup hangs indefinitely on a non-existent branch (§11.1); fail-fast turns that into an immediate abort instead. |
| `--skip-dry-run` | Skip the ~25-min/scenario dry-run once the canonical's structure is known-good. Keep the dry-run on the first push of a new canonical shape. |
| `--scenarios "A,B,C,D"` | All scenarios in ONE COM session (§A.10). Framework filters each iteration to that scenario's tagged rows. |
| `--include/--exclude-timor-leste` | Mandatory §A.18 decision. |
| `--expect-area` | §A.9 area lock. Overrides the class-level `EXPECT_AREA`. |
| `-y` | Non-interactive; skips the dry-run→real prompt. |

---

## Branch-structure decision matrix — the per-sector adjustment

The general method is identical for all sectors; **only the blind-mode
requirement varies by which branch types the sector writes to.**

| Branch family | Example | Cached writes? | Blind required? |
|---|---|---|---|
| Process | `Transformation\...\Processes\<Tech>` | ✅ work | recommended (faster) |
| Resource | `Resources\Primary\*`, `Resources\Secondary\*` | ✅ work | recommended (faster) |
| **Key Assumptions (KA)** | `Key\TransportDataStock\...` | ❌ **silently no-op** | **MANDATORY** |
| **Demand** | `Demand\Transport\Road\...` | ❌ **silently no-op** | **MANDATORY** |

- **bioenergy / fossil** → Resource + Process branches → cached works,
  but use `--blind --fail-fast` anyway for speed + consistency.
- **power** → Process branches (with subnational group caching) → cached
  works; power keeps its 3-cache `cache_for_region` override for the
  non-blind path, but `--blind` is the faster standard.
- **transport** → KA + Demand branches → **blind is mandatory.** Cached
  writes report `[OK]` but never persist (confirmed 2026-05-20).

**How to tell if a sector needs mandatory blind:** if any canonical row's
`branch` starts with `Key\` or `Demand\`, blind is mandatory. Otherwise
it's the recommended-for-speed default.

---

## Three framework guardrails (all enforced, all sectors)

1. **Scenario-column filter** (`_filter_rows_for_scenario`). Canonicals
   with a per-row `scenario` column ship one row per (branch, ams,
   scenario); the framework filters each scenario iteration to its own
   tagged rows (untagged rows apply to all scenarios — preserves
   bioenergy/fossil/power inheritance semantics). Watch for
   `scenario-column filter: N -> M rows`. Without it, every scenario got
   all rows → last-writer-wins corruption (transport, 2026-05-20).

2. **Decimal-separator regional guard** (`assert_leap_decimal_is_period`).
   Refuses to start (exit 11) if LEAP's regional decimal is comma. Set
   LEAP → Settings → Regional → decimal = '.' (period) before injecting.
   May WARN "could not verify" if no decimal-bearing Interp is in the
   sample — safe to proceed.

3. **Per-scenario readback** (Phase 4). Reads one row per region back and
   compares to the authored expression. Must report `N EXACT, 0
   NORMALISED, 0 FAIL` per scenario.

---

## Verification checklist (CLAUDE.md §4.1 + this SOP)

- [ ] Every scenario: `Readback summary: N EXACT, 0 NORMALISED, 0 FAIL`
- [ ] `scenario-column filter` counts match per-scenario expectations
- [ ] UI eye-test: a multi-scenario branch shows ITS OWN expression per
      scenario (not the same one repeated)
- [ ] **CA-last-year → forward-first-year continuity** for any
      time-series share data — the last historical year must connect
      smoothly to the first projection year. This is an *authoring*
      check (the inject faithfully writes whatever the canonical says).
      Transport ships `_check_ca_to_fwd_continuity.py`; other sectors
      with share data should add an equivalent.
- [ ] Don't save the LEAP area until continuity is clean OR the author
      has confirmed any discontinuities are intended.

---

## Pitfalls catalogue (from the 2026-05-19/20 transport cycle)

| Symptom | Cause | Fix |
|---|---|---|
| Inject `[OK]` but values don't persist in UI | Cached path no-ops KA/Demand writes | `--blind` |
| Readback FAIL with comma decimals (`32,6709`) but values look right | LEAP regional decimal = comma | Flip LEAP regional to period |
| All scenarios show the same expression | Scenario-column filter missing (pre-fix) | Fixed in framework 2026-05-20 |
| Inject dies mid-region after minutes | Cached tree-build slowness + COM bloat | `--blind` (no cache) |
| Share jumps 30% at last-CA-year→first-fwd-year | Author renormalised forward to a narrower fuel set | `Remainder(100)` interim; author re-authors source mix |
| Blind inject hangs | A canonical branch FullName doesn't exist | `--fail-fast` (abort instead of hang); fix the branch path |
