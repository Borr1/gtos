"""Create acquisition requirements for blocked repaired-proxy repair executions."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


REPAIR_ACQUISITION_SURFACE = "src/research_infra/moonshot_repaired_proxy_repair_acquisition.py"
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
    output["repair_acquisition_surface"] = REPAIR_ACQUISITION_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def acquisition_source_family(field: str) -> str:
    if field == "direct_trade_candidate_identifier":
        return "CANDIDATE_OR_DECISION_IDENTIFIER_SOURCE"
    if field == "ticket_identifier":
        return "BROKER_ORDER_DEAL_TICKET_SOURCE"
    if field == "candidate_lock_metadata":
        return "CANDIDATE_LOCK_OR_DECISION_METADATA_SOURCE"
    if field in {"symbol", "route_session", "horizon_id"}:
        return "SCOPE_IDENTITY_SOURCE"
    return "GENERIC_REPAIR_SOURCE"


def acquisition_requirement_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in execution_rows:
        for field in row.get("missing_required_fields") or []:
            output.append(
                boundary_row(
                    {
                        "acquisition_requirement_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-ACQ-REQ-{len(output) + 1:05d}"
                        ),
                        "input_repair_execution_row_id": row.get("repair_execution_row_id"),
                        "input_repair_work_order_row_id": row.get("input_repair_work_order_row_id"),
                        "input_exact_proxy_bridge_row_id": row.get("input_exact_proxy_bridge_row_id"),
                        "repair_route_family": row.get("repair_route_family"),
                        "repair_execution_status": row.get("repair_execution_status"),
                        "symbol": row.get("symbol"),
                        "route_session": row.get("route_session"),
                        "horizon_id": row.get("horizon_id"),
                        "source_component": row.get("source_component"),
                        "missing_required_field": field,
                        "acquisition_source_family": acquisition_source_family(field),
                        "acquisition_requirement_status": "ACQUISITION_REQUIRED_FIELD_MISSING",
                        "acquisition_next_action": "ACQUIRE_OR_REGENERATE_REQUIRED_FIELD_BEFORE_REPAIR_RERUN",
                    }
                )
            )
    return output


def acquisition_batch_rows(requirement_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in requirement_rows:
        grouped[(normalized(row.get("repair_route_family")), normalized(row.get("missing_required_field")))].append(row)

    output: list[dict[str, Any]] = []
    for index, ((family, field), rows) in enumerate(sorted(grouped.items()), 1):
        source_family = acquisition_source_family(field)
        output.append(
            boundary_row(
                {
                    "acquisition_batch_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-ACQ-BATCH-{index:04d}",
                    "repair_route_family": family,
                    "missing_required_field": field,
                    "acquisition_source_family": source_family,
                    "acquisition_requirement_rows": len(rows),
                    "affected_execution_rows": len({row.get("input_repair_execution_row_id") for row in rows}),
                    "acquisition_batch_status": "ACQUISITION_BATCH_READY_FIELD_REQUIREMENTS_ONLY",
                }
            )
        )
    return output


def source_candidate_rows(batch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_map = {
        "CANDIDATE_OR_DECISION_IDENTIFIER_SOURCE": [
            "candidate_records_or_decision_rows",
            "shadow_candidate_feature_rows",
            "trade_record_rows",
        ],
        "BROKER_ORDER_DEAL_TICKET_SOURCE": [
            "mt5_order_history",
            "mt5_deal_history",
            "broker_actual_r_exports",
        ],
        "CANDIDATE_LOCK_OR_DECISION_METADATA_SOURCE": [
            "candidate_lock_or_snapshot_metadata",
            "decision_packet_metadata",
            "execution_intent_metadata",
        ],
        "SCOPE_IDENTITY_SOURCE": [
            "scope_registry_rows",
            "execution_spec_rows",
            "numeric_shadow_event_rows",
        ],
    }
    output: list[dict[str, Any]] = []
    for batch in batch_rows:
        source_family = normalized(batch.get("acquisition_source_family"))
        for source_name in source_map.get(source_family, ["branch_local_source_search"]):
            output.append(
                boundary_row(
                    {
                        "source_candidate_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-ACQ-SRC-{len(output) + 1:04d}",
                        "input_acquisition_batch_row_id": batch.get("acquisition_batch_row_id"),
                        "missing_required_field": batch.get("missing_required_field"),
                        "acquisition_source_family": source_family,
                        "source_candidate_name": source_name,
                        "source_candidate_status": "SOURCE_CANDIDATE_REQUIRES_BRANCH_LOCAL_LOOKUP",
                    }
                )
            )
    return output


def unblock_plan_rows(requirement_rows: list[dict[str, Any]], batch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        (
            "RUN_BRANCH_LOCAL_SOURCE_LOOKUPS_FOR_REQUIRED_FIELDS",
            len(requirement_rows),
            "Resolve missing fields from explicit source candidates without opening result validation.",
        ),
        (
            "RERUN_REPAIR_EXECUTION_AFTER_FIELD_ACQUISITION",
            len(requirement_rows),
            "Repair execution remains the gate before exact/proxy bridge rerun.",
        ),
        (
            "RERUN_EXACT_PROXY_BRIDGE_ONLY_AFTER_ELIGIBLE_REPAIR_ROWS_EXIST",
            len(batch_rows),
            "Exact/proxy bridge rerun requires at least one repaired row eligible at the repair gate.",
        ),
    ]
    output: list[dict[str, Any]] = []
    for index, (step, rows, description) in enumerate(specs, 1):
        output.append(
            boundary_row(
                {
                    "unblock_plan_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-ACQ-PLAN-{index:04d}",
                    "step_order": index,
                    "unblock_plan_step": step,
                    "dependent_rows": rows,
                    "unblock_plan_status": "ACQUISITION_UNBLOCK_PLAN_READY",
                    "description": description,
                }
            )
        )
    return output


def bucket_rows(
    requirement_rows: list[dict[str, Any]],
    batch_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    specs = [
        ("missing_required_field", requirement_rows, "missing_required_field"),
        ("acquisition_source_family", requirement_rows, "acquisition_source_family"),
        ("acquisition_batch_status", batch_rows, "acquisition_batch_status"),
        ("source_candidate_status", source_rows, "source_candidate_status"),
    ]
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "acquisition_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-ACQ-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
