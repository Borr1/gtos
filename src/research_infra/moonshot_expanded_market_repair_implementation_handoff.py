"""Implementation handoff packet from expanded-market final artifact executions."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_impl_candidates import research_boundary
from src.research_infra.moonshot_expanded_market_impl_candidate_execution import normalized
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF = (
    "src/research_infra/moonshot_expanded_market_repair_implementation_handoff.py"
)


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_repair_implementation_handoff_surface"] = (
        EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF
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


def handoff_payload(execution: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_repair_final_artifact_execution_row_id": execution.get(
            "expanded_market_repair_final_artifact_execution_row_id"
        ),
        "input_repair_final_artifact_row_id": execution.get("input_repair_final_artifact_row_id"),
        "input_repair_application_execution_row_id": execution.get(
            "input_repair_application_execution_row_id"
        ),
        "input_implementation_priority_row_id": execution.get("input_implementation_priority_row_id"),
        "final_repair_artifact_function_name": execution.get("final_repair_artifact_function_name"),
        "final_repair_artifact_scope_sha256": execution.get("final_repair_artifact_scope_sha256"),
        "final_repair_artifact_source_path": execution.get("final_repair_artifact_source_path"),
        "final_repair_artifact_source_file_sha256": execution.get(
            "final_repair_artifact_source_file_sha256"
        ),
        "symbol_family": execution.get("symbol_family"),
        "symbol": execution.get("symbol"),
        "source_symbol": execution.get("source_symbol"),
        "market_timeframe": execution.get("market_timeframe"),
        "route_session": execution.get("route_session"),
        "horizon_id": execution.get("horizon_id"),
        "side": execution.get("side"),
        "repair_application_proxy_entry_price": execution.get("repair_application_proxy_entry_price"),
        "repair_application_proxy_denominator_price": execution.get(
            "repair_application_proxy_denominator_price"
        ),
        "repair_application_proxy_target_price": execution.get("repair_application_proxy_target_price"),
        "repair_application_proxy_stop_price": execution.get("repair_application_proxy_stop_price"),
        "final_repair_artifact_cost_adjusted_simulated_r": execution.get(
            "final_repair_artifact_cost_adjusted_simulated_r"
        ),
        "final_repair_artifact_stress_simulated_r": execution.get("final_repair_artifact_stress_simulated_r"),
        "final_repair_artifact_effective_n": execution.get("final_repair_artifact_effective_n"),
    }


def handoff_matches_execution(handoff: dict[str, Any], execution: dict[str, Any]) -> bool:
    payload = handoff.get("implementation_handoff_payload") or {}
    execution_field_map = {
        "input_repair_final_artifact_execution_row_id": (
            "expanded_market_repair_final_artifact_execution_row_id"
        ),
    }
    for field, expected in payload.items():
        execution_field = execution_field_map.get(field, field)
        if field in {
            "repair_application_proxy_entry_price",
            "repair_application_proxy_denominator_price",
            "repair_application_proxy_target_price",
            "repair_application_proxy_stop_price",
            "final_repair_artifact_cost_adjusted_simulated_r",
            "final_repair_artifact_stress_simulated_r",
            "final_repair_artifact_effective_n",
        }:
            if not same_float(execution.get(execution_field), expected):
                return False
        elif normalized(execution.get(execution_field)) != normalized(expected):
            return False
    return True


def handoff_row(execution: dict[str, Any], sequence: int) -> dict[str, Any]:
    ready = execution.get("final_artifact_execution_status") == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS"
    payload = handoff_payload(execution)
    signature = digest(payload)
    acceptance = digest(
        {
            "handoff_payload_sha256": signature,
            "required_execution_status": "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS",
            "required_control_status": "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS",
            "required_noncandidate_scope_leakage_count": 0,
        }
    )
    output = dict(execution)
    output.update(
        {
            "expanded_market_repair_implementation_handoff_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-{sequence:07d}"
            ),
            "input_repair_final_artifact_execution_row_id": execution.get(
                "expanded_market_repair_final_artifact_execution_row_id"
            ),
            "implementation_handoff_family": "positive_alternate_source_repair",
            "implementation_handoff_payload": payload,
            "implementation_handoff_scope": payload,
            "implementation_handoff_signature_sha256": signature,
            "implementation_handoff_acceptance_sha256": acceptance,
            "implementation_handoff_function_name": execution.get("final_repair_artifact_function_name"),
            "implementation_handoff_expression": execution.get("final_repair_artifact_expression"),
            "implementation_handoff_scope_sha256": execution.get("final_repair_artifact_scope_sha256"),
            "implementation_handoff_source_path": execution.get("final_repair_artifact_source_path"),
            "implementation_handoff_source_file_sha256": execution.get(
                "final_repair_artifact_source_file_sha256"
            ),
            "implementation_handoff_entry_reference": execution.get("repair_application_entry_reference"),
            "implementation_handoff_entry_reference_time": execution.get(
                "repair_application_entry_reference_time"
            ),
            "implementation_handoff_path_order_result": execution.get(
                "repair_application_path_order_result"
            ),
            "implementation_handoff_fill_status": execution.get("repair_application_fill_status"),
            "implementation_handoff_proxy_entry_price": execution.get(
                "repair_application_proxy_entry_price"
            ),
            "implementation_handoff_proxy_denominator_price": execution.get(
                "repair_application_proxy_denominator_price"
            ),
            "implementation_handoff_proxy_target_price": execution.get(
                "repair_application_proxy_target_price"
            ),
            "implementation_handoff_proxy_stop_price": execution.get(
                "repair_application_proxy_stop_price"
            ),
            "implementation_handoff_cost_adjusted_simulated_r": execution.get(
                "final_repair_artifact_cost_adjusted_simulated_r"
            ),
            "implementation_handoff_stress_simulated_r": execution.get(
                "final_repair_artifact_stress_simulated_r"
            ),
            "implementation_handoff_effective_n": execution.get("final_repair_artifact_effective_n"),
            "implementation_handoff_status": "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_HANDOFF_READY"
            if ready
            else "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_HANDOFF_REDESIGN",
            "follow_inverse_default_off_avoid_class": "follow" if ready else "redesign",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF"
                if ready
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF"
            ),
        }
    )
    return boundary_row(output)


def evidence_handoff_row(evidence: dict[str, Any], sequence: int) -> dict[str, Any]:
    output = dict(evidence)
    output.update(
        {
            "expanded_market_repair_implementation_handoff_evidence_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-EVIDENCE-{sequence:07d}"
            ),
            "input_repair_final_artifact_evidence_execution_row_id": evidence.get(
                "expanded_market_repair_final_artifact_evidence_execution_row_id"
            ),
            "implementation_handoff_evidence_status": (
                "PRESERVED_NONCANDIDATE_REPAIR_IMPLEMENTATION_HANDOFF_EVIDENCE"
            ),
        }
    )
    return boundary_row(output)


def handoff_control_row(
    handoff: dict[str, Any],
    execution: dict[str, Any],
    execution_control: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    handoff_match = handoff_matches_execution(handoff, execution)
    pass_status = (
        handoff.get("implementation_handoff_status") == "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_HANDOFF_READY"
        and handoff_match
        and (execution_control or {}).get("control_status")
        == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS"
        and (execution_control or {}).get("noncandidate_scope_leakage_count") == 0
    )
    return boundary_row(
        {
            "expanded_market_repair_implementation_handoff_control_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-CONTROL-{sequence:07d}"
            ),
            "input_repair_implementation_handoff_row_id": handoff.get(
                "expanded_market_repair_implementation_handoff_row_id"
            ),
            "input_repair_final_artifact_execution_row_id": execution.get(
                "expanded_market_repair_final_artifact_execution_row_id"
            ),
            "input_repair_final_artifact_execution_control_row_id": (execution_control or {}).get(
                "expanded_market_repair_final_artifact_execution_control_row_id"
            ),
            "input_implementation_priority_row_id": handoff.get("input_implementation_priority_row_id"),
            "implementation_handoff_signature_sha256": handoff.get("implementation_handoff_signature_sha256"),
            "implementation_handoff_acceptance_sha256": handoff.get(
                "implementation_handoff_acceptance_sha256"
            ),
            "implementation_handoff_matches_execution": handoff_match,
            "artifact_execution_control_status": (execution_control or {}).get("control_status"),
            "noncandidate_scope_leakage_count": (execution_control or {}).get(
                "noncandidate_scope_leakage_count"
            ),
            "control_status": "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_CONTROL_PASS"
            if pass_status
            else "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_CONTROL_REDESIGN",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF_CONTROL"
                if pass_status
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF_CONTROL"
            ),
        }
    )


def issue_rows(handoffs: list[dict[str, Any]], controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in handoffs:
        if row.get("implementation_handoff_status") != "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_HANDOFF_READY":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_implementation_handoff_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_implementation_handoff_row_id": row.get(
                            "expanded_market_repair_implementation_handoff_row_id"
                        ),
                        "issue_status": row.get("implementation_handoff_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF"
                        ),
                    }
                )
            )
    for row in controls:
        if row.get("control_status") != "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_CONTROL_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_implementation_handoff_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_repair_implementation_handoff_row_id": row.get(
                            "input_repair_implementation_handoff_row_id"
                        ),
                        "issue_status": row.get("control_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_HANDOFF_CONTROL"
                        ),
                    }
                )
            )
    return issues


def implementation_handoff_rows(
    executions: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    controls_by_execution = {
        normalized(row.get("input_repair_final_artifact_execution_row_id")): row for row in controls
    }
    handoffs: list[dict[str, Any]] = []
    handoff_controls: list[dict[str, Any]] = []
    for execution in executions:
        handoff = handoff_row(execution, len(handoffs) + 1)
        handoffs.append(handoff)
        handoff_controls.append(
            handoff_control_row(
                handoff,
                execution,
                controls_by_execution.get(
                    normalized(execution.get("expanded_market_repair_final_artifact_execution_row_id"))
                ),
                len(handoff_controls) + 1,
            )
        )
    evidence = [
        evidence_handoff_row(row, index) for index, row in enumerate(evidence_rows, 1)
    ]
    issues = issue_rows(handoffs, handoff_controls)
    return handoffs, evidence, handoff_controls, issues


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
        "handoff_ready_rows": 0,
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
    if row.get("implementation_handoff_status") == "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_HANDOFF_READY":
        bucket["handoff_ready_rows"] += 1
    if row_kind == "evidence":
        bucket["evidence_rows"] += 1
    if row.get("control_status") == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_CONTROL_PASS":
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
                    "expanded_market_repair_implementation_handoff_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-HANDOFF-AGG-{len(rows) + 1:07d}"
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
                    "handoff_ready_rows": bucket["handoff_ready_rows"],
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


def aggregate_handoff_rows(
    handoffs: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    for row in handoffs:
        update_bucket(buckets[aggregate_key(row, "handoff")], row, "handoff")
    for row in evidence:
        update_bucket(buckets[aggregate_key(row, "evidence")], row, "evidence")
    for row in controls:
        update_bucket(buckets[aggregate_key(row, "control")], row, "control")
    return aggregate_rows_from_buckets(buckets)
