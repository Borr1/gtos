"""Implementation and redesign actions from expanded-market stress qualification rows."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any


EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unified_implementation_actions.py"
)
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
    output["expanded_market_unified_implementation_actions_surface"] = (
        EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def sha_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def scope_value(row: dict[str, Any], field: str) -> Any:
    return row.get(field)


def numeric_scope(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "source_path": row.get("source_path"),
        "source_file_sha256": row.get("source_file_sha256"),
        "selected_side": row.get("selected_side"),
        "minimum_cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
        "minimum_stress_simulated_r": row.get("stress_simulated_r"),
        "minimum_effective_n": row.get("effective_n"),
        "minimum_target_stop_edge_share": row.get("target_stop_edge_share"),
        "maximum_ambiguous_share": row.get("ambiguous_share"),
        "maximum_concentration_top_month_share": row.get("concentration_top_month_share"),
    }


def action_expression(row: dict[str, Any], include_source_path: bool = True) -> str:
    equality_fields = [
        "symbol",
        "source_symbol",
        "market_timeframe",
        "route_session",
        "horizon_id",
        "source_component",
        "selected_side",
    ]
    if include_source_path:
        equality_fields.extend(["source_path", "source_file_sha256"])
    predicates = [f"row.get({field!r}) == {normalized(row.get(field))!r}" for field in equality_fields]
    thresholds = [
        ("cost_adjusted_simulated_r", "cost_adjusted_simulated_r"),
        ("stress_simulated_r", "stress_simulated_r"),
        ("effective_n", "effective_n"),
        ("target_stop_edge_share", "target_stop_edge_share"),
    ]
    for row_field, threshold_field in thresholds:
        value = as_float(row.get(threshold_field))
        if value is not None:
            predicates.append(f"float(row.get({row_field!r}) or -999999999.0) >= {rounded(value)}")
    ambiguous = as_float(row.get("ambiguous_share"))
    if ambiguous is not None:
        predicates.append(f"float(row.get('ambiguous_share') or 999999999.0) <= {rounded(ambiguous)}")
    concentration = as_float(row.get("concentration_top_month_share"))
    if concentration is not None:
        predicates.append(
            f"float(row.get('concentration_top_month_share') or 999999999.0) <= {rounded(concentration)}"
        )
    return " and ".join(predicates)


def action_decision(row: dict[str, Any], row_kind: str) -> tuple[str, str, str, str]:
    stress_decision = normalized(row.get("keep_kill_redesign_implement_decision"))
    reason = normalized(row.get("stress_blocking_reason"))
    if row_kind == "terminal":
        return (
            "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_TERMINAL_CAPACITY",
            "TERMINAL_CAPACITY_REDESIGN_ACTION",
            "expanded_market_terminal_capacity_redesign",
            "redesign",
        )
    if stress_decision == "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED":
        if row_kind == "decision":
            return (
                "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_DECISION_SCOPE",
                "DECISION_SCOPE_ACTION_READY",
                "expanded_market_stress_qualified_decision_scope",
                "follow",
            )
        return (
            "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SCORER_ROW",
            "SCORER_ROW_ACTION_READY",
            "expanded_market_stress_qualified_scorer_row",
            "follow",
        )
    if reason == "underpowered_effective_n":
        return (
            "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_UNDERPOWERED",
            "UNDERPOWERED_REDESIGN_ACTION",
            "expanded_market_underpowered_redesign",
            "redesign",
        )
    if stress_decision.startswith("KILL_"):
        return (
            "KILL_EXPANDED_MARKET_UNIFIED_ACTION_NUMERIC_FAILURE",
            "NUMERIC_FAILURE_ACTION",
            "expanded_market_numeric_failure",
            "default-off",
        )
    return (
        "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_NUMERIC_CONDITION",
        "NUMERIC_CONDITION_REDESIGN_ACTION",
        "expanded_market_numeric_condition_redesign",
        "redesign",
    )


def action_row(row: dict[str, Any], row_id: str, row_kind: str) -> dict[str, Any]:
    decision, status, family, class_name = action_decision(row, row_kind)
    include_source_path = row_kind != "decision"
    scope = numeric_scope(row)
    expression = action_expression(row, include_source_path=include_source_path)
    output = {
        "unified_implementation_action_row_id": row_id,
        "action_row_kind": row_kind,
        "input_unified_stress_qualification_row_id": row.get("unified_stress_qualification_row_id"),
        "input_unified_stress_decision_row_id": row.get("unified_stress_decision_row_id"),
        "input_unified_final_evidence_row_id": row.get("input_unified_final_evidence_row_id"),
        "input_unified_final_terminal_redesign_row_id": row.get(
            "input_unified_final_terminal_redesign_row_id"
        ),
        "input_unified_final_decision_row_id": row.get("input_unified_final_decision_row_id"),
        "input_unified_numeric_decision_row_id": row.get("input_unified_numeric_decision_row_id"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "source_path": row.get("source_path"),
        "source_file_sha256": row.get("source_file_sha256"),
        "selected_side": row.get("selected_side"),
        "entry_reference": row.get("entry_reference"),
        "proxy_entry_price": row.get("proxy_entry_price"),
        "proxy_stop_price": row.get("proxy_stop_price"),
        "proxy_target_price": row.get("proxy_target_price"),
        "proxy_denominator_price": row.get("proxy_denominator_price"),
        "path_order_result": row.get("path_order_result"),
        "fill_status": row.get("fill_status"),
        "gross_simulated_r": row.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": row.get("stress_simulated_r"),
        "win_count": row.get("win_count"),
        "loss_count": row.get("loss_count"),
        "flat_count": row.get("flat_count"),
        "zero_count": row.get("zero_count"),
        "no_fill_count": row.get("no_fill_count"),
        "average_win": row.get("average_win"),
        "average_loss": row.get("average_loss"),
        "target_first_count": row.get("target_first_count"),
        "stop_first_count": row.get("stop_first_count"),
        "neither_count": row.get("neither_count"),
        "ambiguous_count": row.get("ambiguous_count"),
        "effective_n": row.get("effective_n"),
        "effective_n_after_duplicate_collapse": row.get("effective_n_after_duplicate_collapse"),
        "duplicate_row_count": row.get("duplicate_row_count"),
        "target_first_share": row.get("target_first_share"),
        "stop_first_share": row.get("stop_first_share"),
        "target_stop_edge_share": row.get("target_stop_edge_share"),
        "ambiguous_share": row.get("ambiguous_share"),
        "concentration_top_month_share": row.get("concentration_top_month_share"),
        "stress_blocking_reason": row.get("stress_blocking_reason"),
        "source_stress_decision": row.get("keep_kill_redesign_implement_decision"),
        "branch_local_action_family": family,
        "branch_local_action_status": status,
        "branch_local_action_scope": scope,
        "branch_local_action_scope_sha256": sha_payload(scope),
        "branch_local_action_expression": expression,
        "branch_local_action_expression_sha256": sha_payload({"expression": expression}),
        "keep_kill_redesign_implement_decision": decision,
        "follow_inverse_default_off_avoid_class": class_name,
    }
    return boundary_row(output)


def unified_implementation_action_rows(
    evidence_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    evidence_actions = [
        action_row(
            row,
            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-EVIDENCE-{index:08d}",
            "evidence",
        )
        for index, row in enumerate(
            sorted(evidence_rows, key=lambda item: normalized(item.get("unified_stress_qualification_row_id"))),
            start=1,
        )
    ]
    terminal_actions = [
        action_row(
            row,
            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-TERMINAL-{index:08d}",
            "terminal",
        )
        for index, row in enumerate(
            sorted(terminal_rows, key=lambda item: normalized(item.get("unified_stress_qualification_row_id"))),
            start=1,
        )
    ]
    decision_actions = [
        action_row(
            row,
            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-DECISION-{index:06d}",
            "decision",
        )
        for index, row in enumerate(
            sorted(decision_rows, key=lambda item: normalized(item.get("unified_stress_decision_row_id"))),
            start=1,
        )
    ]
    all_actions = evidence_actions + terminal_actions + decision_actions
    redesign_actions = [
        boundary_row(
            {
                "unified_redesign_action_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-REDESIGN-ACTION-{index:06d}"
                ),
                "input_unified_implementation_action_row_id": row.get("unified_implementation_action_row_id"),
                "action_row_kind": row.get("action_row_kind"),
                "symbol": row.get("symbol"),
                "market_timeframe": row.get("market_timeframe"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "source_component": row.get("source_component"),
                "source_path": row.get("source_path"),
                "source_file_sha256": row.get("source_file_sha256"),
                "selected_side": row.get("selected_side"),
                "stress_blocking_reason": row.get("stress_blocking_reason"),
                "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
                "stress_simulated_r": row.get("stress_simulated_r"),
                "effective_n": row.get("effective_n"),
                "branch_local_action_status": row.get("branch_local_action_status"),
                "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
                "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
            }
        )
        for index, row in enumerate(
            [
                row
                for row in all_actions
                if normalized(row.get("keep_kill_redesign_implement_decision")).startswith("REDESIGN_")
                or normalized(row.get("keep_kill_redesign_implement_decision")).startswith("KILL_")
            ],
            start=1,
        )
    ]
    aggregate_actions = aggregate_action_rows(all_actions)
    return evidence_actions, terminal_actions, decision_actions, redesign_actions, aggregate_actions


def aggregate_action_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("portfolio", []),
        ("action_kind", ["action_row_kind"]),
        ("action_status", ["branch_local_action_status"]),
        ("decision", ["keep_kill_redesign_implement_decision"]),
        ("class", ["follow_inverse_default_off_avoid_class"]),
        ("symbol", ["symbol"]),
        ("symbol_timeframe", ["symbol", "market_timeframe"]),
        ("source_component", ["source_component"]),
    ]
    output: list[dict[str, Any]] = []
    for level, fields in specs:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[tuple(row.get(field) for field in fields)].append(row)
        for key, members in sorted(groups.items(), key=lambda item: tuple(normalized(part) for part in item[0])):
            output.append(
                boundary_row(
                    {
                        "unified_action_aggregate_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-AGG-{len(output) + 1:06d}"
                        ),
                        "aggregate_level": level,
                        "aggregate_dimensions": {field: value for field, value in zip(fields, key)},
                        "row_count": len(members),
                        "source_path_count": len({member.get("source_path") for member in members if member.get("source_path")}),
                        "effective_n_sum": sum(as_int(member.get("effective_n")) for member in members),
                        "implementation_action_rows": sum(
                            1
                            for member in members
                            if normalized(member.get("keep_kill_redesign_implement_decision")).startswith("IMPLEMENT_")
                        ),
                        "redesign_action_rows": sum(
                            1
                            for member in members
                            if normalized(member.get("keep_kill_redesign_implement_decision")).startswith("REDESIGN_")
                        ),
                        "kill_action_rows": sum(
                            1
                            for member in members
                            if normalized(member.get("keep_kill_redesign_implement_decision")).startswith("KILL_")
                        ),
                        "cost_adjusted_simulated_r_min": rounded(
                            min((as_float(member.get("cost_adjusted_simulated_r")) or 0.0) for member in members)
                        ),
                        "cost_adjusted_simulated_r_max": rounded(
                            max((as_float(member.get("cost_adjusted_simulated_r")) or 0.0) for member in members)
                        ),
                        "stress_simulated_r_min": rounded(
                            min((as_float(member.get("stress_simulated_r")) or 0.0) for member in members)
                        ),
                        "stress_simulated_r_max": rounded(
                            max((as_float(member.get("stress_simulated_r")) or 0.0) for member in members)
                        ),
                        "keep_kill_redesign_implement_decision": aggregate_decision(members),
                        "follow_inverse_default_off_avoid_class": aggregate_class(members),
                    }
                )
            )
    return output


def aggregate_decision(rows: list[dict[str, Any]]) -> str:
    decisions = {normalized(row.get("keep_kill_redesign_implement_decision")) for row in rows}
    if all(decision.startswith("IMPLEMENT_") for decision in decisions):
        return "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_AGGREGATE"
    if all(decision.startswith("REDESIGN_") for decision in decisions):
        return "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_AGGREGATE"
    if any(decision.startswith("KILL_") for decision in decisions):
        return "KILL_EXPANDED_MARKET_UNIFIED_ACTION_AGGREGATE"
    return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_UNIFIED_ACTION_AGGREGATE"


def aggregate_class(rows: list[dict[str, Any]]) -> str:
    classes = {normalized(row.get("follow_inverse_default_off_avoid_class")) for row in rows}
    classes.discard("")
    return next(iter(classes)) if len(classes) == 1 else "mixed"


def system_unified_implementation_action_rows(
    evidence_actions: list[dict[str, Any]],
    terminal_actions: list[dict[str, Any]],
    decision_actions: list[dict[str, Any]],
    redesign_actions: list[dict[str, Any]],
    aggregate_actions: list[dict[str, Any]],
    input_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    all_actions = evidence_actions + terminal_actions + decision_actions
    return [
        boundary_row(
            {
                "system_row_id": "OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SYSTEM-000001",
                "input_counts": input_counts,
                "evidence_action_rows": len(evidence_actions),
                "terminal_action_rows": len(terminal_actions),
                "decision_action_rows": len(decision_actions),
                "redesign_action_rows": len(redesign_actions),
                "aggregate_rows": len(aggregate_actions),
                "total_action_rows": len(all_actions),
                "implementation_action_rows": sum(
                    1
                    for row in all_actions
                    if normalized(row.get("keep_kill_redesign_implement_decision")).startswith("IMPLEMENT_")
                ),
                "terminal_capacity_action_rows": sum(
                    1
                    for row in all_actions
                    if row.get("keep_kill_redesign_implement_decision")
                    == "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_TERMINAL_CAPACITY"
                ),
                "underpowered_redesign_action_rows": sum(
                    1
                    for row in all_actions
                    if row.get("keep_kill_redesign_implement_decision")
                    == "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_UNDERPOWERED"
                ),
                "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SYSTEM",
                "follow_inverse_default_off_avoid_class": "mixed",
            }
        )
    ]
