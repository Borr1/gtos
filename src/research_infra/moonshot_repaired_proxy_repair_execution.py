"""Execute repaired-proxy repair work orders against available branch-local fields."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


REPAIR_EXECUTION_SURFACE = "src/research_infra/moonshot_repaired_proxy_repair_execution.py"
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
    output["repair_execution_surface"] = REPAIR_EXECUTION_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def present_fields(row: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if normalized(row.get(field))]


def missing_fields(row: dict[str, Any], fields: list[str]) -> list[str]:
    return [field for field in fields if not normalized(row.get(field))]


def execution_status(family: str, missing: list[str]) -> str:
    if not missing:
        return "REPAIR_EXECUTION_READY_FOR_EXACT_PROXY_RERUN"
    if family == "SCOPE_IDENTITY_REPAIR_REQUIRED":
        return "REPAIR_EXECUTION_BLOCKED_MISSING_SCOPE_IDENTITY_FIELDS"
    if family == "GEOMETRY_FIELD_REPAIR_REQUIRED":
        return "REPAIR_EXECUTION_BLOCKED_MISSING_GEOMETRY_FIELDS"
    return "REPAIR_EXECUTION_BLOCKED_MISSING_DIRECT_IDENTIFIER_FIELDS"


def execution_next_action(status: str) -> str:
    if status == "REPAIR_EXECUTION_READY_FOR_EXACT_PROXY_RERUN":
        return "INCLUDE_IN_EXACT_PROXY_RERUN_INPUT"
    if status == "REPAIR_EXECUTION_BLOCKED_MISSING_SCOPE_IDENTITY_FIELDS":
        return "ACQUIRE_OR_REGENERATE_SCOPE_IDENTITY_FIELDS"
    if status == "REPAIR_EXECUTION_BLOCKED_MISSING_GEOMETRY_FIELDS":
        return "ACQUIRE_OR_REGENERATE_GEOMETRY_FIELDS"
    return "ACQUIRE_OR_REGENERATE_DIRECT_IDENTIFIER_FIELDS"


def repair_execution_rows(work_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(work_rows, 1):
        fields = list(row.get("required_fields") or [])
        missing = missing_fields(row, fields)
        present = present_fields(row, fields)
        family = normalized(row.get("repair_route_family"))
        status = execution_status(family, missing)
        output.append(
            boundary_row(
                {
                    "repair_execution_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXEC-{index:05d}",
                    "input_repair_work_order_row_id": row.get("repair_work_order_row_id"),
                    "input_score_rebuilt_bridge_row_id": row.get("input_score_rebuilt_bridge_row_id"),
                    "input_exact_proxy_bridge_row_id": row.get("input_exact_proxy_bridge_row_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "repair_route_family": family,
                    "required_fields": fields,
                    "present_required_fields": present,
                    "missing_required_fields": missing,
                    "repair_execution_status": status,
                    "repair_execution_next_action": execution_next_action(status),
                    "exact_proxy_rerun_eligible": status == "REPAIR_EXECUTION_READY_FOR_EXACT_PROXY_RERUN",
                }
            )
        )
    return output


def field_coverage_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in execution_rows:
        family = normalized(row.get("repair_route_family"))
        for field in row.get("required_fields") or []:
            grouped[(family, field)].append(row)

    output: list[dict[str, Any]] = []
    for index, ((family, field), rows) in enumerate(sorted(grouped.items()), 1):
        present = sum(1 for row in rows if field in (row.get("present_required_fields") or []))
        missing = len(rows) - present
        output.append(
            boundary_row(
                {
                    "field_coverage_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-FIELD-{index:04d}",
                    "repair_route_family": family,
                    "required_field": field,
                    "work_order_rows": len(rows),
                    "field_present_rows": present,
                    "field_missing_rows": missing,
                    "field_coverage_status": (
                        "REPAIR_FIELD_PRESENT_FOR_ALL_ROWS"
                        if missing == 0
                        else "REPAIR_FIELD_MISSING_FOR_SOME_ROWS"
                    ),
                }
            )
        )
    return output


def execution_batch_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in execution_rows:
        grouped[normalized(row.get("repair_execution_status"))].append(row)

    output: list[dict[str, Any]] = []
    for index, (status, rows) in enumerate(sorted(grouped.items()), 1):
        output.append(
            boundary_row(
                {
                    "repair_execution_batch_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXEC-BATCH-{index:04d}",
                    "repair_execution_status": status,
                    "repair_execution_rows": len(rows),
                    "eligible_rows": sum(1 for row in rows if row.get("exact_proxy_rerun_eligible") is True),
                    "next_action_counts": dict(
                        sorted(Counter(normalized(row.get("repair_execution_next_action")) for row in rows).items())
                    ),
                }
            )
        )
    return output


def rerun_gate_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [row for row in execution_rows if row.get("exact_proxy_rerun_eligible") is True]
    blocked = len(execution_rows) - len(eligible)
    status = (
        "EXACT_PROXY_RERUN_GATE_READY_WITH_REPAIRED_ROWS"
        if eligible
        else "EXACT_PROXY_RERUN_GATE_HELD_ALL_REPAIR_WORK_ORDERS_BLOCKED"
    )
    return [
        boundary_row(
            {
                "rerun_gate_row_id": "OHLC-GTOS-REPAIRED-PROXY-REPAIR-RERUN-GATE-0001",
                "repair_execution_rows": len(execution_rows),
                "rerun_eligible_rows": len(eligible),
                "blocked_repair_rows": blocked,
                "rerun_gate_status": status,
                "rerun_gate_next_action": (
                    "RERUN_EXACT_PROXY_BRIDGE_WITH_ELIGIBLE_REPAIRS"
                    if eligible
                    else "COMPLETE_MISSING_IDENTIFIER_AND_SCOPE_FIELDS_BEFORE_RERUN"
                ),
            }
        )
    ]


def bucket_rows(
    execution_rows: list[dict[str, Any]],
    field_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    specs = [
        ("repair_execution_status", execution_rows, "repair_execution_status"),
        ("repair_execution_next_action", execution_rows, "repair_execution_next_action"),
        ("field_coverage_status", field_rows, "field_coverage_status"),
        ("rerun_gate_status", gate_rows, "rerun_gate_status"),
    ]
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "repair_execution_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXEC-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
