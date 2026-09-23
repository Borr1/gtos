#!/usr/bin/env python3
"""Verify final-selection source exhaustion artifacts."""

from __future__ import annotations

import json
import errno
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PARENT_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_full_plan_goal_session_2026_06_19"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EDEADLK:
            raise
        path.unlink(missing_ok=True)
        path.write_text(text, encoding="utf-8")


def stable_verified_utc(result: dict[str, Any]) -> str:
    path = ROUTE / "VERIFICATION_RESULT.json"
    if not path.exists():
        return utc_now()
    try:
        existing = read_json(path)
    except json.JSONDecodeError:
        return utc_now()
    old = {key: value for key, value in existing.items() if key != "verified_utc"}
    new = {key: value for key, value in result.items() if key != "verified_utc"}
    if old == new:
        return existing.get("verified_utc") or utc_now()
    return utc_now()


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "FINAL_SELECTION_SOURCE_EXHAUSTION_SUMMARY.json")
    gates = read_jsonl(ROUTE / "FINAL_SELECTION_GATE_LEDGER.jsonl")
    requirements = read_jsonl(ROUTE / "FINAL_SELECTION_SOURCE_REQUIREMENT_LEDGER.jsonl")
    evidence = read_jsonl(ROUTE / "FINAL_SELECTION_EVIDENCE_POINTER_LEDGER.jsonl")
    decisions = read_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    repairs = read_jsonl(ROUTE / "REPAIR_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")

    if summary.get("status") != "final_selection_source_exhaustion_checkpoint_no_final_package":
        issues.append("summary_status_mismatch")
    if summary.get("gate_rows") != len(gates) or len(gates) != 14:
        issues.append("gate_row_count_mismatch")
    if summary.get("open_gate_rows") != 12:
        issues.append("open_gate_row_count_mismatch")
    if summary.get("requirement_rows") != len(requirements) or len(requirements) != 13:
        issues.append("requirement_row_count_mismatch")
    if summary.get("evidence_pointer_rows") != len(evidence) or len(evidence) != 10:
        issues.append("evidence_pointer_row_count_mismatch")
    if summary.get("broker_actual_r_joined_rows") != 1:
        issues.append("broker_actual_r_joined_rows_not_one")
    if summary.get("close_side_all_in_cost_joined_rows") != 1:
        issues.append("close_side_cost_rows_not_one")
    if summary.get("remaining_required_close_history_rows") != 8:
        issues.append("remaining_close_history_rows_not_eight")
    if summary.get("training_ready_label_count") != 0:
        issues.append("training_ready_label_count_nonzero")
    if summary.get("order_type_exact_join_rows") != 0:
        issues.append("order_type_exact_join_rows_nonzero")
    if summary.get("wave_f_validation_proxy_checkpoint_materialized") is not True:
        issues.append("wave_f_validation_checkpoint_not_materialized")
    if summary.get("wave_h_rework_required") is not True:
        issues.append("wave_h_rework_required_not_true")
    if not str(summary.get("vps_fetch_current_session_status", "")).startswith("passed_origin_vps_floor_or_newer:"):
        issues.append("vps_fetch_status_mismatch")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")

    terminal = summary.get("terminal_decision", {})
    if terminal.get("current_local_sources_exhausted_for_final_selection") is not True:
        issues.append("current_local_exhaustion_flag_not_true")
    for field in [
        "final_package_selected",
        "model_training_allowed",
        "deployment_dossier_allowed",
        "live_execution_activation_allowed",
        "broker_real_expectancy_claim_allowed",
    ]:
        if terminal.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")

    gate_by_id = {row.get("gate_id"): row for row in gates}
    required_gate_ids = {f"FSG{idx:03d}" for idx in range(1, 15)}
    if set(gate_by_id) != required_gate_ids:
        issues.append("gate_ids_mismatch")
    if gate_by_id.get("FSG001", {}).get("status") != "closed_current_vps_floor_verified":
        issues.append("fsg001_not_closed")
    if gate_by_id.get("FSG003", {}).get("status") != "partial_ticket_bound_repair_remaining_close_history_required":
        issues.append("fsg003_partial_status_mismatch")
    if gate_by_id.get("FSG004", {}).get("status") != "partial_ticket_bound_close_cost_repair_remaining_rows_required":
        issues.append("fsg004_partial_status_mismatch")
    for gate_id, row in gate_by_id.items():
        if row.get("final_selection_allowed") is not False:
            issues.append(f"gate_allows_final_selection:{gate_id}")
        if gate_id != "FSG014" and not row.get("required_repair"):
            issues.append(f"gate_missing_required_repair:{gate_id}")
    requirement_gate_ids = {row.get("gate_id") for row in requirements}
    if requirement_gate_ids != {f"FSG{idx:03d}" for idx in range(1, 14)}:
        issues.append("requirement_gate_ids_mismatch")
    if len(decisions) < 3:
        issues.append("decision_rows_too_low")
    if len(repairs) < 3:
        issues.append("repair_rows_too_low")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    if completion.get("verification", {}).get("final_selection_source_exhaustion") not in {"pending", "passed"}:
        issues.append("completion_verification_status_invalid")
    manifest_files = set(manifest.get("files") or [])
    for required in [
        "FINAL_SELECTION_SOURCE_EXHAUSTION_SUMMARY.json",
        "FINAL_SELECTION_GATE_LEDGER.jsonl",
        "FINAL_SELECTION_SOURCE_REQUIREMENT_LEDGER.jsonl",
        "FINAL_SELECTION_EVIDENCE_POINTER_LEDGER.jsonl",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in manifest_files:
            issues.append(f"manifest_missing:{required}")
    if any(row.get("readable") is not True for row in evidence):
        issues.append("evidence_pointer_unreadable")

    parent_questions = {row.get("question_id"): row for row in read_jsonl(PARENT_ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl")}
    parent_sources = {row.get("request_id"): row for row in read_jsonl(PARENT_ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl")}
    parent_merges = {row.get("decision_id"): row for row in read_jsonl(PARENT_ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl")}
    if parent_questions.get("PQ025", {}).get("status") != "answered_final_selection_source_exhaustion_partial_broker_repair":
        issues.append("parent_pq025_missing")
    if parent_sources.get("PSR025", {}).get("status") != "partial_broker_close_history_repaired_remaining_final_selection_sources_exact":
        issues.append("parent_psr025_missing")
    if parent_merges.get("PMD023", {}).get("status") != "selected":
        issues.append("parent_pmd023_missing")

    result = {
        "schema": "gtos.final_moonshot.final_selection.source_exhaustion.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "gate_rows": len(gates),
        "open_gate_rows": summary.get("open_gate_rows"),
        "requirement_rows": len(requirements),
        "evidence_pointer_rows": len(evidence),
        "broker_actual_r_joined_rows": summary.get("broker_actual_r_joined_rows"),
        "close_side_all_in_cost_joined_rows": summary.get("close_side_all_in_cost_joined_rows"),
        "remaining_required_close_history_rows": summary.get("remaining_required_close_history_rows"),
        "training_ready_label_count": summary.get("training_ready_label_count"),
        "order_type_exact_join_rows": summary.get("order_type_exact_join_rows"),
        "final_package_selected": terminal.get("final_package_selected"),
        "wave_h_rework_required": summary.get("wave_h_rework_required"),
        "forbidden_surface_status": summary.get("forbidden_surface_status", {}),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    completion["verification"]["final_selection_source_exhaustion"] = "passed" if not issues else "failed"
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    focused = read_json(ROUTE / "FOCUSED_TEST_RESULT.json")
    focused["status"] = "passed" if not issues else "failed"
    focused["verification_result"] = {
        "ok": result["ok"],
        "issue_count": result["issue_count"],
        "verified_utc": result["verified_utc"],
    }
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
