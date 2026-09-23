"""Implementation selection from deconcentrated expanded-market performance rows."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_DECONCENTRATED_IMPLEMENTATION_SELECTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_deconcentrated_implementation_selection.py"
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
    output["expanded_market_deconcentrated_implementation_selection_surface"] = (
        EXPANDED_MARKET_DECONCENTRATED_IMPLEMENTATION_SELECTION_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def implementation_decision(row: dict[str, Any]) -> tuple[str, str]:
    source_decision = normalized(row.get("keep_kill_redesign_implement_decision"))
    if source_decision == "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_PERFORMANCE":
        return "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_CANDIDATE", "numeric_deconcentrated_follow"
    if source_decision == "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_DECONCENTRATION":
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_DECONCENTRATED_SCOPE", "negative_deconcentrated_proxy"
    if source_decision == "KILL_EXPANDED_MARKET_DECONCENTRATED_BRANCH":
        return "KILL_EXPANDED_MARKET_DECONCENTRATED_IMPLEMENTATION_SCOPE", "negative_deconcentrated_stress"
    if source_decision == "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_RESIDUAL_CONCENTRATION":
        return "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_SOURCE_REPAIR", "residual_source_path_concentration"
    if source_decision == "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_SINGLE_SOURCE":
        return "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_SOURCE_EXPANSION", "single_source_path"
    if source_decision == "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_UNDERPOWERED":
        return "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_UNDERPOWERED", "underpowered_after_source_cap"
    if source_decision == "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_MISSING_SIMULATED_R":
        return "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_REPLAY_IMPLEMENTATION", "missing_simulated_r"
    return "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_WEAK_EDGE", "weak_deconcentrated_edge"


def numeric_priority_score(row: dict[str, Any]) -> float | None:
    cost = as_float(row.get("deconcentrated_cost_adjusted_simulated_r"))
    stress = as_float(row.get("deconcentrated_stress_simulated_r"))
    effective_n = as_float(row.get("deconcentrated_effective_n_sum"))
    concentration = as_float(row.get("deconcentrated_top_source_path_effective_n_share"))
    if cost is None or stress is None or effective_n is None or concentration is None:
        return None
    effective_bonus = min(effective_n / 1000.0, 0.25)
    concentration_penalty = max(0.0, concentration - 0.35)
    stress_penalty = max(0.0, -stress) * 0.5
    return rounded(cost + effective_bonus - concentration_penalty - stress_penalty)


def branch_local_expression(row: dict[str, Any]) -> str:
    fields = {
        "symbol_family": row.get("symbol_family"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
        "source_path_sha256": row.get("source_file_sha256"),
    }
    clauses = [f"{key}={normalized(value)}" for key, value in fields.items()]
    return " and ".join(clauses)


def selection_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for row in rows:
        decision, reason = implementation_decision(row)
        missing = list(row.get("missing_simulated_fields") or [])
        priority = numeric_priority_score(row)
        if priority is None:
            missing.append("deconcentrated_priority_score_inputs")
        selection = boundary_row(
            {
                "expanded_market_deconcentrated_selection_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-DECON-SELECT-{len(output) + 1:07d}"
                ),
                "input_deconcentration_row_id": row.get("expanded_market_deconcentration_row_id"),
                "input_source_consensus_row_id": row.get("input_source_consensus_row_id"),
                "performance_source_family": row.get("performance_source_family"),
                "symbol_family": row.get("symbol_family"),
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol"),
                "market_timeframe": row.get("market_timeframe"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "side": row.get("side"),
                "source_component": row.get("source_component"),
                "source_path": row.get("source_path"),
                "source_file_sha256": row.get("source_file_sha256"),
                "source_record_selector": row.get("source_record_selector"),
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
                "deconcentrated_effective_n": row.get("deconcentrated_effective_n"),
                "deconcentrated_effective_n_sum": row.get("deconcentrated_effective_n_sum"),
                "deconcentrated_cost_adjusted_simulated_r": row.get("deconcentrated_cost_adjusted_simulated_r"),
                "deconcentrated_stress_simulated_r": row.get("deconcentrated_stress_simulated_r"),
                "deconcentrated_top_source_path_effective_n_share": row.get(
                    "deconcentrated_top_source_path_effective_n_share"
                ),
                "source_path_deconcentration_weight": row.get("source_path_deconcentration_weight"),
                "win_count": int(row.get("win_count") or 0),
                "loss_count": int(row.get("loss_count") or 0),
                "zero_count": int(row.get("zero_count") or 0),
                "target_first_count": int(row.get("target_first_count") or 0),
                "stop_first_count": int(row.get("stop_first_count") or 0),
                "neither_count": int(row.get("neither_count") or 0),
                "ambiguous_count": int(row.get("ambiguous_count") or 0),
                "effective_n": int(row.get("effective_n") or 0),
                "missing_simulated_fields": sorted(set(missing)),
                "numeric_priority_score": priority,
                "branch_local_selection_expression": branch_local_expression(row),
                "source_deconcentration_decision": row.get("keep_kill_redesign_implement_decision"),
                "selection_reason": reason,
                "keep_kill_redesign_implement_decision": decision,
                "follow_inverse_default_off_avoid_class": class_from_decision(decision),
            }
        )
        output.append(selection)
        if missing:
            issues.append(
                boundary_row(
                    {
                        "expanded_market_deconcentrated_selection_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-DECON-SELECT-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_selection_row_id": selection["expanded_market_deconcentrated_selection_row_id"],
                        "input_deconcentration_row_id": row.get("expanded_market_deconcentration_row_id"),
                        "symbol_family": row.get("symbol_family"),
                        "symbol": row.get("symbol"),
                        "market_timeframe": row.get("market_timeframe"),
                        "route_session": row.get("route_session"),
                        "horizon_id": row.get("horizon_id"),
                        "side": row.get("side"),
                        "source_path": row.get("source_path"),
                        "source_file_sha256": row.get("source_file_sha256"),
                        "missing_simulated_fields": sorted(set(missing)),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_REPLAY_IMPLEMENTATION"
                        ),
                    }
                )
            )
    return output, issues


def aggregate_selection_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(
            (
                normalized(row.get("symbol_family")),
                normalized(row.get("market_timeframe")),
                normalized(row.get("route_session")),
                normalized(row.get("horizon_id")),
                normalized(row.get("side")),
                normalized(row.get("follow_inverse_default_off_avoid_class")),
            ),
            [],
        ).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        costs = [
            value
            for value in (as_float(row.get("deconcentrated_cost_adjusted_simulated_r")) for row in members)
            if value is not None
        ]
        stress = [
            value for value in (as_float(row.get("deconcentrated_stress_simulated_r")) for row in members) if value is not None
        ]
        scores = [value for value in (as_float(row.get("numeric_priority_score")) for row in members) if value is not None]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_deconcentrated_selection_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-DECON-SELECT-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol_family": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "side": key[4],
                    "follow_inverse_default_off_avoid_class": key[5],
                    "row_count": len(members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "source_family_count": len({row.get("performance_source_family") for row in members}),
                    "simulated_r_row_count": len(costs),
                    "missing_simulated_row_count": sum(1 for row in members if row.get("missing_simulated_fields")),
                    "effective_n": sum(int(row.get("effective_n") or 0) for row in members),
                    "deconcentrated_effective_n": rounded(
                        sum(float(row.get("deconcentrated_effective_n") or 0.0) for row in members)
                    ),
                    "win_count": sum(int(row.get("win_count") or 0) for row in members),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
                    "zero_count": sum(int(row.get("zero_count") or 0) for row in members),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
                    "expectancy_deconcentrated_cost_adjusted_simulated_r": rounded(average(costs)),
                    "expectancy_deconcentrated_stress_simulated_r": rounded(average(stress)),
                    "average_numeric_priority_score": rounded(average(scores)),
                    "average_win": rounded(average([value for value in costs if value > 0])),
                    "average_loss": rounded(average([value for value in costs if value < 0])),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0] if decisions else None,
                }
            )
        )
    return output


def system_selection_rows(
    rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "expanded_market_deconcentrated_selection_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-DECON-SELECT-SYSTEM-0001"
                ),
                "selection_rows": len(rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "rows_with_simulated_r": sum(1 for row in rows if not row.get("missing_simulated_fields")),
                "symbol_family_count": len({row.get("symbol_family") for row in rows}),
                "source_path_count": len({row.get("source_path") for row in rows}),
                "source_family_count": len({row.get("performance_source_family") for row in rows}),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in rows).items())
                ),
                "class_counts": dict(sorted(Counter(row.get("follow_inverse_default_off_avoid_class") for row in rows).items())),
                "metadata": metadata,
            }
        )
    ]
