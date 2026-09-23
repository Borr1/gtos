"""Action-candidate helpers for denominator/source execution decisions."""

from __future__ import annotations

from typing import Any


DENOMINATOR_SOURCE_ACTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_source_action_candidates.py"
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
        "denominator_source_action_surface": DENOMINATOR_SOURCE_ACTION_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "live_effect": False,
    }


def exact_control_target_action_candidate(row: dict[str, Any]) -> dict[str, Any]:
    rows_needed = to_int(row.get("best_available_proxy_rows_needed_to_n20"))
    exact_count = to_int(row.get("exact_control_count"))
    if exact_count >= 20:
        status = "DENOM_SOURCE_ACTION_EXACT_CONTROL_TARGET_SCOREABLE"
        decision = "REGISTER_EXACT_CONTROL_TARGET_SCORE"
        ready = True
    else:
        status = "DENOM_SOURCE_ACTION_EXACT_CONTROL_TARGET_BUILD_REQUIRED"
        decision = "BUILD_EXACT_CONTROL_TARGET_DENOMINATOR_BEFORE_SCALAR_USE"
        ready = False
    return {
        **_base(row),
        "denominator_source_action_lane": "EXACT_CONTROL_TARGET_ACTION",
        "denominator_source_action_status": status,
        "denominator_source_action_decision": decision,
        "input_denominator_source_execution_row_id": row.get("denominator_source_execution_row_id"),
        "input_denominator_source_rebuild_row_id": row.get("input_denominator_source_rebuild_row_id"),
        "implementation_candidate_family": "EXACT_CONTROL_TARGET_DENOMINATOR_BUILDER",
        "keep_kill_redesign_decision": "BUILD_REQUIRED" if not ready else "KEEP_EXACT_SCOREABLE",
        "registry_action": "withhold_target_scalar_until_exact_control_n20",
        "acquisition_requirement_family": "EXACT_CONTROL_TARGET_DENOMINATOR",
        "acquisition_requirement_status": "CONTROL_TARGET_EXACT_N20_REQUIRED",
        "rows_needed_to_n20": rows_needed,
        "proxy_scalar_interpretation_allowed": bool(row.get("proxy_scalar_interpretation_allowed")),
        "implementation_ready": ready,
        "exact_rebuild_required": not ready,
        "next_computation": "materialize_exact_control_target_denominator_from_current_source_or_proxy_rows",
    }


def exact_control_scope_action_candidate(row: dict[str, Any]) -> dict[str, Any]:
    scalar_allowed = bool(row.get("proxy_scalar_interpretation_allowed"))
    rows_needed = to_int(row.get("best_proxy_rows_needed_to_n20"))
    if scalar_allowed:
        status = "DENOM_SOURCE_ACTION_EXACT_CONTROL_SCOPE_PROXY_GUARD_REGISTER_AND_BUILD"
        decision = "REGISTER_GUARDED_PROXY_CONTROL_SCOPE_AND_BUILD_EXACT_DENOMINATOR"
        keep_kill_redesign = "KEEP_GUARDED_PROXY"
        ready = True
    else:
        status = "DENOM_SOURCE_ACTION_EXACT_CONTROL_SCOPE_BUILD_REQUIRED"
        decision = "BUILD_EXACT_CONTROL_SCOPE_DENOMINATOR_BEFORE_SCOPE_SCALAR_USE"
        keep_kill_redesign = "BUILD_REQUIRED"
        ready = False
    return {
        **_base(row),
        "denominator_source_action_lane": "EXACT_CONTROL_SCOPE_ACTION",
        "denominator_source_action_status": status,
        "denominator_source_action_decision": decision,
        "input_exact_control_scope_execution_row_id": row.get("exact_control_scope_execution_row_id"),
        "input_exact_control_scope_denominator_row_id": row.get("input_exact_control_scope_denominator_row_id"),
        "implementation_candidate_family": "EXACT_CONTROL_SCOPE_GUARD_OR_BUILDER",
        "keep_kill_redesign_decision": keep_kill_redesign,
        "registry_action": (
            "register_guarded_scope_proxy_with_exact_denominator_build_requirement"
            if scalar_allowed
            else "withhold_scope_scalar_until_exact_control_n20"
        ),
        "acquisition_requirement_family": "EXACT_CONTROL_SCOPE_DENOMINATOR",
        "acquisition_requirement_status": "CONTROL_SCOPE_EXACT_N20_REQUIRED",
        "rows_needed_to_n20": rows_needed,
        "best_proxy_member_count": to_int(row.get("best_proxy_member_count")),
        "proxy_scalar_interpretation_allowed": scalar_allowed,
        "implementation_ready": ready,
        "exact_rebuild_required": True,
        "next_computation": "materialize_exact_control_scope_denominator_and_recheck_proxy_guard",
    }


