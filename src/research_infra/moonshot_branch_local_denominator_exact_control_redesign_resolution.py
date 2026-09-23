"""Resolve exact-control split/redesign runtime rows into concrete decisions."""

from __future__ import annotations

from statistics import mean
from typing import Any


EXACT_CONTROL_REDESIGN_RESOLUTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_redesign_resolution.py"
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


def mechanism_key(row: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("primitive_flag"))


def horizon_number(horizon_id: Any) -> int | None:
    text = str(horizon_id or "")
    if text.startswith("h"):
        try:
            return int(text[1:])
        except ValueError:
            return None
    return None


def _mean(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None


def _alignment_rate(rows: list[dict[str, Any]]) -> float | None:
    values = [bool(row.get("delta_aligned_with_future")) for row in rows if row.get("delta_aligned_with_future") is not None]
    if not values:
        return None
    return round(sum(1 for value in values if value) / len(values), 6)


def _common(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "exact_control_redesign_resolution_surface": EXACT_CONTROL_REDESIGN_RESOLUTION_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "tick_session_bucket": row.get("tick_session_bucket"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }


def redesign_scope_resolution(
    effective_scope_row: dict[str, Any],
    event_rows_for_scope: list[dict[str, Any]],
    all_effective_scope_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    flagged = [row for row in event_rows_for_scope if row.get("primitive_present")]
    controls = [row for row in event_rows_for_scope if not row.get("primitive_present")]
    flagged_future = [to_float(row.get("future_change_per_current_range")) for row in flagged]
    control_future = [to_float(row.get("future_change_per_current_range")) for row in controls]
    flagged_future_values = [value for value in flagged_future if value is not None]
    control_future_values = [value for value in control_future if value is not None]
    flagged_mean = _mean(flagged_future_values)
    control_mean = _mean(control_future_values)
    target_delta = round(flagged_mean - control_mean, 6) if flagged_mean is not None and control_mean is not None else None
    flagged_alignment = _alignment_rate(flagged)
    control_alignment = _alignment_rate(controls)
    alignment_delta = (
        round(flagged_alignment - control_alignment, 6)
        if flagged_alignment is not None and control_alignment is not None
        else None
    )
    family = effective_scope_row.get("redesign_family")
    current_horizon = horizon_number(effective_scope_row.get("horizon_id"))
    transfer_candidates = []
    for candidate in all_effective_scope_rows:
        if mechanism_key(candidate) != mechanism_key(effective_scope_row):
            continue
        if candidate.get("effective_runtime_family") != "DEFAULT_OFF_SCORER":
            continue
        candidate_horizon = horizon_number(candidate.get("horizon_id"))
        if current_horizon is not None and candidate_horizon is not None and candidate_horizon >= current_horizon:
            continue
        score = to_float(candidate.get("default_off_exact_control_score"))
        if score is not None:
            transfer_candidates.append((score, candidate_horizon or 0, candidate))
    transfer_candidates.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    best_transfer = transfer_candidates[0][2] if transfer_candidates else {}
    best_transfer_score = to_float(best_transfer.get("default_off_exact_control_score"))
    if best_transfer:
        transfer_status = "REDESIGN_RESOLUTION_HORIZON_TRANSFER_DEFAULT_OFF_SCORER_AVAILABLE"
    else:
        transfer_status = "REDESIGN_RESOLUTION_NO_SHORTER_POSITIVE_HORIZON_TRANSFER"

    if family == "REDESIGN_DIRECTIONAL_FEATURE_DROP_TARGET_MAGNITUDE_SCALAR" and (alignment_delta or 0) > 0:
        decision = "REDESIGN_RESOLVE_DIRECTIONAL_CONTEXT_FEATURE_DROP_TARGET_SCALAR"
        action = "implement_directional_alignment_context_feature_default_off"
    elif best_transfer_score is not None and best_transfer_score > 0:
        decision = "REDESIGN_RESOLVE_SWITCH_TO_SHORTER_HORIZON_DEFAULT_OFF_SCORER"
        action = "route_to_shorter_horizon_exact_control_default_off_scorer"
    elif family == "REDESIGN_TIGHTEN_TARGET_OR_SHORTER_HORIZON" and (target_delta or 0) >= -0.05 and (alignment_delta or 0) > 0:
        decision = "REDESIGN_RESOLVE_TIGHTEN_TARGET_STRESS_FIRST"
        action = "stress_tighter_target_or_shorter_horizon_before_scalar_use"
    else:
        decision = "REDESIGN_RESOLVE_ENTRY_GEOMETRY_OR_AVOID_INVERSE_SPLIT"
        action = "split_entry_geometry_or_convert_to_avoid_inverse_context"

    return {
        **_common(effective_scope_row),
        "input_effective_scope_registration_row_id": effective_scope_row.get("exact_control_effective_scope_registration_row_id"),
        "redesign_family": family,
        "flagged_event_rows": len(flagged),
        "control_event_rows": len(controls),
        "flagged_mean_future_change_per_current_range": flagged_mean,
        "control_mean_future_change_per_current_range": control_mean,
        "redesign_exact_target_delta": target_delta,
        "flagged_alignment_rate": flagged_alignment,
        "control_alignment_rate": control_alignment,
        "redesign_alignment_delta": alignment_delta,
        "horizon_transfer_status": transfer_status,
        "transfer_target_horizon_id": best_transfer.get("horizon_id"),
        "transfer_target_score": best_transfer_score,
        "redesign_resolution_decision": decision,
        "redesign_resolution_action": action,
        "missed_opportunity_preserved": True,
        "underlying_mechanism_preserved_as": "redesign_or_directional_context_or_horizon_transfer_or_avoid_inverse_candidate",
    }


def redesign_blocker_resolution(
    blocker_row: dict[str, Any],
    scope_resolution_row: dict[str, Any],
) -> dict[str, Any]:
    return {
        **_common(blocker_row),
        "input_blocker_implementation_candidate_row_id": blocker_row.get(
            "exact_control_blocker_implementation_candidate_row_id"
        ),
        "input_effective_scope_registration_row_id": scope_resolution_row.get("input_effective_scope_registration_row_id"),
        "input_redesign_scope_resolution_row_id": scope_resolution_row.get("exact_control_redesign_scope_resolution_row_id"),
        "redesign_family": blocker_row.get("redesign_family"),
        "redesign_resolution_decision": scope_resolution_row.get("redesign_resolution_decision"),
        "redesign_resolution_action": scope_resolution_row.get("redesign_resolution_action"),
        "transfer_target_horizon_id": scope_resolution_row.get("transfer_target_horizon_id"),
        "transfer_target_score": scope_resolution_row.get("transfer_target_score"),
        "redesign_alignment_delta": scope_resolution_row.get("redesign_alignment_delta"),
        "redesign_exact_target_delta": scope_resolution_row.get("redesign_exact_target_delta"),
        "missed_opportunity_preserved": True,
        "candidate_use_allowed_now": False,
    }


def redesign_event_signal_resolution(
    event_row: dict[str, Any],
    scope_resolution_row: dict[str, Any],
) -> dict[str, Any]:
    return {
        **_common(event_row),
        "input_event_runtime_routing_row_id": event_row.get("exact_control_event_runtime_routing_row_id"),
        "input_redesign_scope_resolution_row_id": scope_resolution_row.get("exact_control_redesign_scope_resolution_row_id"),
        "runtime_redesign_alignment_signal": event_row.get("runtime_redesign_alignment_signal"),
        "redesign_family": event_row.get("redesign_family"),
        "redesign_event_resolution_status": "REDESIGN_EVENT_SIGNAL_CONSUMED_IN_SCOPE_DECISION",
        "redesign_resolution_decision": scope_resolution_row.get("redesign_resolution_decision"),
        "redesign_resolution_action": scope_resolution_row.get("redesign_resolution_action"),
        "future_change_per_current_range": event_row.get("future_change_per_current_range"),
        "delta_aligned_with_future": event_row.get("delta_aligned_with_future"),
        "candidate_use_allowed_now": False,
    }
