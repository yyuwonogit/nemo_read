# Reply to the bioenergy blend-ramp handover — 2026-07-22

**From:** AEO-9 LEAP modelling / canon team
**To:** bioenergy team
**Re:** `blend_ceiling_ramp.csv` + Parts B/C handover (received 2026-07-21)
**Package:** this cover · [OUR_RULINGS_20260722.md](OUR_RULINGS_20260722.md) · [CONTENT_ASKS_20260722.md](CONTENT_ASKS_20260722.md)

---

## 0. Headline

**The method is accepted. The payload is not injected as delivered — but almost none of
that is on you.** Everything that stopped it was structural (branch paths, variable
spelling, units, scenario tagging, region names, the volume→energy conversion), and
structure is ours. We fixed all of it on our side and authored the injectable delta
ourselves.

Two of the blockers were **our errors**, and we own them explicitly in §3.

What we still need from you is a short list of genuine content gaps — nine items, in
[CONTENT_ASKS_20260722.md](CONTENT_ASKS_20260722.md). **Do not re-issue any of the
shipped files for structural reasons.** We have already applied those corrections.

---

## 1. What we accepted

**Your ceiling-semantics ruling is the best thinking in the package.** The rule that
*a ceiling may encode only physical and legal limits* — not economics, not programme
maturity, not investment appetite — is correct and we are adopting it as the standing
convention for this variable. It avoids double-counting against the cost stack the
optimiser already sees, it makes the ceiling scenario-invariant (which is exactly why
it can live in RAS alone without distorting the narrative), and it is what killed the
self-negating "no programme, therefore no industry" row. We would have had to invent
this rule if you hadn't.

Also accepted, without amendment:

- **`blend_observed_panel.csv`** — mandate and achieved kept in separate columns,
  per-row sourcing, and inconvenient observations retained rather than smoothed. This is
  a usable evidence base and it is what made our own independent checks possible at all.
- **Retiring your earlier `D = 0.00` model.** You caught it yourselves; it would have
  pinned five AMS at zero blend for 35 years.
- **Demoting `enabling_conditions_scorecard.csv` to informational.** You said you
  demoted it and you actually did — we tested it: the correlation between your
  difficulty score and the ceiling decays from −0.72 (2025) to −0.08 (2050+). Had it
  been a live input it would bind harder over time, not weaker. Accepted as
  informational-only, on the record.
- **The HVO scope note.** Correct, and canon confirms it: `Diesel Blending` carries
  exactly two processes, and `HVO Renewable Diesel` lives in a separate
  `Renewable Diesel Production` module. (One correction: your D3 says a structural
  create is needed — it is not, the branch already exists.)
- **Keeping all 10 year anchors.** We kept them. Dropping the off-milestone years to
  match the current 5-year `YEAR` set changes no solved value and would break under
  any future `YEAR`-set change. Do not trim them next time either.
- **Your per-AMS convergence result.** You state in bold in both the README and the
  workplan that the ceiling converges on a broadly common technical wall. That is a
  stated answer to our Part A ask, not a concealment, and we are treating it as such.

**Your methodology is yours.** Your haircuts, your ramp-rate construction rule, your
realisation derivation, your evidence weighting and your per-AMS convergence argument
are not challenged anywhere in this package, and nothing in
[CONTENT_ASKS_20260722.md](CONTENT_ASKS_20260722.md) asks you to revisit them.

---

## 2. What we ruled (structural — ours, not open for negotiation)

Full detail with evidence in [OUR_RULINGS_20260722.md](OUR_RULINGS_20260722.md). In one
line each:

| # | Ruling | Why it matters to you |
|---|---|---|
| R2 | **`InterpFSY` = RAMP**, linear from (2024, 0) to the first anchor, flat after the last | Your README says step, your own `mandate_floor_reshape.csv` says ramp. The ruling is ramp; it changes which of your "canon below dated instrument" findings stand |
| R3 | **Blend denominator = total distributed pool**, not on-road | You flagged this as an open question and defaulted to on-road. The default is overturned — ~2.6 pp on Indonesia, propagating to all 10 AMS |
| R4 | **Indonesia bioethanol: your E20 wall wins over canon's E50** | We are lowering the canon mandate floor to meet it. See §4 below and the ruling — this one has a consequence you need to know about |
| R5 | **Uniform 2025 start across BAS/ATS/RAS** | We aligned it. No action from you |
| R6 | **Nothing stays `Unlimited`** in the liquid-biofuel chain | Includes one lower-bound subtlety that is *not* simply "capped" — see the ruling |
| R7 | **`Max(reference, numeric)` guard pattern** on every bound that could invert | Reference first, numeric last. Ours to author |
| — | **"Cap RAS, leave ambition in ATS" does not work** | ATS and BAS carry `Optimize = No`. Bounds are inert there. Stated as a structural fact, not a disagreement |

