"""Tests for ``src/research_infra/decay_velocity.py``.

Methodology:
  - Hand-verified rolling-window math on 3 synthetic series.
  - Window < N trades → empty / short series (graceful).
  - Decay slope: known-slope synthetic series → recovered slope (within tol).
  - Per-instrument aggregation: 3-instrument tmp dir → 3 series.
  - p-value: synthetic null (random R) → high p; strong decay → low p.

All tests use ``tmp_path``; conftest write-guard prevents accidental writes
to production paths.
"""

from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research_infra.decay_velocity import (
    InstrumentVerdict,
    RollingSeries,
    SlopeResult,
    WindowPoint,
    build_per_instrument_verdicts,
    classify_verdict,
    decay_concentration,
    decay_slope,
    per_instrument_decay_velocity,
    rolling_window_wr_exp,
)


# ────────────────────────────────────────────────────────────────────────────
# Helper builders
# ────────────────────────────────────────────────────────────────────────────

def _trade(ts: datetime, r: float, *, symbol: str = "XAUUSD", framework: str = "ob_retest") -> dict:
    """Compact synthetic trade dict using the schema fields the loader looks at."""
    return {
        "trade_id": f"{symbol}_{ts.isoformat()}_{r:+.2f}",
        "symbol": symbol,
        "candle_close_time": ts.isoformat(),
        "direction": "LONG",
        "framework": framework,
        "exit": {"realized_R": r},
    }


def _series_walk(start: datetime, n: int, *, gap_minutes: int = 60) -> list[datetime]:
    """Linear timestamp walk."""
    return [start + timedelta(minutes=gap_minutes * i) for i in range(n)]


# ────────────────────────────────────────────────────────────────────────────
# rolling_window_wr_exp — hand-verified on 3 synthetic series
# ────────────────────────────────────────────────────────────────────────────

class TestRollingWindow:

    def test_alternating_wins_losses_window_4(self):
        """Series 1: alternating +1 / -1, window=4 → WR=0.5 every window."""
        ts = _series_walk(datetime(2026, 1, 1, tzinfo=timezone.utc), 12)
        rs = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
        trades = [_trade(t, r) for t, r in zip(ts, rs)]
        series = rolling_window_wr_exp(trades, window=4)
        assert series.symbol == "XAUUSD"
        assert series.window == 4
        assert series.total_trades == 12
        assert len(series) == 3  # 12 / 4
        for p in series.points:
            assert p.n == 4
            assert p.wr == 0.5
            assert p.exp_r == 0.0
        # window indexes 0, 1, 2
        assert [p.window_index for p in series.points] == [0, 1, 2]

    def test_all_wins_then_all_losses(self):
        """Series 2: 5 wins followed by 5 losses, window=5 → WR 1.0 then 0.0."""
        ts = _series_walk(datetime(2026, 1, 1, tzinfo=timezone.utc), 10)
        rs = [1.5, 1.5, 1.5, 1.5, 1.5, -1.0, -1.0, -1.0, -1.0, -1.0]
        trades = [_trade(t, r) for t, r in zip(ts, rs)]
        series = rolling_window_wr_exp(trades, window=5)
        assert len(series) == 2
        p0, p1 = series.points
        assert p0.wr == 1.0
        assert p0.exp_r == pytest.approx(1.5)
        assert p1.wr == 0.0
        assert p1.exp_r == pytest.approx(-1.0)

    def test_known_wr_75pct_window_4(self):
        """Series 3: 3 wins + 1 loss per window, window=4 → WR 0.75 each."""
        # Pattern: W W W L | W W W L
        ts = _series_walk(datetime(2026, 1, 1, tzinfo=timezone.utc), 8)
        rs = [2.0, 1.0, 1.5, -1.0, 2.0, 1.0, 1.5, -1.0]
        trades = [_trade(t, r) for t, r in zip(ts, rs)]
        series = rolling_window_wr_exp(trades, window=4)
        assert len(series) == 2
        for p in series.points:
            assert p.wr == 0.75
            assert p.exp_r == pytest.approx((2.0 + 1.0 + 1.5 - 1.0) / 4)


class TestRollingWindowEdgeCases:

    def test_empty_input_returns_empty_series(self):
        series = rolling_window_wr_exp([], window=50)
        assert series.is_empty
        assert series.total_trades == 0
        assert len(series) == 0

    def test_too_few_trades_for_window_returns_empty(self):
        ts = _series_walk(datetime(2026, 1, 1, tzinfo=timezone.utc), 10)
        trades = [_trade(t, 1.0) for t in ts]
        series = rolling_window_wr_exp(trades, window=50)
        assert series.is_empty
        assert series.total_trades == 10

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError):
            rolling_window_wr_exp([], window=1)
        with pytest.raises(ValueError):
            rolling_window_wr_exp([], window=0)

    def test_invalid_trades_type_raises(self):
        with pytest.raises(TypeError):
            rolling_window_wr_exp("not a list", window=10)  # type: ignore[arg-type]

    def test_filters_out_unfilled_trades(self):
        """Trades without realised R are skipped silently."""
        ts = _series_walk(datetime(2026, 1, 1, tzinfo=timezone.utc), 10)
        trades = [_trade(ts[i], 1.0) for i in range(5)] + [
            {"symbol": "XAUUSD", "candle_close_time": ts[i].isoformat()}
            for i in range(5, 10)
        ]
        series = rolling_window_wr_exp(trades, window=4)
        # only 5 valid trades remain → only 1 full window of 4
        assert series.total_trades == 5
        assert len(series) == 1
        assert series.points[0].wr == 1.0

    def test_unsorted_trades_are_sorted_by_time(self):
        """Unsorted input is sorted ascending before windowing."""
        ts = _series_walk(datetime(2026, 1, 1, tzinfo=timezone.utc), 4)
        # Build trades in REVERSE order
        trades = [
            _trade(ts[3], 1.0),
            _trade(ts[2], 1.0),
            _trade(ts[1], -1.0),
            _trade(ts[0], -1.0),
        ]
        series = rolling_window_wr_exp(trades, window=4)
        assert len(series) == 1
        # First two (original order) are losses, last two are wins → WR 0.5
        assert series.points[0].wr == 0.5

    def test_non_overlapping_windows(self):
        """Windows are non-overlapping (step == window)."""
        # 100 trades, window 50 → exactly 2 windows
        ts = _series_walk(datetime(2026, 1, 1, tzinfo=timezone.utc), 100)
        trades = [_trade(ts[i], 1.0 if i < 50 else -1.0) for i in range(100)]
        series = rolling_window_wr_exp(trades, window=50)
        assert len(series) == 2
        assert series.points[0].wr == 1.0
        assert series.points[1].wr == 0.0


# ────────────────────────────────────────────────────────────────────────────
# decay_slope — known-slope recovery
# ────────────────────────────────────────────────────────────────────────────

