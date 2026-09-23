"""Research-only registry/router for numeric decision modules."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from src.research_infra.moonshot_numeric_decision_modules import execute_numeric_module_event


NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE = "src/research_infra/moonshot_numeric_module_registry_router.py"


def event_from_numeric_result(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "numeric_result_row_id": row.get("numeric_result_row_id"),
        "numeric_scope_key": row.get("mechanical_scope_key"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
    }


def build_numeric_module_registry(module_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_numeric_id = {
        str(row.get("input_numeric_result_row_id")): row
        for row in module_rows
        if row.get("input_numeric_result_row_id")
    }
    by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in module_rows:
        by_scope[str(row.get("numeric_scope_key") or "")].append(row)
        by_role[str(row.get("numeric_module_role") or "")].append(row)
    return {
        "numeric_module_registry_surface": NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE,
        "module_count": len(module_rows),
        "by_numeric_id": by_numeric_id,
        "by_scope": dict(by_scope),
        "by_role": dict(by_role),
    }


def route_numeric_event(event_row: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    numeric_id = str(event_row.get("numeric_result_row_id") or "")
    module = registry.get("by_numeric_id", {}).get(numeric_id)
    lookup_method = "numeric_result_row_id"
    if module is None:
        scope_modules = registry.get("by_scope", {}).get(str(event_row.get("numeric_scope_key") or ""), [])
        module = scope_modules[0] if len(scope_modules) == 1 else None
        lookup_method = "unique_numeric_scope_key" if module else "no_unique_module_match"
    if module is None:
        return {
            "numeric_module_registry_surface": NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE,
            "event_match": False,
            "module_lookup_method": lookup_method,
            "numeric_module_event_status": "NUMERIC_MODULE_ROUTER_NO_UNIQUE_MODULE_MATCH",
            "numeric_module_event_score": None,
            "avoid_inverse_filter_emitted": False,
            "source_geometry_repair_action": None,
            "runtime_score_allowed": False,
            "unconditional_scalar_use_allowed": False,
            "candidate_use_allowed_now": False,
            "live_effect": False,
        }
    routed = execute_numeric_module_event(event_row, module)
    routed["numeric_module_registry_surface"] = NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE
    routed["module_lookup_method"] = lookup_method
    return routed


def route_action_from_event(routed_event: dict[str, Any]) -> str:
    status = str(routed_event.get("numeric_module_event_status") or "")
    if status == "NUMERIC_MODULE_EVENT_DEFAULT_OFF_SCORE_EMITTED":
        return "REGISTER_DEFAULT_OFF_SCORER_SURFACE"
    if status == "NUMERIC_MODULE_EVENT_AVOID_INVERSE_FILTER_EMITTED":
        return "REGISTER_AVOID_INVERSE_FILTER_SURFACE"
    if status == "NUMERIC_MODULE_EVENT_SOURCE_GEOMETRY_REPAIR_REQUIRED":
        return "EXECUTE_SOURCE_GEOMETRY_REPAIR_PATH"
    if status == "NUMERIC_MODULE_EVENT_CONTEXT_OR_STRESS_ONLY":
        return "BIND_CONTEXT_STRESS_GUARD_SURFACE"
    return "RECHECK_ROUTER_EVENT_SCOPE"


def router_application_row(
    numeric_row: dict[str, Any],
    routed_event: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    action = route_action_from_event(routed_event)
    return {
        "numeric_module_router_surface": NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE,
        "numeric_module_router_application_row_id": f"OHLC-GTOS-NUMERIC-MODULE-ROUTER-APPLICATION-{index:06d}",
        "input_numeric_result_row_id": numeric_row.get("numeric_result_row_id"),
        "input_numeric_decision_module_row_id": routed_event.get("input_numeric_decision_module_row_id"),
        "numeric_module_key": routed_event.get("numeric_module_key"),
        "numeric_module_role": routed_event.get("numeric_module_role"),
        "module_lookup_method": routed_event.get("module_lookup_method"),
        "symbol": numeric_row.get("symbol"),
        "route_session": numeric_row.get("route_session"),
        "horizon_id": numeric_row.get("horizon_id"),
        "primitive_flag": numeric_row.get("primitive_flag"),
        "source_component": numeric_row.get("source_component"),
        "source_row_id": numeric_row.get("source_row_id"),
        "proxy_r_value": numeric_row.get("proxy_r_value"),
        "decision_proxy_value": numeric_row.get("decision_proxy_value"),
        "proxy_r_class": numeric_row.get("proxy_r_class"),
        "target_stop_order_class": numeric_row.get("target_stop_order_class"),
        "exact_r_status": numeric_row.get("exact_r_status"),
        "keep_kill_redesign_implement_decision": numeric_row.get("keep_kill_redesign_implement_decision"),
        "numeric_module_event_status": routed_event.get("numeric_module_event_status"),
        "numeric_module_event_score": routed_event.get("numeric_module_event_score"),
        "avoid_inverse_filter_emitted": routed_event.get("avoid_inverse_filter_emitted"),
        "source_geometry_repair_action": routed_event.get("source_geometry_repair_action"),
        "router_application_action": action,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def source_repair_execution_row(spec_row: dict[str, Any], index: int) -> dict[str, Any]:
    repair_action = str(spec_row.get("repair_action") or "")
    missing_fields = spec_row.get("exact_missing_field_proof") or []
    if repair_action == "acquire_or_rebuild_missing_source_join_before_exact_r":
        status = "SOURCE_REPAIR_EXECUTION_SOURCE_JOIN_NOT_PRESENT_IN_CURRENT_NUMERIC_PACKET"
        exact_repair_possible_now = False
    elif repair_action == "attach_broker_execution_geometry_to_exact_spread_proxy":
        status = "SOURCE_REPAIR_EXECUTION_BROKER_GEOMETRY_ATTACHMENT_REQUIRED"
        exact_repair_possible_now = False
    elif missing_fields:
        status = "SOURCE_REPAIR_EXECUTION_BROKER_EXECUTION_GEOMETRY_FIELDS_REQUIRED"
        exact_repair_possible_now = False
    else:
        status = "SOURCE_REPAIR_EXECUTION_REPLAY_PROXY_REPAIR_REQUIRED"
        exact_repair_possible_now = True
    return {
        "numeric_module_router_surface": NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE,
        "source_repair_execution_row_id": f"OHLC-GTOS-NUMERIC-MODULE-SOURCE-REPAIR-EXECUTION-{index:06d}",
        "input_source_geometry_repair_spec_row_id": spec_row.get("source_geometry_repair_spec_row_id"),
        "input_numeric_result_row_id": spec_row.get("input_numeric_result_row_id"),
        "symbol": spec_row.get("symbol"),
        "route_session": spec_row.get("route_session"),
        "horizon_id": spec_row.get("horizon_id"),
        "primitive_flag": spec_row.get("primitive_flag"),
        "source_component": spec_row.get("source_component"),
        "source_row_id": spec_row.get("source_row_id"),
        "repair_action": repair_action,
        "source_repair_execution_status": status,
        "exact_repair_possible_from_current_packet": exact_repair_possible_now,
        "missing_field_count": spec_row.get("missing_field_count"),
        "exact_missing_field_proof": missing_fields,
        "opportunity_preserved": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def scope_router_decision(rows: list[dict[str, Any]], index: int, key: tuple[Any, ...]) -> dict[str, Any]:
    scores = [row.get("numeric_module_event_score") for row in rows if isinstance(row.get("numeric_module_event_score"), (int, float))]
    avoid_count = sum(1 for row in rows if row.get("avoid_inverse_filter_emitted") is True)
    repair_count = sum(1 for row in rows if row.get("router_application_action") == "EXECUTE_SOURCE_GEOMETRY_REPAIR_PATH")
    context_count = sum(1 for row in rows if row.get("router_application_action") == "BIND_CONTEXT_STRESS_GUARD_SURFACE")
    scorer_count = sum(1 for row in rows if row.get("router_application_action") == "REGISTER_DEFAULT_OFF_SCORER_SURFACE")
    if scorer_count and (not scores or mean(scores) > 0):
        decision = "IMPLEMENT_DEFAULT_OFF_SCORER_SCOPE_WITH_GUARDS"
    elif avoid_count:
        decision = "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE"
    elif repair_count:
        decision = "EXECUTE_SOURCE_GEOMETRY_REPAIR_SCOPE"
    elif context_count:
        decision = "MERGE_CONTEXT_STRESS_SCOPE_AS_GUARD_INPUT"
    else:
        decision = "RECHECK_NUMERIC_ROUTER_SCOPE"
    return {
        "numeric_module_router_surface": NUMERIC_MODULE_REGISTRY_ROUTER_SURFACE,
        "scope_router_decision_row_id": f"OHLC-GTOS-NUMERIC-MODULE-SCOPE-DECISION-{index:05d}",
        "symbol": key[0],
        "route_session": key[1],
        "horizon_id": key[2],
        "source_component": key[3],
        "row_count": len(rows),
        "scorer_event_count": scorer_count,
        "avoid_inverse_event_count": avoid_count,
        "source_repair_event_count": repair_count,
        "context_stress_event_count": context_count,
        "score_count": len(scores),
        "score_mean": round(mean(scores), 10) if scores else None,
        "score_min": min(scores) if scores else None,
        "score_max": max(scores) if scores else None,
        "router_scope_decision": decision,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }
