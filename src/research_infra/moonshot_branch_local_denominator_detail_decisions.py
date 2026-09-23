"""Decision helpers that consume denominator detail execution rows."""

from __future__ import annotations

from typing import Any


DETAIL_DECISION_SURFACE = "src/research_infra/moonshot_branch_local_denominator_detail_decisions.py"


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "detail_decision_surface": DETAIL_DECISION_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def _to_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def exact_control_expansion_decision(row: dict[str, Any]) -> dict[str, Any]:
    status = row.get("detail_execution_status")
    if status == "DETAIL_EXEC_EXACT_CONTROL_TARGET_EXACT_UNAVAILABLE_PROXY_UNDER_N20":
        decision_status = "EXACT_CONTROL_EXPANSION_TARGET_EXACT_UNAVAILABLE_BUILD_REQUIRED"
        implementation_action = "build_exact_target_control_denominator_before_scalar_use"
        default_off_permission = "BLOCK_DEFAULT_OFF_UNTIL_EXACT_CONTROL_TARGET_N20"
        candidate_use = False
    elif status == "DETAIL_EXEC_EXACT_CONTROL_SCOPE_GUARDED_SCORER_REGISTERED_BUILD_OPEN_TARGETS_UNDER_N20":
        decision_status = "EXACT_CONTROL_EXPANSION_SCOPE_GUARDED_SCORER_DEFAULT_OFF_READY_BUILD_OPEN"
        implementation_action = "keep_guarded_scope_proxy_default_off_and_continue_exact_scope_build"
        default_off_permission = "ALLOW_RESEARCH_ONLY_DEFAULT_OFF_GUARDED_SCOPE_SCORER"
        candidate_use = True
    else:
        decision_status = "EXACT_CONTROL_EXPANSION_SCOPE_BUILD_OPEN_NO_SCALAR"
        implementation_action = "build_exact_scope_control_denominator_before_scalar_use"
        default_off_permission = "BLOCK_DEFAULT_OFF_UNTIL_EXACT_CONTROL_SCOPE_N20"
        candidate_use = False
    return {
        **_base(row),
        "input_detail_execution_row_id": row.get("denominator_detail_execution_row_id"),
        "detail_execution_status": status,
        "exact_control_expansion_status": decision_status,
        "exact_control_expansion_action": implementation_action,
        "default_off_permission": default_off_permission,
        "best_available_proxy_relation": row.get("best_available_proxy_relation"),
        "best_available_proxy_member_count": _to_int(row.get("best_available_proxy_member_count")),
        "best_proxy_rows_needed_to_n20": _to_int(row.get("best_proxy_rows_needed_to_n20") or row.get("rows_needed_to_n20")),
        "exact_control_member_count": _to_int(row.get("exact_control_member_count")),
        "target_action_rows": _to_int(row.get("target_action_rows")),
        "target_underpowered_rows": _to_int(row.get("target_underpowered_rows")),
        "candidate_use_allowed_now": candidate_use,
        "unconditional_scalar_use_allowed": False,
        "decision_result": "BUILD_OR_GUARDED_ONLY",
        "next_same_resource_action": implementation_action,
    }


def source_completeness_decision(row: dict[str, Any]) -> dict[str, Any]:
    contradiction = bool(row.get("proxy_contradiction_found"))
    proxy_class = row.get("decision_proxy_r_style_result_class")
    if proxy_class == "PROXY_R_INTERVAL_ALL_NEGATIVE" and not contradiction:
        status = "SOURCE_COMPLETENESS_NO_EXACT_CONTRADICTION_NEGATIVE_PROXY_KILL_PERSISTS"
        decision = "preserve_source_proxy_kill_and_use_as_failure_or_avoid_intelligence"
        implementation_permission = "DO_NOT_IMPLEMENT_SOURCE_PROXY_BRANCH"
    elif contradiction:
        status = "SOURCE_COMPLETENESS_EXACT_CONTRADICTION_FOUND_REPAIR_REQUIRED"
        decision = "repair_source_proxy_kill_before_any_candidate_use"
        implementation_permission = "REPAIR_BEFORE_DEFAULT_OFF"
    else:
        status = "SOURCE_COMPLETENESS_RECHECK_PROXY_CLASS"
        decision = "recheck_source_proxy_class_before_candidate_use"
        implementation_permission = "RECHECK_BEFORE_DEFAULT_OFF"
    return {
        **_base(row),
        "input_detail_execution_row_id": row.get("denominator_detail_execution_row_id"),
        "detail_execution_status": row.get("detail_execution_status"),
        "source_completeness_status": status,
        "source_completeness_decision": decision,
        "implementation_permission": implementation_permission,
        "proxy_contradiction_found": contradiction,
        "current_targetable_flagged_n": _to_int(row.get("current_targetable_flagged_n")),
        "current_source_flagged_n": _to_int(row.get("current_source_flagged_n")),
        "current_failclosed_flagged_n": _to_int(row.get("current_failclosed_flagged_n")),
        "best_expanded_targetable_count": _to_int(row.get("best_expanded_targetable_count")),
        "materialization_status": row.get("materialization_status"),
        "materialization_proxy_scope": row.get("materialization_proxy_scope"),
        "decision_proxy_r_style_result_class": proxy_class,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "decision_result": "KILL_OR_REPAIR_REQUIRED",
        "next_same_resource_action": decision,
    }


