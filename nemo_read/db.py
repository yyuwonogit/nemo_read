"""
Core connection and introspection class for a NEMO scenario database.

The database is a plain SQLite file. This module provides a thin wrapper
around `sqlite3` that layers NEMO-aware helpers on top: version checks,
table discovery, schema mismatch detection, and the uniform access point
for parameters, dimensions, and result variables.

Design choices:
    * Read-only by default (`mode=ro` via URI) to guard against accidental
      writes while LEAP has the database open.
    * Every query returns a pandas DataFrame for friction-free downstream
      use with xarray/NumPy/SciPy.
    * Default values are resolved via `_def` views if present, otherwise
      from the DefaultParams table. This matches NEMO's own internal
      convention and avoids silent zeros when a parameter was left sparse.
"""

from __future__ import annotations
import os                                           # filesystem paths
import sqlite3                                      # stdlib SQLite driver
from contextlib import contextmanager               # for `connect` context manager
from pathlib import Path                            # ergonomic path handling
from typing import Iterable, Iterator, List, Optional, Sequence, Union

import pandas as pd                                 # primary tabular return type

from .schema import (
    DIMENSIONS,
    DIMENSION_ABBREVIATIONS,
    PARAMETERS,
    RESULT_VARIABLES,
    TARGET_DB_VERSION,
)


PathLike = Union[str, os.PathLike]


