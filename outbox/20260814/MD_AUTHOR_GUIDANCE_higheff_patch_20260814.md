# High-Eff patch (2026-08-14) — review result + authoring rules for next drops

**From:** LEAP inject team (we hold structure/units canon) · **To:** Residential author team
**Re:** `higheff_patch_canonical.csv` (your 2026-08-14 response, 1,500 rows) · **Target:** aeo9_v0.92, ACT

## Verdict

**Your fix is the right fix, and your numbers are exactly right.** We validated every
one of your 180 new `Unit Capacity` rows against the live area: all 60
country×appliance×size values carry precisely the intended re-anchor factor
(AC ×0.8391 = new/old Useful_EI; Fridge ×0.4931), matching per-country for AC
(FLEH differs by country) and global for fridge. The added Unit Capacity rows are
what was missing from the previous patch — they restore the balance your
device-stock design guarantees: *the installed fleet's deliverable energy equals
what the demand side asks of it in the base year.* With them, the fridge block
returns to an exact match (was 2× off after the previous patch — the cause of the
failed run) and AC returns to the same margin the solved runs had.

**We corrected two UNIT conventions and injected nothing of yours by value** —
your figures are untouched, only their unit expression:

| # | What you sent | What the model stores | Our correction |
|---|---|---|---|
| 1 | `Unit Capacity` = `0.4696378952 * 10^6` (etc., all 180 rows) | **plain kilowatts per device** — e.g. Indonesia AC Large is stored as `0.5597` | stripped the `* 10^6`. As sent, each AC would have been a 469,638 kW machine — a million-fold overshoot. |
| 2 | 30 fridge-Large `Variable OM Cost` rows in **USD/kWh** (e.g. Cambodia `0.15`) | **USD/Gigajoule** since v0.92 (the solver-conditioning change) | multiplied by 277.778 (kWh→GJ), e.g. `0.15 → 41.666667`. As sent, they'd land 278× too cheap — the stored unit label wins; your unit column is not read by the model. |

The corrected, inject-ready file is `higheff_patch_inject_ready_20260814.csv`
(same folder). Nothing else was altered — 1,290 of your rows are byte-identical
to what already injected cleanly, and your 180 Unit Capacity rows differ only by
the stripped scaler.

## Authoring rules to carry forward (these prevent the next round-trip)

1. **The expression is the only thing that lands.** The `unit` column in the CSV
   is documentation; LEAP keeps its stored unit and reads your expression as a
   number in that unit. Always author the number in the unit the area already
   stores. Current storage for the device panel:
   - `Unit Capacity` → **kW per device**, plain number (no scalers, no `10^x`).
   - `Variable OM Cost` → **USD/GJ** (since v0.92).
   - `Exogenous Devices` → device count. `Efficiency` → percent. `Useful_EI` → TOE.
2. **No arithmetic idioms in expressions.** `0.4696 * 10^6`, `x/1000`, etc. —
   author the final number. Expressions do evaluate in LEAP, but scalers hide
   unit mistakes from every automated check (ours caught this one by comparing
   against the live export — don't rely on that).
3. **The pairing law that caused the failed run — treat it as canon:**
   *if you scale `Useful_EI` by factor k, you must scale `Unit Capacity` by the
   same k in the same drop* (per appliance×size; per country for AC). One
   without the other breaks the fleet-vs-demand balance and the run fails.
   Your current drop applies this law correctly.
4. **Scenario names:** `ASEAN Coordinated Transition` (ACT) — correct in your
   drop; `Regional Aspiration Scenario` no longer exists in v0.92+.
   Device-panel variables (`Unit Capacity`, `Exogenous Devices`,
   `Variable OM Cost`) go to ACT only; `Efficiency` and `Useful_EI` go to all
   four (Current Accounts included — base-year values live there).
5. **Interp form** (unchanged rule): comma list-separator, period decimal —
   `Interp(2025, 0.5597, ...)`. Never semicolons.

Questions → us. The structure and units are ours to hold; the values are yours —
and this drop's values were right.

---

## CORRECTION (2026-08-18) — rule 1 above was wrong; your `* 10^6` was right

Our 2026-08-14 review misread the v0.92 export: we checked Unit Capacity against
a truncated preview of the expression and the trailing `* 10^6` sat beyond the
cutoff. A full-length scan confirms what your rev 5 README states: **the ACT
device panel is uniformly on the LEAP-device basis (1 LEAP device = 10^6 actual)**
— `Unit Capacity` `* 10^6`, `Capital Cost` `* 10^6`, `Exogenous Devices`
`/ 10^6`, on all 180 real-country rows of each, with the definition comment on
the Base Template row itself. Stripping your scaler put capacity off-basis
against capital and fleet, producing the ACFRIDGE tier flip you diagnosed.
That inject was ours to answer for, not yours.

Standing corrections to the rules above:
- Rule 1 is REPLACED: for the ACT device panel, author in the **v0.92 stored
  form** — `Unit Capacity` and `Capital Cost` as `value * 10^6`, `Exogenous
  Devices` as `Interp(actual counts…) / 10^6`. The export defines the stored
  convention; scale-free variables (Efficiency %, VOM USD/GJ) need no basis.
- Rule 2 (VOM in USD/GJ) stands, and your rev 5 conforms.
- Your rev 5 delta passed our full validation unchanged — 600/600 rows,
  forms, factors, and per-device dollars verified.
