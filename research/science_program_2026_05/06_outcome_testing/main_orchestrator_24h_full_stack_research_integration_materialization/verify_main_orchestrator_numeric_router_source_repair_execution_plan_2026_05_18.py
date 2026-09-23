from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-18"
ROUTE_DIR = Path(__file__).resolve().parent
SOURCE_REPAIR_QUEUE_LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE_LEDGER_{DATE}.jsonl"
LEDGER = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN_MANIFEST_{DATE}.json"
VERIFY_RESULT = ROUTE_DIR / f"MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN_VERIFY_RESULT_{DATE}.json"


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
    for path in (SOURCE_REPAIR_QUEUE_LEDGER, LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if summary.get("plan_rows") != len(rows):
        issues.append("plan_rows_mismatch")
    if len(rows) != 1119:
        issues.append(f"plan_rows_unexpected:{len(rows)}")
    if summary.get("ready_plan_rows") != 1119:
        issues.append(f"ready_plan_rows_unexpected:{summary.get('ready_plan_rows')}")
    if summary.get("input_action_rows") != 17753:
        issues.append(f"input_action_rows_unexpected:{summary.get('input_action_rows')}")

    expected_plan_action_counts = {
        "broker_execution_geometry_exact_r_repair_plan": 10597,
        "source_join_absence_proof_repair_plan": 7045,
        "broker_spread_geometry_attachment_repair_plan": 111,
    }
    plan_action_counts = summary.get("source_repair_plan_kind_input_action_counts") or {}
    for plan_kind, expected in expected_plan_action_counts.items():
        if plan_action_counts.get(plan_kind) != expected:
            issues.append(f"plan_action_count_unexpected:{plan_kind}")
            break

    if summary.get("requires_broker_operation_now_rows") != 0:
        issues.append("requires_broker_operation_now_nonzero")
    for key in (
        "runtime_score_allowed_rows",
        "runtime_candidate_use_permitted_rows",
        "candidate_use_allowed_now_rows",
        "unconditional_scalar_use_allowed_rows",
        "replay_r_reference_counted_as_new_main_result_rows",
    ):
        if summary.get(key) != 0:
            issues.append(f"{key}_nonzero")
            break

    input_ledger = summary.get("input_source_repair_queue_ledger") or {}
    if input_ledger.get("sha256") != sha256_path(SOURCE_REPAIR_QUEUE_LEDGER):
        issues.append("input_source_repair_queue_hash_mismatch")
    if input_ledger.get("rows") != 1119:
        issues.append("input_source_repair_queue_rows_unexpected")

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
        row_id = row.get("source_repair_plan_row_id")
        if row.get("plan_execution_status") != "READY_OFFLINE_SOURCE_REPAIR_PLAN":
            issues.append(f"plan_not_ready:{row_id}")
            break
        if not row.get("required_source_class"):
            issues.append(f"required_source_class_missing:{row_id}")
            break
        if row.get("requires_broker_operation_now") is not False:
            issues.append(f"broker_operation_required_now:{row_id}")
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
        "route_id": "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN",
        "generated_utc": summary.get("generated_utc"),
        "ok": not issues,
        "issues": issues,
        "plan_rows": len(rows),
        "ready_plan_rows": summary.get("ready_plan_rows"),
        "input_action_rows": summary.get("input_action_rows"),
        "source_repair_plan_kind_input_action_counts": plan_action_counts,
        "required_source_class_counts": summary.get("required_source_class_counts") or {},
        "manifest_output_count": len(output_by_name),
        "can_continue_to_next_system_conversion_plate": not issues,
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
