"""Execute branch-local geometry table code surfaces against observations."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from src.research_infra.moonshot_repaired_proxy_runtime_replay_geometry_table_code_surfaces import (
    execute_code_surface,
)


RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACE_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_code_surface_execution.py"
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
    output["runtime_replay_geometry_table_code_surface_execution_surface"] = (
        RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACE_EXECUTION_SURFACE
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


def observation_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("geometry_table_observation_row_id")): row for row in rows if row.get("geometry_table_observation_row_id")}


def execution_status(surface: dict[str, Any], observation: dict[str, Any], execution: dict[str, Any]) -> str:
    expected = rounded(as_float(observation.get("cost_adjusted_simulated_r")))
    actual = rounded(as_float(execution.get("surface_score")))
    if not observation:
        return "CODE_SURFACE_EXECUTION_OBSERVATION_MISSING"
    if execution.get("surface_match") is not True:
        return "CODE_SURFACE_EXECUTION_SCOPE_MISMATCH"
    if expected != actual:
        return "CODE_SURFACE_EXECUTION_SCORE_MISMATCH"
    if surface.get("production_import_permitted") is not False:
        return "CODE_SURFACE_EXECUTION_BOUNDARY_REPAIR"
    return "CODE_SURFACE_EXECUTION_PASS"


def execution_row(surface: dict[str, Any], observation: dict[str, Any], ordinal: int) -> dict[str, Any]:
    execution = execute_code_surface(surface, observation)
    status = execution_status(surface, observation, execution)
    return boundary_row(
        {
            "geometry_table_code_surface_execution_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SURFACE-EXEC-{ordinal:06d}"
            ),
            "input_geometry_table_code_surface_row_id": surface.get("geometry_table_code_surface_row_id"),
            "input_geometry_table_code_candidate_row_id": surface.get("input_geometry_table_code_candidate_row_id"),
            "input_geometry_table_observation_row_id": surface.get("input_geometry_table_observation_row_id"),
            "input_geometry_table_execution_row_id": surface.get("input_geometry_table_execution_row_id"),
            "input_geometry_repair_row_id": surface.get("input_geometry_repair_row_id"),
            "input_performance_row_id": surface.get("input_performance_row_id"),
            "input_replay_numeric_event_row_id": surface.get("input_replay_numeric_event_row_id"),
            "code_surface_kind": surface.get("code_surface_kind"),
            "surface_function": surface.get("surface_function"),
            "surface_action": surface.get("surface_action"),
            "surface_execution_status": status,
            "surface_match": execution.get("surface_match"),
            "surface_score": execution.get("surface_score"),
            "expected_observation_score": rounded(as_float(observation.get("cost_adjusted_simulated_r"))),
            "family": surface.get("family"),
            "symbol": surface.get("symbol"),
            "route_session": surface.get("route_session"),
            "market_timeframe": surface.get("market_timeframe"),
            "horizon_id": surface.get("horizon_id"),
            "source_component": surface.get("source_component"),
            "default_off_avoid_class": surface.get("default_off_avoid_class"),
            "entry_reference": surface.get("entry_reference"),
            "source_path": surface.get("source_path"),
            "source_file_sha256": surface.get("source_file_sha256"),
            "path_order_result": surface.get("path_order_result"),
            "fill_status": surface.get("fill_status"),
            "cost_adjusted_simulated_r": rounded(as_float(surface.get("cost_adjusted_simulated_r"))),
            "stress_simulated_r": surface.get("stress_simulated_r"),
        }
    )


def code_surface_execution_rows(
    surface_rows: list[dict[str, Any]],
    observation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    observations = observation_by_id(observation_rows)
    output: list[dict[str, Any]] = []
    for surface in surface_rows:
        observation = observations.get(str(surface.get("input_geometry_table_observation_row_id")), {})
        output.append(execution_row(surface, observation, len(output) + 1))
    return output


def execution_issue_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in execution_rows:
        if row.get("surface_execution_status") == "CODE_SURFACE_EXECUTION_PASS":
            continue
        output.append(
            boundary_row(
                {
                    "geometry_table_code_surface_execution_issue_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SURFACE-EXEC-ISSUE-{len(output) + 1:06d}"
                    ),
                    "input_geometry_table_code_surface_execution_row_id": row.get(
                        "geometry_table_code_surface_execution_row_id"
                    ),
                    "input_geometry_table_code_surface_row_id": row.get(
                        "input_geometry_table_code_surface_row_id"
                    ),
                    "surface_execution_status": row.get("surface_execution_status"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "market_timeframe": row.get("market_timeframe"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "issue_action": "REPAIR_CODE_SURFACE_EXECUTION_ROW",
                }
            )
        )
    return output


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("code_surface_kind")),
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


def aggregate_status(kind: str, issue_rows: int, expectancy: float | None) -> str:
    if issue_rows:
        return "REPAIR_CODE_SURFACE_EXECUTION_GROUP"
    if kind == "GEOMETRY_SCORER_EXECUTABLE_SURFACE":
        return "KEEP_SCORER_CODE_SURFACE_EXECUTION_GROUP" if expectancy and expectancy > 0 else "REDESIGN_SCORER_CODE_SURFACE_EXECUTION_GROUP"
    return "KEEP_AVOID_CODE_SURFACE_EXECUTION_GROUP" if expectancy and expectancy > 0 else "KILL_AVOID_CODE_SURFACE_EXECUTION_GROUP"


def aggregate_code_surface_execution_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in execution_rows:
        grouped.setdefault(aggregate_key(row), []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        values = [float(row["surface_score"]) for row in rows if row.get("surface_score") is not None]
        issue_count = sum(1 for row in rows if row.get("surface_execution_status") != "CODE_SURFACE_EXECUTION_PASS")
        expectancy = avg(values)
        output.append(
            boundary_row(
                {
                    "aggregate_geometry_table_code_surface_execution_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SURFACE-EXEC-AGG-{len(output) + 1:05d}"
                    ),
                    "code_surface_kind": key[0],
                    "family": key[1],
                    "symbol": key[2],
                    "route_session": key[3],
                    "market_timeframe": key[4],
                    "horizon_id": key[5],
                    "source_component": key[6],
                    "default_off_avoid_class": key[7],
                    "row_count": len(rows),
                    "execution_issue_rows": issue_count,
                    "pass_rows": len(rows) - issue_count,
                    "expectancy_surface_score": expectancy,
                    "aggregate_code_surface_execution_status": aggregate_status(key[0], issue_count, expectancy),
                }
            )
        )
    return output


def system_code_surface_execution_rows(
    execution_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    statuses = Counter(row.get("surface_execution_status") for row in execution_rows)
    aggregate_statuses = Counter(row.get("aggregate_code_surface_execution_status") for row in aggregate_rows)
    return [
        boundary_row(
            {
                "system_geometry_table_code_surface_execution_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SURFACE-EXEC-SYSTEM-00001"
                ),
                "code_surface_execution_rows": len(execution_rows),
                "code_surface_execution_issue_rows": len(issue_rows),
                "aggregate_code_surface_execution_rows": len(aggregate_rows),
                "surface_execution_status_counts": dict(sorted(statuses.items())),
                "aggregate_code_surface_execution_status_counts": dict(sorted(aggregate_statuses.items())),
            }
        )
    ]
