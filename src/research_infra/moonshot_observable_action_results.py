"""Research-only action-result helpers for moonshot observable execution rows."""

from __future__ import annotations

from statistics import mean
from typing import Any


ACTION_RESULT_SURFACE = "src/research_infra/moonshot_observable_action_results.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _score(row: dict[str, Any]) -> float:
    return clamp01(to_float(row.get("execution_priority_score")) or 0.0)


def _score_values(rows: list[dict[str, Any]]) -> list[float]:
    return [_score(row) for row in rows]


def _delta_status(delta: float, n: int) -> str:
    if n <= 0:
        return "CONTROL_SCORE_RESULT_CONTROL_MATCH_MISSING"
    if delta >= 0.05:
        return "CONTROL_SCORE_RESULT_POSITIVE_DELTA"
    if delta <= -0.05:
        return "CONTROL_SCORE_RESULT_NEGATIVE_DELTA"
    return "CONTROL_SCORE_RESULT_NEUTRAL_DELTA"


def desired_control_family(row: dict[str, Any]) -> str:
    family = str(row.get("observable_family") or "")
    binding = str(row.get("scorer_binding") or "")
    if family == "ENTRY_GEOMETRY_OBSERVABLE":
        return "CONTROL_EXPERIMENT_ENTRY_GEOMETRY_VS_STATUS_QUO"
    if family == "MARKET_ENTRY_COMPARATOR_OBSERVABLE":
        return "CONTROL_EXPERIMENT_FILLABILITY_REDESIGN_BEFORE_ENABLE"
    if family == "MARKET_GAP_ENTRY_GEOMETRY_OBSERVABLE":
        return "CONTROL_EXPERIMENT_MARKET_GAP_ENTRY_VS_STATUS_QUO"
    if family == "AVOID_FILTER_OBSERVABLE":
        return "CONTROL_EXPERIMENT_AVOID_FILTER_WITH_INVERSE_SIBLING"
    if binding == "status_quo_control_required":
        return "CONTROL_EXPERIMENT_STATUS_QUO_REQUIRED"
    return "CONTROL_EXPERIMENT_NOT_REQUIRED"


