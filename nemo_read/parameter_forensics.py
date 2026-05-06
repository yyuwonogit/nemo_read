"""
Parameter forensics — Stages 4 and 5 of the infeasibility-resolution pipeline.

When the solver pins a column (Stage 3 — see :mod:`lp_column_decode`) we know
*which* JuMP variable is bound, but not *why* the surrounding data forces it
there.  This module is the second eye: it inspects the data clusters that
touch the pinned variable, classifies each cluster's pattern, separates
likely export bugs from intentional modelling, and emits ranked placeholder
patches the user can apply to test each hypothesis.

Pipeline placement::

    Stage 1  Pre-flight        validate_scenario + find_infeasibilities
    Stage 2  Solver run        LEAP/NEMO/CPLEX
    Stage 3  Triage            decode_lp_column   (lp_column_decode)
    Stage 4  Forensics         classify_parameter / forensics_for_pinned_variable  ← here
    Stage 5  Placeholders      propose_placeholders                                 ← here
    Stage 6  Diagnostic test   user applies top placeholder, re-runs Stage 2
    Stage 7  Probe brief       emit_probe_brief   (probe_brief)
    Stage 8  LEAP COM probing  human + LEAP open
    Stage 9  Real-fix design   informed by Stage 4 + 6 + 8
    Stage 10 Patch injection   inject_to_leap.py
    Stage 11 Verification      loop back to Stage 1

Six detectors run on every ``(r, t)`` cluster of the parameter under
inspection:

  - ``algebraic_of(other)``        — fits ``MU = AF``, ``MU = AF²``,
                                      ``MU = α·AF + β`` against companion
                                      parameters; catches export bugs that
                                      reuse another variable's value.
  - ``broadcast_across_regions``   — same value(s) across all regions ⇒
                                      the parameter lives at tech-template
                                      scope (parent process branch).
  - ``cross_parameter_broadcast``  — extends the above by checking whether
                                      *other* parameters of the same tech
                                      are also broadcast; distinguishes
                                      tech-template bugs from
                                      variable-specific accidents.
  - ``year_split``                 — partitions rows by year, reports per-
                                      cluster sub-pattern; catches the
                                      "bug-baseline + intentional ramp"
                                      mixture.
  - ``small_denom_fraction``       — tests ``Fraction(v).limit_denominator``
                                      over ``{7, 10, 12, 13, 14, 24, 30, 52,
                                      365}``; catches operating-days/week
                                      style intentional values.
  - ``varies_per_timeslice_only``  — flags load-shape-driven values.

Each detector returns a :class:`DetectionResult`.  Per cluster, all
detectors run; the cluster's :attr:`Cluster.detections` is the full battery
result and :attr:`Cluster.summary` collapses it to a single ``"intent"`` /
``"bug"`` / ``"unknown"`` verdict using the conservative rule:

  - any detector flagged ``intent`` → cluster is intent (preserve)
  - all flagged detectors are ``bug`` → cluster is bug (placeholder candidate)
  - otherwise → unknown (manual review or LEAP probe needed)

Stage 5 turns each ``bug`` or ``unknown`` cluster into a
:class:`PlaceholderProposal` whose ``rows`` are ready to drop into the
existing ``canonical_leap_inputs.csv`` format used by
``mailbox/.../inject_to_leap.py``.  Proposals are sorted lexicographically
by ``(blast_radius, -confidence, reverse_difficulty)`` so the user always
gets the smallest, most-confident, most-reversible test first.

Public API:
    Cluster, DetectionResult, ForensicReport, PlaceholderProposal,
    classify_parameter, forensics_for_pinned_variable, propose_placeholders,
    PLACEHOLDER_SENTINEL, VARIABLE_TO_CANDIDATE_PARAMS
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from .db import NemoDB
from .lp_column_decode import ColumnIdentity


PLACEHOLDER_SENTINEL = "PLACEHOLDER"
"""Marker placed in the CSV ``data_confidence`` column for placeholder rows.

