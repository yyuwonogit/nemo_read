"""
Offline LEAP-area context: loads files written by ``nemo_read-leap-export``
and exposes decoded metadata to the rest of :mod:`nemo_read`.

Core entry points:

- :class:`LeapAreaContext` — holds branches, fuels, regions, timeslices,
  scenarios, nemo.cfg, custom constraints for one exported LEAP area.
- :meth:`LeapAreaContext.from_export` — load from a directory of plain files.
- :meth:`LeapAreaContext.discover` — auto-find an adjacent export directory
  given a :class:`~nemo_read.db.NemoDB` instance.
- :func:`read_nemo_cfg` — parse LEAP's nemo.cfg (TOML).
- :func:`read_custom_constraints` — extract function names, NEMOcc table
  references, and pollutant→eid map from ``customconstraints.txt``.
- :func:`where_in_leap` — given a parameter row, return the LEAP branch +
  variable + UI path hint that populates it.
"""
from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .schema import LEAP_SOURCE_MAP, LeapSource


def read_nemo_cfg(path: str | Path) -> dict[str, Any]:
    """Parse LEAP's ``nemo.cfg`` (TOML). Returns the parsed dict.

    Common keys:

    - ``calculatescenarioargs.varstosave``  — list of v* tables LEAP will
      populate on calculation
    - ``calculatescenarioargs.calcyears``   — optional calc-year restriction
    - ``solver.parameters``                 — solver parameter string
    - ``includes.customconstraints``        — path to customconstraints.txt
    """
    path = Path(path)
    with path.open("rb") as f:
        return tomllib.load(f)


