#!/usr/bin/env python3
"""Verify Wave F lifecycle denominator policy artifacts."""

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
    existing_path = ROUTE / "VERIFICATION_RESULT.json"
    if not existing_path.exists():
        return utc_now()
    try:
        existing = read_json(existing_path)
    except json.JSONDecodeError:
        return utc_now()
    old = {key: value for key, value in existing.items() if key != "verified_utc"}
    new = {key: value for key, value in result.items() if key != "verified_utc"}
    if old == new:
        return existing.get("verified_utc") or utc_now()
    return utc_now()


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json")
    policy_rows = read_jsonl(ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl")
    feasibility_rows = read_jsonl(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl")
    source_rows = read_jsonl(ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_SOURCE_LEDGER.jsonl")
    residuals = read_jsonl(ROUTE / "WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl")
    decisions = read_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    repairs = read_jsonl(ROUTE / "REPAIR_LEDGER.jsonl")
    completion = read_json(ROUTE / "COMPLETION_AUDIT.json")
    manifest = read_json(ROUTE / "OUTPUT_MANIFEST.json")
    parent_board = read_json(PARENT_ROUTE / "PARENT_WAVE_STATUS_BOARD.json")
    parent_audit = read_json(PARENT_ROUTE / "PARENT_COMPLETION_AUDIT.json")
    parent_manifest = read_json(PARENT_ROUTE / "PARENT_OUTPUT_MANIFEST.json")
    parent_questions = {row.get("question_id"): row for row in read_jsonl(PARENT_ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl")}
    parent_sources = {row.get("request_id"): row for row in read_jsonl(PARENT_ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl")}
    parent_merges = {row.get("decision_id"): row for row in read_jsonl(PARENT_ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl")}

    if summary.get("status") != "wave_f_lifecycle_denominator_policy_checkpoint_not_final_selection":
        issues.append("summary_status_mismatch")
    if summary.get("input_bridge_rows") != 877 or summary.get("policy_rows") != 877 or len(policy_rows) != 877:
        issues.append("policy_row_count_mismatch")
    if summary.get("excluded_from_current_denominator_rows") != 877:
        issues.append("excluded_row_count_mismatch")
    if summary.get("current_denominator_included_rows") != 0:
        issues.append("current_denominator_included_rows_nonzero")
    for field in ["wave_b_direct_joins", "wave_c_direct_joins", "wave_b_symbol_side_time_joins", "wave_c_symbol_side_time_joins"]:
        if summary.get(field) != 0:
            issues.append(f"unexpected_bridge_join:{field}")
    if summary.get("main_orch24_matched_candidate_ids") != 16:
        issues.append("main_orch24_candidate_id_count_mismatch")
    if summary.get("main_orch24_matched_rows", 0) <= 0:
        issues.append("main_orch24_matched_rows_not_positive")
    if summary.get("main_orch24_full_replay_geometry_rows") != 0:
        issues.append("main_orch24_full_replay_geometry_rows_nonzero")
    if summary.get("main_orch24_exact_r_rows") != 0:
        issues.append("main_orch24_exact_r_rows_nonzero")
    if len(feasibility_rows) != 16:
        issues.append("feasibility_candidate_row_count_mismatch")
    if any(row.get("extension_materializable_now") is not False for row in feasibility_rows):
        issues.append("feasibility_row_allows_extension")
    if any(row.get("full_replay_geometry_rows") != 0 for row in feasibility_rows):
        issues.append("feasibility_full_geometry_nonzero")
    if any(row.get("exact_r_rows") != 0 for row in feasibility_rows):
        issues.append("feasibility_exact_r_nonzero")
    if any(row.get("current_wave_b_c_denominator_joinable") is not False for row in policy_rows):
        issues.append("policy_row_denominator_joinable")
    if any(row.get("final_package_selection_allowed") is not False for row in policy_rows):
        issues.append("policy_row_allows_final_selection")
    if any(row.get("model_training_allowed") is not False for row in policy_rows):
        issues.append("policy_row_allows_training")
    if any(row.get("selected_package_denominator_policy") != "exclude_until_replay_extension_or_explicit_owner_override" for row in policy_rows):
        issues.append("policy_row_policy_mismatch")
    if not any(row.get("matched_lifecycle_candidate_rows", 0) > 0 for row in source_rows):
        issues.append("source_rows_have_no_matches")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")
    terminal = summary.get("terminal_decision", {})
    if terminal.get("current_denominator_policy_complete") is not True:
        issues.append("current_denominator_policy_not_complete")
    for field in [
        "lifecycle_labels_included_in_current_denominator",
        "selected_package_replay_extension_materializable_now",
        "final_package_selected",
        "model_training_allowed",
        "deployment_dossier_allowed",
        "live_execution_activation_allowed",
        "wave_f_complete",
    ]:
        if terminal.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")
    residual_by_id = {row.get("blocker_id"): row for row in residuals}
    if residual_by_id.get("WFB003", {}).get("status") != "current_denominator_exclusion_policy_complete_replay_extension_required":
        issues.append("wfb003_residual_status_mismatch")
    if residual_by_id.get("WFB002", {}).get("status") != "still_open_exact_capture_requirement":
        issues.append("wfb002_residual_status_mismatch")
    if len(decisions) < 2:
        issues.append("decision_rows_too_low")
    if len(repairs) < 2:
        issues.append("repair_rows_too_low")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    manifest_files = set(manifest.get("files") or [])
    for required in [
        "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json",
        "WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl",
        "WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl",
        "WAVE_F_LIFECYCLE_DENOMINATOR_SOURCE_LEDGER.jsonl",
        "WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in manifest_files:
            issues.append(f"manifest_missing:{required}")

    waves = {row.get("wave"): row for row in parent_board.get("waves", [])}
    if waves.get("F", {}).get("status") != "lifecycle_denominator_policy_checkpoint_final_selection_still_blocked":
        issues.append("parent_wave_f_status_mismatch")
    if waves.get("G", {}).get("status") != "blocked_by_no_selected_final_package":
        issues.append("parent_wave_g_status_mismatch")
    if parent_questions.get("PQ020", {}).get("status") != "answered_lifecycle_denominator_policy_checkpoint":
        issues.append("parent_pq020_missing")
    if parent_sources.get("PSR020", {}).get("status") != "completed_current_denominator_exclusion_policy_replay_extension_required":
        issues.append("parent_psr020_missing")
    if parent_merges.get("PMD019", {}).get("status") != "selected":
        issues.append("parent_pmd019_missing")
    if parent_audit.get("verification", {}).get("wave_f_lifecycle_denominator_policy") != "passed":
        issues.append("parent_completion_audit_not_updated")
    linked = set(parent_manifest.get("linked_child_or_checkpoint_artifacts") or [])
    route_rel = str(ROUTE.relative_to(ROOT))
    for artifact in [
        f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_SUMMARY.json",
        f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_POLICY_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_EXTENSION_FEASIBILITY_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_SOURCE_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_DENOMINATOR_RESIDUAL_BLOCKER_LEDGER.jsonl",
        f"{route_rel}/VERIFICATION_RESULT.json",
    ]:
        if artifact not in linked:
            issues.append(f"parent_manifest_missing:{artifact}")

    result = {
        "schema": "gtos.final_moonshot.wave_f.lifecycle_denominator_policy.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "policy_rows": len(policy_rows),
        "excluded_from_current_denominator_rows": summary.get("excluded_from_current_denominator_rows"),
        "main_orch24_matched_candidate_ids": summary.get("main_orch24_matched_candidate_ids"),
        "main_orch24_matched_rows": summary.get("main_orch24_matched_rows"),
        "main_orch24_full_replay_geometry_rows": summary.get("main_orch24_full_replay_geometry_rows"),
        "main_orch24_exact_r_rows": summary.get("main_orch24_exact_r_rows"),
        "final_package_selected": terminal.get("final_package_selected"),
        "model_training_allowed": terminal.get("model_training_allowed"),
        "forbidden_surface_status": summary.get("forbidden_surface_status", {}),
    }
    result["verified_utc"] = stable_verified_utc(result)
    write_json(ROUTE / "VERIFICATION_RESULT.json", result)
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
