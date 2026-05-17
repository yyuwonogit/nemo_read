"""
Internal Windows-only COM helpers. Imports `pywin32` lazily so the rest of
`nemo_read` stays pure-Python on Linux/Mac.

Not part of the public API. Only `nemo_read.leap_export` imports from here.

Two blockers these helpers address:

Blocker 1 (hang): ``leap.Branches("non-existent FullName")`` hangs LEAP.
    Fix: build id->idx and fullname->idx maps once; look up via ``Item(idx)``.

Blocker 2 (modal popup): ``variable.Expression`` on certain result variables
    raises a LEAP automation error and a modal dialog.
    Fix: try/except around every ``.Expression`` access.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

try:
    import pywintypes
    import win32com.client
    _HAS_PYWIN32 = True
except ImportError:
    pywintypes = None  # type: ignore[assignment]
    win32com = None  # type: ignore[assignment]
    _HAS_PYWIN32 = False


_NOT_WINDOWS_ERROR = (
    "nemo_read-leap-export requires pywin32 and a Windows install of LEAP. "
    "Install with: pip install 'nemo_read[leap]'"
)


def dispatch_leap():
    """Return a LEAP COM dispatch; raise a clear error if pywin32 missing."""
    if not _HAS_PYWIN32:
        raise RuntimeError(_NOT_WINDOWS_ERROR)
    return win32com.client.Dispatch("LEAP.LEAPApplication")


class LeapTreeCache:
    """Cached view of ``leap.Branches`` with safe lookup by ID or FullName.

    Builds ``id -> positional-index`` and ``fullname -> positional-index``
    maps on first access. Optional ``cache_file`` persists them as JSON.

    Never call ``leap.Branches("string")`` with an unverified path —
    use :meth:`by_id` or :meth:`by_fullname` instead.
    """

    def __init__(self, leap=None, cache_file: str | Path | None = None):
        self.leap = leap if leap is not None else dispatch_leap()
        self.branches = self.leap.Branches
        self._id_to_idx: dict[int, int] | None = None
        self._fullname_to_idx: dict[str, int] | None = None
        self._build_errors: int = 0
        self.cache_file: Path | None = Path(cache_file) if cache_file else None

    def _build_maps(self) -> None:
        if self.cache_file and self.cache_file.exists():
            try:
                data = json.loads(self.cache_file.read_text(encoding="utf-8"))
                # Cache keyed on area name only (since 0.6.4). LEAP's
                # Branches.Count occasionally fluctuates by 1 between calls
                # — exact-equality on count caused unnecessary 3-minute
                # rebuilds. Tolerate ±5 as a sanity bound.
                cached_area = data.get("area")
                cached_count = int(data.get("count", 0))
                live_area = self.leap.ActiveArea.Name
                live_count = self.branches.Count
                if cached_area == live_area and abs(cached_count - live_count) <= 5:
                    self._id_to_idx = {int(k): int(v) for k, v in data["id_to_idx"].items()}
                    self._fullname_to_idx = dict(data["fullname_to_idx"])
                    return
            except Exception:
                pass
        self._id_to_idx = {}
        self._fullname_to_idx = {}
        for i in range(1, self.branches.Count + 1):
            try:
                b = self.branches.Item(i)
            except Exception:
                self._build_errors += 1
                continue
            try:
                self._id_to_idx[b.ID] = i
            except Exception:
                pass
            try:
                self._fullname_to_idx[b.FullName] = i
            except Exception:
                pass
        if self.cache_file:
            try:
                self.cache_file.parent.mkdir(parents=True, exist_ok=True)
                self.cache_file.write_text(json.dumps({
                    "area": self.leap.ActiveArea.Name,
                    "count": self.branches.Count,
                    "id_to_idx": {str(k): v for k, v in self._id_to_idx.items()},
                    "fullname_to_idx": self._fullname_to_idx,
                }), encoding="utf-8")
            except Exception:
                pass

    @property
    def id_to_idx(self) -> dict[int, int]:
        if self._id_to_idx is None:
            self._build_maps()
        return self._id_to_idx  # type: ignore[return-value]

    @property
    def fullname_to_idx(self) -> dict[str, int]:
        if self._fullname_to_idx is None:
            self._build_maps()
        return self._fullname_to_idx  # type: ignore[return-value]

    def by_id(self, branch_id: int):
        idx = self.id_to_idx.get(branch_id)
        return self.branches.Item(idx) if idx is not None else None

    def by_fullname(self, full_name: str):
        idx = self.fullname_to_idx.get(full_name)
        return self.branches.Item(idx) if idx is not None else None

    def reconnect(self) -> None:
        """Re-dispatch LEAP after an RPC drop. Positional indexes stay valid,
        so cached maps don't need to be rebuilt."""
        self.leap = dispatch_leap()
        self.branches = self.leap.Branches


