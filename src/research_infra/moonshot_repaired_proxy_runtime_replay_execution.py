"""Execute repaired-proxy runtime registry modules against replay score rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from src.research_infra.moonshot_repaired_proxy_runtime_candidate_registry import (
    evaluate_runtime_candidate_event,
    scope_matches,
)


RUNTIME_REPLAY_EXECUTION_SURFACE = "src/research_infra/moonshot_repaired_proxy_runtime_replay_execution.py"
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
    output["runtime_replay_execution_surface"] = RUNTIME_REPLAY_EXECUTION_SURFACE
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


def replay_family_to_candidate_family(registry_family: str) -> str:
    if registry_family == "default_off_repaired_proxy_scorer":
        return "branch_local_default_off_repaired_proxy_scorer_candidate"
    if registry_family == "avoid_redesign_repaired_proxy_comparator":
        return "branch_local_avoid_redesign_repaired_proxy_comparator_candidate"
    return ""


def registry_group_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalized(row.get("runtime_candidate_family")),
        normalized(row.get("symbol")),
        normalized(row.get("source_component")),
    )


def registry_index(registry_rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    output: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in registry_rows:
        output[registry_group_key(row)].append(row)
    return output


def replay_event(row: dict[str, Any]) -> dict[str, Any]:
    score = as_float(row.get("replay_rerun_score"))
    return {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "score_context_index": score,
        "net_proxy_r": score,
    }


def matching_registry_rows(
    replay_row: dict[str, Any],
    index_by_family_symbol_source: dict[tuple[str, str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    candidate_family = replay_family_to_candidate_family(normalized(replay_row.get("registry_family")))
    if not candidate_family:
        return []
    candidates = index_by_family_symbol_source.get(
        (
            candidate_family,
            normalized(replay_row.get("symbol")),
            normalized(replay_row.get("source_component")),
        ),
        [],
    )
    event = replay_event(replay_row)
    return [row for row in candidates if scope_matches(row, event)]


def executed_outcome_counts(replay_row: dict[str, Any], matches: list[dict[str, Any]]) -> Counter[str]:
    event = replay_event(replay_row)
    return Counter(
        normalized(evaluate_runtime_candidate_event(registry_row, event).get("candidate_event_outcome"))
        for registry_row in matches
    )


def execution_status(replay_row: dict[str, Any], matches: list[dict[str, Any]], outcomes: Counter[str]) -> tuple[str, str]:
    family = normalized(replay_row.get("registry_family"))
    score = as_float(replay_row.get("replay_rerun_score"))
    if family == "source_or_broker_geometry_repair":
        return "REPLAY_REGISTRY_EXECUTION_REPAIR_CONTEXT_NO_RUNTIME_CANDIDATE", "CARRY_REPAIR_CONTEXT_SEPARATELY"
    if score is None:
        return "REPLAY_REGISTRY_EXECUTION_MISSING_REPLAY_SCORE", "CARRY_REPLAY_ROW_WITHOUT_MODULE_SCORE"
    if not matches:
        return "REPLAY_REGISTRY_EXECUTION_NO_MATCHING_RUNTIME_CANDIDATE", "CARRY_UNMATCHED_REPLAY_ROW_FOR_SCOPE_REVIEW"
    accepted = outcomes.get("DEFAULT_OFF_SCORER_EVENT_ACCEPTED_BRANCH_LOCAL", 0)
    triggered = outcomes.get("AVOID_REDESIGN_COMPARATOR_EVENT_TRIGGERED_BRANCH_LOCAL", 0)
    if accepted or triggered:
        return "REPLAY_REGISTRY_EXECUTION_CANDIDATE_TRIGGERED_BRANCH_LOCAL", "KEEP_REPLAY_MODULE_SIGNAL"
    return "REPLAY_REGISTRY_EXECUTION_CANDIDATE_EVALUATED_NO_TRIGGER", "KEEP_REPLAY_MODULE_CONTEXT"


def replay_registry_execution_rows(
    score_rows: list[dict[str, Any]], registry_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    index = registry_index(registry_rows)
    output: list[dict[str, Any]] = []
    for score_row in score_rows:
        matches = matching_registry_rows(score_row, index)
        outcomes = executed_outcome_counts(score_row, matches)
        status, action = execution_status(score_row, matches, outcomes)
        output.append(
            boundary_row(
                {
                    "replay_registry_execution_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-EXEC-{len(output) + 1:06d}"
                    ),
                    "input_replay_score_rerun_row_id": score_row.get("replay_score_rerun_row_id"),
                    "input_replay_numeric_event_row_id": score_row.get("input_replay_numeric_event_row_id"),
                    "input_registry_scope_row_id": score_row.get("input_registry_scope_row_id"),
                    "registry_family": score_row.get("registry_family"),
                    "runtime_candidate_family": replay_family_to_candidate_family(
                        normalized(score_row.get("registry_family"))
                    ),
                    "symbol": score_row.get("symbol"),
                    "route_session": score_row.get("route_session"),
                    "horizon_id": score_row.get("horizon_id"),
                    "source_component": score_row.get("source_component"),
                    "market_timeframe": score_row.get("market_timeframe"),
                    "market_source_path": score_row.get("market_source_path"),
                    "replay_rerun_score": as_float(score_row.get("replay_rerun_score")),
                    "matching_registry_module_rows": len(matches),
                    "matched_registry_module_row_ids": [row.get("registry_module_row_id") for row in matches],
                    "module_event_outcome_counts": dict(sorted(outcomes.items())),
                    "replay_registry_execution_status": status,
                    "replay_registry_execution_action": action,
                }
            )
        )
    return output


def replay_module_match_rows(score_rows: list[dict[str, Any]], registry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = registry_index(registry_rows)
    output: list[dict[str, Any]] = []
    for score_row in score_rows:
        matches = matching_registry_rows(score_row, index)
        event = replay_event(score_row)
        for registry_row in matches:
            result = evaluate_runtime_candidate_event(registry_row, event)
            output.append(
                boundary_row(
                    {
                        "replay_module_match_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-MATCH-{len(output) + 1:06d}"
                        ),
                        "input_replay_score_rerun_row_id": score_row.get("replay_score_rerun_row_id"),
                        "input_registry_module_row_id": registry_row.get("registry_module_row_id"),
                        "symbol": score_row.get("symbol"),
                        "route_session": score_row.get("route_session"),
                        "horizon_id": score_row.get("horizon_id"),
                        "source_component": score_row.get("source_component"),
                        "runtime_candidate_family": registry_row.get("runtime_candidate_family"),
                        "runtime_candidate_kind": registry_row.get("runtime_candidate_kind"),
                        "replay_rerun_score": as_float(score_row.get("replay_rerun_score")),
                        "module_event_score": result.get("candidate_event_score"),
                        "module_event_outcome": result.get("candidate_event_outcome"),
                        "replay_module_match_status": "RUNTIME_REGISTRY_MODULE_REPLAY_MATCH_EXECUTED_BRANCH_LOCAL",
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


def replay_symbol_outcome_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in execution_rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("route_session")),
                normalized(row.get("horizon_id")),
                normalized(row.get("registry_family")),
            )
        ].append(row)
    output: list[dict[str, Any]] = []
    for (symbol, route_session, horizon_id, registry_family), rows in sorted(grouped.items()):
        scores = numeric_values(rows, "replay_rerun_score")
        status_counts = Counter(normalized(row.get("replay_registry_execution_status")) for row in rows)
        output.append(
            boundary_row(
                {
                    "replay_symbol_outcome_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-SYMBOL-{len(output) + 1:05d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "registry_family": registry_family,
                    "replay_registry_execution_rows": len(rows),
                    "matched_registry_module_rows": sum(int(row.get("matching_registry_module_rows") or 0) for row in rows),
                    "score_count": len(scores),
                    "replay_rerun_score_mean": mean(scores) if scores else None,
                    "replay_rerun_score_min": min(scores) if scores else None,
                    "replay_rerun_score_max": max(scores) if scores else None,
                    "execution_status_counts": dict(sorted(status_counts.items())),
                    "replay_symbol_outcome_status": "REPLAY_REGISTRY_SYMBOL_OUTCOME_ROLLED_UP_BRANCH_LOCAL",
                }
            )
        )
    return output


def nonregistration_replay_carry_rows(nonregistration_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in nonregistration_rows:
        output.append(
            boundary_row(
                {
                    "nonregistration_replay_carry_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-NONREG-{len(output) + 1:05d}"
                    ),
                    "input_nonregistration_registry_review_row_id": row.get("nonregistration_registry_review_row_id"),
                    "input_comparator_execution_row_id": row.get("input_comparator_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "review_action": row.get("review_action"),
                    "bridge_rows": int(row.get("bridge_rows") or 0),
                    "nonregistration_replay_carry_status": "NONREGISTRATION_CONTEXT_CARRIED_OUTSIDE_REPLAY_EXECUTION",
                }
            )
        )
    return output


def replay_execution_bucket_rows(
    execution_rows: list[dict[str, Any]],
    match_rows: list[dict[str, Any]],
    symbol_rows: list[dict[str, Any]],
    nonregistration_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("replay_registry_execution_status", execution_rows, "replay_registry_execution_status"),
        ("replay_registry_execution_action", execution_rows, "replay_registry_execution_action"),
        ("registry_family", execution_rows, "registry_family"),
        ("module_event_outcome", match_rows, "module_event_outcome"),
        ("replay_module_match_status", match_rows, "replay_module_match_status"),
        ("replay_symbol_outcome_status", symbol_rows, "replay_symbol_outcome_status"),
        ("nonregistration_replay_carry_status", nonregistration_rows, "nonregistration_replay_carry_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "replay_execution_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