class NemoDB:
    """Handle to a NEMO/LEAP scenario SQLite database.

    Parameters
    ----------
    path : str or Path
        Path to the .sqlite file. For LEAP-generated databases this is
        typically `<LEAP working dir>/<Area>/<Scenario>.sqlite` or a file
        in the LEAP settings folder. Use `LEAP.WorkingDirectory` from the
        COM API to locate it programmatically.
    read_only : bool, default True
        Open with `mode=ro`. Switch to False only when deliberately writing.
    strict_version : bool, default False
        Raise if the database's Version row does not match
        `schema.TARGET_DB_VERSION`. Keep False for tolerant exploration.
    """

    def __init__(self, path: PathLike, read_only: bool = True, strict_version: bool = False):
        self.path = Path(path).expanduser().resolve()           # absolute path
        if not self.path.exists():                              # fail fast if missing
            raise FileNotFoundError(f"No NEMO database at {self.path}")
        self.read_only = read_only                              # store flag for connect()
        self._version: Optional[int] = None                     # cached after first lookup

        with self.connect() as con:                             # open briefly to check
            self._version = self._read_version(con)             # populate cache
            if strict_version and self._version != TARGET_DB_VERSION:
                raise RuntimeError(
                    f"Database at {self.path} reports NEMO DB version "
                    f"{self._version}; this library targets v{TARGET_DB_VERSION}."
                )

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a `sqlite3.Connection`. Use as a context manager so
        connections always close even on exceptions."""
        if self.read_only:                                      # URI form for read-only
            uri = f"file:{self.path}?mode=ro"                   # SQLite URI literal
            con = sqlite3.connect(uri, uri=True)                # open via URI
        else:
            con = sqlite3.connect(self.path)                    # normal read/write
        con.row_factory = sqlite3.Row                           # dict-like row access
        try:
            yield con                                           # hand back to caller
        finally:
            con.close()                                         # always tidy up

    def query(self, sql: str, params: Sequence = ()) -> pd.DataFrame:
        """Run an arbitrary SELECT and return a DataFrame.
        Prefer the higher-level helpers; this is an escape hatch."""
        with self.connect() as con:                             # open connection
            return pd.read_sql_query(sql, con, params=list(params))  # delegate to pandas

    # ------------------------------------------------------------------
    # Version and inventory
    # ------------------------------------------------------------------
    @property
    def version(self) -> int:
        """NEMO data-dictionary version number from the `Version` table."""
        return self._version if self._version is not None else -1

    @staticmethod
    def _read_version(con: sqlite3.Connection) -> Optional[int]:
        """Look up the single row in the `Version` table if it exists."""
        cur = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='Version'"
        )
        if cur.fetchone() is None:                              # no Version table
            return None
        cur = con.execute("SELECT version FROM Version LIMIT 1")
        row = cur.fetchone()
        return int(row[0]) if row is not None else None

    def list_tables(self) -> List[str]:
        """All physical tables in the database (excluding internal sqlite_* ones)."""
        sql = ("SELECT name FROM sqlite_master WHERE type='table' "
               "AND name NOT LIKE 'sqlite_%' ORDER BY name")
        return [r[0] for r in self._rows(sql)]

    def list_views(self) -> List[str]:
        """All views. NEMO creates `_def` views for parameters with defaults."""
        sql = "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
        return [r[0] for r in self._rows(sql)]

    def list_result_tables(self) -> List[str]:
        """Return every `v*` table present: the subset of result variables
        that were requested via `varstosave` for this run."""
        return [t for t in self.list_tables() if t.startswith("v")]

    def solvedtm_values(self, result_table: str = "vtotaldiscountedcost") -> List[str]:
        """Distinct timestamps NEMO stamped onto result rows. Handy when a
        database has been calculated multiple times and results accumulated."""
        if result_table not in self.list_tables():              # guard
            raise ValueError(f"Result table {result_table!r} not present.")
        df = self.query(f"SELECT DISTINCT solvedtm FROM {result_table} ORDER BY solvedtm")
        return df["solvedtm"].astype(str).tolist()

    def table_columns(self, table: str) -> List[str]:
        """Column names in order, via PRAGMA table_info."""
        return [r[1] for r in self._rows(f"PRAGMA table_info('{table}')")]

    def row_count(self, table: str) -> int:
        """Quick SELECT COUNT(*) for a table or view."""
        return int(self._rows(f"SELECT COUNT(*) FROM {table}")[0][0])

    def summary(self) -> pd.DataFrame:
        """One-row-per-table overview: kind, expected category, row count."""
        rows = []                                               # accumulator
        for t in self.list_tables():                            # iterate tables
            kind = self._classify_table(t)                      # dimension / parameter / result / meta
            try:
                n = self.row_count(t)                           # count rows
            except sqlite3.DatabaseError:                       # table might be odd
                n = -1
            rows.append({"table": t, "kind": kind, "rows": n})
        return pd.DataFrame(rows).sort_values(["kind", "table"]).reset_index(drop=True)

    def _classify_table(self, name: str) -> str:
        """Heuristic classifier used by summary()."""
        if name in DIMENSIONS:                                  # known dimension
            return "dimension"
        if name in PARAMETERS:                                  # known parameter
            return "parameter"
        if name in RESULT_VARIABLES or name.startswith("v"):    # known or v-prefix
            return "result"
        if name in ("Version", "DefaultParams", "nodalstorage", "yearintervals"):
            return "meta"                                       # NEMO internal
        return "other"

    # ------------------------------------------------------------------
    # Default value resolution
    # ------------------------------------------------------------------
    def default_params(self) -> pd.DataFrame:
        """Return the DefaultParams table (tablename → default val)."""
        if "DefaultParams" not in self.list_tables():           # missing in some old DBs
            return pd.DataFrame(columns=["tablename", "val"])
        return self.query("SELECT tablename, val FROM DefaultParams ORDER BY tablename")

    def default_for(self, table: str) -> Optional[float]:
        """Fetch the single default scalar for `table`, or None if unset."""
        df = self.query(
            "SELECT val FROM DefaultParams WHERE tablename = ?", (table,)
        )
        if df.empty:
            return None
        return float(df["val"].iloc[0])

    def has_def_view(self, parameter: str) -> bool:
        """True if NEMO has already materialised `<parameter>_def` for us.
        LEAP/NEMO build these views during scenario calculation, so pre-run
        databases will not have them."""
        return f"{parameter}_def" in self.list_views()

    # ------------------------------------------------------------------
    # Low-level helper
    # ------------------------------------------------------------------
    def _rows(self, sql: str, params: Sequence = ()) -> List[sqlite3.Row]:
        """Execute and fetchall, used for small metadata queries."""
        with self.connect() as con:                             # transient connection
            return list(con.execute(sql, list(params)).fetchall())

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"NemoDB(path={self.path!s}, version={self.version})"
