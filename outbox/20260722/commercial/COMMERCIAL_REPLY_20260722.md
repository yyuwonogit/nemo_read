# Commercial send-back — our reply

**From:** AEO-9 LEAP modelling / canon team · **To:** Commercial buildings team
**Date:** 2026-07-22 · **Re:** `commercial_leap_sendback_20260721.zip`

Good package. It is built against our canon handover, your self-audit is real, and the
per-leaf disposition for all 36 leaves is exactly the shape we want. We are authoring
from it now.

**We do not contest your content.** Your levels, saturations, sources, reconciliation and
per-country judgements are yours. Everything below is **structure and shape** — which
slot a number goes in, and where a deliverable has nowhere to land.

---

## 1. Structural rulings we made (no action needed from you)

**The shares land on `Activity Level`, not `Commercial Fuel Share_`.**
`Commercial Fuel Share_` is inert on all six of your authored leaves — canon annotates it
`0 ? Only used for water heating, cooking, other`, and a full-corpus scan of all eight raw
workbooks (2,493,853 rows) finds **zero** expression-side references to it, against a
validated control (`Commercial Cooking Efficiency_`, 924 references). The live
efficiency-class split sits on leaf `Activity Level`, closed by `Remainder(100)`.

**Consequence for your B10 list:** seven of the nine reported bugs are on that inert
variable. The missing `/100` asymmetry is real and we verified it verbatim — but nothing
reads those cells, so they are not live defects. No action. **Bug 7 is the exception and
it is live** (see §2.4).

**AC borrow: we are re-pointing it, you do not need to.** Your instruction was to leave
the AC leaf `Final Energy Intensity` alone until the residential rebuild lands. It landed
(2026-07-16). The legacy target carries `!EER`, which does not exist in the rebuilt tree,
so we re-point to the parent-level `Useful Energy Intensity` ratio — same ratio shape, no
size assumption. One item from you in §2.5.

**We also fixed on our side, no resend:** region names (`Brunei Darussalam`→`Brunei`,
`Lao PDR`→`Laos`, `Viet Nam`→`Vietnam`), scenario names, the snake_case→branch-name map
(`cooking`→`Cooking and Food Processing` is not title-casable), all `Interp()` assembly,
and the `Remainder(100)` closure. Your files carry no branch/variable/unit/expression
columns by design — expression authoring is ours.

**Refrigeration ratio: we use `0.604`** — your CSV column governs over the prose `0.60`.

---

## 2. What we need from you — six items, all content

### 2.1 The building control belongs in a different slot
Your re-sourced controls (Singapore BCA: Office 218 / Hotel 292 / Retail 405) do not go on
`Key\Commercial\Average Energy Intensity`. That branch is a **composite**:

```
Key\Commercial\Share_ of Buildings\<Type>           weights
Key\Commercial\Energy consumption per area\<Type>   per-type kWh/m2   <-- your values go HERE
Key\Commercial\Average Energy Intensity             = SUM(share x intensity)
Key\Commercial\Gross Floor_Area                     consumes it
```

Send the **per-building-type** values for every AMS you re-sourced. The composite then
recomputes itself. This matters because your B1 is `split% x control / saturation` against
**your** control, which the model does not currently hold — Singapore is 282.89 in your
file versus 214 in the model.

### 2.2 Thailand `Retailer`
Same slot as above: `Key\Commercial\Energy consumption per area\Retailer`, Thailand,
currently `.350`. Confirm **350**.

### 2.3 The 10 Lighting B1 rows have nowhere to land
`Lighting` carries `Commercial Uncalibrated Energy Intensity`, but **no leaf under it
consumes it** — the five Electricity techs hold hardcoded FEI constants,
`Other\Kerosene and Candles` reads a residential cal branch, and `Other\Solar Lighting`
is `0 ? not measured`. Writing those 10 rows changes nothing. Telling you rather than
silently dropping them: is the intent to re-wire the Lighting leaves onto B1, or should
these 10 be withdrawn?

### 2.4 Bug 7 — the value is yours, and it is wider than you flagged
`Water Heating\Solar Heating : Activity Level` carries a uniform `2` that overrides your
sourced Indonesia 30.71 / Thailand 3.39. Confirmed live. It is authored in **Regional
Aspiration Scenario AND Carbon Neutrality_ Net Zero Scenario** — you flagged only RAS;
CNZ carries the identical row. Send the per-region values for both.

### 2.5 AC class → efficiency tier
The rebuilt residential AC tree has **three** efficiency tiers (`Low_eff` / `Mid_eff` /
`High_eff`); your commercial branch has **four** classes. Which tier represents
`Best Practice`, `Efficient`, `Current Sales_Average` and `Current Stock_Average`? Pure
domain judgement, so yours. Default we will use if you have no preference:
Best Practice → `High_eff`, Efficient → `Mid_eff`, the two Current_* → the stock-weighted
parent.

### 2.6 `!Missing Branch (ID=1687/825)` — the repoint target is yours
Both `Resources\Secondary\{Ethanol, Biodiesel}:Commercial Consumer Price` exist but are
`0` in every region and every scenario, so the obvious target yields `Ln(0)` across 240
rows. Sibling branches use three different shapes (same-name price / proxy price / no
price term). Which do you want?

---

## 3. Two smaller structural notes

- **Your disposition roster is 38 leaves, not 36.** Seven rows name Lighting *sub*-leaves
  that carry no `Commercial Fuel Share_`, while the two branches that do
  (`Lighting\Electricity`, `Lighting\Other`) are absent.
- **`floor_area.csv` was not in the package** — your README §8 describes it as driving the
  sector.

---

## 4. One retraction from us

Our earlier review reported an empty-name `Data_Center\` branch as a model defect. It is
an artifact of our own tree-builder, not your model, and not the model's problem.
Withdrawn.

---

## 5. What we are not asking about

Your sourcing, reconciliation method, saturation assumptions, confidence tiers,
split-mismatch provenance, scenario ambition ordering, and per-country judgements. Those
are yours and need no reply.

Questions on structure → us. Questions on values → you.
