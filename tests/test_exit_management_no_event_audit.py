from __future__ import annotations

from src.research_infra.exit_management_no_event_audit import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_EVENTS,
    build_exit_management_status_rows,
    build_rolling_status,
)


def _candidate(**overrides):
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "created_at_utc": "2026-05-04T07:15:25+00:00",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "side": "SHORT",
        "framework": "ob_retest",
        "session": "london",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "final_outcome_at_log": "LIMIT_PLACED",
        "trade_id": None,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _pending(**overrides):
    row = {
        "schema_version": "pending_limit_lifecycle_join_backfill_v1",
        "row_key": "pending-row",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "source_row": {
            "fill_no_fill_label": "no_fill_cancelled",
            "intent_after_check": "manual_or_system_cancelled",
        },
    }
    row.update(overrides)
    return row


def _account(**overrides):
    row = {
        "schema_version": "account_truth_reconciliation_status_v1",
        "row_key": "account-row",
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "created_at_utc": "2026-05-05T00:00:00+00:00",
        "account_truth_status": "NO_REALIZED_ACCOUNT_HISTORY_FOR_CANDIDATE_OR_NOT_QUERIED_IN_CLOSURE",
        "actual_r_claim_allowed": False,
    }
    row.update(overrides)
    return row


def test_no_filled_trade_documents_empty_exit_management_lanes():
    rows = build_exit_management_status_rows(
        [(1, _candidate())],
        pending_rows=[(1, _pending())],
        account_rows=[(1, _account())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["exit_management_status"] == COMPLETE
    assert row["fill_state"] == "NO_FILLED_TRADE"
    assert row["be_shadow_status"] == "NO_FILLED_TRADE"
    assert row["partial_close_shadow_status"] == "NO_FILLED_TRADE"
    assert row["time_in_trade_shadow_status"] == "NO_FILLED_TRADE"
    assert row["documented_no_event_codes"] == [
        "NO_BE_TRIGGER",
        "NO_CLOSE_EVENT",
        "NO_FILLED_TRADE",
        "NO_PARTIAL_TRIGGER",
    ]
    assert row["event_rows_separate_from_status_rows"] is True
    assert row["no_ai_calls"] is True
    assert row["paid_data_calls"] == 0


def test_filled_trade_without_event_rows_is_action_required():
    rows = build_exit_management_status_rows(
        [(1, _candidate(trade_id="filled-1"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["exit_management_status"] == ACTION_REQUIRED
    assert row["fill_state"] == "FILLED_TRADE_OR_ACCOUNT_HISTORY_PRESENT"
    assert set(row["action_required_codes"]) == {
        "FILLED_TRADE_WITHOUT_BE_TRIGGER_STATUS_ROW",
        "FILLED_TRADE_WITHOUT_PARTIAL_TRIGGER_STATUS_ROW",
        "FILLED_TRADE_WITHOUT_TIME_IN_TRADE_ROW",
    }


def test_filled_trade_alias_joins_time_in_trade_and_documents_below_1r_no_trigger():
    rows = build_exit_management_status_rows(
        [(1, _candidate(trade_id="lim_GBPJPY_2026-05-11_073031"))],
        pending_rows=[
            (
                1,
                {
                    "schema_version": "pending_limit_lifecycle_v1",
                    "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
                    "trade_id": "lim_GBPJPY_2026-05-11_073031",
                    "trade_state_ticket": 237192029,
                    "fill_no_fill_label": "internal_filled_broker_ticket_known",
                    "intent_after_check": "order_send_success_filled",
                    "created_at_utc": "2026-05-11T10:45:05+00:00",
                },
            )
        ],
        broker_rows=[
            (
                1,
                {
                    "schema_version": "broker_actual_r_audit_v1",
                    "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
                    "trade_id": "lim_GBPJPY_2026-05-11_073031",
                    "accounting_evidence_class": "LIVE_R_ARTIFACT",
                    "actual_r_claim_allowed": False,
                    "created_at_utc": "2026-05-11T07:38:29+00:00",
                },
            ),
            (
                2,
                {
                    "schema_version": "broker_actual_r_audit_v1",
                    "fill_id": "GBPJPY_2026-05-11_london_0730",
                    "trade_id": "GBPJPY_2026-05-11_london_0730",
                    "ticket": 237192029,
                    "actual_r_claim_allowed": True,
                    "accounting_evidence_class": "ACCOUNT_HISTORY_REALIZED",
                    "created_at_utc": "2026-05-11T13:16:59+00:00",
                },
            )
        ],
        time_in_trade_rows=[
            (
                1,
                {
                    "trade_id": "GBPJPY_2026-05-11_london_0730",
                    "actual_close_r": 0.615,
                },
            )
        ],
        generated_at_utc="2026-05-11T13:20:00+00:00",
    )

    row = rows[0]
    assert row["exit_management_status"] == COMPLETE_WITH_EVENTS
    assert row["fill_state"] == "FILLED_TRADE_OR_ACCOUNT_HISTORY_PRESENT"
    assert row["time_in_trade_shadow_status"] == "EVENT_ROW_PRESENT"
    assert row["be_shadow_status"] == "NO_BE_TRIGGER_BELOW_1R_TIME_IN_TRADE"
    assert row["partial_close_shadow_status"] == "NO_PARTIAL_TRIGGER_BELOW_1R_TIME_IN_TRADE"
    assert row["time_in_trade_actual_close_r"] == 0.615
    assert row["action_required_codes"] == []


def test_trade_record_id_alias_joins_time_in_trade_without_account_history():
    rows = build_exit_management_status_rows(
        [
            (
                1,
                _candidate(
                    candidate_id="GBPJPY_2026-05-11T07:30:00+00:00",
                    symbol="GBPJPY",
                    session="london",
                    decision_time_utc="2026-05-11T07:30:00+00:00",
                    trade_id="lim_GBPJPY_2026-05-11_073031",
                ),
            )
        ],
        pending_rows=[
            (
                1,
                _pending(
                    candidate_id="GBPJPY_2026-05-11T07:30:00+00:00",
                    trade_id="lim_GBPJPY_2026-05-11_073031",
                    source_row={
                        "trade_id": "lim_GBPJPY_2026-05-11_073031",
                        "fill_no_fill_label": "internal_filled_broker_ticket_known",
                        "intent_after_check": "order_send_success_filled",
                    },
                ),
            )
        ],
        time_in_trade_rows=[
            (
                1,
                {
                    "trade_id": "GBPJPY_2026-05-11_london_0730",
                    "actual_close_r": 0.615,
                },
            )
        ],
        generated_at_utc="2026-05-11T13:20:00+00:00",
    )

    row = rows[0]
    assert row["exit_management_status"] == COMPLETE_WITH_EVENTS
    assert row["time_in_trade_shadow_status"] == "EVENT_ROW_PRESENT"
    assert row["be_shadow_status"] == "NO_BE_TRIGGER_BELOW_1R_TIME_IN_TRADE"
    assert row["partial_close_shadow_status"] == "NO_PARTIAL_TRIGGER_BELOW_1R_TIME_IN_TRADE"
    assert row["action_required_codes"] == []


def test_rolling_status_counts_no_event_codes():
    rows = build_exit_management_status_rows(
        [(1, _candidate()), (2, _candidate(candidate_id="NAS100_2026-05-04T13:15:00+00:00", symbol="NAS100"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    rolling = build_rolling_status(rows)

    assert rolling["rows"] == 2
    assert rolling["exit_management_status_counts"][COMPLETE] == 2
    assert rolling["documented_no_event_code_counts"]["NO_FILLED_TRADE"] == 2
