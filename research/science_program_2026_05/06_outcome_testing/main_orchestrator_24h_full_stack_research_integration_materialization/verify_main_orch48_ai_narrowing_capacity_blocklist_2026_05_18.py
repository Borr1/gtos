from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_CAPACITY_BLOCKLIST"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
EXPECTED_ROWS = 32
EXPECTED_CANDIDATE_IDS = 151
EXPECTED_PRE_AI_SCOPE_ROWS = 22
EXPECTED_PRE_AI_CANDIDATE_IDS = 71
EXPECTED_REDESIGN_ONLY_SCOPE_ROWS = 10
EXPECTED_REDESIGN_ONLY_CANDIDATE_IDS = 80
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
    blocklist_summary = summary.get("blocklist_summary") or {}
    registry_summary = summary.get("blocklist_registry_summary") or {}
    effect = summary.get("implementation_effect") or {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"blocklist_rows_unexpected:{len(rows)}")
    if summary.get("status") != "OK_DEFAULT_OFF_AI_NARROWING_CAPACITY_BLOCKLIST_MATERIALIZED":
        issues.append(f"summary_status_unexpected:{summary.get('status')}")
    if summary.get("runtime_halt_active") is not True:
        issues.append(f"runtime_halt_active_not_true:{summary.get('runtime_halt_active')}")
    if blocklist_summary.get("rows") != EXPECTED_ROWS:
        issues.append(f"summary_rows_unexpected:{blocklist_summary.get('rows')}")
    if blocklist_summary.get("unique_capacity_blocked_candidate_ids") != EXPECTED_CANDIDATE_IDS:
        issues.append(
            "unique_capacity_blocked_candidate_ids_unexpected:"
            f"{blocklist_summary.get('unique_capacity_blocked_candidate_ids')}"
        )
    if blocklist_summary.get("pre_ai_selector_blocklist_scope_rows") != EXPECTED_PRE_AI_SCOPE_ROWS:
        issues.append(
            "pre_ai_selector_blocklist_scope_rows_unexpected:"
            f"{blocklist_summary.get('pre_ai_selector_blocklist_scope_rows')}"
        )
    if blocklist_summary.get("unique_pre_ai_selector_blocked_candidate_ids") != EXPECTED_PRE_AI_CANDIDATE_IDS:
        issues.append(
            "unique_pre_ai_selector_blocked_candidate_ids_unexpected:"
            f"{blocklist_summary.get('unique_pre_ai_selector_blocked_candidate_ids')}"
        )
    if blocklist_summary.get("redesign_only_blocklist_scope_rows") != EXPECTED_REDESIGN_ONLY_SCOPE_ROWS:
        issues.append(
            "redesign_only_blocklist_scope_rows_unexpected:"
            f"{blocklist_summary.get('redesign_only_blocklist_scope_rows')}"
        )
    if blocklist_summary.get("unique_redesign_only_blocked_candidate_ids") != EXPECTED_REDESIGN_ONLY_CANDIDATE_IDS:
        issues.append(
            "unique_redesign_only_blocked_candidate_ids_unexpected:"
            f"{blocklist_summary.get('unique_redesign_only_blocked_candidate_ids')}"
        )
    if registry_summary.get("unique_candidate_ids") != EXPECTED_CANDIDATE_IDS:
        issues.append(f"registry_unique_candidate_ids_unexpected:{registry_summary.get('unique_candidate_ids')}")
    if summary.get("self_check_candidate_rows") != EXPECTED_CANDIDATE_IDS:
        issues.append(f"self_check_candidate_rows_unexpected:{summary.get('self_check_candidate_rows')}")

    expected_status_counts = {
        "AI_NARROWING_CAPACITY_BLOCKLIST_REQUIRED_FOR_PRE_AI_SELECTOR_REVIEW": EXPECTED_PRE_AI_SCOPE_ROWS,
        "AI_NARROWING_CAPACITY_BLOCKLIST_PRESERVED_REDESIGN_ONLY_KEEP_AI_UNCHANGED": (
            EXPECTED_REDESIGN_ONLY_SCOPE_ROWS
        ),
    }
    if blocklist_summary.get("ai_narrowing_capacity_blocklist_status_counts") != expected_status_counts:
        issues.append(
            "blocklist_status_counts_unexpected:"
            f"{blocklist_summary.get('ai_narrowing_capacity_blocklist_status_counts')}"
        )
    expected_eval_counts = {
        "AI_NARROWING_CAPACITY_BLOCKLIST_MATCH_BLOCK_PRE_AI_SELECTOR": EXPECTED_PRE_AI_CANDIDATE_IDS,
        "AI_NARROWING_CAPACITY_BLOCKLIST_MATCH_REDESIGN_ONLY_KEEP_AI_UNCHANGED": (
            EXPECTED_REDESIGN_ONLY_CANDIDATE_IDS
        ),
    }
    if summary.get("self_check_eval_status_counts") != expected_eval_counts:
        issues.append(f"self_check_eval_status_counts_unexpected:{summary.get('self_check_eval_status_counts')}")

    for key in (
        "capacity_blocklist_active_now_rows",
        "ai_call_skip_allowed_now_rows",
        "production_change_opened_now_rows",
        "live_ai_runtime_change_now_rows",
        "live_selector_change_now_rows",
        "paid_api_or_vendor_call_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if blocklist_summary.get(key) != 0:
            issues.append(f"blocklist_summary_{key}_nonzero:{blocklist_summary.get(key)}")
    for key in (
        "capacity_blocklist_active_now",
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

    seen_candidate_ids: set[str] = set()
    for row in rows:
        row_id = row.get("ai_narrowing_capacity_blocklist_row_id")
        for candidate_id in row.get("capacity_blocked_candidate_row_ids") or []:
            if candidate_id in seen_candidate_ids:
                issues.append(f"duplicate_capacity_candidate_id:{candidate_id}")
                break
            seen_candidate_ids.add(candidate_id)
        for key in (
            "capacity_blocklist_active_now",
            "ai_call_skip_allowed_now",
            "production_change_opened_now",
            "live_ai_runtime_change_now",
            "live_selector_change_now",
            "runtime_candidate_use_permitted",
            "candidate_use_allowed_now",
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
        "blocklist_rows": len(rows),
        "unique_capacity_blocked_candidate_ids": len(seen_candidate_ids),
        "pre_ai_selector_blocklist_scope_rows": blocklist_summary.get("pre_ai_selector_blocklist_scope_rows"),
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
