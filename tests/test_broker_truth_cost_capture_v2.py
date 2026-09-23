from __future__ import annotations

from src.components.broker_truth_cost_capture_v2 import (
    build_lifecycle_row,
    iter_lifecycle_rows_from_readonly_export,
    record_lifecycle_event_if_enabled,
    readonly_export_source_manifest,
    spread_context_from_tick,
    stop_freeze_context_from_symbol_info,
    validate_lifecycle_row,
)
from src.mt5.mt5_interface import OrderResult, TickData

from datetime import datetime, timezone
from types import SimpleNamespace


def test_default_off_capture_does_not_write(tmp_path):
    path = tmp_path / "capture.jsonl"

    row = record_lifecycle_event_if_enabled(
        {"broker_truth_cost_capture_v2": {"enabled": False, "log_path": str(path)}},
        lifecycle_event_type="order_result",
        symbol="XAUUSD",
        source_family="unit_test",
        source_refs=["tests/test_broker_truth_cost_capture_v2.py"],
        result=OrderResult(
            retcode=10009,
            order=123,
            volume=0.01,
            price=2350.0,
            comment="done",
            deal=456,
        ),
    )

    assert row is None
    assert not path.exists()


def test_lifecycle_row_captures_ticket_result_spread_and_stop_freeze_context():
    tick = TickData(
        bid=2350.0,
        ask=2350.2,
        time=datetime(2026, 6, 1, tzinfo=timezone.utc),
        spread_cents=20.0,
    )
    symbol_info = SimpleNamespace(
        name="XAUUSD",
        trade_stops_level=50,
        trade_freeze_level=10,
        point=0.01,
        trade_tick_size=0.01,
        trade_tick_value=1.0,
    )
    result = OrderResult(
        retcode=10009,
        order=123,
        volume=0.01,
        price=2350.1,
        comment="done",
        deal=456,
        request_id=789,
        retcode_external=0,
    )

    row = build_lifecycle_row(
        lifecycle_event_type="order_result",
        symbol="XAUUSD",
        source_family="unit_test_broker_order_result",
        source_refs=["tests/test_broker_truth_cost_capture_v2.py"],
        result=result,
        spread_at_action=spread_context_from_tick(tick),
        stop_freeze_context=stop_freeze_context_from_symbol_info(symbol_info),
    )

    assert row["ticket_identity_status"] == "TICKET_BOUND"
    assert row["request_id"] == 789
    assert row["retcode_external"] == 0
    assert round(row["spread_at_action"]["spread_price"], 6) == 0.2
    assert row["stop_freeze_context"]["trade_freeze_level"] == 10
    assert row["validation_issues"] == []


def test_lifecycle_validator_fails_missing_ticket_identity_and_source():
    row = build_lifecycle_row(
        lifecycle_event_type="modify_result",
        symbol="XAUUSD",
        source_family="",
        source_refs=[],
    )

    issues = validate_lifecycle_row(row)

    assert "missing_source_family" in issues
    assert "missing_source_identity" in issues
    assert "ticket_bound_lifecycle_missing_ticket_order_deal_position_identity" in issues


def test_lifecycle_validator_fails_unmanaged_false_local_close():
    row = build_lifecycle_row(
        lifecycle_event_type="false_local_close",
        symbol="NAS100",
        source_family="unit_test",
        source_refs=["test"],
        ticket=123,
    )

    assert "false_local_close_missing_broker_contradiction_classification" in row["validation_issues"]


def test_lifecycle_validator_fails_cost_without_source_reason():
    row = build_lifecycle_row(
        lifecycle_event_type="cost",
        symbol="XAUUSD",
        source_family="unit_test_account_history",
        source_refs=["test"],
        deal_id=456,
        commission=-0.7,
        swap=0.0,
        broker_profit=-10.0,
    )

    assert "missing_cost_source_reason" in row["validation_issues"]


def test_lifecycle_validator_rejects_broker_real_proxy_confusion():
    row = build_lifecycle_row(
        lifecycle_event_type="cost",
        symbol="XAUUSD",
        source_family="proxy_projection_source",
        source_refs=["test"],
        deal_id=456,
        broker_real_or_proxy_state="BROKER_REAL",
        commission=-0.7,
        swap=0.0,
        broker_profit=-10.0,
        cost_source_reason="proxy projection cost reused",
    )

    assert "broker_real_row_uses_proxy_or_projection_source_family" in row["validation_issues"]
    assert "broker_real_cost_source_reason_uses_proxy_or_projection" in row["validation_issues"]


def test_readonly_export_parser_builds_broker_snapshot_rows(tmp_path):
    path = tmp_path / "history.jsonl"
    path.write_text(
        '{"deal":456,"order":123,"symbol":"XAUUSD","time":"2026-05-29T21:00:00Z",'
        '"volume":0.01,"price":2350.1,"commission":-0.7,"swap":0,"profit":12.5}\n',
        encoding="utf-8",
    )

    manifest = readonly_export_source_manifest(path, captured_asof_utc="2026-06-01T00:00:00Z")
    rows = list(iter_lifecycle_rows_from_readonly_export(path, source_capture_utc=manifest["captured_asof_utc"]))

    assert manifest["no_broker_access"] is True
    assert manifest["order_calls"] == 0
    assert manifest["nonempty_line_count"] == 1
    assert rows[0]["broker_real_or_proxy_state"] == "BROKER_READONLY_SNAPSHOT"
    assert rows[0]["ticket_identity_status"] == "TICKET_BOUND"
    assert rows[0]["deal_id"] == 456
    assert rows[0]["commission"] == -0.7
    assert rows[0]["cost_source_reason"] == "read_only_broker_history_export"
    assert rows[0]["validation_issues"] == []
