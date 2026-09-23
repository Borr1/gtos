"""Apply runtime replay decision-bundle rows as branch-local comparison inputs."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RUNTIME_REPLAY_DECISION_APPLICATION_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_application.py"
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
    output["runtime_replay_decision_application_surface"] = RUNTIME_REPLAY_DECISION_APPLICATION_SURFACE
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


def packet_application(final_class: str) -> tuple[str, str]:
    if final_class == "FINAL_BUNDLE_PACKET_CLEAR_ADVANCE":
        return (
            "APPLY_PACKET_AS_CLEAR_BRANCH_LOCAL_COMPARISON_INPUT",
            "PACKET_APPLICATION_CLEAR_ADVANCE",
        )
    if final_class == "FINAL_BUNDLE_PACKET_CONTEXT_ADVANCE":
        return (
            "APPLY_PACKET_WITH_CONTEXT_BRANCH_LOCAL_COMPARISON_INPUT",
            "PACKET_APPLICATION_CONTEXT_ADVANCE",
        )
    if final_class == "FINAL_BUNDLE_PACKET_REVIEW_HOLD":
        return (
            "HOLD_PACKET_UNTIL_REVIEW_SIDECARS_ARE_RESOLVED",
            "PACKET_APPLICATION_REVIEW_HOLD",
        )
    return (
        "REVIEW_PACKET_BEFORE_BRANCH_LOCAL_COMPARISON_INPUT",
        "PACKET_APPLICATION_REVIEW_ONLY",
    )


def packet_application_rows(packet_bundle_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in packet_bundle_rows:
        action, family = packet_application(normalized(row.get("final_packet_bundle_class")))
        output.append(
            boundary_row(
                {
                    "packet_application_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-DECISION-APPLICATION-PACKET-{len(output) + 1:06d}"
                    ),
                    "input_final_packet_bundle_row_id": row.get("final_packet_bundle_row_id"),
                    "input_packet_decision_row_id": row.get("input_packet_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "comparison_packet_role": row.get("comparison_packet_role"),
                    "sidecar_aware_comparison_score": row.get("sidecar_aware_comparison_score"),
                    "packet_decision_family": row.get("packet_decision_family"),
                    "final_packet_bundle_class": row.get("final_packet_bundle_class"),
                    "packet_application_action": action,
                    "packet_application_family": family,
                    "packet_application_status": "RUNTIME_REPLAY_PACKET_APPLICATION_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def scope_application(final_class: str, packet_count: int) -> tuple[str, str]:
    if final_class == "FINAL_BUNDLE_SCOPE_CLEAR_ADVANCE":
        return (
            "APPLY_SCOPE_AS_CLEAR_BRANCH_LOCAL_COMPARISON_SCOPE",
            "SCOPE_APPLICATION_CLEAR_ADVANCE",
        )
    if final_class == "FINAL_BUNDLE_SCOPE_CONTEXT_ADVANCE":
        return (
            "APPLY_SCOPE_WITH_CONTEXT_BRANCH_LOCAL_COMPARISON_SCOPE",
            "SCOPE_APPLICATION_CONTEXT_ADVANCE",
        )
    if final_class == "FINAL_BUNDLE_SCOPE_REVIEW_HELD" or packet_count:
        return (
            "HOLD_SCOPE_FOR_PACKET_OR_SIDECAR_REVIEW",
            "SCOPE_APPLICATION_REVIEW_HOLD",
        )
    return (
        "ROUTE_SCOPE_TO_SIDECAR_ONLY_REVIEW",
        "SCOPE_APPLICATION_SIDECAR_ONLY_REVIEW",
    )


def scope_application_rows(
    scope_bundle_rows: list[dict[str, Any]], packet_application_rows_in: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in packet_application_rows_in:
        grouped[scope_key(row)].append(row)
    output: list[dict[str, Any]] = []
    for row in scope_bundle_rows:
        packets = grouped.get(scope_key(row), [])
        packet_families = Counter(normalized(packet.get("packet_application_family")) for packet in packets)
        action, family = scope_application(normalized(row.get("final_scope_bundle_class")), len(packets))
        output.append(
            boundary_row(
                {
                    "scope_application_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-DECISION-APPLICATION-SCOPE-{len(output) + 1:05d}"
                    ),
                    "input_final_scope_bundle_row_id": row.get("final_scope_bundle_row_id"),
                    "input_scope_decision_row_id": row.get("input_scope_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "registry_family": row.get("registry_family"),
                    "scope_comparison_class": row.get("scope_comparison_class"),
                    "comparison_packet_rows": int(row.get("comparison_packet_rows") or 0),
                    "review_sidecar_rows": int(row.get("review_sidecar_rows") or 0),
                    "packet_application_rows": len(packets),
                    "packet_application_family_counts": dict(sorted(packet_families.items())),
                    "final_scope_bundle_class": row.get("final_scope_bundle_class"),
                    "scope_application_action": action,
                    "scope_application_family": family,
                    "scope_application_status": "RUNTIME_REPLAY_SCOPE_APPLICATION_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def sidecar_application(final_class: str) -> tuple[str, str]:
    if final_class == "FINAL_BUNDLE_SIDECAR_SCORE_DAMPER":
        return (
            "APPLY_SIDECAR_AS_COMPARISON_SCORE_DAMPER",
            "SIDECAR_APPLICATION_SCORE_DAMPER",
        )
    return (
        "APPLY_SIDECAR_AS_SCOPE_REVIEW_REQUIREMENT",
        "SIDECAR_APPLICATION_SCOPE_REVIEW_REQUIREMENT",
    )


def sidecar_application_rows(sidecar_bundle_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in sidecar_bundle_rows:
        action, family = sidecar_application(normalized(row.get("final_sidecar_bundle_class")))
        output.append(
            boundary_row(
                {
                    "sidecar_application_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-DECISION-APPLICATION-SIDECAR-{len(output) + 1:06d}"
                    ),
                    "input_final_sidecar_bundle_row_id": row.get("final_sidecar_bundle_row_id"),
                    "input_sidecar_decision_row_id": row.get("input_sidecar_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "review_sidecar_family": row.get("review_sidecar_family"),
                    "sidecar_decision_family": row.get("sidecar_decision_family"),
                    "final_sidecar_bundle_class": row.get("final_sidecar_bundle_class"),
                    "sidecar_application_action": action,
                    "sidecar_application_family": family,
                    "sidecar_application_status": "RUNTIME_REPLAY_SIDECAR_APPLICATION_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def system_application_rows(
    packet_rows: list[dict[str, Any]], scope_rows: list[dict[str, Any]], sidecar_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    packet_counts = Counter(normalized(row.get("packet_application_family")) for row in packet_rows)
    scope_counts = Counter(normalized(row.get("scope_application_family")) for row in scope_rows)
    sidecar_counts = Counter(normalized(row.get("sidecar_application_family")) for row in sidecar_rows)
    return [
        boundary_row(
            {
                "system_application_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-DECISION-APPLICATION-SYSTEM-0001",
                "packet_application_rows": len(packet_rows),
                "scope_application_rows": len(scope_rows),
                "sidecar_application_rows": len(sidecar_rows),
                "packet_application_family_counts": dict(sorted(packet_counts.items())),
                "scope_application_family_counts": dict(sorted(scope_counts.items())),
                "sidecar_application_family_counts": dict(sorted(sidecar_counts.items())),
                "system_application": (
                    "Use clear and context packet applications as branch-local comparison inputs, while carrying "
                    "review-held packets, scope review, and sidecar requirements into the next pass."
                ),
                "system_application_status": "RUNTIME_REPLAY_DECISION_APPLICATION_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def application_bucket_rows(
    packet_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    sidecar_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("packet_application_family", packet_rows, "packet_application_family"),
        ("scope_application_family", scope_rows, "scope_application_family"),
        ("sidecar_application_family", sidecar_rows, "sidecar_application_family"),
        ("system_application_status", system_rows, "system_application_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "decision_application_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-DECISION-APPLICATION-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
