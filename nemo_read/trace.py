"""
Result-side traceback (0.6.1).

Given a value in a NEMO result variable table (``v*``), explain where it came
from:

- :func:`trace_result` — for a specific ``(table, row)`` pair, walk
  :data:`nemo_read.schema.RESULT_DEPENDENCIES` to list contributing input
  parameters and upstream result variables, each with a LEAP UI hint when a
  :class:`~nemo_read.leap_area.LeapAreaContext` is supplied. Also detects
  whether the row's value is binding against an upper or lower bound.

- :func:`trace_cost` — decompose ``vtotaldiscountedcost`` for a given
  ``(region, year)`` into the individual cost streams that add up to it.

These helpers don't run any solver — they use only values already in the
SQLite, plus the ancestry encoded in :data:`RESULT_DEPENDENCIES`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .db import NemoDB
from .schema import PARAMETERS, RESULT_DEPENDENCIES, ResultDependency

# Tolerance when comparing an actual value against a bound to call it binding.
_BIND_REL_TOL = 1e-6
_BIND_ABS_TOL = 1e-9


#: Bound states recognised by :func:`trace_result`.
BOUND_FREE = "freely_optimized"
BOUND_HIT_UPPER = "hit_upper_bound"
BOUND_HIT_LOWER = "floored_at_lower_bound"
BOUND_ABSENT = "no_bound_defined"
BOUND_UNKNOWN = "unknown"


@dataclass
class InputTrace:
    """One input contributing to a result row."""
    parameter: str
    row_value: float | None               # parameter value for the matching key tuple
    leap_ui_hint: str | None = None       # from where_in_leap, if context supplied
    confidence: str | None = None


@dataclass
class BoundCheck:
    """Whether a result row's value is binding against one of its bounds."""
    state: str                            # BOUND_* constant
    bound_table: str | None = None        # parameter table that holds the active bound
    bound_value: float | None = None
    actual_value: float | None = None
    note: str = ""


@dataclass
class ResultTrace:
    """Full traceback for a single result row."""
    table: str
    row: dict
    value: float | None
    dependency: ResultDependency | None
    contributing_inputs: list[InputTrace] = field(default_factory=list)
    upstream_results: list[str] = field(default_factory=list)
    bound: BoundCheck | None = None

    def print(self) -> None:
        """Short stdout summary."""
        print(f"[trace] {self.table}  row={self.row}  value={self.value!r}")
        if self.dependency is None:
            print("  no dependency entry (unknown or out-of-scope result variable)")
            return
        if self.dependency.formula_hint:
            print(f"  formula: {self.dependency.formula_hint}")
        if self.bound:
            print(f"  bound state: {self.bound.state}"
                  + (f" ({self.bound.bound_table}={self.bound.bound_value!r})"
                     if self.bound.bound_table else ""))
        if self.contributing_inputs:
            print("  contributing inputs:")
            for t in self.contributing_inputs:
                extra = f"  (LEAP: {t.leap_ui_hint})" if t.leap_ui_hint else ""
                print(f"    {t.parameter}: value={t.row_value!r}{extra}")
        if self.upstream_results:
            print(f"  upstream results: {', '.join(self.upstream_results)}")


def _fetch_row_value(db: NemoDB, table: str, row: dict) -> float | None:
    """SELECT val for a specific dim-tuple row; returns None if the table is
    absent or the row does not exist."""
    if table not in db.list_tables():
        return None
    filters = []
    params: list[Any] = []
    for k, v in row.items():
        if k.startswith("_"):       # skip private keys like _module_branch_id
            continue
        filters.append(f'"{k}" = ?')
        params.append(str(v) if not isinstance(v, (int, float)) else v)
    where = " AND ".join(filters) if filters else "1=1"
    try:
        df = db.query(
            f"SELECT val FROM \"{table}\" WHERE {where} LIMIT 1",
            params=params,
        )
    except Exception:
        return None
    if df.empty:
        return None
    v = df.iloc[0]["val"]
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _matching_dim_row(param: str, row: dict) -> dict:
    """Subset a result-row dict to the dim columns a parameter expects."""
    p = PARAMETERS.get(param)
    if p is None:
        # best-effort: use whatever keys match
        return {k: v for k, v in row.items() if not k.startswith("_")}
    return {dim: row[dim] for dim in p.dims if dim in row}


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(_BIND_ABS_TOL, _BIND_REL_TOL * max(abs(a), abs(b), 1.0))


