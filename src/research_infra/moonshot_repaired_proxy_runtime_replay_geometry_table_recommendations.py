"""Branch-local recommendations from geometry table code-surface execution."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


RUNTIME_REPLAY_GEOMETRY_TABLE_RECOMMENDATIONS_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_recommendations.py"
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
    output["runtime_replay_geometry_table_recommendations_surface"] = (
        RUNTIME_REPLAY_GEOMETRY_TABLE_RECOMMENDATIONS_SURFACE
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


def recommendation_kind(row: dict[str, Any]) -> str:
    if row.get("surface_execution_status") != "CODE_SURFACE_EXECUTION_PASS":
        return "REPAIR_BRANCH_LOCAL_CODE_SURFACE_RECOMMENDATION"
    if row.get("code_surface_kind") == "GEOMETRY_SCORER_EXECUTABLE_SURFACE":
        return "KEEP_BRANCH_LOCAL_SCORER_RECOMMENDATION"
    return "KEEP_BRANCH_LOCAL_AVOID_INTELLIGENCE_RECOMMENDATION"


def recommendation_action(row: dict[str, Any]) -> str:
    kind = recommendation_kind(row)
    if kind == "KEEP_BRANCH_LOCAL_SCORER_RECOMMENDATION":
        return "RETAIN_SCORER_SURFACE_FOR_BRANCH_LOCAL_REPLAY_REVIEW"
    if kind == "KEEP_BRANCH_LOCAL_AVOID_INTELLIGENCE_RECOMMENDATION":
        return "RETAIN_AVOID_INTELLIGENCE_SURFACE_FOR_BRANCH_LOCAL_REPLAY_REVIEW"
    return "REPAIR_CODE_SURFACE_BEFORE_RECOMMENDATION"


def recommendation_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in execution_rows:
        output.append(
            boundary_row(
                {
                    "geometry_table_recommendation_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-REC-{len(output) + 1:06d}"
                    ),
                    "input_geometry_table_code_surface_execution_row_id": row.get(
                        "geometry_table_code_surface_execution_row_id"
                    ),
                    "input_geometry_table_code_surface_row_id": row.get(
                        "input_geometry_table_code_surface_row_id"
                    ),
                    "input_geometry_table_observation_row_id": row.get(
                        "input_geometry_table_observation_row_id"
                    ),
                    "input_replay_numeric_event_row_id": row.get("input_replay_numeric_event_row_id"),
                    "recommendation_kind": recommendation_kind(row),
                    "recommendation_action": recommendation_action(row),
                    "surface_execution_status": row.get("surface_execution_status"),
                    "code_surface_kind": row.get("code_surface_kind"),
                    "surface_function": row.get("surface_function"),
                    "surface_score": rounded(as_float(row.get("surface_score"))),
                    "family": row.get("family"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "market_timeframe": row.get("market_timeframe"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "default_off_avoid_class": row.get("default_off_avoid_class"),
                    "entry_reference": row.get("entry_reference"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "path_order_result": row.get("path_order_result"),
                    "fill_status": row.get("fill_status"),
                    "cost_adjusted_simulated_r": rounded(as_float(row.get("cost_adjusted_simulated_r"))),
                    "stress_simulated_r": row.get("stress_simulated_r"),
                }
            )
        )
    return output


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("recommendation_kind")),
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


def aggregate_action(kind: str, expectancy: float | None, repair_rows: int) -> str:
    if repair_rows:
        return "REPAIR_RECOMMENDATION_GROUP"
    if kind == "KEEP_BRANCH_LOCAL_SCORER_RECOMMENDATION":
        return "KEEP_SCORER_RECOMMENDATION_GROUP" if expectancy and expectancy > 0 else "REDESIGN_SCORER_RECOMMENDATION_GROUP"
    if kind == "KEEP_BRANCH_LOCAL_AVOID_INTELLIGENCE_RECOMMENDATION":
        return "KEEP_AVOID_INTELLIGENCE_RECOMMENDATION_GROUP" if expectancy and expectancy > 0 else "KILL_AVOID_INTELLIGENCE_RECOMMENDATION_GROUP"
    return "REPAIR_RECOMMENDATION_GROUP"


def aggregate_recommendation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(aggregate_key(row), []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        group = grouped[key]
        values = [float(row["surface_score"]) for row in group if row.get("surface_score") is not None]
        repair_rows = sum(1 for row in group if row.get("recommendation_kind") == "REPAIR_BRANCH_LOCAL_CODE_SURFACE_RECOMMENDATION")
        expectancy = avg(values)
        output.append(
            boundary_row(
                {
                    "aggregate_geometry_table_recommendation_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-REC-AGG-{len(output) + 1:05d}"
                    ),
                    "recommendation_kind": key[0],
                    "family": key[1],
                    "symbol": key[2],
                    "route_session": key[3],
                    "market_timeframe": key[4],
                    "horizon_id": key[5],
                    "source_component": key[6],
                    "default_off_avoid_class": key[7],
                    "row_count": len(group),
                    "repair_rows": repair_rows,
                    "expectancy_surface_score": expectancy,
                    "aggregate_recommendation_action": aggregate_action(key[0], expectancy, repair_rows),
                }
            )
        )
    return output


def system_recommendation_rows(
    rows: list[dict[str, Any]], aggregate_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    kinds = Counter(row.get("recommendation_kind") for row in rows)
    actions = Counter(row.get("recommendation_action") for row in rows)
    aggregate_actions = Counter(row.get("aggregate_recommendation_action") for row in aggregate_rows)
    return [
        boundary_row(
            {
                "system_geometry_table_recommendation_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-REC-SYSTEM-00001"
                ),
                "recommendation_rows": len(rows),
                "aggregate_recommendation_rows": len(aggregate_rows),
                "recommendation_kind_counts": dict(sorted(kinds.items())),
                "recommendation_action_counts": dict(sorted(actions.items())),
                "aggregate_recommendation_action_counts": dict(sorted(aggregate_actions.items())),
            }
        )
    ]
