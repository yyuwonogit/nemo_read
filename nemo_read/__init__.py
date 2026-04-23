"""
nemo_read — decode LEAP/NEMO scenario SQLite databases.

Public API:
    NemoDB                              — connection wrapper
    inspect_scenario, print_overview    — one-shot overview

Dimensions (readers returning pandas DataFrames):
    regions, fuels, technologies, emissions, storages,
    modes_of_operation, years, timeslices, timeslice_groups,
    nodes, transmission_lines, region_groups

Parameters:
    get_parameter, get_parameter_raw, list_populated_parameters

Results:
    get_result, list_present_results, capacity_stack, energy_balance

Time-slicing:
    year_split, weighted_by_yearsplit, aggregate_to_group, HOURS_PER_YEAR

Export:
    to_dataarray, parameter_to_dataarray, result_to_dataarray,
    dump_to_csv, dump_to_parquet

Schema metadata:
    DIMENSIONS, PARAMETERS, RESULT_VARIABLES, DIMENSION_ABBREVIATIONS,
    TARGET_DB_VERSION
"""

from .db import NemoDB

from .inspect import inspect_scenario, print_overview

from .dimensions import (
    emissions, fuels, get_dimension, list_unused_technologies,
    modes_of_operation, nodes, regions, region_groups, storages,
    technologies, timeslices, timeslice_groups,
    transmission_candidates, transmission_lines, years,
)

from .parameters import (
    get_parameter, get_parameter_raw, list_populated_parameters,
)

from .variables import (
    capacity_stack, energy_balance, get_result, list_present_results,
)

from .timeslice import (
    HOURS_PER_YEAR, aggregate_to_group, weighted_by_yearsplit, year_split,
)

from .export import (
    dump_to_csv, dump_to_parquet, parameter_to_dataarray,
    result_to_dataarray, to_dataarray,
)

from .custom import (
    detect_slack_technologies, get_custom_constraint,
    list_custom_constraints, slack_technology_ids,
    SLACK_CAPITAL_COST_THRESHOLD, SLACK_RESIDUAL_CAPACITY_THRESHOLD,
)

from .leap_conventions import (
    LEAP_NEMO_UNITS, PJ_TO_J, GW_TO_W, T_TO_KG, MILLION,
    classify_technology_id, extract_leap_ids, fuels_with_leap_ids,
    technology_kinds, units_for,
)

from .validate import validate_scenario, ValidationIssue, ValidationReport

from .infeasibility import check_scenario, find_infeasibilities

from .timeslice import (
    HOURS_PER_YEAR, HOURS_PER_WEEK, aggregate_to_group,
    tsgroup_hours, weighted_by_yearsplit, year_split,
)

from .schema import (
    DIMENSION_ABBREVIATIONS, DIMENSIONS, PARAMETERS,
    RESULT_VARIABLES, TARGET_DB_VERSION,
)

from .scaffold import scaffold_package

__all__ = [
    "NemoDB",
    "inspect_scenario", "print_overview",
    "emissions", "fuels", "get_dimension", "list_unused_technologies",
    "modes_of_operation", "nodes",
    "regions", "region_groups", "storages", "technologies", "timeslices",
    "timeslice_groups", "transmission_candidates", "transmission_lines", "years",
    "get_parameter", "get_parameter_raw", "list_populated_parameters",
    "capacity_stack", "energy_balance", "get_result", "list_present_results",
    "HOURS_PER_YEAR", "HOURS_PER_WEEK", "aggregate_to_group",
    "tsgroup_hours", "weighted_by_yearsplit", "year_split",
    "dump_to_csv", "dump_to_parquet", "parameter_to_dataarray",
    "result_to_dataarray", "to_dataarray",
    "detect_slack_technologies", "get_custom_constraint",
    "list_custom_constraints", "slack_technology_ids",
    "SLACK_CAPITAL_COST_THRESHOLD", "SLACK_RESIDUAL_CAPACITY_THRESHOLD",
    "LEAP_NEMO_UNITS", "PJ_TO_J", "GW_TO_W", "T_TO_KG", "MILLION",
    "classify_technology_id", "extract_leap_ids", "fuels_with_leap_ids",
    "technology_kinds", "units_for",
    "validate_scenario", "ValidationIssue", "ValidationReport",
    "check_scenario", "find_infeasibilities",
    "DIMENSION_ABBREVIATIONS", "DIMENSIONS", "PARAMETERS",
    "RESULT_VARIABLES", "TARGET_DB_VERSION",
    "scaffold_package",
]

__version__ = "0.1.0"