def _check_bound(
    db: NemoDB, table: str, row: dict, dep: ResultDependency, value: float | None,
) -> BoundCheck:
    if value is None:
        return BoundCheck(state=BOUND_UNKNOWN, note="no value found for this row")

    # Upper bounds
    for bound_table in dep.upper_bounds:
        param_row = _matching_dim_row(bound_table, row)
        bound_val = _fetch_row_value(db, bound_table, param_row)
        if bound_val is not None and _close(value, bound_val):
            return BoundCheck(
                state=BOUND_HIT_UPPER,
                bound_table=bound_table,
                bound_value=bound_val,
                actual_value=value,
            )

    # Lower bounds
    for bound_table in dep.lower_bounds:
        param_row = _matching_dim_row(bound_table, row)
        bound_val = _fetch_row_value(db, bound_table, param_row)
        if bound_val is not None and _close(value, bound_val):
            return BoundCheck(
                state=BOUND_HIT_LOWER,
                bound_table=bound_table,
                bound_value=bound_val,
                actual_value=value,
            )

    if not dep.upper_bounds and not dep.lower_bounds:
        return BoundCheck(state=BOUND_ABSENT, actual_value=value,
                          note="no bounds declared for this result")
    return BoundCheck(state=BOUND_FREE, actual_value=value)


def trace_result(
    db: NemoDB,
    table: str,
    row: dict,
    context=None,
) -> ResultTrace:
    """Return a full ancestry trace for a single result-variable row.

    Parameters
    ----------
    db : NemoDB
    table : str
        Name of the v* result table (e.g. ``"vtotalcapacityannual"``).
    row : dict
        Dim-tuple identifying the row (e.g.
        ``{"r": "R1", "t": "P16756", "y": "2030"}``). ``val`` is looked up
        automatically.
    context : LeapAreaContext, optional
        When supplied, each input carries a LEAP UI hint via
        :func:`nemo_read.leap_area.where_in_leap`.

    Returns
    -------
    ResultTrace
    """
    dep = RESULT_DEPENDENCIES.get(table)
    value = _fetch_row_value(db, table, row)

    trace = ResultTrace(table=table, row=dict(row), value=value, dependency=dep)

    if dep is None:
        return trace

    # Contributing inputs
    for param_name in dep.inputs:
        param_row = _matching_dim_row(param_name, row)
        param_value = _fetch_row_value(db, param_name, param_row)
        ui_hint = None
        confidence = None
        if context is not None:
            from .leap_area import where_in_leap  # local import to avoid cycles
            hint = where_in_leap(param_name, param_row, context)
            if hint:
                ui_hint = hint["ui_path_hint"]
                confidence = hint["confidence"]
        trace.contributing_inputs.append(InputTrace(
            parameter=param_name,
            row_value=param_value,
            leap_ui_hint=ui_hint,
            confidence=confidence,
        ))

    trace.upstream_results = list(dep.upstream_results)
    trace.bound = _check_bound(db, table, row, dep, value)
    return trace


# ---------------------------------------------------------------------------
# Cost decomposition
# ---------------------------------------------------------------------------

# Components of vtotaldiscountedcost by cost "stream". Positive = added to
# total, negative = subtracted (salvage value).
_COST_STREAMS: dict[str, tuple[str, ...]] = {
    "capital_investment_tech":   ("vdiscountedcapitalinvestment",),
    "capital_investment_storage":("vdiscountedcapitalinvestmentstorage",),
    "capital_investment_transmission":
                                  ("vdiscountedcapitalinvestmenttransmission",),
    "operating_cost_tech":       ("vdiscountedoperatingcost",),
    "operating_cost_transmission":("vdiscountedoperatingcosttransmission",),
    "emissions_penalty":         ("vdiscountedtechnologyemissionspenalty",),
    "finance_cost_tech":         ("vfinancecost",),
    "finance_cost_storage":      ("vfinancecoststorage",),
    "finance_cost_transmission": ("vfinancecosttransmission",),
    "salvage_value_tech":        ("vdiscountedsalvagevalue",),
    "salvage_value_storage":     ("vdiscountedsalvagevaluestorage",),
    "salvage_value_transmission":("vdiscountedsalvagevaluetransmission",),
}

