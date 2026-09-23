from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_POLICY"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"

EXPECTED_ROWS = 231
EXPECTED_READY_ROWS = 221
EXPECTED_BLOCKLIST_ROWS = 22
EXPECTED_REDESIGN_ONLY_ROWS = 10
EXPECTED_MANIFEST_OUTPUT_COUNT = 2
EXPECTED_POLICY_STATUS_COUNTS = {
    "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY": 199,
    "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY_WITH_CAPACITY_BLOCKLIST": 22,
    "AI_NARROWING_POLICY_KEEP_AI_UNCHANGED_MECHANICAL_SCOPE_REDESIGN_ONLY": 10,
}


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
    if summary.get("ai_narrowing_review_ready_rows") != EXPECTED_READY_ROWS:
        issues.append(f"ai_narrowing_review_ready_rows_unexpected:{summary.get('ai_narrowing_review_ready_rows')}")
    if summary.get("capacity_blocklist_required_before_ai_narrowing_rows") != EXPECTED_BLOCKLIST_ROWS:
        issues.append(
            "capacity_blocklist_required_before_ai_narrowing_rows_unexpected:"
            f"{summary.get('capacity_blocklist_required_before_ai_narrowing_rows')}"
        )
    if summary.get("ai_narrowing_policy_status_counts") != EXPECTED_POLICY_STATUS_COUNTS:
        issues.append(f"policy_status_counts_unexpected:{summary.get('ai_narrowing_policy_status_counts')}")

    keep_ai_count = (summary.get("ai_narrowing_policy_status_counts") or {}).get(
        "AI_NARROWING_POLICY_KEEP_AI_UNCHANGED_MECHANICAL_SCOPE_REDESIGN_ONLY"
    )
    if keep_ai_count != EXPECTED_REDESIGN_ONLY_ROWS:
        issues.append(f"keep_ai_redesign_only_rows_unexpected:{keep_ai_count}")

    for key in (
        "production_change_opened_now_rows",
        "live_ai_runtime_change_now_rows",
        "live_selector_change_now_rows",
        "paid_api_or_vendor_call_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")

    effect = summary.get("implementation_effect") or {}
    if effect.get("ai_narrowing_policy_default_off_available") is not True:
        issues.append("effect_ai_narrowing_policy_not_available")
    if effect.get("default_off_mechanical_selector_scope_rows_for_review") != EXPECTED_READY_ROWS:
        issues.append(
            "effect_default_off_mechanical_selector_scope_rows_unexpected:"
            f"{effect.get('default_off_mechanical_selector_scope_rows_for_review')}"
        )
    if effect.get("current_ai_runtime_behavior") != "UNCHANGED_DEFAULT_AI_DECISION_GATE":
        issues.append(f"effect_current_ai_runtime_behavior_unexpected:{effect.get('current_ai_runtime_behavior')}")
    for key in (
        "production_change_opened_now",
        "live_ai_runtime_change_now",
        "live_selector_change_now",
        "runtime_trading_or_live_broker_effect",
        "runtime_candidate_use_permitted",
        "broker_operation",
        "paid_api_or_vendor_call",
    ):
        if effect.get(key) is not False:
            issues.append(f"effect_{key}_unexpected:{effect.get(key)}")

    for row in rows:
        row_id = row.get("ai_narrowing_policy_row_id")
        if not row.get("runtime_enablement_prerequisites"):
            issues.append(f"missing_runtime_enablement_prerequisites:{row_id}")
            break
        if row.get("current_ai_runtime_behavior") != "UNCHANGED_DEFAULT_AI_DECISION_GATE":
            issues.append(f"row_current_ai_runtime_behavior_changed:{row_id}")
            break
        for key in (
            "production_change_opened_now",
            "live_ai_runtime_change_now",
            "live_selector_change_now",
            "paid_api_or_vendor_call",
            "runtime_candidate_use_permitted",
            "candidate_use_allowed_now",
        ):
            if row.get(key):
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
        "policy_rows": len(rows),
        "ai_narrowing_review_ready_rows": summary.get("ai_narrowing_review_ready_rows"),
        "capacity_blocklist_required_before_ai_narrowing_rows": summary.get(
            "capacity_blocklist_required_before_ai_narrowing_rows"
        ),
        "policy_status_counts": summary.get("ai_narrowing_policy_status_counts"),
        "production_change_opened_now_rows": summary.get("production_change_opened_now_rows"),
        "live_ai_runtime_change_now_rows": summary.get("live_ai_runtime_change_now_rows"),
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