def source_proxy_kill_action_candidate(row: dict[str, Any]) -> dict[str, Any]:
    keep_kill = str(row.get("keep_kill_redesign_decision") or "")
    if keep_kill == "KILL_PROXY":
        status = "DENOM_SOURCE_ACTION_SOURCE_PROXY_KILL_EXACT_REBUILD_REQUIRED"
        decision = "REMOVE_SOURCE_PROXY_FROM_IMPLEMENTATION_QUEUE_KEEP_EXACT_REBUILD"
        registry_action = "do_not_register_source_proxy_candidate"
    elif keep_kill == "KEEP_GUARDED_PROXY":
        status = "DENOM_SOURCE_ACTION_SOURCE_PROXY_GUARDED_KEEP_EXACT_REBUILD"
        decision = "REGISTER_GUARDED_SOURCE_PROXY_AND_REBUILD_EXACT_SOURCE"
        registry_action = "register_guarded_source_proxy_candidate"
    else:
        status = "DENOM_SOURCE_ACTION_SOURCE_PROXY_REDESIGN_EXACT_REBUILD"
        decision = "REDESIGN_SOURCE_PROXY_AND_REBUILD_EXACT_SOURCE"
        registry_action = "withhold_source_proxy_candidate_pending_redesign"
    return {
        **_base(row),
        "denominator_source_action_lane": "SOURCE_PROXY_KILL_ACTION",
        "denominator_source_action_status": status,
        "denominator_source_action_decision": decision,
        "input_denominator_source_execution_row_id": row.get("denominator_source_execution_row_id"),
        "input_denominator_source_rebuild_row_id": row.get("input_denominator_source_rebuild_row_id"),
        "source_materialization_execution_id": row.get("source_materialization_execution_id"),
        "implementation_candidate_family": "SOURCE_PROXY_KILL_AND_EXACT_REBUILD",
        "keep_kill_redesign_decision": keep_kill,
        "registry_action": registry_action,
        "acquisition_requirement_family": "EXACT_SOURCE_REBUILD",
        "acquisition_requirement_status": "EXACT_SOURCE_ROWS_REQUIRED_TO_CHALLENGE_PROXY_KILL",
        "rows_needed_to_n20": to_int(row.get("current_exact_gap_to_n20")),
        "proxy_r_style_result_class": row.get("materialization_proxy_r_style_result_class"),
        "proxy_scalar_interpretation_allowed": False,
        "implementation_ready": keep_kill != "KILL_PROXY",
        "exact_rebuild_required": True,
        "next_computation": "rebuild_exact_source_denominator_or_preserve_proxy_kill_decision",
    }


def horizon_repair_action_candidate(row: dict[str, Any]) -> dict[str, Any]:
    keep_kill = str(row.get("keep_kill_redesign_decision") or "")
    if keep_kill == "KILL_CHECK":
        status = "DENOM_SOURCE_ACTION_HORIZON_KILL_CHECK_REPAIR"
        decision = "REPAIR_HORIZON_AND_KILL_IF_NEGATIVE_PERSISTS"
        family = "HORIZON_KILL_CHECK_REPAIR"
    elif keep_kill == "REDESIGN":
        status = "DENOM_SOURCE_ACTION_HORIZON_HIGH_FAILCLOSED_REDESIGN"
        decision = "REDESIGN_TARGETABLE_HORIZON_AND_RESCORE"
        family = "HORIZON_TARGETABILITY_REDESIGN"
    else:
        status = "DENOM_SOURCE_ACTION_HORIZON_REPAIR_RESCORE"
        decision = "REPAIR_TARGETABLE_HORIZON_AND_RESCORE"
        family = "HORIZON_TARGETABILITY_REPAIR"
    return {
        **_base(row),
        "denominator_source_action_lane": "HORIZON_REPAIR_ACTION",
        "denominator_source_action_status": status,
        "denominator_source_action_decision": decision,
        "input_denominator_source_execution_row_id": row.get("denominator_source_execution_row_id"),
        "input_denominator_source_rebuild_row_id": row.get("input_denominator_source_rebuild_row_id"),
        "input_horizon_rebuild_split_row_id": row.get("input_horizon_rebuild_split_row_id"),
        "source_materialization_execution_id": row.get("source_materialization_execution_id"),
        "implementation_candidate_family": family,
        "keep_kill_redesign_decision": keep_kill,
        "registry_action": "withhold_horizon_candidate_until_repair_rescore",
        "acquisition_requirement_family": "HORIZON_TARGETABILITY_REBUILD",
        "acquisition_requirement_status": status.replace("DENOM_SOURCE_ACTION_", ""),
        "rows_needed_to_n20": to_int(row.get("current_targetable_gap_to_n20")),
        "proxy_r_style_result_class": row.get("horizon_proxy_r_style_result_class"),
        "fail_if_negative_persists": bool(row.get("fail_if_negative_persists")),
        "proxy_scalar_interpretation_allowed": False,
        "implementation_ready": False,
        "exact_rebuild_required": True,
        "next_computation": "repair_horizon_targetability_and_rescore_or_kill_check",
    }


