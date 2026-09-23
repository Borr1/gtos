import csv
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.build_historical_opportunity_truth_layer as truth_layer
from scripts.build_historical_opportunity_truth_layer import (
    classify_truth_row,
    inspect_lower_timeframe,
)


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"historical_opportunity_truth_layer_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_gate_reject_maps_htf_conflict_to_setup_bucket():
    row = _base_row(
        pre_ai_gate_status="PRE_SCREEN_REJECT",
        pre_ai_gate_reason="L2_h4_conflict_bearish_vs_d1_bullish",
        would_send_ai=False,
        mechanical_setup_status="NOT_EVALUATED",
    )

    classified = classify_truth_row(row, lower_timeframes=["M5"], data_dirs=[])

    assert classified["truth_outcome"] == "PRE_SCREEN_REJECT"
    assert classified["truth_failure_bucket"] == "SETUP_HTF_CONFLICT"
    assert classified["truth_fill_status"] == "NOT_APPLICABLE"
    assert classified["truth_confidence"] == "NONE"
    assert classified["m5_refinement_attempted"] is False


def test_same_bar_uses_contiguous_lower_timeframe_resolution(tmp_path):
    data_dir = tmp_path / "ohlcv"
    _write_ohlcv(
        data_dir / "XAUUSD_M5.csv",
        start=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(minutes=5),
        count=4,
        lows=[99.8, 100.2, 100.1, 100.0],
        highs=[100.8, 101.6, 100.6, 100.5],
    )
    row = _setup_row("2026-01-01T00:00:00+00:00")

    classified = classify_truth_row(row, lower_timeframes=["M5"], data_dirs=[data_dir])

    assert classified["truth_source"] == "lower_timeframe"
    assert classified["truth_source_timeframe"] == "M5"
    assert classified["truth_outcome"] == "TP"
    assert classified["truth_realized_r"] == pytest.approx(1.5)
    assert classified["truth_failure_bucket"] == "SUCCESS_TP_FIRST"
    assert classified["truth_confidence"] == "HIGH"
    assert classified["m5_local_coverage"] is True
    assert classified["m5_gap_count_in_horizon"] == 0


def test_same_bar_preserved_when_lower_timeframe_is_not_local(tmp_path):
    data_dir = tmp_path / "ohlcv"
    _write_ohlcv(
        data_dir / "XAUUSD_M5.csv",
        start=datetime(2026, 1, 1, 0, 10, tzinfo=timezone.utc),
        delta=timedelta(minutes=5),
        count=3,
    )
    row = _setup_row("2026-01-01T00:00:00+00:00")

    classified = classify_truth_row(row, lower_timeframes=["M5"], data_dirs=[data_dir])

    assert classified["truth_source"] == "m15_mechanical"
    assert classified["truth_source_timeframe"] == "M15"
    assert classified["truth_outcome"] == "SAME_BAR"
    assert classified["truth_failure_bucket"] == "AMBIGUOUS_FILL_AND_EXIT_SAME_BAR"
    assert classified["truth_ambiguity_bucket"] == "M15_SAME_BAR_NO_LOCAL_LOWER_TF"
    assert classified["truth_confidence"] == "LOW"


def test_lower_timeframe_gap_is_explicit_data_bucket(tmp_path):
    data_dir = tmp_path / "ohlcv"
    _write_ohlcv_at_times(
        data_dir / "XAUUSD_M5.csv",
        opened_at=[
            datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc),
        ],
        lows=[99.8, 100.1],
        highs=[100.8, 101.6],
    )
    row = _setup_row("2026-01-01T00:00:00+00:00")

    diagnostics = inspect_lower_timeframe(row, timeframe="M5", data_dirs=[data_dir])
    classified = classify_truth_row(row, lower_timeframes=["M5"], data_dirs=[data_dir])

    assert diagnostics.local_coverage is True
    assert diagnostics.gap_count_in_horizon == 1
    assert classified["truth_source"] == "lower_timeframe"
    assert classified["truth_outcome"] == "LOWER_TF_GAPPY"
    assert classified["truth_failure_bucket"] == "DATA_LOWER_TF_GAP_BEFORE_RESOLUTION"
    assert classified["truth_ambiguity_bucket"] == "LOWER_TF_GAPPY"
    assert classified["truth_confidence"] == "LOW"


