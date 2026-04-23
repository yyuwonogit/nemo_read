"""
Export helpers: cast any parameter or result into an xarray DataArray,
or dump a whole scenario to a directory of CSVs / one parquet file.

xarray is the natural shape for NEMO data: every table is effectively a
sparse labelled tensor over (r, t, f, m, y, l, ...). Converting to xarray
unlocks trivial slicing, arithmetic, and plotting.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr

from .db import NemoDB
from .parameters import get_parameter, get_parameter_raw, list_populated_parameters
from .variables import get_result, list_present_results
from .dimensions import (
    emissions, fuels, modes_of_operation, nodes, regions,
    storages, technologies, years,
)
from .schema import DIMENSIONS, DIMENSION_ABBREVIATIONS, PARAMETERS, RESULT_VARIABLES


# --------------------------------------------------------------------------
# DataFrame → xarray.DataArray
# --------------------------------------------------------------------------
def to_dataarray(
    df: pd.DataFrame,
    dims: Sequence[str],
    value_col: str = "val",
    name: Optional[str] = None,
    fill_value: float = 0.0,
) -> xr.DataArray:
    """Pivot a long DataFrame into a dense labelled DataArray.

    Missing combinations are filled with `fill_value`. For sparse
    parameters this is usually 0.0; for result variables where absence
    means "not computed", pass `fill_value=np.nan` to preserve the
    distinction.
    """
    missing_dims = [d for d in dims if d not in df.columns]     # schema check
    if missing_dims:
        raise KeyError(f"DataFrame missing expected dimensions: {missing_dims}")
    if value_col not in df.columns:
        raise KeyError(f"Value column {value_col!r} not in DataFrame.")

    # Drop rows with NaN in any dim label — those cannot be indexed.
    df = df.dropna(subset=list(dims))

    # Use pandas MultiIndex -> xarray.
    indexed = df.set_index(list(dims))[value_col]
    # If the same dim combo appears multiple times (e.g. multiple solvedtm
    # sneaking through), collapse to the last entry and warn the caller.
    if indexed.index.duplicated().any():
        indexed = indexed[~indexed.index.duplicated(keep="last")]
    da = indexed.to_xarray()                                    # dense cube
    if fill_value is not None:
        da = da.fillna(fill_value)
    if name is not None:
        da.name = name
    return da


def parameter_to_dataarray(
    db: NemoDB,
    name: str,
    with_defaults: bool = True,
    fill_value: float = 0.0,
) -> xr.DataArray:
    """Fetch a parameter and return it as a DataArray.

    The resulting cube spans every member of every dimension of the
    parameter. Missing combinations are filled with ``fill_value`` (0 by
    default); when a parameter has no registered default, ``keep_missing``
    is passed through so the library fills NaN for absent rows instead of
    dropping them, which would silently shrink the cube's shape."""
    p = PARAMETERS[name]                                        # metadata
    df = get_parameter(db, name, with_defaults=with_defaults, keep_missing=True)
    return to_dataarray(df, dims=p.dims, value_col=p.value_col,
                        name=name, fill_value=fill_value)


def result_to_dataarray(
    db: NemoDB,
    name: str,
    solvedtm: Optional[str] = None,
    fill_value: float = np.nan,
) -> xr.DataArray:
    """Fetch a result variable and return it as a DataArray.
    Defaults to NaN fill because absence of a result row means that
    combination was not part of the saved output."""
    df = get_result(db, name, solvedtm=solvedtm)
    meta = RESULT_VARIABLES.get(name)
    dims = meta.dims if meta is not None else tuple(
        c for c in db.table_columns(name) if c not in ("val", "solvedtm")
    )
    return to_dataarray(df, dims=dims, value_col="val",
                        name=name, fill_value=fill_value)


# --------------------------------------------------------------------------
# Full scenario dump
# --------------------------------------------------------------------------
_INCLUDE_PRESETS = frozenset({"all", "dimensions", "parameters", "results"})


