"""Concrete branch-local tables from geometry implementation candidates."""

from __future__ import annotations

from collections import Counter
from typing import Any


RUNTIME_REPLAY_GEOMETRY_TABLES_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_tables.py"
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
    output["runtime_replay_geometry_tables_surface"] = RUNTIME_REPLAY_GEOMETRY_TABLES_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def payload(row: dict[str, Any]) -> dict[str, Any]:
    data = row.get("implementation_payload") or {}
    return data if isinstance(data, dict) else {}


def table_key(row: dict[str, Any]) -> str:
    data = payload(row)
    parts = [
        data.get("symbol"),
        data.get("route_session"),
        data.get("market_timeframe"),
        data.get("horizon_id"),
        data.get("source_component"),
        data.get("family"),
        data.get("path_order_result"),
        data.get("source_file_sha256"),
    ]
    return "|".join("" if part is None else str(part) for part in parts)


def scorer_table_rows(implementation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in implementation_rows:
        if row.get("implementation_kind") != "GEOMETRY_SCORER_PROTOTYPE_IMPLEMENTATION":
            continue
        data = payload(row)
        output.append(
            boundary_row(
                {
                    "geometry_scorer_table_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SCORER-{len(output) + 1:06d}"
                    ),
                    "input_geometry_implementation_row_id": row.get("geometry_implementation_row_id"),
                    "branch_local_table_key": table_key(row),
                    "symbol": data.get("symbol"),
                    "route_session": data.get("route_session"),
                    "market_timeframe": data.get("market_timeframe"),
                    "horizon_id": data.get("horizon_id"),
                    "source_component": data.get("source_component"),
                    "source_path": data.get("source_path"),
                    "source_file_sha256": data.get("source_file_sha256"),
                    "proxy_trade_direction": data.get("proxy_trade_direction"),
                    "proxy_entry_price": data.get("proxy_entry_price"),
                    "proxy_target_price": data.get("proxy_target_price"),
                    "proxy_stop_price": data.get("proxy_stop_price"),
                    "proxy_denominator_price": data.get("proxy_denominator_price"),
                    "path_order_result": data.get("path_order_result"),
                    "expected_cost_adjusted_geometry_r": data.get("expected_cost_adjusted_geometry_r"),
                    "remaining_missing_geometry_fields": data.get("remaining_missing_geometry_fields") or [],
                    "table_application_status": "BRANCH_LOCAL_GEOMETRY_SCORER_TABLE_READY",
                }
            )
        )
    return output


def avoid_intelligence_table_rows(implementation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in implementation_rows:
        if row.get("implementation_kind") != "GEOMETRY_AVOID_INTELLIGENCE_IMPLEMENTATION":
            continue
        data = payload(row)
        output.append(
            boundary_row(
                {
                    "geometry_avoid_table_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-AVOID-{len(output) + 1:06d}"
                    ),
                    "input_geometry_implementation_row_id": row.get("geometry_implementation_row_id"),
                    "branch_local_table_key": table_key(row),
                    "symbol": data.get("symbol"),
                    "route_session": data.get("route_session"),
                    "market_timeframe": data.get("market_timeframe"),
                    "horizon_id": data.get("horizon_id"),
                    "source_component": data.get("source_component"),
                    "source_path": data.get("source_path"),
                    "source_file_sha256": data.get("source_file_sha256"),
                    "proxy_trade_direction": data.get("proxy_trade_direction"),
                    "proxy_entry_price": data.get("proxy_entry_price"),
                    "proxy_target_price": data.get("proxy_target_price"),
                    "proxy_stop_price": data.get("proxy_stop_price"),
                    "proxy_denominator_price": data.get("proxy_denominator_price"),
                    "path_order_result": data.get("path_order_result"),
                    "expected_cost_adjusted_geometry_r": data.get("expected_cost_adjusted_geometry_r"),
                    "remaining_missing_geometry_fields": data.get("remaining_missing_geometry_fields") or [],
                    "table_application_status": "BRANCH_LOCAL_GEOMETRY_AVOID_INTELLIGENCE_TABLE_READY",
                }
            )
        )
    return output


def kill_table_rows(implementation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in implementation_rows:
        if row.get("implementation_kind") not in {
            "GEOMETRY_AVOID_COMPARATOR_KILL_IMPLEMENTATION",
            "GEOMETRY_DEFAULT_OFF_KILL_IMPLEMENTATION",
        }:
            continue
        data = payload(row)
        output.append(
            boundary_row(
                {
                    "geometry_kill_table_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-KILL-{len(output) + 1:06d}"
                    ),
                    "input_geometry_implementation_row_id": row.get("geometry_implementation_row_id"),
                    "implementation_kind": row.get("implementation_kind"),
                    "branch_local_table_key": table_key(row),
                    "symbol": data.get("symbol"),
                    "route_session": data.get("route_session"),
                    "market_timeframe": data.get("market_timeframe"),
                    "horizon_id": data.get("horizon_id"),
                    "source_component": data.get("source_component"),
                    "source_path": data.get("source_path"),
                    "source_file_sha256": data.get("source_file_sha256"),
                    "path_order_result": data.get("path_order_result"),
                    "expected_cost_adjusted_geometry_r": data.get("expected_cost_adjusted_geometry_r"),
                    "kill_reason": row.get("implementation_action"),
                    "remaining_missing_geometry_fields": data.get("remaining_missing_geometry_fields") or [],
                    "table_application_status": "BRANCH_LOCAL_GEOMETRY_KILL_TABLE_READY",
                }
            )
        )
    return output


def redirection_task_rows(aggregate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in aggregate_rows:
        if row.get("aggregate_implementation_action") != "OPEN_BRANCH_LOCAL_REDIRECTION_TASK_FOR_AGGREGATE":
            continue
        output.append(
            boundary_row(
                {
                    "geometry_redirection_task_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-REDIRECT-{len(output) + 1:05d}"
                    ),
                    "input_aggregate_implementation_row_id": row.get("aggregate_implementation_row_id"),
                    "family": row.get("family"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "market_timeframe": row.get("market_timeframe"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "default_off_avoid_class": row.get("default_off_avoid_class"),
                    "row_count": row.get("row_count"),
                    "effective_n": row.get("effective_n"),
                    "expectancy_cost_adjusted_geometry_r": row.get("expectancy_cost_adjusted_geometry_r"),
                    "geometry_aggregate_decision": row.get("geometry_aggregate_decision"),
                    "table_application_status": "BRANCH_LOCAL_REDIRECTION_TASK_READY",
                }
            )
        )
    return output


def system_table_rows(
    scorer_rows: list[dict[str, Any]],
    avoid_rows: list[dict[str, Any]],
    kill_rows: list[dict[str, Any]],
    redirection_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    status_counts = Counter(
        row.get("table_application_status")
        for row in scorer_rows + avoid_rows + kill_rows + redirection_rows
    )
    return [
        boundary_row(
            {
                "system_geometry_table_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SYSTEM-00001",
                "geometry_scorer_table_rows": len(scorer_rows),
                "geometry_avoid_table_rows": len(avoid_rows),
                "geometry_kill_table_rows": len(kill_rows),
                "geometry_redirection_task_rows": len(redirection_rows),
                "table_application_status_counts": dict(sorted(status_counts.items())),
            }
        )
    ]
