"""Execute concrete geometry tables against held local replay geometry."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


RUNTIME_REPLAY_GEOMETRY_TABLE_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_execution.py"
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
    output["runtime_replay_geometry_table_execution_surface"] = (
        RUNTIME_REPLAY_GEOMETRY_TABLE_EXECUTION_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def table_row_id(row: dict[str, Any]) -> str | None:
    for field in (
        "geometry_scorer_table_row_id",
        "geometry_avoid_table_row_id",
        "geometry_kill_table_row_id",
        "geometry_redirection_task_row_id",
    ):
        if row.get(field):
            return str(row[field])
    return None


def build_index(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(field)): row for row in rows if row.get(field)}


def geometry_table_execution_class(table_kind: str, cost_r: float | None, gap_fields: list[str]) -> str:
    if gap_fields:
        return "GEOMETRY_TABLE_EXECUTION_SOURCE_GAP"
    if table_kind == "scorer":
        return (
            "GEOMETRY_SCORER_EXECUTION_POSITIVE_REPLAY_R"
            if cost_r is not None and cost_r > 0
            else "GEOMETRY_SCORER_EXECUTION_NONPOSITIVE_REPLAY_R"
        )
    return (
        "GEOMETRY_AVOID_EXECUTION_USEFUL_AVOID_INTELLIGENCE"
        if cost_r is not None and cost_r > 0
        else "GEOMETRY_AVOID_EXECUTION_NONUSEFUL_AVOID_INTELLIGENCE"
    )


def geometry_table_execution_decision(table_kind: str, cost_r: float | None, gap_fields: list[str]) -> str:
    if gap_fields:
        return "REPLAY_SOURCE_GAP_REQUIRES_ROW_LEVEL_REPAIR"
    if table_kind == "scorer":
        return (
            "KEEP_BRANCH_LOCAL_SCORER_OBSERVATION"
            if cost_r is not None and cost_r > 0
            else "REDESIGN_BRANCH_LOCAL_SCORER_OBSERVATION"
        )
    return (
        "CARRY_BRANCH_LOCAL_AVOID_INTELLIGENCE_OBSERVATION"
        if cost_r is not None and cost_r > 0
        else "KILL_BRANCH_LOCAL_AVOID_INTELLIGENCE_OBSERVATION"
    )


def execution_row(
    row: dict[str, Any],
    table_kind: str,
    ordinal: int,
    implementation_by_id: dict[str, dict[str, Any]],
    geometry_by_id: dict[str, dict[str, Any]],
    performance_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    input_impl_id = row.get("input_geometry_implementation_row_id")
    implementation = implementation_by_id.get(str(input_impl_id), {})
    geometry = geometry_by_id.get(str(implementation.get("input_geometry_repair_row_id")), {})
    performance = performance_by_id.get(str(implementation.get("input_performance_row_id")), {})
    gap_fields: list[str] = []
    if not implementation:
        gap_fields.append("geometry_implementation_row")
    if implementation and not geometry:
        gap_fields.append("geometry_repair_row")
    if implementation and not performance:
        gap_fields.append("performance_row")
    if geometry and geometry.get("cost_adjusted_geometry_r") is None:
        gap_fields.append("cost_adjusted_geometry_r")
    if geometry and geometry.get("action_adjusted_geometry_r") is None:
        gap_fields.append("action_adjusted_geometry_r")

    cost_r = as_float(geometry.get("cost_adjusted_geometry_r"))
    gross_r = as_float(geometry.get("action_adjusted_geometry_r"))
    stress_r = as_float(geometry.get("stress_geometry_r"))
    exec_class = geometry_table_execution_class(table_kind, cost_r, gap_fields)
    exec_decision = geometry_table_execution_decision(table_kind, cost_r, gap_fields)
    input_table_id = table_row_id(row)
    prefix = "SCORER" if table_kind == "scorer" else "AVOID"
    source_path = row.get("source_path") or geometry.get("source_path") or performance.get("market_source_path")

    return boundary_row(
        {
            "geometry_table_execution_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-EXEC-{prefix}-{ordinal:06d}"
            ),
            "input_geometry_table_row_id": input_table_id,
            "input_geometry_implementation_row_id": input_impl_id,
            "input_geometry_repair_row_id": implementation.get("input_geometry_repair_row_id"),
            "input_performance_row_id": implementation.get("input_performance_row_id"),
            "input_replay_numeric_event_row_id": geometry.get("input_replay_numeric_event_row_id")
            or performance.get("input_replay_numeric_event_row_id"),
            "table_execution_kind": table_kind,
            "branch": geometry.get("branch") or performance.get("branch"),
            "family": row.get("family") or implementation.get("family"),
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "market_timeframe": row.get("market_timeframe"),
            "horizon_id": row.get("horizon_id"),
            "source_component": row.get("source_component"),
            "default_off_avoid_class": implementation.get("default_off_avoid_class")
            or performance.get("default_off_avoid_class"),
            "follow_inverse_default_off_avoid_class": performance.get(
                "follow_inverse_default_off_avoid_class"
            ),
            "proxy_trade_direction": row.get("proxy_trade_direction"),
            "entry_reference": (
                f"GEOMETRY_TABLE:{source_path}:{input_table_id}"
                if source_path and input_table_id
                else None
            ),
            "source_path": source_path,
            "source_file_sha256": row.get("source_file_sha256") or geometry.get("source_file_sha256"),
            "proxy_entry_price": row.get("proxy_entry_price"),
            "proxy_stop_price": row.get("proxy_stop_price"),
            "proxy_target_price": row.get("proxy_target_price"),
            "proxy_denominator_price": row.get("proxy_denominator_price"),
            "path_order_result": geometry.get("path_order_result") or row.get("path_order_result"),
            "fill_status": geometry.get("fill_status"),
            "gross_simulated_r": rounded(gross_r),
            "cost_adjusted_simulated_r": rounded(cost_r),
            "stress_simulated_r": rounded(stress_r),
            "result_class": geometry.get("geometry_result_class"),
            "win_count": int(geometry.get("win_count") or 0),
            "loss_count": int(geometry.get("loss_count") or 0),
            "flat_count": int(geometry.get("flat_count") or 0),
            "no_fill_count": int(geometry.get("no_fill_count") or 0),
            "target_first_count": int(geometry.get("target_first_count") or 0),
            "stop_first_count": int(geometry.get("stop_first_count") or 0),
            "neither_count": int(geometry.get("neither_count") or 0),
            "ambiguous_count": int(geometry.get("ambiguous_count") or 0),
            "remaining_missing_geometry_fields": row.get("remaining_missing_geometry_fields") or [],
            "source_gap_fields": gap_fields,
            "source_join_status": (
                "HELD_REPLAY_GEOMETRY_JOINED" if not gap_fields else "HELD_REPLAY_SOURCE_GAP"
            ),
            "table_execution_class": exec_class,
            "table_execution_decision": exec_decision,
        }
    )


def scorer_table_execution_rows(
    scorer_rows: list[dict[str, Any]],
    implementation_rows: list[dict[str, Any]],
    geometry_rows: list[dict[str, Any]],
    performance_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    implementation_by_id = build_index(implementation_rows, "geometry_implementation_row_id")
    geometry_by_id = build_index(geometry_rows, "geometry_repair_row_id")
    performance_by_id = build_index(performance_rows, "performance_row_id")
    return [
        execution_row(row, "scorer", index, implementation_by_id, geometry_by_id, performance_by_id)
        for index, row in enumerate(scorer_rows, start=1)
    ]


def avoid_table_execution_rows(
    avoid_rows: list[dict[str, Any]],
    implementation_rows: list[dict[str, Any]],
    geometry_rows: list[dict[str, Any]],
    performance_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    implementation_by_id = build_index(implementation_rows, "geometry_implementation_row_id")
    geometry_by_id = build_index(geometry_rows, "geometry_repair_row_id")
    performance_by_id = build_index(performance_rows, "performance_row_id")
    return [
        execution_row(row, "avoid", index, implementation_by_id, geometry_by_id, performance_by_id)
        for index, row in enumerate(avoid_rows, start=1)
    ]


def source_gap_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in execution_rows:
        fields = row.get("source_gap_fields") or []
        if not fields:
            continue
        output.append(
            boundary_row(
                {
                    "geometry_table_source_gap_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-GAP-{len(output) + 1:06d}"
                    ),
                    "input_geometry_table_execution_row_id": row.get("geometry_table_execution_row_id"),
                    "input_geometry_table_row_id": row.get("input_geometry_table_row_id"),
                    "table_execution_kind": row.get("table_execution_kind"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "market_timeframe": row.get("market_timeframe"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_gap_fields": fields,
                    "source_gap_decision": "ROW_LEVEL_REPLAY_SOURCE_REPAIR_REQUIRED",
                }
            )
        )
    return output


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("table_execution_kind")),
        normalized(row.get("family")),
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("default_off_avoid_class")),
    )


def avg(values: list[float]) -> float | None:
    return rounded(mean(values)) if values else None


def aggregate_decision(kind: str, expectancy: float | None, gap_rows: int) -> str:
    if gap_rows:
        return "REDESIGN_TABLE_EXECUTION_SOURCE_GAP"
    if kind == "scorer":
        return (
            "KEEP_BRANCH_LOCAL_SCORER_TABLE_EXECUTION"
            if expectancy is not None and expectancy > 0
            else "REDESIGN_BRANCH_LOCAL_SCORER_TABLE_EXECUTION"
        )
    return (
        "CARRY_BRANCH_LOCAL_AVOID_TABLE_EXECUTION"
        if expectancy is not None and expectancy > 0
        else "KILL_BRANCH_LOCAL_AVOID_TABLE_EXECUTION"
    )


def aggregate_table_execution_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in execution_rows:
        grouped.setdefault(aggregate_key(row), []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        cost_values = [float(row["cost_adjusted_simulated_r"]) for row in rows if row.get("cost_adjusted_simulated_r") is not None]
        wins = [value for value in cost_values if value > 0]
        losses = [value for value in cost_values if value < 0]
        event_keys = {
            normalized(row.get("input_replay_numeric_event_row_id") or row.get("input_geometry_repair_row_id"))
            for row in rows
        }
        event_keys.discard("")
        source_counts = Counter(normalized(row.get("source_file_sha256")) for row in rows)
        dominant_source_count = max(source_counts.values()) if source_counts else 0
        expectancy = avg(cost_values)
        gap_count = sum(1 for row in rows if row.get("source_gap_fields"))
        output.append(
            boundary_row(
                {
                    "aggregate_geometry_table_execution_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-EXEC-AGG-{len(output) + 1:05d}"
                    ),
                    "table_execution_kind": key[0],
                    "family": key[1],
                    "symbol": key[2],
                    "route_session": key[3],
                    "market_timeframe": key[4],
                    "horizon_id": key[5],
                    "source_component": key[6],
                    "default_off_avoid_class": key[7],
                    "row_count": len(rows),
                    "source_gap_rows": gap_count,
                    "effective_n": len(event_keys),
                    "duplicate_rows": len(rows) - len(event_keys),
                    "dominant_source_file_sha256": source_counts.most_common(1)[0][0] if source_counts else None,
                    "dominant_source_row_count": dominant_source_count,
                    "dominant_source_concentration": rounded(dominant_source_count / len(rows), 6),
                    "win_count": sum(int(row.get("win_count") or 0) for row in rows),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in rows),
                    "flat_count": sum(int(row.get("flat_count") or 0) for row in rows),
                    "no_fill_count": sum(int(row.get("no_fill_count") or 0) for row in rows),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in rows),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in rows),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in rows),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in rows),
                    "expectancy_cost_adjusted_simulated_r": expectancy,
                    "average_win_cost_adjusted_simulated_r": avg(wins),
                    "average_loss_cost_adjusted_simulated_r": avg(losses),
                    "table_execution_decision": aggregate_decision(key[0], expectancy, gap_count),
                }
            )
        )
    return output


def system_table_execution_rows(
    scorer_rows: list[dict[str, Any]],
    avoid_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_rows = scorer_rows + avoid_rows
    classes = Counter(row.get("table_execution_class") for row in all_rows)
    decisions = Counter(row.get("table_execution_decision") for row in all_rows)
    aggregate_decisions = Counter(row.get("table_execution_decision") for row in aggregate_rows)
    return [
        boundary_row(
            {
                "system_geometry_table_execution_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-EXEC-SYSTEM-00001"
                ),
                "scorer_table_execution_rows": len(scorer_rows),
                "avoid_table_execution_rows": len(avoid_rows),
                "total_table_execution_rows": len(all_rows),
                "aggregate_table_execution_rows": len(aggregate_rows),
                "source_gap_rows": len(gap_rows),
                "joined_replay_geometry_rows": sum(
                    1 for row in all_rows if row.get("source_join_status") == "HELD_REPLAY_GEOMETRY_JOINED"
                ),
                "table_execution_class_counts": dict(sorted(classes.items())),
                "table_execution_decision_counts": dict(sorted(decisions.items())),
                "aggregate_table_execution_decision_counts": dict(sorted(aggregate_decisions.items())),
            }
        )
    ]
