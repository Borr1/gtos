from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP_VERIFY_RESULT_{DATE}.json"


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
    if summary.get("rollup_rows") != len(rows):
        issues.append("rollup_rows_mismatch")
    if len(rows) != 1748:
        issues.append(f"rollup_row_count_unexpected:{len(rows)}")
    if summary.get("candidates_with_event_matches") != 1748:
        issues.append("candidates_with_event_matches_unexpected")
    if summary.get("candidates_without_event_matches") != 0:
        issues.append("candidates_without_event_matches_nonzero")
    if summary.get("event_registry_match_rows") != 55646:
        issues.append("event_registry_match_rows_unexpected")
    if summary.get("expected_candidate_event_rows") != 9266:
        issues.append("expected_candidate_event_rows_unexpected")
    if summary.get("duplicate_scope_event_match_rows") != 46380:
        issues.append("duplicate_scope_event_match_rows_unexpected")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")
    if summary.get("replay_r_reference_counted_as_new_main_result_rows") != 0:
        issues.append("replay_r_counted_as_new_main_result")

    status_counts = summary.get("candidate_event_rollup_status_counts") or {}
    if status_counts.get("DEFAULT_OFF_REDUCED_SURFACE_CANDIDATE_HAS_EVENT_MATCHES") != 1748:
        issues.append("rollup_status_not_all_matched")
    action_counts = summary.get("main_compiler_action_counts") or {}
    if action_counts.get("REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE") != 1724:
        issues.append("leakage_reduced_action_count_unexpected")
    if action_counts.get("REGISTER_DEFAULT_OFF_BRANCH_LOCAL_PRESERVED_REDUCED_SURFACE_CANDIDATE") != 24:
        issues.append("preserved_action_count_unexpected")

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
    event_ledger = Path(summary.get("event_ledger") or "")
    if event_ledger.exists():
        if summary.get("event_ledger_sha256") != sha256_path(event_ledger):
            issues.append("event_ledger_hash_mismatch")
    else:
        issues.append("event_ledger_missing")

    for row in rows:
        row_id = row.get("candidate_row_id")
        if row.get("candidate_event_rollup_status") != "DEFAULT_OFF_REDUCED_SURFACE_CANDIDATE_HAS_EVENT_MATCHES":
            issues.append(f"candidate_rollup_status_not_matched:{row_id}")
            break
        if int(row.get("event_registry_match_rows") or 0) <= 0:
            issues.append(f"candidate_event_match_count_zero:{row_id}")
            break
        if int(row.get("expected_candidate_event_rows") or 0) <= 0:
            issues.append(f"candidate_expected_event_count_zero:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_SCORER_ROLLUP",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "rollup_rows": len(rows),
        "event_rows": summary.get("event_rows"),
        "event_registry_match_rows": summary.get("event_registry_match_rows"),
        "expected_candidate_event_rows": summary.get("expected_candidate_event_rows"),
        "candidates_without_event_matches": summary.get("candidates_without_event_matches"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
