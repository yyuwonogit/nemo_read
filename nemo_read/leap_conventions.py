"""
LEAP conventions: units of measure, ID conventions, and naming patterns.

Three categories of knowledge that are true for every LEAP-generated NEMO
database but are not stored explicitly in the SQLite file:

1.  **Units of measure.** When LEAP drives NEMO, it fixes the units:
    energy = petajoules, power = gigawatts, cost = million currency units,
    emissions = metric tonnes. These do not appear in the schema but every
    numeric value is denominated in them, so analysis code that adds
    labels to plots needs to know this.

2.  **LEAP branch IDs.** LEAP generates the NEMO database and embeds its
    own branch IDs into two places: as literal IDs in the fuel and
    technology ``val`` columns, and as the numeric suffix following
    ``[LEAP ID:NNNN]`` inside fuel descriptions. These IDs are the key
    to joining scenario-database rows back to the LEAP tree.

3.  **Technology ID prefix convention.** LEAP encodes technology kind in
    the first letter of the ``val`` string:

    * ``D`` — demand-side technology (end-use)
    * ``P`` — process / supply-side technology (generation or conversion)
    * ``S`` — resource / import technology

    Slack technologies break this convention with human-readable names
    like ``"Unserved"``.

The functions here surface these conventions so downstream code can rely
on them without re-deriving each time.
"""

from __future__ import annotations
import re
from typing import Dict, Optional

import pandas as pd

from .db import NemoDB


# ---------------------------------------------------------------------------
# Units LEAP uses when driving NEMO
# ---------------------------------------------------------------------------
# Source: https://sei-international.github.io/NemoMod.jl/stable/custom_constraints/
# "When LEAP runs NEMO, it uses petajoules as the energy unit, gigawatts
#  for power, million $ for costs, and metric tonnes for emissions."
LEAP_NEMO_UNITS: Dict[str, str] = {
    "energy": "PJ",                    # petajoules
    "power": "GW",                     # gigawatts
    "cost": "million currency units",  # million $ (or whatever currency LEAP is set to)
    "emissions": "t",                  # metric tonnes
}

# Conversions to SI base units that might be useful for analysis.
PJ_TO_J = 1.0e15                       # 1 PJ = 10^15 J
GW_TO_W = 1.0e9                        # 1 GW = 10^9 W
T_TO_KG = 1.0e3                        # 1 t = 10^3 kg
MILLION = 1.0e6                        # for cost readability


def units_for(variable_or_param: str) -> Optional[str]:
    """Return the LEAP-NEMO unit label for a given parameter or result variable,
    based on what quantity it represents. Returns None for dimensionless
    parameters (fractions, tags, rates ≤ 1).

    Covers the common cases. Edge-case variables return None rather than
    a confident but wrong answer.
    """
    # Normalise
    name = variable_or_param

    # Energy-valued (PJ)
    energy_exact = {
        "AccumulatedAnnualDemand", "SpecifiedAnnualDemand",
        "vdemandnn", "vdemandannualnn",
        "vproductionannualnn", "vuseannualnn",
        "vproductionannualnodal", "vuseannualnodal",
        "vgenerationannualnn", "vregenerationannualnn",
        "vgenerationannualnodal", "vregenerationannualnodal",
        "vproductionbytechnologyannual", "vusebytechnologyannual",
        "vtotaltechnologyannualactivity", "vtotaltechnologymodelperiodactivity",
        "vtotalannualtechnologyactivitybymode",
        "vproductionnn", "vusenn", "vproductionnodal", "vusenodal",
        "vproductionbytechnology", "vusebytechnology",
        "vtradeannual", "vtrade", "vtransmissionannual", "vtransmissionbyline",
    }
    if name in energy_exact:
        return "PJ"

    # Rates: energy per year
    if name.startswith("vrateof"):
        return "PJ/year"

    # Capacity (GW)
    capacity_exact = {
        "vnewcapacity", "vaccumulatednewcapacity", "vtotalcapacityannual",
        "vtotalcapacityinreservemargin",
        "ResidualCapacity", "CapacityOfOneTechnologyUnit",
        "TotalAnnualMaxCapacity", "TotalAnnualMinCapacity",
        "TotalAnnualMaxCapacityInvestment", "TotalAnnualMinCapacityInvestment",
    }
    if name in capacity_exact:
        return "GW"

    storage_capacity = {
        "vnewstoragecapacity", "vaccumulatednewstoragecapacity",
        "ResidualStorageCapacity", "CapitalCostStorage",
        "TotalAnnualMaxCapacityStorage", "TotalAnnualMinCapacityStorage",
        "TotalAnnualMaxCapacityInvestmentStorage",
        "TotalAnnualMinCapacityInvestmentStorage",
    }
    if name in storage_capacity:
        return "PJ"    # storage capacity in NEMO is energy not power

    # Costs
    cost_exact = {
        "CapitalCost", "FixedCost", "VariableCost",
        "vcapitalinvestment", "vcapitalinvestmentstorage", "vcapitalinvestmenttransmission",
        "vdiscountedcapitalinvestment", "vdiscountedcapitalinvestmentstorage",
        "vdiscountedcapitalinvestmenttransmission",
        "vfinancecost", "vfinancecoststorage", "vfinancecosttransmission",
        "voperatingcost", "vdiscountedoperatingcost",
        "voperatingcosttransmission", "vdiscountedoperatingcosttransmission",
        "vannualfixedoperatingcost", "vannualvariableoperatingcost",
        "vvariablecosttransmission", "vvariablecosttransmissionbyts",
        "vsalvagevalue", "vsalvagevaluestorage", "vsalvagevaluetransmission",
        "vdiscountedsalvagevalue", "vdiscountedsalvagevaluestorage",
        "vdiscountedsalvagevaluetransmission",
        "vtotaldiscountedcost", "vmodelperiodcostbyregion",
        "vannualtechnologyemissionpenaltybyemission",
        "vannualtechnologyemissionspenalty",
        "vdiscountedtechnologyemissionspenalty",
        "EmissionsPenalty",   # cost per mass
    }
    if name in cost_exact:
        return "million currency units"

    # Emissions (tonnes)
    emissions_exact = {
        "vannualemissions", "vmodelperiodemissions",
        "vannualtechnologyemission", "vannualtechnologyemissionbymode",
        "AnnualEmissionLimit", "AnnualExogenousEmission",
        "ModelPeriodEmissionLimit", "ModelPeriodExogenousEmission",
    }
    if name in emissions_exact:
        return "t"

    # Dimensionless: fractions, ratios, availability factors, share targets
    return None


# ---------------------------------------------------------------------------
# LEAP ID extraction
# ---------------------------------------------------------------------------
_LEAP_ID_RE = re.compile(r"\[LEAP ID:(\d+)\]")


def extract_leap_ids(df: pd.DataFrame, desc_col: str = "desc",
                     out_col: str = "leap_id") -> pd.DataFrame:
    """Extract ``[LEAP ID:N]`` from a ``desc`` column into ``leap_id``.

    Operates out-of-place and returns a new DataFrame. Non-matching rows
    get ``<NA>`` in the new column.
    """
    if desc_col not in df.columns:
        raise KeyError(f"Column {desc_col!r} not found.")
    out = df.copy()
    extracted = out[desc_col].astype("string").str.extract(_LEAP_ID_RE)
    out[out_col] = pd.to_numeric(extracted[0], errors="coerce").astype("Int64")
    return out


# ---------------------------------------------------------------------------
# Technology ID categorisation
# ---------------------------------------------------------------------------
# LEAP's NEMO export uses single-letter prefixes on technology and fuel IDs.
# This mapping is empirical but stable across LEAP 2024+ exports.
_TECH_PREFIX_KIND: Dict[str, str] = {
    "D": "demand",
    "P": "process",
    "S": "supply",
}


def classify_technology_id(tech_id: str) -> str:
    """Return a coarse kind for a LEAP/NEMO technology ID.

    Returns one of: ``"demand"``, ``"process"``, ``"supply"``, or
    ``"other"``. The ``"other"`` bucket catches named slack technologies
    like ``"Unserved"`` and anything not matching the expected prefix
    pattern (digit, non-standard letter, etc.).
    """
    if not tech_id:
        return "other"
    first = tech_id[0]
    if first.isalpha() and first.upper() in _TECH_PREFIX_KIND:
        # Only count as kind if followed by a digit (P2641) or all-digits
        # variants like S13D — not if it's a full word like "Unserved".
        if len(tech_id) > 1 and (tech_id[1].isdigit() or tech_id[1].isalpha() and tech_id[1].isupper() and any(c.isdigit() for c in tech_id[1:])):
            return _TECH_PREFIX_KIND[first.upper()]
        if len(tech_id) > 1 and tech_id[1].isdigit():
            return _TECH_PREFIX_KIND[first.upper()]
    return "other"


