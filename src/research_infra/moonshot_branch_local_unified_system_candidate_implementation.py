"""Convert materialized candidate surfaces into final branch-local implementation actions."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION = (
    "src/research_infra/moonshot_branch_local_unified_system_candidate_implementation.py"
)


def to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stable_key(*parts: Any) -> str:
    payload = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _scope(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "tradability_status": row.get("tradability_status"),
        "available_timeframes": row.get("available_timeframes", []),
        "computed_proxy_delta": row.get("computed_proxy_delta"),
        "computed_proxy_delta_class": row.get("computed_proxy_delta_class"),
        "computed_proxy_score_basis": row.get("computed_proxy_score_basis"),
        "exact_R_availability": row.get("exact_R_availability"),
        "proxy_R_availability": row.get("proxy_R_availability"),
        "fillability_no_fill_status": row.get("fillability_no_fill_status"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def implementation_action_from_materialization(row: dict[str, Any]) -> tuple[str, str, str]:
    family = str(row.get("candidate_materialization_family") or "")
    if family == "SCORER_CODE_SURFACE_MATERIALIZATION":
        return (
            "IMPLEMENT_DEFAULT_OFF_SCORER_CODE_CANDIDATE",
            "IMPLEMENTATION_READY_DEFAULT_OFF_SCORER",
            "register scorer behind source/control guards",
        )
    if family == "NOFILL_CHALLENGER_COMPARATOR_MATERIALIZATION":
        return (
            "IMPLEMENT_NOFILL_CHALLENGER_COMPARATOR",
            "IMPLEMENTATION_READY_NOFILL_CHALLENGER",
            "compare challenger against status quo and sibling control",
        )
    if family == "AVOID_INVERSE_FILTER_MATERIALIZATION":
        return (
            "IMPLEMENT_AVOID_INVERSE_OR_ENTRY_FAILURE_FILTER",
            "IMPLEMENTATION_READY_AVOID_INVERSE_FILTER",
            "route adverse condition to avoid/inverse/default-off filter",
        )
    if family == "NON_SCALAR_SOURCE_GUARD_ACTION_MATERIALIZATION":
        return (
            "IMPLEMENT_NON_SCALAR_SOURCE_GUARD_OR_OPPORTUNITY_ACTION",
            "IMPLEMENTATION_READY_NON_SCALAR_ACTION",
            "bind source guard, opportunity audit, or context action",
        )
    return (
        "RUN_REPAIR_STRESS_CONTEXT_BEFORE_IMPLEMENTATION",
        "IMPLEMENTATION_REPAIR_STRESS_REQUIRED",
        "repair source/control or stress context before scorer use",
    )


def candidate_implementation_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    action, status, next_step = implementation_action_from_materialization(row)
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "candidate_implementation_decision_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-IMPLEMENTATION-{index:06d}",
        "input_candidate_materialization_decision_row_id": row.get("candidate_materialization_decision_row_id"),
        "input_candidate_dispatch_decision_row_id": row.get("input_candidate_dispatch_decision_row_id"),
        "input_candidate_runtime_decision_row_id": row.get("input_candidate_runtime_decision_row_id"),
        "input_candidate_execution_row_id": row.get("input_candidate_execution_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "candidate_materialization_family": row.get("candidate_materialization_family"),
        "candidate_materialization_status": row.get("candidate_materialization_status"),
        "candidate_implementation_action": action,
        "candidate_implementation_status": status,
        "candidate_implementation_next_step": next_step,
        "candidate_implementation_key": stable_key(row.get("candidate_materialization_key"), action, row.get("source_row_id")),
        "default_off_observation_score": row.get("default_off_observation_score"),
        "implementation_output_contract": "branch_local_default_off_code_or_research_execution_action",
        "materialization_row_consumed_in_implementation": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def scorer_code_integration_candidate(row: dict[str, Any], index: int) -> dict[str, Any]:
    ready = row.get("scorer_materialization_status") == "SCORER_CODE_SURFACE_READY_DEFAULT_OFF_WITH_GUARD"
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "scorer_code_integration_candidate_row_id": f"OHLC-GTOS-UNIFIED-SCORER-CODE-INTEGRATION-{index:05d}",
        "input_scorer_code_surface_materialization_row_id": row.get("scorer_code_surface_materialization_row_id"),
        "scorer_code_integration_status": (
            "SCORER_CODE_INTEGRATION_CANDIDATE_READY_DEFAULT_OFF"
            if ready
            else "SCORER_CODE_INTEGRATION_HELD_FOR_REPAIR_OR_REDESIGN"
        ),
        "proposed_registry_module": "src/research_infra/moonshot_branch_local_unified_system_candidate_implementation.py",
        "branch_local_registry_key": row.get("branch_local_registry_key"),
        "candidate_callable_name": row.get("candidate_callable_name"),
        "required_guards": row.get("required_guards", []),
        "implementation_spec": "register callable as default-off research scorer with fail-closed source/control guard",
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def source_control_run_action(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("source_control_materialization_status") or "")
    if status == "SOURCE_CONTROL_BUILDER_EXECUTABLE":
        run_status = "SOURCE_CONTROL_RUN_QUEUE_EXECUTE_NOW"
        action = "run_same_resource_source_control_builder"
    elif status == "SOURCE_CONTROL_BUILDER_REPAIR_OR_PROXY_REQUIRED":
        run_status = "SOURCE_CONTROL_RUN_QUEUE_REPAIR_OR_PROXY_REQUIRED"
        action = "repair_source_or_build_proxy_control"
    else:
        run_status = "SOURCE_CONTROL_RUN_QUEUE_CONTEXT_ONLY"
        action = "preserve_context_until_source_or_control_available"
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "source_control_run_action_row_id": f"OHLC-GTOS-UNIFIED-SOURCE-CONTROL-RUN-{index:05d}",
        "input_source_control_builder_materialization_row_id": row.get("source_control_builder_materialization_row_id"),
        "source_control_run_status": run_status,
        "source_control_run_action": action,
        "same_resource_execution_available": row.get("same_resource_execution_available"),
        "missing_source_proof": row.get("missing_source_proof", []),
        "builder_spec": row.get("builder_spec"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def score_control_execution_action(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("score_control_materialization_status") or "")
    if status == "SCORE_CONTROL_COMPARATOR_POSITIVE_READY":
        action_status = "SCORE_CONTROL_EXECUTE_COMPARATOR_READY"
        action = "execute_same_scope_score_control_comparison"
    elif status == "SCORE_CONTROL_COMPARATOR_REPAIR_REQUIRED":
        action_status = "SCORE_CONTROL_EXECUTION_REPAIR_REQUIRED"
        action = "route_to_source_control_builder_before_score_use"
    else:
        action_status = "SCORE_CONTROL_EXECUTION_CONTEXT_OR_REDESIGN"
        action = "preserve_as_context_or_redesign_input"
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "score_control_execution_action_row_id": f"OHLC-GTOS-UNIFIED-SCORE-CONTROL-EXECUTION-{index:05d}",
        "input_score_control_comparator_materialization_row_id": row.get("score_control_comparator_materialization_row_id"),
        "score_control_execution_status": action_status,
        "score_control_execution_action": action,
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "control_denominator_required": row.get("control_denominator_required"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def nofill_execution_action(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("nofill_materialization_status") or "")
    if status == "NOFILL_MATERIALIZE_POSITIVE_CHALLENGER_COMPARATOR":
        action_status = "NOFILL_EXECUTE_POSITIVE_CHALLENGER_COMPARATOR"
        action = "score_nofill_variant_against_status_quo_control"
    elif status == "NOFILL_MATERIALIZE_AVOID_INVERSE_FILTER":
        action_status = "NOFILL_EXECUTE_AVOID_INVERSE_FILTER"
        action = "score_adverse_condition_as_avoid_inverse_or_entry_failure"
    elif status == "NOFILL_MATERIALIZE_SOURCE_REPAIR_REQUIRED":
        action_status = "NOFILL_EXECUTION_SOURCE_REPAIR_REQUIRED"
        action = "repair_targetstop_source_or_no_fill_denominator"
    else:
        action_status = "NOFILL_EXECUTE_STRESS_CONTROL"
        action = "stress_cost_source_target_stop_and_status_quo_controls"
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "nofill_execution_action_row_id": f"OHLC-GTOS-UNIFIED-NOFILL-EXECUTION-{index:05d}",
        "input_nofill_comparator_materialization_row_id": row.get("nofill_comparator_materialization_row_id"),
        "nofill_execution_status": action_status,
        "nofill_execution_action": action,
        "nofill_system_role": row.get("nofill_system_role"),
        "status_quo_control_required": row.get("status_quo_control_required"),
        "opportunity_preserved_as": row.get("opportunity_preserved_as"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def guard_registry_action(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "guard_registry_action_row_id": f"OHLC-GTOS-UNIFIED-GUARD-REGISTRY-{index:05d}",
        "input_guard_enforcement_materialization_row_id": row.get("guard_enforcement_materialization_row_id"),
        "guard_registry_status": "GUARD_REGISTRY_BIND_FAIL_CLOSED_READY",
        "guard_registry_action": "bind_fail_closed_guard_before_score_or_variant_use",
        "guard_family": row.get("guard_family"),
        "fail_closed_condition": row.get("fail_closed_condition"),
        "guard_spec": row.get("guard_spec"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def opportunity_system_input_action(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "opportunity_system_input_action_row_id": f"OHLC-GTOS-UNIFIED-OPPORTUNITY-SYSTEM-INPUT-{index:05d}",
        "input_opportunity_materialization_row_id": row.get("opportunity_materialization_row_id"),
        "opportunity_system_input_status": "OPPORTUNITY_SYSTEM_INPUT_READY",
        "opportunity_system_input_action": row.get("opportunity_materialization_action"),
        "missed_opportunity_preserved": True,
        "preserved_roles": row.get("preserved_roles", []),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def recheck_run_action(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "recheck_run_action_row_id": f"OHLC-GTOS-UNIFIED-RECHECK-RUN-{index:05d}",
        "input_recheck_materialization_row_id": row.get("recheck_materialization_row_id"),
        "recheck_run_status": "RECHECK_RUN_QUEUE_READY",
        "recheck_run_action": row.get("recheck_materialization_action"),
        "missing_source_proof": row.get("missing_source_proof", []),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def market_priority_action(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("market_action_materialization_status") or "")
    if "SOURCE_REPAIR_OR_PROXY" in status:
        priority = "MARKET_PRIORITY_SOURCE_REPAIR_OR_PROXY_NOW"
    elif "SHADOW_DEFAULT_OFF" in status:
        priority = "MARKET_PRIORITY_SHADOW_DEFAULT_OFF"
    elif "PROXY_CONTROL" in status:
        priority = "MARKET_PRIORITY_PROXY_CONTROL_FEATURE"
    elif "SYSTEM_INPUT" in status:
        priority = "MARKET_PRIORITY_MERGE_SYSTEM_INPUT"
    elif "REJECTION" in status:
        priority = "MARKET_PRIORITY_PRESERVE_REJECTED_CLAIM_OPPORTUNITY"
    else:
        priority = "MARKET_PRIORITY_REPLAY_ONLY"
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "market_priority_action_row_id": f"OHLC-GTOS-UNIFIED-MARKET-PRIORITY-{index:05d}",
        "input_market_action_materialization_row_id": row.get("market_action_materialization_row_id"),
        "market_priority_status": priority,
        "market_action_materialization_status": row.get("market_action_materialization_status"),
        "market_action_materialization_role": row.get("market_action_materialization_role"),
        "market_action_materialization_action": row.get("market_action_materialization_action"),
        "symbol": row.get("symbol"),
        "broker_proxy_mapping": row.get("broker_proxy_mapping"),
        "tradability_status": row.get("tradability_status"),
        "data_source": row.get("data_source", []),
        "available_timeframes": row.get("available_timeframes", []),
        "session_kz_offkz_coverage": row.get("session_kz_offkz_coverage", []),
        "spread_cost_source": row.get("spread_cost_source"),
        "computed_action_rows": row.get("computed_action_rows"),
        "computed_delta_rows": row.get("computed_delta_rows"),
        "missing_evidence": row.get("missing_evidence", []),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def candidate_implementation_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("candidate_implementation_status")
            or row.get("scorer_code_integration_status")
            or row.get("source_control_run_status")
            or row.get("score_control_execution_status")
            or row.get("nofill_execution_status")
            or row.get("guard_registry_status")
            or row.get("opportunity_system_input_status")
            or row.get("recheck_run_status")
            or row.get("market_priority_status")
        )
        for row in rows
    )
    return {
        "unified_system_candidate_implementation": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION,
        "candidate_implementation_rollup_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-IMPLEMENTATION-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "row_count": len(rows),
        "status_counts": {key: int(status_counts[key]) for key in sorted(status_counts)},
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }
