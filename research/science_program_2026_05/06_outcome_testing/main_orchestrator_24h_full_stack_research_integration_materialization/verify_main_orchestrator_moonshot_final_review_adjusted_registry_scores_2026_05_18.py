from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_REGISTRY_SCORE_VERIFY_RESULT_{DATE}.json"


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

    if summary.get("candidate_rows") != 1748:
        issues.append("candidate_rows_unexpected")
    if summary.get("event_rows") != 9266:
        issues.append("event_rows_unexpected")
    if summary.get("adjusted_rollup_rows") != 1748:
        issues.append("adjusted_rollup_rows_unexpected")
    if summary.get("score_rows") != len(rows):
        issues.append("score_rows_mismatch")
    if len(rows) != 9266:
        issues.append(f"score_row_count_unexpected:{len(rows)}")
    if summary.get("registry_match_rows") != 55646:
        issues.append("registry_match_rows_unexpected")
    if summary.get("implementation_ready_registry_match_rows") != 50659:
        issues.append("implementation_ready_registry_match_rows_unexpected")
    if summary.get("capacity_blocked_registry_match_rows") != 4987:
        issues.append("capacity_blocked_registry_match_rows_unexpected")
    if summary.get("binding_repair_registry_match_rows") != 0:
        issues.append("binding_repair_registry_match_rows_nonzero")
    if summary.get("expected_candidate_found_in_registry_rows") != 9266:
        issues.append("expected_candidate_found_rows_unexpected")
    if summary.get("expected_candidate_implementation_ready_rows") != 8453:
        issues.append("expected_candidate_implementation_ready_rows_unexpected")
    if summary.get("expected_candidate_capacity_blocked_rows") != 813:
        issues.append("expected_candidate_capacity_blocked_rows_unexpected")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")
    if summary.get("replay_r_reference_counted_as_new_main_result_rows") != 0:
        issues.append("replay_r_counted_as_new_main_result")

    status_counts = summary.get("final_review_registry_score_status_counts") or {}
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_MATCHES_ONLY") != 8419:
        issues.append("ready_only_score_count_unexpected")
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_WITH_REDESIGN_MATCHES") != 123:
        issues.append("mixed_score_count_unexpected")
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_REDESIGN_BLOCKED_MATCHES_ONLY") != 724:
        issues.append("redesign_only_score_count_unexpected")

    match_status_counts = summary.get("final_review_registry_match_status_counts") or {}
    if match_status_counts.get("DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_READY") != 50659:
        issues.append("ready_match_status_count_unexpected")
    if match_status_counts.get("DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN") != 4987:
        issues.append("blocked_match_status_count_unexpected")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (SUMMARY, LEDGER):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    for field, issue_name in (
        ("candidate_ledger", "candidate_ledger"),
        ("event_ledger", "event_ledger"),
        ("adjusted_rollup_ledger", "adjusted_rollup_ledger"),
    ):
        path = Path(summary.get(field) or "")
        if path.exists():
            if summary.get(f"{field}_sha256") != sha256_path(path):
                issues.append(f"{issue_name}_hash_mismatch")
        else:
            issues.append(f"{issue_name}_missing")

    for row in rows:
        row_id = row.get("event_row_id")
        ready = int(row.get("implementation_ready_registry_match_rows") or 0)
        blocked = int(row.get("capacity_blocked_registry_match_rows") or 0)
        repair = int(row.get("binding_repair_registry_match_rows") or 0)
        total = int(row.get("registry_match_rows") or 0)
        status = row.get("final_review_registry_score_status")
        if ready + blocked + repair != total:
            issues.append(f"registry_match_sum_mismatch:{row_id}")
            break
        if ready > 0 and blocked == 0 and status != "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_MATCHES_ONLY":
            issues.append(f"ready_only_status_unexpected:{row_id}")
            break
        if ready > 0 and blocked > 0 and status != "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_WITH_REDESIGN_MATCHES":
            issues.append(f"mixed_status_unexpected:{row_id}")
            break
        if ready == 0 and blocked > 0 and status != "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_REDESIGN_BLOCKED_MATCHES_ONLY":
            issues.append(f"redesign_only_status_unexpected:{row_id}")
            break
        if row.get("expected_candidate_found_in_registry") is not True:
            issues.append(f"expected_candidate_not_found:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_REGISTRY_SCORES",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "score_rows": len(rows),
        "registry_match_rows": summary.get("registry_match_rows"),
        "implementation_ready_registry_match_rows": summary.get("implementation_ready_registry_match_rows"),
        "capacity_blocked_registry_match_rows": summary.get("capacity_blocked_registry_match_rows"),
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
