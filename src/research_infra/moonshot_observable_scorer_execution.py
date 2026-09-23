"""Research-only executable scorer helpers for moonshot observable runtime work."""

from __future__ import annotations

from typing import Any


SCORER_EXECUTION_SURFACE = "src/research_infra/moonshot_observable_scorer_execution.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _positive_delta(delta: float | None) -> bool:
    return delta is not None and delta > 0.0


def _score_band(value: float | None) -> str:
    if value is None:
        return "SCORE_BAND_NO_SCALAR"
    if value >= 0.75:
        return "SCORE_BAND_HIGH"
    if value >= 0.5:
        return "SCORE_BAND_MEDIUM"
    if value >= 0.25:
        return "SCORE_BAND_LOW"
    return "SCORE_BAND_WEAK"


def controlled_scorer_execution(runtime_row: dict[str, Any], action_row: dict[str, Any]) -> dict[str, Any]:
    delta = to_float(action_row.get("proxy_r_style_score_delta"))
    expectancy_delta = to_float(action_row.get("expectancy_style_proxy_delta"))
    control_count = int(action_row.get("control_match_count") or 0)
    observable_score = to_float(action_row.get("observable_proxy_score"))
    if _positive_delta(delta) and control_count > 0:
        status = "SCORER_EXECUTION_CONTROLLED_POSITIVE_DELTA"
        decision = "EXECUTE_BRANCH_LOCAL_CONTROLLED_CHALLENGER_SCORE"
    elif control_count <= 0:
        status = "SCORER_EXECUTION_CONTROL_MATCH_MISSING"
        decision = "BUILD_CONTROL_SCOPE_BEFORE_SCORING"
    elif delta is None:
        status = "SCORER_EXECUTION_CONTROLLED_NO_DELTA"
        decision = "PRESERVE_SCORER_CONTEXT_NO_SCALAR"
    else:
        status = "SCORER_EXECUTION_CONTROLLED_NONPOSITIVE_DELTA"
        decision = "DO_NOT_ADVANCE_CHALLENGER_WITHOUT_REDESIGN"
    score = clamp01((observable_score or 0.0) * 0.55 + max(delta or 0.0, 0.0) * 0.35 + min(control_count / 20, 1.0) * 0.10)
    return {
        "scorer_execution_surface": SCORER_EXECUTION_SURFACE,
        "scorer_execution_status": status,
        "scorer_execution_decision": decision,
        "scorer_execution_component": "controlled_observable_challenger",
        "proxy_r_style_score_delta": delta,
        "expectancy_style_proxy_delta": expectancy_delta,
        "scorer_proxy_score": score,
        "scorer_proxy_score_band": _score_band(score),
        "control_match_count": control_count,
        "control_proxy_score_mean": to_float(action_row.get("control_proxy_score_mean")),
        "control_proxy_score_min": to_float(action_row.get("control_proxy_score_min")),
        "control_proxy_score_max": to_float(action_row.get("control_proxy_score_max")),
        "source_repair_required": bool(action_row.get("source_repair_required")),
        "control_required": bool(action_row.get("control_required")),
        "executable_now": status == "SCORER_EXECUTION_CONTROLLED_POSITIVE_DELTA",
        "live_effect": False,
    }


