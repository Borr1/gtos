"""Compare executed redesign modules against exact-control default-off scopes."""

from __future__ import annotations

from typing import Any


EXACT_CONTROL_REDESIGN_MODULE_DELTA_COMPARATOR_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_redesign_module_delta_comparator.py"
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


def mechanical_scope_key(row: dict[str, Any]) -> str:
    return (
        f"symbol={row.get('symbol')}|session={row.get('route_session')}|"
        f"horizon={row.get('horizon_id')}|primitive={row.get('primitive_flag')}"
    )


def _common(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "exact_control_redesign_module_delta_comparator_surface": EXACT_CONTROL_REDESIGN_MODULE_DELTA_COMPARATOR_SURFACE,
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


def default_scope_candidates(
    scope_execution_row: dict[str, Any],
    effective_scope_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current_horizon = horizon_number(scope_execution_row.get("horizon_id"))
    candidates = []
    for row in effective_scope_rows:
        if row.get("effective_runtime_family") != "DEFAULT_OFF_SCORER":
            continue
        if mechanism_key(row) != mechanism_key(scope_execution_row):
            continue
        score = to_float(row.get("default_off_exact_control_score"))
        if score is None:
            continue
        candidate = dict(row)
        candidate["_score"] = score
        candidate["_is_shorter"] = (
            current_horizon is not None
            and horizon_number(row.get("horizon_id")) is not None
            and horizon_number(row.get("horizon_id")) < current_horizon
        )
        candidates.append(candidate)
    candidates.sort(key=lambda item: (item["_score"], item.get("_is_shorter", False)), reverse=True)
    return candidates


def redesign_scope_module_delta_comparison(
    scope_execution_row: dict[str, Any],
    effective_scope_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidates = default_scope_candidates(scope_execution_row, effective_scope_rows)
    shorter = [row for row in candidates if row.get("_is_shorter")]
    best_any = candidates[0] if candidates else {}
    best_shorter = shorter[0] if shorter else {}
    target_delta = to_float(scope_execution_row.get("module_execution_target_delta"))
    alignment_delta = to_float(scope_execution_row.get("module_execution_alignment_delta"))
    module_slot = scope_execution_row.get("module_slot")
    transfer_score = to_float(scope_execution_row.get("transfer_target_score"))
    if module_slot == "branch_local_exact_control_shorter_horizon_transfer_router" and transfer_score is not None:
        comparator_decision = "MODULE_DELTA_REGISTER_SHORTER_HORIZON_TRANSFER_CANDIDATE"
        registry_candidate_class = "FINAL_REGISTRY_CANDIDATE_SHORTER_HORIZON_TRANSFER"
    elif module_slot == "branch_local_exact_control_directional_context_feature" and (alignment_delta or 0) >= 0.05:
        comparator_decision = "MODULE_DELTA_REGISTER_DIRECTIONAL_CONTEXT_FEATURE_CANDIDATE"
        registry_candidate_class = "FINAL_REGISTRY_CANDIDATE_DIRECTIONAL_CONTEXT_FEATURE"
    elif module_slot == "branch_local_exact_control_tighter_target_stress_tester":
        comparator_decision = "MODULE_DELTA_REGISTER_TIGHTER_TARGET_STRESS_CANDIDATE"
        registry_candidate_class = "FINAL_REGISTRY_CANDIDATE_TIGHTER_TARGET_STRESS"
    else:
        comparator_decision = "MODULE_DELTA_REGISTER_ENTRY_AVOID_INVERSE_SPLIT_CANDIDATE"
        registry_candidate_class = "FINAL_REGISTRY_CANDIDATE_ENTRY_AVOID_INVERSE_SPLIT"
    if target_delta is not None and target_delta < 0:
        target_delta_use = "TARGET_DELTA_NEGATIVE_DO_NOT_USE_AS_SCALAR"
    else:
        target_delta_use = "TARGET_DELTA_NONNEGATIVE_RECHECK_BEFORE_SCALAR"
    return {
        **_common(scope_execution_row),
        "input_scope_module_execution_row_id": scope_execution_row.get(
            "exact_control_redesign_scope_module_execution_row_id"
        ),
        "module_slot": module_slot,
        "module_scope_signal_event_rows": scope_execution_row.get("module_scope_signal_event_rows"),
        "module_scope_control_event_rows": scope_execution_row.get("module_scope_control_event_rows"),
        "module_execution_target_delta": target_delta,
        "module_execution_alignment_delta": alignment_delta,
        "target_delta_use": target_delta_use,
        "same_mechanism_default_off_candidate_count": len(candidates),
        "same_mechanism_shorter_default_off_candidate_count": len(shorter),
        "best_default_off_horizon_id": best_any.get("horizon_id"),
        "best_default_off_score": best_any.get("_score"),
        "best_shorter_default_off_horizon_id": best_shorter.get("horizon_id"),
        "best_shorter_default_off_score": best_shorter.get("_score"),
        "transfer_target_horizon_id": scope_execution_row.get("transfer_target_horizon_id"),
        "transfer_target_score": transfer_score,
        "module_delta_comparator_decision": comparator_decision,
        "registry_candidate_class": registry_candidate_class,
        "missed_opportunity_preserved": True,
    }


def redesign_event_module_delta_comparison(
    event_execution_row: dict[str, Any],
    scope_comparison_row: dict[str, Any] | None,
) -> dict[str, Any]:
    scope_comparison = scope_comparison_row or {}
    return {
        **_common(event_execution_row),
        "input_event_module_execution_row_id": event_execution_row.get(
            "exact_control_redesign_event_module_execution_row_id"
        ),
        "input_scope_module_delta_comparison_row_id": scope_comparison.get(
            "exact_control_redesign_scope_module_delta_comparison_row_id"
        ),
        "module_slot": event_execution_row.get("module_slot"),
        "module_scope_relation": event_execution_row.get("module_scope_relation"),
        "event_module_execution_status": event_execution_row.get("event_module_execution_status"),
        "event_delta_comparison_status": "MODULE_DELTA_EVENT_CONSUMED_IN_SCOPE_COMPARATOR",
        "module_delta_comparator_decision": scope_comparison.get("module_delta_comparator_decision"),
        "registry_candidate_class": scope_comparison.get("registry_candidate_class"),
        "future_change_per_current_range": event_execution_row.get("future_change_per_current_range"),
        "delta_aligned_with_future": event_execution_row.get("delta_aligned_with_future"),
        "runtime_redesign_alignment_signal": event_execution_row.get("runtime_redesign_alignment_signal"),
    }


def redesign_registry_candidate_from_comparison(
    scope_comparison_row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    return {
        **_common(scope_comparison_row),
        "exact_control_redesign_registry_candidate_row_id": (
            f"OHLC-GTOS-DENOM-EXACTCTRL-REDESIGN-REGISTRY-CANDIDATE-{index:04d}"
        ),
        "input_scope_module_delta_comparison_row_id": scope_comparison_row.get(
            "exact_control_redesign_scope_module_delta_comparison_row_id"
        ),
        "module_slot": scope_comparison_row.get("module_slot"),
        "module_delta_comparator_decision": scope_comparison_row.get("module_delta_comparator_decision"),
        "registry_candidate_class": scope_comparison_row.get("registry_candidate_class"),
        "target_delta_use": scope_comparison_row.get("target_delta_use"),
        "module_execution_target_delta": scope_comparison_row.get("module_execution_target_delta"),
        "module_execution_alignment_delta": scope_comparison_row.get("module_execution_alignment_delta"),
        "best_shorter_default_off_horizon_id": scope_comparison_row.get("best_shorter_default_off_horizon_id"),
        "best_shorter_default_off_score": scope_comparison_row.get("best_shorter_default_off_score"),
        "registry_candidate_status": "REDESIGN_FINAL_REGISTRY_CANDIDATE_DEFAULT_OFF",
        "registry_candidate_action": "materialize_final_branch_local_default_off_redesign_candidate",
        "candidate_use_allowed_now": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
