"""Observation ledgers from held-replay geometry table execution rows."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


RUNTIME_REPLAY_GEOMETRY_TABLE_OBSERVATIONS_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_observations.py"
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
    output["runtime_replay_geometry_table_observations_surface"] = (
        RUNTIME_REPLAY_GEOMETRY_TABLE_OBSERVATIONS_SURFACE
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


def observation_signal(kind: str, cost_r: float | None, gap_fields: list[str]) -> str:
    if gap_fields:
        return "GEOMETRY_TABLE_OBSERVATION_SOURCE_GAP"
    if kind == "scorer":
        return (
            "GEOMETRY_SCORER_OBSERVATION_REPLAY_POSITIVE"
            if cost_r is not None and cost_r > 0
            else "GEOMETRY_SCORER_OBSERVATION_REPLAY_NONPOSITIVE"
        )
    return (
        "GEOMETRY_AVOID_OBSERVATION_REPLAY_USEFUL"
        if cost_r is not None and cost_r > 0
        else "GEOMETRY_AVOID_OBSERVATION_REPLAY_NOT_USEFUL"
    )


def observation_action(kind: str, cost_r: float | None, gap_fields: list[str]) -> str:
    if gap_fields:
        return "PRESERVE_ROW_LEVEL_SOURCE_GAP_FOR_REPAIR"
    if kind == "scorer":
        return (
            "RETAIN_BRANCH_LOCAL_SCORER_OBSERVATION"
            if cost_r is not None and cost_r > 0
            else "REDESIGN_BRANCH_LOCAL_SCORER_OBSERVATION"
        )
    return (
        "RETAIN_BRANCH_LOCAL_AVOID_INTELLIGENCE_OBSERVATION"
        if cost_r is not None and cost_r > 0
        else "KILL_BRANCH_LOCAL_AVOID_INTELLIGENCE_OBSERVATION"
    )


def observation_from_execution(row: dict[str, Any], kind: str, ordinal: int) -> dict[str, Any]:
    gap_fields = row.get("source_gap_fields") or []
    cost_r = as_float(row.get("cost_adjusted_simulated_r"))
    signal = observation_signal(kind, cost_r, gap_fields)
    action = observation_action(kind, cost_r, gap_fields)
    prefix = "SCORER" if kind == "scorer" else "AVOID"
    return boundary_row(
        {
            "geometry_table_observation_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-OBS-{prefix}-{ordinal:06d}"
            ),
            "input_geometry_table_execution_row_id": row.get("geometry_table_execution_row_id"),
            "input_geometry_table_row_id": row.get("input_geometry_table_row_id"),
            "input_geometry_implementation_row_id": row.get("input_geometry_implementation_row_id"),
            "input_geometry_repair_row_id": row.get("input_geometry_repair_row_id"),
            "input_performance_row_id": row.get("input_performance_row_id"),
            "input_replay_numeric_event_row_id": row.get("input_replay_numeric_event_row_id"),
            "observation_kind": kind,
            "branch": row.get("branch"),
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
            "source_gap_fields": gap_fields,
            "observation_signal": signal,
            "observation_action": action,
        }
    )


def scorer_observation_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        observation_from_execution(row, "scorer", index)
        for index, row in enumerate(execution_rows, start=1)
    ]


def avoid_observation_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        observation_from_execution(row, "avoid", index)
        for index, row in enumerate(execution_rows, start=1)
    ]


def source_gap_preservation_rows(observation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in observation_rows:
        fields = row.get("source_gap_fields") or []
        if not fields:
            continue
        output.append(
            boundary_row(
                {
                    "geometry_table_observation_source_gap_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-OBS-GAP-{len(output) + 1:06d}"
                    ),
                    "input_geometry_table_observation_row_id": row.get("geometry_table_observation_row_id"),
                    "input_geometry_table_execution_row_id": row.get("input_geometry_table_execution_row_id"),
                    "observation_kind": row.get("observation_kind"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "market_timeframe": row.get("market_timeframe"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "source_gap_fields": fields,
                    "source_gap_preservation_action": "PRESERVE_ROW_LEVEL_SOURCE_GAP_FOR_REPAIR",
                }
            )
        )
    return output


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("observation_kind")),
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


def aggregate_observation_action(kind: str, expectancy: float | None, gap_rows: int) -> str:
    if gap_rows:
        return "PRESERVE_SOURCE_GAP_OBSERVATION_GROUP"
    if kind == "scorer":
        return (
            "RETAIN_SCORER_OBSERVATION_GROUP"
            if expectancy is not None and expectancy > 0
            else "REDESIGN_SCORER_OBSERVATION_GROUP"
        )
    return (
        "RETAIN_AVOID_INTELLIGENCE_OBSERVATION_GROUP"
        if expectancy is not None and expectancy > 0
        else "KILL_AVOID_INTELLIGENCE_OBSERVATION_GROUP"
    )


def aggregate_observation_rows(observation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in observation_rows:
        grouped.setdefault(aggregate_key(row), []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        values = [float(row["cost_adjusted_simulated_r"]) for row in rows if row.get("cost_adjusted_simulated_r") is not None]
        wins = [value for value in values if value > 0]
        losses = [value for value in values if value < 0]
        event_keys = {
            normalized(row.get("input_replay_numeric_event_row_id") or row.get("input_geometry_repair_row_id"))
            for row in rows
        }
        event_keys.discard("")
        source_counts = Counter(normalized(row.get("source_file_sha256")) for row in rows)
        dominant_source_count = max(source_counts.values()) if source_counts else 0
        expectancy = avg(values)
        gap_rows = sum(1 for row in rows if row.get("source_gap_fields"))
        output.append(
            boundary_row(
                {
                    "aggregate_geometry_table_observation_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-OBS-AGG-{len(output) + 1:05d}"
                    ),
                    "observation_kind": key[0],
                    "family": key[1],
                    "symbol": key[2],
                    "route_session": key[3],
                    "market_timeframe": key[4],
                    "horizon_id": key[5],
                    "source_component": key[6],
                    "default_off_avoid_class": key[7],
                    "row_count": len(rows),
                    "source_gap_rows": gap_rows,
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
                    "aggregate_observation_action": aggregate_observation_action(key[0], expectancy, gap_rows),
                }
            )
        )
    return output


def system_observation_rows(
    scorer_rows: list[dict[str, Any]],
    avoid_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    gap_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_rows = scorer_rows + avoid_rows
    signals = Counter(row.get("observation_signal") for row in all_rows)
    actions = Counter(row.get("observation_action") for row in all_rows)
    aggregate_actions = Counter(row.get("aggregate_observation_action") for row in aggregate_rows)
    return [
        boundary_row(
            {
                "system_geometry_table_observation_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-OBS-SYSTEM-00001"
                ),
                "scorer_observation_rows": len(scorer_rows),
                "avoid_observation_rows": len(avoid_rows),
                "total_observation_rows": len(all_rows),
                "aggregate_observation_rows": len(aggregate_rows),
                "source_gap_preservation_rows": len(gap_rows),
                "observation_signal_counts": dict(sorted(signals.items())),
                "observation_action_counts": dict(sorted(actions.items())),
                "aggregate_observation_action_counts": dict(sorted(aggregate_actions.items())),
            }
        )
    ]
