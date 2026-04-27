"""
NEMO scenario database schema (data dictionary v11).

Source of truth: NemoMod.jl/src/db_structure.jl at master.
Covers LEAP versions shipping with NEMO v2.0+ (LEAP 2024 family, incl. v0.17).

Every dict here is a plain-data description of the schema so the rest of the
library can introspect tables without hitting the database.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Current NEMO data dictionary version this module targets.
TARGET_DB_VERSION = 11

# NEMO uses short column abbreviations consistently; this maps them to the
# dimension (set) table they reference. Useful when decoding any parameter or
# result row without re-reading table metadata.
DIMENSION_ABBREVIATIONS: Dict[str, str] = {
    "r":  "REGION",                # region
    "rr": "REGION",                # destination region (trade)
    "rg": "REGIONGROUP",           # region group
    "t":  "TECHNOLOGY",            # technology
    "f":  "FUEL",                  # fuel / energy carrier
    "e":  "EMISSION",              # emission species
    "m":  "MODE_OF_OPERATION",     # technology operating mode
    "s":  "STORAGE",               # storage facility
    "y":  "YEAR",                  # model year (stored as TEXT)
    "l":  "TIMESLICE",             # sub-annual time slice
    "n":  "NODE",                  # transmission node
    "n1": "NODE",                  # from-node
    "n2": "NODE",                  # to-node
    "tr": "TransmissionLine",      # transmission line id
    "tg1": "TSGROUP1",             # time-slice group level 1 (e.g. season)
    "tg2": "TSGROUP2",             # time-slice group level 2 (e.g. day type)
}


@dataclass(frozen=True)
class Dimension:
    """A NEMO set / dimension table. `pk` is the primary-key column that
    other tables reference via the abbreviations above."""
    name: str
    pk: str
    columns: Tuple[str, ...]
    description: str = ""


@dataclass(frozen=True)
class Parameter:
    """A NEMO parameter (input data) table. `dims` lists the foreign-key
    columns in the order NEMO uses. The value column is always `val`.
    Every parameter table also has an integer `id` PRIMARY KEY."""
    name: str
    dims: Tuple[str, ...]
    value_col: str = "val"
    description: str = ""
    unit: str = ""


@dataclass(frozen=True)
class ResultVariable:
    """A NEMO output variable (the v*-prefixed tables). `dims` lists the
    index columns on the JuMP variable. Stored rows always include `val`
    plus a `solvedtm` timestamp column added when writing results."""
    name: str
    dims: Tuple[str, ...]
    category: str
    description: str = ""
    unit: str = ""


# ---------------------------------------------------------------------------
# Dimension tables. Columns shown in the order NEMO creates them.
# ---------------------------------------------------------------------------
DIMENSIONS: Dict[str, Dimension] = {
    "EMISSION":          Dimension("EMISSION",          "val",  ("val", "desc"),
                                   "Emission species (e.g. CO2, CH4, NOx)."),
    "FUEL":              Dimension("FUEL",              "val",  ("val", "desc"),
                                   "Fuel / energy carrier."),
    "MODE_OF_OPERATION": Dimension("MODE_OF_OPERATION", "val",  ("val", "desc"),
                                   "Technology operating modes (integer-like strings)."),
    "REGION":            Dimension("REGION",            "val",  ("val", "desc"),
                                   "Geographic region."),
    "REGIONGROUP":       Dimension("REGIONGROUP",       "val",  ("val", "desc"),
                                   "Group of regions for aggregate constraints."),
    "STORAGE":           Dimension("STORAGE",           "val",
                                   ("val", "desc", "netzeroyear", "netzerotg1", "netzerotg2"),
                                   "Storage facility; netzero* control charge/discharge balance."),
    "TECHNOLOGY":        Dimension("TECHNOLOGY",        "val",  ("val", "desc"),
                                   "Technology (generator, conversion, demand, etc.)."),
    "TIMESLICE":         Dimension("TIMESLICE",         "val",  ("val", "desc"),
                                   "Sub-annual time slice label."),
    "TSGROUP1":          Dimension("TSGROUP1",          "name",
                                   ("name", "desc", "order", "multiplier"),
                                   "Upper time-slice group (e.g. season). multiplier scales weight."),
    "TSGROUP2":          Dimension("TSGROUP2",          "name",
                                   ("name", "desc", "order", "multiplier"),
                                   "Lower time-slice group (e.g. day type)."),
    "YEAR":              Dimension("YEAR",              "val",  ("val", "desc"),
                                   "Model year. Stored as TEXT despite representing an integer."),
    "NODE":              Dimension("NODE",              "val",  ("val", "desc", "r"),
                                   "Transmission node; `r` ties node to its region."),
    "LTsGroup":          Dimension("LTsGroup",          "l",
                                   ("id", "l", "lorder", "tg2", "tg1"),
                                   "Maps each TIMESLICE l into TSGROUP1 (tg1) and TSGROUP2 (tg2)."),
    "RRGroup":           Dimension("RRGroup",           "rg",
                                   ("id", "rg", "r"),
                                   "Maps regions (r) to region groups (rg)."),
    "TransmissionLine":  Dimension("TransmissionLine",  "id",
                                   ("id", "n1", "n2", "f", "maxflow", "reactance",
                                    "yconstruction", "capitalcost", "fixedcost",
                                    "variablecost", "operationallife", "efficiency",
                                    "interestrate"),
                                   "Transmission line; mixes dimension-like ids with exogenous parameters."),
}


# ---------------------------------------------------------------------------
# Parameter tables. The `id` column is omitted from `dims` because it is a
# surrogate row identifier and carries no modelling meaning.
# ---------------------------------------------------------------------------
PARAMETERS: Dict[str, Parameter] = {
    # --- Demand ----------------------------------------------------------
    "AccumulatedAnnualDemand":
        Parameter("AccumulatedAnnualDemand", ("r", "f", "y"),
                  description="Demand that can be satisfied at any time within the year.",
                  unit="energy unit / year"),
    "SpecifiedAnnualDemand":
        Parameter("SpecifiedAnnualDemand", ("r", "f", "y"),
                  description="Annual demand that must follow SpecifiedDemandProfile within the year.",
                  unit="energy unit / year"),
    "SpecifiedDemandProfile":
        Parameter("SpecifiedDemandProfile", ("r", "f", "l", "y"),
                  description="Fraction of SpecifiedAnnualDemand occurring in time slice l. Rows sum to 1 per (r,f,y).",
                  unit="fraction"),

    # --- Time-slicing ---------------------------------------------------
    "YearSplit":
        Parameter("YearSplit", ("l", "y"),
                  description="Fraction of the year occupied by time slice l.",
                  unit="fraction"),

    # --- Capacity factors / availability --------------------------------
    "AvailabilityFactor":
        Parameter("AvailabilityFactor", ("r", "t", "l", "y"),
                  description="Fraction of nameplate capacity available in time slice. "
                              "Renamed from CapacityFactor in NEMO 2.0 (DB v10).",
                  unit="fraction"),

    "CapacityToActivityUnit":
        Parameter("CapacityToActivityUnit", ("r", "t"),
                  description="Conversion factor: annual energy produced per unit of capacity "
                              "running at 100% for the full year.",
                  unit="energy unit / capacity unit / year"),

    "CapacityOfOneTechnologyUnit":
        Parameter("CapacityOfOneTechnologyUnit", ("r", "t", "y"),
                  description="Discrete unit size; forces integer builds when set.",
                  unit="capacity unit"),

    # --- Activity ratios -------------------------------------------------
    "InputActivityRatio":
        Parameter("InputActivityRatio", ("r", "t", "f", "m", "y"),
                  description="Fuel input per unit of nominal activity for technology t in mode m.",
                  unit="energy unit / energy unit"),
    "OutputActivityRatio":
        Parameter("OutputActivityRatio", ("r", "t", "f", "m", "y"),
                  description="Fuel output per unit of nominal activity for technology t in mode m.",
                  unit="energy unit / energy unit"),
    "EmissionActivityRatio":
        Parameter("EmissionActivityRatio", ("r", "t", "e", "m", "y"),
                  description="Emissions per unit of nominal activity.",
                  unit="mass / energy unit"),

    # --- Costs -----------------------------------------------------------
    "CapitalCost":         Parameter("CapitalCost",         ("r", "t", "y"),
                                     description="Overnight capex per unit capacity.", unit="cost / capacity"),
    "CapitalCostStorage":  Parameter("CapitalCostStorage",  ("r", "s", "y"),
                                     description="Overnight capex per unit storage energy.", unit="cost / energy"),
    "FixedCost":           Parameter("FixedCost",           ("r", "t", "y"),
                                     description="Fixed O&M per unit capacity per year.", unit="cost / capacity / year"),
    "VariableCost":        Parameter("VariableCost",        ("r", "t", "m", "y"),
                                     description="Variable O&M per unit of activity.", unit="cost / energy unit"),
    "EmissionsPenalty":    Parameter("EmissionsPenalty",    ("r", "e", "y"),
                                     description="Cost imposed per unit of emission.", unit="cost / mass"),
    "DiscountRate":        Parameter("DiscountRate",        ("r",),
                                     description="Region-level discount rate applied to cash flows.", unit="fraction"),
    "InterestRateTechnology":
        Parameter("InterestRateTechnology", ("r", "t", "y"),
                  description="Technology financing rate (introduced DB v7).", unit="fraction"),
    "InterestRateStorage":
        Parameter("InterestRateStorage", ("r", "s", "y"),
                  description="Storage financing rate (introduced DB v7).", unit="fraction"),
    "DepreciationMethod":
        Parameter("DepreciationMethod", ("r",),
                  description="1 = sinking-fund, 2 = straight-line salvage.", unit="code"),

    # --- Operational life ------------------------------------------------
    "OperationalLife":        Parameter("OperationalLife",        ("r", "t"), description="Years.", unit="year"),
    "OperationalLifeStorage": Parameter("OperationalLifeStorage", ("r", "s"), description="Years.", unit="year"),

    # --- Capacity bounds -------------------------------------------------
    "ResidualCapacity":
        Parameter("ResidualCapacity", ("r", "t", "y"),
                  description="Exogenous existing capacity surviving into year y."),
    "ResidualStorageCapacity":
        Parameter("ResidualStorageCapacity", ("r", "s", "y")),
    "TotalAnnualMaxCapacity":            Parameter("TotalAnnualMaxCapacity",            ("r", "t", "y")),
    "TotalAnnualMinCapacity":            Parameter("TotalAnnualMinCapacity",            ("r", "t", "y")),
    "TotalAnnualMaxCapacityStorage":     Parameter("TotalAnnualMaxCapacityStorage",     ("r", "s", "y")),
    "TotalAnnualMinCapacityStorage":     Parameter("TotalAnnualMinCapacityStorage",     ("r", "s", "y")),
    "TotalAnnualMaxCapacityInvestment":  Parameter("TotalAnnualMaxCapacityInvestment",  ("r", "t", "y")),
    "TotalAnnualMinCapacityInvestment":  Parameter("TotalAnnualMinCapacityInvestment",  ("r", "t", "y")),
    "TotalAnnualMaxCapacityInvestmentStorage":
        Parameter("TotalAnnualMaxCapacityInvestmentStorage", ("r", "s", "y")),
    "TotalAnnualMinCapacityInvestmentStorage":
        Parameter("TotalAnnualMinCapacityInvestmentStorage", ("r", "s", "y")),

    # --- Activity bounds -------------------------------------------------
    "TotalTechnologyAnnualActivityUpperLimit":
        Parameter("TotalTechnologyAnnualActivityUpperLimit", ("r", "t", "y")),
    "TotalTechnologyAnnualActivityLowerLimit":
        Parameter("TotalTechnologyAnnualActivityLowerLimit", ("r", "t", "y")),
    "TotalTechnologyModelPeriodActivityUpperLimit":
        Parameter("TotalTechnologyModelPeriodActivityUpperLimit", ("r", "t")),
    "TotalTechnologyModelPeriodActivityLowerLimit":
        Parameter("TotalTechnologyModelPeriodActivityLowerLimit", ("r", "t")),

    # --- Renewable & utilisation ----------------------------------------
    "REMinProductionTarget":
        Parameter("REMinProductionTarget", ("r", "f", "y"),
                  description="Fraction of fuel f in region r, year y that must be renewable. "
                              "Added fuel dimension in DB v8."),
    "REMinProductionTargetRG":
        Parameter("REMinProductionTargetRG", ("rg", "f", "y"),
                  description="Same as REMinProductionTarget but for a region group."),
    "RETagTechnology":
        Parameter("RETagTechnology", ("r", "t", "y"),
                  description="1 if technology counts as renewable for REMinProductionTarget."),
    "MinShareProduction":
        Parameter("MinShareProduction", ("r", "t", "f", "y"),
                  description="Minimum share of production of fuel f that must come from technology t."),
    "MinimumUtilization":
        Parameter("MinimumUtilization", ("r", "t", "l", "y"),
                  description="Minimum utilisation fraction of installed capacity per time slice."),

    # --- Reserve margin --------------------------------------------------
    "ReserveMargin":
        Parameter("ReserveMargin", ("r", "f", "y"),
                  description="Required reserve margin for fuel f (fuel dim added DB v10)."),
    "ReserveMarginTagTechnology":
        Parameter("ReserveMarginTagTechnology", ("r", "t", "f", "y"),
                  description="Contribution of technology to reserve margin for fuel f."),

    # --- Ramping ---------------------------------------------------------
    "RampRate":     Parameter("RampRate",     ("r", "t", "y", "l"),
                              description="Max fractional change in output between adjacent time slices."),
    "RampingReset": Parameter("RampingReset", ("r",),
                              description="0|1|2 flag controlling when ramping constraints reset."),

    # --- Storage dynamics -----------------------------------------------
    "MinStorageCharge":       Parameter("MinStorageCharge",       ("r", "s", "y")),
    "StorageLevelStart":      Parameter("StorageLevelStart",      ("r", "s")),
    "StorageMaxChargeRate":   Parameter("StorageMaxChargeRate",   ("r", "s")),
    "StorageMaxDischargeRate":Parameter("StorageMaxDischargeRate",("r", "s")),
    "StorageFullLoadHours":   Parameter("StorageFullLoadHours",   ("r", "s", "y")),
    "TechnologyFromStorage":  Parameter("TechnologyFromStorage",  ("r", "t", "s", "m"),
                                        description="1 if technology t in mode m discharges storage s."),
    "TechnologyToStorage":    Parameter("TechnologyToStorage",    ("r", "t", "s", "m"),
                                        description="1 if technology t in mode m charges storage s."),

    # --- Emissions limits ------------------------------------------------
    "AnnualEmissionLimit":
        Parameter("AnnualEmissionLimit", ("r", "e", "y")),
    "AnnualExogenousEmission":
        Parameter("AnnualExogenousEmission", ("r", "e", "y"),
                  description="Emissions added to the model outside of technology activity."),
    "ModelPeriodEmissionLimit":
        Parameter("ModelPeriodEmissionLimit", ("r", "e")),
    "ModelPeriodExogenousEmission":
        Parameter("ModelPeriodExogenousEmission", ("r", "e")),

    # --- Trade & transmission -------------------------------------------
    "TradeRoute":
        Parameter("TradeRoute", ("r", "rr", "f", "y"),
                  description="1 if fuel f can be traded between regions r and rr in year y."),
    "TransmissionModelingEnabled":
        Parameter("TransmissionModelingEnabled", ("r", "f", "y"),
                  value_col="type",
                  description="Presence switches on nodal transmission modelling. "
                              "`type` field (default 1) selects linearised flow formulation."),
    "TransmissionCapacityToActivityUnit":
        Parameter("TransmissionCapacityToActivityUnit", ("r", "f"),
                  description="Conversion from transmission capacity to energy per year."),
    "TransmissionAvailabilityFactor":
        Parameter("TransmissionAvailabilityFactor", ("tr", "l", "y"),
                  description="Per-time-slice availability of a transmission line. "
                              "Added DB v10, default 1.0."),
    "MinAnnualTransmissionNodes":
        Parameter("MinAnnualTransmissionNodes", ("n1", "n2", "f", "y"),
                  description="Added DB v11."),
    "MaxAnnualTransmissionNodes":
        Parameter("MaxAnnualTransmissionNodes", ("n1", "n2", "f", "y"),
                  description="Added DB v11."),

    # --- Nodal distribution ---------------------------------------------
    "NodalDistributionDemand":
        Parameter("NodalDistributionDemand", ("n", "f", "y"),
                  description="Fraction of regional demand allocated to node n."),
    "NodalDistributionTechnologyCapacity":
        Parameter("NodalDistributionTechnologyCapacity", ("n", "t", "y"),
                  description="Fraction of regional capacity allocated to node n."),
    "NodalDistributionStorageCapacity":
        Parameter("NodalDistributionStorageCapacity", ("n", "s", "y")),
}

# ---------------------------------------------------------------------------
# Output / result variable tables. Column order follows the JuMP variable
# signatures shown in the NEMO docs. Result rows also carry `solvedtm` and
# occasionally additional provenance columns NEMO may add in the future, so
# consumers should always read by column name.
# ---------------------------------------------------------------------------
RESULT_VARIABLES: Dict[str, ResultVariable] = {
    # --- Capacity --------------------------------------------------------
    "vnewcapacity":                 ResultVariable("vnewcapacity", ("r","t","y"), "capacity",
                                                   "New endogenous build of technology capacity in year y.",
                                                   "capacity unit"),
    "vaccumulatednewcapacity":      ResultVariable("vaccumulatednewcapacity", ("r","t","y"), "capacity",
                                                   "Sum of vnewcapacity from first year through y.", "capacity unit"),
    "vtotalcapacityannual":         ResultVariable("vtotalcapacityannual", ("r","t","y"), "capacity",
                                                   "Total installed capacity = ResidualCapacity + accumulated new capacity still within life.",
                                                   "capacity unit"),
    "vnewstoragecapacity":          ResultVariable("vnewstoragecapacity", ("r","s","y"), "capacity", "", "energy unit"),
    "vaccumulatednewstoragecapacity":ResultVariable("vaccumulatednewstoragecapacity",("r","s","y"),"capacity","","energy unit"),
    "vtotalcapacityinreservemargin":ResultVariable("vtotalcapacityinreservemargin", ("r","f","y"), "capacity",
                                                   "Capacity counted toward reserve margin for fuel f.", "capacity unit"),

    # --- Activity (annual) ----------------------------------------------
    "vtotaltechnologyannualactivity":
        ResultVariable("vtotaltechnologyannualactivity", ("r","t","y"), "activity",
                       "Nominal annual energy output of technology t.", "energy unit"),
    "vtotaltechnologymodelperiodactivity":
        ResultVariable("vtotaltechnologymodelperiodactivity", ("r","t"), "activity",
                       "Nominal energy output over the full model period."),
    "vtotalannualtechnologyactivitybymode":
        ResultVariable("vtotalannualtechnologyactivitybymode", ("r","t","m","y"), "activity"),
    "vproductionbytechnologyannual":
        ResultVariable("vproductionbytechnologyannual", ("r","t","f","y"), "activity",
                       "Annual production of fuel f by technology t (nodal + non-nodal).", "energy unit"),
    "vusebytechnologyannual":
        ResultVariable("vusebytechnologyannual", ("r","t","f","y"), "activity",
                       "Annual use of fuel f by technology t.", "energy unit"),

    # non-nodal
    "vproductionannualnn":          ResultVariable("vproductionannualnn",   ("r","f","y"), "activity", unit="energy unit"),
    "vuseannualnn":                 ResultVariable("vuseannualnn",          ("r","f","y"), "activity", unit="energy unit"),
    "vgenerationannualnn":          ResultVariable("vgenerationannualnn",   ("r","f","y"), "activity",
                                                   "Production excluding discharge from storage.", "energy unit"),
    "vregenerationannualnn":        ResultVariable("vregenerationannualnn", ("r","f","y"), "activity",
                                                   "Renewable generation (RETagTechnology-weighted).", "energy unit"),
    "vdemandnn":                    ResultVariable("vdemandnn",             ("r","l","f","y"), "demand",
                                                   "Non-nodal time-sliced demand.", "energy unit"),
    "vdemandannualnn":              ResultVariable("vdemandannualnn",       ("r","f","y"), "demand", unit="energy unit"),
    "vproductionnn":                ResultVariable("vproductionnn",         ("r","l","f","y"), "activity", unit="energy unit"),
    "vusenn":                       ResultVariable("vusenn",                ("r","l","f","y"), "activity", unit="energy unit"),
    "vproductionbytechnology":      ResultVariable("vproductionbytechnology",("r","l","t","f","y"),"activity"),
    "vusebytechnology":             ResultVariable("vusebytechnology",     ("r","l","t","f","y"),"activity"),
    "vrateofactivity":              ResultVariable("vrateofactivity",      ("r","l","t","m","y"),"rate",
                                                   "Capacity in use per time slice.", "energy unit / year"),
    "vrateoftotalactivity":         ResultVariable("vrateoftotalactivity", ("r","t","l","y"),   "rate"),
    "vrateofproduction":            ResultVariable("vrateofproduction",    ("r","l","f","y"),   "rate"),
    "vrateofuse":                   ResultVariable("vrateofuse",           ("r","l","f","y"),   "rate"),
    "vrateofproductionbytechnologynn":
        ResultVariable("vrateofproductionbytechnologynn", ("r","l","t","f","y"), "rate"),
    "vrateofusebytechnologynn":
        ResultVariable("vrateofusebytechnologynn",       ("r","l","t","f","y"), "rate"),
    "vrateofproductionbytechnologybymodenn":
        ResultVariable("vrateofproductionbytechnologybymodenn", ("r","l","t","m","f","y"), "rate"),
    "vrateofusebytechnologybymodenn":
        ResultVariable("vrateofusebytechnologybymodenn",       ("r","l","t","m","f","y"), "rate"),
    "vrateofproductionnn":          ResultVariable("vrateofproductionnn",  ("r","l","f","y"), "rate"),
    "vrateofusenn":                 ResultVariable("vrateofusenn",         ("r","l","f","y"), "rate"),

    # nodal
    "vproductionannualnodal":       ResultVariable("vproductionannualnodal",   ("n","f","y"), "activity", unit="energy unit"),
    "vuseannualnodal":              ResultVariable("vuseannualnodal",          ("n","l","f","y"), "activity", unit="energy unit"),
    "vgenerationannualnodal":       ResultVariable("vgenerationannualnodal",   ("n","f","y"), "activity", unit="energy unit"),
    "vregenerationannualnodal":     ResultVariable("vregenerationannualnodal", ("n","f","y"), "activity", unit="energy unit"),
    "vproductionnodal":             ResultVariable("vproductionnodal",         ("n","l","f","y"), "activity", unit="energy unit"),
    "vusenodal":                    ResultVariable("vusenodal",                ("n","l","f","y"), "activity", unit="energy unit"),
    "vrateofactivitynodal":         ResultVariable("vrateofactivitynodal",     ("n","l","t","m","y"), "rate"),
    "vrateoftotalactivitynodal":    ResultVariable("vrateoftotalactivitynodal",("n","t","l","y"), "rate"),
    "vrateofproductionnodal":       ResultVariable("vrateofproductionnodal",   ("n","l","f","y"), "rate"),
    "vrateofusenodal":              ResultVariable("vrateofusenodal",          ("n","l","f","y"), "rate"),
    "vrateofproductionbytechnologynodal":
        ResultVariable("vrateofproductionbytechnologynodal", ("n","l","t","f","y"), "rate"),
    "vrateofusebytechnologynodal":
        ResultVariable("vrateofusebytechnologynodal",       ("n","l","t","f","y"), "rate"),

    # --- Emissions -------------------------------------------------------
    "vannualtechnologyemission":        ResultVariable("vannualtechnologyemission",        ("r","t","e","y"), "emissions",
                                                       unit="mass"),
    "vannualtechnologyemissionbymode":  ResultVariable("vannualtechnologyemissionbymode",  ("r","t","e","m","y"), "emissions"),
    "vannualtechnologyemissionpenaltybyemission":
        ResultVariable("vannualtechnologyemissionpenaltybyemission",("r","t","e","y"),"emissions", unit="cost"),
    "vannualtechnologyemissionspenalty":
        ResultVariable("vannualtechnologyemissionspenalty", ("r","t","y"), "emissions", unit="cost"),
    "vdiscountedtechnologyemissionspenalty":
        ResultVariable("vdiscountedtechnologyemissionspenalty",("r","t","y"),"emissions", unit="cost"),
    "vannualemissions":                 ResultVariable("vannualemissions", ("r","e","y"), "emissions",
                                                       "Total emissions including AnnualExogenousEmission.", "mass"),
    "vmodelperiodemissions":            ResultVariable("vmodelperiodemissions", ("r","e"), "emissions",
                                                       unit="mass"),

    # --- Costs -----------------------------------------------------------
    "vcapitalinvestment":              ResultVariable("vcapitalinvestment", ("r","t","y"), "cost",
                                                      "Undiscounted capex incl. financing.", "cost"),
    "vdiscountedcapitalinvestment":    ResultVariable("vdiscountedcapitalinvestment", ("r","t","y"), "cost", unit="cost"),
    "vcapitalinvestmentstorage":       ResultVariable("vcapitalinvestmentstorage", ("r","s","y"), "cost", unit="cost"),
    "vdiscountedcapitalinvestmentstorage":
        ResultVariable("vdiscountedcapitalinvestmentstorage", ("r","s","y"), "cost", unit="cost"),
    "vcapitalinvestmenttransmission":  ResultVariable("vcapitalinvestmenttransmission", ("tr","y"), "cost", unit="cost"),
    "vdiscountedcapitalinvestmenttransmission":
        ResultVariable("vdiscountedcapitalinvestmenttransmission", ("tr","y"), "cost", unit="cost"),
    "vfinancecost":                    ResultVariable("vfinancecost",           ("r","t","y"), "cost", unit="cost"),
    "vfinancecoststorage":             ResultVariable("vfinancecoststorage",    ("r","s","y"), "cost", unit="cost"),
    "vfinancecosttransmission":        ResultVariable("vfinancecosttransmission",("tr","y"),    "cost", unit="cost"),
    "voperatingcost":                  ResultVariable("voperatingcost",         ("r","t","y"), "cost", unit="cost"),
    "vdiscountedoperatingcost":        ResultVariable("vdiscountedoperatingcost",("r","t","y"),"cost", unit="cost"),
    "voperatingcosttransmission":      ResultVariable("voperatingcosttransmission",("tr","y"), "cost", unit="cost"),
    "vdiscountedoperatingcosttransmission":
        ResultVariable("vdiscountedoperatingcosttransmission", ("tr","y"), "cost", unit="cost"),
    "vannualfixedoperatingcost":       ResultVariable("vannualfixedoperatingcost",   ("r","t","y"), "cost", unit="cost"),
    "vannualvariableoperatingcost":    ResultVariable("vannualvariableoperatingcost",("r","t","y"), "cost", unit="cost"),
    "vvariablecosttransmission":       ResultVariable("vvariablecosttransmission",   ("tr","y"),    "cost", unit="cost"),
    "vvariablecosttransmissionbyts":   ResultVariable("vvariablecosttransmissionbyts",("tr","l","f","y"),"cost", unit="cost"),
    "vsalvagevalue":                   ResultVariable("vsalvagevalue",          ("r","t","y"), "cost", unit="cost"),
    "vsalvagevaluestorage":            ResultVariable("vsalvagevaluestorage",   ("r","s","y"), "cost", unit="cost"),
    "vsalvagevaluetransmission":       ResultVariable("vsalvagevaluetransmission",("tr","y"),  "cost", unit="cost"),
    "vdiscountedsalvagevalue":         ResultVariable("vdiscountedsalvagevalue",("r","t","y"), "cost", unit="cost"),
    "vdiscountedsalvagevaluestorage":  ResultVariable("vdiscountedsalvagevaluestorage",("r","s","y"),"cost", unit="cost"),
    "vdiscountedsalvagevaluetransmission":
        ResultVariable("vdiscountedsalvagevaluetransmission", ("tr","y"), "cost", unit="cost"),
    "vtotaldiscountedcost":            ResultVariable("vtotaldiscountedcost", ("r","y"), "cost",
                                                      "Objective function component per region-year.", "cost"),
    "vmodelperiodcostbyregion":        ResultVariable("vmodelperiodcostbyregion", ("r",), "cost",
                                                      "Sum of all discounted costs by region.", "cost"),

    # --- Trade & transmission -------------------------------------------
    "vtradeannual":                    ResultVariable("vtradeannual", ("r","rr","f","y"), "trade",
                                                      "Annual inter-regional fuel flow.", "energy unit"),
    "vtrade":                          ResultVariable("vtrade", ("r","rr","l","f","y"), "trade", unit="energy unit"),
    "vtransmissionbuilt":              ResultVariable("vtransmissionbuilt", ("tr","y"), "transmission",
                                                      "1 if line tr endogenously built in year y."),
    "vtransmissionexists":             ResultVariable("vtransmissionexists",("tr","y"), "transmission",
                                                      "1 if line tr exists (built or exogenous) in year y."),
    "vtransmissionbyline":             ResultVariable("vtransmissionbyline",("tr","l","f","y"), "transmission",
                                                      "Flow on transmission line per time slice.", "energy unit"),
    "vtransmissionannual":             ResultVariable("vtransmissionannual",("n","f","y"), "transmission",
                                                      "Net annual inflow at node n.", "energy unit"),

    # --- Storage ---------------------------------------------------------
    "vstoragelevelyearstart":          ResultVariable("vstoragelevelyearstart", ("r","s","y"), "storage", unit="energy unit"),
    "vstoragelevelyearfinish":         ResultVariable("vstoragelevelyearfinish",("r","s","y"), "storage", unit="energy unit"),
    "vstoragelevelseasonstart":        ResultVariable("vstoragelevelseasonstart",("r","s","ls","y"), "storage"),
    "vstorageleveldaytypestart":       ResultVariable("vstorageleveldaytypestart",("r","s","ls","ld","y"),"storage"),
    "vstorageleveldaytypefinish":      ResultVariable("vstorageleveldaytypefinish",("r","s","ls","ld","y"),"storage"),
    "vstoragelevelts":                 ResultVariable("vstoragelevelts",      ("r","s","l","y"), "storage", unit="energy unit"),
    "vstoragelevelnodal":              ResultVariable("vstoragelevelnodal",   ("n","s","l","y"), "storage", unit="energy unit"),
}


def parameter_has_value_col(param_name: str) -> bool:
    """Return False for oddball tables like TransmissionModelingEnabled
    where the scalar column is not literally named `val`."""
    p = PARAMETERS.get(param_name)                          # look up parameter
    return p is not None and p.value_col == "val"           # simple check


# ---------------------------------------------------------------------------
# LEAP source map — which LEAP UI Variable + BranchType feeds each NEMO table.
# Used by nemo_read.leap_area.where_in_leap() for input-side traceback.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LeapSource:
    """How to locate a NEMO parameter's input in the LEAP UI.

    - ``variable``: the LEAP Variable Name as it appears in the Analysis view.
    - ``branch_type``: the integer BranchType code that owns this variable.
    - ``branch_type_name``: human-readable branch-type label (for UI hints).
    - ``branch_dim``: which dim column in a parameter row picks the specific
      branch. Common values: ``"t"``, ``"s"``, ``"tr"``, ``"module"`` (row
      carries ``_module_branch_id``), ``"n_within_t"`` (Process Node under a
      tech's Transmission Nodes folder).
    - ``confidence``: ``"confirmed"`` (seen in probes), ``"inferred"`` (from
      LEAP/NEMO conventions), or ``"unknown"``.
    """
    variable: str
    branch_type: int
    branch_type_name: str
    branch_dim: str
    confidence: str = "inferred"


# Process-scoped parameters (BranchType=3 Transformation Process, or BT=4 Demand Technology).
_PROCESS = 3
_PROCESS_NAME = "Transformation Process"

# Transformation Module (BT=2) — aggregate decision variables.
_MODULE = 2
_MODULE_NAME = "Transformation Module"

# Process Node (BT=57) — per-process spatial node children.
_PROCESS_NODE = 57
_PROCESS_NODE_NAME = "Process Node"

# Transmission Line (BT=55).
_TRANSMISSION_LINE = 55
_TRANSMISSION_LINE_NAME = "Transmission Line"

# Environmental Effect (BT=34) — per-pollutant children of processes.
_ENV_EFFECT = 34
_ENV_EFFECT_NAME = "Environmental Effect"

# Demand Fuel (BT=36).
_DEMAND_FUEL = 36
_DEMAND_FUEL_NAME = "Demand Fuel"


LEAP_SOURCE_MAP: Dict[str, LeapSource] = {
    # --- Transformation Process -----------------------------------------
    "CapitalCost":            LeapSource("Capital Cost",                    _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "FixedCost":              LeapSource("Fixed OM Cost",                    _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "VariableCost":           LeapSource("Variable OM Cost",                 _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "OperationalLife":        LeapSource("Lifetime",                         _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "AvailabilityFactor":     LeapSource("Maximum Availability",             _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "MinimumUtilization":     LeapSource("Minimum Utilization",              _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "ResidualCapacity":       LeapSource("Exogenous Capacity",               _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "TotalAnnualMaxCapacity": LeapSource("Maximum Capacity",                 _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "TotalAnnualMinCapacity": LeapSource("Minimum Capacity",                 _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "TotalAnnualMaxCapacityInvestment":
                              LeapSource("Maximum Capacity Addition",        _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "TotalAnnualMinCapacityInvestment":
                              LeapSource("Minimum Capacity Addition",        _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "TotalTechnologyAnnualActivityUpperLimit":
                              LeapSource("Maximum Production",               _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "TotalTechnologyAnnualActivityLowerLimit":
                              LeapSource("Minimum Production",               _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "MinShareProduction":     LeapSource("Minimum Share of Production",      _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "RETagTechnology":        LeapSource("Renewable Qualified",              _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "ReserveMarginTagTechnology":
                              LeapSource("Capacity Credit",                  _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "InterestRateTechnology": LeapSource("Interest Rate",                    _PROCESS, _PROCESS_NAME, "t", "confirmed"),
    "CapacityToActivityUnit": LeapSource("Full Load Hours",                  _PROCESS, _PROCESS_NAME, "t", "inferred"),
    "CapacityOfOneTechnologyUnit":
                              LeapSource("Use Addition Size",                _MODULE, _MODULE_NAME, "module", "inferred"),
    "InputActivityRatio":     LeapSource("Feedstock Fuel + Process Efficiency",
                                         _PROCESS, _PROCESS_NAME, "t", "inferred"),
    "OutputActivityRatio":    LeapSource("Output Fuel + Process Efficiency",
                                         _PROCESS, _PROCESS_NAME, "t", "inferred"),
    "TotalTechnologyModelPeriodActivityUpperLimit":
                              LeapSource("Model Period Max Activity",        _PROCESS, _PROCESS_NAME, "t", "inferred"),
    "TotalTechnologyModelPeriodActivityLowerLimit":
                              LeapSource("Model Period Min Activity",        _PROCESS, _PROCESS_NAME, "t", "inferred"),

    # --- Process Node (nodal distribution) -------------------------------
    "NodalDistributionTechnologyCapacity":
                              LeapSource("Nodal Distribution",               _PROCESS_NODE, _PROCESS_NODE_NAME, "n_within_t", "confirmed"),
    "NodalDistributionStorageCapacity":
                              LeapSource("Nodal Distribution",               _PROCESS_NODE, _PROCESS_NODE_NAME, "n_within_t", "confirmed"),

    # --- Environmental Effect --------------------------------------------
    "EmissionActivityRatio":  LeapSource("Emission Factor",                  _ENV_EFFECT, _ENV_EFFECT_NAME, "t", "inferred"),

    # --- Demand Fuel ------------------------------------------------------
    "SpecifiedAnnualDemand":  LeapSource("Final Energy Demand",              _DEMAND_FUEL, _DEMAND_FUEL_NAME, "t", "inferred"),
    "AccumulatedAnnualDemand":LeapSource("Final Energy Demand",              _DEMAND_FUEL, _DEMAND_FUEL_NAME, "t", "inferred"),
    "SpecifiedDemandProfile": LeapSource("Demand Profile",                   _DEMAND_FUEL, _DEMAND_FUEL_NAME, "t", "inferred"),

    # --- Transformation Module -------------------------------------------
    "ReserveMargin":          LeapSource("Planning Reserve Margin",          _MODULE, _MODULE_NAME, "module", "confirmed"),
    "REMinProductionTarget":  LeapSource("Renewable Target",                 _MODULE, _MODULE_NAME, "module", "confirmed"),
    "REMinProductionTargetRG":LeapSource("Renewable Target (region group)",  _MODULE, _MODULE_NAME, "module", "inferred"),
    "DepreciationMethod":     LeapSource("Depreciation Method",              _MODULE, _MODULE_NAME, "module", "inferred"),
    "DiscountRate":           LeapSource("Discount Rate",                    8, "Key Assumption", "module", "inferred"),

    # --- Transmission Line / Key\Transmission ----------------------------
    "TransmissionAvailabilityFactor":
                              LeapSource("Availability Factor",              _TRANSMISSION_LINE, _TRANSMISSION_LINE_NAME, "tr", "inferred"),
    "TransmissionCapacityToActivityUnit":
                              LeapSource("Capacity to Activity Conversion",  _TRANSMISSION_LINE, _TRANSMISSION_LINE_NAME, "tr", "inferred"),
    "MinAnnualTransmissionNodes":
                              LeapSource("Minimum Flow",                     _TRANSMISSION_LINE, _TRANSMISSION_LINE_NAME, "tr", "inferred"),
    "MaxAnnualTransmissionNodes":
                              LeapSource("Maximum Flow",                     _TRANSMISSION_LINE, _TRANSMISSION_LINE_NAME, "tr", "inferred"),
    "TransmissionModelingEnabled":
                              LeapSource("Activity Level",                   10, "Key Assumption (Key\\Transmission\\Transmission Enabled)", "module", "confirmed"),
    "NodalDistributionDemand":LeapSource("Activity Level",                   10, "Key Assumption (Key\\Transmission\\Demand Distribution)", "module", "confirmed"),

    # --- Storage-scoped (applied to a Process branch flagged as storage) -
    "CapitalCostStorage":     LeapSource("Capital Cost",                     _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "MinStorageCharge":       LeapSource("Minimum Charge",                   _PROCESS, _PROCESS_NAME, "s", "confirmed"),
    "StorageLevelStart":      LeapSource("Storage Level Start",              _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "StorageMaxChargeRate":   LeapSource("Maximum Charge Rate",              _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "StorageMaxDischargeRate":LeapSource("Maximum Discharge Rate",           _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "StorageFullLoadHours":   LeapSource("Full Load Hours",                  _PROCESS, _PROCESS_NAME, "s", "confirmed"),
    "OperationalLifeStorage": LeapSource("Lifetime",                         _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "ResidualStorageCapacity":LeapSource("Exogenous Capacity (storage)",     _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "TotalAnnualMaxCapacityStorage":
                              LeapSource("Maximum Capacity",                 _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "TotalAnnualMinCapacityStorage":
                              LeapSource("Minimum Capacity",                 _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "TotalAnnualMaxCapacityInvestmentStorage":
                              LeapSource("Maximum Capacity Addition",        _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "TotalAnnualMinCapacityInvestmentStorage":
                              LeapSource("Minimum Capacity Addition",        _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "InterestRateStorage":    LeapSource("Interest Rate",                    _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "TechnologyFromStorage":  LeapSource("(auto-generated storage link)",    _PROCESS, _PROCESS_NAME, "s", "inferred"),
    "TechnologyToStorage":    LeapSource("(auto-generated storage link)",    _PROCESS, _PROCESS_NAME, "s", "inferred"),

    # --- Emission-scoped --------------------------------------------------
    "EmissionsPenalty":       LeapSource("Penalty",                          _ENV_EFFECT, _ENV_EFFECT_NAME, "t", "inferred"),
    "AnnualEmissionLimit":    LeapSource("Emissions Limit",                  _MODULE, _MODULE_NAME, "module", "inferred"),
    "AnnualExogenousEmission":LeapSource("Exogenous Emissions",              _ENV_EFFECT, _ENV_EFFECT_NAME, "t", "inferred"),
    "ModelPeriodEmissionLimit":
                              LeapSource("Model Period Emissions Limit",     _MODULE, _MODULE_NAME, "module", "inferred"),
    "ModelPeriodExogenousEmission":
                              LeapSource("Model Period Exogenous Emissions", _ENV_EFFECT, _ENV_EFFECT_NAME, "t", "inferred"),

    # --- Ramping ---------------------------------------------------------
    "RampingReset":           LeapSource("Ramping Reset",                    10, "Key Assumption", "module", "inferred"),

    # --- Time-slicing ----------------------------------------------------
    "YearSplit":              LeapSource("(derived from TimeSlice.Hours / 8760)",
                                         0, "(auto)", "module", "inferred"),
}


def leap_source(table: str) -> "LeapSource | None":
    """Return the :class:`LeapSource` for a NEMO parameter table, or None."""
    return LEAP_SOURCE_MAP.get(table)


# ---------------------------------------------------------------------------
# Result → dependency map (0.6.1)
#
# For each v* result variable, list which input parameters and upstream
# result variables mathematically determine it, plus the parameter tables
# that upper/lower-bound it.
#
# Sourced from NemoMod.jl's constraint and objective definitions (NEMO v11).
# Used by :func:`nemo_read.trace.trace_result` to explain why a computed
# number is what it is.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResultDependency:
    """Mathematical ancestry of a NEMO result variable.

    - ``inputs``            : parameter tables that appear in the defining
      JuMP constraint/objective term.
    - ``upstream_results``  : other v* tables this one is composed from.
    - ``upper_bounds``      : parameter tables that set an upper bound.
      Binding against any of these means the optimizer would choose higher
      if the bound were relaxed.
    - ``lower_bounds``      : parameter tables that set a lower bound.
    - ``formula_hint``      : short human description of the defining equation.
    """
    inputs: Tuple[str, ...] = ()
    upstream_results: Tuple[str, ...] = ()
    upper_bounds: Tuple[str, ...] = ()
    lower_bounds: Tuple[str, ...] = ()
    formula_hint: str = ""


RESULT_DEPENDENCIES: Dict[str, ResultDependency] = {
    # --- Capacity --------------------------------------------------------
    "vnewcapacity": ResultDependency(
        inputs=("CapacityOfOneTechnologyUnit",),
        upper_bounds=("TotalAnnualMaxCapacityInvestment",),
        lower_bounds=("TotalAnnualMinCapacityInvestment",),
        formula_hint="Endogenous capacity added in year y; integer if CapacityOfOneTechnologyUnit is set.",
    ),
    "vaccumulatednewcapacity": ResultDependency(
        inputs=("OperationalLife",),
        upstream_results=("vnewcapacity",),
        formula_hint="Sum of vnewcapacity still within OperationalLife window at year y.",
    ),
    "vtotalcapacityannual": ResultDependency(
        inputs=("ResidualCapacity",),
        upstream_results=("vaccumulatednewcapacity",),
        upper_bounds=("TotalAnnualMaxCapacity",),
        lower_bounds=("TotalAnnualMinCapacity",),
        formula_hint="ResidualCapacity + vaccumulatednewcapacity.",
    ),
    "vnewstoragecapacity": ResultDependency(
        upper_bounds=("TotalAnnualMaxCapacityInvestmentStorage",),
        lower_bounds=("TotalAnnualMinCapacityInvestmentStorage",),
        formula_hint="Endogenous storage energy capacity added in year y.",
    ),
    "vaccumulatednewstoragecapacity": ResultDependency(
        inputs=("OperationalLifeStorage",),
        upstream_results=("vnewstoragecapacity",),
        formula_hint="Sum of vnewstoragecapacity still within OperationalLifeStorage window.",
    ),
    "vtotalcapacityinreservemargin": ResultDependency(
        inputs=("ReserveMarginTagTechnology",),
        upstream_results=("vtotalcapacityannual",),
        lower_bounds=("ReserveMargin",),
        formula_hint="sum_t vtotalcapacityannual × ReserveMarginTagTechnology; ≥ ReserveMargin × peak.",
    ),

    # --- Activity / production ------------------------------------------
    "vrateofactivity": ResultDependency(
        inputs=("AvailabilityFactor", "CapacityToActivityUnit"),
        upstream_results=("vtotalcapacityannual",),
        upper_bounds=("AvailabilityFactor",),
        lower_bounds=("MinimumUtilization",),
        formula_hint="Bounded by vtotalcapacityannual × AvailabilityFactor × CapacityToActivityUnit.",
    ),
    "vrateoftotalactivity": ResultDependency(
        upstream_results=("vrateofactivity",),
        formula_hint="Sum over modes of vrateofactivity.",
    ),
    "vtotaltechnologyannualactivity": ResultDependency(
        inputs=("YearSplit",),
        upstream_results=("vrateoftotalactivity",),
        upper_bounds=("TotalTechnologyAnnualActivityUpperLimit",),
        lower_bounds=("TotalTechnologyAnnualActivityLowerLimit",),
        formula_hint="Sum over l of vrateoftotalactivity × YearSplit.",
    ),
    "vtotaltechnologymodelperiodactivity": ResultDependency(
        upstream_results=("vtotaltechnologyannualactivity",),
        upper_bounds=("TotalTechnologyModelPeriodActivityUpperLimit",),
        lower_bounds=("TotalTechnologyModelPeriodActivityLowerLimit",),
        formula_hint="Sum over y of vtotaltechnologyannualactivity.",
    ),
    "vtotalannualtechnologyactivitybymode": ResultDependency(
        inputs=("YearSplit",),
        upstream_results=("vrateofactivity",),
        formula_hint="Sum over l of vrateofactivity × YearSplit for a given mode m.",
    ),
    "vproductionbytechnologyannual": ResultDependency(
        inputs=("OutputActivityRatio", "YearSplit"),
        upstream_results=("vrateofactivity",),
        formula_hint="Sum over (l,m) of vrateofactivity × OutputActivityRatio × YearSplit.",
    ),
    "vusebytechnologyannual": ResultDependency(
        inputs=("InputActivityRatio", "YearSplit"),
        upstream_results=("vrateofactivity",),
        formula_hint="Sum over (l,m) of vrateofactivity × InputActivityRatio × YearSplit.",
    ),
    "vrateofproduction": ResultDependency(
        inputs=("OutputActivityRatio",),
        upstream_results=("vrateofactivity",),
        formula_hint="Sum over (t,m) of vrateofactivity × OutputActivityRatio.",
    ),
    "vrateofuse": ResultDependency(
        inputs=("InputActivityRatio",),
        upstream_results=("vrateofactivity",),
        formula_hint="Sum over (t,m) of vrateofactivity × InputActivityRatio.",
    ),
    "vproductionannualnn": ResultDependency(
        inputs=("YearSplit",),
        upstream_results=("vrateofproduction",),
        formula_hint="Sum over l of vrateofproduction × YearSplit (non-nodal).",
    ),
    "vuseannualnn": ResultDependency(
        inputs=("YearSplit",),
        upstream_results=("vrateofuse",),
        formula_hint="Sum over l of vrateofuse × YearSplit (non-nodal).",
    ),
    "vgenerationannualnn": ResultDependency(
        upstream_results=("vproductionannualnn", "vstoragelevelts"),
        formula_hint="Production excluding storage discharge.",
    ),
    "vregenerationannualnn": ResultDependency(
        inputs=("RETagTechnology",),
        upstream_results=("vproductionbytechnologyannual",),
        formula_hint="Renewable share of production (RETagTechnology-weighted).",
    ),
    "vdemandnn": ResultDependency(
        inputs=("SpecifiedAnnualDemand", "SpecifiedDemandProfile",
                "AccumulatedAnnualDemand", "YearSplit"),
        formula_hint="Time-sliced demand = SpecifiedAnnualDemand × SpecifiedDemandProfile + allocated AccumulatedAnnualDemand.",
    ),

    # --- Emissions -------------------------------------------------------
    "vannualtechnologyemissionbymode": ResultDependency(
        inputs=("EmissionActivityRatio",),
        upstream_results=("vtotalannualtechnologyactivitybymode",),
        formula_hint="vtotalannualtechnologyactivitybymode × EmissionActivityRatio.",
    ),
    "vannualtechnologyemission": ResultDependency(
        upstream_results=("vannualtechnologyemissionbymode",),
        formula_hint="Sum over m of vannualtechnologyemissionbymode.",
    ),
    "vannualemissions": ResultDependency(
        inputs=("AnnualExogenousEmission",),
        upstream_results=("vannualtechnologyemission",),
        upper_bounds=("AnnualEmissionLimit",),
        formula_hint="Sum over t of vannualtechnologyemission + AnnualExogenousEmission.",
    ),
    "vmodelperiodemissions": ResultDependency(
        inputs=("ModelPeriodExogenousEmission",),
        upstream_results=("vannualemissions",),
        upper_bounds=("ModelPeriodEmissionLimit",),
        formula_hint="Sum over y of vannualemissions + ModelPeriodExogenousEmission.",
    ),
    "vannualtechnologyemissionpenaltybyemission": ResultDependency(
        inputs=("EmissionsPenalty",),
        upstream_results=("vannualtechnologyemission",),
        formula_hint="vannualtechnologyemission × EmissionsPenalty.",
    ),
    "vannualtechnologyemissionspenalty": ResultDependency(
        upstream_results=("vannualtechnologyemissionpenaltybyemission",),
        formula_hint="Sum over e of vannualtechnologyemissionpenaltybyemission.",
    ),
    "vdiscountedtechnologyemissionspenalty": ResultDependency(
        inputs=("DiscountRate",),
        upstream_results=("vannualtechnologyemissionspenalty",),
        formula_hint="vannualtechnologyemissionspenalty discounted by DiscountRate.",
    ),

    # --- Costs -----------------------------------------------------------
    "vcapitalinvestment": ResultDependency(
        inputs=("CapitalCost",),
        upstream_results=("vnewcapacity",),
        formula_hint="vnewcapacity × CapitalCost.",
    ),
    "vdiscountedcapitalinvestment": ResultDependency(
        inputs=("DiscountRate",),
        upstream_results=("vcapitalinvestment",),
        formula_hint="vcapitalinvestment discounted to base year.",
    ),
    "vcapitalinvestmentstorage": ResultDependency(
        inputs=("CapitalCostStorage",),
        upstream_results=("vnewstoragecapacity",),
        formula_hint="vnewstoragecapacity × CapitalCostStorage.",
    ),
    "vdiscountedcapitalinvestmentstorage": ResultDependency(
        inputs=("DiscountRate",),
        upstream_results=("vcapitalinvestmentstorage",),
    ),
    "vfinancecost": ResultDependency(
        inputs=("InterestRateTechnology", "OperationalLife"),
        upstream_results=("vcapitalinvestment",),
        formula_hint="Financing charge on vcapitalinvestment over OperationalLife.",
    ),
    "vfinancecoststorage": ResultDependency(
        inputs=("InterestRateStorage", "OperationalLifeStorage"),
        upstream_results=("vcapitalinvestmentstorage",),
    ),
    "vannualfixedoperatingcost": ResultDependency(
        inputs=("FixedCost",),
        upstream_results=("vtotalcapacityannual",),
        formula_hint="vtotalcapacityannual × FixedCost.",
    ),
    "vannualvariableoperatingcost": ResultDependency(
        inputs=("VariableCost",),
        upstream_results=("vtotalannualtechnologyactivitybymode",),
        formula_hint="Sum over m of vtotalannualtechnologyactivitybymode × VariableCost.",
    ),
    "voperatingcost": ResultDependency(
        upstream_results=("vannualfixedoperatingcost", "vannualvariableoperatingcost"),
        formula_hint="Annual fixed + variable O&M.",
    ),
    "vdiscountedoperatingcost": ResultDependency(
        inputs=("DiscountRate",),
        upstream_results=("voperatingcost",),
    ),
    "vsalvagevalue": ResultDependency(
        inputs=("DepreciationMethod", "OperationalLife"),
        upstream_results=("vcapitalinvestment",),
        formula_hint="Residual value of vcapitalinvestment at end of model period.",
    ),
    "vdiscountedsalvagevalue": ResultDependency(
        inputs=("DiscountRate",),
        upstream_results=("vsalvagevalue",),
    ),
    "vsalvagevaluestorage": ResultDependency(
        inputs=("DepreciationMethod", "OperationalLifeStorage"),
        upstream_results=("vcapitalinvestmentstorage",),
    ),
    "vdiscountedsalvagevaluestorage": ResultDependency(
        inputs=("DiscountRate",),
        upstream_results=("vsalvagevaluestorage",),
    ),
    "vtotaldiscountedcost": ResultDependency(
        upstream_results=(
            "vdiscountedcapitalinvestment",
            "vdiscountedcapitalinvestmentstorage",
            "vdiscountedcapitalinvestmenttransmission",
            "vdiscountedoperatingcost",
            "vdiscountedoperatingcosttransmission",
            "vdiscountedtechnologyemissionspenalty",
            "vdiscountedsalvagevalue",
            "vdiscountedsalvagevaluestorage",
            "vdiscountedsalvagevaluetransmission",
            "vfinancecost",
            "vfinancecoststorage",
            "vfinancecosttransmission",
        ),
        formula_hint="Objective-function component per (region, year): sum of all discounted cost streams minus salvage.",
    ),
    "vmodelperiodcostbyregion": ResultDependency(
        upstream_results=("vtotaldiscountedcost",),
        formula_hint="Sum over y of vtotaldiscountedcost.",
    ),

    # --- Trade -----------------------------------------------------------
    "vtrade": ResultDependency(
        inputs=("TradeRoute",),
        formula_hint="Inter-regional fuel flow; 0 when TradeRoute=0.",
    ),
    "vtradeannual": ResultDependency(
        inputs=("YearSplit",),
        upstream_results=("vtrade",),
        formula_hint="Sum over l of vtrade × YearSplit.",
    ),

    # --- Transmission ----------------------------------------------------
    "vtransmissionbuilt": ResultDependency(
        formula_hint="Endogenous decision: 1 if line built in year y.",
    ),
    "vtransmissionexists": ResultDependency(
        upstream_results=("vtransmissionbuilt",),
        formula_hint="1 if line exists (previously built or exogenous).",
    ),
    "vtransmissionbyline": ResultDependency(
        inputs=("TransmissionAvailabilityFactor", "TransmissionCapacityToActivityUnit"),
        upstream_results=("vtransmissionexists",),
        upper_bounds=("MaxAnnualTransmissionNodes",),
        lower_bounds=("MinAnnualTransmissionNodes",),
        formula_hint="Flow on line tr per time slice, bounded by capacity × availability.",
    ),
    "vtransmissionannual": ResultDependency(
        inputs=("YearSplit",),
        upstream_results=("vtransmissionbyline",),
        formula_hint="Net annual inflow at node n.",
    ),

    # --- Capital investment — transmission -------------------------------
    "vcapitalinvestmenttransmission": ResultDependency(
        upstream_results=("vtransmissionbuilt",),
        formula_hint="Transmission line construction cost when built.",
    ),
    "vdiscountedcapitalinvestmenttransmission": ResultDependency(
        inputs=("DiscountRate",),
        upstream_results=("vcapitalinvestmenttransmission",),
    ),
    "voperatingcosttransmission": ResultDependency(
        upstream_results=("vtransmissionbyline", "vtransmissionexists"),
        formula_hint="Variable + fixed transmission O&M.",
    ),
    "vdiscountedoperatingcosttransmission": ResultDependency(
        inputs=("DiscountRate",),
        upstream_results=("voperatingcosttransmission",),
    ),
    "vfinancecosttransmission": ResultDependency(
        upstream_results=("vcapitalinvestmenttransmission",),
    ),
    "vsalvagevaluetransmission": ResultDependency(
        upstream_results=("vcapitalinvestmenttransmission",),
    ),
    "vdiscountedsalvagevaluetransmission": ResultDependency(
        inputs=("DiscountRate",),
        upstream_results=("vsalvagevaluetransmission",),
    ),

    # --- Storage ---------------------------------------------------------
    "vstoragelevelyearstart": ResultDependency(
        inputs=("StorageLevelStart",),
        formula_hint="Storage level at start of year y.",
    ),
    "vstoragelevelyearfinish": ResultDependency(
        upstream_results=("vstoragelevelyearstart", "vstoragelevelts"),
        formula_hint="Storage level at end of year y.",
    ),
    "vstoragelevelts": ResultDependency(
        inputs=("StorageMaxChargeRate", "StorageMaxDischargeRate",
                "TechnologyFromStorage", "TechnologyToStorage"),
        upstream_results=("vrateofactivity",),
        lower_bounds=("MinStorageCharge",),
        formula_hint="Storage level per time slice; dynamic balance with charge/discharge.",
    ),
}


def result_dependency(table: str) -> "ResultDependency | None":
    """Return the :class:`ResultDependency` for a result table, or None."""
    return RESULT_DEPENDENCIES.get(table)
