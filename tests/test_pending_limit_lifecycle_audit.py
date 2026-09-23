from __future__ import annotations

from pathlib import Path

from src.research_infra.pending_limit_lifecycle_audit import (
    ACTION_REQUIRED,
    COMPLETE_WITH_LIMITATIONS,
    build_pending_limit_lifecycle_audit_rows,
)
from src.research_infra.trade_record_candidate_backfill import TradeRecordCandidate


def _candidate(symbol: str = "XAUUSD", side: str = "SHORT", *, trade_id: str = "lim_2026-05-04_0715") -> dict:
    return {
        "candidate_id": f"{symbol}_2026-05-04T07:15:00+00:00",
        "created_at_utc": "2026-05-04T07:15:25+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "symbol": symbol,
        "broker_symbol": "NDX100" if symbol == "NAS100" else symbol,
        "source_symbol": None,
        "side": side,
        "framework": "ob_retest",
        "final_outcome_at_log": "LIMIT_PLACED",
        "trade_id": trade_id,
        "trade_parameters": {
            "direction": side,
            "entry_price": 100.0 if symbol == "XAUUSD" else 200.0,
            "stop_loss": 110.0 if side == "SHORT" else 190.0,
            "take_profit_1": 85.0 if side == "SHORT" else 215.0,
        },
    }


def _lifecycle(symbol: str = "XAUUSD", side: str = "SHORT", *, state: str = "still_pending_no_trigger", **overrides) -> dict:
    row = {
        "schema_version": "pending_limit_lifecycle_v1",
        "created_at_utc": "2026-05-04T07:30:05+00:00",
        "timestamp_utc": "2026-05-04T07:30:05+00:00",
        "symbol": symbol,
        "broker_symbol": "NDX100" if symbol == "NAS100" else symbol,
        "source_symbol": None,
        "candidate_id": None,
        "decision_time_utc": None,
        "trade_id": "lim_2026-05-04_0715",
        "side": side,
        "entry_price": 100.0 if symbol == "XAUUSD" else 200.0,
        "stop_loss": 110.0 if side == "SHORT" else 190.0,
        "take_profit_1": 85.0 if side == "SHORT" else 215.0,
        "pending_created_time_utc": "2026-05-04T07:15:25+00:00",
        "checked_candle_time_utc": "2026-05-04T07:30:00+00:00",
        "intent_after_check": state,
        "fill_no_fill_label": "no_fill_still_pending",
        "broker_fill_state": "not_filled",
        "order_send_attempted": False,
        "order_send_success": False,
        "check_context": "inside_kz",
    }
    if state == "cancelled_wrong_side":
        row.update(
            {
                "fill_no_fill_label": "no_fill_cancelled_wrong_side",
                "cancel_reason": "price_beyond_sl",
                "reason": "price_beyond_sl",
                "wrong_side_abort": True,
            }
        )
    row.update(overrides)
    return row


def _path(symbol: str = "XAUUSD", side: str = "SHORT", *, label: str = "continued_without_entry_touch_to_tp_area") -> dict:
    candidate = _candidate(symbol, side)
    return {
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "symbol": symbol,
        "broker_symbol": candidate["broker_symbol"],
        "decision_time_utc": candidate["decision_time_utc"],
        "side": side,
        "framework": "ob_retest",
        "path_label": label,
        "trade_parameters": candidate["trade_parameters"],
    }


def _trade_record_candidate(symbol: str = "XAUUSD", side: str = "SHORT") -> TradeRecordCandidate:
    candidate = _candidate(symbol, side)
    record = {
        "metadata": {
            "symbol": symbol,
            "candle_close_utc": candidate["decision_time_utc"],
            "kill_zone": "london",
        },
        "decision_pipeline": {"final_outcome": "LIMIT_PLACED"},
        "ai_response": {"trade_parameters": candidate["trade_parameters"]},
        "execution": None,
        "pending_lifecycle": None,
        "limit_intent": {
            "trade_id": candidate["trade_id"],
            "limit_price": candidate["trade_parameters"]["entry_price"],
            "stop_loss": candidate["trade_parameters"]["stop_loss"],
            "take_profit_1": candidate["trade_parameters"]["take_profit_1"],
        },
    }
    return TradeRecordCandidate(
        path=Path(f"knowledge_base/trade_records/{symbol}/2026-05-04_london_0715.json"),
        record=record,
        candidate_id=candidate["candidate_id"],
        symbol=symbol,
        broker_symbol=candidate["broker_symbol"],
        decision_time_utc=candidate["decision_time_utc"],
        kill_zone="london",
        side=side,
        framework="ob_retest",
        final_outcome="LIMIT_PLACED",
        trade_parameters=candidate["trade_parameters"],
    )


def test_lifecycle_audit_disambiguates_cross_symbol_trade_id_collision():
    xau = _candidate("XAUUSD", "SHORT")
    nas = _candidate("NAS100", "LONG")
    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, xau), (2, nas)],
        [(1, _lifecycle("XAUUSD", "SHORT")), (2, _lifecycle("NAS100", "LONG"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    by_symbol = {row["symbol"]: row for row in rows}
    assert by_symbol["XAUUSD"]["candidate_id"] == xau["candidate_id"]
    assert by_symbol["NAS100"]["candidate_id"] == nas["candidate_id"]
    assert by_symbol["XAUUSD"]["pending_intent_global_key"] != by_symbol["NAS100"]["pending_intent_global_key"]
    assert by_symbol["XAUUSD"]["trade_id_global_uniqueness_status"] == "LEGACY_COLLIDES_ACROSS_SYMBOLS"
    assert "LEGACY_RAW_TRADE_ID_NOT_GLOBALLY_UNIQUE" in by_symbol["XAUUSD"]["documented_limitation_codes"]


def test_lifecycle_audit_marks_no_fill_tp_area_reached_without_entry_touch():
    candidate = _candidate()
    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, candidate)],
        [(1, _lifecycle())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        path_rows=[(1, _path())],
        persisted_pending_intents=[
            {
                "symbol": "XAUUSD",
                "trade_id": "lim_2026-05-04_0715",
                "side": "SHORT",
                "entry_price": 100.0,
                "stop_loss": 110.0,
                "take_profit_1": 85.0,
                "source_path": "knowledge_base/meta/pending_intent_XAUUSD.pkl",
            }
        ],
    )

    assert rows[0]["missed_move_classification"] == "NO_FILL_TP_AREA_REACHED_WITHOUT_LIMIT_TOUCH"
    assert rows[0]["final_state"] == "NO_FILL_STILL_PENDING"
    assert rows[0]["persisted_pending_intent_status"] == "MATCHED_ACTIVE_PERSISTED_INTENT"


def test_lifecycle_audit_accepts_wrong_side_cancel_with_reason():
    candidate = _candidate()
    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, candidate)],
        [(1, _lifecycle(state="cancelled_wrong_side"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["pending_limit_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert rows[0]["final_state"] == "NO_FILL_CANCELLED_WRONG_SIDE"
    assert rows[0]["required_field_statuses"]["cancel_reason"] == "RAW_CAPTURED"


def test_lifecycle_audit_accepts_target_reached_without_fill_cancel():
    candidate = _candidate()
    lifecycle = _lifecycle(
        state="cancelled_target_reached_without_fill",
        fill_no_fill_label="no_fill_cancelled_target_reached_without_entry_touch",
        reason="target_reached_without_entry_touch",
    )

    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, candidate)],
        [(1, lifecycle)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["pending_limit_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert rows[0]["final_state"] == "NO_FILL_CANCELLED_TARGET_REACHED_WITHOUT_ENTRY_TOUCH"
    assert rows[0]["required_field_statuses"]["cancel_reason"] == "RAW_CAPTURED"


def test_lifecycle_audit_flags_active_pending_without_persisted_intent():
    candidate = _candidate()
    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, candidate)],
        [(1, _lifecycle())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["pending_limit_lifecycle_audit_status"] == ACTION_REQUIRED
    assert "PERSISTED_PENDING_INTENT:ACTION_REQUIRED_ACTIVE_PENDING_INTENT_NOT_PERSISTED" in rows[0]["action_required_codes"]


def test_lifecycle_audit_documents_stale_internal_pending_without_broker_order():
    candidate = _candidate("NAS100", "LONG", trade_id="lim_NAS100_2026-05-07_071536")
    lifecycle = _lifecycle(
        "NAS100",
        "LONG",
        trade_id="lim_NAS100_2026-05-07_071536",
        pending_created_time_utc="2026-05-07T07:15:36.881731+00:00",
        pending_order_mode="INTERNAL_CANDLE_POLLED_INTENT",
        broker_pending_order_created=False,
        mt5_order_ticket=None,
        pending_ticket=None,
        trade_state_ticket=None,
    )

    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, candidate)],
        [(1, lifecycle)],
        generated_at_utc="2026-05-08T08:30:00+00:00",
    )

    assert rows[0]["pending_limit_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert (
        rows[0]["persisted_pending_intent_status"]
        == "DOCUMENTED_STALE_INTERNAL_INTENT_NOT_PERSISTED_NO_BROKER_ORDER"
    )
    assert "STALE_INTERNAL_PENDING_INTENT_NOT_PERSISTED_NO_BROKER_ORDER" in rows[0]["documented_limitation_codes"]
    assert "PERSISTED_PENDING_INTENT:ACTION_REQUIRED_ACTIVE_PENDING_INTENT_NOT_PERSISTED" not in rows[0]["action_required_codes"]


