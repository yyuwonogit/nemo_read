# Residential + Transport — 2026-05-21 cycle notes

End-to-end record of two parallel inject cycles run 2026-05-20 to
2026-05-21. Captured for the next session and the cross-sector
playbook.

---

## 1. Residential lighting — clean cycle

**Pattern**: ours handover-out → team data-back → our inject.

1. 2026-05-20: Probed `Demand\Residential\Projections\{Lighting,
   Air Conditioning, Refrigeration}` branches (popup-safe, BT={3,50}
   guard). Wrote `LIGHTING_TEAM_HANDOVER_20260520.md` and
   `REFRIGERATION_TEAM_HANDOVER_20260520.md` — both with branch
   taxonomy, variables, units, current Indonesia 2005 values, and
   open questions for the team.
2. 2026-05-21: Team replied with
   `20260521/inject_handover_lighting_AC_fridge_20260521.zip`
   containing two ready-to-paste lighting CSVs + a structure-build
   request for AC + fridge.
3. Built the residential adapter
   ([build_canonical.py](build_canonical.py)) following the transport
   pattern. Produced 200-row canonical (150 Activity Level scenario-
   tagged + 50 Bulb Wattage untagged).
4. Injected against `aeo9_v0.48` with `--blind --fail-fast -y` (no
   `--skip-dry-run` since v0.48 was first push of this canonical
   shape). Result: 100 rows pushed, **Readback 10 EXACT / 0 NORMALISED
   / 0 FAIL**. Elapsed 4m04s.

**What stayed deferred** (per team direction): `Final Energy
Intensity` (LEAP formula), `BulbsPerHH` / `LightingHours` (LEAP
defaults 7 / 6), the `\Lighting\Other` arm (Kerosene+Candles, Solar
Lighting).

---

## 2. AC + Refrigeration — structure-build request OUTSTANDING

Team's reply for AC + fridge is **a request, not data**: they need us
(or rather LEAP authors) to **create new nested branches** because
their internal model is 2-layer (Size × Efficiency, 9 cells) while
the existing LEAP tree is flat 3-tier (legacy AEO-8 placeholder).

Target structure (build for both `Refrigeration` and `Air Conditioning`):

```
<parent> (BT=1)
├── Small (BT=1)  → Low_eff / Mid_eff / High_eff (BT=4)
├── Medium (BT=1) → Low_eff / Mid_eff / High_eff (BT=4)
└── Large (BT=1)  → Low_eff / Mid_eff / High_eff (BT=4)
```

