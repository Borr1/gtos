"""Executable research-only modules from numeric moonshot result rows."""

from __future__ import annotations

import hashlib
from typing import Any


NUMERIC_DECISION_MODULE_SURFACE = "src/research_infra/moonshot_numeric_decision_modules.py"


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stable_key(*parts: Any) -> str:
    payload = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def numeric_scope_key(row: dict[str, Any]) -> str:
    existing = row.get("mechanical_scope_key")
    if existing:
        return str(existing)
    return "|".join(
        f"{field}={row.get(field) or ''}"
        for field in ("symbol", "route_session", "horizon_id", "primitive_flag", "source_component")
    )


def numeric_decision_role(row: dict[str, Any]) -> str:
    decision = str(row.get("keep_kill_redesign_implement_decision") or "")
    if decision == "IMPLEMENT_DEFAULT_OFF_SCORER_RESEARCH_MODULE":
        return "DEFAULT_OFF_NUMERIC_SCORER_MODULE"
    if decision in {
        "KEEP_NOFILL_CHALLENGER_COMPARATOR_STRONG_POSITIVE",
        "KEEP_STRONG_POSITIVE_PROXY_R_WITH_CONTROL",
        "KEEP_POSITIVE_PROXY_R_WITH_CONTROL",
    }:
        return "DEFAULT_OFF_PROXY_CHALLENGER_SCORER_MODULE"
    if decision == "CONVERT_STRONG_NEGATIVE_TO_AVOID_INVERSE_OR_FAILURE_FILTER":
        return "AVOID_INVERSE_OR_FAILURE_FILTER_MODULE"
    if decision in {
        "SOURCE_GEOMETRY_REPAIR_OR_GUARD_BINDING_REQUIRED",
        "REDESIGN_OR_REPLAY_REPAIR_REQUIRED_NO_NUMERIC_PROXY",
    }:
        return "SOURCE_GEOMETRY_REPAIR_MODULE"
    if decision in {
        "MERGE_AS_CONTROL_CONTEXT_PENDING_EXACT_GEOMETRY",
        "REDESIGN_NEGATIVE_PROXY_OR_MERGE_AS_CONTEXT_FEATURE",
        "KEEP_NEUTRAL_PROXY_AS_CONTEXT_OR_STRESS_CONTROL",
    }:
        return "CONTEXT_STRESS_OR_REDESIGN_MODULE"
    return "RECHECK_NUMERIC_DECISION_MODULE"


def _module_status(role: str) -> str:
    return {
        "DEFAULT_OFF_NUMERIC_SCORER_MODULE": "NUMERIC_MODULE_DEFAULT_OFF_SCORER_EXECUTABLE",
        "DEFAULT_OFF_PROXY_CHALLENGER_SCORER_MODULE": "NUMERIC_MODULE_PROXY_CHALLENGER_SCORER_EXECUTABLE",
        "AVOID_INVERSE_OR_FAILURE_FILTER_MODULE": "NUMERIC_MODULE_AVOID_INVERSE_FILTER_EXECUTABLE",
        "SOURCE_GEOMETRY_REPAIR_MODULE": "NUMERIC_MODULE_SOURCE_GEOMETRY_REPAIR_EXECUTABLE",
        "CONTEXT_STRESS_OR_REDESIGN_MODULE": "NUMERIC_MODULE_CONTEXT_STRESS_EXECUTABLE",
    }.get(role, "NUMERIC_MODULE_RECHECK_REQUIRED")


def source_geometry_repair_action(row: dict[str, Any]) -> str:
    exact_status = str(row.get("exact_r_status") or "")
    if exact_status == "EXACT_R_NOT_COMPUTABLE_SOURCE_JOIN_ABSENT":
        return "acquire_or_rebuild_missing_source_join_before_exact_r"
    if exact_status == "EXACT_SPREAD_REPAIRED_PROXY_AVAILABLE_NOT_BROKER_EXACT_R":
        return "attach_broker_execution_geometry_to_exact_spread_proxy"
    if row.get("exact_missing_field_proof"):
        return "join_or_reconstruct_broker_execution_geometry_fields"
    if row.get("proxy_r_value") is None:
        return "replay_or_proxy_numeric_geometry_before_score_use"
    return "no_source_geometry_repair_required_for_current_proxy"


