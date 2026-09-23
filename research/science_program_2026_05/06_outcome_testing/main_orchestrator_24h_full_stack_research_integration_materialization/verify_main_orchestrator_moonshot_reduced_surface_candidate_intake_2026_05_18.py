from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_VERIFY_RESULT_{DATE}.json"


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

    source_counts = summary.get("moonshot_reduced_surface_execution_counts") or {}
    expected_rows = int(source_counts.get("execution_rows") or -1)
    if len(rows) != expected_rows:
        issues.append(f"ledger_row_count_mismatch:{len(rows)}!={expected_rows}")
    if source_counts.get("execution_pass_rows") != expected_rows:
        issues.append("source_execution_pass_rows_mismatch")
    if source_counts.get("execution_repair_rows") != 0:
        issues.append("source_execution_repair_rows_nonzero")
    if source_counts.get("self_test_pass_rows") != expected_rows:
        issues.append("source_self_test_pass_rows_mismatch")
    if source_counts.get("execution_match_rows") != 9266:
        issues.append("source_execution_match_rows_unexpected")

    candidate_summary = summary.get("candidate_summary") or {}
    if candidate_summary.get("rows") != len(rows):
        issues.append("summary_rows_mismatch")
    if candidate_summary.get("matched_selection_rows") != 9266:
        issues.append("summary_matched_selection_rows_unexpected")
    if candidate_summary.get("matched_implement_rows") != 9266:
        issues.append("summary_matched_implement_rows_unexpected")
    if candidate_summary.get("matched_nonimplement_rows") != 0:
        issues.append("summary_matched_nonimplement_rows_nonzero")
    if candidate_summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if candidate_summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")
    if candidate_summary.get("replay_r_reference_counted_as_new_main_result_rows") != 0:
        issues.append("replay_r_counted_as_new_main_result")

    action_counts = summary.get("action_decision_counts") or {}
    if action_counts.get("REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE") != 1724:
        issues.append("unexpected_leakage_reduced_candidate_count")
    if action_counts.get("REGISTER_DEFAULT_OFF_BRANCH_LOCAL_PRESERVED_REDUCED_SURFACE_CANDIDATE") != 24:
        issues.append("unexpected_preserved_candidate_count")

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (SUMMARY, LEDGER):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    source_manifest = summary.get("source_manifest") or []
    for source in source_manifest:
        source_path = Path(source.get("absolute_path") or "")
        if not source_path.exists():
            issues.append(f"missing_source:{source.get('path')}")
            continue
        if source.get("sha256") != sha256_path(source_path):
            issues.append(f"source_hash_mismatch:{source.get('path')}")

    seen_ids = set()
    for row in rows:
        row_id = row.get("candidate_row_id")
        if row_id in seen_ids:
            issues.append(f"duplicate_candidate_row_id:{row_id}")
            break
        seen_ids.add(row_id)
        if row.get("execution_integrity_status") != "REDUCED_SURFACE_EXECUTION_VERIFIED_PASS":
            issues.append(f"execution_integrity_not_pass:{row_id}")
            break
        if row.get("branch_local_candidate_status") != "READY_DEFAULT_OFF_BRANCH_LOCAL_CANDIDATE":
            issues.append(f"candidate_status_not_ready:{row_id}")
            break
        if int(row.get("matched_nonimplement_rows") or 0) != 0:
            issues.append(f"row_nonimplement_matches:{row_id}")
            break
        if int(row.get("matched_selection_rows") or 0) != int(row.get("expected_matched_selection_rows") or -1):
            issues.append(f"row_expected_match_mismatch:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted_as_new_main_result:{row_id}")
            break
        boundary = row.get("research_boundary") or {}
        if boundary.get("runtime_candidate_use_permitted") is not False:
            issues.append(f"row_boundary_runtime_enabled:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATES",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "ledger_rows": len(rows),
        "expected_rows": expected_rows,
        "source_count": len(source_manifest),
        "manifest_output_count": len(output_by_name),
        "action_decision_counts": action_counts,
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
