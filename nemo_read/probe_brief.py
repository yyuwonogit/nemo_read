"""
Probe brief generator — Stage 7 of the infeasibility-resolution pipeline.

When the Stage-6 placeholder cycle doesn't converge (placeholders applied
but the model is still infeasible at the same column, OR the user wants
to understand the LEAP-side mechanism before designing a real fix), the
remaining unknowns get compressed into the smallest possible set of LEAP
COM reads.

A :class:`ProbeBriefItem` is one such read: ``(branch, variable)`` plus
the offline-derived hypothesis it tests, the answer that would confirm
or refute it, and the next step under each outcome.  The intent is that
when the user opens LEAP they have a 30-second checklist instead of an
open-ended hunt.

Public API:
    ProbeBriefItem, ProbeBrief, emit_probe_brief, format_brief_text
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parameter_forensics import (
    Cluster, ForensicReport, _PARAM_TO_LEAP_VAR, _guess_branch_path,
)


@dataclass
class ProbeBriefItem:
    """One LEAP COM read with its surrounding rationale.

    Attributes
    ----------
    branch : str
        LEAP branch full path (best guess from offline analysis; user
        should confirm).
    variable : str
        LEAP variable name to read (e.g. ``"Minimum Utilization"``).
    region : str
        LEAP region name (``ams`` in the canonical CSV).  May be ``"any"``
        for tech-broadcast variables.
    hypothesis : str
        What we believe the Expression contains, derived offline.
    on_confirm : str
        Action to take if the read confirms the hypothesis.
    on_refute : str
        Action to take if the read contradicts the hypothesis.
    related_cluster : Cluster, optional
        The forensic cluster that motivated this probe.
    """
    branch: str
    variable: str
    region: str
    hypothesis: str
    on_confirm: str
    on_refute: str
    related_cluster: Optional[Cluster] = None

    def as_text(self, idx: int = 1) -> str:
        cluster_tag = ""
        if self.related_cluster:
            cluster_tag = (f"  [forensic cluster: {self.related_cluster.parameter}"
                           f"[{self.related_cluster.region},"
                           f"{self.related_cluster.tech}]]")
        return (
            f"\nProbe {idx}{cluster_tag}\n"
            f"  Region:     {self.region}\n"
            f"  Branch:     {self.branch}\n"
            f"  Variable:   {self.variable}\n"
            f"  Hypothesis: {self.hypothesis}\n"
            f"  If confirmed → {self.on_confirm}\n"
            f"  If refuted   → {self.on_refute}"
        )


@dataclass
class ProbeBrief:
    """Ordered list of probes with a header explaining the context."""
    items: List[ProbeBriefItem] = field(default_factory=list)
    title: str = "LEAP COM probe brief"
    context: str = ""

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def to_text(self) -> str:
        lines = [f"=== {self.title} ===", ""]
        if self.context:
            lines.append(self.context)
            lines.append("")
        if not self.items:
            lines.append("(no probes — Stage 5 placeholders should have already "
                         "resolved everything)")
        for i, item in enumerate(self.items, start=1):
            lines.append(item.as_text(i))
        return "\n".join(lines)


def _hypothesis_for_cluster(cluster: Cluster) -> tuple:
    """Derive (hypothesis, on_confirm, on_refute) text for one cluster."""
    fired = [d for d in cluster.detections if d.fired]
    forms = {d.evidence.get("form") for d in fired
             if d.detector.startswith("algebraic_of")}
    var_name = _PARAM_TO_LEAP_VAR.get(cluster.parameter, cluster.parameter)

    if "squared" in forms:
        return (
            f"`{var_name}` Expression is `=Maximum Availability ^ 2` "
            f"(or equivalent self-multiplication of another variable).",
            f"Replace with explicit numeric value or zero. If the formula "
            f"sits on a parent branch, walk up to find inheritance source.",
            f"Read the parent process branch's `{var_name}` next; the "
            f"squared value may be inherited rather than locally defined.",
        )
    if "equal" in forms:
        return (
            f"`{var_name}` Expression is a passthrough copy of another "
            f"variable's value (likely accidental).",
            f"Set to explicit value or zero in LEAP.",
            f"Same value may come from a different formula — read the "
            f"parent branch.",
        )
    year_split = next((d for d in fired if d.detector == "year_split"), None)
    if year_split:
        late_seq = year_split.evidence.get("late_sequence", [])
        knee = year_split.evidence.get("knee_year", "?")
        return (
            f"`{var_name}` Expression has two parts: bug-pattern up to "
            f"year {knee}, then user-set ramp {late_seq}. Likely "
            f"`Step({knee}, {late_seq[0]}, ...)` × Maximum Availability "
            f"or similar.",
            f"Preserve the late-year Step() exactly. Replace the early-"
            f"year portion with explicit zeros (or the intended floor).",
            f"Year split may come from an `If(year>=…)` conditional. Read "
            f"the full Expression text to identify the conditional.",
        )
    fraction_det = next(
        (d for d in fired if d.detector == "small_denom_fraction"), None)
    if fraction_det:
        matches = fraction_det.evidence.get("matches", [])
        return (
            f"`{var_name}` Expression contains a fractional value "
            f"(matches: {matches[:3]}). Probably a typed numeric literal "
            f"(e.g. `0.864286` or `=6.05/7`) or an indirect reference to "
            f"a `Days_Per_Week` user variable.",
            f"Leave `{var_name}` alone; the cluster is likely intent. "
            f"Audit COMPANION variables (ResidualCapacity, demand sinks).",
            f"If formula references a User Variable, check the variable's "
            f"definition in Key Assumptions.",
        )
    return (
        f"`{var_name}` Expression source unclear from offline analysis. "
        f"Read whatever is there to understand origin.",
        f"Document the finding and update parameter_forensics detectors "
        f"if a new pattern surfaces.",
        f"Try walking the branch parent for inherited expressions.",
    )


def emit_probe_brief(
    *reports: ForensicReport,
    only_unresolved: bool = True,
    include_intent: bool = False,
) -> ProbeBrief:
    """Generate a :class:`ProbeBrief` from one or more forensic reports.

    Parameters
    ----------
    reports : ForensicReport
        One or more reports (e.g. from
        :func:`forensics_for_pinned_variable`).
    only_unresolved : bool, default True
        If True, emit probes only for ``unknown`` clusters (those Stage 5
        placeholders couldn't fully classify).  If False, also emit
        probes for ``bug`` clusters — useful when the user wants the LEAP
        Expression text for a confident-bug cluster to confirm the
        underlying mechanism before writing the real fix.
    include_intent : bool, default False
        Add probes for ``intent`` clusters too (rarely useful — only when
        the user wants to verify the Step()/Interp() recipe matches what
        SQLite implies).
    """
    items: List[ProbeBriefItem] = []
    seen_keys: set = set()  # (tech, parameter) — one probe per tech+var
    for report in reports:
        for cluster in report.clusters:
            verdict = cluster.summary
            if verdict == "intent" and not include_intent:
                continue
            if verdict == "bug" and only_unresolved:
                continue
            if verdict == "empty":
                continue
            key = (cluster.tech, cluster.parameter)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            hypothesis, on_confirm, on_refute = _hypothesis_for_cluster(cluster)
            items.append(ProbeBriefItem(
                branch=_guess_branch_path(cluster.tech, cluster.tech_desc),
                variable=_PARAM_TO_LEAP_VAR.get(cluster.parameter,
                                                 cluster.parameter),
                region=cluster.region_desc or cluster.region,
                hypothesis=hypothesis,
                on_confirm=on_confirm,
                on_refute=on_refute,
                related_cluster=cluster,
            ))

    n_reports = len(reports)
    n_clusters = sum(len(r.clusters) for r in reports)
    context = (f"Generated from {n_reports} forensic report(s) covering "
               f"{n_clusters} cluster(s). Each probe is one LEAP COM "
               f"`var.Expression` read; total estimated time < {len(items)*3}s.")
    return ProbeBrief(items=items, context=context)


def format_brief_text(brief: ProbeBrief) -> str:
    """Convenience: print-friendly representation of the brief."""
    return brief.to_text()
