"""Verify exact-R bridge search materialization."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROUTE_DIR = Path(__file__).resolve().parent
ACTION_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_SUMMARY_2026-05-17.json"
MANIFEST_PATH = ROUTE_DIR / "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_OUTPUT_MANIFEST_2026-05-17.json"
VERIFY_PATH = ROUTE_DIR / "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_VERIFICATION_RESULT_2026-05-17.json"

RESULT_SCOPE = {
    "result_use": "RESULT_MATERIALIZATION_REQUIRED",
    "source_operation": "LOCAL_LOG_AND_READONLY_ACCOUNT_HISTORY_SEARCH",
    "runtime_change": "NONE_FROM_SEARCH",
    "ledger_effect": "EXACT_R_OWNER_REFERENCE_AND_UNRESOLVED_ROW_DISPOSITION",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    action_rows = read_jsonl(ACTION_LEDGER)
    rows = read_jsonl(OUTPUT_LEDGER)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    issues: list[str] = []
    if len(rows) != len(action_rows):
        issues.append("row_count_mismatch")
    if summary.get("input_action_rows") != len(action_rows):
        issues.append("summary_input_count_mismatch")
    if summary.get("before_exact_r_rows") != 0:
        issues.append("before_exact_r_rows_not_zero")
    if summary.get("after_exact_r_owner_rows") != 2:
        issues.append("exact_owner_row_count_mismatch")
    if abs(float(summary.get("after_exact_r_owner_sum", 0.0)) - 0.6439) > 1e-9:
        issues.append("exact_owner_sum_mismatch")
    if summary.get("after_exact_r_reference_rows") != 24:
        issues.append("exact_reference_row_count_mismatch")
    if summary.get("exact_r_owner_row_delta") != 2:
        issues.append("exact_owner_delta_mismatch")

    row_status_counts = Counter(row.get("exact_r_bridge_status") for row in rows)
    if dict(sorted(row_status_counts.items())) != summary.get("exact_r_status_counts"):
        issues.append("status_counts_mismatch")
    decision_counts = Counter(row.get("exact_join_decision") for row in rows)
    if dict(sorted(decision_counts.items())) != summary.get("exact_join_decision_counts"):
        issues.append("decision_counts_mismatch")

    for index, (action, row) in enumerate(zip(action_rows, rows), 1):
        if row.get("source_action_row_id") != action.get("row_id"):
            issues.append(f"row_identity_mismatch:{index}")
            break
        if not row.get("candidate_id") or not row.get("candidate_symbol"):
            issues.append(f"missing_identity_fields:{index}")
            break
        if not row.get("strategy_or_family_id"):
            issues.append(f"missing_strategy_or_family_id:{index}")
            break
        if row.get("symbol") != row.get("candidate_symbol"):
            issues.append(f"symbol_mismatch:{index}")
            break
        if not row.get("searched_source_paths"):
            issues.append(f"missing_source_paths:{index}")
            break
        if not (row.get("searched_candidate_keys") or row.get("searched_trade_keys") or row.get("searched_order_position_keys")):
            issues.append(f"missing_searched_keys:{index}")
            break
        if row.get("result_scope") != RESULT_SCOPE:
            issues.append(f"result_scope_mismatch:{index}")
            break
        if row.get("exact_r_bridge_status") == "EXACT_R_NOT_FOUND" and not row.get("missing_identifier"):
            issues.append(f"missing_identifier_absent:{index}")
            break

    owner_rows = [row for row in rows if row.get("exact_r_bridge_status") == "EXACT_R_COUNTED_ON_OWNER_ROW"]
    owner_by_candidate = {row.get("candidate_id"): row for row in owner_rows}
    gbpjpy_owner = owner_by_candidate.get("GBPJPY_2026-05-11T07:30:00+00:00")
    if not gbpjpy_owner:
        issues.append("gbpjpy_owner_missing")
    else:
        if gbpjpy_owner.get("strategy_id") != "PENDING_LIMIT_LIFECYCLE":
            issues.append("gbpjpy_owner_strategy_mismatch")
        if gbpjpy_owner.get("pending_lifecycle_trade_state_ticket") != 237192029:
            issues.append("gbpjpy_owner_position_mismatch")
        if gbpjpy_owner.get("exact_r_mt5_deal_id") != 221459626:
            issues.append("gbpjpy_owner_deal_mismatch")
    xagusd_owner = owner_by_candidate.get("XAGUSD_2026-05-14T13:15:00+00:00")
    if not xagusd_owner:
        issues.append("xagusd_owner_missing")
    else:
        if xagusd_owner.get("pending_lifecycle_trade_state_ticket") != 238316913:
            issues.append("xagusd_owner_position_mismatch")
        if xagusd_owner.get("exact_r_mt5_deal_id") != 222552477:
            issues.append("xagusd_owner_deal_mismatch")
        if abs(float(xagusd_owner.get("exact_r") or 0.0) - 0.0289) > 1e-9:
            issues.append("xagusd_owner_exact_r_mismatch")
    xagusd_missing = [
        row
        for row in rows
        if row.get("candidate_id") == "XAGUSD_2026-05-14T13:15:00+00:00"
        and row.get("missing_identifier") == "mt5_account_history_close_deal_for_position_id=238316913"
    ]
    if xagusd_missing:
        issues.append("xagusd_missing_close_deal_not_resolved")

    for output_path in (OUTPUT_LEDGER, SUMMARY_PATH):
        manifest_hash = manifest.get("outputs", {}).get(str(output_path), {}).get("sha256")
        if manifest_hash != sha256_file(output_path):
            issues.append(f"manifest_hash_mismatch:{output_path.name}")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "before_exact_r_rows": summary.get("before_exact_r_rows"),
        "after_exact_r_owner_rows": summary.get("after_exact_r_owner_rows"),
        "after_exact_r_owner_sum": summary.get("after_exact_r_owner_sum"),
        "after_exact_r_reference_rows": summary.get("after_exact_r_reference_rows"),
        "local_non_account_r_reference_rows": summary.get("local_non_account_r_reference_rows"),
        "missing_identifier_counts": summary.get("missing_identifier_counts"),
    }
    VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
