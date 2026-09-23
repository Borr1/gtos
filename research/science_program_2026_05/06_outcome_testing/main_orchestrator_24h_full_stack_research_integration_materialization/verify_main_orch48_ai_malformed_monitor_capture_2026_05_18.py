from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_MALFORMED_MONITOR_CAPTURE"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.api_refusal_monitor import malformed_response_category  # noqa: E402
from src.research_infra.ai_decision_architecture_audit import parse_jsonl  # noqa: E402


LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
MALFORMED_LOG = REPO / "shadow_logs/malformed_responses.jsonl"

EXPECTED_ROWS = 5
EXPECTED_MALFORMED_ROWS = 39
EXPECTED_FLAT_REFUSAL_ROWS = 36
EXPECTED_PARSER_SCOPE_ROWS = 2
EXPECTED_CONTEXT_PRESENT_ROWS = 0
EXPECTED_CONTEXT_MISSING_ROWS = 39
EXPECTED_TEST_COVERAGE_ROWS = 5
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
    if summary.get("malformed_response_rows") != EXPECTED_MALFORMED_ROWS:
        issues.append(f"malformed_response_rows_unexpected:{summary.get('malformed_response_rows')}")
    if summary.get("flat_refusal_or_short_non_json_rows") != EXPECTED_FLAT_REFUSAL_ROWS:
        issues.append(f"flat_refusal_rows_unexpected:{summary.get('flat_refusal_or_short_non_json_rows')}")
    if summary.get("json_fence_or_trailing_text_parse_failure_rows") != EXPECTED_PARSER_SCOPE_ROWS:
        issues.append(
            "json_fence_or_trailing_text_parse_failure_rows_unexpected:"
            f"{summary.get('json_fence_or_trailing_text_parse_failure_rows')}"
        )
    if summary.get("malformed_response_rows_with_symbol_and_candle_time") != EXPECTED_CONTEXT_PRESENT_ROWS:
        issues.append(
            "context_present_rows_unexpected:"
            f"{summary.get('malformed_response_rows_with_symbol_and_candle_time')}"
        )
    if summary.get("malformed_response_rows_missing_symbol_or_candle_time") != EXPECTED_CONTEXT_MISSING_ROWS:
        issues.append(
            "context_missing_rows_unexpected:"
            f"{summary.get('malformed_response_rows_missing_symbol_or_candle_time')}"
        )
    if summary.get("monitor_taxonomy_hardened_rows") != 1:
        issues.append(f"monitor_taxonomy_hardened_rows_unexpected:{summary.get('monitor_taxonomy_hardened_rows')}")
    if summary.get("future_malformed_context_capture_wired_rows") != 1:
        issues.append(
            "future_malformed_context_capture_wired_rows_unexpected:"
            f"{summary.get('future_malformed_context_capture_wired_rows')}"
        )
    if summary.get("retry_transport_failure_raw2_guard_present_rows") != 1:
        issues.append(
            "retry_transport_failure_raw2_guard_present_rows_unexpected:"
            f"{summary.get('retry_transport_failure_raw2_guard_present_rows')}"
        )
    if summary.get("expected_test_names_covered_rows") != EXPECTED_TEST_COVERAGE_ROWS:
        issues.append(f"expected_test_names_covered_rows_unexpected:{summary.get('expected_test_names_covered_rows')}")

    expected_surfaces = {
        "ai_parser_hardening_inheritance",
        "api_refusal_monitor_taxonomy",
        "focused_malformed_monitor_capture_test_coverage",
        "malformed_response_log_context_gap",
        "primary_analyzer_malformed_context_capture",
    }
    if set(summary.get("audit_surface_counts") or {}) != expected_surfaces:
        issues.append(f"audit_surface_counts_unexpected:{summary.get('audit_surface_counts')}")

    for key in ("paid_api_or_vendor_call_rows", "broker_operation_rows", "runtime_candidate_use_permitted_rows"):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")

    effect = summary.get("implementation_effect") or {}
    for key in (
        "api_refusal_monitor_taxonomy_hardened",
        "future_malformed_response_context_capture_wired",
        "retry_transport_failure_raw2_guard_present",
    ):
        if effect.get(key) is not True:
            issues.append(f"effect_{key}_not_true:{effect.get(key)}")
    for key in ("paid_api_or_vendor_call", "broker_operation", "runtime_trading_or_live_broker_effect", "runtime_candidate_use_permitted"):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

    for row in rows:
        boundary = row.get("research_boundary") or {}
        row_id = row.get("ai_malformed_monitor_capture_row_id")
        for key in ("paid_api_or_vendor_call", "broker_operation", "runtime_trading_or_live_broker_effect", "runtime_candidate_use_permitted"):
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

    malformed_rows = parse_jsonl(MALFORMED_LOG.read_text(encoding="utf-8")) if MALFORMED_LOG.exists() else []
    category_counts: dict[str, int] = {}
    for row in malformed_rows:
        category = malformed_response_category(row)
        category_counts[category] = category_counts.get(category, 0) + 1
    if category_counts != summary.get("malformed_response_category_counts"):
        issues.append(f"category_counts_mismatch:{category_counts}:{summary.get('malformed_response_category_counts')}")

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rows": len(rows),
        "malformed_response_rows": summary.get("malformed_response_rows"),
        "flat_refusal_or_short_non_json_rows": summary.get("flat_refusal_or_short_non_json_rows"),
        "malformed_response_rows_missing_symbol_or_candle_time": summary.get(
            "malformed_response_rows_missing_symbol_or_candle_time"
        ),
        "monitor_taxonomy_hardened_rows": summary.get("monitor_taxonomy_hardened_rows"),
        "future_malformed_context_capture_wired_rows": summary.get("future_malformed_context_capture_wired_rows"),
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
