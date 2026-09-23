"""Summarize exhausted branch-local source lookup for repaired-proxy repair rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


REPAIR_SOURCE_EXHAUSTION_SURFACE = "src/research_infra/moonshot_repaired_proxy_repair_source_exhaustion.py"
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
    output["repair_source_exhaustion_surface"] = REPAIR_SOURCE_EXHAUSTION_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def exhaustion_class(field_status: str) -> str:
    if field_status == "FIELD_NOT_FULFILLED_EXACT_JOIN_FIELD_ABSENT":
        return "ROW_KEY_JOINED_BUT_REQUIRED_FIELD_ABSENT_IN_BRANCH_LOCAL_SOURCES"
    if field_status == "FIELD_NOT_FULFILLED_FIELD_PRESENT_WITHOUT_JOIN":
        return "FIELD_EXISTS_IN_SOURCE_FAMILY_BUT_REQUIREMENT_HAS_NO_ROW_KEY_JOIN"
    if field_status == "FIELD_NOT_FULFILLED_SCOPE_MATCH_NOT_ROW_UNIQUE":
        return "FIELD_OBSERVED_AT_SCOPE_BUT_NOT_ROW_UNIQUE"
    return "FIELD_NOT_FOUND_IN_BRANCH_LOCAL_SOURCE_CANDIDATES"


def requirement_exhaustion_rows(
    field_rows: list[dict[str, Any]], lookup_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    lookups_by_requirement: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in lookup_rows:
        lookups_by_requirement[normalized(row.get("input_acquisition_requirement_row_id"))].append(row)

    output: list[dict[str, Any]] = []
    for field_row in field_rows:
        requirement_id = normalized(field_row.get("input_acquisition_requirement_row_id"))
        lookups = lookups_by_requirement.get(requirement_id, [])
        status_counts = Counter(normalized(row.get("lookup_execution_status")) for row in lookups)
        source_candidates = sorted({normalized(row.get("source_candidate_name")) for row in lookups if row.get("source_candidate_name")})
        field_status = normalized(field_row.get("field_fulfillment_status"))
        cls = exhaustion_class(field_status)
        output.append(
            boundary_row(
                {
                    "requirement_exhaustion_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXHAUST-REQ-{len(output) + 1:05d}"
                    ),
                    "input_acquisition_requirement_row_id": requirement_id,
                    "input_repair_execution_row_id": field_row.get("input_repair_execution_row_id"),
                    "missing_required_field": field_row.get("missing_required_field"),
                    "acquisition_source_family": field_row.get("acquisition_source_family"),
                    "lookup_source_attempts": len(lookups),
                    "source_candidates_searched": source_candidates,
                    "lookup_execution_status_counts": dict(sorted(status_counts.items())),
                    "source_rows_scanned_total": sum(int(row.get("source_rows_scanned") or 0) for row in lookups),
                    "source_field_present_rows_total": sum(int(row.get("source_field_present_rows") or 0) for row in lookups),
                    "exact_join_rows_total": sum(int(row.get("exact_join_rows") or 0) for row in lookups),
                    "exact_field_value_rows_total": sum(int(row.get("exact_field_value_rows") or 0) for row in lookups),
                    "scope_field_value_rows_total": sum(int(row.get("scope_field_value_rows") or 0) for row in lookups),
                    "field_fulfillment_status": field_status,
                    "exhaustion_class": cls,
                    "exhaustion_next_action": (
                        "REGENERATE_UPSTREAM_ROW_KEYS_OR_LEAVE_REPAIR_ROW_UNRERUNNABLE_CURRENT_BRANCH"
                    ),
                }
            )
        )
    return output


def source_family_exhaustion_rows(requirement_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in requirement_rows:
        key = (
            normalized(row.get("acquisition_source_family")),
            normalized(row.get("missing_required_field")),
            normalized(row.get("exhaustion_class")),
        )
        grouped[key].append(row)

    output: list[dict[str, Any]] = []
    for (source_family, field, cls), rows in sorted(grouped.items()):
        output.append(
            boundary_row(
                {
                    "source_family_exhaustion_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXHAUST-FAMILY-{len(output) + 1:04d}"
                    ),
                    "acquisition_source_family": source_family,
                    "missing_required_field": field,
                    "exhaustion_class": cls,
                    "requirement_rows": len(rows),
                    "lookup_source_attempts": sum(int(row.get("lookup_source_attempts") or 0) for row in rows),
                    "source_rows_scanned_total": sum(int(row.get("source_rows_scanned_total") or 0) for row in rows),
                    "source_field_present_rows_total": sum(
                        int(row.get("source_field_present_rows_total") or 0) for row in rows
                    ),
                    "exact_join_rows_total": sum(int(row.get("exact_join_rows_total") or 0) for row in rows),
                    "exact_field_value_rows_total": sum(
                        int(row.get("exact_field_value_rows_total") or 0) for row in rows
                    ),
                    "source_family_next_action": (
                        "UPSTREAM_KEY_PROPAGATION_REQUIRED_BEFORE_THIS_FIELD_CAN_REPAIR_CURRENT_ROWS"
                    ),
                }
            )
        )
    return output


def repair_execution_exhaustion_rows(requirement_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in requirement_rows:
        grouped[normalized(row.get("input_repair_execution_row_id"))].append(row)

    output: list[dict[str, Any]] = []
    for execution_id in sorted(grouped):
        rows = grouped[execution_id]
        classes = sorted({normalized(row.get("exhaustion_class")) for row in rows})
        if classes == ["ROW_KEY_JOINED_BUT_REQUIRED_FIELD_ABSENT_IN_BRANCH_LOCAL_SOURCES"]:
            status = "SCOPE_IDENTITY_REPAIR_EXHAUSTED_EXACT_JOIN_FIELDS_ABSENT"
        elif "FIELD_EXISTS_IN_SOURCE_FAMILY_BUT_REQUIREMENT_HAS_NO_ROW_KEY_JOIN" in classes:
            status = "DIRECT_IDENTIFIER_REPAIR_EXHAUSTED_NO_ROW_KEY_JOIN"
        else:
            status = "REPAIR_SOURCE_EXHAUSTED_CURRENT_BRANCH"
        output.append(
            boundary_row(
                {
                    "repair_execution_exhaustion_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXHAUST-EXEC-{len(output) + 1:05d}"
                    ),
                    "input_repair_execution_row_id": execution_id,
                    "requirement_rows": len(rows),
                    "missing_required_fields": sorted({normalized(row.get("missing_required_field")) for row in rows}),
                    "exhaustion_classes": classes,
                    "repair_execution_exhaustion_status": status,
                    "repair_rerun_ready_after_exhaustion": False,
                }
            )
        )
    return output


def source_path_proof_rows(source_candidate_lookup_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in source_candidate_lookup_rows:
        output.append(
            boundary_row(
                {
                    "source_path_proof_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXHAUST-SOURCE-{len(output) + 1:04d}"
                    ),
                    "input_source_candidate_lookup_row_id": row.get("source_candidate_lookup_row_id"),
                    "source_candidate_name": row.get("source_candidate_name"),
                    "missing_required_field": row.get("missing_required_field"),
                    "acquisition_source_family": row.get("acquisition_source_family"),
                    "local_source_path_count": row.get("local_source_path_count"),
                    "source_rows_scanned": row.get("source_rows_scanned"),
                    "field_present_counts": row.get("field_present_counts") or {},
                    "source_candidate_lookup_status": row.get("source_candidate_lookup_status"),
                    "source_path_proof_status": "SOURCE_CANDIDATE_STREAMED_AND_HASHED_IN_LOOKUP_MANIFEST",
                }
            )
        )
    return output


def exhaustion_gate_rows(execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "source_exhaustion_gate_row_id": "OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXHAUST-GATE-0001",
                "repair_execution_rows_checked": len(execution_rows),
                "repair_rerun_ready_rows": 0,
                "source_exhaustion_gate_status": "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH",
                "gate_next_action": "DO_NOT_RERUN_EXACT_PROXY_BRIDGE_AS_REPAIRED_WITH_CURRENT_SOURCE_SET",
            }
        )
    ]


def exhaustion_bucket_rows(
    requirement_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs = [
        ("requirement_exhaustion_class", requirement_rows, "exhaustion_class"),
        ("source_family_exhaustion_class", family_rows, "exhaustion_class"),
        ("repair_execution_exhaustion_status", execution_rows, "repair_execution_exhaustion_status"),
        ("source_path_proof_status", source_rows, "source_path_proof_status"),
    ]
    output: list[dict[str, Any]] = []
    for family, rows, field in specs:
        counter = Counter(normalized(row.get(field)) for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "exhaustion_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-REPAIR-EXHAUST-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
