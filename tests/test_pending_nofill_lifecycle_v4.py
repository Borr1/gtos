import json
from pathlib import Path

from src.components.pending_limit_lifecycle_logger import (
    build_pending_limit_lifecycle_entry,
)
from src.components.pending_nofill_lifecycle_v4 import (
    build_lifecycle_v4_fields,
    build_risk_reservation,
    project_wave2_fixture_row,
)


WAVE2_PENDING_RECONCILIATION = Path(
    "research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/"
    "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl"
)


def test_source_repair_retry_is_not_reclassified_as_cancelled() -> None:
    row = build_pending_limit_lifecycle_entry(
        symbol="XAUUSD",
        side="LONG",
        trade_id="lim_XAUUSD_retry",
        entry_price=2400.0,
        stop_loss=2390.0,
        take_profit_1=2415.0,
        pending_created_time_utc="2026-06-04T08:00:00+00:00",
        checked_candle_time_utc="2026-06-04T08:15:00+00:00",
        intent_after_check="source_repair_failed_retry",
        trigger_condition_met=False,
        reason="malformed_ohlc_source_repair_failed",
    )

    assert row["intent_after_check"] == "source_repair_failed_retry"
    assert row["fill_no_fill_label"] == "no_fill_source_repair_failed_retry"
    assert row["pending_lifecycle_v4_state"] == "PENDING_ACTIVE_SOURCE_REPAIR_RETRY"
    assert row["pending_lifecycle_v4_terminal"] is False
    assert row["path_touch_ordering_status"] == "OHLC_SOURCE_REPAIR_FAILED_NO_TOUCH_CLAIM"


def test_risk_reservation_releases_on_terminal_no_fill() -> None:
    reservation = build_risk_reservation(
        account_balance=100000.0,
        risk_pct=0.5,
        broker_namespace="redacted_account:demo",
        symbol="XAUUSD",
        trade_id="lim_XAUUSD_cancel",
    )
    row = build_pending_limit_lifecycle_entry(
        symbol="XAUUSD",
        side="LONG",
        trade_id="lim_XAUUSD_cancel",
        entry_price=2400.0,
        stop_loss=2390.0,
        take_profit_1=2415.0,
        pending_created_time_utc="2026-06-04T08:00:00+00:00",
        checked_candle_time_utc="2026-06-04T08:15:00+00:00",
        intent_after_check="manual_or_system_cancelled",
        cancel_reason="test_cancel",
        **reservation,
    )

    assert row["risk_reserved_pct"] == 0.5
    assert row["risk_reserved_cash"] == 500.0
    assert row["risk_reservation_status"] == "RISK_RESERVATION_RELEASED_ON_TERMINAL_STATE"
    assert row["risk_reservation_release_reason"] == "manual_or_system_cancelled"


def test_filled_row_requires_broker_ticket_truth() -> None:
    row = build_pending_limit_lifecycle_entry(
        symbol="XAUUSD",
        side="LONG",
        trade_id="lim_XAUUSD_fill",
        entry_price=2400.0,
        stop_loss=2390.0,
        take_profit_1=2415.0,
        pending_created_time_utc="2026-06-04T08:00:00+00:00",
        checked_candle_time_utc="2026-06-04T08:15:00+00:00",
        intent_after_check="order_send_success_filled",
        trigger_condition_met=True,
        order_send_attempted=True,
        order_send_success=True,
        tick_bid=2399.8,
        tick_ask=2400.0,
        trade_state_ticket=123456,
        mt5_entry_order_ticket=123456,
    )

    assert row["broker_ticket_truth_status"] == "FILLED_MARKET_ORDER_TICKET_CAPTURED"
    assert row["pending_lifecycle_v4_state"] == "FILLED_MARKET_ORDER_ON_ENTRY_TOUCH"
    assert row["v4_source_completeness_status"] == "SOURCE_COMPLETE_FOR_TERMINAL_STATE"


def test_wave2_877_pending_rows_project_to_v4_fixture_shape() -> None:
    rows = [
        json.loads(line)
        for line in WAVE2_PENDING_RECONCILIATION.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    projected = [project_wave2_fixture_row(row) for row in rows]

    assert len(projected) == 877
    assert {row["pending_lifecycle_v4_schema_version"] for row in projected} == {
        "pending_nofill_lifecycle_v4"
    }
    assert all(row["wave2_source_row"]["row_id"] for row in projected)
    assert sum(1 for row in projected if row["pending_lifecycle_v4_terminal"]) == 88
    assert sum(
        1
        for row in projected
        if row["pending_lifecycle_v4_state"] == "PENDING_ACTIVE_NO_ENTRY_TOUCH"
    ) == 738
    assert all(
        row["result_use_status"]
        == "pending_nofill_lifecycle_source_reconciliation_not_broker_real_execution_truth"
        for row in projected
    )


def test_unknown_state_fails_closed_without_source_class_inflation() -> None:
    fields = build_lifecycle_v4_fields(
        {
            "intent_after_check": "surprise_state",
            "symbol": "XAUUSD",
            "side": "LONG",
            "trade_id": "lim_unknown",
            "entry_price": 2400.0,
            "stop_loss": 2390.0,
            "take_profit_1": 2415.0,
            "pending_created_time_utc": "2026-06-04T08:00:00+00:00",
            "checked_candle_time_utc": "2026-06-04T08:15:00+00:00",
        }
    )

    assert fields["pending_lifecycle_v4_state"] == "UNKNOWN_PENDING_LIFECYCLE_STATE"
    assert fields["pending_lifecycle_v4_transition_status"] == "UNKNOWN_TRANSITION_FAIL_CLOSED"
    assert fields["ftmo_no_copy_boundary"].endswith("DO_NOT_COPY_redacted_account_TO_FTMO")
