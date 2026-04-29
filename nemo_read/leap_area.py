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


def _load_tree_paths(path: Path) -> list[str]:
    """Read a tree_paths.csv (single-column 'branch_full_name'). Returns
    [] when the file doesn't exist, so existing exports stay backwards-
    compatible."""
    if not path.exists():
        return []
    try:
        df = pd.read_csv(path)
    except Exception:
        return []
    if "branch_full_name" not in df.columns:
        return []
    return [str(s) for s in df["branch_full_name"].dropna().tolist()]


def _is_acronym_of(short_leaf: str, long_leaf: str) -> bool:
    """True if ``short_leaf`` is plausibly an initial-letter acronym of
    the words in ``long_leaf``.

    Examples:
      "POME" matches "Palm Oil Mill Effluent"
      "UCO"  matches "Used Cooking Oil"
      "FFB"  matches "Fresh Fruit Bunches"
    Requires the short leaf to be 2–6 chars and the long leaf to have
    a matching word count whose initials line up. Hyphens, slashes and
    parentheses in the long leaf are treated as word separators.
    """
    s = short_leaf.strip()
    if len(s) < 2 or len(s) > 6 or " " in s:
        return False
    if not s.isalpha():
        return False
    import re
    words = [w for w in re.split(r"[\s\-/().,]+", long_leaf.strip()) if w]
    if len(words) != len(s):
        return False
    return all(w[:1].lower() == c.lower() for w, c in zip(words, s))


def suggest_closest_branches(
    missing_path: str,
    known_paths: list[str],
    *,
    n: int = 3,
) -> list[tuple[str, str]]:
    """Return up to ``n`` closest matches for a missing branch path.

    Each result is a ``(suggested_path, reason)`` pair. Reasons explain
    why the match was offered, in priority order:

    - ``"sibling"`` — same parent path, leaf-name fuzzy match
    - ``"same_leaf"`` — different parent, identical leaf name
    - ``"restructured"`` — same root segment + same leaf, different
      intermediate path (e.g. ``A\\B\\C\\Leaf`` exists at ``A\\Leaf``)
    - ``"acronym_expansion"`` — leaf appears to be an initial-letter
      acronym of an existing branch's leaf (e.g. ``POME`` →
      ``Palm Oil Mill Effluent``)
    - ``"path_fuzzy"`` — full-path fuzzy match (last resort)

    Returns ``[]`` if ``known_paths`` is empty (e.g. tree_paths.csv was
    not written by an older `nemo_read-leap-units` build).
    """
    import difflib

    if not known_paths or not missing_path:
        return []

    missing_clean = missing_path.strip()
    segments = missing_clean.split("\\")
    parent = "\\".join(segments[:-1])
    root = segments[0] if segments else ""
    leaf = segments[-1].lower()

    # Always exclude the missing path itself — it may legitimately appear
    # in known_paths (e.g. when the branch exists but its specific variable
    # was never probed) yet self-suggesting it is unhelpful.
    seen: set[str] = {missing_clean}
    out: list[tuple[str, str]] = []

    # 1) Siblings — same parent, fuzzy leaf-name match
    if parent:
        siblings = [p for p in known_paths
                    if p.startswith(parent + "\\") and p != missing_clean]
        sibling_leaves = {p.split("\\")[-1].lower(): p for p in siblings}
        for cand_leaf in difflib.get_close_matches(
            leaf, list(sibling_leaves.keys()), n=n, cutoff=0.5,
        ):
            full = sibling_leaves[cand_leaf]
            if full not in seen:
                out.append((full, "sibling"))
                seen.add(full)
            if len(out) >= n:
                return out

    # 2) Same leaf, different parent
    same_leaf_matches = [
        p for p in known_paths
        if p.split("\\")[-1].lower() == leaf and p not in seen
    ]
    for full in same_leaf_matches[: n - len(out)]:
        out.append((full, "same_leaf"))
        seen.add(full)
        if len(out) >= n:
            return out

    # 3) Restructured — same root segment + same leaf, intermediate path
    #    differs. E.g. canonical asks for `Resources\Primary\Bioenergy
    #    Land\Arable` but LEAP has `Resources\Primary\Arable` directly.
    if root and len(out) < n:
        restructured = [
            p for p in known_paths
            if p not in seen
            and p.split("\\")[0] == root
            and p.split("\\")[-1].lower() == leaf
        ]
        for full in restructured[: n - len(out)]:
            out.append((full, "restructured"))
            seen.add(full)
            if len(out) >= n:
                return out

    # 4) Acronym expansion — leaf could be an initial-letter abbreviation
    #    of an existing branch's leaf. Prefer same root subtree.
    if leaf and len(out) < n:
        # Same root first
        acronym_in_root = [
            p for p in known_paths
            if p not in seen
            and (not root or p.split("\\")[0] == root)
            and _is_acronym_of(leaf, p.split("\\")[-1])
        ]
        for full in acronym_in_root[: n - len(out)]:
            out.append((full, "acronym_expansion"))
            seen.add(full)
            if len(out) >= n:
                return out
        # Then anywhere
        if len(out) < n:
            acronym_anywhere = [
                p for p in known_paths
                if p not in seen
                and _is_acronym_of(leaf, p.split("\\")[-1])
            ]
            for full in acronym_anywhere[: n - len(out)]:
                out.append((full, "acronym_expansion"))
                seen.add(full)
                if len(out) >= n:
                    return out

    # 5) Full-path fuzzy match (case-insensitive)
    if len(out) < n:
        lower_to_full = {p.lower(): p for p in known_paths if p not in seen}
        for cand_lower in difflib.get_close_matches(
            missing_clean.lower(), list(lower_to_full.keys()),
            n=n - len(out), cutoff=0.5,
        ):
            full = lower_to_full[cand_lower]
            if full not in seen:
                out.append((full, "path_fuzzy"))
                seen.add(full)

    return out[:n]


