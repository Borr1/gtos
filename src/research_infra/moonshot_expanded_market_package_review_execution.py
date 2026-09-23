"""Implementation-review execution for expanded-market package slices."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_PACKAGE_REVIEW_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_package_review_execution.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"


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
    output["expanded_market_package_review_execution_surface"] = EXPANDED_MARKET_PACKAGE_REVIEW_EXECUTION_SURFACE
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


def sha_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def group_by(rows: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[normalized(row.get(field))].append(row)
    return grouped


def one_by(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    return {normalized(row.get(field)): row for row in rows}


def package_execution_status(
    package: dict[str, Any],
    members: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    control: dict[str, Any],
    self_test: dict[str, Any],
) -> str:
    if not members:
        return "PACKAGE_REVIEW_EXECUTION_NO_MEMBERS"
    if len(members) != as_int(package.get("member_rows")):
        return "PACKAGE_REVIEW_EXECUTION_MEMBER_COUNT_MISMATCH"
    if len(evidence) != as_int(package.get("package_evidence_rows")):
        return "PACKAGE_REVIEW_EXECUTION_EVIDENCE_COUNT_MISMATCH"
    if control.get("control_status") != "PACKAGE_CONTROL_PASS":
        return "PACKAGE_REVIEW_EXECUTION_CONTROL_REPAIR"
    if self_test.get("self_test_status") != "PACKAGE_SLICE_SELF_TEST_PASS":
        return "PACKAGE_REVIEW_EXECUTION_SELF_TEST_REPAIR"
    return "PACKAGE_REVIEW_EXECUTION_PASS"


def review_decision(status: str) -> str:
    if status == "PACKAGE_REVIEW_EXECUTION_PASS":
        return "IMPLEMENT_EXPANDED_MARKET_PACKAGE_REVIEW_ARTIFACT"
    return "REDESIGN_EXPANDED_MARKET_PACKAGE_REVIEW_ARTIFACT"


def package_review_execution_rows(
    package_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    self_test_rows: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    members_by_package = group_by(member_rows, "input_package_slice_row_id")
    evidence_by_package = group_by(evidence_rows, "input_package_slice_row_id")
    controls_by_package = one_by(control_rows, "input_package_slice_row_id")
    self_tests_by_package = one_by(self_test_rows, "input_package_slice_row_id")

    artifact_rows: list[dict[str, Any]] = []
    member_execution_rows: list[dict[str, Any]] = []
    evidence_execution_rows: list[dict[str, Any]] = []
    redesign_execution_rows: list[dict[str, Any]] = []
    control_execution_rows: list[dict[str, Any]] = []

    artifact_id_by_package: dict[str, str] = {}
    for package in sorted(package_rows, key=lambda row: normalized(row.get("package_slice_row_id"))):
        package_id = normalized(package.get("package_slice_row_id"))
        members = members_by_package.get(package_id, [])
        evidence = evidence_by_package.get(package_id, [])
        control = controls_by_package.get(package_id, {})
        self_test = self_tests_by_package.get(package_id, {})
        status = package_execution_status(package, members, evidence, control, self_test)
        artifact_id = f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-REVIEW-ARTIFACT-{len(artifact_rows) + 1:06d}"
        artifact_id_by_package[package_id] = artifact_id
        expression_payload = {
            "package": package_id,
            "expression": package.get("branch_local_package_expression"),
            "source_hashes": package.get("source_file_sha256_values"),
        }
        artifact_rows.append(
            boundary_row(
                {
                    "package_review_artifact_row_id": artifact_id,
                    "input_package_slice_row_id": package_id,
                    "package_key_sha256": package.get("package_key_sha256"),
                    "symbol": package.get("symbol"),
                    "market_timeframe": package.get("market_timeframe"),
                    "route_session": package.get("route_session"),
                    "horizon_id": package.get("horizon_id"),
                    "source_component": package.get("source_component"),
                    "selected_side": package.get("selected_side"),
                    "branch_local_package_expression": package.get("branch_local_package_expression"),
                    "package_artifact_expression_sha256": sha_payload(expression_payload),
                    "member_rows_expected": package.get("member_rows"),
                    "member_rows_executed": len(members),
                    "evidence_rows_expected": package.get("package_evidence_rows"),
                    "evidence_rows_executed": len(evidence),
                    "source_path_count": package.get("source_path_count"),
                    "source_file_sha256_count": package.get("source_file_sha256_count"),
                    "source_paths": package.get("source_paths"),
                    "source_file_sha256_values": package.get("source_file_sha256_values"),
                    "average_selected_intrabar_cost_adjusted_simulated_r": package.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "average_recomputed_selected_intrabar_cost_adjusted_simulated_r": package.get(
                        "average_recomputed_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "average_final_review_score": package.get("average_final_review_score"),
                    "min_final_review_score": package.get("min_final_review_score"),
                    "max_final_review_score": package.get("max_final_review_score"),
                    "average_max_capacity_utilization": package.get("average_max_capacity_utilization"),
                    "evidence_effective_n_sum": package.get("evidence_effective_n_sum"),
                    "same_scope_redesign_rows": package.get("same_scope_redesign_rows"),
                    "self_test_status": self_test.get("self_test_status"),
                    "control_status": control.get("control_status"),
                    "package_review_execution_status": status,
                    "keep_kill_redesign_implement_decision": review_decision(status),
                    "follow_inverse_default_off_avoid_class": "follow"
                    if status == "PACKAGE_REVIEW_EXECUTION_PASS"
                    else "redesign",
                }
            )
        )
        control_execution_rows.append(
            boundary_row(
                {
                    "package_review_control_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-REVIEW-CONTROL-{len(control_execution_rows) + 1:06d}"
                    ),
                    "input_package_slice_row_id": package_id,
                    "input_package_control_row_id": control.get("package_control_row_id"),
                    "input_package_self_test_row_id": self_test.get("package_self_test_row_id"),
                    "input_package_review_artifact_row_id": artifact_id,
                    "positive_member_rows": self_test.get("positive_member_rows"),
                    "positive_package_match_rows": self_test.get("positive_package_match_rows"),
                    "same_scope_redesign_rows": control.get("same_scope_redesign_rows"),
                    "package_expression_rejected_redesign_rows": control.get(
                        "package_expression_rejected_redesign_rows"
                    ),
                    "package_expression_leaked_redesign_rows": control.get(
                        "package_expression_leaked_redesign_rows"
                    ),
                    "control_execution_status": "PACKAGE_REVIEW_CONTROL_PASS"
                    if status == "PACKAGE_REVIEW_EXECUTION_PASS"
                    else "PACKAGE_REVIEW_CONTROL_REPAIR",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_REVIEW_CONTROL"
                    if status == "PACKAGE_REVIEW_EXECUTION_PASS"
                    else "REDESIGN_EXPANDED_MARKET_PACKAGE_REVIEW_CONTROL",
                }
            )
        )
        for member in sorted(members, key=lambda row: normalized(row.get("package_member_row_id"))):
            member_execution_rows.append(
                boundary_row(
                    {
                        "package_review_member_execution_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-REVIEW-MEMBER-{len(member_execution_rows) + 1:07d}"
                        ),
                        "input_package_review_artifact_row_id": artifact_id,
                        "input_package_slice_row_id": package_id,
                        "input_package_member_row_id": member.get("package_member_row_id"),
                        "input_final_review_row_id": member.get("input_final_review_row_id"),
                        "input_deconcentration_row_id": member.get("input_deconcentration_row_id"),
                        "symbol": member.get("symbol"),
                        "source_symbol": member.get("source_symbol"),
                        "market_timeframe": member.get("market_timeframe"),
                        "route_session": member.get("route_session"),
                        "horizon_id": member.get("horizon_id"),
                        "source_component": member.get("source_component"),
                        "source_path": member.get("source_path"),
                        "source_file_sha256": member.get("source_file_sha256"),
                        "selected_side": member.get("selected_side"),
                        "artifact_function_name": member.get("artifact_function_name"),
                        "artifact_scope_sha256": member.get("artifact_scope_sha256"),
                        "final_review_score": member.get("final_review_score"),
                        "row_average_selected_intrabar_cost_adjusted_simulated_r": member.get(
                            "row_average_selected_intrabar_cost_adjusted_simulated_r"
                        ),
                        "package_review_member_execution_status": "PACKAGE_REVIEW_MEMBER_EXECUTION_PASS"
                        if status == "PACKAGE_REVIEW_EXECUTION_PASS"
                        else "PACKAGE_REVIEW_MEMBER_EXECUTION_REPAIR",
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_REVIEW_MEMBER"
                        if status == "PACKAGE_REVIEW_EXECUTION_PASS"
                        else "REDESIGN_EXPANDED_MARKET_PACKAGE_REVIEW_MEMBER",
                        "follow_inverse_default_off_avoid_class": "follow"
                        if status == "PACKAGE_REVIEW_EXECUTION_PASS"
                        else "redesign",
                    }
                )
            )
        for evidence in sorted(evidence, key=lambda row: normalized(row.get("package_evidence_row_id"))):
            evidence_execution_rows.append(
                boundary_row(
                    {
                        "package_review_evidence_execution_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-REVIEW-EVIDENCE-{len(evidence_execution_rows) + 1:08d}"
                        ),
                        "input_package_review_artifact_row_id": artifact_id,
                        "input_package_slice_row_id": package_id,
                        "input_package_evidence_row_id": evidence.get("package_evidence_row_id"),
                        "input_final_review_row_id": evidence.get("input_final_review_row_id"),
                        "input_final_review_evidence_row_id": evidence.get("input_final_review_evidence_row_id"),
                        "symbol": evidence.get("symbol"),
                        "source_symbol": evidence.get("source_symbol"),
                        "market_timeframe": evidence.get("market_timeframe"),
                        "route_session": evidence.get("route_session"),
                        "horizon_id": evidence.get("horizon_id"),
                        "source_component": evidence.get("source_component"),
                        "source_path": evidence.get("source_path"),
                        "source_file_sha256": evidence.get("source_file_sha256"),
                        "selected_side": evidence.get("selected_side"),
                        "selected_intrabar_cost_adjusted_simulated_r": evidence.get(
                            "selected_intrabar_cost_adjusted_simulated_r"
                        ),
                        "selected_minus_rejected_intrabar_cost_adjusted_r": evidence.get(
                            "selected_minus_rejected_intrabar_cost_adjusted_r"
                        ),
                        "effective_n": evidence.get("effective_n"),
                        "package_review_evidence_execution_status": "PACKAGE_REVIEW_EVIDENCE_EXECUTION_PASS"
                        if status == "PACKAGE_REVIEW_EXECUTION_PASS"
                        else "PACKAGE_REVIEW_EVIDENCE_EXECUTION_REPAIR",
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_REVIEW_EVIDENCE"
                        if status == "PACKAGE_REVIEW_EXECUTION_PASS"
                        else "REDESIGN_EXPANDED_MARKET_PACKAGE_REVIEW_EVIDENCE",
                    }
                )
            )

    for row in sorted(redesign_rows, key=lambda item: normalized(item.get("package_redesign_carry_row_id"))):
        redesign_execution_rows.append(
            boundary_row(
                {
                    "package_review_redesign_execution_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-REVIEW-REDESIGN-{len(redesign_execution_rows) + 1:06d}"
                    ),
                    "input_package_redesign_carry_row_id": row.get("package_redesign_carry_row_id"),
                    "input_final_review_row_id": row.get("input_final_review_row_id"),
                    "input_deconcentration_row_id": row.get("input_deconcentration_row_id"),
                    "symbol": row.get("symbol"),
                    "source_symbol": row.get("source_symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "selected_side": row.get("selected_side"),
                    "capacity_blocking_dimensions": row.get("capacity_blocking_dimensions") or [],
                    "final_review_score": row.get("final_review_score"),
                    "final_review_evidence_rows": row.get("final_review_evidence_rows"),
                    "package_review_redesign_execution_status": "PACKAGE_REVIEW_REDESIGN_PRESERVED",
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_PACKAGE_REVIEW_CAPACITY_PRESERVED",
                    "follow_inverse_default_off_avoid_class": "redesign",
                }
            )
        )

    for evidence in sorted(
        [row for row in evidence_rows if not normalized(row.get("input_package_slice_row_id"))],
        key=lambda row: normalized(row.get("package_evidence_row_id")),
    ):
        evidence_execution_rows.append(
            boundary_row(
                {
                    "package_review_evidence_execution_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-REVIEW-EVIDENCE-{len(evidence_execution_rows) + 1:08d}"
                    ),
                    "input_package_review_artifact_row_id": None,
                    "input_package_slice_row_id": None,
                    "input_package_evidence_row_id": evidence.get("package_evidence_row_id"),
                    "input_final_review_row_id": evidence.get("input_final_review_row_id"),
                    "input_final_review_evidence_row_id": evidence.get("input_final_review_evidence_row_id"),
                    "symbol": evidence.get("symbol"),
                    "source_symbol": evidence.get("source_symbol"),
                    "market_timeframe": evidence.get("market_timeframe"),
                    "route_session": evidence.get("route_session"),
                    "horizon_id": evidence.get("horizon_id"),
                    "source_component": evidence.get("source_component"),
                    "source_path": evidence.get("source_path"),
                    "source_file_sha256": evidence.get("source_file_sha256"),
                    "selected_side": evidence.get("selected_side"),
                    "selected_intrabar_cost_adjusted_simulated_r": evidence.get(
                        "selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "selected_minus_rejected_intrabar_cost_adjusted_r": evidence.get(
                        "selected_minus_rejected_intrabar_cost_adjusted_r"
                    ),
                    "effective_n": evidence.get("effective_n"),
                    "package_review_evidence_execution_status": "PACKAGE_REVIEW_EVIDENCE_PRESERVED",
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_PACKAGE_REVIEW_EVIDENCE_PRESERVED",
                }
            )
        )

    return artifact_rows, member_execution_rows, evidence_execution_rows, redesign_execution_rows, control_execution_rows


def aggregate_review_artifact_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("source_component")),
                normalized(row.get("selected_side")),
            )
        ].append(row)
    total_members = sum(as_int(row.get("member_rows_executed")) for row in rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        member_count = sum(as_int(row.get("member_rows_executed")) for row in members)
        output.append(
            boundary_row(
                {
                    "package_review_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-REVIEW-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "source_component": key[1],
                    "selected_side": key[2],
                    "artifact_rows": len(members),
                    "member_rows": member_count,
                    "evidence_rows": sum(as_int(row.get("evidence_rows_executed")) for row in members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "average_selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "average_final_review_score": rounded(average(numeric_values(members, "average_final_review_score"))),
                    "average_max_capacity_utilization": rounded(
                        average(numeric_values(members, "average_max_capacity_utilization"))
                    ),
                    "concentration_share_of_package_review_members": rounded(member_count / total_members),
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_REVIEW_AGGREGATE",
                }
            )
        )
    return output


def system_review_execution_rows(
    artifact_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_package_rows: int,
    input_member_rows: int,
    input_evidence_rows: int,
    input_redesign_rows: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "package_review_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-PACKAGE-REVIEW-SYSTEM-0001",
                "input_package_slice_rows": input_package_rows,
                "input_package_member_rows": input_member_rows,
                "input_package_evidence_rows": input_evidence_rows,
                "input_package_redesign_carry_rows": input_redesign_rows,
                "package_review_artifact_rows": len(artifact_rows),
                "package_review_member_execution_rows": len(member_rows),
                "package_review_evidence_execution_rows": len(evidence_rows),
                "package_review_redesign_execution_rows": len(redesign_rows),
                "package_review_control_rows": len(control_rows),
                "aggregate_rows": len(aggregate_rows),
                "artifact_pass_rows": sum(
                    1 for row in artifact_rows if row.get("package_review_execution_status") == "PACKAGE_REVIEW_EXECUTION_PASS"
                ),
                "member_pass_rows": sum(
                    1
                    for row in member_rows
                    if row.get("package_review_member_execution_status") == "PACKAGE_REVIEW_MEMBER_EXECUTION_PASS"
                ),
                "evidence_pass_rows": sum(
                    1
                    for row in evidence_rows
                    if row.get("package_review_evidence_execution_status") == "PACKAGE_REVIEW_EVIDENCE_EXECUTION_PASS"
                ),
                "decision_counts": dict(
                    sorted(
                        Counter(
                            [row.get("keep_kill_redesign_implement_decision") for row in artifact_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in redesign_rows]
                        ).items()
                    )
                ),
            }
        )
    ]
