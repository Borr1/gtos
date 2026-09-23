"""Portfolio-level selection for expanded-market final branch artifacts."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_PORTFOLIO_ARTIFACT_SELECTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_portfolio_artifact_selection.py"
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
    output["expanded_market_portfolio_artifact_selection_surface"] = (
        EXPANDED_MARKET_PORTFOLIO_ARTIFACT_SELECTION_SURFACE
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


def concentration_counts(artifacts: list[dict[str, Any]]) -> dict[str, Counter[Any]]:
    return {
        "symbol": Counter(normalized(row.get("symbol")) for row in artifacts),
        "source_component": Counter(normalized(row.get("source_component")) for row in artifacts),
        "source_path": Counter(normalized(row.get("source_path")) for row in artifacts),
        "portfolio_profile": Counter(profile_key(row) for row in artifacts),
    }


def concentration_flags(row: dict[str, Any], counts: dict[str, Counter[Any]], total: int) -> dict[str, float]:
    if total <= 0:
        return {}
    values = {
        "symbol": counts["symbol"][normalized(row.get("symbol"))] / total,
        "source_component": counts["source_component"][normalized(row.get("source_component"))] / total,
        "source_path": counts["source_path"][normalized(row.get("source_path"))] / total,
        "portfolio_profile": counts["portfolio_profile"][profile_key(row)] / total,
    }
    return {
        key: rounded(value)
        for key, value in values.items()
        if value > CONCENTRATION_LIMITS[key] and not (key == "portfolio_profile" and total < 20)
    }


def selection_decision(row: dict[str, Any], flags: dict[str, float]) -> str:
    selected_r = as_float(row.get("average_selected_intrabar_cost_adjusted_simulated_r"))
    spread_r = as_float(row.get("average_selected_minus_rejected_intrabar_cost_adjusted_r"))
    path_edge = as_float(row.get("target_first_minus_stop_first_share"))
    if row.get("artifact_status") != "FINAL_BRANCH_LOCAL_ARTIFACT_READY":
        return "REDESIGN_EXPANDED_MARKET_PORTFOLIO_ARTIFACT_NOT_READY"
    if selected_r is None or spread_r is None or path_edge is None:
        return "REDESIGN_EXPANDED_MARKET_PORTFOLIO_ARTIFACT_MISSING_NUMERIC_FIELD"
    if selected_r <= 0 or spread_r <= 0 or path_edge <= 0:
        return "KILL_EXPANDED_MARKET_PORTFOLIO_ARTIFACT_NEGATIVE_REPLAY_EDGE"
    if flags:
        return "REDESIGN_EXPANDED_MARKET_PORTFOLIO_CONCENTRATION_GUARD_REQUIRED"
    return "IMPLEMENT_EXPANDED_MARKET_PORTFOLIO_ARTIFACT"


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def portfolio_selection_rows(
    artifacts: list[dict[str, Any]],
    evidence_executions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    counts = concentration_counts(artifacts)
    total = len(artifacts)
    evidence_by_artifact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence_executions:
        evidence_by_artifact[normalized(row.get("input_final_branch_artifact_row_id"))].append(row)

    selection_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        flags = concentration_flags(artifact, counts, total)
        decision = selection_decision(artifact, flags)
        selection_row_id = (
            f"OHLC-GTOS-EXPANDED-MARKET-PORTFOLIO-ARTIFACT-SELECTION-{len(selection_rows) + 1:07d}"
        )
        evidence_members = evidence_by_artifact.get(normalized(artifact.get("final_branch_artifact_row_id")), [])
        selection_rows.append(
            boundary_row(
                {
                    "portfolio_artifact_selection_row_id": selection_row_id,
                    "input_final_branch_artifact_row_id": artifact.get("final_branch_artifact_row_id"),
                    "input_implementation_candidate_row_id": artifact.get("input_implementation_candidate_row_id"),
                    "artifact_family": artifact.get("artifact_family"),
                    "artifact_module_path": artifact.get("artifact_module_path"),
                    "artifact_function_name": artifact.get("artifact_function_name"),
                    "symbol": artifact.get("symbol"),
                    "source_symbol": artifact.get("source_symbol"),
                    "market_timeframe": artifact.get("market_timeframe"),
                    "route_session": artifact.get("route_session"),
                    "horizon_id": artifact.get("horizon_id"),
                    "source_component": artifact.get("source_component"),
                    "source_path": artifact.get("source_path"),
                    "source_file_sha256": artifact.get("source_file_sha256"),
                    "selected_side": artifact.get("selected_side"),
                    "branch_local_code_expression": artifact.get("branch_local_code_expression"),
                    "artifact_scope_sha256": artifact.get("artifact_scope_sha256"),
                    "matched_selection_rows": artifact.get("matched_selection_rows"),
                    "matched_implement_rows": artifact.get("matched_implement_rows"),
                    "evidence_execution_rows": len(evidence_members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": artifact.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": artifact.get(
                        "average_selected_minus_rejected_intrabar_cost_adjusted_r"
                    ),
                    "target_first_share": artifact.get("target_first_share"),
                    "stop_first_share": artifact.get("stop_first_share"),
                    "target_first_minus_stop_first_share": artifact.get("target_first_minus_stop_first_share"),
                    "matched_effective_n_sum": artifact.get("matched_effective_n_sum"),
                    "matched_effective_n_min": artifact.get("matched_effective_n_min"),
                    "matched_effective_n_max": artifact.get("matched_effective_n_max"),
                    "selected_intrabar_target_first_count_total": artifact.get(
                        "selected_intrabar_target_first_count_total"
                    ),
                    "selected_intrabar_stop_first_count_total": artifact.get(
                        "selected_intrabar_stop_first_count_total"
                    ),
                    "selected_intrabar_neither_count_total": artifact.get("selected_intrabar_neither_count_total"),
                    "selected_intrabar_ambiguous_count_total": artifact.get(
                        "selected_intrabar_ambiguous_count_total"
                    ),
                    "concentration_flags": flags,
                    "symbol_concentration_share": rounded(counts["symbol"][normalized(artifact.get("symbol"))] / total),
                    "source_component_concentration_share": rounded(
                        counts["source_component"][normalized(artifact.get("source_component"))] / total
                    ),
                    "source_path_concentration_share": rounded(
                        counts["source_path"][normalized(artifact.get("source_path"))] / total
                    ),
                    "portfolio_profile_concentration_share": rounded(counts["portfolio_profile"][profile_key(artifact)] / total),
                    "portfolio_selection_status": "PORTFOLIO_ARTIFACT_SELECTED"
                    if decision.startswith("IMPLEMENT")
                    else "PORTFOLIO_ARTIFACT_PRESERVED_FOR_REDESIGN_OR_KILL",
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
        )
        for evidence in evidence_members:
            evidence_rows.append(
                boundary_row(
                    {
                        "portfolio_artifact_selection_evidence_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-PORTFOLIO-ARTIFACT-EVIDENCE-{len(evidence_rows) + 1:08d}"
                        ),
                        "input_portfolio_artifact_selection_row_id": selection_row_id,
                        "input_final_branch_artifact_row_id": artifact.get("final_branch_artifact_row_id"),
                        "input_final_branch_artifact_evidence_execution_row_id": evidence.get(
                            "final_branch_artifact_evidence_execution_row_id"
                        ),
                        "input_implementation_candidate_evidence_row_id": evidence.get(
                            "input_implementation_candidate_evidence_row_id"
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
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PORTFOLIO_ARTIFACT_EVIDENCE"
                        if decision.startswith("IMPLEMENT")
                        else "REDESIGN_EXPANDED_MARKET_PORTFOLIO_ARTIFACT_EVIDENCE_PRESERVED",
                    }
                )
            )
    concentration_rows = concentration_ledger_rows(counts, total)
    return selection_rows, evidence_rows, concentration_rows


def concentration_ledger_rows(counts: dict[str, Counter[Any]], total: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dimension in ["symbol", "source_component", "source_path", "portfolio_profile"]:
        for value, count in sorted(counts[dimension].items(), key=lambda item: (str(item[0]), item[1])):
            share = count / total if total else 0.0
            guard_required = share > CONCENTRATION_LIMITS[dimension] and not (dimension == "portfolio_profile" and total < 20)
            rows.append(
                boundary_row(
                    {
                        "portfolio_concentration_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-PORTFOLIO-CONCENTRATION-{len(rows) + 1:06d}"
                        ),
                        "concentration_dimension": dimension,
                        "concentration_value": list(value) if isinstance(value, tuple) else value,
                        "artifact_rows": count,
                        "artifact_share": rounded(share),
                        "concentration_limit": CONCENTRATION_LIMITS[dimension],
                        "concentration_status": "CONCENTRATION_GUARD_REQUIRED"
                        if guard_required
                        else "CONCENTRATION_WITHIN_LIMIT",
                        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_PORTFOLIO_CONCENTRATION"
                        if guard_required
                        else "IMPLEMENT_EXPANDED_MARKET_PORTFOLIO_CONCENTRATION",
                    }
                )
            )
    return rows


def aggregate_selection_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                    "portfolio_artifact_selection_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PORTFOLIO-ARTIFACT-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "selected_side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "selected_rows": sum(1 for row in members if row.get("portfolio_selection_status") == "PORTFOLIO_ARTIFACT_SELECTED"),
                    "preserved_rows": sum(
                        1
                        for row in members
                        if row.get("portfolio_selection_status") == "PORTFOLIO_ARTIFACT_PRESERVED_FOR_REDESIGN_OR_KILL"
                    ),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(average(selected_values)),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": rounded(average(spread_values)),
                    "concentration_share_of_all_selection_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_selection_rows(
    selections: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    concentration: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    input_artifact_rows: int,
    input_evidence_rows: int,
) -> list[dict[str, Any]]:
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in selections)
    return [
        boundary_row(
            {
                "portfolio_artifact_selection_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-PORTFOLIO-ARTIFACT-SYSTEM-0001"
                ),
                "input_artifact_rows": input_artifact_rows,
                "input_evidence_rows": input_evidence_rows,
                "portfolio_artifact_selection_rows": len(selections),
                "portfolio_artifact_selection_evidence_rows": len(evidence),
                "portfolio_concentration_rows": len(concentration),
                "aggregate_rows": len(aggregates),
                "selected_rows": sum(
                    1 for row in selections if row.get("portfolio_selection_status") == "PORTFOLIO_ARTIFACT_SELECTED"
                ),
                "preserved_redesign_or_kill_rows": sum(
                    1
                    for row in selections
                    if row.get("portfolio_selection_status") == "PORTFOLIO_ARTIFACT_PRESERVED_FOR_REDESIGN_OR_KILL"
                ),
                "concentration_guard_rows": sum(
                    1 for row in concentration if row.get("concentration_status") == "CONCENTRATION_GUARD_REQUIRED"
                ),
                "decision_counts": dict(sorted(decisions.items())),
            }
        )
    ]
