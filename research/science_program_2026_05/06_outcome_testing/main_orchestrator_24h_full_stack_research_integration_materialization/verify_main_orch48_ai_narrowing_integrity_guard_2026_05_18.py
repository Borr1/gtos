from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_INTEGRITY_GUARD"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
EXPECTED_ROWS = 4
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


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"route_rows_unexpected:{len(rows)}")
    if summary.get("route_rows") != len(rows):
        issues.append(f"summary_rows_mismatch:{summary.get('route_rows')}:{len(rows)}")
    if summary.get("jsonl_spec_registered") is not True:
        issues.append(f"jsonl_spec_not_registered:{summary.get('jsonl_spec_registered')}")
    if summary.get("synthetic_health_status") != "OK_WITH_DEFAULT_OFF_AI_NARROWING_SHADOW_EVALUATIONS":
        issues.append(f"synthetic_health_status_unexpected:{summary.get('synthetic_health_status')}")
    if summary.get("synthetic_health_issues") != []:
        issues.append(f"synthetic_health_issues:{summary.get('synthetic_health_issues')}")
    if summary.get("forbidden_runtime_flag_detected") is not True:
        issues.append("forbidden_runtime_flag_not_detected")
    if summary.get("runtime_halt_active") is not True:
        issues.append(f"runtime_halt_active_not_true:{summary.get('runtime_halt_active')}")

    effect = summary.get("implementation_effect") or {}
    for key in (
        "ai_call_skip_allowed_now",
        "production_change_opened_now",
        "live_ai_runtime_change_now",
        "live_selector_change_now",
        "runtime_candidate_use_permitted",
        "broker_operation",
        "paid_api_or_vendor_call",
    ):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

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

    for row in rows:
        row_id = row.get("route_row_id")
        for key in ("broker_operation", "paid_api_or_vendor_call", "runtime_candidate_use_permitted"):
            if row.get(key):
                issues.append(f"{key}_claimed:{row_id}")
                break

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "route_rows": len(rows),
        "synthetic_health_status": summary.get("synthetic_health_status"),
        "forbidden_runtime_flag_detected": summary.get("forbidden_runtime_flag_detected"),
        "runtime_halt_active": summary.get("runtime_halt_active"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
