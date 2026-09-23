from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CP281_BRANCH_DECISIONS"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
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
    for path in [LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    rows = read_jsonl(LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    if len(rows) != 107:
        issues.append(f"branch_decision_row_count_mismatch:{len(rows)}")
    if summary.get("branch_decision_rows") != len(rows):
        issues.append(f"summary_branch_decision_count_mismatch:{summary.get('branch_decision_rows')}:{len(rows)}")
    if summary.get("ready_branch_decision_rows") != 107:
        issues.append(f"ready_branch_count_mismatch:{summary.get('ready_branch_decision_rows')}")
    if summary.get("repair_required_branch_decision_rows") != 0:
        issues.append(f"repair_required_rows_nonzero:{summary.get('repair_required_branch_decision_rows')}")
    if summary.get("ready_follow_scope_rows") != 42:
        issues.append(f"ready_follow_scope_mismatch:{summary.get('ready_follow_scope_rows')}")
    if summary.get("ready_avoid_scope_rows") != 65:
        issues.append(f"ready_avoid_scope_mismatch:{summary.get('ready_avoid_scope_rows')}")
    if summary.get("all_member_rows_preserved_rows") != 107:
        issues.append(f"member_preservation_mismatch:{summary.get('all_member_rows_preserved_rows')}")
    if summary.get("source_capture_contract_ready_rows") != 107:
        issues.append(f"contract_ready_scope_mismatch:{summary.get('source_capture_contract_ready_rows')}")
    if summary.get("self_test_pass_rows") != 107:
        issues.append(f"self_test_scope_mismatch:{summary.get('self_test_pass_rows')}")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")

    member_count_sum = sum(int(row.get("member_rule_count") or 0) for row in rows)
    if member_count_sum != 461:
        issues.append(f"member_rule_count_sum_mismatch:{member_count_sum}")

    for row in rows:
        if row.get("branch_decision_status") != "READY_DEFAULT_OFF_CP281_BRANCH_DECISION":
            issues.append(f"branch_decision_not_ready:{row.get('cp281_aggregate_row_id')}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"default_off_controls_failed:{row.get('cp281_aggregate_row_id')}")
            break
        if row.get("production_change_approved") is not False:
            issues.append(f"production_change_not_false:{row.get('cp281_aggregate_row_id')}")
            break
        if row.get("member_rule_count") != row.get("aggregate_rule_count"):
            issues.append(f"member_count_not_preserved:{row.get('cp281_aggregate_row_id')}")
            break

    manifest_outputs = manifest.get("outputs") or []
    if len(manifest_outputs) != 2:
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
        "generated_from": "verify_main_orch48_cp281_branch_decisions_2026_05_18.py",
        "branch_decision_rows": len(rows),
        "ready_branch_decision_rows": summary.get("ready_branch_decision_rows"),
        "ready_follow_scope_rows": summary.get("ready_follow_scope_rows"),
        "ready_avoid_scope_rows": summary.get("ready_avoid_scope_rows"),
        "member_rule_count_sum": member_count_sum,
        "manifest_output_count": len(manifest_outputs),
        "issues": issues,
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
