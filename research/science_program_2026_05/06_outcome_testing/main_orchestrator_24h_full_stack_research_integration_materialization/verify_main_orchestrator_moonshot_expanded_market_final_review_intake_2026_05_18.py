from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE_VERIFY_RESULT_{DATE}.json"
MOONSHOT_ROOT = Path("C:/tmp/")


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

    if summary.get("main_candidate_rows") != 1748:
        issues.append("main_candidate_rows_unexpected")
    if summary.get("implementation_candidate_rows") != 1748:
        issues.append("implementation_candidate_rows_unexpected")
    if summary.get("final_review_rows") != len(rows):
        issues.append("final_review_rows_mismatch")
    if len(rows) != 1748:
        issues.append(f"final_review_row_count_unexpected:{len(rows)}")
    if summary.get("main_candidate_bound_rows") != 1748:
        issues.append("main_candidate_bound_rows_unexpected")
    if summary.get("final_review_evidence_rows") != 9266:
        issues.append("final_review_evidence_rows_unexpected")
    if summary.get("evidence_execution_rows_claimed") != 9266:
        issues.append("evidence_execution_rows_claimed_unexpected")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")
    if summary.get("replay_r_reference_counted_as_new_main_result_rows") != 0:
        issues.append("replay_r_counted_as_new_main_result")

    action_counts = summary.get("main_compiler_final_review_action_counts") or {}
    if action_counts.get("KEEP_DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_CANDIDATE") != 1597:
        issues.append("implement_action_count_unexpected")
    if action_counts.get("REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE") != 151:
        issues.append("capacity_redesign_action_count_unexpected")
    integrity_counts = summary.get("final_review_integrity_status_counts") or {}
    if integrity_counts.get("FINAL_REVIEW_VERIFIED") != 1748:
        issues.append("final_review_integrity_not_all_verified")

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
    for field, issue_name in (
        ("final_review_ledger", "final_review_ledger"),
        ("implementation_candidate_ledger", "implementation_candidate_ledger"),
    ):
        path = MOONSHOT_ROOT / str(summary.get(field) or "")
        if path.exists():
            if summary.get(f"{field}_sha256") != sha256_path(path):
                issues.append(f"{issue_name}_hash_mismatch")
        else:
            issues.append(f"{issue_name}_missing")

    for row in rows:
        row_id = row.get("final_review_overlay_row_id")
        if row.get("main_candidate_bound") is not True:
            issues.append(f"main_candidate_not_bound:{row_id}")
            break
        if row.get("final_review_integrity_status") != "FINAL_REVIEW_VERIFIED":
            issues.append(f"integrity_status_not_verified:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_EXPANDED_MARKET_FINAL_REVIEW_INTAKE",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "final_review_rows": len(rows),
        "main_candidate_bound_rows": summary.get("main_candidate_bound_rows"),
        "action_counts": action_counts,
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
