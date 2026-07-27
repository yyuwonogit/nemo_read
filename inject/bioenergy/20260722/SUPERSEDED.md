# SUPERSEDED — do not inject anything in this directory

**Superseded:** 2026-07-22 by `inject/bioenergy/20260722b/`
**Status of `bioenergy_delta_20260722.csv` (539 rows): KNOWN-BAD. Do not push.**

## Why

**1. It rewrote refinery `Maximum Capacity` from `Add()` to a level — the fatal one.**
All 70 refinery rows were authored as `Max(Exogenous Capacity, Interp(...))`. Canon
authors that variable as `Add(...)` on all 7 refineries (11 of 12 rows each), and `Add()`
is **cumulative additions on top of `Exogenous Capacity`**, not a total-capacity level.

Indonesia FAME: `Add()` values sum to **65** Million GJ/Yr against **~612** already
standing. Injected as a level, it would have instructed the model to scrap roughly **90%
of the Indonesian biodiesel fleet**.

Caught twice independently — by our own adversarial verifier during the build, and by the
bioenergy team in their 2026-07-22 return (their ask A9, which we had wrongly raised
against them and have now withdrawn).

**2. `10^10` pseudo-caps.** 120 rows (90 `Maximum Production` + 30 `Maximum Imports`)
replaced `Unlimited` with `10^10`. That is not a cap — it is a new sentinel, and ≥10⁹
breaches CPLEX's numerical tolerance (§A.11).

**3. 90 of 110 `Max()` references missing their unit bracket.** Canon precedent is
`Max(Exogenous Capacity[MW], N)`.

**4. `Exogenous Capacity` written into Current Accounts** — 40 rows rewriting the
historical base.

**5. 80 rows of scope creep onto the fossil blending legs** (`Diesel Blending\Diesel`,
`Gasoline Blending\Gasoline`) — outside the biodiesel/bioethanol chain, and the exact
branches of the 2026-05-12 p9 burn.

**6. Asymmetric `Unlimited` sweep.** 60 `Unlimited` cells survived on the fossil legs
while the biofuel leg was capped on all three upper bounds — in a share-dispatched module
that biases the split toward fossil, the opposite of the intent. `BUILD_NOTES` §7 claimed
otherwise.

## What replaces it

`inject/bioenergy/20260722b/` — built against the team's 2026-07-22 return package with
`Add()` semantics preserved, the mandate forced as a floor on all 200 cells, the ceiling
authored only on the 162 cells where it exceeds the floor (so the optimiser stays free
above the mandate), the Möbius volume→energy conversion on both bounds, and the
Philippines FAME `Exogenous Capacity` multiplier restored.

Keep this directory as the audit trail. Nothing in it ships.
