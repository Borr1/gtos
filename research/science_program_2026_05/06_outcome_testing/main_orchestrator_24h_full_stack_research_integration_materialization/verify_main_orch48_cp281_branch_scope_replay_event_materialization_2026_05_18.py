from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CP281_BRANCH_SCOPE_REPLAY_EVENT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

EVENT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_EVENT_LEDGER_{DATE}.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_MATCH_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    for path in [EVENT_LEDGER, MATCH_LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    events = read_jsonl(EVENT_LEDGER)
    matches = read_jsonl(MATCH_LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    if len(events) != 107:
        issues.append(f"event_count_mismatch:{len(events)}")
    if len(matches) != 117:
        issues.append(f"match_count_mismatch:{len(matches)}")
    if summary.get("branch_scope_replay_event_rows") != 107:
        issues.append(f"summary_event_rows_mismatch:{summary.get('branch_scope_replay_event_rows')}")
    if summary.get("branch_scope_replay_match_rows") != 117:
        issues.append(f"summary_match_rows_mismatch:{summary.get('branch_scope_replay_match_rows')}")
    if summary.get("matched_event_rows") != 107:
        issues.append(f"matched_event_rows_mismatch:{summary.get('matched_event_rows')}")
    if summary.get("unmatched_event_rows") != 0:
        issues.append(f"unmatched_event_rows_nonzero:{summary.get('unmatched_event_rows')}")
    if summary.get("own_branch_match_rows") != 107:
        issues.append(f"own_branch_match_rows_mismatch:{summary.get('own_branch_match_rows')}")
    if summary.get("duplicate_portable_scope_count") != 5:
        issues.append(f"duplicate_portable_scope_count_mismatch:{summary.get('duplicate_portable_scope_count')}")
    if summary.get("duplicate_scope_event_rows") != 10:
        issues.append(f"duplicate_scope_event_rows_mismatch:{summary.get('duplicate_scope_event_rows')}")
    if summary.get("duplicate_scope_match_rows") != 20:
        issues.append(f"duplicate_scope_match_rows_mismatch:{summary.get('duplicate_scope_match_rows')}")
    if summary.get("action_conflict_match_rows") != 10:
        issues.append(f"action_conflict_match_rows_mismatch:{summary.get('action_conflict_match_rows')}")
    if summary.get("event_action_class_counts") != {"avoid_filter": 65, "follow_rule": 42}:
        issues.append(f"event_action_counts_unexpected:{summary.get('event_action_class_counts')}")
    if summary.get("matched_action_class_counts") != {"avoid_filter": 70, "follow_rule": 47}:
        issues.append(f"matched_action_counts_unexpected:{summary.get('matched_action_class_counts')}")
    if summary.get("live_shadow_matching_role") != "SECONDARY_EVENT_FIELD_INTEGRATION_EVIDENCE_ONLY_NOT_STRATEGY_EVIDENCE":
        issues.append("live_shadow_matching_role_missing_or_wrong")
    if summary.get("source_evidence_role") != "CP281_NATIVE_REPLAY_EVENT_MATERIALIZATION_FROM_CP280_CP281_HISTORICAL_READY_SLICE":
        issues.append("source_evidence_role_missing_or_wrong")
    if summary.get("can_continue_to_historical_replay_execution") is not True:
        issues.append("can_continue_to_historical_replay_execution_not_true")

    for row in events:
        row_id = row.get("cp281_branch_scope_replay_event_id")
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"event_default_off_controls_failed:{row_id}")
            break
        if row.get("production_change_approved") is not False:
            issues.append(f"event_production_change_not_false:{row_id}")
            break
    for row in matches:
        row_key = row.get("row_key")
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"match_default_off_controls_failed:{row_key}")
            break
        if row.get("production_change_approved") is not False:
            issues.append(f"match_production_change_not_false:{row_key}")
            break

    manifest_outputs = manifest.get("outputs") or []
    if len(manifest_outputs) != 3:
        issues.append(f"manifest_output_count_mismatch:{len(manifest_outputs)}")
    for item in manifest_outputs:
        output_path = REPO / item["path"]
        if not output_path.exists():
            issues.append(f"manifest_missing_path:{item['path']}")
            continue
        if sha256_path(output_path) != item.get("sha256"):
            issues.append(f"manifest_sha_mismatch:{item['path']}")
        if count_lines(output_path) != item.get("lines"):
            issues.append(f"manifest_line_mismatch:{item['path']}")

    effect = summary.get("implementation_effect") or {}
    for field in [
        "broker_operation",
        "paid_api_or_vendor_call",
        "runtime_candidate_use_permitted",
        "candidate_use_allowed_now",
        "production_import_path",
        "mutates_order_risk_prompt_safety_or_mt5",
    ]:
        if effect.get(field) is not False:
            issues.append(f"implementation_effect_not_false:{field}")

    result = {
        "ok": not issues,
        "route_id": ROUTE_ID,
        "generated_from": "verify_main_orch48_cp281_branch_scope_replay_event_materialization_2026_05_18.py",
        "branch_scope_replay_event_rows": len(events),
        "branch_scope_replay_match_rows": len(matches),
        "duplicate_scope_event_rows": summary.get("duplicate_scope_event_rows"),
        "action_conflict_match_rows": summary.get("action_conflict_match_rows"),
        "manifest_output_count": len(manifest_outputs),
        "issues": issues,
        "can_continue_to_historical_replay_execution": not issues,
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