class TestDecaySlope:

    def test_known_decay_slope_recovered(self):
        """Synthetic series with WR linearly decaying 1.0 → 0.0 over 5 points."""
        ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Build a RollingSeries directly with chosen WR values
        points = tuple(
            WindowPoint(
                timestamp=ts0 + timedelta(days=30 * i),
                n=50,
                wr=1.0 - 0.25 * i,  # slope = -0.25 per window step
                exp_r=0.5 - 0.25 * i,
                window_index=i,
            )
            for i in range(5)
        )
        series = RollingSeries(symbol="X", window=50, points=points, total_trades=250)
        result = decay_slope(series)
        assert result.n_points == 5
        assert result.slope_per_window == pytest.approx(-0.25, abs=1e-9)
        # avg_window_days = 30 → slope_per_30d == slope_per_window
        assert result.slope_per_30d == pytest.approx(-0.25, abs=1e-9)
        # Perfect linear → r² = 1.0
        assert result.r_squared == pytest.approx(1.0, abs=1e-9)
        # Perfect linear → t-stat is infinite, p-value should be ~0
        # (or NaN due to division by zero residual; either is acceptable
        # for a perfect fit)
        assert math.isnan(result.p_value) or result.p_value < 1e-6

    def test_known_improvement_slope_recovered(self):
        """Synthetic series with WR linearly improving."""
        ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        points = tuple(
            WindowPoint(
                timestamp=ts0 + timedelta(days=30 * i),
                n=50,
                wr=0.5 + 0.10 * i,  # slope = +0.10
                exp_r=0.0,
                window_index=i,
            )
            for i in range(4)
        )
        series = RollingSeries(symbol="X", window=50, points=points, total_trades=200)
        result = decay_slope(series)
        assert result.slope_per_window == pytest.approx(0.10, abs=1e-9)
        assert result.slope_per_30d == pytest.approx(0.10, abs=1e-9)

    def test_constant_series_slope_is_zero(self):
        ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        points = tuple(
            WindowPoint(
                timestamp=ts0 + timedelta(days=30 * i),
                n=50,
                wr=0.6,
                exp_r=0.0,
                window_index=i,
            )
            for i in range(4)
        )
        series = RollingSeries(symbol="X", window=50, points=points, total_trades=200)
        result = decay_slope(series)
        assert result.slope_per_window == pytest.approx(0.0, abs=1e-9)
        # ssyy == 0 → r² is NaN (legitimate edge case, no variance to explain)
        # and p-value is NaN (no residual variance to test against)
        assert math.isnan(result.p_value) or result.p_value > 0.5

    def test_too_few_points_returns_nan(self):
        ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # 1 point → cannot regress
        points = (
            WindowPoint(timestamp=ts0, n=50, wr=0.6, exp_r=0.0, window_index=0),
        )
        series = RollingSeries(symbol="X", window=50, points=points, total_trades=50)
        result = decay_slope(series)
        assert math.isnan(result.slope_per_window)
        assert math.isnan(result.p_value)

    def test_empty_series_returns_nan(self):
        series = RollingSeries(symbol="X", window=50, points=tuple(), total_trades=0)
        result = decay_slope(series)
        assert math.isnan(result.slope_per_window)
        assert result.n_points == 0


# ────────────────────────────────────────────────────────────────────────────
# Per-instrument aggregation
# ────────────────────────────────────────────────────────────────────────────

class TestPerInstrumentAggregation:

    def _write_record(self, dirpath: Path, symbol: str, idx: int, ts: datetime, r: float | None) -> Path:
        """Write a single trade-record JSON file matching the live schema."""
        rec: dict = {
            "metadata": {
                "trade_id": f"{symbol}_{idx:04d}_{ts.isoformat()}",
                "date": ts.date().isoformat(),
                "symbol": symbol,
                "candle_time": ts.isoformat(),
            },
            "decision_pipeline": {"final_outcome": "FILLED" if r is not None else "REJECTED_L2"},
            "exit": ({"realized_R": r} if r is not None else None),
            "execution": ({"order_id": idx} if r is not None else None),
        }
        fp = dirpath / f"{ts.date().isoformat()}_{idx:04d}.json"
        fp.write_text(json.dumps(rec), encoding="utf-8")
        return fp

    def test_three_instruments_three_series(self, tmp_path: Path):
        """Trade-records dir with 3 instruments → 3 series in output."""
        base = tmp_path / "trade_records"
        base.mkdir()

        # XAU: 100 filled, 50 rejected (only filled count toward windows)
        xau_dir = base / "XAUUSD"
        xau_dir.mkdir()
        ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        for i in range(100):
            self._write_record(xau_dir, "XAUUSD", i, ts0 + timedelta(hours=i),
                               1.0 if i % 2 == 0 else -1.0)
        for i in range(100, 150):
            self._write_record(xau_dir, "XAUUSD", i, ts0 + timedelta(hours=i), None)

        # USDJPY: 50 filled
        usd_dir = base / "USDJPY"
        usd_dir.mkdir()
        for i in range(50):
            self._write_record(usd_dir, "USDJPY", i, ts0 + timedelta(hours=i), 1.5)

        # GBPJPY: 5 filled (insufficient for window=50)
        gbp_dir = base / "GBPJPY"
        gbp_dir.mkdir()
        for i in range(5):
            self._write_record(gbp_dir, "GBPJPY", i, ts0 + timedelta(hours=i), 1.0)

        result = per_instrument_decay_velocity(base, window=50)
        assert set(result.keys()) == {"XAUUSD", "USDJPY", "GBPJPY"}
        # XAUUSD: 100 filled / 50 = 2 windows
        assert result["XAUUSD"].total_trades == 100
        assert len(result["XAUUSD"]) == 2
        for p in result["XAUUSD"].points:
            assert p.wr == 0.5
        # USDJPY: 50 / 50 = 1 window, all wins
        assert result["USDJPY"].total_trades == 50
        assert len(result["USDJPY"]) == 1
        assert result["USDJPY"].points[0].wr == 1.0
        # GBPJPY: 5 / 50 → 0 windows
        assert result["GBPJPY"].total_trades == 5
        assert len(result["GBPJPY"]) == 0

    def test_symbols_filter(self, tmp_path: Path):
        """The ``symbols`` arg restricts which dirs are read."""
        base = tmp_path / "trade_records"
        base.mkdir()
        for sym in ("XAUUSD", "USDJPY", "GBPJPY"):
            (base / sym).mkdir()
            ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
            for i in range(60):
                self._write_record(base / sym, sym, i, ts0 + timedelta(hours=i), 1.0)
        # Filter to only XAUUSD
        result = per_instrument_decay_velocity(base, window=50, symbols=["XAUUSD"])
        assert set(result.keys()) == {"XAUUSD"}

    def test_missing_dir_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            per_instrument_decay_velocity(tmp_path / "nope", window=50)

    def test_aux_index_merge(self, tmp_path: Path):
        """Trades from aux_index_path are merged into per-symbol lists."""
        base = tmp_path / "trade_records"
        base.mkdir()
        # Empty trade_records dir; all trades come from aux index
        aux = tmp_path / "_trade_index.json"
        ts0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        trades = [
            {
                "trade_id": f"bt_{i:03d}",
                "symbol": "XAUUSD",
                "date": (ts0 + timedelta(days=i)).date().isoformat(),
                "r_multiple": 1.0 if i % 3 != 0 else -1.0,
            }
            for i in range(60)
        ]
        aux.write_text(json.dumps({"trades": trades}), encoding="utf-8")
        result = per_instrument_decay_velocity(base, window=50, aux_index_path=aux)
        assert "XAUUSD" in result
        assert result["XAUUSD"].total_trades == 60
        assert len(result["XAUUSD"]) == 1


