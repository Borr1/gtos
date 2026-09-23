from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_NUMERIC_R_RESOLUTION_LEDGER_{DATE}.jsonl"
FIELD_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_OUTPUT_MANIFEST_{DATE}.json"

COUNTED_RESULT_FIELDS = {
    "exact_r",
    "exact_r_reference",
    "materialized_proxy_r",
    "local_non_account_r_reference",
    "exact_proxy_delta",
}

CURRENT_PROXY_SOURCE_FIELDS = {
    "after_proxy_r",
    "strategy_proxy_r",
}

NON_RESULT_DISTANCE_FIELDS = {
    "m15_nearest_distance_to_entry_r",
    "nearest_distance_to_entry_r",
    "entry_offset_m15_hard_no_fill_min_distance_r",
    "entry_offset_m15_nearest_distance_to_entry_r",
}

PREFILL_OWNER_REFERENCE_FIELDS = {
    "prefill_proxy_reference_r",
    "linked_prefill_after_proxy_r",
    "linked_prefill_before_proxy_r",
}

ENTRY_OFFSET_OWNER_REFERENCE_FIELDS = {
    "entry_offset_after_entry_proxy_r",
    "linked_entry_offset_after_proxy_r",
    "linked_entry_offset_before_proxy_r",
    "linked_entry_offset_selected_proxy_r",
}

ADVERSE_AVOID_CONTEXT_REFERENCE_FIELDS = {
    "gbpjpy_long_adverse_avoid_saved_proxy_r",
}

FVG_BOUNDS_REFERENCE_FIELDS = {
    "before_fvg_ob_exact_bounds_requirement_after_proxy_r",
    "fvg_ob_exact_bounds_proxy_reference_r",
    "selected_shift_proxy_r",
}

SOURCE_INTERVAL_REFERENCE_FIELDS = {
    "ordering_proxy_lower_r",
    "ordering_proxy_midpoint_r",
    "ordering_proxy_upper_r",
    "source_cost_rstyle_lower_r",
    "source_cost_rstyle_midpoint_r",
    "source_cost_rstyle_upper_r",
    "source_provenance_rstyle_lower_reference",
    "source_provenance_rstyle_midpoint_reference",
    "source_provenance_rstyle_upper_reference",
    "before_residual_source_proxy_redesign_after_proxy_r",
}

MERGED_DUPLICATE_REFERENCE_FIELDS = {
    "merged_duplicate_proxy_reference_r",
    "before_structural_duplicate_merge_after_proxy_r",
    "before_fvg_duplicate_merge_after_proxy_r",
    "before_pending_duplicate_merge_after_proxy_r",
}

PENDING_HYPOTHETICAL_REFERENCE_FIELDS = {
    "before_proxy_r",
    "pending_hypothetical_proxy_reference_r",
    "before_pending_tick_action_after_proxy_r",
    "pending_scorer_metadata_refresh_recomputed_proxy_r",
}

PREVIOUS_STATE_REFERENCE_FIELDS = {
    "action_decision_recomputed_proxy_r",
    "source_pending_metadata_recomputed_proxy_r",
    "before_pending_lifecycle_source_after_proxy_r",
}

