from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP_VERIFY_RESULT_{DATE}.json"


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

    if summary.get("input_rollup_rows") != 1748:
        issues.append("input_rollup_rows_unexpected")
    if summary.get("input_final_review_rows") != 1748:
        issues.append("input_final_review_rows_unexpected")
    if summary.get("adjusted_rollup_rows") != len(rows):
        issues.append("adjusted_rollup_rows_mismatch")
    if len(rows) != 1748:
        issues.append(f"adjusted_rollup_row_count_unexpected:{len(rows)}")
    if summary.get("final_review_overlay_bound_rows") != 1748:
        issues.append("final_review_overlay_bound_rows_unexpected")
    if summary.get("event_registry_match_rows") != 55646:
        issues.append("event_registry_match_rows_unexpected")
    if summary.get("expected_candidate_event_rows") != 9266:
        issues.append("expected_candidate_event_rows_unexpected")
    if summary.get("duplicate_scope_event_match_rows") != 46380:
        issues.append("duplicate_scope_event_match_rows_unexpected")
    if summary.get("final_review_evidence_rows") != 9266:
        issues.append("final_review_evidence_rows_unexpected")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")
    if summary.get("replay_r_reference_counted_as_new_main_result_rows") != 0:
        issues.append("replay_r_counted_as_new_main_result")

    status_counts = summary.get("final_review_adjusted_rollup_status_counts") or {}
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_READY") != 1597:
        issues.append("final_review_implement_ready_count_unexpected")
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN") != 151:
        issues.append("final_review_capacity_blocked_count_unexpected")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (SUMMARY, LEDGER):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    for field, issue_name in (("rollup_ledger", "rollup_ledger"), ("final_review_ledger", "final_review_ledger")):
        path = Path(summary.get(field) or "")
        if path.exists():
            if summary.get(f"{field}_sha256") != sha256_path(path):
                issues.append(f"{issue_name}_hash_mismatch")
        else:
            issues.append(f"{issue_name}_missing")

    for row in rows:
        row_id = row.get("candidate_row_id")
        if row.get("final_review_overlay_bound") is not True:
            issues.append(f"final_review_overlay_not_bound:{row_id}")
            break
        if row.get("final_review_adjusted_rollup_status") not in {
            "DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_READY",
            "DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN",
        }:
            issues.append(f"unexpected_adjusted_status:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_ROLLUP",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "adjusted_rollup_rows": len(rows),
        "status_counts": status_counts,
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
