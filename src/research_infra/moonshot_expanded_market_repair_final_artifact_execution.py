"""Execute expanded-market final repair artifacts against held repair executions."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_impl_candidates import research_boundary
from src.research_infra.moonshot_expanded_market_impl_candidate_execution import normalized
from src.research_infra.moonshot_expanded_market_repair_final_artifacts import artifact_matches_execution
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_repair_final_artifact_execution.py"
)


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_repair_final_artifact_execution_surface"] = (
        EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def final_artifact_execution_row(
    artifact: dict[str, Any],
    held_execution: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    held = held_execution or {}
    matched = bool(held_execution) and artifact_matches_execution(artifact, held)
    payload = dict(artifact)
    payload.update(
        {
            "expanded_market_repair_final_artifact_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-EXECUTION-{sequence:07d}"
            ),
            "input_repair_final_artifact_row_id": artifact.get(
                "expanded_market_repair_final_artifact_row_id"
            ),
            "input_repair_application_execution_row_id": artifact.get(
                "input_repair_application_execution_row_id"
            ),
            "held_repair_application_execution_found": bool(held_execution),
            "final_artifact_execution_match": matched,
            "final_artifact_execution_status": "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS"
            if matched
            else "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_REDESIGN",
            "held_repair_application_execution_status": held.get("repair_application_execution_status"),
            "held_repair_application_cost_adjusted_simulated_r": held.get(
                "repair_application_cost_adjusted_simulated_r"
            ),
            "held_repair_application_stress_simulated_r": held.get(
                "repair_application_stress_simulated_r"
            ),
            "follow_inverse_default_off_avoid_class": "follow" if matched else "redesign",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT_EXECUTION"
                if matched
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT_EXECUTION"
            ),
        }
    )
    return boundary_row(payload)


def evidence_execution_row(evidence: dict[str, Any], sequence: int) -> dict[str, Any]:
    payload = dict(evidence)
    payload.update(
        {
            "expanded_market_repair_final_artifact_evidence_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-EVIDENCE-EXECUTION-{sequence:07d}"
            ),
            "input_repair_final_artifact_evidence_row_id": evidence.get(
                "expanded_market_repair_final_artifact_evidence_row_id"
            ),
            "final_artifact_execution_evidence_status": (
                "PRESERVED_NONCANDIDATE_REPAIR_FINAL_ARTIFACT_EXECUTION_EVIDENCE"
            ),
        }
    )
    return boundary_row(payload)


def control_execution_row(
    artifact_execution: dict[str, Any],
    artifact_control: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    pass_status = (
        artifact_execution.get("final_artifact_execution_status")
        == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS"
        and (artifact_control or {}).get("control_status")
        == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_CONTROL_PASS"
        and (artifact_control or {}).get("noncandidate_scope_leakage_count") == 0
    )
    return boundary_row(
        {
            "expanded_market_repair_final_artifact_execution_control_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-EXECUTION-CONTROL-{sequence:07d}"
            ),
            "input_repair_final_artifact_execution_row_id": artifact_execution.get(
                "expanded_market_repair_final_artifact_execution_row_id"
            ),
            "input_repair_final_artifact_row_id": artifact_execution.get(
                "input_repair_final_artifact_row_id"
            ),
            "input_repair_final_artifact_control_row_id": (artifact_control or {}).get(
                "expanded_market_repair_final_artifact_control_row_id"
            ),
            "input_implementation_priority_row_id": artifact_execution.get(
                "input_implementation_priority_row_id"
            ),
            "final_artifact_execution_match": artifact_execution.get("final_artifact_execution_match"),
            "held_repair_application_execution_found": artifact_execution.get(
                "held_repair_application_execution_found"
            ),
            "artifact_control_status": (artifact_control or {}).get("control_status"),
            "noncandidate_scope_leakage_count": (artifact_control or {}).get(
                "noncandidate_scope_leakage_count"
            ),
            "control_status": "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS"
            if pass_status
            else "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_REDESIGN",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL"
                if pass_status
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL"
            ),
        }
    )


def issue_rows(
    artifact_executions: list[dict[str, Any]],
    control_executions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in artifact_executions:
        if row.get("final_artifact_execution_status") != "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_final_artifact_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_final_artifact_row_id": row.get("input_repair_final_artifact_row_id"),
                        "issue_status": row.get("final_artifact_execution_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT_EXECUTION"
                        ),
                    }
                )
            )
    for row in control_executions:
        if row.get("control_status") != "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_final_artifact_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_final_artifact_row_id": row.get("input_repair_final_artifact_row_id"),
                        "issue_status": row.get("control_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL"
                        ),
                    }
                )
            )
    return issues


def execution_rows(
    artifacts: list[dict[str, Any]],
    held_repair_executions: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    held_by_id = {
        normalized(row.get("expanded_market_repair_application_execution_row_id")): row
        for row in held_repair_executions
    }
    controls_by_artifact = {
        normalized(row.get("input_repair_final_artifact_row_id")): row for row in controls
    }
    artifact_executions: list[dict[str, Any]] = []
    control_executions: list[dict[str, Any]] = []
    for artifact in artifacts:
        held = held_by_id.get(normalized(artifact.get("input_repair_application_execution_row_id")))
        execution = final_artifact_execution_row(artifact, held, len(artifact_executions) + 1)
        artifact_executions.append(execution)
        control_executions.append(
            control_execution_row(
                execution,
                controls_by_artifact.get(normalized(artifact.get("expanded_market_repair_final_artifact_row_id"))),
                len(control_executions) + 1,
            )
        )
    evidence_executions = [
        evidence_execution_row(row, index) for index, row in enumerate(evidence_rows, 1)
    ]
    issues = issue_rows(artifact_executions, control_executions)
    return artifact_executions, evidence_executions, control_executions, issues


def aggregate_key(row: dict[str, Any], row_kind: str) -> tuple[str, ...]:
    return (
        row_kind,
        normalized(row.get("implementation_priority_class") or row.get("evidence_preservation_class")),
        normalized(row.get("implementation_priority_tier")),
        normalized(row.get("symbol_family")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
    )


def empty_bucket() -> dict[str, Any]:
    return {
        "row_count": 0,
        "execution_pass_rows": 0,
        "evidence_rows": 0,
        "control_pass_rows": 0,
        "artifact_r_sum": 0.0,
        "artifact_r_count": 0,
        "effective_n_sum": 0.0,
        "source_paths": set(),
        "decisions": Counter(),
    }


def update_bucket(bucket: dict[str, Any], row: dict[str, Any], row_kind: str) -> None:
    bucket["row_count"] += 1
    if row.get("final_artifact_execution_status") == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS":
        bucket["execution_pass_rows"] += 1
    if row_kind == "evidence":
        bucket["evidence_rows"] += 1
    if row.get("control_status") == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS":
        bucket["control_pass_rows"] += 1
    value = as_float(row.get("final_repair_artifact_cost_adjusted_simulated_r"))
    if value is not None:
        bucket["artifact_r_sum"] += value
        bucket["artifact_r_count"] += 1
    effective_n = as_float(row.get("final_repair_artifact_effective_n"))
    if effective_n is not None:
        bucket["effective_n_sum"] += effective_n
    bucket["source_paths"].add(str(row.get("final_repair_artifact_source_path") or row.get("source_path") or ""))
    bucket["decisions"][row.get("keep_kill_redesign_implement_decision")] += 1


def aggregate_rows_from_buckets(buckets: dict[tuple[str, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        rows.append(
            boundary_row(
                {
                    "expanded_market_repair_final_artifact_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-EXEC-AGG-{len(rows) + 1:07d}"
                    ),
                    "row_kind": key[0],
                    "implementation_priority_class": key[1],
                    "implementation_priority_tier": key[2],
                    "symbol_family": key[3],
                    "market_timeframe": key[4],
                    "route_session": key[5],
                    "horizon_id": key[6],
                    "side": key[7],
                    "row_count": bucket["row_count"],
                    "execution_pass_rows": bucket["execution_pass_rows"],
                    "evidence_rows": bucket["evidence_rows"],
                    "control_pass_rows": bucket["control_pass_rows"],
                    "average_final_artifact_cost_adjusted_simulated_r": rounded(
                        bucket["artifact_r_sum"] / bucket["artifact_r_count"]
                        if bucket["artifact_r_count"]
                        else None
                    ),
                    "effective_n_sum": rounded(bucket["effective_n_sum"]),
                    "source_path_count": len(bucket["source_paths"]),
                    "decision_counts": dict(sorted(bucket["decisions"].items())),
                    "keep_kill_redesign_implement_decision": bucket["decisions"].most_common(1)[0][0],
                }
            )
        )
    return rows


def aggregate_execution_rows(
    artifact_executions: list[dict[str, Any]],
    evidence_executions: list[dict[str, Any]],
    control_executions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    for row in artifact_executions:
        update_bucket(buckets[aggregate_key(row, "artifact_execution")], row, "artifact_execution")
    for row in evidence_executions:
        update_bucket(buckets[aggregate_key(row, "evidence_execution")], row, "evidence")
    for row in control_executions:
        update_bucket(buckets[aggregate_key(row, "control_execution")], row, "control_execution")
    return aggregate_rows_from_buckets(buckets)
