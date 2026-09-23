from __future__ import annotations

from build_vnext_moonshot_lane09b_selector_scheduler_reconciliation import (
    EXPECTED_LANE09_CAPTURE_REQUIREMENT_ROWS,
    EXPECTED_LANE09_CLAUSE_ROWS,
    EXPECTED_LANE09_DISCOVERY_ROWS,
    EXPECTED_LANE09_MECHANISM_ROWS,
    EXPECTED_LANE09_ROW_EVIDENCE_ROWS,
    EXPECTED_LANE10_ACCEPTED_REDUCED_ROWS,
    EXPECTED_LANE10_ACCEPTED_ROWS,
    EXPECTED_LANE10_REJECT_ROWS,
    EXPECTED_LANE10_REPLAY_ROWS,
    OutcomeAggregate,
    build_joined_row,
    classify_reconciliation,
    recommendation_for_aggregate,
    requirement_key,
)


def test_lane09_and_lane10_terminal_counts_are_frozen_inputs():
    assert EXPECTED_LANE09_ROW_EVIDENCE_ROWS == 289_928
    assert EXPECTED_LANE09_DISCOVERY_ROWS == 21_052
    assert EXPECTED_LANE09_CLAUSE_ROWS == 9_808
    assert EXPECTED_LANE09_MECHANISM_ROWS == 43
    assert EXPECTED_LANE09_CAPTURE_REQUIREMENT_ROWS == 1_909
    assert EXPECTED_LANE10_REPLAY_ROWS == 289_928
    assert EXPECTED_LANE10_REJECT_ROWS == 215_495
    assert EXPECTED_LANE10_ACCEPTED_ROWS == 67_365
    assert EXPECTED_LANE10_ACCEPTED_REDUCED_ROWS == 7_068


def test_row_classification_distinguishes_scheduler_survival_and_false_positive():
    selector = {
        "source_row_id": "lane08_replay_000000001",
        "origin_family": "current_ob_retest",
        "path_class": "winner_reached_1r_or_better",
    }
    accepted = {"scheduler_decision": "ACCEPTED", "scheduler_reason": "accepted_money_risk_portfolio_exposure", "result_r": 1.5}
    losing = {"scheduler_decision": "ACCEPTED", "scheduler_reason": "accepted_money_risk_portfolio_exposure", "result_r": -1.0}

    assert classify_reconciliation(selector, accepted, "reduce") == "scheduler-survived"
    assert classify_reconciliation(selector, losing, "promote") == "selector-false-positive"


def test_row_classification_identifies_repairable_and_correct_blocks():
    selector = {"path_class": "loss_sl_or_stop_policy_exit"}
    positive_reject = {
        "scheduler_decision": "REJECTED",
        "scheduler_reason": "same_symbol_exposure_conflict_active_until_lifecycle_close",
        "result_r": 2.0,
    }
    negative_reject = {
        "scheduler_decision": "REJECTED",
        "scheduler_reason": "same_symbol_exposure_conflict_active_until_lifecycle_close",
        "result_r": -1.0,
    }

    assert classify_reconciliation(selector, positive_reject, "promote") == "scheduler-blocked-repairable"
    assert classify_reconciliation(selector, negative_reject, "promote") == "scheduler-blocked-correctly"


def test_source_gap_scheduler_reason_is_preserved():
    selector = {"path_class": "winner_reached_1r_or_better"}
    scheduler = {
        "scheduler_decision": "REJECTED",
        "scheduler_reason": "selected_cell_or_effective_risk_missing_nonpositive_stale_source_repair_required",
        "result_r": 3.0,
    }

    assert classify_reconciliation(selector, scheduler, "promote") == "source-gap"


def test_aggregate_recommendation_reduces_scheduler_constrained_promote():
    aggregate = OutcomeAggregate()
    aggregate.add(
        {
            "scheduler_decision": "REJECTED",
            "scheduler_reason": "same_symbol_exposure_conflict_active_until_lifecycle_close",
            "reconciliation_class": "scheduler-blocked-repairable",
            "risk_state": "same_symbol_conflict",
            "lane09_mechanism_decision": "promote",
            "result_r": 2.0,
        }
    )
    aggregate.add(
        {
            "scheduler_decision": "ACCEPTED",
            "scheduler_reason": "accepted_money_risk_portfolio_exposure",
            "reconciliation_class": "scheduler-survived",
            "risk_state": "accepted_full_risk",
            "lane09_mechanism_decision": "promote",
            "result_r": 0.5,
        }
    )

    refined, reason = recommendation_for_aggregate("promote", aggregate)

    assert refined == "reduce_risk"
    assert "scheduler_constrained" in reason


def test_requirement_key_normalizes_no_side_to_lane10_unknown_side():
    requirement = {
        "symbol": "AUDJPY",
        "framework": "NO_CANDIDATE",
        "side": "NO_SIDE",
        "replay_gap_reason_code": "NO_JOINED_LABEL_SOURCE_CURRENT_INPUTS",
        "repair_requirement_code": "RUN_OR_JOIN_MICROSCOPE_REPLAY_OR_READONLY_BROKER_LIFECYCLE_COST_SOURCE",
    }
    lane10_gap = dict(requirement)
    lane10_gap["side"] = "unknown_side"

    assert requirement_key(requirement) == requirement_key(lane10_gap)


def test_build_joined_row_uses_lane09_source_row_identity():
    selector = {
        "source_row_id": "lane08_replay_000000123",
        "candidate_id": "cand",
        "selected_row_id": "selected",
        "origin_family": "current_ob_retest",
        "path_class": "winner_reached_1r_or_better",
        "symbol": "XAUUSD",
    }
    scheduler = {
        "row_id": "lane08_replay_000000123",
        "scheduler_decision": "ACCEPTED",
        "scheduler_reason": "accepted_money_risk_portfolio_exposure",
        "risk_state": "accepted_full_risk",
        "result_r": 1.0,
    }

    joined = build_joined_row(selector, scheduler, {"mechanism_decision": "reduce"})

    assert joined["join_status"] == "joined_lane09_source_row_id_to_lane10_row_id"
    assert joined["source_row_id"] == joined["lane10_row_id"]
    assert joined["reconciliation_class"] == "scheduler-survived"