The injector (mailbox/.../inject_to_leap.py) refuses to push rows tagged
with this sentinel unless ``--placeholder-mode`` is set; the pre-flight
validator (Stage 1) warns when the value still appears in a database, so
placeholder runs are never mistaken for real fixes.
"""

PLACEHOLDER_NOTE_PREFIX = "PLACEHOLDER (Stage 5 diagnostic): "
"""Required prefix on the ``note`` column for placeholder rows."""


# --------------------------------------------------------------------------
# Variable → candidate parameter map
# --------------------------------------------------------------------------
# When forensics_for_pinned_variable() runs, we need to know which
# parameter tables reasonably constrain the pinned variable.  This map
# encodes NemoMod's constraint structure at a coarse level — enough to
# point forensics at the right tables.  Extend as new patterns surface.
VARIABLE_TO_CANDIDATE_PARAMS: Dict[str, Tuple[str, ...]] = {
    "vaccumulatednewcapacity": (
        "MinimumUtilization", "AvailabilityFactor",
        "TotalAnnualMaxCapacity", "TotalAnnualMaxCapacityInvestment",
        "TotalAnnualMinCapacity", "TotalAnnualMinCapacityInvestment",
        "ResidualCapacity",
    ),
    "vnewcapacity": (
        "TotalAnnualMaxCapacityInvestment", "TotalAnnualMinCapacityInvestment",
        "CapacityOfOneTechnologyUnit",
    ),
    "vtotalcapacityannual": (
        "TotalAnnualMaxCapacity", "TotalAnnualMinCapacity", "ResidualCapacity",
        "MinimumUtilization", "AvailabilityFactor",
    ),
    "vrateofactivity": (
        "MinimumUtilization", "AvailabilityFactor",
        "TotalTechnologyAnnualActivityUpperLimit",
        "TotalTechnologyAnnualActivityLowerLimit",
    ),
    "vdemandnn": (
        "SpecifiedAnnualDemand", "SpecifiedDemandProfile",
        "AccumulatedAnnualDemand",
    ),
}


# --------------------------------------------------------------------------
# Data containers
# --------------------------------------------------------------------------
@dataclass
class DetectionResult:
    """One detector's verdict on a cluster.

    Attributes
    ----------
    detector : str
        Name of the detector that produced this result.
    fired : bool
        True if the detector matched something on this cluster.
    confidence : float
        0..1 score for how cleanly the pattern matched.
    classification : str
        ``"intent"`` (modeller-set), ``"bug"`` (export artifact),
        ``"unknown"`` (matches but interpretation ambiguous), or
        ``"none"`` (didn't fire).
    evidence : dict
        Detector-specific evidence (matched fraction, residuals, etc.).
    """
    detector: str
    fired: bool
    confidence: float = 0.0
    classification: str = "none"
    evidence: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        if not self.fired:
            return f"<{self.detector}: none>"
        return (f"<{self.detector}: {self.classification} "
                f"conf={self.confidence:.2f}>")


@dataclass
class Cluster:
    """All rows of one parameter for one ``(r, t)`` combo.

    Carries the raw row data plus every detector's result.  ``summary``
    collapses the detector battery to a single verdict using the
    conservative rule documented at the module level.
    """
    region: str
    tech: str
    parameter: str
    rows: List[tuple]                                 # (l, y, val) or (y, val)
    detections: List[DetectionResult] = field(default_factory=list)
    region_desc: str = ""
    tech_desc: str = ""

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def summary(self) -> str:
        """One-word verdict: ``intent`` / ``bug`` / ``unknown`` / ``empty``.

        Verdict order:
          1. high-confidence bug detector (≥0.85) → ``bug`` (placeholder
             candidate)
          2. any intent detector → ``intent`` (preserve)
          3. low-confidence bug or unknown detector → ``unknown``
          4. nothing fired → ``empty``
        """
        fired = [d for d in self.detections if d.fired]
        if not fired:
            return "empty" if not self.rows else "unknown"
        bug_strong = [d for d in fired
                      if d.classification == "bug" and d.confidence >= 0.85]
        if bug_strong:
            return "bug"
        if any(d.classification == "intent" for d in fired):
            return "intent"
        if all(d.classification == "bug" for d in fired):
            return "bug"
        return "unknown"

    def __repr__(self) -> str:
        return (f"<Cluster {self.parameter}[{self.region},{self.tech}]: "
                f"{self.summary} ({self.n_rows} rows, "
                f"{sum(1 for d in self.detections if d.fired)} detectors fired)>")


@dataclass
class ForensicReport:
    """All clusters for one parameter inspection.

    Iterate ``clusters`` directly, or use the helper accessors to filter
    by verdict.  Pass the report to :func:`propose_placeholders` to get
    Stage 5 output.
    """
    parameter: str
    clusters: List[Cluster] = field(default_factory=list)
    related_params: Tuple[str, ...] = ()

    def by_verdict(self, verdict: str) -> List[Cluster]:
        """Return clusters whose ``summary`` equals ``verdict``."""
        return [c for c in self.clusters if c.summary == verdict]

    def summary_counts(self) -> Dict[str, int]:
        """Count of clusters per verdict — quick overview."""
        out: Dict[str, int] = defaultdict(int)
        for c in self.clusters:
            out[c.summary] += 1
        return dict(out)

    def __repr__(self) -> str:
        return (f"<ForensicReport {self.parameter}: "
                f"{len(self.clusters)} clusters, {self.summary_counts()}>")


@dataclass
class PlaceholderProposal:
    """One Stage-5 placeholder patch proposal — a self-contained test."""
    cluster: Cluster
    rows: List[dict]                            # CSV-row dicts
    real_fix_prompt: str
    blast_radius: int                           # number of rows it touches
    confidence: float                           # 0..1, higher = more sure
    reverse_difficulty: int                     # 1=trivial, 5=hard
    rationale: str

    @property
    def sort_key(self) -> tuple:
        """Lex sort: smallest blast → highest confidence → easiest reverse."""
        return (self.blast_radius, -self.confidence, self.reverse_difficulty)

    def __repr__(self) -> str:
        return (f"<Placeholder for {self.cluster.parameter}"
                f"[{self.cluster.region},{self.cluster.tech}]: "
                f"{self.blast_radius} rows, conf={self.confidence:.2f}>")


# --------------------------------------------------------------------------
# Detectors — pure functions over a Cluster's rows
# --------------------------------------------------------------------------
EPS = 1e-9
SMALL_DENOMINATORS = (7, 10, 12, 13, 14, 24, 30, 52, 365)


def _algebraic_of(cluster: Cluster, companion_rows: List[tuple]) -> DetectionResult:
    """Test ``cluster.val`` against ``companion.val`` for common forms.

    Tries identity, square, complement.  Fires when at least 80% of
    aligned rows match a form; confidence = match_fraction.  This
    catches the year-split case where the bug is only in early years
    (algebraic match is partial because intentional late-year values
    diverge).
    """
    detector = "algebraic_of"
    if not cluster.rows or not companion_rows:
        return DetectionResult(detector=detector, fired=False)
    n_cluster_keys = len(cluster.rows[0]) - 1
    by_key = {}
    for row in companion_rows:
        key = row[:n_cluster_keys]
        by_key[key] = row[-1]
    aligned = []
    for row in cluster.rows:
        key = row[:n_cluster_keys]
        comp = by_key.get(key)
        if comp is not None and comp > 0:
            aligned.append((row[-1], comp))
    if not aligned:
        return DetectionResult(detector=detector, fired=False)

    forms = {
        "equal":      lambda v, c: abs(v - c) < EPS,
        "squared":    lambda v, c: abs(v - c * c) < EPS,
        "complement": lambda v, c: abs(v - (1 - c)) < EPS,
    }
    best = None  # (n_match, form_name)
    for form_name, predicate in forms.items():
        n_match = sum(1 for v, c in aligned if predicate(v, c))
        if best is None or n_match > best[0]:
            best = (n_match, form_name)
    n_match, form_name = best
    match_frac = n_match / len(aligned)
    if match_frac < 0.8:
        return DetectionResult(detector=detector, fired=False)
    # Bug-vs-intent verdict for the form
    classification = "bug" if form_name in ("equal", "squared") else "unknown"
    return DetectionResult(
        detector=detector,
        fired=True,
        confidence=match_frac,
        classification=classification,
        evidence={"form": form_name, "n_match": n_match,
                  "n_total": len(aligned),
                  "match_fraction": round(match_frac, 4)},
    )


def _broadcast_across_regions(cluster: Cluster,
                              same_tech_other_regions: Dict[str, List[tuple]]
                              ) -> DetectionResult:
    """Test whether the same value-set appears in 3+ regions for this tech."""
    detector = "broadcast_across_regions"
    if len(same_tech_other_regions) < 2:
        return DetectionResult(detector=detector, fired=False)
    own_sig = tuple(sorted({round(r[-1], 10) for r in cluster.rows}))
    matching = sum(
        1 for rows in same_tech_other_regions.values()
        if rows and tuple(sorted({round(r[-1], 10) for r in rows})) == own_sig
    )
    n_total = len(same_tech_other_regions)
    if matching >= max(2, n_total - 1):
        return DetectionResult(
            detector=detector,
            fired=True,
            confidence=matching / n_total,
            # Broadcast is scope evidence, not bug-vs-intent on its own.
            classification="unknown",
            evidence={"matching_regions": matching, "total_regions": n_total},
        )
    return DetectionResult(detector=detector, fired=False)


def _year_split(cluster: Cluster,
                companion_rows: Optional[List[tuple]] = None
                ) -> DetectionResult:
    """Detect a year boundary that separates two distinct sub-patterns.

    A real year-split is a STRUCTURAL break — different formula in
    different year ranges.  We don't fire when the year-to-year value
    variation is just driven by a companion (e.g. MU=AF² where AF
    happens to vary by year).  That's tested by checking whether the
    cluster ÷ companion ratio is constant across years; if it is, the
    "split" is illusory.
    """
    detector = "year_split"
    if not cluster.rows or len(cluster.rows[0]) < 3:
        return DetectionResult(detector=detector, fired=False)
    by_year: Dict[str, List[float]] = defaultdict(list)
    for row in cluster.rows:
        by_year[row[1]].append(row[-1])
    yrs = sorted(by_year.keys())
    if len(yrs) < 3:
        return DetectionResult(detector=detector, fired=False)
    medians = [(y, sorted(by_year[y])[len(by_year[y]) // 2]) for y in yrs]
    base = medians[0][1]
    knee_idx = None
    for i, (y, v) in enumerate(medians[1:], start=1):
        if abs(v - base) > max(EPS, 0.01 * abs(base)):
            knee_idx = i
            break
    if knee_idx is None:
        return DetectionResult(detector=detector, fired=False)

    # Check if the year-to-year variation is just companion-driven.
    # If cluster_val[y] / companion_val[y]² is constant → not a real split.
    if companion_rows:
        comp_by_year: Dict[str, List[float]] = defaultdict(list)
        for row in companion_rows:
            comp_by_year[row[-2] if len(row) > 2 else row[0]].append(row[-1])
        ratios = []
        for y in yrs:
            if y not in comp_by_year:
                continue
            cv = sorted(by_year[y])[len(by_year[y]) // 2]
            cmv = sorted(comp_by_year[y])[len(comp_by_year[y]) // 2]
            if cmv > 0:
                ratios.append(cv / (cmv * cmv))
        if ratios and len(ratios) >= 3:
            rmin, rmax = min(ratios), max(ratios)
            if rmax > 0 and (rmax - rmin) / rmax < 0.02:
                return DetectionResult(detector=detector, fired=False)

    early = medians[:knee_idx]
    late = medians[knee_idx:]
    late_vals = [v for _, v in late]
    monotonic_dec = all(b <= a + EPS for a, b in zip(late_vals, late_vals[1:]))
    monotonic_inc = all(b >= a - EPS for a, b in zip(late_vals, late_vals[1:]))
    if monotonic_dec or monotonic_inc:
        return DetectionResult(
            detector=detector,
            fired=True,
            confidence=0.9,
            classification="intent",
            evidence={
                "knee_year": late[0][0],
                "early_years": [y for y, _ in early],
                "late_years": [y for y, _ in late],
                "late_sequence": [round(v, 4) for v in late_vals],
                "direction": "decreasing" if monotonic_dec else "increasing",
            },
        )
    return DetectionResult(detector=detector, fired=False)


def _small_denom_fraction(cluster: Cluster) -> DetectionResult:
    """Test whether values cleanly fit ``N/D`` for small integer ``D``.

    Hits the bioenergy "operating days per week" case (X/7).  Strict:
    must match for ALL distinct values, must include at least one
    non-trivial fraction, must have at least one denominator ``D`` that
    appears 2+ times across the distinct value set (single-value clean
    fractions like ``0.5 = 1/2`` are too easy to hit accidentally).
    """
    detector = "small_denom_fraction"
    if not cluster.rows:
        return DetectionResult(detector=detector, fired=False)
    distinct = sorted({round(r[-1], 10) for r in cluster.rows} - {0.0, 1.0})
    if len(distinct) < 1:
        return DetectionResult(detector=detector, fired=False)

    matched: List[Tuple[float, str, int]] = []
    for v in distinct:
        hit = None
        for d in SMALL_DENOMINATORS:
            f = Fraction(v).limit_denominator(d)
            if abs(float(f) - v) < 1e-6 and f.denominator > 1:
                hit = (v, f"{f.numerator}/{f.denominator}", f.denominator)
                break
        if hit is None:
            # Try fractional-numerator form (e.g. 6.05/7) with stricter tolerance
            for d in SMALL_DENOMINATORS:
                approx_n = round(v * d, 2)
                if approx_n > 0 and abs(approx_n / d - v) < 1e-4:
                    hit = (v, f"{approx_n}/{d}", d)
                    break
        if hit is None:
            return DetectionResult(detector=detector, fired=False)
        matched.append(hit)

    # Require: at least one denominator repeats across distinct values
    # (single accidental matches like 0.5=1/2 don't count)
    from collections import Counter
    denom_counts = Counter(m[2] for m in matched)
    has_repeated = any(n >= 2 for n in denom_counts.values()) or len(matched) >= 3
    if not has_repeated:
        return DetectionResult(detector=detector, fired=False)

    return DetectionResult(
        detector=detector,
        fired=True,
        confidence=0.85,
        classification="intent",
        evidence={"matches": [(v, s) for v, s, _ in matched[:6]],
                  "shared_denominator": denom_counts.most_common(1)[0][0]},
    )


def _varies_per_timeslice_only(cluster: Cluster) -> DetectionResult:
    """Detect values that vary across the timeslice axis but not other axes.

    Per-timeslice variation usually means the value was derived from a
    load shape — could be intent (proper load profile) or accident (a
    "tiny floor at midnight when AF=0" kind of bug).  Reports as
    ``unknown`` so the user investigates.
    """
    detector = "varies_per_timeslice_only"
    if not cluster.rows or len(cluster.rows[0]) < 3:
        return DetectionResult(detector=detector, fired=False)
    # Need (l, y, val) shape to check
    by_y_l = defaultdict(set)
    for row in cluster.rows:
        l, y, v = row[0], row[1], row[-1]
        by_y_l[y].add(round(v, 10))
    # If MANY distinct values per year, varies across timeslices
    varying_years = sum(1 for vals in by_y_l.values() if len(vals) >= 5)
    if varying_years >= max(1, len(by_y_l) // 2):
        return DetectionResult(
            detector=detector,
            fired=True,
            confidence=0.7,
            classification="unknown",
            evidence={
                "varying_years": varying_years,
                "total_years": len(by_y_l),
                "avg_distinct_per_year": sum(len(v) for v in by_y_l.values()) / len(by_y_l),
            },
        )
    return DetectionResult(detector=detector, fired=False)


# --------------------------------------------------------------------------
# Parameter table inspection helpers
# --------------------------------------------------------------------------
def _resolve_def_view(db: NemoDB, parameter: str) -> Optional[str]:
    """Prefer ``<parameter>_def`` (default-overlay view) when present."""
    if db.has_def_view(parameter):
        return f"{parameter}_def"
    if parameter in db.list_tables():
        return parameter
    return None


def _table_columns_excluding(db: NemoDB, table: str, exclude=("val", "id")) -> List[str]:
    return [c for c in db.table_columns(table) if c not in exclude]


def _read_param_rows(db: NemoDB, parameter: str,
                     r: Optional[str] = None, t: Optional[str] = None
                     ) -> Tuple[List[tuple], List[str]]:
    """Read all rows for a parameter; returns (rows, key_cols).

    ``rows`` are tuples of (key1, key2, ..., val) in the natural column
    order.  Key cols exclude ``val`` and ``id``.  Filters by region and
    tech if supplied.
    """
    tbl = _resolve_def_view(db, parameter)
    if tbl is None:
        return ([], [])
    cols = _table_columns_excluding(db, tbl)
    if "val" not in db.table_columns(tbl):
        return ([], cols)
    select = ", ".join(f'"{c}"' for c in cols + ["val"])
    where_parts = []
    params: List[str] = []
    if r is not None and "r" in cols:
        where_parts.append('"r" = ?')
        params.append(r)
    if t is not None and "t" in cols:
        where_parts.append('"t" = ?')
        params.append(t)
    sql = f'SELECT {select} FROM "{tbl}"'
    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)
    df = db.query(sql, tuple(params))
    return ([tuple(row) for row in df.itertuples(index=False, name=None)], cols)


def _index_by_rt(rows: List[tuple], cols: List[str]
                 ) -> Dict[Tuple[str, str], List[tuple]]:
    """Group ``(key..., val)`` tuples by their (r, t) prefix."""
    if "r" not in cols or "t" not in cols:
        return {}
    r_idx = cols.index("r")
    t_idx = cols.index("t")
    other_indices = [i for i in range(len(cols)) if i not in (r_idx, t_idx)]
    out: Dict[Tuple[str, str], List[tuple]] = defaultdict(list)
    for row in rows:
        r = row[r_idx]
        t = row[t_idx]
        rest = tuple(row[i] for i in other_indices) + (row[-1],)
        out[(r, t)].append(rest)
    return out


# --------------------------------------------------------------------------
# Public entry points
# --------------------------------------------------------------------------
def classify_parameter(
    db: NemoDB,
    parameter: str,
    *,
    related: Sequence[str] = ("AvailabilityFactor",),
    only_nonzero: bool = True,
) -> ForensicReport:
    """Run the full detector battery against ``parameter`` and return a
    :class:`ForensicReport` with one :class:`Cluster` per ``(r, t)``.

    Parameters
    ----------
    db : NemoDB
    parameter : str
        Table name to inspect (e.g. ``"MinimumUtilization"``).  The
        function reads from ``<parameter>_def`` if present (default-
        overlay view) otherwise from the bare table.
    related : sequence of str
        Companion parameters to feed the algebraic-relationship detector.
        For ``MinimumUtilization`` the canonical companion is
        ``"AvailabilityFactor"``; for ``CapitalCost`` it might be
        ``"FixedCost"`` / ``"VariableCost"``.
    only_nonzero : bool, default True
        Skip clusters whose values are all zero — they aren't binding
        constraints and would dilute the report.
    """
    rows, cols = _read_param_rows(db, parameter)
    if not rows:
        return ForensicReport(parameter=parameter, related_params=tuple(related))

    by_rt = _index_by_rt(rows, cols)

    # Read companion rows (AF etc.) once and group by (r, t).  Skip
    # the companion if it's the parameter under inspection (self-compare
    # would always return equal/squared trivially).
    companion_by_rt: Dict[str, Dict[Tuple[str, str], List[tuple]]] = {}
    for comp in related:
        if comp == parameter:
            continue
        c_rows, c_cols = _read_param_rows(db, comp)
        companion_by_rt[comp] = _index_by_rt(c_rows, c_cols)

    # Read tech & region descriptions once
    tech_desc = {row[0]: row[1] for row in db.query(
        "SELECT val, desc FROM TECHNOLOGY"
    ).itertuples(index=False, name=None)}
    region_desc = {row[0]: row[1] for row in db.query(
        "SELECT val, desc FROM REGION"
    ).itertuples(index=False, name=None)}

    # Group all (r, t) by tech for the cross-region broadcast detector
    by_t: Dict[str, Dict[str, List[tuple]]] = defaultdict(dict)
    for (r, t), rt_rows in by_rt.items():
        by_t[t][r] = rt_rows

    report = ForensicReport(parameter=parameter, related_params=tuple(related))
    for (r, t), rt_rows in sorted(by_rt.items()):
        if only_nonzero and all(row[-1] == 0 for row in rt_rows):
            continue
        cluster = Cluster(
            region=r, tech=t, parameter=parameter, rows=rt_rows,
            region_desc=region_desc.get(r, ""),
            tech_desc=tech_desc.get(t, ""),
        )
        # Detector battery
        primary_companion = None
        for comp_name, comp_rt in companion_by_rt.items():
            comp_rows = comp_rt.get((r, t), [])
            if comp_rows:
                det = _algebraic_of(cluster, comp_rows)
                if det.fired:
                    det.detector = f"algebraic_of({comp_name})"
                cluster.detections.append(det)
                if primary_companion is None:
                    primary_companion = comp_rows
        cluster.detections.append(_year_split(cluster, primary_companion))
        cluster.detections.append(_small_denom_fraction(cluster))
        cluster.detections.append(_varies_per_timeslice_only(cluster))
        same_tech_others = {rr: rows for rr, rows in by_t[t].items() if rr != r}
        cluster.detections.append(_broadcast_across_regions(cluster, same_tech_others))
        report.clusters.append(cluster)

    return report


def forensics_for_pinned_variable(
    db: NemoDB,
    column_identity: ColumnIdentity,
    *,
    related: Sequence[str] = ("AvailabilityFactor",),
    extra_params: Sequence[str] = (),
) -> List[ForensicReport]:
    """Bridge Stage 3 → Stage 4.

    Looks up the candidate parameters that constrain the pinned variable
    (via :data:`VARIABLE_TO_CANDIDATE_PARAMS`), runs
    :func:`classify_parameter` on each, and returns the reports.  Adds
    any ``extra_params`` the caller wants inspected on top.

    Parameters
    ----------
    db : NemoDB
    column_identity : ColumnIdentity
        Output of :func:`nemo_read.decode_lp_column`.
    related : sequence of str
        Companion parameters for the algebraic detector.
    extra_params : sequence of str
        Additional parameter tables to inspect beyond the canonical
        candidate list.
    """
    candidates = list(VARIABLE_TO_CANDIDATE_PARAMS.get(
        column_identity.variable, ()))
    candidates.extend(extra_params)
    seen: set = set()
    out: List[ForensicReport] = []
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        out.append(classify_parameter(db, p, related=related))
    return out


# --------------------------------------------------------------------------
# Stage 5 — placeholder synthesis
# --------------------------------------------------------------------------
def _csv_row_zero_minutil(cluster: Cluster) -> dict:
    """Build a placeholder CSV row that overrides the parameter to zero
    at branch scope (no per-timeslice or per-year breakdown).  Branch
    path is a best-guess from tech_desc; user should verify with LEAP COM
    before injecting.
    """
    branch_hint = _guess_branch_path(cluster.tech, cluster.tech_desc)
    return {
        "ams": cluster.region_desc or cluster.region,
        "branch": branch_hint,
        "variable": _PARAM_TO_LEAP_VAR.get(cluster.parameter, cluster.parameter),
        "expression": "0",
        "unit": "",
        "fuel": "",
        "source": "nemo_read.parameter_forensics (Stage 5)",
        "note": (PLACEHOLDER_NOTE_PREFIX +
                 f"override {cluster.parameter} to 0 for "
                 f"({cluster.region}, {cluster.tech}); "
                 f"tests whether this cluster pins the infeasibility."),
        "src_csv": "placeholder",
        "domain": "infeasibility_diagnostic",
        "data_confidence": PLACEHOLDER_SENTINEL,
    }


_PARAM_TO_LEAP_VAR = {
    "MinimumUtilization":               "Minimum Utilization",
    "AvailabilityFactor":               "Maximum Availability",
    "ResidualCapacity":                 "Exogenous Capacity",
    "TotalAnnualMaxCapacity":           "Maximum Capacity",
    "TotalAnnualMinCapacity":           "Minimum Capacity",
    "TotalAnnualMaxCapacityInvestment": "Maximum Capacity Addition",
    "TotalAnnualMinCapacityInvestment": "Minimum Capacity Addition",
    "TotalTechnologyAnnualActivityUpperLimit": "Maximum Production",
    "TotalTechnologyAnnualActivityLowerLimit": "Minimum Production",
}


def _guess_branch_path(tech_id: str, tech_desc: str) -> str:
    """Best-effort LEAP branch path from tech metadata.

    The user should verify with LEAP COM before injecting.  We don't have
    enough information from SQLite alone to pin the exact module; we
    return a clearly-marked stub that the user (or a follow-up COM
    helper) can complete.
    """
    desc = (tech_desc or tech_id).split(" [LEAP ID")[0].strip()
    # Very rough heuristic — bioenergy techs live under Bioethanol /
    # Biodiesel modules; everything else under Centralized Electricity.
    bioethanol = {"Sugarcane", "Cassava", "Molasses", "Corn Ethanol"}
    biodiesel  = {"FAME Biodiesel", "CME Biodiesel", "POME Biodiesel"}
    if desc in bioethanol:
        return f"Transformation\\Bioethanol Production\\Processes\\{desc}"
    if desc in biodiesel:
        return f"Transformation\\Biodiesel Production\\Processes\\{desc}"
    return f"Transformation\\Centralized Electricity Generation\\Processes\\{desc}"


def propose_placeholders(
    report: ForensicReport,
    *,
    include_unknown: bool = True,
    max_per_report: int = 25,
) -> List[PlaceholderProposal]:
    """Stage 5 — generate ranked placeholder proposals from a forensic report.

    For each ``bug``-verdict cluster (and optionally ``unknown``),
    synthesises a minimum-perturbation override that would slacken the
    suspected constraint.  Returns proposals sorted lexicographically by
    ``(blast_radius, -confidence, reverse_difficulty)`` so the smallest,
    most-confident, easiest-to-reverse test is first.

    Parameters
    ----------
    report : ForensicReport
    include_unknown : bool, default True
        If True, also propose placeholders for ``unknown`` clusters
        (manual review may be needed).  If False, only ``bug`` clusters.
    max_per_report : int, default 25
        Cap the proposals returned to avoid overwhelming the user when
        a parameter has hundreds of bug clusters; the truncation is
        applied AFTER ranking so the most-promising ones survive.
    """
    proposals: List[PlaceholderProposal] = []
    for cluster in report.clusters:
        verdict = cluster.summary
        if verdict == "intent" or verdict == "empty":
            continue
        if verdict == "unknown" and not include_unknown:
            continue

        # Confidence: average of fired-detector confidences, biased toward
        # bug verdicts (we're more confident the placeholder will help)
        fired = [d for d in cluster.detections if d.fired]
        if fired:
            confidence = sum(d.confidence for d in fired) / len(fired)
            if verdict == "bug":
                confidence = min(1.0, confidence + 0.1)
        else:
            confidence = 0.5

        # Build the row & associated real-fix prompt
        rows = [_csv_row_zero_minutil(cluster)]
        prompt = _real_fix_prompt(cluster)
        rationale = _rationale(cluster)
        proposal = PlaceholderProposal(
            cluster=cluster,
            rows=rows,
            real_fix_prompt=prompt,
            blast_radius=len(rows),
            confidence=confidence,
            reverse_difficulty=1,                    # one CSV row to undo
            rationale=rationale,
        )
        proposals.append(proposal)

    proposals.sort(key=lambda p: p.sort_key)
    return proposals[:max_per_report]


def _real_fix_prompt(cluster: Cluster) -> str:
    """Generate a textual prompt for what the user should do AFTER the
    placeholder confirms the cluster is the binder."""
    fired = [d for d in cluster.detections if d.fired]
    forms = {d.evidence.get("form") for d in fired
             if d.detector.startswith("algebraic_of") and d.evidence.get("form")}
    if "squared" in forms:
        return (
            f"Real fix: in LEAP, inspect the `{_PARAM_TO_LEAP_VAR.get(cluster.parameter, cluster.parameter)}` "
            f"expression on `{cluster.tech_desc or cluster.tech}` (and any parent process branch). "
            f"It almost certainly contains a `=Maximum Availability ^ 2` (or equivalent) "
            f"formula — replace with an explicit numeric value reflecting actual minimum "
            f"dispatch policy, or remove entirely if no minimum is intended."
        )
    if any(d.detector == "year_split" for d in fired):
        return (
            f"Real fix: this cluster has a year-split pattern. The early years are likely the "
            f"export bug; the late years are an intentional ramp. In LEAP, replace the early-year "
            f"portion with explicit zeros while preserving the late-year Step()/Interp() schedule."
        )
    if any(d.detector == "small_denom_fraction" for d in fired):
        return (
            f"Real fix: the values are clean N/D fractions (likely operating-days/week). "
            f"This is probably modeller intent. Audit the COMPANION variable instead: "
            f"check ResidualCapacity units (often the real bug) and confirm downstream demand "
            f"sinks exist for the output fuel."
        )
    return (
        f"Real fix: cluster doesn't match a known intent pattern. Read "
        f"`{_PARAM_TO_LEAP_VAR.get(cluster.parameter, cluster.parameter)}` Expression on "
        f"`{cluster.tech_desc or cluster.tech}` in LEAP to determine origin."
    )


def _rationale(cluster: Cluster) -> str:
    fired = [d for d in cluster.detections if d.fired]
    if not fired:
        return "No detector fired; placeholder applied as default safety override."
    parts = []
    for d in fired:
        parts.append(f"{d.detector}={d.classification}({d.confidence:.2f})")
    return "Detectors: " + "; ".join(parts)
