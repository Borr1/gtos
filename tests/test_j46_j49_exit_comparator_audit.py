from __future__ import annotations

from src.research_infra.j46_j49_exit_comparator_audit import (
    CANDIDATE_NO_FILL_CONTEXT,
    CANDIDATE_PATH_SYNTHETIC_ONLY,
    FILLED_JOINED,
    FILLED_MISSING,
    build_j46_j49_exit_comparator_audit_rows,
    build_rolling_status,
)


def _j46(**overrides):
    row = {
        "fill_id": "NAS100_2026-04-29_ny_1500",
        "instrument": "NAS100",
        "direction": "LONG",
        "entry_time": "2026-04-29T15:15:05+00:00",
        "entry_price": 27100.36,
        "actual_close": {
            "exit_price": 26970.57,
            "exit_time": "2026-04-29T20:15:06+00:00",
            "exit_reason": "sl_hit",
            "realized_R": -1.0167,
        },
        "hypothetical_old": {
            "exit_price": 27109.02,
            "exit_reason": "old_open_at_actual_exit",
            "hypothetical_R": 0.0678,
        },
        "delta_r": -1.0845,
        "shadow_better": False,
        "policy_version": "j46_j49_v2_2026_04_28",
        "timestamp_logged": "2026-04-29T15:15:05+00:00",
    }
    row.update(overrides)
    return row


def _broker(**overrides):
    row = {
        "schema_version": "broker_actual_r_audit_v1",
        "row_key": "broker-row",
        "source_dependency_signature": "broker-source",
        "fill_id": "NAS100_2026-04-29_ny_1500",
        "trade_id": "NAS100_2026-04-29_ny_1500",
        "symbol": "NAS100",
        "broker_symbol": "NAS100",
        "decision_time_utc": "2026-04-29T15:15:05+00:00",
        "accounting_evidence_class": "ACCOUNT_HISTORY_REALIZED",
        "truth_lane": "ACCOUNT_HISTORY_REALIZED",
        "actual_r_claim_allowed": True,
        "broker_actual_r": -1.0167,
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "source_links": {"mt5_export_deal_id": 219032030},
    }
    row.update(overrides)
    return row


def _candidate(**overrides):
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "created_at_utc": "2026-05-04T17:00:24+00:00",
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "side": "LONG",
        "framework": "ob_retest",
        "session": "ny",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "final_outcome_at_log": "REJECTED_GATE1_SAFETY",
        "trade_id": None,
    }
    row.update(overrides)
    return row


def _path(**overrides):
    row = {
        "schema_version": "candidate_path_follow_v1",
        "created_at_utc": "2026-05-05T02:44:30+00:00",
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "side": "LONG",
        "framework": "ob_retest",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "asof_latest_candle_utc": "2026-05-05T02:30:00+00:00",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "path_ambiguity_status": "NO_ENTRY_TOUCH_TP_AREA_NOT_A_FILL",
        "trade_id": None,
    }
    row.update(overrides)
    return row


def test_filled_j46_row_joins_account_history_and_allows_actual_r():
    rows = build_j46_j49_exit_comparator_audit_rows(
        [(1, _j46())],
        broker_rows=[(1, _broker())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["j46_j49_exit_comparator_status"] == FILLED_JOINED
    assert row["actual_r_claim_allowed"] is True
    assert row["broker_actual_r"] == -1.0167
    assert row["broker_actual_r_evidence_class"] == "ACCOUNT_HISTORY_REALIZED"
    assert row["hypothetical_old_r"] == 0.0678
    assert row["ml_label_eligibility"] == "ELIGIBLE_ACCOUNT_HISTORY_REALIZED_LABEL_AFTER_TARGET_REFRESH"
    assert row["ai_calls"] == 0
    assert row["order_calls"] == 0


def test_filled_j46_row_missing_broker_history_does_not_allow_actual_r():
    rows = build_j46_j49_exit_comparator_audit_rows(
        [(1, _j46())],
        broker_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["j46_j49_exit_comparator_status"] == FILLED_MISSING
    assert row["actual_r_claim_allowed"] is False
    assert row["broker_actual_r"] is None
    assert row["action_required_codes"] == ["FILLED_J46_ROW_WITHOUT_ACCOUNT_HISTORY_REALIZED_AUDIT"]
    assert row["ml_label_eligibility"] == "NOT_ELIGIBLE_ACTION_REQUIRED_OR_MISSING_ACCOUNT_HISTORY"


def test_no_fill_candidate_context_never_claims_actual_r():
    rows = build_j46_j49_exit_comparator_audit_rows(
        [],
        candidate_rows=[(1, _candidate())],
        path_rows=[(1, _path())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["j46_j49_exit_comparator_status"] == CANDIDATE_NO_FILL_CONTEXT
    assert row["row_type"] == "candidate_context"
    assert row["actual_r_claim_allowed"] is False
    assert row["broker_actual_r"] is None
    assert row["path_label"] == "continued_without_entry_touch_to_tp_area"
    assert row["ml_label_eligibility"] == "NO_ACTUAL_R_LABEL_NO_FILL_CONTEXT"


def test_entry_touched_path_context_is_synthetic_only_not_actual_r():
    rows = build_j46_j49_exit_comparator_audit_rows(
        [],
        candidate_rows=[(1, _candidate())],
        path_rows=[(1, _path(path_label="entry_touched_then_reached_tp1", touched_entry=True))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["j46_j49_exit_comparator_status"] == CANDIDATE_PATH_SYNTHETIC_ONLY
    assert row["actual_r_claim_allowed"] is False
    assert row["evidence_class"] == "SYNTHETIC_PATH_R"
    assert row["ml_label_eligibility"] == "SYNTHETIC_PATH_LABEL_ONLY_NOT_ACCOUNT_HISTORY_ACTUAL_R"


def test_row_key_is_stable_and_rolling_status_counts_ml_eligibility():
    rows_a = build_j46_j49_exit_comparator_audit_rows(
        [(1, _j46())],
        broker_rows=[(1, _broker())],
        candidate_rows=[(1, _candidate())],
        path_rows=[(1, _path())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )
    rows_b = build_j46_j49_exit_comparator_audit_rows(
        [(1, _j46())],
        broker_rows=[(1, _broker())],
        candidate_rows=[(1, _candidate())],
        path_rows=[(1, _path())],
        generated_at_utc="2026-05-05T01:00:00+00:00",
    )

    assert [row["row_key"] for row in rows_a] == [row["row_key"] for row in rows_b]
    rolling = build_rolling_status(rows_a)
    assert rolling["filled_comparator_rows"] == 1
    assert rolling["candidate_context_rows"] == 1
    assert rolling["actual_r_claim_allowed_rows"] == 1
