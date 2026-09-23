"""Runtime router surfaces for exact-control implementation code paths."""

from __future__ import annotations

from typing import Any


EXACT_CONTROL_RUNTIME_ROUTER_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_runtime_router.py"
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
        "exact_control_runtime_router_surface": EXACT_CONTROL_RUNTIME_ROUTER_SURFACE,
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


def register_exact_control_code_path(code_path_row: dict[str, Any]) -> dict[str, Any]:
    status = code_path_row.get("code_path_status")
    if status == "EXACT_CONTROL_CODE_PATH_DEFAULT_OFF_SCORER_SPEC":
        registration_status = "EXACT_CONTROL_RUNTIME_REGISTER_DEFAULT_OFF_SCORER_CODE_PATH"
        runtime_family = "DEFAULT_OFF_SCORER"
        runtime_action = "register_exact_scope_default_off_scorer_without_live_effect"
    elif status == "EXACT_CONTROL_CODE_PATH_SPLIT_REDESIGN_SPEC":
        registration_status = "EXACT_CONTROL_RUNTIME_REGISTER_SPLIT_REDESIGN_CODE_PATH"
        runtime_family = "SPLIT_REDESIGN_ROUTER"
        runtime_action = "register_exact_scope_split_redesign_router_without_live_effect"
    else:
        registration_status = "EXACT_CONTROL_RUNTIME_REGISTER_RECHECK_CODE_PATH"
        runtime_family = "RECHECK"
        runtime_action = "recheck_code_path_before_runtime_registration"
    lineage = "SCOPE_SPEC" if code_path_row.get("input_scope_runtime_spec_row_id") else "BLOCKER_SPEC"
    return {
        **_common(code_path_row),
        "input_code_path_spec_row_id": code_path_row.get("exact_control_code_path_spec_row_id"),
        "input_scope_runtime_spec_row_id": code_path_row.get("input_scope_runtime_spec_row_id"),
        "input_blocker_runtime_decision_row_id": code_path_row.get("input_blocker_runtime_decision_row_id"),
        "source_code_path_status": status,
        "runtime_code_path_lineage": lineage,
        "runtime_registration_status": registration_status,
        "runtime_family": runtime_family,
        "runtime_action": runtime_action,
        "module_slot": code_path_row.get("module_slot"),
        "required_guard": code_path_row.get("required_guard"),
        "default_off_exact_control_score": code_path_row.get("default_off_exact_control_score"),
        "redesign_family": code_path_row.get("redesign_family"),
        "registration_scope_key": mechanical_scope_key(code_path_row),
        "duplicate_runtime_use_allowed": False,
    }


def effective_scope_registration(registrations: list[dict[str, Any]]) -> dict[str, Any]:
    if not registrations:
        return {
            "exact_control_runtime_router_surface": EXACT_CONTROL_RUNTIME_ROUTER_SURFACE,
            "effective_scope_registration_status": "EXACT_CONTROL_RUNTIME_EFFECTIVE_SCOPE_RECHECK_NO_REGISTRATION",
            "linked_code_path_count": 0,
            "duplicate_code_path_count": 0,
            "runtime_score_allowed": False,
            "unconditional_scalar_use_allowed": False,
            "candidate_use_allowed_now": False,
            "live_effect": False,
        }
    first = registrations[0]
    default_rows = [row for row in registrations if row.get("runtime_family") == "DEFAULT_OFF_SCORER"]
    split_rows = [row for row in registrations if row.get("runtime_family") == "SPLIT_REDESIGN_ROUTER"]
    if default_rows and not split_rows:
        status = "EXACT_CONTROL_RUNTIME_EFFECTIVE_DEFAULT_OFF_SCORER_SCOPE"
        family = "DEFAULT_OFF_SCORER"
        action = "dedupe_default_off_scorer_scope_and_preserve_all_code_path_lineage"
        score = default_rows[0].get("default_off_exact_control_score")
        redesign_family = None
    elif split_rows and not default_rows:
        status = "EXACT_CONTROL_RUNTIME_EFFECTIVE_SPLIT_REDESIGN_SCOPE"
        family = "SPLIT_REDESIGN_ROUTER"
        action = "dedupe_split_redesign_scope_and_preserve_all_code_path_lineage"
        score = None
        redesign_family = split_rows[0].get("redesign_family")
    else:
        status = "EXACT_CONTROL_RUNTIME_EFFECTIVE_SCOPE_RECHECK_MIXED_REGISTRATION"
        family = "RECHECK"
        action = "recheck_mixed_scope_registration_before_event_routing"
        score = None
        redesign_family = None
    return {
        **_common(first),
        "effective_scope_registration_status": status,
        "effective_runtime_family": family,
        "effective_scope_action": action,
        "linked_code_path_count": len(registrations),
        "duplicate_code_path_count": max(len(registrations) - 1, 0),
        "scope_spec_lineage_count": sum(1 for row in registrations if row.get("runtime_code_path_lineage") == "SCOPE_SPEC"),
        "blocker_spec_lineage_count": sum(
            1 for row in registrations if row.get("runtime_code_path_lineage") == "BLOCKER_SPEC"
        ),
        "default_off_exact_control_score": score,
        "redesign_family": redesign_family,
        "duplicate_handling_status": "DUPLICATE_CODE_PATH_LINEAGE_DEDUPED_FOR_RUNTIME_PRESERVED_FOR_AUDIT",
        "linked_code_path_ids": [row.get("exact_control_runtime_code_path_registration_row_id") for row in registrations],
    }


