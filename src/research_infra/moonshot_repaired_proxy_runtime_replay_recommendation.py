"""Route runtime replay execution outcomes into branch-local recommendations."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


RUNTIME_REPLAY_RECOMMENDATION_SURFACE = "src/research_infra/moonshot_repaired_proxy_runtime_replay_recommendation.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["runtime_replay_recommendation_surface"] = RUNTIME_REPLAY_RECOMMENDATION_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def route_class(row: dict[str, Any]) -> tuple[str, str]:
    status = normalized(row.get("replay_registry_execution_status"))
    family = normalized(row.get("registry_family"))
    if status == "REPLAY_REGISTRY_EXECUTION_CANDIDATE_TRIGGERED_BRANCH_LOCAL":
        if family == "default_off_repaired_proxy_scorer":
            return "DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL", "CARRY_DEFAULT_OFF_SIGNAL_TO_SYMBOL_REVIEW"
        if family == "avoid_redesign_repaired_proxy_comparator":
            return "AVOID_REDESIGN_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL", "CARRY_AVOID_SIGNAL_TO_SYMBOL_REVIEW"
        return "OTHER_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL", "CARRY_SIGNAL_TO_SYMBOL_REVIEW"
    if status == "REPLAY_REGISTRY_EXECUTION_CANDIDATE_EVALUATED_NO_TRIGGER":
        return "REPLAY_SIGNAL_CONTEXT_ONLY_BRANCH_LOCAL", "CARRY_CONTEXT_WITHOUT_SIGNAL"
    if status == "REPLAY_REGISTRY_EXECUTION_NO_MATCHING_RUNTIME_CANDIDATE":
        return "REPLAY_SCOPE_UNMATCHED_REVIEW_BRANCH_LOCAL", "REVIEW_SCOPE_MATCH_GAP"
    if status == "REPLAY_REGISTRY_EXECUTION_REPAIR_CONTEXT_NO_RUNTIME_CANDIDATE":
        return "REPLAY_REPAIR_CONTEXT_CARRY_BRANCH_LOCAL", "CARRY_REPAIR_CONTEXT"
    return "REPLAY_EXECUTION_STATUS_REVIEW_BRANCH_LOCAL", "REVIEW_EXECUTION_STATUS"


def replay_signal_route_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in execution_rows:
        route, action = route_class(row)
        output.append(
            boundary_row(
                {
                    "replay_signal_route_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RECOMMEND-ROUTE-{len(output) + 1:06d}"
                    ),
                    "input_replay_registry_execution_row_id": row.get("replay_registry_execution_row_id"),
                    "input_replay_score_rerun_row_id": row.get("input_replay_score_rerun_row_id"),
                    "registry_family": row.get("registry_family"),
                    "runtime_candidate_family": row.get("runtime_candidate_family"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "market_timeframe": row.get("market_timeframe"),
                    "replay_rerun_score": as_float(row.get("replay_rerun_score")),
                    "matching_registry_module_rows": int(row.get("matching_registry_module_rows") or 0),
                    "replay_registry_execution_status": row.get("replay_registry_execution_status"),
                    "replay_signal_route_class": route,
                    "replay_signal_route_action": action,
                    "replay_signal_route_status": "REPLAY_SIGNAL_ROUTE_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = as_float(row.get(field))
        if value is not None:
            values.append(value)
    return values


def recommendation_for_group(route_counts: Counter[str], registry_family: str) -> str:
    if route_counts.get("DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL", 0):
        return "BRANCH_LOCAL_DEFAULT_OFF_REPLAY_SIGNAL_RECOMMENDED_FOR_COMPARISON"
    if route_counts.get("AVOID_REDESIGN_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL", 0):
        return "BRANCH_LOCAL_AVOID_REDESIGN_REPLAY_SIGNAL_RECOMMENDED_FOR_COMPARISON"
    if route_counts.get("REPLAY_SIGNAL_CONTEXT_ONLY_BRANCH_LOCAL", 0):
        return "BRANCH_LOCAL_REPLAY_CONTEXT_RETAINED_WITHOUT_SIGNAL"
    if route_counts.get("REPLAY_SCOPE_UNMATCHED_REVIEW_BRANCH_LOCAL", 0):
        return "BRANCH_LOCAL_REPLAY_SCOPE_MATCH_REVIEW_REQUIRED"
    if route_counts.get("REPLAY_REPAIR_CONTEXT_CARRY_BRANCH_LOCAL", 0) or registry_family == "source_or_broker_geometry_repair":
        return "BRANCH_LOCAL_REPLAY_REPAIR_CONTEXT_CARRIED"
    return "BRANCH_LOCAL_REPLAY_RECOMMENDATION_REVIEW_REQUIRED"


def symbol_recommendation_rows(
    symbol_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    grouped_routes: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in route_rows:
        grouped_routes[
            (
                normalized(row.get("symbol")),
                normalized(row.get("route_session")),
                normalized(row.get("horizon_id")),
                normalized(row.get("registry_family")),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for symbol_row in symbol_rows:
        key = (
            normalized(symbol_row.get("symbol")),
            normalized(symbol_row.get("route_session")),
            normalized(symbol_row.get("horizon_id")),
            normalized(symbol_row.get("registry_family")),
        )
        rows = grouped_routes.get(key, [])
        route_counts = Counter(normalized(row.get("replay_signal_route_class")) for row in rows)
        scores = numeric_values(rows, "replay_rerun_score")
        output.append(
            boundary_row(
                {
                    "symbol_recommendation_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RECOMMEND-SYMBOL-{len(output) + 1:05d}"
                    ),
                    "input_replay_symbol_outcome_row_id": symbol_row.get("replay_symbol_outcome_row_id"),
                    "symbol": symbol_row.get("symbol"),
                    "route_session": symbol_row.get("route_session"),
                    "horizon_id": symbol_row.get("horizon_id"),
                    "registry_family": symbol_row.get("registry_family"),
                    "replay_registry_execution_rows": int(symbol_row.get("replay_registry_execution_rows") or 0),
                    "matched_registry_module_rows": int(symbol_row.get("matched_registry_module_rows") or 0),
                    "signal_route_counts": dict(sorted(route_counts.items())),
                    "score_count": len(scores),
                    "replay_rerun_score_mean": mean(scores) if scores else None,
                    "symbol_recommendation": recommendation_for_group(
                        route_counts,
                        normalized(symbol_row.get("registry_family")),
                    ),
                    "symbol_recommendation_status": "SYMBOL_REPLAY_RECOMMENDATION_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def unmatched_scope_review_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in route_rows:
        if row.get("replay_signal_route_class") != "REPLAY_SCOPE_UNMATCHED_REVIEW_BRANCH_LOCAL":
            continue
        output.append(
            boundary_row(
                {
                    "unmatched_scope_review_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RECOMMEND-UNMATCHED-{len(output) + 1:05d}"
                    ),
                    "input_replay_signal_route_row_id": row.get("replay_signal_route_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "replay_rerun_score": row.get("replay_rerun_score"),
                    "unmatched_scope_review_status": "UNMATCHED_REPLAY_SCOPE_REVIEW_REQUIRED_BRANCH_LOCAL",
                }
            )
        )
    return output


def repair_context_recommendation_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in route_rows:
        if row.get("replay_signal_route_class") != "REPLAY_REPAIR_CONTEXT_CARRY_BRANCH_LOCAL":
            continue
        output.append(
            boundary_row(
                {
                    "repair_context_recommendation_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RECOMMEND-REPAIR-{len(output) + 1:05d}"
                    ),
                    "input_replay_signal_route_row_id": row.get("replay_signal_route_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "repair_context_recommendation": "CARRY_REPLAY_REPAIR_CONTEXT_TO_SOURCE_SCOPE_REVIEW",
                    "repair_context_recommendation_status": "REPLAY_REPAIR_CONTEXT_RECOMMENDATION_MATERIALIZED",
                }
            )
        )
    return output


def nonregistration_recommendation_rows(nonregistration_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in nonregistration_rows:
        output.append(
            boundary_row(
                {
                    "nonregistration_recommendation_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RECOMMEND-NONREG-{len(output) + 1:05d}"
                    ),
                    "input_nonregistration_replay_carry_row_id": row.get("nonregistration_replay_carry_row_id"),
                    "input_comparator_execution_row_id": row.get("input_comparator_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "review_action": row.get("review_action"),
                    "nonregistration_recommendation_status": "NONREGISTRATION_CONTEXT_RECOMMENDATION_CARRIED_BRANCH_LOCAL",
                }
            )
        )
    return output


def system_recommendation_rows(symbol_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recommendation_counts = Counter(normalized(row.get("symbol_recommendation")) for row in symbol_rows)
    route_counts = Counter(normalized(row.get("replay_signal_route_class")) for row in route_rows)
    return [
        boundary_row(
            {
                "system_recommendation_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RECOMMEND-SYSTEM-0001",
                "symbol_recommendation_rows": len(symbol_rows),
                "replay_signal_route_rows": len(route_rows),
                "symbol_recommendation_counts": dict(sorted(recommendation_counts.items())),
                "replay_signal_route_counts": dict(sorted(route_counts.items())),
                "system_recommendation": (
                    "Carry branch-local replay signal candidates forward for comparison, preserve context-only rows, "
                    "and keep unmatched plus repair-context rows in explicit review ledgers."
                ),
                "system_recommendation_status": "RUNTIME_REPLAY_SYSTEM_RECOMMENDATION_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def recommendation_bucket_rows(
    route_rows: list[dict[str, Any]],
    symbol_rows: list[dict[str, Any]],
    unmatched_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
    nonregistration_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("replay_signal_route_class", route_rows, "replay_signal_route_class"),
        ("symbol_recommendation", symbol_rows, "symbol_recommendation"),
        ("symbol_recommendation_status", symbol_rows, "symbol_recommendation_status"),
        ("unmatched_scope_review_status", unmatched_rows, "unmatched_scope_review_status"),
        ("repair_context_recommendation_status", repair_rows, "repair_context_recommendation_status"),
        ("nonregistration_recommendation_status", nonregistration_rows, "nonregistration_recommendation_status"),
        ("system_recommendation_status", system_rows, "system_recommendation_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "recommendation_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RECOMMEND-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
