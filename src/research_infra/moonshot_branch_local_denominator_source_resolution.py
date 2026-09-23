"""Resolution helpers for denominator/source acquisition-execution rows."""

from __future__ import annotations

from statistics import mean
from typing import Any


DENOMINATOR_SOURCE_RESOLUTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_source_resolution.py"
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
        "denominator_source_resolution_surface": DENOMINATOR_SOURCE_RESOLUTION_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def _interval_from_fields(
    row: dict[str, Any],
    *,
    score: str,
    lower: str,
    midpoint: str,
    upper: str,
    result_class: str,
) -> dict[str, Any]:
    return {
        "decision_proxy_score": to_float(row.get(score)),
        "decision_proxy_r_style_lower": to_float(row.get(lower)),
        "decision_proxy_r_style_midpoint": to_float(row.get(midpoint)),
        "decision_proxy_r_style_upper": to_float(row.get(upper)),
        "decision_proxy_r_style_result_class": row.get(result_class),
    }


def exact_control_target_resolution(row: dict[str, Any]) -> dict[str, Any]:
    interval = _interval_from_fields(
        row,
        score="best_proxy_score",
        lower="best_proxy_r_style_lower",
        midpoint="best_proxy_r_style_midpoint",
        upper="best_proxy_r_style_upper",
        result_class="best_proxy_r_style_result_class",
    )
    if row.get("denominator_source_acquisition_status") == "DENOM_SOURCE_ACQ_EXEC_EXACT_CONTROL_TARGET_BUILT_N20":
        status = "DENOM_SOURCE_RESOLUTION_EXACT_CONTROL_TARGET_SCOREABLE"
        action = "use_exact_control_target_score"
        implementation_state = "EXACT_CONTROL_TARGET_SCOREABLE"
        terminal = False
    else:
        status = "DENOM_SOURCE_RESOLUTION_EXACT_CONTROL_TARGET_BUILD_REQUIRED"
        action = "build_exact_control_target_denominator_before_scalar_use"
        implementation_state = "BLOCKED_EXACT_CONTROL_TARGET_BUILD"
        terminal = False
    return {
        **_base(row),
        "denominator_source_resolution_lane": "EXACT_CONTROL_TARGET_RESOLUTION",
        "denominator_source_resolution_status": status,
        "resolution_action": action,
        "input_acquisition_execution_row_id": row.get("denominator_source_acquisition_execution_row_id"),
        "input_action_candidate_row_id": row.get("input_action_candidate_row_id"),
        "input_denominator_source_execution_row_id": row.get("input_denominator_source_execution_row_id"),
        "member_rows_examined": to_int(row.get("member_rows_examined")),
        "exact_control_member_count": to_int(row.get("exact_control_member_count")),
        "best_available_proxy_relation": row.get("best_available_proxy_relation"),
        "best_available_proxy_member_count": to_int(row.get("best_available_proxy_member_count")),
        "best_proxy_rows_needed_to_n20": to_int(row.get("best_proxy_rows_needed_to_n20")),
        **interval,
        "proxy_scalar_interpretation_allowed": bool(row.get("proxy_scalar_interpretation_allowed")),
        "terminal_decision": terminal,
        "candidate_implementation_state": implementation_state,
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "implementation_implication": row.get("implementation_implication"),
        "next_same_resource_action": "exact_control_target_denominator_build",
    }


