# nemo_read cookbook

Idiomatic recipes for common tasks against LEAP/NEMO scenario databases. Every recipe assumes `from nemo_read import ...` and `db = NemoDB("path.sqlite")` at the top.

## Contents

1. [First-look inventory](#first-look-inventory)
2. [Installed capacity by technology and year](#installed-capacity-by-technology-and-year)
3. [Production mix by fuel](#production-mix-by-fuel)
4. [Emissions trajectories](#emissions-trajectories)
5. [Total system cost decomposition](#total-system-cost-decomposition)
6. [Per-time-slice dispatch profile](#per-time-slice-dispatch-profile)
7. [Joining results with descriptive labels](#joining-results-with-descriptive-labels)
8. [Cross-scenario differences](#cross-scenario-differences)
9. [Diagnosing output discontinuities at historical-to-scenario boundaries](#diagnosing-output-discontinuities)
10. [Transmission and trade](#transmission-and-trade)
11. [Custom constraints (`__NEMOcc`)](#custom-constraints-nemocc)
12. [Excluding slack technologies](#excluding-slack-technologies)
13. [Full-grid xarray for sparse parameters](#full-grid-xarray-for-sparse-parameters)
14. [Finding dormant technologies and candidate transmission](#finding-dormant-and-candidate-assets)
15. [Exporting the whole scenario for external tools](#exporting-the-whole-scenario)
16. [Working across multiple solves](#working-across-multiple-solves)
17. [Demand by sector — pairing with a LEAP-area export](#demand-by-sector)

---

## First-look inventory

```python
from nemo_read import NemoDB, print_overview, inspect_scenario

db = NemoDB("scenario.sqlite")
print_overview(db)

# Structured form for downstream filtering:
ov = inspect_scenario(db)
ov["dimensions"]   # DataFrame: dimension, present, members
ov["parameters"]   # DataFrame: parameter, present, rows, default
ov["results"]      # DataFrame: variable, known, rows, n_solves, latest_solve, dims
```

The `unknown_tables` key flags tables the library does not recognise, which usually signals either a newer NEMO version or a user-added auxiliary table.

## Installed capacity by technology and year

```python
from nemo_read import get_result, technologies

cap = get_result(db, "vtotalcapacityannual")                   # r, t, y, val, solvedtm
t_meta = technologies(db).rename(columns={"val": "t", "desc": "technology"})
cap = cap.merge(t_meta, on="t", how="left")

wide = cap.pivot_table(index="y", columns="t", values="val", aggfunc="sum")
```

`wide` is now years × technology with installed capacity values, ready for a stacked-area plot in matplotlib or for conversion to xarray via `wide.stack().to_xarray()`.

For a long-form view that includes residual plus new plus accumulated:

```python
from nemo_read import capacity_stack

stk = capacity_stack(db)                                       # r, t, y, kind, val
pivot = stk.pivot_table(index=["r", "y"], columns="kind", values="val",
                        aggfunc="sum").fillna(0)
```

## Production mix by fuel

The annual production of each fuel, combining nodal and non-nodal:

```python
from nemo_read import get_result

prod = get_result(db, "vproductionbytechnologyannual")         # r, t, f, y, val
mix = prod.groupby(["r", "f", "y"], as_index=False)["val"].sum()
```

To include residual generation patterns and renewable share:

```python
import pandas as pd

gen_nn = get_result(db, "vgenerationannualnn")                 # r, f, y, val
re_gen_nn = get_result(db, "vregenerationannualnn")
mix = gen_nn.merge(re_gen_nn, on=["r", "f", "y"], suffixes=("_total", "_re"))
mix["re_share"] = mix["val_re"] / mix["val_total"]
```

## Emissions trajectories

```python
from nemo_read import get_result, emissions

em = get_result(db, "vannualemissions")                        # r, e, y, val
em_meta = emissions(db).rename(columns={"val": "e"})
em = em.merge(em_meta, on="e", how="left")

co2 = em[em["e"] == "CO2"].pivot_table(
    index="y", columns="r", values="val", aggfunc="sum"
)
```

Technology-level attribution:

```python
by_tech = get_result(db, "vannualtechnologyemission")          # r, t, e, y, val
co2_by_tech = by_tech[by_tech["e"] == "CO2"].groupby(
    ["r", "t", "y"], as_index=False
)["val"].sum()
```

Note that `vannualemissions` includes `AnnualExogenousEmission` while `vannualtechnologyemission` does not. Differences between the two across `r`, `e`, `y` after summing over `t` isolate exogenous emissions.

## Total system cost decomposition

```python
from nemo_read import get_result

components = {
    "capex":           "vdiscountedcapitalinvestment",
    "opex_fixed":      "vannualfixedoperatingcost",
    "opex_variable":   "vannualvariableoperatingcost",
    "emission_penalty":"vdiscountedtechnologyemissionspenalty",
    "salvage":         "vdiscountedsalvagevalue",
}
frames = []
for label, table in components.items():
    if table in db.list_tables():
        df = get_result(db, table)[["r", "t", "y", "val"]].copy()
        df["component"] = label
        frames.append(df)
cost_breakdown = pd.concat(frames, ignore_index=True)

# Match against vtotaldiscountedcost (should reconcile to within rounding
# once salvage is subtracted and transmission costs are added):
total = get_result(db, "vtotaldiscountedcost").groupby("r")["val"].sum()
```

## Per-time-slice dispatch profile

Per-time-slice rates need to be weighted by `YearSplit × 8760` for energy:

```python
from nemo_read import get_result, weighted_by_yearsplit, aggregate_to_group

rate = get_result(db, "vrateofproductionbytechnologynn")       # r, l, t, f, y, val
energy = weighted_by_yearsplit(db, rate)                       # adds hours, energy

# Seasonal totals (TSGROUP1):
seasonal = aggregate_to_group(db, energy, by="tg1", value_col="energy")
```

Dispatch order within a year:

```python
from nemo_read import timeslices

ts = timeslices(db)[["l", "lorder", "tg1", "tg2", "tg1_order", "tg2_order"]]
# Chronological order requires the full composite key, not lorder alone.
dispatch = rate.merge(ts, on="l", how="left").sort_values(
    ["y", "tg1_order", "tg2_order", "lorder"]
)
```

## Joining results with descriptive labels

NEMO stores abbreviated identifiers in result tables. Merging the `desc` column from each dimension turns codes into readable names:

```python
from nemo_read import technologies, fuels, regions

def label(df, db):
    t = technologies(db).rename(columns={"val": "t", "desc": "technology"})
    f = fuels(db).rename(columns={"val": "f", "desc": "fuel"})
    r = regions(db).rename(columns={"val": "r", "desc": "region"})
    for meta, key in [(t, "t"), (f, "f"), (r, "r")]:
        if key in df.columns:
            df = df.merge(meta, on=key, how="left")
    return df

prod_labelled = label(get_result(db, "vproductionbytechnologyannual"), db)
```

## Cross-scenario differences

Opening two databases and differencing them is a common pattern for counterfactual analysis:

```python
from nemo_read import NemoDB, result_to_dataarray

bas = NemoDB("BAS.sqlite")
ats = NemoDB("ATS.sqlite")

cap_bas = result_to_dataarray(bas, "vtotalcapacityannual")
cap_ats = result_to_dataarray(ats, "vtotalcapacityannual")

delta = (cap_ats - cap_bas)                                    # aligned by labels
delta_annual = delta.sum(dim=["r", "t"])                       # total net change

# If scenarios have different member sets (new technologies in ATS), xarray
# aligns on union and fills with NaN. Use .fillna(0) when treating new entries
# as zero in the baseline.
```

For sparse comparison via pandas:

```python
cap_b = get_result(bas, "vtotalcapacityannual").assign(scenario="BAS")
cap_a = get_result(ats, "vtotalcapacityannual").assign(scenario="ATS")
long = pd.concat([cap_b, cap_a], ignore_index=True)
wide = long.pivot_table(index=["r", "t", "y"], columns="scenario", values="val").fillna(0)
wide["delta"] = wide["ATS"] - wide["BAS"]
```

## Diagnosing output discontinuities

A common diagnostic in LEAP workflows is checking whether transformation processes show a clean handover between the historical era (up to the last historical year, often 2024) and the scenario era (2025 onward). Discontinuities show up as step changes in capacity or activity that are not explained by residual retirements or exogenous capacity additions.

```python
import numpy as np
from nemo_read import get_result

hist_year = 2024
scen_year = 2025

cap = get_result(db, "vtotalcapacityannual")
pivot = cap.pivot_table(index=["r", "t"], columns="y", values="val", aggfunc="sum")

if {hist_year, scen_year}.issubset(pivot.columns):
    pivot["jump"] = pivot[scen_year] - pivot[hist_year]
    pivot["jump_frac"] = pivot["jump"] / pivot[hist_year].replace(0, np.nan)
    suspects = pivot[(pivot["jump_frac"].abs() > 0.1) | (pivot["jump"].abs() > 1.0)]
```

Cross-reference suspects against `ResidualCapacity` and `TotalAnnualMinCapacity` to see whether the step is driven by input data or by the optimiser.

```python
from nemo_read import get_parameter

res = get_parameter(db, "ResidualCapacity")
res_pivot = res.pivot_table(index=["r", "t"], columns="y", values="val", aggfunc="sum")
residual_jump = res_pivot[scen_year] - res_pivot[hist_year]
```

If the residual jump explains the total jump, the input data carries the discontinuity. If not, the optimiser is rebalancing across the boundary.

## Transmission and trade

```python
from nemo_read import get_result, transmission_lines

lines = transmission_lines(db)                                 # id, n1, n2, f, ...
flow = get_result(db, "vtransmissionbyline")                   # tr, l, f, y, val

flow_annual = (flow.groupby(["tr", "f", "y"], as_index=False)["val"]
                   .sum()
                   .merge(lines[["id", "n1", "n2"]], left_on="tr", right_on="id"))

built = get_result(db, "vtransmissionbuilt")                   # tr, y, val (0/1)
```

For bilateral trade without nodal modelling:

```python
trade = get_result(db, "vtradeannual")                         # r, rr, f, y, val
net = (trade.groupby(["r", "rr", "f", "y"], as_index=False)["val"].sum())
```

## Custom constraints (`__NEMOcc`)

LEAP lets users define custom NEMO constraints through its UI; each one lands in the scenario database as a `<Name>__NEMOcc` table with columns `(id, r, bid, eid, y, val)`. The `bid` is usually a LEAP branch ID, `eid` is a secondary identifier (often `-1` as a "not applicable" sentinel), and the values are annual across the constraint's domain.

```python
from nemo_read import list_custom_constraints, get_custom_constraint

cc = list_custom_constraints(db)
# name, short_name, rows, columns, regions, year_min, year_max

# Read one (suffix is optional):
asean = get_custom_constraint(db, "ASEANRenewableCapacityTarget")
asean_idn = asean[asean["r"] == "R1"]
```

Custom constraint tables can span a finer year resolution than the model's YEAR dimension (for example, annual 2025–2060 when YEAR only contains 2025, 2030, 2035, ..., 2060). Don't assume the `y` column aligns with YEAR.

## Excluding slack technologies

LEAP/NEMO scenarios typically carry slack technologies — "Unserved" or "Unmet Load" pseudo-processes with enormous capital costs, plus supply-side slacks with 10¹² residual capacity — to guarantee feasibility. Including them in summary totals skews everything.

```python
from nemo_read import slack_technology_ids, detect_slack_technologies

slk = detect_slack_technologies(db)
# columns: t, desc, reason (e.g. "capital_cost>=100000,name_match")

ids_to_drop = slack_technology_ids(db)

# Exclude from a DataFrame:
clean = df[~df["t"].isin(ids_to_drop)]

# Exclude from an xarray cube:
cap = parameter_to_dataarray(db, "CapitalCost")
slack_in_cube = [t for t in ids_to_drop if t in cap.coords["t"].values]
cap_clean = cap.drop_sel(t=slack_in_cube)
```

Thresholds are tunable:

```python
from nemo_read import SLACK_CAPITAL_COST_THRESHOLD, SLACK_RESIDUAL_CAPACITY_THRESHOLD
slk = detect_slack_technologies(
    db,
    residual_threshold=1e11,      # default
    cost_threshold=1e5,           # default
    name_patterns=("unserved", "unmet", "dummy"),
)
```

## Full-grid xarray for sparse parameters

Parameters without a registered default (YearSplit, ReserveMargin, TotalAnnualMaxCapacity, ...) are stored sparsely. NEMO's `_def` view returns only the stored rows, so an xarray cube built from it silently shrinks on the dimensions where a scenario happens to have partial coverage.

`parameter_to_dataarray` passes `keep_missing=True` under the hood, which bypasses the `_def` view in those cases and builds the full Cartesian grid with NaN in missing cells. For analysis that should preserve the dimension cardinality (for example, iterating over all 11 regions in a multi-region SE Asia model even when ReserveMargin only covers 10):

```python
rm = parameter_to_dataarray(db, "ReserveMargin", fill_value=float("nan"))
# shape: (|REGION|, |FUEL|, |YEAR|), NaN where ReserveMargin is silent

# Region-level aggregate that respects NaN:
rm.mean(dim=["f", "y"], skipna=True)
```

To work in pandas with the same completeness, pass `keep_missing=True` to `get_parameter`:

```python
rm_full = get_parameter(db, "ReserveMargin", keep_missing=True)
# 11 × 77 × 8 = 6776 rows, most with NaN in `val`
```

## Finding dormant and candidate assets

Two forensic helpers for scenario setup review:

```python
from nemo_read import list_unused_technologies, transmission_candidates

# Technologies declared in TECHNOLOGY but never referenced by any
# parameter — dormant, contribute nothing to the optimisation.
dormant = list_unused_technologies(db)
# val     desc
# D16175  Optimized Private Passenger Vehicles:Gasoline
# ...

# Transmission lines the optimiser may choose to build (yconstruction
# falls after the earliest modelled year).
cand = transmission_candidates(db)
# id  n1   n2   yconstruction  maxflow
# T14 N4   N5   2040           1250.0
# T21 N6   N5   2040           350.0
```

Dormant technologies are usually artefacts of how the LEAP area was exported — the schema carries more branches than the scenario actually uses. They're harmless, but a long list may indicate that the scenario is a trimmed subset of a larger model and some demand-side techs are missing their input-activity or output-activity data (in which case NEMO will not build capacity for them; the technology effectively does not exist from the optimiser's point of view).

## Exporting the whole scenario

```python
from nemo_read import dump_to_csv, dump_to_parquet

# One CSV per table, with default parameter overlay:
dump_to_csv(db, "exports/", include="all", with_defaults=True)

# Single Parquet file, sparse parameters:
dump_to_parquet(db, "scenario.parquet", with_defaults=False)
```

CSV exports are convenient for spreadsheet review and versioning in Git. Parquet preserves dtypes and is far faster to re-ingest.

## Working across multiple solves

```python
db.solvedtm_values("vtotaldiscountedcost")
# e.g. ['2026-01-15 09:30:00', '2026-02-20 14:05:00']
```

To materialise results from a specific solve rather than the latest:

```python
cap_v1 = get_result(db, "vtotalcapacityannual", solvedtm="2026-01-15 09:30:00")
cap_v2 = get_result(db, "vtotalcapacityannual", solvedtm="2026-02-20 14:05:00")
```

When a scenario has been recalculated and the older rows are no longer useful, `NemoMod.dropresulttables(db)` in Julia clears everything `v*`-prefixed, or use `NemoDB(path, read_only=False).query("DELETE FROM vtotalcapacityannual WHERE solvedtm < ?", [cutoff])` from Python. Be careful: this modifies the database LEAP shares with the UI.

## Demand by sector

NEMO's `SpecifiedAnnualDemand(r, f, y)` and `AccumulatedAnnualDemand(r, f, y)` carry only fuel × region × year totals — sector breakdown (Industry / Residential / Transport / etc.) is collapsed during LEAP's NEMO export. To recover sectors, pair the SQLite with a one-time LEAP-area export captured by `nemo_read-leap-export`.

### One-time setup (Windows + LEAP, ~15–20 minutes)

```bash
# In a venv with the [leap] extra:
pip install 'nemo_read[leap]'

# With LEAP open and the target area loaded:
nemo_read-leap-export --scenario "Regional Aspiration Scenario"
```

This writes (defaults) to `<scenario_db_stem>.leap_export/` next to the SQLite. The directory contains `branches.csv`, `branch_variable_values.csv` (Final Energy Demand + Activity Level for every demand-tree leaf, all years × all regions), and the dimension catalogues. You only need to re-run this when the LEAP area changes structurally.

### Reading sector-level demand (any platform, no LEAP needed)

```python
from nemo_read import NemoDB, LeapAreaContext, read_demand

db  = NemoDB("NEMO_25.sqlite")
ctx = LeapAreaContext.discover(db)        # auto-finds the adjacent .leap_export/

# Sector × subsector × region × year
df = read_demand(db, by="sector", context=ctx)

# Indonesia 2030 sectoral mix
indo = df[(df["region_name"] == "Indonesia") & (df["year"] == 2030)]
sector_totals = indo.groupby("sector")["val"].sum().sort_values(ascending=False)
```

`val` is in the LEAP variable's own unit (typically GJ for per-tech demand). Cross-check one number against LEAP's Results pane to confirm scale.

### Falling back to fuel-only when no LEAP context is available

```python
df = read_demand(db)                       # by="fuel" default; SQLite-only, decoded
# columns: region_name, r, fuel_name, f, y, val, source
```

This works on any machine — no LEAP, no pywin32 — but the sector dimension is gone (NEMO never had it).
