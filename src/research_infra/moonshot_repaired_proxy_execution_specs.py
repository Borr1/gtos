"""Branch-local executable specs over repaired proxy scorer outputs."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


EXECUTION_SPEC_SURFACE = "src/research_infra/moonshot_repaired_proxy_execution_specs.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"


def to_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def aggregate_scope_key(row: dict[str, Any]) -> str:
    existing = row.get("aggregate_scope_key")
    if existing:
        return str(existing)
    return "|".join(
        f"{field}={row.get(field) or ''}"
        for field in ("symbol", "route_session", "horizon_id", "source_component")
    )


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["research_boundary"] = research_boundary()
    output["execution_spec_surface"] = EXECUTION_SPEC_SURFACE
    return output


def default_off_scorer_spec_from_event(row: dict[str, Any], index: int) -> dict[str, Any]:
    score = to_float(row.get("repaired_proxy_event_score"))
    return boundary_row(
        {
            "default_off_scorer_spec_id": f"OHLC-GTOS-REPAIRED-PROXY-DEFAULT-SPEC-{index:06d}",
            "input_repaired_proxy_event_application_row_id": row.get("repaired_proxy_event_application_row_id"),
            "input_numeric_result_row_id": row.get("input_numeric_result_row_id"),
            "input_shadow_scorer_event_score_row_id": row.get("input_shadow_scorer_event_score_row_id"),
            "input_repaired_proxy_scope_registry_row_id": row.get("input_repaired_proxy_scope_registry_row_id"),
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "primitive_flag": row.get("primitive_flag"),
            "source_component": row.get("source_component"),
            "aggregate_scope_key": aggregate_scope_key(row),
            "score_value": score,
            "score_source": row.get("repaired_proxy_event_score_source"),
            "required_guards": list(row.get("required_guards") or []),
            "scorer_registration_action": "REGISTER_BRANCH_LOCAL_DEFAULT_OFF_REPAIRED_PROXY_SCORER",
            "scorer_formula": "score_value := repaired_proxy_event_score after source-repair guard evaluation",
            "runtime_score_allowed": False,
            "candidate_use_allowed_now": False,
            "unconditional_scalar_use_allowed": False,
        }
    )


def avoid_comparator_spec_from_event(row: dict[str, Any], index: int) -> dict[str, Any]:
    score = to_float(row.get("repaired_proxy_event_score"))
    comparator_direction = "avoid_or_redesign" if score is None or score < 0 else "redesign_review"
    return boundary_row(
        {
            "avoid_comparator_spec_id": f"OHLC-GTOS-REPAIRED-PROXY-AVOID-SPEC-{index:06d}",
            "input_repaired_proxy_event_application_row_id": row.get("repaired_proxy_event_application_row_id"),
            "input_numeric_result_row_id": row.get("input_numeric_result_row_id"),
            "input_shadow_scorer_event_score_row_id": row.get("input_shadow_scorer_event_score_row_id"),
            "input_repaired_proxy_scope_registry_row_id": row.get("input_repaired_proxy_scope_registry_row_id"),
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "primitive_flag": row.get("primitive_flag"),
            "source_component": row.get("source_component"),
            "aggregate_scope_key": aggregate_scope_key(row),
            "comparator_score": score,
            "score_source": row.get("repaired_proxy_event_score_source"),
            "required_guards": list(row.get("required_guards") or []),
            "comparator_direction": comparator_direction,
            "comparator_action": "REGISTER_BRANCH_LOCAL_AVOID_REDESIGN_COMPARATOR",
            "comparator_formula": "compare repaired proxy score against same-scope default-off and source-repair context",
            "runtime_score_allowed": False,
            "candidate_use_allowed_now": False,
            "unconditional_scalar_use_allowed": False,
        }
    )


def repair_task_from_event(
    row: dict[str, Any],
    exact_join_row: dict[str, Any] | None,
    source_counts: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    exact_join_row = exact_join_row or {}
    direct_keys = {
        key: row.get(key)
        for key in (
            "candidate_id",
            "strategy_id",
            "row_id",
            "decision_time_utc",
            "broker_symbol",
            "order",
            "order_ticket",
            "ticket",
            "deal",
            "deal_ticket",
            "position_id",
            "trade_id",
            "lifecycle_row_id",
            "account_truth_row_id",
            "broker_actual_r_row_id",
            "trade_record_row_id",
        )
        if row.get(key) not in (None, "")
    }
    symbolic_keys = {
        "input_numeric_result_row_id": row.get("input_numeric_result_row_id"),
        "input_shadow_scorer_event_score_row_id": row.get("input_shadow_scorer_event_score_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_component": row.get("source_component"),
        "aggregate_scope_key": aggregate_scope_key(row),
    }
    missing_fields = list(exact_join_row.get("exact_missing_field_proof") or [])
    return boundary_row(
        {
            "repair_task_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-TASK-{index:05d}",
            "input_repaired_proxy_event_application_row_id": row.get("repaired_proxy_event_application_row_id"),
            "input_numeric_result_row_id": row.get("input_numeric_result_row_id"),
            "input_repaired_proxy_scope_registry_row_id": row.get("input_repaired_proxy_scope_registry_row_id"),
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "source_component": row.get("source_component"),
            "primitive_flag": row.get("primitive_flag"),
            "aggregate_scope_key": aggregate_scope_key(row),
            "direct_search_keys_present": direct_keys,
            "symbolic_search_keys_present": symbolic_keys,
            "searched_key_families": [
                "candidate_id",
                "strategy_id",
                "row_id",
                "decision_time_utc",
                "symbol_or_broker_symbol",
                "order_ticket_deal_position",
                "lifecycle_row",
                "account_truth_row",
                "broker_actual_r_row",
                "trade_record_row",
            ],
            "exact_join_status_after_streamed_sources": exact_join_row.get("exact_broker_join_status"),
            "exact_value_after_streamed_sources": exact_join_row.get("exact_broker_r_value"),
            "missing_geometry_or_identifier_fields": missing_fields,
            "source_search_observation_counts": dict(source_counts),
            "repair_path": choose_repair_path(direct_keys, missing_fields, source_counts),
            "repair_action": "BUILD_ROW_LEVEL_SOURCE_OR_BROKER_GEOMETRY_REPAIR",
            "runtime_score_allowed": False,
            "candidate_use_allowed_now": False,
            "unconditional_scalar_use_allowed": False,
        }
    )


def choose_repair_path(
    direct_keys: dict[str, Any],
    missing_fields: list[str],
    source_counts: dict[str, Any],
) -> str:
    if direct_keys:
        return "RETRY_DIRECT_IDENTIFIER_JOIN_THEN_ATTACH_GEOMETRY"
    if source_counts.get("symbol_exact_r_rows", 0):
        return "REBUILD_DIRECT_IDENTIFIER_FROM_SYMBOL_TIME_LIFECYCLE_OR_TRADE_RECORD"
    if any("executed_" in field or "ticket" in field for field in missing_fields):
        return "ACQUIRE_OR_RECONSTRUCT_BROKER_EXECUTION_GEOMETRY"
    return "REBUILD_SOURCE_JOIN_KEYS_BEFORE_SCALAR_USE"


def exact_proxy_bridge_row(
    app_row: dict[str, Any],
    numeric_row: dict[str, Any] | None,
    exact_join_row: dict[str, Any] | None,
    symbol_cost: dict[str, Any] | None,
    index: int,
) -> dict[str, Any]:
    numeric_row = numeric_row or {}
    exact_join_row = exact_join_row or {}
    exact_value = to_float(exact_join_row.get("exact_broker_r_value"))
    proxy_value = first_float(
        app_row.get("repaired_proxy_event_score"),
        numeric_row.get("cost_stress_adjusted_proxy_r"),
        numeric_row.get("proxy_r_value"),
        numeric_row.get("shadow_score"),
    )
    cost_mean = to_float((symbol_cost or {}).get("mean_cost_r"))
    cost_stress = to_float((symbol_cost or {}).get("stress_cost_r"))
    net_proxy = round(proxy_value - cost_mean, 10) if proxy_value is not None and cost_mean is not None else proxy_value
    stress_proxy = (
        round(proxy_value - cost_stress, 10) if proxy_value is not None and cost_stress is not None else net_proxy
    )
    return boundary_row(
        {
            "exact_proxy_bridge_row_id": f"OHLC-GTOS-REPAIRED-PROXY-EXACT-PROXY-{index:06d}",
            "input_repaired_proxy_event_application_row_id": app_row.get("repaired_proxy_event_application_row_id"),
            "input_numeric_result_row_id": app_row.get("input_numeric_result_row_id"),
            "symbol": app_row.get("symbol"),
            "route_session": app_row.get("route_session"),
            "horizon_id": app_row.get("horizon_id"),
            "primitive_flag": app_row.get("primitive_flag"),
            "source_component": app_row.get("source_component"),
            "exact_r_status": exact_join_row.get("exact_broker_join_status") or numeric_row.get("exact_r_compute_status"),
            "exact_r_value": exact_value,
            "gross_proxy_r": proxy_value,
            "cost_proxy_source_count": int((symbol_cost or {}).get("cost_source_rows") or 0),
            "cost_mean_r": cost_mean,
            "cost_stress_r": cost_stress,
            "net_proxy_r": net_proxy,
            "stress_proxy_r": stress_proxy,
            "bridge_value_source": "exact_r" if exact_value is not None else "repaired_or_numeric_proxy_r",
            "searched_key_families": [
                "candidate_id",
                "strategy_id",
                "row_id",
                "decision_time_utc",
                "symbol_or_broker_symbol",
                "order_ticket_deal_position",
                "lifecycle_row",
                "account_truth_row",
                "broker_actual_r_row",
                "trade_record_row",
            ],
            "direct_identifier_match_count": int(exact_join_row.get("direct_identifier_match_count") or 0),
            "direct_exact_r_match_count": int(exact_join_row.get("direct_exact_r_match_count") or 0),
            "missing_fields": list(
                exact_join_row.get("exact_missing_field_proof")
                or numeric_row.get("exact_r_missing_fields")
                or []
            ),
            "runtime_score_allowed": False,
            "candidate_use_allowed_now": False,
            "unconditional_scalar_use_allowed": False,
        }
    )


def first_float(*values: Any) -> float | None:
    for value in values:
        parsed = to_float(value)
        if parsed is not None:
            return parsed
    return None


def cost_observation_from_source(row: dict[str, Any], source_path: str, index: int) -> dict[str, Any] | None:
    entry = first_float(row.get("entry_price"), row.get("requested_price"))
    stop = to_float(row.get("stop_loss"))
    if entry is None or stop is None:
        return None
    denominator = abs(entry - stop)
    if denominator <= 0:
        return None
    spread = abs(to_float(row.get("spread")) or to_float(row.get("spread_at_request")) or 0.0)
    slippage = abs(to_float(row.get("slippage_price")) or to_float(row.get("slippage_directional")) or 0.0)
    cost_r = round((spread + slippage) / denominator, 10)
    if cost_r < 0 or cost_r > 20:
        return None
    return boundary_row(
        {
            "cost_observation_id": f"OHLC-GTOS-REPAIRED-PROXY-COST-OBS-{index:05d}",
            "source_path": source_path,
            "source_symbol": row.get("symbol") or row.get("broker_symbol") or row.get("source_symbol"),
            "source_time_utc": row.get("timestamp_utc") or row.get("ts") or row.get("created_at_utc"),
            "entry_price": entry,
            "stop_loss": stop,
            "denominator_price_distance": denominator,
            "spread_price": spread,
            "slippage_price_abs": slippage,
            "cost_r": cost_r,
        }
    )


def summarize_cost_by_symbol(cost_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[float]] = {}
    for row in cost_rows:
        symbol = str(row.get("source_symbol") or "")
        value = to_float(row.get("cost_r"))
        if symbol and value is not None:
            grouped.setdefault(symbol, []).append(value)
    output = {}
    for symbol, values in grouped.items():
        values_sorted = sorted(values)
        stress_index = min(len(values_sorted) - 1, int(round((len(values_sorted) - 1) * 0.9)))
        output[symbol] = {
            "symbol": symbol,
            "cost_source_rows": len(values_sorted),
            "mean_cost_r": round(mean(values_sorted), 10),
            "stress_cost_r": round(values_sorted[stress_index], 10),
            "max_cost_r": round(max(values_sorted), 10),
        }
    return output


def market_population_row(
    source_path: str,
    symbol: str,
    timeframe: str | None,
    row_count: int,
    first_time: str | None,
    last_time: str | None,
    sha256: str | None,
    index: int,
) -> dict[str, Any]:
    return boundary_row(
        {
            "market_population_row_id": f"OHLC-GTOS-REPAIRED-PROXY-MARKET-POP-{index:05d}",
            "source_path": source_path,
            "symbol": symbol,
            "timeframe": timeframe,
            "row_count": row_count,
            "first_time": first_time,
            "last_time": last_time,
            "sha256": sha256,
            "population_action": "USE_AS_LOCAL_MARKET_EXPANSION_POPULATION",
        }
    )


def scope_summary_rows(rows: list[dict[str, Any]], row_id_name: str, prefix: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(aggregate_scope_key(row), []).append(row)
    output = []
    for index, (scope, group) in enumerate(sorted(groups.items()), 1):
        scores = [
            to_float(row.get("score_value") or row.get("comparator_score") or row.get("gross_proxy_r"))
            for row in group
        ]
        scores = [value for value in scores if value is not None]
        output.append(
            boundary_row(
                {
                    row_id_name: f"{prefix}-{index:05d}",
                    "aggregate_scope_key": scope,
                    "row_count": len(group),
                    "score_rows": len(scores),
                    "score_mean": round(mean(scores), 10) if scores else None,
                    "symbol": group[0].get("symbol"),
                    "route_session": group[0].get("route_session"),
                    "horizon_id": group[0].get("horizon_id"),
                    "source_component": group[0].get("source_component"),
                }
            )
        )
    return output


def bucket_rows(named_rowsets: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for rowset_name, source_rows in named_rowsets.items():
        for field in ("symbol", "route_session", "horizon_id", "source_component", "repair_path", "bridge_value_source"):
            counter = Counter(str(row.get(field)) for row in source_rows if row.get(field) not in (None, ""))
            for value, count in sorted(counter.items()):
                rows.append(
                    boundary_row(
                        {
                            "bucket_row_id": f"OHLC-GTOS-REPAIRED-PROXY-EXEC-BUCKET-{len(rows) + 1:05d}",
                            "rowset": rowset_name,
                            "bucket_field": field,
                            "bucket_value": value,
                            "row_count": int(count),
                        }
                    )
                )
    return rows
