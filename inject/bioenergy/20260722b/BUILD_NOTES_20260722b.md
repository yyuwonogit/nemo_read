# BUILD NOTES — bioenergy delta 20260722b

**Built:** 2026-07-22 · **Builder:** [build_bio_delta_20260722b.py](build_bio_delta_20260722b.py)
**Output:** [bioenergy_delta_20260722b.csv](bioenergy_delta_20260722b.csv) — **112 rows**
**Supersedes:** `inject/bioenergy/20260722/bioenergy_delta_20260722.csv` (539 rows, KNOWN-BAD)
**Status:** FILES ONLY. No LEAP COM was touched. Nothing is injected.

Input: the bioenergy team's 2026-07-22 RETURN package (13 files), read-only.
Structure reference: canon `LEAP structure/LEAP Input Transformation.xlsx`
(area `aeo9_v0.67_w_results`).

> **§A.14 staleness label.** Canon is v0.67; the live area is v0.76+. Every canon
> **VALUE** quoted below (`Add()` arguments, `Exogenous Capacity` series, the
> `Unlimited` on `Maximum Capacity Addition`) is **stale-able** — it is what v0.67
> held, not a verified read of the live area. Canon **STRUCTURE** (branch paths,
> variable names, units, scenario roster) is authoritative and is what this delta
> is built against.

---

## 0. Row count by group

| Group | What | Rows |
|---|---|---:|
| G1 | Blend **FLOOR** — `Minimum Share of Production` | **20** |
| G2 | Blend **CEILING** — `Maximum_Share_of_Production` | **19** |
| G3 | Refinery `Maximum Capacity` | **0** (refused, B1) |
| G4 | Refinery build rate — `Maximum Capacity Addition` | **70** |
| G5 | Philippines FAME `Exogenous Capacity` fix | **3** |
| G6 | Anything else canon-backed and in scope | **0** |
| | **TOTAL** | **112** |

Scenario split: `Regional Aspiration Scenario` 110 · `AMS Target Scenario` 1 ·
`Baseline Simulation` 1. No `Current Accounts`. No CNZ.

Column set is the canonical one read off
[inject/bioenergy/canonical_leap_inputs.csv](../canonical_leap_inputs.csv)
(`ams,branch,variable,expression,unit,fuel,source,note,src_csv,domain,data_confidence`)
**plus a `scenario` column** — that file has none, and the `CanonicalInjector`
filters per-scenario on it (§A.20 #2). Untagged rows would otherwise be written
into every scenario iteration.

Branch paths were taken byte-exact from canon column E. The two blending targets:

```
Transformation\Diesel Blending\Processes\Biodiesel
Transformation\Gasoline Blending\Processes\Ethanol
```

Units taken from canon, not from the team's labels: `Minimum Share of Production`
= **`Percent`**, `Maximum_Share_of_Production` = **`%`** (canon really does use two
different unit strings for the two variables), `Maximum Capacity Addition` =
`Million Gigajoules/Year` (3 biodiesel processes) / `Million Tonne Coal Equiv/Year`
(4 ethanol processes), `Exogenous Capacity` = `Million Gigajoules/Year`.

---

## 1. Group 1 — blend FLOOR, all 200 cells → 20 Interp series

Source: `blend_floor_mandated.csv`, column `min_blend_share_volume_pct`, joined on
the team's **`region`** column (B7 — never `ams`, which holds their descriptive
names). All 200 cells authored, per B3: the mandate is a forced minimum and every
cell carries one, including the zeros.

Ten anchors per series: 2025, 2026, 2027, 2030, 2035, 2040, 2045, 2050, 2055, 2060.
20 series = 10 regions × {Biodiesel, Bioethanol}.

### The Möbius conversion (B8) — worked example

Their values are **volume %**. LEAP's share variables are **energy %**. The
transform is **non-linear**:

