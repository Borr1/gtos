"""Materialize branch-local scorer and comparator specs from implementation steps."""

from __future__ import annotations

from collections import Counter
from typing import Any


RUNTIME_REPLAY_SPEC_MATERIALIZATION_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_spec_materialization.py"
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
    output["runtime_replay_spec_materialization_surface"] = RUNTIME_REPLAY_SPEC_MATERIALIZATION_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def spec_context_mode(step_family: str) -> str:
    if step_family in {"IMPLEMENTATION_STEP_READY_SCORER_BATCH", "IMPLEMENTATION_STEP_READY_COMPARATOR_BATCH"}:
        return "SPEC_CONTEXT_READY_BATCH"
    if step_family in {"IMPLEMENTATION_STEP_CONTEXT_SCORER_BATCH", "IMPLEMENTATION_STEP_CONTEXT_COMPARATOR_BATCH"}:
        return "SPEC_CONTEXT_ATTACHED_CONTEXT_BATCH"
    return "SPEC_CONTEXT_CARRY_FORWARD_BATCH"


def scorer_spec_rows(action_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in action_rows:
        if normalized(row.get("implementation_family")) != "IMPLEMENTATION_FAMILY_DEFAULT_OFF_SCORER":
            continue
        output.append(
            boundary_row(
                {
                    "scorer_spec_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-SCORER-{len(output) + 1:06d}"
                    ),
                    "input_implementation_action_row_id": row.get("implementation_action_row_id"),
                    "packet_rank": int(row.get("packet_rank") or 0),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "comparison_packet_role": row.get("comparison_packet_role"),
                    "packet_rank_score": row.get("packet_rank_score"),
                    "implementation_step_family": row.get("implementation_step_family"),
                    "spec_context_mode": spec_context_mode(normalized(row.get("implementation_step_family"))),
                    "branch_local_spec_kind": "DEFAULT_OFF_REPAIRED_PROXY_SCORER_SPEC",
                    "branch_local_spec_action": "MATERIALIZE_DEFAULT_OFF_REPAIRED_PROXY_SCORER_SPEC",
                    "scorer_spec_status": "RUNTIME_REPLAY_SCORER_SPEC_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def comparator_spec_rows(action_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in action_rows:
        if normalized(row.get("implementation_family")) != "IMPLEMENTATION_FAMILY_AVOID_REDESIGN_COMPARATOR":
            continue
        output.append(
            boundary_row(
                {
                    "comparator_spec_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-COMPARATOR-{len(output) + 1:06d}"
                    ),
                    "input_implementation_action_row_id": row.get("implementation_action_row_id"),
                    "packet_rank": int(row.get("packet_rank") or 0),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "registry_family": row.get("registry_family"),
                    "comparison_packet_role": row.get("comparison_packet_role"),
                    "packet_rank_score": row.get("packet_rank_score"),
                    "implementation_step_family": row.get("implementation_step_family"),
                    "spec_context_mode": spec_context_mode(normalized(row.get("implementation_step_family"))),
                    "branch_local_spec_kind": "AVOID_REDESIGN_REPAIRED_PROXY_COMPARATOR_SPEC",
                    "branch_local_spec_action": "MATERIALIZE_AVOID_REDESIGN_REPAIRED_PROXY_COMPARATOR_SPEC",
                    "comparator_spec_status": "RUNTIME_REPLAY_COMPARATOR_SPEC_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def spec_batch_rows(scorer_rows: list[dict[str, Any]], comparator_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    combined = [
        ("DEFAULT_OFF_REPAIRED_PROXY_SCORER_SPEC", row)
        for row in scorer_rows
    ] + [
        ("AVOID_REDESIGN_REPAIRED_PROXY_COMPARATOR_SPEC", row)
        for row in comparator_rows
    ]
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for kind, row in combined:
        key = (
            kind,
            normalized(row.get("symbol")),
            normalized(row.get("route_session")),
            normalized(row.get("spec_context_mode")),
        )
        grouped.setdefault(key, []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        output.append(
            boundary_row(
                {
                    "spec_batch_row_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-BATCH-{len(output) + 1:05d}",
                    "branch_local_spec_kind": key[0],
                    "symbol": key[1],
                    "route_session": key[2],
                    "spec_context_mode": key[3],
                    "spec_rows": len(rows),
                    "best_packet_rank": min(int(row.get("packet_rank") or 0) for row in rows),
                    "max_packet_rank_score": round(max(float(row.get("packet_rank_score") or 0.0) for row in rows), 6),
                    "spec_batch_status": "RUNTIME_REPLAY_SPEC_BATCH_MATERIALIZED_BRANCH_LOCAL",
                }
            )
        )
    return output


def system_spec_materialization_rows(
    scorer_rows: list[dict[str, Any]],
    comparator_rows: list[dict[str, Any]],
    batch_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    context_counts = Counter(normalized(row.get("spec_context_mode")) for row in scorer_rows + comparator_rows)
    return [
        boundary_row(
            {
                "system_spec_materialization_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-MATERIALIZATION-SYSTEM-0001"
                ),
                "scorer_spec_rows": len(scorer_rows),
                "comparator_spec_rows": len(comparator_rows),
                "spec_batch_rows": len(batch_rows),
                "spec_context_mode_counts": dict(sorted(context_counts.items())),
                "system_spec_materialization": (
                    "Materialize ranked implementation steps into branch-local scorer and comparator spec rows."
                ),
                "system_spec_materialization_status": (
                    "RUNTIME_REPLAY_SPEC_MATERIALIZATION_MATERIALIZED_BRANCH_LOCAL"
                ),
            }
        )
    ]


def spec_materialization_bucket_rows(
    scorer_rows: list[dict[str, Any]],
    comparator_rows: list[dict[str, Any]],
    batch_rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("scorer_spec_status", scorer_rows, "scorer_spec_status"),
        ("comparator_spec_status", comparator_rows, "comparator_spec_status"),
        ("spec_context_mode", scorer_rows + comparator_rows, "spec_context_mode"),
        ("spec_batch_status", batch_rows, "spec_batch_status"),
        ("system_spec_materialization_status", system_rows, "system_spec_materialization_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "spec_materialization_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-SPEC-MATERIALIZATION-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
