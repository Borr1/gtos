"""Unit tests for ``src.components.tick_features``.

Covers the per-bar feature extractor, sidecar I/O, and edge cases (empty bar,
single tick, all-mid ticks, NaN handling).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# Skip whole module if pyarrow / pandas missing.
pytest.importorskip("pyarrow")
pytest.importorskip("pandas")

import pandas as pd

from src.components import tick_features as tf
from src.components.tick_features import (
    SCHEMA_VERSION,
    TickFeatures,
    _count_micro_reversals,
    _empty_features,
    compute_features_from_df,
    compute_for_bar,
    m15_bar_window,
    read_sidecar,
    sidecar_path_for,
    write_sidecar,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_df(rows: list[dict]) -> pd.DataFrame:
    """Build a tick DataFrame matching the tick_capture parquet schema."""
    base = []
    for r in rows:
        base.append({
            "ts_utc": r.get("ts_utc"),
            "ts_msc": int(r.get("ts_msc", 0)),
            "bid": float(r.get("bid", 0.0)),
            "ask": float(r.get("ask", 0.0)),
            "last": float(r.get("last", 0.0)),
            "volume": float(r.get("volume", 1.0)),
            "flags": int(r.get("flags", 0)),
            "inferred_aggressor": str(r.get("inferred_aggressor", "neutral")),
        })
    df = pd.DataFrame(base)
    if not df.empty:
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df


def _bar_close() -> datetime:
    return datetime(2026, 4, 25, 13, 15, 0, tzinfo=timezone.utc)


def _seed_uptrend_buys(n=20):
    """Simple uptrend with buy aggressor on every tick."""
    base_ts = _bar_close() - timedelta(minutes=15)
    rows = []
    for i in range(n):
        rows.append({
            "ts_utc": base_ts + timedelta(seconds=i * 30),
            "ts_msc": int((base_ts.timestamp() + i * 30) * 1000),
            "bid": 100.0 + i * 0.05,
            "ask": 100.05 + i * 0.05,
            "last": 100.05 + i * 0.05,
            "volume": 1.0,
            "flags": 4,  # TICK_FLAG_ASK
            "inferred_aggressor": "buy",
        })
    return _make_df(rows)


# ---------------------------------------------------------------------------
# m15_bar_window
# ---------------------------------------------------------------------------


class TestM15BarWindow:
    def test_open_close_on_grid(self):
        ts = datetime(2026, 4, 25, 13, 15, 0, tzinfo=timezone.utc)
        bar_open, bar_close = m15_bar_window(ts)
        assert bar_open == datetime(2026, 4, 25, 13, 0, 0, tzinfo=timezone.utc)
        assert bar_close == datetime(2026, 4, 25, 13, 15, 0, tzinfo=timezone.utc)

    def test_snaps_to_m15_grid(self):
        # Caller passes a non-snapped time; we snap down to the M15 boundary.
        ts = datetime(2026, 4, 25, 13, 17, 30, tzinfo=timezone.utc)
        bar_open, bar_close = m15_bar_window(ts)
        assert bar_close.minute == 15
        assert bar_open.minute == 0


# ---------------------------------------------------------------------------
# compute_features_from_df — empty / degenerate / single-tick
# ---------------------------------------------------------------------------


class TestEmptyAndDegenerate:
    def test_empty_df_returns_zero_features(self):
        df = _make_df([])
        f = compute_features_from_df(df, symbol="XAUUSD")
        assert f["n_ticks_unused" if False else "cumulative_delta"] == 0.0
        assert f["spread_max_cents"] == 0.0
        assert f["aggressor_balance"] is None
        assert f["buy_pct"] is None
        assert f["cvd_divergence_flag"] is False

    def test_none_df_returns_empty(self):
        f = compute_features_from_df(None, symbol="XAUUSD")
        assert f == _empty_features()

    def test_single_tick_features(self):
        df = _make_df([{
            "ts_utc": _bar_close() - timedelta(minutes=15),
            "ts_msc": 1000, "bid": 100.0, "ask": 100.05, "last": 100.05,
            "volume": 1.0, "flags": 4, "inferred_aggressor": "buy",
        }])
        f = compute_features_from_df(df, symbol="XAUUSD")
        # +1 buy.
        assert f["cumulative_delta"] == 1.0
        assert f["max_delta_within_bar"] == 1.0
        assert f["min_delta_within_bar"] == 1.0
        # 100% buy classified.
        assert f["buy_pct"] == 1.0
        assert f["aggressor_balance"] == 1.0

    def test_all_mid_ticks_aggressor_balance_none(self):
        rows = []
        for i in range(5):
            rows.append({
                "ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(seconds=i),
                "ts_msc": i, "bid": 100.0, "ask": 100.10, "last": 100.05,
                "volume": 1.0, "flags": 0, "inferred_aggressor": "neutral",
            })
        df = _make_df(rows)
        f = compute_features_from_df(df, symbol="XAUUSD")
        assert f["aggressor_balance"] is None
        assert f["buy_pct"] is None
        assert f["cumulative_delta"] == 0.0
        assert f["footprint_imbalance"] == 0.0

    def test_nan_rows_filtered(self):
        rows = [{
            "ts_utc": _bar_close() - timedelta(minutes=15),
            "ts_msc": 1, "bid": 100.0, "ask": 100.05, "last": 100.05,
            "volume": 1.0, "flags": 4, "inferred_aggressor": "buy",
        }]
        df = _make_df(rows)
        # Inject NaN rows.
        nan_row = pd.DataFrame([{
            "ts_utc": pd.Timestamp(_bar_close()),
            "ts_msc": 2, "bid": float("nan"), "ask": 100.05, "last": 0.0,
            "volume": 1.0, "flags": 0, "inferred_aggressor": "neutral",
        }])
        df = pd.concat([df, nan_row], ignore_index=True)
        f = compute_features_from_df(df, symbol="XAUUSD")
        # Should have processed only the non-NaN row.
        assert f["cumulative_delta"] == 1.0


# ---------------------------------------------------------------------------
# Specific feature semantics
# ---------------------------------------------------------------------------


class TestCumulativeDelta:
    def test_pure_buy_flow_positive_delta(self):
        df = _seed_uptrend_buys(n=10)
        f = compute_features_from_df(df, symbol="XAUUSD")
        assert f["cumulative_delta"] == 10.0
        assert f["max_delta_within_bar"] == 10.0
        assert f["min_delta_within_bar"] == 1.0

    def test_pure_sell_flow_negative_delta(self):
        rows = [{
            "ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(seconds=i),
            "ts_msc": i, "bid": 100.0, "ask": 100.05, "last": 100.0,
            "volume": 1.0, "flags": 2, "inferred_aggressor": "sell",
        } for i in range(8)]
        df = _make_df(rows)
        f = compute_features_from_df(df, symbol="XAUUSD")
        assert f["cumulative_delta"] == -8.0
        assert f["max_delta_within_bar"] == -1.0
        assert f["min_delta_within_bar"] == -8.0

    def test_balanced_two_sided_max_min_capture_swing(self):
        # Up 5, down 5 → cum_delta=0, max=5, min=0.
        rows = []
        for i in range(5):
            rows.append({"ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(seconds=i),
                          "ts_msc": i, "bid": 100.0, "ask": 100.05, "last": 100.05,
                          "volume": 1.0, "flags": 4, "inferred_aggressor": "buy"})
        for i in range(5, 10):
            rows.append({"ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(seconds=i),
                          "ts_msc": i, "bid": 100.0, "ask": 100.05, "last": 100.0,
                          "volume": 1.0, "flags": 2, "inferred_aggressor": "sell"})
        df = _make_df(rows)
        f = compute_features_from_df(df, symbol="XAUUSD")
        assert f["cumulative_delta"] == 0.0
        assert f["max_delta_within_bar"] == 5.0
        assert f["min_delta_within_bar"] == 0.0


class TestFootprintImbalance:
    def test_one_sided_at_one_level_returns_one(self):
        # All buys at the same price.
        rows = [{
            "ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(seconds=i),
            "ts_msc": i, "bid": 100.0, "ask": 100.10, "last": 100.10,
            "volume": 1.0, "flags": 4, "inferred_aggressor": "buy",
        } for i in range(5)]
        df = _make_df(rows)
        f = compute_features_from_df(df, symbol="XAUUSD")
        assert f["footprint_imbalance"] == 1.0

    def test_perfectly_balanced_returns_zero(self):
        rows = []
        for i in range(5):
            # Same bucket; 5 buys + 5 sells.
            rows.append({"ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(seconds=i),
                          "ts_msc": i, "bid": 100.0, "ask": 100.10, "last": 100.05,
                          "volume": 1.0, "flags": 4, "inferred_aggressor": "buy"})
        for i in range(5, 10):
            rows.append({"ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(seconds=i),
                          "ts_msc": i, "bid": 100.0, "ask": 100.10, "last": 100.05,
                          "volume": 1.0, "flags": 2, "inferred_aggressor": "sell"})
        df = _make_df(rows)
        f = compute_features_from_df(df, symbol="XAUUSD", bucket_size=1.0)
        assert f["footprint_imbalance"] == 0.0


class TestSpreadSpike:
    def test_no_spike_when_spread_constant(self):
        rows = [{
            "ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(milliseconds=i * 100),
            "ts_msc": i, "bid": 100.0, "ask": 100.10, "last": 0.0,
            "volume": 1.0, "flags": 0, "inferred_aggressor": "neutral",
        } for i in range(50)]
        df = _make_df(rows)
        f = compute_features_from_df(df, symbol="XAUUSD")
        assert f["spread_spike_count"] == 0

    def test_one_spike_detected(self):
        rows = []
        for i in range(48):
            rows.append({
                "ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(milliseconds=i * 100),
                "ts_msc": i, "bid": 100.0, "ask": 100.10, "last": 0.0,
                "volume": 1.0, "flags": 0, "inferred_aggressor": "neutral",
            })
        # One spike: spread = 0.50 (5x normal), should trigger.
        rows.append({
            "ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(milliseconds=48 * 100),
            "ts_msc": 48, "bid": 100.0, "ask": 100.50, "last": 0.0,
            "volume": 1.0, "flags": 0, "inferred_aggressor": "neutral",
        })
        rows.append({
            "ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(milliseconds=49 * 100),
            "ts_msc": 49, "bid": 100.0, "ask": 100.10, "last": 0.0,
            "volume": 1.0, "flags": 0, "inferred_aggressor": "neutral",
        })
        df = _make_df(rows)
        f = compute_features_from_df(df, symbol="XAUUSD")
        assert f["spread_spike_count"] >= 1


class TestCVDDivergence:
    def test_price_up_delta_up_no_divergence(self):
        df = _seed_uptrend_buys(n=10)
        f = compute_features_from_df(df, symbol="XAUUSD")
        assert f["cvd_divergence_flag"] is False

    def test_price_up_delta_down_flagged(self):
        # Price grinds up but every tick is sell-classified (absorption).
        rows = []
        for i in range(10):
            rows.append({
                "ts_utc": _bar_close() - timedelta(minutes=15) + timedelta(seconds=i * 30),
                "ts_msc": i,
                "bid": 100.0 + i * 0.05,
                "ask": 100.05 + i * 0.05,
                "last": 100.0 + i * 0.05,  # at bid → SELL
                "volume": 1.0, "flags": 2,
                "inferred_aggressor": "sell",
            })
        df = _make_df(rows)
        f = compute_features_from_df(df, symbol="XAUUSD")
        # Price moved up 0.45; cum_delta = -10 → divergence.
        assert f["cvd_divergence_flag"] is True


class TestMicroReversals:
    def test_zero_when_monotone(self):
        prices = [100.0, 100.1, 100.2, 100.3, 100.4]
        c = _count_micro_reversals(prices, threshold_dist=0.05)
        assert c == 0

    def test_one_reversal_after_threshold(self):
        # Up 1.0, down 0.6 (>= 0.5 threshold) → 1 reversal.
        prices = [100.0, 100.5, 101.0, 100.7, 100.4]
        c = _count_micro_reversals(prices, threshold_dist=0.5)
        assert c == 1

    def test_two_reversals_zigzag(self):
        prices = [100.0, 101.0, 99.0, 101.0, 99.0]
        # Threshold 0.5 → multiple legs.
        c = _count_micro_reversals(prices, threshold_dist=0.5)
        assert c >= 2

    def test_short_series_returns_zero(self):
        assert _count_micro_reversals([100.0], threshold_dist=0.5) == 0
        assert _count_micro_reversals([100.0, 101.0], threshold_dist=0.5) == 0


class TestTickVelocity:
    def test_velocity_proportional_to_count(self):
        df = _seed_uptrend_buys(n=30)
        f = compute_features_from_df(df, symbol="XAUUSD", bar_seconds=900.0)
        assert f["tick_velocity"] == pytest.approx(30 / 900.0)


# ---------------------------------------------------------------------------
# Sidecar I/O
# ---------------------------------------------------------------------------


class TestSidecar:
    def test_write_and_read_roundtrip(self, tmp_path: Path):
        sidecar_root = tmp_path / "pipeline_state"
        record = TickFeatures(
            schema_version=SCHEMA_VERSION,
            symbol="XAUUSD",
            candle_time_utc=_bar_close().isoformat(),
            bar_open_utc=(_bar_close() - timedelta(minutes=15)).isoformat(),
            bar_close_utc=_bar_close().isoformat(),
            n_ticks=5,
            features={"cumulative_delta": 3.0, "buy_pct": 0.6,
                       "spread_max_cents": 0.10, "aggressor_balance": 0.6,
                       "cvd_divergence_flag": False},
        )
        path = write_sidecar(record, sidecar_root=sidecar_root)
        assert path.exists()
        loaded = read_sidecar("XAUUSD", _bar_close(), sidecar_root=sidecar_root)
        assert loaded is not None
        assert loaded["symbol"] == "XAUUSD"
        assert loaded["n_ticks"] == 5
        assert loaded["features"]["cumulative_delta"] == 3.0

    def test_read_missing_returns_none(self, tmp_path: Path):
        sidecar_root = tmp_path / "pipeline_state"
        out = read_sidecar("XAUUSD", _bar_close(), sidecar_root=sidecar_root)
        assert out is None

    def test_sidecar_path_format(self, tmp_path: Path):
        sidecar_root = tmp_path / "ps"
        p = sidecar_path_for("US30_cash", _bar_close(), sidecar_root=sidecar_root)
        assert p.name == "03_tick_features_US30_cash_20260425T131500.json"


# ---------------------------------------------------------------------------
# compute_for_bar — top-level integration
# ---------------------------------------------------------------------------


class TestComputeForBar:
    def test_returns_none_when_no_parquet(self, tmp_path: Path):
        ticks_root = tmp_path / "ticks"
        sidecar_root = tmp_path / "ps"
        out = compute_for_bar(
            "XAUUSD", _bar_close(),
            ticks_root=ticks_root, sidecar_root=sidecar_root,
        )
        assert out is None

    def test_produces_record_when_parquet_present(self, tmp_path: Path):
        from src.components.tick_capture import write_ticks_parquet, parquet_path_for
        ticks_root = tmp_path / "ticks"
        sidecar_root = tmp_path / "ps"
        bar_close = _bar_close()
        bar_open = bar_close - timedelta(minutes=15)
        rows = []
        for i in range(20):
            ts = bar_open + timedelta(seconds=i * 30)
            rows.append({
                "ts_utc": ts,
                "ts_msc": int(ts.timestamp() * 1000),
                "bid": 100.0 + i * 0.01,
                "ask": 100.05 + i * 0.01,
                "last": 100.05 + i * 0.01,
                "volume": 1.0,
                "flags": 4,
                "inferred_aggressor": "buy",
            })
        path = parquet_path_for("XAUUSD", bar_close.date(), root=ticks_root)
        write_ticks_parquet(rows, path)

        record = compute_for_bar(
            "XAUUSD", bar_close,
            ticks_root=ticks_root, sidecar_root=sidecar_root,
        )
        assert record is not None
        assert record.n_ticks == 20
        assert record.symbol == "XAUUSD"
        assert record.features["cumulative_delta"] == 20.0
        # Sidecar persisted.
        assert (sidecar_root /
                f"03_tick_features_XAUUSD_{bar_close.strftime('%Y%m%dT%H%M%S')}.json"
                ).exists()

    def test_filters_to_bar_window(self, tmp_path: Path):
        """Ticks outside [bar_open, bar_close) must be excluded."""
        from src.components.tick_capture import write_ticks_parquet, parquet_path_for
        ticks_root = tmp_path / "ticks"
        sidecar_root = tmp_path / "ps"
        bar_close = _bar_close()
        bar_open = bar_close - timedelta(minutes=15)
        # 5 in-window ticks, 5 BEFORE the bar, 5 AFTER the bar.
        rows = []
        for i in range(5):
            ts = bar_open - timedelta(seconds=10) + timedelta(seconds=i)
            rows.append({"ts_utc": ts, "ts_msc": int(ts.timestamp() * 1000),
                          "bid": 100.0, "ask": 100.05, "last": 100.05,
                          "volume": 1.0, "flags": 4,
                          "inferred_aggressor": "buy"})
        for i in range(5):
            ts = bar_open + timedelta(seconds=i * 60)
            rows.append({"ts_utc": ts, "ts_msc": int(ts.timestamp() * 1000),
                          "bid": 100.0, "ask": 100.05, "last": 100.05,
                          "volume": 1.0, "flags": 4,
                          "inferred_aggressor": "buy"})
        for i in range(5):
            ts = bar_close + timedelta(seconds=i)
            rows.append({"ts_utc": ts, "ts_msc": int(ts.timestamp() * 1000),
                          "bid": 100.0, "ask": 100.05, "last": 100.05,
                          "volume": 1.0, "flags": 4,
                          "inferred_aggressor": "buy"})
        path = parquet_path_for("XAUUSD", bar_close.date(), root=ticks_root)
        write_ticks_parquet(rows, path)

        record = compute_for_bar("XAUUSD", bar_close,
                                  ticks_root=ticks_root,
                                  sidecar_root=sidecar_root)
        assert record is not None
        assert record.n_ticks == 5  # only the in-window ones
