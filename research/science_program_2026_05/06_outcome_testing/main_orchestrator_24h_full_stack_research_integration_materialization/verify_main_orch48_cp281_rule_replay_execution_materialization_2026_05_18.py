from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CP281_RULE_REPLAY_EXECUTION_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

EVENT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_EVENT_LEDGER_{DATE}.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_MATCH_LEDGER_{DATE}.jsonl"
RESULT_TABLE_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_RESULT_TABLE_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"{ROUTE_ID}_VERIFY_RESULT_{DATE}.json"

LIVE_SHADOW_SECONDARY_ROLE = "SECONDARY_EVENT_FIELD_INTEGRATION_EVIDENCE_ONLY_NOT_STRATEGY_EVIDENCE"
RULE_REPLAY_SOURCE_EVIDENCE_ROLE = "CP281_NATIVE_RULE_REPLAY_EVENT_FROM_HISTORICAL_READY_SLICE"
EXPECTED_GROUP_COUNTS = {
    "action_class": 2,
    "branch": 5,
    "follow_vs_avoid_scope": 153,
    "horizon": 3,
    "main_system_surface": 2,
    "market": 10,
    "overall": 1,
    "rule": 461,
    "session": 5,
    "side": 2,
    "symbol_family": 7,
    "symbol_family_market_timeframe": 10,
    "symbol_family_market_timeframe_session_horizon_side": 153,
    "symbol_family_session": 23,
    "timeframe": 4,
}


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
    for path in [EVENT_LEDGER, MATCH_LEDGER, RESULT_TABLE_LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    events = read_jsonl(EVENT_LEDGER)
    matches = read_jsonl(MATCH_LEDGER)
    result_tables = read_jsonl(RESULT_TABLE_LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    if len(events) != 461:
        issues.append(f"event_count_mismatch:{len(events)}")
    if len(matches) != 1343:
        issues.append(f"match_count_mismatch:{len(matches)}")
    if len(result_tables) != 841:
        issues.append(f"result_table_count_mismatch:{len(result_tables)}")
    if summary.get("rule_replay_event_rows") != 461:
        issues.append(f"summary_event_rows_mismatch:{summary.get('rule_replay_event_rows')}")
    if summary.get("rule_replay_match_rows") != 1343:
        issues.append(f"summary_match_rows_mismatch:{summary.get('rule_replay_match_rows')}")
    if summary.get("rule_replay_result_table_rows") != 841:
        issues.append(f"summary_result_table_rows_mismatch:{summary.get('rule_replay_result_table_rows')}")
    if summary.get("matched_event_rows") != 461:
        issues.append(f"matched_event_rows_mismatch:{summary.get('matched_event_rows')}")
    if summary.get("unmatched_event_rows") != 0:
        issues.append(f"unmatched_event_rows_nonzero:{summary.get('unmatched_event_rows')}")
    if summary.get("own_rule_match_rows") != 461:
        issues.append(f"own_rule_match_rows_mismatch:{summary.get('own_rule_match_rows')}")
    if summary.get("duplicate_rule_event_rows") != 441:
        issues.append(f"duplicate_rule_event_rows_mismatch:{summary.get('duplicate_rule_event_rows')}")
    if summary.get("duplicate_rule_match_rows") != 1323:
        issues.append(f"duplicate_rule_match_rows_mismatch:{summary.get('duplicate_rule_match_rows')}")
    if summary.get("action_conflict_match_rows") != 0:
        issues.append(f"action_conflict_match_rows_nonzero:{summary.get('action_conflict_match_rows')}")
    if summary.get("event_action_class_counts") != {"avoid_filter": 288, "follow_rule": 173}:
        issues.append(f"event_action_counts_unexpected:{summary.get('event_action_class_counts')}")
    if summary.get("matched_action_class_counts") != {"avoid_filter": 864, "follow_rule": 479}:
        issues.append(f"matched_action_counts_unexpected:{summary.get('matched_action_class_counts')}")
    if summary.get("result_table_group_counts") != EXPECTED_GROUP_COUNTS:
        issues.append(f"result_table_group_counts_unexpected:{summary.get('result_table_group_counts')}")
    if summary.get("live_shadow_matching_role") != LIVE_SHADOW_SECONDARY_ROLE:
        issues.append("live_shadow_matching_role_missing_or_wrong")
    if summary.get("source_evidence_role") != RULE_REPLAY_SOURCE_EVIDENCE_ROLE:
        issues.append("source_evidence_role_missing_or_wrong")
    if summary.get("primary_evidence_path") != "CP280_CP281_HISTORICAL_REPLAY_EXECUTION_NOT_LIVE_SHADOW_NO_MATCH":
        issues.append("primary_evidence_path_missing_or_wrong")
    if summary.get("live_shadow_no_match_terminal_product_allowed") is not False:
        issues.append("live_shadow_no_match_terminal_product_allowed_not_false")
    if summary.get("cp281_rejection_from_live_shadow_no_match_allowed") is not False:
        issues.append("cp281_rejection_from_live_shadow_no_match_allowed_not_false")

    for row in events:
        row_id = row.get("cp281_rule_replay_event_id")
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"event_default_off_controls_failed:{row_id}")
            break
        if row.get("production_change_approved") is not False:
            issues.append(f"event_production_change_not_false:{row_id}")
            break
        if row.get("source_evidence_role") != RULE_REPLAY_SOURCE_EVIDENCE_ROLE:
            issues.append(f"event_source_evidence_role_wrong:{row_id}")
            break
        if row.get("live_shadow_matching_role") != LIVE_SHADOW_SECONDARY_ROLE:
            issues.append(f"event_live_shadow_role_wrong:{row_id}")
            break

    for row in matches:
        row_key = row.get("row_key")
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"match_default_off_controls_failed:{row_key}")
            break
        if row.get("production_change_approved") is not False:
            issues.append(f"match_production_change_not_false:{row_key}")
            break
        if row.get("source_evidence_role") != RULE_REPLAY_SOURCE_EVIDENCE_ROLE:
            issues.append(f"match_source_evidence_role_wrong:{row_key}")
            break
        if row.get("live_shadow_matching_role") != LIVE_SHADOW_SECONDARY_ROLE:
            issues.append(f"match_live_shadow_role_wrong:{row_key}")
            break

    for row in result_tables:
        row_key = row.get("row_key")
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"result_table_default_off_controls_failed:{row_key}")
            break
        if row.get("production_change_approved") is not False:
            issues.append(f"result_table_production_change_not_false:{row_key}")
            break
        if row.get("source_evidence_role") != RULE_REPLAY_SOURCE_EVIDENCE_ROLE:
            issues.append(f"result_table_source_evidence_role_wrong:{row_key}")
            break
        if row.get("live_shadow_matching_role") != LIVE_SHADOW_SECONDARY_ROLE:
            issues.append(f"result_table_live_shadow_role_wrong:{row_key}")
            break

    manifest_outputs = manifest.get("outputs") or []
    if len(manifest_outputs) != 4:
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
        "generated_from": "verify_main_orch48_cp281_rule_replay_execution_materialization_2026_05_18.py",
        "rule_replay_event_rows": len(events),
        "rule_replay_match_rows": len(matches),
        "rule_replay_result_table_rows": len(result_tables),
        "matched_event_rows": summary.get("matched_event_rows"),
        "unmatched_event_rows": summary.get("unmatched_event_rows"),
        "duplicate_rule_event_rows": summary.get("duplicate_rule_event_rows"),
        "duplicate_rule_match_rows": summary.get("duplicate_rule_match_rows"),
        "manifest_output_count": len(manifest_outputs),
        "issues": issues,
        "can_continue_to_historical_replay_execution": not issues,
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
