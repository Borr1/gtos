"""All-row replay performance decision matrix for geometry table recommendations."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from statistics import mean
from typing import Any


RUNTIME_REPLAY_GEOMETRY_TABLE_PERFORMANCE_MATRIX_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_performance_matrix.py"
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
    output["runtime_replay_geometry_table_performance_matrix_surface"] = (
        RUNTIME_REPLAY_GEOMETRY_TABLE_PERFORMANCE_MATRIX_SURFACE
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


def scope_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("branch")),
        normalized(row.get("family")),
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("follow_inverse_default_off_avoid_class")),
    )


def recommendation_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("input_replay_numeric_event_row_id")),
        normalized(row.get("family")),
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("default_off_avoid_class")),
        normalized(row.get("path_order_result")),
        normalized(row.get("source_file_sha256")),
    )


def broader_scope_key(row: dict[str, Any], include_source: bool = True) -> tuple[str, ...]:
    base = (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
    )
    if include_source:
        return (*base, normalized(row.get("source_component")))
    return base


def geometry_by_performance_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {normalized(row.get("input_performance_row_id")): row for row in rows}


def recommendation_queues(rows: list[dict[str, Any]]) -> dict[tuple[str, ...], deque[dict[str, Any]]]:
    queues: dict[tuple[str, ...], deque[dict[str, Any]]] = defaultdict(deque)
    for row in rows:
        queues[recommendation_key(row)].append(row)
    return queues


def broader_inventory_index(rows: list[dict[str, Any]]) -> tuple[dict[tuple[str, ...], list[dict[str, Any]]], dict[tuple[str, ...], list[dict[str, Any]]]]:
    exact: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    broad: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        exact[broader_scope_key(row, include_source=True)].append(row)
        broad[broader_scope_key(row, include_source=False)].append(row)
    return exact, broad


def broader_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(normalized(row.get("unified_decision_group")) for row in rows).items()))


def broader_actions(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({normalized(row.get("unified_action_class")) for row in rows if row.get("unified_action_class")})


def broader_status(row: dict[str, Any], exact_rows: list[dict[str, Any]], broad_rows: list[dict[str, Any]]) -> str:
    if exact_rows:
        return "BROADER_BRANCH_LOCAL_RECOMMENDATION_EXACT_SCOPE_PRESENT"
    if broad_rows:
        return "BROADER_BRANCH_LOCAL_RECOMMENDATION_BROAD_SCOPE_PRESENT"
    if row.get("source_component"):
        return "BROADER_BRANCH_LOCAL_RECOMMENDATION_SCOPE_NOT_PRESENT"
    return "BROADER_BRANCH_LOCAL_RECOMMENDATION_SCOPE_FIELDS_INCOMPLETE"


def result_class_from_value(value: float | None) -> str:
    if value is None:
        return "NO_FILL"
    if value > 0:
        return "WIN"
    if value < 0:
        return "LOSS"
    return "FLAT"


def row_decision(
    perf: dict[str, Any],
    geometry: dict[str, Any] | None,
    recommendation: dict[str, Any] | None,
) -> str:
    if recommendation and recommendation.get("recommendation_kind") == "KEEP_BRANCH_LOCAL_SCORER_RECOMMENDATION":
        return "IMPLEMENT_BRANCH_LOCAL_SCORER_FROM_REPLAY_GEOMETRY_TABLE"
    if recommendation and recommendation.get("recommendation_kind") == "KEEP_BRANCH_LOCAL_AVOID_INTELLIGENCE_RECOMMENDATION":
        return "CARRY_AS_AVOID_INTELLIGENCE_FROM_REPLAY_GEOMETRY_TABLE"
    decision = normalized((geometry or {}).get("geometry_repair_decision"))
    if decision == "KILL_AVOID_COMPARATOR_FROM_GEOMETRY":
        return "KILL_AVOID_COMPARATOR_FROM_REPLAY_GEOMETRY"
    if decision == "KILL_DEFAULT_OFF_FROM_GEOMETRY":
        return "KILL_DEFAULT_OFF_FROM_REPLAY_GEOMETRY"
    if decision == "REDESIGN_AVOID_COMPARATOR_FROM_GEOMETRY":
        return "REDESIGN_AVOID_COMPARATOR_FROM_REPLAY_GEOMETRY"
    if decision == "REDESIGN_DEFAULT_OFF_FROM_GEOMETRY":
        return "REDESIGN_DEFAULT_OFF_FROM_REPLAY_GEOMETRY"
    if decision == "CONCRETE_REPLAY_SOURCE_REPAIR_REQUIRED":
        return "NEEDS_CONCRETE_REPLAY_SOURCE_REPAIR"
    if decision == "CONCRETE_INTRABAR_PATH_REPLAY_REQUIRED":
        return "NEEDS_CONCRETE_INTRABAR_REPLAY_IMPLEMENTATION"
    disposition = normalized(perf.get("row_disposition"))
    if disposition.startswith("KILL_AVOID"):
        return "KILL_AVOID_COMPARATOR_FROM_PERFORMANCE_PROXY"
    if disposition.startswith("KILL_BRANCH_LOCAL"):
        return "KILL_DEFAULT_OFF_FROM_PERFORMANCE_PROXY"
    if disposition.startswith("REDESIGN"):
        return "REDESIGN_FROM_PERFORMANCE_PROXY"
    return "NEEDS_CONCRETE_REPLAY_IMPLEMENTATION"


def matrix_row(
    perf: dict[str, Any],
    geometry: dict[str, Any] | None,
    recommendation: dict[str, Any] | None,
    broader_exact_rows: list[dict[str, Any]],
    broader_broad_rows: list[dict[str, Any]],
    sequence: int,
) -> dict[str, Any]:
    source = geometry or perf
    gross_r = as_float((geometry or {}).get("action_adjusted_geometry_r"))
    cost_r = as_float((geometry or {}).get("cost_adjusted_geometry_r"))
    stress_r = as_float((geometry or {}).get("stress_geometry_r"))
    if gross_r is None:
        gross_r = as_float(perf.get("gross_simulated_r"))
    if cost_r is None:
        cost_r = as_float(perf.get("cost_adjusted_simulated_r"))
    if stress_r is None:
        stress_r = as_float(perf.get("stress_simulated_r"))
    result_class = normalized((geometry or {}).get("geometry_result_class")) or result_class_from_value(cost_r)
    chosen_broader = broader_exact_rows if broader_exact_rows else broader_broad_rows
    output = {
        "performance_matrix_row_id": (
            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-PERF-MATRIX-ROW-{sequence:06d}"
        ),
        "input_performance_row_id": perf.get("performance_row_id"),
        "input_geometry_repair_row_id": (geometry or {}).get("geometry_repair_row_id"),
        "input_geometry_table_recommendation_row_id": (recommendation or {}).get(
            "geometry_table_recommendation_row_id"
        ),
        "input_replay_numeric_event_row_id": perf.get("input_replay_numeric_event_row_id"),
        "branch": perf.get("branch"),
        "family": perf.get("family"),
        "symbol": perf.get("symbol"),
        "route_session": perf.get("route_session"),
        "market_timeframe": perf.get("market_timeframe"),
        "horizon_id": perf.get("horizon_id"),
        "source_component": perf.get("source_component"),
        "side": perf.get("side"),
        "proxy_trade_direction": (geometry or {}).get("proxy_trade_direction"),
        "follow_inverse_default_off_avoid_class": perf.get("follow_inverse_default_off_avoid_class"),
        "default_off_avoid_class": perf.get("default_off_avoid_class"),
        "entry_reference": (recommendation or {}).get("entry_reference") or perf.get("entry_reference"),
        "entry_reference_type": "GEOMETRY_TABLE_RECOMMENDATION" if recommendation else perf.get("entry_reference_type"),
        "source_path": source.get("source_path"),
        "source_file_sha256": source.get("source_file_sha256"),
        "proxy_entry_price": (geometry or {}).get("proxy_entry_price"),
        "proxy_stop_price": (geometry or {}).get("proxy_stop_price"),
        "proxy_target_price": (geometry or {}).get("proxy_target_price"),
        "stop_target_or_proxy_denominator_field": perf.get("stop_target_or_proxy_denominator_field"),
        "stop_target_or_proxy_denominator_value": perf.get("stop_target_or_proxy_denominator_value"),
        "proxy_denominator_pct": (geometry or {}).get("proxy_denominator_pct"),
        "proxy_denominator_price": (geometry or {}).get("proxy_denominator_price"),
        "path_order_result": source.get("path_order_result"),
        "path_scan_status": (geometry or {}).get("path_scan_status"),
        "fill_status": source.get("fill_status"),
        "first_touch_time": (geometry or {}).get("first_touch_time"),
        "first_touch_bar_index": (geometry or {}).get("first_touch_bar_index"),
        "gross_simulated_r": rounded(gross_r),
        "cost_adjustment_r": rounded(as_float(source.get("cost_adjustment_r"))),
        "cost_adjusted_simulated_r": rounded(cost_r),
        "stress_simulated_r": rounded(stress_r),
        "proxy_aggregate_gross_simulated_r": perf.get("gross_simulated_r"),
        "proxy_aggregate_cost_adjusted_simulated_r": perf.get("cost_adjusted_simulated_r"),
        "proxy_aggregate_stress_simulated_r": perf.get("stress_simulated_r"),
        "result_class": result_class,
        "win_count": 1 if result_class == "WIN" else 0,
        "loss_count": 1 if result_class == "LOSS" else 0,
        "flat_count": 1 if result_class == "FLAT" else 0,
        "no_fill_count": 1 if result_class == "NO_FILL" else 0,
        "target_first_count": int(source.get("target_first_count") or 0),
        "stop_first_count": int(source.get("stop_first_count") or 0),
        "neither_count": int(source.get("neither_count") or 0),
        "ambiguous_count": int(source.get("ambiguous_count") or 0),
        "duplicate_key": perf.get("duplicate_key"),
        "effective_n_key": perf.get("effective_n_key") or perf.get("input_replay_numeric_event_row_id"),
        "recommendation_kind": (recommendation or {}).get("recommendation_kind"),
        "recommendation_action": (recommendation or {}).get("recommendation_action"),
        "surface_function": (recommendation or {}).get("surface_function"),
        "surface_score": (recommendation or {}).get("surface_score"),
        "geometry_repair_decision": (geometry or {}).get("geometry_repair_decision"),
        "performance_row_disposition": perf.get("row_disposition"),
        "broader_recommendation_scope_status": broader_status(perf, broader_exact_rows, broader_broad_rows),
        "broader_recommendation_exact_scope_rows": len(broader_exact_rows),
        "broader_recommendation_broad_scope_rows": len(broader_broad_rows),
        "broader_recommendation_decision_group_counts": broader_counts(chosen_broader),
        "broader_recommendation_action_classes": broader_actions(chosen_broader),
        "remaining_exact_geometry_fields": (geometry or {}).get("remaining_missing_geometry_fields")
        or perf.get("missing_simulated_fields")
        or [],
        "simulated_r_missing_fields": [] if cost_r is not None else (perf.get("missing_simulated_fields") or []),
    }
    output["simulated_r_missing_field_count"] = len(output["simulated_r_missing_fields"])
    output["keep_kill_redesign_implement_decision"] = row_decision(perf, geometry, recommendation)
    return boundary_row(output)


def add_scope_statistics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[scope_key(row)].append(row)
    total = len(rows) or 1
    for row in rows:
        members = grouped[scope_key(row)]
        effective_keys = {normalized(member.get("effective_n_key")) for member in members if member.get("effective_n_key")}
        row["scope_row_count"] = len(members)
        row["scope_effective_n"] = len(effective_keys)
        row["scope_duplicate_row_count"] = len(members) - len(effective_keys)
        row["scope_duplicate_inflation_ratio"] = rounded(len(members) / len(effective_keys)) if effective_keys else None
        row["scope_concentration_share_of_all_rows"] = rounded(len(members) / total)
    return rows


def performance_matrix_rows(
    performance_rows: list[dict[str, Any]],
    geometry_rows: list[dict[str, Any]],
    recommendation_rows: list[dict[str, Any]],
    broader_inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    geometry_index = geometry_by_performance_id(geometry_rows)
    recommendation_index = recommendation_queues(recommendation_rows)
    broader_exact_index, broader_broad_index = broader_inventory_index(broader_inventory_rows)
    output: list[dict[str, Any]] = []
    for perf in performance_rows:
        geometry = geometry_index.get(normalized(perf.get("performance_row_id")))
        rec_key_source = dict(perf)
        if geometry:
            rec_key_source.update(
                {
                    "path_order_result": geometry.get("path_order_result"),
                    "source_file_sha256": geometry.get("source_file_sha256"),
                }
            )
        queue = recommendation_index.get(recommendation_key(rec_key_source))
        recommendation = queue.popleft() if queue else None
        broader_exact_rows = broader_exact_index.get(broader_scope_key(perf, include_source=True), [])
        broader_broad_rows = broader_broad_index.get(broader_scope_key(perf, include_source=False), [])
        output.append(
            matrix_row(
                perf,
                geometry,
                recommendation,
                broader_exact_rows,
                broader_broad_rows,
                len(output) + 1,
            )
        )
    return add_scope_statistics(output)


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


def aggregate_matrix_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[aggregate_key(row)].append(row)
    total = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        gross_values = [as_float(row.get("gross_simulated_r")) for row in members]
        gross_values = [value for value in gross_values if value is not None]
        cost_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members]
        cost_values = [value for value in cost_values if value is not None]
        stress_values = [as_float(row.get("stress_simulated_r")) for row in members]
        stress_values = [value for value in stress_values if value is not None]
        win_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members if row.get("result_class") == "WIN"]
        loss_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members if row.get("result_class") == "LOSS"]
        effective_keys = {normalized(row.get("effective_n_key")) for row in members if row.get("effective_n_key")}
        path_counts = Counter(normalized(row.get("path_order_result")) for row in members)
        recommendation_counts = Counter(normalized(row.get("recommendation_kind")) or "NO_TABLE_RECOMMENDATION" for row in members)
        record = {
            "aggregate_performance_matrix_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-PERF-MATRIX-AGG-{len(output) + 1:05d}"
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
            "simulated_r_row_count": len(cost_values),
            "win_count": sum(int(row.get("win_count") or 0) for row in members),
            "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
            "flat_count": sum(int(row.get("flat_count") or 0) for row in members),
            "no_fill_count": sum(int(row.get("no_fill_count") or 0) for row in members),
            "expectancy_gross_simulated_r": rounded(average(gross_values)),
            "expectancy_cost_adjusted_simulated_r": rounded(average(cost_values)),
            "expectancy_stress_simulated_r": rounded(average(stress_values)),
            "average_win": rounded(average([value for value in win_values if value is not None])),
            "average_loss": rounded(average([value for value in loss_values if value is not None])),
            "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
            "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
            "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
            "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
            "effective_n": len(effective_keys),
            "duplicate_row_count": len(members) - len(effective_keys),
            "duplicate_inflation_ratio": rounded(len(members) / len(effective_keys)) if effective_keys else None,
            "concentration_share_of_all_rows": rounded(len(members) / total),
            "path_order_counts": dict(sorted(path_counts.items())),
            "recommendation_kind_counts": dict(sorted(recommendation_counts.items())),
            "broader_exact_scope_rows": sum(int(row.get("broader_recommendation_exact_scope_rows") or 0) for row in members),
            "broader_broad_scope_rows": sum(int(row.get("broader_recommendation_broad_scope_rows") or 0) for row in members),
        }
        output.append(boundary_row(record))
    return output


def simulated_missing_field_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if row.get("cost_adjusted_simulated_r") is not None:
            continue
        fields = row.get("simulated_r_missing_fields") or []
        if not fields:
            fields = ["cost_adjusted_simulated_r"]
        for field in fields:
            output.append(
                boundary_row(
                    {
                        "simulated_missing_field_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-PERF-MISSING-{len(output) + 1:06d}"
                        ),
                        "performance_matrix_row_id": row.get("performance_matrix_row_id"),
                        "input_performance_row_id": row.get("input_performance_row_id"),
                        "input_replay_numeric_event_row_id": row.get("input_replay_numeric_event_row_id"),
                        "missing_simulated_field": field,
                        "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
                        "symbol": row.get("symbol"),
                        "route_session": row.get("route_session"),
                        "market_timeframe": row.get("market_timeframe"),
                        "horizon_id": row.get("horizon_id"),
                        "source_component": row.get("source_component"),
                    }
                )
            )
    return output


def source_join_issue_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        issues: list[str] = []
        if not row.get("input_geometry_repair_row_id"):
            issues.append("MISSING_GEOMETRY_REPAIR_ROW")
        decision = normalized(row.get("geometry_repair_decision"))
        if decision in {
            "IMPLEMENT_BRANCH_LOCAL_REPLAY_GEOMETRY_PROTOTYPE",
            "CARRY_AS_AVOID_INTELLIGENCE_FROM_GEOMETRY",
        } and not row.get("input_geometry_table_recommendation_row_id"):
            issues.append("MISSING_GEOMETRY_TABLE_RECOMMENDATION_ROW")
        for issue in issues:
            output.append(
                boundary_row(
                    {
                        "source_join_issue_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-PERF-JOIN-{len(output) + 1:06d}"
                        ),
                        "performance_matrix_row_id": row.get("performance_matrix_row_id"),
                        "input_performance_row_id": row.get("input_performance_row_id"),
                        "issue": issue,
                        "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
                    }
                )
            )
    return output


def system_matrix_rows(
    rows: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    missing_rows: list[dict[str, Any]],
    join_issue_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in rows)
    aggregate_decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in aggregates)
    path_counts = Counter(row.get("path_order_result") for row in rows)
    return [
        boundary_row(
            {
                "system_performance_matrix_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-TABLE-PERF-MATRIX-SYSTEM-00001"
                ),
                "performance_matrix_rows": len(rows),
                "aggregate_performance_matrix_rows": len(aggregates),
                "simulated_missing_field_rows": len(missing_rows),
                "source_join_issue_rows": len(join_issue_rows),
                "rows_with_simulated_r": sum(row.get("cost_adjusted_simulated_r") is not None for row in rows),
                "rows_without_simulated_r": sum(row.get("cost_adjusted_simulated_r") is None for row in rows),
                "win_count": sum(int(row.get("win_count") or 0) for row in rows),
                "loss_count": sum(int(row.get("loss_count") or 0) for row in rows),
                "flat_count": sum(int(row.get("flat_count") or 0) for row in rows),
                "no_fill_count": sum(int(row.get("no_fill_count") or 0) for row in rows),
                "target_first_count": sum(int(row.get("target_first_count") or 0) for row in rows),
                "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in rows),
                "neither_count": sum(int(row.get("neither_count") or 0) for row in rows),
                "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in rows),
                "decision_counts": dict(sorted(decisions.items())),
                "aggregate_decision_counts": dict(sorted(aggregate_decisions.items())),
                "path_order_counts": dict(sorted(path_counts.items())),
            }
        )
    ]
