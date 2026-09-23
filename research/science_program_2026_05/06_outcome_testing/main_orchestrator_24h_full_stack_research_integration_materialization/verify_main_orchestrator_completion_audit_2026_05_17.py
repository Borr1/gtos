from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-17"

AUDIT_PATH = ROUTE_DIR / f"MAIN_ORCH24_COMPLETION_AUDIT_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_COMPLETION_AUDIT_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_PATH = ROUTE_DIR / f"MAIN_ORCH24_COMPLETION_AUDIT_VERIFY_RESULT_{DATE}.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    audit = load_json(AUDIT_PATH)
    manifest = load_json(MANIFEST_PATH)
    issues: list[str] = []

    output_record = manifest.get("outputs", {}).get(str(AUDIT_PATH.relative_to(REPO_ROOT)), {})
    if output_record.get("sha256") != sha256_file(AUDIT_PATH):
        issues.append("completion_audit_hash_mismatch")
    numeric = audit.get("numeric_results", {})
    expected_numbers = {
        "action_rows": 3426,
        "exact_owner_rows": 2,
        "exact_owner_sum": 0.6439,
        "exact_reference_rows": 24,
        "exact_reference_sum": 7.7268,
        "proxy_owner_rows": 718,
        "proxy_owner_sum": 35.50010387,
        "exact_proxy_overlap_rows": 5,
        "exact_proxy_delta_sum": 3.2306,
        "exact_broker_profit_rows": 24,
        "exact_broker_profit_sum_usd": 7685.64,
        "split_rows": 135,
    }
    for key, expected in expected_numbers.items():
        actual = numeric.get(key)
        if isinstance(expected, float):
            if abs(float(actual) - expected) > 1e-9:
                issues.append(f"numeric_mismatch:{key}")
        elif actual != expected:
            issues.append(f"numeric_mismatch:{key}")

    source = audit.get("source_search_proof", {})
    if source.get("materialization_source_paths_scanned") != 1076:
        issues.append("source_paths_scanned_mismatch")
    if source.get("materialization_source_rows_scanned") != 1620573:
        issues.append("source_rows_scanned_mismatch")
    if source.get("missing_exact_r_rows_with_row_level_disposition") != 3402:
        issues.append("missing_exact_row_proof_count_mismatch")
    if source.get("xagusd_position_238316913_missing_close_rows") != 0:
        issues.append("xagusd_close_missing_rows_not_zero")

    scan = audit.get("active_retired_label_scan", {})
    if not scan.get("ok") or scan.get("hits"):
        issues.append("active_retired_label_scan_failed")

    checklist = audit.get("completion_checklist") or []
    if not checklist or any(not item.get("covered") for item in checklist):
        issues.append("completion_checklist_uncovered")
    if audit.get("issues"):
        issues.append("audit_contains_internal_issues")
    if audit.get("terminal_decision") != "CURRENT_REPLAYABLE_GEOMETRY_RESULTS_MATERIALIZED_WITH_EXACT_AND_PROXY_R_ROWS":
        issues.append("terminal_decision_mismatch")
    if audit.get("can_mark_active_24h_goal_complete") is not True:
        issues.append("completion_flag_not_true")

    result = {
        "verified": not issues,
        "issues": issues,
        "can_mark_active_24h_goal_complete": audit.get("can_mark_active_24h_goal_complete"),
        "terminal_decision": audit.get("terminal_decision"),
        "action_rows": numeric.get("action_rows"),
        "exact_owner_rows": numeric.get("exact_owner_rows"),
        "exact_owner_sum": numeric.get("exact_owner_sum"),
        "exact_reference_rows": numeric.get("exact_reference_rows"),
        "exact_reference_sum": numeric.get("exact_reference_sum"),
        "proxy_owner_rows": numeric.get("proxy_owner_rows"),
        "proxy_owner_sum": numeric.get("proxy_owner_sum"),
        "split_rows": numeric.get("split_rows"),
        "source_paths_scanned": source.get("materialization_source_paths_scanned"),
        "source_rows_scanned": source.get("materialization_source_rows_scanned"),
    }
    VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
