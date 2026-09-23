from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = (
    ROOT
    / "research"
    / "operations"
    / "vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01"
    / "build_vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design.py"
)
SPEC = importlib.util.spec_from_file_location("lane10b_builder", BUILDER_PATH)
lane10b = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(lane10b)


def base_row(**overrides):
    row = {
        "row_id": "row_1",
        "selected_row_id": "sel_1",
        "candidate_id": "cand_1",
        "candidate_time_utc": "2022-01-01T10:00:00+00:00",
        "symbol": "XAUUSD",
        "side": "LONG",
        "scheduler_decision": "REJECTED",
        "scheduler_reason": "same_symbol_exposure_conflict_active_until_lifecycle_close",
        "requested_risk_pct": 1.0,
        "approved_risk_pct": 0.0,
        "account_available_risk_pct": 4.0,
        "dynamic_portfolio_ceiling_pct": 7.0,
        "total_risk_pct_before": 1.0,
        "correlated_cluster_risk_pct_before": 1.0,
        "current_equity": 101000.0,
        "day_start_baseline": 100000.0,
        "daily_cushion_before": 5000.0,
        "overall_cushion_before": 11000.0,
        "cost_buffer_pct": 0.1,
        "open_risk_pct_before": 1.0,
        "pending_risk_pct_before": 0.0,
        "same_symbol_risk_pct_before": 1.0,
        "same_symbol_conflict_ids": ["active_1"],
        "correlated_cluster_conflict_ids": [],
        "result_r": 1.2,
        "origin_family": "current_ob_retest",
        "session_bucket": "london_broad",
        "spread_r_bucket": "spread_or_cost_r_missing",
    }
    row.update(overrides)
    return row


def active_ticket(**overrides):
    row = {
        "selected_row_id": "active_1",
        "side": "LONG",
        "symbol": "XAUUSD",
        "risk_release_time_utc": "2022-01-01T11:00:00+00:00",
        "exit_time_utc": "2022-01-01T12:00:00+00:00",
    }
    row.update(overrides)
    return row


def classify(row, active):
    return lane10b.classify_scheduler_row(
        row,
        [active],
        [],
        [],
        {},
        {"mechanism_decision": "promote", "expectancy_r": 0.4},
    )


def test_opposite_side_same_symbol_stays_fail_closed():
    row = base_row(side="SHORT")
    result = classify(row, active_ticket(side="LONG"))

    assert result["correct_reject"] is True
    assert result["repairable_scheduler_block"] is False
    assert result["same_symbol_state"] == "same_symbol_opposite_side_active"
    assert "opposite_side_hedge_rejection_design" in result["branch_candidates"]


def test_same_side_risk_released_ticket_is_repairable():
    row = base_row(candidate_time_utc="2022-01-01T11:30:00+00:00")
    result = classify(
        row,
        active_ticket(
            side="LONG",
            risk_release_time_utc="2022-01-01T11:00:00+00:00",
            exit_time_utc="2022-01-01T12:00:00+00:00",
        ),
    )

    assert result["repairable_scheduler_block"] is True
    assert result["same_symbol_state"] == "same_symbol_same_side_active"
    assert result["same_symbol_release_state"] == "same_symbol_all_risk_released_lifecycle_active"
    assert "partial_be_risk_release" in result["branch_candidates"]
    assert "same_side_stacking_design" in result["branch_candidates"]


def test_missing_risk_is_correct_source_gap_not_scheduler_relaxation():
    row = base_row(
        scheduler_reason="selected_cell_or_effective_risk_missing_nonpositive_stale_source_repair_required",
        requested_risk_pct=0.0,
        result_r=2.0,
        same_symbol_conflict_ids=[],
    )
    result = lane10b.classify_scheduler_row(row, [], [], [], {}, {})

    assert result["correct_reject"] is True
    assert result["classification"] == "correct_fail_closed_source_risk_gap"
    assert result["v3_action"] == "source_repair_required_not_scheduler_relaxation"


def test_reduced_risk_action_records_haircut_missed_edge():
    row = base_row(
        scheduler_decision="ACCEPTED_REDUCED_RISK",
        scheduler_reason="accepted_reduced_risk_to_account_or_portfolio_budget",
        requested_risk_pct=1.0,
        approved_risk_pct=0.4,
        same_symbol_conflict_ids=[],
        result_r=2.0,
    )
    result = lane10b.classify_scheduler_row(row, [], [], [], {}, {})

    assert result["repairable_scheduler_block"] is True
    assert result["missed_edge_scope"] == "accepted_reduced_risk_haircut"
    assert result["missed_risk_pct"] == 0.6
    assert result["missed_result_r"] == 1.2


def test_required_v3_branches_are_declared():
    package = lane10b.build_scheduler_v3_package("2026-06-01T00:00:00+00:00", {})

    for branch in lane10b.REQUIRED_BRANCHES:
        assert branch in package["branch_names"]
    assert package["enabled_by_default"] is False
    assert "static count cap" in package["forbidden_authority"]