def test_lifecycle_audit_flags_broker_position_mismatch_status():
    candidate = _candidate()
    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, candidate)],
        [(1, _lifecycle(state="cancelled_wrong_side"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        account_truth_rows=[
            (
                1,
                {
                    "candidate_id": candidate["candidate_id"],
                    "created_at_utc": "2026-05-04T08:00:00+00:00",
                    "account_truth_status": "BROKER_POSITION_MISMATCH",
                    "actual_r_claim_allowed": False,
                },
            )
        ],
    )

    assert rows[0]["pending_limit_lifecycle_audit_status"] == ACTION_REQUIRED
    assert "BROKER_POSITION_MISMATCH_REPORTED_BY_ACCOUNT_TRUTH" in rows[0]["action_required_codes"]


def test_lifecycle_audit_recovers_trade_record_only_old_row():
    record = _trade_record_candidate()
    rows = build_pending_limit_lifecycle_audit_rows(
        [],
        [(1, _lifecycle())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        trade_record_candidates=[record],
    )

    assert rows[0]["candidate_id"] == record.candidate_id
    assert rows[0]["trade_record_match_status"] == "MATCHED_BY_LIMIT_INTENT_TRADE_ID_OR_SYMBOL_SIDE_PRICE_GEOMETRY"
    assert "LEGACY_LIFECYCLE_ROW_CANDIDATE_ID_NOT_CAPTURED_RECOVERED_FROM_TRADE_RECORD" in rows[0]["documented_limitation_codes"]


def test_lifecycle_audit_flags_limit_placed_source_without_lifecycle_group():
    candidate = _candidate()
    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, candidate)],
        [],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["pending_limit_lifecycle_audit_status"] == ACTION_REQUIRED
    assert rows[0]["final_state"] == "PENDING_LIFECYCLE_GROUP_MISSING"
    assert "LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP" in rows[0]["action_required_codes"]


def test_lifecycle_audit_documents_pre_logger_trade_record_only_gap():
    record = _trade_record_candidate()
    nas = _candidate("NAS100", "LONG")
    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, nas)],
        [(1, _lifecycle("NAS100", "LONG"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        trade_record_candidates=[record],
    )

    source_only = [row for row in rows if row["candidate_id"] == record.candidate_id][0]
    assert source_only["pending_limit_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert source_only["final_state"] == "LEGACY_PENDING_LIFECYCLE_TRUTH_UNRECOVERABLE"
    assert "LEGACY_SOURCE_PREDATES_PENDING_LIFECYCLE_LOGGER" in source_only["documented_limitation_codes"]
    assert not source_only["action_required_codes"]


def test_lifecycle_audit_recovers_source_only_trade_record_exit():
    record = _trade_record_candidate()
    record.record["exit"] = {"exit_time": "2026-05-04T08:00:00+00:00", "actual_r": 0.5}
    nas = _candidate("NAS100", "LONG")
    rows = build_pending_limit_lifecycle_audit_rows(
        [(1, nas)],
        [(1, _lifecycle("NAS100", "LONG"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        trade_record_candidates=[record],
    )

    source_only = [row for row in rows if row["candidate_id"] == record.candidate_id][0]
    assert source_only["pending_limit_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert source_only["final_state"] == "TRADE_RECORD_EXIT_PRESENT_NO_LIFECYCLE_GROUP"
    assert (
        "PENDING_LIFECYCLE_GROUP_MISSING_RECOVERED_FROM_TRADE_RECORD_EXIT"
        in source_only["documented_limitation_codes"]
    )
    assert not source_only["action_required_codes"]


def test_lifecycle_audit_uses_event_time_when_fill_checked_candle_is_older():
    rows = build_pending_limit_lifecycle_audit_rows(
        [],
        [
            (
                1,
                _lifecycle(
                    "NAS100",
                    "SHORT",
                    candidate_id="broadorigin_b08a864b1bb511080487d03a",
                    checked_candle_time_utc="2026-05-29T14:29:00+00:00",
                    created_at_utc="2026-05-29T14:30:05.003373+00:00",
                    timestamp_utc="2026-05-29T14:30:05.003373+00:00",
                ),
            ),
            (
                2,
                _lifecycle(
                    "NAS100",
                    "SHORT",
                    state="order_send_success_filled",
                    candidate_id="broadorigin_b08a864b1bb511080487d03a",
                    checked_candle_time_utc="2026-05-29T14:15:00+00:00",
                    created_at_utc="2026-05-29T14:30:06.151361+00:00",
                    timestamp_utc="2026-05-29T14:30:06.151361+00:00",
                    fill_time_utc="2026-05-29T14:30:06.151322+00:00",
                    fill_no_fill_label="internal_filled_broker_ticket_known",
                    broker_fill_state="filled",
                    order_send_attempted=True,
                    order_send_success=True,
                    trade_state_ticket=241948220,
                ),
            ),
        ],
        generated_at_utc="2026-05-31T00:00:00+00:00",
    )

    assert len(rows) == 1
    assert rows[0]["final_state"] == "BROKER_FILLED_AWAITING_EXIT_OR_ACCOUNT_TRUTH"
    assert rows[0]["final_state_status"] == "BROKER_FILL_PENDING_EXIT_TRUTH"
    assert rows[0]["latest_lifecycle_intent_after_check"] == "order_send_success_filled"