def infer_fuel_from_consumers(
    missing_resource_path: str,
    known_paths: list[str],
    *,
    n: int = 5,
) -> list[str]:
    """For a missing primary/secondary fuel, return the actual leaf names
    that LEAP-side consumer processes use as their feedstocks.

    Rationale: when canonical references e.g. ``Resources\\Primary\\POME``
    but LEAP has the fuel under a different name (e.g. ``Palm Oil Mill
    Effluent``), the consumer process — typically named after the
    feedstock (e.g. ``POME Biodiesel``) — IS in the LEAP tree, and ITS
    ``Feedstock Fuels\\<X>`` child names the actual fuel.

    Algorithm:
      1. Identify the missing leaf (``POME``, ``Used Cooking Oil``, …).
      2. Find any LEAP path matching ``Transformation\\...\\Processes\\
         <X>\\Feedstock Fuels\\<Y>`` whose ``<X>`` contains the leaf
         (case-insensitive substring) or whose ``<X>`` is an acronym
         expansion candidate.
      3. Return up to ``n`` distinct ``<Y>`` values — those are the
         LEAP-side names the canonical row should use.

    Returns ``[]`` when no consumer process pattern is recognised.
    """
    if not known_paths or not missing_resource_path:
        return []
    segments = missing_resource_path.strip().split("\\")
    if len(segments) < 2:
        return []
    # Only handle Resources\Primary\* and Resources\Secondary\* missing fuels.
    if not (segments[0].lower() == "resources"
            and segments[1].lower() in {"primary", "secondary"}):
        return []
    missing_leaf = segments[-1]
    leaf_lower = missing_leaf.lower()

    # Walk known paths for "...\Processes\<X>\Feedstock Fuels\<Y>" matches.
    out: list[str] = []
    seen: set[str] = set()
    for p in known_paths:
        parts = p.split("\\")
        if len(parts) < 5:
            continue
        # Shape: ...\Processes\<process_leaf>\Feedstock Fuels\<fuel_leaf>
        try:
            processes_idx = parts.index("Processes")
        except ValueError:
            continue
        if processes_idx + 3 >= len(parts):
            continue
        if parts[processes_idx + 2] != "Feedstock Fuels":
            continue
        process_leaf = parts[processes_idx + 1]
        fuel_leaf = parts[processes_idx + 3]
        # Match if missing-leaf appears in process_leaf, or process_leaf is
        # an acronym expansion of missing-leaf, or fuel_leaf already names
        # something that looks like an expansion of missing-leaf.
        match = (
            leaf_lower in process_leaf.lower()
            or _is_acronym_of(missing_leaf, process_leaf)
            or _is_acronym_of(missing_leaf, fuel_leaf)
            or leaf_lower in fuel_leaf.lower()
        )
        if not match:
            continue
        if fuel_leaf not in seen:
            out.append(fuel_leaf)
            seen.add(fuel_leaf)
        if len(out) >= n:
            break
    return out


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
    branch_units: pd.DataFrame    # branch_id, branch_full_name, variable_name, data_unit_text, data_unit_id
    tree_paths: list[str]         # every branch FullName (lightweight; written by nemo_read-leap-units)
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
            branch_units=_load_csv("branch_variable_units.csv", [
                "branch_id", "branch_full_name", "variable_name",
                "data_unit_text", "data_unit_id",
            ]),
            tree_paths=_load_tree_paths(export_dir / "tree_paths.csv"),
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


