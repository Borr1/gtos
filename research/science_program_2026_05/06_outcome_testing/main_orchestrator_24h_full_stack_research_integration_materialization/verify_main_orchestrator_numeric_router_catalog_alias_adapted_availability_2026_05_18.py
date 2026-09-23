from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_LEDGER_{DATE}.jsonl"
ADAPTER_SPEC_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_ADAPTER_SPEC_LEDGER_{DATE}.jsonl"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_ALIAS_ADAPTED_AVAILABILITY_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_ALIAS_ADAPTED_AVAILABILITY_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_ALIAS_ADAPTED_AVAILABILITY_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_ALIAS_ADAPTED_AVAILABILITY_VERIFY_RESULT_{DATE}.json"


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

    if summary.get("source_rows") != len(rows):
        issues.append("source_rows_mismatch")
    if len(rows) != 7:
        issues.append(f"source_rows_unexpected:{len(rows)}")
    if summary.get("contract_rows") != 1072:
        issues.append(f"contract_rows_unexpected:{summary.get('contract_rows')}")
    if int(summary.get("total_rows_scanned") or 0) <= 0:
        issues.append("total_rows_scanned_empty")
    if summary.get("total_parse_errors") != 0:
        issues.append(f"parse_errors_nonzero:{summary.get('total_parse_errors')}")

    aggregate_fields = summary.get("aggregate_alias_adapted_field_presence_counts") or {}
    if aggregate_fields.get("symbol", 0) <= 0:
        issues.append("symbol_alias_adapted_missing")
    if aggregate_fields.get("route_session", 0) <= 0:
        issues.append("route_session_alias_adapted_missing")
    if aggregate_fields.get("source_component", 0) <= 0:
        issues.append("source_component_alias_adapted_missing")
    if summary.get("max_structurally_coverable_contract_rows_by_single_source") != 0:
        issues.append("unexpected_full_contract_coverage")

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
        row_id = row.get("alias_availability_row_id")
        if row.get("source_exists") is not True:
            issues.append(f"source_missing:{row_id}")
            break
        if int(row.get("parse_errors") or 0) != 0:
            issues.append(f"source_parse_errors:{row_id}")
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
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_ALIAS_ADAPTED_AVAILABILITY",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "source_rows": len(rows),
        "total_rows_scanned": summary.get("total_rows_scanned"),
        "contract_rows": summary.get("contract_rows"),
        "aggregate_alias_adapted_field_presence_counts": aggregate_fields,
        "max_structurally_coverable_contract_rows_by_single_source": summary.get(
            "max_structurally_coverable_contract_rows_by_single_source"
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
