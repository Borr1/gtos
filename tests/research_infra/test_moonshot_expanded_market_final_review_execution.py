from __future__ import annotations

from src.research_infra.moonshot_expanded_market_final_review_execution import (
    apply_final_review_overlay_to_rollups,
    compact_final_review_row,
    final_review_action,
    final_review_integrity_status,
    summarize_final_review_adjusted_rollups,
    summarize_final_review_rows,
)


def _final_review_row(**overrides):
    row = {
        "final_review_row_id": "FINAL-1",
        "input_deconcentration_row_id": "DECON-1",
        "input_final_branch_artifact_row_id": "ARTIFACT-1",
        "input_implementation_candidate_row_id": "IMPL-1",
        "artifact_family": "expanded_market_reduced_side_filter",
        "artifact_function_name": "final_expanded_market_reduced_surface_abc",
        "artifact_scope_sha256": "scope-sha",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "H4",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "market_gap_code",
        "selected_side": "LONG",
        "source_path": "data/historical_2026/XAUUSD_H4.csv",
        "source_file_sha256": "file-sha",
        "branch_local_code_expression": "row.get('symbol') == 'XAUUSD'",
        "capacity_blocking_dimensions": [],
        "capacity_selected_input": True,
        "base_selected_input": True,
        "final_review_evidence_status": "FINAL_REVIEW_EVIDENCE_COMPLETE",
        "final_review_evidence_rows": 5,
        "evidence_execution_rows_claimed": 5,
        "evidence_effective_n_sum": 180.0,
        "matched_effective_n_sum": 180.0,
        "deconcentration_score": 0.31,
        "final_review_score": 0.42,
        "max_capacity_utilization": 0.66,
        "row_average_selected_intrabar_cost_adjusted_simulated_r": 0.10,
        "recomputed_average_selected_intrabar_cost_adjusted_simulated_r": 0.10,
        "row_average_selected_minus_rejected_intrabar_cost_adjusted_r": 0.20,
        "recomputed_average_selected_minus_rejected_intrabar_cost_adjusted_r": 0.20,
        "average_selected_intrabar_cost_adjusted_recompute_delta": 0.0,
        "target_first_share": 0.5,
        "stop_first_share": 0.4,
        "target_first_minus_stop_first_share": 0.1,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL",
    }
    row.update(overrides)
    return row


def _implementation_candidate_row(**overrides):
    row = {
        "implementation_candidate_row_id": "IMPL-1",
        "input_reduced_surface_execution_row_id": "EXEC-1",
    }
    row.update(overrides)
    return row


def _main_candidate(**overrides):
    row = {
        "candidate_row_id": "MAIN-CAND-1",
        "source_reduced_surface_execution_row_id": "EXEC-1",
        "surface_scope_sha256": "scope-sha",
    }
    row.update(overrides)
    return row


def test_final_review_action_maps_implement_and_capacity_redesign():
    assert (
        final_review_action("IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL")
        == "KEEP_DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_CANDIDATE"
    )
    assert (
        final_review_action("REDESIGN_EXPANDED_MARKET_FINAL_REVIEW_CAPACITY_BLOCKED")
        == "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE"
    )


def test_integrity_requires_main_candidate_complete_evidence_and_zero_recompute_delta():
    assert final_review_integrity_status(_final_review_row(), _main_candidate()) == "FINAL_REVIEW_VERIFIED"
    assert (
        final_review_integrity_status(_final_review_row(average_selected_intrabar_cost_adjusted_recompute_delta=0.1), _main_candidate())
        == "FINAL_REVIEW_RECOMPUTE_REPAIR_REQUIRED"
    )
    assert final_review_integrity_status(_final_review_row(), None) == "FINAL_REVIEW_MAIN_CANDIDATE_BINDING_REPAIR_REQUIRED"


