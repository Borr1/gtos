"""Materialize runtime replay advancement surfaces into comparison packets."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RUNTIME_REPLAY_COMPARISON_PACKET_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_comparison_packet.py"
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
    output["runtime_replay_comparison_packet_surface"] = RUNTIME_REPLAY_COMPARISON_PACKET_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def comparison_packet_role(row: dict[str, Any]) -> str:
    route_class = normalized(row.get("replay_signal_route_class"))
    if route_class == "DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL":
        return "DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT"
    if route_class == "AVOID_REDESIGN_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL":
        return "AVOID_REDESIGN_REPLAY_SIGNAL_COMPARISON_INPUT"
    return "REPRESENTED_REPLAY_CONTEXT_COMPARISON_INPUT"


def comparison_packet_rows(represented_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in represented_rows:
        role = comparison_packet_role(row)
        output.append(
            boundary_row(
                {
                    "comparison_packet_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-PACKET-{len(output) + 1:06d}"
                    ),
                    "input_represented_surface_row_id": row.get("represented_surface_row_id"),
                    "input_advancement_decision_row_id": row.get("input_advancement_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "replay_signal_route_class": row.get("replay_signal_route_class"),
                    "inventory_alignment_class": row.get("inventory_alignment_class"),
                    "advancement_action": row.get("advancement_action"),
                    "comparison_packet_role": role,
                    "comparison_packet_next_step": "COMPARE_REPRESENTED_REPLAY_SURFACE_WITH_BRANCH_LOCAL_PACKET",
                    "comparison_packet_status": "REPRESENTED_SURFACE_COMPARISON_PACKET_INPUT_MATERIALIZED",
                }
            )
        )
    return output


def review_sidecar_rows(
    action_conflict_rows: list[dict[str, Any]], unmatched_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in action_conflict_rows:
        output.append(
            boundary_row(
                {
                    "comparison_review_sidecar_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SIDECAR-{len(output) + 1:06d}"
                    ),
                    "input_action_conflict_review_row_id": row.get("action_conflict_review_row_id"),
                    "input_advancement_decision_row_id": row.get("input_advancement_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "replay_signal_route_class": row.get("replay_signal_route_class"),
                    "inventory_alignment_class": row.get("inventory_alignment_class"),
                    "inventory_decision_group_counts": row.get("inventory_decision_group_counts") or {},
                    "inventory_action_classes": list(row.get("inventory_action_classes") or []),
                    "review_sidecar_family": "ACTION_CONFLICT_REVIEW_SIDECAR",
                    "review_sidecar_next_step": "RECONCILE_EXACT_SCOPE_ACTION_BEFORE_COMPARISON_USE",
                    "review_sidecar_status": "ACTION_CONFLICT_REVIEW_SIDECAR_MATERIALIZED",
                }
            )
        )
    for row in unmatched_rows:
        output.append(
            boundary_row(
                {
                    "comparison_review_sidecar_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SIDECAR-{len(output) + 1:06d}"
                    ),
                    "input_unmatched_scope_advancement_row_id": row.get("unmatched_scope_advancement_row_id"),
                    "input_advancement_decision_row_id": row.get("input_advancement_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "replay_signal_route_class": row.get("replay_signal_route_class"),
                    "inventory_alignment_class": row.get("inventory_alignment_class"),
                    "review_sidecar_family": "UNMATCHED_SCOPE_REVIEW_SIDECAR",
                    "review_sidecar_next_step": "REVIEW_SCOPE_MATCH_BEFORE_COMPARISON_USE",
                    "review_sidecar_status": "UNMATCHED_SCOPE_REVIEW_SIDECAR_MATERIALIZED",
                }
            )
        )
    return output


def scope_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("registry_family")),
    )


def comparison_scope_rows(
    packet_rows: list[dict[str, Any]], sidecar_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    grouped_packets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    grouped_sidecars: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in packet_rows:
        grouped_packets[scope_key(row)].append(row)
    for row in sidecar_rows:
        grouped_sidecars[scope_key(row)].append(row)

    keys = sorted(set(grouped_packets) | set(grouped_sidecars))
    output: list[dict[str, Any]] = []
    for symbol, route_session, horizon_id, registry_family in keys:
        packets = grouped_packets.get((symbol, route_session, horizon_id, registry_family), [])
        sidecars = grouped_sidecars.get((symbol, route_session, horizon_id, registry_family), [])
        role_counts = Counter(normalized(row.get("comparison_packet_role")) for row in packets)
        sidecar_counts = Counter(normalized(row.get("review_sidecar_family")) for row in sidecars)
        output.append(
            boundary_row(
                {
                    "comparison_scope_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SCOPE-{len(output) + 1:05d}"
                    ),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "registry_family": registry_family,
                    "comparison_packet_rows": len(packets),
                    "review_sidecar_rows": len(sidecars),
                    "comparison_packet_role_counts": dict(sorted(role_counts.items())),
                    "review_sidecar_family_counts": dict(sorted(sidecar_counts.items())),
                    "comparison_scope_status": "COMPARISON_SCOPE_ROLLED_UP_BRANCH_LOCAL",
                }
            )
        )
    return output


def system_comparison_rows(
    packet_rows: list[dict[str, Any]], sidecar_rows: list[dict[str, Any]], scope_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    role_counts = Counter(normalized(row.get("comparison_packet_role")) for row in packet_rows)
    sidecar_counts = Counter(normalized(row.get("review_sidecar_family")) for row in sidecar_rows)
    return [
        boundary_row(
            {
                "system_comparison_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-SYSTEM-0001",
                "comparison_packet_rows": len(packet_rows),
                "review_sidecar_rows": len(sidecar_rows),
                "comparison_scope_rows": len(scope_rows),
                "comparison_packet_role_counts": dict(sorted(role_counts.items())),
                "review_sidecar_family_counts": dict(sorted(sidecar_counts.items())),
                "system_comparison": (
                    "Use represented replay surfaces as comparison-packet inputs and carry action-conflict plus "
                    "unmatched-scope rows as explicit review sidecars."
                ),
                "system_comparison_status": "RUNTIME_REPLAY_COMPARISON_PACKET_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def comparison_bucket_rows(
    packet_rows: list[dict[str, Any]],
    sidecar_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("comparison_packet_role", packet_rows, "comparison_packet_role"),
        ("comparison_packet_status", packet_rows, "comparison_packet_status"),
        ("review_sidecar_family", sidecar_rows, "review_sidecar_family"),
        ("review_sidecar_status", sidecar_rows, "review_sidecar_status"),
        ("comparison_scope_status", scope_rows, "comparison_scope_status"),
        ("system_comparison_status", system_rows, "system_comparison_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "comparison_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-COMPARISON-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
