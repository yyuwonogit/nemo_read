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

Infeasibility resolution pipeline (11 stages, see docs/infeasibility_methodology.md):
    Stage 1  validate_scenario, find_infeasibilities, check_scenario
        — pre-flight static checks (run before calculatescenario).
    Stage 3  decode_lp_column, enumerate_dense_blocks
        — post-mortem offline decoding of CPLEX/LP `xN` column indices
          back to (variable, region, tech, year) tuples.
    Stages 4-5  classify_parameter, forensics_for_pinned_variable,
                propose_placeholders
        — pattern forensics on the data clusters around the pinned
          variable; ranked placeholder patches for diagnostic testing.
    Stage 7  emit_probe_brief
        — minimum LEAP COM read list when placeholders don't converge.
    Stage 10 inject/.../inject_to_leap.py (existing)
        — pushes patches via LEAP COM; refuses placeholder rows without
          --placeholder-mode flag.

Standardised LEAP COM frameworks (2026-05-17):
    CanonicalInjector   — subclass for sector-specific authoring pipelines.
        Sealed safe_set_expression chokepoint, area/scenario locks,
        warm-COM multi-phase flow (dry-run → confirm → real → readback),
        multi-scenario in one COM session. See docs/FLOWS.md §1.
    CanonicalProber     — subclass for long-running LEAP COM probes
        (results harvest, units harvest). Sealed safe_value /
        safe_data_unit_text reads, BT={3,50} popup-safe guard,
        heartbeat + progress JSON convention. See docs/FLOWS.md §2.
    HeartbeatLogger     — universal heartbeat + _progress_*.json file
        for any LEAP COM op > 60s (§A.16).
    safe_set_expression, normalize_interp, validate_canonical_csv_expressions,
    compare_expressions — the §A.15 Interp() separator enforcement
    primitives.
