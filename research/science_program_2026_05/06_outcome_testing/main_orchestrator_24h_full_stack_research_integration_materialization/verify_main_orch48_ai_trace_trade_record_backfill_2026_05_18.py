from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"

EXPECTED_TEST_COVERAGE_ROWS = 3
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

    if summary.get("rows") != len(rows):
        issues.append(f"summary_rows_mismatch:{summary.get('rows')}:{len(rows)}")
    if not rows:
        issues.append("no_backfill_rows")
    if summary.get("complete_rows") != len(rows):
        issues.append(f"complete_rows_unexpected:{summary.get('complete_rows')}:{len(rows)}")
    if summary.get("incomplete_rows") != 0:
        issues.append(f"incomplete_rows_unexpected:{summary.get('incomplete_rows')}")
    if summary.get("stores_full_prompt_or_response_text_rows") != 0:
        issues.append(
            f"stores_full_prompt_or_response_text_rows_unexpected:{summary.get('stores_full_prompt_or_response_text_rows')}"
        )
    if summary.get("runtime_trace_stream_write_rows") != 0:
        issues.append(f"runtime_trace_stream_write_rows_unexpected:{summary.get('runtime_trace_stream_write_rows')}")
    if summary.get("paid_api_or_vendor_call_rows") != 0:
        issues.append(f"paid_api_or_vendor_call_rows_unexpected:{summary.get('paid_api_or_vendor_call_rows')}")
    if summary.get("broker_operation_rows") != 0:
        issues.append(f"broker_operation_rows_unexpected:{summary.get('broker_operation_rows')}")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append(
            f"runtime_candidate_use_permitted_rows_unexpected:{summary.get('runtime_candidate_use_permitted_rows')}"
        )
    if summary.get("expected_test_names_covered_rows") != EXPECTED_TEST_COVERAGE_ROWS:
        issues.append(f"expected_test_names_covered_rows_unexpected:{summary.get('expected_test_names_covered_rows')}")
    if summary.get("inherited_trace_logger_enabled") is not True:
        issues.append(f"inherited_trace_logger_enabled_unexpected:{summary.get('inherited_trace_logger_enabled')}")
    if summary.get("inherited_hash_only_prompt_response_provenance") is not True:
        issues.append(
            "inherited_hash_only_prompt_response_provenance_unexpected:"
            f"{summary.get('inherited_hash_only_prompt_response_provenance')}"
        )

    effect = summary.get("implementation_effect") or {}
    for key in ("trade_record_ai_trace_backfill_materialized", "hash_only_prompt_response_provenance"):
        if effect.get(key) is not True:
            issues.append(f"effect_{key}_not_true:{effect.get(key)}")
    for key in ("runtime_trace_stream_write", "trading_decision_behavior_changed", "paid_api_or_vendor_call", "broker_operation", "runtime_candidate_use_permitted"):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

    seen_keys: set[str] = set()
    for row in rows:
        row_key = row.get("row_key")
        if not row_key:
            issues.append("row_key_missing")
            break
        if row_key in seen_keys:
            issues.append(f"duplicate_row_key:{row_key}")
            break
        seen_keys.add(row_key)
        for forbidden_field in ("system_prompt", "user_message", "raw_response", "prompt_text", "response_text"):
            if forbidden_field in row:
                issues.append(f"full_text_field_present:{forbidden_field}:{row_key}")
                break
        encoded = json.dumps(row, sort_keys=True)
        for forbidden_text in ("secret system prompt", "secret user message"):
            if forbidden_text in encoded:
                issues.append(f"full_text_leak:{forbidden_text}:{row_key}")
                break
        boundary = row.get("research_boundary") or {}
        for key in ("runtime_trace_stream_write", "paid_api_or_vendor_call", "broker_operation", "runtime_candidate_use_permitted"):
            if boundary.get(key):
                issues.append(f"{key}_claimed:{row_key}")
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
        "complete_rows": summary.get("complete_rows"),
        "unique_prompt_bundle_hashes": summary.get("unique_prompt_bundle_hashes"),
        "stores_full_prompt_or_response_text_rows": summary.get("stores_full_prompt_or_response_text_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
