"""Resolve source-expansion action-pack work rows into concrete task statuses."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_action_pack_work_resolution.py"
)


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": "concrete_branch_local_research_boundary_v1",
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_source_expansion_action_pack_work_resolution_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def stable_sha256(payload: dict[str, Any]) -> str:
    import json

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def resolution_status(row: dict[str, Any]) -> str:
    work_status = normalized(row.get("work_status"))
    if work_status == "ACTION_PACK_SOURCE_GAP_WORK_PRESERVED":
        return "ACTION_PACK_WORK_RESOLUTION_SOURCE_ACQUISITION_REQUIRED"
    if work_status == "ACTION_PACK_NONCOMPUTABLE_REPLAY_WORK_PRESERVED":
        return "ACTION_PACK_WORK_RESOLUTION_REPLAY_IMPLEMENTATION_REQUIRED"
    if row.get("cost_adjusted_simulated_r") is not None:
        return "ACTION_PACK_WORK_RESOLUTION_RULE_REDESIGN_NUMERIC_AVAILABLE"
    return "ACTION_PACK_WORK_RESOLUTION_REPLAY_FIELD_REQUIRED"


def decision_for_status(status: str) -> str:
    if status == "ACTION_PACK_WORK_RESOLUTION_RULE_REDESIGN_NUMERIC_AVAILABLE":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_RULE_REQUIRED"
    if status == "ACTION_PACK_WORK_RESOLUTION_SOURCE_ACQUISITION_REQUIRED":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SOURCE_ACQUISITION_REQUIRED"
    return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_REPLAY_IMPLEMENTATION_REQUIRED"


def work_resolution_row(
    row: dict[str, Any],
    source_proof: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    status = resolution_status(row)
    decision = decision_for_status(status)
    expression = {
        "status": status,
        "work_execution_row_id": row.get(
            "expanded_market_source_expansion_action_pack_work_execution_row_id"
        ),
        "source_path": row.get("source_path"),
        "source_proof": source_proof,
        "missing_work_fields": row.get("missing_work_fields") or [],
    }
    return boundary_row(
        {
            "expanded_market_source_expansion_action_pack_work_resolution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-WORK-RES-{sequence:07d}"
            ),
            "input_action_pack_work_execution_row_id": row.get(
                "expanded_market_source_expansion_action_pack_work_execution_row_id"
            ),
            "input_action_pack_work_row_id": row.get("input_action_pack_work_row_id"),
            "input_source_expansion_action_application_row_id": row.get(
                "input_source_expansion_action_application_row_id"
            ),
            "work_resolution_status": status,
            "work_status": row.get("work_status"),
            "symbol_family": row.get("symbol_family"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "side": row.get("side"),
            "source_path": row.get("source_path"),
            "source_path_sha256": row.get("source_path_sha256"),
            "source_file_sha256": row.get("source_file_sha256"),
            "current_source_path_exists": source_proof.get("current_source_path_exists"),
            "current_source_file_sha256": source_proof.get("current_source_file_sha256"),
            "current_source_file_hash_matches_row": source_proof.get(
                "current_source_file_hash_matches_row"
            ),
            "discovered_same_symbol_timeframe_source_count": source_proof.get(
                "discovered_same_symbol_timeframe_source_count"
            ),
            "discovered_same_symbol_timeframe_source_paths": source_proof.get(
                "discovered_same_symbol_timeframe_source_paths"
            ),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "effective_n": row.get("effective_n"),
            "missing_work_fields": row.get("missing_work_fields") or [],
            "branch_local_work_resolution_expression": expression,
            "branch_local_work_resolution_expression_sha256": stable_sha256(expression),
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def aggregate_work_resolution_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            normalized(row.get("work_resolution_status")),
            normalized(row.get("symbol_family")),
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("side")),
        )
        grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        values = [
            as_float(row.get("cost_adjusted_simulated_r"))
            for row in members
            if as_float(row.get("cost_adjusted_simulated_r")) is not None
        ]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_action_pack_work_resolution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-ACTION-PACK-WORK-RES-AGG-{len(output) + 1:07d}"
                    ),
                    "work_resolution_status": key[0],
                    "symbol_family": key[1],
                    "symbol": key[2],
                    "market_timeframe": key[3],
                    "route_session": key[4],
                    "horizon_id": key[5],
                    "side": key[6],
                    "row_count": len(members),
                    "rows_with_simulated_r": len(values),
                    "average_cost_adjusted_simulated_r": rounded(
                        sum(values) / len(values) if values else None
                    ),
                    "effective_n_sum": sum(int(row.get("effective_n") or 0) for row in members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "current_source_path_exists_count": sum(
                        1 for row in members if row.get("current_source_path_exists") is True
                    ),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output
