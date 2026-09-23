"""Execute expanded-market unpackaged repackage candidates with source proof."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


EXPANDED_MARKET_REPACKAGE_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_repackage_execution.py"
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
    output["expanded_market_repackage_execution_surface"] = EXPANDED_MARKET_REPACKAGE_EXECUTION_SURFACE
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


def group_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, str, str]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("selected_side")),
        normalized(row.get("source_path")),
        normalized(row.get("source_file_sha256")),
    )


def sha_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_proof(repo_root: Path, source_path: str, expected_hash: str) -> dict[str, Any]:
    path = repo_root / source_path
    observed = file_sha256(path)
    return {
        "source_path": source_path,
        "source_path_exists": path.exists() and path.is_file(),
        "source_file_sha256_expected": expected_hash,
        "source_file_sha256_observed": observed,
        "source_file_hash_match": observed == expected_hash if observed is not None else False,
    }


def execution_status(
    candidate: dict[str, Any],
    rows: list[dict[str, Any]],
    proof: dict[str, Any],
) -> str:
    if not rows:
        return "UNPACKAGED_REPACKAGE_EXECUTION_NO_EVIDENCE"
    if len(rows) != as_int(candidate.get("unpackaged_evidence_rows")):
        return "UNPACKAGED_REPACKAGE_EXECUTION_EVIDENCE_COUNT_MISMATCH"
    if not proof.get("source_path_exists"):
        return "UNPACKAGED_REPACKAGE_EXECUTION_SOURCE_MISSING"
    if not proof.get("source_file_hash_match"):
        return "UNPACKAGED_REPACKAGE_EXECUTION_SOURCE_HASH_MISMATCH"
    average_r = as_float(candidate.get("average_selected_intrabar_cost_adjusted_simulated_r"))
    if average_r is None:
        return "UNPACKAGED_REPACKAGE_EXECUTION_MISSING_SIMULATED_R"
    if average_r <= 0:
        return "UNPACKAGED_REPACKAGE_EXECUTION_KILL_NONPOSITIVE_R"
    if sum(as_int(row.get("effective_n")) for row in rows) != as_int(candidate.get("effective_n_sum")):
        return "UNPACKAGED_REPACKAGE_EXECUTION_EFFECTIVE_N_MISMATCH"
    return "UNPACKAGED_REPACKAGE_EXECUTION_PASS"


def execution_decision(status: str) -> str:
    if status == "UNPACKAGED_REPACKAGE_EXECUTION_PASS":
        return "IMPLEMENT_EXPANDED_MARKET_UNPACKAGED_REPACKAGE_EXECUTION"
    if status == "UNPACKAGED_REPACKAGE_EXECUTION_KILL_NONPOSITIVE_R":
        return "KILL_EXPANDED_MARKET_UNPACKAGED_REPACKAGE_EXECUTION"
    return "REDESIGN_EXPANDED_MARKET_UNPACKAGED_REPACKAGE_EXECUTION"


def follow_class(status: str) -> str:
    if status == "UNPACKAGED_REPACKAGE_EXECUTION_PASS":
        return "follow"
    if status == "UNPACKAGED_REPACKAGE_EXECUTION_KILL_NONPOSITIVE_R":
        return "avoid"
    return "redesign"


def expanded_market_repackage_execution_rows(
    candidate_rows: list[dict[str, Any]],
    resolution_rows: list[dict[str, Any]],
    terminal_redesign_rows: list[dict[str, Any]],
    repo_root: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    repackage_groups: dict[tuple[str, str, str, str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    existing_resolution_rows: list[dict[str, Any]] = []
    for row in resolution_rows:
        if row.get("resolution_status") == "UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED":
            repackage_groups[group_key(row)].append(row)
        else:
            existing_resolution_rows.append(row)

    execution_rows: list[dict[str, Any]] = []
    repackage_evidence_rows: list[dict[str, Any]] = []
    existing_evidence_rows: list[dict[str, Any]] = []
    terminal_rows: list[dict[str, Any]] = []
    execution_by_key: dict[tuple[str, str, str, str, str, str, str, str], tuple[str, str, dict[str, Any]]] = {}

    for candidate in sorted(candidate_rows, key=lambda row: normalized(row.get("unpackaged_repackage_candidate_row_id"))):
        key = group_key(candidate)
        members = sorted(repackage_groups.get(key, []), key=lambda row: normalized(row.get("unpackaged_evidence_resolution_row_id")))
        proof = source_proof(repo_root, normalized(candidate.get("source_path")), normalized(candidate.get("source_file_sha256")))
        status = execution_status(candidate, members, proof)
        execution_id = f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-EXECUTION-{len(execution_rows) + 1:06d}"
        payload = {
            "candidate": candidate.get("unpackaged_repackage_candidate_row_id"),
            "key": key,
            "evidence_ids": [row.get("unpackaged_evidence_resolution_row_id") for row in members],
            "proof": proof,
            "status": status,
        }
        execution_by_key[key] = (execution_id, status, proof)
        execution_rows.append(
            boundary_row(
                {
                    "repackage_execution_row_id": execution_id,
                    "input_unpackaged_repackage_candidate_row_id": candidate.get(
                        "unpackaged_repackage_candidate_row_id"
                    ),
                    "symbol": candidate.get("symbol"),
                    "market_timeframe": candidate.get("market_timeframe"),
                    "route_session": candidate.get("route_session"),
                    "horizon_id": candidate.get("horizon_id"),
                    "source_component": candidate.get("source_component"),
                    "selected_side": candidate.get("selected_side"),
                    "source_path": candidate.get("source_path"),
                    "source_file_sha256": candidate.get("source_file_sha256"),
                    "source_path_exists": proof["source_path_exists"],
                    "source_file_sha256_expected": proof["source_file_sha256_expected"],
                    "source_file_sha256_observed": proof["source_file_sha256_observed"],
                    "source_file_hash_match": proof["source_file_hash_match"],
                    "candidate_evidence_rows_expected": candidate.get("unpackaged_evidence_rows"),
                    "candidate_evidence_rows_executed": len(members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "min_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                        "min_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "max_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                        "max_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "effective_n_sum_expected": candidate.get("effective_n_sum"),
                    "effective_n_sum_executed": sum(as_int(row.get("effective_n")) for row in members),
                    "repackage_execution_payload_sha256": sha_payload(payload),
                    "repackage_execution_status": status,
                    "keep_kill_redesign_implement_decision": execution_decision(status),
                    "follow_inverse_default_off_avoid_class": follow_class(status),
                }
            )
        )

    for key in sorted(repackage_groups):
        execution_id, status, proof = execution_by_key.get(key, (None, "UNPACKAGED_REPACKAGE_EXECUTION_ORPHAN_EVIDENCE", {}))
        for row in sorted(repackage_groups[key], key=lambda item: normalized(item.get("unpackaged_evidence_resolution_row_id"))):
            repackage_evidence_rows.append(
                boundary_row(
                    {
                        "repackage_evidence_execution_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-EVIDENCE-EXECUTION-{len(repackage_evidence_rows) + 1:08d}"
                        ),
                        "input_repackage_execution_row_id": execution_id,
                        "input_unpackaged_evidence_resolution_row_id": row.get(
                            "unpackaged_evidence_resolution_row_id"
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
                        "source_path_exists": proof.get("source_path_exists"),
                        "source_file_hash_match": proof.get("source_file_hash_match"),
                        "selected_side": row.get("selected_side"),
                        "selected_intrabar_cost_adjusted_simulated_r": row.get(
                            "selected_intrabar_cost_adjusted_simulated_r"
                        ),
                        "selected_minus_rejected_intrabar_cost_adjusted_r": row.get(
                            "selected_minus_rejected_intrabar_cost_adjusted_r"
                        ),
                        "effective_n": row.get("effective_n"),
                        "repackage_evidence_execution_status": "REPACKAGE_EVIDENCE_EXECUTION_PASS"
                        if status == "UNPACKAGED_REPACKAGE_EXECUTION_PASS"
                        else "REPACKAGE_EVIDENCE_EXECUTION_REPAIR",
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_REPACKAGE_EVIDENCE_EXECUTION"
                        if status == "UNPACKAGED_REPACKAGE_EXECUTION_PASS"
                        else "REDESIGN_EXPANDED_MARKET_REPACKAGE_EVIDENCE_EXECUTION",
                        "follow_inverse_default_off_avoid_class": "follow"
                        if status == "UNPACKAGED_REPACKAGE_EXECUTION_PASS"
                        else "redesign",
                    }
                )
            )

    for row in sorted(existing_resolution_rows, key=lambda item: normalized(item.get("unpackaged_evidence_resolution_row_id"))):
        existing_evidence_rows.append(
            boundary_row(
                {
                    "existing_evidence_preservation_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-EXISTING-EVIDENCE-PRESERVATION-{len(existing_evidence_rows) + 1:08d}"
                    ),
                    "input_unpackaged_evidence_resolution_row_id": row.get("unpackaged_evidence_resolution_row_id"),
                    "input_final_implementation_evidence_row_id": row.get("input_final_implementation_evidence_row_id"),
                    "input_final_implementation_decision_row_id": row.get("input_final_implementation_decision_row_id"),
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
                    "existing_evidence_preservation_status": "EXISTING_FINAL_DECISION_EVIDENCE_PRESERVED",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_EXISTING_FINAL_DECISION_EVIDENCE",
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )

    for row in sorted(terminal_redesign_rows, key=lambda item: normalized(item.get("unpackaged_terminal_redesign_row_id"))):
        proof = source_proof(repo_root, normalized(row.get("source_path")), normalized(row.get("source_file_sha256")))
        terminal_rows.append(
            boundary_row(
                {
                    "repackage_terminal_redesign_execution_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-TERMINAL-REDESIGN-{len(terminal_rows) + 1:06d}"
                    ),
                    "input_unpackaged_terminal_redesign_row_id": row.get("unpackaged_terminal_redesign_row_id"),
                    "input_final_implementation_redesign_row_id": row.get("input_final_implementation_redesign_row_id"),
                    "input_package_preservation_redesign_row_id": row.get(
                        "input_package_preservation_redesign_row_id"
                    ),
                    "symbol": row.get("symbol"),
                    "source_symbol": row.get("source_symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "source_path_exists": proof["source_path_exists"],
                    "source_file_hash_match": proof["source_file_hash_match"],
                    "selected_side": row.get("selected_side"),
                    "capacity_blocking_dimensions": row.get("capacity_blocking_dimensions") or [],
                    "final_review_score": row.get("final_review_score"),
                    "terminal_redesign_execution_status": "REPACKAGE_TERMINAL_REDESIGN_SOURCE_PROOF_PASS"
                    if proof["source_path_exists"] and proof["source_file_hash_match"]
                    else "REPACKAGE_TERMINAL_REDESIGN_SOURCE_PROOF_REPAIR",
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_REPACKAGE_TERMINAL_CAPACITY",
                    "follow_inverse_default_off_avoid_class": "redesign",
                }
            )
        )

    aggregate_rows = aggregate_repackage_execution_rows(execution_rows)
    return execution_rows, repackage_evidence_rows, existing_evidence_rows, terminal_rows, aggregate_rows


def aggregate_repackage_execution_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("source_component")),
                normalized(row.get("selected_side")),
                normalized(row.get("repackage_execution_status")),
            )
        ].append(row)
    total_evidence = sum(as_int(row.get("candidate_evidence_rows_executed")) for row in rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        evidence_count = sum(as_int(row.get("candidate_evidence_rows_executed")) for row in members)
        output.append(
            boundary_row(
                {
                    "repackage_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-EXECUTION-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "source_component": key[1],
                    "selected_side": key[2],
                    "repackage_execution_status": key[3],
                    "repackage_execution_rows": len(members),
                    "candidate_evidence_rows_executed": evidence_count,
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "average_selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "effective_n_sum_executed": sum(as_int(row.get("effective_n_sum_executed")) for row in members),
                    "concentration_share_of_repackage_evidence": rounded(evidence_count / total_evidence),
                    "source_proof_pass_rows": sum(
                        1
                        for row in members
                        if row.get("source_path_exists") is True and row.get("source_file_hash_match") is True
                    ),
                    "decision_counts": dict(
                        sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in members).items())
                    ),
                }
            )
        )
    return output


def system_repackage_execution_rows(
    execution_rows: list[dict[str, Any]],
    repackage_evidence_rows: list[dict[str, Any]],
    existing_evidence_rows: list[dict[str, Any]],
    terminal_redesign_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_candidate_rows: int,
    input_resolution_rows: int,
    input_terminal_redesign_rows: int,
) -> list[dict[str, Any]]:
    status_counts = Counter(row.get("repackage_execution_status") for row in execution_rows)
    return [
        boundary_row(
            {
                "repackage_execution_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-REPACKAGE-EXECUTION-SYSTEM-0001",
                "input_unpackaged_repackage_candidate_rows": input_candidate_rows,
                "input_unpackaged_evidence_resolution_rows": input_resolution_rows,
                "input_terminal_redesign_rows": input_terminal_redesign_rows,
                "repackage_execution_rows": len(execution_rows),
                "repackage_evidence_execution_rows": len(repackage_evidence_rows),
                "existing_evidence_preservation_rows": len(existing_evidence_rows),
                "terminal_redesign_execution_rows": len(terminal_redesign_rows),
                "aggregate_rows": len(aggregate_rows),
                "repackage_execution_pass_rows": status_counts.get("UNPACKAGED_REPACKAGE_EXECUTION_PASS", 0),
                "repackage_execution_repair_rows": len(execution_rows)
                - status_counts.get("UNPACKAGED_REPACKAGE_EXECUTION_PASS", 0),
                "source_proof_pass_rows": sum(
                    1
                    for row in execution_rows
                    if row.get("source_path_exists") is True and row.get("source_file_hash_match") is True
                ),
                "terminal_redesign_source_proof_pass_rows": sum(
                    1
                    for row in terminal_redesign_rows
                    if row.get("terminal_redesign_execution_status")
                    == "REPACKAGE_TERMINAL_REDESIGN_SOURCE_PROOF_PASS"
                ),
                "decision_counts": dict(
                    sorted(
                        Counter(
                            [row.get("keep_kill_redesign_implement_decision") for row in execution_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in repackage_evidence_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in existing_evidence_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in terminal_redesign_rows]
                        ).items()
                    )
                ),
            }
        )
    ]
