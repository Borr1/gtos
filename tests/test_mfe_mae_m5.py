"""Tests for the M5-based MFE/MAE computation in the orchestrator."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import pytest


def _make_orchestrator_stub():
    """Create a minimal orchestrator with just the MFE/MAE method."""
    from src.components.orchestrator import SessionOrchestrator

    stub = MagicMock(spec=SessionOrchestrator)
    stub._mt5_symbol = "XAUUSD"
    stub.mt5 = MagicMock()
    # Bind the real methods used by the M5 analytics path.
    stub._parse_utc_datetime = SessionOrchestrator._parse_utc_datetime
    stub._bar_time_utc = SessionOrchestrator._bar_time_utc
    stub._m5_rates_inside_trade_window = (
        SessionOrchestrator._m5_rates_inside_trade_window.__get__(stub)
    )
    stub._compute_mfe_mae_m5 = SessionOrchestrator._compute_mfe_mae_m5.__get__(stub)
    stub._compute_shadow_exit_fields = (
        SessionOrchestrator._compute_shadow_exit_fields.__get__(stub)
    )
    return stub


def _make_bars(bars: list[dict]) -> list[dict]:
    """Convert bar dicts to the wrapper format (ISO string times)."""
    result = []
    for b in bars:
        t = b["time"]
        result.append({
            "time": t.isoformat() if isinstance(t, datetime) else t,
            "open": b.get("open", b["low"]),
            "high": b["high"],
            "low": b["low"],
            "close": b.get("close", b["high"]),
            "volume": b.get("volume", 0),
        })
    return result


class TestMfeMaeM5:
    """Test _compute_mfe_mae_m5 with mocked MT5 wrapper data."""

    @pytest.fixture
    def orch(self):
        return _make_orchestrator_stub()

    def test_long_trade_basic(self, orch):
        entry = datetime(2026, 4, 7, 8, 0, tzinfo=timezone.utc)
        exit_ = datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc)
        entry_price = 3050.0
        sl_distance = 10.0  # SL at 3040

        bars = _make_bars([
            {"time": entry + timedelta(minutes=5),  "high": 3055.0, "low": 3048.0},
            {"time": entry + timedelta(minutes=10), "high": 3060.0, "low": 3050.0},  # MFE = +1.0R
            {"time": entry + timedelta(minutes=15), "high": 3052.0, "low": 3042.0},  # MAE = -0.8R
            {"time": entry + timedelta(minutes=20), "high": 3058.0, "low": 3053.0},
        ])
        orch.mt5.get_candles_range.return_value = bars

        result = orch._compute_mfe_mae_m5(entry_price, "LONG", entry, exit_, sl_distance)

        assert result is not None
        assert result["mfe_r_m5"] == 1.0    # (3060-3050)/10
        assert result["mae_r_m5"] == -0.8   # -(3050-3042)/10
        assert result["mfe_time_minutes"] == 10
        assert result["mae_time_minutes"] == 15

    def test_short_trade_basic(self, orch):
        entry = datetime(2026, 4, 7, 14, 0, tzinfo=timezone.utc)
        exit_ = datetime(2026, 4, 7, 15, 0, tzinfo=timezone.utc)
        entry_price = 3050.0
        sl_distance = 10.0  # SL at 3060

        bars = _make_bars([
            {"time": entry + timedelta(minutes=5),  "high": 3052.0, "low": 3040.0},  # MFE = +1.0R
            {"time": entry + timedelta(minutes=10), "high": 3058.0, "low": 3045.0},  # MAE = -0.8R
            {"time": entry + timedelta(minutes=15), "high": 3048.0, "low": 3035.0},  # MFE = +1.5R
        ])
        orch.mt5.get_candles_range.return_value = bars

        result = orch._compute_mfe_mae_m5(entry_price, "SHORT", entry, exit_, sl_distance)

        assert result is not None
        assert result["mfe_r_m5"] == 1.5    # (3050-3035)/10
        assert result["mae_r_m5"] == -0.8   # -(3058-3050)/10
        assert result["mfe_time_minutes"] == 15
        assert result["mae_time_minutes"] == 10

    def test_no_mt5_data_returns_none(self, orch):
        entry = datetime(2026, 4, 7, 8, 0, tzinfo=timezone.utc)
        exit_ = datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc)

        orch.mt5.get_candles_range.return_value = []
        result = orch._compute_mfe_mae_m5(3050.0, "LONG", entry, exit_, 10.0)

        assert result is None

    def test_missing_params_returns_none(self, orch):
        assert orch._compute_mfe_mae_m5(None, "LONG", None, None, 10.0) is None
        assert orch._compute_mfe_mae_m5(3050.0, "LONG", None, None, 0) is None

    def test_zero_sl_returns_none(self, orch):
        entry = datetime(2026, 4, 7, 8, 0, tzinfo=timezone.utc)
        exit_ = datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc)
        assert orch._compute_mfe_mae_m5(3050.0, "LONG", entry, exit_, 0) is None

    def test_single_bar(self, orch):
        entry = datetime(2026, 4, 7, 8, 0, tzinfo=timezone.utc)
        exit_ = datetime(2026, 4, 7, 8, 10, tzinfo=timezone.utc)
        bars = _make_bars([
            {"time": entry + timedelta(minutes=5), "high": 3055.0, "low": 3047.0},
        ])
        orch.mt5.get_candles_range.return_value = bars

        result = orch._compute_mfe_mae_m5(3050.0, "LONG", entry, exit_, 10.0)

        assert result is not None
        assert result["mfe_r_m5"] == 0.5   # (3055-3050)/10
        assert result["mae_r_m5"] == -0.3  # -(3050-3047)/10

    def test_flat_trade_no_excursion(self, orch):
        entry = datetime(2026, 4, 7, 8, 0, tzinfo=timezone.utc)
        exit_ = datetime(2026, 4, 7, 8, 10, tzinfo=timezone.utc)
        bars = _make_bars([
            {"time": entry + timedelta(minutes=5), "high": 3050.0, "low": 3050.0},
        ])
        orch.mt5.get_candles_range.return_value = bars

        result = orch._compute_mfe_mae_m5(3050.0, "LONG", entry, exit_, 10.0)

        assert result["mfe_r_m5"] == 0.0
        assert result["mae_r_m5"] == 0.0

    def test_ignores_pre_entry_and_post_exit_bars(self, orch):
        entry = datetime(2026, 6, 2, 9, 20, tzinfo=timezone.utc)
        exit_ = datetime(2026, 6, 2, 9, 40, tzinfo=timezone.utc)
        bars = _make_bars([
            {"time": entry - timedelta(minutes=5), "high": 3080.0, "low": 3040.0},
            {"time": entry + timedelta(minutes=5), "high": 3055.0, "low": 3047.0},
            {"time": exit_, "high": 3090.0, "low": 3000.0},
        ])
        orch.mt5.get_candles_range.return_value = bars

        result = orch._compute_mfe_mae_m5(3050.0, "LONG", entry, exit_, 10.0)

        assert result is not None
        assert result["mfe_r_m5"] == 0.5
        assert result["mae_r_m5"] == -0.3
        assert result["mfe_time_minutes"] == 5
        assert result["mae_time_minutes"] == 5

    def test_shadow_exit_ignores_out_of_window_tp_hits(self, orch):
        entry = datetime(2026, 6, 2, 9, 20, tzinfo=timezone.utc)
        exit_ = datetime(2026, 6, 2, 9, 40, tzinfo=timezone.utc)
        bars = _make_bars([
            {"time": entry - timedelta(minutes=5), "high": 3080.0, "low": 3040.0},
            {"time": entry + timedelta(minutes=5), "high": 3055.0, "low": 3047.0},
            {"time": exit_, "high": 3090.0, "low": 3000.0},
        ])
        orch.mt5.get_candles_range.return_value = bars

        shadow = orch._compute_shadow_exit_fields(
            entry_price=3050.0,
            sl_price=3040.0,
            direction="LONG",
            entry_time=entry,
            exit_time=exit_,
        )

        assert shadow["shadow_tp_1.0R_hit"] is False
        assert shadow["shadow_tp_1.5R_hit"] is False
        assert shadow["shadow_mae_candle_1"] == 0.3
