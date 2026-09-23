"""Branch-local scorer modules for exact-control redesign final registry rows."""

from __future__ import annotations

from typing import Any


EXACT_CONTROL_REDESIGN_REGISTRY_SCORER_MODULE_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_redesign_registry_scorer_modules.py"
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
        "exact_control_redesign_registry_scorer_module_surface": (
            EXACT_CONTROL_REDESIGN_REGISTRY_SCORER_MODULE_SURFACE
        ),
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


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _rate(true_count: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(true_count / denominator, 6)


def _delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 6)


def _module_status_and_action(implementation_family: Any) -> tuple[str, str, str, str]:
    if implementation_family == "directional_context_feature_drop_target_scalar":
        return (
            "REGISTRY_SCORER_MODULE_DIRECTIONAL_CONTEXT_FEATURE_DEFAULT_OFF_EXACT_SCOPE",
            "emit_directional_context_feature_without_target_delta_scalar",
            "branch_local_directional_context_feature_scorer_module",
            "score_directional_context_feature_default_off",
        )
    if implementation_family == "shorter_horizon_transfer_default_off":
        return (
            "REGISTRY_SCORER_MODULE_SHORTER_HORIZON_TRANSFER_DEFAULT_OFF_EXACT_SCOPE",
            "route_shorter_horizon_transfer_candidate_without_target_delta_scalar",
            "branch_local_shorter_horizon_transfer_router_module",
            "route_shorter_horizon_transfer_default_off",
        )
    if implementation_family == "tighter_target_stress_default_off":
        return (
            "REGISTRY_SCORER_MODULE_TIGHTER_TARGET_STRESS_DEFAULT_OFF_EXACT_SCOPE",
            "stress_tighter_target_before_any_runtime_score",
            "branch_local_tighter_target_stress_module",
            "stress_tighter_target_before_scalar_use",
        )
    return (
        "REGISTRY_SCORER_MODULE_ENTRY_AVOID_INVERSE_SPLIT_DEFAULT_OFF_EXACT_SCOPE",
        "split_entry_geometry_or_avoid_inverse_without_target_delta_scalar",
        "branch_local_entry_avoid_inverse_splitter_module",
        "split_entry_geometry_or_avoid_inverse_default_off",
    )


def event_signal_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in events
        if str(row.get("event_final_registry_application_status") or "").endswith("_SIGNAL")
    ]


def event_control_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in events
        if row.get("event_final_registry_application_status") == "FINAL_RED_REGISTRY_EVENT_SAME_SCOPE_CONTROL_CONTEXT"
    ]


def module_observation_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    signals = event_signal_rows(events)
    controls = event_control_rows(events)
    signal_future = [
        value
        for value in (to_float(row.get("future_change_per_current_range")) for row in signals)
        if value is not None
    ]
    control_future = [
        value
        for value in (to_float(row.get("future_change_per_current_range")) for row in controls)
        if value is not None
    ]
    signal_aligned = sum(1 for row in signals if bool(row.get("delta_aligned_with_future")))
    control_aligned = sum(1 for row in controls if bool(row.get("delta_aligned_with_future")))
    signal_alignment_rate = _rate(signal_aligned, len(signals))
    control_alignment_rate = _rate(control_aligned, len(controls))
    signal_future_mean = _mean(signal_future)
    control_future_mean = _mean(control_future)
    return {
        "exact_scope_event_rows": len(events),
        "signal_event_rows": len(signals),
        "same_scope_control_event_rows": len(controls),
        "signal_alignment_true_rows": signal_aligned,
        "control_alignment_true_rows": control_aligned,
        "signal_alignment_rate": signal_alignment_rate,
        "control_alignment_rate": control_alignment_rate,
        "alignment_rate_delta_signal_minus_control": _delta(signal_alignment_rate, control_alignment_rate),
        "signal_future_change_mean": signal_future_mean,
        "control_future_change_mean": control_future_mean,
        "future_change_mean_delta_signal_minus_control": _delta(signal_future_mean, control_future_mean),
    }


def scorer_module_registration(
    code_spec_row: dict[str, Any],
    final_registry_row: dict[str, Any],
    exact_scope_events: list[dict[str, Any]],
    index: int,
) -> dict[str, Any]:
    status, action, module_family, function_name = _module_status_and_action(
        final_registry_row.get("implementation_family")
    )
    metrics = module_observation_metrics(exact_scope_events)
    return {
        **_common(code_spec_row),
        "exact_control_redesign_registry_scorer_module_row_id": (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REGISTRY-SCORER-MODULE-{index:04d}"
        ),
        "input_final_registry_row_id": final_registry_row.get("exact_control_redesign_final_registry_row_id"),
        "input_code_spec_row_id": code_spec_row.get("exact_control_redesign_final_registry_code_spec_row_id"),
        "module_registration_status": status,
        "module_registration_action": action,
        "scorer_module_family": module_family,
        "candidate_function_name": function_name,
        "implementation_family": final_registry_row.get("implementation_family"),
        "final_registry_status": final_registry_row.get("final_registry_status"),
        "registry_candidate_class": final_registry_row.get("registry_candidate_class"),
        "module_slot": final_registry_row.get("module_slot"),
        "exact_scope_guard": code_spec_row.get("exact_scope_guard"),
        "event_application_guard": code_spec_row.get("event_application_guard"),
        "target_delta_use": final_registry_row.get("target_delta_use"),
        "target_delta_scalar_use_allowed": False,
        "module_runtime_score": None,
        "module_non_scalar_metric_family": "signal_vs_same_scope_control_alignment_and_future_change",
        "module_execution_target_delta": final_registry_row.get("module_execution_target_delta"),
        "module_execution_alignment_delta": final_registry_row.get("module_execution_alignment_delta"),
        "same_mechanism_default_off_candidate_count": final_registry_row.get(
            "same_mechanism_default_off_candidate_count"
        ),
        "same_mechanism_shorter_default_off_candidate_count": final_registry_row.get(
            "same_mechanism_shorter_default_off_candidate_count"
        ),
        "best_default_off_horizon_id": final_registry_row.get("best_default_off_horizon_id"),
        "best_default_off_score": final_registry_row.get("best_default_off_score"),
        "best_shorter_default_off_horizon_id": final_registry_row.get("best_shorter_default_off_horizon_id"),
        "best_shorter_default_off_score": final_registry_row.get("best_shorter_default_off_score"),
        "transfer_target_horizon_id": final_registry_row.get("transfer_target_horizon_id"),
        "transfer_target_score": final_registry_row.get("transfer_target_score"),
        "missed_opportunity_preserved": True,
        "underlying_mechanism_preserved_as": final_registry_row.get("underlying_mechanism_preserved_as"),
        **metrics,
    }


