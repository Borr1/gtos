"""Execute deconcentrated source-expansion rows into branch-local action rows."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_action_execution.py"
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
    output["expanded_market_source_expansion_action_execution_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def monthly_stability(month_rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [
        as_float(row.get("cost_adjusted_simulated_r"))
        for row in month_rows
        if as_float(row.get("cost_adjusted_simulated_r")) is not None
    ]
    gross_values = [
        as_float(row.get("gross_simulated_r"))
        for row in month_rows
        if as_float(row.get("gross_simulated_r")) is not None
    ]
    stress_values = [
        as_float(row.get("stress_simulated_r"))
        for row in month_rows
        if as_float(row.get("stress_simulated_r")) is not None
    ]
    effective_sum = sum(int(row.get("effective_n") or 0) for row in month_rows)
    path_counts: Counter[str] = Counter()
    for row in month_rows:
        for path, count in (row.get("path_order_counts") or {}).items():
            path_counts[path] += int(count)
    if not values:
        return {
            "month_fold_count": 0,
            "positive_month_count": 0,
            "negative_month_count": 0,
            "flat_month_count": 0,
            "positive_month_share": None,
            "negative_month_share": None,
            "average_month_cost_adjusted_simulated_r": None,
            "average_month_gross_simulated_r": None,
            "average_month_stress_simulated_r": None,
            "worst_month": None,
            "worst_month_cost_adjusted_simulated_r": None,
            "best_month": None,
            "best_month_cost_adjusted_simulated_r": None,
            "monthly_effective_n_sum": 0,
            "monthly_path_order_counts": {},
        }
    month_values = [(normalized(row.get("month")), as_float(row.get("cost_adjusted_simulated_r"))) for row in month_rows]
    month_values = [(month, value) for month, value in month_values if value is not None]
    worst = min(month_values, key=lambda item: item[1])
    best = max(month_values, key=lambda item: item[1])
    positive = sum(1 for value in values if value > 0)
    negative = sum(1 for value in values if value < 0)
    flat = sum(1 for value in values if value == 0)
    return {
        "month_fold_count": len(values),
        "positive_month_count": positive,
        "negative_month_count": negative,
        "flat_month_count": flat,
        "positive_month_share": rounded(positive / len(values)),
        "negative_month_share": rounded(negative / len(values)),
        "average_month_cost_adjusted_simulated_r": rounded(sum(values) / len(values)),
        "average_month_gross_simulated_r": rounded(sum(gross_values) / len(gross_values) if gross_values else None),
        "average_month_stress_simulated_r": rounded(
            sum(stress_values) / len(stress_values) if stress_values else None
        ),
        "worst_month": worst[0],
        "worst_month_cost_adjusted_simulated_r": rounded(worst[1]),
        "best_month": best[0],
        "best_month_cost_adjusted_simulated_r": rounded(best[1]),
        "monthly_effective_n_sum": effective_sum,
        "monthly_path_order_counts": dict(sorted(path_counts.items())),
    }


def action_execution_decision(row: dict[str, Any], stats: dict[str, Any]) -> str:
    original = normalized(row.get("keep_kill_redesign_implement_decision"))
    status = normalized(row.get("source_expansion_deconcentration_status"))
    if status == "SOURCE_EXPANSION_DECONCENTRATION_LOCAL_SOURCE_GAP_PRESERVED":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_LOCAL_SOURCE_GAP"
    if status != "SOURCE_EXPANSION_DECONCENTRATION_REPLAYED":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_REPLAY_IMPLEMENTATION"

    cost_r = as_float(row.get("deconcentrated_cost_adjusted_simulated_r"))
    stress_r = as_float(row.get("deconcentrated_stress_simulated_r"))
    effective_n = int(row.get("deconcentrated_effective_n") or 0)
    positive_share = as_float(stats.get("positive_month_share"))
    negative_share = as_float(stats.get("negative_month_share"))
    worst_month = as_float(stats.get("worst_month_cost_adjusted_simulated_r"))
    month_count = int(stats.get("month_fold_count") or 0)

    if cost_r is None:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_REPLAY_IMPLEMENTATION"
    if effective_n < 20:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_UNDERPOWERED"
    if original.startswith("IMPLEMENT"):
        if (
            cost_r >= 0.10
            and (stress_r if stress_r is not None else cost_r) > -0.05
            and month_count >= 2
            and (positive_share or 0.0) >= 0.50
            and (worst_month if worst_month is not None else cost_r) > -0.25
        ):
            return "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_MONTH_INSTABILITY"
    if "AVOID" in original:
        if cost_r < -0.05 and ((negative_share or 0.0) >= 0.50 or (worst_month or 0.0) <= -0.20):
            return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_AVOID_MONTH_INSTABILITY"
    if original.startswith("KILL"):
        if cost_r <= -0.20 and (stress_r if stress_r is not None else cost_r) <= -0.20:
            return "KILL_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_KILL_MONTH_INSTABILITY"
    if cost_r < -0.05 and (negative_share or 0.0) >= 0.50:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
    return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_SIGNAL_GEOMETRY"


def action_expression(row: dict[str, Any], source_execution: dict[str, Any] | None, decision: str) -> dict[str, Any]:
    return {
        "decision": decision,
        "symbol_family": row.get("symbol_family"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
        "source_path": row.get("source_path"),
        "source_file_sha256": row.get("source_file_sha256"),
        "entry_reference": (source_execution or {}).get("entry_reference"),
        "proxy_denominator_price": (source_execution or {}).get("proxy_denominator_price"),
    }


def action_execution_row(
    row: dict[str, Any],
    source_execution: dict[str, Any] | None,
    month_rows: list[dict[str, Any]],
    sequence: int,
) -> dict[str, Any]:
    stats = monthly_stability(month_rows)
    decision = action_execution_decision(row, stats)
    expression = action_expression(row, source_execution, decision)
    source_execution = source_execution or {}
    return boundary_row(
        {
            "expanded_market_source_expansion_action_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-EXEC-{sequence:07d}"
            ),
            "input_source_expansion_deconcentration_row_id": row.get(
                "expanded_market_source_expansion_deconcentration_row_id"
            ),
            "input_source_expansion_execution_row_id": row.get(
                "input_source_expansion_execution_row_id"
            ),
            "input_source_expansion_gap_row_id": row.get("input_source_expansion_gap_row_id"),
            "action_execution_status": "SOURCE_EXPANSION_ACTION_EXECUTED"
            if row.get("source_expansion_deconcentration_status")
            == "SOURCE_EXPANSION_DECONCENTRATION_REPLAYED"
            else "SOURCE_EXPANSION_ACTION_NONCOMPUTABLE_PRESERVED",
            "source_expansion_deconcentration_status": row.get(
                "source_expansion_deconcentration_status"
            ),
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
            "entry_reference": source_execution.get("entry_reference"),
            "entry_reference_time": source_execution.get("entry_reference_time"),
            "proxy_entry_price": source_execution.get("proxy_entry_price"),
            "proxy_denominator_price": source_execution.get("proxy_denominator_price"),
            "proxy_target_price": source_execution.get("proxy_target_price"),
            "proxy_stop_price": source_execution.get("proxy_stop_price"),
            "path_order_result": source_execution.get("path_order_result"),
            "fill_status": source_execution.get("fill_status"),
            "gross_simulated_r": row.get("deconcentrated_gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("deconcentrated_cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("deconcentrated_stress_simulated_r"),
            "win_count": row.get("deconcentrated_win_count"),
            "loss_count": row.get("deconcentrated_loss_count"),
            "zero_count": row.get("deconcentrated_zero_count"),
            "average_win": row.get("deconcentrated_average_win"),
            "average_loss": row.get("deconcentrated_average_loss"),
            "target_first_count": row.get("deconcentrated_target_first_count"),
            "stop_first_count": row.get("deconcentrated_stop_first_count"),
            "neither_count": row.get("deconcentrated_neither_count"),
            "ambiguous_count": row.get("deconcentrated_ambiguous_count"),
            "effective_n": row.get("deconcentrated_effective_n"),
            "duplicate_row_count": source_execution.get("duplicate_row_count"),
            "effective_n_after_duplicate_collapse": source_execution.get(
                "effective_n_after_duplicate_collapse"
            ),
            "concentration_top_month_share": row.get("remaining_top_month_share"),
            "dominant_month_removed": row.get("dominant_month"),
            "original_decision": row.get("keep_kill_redesign_implement_decision"),
            **stats,
            "missing_simulated_fields": row.get("missing_simulated_fields") or [],
            "branch_local_action_expression": expression,
            "branch_local_action_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": class_from_decision(decision),
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def aggregate_action_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                    "expanded_market_source_expansion_action_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-AGG-{len(output) + 1:07d}"
                    ),
                    "symbol_family": key[0],
                    "symbol": key[1],
                    "market_timeframe": key[2],
                    "route_session": key[3],
                    "horizon_id": key[4],
                    "side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
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