def test_compact_final_review_overlay_binds_main_candidate_and_disables_runtime_use():
    row = compact_final_review_row(
        _final_review_row(),
        _implementation_candidate_row(),
        _main_candidate(),
        final_review_source_artifact="final.jsonl",
        final_review_source_line_no=1,
        final_review_source_sha256="final-sha",
        implementation_candidate_source_artifact="impl.jsonl",
        implementation_candidate_source_line_no=2,
        implementation_candidate_source_sha256="impl-sha",
        output_row_id="OVERLAY-1",
    )

    assert row["main_candidate_row_id"] == "MAIN-CAND-1"
    assert row["source_input_reduced_surface_execution_row_id"] == "EXEC-1"
    assert row["main_compiler_final_review_action"] == "KEEP_DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_CANDIDATE"
    assert row["branch_local_candidate_status_after_final_review"] == "READY_DEFAULT_OFF_FINAL_REVIEW_CANDIDATE"
    assert row["runtime_candidate_use_permitted"] is False
    assert row["candidate_use_allowed_now"] is False
    assert row["replay_r_reference_counted_as_new_main_result"] is False
    assert row["research_boundary"]["runtime_candidate_use_permitted"] is False


def test_compact_capacity_blocked_row_preserves_redesign_status_and_summary_counts():
    row = compact_final_review_row(
        _final_review_row(
            keep_kill_redesign_implement_decision="REDESIGN_EXPANDED_MARKET_FINAL_REVIEW_CAPACITY_BLOCKED",
            capacity_blocking_dimensions=["source_component"],
        ),
        _implementation_candidate_row(),
        _main_candidate(),
        final_review_source_artifact="final.jsonl",
        final_review_source_line_no=1,
        final_review_source_sha256="final-sha",
        implementation_candidate_source_artifact="impl.jsonl",
        implementation_candidate_source_line_no=2,
        implementation_candidate_source_sha256="impl-sha",
        output_row_id="OVERLAY-1",
    )
    summary = summarize_final_review_rows([row])

    assert row["main_compiler_final_review_action"] == "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE"
    assert row["branch_local_candidate_status_after_final_review"] == "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CANDIDATE"
    assert row["capacity_blocking_dimensions"] == ["source_component"]
    assert summary["rows"] == 1
    assert summary["final_review_evidence_rows"] == 5
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_apply_final_review_overlay_to_rollups_marks_capacity_blocked_rows():
    final_overlay = compact_final_review_row(
        _final_review_row(
            keep_kill_redesign_implement_decision="REDESIGN_EXPANDED_MARKET_FINAL_REVIEW_CAPACITY_BLOCKED"
        ),
        _implementation_candidate_row(),
        _main_candidate(),
        final_review_source_artifact="final.jsonl",
        final_review_source_line_no=1,
        final_review_source_sha256="final-sha",
        implementation_candidate_source_artifact="impl.jsonl",
        implementation_candidate_source_line_no=2,
        implementation_candidate_source_sha256="impl-sha",
        output_row_id="OVERLAY-1",
    )
    adjusted = apply_final_review_overlay_to_rollups(
        [
            {
                "candidate_row_id": "MAIN-CAND-1",
                "event_registry_match_rows": 3,
                "expected_candidate_event_rows": 1,
                "duplicate_scope_event_match_rows": 2,
                "symbol": "XAUUSD",
                "market_timeframe": "H4",
                "source_component": "market_gap_code",
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "replay_r_reference_counted_as_new_main_result": False,
            }
        ],
        [final_overlay],
    )
    summary = summarize_final_review_adjusted_rollups(adjusted)

    assert adjusted[0]["final_review_overlay_bound"] is True
    assert adjusted[0]["final_review_adjusted_rollup_status"] == "DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN"
    assert adjusted[0]["main_compiler_final_review_action"] == "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE"
    assert summary["final_review_overlay_bound_rows"] == 1
    assert summary["event_registry_match_rows"] == 3
    assert summary["runtime_candidate_use_permitted_rows"] == 0
