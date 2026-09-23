"""Final branch-local decisions for executed expanded-market repackage rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_REPACKAGE_FINAL_DECISIONS_SURFACE = (
    "src/research_infra/moonshot_expanded_market_repackage_final_decisions.py"
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
    output["expanded_market_repackage_final_decisions_surface"] = (
        EXPANDED_MARKET_REPACKAGE_FINAL_DECISIONS_SURFACE
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


def final_decision_status(execution: dict[str, Any], evidence: list[dict[str, Any]]) -> str:
    if execution.get("repackage_execution_status") != "UNPACKAGED_REPACKAGE_EXECUTION_PASS":
        return "REPACKAGE_FINAL_DECISION_EXECUTION_REPAIR"
    if execution.get("source_path_exists") is not True or execution.get("source_file_hash_match") is not True:
        return "REPACKAGE_FINAL_DECISION_SOURCE_PROOF_REPAIR"
    if len(evidence) != as_int(execution.get("candidate_evidence_rows_executed")):
        return "REPACKAGE_FINAL_DECISION_EVIDENCE_COUNT_MISMATCH"
    average_r = as_float(execution.get("average_selected_intrabar_cost_adjusted_simulated_r"))
    if average_r is None:
        return "REPACKAGE_FINAL_DECISION_MISSING_SIMULATED_R"
    if average_r <= 0:
        return "REPACKAGE_FINAL_DECISION_KILL_NONPOSITIVE_R"
    return "REPACKAGE_FINAL_DECISION_READY"


def final_decision(status: str) -> str:
    if status == "REPACKAGE_FINAL_DECISION_READY":
        return "IMPLEMENT_EXPANDED_MARKET_REPACKAGE_FINAL_DECISION"
    if status == "REPACKAGE_FINAL_DECISION_KILL_NONPOSITIVE_R":
        return "KILL_EXPANDED_MARKET_REPACKAGE_FINAL_DECISION"
    return "REDESIGN_EXPANDED_MARKET_REPACKAGE_FINAL_DECISION"


def follow_class(status: str) -> str:
    if status == "REPACKAGE_FINAL_DECISION_READY":
        return "follow"
    if status == "REPACKAGE_FINAL_DECISION_KILL_NONPOSITIVE_R":
        return "avoid"
    return "redesign"


def repackage_final_decision_rows(
    execution_rows: list[dict[str, Any]],
    repackage_evidence_rows: list[dict[str, Any]],
    existing_evidence_rows: list[dict[str, Any]],
    terminal_redesign_rows: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    evidence_by_execution = group_by(repackage_evidence_rows, "input_repackage_execution_row_id")
    decision_rows: list[dict[str, Any]] = []
    final_repackage_evidence_rows: list[dict[str, Any]] = []
    existing_evidence_carry_rows: list[dict[str, Any]] = []
    terminal_redesign_carry_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    decision_by_execution: dict[str, tuple[str, str]] = {}

    for execution in sorted(execution_rows, key=lambda row: normalized(row.get("repackage_execution_row_id"))):
        execution_id = normalized(execution.get("repackage_execution_row_id"))
        evidence = evidence_by_execution.get(execution_id, [])
        status = final_decision_status(execution, evidence)
        decision_id = f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-FINAL-DECISION-{len(decision_rows) + 1:06d}"
        decision_by_execution[execution_id] = (decision_id, status)
        payload = {
            "execution": execution_id,
            "evidence_ids": sorted(row.get("repackage_evidence_execution_row_id") for row in evidence),
            "source_path": execution.get("source_path"),
            "source_hash": execution.get("source_file_sha256"),
            "status": status,
        }
        decision_rows.append(
            boundary_row(
                {
                    "repackage_final_decision_row_id": decision_id,
                    "input_repackage_execution_row_id": execution_id,
                    "input_unpackaged_repackage_candidate_row_id": execution.get(
                        "input_unpackaged_repackage_candidate_row_id"
                    ),
                    "symbol": execution.get("symbol"),
                    "market_timeframe": execution.get("market_timeframe"),
                    "route_session": execution.get("route_session"),
                    "horizon_id": execution.get("horizon_id"),
                    "source_component": execution.get("source_component"),
                    "selected_side": execution.get("selected_side"),
                    "source_path": execution.get("source_path"),
                    "source_file_sha256": execution.get("source_file_sha256"),
                    "source_path_exists": execution.get("source_path_exists"),
                    "source_file_hash_match": execution.get("source_file_hash_match"),
                    "candidate_evidence_rows_expected": execution.get("candidate_evidence_rows_executed"),
                    "candidate_evidence_rows_decided": len(evidence),
                    "average_selected_intrabar_cost_adjusted_simulated_r": execution.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "min_selected_intrabar_cost_adjusted_simulated_r": execution.get(
                        "min_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "max_selected_intrabar_cost_adjusted_simulated_r": execution.get(
                        "max_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "effective_n_sum_decided": sum(as_int(row.get("effective_n")) for row in evidence),
                    "repackage_final_decision_payload_sha256": sha_payload(payload),
                    "repackage_final_decision_status": status,
                    "keep_kill_redesign_implement_decision": final_decision(status),
                    "follow_inverse_default_off_avoid_class": follow_class(status),
                }
            )
        )
        control_rows.append(
            boundary_row(
                {
                    "repackage_final_control_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-FINAL-CONTROL-{len(control_rows) + 1:06d}"
                    ),
                    "input_repackage_final_decision_row_id": decision_id,
                    "input_repackage_execution_row_id": execution_id,
                    "candidate_evidence_rows_expected": execution.get("candidate_evidence_rows_executed"),
                    "candidate_evidence_rows_decided": len(evidence),
                    "source_path_exists": execution.get("source_path_exists"),
                    "source_file_hash_match": execution.get("source_file_hash_match"),
                    "control_status": "REPACKAGE_FINAL_DECISION_CONTROL_PASS"
                    if status == "REPACKAGE_FINAL_DECISION_READY"
                    else "REPACKAGE_FINAL_DECISION_CONTROL_REPAIR",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_REPACKAGE_FINAL_CONTROL"
                    if status == "REPACKAGE_FINAL_DECISION_READY"
                    else "REDESIGN_EXPANDED_MARKET_REPACKAGE_FINAL_CONTROL",
                }
            )
        )

    for row in sorted(repackage_evidence_rows, key=lambda item: normalized(item.get("repackage_evidence_execution_row_id"))):
        execution_id = normalized(row.get("input_repackage_execution_row_id"))
        decision_id, status = decision_by_execution.get(execution_id, (None, "REPACKAGE_FINAL_EVIDENCE_ORPHAN"))
        final_repackage_evidence_rows.append(
            boundary_row(
                {
                    "repackage_final_evidence_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-FINAL-EVIDENCE-{len(final_repackage_evidence_rows) + 1:08d}"
                    ),
                    "input_repackage_final_decision_row_id": decision_id,
                    "input_repackage_execution_row_id": execution_id,
                    "input_repackage_evidence_execution_row_id": row.get("repackage_evidence_execution_row_id"),
                    "input_unpackaged_evidence_resolution_row_id": row.get(
                        "input_unpackaged_evidence_resolution_row_id"
                    ),
                    "input_final_implementation_evidence_row_id": row.get(
                        "input_final_implementation_evidence_row_id"
                    ),
                    "symbol": row.get("symbol"),
                    "source_symbol": row.get("source_symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "selected_side": row.get("selected_side"),
                    "selected_intrabar_cost_adjusted_simulated_r": row.get(
                        "selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "effective_n": row.get("effective_n"),
                    "repackage_final_evidence_status": "REPACKAGE_FINAL_EVIDENCE_DECISION_PASS"
                    if status == "REPACKAGE_FINAL_DECISION_READY"
                    else "REPACKAGE_FINAL_EVIDENCE_DECISION_REPAIR",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_REPACKAGE_FINAL_EVIDENCE"
                    if status == "REPACKAGE_FINAL_DECISION_READY"
                    else "REDESIGN_EXPANDED_MARKET_REPACKAGE_FINAL_EVIDENCE",
                    "follow_inverse_default_off_avoid_class": "follow"
                    if status == "REPACKAGE_FINAL_DECISION_READY"
                    else "redesign",
                }
            )
        )

    for row in sorted(existing_evidence_rows, key=lambda item: normalized(item.get("existing_evidence_preservation_row_id"))):
        existing_evidence_carry_rows.append(
            boundary_row(
                {
                    "repackage_final_existing_evidence_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-FINAL-EXISTING-EVIDENCE-{len(existing_evidence_carry_rows) + 1:08d}"
                    ),
                    "input_existing_evidence_preservation_row_id": row.get("existing_evidence_preservation_row_id"),
                    "input_unpackaged_evidence_resolution_row_id": row.get(
                        "input_unpackaged_evidence_resolution_row_id"
                    ),
                    "input_final_implementation_evidence_row_id": row.get(
                        "input_final_implementation_evidence_row_id"
                    ),
                    "input_final_implementation_decision_row_id": row.get(
                        "input_final_implementation_decision_row_id"
                    ),
                    "symbol": row.get("symbol"),
                    "source_symbol": row.get("source_symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "selected_side": row.get("selected_side"),
                    "selected_intrabar_cost_adjusted_simulated_r": row.get(
                        "selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "effective_n": row.get("effective_n"),
                    "repackage_final_existing_evidence_status": "REPACKAGE_FINAL_EXISTING_EVIDENCE_PRESERVED",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_EXISTING_FINAL_DECISION_EVIDENCE",
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )

    for row in sorted(terminal_redesign_rows, key=lambda item: normalized(item.get("repackage_terminal_redesign_execution_row_id"))):
        terminal_redesign_carry_rows.append(
            boundary_row(
                {
                    "repackage_final_terminal_redesign_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-FINAL-TERMINAL-REDESIGN-{len(terminal_redesign_carry_rows) + 1:06d}"
                    ),
                    "input_repackage_terminal_redesign_execution_row_id": row.get(
                        "repackage_terminal_redesign_execution_row_id"
                    ),
                    "input_unpackaged_terminal_redesign_row_id": row.get("input_unpackaged_terminal_redesign_row_id"),
                    "symbol": row.get("symbol"),
                    "source_symbol": row.get("source_symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "source_path_exists": row.get("source_path_exists"),
                    "source_file_hash_match": row.get("source_file_hash_match"),
                    "selected_side": row.get("selected_side"),
                    "capacity_blocking_dimensions": row.get("capacity_blocking_dimensions") or [],
                    "final_review_score": row.get("final_review_score"),
                    "repackage_final_terminal_redesign_status": "REPACKAGE_FINAL_TERMINAL_REDESIGN_PRESERVED",
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_REPACKAGE_FINAL_TERMINAL_CAPACITY",
                    "follow_inverse_default_off_avoid_class": "redesign",
                }
            )
        )

    aggregate_rows = aggregate_repackage_final_decision_rows(decision_rows)
    return decision_rows, final_repackage_evidence_rows, existing_evidence_carry_rows, terminal_redesign_carry_rows, control_rows, aggregate_rows


def aggregate_repackage_final_decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("source_component")),
                normalized(row.get("selected_side")),
                normalized(row.get("repackage_final_decision_status")),
            )
        ].append(row)
    total_evidence = sum(as_int(row.get("candidate_evidence_rows_decided")) for row in rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        evidence_count = sum(as_int(row.get("candidate_evidence_rows_decided")) for row in members)
        output.append(
            boundary_row(
                {
                    "repackage_final_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-FINAL-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "source_component": key[1],
                    "selected_side": key[2],
                    "repackage_final_decision_status": key[3],
                    "repackage_final_decision_rows": len(members),
                    "candidate_evidence_rows_decided": evidence_count,
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "average_selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "effective_n_sum_decided": sum(as_int(row.get("effective_n_sum_decided")) for row in members),
                    "concentration_share_of_repackage_final_evidence": rounded(evidence_count / total_evidence),
                    "decision_counts": dict(
                        sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in members).items())
                    ),
                }
            )
        )
    return output


def system_repackage_final_decision_rows(
    decision_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    existing_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_execution_rows: int,
    input_repackage_evidence_rows: int,
    input_existing_evidence_rows: int,
    input_terminal_redesign_rows: int,
) -> list[dict[str, Any]]:
    status_counts = Counter(row.get("repackage_final_decision_status") for row in decision_rows)
    return [
        boundary_row(
            {
                "repackage_final_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-FINAL-SYSTEM-0001",
                "input_repackage_execution_rows": input_execution_rows,
                "input_repackage_evidence_execution_rows": input_repackage_evidence_rows,
                "input_existing_evidence_preservation_rows": input_existing_evidence_rows,
                "input_terminal_redesign_execution_rows": input_terminal_redesign_rows,
                "repackage_final_decision_rows": len(decision_rows),
                "repackage_final_evidence_rows": len(evidence_rows),
                "repackage_final_existing_evidence_rows": len(existing_rows),
                "repackage_final_terminal_redesign_rows": len(terminal_rows),
                "repackage_final_control_rows": len(control_rows),
                "aggregate_rows": len(aggregate_rows),
                "ready_repackage_final_decision_rows": status_counts.get("REPACKAGE_FINAL_DECISION_READY", 0),
                "repair_repackage_final_decision_rows": len(decision_rows)
                - status_counts.get("REPACKAGE_FINAL_DECISION_READY", 0),
                "evidence_pass_rows": sum(
                    1
                    for row in evidence_rows
                    if row.get("repackage_final_evidence_status") == "REPACKAGE_FINAL_EVIDENCE_DECISION_PASS"
                ),
                "control_pass_rows": sum(
                    1 for row in control_rows if row.get("control_status") == "REPACKAGE_FINAL_DECISION_CONTROL_PASS"
                ),
                "terminal_redesign_rows": len(terminal_rows),
                "decision_counts": dict(
                    sorted(
                        Counter(
                            [row.get("keep_kill_redesign_implement_decision") for row in decision_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in evidence_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in existing_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in terminal_rows]
                        ).items()
                    )
                ),
            }
        )
    ]
