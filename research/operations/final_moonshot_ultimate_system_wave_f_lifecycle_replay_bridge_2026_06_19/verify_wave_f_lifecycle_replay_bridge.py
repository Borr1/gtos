#!/usr/bin/env python3
"""Verify Wave F lifecycle replay bridge artifacts."""

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
    comparable_existing = {key: value for key, value in existing.items() if key != "verified_utc"}
    comparable_result = {key: value for key, value in result.items() if key != "verified_utc"}
    if comparable_existing == comparable_result:
        return existing.get("verified_utc") or utc_now()
    return utc_now()


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json")
    bridge_rows = read_jsonl(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl")
    source_rows = read_jsonl(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SOURCE_SEARCH_LEDGER.jsonl")
    keyspace = read_json(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json")
    residuals = read_jsonl(ROUTE / "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl")
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

    if summary.get("status") != "wave_f_lifecycle_replay_bridge_checkpoint_not_final_selection":
        issues.append("summary_status_mismatch")
    if summary.get("input_label_rows") != 877 or len(bridge_rows) != 877:
        issues.append("bridge_row_count_mismatch")
    if summary.get("bridge_rows") != len(bridge_rows):
        issues.append("summary_bridge_rows_mismatch")
    if summary.get("unique_label_candidate_ids") != 92:
        issues.append("unique_label_candidate_count_mismatch")
    if summary.get("label_rows_with_decision_time") != 428:
        issues.append("label_decision_time_count_mismatch")
    if summary.get("wave_b_rows_scanned") != 214536:
        issues.append("wave_b_scan_count_mismatch")
    if summary.get("wave_c_rows_scanned") != 214536:
        issues.append("wave_c_scan_count_mismatch")
    for field in [
        "wave_b_exact_candidate_id_matches",
        "wave_c_exact_candidate_id_matches",
        "wave_b_symbol_side_time_matches",
        "wave_c_symbol_side_time_matches",
    ]:
        if summary.get(field) != 0:
            issues.append(f"unexpected_join_count:{field}")
    if summary.get("wave_b_max_time_utc") != "2026-05-01T23:45:00+00:00":
        issues.append("wave_b_max_time_mismatch")
    if summary.get("wave_c_max_time_utc") != "2026-05-01T23:45:00+00:00":
        issues.append("wave_c_max_time_mismatch")
    if summary.get("alternate_historical_owner_candidate_ids", 0) <= 0:
        issues.append("alternate_historical_owner_candidate_ids_not_positive")
    if summary.get("alternate_historical_owner_label_rows", 0) <= 0:
        issues.append("alternate_historical_owner_label_rows_not_positive")
    if summary.get("wfb003_status") != "zero_join_exclusion_recorded_current_wave_b_c_universe_not_closed":
        issues.append("wfb003_status_mismatch")
    if summary.get("wfb011_status") != "open_exact_replay_extension_or_namespace_bridge_requirement":
        issues.append("wfb011_status_mismatch")
    terminal = summary.get("terminal_decision", {})
    if terminal.get("lifecycle_bridge_complete_for_current_wave_b_c_universe") is not True:
        issues.append("bridge_current_universe_not_complete")
    for field in [
        "row_bound_fillability_complete_for_selected_package",
        "final_package_selected",
        "model_training_allowed",
        "deployment_dossier_allowed",
        "live_execution_activation_allowed",
        "wave_f_complete",
    ]:
        if terminal.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")

    if keyspace.get("bridge_conclusion", {}).get("current_wave_b_c_replay_denominator_backfilled") is not False:
        issues.append("keyspace_backfilled_current_denominator")
    if keyspace.get("wave_b_keyspace", {}).get("candidate_prefix_counts", {}).get("cand") != 214536:
        issues.append("wave_b_candidate_prefix_not_cand")
    if keyspace.get("wave_c_keyspace", {}).get("candidate_prefix_counts", {}).get("cand") != 214536:
        issues.append("wave_c_candidate_prefix_not_cand")
    if keyspace.get("label_keyspace", {}).get("candidate_prefix_counts", {}).get("NAS100", 0) <= 0:
        issues.append("label_keyspace_missing_runtime_prefixes")
    if any(row.get("wave_b_direct_candidate_id_join") for row in bridge_rows):
        issues.append("bridge_row_has_wave_b_direct_join")
    if any(row.get("wave_c_direct_candidate_id_join") for row in bridge_rows):
        issues.append("bridge_row_has_wave_c_direct_join")
    if any(row.get("wave_b_symbol_side_time_join") for row in bridge_rows):
        issues.append("bridge_row_has_wave_b_symbol_side_time_join")
    if any(row.get("wave_c_symbol_side_time_join") for row in bridge_rows):
        issues.append("bridge_row_has_wave_c_symbol_side_time_join")
    if not all(row.get("final_package_selection_allowed") is False for row in bridge_rows):
        issues.append("bridge_row_allows_final_selection")
    if not any(row.get("alternate_historical_owner_found") is True for row in bridge_rows):
        issues.append("no_bridge_row_records_alternate_owner")
    if not any(row.get("source_id") == "wave_b_candidate_replay_materialization" and row.get("rows_scanned") == 214536 for row in source_rows):
        issues.append("missing_wave_b_source_search_row")
    if not any(row.get("source_id") == "wave_c_no_fill_opportunity_cost" and row.get("rows_scanned") == 214536 for row in source_rows):
        issues.append("missing_wave_c_source_search_row")
    if not any(str(row.get("source_id", "")).startswith("main_orch24:") and row.get("matched_rows", 0) > 0 for row in source_rows):
        issues.append("missing_main_orch24_match_source_row")

    residual_by_id = {row.get("blocker_id"): row for row in residuals}
    if residual_by_id.get("WFB003", {}).get("status") != summary.get("wfb003_status"):
        issues.append("wfb003_residual_status_mismatch")
    if residual_by_id.get("WFB011", {}).get("status") != summary.get("wfb011_status"):
        issues.append("wfb011_residual_status_mismatch")
    if len(decisions) < 3:
        issues.append("decision_rows_too_low")
    if len(repairs) < 3:
        issues.append("repair_rows_too_low")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    manifest_files = set(manifest.get("files") or [])
    for required in [
        "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
        "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl",
        "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SOURCE_SEARCH_LEDGER.jsonl",
        "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json",
        "WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "VERIFICATION_RESULT.json",
    ]:
        if required not in manifest_files:
            issues.append(f"manifest_missing:{required}")

    waves = {row.get("wave"): row for row in parent_board.get("waves", [])}
    if waves.get("F", {}).get("status") != "lifecycle_replay_bridge_checkpoint_final_selection_still_blocked":
        issues.append("parent_wave_f_status_mismatch")
    if waves.get("G", {}).get("status") != "blocked_by_no_selected_final_package":
        issues.append("parent_wave_g_status_mismatch")
    if parent_questions.get("PQ019", {}).get("status") != "answered_lifecycle_replay_bridge_checkpoint":
        issues.append("parent_pq019_missing")
    if parent_sources.get("PSR019", {}).get("status") != "completed_zero_join_exclusion_recorded_remaining_replay_extension_required":
        issues.append("parent_psr019_missing")
    if parent_merges.get("PMD018", {}).get("status") != "selected":
        issues.append("parent_pmd018_missing")
    if parent_audit.get("verification", {}).get("wave_f_lifecycle_replay_bridge") != "passed":
        issues.append("parent_completion_audit_not_updated")
    linked = set(parent_manifest.get("linked_child_or_checkpoint_artifacts") or [])
    route_rel = str(ROUTE.relative_to(ROOT))
    for artifact in [
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SUMMARY.json",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_SOURCE_SEARCH_LEDGER.jsonl",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_KEYSPACE_AUDIT.json",
        f"{route_rel}/WAVE_F_LIFECYCLE_REPLAY_BRIDGE_RESIDUAL_BLOCKER_LEDGER.jsonl",
        f"{route_rel}/VERIFICATION_RESULT.json",
    ]:
        if artifact not in linked:
            issues.append(f"parent_manifest_missing:{artifact}")

    result = {
        "schema": "gtos.final_moonshot.wave_f.lifecycle_replay_bridge.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "bridge_rows": len(bridge_rows),
        "wave_b_rows_scanned": summary.get("wave_b_rows_scanned"),
        "wave_c_rows_scanned": summary.get("wave_c_rows_scanned"),
        "wave_b_exact_candidate_id_matches": summary.get("wave_b_exact_candidate_id_matches"),
        "wave_c_exact_candidate_id_matches": summary.get("wave_c_exact_candidate_id_matches"),
        "wave_b_symbol_side_time_matches": summary.get("wave_b_symbol_side_time_matches"),
        "wave_c_symbol_side_time_matches": summary.get("wave_c_symbol_side_time_matches"),
        "alternate_historical_owner_candidate_ids": summary.get("alternate_historical_owner_candidate_ids"),
        "alternate_historical_owner_label_rows": summary.get("alternate_historical_owner_label_rows"),
        "wfb003_status": summary.get("wfb003_status"),
        "wfb011_status": summary.get("wfb011_status"),
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
