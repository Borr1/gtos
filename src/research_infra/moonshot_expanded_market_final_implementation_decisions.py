"""Final branch-local implementation decisions for expanded-market packages."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS_SURFACE = (
    "src/research_infra/moonshot_expanded_market_final_implementation_decisions.py"
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
    output["expanded_market_final_implementation_decisions_surface"] = (
        EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS_SURFACE
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


def decision_status(
    candidate: dict[str, Any],
    members: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> str:
    if candidate.get("preservation_status") != "PACKAGE_REVIEW_PRESERVATION_READY":
        return "FINAL_IMPLEMENTATION_DECISION_PRESERVATION_REPAIR"
    if len(members) != as_int(candidate.get("member_rows_preserved")):
        return "FINAL_IMPLEMENTATION_DECISION_MEMBER_MISMATCH"
    if len(evidence) != as_int(candidate.get("evidence_rows_preserved")):
        return "FINAL_IMPLEMENTATION_DECISION_EVIDENCE_MISMATCH"
    selected_r = as_float(candidate.get("average_selected_intrabar_cost_adjusted_simulated_r"))
    if selected_r is None:
        return "FINAL_IMPLEMENTATION_DECISION_MISSING_SIMULATED_R"
    if selected_r <= 0:
        return "FINAL_IMPLEMENTATION_DECISION_NONPOSITIVE_SIMULATED_R"
    effective_n_sum = as_float(candidate.get("evidence_effective_n_sum"))
    if effective_n_sum is None or effective_n_sum <= 0:
        return "FINAL_IMPLEMENTATION_DECISION_MISSING_EFFECTIVE_N"
    return "FINAL_IMPLEMENTATION_DECISION_READY"


def final_decision(status: str) -> str:
    if status == "FINAL_IMPLEMENTATION_DECISION_READY":
        return "IMPLEMENT_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_DECISION"
    return "REDESIGN_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_DECISION"


def final_implementation_decision_rows(
    candidate_rows: list[dict[str, Any]],
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
    members_by_candidate = group_by(member_rows, "input_package_preservation_candidate_row_id")
    evidence_by_candidate = group_by(evidence_rows, "input_package_preservation_candidate_row_id")
    decision_rows: list[dict[str, Any]] = []
    final_member_rows: list[dict[str, Any]] = []
    final_evidence_rows: list[dict[str, Any]] = []
    final_redesign_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    decision_by_candidate: dict[str, tuple[str, str]] = {}

    for candidate in sorted(candidate_rows, key=lambda row: normalized(row.get("package_preservation_candidate_row_id"))):
        candidate_id = normalized(candidate.get("package_preservation_candidate_row_id"))
        members = members_by_candidate.get(candidate_id, [])
        evidence = evidence_by_candidate.get(candidate_id, [])
        status = decision_status(candidate, members, evidence)
        decision_id = f"OHLC-GTOS-EXPANDED-MARKET-FINAL-IMPLEMENTATION-DECISION-{len(decision_rows) + 1:06d}"
        decision_by_candidate[candidate_id] = (decision_id, status)
        tied_effective_n = sum(as_int(row.get("effective_n")) for row in evidence)
        payload = {
            "candidate": candidate_id,
            "package_key_sha256": candidate.get("package_key_sha256"),
            "expression_sha256": candidate.get("package_artifact_expression_sha256"),
            "source_file_sha256_values": candidate.get("source_file_sha256_values"),
            "member_row_ids": sorted(normalized(row.get("package_preservation_member_row_id")) for row in members),
            "evidence_row_ids": sorted(normalized(row.get("package_preservation_evidence_row_id")) for row in evidence),
            "status": status,
        }
        decision_rows.append(
            boundary_row(
                {
                    "final_implementation_decision_row_id": decision_id,
                    "input_package_preservation_candidate_row_id": candidate_id,
                    "input_package_review_artifact_row_id": candidate.get("input_package_review_artifact_row_id"),
                    "input_package_slice_row_id": candidate.get("input_package_slice_row_id"),
                    "package_key_sha256": candidate.get("package_key_sha256"),
                    "symbol": candidate.get("symbol"),
                    "market_timeframe": candidate.get("market_timeframe"),
                    "route_session": candidate.get("route_session"),
                    "horizon_id": candidate.get("horizon_id"),
                    "source_component": candidate.get("source_component"),
                    "selected_side": candidate.get("selected_side"),
                    "branch_local_package_expression": candidate.get("branch_local_package_expression"),
                    "package_artifact_expression_sha256": candidate.get("package_artifact_expression_sha256"),
                    "final_decision_payload_sha256": sha_payload(payload),
                    "member_rows_expected": candidate.get("member_rows_preserved"),
                    "member_rows_decided": len(members),
                    "evidence_rows_expected": candidate.get("evidence_rows_preserved"),
                    "evidence_rows_decided": len(evidence),
                    "source_path_count": candidate.get("source_path_count"),
                    "source_file_sha256_count": candidate.get("source_file_sha256_count"),
                    "source_paths": candidate.get("source_paths"),
                    "source_file_sha256_values": candidate.get("source_file_sha256_values"),
                    "average_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "average_recomputed_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                        "average_recomputed_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "average_final_review_score": candidate.get("average_final_review_score"),
                    "min_final_review_score": candidate.get("min_final_review_score"),
                    "max_final_review_score": candidate.get("max_final_review_score"),
                    "average_max_capacity_utilization": candidate.get("average_max_capacity_utilization"),
                    "evidence_effective_n_sum": candidate.get("evidence_effective_n_sum"),
                    "recomputed_evidence_effective_n_sum": tied_effective_n,
                    "same_scope_redesign_rows": candidate.get("same_scope_redesign_rows"),
                    "final_implementation_decision_status": status,
                    "keep_kill_redesign_implement_decision": final_decision(status),
                    "follow_inverse_default_off_avoid_class": "follow"
                    if status == "FINAL_IMPLEMENTATION_DECISION_READY"
                    else "redesign",
                }
            )
        )
        control_rows.append(
            boundary_row(
                {
                    "final_implementation_control_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-FINAL-IMPLEMENTATION-CONTROL-{len(control_rows) + 1:06d}"
                    ),
                    "input_final_implementation_decision_row_id": decision_id,
                    "input_package_preservation_candidate_row_id": candidate_id,
                    "member_rows_expected": candidate.get("member_rows_preserved"),
                    "member_rows_decided": len(members),
                    "evidence_rows_expected": candidate.get("evidence_rows_preserved"),
                    "evidence_rows_decided": len(evidence),
                    "selected_r_positive": (as_float(candidate.get("average_selected_intrabar_cost_adjusted_simulated_r")) or 0) > 0,
                    "effective_n_positive": (as_float(candidate.get("evidence_effective_n_sum")) or 0) > 0,
                    "final_implementation_decision_status": status,
                    "control_status": "FINAL_IMPLEMENTATION_DECISION_CONTROL_PASS"
                    if status == "FINAL_IMPLEMENTATION_DECISION_READY"
                    else "FINAL_IMPLEMENTATION_DECISION_CONTROL_REPAIR",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_FINAL_DECISION_CONTROL"
                    if status == "FINAL_IMPLEMENTATION_DECISION_READY"
                    else "REDESIGN_EXPANDED_MARKET_FINAL_DECISION_CONTROL",
                }
            )
        )
        for member in sorted(members, key=lambda row: normalized(row.get("package_preservation_member_row_id"))):
            final_member_rows.append(
                boundary_row(
                    {
                        "final_implementation_member_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-FINAL-IMPLEMENTATION-MEMBER-{len(final_member_rows) + 1:07d}"
                        ),
                        "input_final_implementation_decision_row_id": decision_id,
                        "input_package_preservation_candidate_row_id": candidate_id,
                        "input_package_preservation_member_row_id": member.get("package_preservation_member_row_id"),
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
                        "final_implementation_member_status": "FINAL_IMPLEMENTATION_MEMBER_DECISION_PASS"
                        if status == "FINAL_IMPLEMENTATION_DECISION_READY"
                        else "FINAL_IMPLEMENTATION_MEMBER_DECISION_REPAIR",
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_FINAL_DECISION_MEMBER"
                        if status == "FINAL_IMPLEMENTATION_DECISION_READY"
                        else "REDESIGN_EXPANDED_MARKET_FINAL_DECISION_MEMBER",
                        "follow_inverse_default_off_avoid_class": "follow"
                        if status == "FINAL_IMPLEMENTATION_DECISION_READY"
                        else "redesign",
                    }
                )
            )

    for evidence in sorted(evidence_rows, key=lambda row: normalized(row.get("package_preservation_evidence_row_id"))):
        candidate_id = normalized(evidence.get("input_package_preservation_candidate_row_id"))
        decision_id, status = decision_by_candidate.get(candidate_id, (None, "FINAL_IMPLEMENTATION_EVIDENCE_UNPACKAGED"))
        tied = bool(decision_id)
        final_evidence_rows.append(
            boundary_row(
                {
                    "final_implementation_evidence_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-FINAL-IMPLEMENTATION-EVIDENCE-{len(final_evidence_rows) + 1:08d}"
                    ),
                    "input_final_implementation_decision_row_id": decision_id,
                    "input_package_preservation_candidate_row_id": evidence.get(
                        "input_package_preservation_candidate_row_id"
                    ),
                    "input_package_preservation_evidence_row_id": evidence.get("package_preservation_evidence_row_id"),
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
                    "source_evidence_status": evidence.get("package_review_evidence_execution_status"),
                    "final_implementation_evidence_status": "FINAL_IMPLEMENTATION_EVIDENCE_DECISION_PASS"
                    if tied and status == "FINAL_IMPLEMENTATION_DECISION_READY"
                    else "FINAL_IMPLEMENTATION_EVIDENCE_UNPACKAGED",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_FINAL_DECISION_EVIDENCE"
                    if tied and status == "FINAL_IMPLEMENTATION_DECISION_READY"
                    else "REDESIGN_EXPANDED_MARKET_FINAL_DECISION_UNPACKAGED_EVIDENCE",
                    "follow_inverse_default_off_avoid_class": "follow"
                    if tied and status == "FINAL_IMPLEMENTATION_DECISION_READY"
                    else "redesign",
                }
            )
        )

    for row in sorted(redesign_rows, key=lambda item: normalized(item.get("package_preservation_redesign_row_id"))):
        final_redesign_rows.append(
            boundary_row(
                {
                    "final_implementation_redesign_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-FINAL-IMPLEMENTATION-REDESIGN-{len(final_redesign_rows) + 1:06d}"
                    ),
                    "input_package_preservation_redesign_row_id": row.get("package_preservation_redesign_row_id"),
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
                    "final_implementation_redesign_status": "FINAL_IMPLEMENTATION_REDESIGN_CAPACITY_PRESERVED",
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_CAPACITY",
                    "follow_inverse_default_off_avoid_class": "redesign",
                }
            )
        )

    return decision_rows, final_member_rows, final_evidence_rows, final_redesign_rows, control_rows


def aggregate_final_implementation_decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("source_component")),
                normalized(row.get("selected_side")),
            )
        ].append(row)
    total_members = sum(as_int(row.get("member_rows_decided")) for row in rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        member_count = sum(as_int(row.get("member_rows_decided")) for row in members)
        output.append(
            boundary_row(
                {
                    "final_implementation_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-FINAL-IMPLEMENTATION-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "source_component": key[1],
                    "selected_side": key[2],
                    "decision_rows": len(members),
                    "member_rows": member_count,
                    "evidence_rows": sum(as_int(row.get("evidence_rows_decided")) for row in members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "average_selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "average_final_review_score": rounded(average(numeric_values(members, "average_final_review_score"))),
                    "average_max_capacity_utilization": rounded(
                        average(numeric_values(members, "average_max_capacity_utilization"))
                    ),
                    "evidence_effective_n_sum": sum(as_int(row.get("recomputed_evidence_effective_n_sum")) for row in members),
                    "concentration_share_of_final_members": rounded(member_count / total_members),
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_FINAL_DECISION_AGGREGATE",
                }
            )
        )
    return output


def system_final_implementation_decision_rows(
    decision_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_candidate_rows: int,
    input_member_rows: int,
    input_evidence_rows: int,
    input_redesign_rows: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "final_implementation_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-FINAL-IMPLEMENTATION-SYSTEM-0001",
                "input_package_preservation_candidate_rows": input_candidate_rows,
                "input_package_preservation_member_rows": input_member_rows,
                "input_package_preservation_evidence_rows": input_evidence_rows,
                "input_package_preservation_redesign_rows": input_redesign_rows,
                "final_implementation_decision_rows": len(decision_rows),
                "final_implementation_member_rows": len(member_rows),
                "final_implementation_evidence_rows": len(evidence_rows),
                "final_implementation_redesign_rows": len(redesign_rows),
                "final_implementation_control_rows": len(control_rows),
                "aggregate_rows": len(aggregate_rows),
                "ready_final_implementation_decision_rows": sum(
                    1
                    for row in decision_rows
                    if row.get("final_implementation_decision_status") == "FINAL_IMPLEMENTATION_DECISION_READY"
                ),
                "member_pass_rows": sum(
                    1
                    for row in member_rows
                    if row.get("final_implementation_member_status") == "FINAL_IMPLEMENTATION_MEMBER_DECISION_PASS"
                ),
                "evidence_pass_rows": sum(
                    1
                    for row in evidence_rows
                    if row.get("final_implementation_evidence_status") == "FINAL_IMPLEMENTATION_EVIDENCE_DECISION_PASS"
                ),
                "unpackaged_evidence_rows": sum(
                    1
                    for row in evidence_rows
                    if row.get("final_implementation_evidence_status") == "FINAL_IMPLEMENTATION_EVIDENCE_UNPACKAGED"
                ),
                "terminal_redesign_rows": len(redesign_rows),
                "control_pass_rows": sum(
                    1 for row in control_rows if row.get("control_status") == "FINAL_IMPLEMENTATION_DECISION_CONTROL_PASS"
                ),
                "decision_counts": dict(
                    sorted(
                        Counter(
                            [row.get("keep_kill_redesign_implement_decision") for row in decision_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in evidence_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in redesign_rows]
                        ).items()
                    )
                ),
            }
        )
    ]