```
E(v) = v·E_bio / ( v·E_bio + (1 − v)·E_fossil ) × 100        v = vol% / 100

  biodiesel   E_bio = 38.997   E_fossil = 43.330
  bioethanol  E_bio = 26.744   E_fossil = 44.8
```

Constants are not invented — they are lifted verbatim from canon's own expression
on this exact variable (`Transformation\Diesel Blending\Processes\Biodiesel`,
`Minimum Share of Production`, RAS):

```
Key\Biofuel Blending Targets\Biodiesel:Activity Level[Volume %]/100 * 38.997
  / (Key\Biofuel Blending Targets\Biodiesel:Activity Level[Volume %]/100 * 38.997
     + (1 - Key\Biofuel Blending Targets\Biodiesel:Activity Level[Volume %]/100) * 43.330)
  * 100 ? Energy contents taken from Fuels database
```

**Worked example — Malaysia, Biodiesel, 2030. Their floor is B30 (30.0 volume %).**

```
v      = 30.0 / 100                    = 0.30
num    = 0.30 × 38.997                 = 11.6991
den    = 11.6991 + 0.70 × 43.330       = 11.6991 + 30.3310  = 42.0301
E      = 11.6991 / 42.0301 × 100       = 27.835052 energy %
```

So **B30 by volume = 27.835 % by energy**. Biodiesel is energy-*poorer* per litre
than diesel (38.997 < 43.330 GJ), so its energy share always sits **below** its
volume share. The authored row is:

```
Malaysia | Transformation\Diesel Blending\Processes\Biodiesel | Minimum Share of Production | Percent
Interp(2025, 4.522613, 2026, 13.705584, 2027, 13.705584, 2030, 27.835052, 2035, 27.835052,
       2040, 27.835052, 2045, 27.835052, 2050, 27.835052, 2055, 27.835052, 2060, 27.835052)
```

**A linear ×38.997 would have given 30 × 38.997/43.330 = 27.0 %** — close here, but
the error is not constant: it grows with v and at the ceiling values it over-permits
by roughly the 1.48× flagged in B8. Both bounds go through the **same** transform so
the floor ≤ ceiling parity that holds in volume space holds in energy space too.

Full per-cell conversion trail: [_audit_floor_mobius.csv](_audit_floor_mobius.csv)
(200 rows: region, fuel, year, volume_pct, energy_pct).

### What this replaces

Canon currently carries the live **reference** expression shown above — the share
tracks `Key\Biofuel Blending Targets\…:Activity Level` dynamically. This delta
**pins it to the team's explicit anchors**, which is what makes the floor a forced
legal minimum rather than a follower of the Key branch. That is a deliberate
consequence of B3, not an accident: after this inject, editing the Key branch no
longer moves the blending floor. Flagged for the operator.

---

## 2. Group 2 — blend CEILING, 162 of 200 cells → 19 series

Source: `blend_ceiling_ramp.csv`, column `max_blend_share_volume_pct`. Same Möbius
transform, same anchors, same join key.

Independently recomputed on the shipped CSVs before authoring:

```
ceiling >  floor : 162      -> authored
ceiling == floor :  38      -> NOT authored (B3)
ceiling <  floor :   0      -> build aborts if this is ever non-zero
```

Authored form, guard reference-first per §11.2e (a numeric first argument parses as
a **year** — the 2026-07-07 Philippines Small Hydro burn):

```
Max(Minimum Share of Production, Interp(...))
```

### The 38 pinned cells are deliberately left unauthored

Where ceiling == floor, authoring `Max(floor, ceiling)` would **create** the pin and
bolt the optimiser to the mandate. Canon's default of `100` is left standing instead,
so above the mandate the optimiser stays free. This is the whole point of B3.

19 series, not 20: **Indonesia / Biodiesel has all 10 anchors pinned** (2025 at
40.0, 2026–2060 all at 50.0) so **nothing at all is authored for that series** —
its `Maximum_Share_of_Production` keeps canon's `100`.

### Partially-pinned series — how the omitted anchors behave

