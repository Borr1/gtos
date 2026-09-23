"""Rebuild exact/proxy bridge rows with replay score-rerun fields."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


SCORE_BRIDGE_SURFACE = "src/research_infra/moonshot_repaired_proxy_score_bridge_rebuild.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
SCOPE_JOIN_FIELDS = ("symbol", "route_session", "horizon_id", "source_component")


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
    output["score_bridge_surface"] = SCORE_BRIDGE_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def to_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: float | None, places: int = 10) -> float | None:
    return round(value, places) if value is not None else None


def aggregate_scope_key(row: dict[str, Any]) -> str:
    existing = row.get("aggregate_scope_key")
    if existing:
        return str(existing)
    return "|".join(
        f"{field}={row.get(field) or ''}"
        for field in ("symbol", "route_session", "horizon_id", "source_component")
    )


def normalized_scope_value(value: Any) -> str:
    return "" if value is None else str(value)


def scope_join_tuple(row: dict[str, Any], fields: tuple[str, ...] = SCOPE_JOIN_FIELDS) -> tuple[str, ...]:
    return tuple(normalized_scope_value(row.get(field)) for field in fields)


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = to_float(row.get(field))
        if value is not None:
            values.append(value)
    return values


def score_scope_summary_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in score_rows:
        grouped[aggregate_scope_key(row)].append(row)
    output: list[dict[str, Any]] = []
    for index, (key, rows) in enumerate(sorted(grouped.items()), 1):
        first = rows[0]
        scores = numeric_values(rows, "replay_rerun_score")
        modifiers = numeric_values(rows, "replay_context_modifier")
        output.append(
            boundary_row(
                {
                    "score_scope_summary_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-BRIDGE-SCOPE-{index:05d}",
                    "aggregate_scope_key": key,
                    "symbol": first.get("symbol"),
                    "route_session": first.get("route_session"),
                    "horizon_id": first.get("horizon_id"),
                    "source_component": first.get("source_component"),
                    "registry_family": first.get("registry_family"),
                    "score_rerun_rows": len(rows),
                    "score_count": len(scores),
                    "score_mean": round_or_none(mean(scores) if scores else None),
                    "score_min": min(scores) if scores else None,
                    "score_max": max(scores) if scores else None,
                    "context_modifier_mean": round_or_none(mean(modifiers) if modifiers else None),
                    "market_timeframe_count": len({str(row.get("market_timeframe") or "") for row in rows}),
                    "market_source_count": len({str(row.get("market_source_path") or "") for row in rows}),
                    "status_counts": dict(
                        sorted(Counter(str(row.get("replay_score_rerun_status") or "") for row in rows).items())
                    ),
                    "action_counts": dict(
                        sorted(Counter(str(row.get("replay_score_rerun_action") or "") for row in rows).items())
                    ),
                }
            )
        )
    return output


def scope_summary_lookup(scope_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("aggregate_scope_key") or ""): row for row in scope_rows}


def scope_summary_join_lookups(scope_rows: list[dict[str, Any]]) -> dict[str, dict[Any, dict[str, Any]]]:
    return {
        "aggregate_scope_key": scope_summary_lookup(scope_rows),
        "symbol_route_horizon_source": {scope_join_tuple(row): row for row in scope_rows},
    }


def select_scope_summary(
    bridge_row: dict[str, Any],
    lookups: dict[str, dict[Any, dict[str, Any]]],
) -> tuple[dict[str, Any] | None, str]:
    stored_key = str(bridge_row.get("aggregate_scope_key") or "")
    if stored_key:
        stored_match = lookups.get("aggregate_scope_key", {}).get(stored_key)
        if stored_match is not None:
            return stored_match, "stored_aggregate_scope_key"

    computed_key = aggregate_scope_key(bridge_row)
    computed_match = lookups.get("aggregate_scope_key", {}).get(computed_key)
    if computed_match is not None:
        return computed_match, "computed_aggregate_scope_key"

    tuple_match = lookups.get("symbol_route_horizon_source", {}).get(scope_join_tuple(bridge_row))
    if tuple_match is not None:
        return tuple_match, "symbol_route_horizon_source_tuple"

    return None, "no_replay_score_scope_match"


def score_context_index(net_proxy_r: float | None, score_mean: float | None) -> float | None:
    if net_proxy_r is None and score_mean is None:
        return None
    return round((net_proxy_r or 0.0) + 0.1 * (score_mean or 0.0), 10)


def rebuilt_bridge_row(
    bridge_row: dict[str, Any],
    scope_summary: dict[str, Any] | None,
    index: int,
    join_method: str | None = None,
) -> dict[str, Any]:
    net_proxy_r = to_float(bridge_row.get("net_proxy_r"))
    score_mean = to_float((scope_summary or {}).get("score_mean"))
    if scope_summary is None:
        status = "SCORE_BRIDGE_REBUILT_NO_REPLAY_SCORE_SCOPE_MATCH"
        action = "PRESERVE_ORIGINAL_EXACT_PROXY_BRIDGE_AND_RECHECK_SCOPE_JOIN"
    elif (scope_summary or {}).get("registry_family") == "source_or_broker_geometry_repair":
        status = "SCORE_BRIDGE_REBUILT_WITH_REPAIR_CONTEXT_SCOPE"
        action = "CARRY_REPAIR_CONTEXT_INTO_IDENTIFIER_GEOMETRY_REPAIR"
    else:
        status = "SCORE_BRIDGE_REBUILT_WITH_REPLAY_SCORE_SCOPE"
        action = "USE_SCORE_FIELDS_FOR_BRANCH_LOCAL_COMPARATOR_PACKET"
    return boundary_row(
        {
            "score_rebuilt_bridge_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-BRIDGE-{index:06d}",
            "input_exact_proxy_bridge_row_id": bridge_row.get("exact_proxy_bridge_row_id"),
            "input_repaired_proxy_event_application_row_id": bridge_row.get(
                "input_repaired_proxy_event_application_row_id"
            ),
            "input_score_scope_summary_row_id": (scope_summary or {}).get("score_scope_summary_row_id"),
            "score_scope_join_method": join_method
            or ("direct_scope_summary_argument" if scope_summary is not None else "no_replay_score_scope_match"),
            "aggregate_scope_key": aggregate_scope_key(bridge_row),
            "symbol": bridge_row.get("symbol"),
            "route_session": bridge_row.get("route_session"),
            "horizon_id": bridge_row.get("horizon_id"),
            "primitive_flag": bridge_row.get("primitive_flag"),
            "source_component": bridge_row.get("source_component"),
            "gross_proxy_r": to_float(bridge_row.get("gross_proxy_r")),
            "net_proxy_r": net_proxy_r,
            "stress_proxy_r": to_float(bridge_row.get("stress_proxy_r")),
            "cost_mean_r": to_float(bridge_row.get("cost_mean_r")),
            "cost_stress_r": to_float(bridge_row.get("cost_stress_r")),
            "exact_r_value": to_float(bridge_row.get("exact_r_value")),
            "exact_r_status": bridge_row.get("exact_r_status"),
            "direct_identifier_match_count": bridge_row.get("direct_identifier_match_count"),
            "direct_exact_r_match_count": bridge_row.get("direct_exact_r_match_count"),
            "rerun_registry_family": (scope_summary or {}).get("registry_family"),
            "rerun_scope_score_rows": (scope_summary or {}).get("score_rerun_rows"),
            "rerun_scope_score_count": (scope_summary or {}).get("score_count"),
            "rerun_scope_score_mean": score_mean,
            "rerun_scope_score_min": (scope_summary or {}).get("score_min"),
            "rerun_scope_score_max": (scope_summary or {}).get("score_max"),
            "rerun_context_modifier_mean": (scope_summary or {}).get("context_modifier_mean"),
            "score_context_net_proxy_index": score_context_index(net_proxy_r, score_mean),
            "score_bridge_rebuild_status": status,
            "score_bridge_next_action": action,
        }
    )


def symbol_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    symbols = sorted({str(row.get("symbol") or "") for row in rows})
    for index, symbol in enumerate(symbols, 1):
        symbol_rows = [row for row in rows if str(row.get("symbol") or "") == symbol]
        indexes = numeric_values(symbol_rows, "score_context_net_proxy_index")
        output.append(
            boundary_row(
                {
                    "score_bridge_symbol_summary_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-BRIDGE-SYMBOL-{index:04d}",
                    "symbol": symbol,
                    "rebuilt_bridge_rows": len(symbol_rows),
                    "score_context_index_count": len(indexes),
                    "score_context_index_mean": round_or_none(mean(indexes) if indexes else None),
                    "status_counts": dict(
                        sorted(Counter(str(row.get("score_bridge_rebuild_status") or "") for row in symbol_rows).items())
                    ),
                    "action_counts": dict(
                        sorted(Counter(str(row.get("score_bridge_next_action") or "") for row in symbol_rows).items())
                    ),
                }
            )
        )
    return output


def bucket_rows(scope_rows: list[dict[str, Any]], bridge_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    specs = [
        ("scope_registry_family", scope_rows, "registry_family"),
        ("bridge_rebuild_status", bridge_rows, "score_bridge_rebuild_status"),
        ("bridge_next_action", bridge_rows, "score_bridge_next_action"),
        ("bridge_registry_family", bridge_rows, "rerun_registry_family"),
        ("score_scope_join_method", bridge_rows, "score_scope_join_method"),
        ("exact_r_status", bridge_rows, "exact_r_status"),
    ]
    for family, rows, field in specs:
        counter = Counter(str(row.get(field) or "") for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "score_bridge_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-SCORE-BRIDGE-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