def denominator_guarded_observable_execution(runtime_row: dict[str, Any], action_row: dict[str, Any]) -> dict[str, Any]:
    guard_strength = to_float(action_row.get("guard_strength_score"))
    guard_count = int(action_row.get("denominator_guard_match_count") or 0)
    if guard_strength is not None and guard_strength >= 0.8 and guard_count > 0:
        status = "SCORER_EXECUTION_DENOMINATOR_GUARDED_OBSERVABLE_STRONG"
        decision = "REGISTER_GUARDED_OBSERVABLE_WITH_STRONG_DENOMINATOR"
    elif guard_count > 0:
        status = "SCORER_EXECUTION_DENOMINATOR_GUARDED_OBSERVABLE_PARTIAL"
        decision = "REGISTER_GUARDED_OBSERVABLE_WITH_PARTIAL_DENOMINATOR"
    else:
        status = "SCORER_EXECUTION_DENOMINATOR_GUARD_MISSING"
        decision = "BUILD_DENOMINATOR_GUARD_BEFORE_REGISTRATION"
    score = clamp01((guard_strength or 0.0) * 0.80 + min(guard_count / 20, 1.0) * 0.20)
    return {
        "scorer_execution_surface": SCORER_EXECUTION_SURFACE,
        "scorer_execution_status": status,
        "scorer_execution_decision": decision,
        "scorer_execution_component": "denominator_guarded_observable",
        "guard_strength_score": guard_strength,
        "denominator_guard_match_count": guard_count,
        "denominator_guard_statuses": action_row.get("denominator_guard_statuses") or [],
        "scorer_proxy_score": score,
        "scorer_proxy_score_band": _score_band(score),
        "proxy_r_style_score_delta": to_float(action_row.get("proxy_r_style_score_delta")),
        "expectancy_style_proxy_delta": to_float(action_row.get("expectancy_style_proxy_delta")),
        "executable_now": status != "SCORER_EXECUTION_DENOMINATOR_GUARD_MISSING",
        "live_effect": False,
    }


def source_scorer_execution(runtime_row: dict[str, Any], action_row: dict[str, Any]) -> dict[str, Any]:
    family = str(action_row.get("source_action_result_family") or "")
    proxy_score = to_float(action_row.get("source_proxy_score"))
    delta = to_float(action_row.get("proxy_r_style_score_delta"))
    if family == "SOURCE_ACTION_GUARDED_PROXY_SCOREABLE":
        status = "SOURCE_SCORER_EXECUTION_GUARDED_PROXY_SCORE"
        decision = "SCORE_SOURCE_PROXY_WITH_GUARDS"
        control_required = False
    elif family == "SOURCE_ACTION_AMBIGUOUS_PROXY_CONTROL_REQUIRED":
        status = "SOURCE_SCORER_EXECUTION_AMBIGUOUS_PROXY_CONTROL_SCORE"
        decision = "SCORE_SOURCE_PROXY_WITH_AMBIGUITY_CONTROL"
        control_required = True
    else:
        status = "SOURCE_SCORER_EXECUTION_UNEXPECTED_SOURCE_FAMILY"
        decision = "PRESERVE_SOURCE_CONTEXT_REPAIR_CLASSIFICATION"
        control_required = bool(action_row.get("control_required"))
    score = clamp01((proxy_score or 0.0) * 0.70 + max(delta or 0.0, 0.0) * 0.30)
    return {
        "scorer_execution_surface": SCORER_EXECUTION_SURFACE,
        "source_scorer_execution_status": status,
        "source_scorer_execution_decision": decision,
        "source_action_result_family": family or None,
        "source_action_result_status": action_row.get("action_result_status"),
        "source_proxy_score": proxy_score,
        "proxy_r_style_score_delta": delta,
        "expectancy_style_proxy_delta": to_float(action_row.get("expectancy_style_proxy_delta")),
        "source_scorer_proxy_score": score,
        "source_scorer_proxy_score_band": _score_band(score),
        "control_required": control_required,
        "source_repair_required": bool(action_row.get("source_repair_required")),
        "executable_now": status in {
            "SOURCE_SCORER_EXECUTION_GUARDED_PROXY_SCORE",
            "SOURCE_SCORER_EXECUTION_AMBIGUOUS_PROXY_CONTROL_SCORE",
        },
        "live_effect": False,
    }


