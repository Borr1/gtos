"""Stress qualification over expanded-market unified numeric evidence."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


EXPANDED_MARKET_UNIFIED_STRESS_QUALIFICATION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unified_stress_qualification.py"
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
    output["expanded_market_unified_stress_qualification_surface"] = (
        EXPANDED_MARKET_UNIFIED_STRESS_QUALIFICATION_SURFACE
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


def stress_flags(row: dict[str, Any]) -> dict[str, Any]:
    cost_r = as_float(row.get("cost_adjusted_simulated_r"))
    stress_r = as_float(row.get("stress_simulated_r"))
    effective_n = as_int(row.get("effective_n"))
    target_first_share = as_float(row.get("target_first_share"))
    stop_first_share = as_float(row.get("stop_first_share"))
    ambiguous_share = as_float(row.get("ambiguous_share"))
    if target_first_share is None or stop_first_share is None:
        target_first = as_int(row.get("target_first_count"))
        stop_first = as_int(row.get("stop_first_count"))
        neither = as_int(row.get("neither_count"))
        ambiguous = as_int(row.get("ambiguous_count"))
        total = target_first + stop_first + neither + ambiguous
        target_first_share = None if total == 0 else target_first / total
        stop_first_share = None if total == 0 else stop_first / total
        ambiguous_share = None if total == 0 else ambiguous / total
    path_edge_share = None
    if target_first_share is not None and stop_first_share is not None:
        path_edge_share = target_first_share - stop_first_share
    concentration = as_float(row.get("concentration_top_month_share"))
    source_status = row.get("source_access_status")
    return {
        "cost_positive_pass": cost_r is not None and cost_r > 0,
        "cost_margin_pass": cost_r is not None and cost_r >= 0.10,
        "stress_positive_pass": stress_r is not None and stress_r > 0,
        "effective_n_pass": effective_n >= 100,
        "path_edge_pass": path_edge_share is not None and path_edge_share > 0,
        "ambiguity_pass": ambiguous_share is not None and ambiguous_share <= 0.15,
        "concentration_pass": concentration is not None and concentration <= 0.40,
        "source_access_pass": source_status in (None, "SOURCE_PATH_HASH_CONFIRMED"),
        "cost_margin_r": rounded(cost_r),
        "stress_margin_r": rounded(stress_r),
        "target_first_share": rounded(target_first_share),
        "stop_first_share": rounded(stop_first_share),
        "target_stop_edge_share": rounded(path_edge_share),
        "ambiguous_share": rounded(ambiguous_share),
        "concentration_top_month_share": rounded(concentration),
    }


def qualification_decision(row: dict[str, Any], terminal: bool = False) -> tuple[str, str, str]:
    flags = stress_flags(row)
    if terminal:
        if flags["cost_positive_pass"] and flags["stress_positive_pass"] and flags["source_access_pass"]:
            return (
                "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_TERMINAL_CAPACITY",
                "terminal_capacity_not_performance_failure",
                "redesign",
            )
        return (
            "KILL_EXPANDED_MARKET_UNIFIED_STRESS_TERMINAL_NUMERIC_FAILURE",
            "terminal_numeric_failure",
            "default-off",
        )
    checks = [
        ("cost_positive_pass", "cost_not_positive", "KILL_EXPANDED_MARKET_UNIFIED_STRESS_COST"),
        ("stress_positive_pass", "stress_not_positive", "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_BUFFER"),
        ("effective_n_pass", "underpowered_effective_n", "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_UNDERPOWERED"),
        ("cost_margin_pass", "thin_cost_margin", "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_COST_MARGIN"),
        ("path_edge_pass", "path_edge_not_positive", "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_PATH_EDGE"),
        ("ambiguity_pass", "ambiguous_path_share_high", "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_AMBIGUITY"),
        ("concentration_pass", "concentration_high", "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_CONCENTRATION"),
        ("source_access_pass", "source_access_not_confirmed", "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_SOURCE"),
    ]
    for flag, reason, decision in checks:
        if not flags[flag]:
            return decision, reason, "redesign" if not decision.startswith("KILL_") else "default-off"
    return "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED", "all_numeric_stress_checks_pass", "follow"


def qualification_row(row: dict[str, Any], row_id: str, input_id_field: str, terminal: bool = False) -> dict[str, Any]:
    flags = stress_flags(row)
    decision, reason, class_name = qualification_decision(row, terminal=terminal)
    output = {
        "unified_stress_qualification_row_id": row_id,
        input_id_field: row.get(input_id_field.replace("input_", "")) or row.get(input_id_field),
        "input_unified_final_decision_row_id": row.get("input_unified_final_decision_row_id"),
        "numeric_row_kind": row.get("numeric_row_kind"),
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
        **flags,
        "stress_blocking_reason": reason,
        "keep_kill_redesign_implement_decision": decision,
        "follow_inverse_default_off_avoid_class": class_name,
    }
    return boundary_row(output)


def unified_stress_qualification_rows(
    evidence_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    evidence_output = [
        qualification_row(
            row,
            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRESS-EVIDENCE-{index:08d}",
            "input_unified_final_evidence_row_id",
        )
        for index, row in enumerate(
            sorted(evidence_rows, key=lambda item: normalized(item.get("unified_numeric_evidence_row_id"))),
            start=1,
        )
    ]
    terminal_output = [
        qualification_row(
            row,
            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRESS-TERMINAL-{index:08d}",
            "input_unified_final_terminal_redesign_row_id",
            terminal=True,
        )
        for index, row in enumerate(
            sorted(terminal_rows, key=lambda item: normalized(item.get("unified_numeric_evidence_row_id"))),
            start=1,
        )
    ]
    decision_output = []
    for index, row in enumerate(
        sorted(decision_rows, key=lambda item: normalized(item.get("unified_numeric_decision_row_id"))),
        start=1,
    ):
        decision, reason, class_name = qualification_decision(row)
        flags = stress_flags(row)
        decision_output.append(
            boundary_row(
                {
                    "unified_stress_decision_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRESS-DECISION-{index:06d}"
                    ),
                    "input_unified_numeric_decision_row_id": row.get("unified_numeric_decision_row_id"),
                    "input_unified_final_decision_row_id": row.get("input_unified_final_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "selected_side": row.get("selected_side"),
                    "numeric_evidence_rows": row.get("numeric_evidence_rows"),
                    "source_path_count": row.get("source_path_count"),
                    "source_hash_count": row.get("source_hash_count"),
                    "gross_simulated_r": row.get("gross_simulated_r"),
                    "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
                    "stress_simulated_r": row.get("stress_simulated_r"),
                    "expectancy": row.get("expectancy"),
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
                    **flags,
                    "stress_blocking_reason": reason,
                    "keep_kill_redesign_implement_decision": decision,
                    "follow_inverse_default_off_avoid_class": class_name,
                }
            )
        )
    aggregate_output = aggregate_stress_rows(evidence_output + terminal_output + decision_output)
    issue_output = [
        boundary_row(
            {
                "unified_stress_issue_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRESS-ISSUE-{index:06d}"
                ),
                "input_stress_row_id": row.get("unified_stress_qualification_row_id")
                or row.get("unified_stress_decision_row_id"),
                "stress_blocking_reason": row.get("stress_blocking_reason"),
                "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
                "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
            }
        )
        for index, row in enumerate(
            [
                row
                for row in evidence_output + decision_output
                if row.get("keep_kill_redesign_implement_decision") != "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED"
            ],
            start=1,
        )
    ]
    return evidence_output, terminal_output, decision_output, aggregate_output, issue_output


def aggregate_stress_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("portfolio", []),
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
                        "unified_stress_aggregate_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRESS-AGG-{len(output) + 1:06d}"
                        ),
                        "aggregate_level": level,
                        "aggregate_dimensions": {field: value for field, value in zip(fields, key)},
                        "row_count": len(members),
                        "effective_n_sum": sum(as_int(row.get("effective_n")) for row in members),
                        "cost_adjusted_simulated_r_min": rounded(
                            min((as_float(row.get("cost_adjusted_simulated_r")) or 0.0) for row in members)
                        ),
                        "cost_adjusted_simulated_r_max": rounded(
                            max((as_float(row.get("cost_adjusted_simulated_r")) or 0.0) for row in members)
                        ),
                        "stress_simulated_r_min": rounded(
                            min((as_float(row.get("stress_simulated_r")) or 0.0) for row in members)
                        ),
                        "stress_simulated_r_max": rounded(
                            max((as_float(row.get("stress_simulated_r")) or 0.0) for row in members)
                        ),
                        "cost_positive_pass_rows": sum(1 for row in members if row.get("cost_positive_pass")),
                        "stress_positive_pass_rows": sum(1 for row in members if row.get("stress_positive_pass")),
                        "effective_n_pass_rows": sum(1 for row in members if row.get("effective_n_pass")),
                        "path_edge_pass_rows": sum(1 for row in members if row.get("path_edge_pass")),
                        "ambiguity_pass_rows": sum(1 for row in members if row.get("ambiguity_pass")),
                        "concentration_pass_rows": sum(1 for row in members if row.get("concentration_pass")),
                        "keep_kill_redesign_implement_decision": aggregate_decision(members),
                        "follow_inverse_default_off_avoid_class": aggregate_class(members),
                    }
                )
            )
    return output


def aggregate_decision(rows: list[dict[str, Any]]) -> str:
    decisions = {row.get("keep_kill_redesign_implement_decision") for row in rows}
    if decisions == {"IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED"}:
        return "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_AGGREGATE"
    if all(normalized(decision).startswith("REDESIGN_") for decision in decisions):
        return "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_AGGREGATE"
    if any(normalized(decision).startswith("KILL_") for decision in decisions):
        return "KILL_EXPANDED_MARKET_UNIFIED_STRESS_AGGREGATE"
    return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_UNIFIED_STRESS_AGGREGATE"


def aggregate_class(rows: list[dict[str, Any]]) -> str:
    classes = {normalized(row.get("follow_inverse_default_off_avoid_class")) for row in rows}
    classes.discard("")
    return next(iter(classes)) if len(classes) == 1 else "mixed"


def system_unified_stress_qualification_rows(
    evidence_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    input_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "system_row_id": "OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRESS-SYSTEM-000001",
                "input_counts": input_counts,
                "stress_evidence_rows": len(evidence_rows),
                "stress_terminal_rows": len(terminal_rows),
                "stress_decision_rows": len(decision_rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "qualified_evidence_rows": sum(
                    1
                    for row in evidence_rows
                    if row.get("keep_kill_redesign_implement_decision")
                    == "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED"
                ),
                "qualified_decision_rows": sum(
                    1
                    for row in decision_rows
                    if row.get("keep_kill_redesign_implement_decision")
                    == "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFIED"
                ),
                "terminal_capacity_rows": sum(
                    1
                    for row in terminal_rows
                    if row.get("keep_kill_redesign_implement_decision")
                    == "REDESIGN_EXPANDED_MARKET_UNIFIED_STRESS_TERMINAL_CAPACITY"
                ),
                "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRESS_SYSTEM",
                "follow_inverse_default_off_avoid_class": "mixed",
            }
        )
    ]
