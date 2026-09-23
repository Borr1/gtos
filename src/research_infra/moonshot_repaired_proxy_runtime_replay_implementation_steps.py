"""Convert ranked runtime replay packets into branch-local implementation steps."""

from __future__ import annotations

from collections import Counter
from typing import Any


RUNTIME_REPLAY_IMPLEMENTATION_STEPS_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_implementation_steps.py"
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
    output["runtime_replay_implementation_steps_surface"] = RUNTIME_REPLAY_IMPLEMENTATION_STEPS_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def implementation_family(registry_family: str) -> str:
    if registry_family == "default_off_repaired_proxy_scorer":
        return "IMPLEMENTATION_FAMILY_DEFAULT_OFF_SCORER"
    if registry_family == "avoid_redesign_repaired_proxy_comparator":
        return "IMPLEMENTATION_FAMILY_AVOID_REDESIGN_COMPARATOR"
    return "IMPLEMENTATION_FAMILY_CONTEXT_PACKET"


def next_step_for(family: str, rank_tier: str) -> tuple[str, str]:
    if family == "IMPLEMENTATION_FAMILY_DEFAULT_OFF_SCORER":
        if rank_tier in {"RANKED_PACKET_DIRECT_CLEAR_BATCH", "RANKED_PACKET_ADVANCE_READY_BATCH"}:
            return (
                "BUILD_DEFAULT_OFF_SCORER_BRANCH_LOCAL_BATCH_SPEC",
                "IMPLEMENTATION_STEP_READY_SCORER_BATCH",
            )
        if rank_tier == "RANKED_PACKET_ADVANCE_WITH_CONTEXT_BATCH":
            return (
                "BUILD_DEFAULT_OFF_SCORER_WITH_CONTEXT_BRANCH_LOCAL_SPEC",
                "IMPLEMENTATION_STEP_CONTEXT_SCORER_BATCH",
            )
        return (
            "CARRY_DEFAULT_OFF_SCORER_CONTEXT_TO_LATER_BRANCH_LOCAL_BATCH",
            "IMPLEMENTATION_STEP_CONTEXT_CARRY_SCORER",
        )
    if family == "IMPLEMENTATION_FAMILY_AVOID_REDESIGN_COMPARATOR":
        if rank_tier in {"RANKED_PACKET_DIRECT_CLEAR_BATCH", "RANKED_PACKET_ADVANCE_READY_BATCH"}:
            return (
                "BUILD_AVOID_REDESIGN_COMPARATOR_BRANCH_LOCAL_BATCH_SPEC",
                "IMPLEMENTATION_STEP_READY_COMPARATOR_BATCH",
            )
        if rank_tier == "RANKED_PACKET_ADVANCE_WITH_CONTEXT_BATCH":
            return (
                "BUILD_AVOID_REDESIGN_COMPARATOR_WITH_CONTEXT_BRANCH_LOCAL_SPEC",
                "IMPLEMENTATION_STEP_CONTEXT_COMPARATOR_BATCH",
            )
        return (
            "CARRY_AVOID_REDESIGN_COMPARATOR_CONTEXT_TO_LATER_BRANCH_LOCAL_BATCH",
            "IMPLEMENTATION_STEP_CONTEXT_CARRY_COMPARATOR",
        )
    return (
        "CARRY_CONTEXT_PACKET_TO_BRANCH_LOCAL_IMPLEMENTATION_PACKET",
        "IMPLEMENTATION_STEP_CONTEXT_PACKET",
    )


def implementation_action_rows(next_packet_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in next_packet_rows:
        family = implementation_family(normalized(row.get("registry_family")))
        action, step_family = next_step_for(family, normalized(row.get("packet_rank_tier")))
        output.append(
            boundary_row(
                {
                    "implementation_action_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-IMPLEMENTATION-ACTION-{len(output) + 1:06d}"
                    ),
                    "input_next_branch_local_packet_row_id": row.get("next_branch_local_packet_row_id"),
                    "input_ranked_advance_packet_row_id": row.get("input_ranked_advance_packet_row_id"),
                    "packet_rank": int(row.get("packet_rank") or 0),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "comparison_packet_role": row.get("comparison_packet_role"),
                    "packet_rank_score": row.get("packet_rank_score"),
                    "packet_rank_tier": row.get("packet_rank_tier"),
                    "coarse_held_scope_rows": int(row.get("coarse_held_scope_rows") or 0),
                    "coarse_held_sidecar_requirement_rows": int(
                        row.get("coarse_held_sidecar_requirement_rows") or 0
                    ),
                    "implementation_family": family,
                    "implementation_next_action": action,
                    "implementation_step_family": step_family,
                    "implementation_action_status": "RUNTIME_REPLAY_IMPLEMENTATION_ACTION_MATERIALIZED",
                }
            )
        )
    return output