def _resolve_include(
    db: NemoDB,
    include: Union[str, Iterable[str]],
) -> Tuple[set, set, set]:
    """Return three sets of table names: dimensions, parameters, results.

    ``include`` can be one of the presets ("all", "dimensions", "parameters",
    "results") or any iterable of specific table names to restrict output
    to just those tables.
    """
    if isinstance(include, str):
        if include not in _INCLUDE_PRESETS:
            raise ValueError(
                f"include must be one of {sorted(_INCLUDE_PRESETS)} or a "
                f"list of table names; got {include!r}"
            )
        want_dims = include in ("all", "dimensions")
        want_params = include in ("all", "parameters")
        want_results = include in ("all", "results")
        dim_names = set(DIMENSIONS) if want_dims else set()
        par_names = set(PARAMETERS) if want_params else set()
        res_names = set(db.list_result_tables()) if want_results else set()
    else:
        requested = set(include)
        dim_names = requested & set(DIMENSIONS)
        par_names = requested & set(PARAMETERS)
        res_names = requested & set(db.list_result_tables())
        unknown = requested - dim_names - par_names - res_names
        if unknown:
            raise KeyError(
                f"Unknown table name(s) in include: {sorted(unknown)}"
            )
    return dim_names, par_names, res_names


def dump_to_csv(
    db: NemoDB,
    out_dir: Union[str, Path],
    include: Union[str, Iterable[str]] = "all",
    with_defaults: bool = False,
) -> Dict[str, Path]:
    """Write scenario tables to CSV files in ``out_dir``.

    Parameters
    ----------
    db : NemoDB
    out_dir : str or Path
        Destination directory. Created if missing.
    include : str or iterable of str, default 'all'
        One of the presets ``'all'``, ``'dimensions'``, ``'parameters'``,
        ``'results'``, or an iterable of specific table names (e.g.
        ``['REGION', 'CapitalCost', 'vnewcapacity']``) for targeted export.
    with_defaults : bool, default False
        Keeps parameters sparse (what NEMO stores) when False; switch to
        True to materialise the default-overlaid view.

    Returns
    -------
    dict
        Mapping ``table_name → output path`` for every file written.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    written: Dict[str, Path] = {}

    dim_names, par_names, res_names = _resolve_include(db, include)
    all_tables = set(db.list_tables())

    for name in sorted(dim_names):
        if name in all_tables:
            df = db.query(f"SELECT * FROM {name}")
            path = out_path / f"dim_{name}.csv"
            df.to_csv(path, index=False)
            written[name] = path

    for name in sorted(par_names):
        if name not in all_tables:
            continue
        df = (get_parameter(db, name) if with_defaults
              else get_parameter_raw(db, name))
        path = out_path / f"par_{name}.csv"
        df.to_csv(path, index=False)
        written[name] = path

    for name in sorted(res_names):
        df = get_result(db, name)
        path = out_path / f"res_{name}.csv"
        df.to_csv(path, index=False)
        written[name] = path

    return written


def dump_to_parquet(
    db: NemoDB,
    out_path: Union[str, Path],
    include: Union[str, Iterable[str]] = "all",
    with_defaults: bool = False,
) -> Path:
    """Write a selection of tables into a single Parquet file.

    Every row carries ``__table__`` and ``__kind__`` columns so callers
    can partition the result by table downstream. Requires ``pyarrow``
    or ``fastparquet``.

    ``include`` accepts the same presets and table-name iterables as
    :func:`dump_to_csv`.
    """
    out = Path(out_path)
    frames: List[pd.DataFrame] = []

    dim_names, par_names, res_names = _resolve_include(db, include)
    all_tables = set(db.list_tables())

    for name in sorted(dim_names):
        if name in all_tables:
            df = db.query(f"SELECT * FROM {name}").assign(
                __table__=name, __kind__="dimension"
            )
            frames.append(df)

    for name in sorted(par_names):
        if name not in all_tables:
            continue
        df = (get_parameter(db, name) if with_defaults
              else get_parameter_raw(db, name))
        frames.append(df.assign(__table__=name, __kind__="parameter"))

    for name in sorted(res_names):
        df = get_result(db, name).assign(__table__=name, __kind__="result")
        frames.append(df)

    if not frames:
        raise ValueError(
            "No tables selected to dump. Check your include specifier."
        )

    big = pd.concat(frames, ignore_index=True)
    big.to_parquet(out, index=False)
    return out
