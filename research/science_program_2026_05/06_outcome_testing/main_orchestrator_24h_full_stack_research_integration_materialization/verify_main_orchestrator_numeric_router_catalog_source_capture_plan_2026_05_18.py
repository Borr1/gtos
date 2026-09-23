from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_LEDGER_{DATE}.jsonl"
ADAPTER_SPEC_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC_LEDGER_{DATE}.jsonl"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SOURCE_CAPTURE_PLAN_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SOURCE_CAPTURE_PLAN_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SOURCE_CAPTURE_PLAN_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SOURCE_CAPTURE_PLAN_VERIFY_RESULT_{DATE}.json"


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
    for path in (CONTRACT_LEDGER, ADAPTER_SPEC_LEDGER, LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("rows") != len(rows):
        issues.append("plan_rows_mismatch")
    if len(rows) != 49:
        issues.append(f"plan_rows_unexpected:{len(rows)}")
    if summary.get("source_count") != 7:
        issues.append(f"source_count_unexpected:{summary.get('source_count')}")
    expected_status_counts = {
        "CURRENT_SOURCE_FIELD_ALIAS_ADAPTABLE": 11,
        "CURRENT_SOURCE_FIELD_DIRECTLY_ADAPTABLE": 7,
        "NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_REQUIRED": 28,
        "PRODUCER_ROUTE_SESSION_CAPTURE_PATCHED_OR_REQUIRED": 3,
    }
    if summary.get("source_capture_plan_status_counts") != expected_status_counts:
        issues.append(f"status_counts_unexpected:{summary.get('source_capture_plan_status_counts')}")
    if summary.get("current_source_complete_event_sources") != 0:
        issues.append("unexpected_current_complete_source")
    if summary.get("current_log_complete_field_rows") != 18:
        issues.append(f"current_log_complete_field_rows_unexpected:{summary.get('current_log_complete_field_rows')}")
    if summary.get("requires_code_or_upstream_capture_rows") != 31:
        issues.append(f"requires_capture_rows_unexpected:{summary.get('requires_code_or_upstream_capture_rows')}")

    for key in (
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero")
            break

    input_contract_ledger = summary.get("input_contract_ledger") or {}
    if input_contract_ledger.get("sha256") != sha256_path(CONTRACT_LEDGER):
        issues.append("input_contract_ledger_hash_mismatch")
    input_adapter_spec_ledger = summary.get("input_adapter_spec_ledger") or {}
    if input_adapter_spec_ledger.get("sha256") != sha256_path(ADAPTER_SPEC_LEDGER):
        issues.append("input_adapter_spec_hash_mismatch")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
        if path.suffix == ".jsonl" and path.stat().st_size >= 100_000_000:
            issues.append(f"raw_jsonl_over_github_limit:{path.name}")

    for row in rows:
        row_id = row.get("source_capture_plan_row_id")
        if row.get("runtime_score_allowed") is not False:
            issues.append(f"runtime_score_allowed:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SOURCE_CAPTURE_PLAN",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "plan_rows": len(rows),
        "source_count": summary.get("source_count"),
        "source_capture_plan_status_counts": summary.get("source_capture_plan_status_counts"),
        "current_source_complete_event_sources": summary.get("current_source_complete_event_sources"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