Where a series has *some* pinned years, the `Interp()` is authored over **only the
unpinned anchors**, so the pinned years are absent from the interpolation. LEAP then
interpolates straight across the gap, which can put the raw `Interp` **below** the
floor in those years — and that is exactly what the `Max(Minimum Share of Production, …)`
guard absorbs: those years resolve back to the floor, never below it, and never
pinned from above. Example, Philippines / Biodiesel — 2025 is pinned (4.0 == 4.0) and
omitted; the series starts at 2026:

```
Max(Minimum Share of Production, Interp(2026, 6.344411, 2027, 9.090909, 2030, 17.431193,
    2035, 31.677019, 2040, 46.37224, 2045, 47.368421, 2050, 47.368421, 2055, 47.368421,
    2060, 47.368421))
```

### Exactly which cells were skipped, and why

All 38 are `ceiling == floor` → "canon default 100 left standing (B3: do not create
the pin)". Per-cell list in
[_audit_ceiling_skipped_pins.csv](_audit_ceiling_skipped_pins.csv); authored cells in
[_audit_ceiling_authored.csv](_audit_ceiling_authored.csv).

| Region | Fuel | Pinned anchors (volume %) |
|---|---|---|
| Brunei | Biodiesel · Bioethanol | 2025 (0.0) each |
| Cambodia | Biodiesel · Bioethanol | 2025 (0.0) each |
| Myanmar | Biodiesel · Bioethanol | 2025 (0.0) each |
| Singapore | Biodiesel · Bioethanol | 2025 (0.0) each |
| Malaysia | Bioethanol | 2025 (0.0) |
| Indonesia | Bioethanol | 2050, 2055, 2060 (20.0) |
| Philippines | Biodiesel | 2025 (4.0) |
| Philippines | Bioethanol | 2025 (10.0) |
| Malaysia | Biodiesel | 2026 (15.0), 2030 (30.0) |
| Thailand | Bioethanol | 2027–2060, 8 anchors (20.0) |
| Vietnam | Bioethanol | 2050, 2055, 2060 (20.0) |
| **Indonesia** | **Biodiesel** | **2025 (40.0), 2026–2060 all 8 anchors (50.0) — whole series** |

10 of the 38 are trivial `0.0 == 0.0`; **28 are non-trivial pins**.

> **Report back to the team.** Their `README §3` and `ANSWERS_ROUND2` line 317 both
> say **"45 of 200 cells"** are pinned. The shipped CSVs give **38**. The CSVs
> govern (their own ask A4). The prose number is wrong.

---

## 3. Group 3 — refinery `Maximum Capacity`: **0 rows**, and the Add()-preservation proof

**The team shipped a change and it was refused.** `bioenergy_leap_input.csv` carries
**80 `Maximum Capacity` rows, all in `Interp(2025, X, 2030, Y, …)` LEVEL form —
zero `Add(`**. Injecting those flips the semantics of a live variable and is the
same defect class as our own withdrawn 20260722 delta, arriving from their side.
Their `note` column concedes the uncertainty verbatim
(*"LEAP team to verify Variable name + Units match RAS schema"*). Structure is ours
(§A.23), so this is our call, not a negotiation.

### Proof that `Add()` is cumulative additions, not a level

Canon read verbatim, Indonesia / FAME Biodiesel / RAS — **untouched by this delta**:

```
Add(2025, 16, 2030, 7.5, 2035, 7.5, 2040, 7.5, 2045, 7.5, 2050, 7.5, 2055, 7.5, 2060, 4)
        sum of arguments = 65 Million GJ/Yr
```

against `Exogenous Capacity` at 2023 for the same branch/region:

```
Interp(2015, 6887, …, 2023, 18548) * 10^6 * ConvFuelUnits(liter, gj, biodiesel)
        = 636.518 Million GJ/Yr already standing
```

65 of *additions* on top of 636.5 *standing*. The team's replacement reads
`Interp(2025, 623.952, …, 2060, 2534.805)`; as a level that instructs the model to
hold Indonesian FAME at 623.952 in 2025 — i.e. **scrap ~90 % of the fleet**. The
`Add()` reading is the only one consistent with the data.

