"""Execute expanded-market repair implementation handoffs against held artifact executions."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_impl_candidate_execution import normalized
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded
from src.research_infra.moonshot_expanded_market_repair_implementation_handoff import (
    handoff_matches_execution,
    research_boundary,
)


EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_repair_implementation_handoff_execution.py"
)


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_repair_implementation_handoff_execution_surface"] = (
        EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def handoff_execution_row(
    handoff: dict[str, Any],
    held_artifact_execution: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    held = held_artifact_execution or {}
    matched = bool(held_artifact_execution) and handoff_matches_execution(handoff, held)
    output = dict(handoff)
    output.update(
        {
            "expanded_market_repair_implementation_handoff_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-EXECUTION-{sequence:07d}"
            ),
            "input_repair_implementation_handoff_row_id": handoff.get(
                "expanded_market_repair_implementation_handoff_row_id"
            ),
            "input_repair_final_artifact_execution_row_id": handoff.get(
                "input_repair_final_artifact_execution_row_id"
            ),
            "held_final_artifact_execution_found": bool(held_artifact_execution),
            "held_final_artifact_execution_status": held.get("final_artifact_execution_status"),
            "handoff_execution_match": matched,
            "handoff_execution_status": (
                "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_PASS"
                if matched
                else "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_REDESIGN"
            ),
            "held_final_artifact_cost_adjusted_simulated_r": held.get(
                "final_repair_artifact_cost_adjusted_simulated_r"
            ),
            "held_final_artifact_stress_simulated_r": held.get(
                "final_repair_artifact_stress_simulated_r"
            ),
            "follow_inverse_default_off_avoid_class": "follow" if matched else "redesign",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF_EXECUTION"
                if matched
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF_EXECUTION"
            ),
        }
    )
    return boundary_row(output)


def evidence_execution_row(evidence: dict[str, Any], sequence: int) -> dict[str, Any]:
    output = dict(evidence)
    output.update(
        {
            "expanded_market_repair_implementation_handoff_evidence_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-EVIDENCE-EXECUTION-{sequence:07d}"
            ),
            "input_repair_implementation_handoff_evidence_row_id": evidence.get(
                "expanded_market_repair_implementation_handoff_evidence_row_id"
            ),
            "implementation_handoff_execution_evidence_status": (
                "PRESERVED_NONCANDIDATE_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_EVIDENCE"
            ),
        }
    )
    return boundary_row(output)


def control_execution_row(
    handoff_execution: dict[str, Any],
    handoff_control: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    pass_status = (
        handoff_execution.get("handoff_execution_status")
        == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_PASS"
        and (handoff_control or {}).get("control_status")
        == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_CONTROL_PASS"
        and (handoff_control or {}).get("implementation_handoff_matches_execution") is True
        and (handoff_control or {}).get("noncandidate_scope_leakage_count") == 0
    )
    return boundary_row(
        {
            "expanded_market_repair_implementation_handoff_execution_control_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-EXECUTION-CONTROL-{sequence:07d}"
            ),
            "input_repair_implementation_handoff_execution_row_id": handoff_execution.get(
                "expanded_market_repair_implementation_handoff_execution_row_id"
            ),
            "input_repair_implementation_handoff_row_id": handoff_execution.get(
                "input_repair_implementation_handoff_row_id"
            ),
            "input_repair_implementation_handoff_control_row_id": (handoff_control or {}).get(
                "expanded_market_repair_implementation_handoff_control_row_id"
            ),
            "input_repair_final_artifact_execution_row_id": handoff_execution.get(
                "input_repair_final_artifact_execution_row_id"
            ),
            "input_implementation_priority_row_id": handoff_execution.get(
                "input_implementation_priority_row_id"
            ),
            "handoff_execution_match": handoff_execution.get("handoff_execution_match"),
            "held_final_artifact_execution_found": handoff_execution.get(
                "held_final_artifact_execution_found"
            ),
            "handoff_control_status": (handoff_control or {}).get("control_status"),
            "noncandidate_scope_leakage_count": (handoff_control or {}).get(
                "noncandidate_scope_leakage_count"
            ),
            "control_status": (
                "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_CONTROL_PASS"
                if pass_status
                else "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_CONTROL_REDESIGN"
            ),
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF_EXECUTION_CONTROL"
                if pass_status
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF_EXECUTION_CONTROL"
            ),
        }
    )


def issue_rows(
    executions: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in executions:
        if row.get("handoff_execution_status") != "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_implementation_handoff_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-HANDOFF-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_implementation_handoff_row_id": row.get(
                            "input_repair_implementation_handoff_row_id"
                        ),
                        "issue_status": row.get("handoff_execution_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF_EXECUTION"
                        ),
                    }
                )
            )
    for row in controls:
        if row.get("control_status") != "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_CONTROL_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_implementation_handoff_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-HANDOFF-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_implementation_handoff_row_id": row.get(
                            "input_repair_implementation_handoff_row_id"
                        ),
                        "issue_status": row.get("control_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF_EXECUTION_CONTROL"
                        ),
                    }
                )
            )
    return issues


def execution_rows(
    handoffs: list[dict[str, Any]],
    held_artifact_executions: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    held_by_execution = {
        normalized(row.get("expanded_market_repair_final_artifact_execution_row_id")): row
        for row in held_artifact_executions
    }
    controls_by_handoff = {
        normalized(row.get("input_repair_implementation_handoff_row_id")): row for row in controls
    }
    executions: list[dict[str, Any]] = []
    execution_controls: list[dict[str, Any]] = []
    for handoff in handoffs:
        held = held_by_execution.get(
            normalized(handoff.get("input_repair_final_artifact_execution_row_id"))
        )
        execution = handoff_execution_row(handoff, held, len(executions) + 1)
        executions.append(execution)
        execution_controls.append(
            control_execution_row(
                execution,
                controls_by_handoff.get(
                    normalized(handoff.get("expanded_market_repair_implementation_handoff_row_id"))
                ),
                len(execution_controls) + 1,
            )
        )
    evidence_executions = [
        evidence_execution_row(row, index) for index, row in enumerate(evidence_rows, 1)
    ]
    issues = issue_rows(executions, execution_controls)
    return executions, evidence_executions, execution_controls, issues


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
        "handoff_r_sum": 0.0,
        "handoff_r_count": 0,
        "effective_n_sum": 0.0,
        "source_paths": set(),
        "decisions": Counter(),
    }


def update_bucket(bucket: dict[str, Any], row: dict[str, Any], row_kind: str) -> None:
    bucket["row_count"] += 1
    if row.get("handoff_execution_status") == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_PASS":
        bucket["execution_pass_rows"] += 1
    if row_kind == "evidence":
        bucket["evidence_rows"] += 1
    if row.get("control_status") == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_CONTROL_PASS":
        bucket["control_pass_rows"] += 1
    value = as_float(row.get("implementation_handoff_cost_adjusted_simulated_r"))
    if value is not None:
        bucket["handoff_r_sum"] += value
        bucket["handoff_r_count"] += 1
    effective_n = as_float(row.get("implementation_handoff_effective_n"))
    if effective_n is not None:
        bucket["effective_n_sum"] += effective_n
    bucket["source_paths"].add(str(row.get("implementation_handoff_source_path") or row.get("source_path") or ""))
    bucket["decisions"][row.get("keep_kill_redesign_implement_decision")] += 1


def aggregate_rows_from_buckets(buckets: dict[tuple[str, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        rows.append(
            boundary_row(
                {
                    "expanded_market_repair_implementation_handoff_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-HANDOFF-EXEC-AGG-{len(rows) + 1:07d}"
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
                    "average_implementation_handoff_cost_adjusted_simulated_r": rounded(
                        bucket["handoff_r_sum"] / bucket["handoff_r_count"]
                        if bucket["handoff_r_count"]
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
    executions: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    for row in executions:
        update_bucket(buckets[aggregate_key(row, "handoff_execution")], row, "handoff_execution")
    for row in evidence:
        update_bucket(buckets[aggregate_key(row, "evidence_execution")], row, "evidence")
    for row in controls:
        update_bucket(buckets[aggregate_key(row, "control_execution")], row, "control_execution")
    return aggregate_rows_from_buckets(buckets)
