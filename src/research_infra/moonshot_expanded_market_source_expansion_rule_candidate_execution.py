"""Execute expanded-market rule candidates against work-resolution rows."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_rule_candidate_execution.py"
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
    output["expanded_market_source_expansion_rule_candidate_execution_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def work_resolution_contract(row: dict[str, Any]) -> dict[str, Any]:
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


def candidate_matches(candidate: dict[str, Any], work_row: dict[str, Any]) -> bool:
    match = candidate.get("branch_local_rule_candidate_match_contract") or {}
    target = work_resolution_contract(work_row)
    return all(normalized(match.get(key)) == normalized(target.get(key)) for key in match)


def execute_rule_candidate(candidate: dict[str, Any], work_rows: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [row for row in work_rows if candidate_matches(candidate, row)]
    expected_id = normalized(candidate.get("input_work_resolution_row_id"))
    matched_ids = [
        normalized(row.get("expanded_market_source_expansion_action_pack_work_resolution_row_id"))
        for row in matched
    ]
    cost_mismatches = [
        row
        for row in matched
        if as_float(row.get("cost_adjusted_simulated_r"))
        != as_float(candidate.get("cost_adjusted_simulated_r"))
    ]
    return {
        "candidate_rows_scanned": len(work_rows),
        "matched_work_resolution_row_ids": matched_ids,
        "match_count": len(matched),
        "negative_mismatch_count": len(work_rows) - len(matched),
        "expected_work_resolution_row_matched": expected_id in matched_ids,
        "cost_mismatch_count": len(cost_mismatches),
        "execution_pass": bool(matched) and expected_id in matched_ids and not cost_mismatches,
    }


def rule_candidate_execution_row(
    candidate: dict[str, Any],
    work_rows: list[dict[str, Any]],
    sequence: int,
) -> dict[str, Any]:
    execution = execute_rule_candidate(candidate, work_rows)
    expression = {
        "rule_candidate_row_id": candidate.get("expanded_market_source_expansion_rule_candidate_row_id"),
        "match_contract": candidate.get("branch_local_rule_candidate_match_contract"),
        "emit_contract": candidate.get("branch_local_rule_candidate_emit_contract"),
        "matched_work_resolution_row_ids": execution["matched_work_resolution_row_ids"],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_rule_candidate_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-CAND-EXEC-{sequence:07d}"
            ),
            "input_rule_candidate_row_id": candidate.get(
                "expanded_market_source_expansion_rule_candidate_row_id"
            ),
            "input_work_resolution_row_id": candidate.get("input_work_resolution_row_id"),
            "rule_candidate_execution_status": "SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION_PASS"
            if execution["execution_pass"]
            else "SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION_REPAIR_REQUIRED",
            "rule_candidate_class": candidate.get("rule_candidate_class"),
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
            "gross_simulated_r": candidate.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": candidate.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": candidate.get("stress_simulated_r"),
            "effective_n": candidate.get("effective_n"),
            **execution,
            "branch_local_rule_candidate_execution_expression": expression,
            "branch_local_rule_candidate_execution_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": candidate.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def rule_match_rows(
    candidate: dict[str, Any],
    execution: dict[str, Any],
    work_rows_by_id: dict[str, dict[str, Any]],
    start_sequence: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset, work_id in enumerate(execution.get("matched_work_resolution_row_ids") or []):
        work_row = work_rows_by_id.get(work_id) or {}
        rows.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_rule_candidate_match_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-CAND-MATCH-{start_sequence + offset:07d}"
                    ),
                    "input_rule_candidate_execution_row_id": execution.get(
                        "expanded_market_source_expansion_rule_candidate_execution_row_id"
                    ),
                    "input_rule_candidate_row_id": candidate.get(
                        "expanded_market_source_expansion_rule_candidate_row_id"
                    ),
                    "input_work_resolution_row_id": work_id,
                    "match_status": "SOURCE_EXPANSION_RULE_CANDIDATE_CONTRACT_MATCH",
                    "symbol_family": work_row.get("symbol_family"),
                    "symbol": work_row.get("symbol"),
                    "source_symbol": work_row.get("source_symbol"),
                    "market_timeframe": work_row.get("market_timeframe"),
                    "route_session": work_row.get("route_session"),
                    "horizon_id": work_row.get("horizon_id"),
                    "side": work_row.get("side"),
                    "source_path": work_row.get("source_path"),
                    "source_path_sha256": work_row.get("source_path_sha256"),
                    "source_file_sha256": work_row.get("source_file_sha256"),
                    "gross_simulated_r": work_row.get("gross_simulated_r"),
                    "cost_adjusted_simulated_r": work_row.get("cost_adjusted_simulated_r"),
                    "stress_simulated_r": work_row.get("stress_simulated_r"),
                    "follow_inverse_default_off_avoid_class": "redesign",
                    "keep_kill_redesign_implement_decision": candidate.get(
                        "keep_kill_redesign_implement_decision"
                    ),
                }
            )
        )
    return rows


def replay_task_execution_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    expression = {
        "task_row_id": row.get("expanded_market_source_expansion_replay_task_row_id"),
        "missing_work_fields": row.get("missing_work_fields") or [],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_replay_task_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-REPLAY-TASK-EXEC-{sequence:07d}"
            ),
            "input_replay_task_row_id": row.get(
                "expanded_market_source_expansion_replay_task_row_id"
            ),
            "replay_task_execution_status": "SOURCE_EXPANSION_REPLAY_TASK_EXECUTION_PRESERVED",
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
            "replay_task_execution_expression": expression,
            "replay_task_execution_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": row.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def source_task_execution_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    expression = {
        "task_row_id": row.get("expanded_market_source_expansion_source_task_row_id"),
        "missing_work_fields": row.get("missing_work_fields") or [],
        "same_symbol_timeframe_sources": row.get("discovered_same_symbol_timeframe_source_paths") or [],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_source_task_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-SOURCE-TASK-EXEC-{sequence:07d}"
            ),
            "input_source_task_row_id": row.get(
                "expanded_market_source_expansion_source_task_row_id"
            ),
            "source_task_execution_status": "SOURCE_EXPANSION_SOURCE_TASK_EXECUTION_PRESERVED",
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
            "discovered_same_symbol_timeframe_source_count": row.get(
                "discovered_same_symbol_timeframe_source_count"
            ),
            "discovered_same_symbol_timeframe_source_paths": row.get(
                "discovered_same_symbol_timeframe_source_paths"
            ),
            "missing_work_fields": row.get("missing_work_fields") or [],
            "source_task_execution_expression": expression,
            "source_task_execution_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": row.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def aggregate_rule_execution_rows(
    rule_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tagged = (
        [("rule_execution", row) for row in rule_rows]
        + [("replay_task_execution", row) for row in replay_rows]
        + [("source_task_execution", row) for row in source_rows]
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
                    "expanded_market_source_expansion_rule_candidate_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-RULE-CAND-EXEC-AGG-{len(output) + 1:07d}"
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
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output
