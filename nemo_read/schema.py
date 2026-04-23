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
