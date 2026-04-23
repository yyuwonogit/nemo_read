"""
Time-slice utilities.

NEMO's sub-annual representation has three tiers:

    TSGROUP1   (e.g. season)
        └── TSGROUP2   (e.g. day type)
                  └── TIMESLICE   (intra-day / intra-week bracket)

The mapping is stored in `LTsGroup` with each TIMESLICE `l` tagged with its
`tg1` and `tg2`. `YearSplit(l, y)` gives the fraction of the year covered by
`l` in year `y`. Multiplying a per-time-slice rate by `YearSplit × 8760`
yields annual energy.

TSGROUP multipliers and representative weeks
---------------------------------------------
LEAP often builds the 48-slice structure from a *representative week per
season*: two seasons × one day type × 24 hour-slices × 1 week = 48 slices,
then scales up to the full 8760 hours via `TSGROUP1.multiplier`. In that
convention::

    TSGROUP1.multiplier = (hours in season) / 168

so `multiplier × 168 = seasonal hours`, and the sum of seasonal hours
across TSGROUP1 members equals 8760. `tsgroup_hours()` surfaces this
directly.
"""

from __future__ import annotations
from typing import Optional

import pandas as pd

from .db import NemoDB
from .parameters import get_parameter
from .dimensions import timeslices, timeslice_groups


HOURS_PER_YEAR = 8760.0                                         # nominal, NEMO convention
HOURS_PER_WEEK = 168.0                                          # for representative-week scaling


def year_split(db: NemoDB) -> pd.DataFrame:
    """YearSplit parameter expanded with group context.

    Returns columns: l, y, yearsplit, hours, tg1, tg2, lorder.
    `hours` = yearsplit × 8760 for convenience.
    """
    ys = get_parameter(db, "YearSplit")                         # defaults-resolved
    ts = timeslices(db)                                         # l -> tg1/tg2
    out = ys.rename(columns={"val": "yearsplit"}).merge(ts, on="l", how="left")
    out["hours"] = out["yearsplit"].astype(float) * HOURS_PER_YEAR
    return out.sort_values(["y", "lorder"]).reset_index(drop=True)


def weighted_by_yearsplit(
    db: NemoDB,
    rate_df: pd.DataFrame,
    value_col: str = "val",
) -> pd.DataFrame:
    """Convert a per-time-slice rate into annual energy by multiplying
    by `YearSplit × 8760` per (l, y). Adds an `energy` column and leaves
    the original rate intact."""
    ys = year_split(db)[["l", "y", "hours"]]                    # lookup table
    merged = rate_df.merge(ys, on=["l", "y"], how="left")       # attach hours
    merged["energy"] = merged[value_col].astype(float) * merged["hours"]
    return merged


def aggregate_to_group(
    db: NemoDB,
    df: pd.DataFrame,
    by: str = "tg1",
    value_col: str = "val",
) -> pd.DataFrame:
    """Aggregate a time-sliced frame up to TSGROUP1 or TSGROUP2 level.
    Sums `value_col` across time slices within each group, keeping any
    other dimension columns (r, t, f, y, n, ...) as grouping keys.
    """
    if by not in ("tg1", "tg2"):                                # validate
        raise ValueError("by must be 'tg1' or 'tg2'.")
    ts = timeslices(db)[["l", by]]                              # mapping
    joined = df.merge(ts, on="l", how="left")                   # attach group
    other_keys = [c for c in joined.columns if c not in ("l", "val", "energy", value_col)]
    group_cols = [c for c in other_keys if c in joined.columns and c != by] + [by]
    return joined.groupby(group_cols, dropna=False)[value_col].sum().reset_index()


def tsgroup_hours(db: NemoDB) -> pd.DataFrame:
    """Return per-TSGROUP1 annualised hours derived from NEMO's time-slicing identity.

    NEMO's docs specify: for every year, the group and slice counts
    multiplied by both group multipliers must sum to 8760:

        sum_tg1 [ sum_tg2 [ ( sum_l 1 ) × m_tg2 ] × m_tg1 ] = 8760

    In practice LEAP often builds 48 slices = 2 seasons × 1 day-type × 24
    hour-slices, scaled up by m_tg1 × m_tg2 to reach 8760. This helper
    computes the annualised hours each TSGROUP1 member occupies over the
    full year, correctly accounting for the TSGROUP2 multiplier.

    Columns returned:

        level       : always 'tg1'
        name        : TSGROUP1 member (e.g. 'TGA1')
        desc        : description
        grp_order   : chronological order within the year
        multiplier  : TSGROUP1.multiplier, as stored
        slices      : number of TIMESLICE rows mapped into this group
        hours_yr    : annualised hours occupied by the group over the
                      full year, computed via the NEMO identity above

    When ``hours_yr`` across TSGROUP1 sums to 8760, the schema is
    consistent. A mismatch means either the time-slicing is malformed or
    uses a non-representative-week structure; in that case ``YearSplit``
    is the authoritative source.
    """
    tsg = timeslice_groups(db)                                  # both levels
    tg1 = tsg[tsg["level"] == "tg1"].copy()                     # TSGROUP1 only
    tg2 = tsg[tsg["level"] == "tg2"].copy()                     # TSGROUP2 only

    # For each (tg1, tg2), count slices and multiply by tg2.multiplier to
    # get the hours contributed by that sub-group for one cycle of tg1.
    # Then multiply by tg1.multiplier to annualise.
    slice_counts = (timeslices(db)
                    .groupby(["tg1", "tg2"])
                    .size()
                    .rename("slices")
                    .reset_index())
    slice_counts = slice_counts.merge(
        tg2[["name", "multiplier"]].rename(
            columns={"name": "tg2", "multiplier": "m_tg2"}),
        on="tg2", how="left",
    )
    # Hours per tg1 from this sub-group, per single tg1 cycle:
    slice_counts["hours_per_tg1_cycle"] = (
        slice_counts["slices"].astype(float)
        * slice_counts["m_tg2"].astype(float)
    )
    per_tg1 = (slice_counts.groupby("tg1")["hours_per_tg1_cycle"]
               .sum().rename("hours_per_cycle").reset_index())

    out = tg1.merge(per_tg1, left_on="name", right_on="tg1", how="left")
    out = out.drop(columns=["tg1"])
    out["slices"] = out["name"].map(
        slice_counts.groupby("tg1")["slices"].sum().to_dict()
    ).fillna(0).astype(int)
    out["hours_yr"] = (out["multiplier"].astype(float)
                       * out["hours_per_cycle"].astype(float))
    return out[["level", "name", "desc", "grp_order",
                "multiplier", "slices", "hours_yr"]]
