"""Route sidecar-aware runtime replay scores into branch-local comparison decisions."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RUNTIME_REPLAY_SIDECAR_AWARE_DECISION_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_sidecar_aware_decision.py"
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
    output["runtime_replay_sidecar_aware_decision_surface"] = RUNTIME_REPLAY_SIDECAR_AWARE_DECISION_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def scope_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("registry_family")),
    )


def packet_decision(row: dict[str, Any]) -> tuple[str, str]:
    score_class = normalized(row.get("sidecar_aware_score_class"))
    sidecars = int(row.get("scope_review_sidecar_rows") or 0)
    if score_class == "COMPARISON_SCORE_HIGH_CLEAR" and sidecars == 0:
        return "ADVANCE_CLEAR_REPRESENTED_PACKET_TO_DECISION_COMPARISON", "PACKET_DECISION_CLEAR_ADVANCE"
    if score_class == "COMPARISON_SCORE_USABLE_WITH_CONTEXT":
        return "ADVANCE_REPRESENTED_PACKET_WITH_CONTEXT_REVIEW", "PACKET_DECISION_CONTEXT_ADVANCE"
    if score_class == "COMPARISON_SCORE_CONTEXT_ONLY_OR_SIDECAR_DAMPED":
        return "HOLD_REPRESENTED_PACKET_FOR_CONTEXT_OR_SIDECAR_REVIEW", "PACKET_DECISION_REVIEW_HOLD"
    return "REVIEW_REPRESENTED_PACKET_BEFORE_DECISION_COMPARISON", "PACKET_DECISION_REVIEW_ONLY"


def packet_decision_rows(packet_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in packet_scores:
        action, family = packet_decision(row)
        output.append(
            boundary_row(
                {
                    "packet_decision_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-DECISION-PACKET-{len(output) + 1:06d}"
                    ),
                    "input_packet_score_row_id": row.get("packet_score_row_id"),
                    "input_comparison_packet_row_id": row.get("input_comparison_packet_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "comparison_packet_role": row.get("comparison_packet_role"),
                    "scope_comparison_class": row.get("scope_comparison_class"),
                    "signal_count_balance": row.get("signal_count_balance"),
                    "sidecar_aware_comparison_score": to_float(row.get("sidecar_aware_comparison_score")),
                    "sidecar_aware_score_class": row.get("sidecar_aware_score_class"),
                    "scope_review_sidecar_rows": int(row.get("scope_review_sidecar_rows") or 0),
                    "packet_decision_action": action,
                    "packet_decision_family": family,
                    "packet_decision_status": "SIDECAR_AWARE_PACKET_DECISION_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def scope_decision_rows(
    packet_decisions: list[dict[str, Any]], scope_scores: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in packet_decisions:
        grouped[scope_key(row)].append(row)
    output: list[dict[str, Any]] = []
    for scope in scope_scores:
        rows = grouped.get(scope_key(scope), [])
        family_counts = Counter(normalized(row.get("packet_decision_family")) for row in rows)
        if family_counts.get("PACKET_DECISION_CLEAR_ADVANCE", 0):
            decision = "SCOPE_DECISION_HAS_CLEAR_ADVANCE_PACKET"
        elif family_counts.get("PACKET_DECISION_CONTEXT_ADVANCE", 0):
            decision = "SCOPE_DECISION_HAS_CONTEXT_ADVANCE_PACKET"
        elif rows:
            decision = "SCOPE_DECISION_REVIEW_HELD_PACKET_SCOPE"
        else:
            decision = "SCOPE_DECISION_SIDECAR_ONLY_REVIEW"
        output.append(
            boundary_row(
                {
                    "scope_decision_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-DECISION-SCOPE-{len(output) + 1:05d}"
                    ),
                    "symbol": scope.get("symbol"),
                    "route_session": scope.get("route_session"),
                    "horizon_id": scope.get("horizon_id"),
                    "registry_family": scope.get("registry_family"),
                    "scope_comparison_class": scope.get("scope_comparison_class"),
                    "comparison_packet_rows": int(scope.get("comparison_packet_rows") or 0),
                    "review_sidecar_rows": int(scope.get("review_sidecar_rows") or 0),
                    "packet_decision_rows": len(rows),
                    "packet_decision_family_counts": dict(sorted(family_counts.items())),
                    "scope_decision_class": decision,
                    "scope_decision_status": "SIDECAR_AWARE_SCOPE_DECISION_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def sidecar_decision_rows(impact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in impact_rows:
        impact = normalized(row.get("sidecar_score_impact_class"))
        if impact == "SIDECAR_DAMPS_REPRESENTED_SCOPE_SCORE":
            action = "CARRY_SIDECAR_AS_SCORE_DAMPER"
            family = "SIDECAR_DECISION_SCORE_DAMPER"
        else:
            action = "CARRY_SIDECAR_AS_SCOPE_REVIEW_REQUIREMENT"
            family = "SIDECAR_DECISION_SCOPE_REVIEW_REQUIREMENT"
        output.append(
            boundary_row(
                {
                    "sidecar_decision_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-DECISION-SIDECAR-{len(output) + 1:06d}"
                    ),
                    "input_sidecar_score_impact_row_id": row.get("sidecar_score_impact_row_id"),
                    "input_sidecar_attachment_row_id": row.get("input_sidecar_attachment_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "review_sidecar_family": row.get("review_sidecar_family"),
                    "sidecar_attachment_class": row.get("sidecar_attachment_class"),
                    "sidecar_score_impact_class": row.get("sidecar_score_impact_class"),
                    "sidecar_decision_action": action,
                    "sidecar_decision_family": family,
                    "sidecar_decision_status": "SIDECAR_AWARE_SIDECAR_DECISION_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def system_decision_rows(
    packet_decisions: list[dict[str, Any]], scope_decisions: list[dict[str, Any]], sidecar_decisions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    packet_counts = Counter(normalized(row.get("packet_decision_family")) for row in packet_decisions)
    scope_counts = Counter(normalized(row.get("scope_decision_class")) for row in scope_decisions)
    sidecar_counts = Counter(normalized(row.get("sidecar_decision_family")) for row in sidecar_decisions)
    return [
        boundary_row(
            {
                "system_decision_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-DECISION-SYSTEM-0001",
                "packet_decision_rows": len(packet_decisions),
                "scope_decision_rows": len(scope_decisions),
                "sidecar_decision_rows": len(sidecar_decisions),
                "packet_decision_family_counts": dict(sorted(packet_counts.items())),
                "scope_decision_class_counts": dict(sorted(scope_counts.items())),
                "sidecar_decision_family_counts": dict(sorted(sidecar_counts.items())),
                "system_decision": (
                    "Route sidecar-aware packet scores into branch-local decision comparison inputs while carrying "
                    "sidecars as score dampers or scope-review requirements."
                ),
                "system_decision_status": "SIDECAR_AWARE_SYSTEM_DECISION_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def sidecar_decision_bucket_rows(
    packet_decisions: list[dict[str, Any]],
    scope_decisions: list[dict[str, Any]],
    sidecar_decisions: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("packet_decision_family", packet_decisions, "packet_decision_family"),
        ("packet_decision_status", packet_decisions, "packet_decision_status"),
        ("scope_decision_class", scope_decisions, "scope_decision_class"),
        ("sidecar_decision_family", sidecar_decisions, "sidecar_decision_family"),
        ("system_decision_status", system_rows, "system_decision_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "sidecar_decision_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SIDECAR-DECISION-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
