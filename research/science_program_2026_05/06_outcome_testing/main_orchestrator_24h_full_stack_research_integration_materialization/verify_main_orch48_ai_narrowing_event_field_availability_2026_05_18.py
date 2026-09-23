from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_EVENT_FIELD_AVAILABILITY"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
EXPECTED_SOURCE_COUNT = 7
EXPECTED_POLICY_ROWS = 231
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

    if len(rows) != EXPECTED_SOURCE_COUNT:
        issues.append(f"ledger_row_count_unexpected:{len(rows)}")
    if summary.get("event_source_count") != len(rows):
        issues.append(f"event_source_count_mismatch:{summary.get('event_source_count')}:{len(rows)}")
    policy_input = summary.get("input_ai_narrowing_policy_ledger") or {}
    if policy_input.get("rows") != EXPECTED_POLICY_ROWS:
        issues.append(f"policy_rows_unexpected:{policy_input.get('rows')}")
    if int(summary.get("event_source_rows_total") or 0) <= 0:
        issues.append("event_source_rows_total_zero")
    if summary.get("parse_error_rows_total") != 0:
        issues.append(f"parse_error_rows_total_nonzero:{summary.get('parse_error_rows_total')}")
    if summary.get("rows_with_ai_narrowing_required_fields_total") != 0:
        issues.append(
            "current_sources_unexpectedly_feed_ai_narrowing_contract:"
            f"{summary.get('rows_with_ai_narrowing_required_fields_total')}"
        )
    if summary.get("complete_events_matched_policy_rows_total") != 0:
        issues.append(
            "current_sources_unexpectedly_match_ai_narrowing_policy:"
            f"{summary.get('complete_events_matched_policy_rows_total')}"
        )
    if summary.get("complete_events_review_ready_rows_total") != 0:
        issues.append(
            "current_sources_unexpectedly_review_ready:"
            f"{summary.get('complete_events_review_ready_rows_total')}"
        )
    if summary.get("field_availability_status_counts") != {
        "CURRENT_SOURCE_MISSING_AI_NARROWING_BASE_SCOPE_FIELDS": EXPECTED_SOURCE_COUNT
    }:
        issues.append(f"field_availability_status_counts_unexpected:{summary.get('field_availability_status_counts')}")

    effect = summary.get("implementation_effect") or {}
    if effect.get("default_off_ai_narrowing_event_adapter_available") is not True:
        issues.append("effect_event_adapter_not_available")
    if effect.get("current_ai_runtime_behavior") != "UNCHANGED_DEFAULT_AI_DECISION_GATE":
        issues.append(f"effect_current_ai_runtime_behavior_unexpected:{effect.get('current_ai_runtime_behavior')}")
    for key in (
        "ai_call_skip_allowed_now",
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
        row_id = row.get("field_availability_row_id")
        if row.get("event_source_exists") is not True:
            issues.append(f"event_source_missing:{row.get('event_source_path')}")
            break
        if int(row.get("parse_error_rows") or 0) != 0:
            issues.append(f"parse_errors:{row.get('event_source_path')}")
            break
        if int(row.get("rows_with_ai_narrowing_required_fields") or 0) != 0:
            issues.append(f"source_contract_complete_rows_nonzero:{row_id}")
            break
        if int(row.get("complete_events_matched_policy_rows") or 0) != 0:
            issues.append(f"source_policy_match_rows_nonzero:{row_id}")
            break
        for key in (
            "ai_call_skip_allowed_now",
            "production_change_opened_now",
            "live_ai_runtime_change_now",
            "live_selector_change_now",
            "paid_api_or_vendor_call",
            "runtime_candidate_use_permitted",
            "candidate_use_allowed_now",
            "replay_r_reference_counted_as_new_main_result",
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

    policy_path = resolve_display_path(policy_input.get("path", ""))
    if not policy_path.exists():
        issues.append(f"policy_ledger_missing:{policy_input.get('path')}")
    elif policy_input.get("sha256") != sha256_path(policy_path):
        issues.append("policy_ledger_hash_mismatch")

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
        "ledger_rows": len(rows),
        "event_source_rows_total": summary.get("event_source_rows_total"),
        "rows_with_ai_narrowing_required_fields_total": summary.get(
            "rows_with_ai_narrowing_required_fields_total"
        ),
        "complete_events_matched_policy_rows_total": summary.get("complete_events_matched_policy_rows_total"),
        "complete_events_review_ready_rows_total": summary.get("complete_events_review_ready_rows_total"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
