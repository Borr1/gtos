from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REPLAY_VALIDATOR_SUMMARY_{DATE}.json"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REPLAY_VALIDATOR_LEDGER_{DATE}.jsonl"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REPLAY_VALIDATOR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REPLAY_VALIDATOR_VERIFY_RESULT_{DATE}.json"
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

    if summary.get("candidate_rows") != 1748:
        issues.append("candidate_rows_unexpected")
    if summary.get("held_match_rows") != len(rows):
        issues.append("held_match_rows_mismatch")
    if len(rows) != 9266:
        issues.append(f"held_match_row_count_unexpected:{len(rows)}")
    if summary.get("expected_candidate_found_rows") != len(rows):
        issues.append("expected_candidate_found_rows_mismatch")
    if summary.get("replay_repair_rows") != 0:
        issues.append("replay_repair_rows_nonzero")
    if summary.get("runtime_candidate_use_permitted_rows") != 0:
        issues.append("runtime_candidate_use_permitted_rows_nonzero")
    if summary.get("candidate_use_allowed_now_rows") != 0:
        issues.append("candidate_use_allowed_now_rows_nonzero")
    if summary.get("replay_r_reference_counted_as_new_main_result_rows") != 0:
        issues.append("replay_r_counted_as_new_main_result")

    decision_counts = summary.get("matched_decision_family_counts") or {}
    if decision_counts.get("implement") != 9266:
        issues.append("matched_decision_family_not_all_implement")

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
    match_ledger = MOONSHOT_ROOT / str(summary.get("match_ledger") or "")
    if match_ledger.exists():
        if summary.get("match_ledger_sha256") != sha256_path(match_ledger):
            issues.append("match_ledger_hash_mismatch")
    else:
        issues.append("match_ledger_missing")

    for row in rows:
        row_id = row.get("replay_validator_row_id")
        if row.get("expected_candidate_found") is not True:
            issues.append(f"expected_candidate_not_found:{row_id}")
            break
        if row.get("replay_validator_status") != "MAIN_REGISTRY_REPLAYS_HELD_MATCH":
            issues.append(f"replay_validator_status_not_pass:{row_id}")
            break
        if int(row.get("registry_matched_candidate_rows") or 0) < 1:
            issues.append(f"registry_match_count_zero:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"row_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"row_replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_REPLAY_VALIDATOR",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "ledger_rows": len(rows),
        "expected_candidate_found_rows": summary.get("expected_candidate_found_rows"),
        "total_registry_matched_candidate_rows": summary.get("total_registry_matched_candidate_rows"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
