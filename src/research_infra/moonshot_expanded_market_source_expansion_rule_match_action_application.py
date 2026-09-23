"""Apply rule-match performance decisions into branch-local action rows."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_APPLICATION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_action_application.py"
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
    output["expanded_market_source_expansion_rule_match_action_application_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_APPLICATION
    )
    output["research_boundary"] = research_boundary()
    return output


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def action_kind(row: dict[str, Any]) -> str:
    decision = str(row.get("keep_kill_redesign_implement_decision") or "")
    if decision == "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_FOLLOW":
        return "branch-local-follow-rule-action"
    if decision == "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_AVOID":
        return "branch-local-avoid-rule-action"
    if decision == "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_UNDERPOWERED":
        return "rule-match-underpowered-redesign-action"
    return "rule-match-mixed-redesign-action"


def action_status(kind: str) -> str:
    if kind == "branch-local-follow-rule-action":
        return "SOURCE_EXPANSION_RULE_MATCH_ACTION_FOLLOW_READY"
    if kind == "branch-local-avoid-rule-action":
        return "SOURCE_EXPANSION_RULE_MATCH_ACTION_AVOID_READY"
    if kind == "rule-match-underpowered-redesign-action":
        return "SOURCE_EXPANSION_RULE_MATCH_ACTION_UNDERPOWERED_REDESIGN"
    return "SOURCE_EXPANSION_RULE_MATCH_ACTION_MIXED_REDESIGN"


def application_decision(kind: str) -> str:
    if kind == "branch-local-follow-rule-action":
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_FOLLOW_RULE_ACTION"
    if kind == "branch-local-avoid-rule-action":
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_AVOID_RULE_ACTION"
    if kind == "rule-match-underpowered-redesign-action":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_UNDERPOWERED_RULE_ACTION"
    return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_MIXED_RULE_ACTION"


def rule_match_action_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    kind = action_kind(row)
    expression = {
        "action_kind": kind,
        "input_rule_match_performance_row_id": row.get(
            "expanded_market_source_expansion_rule_match_performance_row_id"
        ),
        "symbol_family": row.get("symbol_family"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
        "cost_adjusted_simulated_r_expectancy": row.get(
            "cost_adjusted_simulated_r_expectancy"
        ),
        "stress_simulated_r_expectancy": row.get("stress_simulated_r_expectancy"),
        "effective_n": row.get("effective_n"),
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_rule_match_action_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-ACTION-{sequence:07d}"
            ),
            "input_rule_match_performance_row_id": row.get(
                "expanded_market_source_expansion_rule_match_performance_row_id"
            ),
            "input_rule_candidate_execution_row_id": row.get(
                "input_rule_candidate_execution_row_id"
            ),
            "rule_match_action_status": action_status(kind),
            "rule_match_action_kind": kind,
            "rule_candidate_class": row.get("rule_candidate_class"),
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
            "dominant_source_path_share": row.get("dominant_source_path_share"),
            "dominant_source_file_share": row.get("dominant_source_file_share"),
            "follow_inverse_default_off_avoid_class": row.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "source_decision": row.get("keep_kill_redesign_implement_decision"),
            "keep_kill_redesign_implement_decision": application_decision(kind),
            "rule_match_action_expression": expression,
            "rule_match_action_expression_sha256": stable_sha256(expression),
        }
    )


def action_self_test_row(action: dict[str, Any], sequence: int) -> dict[str, Any]:
    kind = action.get("rule_match_action_kind")
    expectancy = as_float(action.get("cost_adjusted_simulated_r_expectancy"))
    stress = as_float(action.get("stress_simulated_r_expectancy"))
    effective_n = int(action.get("effective_n") or 0)
    if kind == "branch-local-follow-rule-action":
        passed = expectancy is not None and stress is not None and expectancy >= 0.05 and stress >= 0
    elif kind == "branch-local-avoid-rule-action":
        passed = expectancy is not None and stress is not None and expectancy <= -0.05 and stress <= 0
    else:
        passed = effective_n >= 0 and bool(action.get("source_decision"))
    return boundary_row(
        {
            "expanded_market_source_expansion_rule_match_action_self_test_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-ACTION-SELFTEST-{sequence:07d}"
            ),
            "input_rule_match_action_row_id": action.get(
                "expanded_market_source_expansion_rule_match_action_row_id"
            ),
            "self_test_status": "SOURCE_EXPANSION_RULE_MATCH_ACTION_SELF_TEST_PASS"
            if passed
            else "SOURCE_EXPANSION_RULE_MATCH_ACTION_SELF_TEST_REPAIR_REQUIRED",
            "rule_match_action_kind": kind,
            "cost_adjusted_simulated_r_expectancy": expectancy,
            "stress_simulated_r_expectancy": stress,
            "effective_n": effective_n,
            "follow_inverse_default_off_avoid_class": action.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": action.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def replay_task_action_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_replay_task_action_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-REPLAY-TASK-ACTION-{sequence:07d}"
            ),
            "input_replay_task_performance_row_id": row.get(
                "expanded_market_source_expansion_replay_task_performance_row_id"
            ),
            "replay_task_action_status": "SOURCE_EXPANSION_REPLAY_TASK_ACTION_REQUIRED",
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
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_REPLAY_TASK_ACTION"
            ),
        }
    )


def source_task_action_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_source_task_action_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-SOURCE-TASK-ACTION-{sequence:07d}"
            ),
            "input_source_task_performance_row_id": row.get(
                "expanded_market_source_expansion_source_task_performance_row_id"
            ),
            "source_task_action_status": "SOURCE_EXPANSION_SOURCE_TASK_ACTION_REQUIRED",
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
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SOURCE_TASK_ACTION"
            ),
        }
    )


def aggregate_action_rows(
    action_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], dict[str, Any]] = {}
    for row_type, rows in (
        ("rule_match_action", action_rows),
        ("replay_task_action", replay_rows),
        ("source_task_action", source_rows),
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
                    "expanded_market_source_expansion_rule_match_action_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-MATCH-ACTION-AGG-{sequence:07d}"
                    ),
                    **{
                        key: value
                        for key, value in bucket.items()
                        if key not in {"cost_sum", "stress_sum"}
                    },
                    "cost_adjusted_simulated_r_expectancy": (
                        rounded(bucket["cost_sum"] / count) if count and bucket["row_type"] == "rule_match_action" else None
                    ),
                    "stress_simulated_r_expectancy": (
                        rounded(bucket["stress_sum"] / count) if count and bucket["row_type"] == "rule_match_action" else None
                    ),
                }
            )
        )
    return aggregates


def status_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row.get(field) for row in rows).items()))
