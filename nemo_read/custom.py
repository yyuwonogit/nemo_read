"""
Custom constraints and slack-technology detection.

Two NEMO features that the stock schema doesn't cover but which appear
routinely in LEAP-generated databases:

1.  **Custom constraints** (``__NEMOcc`` tables). LEAP lets the modeller
    define additional constraints via the NEMO configuration file. LEAP
    stores each constraint's data in a table named
    ``<ConstraintName>__NEMOcc`` with columns ``(id, r, bid, eid, y, val)``
    where ``bid`` is typically a LEAP branch ID and ``eid`` is a secondary
    identifier (often ``-1`` as a "not applicable" sentinel).

    The NEMO source does not fix these columns — the name suffix is the
    only reliable signature — so this module discovers them at runtime
    and reads them generically.

2.  **Slack technologies**. LEAP/NEMO models traditionally carry synthetic
    "unserved demand" or "unmet load" technologies so the optimiser can
    always find a feasible solution. They are recognisable by very high
    capital cost (10^6 or more) or very high residual capacity (10^11+).
    Hiding them from routine summary stats prevents misleading totals.
"""

from __future__ import annotations
from typing import List, Optional, Sequence

import pandas as pd

from .db import NemoDB


# Suffix NEMO appends to custom-constraint tables. Empirically observed
# across LEAP 2024+ scenario databases.
_NEMOCC_SUFFIX = "__NEMOcc"

# Thresholds above which a technology is classified as a slack. Both are
# deliberately conservative so real-world capacity (a few thousand GW
# globally) and real capital costs (a few thousand currency units per kW)
# don't trip them.
SLACK_RESIDUAL_CAPACITY_THRESHOLD = 1e11
SLACK_CAPITAL_COST_THRESHOLD = 1e5


def list_custom_constraints(db: NemoDB) -> pd.DataFrame:
    """Return a summary of every ``*__NEMOcc`` table present.

    Columns
    -------
    name       : full table name including the ``__NEMOcc`` suffix
    short_name : the constraint name with the suffix stripped
    rows       : row count
    columns    : list of column names (typically id, r, bid, eid, y, val)
    regions    : distinct ``r`` values if an ``r`` column exists
    year_min   : minimum year value, or None
    year_max   : maximum year value, or None
    """
    out: List[dict] = []
    for t in db.list_tables():
        if not t.endswith(_NEMOCC_SUFFIX):
            continue
        cols = db.table_columns(t)
        n = db.row_count(t)
        entry = {
            "name": t,
            "short_name": t[: -len(_NEMOCC_SUFFIX)],
            "rows": n,
            "columns": cols,
            "regions": None,
            "year_min": None,
            "year_max": None,
        }
        if n > 0:
            if "r" in cols:
                rs = db.query(f'SELECT DISTINCT "r" FROM "{t}" ORDER BY "r"')
                entry["regions"] = rs["r"].tolist()
            if "y" in cols:
                yr = db.query(f'SELECT MIN("y") AS lo, MAX("y") AS hi FROM "{t}"')
                entry["year_min"] = yr["lo"].iloc[0]
                entry["year_max"] = yr["hi"].iloc[0]
        out.append(entry)
    return pd.DataFrame(out)


def get_custom_constraint(
    db: NemoDB,
    name: str,
    coerce_years: bool = True,
) -> pd.DataFrame:
    """Return a custom-constraint table as a DataFrame.

    ``name`` may be supplied with or without the ``__NEMOcc`` suffix; the
    function resolves either form to the canonical table name.
    """
    tables = set(db.list_tables())
    candidates = (name, name + _NEMOCC_SUFFIX)
    hit = next((c for c in candidates if c in tables), None)
    if hit is None:
        raise KeyError(
            f"No custom-constraint table named {name!r} "
            f"(tried {candidates})."
        )
    df = db.query(f'SELECT * FROM "{hit}"')
    if coerce_years and "y" in df.columns:
        df["y"] = pd.to_numeric(df["y"], errors="coerce").astype("Int64")
    return df


def detect_slack_technologies(
    db: NemoDB,
    residual_threshold: float = SLACK_RESIDUAL_CAPACITY_THRESHOLD,
    cost_threshold: float = SLACK_CAPITAL_COST_THRESHOLD,
    name_patterns: Sequence[str] = ("unserved", "unmet"),
) -> pd.DataFrame:
    """Identify technologies that look like optimisation slacks.

    A technology is flagged if it meets any of:

    - ``ResidualCapacity.val >= residual_threshold`` in any (r, y)
    - ``CapitalCost.val >= cost_threshold`` in any (r, y)
    - ``TECHNOLOGY.val`` or ``TECHNOLOGY.desc`` contains any of
      ``name_patterns`` (case-insensitive)

    Returns a frame with columns ``t``, ``desc``, ``reason``, where
    ``reason`` joins every matched criterion.
    """
    reasons: dict[str, List[str]] = {}

    tables = set(db.list_tables())
    if "ResidualCapacity" in tables:
        df = db.query(
            "SELECT DISTINCT t FROM ResidualCapacity WHERE val >= ?",
            (residual_threshold,),
        )
        for t in df["t"]:
            reasons.setdefault(t, []).append(
                f"residual_capacity>={residual_threshold:g}"
            )

    if "CapitalCost" in tables:
        df = db.query(
            "SELECT DISTINCT t FROM CapitalCost WHERE val >= ?",
            (cost_threshold,),
        )
        for t in df["t"]:
            reasons.setdefault(t, []).append(
                f"capital_cost>={cost_threshold:g}"
            )

    # Name-based match against TECHNOLOGY.val and .desc.
    if "TECHNOLOGY" in tables and name_patterns:
        pat = " OR ".join(
            f"LOWER(val) LIKE ? OR LOWER(IFNULL(desc, '')) LIKE ?"
            for _ in name_patterns
        )
        params: List = []
        for p in name_patterns:
            like = f"%{p.lower()}%"
            params.extend([like, like])
        df = db.query(f"SELECT val, desc FROM TECHNOLOGY WHERE {pat}", params)
        for _, row in df.iterrows():
            reasons.setdefault(row["val"], []).append("name_match")

    if not reasons:
        return pd.DataFrame(columns=["t", "desc", "reason"])

    # Attach descriptions.
    ts = tuple(reasons.keys())
    placeholders = ",".join(["?"] * len(ts))
    desc_df = db.query(
        f"SELECT val AS t, desc FROM TECHNOLOGY WHERE val IN ({placeholders})",
        ts,
    )
    desc_lookup = dict(zip(desc_df["t"], desc_df["desc"]))

    rows = [
        {"t": t, "desc": desc_lookup.get(t), "reason": ",".join(rs)}
        for t, rs in sorted(reasons.items())
    ]
    return pd.DataFrame(rows)


def slack_technology_ids(db: NemoDB, **kwargs) -> List[str]:
    """Convenience: just the list of slack technology IDs."""
    return detect_slack_technologies(db, **kwargs)["t"].tolist()
