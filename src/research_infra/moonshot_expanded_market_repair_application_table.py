"""Branch-local repair application table from expanded-market candidate executions."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_impl_candidates import research_boundary
from src.research_infra.moonshot_expanded_market_impl_candidate_execution import normalized
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_REPAIR_APPLICATION_TABLE = (
    "src/research_infra/moonshot_expanded_market_repair_application_table.py"
)


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_repair_application_table_surface"] = (
        EXPANDED_MARKET_REPAIR_APPLICATION_TABLE
    )
    output["research_boundary"] = research_boundary()
    return output


def application_ready(execution: dict[str, Any], control: dict[str, Any] | None) -> bool:
    return (
        execution.get("candidate_execution_status") == "EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION_PASS"
        and (control or {}).get("control_status") == "EXPANDED_MARKET_IMPL_CANDIDATE_CONTROL_PASS"
        and execution.get("candidate_scope_match") is True
    )


def repair_application_row(
    execution: dict[str, Any],
    control: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    ready = application_ready(execution, control)
    payload = dict(execution)
    payload.update(
        {
            "expanded_market_repair_application_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-{sequence:07d}"
            ),
            "input_impl_candidate_execution_row_id": execution.get(
                "expanded_market_impl_candidate_execution_row_id"
            ),
            "input_impl_candidate_control_row_id": (control or {}).get(
                "expanded_market_impl_candidate_control_row_id"
            ),
            "repair_application_family": "positive_alternate_source_repair",
            "repair_application_status": "BRANCH_LOCAL_REPAIR_APPLICATION_READY"
            if ready
            else "BRANCH_LOCAL_REPAIR_APPLICATION_REDESIGN",
            "repair_application_action": "FOLLOW_POSITIVE_ALTERNATE_SOURCE_REPAIR_TABLE_ROW"
            if ready
            else "REDESIGN_POSITIVE_ALTERNATE_SOURCE_REPAIR_TABLE_ROW",
            "repair_application_scope_sha256": execution.get("branch_local_candidate_scope_sha256"),
            "repair_application_expression": execution.get("branch_local_code_expression"),
            "repair_application_source_path": execution.get("source_path"),
            "repair_application_source_file_sha256": execution.get("source_file_sha256"),
            "repair_application_entry_reference": execution.get("entry_reference"),
            "repair_application_entry_reference_time": execution.get("entry_reference_time"),
            "repair_application_proxy_entry_price": execution.get("proxy_entry_price"),
            "repair_application_proxy_denominator_price": execution.get("proxy_denominator_price"),
            "repair_application_proxy_target_price": execution.get("proxy_target_price"),
            "repair_application_proxy_stop_price": execution.get("proxy_stop_price"),
            "repair_application_path_order_result": execution.get("path_order_result"),
            "repair_application_fill_status": execution.get("fill_status"),
            "repair_application_cost_adjusted_simulated_r": execution.get(
                "execution_cost_adjusted_simulated_r"
            ),
            "repair_application_stress_simulated_r": execution.get("execution_observed_stress_simulated_r"),
            "repair_application_effective_n": execution.get("candidate_effective_n"),
            "control_status": (control or {}).get("control_status"),
            "noncandidate_scope_leakage_count": (control or {}).get("noncandidate_scope_leakage_count"),
            "follow_inverse_default_off_avoid_class": "follow" if ready else "redesign",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION"
                if ready
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION"
            ),
        }
    )
    return boundary_row(payload)


def evidence_application_row(evidence: dict[str, Any], sequence: int) -> dict[str, Any]:
    payload = dict(evidence)
    payload.update(
        {
            "expanded_market_repair_application_evidence_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-EVIDENCE-{sequence:07d}"
            ),
            "input_impl_candidate_evidence_execution_row_id": evidence.get(
                "expanded_market_impl_candidate_evidence_execution_row_id"
            ),
            "repair_application_evidence_status": "PRESERVED_NONCANDIDATE_REPAIR_APPLICATION_EVIDENCE",
        }
    )
    return boundary_row(payload)


def repair_application_control_row(
    application: dict[str, Any],
    control: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    pass_status = (
        application.get("repair_application_status") == "BRANCH_LOCAL_REPAIR_APPLICATION_READY"
        and (control or {}).get("control_status") == "EXPANDED_MARKET_IMPL_CANDIDATE_CONTROL_PASS"
    )
    return boundary_row(
        {
            "expanded_market_repair_application_control_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-CONTROL-{sequence:07d}"
            ),
            "input_repair_application_row_id": application.get("expanded_market_repair_application_row_id"),
            "input_impl_candidate_control_row_id": (control or {}).get(
                "expanded_market_impl_candidate_control_row_id"
            ),
            "input_implementation_priority_row_id": application.get("input_implementation_priority_row_id"),
            "repair_application_scope_sha256": application.get("repair_application_scope_sha256"),
            "positive_execution_match": (control or {}).get("positive_execution_match"),
            "noncandidate_scope_leakage_count": (control or {}).get("noncandidate_scope_leakage_count"),
            "control_status": "EXPANDED_MARKET_REPAIR_APPLICATION_CONTROL_PASS"
            if pass_status
            else "EXPANDED_MARKET_REPAIR_APPLICATION_CONTROL_REDESIGN",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION_CONTROL"
                if pass_status
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION_CONTROL"
            ),
        }
    )


def issue_rows(applications: list[dict[str, Any]], controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in applications:
        if row.get("repair_application_status") != "BRANCH_LOCAL_REPAIR_APPLICATION_READY":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_application_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_application_row_id": row.get("expanded_market_repair_application_row_id"),
                        "issue_status": row.get("repair_application_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION"
                        ),
                    }
                )
            )
    for row in controls:
        if row.get("control_status") != "EXPANDED_MARKET_REPAIR_APPLICATION_CONTROL_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_application_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_application_row_id": row.get("input_repair_application_row_id"),
                        "issue_status": row.get("control_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION_CONTROL"
                        ),
                    }
                )
            )
    return issues


def application_rows(
    executions: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    controls_by_priority_id = {
        normalized(row.get("input_implementation_priority_row_id")): row for row in controls
    }
    applications: list[dict[str, Any]] = []
    application_controls: list[dict[str, Any]] = []
    for execution in executions:
        control = controls_by_priority_id.get(normalized(execution.get("input_implementation_priority_row_id")))
        application = repair_application_row(execution, control, len(applications) + 1)
        applications.append(application)
        application_controls.append(
            repair_application_control_row(application, control, len(application_controls) + 1)
        )
    evidence = [
        evidence_application_row(row, index) for index, row in enumerate(evidence_rows, 1)
    ]
    issues = issue_rows(applications, application_controls)
    return applications, evidence, application_controls, issues


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
        "application_r_sum": 0.0,
        "application_r_count": 0,
        "effective_n_sum": 0.0,
        "source_paths": set(),
        "decisions": Counter(),
    }


def update_bucket(bucket: dict[str, Any], row: dict[str, Any], row_kind: str) -> None:
    bucket["row_count"] += 1
    if row.get("repair_application_status") == "BRANCH_LOCAL_REPAIR_APPLICATION_READY":
        bucket["ready_rows"] += 1
    if row_kind == "evidence":
        bucket["evidence_rows"] += 1
    if row.get("control_status") == "EXPANDED_MARKET_REPAIR_APPLICATION_CONTROL_PASS":
        bucket["control_pass_rows"] += 1
    value = as_float(row.get("repair_application_cost_adjusted_simulated_r"))
    if value is not None:
        bucket["application_r_sum"] += value
        bucket["application_r_count"] += 1
    effective_n = as_float(row.get("repair_application_effective_n") or row.get("candidate_effective_n"))
    if effective_n is not None:
        bucket["effective_n_sum"] += effective_n
    bucket["source_paths"].add(str(row.get("source_path") or row.get("repair_application_source_path") or ""))
    bucket["decisions"][row.get("keep_kill_redesign_implement_decision")] += 1


def aggregate_rows_from_buckets(buckets: dict[tuple[str, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        rows.append(
            boundary_row(
                {
                    "expanded_market_repair_application_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-AGG-{len(rows) + 1:07d}"
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
                    "average_repair_application_cost_adjusted_simulated_r": rounded(
                        bucket["application_r_sum"] / bucket["application_r_count"]
                        if bucket["application_r_count"]
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


def aggregate_application_rows(
    applications: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    for row in applications:
        update_bucket(buckets[aggregate_key(row, "application")], row, "application")
    for row in evidence:
        update_bucket(buckets[aggregate_key(row, "evidence")], row, "evidence")
    for row in controls:
        update_bucket(buckets[aggregate_key(row, "control")], row, "control")
    return aggregate_rows_from_buckets(buckets)
