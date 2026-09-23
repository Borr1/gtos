from __future__ import annotations

from datetime import datetime, timezone

from src.components.prop_firm_headroom_v4 import (
    build_prop_firm_headroom_snapshot_v4,
    build_prop_firm_headroom_snapshot_v4_from_account_state,
    evaluate_prop_firm_headroom_snapshot_v4,
)


def _snapshot(**overrides) -> dict:
    base = build_prop_firm_headroom_snapshot_v4(
        account_info={
            "login": "unit-account-login",
            "balance": 100500.0,
            "equity": 100500.0,
        },
        account_namespace="redacted_account_live_bee34003",
        day_start_equity_or_balance_baseline=100000.0,
        initial_equity_or_balance_baseline=100000.0,
        daily_loss_limit_pct=4.0,
        overall_loss_limit_pct=9.0,
        daily_reset_window_id="2026-06-06T00:00:00+00:00/redacted_account",
        now_utc=datetime(2026, 6, 6, 0, 0, tzinfo=timezone.utc),
    )
    base["max_allowed_new_trade_risk_pct"] = 0.5
    base["snapshot_hash_sha256"] = "a" * 64
    base.update(overrides)
    return base


def test_prop_firm_headroom_snapshot_allows_fresh_sufficient_broker_real_source():
    result = evaluate_prop_firm_headroom_snapshot_v4(
        snapshot=_snapshot(),
        requested_risk_pct=0.5,
        now_utc=datetime(2026, 6, 6, 0, 5, tzinfo=timezone.utc),
    )

    assert result.allowed is True
    assert result.reason == "source_bound_broker_real_headroom_sufficient"
    assert result.to_packet()["broker_runtime_change_status"] is False


def test_prop_firm_headroom_snapshot_blocks_insufficient_headroom():
    result = evaluate_prop_firm_headroom_snapshot_v4(
        snapshot=_snapshot(max_allowed_new_trade_risk_pct=0.25),
        requested_risk_pct=0.5,
        now_utc=datetime(2026, 6, 6, 0, 5, tzinfo=timezone.utc),
    )

    assert result.allowed is False
    assert result.reason == "snapshot_insufficient_headroom"
    assert result.max_allowed_new_trade_risk_pct == 0.25


def test_prop_firm_headroom_builder_hashes_account_and_computes_headroom():
    snapshot = build_prop_firm_headroom_snapshot_v4(
        account_info={"login": 0, "balance": 100000.0, "equity": 98500.0},
        account_namespace="redacted_account_live_bee34003",
        day_start_equity_or_balance_baseline=100000.0,
        daily_reset_window_id="2026-06-06/redacted_account",
        initial_equity_or_balance_baseline=100000.0,
        daily_loss_limit_pct=5.0,
        overall_loss_limit_pct=10.0,
        new_trade_buffer_pct=0.25,
        now_utc=datetime(2026, 6, 6, 0, 0, tzinfo=timezone.utc),
    )

    assert "login" not in snapshot
    assert len(snapshot["account_login_hash"]) == 64
    assert len(snapshot["source_event_hash_sha256"]) == 64
    assert len(snapshot["snapshot_hash_sha256"]) == 64
    assert snapshot["available_daily_loss_headroom_pct"] == 3.5
    assert snapshot["available_overall_loss_headroom_pct"] == 8.5
    assert snapshot["max_allowed_new_trade_risk_pct"] == 3.25


def test_prop_firm_headroom_account_state_adapter_is_read_only_and_source_bound():
    snapshot = build_prop_firm_headroom_snapshot_v4_from_account_state(
        {
            "schema_version": "prop_firm_headroom_account_state_v4",
            "account_namespace": "redacted_account_live_bee34003",
            "account_login": 0,
            "current_balance": 100000.0,
            "current_equity": 99000.0,
            "day_start_equity_or_balance_baseline": 100000.0,
            "initial_balance": 100000.0,
            "daily_loss_limit_pct": 5.0,
            "overall_loss_limit_pct": 10.0,
            "new_trade_buffer_pct": 0.25,
            "daily_reset_window_id": "2026-06-06/redacted_account",
        },
        now_utc=datetime(2026, 6, 6, 0, 0, tzinfo=timezone.utc),
    )

    assert snapshot["schema_version"] == "prop_firm_headroom_snapshot_v4"
    assert snapshot["source_status"] == "source_bound_broker_real_account_headroom"
    assert "account_login" not in snapshot
    assert len(snapshot["account_login_hash"]) == 64
    assert snapshot["broker_runtime_change_status"] is False
    assert snapshot["broker_order_mutation"] is False
    assert snapshot["available_daily_loss_headroom_pct"] == 4.0
    assert snapshot["max_allowed_new_trade_risk_pct"] == 3.75


def test_prop_firm_headroom_snapshot_requires_durable_hashes():
    snapshot = _snapshot()
    snapshot.pop("source_event_hash_sha256")

    result = evaluate_prop_firm_headroom_snapshot_v4(
        snapshot=snapshot,
        requested_risk_pct=0.5,
        now_utc=datetime(2026, 6, 6, 0, 5, tzinfo=timezone.utc),
    )

    assert result.allowed is False
    assert result.reason == "snapshot_incomplete"
    assert "source_event_hash_sha256" in result.missing_fields


def test_prop_firm_headroom_snapshot_blocks_configured_account_mismatch():
    result = evaluate_prop_firm_headroom_snapshot_v4(
        snapshot=_snapshot(account_namespace="ftmo_follower"),
        requested_risk_pct=0.5,
        config={
            "gtos_vnext_runtime": {
                "prop_firm_headroom_required_account_namespace": (
                    "redacted_account_live_bee34003"
                )
            }
        },
        now_utc=datetime(2026, 6, 6, 0, 5, tzinfo=timezone.utc),
    )

    assert result.allowed is False
    assert result.reason == "snapshot_incomplete"
    assert "account_namespace:configured_account_mismatch" in result.missing_fields
