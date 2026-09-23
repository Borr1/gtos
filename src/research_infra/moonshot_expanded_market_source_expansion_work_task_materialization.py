"""Materialize concrete tasks from source-expansion work-resolution rows."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_WORK_TASK_MATERIALIZATION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_work_task_materialization.py"
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
    output["expanded_market_source_expansion_work_task_materialization_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_WORK_TASK_MATERIALIZATION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def rule_candidate_class(row: dict[str, Any]) -> str:
    cost_r = as_float(row.get("cost_adjusted_simulated_r"))
    effective_n = int(row.get("effective_n") or 0)
    if cost_r is None:
        return "rule-redesign-noncomputed"
    if effective_n < 20:
        return "rule-redesign-underpowered"
    if cost_r >= 0.10:
        return "rule-redesign-positive-follow-retest"
    if cost_r <= -0.05:
        return "rule-redesign-negative-avoid-retest"
    return "rule-redesign-weak-neutral-retest"


def rule_candidate_decision(candidate_class: str) -> str:
    if candidate_class == "rule-redesign-positive-follow-retest":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_POSITIVE_RULE_RETEST"
    if candidate_class == "rule-redesign-negative-avoid-retest":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_AVOID_RULE_RETEST"
    if candidate_class == "rule-redesign-underpowered":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_UNDERPOWERED_RULE_RETEST"
    return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_WEAK_RULE_RETEST"


def rule_match_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol_family": row.get("symbol_family"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
        "source_path_sha256": row.get("source_path_sha256"),
        "source_file_sha256": row.get("source_file_sha256"),
        "work_resolution_status": row.get("work_resolution_status"),
    }


def rule_emit_contract(row: dict[str, Any], candidate_class: str) -> dict[str, Any]:
    return {
        "candidate_class": candidate_class,
        "gross_simulated_r": row.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": row.get("stress_simulated_r"),
        "effective_n": row.get("effective_n"),
        "current_source_file_hash_matches_row": row.get("current_source_file_hash_matches_row"),
    }


def rule_candidate_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    candidate_class = rule_candidate_class(row)
    decision = rule_candidate_decision(candidate_class)
    match = rule_match_contract(row)
    emit = rule_emit_contract(row, candidate_class)
    expression = {"match": match, "emit": emit}
    return boundary_row(
        {
            "expanded_market_source_expansion_rule_candidate_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-CAND-{sequence:07d}"
            ),
            "input_work_resolution_row_id": row.get(
                "expanded_market_source_expansion_action_pack_work_resolution_row_id"
            ),
            "input_action_pack_work_execution_row_id": row.get(
                "input_action_pack_work_execution_row_id"
            ),
            "rule_candidate_status": "SOURCE_EXPANSION_RULE_CANDIDATE_MATERIALIZED",
            "rule_candidate_class": candidate_class,
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
            "current_source_path_exists": row.get("current_source_path_exists"),
            "current_source_file_sha256": row.get("current_source_file_sha256"),
            "current_source_file_hash_matches_row": row.get(
                "current_source_file_hash_matches_row"
            ),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "effective_n": row.get("effective_n"),
            "missing_work_fields": row.get("missing_work_fields") or [],
            "branch_local_rule_candidate_match_contract": match,
            "branch_local_rule_candidate_emit_contract": emit,
            "branch_local_rule_candidate_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def rule_candidate_self_test_row(candidate: dict[str, Any], source_row: dict[str, Any], sequence: int) -> dict[str, Any]:
    match = candidate.get("branch_local_rule_candidate_match_contract") or {}
    source_match = rule_match_contract(source_row)
    checks = {
        key: normalized(match.get(key)) == normalized(source_match.get(key))
        for key in match
    }
    cost_match = as_float(candidate.get("cost_adjusted_simulated_r")) == as_float(
        source_row.get("cost_adjusted_simulated_r")
    )
    passed = all(checks.values()) and cost_match
    return boundary_row(
        {
            "expanded_market_source_expansion_rule_candidate_self_test_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-CAND-SELFTEST-{sequence:07d}"
            ),
            "input_rule_candidate_row_id": candidate.get(
                "expanded_market_source_expansion_rule_candidate_row_id"
            ),
            "input_work_resolution_row_id": source_row.get(
                "expanded_market_source_expansion_action_pack_work_resolution_row_id"
            ),
            "self_test_status": "SOURCE_EXPANSION_RULE_CANDIDATE_SELF_TEST_PASS"
            if passed
            else "SOURCE_EXPANSION_RULE_CANDIDATE_SELF_TEST_FAIL",
            "match_checks": checks,
            "cost_adjusted_simulated_r_match": cost_match,
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": candidate.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def replay_task_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    expression = {
        "task": "replay_implementation",
        "work_resolution_row_id": row.get(
            "expanded_market_source_expansion_action_pack_work_resolution_row_id"
        ),
        "missing_work_fields": row.get("missing_work_fields") or [],
        "source_path": row.get("source_path"),
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_replay_task_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-REPLAY-TASK-{sequence:07d}"
            ),
            "input_work_resolution_row_id": row.get(
                "expanded_market_source_expansion_action_pack_work_resolution_row_id"
            ),
            "replay_task_status": "SOURCE_EXPANSION_REPLAY_IMPLEMENTATION_TASK_MATERIALIZED",
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
            "current_source_path_exists": row.get("current_source_path_exists"),
            "current_source_file_hash_matches_row": row.get(
                "current_source_file_hash_matches_row"
            ),
            "missing_work_fields": row.get("missing_work_fields") or [],
            "replay_task_expression": expression,
            "replay_task_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_REPLAY_TASK_MATERIALIZED"
            ),
        }
    )


def source_task_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    expression = {
        "task": "source_acquisition",
        "work_resolution_row_id": row.get(
            "expanded_market_source_expansion_action_pack_work_resolution_row_id"
        ),
        "missing_work_fields": row.get("missing_work_fields") or [],
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "same_symbol_timeframe_sources": row.get("discovered_same_symbol_timeframe_source_paths") or [],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_source_task_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-SOURCE-TASK-{sequence:07d}"
            ),
            "input_work_resolution_row_id": row.get(
                "expanded_market_source_expansion_action_pack_work_resolution_row_id"
            ),
            "source_task_status": "SOURCE_EXPANSION_SOURCE_ACQUISITION_TASK_MATERIALIZED",
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
            "current_source_path_exists": row.get("current_source_path_exists"),
            "current_source_file_hash_matches_row": row.get(
                "current_source_file_hash_matches_row"
            ),
            "discovered_same_symbol_timeframe_source_count": row.get(
                "discovered_same_symbol_timeframe_source_count"
            ),
            "discovered_same_symbol_timeframe_source_paths": row.get(
                "discovered_same_symbol_timeframe_source_paths"
            ),
            "missing_work_fields": row.get("missing_work_fields") or [],
            "source_task_expression": expression,
            "source_task_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SOURCE_TASK_MATERIALIZED"
            ),
        }
    )


def aggregate_task_rows(
    rule_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tagged = (
        [("rule_candidate", row) for row in rule_rows]
        + [("replay_task", row) for row in replay_rows]
        + [("source_task", row) for row in source_rows]
    )
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for kind, row in tagged:
        key = (
            kind,
            normalized(row.get("symbol_family")),
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("side")),
            normalized(row.get("rule_candidate_class")),
        )
        grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        values = [
            as_float(row.get("cost_adjusted_simulated_r"))
            for row in members
            if as_float(row.get("cost_adjusted_simulated_r")) is not None
        ]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_work_task_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-WORK-TASK-AGG-{len(output) + 1:07d}"
                    ),
                    "row_kind": key[0],
                    "symbol_family": key[1],
                    "symbol": key[2],
                    "market_timeframe": key[3],
                    "route_session": key[4],
                    "horizon_id": key[5],
                    "side": key[6],
                    "rule_candidate_class": key[7],
                    "row_count": len(members),
                    "rows_with_simulated_r": len(values),
                    "average_cost_adjusted_simulated_r": rounded(
                        sum(values) / len(values) if values else None
                    ),
                    "effective_n_sum": sum(int(row.get("effective_n") or 0) for row in members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output
