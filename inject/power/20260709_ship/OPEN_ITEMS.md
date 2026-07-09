# Open items — power sector, v0.71 cycle (2026-07-09)

Tracked on both sides so nothing lives only in email.

## Your action (power team)

1. **Stranded-cost test row — HELD, needs one fix.** The row you sent
   (`stranded_cost_test_row.csv`) writes the value on the **Capital Cost**
   variable. Capital Cost is not optimization-inert and its unit is
   `thousand USD/MW`, so injecting 614,245,472 there would corrupt the
   Indonesia coal node. `Stranded Cost` **is** a real variable on the same
   branch, unit `U.S. Dollar` (your value's unit is already correct). Re-send
   the row on the **Stranded Cost** variable and we inject it — it's inert, so
   it won't move results, just populates the cost report.

2. **Carry the 4 MaxCap wrappers forward in EVERY future payload.** These four
   RAS `Maximum Capacity` cells must stay as `Max(Exogenous Capacity[MW], N)`:
   - Cambodia · Wind Onshore · `Max(Exogenous Capacity[MW], 1500.0)`
   - Philippines · Small Hydro · `Max(Exogenous Capacity[MW], 1874.0)`
   - Vietnam · Wind Onshore · `Max(Exogenous Capacity[MW], 24000.0)`
   - Malaysia · Large Hydro_MYPE · `Max(Exogenous Capacity[MW], 3100.0)`
   A full re-inject that reverts them to a bare number breaks the calc
   ("Maximum capacity constraint is less than exogenous capacity"). Reason: the
   committed fleet exceeds the raw cap; the `Max()` lets the fleet through while
   the cap still binds new builds. Also — author `Max()`/`Min()` **reference
   first, number last**; a numeric first argument is parsed as a year and fails.

3. **Re-author 3 orphan variables per node.** When we cleaned the payload we
   removed base-branch rows for Indonesia `Biogas` / `Gas Engine` / `Gas
   Turbine` / `Geothermal Flash` (Indonesia authors on the `_ID*` nodes, not the
   base branch). Most vars were duplicated on the nodes already, but these three
   existed ONLY on the base rows: `Capacity Retirement`, `Endogenous Capacity`,
   `Maximum Capacity`. If that data is real, re-author it per `_ID*` node.

4. **Negative-Exogenous-Capacity cliff (ATS) — patched, root fix is yours.**
   In ATS, `Exogenous Capacity = Existing + Additions − Retirement` (no floor)
   goes negative for Indonesia `Gas Turbine_ID*` and Malaysia `Coal
   Subcritical_MYPE/MYSR`, `Fuel Oil` — the retirement schedule retires more
   than the fleet holds. We patched Exo with `Max(…, 0)` to unblock ATS/BAS
   calc. To fix at source, cap the retirement so cumulative retirement never
   exceeds Existing + Additions.

5. **WPJ run-2 (dispatch reversal) — tell us when.** Your 18-row must-run
   experiment: run-1 (the `Min(CF, Maximum Availability)` floors) is already in
   the model. `wpj_run2_dispatch_reversal.csv` restores the originals — it's
   the *other arm*, so it must be a **separate run** (injecting it now cancels
   run-1). Signal when you want run-2 and we push it alone.

6. **WP-F gas-supply ceiling → fossil team.** Your gas-ceiling proposal is a
   Resources-tree edit, not a power inject. We've flagged it to the fossil team;
   coordinate the ceiling values with them. Until they apply it, gas supply is
   uncapped in the run (by your own note).

## Our action (inject team)

- Inject **WPJ run-2** when you signal (§5).
- Inject the **corrected stranded-cost row** when received (§1).
- Deliver the **v2 results export** you asked for: NEMO tech-ID + branch-path
  columns, module filter (drops the 1e12 Diesel-Blending sentinels), explicit
  2025 zeros, fixed xlsx tab names, and the Large Hydro_IDKA 2060 zero-
  production anomaly. (This CSV is a first cut — unit-stamped, Total row
  removed.)
