"""Runnable repaired-proxy scope scorer for moonshot branch-local research."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any, Iterable


REPAIRED_PROXY_SCOPE_SCORER_SURFACE = "src/research_infra/moonshot_repaired_proxy_scope_scorer.py"


def to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def aggregate_scope_key(row: dict[str, Any]) -> str:
    existing = row.get("aggregate_scope_key")
    if existing:
        return str(existing)
    return "|".join(
        f"{field}={row.get(field) or ''}"
        for field in ("symbol", "route_session", "horizon_id", "source_component")
    )


def registry_role(implementation_decision: str) -> str:
    if implementation_decision == "IMPLEMENT_SCOPE_DEFAULT_OFF_PROXY_SCORER_WITH_SOURCE_REPAIR_GUARDS":
        return "DEFAULT_OFF_REPAIRED_PROXY_SCORER_SCOPE"
    if implementation_decision == "IMPLEMENT_SCOPE_AVOID_OR_REDESIGN_FROM_REPAIRED_NEGATIVE_PROXY":
        return "AVOID_OR_REDESIGN_REPAIRED_PROXY_SCOPE"
    if implementation_decision == "SOURCE_OR_BROKER_GEOMETRY_REPAIR_REMAINS_REQUIRED_FOR_SCOPE":
        return "SOURCE_OR_BROKER_GEOMETRY_REPAIR_REQUIRED_SCOPE"
    return "CONTEXT_ONLY_REPAIRED_PROXY_SCOPE"


def registry_row_from_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    role = registry_role(str(row.get("implementation_decision") or ""))
    repaired_mean = to_float(row.get("scope_repaired_proxy_mean"))
    event_mean = to_float(row.get("scope_event_score_mean"))
    score = repaired_mean if repaired_mean is not None else event_mean
    return {
        "repaired_proxy_scope_scorer_surface": REPAIRED_PROXY_SCOPE_SCORER_SURFACE,
        "repaired_proxy_scope_registry_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCOPE-REGISTRY-{index:05d}",
        "input_broker_source_implementation_decision_row_id": row.get("broker_source_implementation_decision_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "aggregate_scope_key": aggregate_scope_key(row),
        "registry_role": role,
        "implementation_decision": row.get("implementation_decision"),
        "scope_repaired_proxy_mean": repaired_mean,
        "scope_event_score_mean": event_mean,
        "scope_score_for_application": score,
        "scope_event_rows": row.get("scope_event_rows"),
        "scope_repair_rows": row.get("scope_repair_rows"),
        "scope_positive_repaired_proxy_rows": row.get("scope_positive_repaired_proxy_rows"),
        "scope_negative_repaired_proxy_rows": row.get("scope_negative_repaired_proxy_rows"),
        "repair_queue_counts": row.get("repair_queue_counts") or {},
        "hard_repair_decision_counts": row.get("hard_repair_decision_counts") or {},
        "required_guards": required_guards_for_role(role),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def required_guards_for_role(role: str) -> list[str]:
    if role == "DEFAULT_OFF_REPAIRED_PROXY_SCORER_SCOPE":
        return ["source_repair_guard", "avoid_inverse_scope_guard", "exact_geometry_absence_guard"]
    if role == "AVOID_OR_REDESIGN_REPAIRED_PROXY_SCOPE":
        return ["avoid_scope_guard", "source_repair_guard"]
    if role == "SOURCE_OR_BROKER_GEOMETRY_REPAIR_REQUIRED_SCOPE":
        return ["fail_closed_until_direct_geometry_identifier_or_source_rebuild"]
    return ["context_only_guard"]


def build_registry(registry_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(registry_rows)
    by_scope = {row["aggregate_scope_key"]: row for row in rows}
    return {
        "repaired_proxy_scope_scorer_surface": REPAIRED_PROXY_SCOPE_SCORER_SURFACE,
        "registry_rows": rows,
        "by_scope": by_scope,
    }


def repair_proxy_mean(repair_rows: list[dict[str, Any]]) -> float | None:
    values = [
        to_float(row.get("source_repaired_proxy_value"))
        for row in repair_rows
        if to_float(row.get("source_repaired_proxy_value")) is not None
    ]
    return round(mean(values), 10) if values else None


def score_event_with_repaired_scope(
    event_row: dict[str, Any],
    registry_row: dict[str, Any] | None,
    repair_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    repair_rows = repair_rows or []
    if registry_row is None:
        return {
            "repaired_proxy_event_status": "REPAIRED_PROXY_EVENT_NO_REGISTERED_SCOPE",
            "repaired_proxy_event_action": "fail_closed_unregistered_scope",
            "repaired_proxy_event_score": None,
            "repaired_proxy_event_score_source": "no_registered_scope",
            "emits_default_off_score": False,
            "emits_avoid_or_redesign": False,
            "emits_source_repair_required": True,
        }
    event_key = aggregate_scope_key(event_row)
    if event_key != registry_row.get("aggregate_scope_key"):
        return {
            "repaired_proxy_event_status": "REPAIRED_PROXY_EVENT_SCOPE_MISMATCH",
            "repaired_proxy_event_action": "ignore_scope_mismatch",
            "repaired_proxy_event_score": None,
            "repaired_proxy_event_score_source": "scope_mismatch",
            "emits_default_off_score": False,
            "emits_avoid_or_redesign": False,
            "emits_source_repair_required": False,
        }
    repaired_score = repair_proxy_mean(repair_rows)
    event_score = to_float(event_row.get("shadow_score"))
    scope_score = to_float(registry_row.get("scope_score_for_application"))
    if repaired_score is not None:
        score = repaired_score
        score_source = "repair_result_source_repaired_proxy_mean"
    elif event_score is not None:
        score = event_score
        score_source = "numeric_shadow_event_score"
    else:
        score = scope_score
        score_source = "scope_score_for_application"
    role = str(registry_row.get("registry_role") or "")
    if role == "DEFAULT_OFF_REPAIRED_PROXY_SCORER_SCOPE":
        return {
            "repaired_proxy_event_status": "REPAIRED_PROXY_EVENT_DEFAULT_OFF_SCORE_EMITTED",
            "repaired_proxy_event_action": "score_default_off_with_source_repair_guards",
            "repaired_proxy_event_score": score,
            "repaired_proxy_event_score_source": score_source,
            "emits_default_off_score": True,
            "emits_avoid_or_redesign": False,
            "emits_source_repair_required": False,
        }
    if role == "AVOID_OR_REDESIGN_REPAIRED_PROXY_SCOPE":
        return {
            "repaired_proxy_event_status": "REPAIRED_PROXY_EVENT_AVOID_OR_REDESIGN_EMITTED",
            "repaired_proxy_event_action": "emit_avoid_or_redesign_comparator",
            "repaired_proxy_event_score": score,
            "repaired_proxy_event_score_source": score_source,
            "emits_default_off_score": False,
            "emits_avoid_or_redesign": True,
            "emits_source_repair_required": False,
        }
    if role == "SOURCE_OR_BROKER_GEOMETRY_REPAIR_REQUIRED_SCOPE":
        return {
            "repaired_proxy_event_status": "REPAIRED_PROXY_EVENT_SOURCE_REPAIR_REQUIRED",
            "repaired_proxy_event_action": "fail_closed_and_repair_source_or_broker_geometry",
            "repaired_proxy_event_score": None,
            "repaired_proxy_event_score_source": "source_or_broker_geometry_required",
            "emits_default_off_score": False,
            "emits_avoid_or_redesign": False,
            "emits_source_repair_required": True,
        }
    return {
        "repaired_proxy_event_status": "REPAIRED_PROXY_EVENT_CONTEXT_ONLY",
        "repaired_proxy_event_action": "merge_context_guard_input",
        "repaired_proxy_event_score": score,
        "repaired_proxy_event_score_source": score_source,
        "emits_default_off_score": False,
        "emits_avoid_or_redesign": False,
        "emits_source_repair_required": False,
    }


def event_application_row(
    event_row: dict[str, Any],
    registry_row: dict[str, Any] | None,
    repair_rows: list[dict[str, Any]],
    index: int,
) -> dict[str, Any]:
    scored = score_event_with_repaired_scope(event_row, registry_row, repair_rows)
    return {
        "repaired_proxy_scope_scorer_surface": REPAIRED_PROXY_SCOPE_SCORER_SURFACE,
        "repaired_proxy_event_application_row_id": f"OHLC-GTOS-REPAIRED-PROXY-EVENT-APP-{index:06d}",
        "input_shadow_scorer_event_score_row_id": event_row.get("shadow_scorer_event_score_row_id"),
        "input_numeric_result_row_id": event_row.get("input_numeric_result_row_id"),
        "input_repaired_proxy_scope_registry_row_id": (registry_row or {}).get("repaired_proxy_scope_registry_row_id"),
        "symbol": event_row.get("symbol"),
        "route_session": event_row.get("route_session"),
        "horizon_id": event_row.get("horizon_id"),
        "primitive_flag": event_row.get("primitive_flag"),
        "source_component": event_row.get("source_component"),
        "aggregate_scope_key": aggregate_scope_key(event_row),
        "registry_role": (registry_row or {}).get("registry_role"),
        "source_repair_rows_for_event": len(repair_rows),
        "event_shadow_score": event_row.get("shadow_score"),
        "event_shadow_score_basis": event_row.get("shadow_score_basis"),
        "repair_proxy_mean_for_event": repair_proxy_mean(repair_rows),
        **scored,
        "required_guards": (registry_row or {}).get("required_guards") or ["fail_closed_unregistered_scope"],
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def application_summary_row(
    rows: list[dict[str, Any]],
    group_values: tuple[Any, ...],
    group_fields: tuple[str, ...],
    index: int,
    summary_family: str,
) -> dict[str, Any]:
    scores = [
        to_float(row.get("repaired_proxy_event_score"))
        for row in rows
        if to_float(row.get("repaired_proxy_event_score")) is not None
    ]
    output = {
        "repaired_proxy_application_summary_row_id": f"OHLC-GTOS-REPAIRED-PROXY-APP-SUMMARY-{index:05d}",
        "repaired_proxy_scope_scorer_surface": REPAIRED_PROXY_SCOPE_SCORER_SURFACE,
        "summary_family": summary_family,
        "row_count": len(rows),
        "score_rows": len(scores),
        "score_mean": round(mean(scores), 10) if scores else None,
        "score_min": min(scores) if scores else None,
        "score_max": max(scores) if scores else None,
        "event_status_counts": dict(sorted(Counter(str(row.get("repaired_proxy_event_status")) for row in rows).items())),
        "registry_role_counts": dict(sorted(Counter(str(row.get("registry_role")) for row in rows).items())),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }
    for field, value in zip(group_fields, group_values):
        output[field] = value
    return output
