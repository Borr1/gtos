"""Capacity execution for expanded-market portfolio concentration guards."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_DECONCENTRATION_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_deconcentration_execution.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
CONCENTRATION_LIMITS = {
    "symbol": 0.45,
    "source_component": 0.45,
    "source_path": 0.35,
    "portfolio_profile": 0.05,
}


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
    output["expanded_market_deconcentration_execution_surface"] = (
        EXPANDED_MARKET_DECONCENTRATION_EXECUTION_SURFACE
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


def profile_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("selected_side")),
    )


def concentration_value(row: dict[str, Any], dimension: str) -> str | tuple[str, ...]:
    if dimension == "portfolio_profile":
        return profile_key(row)
    return normalized(row.get(dimension))


def capacity(total_rows: int, dimension: str) -> int:
    return max(1, math.floor(CONCENTRATION_LIMITS[dimension] * total_rows))


def deconcentration_score(row: dict[str, Any]) -> float:
    selected = as_float(row.get("average_selected_intrabar_cost_adjusted_simulated_r")) or 0.0
    spread = as_float(row.get("average_selected_minus_rejected_intrabar_cost_adjusted_r")) or 0.0
    path_edge = as_float(row.get("target_first_minus_stop_first_share")) or 0.0
    precision = as_float(row.get("selection_precision")) or 0.0
    return selected + (0.5 * spread) + path_edge + (0.05 * precision)


def selection_sort_key(row: dict[str, Any]) -> tuple[float, str]:
    return (-deconcentration_score(row), normalized(row.get("portfolio_artifact_selection_row_id")))


def row_decision(base_selected: bool, blockers: list[str]) -> str:
    if base_selected:
        return "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATION_BASE_SELECTED"
    if not blockers:
        return "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATION_CAPACITY_SELECTED"
    return "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_CAPACITY_BLOCKED"


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def deconcentration_rows(
    selection_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    evidence_by_selection: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence_rows:
        evidence_by_selection[normalized(row.get("input_portfolio_artifact_selection_row_id"))].append(row)

    total = len(selection_rows)
    capacities = {dimension: capacity(total, dimension) for dimension in CONCENTRATION_LIMITS}
    selected_counts: dict[str, Counter[Any]] = {dimension: Counter() for dimension in CONCENTRATION_LIMITS}
    output_rows: list[dict[str, Any]] = []
    output_evidence_rows: list[dict[str, Any]] = []
    rows_by_id: dict[str, dict[str, Any]] = {}

    base_selected = [
        row for row in selection_rows if row.get("portfolio_selection_status") == "PORTFOLIO_ARTIFACT_SELECTED"
    ]
    guarded = [
        row
        for row in selection_rows
        if row.get("portfolio_selection_status") == "PORTFOLIO_ARTIFACT_PRESERVED_FOR_REDESIGN_OR_KILL"
    ]

    def emit(row: dict[str, Any], base: bool, blockers: list[str]) -> None:
        decision = row_decision(base, blockers)
        selected = decision.startswith("IMPLEMENT")
        for dimension in CONCENTRATION_LIMITS:
            if selected:
                selected_counts[dimension][concentration_value(row, dimension)] += 1
        output_id = f"OHLC-GTOS-EXPANDED-MARKET-DECONCENTRATION-{len(output_rows) + 1:07d}"
        evidence_members = evidence_by_selection.get(normalized(row.get("portfolio_artifact_selection_row_id")), [])
        output_rows.append(
            boundary_row(
                {
                    "deconcentration_row_id": output_id,
                    "input_portfolio_artifact_selection_row_id": row.get("portfolio_artifact_selection_row_id"),
                    "input_final_branch_artifact_row_id": row.get("input_final_branch_artifact_row_id"),
                    "input_implementation_candidate_row_id": row.get("input_implementation_candidate_row_id"),
                    "symbol": row.get("symbol"),
                    "source_symbol": row.get("source_symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "selected_side": row.get("selected_side"),
                    "artifact_family": row.get("artifact_family"),
                    "artifact_function_name": row.get("artifact_function_name"),
                    "branch_local_code_expression": row.get("branch_local_code_expression"),
                    "artifact_scope_sha256": row.get("artifact_scope_sha256"),
                    "deconcentration_score": rounded(deconcentration_score(row)),
                    "capacity_blocking_dimensions": blockers,
                    "capacity_selected": selected,
                    "base_selected_input": base,
                    "symbol_capacity": capacities["symbol"],
                    "source_component_capacity": capacities["source_component"],
                    "source_path_capacity": capacities["source_path"],
                    "portfolio_profile_capacity": capacities["portfolio_profile"],
                    "selected_symbol_count_after": selected_counts["symbol"][concentration_value(row, "symbol")],
                    "selected_source_component_count_after": selected_counts["source_component"][
                        concentration_value(row, "source_component")
                    ],
                    "selected_source_path_count_after": selected_counts["source_path"][
                        concentration_value(row, "source_path")
                    ],
                    "selected_portfolio_profile_count_after": selected_counts["portfolio_profile"][
                        concentration_value(row, "portfolio_profile")
                    ],
                    "matched_selection_rows": row.get("matched_selection_rows"),
                    "matched_implement_rows": row.get("matched_implement_rows"),
                    "evidence_execution_rows": len(evidence_members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": row.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": row.get(
                        "average_selected_minus_rejected_intrabar_cost_adjusted_r"
                    ),
                    "target_first_share": row.get("target_first_share"),
                    "stop_first_share": row.get("stop_first_share"),
                    "target_first_minus_stop_first_share": row.get("target_first_minus_stop_first_share"),
                    "matched_effective_n_sum": row.get("matched_effective_n_sum"),
                    "keep_kill_redesign_implement_decision": decision,
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                }
            )
        )
        rows_by_id[normalized(row.get("portfolio_artifact_selection_row_id"))] = output_rows[-1]
        for evidence in evidence_members:
            output_evidence_rows.append(
                boundary_row(
                    {
                        "deconcentration_evidence_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-DECONCENTRATION-EVIDENCE-{len(output_evidence_rows) + 1:08d}"
                        ),
                        "input_deconcentration_row_id": output_id,
                        "input_portfolio_artifact_selection_row_id": row.get("portfolio_artifact_selection_row_id"),
                        "input_portfolio_artifact_selection_evidence_row_id": evidence.get(
                            "portfolio_artifact_selection_evidence_row_id"
                        ),
                        "input_final_branch_artifact_row_id": evidence.get("input_final_branch_artifact_row_id"),
                        "input_final_branch_artifact_evidence_execution_row_id": evidence.get(
                            "input_final_branch_artifact_evidence_execution_row_id"
                        ),
                        "symbol": evidence.get("symbol"),
                        "source_symbol": evidence.get("source_symbol"),
                        "market_timeframe": evidence.get("market_timeframe"),
                        "route_session": evidence.get("route_session"),
                        "horizon_id": evidence.get("horizon_id"),
                        "source_component": evidence.get("source_component"),
                        "source_path": evidence.get("source_path"),
                        "source_file_sha256": evidence.get("source_file_sha256"),
                        "selected_side": evidence.get("selected_side"),
                        "artifact_match": evidence.get("artifact_match"),
                        "selected_intrabar_cost_adjusted_simulated_r": evidence.get(
                            "selected_intrabar_cost_adjusted_simulated_r"
                        ),
                        "selected_minus_rejected_intrabar_cost_adjusted_r": evidence.get(
                            "selected_minus_rejected_intrabar_cost_adjusted_r"
                        ),
                        "effective_n": evidence.get("effective_n"),
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATION_EVIDENCE"
                        if selected
                        else "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_EVIDENCE_PRESERVED",
                    }
                )
            )

    for row in sorted(base_selected, key=lambda item: normalized(item.get("portfolio_artifact_selection_row_id"))):
        emit(row, True, [])

    for row in sorted(guarded, key=selection_sort_key):
        blockers = [
            dimension
            for dimension in CONCENTRATION_LIMITS
            if selected_counts[dimension][concentration_value(row, dimension)] + 1 > capacities[dimension]
        ]
        emit(row, False, blockers)

    capacity_rows = capacity_ledger_rows(selection_rows, output_rows, capacities)
    return output_rows, output_evidence_rows, capacity_rows


def capacity_ledger_rows(
    input_rows: list[dict[str, Any]],
    output_rows: list[dict[str, Any]],
    capacities: dict[str, int],
) -> list[dict[str, Any]]:
    input_counts: dict[str, Counter[Any]] = {dimension: Counter() for dimension in CONCENTRATION_LIMITS}
    selected_counts: dict[str, Counter[Any]] = {dimension: Counter() for dimension in CONCENTRATION_LIMITS}
    for row in input_rows:
        for dimension in CONCENTRATION_LIMITS:
            input_counts[dimension][concentration_value(row, dimension)] += 1
    for row in output_rows:
        if row.get("capacity_selected") is True:
            for dimension in CONCENTRATION_LIMITS:
                selected_counts[dimension][concentration_value(row, dimension)] += 1
    rows: list[dict[str, Any]] = []
    for dimension in CONCENTRATION_LIMITS:
        for value, count in sorted(input_counts[dimension].items(), key=lambda item: str(item[0])):
            selected_count = selected_counts[dimension][value]
            cap = capacities[dimension]
            rows.append(
                boundary_row(
                    {
                        "deconcentration_capacity_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-DECONCENTRATION-CAPACITY-{len(rows) + 1:06d}"
                        ),
                        "capacity_dimension": dimension,
                        "capacity_value": list(value) if isinstance(value, tuple) else value,
                        "input_artifact_rows": count,
                        "selected_artifact_rows": selected_count,
                        "redesign_preserved_rows": count - selected_count,
                        "capacity_limit_rows": cap,
                        "capacity_limit_share": CONCENTRATION_LIMITS[dimension],
                        "selected_share_of_input_universe": rounded(selected_count / len(input_rows) if input_rows else None),
                        "capacity_status": "CAPACITY_FILLED_OR_EXCEEDED_INPUT"
                        if selected_count >= cap
                        else "CAPACITY_REMAINING",
                        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_CAPACITY_FILLED"
                        if selected_count >= cap and count > cap
                        else "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATION_CAPACITY",
                    }
                )
            )
    return rows


def aggregate_deconcentration_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        output.append(
            boundary_row(
                {
                    "deconcentration_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-DECONCENTRATION-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "selected_side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "capacity_selected_rows": sum(1 for row in members if row.get("capacity_selected") is True),
                    "redesign_preserved_rows": sum(1 for row in members if row.get("capacity_selected") is not True),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(average(selected_values)),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": rounded(average(spread_values)),
                    "concentration_share_of_all_deconcentration_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_deconcentration_rows(
    rows: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    capacity_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_selection_rows: int,
    input_evidence_rows: int,
) -> list[dict[str, Any]]:
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in rows)
    return [
        boundary_row(
            {
                "deconcentration_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-DECONCENTRATION-SYSTEM-0001",
                "input_portfolio_artifact_selection_rows": input_selection_rows,
                "input_portfolio_artifact_selection_evidence_rows": input_evidence_rows,
                "deconcentration_rows": len(rows),
                "deconcentration_evidence_rows": len(evidence),
                "deconcentration_capacity_rows": len(capacity_rows),
                "aggregate_rows": len(aggregate_rows),
                "capacity_selected_rows": sum(1 for row in rows if row.get("capacity_selected") is True),
                "base_selected_rows": sum(1 for row in rows if row.get("base_selected_input") is True),
                "capacity_added_rows": sum(
                    1
                    for row in rows
                    if row.get("capacity_selected") is True and row.get("base_selected_input") is not True
                ),
                "redesign_preserved_rows": sum(1 for row in rows if row.get("capacity_selected") is not True),
                "capacity_filled_rows": sum(
                    1 for row in capacity_rows if row.get("capacity_status") == "CAPACITY_FILLED_OR_EXCEEDED_INPUT"
                ),
                "decision_counts": dict(sorted(decisions.items())),
            }
        )
    ]
