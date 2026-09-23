from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SOURCE_PRIORITY_VERIFY_RESULT_{DATE}.json"


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
    for path in (SUMMARY, LEDGER, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    rows = read_jsonl(LEDGER) if LEDGER.exists() else []

    if summary.get("adjusted_rollup_rows") != 1748:
        issues.append("adjusted_rollup_rows_unexpected")
    if summary.get("contract_rows") != 1748:
        issues.append("contract_rows_unexpected")
    if summary.get("priority_groups") != len(rows):
        issues.append("priority_groups_mismatch")
    if len(rows) != 231:
        issues.append(f"priority_group_count_unexpected:{len(rows)}")
    if summary.get("candidate_rows") != 1748:
        issues.append("candidate_rows_unexpected")
    if summary.get("final_review_overlay_bound_rows") != 1748:
        issues.append("final_review_overlay_bound_rows_unexpected")
    if summary.get("implementation_ready_candidate_rows") != 1597:
        issues.append("implementation_ready_candidate_rows_unexpected")
    if summary.get("capacity_blocked_candidate_rows") != 151:
        issues.append("capacity_blocked_candidate_rows_unexpected")
    if summary.get("event_registry_match_rows") != 55646:
        issues.append("event_registry_match_rows_unexpected")
    if summary.get("expected_candidate_event_rows") != 9266:
        issues.append("expected_candidate_event_rows_unexpected")
    if summary.get("duplicate_scope_event_match_rows") != 46380:
        issues.append("duplicate_scope_event_match_rows_unexpected")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")
    if summary.get("replay_r_reference_counted_as_new_main_result_rows") != 0:
        issues.append("replay_r_counted_as_new_main_result")

    status_counts = summary.get("source_capture_priority_status_counts") or {}
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_IMPLEMENT_READY") != 199:
        issues.append("implementation_ready_priority_group_count_unexpected")
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_IMPLEMENT_READY_WITH_REDESIGN_SUBSET") != 22:
        issues.append("mixed_priority_group_count_unexpected")
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_REDESIGN_ONLY") != 10:
        issues.append("redesign_only_priority_group_count_unexpected")

    class_counts = summary.get("source_capture_priority_class_counts") or {}
    if class_counts.get("LEAKAGE_REDUCED_SOURCE_IDENTITY_AND_NUMERIC_CAPTURE") != 217:
        issues.append("leakage_reduced_capture_class_count_unexpected")
    if class_counts.get("PRESERVED_BASE_SCOPE_CAPTURE") != 14:
        issues.append("preserved_capture_class_count_unexpected")

    final_review_status_counts = summary.get("final_review_adjusted_rollup_status_counts") or {}
    if final_review_status_counts.get("DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_READY") != 1597:
        issues.append("final_review_implement_ready_row_count_unexpected")
    if final_review_status_counts.get("DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN") != 151:
        issues.append("final_review_capacity_blocked_row_count_unexpected")

    required_event_counts = summary.get("required_event_field_counts") or {}
    base_fields = ("horizon_id", "market_timeframe", "route_session", "selected_side", "source_component", "source_symbol", "symbol")
    for field in base_fields:
        if required_event_counts.get(field) != 231:
            issues.append(f"base_required_field_count_unexpected:{field}")
            break
    required_source_counts = summary.get("required_source_identity_field_counts") or {}
    if required_source_counts.get("source_path") != 217 or required_source_counts.get("source_file_sha256") != 217:
        issues.append("source_identity_required_field_counts_unexpected")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (SUMMARY, LEDGER):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    for field, issue_name in (("adjusted_rollup_ledger", "adjusted_rollup_ledger"), ("contract_ledger", "contract_ledger")):
        path = Path(summary.get(field) or "")
        if path.exists():
            if summary.get(f"{field}_sha256") != sha256_path(path):
                issues.append(f"{issue_name}_hash_mismatch")
        else:
            issues.append(f"{issue_name}_missing")

    previous_rank = 0
    for row in rows:
        rank = int(row.get("source_capture_priority_rank") or 0)
        if rank != previous_rank + 1:
            issues.append(f"source_capture_priority_rank_gap:{row.get('symbol')}:{rank}")
            break
        previous_rank = rank
        impl_rows = int(row.get("implementation_ready_candidate_rows") or 0)
        blocked_rows = int(row.get("capacity_blocked_candidate_rows") or 0)
        if impl_rows + blocked_rows != int(row.get("candidate_rows") or 0):
            issues.append(f"final_review_candidate_row_sum_mismatch:{rank}")
            break
        status = row.get("source_capture_priority_status")
        if impl_rows == 0 and blocked_rows > 0 and status != "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_REDESIGN_ONLY":
            issues.append(f"redesign_only_status_unexpected:{rank}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{rank}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{rank}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_SOURCE_CAPTURE_PRIORITIES",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "priority_groups": len(rows),
        "candidate_rows": summary.get("candidate_rows"),
        "implementation_ready_candidate_rows": summary.get("implementation_ready_candidate_rows"),
        "capacity_blocked_candidate_rows": summary.get("capacity_blocked_candidate_rows"),
        "status_counts": status_counts,
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