Scope was also narrowed by our operator: **this cycle covers the liquid-biofuel chain
only** — 7 feedstock resources → 7 refinery processes → the Blending module. The five
lite-panel processes (`Charcoal\All Biomass`, `Domestic Biogas\Anaerobic Digestion`,
both Methanol branches, Ammonia) are **out of scope** and were not authored. Nothing in
your handover is rejected on this ground; it simply is not in this delta.

---

## 3. What we fixed ourselves — including our two errors

**Do not re-issue anything for the items in this section.**

### 3.1 Our error #1 — we gave you the wrong conversion instruction

Our ASK told you the volume→energy conversion was `× 38.997 / 100`. **That is wrong,
and it was our instruction, not your mistake.** The correct transform is non-linear —
a Möbius function, because the denominator contains the blend itself:

```
E(v) = v·E_bio / ( v·E_bio + (1−v)·E_fossil ) × 100
   biodiesel   E_bio = 38.997   E_fossil = 43.330
   bioethanol  E_bio = 26.744   E_fossil = 44.800
```

`v` is the volume fraction (0–1); `E(v)` is the energy percent. Worked: B20 → 18.3673,
B50 → **47.3684**, E10 → 6.2203, E20 → **12.9861**. The linear recipe we gave you
over-permits by roughly 1.48× at the top of the range.

**This cost you nothing to fix** — you shipped volume %, which is the right basis to
ship in, and we applied the correct transform on our side across all 200 cells. Keep
shipping volume %.

*(Canon source for the transform: `current_expressions_transformation_slice_4scenarios.csv`
lines 624 and 1980, v0.67 canon — the value may be stale against the live v0.76+ area,
but the functional form is confirmed on canon's own floor expression, so floor and
ceiling share one transform and parity holds.)*

### 3.2 Our error #2 — the authoring guide lied about unit conversion

`inject/bioenergy/CSV_AUTHORING_GUIDE.md` §11.2 and §12.2 stated that unit mismatches
"don't need author action — the audit pipeline applies the conversion factor
automatically." **That is false and it is what caused you to re-author 15 unit rows.**
`grep -rn unit_conversions --include=*.py inject/ nemo_read/inject_base.py` returns zero
hits: the adapter is a pass-through and the injector never reads the `unit` column at
all.

There *is* a conversion path, but it is not the one the guide described — it is opt-in,
requires a fresh live-LEAP units probe, and writes a *separate* file
(`canonical_leap_native.csv`). So the guide was wrong on all three counts: not
automatic, not at inject time, not the same file.

**Corrected in the guide on 2026-07-22**, with the retraction dated and quoted. Going
forward the rule is: **author the unit LEAP actually holds**, because a wrong unit
string fails *silently*.

### 3.3 Structural corrections applied, no resend needed

- **Region names alias-mapped.** `Brunei Darussalam → Brunei`, `Lao PDR → Laos`,
  `Viet Nam → Vietnam`. This touched 7 of your files (60/200 rows in
  `blend_ceiling_ramp.csv` alone). Worth knowing *why* it mattered: wrong region names
  do **not** raise — the injector warns and continues, writing every subsequent row into
  the previously-active region. Silent cross-region corruption. **One vocabulary across
  all emitters, please, on future drops** — but we are not asking you to re-issue this
  one.
- **Branch paths, variable names, units, scenario tags authored by us.** None of your
  nine payload files carried branch / variable / scenario / unit columns — they are
  analysis artifacts, which is fine. We authored the canonical delta.
