# Structural rulings — bioenergy blend ramp, 2026-07-22

These are decisions we made **on your behalf**, because they are questions about LEAP
model structure and modelling convention, not about bioenergy content. They are issued,
not proposed. None of them requires you to re-author anything.

Standing division: **we hold the truth of LEAP structure — branch paths, variables,
units, scenario and region rosters, and model conventions. You hold content — the
values.** Where a ruling below overturns something in your package, it overturns it on
structural grounds only.

---

## R1 — Scope: the liquid-biofuel chain only

This cycle authors the complete liquid-biofuel chain and nothing else:

```
Resources\Primary\{7 feedstocks}
   → 7 refinery processes
        biodiesel : FAME Biodiesel · CME Biodiesel · POME Biodiesel
        ethanol   : Cassava · Corn Ethanol · Molasses · Sugarcane
   → Diesel Blending\Processes\Biodiesel  ·  Gasoline Blending\Processes\Ethanol
```

**Excluded entirely, not authored:** `Charcoal\All Biomass`,
`Domestic Biogas\Anaerobic Digestion`, both Methanol processes, and Ammonia. These are
lite-panel processes outside the liquid-fuel chain. Nothing you shipped is rejected on
this ground — they simply are not in this delta and should not be in the next one
either unless we reopen the scope.

`Cellulosic Rice Straw` is in scope in principle but its branch does not yet exist;
its 10 rows are held pending the manual branch create.

---

## R2 — `InterpFSY` is a RAMP, not a step

**Ruling.** `InterpFSY(y1, v1, y2, v2, …)` ramps **linearly from (2024, 0)** to the
first named anchor, interpolates linearly between anchors, and **holds flat** after the
last anchor. It does *not* hold zero until the first anchor and then step.

**Evidence — an exact-value reconstruction, not a preference.** Inverting the energy
transform on the biofuel `MinShareProduction` rows in the exported NEMO database
reproduces exact round volume percentages **only** under the ramp reading:

| Region | Canon floor expression | Solved value at 2025 | Ramp prediction | Round vol % |
|---|---|---|---|---|
| Malaysia | `InterpFSY(2030, 30)` | 5.00 | 30 × 1/6 | **5.00** ✔ |
| Thailand | `InterpFSY(2037, 25)` | 1.923 | 25 × 1/13 | **1.923** ✔ |
| Philippines | `InterpFSY(2026, 10)` | 5.00 | 10 × 1/2 | **5.00** ✔ |

Under the step reading all three would solve to 0 at 2025. They do not. Corroborating:
our residential canon README and our own earlier ASK to you both state the ramp reading
("`InterpFSY(2030, 30)` ⇒ 6 pp/yr").

**Note, stated without reproach:** your README describes the step reading while your own
`mandate_floor_reshape.csv` is built on the ramp reading. Two files in one zip, two
conventions. The ruling is ramp; where a finding of yours depended on the step reading
(specifically the "canon floor sits below a dated legal instrument" findings), it needs
re-checking against the ramp — but *we* have already re-derived the conflict set on our
side, so this is for your record, not a task.

**Hedge (§A.14).** The database this was inverted from is v0.69-era, not the live
v0.76+. The ramp *shape* is what that export establishes. Whether the anchor year is
literally 2024 or 2025-with-a-2024-historical-point is **not** distinguishable from it.
The distinction does not change any ruling here.

---

## R3 — Blend denominator = the total distributed pool

**Ruling.** The blend share is measured at the **Blending module output** — the
`Diesel Blending` module over `Blended Diesel`, and `Gasoline Blending` over
`Blended Gasoline`. That is the **total distributed pool**, all consuming sectors. It is
**not** on-road demand.

This answers the open question you flagged and defaulted on. Had we stayed silent you
would have shipped on-road, and the difference is roughly **2.6 pp on Indonesia**,
propagating to all 10 AMS.

**Why it is ours:** the denominator is not an empirical quantity to be researched, it is
where the constraint attaches in the model. `Minimum Share of Production` and
`Maximum_Share_of_Production` both live on the Blending *process* branch, and the
denominator is structurally the module's own output. Nothing about your evidence base
changes; only the reference pool your percentages are read against.

**Applies to both sides.** Floor and ceiling share the denominator, so parity holds and
no conflict is created or removed by this ruling alone.

---

## R4 — Indonesia bioethanol: your E20 wall stands over canon's E50

**Ruling.** We **accept your number**. Canon's `E50 by 2050` for Indonesia is content,
not structure, and on content your context expertise governs. Your case is strong:
0.0% achieved ethanol blend in every observed year 2015–2025 in your own panel, against
fuel-grade capacity roughly 60× short of national E5. An E50 endpoint against that
record is not defensible.

