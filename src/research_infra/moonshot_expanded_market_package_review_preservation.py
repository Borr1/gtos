"""Execution preservation for expanded-market package-review artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_package_review_preservation.py"
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
    output["expanded_market_package_review_preservation_surface"] = (
        EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION_SURFACE
    )
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


def implementation_payload(artifact: dict[str, Any], members: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "artifact": artifact.get("package_review_artifact_row_id"),
        "package_key_sha256": artifact.get("package_key_sha256"),
        "expression_sha256": artifact.get("package_artifact_expression_sha256"),
        "source_file_sha256_values": artifact.get("source_file_sha256_values"),
        "member_scope_hashes": sorted({normalized(row.get("artifact_scope_sha256")) for row in members}),
    }


def candidate_status(artifact: dict[str, Any], members: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> str:
    if artifact.get("package_review_execution_status") != "PACKAGE_REVIEW_EXECUTION_PASS":
        return "PACKAGE_REVIEW_PRESERVATION_ARTIFACT_REPAIR"
    if len(members) != as_int(artifact.get("member_rows_executed")):
        return "PACKAGE_REVIEW_PRESERVATION_MEMBER_MISMATCH"
    if len(evidence) != as_int(artifact.get("evidence_rows_executed")):
        return "PACKAGE_REVIEW_PRESERVATION_EVIDENCE_MISMATCH"
    return "PACKAGE_REVIEW_PRESERVATION_READY"


def preservation_decision(status: str) -> str:
    if status == "PACKAGE_REVIEW_PRESERVATION_READY":
        return "IMPLEMENT_EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION"
    return "REDESIGN_EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION"


def package_review_preservation_rows(
    artifact_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    members_by_artifact = group_by(member_rows, "input_package_review_artifact_row_id")
    evidence_by_artifact = group_by(evidence_rows, "input_package_review_artifact_row_id")
    candidate_rows: list[dict[str, Any]] = []
    preserved_member_rows: list[dict[str, Any]] = []
    preserved_evidence_rows: list[dict[str, Any]] = []
    preserved_redesign_rows: list[dict[str, Any]] = []
    self_test_rows: list[dict[str, Any]] = []

    for artifact in sorted(artifact_rows, key=lambda row: normalized(row.get("package_review_artifact_row_id"))):
        artifact_id = normalized(artifact.get("package_review_artifact_row_id"))
        members = members_by_artifact.get(artifact_id, [])
        evidence = evidence_by_artifact.get(artifact_id, [])
        status = candidate_status(artifact, members, evidence)
        candidate_id = f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-PRESERVATION-CANDIDATE-{len(candidate_rows) + 1:06d}"
        payload = implementation_payload(artifact, members)
        candidate_rows.append(
            boundary_row(
                {
                    "package_preservation_candidate_row_id": candidate_id,
                    "input_package_review_artifact_row_id": artifact.get("package_review_artifact_row_id"),
                    "input_package_slice_row_id": artifact.get("input_package_slice_row_id"),
                    "package_key_sha256": artifact.get("package_key_sha256"),
                    "symbol": artifact.get("symbol"),
                    "market_timeframe": artifact.get("market_timeframe"),
                    "route_session": artifact.get("route_session"),
                    "horizon_id": artifact.get("horizon_id"),
                    "source_component": artifact.get("source_component"),
                    "selected_side": artifact.get("selected_side"),
                    "branch_local_package_expression": artifact.get("branch_local_package_expression"),
                    "package_artifact_expression_sha256": artifact.get("package_artifact_expression_sha256"),
                    "implementation_payload_sha256": sha_payload(payload),
                    "member_rows_expected": artifact.get("member_rows_executed"),
                    "member_rows_preserved": len(members),
                    "evidence_rows_expected": artifact.get("evidence_rows_executed"),
                    "evidence_rows_preserved": len(evidence),
                    "source_path_count": artifact.get("source_path_count"),
                    "source_file_sha256_count": artifact.get("source_file_sha256_count"),
                    "source_paths": artifact.get("source_paths"),
                    "source_file_sha256_values": artifact.get("source_file_sha256_values"),
                    "average_selected_intrabar_cost_adjusted_simulated_r": artifact.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "average_recomputed_selected_intrabar_cost_adjusted_simulated_r": artifact.get(
                        "average_recomputed_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "average_final_review_score": artifact.get("average_final_review_score"),
                    "min_final_review_score": artifact.get("min_final_review_score"),
                    "max_final_review_score": artifact.get("max_final_review_score"),
                    "average_max_capacity_utilization": artifact.get("average_max_capacity_utilization"),
                    "evidence_effective_n_sum": artifact.get("evidence_effective_n_sum"),
                    "same_scope_redesign_rows": artifact.get("same_scope_redesign_rows"),
                    "preservation_status": status,
                    "keep_kill_redesign_implement_decision": preservation_decision(status),
                    "follow_inverse_default_off_avoid_class": "follow"
                    if status == "PACKAGE_REVIEW_PRESERVATION_READY"
                    else "redesign",
                }
            )
        )
        self_test_rows.append(
            boundary_row(
                {
                    "package_preservation_self_test_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-PRESERVATION-SELF-TEST-{len(self_test_rows) + 1:06d}"
                    ),
                    "input_package_preservation_candidate_row_id": candidate_id,
                    "input_package_review_artifact_row_id": artifact_id,
                    "member_rows_expected": artifact.get("member_rows_executed"),
                    "member_rows_preserved": len(members),
                    "evidence_rows_expected": artifact.get("evidence_rows_executed"),
                    "evidence_rows_preserved": len(evidence),
                    "artifact_execution_status": artifact.get("package_review_execution_status"),
                    "self_test_status": "PACKAGE_REVIEW_PRESERVATION_SELF_TEST_PASS"
                    if status == "PACKAGE_REVIEW_PRESERVATION_READY"
                    else "PACKAGE_REVIEW_PRESERVATION_SELF_TEST_REPAIR",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_PRESERVATION_SELF_TEST"
                    if status == "PACKAGE_REVIEW_PRESERVATION_READY"
                    else "REDESIGN_EXPANDED_MARKET_PACKAGE_PRESERVATION_SELF_TEST",
                }
            )
        )
        for member in sorted(members, key=lambda row: normalized(row.get("package_review_member_execution_row_id"))):
            preserved_member_rows.append(
                boundary_row(
                    {
                        "package_preservation_member_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-PRESERVATION-MEMBER-{len(preserved_member_rows) + 1:07d}"
                        ),
                        "input_package_preservation_candidate_row_id": candidate_id,
                        "input_package_review_artifact_row_id": artifact_id,
                        "input_package_review_member_execution_row_id": member.get(
                            "package_review_member_execution_row_id"
                        ),
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
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_PRESERVATION_MEMBER"
                        if status == "PACKAGE_REVIEW_PRESERVATION_READY"
                        else "REDESIGN_EXPANDED_MARKET_PACKAGE_PRESERVATION_MEMBER",
                        "follow_inverse_default_off_avoid_class": "follow"
                        if status == "PACKAGE_REVIEW_PRESERVATION_READY"
                        else "redesign",
                    }
                )
            )
        for evidence in sorted(evidence, key=lambda row: normalized(row.get("package_review_evidence_execution_row_id"))):
            preserved_evidence_rows.append(
                boundary_row(
                    {
                        "package_preservation_evidence_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-PRESERVATION-EVIDENCE-{len(preserved_evidence_rows) + 1:08d}"
                        ),
                        "input_package_preservation_candidate_row_id": candidate_id,
                        "input_package_review_artifact_row_id": artifact_id,
                        "input_package_review_evidence_execution_row_id": evidence.get(
                            "package_review_evidence_execution_row_id"
                        ),
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
                        "package_review_evidence_execution_status": evidence.get(
                            "package_review_evidence_execution_status"
                        ),
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_PRESERVATION_EVIDENCE"
                        if status == "PACKAGE_REVIEW_PRESERVATION_READY"
                        else "REDESIGN_EXPANDED_MARKET_PACKAGE_PRESERVATION_EVIDENCE",
                    }
                )
            )

    for row in sorted(redesign_rows, key=lambda item: normalized(item.get("package_review_redesign_execution_row_id"))):
        preserved_redesign_rows.append(
            boundary_row(
                {
                    "package_preservation_redesign_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-PRESERVATION-REDESIGN-{len(preserved_redesign_rows) + 1:06d}"
                    ),
                    "input_package_review_redesign_execution_row_id": row.get(
                        "package_review_redesign_execution_row_id"
                    ),
                    "input_package_redesign_carry_row_id": row.get("input_package_redesign_carry_row_id"),
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
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_PACKAGE_PRESERVATION_CAPACITY",
                    "follow_inverse_default_off_avoid_class": "redesign",
                }
            )
        )

    for evidence in sorted(
        [row for row in evidence_rows if not normalized(row.get("input_package_review_artifact_row_id"))],
        key=lambda row: normalized(row.get("package_review_evidence_execution_row_id")),
    ):
        preserved_evidence_rows.append(
            boundary_row(
                {
                    "package_preservation_evidence_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-PRESERVATION-EVIDENCE-{len(preserved_evidence_rows) + 1:08d}"
                    ),
                    "input_package_preservation_candidate_row_id": None,
                    "input_package_review_artifact_row_id": None,
                    "input_package_review_evidence_execution_row_id": evidence.get(
                        "package_review_evidence_execution_row_id"
                    ),
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
                    "package_review_evidence_execution_status": evidence.get(
                        "package_review_evidence_execution_status"
                    ),
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_PACKAGE_PRESERVATION_EVIDENCE",
                }
            )
        )

    return candidate_rows, preserved_member_rows, preserved_evidence_rows, preserved_redesign_rows, self_test_rows


def aggregate_preservation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("source_component")),
                normalized(row.get("selected_side")),
            )
        ].append(row)
    total_members = sum(as_int(row.get("member_rows_preserved")) for row in rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        member_count = sum(as_int(row.get("member_rows_preserved")) for row in members)
        output.append(
            boundary_row(
                {
                    "package_preservation_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-PACKAGE-PRESERVATION-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "source_component": key[1],
                    "selected_side": key[2],
                    "candidate_rows": len(members),
                    "member_rows": member_count,
                    "evidence_rows": sum(as_int(row.get("evidence_rows_preserved")) for row in members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "average_selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "average_final_review_score": rounded(average(numeric_values(members, "average_final_review_score"))),
                    "average_max_capacity_utilization": rounded(
                        average(numeric_values(members, "average_max_capacity_utilization"))
                    ),
                    "concentration_share_of_preserved_members": rounded(member_count / total_members),
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_PACKAGE_PRESERVATION_AGGREGATE",
                }
            )
        )
    return output


def system_preservation_rows(
    candidate_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    self_test_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_artifact_rows: int,
    input_member_rows: int,
    input_evidence_rows: int,
    input_redesign_rows: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "package_preservation_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-PACKAGE-PRESERVATION-SYSTEM-0001",
                "input_package_review_artifact_rows": input_artifact_rows,
                "input_package_review_member_execution_rows": input_member_rows,
                "input_package_review_evidence_execution_rows": input_evidence_rows,
                "input_package_review_redesign_execution_rows": input_redesign_rows,
                "package_preservation_candidate_rows": len(candidate_rows),
                "package_preservation_member_rows": len(member_rows),
                "package_preservation_evidence_rows": len(evidence_rows),
                "package_preservation_redesign_rows": len(redesign_rows),
                "package_preservation_self_test_rows": len(self_test_rows),
                "aggregate_rows": len(aggregate_rows),
                "ready_candidate_rows": sum(
                    1 for row in candidate_rows if row.get("preservation_status") == "PACKAGE_REVIEW_PRESERVATION_READY"
                ),
                "self_test_pass_rows": sum(
                    1
                    for row in self_test_rows
                    if row.get("self_test_status") == "PACKAGE_REVIEW_PRESERVATION_SELF_TEST_PASS"
                ),
                "decision_counts": dict(
                    sorted(
                        Counter(
                            [row.get("keep_kill_redesign_implement_decision") for row in candidate_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in redesign_rows]
                        ).items()
                    )
                ),
            }
        )
    ]
