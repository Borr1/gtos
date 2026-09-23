"""Aggregate repaired-proxy score bridge rows into branch-local action packets."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


ACTION_PACKET_SURFACE = "src/research_infra/moonshot_repaired_proxy_score_bridge_action_packet.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
SCOPE_FIELDS = ("symbol", "route_session", "horizon_id", "source_component")


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
    output["action_packet_surface"] = ACTION_PACKET_SURFACE
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


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = to_float(row.get(field))
        if value is not None:
            values.append(value)
    return values


def group_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        *(normalized(row.get(field)) for field in SCOPE_FIELDS),
        normalized(row.get("rerun_registry_family")),
        normalized(row.get("score_bridge_rebuild_status")),
        normalized(row.get("score_bridge_next_action")),
    )


def action_scope_status(bridge_status: str) -> str:
    if bridge_status == "SCORE_BRIDGE_REBUILT_WITH_REPLAY_SCORE_SCOPE":
        return "ACTION_SCOPE_READY_FOR_SCORE_AUGMENTED_COMPARATOR_PACKET"
    if bridge_status == "SCORE_BRIDGE_REBUILT_WITH_REPAIR_CONTEXT_SCOPE":
        return "ACTION_SCOPE_READY_FOR_IDENTIFIER_GEOMETRY_REPAIR_ROUTING"
    return "ACTION_SCOPE_UNJOINED_SYSTEM_SCOPE_REQUIRES_SCOPE_REPAIR"


def action_scope_next_step(status: str) -> str:
    if status == "ACTION_SCOPE_READY_FOR_SCORE_AUGMENTED_COMPARATOR_PACKET":
        return "MATERIALIZE_BRANCH_LOCAL_COMPARATOR_PACKET_ROW"
    if status == "ACTION_SCOPE_READY_FOR_IDENTIFIER_GEOMETRY_REPAIR_ROUTING":
        return "ROUTE_TO_IDENTIFIER_GEOMETRY_REPAIR_QUEUE"
    return "ROUTE_TO_SCOPE_IDENTITY_REPAIR_QUEUE"


def action_scope_rows(bridge_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in bridge_rows:
        grouped[group_key(row)].append(row)

    output: list[dict[str, Any]] = []
    for index, (key, rows) in enumerate(sorted(grouped.items()), 1):
        symbol, route_session, horizon_id, source_component, registry_family, bridge_status, bridge_action = key
        indexes = numeric_values(rows, "score_context_net_proxy_index")
        net_values = numeric_values(rows, "net_proxy_r")
        gross_values = numeric_values(rows, "gross_proxy_r")
        status = action_scope_status(bridge_status)
        output.append(
            boundary_row(
                {
                    "action_scope_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-ACTION-SCOPE-{index:05d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "source_component": source_component,
                    "rerun_registry_family": registry_family,
                    "score_bridge_rebuild_status": bridge_status,
                    "score_bridge_next_action": bridge_action,
                    "action_scope_status": status,
                    "action_scope_next_step": action_scope_next_step(status),
                    "bridge_rows": len(rows),
                    "score_context_index_count": len(indexes),
                    "score_context_index_mean": round_or_none(mean(indexes) if indexes else None),
                    "score_context_index_min": min(indexes) if indexes else None,
                    "score_context_index_max": max(indexes) if indexes else None,
                    "net_proxy_r_count": len(net_values),
                    "net_proxy_r_mean": round_or_none(mean(net_values) if net_values else None),
                    "gross_proxy_r_count": len(gross_values),
                    "gross_proxy_r_mean": round_or_none(mean(gross_values) if gross_values else None),
                    "score_scope_summary_count": len(
                        {normalized(row.get("input_score_scope_summary_row_id")) for row in rows}
                        - {""}
                    ),
                    "primitive_flag_count": len({normalized(row.get("primitive_flag")) for row in rows} - {""}),
                    "exact_r_status_counts": dict(
                        sorted(Counter(normalized(row.get("exact_r_status")) for row in rows).items())
                    ),
                    "join_method_counts": dict(
                        sorted(Counter(normalized(row.get("score_scope_join_method")) for row in rows).items())
                    ),
                }
            )
        )
    return output


def comparator_packet_status(registry_family: str) -> str:
    if registry_family == "default_off_repaired_proxy_scorer":
        return "COMPARATOR_PACKET_DEFAULT_OFF_SCORER_CONTEXT_READY"
    if registry_family == "avoid_redesign_repaired_proxy_comparator":
        return "COMPARATOR_PACKET_AVOID_COMPARATOR_CONTEXT_READY"
    return "COMPARATOR_PACKET_NON_COMPARATOR_SCOPE_HELD_OUT"


def comparator_packet_rows(scope_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    ready_rows = [
        row
        for row in scope_rows
        if row.get("action_scope_status") == "ACTION_SCOPE_READY_FOR_SCORE_AUGMENTED_COMPARATOR_PACKET"
    ]
    for index, row in enumerate(ready_rows, 1):
        registry_family = normalized(row.get("rerun_registry_family"))
        output.append(
            boundary_row(
                {
                    "comparator_packet_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-COMPARATOR-PACKET-{index:05d}",
                    "input_action_scope_row_id": row.get("action_scope_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "rerun_registry_family": registry_family,
                    "comparator_packet_status": comparator_packet_status(registry_family),
                    "comparator_packet_use": "BRANCH_LOCAL_COMPARATOR_INPUT_ONLY",
                    "bridge_rows": row.get("bridge_rows"),
                    "score_context_index_count": row.get("score_context_index_count"),
                    "score_context_index_mean": row.get("score_context_index_mean"),
                    "net_proxy_r_count": row.get("net_proxy_r_count"),
                    "net_proxy_r_mean": row.get("net_proxy_r_mean"),
                    "primitive_flag_count": row.get("primitive_flag_count"),
                }
            )
        )
    return output


def repair_route_family(row: dict[str, Any]) -> str:
    status = normalized(row.get("score_bridge_rebuild_status"))
    exact_status = normalized(row.get("exact_r_status"))
    if status == "SCORE_BRIDGE_REBUILT_NO_REPLAY_SCORE_SCOPE_MATCH":
        return "SCOPE_IDENTITY_REPAIR_REQUIRED"
    if "MISSING_GEOMETRY_FIELDS" in exact_status:
        return "GEOMETRY_FIELD_REPAIR_REQUIRED"
    if "NO_DIRECT_TRADE_CANDIDATE_OR_TICKET_IDENTIFIER" in exact_status:
        return "IDENTIFIER_LINKAGE_REPAIR_REQUIRED"
    return "IDENTIFIER_GEOMETRY_REVIEW_REQUIRED"


def repair_routing_rows(bridge_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    routed = [
        row
        for row in bridge_rows
        if row.get("score_bridge_rebuild_status")
        in {
            "SCORE_BRIDGE_REBUILT_WITH_REPAIR_CONTEXT_SCOPE",
            "SCORE_BRIDGE_REBUILT_NO_REPLAY_SCORE_SCOPE_MATCH",
        }
    ]
    output: list[dict[str, Any]] = []
    for index, row in enumerate(routed, 1):
        family = repair_route_family(row)
        output.append(
            boundary_row(
                {
                    "repair_routing_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-REPAIR-ROUTE-{index:05d}",
                    "input_score_rebuilt_bridge_row_id": row.get("score_rebuilt_bridge_row_id"),
                    "input_exact_proxy_bridge_row_id": row.get("input_exact_proxy_bridge_row_id"),
                    "input_score_scope_summary_row_id": row.get("input_score_scope_summary_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "primitive_flag": row.get("primitive_flag"),
                    "score_bridge_rebuild_status": row.get("score_bridge_rebuild_status"),
                    "exact_r_status": row.get("exact_r_status"),
                    "repair_route_family": family,
                    "repair_route_next_step": (
                        "REPAIR_SCOPE_IDENTITY_BEFORE_SCORE_JOIN"
                        if family == "SCOPE_IDENTITY_REPAIR_REQUIRED"
                        else "REPAIR_IDENTIFIER_OR_GEOMETRY_FIELDS_THEN_RERUN_EXACT_PROXY_BRIDGE"
                    ),
                }
            )
        )
    return output


def symbol_market_packet_rows(scope_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scope_rows:
        grouped[(normalized(row.get("symbol")), normalized(row.get("route_session")), normalized(row.get("horizon_id")))].append(row)

    output: list[dict[str, Any]] = []
    for index, ((symbol, route_session, horizon_id), rows) in enumerate(sorted(grouped.items()), 1):
        bridge_row_count = sum(int(row.get("bridge_rows") or 0) for row in rows)
        ready_scope_count = sum(
            1
            for row in rows
            if row.get("action_scope_status") == "ACTION_SCOPE_READY_FOR_SCORE_AUGMENTED_COMPARATOR_PACKET"
        )
        repair_scope_count = sum(
            1
            for row in rows
            if row.get("action_scope_status") == "ACTION_SCOPE_READY_FOR_IDENTIFIER_GEOMETRY_REPAIR_ROUTING"
        )
        unjoined_scope_count = sum(
            1
            for row in rows
            if row.get("action_scope_status") == "ACTION_SCOPE_UNJOINED_SYSTEM_SCOPE_REQUIRES_SCOPE_REPAIR"
        )
        output.append(
            boundary_row(
                {
                    "symbol_market_packet_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-SYMBOL-MARKET-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "action_scope_rows": len(rows),
                    "bridge_rows": bridge_row_count,
                    "ready_comparator_scope_rows": ready_scope_count,
                    "repair_scope_rows": repair_scope_count,
                    "unjoined_scope_rows": unjoined_scope_count,
                    "symbol_market_packet_status": (
                        "SYMBOL_MARKET_PACKET_HAS_COMPARATOR_AND_REPAIR_ACTIONS"
                        if ready_scope_count and (repair_scope_count or unjoined_scope_count)
                        else "SYMBOL_MARKET_PACKET_COMPARATOR_READY"
                        if ready_scope_count
                        else "SYMBOL_MARKET_PACKET_REPAIR_ONLY"
                    ),
                }
            )
        )
    return output


def bucket_rows(
    action_rows: list[dict[str, Any]],
    comparator_rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    specs = [
        ("action_scope_status", action_rows, "action_scope_status"),
        ("action_scope_next_step", action_rows, "action_scope_next_step"),
        ("comparator_packet_status", comparator_rows, "comparator_packet_status"),
        ("repair_route_family", repair_rows, "repair_route_family"),
        ("repair_route_next_step", repair_rows, "repair_route_next_step"),
    ]
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "action_packet_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-SCORE-ACTION-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
