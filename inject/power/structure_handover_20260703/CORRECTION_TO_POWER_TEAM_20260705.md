# Correction & apology — Power team handover (2026-07-05)

This note owns up to mistakes **I (the canon maintainer) made** in the material
handed to you, and gives you the correction to fold into your own canon so we
stay in sync. Two of these were my errors; one is a data-hygiene rule your
`fix_exogenous_capacity.csv` tripped that we should both enforce going forward.

---

## Mistake 1 (mine) — I shipped a dataset with `_MY*` region leaks

I placed **`processes_full_dataset_4scenarios.csv`** into this handover carrying
**13,480 phantom rows**: every Malaysia `_MY*` node (`Solar PV_MYPE`, etc.)
replicated across all 10 non-Malaysia AMS. Those are LEAP inheritance-tree
artifacts, **not real data** — a `_MY*` branch is `Node=0` (unwired from the
grid) everywhere but Malaysia, so a value on `Solar PV_MYPE` in Vietnam is
inert/misleading.

**Fixed:** the dataset is now **home-region-only** (29,670 → 16,190 rows) —
`_MY*` rows only for Malaysia, `_ID*` only for Indonesia, base (un-suffixed)
nodes in all regions as before. Please re-pull it.

## Mistake 2 (mine) — the earlier "Malaysia-only decomposition" framing was wrong

Earlier handover text (and the canon anatomy it came from) said the power tree
was **Malaysia-decomposed only** and that Indonesia's `_IDxx` variants were
"referenced but not materialised." **That was wrong.** The main transformation
export was *region-scoped* to a Malaysia context and simply didn't contain
Indonesia's nodes. Indonesia **is** sub-nationally decomposed — **4 nodes**
(`_IDJW` Jawa-Madura-Bali / `_IDSA` Sumatra / `_IDKA` Kalimantan / `_IDEast`
Eastern), **51 process nodes across 13 families** — merged into canon 2026-07-04.

**Corrected structure (now canon):**
- **Malaysia — 3 nodes** (`_MYPE` / `_MYSB` / `_MYSR`), 33 process nodes.
- **Indonesia — 4 nodes** (`_IDJW` / `_IDSA` / `_IDKA` / `_IDEast`), 51 process nodes.
- **The other 8 ASEAN are single copper-plate nodes** (user-confirmed 2026-07-04).
- Merged Centralized roster = **115 process nodes**.

See the updated `README_POWER_CANON_STRUCTURE.md`, `transformation_slice_tree.txt`
(now includes the Indonesia nodes), and `CANON_ANOMALY_AUDIT_20260704.md` Part D.

---

## The rule to canonize on your side — node-variants are REGION-LOCKED

**A `_MY*` node exists ONLY in Malaysia; a `_ID*` node ONLY in Indonesia.**
Authoring a value for one in any other AMS is a data error. Base (un-suffixed)
nodes are region-general and legitimately appear everywhere.

### Your `fix_exogenous_capacity.csv` tripped this — 330 rows

`inject/power/20260507/from PowerTeam/fix_exogenous_capacity.csv` applied the
Exogenous Capacity formula to **every** region, so all **33 `_MY*` nodes** were
authored across the **10 non-Malaysia AMS** = **330 wrong rows**. (Your `_ID*`
nodes were correct — Indonesia only — nice.)

**I removed those 330 rows** (725 → 395), backed the original up as
`fix_exogenous_capacity.csv.bak_pre_regionlock`, and listed every removed
`node × wrong-AMS` in `REGION_LOCK_REMOVED_NOTES.md` beside it. The cleaned file
has been converted to the canonical inject format (see
`inject/power/20260705/exo_capacity_canonical.csv`).

### How to enforce it on your side (please adopt)

- **Check any CSV before handing it over:**
  `python -c "from nemo_read import find_region_lock_violations as f; print(f('yourfile.csv'))"`
  — returns `(row, node, region, home)` for each violation; empty list = clean.
  Works on both shapes (`ams`/`branch` or `region`/`node`).
- The injector framework now **aborts** on a canonical with any violation
  (`CanonicalInjector._preflight_csv`), and CI (`tests/test_region_lock.py`)
  fails on any `inject/**/*.csv` that leaks. So please **strip `_MY*` rows to
  Malaysia-only and `_ID*` rows to Indonesia-only** in whatever you generate.

Full rule + rationale: **CLAUDE.md §A.21** and canon anatomy §1.1.

---

*Sorry for the mixed signals — the region-scoped export genuinely fooled me on
the Indonesia nodes, and I shouldn't have shipped the un-filtered dataset. The
canon is now correct and enforced; the region-lock check will keep both our
sides honest.*
