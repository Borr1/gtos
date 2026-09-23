from __future__ import annotations

from datetime import datetime, timezone

from scripts import build_raw_ohlc_prefill_delivery_path as mod


def _dt(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _bar(time: str, open_: float, high: float, low: float, close: float) -> dict:
    return {
        "time": _dt(time),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
    }


def _setup(
    *,
    side: str = "LONG",
    entry: float = 99.0,
    symbol: str = "XAUUSD",
    clock: str = "2026-01-01T00:00:00+00:00",
) -> dict:
    return {
        "event_key": f"{symbol}|{clock}",
        "symbol": symbol,
        "session": "ny",
        "mechanical_side": side,
        "mechanical_entry": entry,
        "mechanical_sl": 97.0,
        "mechanical_tp": 105.0,
        "candle_close_utc": clock,
        "raw_cohort_key": f"{symbol}|ny|bullish|D1",
        "role": "dominance_watchlist",
        "outcome": "TIMEOUT",
        "bars_to_fill": 2,
        "path_rows_to_fill": 2,
        "selected_timeframe": "M15",
    }


def test_capture_prefill_uses_m1_until_reconstructed_touch_without_scoring():
    setup = _setup()
    indexes = {
        ("XAUUSD", "M1"): mod.PathIndex(
            "XAUUSD",
            "M1",
            [
                _bar("2026-01-01T00:01:00+00:00", 100.0, 100.2, 99.4, 99.6),
                _bar("2026-01-01T00:02:00+00:00", 99.6, 99.7, 98.9, 99.1),
                _bar("2026-01-01T00:03:00+00:00", 99.1, 101.0, 99.0, 100.5),
            ],
        ),
        ("XAUUSD", "M5"): mod.PathIndex("XAUUSD", "M5", []),
        ("XAUUSD", "M15"): mod.PathIndex("XAUUSD", "M15", []),
    }

    record = mod.capture_setup(setup, indexes=indexes, pending_expiry_bars=4)

    assert record["pre_fill_path_timeframe"] == "M1"
    assert record["fill_or_expiry_state"] == "FILLED_RECONSTRUCTED_PATH_TOUCH"
    assert record["pre_fill_path_rows"] == 2
    assert record["fill_time_utc"] == "2026-01-01T00:02:00+00:00"
    assert record["lower_tf_available"] is True
    assert record["original_poi_type_and_bounds"]["available"] is False
    assert "M1_FILL_ROW_INTRABAR_ORDER_AMBIGUOUS" in record["ambiguity_flags"]
    assert record["as_of_delivery_structure_flags"]["status"] == "STRUCTURE_PROXY_ONLY_NOT_VALIDATION"
    assert "realized_r" not in record


def test_capture_reports_m15_fallback_and_missing_lifecycle_when_no_fill():
    setup = _setup(side="SHORT", entry=101.0, symbol="USDJPY")
    indexes = {
        ("USDJPY", "M1"): mod.PathIndex("USDJPY", "M1", []),
        ("USDJPY", "M5"): mod.PathIndex("USDJPY", "M5", []),
        ("USDJPY", "M15"): mod.PathIndex(
            "USDJPY",
            "M15",
            [
                _bar("2026-01-01T00:15:00+00:00", 100.0, 100.2, 99.7, 100.1),
                _bar("2026-01-01T00:30:00+00:00", 100.1, 100.3, 99.8, 100.0),
                _bar("2026-01-01T00:45:00+00:00", 100.0, 100.4, 99.9, 100.2),
                _bar("2026-01-01T01:00:00+00:00", 100.2, 100.5, 99.9, 100.3),
            ],
        ),
    }

    record = mod.capture_setup(setup, indexes=indexes, pending_expiry_bars=4)

    assert record["pre_fill_path_timeframe"] == "M15"
    assert record["fill_or_expiry_state"] == "NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH"
    assert record["lower_tf_available"] is False
    assert "LOWER_TF_UNAVAILABLE_SELECTED_M15" in record["ambiguity_flags"]
    assert "BROKER_PENDING_LIFECYCLE_STATE_MISSING" in record["ambiguity_flags"]
    assert record["pre_fill_path_row_counts_by_timeframe"] == {"M1": 0, "M5": 0, "M15": 4}


def test_summary_preserves_no_promotion_and_non_claims():
    records = [
        {
            "symbol": "XAUUSD",
            "lower_tf_available": True,
            "pre_fill_path_timeframe": "M1",
            "fill_or_expiry_state": "FILLED_RECONSTRUCTED_PATH_TOUCH",
            "original_poi_type_and_bounds": {"available": False},
            "as_of_delivery_structure_flags": {"status": "STRUCTURE_PROXY_ONLY_NOT_VALIDATION"},
            "ambiguity_flags": ["BROKER_PENDING_LIFECYCLE_STATE_MISSING"],
        },
        {
            "symbol": "USDJPY",
            "lower_tf_available": False,
            "pre_fill_path_timeframe": "M15",
            "fill_or_expiry_state": "NOT_FILLED_BEFORE_EXPIRY_ON_SELECTED_PATH",
            "original_poi_type_and_bounds": {"available": False},
            "as_of_delivery_structure_flags": {"status": "INSUFFICIENT_PREFILL_ROWS"},
            "ambiguity_flags": ["LOWER_TF_UNAVAILABLE_SELECTED_M15"],
        },
    ]

    summary = mod.summarize(records, setup_rows_seen=2, event_log_path="events.jsonl", data_roots=[])

    assert summary["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert summary["discovery_label"] == "COVERAGE_ONLY_NOT_STRATEGY_SCORE"
    assert summary["coverage"]["captured_setup_rows"] == 2
    assert summary["coverage"]["lower_tf_available_rate"] == 0.5
    assert "No delivery-leg strategy is scored." in summary["explicit_non_claims"]
