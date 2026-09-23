"""Consume exact-control construction rows into default-off scorers and redesigns."""

from __future__ import annotations

from typing import Any


EXACT_CONTROL_SCORER_REDESIGN_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_scorer_redesign.py"
)


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))


def redesign_family(row: dict[str, Any]) -> str | None:
    result_class = row.get("exact_control_result_class")
    if result_class != "EXACT_CONTROL_NEGATIVE_TARGET_DELTA_ALIGNMENT_POSITIVE_SPLIT":
        return None
    delta = to_float(row.get("exact_control_proxy_r_style_delta")) or 0.0
    if delta <= -0.25:
        return "REDESIGN_DIRECTIONAL_FEATURE_DROP_TARGET_MAGNITUDE_SCALAR"
    if delta >= -0.05:
        return "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON"
    return "REDESIGN_HORIZON_ENTRY_GEOMETRY_SPLIT"


def exact_control_scope_runtime_spec(scope_row: dict[str, Any]) -> dict[str, Any]:
    result_class = str(scope_row.get("exact_control_result_class"))
    positive = result_class == "EXACT_CONTROL_POSITIVE_TARGET_AND_ALIGNMENT_DELTA"
    split_family = redesign_family(scope_row)
    if positive:
        status = "EXACT_CONTROL_SCOPE_DEFAULT_OFF_SCORER_REGISTER"
        action = "register_default_off_exact_control_scope_scorer"
        score = to_float(scope_row.get("exact_control_proxy_r_style_delta"))
    else:
        status = "EXACT_CONTROL_SCOPE_SPLIT_REDESIGN_REGISTER"
        action = "register_alignment_positive_target_delta_redesign"
        score = None
    return {
        "exact_control_scorer_redesign_surface": EXACT_CONTROL_SCORER_REDESIGN_SURFACE,
        "input_scope_construction_row_id": scope_row.get("exact_control_scope_construction_row_id"),
        "input_scope_effective_n_row_id": scope_row.get("input_scope_effective_n_row_id"),
        "symbol": scope_row.get("symbol"),
        "route_session": scope_row.get("route_session"),
        "tick_session_bucket": scope_row.get("tick_session_bucket"),
        "horizon_id": scope_row.get("horizon_id"),
        "primitive_flag": scope_row.get("primitive_flag"),
        "outside_gbpjpy_xauusd_current_branch_box": scope_row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "exact_control_scope_runtime_status": status,
        "exact_control_scope_runtime_action": action,
        "exact_control_result_class": result_class,
        "exact_control_flagged_n": scope_row.get("exact_control_flagged_n"),
        "exact_control_control_n": scope_row.get("exact_control_control_n"),
        "exact_control_proxy_r_style_delta": scope_row.get("exact_control_proxy_r_style_delta"),
        "exact_control_alignment_delta": scope_row.get("exact_control_alignment_delta"),
        "default_off_exact_control_score": score,
        "redesign_family": split_family,
        "branch_local_score_allowed": positive,
        "branch_local_redesign_required": split_family is not None,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }


def exact_control_blocker_runtime_decision(
    blocker_row: dict[str, Any],
    scope_spec_row: dict[str, Any] | None,
) -> dict[str, Any]:
    scope = scope_spec_row or {}
    score_allowed = bool(scope.get("branch_local_score_allowed"))
    redesign_required = bool(scope.get("branch_local_redesign_required"))
    if score_allowed:
        status = "EXACT_CONTROL_BLOCKER_DEFAULT_OFF_SCORER_READY"
        decision = "score_exact_scope_default_off_research_only"
    elif redesign_required:
        status = "EXACT_CONTROL_BLOCKER_SPLIT_REDESIGN_REQUIRED"
        decision = "do_not_score_target_delta_preserve_alignment_redesign"
    else:
        status = "EXACT_CONTROL_BLOCKER_CONSTRUCTION_UNCONSUMED_RECHECK"
        decision = "recheck_construction_inputs"
    return {
        "exact_control_scorer_redesign_surface": EXACT_CONTROL_SCORER_REDESIGN_SURFACE,
        "input_blocker_construction_row_id": blocker_row.get("exact_control_blocker_construction_row_id"),
        "input_exact_control_blocker_effective_n_row_id": blocker_row.get("input_exact_control_blocker_effective_n_row_id"),
        "symbol": blocker_row.get("symbol"),
        "route_session": blocker_row.get("route_session"),
        "tick_session_bucket": blocker_row.get("tick_session_bucket"),
        "horizon_id": blocker_row.get("horizon_id"),
        "primitive_flag": blocker_row.get("primitive_flag"),
        "outside_gbpjpy_xauusd_current_branch_box": blocker_row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "exact_control_blocker_runtime_status": status,
        "exact_control_blocker_runtime_decision": decision,
        "exact_control_result_class": blocker_row.get("exact_control_result_class"),
        "exact_control_proxy_r_style_delta": blocker_row.get("exact_control_proxy_r_style_delta"),
        "exact_control_alignment_delta": blocker_row.get("exact_control_alignment_delta"),
        "default_off_exact_control_score": scope.get("default_off_exact_control_score"),
        "redesign_family": scope.get("redesign_family"),
        "branch_local_score_allowed": score_allowed,
        "branch_local_redesign_required": redesign_required,
        "missed_opportunity_preserved": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }


def exact_control_event_score(
    event_row: dict[str, Any],
    scope_spec_row: dict[str, Any] | None,
) -> dict[str, Any]:
    scope = scope_spec_row or {}
    primitive_present = bool(event_row.get("primitive_present"))
    score_allowed = bool(scope.get("branch_local_score_allowed"))
    redesign_required = bool(scope.get("branch_local_redesign_required"))
    if primitive_present and score_allowed:
        status = "EXACT_CONTROL_EVENT_DEFAULT_OFF_SCORE_EMITTED"
        score = scope.get("default_off_exact_control_score")
        redesign_signal = None
    elif primitive_present and redesign_required:
        status = "EXACT_CONTROL_EVENT_REDESIGN_ALIGNMENT_SIGNAL_EMITTED"
        score = None
        redesign_signal = scope.get("exact_control_alignment_delta")
    elif primitive_present:
        status = "EXACT_CONTROL_EVENT_PRIMITIVE_PRESENT_UNCONSUMED_RECHECK"
        score = None
        redesign_signal = None
    else:
        status = "EXACT_CONTROL_EVENT_DENOMINATOR_CONTROL_CONTEXT"
        score = None
        redesign_signal = None
    return {
        "exact_control_scorer_redesign_surface": EXACT_CONTROL_SCORER_REDESIGN_SURFACE,
        "input_denominator_event_row_id": event_row.get("exact_control_denominator_event_row_id"),
        "input_scope_construction_row_id": event_row.get("input_scope_construction_row_id")
        or event_row.get("input_scope_effective_n_row_id"),
        "symbol": event_row.get("symbol"),
        "route_session": event_row.get("route_session"),
        "tick_session_bucket": event_row.get("tick_session_bucket"),
        "horizon_id": event_row.get("horizon_id"),
        "primitive_flag": event_row.get("primitive_flag"),
        "bar_open_utc": event_row.get("bar_open_utc"),
        "future_bar_open_utc": event_row.get("future_bar_open_utc"),
        "primitive_present": primitive_present,
        "exact_control_event_runtime_status": status,
        "default_off_exact_control_event_score": score,
        "redesign_alignment_signal": redesign_signal,
        "redesign_family": scope.get("redesign_family"),
        "future_change_per_current_range": event_row.get("future_change_per_current_range"),
        "delta_aligned_with_future": event_row.get("delta_aligned_with_future"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