def exact_control_scope_resolution(
    row: dict[str, Any],
    target_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    proxy_scores = [
        to_float(target.get("decision_proxy_score", target.get("best_proxy_score")))
        for target in target_rows
        if to_float(target.get("decision_proxy_score", target.get("best_proxy_score"))) is not None
    ]
    scope_proxy_mean = round(mean(proxy_scores), 6) if proxy_scores else None
    if row.get("denominator_source_acquisition_status") == "DENOM_SOURCE_ACQ_EXEC_CONTROL_SCOPE_GUARDED_PROXY_CONFIRMED_BUILD_OPEN":
        status = "DENOM_SOURCE_RESOLUTION_EXACT_CONTROL_SCOPE_GUARDED_IMPLEMENTATION_CANDIDATE"
        action = "register_guarded_scope_proxy_and_continue_exact_build"
        implementation_state = "GUARDED_PROXY_IMPLEMENTATION_CANDIDATE"
    else:
        status = "DENOM_SOURCE_RESOLUTION_EXACT_CONTROL_SCOPE_BUILD_REQUIRED"
        action = "build_exact_control_scope_denominator_before_scalar_use"
        implementation_state = "BLOCKED_EXACT_CONTROL_SCOPE_BUILD"
    return {
        **_base(row),
        "denominator_source_resolution_lane": "EXACT_CONTROL_SCOPE_RESOLUTION",
        "denominator_source_resolution_status": status,
        "resolution_action": action,
        "input_exact_control_scope_acquisition_execution_row_id": row.get(
            "exact_control_scope_acquisition_execution_row_id"
        ),
        "input_exact_control_scope_action_row_id": row.get("input_exact_control_scope_action_row_id"),
        "target_action_rows": to_int(row.get("target_action_rows")),
        "target_exact_built_rows": to_int(row.get("target_exact_built_rows")),
        "target_proxy_n20_rows": to_int(row.get("target_proxy_n20_rows")),
        "target_underpowered_rows": to_int(row.get("target_underpowered_rows")),
        "target_resolution_rows_joined": len(target_rows),
        "scope_target_proxy_score_mean": scope_proxy_mean,
        "proxy_scalar_interpretation_allowed": bool(row.get("proxy_scalar_interpretation_allowed")),
        "terminal_decision": False,
        "candidate_implementation_state": implementation_state,
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "implementation_implication": row.get("implementation_implication"),
        "next_same_resource_action": "exact_control_scope_denominator_build",
    }


def source_resolution(row: dict[str, Any]) -> dict[str, Any]:
    interval = _interval_from_fields(
        row,
        score="materialization_proxy_score",
        lower="materialization_proxy_r_style_lower",
        midpoint="materialization_proxy_r_style_midpoint",
        upper="materialization_proxy_r_style_upper",
        result_class="materialization_proxy_r_style_result_class",
    )
    if row.get("denominator_source_acquisition_status") == (
        "DENOM_SOURCE_ACQ_EXEC_SOURCE_EXACT_UNDER_N20_NEGATIVE_PROXY_KILL_CONFIRMED"
    ):
        status = "DENOM_SOURCE_RESOLUTION_SOURCE_KILL_CONFIRMED_EXACT_REBUILD_CONTRADICTION_ONLY"
        action = "suppress_source_proxy_candidate_and_keep_exact_rebuild_as_contradiction_route"
        implementation_state = "SOURCE_PROXY_KILLED"
        terminal = True
        next_action = "exact_source_rebuild_contradiction_check_only"
    else:
        status = "DENOM_SOURCE_RESOLUTION_SOURCE_RECHECK_REQUIRED"
        action = "continue_exact_source_rebuild_before_implementation"
        implementation_state = "SOURCE_EXACT_RECHECK_REQUIRED"
        terminal = False
        next_action = "exact_source_rebuild"
    return {
        **_base(row),
        "denominator_source_resolution_lane": "SOURCE_RESOLUTION",
        "denominator_source_resolution_status": status,
        "resolution_action": action,
        "input_acquisition_execution_row_id": row.get("denominator_source_acquisition_execution_row_id"),
        "input_action_candidate_row_id": row.get("input_action_candidate_row_id"),
        "input_denominator_source_execution_row_id": row.get("input_denominator_source_execution_row_id"),
        "current_targetable_flagged_n": to_int(row.get("current_targetable_flagged_n")),
        "current_source_flagged_n": to_int(row.get("current_source_flagged_n")),
        "current_failclosed_flagged_n": to_int(row.get("current_failclosed_flagged_n")),
        "current_exact_gap_to_n20": to_int(row.get("current_exact_gap_to_n20")),
        "best_expanded_targetable_count": to_int(row.get("best_expanded_targetable_count")),
        "materialization_proxy_scope": row.get("materialization_proxy_scope"),
        **interval,
        "proxy_contradiction_found": bool(row.get("proxy_contradiction_found")),
        "proxy_scalar_interpretation_allowed": bool(row.get("proxy_scalar_interpretation_allowed")),
        "terminal_decision": terminal,
        "candidate_implementation_state": implementation_state,
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "implementation_implication": row.get("implementation_implication"),
        "next_same_resource_action": next_action,
    }


def horizon_resolution(row: dict[str, Any]) -> dict[str, Any]:
    interval = _interval_from_fields(
        row,
        score="source_proxy_score",
        lower="repair_upper_proxy_r_style_lower",
        midpoint="repair_upper_proxy_r_style_midpoint",
        upper="repair_upper_proxy_r_style_upper",
        result_class="repair_upper_proxy_r_style_result_class",
    )
    decision = row.get("keep_kill_redesign_decision")
    if decision == "KILL":
        status = "DENOM_SOURCE_RESOLUTION_HORIZON_KILL_CONFIRMED"
        action = "suppress_horizon_candidate_after_negative_repair_upper_bound"
        implementation_state = "HORIZON_KILLED"
        terminal = True
        next_action = "preserve_kill_evidence_no_candidate_use"
    elif decision == "KILL_CHECK":
        status = "DENOM_SOURCE_RESOLUTION_HORIZON_KILL_CHECK_REPAIR_FIRST"
        action = "repair_horizon_targetability_then_kill_only_if_negative_persists"
        implementation_state = "HORIZON_KILL_CHECK_REPAIR_REQUIRED"
        terminal = False
        next_action = "horizon_targetability_repair_and_kill_check"
    elif decision == "REDESIGN":
        status = "DENOM_SOURCE_RESOLUTION_HORIZON_REDESIGN_REQUIRED"
        action = "redesign_horizon_targetability_and_rescore"
        implementation_state = "HORIZON_REDESIGN_REQUIRED"
        terminal = False
        next_action = "horizon_targetability_redesign"
    else:
        status = "DENOM_SOURCE_RESOLUTION_HORIZON_REPAIR_RESCORABLE"
        action = "repair_horizon_targetability_and_rescore"
        implementation_state = "HORIZON_REPAIR_REQUIRED"
        terminal = False
        next_action = "horizon_targetability_repair_rescore"
    return {
        **_base(row),
        "denominator_source_resolution_lane": "HORIZON_RESOLUTION",
        "denominator_source_resolution_status": status,
        "resolution_action": action,
        "input_acquisition_execution_row_id": row.get("denominator_source_acquisition_execution_row_id"),
        "input_action_candidate_row_id": row.get("input_action_candidate_row_id"),
        "input_denominator_source_execution_row_id": row.get("input_denominator_source_execution_row_id"),
        "current_targetable_flagged_n": to_int(row.get("current_targetable_flagged_n")),
        "current_failclosed_flagged_n": to_int(row.get("current_failclosed_flagged_n")),
        "current_source_flagged_n": to_int(row.get("current_source_flagged_n")),
        "repaired_targetable_upper_bound_n": to_int(row.get("repaired_targetable_upper_bound_n")),
        "repaired_targetable_upper_bound_reaches_n20": bool(row.get("repaired_targetable_upper_bound_reaches_n20")),
        "current_targetable_gap_to_n20": to_int(row.get("current_targetable_gap_to_n20")),
        "horizon_proxy_score": to_float(row.get("horizon_proxy_score")),
        "source_minus_horizon_proxy_delta": to_float(row.get("source_minus_horizon_proxy_delta")),
        "current_horizon_proxy_r_style_result_class": row.get("current_horizon_proxy_r_style_result_class"),
        **interval,
        "fail_if_negative_persists": bool(row.get("fail_if_negative_persists")),
        "proxy_scalar_interpretation_allowed": bool(row.get("proxy_scalar_interpretation_allowed")),
        "terminal_decision": terminal,
        "candidate_implementation_state": implementation_state,
        "keep_kill_redesign_decision": decision,
        "implementation_implication": row.get("implementation_implication"),
        "next_same_resource_action": next_action,
    }


def implementation_resolution(row: dict[str, Any]) -> dict[str, Any]:
    state = row.get("candidate_implementation_state")
    if state == "GUARDED_PROXY_IMPLEMENTATION_CANDIDATE":
        disposition = "IMPLEMENT_GUARDED_SCOPE_PROXY_CANDIDATE"
        use_candidate = True
    elif state in {"SOURCE_PROXY_KILLED", "HORIZON_KILLED"}:
        disposition = "DO_NOT_IMPLEMENT_KILLED_CANDIDATE"
        use_candidate = False
    elif str(state or "").startswith("HORIZON_"):
        disposition = "REPAIR_OR_REDESIGN_BEFORE_IMPLEMENTATION"
        use_candidate = False
    else:
        disposition = "BUILD_DENOMINATOR_BEFORE_IMPLEMENTATION"
        use_candidate = False
    return {
        **_base(row),
        "implementation_resolution_status": disposition,
        "candidate_implementation_state": state,
        "candidate_use_allowed_now": use_candidate,
        "terminal_decision": bool(row.get("terminal_decision")),
        "input_resolution_row_id": row.get("denominator_source_resolution_row_id"),
        "source_resolution_lane": row.get("denominator_source_resolution_lane"),
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "next_same_resource_action": row.get("next_same_resource_action"),
        "resolution_action": row.get("resolution_action"),
        "implementation_implication": row.get("implementation_implication"),
        "live_effect": False,
    }


def acquisition_requirement_resolution(
    row: dict[str, Any],
    resolved_row: dict[str, Any] | None,
) -> dict[str, Any]:
    resolved_row = resolved_row or {}
    return {
        **_base(row),
        "denominator_source_resolution_lane": "ACQUISITION_REQUIREMENT_RESOLUTION",
        "denominator_source_resolution_status": resolved_row.get(
            "denominator_source_resolution_status",
            "DENOM_SOURCE_RESOLUTION_REQUIREMENT_RECHECK_JOIN",
        ),
        "resolution_action": resolved_row.get("resolution_action", "recheck_acquisition_requirement_resolution_join"),
        "input_acquisition_requirement_execution_row_id": row.get("acquisition_requirement_execution_row_id"),
        "input_acquisition_requirement_row_id": row.get("input_acquisition_requirement_row_id"),
        "input_action_candidate_row_id": row.get("input_action_candidate_row_id"),
        "matched_resolution_row_id": resolved_row.get("denominator_source_resolution_row_id"),
        "acquisition_requirement_family": row.get("acquisition_requirement_family"),
        "acquisition_requirement_status": row.get("acquisition_requirement_status"),
        "rows_needed_to_n20": to_int(row.get("rows_needed_to_n20")),
        "candidate_implementation_state": resolved_row.get("candidate_implementation_state"),
        "proxy_scalar_interpretation_allowed": bool(resolved_row.get("proxy_scalar_interpretation_allowed")),
        "terminal_decision": bool(resolved_row.get("terminal_decision")),
        "keep_kill_redesign_decision": resolved_row.get("keep_kill_redesign_decision"),
        "next_same_resource_action": resolved_row.get("next_same_resource_action"),
        "implementation_implication": resolved_row.get("implementation_implication"),
    }


def next_compute_action(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("candidate_implementation_state") == "HORIZON_KILLED":
        return None
    return {
        **_base(row),
        "next_compute_action_status": "DENOM_SOURCE_RESOLUTION_NEXT_COMPUTE_ACTION_OPEN",
        "input_resolution_row_id": row.get("denominator_source_resolution_row_id"),
        "source_resolution_lane": row.get("denominator_source_resolution_lane"),
        "candidate_implementation_state": row.get("candidate_implementation_state"),
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "next_same_resource_action": row.get("next_same_resource_action"),
        "resolution_action": row.get("resolution_action"),
        "terminal_decision": bool(row.get("terminal_decision")),
        "live_effect": False,
    }
