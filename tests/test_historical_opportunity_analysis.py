import csv
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.analyze_historical_opportunity_dataset import (
    _scaled_hold_bars,
    refine_mechanical_outcome,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"historical_opportunity_analysis_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_refinement_rejects_nonlocal_lower_timeframe_data(tmp_path):
    data_dir = tmp_path / "ohlcv"
    _write_ohlcv(
        data_dir / "XAUUSD_M5.csv",
        start=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(minutes=5),
        count=4,
    )
    row = _setup_row("2022-02-02T07:15:00+00:00")

    refined = refine_mechanical_outcome(row, timeframe="M5", data_dirs=[data_dir])

    assert refined["refined_outcome"] == "NO_LOCAL_OHLCV"
    assert refined["lower_tf_local_coverage"] is False
    assert refined["refined_skip_reason"] == "lower_timeframe_not_contiguous_at_candle"


def test_refinement_uses_scaled_wall_clock_hold_window(tmp_path):
    data_dir = tmp_path / "ohlcv"
    _write_ohlcv(
        data_dir / "XAUUSD_M5.csv",
        start=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(minutes=5),
        count=6,
        lows=[100.5, 99.8, 99.7, 99.6, 99.5, 99.4],
        highs=[100.8, 100.2, 101.6, 100.5, 100.3, 100.1],
    )
    row = _setup_row("2026-01-01T00:00:00+00:00")

    refined = refine_mechanical_outcome(row, timeframe="M5", data_dirs=[data_dir])

    assert refined["refined_max_hold_bars"] == _scaled_hold_bars("M5")
    assert refined["lower_tf_local_coverage"] is True
    assert refined["refined_outcome"] == "TP"
    assert refined["refined_realized_r"] == pytest.approx(1.5)


def _setup_row(candle_close):
    return {
        "opportunity_key": f"XAUUSD|{candle_close}",
        "symbol": "XAUUSD",
        "candle_close_utc": candle_close,
        "mechanical_setup_status": "OK",
        "mechanical_outcome": "SAME_BAR",
        "mechanical_realized_r": None,
        "mechanical_side": "LONG",
        "mechanical_framework": "ob_retest",
        "mechanical_entry": 100.0,
        "mechanical_sl": 99.0,
        "mechanical_tp": 101.5,
        "mechanical_rr": 1.5,
        "mechanical_sl_buffer_used": 0.1,
        "mechanical_h1_atr": 1.0,
        "mechanical_tp_source": "rr_floor",
    }


def _write_ohlcv(
    path,
    *,
    start,
    delta,
    count,
    lows=None,
    highs=None,
):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["time", "open", "high", "low", "close", "volume"],
        )
        writer.writeheader()
        for idx in range(count):
            opened_at = start + delta * idx
            writer.writerow(
                {
                    "time": opened_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": "100.50",
                    "high": f"{(highs[idx] if highs else 100.80):.5f}",
                    "low": f"{(lows[idx] if lows else 99.80):.5f}",
                    "close": "100.10",
                    "volume": 1000 + idx,
                }
            )
