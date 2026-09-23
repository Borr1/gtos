from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
CATALOG_LEDGER_PATHS = [
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SCORER_REGISTRY_CATALOG_LEDGER_{DATE}.jsonl",
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_AVOID_FILTER_CATALOG_LEDGER_{DATE}.jsonl",
    ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CONTEXT_GUARD_CATALOG_LEDGER_{DATE}.jsonl",
]
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVALUATOR_SELF_CHECK_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVALUATOR_SELF_CHECK_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVALUATOR_SELF_CHECK_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVALUATOR_SELF_CHECK_VERIFY_RESULT_{DATE}.json"


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
    for path in [*CATALOG_LEDGER_PATHS, LEDGER, SUMMARY, MANIFEST]:
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("self_check_rows") != len(rows):
        issues.append("self_check_rows_mismatch")
    if len(rows) != 1072:
        issues.append(f"self_check_rows_unexpected:{len(rows)}")
    status_counts = summary.get("self_check_status_counts") or {}
    if status_counts.get("PASS") != 1072 or status_counts.get("FAIL", 0) != 0:
        issues.append("self_check_status_counts_unexpected")

    catalog_summary = summary.get("catalog_summary") or {}
    if catalog_summary.get("catalog_entries") != 1072:
        issues.append("catalog_entry_count_unexpected")
    if catalog_summary.get("input_action_rows") != 10969:
        issues.append(f"catalog_input_action_rows_unexpected:{catalog_summary.get('input_action_rows')}")
    expected_catalog_counts = {
        "default_off_scorer_registry_catalog_entry": 340,
        "default_off_avoid_filter_catalog_entry": 470,
        "default_off_context_guard_catalog_entry": 262,
    }
    catalog_counts = catalog_summary.get("catalog_type_counts") or {}
    for catalog_type, expected in expected_catalog_counts.items():
        if catalog_counts.get(catalog_type) != expected:
            issues.append(f"catalog_count_unexpected:{catalog_type}")
            break
    if catalog_counts.get("source_repair_queue_entry", 0) != 0:
        issues.append("source_repair_queue_in_default_evaluator_self_check")

    for key in (
        "live_effect_rows",
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero")
            break

    for item in summary.get("input_catalog_ledgers") or []:
        path = Path(item.get("path") or "")
        if not path.exists():
            issues.append(f"input_catalog_ledger_missing:{item.get('path')}")
            break
        if item.get("sha256") != sha256_path(path):
            issues.append(f"input_catalog_ledger_hash_mismatch:{item.get('path')}")
            break

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (LEDGER, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")
        if path.suffix == ".jsonl" and path.stat().st_size >= 100_000_000:
            issues.append(f"raw_jsonl_over_github_limit:{path.name}")

    for row in rows:
        row_id = row.get("self_check_row_id")
        if row.get("self_check_status") != "PASS":
            issues.append(f"self_check_not_pass:{row_id}")
            break
        if row.get("matched_own_entry") is not True:
            issues.append(f"own_entry_not_matched:{row_id}")
            break
        if int(row.get("match_count") or 0) <= 0:
            issues.append(f"match_count_empty:{row_id}")
            break
        if row.get("runtime_score_allowed") is not False:
            issues.append(f"runtime_score_allowed:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_CATALOG_EVALUATOR_SELF_CHECK",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "self_check_rows": len(rows),
        "self_check_status_counts": status_counts,
        "catalog_type_counts": catalog_counts,
        "catalog_input_action_rows": catalog_summary.get("input_action_rows"),
        "match_count_sum": summary.get("match_count_sum"),
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
