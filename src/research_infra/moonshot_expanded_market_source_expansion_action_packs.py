"""Materialize branch-local action packs from expanded-market action applications."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACKS = (
    "src/research_infra/moonshot_expanded_market_source_expansion_action_packs.py"
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
    output["expanded_market_source_expansion_action_pack_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACKS
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def is_applied_action(row: dict[str, Any]) -> bool:
    return normalized(row.get("action_application_status")) in {
        "ACTION_APPLICATION_EXACT_RULE_APPLIED",
        "ACTION_APPLICATION_SCOPE_RULE_APPLIED",
    }


def action_pack_kind(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "branch-local-follow-action-pack"
    if decision.startswith("CARRY_AS_AVOID"):
        return "branch-local-avoid-intelligence-action-pack"
    if decision.startswith("KILL"):
        return "branch-local-default-off-action-pack"
    return "branch-local-redesign-action-pack"


def match_contract(row: dict[str, Any]) -> dict[str, Any]:
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
        "entry_reference": row.get("entry_reference"),
    }


def emit_contract(row: dict[str, Any], decision: str) -> dict[str, Any]:
    return {
        "decision": decision,
        "follow_inverse_default_off_avoid_class": row.get(
            "follow_inverse_default_off_avoid_class"
        ),
        "gross_simulated_r": row.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": row.get("stress_simulated_r"),
        "path_order_result": row.get("path_order_result"),
        "fill_status": row.get("fill_status"),
        "effective_n": row.get("effective_n"),
        "concentration_top_month_share": row.get("concentration_top_month_share"),
    }


def action_pack_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    decision = normalized(row.get("keep_kill_redesign_implement_decision"))
    match = match_contract(row)
    emit = emit_contract(row, decision)
    expression = {"match": match, "emit": emit}
    return boundary_row(
        {
            "expanded_market_source_expansion_action_pack_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-{sequence:07d}"
            ),
            "input_source_expansion_action_application_row_id": row.get(
                "expanded_market_source_expansion_action_application_row_id"
            ),
            "input_source_expansion_execution_row_id": row.get(
                "input_source_expansion_execution_row_id"
            ),
            "input_action_application_rule_row_id": row.get(
                "input_action_application_rule_row_id"
            ),
            "input_source_expansion_action_execution_row_id": row.get(
                "input_source_expansion_action_execution_row_id"
            ),
            "action_pack_status": "ACTION_PACK_MATERIALIZED",
            "action_pack_kind": action_pack_kind(decision),
            "application_status": row.get("action_application_status"),
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
            "entry_reference": row.get("entry_reference"),
            "entry_reference_time": row.get("entry_reference_time"),
            "proxy_entry_price": row.get("proxy_entry_price"),
            "proxy_denominator_price": row.get("proxy_denominator_price"),
            "proxy_target_price": row.get("proxy_target_price"),
            "proxy_stop_price": row.get("proxy_stop_price"),
            "path_order_result": row.get("path_order_result"),
            "fill_status": row.get("fill_status"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "rule_cost_adjusted_simulated_r": row.get("rule_cost_adjusted_simulated_r"),
            "win_count": row.get("win_count"),
            "loss_count": row.get("loss_count"),
            "zero_count": row.get("zero_count"),
            "target_first_count": row.get("target_first_count"),
            "stop_first_count": row.get("stop_first_count"),
            "neither_count": row.get("neither_count"),
            "ambiguous_count": row.get("ambiguous_count"),
            "effective_n": row.get("effective_n"),
            "duplicate_row_count": row.get("duplicate_row_count"),
            "effective_n_after_duplicate_collapse": row.get(
                "effective_n_after_duplicate_collapse"
            ),
            "concentration_top_month_share": row.get("concentration_top_month_share"),
            "branch_local_action_pack_match_contract": match,
            "branch_local_action_pack_emit_contract": emit,
            "branch_local_action_pack_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": row.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def execute_action_pack(pack: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    match = pack.get("branch_local_action_pack_match_contract") or {}
    checks = {
        key: normalized(match.get(key)) == normalized(match_contract(row).get(key))
        for key in match
    }
    expected_decision = normalized(pack.get("keep_kill_redesign_implement_decision"))
    emitted_decision = normalized(row.get("keep_kill_redesign_implement_decision"))
    cost_match = as_float(pack.get("cost_adjusted_simulated_r")) == as_float(
        row.get("cost_adjusted_simulated_r")
    )
    return {
        "match_checks": checks,
        "all_match_checks_pass": all(checks.values()),
        "expected_decision": expected_decision,
        "emitted_decision": emitted_decision,
        "decision_match": expected_decision == emitted_decision,
        "cost_adjusted_simulated_r_match": cost_match,
        "execution_pass": all(checks.values()) and expected_decision == emitted_decision and cost_match,
    }


def action_pack_self_test_row(
    pack: dict[str, Any],
    row: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    execution = execute_action_pack(pack, row)
    return boundary_row(
        {
            "expanded_market_source_expansion_action_pack_self_test_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-SELFTEST-{sequence:07d}"
            ),
            "input_action_pack_row_id": pack.get(
                "expanded_market_source_expansion_action_pack_row_id"
            ),
            "input_source_expansion_action_application_row_id": row.get(
                "expanded_market_source_expansion_action_application_row_id"
            ),
            "self_test_status": "ACTION_PACK_SELF_TEST_PASS"
            if execution["execution_pass"]
            else "ACTION_PACK_SELF_TEST_FAIL",
            **execution,
            "follow_inverse_default_off_avoid_class": pack.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": pack.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def replay_work_fields(row: dict[str, Any]) -> list[str]:
    fields = list(row.get("missing_simulated_fields") or [])
    status = normalized(row.get("action_application_status"))
    if status == "ACTION_APPLICATION_NO_MONTH_STABLE_RULE":
        fields.append("month_stable_action_rule_for_scope")
    if status == "ACTION_APPLICATION_SOURCE_GAP_PRESERVED":
        fields.append("alternate_replay_source_for_symbol_timeframe")
    if row.get("cost_adjusted_simulated_r") is None:
        fields.append("cost_adjusted_simulated_r")
    return sorted(set(fields))


def replay_work_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    fields = replay_work_fields(row)
    status = normalized(row.get("action_application_status"))
    if status == "ACTION_APPLICATION_SOURCE_GAP_PRESERVED":
        work_status = "ACTION_PACK_SOURCE_GAP_WORK_PRESERVED"
    elif row.get("cost_adjusted_simulated_r") is None:
        work_status = "ACTION_PACK_NONCOMPUTABLE_REPLAY_WORK_PRESERVED"
    else:
        work_status = "ACTION_PACK_NO_MONTH_STABLE_RULE_WORK_PRESERVED"
    expression = {
        "work_status": work_status,
        "application_row_id": row.get("expanded_market_source_expansion_action_application_row_id"),
        "source_path": row.get("source_path"),
        "missing_work_fields": fields,
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_action_pack_work_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-WORK-{sequence:07d}"
            ),
            "input_source_expansion_action_application_row_id": row.get(
                "expanded_market_source_expansion_action_application_row_id"
            ),
            "input_source_expansion_execution_row_id": row.get(
                "input_source_expansion_execution_row_id"
            ),
            "input_source_expansion_gap_row_id": row.get("input_source_expansion_gap_row_id"),
            "work_status": work_status,
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
            "source_access_status": row.get("source_access_status"),
            "entry_reference": row.get("entry_reference"),
            "proxy_denominator_price": row.get("proxy_denominator_price"),
            "path_order_result": row.get("path_order_result"),
            "fill_status": row.get("fill_status"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "effective_n": row.get("effective_n"),
            "concentration_top_month_share": row.get("concentration_top_month_share"),
            "missing_work_fields": fields,
            "branch_local_action_pack_work_expression": expression,
            "branch_local_action_pack_work_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_REPLAY_WORK"
            ),
        }
    )


def aggregate_action_pack_rows(
    pack_rows: list[dict[str, Any]],
    work_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = [("pack", row) for row in pack_rows] + [("work", row) for row in work_rows]
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row_kind, row in rows:
        key = (
            row_kind,
            normalized(row.get("symbol_family")),
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("side")),
            normalized(row.get("follow_inverse_default_off_avoid_class")),
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
                    "expanded_market_source_expansion_action_pack_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-AGG-{len(output) + 1:07d}"
                    ),
                    "row_kind": key[0],
                    "symbol_family": key[1],
                    "symbol": key[2],
                    "market_timeframe": key[3],
                    "route_session": key[4],
                    "horizon_id": key[5],
                    "side": key[6],
                    "follow_inverse_default_off_avoid_class": key[7],
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
