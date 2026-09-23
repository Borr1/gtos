from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_VERIFY_RESULT_{DATE}.json"


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

    if summary.get("priority_groups") != 231:
        issues.append("priority_groups_unexpected")
    if summary.get("emitter_contract_rows") != len(rows):
        issues.append("emitter_contract_rows_mismatch")
    if len(rows) != 231:
        issues.append(f"emitter_contract_row_count_unexpected:{len(rows)}")
    if summary.get("candidate_rows") != 1748:
        issues.append("candidate_rows_unexpected")
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

    status_counts = summary.get("emitter_contract_status_counts") or {}
    if status_counts.get("READY_DEFAULT_OFF_REDUCED_SURFACE_EVENT_EMITTER_CONTRACT") != 231:
        issues.append("emitter_contract_status_not_all_ready")
    class_counts = summary.get("source_capture_priority_class_counts") or {}
    if class_counts.get("LEAKAGE_REDUCED_SOURCE_IDENTITY_AND_NUMERIC_CAPTURE") != 217:
        issues.append("leakage_reduced_emitter_class_count_unexpected")
    if class_counts.get("PRESERVED_BASE_SCOPE_CAPTURE") != 14:
        issues.append("preserved_emitter_class_count_unexpected")

    required_event_counts = summary.get("required_event_field_counts") or {}
    for field in ("horizon_id", "market_timeframe", "route_session", "selected_side", "source_component", "source_symbol", "symbol"):
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

    priority_ledger = Path(summary.get("priority_ledger") or "")
    if priority_ledger.exists():
        if summary.get("priority_ledger_sha256") != sha256_path(priority_ledger):
            issues.append("priority_ledger_hash_mismatch")
    else:
        issues.append("priority_ledger_missing")

    previous_rank = 0
    for row in rows:
        row_id = row.get("emitter_contract_row_id")
        rank = int(row.get("source_capture_priority_rank") or 0)
        if rank != previous_rank + 1:
            issues.append(f"source_capture_priority_rank_gap:{row_id}")
            break
        previous_rank = rank
        if row.get("emitter_contract_status") != "READY_DEFAULT_OFF_REDUCED_SURFACE_EVENT_EMITTER_CONTRACT":
            issues.append(f"emitter_contract_status_not_ready:{row_id}")
            break
        if row.get("event_emitter_surface") != "emit_reduced_surface_event_for_priority_group":
            issues.append(f"event_emitter_surface_unexpected:{row_id}")
            break
        if row.get("source_hash_alias_policy") != "DO_NOT_TREAT_GENERIC_SOURCE_HASH_AS_SOURCE_FILE_SHA256":
            issues.append(f"source_hash_alias_policy_unexpected:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_EVENT_EMITTER_CONTRACTS",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "emitter_contract_rows": len(rows),
        "candidate_rows": summary.get("candidate_rows"),
        "event_registry_match_rows": summary.get("event_registry_match_rows"),
        "expected_candidate_event_rows": summary.get("expected_candidate_event_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
