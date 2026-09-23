"""Materialize exact-control redesign-resolution decisions into module slots."""

from __future__ import annotations

from typing import Any


EXACT_CONTROL_REDESIGN_MODULE_INTEGRATION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_redesign_module_integration.py"
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


def _common(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "exact_control_redesign_module_integration_surface": EXACT_CONTROL_REDESIGN_MODULE_INTEGRATION_SURFACE,
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


def module_slot_for_decision(decision: Any) -> tuple[str, str, str, list[str], str]:
    if decision == "REDESIGN_RESOLVE_DIRECTIONAL_CONTEXT_FEATURE_DROP_TARGET_SCALAR":
        return (
            "REDESIGN_MODULE_REGISTER_DIRECTIONAL_CONTEXT_FEATURE",
            "branch_local_exact_control_directional_context_feature",
            "exact_scope_match_and_alignment_delta_positive",
            ["symbol", "route_session", "horizon_id", "primitive_flag", "primitive_present", "delta_aligned_with_future"],
            "register_directional_alignment_context_feature_without_target_delta_scalar",
        )
    if decision == "REDESIGN_RESOLVE_SWITCH_TO_SHORTER_HORIZON_DEFAULT_OFF_SCORER":
        return (
            "REDESIGN_MODULE_REGISTER_SHORTER_HORIZON_TRANSFER",
            "branch_local_exact_control_shorter_horizon_transfer_router",
            "exact_scope_match_and_transfer_target_horizon_available",
            ["symbol", "route_session", "primitive_flag", "primitive_present", "transfer_target_horizon_id"],
            "route_scope_to_shorter_horizon_default_off_scorer_without_live_effect",
        )
    if decision == "REDESIGN_RESOLVE_TIGHTEN_TARGET_STRESS_FIRST":
        return (
            "REDESIGN_MODULE_REGISTER_TIGHTER_TARGET_STRESS",
            "branch_local_exact_control_tighter_target_stress_tester",
            "exact_scope_match_and_target_delta_near_zero_alignment_positive",
            ["symbol", "route_session", "horizon_id", "primitive_flag", "primitive_present", "future_change_per_current_range"],
            "register_tighter_target_or_shorter_horizon_stress_before_scalar_use",
        )
    return (
        "REDESIGN_MODULE_REGISTER_ENTRY_AVOID_INVERSE_SPLIT",
        "branch_local_exact_control_entry_avoid_inverse_splitter",
        "exact_scope_match_and_entry_geometry_or_avoid_inverse_required",
        ["symbol", "route_session", "horizon_id", "primitive_flag", "primitive_present", "delta_aligned_with_future"],
        "register_entry_geometry_or_avoid_inverse_split_without_claim_deletion",
    )


def redesign_scope_module_integration(scope_resolution_row: dict[str, Any]) -> dict[str, Any]:
    status, module_slot, guard, required_fields, action = module_slot_for_decision(
        scope_resolution_row.get("redesign_resolution_decision")
    )
    expression = (
        f"if {mechanical_scope_key(scope_resolution_row)} and primitive_present then {action}; "
        "preserve mechanism intelligence and keep runtime default-off"
    )
    return {
        **_common(scope_resolution_row),
        "input_redesign_scope_resolution_row_id": scope_resolution_row.get(
            "exact_control_redesign_scope_resolution_row_id"
        ),
        "input_effective_scope_registration_row_id": scope_resolution_row.get(
            "input_effective_scope_registration_row_id"
        ),
        "redesign_resolution_decision": scope_resolution_row.get("redesign_resolution_decision"),
        "redesign_resolution_action": scope_resolution_row.get("redesign_resolution_action"),
        "redesign_family": scope_resolution_row.get("redesign_family"),
        "redesign_module_integration_status": status,
        "module_slot": module_slot,
        "required_guard": guard,
        "required_runtime_fields": required_fields,
        "mechanical_rule_expression": expression,
        "transfer_target_horizon_id": scope_resolution_row.get("transfer_target_horizon_id"),
        "transfer_target_score": scope_resolution_row.get("transfer_target_score"),
        "redesign_alignment_delta": scope_resolution_row.get("redesign_alignment_delta"),
        "redesign_exact_target_delta": scope_resolution_row.get("redesign_exact_target_delta"),
        "module_integration_action": action,
        "missed_opportunity_preserved": True,
        "underlying_mechanism_preserved_as": scope_resolution_row.get("underlying_mechanism_preserved_as"),
    }


def redesign_blocker_module_integration(
    blocker_resolution_row: dict[str, Any],
    scope_module_row: dict[str, Any],
) -> dict[str, Any]:
    return {
        **_common(blocker_resolution_row),
        "input_redesign_blocker_resolution_row_id": blocker_resolution_row.get(
            "exact_control_redesign_blocker_resolution_row_id"
        ),
        "input_blocker_implementation_candidate_row_id": blocker_resolution_row.get(
            "input_blocker_implementation_candidate_row_id"
        ),
        "input_scope_module_integration_row_id": scope_module_row.get(
            "exact_control_redesign_scope_module_integration_row_id"
        ),
        "module_slot": scope_module_row.get("module_slot"),
        "required_guard": scope_module_row.get("required_guard"),
        "redesign_resolution_decision": blocker_resolution_row.get("redesign_resolution_decision"),
        "redesign_module_integration_status": scope_module_row.get("redesign_module_integration_status"),
        "module_integration_action": scope_module_row.get("module_integration_action"),
        "transfer_target_horizon_id": blocker_resolution_row.get("transfer_target_horizon_id"),
        "transfer_target_score": blocker_resolution_row.get("transfer_target_score"),
        "redesign_alignment_delta": blocker_resolution_row.get("redesign_alignment_delta"),
        "redesign_exact_target_delta": blocker_resolution_row.get("redesign_exact_target_delta"),
        "missed_opportunity_preserved": True,
    }


def redesign_event_module_observation(
    event_resolution_row: dict[str, Any],
    scope_module_row: dict[str, Any],
) -> dict[str, Any]:
    return {
        **_common(event_resolution_row),
        "input_redesign_event_signal_resolution_row_id": event_resolution_row.get(
            "exact_control_redesign_event_signal_resolution_row_id"
        ),
        "input_event_runtime_routing_row_id": event_resolution_row.get("input_event_runtime_routing_row_id"),
        "input_scope_module_integration_row_id": scope_module_row.get(
            "exact_control_redesign_scope_module_integration_row_id"
        ),
        "module_slot": scope_module_row.get("module_slot"),
        "required_guard": scope_module_row.get("required_guard"),
        "event_module_observation_status": "REDESIGN_EVENT_CONSUMED_BY_BRANCH_LOCAL_MODULE_SLOT",
        "event_module_observation_action": scope_module_row.get("module_integration_action"),
        "redesign_resolution_decision": event_resolution_row.get("redesign_resolution_decision"),
        "redesign_family": event_resolution_row.get("redesign_family"),
        "runtime_redesign_alignment_signal": event_resolution_row.get("runtime_redesign_alignment_signal"),
        "future_change_per_current_range": event_resolution_row.get("future_change_per_current_range"),
        "delta_aligned_with_future": event_resolution_row.get("delta_aligned_with_future"),
    }


def redesign_code_surface_registration(scope_module_row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        **_common(scope_module_row),
        "exact_control_redesign_code_surface_registration_row_id": (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-MODULE-CODE-{index:04d}"
        ),
        "input_scope_module_integration_row_id": scope_module_row.get(
            "exact_control_redesign_scope_module_integration_row_id"
        ),
        "module_slot": scope_module_row.get("module_slot"),
        "required_guard": scope_module_row.get("required_guard"),
        "required_runtime_fields": scope_module_row.get("required_runtime_fields"),
        "redesign_module_integration_status": scope_module_row.get("redesign_module_integration_status"),
        "redesign_resolution_decision": scope_module_row.get("redesign_resolution_decision"),
        "mechanical_rule_expression": scope_module_row.get("mechanical_rule_expression"),
        "code_surface_status": "REDESIGN_MODULE_CODE_SURFACE_REGISTERED_DEFAULT_OFF",
        "code_surface_action": "materialize_branch_local_module_slot_for_next_execution_layer",
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
