"""Translate exact-control scorer/redesign rows into implementation candidates."""

from __future__ import annotations

from typing import Any


EXACT_CONTROL_IMPLEMENTATION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_implementation_candidates.py"
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


def mechanical_scope_key(row: dict[str, Any]) -> str:
    return (
        f"symbol={row.get('symbol')}|session={row.get('route_session')}|"
        f"horizon={row.get('horizon_id')}|primitive={row.get('primitive_flag')}"
    )


def _score_band(value: float | None) -> str:
    if value is None:
        return "NO_SCALAR"
    if value >= 0.20:
        return "EXACT_CONTROL_SCORE_STRONG_POSITIVE"
    if value >= 0.05:
        return "EXACT_CONTROL_SCORE_POSITIVE"
    if value >= 0.0:
        return "EXACT_CONTROL_SCORE_THIN_POSITIVE"
    return "EXACT_CONTROL_SCORE_NEGATIVE_REDESIGN_REQUIRED"


def _common(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "exact_control_implementation_surface": EXACT_CONTROL_IMPLEMENTATION_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "tick_session_bucket": row.get("tick_session_bucket"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "mechanical_scope_key": mechanical_scope_key(row),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }


def exact_control_scope_implementation_candidate(scope_row: dict[str, Any]) -> dict[str, Any]:
    status = scope_row.get("exact_control_scope_runtime_status")
    score = to_float(scope_row.get("default_off_exact_control_score"))
    if status == "EXACT_CONTROL_SCOPE_DEFAULT_OFF_SCORER_REGISTER":
        candidate_status = "EXACT_CONTROL_SCOPE_IMPLEMENT_DEFAULT_OFF_SCORER_CODE_PATH"
        candidate_family = "EXACT_CONTROL_DEFAULT_OFF_SCORER"
        action = "register_exact_scope_default_off_scorer_code_path"
        decision = "IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE"
        missing_or_repair_reason = None
        required_runtime_fields = [
            "symbol",
            "route_session",
            "horizon_id",
            "primitive_flag",
            "tick_session_bucket",
            "primitive_present",
        ]
        expression = (
            f"if {mechanical_scope_key(scope_row)} and primitive_present then emit "
            "default_off_exact_control_score as research-only scorer"
        )
    else:
        candidate_status = "EXACT_CONTROL_SCOPE_IMPLEMENT_SPLIT_REDESIGN_CODE_PATH"
        candidate_family = "EXACT_CONTROL_SPLIT_REDESIGN"
        action = "register_alignment_positive_target_negative_redesign_code_path"
        decision = "IMPLEMENT_SPLIT_REDESIGN_CANDIDATE"
        missing_or_repair_reason = "target_delta_negative_alignment_positive_requires_split_before_scalar_use"
        required_runtime_fields = [
            "symbol",
            "route_session",
            "horizon_id",
            "primitive_flag",
            "tick_session_bucket",
            "primitive_present",
            "delta_aligned_with_future",
        ]
        expression = (
            f"if {mechanical_scope_key(scope_row)} and primitive_present then route to "
            f"{scope_row.get('redesign_family')} instead of target-delta scalar use"
        )
    return {
        **_common(scope_row),
        "input_scope_runtime_spec_row_id": scope_row.get("exact_control_scope_runtime_spec_row_id"),
        "input_scope_construction_row_id": scope_row.get("input_scope_construction_row_id"),
        "exact_control_scope_implementation_status": candidate_status,
        "implementation_candidate_family": candidate_family,
        "implementation_decision": decision,
        "implementation_action": action,
        "default_off_exact_control_score": score,
        "score_band": _score_band(score),
        "exact_control_result_class": scope_row.get("exact_control_result_class"),
        "exact_control_alignment_delta": scope_row.get("exact_control_alignment_delta"),
        "redesign_family": scope_row.get("redesign_family"),
        "required_runtime_fields": required_runtime_fields,
        "mechanical_rule_expression": expression,
        "missing_or_repair_reason": missing_or_repair_reason,
        "candidate_use_allowed_now": False,
        "missed_opportunity_preserved": True,
    }


def exact_control_blocker_implementation_candidate(
    blocker_row: dict[str, Any],
    scorer_row: dict[str, Any] | None = None,
    redesign_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status = blocker_row.get("exact_control_blocker_runtime_status")
    score = to_float(blocker_row.get("default_off_exact_control_score"))
    scorer = scorer_row or {}
    redesign = redesign_row or {}
    if status == "EXACT_CONTROL_BLOCKER_DEFAULT_OFF_SCORER_READY":
        candidate_status = "EXACT_CONTROL_BLOCKER_IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE"
        candidate_family = "EXACT_CONTROL_DEFAULT_OFF_SCORER"
        action = "materialize_blocker_default_off_exact_control_scorer"
        decision = "IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE"
        blocker_implication = "branch_local_default_off_scorer_candidate_exact_n20_available"
        preserve_route = "preserve_score_and_compare_against controls before any promotion dossier"
    elif status == "EXACT_CONTROL_BLOCKER_SPLIT_REDESIGN_REQUIRED":
        candidate_status = "EXACT_CONTROL_BLOCKER_IMPLEMENT_SPLIT_REDESIGN_CANDIDATE"
        candidate_family = "EXACT_CONTROL_SPLIT_REDESIGN"
        action = "materialize_alignment_positive_target_delta_redesign"
        decision = "IMPLEMENT_SPLIT_REDESIGN_CANDIDATE"
        blocker_implication = "do_not_use_negative_target_delta_as_scalar_preserve_alignment_signal"
        preserve_route = "split_horizon_direction_entry_geometry_or_convert_to_avoid_inverse_context"
    else:
        candidate_status = "EXACT_CONTROL_BLOCKER_RECHECK_IMPLEMENTATION_INPUTS"
        candidate_family = "EXACT_CONTROL_RECHECK"
        action = "recheck_exact_control_scorer_redesign_inputs"
        decision = "RECHECK_BEFORE_IMPLEMENTATION"
        blocker_implication = "missing scorer_redesign status"
        preserve_route = "repair_input_join_before rejecting current claim"
    return {
        **_common(blocker_row),
        "input_blocker_runtime_decision_row_id": blocker_row.get("exact_control_blocker_runtime_decision_row_id"),
        "input_blocker_construction_row_id": blocker_row.get("input_blocker_construction_row_id"),
        "input_scope_default_off_scorer_row_id": scorer.get("exact_control_scope_default_off_scorer_row_id"),
        "input_redesign_execution_row_id": redesign.get("exact_control_redesign_execution_row_id"),
        "exact_control_blocker_implementation_status": candidate_status,
        "implementation_candidate_family": candidate_family,
        "implementation_decision": decision,
        "implementation_action": action,
        "implementation_implication": blocker_implication,
        "default_off_exact_control_score": score,
        "score_band": _score_band(score),
        "exact_control_proxy_r_style_delta": blocker_row.get("exact_control_proxy_r_style_delta"),
        "exact_control_alignment_delta": blocker_row.get("exact_control_alignment_delta"),
        "exact_control_result_class": blocker_row.get("exact_control_result_class"),
        "redesign_family": blocker_row.get("redesign_family"),
        "mechanical_rule_expression": (
            f"{mechanical_scope_key(blocker_row)} maps {status} to {action}; "
            "candidate remains default-off and branch-local"
        ),
        "missed_opportunity_preserved": True,
        "missed_opportunity_preservation_route": preserve_route,
        "candidate_use_allowed_now": False,
    }


def exact_control_event_implementation_observation(event_row: dict[str, Any]) -> dict[str, Any]:
    status = event_row.get("exact_control_event_runtime_status")
    if status == "EXACT_CONTROL_EVENT_DEFAULT_OFF_SCORE_EMITTED":
        observation_status = "EXACT_CONTROL_EVENT_IMPLEMENTATION_SCORE_OBSERVATION"
        observation_family = "DEFAULT_OFF_SCORER_EVENT"
        observation_action = "observe_default_off_score_emission_on_event"
    elif status == "EXACT_CONTROL_EVENT_REDESIGN_ALIGNMENT_SIGNAL_EMITTED":
        observation_status = "EXACT_CONTROL_EVENT_IMPLEMENTATION_REDESIGN_SIGNAL_OBSERVATION"
        observation_family = "REDESIGN_ALIGNMENT_SIGNAL_EVENT"
        observation_action = "observe_alignment_signal_for_redesign_event"
    else:
        observation_status = "EXACT_CONTROL_EVENT_IMPLEMENTATION_DENOMINATOR_CONTEXT_OBSERVATION"
        observation_family = "DENOMINATOR_CONTROL_CONTEXT_EVENT"
        observation_action = "preserve_denominator_context_event"
    return {
        **_common(event_row),
        "input_event_score_row_id": event_row.get("exact_control_event_score_row_id"),
        "input_denominator_event_row_id": event_row.get("input_denominator_event_row_id"),
        "input_scope_construction_row_id": event_row.get("input_scope_construction_row_id"),
        "bar_open_utc": event_row.get("bar_open_utc"),
        "future_bar_open_utc": event_row.get("future_bar_open_utc"),
        "primitive_present": bool(event_row.get("primitive_present")),
        "exact_control_event_implementation_status": observation_status,
        "implementation_observation_family": observation_family,
        "implementation_observation_action": observation_action,
        "default_off_exact_control_event_score": event_row.get("default_off_exact_control_event_score"),
        "redesign_alignment_signal": event_row.get("redesign_alignment_signal"),
        "redesign_family": event_row.get("redesign_family"),
        "future_change_per_current_range": event_row.get("future_change_per_current_range"),
        "delta_aligned_with_future": event_row.get("delta_aligned_with_future"),
        "candidate_use_allowed_now": False,
    }


def exact_control_code_path_spec(candidate_row: dict[str, Any], path_index: int) -> dict[str, Any]:
    family = str(candidate_row.get("implementation_candidate_family") or "EXACT_CONTROL_CONTEXT")
    if family == "EXACT_CONTROL_DEFAULT_OFF_SCORER":
        code_path_status = "EXACT_CONTROL_CODE_PATH_DEFAULT_OFF_SCORER_SPEC"
        module_slot = "branch_local_exact_control_default_off_scorer_registry"
        required_guard = "exact_scope_match_and_primitive_present"
    elif family == "EXACT_CONTROL_SPLIT_REDESIGN":
        code_path_status = "EXACT_CONTROL_CODE_PATH_SPLIT_REDESIGN_SPEC"
        module_slot = "branch_local_exact_control_redesign_router"
        required_guard = "exact_scope_match_and_redesign_family"
    else:
        code_path_status = "EXACT_CONTROL_CODE_PATH_RECHECK_SPEC"
        module_slot = "branch_local_exact_control_recheck_queue"
        required_guard = "input_join_recheck"
    return {
        "exact_control_implementation_surface": EXACT_CONTROL_IMPLEMENTATION_SURFACE,
        "exact_control_code_path_spec_row_id": f"OHLC-GTOS-DENOM-EXACTCTRL-IMPL-CODEPATH-{path_index:05d}",
        "input_scope_runtime_spec_row_id": candidate_row.get("input_scope_runtime_spec_row_id"),
        "input_blocker_runtime_decision_row_id": candidate_row.get("input_blocker_runtime_decision_row_id"),
        "symbol": candidate_row.get("symbol"),
        "route_session": candidate_row.get("route_session"),
        "tick_session_bucket": candidate_row.get("tick_session_bucket"),
        "horizon_id": candidate_row.get("horizon_id"),
        "primitive_flag": candidate_row.get("primitive_flag"),
        "mechanical_scope_key": candidate_row.get("mechanical_scope_key"),
        "code_path_status": code_path_status,
        "implementation_candidate_family": family,
        "module_slot": module_slot,
        "required_guard": required_guard,
        "mechanical_rule_expression": candidate_row.get("mechanical_rule_expression"),
        "default_off_exact_control_score": candidate_row.get("default_off_exact_control_score"),
        "redesign_family": candidate_row.get("redesign_family"),
        "candidate_use_allowed_now": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
