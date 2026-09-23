#!/usr/bin/env python3
"""Verify Wave F fillability label partial repair artifacts."""

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


def write_json(name: str, data: Any) -> None:
    (ROUTE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    issues: list[str] = []
    summary = read_json(ROUTE / "WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json")
    labels = read_jsonl(ROUTE / "WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl")
    join_rows = read_jsonl(ROUTE / "WAVE_F_FILLABILITY_WAVE_C_JOIN_ATTEMPT_LEDGER.jsonl")
    source_rows = read_jsonl(ROUTE / "WAVE_F_FILLABILITY_SOURCE_SEARCH_LEDGER.jsonl")
    residuals = read_jsonl(ROUTE / "WAVE_F_FILLABILITY_RESIDUAL_BLOCKER_LEDGER.jsonl")
    decisions = read_jsonl(ROUTE / "DECISION_LEDGER.jsonl")
    repairs = read_jsonl(ROUTE / "REPAIR_LEDGER.jsonl")
    parent_board = read_json(PARENT_ROUTE / "PARENT_WAVE_STATUS_BOARD.json")
    parent_manifest = read_json(PARENT_ROUTE / "PARENT_OUTPUT_MANIFEST.json")
    parent_questions = {
        row.get("question_id"): row
        for row in read_jsonl(PARENT_ROUTE / "PARENT_ACTIVE_QUESTION_STACK.jsonl")
    }
    parent_sources = {
        row.get("request_id"): row
        for row in read_jsonl(PARENT_ROUTE / "PARENT_SOURCE_REQUEST_LEDGER.jsonl")
    }
    parent_merges = {
        row.get("decision_id"): row
        for row in read_jsonl(PARENT_ROUTE / "PARENT_MERGE_DECISION_LEDGER.jsonl")
    }

    if summary.get("status") != "wave_f_fillability_label_repair_checkpoint_not_final_selection":
        issues.append("summary_status_mismatch")
    if summary.get("input_fixture_rows") != 877:
        issues.append("input_fixture_rows_mismatch")
    if summary.get("row_bound_fillability_label_rows") != 877:
        issues.append("label_rows_mismatch")
    if len(labels) != 877:
        issues.append("label_ledger_row_count_mismatch")
    if summary.get("rows_with_candidate_id", 0) <= 0:
        issues.append("candidate_id_rows_not_positive")
    if summary.get("rows_with_repaired_decision_time", 0) <= 0:
        issues.append("decision_time_rows_not_positive")
    join = summary.get("wave_c_join_attempt", {})
    if join.get("wave_c_no_fill_rows_scanned") != 214536:
        issues.append("wave_c_scan_count_mismatch")
    if join.get("wave_c_no_fill_rows_joined") != 0:
        issues.append("wave_c_join_unexpectedly_nonzero")
    if join.get("join_status") != "no_direct_wave_c_join_from_symbol_side_decision_time":
        issues.append("wave_c_join_status_mismatch")
    if summary.get("wfb003_status") != "partially_repaired_877_recoverable_pending_lifecycle_rows_materialized_zero_wave_c_replay_joins":
        issues.append("wfb003_status_mismatch")
    terminal = summary.get("terminal_decision", {})
    if terminal.get("row_bound_fillability_repair_complete_for_recoverable_fixture") is not True:
        issues.append("recoverable_fixture_not_marked_complete")
    for field in [
        "row_bound_fillability_repair_complete_for_wave_c_universe",
        "final_package_selected",
        "model_training_allowed",
        "deployment_dossier_allowed",
        "live_execution_activation_allowed",
    ]:
        if terminal.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")
    forbidden = summary.get("forbidden_surface_status", {})
    if any(value is not False for value in forbidden.values()):
        issues.append("forbidden_surface_crossed")
    latest_vps_guard = summary.get("latest_vps_guard", {})
    if latest_vps_guard.get("runtime_packet_rows") != 4006:
        issues.append("latest_vps_runtime_packet_rows_mismatch")
    if latest_vps_guard.get("pending_lifecycle_rows") != 877:
        issues.append("latest_vps_pending_lifecycle_rows_mismatch")
    if latest_vps_guard.get("slippage_rows") != 13:
        issues.append("latest_vps_slippage_rows_mismatch")
    if latest_vps_guard.get("trade_records_chronology_count") != 16:
        issues.append("latest_vps_trade_records_chronology_count_mismatch")
    if latest_vps_guard.get("trade_records_candidate_decision_policy_joinable") != 13:
        issues.append("latest_vps_candidate_decision_joinable_trade_records_mismatch")
    if latest_vps_guard.get("trade_records_broker_r_coverage_total") != 26:
        issues.append("latest_vps_broker_r_coverage_trade_records_mismatch")
    if latest_vps_guard.get("broker_lifecycle_rows") != 33:
        issues.append("latest_vps_broker_lifecycle_rows_mismatch")
    if latest_vps_guard.get("broker_actual_r_rows") != 0:
        issues.append("latest_vps_broker_actual_r_rows_unexpected")
    if latest_vps_guard.get("close_side_cost_rows") != 0:
        issues.append("latest_vps_close_side_cost_rows_unexpected")
    if latest_vps_guard.get("placement_capture_contract_present") is not True:
        issues.append("latest_vps_placement_capture_contract_missing")
    if not any(row.get("source_id") == "local_wave3_pending_nofill_fixture" and row.get("rows_read") == 877 for row in source_rows):
        issues.append("missing_local_fixture_source_row")
    if not any(row.get("source_id") == "vps_remote_pending_lifecycle_lfs_pointer" for row in source_rows):
        issues.append("missing_remote_pointer_source_row")
    if len(join_rows) != join.get("fixture_join_key_count"):
        issues.append("join_ledger_key_count_mismatch")
    if any(row.get("wave_c_no_fill_rows_joined") for row in join_rows):
        issues.append("join_ledger_contains_nonzero_join")
    residual_by_id = {row.get("blocker_id"): row for row in residuals}
    if residual_by_id.get("WFB003", {}).get("status") != summary.get("wfb003_status"):
        issues.append("residual_wfb003_status_mismatch")
    if len(decisions) < 3:
        issues.append("decision_rows_too_low")
    if len(repairs) < 3:
        issues.append("repair_rows_too_low")

    waves = {row.get("wave"): row for row in parent_board.get("waves", [])}
    if waves.get("F", {}).get("status") != "fillability_label_repair_checkpoint_final_selection_still_blocked":
        issues.append("parent_wave_f_status_mismatch")
    if waves.get("G", {}).get("status") != "blocked_by_no_selected_final_package":
        issues.append("parent_wave_g_not_blocked")
    if parent_questions.get("PQ017", {}).get("status") != "answered_fillability_label_repair_checkpoint":
        issues.append("missing_parent_question_pq017")
    if parent_sources.get("PSR008", {}).get("status") != "partial_fillability_label_repair_877_rows_remaining_replay_universe_unjoined":
        issues.append("parent_psr008_status_mismatch")
    if parent_merges.get("PMD016", {}).get("status") != "selected":
        issues.append("missing_parent_merge_pmd016")
    linked = set(parent_manifest.get("linked_child_or_checkpoint_artifacts") or [])
    for artifact in [
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_LABEL_REPAIR_SUMMARY.json",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_WAVE_C_JOIN_ATTEMPT_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_SOURCE_SEARCH_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/WAVE_F_FILLABILITY_RESIDUAL_BLOCKER_LEDGER.jsonl",
        "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19/VERIFICATION_RESULT.json",
    ]:
        if artifact not in linked:
            issues.append(f"parent_manifest_missing:{artifact}")

    result = {
        "schema": "gtos.final_moonshot.wave_f.fillability_label_repair.verification_result.v1",
        "verified_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "label_rows": len(labels),
        "wave_c_no_fill_rows_scanned": join.get("wave_c_no_fill_rows_scanned"),
        "wave_c_no_fill_rows_joined": join.get("wave_c_no_fill_rows_joined"),
        "wfb003_status": summary.get("wfb003_status"),
        "latest_vps_guard_head": latest_vps_guard.get("head"),
        "latest_vps_runtime_packet_rows": latest_vps_guard.get("runtime_packet_rows"),
        "latest_vps_trade_records_chronology_count": latest_vps_guard.get("trade_records_chronology_count"),
        "latest_vps_trade_records_broker_r_coverage_total": latest_vps_guard.get("trade_records_broker_r_coverage_total"),
        "final_package_selected": terminal.get("final_package_selected"),
        "model_training_allowed": terminal.get("model_training_allowed"),
        "forbidden_surface_status": forbidden,
    }
    write_json("VERIFICATION_RESULT.json", result)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
