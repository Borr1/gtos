#!/usr/bin/env python3
"""Verify the no-top-N final-package synthesis checkpoint."""

from __future__ import annotations

import json
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


def close_enough(actual: float, expected: float, tolerance: float = 1e-6) -> bool:
    return abs(float(actual) - expected) <= tolerance


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "FINAL_PACKAGE_SYNTHESIS_SUMMARY.json")
    source_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_SYNTHESIS_SOURCE_LEDGER.jsonl")
    axis_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_AXIS_SCORE_LEDGER.jsonl")
    shortlist_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_CANDIDATE_SHORTLIST_LEDGER.jsonl")
    split_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_SPLIT_STRESS_LEDGER.jsonl")
    concentration_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_CONCENTRATION_CONTROL_LEDGER.jsonl")
    successor_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_SUCCESSOR_PRIMITIVE_LEDGER.jsonl")
    residual_rows = read_jsonl(ROUTE / "FINAL_PACKAGE_RESIDUAL_GATE_LEDGER.jsonl")
    decisions = read_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")

    if summary.get("status") != "candidate_final_package_synthesis_checkpoint_not_final_selection":
        issues.append("summary_status_mismatch")
    if summary.get("selector_candidate_rows") != 289928:
        issues.append("selector_candidate_rows_mismatch")
    if summary.get("selector_positive_lift_rows") != 251273:
        issues.append("selector_positive_lift_rows_mismatch")
    if summary.get("candidate_level_rows") != 38863:
        issues.append("candidate_level_rows_mismatch")
    if not close_enough(summary.get("candidate_level_source_bound_r_sum"), 285719.394083207):
        issues.append("candidate_level_source_bound_r_sum_mismatch")
    if summary.get("scheduler_rows") != 179575:
        issues.append("scheduler_rows_mismatch")
    if not close_enough(summary.get("scheduler_result_r_sum"), 237632.550316219):
        issues.append("scheduler_result_r_sum_mismatch")
    if summary.get("axis_score_rows") != len(axis_rows):
        issues.append("axis_score_rows_mismatch")
    if summary.get("candidate_package_shortlist_rows") != len(shortlist_rows):
        issues.append("shortlist_rows_mismatch")
    if len(axis_rows) != len(shortlist_rows):
        issues.append("top_n_or_shortlist_truncation_detected")
    if summary.get("split_stress_rows") != len(split_rows):
        issues.append("split_stress_rows_mismatch")
    if summary.get("concentration_rows") != len(concentration_rows):
        issues.append("concentration_rows_mismatch")
    if summary.get("successor_primitive_rows") != len(successor_rows):
        issues.append("successor_rows_mismatch")
    if summary.get("residual_gate_rows") != len(residual_rows) or len(residual_rows) != 4:
        issues.append("residual_gate_rows_mismatch")
    if len(source_rows) != 4:
        issues.append("source_rows_mismatch")
    if len(decisions) < 3:
        issues.append("decision_rows_too_low")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")
    terminal = summary.get("terminal_decision", {})
    if terminal.get("candidate_final_package_shortlist_materialized") is not True:
        issues.append("shortlist_not_materialized")
    if terminal.get("broker_actual_r_is_edge_source") is not False:
        issues.append("broker_r_treated_as_edge_source")
    for field in [
        "broker_actual_r_claim_allowed",
        "deployment_dossier_allowed",
        "final_package_selected",
        "live_execution_activation_allowed",
        "model_training_allowed",
    ]:
        if terminal.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")
    if not any(row.get("disposition") == "promote_default_off_package_candidate" for row in axis_rows):
        issues.append("missing_promote_default_off_disposition")
    if not any(row.get("disposition") == "merge_with_scheduler_lifecycle_controls" for row in axis_rows):
        issues.append("missing_merge_disposition")
    if not any(row.get("disposition") == "redesign_or_source_repair_candidate" for row in axis_rows):
        issues.append("missing_redesign_disposition")
    if not any(row.get("disposition") == "avoid_or_preserve_as_failure_feature" for row in axis_rows):
        issues.append("missing_avoid_disposition")
    manifest_files = set(manifest.get("files") or [])
    for required in [
        "FINAL_PACKAGE_SYNTHESIS_SUMMARY.json",
        "FINAL_PACKAGE_AXIS_SCORE_LEDGER.jsonl",
        "FINAL_PACKAGE_CANDIDATE_SHORTLIST_LEDGER.jsonl",
        "FINAL_PACKAGE_SPLIT_STRESS_LEDGER.jsonl",
        "FINAL_PACKAGE_CONCENTRATION_CONTROL_LEDGER.jsonl",
        "FINAL_PACKAGE_RESIDUAL_GATE_LEDGER.jsonl",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in manifest_files:
            issues.append(f"manifest_missing:{required}")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")

    result = {
        "schema": "gtos.final_moonshot.final_package_synthesis.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "selector_candidate_rows": summary.get("selector_candidate_rows"),
        "selector_positive_lift_rows": summary.get("selector_positive_lift_rows"),
        "candidate_level_source_bound_r_sum": summary.get("candidate_level_source_bound_r_sum"),
        "scheduler_result_r_sum": summary.get("scheduler_result_r_sum"),
        "axis_score_rows": len(axis_rows),
        "candidate_package_shortlist_rows": len(shortlist_rows),
        "residual_gate_rows": len(residual_rows),
        "final_package_selected": terminal.get("final_package_selected"),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json(ROUTE / "VERIFICATION_RESULT.json", result)
    completion["verification"]["final_package_synthesis"] = "passed" if not issues else "failed"
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
