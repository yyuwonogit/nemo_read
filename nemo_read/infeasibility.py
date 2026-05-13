"""
Static infeasibility and unboundedness checks.

NEMO itself ships a ``find_infeasibilities`` function, but that one
operates on a built JuMP model and requires the full Julia runtime. This
module provides the static counterpart: a battery of checks that can
flag common infeasibility and unboundedness patterns from the scenario
database alone, before anyone calls ``calculatescenario``.

Checks implemented:

    * Bound inversions on capacity, investment, and activity limits.
    * Exogenous emissions that already exceed their limit.
    * MinShareProduction fractions that sum to more than 1.0 per (r, f, y).
    * MinimumUtilization that exceeds AvailabilityFactor per (r, t, l, y).
    * MinStorageCharge that exceeds StorageLevelStart per (r, s, y).
    * Demanded fuels that no technology produces (no OAR path).
    * Reserve margin requirement without any reserve-tagged technology.
    * Storage with residual capacity but no charging path.
    * CCS unbounded-profit risk: negative emission factor + negative
      penalty + no capacity or activity upper bound.

Each finding carries a severity. Use :func:`find_infeasibilities` to run
the lot and get a :class:`ValidationReport`; the report shares the same
class as :func:`validate_scenario` so the two can be combined with
:meth:`ValidationReport.extend` if needed.

The check list is intentionally conservative: if a check cannot be
decided statically from the SQLite data (e.g. whether a renewable share
target is achievable given endogenous capacity expansion), the check is
skipped rather than emitting a guess. NEMO's own ``find_infeasibilities``
is the right tool for the dynamic case.

When the run *did* go through and the solver reported a column-index
infeasibility (e.g. CPLEX presolve: ``Infeasible column 'x435004'``),
the static checks here usually come up clean — the contradiction lives
in a multi-constraint chain rather than in a single bad row. Use
:func:`nemo_read.decode_lp_column` (in :mod:`nemo_read.lp_column_decode`)
to translate the ``xN`` index back to its NemoMod variable identity
(family + region + tech + year). That tells you which corner of the
data to inspect; the static checks above tell you what to fix.
"""

from __future__ import annotations
from typing import List, Optional, Tuple

import pandas as pd

from .db import NemoDB
from .schema import PARAMETERS
from .validate import ValidationIssue, ValidationReport


def find_infeasibilities(
    db: NemoDB,
    sample_rows: int = 5,
) -> ValidationReport:
    """Run every static infeasibility check against ``db`` and return the
    consolidated report.

    Parameters
    ----------
    db : NemoDB
    sample_rows : int, default 5
        Maximum number of example rows attached to each issue via
        ``ValidationIssue.sample``. Helpful for pinpointing the
        offending (r, t, y, ...) combination.
    """
    report = ValidationReport()
    all_tables = set(db.list_tables())

    _check_bound_inversions(db, all_tables, report, sample_rows)
    _check_emission_limits_vs_exogenous(db, all_tables, report, sample_rows)
    _check_min_share_production_sum(db, all_tables, report, sample_rows)
    _check_min_utilization_vs_availability(db, all_tables, report, sample_rows)
    _check_min_storage_vs_start(db, all_tables, report, sample_rows)
    _check_demand_without_supply(db, all_tables, report, sample_rows)
    _check_reserve_margin_without_tags(db, all_tables, report, sample_rows)
    _check_storage_without_charge_path(db, all_tables, report, sample_rows)
    _check_ccs_unbounded(db, all_tables, report, sample_rows)
    _check_fuel_mass_balance(db, all_tables, report, sample_rows)

    return report


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
# Each check follows the same pattern: early-exit if the relevant tables
# are empty or missing, join upper vs lower bounds, and emit an issue
# when a conflict is detected.

# List of (lower-table, upper-table, join-columns, description) triples.
_BOUND_PAIRS: List[Tuple[str, str, Tuple[str, ...], str]] = [
    ("TotalAnnualMinCapacity", "TotalAnnualMaxCapacity",
     ("r", "t", "y"), "annual capacity"),
    ("TotalAnnualMinCapacityInvestment", "TotalAnnualMaxCapacityInvestment",
     ("r", "t", "y"), "annual capacity investment"),
    ("TotalAnnualMinCapacityStorage", "TotalAnnualMaxCapacityStorage",
     ("r", "s", "y"), "annual storage capacity"),
    ("TotalAnnualMinCapacityInvestmentStorage",
     "TotalAnnualMaxCapacityInvestmentStorage",
     ("r", "s", "y"), "annual storage capacity investment"),
    ("TotalTechnologyAnnualActivityLowerLimit",
     "TotalTechnologyAnnualActivityUpperLimit",
     ("r", "t", "y"), "annual technology activity"),
    ("TotalTechnologyModelPeriodActivityLowerLimit",
     "TotalTechnologyModelPeriodActivityUpperLimit",
     ("r", "t"), "model-period technology activity"),
]


