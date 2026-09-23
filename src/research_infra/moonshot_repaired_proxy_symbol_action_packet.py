"""Materialize repaired-proxy comparator executions into symbol action packets."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


SYMBOL_ACTION_PACKET_SURFACE = "src/research_infra/moonshot_repaired_proxy_symbol_action_packet.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
REGISTER_ACTIONS = {
    "REGISTER_DEFAULT_OFF_SCORER_COMPARATOR",
    "REGISTER_AVOID_REDESIGN_COMPARATOR",
}


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
    output["symbol_action_packet_surface"] = SYMBOL_ACTION_PACKET_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def weighted_mean(rows: list[dict[str, Any]], field: str) -> float | None:
    pairs: list[tuple[float, int]] = []
    for row in rows:
        value = as_float(row.get(field))
        weight = int(row.get("bridge_rows") or 0)
        if value is not None and weight > 0:
            pairs.append((value, weight))
    total_weight = sum(weight for _, weight in pairs)
    if total_weight <= 0:
        values = [as_float(row.get(field)) for row in rows]
        clean = [value for value in values if value is not None]
        return mean(clean) if clean else None
    return sum(value * weight for value, weight in pairs) / total_weight


def symbol_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
    )


def packet_status(action_counts: Counter[str]) -> tuple[str, str]:
    default_count = action_counts.get("REGISTER_DEFAULT_OFF_SCORER_COMPARATOR", 0)
    avoid_count = action_counts.get("REGISTER_AVOID_REDESIGN_COMPARATOR", 0)
    hold_count = action_counts.get("HOLD_DEFAULT_OFF_SCORER_CONTEXT", 0)
    if default_count and avoid_count:
        return "SYMBOL_ACTION_PACKET_MIXED_DEFAULT_AND_AVOID_REGISTRATION", "MATERIALIZE_MIXED_SYMBOL_COMPARATOR_PACKET"
    if avoid_count:
        return "SYMBOL_ACTION_PACKET_AVOID_REDESIGN_REGISTRATION", "MATERIALIZE_AVOID_REDESIGN_SYMBOL_PACKET"
    if default_count:
        return "SYMBOL_ACTION_PACKET_DEFAULT_OFF_REGISTRATION", "MATERIALIZE_DEFAULT_OFF_SYMBOL_PACKET"
    if hold_count:
        return "SYMBOL_ACTION_PACKET_HOLD_WEAK_DEFAULT_OFF_CONTEXT", "CARRY_HOLD_CONTEXT_WITHOUT_REGISTRATION"
    return "SYMBOL_ACTION_PACKET_REJECTED_OR_NONREGISTERING_CONTEXT", "PRESERVE_REJECTED_CONTEXT"


def symbol_action_packet_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in execution_rows:
        grouped[symbol_key(row)].append(row)

    output: list[dict[str, Any]] = []
    for (symbol, route_session, horizon_id), rows in sorted(grouped.items()):
        action_counts = Counter(normalized(row.get("comparator_execution_action")) for row in rows)
        status, next_action = packet_status(action_counts)
        output.append(
            boundary_row(
                {
                    "symbol_action_packet_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-SYMBOL-ACTION-PACKET-{len(output) + 1:05d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "comparator_execution_rows": len(rows),
                    "bridge_rows": sum(int(row.get("bridge_rows") or 0) for row in rows),
                    "registration_candidate_rows": sum(
                        1 for row in rows if normalized(row.get("comparator_execution_action")) in REGISTER_ACTIONS
                    ),
                    "nonregistration_rows": sum(
                        1 for row in rows if normalized(row.get("comparator_execution_action")) not in REGISTER_ACTIONS
                    ),
                    "net_proxy_r_weighted_mean": weighted_mean(rows, "net_proxy_r_mean"),
                    "score_context_index_weighted_mean": weighted_mean(rows, "score_context_index_mean"),
                    "comparator_execution_action_counts": dict(sorted(action_counts.items())),
                    "source_exhaustion_gate_status": normalized(rows[0].get("source_exhaustion_gate_status")),
                    "symbol_action_packet_status": status,
                    "symbol_action_packet_next_action": next_action,
                }
            )
        )
    return output


def comparator_registration_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in execution_rows:
        action = normalized(row.get("comparator_execution_action"))
        if action not in REGISTER_ACTIONS:
            continue
        family = (
            "DEFAULT_OFF_SCORER_COMPARATOR_REGISTRATION"
            if action == "REGISTER_DEFAULT_OFF_SCORER_COMPARATOR"
            else "AVOID_REDESIGN_COMPARATOR_REGISTRATION"
        )
        output.append(
            boundary_row(
                {
                    "comparator_registration_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-SYMBOL-ACTION-REG-{len(output) + 1:05d}"
                    ),
                    "input_comparator_execution_row_id": row.get("comparator_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "comparator_input_family": row.get("comparator_input_family"),
                    "comparator_execution_action": action,
                    "registration_family": family,
                    "bridge_rows": row.get("bridge_rows"),
                    "net_proxy_r_mean": row.get("net_proxy_r_mean"),
                    "score_context_index_mean": row.get("score_context_index_mean"),
                    "source_exhaustion_gate_status": row.get("source_exhaustion_gate_status"),
                    "registration_status": "COMPARATOR_REGISTRATION_CANDIDATE_READY_BRANCH_LOCAL",
                }
            )
        )
    return output


def comparator_nonregistration_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in execution_rows:
        action = normalized(row.get("comparator_execution_action"))
        if action in REGISTER_ACTIONS:
            continue
        output.append(
            boundary_row(
                {
                    "comparator_nonregistration_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-SYMBOL-ACTION-NONREG-{len(output) + 1:05d}"
                    ),
                    "input_comparator_execution_row_id": row.get("comparator_execution_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "comparator_execution_action": action,
                    "bridge_rows": row.get("bridge_rows"),
                    "net_proxy_r_mean": row.get("net_proxy_r_mean"),
                    "score_context_index_mean": row.get("score_context_index_mean"),
                    "nonregistration_status": "COMPARATOR_EXECUTION_NOT_REGISTERED_CURRENT_PROXY_CONTEXT",
                }
            )
        )
    return output


def symbol_proxy_surface_rows(packet_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for packet in packet_rows:
        output.append(
            boundary_row(
                {
                    "symbol_proxy_surface_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-SYMBOL-ACTION-PROXY-{len(output) + 1:05d}"
                    ),
                    "input_symbol_action_packet_row_id": packet.get("symbol_action_packet_row_id"),
                    "symbol": packet.get("symbol"),
                    "route_session": packet.get("route_session"),
                    "horizon_id": packet.get("horizon_id"),
                    "bridge_rows": packet.get("bridge_rows"),
                    "registration_candidate_rows": packet.get("registration_candidate_rows"),
                    "net_proxy_r_weighted_mean": packet.get("net_proxy_r_weighted_mean"),
                    "score_context_index_weighted_mean": packet.get("score_context_index_weighted_mean"),
                    "symbol_proxy_surface_status": "SYMBOL_PROXY_R_SURFACE_MATERIALIZED_FROM_COMPARATOR_EXECUTION",
                }
            )
        )
    return output


def symbol_action_bucket_rows(
    packet_rows: list[dict[str, Any]],
    registration_rows: list[dict[str, Any]],
    nonregistration_rows: list[dict[str, Any]],
    proxy_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("symbol_action_packet_status", packet_rows, "symbol_action_packet_status"),
        ("registration_family", registration_rows, "registration_family"),
        ("registration_status", registration_rows, "registration_status"),
        ("nonregistration_status", nonregistration_rows, "nonregistration_status"),
        ("symbol_proxy_surface_status", proxy_rows, "symbol_proxy_surface_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "symbol_action_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-SYMBOL-ACTION-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