"""

from .db import NemoDB

from .inspect import inspect_scenario, print_overview

from .dimensions import (
    decode_dims, emissions, fuels, get_dimension, list_unused_technologies,
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
    LEAP_BRANCH_TYPES, LEAP_NEMO_UNITS, PJ_TO_J, GW_TO_W, T_TO_KG, MILLION,
    classify_technology_id, extract_leap_ids, fuels_with_leap_ids,
    resolve_leap_ids, technology_kinds, units_for,
)

from .leap_area import (
    CustomConstraintsDoc, LeapAreaContext,
    apply_audit_conversions, audit_canonical_units,
    infer_fuel_from_consumers,
    read_custom_constraints, read_demand, read_nemo_cfg,
    suggest_closest_branches, where_in_leap,
)

from .unit_conversions import (
    ConversionProposal, fuel_specific_alternatives,
    list_known_conversions, propose_conversion,
)

from .validate import validate_scenario, ValidationIssue, ValidationReport

from .infeasibility import check_scenario, find_infeasibilities

from .lp_column_decode import (
    ColumnIdentity, NEMO_DEFAULT_VARSTOSAVE,
    decode_lp_column, enumerate_dense_blocks,
)

from .parameter_forensics import (
    Cluster, DetectionResult, ForensicReport, PlaceholderProposal,
    PLACEHOLDER_SENTINEL, PLACEHOLDER_NOTE_PREFIX,
    VARIABLE_TO_CANDIDATE_PARAMS,
    classify_parameter, forensics_for_pinned_variable, propose_placeholders,
)

from .probe_brief import (
    ProbeBrief, ProbeBriefItem, emit_probe_brief, format_brief_text,
)

from .timeslice import (
    HOURS_PER_YEAR, HOURS_PER_WEEK, aggregate_to_group,
    tsgroup_hours, weighted_by_yearsplit, year_split,
)

from .schema import (
    DIMENSION_ABBREVIATIONS, DIMENSIONS, LEAP_SOURCE_MAP, LeapSource,
    PARAMETERS, RESULT_DEPENDENCIES, RESULT_VARIABLES, ResultDependency,
    TARGET_DB_VERSION, leap_source, result_dependency,
)

from .trace import (
    BOUND_ABSENT, BOUND_FREE, BOUND_HIT_LOWER, BOUND_HIT_UPPER, BOUND_UNKNOWN,
    BoundCheck, CostBreakdown, InputTrace, ResultTrace,
    trace_cost, trace_result,
)

from .scaffold import scaffold_package

# Standardised LEAP COM frameworks (2026-05-17)
from .inject_base import (
    CanonicalInjector, InjectorSealError,
)
from .probe_base import (
    CanonicalProber, ProberSealError,
    DEFAULT_RESULT_VARS, DEFAULT_INPUT_VARS,
    DEFAULT_RESULT_BRANCH_TYPES, DEFAULT_UNIT_BRANCH_TYPES,
    DEFAULT_YEARS,
)
from ._heartbeat import HeartbeatLogger, read_progress
from ._leap_com import (
    InterpSeparatorError,
    assert_interp_canonical, compare_expressions,
    normalize_interp, safe_set_expression,
    validate_canonical_csv_expressions,
)

__all__ = [
    "NemoDB",
    "inspect_scenario", "print_overview",
    "decode_dims",
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
    "LEAP_BRANCH_TYPES", "LEAP_NEMO_UNITS",
    "PJ_TO_J", "GW_TO_W", "T_TO_KG", "MILLION",
    "classify_technology_id", "extract_leap_ids", "fuels_with_leap_ids",
    "resolve_leap_ids", "technology_kinds", "units_for",
    "CustomConstraintsDoc", "LeapAreaContext",
    "apply_audit_conversions", "audit_canonical_units",
    "infer_fuel_from_consumers",
    "read_custom_constraints", "read_demand", "read_nemo_cfg",
    "suggest_closest_branches", "where_in_leap",
    "ConversionProposal", "fuel_specific_alternatives",
    "list_known_conversions", "propose_conversion",
    "validate_scenario", "ValidationIssue", "ValidationReport",
    "check_scenario", "find_infeasibilities",
    "ColumnIdentity", "NEMO_DEFAULT_VARSTOSAVE",
    "decode_lp_column", "enumerate_dense_blocks",
    "Cluster", "DetectionResult", "ForensicReport", "PlaceholderProposal",
    "PLACEHOLDER_SENTINEL", "PLACEHOLDER_NOTE_PREFIX",
    "VARIABLE_TO_CANDIDATE_PARAMS",
    "classify_parameter", "forensics_for_pinned_variable",
    "propose_placeholders",
    "ProbeBrief", "ProbeBriefItem", "emit_probe_brief", "format_brief_text",
    "DIMENSION_ABBREVIATIONS", "DIMENSIONS", "LEAP_SOURCE_MAP", "LeapSource",
    "PARAMETERS", "RESULT_DEPENDENCIES", "RESULT_VARIABLES", "ResultDependency",
    "TARGET_DB_VERSION", "leap_source", "result_dependency",
    "BOUND_ABSENT", "BOUND_FREE", "BOUND_HIT_LOWER", "BOUND_HIT_UPPER",
    "BOUND_UNKNOWN",
    "BoundCheck", "CostBreakdown", "InputTrace", "ResultTrace",
    "trace_cost", "trace_result",
    "scaffold_package",
    # Standardised LEAP COM frameworks (2026-05-17, §A.10 + §A.15 + §A.16)
    "CanonicalInjector", "InjectorSealError",
    "CanonicalProber", "ProberSealError",
    "DEFAULT_RESULT_VARS", "DEFAULT_INPUT_VARS",
    "DEFAULT_RESULT_BRANCH_TYPES", "DEFAULT_UNIT_BRANCH_TYPES",
    "DEFAULT_YEARS",
    "HeartbeatLogger", "read_progress",
    "InterpSeparatorError",
    "assert_interp_canonical", "compare_expressions",
    "normalize_interp", "safe_set_expression",
    "validate_canonical_csv_expressions",
]

__version__ = "0.6.9"
