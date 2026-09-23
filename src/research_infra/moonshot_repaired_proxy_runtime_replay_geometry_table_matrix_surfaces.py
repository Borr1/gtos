"""Branch-local implementation surfaces from the replay performance matrix."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from statistics import mean
from typing import Any


RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACES_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surfaces.py"
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
    output["runtime_replay_geometry_table_matrix_surfaces_surface"] = (
        RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACES_SURFACE
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


def slug(value: Any) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", normalized(value).lower()).strip("_")
    return text or "blank"


def scope_fields() -> list[str]:
    return [
        "symbol",
        "route_session",
        "market_timeframe",
        "horizon_id",
        "source_component",
        "source_file_sha256",
        "path_order_result",
        "keep_kill_redesign_implement_decision",
    ]


def surface_scope_key(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field) for field in scope_fields()}


def event_matches_surface(surface: dict[str, Any], event: dict[str, Any]) -> bool:
    return all(normalized(surface.get(field)) == normalized(event.get(field)) for field in scope_fields())


def execute_matrix_surface(surface: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    matched = event_matches_surface(surface, event)
    return {
        "surface_match": matched,
        "surface_score": rounded(as_float(surface.get("surface_cost_adjusted_simulated_r"))) if matched else None,
        "surface_action": surface.get("surface_action") if matched else "PERFORMANCE_MATRIX_SURFACE_SCOPE_MISMATCH",
    }


def positive_event(surface: dict[str, Any]) -> dict[str, Any]:
    return surface_scope_key(surface)


def negative_event(surface: dict[str, Any]) -> dict[str, Any]:
    event = positive_event(surface)
    event["symbol"] = normalized(event.get("symbol")) + "_MISMATCH"
    return event


def surface_kind(row: dict[str, Any]) -> str | None:
    decision = normalized(row.get("keep_kill_redesign_implement_decision"))
    if decision == "IMPLEMENT_BRANCH_LOCAL_SCORER_FROM_REPLAY_GEOMETRY_TABLE":
        return "PERFORMANCE_MATRIX_SCORER_IMPLEMENTATION_SURFACE"
    if decision == "CARRY_AS_AVOID_INTELLIGENCE_FROM_REPLAY_GEOMETRY_TABLE":
        return "PERFORMANCE_MATRIX_AVOID_INTELLIGENCE_SURFACE"
    return None


def surface_action(kind: str | None) -> str:
    if kind == "PERFORMANCE_MATRIX_SCORER_IMPLEMENTATION_SURFACE":
        return "EMIT_BRANCH_LOCAL_SCORER_MATRIX_OBSERVATION"
    if kind == "PERFORMANCE_MATRIX_AVOID_INTELLIGENCE_SURFACE":
        return "EMIT_BRANCH_LOCAL_AVOID_MATRIX_OBSERVATION"
    return "NO_SURFACE_FOR_TERMINAL_MATRIX_DECISION"


def surface_function(row: dict[str, Any], prefix: str, ordinal: int) -> str:
    source_hash = normalized(row.get("source_file_sha256"))[:8] or "nohash"
    return "_".join(
        [
            "score",
            prefix.lower(),
            slug(row.get("symbol")),
            slug(row.get("route_session")),
            slug(row.get("market_timeframe")),
            slug(row.get("horizon_id")),
            slug(row.get("source_component")),
            source_hash,
            f"{ordinal:06d}",
        ]
    )


def common_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_performance_matrix_row_id": row.get("performance_matrix_row_id"),
        "input_performance_row_id": row.get("input_performance_row_id"),
        "input_geometry_repair_row_id": row.get("input_geometry_repair_row_id"),
        "input_geometry_table_recommendation_row_id": row.get("input_geometry_table_recommendation_row_id"),
        "input_replay_numeric_event_row_id": row.get("input_replay_numeric_event_row_id"),
        "branch": row.get("branch"),
        "family": row.get("family"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "market_timeframe": row.get("market_timeframe"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "side": row.get("side"),
        "proxy_trade_direction": row.get("proxy_trade_direction"),
        "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
        "default_off_avoid_class": row.get("default_off_avoid_class"),
        "entry_reference": row.get("entry_reference"),
        "source_path": row.get("source_path"),
        "source_file_sha256": row.get("source_file_sha256"),
        "path_order_result": row.get("path_order_result"),
        "fill_status": row.get("fill_status"),
        "proxy_entry_price": row.get("proxy_entry_price"),
        "proxy_stop_price": row.get("proxy_stop_price"),
        "proxy_target_price": row.get("proxy_target_price"),
        "stop_target_or_proxy_denominator_field": row.get("stop_target_or_proxy_denominator_field"),
        "stop_target_or_proxy_denominator_value": row.get("stop_target_or_proxy_denominator_value"),
        "gross_simulated_r": row.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": row.get("stress_simulated_r"),
        "result_class": row.get("result_class"),
        "win_count": int(row.get("win_count") or 0),
        "loss_count": int(row.get("loss_count") or 0),
        "flat_count": int(row.get("flat_count") or 0),
        "no_fill_count": int(row.get("no_fill_count") or 0),
        "target_first_count": int(row.get("target_first_count") or 0),
        "stop_first_count": int(row.get("stop_first_count") or 0),
        "neither_count": int(row.get("neither_count") or 0),
        "ambiguous_count": int(row.get("ambiguous_count") or 0),
        "effective_n_key": row.get("effective_n_key"),
        "scope_effective_n": row.get("scope_effective_n"),
        "scope_duplicate_row_count": row.get("scope_duplicate_row_count"),
        "scope_concentration_share_of_all_rows": row.get("scope_concentration_share_of_all_rows"),
        "broader_recommendation_scope_status": row.get("broader_recommendation_scope_status"),
        "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
    }


def surface_from_matrix_row(row: dict[str, Any], ordinal: int) -> dict[str, Any]:
    kind = surface_kind(row)
    prefix = "SCORER" if kind == "PERFORMANCE_MATRIX_SCORER_IMPLEMENTATION_SURFACE" else "AVOID"
    payload = common_payload(row)
    payload.update(
        {
            "matrix_surface_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-SURFACE-{prefix}-{ordinal:06d}"
            ),
            "matrix_surface_kind": kind,
            "surface_function": surface_function(row, prefix, ordinal),
            "surface_module": RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACES_SURFACE,
            "surface_action": surface_action(kind),
            "surface_cost_adjusted_simulated_r": rounded(as_float(row.get("cost_adjusted_simulated_r"))),
            "surface_scope_fields": scope_fields(),
            "production_import_permitted": False,
        }
    )
    return boundary_row(payload)


def scorer_surface_rows(matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [row for row in matrix_rows if surface_kind(row) == "PERFORMANCE_MATRIX_SCORER_IMPLEMENTATION_SURFACE"]
    return [surface_from_matrix_row(row, index) for index, row in enumerate(rows, start=1)]


def avoid_surface_rows(matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [row for row in matrix_rows if surface_kind(row) == "PERFORMANCE_MATRIX_AVOID_INTELLIGENCE_SURFACE"]
    return [surface_from_matrix_row(row, index) for index, row in enumerate(rows, start=1)]


def terminal_decision_rows(matrix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terminal = [row for row in matrix_rows if surface_kind(row) is None]
    output: list[dict[str, Any]] = []
    for row in terminal:
        payload = common_payload(row)
        payload.update(
            {
                "terminal_matrix_decision_row_id": (
                    f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-TERMINAL-{len(output) + 1:06d}"
                ),
                "terminal_action": row.get("keep_kill_redesign_implement_decision"),
                "terminal_reason": "PERFORMANCE_MATRIX_TERMINAL_DECISION_NO_BRANCH_LOCAL_SURFACE",
            }
        )
        output.append(boundary_row(payload))
    return output


def surface_self_test_rows(surface_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in surface_rows:
        positive = execute_matrix_surface(row, positive_event(row))
        negative = execute_matrix_surface(row, negative_event(row))
        status = (
            "PERFORMANCE_MATRIX_SURFACE_SELF_TEST_PASS"
            if positive.get("surface_match") is True
            and positive.get("surface_score") == row.get("surface_cost_adjusted_simulated_r")
            and negative.get("surface_match") is False
            and negative.get("surface_score") is None
            else "PERFORMANCE_MATRIX_SURFACE_SELF_TEST_REPAIR"
        )
        output.append(
            boundary_row(
                {
                    "matrix_surface_self_test_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-SURFACE-TEST-{len(output) + 1:06d}"
                    ),
                    "input_matrix_surface_row_id": row.get("matrix_surface_row_id"),
                    "matrix_surface_kind": row.get("matrix_surface_kind"),
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


def aggregate_surface_rows(
    scorer_rows: list[dict[str, Any]],
    avoid_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    self_test_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = scorer_rows + avoid_rows + terminal_rows
    test_status_by_surface = {
        row.get("input_matrix_surface_row_id"): row.get("surface_self_test_status") for row in self_test_rows
    }
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
        win_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members if row.get("result_class") == "WIN"]
        loss_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members if row.get("result_class") == "LOSS"]
        effective_keys = {normalized(row.get("effective_n_key")) for row in members if row.get("effective_n_key")}
        path_counts = Counter(normalized(row.get("path_order_result")) for row in members)
        surface_rows = [row for row in members if row.get("matrix_surface_row_id")]
        repair_rows = sum(
            1
            for row in surface_rows
            if test_status_by_surface.get(row.get("matrix_surface_row_id")) != "PERFORMANCE_MATRIX_SURFACE_SELF_TEST_PASS"
        )
        record = {
            "aggregate_matrix_surface_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-SURFACE-AGG-{len(output) + 1:05d}"
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
            "surface_row_count": len(surface_rows),
            "terminal_row_count": len(members) - len(surface_rows),
            "self_test_repair_rows": repair_rows,
            "expectancy_cost_adjusted_simulated_r": rounded(average(cost_values)),
            "expectancy_stress_simulated_r": rounded(average(stress_values)),
            "average_win": rounded(average([value for value in win_values if value is not None])),
            "average_loss": rounded(average([value for value in loss_values if value is not None])),
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
            "duplicate_inflation_ratio": rounded(len(members) / len(effective_keys)) if effective_keys else None,
            "concentration_share_of_all_rows": rounded(len(members) / total),
            "path_order_counts": dict(sorted(path_counts.items())),
        }
        output.append(boundary_row(record))
    return output


def system_surface_rows(
    scorer_rows: list[dict[str, Any]],
    avoid_rows: list[dict[str, Any]],
    terminal_rows: list[dict[str, Any]],
    self_test_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    all_surface_rows = scorer_rows + avoid_rows
    all_rows = all_surface_rows + terminal_rows
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in all_rows)
    tests = Counter(row.get("surface_self_test_status") for row in self_test_rows)
    path_counts = Counter(row.get("path_order_result") for row in all_rows)
    return [
        boundary_row(
            {
                "system_matrix_surface_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-MATRIX-SURFACE-SYSTEM-00001"
                ),
                "scorer_surface_rows": len(scorer_rows),
                "avoid_surface_rows": len(avoid_rows),
                "terminal_decision_rows": len(terminal_rows),
                "total_matrix_rows_consumed": len(all_rows),
                "surface_self_test_rows": len(self_test_rows),
                "aggregate_surface_rows": len(aggregate_rows),
                "surface_self_test_status_counts": dict(sorted(tests.items())),
                "decision_counts": dict(sorted(decisions.items())),
                "path_order_counts": dict(sorted(path_counts.items())),
            }
        )
    ]
