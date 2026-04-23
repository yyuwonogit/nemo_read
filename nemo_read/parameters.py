"""
Readers for NEMO parameter (input) tables.

Two levels of access:
    * `get_parameter_raw()`  — exactly what is stored in the table.
    * `get_parameter()`      — default-resolved; uses the NEMO `_def` view
                                when available, otherwise reconstructs the
                                default overlay ourselves from DefaultParams
                                plus the Cartesian product of the dimensions.

The default overlay matters because NEMO stores parameters sparsely. A
user who reads `CapitalCost` directly sees only the rows that differ from
the default, which is almost never what you want for analysis.
"""

from __future__ import annotations
from functools import reduce
from typing import Dict, List, Mapping, Optional, Sequence

import pandas as pd

from .db import NemoDB
from .schema import DIMENSIONS, DIMENSION_ABBREVIATIONS, PARAMETERS, Parameter


def _coerce_year_column(df: pd.DataFrame, year_col: str = "y") -> pd.DataFrame:
    """Cast `y` column to Int64 if present. NEMO stores years as TEXT."""
    if year_col in df.columns:                                  # only if present
        df[year_col] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
    return df


def get_parameter_raw(db: NemoDB, name: str) -> pd.DataFrame:
    """Return the stored parameter rows with no default expansion."""
    if name not in PARAMETERS:                                  # validate name
        raise KeyError(f"{name!r} is not a known NEMO parameter.")
    cols = PARAMETERS[name].dims + (PARAMETERS[name].value_col,)# dims + val-or-type
    col_list = ", ".join(cols)                                  # SQL column list
    df = db.query(f"SELECT {col_list} FROM {name}")             # fetch
    return _coerce_year_column(df)                              # normalise y


def get_parameter(
    db: NemoDB,
    name: str,
    apply_filters: Optional[Mapping[str, Sequence]] = None,
    with_defaults: bool = True,
    keep_missing: bool = False,
) -> pd.DataFrame:
    """Return the parameter with defaults applied (if any).

    Parameters
    ----------
    db : NemoDB
    name : str
        Parameter table name, e.g. 'CapitalCost'.
    apply_filters : dict, optional
        Column → iterable of allowed values. Applied after the fetch, so
        works uniformly whether defaults come from a NEMO view or this
        module's reconstruction.
    with_defaults : bool, default True
        If False, behaves like `get_parameter_raw`.
    keep_missing : bool, default False
        When the parameter has no registered default, controls what
        happens to missing (r, t, y, ...) combinations. False (default)
        drops them, matching NEMO's own `_def` views. True keeps the full
        Cartesian grid with NaN in the value column — useful for
        ``parameter_to_dataarray`` so the resulting cube covers every
        dimension member rather than silently shrinking.
    """
    if name not in PARAMETERS:                                  # validate
        raise KeyError(f"{name!r} is not a known NEMO parameter.")

    value_col = PARAMETERS[name].value_col                      # 'val' for most, 'type' for TME

    if not with_defaults:                                       # short-circuit
        df = get_parameter_raw(db, name)
    elif (db.has_def_view(name) and value_col == "val"
          and not keep_missing):                                # prefer NEMO view
        # When keep_missing=True is requested, we deliberately bypass the
        # NEMO `_def` view and use our own overlay, because the view does
        # not emit rows for combinations outside the stored table when no
        # default is registered. Our reconstruction can keep NaN rows.
        cols = PARAMETERS[name].dims + (value_col,)
        df = db.query(f"SELECT {', '.join(cols)} FROM {name}_def")
        df = _coerce_year_column(df)
    else:                                                       # build overlay here
        df = _reconstruct_default_overlay(db, name, keep_missing=keep_missing)

    if apply_filters:                                           # optional subset
        for col, allowed in apply_filters.items():
            if col not in df.columns:
                continue
            # Coerce filter values to match the column's dtype so that
            # {"y": ["2025"]} works as well as {"y": [2025]}. Years are
            # stored as TEXT in NEMO but get coerced to Int64 by the reader;
            # without this step, str filters silently return zero rows.
            target_dtype = df[col].dtype
            try:
                allowed_coerced = pd.Series(list(allowed)).astype(target_dtype).tolist()
            except (TypeError, ValueError):
                allowed_coerced = list(allowed)
            df = df[df[col].isin(allowed_coerced)]
    return df.reset_index(drop=True)


