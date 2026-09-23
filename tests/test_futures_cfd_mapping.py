from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pandas as pd
import pytest

from src.research_infra import futures_cfd_mapping as mod


@pytest.fixture
def tmp_path():
    path = Path(".test_tmp") / f"futures_cfd_mapping_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def test_parse_pair_requires_colon():
    pair = mod.parse_pair("GC.v.0:XAUUSD")
    assert pair.futures_symbol == "GC.v.0"
    assert pair.mt5_symbol == "XAUUSD"
    assert pair.return_transform == "direct"


def test_parse_pair_supports_inverse_return_transform():
    pair = mod.parse_pair("6J.v.0:USDJPY:inverse_return")
    assert pair.futures_symbol == "6J.v.0"
    assert pair.mt5_symbol == "USDJPY"
    assert pair.return_transform == "inverse_return"


def test_aggregate_futures_m1_builds_symbol_minutes():
    df = pd.DataFrame(
        {
            "ts_event": [
                "2026-04-24T13:00:00Z",
                "2026-04-24T13:00:30Z",
                "2026-04-24T13:01:00Z",
            ],
            "symbol": ["GC.v.0", "GC.v.0", "GC.v.0"],
            "price": [3300.0, 3301.0, 3302.0],
            "size": [1, 2, 3],
            "side": ["B", "A", "B"],
        }
    )
    out = mod.aggregate_futures_m1(df)
    first = out[out["symbol"] == "GC.v.0"].iloc[0]
    assert first["open"] == 3300.0
    assert first["high"] == 3301.0
    assert first["close"] == 3301.0
    assert first["volume"] == 3
    assert first["trade_count"] == 2
    assert first["signed_volume"] == -1


def test_load_mt5_m1_treats_times_as_utc(tmp_path):
    path = tmp_path / "XAUUSD_M1.csv"
    path.write_text(
        "time,open,high,low,close,volume\n"
        "2026-04-24 13:00:00,1,2,0.5,1.5,10\n",
        encoding="utf-8",
    )
    df = mod.load_mt5_m1("XAUUSD", data_dir=tmp_path)
    assert str(df.index[0].tz) == "UTC"
    assert df.iloc[0]["close"] == 1.5


def test_load_mt5_m1_applies_time_shift(tmp_path):
    path = tmp_path / "XAUUSD_M1.csv"
    path.write_text(
        "time,open,high,low,close,volume\n"
        "2026-04-24 03:00:00,1,2,0.5,1.5,10\n",
        encoding="utf-8",
    )
    df = mod.load_mt5_m1("XAUUSD", data_dir=tmp_path, time_shift_minutes=-180)
    assert df.index[0].isoformat() == "2026-04-24T00:00:00+00:00"


def test_diagnose_pair_reports_high_correlation_for_scaled_returns():
    idx = pd.date_range("2026-04-24T13:00:00Z", periods=6, freq="min")
    fut = pd.DataFrame(
        {
            "symbol": ["GC.v.0"] * 6,
            "open": [100, 102, 101, 103, 104, 102],
            "high": [100, 101, 102, 103, 104, 105],
            "low": [100, 101, 102, 103, 104, 105],
            "close": [100, 101, 102, 103, 104, 105],
            "volume": [10] * 6,
            "trade_count": [2] * 6,
        },
        index=idx,
    )
    mt5 = pd.DataFrame(
        {
            "open": [200, 202, 204, 206, 208, 210],
            "high": [200, 202, 204, 206, 208, 210],
            "low": [200, 202, 204, 206, 208, 210],
            "close": [200, 202, 204, 206, 208, 210],
            "volume": [20] * 6,
        },
        index=idx,
    )
    diag = mod.diagnose_pair(
        fut,
        mt5,
        mod.MappingPair("GC.v.0", "XAUUSD"),
        max_lag_minutes=2,
    )
    assert diag.aligned_minutes == 6
    assert diag.zero_lag_return_corr is not None
    assert diag.zero_lag_return_corr > 0.99
    assert diag.directional_agreement == 1.0


def test_diagnose_pair_supports_inverse_return_alignment():
    idx = pd.date_range("2026-04-24T13:00:00Z", periods=6, freq="min")
    fut = pd.DataFrame(
        {
            "symbol": ["6J.v.0"] * 6,
            "open": [100, 98.0392156863, 99.0099009901, 97.0873786408, 96.1538461538, 98.0392156863],
            "high": [100, 98.0392156863, 99.0099009901, 97.0873786408, 96.1538461538, 98.0392156863],
            "low": [100, 98.0392156863, 99.0099009901, 97.0873786408, 96.1538461538, 98.0392156863],
            "close": [100, 98.0392156863, 99.0099009901, 97.0873786408, 96.1538461538, 98.0392156863],
            "volume": [10] * 6,
            "trade_count": [2] * 6,
        },
        index=idx,
    )
    mt5 = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105],
            "high": [100, 102, 101, 103, 104, 102],
            "low": [100, 102, 101, 103, 104, 102],
            "close": [100, 102, 101, 103, 104, 102],
            "volume": [20] * 6,
        },
        index=idx,
    )

    direct = mod.diagnose_pair(fut, mt5, mod.MappingPair("6J.v.0", "USDJPY"))
    inverse = mod.diagnose_pair(
        fut,
        mt5,
        mod.MappingPair("6J.v.0", "USDJPY", return_transform="inverse_return"),
    )

    assert direct.zero_lag_return_corr is not None
    assert direct.zero_lag_return_corr < -0.99
    assert inverse.zero_lag_return_corr is not None
    assert inverse.zero_lag_return_corr > 0.99
    assert inverse.directional_agreement == 1.0
    assert inverse.basis_mean is None
    assert inverse.return_transform == "inverse_return"


def test_write_mapping_report_includes_no_promotion(tmp_path):
    diag = mod.PairDiagnostics(
        futures_symbol="GC.v.0",
        mt5_symbol="XAUUSD",
        aligned_minutes=0,
        futures_minutes=0,
        mt5_minutes=0,
        start_utc=None,
        end_utc=None,
        basis_mean=None,
        basis_std=None,
        basis_min=None,
        basis_max=None,
        basis_z_abs_p95=None,
        zero_lag_return_corr=None,
        best_lag_minutes=None,
        best_lag_corr=None,
        beta_mt5_per_futures=None,
        directional_agreement=None,
        futures_volume_sum=None,
        futures_trade_count_sum=None,
    )
    output = tmp_path / "report.json"
    payload = mod.write_mapping_report([diag], output_path=output, inputs={})
    assert output.exists()
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert payload["synthesis"]["ambiguities"]
