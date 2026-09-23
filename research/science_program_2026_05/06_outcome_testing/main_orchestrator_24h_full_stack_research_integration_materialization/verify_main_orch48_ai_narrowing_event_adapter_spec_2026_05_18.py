from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_AI_NARROWING_EVENT_ADAPTER_SPEC"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
FIELD_AVAILABILITY_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_AI_NARROWING_EVENT_FIELD_AVAILABILITY_LEDGER_{DATE}.jsonl"
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"

EXPECTED_SOURCE_COUNT = 7
EXPECTED_FIELD_COUNT = 7
EXPECTED_SPEC_ROWS = EXPECTED_SOURCE_COUNT * EXPECTED_FIELD_COUNT
EXPECTED_MANIFEST_OUTPUT_COUNT = 2
EXPECTED_EXPLICIT_CAPTURE_FIELDS = ["horizon_id", "market_timeframe", "source_component", "source_symbol"]


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
    for path in (FIELD_AVAILABILITY_LEDGER, LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != EXPECTED_SPEC_ROWS:
        issues.append(f"adapter_spec_rows_unexpected:{len(rows)}")
    if summary.get("adapter_spec_rows") != len(rows):
        issues.append(f"summary_rows_mismatch:{summary.get('adapter_spec_rows')}:{len(rows)}")
    if summary.get("source_count") != EXPECTED_SOURCE_COUNT:
        issues.append(f"source_count_unexpected:{summary.get('source_count')}")
    if summary.get("required_field_count") != EXPECTED_FIELD_COUNT:
        issues.append(f"required_field_count_unexpected:{summary.get('required_field_count')}")

    resolution_counts = summary.get("adapter_resolution_counts") or {}
    if int(resolution_counts.get("DIRECT_FIELD_PRESENT") or 0) <= 0:
        issues.append("no_direct_fields_present")
    if int(resolution_counts.get("ALIAS_AVAILABLE_NEEDS_ADAPTER_MAPPING") or 0) <= 0:
        issues.append("no_alias_mappings_available")
    if int(resolution_counts.get("MISSING_REQUIRES_EXPLICIT_UPSTREAM_CAPTURE") or 0) <= 0:
        issues.append("no_explicit_upstream_capture_fields")
    if summary.get("explicit_upstream_capture_required_fields") != EXPECTED_EXPLICIT_CAPTURE_FIELDS:
        issues.append(
            "explicit_capture_fields_unexpected:"
            f"{summary.get('explicit_upstream_capture_required_fields')}"
        )

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
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero:{summary.get(key)}")
            break

    effect = summary.get("implementation_effect") or {}
    if effect.get("default_off_ai_narrowing_adapter_spec_available") is not True:
        issues.append("effect_adapter_spec_not_available")
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

    input_ledger = summary.get("input_field_availability_ledger") or {}
    if input_ledger.get("rows") != EXPECTED_SOURCE_COUNT:
        issues.append(f"input_field_availability_rows_unexpected:{input_ledger.get('rows')}")
    if input_ledger.get("sha256") != sha256_path(FIELD_AVAILABILITY_LEDGER):
        issues.append("input_field_availability_hash_mismatch")

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
        row_id = row.get("adapter_spec_row_id")
        if not row.get("source_exists"):
            issues.append(f"source_missing:{row_id}")
            break
        if not row.get("producer_owner"):
            issues.append(f"producer_owner_missing:{row_id}")
            break
        if not row.get("alias_candidates"):
            issues.append(f"alias_candidates_missing:{row_id}")
            break
        if not row.get("adapter_resolution") or not row.get("adapter_action"):
            issues.append(f"adapter_decision_missing:{row_id}")
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

    result = {
        "route_id": ROUTE_ID,
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "adapter_spec_rows": len(rows),
        "adapter_resolution_counts": resolution_counts,
        "explicit_upstream_capture_required_fields": summary.get("explicit_upstream_capture_required_fields"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
