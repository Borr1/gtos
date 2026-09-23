"""Resolve unpackaged evidence left after expanded-market final decisions."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_UNPACKAGED_EVIDENCE_RESOLUTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unpackaged_evidence_resolution.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
MIN_REPACKAGE_EFFECTIVE_N = 20


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
    output["expanded_market_unpackaged_evidence_resolution_surface"] = (
        EXPANDED_MARKET_UNPACKAGED_EVIDENCE_RESOLUTION_SURFACE
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


def evidence_resolution_status(row: dict[str, Any]) -> str:
    if row.get("final_implementation_evidence_status") == "FINAL_IMPLEMENTATION_EVIDENCE_DECISION_PASS":
        return "UNPACKAGED_EVIDENCE_RESOLUTION_ALREADY_IMPLEMENTED"
    selected_r = as_float(row.get("selected_intrabar_cost_adjusted_simulated_r"))
    if selected_r is None:
        return "UNPACKAGED_EVIDENCE_RESOLUTION_MISSING_SIMULATED_R"
    if selected_r <= 0:
        return "UNPACKAGED_EVIDENCE_RESOLUTION_KILL_NONPOSITIVE_R"
    if as_int(row.get("effective_n")) < MIN_REPACKAGE_EFFECTIVE_N:
        return "UNPACKAGED_EVIDENCE_RESOLUTION_REDESIGN_UNDERPOWERED"
    return "UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED"


def resolution_decision(status: str) -> str:
    if status == "UNPACKAGED_EVIDENCE_RESOLUTION_ALREADY_IMPLEMENTED":
        return "IMPLEMENT_EXPANDED_MARKET_EXISTING_FINAL_DECISION_EVIDENCE"
    if status == "UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED":
        return "REDESIGN_EXPANDED_MARKET_UNPACKAGED_EVIDENCE_REPACKAGE"
    if status == "UNPACKAGED_EVIDENCE_RESOLUTION_REDESIGN_UNDERPOWERED":
        return "REDESIGN_EXPANDED_MARKET_UNPACKAGED_EVIDENCE_UNDERPOWERED"
    return "KILL_EXPANDED_MARKET_UNPACKAGED_EVIDENCE"


def follow_class(status: str) -> str:
    if status == "UNPACKAGED_EVIDENCE_RESOLUTION_ALREADY_IMPLEMENTED":
        return "follow"
    if status.startswith("UNPACKAGED_EVIDENCE_RESOLUTION_KILL"):
        return "avoid"
    return "redesign"


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


def unpackaged_evidence_resolution_rows(
    evidence_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    resolution_rows: list[dict[str, Any]] = []
    groups: dict[tuple[str, str, str, str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    terminal_redesign_rows: list[dict[str, Any]] = []

    for row in sorted(evidence_rows, key=lambda item: normalized(item.get("final_implementation_evidence_row_id"))):
        status = evidence_resolution_status(row)
        resolution_id = f"OHLC-GTOS-EXPANDED-MARKET-UNPACKAGED-EVIDENCE-RESOLUTION-{len(resolution_rows) + 1:08d}"
        output = boundary_row(
            {
                "unpackaged_evidence_resolution_row_id": resolution_id,
                "input_final_implementation_evidence_row_id": row.get("final_implementation_evidence_row_id"),
                "input_final_implementation_decision_row_id": row.get("input_final_implementation_decision_row_id"),
                "input_package_preservation_candidate_row_id": row.get("input_package_preservation_candidate_row_id"),
                "input_package_preservation_evidence_row_id": row.get("input_package_preservation_evidence_row_id"),
                "input_final_review_row_id": row.get("input_final_review_row_id"),
                "input_final_review_evidence_row_id": row.get("input_final_review_evidence_row_id"),
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
                "selected_minus_rejected_intrabar_cost_adjusted_r": row.get(
                    "selected_minus_rejected_intrabar_cost_adjusted_r"
                ),
                "effective_n": row.get("effective_n"),
                "final_implementation_evidence_status": row.get("final_implementation_evidence_status"),
                "resolution_status": status,
                "missing_simulated_field": "selected_intrabar_cost_adjusted_simulated_r"
                if status == "UNPACKAGED_EVIDENCE_RESOLUTION_MISSING_SIMULATED_R"
                else None,
                "keep_kill_redesign_implement_decision": resolution_decision(status),
                "follow_inverse_default_off_avoid_class": follow_class(status),
            }
        )
        resolution_rows.append(output)
        if status == "UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED":
            groups[group_key(output)].append(output)

    candidate_rows: list[dict[str, Any]] = []
    for key in sorted(groups):
        members = groups[key]
        payload = {
            "key": key,
            "evidence_ids": sorted(row.get("unpackaged_evidence_resolution_row_id") for row in members),
        }
        candidate_rows.append(
            boundary_row(
                {
                    "unpackaged_repackage_candidate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNPACKAGED-REPACKAGE-CANDIDATE-{len(candidate_rows) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "selected_side": key[5],
                    "source_path": key[6],
                    "source_file_sha256": key[7],
                    "unpackaged_evidence_rows": len(members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "min_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        min(numeric_values(members, "selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "max_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        max(numeric_values(members, "selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "effective_n_sum": sum(as_int(row.get("effective_n")) for row in members),
                    "repackage_candidate_payload_sha256": sha_payload(payload),
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNPACKAGED_GROUP_REPACKAGE",
                    "follow_inverse_default_off_avoid_class": "redesign",
                }
            )
        )

    for row in sorted(redesign_rows, key=lambda item: normalized(item.get("final_implementation_redesign_row_id"))):
        terminal_redesign_rows.append(
            boundary_row(
                {
                    "unpackaged_terminal_redesign_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNPACKAGED-TERMINAL-REDESIGN-{len(terminal_redesign_rows) + 1:06d}"
                    ),
                    "input_final_implementation_redesign_row_id": row.get("final_implementation_redesign_row_id"),
                    "input_package_preservation_redesign_row_id": row.get("input_package_preservation_redesign_row_id"),
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
                    "terminal_redesign_status": "UNPACKAGED_EVIDENCE_RESOLUTION_TERMINAL_REDESIGN_PRESERVED",
                    "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_UNPACKAGED_TERMINAL_CAPACITY",
                    "follow_inverse_default_off_avoid_class": "redesign",
                }
            )
        )

    aggregate_rows = aggregate_resolution_rows(resolution_rows)
    return resolution_rows, candidate_rows, terminal_redesign_rows, aggregate_rows


def aggregate_resolution_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("source_component")),
                normalized(row.get("selected_side")),
                normalized(row.get("resolution_status")),
            )
        ].append(row)
    total_rows = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        output.append(
            boundary_row(
                {
                    "unpackaged_evidence_resolution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNPACKAGED-EVIDENCE-RESOLUTION-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol": key[0],
                    "source_component": key[1],
                    "selected_side": key[2],
                    "resolution_status": key[3],
                    "evidence_rows": len(members),
                    "average_selected_intrabar_cost_adjusted_simulated_r": rounded(
                        average(numeric_values(members, "selected_intrabar_cost_adjusted_simulated_r"))
                    ),
                    "effective_n_sum": sum(as_int(row.get("effective_n")) for row in members),
                    "concentration_share_of_resolution_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(
                        sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in members).items())
                    ),
                }
            )
        )
    return output


def system_resolution_rows(
    resolution_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    terminal_redesign_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    input_evidence_rows: int,
    input_redesign_rows: int,
) -> list[dict[str, Any]]:
    status_counts = Counter(row.get("resolution_status") for row in resolution_rows)
    return [
        boundary_row(
            {
                "unpackaged_evidence_resolution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-UNPACKAGED-EVIDENCE-RESOLUTION-SYSTEM-0001"
                ),
                "input_final_implementation_evidence_rows": input_evidence_rows,
                "input_final_implementation_redesign_rows": input_redesign_rows,
                "unpackaged_evidence_resolution_rows": len(resolution_rows),
                "unpackaged_repackage_candidate_rows": len(candidate_rows),
                "terminal_redesign_rows": len(terminal_redesign_rows),
                "aggregate_rows": len(aggregate_rows),
                "already_implemented_evidence_rows": status_counts.get(
                    "UNPACKAGED_EVIDENCE_RESOLUTION_ALREADY_IMPLEMENTED", 0
                ),
                "repackage_required_evidence_rows": status_counts.get(
                    "UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED", 0
                ),
                "underpowered_evidence_rows": status_counts.get(
                    "UNPACKAGED_EVIDENCE_RESOLUTION_REDESIGN_UNDERPOWERED", 0
                ),
                "kill_evidence_rows": status_counts.get("UNPACKAGED_EVIDENCE_RESOLUTION_KILL_NONPOSITIVE_R", 0),
                "missing_simulated_r_rows": status_counts.get(
                    "UNPACKAGED_EVIDENCE_RESOLUTION_MISSING_SIMULATED_R", 0
                ),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in resolution_rows).items())
                ),
            }
        )
    ]