def control_scope_execution(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("control_scope_build_status") or "")
    selected_count = int(row.get("selected_control_count") or 0)
    if status == "CONTROL_SCOPE_BUILDER_EXACT_SCOPE_READY":
        execution_status = "CONTROL_SCOPE_EXECUTION_EXACT_READY"
        decision = "SCORE_WITH_EXACT_CONTROL_SCOPE"
        proxy_quality = 1.0
        can_score = True
    elif status == "CONTROL_SCOPE_BUILDER_PROXY_SAME_SYMBOL_SESSION_HORIZON_N20":
        execution_status = "CONTROL_SCOPE_EXECUTION_PROXY_SAME_SYMBOL_SESSION_HORIZON"
        decision = "SCORE_WITH_HORIZON_MATCHED_PROXY_CONTROL_GUARD"
        proxy_quality = 0.85
        can_score = True
    elif status == "CONTROL_SCOPE_BUILDER_PROXY_SAME_SYMBOL_SESSION_N20":
        execution_status = "CONTROL_SCOPE_EXECUTION_PROXY_SAME_SYMBOL_SESSION"
        decision = "SCORE_WITH_SESSION_MATCHED_PROXY_CONTROL_GUARD"
        proxy_quality = 0.7
        can_score = True
    elif status == "CONTROL_SCOPE_BUILDER_PROXY_SAME_SYMBOL_N20":
        execution_status = "CONTROL_SCOPE_EXECUTION_PROXY_SAME_SYMBOL"
        decision = "SCORE_WITH_SYMBOL_MATCHED_PROXY_CONTROL_GUARD"
        proxy_quality = 0.55
        can_score = True
    elif status == "CONTROL_SCOPE_BUILDER_UNDERPOWERED_GLOBAL_PROXY_ONLY":
        execution_status = "CONTROL_SCOPE_EXECUTION_EXACT_CONTROL_BUILD_REQUIRED"
        decision = "BUILD_EXACT_OR_BETTER_PROXY_CONTROL_BEFORE_SCALAR_SCORE"
        proxy_quality = 0.2
        can_score = False
    else:
        execution_status = "CONTROL_SCOPE_EXECUTION_NO_CONTROL_SOURCE"
        decision = "BUILD_CONTROL_DENOMINATOR_BEFORE_SCALAR_SCORE"
        proxy_quality = 0.0
        can_score = False
    score = clamp01(proxy_quality * 0.7 + min(selected_count / 20, 1.0) * 0.3)
    return {
        "scorer_execution_surface": SCORER_EXECUTION_SURFACE,
        "control_scope_execution_status": execution_status,
        "control_scope_execution_decision": decision,
        "control_scope_proxy_quality": proxy_quality,
        "control_scope_execution_score": score,
        "control_scope_can_score_now": can_score,
        "selected_control_count": selected_count,
        "exact_control_count": int(row.get("exact_control_count") or 0),
        "same_symbol_session_horizon_control_count": int(row.get("same_symbol_session_horizon_control_count") or 0),
        "same_symbol_session_control_count": int(row.get("same_symbol_session_control_count") or 0),
        "same_symbol_control_count": int(row.get("same_symbol_control_count") or 0),
        "desired_control_family": row.get("desired_control_family"),
        "missing_control_scope_key": row.get("missing_control_scope_key"),
        "selected_control_candidate_ids": row.get("selected_control_candidate_ids") or [],
        "selected_control_runtime_work_row_ids": row.get("selected_control_runtime_work_row_ids") or [],
        "selected_control_input_candidate_ids": row.get("selected_control_input_candidate_ids") or [],
        "selected_control_scope_keys": row.get("selected_control_scope_keys") or [],
        "executable_now": can_score,
        "live_effect": False,
    }


def control_comparator_execution(runtime_row: dict[str, Any], action_row: dict[str, Any]) -> dict[str, Any]:
    score = to_float(action_row.get("control_proxy_score"))
    if runtime_row.get("runtime_work_status") == "RUNTIME_WORK_PRESERVE_CONTEXT" or runtime_row.get(
        "input_candidate_status"
    ) == "CONTROL_IMPL_CONTEXT_ONLY":
        status = "CONTROL_EXECUTION_COMPARATOR_CONTEXT_ONLY"
    else:
        status = "CONTROL_EXECUTION_COMPARATOR_REGISTERED" if score is not None else "CONTROL_EXECUTION_COMPARATOR_CONTEXT_ONLY"
    return {
        "scorer_execution_surface": SCORER_EXECUTION_SURFACE,
        "control_execution_status": status,
        "control_execution_decision": "REGISTER_CONTROL_COMPARATOR_FOR_BRANCH_LOCAL_SCORING",
        "control_action_family": action_row.get("control_action_family"),
        "control_proxy_score": score,
        "control_proxy_score_band": _score_band(score),
        "control_required": bool(action_row.get("control_required")),
        "executable_now": status == "CONTROL_EXECUTION_COMPARATOR_REGISTERED",
        "live_effect": False,
    }


