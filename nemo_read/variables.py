"""
Readers for NEMO output (result) tables.

Result tables are named with a leading `v`. Each has its dimension columns,
a `val` column, and a `solvedtm` timestamp. NEMO appends rows on each
successful calculation without clearing old ones, so consumers usually
want to pin to one solved timestamp at a time.

Helpers here handle:
    * listing what results are actually present in the DB,
    * filtering to the latest solve,
    * converting year columns to Int64,
    * joining across related variables for common comparisons.
"""

from __future__ import annotations
from typing import Iterable, List, Mapping, Optional, Sequence

import pandas as pd

from .db import NemoDB
from .schema import RESULT_VARIABLES


def list_present_results(db: NemoDB) -> pd.DataFrame:
    """Every `v*` table actually stored, with row count and solve timestamps."""
    cols = ["variable", "known", "rows", "n_solves", "latest_solve", "dims"]
    rows = []                                                   # accumulator
    for t in db.list_result_tables():                           # discovery
        n = db.row_count(t)                                     # rowcount
        try:                                                    # solvedtm may be absent
            tms = db.solvedtm_values(t)
        except Exception:                                       # swallow oddities
            tms = []
        known = RESULT_VARIABLES.get(t)                         # metadata lookup
        rows.append({
            "variable": t,
            "known": known is not None,
            "rows": n,
            "n_solves": len(tms),
            "latest_solve": tms[-1] if tms else None,
            "dims": ",".join(known.dims) if known else "",
        })
    if not rows:                                                # no v* tables saved
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows).sort_values("variable").reset_index(drop=True)


def get_result(
    db: NemoDB,
    name: str,
    solvedtm: Optional[str] = None,
    latest: bool = True,
    filters: Optional[Mapping[str, Sequence]] = None,
) -> pd.DataFrame:
    """Fetch a result variable table.

    Parameters
    ----------
    db : NemoDB
    name : str
        Result variable table name, e.g. 'vnewcapacity'.
    solvedtm : str, optional
        If given, restrict to this solve timestamp.
    latest : bool, default True
        If `solvedtm` is None and this table has been solved multiple
        times, return rows from the most recent `solvedtm` only.
    filters : dict, optional
        Column → iterable of allowed values, applied after fetch.
    """
    tables = db.list_tables()                                   # present tables
    if name not in tables:                                      # guard missing
        raise KeyError(f"Result table {name!r} not present. "
                       f"Check list_present_results() for what is saved.")

    cols = db.table_columns(name)                               # discover columns
    select_cols = ", ".join(cols)                               # SQL projection
    params: List = []                                           # bind values
    where = ""                                                  # WHERE clause

    if "solvedtm" in cols:                                      # only filter if exists
        if solvedtm is not None:                                # explicit pin
            where = "WHERE solvedtm = ?"
            params.append(solvedtm)
        elif latest:                                            # most recent solve
            latest_tm = _latest_solvedtm(db, name)
            if latest_tm is not None:
                where = "WHERE solvedtm = ?"
                params.append(latest_tm)

    sql = f"SELECT {select_cols} FROM {name} {where}".strip()   # assemble query
    df = db.query(sql, params)                                  # execute

    if "y" in df.columns:                                       # cast year
        df["y"] = pd.to_numeric(df["y"], errors="coerce").astype("Int64")

    if filters:                                                 # optional subset
        for col, allowed in filters.items():
            if col in df.columns:
                df = df[df[col].isin(list(allowed))]

    return df.reset_index(drop=True)


def _latest_solvedtm(db: NemoDB, table: str) -> Optional[str]:
    """Return the largest (lexicographic) `solvedtm` for `table`."""
    df = db.query(f"SELECT MAX(solvedtm) AS tm FROM {table}")   # simple MAX
    if df.empty or pd.isna(df["tm"].iloc[0]):                   # empty result
        return None
    return str(df["tm"].iloc[0])                                # as string


def capacity_stack(db: NemoDB, solvedtm: Optional[str] = None) -> pd.DataFrame:
    """Return total capacity + new builds + residual in one long frame.

    Columns: r, t, y, kind ∈ {total, new, accumulated_new}, val.
    Useful for stacked-area plots and audit of capacity evolution.
    """
    frames = []                                                 # collect pieces

    spec = [                                                    # (table, kind label)
        ("vtotalcapacityannual",       "total"),
        ("vnewcapacity",               "new"),
        ("vaccumulatednewcapacity",    "accumulated_new"),
    ]
    for table, kind in spec:                                    # iterate
        if table in db.list_tables():                           # only if saved
            df = get_result(db, table, solvedtm=solvedtm)[["r","t","y","val"]]
            df["kind"] = kind                                   # tag
            frames.append(df)
    if not frames:                                              # nothing saved
        return pd.DataFrame(columns=["r","t","y","kind","val"])
    return pd.concat(frames, ignore_index=True)


def energy_balance(
    db: NemoDB,
    region: Optional[str] = None,
    year: Optional[int] = None,
    solvedtm: Optional[str] = None,
) -> pd.DataFrame:
    """Annual energy balance: production, use, trade, and demand by fuel.

    Signs are kept as NEMO stores them (all non-negative) and an explicit
    `component` column labels each contribution. Build a net by subtracting
    use + export from production + import + demand.
    """
    frames = []                                                 # pieces

    mapping = [                                                 # (table, component label)
        ("vproductionannualnn",   "production_nn"),
        ("vproductionannualnodal","production_nodal"),
        ("vuseannualnn",          "use_nn"),
        ("vuseannualnodal",       "use_nodal"),
        ("vdemandannualnn",       "demand_nn"),
        ("vtradeannual",          "trade"),
    ]
    for table, comp in mapping:                                 # iterate candidates
        if table not in db.list_tables():                       # skip if absent
            continue
        df = get_result(db, table, solvedtm=solvedtm)           # fetch
        df["component"] = comp                                  # tag

        # Normalise "node" results up to region via NODE.r
        if "n" in df.columns:                                   # nodal case
            node_r = db.query("SELECT val AS n, r FROM NODE")
            df = df.merge(node_r, on="n", how="left")           # map n -> r

        frames.append(df)                                       # accumulate

    if not frames:                                              # nothing to concat
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)                  # combine

    if region is not None:                                      # optional subset
        out = out[out.get("r", "").eq(region) | out.get("rr", "").eq(region)]
    if year is not None:
        out = out[out["y"].eq(year)]

    return out.reset_index(drop=True)
