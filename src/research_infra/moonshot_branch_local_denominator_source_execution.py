"""Execution-result helpers for denominator/source rebuild rows."""

from __future__ import annotations

from typing import Any


DENOMINATOR_SOURCE_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_source_execution.py"
)
N20 = 20


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


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 6)


def proxy_interval(score: Any, uncertainty: float) -> dict[str, Any]:
    numeric = to_float(score)
    if numeric is None:
        return {
            "proxy_score": None,
            "proxy_r_style_midpoint": None,
            "proxy_r_style_lower": None,
            "proxy_r_style_upper": None,
            "proxy_r_style_result_class": "NO_PROXY_SCORE_AVAILABLE",
            "proxy_r_style_uncertainty": uncertainty,
        }
    midpoint = clamp(numeric - 0.35)
    lower = clamp(midpoint - uncertainty)
    upper = clamp(midpoint + uncertainty)
    if lower > 0:
        result_class = "PROXY_R_INTERVAL_ALL_POSITIVE"
    elif upper < 0:
        result_class = "PROXY_R_INTERVAL_ALL_NEGATIVE"
    else:
        result_class = "PROXY_R_INTERVAL_STRADDLES_ZERO"
    return {
        "proxy_score": round(numeric, 6),
        "proxy_r_style_midpoint": midpoint,
        "proxy_r_style_lower": lower,
        "proxy_r_style_upper": upper,
        "proxy_r_style_result_class": result_class,
        "proxy_r_style_uncertainty": uncertainty,
    }


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "denominator_source_execution_surface": DENOMINATOR_SOURCE_EXECUTION_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def exact_control_target_execution(row: dict[str, Any]) -> dict[str, Any]:
    exact_count = to_int(row.get("exact_control_count"))
    best_count = to_int(row.get("best_available_proxy_member_count"))
    uncertainty = 0.18 if best_count >= N20 else 0.30
    interval = proxy_interval(row.get("best_available_proxy_score_mean"), uncertainty)
    if exact_count >= N20:
        status = "DENOM_SOURCE_EXEC_EXACT_CONTROL_TARGET_CURRENT_N20_SCOREABLE"
        decision = "SCORE_EXACT_CONTROL_TARGET_DENOMINATOR"
        scalar_allowed = True
    elif best_count >= N20:
        status = "DENOM_SOURCE_EXEC_EXACT_CONTROL_TARGET_PROXY_N20_EXACT_BUILD_REQUIRED"
        decision = "USE_PROXY_CONTROL_GUARD_BUILD_EXACT_TARGET_DENOMINATOR"
        scalar_allowed = False
    else:
        status = "DENOM_SOURCE_EXEC_EXACT_CONTROL_TARGET_PROXY_UNDER_N20_BUILD_REQUIRED"
        decision = "DO_NOT_SCORE_TARGET_SCALAR_BUILD_EXACT_CONTROL_DENOMINATOR"
        scalar_allowed = False
    return {
        **_base(row),
        "denominator_source_execution_lane": "EXACT_CONTROL_TARGET_EXECUTION",
        "denominator_source_execution_status": status,
        "denominator_source_execution_decision": decision,
        "input_denominator_source_rebuild_row_id": row.get("denominator_source_rebuild_row_id"),
        "input_repair_execution_row_id": row.get("input_repair_execution_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "exact_control_count": exact_count,
        "best_available_proxy_relation": row.get("best_available_proxy_relation"),
        "best_available_proxy_member_count": best_count,
        "best_available_proxy_rows_needed_to_n20": max(0, N20 - best_count),
        "current_shadow_guard_row_count": to_int(row.get("current_shadow_guard_row_count")),
        "current_materialization_row_count": to_int(row.get("current_materialization_row_count")),
        "current_control_execution_row_count": to_int(row.get("current_control_execution_row_count")),
        "selected_control_member_count": to_int(row.get("selected_control_member_count")),
        "proxy_control_score": interval["proxy_score"],
        "proxy_r_style_midpoint": interval["proxy_r_style_midpoint"],
        "proxy_r_style_lower": interval["proxy_r_style_lower"],
        "proxy_r_style_upper": interval["proxy_r_style_upper"],
        "proxy_r_style_result_class": interval["proxy_r_style_result_class"],
        "proxy_r_style_uncertainty": interval["proxy_r_style_uncertainty"],
        "proxy_scalar_interpretation_allowed": scalar_allowed,
        "implementation_implication": (
            "exact_control_denominator_required_before_branch_scalar_use"
            if not scalar_allowed
            else "exact_control_target_scoreable"
        ),
    }


def exact_control_scope_execution(row: dict[str, Any]) -> dict[str, Any]:
    best_count = to_int(row.get("best_proxy_member_count"))
    exact_targets = to_int(row.get("exact_control_target_row_count"))
    uncertainty = 0.16 if best_count >= N20 else 0.28
    interval = proxy_interval(row.get("best_proxy_score_mean"), uncertainty)
    if to_int(row.get("current_materialization_row_count")) or to_int(row.get("current_control_execution_row_count")):
        status = "DENOM_SOURCE_EXEC_EXACT_CONTROL_SCOPE_CURRENT_ROWS_RECOUNT_REQUIRED"
        decision = "RECOUNT_CURRENT_EXACT_CONTROL_SCOPE_ROWS"
        scalar_allowed = False
    elif best_count >= N20:
        status = "DENOM_SOURCE_EXEC_EXACT_CONTROL_SCOPE_PROXY_N20_SCORE_WITH_GUARD"
        decision = "KEEP_PROXY_CONTROL_SCOPE_AND_BUILD_EXACT_DENOMINATOR"
        scalar_allowed = True
    else:
        status = "DENOM_SOURCE_EXEC_EXACT_CONTROL_SCOPE_PROXY_UNDER_N20_BUILD_REQUIRED"
        decision = "DO_NOT_SCORE_SCOPE_SCALAR_BUILD_EXACT_CONTROL_DENOMINATOR"
        scalar_allowed = False
    return {
        **_base(row),
        "denominator_source_execution_lane": "EXACT_CONTROL_SCOPE_EXECUTION",
        "denominator_source_execution_status": status,
        "denominator_source_execution_decision": decision,
        "input_exact_control_scope_denominator_row_id": row.get("exact_control_scope_denominator_row_id"),
        "input_scope_acquisition_plan_row_id": row.get("input_scope_acquisition_plan_row_id"),
        "exact_control_target_row_count": exact_targets,
        "best_proxy_member_count": best_count,
        "best_proxy_rows_needed_to_n20": max(0, N20 - best_count),
        "selected_control_member_count": to_int(row.get("selected_control_member_count")),
        "current_shadow_guard_row_count": to_int(row.get("current_shadow_guard_row_count")),
        "proxy_control_score": interval["proxy_score"],
        "proxy_r_style_midpoint": interval["proxy_r_style_midpoint"],
        "proxy_r_style_lower": interval["proxy_r_style_lower"],
        "proxy_r_style_upper": interval["proxy_r_style_upper"],
        "proxy_r_style_result_class": interval["proxy_r_style_result_class"],
        "proxy_r_style_uncertainty": interval["proxy_r_style_uncertainty"],
        "proxy_scalar_interpretation_allowed": scalar_allowed,
        "implementation_implication": (
            "control_scope_proxy_guard_available_but_exact_denominator_still_required"
            if scalar_allowed
            else "exact_control_scope_denominator_required"
        ),
    }


def source_rebuild_execution(row: dict[str, Any], materialization_row: dict[str, Any] | None = None) -> dict[str, Any]:
    materialization_row = materialization_row or {}
    result_class = row.get("materialization_proxy_r_style_result_class")
    if result_class == "PROXY_R_INTERVAL_ALL_POSITIVE":
        status = "DENOM_SOURCE_EXEC_EXACT_SOURCE_PROXY_POSITIVE_GUARDED"
        decision = "KEEP_GUARDED_SOURCE_PROXY_AND_REBUILD_EXACT_SOURCE"
        keep_kill_redesign = "KEEP_GUARDED_PROXY"
    elif result_class == "PROXY_R_INTERVAL_ALL_NEGATIVE":
        status = "DENOM_SOURCE_EXEC_EXACT_SOURCE_PROXY_NEGATIVE_KILL"
        decision = "KILL_PROXY_SOURCE_CANDIDATE_KEEP_EXACT_REBUILD_REQUIREMENT"
        keep_kill_redesign = "KILL_PROXY"
    else:
        status = "DENOM_SOURCE_EXEC_EXACT_SOURCE_PROXY_AMBIGUOUS_REDESIGN"
        decision = "REDESIGN_OR_REBUILD_EXACT_SOURCE_BEFORE_SCALAR_USE"
        keep_kill_redesign = "REDESIGN"
    return {
        **_base(row),
        "denominator_source_execution_lane": "EXACT_SOURCE_REBUILD_EXECUTION",
        "denominator_source_execution_status": status,
        "denominator_source_execution_decision": decision,
        "keep_kill_redesign_decision": keep_kill_redesign,
        "input_denominator_source_rebuild_row_id": row.get("denominator_source_rebuild_row_id"),
        "input_repair_execution_row_id": row.get("input_repair_execution_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "source_materialization_execution_id": row.get("source_materialization_execution_id"),
        "current_targetable_flagged_n": to_int(row.get("current_targetable_flagged_n")),
        "current_source_flagged_n": to_int(row.get("current_source_flagged_n")),
        "current_failclosed_flagged_n": to_int(row.get("current_failclosed_flagged_n")),
        "current_exact_gap_to_n20": to_int(row.get("current_exact_gap_to_n20")),
        "best_expanded_targetable_field": row.get("best_expanded_targetable_field"),
        "best_expanded_targetable_count": to_int(row.get("best_expanded_targetable_count")),
        "materialization_proxy_scope": row.get("materialization_proxy_scope"),
        "source_proxy_score": row.get("source_proxy_score"),
        "materialization_proxy_score": row.get("materialization_proxy_score"),
        "materialization_proxy_r_style_lower": materialization_row.get("materialization_proxy_r_style_lower"),
        "materialization_proxy_r_style_midpoint": materialization_row.get("materialization_proxy_r_style_midpoint"),
        "materialization_proxy_r_style_upper": materialization_row.get("materialization_proxy_r_style_upper"),
        "materialization_proxy_r_style_result_class": result_class,
        "proxy_scalar_interpretation_allowed": False,
        "exact_rebuild_required": True,
        "implementation_implication": (
            "do_not_register_source_proxy_candidate_unless_exact_rebuild_contradicts_negative_proxy"
            if keep_kill_redesign == "KILL_PROXY"
            else "source_proxy_requires_guarded_exact_rebuild"
        ),
    }


def horizon_rebuild_execution(row: dict[str, Any], materialization_row: dict[str, Any] | None = None) -> dict[str, Any]:
    materialization_row = materialization_row or {}
    fail_if_negative = bool(row.get("fail_if_negative_persists"))
    fail_ratio = to_float(row.get("current_failclosed_ratio")) or 0.0
    interval = proxy_interval(row.get("horizon_proxy_score"), 0.34 if fail_if_negative or fail_ratio >= 0.75 else 0.28)
    if fail_if_negative:
        status = "DENOM_SOURCE_EXEC_HORIZON_KILL_CHECK_REPAIR_REQUIRED"
        decision = "KILL_IF_REBUILT_HORIZON_PROXY_REMAINS_NEGATIVE"
        keep_kill_redesign = "KILL_CHECK"
    elif fail_ratio >= 0.75:
        status = "DENOM_SOURCE_EXEC_HORIZON_HIGH_FAILCLOSED_REDESIGN"
        decision = "REDESIGN_TARGETABLE_HORIZON_AND_RESCORE"
        keep_kill_redesign = "REDESIGN"
    else:
        status = "DENOM_SOURCE_EXEC_HORIZON_RESCORE_REPAIR_REQUIRED"
        decision = "REPAIR_TARGETABLE_HORIZON_AND_RESCORE"
        keep_kill_redesign = "REPAIR"
    return {
        **_base(row),
        "denominator_source_execution_lane": "HORIZON_REBUILD_EXECUTION",
        "denominator_source_execution_status": status,
        "denominator_source_execution_decision": decision,
        "keep_kill_redesign_decision": keep_kill_redesign,
        "input_denominator_source_rebuild_row_id": row.get("denominator_source_rebuild_row_id"),
        "input_repair_execution_row_id": row.get("input_repair_execution_row_id"),
        "input_horizon_rebuild_split_row_id": row.get("input_horizon_rebuild_split_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "source_materialization_execution_id": row.get("source_materialization_execution_id"),
        "current_targetable_flagged_n": to_int(row.get("current_targetable_flagged_n")),
        "current_targetable_gap_to_n20": to_int(row.get("current_targetable_gap_to_n20")),
        "current_source_flagged_n": to_int(row.get("current_source_flagged_n")),
        "current_failclosed_flagged_n": to_int(row.get("current_failclosed_flagged_n")),
        "current_failclosed_ratio": row.get("current_failclosed_ratio"),
        "source_proxy_score": row.get("source_proxy_score"),
        "horizon_proxy_score": row.get("horizon_proxy_score"),
        "source_minus_horizon_proxy_delta": row.get("source_minus_horizon_proxy_delta"),
        "horizon_proxy_r_style_midpoint": interval["proxy_r_style_midpoint"],
        "horizon_proxy_r_style_lower": interval["proxy_r_style_lower"],
        "horizon_proxy_r_style_upper": interval["proxy_r_style_upper"],
        "horizon_proxy_r_style_result_class": interval["proxy_r_style_result_class"],
        "fail_if_negative_persists": fail_if_negative,
        "materialization_proxy_r_style_result_class": materialization_row.get(
            "materialization_proxy_r_style_result_class"
        ),
        "proxy_scalar_interpretation_allowed": False,
        "exact_rebuild_required": True,
        "implementation_implication": "horizon_targetability_rebuild_required_before_candidate_use",
    }


def scope_action_execution(
    row: dict[str, Any],
    exact_scope_row: dict[str, Any] | None,
    source_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    exact_scope_row = exact_scope_row or {}
    child_rows = ([exact_scope_row] if exact_scope_row else []) + source_rows + horizon_rows
    if exact_scope_row:
        status = exact_scope_row.get("denominator_source_execution_status")
        decision = exact_scope_row.get("denominator_source_execution_decision")
        keep_kill_redesign = (
            "KEEP_GUARDED_PROXY" if exact_scope_row.get("proxy_scalar_interpretation_allowed") else "BUILD_REQUIRED"
        )
    elif horizon_rows:
        status = "DENOM_SOURCE_EXEC_SCOPE_HORIZON_ACTIONS_ACTIVE"
        decision = "EXECUTE_HORIZON_REPAIR_OR_KILL_CHECK_ROWS"
        keep_kill_redesign = "REPAIR_OR_KILL_CHECK"
    elif source_rows:
        killed = sum(1 for item in source_rows if item.get("keep_kill_redesign_decision") == "KILL_PROXY")
        status = "DENOM_SOURCE_EXEC_SCOPE_SOURCE_PROXY_KILL_OR_REBUILD"
        decision = "KILL_NEGATIVE_SOURCE_PROXY_ROWS_AND_KEEP_EXACT_REBUILD_REQUIREMENTS"
        keep_kill_redesign = "KILL_PROXY" if killed == len(source_rows) else "MIXED_SOURCE_REBUILD"
    else:
        status = "DENOM_SOURCE_EXEC_SCOPE_NO_EXECUTION_ROWS_FOUND"
        decision = "RECHECK_SCOPE_EXECUTION_INPUTS"
        keep_kill_redesign = "RECHECK"
    output = {
        **_base(row),
        "denominator_source_execution_lane": "SCOPE_ACTION_EXECUTION",
        "denominator_source_execution_status": status,
        "denominator_source_execution_decision": decision,
        "keep_kill_redesign_decision": keep_kill_redesign,
        "input_scope_rebuild_action_row_id": row.get("scope_rebuild_action_row_id"),
        "exact_control_scope_execution_count": 1 if exact_scope_row else 0,
        "source_rebuild_execution_count": len(source_rows),
        "horizon_rebuild_execution_count": len(horizon_rows),
        "proxy_scalar_interpretation_allowed": bool(
            exact_scope_row and exact_scope_row.get("proxy_scalar_interpretation_allowed")
        ),
        "exact_rebuild_required": bool(exact_scope_row or source_rows or horizon_rows),
    }
    if child_rows:
        output["outside_gbpjpy_xauusd_current_branch_box"] = all(
            bool(item.get("outside_gbpjpy_xauusd_current_branch_box")) for item in child_rows
        )
    return output