# ────────────────────────────────────────────────────────────────────────────
# p-value behaviour: null vs strong-decay
# ────────────────────────────────────────────────────────────────────────────

class TestPValueBehaviour:

    def test_null_series_high_p(self):
        """No-decay synthetic series → p-value should be high (≫ 0.05)."""
        rng = random.Random(42)
        ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # 6 windows; WR drawn from N(0.6, 0.05) — no trend
        points = tuple(
            WindowPoint(
                timestamp=ts0 + timedelta(days=30 * i),
                n=50,
                wr=0.6 + rng.gauss(0, 0.05),
                exp_r=0.0,
                window_index=i,
            )
            for i in range(6)
        )
        series = RollingSeries(symbol="X", window=50, points=points, total_trades=300)
        result = decay_slope(series)
        # Slope ≈ 0; p-value should NOT reject the null
        assert math.isfinite(result.p_value)
        assert result.p_value > 0.05

    def test_strong_decay_low_p(self):
        """Strong-decay synthetic series → low p-value."""
        ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # WR collapses 0.85 → 0.25 over 5 points (slope = -0.15 per step)
        # Add small noise to keep r² < 1 and p computable
        rng = random.Random(7)
        points = tuple(
            WindowPoint(
                timestamp=ts0 + timedelta(days=30 * i),
                n=50,
                wr=0.85 - 0.15 * i + rng.gauss(0, 0.005),
                exp_r=0.0,
                window_index=i,
            )
            for i in range(5)
        )
        series = RollingSeries(symbol="X", window=50, points=points, total_trades=250)
        result = decay_slope(series)
        assert math.isfinite(result.p_value)
        assert result.p_value < 0.001
        assert result.slope_per_window < 0


# ────────────────────────────────────────────────────────────────────────────
# Verdict classification
# ────────────────────────────────────────────────────────────────────────────