# Streams whose contribution is SUBTRACTED from vtotaldiscountedcost.
_SUBTRACTED = {
    "salvage_value_tech", "salvage_value_storage", "salvage_value_transmission",
}


@dataclass
class CostBreakdown:
    """Per-(region, year) decomposition of ``vtotaldiscountedcost``."""
    region: str
    year: str
    total: float
    streams: dict[str, float] = field(default_factory=dict)
    reconstructed: float | None = None     # sum of streams (signed) — should match total

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for name, value in self.streams.items():
            sign = -1 if name in _SUBTRACTED else 1
            signed = sign * value
            share = signed / self.total if self.total else 0.0
            rows.append({
                "stream": name,
                "value": value,
                "sign": "-" if sign < 0 else "+",
                "signed": signed,
                "share_of_total": share,
            })
        return pd.DataFrame(rows).sort_values("signed", ascending=False,
                                              key=lambda s: s.abs())

    def print(self) -> None:
        print(f"[cost] region={self.region!r}  year={self.year!r}  "
              f"vtotaldiscountedcost={self.total!r}")
        if self.reconstructed is not None:
            if self.total:
                diff = self.reconstructed - self.total
                print(f"  reconstructed from streams = {self.reconstructed!r}  "
                      f"(delta={diff:+.3e})")
            elif self.reconstructed != 0.0:
                print(f"  reconstructed from streams = {self.reconstructed!r}  "
                      f"(no stored total — vtotaldiscountedcost not in varstosave?)")
        print("  streams:")
        for name, val in sorted(self.streams.items(),
                                key=lambda kv: -abs(kv[1])):
            sign = "-" if name in _SUBTRACTED else "+"
            print(f"    {sign} {name:<35} {val:>18.4f}")


def _table_columns(db: NemoDB, table: str) -> set[str]:
    try:
        pragma = db.query(f'PRAGMA table_info("{table}")')
        return set(pragma["name"].astype(str).tolist())
    except Exception:
        return set()


def _sum_result_table(db: NemoDB, table: str, region: str, year: str) -> float:
    """Aggregate a cost-stream table to a scalar for given (r, y)."""
    if table not in db.list_tables():
        return 0.0
    cols = _table_columns(db, table)
    # Some cost streams are indexed by (tr, y) without an `r` dimension —
    # in that case we sum across transmission lines for the year.
    filters = ['"y" = ?']
    params: list[Any] = [str(year)]
    if "r" in cols:
        filters.append('"r" = ?')
        params.append(str(region))
    where = " AND ".join(filters)
    try:
        df = db.query(
            f'SELECT COALESCE(SUM(val), 0.0) AS s FROM "{table}" WHERE {where}',
            params=params,
        )
    except Exception:
        return 0.0
    if df.empty:
        return 0.0
    return float(df.iloc[0]["s"])


def trace_cost(
    db: NemoDB,
    region: str,
    year: str | int,
    context=None,
) -> CostBreakdown:
    """Decompose ``vtotaldiscountedcost`` for one (region, year) into
    individual cost streams.

    NEMO stores years as TEXT in the SQLite; integers are accepted and
    str-coerced automatically.
    """
    y = str(year)
    total = _fetch_row_value(db, "vtotaldiscountedcost", {"r": region, "y": y}) or 0.0

    breakdown = CostBreakdown(region=region, year=y, total=total)

    for stream_name, tables in _COST_STREAMS.items():
        # Each stream may have multiple candidate tables (none yet — kept
        # for future flexibility). Sum the first one that has data.
        value = 0.0
        for table in tables:
            value = _sum_result_table(db, table, region, y)
            if value != 0.0:
                break
        breakdown.streams[stream_name] = value

    # Reconstruct: sum with sign conventions
    reconstructed = 0.0
    for name, v in breakdown.streams.items():
        reconstructed += (-v if name in _SUBTRACTED else v)
    breakdown.reconstructed = reconstructed

    return breakdown