def _reconstruct_default_overlay(
    db: NemoDB,
    name: str,
    keep_missing: bool = False,
) -> pd.DataFrame:
    """Reproduce what NEMO's `<n>_def` view would contain.

    Strategy: load the Cartesian product of the dimension members, left-join
    the sparse parameter rows, then fill missing values with the default
    from DefaultParams (if any). When no default is registered and
    ``keep_missing`` is False, missing combinations are dropped, matching
    NEMO's own convention. When True, NaN is retained so the caller can
    build a full-shape DataArray.

    Parameters with a non-``val`` value column (only
    ``TransmissionModelingEnabled.type`` at present) are handled here too,
    because NEMO does not build a `_def` view for them.
    """
    p: Parameter = PARAMETERS[name]                             # metadata
    value_col = p.value_col                                     # 'val' or 'type'
    # Only look up DefaultParams when the value column is 'val'; DefaultParams
    # stores numeric defaults keyed on parameter name.
    default = db.default_for(name) if value_col == "val" else None

    # Cartesian product of dimension members.
    dim_frames: List[pd.DataFrame] = []                         # list to cross-join
    for dim_abbr in p.dims:                                     # iterate dim abbrs
        dim_table = DIMENSION_ABBREVIATIONS.get(dim_abbr, dim_abbr)
        pk_col = DIMENSIONS[dim_table].pk if dim_table in DIMENSIONS else "val"
        values = db.query(f"SELECT {pk_col} AS {dim_abbr} FROM {dim_table}")
        if values.empty:                                        # empty dim -> empty grid
            return pd.DataFrame(columns=list(p.dims) + [value_col])
        dim_frames.append(values)

    grid = reduce(lambda a, b: a.merge(b, how="cross"), dim_frames)

    # Attach stored values.
    stored = get_parameter_raw(db, name)                        # sparse table

    # Align dtypes on every merge key; otherwise pandas refuses the merge
    # when one side comes from SQLite as TEXT and the other was coerced
    # (notably `y`, which we always cast to Int64).
    for col in p.dims:
        if col in grid.columns and col in stored.columns:
            if grid[col].dtype != stored[col].dtype:
                try:
                    grid[col] = grid[col].astype(stored[col].dtype)
                except (TypeError, ValueError):
                    grid[col] = grid[col].astype(str)
                    stored[col] = stored[col].astype(str)

    merged = grid.merge(stored, on=list(p.dims), how="left")    # left-join

    if default is not None:                                     # overlay default
        merged[value_col] = merged[value_col].fillna(default)
    elif not keep_missing:                                      # drop absent rows
        merged = merged.dropna(subset=[value_col])
    # else: retain NaN rows for the full grid.

    return _coerce_year_column(merged).reset_index(drop=True)


def list_populated_parameters(db: NemoDB) -> pd.DataFrame:
    """Report which known parameter tables have any rows. Useful when
    a LEAP area ships a large schema but the scenario only uses a subset."""
    present = set(db.list_tables())                             # what exists
    rows = []                                                   # accumulator
    for name in PARAMETERS:                                     # iterate known
        if name not in present:                                 # skip absent
            rows.append({"parameter": name, "present": False, "rows": 0,
                         "default": db.default_for(name)})
            continue
        n = db.row_count(name)                                  # count rows
        rows.append({"parameter": name, "present": True, "rows": n,
                     "default": db.default_for(name)})
    return pd.DataFrame(rows).sort_values("parameter").reset_index(drop=True)