### The consequence you need to see

We enforce, structurally, that a ceiling can never sit below a floor:

```
ceiling := Max(Minimum Share of Production, <your ceiling>)
```

Applied naively to Indonesia, that wrapper **drags your E20 wall straight back up to
E50** wherever the canon floor exceeds it. Your wall would have been silently void —
present in the file, inert in the model. The Max() wrapper is not optional (it is what
keeps the bound pair from inverting), so the floor is what had to move.

**What we authored — one row, per scenario, fully reversible:**

```
Branch   : Key\Biofuel Blending Targets\Bioethanol
Region   : Indonesia
Variable : Activity Level   (unit: Volume %)

  was :  InterpFSY(2025, 20, 2050, 50)      ← v0.67 canon, may be stale vs live
  now :  InterpFSY(2025,  0, 2050, 20)
```

- **Start 0** = your observed achieved blend (also satisfies R5 below).
- **Endpoint 20** = your E20 physical wall.
- **Canon's ramp shape preserved** — same anchor years, same single-segment form.
- **One edit per scenario, no other row touched.** Reverting is a one-line change.

**Flagged as the highest-narrative-impact row in the delta.** This changes Indonesia's
ethanol storyline for the whole outlook, so it carries an explicit sign-off gate on our
side rather than riding in with the rest of the payload.

**One residual we are tracking:** floor and ceiling now coincide *exactly* from 2050
onward — lower bound equals upper bound, zero optimiser slack on that share. The
alternative shape (endpoint moved to 2060, leaving a sliver of slack) is on the table if
the pinned form causes trouble at solve. This is our problem to resolve, not yours.

---

## R5 — Uniform 2025 start across BAS / ATS / RAS

**Ruling.** The **starting-year (2025) blend anchor is identical in all three
scenarios**, set to the observed achieved blend. Scenarios may — and should — diverge
after 2025.

**Why.** Today the model is inconsistent: BAS carries 0 everywhere except the
Philippines at 2.5%, while ATS and RAS carry full mandates from the start year. That is
not a scenario difference, it is an artifact — three scenarios cannot legitimately
disagree about what a country *already achieved* in the base year. Scenario divergence
belongs in the trajectory, not the anchor.

**We aligned it ourselves — no action from you.** 27 rows authored, 31 further rows
found to be no-ops and skipped, 2 folded into R4. Post-2025 trajectories are preserved
in every case where one existed; where a series was zero throughout, the 2025 anchor now
holds flat.

**Three anchors we set from your peak-observed values rather than a literal 2025
observation**, disclosed rather than buried: Thailand biodiesel 8.2 (achieved 6.8),
Thailand bioethanol 13.7 (achieved 11.3), Malaysia biodiesel 12.0 (a 2026-dated,
low-confidence estimate). These follow your peak rule, which we accept — but the label on
them should say so, which is content ask #6.

---

## R6 — Nothing in this scope stays `Unlimited` — with one critical exception

**Ruling.** Every bound in the liquid-biofuel chain gets a real finite value: all seven
refineries, all feedstock resources, and the blending build rate. `Unlimited` is not an
acceptable authored value anywhere in this scope.

**Why it is not merely untidy:** LEAP's NEMO export translates the literal string
`Unlimited` to the numeric sentinel `1.0e+12`, regardless of which variable it sits on.
On a genuine upper bound that pollutes the LP conditioning (the solver's numerical
tolerance is around 1e+9, so a 1e+12 coefficient floods the basis with precision noise
even when the constraint never binds). On some regions it exports as missing instead,
silently *removing* the cap.

### The exception — read this one carefully

**`Exogenous Capacity` is a LOWER-bound variable.** It exports to NEMO as
`ResidualCapacity`. `Unlimited → 1.0e+12` there is not a loose ceiling, it is a **forced
floor**: the solver must carry 1e+12 units of that technology in the basis.

The intuitive fix — set it to 0 — is wrong, and we know because we did it. On
2026-05-12 we zeroed `Exogenous Capacity` on the four blending pseudo-techs and primal
infeasibility went **24k → 4.6M, 190× worse**.

**So the rule is three-part and the middle clause is the one that gets missed:**

| Variable class | Examples | Authored as |
|---|---|---|
| Genuine **upper** bounds | `Maximum Capacity`, `Maximum Production`, `Maximum Capacity Addition`, `Maximum Imports` | a real, finite, defensible cap |
| **Lower** bound: `Exogenous Capacity` | the 4 blending pseudo-techs + the 7 refineries | **finite-but-large: 100000** |
| — | — | **never 0. never left `Unlimited`.** |

