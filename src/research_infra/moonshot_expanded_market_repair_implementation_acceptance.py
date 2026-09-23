"""Accept executed expanded-market repair implementations for branch-local use."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_impl_candidate_execution import normalized
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded
from src.research_infra.moonshot_expanded_market_repair_implementation_handoff_execution import (
    research_boundary,
)


EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE = (
    "src/research_infra/moonshot_expanded_market_repair_implementation_acceptance.py"
)


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_repair_implementation_acceptance_surface"] = (
        EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE
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


def acceptance_contract(execution: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_handoff_execution_row_id": execution.get(
            "expanded_market_repair_implementation_handoff_execution_row_id"
        ),
        "input_repair_implementation_handoff_row_id": execution.get(
            "input_repair_implementation_handoff_row_id"
        ),
        "input_repair_final_artifact_execution_row_id": execution.get(
            "input_repair_final_artifact_execution_row_id"
        ),
        "input_implementation_priority_row_id": execution.get("input_implementation_priority_row_id"),
        "implementation_handoff_acceptance_sha256": execution.get(
            "implementation_handoff_acceptance_sha256"
        ),
        "implementation_handoff_function_name": execution.get("implementation_handoff_function_name"),
        "implementation_handoff_expression": execution.get("implementation_handoff_expression"),
        "implementation_handoff_scope_sha256": execution.get("implementation_handoff_scope_sha256"),
        "implementation_handoff_source_path": execution.get("implementation_handoff_source_path"),
        "implementation_handoff_source_file_sha256": execution.get(
            "implementation_handoff_source_file_sha256"
        ),
        "symbol_family": execution.get("symbol_family"),
        "symbol": execution.get("symbol"),
        "source_symbol": execution.get("source_symbol"),
        "market_timeframe": execution.get("market_timeframe"),
        "route_session": execution.get("route_session"),
        "horizon_id": execution.get("horizon_id"),
        "side": execution.get("side"),
        "entry_reference": execution.get("implementation_handoff_entry_reference"),
        "entry_reference_time": execution.get("implementation_handoff_entry_reference_time"),
        "path_order_result": execution.get("implementation_handoff_path_order_result"),
        "fill_status": execution.get("implementation_handoff_fill_status"),
        "proxy_entry_price": execution.get("implementation_handoff_proxy_entry_price"),
        "proxy_denominator_price": execution.get(
            "implementation_handoff_proxy_denominator_price"
        ),
        "proxy_target_price": execution.get("implementation_handoff_proxy_target_price"),
        "proxy_stop_price": execution.get("implementation_handoff_proxy_stop_price"),
        "cost_adjusted_simulated_r": execution.get(
            "implementation_handoff_cost_adjusted_simulated_r"
        ),
        "stress_simulated_r": execution.get("implementation_handoff_stress_simulated_r"),
        "effective_n": execution.get("implementation_handoff_effective_n"),
    }


def acceptance_matches_execution(acceptance: dict[str, Any], execution: dict[str, Any]) -> bool:
    contract = acceptance.get("implementation_acceptance_contract") or {}
    execution_field_map = {
        "input_handoff_execution_row_id": (
            "expanded_market_repair_implementation_handoff_execution_row_id"
        ),
        "entry_reference": "implementation_handoff_entry_reference",
        "entry_reference_time": "implementation_handoff_entry_reference_time",
        "path_order_result": "implementation_handoff_path_order_result",
        "fill_status": "implementation_handoff_fill_status",
        "proxy_entry_price": "implementation_handoff_proxy_entry_price",
        "proxy_denominator_price": "implementation_handoff_proxy_denominator_price",
        "proxy_target_price": "implementation_handoff_proxy_target_price",
        "proxy_stop_price": "implementation_handoff_proxy_stop_price",
        "cost_adjusted_simulated_r": "implementation_handoff_cost_adjusted_simulated_r",
        "stress_simulated_r": "implementation_handoff_stress_simulated_r",
        "effective_n": "implementation_handoff_effective_n",
    }
    float_fields = {
        "proxy_entry_price",
        "proxy_denominator_price",
        "proxy_target_price",
        "proxy_stop_price",
        "cost_adjusted_simulated_r",
        "stress_simulated_r",
        "effective_n",
    }
    for field, expected in contract.items():
        execution_field = execution_field_map.get(field, field)
        if field in float_fields:
            if not same_float(execution.get(execution_field), expected):
                return False
        elif normalized(execution.get(execution_field)) != normalized(expected):
            return False
    return True


def acceptance_row(execution: dict[str, Any], sequence: int) -> dict[str, Any]:
    accepted = (
        execution.get("handoff_execution_status")
        == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_PASS"
    )
    contract = acceptance_contract(execution)
    contract_sha = digest(contract)
    output = dict(execution)
    output.update(
        {
            "expanded_market_repair_implementation_acceptance_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-ACCEPTANCE-{sequence:07d}"
            ),
            "input_handoff_execution_row_id": execution.get(
                "expanded_market_repair_implementation_handoff_execution_row_id"
            ),
            "implementation_acceptance_contract": contract,
            "implementation_acceptance_contract_sha256": contract_sha,
            "implementation_acceptance_status": (
                "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_ACCEPTED"
                if accepted
                else "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_REDESIGN"
            ),
            "accepted_branch_local_function_name": execution.get(
                "implementation_handoff_function_name"
            ),
            "accepted_branch_local_expression": execution.get("implementation_handoff_expression"),
            "accepted_source_path": execution.get("implementation_handoff_source_path"),
            "accepted_source_file_sha256": execution.get(
                "implementation_handoff_source_file_sha256"
            ),
            "accepted_entry_reference": execution.get("implementation_handoff_entry_reference"),
            "accepted_entry_reference_time": execution.get(
                "implementation_handoff_entry_reference_time"
            ),
            "accepted_path_order_result": execution.get("implementation_handoff_path_order_result"),
            "accepted_fill_status": execution.get("implementation_handoff_fill_status"),
            "accepted_proxy_entry_price": execution.get("implementation_handoff_proxy_entry_price"),
            "accepted_proxy_denominator_price": execution.get(
                "implementation_handoff_proxy_denominator_price"
            ),
            "accepted_proxy_target_price": execution.get("implementation_handoff_proxy_target_price"),
            "accepted_proxy_stop_price": execution.get("implementation_handoff_proxy_stop_price"),
            "accepted_cost_adjusted_simulated_r": execution.get(
                "implementation_handoff_cost_adjusted_simulated_r"
            ),
            "accepted_stress_simulated_r": execution.get("implementation_handoff_stress_simulated_r"),
            "accepted_effective_n": execution.get("implementation_handoff_effective_n"),
            "follow_inverse_default_off_avoid_class": "follow" if accepted else "redesign",
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_ACCEPTANCE"
                if accepted
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_ACCEPTANCE"
            ),
        }
    )
    return boundary_row(output)


def evidence_acceptance_row(evidence: dict[str, Any], sequence: int) -> dict[str, Any]:
    output = dict(evidence)
    output.update(
        {
            "expanded_market_repair_implementation_acceptance_evidence_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-ACCEPTANCE-EVIDENCE-{sequence:07d}"
            ),
            "input_handoff_execution_evidence_row_id": evidence.get(
                "expanded_market_repair_implementation_handoff_evidence_execution_row_id"
            ),
            "implementation_acceptance_evidence_status": (
                "PRESERVED_NONCANDIDATE_REPAIR_IMPLEMENTATION_ACCEPTANCE_EVIDENCE"
            ),
        }
    )
    return boundary_row(output)


def acceptance_control_row(
    acceptance: dict[str, Any],
    execution: dict[str, Any],
    execution_control: dict[str, Any] | None,
    sequence: int,
) -> dict[str, Any]:
    acceptance_match = acceptance_matches_execution(acceptance, execution)
    pass_status = (
        acceptance.get("implementation_acceptance_status")
        == "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_ACCEPTED"
        and acceptance_match
        and (execution_control or {}).get("control_status")
        == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_EXECUTION_CONTROL_PASS"
        and (execution_control or {}).get("noncandidate_scope_leakage_count") == 0
    )
    return boundary_row(
        {
            "expanded_market_repair_implementation_acceptance_control_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-IMPLEMENTATION-ACCEPTANCE-CONTROL-{sequence:07d}"
            ),
            "input_implementation_acceptance_row_id": acceptance.get(
                "expanded_market_repair_implementation_acceptance_row_id"
            ),
            "input_handoff_execution_row_id": execution.get(
                "expanded_market_repair_implementation_handoff_execution_row_id"
            ),
            "input_handoff_execution_control_row_id": (execution_control or {}).get(
                "expanded_market_repair_implementation_handoff_execution_control_row_id"
            ),
            "input_implementation_priority_row_id": acceptance.get(
                "input_implementation_priority_row_id"
            ),
            "implementation_acceptance_contract_sha256": acceptance.get(
                "implementation_acceptance_contract_sha256"
            ),
            "implementation_acceptance_matches_execution": acceptance_match,
            "handoff_execution_control_status": (execution_control or {}).get("control_status"),
            "noncandidate_scope_leakage_count": (execution_control or {}).get(
                "noncandidate_scope_leakage_count"
            ),
            "control_status": (
                "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_CONTROL_PASS"
                if pass_status
                else "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_CONTROL_REDESIGN"
            ),
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_ACCEPTANCE_CONTROL"
                if pass_status
                else "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_ACCEPTANCE_CONTROL"
            ),
        }
    )


def issue_rows(acceptances: list[dict[str, Any]], controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in acceptances:
        if row.get("implementation_acceptance_status") != "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_ACCEPTED":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_implementation_acceptance_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-ACCEPTANCE-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_handoff_execution_row_id": row.get("input_handoff_execution_row_id"),
                        "issue_status": row.get("implementation_acceptance_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_ACCEPTANCE"
                        ),
                    }
                )
            )
    for row in controls:
        if row.get("control_status") != "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_CONTROL_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_repair_implementation_acceptance_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-ACCEPTANCE-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "input_implementation_acceptance_row_id": row.get(
                            "input_implementation_acceptance_row_id"
                        ),
                        "issue_status": row.get("control_status"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_ACCEPTANCE_CONTROL"
                        ),
                    }
                )
            )
    return issues


def acceptance_rows(
    executions: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    controls_by_execution = {
        normalized(row.get("input_repair_implementation_handoff_execution_row_id")): row
        for row in controls
    }
    acceptances: list[dict[str, Any]] = []
    acceptance_controls: list[dict[str, Any]] = []
    for execution in executions:
        acceptance = acceptance_row(execution, len(acceptances) + 1)
        acceptances.append(acceptance)
        acceptance_controls.append(
            acceptance_control_row(
                acceptance,
                execution,
                controls_by_execution.get(
                    normalized(
                        execution.get(
                            "expanded_market_repair_implementation_handoff_execution_row_id"
                        )
                    )
                ),
                len(acceptance_controls) + 1,
            )
        )
    evidence = [
        evidence_acceptance_row(row, index) for index, row in enumerate(evidence_rows, 1)
    ]
    issues = issue_rows(acceptances, acceptance_controls)
    return acceptances, evidence, acceptance_controls, issues


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
        "accepted_rows": 0,
        "evidence_rows": 0,
        "control_pass_rows": 0,
        "accepted_r_sum": 0.0,
        "accepted_r_count": 0,
        "effective_n_sum": 0.0,
        "source_paths": set(),
        "decisions": Counter(),
    }


def update_bucket(bucket: dict[str, Any], row: dict[str, Any], row_kind: str) -> None:
    bucket["row_count"] += 1
    if row.get("implementation_acceptance_status") == "BRANCH_LOCAL_REPAIR_IMPLEMENTATION_ACCEPTED":
        bucket["accepted_rows"] += 1
    if row_kind == "evidence":
        bucket["evidence_rows"] += 1
    if row.get("control_status") == "EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_CONTROL_PASS":
        bucket["control_pass_rows"] += 1
    value = as_float(row.get("accepted_cost_adjusted_simulated_r"))
    if value is not None:
        bucket["accepted_r_sum"] += value
        bucket["accepted_r_count"] += 1
    effective_n = as_float(row.get("accepted_effective_n"))
    if effective_n is not None:
        bucket["effective_n_sum"] += effective_n
    bucket["source_paths"].add(str(row.get("accepted_source_path") or row.get("source_path") or ""))
    bucket["decisions"][row.get("keep_kill_redesign_implement_decision")] += 1


def aggregate_rows_from_buckets(buckets: dict[tuple[str, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        rows.append(
            boundary_row(
                {
                    "expanded_market_repair_implementation_acceptance_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPAIR-ACCEPTANCE-AGG-{len(rows) + 1:07d}"
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
                    "accepted_rows": bucket["accepted_rows"],
                    "evidence_rows": bucket["evidence_rows"],
                    "control_pass_rows": bucket["control_pass_rows"],
                    "average_accepted_cost_adjusted_simulated_r": rounded(
                        bucket["accepted_r_sum"] / bucket["accepted_r_count"]
                        if bucket["accepted_r_count"]
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


def aggregate_acceptance_rows(
    acceptances: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_bucket)
    for row in acceptances:
        update_bucket(buckets[aggregate_key(row, "acceptance")], row, "acceptance")
    for row in evidence:
        update_bucket(buckets[aggregate_key(row, "evidence")], row, "evidence")
    for row in controls:
        update_bucket(buckets[aggregate_key(row, "control")], row, "control")
    return aggregate_rows_from_buckets(buckets)