def implementation_scope_rollup_rows(action_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in action_rows:
        key = (
            normalized(row.get("symbol")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("registry_family")),
            normalized(row.get("implementation_step_family")),
        )
        grouped.setdefault(key, []).append(row)

    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        ranks = [int(row.get("packet_rank") or 0) for row in rows]
        scores = [float(row.get("packet_rank_score") or 0.0) for row in rows]
        output.append(
            boundary_row(
                {
                    "implementation_scope_rollup_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-IMPLEMENTATION-SCOPE-{len(output) + 1:05d}"
                    ),
                    "symbol": key[0],
                    "route_session": key[1],
                    "horizon_id": key[2],
                    "registry_family": key[3],
                    "implementation_step_family": key[4],
                    "implementation_action_rows": len(rows),
                    "best_packet_rank": min(ranks) if ranks else None,
                    "worst_packet_rank": max(ranks) if ranks else None,
                    "max_packet_rank_score": round(max(scores), 6) if scores else None,
                    "min_packet_rank_score": round(min(scores), 6) if scores else None,
                    "implementation_scope_rollup_status": "RUNTIME_REPLAY_IMPLEMENTATION_SCOPE_ROLLUP_MATERIALIZED",
                }
            )
        )
    return output


def implementation_next_step_rows(action_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in action_rows:
        output.append(
            boundary_row(
                {
                    "implementation_next_step_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-IMPLEMENTATION-NEXT-STEP-{len(output) + 1:06d}"
                    ),
                    "input_implementation_action_row_id": row.get("implementation_action_row_id"),
                    "packet_rank": row.get("packet_rank"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "registry_family": row.get("registry_family"),
                    "implementation_family": row.get("implementation_family"),
                    "implementation_step_family": row.get("implementation_step_family"),
                    "implementation_next_action": row.get("implementation_next_action"),
                    "implementation_next_step_status": "RUNTIME_REPLAY_IMPLEMENTATION_NEXT_STEP_EMITTED",
                }
            )
        )
    return output


def system_implementation_step_rows(
    action_rows: list[dict[str, Any]],
    rollup_rows: list[dict[str, Any]],
    next_step_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    action_counts = Counter(normalized(row.get("implementation_step_family")) for row in action_rows)
    family_counts = Counter(normalized(row.get("implementation_family")) for row in action_rows)
    return [
        boundary_row(
            {
                "system_implementation_step_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-IMPLEMENTATION-STEPS-SYSTEM-0001"
                ),
                "implementation_action_rows": len(action_rows),
                "implementation_scope_rollup_rows": len(rollup_rows),
                "implementation_next_step_rows": len(next_step_rows),
                "implementation_family_counts": dict(sorted(family_counts.items())),
                "implementation_step_family_counts": dict(sorted(action_counts.items())),
                "system_implementation_steps": (
                    "Translate every ranked branch-local packet row into scorer or comparator implementation steps."
                ),
                "system_implementation_step_status": (
                    "RUNTIME_REPLAY_IMPLEMENTATION_STEPS_MATERIALIZED_BRANCH_LOCAL"
                ),
            }
        )
    ]


def implementation_step_bucket_rows(
    action_rows: list[dict[str, Any]],
    rollup_rows: list[dict[str, Any]],
    next_step_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("implementation_family", action_rows, "implementation_family"),
        ("implementation_step_family", action_rows, "implementation_step_family"),
        ("implementation_scope_rollup_status", rollup_rows, "implementation_scope_rollup_status"),
        ("implementation_next_step_status", next_step_rows, "implementation_next_step_status"),
        ("system_implementation_step_status", system_rows, "system_implementation_step_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "implementation_step_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-IMPLEMENTATION-STEPS-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
