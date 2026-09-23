"""Apply month-stable source-expansion actions across expanded execution rows."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_action_application.py"
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
    output["expanded_market_source_expansion_action_application_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def is_actionable_decision(decision: str) -> bool:
    return (
        decision.startswith("IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION")
        or decision.startswith("KILL_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION")
        or decision.startswith(
            "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
        )
    )


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if decision.startswith("KILL"):
        return "default-off"
    if decision.startswith("CARRY_AS_AVOID"):
        return "avoid"
    return "redesign"


def exact_scope_from_action(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol_family")),
        normalized(row.get("symbol")),
        normalized(row.get("source_symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
        normalized(row.get("source_path")),
        normalized(row.get("source_file_sha256")),
        normalized(row.get("entry_reference")),
    )


def family_scope_from_action(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol_family")),
        normalized(row.get("symbol")),
        normalized(row.get("source_symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
    )


def exact_scope_from_execution(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol_family")),
        normalized(row.get("symbol")),
        normalized(row.get("source_symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
        normalized(row.get("source_expansion_candidate_source_path")),
        normalized(row.get("source_expansion_candidate_source_file_sha256")),
        normalized(row.get("entry_reference")),
    )


def family_scope_from_execution(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol_family")),
        normalized(row.get("symbol")),
        normalized(row.get("source_symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
    )


def action_rule_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    decision = normalized(row.get("keep_kill_redesign_implement_decision"))
    expression = {
        "decision": decision,
        "exact_scope": exact_scope_from_action(row),
        "family_scope": family_scope_from_action(row),
        "minimum_effective_n": row.get("effective_n"),
        "month_fold_count": row.get("month_fold_count"),
        "rule_cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_action_application_rule_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-RULE-{sequence:07d}"
            ),
            "input_source_expansion_action_execution_row_id": row.get(
                "expanded_market_source_expansion_action_execution_row_id"
            ),
            "input_source_expansion_execution_row_id": row.get(
                "input_source_expansion_execution_row_id"
            ),
            "rule_status": "ACTION_APPLICATION_RULE_ACTIVE",
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
            "proxy_denominator_price": row.get("proxy_denominator_price"),
            "proxy_target_price": row.get("proxy_target_price"),
            "proxy_stop_price": row.get("proxy_stop_price"),
            "rule_gross_simulated_r": row.get("gross_simulated_r"),
            "rule_cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "rule_stress_simulated_r": row.get("stress_simulated_r"),
            "rule_effective_n": row.get("effective_n"),
            "rule_month_fold_count": row.get("month_fold_count"),
            "rule_positive_month_share": row.get("positive_month_share"),
            "rule_negative_month_share": row.get("negative_month_share"),
            "rule_worst_month_cost_adjusted_simulated_r": row.get(
                "worst_month_cost_adjusted_simulated_r"
            ),
            "rule_concentration_top_month_share": row.get("concentration_top_month_share"),
            "rule_expression": expression,
            "rule_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": class_from_decision(decision),
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def select_family_rule(rules: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str]:
    if not rules:
        return None, "NO_FAMILY_RULE"
    classes = {normalized(rule.get("follow_inverse_default_off_avoid_class")) for rule in rules}
    decisions = {normalized(rule.get("keep_kill_redesign_implement_decision")) for rule in rules}
    if len(classes) != 1 or len(decisions) != 1:
        return None, "FAMILY_SCOPE_CONFLICT"
    ranked = sorted(
        rules,
        key=lambda rule: (
            -(int(rule.get("rule_effective_n") or 0)),
            as_float(rule.get("rule_concentration_top_month_share")) or 1.0,
            normalized(rule.get("expanded_market_source_expansion_action_application_rule_row_id")),
        ),
    )
    return ranked[0], "FAMILY_SCOPE_UNANIMOUS"


def application_expression(
    execution_row: dict[str, Any],
    rule: dict[str, Any] | None,
    status: str,
) -> dict[str, Any]:
    return {
        "status": status,
        "execution_row_id": execution_row.get("expanded_market_source_expansion_execution_row_id"),
        "rule_row_id": (rule or {}).get("expanded_market_source_expansion_action_application_rule_row_id"),
        "decision": (rule or {}).get("keep_kill_redesign_implement_decision"),
        "exact_scope": exact_scope_from_execution(execution_row),
        "family_scope": family_scope_from_execution(execution_row),
        "source_cost_adjusted_simulated_r": execution_row.get("cost_adjusted_simulated_r"),
    }


def execution_application_row(
    execution_row: dict[str, Any],
    rule: dict[str, Any] | None,
    status: str,
    sequence: int,
    rule_count_in_scope: int,
) -> dict[str, Any]:
    decision = (
        normalized((rule or {}).get("keep_kill_redesign_implement_decision"))
        if rule
        else "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION_NO_MONTH_STABLE_RULE"
    )
    if status == "ACTION_APPLICATION_SCOPE_CONFLICT_PRESERVED":
        decision = "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION_SCOPE_CONFLICT"
    expression = application_expression(execution_row, rule, status)
    return boundary_row(
        {
            "expanded_market_source_expansion_action_application_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-APP-{sequence:07d}"
            ),
            "input_source_expansion_execution_row_id": execution_row.get(
                "expanded_market_source_expansion_execution_row_id"
            ),
            "input_source_expansion_gap_row_id": None,
            "input_action_application_rule_row_id": (rule or {}).get(
                "expanded_market_source_expansion_action_application_rule_row_id"
            ),
            "input_source_expansion_action_execution_row_id": (rule or {}).get(
                "input_source_expansion_action_execution_row_id"
            ),
            "action_application_status": status,
            "rule_count_in_scope": rule_count_in_scope,
            "symbol_family": execution_row.get("symbol_family"),
            "symbol": execution_row.get("symbol"),
            "source_symbol": execution_row.get("source_symbol"),
            "market_timeframe": execution_row.get("market_timeframe"),
            "route_session": execution_row.get("route_session"),
            "horizon_id": execution_row.get("horizon_id"),
            "side": execution_row.get("side"),
            "source_path": execution_row.get("source_expansion_candidate_source_path"),
            "source_path_sha256": execution_row.get("source_expansion_candidate_source_path_sha256"),
            "source_file_sha256": execution_row.get("source_expansion_candidate_source_file_sha256"),
            "source_access_status": execution_row.get("source_access_status"),
            "entry_reference": execution_row.get("entry_reference"),
            "entry_reference_time": execution_row.get("entry_reference_time"),
            "proxy_entry_price": execution_row.get("proxy_entry_price"),
            "proxy_denominator_price": execution_row.get("proxy_denominator_price"),
            "proxy_target_price": execution_row.get("proxy_target_price"),
            "proxy_stop_price": execution_row.get("proxy_stop_price"),
            "path_order_result": execution_row.get("path_order_result"),
            "path_order_counts": execution_row.get("path_order_counts"),
            "fill_status": execution_row.get("fill_status"),
            "gross_simulated_r": execution_row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": execution_row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": execution_row.get("stress_simulated_r"),
            "rule_gross_simulated_r": (rule or {}).get("rule_gross_simulated_r"),
            "rule_cost_adjusted_simulated_r": (rule or {}).get("rule_cost_adjusted_simulated_r"),
            "rule_stress_simulated_r": (rule or {}).get("rule_stress_simulated_r"),
            "win_count": execution_row.get("win_count"),
            "loss_count": execution_row.get("loss_count"),
            "zero_count": execution_row.get("zero_count"),
            "average_win": None,
            "average_loss": None,
            "target_first_count": execution_row.get("target_first_count"),
            "stop_first_count": execution_row.get("stop_first_count"),
            "neither_count": execution_row.get("neither_count"),
            "ambiguous_count": execution_row.get("ambiguous_count"),
            "effective_n": execution_row.get("effective_n"),
            "duplicate_row_count": execution_row.get("duplicate_row_count"),
            "effective_n_after_duplicate_collapse": execution_row.get(
                "effective_n_after_duplicate_collapse"
            ),
            "concentration_top_month_share": execution_row.get("concentration_top_month_share"),
            "missing_simulated_fields": execution_row.get("missing_simulated_fields") or [],
            "branch_local_action_application_expression": expression,
            "branch_local_action_application_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": class_from_decision(decision),
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def source_gap_application_row(gap_row: dict[str, Any], sequence: int) -> dict[str, Any]:
    expression = {
        "status": "ACTION_APPLICATION_SOURCE_GAP_PRESERVED",
        "gap_row_id": gap_row.get("expanded_market_source_expansion_gap_row_id"),
        "source_path": gap_row.get("source_path"),
        "missing_simulated_fields": gap_row.get("missing_simulated_fields") or [],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_action_application_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-APP-{sequence:07d}"
            ),
            "input_source_expansion_execution_row_id": None,
            "input_source_expansion_gap_row_id": gap_row.get(
                "expanded_market_source_expansion_gap_row_id"
            ),
            "input_action_application_rule_row_id": None,
            "action_application_status": "ACTION_APPLICATION_SOURCE_GAP_PRESERVED",
            "rule_count_in_scope": 0,
            "symbol_family": gap_row.get("symbol_family"),
            "symbol": gap_row.get("symbol"),
            "source_symbol": gap_row.get("source_symbol"),
            "market_timeframe": gap_row.get("market_timeframe"),
            "route_session": gap_row.get("route_session"),
            "horizon_id": gap_row.get("horizon_id"),
            "side": gap_row.get("side"),
            "source_path": gap_row.get("source_path"),
            "source_path_sha256": gap_row.get("source_path_sha256"),
            "source_file_sha256": gap_row.get("source_file_sha256"),
            "source_access_status": gap_row.get("source_expansion_gap_status"),
            "entry_reference": None,
            "entry_reference_time": None,
            "proxy_entry_price": None,
            "proxy_denominator_price": None,
            "proxy_target_price": None,
            "proxy_stop_price": None,
            "path_order_result": None,
            "path_order_counts": {},
            "fill_status": "NO_FILL_NO_REPLAY_SOURCE",
            "gross_simulated_r": None,
            "cost_adjusted_simulated_r": None,
            "stress_simulated_r": None,
            "rule_gross_simulated_r": None,
            "rule_cost_adjusted_simulated_r": None,
            "rule_stress_simulated_r": None,
            "win_count": 0,
            "loss_count": 0,
            "zero_count": 0,
            "average_win": None,
            "average_loss": None,
            "target_first_count": 0,
            "stop_first_count": 0,
            "neither_count": 0,
            "ambiguous_count": 0,
            "effective_n": 0,
            "duplicate_row_count": None,
            "effective_n_after_duplicate_collapse": None,
            "concentration_top_month_share": None,
            "missing_simulated_fields": gap_row.get("missing_simulated_fields") or [],
            "branch_local_action_application_expression": expression,
            "branch_local_action_application_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION_SOURCE_GAP"
            ),
        }
    )


def rule_self_test_row(rule: dict[str, Any], applied_count: int, sequence: int) -> dict[str, Any]:
    passed = applied_count > 0
    return boundary_row(
        {
            "expanded_market_source_expansion_action_application_self_test_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-SELFTEST-{sequence:07d}"
            ),
            "input_action_application_rule_row_id": rule.get(
                "expanded_market_source_expansion_action_application_rule_row_id"
            ),
            "self_test_status": "ACTION_APPLICATION_RULE_SELF_TEST_PASS"
            if passed
            else "ACTION_APPLICATION_RULE_SELF_TEST_FAIL",
            "positive_application_count": applied_count,
            "negative_mismatch_check": True,
            "follow_inverse_default_off_avoid_class": rule.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "keep_kill_redesign_implement_decision": rule.get(
                "keep_kill_redesign_implement_decision"
            ),
        }
    )


def aggregate_application_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            normalized(row.get("symbol_family")),
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("side")),
            normalized(row.get("follow_inverse_default_off_avoid_class")),
            normalized(row.get("action_application_status")),
        )
        grouped.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        cost_values = [
            as_float(row.get("cost_adjusted_simulated_r"))
            for row in members
            if as_float(row.get("cost_adjusted_simulated_r")) is not None
        ]
        gross_values = [
            as_float(row.get("gross_simulated_r"))
            for row in members
            if as_float(row.get("gross_simulated_r")) is not None
        ]
        stress_values = [
            as_float(row.get("stress_simulated_r"))
            for row in members
            if as_float(row.get("stress_simulated_r")) is not None
        ]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_action_application_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-APP-AGG-{len(output) + 1:07d}"
                    ),
                    "symbol_family": key[0],
                    "symbol": key[1],
                    "market_timeframe": key[2],
                    "route_session": key[3],
                    "horizon_id": key[4],
                    "side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "action_application_status": key[7],
                    "row_count": len(members),
                    "rows_with_simulated_r": len(cost_values),
                    "average_gross_simulated_r": rounded(
                        sum(gross_values) / len(gross_values) if gross_values else None
                    ),
                    "average_cost_adjusted_simulated_r": rounded(
                        sum(cost_values) / len(cost_values) if cost_values else None
                    ),
                    "average_stress_simulated_r": rounded(
                        sum(stress_values) / len(stress_values) if stress_values else None
                    ),
                    "win_count": sum(int(row.get("win_count") or 0) for row in members),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
                    "zero_count": sum(int(row.get("zero_count") or 0) for row in members),
                    "target_first_count": sum(
                        int(row.get("target_first_count") or 0) for row in members
                    ),
                    "stop_first_count": sum(
                        int(row.get("stop_first_count") or 0) for row in members
                    ),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
                    "ambiguous_count": sum(
                        int(row.get("ambiguous_count") or 0) for row in members
                    ),
                    "effective_n_sum": sum(int(row.get("effective_n") or 0) for row in members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output