def route_exact_control_event(
    event_row: dict[str, Any],
    effective_registration_row: dict[str, Any] | None,
) -> dict[str, Any]:
    registration = effective_registration_row or {}
    primitive_present = bool(event_row.get("primitive_present"))
    family = registration.get("effective_runtime_family")
    if primitive_present and family == "DEFAULT_OFF_SCORER":
        status = "EXACT_CONTROL_RUNTIME_EVENT_DEFAULT_OFF_SCORE_EMITTED"
        action = "emit_default_off_exact_control_score"
        score = registration.get("default_off_exact_control_score")
        redesign_signal = None
    elif primitive_present and family == "SPLIT_REDESIGN_ROUTER":
        status = "EXACT_CONTROL_RUNTIME_EVENT_REDESIGN_SIGNAL_ROUTED"
        action = "route_alignment_positive_target_negative_redesign_signal"
        score = None
        redesign_signal = event_row.get("redesign_alignment_signal")
    elif primitive_present:
        status = "EXACT_CONTROL_RUNTIME_EVENT_RECHECK_NO_EFFECTIVE_SCOPE"
        action = "recheck_missing_or_mixed_effective_scope_registration"
        score = None
        redesign_signal = None
    else:
        status = "EXACT_CONTROL_RUNTIME_EVENT_DENOMINATOR_CONTEXT"
        action = "preserve_denominator_context_without_signal"
        score = None
        redesign_signal = None
    return {
        **_common(event_row),
        "input_event_implementation_observation_row_id": event_row.get(
            "exact_control_event_implementation_observation_row_id"
        ),
        "input_event_score_row_id": event_row.get("input_event_score_row_id"),
        "input_denominator_event_row_id": event_row.get("input_denominator_event_row_id"),
        "input_effective_scope_registration_row_id": registration.get("exact_control_effective_scope_registration_row_id"),
        "bar_open_utc": event_row.get("bar_open_utc"),
        "future_bar_open_utc": event_row.get("future_bar_open_utc"),
        "primitive_present": primitive_present,
        "runtime_event_routing_status": status,
        "runtime_event_action": action,
        "runtime_event_score": score,
        "runtime_redesign_alignment_signal": redesign_signal,
        "redesign_family": registration.get("redesign_family") or event_row.get("redesign_family"),
        "future_change_per_current_range": event_row.get("future_change_per_current_range"),
        "delta_aligned_with_future": event_row.get("delta_aligned_with_future"),
        "linked_code_path_count": registration.get("linked_code_path_count"),
        "duplicate_code_path_count": registration.get("duplicate_code_path_count"),
    }


def duplicate_scope_audit_row(effective_registration_row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_common(effective_registration_row),
        "input_effective_scope_registration_row_id": effective_registration_row.get(
            "exact_control_effective_scope_registration_row_id"
        ),
        "duplicate_scope_audit_status": effective_registration_row.get("duplicate_handling_status"),
        "linked_code_path_count": effective_registration_row.get("linked_code_path_count"),
        "duplicate_code_path_count": effective_registration_row.get("duplicate_code_path_count"),
        "scope_spec_lineage_count": effective_registration_row.get("scope_spec_lineage_count"),
        "blocker_spec_lineage_count": effective_registration_row.get("blocker_spec_lineage_count"),
        "effective_runtime_family": effective_registration_row.get("effective_runtime_family"),
        "audit_decision": "preserve_all_code_path_rows_but_route_events_once_per_effective_scope",
    }
