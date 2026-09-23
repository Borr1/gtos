#!/usr/bin/env python3
"""Verify Wave H rework artifacts after final-selection source exhaustion."""

from __future__ import annotations

import json
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
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    summary = read_json(ROUTE / "WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json")
    audit_rows = read_jsonl(ROUTE / "WAVE_H_REWORK_AUDIT_LEDGER.jsonl")
    issue_rows = read_jsonl(ROUTE / "WAVE_H_REWORK_ISSUE_LEDGER.jsonl")
    decision = read_json(ROUTE / "WAVE_H_REWORK_DECISION.json")
    decisions = read_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    repairs = read_jsonl(ROUTE / "REPAIR_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")

    if summary.get("status") != "wave_h_rework_after_final_selection_checkpoint_still_blocked":
        issues.append("summary_status_mismatch")
    if summary.get("audit_rows") != len(audit_rows) or len(audit_rows) != 14:
        issues.append("audit_row_count_mismatch")
    if summary.get("issue_rows") != len(issue_rows) or len(issue_rows) != 13:
        issues.append("issue_row_count_mismatch")
    if summary.get("blocking_issue_rows") != len(issue_rows):
        issues.append("blocking_issue_row_count_mismatch")
    if summary.get("final_selection_gate_rows") != 14:
        issues.append("final_selection_gate_rows_mismatch")
    if summary.get("final_selection_open_gate_rows") != 13:
        issues.append("final_selection_open_gate_rows_mismatch")
    if summary.get("rework_current_gate_materialized") is not True:
        issues.append("rework_current_gate_not_materialized")
    if summary.get("rework_required") is not True:
        issues.append("rework_required_not_true")
    if summary.get("final_package_selected") is not False:
        issues.append("summary_final_package_selected")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")
    if any(row.get("final_selection_allowed") is not False for row in audit_rows):
        issues.append("audit_row_allows_final_selection")
    if {row.get("severity") for row in issue_rows} != {"blocking_final_selection"}:
        issues.append("issue_severity_mismatch")

    for field in [
        "final_package_selected",
        "deployment_dossier_allowed",
        "live_execution_activation_allowed",
        "model_training_allowed",
        "broker_real_expectancy_claim_allowed",
    ]:
        if decision.get(field) is not False:
            issues.append(f"decision_boundary_not_false:{field}")
    if decision.get("accept_current_a_to_f_as_bounded_checkpoints") is not True:
        issues.append("bounded_checkpoint_acceptance_missing")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    if completion.get("verification", {}).get("wave_h_rework_after_final_selection") not in {"pending", "passed"}:
        issues.append("completion_verification_status_invalid")
    if len(decisions) < 2:
        issues.append("decision_rows_too_low")
    if len(repairs) < 2:
        issues.append("repair_rows_too_low")

    manifest_files = set(manifest.get("files") or [])
    for required in [
        "WAVE_H_REWORK_AFTER_FINAL_SELECTION_SUMMARY.json",
        "WAVE_H_REWORK_AUDIT_LEDGER.jsonl",
        "WAVE_H_REWORK_ISSUE_LEDGER.jsonl",
        "WAVE_H_REWORK_DECISION.json",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in manifest_files:
            issues.append(f"manifest_missing:{required}")

    result = {
        "schema": "gtos.final_moonshot.wave_h.rework_after_final_selection.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "audit_rows": len(audit_rows),
        "issue_rows": len(issue_rows),
        "blocking_issue_rows": len(issue_rows),
        "final_selection_gate_rows": summary.get("final_selection_gate_rows"),
        "final_selection_open_gate_rows": summary.get("final_selection_open_gate_rows"),
        "final_package_selected": summary.get("final_package_selected"),
        "rework_required": summary.get("rework_required"),
        "forbidden_surface_status": summary.get("forbidden_surface_status", {}),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    completion["verification"]["wave_h_rework_after_final_selection"] = "passed" if not issues else "failed"
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