RESOLUTION_METADATA = {
    "CURRENT_PROXY_SOURCE_FIELD_ALREADY_MATERIALIZED": {
        "counted_as_proxy_r": False,
        "ledger_effect": "SOURCE_FIELD_VALUE_ALREADY_REFLECTED_IN_CURRENT_MATERIALIZED_PROXY_R",
        "downstream_path": "current_exact_or_proxy_owner_row_materialized_in_action_ledger",
        "owner_reference_policy": "current_row_materialized_proxy_r_or_exact_r_reference_is_the_counted_owner",
        "duplicate_policy": "do_not_add_a_second_proxy_sum_for_the_same row",
    },
    "DUPLICATE_PROXY_REFERENCE_OWNER_MERGED": {
        "counted_as_proxy_r": False,
        "ledger_effect": "REFERENCE_ONLY_DUPLICATE_OWNER_ALREADY_COUNTS_OR_CURRENT_OWNER_EXCLUDED",
        "downstream_path": "deduplicated_owner_or_unique_variant_redesign",
        "owner_reference_policy": "merged_owner_row_keeps_the countable proxy; duplicate row keeps reference evidence",
        "duplicate_policy": "merge_duplicate_proxy_not_additive",
    },
    "PENDING_HYPOTHETICAL_REFERENCE_NOT_DISTINCT": {
        "counted_as_proxy_r": False,
        "ledger_effect": "REFERENCE_ONLY_NO_LIVE_PENDING_INTENT_OWNER",
        "downstream_path": "source_bound_pending_intent_scorer_or_entry_geometry_owner",
        "owner_reference_policy": "pending_intent_owner_required_before this reference can be counted",
        "duplicate_policy": "hypothetical_reference_not_additive_to_current_proxy_sum",
    },
    "PREFILL_OWNER_REFERENCE_NOT_DUPLICATED": {
        "counted_as_proxy_r": False,
        "ledger_effect": "REFERENCE_ONLY_ENTRY_OFFSET_OWNER_COUNTS_PROXY",
        "downstream_path": "entry_offset_owner_merge_or_retest_control",
        "owner_reference_policy": "entry_offset_or_prefill_owner_row retains countable proxy_r",
        "duplicate_policy": "linked_prefill_reference_not_additive",
    },
    "ENTRY_OFFSET_PROXY_REFERENCE_OWNER_MATERIALIZED": {
        "counted_as_proxy_r": False,
        "ledger_effect": "REFERENCE_ONLY_ENTRY_OFFSET_PROXY_ALREADY_MATERIALIZED_OR_OWNER_LINKED",
        "downstream_path": "entry_offset_owner_merge_or_concentration_guarded_candidate",
        "owner_reference_policy": "entry_offset owner/reference relation is preserved; current action row count remains unchanged",
        "duplicate_policy": "linked_entry_offset_reference_not_additive",
    },
    "ADVERSE_AVOID_SAVED_R_CONTEXT_REFERENCE_NOT_CURRENT_OWNER": {
        "counted_as_proxy_r": False,
        "ledger_effect": "AVOID_CONTEXT_SAVED_R_REFERENCE_NOT_A_CURRENT_TRADE_RESULT_OWNER",
        "downstream_path": "gbpjpy_adverse_avoid_filter_or_context_feature",
        "owner_reference_policy": "avoid-saved-R remains context evidence; current materialized proxy stays the action owner",
        "duplicate_policy": "saved_R_context_reference_not_additive_to_proxy_sum",
    },
    "SOURCE_INTERVAL_OR_RSTYLE_REFERENCE_REDESIGN": {
        "counted_as_proxy_r": False,
        "ledger_effect": "INTERVAL_REFERENCE_FOR_REDESIGN_OR_AVOID_CONTEXT_NOT_POINT_OWNER",
        "downstream_path": "exact_ordering_source_repair_or_avoid_context_feature",
        "owner_reference_policy": "interval field supplies bounded context until point owner exists",
        "duplicate_policy": "interval_bounds_not_summed_with_midpoint_or_current_proxy",
    },
    "FVG_BOUNDS_REFERENCE_NOT_STANDALONE_CONFLUENCE": {
        "counted_as_proxy_r": False,
        "ledger_effect": "REFERENCE_ONLY_FVG_GEOMETRY_WITHOUT_STANDALONE_CONFLUENCE_OWNER",
        "downstream_path": "standalone_fvg_or_source_capture_redesign",
        "owner_reference_policy": "standalone FVG owner requires exact bounds and confluence source identity",
        "duplicate_policy": "FVG_bounds_reference_not_additive",
    },
    "DISTANCE_METRIC_NOT_R_RESULT": {
        "counted_as_proxy_r": False,
        "ledger_effect": "DISTANCE_IN_R_UNITS_NOT_PROFIT_LOSS_RESULT",
        "downstream_path": "entry_distance_feature_or_fillability_context",
        "owner_reference_policy": "distance feature has no profit/loss owner",
        "duplicate_policy": "distance_metric_not_countable_result",
    },
    "PREVIOUS_STATE_PROVENANCE_REFERENCE": {
        "counted_as_proxy_r": False,
        "ledger_effect": "PROVENANCE_OF_PRIOR_LEDGER_STATE_NOT_CURRENT_RESULT_OWNER",
        "downstream_path": "current_branch_decision_already_consumes_or_excludes_prior_value",
        "owner_reference_policy": "current row action class and current proxy/exact fields supersede previous-state value",
        "duplicate_policy": "previous_state_reference_not_additive",
    },
}

