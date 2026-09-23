"""Default-off scorer registry for denominator detail decision rows."""

from __future__ import annotations

from typing import Any


DEFAULT_OFF_SCORER_SURFACE = "src/research_infra/moonshot_branch_local_denominator_default_off_scorers.py"


def _scope_key(row: dict[str, Any]) -> str:
    return "|".join(str(row.get(part) or "") for part in ("symbol", "route_session", "horizon_id", "primitive_flag"))


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_float(*values: Any) -> float | None:
    for value in values:
        converted = _to_float(value)
        if converted is not None:
            return converted
    return None


def register_default_off_scorer(behavior_row: dict[str, Any], source_row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = source_row or {}
    status = behavior_row.get("scorer_behavior_status")
    if status == "SCORER_BEHAVIOR_GUARDED_SCOPE_PROXY_MATCH_ONLY":
        scorer_kind = "DEFAULT_OFF_GUARDED_SCOPE_PROXY_SCORER"
        registration_status = "DEFAULT_OFF_SCORER_REGISTERED_MATCH_SCOPE_SCORE"
        score = _first_float(source.get("decision_proxy_score"), source.get("guarded_proxy_score_mean"))
        permission = "MATCH_SCOPE_ONLY"
    elif status == "SCORER_BEHAVIOR_HORIZON_REPAIR_RESCORER_DEFAULT_OFF":
        scorer_kind = "DEFAULT_OFF_HORIZON_REPAIR_RESCORER"
        registration_status = "DEFAULT_OFF_SCORER_REGISTERED_HORIZON_REPAIR_SCORE"
        score = _to_float(source.get("repair_upper_proxy_r_style_midpoint"))
        permission = "MATCH_SCOPE_ONLY"
    elif status == "SCORER_BEHAVIOR_HORIZON_REDESIGN_DEFAULT_OFF":
        scorer_kind = "DEFAULT_OFF_HORIZON_REDESIGN_SCORER"
        registration_status = "DEFAULT_OFF_SCORER_REGISTERED_HORIZON_REDESIGN_SCORE"
        score = _to_float(source.get("repair_upper_proxy_r_style_midpoint"))
        permission = "MATCH_SCOPE_ONLY"
    elif status == "SCORER_BEHAVIOR_HORIZON_KILL_CHECK_REPAIR_GATE":
        scorer_kind = "DEFAULT_OFF_HORIZON_KILL_CHECK_GATE"
        registration_status = "DEFAULT_OFF_SCORER_REGISTERED_KILL_CHECK_GATE_NO_SCORE"
        score = None
        permission = "MATCH_SCOPE_GATE_ONLY"
    else:
        scorer_kind = "DEFAULT_OFF_RECHECK"
        registration_status = "DEFAULT_OFF_SCORER_RECHECK_BEHAVIOR"
        score = None
        permission = "RECHECK"
    return {
        "default_off_scorer_surface": DEFAULT_OFF_SCORER_SURFACE,
        "input_scorer_behavior_row_id": behavior_row.get("scorer_behavior_row_id"),
        "input_detail_execution_row_id": behavior_row.get("input_detail_execution_row_id"),
        "symbol": behavior_row.get("symbol"),
        "route_session": behavior_row.get("route_session"),
        "horizon_id": behavior_row.get("horizon_id"),
        "primitive_flag": behavior_row.get("primitive_flag"),
        "source_code_candidate_id": behavior_row.get("source_code_candidate_id"),
        "outside_gbpjpy_xauusd_current_branch_box": behavior_row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "default_off_scorer_registration_status": registration_status,
        "default_off_scorer_kind": scorer_kind,
        "default_off_scorer_key": _scope_key(behavior_row),
        "default_off_scorer_score": score,
        "scorer_permission": permission,
        "source_behavior_status": status,
        "default_off": True,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }


def event_matches_default_off_scope(event_row: dict[str, Any], registration_row: dict[str, Any]) -> bool:
    return all(
        str(event_row.get(part) or "") == str(registration_row.get(part) or "")
        for part in ("symbol", "route_session", "horizon_id", "primitive_flag")
    )


def score_default_off_event(event_row: dict[str, Any], registration_row: dict[str, Any]) -> dict[str, Any]:
    matched = event_matches_default_off_scope(event_row, registration_row)
    if not matched:
        status = "DEFAULT_OFF_SCORER_EVENT_SCOPE_MISMATCH"
        score = None
    elif registration_row.get("default_off_scorer_kind") == "DEFAULT_OFF_HORIZON_KILL_CHECK_GATE":
        status = "DEFAULT_OFF_SCORER_EVENT_KILL_CHECK_GATE_HELD"
        score = None
    else:
        status = "DEFAULT_OFF_SCORER_EVENT_SCORE_EMITTED"
        score = registration_row.get("default_off_scorer_score")
    return {
        "default_off_scorer_surface": DEFAULT_OFF_SCORER_SURFACE,
        "input_default_off_scorer_registration_row_id": registration_row.get("default_off_scorer_registration_row_id"),
        "default_off_scorer_key": registration_row.get("default_off_scorer_key"),
        "default_off_scorer_kind": registration_row.get("default_off_scorer_kind"),
        "event_match": matched,
        "default_off_scorer_event_status": status,
        "default_off_scorer_event_score": score,
        "default_off": True,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
