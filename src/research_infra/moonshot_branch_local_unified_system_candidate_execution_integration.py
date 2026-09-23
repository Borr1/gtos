"""Integrate candidate implementation execution outputs into branch-local system artifacts."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION = (
    "src/research_infra/moonshot_branch_local_unified_system_candidate_execution_integration.py"
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


def integration_family(row: dict[str, Any]) -> tuple[str, str, str]:
    family = str(row.get("implementation_execution_family") or "")
    if family == "EXECUTE_DEFAULT_OFF_SCORER_MODULE":
        return (
            "INTEGRATE_DEFAULT_OFF_SCORER_REGISTRY_MODULE",
            "EXECUTION_INTEGRATION_DEFAULT_OFF_SCORER_READY",
            "register_branch_local_default_off_scorer_module",
        )
    if family == "EXECUTE_NOFILL_CHALLENGER_COMPARATOR_OUTPUT":
        return (
            "INTEGRATE_NOFILL_CHALLENGER_COMPARATOR_RESULT",
            "EXECUTION_INTEGRATION_NOFILL_CHALLENGER_READY",
            "materialize_nofill_challenger_result_for_status_quo_comparison",
        )
    if family == "EXECUTE_AVOID_INVERSE_ENTRY_FAILURE_OUTPUT":
        return (
            "INTEGRATE_AVOID_INVERSE_ENTRY_FAILURE_RESULT",
            "EXECUTION_INTEGRATION_AVOID_INVERSE_READY",
            "materialize_avoid_inverse_entry_failure_result",
        )
    if family == "EXECUTE_NON_SCALAR_SOURCE_GUARD_OR_OPPORTUNITY_OUTPUT":
        return (
            "INTEGRATE_NON_SCALAR_GUARD_SOURCE_OR_OPPORTUNITY_RESULT",
            "EXECUTION_INTEGRATION_NON_SCALAR_SYSTEM_INPUT_READY",
            "materialize_guard_source_or_opportunity_system_input",
        )
    return (
        "INTEGRATE_REPAIR_STRESS_CONTEXT_RESULT",
        "EXECUTION_INTEGRATION_REPAIR_STRESS_CONTEXT_READY",
        "materialize_repair_stress_context_result",
    )


def execution_integration_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    family, status, action = integration_family(row)
    delta = to_float(row.get("computed_proxy_delta"))
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "execution_integration_decision_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-EXEC-INTEGRATION-{index:06d}",
        "input_candidate_implementation_execution_result_row_id": row.get("candidate_implementation_execution_result_row_id"),
        "input_candidate_implementation_decision_row_id": row.get("input_candidate_implementation_decision_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "implementation_execution_family": row.get("implementation_execution_family"),
        "implementation_execution_status": row.get("implementation_execution_status"),
        "execution_integration_family": family,
        "execution_integration_status": status,
        "execution_integration_action": action,
        "integration_result_key": stable_key(
            row.get("implementation_execution_key"),
            row.get("implementation_execution_family"),
            row.get("source_row_id"),
        ),
        "integration_proxy_delta": delta,
        "integration_positive_role": (
            "candidate_scoring_or_challenger_component" if delta is not None and delta > 0 else "not_positive_current_proxy"
        ),
        "integration_negative_role": (
            "avoid_inverse_failure_or_context_component" if delta is not None and delta < 0 else "not_negative_current_proxy"
        ),
        "execution_result_row_consumed_in_integration": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def registry_module_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    ready = row.get("scorer_module_artifact_status") == "SCORER_MODULE_ARTIFACT_DEFAULT_OFF_REGISTERED"
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "registry_module_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-REGISTRY-MODULE-{index:05d}",
        "input_scorer_module_artifact_row_id": row.get("scorer_module_artifact_row_id"),
        "registry_module_status": (
            "REGISTRY_MODULE_DEFAULT_OFF_EVENT_MATCH_READY"
            if ready
            else "REGISTRY_MODULE_HELD_FOR_REPAIR_OR_REDESIGN"
        ),
        "branch_local_registry_key": row.get("branch_local_registry_key"),
        "candidate_callable_name": row.get("candidate_callable_name"),
        "event_match_policy": row.get("event_match_policy"),
        "required_guards": row.get("required_guards", []),
        "default_off": True,
        "module_artifact_executable_now": row.get("module_artifact_executable_now"),
        "integration_contract": "branch_local_registry_row_with_fail_closed_guard_and_event_match_scope",
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def source_control_result_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("source_control_output_status") or "")
    if status == "SOURCE_CONTROL_OUTPUT_EXECUTABLE_BUILDER_SPEC":
        result_status = "SOURCE_CONTROL_RESULT_BUILDER_EXECUTION_READY"
        result_action = "execute_builder_and_rejoin_result_to_candidate_scope"
    elif status == "SOURCE_CONTROL_OUTPUT_REPAIR_OR_PROXY_SPEC":
        result_status = "SOURCE_CONTROL_RESULT_REPAIR_PROXY_EXECUTION_READY"
        result_action = "execute_repair_or_proxy_then_rejoin_result_to_candidate_scope"
    else:
        result_status = "SOURCE_CONTROL_RESULT_CONTEXT_ONLY"
        result_action = "preserve_context_until_source_control_route_available"
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "source_control_result_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SOURCE-CONTROL-RESULT-{index:05d}",
        "input_source_control_output_row_id": row.get("source_control_output_row_id"),
        "source_control_result_status": result_status,
        "source_control_result_action": result_action,
        "builder_spec": row.get("builder_spec"),
        "same_resource_execution_available": row.get("same_resource_execution_available"),
        "missing_source_proof": row.get("missing_source_proof", []),
        "result_rejoin_contract": "source_control_result_must_rejoin_same_scope_before_any_score_use",
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def score_control_result_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("score_control_output_status") or "")
    if status == "SCORE_CONTROL_OUTPUT_COMPARATOR_READY":
        result_status = "SCORE_CONTROL_RESULT_COMPARATOR_SCORABLE"
        result_action = "score_against_pass_control_delta_and_preserve_result"
    elif status == "SCORE_CONTROL_OUTPUT_SOURCE_REPAIR_REQUIRED":
        result_status = "SCORE_CONTROL_RESULT_SOURCE_REPAIR_REQUIRED"
        result_action = "route_to_source_control_result_before_score"
    else:
        result_status = "SCORE_CONTROL_RESULT_CONTEXT_OR_REDESIGN"
        result_action = "preserve_as_context_or_redesign_input"
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "score_control_result_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SCORE-CONTROL-RESULT-{index:05d}",
        "input_score_control_comparator_output_row_id": row.get("score_control_comparator_output_row_id"),
        "score_control_result_status": result_status,
        "score_control_result_action": result_action,
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "control_denominator_required": row.get("control_denominator_required"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def nofill_result_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("nofill_output_status") or "")
    if status == "NOFILL_OUTPUT_POSITIVE_CHALLENGER_COMPARATOR_READY":
        result_status = "NOFILL_RESULT_POSITIVE_CHALLENGER_SCORABLE"
        result_action = "score_status_quo_vs_challenger_result"
    elif status == "NOFILL_OUTPUT_AVOID_INVERSE_FILTER_READY":
        result_status = "NOFILL_RESULT_AVOID_INVERSE_FILTER_SCORABLE"
        result_action = "score_avoid_inverse_entry_failure_result"
    elif status == "NOFILL_OUTPUT_SOURCE_REPAIR_REQUIRED":
        result_status = "NOFILL_RESULT_SOURCE_REPAIR_REQUIRED"
        result_action = "repair_target_stop_or_no_fill_source_then_rescore"
    else:
        result_status = "NOFILL_RESULT_STRESS_CONTROL_SCORABLE"
        result_action = "score_cost_source_target_stop_stress_control"
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "nofill_result_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-NOFILL-RESULT-{index:05d}",
        "input_nofill_comparator_output_row_id": row.get("nofill_comparator_output_row_id"),
        "nofill_result_status": result_status,
        "nofill_result_action": result_action,
        "nofill_system_role": row.get("nofill_system_role"),
        "status_quo_control_required": row.get("status_quo_control_required"),
        "opportunity_preserved_as": row.get("opportunity_preserved_as"),
        "negative_signal_preserved_as_filter": row.get("negative_signal_preserved_as_filter"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def guard_bound_integration_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "guard_bound_integration_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-GUARD-BOUND-{index:05d}",
        "input_guard_registry_artifact_row_id": row.get("guard_registry_artifact_row_id"),
        "guard_bound_status": "GUARD_BOUND_INTEGRATION_FAIL_CLOSED_READY",
        "guard_bound_action": "attach_guard_to_registry_source_nofill_or_market_integration_result",
        "guard_family": row.get("guard_family"),
        "fail_closed_condition": row.get("fail_closed_condition"),
        "guard_spec": row.get("guard_spec"),
        "guard_blocks_unconditional_score_use": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def opportunity_integration_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "opportunity_integration_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-OPPORTUNITY-INTEGRATION-{index:05d}",
        "input_opportunity_system_input_output_row_id": row.get("opportunity_system_input_output_row_id"),
        "opportunity_integration_status": "OPPORTUNITY_INTEGRATION_SYSTEM_CONTEXT_READY",
        "opportunity_integration_action": "merge_failure_intelligence_into_candidate_system_context",
        "current_claim_failure_preserved": row.get("current_claim_failure_preserved") is not False,
        "underlying_mechanism_not_discarded": row.get("underlying_mechanism_not_discarded") is not False,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def recheck_integration_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "recheck_integration_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RECHECK-INTEGRATION-{index:05d}",
        "input_recheck_run_output_row_id": row.get("recheck_run_output_row_id"),
        "recheck_integration_status": "RECHECK_INTEGRATION_READY",
        "recheck_integration_action": "execute_recheck_then_route_to_source_control_or_candidate_integration",
        "recheck_reason": row.get("recheck_reason"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def market_system_integration_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("market_priority_execution_status") or "")
    if "SOURCE_REPAIR_OR_PROXY_NOW" in status:
        integration_status = "MARKET_SYSTEM_INTEGRATION_SOURCE_REPAIR_PROXY_READY"
        integration_action = "execute_market_source_repair_proxy_before_candidate_use"
    elif "SHADOW_DEFAULT_OFF" in status:
        integration_status = "MARKET_SYSTEM_INTEGRATION_SHADOW_DEFAULT_OFF_READY"
        integration_action = "register_market_shadow_candidate_default_off"
    elif "PROXY_CONTROL_FEATURE" in status:
        integration_status = "MARKET_SYSTEM_INTEGRATION_PROXY_CONTROL_FEATURE_READY"
        integration_action = "merge_market_as_proxy_control_feature"
    elif "MERGE_SYSTEM_INPUT" in status:
        integration_status = "MARKET_SYSTEM_INTEGRATION_SYSTEM_INPUT_READY"
        integration_action = "merge_market_context_as_system_input"
    elif "PRESERVE_REJECTED_CLAIM_OPPORTUNITY" in status:
        integration_status = "MARKET_SYSTEM_INTEGRATION_REJECTED_CLAIM_OPPORTUNITY_READY"
        integration_action = "preserve_market_opportunity_for_redesign_or_context"
    else:
        integration_status = "MARKET_SYSTEM_INTEGRATION_REPLAY_ONLY_READY"
        integration_action = "preserve_replay_only_scope_for_comparator_or_context"
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "market_system_integration_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MARKET-INTEGRATION-{index:05d}",
        "input_market_priority_execution_output_row_id": row.get("market_priority_execution_output_row_id"),
        "market_system_integration_status": integration_status,
        "market_system_integration_action": integration_action,
        "market_priority_execution_status": row.get("market_priority_execution_status"),
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
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
    }


def execution_integration_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("execution_integration_status")
            or row.get("registry_module_status")
            or row.get("source_control_result_status")
            or row.get("score_control_result_status")
            or row.get("nofill_result_status")
            or row.get("guard_bound_status")
            or row.get("opportunity_integration_status")
            or row.get("recheck_integration_status")
            or row.get("market_system_integration_status")
        )
        for row in rows
    )
    return {
        "unified_system_candidate_execution_integration": UNIFIED_SYSTEM_CANDIDATE_EXECUTION_INTEGRATION,
        "execution_integration_rollup_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-EXEC-INTEGRATION-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "row_count": len(rows),
        "status_counts": {key: int(status_counts[key]) for key in sorted(status_counts)},
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
