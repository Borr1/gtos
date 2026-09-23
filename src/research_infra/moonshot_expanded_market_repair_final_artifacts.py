"""Final branch-local repair artifacts from expanded-market repair executions."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_impl_candidates import research_boundary
from src.research_infra.moonshot_expanded_market_impl_candidate_execution import normalized
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_REPAIR_FINAL_ARTIFACTS = (
    "src/research_infra/moonshot_expanded_market_repair_final_artifacts.py"
)


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_repair_final_artifacts_surface"] = (
        EXPANDED_MARKET_REPAIR_FINAL_ARTIFACTS
    )
    output["research_boundary"] = research_boundary()
    return output


def digest(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def same_float(left: Any, right: Any, tolerance: float = 1e-9) -> bool:
    left_value = as_float(left)
    right_value = as_float(right)
    if left_value is None and right_value is None:
        return True
    if left_value is None or right_value is None:
        return False
    return abs(left_value - right_value) <= tolerance


def artifact_scope(execution: dict[str, Any]) -> dict[str, Any]:
    exact_fields = (
        "input_repair_application_row_id",
        "input_impl_candidate_execution_row_id",
        "input_implementation_priority_row_id",
        "repair_application_scope_sha256",
        "symbol_family",
        "symbol",
        "source_symbol",
        "market_timeframe",
        "route_session",
        "horizon_id",
        "side",
        "repair_application_source_path",
        "repair_application_source_file_sha256",
        "repair_application_entry_reference",
        "repair_application_entry_reference_time",
        "repair_application_path_order_result",
        "repair_application_fill_status",
    )
    numeric_fields = (
        "repair_application_proxy_entry_price",
        "repair_application_proxy_denominator_price",
        "repair_application_proxy_target_price",
        "repair_application_proxy_stop_price",
        "repair_application_cost_adjusted_simulated_r",
        "repair_application_stress_simulated_r",
    )
    return {
        "scope_type": "expanded_market_positive_alternate_source_repair_final_artifact",
        "exact": {field: execution.get(field) for field in exact_fields},
        "numeric_exact": {field: execution.get(field) for field in numeric_fields},
    }


def artifact_matches_execution(artifact: dict[str, Any], execution: dict[str, Any]) -> bool:
    scope = artifact.get("final_repair_artifact_scope") or {}
    for field, expected in (scope.get("exact") or {}).items():
        if normalized(execution.get(field)) != normalized(expected):
            return False
    for field, expected in (scope.get("numeric_exact") or {}).items():
        if not same_float(execution.get(field), expected):
            return False
    return True


def final_artifact_row(execution: dict[str, Any], sequence: int) -> dict[str, Any]:
    ready = execution.get("repair_application_execution_status") == "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_PASS"
    scope = artifact_scope(execution)
    scope_sha = digest(scope)
    payload = dict(execution)
    payload.update(
        {
            "expanded_market_repair_final_artifact_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-{sequence:07d}"
            ),
            "input_repair_application_execution_row_id": execution.get(
                "expanded_market_repair_application_execution_row_id"
            ),
            "final_repair_artifact_family": "positive_alternate_source_repair",
            "final_repair_artifact_module_path": EXPANDED_MARKET_REPAIR_FINAL_ARTIFACTS,
            "final_repair_artifact_function_name": f"apply_expanded_market_repair_{scope_sha[:16]}",
            "final_repair_artifact_scope": scope,
            "final_repair_artifact_scope_sha256": scope_sha,
            "final_repair_artifact_expression": execution.get("repair_application_expression"),
            "final_repair_artifact_source_path": execution.get("repair_application_source_path"),
            "final_repair_artifact_source_file_sha256": execution.get(
                "repair_application_source_file_sha256"
            ),
            "final_repair_artifact_cost_adjusted_simulated_r": execution.get(
                "repair_application_cost_adjusted_simulated_r"
            ),
            "final_repair_artifact_stress_simulated_r": execution.get(
                "repair_application_stress_simulated_r"
            ),
            "final_repair_artifact_effective_n": execution.get("repair_application_effective_n"),
            "final_repair_artifact_status": "BRANCH_LOCAL_REPAIR_FINAL_ARTIFACT_READY"
            if ready
            else "BRANCH_LOCAL_REPAIR_FINAL_ARTIFACT_REDESIGN",
            "follow_inverse_default_off_avoid_class": "follow" if ready else "redesign",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT"
                if ready
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT"
            ),
        }
    )
    return boundary_row(payload)


def final_artifact_evidence_row(evidence: dict[str, Any], sequence: int) -> dict[str, Any]:
    payload = dict(evidence)
    payload.update(
        {
            "expanded_market_repair_final_artifact_evidence_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-EVIDENCE-{sequence:07d}"
            ),
            "input_repair_application_evidence_execution_row_id": evidence.get(
                "expanded_market_repair_application_evidence_execution_row_id"
            ),
            "final_repair_artifact_evidence_status": (
                "PRESERVED_NONCANDIDATE_REPAIR_FINAL_ARTIFACT_EVIDENCE"
            ),
        }
    )
    return boundary_row(payload)


def final_artifact_control_row(
    artifact: dict[str, Any],
    execution: dict[str, Any],
    execution_control: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    artifact_match = artifact_matches_execution(artifact, execution)
    pass_status = (
        artifact.get("final_repair_artifact_status") == "BRANCH_LOCAL_REPAIR_FINAL_ARTIFACT_READY"
        and artifact_match
        and (execution_control or {}).get("control_status")
        == "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_CONTROL_PASS"
        and (execution_control or {}).get("noncandidate_scope_leakage_count") == 0
    )
    return boundary_row(
        {
            "expanded_market_repair_final_artifact_control_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-CONTROL-{sequence:07d}"
            ),
            "input_repair_final_artifact_row_id": artifact.get(
                "expanded_market_repair_final_artifact_row_id"
            ),
            "input_repair_application_execution_row_id": execution.get(
                "expanded_market_repair_application_execution_row_id"
            ),
            "input_repair_application_execution_control_row_id": (execution_control or {}).get(
                "expanded_market_repair_application_execution_control_row_id"
            ),
            "input_implementation_priority_row_id": artifact.get("input_implementation_priority_row_id"),
            "final_repair_artifact_scope_sha256": artifact.get("final_repair_artifact_scope_sha256"),
            "artifact_scope_matches_execution": artifact_match,
            "execution_control_status": (execution_control or {}).get("control_status"),
            "noncandidate_scope_leakage_count": (execution_control or {}).get(
                "noncandidate_scope_leakage_count"
            ),
            "control_status": "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_CONTROL_PASS"
            if pass_status
            else "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_CONTROL_REDESIGN",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT_CONTROL"
                if pass_status
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT_CONTROL"
            ),
        }
    )


def issue_rows(artifacts: list[dict[str, Any]], controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in artifacts:
        if row.get("final_repair_artifact_status") != "BRANCH_LOCAL_REPAIR_FINAL_ARTIFACT_READY":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_final_artifact_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_final_artifact_row_id": row.get(
                            "expanded_market_repair_final_artifact_row_id"
                        ),
                        "issue_status": row.get("final_repair_artifact_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT"
                        ),
                    }
                )
            )
    for row in controls:
        if row.get("control_status") != "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_CONTROL_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_final_artifact_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_final_artifact_row_id": row.get("input_repair_final_artifact_row_id"),
                        "issue_status": row.get("control_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_FINAL_ARTIFACT_CONTROL"
                        ),
                    }
                )
            )
    return issues


def final_artifact_rows(
    executions: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    controls_by_execution = {
        normalized(row.get("input_repair_application_execution_row_id")): row for row in controls
    }
    artifacts: list[dict[str, Any]] = []
    artifact_controls: list[dict[str, Any]] = []
    for execution in executions:
        artifact = final_artifact_row(execution, len(artifacts) + 1)
        artifacts.append(artifact)
        artifact_controls.append(
            final_artifact_control_row(
                artifact,
                execution,
                controls_by_execution.get(
                    normalized(execution.get("expanded_market_repair_application_execution_row_id"))
                ),
                len(artifact_controls) + 1,
            )
        )
    evidence = [
        final_artifact_evidence_row(row, index) for index, row in enumerate(evidence_rows, 1)
    ]
    issues = issue_rows(artifacts, artifact_controls)
    return artifacts, evidence, artifact_controls, issues


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
        "ready_rows": 0,
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
    if row.get("final_repair_artifact_status") == "BRANCH_LOCAL_REPAIR_FINAL_ARTIFACT_READY":
        bucket["ready_rows"] += 1
    if row_kind == "evidence":
        bucket["evidence_rows"] += 1
    if row.get("control_status") == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_CONTROL_PASS":
        bucket["control_pass_rows"] += 1
    value = as_float(row.get("final_repair_artifact_cost_adjusted_simulated_r"))
    if value is not None:
        bucket["artifact_r_sum"] += value
        bucket["artifact_r_count"] += 1
    effective_n = as_float(row.get("final_repair_artifact_effective_n") or row.get("repair_application_effective_n"))
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
                    "expanded_market_repair_final_artifact_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-FINAL-ARTIFACT-AGG-{len(rows) + 1:07d}"
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
                    "ready_rows": bucket["ready_rows"],
                    "evidence_rows": bucket["evidence_rows"],
                    "control_pass_rows": bucket["control_pass_rows"],
                    "average_final_repair_artifact_cost_adjusted_simulated_r": rounded(
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


def aggregate_final_artifact_rows(
    artifacts: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    for row in artifacts:
        update_bucket(buckets[aggregate_key(row, "artifact")], row, "artifact")
    for row in evidence:
        update_bucket(buckets[aggregate_key(row, "evidence")], row, "evidence")
    for row in controls:
        update_bucket(buckets[aggregate_key(row, "control")], row, "control")
    return aggregate_rows_from_buckets(buckets)
