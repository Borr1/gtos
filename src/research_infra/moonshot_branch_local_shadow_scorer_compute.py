"""Callable branch-local shadow scorer and source-repair compute helpers.

The functions in this module consume the numeric moonshot result tables and the
router recommendation ledgers. They are research-only: they compute exact-R
when broker geometry is present, proxy-R when only replay/proxy geometry exists,
and source-repair queues when exact geometry is absent.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any, Iterable


SHADOW_SCORER_COMPUTE_SURFACE = "src/research_infra/moonshot_branch_local_shadow_scorer_compute.py"

EXACT_R_REQUIRED_FIELDS = (
    "trade_direction",
    "executed_entry_price",
    "executed_exit_price",
    "executed_stop_price",
)


def to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def event_scope_key(row: dict[str, Any]) -> str:
    existing = row.get("mechanical_scope_key") or row.get("numeric_scope_key")
    if existing:
        return str(existing)
    return "|".join(
        f"{field}={row.get(field) or ''}"
        for field in ("symbol", "route_session", "horizon_id", "primitive_flag", "source_component")
    )


def aggregate_scope_key(row: dict[str, Any]) -> str:
    return "|".join(
        f"{field}={row.get(field) or ''}"
        for field in ("symbol", "route_session", "horizon_id", "source_component")
    )


def cost_adjustment_r(row: dict[str, Any]) -> dict[str, Any]:
    """Return only explicit R-denominated friction adjustments."""

    components = {
        key: to_float(row.get(key))
        for key in ("spread_cost_r", "slippage_r", "commission_r", "swap_r")
        if to_float(row.get(key)) is not None
    }
    total = round(sum(abs(value) for value in components.values()), 10)
    return {
        "cost_adjustment_r": total,
        "cost_adjustment_components": components,
        "cost_adjustment_status": (
            "R_DENOMINATED_COST_FIELDS_APPLIED" if components else "NO_R_DENOMINATED_COST_FIELD_PRESENT"
        ),
    }


def exact_r_from_geometry(row: dict[str, Any]) -> dict[str, Any]:
    """Compute exact R if broker execution geometry is available in the row."""

    missing = [field for field in EXACT_R_REQUIRED_FIELDS if to_float(row.get(field)) is None and not row.get(field)]
    if missing:
        return {
            "exact_r_compute_status": "EXACT_R_NOT_COMPUTABLE_MISSING_GEOMETRY_FIELDS",
            "exact_r_value": None,
            "exact_r_missing_fields": missing,
            "exact_r_source": "current_row_geometry",
        }
    direction = str(row.get("trade_direction") or "").upper()
    entry = to_float(row.get("executed_entry_price"))
    exit_price = to_float(row.get("executed_exit_price"))
    stop = to_float(row.get("executed_stop_price"))
    if entry is None or exit_price is None or stop is None:
        return {
            "exact_r_compute_status": "EXACT_R_NOT_COMPUTABLE_MISSING_GEOMETRY_FIELDS",
            "exact_r_value": None,
            "exact_r_missing_fields": list(EXACT_R_REQUIRED_FIELDS),
            "exact_r_source": "current_row_geometry",
        }
    risk_distance = abs(entry - stop)
    if risk_distance <= 0:
        return {
            "exact_r_compute_status": "EXACT_R_NOT_COMPUTABLE_ZERO_OR_NEGATIVE_RISK_DISTANCE",
            "exact_r_value": None,
            "exact_r_missing_fields": [],
            "exact_r_source": "current_row_geometry",
        }
    if direction in {"BUY", "LONG"}:
        raw_r = (exit_price - entry) / risk_distance
    elif direction in {"SELL", "SHORT"}:
        raw_r = (entry - exit_price) / risk_distance
    else:
        return {
            "exact_r_compute_status": "EXACT_R_NOT_COMPUTABLE_UNKNOWN_DIRECTION",
            "exact_r_value": None,
            "exact_r_missing_fields": ["trade_direction"],
            "exact_r_source": "current_row_geometry",
        }
    cost = cost_adjustment_r(row)
    exact = round(raw_r - cost["cost_adjustment_r"], 10)
    return {
        "exact_r_compute_status": "EXACT_R_COMPUTED_FROM_BROKER_GEOMETRY",
        "exact_r_value": exact,
        "exact_r_missing_fields": [],
        "exact_r_source": "current_row_geometry",
        "raw_exact_r_before_cost": round(raw_r, 10),
        **cost,
    }


def proxy_score_value(row: dict[str, Any]) -> float | None:
    for field in ("decision_proxy_value", "proxy_r_value", "expectancy_proxy_value", "registry_surface_score"):
        value = to_float(row.get(field))
        if value is not None:
            return value
    return None


def scored_numeric_event(row: dict[str, Any], index: int) -> dict[str, Any]:
    exact = exact_r_from_geometry(row)
    proxy = proxy_score_value(row)
    cost = cost_adjustment_r(row)
    adjusted_proxy = None if proxy is None else round(proxy - cost["cost_adjustment_r"], 10)
    if exact["exact_r_value"] is not None:
        score_basis = "exact_r"
        score = exact["exact_r_value"]
    elif adjusted_proxy is not None:
        score_basis = "proxy_r"
        score = adjusted_proxy
    else:
        score_basis = "no_scalar"
        score = None
    decision = shadow_decision(row, score, score_basis)
    return {
        "shadow_scorer_compute_surface": SHADOW_SCORER_COMPUTE_SURFACE,
        "shadow_scorer_event_score_row_id": f"OHLC-GTOS-NUMERIC-SHADOW-SCORER-EVENT-{index:06d}",
        "input_numeric_result_row_id": row.get("numeric_result_row_id") or row.get("input_numeric_result_row_id"),
        "input_integrated_result_execution_row_id": row.get("input_integrated_result_execution_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "event_scope_key": event_scope_key(row),
        "aggregate_scope_key": aggregate_scope_key(row),
        "proxy_r_value": proxy,
        "expectancy_proxy_value": to_float(row.get("expectancy_proxy_value")),
        "cost_stress_status": row.get("cost_stress_status"),
        "cost_adjustment_r": cost["cost_adjustment_r"],
        "cost_adjustment_status": cost["cost_adjustment_status"],
        "cost_stress_adjusted_proxy_r": adjusted_proxy,
        "target_stop_order_class": row.get("target_stop_order_class"),
        "proxy_r_class": row.get("proxy_r_class"),
        "exact_r_compute_status": exact["exact_r_compute_status"],
        "exact_r_value": exact["exact_r_value"],
        "exact_r_missing_fields": exact["exact_r_missing_fields"],
        "shadow_score_basis": score_basis,
        "shadow_score": score,
        "shadow_decision": decision,
        "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def shadow_decision(row: dict[str, Any], score: float | None, score_basis: str) -> str:
    decision = str(row.get("keep_kill_redesign_implement_decision") or "")
    proxy_class = str(row.get("proxy_r_class") or "")
    if score_basis == "exact_r" and score is not None:
        if score > 0:
            return "SCORE_DEFAULT_OFF_EXACT_R_RESEARCH_EVENT"
        if score < 0:
            return "CONVERT_EXACT_R_NEGATIVE_TO_AVOID_OR_FAILURE_FILTER"
        return "MERGE_FLAT_EXACT_R_AS_CONTEXT"
    if proxy_class in {"STRONG_POSITIVE_PROXY_R", "POSITIVE_PROXY_R"} or decision.startswith("KEEP_"):
        return "SCORE_DEFAULT_OFF_PROXY_R_RESEARCH_EVENT"
    if proxy_class in {"STRONG_NEGATIVE_PROXY_R", "NEGATIVE_PROXY_R"} or "NEGATIVE" in decision:
        return "SCORE_AVOID_INVERSE_OR_FAILURE_FILTER_PROXY_EVENT"
    if score is None or "SOURCE_GEOMETRY_REPAIR" in decision or "NO_NUMERIC_PROXY" in proxy_class:
        return "QUEUE_SOURCE_GEOMETRY_REPAIR_BEFORE_SCALAR_USE"
    return "MERGE_CONTEXT_OR_STRESS_GUARD_EVENT"


def repair_queue_row(proof_row: dict[str, Any], index: int) -> dict[str, Any]:
    system_decision = str(proof_row.get("source_repair_system_decision") or "")
    if system_decision == "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R":
        queue = "BROKER_EXECUTION_GEOMETRY_EXACT_R_REPAIR_QUEUE"
    elif system_decision == "SOURCE_JOIN_REPAIR_REQUIRED_WITH_CURRENT_PACKET_ABSENCE_PROOF":
        queue = "SOURCE_JOIN_REPAIR_QUEUE"
    elif system_decision == "BROKER_GEOMETRY_ATTACHMENT_REQUIRED_FOR_EXACT_SPREAD_PROXY":
        queue = "BROKER_GEOMETRY_ATTACHMENT_FOR_EXACT_SPREAD_PROXY_QUEUE"
    else:
        queue = "REPLAY_PROXY_REPAIR_QUEUE"
    return {
        "shadow_scorer_compute_surface": SHADOW_SCORER_COMPUTE_SURFACE,
        "source_repair_queue_row_id": f"OHLC-GTOS-NUMERIC-SHADOW-SCORER-REPAIR-{index:06d}",
        "input_source_repair_proof_row_id": proof_row.get("source_repair_proof_row_id"),
        "input_numeric_result_row_id": proof_row.get("input_numeric_result_row_id"),
        "symbol": proof_row.get("symbol"),
        "route_session": proof_row.get("route_session"),
        "horizon_id": proof_row.get("horizon_id"),
        "primitive_flag": proof_row.get("primitive_flag"),
        "source_component": proof_row.get("source_component"),
        "source_row_id": proof_row.get("source_row_id"),
        "repair_queue": queue,
        "repair_action": proof_row.get("repair_action"),
        "source_repair_system_decision": system_decision,
        "exact_repair_possible_from_current_packet": proof_row.get("exact_repair_possible_from_current_packet"),
        "missing_field_count": proof_row.get("missing_field_count"),
        "exact_missing_field_proof": proof_row.get("exact_missing_field_proof") or [],
        "opportunity_preserved": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def build_shadow_scorer_registry(
    event_score_rows: Iterable[dict[str, Any]],
    repair_queue_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    event_by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    repair_by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in event_score_rows:
        event_by_scope[str(row.get("aggregate_scope_key") or "")].append(row)
    for row in repair_queue_rows:
        repair_by_scope[aggregate_scope_key(row)].append(row)
    return {
        "shadow_scorer_compute_surface": SHADOW_SCORER_COMPUTE_SURFACE,
        "event_by_scope": dict(event_by_scope),
        "repair_by_scope": dict(repair_by_scope),
    }


def score_scope_event(scope_row: dict[str, Any], registry: dict[str, Any], index: int = 0) -> dict[str, Any]:
    key = aggregate_scope_key(scope_row)
    event_rows = registry.get("event_by_scope", {}).get(key, [])
    repair_rows = registry.get("repair_by_scope", {}).get(key, [])
    positive_scores = [row["shadow_score"] for row in event_rows if isinstance(row.get("shadow_score"), (int, float)) and row["shadow_score"] > 0]
    negative_scores = [row["shadow_score"] for row in event_rows if isinstance(row.get("shadow_score"), (int, float)) and row["shadow_score"] < 0]
    no_scalar_count = sum(1 for row in event_rows if row.get("shadow_score_basis") == "no_scalar")
    positive_sum = round(sum(positive_scores), 10)
    negative_sum = round(sum(negative_scores), 10)
    net_score = round(positive_sum + negative_sum, 10)
    repair_counts = defaultdict(int)
    for row in repair_rows:
        repair_counts[str(row.get("repair_queue"))] += 1
    if repair_rows and not positive_scores and not negative_scores:
        decision = "SOURCE_REPAIR_FIRST_NO_CURRENT_SCALAR"
    elif abs(negative_sum) >= positive_sum and negative_scores:
        decision = "AVOID_INVERSE_OR_FAILURE_FILTER_FIRST"
    elif positive_sum > 0 and net_score > 0:
        decision = "DEFAULT_OFF_SCORER_WITH_AVOID_AND_SOURCE_GUARDS"
    elif no_scalar_count or repair_rows:
        decision = "REPAIR_OR_CONTEXT_GUARD_BEFORE_SCORER_USE"
    else:
        decision = "CONTEXT_GUARD_ONLY_OR_RECHECK"
    scores = [row["shadow_score"] for row in event_rows if isinstance(row.get("shadow_score"), (int, float))]
    return {
        "shadow_scorer_compute_surface": SHADOW_SCORER_COMPUTE_SURFACE,
        "scope_score_decision_row_id": f"OHLC-GTOS-NUMERIC-SHADOW-SCORER-SCOPE-{index:05d}",
        "input_scope_system_decision_row_id": scope_row.get("scope_system_decision_row_id"),
        "symbol": scope_row.get("symbol"),
        "route_session": scope_row.get("route_session"),
        "horizon_id": scope_row.get("horizon_id"),
        "source_component": scope_row.get("source_component"),
        "aggregate_scope_key": key,
        "scope_event_rows": len(event_rows),
        "scope_repair_rows": len(repair_rows),
        "positive_score_rows": len(positive_scores),
        "negative_score_rows": len(negative_scores),
        "no_scalar_rows": no_scalar_count,
        "positive_score_sum": positive_sum,
        "negative_score_sum": negative_sum,
        "net_shadow_score": net_score,
        "mean_shadow_score": round(mean(scores), 10) if scores else None,
        "repair_queue_counts": dict(sorted(repair_counts.items())),
        "scope_shadow_decision": decision,
        "upstream_router_scope_decision": scope_row.get("router_scope_decision"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }
