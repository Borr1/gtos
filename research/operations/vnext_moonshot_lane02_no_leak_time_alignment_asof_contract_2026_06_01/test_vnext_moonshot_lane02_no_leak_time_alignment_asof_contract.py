from __future__ import annotations

from pathlib import Path

import build_vnext_moonshot_lane02_no_leak_time_alignment_asof_contract as builder
from vnext_lane02_time_contract import (
    candle_close_for,
    canonical_key,
    is_friday_close_risk,
    session_for_utc,
    validate_no_leak_row,
)


def test_feature_store_rejects_outcome_and_post_close_fields():
    result = validate_no_leak_row(
        {
            "candidate_time_utc": "2026-05-31T01:30:00Z",
            "exit_time_utc": "2026-05-31T02:18:16Z",
            "final_r": -1.0,
            "symbol": "XAUUSD",
        },
        context="feature_store",
        decision_time_utc="2026-05-31T01:30:00Z",
    )

    assert result["ok"] is False
    reasons = {issue["reason"] for issue in result["issues"]}
    assert "post_close_not_allowed_in_feature_store" in reasons
    assert "label_only_not_allowed_in_feature_store" in reasons


def test_feature_store_rejects_future_capture_timestamp():
    result = validate_no_leak_row(
        {
            "candidate_time_utc": "2026-05-31T01:30:00Z",
            "source_time_utc": "2026-05-31T01:30:00Z",
            "captured_at_utc": "2026-05-31T01:31:00Z",
            "symbol": "XAUUSD",
        },
        context="feature_store",
        decision_time_utc="2026-05-31T01:30:00Z",
    )

    assert result["ok"] is False
    assert any(issue["field_path"] == "captured_at_utc" for issue in result["issues"])


def test_label_store_accepts_outcome_fields():
    result = validate_no_leak_row(
        {
            "broker_net_r": -0.87,
            "exit_time_utc": "2026-05-31T02:18:16Z",
            "final_r": -1.0,
            "symbol": "XAUUSD",
        },
        context="label_store",
        decision_time_utc="2026-05-31T01:30:00Z",
    )

    assert result["ok"] is True


def test_session_normalizer_uses_utc_authority_across_dst_and_crypto():
    config = builder.load_config()

    before_dst = session_for_utc("2026-03-27T07:30:00Z", "XAUUSD", config)
    after_dst = session_for_utc("2026-03-30T07:30:00Z", "XAUUSD", config)
    crypto = session_for_utc("2026-03-29T04:00:00Z", "BTCUSD", config)

    assert before_dst["session"] == "london"
    assert after_dst["session"] == "london"
    assert before_dst["repo_session_authority"] == "UTC_CONFIG_KILL_ZONE_WINDOWS"
    assert after_dst["london_local"].endswith("+01:00")
    assert crypto["session"] == "off_configured_session"


def test_candle_close_and_friday_close_contract():
    assert candle_close_for("2026-05-31T01:31:06Z", 15) == "2026-05-31T01:45:00+00:00"
    assert is_friday_close_risk("2026-06-05T20:50:00Z", "XAUUSD") is True
    assert is_friday_close_risk("2026-06-05T20:50:00Z", "BTCUSD") is False


def test_canonical_key_preserves_broker_lifecycle_ids():
    key = canonical_key(
        {
            "candidate_id": "broadorigin_b50c4c16b1bb90ec84c9cf81",
            "candle_time_utc": "2026-05-31T01:30:00Z",
            "framework": "ob_retest",
            "mt5_entry_deal_ticket": 225810110,
            "mt5_entry_order_ticket": 241972476,
            "mt5_position_ticket": 241972476,
            "side": "LONG",
            "symbol": "XAUUSD",
        },
        route_id=builder.ROUTE_ID,
        source_path="live_checkpoint",
    )

    assert key["symbol"] == "XAUUSD"
    assert key["order_id"] == 241972476
    assert key["deal_id"] == 225810110
    assert key["position_id"] == 241972476
    assert key["source_row_id"] == "broadorigin_b50c4c16b1bb90ec84c9cf81"


def test_written_route_outputs_verify_without_rewrite():
    if not Path(builder.OUTPUT_MANIFEST).exists():
        builder.build_outputs()
    result = builder.verify_outputs(write=False)

    assert result["ok"] is True
    assert result["timestamp_inventory_rows"] > 0
    assert result["asof_contract_rows"] > 0
