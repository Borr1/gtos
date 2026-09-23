"""Executable branch-local code surfaces for geometry table candidates."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACES_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_code_surfaces.py"
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
    output["runtime_replay_geometry_table_code_surfaces_surface"] = (
        RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACES_SURFACE
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


def scope_fields() -> list[str]:
    return [
        "symbol",
        "route_session",
        "market_timeframe",
        "horizon_id",
        "source_component",
        "source_file_sha256",
        "path_order_result",
    ]


def event_matches_code_surface(surface: dict[str, Any], event: dict[str, Any]) -> bool:
    return all(normalized(surface.get(field)) == normalized(event.get(field)) for field in scope_fields())


def execute_code_surface(surface: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    matched = event_matches_code_surface(surface, event)
    score = as_float(surface.get("surface_cost_adjusted_simulated_r")) if matched else None
    return {
        "surface_match": matched,
        "surface_score": rounded(score),
        "surface_action": surface.get("surface_action") if matched else "CODE_SURFACE_SCOPE_MISMATCH",
    }


def positive_event(surface: dict[str, Any]) -> dict[str, Any]:
    return {field: surface.get(field) for field in scope_fields()}


def negative_event(surface: dict[str, Any]) -> dict[str, Any]:
    event = positive_event(surface)
    event["symbol"] = normalized(event.get("symbol")) + "_MISMATCH"
    return event


def surface_action(kind: str, cost_r: float | None) -> str:
    if kind == "GEOMETRY_SCORER_CODE_CANDIDATE":
        return (
            "EMIT_BRANCH_LOCAL_SCORER_REPLAY_OBSERVATION"
            if cost_r is not None and cost_r > 0
            else "EMIT_BRANCH_LOCAL_SCORER_REDESIGN_OBSERVATION"
        )
    return (
        "EMIT_BRANCH_LOCAL_AVOID_REPLAY_OBSERVATION"
        if cost_r is not None and cost_r > 0
        else "EMIT_BRANCH_LOCAL_AVOID_KILL_OBSERVATION"
    )


def surface_from_candidate(row: dict[str, Any], ordinal: int) -> dict[str, Any]:
    cost_r = as_float(row.get("cost_adjusted_simulated_r"))
    candidate_kind = row.get("code_candidate_kind")
    prefix = "SCORER" if candidate_kind == "GEOMETRY_SCORER_CODE_CANDIDATE" else "AVOID"
    return boundary_row(
        {
            "geometry_table_code_surface_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SURFACE-{prefix}-{ordinal:06d}"
            ),
            "input_geometry_table_code_candidate_row_id": row.get("geometry_table_code_candidate_row_id"),
            "input_geometry_table_observation_row_id": row.get("input_geometry_table_observation_row_id"),
            "input_geometry_table_execution_row_id": row.get("input_geometry_table_execution_row_id"),
            "input_geometry_repair_row_id": row.get("input_geometry_repair_row_id"),
            "input_performance_row_id": row.get("input_performance_row_id"),
            "input_replay_numeric_event_row_id": row.get("input_replay_numeric_event_row_id"),
            "code_surface_kind": (
                "GEOMETRY_SCORER_EXECUTABLE_SURFACE"
                if candidate_kind == "GEOMETRY_SCORER_CODE_CANDIDATE"
                else "GEOMETRY_AVOID_EXECUTABLE_SURFACE"
            ),
            "source_code_candidate_kind": candidate_kind,
            "surface_function": row.get("branch_local_candidate_function"),
            "surface_module": RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACES_SURFACE,
            "surface_action": surface_action(normalized(candidate_kind), cost_r),
            "surface_cost_adjusted_simulated_r": rounded(cost_r),
            "branch_local_candidate_key": row.get("branch_local_candidate_key"),
            "family": row.get("family"),
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "market_timeframe": row.get("market_timeframe"),
            "horizon_id": row.get("horizon_id"),
            "source_component": row.get("source_component"),
            "default_off_avoid_class": row.get("default_off_avoid_class"),
            "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
            "entry_reference": row.get("entry_reference"),
            "source_path": row.get("source_path"),
            "source_file_sha256": row.get("source_file_sha256"),
            "path_order_result": row.get("path_order_result"),
            "fill_status": row.get("fill_status"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": rounded(cost_r),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "win_count": int(row.get("win_count") or 0),
            "loss_count": int(row.get("loss_count") or 0),
            "flat_count": int(row.get("flat_count") or 0),
            "no_fill_count": int(row.get("no_fill_count") or 0),
            "target_first_count": int(row.get("target_first_count") or 0),
            "stop_first_count": int(row.get("stop_first_count") or 0),
            "neither_count": int(row.get("neither_count") or 0),
            "ambiguous_count": int(row.get("ambiguous_count") or 0),
            "source_gap_fields": row.get("source_gap_fields") or [],
            "surface_scope_fields": scope_fields(),
            "production_import_permitted": False,
        }
    )


def scorer_code_surface_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [surface_from_candidate(row, index) for index, row in enumerate(candidate_rows, start=1)]


def avoid_code_surface_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [surface_from_candidate(row, index) for index, row in enumerate(candidate_rows, start=1)]


def surface_self_test_rows(surface_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in surface_rows:
        positive = execute_code_surface(row, positive_event(row))
        negative = execute_code_surface(row, negative_event(row))
        status = (
            "GEOMETRY_CODE_SURFACE_SELF_TEST_PASS"
            if positive.get("surface_match") is True
            and positive.get("surface_score") == row.get("surface_cost_adjusted_simulated_r")
            and negative.get("surface_match") is False
            and negative.get("surface_score") is None
            else "GEOMETRY_CODE_SURFACE_SELF_TEST_REPAIR"
        )
        output.append(
            boundary_row(
                {
                    "geometry_table_code_surface_self_test_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SURFACE-TEST-{len(output) + 1:06d}"
                    ),
                    "input_geometry_table_code_surface_row_id": row.get(
                        "geometry_table_code_surface_row_id"
                    ),
                    "source_code_candidate_kind": row.get("source_code_candidate_kind"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "market_timeframe": row.get("market_timeframe"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "positive_surface_match": positive.get("surface_match"),
                    "positive_surface_score": positive.get("surface_score"),
                    "negative_surface_match": negative.get("surface_match"),
                    "negative_surface_score": negative.get("surface_score"),
                    "surface_self_test_status": status,
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


def aggregate_action(kind: str, expectancy: float | None, repair_rows: int) -> str:
    if repair_rows:
        return "REPAIR_CODE_SURFACE_GROUP"
    if kind == "GEOMETRY_SCORER_EXECUTABLE_SURFACE":
        return (
            "KEEP_SCORER_CODE_SURFACE_GROUP"
            if expectancy is not None and expectancy > 0
            else "REDESIGN_SCORER_CODE_SURFACE_GROUP"
        )
    return (
        "KEEP_AVOID_CODE_SURFACE_GROUP"
        if expectancy is not None and expectancy > 0
        else "KILL_AVOID_CODE_SURFACE_GROUP"
    )


def aggregate_code_surface_rows(
    surface_rows: list[dict[str, Any]], self_test_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    status_by_surface = {
        row.get("input_geometry_table_code_surface_row_id"): row.get("surface_self_test_status")
        for row in self_test_rows
    }
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in surface_rows:
        grouped.setdefault(aggregate_key(row), []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        values = [float(row["cost_adjusted_simulated_r"]) for row in rows if row.get("cost_adjusted_simulated_r") is not None]
        event_keys = {
            normalized(row.get("input_replay_numeric_event_row_id") or row.get("input_geometry_repair_row_id"))
            for row in rows
        }
        event_keys.discard("")
        source_counts = Counter(normalized(row.get("source_file_sha256")) for row in rows)
        dominant_source_count = max(source_counts.values()) if source_counts else 0
        repair_rows = sum(
            1
            for row in rows
            if status_by_surface.get(row.get("geometry_table_code_surface_row_id"))
            != "GEOMETRY_CODE_SURFACE_SELF_TEST_PASS"
        )
        expectancy = avg(values)
        output.append(
            boundary_row(
                {
                    "aggregate_geometry_table_code_surface_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SURFACE-AGG-{len(output) + 1:05d}"
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
                    "self_test_repair_rows": repair_rows,
                    "effective_n": len(event_keys),
                    "duplicate_rows": len(rows) - len(event_keys),
                    "dominant_source_file_sha256": source_counts.most_common(1)[0][0] if source_counts else None,
                    "dominant_source_row_count": dominant_source_count,
                    "dominant_source_concentration": rounded(dominant_source_count / len(rows), 6),
                    "expectancy_cost_adjusted_simulated_r": expectancy,
                    "aggregate_code_surface_action": aggregate_action(key[0], expectancy, repair_rows),
                }
            )
        )
    return output


def system_code_surface_rows(
    scorer_rows: list[dict[str, Any]],
    avoid_rows: list[dict[str, Any]],
    self_test_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_rows = scorer_rows + avoid_rows
    actions = Counter(row.get("surface_action") for row in all_rows)
    tests = Counter(row.get("surface_self_test_status") for row in self_test_rows)
    aggregate_actions = Counter(row.get("aggregate_code_surface_action") for row in aggregate_rows)
    return [
        boundary_row(
            {
                "system_geometry_table_code_surface_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-SURFACE-SYSTEM-00001"
                ),
                "scorer_code_surface_rows": len(scorer_rows),
                "avoid_code_surface_rows": len(avoid_rows),
                "total_code_surface_rows": len(all_rows),
                "surface_self_test_rows": len(self_test_rows),
                "aggregate_code_surface_rows": len(aggregate_rows),
                "surface_action_counts": dict(sorted(actions.items())),
                "surface_self_test_status_counts": dict(sorted(tests.items())),
                "aggregate_code_surface_action_counts": dict(sorted(aggregate_actions.items())),
            }
        )
    ]