def horizon_decision(row: dict[str, Any]) -> dict[str, Any]:
    family = row.get("detail_execution_family")
    terminal = bool(row.get("terminal_decision"))
    status = row.get("detail_execution_status")
    if family == "HORIZON_REPAIR":
        horizon_status = "HORIZON_DETAIL_REPAIR_DEFAULT_OFF_RESCORER_CANDIDATE"
        decision = "build_default_off_horizon_repair_rescorer"
        permission = "DEFAULT_OFF_AFTER_REPAIR_SCORE"
    elif family == "HORIZON_REDESIGN":
        horizon_status = "HORIZON_DETAIL_REDESIGN_DEFAULT_OFF_TARGETABILITY_CANDIDATE"
        decision = "build_default_off_horizon_targetability_redesign"
        permission = "DEFAULT_OFF_AFTER_REDESIGN_SCORE"
    elif family == "HORIZON_KILL_CHECK":
        horizon_status = "HORIZON_DETAIL_KILL_CHECK_REPAIR_OPEN_DEFAULT_OFF_BLOCKED"
        decision = "repair_targetability_then_kill_if_negative_persists"
        permission = "BLOCK_DEFAULT_OFF_UNTIL_KILL_CHECK_REPAIR"
    elif terminal:
        horizon_status = "HORIZON_DETAIL_TERMINAL_KILL_PRESERVED"
        decision = "preserve_horizon_kill_as_targetability_failure_intelligence"
        permission = "DO_NOT_IMPLEMENT_TERMINAL_HORIZON_KILL"
    else:
        horizon_status = "HORIZON_DETAIL_RECHECK"
        decision = "recheck_horizon_detail_row"
        permission = "RECHECK_BEFORE_DEFAULT_OFF"
    return {
        **_base(row),
        "input_detail_execution_row_id": row.get("denominator_detail_execution_row_id")
        or row.get("denominator_terminal_detail_row_id"),
        "detail_execution_status": status,
        "horizon_detail_status": horizon_status,
        "horizon_detail_decision": decision,
        "default_off_permission": permission,
        "repaired_targetable_upper_bound_n": _to_int(row.get("repaired_targetable_upper_bound_n")),
        "repaired_targetable_upper_bound_reaches_n20": bool(row.get("repaired_targetable_upper_bound_reaches_n20")),
        "repair_upper_proxy_r_style_result_class": row.get("repair_upper_proxy_r_style_result_class"),
        "repair_upper_proxy_r_style_lower": row.get("repair_upper_proxy_r_style_lower"),
        "repair_upper_proxy_r_style_midpoint": row.get("repair_upper_proxy_r_style_midpoint"),
        "repair_upper_proxy_r_style_upper": row.get("repair_upper_proxy_r_style_upper"),
        "source_minus_horizon_proxy_delta": row.get("source_minus_horizon_proxy_delta"),
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "decision_result": "REPAIR_REDESIGN_OR_KILL",
        "terminal_decision": terminal,
        "next_same_resource_action": decision,
    }


