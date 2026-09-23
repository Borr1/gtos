from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_DECISION_TRACE_INTEGRITY_GUARD"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 5
EXPECTED_TEST_COVERAGE_ROWS = 4
EXPECTED_REQUIRED_FIELD_COUNT = 16
EXPECTED_MANIFEST_OUTPUT_COUNT = 2


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


def resolve_display_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO / path


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"row_count_unexpected:{len(rows)}")
    if summary.get("rows") != len(rows):
        issues.append(f"summary_rows_mismatch:{summary.get('rows')}:{len(rows)}")
    if summary.get("schema_registered_rows") != 1:
        issues.append(f"schema_registered_rows_unexpected:{summary.get('schema_registered_rows')}")
    if summary.get("required_field_count") != EXPECTED_REQUIRED_FIELD_COUNT:
        issues.append(f"required_field_count_unexpected:{summary.get('required_field_count')}")
    if summary.get("prompt_hash_validation_present_rows") != 1:
        issues.append(
            f"prompt_hash_validation_present_rows_unexpected:{summary.get('prompt_hash_validation_present_rows')}"
        )
    if summary.get("full_text_field_guard_present_rows") != 1:
        issues.append(
            f"full_text_field_guard_present_rows_unexpected:{summary.get('full_text_field_guard_present_rows')}"
        )
    if summary.get("boundary_flag_guard_present_rows") != 1:
        issues.append(f"boundary_flag_guard_present_rows_unexpected:{summary.get('boundary_flag_guard_present_rows')}")
    if summary.get("waiting_lane_registered_rows") != 1:
        issues.append(f"waiting_lane_registered_rows_unexpected:{summary.get('waiting_lane_registered_rows')}")
    if summary.get("trace_log_exists_with_rows") != 0:
        issues.append(f"trace_log_exists_with_rows_unexpected:{summary.get('trace_log_exists_with_rows')}")
    if summary.get("runtime_halt_active_rows") != 1:
        issues.append(f"runtime_halt_active_rows_unexpected:{summary.get('runtime_halt_active_rows')}")
    if summary.get("expected_test_names_covered_rows") != EXPECTED_TEST_COVERAGE_ROWS:
        issues.append(f"expected_test_names_covered_rows_unexpected:{summary.get('expected_test_names_covered_rows')}")
    if summary.get("inherited_trace_logger_enabled_rows") != 1:
        issues.append(
            f"inherited_trace_logger_enabled_rows_unexpected:{summary.get('inherited_trace_logger_enabled_rows')}"
        )
    if summary.get("inherited_hash_only_prompt_response_provenance_rows") != 1:
        issues.append(
            "inherited_hash_only_prompt_response_provenance_rows_unexpected:"
            f"{summary.get('inherited_hash_only_prompt_response_provenance_rows')}"
        )
    if summary.get("trading_decision_behavior_changed_rows") != 0:
        issues.append(
            f"trading_decision_behavior_changed_rows_unexpected:{summary.get('trading_decision_behavior_changed_rows')}"
        )

    expected_surfaces = {
        "ai_decision_trace_hash_only_validation_guard",
        "ai_decision_trace_integrity_test_coverage",
        "ai_decision_trace_provenance_inheritance",
        "ai_decision_trace_runtime_halt_waiting_lane",
        "ai_decision_trace_schema_registration",
    }
    if set(summary.get("audit_surface_counts") or {}) != expected_surfaces:
        issues.append(f"audit_surface_counts_unexpected:{summary.get('audit_surface_counts')}")

    for key in ("paid_api_or_vendor_call_rows", "broker_operation_rows", "runtime_candidate_use_permitted_rows"):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")

    effect = summary.get("implementation_effect") or {}
    for key in (
        "ai_decision_trace_integrity_guard_registered",
        "hash_only_text_storage_guard",
        "runtime_halt_waiting_lane_documented",
    ):
        if effect.get(key) is not True:
            issues.append(f"effect_{key}_not_true:{effect.get(key)}")
    for key in ("trading_decision_behavior_changed", "paid_api_or_vendor_call", "broker_operation", "runtime_candidate_use_permitted"):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

    for row in rows:
        boundary = row.get("research_boundary") or {}
        row_id = row.get("ai_decision_trace_integrity_guard_row_id")
        for key in ("trading_decision_behavior_changed", "paid_api_or_vendor_call", "broker_operation", "runtime_candidate_use_permitted"):
            if boundary.get(key):
                issues.append(f"{key}_claimed:{row_id}")
                break

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
            break
    if len(output_by_name) != EXPECTED_MANIFEST_OUTPUT_COUNT:
        issues.append(f"manifest_output_count_unexpected:{len(output_by_name)}")

    for surface in summary.get("code_surfaces") or []:
        path = resolve_display_path(surface.get("path", ""))
        if not path.exists():
            issues.append(f"code_surface_missing:{surface.get('path')}")
            continue
        if surface.get("sha256") != sha256_path(path):
            issues.append(f"code_surface_hash_mismatch:{surface.get('path')}")
            break

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rows": len(rows),
        "schema_registered_rows": summary.get("schema_registered_rows"),
        "waiting_lane_registered_rows": summary.get("waiting_lane_registered_rows"),
        "trace_log_exists_with_rows": summary.get("trace_log_exists_with_rows"),
        "paid_api_or_vendor_call_rows": summary.get("paid_api_or_vendor_call_rows"),
        "broker_operation_rows": summary.get("broker_operation_rows"),
        "runtime_candidate_use_permitted_rows": summary.get("runtime_candidate_use_permitted_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