def _check_bound_inversions(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """Flag rows where a stored minimum exceeds the stored maximum on the
    same key. Each such row is infeasible regardless of solver."""
    for lo_tbl, hi_tbl, keys, label in _BOUND_PAIRS:
        if not {lo_tbl, hi_tbl} <= all_tables:
            continue
        if db.row_count(lo_tbl) == 0 or db.row_count(hi_tbl) == 0:
            continue
        key_list = ", ".join(f'lo."{k}"' for k in keys)
        join = " AND ".join(f'lo."{k}" = hi."{k}"' for k in keys)
        sql = (
            f"SELECT {key_list}, lo.val AS min_val, hi.val AS max_val "
            f'FROM "{lo_tbl}" lo '
            f'JOIN "{hi_tbl}" hi ON {join} '
            f"WHERE lo.val > hi.val"
        )
        bad = db.query(sql)
        if len(bad) > 0:
            report.issues.append(ValidationIssue(
                severity="error", category="bound_inversion",
                table=f"{lo_tbl} vs {hi_tbl}",
                message=(
                    f"{len(bad)} rows where {label} lower bound exceeds "
                    f"upper bound; NEMO will be infeasible."
                ),
                sample=bad.head(sample_rows),
            ))


def _check_emission_limits_vs_exogenous(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """NEMO docs call this out explicitly: annual exogenous emissions of a
    pollutant exceeding the pollutant's annual emission limit is
    infeasible. Same logic for the model-period variant."""
    if {"AnnualExogenousEmission", "AnnualEmissionLimit"} <= all_tables:
        sql = (
            "SELECT ex.r, ex.e, ex.y, ex.val AS exogenous, lim.val AS limit_val "
            "FROM AnnualExogenousEmission ex "
            "JOIN AnnualEmissionLimit lim "
            "  ON lim.r = ex.r AND lim.e = ex.e AND lim.y = ex.y "
            "WHERE ex.val > lim.val"
        )
        bad = db.query(sql)
        if len(bad) > 0:
            report.issues.append(ValidationIssue(
                severity="error", category="emission_limit",
                table="AnnualExogenousEmission vs AnnualEmissionLimit",
                message=(
                    f"{len(bad)} (r,e,y) combos where exogenous emissions "
                    f"already exceed the annual limit; NEMO will be infeasible."
                ),
                sample=bad.head(sample_rows),
            ))

    if {"ModelPeriodExogenousEmission", "ModelPeriodEmissionLimit"} <= all_tables:
        sql = (
            "SELECT ex.r, ex.e, ex.val AS exogenous, lim.val AS limit_val "
            "FROM ModelPeriodExogenousEmission ex "
            "JOIN ModelPeriodEmissionLimit lim "
            "  ON lim.r = ex.r AND lim.e = ex.e "
            "WHERE ex.val > lim.val"
        )
        bad = db.query(sql)
        if len(bad) > 0:
            report.issues.append(ValidationIssue(
                severity="error", category="emission_limit",
                table="ModelPeriodExogenousEmission vs ModelPeriodEmissionLimit",
                message=(
                    f"{len(bad)} (r,e) combos where model-period exogenous "
                    f"emissions exceed the limit; NEMO will be infeasible."
                ),
                sample=bad.head(sample_rows),
            ))


def _check_min_share_production_sum(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """MinShareProduction is a lower bound on a tech's fraction of (r, f, y)
    production (0 to 1). The sum across all techs producing fuel f must
    not exceed 1.0 — if it does, no feasible production mix exists."""
    if "MinShareProduction" not in all_tables:
        return
    if db.row_count("MinShareProduction") == 0:
        return
    sql = (
        "SELECT r, f, y, SUM(val) AS total_min_share "
        "FROM MinShareProduction GROUP BY r, f, y HAVING total_min_share > 1.000001"
    )
    bad = db.query(sql)
    if len(bad) > 0:
        report.issues.append(ValidationIssue(
            severity="error", category="share_constraints",
            table="MinShareProduction",
            message=(
                f"{len(bad)} (r,f,y) combos where minimum production "
                f"shares sum to more than 1.0; no feasible production "
                f"mix exists."
            ),
            sample=bad.head(sample_rows),
        ))


def _check_min_utilization_vs_availability(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """MinimumUtilization sets the floor on dispatch as a fraction of
    installed capacity; AvailabilityFactor is the ceiling. If the floor
    exceeds the ceiling for any (r, t, l, y), the technology can't meet
    both constraints."""
    if not {"MinimumUtilization", "AvailabilityFactor"} <= all_tables:
        return
    if db.row_count("MinimumUtilization") == 0:
        return
    sql = (
        "SELECT mu.r, mu.t, mu.l, mu.y, mu.val AS min_util, "
        "       af.val AS avail_factor "
        "FROM MinimumUtilization mu "
        "JOIN AvailabilityFactor af "
        "  ON af.r = mu.r AND af.t = mu.t AND af.l = mu.l AND af.y = mu.y "
        "WHERE mu.val > af.val"
    )
    bad = db.query(sql)
    if len(bad) > 0:
        report.issues.append(ValidationIssue(
            severity="error", category="utilization",
            table="MinimumUtilization vs AvailabilityFactor",
            message=(
                f"{len(bad)} (r,t,l,y) combos where MinimumUtilization "
                f"exceeds AvailabilityFactor; technology cannot meet both."
            ),
            sample=bad.head(sample_rows),
        ))


def _check_min_storage_vs_start(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """NEMO documents this infeasibility: if ``MinStorageCharge`` exceeds
    ``StorageLevelStart``, the model will be infeasible. This check is a
    duplicate of one in ``validate_scenario`` but repeated here so the
    infeasibility tool is self-contained."""
    if not {"MinStorageCharge", "StorageLevelStart"} <= all_tables:
        return
    if db.row_count("MinStorageCharge") == 0:
        return
    sql = (
        "SELECT msc.r, msc.s, msc.y, msc.val AS min_charge, "
        "       sls.val AS start_level "
        "FROM MinStorageCharge msc "
        "LEFT JOIN StorageLevelStart sls "
        "  ON sls.r = msc.r AND sls.s = msc.s "
        "WHERE sls.val IS NULL OR msc.val > sls.val"
    )
    bad = db.query(sql)
    if len(bad) > 0:
        report.issues.append(ValidationIssue(
            severity="error", category="storage",
            table="MinStorageCharge vs StorageLevelStart",
            message=(
                f"{len(bad)} (r,s,y) combos where MinStorageCharge exceeds "
                f"or lacks a matching StorageLevelStart; NEMO will be "
                f"infeasible."
            ),
            sample=bad.head(sample_rows),
        ))


def _check_demand_without_supply(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """If a fuel has positive demand but no technology has a non-zero
    OutputActivityRatio for it in that region, the demand cannot be met
    unless the demand is supposed to be satisfied via trade. This is an
    approximate check (trade and storage can cover some cases), so the
    severity is ``warning``, not ``error``."""
    if "OutputActivityRatio" not in all_tables:
        return

    producing_fuels: set = set()
    oar_df = db.query(
        "SELECT DISTINCT r, f FROM OutputActivityRatio WHERE val > 0"
    )
    for _, row in oar_df.iterrows():
        producing_fuels.add((row["r"], row["f"]))

    missing: List[Tuple[str, str, int, str, float]] = []

    for demand_tbl in ("SpecifiedAnnualDemand", "AccumulatedAnnualDemand"):
        if demand_tbl not in all_tables:
            continue
        if db.row_count(demand_tbl) == 0:
            continue
        df = db.query(
            f"SELECT r, f, y, val FROM {demand_tbl} WHERE val > 0"
        )
        for _, row in df.iterrows():
            if (row["r"], row["f"]) not in producing_fuels:
                missing.append(
                    (row["r"], row["f"], int(row["y"]), demand_tbl, row["val"])
                )

    if missing:
        sample = pd.DataFrame(
            missing[:sample_rows],
            columns=["r", "f", "y", "source", "demand"],
        )
        report.issues.append(ValidationIssue(
            severity="warning", category="supply_chain",
            table="OutputActivityRatio",
            message=(
                f"{len(missing)} (r,f,y) combos have positive demand but "
                f"no technology produces that fuel in that region "
                f"(trade may still satisfy demand; review manually)."
            ),
            sample=sample,
        ))


def _check_reserve_margin_without_tags(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """When ReserveMargin is set (typically > 1.0) for a region-fuel-year,
    there must be at least one technology flagged by
    ReserveMarginTagTechnology for that region-fuel-year, otherwise the
    reserve requirement cannot be met.

    The check joins the two tables; ReserveMargin in LEAP is generally
    dimensioned (r, f, y) and ReserveMarginTagTechnology is (r, t, f, y).
    """
    if "ReserveMargin" not in all_tables:
        return
    if db.row_count("ReserveMargin") == 0:
        return
    if "ReserveMarginTagTechnology" not in all_tables:
        report.issues.append(ValidationIssue(
            severity="error", category="reserve_margin",
            table="ReserveMarginTagTechnology",
            message=(
                "ReserveMargin is populated but ReserveMarginTagTechnology "
                "table is absent; reserve requirement cannot be met."
            ),
        ))
        return
    sql = (
        "SELECT rm.r, rm.f, rm.y, rm.val AS margin "
        "FROM ReserveMargin rm "
        "LEFT JOIN ("
        "  SELECT DISTINCT r, f, y FROM ReserveMarginTagTechnology WHERE val > 0"
        ") tag ON tag.r = rm.r AND tag.f = rm.f AND tag.y = rm.y "
        "WHERE rm.val > 0 AND tag.r IS NULL"
    )
    bad = db.query(sql)
    if len(bad) > 0:
        report.issues.append(ValidationIssue(
            severity="error", category="reserve_margin",
            table="ReserveMargin vs ReserveMarginTagTechnology",
            message=(
                f"{len(bad)} (r,f,y) combos have positive ReserveMargin "
                f"but no technology is tagged; infeasible."
            ),
            sample=bad.head(sample_rows),
        ))


def _check_storage_without_charge_path(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """A storage with residual capacity > 0 or with an active charge
    constraint needs at least one technology flagged in
    TechnologyToStorage (can charge it) and one in TechnologyFromStorage
    (can discharge it). Missing either path makes the storage unusable."""
    storages = db.query("SELECT val FROM STORAGE")["val"].tolist()
    if not storages:
        return

    def _tagged(tbl: str) -> set:
        if tbl not in all_tables or db.row_count(tbl) == 0:
            return set()
        return set(db.query(f'SELECT DISTINCT r, s FROM "{tbl}"')
                   .apply(tuple, axis=1))

    to_storage = _tagged("TechnologyToStorage")
    from_storage = _tagged("TechnologyFromStorage")

    issues: List[Tuple[str, str, str]] = []

    # Storages referenced in either NodalDistributionStorageCapacity or
    # ResidualStorageCapacity with val > 0 are "in use" somewhere.
    for src_tbl in ("ResidualStorageCapacity", "NodalDistributionStorageCapacity"):
        if src_tbl not in all_tables or db.row_count(src_tbl) == 0:
            continue
        cols = db.table_columns(src_tbl)
        if "s" not in cols or "r" not in cols:
            continue
        df = db.query(
            f'SELECT DISTINCT r, s FROM "{src_tbl}" WHERE val > 0'
        )
        for _, row in df.iterrows():
            key = (row["r"], row["s"])
            missing_direction = []
            if key not in to_storage:
                missing_direction.append("no TechnologyToStorage (cannot charge)")
            if key not in from_storage:
                missing_direction.append("no TechnologyFromStorage (cannot discharge)")
            if missing_direction:
                issues.append((row["r"], row["s"], "; ".join(missing_direction)))

    # De-duplicate
    unique = sorted(set(issues))
    if unique:
        sample = pd.DataFrame(
            unique[:sample_rows], columns=["r", "s", "missing"],
        )
        report.issues.append(ValidationIssue(
            severity="warning", category="storage",
            table="TechnologyToStorage / TechnologyFromStorage",
            message=(
                f"{len(unique)} (r,s) combos have residual or distributed "
                f"storage capacity but lack a charge or discharge path "
                f"via tagged technologies."
            ),
            sample=sample,
        ))


def _check_ccs_unbounded(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """Mirror the unbounded-profit check in validate_scenario so the
    infeasibility report is self-contained. Duplicate findings are
    harmless; users running both tools expect consistent output.

    The logic is: (r, t, e) combos where a technology has negative
    EmissionActivityRatio on an emission with negative EmissionsPenalty,
    and no TotalAnnualMaxCapacity or activity upper bound exists to keep
    deployment finite.
    """
    if not {"EmissionActivityRatio", "EmissionsPenalty"} <= all_tables:
        return
    neg_ear = db.query(
        "SELECT DISTINCT r, t, e FROM EmissionActivityRatio WHERE val < 0"
    )
    if len(neg_ear) == 0:
        return
    neg_pen = db.query(
        "SELECT DISTINCT r, e FROM EmissionsPenalty WHERE val < 0"
    )
    if len(neg_pen) == 0:
        return
    risky = neg_ear.merge(neg_pen, on=["r", "e"], how="inner")
    if len(risky) == 0:
        return

    bounded: set = set()
    for bound_tbl in (
        "TotalAnnualMaxCapacity",
        "TotalAnnualMaxCapacityInvestment",
        "TotalTechnologyAnnualActivityUpperLimit",
        "TotalTechnologyModelPeriodActivityUpperLimit",
    ):
        if bound_tbl in all_tables and db.row_count(bound_tbl) > 0:
            df = db.query(f'SELECT DISTINCT r, t FROM "{bound_tbl}"')
            bounded.update((row["r"], row["t"]) for _, row in df.iterrows())

    unbounded = risky[~risky[["r", "t"]].apply(tuple, axis=1).isin(bounded)]
    if len(unbounded) > 0:
        report.issues.append(ValidationIssue(
            severity="warning", category="unbounded",
            table="EmissionActivityRatio vs EmissionsPenalty",
            message=(
                f"{len(unbounded)} (r,t,e) combos combine negative "
                f"emission factor and negative emission penalty without "
                f"a capacity or activity upper bound. NEMO may become "
                f"unbounded (infinite profit)."
            ),
            sample=unbounded.head(sample_rows),
        ))


_SLACK_RESIDUAL_THRESHOLD = 1e9


def _nan_safe(v, default=0.0):
    """Return default when v is None or NaN; otherwise v."""
    if v is None:
        return default
    if isinstance(v, float) and (v != v):  # NaN != NaN
        return default
    return v


def _check_fuel_mass_balance(
    db: NemoDB, all_tables: set,
    report: ValidationReport, sample_rows: int,
) -> None:
    """Mass-balance audit per (region, fuel, year).

    Compare total forced demand for fuel f in (r, y) against total maximum
    supply for fuel f in (r, y). When demand > supply, the model is infeasible
    on a constraint somewhere in the fuel-balance chain, and CPLEX presolve
    reports "Implied bounds make row 'cN' infeasible".

    forced_demand(r, f, y) =
        SpecifiedAnnualDemand(r, f, y)
        + AccumulatedAnnualDemand(r, f, y)
        + Σ over consumer techs t of [ min_activity(r, t, y) × max_IAR(r, t, f, y) ]

      where min_activity(r, t, y) =
            MAX( MAX_l(MinimumUtilization[r,t,l,y]) × ResidualCapacity × C2A,
                 TotalTechnologyAnnualActivityLowerLimit[r,t,y] )

    max_supply(r, f, y) =
        Σ over producer techs t of [ max_activity(r, t, y) × max_OAR(r, t, f, y) ]
        + ∞ if any producer is unbounded

      where max_activity(r, t, y) =
            +∞ if ResidualCapacity ≥ 1e9 (slack tech)
            +∞ if no upper bound exists (uncapped investment path)
            TotalTechnologyAnnualActivityUpperLimit[r,t,y] when present
            TotalAnnualMaxCapacity × C2A otherwise (rough proxy)

    The check subsumes:
      - demand_without_supply (max_supply = 0, demand > 0)
      - MinimumUtilization × ResidualCapacity × IAR vs feedstock-cap chain
      - TotalTechnologyAnnualActivityLowerLimit-without-build-path

    Output names contributing consumer and producer techs per (r, f, y) so
    the targeted LEAP probe in Stage 4 (CLAUDE.md §8) knows exactly which
    branches to read.

    Designed 2026-05-11 to replace shape-by-shape checks (the earlier
    `_check_min_util_feedstock_demand_vs_supply`) with a single general
    audit, after the user pointed out that growing a check library is not
    a method.
    """
    needed = {"InputActivityRatio", "OutputActivityRatio"}
    if not needed <= all_tables:
        return
    if (db.row_count("InputActivityRatio") == 0
            and db.row_count("OutputActivityRatio") == 0):
        return

    # --- Forced minimum activity per (r, t, y) ----------------------------
    # MU × ResCap × C2A floor
    mu_floor = pd.DataFrame(columns=["r", "t", "y", "floor"])
    if {"MinimumUtilization", "ResidualCapacity"} <= all_tables:
        sql = (
            "SELECT mu.r, mu.t, mu.y, "
            "       MAX(mu.val) * rc.val * COALESCE(c2a.val, 1.0) AS floor "
            "FROM MinimumUtilization mu "
            "JOIN ResidualCapacity rc "
            "  ON rc.r = mu.r AND rc.t = mu.t AND rc.y = mu.y "
            "LEFT JOIN CapacityToActivityUnit c2a "
            "  ON c2a.r = mu.r AND c2a.t = mu.t "
            "WHERE mu.val > 0 AND rc.val > 0 "
            "GROUP BY mu.r, mu.t, mu.y"
        )
        mu_floor = db.query(sql)

    # TotalTechnologyAnnualActivityLowerLimit floor
    ll_floor = pd.DataFrame(columns=["r", "t", "y", "floor"])
    if "TotalTechnologyAnnualActivityLowerLimit" in all_tables:
        ll_floor = db.query(
            "SELECT r, t, y, val AS floor "
            "FROM TotalTechnologyAnnualActivityLowerLimit WHERE val > 0"
        )

    if len(mu_floor) == 0 and len(ll_floor) == 0:
        forced_act: dict = {}
    else:
        combined = pd.concat([mu_floor, ll_floor], ignore_index=True)
        # Take the binding (largest) floor per (r, t, y)
        per_rty = combined.groupby(["r", "t", "y"])["floor"].max()
        forced_act = {(r, t, y): v for (r, t, y), v in per_rty.items()}

    # --- IAR and OAR per (r, t, f, y), max across modes ------------------
    iar = db.query(
        "SELECT r, t, f, y, MAX(val) AS iar "
        "FROM InputActivityRatio WHERE val > 0 "
        "GROUP BY r, t, f, y"
    )
    oar = db.query(
        "SELECT r, t, f, y, MAX(val) AS oar "
        "FROM OutputActivityRatio WHERE val > 0 "
        "GROUP BY r, t, f, y"
    )

    # --- Supply-side bounds per (r, t, y) --------------------------------
    def _index_rty(table: str) -> dict:
        if table not in all_tables or db.row_count(table) == 0:
            return {}
        return {
            (row.r, row.t, row.y): _nan_safe(row.val)
            for row in db.query(
                f'SELECT r, t, y, val FROM "{table}"'
            ).itertuples(index=False)
        }

    residuals = _index_rty("ResidualCapacity")
    act_ul = _index_rty("TotalTechnologyAnnualActivityUpperLimit")
    max_cap = _index_rty("TotalAnnualMaxCapacity")

    c2a_map: dict = {}
    if "CapacityToActivityUnit" in all_tables:
        c2a_map = {
            (row.r, row.t): _nan_safe(row.val, 1.0)
            for row in db.query(
                "SELECT r, t, val FROM CapacityToActivityUnit"
            ).itertuples(index=False)
        }

    def max_activity(r: str, t: str, y) -> float:
        """Upper bound on annual activity for (r, t, y). +inf if uncapped."""
        resid = residuals.get((r, t, y), 0.0)
        if resid >= _SLACK_RESIDUAL_THRESHOLD:
            return float("inf")
        if (r, t, y) in act_ul:
            return act_ul[(r, t, y)]
        if (r, t, y) in max_cap:
            return max_cap[(r, t, y)] * c2a_map.get((r, t), 1.0)
        return float("inf")

    # --- Exogenous demand per (r, f, y) ----------------------------------
    demand_map: dict = {}
    for table in ("SpecifiedAnnualDemand", "AccumulatedAnnualDemand"):
        if table not in all_tables:
            continue
        df = db.query(f"SELECT r, f, y, val FROM \"{table}\" WHERE val > 0")
        for row in df.itertuples(index=False):
            demand_map[(row.r, row.f, row.y)] = (
                demand_map.get((row.r, row.f, row.y), 0.0) + _nan_safe(row.val)
            )

    # --- Aggregate forced demand per (r, f, y), tag contributing consumers
    forced_demand: dict = dict(demand_map)
    consumer_contribs: dict = {}
    if len(iar) > 0:
        for row in iar.itertuples(index=False):
            floor = forced_act.get((row.r, row.t, row.y), 0.0)
            if floor <= 0:
                continue
            contrib = floor * row.iar
            key = (row.r, row.f, row.y)
            forced_demand[key] = forced_demand.get(key, 0.0) + contrib
            consumer_contribs.setdefault(key, []).append((row.t, contrib))

    # --- Aggregate max supply per (r, f, y), tag contributing producers --
    max_supply: dict = {}
    producer_contribs: dict = {}
    if len(oar) > 0:
        for row in oar.itertuples(index=False):
            key = (row.r, row.f, row.y)
            max_act = max_activity(row.r, row.t, row.y)
            if max_act == float("inf"):
                max_supply[key] = float("inf")
                producer_contribs.setdefault(key, []).append(
                    (row.t, float("inf"))
                )
            else:
                contrib = max_act * row.oar
                if max_supply.get(key) != float("inf"):
                    max_supply[key] = max_supply.get(key, 0.0) + contrib
                producer_contribs.setdefault(key, []).append((row.t, contrib))

    # --- Find binds ------------------------------------------------------
    findings: List[dict] = []
    for key, demand in forced_demand.items():
        if demand <= 0:
            continue
        supply = max_supply.get(key, 0.0)
        if supply == float("inf"):
            continue
        if demand > supply * 1.001:  # 0.1% tolerance for FP noise
            r, fuel, y = key
            consumers = consumer_contribs.get(key, [])
            producers = producer_contribs.get(key, [])
            # Top 3 contributors, sorted by magnitude
            consumers.sort(key=lambda kv: -kv[1])
            producers.sort(key=lambda kv: -(kv[1] if kv[1] != float("inf") else 0))
            findings.append({
                "r": r, "f": fuel, "y": y,
                "forced_demand": demand,
                "max_supply": supply,
                "shortfall_ratio": demand / max(supply, 1e-12),
                "consumers": ",".join(f"{t}:{v:.3g}" for t, v in consumers[:3]),
                "producers": ",".join(f"{t}:{v:.3g}" for t, v in producers[:3]),
            })

    if findings:
        findings.sort(key=lambda d: -d["shortfall_ratio"])
        sample = pd.DataFrame(findings[:sample_rows])
        report.issues.append(ValidationIssue(
            severity="error", category="fuel_balance",
            table="(r, f, y) mass balance audit",
            message=(
                f"{len(findings)} (r, f, y) triples where total forced demand "
                f"exceeds total max supply. Forced demand = "
                f"SpecifiedAnnualDemand + AccumulatedAnnualDemand + sum over "
                f"consumer techs of [min_activity x max_IAR], where "
                f"min_activity = max(MU x ResCap x C2A, ActivityLowerLimit). "
                f"Max supply = sum over producer techs of [max_activity x "
                f"max_OAR], with slack/uncapped producers treated as +inf. "
                f"CPLEX presolve will report 'implied bounds make row "
                f"infeasible' on a row in this fuel balance. The 'consumers' "
                f"and 'producers' columns name the techs to probe in LEAP."
            ),
            sample=sample,
        ))


# ---------------------------------------------------------------------------
# Combined report
# ---------------------------------------------------------------------------
def check_scenario(
    db: NemoDB,
    sample_rows: int = 5,
    context: "LeapAreaContext | None" = None,  # type: ignore[name-defined]
) -> ValidationReport:
    """One-stop check that runs both :func:`validate_scenario` and
    :func:`find_infeasibilities`, merges their findings, and de-duplicates
    identical issues. This is the recommended default for handing a
    freshly-built scenario database to an analyst.

    When ``context`` is supplied, validate_scenario additionally compares
    the nemo.cfg ``varstosave`` list against the populated v* tables.
    """
    from .validate import validate_scenario

    report = ValidationReport()
    v = validate_scenario(db, sample_rows=sample_rows, context=context)
    f = find_infeasibilities(db, sample_rows=sample_rows)

    seen: set = set()
    for issue in list(v.issues) + list(f.issues):
        # Dedup key collapses the two reports' overlapping checks
        # (e.g. both flag MinStorageCharge > StorageLevelStart).
        key = (issue.severity, issue.category, issue.table, issue.message)
        if key in seen:
            continue
        seen.add(key)
        report.issues.append(issue)
    return report