def scorer_module_event_application(
    event_application_row: dict[str, Any],
    module_registration_row: dict[str, Any] | None,
) -> dict[str, Any]:
    module = module_registration_row or {}
    status = event_application_row.get("event_final_registry_application_status")
    if module and str(status or "").endswith("_SIGNAL"):
        module_status = "REGISTRY_SCORER_MODULE_EVENT_SIGNAL_OBSERVATION"
        module_action = "apply_default_off_module_to_signal_observation_without_scalar_score"
        module_relation = "REGISTRY_SCORER_MODULE_SIGNAL"
    elif module and status == "FINAL_RED_REGISTRY_EVENT_SAME_SCOPE_CONTROL_CONTEXT":
        module_status = "REGISTRY_SCORER_MODULE_EVENT_SAME_SCOPE_CONTROL_CONTEXT"
        module_action = "preserve_same_scope_control_for_module_metric_denominator"
        module_relation = "REGISTRY_SCORER_MODULE_SAME_SCOPE_CONTROL"
    else:
        module_status = "REGISTRY_SCORER_MODULE_EVENT_NON_SCOPE_CONTEXT"
        module_action = "preserve_non_scope_context_outside_module_exact_scope"
        module_relation = "REGISTRY_SCORER_MODULE_NON_SCOPE_CONTEXT"
    return {
        **_common(event_application_row),
        "input_final_registry_event_application_row_id": event_application_row.get(
            "exact_control_redesign_final_registry_event_application_row_id"
        ),
        "input_registry_scorer_module_row_id": module.get(
            "exact_control_redesign_registry_scorer_module_row_id"
        ),
        "input_final_registry_row_id": event_application_row.get("input_final_registry_row_id"),
        "module_event_application_status": module_status,
        "module_event_application_action": module_action,
        "module_event_relation": module_relation,
        "module_registration_status": module.get("module_registration_status"),
        "scorer_module_family": module.get("scorer_module_family"),
        "implementation_family": module.get("implementation_family"),
        "final_registry_status": event_application_row.get("final_registry_status"),
        "registry_candidate_class": event_application_row.get("registry_candidate_class"),
        "module_slot": event_application_row.get("module_slot"),
        "module_scope_relation": event_application_row.get("module_scope_relation"),
        "final_registry_event_join_state": event_application_row.get("final_registry_event_join_state"),
        "future_change_per_current_range": event_application_row.get("future_change_per_current_range"),
        "delta_aligned_with_future": event_application_row.get("delta_aligned_with_future"),
        "runtime_redesign_alignment_signal": event_application_row.get("runtime_redesign_alignment_signal"),
        "target_delta_use": event_application_row.get("target_delta_use"),
        "target_delta_scalar_use_allowed": False,
        "module_runtime_score": None,
    }


def scorer_module_code_candidate(module_registration_row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        **_common(module_registration_row),
        "exact_control_redesign_registry_scorer_module_code_candidate_row_id": (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REGISTRY-SCORER-CODE-{index:04d}"
        ),
        "input_registry_scorer_module_row_id": module_registration_row.get(
            "exact_control_redesign_registry_scorer_module_row_id"
        ),
        "input_final_registry_row_id": module_registration_row.get("input_final_registry_row_id"),
        "input_code_spec_row_id": module_registration_row.get("input_code_spec_row_id"),
        "code_candidate_status": "REGISTRY_SCORER_MODULE_CODE_CANDIDATE_DEFAULT_OFF_EXACT_SCOPE",
        "code_candidate_action": "branch_local_implementation_candidate_default_off_module",
        "candidate_function_name": module_registration_row.get("candidate_function_name"),
        "scorer_module_family": module_registration_row.get("scorer_module_family"),
        "implementation_family": module_registration_row.get("implementation_family"),
        "exact_scope_guard": module_registration_row.get("exact_scope_guard"),
        "target_delta_scalar_use_allowed": False,
        "module_runtime_score_allowed": False,
        "required_runtime_fields": [
            "symbol",
            "route_session",
            "horizon_id",
            "primitive_flag",
            "future_change_per_current_range",
            "delta_aligned_with_future",
        ],
        "implementation_implication": (
            "Default-off branch-local module can compute non-scalar signal/control diagnostics for the exact scope; "
            "target-delta scalar use remains disabled."
        ),
        "missed_opportunity_preserved": True,
    }