def technology_kinds(db: NemoDB) -> pd.DataFrame:
    """Return the TECHNOLOGY table with an added ``kind`` column.

    Kinds use ``classify_technology_id``; the enrichment makes it trivial
    to filter to demand / process / supply tranches when building
    summaries.
    """
    df = db.query("SELECT val, desc FROM TECHNOLOGY")
    df["kind"] = df["val"].astype(str).map(classify_technology_id)
    return df


def fuels_with_leap_ids(db: NemoDB) -> pd.DataFrame:
    """Return the FUEL table with LEAP IDs extracted from the desc column.

    LEAP formats fuel descriptions as ``"<human-readable> [LEAP ID:N]"``,
    so the numeric ID is recoverable with a simple regex.
    """
    df = db.query("SELECT val, desc FROM FUEL")
    return extract_leap_ids(df)


# ---------------------------------------------------------------------------
# LEAP BranchType code → human name. Enumerated during probe against AEO9
# (5194 branches) and Freedonia. Codes not yet seen can be added as discovered.
# ---------------------------------------------------------------------------
LEAP_BRANCH_TYPES: Dict[int, str] = {
    0:  "Unknown Branch Type",
    1:  "Demand Category",
    2:  "Transformation Module",
    3:  "Transformation Process",
    4:  "Demand Technology",
    5:  "Transformation Process Category",
    6:  "Transformation Output Category",
    7:  "Transformation Output Fuel",
    8:  "Key Assumptions Branch",
    9:  "Key Assumption Category",
    10: "Key Assumption",
    11: "Resource Category",
    12: "Resource Category",
    13: "Resource Category",
    14: "Demand Branch",
    15: "Resource",
    26: "Non Energy Category",
    27: "Non Energy",
    28: "Non Energy Branch",
    30: "Transformation Auxiliary Fuel Category",
    31: "Transformation Auxiliary Fuel",
    32: "Transformation Feedstock Fuel Category",
    33: "Transformation Feedstock Fuel",
    34: "Environmental Effect",
    35: "Environmental Effect",
    36: "Demand Fuel",
    39: "Effects",
    48: "Load Shapes Category",
    49: "Load Shape",
    50: "Transformation Branch",
    51: "Effect Category",
    52: "Transmission Nodes",
    53: "Requirement Node",
    54: "Transmission Lines",
    55: "Transmission Line",
    56: "Transmission Nodes",
    57: "Process Node",
}


def resolve_leap_ids(
    df: pd.DataFrame,
    context,
    *,
    branch_id_col: str = "bid",
    tech_col: str | None = "t",
    fuel_leap_id_col: str | None = "leap_id",
) -> pd.DataFrame:
    """Enrich a DataFrame with LEAP branch/fuel names using a LeapAreaContext.

    Adds columns:

    - ``branch_full_name``  — if ``branch_id_col`` is present
    - ``tech_branch_full_name`` — if ``tech_col`` is present and values
      match the ``P<id>`` / ``D<id>`` / ``S<id>`` convention
    - ``fuel_name``         — if ``fuel_leap_id_col`` is present

    ``context`` must be a :class:`nemo_read.leap_area.LeapAreaContext`.
    Columns that aren't present in ``df`` are silently skipped.
    """
    out = df.copy()
    if branch_id_col and branch_id_col in out.columns:
        out["branch_full_name"] = out[branch_id_col].map(
            lambda bid: context.branch_full_name(int(bid)) if pd.notna(bid) else None
        )
    if tech_col and tech_col in out.columns:
        def _lookup_tech(val):
            if not isinstance(val, str) or len(val) < 2:
                return None
            if val[0] in "PDS" and val[1:].isdigit():
                return context.branch_full_name(int(val[1:]))
            return None
        out["tech_branch_full_name"] = out[tech_col].map(_lookup_tech)
    if fuel_leap_id_col and fuel_leap_id_col in out.columns:
        out["fuel_name"] = out[fuel_leap_id_col].map(
            lambda fid: context.fuel_name(int(fid)) if pd.notna(fid) else None
        )
    return out