def audit_canonical_units(
    canonical_df: pd.DataFrame,
    context: LeapAreaContext,
    *,
    propose: bool = True,
) -> pd.DataFrame:
    """Compare a canonical injection CSV's documented units against LEAP's
    actual variable units (from ``context.branch_units``).

    The canonical CSV must have ``branch``, ``variable``, ``unit`` columns
    (the format produced by mailbox/build_canonical.py). When ``propose=True``
    (default), a fuel column is also looked at for fuel-specific conversion
    proposals from :mod:`nemo_read.unit_conversions`.

    Returns a DataFrame with one row per unique (branch, variable[, fuel])
    triple. Always includes ``status``:

    - ``"match"``       — unit families align; no conversion needed
    - ``"likely_match"`` — close keywords; visual review recommended
    - ``"mismatch"``    — different unit families; values need conversion
    - ``"no_leap_unit"`` — branch_units doesn't carry this pair

    When ``propose=True`` and status is ``"mismatch"``, also adds:

    - ``proposed_factor`` (float or NaN if no proposal exists)
    - ``confidence_stars`` (1–5 integer or 0 if no proposal)
    - ``conversion_source`` (citation string)
    - ``conversion_caveat`` (optional warning)
    """
    if context.branch_units.empty:
        raise ValueError(
            "context.branch_units is empty — run nemo_read-leap-units first "
            "(it writes branch_variable_units.csv into the export dir)"
        )

    pairs = (canonical_df[["branch", "variable", "unit"]]
             .drop_duplicates(["branch", "variable"]))
    units_idx = {
        (row["branch_full_name"], row["variable_name"]): row["data_unit_text"]
        for _, row in context.branch_units.iterrows()
    }

    def _normalise(s: str) -> str:
        s = str(s or "").lower()
        return (s.replace("u.s. dollar", "usd")
                  .replace("united states dollar", "usd")
                  .replace("2020 usd", "usd")
                  .replace("billion barrel of oil equivalent", "gbbl")
                  .replace("barrel", "bbl")
                  .replace("metric tonne", "tonne")
                  .replace("million btu", "mmbtu")
                  .replace("petajoule", "pj")
                  .replace("thousand gigajoules", "tgj")
                  .replace("thousand gigajoule", "tgj")
                  .replace("gigajoules", "gj")
                  .replace("gigajoule", "gj")
                  .replace("megawatt", "mw")
                  .replace("100l", "hundredliter"))

    def _denominator(s: str) -> str:
        return s.split("/", 1)[1].strip().split()[0] if "/" in s else ""

    def _numerator(s: str) -> str:
        head = s.split("/", 1)[0]
        return head.strip().split()[-1] if head.strip() else ""

    # Known unit-family equivalents (no conversion needed)
    _SAME_FAMILY = {
        "bbl": {"bbl"},
        "tonne": {"tonne"},
        "gj": {"gj"},
        "mmbtu": {"mmbtu"},
        "pj": {"pj"},
        "year": {"year", "yr"},
        "gbbl": {"gbbl"},
        "tgj": {"tgj"},
        "mw": {"mw"},
        "kw": {"kw"},
        "hundredliter": {"hundredliter"},
    }

    def _families_match(a: str, b: str) -> bool:
        for fam in _SAME_FAMILY.values():
            if a in fam and b in fam:
                return True
        return False

    def _classify(your_unit: str, leap_unit: str) -> str:
        if not leap_unit or leap_unit.startswith("<"):
            return "no_leap_unit"
        y, l = _normalise(your_unit), _normalise(leap_unit)
        # Short-circuit: identical normalised strings always match. Avoids
        # false-positive mismatches for units (like "t/ha") whose tokens
        # are not in the _SAME_FAMILY registry.
        if y.strip() == l.strip() and y.strip():
            return "match"
        y_num, y_den = _numerator(y), _denominator(y)
        l_num, l_den = _numerator(l), _denominator(l)

        # Reserves-style (no slash on either side)
        if "/" not in y and "/" not in l:
            if _families_match(y.split()[-1] if y.split() else "",
                               l.split()[-1] if l.split() else ""):
                return "match"
            # Petajoule alone vs PJ/year: LEAP shows Petajoule for annual flows
            if "pj" in y and "pj" in l:
                return "match"
        if "/" not in l and ("pj" in y and "pj" in l):
            return "match"  # "PJ/year" vs "Petajoule" — LEAP convention

        # Both have / — compare numerator AND denominator family
        if y_num and l_num and y_den and l_den:
            num_ok = _families_match(y_num, l_num) or (y_num == "usd" and l_num == "usd")
            den_ok = _families_match(y_den, l_den)
            if num_ok and den_ok:
                return "match"
            if num_ok and not den_ok:
                return "mismatch"          # same numerator, different denominator → conversion needed
            if not num_ok and den_ok:
                return "mismatch"
            return "mismatch"

        # Token overlap as last resort — but only call it likely_match
        ytok = set(y.replace("/", " ").split())
        ltok = set(l.replace("/", " ").split())
        if ytok & ltok:
            return "likely_match"
        return "mismatch"

    # When proposing conversions we also need the fuel column from canonical.
    # Coerce to str — pandas turns empty cells into float NaN, which would
    # crash propose_conversion's fuel.strip() call.
    fuel_lookup = {}
    if propose and "fuel" in canonical_df.columns:
        for _, r in canonical_df.iterrows():
            fuel_val = r.get("fuel", "")
            if fuel_val is None or (isinstance(fuel_val, float) and pd.isna(fuel_val)):
                fuel_val = ""
            fuel_lookup[(r["branch"], r["variable"])] = str(fuel_val)

    from .unit_conversions import propose_conversion, fuel_specific_alternatives

    # If the canonical row's expression already uses LEAP's `[unit]` specifier
    # (formula reference like `Import Cost[2020 USD/bbl] * 0.97`), LEAP
    # converts internally and we should not flag it as a unit mismatch.
    formula_pairs = set()
    if "expression" in canonical_df.columns:
        for _, cr in canonical_df.iterrows():
            expr = str(cr.get("expression", ""))
            if "[" in expr and "]" in expr:
                formula_pairs.add((cr["branch"], cr["variable"]))

    # Tree-path universe for fuzzy branch suggestions on no_leap_unit rows.
    # Prefer the dedicated tree_paths.csv (full LEAP tree, ~3k paths) when
    # present; fall back to branch_units' branch_full_name column so older
    # exports without tree_paths.csv still get usable suggestions.
    known_paths = list(getattr(context, "tree_paths", []) or [])
    if not known_paths and not context.branch_units.empty:
        bf = context.branch_units["branch_full_name"].dropna().unique().tolist()
        known_paths = [str(p) for p in bf if p]

    out_rows = []
    for _, r in pairs.iterrows():
        leap_unit = units_idx.get((r["branch"], r["variable"]), "")
        if (r["branch"], r["variable"]) in formula_pairs:
            status = "formula_reference"
        else:
            status = _classify(r["unit"], leap_unit)
        row = {
            "branch": r["branch"],
            "variable": r["variable"],
            "your_unit": r["unit"],
            "leap_unit": leap_unit,
            "status": status,
        }
        # Branch suggestion + consumer-process hint for missing branches.
        row["branch_suggestion"] = ""
        row["consumer_fuel_hint"] = ""
        if status == "no_leap_unit" and known_paths:
            sugg = suggest_closest_branches(r["branch"], known_paths, n=3)
            if sugg:
                # Compact: "<path> (sibling); <path> (same_leaf); ..."
                row["branch_suggestion"] = "; ".join(
                    f"{p} ({reason})" for p, reason in sugg
                )
            # If the missing branch is a Resources\Primary or \Secondary
            # fuel, also try consumer-process inference — finds the
            # actual LEAP-side fuel name from the relevant process's
            # Feedstock Fuels children.
            consumer = infer_fuel_from_consumers(r["branch"], known_paths, n=5)
            if consumer:
                row["consumer_fuel_hint"] = "; ".join(consumer)

        # Fuel advice — flag rows that could lift confidence by adding fuel.
        row["fuel_advice"] = ""
        if propose and status == "mismatch":
            fuel = fuel_lookup.get((r["branch"], r["variable"]), None)
            prop = propose_conversion(r["unit"], leap_unit, fuel=fuel)
            if prop is not None:
                row["proposed_factor"] = prop.factor
                row["confidence_stars"] = prop.confidence_stars
                row["conversion_source"] = prop.source
                row["conversion_caveat"] = prop.caveat
            else:
                row["proposed_factor"] = float("nan")
                row["confidence_stars"] = 0
                row["conversion_source"] = "(no proposal in registry — add to nemo_read.unit_conversions or supply manual override)"
                row["conversion_caveat"] = ""
            # If we resolved (or fell back), check whether a fuel-keyed
            # alternative exists for this unit pair. If yes AND the row's
            # current `fuel` doesn't match any of them, surface the advice.
            alts = fuel_specific_alternatives(r["unit"], leap_unit)
            if alts:
                fuel_norm = (fuel or "").strip().lower()
                if not fuel_norm:
                    row["fuel_advice"] = (
                        f"add output_fuel context to lift confidence "
                        f"(known: {', '.join(alts)})"
                    )
                elif fuel_norm not in alts:
                    row["fuel_advice"] = (
                        f"row's fuel={fuel!r} not registered for this unit "
                        f"pair (known: {', '.join(alts)}) — verify or "
                        f"extend nemo_read.unit_conversions"
                    )
        else:
            row["proposed_factor"] = float("nan")
            row["confidence_stars"] = 0
            row["conversion_source"] = ""
            row["conversion_caveat"] = ""
        out_rows.append(row)
    return pd.DataFrame(out_rows)