### B2 invariant, asserted at build time

The builder parses every canon refinery `Maximum Capacity` expression across all
scenarios and regions and asserts **no `Add()` argument is negative**:

```
[B2] canon refinery `Maximum Capacity` rows in Add() form : 154
[B2] negative Add() arguments found                       : 0   -> PASS
```

**A negative argument aborts the build.** Because additions are never negative,
cumulative capacity can never fall below the standing fleet, so cap-below-fleet is
**structurally unreachable** and the power-sector idiom
`Max(Exogenous Capacity[MW], N)` has nothing to guard against here. Per B2 **no such
guard is authored** — that idiom belongs to LEVEL-semantics variables only.

The 5 `canon_cap_below_own_fleet == True` rows in the team's
`capacity_vs_fleet_audit.csv` are artifacts of comparing a cumulative-additions
number against a level, not defects.

---

## 4. Group 4 — refinery build rate, 70 rows

Source: `build_rate_limit.csv` (10 regions × 7 processes, no gaps, no dupes).
Variable: `Maximum Capacity Addition` on the 7 refinery process branches.

**Units:** the team's `unit` column was checked byte-exact against canon per process
and the build aborts on any mismatch. It matched 70/70 — 30 biodiesel rows
`Million Gigajoules/Year`, 40 ethanol rows `Million Tonne Coal Equiv/Year`.

**Canon currently holds `Unlimited` on all 70 of these cells.** Replacing it with a
finite numeric is the direction §A.11 asks for, not a tightening we invented.

### Their rule, and how the recursion was closed

```
MaxCapAdd(y) = 0                                          if y < first_feasible_year
             = MAX(one_train_floor, alpha × installed(y−1))   otherwise
```

`installed(y−1)` is the model's own accumulated capacity, so **as written the rule
is self-referential and not offline-resolvable** for any row with a non-zero
installed base.

