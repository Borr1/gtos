"""Build implementation candidates from reduced expanded-market executions."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES_SURFACE = (
    "src/research_infra/moonshot_expanded_market_reduced_implementation_candidates.py"
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
    output["expanded_market_reduced_implementation_candidates_surface"] = (
        EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES_SURFACE
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


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values = [as_float(row.get(field)) for row in rows]
    return [value for value in values if value is not None]


def sum_int(rows: list[dict[str, Any]], field: str) -> int:
    return sum(as_int(row.get(field)) for row in rows)


def candidate_decision(execution: dict[str, Any], matches: list[dict[str, Any]]) -> str:
    nonimplement = int(execution.get("matched_nonimplement_rows") or 0)
    implement = int(execution.get("matched_implement_rows") or 0)
    if execution.get("execution_status") == "REDUCED_SURFACE_EXECUTION_PASS" and implement > 0 and nonimplement == 0:
        return "IMPLEMENT_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATE"
    if not matches:
        return "REDESIGN_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATE_NO_MATCH"
    return "REDESIGN_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATE"


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def implementation_candidate_rows(
    surfaces: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    matches: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    surface_by_id = {normalized(row.get("reduced_surface_row_id")): row for row in surfaces}
    matches_by_execution: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matches:
        matches_by_execution[normalized(row.get("input_reduced_surface_execution_row_id"))].append(row)

    candidate_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    for execution in executions:
        surface = surface_by_id.get(normalized(execution.get("input_reduced_surface_row_id")), {})
        matched_rows = matches_by_execution.get(normalized(execution.get("reduced_surface_execution_row_id")), [])
        decision = candidate_decision(execution, matched_rows)
        selected_values = numeric_values(matched_rows, "selected_intrabar_cost_adjusted_simulated_r")
        rejected_values = numeric_values(matched_rows, "rejected_intrabar_cost_adjusted_simulated_r")
        spread_values = numeric_values(matched_rows, "selected_minus_rejected_intrabar_cost_adjusted_r")
        temporal_consistency_values = numeric_values(matched_rows, "temporal_winner_consistency_share")
        temporal_positive_values = numeric_values(matched_rows, "temporal_positive_winner_fold_share")
        effective_values = numeric_values(matched_rows, "effective_n")
        target_first_total = sum_int(matched_rows, "selected_intrabar_target_first_count")
        stop_first_total = sum_int(matched_rows, "selected_intrabar_stop_first_count")
        neither_total = sum_int(matched_rows, "selected_intrabar_neither_count")
        ambiguous_total = sum_int(matched_rows, "selected_intrabar_ambiguous_count")
        path_total = target_first_total + stop_first_total + neither_total + ambiguous_total
        candidate_row_id = (
            f"OHLC-GTOS-EXPANDED-MARKET-REDUCED-IMPLEMENTATION-CANDIDATE-{len(candidate_rows) + 1:07d}"
        )
        candidate_rows.append(
            boundary_row(
                {
                    "implementation_candidate_row_id": candidate_row_id,
                    "input_reduced_surface_execution_row_id": execution.get("reduced_surface_execution_row_id"),
                    "input_reduced_surface_row_id": execution.get("input_reduced_surface_row_id"),
                    "input_leakage_reduction_row_id": execution.get("input_leakage_reduction_row_id"),
                    "input_code_candidate_execution_row_id": surface.get("input_code_candidate_execution_row_id"),
                    "input_code_candidate_row_id": surface.get("input_code_candidate_row_id"),
                    "input_implementation_selection_row_id": surface.get("input_implementation_selection_row_id"),
                    "candidate_function_name": surface.get("candidate_function_name"),
                    "surface_function_name": execution.get("surface_function_name"),
                    "symbol": execution.get("symbol"),
                    "source_symbol": execution.get("source_symbol"),
                    "market_timeframe": execution.get("market_timeframe"),
                    "route_session": execution.get("route_session"),
                    "horizon_id": execution.get("horizon_id"),
                    "source_component": execution.get("source_component"),
                    "source_path": execution.get("source_path"),
                    "source_file_sha256": execution.get("source_file_sha256"),
                    "selected_side": execution.get("selected_side"),
                    "implementation_candidate_family": "expanded_market_reduced_side_filter",
                    "implementation_candidate_action": "FOLLOW_SELECTED_SIDE_IN_BRANCH_LOCAL_REPLAY_ONLY",
                    "branch_local_code_expression": surface.get("branch_local_code_expression"),
                    "candidate_scope": surface.get("surface_scope"),
                    "candidate_scope_sha256": execution.get("surface_scope_sha256"),
                    "matched_selection_rows": execution.get("matched_selection_rows"),
                    "matched_implement_rows": execution.get("matched_implement_rows"),
                    "matched_nonimplement_rows": execution.get("matched_nonimplement_rows"),
                    "selection_precision": execution.get("selection_precision"),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(average(selected_values)),
                    "minimum_selected_intrabar_cost_adjusted_simulated_r": rounded(min(selected_values) if selected_values else None),
                    "maximum_selected_intrabar_cost_adjusted_simulated_r": rounded(max(selected_values) if selected_values else None),
                    "average_rejected_intrabar_cost_adjusted_simulated_r": rounded(average(rejected_values)),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": rounded(average(spread_values)),
                    "minimum_selected_minus_rejected_intrabar_cost_adjusted_r": rounded(
                        min(spread_values) if spread_values else None
                    ),
                    "minimum_temporal_winner_consistency_share": rounded(
                        min(temporal_consistency_values) if temporal_consistency_values else None
                    ),
                    "average_temporal_winner_consistency_share": rounded(average(temporal_consistency_values)),
                    "minimum_temporal_positive_winner_fold_share": rounded(
                        min(temporal_positive_values) if temporal_positive_values else None
                    ),
                    "average_temporal_positive_winner_fold_share": rounded(average(temporal_positive_values)),
                    "matched_effective_n_sum": rounded(sum(effective_values) if effective_values else None),
                    "matched_effective_n_min": rounded(min(effective_values) if effective_values else None),
                    "matched_effective_n_max": rounded(max(effective_values) if effective_values else None),
                    "selected_intrabar_target_first_count_total": target_first_total,
                    "selected_intrabar_stop_first_count_total": stop_first_total,
                    "selected_intrabar_neither_count_total": neither_total,
                    "selected_intrabar_ambiguous_count_total": ambiguous_total,
                    "selected_intrabar_path_count_total": path_total,
                    "target_first_share": rounded(target_first_total / path_total if path_total else None),
                    "stop_first_share": rounded(stop_first_total / path_total if path_total else None),
                    "neither_share": rounded(neither_total / path_total if path_total else None),
                    "ambiguous_share": rounded(ambiguous_total / path_total if path_total else None),
                    "target_first_minus_stop_first_share": rounded(
                        (target_first_total - stop_first_total) / path_total if path_total else None
                    ),
                    "target_selected_intrabar_cost_adjusted_simulated_r": surface.get(
                        "target_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "target_rejected_intrabar_cost_adjusted_simulated_r": surface.get(
                        "target_rejected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "target_selected_minus_rejected_intrabar_cost_adjusted_r": surface.get(
                        "target_selected_minus_rejected_intrabar_cost_adjusted_r"
                    ),
                    "target_temporal_winner_consistency_share": surface.get("target_temporal_winner_consistency_share"),
                    "target_temporal_positive_winner_fold_share": surface.get(
                        "target_temporal_positive_winner_fold_share"
                    ),
                    "target_effective_n": surface.get("target_effective_n"),
                    "target_selected_intrabar_target_first_count": surface.get(
                        "target_selected_intrabar_target_first_count"
                    ),
                    "target_selected_intrabar_stop_first_count": surface.get("target_selected_intrabar_stop_first_count"),
                    "target_selected_intrabar_neither_count": surface.get("target_selected_intrabar_neither_count"),
                    "target_selected_intrabar_ambiguous_count": surface.get("target_selected_intrabar_ambiguous_count"),
                    "implementation_candidate_status": "IMPLEMENTATION_CANDIDATE_READY"
                    if decision.startswith("IMPLEMENT")
                    else "IMPLEMENTATION_CANDIDATE_REDESIGN",
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
        )
        for match in matched_rows:
            evidence_rows.append(
                boundary_row(
                    {
                        "implementation_candidate_evidence_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REDUCED-IMPLEMENTATION-EVIDENCE-{len(evidence_rows) + 1:08d}"
                        ),
                        "input_implementation_candidate_row_id": candidate_row_id,
                        "input_reduced_surface_execution_row_id": execution.get("reduced_surface_execution_row_id"),
                        "input_reduced_surface_execution_match_row_id": match.get(
                            "reduced_surface_execution_match_row_id"
                        ),
                        "input_matched_implementation_selection_row_id": match.get(
                            "input_matched_implementation_selection_row_id"
                        ),
                        "symbol": match.get("symbol"),
                        "source_symbol": match.get("source_symbol"),
                        "market_timeframe": match.get("market_timeframe"),
                        "route_session": match.get("route_session"),
                        "horizon_id": match.get("horizon_id"),
                        "source_component": match.get("source_component"),
                        "source_path": match.get("source_path"),
                        "source_file_sha256": match.get("source_file_sha256"),
                        "selected_side": match.get("selected_side"),
                        "matched_selection_decision": match.get("matched_selection_decision"),
                        "matched_decision_family": match.get("matched_decision_family"),
                        "selected_intrabar_cost_adjusted_simulated_r": match.get(
                            "selected_intrabar_cost_adjusted_simulated_r"
                        ),
                        "rejected_intrabar_cost_adjusted_simulated_r": match.get(
                            "rejected_intrabar_cost_adjusted_simulated_r"
                        ),
                        "selected_minus_rejected_intrabar_cost_adjusted_r": match.get(
                            "selected_minus_rejected_intrabar_cost_adjusted_r"
                        ),
                        "temporal_winner_consistency_share": match.get("temporal_winner_consistency_share"),
                        "temporal_positive_winner_fold_share": match.get("temporal_positive_winner_fold_share"),
                        "effective_n": match.get("effective_n"),
                        "selected_intrabar_target_first_count": match.get("selected_intrabar_target_first_count"),
                        "selected_intrabar_stop_first_count": match.get("selected_intrabar_stop_first_count"),
                        "selected_intrabar_neither_count": match.get("selected_intrabar_neither_count"),
                        "selected_intrabar_ambiguous_count": match.get("selected_intrabar_ambiguous_count"),
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_EVIDENCE",
                    }
                )
            )
    return candidate_rows, evidence_rows


def aggregate_candidate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        selected_values = numeric_values(members, "average_selected_intrabar_cost_adjusted_simulated_r")
        spread_values = numeric_values(members, "average_selected_minus_rejected_intrabar_cost_adjusted_r")
        path_total = sum_int(members, "selected_intrabar_path_count_total")
        target_total = sum_int(members, "selected_intrabar_target_first_count_total")
        stop_total = sum_int(members, "selected_intrabar_stop_first_count_total")
        output.append(
            boundary_row(
                {
                    "implementation_candidate_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REDUCED-IMPLEMENTATION-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "selected_side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "matched_selection_rows": sum_int(members, "matched_selection_rows"),
                    "matched_implement_rows": sum_int(members, "matched_implement_rows"),
                    "matched_nonimplement_rows": sum_int(members, "matched_nonimplement_rows"),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(average(selected_values)),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": rounded(average(spread_values)),
                    "selected_intrabar_target_first_count_total": target_total,
                    "selected_intrabar_stop_first_count_total": stop_total,
                    "selected_intrabar_path_count_total": path_total,
                    "target_first_share": rounded(target_total / path_total if path_total else None),
                    "stop_first_share": rounded(stop_total / path_total if path_total else None),
                    "target_first_minus_stop_first_share": rounded(
                        (target_total - stop_total) / path_total if path_total else None
                    ),
                    "concentration_share_of_all_candidate_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_candidate_rows(
    candidates: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    input_execution_rows: int,
    input_match_rows: int,
) -> list[dict[str, Any]]:
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in candidates)
    return [
        boundary_row(
            {
                "implementation_candidate_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-REDUCED-IMPLEMENTATION-SYSTEM-0001"
                ),
                "input_execution_rows": input_execution_rows,
                "input_match_rows": input_match_rows,
                "implementation_candidate_rows": len(candidates),
                "implementation_candidate_evidence_rows": len(evidence),
                "aggregate_rows": len(aggregates),
                "ready_candidate_rows": sum(
                    1 for row in candidates if row.get("implementation_candidate_status") == "IMPLEMENTATION_CANDIDATE_READY"
                ),
                "redesign_candidate_rows": sum(
                    1
                    for row in candidates
                    if row.get("implementation_candidate_status") == "IMPLEMENTATION_CANDIDATE_REDESIGN"
                ),
                "decision_counts": dict(sorted(decisions.items())),
            }
        )
    ]