@dataclass
class CustomConstraintsDoc:
    """Parsed summary of ``customconstraints.txt``."""

    raw: str
    #: Julia function names that build constraints.
    functions: list[str]
    #: ``*__NEMOcc`` table names referenced via SQL ``from`` clauses.
    nemocc_tables: list[str]
    #: Pollutant short-code → LEAP emission ID (e.g. ``"CO2" -> 2``).
    #: Parsed from inline comments like ``# CO2`` next to ``E2`` references.
    pollutant_to_eid: dict[str, int]
    #: Reverse of above (e.g. ``2 -> "CO2"``).
    eid_to_pollutant: dict[int, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.eid_to_pollutant:
            self.eid_to_pollutant = {v: k for k, v in self.pollutant_to_eid.items()}


_FUNCTION_RE = re.compile(r"^\s*function\s+(\w+)\s*\(", re.MULTILINE)
_NEMOCC_RE = re.compile(r"(\w+__NEMOcc)\b")
# match a line like: "vannualemissions[$r,E2,$y])) # CO2"
_EID_COMMENT_RE = re.compile(r"\bE(\d+)[^#\n]*#\s*([A-Za-z0-9][^\n]*?)(?:\s*$|\s+using)", re.MULTILINE)


def read_custom_constraints(path: str | Path) -> CustomConstraintsDoc:
    """Parse ``customconstraints.txt`` for structural metadata.

    The file is Julia source. We don't execute it — regex extracts function
    names, NEMOcc table references, and a best-effort pollutant→eid map
    from inline comments.
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="replace")

    functions = sorted(set(_FUNCTION_RE.findall(raw)))
    nemocc_tables = sorted(set(_NEMOCC_RE.findall(raw)))

    pollutant_to_eid: dict[str, int] = {}
    for m in _EID_COMMENT_RE.finditer(raw):
        eid = int(m.group(1))
        label = m.group(2).strip()
        # keep short labels only — comments like "CO2" or "CH4 using AR5..."
        label_short = label.split()[0] if label else ""
        if label_short and eid not in pollutant_to_eid.values():
            pollutant_to_eid.setdefault(label_short, eid)

    return CustomConstraintsDoc(
        raw=raw,
        functions=functions,
        nemocc_tables=nemocc_tables,
        pollutant_to_eid=pollutant_to_eid,
    )


@dataclass
class LeapAreaContext:
    """Decoded LEAP-area metadata paired with a NEMO SQLite scenario database.

    Load with :meth:`from_export` or :meth:`discover`. All frames use plain
    string / int columns so they can be serialised as CSV.
    """

    area: str
    export_dir: Path
    branches: pd.DataFrame        # id, name, full_name, parent_id, parent_name, branch_type, branch_type_name, level, notes
    fuels: pd.DataFrame           # id, name
    regions: pd.DataFrame         # id, name
    timeslices: pd.DataFrame      # id, name, hours
    scenarios: pd.DataFrame       # id, name, results_shown, last_calculated
    tags: pd.DataFrame            # id, name
    units: pd.DataFrame           # id, name
    nemocc_sources: pd.DataFrame  # table_name, branch_id, branch_full_name, expression_head
    branch_expressions: pd.DataFrame  # branch_id, variable_name, scenario_name, expression
    branch_values: pd.DataFrame   # branch_id, variable_name, scenario_id, scenario_name, region_id, year, value
    nemo_cfg: dict[str, Any] | None
    custom_constraints: CustomConstraintsDoc | None
    manifest: dict[str, Any]

    # ------------------------------------------------------------------ loaders
    @classmethod
    def from_export(cls, export_dir: str | Path) -> "LeapAreaContext":
        """Load a context from a directory produced by ``nemo_read-leap-export``."""
        export_dir = Path(export_dir)
        if not export_dir.exists():
            raise FileNotFoundError(f"Export directory does not exist: {export_dir}")

        def _load_csv(name: str, empty_cols: list[str]) -> pd.DataFrame:
            p = export_dir / name
            if not p.exists():
                return pd.DataFrame({c: [] for c in empty_cols})
            return pd.read_csv(p)

        manifest_path = export_dir / "manifest.json"
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        nemo_cfg_path = export_dir / "nemo.cfg"
        nemo_cfg = read_nemo_cfg(nemo_cfg_path) if nemo_cfg_path.exists() else None

        cc_path = export_dir / "customconstraints.txt"
        cc = read_custom_constraints(cc_path) if cc_path.exists() else None

        return cls(
            area=manifest.get("area", export_dir.parent.name),
            export_dir=export_dir,
            branches=_load_csv("branches.csv", [
                "id", "name", "full_name", "parent_id", "parent_name",
                "branch_type", "branch_type_name", "level", "notes",
            ]),
            fuels=_load_csv("fuels.csv", ["id", "name"]),
            regions=_load_csv("regions.csv", ["id", "name"]),
            timeslices=_load_csv("timeslices.csv", ["id", "name", "hours"]),
            scenarios=_load_csv("scenarios.csv", [
                "id", "name", "results_shown", "last_calculated",
            ]),
            tags=_load_csv("tags.csv", ["id", "name"]),
            units=_load_csv("units.csv", ["id", "name"]),
            nemocc_sources=_load_csv("nemocc_sources.csv", [
                "table_name", "branch_id", "branch_full_name", "expression_head",
            ]),
            branch_expressions=_load_csv("branch_variable_expressions.csv", [
                "branch_id", "variable_name", "scenario_name", "expression",
            ]),
            branch_values=_load_csv("branch_variable_values.csv", [
                "branch_id", "variable_name", "scenario_id", "scenario_name",
                "region_id", "year", "value",
            ]),
            nemo_cfg=nemo_cfg,
            custom_constraints=cc,
            manifest=manifest,
        )

    @classmethod
    def discover(cls, db) -> "LeapAreaContext | None":
        """Find an export directory adjacent to a :class:`NemoDB`'s sqlite file.

        Priority order:
        1. ``<sqlite_path>.leap_export/``      (same stem as the sqlite)
        2. ``<sqlite_dir>/leap_export/``       (sibling generic dir)

        Returns None if nothing found.
        """
        sqlite_path = Path(db.path if hasattr(db, "path") else db)
        candidates = [
            sqlite_path.with_suffix(".leap_export"),
            sqlite_path.parent / "leap_export",
        ]
        for c in candidates:
            if c.exists() and (c / "branches.csv").exists():
                return cls.from_export(c)
        return None

    # ------------------------------------------------------------ lookup helpers
    def branch_full_name(self, branch_id: int) -> str | None:
        """Return a branch's ``FullName`` by its LEAP ID."""
        if self.branches.empty:
            return None
        match = self.branches.loc[self.branches["id"] == branch_id, "full_name"]
        if match.empty:
            return None
        return str(match.iloc[0])

    def branch_by_id(self, branch_id: int) -> dict | None:
        """Return the full branch row as a dict, or None."""
        if self.branches.empty:
            return None
        match = self.branches.loc[self.branches["id"] == branch_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def fuel_name(self, leap_id: int) -> str | None:
        if self.fuels.empty:
            return None
        match = self.fuels.loc[self.fuels["id"] == leap_id, "name"]
        return None if match.empty else str(match.iloc[0])

    def region_name(self, leap_id: int) -> str | None:
        if self.regions.empty:
            return None
        match = self.regions.loc[self.regions["id"] == leap_id, "name"]
        return None if match.empty else str(match.iloc[0])

    def nemocc_source_for(self, table_name: str) -> dict | None:
        """Given a ``*__NEMOcc`` table name, return its defining branch."""
        if self.nemocc_sources.empty:
            return None
        match = self.nemocc_sources.loc[self.nemocc_sources["table_name"] == table_name]
        return None if match.empty else match.iloc[0].to_dict()

    # ----------------------------------------------------------- NEMOcc semantics
    @property
    def varstosave(self) -> list[str]:
        """Convenience accessor for ``nemo.cfg``'s varstosave list."""
        if not self.nemo_cfg:
            return []
        return list(
            self.nemo_cfg.get("calculatescenarioargs", {}).get("varstosave", [])
        )

    # --------------------------------------------------- LEAP-side value lookup
    def variable_value(
        self,
        branch_id: int,
        variable_name: str,
        year: int | None = None,
        region_id: int | None = None,
        scenario_name: str | None = None,
    ) -> "pd.Series | float | None":
        """Look up a numeric Variable value captured during export.

        Filters ``branch_values`` by branch + variable + (optional)
        scenario / year / region. Returns:

        - a single ``float`` if all three of (year, region_id, scenario)
          uniquely identify one row
        - a ``pd.Series`` indexed by the unspecified dim(s) otherwise
        - ``None`` if no rows match
        """
        if self.branch_values.empty:
            return None
        df = self.branch_values
        df = df[(df["branch_id"] == branch_id) & (df["variable_name"] == variable_name)]
        if scenario_name is not None:
            df = df[df["scenario_name"] == scenario_name]
        if year is not None:
            df = df[df["year"] == year]
        if region_id is not None:
            df = df[df["region_id"] == region_id]
        if df.empty:
            return None
        if len(df) == 1:
            return float(df.iloc[0]["value"])
        return df["value"].reset_index(drop=True)

    # ---------------------------------------------------------------- UI hints
    def where_in_leap(self, table: str, row: dict) -> dict | None:
        """Return a UI hint dict for a parameter-table row, or None if the
        table isn't mapped (dimensions, results).

        Delegates to :func:`where_in_leap` with ``self`` as the context.
        """
        return where_in_leap(table, row, self)


# ---------------------------------------------------------------------------
# Row → LEAP UI hint (uses LEAP_SOURCE_MAP from schema.py)
# ---------------------------------------------------------------------------


def _strip_tech_prefix(tech_val: str) -> int | None:
    """Turn ``'P16756'`` / ``'D123'`` / ``'S45'`` into the integer LEAP branch ID."""
    if not isinstance(tech_val, str) or len(tech_val) < 2:
        return None
    if tech_val[0] in "PDS" and tech_val[1:].isdigit():
        return int(tech_val[1:])
    return None


def _branch_id_from_row(
    source: LeapSource, row: dict, context: LeapAreaContext
) -> int | None:
    """Derive the LEAP branch ID from a parameter row + LeapSource spec."""
    kind = source.branch_dim
    if kind == "t" or kind == "s":
        val = row.get(kind) or row.get("t") or row.get("s")
        return _strip_tech_prefix(str(val)) if val else None
    if kind == "tr":
        val = row.get("tr")
        try:
            return int(val) if val is not None else None
        except (TypeError, ValueError):
            return None
    if kind == "module":
        # Caller must supply module_branch_id explicitly — we can't infer
        # which module a (r, f, y) reserve-margin row belongs to from dims alone.
        return row.get("_module_branch_id")
    if kind == "n_within_t":
        # Resolve Process Node: child of t's branch under "Transmission Nodes"
        tech_id = _strip_tech_prefix(str(row.get("t") or row.get("s") or ""))
        node_val = row.get("n")
        if tech_id is None or node_val is None:
            return None
        return _find_process_node(tech_id, str(node_val), context)
    return None


def _find_process_node(
    tech_id: int, node_name: str, context: LeapAreaContext
) -> int | None:
    """Find the Process Node (BT=57) child under a tech's Transmission Nodes folder."""
    branches = context.branches
    if branches.empty:
        return None
    # Find Transmission Nodes folder (BT=56) whose parent is tech_id
    folders = branches.loc[
        (branches["parent_id"] == tech_id) & (branches["branch_type"] == 56)
    ]
    if folders.empty:
        return None
    folder_id = int(folders.iloc[0]["id"])
    # Find Process Node child whose name matches
    node_row = branches.loc[
        (branches["parent_id"] == folder_id)
        & (branches["branch_type"] == 57)
        & (branches["name"].str.casefold() == node_name.casefold())
    ]
    if node_row.empty:
        return None
    return int(node_row.iloc[0]["id"])


def read_demand(
    db,
    *,
    by: str = "fuel",
    context: LeapAreaContext | None = None,
    include_specified: bool = True,
    include_accumulated: bool = True,
    decode: bool = True,
) -> pd.DataFrame:
    """Return demand in user-readable form.

    Parameters
    ----------
    db : NemoDB
    by : ``"fuel"`` (default) or ``"sector"``.
        ``"fuel"``  — region × fuel × year totals (purely from the SQLite).
        ``"sector"`` — sector × subsector × region × fuel × year, derived
        from the LEAP demand-tree leaves' captured ``Final Energy Demand``
        values. Requires ``context`` (a :class:`LeapAreaContext` produced
        by ``nemo_read-leap-export``) **and** that the export was run with
        a values scope that included demand leaves (the default since 0.6.2).
    context : LeapAreaContext, optional
        Required when ``by="sector"``.
    include_specified, include_accumulated : bool
        Whether to include rows from ``SpecifiedAnnualDemand`` and
        ``AccumulatedAnnualDemand``. Both default True.
    decode : bool
        If True (default), attach ``region_name`` / ``fuel_name`` columns.

    Returns
    -------
    pandas DataFrame.
    """
    from .dimensions import decode_dims
    from .parameters import get_parameter

    if by == "fuel":
        frames = []
        if include_specified:
            sad = get_parameter(db, "SpecifiedAnnualDemand")
            sad["source"] = "SpecifiedAnnualDemand"
            frames.append(sad)
        if include_accumulated:
            aad = get_parameter(db, "AccumulatedAnnualDemand")
            aad["source"] = "AccumulatedAnnualDemand"
            frames.append(aad)
        if not frames:
            return pd.DataFrame()
        out = pd.concat(frames, ignore_index=True)
        if decode:
            out = decode_dims(out, db, dims=("r", "f"))
        return out

    if by == "sector":
        if context is None:
            raise ValueError(
                "read_demand(by='sector') requires a LeapAreaContext. "
                "Run nemo_read-leap-export against the LEAP area, then "
                "ctx = LeapAreaContext.discover(db) and pass it as context="
            )
        if context.branch_values.empty:
            raise ValueError(
                "Context has no branch_values rows — re-export with "
                "--values-scope=demand-leaves (the default in 0.6.2+)."
            )
        # Demand leaves: BT=4 under Demand subtree
        demand_leaves = context.branches[
            context.branches["full_name"].str.startswith("Demand", na=False)
            & (context.branches["branch_type"] == 4)
        ].copy()
        if demand_leaves.empty:
            return pd.DataFrame()
        # Sector = path component at level 2 (Demand\<Sector>\...)
        def _split(full_name: str) -> tuple[str, str]:
            parts = full_name.split("\\")
            sector = parts[1] if len(parts) >= 2 else ""
            subsector = parts[2] if len(parts) >= 3 else ""
            return sector, subsector
        demand_leaves[["sector", "subsector"]] = demand_leaves["full_name"].apply(
            lambda fn: pd.Series(_split(fn))
        )
        # Filter values to Final Energy Demand on demand leaves
        values = context.branch_values[
            context.branch_values["variable_name"] == "Final Energy Demand"
        ]
        if values.empty:
            raise ValueError(
                "No 'Final Energy Demand' values captured. Re-export with "
                "--values-scope=demand-leaves (default since 0.6.2)."
            )
        merged = values.merge(
            demand_leaves[["id", "sector", "subsector", "name"]],
            left_on="branch_id", right_on="id", how="inner",
        )
        # Aggregate by (sector, subsector, region_id, year)
        out = (merged.groupby(
                  ["sector", "subsector", "region_id", "year"], as_index=False
              )["value"].sum()
              .rename(columns={"value": "val"}))
        if decode:
            region_lookup = context.regions.set_index("id")["name"].to_dict()
            out["region_name"] = out["region_id"].map(region_lookup)
        return out

    raise ValueError(f"Unknown by={by!r}; expected 'fuel' or 'sector'.")


def where_in_leap(
    table: str, row: dict, context: LeapAreaContext
) -> dict | None:
    """Return a UI hint for a parameter-table row.

    Output fields:

    - ``table``              — the SQLite table name
    - ``variable_name``      — LEAP Variable on the branch
    - ``branch_type_name``   — e.g. ``'Transformation Process'``
    - ``branch_id``          — resolved LEAP branch ID (may be None)
    - ``branch_full_name``   — full path if resolved
    - ``ui_path_hint``       — human-readable navigation
    - ``confidence``         — ``'confirmed'`` / ``'inferred'`` / ``'unknown'``

    Returns None if the table has no mapping (result variables, dimensions).
    """
    source = LEAP_SOURCE_MAP.get(table)
    if source is None:
        return None
    branch_id = _branch_id_from_row(source, row, context)
    branch_full = context.branch_full_name(branch_id) if branch_id is not None else None
    if branch_full:
        ui_hint = f"{branch_full} -> Variable: {source.variable!r}"
    else:
        ui_hint = (
            f"Branch (type {source.branch_type_name}) -> Variable: {source.variable!r}"
        )
    return {
        "table": table,
        "variable_name": source.variable,
        "branch_type_name": source.branch_type_name,
        "branch_id": branch_id,
        "branch_full_name": branch_full,
        "ui_path_hint": ui_hint,
        "confidence": source.confidence,
    }
