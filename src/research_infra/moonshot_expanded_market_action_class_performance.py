"""Action-class performance rows from expanded-market scorer execution evidence."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_ACTION_CLASS_PERFORMANCE = "src/research_infra/moonshot_expanded_market_action_class_performance.py"
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
    output["expanded_market_action_class_performance_surface"] = EXPANDED_MARKET_ACTION_CLASS_PERFORMANCE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    return [value for value in (as_float(row.get(field)) for row in rows) if value is not None]


def average_win(values: list[float]) -> float | None:
    wins = [value for value in values if value > 0]
    return average(wins)


def average_loss(values: list[float]) -> float | None:
    losses = [value for value in values if value < 0]
    return average(losses)


def observed_cost(row: dict[str, Any]) -> float | None:
    value = as_float(row.get("deconcentrated_cost_adjusted_simulated_r"))
    return value if value is not None else as_float(row.get("cost_adjusted_simulated_r"))


def observed_stress(row: dict[str, Any]) -> float | None:
    value = as_float(row.get("deconcentrated_stress_simulated_r"))
    return value if value is not None else as_float(row.get("stress_simulated_r"))


def observed_gross(row: dict[str, Any]) -> float | None:
    return as_float(row.get("gross_simulated_r"))


def decision_to_action_class(decision: str | None) -> str:
    text = normalized(decision)
    if text.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID_INTELLIGENCE" in text:
        return "avoid"
    if text.startswith("KILL"):
        return "default-off"
    if "SOURCE_REPAIR" in text:
        return "redesign-source-repair"
    if "SOURCE_EXPANSION" in text:
        return "redesign-source-expansion"
    return "redesign-weak-edge"


def action_decision(action_class: str) -> str:
    if action_class == "follow":
        return "IMPLEMENT_EXPANDED_MARKET_ACTION_CLASS_FOLLOW_PERFORMANCE"
    if action_class == "avoid":
        return "IMPLEMENT_EXPANDED_MARKET_ACTION_CLASS_AVOID_SAVED_R"
    if action_class == "default-off":
        return "KILL_EXPANDED_MARKET_ACTION_CLASS_DEFAULT_OFF_SAVED_R"
    if action_class == "redesign-source-repair":
        return "REDESIGN_EXPANDED_MARKET_ACTION_CLASS_SOURCE_REPAIR"
    if action_class == "redesign-source-expansion":
        return "REDESIGN_EXPANDED_MARKET_ACTION_CLASS_SOURCE_EXPANSION"
    return "REDESIGN_EXPANDED_MARKET_ACTION_CLASS_WEAK_EDGE"


def action_missing_fields(action_class: str) -> list[str]:
    if action_class.startswith("redesign"):
        return ["concrete_replay_implementation_for_redesign_action_r"]
    return []


def action_values(row: dict[str, Any], action_class: str) -> dict[str, Any]:
    gross = observed_gross(row)
    cost = observed_cost(row)
    stress = observed_stress(row)
    if action_class == "follow":
        return {
            "primary_action_gross_simulated_r": rounded(gross),
            "primary_action_cost_adjusted_simulated_r": rounded(cost),
            "primary_action_stress_simulated_r": rounded(stress),
            "saved_cost_adjusted_simulated_r": None,
            "proxy_inverse_cost_adjusted_simulated_r": None,
            "default_off_account_simulated_r": None,
            "proxy_geometry_basis": "executed_follow_deconcentrated_replay_geometry",
        }
    if action_class in {"avoid", "default-off"}:
        return {
            "primary_action_gross_simulated_r": rounded(-gross) if gross is not None else None,
            "primary_action_cost_adjusted_simulated_r": rounded(-cost) if cost is not None else None,
            "primary_action_stress_simulated_r": rounded(-stress) if stress is not None else None,
            "saved_cost_adjusted_simulated_r": rounded(-cost) if cost is not None else None,
            "proxy_inverse_cost_adjusted_simulated_r": rounded(-cost) if action_class == "avoid" and cost is not None else None,
            "default_off_account_simulated_r": 0.0 if action_class == "default-off" else None,
            "proxy_geometry_basis": "negated_observed_proxy_r_no_direct_inverse_trade_geometry"
            if action_class == "avoid"
            else "default_off_saved_r_from_observed_negative_proxy",
        }
    return {
        "primary_action_gross_simulated_r": None,
        "primary_action_cost_adjusted_simulated_r": None,
        "primary_action_stress_simulated_r": None,
        "saved_cost_adjusted_simulated_r": None,
        "proxy_inverse_cost_adjusted_simulated_r": None,
        "default_off_account_simulated_r": 0.0,
        "proxy_geometry_basis": "redesign_row_preserves_observed_r_without_action_r",
    }


def base_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol_family": row.get("symbol_family"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
        "performance_source_family": row.get("performance_source_family"),
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
        "observed_gross_simulated_r": row.get("gross_simulated_r"),
        "observed_cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
        "observed_stress_simulated_r": row.get("stress_simulated_r"),
        "observed_deconcentrated_cost_adjusted_simulated_r": row.get("deconcentrated_cost_adjusted_simulated_r"),
        "observed_deconcentrated_stress_simulated_r": row.get("deconcentrated_stress_simulated_r"),
        "deconcentrated_effective_n": row.get("deconcentrated_effective_n"),
        "effective_n": int(row.get("effective_n") or 0),
        "win_count": int(row.get("win_count") or 0),
        "loss_count": int(row.get("loss_count") or 0),
        "zero_count": int(row.get("zero_count") or 0),
        "target_first_count": int(row.get("target_first_count") or 0),
        "stop_first_count": int(row.get("stop_first_count") or 0),
        "neither_count": int(row.get("neither_count") or 0),
        "ambiguous_count": int(row.get("ambiguous_count") or 0),
        "source_path_deconcentration_weight": row.get("source_path_deconcentration_weight"),
        "deconcentrated_top_source_path_effective_n_share": row.get(
            "deconcentrated_top_source_path_effective_n_share"
        ),
        "selection_reason": row.get("selection_reason"),
        "input_decision": row.get("keep_kill_redesign_implement_decision"),
        "input_follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
    }


def action_class_performance_rows(
    member_execution_rows: list[dict[str, Any]],
    evidence_execution_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    issue_rows: list[dict[str, Any]] = []
    for input_family, source_rows in (
        ("member_execution", member_execution_rows),
        ("nonimplement_evidence_execution", evidence_execution_rows),
    ):
        for source in source_rows:
            action_class = decision_to_action_class(source.get("keep_kill_redesign_implement_decision"))
            decision = action_decision(action_class)
            missing_fields = action_missing_fields(action_class)
            row_id = f"OHLC-GTOS-EXPANDED-MARKET-ACTION-CLASS-PERF-{len(rows) + 1:07d}"
            output = boundary_row(
                {
                    "expanded_market_action_class_performance_row_id": row_id,
                    "input_row_family": input_family,
                    "input_member_execution_row_id": source.get(
                        "expanded_market_deconcentrated_scorer_member_execution_row_id"
                    ),
                    "input_nonimplement_evidence_execution_row_id": source.get(
                        "expanded_market_deconcentrated_nonimplement_evidence_execution_row_id"
                    ),
                    "input_selection_row_id": source.get("input_selection_row_id"),
                    "action_class": action_class,
                    "action_missing_simulated_fields": missing_fields,
                    **base_fields(source),
                    **action_values(source, action_class),
                    "follow_inverse_default_off_avoid_class": action_class,
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
            rows.append(output)
            if missing_fields and action_class.startswith("redesign"):
                continue
            if output.get("primary_action_cost_adjusted_simulated_r") is None:
                issue_rows.append(
                    boundary_row(
                        {
                            "expanded_market_action_class_performance_issue_row_id": (
                                f"OHLC-GTOS-EXPANDED-MARKET-ACTION-CLASS-PERF-ISSUE-{len(issue_rows) + 1:06d}"
                            ),
                            "input_action_class_performance_row_id": row_id,
                            "issue_status": "MISSING_PRIMARY_ACTION_COST_ADJUSTED_SIMULATED_R",
                            "action_class": action_class,
                            "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_ACTION_CLASS_PERFORMANCE_ROW",
                        }
                    )
                )
    return rows, issue_rows


def aggregate_action_class_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            normalized(row.get("action_class")),
            normalized(row.get("symbol_family")),
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("side")),
        )
        grouped[key].append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        action_costs = numeric_values(members, "primary_action_cost_adjusted_simulated_r")
        observed_costs = numeric_values(members, "observed_deconcentrated_cost_adjusted_simulated_r")
        saved_costs = numeric_values(members, "saved_cost_adjusted_simulated_r")
        source_counts = Counter(normalized(row.get("source_path")) for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_action_class_performance_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-ACTION-CLASS-PERF-AGG-{len(output) + 1:06d}"
                    ),
                    "action_class": key[0],
                    "symbol_family": key[1],
                    "symbol": key[2],
                    "market_timeframe": key[3],
                    "route_session": key[4],
                    "horizon_id": key[5],
                    "side": key[6],
                    "row_count": len(members),
                    "scored_action_rows": len(action_costs),
                    "missing_action_rows": len(members) - len(action_costs),
                    "observed_expectancy_cost_adjusted_simulated_r": rounded(average(observed_costs)),
                    "primary_action_expectancy_cost_adjusted_simulated_r": rounded(average(action_costs)),
                    "saved_expectancy_cost_adjusted_simulated_r": rounded(average(saved_costs)),
                    "average_action_win_simulated_r": rounded(average_win(action_costs)),
                    "average_action_loss_simulated_r": rounded(average_loss(action_costs)),
                    "effective_n_sum": sum(int(row.get("effective_n") or 0) for row in members),
                    "deconcentrated_effective_n_sum": rounded(
                        sum(float(row.get("deconcentrated_effective_n") or 0.0) for row in members)
                    ),
                    "win_count": sum(int(row.get("win_count") or 0) for row in members),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
                    "zero_count": sum(int(row.get("zero_count") or 0) for row in members),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
                    "source_path_count": len(source_counts),
                    "concentration_top_source_path_share": rounded(
                        (source_counts.most_common(1)[0][1] / len(members)) if members and source_counts else None
                    ),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_action_class_rows(
    rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "expanded_market_action_class_performance_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-ACTION-CLASS-PERF-SYSTEM-0001"
                ),
                "action_class_performance_rows": len(rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "scored_action_rows": sum(
                    1 for row in rows if row.get("primary_action_cost_adjusted_simulated_r") is not None
                ),
                "missing_action_rows": sum(
                    1 for row in rows if row.get("primary_action_cost_adjusted_simulated_r") is None
                ),
                "action_class_counts": dict(sorted(Counter(row.get("action_class") for row in rows).items())),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in rows).items())
                ),
                "source_path_count": len({row.get("source_path") for row in rows}),
                "symbol_family_count": len({row.get("symbol_family") for row in rows}),
                "metadata": metadata,
            }
        )
    ]
