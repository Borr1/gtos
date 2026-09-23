from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pandas as pd
import pytest

from src.research_infra import orderflow_features as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"orderflow_features_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_prepare_trades_builds_signed_size():
    df = pd.DataFrame(
        {
            "ts_event": ["2026-04-17T13:00:00Z", "2026-04-17T13:00:01Z"],
            "symbol": ["GC.v.0", "GC.v.0"],
            "price": [2400.0, 2400.1],
            "size": [2, 3],
            "side": ["B", "A"],
        }
    )
    out = mod.prepare_trades(df)
    assert out["signed_size"].tolist() == [2.0, -3.0]


def test_volume_profile_stats_finds_event_bin_percentile_and_lvn():
    df = pd.DataFrame(
        {
            "ts_event": pd.date_range("2026-04-17T13:00:00Z", periods=5, freq="min"),
            "symbol": ["GC.v.0"] * 5,
            "price": [2400.0, 2400.0, 2400.1, 2400.2, 2400.2],
            "size": [10, 10, 1, 20, 20],
            "side": ["B"] * 5,
            "signed_size": [10, 10, 1, 20, 20],
        }
    )
    stats = mod.volume_profile_stats(df, "GC.v.0", 2400.1)
    assert stats["profile_poc_price"] == 2400.2
    assert stats["profile_event_price_volume"] == 1.0
    assert stats["profile_event_price_volume_percentile"] > 0
    assert stats["profile_nearest_lvn_distance_ticks"] == 0.0


def test_compute_event_features_has_pre_and_post_windows():
    event = {
        "event_id": "e1",
        "symbol": "XAUUSD",
        "event_class": "candidate",
        "decision": "CANDIDATE",
        "framework": "ob_retest",
        "setup_grade": "A+",
        "direction": "LONG",
        "canonical_m15_close_utc": "2026-04-17T13:15:00+00:00",
        "window_start_utc": "2026-04-17T12:15:00+00:00",
        "window_end_utc": "2026-04-17T14:15:00+00:00",
    }
    trades = pd.DataFrame(
        {
            "ts_event": [
                "2026-04-17T13:00:00Z",
                "2026-04-17T13:10:00Z",
                "2026-04-17T13:16:00Z",
            ],
            "symbol": ["GC.v.0", "GC.v.0", "GC.v.0"],
            "price": [2400.0, 2400.2, 2400.4],
            "size": [1, 2, 3],
            "side": ["B", "B", "A"],
        }
    )
    row = mod.compute_event_features(event, trades, "GC.v.0")
    assert row["is_primary_proxy"] is True
    assert row["data_status"] == "ok"
    assert row["event15_trade_count"] == 2
    assert row["post15_trade_count"] == 1
    assert row["event15_signed_volume"] == 3.0
    assert row["post15_signed_volume"] == -3.0


def test_compute_event_features_marks_expanded_primary_proxies():
    base_event = {
        "event_id": "e1",
        "event_class": "candidate",
        "decision": "CANDIDATE",
        "framework": "ob_retest",
        "setup_grade": "A+",
        "direction": "LONG",
        "canonical_m15_close_utc": "2026-04-17T13:15:00+00:00",
        "window_start_utc": "2026-04-17T12:15:00+00:00",
        "window_end_utc": "2026-04-17T14:15:00+00:00",
    }
    trades = pd.DataFrame(
        {
            "ts_event": ["2026-04-17T13:00:00Z"],
            "symbol": ["SI.v.0"],
            "price": [29.125],
            "size": [1],
            "side": ["B"],
        }
    )

    xag = mod.compute_event_features({**base_event, "symbol": "XAGUSD"}, trades, "SI.v.0")
    gbp = mod.compute_event_features(
        {**base_event, "symbol": "GBPUSD"},
        trades.assign(symbol="6B.v.0", price=1.2500),
        "6B.v.0",
    )
    non_primary = mod.compute_event_features({**base_event, "symbol": "GBPUSD"}, trades, "SI.v.0")

    assert xag["is_primary_proxy"] is True
    assert gbp["is_primary_proxy"] is True
    assert non_primary["is_primary_proxy"] is False
    assert mod.tick_size("SI.v.0") == 0.005
    assert mod.tick_size("6B.v.0") == 0.0001
    assert mod.tick_size("6J.v.0") == 0.0000005
