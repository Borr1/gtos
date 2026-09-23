from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REGISTRY_SELF_CHECK_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REGISTRY_SELF_CHECK_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REGISTRY_SELF_CHECK_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REGISTRY_SELF_CHECK_VERIFY_RESULT_{DATE}.json"


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

    expected_rows = int(summary.get("candidate_rows") or -1)
    if len(rows) != expected_rows:
        issues.append(f"ledger_row_count_mismatch:{len(rows)}!={expected_rows}")
    if summary.get("self_check_rows") != len(rows):
        issues.append("summary_self_check_rows_mismatch")
    if summary.get("self_check_pass_rows") != len(rows):
        issues.append("self_check_pass_rows_mismatch")
    if summary.get("self_check_repair_rows") != 0:
        issues.append("self_check_repair_rows_nonzero")
    if int(summary.get("total_registry_match_rows") or 0) < len(rows):
        issues.append("total_registry_matches_less_than_rows")

    registry_summary = summary.get("registry_summary") or {}
    if registry_summary.get("candidate_rows") != len(rows):
        issues.append("registry_candidate_rows_mismatch")
    if registry_summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("registry_runtime_candidate_use_nonzero")

    action_counts = summary.get("action_decision_counts") or {}
    if action_counts.get("REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE") != 1724:
        issues.append("unexpected_leakage_reduced_self_check_count")
    if action_counts.get("REGISTER_DEFAULT_OFF_BRANCH_LOCAL_PRESERVED_REDUCED_SURFACE_CANDIDATE") != 24:
        issues.append("unexpected_preserved_self_check_count")

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
    candidate_summary = Path(summary.get("candidate_summary") or "")
    if candidate_summary.exists():
        if summary.get("candidate_summary_sha256") != sha256_path(candidate_summary):
            issues.append("candidate_summary_hash_mismatch")
    else:
        issues.append("candidate_summary_missing")

    seen_ids = set()
    for row in rows:
        row_id = row.get("self_check_row_id")
        if row_id in seen_ids:
            issues.append(f"duplicate_self_check_row_id:{row_id}")
            break
        seen_ids.add(row_id)
        if row.get("self_match_found") is not True:
            issues.append(f"self_match_missing:{row.get('candidate_row_id')}")
            break
        if row.get("registry_self_check_status") != "REDUCED_SURFACE_REGISTRY_SELF_CHECK_PASS":
            issues.append(f"self_check_status_not_pass:{row_id}")
            break
        if int(row.get("matched_candidate_rows") or 0) < 1:
            issues.append(f"no_registry_matches:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REGISTRY_SELF_CHECK",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "ledger_rows": len(rows),
        "expected_rows": expected_rows,
        "total_registry_match_rows": summary.get("total_registry_match_rows"),
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
