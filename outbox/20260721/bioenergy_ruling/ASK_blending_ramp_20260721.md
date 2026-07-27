# NEW ASK — defensible per-country biofuel blend ramp

**Priority: highest.** This is the one deliverable we need from you before the
next RAS run is defensible. It is a data/evidence ask, entirely in your domain.

## The problem, with the evidence

`Diesel Blending` and `Gasoline Blending` are **optimised** transformation
modules in RAS. Each has exactly two competing processes:

```
Transformation\...\Diesel Blending      →  Biodiesel  vs  Diesel     →  Blended Diesel
Transformation\...\Gasoline Blending    →  Ethanol    vs  Gasoline   →  Blended Gasoline
```

Here is what is actually authored on the bio side today (canon, all 3 scenarios):

| Control | Variable | Current value | Effect |
|---|---|---|---|
| Blend **floor** | `Minimum Share of Production` | `Key\Biofuel Blending Targets\<Fuel>:Activity Level[Volume %]/100 * <factor>` | mandate is enforced ✓ |
| Blend **ceiling** | `Maximum_Share_of_Production` | **`100`** | **no upper limit** |
| **Build rate** | `Maximum Capacity Addition` | **`Unlimited`** | **no rate limit** |

**Consequence:** in RAS the optimiser may take a country from its mandate share
to *any* share — up to 100% — **in a single year**, if biofuel prices out
favourably. Nothing in the model prevents 0% one year and 50% the next. There
is no blend wall, no infrastructure lag, no fleet-compatibility limit.

The mandate floors are also thin. Only **Indonesia** carries a genuine
multi-point observed curve:

| Country | Biodiesel mandate today | Implied ramp |
|---|---|---|
| **Indonesia** | `InterpFSY(2023, 35, 2025, 40, 2050, 50)` | ~2–3 pp/yr then plateau — **evidence-based** |
| Malaysia | `InterpFSY(2030, 30)` | single endpoint ⇒ **0→30% in 5 yrs (6 pp/yr)** |
| Thailand | `InterpFSY(2037, 25)` | single endpoint |
| Laos | `InterpFSY(2030, 10)` | single endpoint |
| Philippines | `InterpFSY(2024, 3, 2025, 4, 2026, 5)` | short-horizon only |
| Brunei, Cambodia, Myanmar, Singapore | `0` | no mandate |

Bioethanol is the same shape (Indonesia `InterpFSY(2025, 20, 2050, 50)`;
Malaysia/Myanmar/Brunei/Cambodia/Singapore zero).

Indonesia's B0→B50 trajectory is the empirical anchor we want the rest of the
region benchmarked against — it is the only ASEAN case with a full observed
adoption record from zero to a high blend.

## What we need — three parts

### A. Maximum blend-share trajectory per country (the ramp) — **required**

For **each of the 10 AMS**, for **both** biodiesel-in-diesel and
ethanol-in-gasoline, a year-by-year or milestone trajectory **2025 → 2060** of
the **maximum credible blend share**, in **volume %** (B30, E10 — the
policy-native unit).

For each country, state the binding reason at each stage:

- **Technical blend wall** — the hard one. E10 is a ceiling in most
  non-flex-fuel vehicle stocks; biodiesel is limited by engine/warranty
  compatibility (B7 / B10 / B20 tiers) until the fleet turns over. If a
  country cannot physically exceed E10 before year X, that is the ceiling and
  it matters more than any policy aspiration.
- **Blending & distribution infrastructure** — depots, splash vs in-line
  blending, terminal retrofit lead times.
- **Feedstock availability** — should be consistent with the supply caps in
  your own 89-row payload.
- **Announced policy** — with source.

### B. Re-shape the single-endpoint mandate floors — **required**

Malaysia 0→30% in five years (6 pp/yr) is roughly double Indonesia's observed
sustained rate. Either supply interim milestones that justify it, or re-shape
it. Same for Thailand and Laos. Give us the shape, not just the endpoint.

### C. Annual build-rate limit — **optional but wanted**

Should `Maximum Capacity Addition` on the two bio processes carry a finite
annual limit (blending/refinery capacity added per year) instead of
`Unlimited`? If you can defend a number, send it.

## Format — and what NOT to send

Send a simple table. **Volume %, not energy %:**

```
ams, fuel, year, max_blend_share_volume_pct, binding_reason, source
Indonesia, Biodiesel, 2030, 45, feedstock + announced B50 roadmap, <ref>
Indonesia, Biodiesel, 2040, 50, technical ceiling for compression-ignition fleet, <ref>
Malaysia,  Bioethanol, 2030, 10, E10 blend wall, non-flex-fuel stock, <ref>
```

**Do not convert to energy %, and do not author branch paths or variables.**
The model stores these as an energy share and converts internally using
`* 38.997` (biodiesel) and `* 26.744` (bioethanol). **We** apply that
conversion with the identical idiom already in the model, so your numbers stay
comparable to the mandate floors.

> Two canon notes so nothing is mis-typed on our side or yours:
> the ceiling variable is spelled **`Maximum_Share_of_Production`** — with
> **underscores** — while the floor is `Minimum Share of Production` with
> spaces. And those `38.997` / `26.744` factors are **the same numbers you
> proposed in ask 7a/7b**; the model has been using them all along, which
> independently confirms your unit ruling was right.

## Why this matters

Without a ceiling, a RAS result showing a country at 50% blending in 2031
carries no physical claim — the optimiser reached it because biofuel was cheap
that year, not because the country could do it. With your ramp in place, the
blend path becomes a defensible statement about what each AMS can actually
absorb. This is the difference between a number we can publish and one we
cannot.
