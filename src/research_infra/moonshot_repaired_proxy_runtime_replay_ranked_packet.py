"""Rank advance packet applications with held-scope context."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


RUNTIME_REPLAY_RANKED_PACKET_SURFACE = "src/research_infra/moonshot_repaired_proxy_runtime_replay_ranked_packet.py"
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
    output["runtime_replay_ranked_packet_surface"] = RUNTIME_REPLAY_RANKED_PACKET_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def coarse_context_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("registry_family")),
    )


def held_scope_context_rows(held_scope_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in held_scope_rows:
        output.append(
            boundary_row(
                {
                    "held_scope_context_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RANKED-PACKET-HELD-CONTEXT-{len(output) + 1:05d}"
                    ),
                    "input_held_review_scope_row_id": row.get("held_review_scope_row_id"),
                    "input_scope_review_comparison_row_id": row.get("scope_review_comparison_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "registry_family": row.get("registry_family"),
                    "scope_review_comparison_class": row.get("scope_review_comparison_class"),
                    "held_packet_rows": int(row.get("held_packet_rows") or 0),
                    "sidecar_scope_requirement_rows": int(row.get("sidecar_scope_requirement_rows") or 0),
                    "held_scope_context_status": "RUNTIME_REPLAY_HELD_SCOPE_CONTEXT_AVAILABLE_FOR_PACKET_RANKING",
                }
            )
        )
    return output


def held_context_index(held_context_rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, int]]:
    grouped: dict[tuple[str, str, str], dict[str, int]] = defaultdict(
        lambda: {"held_scope_rows": 0, "held_packet_rows": 0, "held_sidecar_requirement_rows": 0}
    )
    for row in held_context_rows:
        key = coarse_context_key(row)
        grouped[key]["held_scope_rows"] += 1
        grouped[key]["held_packet_rows"] += int(row.get("held_packet_rows") or 0)
        grouped[key]["held_sidecar_requirement_rows"] += int(row.get("sidecar_scope_requirement_rows") or 0)
    return dict(grouped)


def packet_rank_score(packet: dict[str, Any], held_context: dict[str, int]) -> float:
    base_score = as_float(packet.get("sidecar_aware_comparison_score"))
    family = normalized(packet.get("packet_application_family"))
    scope_class = normalized(packet.get("scope_review_comparison_class"))
    clear_bonus = 0.10 if family == "PACKET_APPLICATION_CLEAR_ADVANCE" else 0.03
    attached_review_penalty = 0.10 if "WITH_ATTACHED_REVIEW_CONTEXT" in scope_class else 0.0
    scope_requirement_penalty = min(0.20, int(packet.get("scope_sidecar_requirement_rows") or 0) * 0.01)
    scope_held_packet_penalty = min(0.15, int(packet.get("scope_held_packet_rows") or 0) * 0.005)
    coarse_held_penalty = min(
        0.20,
        held_context.get("held_scope_rows", 0) * 0.01
        + held_context.get("held_sidecar_requirement_rows", 0) * 0.0005,
    )
    score = base_score + clear_bonus - attached_review_penalty - scope_requirement_penalty
    score -= scope_held_packet_penalty + coarse_held_penalty
    return round(max(0.0, min(1.25, score)), 6)


def rank_tier(packet: dict[str, Any], score: float, held_context: dict[str, int]) -> str:
    scope_class = normalized(packet.get("scope_review_comparison_class"))
    family = normalized(packet.get("packet_application_family"))
    attached_review = "WITH_ATTACHED_REVIEW_CONTEXT" in scope_class
    if score >= 0.95 and family == "PACKET_APPLICATION_CLEAR_ADVANCE" and not attached_review:
        return "RANKED_PACKET_DIRECT_CLEAR_BATCH"
    if score >= 0.80 and not attached_review:
        return "RANKED_PACKET_ADVANCE_READY_BATCH"
    if score >= 0.65:
        return "RANKED_PACKET_ADVANCE_WITH_CONTEXT_BATCH"
    if held_context.get("held_scope_rows", 0):
        return "RANKED_PACKET_ADVANCE_WITH_HELD_SCOPE_PRESSURE"
    return "RANKED_PACKET_ADVANCE_LOW_PRIORITY_CONTEXT"


def ranked_advance_packet_rows(
    advance_packet_rows_in: list[dict[str, Any]], held_context_rows_in: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    index = held_context_index(held_context_rows_in)
    unsorted: list[dict[str, Any]] = []
    for row in advance_packet_rows_in:
        held_context = index.get(coarse_context_key(row), {})
        score = packet_rank_score(row, held_context)
        tier = rank_tier(row, score, held_context)
        unsorted.append(
            {
                "input_advance_packet_row_id": row.get("advance_packet_row_id"),
                "input_packet_scope_comparison_row_id": row.get("packet_scope_comparison_row_id"),
                "symbol": row.get("symbol"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "source_component": row.get("source_component"),
                "registry_family": row.get("registry_family"),
                "comparison_packet_role": row.get("comparison_packet_role"),
                "packet_application_family": row.get("packet_application_family"),
                "sidecar_aware_comparison_score": row.get("sidecar_aware_comparison_score"),
                "scope_application_family": row.get("scope_application_family"),
                "scope_review_comparison_class": row.get("scope_review_comparison_class"),
                "scope_sidecar_requirement_rows": int(row.get("scope_sidecar_requirement_rows") or 0),
                "scope_held_packet_rows": int(row.get("scope_held_packet_rows") or 0),
                "coarse_held_scope_rows": int(held_context.get("held_scope_rows", 0)),
                "coarse_held_packet_rows": int(held_context.get("held_packet_rows", 0)),
                "coarse_held_sidecar_requirement_rows": int(
                    held_context.get("held_sidecar_requirement_rows", 0)
                ),
                "packet_rank_score": score,
                "packet_rank_tier": tier,
                "packet_rank_status": "RUNTIME_REPLAY_ADVANCE_PACKET_RANKED_BRANCH_LOCAL",
            }
        )
    unsorted.sort(
        key=lambda item: (
            -as_float(item.get("packet_rank_score")),
            normalized(item.get("symbol")),
            normalized(item.get("route_session")),
            normalized(item.get("registry_family")),
            normalized(item.get("horizon_id")),
            normalized(item.get("input_advance_packet_row_id")),
        )
    )
    output: list[dict[str, Any]] = []
    for index_value, item in enumerate(unsorted, 1):
        ranked = dict(item)
        ranked["ranked_advance_packet_row_id"] = (
            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RANKED-PACKET-ADVANCE-{index_value:06d}"
        )
        ranked["packet_rank"] = index_value
        output.append(boundary_row(ranked))
    return output


def next_branch_local_packet_rows(ranked_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in ranked_rows:
        output.append(
            boundary_row(
                {
                    "next_branch_local_packet_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-NEXT-BRANCH-PACKET-{len(output) + 1:06d}"
                    ),
                    "input_ranked_advance_packet_row_id": row.get("ranked_advance_packet_row_id"),
                    "packet_rank": row.get("packet_rank"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "comparison_packet_role": row.get("comparison_packet_role"),
                    "packet_rank_score": row.get("packet_rank_score"),
                    "packet_rank_tier": row.get("packet_rank_tier"),
                    "coarse_held_scope_rows": row.get("coarse_held_scope_rows"),
                    "coarse_held_sidecar_requirement_rows": row.get(
                        "coarse_held_sidecar_requirement_rows"
                    ),
                    "next_branch_local_packet_action": "MATERIALIZE_RANKED_ADVANCE_PACKET_FOR_NEXT_BRANCH_LOCAL_PASS",
                    "next_branch_local_packet_status": "RUNTIME_REPLAY_NEXT_BRANCH_LOCAL_PACKET_MATERIALIZED",
                }
            )
        )
    return output


def system_ranked_packet_rows(
    ranked_rows: list[dict[str, Any]],
    held_context_rows_in: list[dict[str, Any]],
    next_packet_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tier_counts = Counter(normalized(row.get("packet_rank_tier")) for row in ranked_rows)
    return [
        boundary_row(
            {
                "system_ranked_packet_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RANKED-PACKET-SYSTEM-0001",
                "ranked_advance_packet_rows": len(ranked_rows),
                "held_scope_context_rows": len(held_context_rows_in),
                "next_branch_local_packet_rows": len(next_packet_rows),
                "packet_rank_tier_counts": dict(sorted(tier_counts.items())),
                "system_ranked_packet": (
                    "Rank all advance packet applications with held-scope pressure and carry every ranked row "
                    "into the next branch-local packet."
                ),
                "system_ranked_packet_status": "RUNTIME_REPLAY_RANKED_PACKET_MATERIALIZED_BRANCH_LOCAL",
            }
        )
    ]


def ranked_packet_bucket_rows(
    ranked_rows: list[dict[str, Any]],
    held_context_rows_in: list[dict[str, Any]],
    next_packet_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("packet_rank_tier", ranked_rows, "packet_rank_tier"),
        ("held_scope_context_status", held_context_rows_in, "held_scope_context_status"),
        ("next_branch_local_packet_status", next_packet_rows, "next_branch_local_packet_status"),
        ("system_ranked_packet_status", system_rows, "system_ranked_packet_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "ranked_packet_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-RANKED-PACKET-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