> **STRUCTURAL RESOLUTION (ours — flag it back to the team).** We closed the
> recursion by holding **`installed(y) ≡ canon `Exogenous Capacity`, which is
> constant post-2023**. The rule then collapses to a **constant annual allowance**
> from `first_feasible_year` onward. This is the resolution the verification report
> recommended; it is a structural convention, not a content judgement, but the team
> should confirm it is the reading they intended.
>
> The alternative — unrolling on the rule's own trajectory, i.e. assuming full
> take-up so `installed(y) = installed(y−1) + MaxCapAdd(y)` — was built and
> discarded: it compounds at 1.2ⁿ and puts Indonesia FAME at ~3.8 × 10⁵ Million
> GJ/Yr by 2060. That is a badly-conditioned coefficient for no benefit, since the
> `Add()` cumulative cap (65 for Indonesia FAME) binds far tighter than either
> reading anyway. Under **both** resolutions the build-rate limit is non-binding in
> practice — it is a physical-plausibility statement, not an active constraint.

### The unrolled recursion

```
allowance = MAX(one_train_floor, alpha × installed_2023)         [constant]
series    = Interp(2025, 0, …, ffy−1, 0, ffy, allowance, 2060, allowance)
```

`alpha = 0.2/yr` uniform (70/70). `one_train_floor` = 5.8495 on all 30 GJ rows,
0.1369 on all 40 TCE rows. `first_feasible_year` = 2026 brownfield / 2028 greenfield.

- **60 of 70 rows are greenfield** (`installed_2023 = 0`) ⇒ `alpha × 0 = 0` ⇒ the
  floor binds ⇒ constant `one_train_floor` from 2028. No recursion at all.
  ```
  Brunei / CME Biodiesel : Interp(2025, 0, 2027, 0, 2028, 5.8495, 2060, 5.8495)
  ```
- **10 rows are brownfield.** 4 have `alpha × installed` above the floor:
  ```
  Indonesia / FAME Biodiesel : Interp(2025, 0, 2026, 127.3037, 2060, 127.3037)
  Thailand  / FAME Biodiesel : Interp(2025, 0, 2026,  19.9727, 2060,  19.9727)
  Malaysia  / FAME Biodiesel : Interp(2025, 0, 2026,  10.8443, 2060,  10.8443)
  Thailand  / Molasses       : Interp(2025, 0, 2026,   0.2227, 2060,   0.2227)
  ```
  The other 6 fall back to the floor.

Per-row trail — installed used, `alpha × installed`, which term binds, and the
resulting series: [_audit_buildrate_unroll.csv](_audit_buildrate_unroll.csv).

### B4 knock-on: Philippines FAME `installed_2023` was re-based

The team read `installed_2023 = 225.0` for Philippines FAME straight off the
**defective** canon expression (bare `Interp`, no multiplier — see §5). Left alone it
would hand the Philippines a ~29× inflated build allowance (45 vs 1.54 Mn GJ/yr at
first step). The builder re-bases it:

```
225.0 × 0.0343174 GJ/liter = 7.7214 Million GJ/Yr
alpha × 7.7214 = 1.5443  <  one_train_floor 5.8495   ->  the FLOOR binds
Philippines / FAME Biodiesel : Interp(2025, 0, 2026, 5.8495, 2060, 5.8495)
```

The GJ/liter factor is **derived, not hardcoded** — it is
`Indonesia installed_2023 / 18548` from the team's own file, cross-checked against
the Malaysia (1580) and Thailand (2910) siblings (agreement to 6×10⁻⁷ relative;
the build aborts above 10⁻⁵).

**Emitted as pure numerics** — no `Max()`, no `Min()` — so §11.2e cannot fire.

---

## 5. Group 5 — Philippines FAME `Exogenous Capacity` (B4), 3 rows

**The defect.** Canon holds, for `Transformation\Biodiesel Production\Processes\FAME Biodiesel`,
region Philippines:

```
Interp(2015, 204, 2016, 227, 2017, 220, 2018, 220, 2019, 242, 2020, 188,
       2021, 198, 2022, 203, 2023, 225)
```

while **all three non-zero siblings carry a multiplier**. Sibling quoted verbatim
(Thailand, RAS):

```
Interp(2015, 2060, 2016, 2060, 2017, 2310, 2018, 2445, 2019, 2580, 2020, 2580,
       2021, 2910, 2022, 2910, 2023, 2910) * 10^6 * ConvFuelUnits(liter, gj, biodiesel)
       ? (ACE) Biofuel Production, Feedstock, and Land Use Data in ASEAN.xlsx
```

(Indonesia and Malaysia are identical in shape.) The Philippines series is in the
same underlying units — million litres per year — so without the multiplier it is
read as ~225 **Million GJ/Yr** instead of 7.72, a **~29× overstatement**.
`Exogenous Capacity` is a **LOWER** bound (it exports to NEMO as `ResidualCapacity`),
so this forces plant the Philippines does not have.

**The fix — sibling shape mirrored exactly, series untouched:**

```
Interp(2015, 204, 2016, 227, 2017, 220, 2018, 220, 2019, 242, 2020, 188,
       2021, 198, 2022, 203, 2023, 225) * 10^6 * ConvFuelUnits(liter, gj, biodiesel)
       ? (ACE) Biofuel Production, Feedstock, and Land Use Data in ASEAN.xlsx
