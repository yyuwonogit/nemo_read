"""
Map a solver-reported LP column index back to its NemoMod variable identity.

Use case:
    CPLEX presolve aborts with a message like

        Infeasible column 'x435004'.

    That ``x435004`` is the 1-indexed position of a JuMP variable in the
    order NemoMod added it to the model — but the solver doesn't tell you
    which (variable_family, region, technology, year, ...) tuple it
    corresponds to. Without that, you can't see what data is forcing the
    contradiction.

    This decoder rebuilds the variable-creation sequence offline from the
    scenario SQLite alone, so the column index can be resolved without
    rerunning Julia or instrumenting NemoMod.

How the ordering works:

    * NemoMod declares variables in the order written in
      ``scenario_calculation.jl`` (lines ~490–800). Each ``@variable
      jumpmodel x[A, B, C, ...]`` produces a ``Containers.DenseAxisArray``
      whose underlying iteration is Julia's ``Iterators.product``. That
      iterator advances **column-major**: the leftmost axis varies
      fastest. So for axes ``(R, T, Y)`` and offset ``N`` (1-indexed)
      within the variable::

          y_idx = (N - 1) // (R * T)
          t_idx = ((N - 1) // R) % T
          r_idx = (N - 1) % R

    * Dimension lists come from the database via the same SQL NemoMod
      uses (``SELECT val FROM REGION`` with no ``ORDER BY`` etc.). On
      SQLite that resolves to the primary-key index order (lex by ``val``
      for TEXT PKs); Julia's ``SQLite.jl`` sees the same.

    * Some variables are conditional. ``vrateofdemandnn`` is created only
      when it appears in ``varstosave``. ``vnumberofnewtechnologyunits``
      is created only when ``CapacityOfOneTechnologyUnit`` has nonzero
      rows or ``forcemip=true``. ``calcyears`` (when set in the cfg)
      filters the YEAR list. The decoder applies these gates so the
      cumulative offsets match the actual run.

Limitations:

    * Only the **dense** prefix is decoded — variables before
      ``vrateofactivity``: ``vrateofdemandnn`` (optional), ``vdemandnn``,
      ``vdemandannualnn``, the 18 storage variables, ``vnumberofnew‐
      technologyunits`` (optional), ``vnewcapacity``,
      ``vaccumulatednewcapacity``, ``vtotalcapacityannual``. Past that,
      NemoMod uses ``keydicts_threaded`` to restrict variable indices to
      tuples that have data, which depends on runtime queries that
      aren't reproducible from SQLite alone (cardinalities differ from
      the full Cartesian product). For columns past the dense prefix the
      decoder reports the bracketing variable family and the **maximum**
      offset within it but does not decode the tuple.

    * The default ``varstosave`` is NemoMod's own (``vdemandnn,
      vnewcapacity, vtotalcapacityannual, vproductionbytechnologyannual,
      vproductionnn, vusebytechnologyannual, vusenn,
      vtotaldiscountedcost``). If the scenario's ``nemo.cfg`` adds to
      that list, pass the union via ``varstosave=...`` so the conditional
      gates evaluate correctly. Use :func:`nemo_read.read_nemo_cfg` to
      read the cfg file.

Public API:
    * :class:`ColumnIdentity` — decoded result.
    * :func:`decode_lp_column` — single-column decode.
    * :func:`enumerate_dense_blocks` — table of (variable, start, end)
      ranges; useful for sanity-checking the layout against a manual
      reconstruction.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from .db import NemoDB


# Default varstosave string in NemoMod's calculatescenario signature.
# Source: scenario_calculation.jl line 108.
NEMO_DEFAULT_VARSTOSAVE: Tuple[str, ...] = (
    "vdemandnn",
    "vnewcapacity",
    "vtotalcapacityannual",
    "vproductionbytechnologyannual",
    "vproductionnn",
    "vusebytechnologyannual",
    "vusenn",
    "vtotaldiscountedcost",
)


@dataclass
class ColumnIdentity:
    """Decoded identity for one LP column index.

    Attributes
    ----------
    column : int
        The 1-indexed column number that was decoded.
    variable : str
        The NemoMod variable family (e.g. ``'vaccumulatednewcapacity'``).
    offset : int
        1-indexed offset of the column within ``variable``.
    indices : dict
        Axis name -> dimension value (e.g. ``{'r': 'R19', 't': 'P16166',
        'y': '2025'}``). Empty when the column lands past the dense
        prefix.
    descriptions : dict
        Axis value -> human-friendly description (e.g.
        ``{'R19': 'Philippines'}``). Empty when descriptions are
        unavailable in the source DB.
    dense : bool
        True if the column was inside the dense Cartesian prefix (and
        therefore decoded). False if the column lands in the sparse
        section past ``vtotalcapacityannual``; in that case ``indices``
        is empty.
    """

    column: int
    variable: str
    offset: int
    indices: Dict[str, str] = field(default_factory=dict)
    descriptions: Dict[str, str] = field(default_factory=dict)
    dense: bool = True

    def __repr__(self) -> str:
        if not self.indices:
            return (f"<x{self.column}: in {self.variable} "
                    f"(offset {self.offset}, undecoded — sparse)>")
        idx_str = ", ".join(f"{k}={v}" for k, v in self.indices.items())
        return f"<x{self.column}: {self.variable}[{idx_str}]>"


@dataclass
class _Block:
    """Internal: one variable family in the dense prefix."""
    name: str
    axes: List[Tuple[str, List[str]]]   # ordered (axis_name, axis_values)
    start: int                          # 1-indexed first column
    end: int                            # 1-indexed last column

    @property
    def size(self) -> int:
        return self.end - self.start + 1


def _read_dimensions(db: NemoDB) -> Dict[str, List[str]]:
    """Read each dimension list in the same form NemoMod uses.

    NemoMod queries are in scenario_calculation.jl lines 413–438. None
    have an ``ORDER BY`` except YEAR, so SQLite returns them in
    primary-key index order (lex by ``val``). Julia's SQLite.jl sees the
    same order — that's the order JuMP's variable container axes will
    have, and therefore the order Iterators.product iterates.
    """
    dims: Dict[str, List[str]] = {}
    dims["y"] = [r[0] for r in db.query("SELECT val FROM YEAR ORDER BY val").itertuples(index=False, name=None)]
    dims["t"] = [r[0] for r in db.query("SELECT val FROM TECHNOLOGY").itertuples(index=False, name=None)]
    dims["l"] = [r[0] for r in db.query("SELECT val FROM TIMESLICE").itertuples(index=False, name=None)]
    dims["f"] = [r[0] for r in db.query("SELECT val FROM FUEL").itertuples(index=False, name=None)]
    dims["e"] = [r[0] for r in db.query("SELECT val FROM EMISSION").itertuples(index=False, name=None)]
    dims["m"] = [r[0] for r in db.query("SELECT val FROM MODE_OF_OPERATION").itertuples(index=False, name=None)]
    dims["r"] = [r[0] for r in db.query("SELECT val FROM REGION").itertuples(index=False, name=None)]
    dims["s"] = [r[0] for r in db.query("SELECT val FROM STORAGE").itertuples(index=False, name=None)]
    dims["tg1"] = [r[0] for r in db.query("SELECT name FROM TSGROUP1").itertuples(index=False, name=None)]
    dims["tg2"] = [r[0] for r in db.query("SELECT name FROM TSGROUP2").itertuples(index=False, name=None)]
    return dims


def _vnumberofnewtechnologyunits_needed(
    db: NemoDB, varstosave: Sequence[str], forcemip: bool,
) -> bool:
    """Mirror scenario_calculation.jl line 551.

    Variable is created if any of:
        - ``vnumberofnewtechnologyunits`` is in varstosave
        - ``CapacityOfOneTechnologyUnit`` has at least one nonzero row
        - forcemip is true
    """
    if "vnumberofnewtechnologyunits" in varstosave:
        return True
    if forcemip:
        return True
    tables = set(db.list_tables())
    name = "CapacityOfOneTechnologyUnit_def"
    if name not in tables:
        name = "CapacityOfOneTechnologyUnit"
        if name not in tables:
            return False
    df = db.query(f'SELECT COUNT(*) AS n FROM "{name}" WHERE val <> 0')
    return int(df["n"].iloc[0]) > 0


def _build_dense_blocks(
    db: NemoDB,
    varstosave: Sequence[str],
    calcyears: Optional[Sequence[str]],
    forcemip: bool,
) -> List[_Block]:
    """Build the ordered list of dense-prefix variable families with
    their column ranges, applying all conditional gates from
    scenario_calculation.jl."""
    dims = _read_dimensions(db)
    if calcyears is not None:
        # Filter the YEAR axis to just the calcyears (preserving order).
        wanted = {str(y) for y in calcyears}
        dims["y"] = [y for y in dims["y"] if y in wanted]

    r, t, f, s, l_, m, y = (dims["r"], dims["t"], dims["f"], dims["s"],
                            dims["l"], dims["m"], dims["y"])
    tg1, tg2 = dims["tg1"], dims["tg2"]

    # axis-list builders (so we don't accidentally share references)
    def ax(*names: str) -> List[Tuple[str, List[str]]]:
        return [(n, dims[n][:]) for n in names]

    blocks: List[Tuple[str, List[Tuple[str, List[str]]]]] = []

    # vrateofdemandnn — only if user asked for it
    if "vrateofdemandnn" in varstosave:
        blocks.append(("vrateofdemandnn", ax("r", "l", "f", "y")))

    # always-on demand vars
    blocks.append(("vdemandnn", ax("r", "l", "f", "y")))
    blocks.append(("vdemandannualnn", ax("r", "f", "y")))

    # 18 storage variables, all full-Cartesian, no conditionals
    blocks.append(("vstorageleveltsgroup1startnn",        ax("r", "s", "tg1", "y")))
    blocks.append(("vstorageleveltsgroup1endnn",          ax("r", "s", "tg1", "y")))
    blocks.append(("vstorageleveltsgroup2startnn",        ax("r", "s", "tg1", "tg2", "y")))
    blocks.append(("vstorageleveltsgroup2endnn",          ax("r", "s", "tg1", "tg2", "y")))
    blocks.append(("vstorageleveltsendnn",                ax("r", "s", "l", "y")))
    blocks.append(("vstoragelevelyearendnn",              ax("r", "s", "y")))
    blocks.append(("vrateofstoragechargenn",              ax("r", "s", "l", "y")))
    blocks.append(("vrateofstoragedischargenn",           ax("r", "s", "l", "y")))
    blocks.append(("vstoragelowerlimit",                  ax("r", "s", "y")))
    blocks.append(("vstorageupperlimit",                  ax("r", "s", "y")))
    blocks.append(("vaccumulatednewstoragecapacity",      ax("r", "s", "y")))
    blocks.append(("vnewstoragecapacity",                 ax("r", "s", "y")))
    blocks.append(("vfinancecoststorage",                 ax("r", "s", "y")))
    blocks.append(("vcapitalinvestmentstorage",           ax("r", "s", "y")))
    blocks.append(("vdiscountedcapitalinvestmentstorage", ax("r", "s", "y")))
    blocks.append(("vsalvagevaluestorage",                ax("r", "s", "y")))
    blocks.append(("vdiscountedsalvagevaluestorage",      ax("r", "s", "y")))
    blocks.append(("vtotaldiscountedstoragecost",         ax("r", "s", "y")))

    # vnumberofnewtechnologyunits — conditional
    if _vnumberofnewtechnologyunits_needed(db, varstosave, forcemip):
        blocks.append(("vnumberofnewtechnologyunits", ax("r", "t", "y")))

    # always-on capacity vars
    blocks.append(("vnewcapacity",              ax("r", "t", "y")))
    blocks.append(("vaccumulatednewcapacity",   ax("r", "t", "y")))
    blocks.append(("vtotalcapacityannual",      ax("r", "t", "y")))

    # Compute cumulative column ranges
    out: List[_Block] = []
    cum = 0
    for name, axes in blocks:
        size = 1
        for _, vals in axes:
            size *= len(vals)
        out.append(_Block(name=name, axes=axes,
                          start=cum + 1, end=cum + size))
        cum += size
    return out


def _decode_offset(
    block: _Block, offset_1: int,
    db: Optional[NemoDB] = None,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Convert a 1-indexed in-block offset to its axis-tuple, applying
    Julia's column-major (leftmost-fastest) ordering.

    Returns ``(indices, descriptions)``. Descriptions are populated for
    axes with a known ``desc`` column in the source DB (REGION,
    TECHNOLOGY, FUEL, EMISSION, STORAGE).
    """
    indices: Dict[str, str] = {}
    idx0 = offset_1 - 1
    for ax_name, vals in block.axes:
        n = len(vals)
        indices[ax_name] = vals[idx0 % n]
        idx0 //= n

    # Best-effort descriptions from the dimension tables that have them.
    descriptions: Dict[str, str] = {}
    if db is not None:
        _DESC_TABLES = {
            "r": "REGION", "t": "TECHNOLOGY", "f": "FUEL",
            "e": "EMISSION", "s": "STORAGE",
        }
        for ax_name, val in indices.items():
            tbl = _DESC_TABLES.get(ax_name)
            if not tbl:
                continue
            try:
                df = db.query(
                    f'SELECT desc FROM "{tbl}" WHERE val = ?', (val,)
                )
                if not df.empty:
                    descriptions[val] = str(df["desc"].iloc[0])
            except Exception:
                # tables without a desc column are fine — skip silently
                pass
    return indices, descriptions


