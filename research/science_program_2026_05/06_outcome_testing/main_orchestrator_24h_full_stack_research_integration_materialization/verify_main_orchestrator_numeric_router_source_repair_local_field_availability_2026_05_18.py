from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SOURCE_REPAIR_PLAN_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN_LEDGER_{DATE}.jsonl"
SOURCE_REPAIR_PROOF_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_PROOF_LEDGER_{DATE}.jsonl"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY_MANIFEST_{DATE}.json"
VERIFY_RESULT = (
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY_VERIFY_RESULT_{DATE}.json"
)

EXPECTED_MISSING_FIELDS = {
    "broker_fill_time_utc",
    "commission",
    "deal_ticket",
    "executed_entry_price",
    "executed_exit_price",
    "executed_lot_size",
    "executed_stop_price",
    "executed_target_price",
    "order_ticket",
    "partial_exit_lifecycle",
    "slippage_price",
    "swap",
}
EXPECTED_STATUS_VALUES = {
    "CURRENT_LOCAL_FIELD_PRESENT_BUT_NOT_BOUND_TO_NUMERIC_ROUTER_ROWS",
    "NOT_PRESENT_IN_SELECTED_LOCAL_SOURCE_FILES",
}
FALSE_FLAG_KEYS = (
    "runtime_score_allowed",
    "runtime_candidate_use_permitted",
    "candidate_use_allowed_now",
    "unconditional_scalar_use_allowed",
    "replay_r_reference_counted_as_new_main_result",
)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def verify() -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    for path in (SOURCE_REPAIR_PLAN_LEDGER, SOURCE_REPAIR_PROOF_LEDGER, LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("rows") != len(rows):
        issues.append("ledger_rows_mismatch")
    if len(rows) != len(EXPECTED_MISSING_FIELDS):
        issues.append(f"missing_field_rows_unexpected:{len(rows)}")
    row_fields = {str(row.get("missing_field")) for row in rows}
    if row_fields != EXPECTED_MISSING_FIELDS:
        issues.append(f"missing_field_set_unexpected:{sorted(row_fields)}")
    if summary.get("source_repair_plan_rows") != 1119:
        issues.append(f"source_repair_plan_rows_unexpected:{summary.get('source_repair_plan_rows')}")
    if summary.get("source_repair_proof_rows") != 17753:
        issues.append(f"source_repair_proof_rows_unexpected:{summary.get('source_repair_proof_rows')}")
    if summary.get("unique_missing_field_count") != len(EXPECTED_MISSING_FIELDS):
        issues.append("unique_missing_field_count_unexpected")
    if (
        int(summary.get("local_fields_present_count") or 0)
        + int(summary.get("local_fields_absent_count") or 0)
        != len(rows)
    ):
        issues.append("present_absent_counts_do_not_cover_all_fields")
    if summary.get("all_field_key_scan_only_rows") != len(rows):
        issues.append("field_key_scan_only_rows_unexpected")
    if summary.get("row_identity_bound_to_numeric_router_source_repair_queue_rows") != 0:
        issues.append("unexpected_row_identity_binding")
    if int(summary.get("local_source_parse_errors") or 0) > 0:
        warnings.append(f"local_source_parse_errors:{summary.get('local_source_parse_errors')}")
    if int(summary.get("local_source_candidate_files") or 0) <= 0:
        issues.append("no_local_source_candidate_files_scanned")
    if int(summary.get("local_source_records_scanned_total") or 0) <= 0:
        issues.append("no_local_source_records_scanned")

    for key in (
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero")
            break

    for input_key, source_path in (
        ("input_source_repair_plan_ledger", SOURCE_REPAIR_PLAN_LEDGER),
        ("input_source_repair_proof_ledger", SOURCE_REPAIR_PROOF_LEDGER),
    ):
        input_summary = summary.get(input_key) or {}
        if input_summary.get("sha256") != sha256_path(source_path):
            issues.append(f"{input_key}_hash_mismatch")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
        if path.suffix == ".jsonl" and path.stat().st_size >= 100_000_000:
            issues.append(f"raw_jsonl_over_github_limit:{path.name}")

    for row in rows:
        row_id = row.get("field_availability_row_id")
        status = row.get("local_field_availability_status")
        if status not in EXPECTED_STATUS_VALUES:
            issues.append(f"unexpected_local_availability_status:{row_id}:{status}")
            break
        if row.get("source_repair_proof_rows_missing_field") != 17753:
            issues.append(f"unexpected_proof_rows_missing_field:{row_id}")
            break
        if row.get("source_repair_plan_rows_requiring_field") != 1119:
            issues.append(f"unexpected_plan_rows_requiring_field:{row_id}")
            break
        if row.get("source_operation") != "read_only_local_json_key_scan":
            issues.append(f"unexpected_source_operation:{row_id}")
            break
        if row.get("field_key_scan_only") is not True:
            issues.append(f"field_key_scan_only_false:{row_id}")
            break
        if row.get("row_identity_bound_to_numeric_router_source_repair_queue") is not False:
            issues.append(f"unexpected_row_identity_bound:{row_id}")
            break
        for flag_key in FALSE_FLAG_KEYS:
            if row.get(flag_key) is not False:
                issues.append(f"{flag_key}_enabled:{row_id}")
                break
        if issues:
            break

    status_counts = summary.get("local_field_availability_status_counts") or {}
    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_LOCAL_FIELD_AVAILABILITY",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "warnings": warnings,
        "field_availability_rows": len(rows),
        "local_field_availability_status_counts": status_counts,
        "local_source_candidate_files": summary.get("local_source_candidate_files"),
        "local_source_records_scanned_total": summary.get("local_source_records_scanned_total"),
        "local_source_parse_errors": summary.get("local_source_parse_errors"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