def denominator_guard_execution(runtime_row: dict[str, Any], action_row: dict[str, Any]) -> dict[str, Any]:
    guard_strength = to_float(action_row.get("guard_strength_score"))
    status = (
        "DENOMINATOR_EXECUTION_GUARD_REGISTERED"
        if action_row.get("action_result_status")
        else "DENOMINATOR_EXECUTION_GUARD_CONTEXT_ONLY"
    )
    return {
        "scorer_execution_surface": SCORER_EXECUTION_SURFACE,
        "denominator_execution_status": status,
        "denominator_execution_decision": "REGISTER_DENOMINATOR_GUARD_FOR_SCORER",
        "denominator_action_result_status": action_row.get("action_result_status"),
        "guard_strength_score": guard_strength,
        "guard_strength_band": _score_band(guard_strength),
        "executable_now": status == "DENOMINATOR_EXECUTION_GUARD_REGISTERED",
        "live_effect": False,
    }


def source_repair_execution(
    runtime_row: dict[str, Any],
    action_row: dict[str, Any],
    horizon_action_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status = str(runtime_row.get("source_repair_runtime_status") or "")
    source_family = str(action_row.get("source_action_result_family") or runtime_row.get("source_action_result_family") or "")
    fail_if_negative = bool(runtime_row.get("fail_if_negative_persists"))
    if status == "SOURCE_REPAIR_RUNTIME_EXACT_SOURCE_REBUILD_OR_ACQUIRE":
        execution_status = "SOURCE_REPAIR_EXECUTION_EXACT_SOURCE_REBUILD_OR_ACQUIRE"
        decision = "EXECUTE_EXACT_SOURCE_REPAIR_BEFORE_SCORING"
        exact_reason = "current branch has exact-source repair requirement; proxy scalar withheld until source rows are rebuilt or acquired"
    elif status == "SOURCE_REPAIR_RUNTIME_REBUILD_HORIZON_RESCORE":
        execution_status = "SOURCE_REPAIR_EXECUTION_HORIZON_REBUILD_RESCORE"
        decision = "EXECUTE_HORIZON_REBUILD_THEN_RECOMPUTE_SCORE"
        exact_reason = "horizon targetability is fail-closed or incomplete; rebuild targetable horizon rows and rescore"
    elif status == "SOURCE_REPAIR_RUNTIME_REBUILD_HORIZON_KILL_CHECK":
        execution_status = "SOURCE_REPAIR_EXECUTION_HORIZON_REBUILD_KILL_CHECK"
        decision = "EXECUTE_HORIZON_REBUILD_THEN_KILL_IF_NEGATIVE_PERSISTS"
        exact_reason = "negative proxy exists under horizon fail-closed stress; rebuild horizon rows and keep kill-check if negative persists"
    else:
        execution_status = "SOURCE_REPAIR_EXECUTION_CONTEXT_ONLY"
        decision = "PRESERVE_SOURCE_REPAIR_CONTEXT"
        exact_reason = "source repair status not executable from current runtime row"
    return {
        "scorer_execution_surface": SCORER_EXECUTION_SURFACE,
        "source_repair_execution_status": execution_status,
        "source_repair_execution_decision": decision,
        "source_action_result_family": source_family or None,
        "source_action_result_status": action_row.get("action_result_status") or runtime_row.get("source_action_result_status"),
        "source_proxy_score": to_float(action_row.get("source_proxy_score")),
        "horizon_proxy_score": to_float((horizon_action_row or {}).get("horizon_proxy_score")),
        "current_targetable_flagged_n": (horizon_action_row or {}).get("current_targetable_flagged_n"),
        "current_source_flagged_n": (horizon_action_row or {}).get("current_source_flagged_n"),
        "current_failclosed_flagged_n": (horizon_action_row or {}).get("current_failclosed_flagged_n"),
        "duplicate_repair_scope_count": int(runtime_row.get("duplicate_repair_scope_count") or 0),
        "fail_if_negative_persists": fail_if_negative,
        "exact_missing_geometry_or_source_reason": exact_reason,
        "executable_now": execution_status != "SOURCE_REPAIR_EXECUTION_CONTEXT_ONLY",
        "live_effect": False,
    }


def horizon_repair_execution(runtime_row: dict[str, Any], action_row: dict[str, Any]) -> dict[str, Any]:
    status = str(action_row.get("action_result_status") or runtime_row.get("input_candidate_status") or "")
    if status == "HORIZON_ACTION_RESULT_REBUILD_RESCORE":
        execution_status = "HORIZON_REPAIR_EXECUTION_REBUILD_RESCORE"
        decision = "REBUILD_TARGETABLE_HORIZON_AND_RESCORE"
    elif status == "HORIZON_ACTION_RESULT_REBUILD_KILL_CHECK":
        execution_status = "HORIZON_REPAIR_EXECUTION_REBUILD_KILL_CHECK"
        decision = "REBUILD_TARGETABLE_HORIZON_AND_KILL_IF_NEGATIVE"
    else:
        execution_status = "HORIZON_REPAIR_EXECUTION_CONTEXT_ONLY"
        decision = "PRESERVE_HORIZON_REPAIR_CONTEXT"
    return {
        "scorer_execution_surface": SCORER_EXECUTION_SURFACE,
        "horizon_repair_execution_status": execution_status,
        "horizon_repair_execution_decision": decision,
        "horizon_proxy_score": to_float(action_row.get("horizon_proxy_score")),
        "current_targetable_flagged_n": action_row.get("current_targetable_flagged_n"),
        "current_source_flagged_n": action_row.get("current_source_flagged_n"),
        "current_failclosed_flagged_n": action_row.get("current_failclosed_flagged_n"),
        "source_repair_required": bool(action_row.get("source_repair_required") or runtime_row.get("runtime_source_repair_required")),
        "executable_now": execution_status != "HORIZON_REPAIR_EXECUTION_CONTEXT_ONLY",
        "live_effect": False,
    }


def coverage_scorer_execution(runtime_row: dict[str, Any], action_row: dict[str, Any]) -> dict[str, Any]:
    status = str(action_row.get("action_result_status") or runtime_row.get("input_candidate_status") or "")
    if "CONTROL" in status:
        execution_status = "COVERAGE_EXECUTION_CONTROL_PATH_ACTIVE"
    elif "SOURCE" in status:
        execution_status = "COVERAGE_EXECUTION_SOURCE_OR_REPAIR_PATH_ACTIVE"
    elif "DENOMINATOR" in status:
        execution_status = "COVERAGE_EXECUTION_DENOMINATOR_GUARD_ACTIVE"
    elif "HORIZON" in status:
        execution_status = "COVERAGE_EXECUTION_HORIZON_REPAIR_ACTIVE"
    elif "OBSERVABLE" in status:
        execution_status = "COVERAGE_EXECUTION_OBSERVABLE_CANDIDATE_ACTIVE"
    else:
        execution_status = "COVERAGE_EXECUTION_CONTEXT_PRESERVED"
    return {
        "scorer_execution_surface": SCORER_EXECUTION_SURFACE,
        "coverage_execution_status": execution_status,
        "coverage_execution_decision": "PRESERVE_OR_EXECUTE_FULL_COVERAGE_PATH",
        "coverage_row_count": action_row.get("coverage_row_count"),
        "covered_status_counts": action_row.get("covered_status_counts") or {},
        "implementation_stage_counts": action_row.get("implementation_stage_counts") or {},
        "live_effect": False,
    }
