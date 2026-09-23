"""Execute branch-local candidate implementation actions into concrete artifacts."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION = (
    "src/research_infra/moonshot_branch_local_unified_system_candidate_implementation_execution.py"
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


def score_band(value: float | None) -> str:
    if value is None:
        return "SCORE_BAND_NO_SCALAR"
    if value >= 0.30:
        return "SCORE_BAND_STRONG"
    if value >= 0.15:
        return "SCORE_BAND_MEDIUM"
    if value > 0.0:
        return "SCORE_BAND_WEAK_POSITIVE"
    if value == 0.0:
        return "SCORE_BAND_ZERO"
    if value > -0.15:
        return "SCORE_BAND_WEAK_NEGATIVE"
    return "SCORE_BAND_STRONG_NEGATIVE"


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


def implementation_execution_family(row: dict[str, Any]) -> tuple[str, str, str, str]:
    action = str(row.get("candidate_implementation_action") or "")
    if action == "IMPLEMENT_DEFAULT_OFF_SCORER_CODE_CANDIDATE":
        return (
            "EXECUTE_DEFAULT_OFF_SCORER_MODULE",
            "CANDIDATE_IMPLEMENTATION_EXECUTED_DEFAULT_OFF_SCORER_MODULE",
            "register_default_off_scorer_module_artifact",
            "default_off_scorer_module",
        )
    if action == "IMPLEMENT_NOFILL_CHALLENGER_COMPARATOR":
        return (
            "EXECUTE_NOFILL_CHALLENGER_COMPARATOR_OUTPUT",
            "CANDIDATE_IMPLEMENTATION_EXECUTED_NOFILL_CHALLENGER_COMPARATOR",
            "write_nofill_status_quo_vs_challenger_output",
            "nofill_challenger_comparator",
        )
    if action == "IMPLEMENT_AVOID_INVERSE_OR_ENTRY_FAILURE_FILTER":
        return (
            "EXECUTE_AVOID_INVERSE_ENTRY_FAILURE_OUTPUT",
            "CANDIDATE_IMPLEMENTATION_EXECUTED_AVOID_INVERSE_FILTER",
            "write_avoid_inverse_or_entry_failure_filter_output",
            "avoid_inverse_entry_failure_filter",
        )
    if action == "IMPLEMENT_NON_SCALAR_SOURCE_GUARD_OR_OPPORTUNITY_ACTION":
        return (
            "EXECUTE_NON_SCALAR_SOURCE_GUARD_OR_OPPORTUNITY_OUTPUT",
            "CANDIDATE_IMPLEMENTATION_EXECUTED_NON_SCALAR_ACTION",
            "write_source_guard_opportunity_or_context_output",
            "non_scalar_source_guard_or_opportunity",
        )
    return (
        "EXECUTE_REPAIR_STRESS_CONTEXT_OUTPUT",
        "CANDIDATE_IMPLEMENTATION_EXECUTED_REPAIR_STRESS_CONTEXT",
        "write_repair_stress_context_output",
        "repair_stress_context_action",
    )


def candidate_implementation_execution_result(row: dict[str, Any], index: int) -> dict[str, Any]:
    family, status, action, output_component = implementation_execution_family(row)
    delta = to_float(row.get("computed_proxy_delta"))
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "candidate_implementation_execution_result_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-IMPL-EXEC-{index:06d}",
        "input_candidate_implementation_decision_row_id": row.get("candidate_implementation_decision_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "candidate_implementation_action": row.get("candidate_implementation_action"),
        "candidate_implementation_status": row.get("candidate_implementation_status"),
        "implementation_execution_family": family,
        "implementation_execution_status": status,
        "implementation_execution_action": action,
        "implementation_output_component": output_component,
        "implementation_execution_key": stable_key(
            row.get("candidate_implementation_key"),
            row.get("candidate_implementation_action"),
            row.get("source_row_id"),
        ),
        "proxy_delta_band": score_band(delta),
        "default_off_observation_score": row.get("default_off_observation_score"),
        "positive_opportunity_role": (
            "default_off_scorer_or_challenger_comparator"
            if delta is not None and delta > 0
            else "not_positive_current_proxy"
        ),
        "negative_opportunity_role": (
            "avoid_inverse_entry_failure_or_control_context"
            if delta is not None and delta < 0
            else "not_negative_current_proxy"
        ),
        "implementation_row_consumed_in_execution": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def scorer_module_artifact(row: dict[str, Any], index: int) -> dict[str, Any]:
    ready = row.get("scorer_code_integration_status") == "SCORER_CODE_INTEGRATION_CANDIDATE_READY_DEFAULT_OFF"
    delta = to_float(row.get("computed_proxy_delta"))
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "scorer_module_artifact_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SCORER-MODULE-{index:05d}",
        "input_scorer_code_integration_candidate_row_id": row.get("scorer_code_integration_candidate_row_id"),
        "scorer_module_artifact_status": (
            "SCORER_MODULE_ARTIFACT_DEFAULT_OFF_REGISTERED"
            if ready
            else "SCORER_MODULE_ARTIFACT_HELD_FOR_REPAIR_OR_REDESIGN"
        ),
        "branch_local_registry_key": row.get("branch_local_registry_key"),
        "candidate_callable_name": row.get("candidate_callable_name") or f"score_candidate_implementation_{index:05d}",
        "proposed_registry_module": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "required_guards": row.get("required_guards", []),
        "event_match_policy": "match_symbol_session_horizon_primitive_scope_then_emit_research_observation",
        "score_policy": "proxy_delta_default_off_no_unconditional_scalar_use",
        "scorer_proxy_score": max(delta or 0.0, 0.0),
        "scorer_proxy_score_band": score_band(delta),
        "module_artifact_executable_now": ready,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def source_control_run_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("source_control_run_status") or "")
    if status == "SOURCE_CONTROL_RUN_QUEUE_EXECUTE_NOW":
        output_status = "SOURCE_CONTROL_OUTPUT_EXECUTABLE_BUILDER_SPEC"
        output_action = "execute_same_resource_source_control_builder"
        executable = True
    elif status == "SOURCE_CONTROL_RUN_QUEUE_REPAIR_OR_PROXY_REQUIRED":
        output_status = "SOURCE_CONTROL_OUTPUT_REPAIR_OR_PROXY_SPEC"
        output_action = "repair_source_or_build_proxy_control_then_rescore"
        executable = True
    else:
        output_status = "SOURCE_CONTROL_OUTPUT_CONTEXT_ONLY"
        output_action = "preserve_context_until_better_source_control_available"
        executable = False
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "source_control_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SOURCE-CONTROL-OUTPUT-{index:05d}",
        "input_source_control_run_action_row_id": row.get("source_control_run_action_row_id"),
        "source_control_output_status": output_status,
        "source_control_output_action": output_action,
        "builder_spec": row.get("builder_spec"),
        "same_resource_execution_available": row.get("same_resource_execution_available"),
        "missing_source_proof": row.get("missing_source_proof", []),
        "source_control_output_contract": "source_control_result_row_rejoins_candidate_scope_before_score_use",
        "source_control_executable_now": executable,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def score_control_comparator_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("score_control_execution_status") or "")
    delta = to_float(row.get("computed_proxy_delta"))
    if status == "SCORE_CONTROL_EXECUTE_COMPARATOR_READY":
        output_status = "SCORE_CONTROL_OUTPUT_COMPARATOR_READY"
        output_action = "score_candidate_against_pass_control_delta"
        executable = True
    elif status == "SCORE_CONTROL_EXECUTION_REPAIR_REQUIRED":
        output_status = "SCORE_CONTROL_OUTPUT_SOURCE_REPAIR_REQUIRED"
        output_action = "repair_source_control_before_comparator_score"
        executable = False
    else:
        output_status = "SCORE_CONTROL_OUTPUT_CONTEXT_OR_REDESIGN"
        output_action = "preserve_comparator_as_context_or_redesign_input"
        executable = False
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "score_control_comparator_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SCORE-CONTROL-OUTPUT-{index:05d}",
        "input_score_control_execution_action_row_id": row.get("score_control_execution_action_row_id"),
        "score_control_output_status": output_status,
        "score_control_output_action": output_action,
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "control_denominator_required": row.get("control_denominator_required"),
        "comparator_proxy_score": max(delta or 0.0, 0.0),
        "comparator_proxy_score_band": score_band(delta),
        "score_control_executable_now": executable,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def nofill_comparator_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("nofill_execution_status") or "")
    delta = to_float(row.get("computed_proxy_delta"))
    if status == "NOFILL_EXECUTE_POSITIVE_CHALLENGER_COMPARATOR":
        output_status = "NOFILL_OUTPUT_POSITIVE_CHALLENGER_COMPARATOR_READY"
        output_action = "execute_status_quo_vs_nofill_challenger_comparator"
        system_role = "positive_challenger_comparator"
    elif status == "NOFILL_EXECUTE_AVOID_INVERSE_FILTER":
        output_status = "NOFILL_OUTPUT_AVOID_INVERSE_FILTER_READY"
        output_action = "execute_avoid_inverse_or_entry_failure_filter_observation"
        system_role = "avoid_inverse_or_entry_failure_filter"
    elif status == "NOFILL_EXECUTION_SOURCE_REPAIR_REQUIRED":
        output_status = "NOFILL_OUTPUT_SOURCE_REPAIR_REQUIRED"
        output_action = "repair_target_stop_or_no_fill_source_before_decision"
        system_role = "source_repair_before_nofill_decision"
    else:
        output_status = "NOFILL_OUTPUT_STRESS_CONTROL_READY"
        output_action = "execute_cost_source_target_stop_stress_control"
        system_role = "stress_control_before_enable"
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "nofill_comparator_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-NOFILL-OUTPUT-{index:05d}",
        "input_nofill_execution_action_row_id": row.get("nofill_execution_action_row_id"),
        "nofill_output_status": output_status,
        "nofill_output_action": output_action,
        "nofill_system_role": system_role,
        "status_quo_control_required": row.get("status_quo_control_required"),
        "opportunity_preserved_as": row.get("opportunity_preserved_as"),
        "nofill_proxy_score": max(delta or 0.0, 0.0),
        "nofill_proxy_score_band": score_band(delta),
        "negative_signal_preserved_as_filter": status == "NOFILL_EXECUTE_AVOID_INVERSE_FILTER",
        "nofill_output_executable_now": status != "NOFILL_EXECUTION_SOURCE_REPAIR_REQUIRED",
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def guard_registry_artifact(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "guard_registry_artifact_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-GUARD-ARTIFACT-{index:05d}",
        "input_guard_registry_action_row_id": row.get("guard_registry_action_row_id"),
        "guard_registry_artifact_status": "GUARD_REGISTRY_ARTIFACT_BOUND_FAIL_CLOSED",
        "guard_registry_artifact_action": "bind_fail_closed_guard_to_candidate_scope",
        "guard_family": row.get("guard_family"),
        "fail_closed_condition": row.get("fail_closed_condition"),
        "guard_spec": row.get("guard_spec"),
        "guard_blocks_unconditional_score_use": True,
        "guard_artifact_executable_now": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def opportunity_system_input_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "opportunity_system_input_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-OPPORTUNITY-OUTPUT-{index:05d}",
        "input_opportunity_system_input_row_id": row.get("opportunity_system_input_row_id"),
        "opportunity_output_status": "OPPORTUNITY_OUTPUT_READY_FOR_SYSTEM_CONTEXT_OR_REDESIGN",
        "opportunity_output_action": "merge_current_claim_failure_intelligence_into_system_context",
        "opportunity_system_role": row.get("opportunity_system_role"),
        "current_claim_failure_preserved": True,
        "underlying_mechanism_not_discarded": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def recheck_run_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "recheck_run_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RECHECK-OUTPUT-{index:05d}",
        "input_recheck_run_action_row_id": row.get("recheck_run_action_row_id"),
        "recheck_output_status": "RECHECK_OUTPUT_READY",
        "recheck_output_action": "recheck_source_targetability_horizon_and_route_to_next_concrete_action",
        "recheck_reason": row.get("recheck_reason"),
        "recheck_executable_now": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def market_priority_execution_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("market_priority_status") or "")
    if status == "MARKET_PRIORITY_SOURCE_REPAIR_OR_PROXY_NOW":
        action = "execute_market_source_repair_or_proxy"
    elif status == "MARKET_PRIORITY_SHADOW_DEFAULT_OFF":
        action = "register_market_shadow_default_off_candidate"
    elif status == "MARKET_PRIORITY_PROXY_CONTROL_FEATURE":
        action = "merge_market_as_proxy_control_feature"
    elif status == "MARKET_PRIORITY_MERGE_SYSTEM_INPUT":
        action = "merge_market_context_as_system_input"
    elif status == "MARKET_PRIORITY_PRESERVE_REJECTED_CLAIM_OPPORTUNITY":
        action = "preserve_market_rejected_claim_opportunity"
    else:
        action = "preserve_market_replay_only_scope"
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "market_priority_execution_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MARKET-OUTPUT-{index:05d}",
        "input_market_priority_action_row_id": row.get("market_priority_action_row_id"),
        "market_priority_execution_status": f"{status}_EXECUTED",
        "market_priority_execution_action": action,
        "market_action_materialization_status": row.get("market_action_materialization_status"),
        "market_action_materialization_role": row.get("market_action_materialization_role"),
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
        "market_priority_consumed_in_execution": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
    }


def candidate_implementation_execution_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("implementation_execution_status")
            or row.get("scorer_module_artifact_status")
            or row.get("source_control_output_status")
            or row.get("score_control_output_status")
            or row.get("nofill_output_status")
            or row.get("guard_registry_artifact_status")
            or row.get("opportunity_output_status")
            or row.get("recheck_output_status")
            or row.get("market_priority_execution_status")
        )
        for row in rows
    )
    return {
        "unified_system_candidate_implementation_execution": UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_EXECUTION,
        "candidate_implementation_execution_rollup_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-IMPL-EXEC-ROLLUP-{index:05d}",
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
