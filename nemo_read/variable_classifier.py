"""Heuristic LEAP variable input/result classifier.

Background: LEAP COM does NOT expose any property that distinguishes
input-side from result-side variables (verified empirically 2026-05-19
via TypeInfo enumeration + ~50 candidate attribute name probes — none
worked). Reading `.Expression` on a result-side variable fires a modal
popup that destabilizes COM. So before any inject or input-side probe,
we need to classify each variable name by its likely side.

This module encodes the classification heuristic in code. Not
deterministic (the API doesn't give us certainty), but:
  - Reproducible (rule-based, not memory)
  - Auditable (you can see exactly why a name was classified)
  - Overridable (caller can pass extra overrides)
  - Updateable (when a new variable name appears in a probe, add it
    here or via override)

Per the user's directive (2026-05-19): minimize reliance on individual
LEAP-domain knowledge that doesn't carry across sessions. The rules
below capture that knowledge once, in code.
"""
from __future__ import annotations

import re
from typing import Iterable


# ---------------------------------------------------------------------------
# Heuristic rules — pattern → side
# ---------------------------------------------------------------------------

# Result-side: variables that LEAP computes (not user-authored).
# Reading `.Expression` on these fires the modal popup.
RESULT_NAME_PATTERNS = [
    re.compile(r"\bGWP\b", re.IGNORECASE),
    re.compile(r"\bPollutant\b", re.IGNORECASE),
    re.compile(r"\bLoadings\b", re.IGNORECASE),
    re.compile(r"\bAllocated\b", re.IGNORECASE),
    re.compile(r"^Total ", re.IGNORECASE),
    re.compile(r"^Gross ", re.IGNORECASE),
    re.compile(r"^Primary ", re.IGNORECASE),
    re.compile(r"^Final Energy Demand$", re.IGNORECASE),
    re.compile(r"^Useful Energy Demand$", re.IGNORECASE),
    re.compile(r"^Demand Coproduction$", re.IGNORECASE),
    re.compile(r"^Social Costs?$", re.IGNORECASE),
    re.compile(r"^Demand Cost$", re.IGNORECASE),  # computed Activity × cost
    re.compile(r"^Final On-Road ", re.IGNORECASE),  # computed adjustment
    re.compile(r"^Average Mileage$", re.IGNORECASE),  # computed average
    re.compile(r"^Energy Generation$", re.IGNORECASE),
    re.compile(r"^Power Generation$", re.IGNORECASE),
    re.compile(r"^Existing Capacity$", re.IGNORECASE),  # result aggregate
    re.compile(r"^Capacity Additions$", re.IGNORECASE),
    re.compile(r"^Capacity Retirement$", re.IGNORECASE),
    re.compile(r"^Costs of Production$", re.IGNORECASE),
    re.compile(r"^Curtailed Energy Production$", re.IGNORECASE),
]

# Input-side: variables the user authors. Safe to read `.Expression`.
INPUT_NAME_PATTERNS = [
    # Authored data
    re.compile(r"^Sales$", re.IGNORECASE),
    re.compile(r"^Device Sales$", re.IGNORECASE),
    re.compile(r"^Retirements$", re.IGNORECASE),
    re.compile(r"^Device Retirements$", re.IGNORECASE),
    re.compile(r"^Scrappage$", re.IGNORECASE),
    re.compile(r"^Device Scrappage$", re.IGNORECASE),
    re.compile(r"\bStocks?\b", re.IGNORECASE),
    re.compile(r"^Device Devices?$|^Demand Devices?$", re.IGNORECASE),
    # Transport
    re.compile(r"^Vehicle Distance$", re.IGNORECASE),
    re.compile(r"^New Vehicle ", re.IGNORECASE),
    re.compile(r"^Stock Average ", re.IGNORECASE),  # authored stock-weighted avg
    re.compile(r"^Mileage$", re.IGNORECASE),
    re.compile(r"^Fuel Economy$", re.IGNORECASE),
    re.compile(r"Correction Factor$", re.IGNORECASE),
    # Cost / financial (input authoring)
    re.compile(r"^Capital Cost$", re.IGNORECASE),
    re.compile(r"^Fixed OM Cost$", re.IGNORECASE),
    re.compile(r"^Variable OM Cost$", re.IGNORECASE),
    re.compile(r"^Investment Costs?$", re.IGNORECASE),
    re.compile(r"^Lifetime$", re.IGNORECASE),
    re.compile(r"^Interest Rate$", re.IGNORECASE),
    # Capacity bounds (input)
    re.compile(r"^Maximum Capacity$", re.IGNORECASE),
    re.compile(r"^Minimum Capacity$", re.IGNORECASE),
    re.compile(r"^Maximum Availability$", re.IGNORECASE),
    re.compile(r"^Minimum Utilization$", re.IGNORECASE),
    re.compile(r"^Maximum Devices?$", re.IGNORECASE),
    re.compile(r"^Maximum Device Additions?$", re.IGNORECASE),
    re.compile(r"^Maximum Production$", re.IGNORECASE),
    re.compile(r"^Exogenous Capacity$", re.IGNORECASE),
    # Share / fraction (input authoring)
    re.compile(r"^Share$|^Fuel Share$|Share_", re.IGNORECASE),
    re.compile(r"^Device Share$", re.IGNORECASE),
    re.compile(r"^Max Scrappage Fraction$", re.IGNORECASE),
    re.compile(r"^Fraction of Scrapped Replaced$", re.IGNORECASE),
    # Activity (input — Activity Level is authored; Total Activity is result)
    re.compile(r"^Activity Level$", re.IGNORECASE),
    # Intensity (mostly input, but Final Energy Intensity is computed)
    re.compile(r"^Fuel Economy Correction Factor$", re.IGNORECASE),
    # Shapes (input)
    re.compile(r"\bLoad Shape\b", re.IGNORECASE),
    # Process input
    re.compile(r"^Process Efficiency$", re.IGNORECASE),
    re.compile(r"^Efficiency$", re.IGNORECASE),
    re.compile(r"^Capacity Credit$", re.IGNORECASE),
    # Cost authoring (Production Cost = USD/tonne for primary resources)
    re.compile(r"^Production Cost$", re.IGNORECASE),
    re.compile(r"^Import Cost$", re.IGNORECASE),
    re.compile(r"^Export Benefit$", re.IGNORECASE),
    # Process Inputs (this is INPUT side; "Inputs" on result side is computed)
]


def classify(
    name: str,
    overrides: dict[str, str] | None = None,
) -> str:
    """Classify a variable name as 'input', 'result', or 'uncertain'.

    Precedence:
      1. `overrides` dict (caller-supplied) — wins absolutely
      2. RESULT_NAME_PATTERNS match → 'result'
      3. INPUT_NAME_PATTERNS match → 'input'
      4. Default → 'uncertain' (caller should treat as result-side
         for popup safety until manually verified)

    Args:
        name: Variable name as returned by LEAP COM `Variable.Name`
        overrides: Optional explicit name → 'input'/'result' map.
            Use when the heuristic gets a known name wrong.

    Returns:
        'input', 'result', or 'uncertain'
    """
    if not name:
        return "uncertain"
    if overrides and name in overrides:
        return overrides[name]
    for p in RESULT_NAME_PATTERNS:
        if p.search(name):
            return "result"
    for p in INPUT_NAME_PATTERNS:
        if p.search(name):
            return "input"
    return "uncertain"


def classify_many(
    names: Iterable[str],
    overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    """Classify multiple names. Returns dict[name -> 'input'/'result'/'uncertain']."""
    return {n: classify(n, overrides) for n in names}


def filter_input_names(
    names: Iterable[str],
    overrides: dict[str, str] | None = None,
    include_uncertain: bool = False,
) -> list[str]:
    """Return the subset of names classified as 'input'.

    If `include_uncertain=True`, also include uncertain names (riskier:
    may include result-side vars that the heuristic missed, → popups).
    Default False (popup-safe).
    """
    cls = classify_many(names, overrides)
    targets = {"input"} if not include_uncertain else {"input", "uncertain"}
    return [n for n, side in cls.items() if side in targets]
