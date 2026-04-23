# LEAP conventions and validation

Three things the NEMO SQLite file does not tell you explicitly but that every LEAP-generated database follows. Plus a pre-flight validator that catches common issues.

## Contents

- [Units of measure](#units-of-measure)
- [LEAP branch IDs in fuel descriptions](#leap-branch-ids-in-fuel-descriptions)
- [Technology ID prefix convention](#technology-id-prefix-convention)
- [Time-slice scaling: the representative-week convention](#time-slice-scaling-the-representative-week-convention)
- [Validation](#validation)
- [Reading `nemo.cfg` options](#reading-nemo-cfg-options)

## Units of measure

From the NEMO documentation on custom constraints: "When LEAP runs NEMO, it uses petajoules as the energy unit, gigawatts for power, million $ for costs, and metric tonnes for emissions." The library exposes these as constants:

```python
from nemo_read import LEAP_NEMO_UNITS, units_for

LEAP_NEMO_UNITS
# {'energy': 'PJ', 'power': 'GW',
#  'cost': 'million currency units', 'emissions': 't'}

units_for("vnewcapacity")                 # 'GW'
units_for("vproductionbytechnologyannual")# 'PJ'
units_for("vannualemissions")             # 't'
units_for("CapitalCost")                  # 'million currency units'
units_for("AvailabilityFactor")           # None (dimensionless)
```

Conversion helpers: `PJ_TO_J`, `GW_TO_W`, `T_TO_KG`, `MILLION` are exported for when you need to convert to SI base units (e.g. for comparison with IEA statistics that report TWh or EJ).

## LEAP branch IDs in fuel descriptions

LEAP formats every fuel's `desc` as `"<human readable> [LEAP ID:N]"`, where `N` is the LEAP branch ID. This is the key for joining the NEMO SQLite data back to the LEAP tree:

```python
from nemo_read import fuels_with_leap_ids, extract_leap_ids

fli = fuels_with_leap_ids(db)
# val    desc                                                        leap_id
# F1     Useful demand for Trucks [LEAP ID:16575]                    16575
# F2     Hydrogen input to "Centralized Electricity Gen..." [ID:35]  35
# ...

# Works on any DataFrame with a desc column:
custom = extract_leap_ids(some_df, desc_col="desc", out_col="leap_id")
```

Technology descriptions do **not** follow this pattern consistently, so the LEAP branch ID for a technology has to be recovered a different way (see the open questions at the end of this document).

## Technology ID prefix convention

LEAP's NEMO export assigns single-letter prefixes to technology IDs based on their role in the energy system:

| Prefix | Kind | Example | Description |
|---|---|---|---|
| `D` | demand | `D16677` | end-use technology (transport, building heat, appliances) |
| `P` | process | `P16756`, `P2641` | generation, conversion, distribution, storage technology |
| `S` | supply | `S13I`, `S15D` | resource extraction or fuel import |
| (other) | other | `Unserved` | slack and named pseudo-technologies |

```python
from nemo_read import technology_kinds, classify_technology_id

tk = technology_kinds(db)
# val      desc             kind
# D16677   Trucks:Hydrogen  demand
# P16756   Solar PV Rooftop process
# S13I     Solar Imports    supply
# Unserved Unserved         other

classify_technology_id("P2641")    # 'process'
classify_technology_id("Unserved") # 'other'
```

Use this to split a summary by kind rather than re-filtering by hand each time.

## Time-slice scaling: NEMO's hours identity

NEMO's official time-slicing identity is:

```
sum_{tg1} [ sum_{tg2} [ ( sum_{l in (tg1,tg2)} 1 ) × TSGROUP2.multiplier ] × TSGROUP1.multiplier ] = 8760
```

Every LEAP-generated time-slice schema must satisfy this. A common LEAP pattern is `N seasons × 1 day-type × 24 hour-slices`, with `TSGROUP1.multiplier = seasonal_hours / 168` and `TSGROUP2.multiplier = 7`. For a wet/dry split on the SE Asia database:

```
TGA1 Wet: 24 slices × 7 (weekdays/week) × 21.857143 (weeks / season) = 3672 hours
TGA2 Dry: 24 slices × 7 × 30.285714                                 = 5088 hours
Total: 8760
```

The library surfaces the annualised hours per TSGROUP1 member directly:

```python
from nemo_read import tsgroup_hours

tgh = tsgroup_hours(db)
# level name desc             grp_order  multiplier  slices  hours_yr
# tg1   TGA1 Wet (Hrs:3672)   1          21.857143   24      3672.0
# tg1   TGA2 Dry (Hrs:5088)   2          30.285714   24      5088.0

# Sanity: hours_yr should sum to 8760
assert abs(tgh["hours_yr"].sum() - 8760) < 1e-6
```

The internal computation uses the full identity, so it is agnostic to whether the scheme is representative-week, monthly, or something else. A mismatch against 8760 indicates an inconsistent time-slicing setup.

**Ordering**: `LTsGroup.lorder` is only unique within each `(tg1, tg2)` combination, not globally. For chronological ordering, `timeslices(db)` sorts by `(tg1_order, tg2_order, lorder)` and exposes those order columns. Sorting by `lorder` alone interleaves seasons, which is wrong for dispatch plots.

## Validation

`validate_scenario(db)` runs a battery of sanity checks and returns a `ValidationReport`:

```python
from nemo_read import validate_scenario

report = validate_scenario(db)
report.print()
# Validation: 0 errors, 1 warnings, 0 info.
#   ⚠ [demand] SpecifiedDemandProfile: 184 (r,f,y) combos have
#     SpecifiedAnnualDemand>0 but no profile; NEMO may fail or assume
#     uniform profile.

if not report.ok():
    for issue in report.errors():
        print(issue.message)
        if issue.sample is not None:
            print(issue.sample)
```

Checks performed:

| Category | What it catches |
|---|---|
| `schema` | NEMO data-dictionary version mismatch |
| `referential` | Any parameter row whose dimension column references an unknown member (e.g. `CapitalCost.t` pointing to a technology not in `TECHNOLOGY`) |
| `referential` | `NODE.r` → `REGION`, `TransmissionLine.n1/n2/f` → `NODE`/`FUEL` |
| `timeslice` | `YearSplit` not summing to 1.0 per year |
| `demand` | `SpecifiedDemandProfile` not summing to 1.0 per `(r, f, y)` |
| `demand` | `SpecifiedAnnualDemand > 0` with no matching `SpecifiedDemandProfile` rows |
| `storage` | `MinStorageCharge` without matching `StorageLevelStart`, or `MinStorageCharge > StorageLevelStart` per (r, s, y) — NEMO's documented infeasibility trigger |
| `emissions` | Negative `EmissionActivityRatio` combined with negative `EmissionsPenalty` and no activity/capacity upper bound — NEMO's documented unbounded-profit risk for CCS-like configurations |
| `emissions` (info) | Presence of negative emission factors, flagged as informational since they're legitimate for sequestration technologies |
| `missing` | Critical parameters (`YearSplit`, `OperationalLife`, `CapitalCost`, `OutputActivityRatio`) absent or empty |

Severity levels:

- `error` — will likely cause NEMO to fail or produce meaningless output. Fix before calculating.
- `warning` — investigate. May be intentional (e.g. feedstock demands that use accumulated rather than time-sliced profiles).
- `info` — neutral, informational.

`strict=True` elevates certain warnings to errors and is appropriate when a script is about to feed the database to NEMO. The default is tolerant so that exploratory scripts don't get blocked by cosmetic issues.

Always run validation before analysis on a database you didn't build yourself. The 184-row missing-profile warning on the real SE Asia database caught a legitimate modelling question about biofuel feedstock demands that would otherwise have been invisible.

## Infeasibility checks

`find_infeasibilities(db)` runs a battery of static checks that look for patterns the NEMO solver will reject — the Python-only counterpart to NEMO's own `find_infeasibilities` function, which operates on a built JuMP model and requires the Julia runtime. The static tool catches the common culprits the NEMO docs list:

| Category | What it catches |
|---|---|
| `bound_inversion` | `TotalAnnualMinCapacity > TotalAnnualMaxCapacity` per `(r, t, y)`, same for investment bounds, storage bounds, and activity limits (annual and model-period) |
| `emission_limit` | `AnnualExogenousEmission > AnnualEmissionLimit` per `(r, e, y)` and the model-period variant — NEMO docs flag this as a classic infeasibility trigger |
| `share_constraints` | `MinShareProduction` entries summing to more than 1.0 per `(r, f, y)` |
| `utilization` | `MinimumUtilization > AvailabilityFactor` per `(r, t, l, y)` — forces dispatch above physical availability |
| `storage` | `MinStorageCharge > StorageLevelStart` (NEMO-documented infeasibility) |
| `storage` (warning) | Residual storage capacity with no charging or discharging technology tagged |
| `reserve_margin` | `ReserveMargin > 0` without any `ReserveMarginTagTechnology` entry for the same `(r, f, y)` |
| `supply_chain` (warning) | Demand for a fuel in a region with no technology producing it via `OutputActivityRatio` (trade may still cover it; review manually) |
| `unbounded` (warning) | Negative `EmissionActivityRatio` combined with negative `EmissionsPenalty` and no activity or capacity upper bound — NEMO's documented infinite-profit trap for CCS configurations |

```python
from nemo_read import find_infeasibilities, check_scenario

inf = find_infeasibilities(db)
inf.print()
# ✗ [utilization] MinimumUtilization vs AvailabilityFactor:
#     48 (r,t,l,y) combos where MinimumUtilization exceeds
#     AvailabilityFactor; technology cannot meet both.
# ⚠ [unbounded] EmissionActivityRatio vs EmissionsPenalty:
#     44 (r,t,e) combos combine negative emission factor and
#     negative emission penalty without a capacity or activity
#     upper bound. NEMO may become unbounded (infinite profit).

# One-stop that merges validation + infeasibility and dedupes:
all_issues = check_scenario(db)
```

Severity levels match `validate_scenario`:

- `error` — structurally infeasible. NEMO will report infeasibility or refuse to build the model.
- `warning` — unboundedness risk or a likely-but-not-guaranteed issue (e.g. demand for a fuel with no local producer that might still be covered via trade).

The checks are conservative by design. If a condition cannot be decided from the SQLite data alone (e.g. whether a renewable share target is achievable given endogenous capacity expansion), the check is skipped rather than emitting a guess. For dynamic diagnosis after the model builds, use NEMO's own `find_infeasibilities` from Julia.

Run the combined check before every calculation. The infeasibility tool caught 48 genuine (r, t, l, y) combos on the real SE Asia database where three solar technologies in one sub-region have tiny non-zero `MinimumUtilization` floors at nighttime timeslices where `AvailabilityFactor = 0` — a guaranteed solver failure that would have taken hours to diagnose from NEMO's error output alone.

## Reading `nemo.cfg` options

LEAP scenarios can ship with a `nemo.cfg` or `nemo.toml` file (in the LEAP area folder, not the SQLite file) that sets NEMO runtime options: `varstosave`, `calcyears`, `continuoustransmission`, `forcemip`, and so on. These options control what gets computed and saved when the scenario runs, so they affect what the library will eventually find in the `v*` tables.

The config file is not part of the SQLite database and the library cannot read it directly. If the config path is known, read it with Python's standard library:

```python
import tomllib
from pathlib import Path

cfg_path = Path("/path/to/LEAP Areas/MyArea/nemo.cfg")
if cfg_path.exists():
    with open(cfg_path, "rb") as f:
        cfg = tomllib.load(f)
    varstosave = cfg.get("calculatescenarioargs", {}).get("varstosave", [])
    calcyears = cfg.get("calculatescenarioargs", {}).get("calcyears", [])
```

Custom constraints scripts referenced by the config (`customconstraints = "./customconstraints.txt"`) live alongside in the LEAP Areas folder and are Julia source. The library does not parse Julia; inspect manually to understand constraint logic.
