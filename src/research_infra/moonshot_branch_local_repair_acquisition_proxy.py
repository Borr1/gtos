"""Acquisition/proxy replay helpers for branch-local repair execution rows."""

from __future__ import annotations

from typing import Any


ACQUISITION_PROXY_SURFACE = "src/research_infra/moonshot_branch_local_repair_acquisition_proxy.py"
N20 = 20


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def rows_needed_to_n20(value: Any) -> int:
    return max(0, N20 - to_int(value))


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "acquisition_proxy_surface": ACQUISITION_PROXY_SURFACE,
        "input_repair_execution_row_id": row.get("repair_execution_row_id"),
        "input_repair_execution_status": row.get("repair_execution_status"),
        "input_repair_execution_decision": row.get("repair_execution_decision"),
        "input_module_materialization_row_id": row.get("input_module_materialization_row_id"),
        "input_code_integration_candidate_row_id": row.get("input_code_integration_candidate_row_id"),
        "input_runtime_work_row_id": row.get("input_runtime_work_row_id"),
        "input_implementation_candidate_row_id": row.get("input_implementation_candidate_row_id"),
        "input_execution_bundle_row_id": row.get("input_execution_bundle_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "observable_scope_key": row.get("observable_scope_key"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "scope_symbol": row.get("scope_symbol"),
        "scope_session": row.get("scope_session"),
        "scope_horizon": row.get("scope_horizon"),
        "scope_primitive": row.get("scope_primitive"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def score_band(score: Any) -> str:
    numeric = to_float(score)
    if numeric is None:
        return "SCORE_MISSING"
    if numeric >= 0.5:
        return "SCORE_HIGH"
    if numeric >= 0.25:
        return "SCORE_MID"
    if numeric > 0:
        return "SCORE_LOW"
    return "SCORE_ZERO_OR_NEGATIVE"


def control_relation(target_row: dict[str, Any], control_row: dict[str, Any]) -> str:
    symbol_match = target_row.get("scope_symbol") == control_row.get("scope_symbol")
    session_match = target_row.get("scope_session") == control_row.get("scope_session")
    horizon_match = target_row.get("scope_horizon") == control_row.get("scope_horizon")
    primitive_match = target_row.get("scope_primitive") == control_row.get("scope_primitive")
    if symbol_match and session_match and horizon_match and primitive_match:
        return "CONTROL_MEMBER_RELATION_EXACT_SCOPE"
    if symbol_match and session_match and horizon_match:
        return "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION_HORIZON"
    if symbol_match and session_match:
        return "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION"
    if symbol_match:
        return "CONTROL_MEMBER_RELATION_SAME_SYMBOL"
    return "CONTROL_MEMBER_RELATION_GLOBAL_CROSS_SYMBOL"


def exact_control_acquisition_requirement(row: dict[str, Any]) -> dict[str, Any]:
    exact_count = to_int(row.get("exact_control_count"))
    same_symbol_session_count = to_int(row.get("same_symbol_session_control_count"))
    same_symbol_count = to_int(row.get("same_symbol_control_count"))
    selected_count = to_int(row.get("selected_control_count"))
    if exact_count >= N20:
        status = "ACQUISITION_EXACT_CONTROL_ALREADY_N20"
        decision = "USE_EXACT_CONTROL_ROWS"
        requirement_open = False
    elif same_symbol_session_count >= N20:
        status = "ACQUISITION_EXACT_CONTROL_NEEDS_EXACT_SCOPE_HAS_SESSION_PROXY"
        decision = "BUILD_EXACT_SCOPE_KEEP_SESSION_PROXY_CONTEXT"
        requirement_open = True
    elif same_symbol_count >= N20:
        status = "ACQUISITION_EXACT_CONTROL_NEEDS_EXACT_SCOPE_HAS_SYMBOL_PROXY"
        decision = "BUILD_EXACT_SCOPE_KEEP_SYMBOL_PROXY_CONTEXT"
        requirement_open = True
    elif selected_count >= N20:
        status = "ACQUISITION_EXACT_CONTROL_NEEDS_EXACT_SCOPE_GLOBAL_PROXY_ONLY"
        decision = "BUILD_EXACT_OR_SYMBOL_SESSION_CONTROL_SCOPE_KEEP_GLOBAL_MEMBER_REPLAY"
        requirement_open = True
    else:
        status = "ACQUISITION_EXACT_CONTROL_NEEDS_CONTROL_DENOMINATOR"
        decision = "BUILD_CONTROL_DENOMINATOR_FROM_CURRENT_OR_RECONSTRUCTED_ROWS"
        requirement_open = True
    return {
        **_base(row),
        "acquisition_proxy_lane": "EXACT_CONTROL_ACQUISITION_REQUIREMENT",
        "acquisition_proxy_status": status,
        "acquisition_proxy_decision": decision,
        "exact_control_count": exact_count,
        "same_symbol_session_control_count": same_symbol_session_count,
        "same_symbol_control_count": same_symbol_count,
        "selected_control_count": selected_count,
        "exact_control_rows_needed_to_n20": rows_needed_to_n20(exact_count),
        "same_symbol_session_rows_needed_to_n20": rows_needed_to_n20(same_symbol_session_count),
        "same_symbol_rows_needed_to_n20": rows_needed_to_n20(same_symbol_count),
        "global_selected_rows_available": selected_count,
        "control_proxy_score_lower_bound": row.get("control_proxy_score_lower_bound"),
        "acquisition_requirement_open": requirement_open,
        "next_same_resource_action": "materialize exact same-scope controls or stronger same-symbol/session proxy controls",
    }


def control_member_proxy_replay(
    target_row: dict[str, Any],
    control_row: dict[str, Any] | None,
    member_runtime_work_row_id: str | None,
    member_input_candidate_id: str | None,
    member_index: int,
) -> dict[str, Any]:
    control_row = control_row or {}
    relation = control_relation(target_row, control_row) if control_row else "CONTROL_MEMBER_RELATION_UNRESOLVED_MEMBER_ID"
    member_score = control_row.get("control_proxy_score")
    return {
        **_base(target_row),
        "acquisition_proxy_lane": "CONTROL_MEMBER_PROXY_REPLAY",
        "acquisition_proxy_status": f"ACQUISITION_{relation}",
        "acquisition_proxy_decision": "PRESERVE_SELECTED_CONTROL_MEMBER_FOR_STRONGER_PROXY_REPLAY",
        "member_index": member_index,
        "member_runtime_work_row_id": member_runtime_work_row_id,
        "member_input_candidate_id": member_input_candidate_id,
        "member_execution_bundle_row_id": control_row.get("execution_bundle_row_id"),
        "member_observable_scope_key": control_row.get("observable_scope_key"),
        "member_symbol": control_row.get("symbol"),
        "member_route_session": control_row.get("route_session"),
        "member_horizon_id": control_row.get("horizon_id"),
        "member_primitive_flag": control_row.get("primitive_flag"),
        "member_scope_symbol": control_row.get("scope_symbol"),
        "member_scope_session": control_row.get("scope_session"),
        "member_scope_horizon": control_row.get("scope_horizon"),
        "member_scope_primitive": control_row.get("scope_primitive"),
        "control_member_relation": relation,
        "control_proxy_score": member_score,
        "control_proxy_score_band": control_row.get("control_proxy_score_band") or score_band(member_score),
        "member_lookup_status": "CONTROL_MEMBER_JOINED" if control_row else "CONTROL_MEMBER_ID_NOT_FOUND",
    }


def source_acquisition_proxy_requirement(row: dict[str, Any]) -> dict[str, Any]:
    family = str(row.get("source_repair_family") or "")
    source_score = row.get("source_proxy_score")
    horizon_score = row.get("horizon_proxy_score")
    targetable_n = to_int(row.get("current_targetable_flagged_n"))
    source_n = to_int(row.get("current_source_flagged_n"))
    if family == "EXACT_SOURCE_REPAIR":
        status = "ACQUISITION_EXACT_SOURCE_REQUIRED_PROXY_SCORE_PRESERVED"
        decision = "ACQUIRE_OR_REBUILD_EXACT_SOURCE_ROWS_BEFORE_SCALAR_USE"
        rows_needed = None
    elif family == "HORIZON_REBUILD_KILL_CHECK":
        status = "ACQUISITION_HORIZON_REBUILD_KILL_CHECK_REQUIRED"
        decision = "REBUILD_HORIZON_TARGETABLE_ROWS_AND_KILL_IF_NEGATIVE_PERSISTS"
        rows_needed = rows_needed_to_n20(targetable_n)
    elif family == "HORIZON_REBUILD_RESCORE":
        status = "ACQUISITION_HORIZON_REBUILD_RESCORE_REQUIRED"
        decision = "REBUILD_HORIZON_TARGETABLE_ROWS_AND_RESCORE"
        rows_needed = rows_needed_to_n20(targetable_n)
    else:
        status = "ACQUISITION_SOURCE_CONTEXT_ONLY"
        decision = "PRESERVE_SOURCE_CONTEXT"
        rows_needed = None
    priority = to_float(source_score) or 0.0
    failclosed_ratio = to_float(row.get("current_failclosed_ratio")) or 0.0
    if family.startswith("HORIZON"):
        priority = round(priority + failclosed_ratio, 6)
    return {
        **_base(row),
        "acquisition_proxy_lane": "SOURCE_ACQUISITION_PROXY_REQUIREMENT",
        "acquisition_proxy_status": status,
        "acquisition_proxy_decision": decision,
        "source_repair_family": family,
        "source_proxy_score": source_score,
        "source_proxy_score_band": score_band(source_score),
        "horizon_proxy_score": horizon_score,
        "source_minus_horizon_proxy_delta": row.get("source_minus_horizon_proxy_delta"),
        "current_source_flagged_n": source_n if source_n else None,
        "current_targetable_flagged_n": targetable_n if source_n else None,
        "current_failclosed_flagged_n": row.get("current_failclosed_flagged_n"),
        "current_targetable_ratio": row.get("current_targetable_ratio"),
        "current_failclosed_ratio": row.get("current_failclosed_ratio"),
        "targetable_rows_needed_to_n20": rows_needed,
        "fail_if_negative_persists": row.get("fail_if_negative_persists"),
        "acquisition_priority_score": priority,
        "acquisition_requirement_open": bool(row.get("source_repair_requirement_open")),
        "next_same_resource_action": decision.lower(),
    }


def horizon_proxy_stress(row: dict[str, Any]) -> dict[str, Any]:
    source_score = to_float(row.get("source_proxy_score"))
    horizon_score = to_float(row.get("horizon_proxy_score"))
    delta = row.get("source_minus_horizon_proxy_delta")
    failclosed_ratio = to_float(row.get("current_failclosed_ratio"))
    if row.get("fail_if_negative_persists"):
        status = "HORIZON_PROXY_STRESS_KILL_CHECK_ACTIVE"
        decision = "REBUILD_HORIZON_AND_KILL_IF_REBUILT_PROXY_REMAINS_WEAK"
    else:
        status = "HORIZON_PROXY_STRESS_RESCORE_ACTIVE"
        decision = "REBUILD_HORIZON_AND_RESCORE_WITH_FAILCLOSED_STRESS"
    stress_score = None
    if source_score is not None and failclosed_ratio is not None:
        stress_score = round(source_score * (1.0 - min(max(failclosed_ratio, 0.0), 1.0)), 6)
    return {
        **_base(row),
        "acquisition_proxy_lane": "HORIZON_PROXY_STRESS",
        "acquisition_proxy_status": status,
        "acquisition_proxy_decision": decision,
        "source_proxy_score": source_score,
        "horizon_proxy_score": horizon_score,
        "source_minus_horizon_proxy_delta": delta,
        "current_failclosed_ratio": row.get("current_failclosed_ratio"),
        "failclosed_stress_score": stress_score,
        "fail_if_negative_persists": row.get("fail_if_negative_persists"),
        "targetable_rows_needed_to_n20": rows_needed_to_n20(row.get("current_targetable_flagged_n")),
    }