```

Unit `Million Gigajoules/Year`, from canon. This is a **structure-side** correction
(ours, §A.23) — it changes no content, it restores the unit conversion the other
three regions already have. The builder asserts the defect signature is still
present in canon before writing (`Interp(` present, `ConvFuelUnits` absent) and
aborts if canon has moved.

### Scenario scope — what was found, and what was authored

Canon carries the defective bare form in **all 11 scenarios**, including
`Current Accounts`. That is inheritance, not 11 authorings: every region's
`Exogenous Capacity` on this branch is byte-identical across all 11, which is the
signature of one authoring in the CA root inherited everywhere.

**Authored: 3 rows — RAS, ATS, BAS.** The declared scenario set for this cycle is
BAS/ATS/RAS, and `Current Accounts` is outside it. Scenario values override
inheritance, so the three run scenarios are fully corrected.

> **Flag for the operator.** `Current Accounts` still holds the defective bare form
> and is NOT touched by this delta. That is deliberate — the previous delta was
> partly killed for writing `Exogenous Capacity` into CA and rewriting the
> historical base (`SUPERSEDED.md` item 4). Correcting CA is a separate, explicitly
> authorised decision. Until it is made, Current-Accounts results for Philippines
> FAME biodiesel remain ~29× overstated.

---

## 6. Group 6 — 0 rows, and the full inventory of what was left out

`bioenergy_leap_input.csv` (581 rows) was diffed row-by-row against the repo
baseline [inject/bioenergy/canonical_leap_inputs.csv](../canonical_leap_inputs.csv)
after expanding their `All 10 AMS` aggregate token. **Nothing from it is authored.**
Inventory, so the operator can call any block back in:

| Block | Rows | Why it is out |
|---|---:|---|
| Refinery `Maximum Capacity`, LEVEL form | 80 | **B1** — see §3. |
| `Resources\Primary\{Cassava, Coconut Oil, Corn, Palm Oil, Sugarcane}` `Maximum Production` + `Import Cost` | 100 | In R1 scope and canon-backed, but a **re-anchoring** (annual series → 8 anchors) of variables rooted in **Current Accounts** across 11 scenarios. Authoring them needs a scenario-placement ruling we have not been given, and a CA write is the exact failure mode that killed the previous delta. |
| `Resources\Primary\{Molasses, Palm Oil Mill Effluent}` `Import Cost` — genuinely new | 20 | Same CA-rooting problem. These fill the "every cap needs a companion cost" gap (the 2026-05-19 POME unlock) and are the strongest candidate to add next cycle — but that unlock is recorded as already resolved, so re-authoring here would be unverified duplication (§A.14: no COM available to check the live area). |
| `Capital Cost` / `Fuel Cost` / `Avg Environmental Loading` reshaped to `All 10 AMS` | ~40 | Same values as baseline, collapsed to an aggregate token. No content change; pure reshape. |
| `Resources\Primary\{Biomass, Wood}` `Maximum Imports` + `Import Cost` | 4 | Outside R1 (not liquid-chain feedstocks). Already canonised as the aeo9_v0.71 manual fix (J. Veysey, 2026-07-08); these are the team echoing it back. Note they are numeric-first `Max(5000000, Maximum Production[GJ])` — pre-existing, left alone, but **anything we author fresh must stay numeric-last** (§11.2e). |
| 5 lite-panel `Maximum Production` rows (`Charcoal\All Biomass`, `Anaerobic Digestion`, both Methanol, Ammonia) | 5 | **R1** — explicitly out of scope. |
| `Rice Straw`, `Used Cooking Oil`, `Cellulosic Rice Straw` | 61 | **B6** — branches do not exist in canon. |

> **Report back — `p4_pending_branch_creates.csv` under-lists by 10.** It has 51
> rows, but `bioenergy_leap_input.csv` carries **61** rows on those same three
> non-canon branches. The delta is exactly the 10
> `Cellulosic Rice Straw : Maximum Capacity` rows. Any filter must key on the
> **three branch paths**, not on the 51-row pending file, or 10 rows leak in.
> This builder keys on branch path and asserts it.

---

## 7. Gate results

`python inject/bioenergy/20260722b/_run_gates.py` — gates discovered from
`nemo_read.__all__`, not hardcoded:

```
[PASS] assert_interp_canonical            : checked 112 expressions, 0 rejected
[PASS] find_region_lock_violations        : 0 finding(s)      (§A.21 + §A.23)
[PASS] find_zero_existing_capacity_conflicts : 0 finding(s)   (§11.2b)
[PASS] validate_canonical_csv_expressions : 0 finding(s)      (§A.15)

GATES: ALL PASS
```

`assert_interp_canonical` takes an **expression**, not a path — calling it with the
CSV path is a silent false PASS. The runner inspects each gate's signature and
routes per-expression gates over all 112 rows individually.

Additional in-builder assertions, any of which aborts the build:

- no `Unlimited` anywhere (§A.11)
- no `;` in any expression, no comma-decimal (§A.15)
- no numeric-first `Max(`/`Min(` (§11.2e)
- no `Maximum Capacity` row (B1 tripwire)
- no `Rice Straw` / `Used Cooking Oil` / `Cellulosic` branch (B6)
- every `ams` in the 10-name LEAP roster; no Timor Leste, no Base Template
- every `scenario` ∈ {RAS, ATS, BAS}; no CNZ, no Current Accounts
- ceiling < floor anywhere ⇒ abort
- ceiling/floor grids complete at 200 cells with identical key sets
- 162/38/0 split re-derived, not taken on trust
- canon `Add()` arguments all ≥ 0 (B2)
- team `unit` == canon `unit` per process on all 70 build-rate rows
- GJ/liter factor agrees across three sibling regions to < 10⁻⁵ relative
- canon Philippines FAME still matches the B4 defect signature

Round-trip: `normalize_interp()` changes **0 of 112** expressions, so the committed
form is already the normalised form and readback should be EXACT, not NORMALISED.
All 112 rows are pure ASCII — none of the U+2014 em-dashes found in the team's
comment tails carried through.

---

## 8. Inject checklist (when the operator is ready)

Not run here — files only.

- Blind mode is **DEFAULT ON**; pair with `--fail-fast` (§A.20).
- Pass `--exclude-timor-leste` (§A.18; TL is disabled in calc — no TL rows exist in
  this delta either way).
- `--scenarios "Regional Aspiration Scenario,AMS Target Scenario,Baseline Simulation"`
  in ONE COM session (§A.10). The `scenario` column routes each row to its own
  scenario (§A.20 #2).
- Confirm area + scenario with the user before dispatch (§A.9).
- LEAP → Settings → Regional → decimal separator must be `.` (§A.20 #3).
- Delta is small enough for **exhaustive** readback, not sampled: require
  112 EXACT / 0 NORMALISED / 0 FAIL.
- Eye-test one multi-scenario branch in the UI — Philippines FAME
  `Exogenous Capacity` is the right one (it is the only variable written to more
  than one scenario).

## 9. Open items to send back to the team

1. **`Maximum Capacity` must be re-shipped in `Add()` form** if they want a change
   to it — cumulative additions, not a level. (§3)
2. **Indonesia Bioethanol `canon_mandate_vol_pct` is misread**: canon is
   `InterpFSY(2025, 20, 2050, 50)` (E50 at 2050) but their floor column reads it as
   reaching 20 at 2050 — contradicting their own `canon_mandate_parsed.csv`, which
   correctly records `endpoint_pct 50`. Corrected, their floor would exceed their
   own ceiling (20.0) at 2050/2055/2060 — a blocking inversion where they currently
   show a benign pin. **This delta authored their shipped values as given**, so the
   understatement is carried through and will need a re-ship.
3. **45 vs 38** pinned-cell count: prose disagrees with the CSVs. (§2)
4. **`p4_pending` under-lists by 10** `Cellulosic Rice Straw : Maximum Capacity`
   rows. (§6)
5. **Confirm the build-rate recursion convention** — constant allowance on a frozen
   `installed_2023`, vs compounding on full take-up. (§4)
6. **`installed_2023` for Philippines FAME was re-based** 225.0 → 7.7214 on our side
   because it inherited the B4 canon defect. (§4)
7. **Current Accounts still holds the Philippines FAME defect** — needs an explicit
   authorisation to fix. (§5)
