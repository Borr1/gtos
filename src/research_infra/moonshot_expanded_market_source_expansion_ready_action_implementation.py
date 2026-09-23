"""Convert ready action executions into branch-local implementation candidates."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_ready_action_implementation.py"
)


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": "concrete_branch_local_research_boundary_v1",
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_source_expansion_ready_action_implementation_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION
    )
    output["research_boundary"] = research_boundary()
    return output


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def implementation_kind(row: dict[str, Any]) -> str:
    action_class = str(row.get("follow_inverse_default_off_avoid_class") or "")
    if action_class == "follow":
        return "branch-local-expanded-market-follow-implementation-candidate"
    if action_class == "avoid":
        return "branch-local-expanded-market-avoid-implementation-candidate"
    return "branch-local-expanded-market-redesign-implementation-task"


def implementation_status(kind: str) -> str:
    if kind == "branch-local-expanded-market-follow-implementation-candidate":
        return "SOURCE_EXPANSION_READY_ACTION_FOLLOW_IMPLEMENTATION_CANDIDATE"
    if kind == "branch-local-expanded-market-avoid-implementation-candidate":
        return "SOURCE_EXPANSION_READY_ACTION_AVOID_IMPLEMENTATION_CANDIDATE"
    return "SOURCE_EXPANSION_READY_ACTION_REDESIGN_IMPLEMENTATION_TASK"


def implementation_decision(kind: str) -> str:
    if kind == "branch-local-expanded-market-follow-implementation-candidate":
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_FOLLOW_READY_ACTION"
    if kind == "branch-local-expanded-market-avoid-implementation-candidate":
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_AVOID_READY_ACTION"
    return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION"


def ready_implementation_candidate_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    kind = implementation_kind(row)
    expression = {
        "implementation_kind": kind,
        "match_scope": {
            "symbol_family": row.get("symbol_family"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path_sha256": row.get("source_path_sha256"),
            "source_file_sha256": row.get("source_file_sha256"),
        },
        "expected_action": row.get("follow_inverse_default_off_avoid_class"),
        "cost_adjusted_simulated_r_expectancy": row.get("cost_adjusted_simulated_r_expectancy"),
        "stress_simulated_r_expectancy": row.get("stress_simulated_r_expectancy"),
        "effective_n": row.get("effective_n"),
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_ready_action_implementation_candidate_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-CAND-{sequence:07d}"
            ),
            "input_ready_action_execution_row_id": row.get(
                "expanded_market_source_expansion_rule_match_ready_action_execution_row_id"
            ),
            "input_rule_match_action_row_id": row.get("input_rule_match_action_row_id"),
            "input_rule_match_performance_row_id": row.get("input_rule_match_performance_row_id"),
            "ready_action_implementation_status": implementation_status(kind),
            "ready_action_implementation_kind": kind,
            "symbol_family": row.get("symbol_family"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path": row.get("source_path"),
            "source_path_sha256": row.get("source_path_sha256"),
            "source_file_sha256": row.get("source_file_sha256"),
            "observed_match_rows": row.get("observed_match_rows"),
            "effective_n": row.get("effective_n"),
            "duplicate_inflation": row.get("duplicate_inflation"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "gross_simulated_r_expectancy": row.get("gross_simulated_r_expectancy"),
            "cost_adjusted_simulated_r_expectancy": row.get(
                "cost_adjusted_simulated_r_expectancy"
            ),
            "stress_simulated_r_expectancy": row.get("stress_simulated_r_expectancy"),
            "win_count": row.get("win_count"),
            "loss_count": row.get("loss_count"),
            "zero_count": row.get("zero_count"),
            "win_rate": row.get("win_rate"),
            "average_win": row.get("average_win"),
            "average_loss": row.get("average_loss"),
            "match_count": row.get("match_count"),
            "held_performance_rows_scanned": row.get("held_performance_rows_scanned"),
            "follow_inverse_default_off_avoid_class": row.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "source_decision": row.get("keep_kill_redesign_implement_decision"),
            "keep_kill_redesign_implement_decision": implementation_decision(kind),
            "ready_action_implementation_expression": expression,
            "ready_action_implementation_expression_sha256": stable_sha256(expression),
        }
    )


def implementation_self_test_row(candidate: dict[str, Any], sequence: int) -> dict[str, Any]:
    kind = candidate.get("ready_action_implementation_kind")
    cost_r = as_float(candidate.get("cost_adjusted_simulated_r_expectancy"))
    stress_r = as_float(candidate.get("stress_simulated_r_expectancy"))
    if kind == "branch-local-expanded-market-follow-implementation-candidate":
        passed = cost_r is not None and stress_r is not None and cost_r >= 0.05 and stress_r >= 0
    elif kind == "branch-local-expanded-market-avoid-implementation-candidate":
        passed = cost_r is not None and stress_r is not None and cost_r <= -0.05 and stress_r <= 0
    else:
        passed = False
    return boundary_row(
        {
            "expanded_market_source_expansion_ready_action_implementation_self_test_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-SELFTEST-{sequence:07d}"
            ),
            "input_ready_action_implementation_candidate_row_id": candidate.get(
                "expanded_market_source_expansion_ready_action_implementation_candidate_row_id"
            ),
            "self_test_status": "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_SELF_TEST_PASS"
            if passed
            else "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_SELF_TEST_REPAIR_REQUIRED",
            "ready_action_implementation_kind": kind,
            "cost_adjusted_simulated_r_expectancy": cost_r,
            "stress_simulated_r_expectancy": stress_r,
            "effective_n": candidate.get("effective_n"),
            "follow_inverse_default_off_avoid_class": candidate.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": candidate.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def redesign_implementation_task_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_redesign_implementation_task_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-REDESIGN-IMPL-TASK-{sequence:07d}"
            ),
            "input_redesign_action_execution_row_id": row.get(
                "expanded_market_source_expansion_rule_match_redesign_action_execution_row_id"
            ),
            "redesign_implementation_task_status": "SOURCE_EXPANSION_REDESIGN_IMPLEMENTATION_TASK_PRESERVED",
            "symbol_family": row.get("symbol_family"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path": row.get("source_path"),
            "source_path_sha256": row.get("source_path_sha256"),
            "source_file_sha256": row.get("source_file_sha256"),
            "observed_match_rows": row.get("observed_match_rows"),
            "effective_n": row.get("effective_n"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "follow_inverse_default_off_avoid_class": row.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": row.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def replay_implementation_task_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_replay_implementation_task_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-REPLAY-IMPL-TASK-{sequence:07d}"
            ),
            "input_replay_task_action_execution_row_id": row.get(
                "expanded_market_source_expansion_replay_task_action_execution_row_id"
            ),
            "replay_implementation_task_status": "SOURCE_EXPANSION_REPLAY_IMPLEMENTATION_TASK_PRESERVED",
            "symbol_family": row.get("symbol_family"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path": row.get("source_path"),
            "source_path_sha256": row.get("source_path_sha256"),
            "source_file_sha256": row.get("source_file_sha256"),
            "missing_work_fields": row.get("missing_work_fields") or [],
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": row.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def source_implementation_task_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_source_implementation_task_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-SOURCE-IMPL-TASK-{sequence:07d}"
            ),
            "input_source_task_action_execution_row_id": row.get(
                "expanded_market_source_expansion_source_task_action_execution_row_id"
            ),
            "source_implementation_task_status": "SOURCE_EXPANSION_SOURCE_IMPLEMENTATION_TASK_PRESERVED",
            "symbol_family": row.get("symbol_family"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path": row.get("source_path"),
            "source_path_sha256": row.get("source_path_sha256"),
            "source_file_sha256": row.get("source_file_sha256"),
            "missing_work_fields": row.get("missing_work_fields") or [],
            "discovered_same_symbol_timeframe_source_count": row.get(
                "discovered_same_symbol_timeframe_source_count"
            ),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": row.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def aggregate_implementation_rows(
    candidate_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], dict[str, Any]] = {}
    for row_type, rows in (
        ("ready_implementation_candidate", candidate_rows),
        ("redesign_implementation_task", redesign_rows),
        ("replay_implementation_task", replay_rows),
        ("source_implementation_task", source_rows),
    ):
        for row in rows:
            key = (
                row_type,
                str(row.get("keep_kill_redesign_implement_decision") or ""),
                str(row.get("follow_inverse_default_off_avoid_class") or ""),
                str(row.get("symbol_family") or ""),
                str(row.get("market_timeframe") or ""),
                str(row.get("route_session") or ""),
                str(row.get("horizon_id") or ""),
                str(row.get("side") or ""),
            )
            bucket = grouped.setdefault(
                key,
                {
                    "row_type": key[0],
                    "keep_kill_redesign_implement_decision": key[1],
                    "follow_inverse_default_off_avoid_class": key[2],
                    "symbol_family": key[3],
                    "market_timeframe": key[4],
                    "route_session": key[5],
                    "horizon_id": key[6],
                    "side": key[7],
                    "row_count": 0,
                    "cost_sum": 0.0,
                    "stress_sum": 0.0,
                    "effective_n_sum": 0,
                },
            )
            bucket["row_count"] += 1
            bucket["cost_sum"] += as_float(row.get("cost_adjusted_simulated_r")) or 0.0
            bucket["stress_sum"] += as_float(row.get("stress_simulated_r")) or 0.0
            bucket["effective_n_sum"] += int(row.get("effective_n") or 0)
    aggregates: list[dict[str, Any]] = []
    for sequence, bucket in enumerate(grouped.values(), start=1):
        count = int(bucket["row_count"])
        aggregates.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_ready_action_implementation_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-AGG-{sequence:07d}"
                    ),
                    **{
                        key: value
                        for key, value in bucket.items()
                        if key not in {"cost_sum", "stress_sum"}
                    },
                    "cost_adjusted_simulated_r_expectancy": (
                        rounded(bucket["cost_sum"] / count)
                        if count and bucket["row_type"] in {"ready_implementation_candidate", "redesign_implementation_task"}
                        else None
                    ),
                    "stress_simulated_r_expectancy": (
                        rounded(bucket["stress_sum"] / count)
                        if count and bucket["row_type"] in {"ready_implementation_candidate", "redesign_implementation_task"}
                        else None
                    ),
                }
            )
        )
    return aggregates


def status_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field) for row in rows).items()))
