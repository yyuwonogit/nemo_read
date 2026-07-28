# What we need back — structure and shape only

**Date:** 2026-07-22 · **To:** Bioenergy team · **Re:** `bioenergy_blend_ramp_handover_20260722.zip`

This is the complete list. Every item is a **shape or structure** problem — something
that cannot be authored into LEAP as delivered, or that violates a structural invariant.

**Nothing here touches your content, your method, or your evidence.** Your numbers,
your sources, your blend walls, your ramp rates, your realisation treatment and your
per-country judgements are yours. We do not second-guess them and we are not asking you
to defend them. Where two of your files disagree on a *value*, that is yours to settle
in your own time — we have not listed those.

---

## S1 — Part B cannot be authored: there is no resume year *(blocking)*

`mandate_floor_reshape.csv` gives `t0_achieved_2025`, `step_year`, `step_to`,
`plateau_until`, `resume_to` — but **no year for `resume_to`**.

A LEAP `Interp()` is a list of `(year, value)` pairs. Without the resume year the
expression cannot be closed:

```
Interp(2025, t0, step_year, step_to, plateau_until, step_to, ????, resume_to)
                                                             ^^^^ missing
```

**Send:** the resume year for each of the 5 RESHAPE rows. One column.

Also, where your workplan prose and `mandate_floor_reshape.csv` give different shapes
for the same row, tell us **which file is the payload**. We author from one artifact,
not two.

---

## S2 — Part C cannot be authored: the rule references its own output *(blocking)*

```
MaxCapAdd(y) = 0                                          if y < first_feasible_year
             = MAX(one_train_floor, a x installed(y-1))   otherwise
```

`installed(y-1)` is **endogenous** — it is a result the optimiser produces. An input
bound cannot read it; LEAP has no mechanism for a bound that depends on the solution it
is bounding. Authoring this as written is not possible.

We have pre-solved the recursion offline for this cycle, so it is not blocking us now.

**Send next time:** an explicit pre-solved trajectory — one `(year, value)` series per
(ams, fuel) — rather than a rule. If the recursion is the intent, unroll it on your side
where the inputs live.

---

## S3 — A structural invariant your check suite does not test *(please add)*

`Minimum Share of Production` and `Maximum_Share_of_Production` are a lower and an upper
bound on the **same LP variable**, on the same branch. If the floor exceeds the ceiling
in any model year, the model is primal-infeasible.

`blend_ramp_check.csv` contains **no test of this relationship** in any of its 52 rows.
That is not a criticism of the tests you did write — the class is simply absent, which
means the pass count carries no feasibility assurance.

**Add:** a FAIL-class test asserting `ceiling >= floor` at every anchor year, for every
(ams, fuel).

We were not immune to this either: our own Stage-1 detector returned clean on the same
condition, because `MaxShareProduction` was missing from our schema. We added the table
and a `min > max` detector with a regression test on our side this cycle.

---

## S4 — Bound inversion: three `Maximum Capacity` cells below the existing fleet *(FYI)*

A `Maximum Capacity` below its own branch's `Exogenous Capacity` is a bound inversion.
LEAP raises *"Maximum capacity constraint is less than exogenous capacity"* and the
calculation halts.

**Not blocking** — we wrap every refinery cap as `Max(Exogenous Capacity[...], <your
cap>)`, which makes the inversion structurally impossible: the committed fleet is always
permitted, and your cap binds new build only.

Noted so the shape does not recur. The house idiom is **reference first, numeric last**:
`Max(<variable reference>, <number>)`. A numeric *first* argument is parsed by LEAP as a
**year**, which produces `Invalid value parameter ... for year NNNN` at calculation time.

---

## S5 — Send the current master input file

You re-authored 15 rows and shipped a description of the change rather than the file.
We are one revision behind.

**Send:** the refreshed 581-row `bioenergy_leap_input.csv`.

---

## Not asked

For the avoidance of doubt, none of the following is an ask and none of it needs a reply:

- your ceiling-semantics ruling — we think it is right, and we adopted it
- your haircuts, slip assumptions and realisation derivation
- your ramp-rate construction and its exemptions
- your per-country blend walls and the convergence argument behind them
- your evidence weighting, confidence grades and `binding_reason` labels
- your source citations and their basis
- any place two of your files disagree on a *value*

Region names, unit strings, scenario tagging, branch paths, variable spelling and the
volume-to-energy conversion are **ours**, and all were fixed on our side this cycle. Do
not re-issue anything for them.