MATERIALIZATION_RESULT_SCOPE = {
    "result_use": "RESULT_MATERIALIZATION_REQUIRED",
    "source_operation": "RESIDUAL_NUMERIC_RLIKE_FIELD_CLASSIFICATION",
    "ledger_effect": "ROW_LEVEL_REFERENCE_DUPLICATE_INTERVAL_DISTANCE_AND_PROVENANCE_RESOLUTION",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_r_like_field(field: str) -> bool:
    lowered = field.lower()
    return (
        field.endswith("_r")
        or field.endswith("_proxy_r")
        or field.endswith("_midpoint_r")
        or field.endswith("_lower_r")
        or field.endswith("_upper_r")
        or "rstyle" in lowered
    )


def classify_field(field: str) -> str | None:
    if field in CURRENT_PROXY_SOURCE_FIELDS:
        return "CURRENT_PROXY_SOURCE_FIELD_ALREADY_MATERIALIZED"
    if field in NON_RESULT_DISTANCE_FIELDS:
        return "DISTANCE_METRIC_NOT_R_RESULT"
    if field in ENTRY_OFFSET_OWNER_REFERENCE_FIELDS:
        return "ENTRY_OFFSET_PROXY_REFERENCE_OWNER_MATERIALIZED"
    if field in ADVERSE_AVOID_CONTEXT_REFERENCE_FIELDS:
        return "ADVERSE_AVOID_SAVED_R_CONTEXT_REFERENCE_NOT_CURRENT_OWNER"
    if field in PREFILL_OWNER_REFERENCE_FIELDS:
        return "PREFILL_OWNER_REFERENCE_NOT_DUPLICATED"
    if field in FVG_BOUNDS_REFERENCE_FIELDS:
        return "FVG_BOUNDS_REFERENCE_NOT_STANDALONE_CONFLUENCE"
    if field in SOURCE_INTERVAL_REFERENCE_FIELDS:
        return "SOURCE_INTERVAL_OR_RSTYLE_REFERENCE_REDESIGN"
    if field in MERGED_DUPLICATE_REFERENCE_FIELDS:
        return "DUPLICATE_PROXY_REFERENCE_OWNER_MERGED"
    if field in PENDING_HYPOTHETICAL_REFERENCE_FIELDS:
        return "PENDING_HYPOTHETICAL_REFERENCE_NOT_DISTINCT"
    if field in PREVIOUS_STATE_REFERENCE_FIELDS:
        return "PREVIOUS_STATE_PROVENANCE_REFERENCE"
    if field.startswith("before_"):
        return "PREVIOUS_STATE_PROVENANCE_REFERENCE"
    return None


def candidate_session(candidate_id: Any, row: dict[str, Any]) -> str:
    if row.get("route_session"):
        return str(row["route_session"])
    if row.get("session"):
        return str(row["session"])
    text = str(candidate_id or "")
    if "_ny_" in text or "|ny_" in text:
        return "ny"
    if "_tokyo_" in text or "|tokyo_" in text:
        return "tokyo"
    if "_london_" in text or "|london_" in text:
        return "london"
    return "unknown"


def row_field_entries(row: dict[str, Any], line_no: int) -> list[dict[str, Any]]:
    counted_proxy = numeric(row.get("materialized_proxy_r")) is not None
    counted_exact = numeric(row.get("exact_r_reference")) is not None
    entries: list[dict[str, Any]] = []
    for field, value in row.items():
        if field in COUNTED_RESULT_FIELDS or not is_r_like_field(str(field)):
            continue
        number = numeric(value)
        if number is None:
            continue
        status = classify_field(str(field))
        entry = {
            "schema_version": "main_orch24_residual_numeric_r_field_resolution_v1",
            "input_line_no": line_no,
            "source_action_row_id": row.get("row_id"),
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "session": candidate_session(row.get("candidate_id"), row),
            "branch_decision": row.get("branch_decision"),
            "action_class": row.get("action_class"),
            "exact_r_materialization_status": row.get("exact_r_materialization_status"),
            "field_name": field,
            "field_value": number,
            "resolution_status": status,
            "counted_exact_or_proxy_owner_already_present": counted_proxy or counted_exact,
            "materialized_proxy_r": row.get("materialized_proxy_r"),
            "exact_r_reference": row.get("exact_r_reference"),
        }
        if status:
            entry.update(RESOLUTION_METADATA[status])
        else:
            entry.update(
                {
                    "counted_as_proxy_r": False,
                    "ledger_effect": "UNCLASSIFIED_REQUIRES_BUILDER_REPAIR",
                    "downstream_path": "repair_this_builder_before_checkpoint",
                }
            )
        entries.append(entry)
    return entries


def build() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    generated_utc = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    source_hashes = {str(INPUT_LEDGER): {"sha256": sha256_file(INPUT_LEDGER), "rows": len(input_rows)}}
    source_hash_manifest_sha256 = sha256_json(source_hashes)

    field_rows: list[dict[str, Any]] = []
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(input_rows, 1):
        entries = row_field_entries(row, index)
        row_entries = []
        for field_index, entry in enumerate(entries, 1):
            entry = {
                **entry,
                "generated_utc": generated_utc,
                "row_id": f"MAIN-ORCH24-RESIDUAL-R-FIELD-{len(field_rows) + field_index:05d}",
                "source_hash_manifest_sha256": source_hash_manifest_sha256,
                "source_path": str(INPUT_LEDGER),
            }
            row_entries.append(entry)
        field_rows.extend(row_entries)
        statuses = sorted({entry["resolution_status"] or "UNCLASSIFIED_REQUIRES_BUILDER_REPAIR" for entry in row_entries})
        output_rows.append(
            {
                **row,
                "schema_version": "main_orch24_action_after_residual_numeric_r_resolution_v1",
                "generated_utc": generated_utc,
                "residual_numeric_r_field_resolution_status": (
                    "NO_RESIDUAL_NUMERIC_RLIKE_FIELDS"
                    if not row_entries
                    else (
                        "ALL_RESIDUAL_NUMERIC_RLIKE_FIELDS_CLASSIFIED_REFERENCE_OR_NON_RESULT"
                        if all(entry["resolution_status"] for entry in row_entries)
                        else "UNCLASSIFIED_RESIDUAL_NUMERIC_RLIKE_FIELD_REPAIR_REQUIRED"
                    )
                ),
                "residual_numeric_r_field_count": len(row_entries),
                "residual_numeric_r_field_resolution_statuses": statuses,
                "residual_numeric_r_field_resolution_row_ids": [entry["row_id"] for entry in row_entries],
                "residual_numeric_r_counted_proxy_added": 0,
                "residual_numeric_r_counted_proxy_added_reason": (
                    "No additional proxy owner was lawful after exact/source-no-scalar materialization; "
                    "remaining R-like fields are duplicate references, owner-merged references, intervals, "
                    "distance features, or previous-state provenance."
                ),
                "residual_numeric_r_resolution_scope": MATERIALIZATION_RESULT_SCOPE,
                "residual_numeric_r_source_hash_manifest_sha256": source_hash_manifest_sha256,
            }
        )

    status_counts = Counter(row.get("resolution_status") or "UNCLASSIFIED_REQUIRES_BUILDER_REPAIR" for row in field_rows)
    field_counts = Counter(row["field_name"] for row in field_rows)
    proxy_rows = [row for row in output_rows if numeric(row.get("materialized_proxy_r")) is not None]
    exact_reference_rows = [row for row in output_rows if numeric(row.get("exact_r_reference")) is not None]
    unclassified_rows = [row for row in field_rows if not row.get("resolution_status")]
    summary = {
        "schema_version": "main_orch24_residual_numeric_r_field_resolution_summary_v1",
        "generated_utc": generated_utc,
        "input_rows": len(input_rows),
        "output_rows": len(output_rows),
        "residual_numeric_field_rows": len(field_rows),
        "rows_with_residual_numeric_fields": len({row["source_action_row_id"] for row in field_rows}),
        "unclassified_residual_numeric_field_rows": len(unclassified_rows),
        "resolution_status_counts": dict(sorted(status_counts.items())),
        "field_counts": dict(sorted(field_counts.items())),
        "exact_r_reference_rows": len(exact_reference_rows),
        "exact_r_reference_sum": round(sum(float(row["exact_r_reference"]) for row in exact_reference_rows), 10),
        "proxy_r_rows": len(proxy_rows),
        "proxy_r_sum": round(sum(float(row["materialized_proxy_r"]) for row in proxy_rows), 10),
        "residual_numeric_r_counted_proxy_added_rows": 0,
        "residual_numeric_r_counted_proxy_added_sum": 0.0,
        "source_hash_manifest_sha256": source_hash_manifest_sha256,
        "materialization_result_scope": MATERIALIZATION_RESULT_SCOPE,
    }
    manifest = {
        "schema_version": "main_orch24_residual_numeric_r_field_resolution_manifest_v1",
        "generated_utc": generated_utc,
        "source_hashes": source_hashes,
        "source_hash_manifest_sha256": source_hash_manifest_sha256,
        "outputs": {
            str(OUTPUT_LEDGER): {"sha256": None, "rows": len(output_rows)},
            str(FIELD_LEDGER): {"sha256": None, "rows": len(field_rows)},
            str(SUMMARY_PATH): {"sha256": None},
        },
    }
    return output_rows, field_rows, summary, manifest


def main() -> None:
    output_rows, field_rows, summary, manifest = build()
    write_jsonl(OUTPUT_LEDGER, output_rows)
    write_jsonl(FIELD_LEDGER, field_rows)
    write_json(SUMMARY_PATH, summary)
    manifest["outputs"][str(OUTPUT_LEDGER)]["sha256"] = sha256_file(OUTPUT_LEDGER)
    manifest["outputs"][str(FIELD_LEDGER)]["sha256"] = sha256_file(FIELD_LEDGER)
    manifest["outputs"][str(SUMMARY_PATH)]["sha256"] = sha256_file(SUMMARY_PATH)
    write_json(MANIFEST_PATH, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