class TestVerdictClassification:

    def test_decaying_label(self):
        s = SlopeResult(slope_per_window=-0.05, slope_per_30d=-0.05, intercept=0.7,
                        p_value=0.002, r_squared=0.9, n_points=5, avg_window_days=30.0)
        assert classify_verdict(s, n_total=100, p_corrected=0.014, alpha=0.05) == "DECAYING"

    def test_improving_label(self):
        s = SlopeResult(slope_per_window=0.04, slope_per_30d=0.04, intercept=0.5,
                        p_value=0.001, r_squared=0.95, n_points=5, avg_window_days=30.0)
        assert classify_verdict(s, n_total=80, p_corrected=0.007, alpha=0.05) == "IMPROVING"

    def test_insufficient_n(self):
        s = SlopeResult(slope_per_window=-0.1, slope_per_30d=-0.1, intercept=0.5,
                        p_value=0.01, r_squared=0.99, n_points=2, avg_window_days=30.0)
        assert classify_verdict(s, n_total=15, p_corrected=0.07, alpha=0.05) == "INSUFFICIENT_N"

    def test_stable_label(self):
        s = SlopeResult(slope_per_window=0.001, slope_per_30d=0.001, intercept=0.6,
                        p_value=0.6, r_squared=0.05, n_points=5, avg_window_days=30.0)
        assert classify_verdict(s, n_total=200, p_corrected=1.0, alpha=0.05) == "STABLE"

    def test_inconclusive_label(self):
        s = SlopeResult(slope_per_window=-0.04, slope_per_30d=-0.04, intercept=0.6,
                        p_value=0.30, r_squared=0.4, n_points=5, avg_window_days=30.0)
        assert classify_verdict(s, n_total=200, p_corrected=2.1, alpha=0.05) == "INCONCLUSIVE"


# ────────────────────────────────────────────────────────────────────────────
# Bonferroni correction in build_per_instrument_verdicts
# ────────────────────────────────────────────────────────────────────────────

class TestBonferroniBuild:

    def test_bonferroni_applied(self):
        """raw p × N_tested comes out as p_corrected."""
        ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

        def linear_decay_series(symbol: str, slope: float, seed: int, n_points: int = 5) -> RollingSeries:
            # Add small noise so OLS residual variance is nonzero
            rng = random.Random(seed)
            return RollingSeries(
                symbol=symbol,
                window=50,
                points=tuple(
                    WindowPoint(
                        timestamp=ts0 + timedelta(days=30 * i),
                        n=50,
                        wr=0.7 + slope * i + rng.gauss(0, 0.01),
                        exp_r=0.0,
                        window_index=i,
                    )
                    for i in range(n_points)
                ),
                total_trades=50 * n_points,
            )

        # 3 instruments tested, all with same slope but distinct noise seeds
        series_map = {
            "AAA": linear_decay_series("AAA", -0.05, seed=1),
            "BBB": linear_decay_series("BBB", -0.05, seed=2),
            "CCC": linear_decay_series("CCC", -0.05, seed=3),
        }

        # Build trades (used only for H1/H2 split)
        trades_map = {sym: [
            {"symbol": sym, "candle_close_time": (ts0 + timedelta(hours=i)).isoformat(),
             "exit": {"realized_R": (1.0 if i % 2 == 0 else -1.0)}}
            for i in range(50 * 5)
        ] for sym in series_map}

        verdicts = build_per_instrument_verdicts(series_map, trades_map, n_min=20, alpha=0.05)
        # All three produced a finite raw p-value (no NaN), so bonferroni_n=3
        for sym, v in verdicts.items():
            assert math.isfinite(v.p_value_raw)
            # Allow rounding equality
            expected_corr = min(1.0, v.p_value_raw * 3)
            assert v.p_value_bonferroni == pytest.approx(expected_corr, rel=1e-9)

    def test_bonferroni_capped_at_1(self):
        """p × N_tested cannot exceed 1.0."""
        ts0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Synthetic series with intentionally high p
        flat_points = tuple(
            WindowPoint(timestamp=ts0 + timedelta(days=30 * i), n=50,
                        wr=0.6 + (0.001 if i % 2 else -0.001),
                        exp_r=0.0, window_index=i)
            for i in range(5)
        )
        series_map = {f"S{i}": RollingSeries(
            symbol=f"S{i}", window=50, points=flat_points, total_trades=250
        ) for i in range(7)}
        trades_map = {sym: [{"symbol": sym, "candle_close_time": ts0.isoformat(),
                              "exit": {"realized_R": 0.5}}] for sym in series_map}
        verdicts = build_per_instrument_verdicts(series_map, trades_map, n_min=20, alpha=0.05)
        for v in verdicts.values():
            assert 0.0 <= v.p_value_bonferroni <= 1.0


