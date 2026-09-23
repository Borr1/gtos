"""Materialize final default-off registry rows from redesign module deltas."""

from __future__ import annotations

from typing import Any


EXACT_CONTROL_REDESIGN_FINAL_REGISTRY_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_redesign_final_registry.py"
)


def scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))


def mechanical_scope_key(row: dict[str, Any]) -> str:
    return (
        f"symbol={row.get('symbol')}|session={row.get('route_session')}|"
        f"horizon={row.get('horizon_id')}|primitive={row.get('primitive_flag')}"
    )


def _common(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "exact_control_redesign_final_registry_surface": EXACT_CONTROL_REDESIGN_FINAL_REGISTRY_SURFACE,
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


def _registry_status(candidate_class: Any) -> tuple[str, str, str]:
    if candidate_class == "FINAL_REGISTRY_CANDIDATE_DIRECTIONAL_CONTEXT_FEATURE":
        return (
            "FINAL_RED_REGISTRY_DIRECTIONAL_CONTEXT_FEATURE_DEFAULT_OFF",
            "emit_directional_context_feature_no_target_scalar",
            "directional_context_feature_drop_target_scalar",
        )
    if candidate_class == "FINAL_REGISTRY_CANDIDATE_SHORTER_HORIZON_TRANSFER":
        return (
            "FINAL_RED_REGISTRY_SHORTER_HORIZON_TRANSFER_DEFAULT_OFF",
            "route_to_shorter_horizon_default_off_transfer_candidate",
            "shorter_horizon_transfer_default_off",
        )
    if candidate_class == "FINAL_REGISTRY_CANDIDATE_TIGHTER_TARGET_STRESS":
        return (
            "FINAL_RED_REGISTRY_TIGHTER_TARGET_STRESS_DEFAULT_OFF",
            "stress_tighter_target_before_any_scalar_use",
            "tighter_target_stress_default_off",
        )
    return (
        "FINAL_RED_REGISTRY_ENTRY_AVOID_INVERSE_SPLIT_DEFAULT_OFF",
        "split_entry_geometry_or_avoid_inverse_before_any_scalar_use",
        "entry_geometry_or_avoid_inverse_split_default_off",
    )


def final_registry_row(
    registry_candidate_row: dict[str, Any],
    scope_comparison_row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    candidate_class = registry_candidate_row.get("registry_candidate_class")
    status, action, implementation_family = _registry_status(candidate_class)
    return {
        **_common(registry_candidate_row),
        "exact_control_redesign_final_registry_row_id": (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-FINAL-REGISTRY-{index:04d}"
        ),
        "input_registry_candidate_row_id": registry_candidate_row.get(
            "exact_control_redesign_registry_candidate_row_id"
        ),
        "input_scope_module_delta_comparison_row_id": registry_candidate_row.get(
            "input_scope_module_delta_comparison_row_id"
        ),
        "module_slot": registry_candidate_row.get("module_slot"),
        "module_delta_comparator_decision": registry_candidate_row.get("module_delta_comparator_decision"),
        "registry_candidate_class": candidate_class,
        "final_registry_status": status,
        "final_registry_action": action,
        "implementation_family": implementation_family,
        "exact_scope_guard": "symbol_session_horizon_primitive_match",
        "event_application_guard": "exact_scope_match_preserve_signal_control_context",
        "target_delta_use": registry_candidate_row.get("target_delta_use"),
        "module_execution_target_delta": registry_candidate_row.get("module_execution_target_delta"),
        "module_execution_alignment_delta": registry_candidate_row.get("module_execution_alignment_delta"),
        "same_mechanism_default_off_candidate_count": scope_comparison_row.get(
            "same_mechanism_default_off_candidate_count"
        ),
        "same_mechanism_shorter_default_off_candidate_count": scope_comparison_row.get(
            "same_mechanism_shorter_default_off_candidate_count"
        ),
        "best_default_off_horizon_id": scope_comparison_row.get("best_default_off_horizon_id"),
        "best_default_off_score": scope_comparison_row.get("best_default_off_score"),
        "best_shorter_default_off_horizon_id": scope_comparison_row.get("best_shorter_default_off_horizon_id"),
        "best_shorter_default_off_score": scope_comparison_row.get("best_shorter_default_off_score"),
        "transfer_target_horizon_id": scope_comparison_row.get("transfer_target_horizon_id"),
        "transfer_target_score": scope_comparison_row.get("transfer_target_score"),
        "missed_opportunity_preserved": True,
        "underlying_mechanism_preserved_as": implementation_family,
    }


def final_registry_code_spec(final_registry: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        **_common(final_registry),
        "exact_control_redesign_final_registry_code_spec_row_id": (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-FINAL-CODE-SPEC-{index:04d}"
        ),
        "input_final_registry_row_id": final_registry.get("exact_control_redesign_final_registry_row_id"),
        "module_slot": final_registry.get("module_slot"),
        "registry_candidate_class": final_registry.get("registry_candidate_class"),
        "final_registry_status": final_registry.get("final_registry_status"),
        "code_spec_status": "FINAL_RED_REGISTRY_CODE_SPEC_DEFAULT_OFF_EXACT_SCOPE",
        "code_spec_action": "materialize_exact_scope_default_off_registry_spec",
        "implementation_family": final_registry.get("implementation_family"),
        "exact_scope_guard": final_registry.get("exact_scope_guard"),
        "event_application_guard": final_registry.get("event_application_guard"),
        "target_delta_use": final_registry.get("target_delta_use"),
        "mechanical_rule_expression": (
            "when symbol/session/horizon/primitive match, preserve signal/control/context observation for "
            f"{final_registry.get('implementation_family')} with target_delta scalar disabled"
        ),
        "required_runtime_fields": [
            "symbol",
            "route_session",
            "horizon_id",
            "primitive_flag",
            "module_scope_relation",
            "future_change_per_current_range",
            "delta_aligned_with_future",
        ],
    }


def final_registry_event_application(
    event_comparison_row: dict[str, Any],
    final_registry: dict[str, Any] | None,
) -> dict[str, Any]:
    registry = final_registry or {}
    module_scope_relation = event_comparison_row.get("module_scope_relation")
    candidate_class = registry.get("registry_candidate_class")
    if registry and module_scope_relation == "MODULE_SCOPE_SIGNAL_EVENT":
        if candidate_class == "FINAL_REGISTRY_CANDIDATE_DIRECTIONAL_CONTEXT_FEATURE":
            status = "FINAL_RED_REGISTRY_EVENT_DIRECTIONAL_CONTEXT_SIGNAL"
        elif candidate_class == "FINAL_REGISTRY_CANDIDATE_SHORTER_HORIZON_TRANSFER":
            status = "FINAL_RED_REGISTRY_EVENT_SHORTER_HORIZON_TRANSFER_SIGNAL"
        elif candidate_class == "FINAL_REGISTRY_CANDIDATE_TIGHTER_TARGET_STRESS":
            status = "FINAL_RED_REGISTRY_EVENT_TIGHTER_TARGET_STRESS_SIGNAL"
        else:
            status = "FINAL_RED_REGISTRY_EVENT_ENTRY_AVOID_INVERSE_SIGNAL"
        action = "preserve_default_off_redesign_signal_observation"
    elif registry and module_scope_relation == "MODULE_SCOPE_CONTROL_EVENT":
        status = "FINAL_RED_REGISTRY_EVENT_SAME_SCOPE_CONTROL_CONTEXT"
        action = "preserve_same_scope_control_context"
    else:
        status = "FINAL_RED_REGISTRY_EVENT_NON_SCOPE_CONTEXT"
        action = "preserve_non_scope_denominator_context"
    join_state = (
        "FINAL_RED_REGISTRY_EVENT_JOINED_EXACT_SCOPE"
        if registry
        else "FINAL_RED_REGISTRY_EVENT_NO_EXACT_SCOPE_CONTEXT"
    )
    return {
        **_common(event_comparison_row),
        "input_event_module_delta_comparison_row_id": event_comparison_row.get(
            "exact_control_redesign_event_module_delta_comparison_row_id"
        ),
        "input_final_registry_row_id": registry.get("exact_control_redesign_final_registry_row_id"),
        "final_registry_event_join_state": join_state,
        "module_slot": event_comparison_row.get("module_slot"),
        "module_scope_relation": module_scope_relation,
        "registry_candidate_class": candidate_class,
        "final_registry_status": registry.get("final_registry_status"),
        "event_final_registry_application_status": status,
        "event_final_registry_application_action": action,
        "future_change_per_current_range": event_comparison_row.get("future_change_per_current_range"),
        "delta_aligned_with_future": event_comparison_row.get("delta_aligned_with_future"),
        "runtime_redesign_alignment_signal": event_comparison_row.get("runtime_redesign_alignment_signal"),
        "target_delta_use": registry.get("target_delta_use"),
    }