**Naming polarity gotcha**: inner tier is efficiency, so `High_eff` =
lowest kWh/HH (opposite of size's "High = biggest"). Team recommends
`High_eff / Mid_eff / Low_eff` labels to avoid confusion.

The team answered all 6 open questions from our refrigeration
handover §5 (uncalibrated == calibrated, full 2025–2060 trajectory
per leaf, flat FEI, etc.). Ready to emit per-leaf data CSVs as soon
as the LEAP structure exists.

**This is NOT a `CanonicalInjector` task** — it's manual branch
creation in LEAP UI by a LEAP author. Full details in
[20260521/ac_fridge/structure_request_AC_fridge_2layer_20260521.md](20260521/ac_fridge/structure_request_AC_fridge_2layer_20260521.md).

---

## 3. Transport 20260521 cycle — clean inject

Parallel work on another local; merged via remote.

1. Team sent
   `inject/transport/20250520/transport_author_handover_20260521.zip`
   (note: folder name is `20250520` — typo for `20260520`; preserved
   as-is). Contains 5 CSVs (sales_mix, sales_magnitude,
   starting_year_sales, mileage_anchors, stock_by_fuel cross-check)
   + 2 docs (HANDOFF_README, LEAP_action_items).
2. Headline fixes from the team:
   - **Lane A** — 13 share-discontinuity cells closed at
     orchestrator level (HybridDiesel+NaturalGas+Gasoline+Hydrogen
     folded into HDV classes). The Remainder(100) interim patches we
     shipped 2026-05-20 are retired.
   - **Sales magnitude rewritten** stock-flow-derived. 2W
     2024→2025 ratio went from up to 75× down to 1.00–1.40×. Brunei
     Bus 2006: 50 → 176.8.
   - **Silent-omission gap closed** — explicit zero rows for IDN
     Bus/Truck Gasoline, TH/VN LDV pre-EV-open years, etc.
3. Staged into `inject/transport/20260521/`. Adapter `INPUT_DIR`
   updated. Canonical rebuilt: 562 → 880 rows (+320 new, −2 removed,
   234 changed expressions). Diff report at
   [_diff_vs_20260520_baseline.py](../transport/20260521/_diff_vs_20260520_baseline.py)
   (output preserved in commit notes).
4. Pytest tripwire suite: 140 passed, 2 pre-existing failures (see §5).
5. Injected against `aeo9_v0.48` — `--blind --fail-fast --skip-dry-run -y`.
   First dispatch hit §11.1 spontaneous-blanking trap (`ActiveArea=''`);
   aborted clean. Re-dispatched after user re-focused LEAP — succeeded.
   Result: **400 rows pushed, Readback 10 EXACT / 0 NORMALISED / 0 FAIL**.
   Elapsed 5m10s.

---

## 4. Cross-cycle learnings worth keeping

### 4.1 The handover-cycle pattern is now proven cross-sector

```
US: probe LEAP branches → write per-sector handover .md to team
TEAM: reply with either:
       (a) ready-to-paste data CSVs (lighting did this)
       (b) structure-build request (AC+fridge did this)
       (c) revised data CSVs after our diagnostic findings (transport)
US: adapter → canonical → blind inject → readback EXACT
```

The doc structure (branch taxonomy → variables+units per level →
gotchas → suggested CSV shape → open questions for team) works
across sectors. Don't reinvent per-domain.

### 4.2 Folder-naming convention: dated by request, not response

`inject/transport/20260521/` holds the team's response received
2026-05-21. The team-reply zip lived under `20250520/` first (a
typo). New rule: when staging the team's response, place CSVs
under `inject/<domain>/<RESPONSE_DATE>/<files>/` directly; don't
re-nest under a request-date folder.

### 4.3 Same-name-different-semantics within a single sector

Lighting `Activity Level` has THREE meanings depending on level:
- At fuel-group node (`…\Electricity`): electrification rate %
- At tech leaf (`…\Electricity\<Tech>`): tech share %
- At calibration key (`Key\Cal\Residential\…`): dimensionless factor

Refrigeration `Activity Level` has two more:
- At parent: household ownership rate %
- At leaf: tier share %

The framework's CanonicalInjector doesn't distinguish — the canonical
just has `variable=Activity Level` on different branches. The
adapter's job is to feed the right value to the right branch.
**Handover docs MUST call out the semantic differences** so the team
sends the right shape data to the right level.

### 4.4 Team-modelled structure ≠ LEAP-author structure

Refrigeration: team's 2-layer Size × Efficiency model didn't match
LEAP's flat 3-tier. Outcome: structure-build request back to LEAP
authors (not a `CanonicalInjector` task). When a sector's existing
LEAP structure is a legacy placeholder (AC+fridge were AEO-8-era
remnants), the team may need new branches before any data can be
authored.

### 4.5 §11.1 spontaneous-blanking trap is still real on v0.48

Re-dispatch after user clicks into LEAP works. The area-lock check
catches it cleanly (exit 0 + safety message). Pair `--fail-fast`
with `--blind` as standard so any branch-lookup hang aborts
immediately.

---

## 5. Open items carried to next session

1. **`variable_classifier.py` __all__ gap** — pytest tripwire
   `test_public_api_completeness.py` fails on
   `classify` / `classify_many` / `filter_input_names` not in
   `nemo_read/__init__.py`'s `__all__`. Pre-existing; fix is the
   §A.17 mechanical-enforcement compliance. One line in
   `nemo_read/__init__.py`.
2. **TL opt-out test failure** in
   `test_inject_base.py::TestTimorLesteSupplement::test_subclass_can_opt_out_entirely`.
   Pre-existing; needs investigation (not blocking ops).
3. **BaseYear_StockData semantic mismatch** (carried from 2026-05-19):
   adapter still sums `sales_count` per
   `starting_year_sales.csv:_build_baseyear_stock_rows`. Team's new
   `stock_by_fuel.csv` could feed proper fleet stock instead, but
   we haven't wired it. Brunei Bus authored ~61 vs actual ~2,300.
   Functionally not broken (writes land cleanly per readback EXACT)
   but semantically wrong number on that one branch family.
4. **AC + Refrigeration LEAP-side structure-build** awaiting a LEAP
   author. Team will emit per-leaf data CSVs once branches exist.
5. **Power sector** — last cycle was 2026-05-07 against an earlier
   LEAP version. Not in this cycle's scope but worth a re-inject
   check against v0.48 when convenient.

---

## 6. Operational sequence reminder (per docs/inject_sop.md)

The standard invocation pattern for every sector now:

```
python inject/<sector>/inject_to_leap.py \
    --scenarios "Baseline Simulation,AMS Target Scenario,Regional Aspiration Scenario,Current Accounts" \
    --expect-area "aeo9_v0.48" \
    --include-timor-leste | --exclude-timor-leste \
    --fail-fast \
    [--skip-dry-run]  # ONLY if same canonical shape already verified clean
    -y
```

Blind mode is default-on. The 4-phase flow (dispatch → dry-run →
real-inject → readback) runs in one COM session. Readback verifies
1 row per region; require `N EXACT, 0 NORMALISED, 0 FAIL` per
scenario.