def _is_rpc_unavailable(exc) -> bool:
    """True if a COM error looks like 'RPC server is unavailable' (0x800706BA)."""
    if not _HAS_PYWIN32 or not isinstance(exc, pywintypes.com_error):
        return False
    try:
        hr = exc.args[0]
    except Exception:
        return False
    # -2147023174 is the decimal of 0x800706BA.
    return hr in (-2147023174, 0x800706BA)


def with_com_retry(func, retries: int = 2, backoff: float = 0.5):
    """Call ``func()``; retry up to ``retries`` times on RPC-unavailable errors.

    Useful for long COM walks where LEAP's RPC connection occasionally drops
    between calls. Any non-RPC com_error is re-raised immediately.
    """
    import time
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            if _is_rpc_unavailable(exc) and attempt < retries:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise
    if last_exc is not None:
        raise last_exc


def safe_expression(variable) -> str | None:
    """Return ``variable.Expression`` or None (never raises to caller).

    Handles: clean None, AttributeError, pywintypes.com_error
    ("Expressions are not used for result variables"), and non-scalar returns.
    """
    if not _HAS_PYWIN32:
        raise RuntimeError(_NOT_WINDOWS_ERROR)
    try:
        expr = variable.Expression
    except (pywintypes.com_error, AttributeError):
        return None
    if expr is not None and not isinstance(expr, (str, int, float, bool)):
        return None
    return expr  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Universal Interp() separator enforcement (CLAUDE.md §A.15)
# ---------------------------------------------------------------------------
import re as _re

_INTERP_RE = _re.compile(r"Interp\(([^)]*)\)", flags=_re.IGNORECASE)
_SEMICOLON_INSIDE_INTERP_RE = _re.compile(r"Interp\([^)]*;[^)]*\)", flags=_re.IGNORECASE)


class InterpSeparatorError(ValueError):
    """Raised when an expression contains a forbidden Interp() form.

    Per CLAUDE.md §A.15, every Interp(...) committed to LEAP must use
    comma list-separator + period decimal. Anything else (semicolon
    list-sep, comma decimal) raises this before any COM write happens.
    """


def normalize_interp(expr):
    """Force every `Interp(...)` substring to comma list-sep + period decimal.

    Returns the input unchanged for non-strings and for strings with no
    Interp() substrings. See CLAUDE.md §A.15 — comma list-sep + period
    decimal is the only accepted form on this engine.
    """
    if not isinstance(expr, str):
        return expr

    def _fix(m):
        inner = m.group(1).replace("; ", ", ").replace(";", ",")
        return f"Interp({inner})"

    return _INTERP_RE.sub(_fix, expr)


def assert_interp_canonical(expr) -> None:
    """Raise InterpSeparatorError if `expr` has any forbidden Interp form.

    Strict gate: refuses to let a wrong-separator Interp expression
    reach the COM layer. Use this in any injector before
    `variable.Expression = expr`.
    """
    if not isinstance(expr, str):
        return
    if _SEMICOLON_INSIDE_INTERP_RE.search(expr):
        raise InterpSeparatorError(
            f"Interp() expression uses ';' as list separator — forbidden "
            f"on this engine (CLAUDE.md §A.15). Expression: {expr!r}. "
            f"Run normalize_interp() upstream or fix the canonical CSV."
        )


def safe_set_expression(variable, expr):
    """The single chokepoint for writing `Variable.Expression` from any
    injector. ALWAYS go through here — never `variable.Expression = expr`
    directly.

    Behaviour:
      1. Normalises any `Interp(...; ...)` to `Interp(..., ..., ...)` so
         a tired author's mis-typed semicolon never reaches LEAP.
      2. After normalisation, asserts the expression is canonical
         (CLAUDE.md §A.15). Raises InterpSeparatorError if not — this
         should be impossible after step 1, so a raise here means the
         input had some other forbidden pattern we should learn about.
      3. Sets `variable.Expression`. Returns the normalised expression
         actually committed, so the caller can log it.

    This is the universal LAST line of defence. Every domain's injector
    (bioenergy, fossil, power, and any future sector) must call this
    function. Bypassing it = the same fossil-domain incident waiting to
    happen.
    """
    if not _HAS_PYWIN32:
        raise RuntimeError(_NOT_WINDOWS_ERROR)
    normalised = normalize_interp(expr)
    assert_interp_canonical(normalised)
    variable.Expression = normalised
    return normalised


