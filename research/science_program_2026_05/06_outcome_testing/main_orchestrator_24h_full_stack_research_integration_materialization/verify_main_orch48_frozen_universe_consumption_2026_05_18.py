from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_FROZEN_UNIVERSE_CONSUMPTION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

ARTIFACT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_ARTIFACT_LEDGER_{DATE}.jsonl"
ORDER_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_ORDER_LEDGER_{DATE}.jsonl"
COUNT_CHECK_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_COUNT_CHECK_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"

EXPECTED_ARTIFACT_ROWS = 27
EXPECTED_CP280_ARTIFACT_ROWS = 16
EXPECTED_CP281_ARTIFACT_ROWS = 11
EXPECTED_ORDER_ROWS = 5
EXPECTED_COUNT_CHECK_ROWS = 12
EXPECTED_TEST_ROWS = 3
EXPECTED_MANIFEST_OUTPUTS = 4


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
    for path in (ARTIFACT_LEDGER, ORDER_LEDGER, COUNT_CHECK_LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    artifact_rows = read_jsonl(ARTIFACT_LEDGER) if ARTIFACT_LEDGER.exists() else []
    order_rows = read_jsonl(ORDER_LEDGER) if ORDER_LEDGER.exists() else []
    count_rows = read_jsonl(COUNT_CHECK_LEDGER) if COUNT_CHECK_LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(artifact_rows) != EXPECTED_ARTIFACT_ROWS:
        issues.append(f"artifact_rows_unexpected:{len(artifact_rows)}")
    if len(order_rows) != EXPECTED_ORDER_ROWS:
        issues.append(f"order_rows_unexpected:{len(order_rows)}")
    if len(count_rows) != EXPECTED_COUNT_CHECK_ROWS:
        issues.append(f"count_check_rows_unexpected:{len(count_rows)}")
    if summary.get("artifact_rows") != len(artifact_rows):
        issues.append(f"summary_artifact_rows_mismatch:{summary.get('artifact_rows')}:{len(artifact_rows)}")
    if summary.get("consumption_order_rows") != len(order_rows):
        issues.append(f"summary_order_rows_mismatch:{summary.get('consumption_order_rows')}:{len(order_rows)}")
    if summary.get("count_check_rows") != len(count_rows):
        issues.append(f"summary_count_rows_mismatch:{summary.get('count_check_rows')}:{len(count_rows)}")
    if summary.get("cp280_artifact_rows") != EXPECTED_CP280_ARTIFACT_ROWS:
        issues.append(f"cp280_artifact_rows_unexpected:{summary.get('cp280_artifact_rows')}")
    if summary.get("cp281_artifact_rows") != EXPECTED_CP281_ARTIFACT_ROWS:
        issues.append(f"cp281_artifact_rows_unexpected:{summary.get('cp281_artifact_rows')}")
    if summary.get("count_check_pass_rows") != EXPECTED_COUNT_CHECK_ROWS:
        issues.append(f"count_check_pass_rows_unexpected:{summary.get('count_check_pass_rows')}")
    if summary.get("expected_test_names_covered_rows") != EXPECTED_TEST_ROWS:
        issues.append(f"expected_test_names_covered_rows_unexpected:{summary.get('expected_test_names_covered_rows')}")

    for key in ("cp280_result_ok", "cp281_result_ok", "cp282_result_ok", "cp282_verifier_ok", "moonshot_status_clean"):
        if summary.get(key) is not True:
            issues.append(f"{key}_unexpected:{summary.get(key)}")

    key_counts = summary.get("key_counts") or {}
    expected_key_counts = {
        "cp281_ready_runtime_rule_rows": 461,
        "cp281_follow_rule_inputs": 173,
        "cp281_avoid_filter_inputs": 288,
        "cp281_self_test_pass_rows": 461,
        "cp280_implementation_ready_rows": 461,
        "cp280_repair_needed_rows": 243649,
        "cp280_kill_preserve_rows": 25811,
        "cp280_coverage_rows": 28474,
        "cp282_repair_needed_rows_preserved": 243649,
        "cp282_kill_preserve_rows_preserved": 25811,
        "cp282_coverage_rows_preserved": 28474,
    }
    for key, expected in expected_key_counts.items():
        if key_counts.get(key) != expected:
            issues.append(f"key_count_{key}_unexpected:{key_counts.get(key)}")

    effect = summary.get("implementation_effect") or {}
    if effect.get("main_side_cp280_cp281_cp282_consumption_index_materialized") is not True:
        issues.append("consumption_index_not_materialized")
    for key in (
        "runtime_trading_or_live_broker_effect",
        "broker_operation",
        "paid_api_or_vendor_call",
        "runtime_candidate_use_permitted",
        "production_import_path",
        "mutates_order_risk_prompt_safety_or_mt5",
    ):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

    seen_keys: set[str] = set()
    for row in [*artifact_rows, *order_rows, *count_rows]:
        row_key = row.get("row_key")
        if not row_key:
            issues.append("row_key_missing")
            break
        if row_key in seen_keys:
            issues.append(f"duplicate_row_key:{row_key}")
            break
        seen_keys.add(row_key)
        boundary = row.get("research_boundary") or {}
        for key in ("runtime_candidate_use_permitted", "broker_operation", "paid_api_or_vendor_call"):
            if boundary.get(key):
                issues.append(f"boundary_{key}_true:{row_key}")
                break

    order_priorities = [row.get("priority_order") for row in order_rows]
    if order_priorities != [1, 2, 3, 4, 5]:
        issues.append(f"order_priorities_unexpected:{order_priorities}")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (ARTIFACT_LEDGER, ORDER_LEDGER, COUNT_CHECK_LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
            break
    if len(output_by_name) != EXPECTED_MANIFEST_OUTPUTS:
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
        "artifact_rows": len(artifact_rows),
        "consumption_order_rows": len(order_rows),
        "count_check_rows": len(count_rows),
        "cp281_ready_runtime_rule_rows": key_counts.get("cp281_ready_runtime_rule_rows"),
        "cp280_repair_needed_rows": key_counts.get("cp280_repair_needed_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_cp281_row_mapping": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
