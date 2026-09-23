from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

RULE_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_RULE_LEDGER_{DATE}.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_AGGREGATE_LEDGER_{DATE}.jsonl"
SOURCE_CONTRACT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_SOURCE_CONTRACT_LEDGER_{DATE}.jsonl"
SELF_CHECK_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_SELF_CHECK_LEDGER_{DATE}.jsonl"
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
    for path in [RULE_LEDGER, AGGREGATE_LEDGER, SOURCE_CONTRACT_LEDGER, SELF_CHECK_LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    rules = read_jsonl(RULE_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    contracts = read_jsonl(SOURCE_CONTRACT_LEDGER)
    self_checks = read_jsonl(SELF_CHECK_LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    expected_counts = summary.get("cp281_result_counts") or {}
    if len(rules) != 461 or len(rules) != expected_counts.get("rule_rows"):
        issues.append(f"rule_count_mismatch:{len(rules)}:{expected_counts.get('rule_rows')}")
    if len(aggregates) != 107 or len(aggregates) != expected_counts.get("aggregate_rows"):
        issues.append(f"aggregate_count_mismatch:{len(aggregates)}:{expected_counts.get('aggregate_rows')}")
    if len(contracts) != len(rules):
        issues.append(f"contract_count_mismatch:{len(contracts)}:{len(rules)}")
    if len(self_checks) != len(rules):
        issues.append(f"self_check_count_mismatch:{len(self_checks)}:{len(rules)}")

    action_counts = summary.get("action_class_counts") or {}
    if action_counts.get("follow_rule") != 173:
        issues.append(f"follow_rule_count_mismatch:{action_counts.get('follow_rule')}")
    if action_counts.get("avoid_filter") != 288:
        issues.append(f"avoid_filter_count_mismatch:{action_counts.get('avoid_filter')}")

    if summary.get("source_capture_contract_ready_rows") != len(rules):
        issues.append("not_all_source_contracts_ready")
    if summary.get("registry_self_check_pass_rows") != len(rules):
        issues.append("not_all_registry_self_checks_pass")
    if summary.get("parked_rows") != 0:
        issues.append(f"unexpected_parked_rows:{summary.get('parked_rows')}")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")

    for row in rules:
        if row.get("runtime_candidate_use_permitted") is not False:
            issues.append(f"rule_runtime_use_not_false:{row.get('cp281_rule_row_id')}")
            break
        if row.get("candidate_use_allowed_now") is not False:
            issues.append(f"rule_candidate_use_not_false:{row.get('cp281_rule_row_id')}")
            break
        if row.get("missing_match_fields"):
            issues.append(f"rule_missing_match_fields:{row.get('cp281_rule_row_id')}")
            break
        if not row.get("source_capture_contract_ready"):
            issues.append(f"rule_contract_not_ready:{row.get('cp281_rule_row_id')}")
            break

    for row in contracts:
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"contract_default_off_controls_failed:{row.get('cp281_rule_row_id')}")
            break
        if row.get("event_required_field_count") != len(row.get("event_required_fields") or []):
            issues.append(f"contract_field_count_mismatch:{row.get('cp281_rule_row_id')}")
            break

    for row in self_checks:
        if row.get("self_check_status") != "CP281_READY_RUNTIME_REGISTRY_SELF_CHECK_PASS":
            issues.append(f"self_check_failed:{row.get('cp281_rule_row_id')}")
            break

    manifest_outputs = manifest.get("outputs") or []
    if len(manifest_outputs) != 5:
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
        "generated_from": "verify_main_orch48_cp281_ready_runtime_mapping_2026_05_18.py",
        "rule_mapping_rows": len(rules),
        "aggregate_mapping_rows": len(aggregates),
        "source_contract_rows": len(contracts),
        "self_check_rows": len(self_checks),
        "follow_rule_rows": action_counts.get("follow_rule"),
        "avoid_filter_rows": action_counts.get("avoid_filter"),
        "manifest_output_count": len(manifest_outputs),
        "issues": issues,
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
