from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_LEDGER_{DATE}.jsonl"
EMITTER_CONTRACT_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT_LEDGER_{DATE}.jsonl"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_EMITTER_DRY_RUN_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_EMITTER_DRY_RUN_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_EMITTER_DRY_RUN_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_EMITTER_DRY_RUN_VERIFY_RESULT_{DATE}.json"


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
    for path in (CONTRACT_LEDGER, EMITTER_CONTRACT_LEDGER, LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("rows") != len(rows):
        issues.append("dry_run_rows_mismatch")
    if len(rows) != 7:
        issues.append(f"dry_run_rows_unexpected:{len(rows)}")
    if summary.get("source_count") != 7:
        issues.append(f"source_count_unexpected:{summary.get('source_count')}")
    if summary.get("source_rows_scanned") != 256104:
        issues.append(f"source_rows_scanned_unexpected:{summary.get('source_rows_scanned')}")
    if summary.get("total_parse_errors") != 0:
        issues.append(f"parse_errors_nonzero:{summary.get('total_parse_errors')}")
    expected_status_counts = {"CURRENT_ROWS_NO_CATALOG_CONTRACT_MATCH_AFTER_ATTACHMENT": 7}
    if summary.get("dry_run_status_counts") != expected_status_counts:
        issues.append(f"dry_run_status_counts_unexpected:{summary.get('dry_run_status_counts')}")
    if summary.get("emitted_complete_catalog_event_count") != 0:
        issues.append("unexpected_emitted_catalog_events")
    if summary.get("source_rows_with_contract_match_after_catalog_attachment") != 0:
        issues.append("unexpected_source_row_contract_matches")
    if summary.get("source_rows_with_symbol") != 256104:
        issues.append(f"symbol_source_rows_unexpected:{summary.get('source_rows_with_symbol')}")
    if summary.get("source_rows_with_source_component") != 255858:
        issues.append(f"source_component_rows_unexpected:{summary.get('source_rows_with_source_component')}")
    if summary.get("source_rows_with_route_session") != 10829:
        issues.append(f"route_session_rows_unexpected:{summary.get('source_rows_with_route_session')}")

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
    input_emitter_contract_ledger = summary.get("input_emitter_contract_ledger") or {}
    if input_emitter_contract_ledger.get("sha256") != sha256_path(EMITTER_CONTRACT_LEDGER):
        issues.append("input_emitter_contract_hash_mismatch")

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
        row_id = row.get("dry_run_row_id")
        if row.get("source_parse_errors") != 0:
            issues.append(f"row_parse_errors:{row_id}")
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
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVENT_EMITTER_DRY_RUN",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "dry_run_rows": len(rows),
        "source_rows_scanned": summary.get("source_rows_scanned"),
        "emitted_complete_catalog_event_count": summary.get("emitted_complete_catalog_event_count"),
        "dry_run_status_counts": summary.get("dry_run_status_counts"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