def controlled_observable_score_result(
    observable_row: dict[str, Any],
    control_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    control_scores = _score_values(control_rows)
    observable_score = _score(observable_row)
    control_mean = round(mean(control_scores), 6) if control_scores else None
    control_min = min(control_scores) if control_scores else None
    control_max = max(control_scores) if control_scores else None
    delta = round(observable_score - control_mean, 6) if control_mean is not None else None
    status = _delta_status(delta or 0.0, len(control_scores))
    if status == "CONTROL_SCORE_RESULT_POSITIVE_DELTA":
        decision = "ACTION_RESULT_KEEP_OBSERVABLE_CHALLENGER_UNDER_CONTROL"
    elif status == "CONTROL_SCORE_RESULT_NEGATIVE_DELTA":
        decision = "ACTION_RESULT_KILL_OR_REDESIGN_OBSERVABLE_UNDER_CONTROL"
    elif status == "CONTROL_SCORE_RESULT_NEUTRAL_DELTA":
        decision = "ACTION_RESULT_SCORE_OBSERVABLE_NEUTRAL_UNDER_CONTROL"
    else:
        decision = "ACTION_RESULT_REQUIRE_EXACT_CONTROL_BEFORE_SCORE"
    return {
        "action_result_surface": ACTION_RESULT_SURFACE,
        "action_stage": "OBSERVABLE_ACTION_RESULT",
        "action_result_status": status,
        "action_result_decision": decision,
        "desired_control_family": desired_control_family(observable_row),
        "control_match_count": len(control_scores),
        "observable_proxy_score": observable_score,
        "control_proxy_score_mean": control_mean,
        "control_proxy_score_min": control_min,
        "control_proxy_score_max": control_max,
        "proxy_r_style_score_delta": delta,
        "expectancy_style_proxy_delta": delta,
        "source_repair_required": False,
        "control_required": True,
        "live_effect": False,
    }


def denominator_guarded_observable_result(
    observable_row: dict[str, Any],
    denominator_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    guard_count = int(observable_row.get("denominator_guard_match_count") or len(denominator_rows))
    guard_strength = clamp01(guard_count / 20.0)
    if guard_count >= 10:
        status = "DENOMINATOR_RESULT_STRONG_SCOPE_GUARD_REGISTER"
        decision = "ACTION_RESULT_REGISTER_OBSERVABLE_WITH_STRONG_DENOMINATOR_GUARD"
    elif guard_count > 0:
        status = "DENOMINATOR_RESULT_SCOPE_GUARD_REGISTER"
        decision = "ACTION_RESULT_REGISTER_OBSERVABLE_WITH_DENOMINATOR_GUARD"
    else:
        status = "DENOMINATOR_RESULT_GUARD_MISSING_FOR_OBSERVABLE"
        decision = "ACTION_RESULT_REQUIRE_DENOMINATOR_GUARD_BEFORE_REGISTER"
    return {
        "action_result_surface": ACTION_RESULT_SURFACE,
        "action_stage": "OBSERVABLE_ACTION_RESULT",
        "action_result_status": status,
        "action_result_decision": decision,
        "denominator_guard_match_count": guard_count,
        "denominator_guard_statuses": [str(row.get("input_implementation_status")) for row in denominator_rows],
        "guard_strength_score": guard_strength,
        "proxy_r_style_score_delta": None,
        "expectancy_style_proxy_delta": None,
        "source_repair_required": False,
        "control_required": False,
        "live_effect": False,
    }


def control_lookup_requirement_result(observable_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_result_surface": ACTION_RESULT_SURFACE,
        "action_stage": "OBSERVABLE_ACTION_RESULT",
        "action_result_status": "CONTROL_LOOKUP_RESULT_EXACT_SCOPE_REQUIRED",
        "action_result_decision": "ACTION_RESULT_BUILD_OR_MATCH_CONTROL_FOR_OBSERVABLE_SCOPE",
        "desired_control_family": desired_control_family(observable_row),
        "missing_control_scope_key": observable_row.get("observable_scope_key"),
        "denominator_guard_match_count": int(observable_row.get("denominator_guard_match_count") or 0),
        "source_policy_match_count": int(observable_row.get("source_policy_match_count") or 0),
        "proxy_r_style_score_delta": None,
        "expectancy_style_proxy_delta": None,
        "source_repair_required": False,
        "control_required": True,
        "live_effect": False,
    }


def observable_action_result(
    observable_row: dict[str, Any],
    control_rows: list[dict[str, Any]],
    denominator_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    decision = str(observable_row.get("execution_decision") or "")
    if decision == "OBSERVABLE_EXECUTE_SCORE_WITH_CONTROL_NOW":
        return controlled_observable_score_result(observable_row, control_rows)
    if decision == "OBSERVABLE_EXECUTE_REGISTER_WITH_DENOMINATOR_GUARD":
        return denominator_guarded_observable_result(observable_row, denominator_rows)
    if decision == "OBSERVABLE_EXECUTE_CONTROL_LOOKUP_REQUIRED":
        return control_lookup_requirement_result(observable_row)
    return {
        "action_result_surface": ACTION_RESULT_SURFACE,
        "action_stage": "OBSERVABLE_ACTION_RESULT",
        "action_result_status": "OBSERVABLE_ACTION_RESULT_CONTEXT_ONLY",
        "action_result_decision": "ACTION_RESULT_PRESERVE_OBSERVABLE_CONTEXT",
        "proxy_r_style_score_delta": None,
        "expectancy_style_proxy_delta": None,
        "source_repair_required": False,
        "control_required": bool(observable_row.get("control_required")),
        "live_effect": False,
    }


def source_policy_action_result(row: dict[str, Any]) -> dict[str, Any]:
    decision = str(row.get("execution_decision") or "")
    proxy_score = _score(row)
    if decision == "SOURCE_EXECUTE_GUARDED_PROXY_SCORE_NOW":
        family = "SOURCE_ACTION_GUARDED_PROXY_SCOREABLE"
        status = "SOURCE_POLICY_RESULT_GUARDED_PROXY_SCOREABLE"
        action = "ACTION_RESULT_SCORE_GUARDED_PROXY_NOW"
        repair_required = False
        score_delta = proxy_score
    elif decision == "SOURCE_EXECUTE_AMBIGUOUS_PROXY_SCORE_WITH_CONTROL":
        family = "SOURCE_ACTION_AMBIGUOUS_PROXY_CONTROL_REQUIRED"
        status = "SOURCE_POLICY_RESULT_AMBIGUOUS_PROXY_CONTROL_REQUIRED"
        action = "ACTION_RESULT_SCORE_PROXY_WITH_AMBIGUITY_CONTROL"
        repair_required = False
        score_delta = round(proxy_score - 0.05, 6)
    elif decision == "SOURCE_EXECUTE_EXACT_SOURCE_REPAIR_WORK_ORDER":
        family = "SOURCE_ACTION_EXACT_SOURCE_REPAIR"
        status = "SOURCE_POLICY_RESULT_EXACT_REPAIR_REQUIRED"
        action = "ACTION_RESULT_REBUILD_EXACT_SOURCE_BEFORE_ENABLE"
        repair_required = True
        score_delta = None
    elif decision == "SOURCE_EXECUTE_HORIZON_REPAIR_AND_KILL_CHECK":
        family = "SOURCE_ACTION_HORIZON_REPAIR_KILL_CHECK"
        status = "SOURCE_POLICY_RESULT_HORIZON_REPAIR_KILL_CHECK"
        action = "ACTION_RESULT_REBUILD_HORIZON_AND_KILL_IF_NEGATIVE"
        repair_required = True
        score_delta = None
    elif decision == "SOURCE_EXECUTE_HORIZON_REPAIR_AND_RESCORE":
        family = "SOURCE_ACTION_HORIZON_REPAIR_RESCORE"
        status = "SOURCE_POLICY_RESULT_HORIZON_REPAIR_RESCORE"
        action = "ACTION_RESULT_REBUILD_HORIZON_AND_RESCORE"
        repair_required = True
        score_delta = None
    else:
        family = "SOURCE_ACTION_CONTEXT_ONLY"
        status = "SOURCE_POLICY_RESULT_CONTEXT_ONLY"
        action = "ACTION_RESULT_PRESERVE_SOURCE_CONTEXT"
        repair_required = False
        score_delta = None
    return {
        "action_result_surface": ACTION_RESULT_SURFACE,
        "action_stage": "SOURCE_POLICY_ACTION_RESULT",
        "source_action_result_family": family,
        "action_result_status": status,
        "action_result_decision": action,
        "source_proxy_score": proxy_score,
        "proxy_r_style_score_delta": score_delta,
        "expectancy_style_proxy_delta": score_delta,
        "source_repair_required": repair_required,
        "control_required": decision == "SOURCE_EXECUTE_AMBIGUOUS_PROXY_SCORE_WITH_CONTROL",
        "live_effect": False,
    }


def control_action_result(row: dict[str, Any]) -> dict[str, Any]:
    decision = str(row.get("execution_decision") or "")
    family = {
        "CONTROL_EXECUTE_ENTRY_STATUS_QUO_COMPARATOR": "CONTROL_ACTION_ENTRY_STATUS_QUO",
        "CONTROL_EXECUTE_FILLABILITY_REDESIGN_COMPARATOR": "CONTROL_ACTION_FILLABILITY_REDESIGN",
        "CONTROL_EXECUTE_MARKET_GAP_ENTRY_COMPARATOR": "CONTROL_ACTION_MARKET_GAP_ENTRY",
        "CONTROL_EXECUTE_AVOID_INVERSE_SIBLING_COMPARATOR": "CONTROL_ACTION_AVOID_INVERSE_SIBLING",
        "CONTROL_EXECUTE_SCORER_PATCH_ABLATION": "CONTROL_ACTION_SCORER_PATCH_ABLATION",
    }.get(decision, "CONTROL_ACTION_CONTEXT_ONLY")
    return {
        "action_result_surface": ACTION_RESULT_SURFACE,
        "action_stage": "CONTROL_ACTION_RESULT",
        "control_action_family": family,
        "action_result_status": "CONTROL_RESULT_COMPARATOR_READY"
        if family != "CONTROL_ACTION_CONTEXT_ONLY"
        else "CONTROL_RESULT_CONTEXT_ONLY",
        "action_result_decision": "ACTION_RESULT_RUN_CONTROL_COMPARATOR"
        if family != "CONTROL_ACTION_CONTEXT_ONLY"
        else "ACTION_RESULT_PRESERVE_CONTROL_CONTEXT",
        "control_proxy_score": _score(row),
        "proxy_r_style_score_delta": None,
        "expectancy_style_proxy_delta": None,
        "source_repair_required": False,
        "control_required": bool(row.get("control_required_before_enable", True)),
        "live_effect": False,
    }


def denominator_action_result(row: dict[str, Any]) -> dict[str, Any]:
    decision = str(row.get("execution_decision") or "")
    if decision == "DENOMINATOR_EXECUTE_OUTSIDE_BRANCH_SCOPE_GUARD":
        status = "DENOMINATOR_ACTION_RESULT_OUTSIDE_BRANCH_SCOPE_ENFORCED"
    elif decision == "DENOMINATOR_EXECUTE_SOURCE_ROOT_COVERAGE_GUARD":
        status = "DENOMINATOR_ACTION_RESULT_SOURCE_ROOT_COVERAGE_ENFORCED"
    elif decision == "DENOMINATOR_EXECUTE_MECHANISM_ARTIFACT_SPLIT_GUARD":
        status = "DENOMINATOR_ACTION_RESULT_MECHANISM_ARTIFACT_SPLIT_ENFORCED"
    else:
        status = "DENOMINATOR_ACTION_RESULT_CONTEXT_COVERAGE_ENFORCED"
    return {
        "action_result_surface": ACTION_RESULT_SURFACE,
        "action_stage": "DENOMINATOR_ACTION_RESULT",
        "action_result_status": status,
        "action_result_decision": "ACTION_RESULT_ENFORCE_DENOMINATOR_GUARD",
        "guard_strength_score": _score(row),
        "proxy_r_style_score_delta": None,
        "expectancy_style_proxy_delta": None,
        "source_repair_required": False,
        "control_required": False,
        "live_effect": False,
    }


def horizon_work_order_result(row: dict[str, Any]) -> dict[str, Any]:
    decision = str(row.get("execution_decision") or "")
    if decision == "HORIZON_WORK_ORDER_REBUILD_THEN_KILL_IF_NEGATIVE":
        status = "HORIZON_ACTION_RESULT_REBUILD_KILL_CHECK"
        action = "ACTION_RESULT_REBUILD_TARGETABLE_HORIZON_KILL_IF_NEGATIVE"
    elif decision == "HORIZON_WORK_ORDER_REBUILD_THEN_ALLOW_IF_POSITIVE":
        status = "HORIZON_ACTION_RESULT_REBUILD_ALLOW_IF_POSITIVE"
        action = "ACTION_RESULT_REBUILD_TARGETABLE_HORIZON_ALLOW_IF_POSITIVE"
    else:
        status = "HORIZON_ACTION_RESULT_REBUILD_RESCORE"
        action = "ACTION_RESULT_REBUILD_TARGETABLE_HORIZON_RESCORE"
    return {
        "action_result_surface": ACTION_RESULT_SURFACE,
        "action_stage": "HORIZON_WORK_ORDER_ACTION_RESULT",
        "action_result_status": status,
        "action_result_decision": action,
        "horizon_proxy_score": _score(row),
        "source_repair_required": True,
        "control_required": False,
        "live_effect": False,
    }


def coverage_action_result(row: dict[str, Any]) -> dict[str, Any]:
    decision = str(row.get("execution_decision") or "")
    status = {
        "COVERAGE_EXECUTE_HORIZON_REPAIR_PATH": "COVERAGE_ACTION_RESULT_HORIZON_REPAIR_ACTIVE",
        "COVERAGE_EXECUTE_SOURCE_POLICY_OR_REPAIR": "COVERAGE_ACTION_RESULT_SOURCE_POLICY_ACTIVE",
        "COVERAGE_EXECUTE_CONTROL_EXPERIMENT": "COVERAGE_ACTION_RESULT_CONTROL_EXPERIMENT_ACTIVE",
        "COVERAGE_EXECUTE_DENOMINATOR_GUARD": "COVERAGE_ACTION_RESULT_DENOMINATOR_GUARD_ACTIVE",
        "COVERAGE_REGISTER_OBSERVABLE_CANDIDATE": "COVERAGE_ACTION_RESULT_OBSERVABLE_CANDIDATE_ACTIVE",
    }.get(decision, "COVERAGE_ACTION_RESULT_CONTEXT_ONLY")
    return {
        "action_result_surface": ACTION_RESULT_SURFACE,
        "action_stage": "PRIMITIVE_COVERAGE_ACTION_RESULT",
        "action_result_status": status,
        "action_result_decision": "ACTION_RESULT_PRESERVE_FULL_COVERAGE_MAP",
        "coverage_row_count": row.get("row_count"),
        "source_repair_required": decision == "COVERAGE_EXECUTE_HORIZON_REPAIR_PATH",
        "control_required": decision == "COVERAGE_EXECUTE_CONTROL_EXPERIMENT",
        "live_effect": False,
    }
