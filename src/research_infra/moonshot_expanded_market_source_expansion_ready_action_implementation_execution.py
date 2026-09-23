"""Execute ready-action implementation candidates against held execution rows."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_ready_action_implementation_execution.py"
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
    output["expanded_market_source_expansion_ready_action_implementation_execution_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def ready_execution_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready_action_execution_row_id": row.get(
            "expanded_market_source_expansion_rule_match_ready_action_execution_row_id"
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


def candidate_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ready_action_execution_row_id": row.get("input_ready_action_execution_row_id"),
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


def candidate_matches_ready_execution(candidate: dict[str, Any], ready_row: dict[str, Any]) -> bool:
    match = candidate_contract(candidate)
    target = ready_execution_contract(ready_row)
    return all(normalized(match.get(key)) == normalized(target.get(key)) for key in match)


def execute_candidate(candidate: dict[str, Any], ready_rows: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [row for row in ready_rows if candidate_matches_ready_execution(candidate, row)]
    cost_mismatch_count = 0
    stress_mismatch_count = 0
    for row in matched:
        if as_float(row.get("cost_adjusted_simulated_r_expectancy")) != as_float(
            candidate.get("cost_adjusted_simulated_r_expectancy")
        ):
            cost_mismatch_count += 1
        if as_float(row.get("stress_simulated_r_expectancy")) != as_float(
            candidate.get("stress_simulated_r_expectancy")
        ):
            stress_mismatch_count += 1
    return {
        "held_ready_action_execution_rows_scanned": len(ready_rows),
        "matched_ready_action_execution_row_ids": [
            row.get("expanded_market_source_expansion_rule_match_ready_action_execution_row_id")
            for row in matched
        ],
        "match_count": len(matched),
        "negative_mismatch_count": len(ready_rows) - len(matched),
        "cost_mismatch_count": cost_mismatch_count,
        "stress_mismatch_count": stress_mismatch_count,
        "execution_pass": bool(matched) and not cost_mismatch_count and not stress_mismatch_count,
    }


def implementation_execution_row(
    candidate: dict[str, Any],
    ready_rows: list[dict[str, Any]],
    sequence: int,
) -> dict[str, Any]:
    execution = execute_candidate(candidate, ready_rows)
    expression = {
        "candidate_row_id": candidate.get(
            "expanded_market_source_expansion_ready_action_implementation_candidate_row_id"
        ),
        "candidate_contract": candidate_contract(candidate),
        "matched_ready_action_execution_row_ids": execution[
            "matched_ready_action_execution_row_ids"
        ],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_ready_action_implementation_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-EXEC-{sequence:07d}"
            ),
            "input_ready_action_implementation_candidate_row_id": candidate.get(
                "expanded_market_source_expansion_ready_action_implementation_candidate_row_id"
            ),
            "input_ready_action_execution_row_id": candidate.get("input_ready_action_execution_row_id"),
            "ready_action_implementation_execution_status": (
                "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION_PASS"
                if execution["execution_pass"]
                else "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION_REPAIR_REQUIRED"
            ),
            "ready_action_implementation_kind": candidate.get("ready_action_implementation_kind"),
            "symbol_family": candidate.get("symbol_family"),
            "symbol": candidate.get("symbol"),
            "source_symbol": candidate.get("source_symbol"),
            "market_timeframe": candidate.get("market_timeframe"),
            "route_session": candidate.get("route_session"),
            "horizon_id": candidate.get("horizon_id"),
            "side": candidate.get("side"),
            "source_path": candidate.get("source_path"),
            "source_path_sha256": candidate.get("source_path_sha256"),
            "source_file_sha256": candidate.get("source_file_sha256"),
            "observed_match_rows": candidate.get("observed_match_rows"),
            "effective_n": candidate.get("effective_n"),
            "duplicate_inflation": candidate.get("duplicate_inflation"),
            "gross_simulated_r": candidate.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": candidate.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": candidate.get("stress_simulated_r"),
            "gross_simulated_r_expectancy": candidate.get("gross_simulated_r_expectancy"),
            "cost_adjusted_simulated_r_expectancy": candidate.get(
                "cost_adjusted_simulated_r_expectancy"
            ),
            "stress_simulated_r_expectancy": candidate.get("stress_simulated_r_expectancy"),
            "win_count": candidate.get("win_count"),
            "loss_count": candidate.get("loss_count"),
            "zero_count": candidate.get("zero_count"),
            "win_rate": candidate.get("win_rate"),
            "average_win": candidate.get("average_win"),
            "average_loss": candidate.get("average_loss"),
            **execution,
            "ready_action_implementation_execution_expression": expression,
            "ready_action_implementation_execution_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": candidate.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": candidate.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def implementation_match_rows(
    candidate: dict[str, Any],
    execution: dict[str, Any],
    ready_rows_by_id: dict[str, dict[str, Any]],
    start_sequence: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset, ready_id in enumerate(execution.get("matched_ready_action_execution_row_ids") or []):
        ready_row = ready_rows_by_id.get(str(ready_id)) or {}
        rows.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_ready_action_implementation_match_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-MATCH-{start_sequence + offset:07d}"
                    ),
                    "input_ready_action_implementation_execution_row_id": execution.get(
                        "expanded_market_source_expansion_ready_action_implementation_execution_row_id"
                    ),
                    "input_ready_action_implementation_candidate_row_id": candidate.get(
                        "expanded_market_source_expansion_ready_action_implementation_candidate_row_id"
                    ),
                    "input_ready_action_execution_row_id": ready_id,
                    "match_status": "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_CONTRACT_MATCH",
                    "symbol_family": ready_row.get("symbol_family"),
                    "symbol": ready_row.get("symbol"),
                    "source_symbol": ready_row.get("source_symbol"),
                    "market_timeframe": ready_row.get("market_timeframe"),
                    "route_session": ready_row.get("route_session"),
                    "horizon_id": ready_row.get("horizon_id"),
                    "side": ready_row.get("side"),
                    "source_path": ready_row.get("source_path"),
                    "source_path_sha256": ready_row.get("source_path_sha256"),
                    "source_file_sha256": ready_row.get("source_file_sha256"),
                    "cost_adjusted_simulated_r_expectancy": ready_row.get(
                        "cost_adjusted_simulated_r_expectancy"
                    ),
                    "stress_simulated_r_expectancy": ready_row.get(
                        "stress_simulated_r_expectancy"
                    ),
                    "follow_inverse_default_off_avoid_class": candidate.get(
                        "follow_inverse_default_off_avoid_class"
                    ),
                    "keep_kill_redesign_implement_decision": candidate.get(
                        "keep_kill_redesign_implement_decision"
                    ),
                }
            )
        )
    return rows


def task_execution_row(row: dict[str, Any], row_type: str, sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_ready_action_implementation_task_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-TASK-EXEC-{sequence:07d}"
            ),
            "task_execution_type": row_type,
            "task_execution_status": "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_TASK_PRESERVED",
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
            "follow_inverse_default_off_avoid_class": row.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": row.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def aggregate_execution_rows(
    execution_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], dict[str, Any]] = {}
    for row_type, rows in (
        ("ready_implementation_execution", execution_rows),
        ("implementation_task_execution", task_rows),
    ):
        for row in rows:
            key = (
                row_type if row_type == "ready_implementation_execution" else str(row.get("task_execution_type") or row_type),
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
                    "expanded_market_source_expansion_ready_action_implementation_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-EXEC-AGG-{sequence:07d}"
                    ),
                    **{
                        key: value
                        for key, value in bucket.items()
                        if key not in {"cost_sum", "stress_sum"}
                    },
                    "cost_adjusted_simulated_r_expectancy": (
                        rounded(bucket["cost_sum"] / count)
                        if count and bucket["row_type"] == "ready_implementation_execution"
                        else None
                    ),
                    "stress_simulated_r_expectancy": (
                        rounded(bucket["stress_sum"] / count)
                        if count and bucket["row_type"] == "ready_implementation_execution"
                        else None
                    ),
                }
            )
        )
    return aggregates


def status_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field) for row in rows).items()))
