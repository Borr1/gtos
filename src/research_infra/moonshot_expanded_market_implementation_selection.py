"""Implementation-selection rows from expanded-market robustness ledgers."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_IMPLEMENTATION_SELECTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_implementation_selection.py"
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
    output["expanded_market_implementation_selection_surface"] = EXPANDED_MARKET_IMPLEMENTATION_SELECTION_SURFACE
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


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


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


def decision_family(decision: str | None) -> str:
    text = normalized(decision)
    if text.startswith("IMPLEMENT"):
        return "implement"
    if "AVOID" in text:
        return "avoid"
    if text.startswith("KILL"):
        return "kill"
    if text.startswith("REDESIGN"):
        return "redesign"
    return "missing"


def selected_intrabar_row(pair_row: dict[str, Any], intrabar_by_performance_id: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    winner_side = pair_row.get("winner_side")
    if winner_side == "LONG":
        return intrabar_by_performance_id.get(normalized(pair_row.get("input_long_performance_row_id")))
    if winner_side == "SHORT":
        return intrabar_by_performance_id.get(normalized(pair_row.get("input_short_performance_row_id")))
    return None


def rejected_intrabar_row(pair_row: dict[str, Any], intrabar_by_performance_id: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    winner_side = pair_row.get("winner_side")
    if winner_side == "LONG":
        return intrabar_by_performance_id.get(normalized(pair_row.get("input_short_performance_row_id")))
    if winner_side == "SHORT":
        return intrabar_by_performance_id.get(normalized(pair_row.get("input_long_performance_row_id")))
    return None


def implementation_decision(
    side_pair_decision: str,
    temporal_decision: str,
    selected_intrabar_decision: str,
    rejected_intrabar_decision: str,
    selected_intrabar_r: float | None,
    temporal_recent_r: float | None,
    temporal_consistency: float | None,
) -> str:
    side_family = decision_family(side_pair_decision)
    temporal_family = decision_family(temporal_decision)
    selected_family = decision_family(selected_intrabar_decision)
    rejected_family = decision_family(rejected_intrabar_decision)
    if selected_family == "kill" or temporal_family == "kill":
        return "KILL_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"
    if side_family == "implement" and temporal_family == "implement" and selected_family == "implement":
        if rejected_family in {"avoid", "kill", "redesign"} and (temporal_consistency or 0.0) >= 0.67:
            return "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_SIDE_FILTER"
    if selected_family in {"avoid", "kill"} or rejected_family in {"implement"}:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"
    if selected_intrabar_r is not None and selected_intrabar_r < -0.05:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"
    if temporal_recent_r is not None and temporal_recent_r < -0.05:
        return "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_SELECTION_RECENT_DECAY"
    return "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"


def implementation_selection_rows(
    side_pair_rows: list[dict[str, Any]],
    temporal_by_pair_id: dict[str, dict[str, Any]],
    intrabar_by_performance_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for pair in side_pair_rows:
        pair_id = normalized(pair.get("side_pair_robustness_row_id"))
        temporal = temporal_by_pair_id.get(pair_id)
        selected_intrabar = selected_intrabar_row(pair, intrabar_by_performance_id)
        rejected_intrabar = rejected_intrabar_row(pair, intrabar_by_performance_id)
        if not temporal or not selected_intrabar or not rejected_intrabar:
            issues.append(
                boundary_row(
                    {
                        "implementation_selection_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-IMPLEMENTATION-SELECTION-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_side_pair_robustness_row_id": pair_id,
                        "input_long_performance_row_id": pair.get("input_long_performance_row_id"),
                        "input_short_performance_row_id": pair.get("input_short_performance_row_id"),
                        "missing_simulated_fields": [
                            field
                            for field, present in (
                                ("temporal_robustness_row", bool(temporal)),
                                ("selected_intrabar_geometry_row", bool(selected_intrabar)),
                                ("rejected_intrabar_geometry_row", bool(rejected_intrabar)),
                            )
                            if not present
                        ],
                        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_SELECTION_INPUT_JOIN",
                    }
                )
            )
            continue
        selected_r = as_float(selected_intrabar.get("cost_adjusted_simulated_r"))
        rejected_r = as_float(rejected_intrabar.get("cost_adjusted_simulated_r"))
        temporal_recent_r = as_float(temporal.get("recent_half_winner_cost_adjusted_simulated_r"))
        temporal_consistency = as_float(temporal.get("winner_consistency_share"))
        decision = implementation_decision(
            normalized(pair.get("keep_kill_redesign_implement_decision")),
            normalized(temporal.get("keep_kill_redesign_implement_decision")),
            normalized(selected_intrabar.get("keep_kill_redesign_implement_decision")),
            normalized(rejected_intrabar.get("keep_kill_redesign_implement_decision")),
            selected_r,
            temporal_recent_r,
            temporal_consistency,
        )
        output.append(
            boundary_row(
                {
                    "implementation_selection_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-IMPLEMENTATION-SELECTION-{len(output) + 1:07d}"
                    ),
                    "input_side_pair_robustness_row_id": pair_id,
                    "input_temporal_robustness_row_id": temporal.get("temporal_robustness_row_id"),
                    "input_selected_intrabar_geometry_row_id": selected_intrabar.get("intrabar_geometry_row_id"),
                    "input_rejected_intrabar_geometry_row_id": rejected_intrabar.get("intrabar_geometry_row_id"),
                    "input_long_performance_row_id": pair.get("input_long_performance_row_id"),
                    "input_short_performance_row_id": pair.get("input_short_performance_row_id"),
                    "symbol": pair.get("symbol"),
                    "source_symbol": pair.get("source_symbol"),
                    "market_timeframe": pair.get("market_timeframe"),
                    "route_session": pair.get("route_session"),
                    "horizon_id": pair.get("horizon_id"),
                    "source_component": pair.get("source_component"),
                    "source_path": pair.get("source_path"),
                    "source_file_sha256": pair.get("source_file_sha256"),
                    "selected_side": pair.get("winner_side"),
                    "rejected_side": pair.get("loser_side"),
                    "side_pair_decision": pair.get("keep_kill_redesign_implement_decision"),
                    "temporal_decision": temporal.get("keep_kill_redesign_implement_decision"),
                    "selected_intrabar_decision": selected_intrabar.get("keep_kill_redesign_implement_decision"),
                    "rejected_intrabar_decision": rejected_intrabar.get("keep_kill_redesign_implement_decision"),
                    "side_pair_spread_cost_adjusted_r": pair.get("side_edge_spread_cost_adjusted_r"),
                    "temporal_winner_consistency_share": temporal.get("winner_consistency_share"),
                    "temporal_positive_winner_fold_share": temporal.get("positive_winner_fold_share"),
                    "temporal_recent_half_winner_cost_adjusted_r": temporal.get("recent_half_winner_cost_adjusted_simulated_r"),
                    "temporal_recent_quarter_winner_cost_adjusted_r": temporal.get("recent_quarter_winner_cost_adjusted_simulated_r"),
                    "selected_intrabar_cost_adjusted_simulated_r": rounded(selected_r),
                    "rejected_intrabar_cost_adjusted_simulated_r": rounded(rejected_r),
                    "selected_minus_rejected_intrabar_cost_adjusted_r": rounded(
                        selected_r - rejected_r if selected_r is not None and rejected_r is not None else None
                    ),
                    "selected_intrabar_target_first_count": selected_intrabar.get("target_first_count"),
                    "selected_intrabar_stop_first_count": selected_intrabar.get("stop_first_count"),
                    "selected_intrabar_neither_count": selected_intrabar.get("neither_count"),
                    "selected_intrabar_ambiguous_count": selected_intrabar.get("ambiguous_count"),
                    "effective_n": min(
                        int(pair.get("effective_n") or 0),
                        int(temporal.get("min_test_effective_n") or 0),
                        int(selected_intrabar.get("effective_n") or 0),
                        int(rejected_intrabar.get("effective_n") or 0),
                    ),
                    "branch_local_candidate_family": "expanded_market_side_filter"
                    if decision.startswith("IMPLEMENT")
                    else "expanded_market_research_control",
                    "branch_local_candidate_expression": (
                        "match(symbol,timeframe,session,horizon,source_component) and follow selected_side"
                        if decision.startswith("IMPLEMENT")
                        else "retain row-level evidence for redesign, avoid-intelligence, or kill handling"
                    ),
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
        )
    return output, issues


def aggregate_implementation_selection_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("source_component")),
            normalized(row.get("selected_side")),
            normalized(row.get("follow_inverse_default_off_avoid_class")),
        )
        grouped[key].append(row)
    total_rows = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        decisions = Counter(normalized(row.get("keep_kill_redesign_implement_decision")) for row in members)
        selected_values = [as_float(row.get("selected_intrabar_cost_adjusted_simulated_r")) for row in members]
        selected_values = [value for value in selected_values if value is not None]
        spread_values = [as_float(row.get("selected_minus_rejected_intrabar_cost_adjusted_r")) for row in members]
        spread_values = [value for value in spread_values if value is not None]
        output.append(
            boundary_row(
                {
                    "implementation_selection_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-IMPLEMENTATION-SELECTION-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "selected_side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "effective_n": sum(int(row.get("effective_n") or 0) for row in members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(average(selected_values)),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": rounded(average(spread_values)),
                    "concentration_share_of_all_selection_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_implementation_selection_rows(
    selection_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    input_side_pair_rows: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "implementation_selection_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-IMPLEMENTATION-SELECTION-SYSTEM-0001"
                ),
                "input_side_pair_rows": input_side_pair_rows,
                "implementation_selection_rows": len(selection_rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "source_path_count": len({row.get("source_path") for row in selection_rows}),
                "symbol_count": len({row.get("symbol") for row in selection_rows}),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in selection_rows).items())
                ),
            }
        )
    ]
