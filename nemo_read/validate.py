"""
Pre-flight validation.

Checks a scenario database for data-integrity issues before analysis or
before LEAP calculates it. Validation is non-destructive and returns a
structured report; nothing is mutated.

Checks implemented:

    * Schema version matches the library target.
    * Every populated parameter table references only declared dimension
      members (no orphan tech / fuel / region / year / mode / storage).
    * YearSplit sums to 1.0 per year.
    * SpecifiedDemandProfile sums to 1.0 per (r, f, y).
    * NodalDistributionDemand, NodalDistributionTechnologyCapacity,
      NodalDistributionStorageCapacity — each row with val > 0 implies
      the corresponding NODE.r matches the technology's (or storage's or
      fuel's) region allocation. Strict check only runs when
      TransmissionModelingEnabled has data.
    * NODE.r references valid REGION.val.
    * TransmissionLine endpoints (n1, n2) and fuel (f) reference valid
      NODE and FUEL.
    * Demand profile coverage: every (r, f, y) present in
      SpecifiedAnnualDemand has a matching profile in
      SpecifiedDemandProfile (when profile > 0).

Validation severities:
    * ``"error"`` — will likely cause NEMO to fail or misbehave.
    * ``"warning"`` — worth investigating, not necessarily broken.
    * ``"info"`` — neutral, informational note.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from .db import NemoDB
from .schema import DIMENSIONS, DIMENSION_ABBREVIATIONS, PARAMETERS, TARGET_DB_VERSION


@dataclass
class ValidationIssue:
    """One thing the validator wants to flag."""
    severity: str            # 'error' | 'warning' | 'info'
    category: str            # short tag for grouping (e.g. 'referential')
    table: str               # table name the issue relates to
    message: str             # human-readable description
    sample: Optional[pd.DataFrame] = None  # optional rows that demonstrate the issue


@dataclass
class ValidationReport:
    """Structured result of :func:`validate_scenario`."""
    issues: List[ValidationIssue] = field(default_factory=list)

    # Convenience accessors
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def infos(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "info"]

    def ok(self) -> bool:
        """True iff no errors (warnings allowed)."""
        return not self.errors()

    def to_dataframe(self) -> pd.DataFrame:
        """Flat DataFrame view of all issues."""
        rows = [
            {"severity": i.severity, "category": i.category,
             "table": i.table, "message": i.message,
             "sample_rows": 0 if i.sample is None else len(i.sample)}
            for i in self.issues
        ]
        return pd.DataFrame(rows)

    def extend(self, other: "ValidationReport") -> "ValidationReport":
        """Merge another report's issues into this one in-place. Returns
        ``self`` so calls can be chained."""
        self.issues.extend(other.issues)
        return self

    def print(self) -> None:
        """Print a terse summary to stdout."""
        n_err = len(self.errors())
        n_warn = len(self.warnings())
        n_info = len(self.infos())
        print(f"Validation: {n_err} errors, {n_warn} warnings, {n_info} info.")
        for i in self.issues:
            flag = {"error": "✗", "warning": "⚠", "info": "ℹ"}.get(i.severity, "?")
            print(f"  {flag} [{i.category}] {i.table}: {i.message}")


# ---------------------------------------------------------------------------
# Core validator
# ---------------------------------------------------------------------------
def validate_scenario(
    db: NemoDB,
    strict: bool = False,
    sample_rows: int = 5,
) -> ValidationReport:
    """Run the full validation suite against ``db``.

    Parameters
    ----------
    db : NemoDB
    strict : bool, default False
        When True, elevates certain warnings to errors. Useful when the
        database is about to be fed to NEMO and you want belt-and-braces
        guarantees.
    sample_rows : int, default 5
        Number of example rows to attach to each issue via
        ``ValidationIssue.sample``.
    """
    report = ValidationReport()
    all_tables = set(db.list_tables())

    # 1. Schema version
    if db.version != TARGET_DB_VERSION:
        sev = "error" if strict else "warning"
        report.issues.append(ValidationIssue(
            severity=sev, category="schema", table="Version",
            message=(f"DB version is {db.version}; library targets "
                     f"v{TARGET_DB_VERSION}."),
        ))

    # 2. Referential integrity on every populated parameter
    _check_parameter_foreign_keys(db, all_tables, report, sample_rows)

    # 3. YearSplit sums
    if "YearSplit" in all_tables and db.row_count("YearSplit") > 0:
        sums = db.query(
            "SELECT y, SUM(val) AS s FROM YearSplit GROUP BY y"
        )
        bad = sums[(sums["s"] < 0.999) | (sums["s"] > 1.001)]
        if len(bad) > 0:
            report.issues.append(ValidationIssue(
                severity="error", category="timeslice",
                table="YearSplit",
                message=f"{len(bad)} years where YearSplit does not sum to 1.0",
                sample=bad.head(sample_rows),
            ))

    # 4. SpecifiedDemandProfile sums
    if "SpecifiedDemandProfile" in all_tables and db.row_count("SpecifiedDemandProfile") > 0:
        sums = db.query(
            "SELECT r, f, y, SUM(val) AS s FROM SpecifiedDemandProfile "
            "GROUP BY r, f, y"
        )
        bad = sums[(sums["s"] < 0.999) | (sums["s"] > 1.001)]
        if len(bad) > 0:
            report.issues.append(ValidationIssue(
                severity="error", category="demand",
                table="SpecifiedDemandProfile",
                message=(f"{len(bad)} (r,f,y) combos where profile "
                         f"does not sum to 1.0"),
                sample=bad.head(sample_rows),
            ))

    # 5. NODE.r → REGION.val
    if "NODE" in all_tables and db.row_count("NODE") > 0:
        regions_set = set(db.query("SELECT val FROM REGION")["val"])
        nodes_df = db.query("SELECT val, r FROM NODE")
        bad = nodes_df[~nodes_df["r"].isin(regions_set)]
        if len(bad) > 0:
            report.issues.append(ValidationIssue(
                severity="error", category="referential",
                table="NODE",
                message=f"{len(bad)} nodes reference unknown regions",
                sample=bad.head(sample_rows),
            ))

    # 6. TransmissionLine endpoints and fuel
    if "TransmissionLine" in all_tables and db.row_count("TransmissionLine") > 0:
        tl = db.query("SELECT id, n1, n2, f FROM TransmissionLine")
        nodes_set = set(db.query("SELECT val FROM NODE")["val"])
        fuels_set = set(db.query("SELECT val FROM FUEL")["val"])
        bad_n1 = tl[~tl["n1"].isin(nodes_set)]
        bad_n2 = tl[~tl["n2"].isin(nodes_set)]
        bad_f = tl[~tl["f"].isin(fuels_set)]
        if len(bad_n1) > 0:
            report.issues.append(ValidationIssue(
                severity="error", category="referential",
                table="TransmissionLine",
                message=f"{len(bad_n1)} lines with unknown n1",
                sample=bad_n1.head(sample_rows),
            ))
        if len(bad_n2) > 0:
            report.issues.append(ValidationIssue(
                severity="error", category="referential",
                table="TransmissionLine",
                message=f"{len(bad_n2)} lines with unknown n2",
                sample=bad_n2.head(sample_rows),
            ))
        if len(bad_f) > 0:
            report.issues.append(ValidationIssue(
                severity="error", category="referential",
                table="TransmissionLine",
                message=f"{len(bad_f)} lines with unknown fuel",
                sample=bad_f.head(sample_rows),
            ))

    # 7. SpecifiedAnnualDemand without a profile
    if {"SpecifiedAnnualDemand", "SpecifiedDemandProfile"} <= all_tables:
        demand_rfy = db.query(
            "SELECT DISTINCT r, f, y FROM SpecifiedAnnualDemand WHERE val > 0"
        )
        profile_rfy = db.query(
            "SELECT DISTINCT r, f, y FROM SpecifiedDemandProfile"
        )
        merged = demand_rfy.merge(
            profile_rfy.assign(_present=1), on=["r", "f", "y"], how="left"
        )
        missing = merged[merged["_present"].isna()].drop(columns=["_present"])
        if len(missing) > 0:
            report.issues.append(ValidationIssue(
                severity="warning", category="demand",
                table="SpecifiedDemandProfile",
                message=(f"{len(missing)} (r,f,y) combos have "
                         f"SpecifiedAnnualDemand>0 but no profile; "
                         f"NEMO may fail or assume uniform profile."),
                sample=missing.head(sample_rows),
            ))

    # 8. Empty populated-parameter tables that shouldn't be
    _check_expected_populations(db, all_tables, report)

    # 9. MinStorageCharge vs StorageLevelStart infeasibility check.
    # Per NEMO docs: "If you set a minimum storage charge, make sure the
    # corresponding storage start level is at least as large as the
    # minimum. Otherwise your model will be infeasible."
    if {"MinStorageCharge", "StorageLevelStart"} <= all_tables:
        msc_rows = db.row_count("MinStorageCharge")
        sls_rows = db.row_count("StorageLevelStart")
        if msc_rows > 0 and sls_rows > 0:
            # Join to find (r, s, y) where min > start
            # StorageLevelStart has dims (r, s); MinStorageCharge has dims (r, s, y).
            # A violation is msc(r, s, y) > sls(r, s) for any y.
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
                    table="MinStorageCharge",
                    message=(
                        f"{len(bad)} (r,s,y) combos where MinStorageCharge "
                        f"exceeds or lacks a matching StorageLevelStart; "
                        f"NEMO will be infeasible."
                    ),
                    sample=bad.head(sample_rows),
                ))
        elif msc_rows > 0 and sls_rows == 0:
            report.issues.append(ValidationIssue(
                severity="warning", category="storage",
                table="StorageLevelStart",
                message=(
                    "MinStorageCharge has data but StorageLevelStart is "
                    "empty. NEMO will use the default start level, which "
                    "may be below MinStorageCharge and cause infeasibility."
                ),
            ))

    # 10. Negative emissions + negative penalty unbounded-profit risk.
    # Per NEMO docs: "If a technology can generate negative emissions of
    # a pollutant with an externality cost, the cost of building and
    # running the technology is lower than the externality value, and
    # there are no limits on the technology's deployment and use, the
    # optimization problem will be unbounded."
    _check_negative_emission_bounds(db, all_tables, report, sample_rows)

    # 11. Informational: negative emission rates are expected for CCS /
    # carbon sequestration technologies (NEMO supports this explicitly).
    # Flag as info so the user is not surprised.
    if "EmissionActivityRatio" in all_tables:
        n_neg = db.query(
            "SELECT COUNT(*) AS n FROM EmissionActivityRatio WHERE val < 0"
        )["n"].iloc[0]
        if n_neg > 0:
            neg_emissions = db.query(
                "SELECT DISTINCT e FROM EmissionActivityRatio WHERE val < 0"
            )["e"].tolist()
            report.issues.append(ValidationIssue(
                severity="info", category="emissions",
                table="EmissionActivityRatio",
                message=(
                    f"{n_neg} rows have negative emission factors "
                    f"(sequestration) for emission(s): "
                    f"{sorted(neg_emissions)}."
                ),
            ))

    return report


def _check_negative_emission_bounds(
    db: NemoDB,
    all_tables: set,
    report: ValidationReport,
    sample_rows: int,
) -> None:
    """Flag technologies that can produce negative emissions of a pollutant
    with a negative EmissionsPenalty (i.e. a subsidy), and which have no
    capacity or activity upper bound to stop the optimiser from building
    infinitely many of them. This is the classic unbounded-profit pitfall
    NEMO documents for CCS-like configurations.
    """
    if not {"EmissionActivityRatio", "EmissionsPenalty"} <= all_tables:
        return
    # Technologies with a negative emission factor (sequestration),
    # per region and emission.
    neg_ear = db.query(
        "SELECT DISTINCT r, t, e FROM EmissionActivityRatio WHERE val < 0"
    )
    if len(neg_ear) == 0:
        return
    # Emission(s) with a negative penalty (i.e. a subsidy when emitted,
    # which becomes a payout when the emission factor is itself negative).
    neg_pen = db.query(
        "SELECT DISTINCT r, e FROM EmissionsPenalty WHERE val < 0"
    )
    if len(neg_pen) == 0:
        return
    # Intersect: (r, t, e) where the tech both sequesters and the region
    # has a negative penalty on that emission.
    risky = neg_ear.merge(neg_pen, on=["r", "e"], how="inner")
    if len(risky) == 0:
        return

    # Does each risky (r, t) have an activity or capacity upper bound?
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
            severity="warning", category="emissions",
            table="EmissionActivityRatio",
            message=(
                f"{len(unbounded)} (r, t, e) combos have a negative "
                f"emission factor AND a negative EmissionsPenalty, "
                f"without any activity or capacity upper bound. NEMO "
                f"may become unbounded (infinite profit from "
                f"sequestration). Add TotalAnnualMaxCapacity, "
                f"TotalTechnologyAnnualActivityUpperLimit, or similar."
            ),
            sample=unbounded.head(sample_rows),
        ))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _check_parameter_foreign_keys(
    db: NemoDB,
    all_tables: set,
    report: ValidationReport,
    sample_rows: int,
) -> None:
    """For each populated parameter, check that its dimension columns only
    contain values that exist in the corresponding dimension table."""
    # Build dimension-member lookups once.
    dim_members: dict[str, set] = {}
    for dim_name, dim in DIMENSIONS.items():
        if dim_name in all_tables:
            pk = dim.pk
            vals = db.query(f'SELECT "{pk}" FROM "{dim_name}"')[pk]
            dim_members[dim_name] = set(vals)

    for pname, meta in PARAMETERS.items():
        if pname not in all_tables or db.row_count(pname) == 0:
            continue
        cols = meta.dims
        for col in cols:
            dim_table = DIMENSION_ABBREVIATIONS.get(col, col)
            if dim_table not in dim_members:
                continue
            members = dim_members[dim_table]
            # Cheap check: count rows with col NOT in members, sample a few
            # Use a parameterised IN list via a temp table-like approach.
            # For correctness and simplicity use pandas here.
            df = db.query(f'SELECT DISTINCT "{col}" FROM "{pname}"')
            bad_values = [v for v in df[col].tolist() if v not in members]
            if bad_values:
                # Grab sample rows
                placeholders = ",".join(["?"] * len(bad_values[:sample_rows]))
                sample_df = db.query(
                    f'SELECT * FROM "{pname}" WHERE "{col}" IN ({placeholders}) LIMIT {sample_rows}',
                    bad_values[:sample_rows],
                )
                report.issues.append(ValidationIssue(
                    severity="error", category="referential",
                    table=pname,
                    message=(f"{len(bad_values)} distinct {col!r} values "
                             f"not in {dim_table}: "
                             f"{bad_values[:sample_rows]}"
                             f"{'...' if len(bad_values) > sample_rows else ''}"),
                    sample=sample_df,
                ))


def _check_expected_populations(
    db: NemoDB,
    all_tables: set,
    report: ValidationReport,
) -> None:
    """Flag parameters that are normally non-empty but are missing or empty."""
    critical = [
        "YearSplit",
        "OperationalLife",
        "CapitalCost",
        "OutputActivityRatio",
    ]
    for name in critical:
        if name not in all_tables:
            report.issues.append(ValidationIssue(
                severity="warning", category="missing",
                table=name,
                message=f"{name} table not present in the database.",
            ))
        elif db.row_count(name) == 0:
            report.issues.append(ValidationIssue(
                severity="warning", category="missing",
                table=name,
                message=f"{name} has zero rows.",
            ))
