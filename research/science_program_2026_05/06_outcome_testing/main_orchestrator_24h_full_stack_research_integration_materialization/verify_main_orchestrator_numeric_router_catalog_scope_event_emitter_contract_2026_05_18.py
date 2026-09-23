from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_LEDGER_{DATE}.jsonl"
SOURCE_CAPTURE_PLAN_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SOURCE_CAPTURE_PLAN_LEDGER_{DATE}.jsonl"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT_VERIFY_RESULT_{DATE}.json"


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
    for path in (CONTRACT_LEDGER, SOURCE_CAPTURE_PLAN_LEDGER, LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("rows") != len(rows):
        issues.append("emitter_rows_mismatch")
    if len(rows) != 7:
        issues.append(f"emitter_rows_unexpected:{len(rows)}")
    if summary.get("source_count") != 7:
        issues.append(f"source_count_unexpected:{summary.get('source_count')}")
    expected_status_counts = {"READY_DEFAULT_OFF_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT": 7}
    if summary.get("event_emitter_contract_status_counts") != expected_status_counts:
        issues.append(f"status_counts_unexpected:{summary.get('event_emitter_contract_status_counts')}")
    if summary.get("source_adapter_prospectively_complete_rows") != 7:
        issues.append("source_adapter_prospective_complete_unexpected")
    if summary.get("historical_current_log_complete_after_catalog_attachment_rows") != 4:
        issues.append("historical_complete_source_rows_unexpected")
    if summary.get("producer_patched_source_rows") != 3:
        issues.append("producer_patched_source_rows_unexpected")
    if summary.get("catalog_scope_attachment_complete_rows") != 7:
        issues.append("catalog_scope_attachment_complete_rows_unexpected")
    expected_catalog_scope_counts = {
        "horizon_id": 7,
        "primitive_flag": 7,
        "proxy_r_class": 7,
        "target_stop_order_class": 7,
    }
    if summary.get("catalog_scope_attachment_field_source_rows") != expected_catalog_scope_counts:
        issues.append(f"catalog_scope_counts_unexpected:{summary.get('catalog_scope_attachment_field_source_rows')}")
    if summary.get("input_catalog_contract_rows_max") != 1072:
        issues.append(f"input_contract_rows_unexpected:{summary.get('input_catalog_contract_rows_max')}")

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
    input_plan_ledger = summary.get("input_source_capture_plan_ledger") or {}
    if input_plan_ledger.get("sha256") != sha256_path(SOURCE_CAPTURE_PLAN_LEDGER):
        issues.append("input_source_capture_plan_hash_mismatch")

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
        row_id = row.get("emitter_contract_id")
        if row.get("runtime_score_allowed") is not False:
            issues.append(f"runtime_score_allowed:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"replay_r_counted:{row_id}")
            break
        if len(row.get("catalog_scope_attachment_fields") or []) != 4:
            issues.append(f"missing_catalog_scope_fields:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "emitter_rows": len(rows),
        "source_count": summary.get("source_count"),
        "event_emitter_contract_status_counts": summary.get("event_emitter_contract_status_counts"),
        "historical_current_log_complete_after_catalog_attachment_rows": summary.get(
            "historical_current_log_complete_after_catalog_attachment_rows"
        ),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
