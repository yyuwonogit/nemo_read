# READ THIS FIRST — Power team, v0.69 reconciliation package (2026-07-07)

## What happened, in one paragraph

While you were preparing your update, the modeller made changes directly in
the LEAP area (v0.67 → v0.68 → v0.69). We exported every country's
Transformation data from v0.69 and compared **every value** against our
v0.67 records. The changes are few, and every one of them is listed in this
package. **Your update is not wrong and stays as it is** — you only need to
make sure the values listed here survive into whatever you send next, so
your work and the modeller's edits don't overwrite each other.

## What is in this zip — read in this order

1. **This file.**
2. **`RECONCILE_V069_TO_POWER_TEAM_20260706.md`** — the full instruction.
   Read it end to end before touching your update. Every changed value,
   with the old and new expressions, is in there.
3. **`v068_unique_edits_52rows.csv`** — the modeller's edit file:
   Singapore's plant history (40 rows) + 12 Malaysia/Indonesia rows.
4. **`v069_ras_edits_myid_25rows.csv`** — the changed values we found in
   the v0.69 area itself, all Malaysia/Indonesia, all in the RAS scenario.

## The five things to remember

1. **Your update stays.** Only the values in the two CSVs must be kept on
   top of it. Together they are the *complete* list of what changed
   between v0.67 and v0.69 — we verified this country by country.
2. **Every country was checked.** Brunei, Cambodia, Laos, Myanmar,
   Philippines, Singapore, Thailand, Vietnam: nothing changed. Malaysia:
   9 changed values. Indonesia: 16. Singapore's plant history was
   corrected for 2023–24. **Timor Leste is the only country we could not
   check** (no export was made for it).
3. **Every technology has a plain branch** (no `_MY`/`_ID` suffix), and
   the nine countries besides Malaysia and Indonesia keep their plant
   data there. When you author country data — including your exogenous
   capacity work — put it on the plain branch. `_MY*` rows are for
   Malaysia only, `_ID*` rows for Indonesia only. Values you may see on
   `_MY*`/`_ID*` branches for other countries are meaningless leftovers —
   do not copy them.
4. **Two plants are still broken and are yours to fix:** `Solar PV_MYSR`
   and `Wind Onshore_MYSR` have no capacity cap and zero build cost —
   the model can build unlimited free capacity there.
5. **Ignore cells that say `? Optimization did not run correctly.`** —
   LEAP writes those by itself when results are stale. They are not data
   and are not part of the change list.

If any value here conflicts with newer numbers you hold, tell us —
don't silently overwrite in either direction.
