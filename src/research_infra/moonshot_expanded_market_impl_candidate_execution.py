"""Execute expanded-market implementation candidates against held priority rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_impl_candidates import (
    EXPANDED_MARKET_IMPL_CANDIDATES,
    matches_candidate_scope,
    normalized,
    research_boundary,
)
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_impl_candidate_execution.py"
)


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_impl_candidate_execution_surface"] = (
        EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def candidate_execution_row(
    candidate: dict[str, Any],
    held_row: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    held = held_row or {}
    matched = bool(held_row) and matches_candidate_scope(candidate, held)
    payload = dict(held)
    payload.update(
        {
            "expanded_market_impl_candidate_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-IMPL-EXECUTION-{sequence:07d}"
            ),
            "input_impl_candidate_row_id": candidate.get("expanded_market_impl_candidate_row_id"),
            "input_implementation_priority_row_id": candidate.get(
                "input_implementation_priority_row_id"
            ),
            "branch_local_candidate_scope_sha256": candidate.get(
                "branch_local_candidate_scope_sha256"
            ),
            "candidate_function_name": candidate.get("candidate_function_name"),
            "branch_local_code_expression": candidate.get("branch_local_code_expression"),
            "held_priority_row_found": bool(held_row),
            "candidate_scope_match": matched,
            "candidate_execution_status": (
                "EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION_PASS"
                if matched
                else "EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION_REDESIGN"
            ),
            "candidate_cost_adjusted_simulated_r": candidate.get(
                "candidate_cost_adjusted_simulated_r"
            ),
            "candidate_stress_simulated_r": candidate.get("candidate_stress_simulated_r"),
            "candidate_effective_n": candidate.get("candidate_effective_n"),
            "execution_cost_adjusted_simulated_r": held.get(
                "alternate_source_proxy_cost_adjusted_simulated_r"
            ),
            "execution_observed_cost_adjusted_simulated_r": held.get(
                "observed_cost_adjusted_simulated_r"
            ),
            "execution_observed_stress_simulated_r": held.get("observed_stress_simulated_r"),
            "follow_inverse_default_off_avoid_class": "follow" if matched else "redesign",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE_EXECUTION"
                if matched
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE_EXECUTION"
            ),
        }
    )
    return boundary_row(payload)


def evidence_execution_row(evidence: dict[str, Any], sequence: int) -> dict[str, Any]:
    payload = dict(evidence)
    payload.update(
        {
            "expanded_market_impl_candidate_evidence_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-IMPL-EVIDENCE-EXECUTION-{sequence:07d}"
            ),
            "input_impl_candidate_evidence_row_id": evidence.get(
                "expanded_market_impl_candidate_evidence_row_id"
            ),
            "input_implementation_priority_row_id": evidence.get(
                "input_implementation_priority_row_id"
            ),
            "evidence_execution_status": "PRESERVED_NONCANDIDATE_PRIORITY_EVIDENCE_EXECUTION",
            "execution_observed_cost_adjusted_simulated_r": evidence.get(
                "observed_cost_adjusted_simulated_r"
            ),
            "execution_observed_stress_simulated_r": evidence.get("observed_stress_simulated_r"),
            "execution_alternate_source_proxy_cost_adjusted_simulated_r": evidence.get(
                "alternate_source_proxy_cost_adjusted_simulated_r"
            ),
        }
    )
    return boundary_row(payload)


def control_row(
    candidate: dict[str, Any],
    execution: dict[str, Any],
    self_test: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    self_test_status = (self_test or {}).get("self_test_status")
    pass_status = (
        execution.get("candidate_scope_match") is True
        and execution.get("held_priority_row_found") is True
        and self_test_status == "EXPANDED_MARKET_IMPL_CANDIDATE_SELF_TEST_PASS"
    )
    return boundary_row(
        {
            "expanded_market_impl_candidate_control_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-IMPL-CONTROL-{sequence:07d}"
            ),
            "input_impl_candidate_row_id": candidate.get("expanded_market_impl_candidate_row_id"),
            "input_impl_candidate_execution_row_id": execution.get(
                "expanded_market_impl_candidate_execution_row_id"
            ),
            "input_impl_candidate_self_test_row_id": (self_test or {}).get(
                "expanded_market_impl_candidate_self_test_row_id"
            ),
            "input_implementation_priority_row_id": candidate.get(
                "input_implementation_priority_row_id"
            ),
            "branch_local_candidate_scope_sha256": candidate.get(
                "branch_local_candidate_scope_sha256"
            ),
            "positive_execution_match": execution.get("candidate_scope_match") is True,
            "held_priority_row_found": execution.get("held_priority_row_found") is True,
            "self_test_status": self_test_status,
            "noncandidate_scope_leakage_count": 0,
            "control_status": "EXPANDED_MARKET_IMPL_CANDIDATE_CONTROL_PASS"
            if pass_status
            else "EXPANDED_MARKET_IMPL_CANDIDATE_CONTROL_REDESIGN",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE_CONTROL"
                if pass_status
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE_CONTROL"
            ),
        }
    )


def issue_rows(
    executions: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in executions:
        if row.get("candidate_execution_status") != "EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_impl_candidate_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-IMPL-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_impl_candidate_row_id": row.get("input_impl_candidate_row_id"),
                        "issue_status": row.get("candidate_execution_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE_EXECUTION"
                        ),
                    }
                )
            )
    for row in controls:
        if row.get("control_status") != "EXPANDED_MARKET_IMPL_CANDIDATE_CONTROL_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_impl_candidate_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-IMPL-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_impl_candidate_row_id": row.get("input_impl_candidate_row_id"),
                        "issue_status": row.get("control_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_CANDIDATE_CONTROL"
                        ),
                    }
                )
            )
    return issues


def execution_rows(
    candidates: list[dict[str, Any]],
    held_priority_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    self_tests: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    held_by_id = {
        normalized(row.get("expanded_market_implementation_priority_row_id")): row
        for row in held_priority_rows
    }
    self_tests_by_id = {
        normalized(row.get("input_implementation_priority_row_id")): row for row in self_tests
    }
    executions: list[dict[str, Any]] = []
    controls: list[dict[str, Any]] = []
    for candidate in candidates:
        held = held_by_id.get(normalized(candidate.get("input_implementation_priority_row_id")))
        execution = candidate_execution_row(candidate, held, len(executions) + 1)
        executions.append(execution)
        controls.append(
            control_row(
                candidate,
                execution,
                self_tests_by_id.get(normalized(candidate.get("input_implementation_priority_row_id"))),
                len(controls) + 1,
            )
        )
    evidence = [
        evidence_execution_row(row, index) for index, row in enumerate(evidence_rows, 1)
    ]
    issues = issue_rows(executions, controls)
    return executions, evidence, controls, issues


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
        "candidate_r_sum": 0.0,
        "candidate_r_count": 0,
        "observed_sum": 0.0,
        "observed_count": 0,
        "effective_n_sum": 0,
        "win_count": 0,
        "loss_count": 0,
        "zero_count": 0,
        "target_first_count": 0,
        "stop_first_count": 0,
        "neither_count": 0,
        "ambiguous_count": 0,
        "source_paths": set(),
        "decisions": Counter(),
    }


def update_bucket(bucket: dict[str, Any], row: dict[str, Any], row_kind: str) -> None:
    bucket["row_count"] += 1
    if row_kind == "execution" and row.get("candidate_scope_match") is True:
        bucket["execution_pass_rows"] += 1
    if row_kind == "evidence":
        bucket["evidence_rows"] += 1
    if row_kind == "control" and row.get("control_status") == "EXPANDED_MARKET_IMPL_CANDIDATE_CONTROL_PASS":
        bucket["control_pass_rows"] += 1
    candidate_r = as_float(row.get("candidate_cost_adjusted_simulated_r"))
    if candidate_r is not None:
        bucket["candidate_r_sum"] += candidate_r
        bucket["candidate_r_count"] += 1
    observed = as_float(row.get("observed_cost_adjusted_simulated_r"))
    if observed is None:
        observed = as_float(row.get("execution_observed_cost_adjusted_simulated_r"))
    if observed is not None:
        bucket["observed_sum"] += observed
        bucket["observed_count"] += 1
    bucket["effective_n_sum"] += int(float(row.get("effective_n") or row.get("candidate_effective_n") or 0))
    for field in (
        "win_count",
        "loss_count",
        "zero_count",
        "target_first_count",
        "stop_first_count",
        "neither_count",
        "ambiguous_count",
    ):
        bucket[field] += int(row.get(field) or 0)
    bucket["source_paths"].add(str(row.get("source_path") or ""))
    bucket["decisions"][row.get("keep_kill_redesign_implement_decision")] += 1


def aggregate_rows_from_buckets(buckets: dict[tuple[str, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        rows.append(
            boundary_row(
                {
                    "expanded_market_impl_candidate_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-IMPL-EXEC-AGG-{len(rows) + 1:07d}"
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
                    "average_candidate_cost_adjusted_simulated_r": rounded(
                        bucket["candidate_r_sum"] / bucket["candidate_r_count"]
                        if bucket["candidate_r_count"]
                        else None
                    ),
                    "average_observed_cost_adjusted_simulated_r": rounded(
                        bucket["observed_sum"] / bucket["observed_count"]
                        if bucket["observed_count"]
                        else None
                    ),
                    "effective_n_sum": bucket["effective_n_sum"],
                    "win_count": bucket["win_count"],
                    "loss_count": bucket["loss_count"],
                    "zero_count": bucket["zero_count"],
                    "target_first_count": bucket["target_first_count"],
                    "stop_first_count": bucket["stop_first_count"],
                    "neither_count": bucket["neither_count"],
                    "ambiguous_count": bucket["ambiguous_count"],
                    "source_path_count": len(bucket["source_paths"]),
                    "decision_counts": dict(sorted(bucket["decisions"].items())),
                    "keep_kill_redesign_implement_decision": bucket["decisions"].most_common(1)[0][0],
                }
            )
        )
    return rows


def aggregate_execution_rows(
    executions: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    for row in executions:
        update_bucket(buckets[aggregate_key(row, "execution")], row, "execution")
    for row in evidence:
        update_bucket(buckets[aggregate_key(row, "evidence")], row, "evidence")
    for row in controls:
        update_bucket(buckets[aggregate_key(row, "control")], row, "control")
    return aggregate_rows_from_buckets(buckets)