# ────────────────────────────────────────────────────────────────────────────
# Concentration heuristic
# ────────────────────────────────────────────────────────────────────────────

class TestConcentration:

    def _verdict(self, sym: str, label: str) -> InstrumentVerdict:
        return InstrumentVerdict(
            symbol=sym,
            n_total=100, n_windows=2,
            h1_wr=0.6, h2_wr=0.5,
            slope_per_30d=-0.01, slope_per_window=-0.01,
            p_value_raw=0.5, p_value_bonferroni=1.0,
            avg_window_days=30.0,
            verdict=label,
        )

    def test_no_decay_uniform(self):
        verdicts = {
            "A": self._verdict("A", "STABLE"),
            "B": self._verdict("B", "STABLE"),
            "C": self._verdict("C", "INSUFFICIENT_N"),
        }
        label, _ = decay_concentration(verdicts)
        assert label == "UNIFORM"

    def test_one_decaying_concentrated(self):
        verdicts = {
            "A": self._verdict("A", "DECAYING"),
            "B": self._verdict("B", "STABLE"),
            "C": self._verdict("C", "STABLE"),
        }
        label, _ = decay_concentration(verdicts)
        assert label == "CONCENTRATED_ON_A"

    def test_two_decaying_concentrated(self):
        verdicts = {
            "A": self._verdict("A", "DECAYING"),
            "B": self._verdict("B", "DECAYING"),
            "C": self._verdict("C", "STABLE"),
        }
        label, _ = decay_concentration(verdicts)
        assert label == "CONCENTRATED_ON_A,B"

    def test_three_or_more_decaying_uniform(self):
        verdicts = {
            "A": self._verdict("A", "DECAYING"),
            "B": self._verdict("B", "DECAYING"),
            "C": self._verdict("C", "DECAYING"),
            "D": self._verdict("D", "STABLE"),
        }
        label, _ = decay_concentration(verdicts)
        assert label == "UNIFORM"


# ────────────────────────────────────────────────────────────────────────────
# Trade extraction (private but covered for confidence)
# ────────────────────────────────────────────────────────────────────────────

class TestTradeExtraction:

    def test_alternative_realized_r_field_names(self):
        """The loader honours all documented realised-R field aliases."""
        from src.research_infra.decay_velocity import _extract_realized_r
        cases = [
            ({"realized_r": 1.5}, 1.5),
            ({"realized_R": 1.5}, 1.5),
            ({"actual_r": 1.5}, 1.5),
            ({"actual_R": 1.5}, 1.5),
            ({"r_multiple": 1.5}, 1.5),
            ({"rR": 1.5}, 1.5),
            ({"exit": {"realized_R": 1.5}}, 1.5),
            ({"exit": {"actual_r": 1.5}}, 1.5),
            ({"unrelated_field": 99}, None),
            ({}, None),
            ({"realized_r": float("nan")}, None),  # NaN excluded by _is_filled
        ]
        for trade, expected in cases:
            got = _extract_realized_r(trade)
            if expected is None:
                assert got is None or (got != got)  # NaN
            else:
                assert got == expected

    def test_alternative_timestamp_fields(self):
        """The loader pulls timestamps from common fields."""
        from src.research_infra.decay_velocity import _extract_timestamp
        ts = datetime(2026, 1, 15, 13, 15, tzinfo=timezone.utc)
        for k in ("candle_close_time", "candle_time", "timestamp", "exit_time"):
            t = _extract_timestamp({k: ts.isoformat()})
            assert t == ts
        # date-only shorthand
        t = _extract_timestamp({"date": "2026-01-15"})
        assert t == datetime(2026, 1, 15, tzinfo=timezone.utc)
        # nested under metadata
        t = _extract_timestamp({"metadata": {"candle_time": ts.isoformat()}})
        assert t == ts
        assert _extract_timestamp({}) is None
