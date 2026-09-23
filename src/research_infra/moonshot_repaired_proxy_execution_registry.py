"""Branch-local registry over repaired-proxy execution specs."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Iterable


EXECUTION_REGISTRY_SURFACE = "src/research_infra/moonshot_repaired_proxy_execution_registry.py"
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
    output["execution_registry_surface"] = EXECUTION_REGISTRY_SURFACE
    output["research_boundary"] = research_boundary()
    return output

def score_values(rows: Iterable[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = to_float(row.get(field))
        if value is not None:
            values.append(value)
    return values


def score_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = score_values(rows, field)
    return {
        "score_count": len(values),
        "score_mean": round(mean(values), 10) if values else None,
        "score_min": min(values) if values else None,
        "score_max": max(values) if values else None,
    }


def group_by_scope(rows: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[aggregate_scope_key(row)].append(row)
    return dict(grouped)


def default_off_scope_registry_rows(spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, (key, rows) in enumerate(sorted(group_by_scope(spec_rows).items()), 1):
        first = rows[0]
        summary = score_summary(rows, "score_value")
        output.append(
            boundary_row(
                {
                    "default_off_scope_registry_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-EXEC-DEFAULT-SCOPE-{index:05d}"
                    ),
                    "registry_family": "default_off_repaired_proxy_scorer",
                    "aggregate_scope_key": key,
                    "symbol": first.get("symbol"),
                    "route_session": first.get("route_session"),
                    "horizon_id": first.get("horizon_id"),
                    "source_component": first.get("source_component"),
                    "input_spec_rows": len(rows),
                    "input_first_spec_id": rows[0].get("default_off_scorer_spec_id"),
                    "input_last_spec_id": rows[-1].get("default_off_scorer_spec_id"),
                    "required_guards": sorted(
                        {guard for row in rows for guard in (row.get("required_guards") or [])}
                    ),
                    "branch_local_registration_status": "DEFAULT_OFF_SCORER_SCOPE_REGISTERED",
                    "registration_action": "REGISTER_SCOPE_DEFAULT_OFF_REPAIRED_PROXY_SCORER",
                    "score_formula": "scope_score_mean := mean(event score_value)",
                    **summary,
                }
            )
        )
    return output


def avoid_scope_registry_rows(spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, (key, rows) in enumerate(sorted(group_by_scope(spec_rows).items()), 1):
        first = rows[0]
        summary = score_summary(rows, "comparator_score")
        output.append(
            boundary_row(
                {
                    "avoid_scope_registry_row_id": f"OHLC-GTOS-REPAIRED-PROXY-EXEC-AVOID-SCOPE-{index:05d}",
                    "registry_family": "avoid_redesign_repaired_proxy_comparator",
                    "aggregate_scope_key": key,
                    "symbol": first.get("symbol"),
                    "route_session": first.get("route_session"),
                    "horizon_id": first.get("horizon_id"),
                    "source_component": first.get("source_component"),
                    "input_spec_rows": len(rows),
                    "input_first_spec_id": rows[0].get("avoid_comparator_spec_id"),
                    "input_last_spec_id": rows[-1].get("avoid_comparator_spec_id"),
                    "required_guards": sorted(
                        {guard for row in rows for guard in (row.get("required_guards") or [])}
                    ),
                    "branch_local_registration_status": "AVOID_REDESIGN_COMPARATOR_SCOPE_REGISTERED",
                    "registration_action": "REGISTER_SCOPE_AVOID_REDESIGN_REPAIRED_PROXY_COMPARATOR",
                    "score_formula": "scope_score_mean := mean(event comparator_score)",
                    **summary,
                }
            )
        )
    return output


def build_execution_registry(
    default_specs: list[dict[str, Any]],
    avoid_specs: list[dict[str, Any]],
    repair_tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    default_scopes = default_off_scope_registry_rows(default_specs)
    avoid_scopes = avoid_scope_registry_rows(avoid_specs)
    return {
        "execution_registry_surface": EXECUTION_REGISTRY_SURFACE,
        "research_boundary": research_boundary(),
        "default_specs_by_event": {
            str(row.get("input_repaired_proxy_event_application_row_id")): row for row in default_specs
        },
        "avoid_specs_by_event": {
            str(row.get("input_repaired_proxy_event_application_row_id")): row for row in avoid_specs
        },
        "repair_tasks_by_event": {
            str(row.get("input_repaired_proxy_event_application_row_id")): row for row in repair_tasks
        },
        "default_scopes_by_key": {row["aggregate_scope_key"]: row for row in default_scopes},
        "avoid_scopes_by_key": {row["aggregate_scope_key"]: row for row in avoid_scopes},
        "default_scope_rows": default_scopes,
        "avoid_scope_rows": avoid_scopes,
    }


def registry_symbol_counts(
    default_specs: list[dict[str, Any]],
    avoid_specs: list[dict[str, Any]],
    repair_tasks: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    symbols = sorted(
        {
            str(row.get("symbol") or "")
            for row in [*default_specs, *avoid_specs, *repair_tasks]
            if row.get("symbol")
        }
    )
    default_event_counts = Counter(str(row.get("symbol") or "") for row in default_specs)
    avoid_event_counts = Counter(str(row.get("symbol") or "") for row in avoid_specs)
    repair_event_counts = Counter(str(row.get("symbol") or "") for row in repair_tasks)
    default_scope_counts = Counter(
        str(row.get("symbol") or "") for row in default_off_scope_registry_rows(default_specs)
    )
    avoid_scope_counts = Counter(str(row.get("symbol") or "") for row in avoid_scope_registry_rows(avoid_specs))
    repair_scope_counts = Counter(
        str(row.get("symbol") or "")
        for row in {aggregate_scope_key(task): task for task in repair_tasks}.values()
    )
    return {
        symbol: {
            "default_event_rows": int(default_event_counts[symbol]),
            "avoid_event_rows": int(avoid_event_counts[symbol]),
            "repair_event_rows": int(repair_event_counts[symbol]),
            "default_scope_rows": int(default_scope_counts[symbol]),
            "avoid_scope_rows": int(avoid_scope_counts[symbol]),
            "repair_scope_rows": int(repair_scope_counts[symbol]),
        }
        for symbol in symbols
    }


def execution_event_application_row(
    bridge_row: dict[str, Any],
    registry: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    event_id = str(bridge_row.get("input_repaired_proxy_event_application_row_id") or "")
    default_spec = registry["default_specs_by_event"].get(event_id)
    avoid_spec = registry["avoid_specs_by_event"].get(event_id)
    repair_task = registry["repair_tasks_by_event"].get(event_id)
    if default_spec is not None:
        status = "EXECUTION_REGISTRY_DEFAULT_OFF_SCORER_EVENT_REGISTERED"
        action = "APPLY_BRANCH_LOCAL_DEFAULT_OFF_SCORER_SPEC"
        family = "default_off_repaired_proxy_scorer"
        spec_id = default_spec.get("default_off_scorer_spec_id")
        emitted_score = to_float(default_spec.get("score_value"))
    elif avoid_spec is not None:
        status = "EXECUTION_REGISTRY_AVOID_REDESIGN_COMPARATOR_EVENT_REGISTERED"
        action = "APPLY_BRANCH_LOCAL_AVOID_REDESIGN_COMPARATOR_SPEC"
        family = "avoid_redesign_repaired_proxy_comparator"
        spec_id = avoid_spec.get("avoid_comparator_spec_id")
        emitted_score = to_float(avoid_spec.get("comparator_score"))
    elif repair_task is not None:
        status = "EXECUTION_REGISTRY_REPAIR_TASK_EVENT_REGISTERED"
        action = "EXECUTE_SOURCE_OR_BROKER_GEOMETRY_REPAIR_TASK"
        family = "source_or_broker_geometry_repair"
        spec_id = repair_task.get("repair_task_id")
        emitted_score = None
    else:
        status = "EXECUTION_REGISTRY_EVENT_HAS_NO_SPEC_MATCH"
        action = "RECHECK_SPEC_DENOMINATOR_JOIN"
        family = "unmatched_context"
        spec_id = None
        emitted_score = None
    key = aggregate_scope_key(bridge_row)
    exact_value = to_float(bridge_row.get("exact_r_value"))
    return boundary_row(
        {
            "execution_registry_application_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-EXEC-REGISTRY-APP-{index:06d}"
            ),
            "input_exact_proxy_bridge_row_id": bridge_row.get("exact_proxy_bridge_row_id"),
            "input_repaired_proxy_event_application_row_id": event_id,
            "input_registry_spec_id": spec_id,
            "aggregate_scope_key": key,
            "symbol": bridge_row.get("symbol"),
            "route_session": bridge_row.get("route_session"),
            "horizon_id": bridge_row.get("horizon_id"),
            "primitive_flag": bridge_row.get("primitive_flag"),
            "source_component": bridge_row.get("source_component"),
            "registry_family": family,
            "execution_registry_status": status,
            "execution_registry_action": action,
            "emitted_repaired_proxy_score": emitted_score,
            "gross_proxy_r": to_float(bridge_row.get("gross_proxy_r")),
            "net_proxy_r": to_float(bridge_row.get("net_proxy_r")),
            "stress_proxy_r": to_float(bridge_row.get("stress_proxy_r")),
            "cost_mean_r": to_float(bridge_row.get("cost_mean_r")),
            "cost_stress_r": to_float(bridge_row.get("cost_stress_r")),
            "exact_r_available_in_current_bridge": exact_value is not None,
            "exact_r_value": exact_value,
            "exact_r_status": bridge_row.get("exact_r_status"),
            "direct_identifier_match_count": bridge_row.get("direct_identifier_match_count"),
            "direct_exact_r_match_count": bridge_row.get("direct_exact_r_match_count"),
        }
    )


def avoid_comparator_execution_row(
    avoid_spec: dict[str, Any],
    default_scope_row: dict[str, Any] | None,
    bridge_row: dict[str, Any] | None,
    index: int,
) -> dict[str, Any]:
    score = to_float(avoid_spec.get("comparator_score"))
    default_mean = to_float((default_scope_row or {}).get("score_mean"))
    if score is None:
        status = "AVOID_COMPARATOR_RECHECK_NO_NUMERIC_SCORE"
    elif score < 0 and default_scope_row is not None:
        status = "AVOID_COMPARATOR_CONFIRMED_NEGATIVE_PROXY_WITH_DEFAULT_SCOPE_CONTEXT"
    elif score < 0:
        status = "AVOID_COMPARATOR_CONFIRMED_NEGATIVE_PROXY_WITHOUT_DEFAULT_SCOPE_CONTEXT"
    else:
        status = "AVOID_COMPARATOR_REDESIGN_REVIEW_NONNEGATIVE_PROXY"
    return boundary_row(
        {
            "avoid_comparator_execution_row_id": f"OHLC-GTOS-REPAIRED-PROXY-EXEC-AVOID-CMP-{index:06d}",
            "input_avoid_comparator_spec_id": avoid_spec.get("avoid_comparator_spec_id"),
            "input_repaired_proxy_event_application_row_id": avoid_spec.get(
                "input_repaired_proxy_event_application_row_id"
            ),
            "input_exact_proxy_bridge_row_id": (bridge_row or {}).get("exact_proxy_bridge_row_id"),
            "same_scope_default_registry_row_id": (default_scope_row or {}).get(
                "default_off_scope_registry_row_id"
            ),
            "aggregate_scope_key": aggregate_scope_key(avoid_spec),
            "symbol": avoid_spec.get("symbol"),
            "route_session": avoid_spec.get("route_session"),
            "horizon_id": avoid_spec.get("horizon_id"),
            "primitive_flag": avoid_spec.get("primitive_flag"),
            "source_component": avoid_spec.get("source_component"),
            "comparator_score": score,
            "same_scope_default_score_mean": default_mean,
            "score_minus_same_scope_default": (
                round(score - default_mean, 10) if score is not None and default_mean is not None else None
            ),
            "net_proxy_r": to_float((bridge_row or {}).get("net_proxy_r")),
            "stress_proxy_r": to_float((bridge_row or {}).get("stress_proxy_r")),
            "avoid_comparator_execution_status": status,
            "comparator_registration_action": "REGISTER_BRANCH_LOCAL_AVOID_REDESIGN_COMPARATOR_EXECUTION",
        }
    )


def repair_execution_row(task_row: dict[str, Any], index: int) -> dict[str, Any]:
    direct_keys = task_row.get("direct_search_keys_present") or {}
    exact_value = to_float(task_row.get("exact_value_after_streamed_sources"))
    if exact_value is not None:
        status = "REPAIR_EXECUTION_EXACT_VALUE_RECOVERED_FROM_STREAMED_SOURCE"
    elif direct_keys:
        status = "REPAIR_EXECUTION_DIRECT_IDENTIFIER_PRESENT_RETRY_EXACT_JOIN"
    else:
        status = "REPAIR_EXECUTION_DIRECT_IDENTIFIER_ABSENT_AFTER_LOCAL_SOURCE_SEARCH"
    return boundary_row(
        {
            "repair_execution_row_id": f"OHLC-GTOS-REPAIRED-PROXY-EXEC-REPAIR-{index:05d}",
            "input_repair_task_id": task_row.get("repair_task_id"),
            "input_repaired_proxy_event_application_row_id": task_row.get(
                "input_repaired_proxy_event_application_row_id"
            ),
            "aggregate_scope_key": aggregate_scope_key(task_row),
            "symbol": task_row.get("symbol"),
            "route_session": task_row.get("route_session"),
            "horizon_id": task_row.get("horizon_id"),
            "primitive_flag": task_row.get("primitive_flag"),
            "source_component": task_row.get("source_component"),
            "repair_path": task_row.get("repair_path"),
            "repair_execution_status": status,
            "exact_value_after_streamed_sources": exact_value,
            "exact_join_status_after_streamed_sources": task_row.get("exact_join_status_after_streamed_sources"),
            "direct_search_key_count": len(direct_keys),
            "missing_geometry_or_identifier_fields": task_row.get("missing_geometry_or_identifier_fields") or [],
            "source_search_observation_counts": task_row.get("source_search_observation_counts") or {},
            "next_repair_action": "REBUILD_DIRECT_IDENTIFIER_FROM_SYMBOL_TIME_LIFECYCLE_OR_TRADE_RECORD",
        }
    )


def market_replay_population_row(
    market_row: dict[str, Any],
    symbol_counts: dict[str, dict[str, int]],
    index: int,
) -> dict[str, Any]:
    symbol = str(market_row.get("symbol") or "")
    counts = symbol_counts.get(symbol, {})
    registered_events = int(counts.get("default_event_rows", 0)) + int(counts.get("avoid_event_rows", 0))
    repair_events = int(counts.get("repair_event_rows", 0))
    timeframe = str(market_row.get("timeframe") or "")
    row_count = int(market_row.get("row_count") or 0)
    if registered_events and timeframe == "M15":
        action = "MATERIALIZE_SYMBOL_M15_REPLAY_NUMERIC_POPULATION"
    elif registered_events:
        action = "MATERIALIZE_SYMBOL_CONTEXT_TIMEFRAME_POPULATION"
    elif repair_events:
        action = "MATERIALIZE_REPAIR_SCOPE_SOURCE_POPULATION"
    else:
        action = "USE_AS_CROSS_MARKET_CONTROL_OR_TRANSFER_POPULATION"
    return boundary_row(
        {
            "market_replay_population_row_id": f"OHLC-GTOS-REPAIRED-PROXY-EXEC-MARKET-REPLAY-{index:05d}",
            "input_market_population_row_id": market_row.get("market_population_row_id"),
            "symbol": symbol,
            "timeframe": timeframe,
            "source_path": market_row.get("source_path"),
            "source_sha256": market_row.get("sha256"),
            "source_row_count": row_count,
            "first_time": market_row.get("first_time"),
            "last_time": market_row.get("last_time"),
            "registered_default_event_rows_for_symbol": int(counts.get("default_event_rows", 0)),
            "registered_avoid_event_rows_for_symbol": int(counts.get("avoid_event_rows", 0)),
            "repair_event_rows_for_symbol": repair_events,
            "registered_default_scope_rows_for_symbol": int(counts.get("default_scope_rows", 0)),
            "registered_avoid_scope_rows_for_symbol": int(counts.get("avoid_scope_rows", 0)),
            "repair_scope_rows_for_symbol": int(counts.get("repair_scope_rows", 0)),
            "source_parse_ready": bool(row_count and market_row.get("sha256")),
            "market_replay_population_action": action,
        }
    )


def bucket_rows(named_rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    specs = [
        ("registry_application_status", "event_applications", "execution_registry_status"),
        ("registry_application_family", "event_applications", "registry_family"),
        ("avoid_comparator_status", "avoid_comparators", "avoid_comparator_execution_status"),
        ("repair_execution_status", "repair_executions", "repair_execution_status"),
        ("market_population_action", "market_populations", "market_replay_population_action"),
    ]
    for family, row_group, field in specs:
        rows = named_rows.get(row_group, [])
        counter = Counter(str(row.get(field) or "") for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "execution_registry_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-EXEC-REG-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
