"""Research-only guarded scorer registry for denominator/source candidates."""

from __future__ import annotations

import re
from typing import Any


GUARDED_SCORER_REGISTRY_SURFACE = "src/research_infra/moonshot_branch_local_denominator_guarded_scorers.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    numeric = to_float(value)
    return int(numeric) if numeric is not None else 0


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text and text.lower() not in {"none", "null"} else None


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def scorer_scope_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            normalize_text(row.get("symbol")) or "ANY_SYMBOL",
            normalize_text(row.get("route_session")) or "ANY_SESSION",
            normalize_text(row.get("horizon_id")) or "ANY_HORIZON",
            normalize_text(row.get("primitive_flag")) or "ANY_PRIMITIVE",
        ]
    )


def scorer_function_name(row: dict[str, Any]) -> str:
    key = scorer_scope_key(row).lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", key).strip("_")
    return f"score_guarded_scope_proxy_{cleaned}"


def _score_class(score: float | None) -> str:
    if score is None:
        return "GUARDED_SCOPE_PROXY_SCORE_MISSING"
    if score >= 0.60:
        return "GUARDED_SCOPE_PROXY_SCORE_GE_060"
    return "GUARDED_SCOPE_PROXY_SCORE_LT_060"


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "guarded_scorer_registry_surface": GUARDED_SCORER_REGISTRY_SURFACE,
        "symbol": normalize_text(row.get("symbol")),
        "route_session": normalize_text(row.get("route_session")),
        "horizon_id": normalize_text(row.get("horizon_id")),
        "primitive_flag": normalize_text(row.get("primitive_flag")),
        "outside_gbpjpy_xauusd_current_branch_box": bool(row.get("outside_gbpjpy_xauusd_current_branch_box")),
        "live_effect": False,
    }


def register_research_only_guarded_scope_proxy_scorer(spec_row: dict[str, Any]) -> dict[str, Any]:
    score = to_float(spec_row.get("guarded_proxy_score_mean"))
    scalar_allowed = bool(spec_row.get("proxy_scalar_interpretation_allowed"))
    candidate_allowed = bool(spec_row.get("candidate_use_allowed_now"))
    exact_guard_open = to_int(spec_row.get("target_underpowered_rows")) > 0
    if candidate_allowed and scalar_allowed and score is not None:
        status = "GUARDED_SCORER_REGISTERED_RESEARCH_ONLY"
        decision = "REGISTER_BRANCH_LOCAL_GUARDED_SCOPE_PROXY_SCORER"
        executable_now = True
    elif score is None:
        status = "GUARDED_SCORER_NOT_REGISTERED_NO_PROXY_SCORE"
        decision = "PRESERVE_CONTEXT_NO_SCALAR"
        executable_now = False
    else:
        status = "GUARDED_SCORER_NOT_REGISTERED_GUARD_BLOCKED"
        decision = "PRESERVE_CONTEXT_BUILD_DENOMINATOR"
        executable_now = False
    return {
        **_base(spec_row),
        "guarded_scorer_registration_status": status,
        "guarded_scorer_registration_decision": decision,
        "guarded_scorer_key": scorer_scope_key(spec_row),
        "guarded_scorer_function_name": scorer_function_name(spec_row),
        "input_guarded_scorer_spec_row_id": spec_row.get("guarded_scorer_spec_row_id"),
        "input_guarded_candidate_row_id": spec_row.get("input_guarded_candidate_row_id"),
        "input_resolution_row_id": spec_row.get("input_resolution_row_id"),
        "guarded_proxy_score_mean": score,
        "guarded_proxy_score_class": spec_row.get("guarded_proxy_score_class") or _score_class(score),
        "guarded_proxy_score_weight": clamp01(score or 0.0),
        "candidate_use_allowed_now": candidate_allowed,
        "proxy_scalar_interpretation_allowed": scalar_allowed,
        "unconditional_scalar_use_allowed": False,
        "exact_control_build_still_open": exact_guard_open,
        "target_action_rows": to_int(spec_row.get("target_action_rows")),
        "target_underpowered_rows": to_int(spec_row.get("target_underpowered_rows")),
        "required_guard": spec_row.get("required_guard")
        or "continue_exact_control_scope_denominator_build_before_unconditional_scalar_use",
        "next_same_resource_action": spec_row.get("next_same_resource_action"),
        "branch_local_research_only": True,
        "registration_runtime_surface": "branch_local_guarded_scope_proxy_registry",
        "executable_now": executable_now,
    }


def event_matches_guarded_scope(event_row: dict[str, Any], registration_row: dict[str, Any]) -> bool:
    for key in ("symbol", "route_session", "horizon_id", "primitive_flag"):
        expected = normalize_text(registration_row.get(key))
        observed = normalize_text(event_row.get(key))
        if expected is not None and observed != expected:
            return False
    return True


def score_guarded_scope_proxy_event(event_row: dict[str, Any], registration_row: dict[str, Any]) -> dict[str, Any]:
    score = to_float(registration_row.get("guarded_proxy_score_mean"))
    registered = registration_row.get("guarded_scorer_registration_status") == "GUARDED_SCORER_REGISTERED_RESEARCH_ONLY"
    scope_match = event_matches_guarded_scope(event_row, registration_row)
    if registered and scope_match and score is not None:
        status = "GUARDED_SCOPE_PROXY_EVENT_SCORE_EMITTED"
        decision = "SCORE_RESEARCH_ONLY_GUARDED_SCOPE_PROXY"
        emitted_score = clamp01(score)
    elif not scope_match:
        status = "GUARDED_SCOPE_PROXY_EVENT_SCOPE_MISMATCH"
        decision = "DO_NOT_SCORE_OUTSIDE_REGISTERED_SCOPE"
        emitted_score = None
    elif score is None:
        status = "GUARDED_SCOPE_PROXY_EVENT_NO_SCALAR"
        decision = "DO_NOT_SCORE_WITHOUT_PROXY_SCALAR"
        emitted_score = None
    else:
        status = "GUARDED_SCOPE_PROXY_EVENT_REGISTRATION_BLOCKED"
        decision = "DO_NOT_SCORE_UNREGISTERED_GUARD"
        emitted_score = None
    return {
        "guarded_scorer_registry_surface": GUARDED_SCORER_REGISTRY_SURFACE,
        "guarded_scorer_key": registration_row.get("guarded_scorer_key"),
        "guarded_scorer_function_name": registration_row.get("guarded_scorer_function_name"),
        "input_guarded_scorer_registration_row_id": registration_row.get("guarded_scorer_registration_row_id"),
        "event_scope_key": scorer_scope_key(event_row),
        "registered_scope_key": registration_row.get("guarded_scorer_key"),
        "scope_match": scope_match,
        "guarded_scope_proxy_event_status": status,
        "guarded_scope_proxy_event_decision": decision,
        "guarded_scope_proxy_score": emitted_score,
        "guarded_proxy_score_class": registration_row.get("guarded_proxy_score_class"),
        "required_guard": registration_row.get("required_guard"),
        "exact_control_build_still_open": bool(registration_row.get("exact_control_build_still_open")),
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