def decode_lp_column(
    db: NemoDB,
    column: int,
    *,
    varstosave: Optional[Sequence[str]] = None,
    calcyears: Optional[Sequence[str]] = None,
    forcemip: bool = False,
) -> ColumnIdentity:
    """Decode a CPLEX/LP ``xN`` column index back to its NemoMod variable.

    Parameters
    ----------
    db : NemoDB
        Connection to the same scenario SQLite that was being solved.
    column : int
        1-indexed column number to decode (the ``N`` in ``xN`` from a
        solver message). Must be ≥ 1.
    varstosave : sequence of str, optional
        The full list of variables NemoMod was told to save for the run.
        Defaults to NemoMod's own default. If your ``nemo.cfg`` adds to
        the list, pass the *union* of the cfg's ``varstosave`` and
        :data:`NEMO_DEFAULT_VARSTOSAVE` so the conditional gates evaluate
        correctly.
    calcyears : sequence of str, optional
        If the run had ``calcyears`` set in the cfg, pass them as strings
        (e.g. ``['2025', '2030']``). When omitted, all rows in the YEAR
        table are used (NemoMod's default).
    forcemip : bool, default False
        Mirror the ``forcemip`` arg from ``calculatescenario``. When
        True, ``vnumberofnewtechnologyunits`` is created unconditionally
        and the column offsets shift accordingly.

    Returns
    -------
    ColumnIdentity
        Decoded result. If the column lands past the dense prefix, the
        ``dense`` flag is False, ``indices`` is empty, and ``offset`` is
        the column's offset relative to the end of the dense prefix.

    Examples
    --------
    >>> db = NemoDB("scenario.sqlite")
    >>> id_ = decode_lp_column(db, 435004)
    >>> id_.variable
    'vaccumulatednewcapacity'
    >>> id_.indices
    {'r': 'R19', 't': 'P16166', 'y': '2025'}
    """
    if column < 1:
        raise ValueError(f"column must be >= 1, got {column}")

    if varstosave is None:
        varstosave = list(NEMO_DEFAULT_VARSTOSAVE)
    else:
        varstosave = list(varstosave)

    blocks = _build_dense_blocks(db, varstosave, calcyears, forcemip)
    last_dense_col = blocks[-1].end if blocks else 0

    if column > last_dense_col:
        return ColumnIdentity(
            column=column,
            variable="(past dense prefix; sparse vars not decoded)",
            offset=column - last_dense_col,
            dense=False,
        )

    for blk in blocks:
        if blk.start <= column <= blk.end:
            offset_1 = column - blk.start + 1
            indices, descriptions = _decode_offset(blk, offset_1, db)
            return ColumnIdentity(
                column=column,
                variable=blk.name,
                offset=offset_1,
                indices=indices,
                descriptions=descriptions,
                dense=True,
            )

    # Should be unreachable
    raise RuntimeError(
        f"column {column} did not match any dense block — internal error"
    )


def enumerate_dense_blocks(
    db: NemoDB,
    *,
    varstosave: Optional[Sequence[str]] = None,
    calcyears: Optional[Sequence[str]] = None,
    forcemip: bool = False,
) -> "pd.DataFrame":
    """Return a DataFrame of the dense-prefix layout: one row per
    variable family with ``start`` / ``end`` column ranges and ``size``.
    Useful for sanity-checking offsets against a hand reconstruction.
    """
    import pandas as pd
    if varstosave is None:
        varstosave = list(NEMO_DEFAULT_VARSTOSAVE)
    blocks = _build_dense_blocks(db, list(varstosave), calcyears, forcemip)
    rows = []
    for blk in blocks:
        rows.append({
            "variable": blk.name,
            "axes": ", ".join(n for n, _ in blk.axes),
            "size": blk.size,
            "start": blk.start,
            "end": blk.end,
        })
    return pd.DataFrame(rows)