`Exogenous Capacity` is therefore *not* "capped" in the ordinary sense — it is
de-sentinelled. The number 100000 is chosen to be far above any plausible binding level
while staying inside sane LP conditioning; it is not a capacity estimate and should not
be read as one.

**Status note for our own record:** these `Exogenous Capacity` rows are the same family
as the 2026-05-12 burn, so they carry a separate validation gate on our side before
anything else rides on them.

---

## R7 — The `Max(reference, numeric)` guard pattern — reference first, numeric last

**Ruling.** Wherever a bound could invert against a co-authored bound on the same
branch, author it with a guard wrapper, taken from the optimised power-generation tree.
This is the house idiom:

```
Maximum Capacity             = Max(Exogenous Capacity[<unit>], <numeric>)
Maximum_Share_of_Production  = Max(Minimum Share of Production, <ceiling>)
```

**Reference FIRST, numeric LAST — always.** A numeric first argument to `Max()` or
`Min()` is parsed by LEAP as a **year**, producing `Invalid value parameter … for year
NNNN` at calculation time. This has cost us a full calculation cycle before.

**Canon precedent** (this is an existing idiom, not an invention): 111 rows of
`Minimum Utilization = Min(…, Maximum Availability)`, and
`Maximum Capacity = Max(Large Hydro:Maximum Capacity[MW], Exogenous Capacity[MW])`.

**Effect on your ceiling.** The wrapper is what makes the ceiling structurally safe: it
guarantees `upper ≥ lower` in every region-year cell without us having to hand-raise
individual cells. It also means a ceiling you author below a canon floor does not break
the model — it is quietly overridden in exactly those cells. That is the mechanism
behind the R4 consequence above, and it is why the floor had to move rather than the
ceiling.

**Disclosure, in both directions:** we count the cells where the wrapper is doing work
and surface them in the delta rather than burying them. Pre-delta there were 61 cells
where the ceiling sat strictly below the floor; post-delta 27 remain, concentrated in
Malaysia biodiesel and Thailand biodiesel in the 2026+ interior years. Those 27 are in
the audit file and are not hidden.

---

## R8 — "Cap RAS, leave ambition in ATS" does not work

**Ruling.** This is a structural fact, not a disagreement about strategy.

**ATS and BAS carry `Optimize = No`.** In those scenarios the blend is fully determined
by `Process Share` plus `Remainder(100)` — there is no optimisation, therefore **no
bound of any kind does anything.** A ceiling authored into ATS is inert. There is no
"ambition" there for a ceiling to preserve, because there is nothing free to constrain.

**RAS is the only scenario where the ceiling has any effect** — and, necessarily, the
only one where it can collide with the floor. So the proposal amounts to withholding the
ceiling from the two scenarios where it is harmless and applying it only in the one where
it binds. That is the opposite of its intent.

**What we authored instead:**

- **Ceilings → RAS only.** Not ATS, not BAS (inert), and **never Current Accounts** —
  canon carries no Current Accounts row for this variable and we are not creating one.
- Floor / anchor rows are scenario-tagged individually per R5.
- No row is left untagged. An untagged row applies to *every* scenario, which is almost
  never what is meant.

---

## Standing conventions confirmed (not new, restated so they are on the record)

- **`Maximum_Share_of_Production`** — two underscores, no spaces, unit `%`.
  **`Minimum Share of Production`** — spaces, unit `Percent`. Both live on
  `Transformation\…\Diesel Blending\Processes\Biodiesel` and
  `…\Gasoline Blending\Processes\Ethanol`. Normalising one spelling into the other is a
  `branch_not_found` or a silent no-op.
- **Region roster:** Brunei, Cambodia, Indonesia, Laos, Malaysia, Myanmar, Philippines,
  Singapore, Thailand, Vietnam. **`Base Template` is not a region.** Timor Leste is
  disabled in the calculation and excluded from this cycle.
- **`Interp()` uses comma list-separators and period decimals.** No semicolons, no comma
  decimals, in any file that reaches an inject path.
- **Refinery cap units:** biodiesel side `Million Gigajoules/Year`; ethanol side
  `Million Tonne Coal Equiv/Year`. Build-rate conversions from Mt/yr: ×38.997 and
  ×0.912528 respectively.
- **The mass-basis-LHV-on-a-volume-fraction caveat in the conversion is left as-is,
  deliberately.** Correcting it on the ceiling alone would break floor/ceiling parity and
  could push the ceiling below the floor. If it is ever corrected it is corrected on both
  sides, in one change.
