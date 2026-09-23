"""Execute performance-matrix branch-local surfaces against held matrix rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surfaces import (
    execute_matrix_surface,
)


RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACE_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surface_execution.py"
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
    output["runtime_replay_geometry_table_matrix_surface_execution_surface"] = (
        RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACE_EXECUTION_SURFACE
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


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def matrix_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {normalized(row.get("performance_matrix_row_id")): row for row in rows}


def common_payload(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_performance_matrix_row_id": source.get("input_performance_matrix_row_id")
        or source.get("performance_matrix_row_id"),
        "input_performance_row_id": source.get("input_performance_row_id"),
        "input_geometry_repair_row_id": source.get("input_geometry_repair_row_id"),
        "input_geometry_table_recommendation_row_id": source.get("input_geometry_table_recommendation_row_id"),
        "input_replay_numeric_event_row_id": source.get("input_replay_numeric_event_row_id"),
        "branch": source.get("branch"),
        "family": source.get("family"),
        "symbol": source.get("symbol"),
        "route_session": source.get("route_session"),
        "market_timeframe": source.get("market_timeframe"),
        "horizon_id": source.get("horizon_id"),
        "source_component": source.get("source_component"),
        "side": source.get("side"),
        "proxy_trade_direction": source.get("proxy_trade_direction"),
        "follow_inverse_default_off_avoid_class": source.get("follow_inverse_default_off_avoid_class"),
        "default_off_avoid_class": source.get("default_off_avoid_class"),
        "entry_reference": source.get("entry_reference"),
        "source_path": source.get("source_path"),
        "source_file_sha256": source.get("source_file_sha256"),
        "path_order_result": source.get("path_order_result"),
        "fill_status": source.get("fill_status"),
        "gross_simulated_r": source.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": source.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": source.get("stress_simulated_r"),
        "result_class": source.get("result_class"),
        "win_count": int(source.get("win_count") or 0),
        "loss_count": int(source.get("loss_count") or 0),
        "flat_count": int(source.get("flat_count") or 0),
        "no_fill_count": int(source.get("no_fill_count") or 0),
        "target_first_count": int(source.get("target_first_count") or 0),
        "stop_first_count": int(source.get("stop_first_count") or 0),
        "neither_count": int(source.get("neither_count") or 0),
        "ambiguous_count": int(source.get("ambiguous_count") or 0),
        "effective_n_key": source.get("effective_n_key"),
        "scope_effective_n": source.get("scope_effective_n"),
        "scope_concentration_share_of_all_rows": source.get("scope_concentration_share_of_all_rows"),
        "keep_kill_redesign_implement_decision": source.get("keep_kill_redesign_implement_decision"),
    }


def surface_execution_rows(
    surface_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = matrix_index(matrix_rows)
    output: list[dict[str, Any]] = []
    for surface in surface_rows:
        matrix = by_id.get(normalized(surface.get("input_performance_matrix_row_id")), {})
        execution = execute_matrix_surface(surface, matrix)
        expected_score = rounded(as_float(surface.get("surface_cost_adjusted_simulated_r")))
        actual_score = rounded(as_float(execution.get("surface_score")))
        status = (
            "PERFORMANCE_MATRIX_SURFACE_EXECUTION_PASS"
            if execution.get("surface_match") is True and actual_score == expected_score
            else "PERFORMANCE_MATRIX_SURFACE_EXECUTION_REPAIR"
        )
        payload = common_payload(surface)
        payload.update(
            {
                "matrix_surface_execution_row_id": (
                    f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-SURFACE-EXEC-{len(output) + 1:06d}"
                ),
                "input_matrix_surface_row_id": surface.get("matrix_surface_row_id"),
                "matrix_surface_kind": surface.get("matrix_surface_kind"),
                "surface_function": surface.get("surface_function"),
                "surface_action": surface.get("surface_action"),
                "surface_match": execution.get("surface_match"),
                "surface_score": actual_score,
                "expected_surface_score": expected_score,
                "surface_execution_status": status,
            }
        )
        output.append(boundary_row(payload))
    return output


def terminal_execution_rows(
    terminal_rows: list[dict[str, Any]],
    matrix_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = matrix_index(matrix_rows)
    output: list[dict[str, Any]] = []
    for terminal in terminal_rows:
        matrix = by_id.get(normalized(terminal.get("input_performance_matrix_row_id")), {})
        source_match = bool(matrix) and normalized(matrix.get("keep_kill_redesign_implement_decision")) == normalized(
            terminal.get("terminal_action")
        )
        status = (
            "TERMINAL_MATRIX_DECISION_EXECUTION_PRESERVED"
            if source_match
            else "TERMINAL_MATRIX_DECISION_EXECUTION_REPAIR"
        )
        payload = common_payload(terminal)
        payload.update(
            {
                "terminal_matrix_execution_row_id": (
                    f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-TERMINAL-EXEC-{len(output) + 1:06d}"
                ),
                "input_terminal_matrix_decision_row_id": terminal.get("terminal_matrix_decision_row_id"),
                "terminal_action": terminal.get("terminal_action"),
                "terminal_source_match": source_match,
                "terminal_execution_status": status,
            }
        )
        output.append(boundary_row(payload))
    return output


def execution_issue_rows(
    surface_exec_rows: list[dict[str, Any]],
    terminal_exec_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in surface_exec_rows:
        if row.get("surface_execution_status") == "PERFORMANCE_MATRIX_SURFACE_EXECUTION_PASS":
            continue
        output.append(
            boundary_row(
                {
                    "matrix_surface_execution_issue_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-EXEC-ISSUE-{len(output) + 1:06d}"
                    ),
                    "input_execution_row_id": row.get("matrix_surface_execution_row_id"),
                    "issue": row.get("surface_execution_status"),
                    "input_performance_matrix_row_id": row.get("input_performance_matrix_row_id"),
                }
            )
        )
    for row in terminal_exec_rows:
        if row.get("terminal_execution_status") == "TERMINAL_MATRIX_DECISION_EXECUTION_PRESERVED":
            continue
        output.append(
            boundary_row(
                {
                    "matrix_surface_execution_issue_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-EXEC-ISSUE-{len(output) + 1:06d}"
                    ),
                    "input_execution_row_id": row.get("terminal_matrix_execution_row_id"),
                    "issue": row.get("terminal_execution_status"),
                    "input_performance_matrix_row_id": row.get("input_performance_matrix_row_id"),
                }
            )
        )
    return output


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("branch")),
        normalized(row.get("family")),
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("side")),
        normalized(row.get("follow_inverse_default_off_avoid_class")),
        normalized(row.get("default_off_avoid_class")),
        normalized(row.get("keep_kill_redesign_implement_decision")),
    )


def aggregate_execution_rows(
    surface_exec_rows: list[dict[str, Any]],
    terminal_exec_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = surface_exec_rows + terminal_exec_rows
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[aggregate_key(row)].append(row)
    total = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        cost_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members]
        cost_values = [value for value in cost_values if value is not None]
        stress_values = [as_float(row.get("stress_simulated_r")) for row in members]
        stress_values = [value for value in stress_values if value is not None]
        effective_keys = {normalized(row.get("effective_n_key")) for row in members if row.get("effective_n_key")}
        statuses = Counter(
            normalized(row.get("surface_execution_status") or row.get("terminal_execution_status"))
            for row in members
        )
        record = {
            "aggregate_matrix_surface_execution_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-SURFACE-EXEC-AGG-{len(output) + 1:05d}"
            ),
            "branch": key[0],
            "family": key[1],
            "symbol": key[2],
            "route_session": key[3],
            "market_timeframe": key[4],
            "horizon_id": key[5],
            "source_component": key[6],
            "side": key[7],
            "follow_inverse_default_off_avoid_class": key[8],
            "default_off_avoid_class": key[9],
            "keep_kill_redesign_implement_decision": key[10],
            "row_count": len(members),
            "expectancy_cost_adjusted_simulated_r": rounded(average(cost_values)),
            "expectancy_stress_simulated_r": rounded(average(stress_values)),
            "win_count": sum(int(row.get("win_count") or 0) for row in members),
            "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
            "flat_count": sum(int(row.get("flat_count") or 0) for row in members),
            "no_fill_count": sum(int(row.get("no_fill_count") or 0) for row in members),
            "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
            "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
            "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
            "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
            "effective_n": len(effective_keys),
            "duplicate_row_count": len(members) - len(effective_keys),
            "concentration_share_of_all_rows": rounded(len(members) / total),
            "execution_status_counts": dict(sorted(statuses.items())),
        }
        output.append(boundary_row(record))
    return output


def system_execution_rows(
    surface_exec_rows: list[dict[str, Any]],
    terminal_exec_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_rows = surface_exec_rows + terminal_exec_rows
    statuses = Counter(
        normalized(row.get("surface_execution_status") or row.get("terminal_execution_status"))
        for row in all_rows
    )
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in all_rows)
    return [
        boundary_row(
            {
                "system_matrix_surface_execution_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-SURFACE-EXEC-SYSTEM-00001"
                ),
                "surface_execution_rows": len(surface_exec_rows),
                "terminal_execution_rows": len(terminal_exec_rows),
                "total_execution_rows": len(all_rows),
                "execution_issue_rows": len(issue_rows),
                "aggregate_execution_rows": len(aggregate_rows),
                "execution_status_counts": dict(sorted(statuses.items())),
                "decision_counts": dict(sorted(decisions.items())),
            }
        )
    ]
