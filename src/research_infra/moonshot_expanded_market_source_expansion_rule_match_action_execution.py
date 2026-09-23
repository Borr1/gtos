"""Execute rule-match action rows against held performance rows."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_action_execution.py"
)


READY_ACTION_STATUSES = {
    "SOURCE_EXPANSION_RULE_MATCH_ACTION_FOLLOW_READY",
    "SOURCE_EXPANSION_RULE_MATCH_ACTION_AVOID_READY",
}


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
    output["expanded_market_source_expansion_rule_match_action_execution_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def performance_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_match_performance_row_id": row.get(
            "expanded_market_source_expansion_rule_match_performance_row_id"
        ),
        "symbol_family": row.get("symbol_family"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
        "source_path_sha256": row.get("source_path_sha256"),
        "source_file_sha256": row.get("source_file_sha256"),
    }


def action_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_match_performance_row_id": row.get("input_rule_match_performance_row_id"),
        "symbol_family": row.get("symbol_family"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
        "source_path_sha256": row.get("source_path_sha256"),
        "source_file_sha256": row.get("source_file_sha256"),
    }


def action_matches_performance(action: dict[str, Any], performance: dict[str, Any]) -> bool:
    action_match = action_contract(action)
    held_match = performance_contract(performance)
    return all(normalized(action_match.get(key)) == normalized(held_match.get(key)) for key in action_match)


def execute_ready_action(action: dict[str, Any], performance_rows: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [row for row in performance_rows if action_matches_performance(action, row)]
    cost_mismatch_count = 0
    stress_mismatch_count = 0
    for row in matched:
        if as_float(row.get("cost_adjusted_simulated_r_expectancy")) != as_float(
            action.get("cost_adjusted_simulated_r_expectancy")
        ):
            cost_mismatch_count += 1
        if as_float(row.get("stress_simulated_r_expectancy")) != as_float(
            action.get("stress_simulated_r_expectancy")
        ):
            stress_mismatch_count += 1
    return {
        "held_performance_rows_scanned": len(performance_rows),
        "matched_performance_row_ids": [
            row.get("expanded_market_source_expansion_rule_match_performance_row_id")
            for row in matched
        ],
        "match_count": len(matched),
        "negative_mismatch_count": len(performance_rows) - len(matched),
        "cost_mismatch_count": cost_mismatch_count,
        "stress_mismatch_count": stress_mismatch_count,
        "execution_pass": bool(matched) and not cost_mismatch_count and not stress_mismatch_count,
    }


def ready_action_execution_row(
    action: dict[str, Any],
    performance_rows: list[dict[str, Any]],
    sequence: int,
) -> dict[str, Any]:
    execution = execute_ready_action(action, performance_rows)
    expression = {
        "action_row_id": action.get("expanded_market_source_expansion_rule_match_action_row_id"),
        "action_contract": action_contract(action),
        "matched_performance_row_ids": execution["matched_performance_row_ids"],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_rule_match_ready_action_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-READY-ACTION-EXEC-{sequence:07d}"
            ),
            "input_rule_match_action_row_id": action.get(
                "expanded_market_source_expansion_rule_match_action_row_id"
            ),
            "input_rule_match_performance_row_id": action.get("input_rule_match_performance_row_id"),
            "ready_action_execution_status": "SOURCE_EXPANSION_RULE_MATCH_READY_ACTION_EXECUTION_PASS"
            if execution["execution_pass"]
            else "SOURCE_EXPANSION_RULE_MATCH_READY_ACTION_EXECUTION_REPAIR_REQUIRED",
            "rule_match_action_kind": action.get("rule_match_action_kind"),
            "rule_match_action_status": action.get("rule_match_action_status"),
            "symbol_family": action.get("symbol_family"),
            "symbol": action.get("symbol"),
            "source_symbol": action.get("source_symbol"),
            "market_timeframe": action.get("market_timeframe"),
            "route_session": action.get("route_session"),
            "horizon_id": action.get("horizon_id"),
            "side": action.get("side"),
            "source_path": action.get("source_path"),
            "source_path_sha256": action.get("source_path_sha256"),
            "source_file_sha256": action.get("source_file_sha256"),
            "observed_match_rows": action.get("observed_match_rows"),
            "effective_n": action.get("effective_n"),
            "duplicate_inflation": action.get("duplicate_inflation"),
            "gross_simulated_r": action.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": action.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": action.get("stress_simulated_r"),
            "gross_simulated_r_expectancy": action.get("gross_simulated_r_expectancy"),
            "cost_adjusted_simulated_r_expectancy": action.get(
                "cost_adjusted_simulated_r_expectancy"
            ),
            "stress_simulated_r_expectancy": action.get("stress_simulated_r_expectancy"),
            "win_count": action.get("win_count"),
            "loss_count": action.get("loss_count"),
            "zero_count": action.get("zero_count"),
            "win_rate": action.get("win_rate"),
            "average_win": action.get("average_win"),
            "average_loss": action.get("average_loss"),
            **execution,
            "ready_action_execution_expression": expression,
            "ready_action_execution_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": action.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": action.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def ready_action_match_rows(
    action: dict[str, Any],
    execution: dict[str, Any],
    performance_rows_by_id: dict[str, dict[str, Any]],
    start_sequence: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset, performance_id in enumerate(execution.get("matched_performance_row_ids") or []):
        performance = performance_rows_by_id.get(str(performance_id)) or {}
        rows.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_rule_match_ready_action_match_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-READY-ACTION-MATCH-{start_sequence + offset:07d}"
                    ),
                    "input_ready_action_execution_row_id": execution.get(
                        "expanded_market_source_expansion_rule_match_ready_action_execution_row_id"
                    ),
                    "input_rule_match_action_row_id": action.get(
                        "expanded_market_source_expansion_rule_match_action_row_id"
                    ),
                    "input_rule_match_performance_row_id": performance_id,
                    "match_status": "SOURCE_EXPANSION_RULE_MATCH_READY_ACTION_CONTRACT_MATCH",
                    "symbol_family": performance.get("symbol_family"),
                    "symbol": performance.get("symbol"),
                    "source_symbol": performance.get("source_symbol"),
                    "market_timeframe": performance.get("market_timeframe"),
                    "route_session": performance.get("route_session"),
                    "horizon_id": performance.get("horizon_id"),
                    "side": performance.get("side"),
                    "source_path": performance.get("source_path"),
                    "source_path_sha256": performance.get("source_path_sha256"),
                    "source_file_sha256": performance.get("source_file_sha256"),
                    "cost_adjusted_simulated_r_expectancy": performance.get(
                        "cost_adjusted_simulated_r_expectancy"
                    ),
                    "stress_simulated_r_expectancy": performance.get(
                        "stress_simulated_r_expectancy"
                    ),
                    "follow_inverse_default_off_avoid_class": action.get(
                        "follow_inverse_default_off_avoid_class"
                    ),
                    "keep_kill_redesign_implement_decision": action.get(
                        "keep_kill_redesign_implement_decision"
                    ),
                }
            )
        )
    return rows


def redesign_action_execution_row(action: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_rule_match_redesign_action_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-REDESIGN-ACTION-EXEC-{sequence:07d}"
            ),
            "input_rule_match_action_row_id": action.get(
                "expanded_market_source_expansion_rule_match_action_row_id"
            ),
            "input_rule_match_performance_row_id": action.get("input_rule_match_performance_row_id"),
            "redesign_action_execution_status": "SOURCE_EXPANSION_RULE_MATCH_REDESIGN_ACTION_PRESERVED",
            "rule_match_action_kind": action.get("rule_match_action_kind"),
            "rule_match_action_status": action.get("rule_match_action_status"),
            "symbol_family": action.get("symbol_family"),
            "symbol": action.get("symbol"),
            "source_symbol": action.get("source_symbol"),
            "market_timeframe": action.get("market_timeframe"),
            "route_session": action.get("route_session"),
            "horizon_id": action.get("horizon_id"),
            "side": action.get("side"),
            "source_path": action.get("source_path"),
            "source_path_sha256": action.get("source_path_sha256"),
            "source_file_sha256": action.get("source_file_sha256"),
            "observed_match_rows": action.get("observed_match_rows"),
            "effective_n": action.get("effective_n"),
            "gross_simulated_r": action.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": action.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": action.get("stress_simulated_r"),
            "follow_inverse_default_off_avoid_class": action.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": action.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def replay_task_execution_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_replay_task_action_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-REPLAY-TASK-ACTION-EXEC-{sequence:07d}"
            ),
            "input_replay_task_action_row_id": row.get(
                "expanded_market_source_expansion_replay_task_action_row_id"
            ),
            "replay_task_action_execution_status": "SOURCE_EXPANSION_REPLAY_TASK_ACTION_EXECUTION_PRESERVED",
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


def source_task_execution_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_source_task_action_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-SOURCE-TASK-ACTION-EXEC-{sequence:07d}"
            ),
            "input_source_task_action_row_id": row.get(
                "expanded_market_source_expansion_source_task_action_row_id"
            ),
            "source_task_action_execution_status": "SOURCE_EXPANSION_SOURCE_TASK_ACTION_EXECUTION_PRESERVED",
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


def aggregate_execution_rows(
    ready_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], dict[str, Any]] = {}
    for row_type, rows in (
        ("ready_action_execution", ready_rows),
        ("redesign_action_execution", redesign_rows),
        ("replay_task_action_execution", replay_rows),
        ("source_task_action_execution", source_rows),
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
                    "match_count_sum": 0,
                },
            )
            bucket["row_count"] += 1
            bucket["cost_sum"] += as_float(row.get("cost_adjusted_simulated_r")) or 0.0
            bucket["stress_sum"] += as_float(row.get("stress_simulated_r")) or 0.0
            bucket["match_count_sum"] += int(row.get("match_count") or 0)
    aggregates: list[dict[str, Any]] = []
    for sequence, bucket in enumerate(grouped.values(), start=1):
        count = int(bucket["row_count"])
        aggregates.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_rule_match_action_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-ACTION-EXEC-AGG-{sequence:07d}"
                    ),
                    **{
                        key: value
                        for key, value in bucket.items()
                        if key not in {"cost_sum", "stress_sum"}
                    },
                    "cost_adjusted_simulated_r_expectancy": (
                        rounded(bucket["cost_sum"] / count)
                        if count and bucket["row_type"] in {"ready_action_execution", "redesign_action_execution"}
                        else None
                    ),
                    "stress_simulated_r_expectancy": (
                        rounded(bucket["stress_sum"] / count)
                        if count and bucket["row_type"] in {"ready_action_execution", "redesign_action_execution"}
                        else None
                    ),
                }
            )
        )
    return aggregates


def status_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field) for row in rows).items()))
