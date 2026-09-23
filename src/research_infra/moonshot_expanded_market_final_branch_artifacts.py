"""Final branch-local artifact execution for expanded-market implementation candidates."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_FINAL_BRANCH_ARTIFACTS_SURFACE = (
    "src/research_infra/moonshot_expanded_market_final_branch_artifacts.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
BASE_SCOPE_KEYS = ("horizon_id", "market_timeframe", "route_session", "selected_side", "source_component", "source_symbol", "symbol")


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
    output["expanded_market_final_branch_artifacts_surface"] = EXPANDED_MARKET_FINAL_BRANCH_ARTIFACTS_SURFACE
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


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def matches_artifact_scope(artifact: dict[str, Any], row: dict[str, Any]) -> bool:
    scope = artifact.get("artifact_scope_definition") or {}
    for key in BASE_SCOPE_KEYS:
        if normalized(row.get(key)) != normalized(scope.get(key)):
            return False
    if normalized(scope.get("source_path")) and normalized(row.get("source_path")) != normalized(scope.get("source_path")):
        return False
    if normalized(scope.get("source_file_sha256")) and normalized(row.get("source_file_sha256")) != normalized(scope.get("source_file_sha256")):
        return False
    for field, threshold in (scope.get("numeric_thresholds") or {}).items():
        value = as_float(row.get(field))
        if value is None or value + 1e-12 < float(threshold):
            return False
    return True


def final_artifact_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        ready = candidate.get("implementation_candidate_status") == "IMPLEMENTATION_CANDIDATE_READY"
        decision = (
            "IMPLEMENT_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_ARTIFACT"
            if ready
            else "REDESIGN_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_ARTIFACT"
        )
        output.append(
            boundary_row(
                {
                    "final_branch_artifact_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-FINAL-BRANCH-ARTIFACT-{len(output) + 1:07d}"
                    ),
                    "input_implementation_candidate_row_id": candidate.get("implementation_candidate_row_id"),
                    "input_reduced_surface_execution_row_id": candidate.get("input_reduced_surface_execution_row_id"),
                    "input_reduced_surface_row_id": candidate.get("input_reduced_surface_row_id"),
                    "input_leakage_reduction_row_id": candidate.get("input_leakage_reduction_row_id"),
                    "artifact_family": "expanded_market_reduced_side_filter",
                    "artifact_module_path": "src/research_infra/moonshot_expanded_market_final_branch_artifacts.py",
                    "artifact_function_name": f"final_{candidate.get('surface_function_name')}",
                    "artifact_action": candidate.get("implementation_candidate_action"),
                    "symbol": candidate.get("symbol"),
                    "source_symbol": candidate.get("source_symbol"),
                    "market_timeframe": candidate.get("market_timeframe"),
                    "route_session": candidate.get("route_session"),
                    "horizon_id": candidate.get("horizon_id"),
                    "source_component": candidate.get("source_component"),
                    "source_path": candidate.get("source_path"),
                    "source_file_sha256": candidate.get("source_file_sha256"),
                    "selected_side": candidate.get("selected_side"),
                    "artifact_scope_definition": candidate.get("candidate_scope"),
                    "artifact_scope_sha256": candidate.get("candidate_scope_sha256"),
                    "branch_local_code_expression": candidate.get("branch_local_code_expression"),
                    "matched_selection_rows": candidate.get("matched_selection_rows"),
                    "matched_implement_rows": candidate.get("matched_implement_rows"),
                    "selection_precision": candidate.get("selection_precision"),
                    "average_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": candidate.get(
                        "average_selected_minus_rejected_intrabar_cost_adjusted_r"
                    ),
                    "minimum_temporal_winner_consistency_share": candidate.get(
                        "minimum_temporal_winner_consistency_share"
                    ),
                    "minimum_temporal_positive_winner_fold_share": candidate.get(
                        "minimum_temporal_positive_winner_fold_share"
                    ),
                    "matched_effective_n_sum": candidate.get("matched_effective_n_sum"),
                    "matched_effective_n_min": candidate.get("matched_effective_n_min"),
                    "matched_effective_n_max": candidate.get("matched_effective_n_max"),
                    "selected_intrabar_target_first_count_total": candidate.get(
                        "selected_intrabar_target_first_count_total"
                    ),
                    "selected_intrabar_stop_first_count_total": candidate.get(
                        "selected_intrabar_stop_first_count_total"
                    ),
                    "selected_intrabar_neither_count_total": candidate.get("selected_intrabar_neither_count_total"),
                    "selected_intrabar_ambiguous_count_total": candidate.get("selected_intrabar_ambiguous_count_total"),
                    "selected_intrabar_path_count_total": candidate.get("selected_intrabar_path_count_total"),
                    "target_first_share": candidate.get("target_first_share"),
                    "stop_first_share": candidate.get("stop_first_share"),
                    "target_first_minus_stop_first_share": candidate.get("target_first_minus_stop_first_share"),
                    "artifact_status": "FINAL_BRANCH_LOCAL_ARTIFACT_READY"
                    if ready
                    else "FINAL_BRANCH_LOCAL_ARTIFACT_REDESIGN",
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
        )
    return output


def artifact_evidence_execution_rows(
    artifacts: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    artifact_by_candidate = {
        normalized(row.get("input_implementation_candidate_row_id")): row for row in artifacts
    }
    execution_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    first_evidence_by_candidate: dict[str, dict[str, Any]] = {}
    for evidence in evidence_rows:
        candidate_id = normalized(evidence.get("input_implementation_candidate_row_id"))
        artifact = artifact_by_candidate.get(candidate_id, {})
        matched = bool(artifact) and matches_artifact_scope(artifact, evidence)
        decision = (
            "IMPLEMENT_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_ARTIFACT_EVIDENCE_EXECUTION"
            if matched
            else "REDESIGN_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_ARTIFACT_EVIDENCE_EXECUTION"
        )
        first_evidence_by_candidate.setdefault(candidate_id, evidence)
        execution_rows.append(
            boundary_row(
                {
                    "final_branch_artifact_evidence_execution_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-FINAL-BRANCH-ARTIFACT-EVIDENCE-{len(execution_rows) + 1:08d}"
                    ),
                    "input_final_branch_artifact_row_id": artifact.get("final_branch_artifact_row_id"),
                    "input_implementation_candidate_row_id": evidence.get("input_implementation_candidate_row_id"),
                    "input_implementation_candidate_evidence_row_id": evidence.get(
                        "implementation_candidate_evidence_row_id"
                    ),
                    "input_matched_implementation_selection_row_id": evidence.get(
                        "input_matched_implementation_selection_row_id"
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
                    "artifact_match": matched,
                    "selected_intrabar_cost_adjusted_simulated_r": evidence.get(
                        "selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "selected_minus_rejected_intrabar_cost_adjusted_r": evidence.get(
                        "selected_minus_rejected_intrabar_cost_adjusted_r"
                    ),
                    "temporal_winner_consistency_share": evidence.get("temporal_winner_consistency_share"),
                    "temporal_positive_winner_fold_share": evidence.get("temporal_positive_winner_fold_share"),
                    "effective_n": evidence.get("effective_n"),
                    "selected_intrabar_target_first_count": evidence.get("selected_intrabar_target_first_count"),
                    "selected_intrabar_stop_first_count": evidence.get("selected_intrabar_stop_first_count"),
                    "selected_intrabar_neither_count": evidence.get("selected_intrabar_neither_count"),
                    "selected_intrabar_ambiguous_count": evidence.get("selected_intrabar_ambiguous_count"),
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
        )
    for artifact in artifacts:
        evidence = dict(first_evidence_by_candidate.get(normalized(artifact.get("input_implementation_candidate_row_id")), {}))
        evidence["selected_side"] = f"{normalized(evidence.get('selected_side'))}__mismatch"
        rejected = not matches_artifact_scope(artifact, evidence)
        control_rows.append(
            boundary_row(
                {
                    "final_branch_artifact_control_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-FINAL-BRANCH-ARTIFACT-CONTROL-{len(control_rows) + 1:07d}"
                    ),
                    "input_final_branch_artifact_row_id": artifact.get("final_branch_artifact_row_id"),
                    "input_implementation_candidate_row_id": artifact.get("input_implementation_candidate_row_id"),
                    "control_type": "SELECTED_SIDE_MISMATCH",
                    "control_rejected": rejected,
                    "symbol": artifact.get("symbol"),
                    "source_symbol": artifact.get("source_symbol"),
                    "market_timeframe": artifact.get("market_timeframe"),
                    "route_session": artifact.get("route_session"),
                    "horizon_id": artifact.get("horizon_id"),
                    "source_component": artifact.get("source_component"),
                    "source_path": artifact.get("source_path"),
                    "source_file_sha256": artifact.get("source_file_sha256"),
                    "selected_side": artifact.get("selected_side"),
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_ARTIFACT_CONTROL"
                    if rejected
                    else "REDESIGN_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_ARTIFACT_CONTROL",
                }
            )
        )
    return execution_rows, control_rows


def aggregate_artifact_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                    "final_branch_artifact_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-FINAL-BRANCH-ARTIFACT-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "selected_side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "matched_selection_rows": sum(as_int(row.get("matched_selection_rows")) for row in members),
                    "matched_implement_rows": sum(as_int(row.get("matched_implement_rows")) for row in members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(average(selected_values)),
                    "average_selected_minus_rejected_intrabar_cost_adjusted_r": rounded(average(spread_values)),
                    "concentration_share_of_all_artifact_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_artifact_rows(
    artifacts: list[dict[str, Any]],
    evidence_executions: list[dict[str, Any]],
    controls: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    input_candidate_rows: int,
    input_evidence_rows: int,
) -> list[dict[str, Any]]:
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in artifacts)
    return [
        boundary_row(
            {
                "final_branch_artifact_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-FINAL-BRANCH-ARTIFACT-SYSTEM-0001"
                ),
                "input_candidate_rows": input_candidate_rows,
                "input_evidence_rows": input_evidence_rows,
                "final_branch_artifact_rows": len(artifacts),
                "artifact_evidence_execution_rows": len(evidence_executions),
                "artifact_control_rows": len(controls),
                "aggregate_rows": len(aggregates),
                "ready_artifact_rows": sum(
                    1 for row in artifacts if row.get("artifact_status") == "FINAL_BRANCH_LOCAL_ARTIFACT_READY"
                ),
                "evidence_execution_pass_rows": sum(
                    1 for row in evidence_executions if row.get("artifact_match") is True
                ),
                "control_rejected_rows": sum(1 for row in controls if row.get("control_rejected") is True),
                "decision_counts": dict(sorted(decisions.items())),
            }
        )
    ]
