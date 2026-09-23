#!/usr/bin/env python3
"""Verify final-package acceptance/compression artifacts."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def close_enough(actual: Any, expected: float, tolerance: float = 1e-6) -> bool:
    try:
        return abs(float(actual) - expected) <= tolerance
    except (TypeError, ValueError):
        return False


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
    return existing.get("verified_utc") or utc_now() if old == new else utc_now()


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_SUMMARY.json")
    source_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_ACCEPTANCE_SOURCE_LEDGER.jsonl")
    sleeve_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl")
    member_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl")
    overlap_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_OVERLAP_DEDUP_CONCENTRATION_LEDGER.jsonl")
    scheduler_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_SCHEDULER_LIFECYCLE_CONTROL_LEDGER.jsonl")
    stress_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_SPLIT_STRESS_ACCEPTANCE_LEDGER.jsonl")
    concentration_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_CONCENTRATION_ACCEPTANCE_LEDGER.jsonl")
    successor_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_SUCCESSOR_PRIMITIVE_ACCEPTANCE_LEDGER.jsonl")
    residual_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_ACCEPTANCE_RESIDUAL_GATE_LEDGER.jsonl")
    decisions = read_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")

    if summary.get("status") != "final_package_acceptance_compression_checkpoint_not_final_selection":
        issues.append("summary_status_mismatch")
    if summary.get("input_shortlist_rows") != 1101:
        issues.append("input_shortlist_rows_mismatch")
    if summary.get("sleeve_member_rows") != len(member_rows) or len(member_rows) != 1101:
        issues.append("member_rows_mismatch")
    if summary.get("package_sleeve_rows") != len(sleeve_rows) or len(sleeve_rows) != 82:
        issues.append("sleeve_rows_mismatch")
    if summary.get("overlap_dedup_rows") != len(overlap_rows) or len(overlap_rows) != 442:
        issues.append("overlap_rows_mismatch")
    if summary.get("concentration_control_rows") != len(concentration_rows) or len(concentration_rows) != 508:
        issues.append("concentration_rows_mismatch")
    if summary.get("scheduler_lifecycle_control_rows") != len(scheduler_rows) or len(scheduler_rows) != len(sleeve_rows):
        issues.append("scheduler_control_rows_mismatch")
    if summary.get("split_stress_leave_one_symbol_rows") != len(stress_rows) or len(stress_rows) != 87:
        issues.append("stress_rows_mismatch")
    if summary.get("successor_primitive_rows") != len(successor_rows) or len(successor_rows) != 20:
        issues.append("successor_rows_mismatch")
    if summary.get("residual_gate_rows") != len(residual_rows) or len(residual_rows) != 4:
        issues.append("residual_rows_mismatch")
    if len(source_rows) != 4:
        issues.append("source_rows_mismatch")
    if len(decisions) < 4:
        issues.append("decision_rows_too_low")
    if not close_enough(summary.get("input_candidate_level_source_bound_r_sum"), 285719.394083207):
        issues.append("input_candidate_level_r_sum_mismatch")
    if not close_enough(summary.get("input_scheduler_result_r_sum"), 237632.550316219):
        issues.append("input_scheduler_result_sum_mismatch")
    if not close_enough(summary.get("compressed_candidate_level_source_bound_r_sum"), 285719.394083207):
        issues.append("compressed_candidate_level_r_sum_mismatch")
    if not close_enough(summary.get("compressed_scheduler_result_r_sum"), 237632.550316219):
        issues.append("compressed_scheduler_result_sum_mismatch")
    if not close_enough(summary.get("compressed_selector_lift_sum"), 725896.086268238):
        issues.append("compressed_selector_lift_sum_mismatch")
    if not close_enough(summary.get("compressed_combined_source_bound_signal_r"), 1249248.030667):
        issues.append("compressed_combined_signal_mismatch")

    sleeve_type_counts = Counter(row.get("sleeve_type") for row in sleeve_rows)
    member_type_counts = Counter(row.get("sleeve_type") for row in member_rows)
    expected_sleeves = {
        "promote_default_off_signal_sleeve": 3,
        "scheduler_lifecycle_merge_sleeve": 20,
        "redesign_repair_sleeve": 24,
        "avoid_failure_feature_sleeve": 27,
        "source_required_hold_sleeve": 8,
    }
    expected_members = {
        "promote_default_off_signal_sleeve": 4,
        "scheduler_lifecycle_merge_sleeve": 707,
        "redesign_repair_sleeve": 144,
        "avoid_failure_feature_sleeve": 216,
        "source_required_hold_sleeve": 30,
    }
    if dict(sleeve_type_counts) != expected_sleeves:
        issues.append("sleeve_type_counts_mismatch")
    if dict(member_type_counts) != expected_members:
        issues.append("member_sleeve_type_counts_mismatch")
    if any(row.get("final_package_selection_allowed") is not False for row in sleeve_rows + member_rows):
        issues.append("selection_allowed_not_false")
    if any(row.get("broker_actual_r_role") != "calibration_only_not_edge_source" for row in sleeve_rows + member_rows):
        issues.append("broker_actual_r_role_mismatch")
    if not any(row.get("control_status") == "dedup_or_merge_required_before_execution" for row in overlap_rows):
        issues.append("missing_dedup_control_rows")
    if not any(row.get("control_status") == "mandatory_scheduler_lifecycle_controls" for row in scheduler_rows):
        issues.append("missing_scheduler_lifecycle_controls")
    if not any(row.get("source") == "hydrated_replay_lift_leave_one_symbol" for row in stress_rows):
        issues.append("missing_leave_one_symbol_stress")
    if not any(row.get("source_disposition") == "avoid_or_reduce_concentrated_cell" for row in concentration_rows):
        issues.append("missing_concentration_reduce_controls")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")
    terminal = summary.get("terminal_decision", {})
    if terminal.get("candidate_package_sleeves_materialized") is not True:
        issues.append("sleeves_not_materialized")
    for field in [
        "broker_actual_r_claim_allowed",
        "broker_actual_r_is_edge_source",
        "deployment_dossier_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
    ]:
        if terminal.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")
    manifest_files = set(manifest.get("files") or [])
    for required in [
        "FINAL_PACKAGE_ACCEPTANCE_COMPRESSION_SUMMARY.json",
        "FINAL_PACKAGE_SLEEVE_CANDIDATE_LEDGER.jsonl",
        "FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl",
        "FINAL_PACKAGE_OVERLAP_DEDUP_CONCENTRATION_LEDGER.jsonl",
        "FINAL_PACKAGE_SCHEDULER_LIFECYCLE_CONTROL_LEDGER.jsonl",
        "FINAL_PACKAGE_SPLIT_STRESS_ACCEPTANCE_LEDGER.jsonl",
        "FINAL_PACKAGE_CONCENTRATION_ACCEPTANCE_LEDGER.jsonl",
        "FINAL_PACKAGE_ACCEPTANCE_RESIDUAL_GATE_LEDGER.jsonl",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in manifest_files:
            issues.append(f"manifest_missing:{required}")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")

    result = {
        "schema": "gtos.final_moonshot.final_package_acceptance_compression.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "input_shortlist_rows": len(member_rows),
        "package_sleeve_rows": len(sleeve_rows),
        "overlap_dedup_rows": len(overlap_rows),
        "concentration_control_rows": len(concentration_rows),
        "scheduler_lifecycle_control_rows": len(scheduler_rows),
        "split_stress_leave_one_symbol_rows": len(stress_rows),
        "compressed_combined_source_bound_signal_r": summary.get("compressed_combined_source_bound_signal_r"),
        "compressed_candidate_level_source_bound_r_sum": summary.get("compressed_candidate_level_source_bound_r_sum"),
        "compressed_scheduler_result_r_sum": summary.get("compressed_scheduler_result_r_sum"),
        "final_package_selected": terminal.get("final_package_selected"),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    completion["verification"]["final_package_acceptance_compression"] = "passed" if not issues else "failed"
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