def compare_expressions(actual, expected) -> str:
    """Compare an actual LEAP read-back to the expected CSV expression.

    Returns one of:
      - "EXACT"      : byte-equal
      - "NORMALISED" : equal after collapsing list-separator variants
                       (e.g. LEAP re-rendered commas as periods on read-back,
                       which means the inject committed wrong — see §A.15).
                       This is a HARD FAIL per §A.15, not a soft pass.
      - "FAIL"       : not equal even after normalisation.
    """
    if actual is None or expected is None:
        return "FAIL"
    actual_s = str(actual)
    expected_s = str(expected)
    if actual_s == expected_s:
        return "EXACT"
    # Locale-flip normalisation: LEAP may display commas as periods when
    # reading back. Both forms collapse to the same canonical sequence.
    def _strip_sep(s: str) -> str:
        # Replace ". " and "; " inside Interp() with ", "
        def _fix(m):
            inner = (m.group(1)
                     .replace(". ", ", ")
                     .replace("; ", ", ")
                     .replace(";", ","))
            return f"Interp({inner})"
        return _INTERP_RE.sub(_fix, s)
    if _strip_sep(actual_s) == _strip_sep(expected_s):
        return "NORMALISED"
    return "FAIL"


def validate_canonical_csv_expressions(csv_path, expr_column: str = "expression"):
    """Pre-flight: scan a canonical CSV for forbidden Interp forms before
    any inject begins. Returns a list of (row_index, expression) tuples
    that violate CLAUDE.md §A.15.

    Empty list = CSV is clean. Non-empty = injector should refuse to
    proceed. This is the upstream complement to safe_set_expression() —
    catches batch problems before COM state is even touched.
    """
    import csv as _csv
    from pathlib import Path as _Path

    violations = []
    with _Path(csv_path).open("r", encoding="utf-8", newline="") as f:
        reader = _csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # start=2 → header is row 1
            expr = row.get(expr_column, "")
            if isinstance(expr, str) and _SEMICOLON_INSIDE_INTERP_RE.search(expr):
                violations.append((i, expr))
    return violations


class visible_false:
    """Context manager: temporarily set ``leap.Visible = False``.

    Belt-and-suspenders fallback if ``safe_expression``'s try/except ever
    fails to suppress a LEAP modal dialog. Not currently needed on LEAP 2024+.
    """

    def __init__(self, leap):
        self.leap = leap
        self._was_visible: bool | None = None

    def __enter__(self):
        try:
            self._was_visible = bool(self.leap.Visible)
            self.leap.Visible = False
        except Exception:
            self._was_visible = None
        return self

    def __exit__(self, *args):
        if self._was_visible is not None:
            try:
                self.leap.Visible = self._was_visible
            except Exception:
                pass


def iterate_variables_safe(
    branch, max_vars: int | None = None,
    deadline_seconds: float | None = None,
    fetch_expression: bool = True,
) -> Iterator[tuple[int, str | None, str | None]]:
    """Yield ``(index, name, expression_or_None)`` for each Variable on ``branch``.

    If ``deadline_seconds`` is set, stop iterating after the wall-clock
    elapsed since the first .Variables call exceeds the limit. Lets callers
    bail out of slow/stuck branches without preempting the COM call itself
    (Python can't interrupt a Windows COM dispatch from outside its thread).

    ``fetch_expression=False`` skips the per-variable ``.Expression`` access.
    Use this when you only care about variable names — touching ``.Expression``
    on a result variable can fire a modal LEAP dialog on some builds, which
    blocks the COM thread until the user dismisses it (the deadline can't
    preempt a modal). Pair with a follow-up :func:`safe_expression` call only
    on the variables whose names you care about.
    """
    import time
    try:
        vc = branch.Variables.Count
    except Exception:
        return
    if max_vars is not None:
        vc = min(vc, max_vars)
    started = time.perf_counter()
    for j in range(1, vc + 1):
        if deadline_seconds is not None and (time.perf_counter() - started) > deadline_seconds:
            return
        try:
            v = branch.Variables.Item(j)
        except Exception:
            yield j, None, None
            continue
        try:
            name = v.Name
        except Exception:
            name = None
        expr = safe_expression(v) if fetch_expression else None
        yield j, name, expr


def safe_value(variable, year: int) -> float | None:
    """Return ``variable.Value(year)`` for the LEAP-globally-active region or None.

    LEAP's Variable.Value signature treats positional args as (year, unit).
    To scope by region, set ``leap.ActiveRegion = name`` BEFORE calling
    this function. Iterate regions in an outer loop so the global setter
    only fires once per region instead of per call.

    Wraps the same defensive try/except as :func:`safe_expression`.
    """
    if not _HAS_PYWIN32:
        raise RuntimeError(_NOT_WINDOWS_ERROR)
    try:
        v = variable.Value(int(year))
    except (pywintypes.com_error, AttributeError, TypeError):
        return None
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