- **`Maximum_Share_of_Production`** — two underscores, unit `%`. Its floor sibling is
  `Minimum Share of Production` — spaces, unit `Percent`. Normalising between the two
  gives `branch_not_found` or a silent no-op. Ours to get right; noted here only so you
  recognise the names.
- **Ceilings scoped to RAS only, never Current Accounts.**
- **`Rice Straw` / `Used Cooking Oil` branch-create instruction corrected.** Our
  `RULINGS_20260721.md` §6 told you to mirror `Bagasse`. Wrong — `Bagasse` carries
  `Maximum Production` in **Terawatt-hour**, and your values are raw tonnes, so cloning
  it would have landed 3.79e+07 in a TWh field, silently. Corrected erratum issued: the
  template is `Resources\Primary\Palm Oil Mill Effluent` (identical 15-variable panel,
  `Metric Tonne`). **Our error; no action from you.**
- **`p4` unit strings** normalised (`Tonne` → `Metric Tonne`, the free-text `USD/t
  <basis>` tokens resolved). In fairness these are the standing repo convention already
  and we are not presenting them as defects on your side.

---

## 4. The one ruling with a consequence you must see — Indonesia bioethanol

**We accepted your number.** Your evidence — Indonesia at 0.0% achieved ethanol blend in
every observed year 2015–2025, fuel-grade capacity roughly 60× short of national E5 —
beats canon's `E50 by 2050`. Canon values are content, not structure, and on content
your context wins.

**The mechanical consequence we had to implement, and want you to see:** we also apply
`ceiling := Max(canon floor, your ceiling)` as a structural invariant, so a ceiling can
never sit below a floor. Left alone, that wrapper would have dragged your E20 wall back
up to E50 wherever the canon floor exceeded it — **your wall would have been void, and
silently so.**

So we lowered the canon mandate floor for Indonesia bioethanol to meet your wall:

```
Key\Biofuel Blending Targets\Bioethanol, Indonesia
  was:  InterpFSY(2025, 20, 2050, 50)
  now:  InterpFSY(2025,  0, 2050, 20)
```

Start = your observed 0.0%; endpoint = your E20 wall; the canon ramp shape is preserved;
one reversible edit per scenario. **Flagged as the single highest-narrative-impact row in
this delta** — it changes Indonesia's ethanol storyline, and our operator has it marked
for explicit sign-off. One residual we are watching: floor and ceiling now coincide
exactly from 2050, i.e. zero optimiser slack on that share.

---

## 5. What we still need from you

Five items, all **structure or shape** — things that cannot be authored into LEAP as
delivered, or that violate a structural invariant. Full detail in
[CONTENT_ASKS_20260722.md](CONTENT_ASKS_20260722.md).

1. **Part B resume year** — `step_year / step_to / plateau_until / resume_to` has no
   resume *year*, so no `Interp()` can be closed. Plus: which artifact is the payload,
   the workplan prose or `mandate_floor_reshape.csv`? We author from one, not two.
2. **Part C pre-solved trajectory** — `installed(y-1)` is endogenous; an input bound
   cannot read the solution it bounds. We pre-solved it offline for this cycle. Ship an
   explicit `(year, value)` series next time.
3. **A FAIL-class `ceiling >= floor` test** in your check suite. Floor and ceiling are a
   lower and an upper bound on the same LP variable; the suite currently contains no test
   of that relationship. Our own Stage-1 detector was equally blind to it - we shipped
   the tripwire on our side this cycle.
4. **The refreshed 581-row `bioenergy_leap_input.csv`** - you re-authored 15 rows and
   shipped the description rather than the file. We are one revision behind master.
5. **Bound-inversion shape, FYI only** - three `Maximum Capacity` cells sit below their
   own branch's existing fleet. Not blocking: we wrap every refinery cap as
   `Max(Exogenous Capacity[...], <your cap>)`, so the inversion is structurally
   impossible. Noted only so the shape does not recur - the house idiom is **reference
   first, numeric last**, because a numeric first argument is parsed by LEAP as a *year*.

**Not asked:** your haircuts, ramp-rate construction, realisation derivation, blend
walls, convergence argument, confidence grades, `binding_reason` labels, source
citations, and any place two of your files disagree on a *value*. Those are yours. We
have not listed them and they need no reply.

---

*Structure is ours; content is yours. Nothing in this package asks you to re-author for
a structural reason.*