def avoid_inverse_filter_action(row: dict[str, Any]) -> str:
    target_stop = str(row.get("target_stop_order_class") or "")
    if target_stop == "STOP_FIRST_PROXY_DOMINANT":
        return "avoid_current_entry_when_scope_matches_stop_first_proxy"
    if target_stop == "TARGET_STOP_AMBIGUOUS_OR_MIXED":
        return "fail_closed_or_downweight_ambiguous_negative_scope"
    return "emit_negative_proxy_failure_filter_for_scope"


def module_record_from_numeric_result(row: dict[str, Any], index: int) -> dict[str, Any]:
    role = numeric_decision_role(row)
    proxy_value = _to_float(row.get("decision_proxy_value"))
    if proxy_value is None:
        proxy_value = _to_float(row.get("proxy_r_value"))
    scope_key = numeric_scope_key(row)
    module_key = _stable_key(scope_key, row.get("source_row_id"), row.get("keep_kill_redesign_implement_decision"))
    return {
        "numeric_decision_module_surface": NUMERIC_DECISION_MODULE_SURFACE,
        "numeric_decision_module_import": "src.research_infra.moonshot_numeric_decision_modules",
        "registration_callable_name": "module_record_from_numeric_result",
        "event_callable_name": "execute_numeric_module_event",
        "numeric_decision_module_row_id": f"OHLC-GTOS-NUMERIC-DECISION-MODULE-{index:06d}",
        "input_numeric_result_row_id": row.get("numeric_result_row_id"),
        "input_integrated_result_execution_row_id": row.get("input_integrated_result_execution_row_id"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "numeric_scope_key": scope_key,
        "numeric_module_key": module_key,
        "numeric_module_role": role,
        "numeric_module_status": _module_status(role),
        "event_input_contract": (
            "numeric_scope_key preferred; otherwise symbol, route_session, horizon_id, primitive_flag, "
            "and source_component must match before any research-only score, avoid/inverse filter, "
            "or source-geometry repair action is emitted"
        ),
        "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
        "proxy_r_value": row.get("proxy_r_value"),
        "decision_proxy_value": proxy_value,
        "expectancy_proxy_value": row.get("expectancy_proxy_value"),
        "proxy_r_class": row.get("proxy_r_class"),
        "exact_r_status": row.get("exact_r_status"),
        "target_stop_order_class": row.get("target_stop_order_class"),
        "cost_stress_status": row.get("cost_stress_status"),
        "default_off": True,
        "match_policy": "exact_numeric_scope_key_or_symbol_session_horizon_primitive_source_component",
        "score_emit_allowed_when_matched": role
        in {
            "DEFAULT_OFF_NUMERIC_SCORER_MODULE",
            "DEFAULT_OFF_PROXY_CHALLENGER_SCORER_MODULE",
        },
        "avoid_inverse_emit_allowed_when_matched": role == "AVOID_INVERSE_OR_FAILURE_FILTER_MODULE",
        "source_geometry_repair_action": source_geometry_repair_action(row),
        "avoid_inverse_filter_action": avoid_inverse_filter_action(row)
        if role == "AVOID_INVERSE_OR_FAILURE_FILTER_MODULE"
        else "not_avoid_inverse_module",
        "required_guard_policy": (
            "source_geometry_and_control_guard_required_before_any_scalar_use"
            if role
            in {
                "SOURCE_GEOMETRY_REPAIR_MODULE",
                "CONTEXT_STRESS_OR_REDESIGN_MODULE",
                "RECHECK_NUMERIC_DECISION_MODULE",
            }
            else "default_off_scope_match_and_source_guard_required"
        ),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def event_matches_numeric_module(event_row: dict[str, Any], module_row: dict[str, Any]) -> bool:
    event_scope = event_row.get("numeric_scope_key") or event_row.get("mechanical_scope_key")
    if event_scope and str(event_scope) == str(module_row.get("numeric_scope_key")):
        return True
    return all(
        str(event_row.get(field) or "") == str(module_row.get(field) or "")
        for field in ("symbol", "route_session", "horizon_id", "primitive_flag", "source_component")
    )


def execute_numeric_module_event(event_row: dict[str, Any], module_row: dict[str, Any]) -> dict[str, Any]:
    matched = event_matches_numeric_module(event_row, module_row)
    role = str(module_row.get("numeric_module_role") or "")
    if not matched:
        status = "NUMERIC_MODULE_EVENT_SCOPE_MISMATCH"
        score = None
        avoid = False
        repair = None
    elif module_row.get("score_emit_allowed_when_matched") is True:
        status = "NUMERIC_MODULE_EVENT_DEFAULT_OFF_SCORE_EMITTED"
        score = module_row.get("decision_proxy_value")
        avoid = False
        repair = None
    elif role == "AVOID_INVERSE_OR_FAILURE_FILTER_MODULE":
        status = "NUMERIC_MODULE_EVENT_AVOID_INVERSE_FILTER_EMITTED"
        score = None
        avoid = True
        repair = None
    elif role == "SOURCE_GEOMETRY_REPAIR_MODULE":
        status = "NUMERIC_MODULE_EVENT_SOURCE_GEOMETRY_REPAIR_REQUIRED"
        score = None
        avoid = False
        repair = module_row.get("source_geometry_repair_action")
    else:
        status = "NUMERIC_MODULE_EVENT_CONTEXT_OR_STRESS_ONLY"
        score = None
        avoid = False
        repair = module_row.get("source_geometry_repair_action")
    return {
        "numeric_decision_module_surface": NUMERIC_DECISION_MODULE_SURFACE,
        "numeric_decision_module_import": "src.research_infra.moonshot_numeric_decision_modules",
        "event_callable_name": "execute_numeric_module_event",
        "input_numeric_decision_module_row_id": module_row.get("numeric_decision_module_row_id"),
        "numeric_module_key": module_row.get("numeric_module_key"),
        "numeric_module_role": role,
        "event_match": matched,
        "numeric_module_event_status": status,
        "numeric_module_event_score": score,
        "avoid_inverse_filter_emitted": avoid,
        "source_geometry_repair_action": repair,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def source_geometry_repair_spec(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "numeric_decision_module_surface": NUMERIC_DECISION_MODULE_SURFACE,
        "numeric_decision_module_import": "src.research_infra.moonshot_numeric_decision_modules",
        "repair_callable_name": "source_geometry_repair_spec",
        "source_geometry_repair_spec_row_id": f"OHLC-GTOS-NUMERIC-SOURCE-GEOMETRY-REPAIR-{index:06d}",
        "input_numeric_result_row_id": row.get("numeric_result_row_id"),
        "input_integrated_result_execution_row_id": row.get("input_integrated_result_execution_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "repair_action": source_geometry_repair_action(row),
        "exact_r_status": row.get("exact_r_status"),
        "missing_field_count": len(row.get("exact_missing_field_proof") or []),
        "exact_missing_field_proof": row.get("exact_missing_field_proof") or [],
        "branch_match_status": row.get("branch_match_status"),
        "target_stop_order_class": row.get("target_stop_order_class"),
        "cost_stress_status": row.get("cost_stress_status"),
        "opportunity_preserved": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def avoid_inverse_filter_spec(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "numeric_decision_module_surface": NUMERIC_DECISION_MODULE_SURFACE,
        "numeric_decision_module_import": "src.research_infra.moonshot_numeric_decision_modules",
        "avoid_inverse_callable_name": "avoid_inverse_filter_spec",
        "avoid_inverse_filter_spec_row_id": f"OHLC-GTOS-NUMERIC-AVOID-INVERSE-FILTER-{index:06d}",
        "input_numeric_result_row_id": row.get("numeric_result_row_id"),
        "input_integrated_result_execution_row_id": row.get("input_integrated_result_execution_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "filter_action": avoid_inverse_filter_action(row),
        "proxy_r_value": row.get("proxy_r_value"),
        "decision_proxy_value": row.get("decision_proxy_value"),
        "proxy_r_class": row.get("proxy_r_class"),
        "target_stop_order_class": row.get("target_stop_order_class"),
        "failure_intelligence_role": row.get("negative_or_failure_intelligence_role"),
        "underlying_mechanism_preserved": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }
