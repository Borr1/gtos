from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_SL_BEYOND_OB_OUTCOME_JOIN"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"
EXPECTED_ROWS = 323
EXPECTED_JOINED_ROWS = 230
EXPECTED_MISSING_ROWS = 93
EXPECTED_REJECT_ROWS = 19
EXPECTED_JOINED_REJECT_ROWS = 0
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
    join_summary = summary.get("join_summary") or {}
    effect = summary.get("implementation_effect") or {}

    if len(rows) != EXPECTED_ROWS:
        issues.append(f"rows_unexpected:{len(rows)}")
    if summary.get("status") != "OK_SL_BEYOND_OB_OUTCOME_JOIN_MATERIALIZED":
        issues.append(f"summary_status_unexpected:{summary.get('status')}")
    if summary.get("runtime_halt_active") is not True:
        issues.append(f"runtime_halt_active_not_true:{summary.get('runtime_halt_active')}")
    if (summary.get("sl_beyond_ob_log") or {}).get("rows") != EXPECTED_ROWS:
        issues.append(f"sl_beyond_rows_unexpected:{(summary.get('sl_beyond_ob_log') or {}).get('rows')}")
    if join_summary.get("rows") != EXPECTED_ROWS:
        issues.append(f"join_summary_rows_unexpected:{join_summary.get('rows')}")
    if join_summary.get("joined_rows") != EXPECTED_JOINED_ROWS:
        issues.append(f"joined_rows_unexpected:{join_summary.get('joined_rows')}")
    if join_summary.get("missing_outcome_rows") != EXPECTED_MISSING_ROWS:
        issues.append(f"missing_outcome_rows_unexpected:{join_summary.get('missing_outcome_rows')}")
    l2_counts = join_summary.get("l2_decision_counts") or {}
    if l2_counts.get("REJECT") != EXPECTED_REJECT_ROWS:
        issues.append(f"reject_rows_unexpected:{l2_counts}")
    if join_summary.get("joined_reject_rows") != EXPECTED_JOINED_REJECT_ROWS:
        issues.append(f"joined_reject_rows_unexpected:{join_summary.get('joined_reject_rows')}")
    if join_summary.get("missing_reject_rows") != EXPECTED_REJECT_ROWS:
        issues.append(f"missing_reject_rows_unexpected:{join_summary.get('missing_reject_rows')}")
    if join_summary.get("joined_reject_positive_fillable_proxy_rows") != 0:
        issues.append(
            "joined_reject_positive_fillable_proxy_rows_nonzero:"
            f"{join_summary.get('joined_reject_positive_fillable_proxy_rows')}"
        )
    expected_action = "KEEP_SL_BEYOND_OB_GATE_AND_CAPTURE_REJECT_OUTCOMES_BEFORE_THRESHOLD_REVIEW"
    if summary.get("gate_action") != expected_action:
        issues.append(f"gate_action_unexpected:{summary.get('gate_action')}")

    for key in (
        "runtime_decision_effect_rows",
        "production_change_opened_now_rows",
        "gate_config_change_now_rows",
        "broker_operation_rows",
        "paid_api_or_vendor_call_rows",
        "runtime_candidate_use_permitted_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if join_summary.get(key) != 0:
            issues.append(f"join_summary_{key}_nonzero:{join_summary.get(key)}")
    for key in (
        "gate_config_change_now",
        "runtime_decision_effect",
        "production_change_opened_now",
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
        row_id = row.get("sl_beyond_ob_outcome_join_row_id")
        for key in (
            "runtime_decision_effect",
            "production_change_opened_now",
            "gate_config_change_now",
            "broker_operation",
            "paid_api_or_vendor_call",
            "runtime_candidate_use_permitted",
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
        "rows": len(rows),
        "joined_rows": join_summary.get("joined_rows"),
        "joined_reject_rows": join_summary.get("joined_reject_rows"),
        "missing_reject_rows": join_summary.get("missing_reject_rows"),
        "gate_action": summary.get("gate_action"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