def default_off_implementation_decision(row: dict[str, Any]) -> dict[str, Any]:
    family = row.get("detail_execution_family")
    status = row.get("detail_execution_status")
    if row.get("candidate_use_allowed_now") and family == "EXACT_CONTROL":
        impl_status = "DEFAULT_OFF_GUARDED_SCOPE_SCORER_CANDIDATE"
        impl_action = "register_default_off_guarded_scope_proxy_scorer"
        decision_result = "DEFAULT_OFF_SCORER_CANDIDATE"
    elif family == "EXACT_CONTROL":
        impl_status = "DEFAULT_OFF_BLOCKED_EXACT_CONTROL_BUILD_REQUIRED"
        impl_action = "withhold_until_exact_control_denominator_built"
        decision_result = "BUILD_REQUIRED"
    elif family == "SOURCE_CONTRADICTION" or family == "SOURCE_TERMINAL_KILL":
        impl_status = "DEFAULT_OFF_KILLED_SOURCE_PROXY_NEGATIVE_NO_CONTRADICTION"
        impl_action = "do_not_implement_preserve_source_avoid_intelligence"
        decision_result = "KILL_PRESERVED"
    elif family == "HORIZON_REPAIR":
        impl_status = "DEFAULT_OFF_HORIZON_REPAIR_RESCORER_CANDIDATE"
        impl_action = "register_default_off_horizon_repair_rescorer"
        decision_result = "REPAIR_CANDIDATE"
    elif family == "HORIZON_REDESIGN":
        impl_status = "DEFAULT_OFF_HORIZON_REDESIGN_CANDIDATE"
        impl_action = "register_default_off_horizon_targetability_redesign"
        decision_result = "REDESIGN_CANDIDATE"
    elif family == "HORIZON_KILL_CHECK":
        impl_status = "DEFAULT_OFF_HORIZON_KILL_CHECK_REPAIR_OPEN"
        impl_action = "withhold_until_horizon_kill_check_repaired"
        decision_result = "KILL_CHECK_OPEN"
    elif family == "HORIZON_TERMINAL_KILL":
        impl_status = "DEFAULT_OFF_TERMINAL_HORIZON_KILL_PRESERVED"
        impl_action = "do_not_implement_preserve_horizon_failure_intelligence"
        decision_result = "KILL_PRESERVED"
    else:
        impl_status = "DEFAULT_OFF_RECHECK_DETAIL_ROW"
        impl_action = "recheck_detail_execution_family"
        decision_result = "RECHECK"
    return {
        **_base(row),
        "input_detail_execution_row_id": row.get("denominator_detail_execution_row_id")
        or row.get("denominator_terminal_detail_row_id"),
        "detail_execution_family": family,
        "detail_execution_status": status,
        "default_off_implementation_status": impl_status,
        "default_off_implementation_action": impl_action,
        "decision_result": decision_result,
        "candidate_use_allowed_now": bool(row.get("candidate_use_allowed_now")),
        "unconditional_scalar_use_allowed": False,
        "terminal_decision": bool(row.get("terminal_decision")),
        "matched_guarded_scorer_registration_row_id": row.get("matched_guarded_scorer_registration_row_id"),
        "next_same_resource_action": impl_action,
    }


def scorer_behavior_decision(row: dict[str, Any]) -> dict[str, Any]:
    family = row.get("detail_execution_family")
    if row.get("candidate_use_allowed_now") and family == "EXACT_CONTROL":
        status = "SCORER_BEHAVIOR_GUARDED_SCOPE_PROXY_MATCH_ONLY"
        action = "emit_score_only_when_symbol_session_horizon_primitive_match"
    elif family == "HORIZON_REPAIR":
        status = "SCORER_BEHAVIOR_HORIZON_REPAIR_RESCORER_DEFAULT_OFF"
        action = "score_repaired_targetability_definition_default_off"
    elif family == "HORIZON_REDESIGN":
        status = "SCORER_BEHAVIOR_HORIZON_REDESIGN_DEFAULT_OFF"
        action = "score_redesigned_targetability_definition_default_off"
    elif family == "HORIZON_KILL_CHECK":
        status = "SCORER_BEHAVIOR_HORIZON_KILL_CHECK_REPAIR_GATE"
        action = "withhold_score_until_repair_then_kill_if_negative_persists"
    else:
        status = "SCORER_BEHAVIOR_RECHECK"
        action = "recheck_scorer_behavior_scope"
    return {
        **_base(row),
        "input_detail_execution_row_id": row.get("denominator_detail_execution_row_id"),
        "detail_execution_family": family,
        "scorer_behavior_status": status,
        "scorer_behavior_action": action,
        "default_off": True,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