def test_lower_timeframe_refinement_slices_horizon_before_resolver(tmp_path, monkeypatch):
    data_dir = tmp_path / "ohlcv"
    _write_ohlcv(
        data_dir / "XAUUSD_M1.csv",
        start=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        delta=timedelta(minutes=1),
        count=1600,
        lows=[100.2] * 1600,
        highs=[100.8] * 1600,
    )
    captured = {}

    def fake_resolve(setup, *, ohlcv_rows, max_hold_bars, require_pending_fill):
        captured["rows_seen"] = len(ohlcv_rows)
        captured["max_hold_bars"] = max_hold_bars
        captured["require_pending_fill"] = require_pending_fill
        return SimpleNamespace(
            outcome="NO_ENTRY",
            realized_r=None,
            bars_in_trade=len(ohlcv_rows),
            exit_time=None,
            skip_reason="NEVER_FILLED",
        )

    monkeypatch.setattr(truth_layer, "resolve_mechanical_outcome", fake_resolve)

    classified = classify_truth_row(
        _setup_row("2026-01-01T00:00:00+00:00"),
        lower_timeframes=["M1"],
        data_dirs=[data_dir],
    )

    assert captured == {
        "rows_seen": 1440,
        "max_hold_bars": 1440,
        "require_pending_fill": True,
    }
    assert classified["m1_future_rows_available"] > captured["rows_seen"]
    assert classified["truth_outcome"] == "NO_ENTRY"


def test_truth_layer_import_does_not_load_paid_ai_clients():
    code = (
        "import sys\n"
        "import scripts.build_historical_opportunity_truth_layer\n"
        "print('anthropic' in sys.modules)\n"
        "print('openai' in sys.modules)\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=True,
    )

    assert result.stdout.strip().splitlines() == ["False", "False"]


def _base_row(**overrides):
    row = {
        "opportunity_key": "XAUUSD|2026-01-01T00:00:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "external_symbol": "XAUUSD",
        "timeframe": "M15",
        "bar_time_utc": "2025-12-31T23:45:00+00:00",
        "candle_close_utc": "2026-01-01T00:00:00+00:00",
        "session": "london",
        "kill_zone": "london",
        "year": "2026",
        "month": "2026-01",
        "day_of_week": "Thursday",
        "hour_utc": 0,
        "bundle_id": "calendar_macro_bundle_v1",
        "pre_ai_gate_policy": "current_orchestrator_deterministic_pre_ai_offline_v1",
        "pre_ai_gate_status": "WOULD_SEND_AI",
        "pre_ai_gate_reason": "passed_deterministic_pre_ai_gates",
        "would_send_ai": True,
        "deterministic_bias": "bullish",
        "deterministic_bias_source": "D1",
        "deterministic_bias_d1": "bullish",
        "deterministic_bias_h4": "bullish",
        "deterministic_bias_h1": "bullish",
        "deterministic_bias_m15": "transitional",
        "all_timeframes_complete": True,
        "mechanical_setup_status": "OK",
        "mechanical_skip_reason": None,
        "mechanical_side": "LONG",
        "mechanical_framework": "ob_retest",
        "mechanical_entry": 100.0,
        "mechanical_sl": 99.0,
        "mechanical_tp": 101.5,
        "mechanical_rr": 1.5,
        "mechanical_sl_buffer_used": 0.1,
        "mechanical_h1_atr": 1.0,
        "mechanical_tp_source": "rr_floor",
        "mechanical_outcome": "SAME_BAR",
        "mechanical_realized_r": None,
        "mechanical_bars_in_trade": 1,
        "mechanical_exit_time": "2026-01-01T00:15:00+00:00",
        "mechanical_outcome_skip_reason": "FILL_AND_TPSL_SAME_BAR",
        "external_snapshot_match_status": "MISSING_ALL_SOURCES",
        "external_snapshot_as_of_utc": None,
        "external_snapshot_missing_sources": ["fred"],
        "feature_availability_flags": {"fred": False},
        "paid_ai_replay": False,
        "ai_call_attempted": False,
        "ai_call_count": 0,
    }
    row.update(overrides)
    return row


def _setup_row(candle_close):
    return _base_row(
        opportunity_key=f"XAUUSD|{candle_close}",
        candle_close_utc=candle_close,
    )


def _write_ohlcv(path, *, start, delta, count, lows=None, highs=None):
    opened_at = [start + delta * idx for idx in range(count)]
    _write_ohlcv_at_times(path, opened_at=opened_at, lows=lows, highs=highs)


def _write_ohlcv_at_times(path, *, opened_at, lows=None, highs=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["time", "open", "high", "low", "close", "volume"],
        )
        writer.writeheader()
        for idx, opened in enumerate(opened_at):
            writer.writerow(
                {
                    "time": opened.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": "100.50",
                    "high": f"{(highs[idx] if highs else 100.80):.5f}",
                    "low": f"{(lows[idx] if lows else 99.80):.5f}",
                    "close": "100.10",
                    "volume": 1000 + idx,
                }
            )
