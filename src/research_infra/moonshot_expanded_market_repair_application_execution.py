"""Execute expanded-market repair application rows against held candidate executions."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_impl_candidates import research_boundary
from src.research_infra.moonshot_expanded_market_impl_candidate_execution import normalized
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_repair_application_execution.py"
)


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_repair_application_execution_surface"] = (
        EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def same_float(left: Any, right: Any, tolerance: float = 1e-9) -> bool:
    left_value = as_float(left)
    right_value = as_float(right)
    if left_value is None and right_value is None:
        return True
    if left_value is None or right_value is None:
        return False
    return abs(left_value - right_value) <= tolerance


def application_matches_execution(application: dict[str, Any], held_execution: dict[str, Any]) -> bool:
    if not held_execution:
        return False
    text_pairs = (
        ("input_impl_candidate_execution_row_id", "expanded_market_impl_candidate_execution_row_id"),
        ("input_implementation_priority_row_id", "input_implementation_priority_row_id"),
        ("repair_application_scope_sha256", "branch_local_candidate_scope_sha256"),
        ("symbol_family", "symbol_family"),
        ("symbol", "symbol"),
        ("source_symbol", "source_symbol"),
        ("market_timeframe", "market_timeframe"),
        ("route_session", "route_session"),
        ("horizon_id", "horizon_id"),
        ("side", "side"),
        ("repair_application_source_path", "source_path"),
        ("repair_application_source_file_sha256", "source_file_sha256"),
        ("repair_application_entry_reference", "entry_reference"),
        ("repair_application_entry_reference_time", "entry_reference_time"),
        ("repair_application_path_order_result", "path_order_result"),
        ("repair_application_fill_status", "fill_status"),
    )
    for left, right in text_pairs:
        if normalized(application.get(left)) != normalized(held_execution.get(right)):
            return False
    numeric_pairs = (
        ("repair_application_proxy_entry_price", "proxy_entry_price"),
        ("repair_application_proxy_denominator_price", "proxy_denominator_price"),
        ("repair_application_proxy_target_price", "proxy_target_price"),
        ("repair_application_proxy_stop_price", "proxy_stop_price"),
        ("repair_application_cost_adjusted_simulated_r", "execution_cost_adjusted_simulated_r"),
        ("repair_application_stress_simulated_r", "execution_observed_stress_simulated_r"),
    )
    return all(same_float(application.get(left), held_execution.get(right)) for left, right in numeric_pairs)


def application_execution_row(
    application: dict[str, Any],
    held_execution: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    held = held_execution or {}
    matched = application_matches_execution(application, held)
    payload = dict(application)
    payload.update(
        {
            "expanded_market_repair_application_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-EXECUTION-{sequence:07d}"
            ),
            "input_repair_application_row_id": application.get("expanded_market_repair_application_row_id"),
            "input_impl_candidate_execution_row_id": application.get("input_impl_candidate_execution_row_id"),
            "held_candidate_execution_row_found": bool(held_execution),
            "repair_application_execution_match": matched,
            "repair_application_execution_status": "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_PASS"
            if matched
            else "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_REDESIGN",
            "held_execution_cost_adjusted_simulated_r": held.get("execution_cost_adjusted_simulated_r"),
            "held_execution_observed_stress_simulated_r": held.get("execution_observed_stress_simulated_r"),
            "held_candidate_execution_status": held.get("candidate_execution_status"),
            "follow_inverse_default_off_avoid_class": "follow" if matched else "redesign",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION_EXECUTION"
                if matched
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION_EXECUTION"
            ),
        }
    )
    return boundary_row(payload)


def evidence_execution_row(evidence: dict[str, Any], sequence: int) -> dict[str, Any]:
    payload = dict(evidence)
    payload.update(
        {
            "expanded_market_repair_application_evidence_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-EVIDENCE-EXECUTION-{sequence:07d}"
            ),
            "input_repair_application_evidence_row_id": evidence.get(
                "expanded_market_repair_application_evidence_row_id"
            ),
            "repair_application_execution_evidence_status": (
                "PRESERVED_NONCANDIDATE_REPAIR_APPLICATION_EXECUTION_EVIDENCE"
            ),
        }
    )
    return boundary_row(payload)


def control_execution_row(
    application_execution: dict[str, Any],
    application_control: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    pass_status = (
        application_execution.get("repair_application_execution_status")
        == "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_PASS"
        and (application_control or {}).get("control_status")
        == "EXPANDED_MARKET_REPAIR_APPLICATION_CONTROL_PASS"
        and (application_control or {}).get("noncandidate_scope_leakage_count") == 0
    )
    return boundary_row(
        {
            "expanded_market_repair_application_execution_control_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-EXECUTION-CONTROL-{sequence:07d}"
            ),
            "input_repair_application_execution_row_id": application_execution.get(
                "expanded_market_repair_application_execution_row_id"
            ),
            "input_repair_application_row_id": application_execution.get("input_repair_application_row_id"),
            "input_repair_application_control_row_id": (application_control or {}).get(
                "expanded_market_repair_application_control_row_id"
            ),
            "input_implementation_priority_row_id": application_execution.get(
                "input_implementation_priority_row_id"
            ),
            "repair_application_execution_match": application_execution.get(
                "repair_application_execution_match"
            ),
            "held_candidate_execution_row_found": application_execution.get("held_candidate_execution_row_found"),
            "application_control_status": (application_control or {}).get("control_status"),
            "noncandidate_scope_leakage_count": (application_control or {}).get(
                "noncandidate_scope_leakage_count"
            ),
            "control_status": "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_CONTROL_PASS"
            if pass_status
            else "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_CONTROL_REDESIGN",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION_EXECUTION_CONTROL"
                if pass_status
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION_EXECUTION_CONTROL"
            ),
        }
    )


def issue_rows(
    application_executions: list[dict[str, Any]],
    control_executions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in application_executions:
        if row.get("repair_application_execution_status") != "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_application_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_application_row_id": row.get("input_repair_application_row_id"),
                        "issue_status": row.get("repair_application_execution_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION_EXECUTION"
                        ),
                    }
                )
            )
    for row in control_executions:
        if row.get("control_status") != "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_CONTROL_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_application_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_application_row_id": row.get("input_repair_application_row_id"),
                        "issue_status": row.get("control_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_APPLICATION_EXECUTION_CONTROL"
                        ),
                    }
                )
            )
    return issues


def execution_rows(
    applications: list[dict[str, Any]],
    held_candidate_executions: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    held_by_id = {
        normalized(row.get("expanded_market_impl_candidate_execution_row_id")): row
        for row in held_candidate_executions
    }
    controls_by_application = {
        normalized(row.get("input_repair_application_row_id")): row for row in controls
    }
    application_executions: list[dict[str, Any]] = []
    control_executions: list[dict[str, Any]] = []
    for application in applications:
        held = held_by_id.get(normalized(application.get("input_impl_candidate_execution_row_id")))
        execution = application_execution_row(application, held, len(application_executions) + 1)
        application_executions.append(execution)
        control_executions.append(
            control_execution_row(
                execution,
                controls_by_application.get(normalized(application.get("expanded_market_repair_application_row_id"))),
                len(control_executions) + 1,
            )
        )
    evidence_executions = [
        evidence_execution_row(row, index) for index, row in enumerate(evidence_rows, 1)
    ]
    issues = issue_rows(application_executions, control_executions)
    return application_executions, evidence_executions, control_executions, issues


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
        "application_r_sum": 0.0,
        "application_r_count": 0,
        "effective_n_sum": 0.0,
        "source_paths": set(),
        "decisions": Counter(),
    }


def update_bucket(bucket: dict[str, Any], row: dict[str, Any], row_kind: str) -> None:
    bucket["row_count"] += 1
    if row.get("repair_application_execution_status") == "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_PASS":
        bucket["execution_pass_rows"] += 1
    if row_kind == "evidence":
        bucket["evidence_rows"] += 1
    if row.get("control_status") == "EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION_CONTROL_PASS":
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
                    "expanded_market_repair_application_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-APPLICATION-EXEC-AGG-{len(rows) + 1:07d}"
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


def aggregate_execution_rows(
    application_executions: list[dict[str, Any]],
    evidence_executions: list[dict[str, Any]],
    control_executions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    for row in application_executions:
        update_bucket(buckets[aggregate_key(row, "application_execution")], row, "application_execution")
    for row in evidence_executions:
        update_bucket(buckets[aggregate_key(row, "evidence_execution")], row, "evidence")
    for row in control_executions:
        update_bucket(buckets[aggregate_key(row, "control_execution")], row, "control_execution")
    return aggregate_rows_from_buckets(buckets)