def scope_rollup_action_candidate(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("denominator_source_execution_status") or "")
    if "SOURCE_PROXY_KILL" in status:
        action_status = "DENOM_SOURCE_ACTION_SCOPE_SOURCE_PROXY_KILL_OR_REBUILD"
        decision = "APPLY_SOURCE_PROXY_KILL_AND_KEEP_EXACT_REBUILD_SCOPE"
    elif "HORIZON_ACTIONS_ACTIVE" in status:
        action_status = "DENOM_SOURCE_ACTION_SCOPE_HORIZON_REPAIR_ACTIVE"
        decision = "APPLY_HORIZON_REPAIR_REDESIGN_OR_KILL_CHECK_SCOPE"
    elif "PROXY_N20_SCORE_WITH_GUARD" in status:
        action_status = "DENOM_SOURCE_ACTION_SCOPE_CONTROL_PROXY_GUARD_ACTIVE"
        decision = "REGISTER_CONTROL_PROXY_GUARD_AND_BUILD_EXACT_SCOPE"
    elif "UNDER_N20_BUILD_REQUIRED" in status:
        action_status = "DENOM_SOURCE_ACTION_SCOPE_EXACT_CONTROL_BUILD_REQUIRED"
        decision = "BUILD_EXACT_CONTROL_SCOPE_DENOMINATOR"
    else:
        action_status = "DENOM_SOURCE_ACTION_SCOPE_RECHECK_REQUIRED"
        decision = "RECHECK_SCOPE_ROLLUP_INPUTS"
    return {
        **_base(row),
        "denominator_source_action_lane": "SCOPE_ROLLUP_ACTION",
        "denominator_source_action_status": action_status,
        "denominator_source_action_decision": decision,
        "input_scope_action_execution_row_id": row.get("scope_action_execution_row_id"),
        "input_scope_rebuild_action_row_id": row.get("input_scope_rebuild_action_row_id"),
        "implementation_candidate_family": "SCOPE_ROLLUP_ACTION",
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "exact_control_scope_execution_count": to_int(row.get("exact_control_scope_execution_count")),
        "source_rebuild_execution_count": to_int(row.get("source_rebuild_execution_count")),
        "horizon_rebuild_execution_count": to_int(row.get("horizon_rebuild_execution_count")),
        "proxy_scalar_interpretation_allowed": bool(row.get("proxy_scalar_interpretation_allowed")),
        "exact_rebuild_required": bool(row.get("exact_rebuild_required")),
        "implementation_ready": bool(row.get("proxy_scalar_interpretation_allowed")),
        "next_computation": "execute_scope_rollup_children_without_denominator_inflation",
    }


def acquisition_requirement_from_action(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_base(row),
        "acquisition_requirement_family": row.get("acquisition_requirement_family"),
        "acquisition_requirement_status": row.get("acquisition_requirement_status"),
        "input_action_candidate_row_id": row.get("denominator_source_action_candidate_row_id"),
        "input_denominator_source_execution_row_id": row.get("input_denominator_source_execution_row_id"),
        "rows_needed_to_n20": to_int(row.get("rows_needed_to_n20")),
        "exact_rebuild_required": bool(row.get("exact_rebuild_required")),
        "proxy_scalar_interpretation_allowed": bool(row.get("proxy_scalar_interpretation_allowed")),
        "next_computation": row.get("next_computation"),
    }
