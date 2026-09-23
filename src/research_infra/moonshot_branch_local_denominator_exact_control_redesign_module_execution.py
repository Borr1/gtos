"""Execute exact-control redesign module slots against runtime event denominators."""

from __future__ import annotations

from statistics import mean
from typing import Any


EXACT_CONTROL_REDESIGN_MODULE_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_redesign_module_execution.py"
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


def _mean(values: list[float]) -> float | None:
    return round(mean(values), 6) if values else None


def _alignment_rate(rows: list[dict[str, Any]]) -> float | None:
    values = [bool(row.get("delta_aligned_with_future")) for row in rows if row.get("delta_aligned_with_future") is not None]
    if not values:
        return None
    return round(sum(1 for value in values if value) / len(values), 6)


def _common(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "exact_control_redesign_module_execution_surface": EXACT_CONTROL_REDESIGN_MODULE_EXECUTION_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "tick_session_bucket": row.get("tick_session_bucket"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "mechanical_scope_key": mechanical_scope_key(row),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }


def module_signal_status(module_slot: Any) -> tuple[str, str]:
    if module_slot == "branch_local_exact_control_directional_context_feature":
        return (
            "REDESIGN_MODULE_EXECUTION_DIRECTIONAL_CONTEXT_SIGNAL",
            "emit_directional_context_feature_observation_without_target_delta_scalar",
        )
    if module_slot == "branch_local_exact_control_shorter_horizon_transfer_router":
        return (
            "REDESIGN_MODULE_EXECUTION_SHORTER_HORIZON_TRANSFER_SIGNAL",
            "route_signal_to_shorter_horizon_transfer_observation",
        )
    if module_slot == "branch_local_exact_control_tighter_target_stress_tester":
        return (
            "REDESIGN_MODULE_EXECUTION_TIGHTER_TARGET_STRESS_SIGNAL",
            "emit_tighter_target_stress_observation_before_scalar_use",
        )
    return (
        "REDESIGN_MODULE_EXECUTION_ENTRY_AVOID_INVERSE_SIGNAL",
        "emit_entry_geometry_or_avoid_inverse_split_observation",
    )


def redesign_scope_module_execution(
    scope_module_row: dict[str, Any],
    runtime_events_for_scope: list[dict[str, Any]],
) -> dict[str, Any]:
    flagged = [row for row in runtime_events_for_scope if row.get("primitive_present")]
    controls = [row for row in runtime_events_for_scope if not row.get("primitive_present")]
    flagged_values = [
        value for row in flagged if (value := to_float(row.get("future_change_per_current_range"))) is not None
    ]
    control_values = [
        value for row in controls if (value := to_float(row.get("future_change_per_current_range"))) is not None
    ]
    flagged_mean = _mean(flagged_values)
    control_mean = _mean(control_values)
    target_delta = round(flagged_mean - control_mean, 6) if flagged_mean is not None and control_mean is not None else None
    flagged_alignment = _alignment_rate(flagged)
    control_alignment = _alignment_rate(controls)
    alignment_delta = (
        round(flagged_alignment - control_alignment, 6)
        if flagged_alignment is not None and control_alignment is not None
        else None
    )
    slot = scope_module_row.get("module_slot")
    if slot == "branch_local_exact_control_shorter_horizon_transfer_router":
        status = "REDESIGN_MODULE_SCOPE_EXECUTE_SHORTER_HORIZON_TRANSFER"
        action = "execute_shorter_horizon_transfer_observation"
    elif slot == "branch_local_exact_control_directional_context_feature":
        status = "REDESIGN_MODULE_SCOPE_EXECUTE_DIRECTIONAL_CONTEXT_FEATURE"
        action = "execute_directional_context_feature_observation"
    elif slot == "branch_local_exact_control_tighter_target_stress_tester":
        status = "REDESIGN_MODULE_SCOPE_EXECUTE_TIGHTER_TARGET_STRESS"
        action = "execute_tighter_target_stress_observation"
    else:
        status = "REDESIGN_MODULE_SCOPE_EXECUTE_ENTRY_AVOID_INVERSE_SPLIT"
        action = "execute_entry_geometry_or_avoid_inverse_observation"
    return {
        **_common(scope_module_row),
        "input_scope_module_integration_row_id": scope_module_row.get(
            "exact_control_redesign_scope_module_integration_row_id"
        ),
        "module_slot": slot,
        "required_guard": scope_module_row.get("required_guard"),
        "redesign_resolution_decision": scope_module_row.get("redesign_resolution_decision"),
        "module_execution_status": status,
        "module_execution_action": action,
        "module_scope_event_rows": len(runtime_events_for_scope),
        "module_scope_signal_event_rows": len(flagged),
        "module_scope_control_event_rows": len(controls),
        "signal_mean_future_change_per_current_range": flagged_mean,
        "control_mean_future_change_per_current_range": control_mean,
        "module_execution_target_delta": target_delta,
        "signal_alignment_rate": flagged_alignment,
        "control_alignment_rate": control_alignment,
        "module_execution_alignment_delta": alignment_delta,
        "transfer_target_horizon_id": scope_module_row.get("transfer_target_horizon_id"),
        "transfer_target_score": scope_module_row.get("transfer_target_score"),
        "missed_opportunity_preserved": True,
    }


def redesign_event_module_execution(
    runtime_event_row: dict[str, Any],
    scope_execution_row: dict[str, Any] | None,
) -> dict[str, Any]:
    scope_execution = scope_execution_row or {}
    module_slot = scope_execution.get("module_slot")
    primitive_present = bool(runtime_event_row.get("primitive_present"))
    if module_slot and primitive_present:
        status, action = module_signal_status(module_slot)
        module_scope_relation = "MODULE_SCOPE_SIGNAL_EVENT"
    elif module_slot:
        status = "REDESIGN_MODULE_EXECUTION_MODULE_SCOPE_CONTROL_CONTEXT"
        action = "preserve_same_scope_control_event_for_module_delta"
        module_scope_relation = "MODULE_SCOPE_CONTROL_EVENT"
    else:
        status = "REDESIGN_MODULE_EXECUTION_NON_MODULE_SCOPE_CONTEXT"
        action = "preserve_non_module_runtime_context_event"
        module_scope_relation = "NON_MODULE_SCOPE_CONTEXT_EVENT"
    return {
        **_common(runtime_event_row),
        "input_event_runtime_routing_row_id": runtime_event_row.get("exact_control_event_runtime_routing_row_id"),
        "input_scope_module_execution_row_id": scope_execution.get("exact_control_redesign_scope_module_execution_row_id"),
        "module_slot": module_slot,
        "module_scope_relation": module_scope_relation,
        "event_module_execution_status": status,
        "event_module_execution_action": action,
        "primitive_present": primitive_present,
        "runtime_redesign_alignment_signal": runtime_event_row.get("runtime_redesign_alignment_signal"),
        "future_change_per_current_range": runtime_event_row.get("future_change_per_current_range"),
        "delta_aligned_with_future": runtime_event_row.get("delta_aligned_with_future"),
        "runtime_event_routing_status": runtime_event_row.get("runtime_event_routing_status"),
    }


def redesign_code_surface_execution(
    code_surface_row: dict[str, Any],
    scope_execution_row: dict[str, Any],
) -> dict[str, Any]:
    return {
        **_common(code_surface_row),
        "input_code_surface_registration_row_id": code_surface_row.get(
            "exact_control_redesign_code_surface_registration_row_id"
        ),
        "input_scope_module_execution_row_id": scope_execution_row.get(
            "exact_control_redesign_scope_module_execution_row_id"
        ),
        "module_slot": code_surface_row.get("module_slot"),
        "required_guard": code_surface_row.get("required_guard"),
        "code_surface_execution_status": "REDESIGN_MODULE_CODE_SURFACE_EXECUTED_DEFAULT_OFF_OBSERVATION",
        "code_surface_execution_action": scope_execution_row.get("module_execution_action"),
        "module_scope_signal_event_rows": scope_execution_row.get("module_scope_signal_event_rows"),
        "module_scope_control_event_rows": scope_execution_row.get("module_scope_control_event_rows"),
        "module_execution_target_delta": scope_execution_row.get("module_execution_target_delta"),
        "module_execution_alignment_delta": scope_execution_row.get("module_execution_alignment_delta"),
    }
