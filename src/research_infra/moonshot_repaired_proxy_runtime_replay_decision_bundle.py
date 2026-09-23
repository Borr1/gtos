"""Bundle sidecar-aware runtime replay decisions for downstream branch-local comparison."""

from __future__ import annotations

from collections import Counter
from typing import Any


RUNTIME_REPLAY_DECISION_BUNDLE_SURFACE = "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_bundle.py"
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
    output["runtime_replay_decision_bundle_surface"] = RUNTIME_REPLAY_DECISION_BUNDLE_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def packet_bundle_class(packet_family: str) -> str:
    if packet_family == "PACKET_DECISION_CLEAR_ADVANCE":
        return "FINAL_BUNDLE_PACKET_CLEAR_ADVANCE"
    if packet_family == "PACKET_DECISION_CONTEXT_ADVANCE":
        return "FINAL_BUNDLE_PACKET_CONTEXT_ADVANCE"
    if packet_family == "PACKET_DECISION_REVIEW_HOLD":
        return "FINAL_BUNDLE_PACKET_REVIEW_HOLD"
    return "FINAL_BUNDLE_PACKET_REVIEW_ONLY"


def scope_bundle_class(scope_class: str) -> str:
    if scope_class == "SCOPE_DECISION_HAS_CLEAR_ADVANCE_PACKET":
        return "FINAL_BUNDLE_SCOPE_CLEAR_ADVANCE"
    if scope_class == "SCOPE_DECISION_HAS_CONTEXT_ADVANCE_PACKET":
        return "FINAL_BUNDLE_SCOPE_CONTEXT_ADVANCE"
    if scope_class == "SCOPE_DECISION_REVIEW_HELD_PACKET_SCOPE":
        return "FINAL_BUNDLE_SCOPE_REVIEW_HELD"
    return "FINAL_BUNDLE_SCOPE_SIDECAR_ONLY_REVIEW"


def sidecar_bundle_class(sidecar_family: str) -> str:
    if sidecar_family == "SIDECAR_DECISION_SCORE_DAMPER":
        return "FINAL_BUNDLE_SIDECAR_SCORE_DAMPER"
    return "FINAL_BUNDLE_SIDECAR_SCOPE_REVIEW_REQUIREMENT"


def final_packet_bundle_rows(packet_decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in packet_decisions:
        bundle_class = packet_bundle_class(normalized(row.get("packet_decision_family")))
        output.append(
            boundary_row(
                {
                    "final_packet_bundle_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-FINAL-BUNDLE-PACKET-{len(output) + 1:06d}"
                    ),
                    "input_packet_decision_row_id": row.get("packet_decision_row_id"),
                    "input_packet_score_row_id": row.get("input_packet_score_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "comparison_packet_role": row.get("comparison_packet_role"),
                    "sidecar_aware_comparison_score": row.get("sidecar_aware_comparison_score"),
                    "packet_decision_family": row.get("packet_decision_family"),
                    "packet_decision_action": row.get("packet_decision_action"),
                    "final_packet_bundle_class": bundle_class,
                    "final_packet_bundle_status": "FINAL_BRANCH_LOCAL_PACKET_DECISION_BUNDLED",
                }
            )
        )
    return output


def final_scope_bundle_rows(scope_decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in scope_decisions:
        bundle_class = scope_bundle_class(normalized(row.get("scope_decision_class")))
        output.append(
            boundary_row(
                {
                    "final_scope_bundle_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-FINAL-BUNDLE-SCOPE-{len(output) + 1:05d}"
                    ),
                    "input_scope_decision_row_id": row.get("scope_decision_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "registry_family": row.get("registry_family"),
                    "scope_comparison_class": row.get("scope_comparison_class"),
                    "comparison_packet_rows": row.get("comparison_packet_rows"),
                    "review_sidecar_rows": row.get("review_sidecar_rows"),
                    "packet_decision_rows": row.get("packet_decision_rows"),
                    "scope_decision_class": row.get("scope_decision_class"),
                    "final_scope_bundle_class": bundle_class,
                    "final_scope_bundle_status": "FINAL_BRANCH_LOCAL_SCOPE_DECISION_BUNDLED",
                }
            )
        )
    return output


def final_sidecar_bundle_rows(sidecar_decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in sidecar_decisions:
        bundle_class = sidecar_bundle_class(normalized(row.get("sidecar_decision_family")))
        output.append(
            boundary_row(
                {
                    "final_sidecar_bundle_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-FINAL-BUNDLE-SIDECAR-{len(output) + 1:06d}"
                    ),
                    "input_sidecar_decision_row_id": row.get("sidecar_decision_row_id"),
                    "input_sidecar_score_impact_row_id": row.get("input_sidecar_score_impact_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "review_sidecar_family": row.get("review_sidecar_family"),
                    "sidecar_decision_family": row.get("sidecar_decision_family"),
                    "sidecar_decision_action": row.get("sidecar_decision_action"),
                    "final_sidecar_bundle_class": bundle_class,
                    "final_sidecar_bundle_status": "FINAL_BRANCH_LOCAL_SIDECAR_DECISION_BUNDLED",
                }
            )
        )
    return output


def system_bundle_rows(
    packet_rows: list[dict[str, Any]], scope_rows: list[dict[str, Any]], sidecar_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    packet_counts = Counter(normalized(row.get("final_packet_bundle_class")) for row in packet_rows)
    scope_counts = Counter(normalized(row.get("final_scope_bundle_class")) for row in scope_rows)
    sidecar_counts = Counter(normalized(row.get("final_sidecar_bundle_class")) for row in sidecar_rows)
    return [
        boundary_row(
            {
                "system_bundle_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-FINAL-BUNDLE-SYSTEM-0001",
                "final_packet_bundle_rows": len(packet_rows),
                "final_scope_bundle_rows": len(scope_rows),
                "final_sidecar_bundle_rows": len(sidecar_rows),
                "final_packet_bundle_class_counts": dict(sorted(packet_counts.items())),
                "final_scope_bundle_class_counts": dict(sorted(scope_counts.items())),
                "final_sidecar_bundle_class_counts": dict(sorted(sidecar_counts.items())),
                "system_bundle": (
                    "Carry packet, scope, and sidecar decisions as a single branch-local comparison decision bundle."
                ),
                "system_bundle_status": "FINAL_BRANCH_LOCAL_RUNTIME_REPLAY_DECISION_BUNDLE_MATERIALIZED",
            }
        )
    ]


def final_bundle_bucket_rows(
    packet_rows: list[dict[str, Any]],
    scope_rows: list[dict[str, Any]],
    sidecar_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("final_packet_bundle_class", packet_rows, "final_packet_bundle_class"),
        ("final_scope_bundle_class", scope_rows, "final_scope_bundle_class"),
        ("final_sidecar_bundle_class", sidecar_rows, "final_sidecar_bundle_class"),
        ("system_bundle_status", system_rows, "system_bundle_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "final_bundle_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-FINAL-BUNDLE-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
