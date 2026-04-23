"""
Readers for NEMO dimension (set) tables.

Each dimension has a small schema; we expose a uniform `get_dimension()`
plus typed convenience methods for the common ones. All return pandas
DataFrames; casting YEAR to integer is done here because NEMO stores
year labels as TEXT even though they are used numerically throughout.
"""

from __future__ import annotations
from typing import List, Optional

import pandas as pd

from .db import NemoDB
from .schema import DIMENSIONS


def get_dimension(db: NemoDB, name: str) -> pd.DataFrame:
    """Return a dimension table as-is.

    Parameters
    ----------
    db : NemoDB
        Open database handle.
    name : str
        Dimension table name. Case matches NEMO (e.g. 'TECHNOLOGY').
    """
    if name not in DIMENSIONS:                                  # guard unknown names
        raise KeyError(f"{name!r} is not a known NEMO dimension.")
    return db.query(f"SELECT * FROM {name}")                    # simple dump


def regions(db: NemoDB) -> pd.DataFrame:
    """REGION dimension with val + desc."""
    return get_dimension(db, "REGION")


def fuels(db: NemoDB) -> pd.DataFrame:
    """FUEL dimension."""
    return get_dimension(db, "FUEL")


def technologies(db: NemoDB) -> pd.DataFrame:
    """TECHNOLOGY dimension."""
    return get_dimension(db, "TECHNOLOGY")


def emissions(db: NemoDB) -> pd.DataFrame:
    """EMISSION dimension."""
    return get_dimension(db, "EMISSION")


def storages(db: NemoDB) -> pd.DataFrame:
    """STORAGE dimension, including netzero* flags."""
    return get_dimension(db, "STORAGE")


def modes_of_operation(db: NemoDB) -> pd.DataFrame:
    """MODE_OF_OPERATION dimension."""
    return get_dimension(db, "MODE_OF_OPERATION")


def years(db: NemoDB, as_int: bool = True) -> pd.DataFrame:
    """YEAR dimension. Values are stored as TEXT in NEMO; when `as_int`
    is True (default) they are cast to int64 for arithmetic use."""
    df = get_dimension(db, "YEAR")                              # raw fetch
    if as_int:                                                  # cast if asked
        df["val"] = pd.to_numeric(df["val"], errors="coerce").astype("Int64")
    return df.sort_values("val").reset_index(drop=True)         # ordered output


def timeslices(db: NemoDB) -> pd.DataFrame:
    """TIMESLICE dimension joined with its TSGROUP1/TSGROUP2 membership.

    Returns columns: l, desc, tg1, tg2, lorder, tg1_order, tg2_order.

    Rows are ordered chronologically by ``(tg1_order, tg2_order, lorder)``.
    The composite key matters because ``lorder`` is only unique within a
    ``(tg1, tg2)`` group, not globally. A naive sort by ``lorder`` alone
    would interleave seasons (e.g. Wet-Hr1, Dry-Hr1, Wet-Hr2, Dry-Hr2...),
    which is wrong for chronological dispatch plots.
    """
    sql = """
    SELECT ts.val AS l,
           ts.desc,
           lts.tg1,
           lts.tg2,
           lts.lorder,
           g1."order" AS tg1_order,
           g2."order" AS tg2_order
    FROM TIMESLICE ts
    LEFT JOIN LTsGroup lts ON lts.l = ts.val
    LEFT JOIN TSGROUP1 g1 ON g1.name = lts.tg1
    LEFT JOIN TSGROUP2 g2 ON g2.name = lts.tg2
    ORDER BY g1."order", g2."order", lts.lorder
    """
    return db.query(sql)


def timeslice_groups(db: NemoDB) -> pd.DataFrame:
    """Return TSGROUP1 and TSGROUP2 stacked with a `level` column."""
    g1 = db.query("SELECT 'tg1' AS level, name, desc, \"order\" AS grp_order, multiplier FROM TSGROUP1")
    g2 = db.query("SELECT 'tg2' AS level, name, desc, \"order\" AS grp_order, multiplier FROM TSGROUP2")
    return pd.concat([g1, g2], ignore_index=True)


def nodes(db: NemoDB) -> pd.DataFrame:
    """NODE dimension: val, desc, r (region assignment)."""
    return get_dimension(db, "NODE")


def transmission_lines(db: NemoDB) -> pd.DataFrame:
    """TransmissionLine: hybrid dimension/parameter. Contains line IDs,
    endpoints, and exogenous cost/efficiency parameters."""
    return db.query("SELECT * FROM TransmissionLine")


def transmission_candidates(db: NemoDB) -> pd.DataFrame:
    """Return only the candidate (not-yet-built) transmission lines.

    A line is considered a candidate when its ``yconstruction`` exceeds
    the earliest modelled year in ``YEAR``. NEMO treats these as
    investment decisions the optimiser may take, subject to MIP/continuous
    transmission settings in the configuration file. Existing lines
    (``yconstruction`` at or before the first modelled year) are assumed
    to be already operational.

    Note the cutoff uses ``min(YEAR)``, not ``max(YEAR)``; candidate
    lines can have a construction year anywhere inside or beyond the
    model horizon.
    """
    first_year = db.query(
        "SELECT MIN(CAST(val AS INTEGER)) AS m FROM YEAR"
    )["m"].iloc[0]
    if first_year is None:
        return db.query("SELECT * FROM TransmissionLine WHERE 1 = 0")
    return db.query(
        "SELECT * FROM TransmissionLine WHERE yconstruction > ?",
        (int(first_year),),
    )


def list_unused_technologies(db: NemoDB) -> pd.DataFrame:
    """Return technologies declared in TECHNOLOGY but never referenced by
    any parameter table.

    NEMO's behaviour: "NEMO will not simulate activity for a (r, t, m, y)
    unless you define a corresponding non-zero ``OutputActivityRatio`` or
    ``InputActivityRatio``." Unreferenced technologies therefore stay
    dormant in the optimisation and contribute nothing. They're usually
    harmless but signal that the LEAP area carries more technology branches
    than the scenario actually uses, which can be worth trimming.

    Technologies referenced only by ``__NEMOcc`` constraint tables via
    their ``bid`` field are still flagged here, because the numeric ``bid``
    does not resolve to a technology ID without external (LEAP area) data.
    """
    from .schema import PARAMETERS

    all_techs = set(db.query("SELECT val FROM TECHNOLOGY")["val"])
    referenced: set = set()

    tables_present = set(db.list_tables())
    for pname, meta in PARAMETERS.items():
        if pname not in tables_present:
            continue
        if "t" not in meta.dims:
            continue
        vals = db.query(f'SELECT DISTINCT "t" FROM "{pname}"')["t"]
        referenced.update(v for v in vals if v is not None)

    unused = sorted(all_techs - referenced)
    if not unused:
        return pd.DataFrame(columns=["val", "desc"])
    placeholders = ",".join(["?"] * len(unused))
    return db.query(
        f"SELECT val, desc FROM TECHNOLOGY WHERE val IN ({placeholders}) ORDER BY val",
        unused,
    )


def region_groups(db: NemoDB) -> pd.DataFrame:
    """REGIONGROUP joined with RRGroup membership: columns rg, desc, r."""
    sql = """
    SELECT rg.val AS rg, rg.desc, rrg.r
    FROM REGIONGROUP rg
    LEFT JOIN RRGroup rrg ON rrg.rg = rg.val
    """
    return db.query(sql)
