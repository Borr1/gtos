"""Unified branch-local final decisions for expanded-market package and repackage rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_UNIFIED_FINAL_DECISIONS_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unified_final_decisions.py"
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
    output["expanded_market_unified_final_decisions_surface"] = EXPANDED_MARKET_UNIFIED_FINAL_DECISIONS_SURFACE
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


def scalar_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [normalized(item) for item in value]
    if value is None or value == "":
        return []
    return [normalized(value)]


def unified_final_decision_rows(
    package_decision_rows: list[dict[str, Any]],
    package_member_rows: list[dict[str, Any]],
    package_evidence_rows: list[dict[str, Any]],
    repackage_decision_rows: list[dict[str, Any]],
    repackage_evidence_rows: list[dict[str, Any]],
    repackage_existing_evidence_rows: list[dict[str, Any]],
    terminal_redesign_rows: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    decision_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    terminal_rows: list[dict[str, Any]] = []
    source_to_unified: dict[tuple[str, str], str] = {}

    for row in sorted(package_decision_rows, key=lambda item: normalized(item.get("final_implementation_decision_row_id"))):
        unified_id = f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-FINAL-DECISION-{len(decision_rows) + 1:06d}"
        source_to_unified[("package", normalized(row.get("final_implementation_decision_row_id")))] = unified_id
        payload = {
            "origin": "package",
            "source_id": row.get("final_implementation_decision_row_id"),
            "evidence_rows": row.get("evidence_rows_decided"),
            "member_rows": row.get("member_rows_decided"),
        }
        decision_rows.append(
            boundary_row(
                {
                    "unified_final_decision_row_id": unified_id,
                    "decision_origin": "package_final",
                    "input_final_implementation_decision_row_id": row.get("final_implementation_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "selected_side": row.get("selected_side"),
                    "source_paths": row.get("source_paths"),
                    "source_file_sha256_values": row.get("source_file_sha256_values"),
                    "decision_evidence_rows": row.get("evidence_rows_decided"),
                    "decision_member_rows": row.get("member_rows_decided"),
                    "average_selected_intrabar_cost_adjusted_simulated_r": row.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "effective_n_sum": row.get("recomputed_evidence_effective_n_sum"),
                    "unified_final_decision_payload_sha256": sha_payload(payload),
                    "unified_final_decision_status": "UNIFIED_FINAL_DECISION_READY",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_FINAL_DECISION",
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )

    for row in sorted(repackage_decision_rows, key=lambda item: normalized(item.get("repackage_final_decision_row_id"))):
        unified_id = f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-FINAL-DECISION-{len(decision_rows) + 1:06d}"
        source_to_unified[("repackage", normalized(row.get("repackage_final_decision_row_id")))] = unified_id
        payload = {
            "origin": "repackage",
            "source_id": row.get("repackage_final_decision_row_id"),
            "evidence_rows": row.get("candidate_evidence_rows_decided"),
        }
        decision_rows.append(
            boundary_row(
                {
                    "unified_final_decision_row_id": unified_id,
                    "decision_origin": "repackage_final",
                    "input_repackage_final_decision_row_id": row.get("repackage_final_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "market_timeframe": row.get("market_timeframe"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "selected_side": row.get("selected_side"),
                    "source_paths": scalar_list(row.get("source_path")),
                    "source_file_sha256_values": scalar_list(row.get("source_file_sha256")),
                    "decision_evidence_rows": row.get("candidate_evidence_rows_decided"),
                    "decision_member_rows": 0,
                    "average_selected_intrabar_cost_adjusted_simulated_r": row.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "effective_n_sum": row.get("effective_n_sum_decided"),
                    "unified_final_decision_payload_sha256": sha_payload(payload),
                    "unified_final_decision_status": "UNIFIED_FINAL_DECISION_READY",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_FINAL_DECISION",
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )

    for row in sorted(package_member_rows, key=lambda item: normalized(item.get("final_implementation_member_row_id"))):
        unified_id = source_to_unified.get(("package", normalized(row.get("input_final_implementation_decision_row_id"))))
        member_rows.append(
            boundary_row(
                {
                    "unified_final_member_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-FINAL-MEMBER-{len(member_rows) + 1:07d}"
                    ),
                    "input_unified_final_decision_row_id": unified_id,
                    "input_final_implementation_member_row_id": row.get("final_implementation_member_row_id"),
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
                    "artifact_function_name": row.get("artifact_function_name"),
                    "artifact_scope_sha256": row.get("artifact_scope_sha256"),
                    "unified_final_member_status": "UNIFIED_FINAL_MEMBER_PRESERVED",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_FINAL_MEMBER",
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )

    for row in sorted(package_evidence_rows, key=lambda item: normalized(item.get("final_implementation_evidence_row_id"))):
        if row.get("final_implementation_evidence_status") != "FINAL_IMPLEMENTATION_EVIDENCE_DECISION_PASS":
            continue
        unified_id = source_to_unified.get(("package", normalized(row.get("input_final_implementation_decision_row_id"))))
        evidence_rows.append(
            boundary_row(
                {
                    "unified_final_evidence_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-FINAL-EVIDENCE-{len(evidence_rows) + 1:08d}"
                    ),
                    "evidence_origin": "package_final",
                    "input_unified_final_decision_row_id": unified_id,
                    "input_final_implementation_evidence_row_id": row.get("final_implementation_evidence_row_id"),
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
                    "unified_final_evidence_status": "UNIFIED_FINAL_EVIDENCE_PRESERVED",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_FINAL_EVIDENCE",
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )

    for row in sorted(repackage_evidence_rows, key=lambda item: normalized(item.get("repackage_final_evidence_row_id"))):
        unified_id = source_to_unified.get(("repackage", normalized(row.get("input_repackage_final_decision_row_id"))))
        evidence_rows.append(
            boundary_row(
                {
                    "unified_final_evidence_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-FINAL-EVIDENCE-{len(evidence_rows) + 1:08d}"
                    ),
                    "evidence_origin": "repackage_final",
                    "input_unified_final_decision_row_id": unified_id,
                    "input_repackage_final_evidence_row_id": row.get("repackage_final_evidence_row_id"),
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
                    "unified_final_evidence_status": "UNIFIED_FINAL_EVIDENCE_PRESERVED",
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_FINAL_EVIDENCE",
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )

    for row in sorted(terminal_redesign_rows, key=lambda item: normalized(item.get("repackage_final_terminal_redesign_row_id"))):
        terminal_rows.append(
            boundary_row(
                {
                    "unified_final_terminal_redesign_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-FINAL-TERMINAL-REDESIGN-{len(terminal_rows) + 1:06d}"
                    ),
                    "input_repackage_final_terminal_redesign_row_id": row.get(
                        "repackage_final_terminal_redesign_row_id"
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
                    "capacity_blocking_dimensions": row.get("capacity_blocking_dimensions") or [],
                    "unified_terminal_redesign_status": "UNIFIED_FINAL_TERMINAL_REDESIGN_PRESERVED",
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNIFIED_FINAL_TERMINAL_CAPACITY",
                    "follow_inverse_default_off_avoid_class": "redesign",
                }
            )
        )

    aggregate_rows = aggregate_unified_final_decision_rows(decision_rows)
    return decision_rows, member_rows, evidence_rows, terminal_rows, aggregate_rows


def aggregate_unified_final_decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                normalized(row.get("decision_origin")),
                normalized(row.get("symbol")),
                normalized(row.get("source_component")),
                normalized(row.get("selected_side")),
            )
        ].append(row)
    total_evidence = sum(as_int(row.get("decision_evidence_rows")) for row in rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        evidence_count = sum(as_int(row.get("decision_evidence_rows")) for row in members)
        output.append(
            boundary_row(
                {
                    "unified_final_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-FINAL-AGG-{len(output) + 1:06d}"
                    ),
                    "decision_origin": key[0],
                    "symbol": key[1],
                    "source_component": key[2],
                    "selected_side": key[3],
                    "unified_final_decision_rows": len(members),
                    "decision_evidence_rows": evidence_count,
                    "decision_member_rows": sum(as_int(row.get("decision_member_rows")) for row in members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "average_selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "effective_n_sum": sum(as_int(row.get("effective_n_sum")) for row in members),
                    "concentration_share_of_unified_evidence": rounded(evidence_count / total_evidence),
                    "decision_counts": dict(
                        sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in members).items())
                    ),
                }
            )
        )
    return output


def system_unified_final_decision_rows(
    decision_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_package_decision_rows: int,
    input_package_member_rows: int,
    input_package_evidence_rows: int,
    input_repackage_decision_rows: int,
    input_repackage_evidence_rows: int,
    input_repackage_existing_rows: int,
    input_terminal_rows: int,
) -> list[dict[str, Any]]:
    origin_counts = Counter(row.get("decision_origin") for row in decision_rows)
    evidence_origin_counts = Counter(row.get("evidence_origin") for row in evidence_rows)
    return [
        boundary_row(
            {
                "unified_final_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-UNIFIED-FINAL-SYSTEM-0001",
                "input_package_decision_rows": input_package_decision_rows,
                "input_package_member_rows": input_package_member_rows,
                "input_package_evidence_rows": input_package_evidence_rows,
                "input_repackage_decision_rows": input_repackage_decision_rows,
                "input_repackage_evidence_rows": input_repackage_evidence_rows,
                "input_repackage_existing_evidence_rows": input_repackage_existing_rows,
                "input_terminal_redesign_rows": input_terminal_rows,
                "unified_final_decision_rows": len(decision_rows),
                "unified_package_decision_rows": origin_counts.get("package_final", 0),
                "unified_repackage_decision_rows": origin_counts.get("repackage_final", 0),
                "unified_final_member_rows": len(member_rows),
                "unified_final_evidence_rows": len(evidence_rows),
                "unified_package_evidence_rows": evidence_origin_counts.get("package_final", 0),
                "unified_repackage_evidence_rows": evidence_origin_counts.get("repackage_final", 0),
                "unified_terminal_redesign_rows": len(terminal_rows),
                "aggregate_rows": len(aggregate_rows),
                "repackage_existing_rows_deduplicated": input_repackage_existing_rows,
                "ready_unified_final_decision_rows": sum(
                    1 for row in decision_rows if row.get("unified_final_decision_status") == "UNIFIED_FINAL_DECISION_READY"
                ),
                "decision_counts": dict(
                    sorted(
                        Counter(
                            [row.get("keep_kill_redesign_implement_decision") for row in decision_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in evidence_rows]
                            + [row.get("keep_kill_redesign_implement_decision") for row in terminal_rows]
                        ).items()
                    )
                ),
            }
        )
    ]