def _rewrite_expression_value(expr: str, factor: float) -> str:
    """Multiply every numeric literal in an Interp(...) / Data(...) / scalar
    expression by ``factor``. Formula-style expressions (containing variable
    references) are returned unchanged with no rewrite — caller should warn.
    """
    import re
    expr = (expr or "").strip()
    # Pure scalar?
    try:
        return f"{float(expr) * factor:g}"
    except ValueError:
        pass
    # Interp / Data call
    m = re.match(r"^(Interp|Data)\s*\((.*)\)\s*$", expr, flags=re.DOTALL)
    if m:
        funcname = m.group(1)
        body = m.group(2)
        parts = [p.strip() for p in body.split(";")]
        out = []
        for i, tok in enumerate(parts):
            # alternating year; value
            if i % 2 == 1:
                try:
                    out.append(f"{float(tok) * factor:g}")
                except ValueError:
                    out.append(tok)
            else:
                out.append(tok)
        return f"{funcname}({'; '.join(out)})"
    # Formula or unknown — leave as-is
    return expr


def apply_audit_conversions(
    canonical_df: pd.DataFrame,
    audit_df: pd.DataFrame,
    overrides: dict | None = None,
) -> pd.DataFrame:
    """Produce a copy of ``canonical_df`` with mismatched-unit values
    converted to LEAP-native units, using the proposed factors from
    ``audit_df`` (and any per-row ``overrides`` the caller supplies).

    ``overrides`` keys are tuples accepted in two shapes:

    - ``(branch, variable)`` — applies regardless of fuel/AMS
    - ``(branch, variable, ams)`` — applies only when the canonical row's
      ``ams`` matches; falls back to the (branch, variable) entry if no
      AMS-specific override is found

    Override values are dicts with at least ``factor``; optional ``source``
    and ``confidence_stars`` are propagated into the new ``unit_audit``
    column for traceability.

    The output DataFrame has the same columns as ``canonical_df`` plus:

    - ``unit`` is updated to the LEAP-native unit string for converted rows
    - ``unit_audit`` records ``"factor=X (source=...) [stars=N]"`` for
      converted rows or ``""`` for matched / unchanged rows
    """
    overrides = overrides or {}
    audit_idx = {(r["branch"], r["variable"]): r
                 for _, r in audit_df.iterrows()}
    out = canonical_df.copy()
    out["unit_audit"] = ""

    def _override(branch: str, variable: str, ams: str) -> dict | None:
        return (overrides.get((branch, variable, ams))
                or overrides.get((branch, variable)))

    for i, row in out.iterrows():
        branch = row["branch"]
        variable = row["variable"]
        ams = row.get("ams", "")
        audit_row = audit_idx.get((branch, variable))
        if audit_row is None:
            continue
        if audit_row["status"] != "mismatch":
            continue

        ovr = _override(branch, variable, ams)
        if ovr is not None:
            factor = float(ovr["factor"])
            source = ovr.get("source", "(user override)")
            stars = ovr.get("confidence_stars", "?")
        else:
            factor = audit_row.get("proposed_factor")
            if factor is None or (isinstance(factor, float) and factor != factor):  # NaN
                # No proposal and no override — leave row alone, mark for attention
                out.at[i, "unit_audit"] = (
                    "MISMATCH unresolved — supply override in apply_audit_conversions"
                )
                continue
            source = audit_row.get("conversion_source", "")
            stars = audit_row.get("confidence_stars", "?")

        new_expr = _rewrite_expression_value(row["expression"], factor)
        out.at[i, "expression"] = new_expr
        out.at[i, "unit"] = audit_row["leap_unit"]
        out.at[i, "unit_audit"] = (
            f"factor={factor:g} stars={stars} source={source[:80]}"
        )
    return out


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
