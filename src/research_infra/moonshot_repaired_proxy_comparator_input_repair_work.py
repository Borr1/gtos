"""Assemble score-bridge comparator inputs and repair work orders."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


COMPARATOR_INPUT_SURFACE = "src/research_infra/moonshot_repaired_proxy_comparator_input_repair_work.py"
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
    output["comparator_input_surface"] = COMPARATOR_INPUT_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def comparator_input_family(registry_family: str) -> str:
    if registry_family == "default_off_repaired_proxy_scorer":
        return "DEFAULT_OFF_SCORER_COMPARATOR_INPUT"
    if registry_family == "avoid_redesign_repaired_proxy_comparator":
        return "AVOID_REDESIGN_COMPARATOR_INPUT"
    return "UNKNOWN_COMPARATOR_INPUT_FAMILY"


def comparator_input_rows(packet_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(packet_rows, 1):
        registry_family = normalized(row.get("rerun_registry_family"))
        output.append(
            boundary_row(
                {
                    "comparator_input_row_id": f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-INPUT-{index:05d}",
                    "input_comparator_packet_row_id": row.get("comparator_packet_row_id"),
                    "input_action_scope_row_id": row.get("input_action_scope_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "rerun_registry_family": registry_family,
                    "comparator_input_family": comparator_input_family(registry_family),
                    "comparator_input_status": "COMPARATOR_INPUT_READY_BRANCH_LOCAL_PACKET_ONLY",
                    "comparator_input_use": "BRANCH_LOCAL_RESEARCH_COMPARATOR_ASSEMBLY_ONLY",
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


def comparator_symbol_queue_rows(input_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[
            (
                normalized(row.get("symbol")),
                normalized(row.get("route_session")),
                normalized(row.get("horizon_id")),
            )
        ].append(row)

    output: list[dict[str, Any]] = []
    for index, ((symbol, route_session, horizon_id), rows) in enumerate(sorted(grouped.items()), 1):
        family_counts = Counter(normalized(row.get("comparator_input_family")) for row in rows)
        bridge_rows = sum(int(row.get("bridge_rows") or 0) for row in rows)
        output.append(
            boundary_row(
                {
                    "comparator_symbol_queue_row_id": f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-SYMBOL-{index:04d}",
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "comparator_input_rows": len(rows),
                    "bridge_rows": bridge_rows,
                    "family_counts": dict(sorted(family_counts.items())),
                    "symbol_queue_status": "COMPARATOR_SYMBOL_QUEUE_READY_BRANCH_LOCAL_PACKET_ONLY",
                }
            )
        )
    return output


def work_order_required_fields(family: str) -> list[str]:
    if family == "SCOPE_IDENTITY_REPAIR_REQUIRED":
        return ["symbol", "route_session", "horizon_id", "source_component"]
    if family == "GEOMETRY_FIELD_REPAIR_REQUIRED":
        return ["entry_price", "stop_loss", "take_profit", "direction", "instrument_tick_size"]
    return ["direct_trade_candidate_identifier", "ticket_identifier", "candidate_lock_metadata"]


def repair_work_order_rows(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(repair_rows, 1):
        family = normalized(row.get("repair_route_family"))
        output.append(
            boundary_row(
                {
                    "repair_work_order_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-WORK-{index:05d}",
                    "input_repair_routing_row_id": row.get("repair_routing_row_id"),
                    "input_score_rebuilt_bridge_row_id": row.get("input_score_rebuilt_bridge_row_id"),
                    "input_exact_proxy_bridge_row_id": row.get("input_exact_proxy_bridge_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "primitive_flag": row.get("primitive_flag"),
                    "repair_route_family": family,
                    "repair_work_order_status": "REPAIR_WORK_ORDER_READY_REQUIREMENTS_ONLY",
                    "required_fields": work_order_required_fields(family),
                    "post_repair_action": "RERUN_EXACT_PROXY_BRIDGE_AFTER_WORK_ORDER_COMPLETION",
                }
            )
        )
    return output


def repair_batch_rows(work_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in work_rows:
        grouped[normalized(row.get("repair_route_family"))].append(row)

    output: list[dict[str, Any]] = []
    for index, (family, rows) in enumerate(sorted(grouped.items()), 1):
        output.append(
            boundary_row(
                {
                    "repair_batch_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-BATCH-{index:04d}",
                    "repair_route_family": family,
                    "repair_work_order_rows": len(rows),
                    "required_field_sets": sorted(
                        {",".join(row.get("required_fields") or []) for row in rows}
                    ),
                    "repair_batch_status": "REPAIR_BATCH_READY_REQUIREMENTS_ONLY",
                }
            )
        )
    return output


def rerun_plan_rows(
    input_rows: list[dict[str, Any]],
    work_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        (
            "ASSEMBLE_COMPARATOR_INPUT_PACKET",
            len(input_rows),
            "Comparator input rows are ready for branch-local research assembly.",
        ),
        (
            "COMPLETE_IDENTIFIER_AND_SCOPE_REPAIR_WORK_ORDERS",
            len(work_rows),
            "Repair work orders must be completed before another exact/proxy bridge pass.",
        ),
        (
            "RERUN_EXACT_PROXY_BRIDGE_AFTER_REPAIRS",
            len(work_rows),
            "The next exact/proxy bridge pass should consume completed repair work orders.",
        ),
        (
            "REBUILD_SCORE_BRIDGE_ACTION_PACKET_AFTER_RERUN",
            len(input_rows),
            "Action packet should be rebuilt after repaired exact/proxy bridge outputs exist.",
        ),
    ]
    output: list[dict[str, Any]] = []
    for index, (step, rows, description) in enumerate(specs, 1):
        output.append(
            boundary_row(
                {
                    "rerun_plan_row_id": f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-RERUN-PLAN-{index:04d}",
                    "step_order": index,
                    "rerun_plan_step": step,
                    "dependent_rows": rows,
                    "rerun_plan_status": "BRANCH_LOCAL_RERUN_PLAN_READY",
                    "description": description,
                }
            )
        )
    return output


def bucket_rows(
    input_rows: list[dict[str, Any]],
    work_rows: list[dict[str, Any]],
    batch_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    specs = [
        ("comparator_input_family", input_rows, "comparator_input_family"),
        ("comparator_input_status", input_rows, "comparator_input_status"),
        ("repair_route_family", work_rows, "repair_route_family"),
        ("repair_work_order_status", work_rows, "repair_work_order_status"),
        ("repair_batch_status", batch_rows, "repair_batch_status"),
    ]
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "comparator_input_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-COMPARATOR-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
