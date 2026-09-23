from __future__ import annotations

import build_vnext_absolute_moonshot_lane17_market_awareness_whiteboard as lane17


def _source_row(symbol: str, timeframe: str) -> dict:
    return {
        "schema_version": "lane17_source_coverage_row_v1",
        "source_family": "unit_test_source",
        "source_path": f"unit/{symbol}_{timeframe}.csv",
        "exists": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "row_count": 100,
        "first_time_utc": "2026-05-28T00:00:00+00:00",
        "last_time_utc": "2026-05-30T00:00:00+00:00",
        "first_date": "2026-05-28",
        "last_date": "2026-05-30",
    }


def test_schema_has_required_market_awareness_fields_and_source_labels() -> None:
    schema = lane17.build_market_awareness_schema()

    assert set(lane17.REQUIRED_WHITEBOARD_FIELDS).issubset(schema["required_whiteboard_fields"])
    assert set(schema["source_state_labels"]) == set(lane17.SOURCE_STATE_LABELS)
    assert schema["timeframes"] == list(lane17.WHITEBOARD_TIMEFRAMES)
    assert "no hidden null" not in schema["no_hidden_null_rule"].lower()


def test_correlation_pairs_cover_full_24_symbol_matrix_without_topn() -> None:
    matrix = {
        symbol: {peer: 0.0 for peer in lane17.LIVE_SYMBOLS if peer != symbol}
        for symbol in lane17.LIVE_SYMBOLS
    }

    rows = lane17.all_correlation_pair_rows(matrix)
    pair_keys = {(row["symbol"], row["peer_symbol"]) for row in rows}
    seen_symbols = {row["symbol"] for row in rows} | {row["peer_symbol"] for row in rows}

    assert len(rows) == 276
    assert len(pair_keys) == 276
    assert seen_symbols == set(lane17.LIVE_SYMBOLS)


def test_sample_whiteboard_row_has_multitimeframe_source_state_and_no_result_leak(monkeypatch) -> None:
    symbol = "XAUUSD"
    coverage_index = {
        (symbol, timeframe): [_source_row(symbol, timeframe)]
        for timeframe in ("D1", "H4", "H1", "M15")
    }
    features = {
        "identity_symbol": symbol,
        "identity_broker_symbol": symbol,
        "feature_time_utc": "2026-05-29T12:00:00+00:00",
        "source_window_complete": True,
        "m15_trend_state_20": "uptrend",
        "m15_volatility_state_14_vs_50": "expanding",
        "liquidity_sweep_proxy_state": "no_recent_sweep",
        "source_quality_status": "complete",
        "m1_entry_minute_available": True,
        "m1_availability_status": "m1_entry_minute_available",
        "strict_tick_available": True,
        "tick_availability_status": "strict_tick_available",
        "strict_tick_entry_spread_r": 0.04,
        "strict_tick_risk_price_distance": 10.0,
        "spread_r_bucket": "low_spread_r",
        "cost_status": "cost_proxy_available",
        "session_bucket": "london_broad",
        "session_source_state": "decision_timestamp_session",
        "correlation_cluster_join_state": "proxy_matrix_join",
        "regime_h4_state": "trend",
        "regime_h4_direction": "bullish",
        "regime_h4_score": 0.77,
        "regime_join_state": "exact_h4_regime_join",
        "source_use_state": "unit_test_source_state",
    }
    replay = {
        "row_id": "lane08_unit_row",
        "symbol": symbol,
        "broker_symbol": symbol,
        "selected_row_id": "dup-unit-1",
        "decision_asof_utc": "2026-05-29T12:00:00+00:00",
        "candidate_id": "candidate-unit-1",
        "side": "LONG",
        "framework": "ob_retest",
        "origin_family": "unit",
        "decision_inputs": {
            "source_completeness": {
                "source_completeness_state": "complete",
                "source_gaps": [],
            },
            "broker_constraints": {"symbol_spec_join_state": "joined"},
        },
    }
    feature = {
        "row_id": "lane05_unit_row",
        "duplicate_key": "dup-unit-1",
        "feature_source_state": "decision-available",
        "features": features,
    }
    spec = {
        "session_status": "SESSION_OPEN",
        "trade_mode": "FULL",
        "spread_sample_status": "AVAILABLE",
        "spread_sample_points": 12,
        "volume_min": 0.01,
        "volume_step": 0.01,
        "volume_max": 100.0,
        "trade_stops_level": 0,
        "trade_freeze_level": 0,
        "trade_tick_size_status": "OK",
        "trade_tick_value_status": "OK",
    }
    correlation_state = {"source_state": "proxy", "matrix_peer_count": 23, "cluster_peer_count": 0}
    monkeypatch.setattr(lane17, "sha256_file", lambda _path: "unit-test-hash")

    row, gaps = lane17.build_whiteboard_row(
        idx=1,
        replay=replay,
        feature=feature,
        coverage_index=coverage_index,
        symbol_specs={symbol: spec},
        correlation_states={symbol: correlation_state},
    )

    assert set(row["timeframe_coverage_state"]) == set(lane17.WHITEBOARD_TIMEFRAMES)
    assert set(row["field_source_state"].values()).issubset(set(lane17.SOURCE_STATE_LABELS))
    assert row["source_hash"] == "unit-test-hash"
    assert row["no_leak_status"].startswith("pass_")
    assert not lane17.validate_row_no_leak(row)
    assert "label_values" not in row
    assert "result_payload" not in row
    assert any(gap["field_family"] == "correlation_cluster_runtime_snapshot" for gap in gaps)
    assert any(gap["source_state"] == "non-generatable" for gap in gaps)


def test_forward_capture_contract_is_default_off() -> None:
    contract = lane17.build_forward_capture_contract()

    assert contract["activation_state"] == "default_off_no_live_behavior_change"
    assert contract["forbidden_activation_without_owner_dossier"] is True
    assert all(field["default_off"] is True for field in contract["packet_fields"])


def test_downstream_contract_has_all_expected_consumers() -> None:
    contract = lane17.build_downstream_contract()

    assert set(contract["consumers"]) == {
        "Selector V3",
        "Scheduler V3",
        "Execution V3",
        "ML",
        "Repair Companion",
        "Command Center",
    }
    assert contract["default_off_contract_only"] is True


def test_validate_row_no_leak_rejects_label_result_fields() -> None:
    row = {
        "timeframe_coverage_state": {timeframe: {} for timeframe in lane17.WHITEBOARD_TIMEFRAMES},
        "stale_or_null_reason": [{"field": "unit", "reason": "unit", "capture_or_repair_requirement": "unit"}],
        "field_source_state": {"unit": "decision-available"},
        "label_values": {"sl_before_1r": True},
    }

    assert "forbidden_field_present:label_values" in lane17.validate_row_no_leak(row)
