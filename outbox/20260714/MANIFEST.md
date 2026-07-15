# Outbox — 2026-07-14 (power batch-1b review-and-confirm)

Review bundle for the Power team on their batch-1b send-back (v0.71
correction cycle). We validated the 262-row delta against canon and against
our 2026-07-13 engine-edit capture: it is **injectable as-is**. This drop is
a review/sign-off gate before we push — nothing here asks Power to re-author
the delta.

| Zip | For | Contents |
|---|---|---|
| `power_batch1b_review_20260714.zip` | Power | (1) `power_batch1b_delta_20260713.csv` — their validated 262-row delta, unchanged; (2) `stranded_cost_test_row_REALIGNED_20260714.csv` — their 1-row probe, column-realigned by us (was 10 fields vs 11-header → scenario parsed empty → would inject into all scenarios; now RAS-only); (3) `REVIEW_AND_ACTIONS_20260714.md` — per-file instructions + 6 action items. |

Two things Power must act on before push: confirm the stranded realignment
(or re-emit 11-column), and acknowledge the two "structural-create"
corrections (base `Nuclear SMR` + base `Unmet Load` already exist —
region-invariant structure; no branch creation). VOLL 20,000 USD/MWh on
Unmet Load `Variable OM Cost` is user-approved and ships with the inject.

Repo-side in the same change: the 262-row delta + the realigned stranded
probe staged into `inject/power/20260713/` (all preflight gates clean),
ready for an area-confirmed inject against `aeo9 v0.71`, exclude-Timor-Leste.
See `inject/power/20260713/INJECT_READY_batch1b_20260714.md`.
