from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT_VERIFY_RESULT_{DATE}.json"


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
    for path in (SUMMARY, LEDGER, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    contract_summary = summary.get("contract_summary") or {}

    if len(rows) != 1748:
        issues.append(f"ledger_row_count_unexpected:{len(rows)}")
    if contract_summary.get("rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if contract_summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if contract_summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")
    if contract_summary.get("replay_r_reference_counted_as_new_main_result_rows") != 0:
        issues.append("replay_r_counted_as_new_main_result")

    action_counts = contract_summary.get("main_compiler_action_counts") or {}
    if action_counts.get("REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE") != 1724:
        issues.append("unexpected_leakage_reduced_contract_count")
    if action_counts.get("REGISTER_DEFAULT_OFF_BRANCH_LOCAL_PRESERVED_REDUCED_SURFACE_CANDIDATE") != 24:
        issues.append("unexpected_preserved_contract_count")

    required_numeric_fields = contract_summary.get("required_numeric_threshold_field_counts") or {}
    for field in (
        "selected_intrabar_cost_adjusted_simulated_r",
        "selected_minus_rejected_intrabar_cost_adjusted_r",
        "temporal_positive_winner_fold_share",
        "temporal_winner_consistency_share",
    ):
        if required_numeric_fields.get(field) != 1724:
            issues.append(f"required_numeric_field_count_unexpected:{field}")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (SUMMARY, LEDGER):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    candidate_ledger = Path(summary.get("candidate_ledger") or "")
    if candidate_ledger.exists():
        if summary.get("candidate_ledger_sha256") != sha256_path(candidate_ledger):
            issues.append("candidate_ledger_hash_mismatch")
    else:
        issues.append("candidate_ledger_missing")

    seen_ids = set()
    for row in rows:
        row_id = row.get("contract_row_id")
        if row_id in seen_ids:
            issues.append(f"duplicate_contract_row_id:{row_id}")
            break
        seen_ids.add(row_id)
        required_fields = set(row.get("required_event_fields") or [])
        for required in ("symbol", "source_symbol", "market_timeframe", "route_session", "horizon_id", "selected_side"):
            if required not in required_fields:
                issues.append(f"row_missing_required_field:{row_id}:{required}")
                break
        if issues and issues[-1].startswith("row_missing_required_field"):
            break
        if row.get("source_capture_contract_status") != "READY_DEFAULT_OFF_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT":
            issues.append(f"row_contract_status_unexpected:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "ledger_rows": len(rows),
        "manifest_output_count": len(output_by_name),
        "action_decision_counts": action_counts,
        "required_numeric_threshold_field_counts": required_numeric_fields,
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
