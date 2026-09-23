from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SCOPE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SCOPE_DECISION_LEDGER_{DATE}.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECO_LEDGER_{DATE}.jsonl"
SOURCE_INVENTORY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_INVENTORY_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECO_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECO_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECO_VERIFY_RESULT_{DATE}.json"


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
    for path in (SCOPE_LEDGER, SYSTEM_LEDGER, SOURCE_INVENTORY, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    scope_rows = read_jsonl(SCOPE_LEDGER) if SCOPE_LEDGER.exists() else []
    system_rows = read_jsonl(SYSTEM_LEDGER) if SYSTEM_LEDGER.exists() else []
    inventory_rows = read_jsonl(SOURCE_INVENTORY) if SOURCE_INVENTORY.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("scope_system_decision_rows") != len(scope_rows):
        issues.append("scope_system_decision_rows_mismatch")
    if len(scope_rows) != 290:
        issues.append(f"scope_system_decision_row_count_unexpected:{len(scope_rows)}")
    if summary.get("system_recommendation_rows") != len(system_rows):
        issues.append("system_recommendation_rows_mismatch")
    if len(system_rows) != 1:
        issues.append(f"system_recommendation_row_count_unexpected:{len(system_rows)}")
    if summary.get("source_inventory_rows") != len(inventory_rows):
        issues.append("source_inventory_rows_mismatch")
    if len(inventory_rows) != 12:
        issues.append(f"source_inventory_row_count_unexpected:{len(inventory_rows)}")
    if summary.get("source_inventory_missing_rows") != 0:
        issues.append("source_inventory_missing_rows_nonzero")

    decision_counts = summary.get("router_scope_decision_counts") or {}
    if decision_counts.get("IMPLEMENT_DEFAULT_OFF_SCORER_SCOPE_WITH_GUARDS") != 177:
        issues.append("default_off_scorer_scope_count_unexpected")
    if decision_counts.get("IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE") != 54:
        issues.append("avoid_inverse_scope_count_unexpected")
    if decision_counts.get("EXECUTE_SOURCE_GEOMETRY_REPAIR_SCOPE") != 41:
        issues.append("source_geometry_repair_scope_count_unexpected")
    if decision_counts.get("MERGE_CONTEXT_STRESS_SCOPE_AS_GUARD_INPUT") != 18:
        issues.append("context_stress_scope_count_unexpected")

    result_counts = summary.get("source_result_counts") or {}
    expected_result_counts = {
        "scope_system_decision_rows": 290,
        "scorer_registry_surface_rows": 5341,
        "avoid_comparator_score_rows": 4115,
        "context_guard_input_rows": 1513,
        "source_repair_proof_rows": 17753,
        "system_recommendation_rows": 1,
        "symbol_rollup_rows": 8,
    }
    for key, expected in expected_result_counts.items():
        if result_counts.get(key) != expected:
            issues.append(f"source_result_count_unexpected:{key}")
            break

    expected_summary_counts = {
        "scope_row_count_sum": 17916,
        "scope_score_count_sum": 5341,
        "scope_scorer_event_count_sum": 5341,
        "scope_avoid_inverse_event_count_sum": 4115,
        "scope_context_stress_event_count_sum": 1513,
        "scope_source_repair_event_count_sum": 6947,
        "system_scorer_registry_surface_rows": 5341,
        "system_avoid_comparator_score_rows": 4115,
        "system_context_guard_input_rows": 1513,
        "system_source_repair_proof_rows": 17753,
        "runtime_score_allowed_rows": 0,
        "runtime_candidate_use_permitted_rows": 0,
        "candidate_use_allowed_now_rows": 0,
        "summary_only_terminal_rows": 0,
        "live_effect_rows": 0,
        "replay_r_reference_counted_as_new_main_result_rows": 0,
    }
    for key, expected in expected_summary_counts.items():
        if summary.get(key) != expected:
            issues.append(f"summary_count_unexpected:{key}")
            break

    output_by_name = {Path(item["path"]).name: item for item in manifest.get("outputs") or []}
    for path in (SCOPE_LEDGER, SYSTEM_LEDGER, SOURCE_INVENTORY, SUMMARY):
        item = output_by_name.get(path.name)
        if not item:
            issues.append(f"manifest_missing_output:{path.name}")
            continue
        if item.get("sha256") != sha256_path(path):
            issues.append(f"manifest_hash_mismatch:{path.name}")

    for row in inventory_rows:
        if row.get("source_exists") is not True:
            issues.append(f"inventory_source_missing:{row.get('logical_name')}")
            break
        if not row.get("source_sha256") or not row.get("source_bytes"):
            issues.append(f"inventory_source_hash_or_size_missing:{row.get('logical_name')}")
            break

    for row in scope_rows:
        row_id = row.get("scope_system_decision_row_id")
        if row.get("summary_only_terminal") is not False:
            issues.append(f"scope_summary_only_terminal:{row_id}")
            break
        if row.get("runtime_score_allowed") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"scope_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("live_effect") is not False:
            issues.append(f"scope_live_effect_enabled:{row_id}")
            break

    for row in system_rows:
        row_id = row.get("system_recommendation_row_id")
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"system_runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"system_replay_r_counted:{row_id}")
            break
        if row.get("live_effect") is not False:
            issues.append(f"system_live_effect_enabled:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SYSTEM_RECOMMENDATION_INTAKE",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "scope_system_decision_rows": len(scope_rows),
        "system_recommendation_rows": len(system_rows),
        "source_inventory_rows": len(inventory_rows),
        "router_scope_decision_counts": decision_counts,
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
