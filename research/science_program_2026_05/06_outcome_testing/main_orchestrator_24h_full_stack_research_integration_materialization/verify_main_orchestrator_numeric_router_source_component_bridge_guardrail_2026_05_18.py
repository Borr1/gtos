from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
BRIDGE_AUDIT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_AUDIT_LEDGER_{DATE}.jsonl"
BRIDGE_AUDIT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_AUDIT_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_GUARDRAIL_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_GUARDRAIL_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_GUARDRAIL_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_GUARDRAIL_VERIFY_RESULT_{DATE}.json"


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
    for path in (BRIDGE_AUDIT_LEDGER, BRIDGE_AUDIT_SUMMARY, LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("rows") != len(rows):
        issues.append("guardrail_rows_mismatch")
    if len(rows) != 35:
        issues.append(f"guardrail_rows_unexpected:{len(rows)}")
    if summary.get("current_source_component_value_rows") != 24:
        issues.append("current_component_value_rows_unexpected")
    if summary.get("catalog_source_component_value_rows") != 11:
        issues.append("catalog_component_value_rows_unexpected")
    if summary.get("accepted_mapping_rows") != 0:
        issues.append("unexpected_accepted_component_mappings")
    expected_status_counts = {
        "CATALOG_COMPONENT_UNMAPPED_BY_CURRENT_SOURCE_VALUES": 11,
        "EXPLICIT_MAPPING_REQUIRED_NOT_ASSUMED": 24,
    }
    if summary.get("guardrail_status_counts") != expected_status_counts:
        issues.append(f"guardrail_status_counts_unexpected:{summary.get('guardrail_status_counts')}")

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

    input_bridge_audit_ledger = summary.get("input_bridge_audit_ledger") or {}
    if input_bridge_audit_ledger.get("sha256") != sha256_path(BRIDGE_AUDIT_LEDGER):
        issues.append("input_bridge_audit_ledger_hash_mismatch")
    input_bridge_audit_summary = summary.get("input_bridge_audit_summary") or {}
    if input_bridge_audit_summary.get("sha256") != sha256_path(BRIDGE_AUDIT_SUMMARY):
        issues.append("input_bridge_audit_summary_hash_mismatch")

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
        row_id = row.get("guardrail_row_id")
        if row.get("accepted_mapping_target"):
            issues.append(f"unexpected_mapping_target:{row_id}")
            break
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
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_COMPONENT_BRIDGE_GUARDRAIL",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "guardrail_rows": len(rows),
        "accepted_mapping_rows": summary.get("accepted_mapping_rows"),
        "guardrail_status_counts": summary.get("guardrail_status_counts"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
