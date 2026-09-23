from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SELECTOR_RECO_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SELECTOR_RECO_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SELECTOR_RECO_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_FINAL_REVIEW_ADJ_SELECTOR_RECO_VERIFY_RESULT_{DATE}.json"


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

    if summary.get("input_score_rows") != 9266:
        issues.append("input_score_rows_unexpected")
    if summary.get("selector_recommendation_rows") != len(rows):
        issues.append("selector_recommendation_rows_mismatch")
    if len(rows) != 231:
        issues.append(f"selector_recommendation_row_count_unexpected:{len(rows)}")
    if summary.get("event_rows") != 9266:
        issues.append("event_rows_unexpected")
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
    if summary.get("implementation_ready_candidate_rows") != 1597:
        issues.append("implementation_ready_candidate_rows_unexpected")
    if summary.get("capacity_blocked_candidate_rows") != 151:
        issues.append("capacity_blocked_candidate_rows_unexpected")
    if summary.get("binding_repair_candidate_rows") != 0:
        issues.append("binding_repair_candidate_rows_nonzero")
    if summary.get("capacity_blocked_selector_blocklist_required_rows") != 32:
        issues.append("capacity_blocked_selector_blocklist_required_rows_unexpected")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")
    if summary.get("replay_r_reference_counted_as_new_main_result_rows") != 0:
        issues.append("replay_r_counted_as_new_main_result")

    status_counts = summary.get("selector_recommendation_status_counts") or {}
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_SCOPE") != 199:
        issues.append("implement_ready_selector_count_unexpected")
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST") != 22:
        issues.append("mixed_selector_count_unexpected")
    if status_counts.get("DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BLOCK_REDESIGN_ONLY_SCOPE") != 10:
        issues.append("redesign_only_selector_count_unexpected")

    score_status_counts = summary.get("final_review_registry_score_status_counts") or {}
    if score_status_counts.get("DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_MATCHES_ONLY") != 8419:
        issues.append("ready_only_score_count_unexpected")
    if score_status_counts.get("DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_WITH_REDESIGN_MATCHES") != 123:
        issues.append("mixed_score_count_unexpected")
    if score_status_counts.get("DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_REDESIGN_BLOCKED_MATCHES_ONLY") != 724:
        issues.append("redesign_only_score_count_unexpected")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (SUMMARY, LEDGER):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    registry_score_ledger = Path(summary.get("registry_score_ledger") or "")
    if registry_score_ledger.exists():
        if summary.get("registry_score_ledger_sha256") != sha256_path(registry_score_ledger):
            issues.append("registry_score_ledger_hash_mismatch")
    else:
        issues.append("registry_score_ledger_missing")

    previous_rank = 0
    for row in rows:
        rank = int(row.get("selector_recommendation_rank") or 0)
        status = row.get("selector_recommendation_status")
        ready_candidates = int(row.get("implementation_ready_candidate_rows") or 0)
        blocked_candidates = int(row.get("capacity_blocked_candidate_rows") or 0)
        repair_candidates = int(row.get("binding_repair_candidate_rows") or 0)
        if rank != previous_rank + 1:
            issues.append(f"selector_recommendation_rank_gap:{rank}")
            break
        previous_rank = rank
        if ready_candidates > 0 and blocked_candidates == 0:
            if status != "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_SCOPE":
                issues.append(f"ready_selector_status_unexpected:{rank}")
                break
        elif ready_candidates > 0 and blocked_candidates > 0:
            if status != "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST":
                issues.append(f"mixed_selector_status_unexpected:{rank}")
                break
        elif ready_candidates == 0 and blocked_candidates > 0:
            if status != "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BLOCK_REDESIGN_ONLY_SCOPE":
                issues.append(f"redesign_selector_status_unexpected:{rank}")
                break
        elif repair_candidates > 0:
            if status != "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BINDING_REPAIR_REQUIRED":
                issues.append(f"repair_selector_status_unexpected:{rank}")
                break
        if bool(row.get("capacity_blocked_selector_blocklist_required")) != (blocked_candidates > 0):
            issues.append(f"blocklist_flag_unexpected:{rank}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{rank}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{rank}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_FINAL_REVIEW_ADJUSTED_SELECTOR_RECOMMENDATIONS",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "selector_recommendation_rows": len(rows),
        "event_rows": summary.get("event_rows"),
        "registry_match_rows": summary.get("registry_match_rows"),
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
