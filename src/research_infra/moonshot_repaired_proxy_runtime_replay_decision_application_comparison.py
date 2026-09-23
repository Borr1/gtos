"""Compare applied runtime replay packets against held review scopes."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RUNTIME_REPLAY_DECISION_APPLICATION_COMPARISON_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_application_comparison.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

ADVANCE_PACKET_FAMILIES = {
    "PACKET_APPLICATION_CLEAR_ADVANCE",
    "PACKET_APPLICATION_CONTEXT_ADVANCE",
}
HELD_SCOPE_FAMILIES = {
    "SCOPE_APPLICATION_REVIEW_HOLD",
    "SCOPE_APPLICATION_SIDECAR_ONLY_REVIEW",
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
    output["runtime_replay_decision_application_comparison_surface"] = (
        RUNTIME_REPLAY_DECISION_APPLICATION_COMPARISON_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def scope_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("registry_family")),
    )


def scope_review_comparison_class(
    scope_family: str,
    advance_packets: int,
    held_packets: int,
    sidecar_requirements: int,
) -> tuple[str, str]:
    if scope_family == "SCOPE_APPLICATION_CLEAR_ADVANCE":
        if held_packets or sidecar_requirements:
            return (
                "SCOPE_REVIEW_COMPARISON_CLEAR_ADVANCE_WITH_ATTACHED_REVIEW_CONTEXT",
                "COMPARE_CLEAR_ADVANCE_SCOPE_WITH_ATTACHED_REVIEW_CONTEXT",
            )
        return (
            "SCOPE_REVIEW_COMPARISON_CLEAR_ADVANCE_READY",
            "ROUTE_CLEAR_ADVANCE_SCOPE_TO_BRANCH_LOCAL_COMPARISON_BATCH",
        )
    if scope_family == "SCOPE_APPLICATION_CONTEXT_ADVANCE":
        if held_packets or sidecar_requirements:
            return (
                "SCOPE_REVIEW_COMPARISON_CONTEXT_ADVANCE_WITH_ATTACHED_REVIEW_CONTEXT",
                "COMPARE_CONTEXT_ADVANCE_SCOPE_WITH_ATTACHED_REVIEW_CONTEXT",
            )
        return (
            "SCOPE_REVIEW_COMPARISON_CONTEXT_ADVANCE_READY",
            "ROUTE_CONTEXT_ADVANCE_SCOPE_TO_BRANCH_LOCAL_COMPARISON_BATCH",
        )
    if scope_family == "SCOPE_APPLICATION_REVIEW_HOLD":
        if advance_packets:
            return (
                "SCOPE_REVIEW_COMPARISON_HELD_SCOPE_WITH_ADVANCE_PACKETS",
                "COMPARE_ADVANCE_PACKETS_AGAINST_HELD_REVIEW_SCOPE",
            )
        return (
            "SCOPE_REVIEW_COMPARISON_HELD_SCOPE_WITH_HELD_PACKETS",
            "KEEP_HELD_PACKET_SCOPE_IN_REVIEW_COMPARISON_QUEUE",
        )
    return (
        "SCOPE_REVIEW_COMPARISON_SIDECAR_ONLY_HELD_SCOPE",
        "KEEP_SIDECAR_ONLY_SCOPE_IN_REVIEW_COMPARISON_QUEUE",
    )


def scope_review_comparison_rows(
    scope_rows: list[dict[str, Any]],
    packet_rows: list[dict[str, Any]],
    sidecar_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    packets_by_scope: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    sidecars_by_scope: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in packet_rows:
        packets_by_scope[scope_key(row)].append(row)
    for row in sidecar_rows:
        sidecars_by_scope[scope_key(row)].append(row)

    output: list[dict[str, Any]] = []
    for row in scope_rows:
        key = scope_key(row)
        packets = packets_by_scope.get(key, [])
        sidecars = sidecars_by_scope.get(key, [])
        packet_counts = Counter(normalized(packet.get("packet_application_family")) for packet in packets)
        sidecar_counts = Counter(normalized(sidecar.get("sidecar_application_family")) for sidecar in sidecars)
        advance_packets = sum(packet_counts.get(family, 0) for family in ADVANCE_PACKET_FAMILIES)
        held_packets = len(packets) - advance_packets
        sidecar_requirements = sidecar_counts.get("SIDECAR_APPLICATION_SCOPE_REVIEW_REQUIREMENT", 0)
        comparison_class, comparison_action = scope_review_comparison_class(
            normalized(row.get("scope_application_family")),
            advance_packets,
            held_packets,
            sidecar_requirements,
        )
        output.append(
            boundary_row(
                {
                    "scope_review_comparison_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-APPLICATION-COMPARISON-SCOPE-{len(output) + 1:05d}"
                    ),
                    "input_scope_application_row_id": row.get("scope_application_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "registry_family": row.get("registry_family"),
                    "scope_application_family": row.get("scope_application_family"),
                    "scope_application_action": row.get("scope_application_action"),
                    "scope_comparison_class": row.get("scope_comparison_class"),
                    "packet_application_rows": len(packets),
                    "advance_packet_rows": int(advance_packets),
                    "held_packet_rows": int(held_packets),
                    "sidecar_application_rows": len(sidecars),
                    "sidecar_scope_requirement_rows": int(sidecar_requirements),
                    "packet_application_family_counts": dict(sorted(packet_counts.items())),
                    "sidecar_application_family_counts": dict(sorted(sidecar_counts.items())),
                    "scope_review_comparison_class": comparison_class,
                    "scope_review_comparison_action": comparison_action,
                    "scope_review_comparison_status": "RUNTIME_REPLAY_APPLICATION_SCOPE_COMPARISON_MATERIALIZED",
                }
            )
        )
    return output


def scope_index(scope_comparison_rows_in: list[dict[str, Any]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    return {scope_key(row): row for row in scope_comparison_rows_in}


def packet_scope_comparison_family(packet_family: str, scope_row: dict[str, Any] | None) -> tuple[str, str]:
    if scope_row is None:
        return (
            "PACKET_SCOPE_COMPARISON_MISSING_SCOPE_CONTEXT",
            "KEEP_PACKET_PENDING_SCOPE_CONTEXT_REPAIR",
        )
    scope_family = normalized(scope_row.get("scope_application_family"))
    if packet_family in ADVANCE_PACKET_FAMILIES and scope_family in HELD_SCOPE_FAMILIES:
        return (
            "PACKET_SCOPE_COMPARISON_ADVANCE_PACKET_AGAINST_HELD_SCOPE",
            "COMPARE_ADVANCE_PACKET_AGAINST_HELD_SCOPE_CONTEXT",
        )
    if packet_family in ADVANCE_PACKET_FAMILIES:
        return (
            "PACKET_SCOPE_COMPARISON_ADVANCE_PACKET_WITH_ADVANCE_SCOPE",
            "ROUTE_ADVANCE_PACKET_TO_BRANCH_LOCAL_COMPARISON_BATCH",
        )
    if scope_family in HELD_SCOPE_FAMILIES:
        return (
            "PACKET_SCOPE_COMPARISON_HELD_PACKET_WITH_HELD_SCOPE",
            "KEEP_HELD_PACKET_WITH_SCOPE_REVIEW_CONTEXT",
        )
    return (
        "PACKET_SCOPE_COMPARISON_HELD_PACKET_ATTACHED_TO_ADVANCE_SCOPE",
        "COMPARE_HELD_PACKET_WITH_ADVANCE_SCOPE_CONTEXT",
    )


def packet_scope_comparison_rows(
    packet_rows: list[dict[str, Any]], scope_comparison_rows_in: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    index = scope_index(scope_comparison_rows_in)
    output: list[dict[str, Any]] = []
    for row in packet_rows:
        scope_row = index.get(scope_key(row))
        family, action = packet_scope_comparison_family(normalized(row.get("packet_application_family")), scope_row)
        output.append(
            boundary_row(
                {
                    "packet_scope_comparison_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-APPLICATION-COMPARISON-PACKET-{len(output) + 1:06d}"
                    ),
                    "input_packet_application_row_id": row.get("packet_application_row_id"),
                    "input_scope_review_comparison_row_id": (
                        scope_row.get("scope_review_comparison_row_id") if scope_row else None
                    ),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "comparison_packet_role": row.get("comparison_packet_role"),
                    "sidecar_aware_comparison_score": row.get("sidecar_aware_comparison_score"),
                    "packet_application_family": row.get("packet_application_family"),
                    "scope_application_family": scope_row.get("scope_application_family") if scope_row else None,
                    "scope_review_comparison_class": (
                        scope_row.get("scope_review_comparison_class") if scope_row else None
                    ),
                    "scope_sidecar_requirement_rows": (
                        int(scope_row.get("sidecar_scope_requirement_rows") or 0) if scope_row else 0
                    ),
                    "scope_held_packet_rows": int(scope_row.get("held_packet_rows") or 0) if scope_row else 0,
                    "packet_scope_comparison_family": family,
                    "packet_scope_comparison_action": action,
                    "packet_scope_comparison_status": "RUNTIME_REPLAY_PACKET_SCOPE_COMPARISON_MATERIALIZED",
                }
            )
        )
    return output


def sidecar_scope_comparison_family(sidecar_family: str, scope_row: dict[str, Any] | None) -> tuple[str, str]:
    if scope_row is None:
        return (
            "SIDECAR_SCOPE_COMPARISON_MISSING_SCOPE_CONTEXT",
            "KEEP_SIDECAR_PENDING_SCOPE_CONTEXT_REPAIR",
        )
    scope_family = normalized(scope_row.get("scope_application_family"))
    if sidecar_family == "SIDECAR_APPLICATION_SCORE_DAMPER" and scope_family in HELD_SCOPE_FAMILIES:
        return (
            "SIDECAR_SCOPE_COMPARISON_SCORE_DAMPER_ON_HELD_SCOPE",
            "KEEP_SCORE_DAMPER_WITH_HELD_SCOPE_CONTEXT",
        )
    if sidecar_family == "SIDECAR_APPLICATION_SCORE_DAMPER":
        return (
            "SIDECAR_SCOPE_COMPARISON_SCORE_DAMPER_ON_ADVANCE_SCOPE",
            "ATTACH_SCORE_DAMPER_TO_ADVANCE_SCOPE_COMPARISON",
        )
    if scope_family in HELD_SCOPE_FAMILIES:
        return (
            "SIDECAR_SCOPE_COMPARISON_REVIEW_REQUIREMENT_ON_HELD_SCOPE",
            "KEEP_SCOPE_REVIEW_REQUIREMENT_WITH_HELD_SCOPE",
        )
    return (
        "SIDECAR_SCOPE_COMPARISON_REVIEW_REQUIREMENT_ON_ADVANCE_SCOPE",
        "ATTACH_SCOPE_REVIEW_REQUIREMENT_TO_ADVANCE_SCOPE",
    )


def sidecar_scope_comparison_rows(
    sidecar_rows: list[dict[str, Any]], scope_comparison_rows_in: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    index = scope_index(scope_comparison_rows_in)
    output: list[dict[str, Any]] = []
    for row in sidecar_rows:
        scope_row = index.get(scope_key(row))
        family, action = sidecar_scope_comparison_family(normalized(row.get("sidecar_application_family")), scope_row)
        output.append(
            boundary_row(
                {
                    "sidecar_scope_comparison_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-APPLICATION-COMPARISON-SIDECAR-{len(output) + 1:06d}"
                    ),
                    "input_sidecar_application_row_id": row.get("sidecar_application_row_id"),
                    "input_scope_review_comparison_row_id": (
                        scope_row.get("scope_review_comparison_row_id") if scope_row else None
                    ),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "review_sidecar_family": row.get("review_sidecar_family"),
                    "sidecar_application_family": row.get("sidecar_application_family"),
                    "scope_application_family": scope_row.get("scope_application_family") if scope_row else None,
                    "scope_review_comparison_class": (
                        scope_row.get("scope_review_comparison_class") if scope_row else None
                    ),
                    "sidecar_scope_comparison_family": family,
                    "sidecar_scope_comparison_action": action,
                    "sidecar_scope_comparison_status": "RUNTIME_REPLAY_SIDECAR_SCOPE_COMPARISON_MATERIALIZED",
                }
            )
        )
    return output


def advance_packet_rows(packet_scope_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in packet_scope_rows:
        if normalized(row.get("packet_application_family")) not in ADVANCE_PACKET_FAMILIES:
            continue
        selected = dict(row)
        selected["advance_packet_row_id"] = (
            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-APPLICATION-COMPARISON-ADVANCE-PACKET-{len(output) + 1:06d}"
        )
        selected["advance_packet_status"] = "RUNTIME_REPLAY_ADVANCE_PACKET_COMPARISON_SELECTED"
        output.append(boundary_row(selected))
    return output


def held_review_scope_rows(scope_comparison_rows_in: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in scope_comparison_rows_in:
        if normalized(row.get("scope_application_family")) not in HELD_SCOPE_FAMILIES:
            continue
        selected = dict(row)
        selected["held_review_scope_row_id"] = (
            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-APPLICATION-COMPARISON-HELD-SCOPE-{len(output) + 1:05d}"
        )
        selected["held_review_scope_status"] = "RUNTIME_REPLAY_HELD_REVIEW_SCOPE_COMPARISON_SELECTED"
        output.append(boundary_row(selected))
    return output


def system_review_comparison_rows(
    scope_rows: list[dict[str, Any]],
    packet_rows: list[dict[str, Any]],
    sidecar_rows: list[dict[str, Any]],
    advance_rows: list[dict[str, Any]],
    held_scope_rows_in: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scope_counts = Counter(normalized(row.get("scope_review_comparison_class")) for row in scope_rows)
    packet_counts = Counter(normalized(row.get("packet_scope_comparison_family")) for row in packet_rows)
    sidecar_counts = Counter(normalized(row.get("sidecar_scope_comparison_family")) for row in sidecar_rows)
    return [
        boundary_row(
            {
                "system_review_comparison_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-APPLICATION-COMPARISON-SYSTEM-0001"
                ),
                "scope_review_comparison_rows": len(scope_rows),
                "packet_scope_comparison_rows": len(packet_rows),
                "sidecar_scope_comparison_rows": len(sidecar_rows),
                "advance_packet_rows": len(advance_rows),
                "held_review_scope_rows": len(held_scope_rows_in),
                "scope_review_comparison_class_counts": dict(sorted(scope_counts.items())),
                "packet_scope_comparison_family_counts": dict(sorted(packet_counts.items())),
                "sidecar_scope_comparison_family_counts": dict(sorted(sidecar_counts.items())),
                "system_review_comparison": (
                    "Compare clear/context packet applications with held packet scopes and sidecar-only review scopes "
                    "as branch-local inputs for the next ranking pass."
                ),
                "system_review_comparison_status": (
                    "RUNTIME_REPLAY_DECISION_APPLICATION_COMPARISON_MATERIALIZED_BRANCH_LOCAL"
                ),
            }
        )
    ]


def comparison_bucket_rows(
    scope_rows: list[dict[str, Any]],
    packet_rows: list[dict[str, Any]],
    sidecar_rows: list[dict[str, Any]],
    advance_rows: list[dict[str, Any]],
    held_scope_rows_in: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("scope_review_comparison_class", scope_rows, "scope_review_comparison_class"),
        ("packet_scope_comparison_family", packet_rows, "packet_scope_comparison_family"),
        ("sidecar_scope_comparison_family", sidecar_rows, "sidecar_scope_comparison_family"),
        ("advance_packet_status", advance_rows, "advance_packet_status"),
        ("held_review_scope_status", held_scope_rows_in, "held_review_scope_status"),
        ("system_review_comparison_status", system_rows, "system_review_comparison_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "application_comparison_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-APPLICATION-COMPARISON-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
