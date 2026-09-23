from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_RUNTIME_CONFIG_GUARD"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
EXPECTED_ROWS = 231
EXPECTED_REVIEW_READY_ROWS = 221
EXPECTED_CAPACITY_BLOCKLIST_ROWS = 22
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
    decision_summary = summary.get("decision_summary") or {}
    eval_summary = summary.get("registry_eval_summary") or {}
    config = (summary.get("config_source") or {}).get("ai_narrowing") or {}
    effect = summary.get("implementation_effect") or {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"decision_rows_unexpected:{len(rows)}")
    if summary.get("status") != "OK_DEFAULT_OFF_AI_NARROWING_RUNTIME_CONFIG_GUARD_DOCUMENTED":
        issues.append(f"summary_status_unexpected:{summary.get('status')}")
    if (summary.get("policy_ledger") or {}).get("rows") != EXPECTED_ROWS:
        issues.append(f"policy_rows_unexpected:{(summary.get('policy_ledger') or {}).get('rows')}")
    if summary.get("runtime_halt_active") is not True:
        issues.append(f"runtime_halt_active_not_true:{summary.get('runtime_halt_active')}")
    if config.get("enabled") is not False:
        issues.append(f"config_enabled_not_false:{config.get('enabled')}")
    if config.get("mode") != "shadow":
        issues.append(f"config_mode_unexpected:{config.get('mode')}")
    if config.get("allow_ai_call_skip") is not False:
        issues.append(f"config_allow_ai_call_skip_not_false:{config.get('allow_ai_call_skip')}")

    if decision_summary.get("ai_narrowing_review_ready_rows") != EXPECTED_REVIEW_READY_ROWS:
        issues.append(f"review_ready_rows_unexpected:{decision_summary.get('ai_narrowing_review_ready_rows')}")
    if (
        decision_summary.get("capacity_blocklist_required_before_ai_narrowing_rows")
        != EXPECTED_CAPACITY_BLOCKLIST_ROWS
    ):
        issues.append(
            "capacity_blocklist_rows_unexpected:"
            f"{decision_summary.get('capacity_blocklist_required_before_ai_narrowing_rows')}"
        )
    if decision_summary.get("matched_policy_rows") != EXPECTED_ROWS:
        issues.append(f"matched_policy_rows_unexpected:{decision_summary.get('matched_policy_rows')}")
    if decision_summary.get("runtime_guard_config_enabled_rows") != 0:
        issues.append(f"runtime_guard_config_enabled_rows_nonzero:{decision_summary.get('runtime_guard_config_enabled_rows')}")
    if decision_summary.get("runtime_guard_allow_ai_call_skip_config_rows") != 0:
        issues.append(
            "runtime_guard_allow_ai_call_skip_config_rows_nonzero:"
            f"{decision_summary.get('runtime_guard_allow_ai_call_skip_config_rows')}"
        )
    if decision_summary.get("runtime_halt_active_rows") != EXPECTED_ROWS:
        issues.append(f"runtime_halt_active_rows_unexpected:{decision_summary.get('runtime_halt_active_rows')}")
    if decision_summary.get("runtime_eligible_after_all_gates_rows") != 0:
        issues.append(
            "runtime_eligible_after_all_gates_rows_nonzero:"
            f"{decision_summary.get('runtime_eligible_after_all_gates_rows')}"
        )

    status_counts = decision_summary.get("ai_narrowing_runtime_guard_decision_status_counts") or {}
    if status_counts != {"AI_NARROWING_RUNTIME_KEEP_AI_CONFIG_DISABLED": EXPECTED_ROWS}:
        issues.append(f"decision_status_counts_unexpected:{status_counts}")
    failure_counts = decision_summary.get("runtime_enablement_gate_failure_counts") or {}
    for key in (
        "CONFIG_DISABLED",
        "CONFIG_MODE_NOT_ACTIVE",
        "AI_CALL_SKIP_FLAG_DISABLED",
        "PRODUCTION_CHANGE_REVIEW_NOT_APPROVED",
        "OWNER_APPROVAL_NOT_CONFIRMED",
        "RUNTIME_HALT_ACTIVE",
        "RUNTIME_HALT_REMOVAL_NOT_CONFIRMED",
        "SELECTOR_CANARY_TESTS_NOT_PASSED",
    ):
        if failure_counts.get(key) != EXPECTED_ROWS:
            issues.append(f"failure_count_unexpected:{key}:{failure_counts.get(key)}")

    eval_status_counts = eval_summary.get("ai_narrowing_registry_eval_status_counts") or {}
    if eval_status_counts.get("AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_READY") != 199:
        issues.append(f"eval_ready_count_unexpected:{eval_status_counts}")
    if eval_status_counts.get("AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_WITH_CAPACITY_BLOCKLIST") != 22:
        issues.append(f"eval_capacity_count_unexpected:{eval_status_counts}")
    if eval_status_counts.get("AI_NARROWING_REGISTRY_MATCH_KEEP_AI_UNCHANGED") != 10:
        issues.append(f"eval_keep_ai_count_unexpected:{eval_status_counts}")

    for key in (
        "ai_call_skip_allowed_now",
        "production_change_opened_now",
        "live_ai_runtime_change_now",
        "live_selector_change_now",
        "runtime_candidate_use_permitted",
        "candidate_use_allowed_now",
        "broker_operation",
        "paid_api_or_vendor_call",
    ):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")
    for key in (
        "ai_call_skip_allowed_now_rows",
        "production_change_opened_now_rows",
        "live_ai_runtime_change_now_rows",
        "live_selector_change_now_rows",
        "paid_api_or_vendor_call_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if decision_summary.get(key) != 0:
            issues.append(f"decision_summary_{key}_nonzero:{decision_summary.get(key)}")

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
        row_id = row.get("ai_narrowing_runtime_guard_decision_row_id")
        for key in (
            "ai_call_skip_allowed_now",
            "production_change_opened_now",
            "live_ai_runtime_change_now",
            "live_selector_change_now",
            "runtime_candidate_use_permitted",
            "candidate_use_allowed_now",
            "broker_operation",
            "paid_api_or_vendor_call",
        ):
            if row.get(key):
                issues.append(f"{key}_claimed:{row_id}")
                break

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "decision_rows": len(rows),
        "decision_status_counts": status_counts,
        "runtime_halt_active": summary.get("runtime_halt_active"),
        "ai_call_skip_allowed_now_rows": decision_summary.get("ai_call_skip_allowed_now_rows"),
        "runtime_eligible_after_all_gates_rows": decision_summary.get("runtime_eligible_after_all_gates_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
