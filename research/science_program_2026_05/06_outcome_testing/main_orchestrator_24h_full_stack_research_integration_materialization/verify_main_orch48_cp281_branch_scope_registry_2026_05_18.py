from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_CP281_BRANCH_SCOPE_REGISTRY"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

CONTRACT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_CONTRACT_LEDGER_{DATE}.jsonl"
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
    for path in [CONTRACT_LEDGER, SELF_CHECK_LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    if issues:
        result = {"ok": False, "route_id": ROUTE_ID, "issues": issues}
        write_json(VERIFY_RESULT, result)
        return result

    contracts = read_jsonl(CONTRACT_LEDGER)
    self_checks = read_jsonl(SELF_CHECK_LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    if len(contracts) != 107:
        issues.append(f"contract_count_mismatch:{len(contracts)}")
    if len(self_checks) != 107:
        issues.append(f"self_check_count_mismatch:{len(self_checks)}")
    if summary.get("branch_decision_rows") != 107:
        issues.append(f"branch_decision_rows_mismatch:{summary.get('branch_decision_rows')}")
    if summary.get("portable_scope_count") != 102:
        issues.append(f"portable_scope_count_mismatch:{summary.get('portable_scope_count')}")
    if summary.get("duplicate_portable_scope_count") != 5:
        issues.append(f"duplicate_scope_count_mismatch:{summary.get('duplicate_portable_scope_count')}")
    if summary.get("branch_scope_self_check_pass_rows") != 107:
        issues.append(f"self_check_pass_mismatch:{summary.get('branch_scope_self_check_pass_rows')}")
    if summary.get("source_hash_required_for_portable_branch_scope") is not False:
        issues.append("portable_branch_scope_unexpectedly_requires_source_hash")
    if len(summary.get("event_required_fields") or []) != 5:
        issues.append(f"event_required_field_count_mismatch:{len(summary.get('event_required_fields') or [])}")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")

    for row in contracts:
        if row.get("event_required_field_count") != 5:
            issues.append(f"contract_field_count_mismatch:{row.get('cp281_aggregate_row_id')}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"contract_default_off_failed:{row.get('cp281_aggregate_row_id')}")
            break
    for row in self_checks:
        if row.get("self_check_status") != "CP281_BRANCH_SCOPE_REGISTRY_SELF_CHECK_PASS":
            issues.append(f"self_check_failed:{row.get('cp281_aggregate_row_id')}")
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
        "generated_from": "verify_main_orch48_cp281_branch_scope_registry_2026_05_18.py",
        "branch_decision_rows": summary.get("branch_decision_rows"),
        "portable_scope_count": summary.get("portable_scope_count"),
        "duplicate_portable_scope_count": summary.get("duplicate_portable_scope_count"),
        "branch_scope_self_check_pass_rows": summary.get("branch_scope_self_check_pass_rows"),
        "manifest_output_count": len(manifest_outputs),
        "issues": issues,
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    write_json(VERIFY_RESULT, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
