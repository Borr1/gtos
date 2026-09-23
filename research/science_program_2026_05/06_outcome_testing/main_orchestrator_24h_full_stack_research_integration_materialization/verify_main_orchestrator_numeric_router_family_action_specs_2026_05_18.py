from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
ACTION_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_ACTION_QUEUE_LEDGER_{DATE}.jsonl"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPEC_VERIFY_RESULT_{DATE}.json"


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
    for path in (ACTION_LEDGER, LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("family_spec_rows") != len(rows):
        issues.append("family_spec_rows_mismatch")
    if len(rows) <= 0:
        issues.append("family_spec_rows_empty")
    if len(rows) >= 28722:
        issues.append(f"family_spec_rows_not_grouped:{len(rows)}")
    if summary.get("input_action_rows") != 28722:
        issues.append(f"input_action_rows_unexpected:{summary.get('input_action_rows')}")

    expected_family_action_counts = {
        "scorer_registry_surface": 5341,
        "avoid_comparator_score": 4115,
        "context_guard_input": 1513,
        "source_repair_proof": 17753,
    }
    family_action_counts = summary.get("output_family_input_action_counts") or {}
    for family, expected in expected_family_action_counts.items():
        if family_action_counts.get(family) != expected:
            issues.append(f"family_action_count_unexpected:{family}")
            break

    expected_action_counts = {
        "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS": 5341,
        "REGISTER_NEGATIVE_PROXY_FAILURE_FEATURE": 3154,
        "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY": 932,
        "FAIL_CLOSED_OR_DOWNWEIGHT_AMBIGUOUS_NEGATIVE_PROXY": 29,
        "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT": 1513,
        "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R": 10597,
        "SOURCE_JOIN_REPAIR_REQUIRED_WITH_CURRENT_PACKET_ABSENCE_PROOF": 7045,
        "BROKER_GEOMETRY_ATTACHMENT_REQUIRED_FOR_EXACT_SPREAD_PROXY": 111,
    }
    action_counts = summary.get("numeric_router_action_counts") or {}
    for action, expected in expected_action_counts.items():
        if action_counts.get(action) != expected:
            issues.append(f"action_count_unexpected:{action}")
            break

    required_targets = {
        "default_off_research_scorer_registry_catalog",
        "default_off_avoid_filter_spec_catalog",
        "default_off_context_guard_spec_catalog",
        "source_repair_queue_catalog",
    }
    target_counts = summary.get("implementation_target_counts") or {}
    missing_targets = sorted(target for target in required_targets if target_counts.get(target, 0) <= 0)
    if missing_targets:
        issues.append(f"missing_implementation_targets:{','.join(missing_targets)}")

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

    input_action_ledger = summary.get("input_action_ledger") or {}
    if input_action_ledger.get("sha256") != sha256_path(ACTION_LEDGER):
        issues.append("input_action_ledger_hash_mismatch")
    if input_action_ledger.get("rows") != 28722:
        issues.append("input_action_ledger_rows_unexpected")

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
        row_id = row.get("numeric_router_family_spec_id")
        if "source_row" in row:
            issues.append(f"source_payload_duplicated:{row_id}")
            break
        if row.get("activation_state") != "DEFAULT_OFF":
            issues.append(f"activation_state_not_default_off:{row_id}")
            break
        if not row.get("implementation_target"):
            issues.append(f"implementation_target_missing:{row_id}")
            break
        if int(row.get("input_action_rows") or 0) <= 0:
            issues.append(f"input_action_rows_empty:{row_id}")
            break
        if not row.get("source_locator_refs"):
            issues.append(f"source_locator_refs_missing:{row_id}")
            break
        if row.get("runtime_score_allowed") is not False:
            issues.append(f"runtime_score_allowed:{row_id}")
            break
        if row.get("runtime_candidate_use_permitted") is not False or row.get("candidate_use_allowed_now") is not False:
            issues.append(f"runtime_or_candidate_use_enabled:{row_id}")
            break
        if row.get("live_effect") is not False:
            issues.append(f"live_effect_enabled:{row_id}")
            break
        if row.get("replay_r_reference_counted_as_new_main_result") is not False:
            issues.append(f"replay_r_counted:{row_id}")
            break

    result = {
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_FAMILY_ACTION_SPECS",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "family_spec_rows": len(rows),
        "input_action_rows": summary.get("input_action_rows"),
        "output_family_input_action_counts": family_action_counts,
        "numeric_router_action_counts": action_counts,
        "implementation_target_counts": target_counts,
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
