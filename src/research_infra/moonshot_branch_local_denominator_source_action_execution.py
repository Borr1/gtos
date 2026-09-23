"""Action-execution helpers for denominator/source resolution rows."""

from __future__ import annotations

from typing import Any


DENOMINATOR_SOURCE_ACTION_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_source_action_execution.py"
)


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    numeric = to_float(value)
    return int(numeric) if numeric is not None else 0


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "denominator_source_action_execution_surface": DENOMINATOR_SOURCE_ACTION_EXECUTION_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def guarded_scorer_spec(row: dict[str, Any]) -> dict[str, Any]:
    score = to_float(row.get("scope_target_proxy_score_mean"))
    if score is not None and score >= 0.60:
        confidence = "GUARDED_SCOPE_PROXY_SCORE_GE_060"
    elif score is not None:
        confidence = "GUARDED_SCOPE_PROXY_SCORE_LT_060"
    else:
        confidence = "GUARDED_SCOPE_PROXY_SCORE_MISSING"
    return {
        **_base(row),
        "action_execution_lane": "GUARDED_SCORER_SPEC",
        "action_execution_status": "ACTION_EXEC_GUARDED_SCORER_SPEC_MATERIALIZED",
        "input_guarded_candidate_row_id": row.get("guarded_candidate_row_id"),
        "input_resolution_row_id": row.get("denominator_source_resolution_row_id"),
        "guarded_proxy_score_mean": score,
        "guarded_proxy_score_class": confidence,
        "target_action_rows": to_int(row.get("target_action_rows")),
        "target_underpowered_rows": to_int(row.get("target_underpowered_rows")),
        "proxy_scalar_interpretation_allowed": bool(row.get("proxy_scalar_interpretation_allowed")),
        "candidate_use_allowed_now": True,
        "candidate_registration": "register_research_only_guarded_scope_proxy_scorer",
        "required_guard": "continue_exact_control_scope_denominator_build_before_unconditional_scalar_use",
        "next_same_resource_action": row.get("next_same_resource_action"),
        "implementation_implication": row.get("implementation_implication"),
    }


def next_action_execution(row: dict[str, Any], resolution_row: dict[str, Any]) -> dict[str, Any]:
    action = row.get("next_same_resource_action")
    state = row.get("candidate_implementation_state")
    if action == "exact_control_target_denominator_build":
        status = "ACTION_EXEC_EXACT_CONTROL_TARGET_DENOMINATOR_BUILD_OPEN"
        lane = "EXACT_CONTROL_TARGET_BUILD"
        next_step = "expand_exact_scope_control_rows_or_keep_scalar_withheld"
    elif action == "exact_control_scope_denominator_build" and state == "GUARDED_PROXY_IMPLEMENTATION_CANDIDATE":
        status = "ACTION_EXEC_EXACT_CONTROL_SCOPE_GUARDED_SPEC_MATERIALIZED_BUILD_OPEN"
        lane = "EXACT_CONTROL_SCOPE_BUILD"
        next_step = "register_guarded_spec_and_continue_exact_scope_denominator_build"
    elif action == "exact_control_scope_denominator_build":
        status = "ACTION_EXEC_EXACT_CONTROL_SCOPE_DENOMINATOR_BUILD_OPEN"
        lane = "EXACT_CONTROL_SCOPE_BUILD"
        next_step = "expand_exact_scope_control_rows_before_scalar_use"
    elif action == "exact_source_rebuild_contradiction_check_only":
        status = "ACTION_EXEC_SOURCE_CONTRADICTION_CHECK_NEGATIVE_PROXY_PERSISTS"
        lane = "SOURCE_CONTRADICTION_CHECK"
        next_step = "preserve_kill_and_search_exact_source_contradiction_only"
    elif action == "horizon_targetability_repair_rescore":
        status = "ACTION_EXEC_HORIZON_REPAIR_RESCORING_REQUIRED"
        lane = "HORIZON_REPAIR"
        next_step = "materialize_repaired_targetability_rows_and_rescore"
    elif action == "horizon_targetability_redesign":
        status = "ACTION_EXEC_HORIZON_REDESIGN_REQUIRED"
        lane = "HORIZON_REDESIGN"
        next_step = "materialize_redesigned_targetability_definition_and_rescore"
    elif action == "horizon_targetability_repair_and_kill_check":
        status = "ACTION_EXEC_HORIZON_KILL_CHECK_REPAIR_REQUIRED"
        lane = "HORIZON_KILL_CHECK"
        next_step = "repair_targetability_then_kill_only_if_negative_persists"
    else:
        status = "ACTION_EXEC_RECHECK_NEXT_ACTION"
        lane = "RECHECK"
        next_step = "recheck_next_action_mapping"
    return {
        **_base(row),
        "action_execution_lane": lane,
        "action_execution_status": status,
        "input_next_compute_action_row_id": row.get("next_compute_action_row_id"),
        "input_resolution_row_id": row.get("input_resolution_row_id"),
        "source_resolution_lane": row.get("source_resolution_lane"),
        "candidate_implementation_state": state,
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "next_same_resource_action": action,
        "resolution_action": row.get("resolution_action"),
        "next_execution_step": next_step,
        "candidate_use_allowed_now": state == "GUARDED_PROXY_IMPLEMENTATION_CANDIDATE",
        "terminal_decision": bool(row.get("terminal_decision")),
        "resolution_status": resolution_row.get("denominator_source_resolution_status"),
        "decision_proxy_score": resolution_row.get("decision_proxy_score"),
        "decision_proxy_r_style_result_class": resolution_row.get("decision_proxy_r_style_result_class"),
        "rows_needed_to_n20": resolution_row.get("best_proxy_rows_needed_to_n20")
        if lane == "EXACT_CONTROL_TARGET_BUILD"
        else resolution_row.get("target_underpowered_rows"),
        "current_exact_gap_to_n20": resolution_row.get("current_exact_gap_to_n20"),
        "repaired_targetable_upper_bound_n": resolution_row.get("repaired_targetable_upper_bound_n"),
        "implementation_implication": row.get("implementation_implication"),
    }


def terminal_kill_preservation(row: dict[str, Any]) -> dict[str, Any]:
    state = row.get("candidate_implementation_state")
    if state == "SOURCE_PROXY_KILLED":
        status = "ACTION_EXEC_TERMINAL_SOURCE_PROXY_KILL_PRESERVED"
        next_step = "use_as_source_failure_or_avoid_intelligence_and_keep_contradiction_route"
    elif state == "HORIZON_KILLED":
        status = "ACTION_EXEC_TERMINAL_HORIZON_KILL_PRESERVED"
        next_step = "use_as_horizon_failure_intelligence_no_candidate_use"
    else:
        status = "ACTION_EXEC_TERMINAL_KILL_RECHECK"
        next_step = "recheck_terminal_kill_mapping"
    return {
        **_base(row),
        "action_execution_lane": "TERMINAL_KILL_PRESERVATION",
        "action_execution_status": status,
        "input_terminal_kill_row_id": row.get("terminal_kill_row_id"),
        "input_resolution_row_id": row.get("denominator_source_resolution_row_id"),
        "candidate_implementation_state": state,
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "candidate_use_allowed_now": False,
        "terminal_decision": True,
        "next_execution_step": next_step,
        "decision_proxy_score": row.get("decision_proxy_score"),
        "decision_proxy_r_style_result_class": row.get("decision_proxy_r_style_result_class"),
        "implementation_implication": row.get("implementation_implication"),
    }
