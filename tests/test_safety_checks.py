"""Tests for deterministic safety checks in BacktestRunner._safety_check."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models.analysis_models import (
    DailyBiasAnalysis,
    H1SetupAnalysis,
    H4AlignmentAnalysis,
    LiquiditySweepAnalysis,
    M15ConfirmationAnalysis,
    PrimaryAnalysisOutput,
    PrimaryAnalysisReasoning,
    TradeParameters,
)
from src.models.market_state_models import (
    DataQuality,
    SessionLevels,
    StructureAnalysis,
    TimeframeState,
    MarketStateObject,
)


def _make_pa(
    direction: str = "LONG",
    daily_bias: str = "bullish",
    grade: str = "A",
    entry: float = 2900.0,
    sl: float = 2890.0,
    tp1: float = 2930.0,
    rr: float = 3.0,
    framework: str = "session_sweep",
) -> PrimaryAnalysisOutput:
    return PrimaryAnalysisOutput(
        timestamp_utc="2025-02-10T07:15:00Z",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=85,
        framework=framework,
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction=daily_bias, confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(poi_identified=True),
            liquidity_sweep=LiquiditySweepAnalysis(detected=True, pool_type="asian_low"),
            m15_confirmation=M15ConfirmationAnalysis(choch_detected=True, displacement_quality="strong"),
            setup_grade=grade,
        ),
        trade_parameters=TradeParameters(
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            take_profit_1=tp1,
            risk_reward_ratio=rr,
        ),
    )


def _make_mso(m15_atr: float = 3.0) -> MarketStateObject:
    return MarketStateObject(
        timestamp_utc="2025-02-10T07:15:00Z",
        timeframes={
            "M15": TimeframeState(
                structure=StructureAnalysis(direction="bullish"),
                atr_14=m15_atr,
            ),
        },
        session_levels=SessionLevels(
            asian_high=2910.0, asian_low=2890.0, pdh=2920.0, pdl=2880.0,
        ),
        data_quality=DataQuality(
            all_timeframes_complete=True, spread_normal=True,
            mt5_connected=False, timestamp_utc="2025-02-10T07:15:00Z",
        ),
    )


def _make_runner():
    """Create a BacktestRunner with mocked dependencies."""
    import sys
    sys.path.insert(0, ".")
    from scripts.backtest_runner import BacktestRunner

    with patch("scripts.backtest_runner.BacktestRunner._load_historical_candles", return_value={}):
        with patch("scripts.backtest_runner.yaml.safe_load", return_value={"ai": {}, "data": {}}):
            with patch("builtins.open", MagicMock()):
                with patch("scripts.backtest_runner.KnowledgeBase"):
                    with patch("scripts.backtest_runner.PrimaryAnalyzer"):
                        with patch("scripts.backtest_runner.DebateEngine"):
                            runner = BacktestRunner.__new__(BacktestRunner)
                            runner.config = {"ai": {}}
                            runner.debate_enabled = False
    return runner


class TestDirectionBiasMatch:
    def test_reject_short_when_daily_bullish(self):
        runner = _make_runner()
        pa = _make_pa(direction="SHORT", daily_bias="bullish")
        mso = _make_mso()
        result = runner._safety_check(pa, mso)
        assert result is not None
        assert "direction_mismatch" in result

    def test_reject_long_when_daily_bearish(self):
        runner = _make_runner()
        pa = _make_pa(direction="LONG", daily_bias="bearish")
        mso = _make_mso()
        result = runner._safety_check(pa, mso)
        assert result is not None
        assert "direction_mismatch" in result

    def test_accept_long_when_daily_bullish(self):
        runner = _make_runner()
        pa = _make_pa(direction="LONG", daily_bias="bullish")
        mso = _make_mso()
        result = runner._safety_check(pa, mso)
        assert result is None  # passes

    def test_accept_short_when_daily_bearish(self):
        runner = _make_runner()
        pa = _make_pa(direction="SHORT", daily_bias="bearish", entry=2900, sl=2910, tp1=2870)
        mso = _make_mso()
        result = runner._safety_check(pa, mso)
        assert result is None  # passes


class TestSLFloor:
    def test_reject_sl_below_5_dollars(self):
        runner = _make_runner()
        pa = _make_pa(entry=2900.0, sl=2896.0, tp1=2930.0)  # $4 SL
        mso = _make_mso(m15_atr=2.0)
        result = runner._safety_check(pa, mso)
        assert result is not None
        assert "sl_below_minimum_floor" in result

    def test_accept_sl_at_5_dollars(self):
        runner = _make_runner()
        pa = _make_pa(entry=2900.0, sl=2895.0, tp1=2930.0)  # $5 SL
        mso = _make_mso(m15_atr=3.0)
        result = runner._safety_check(pa, mso)
        assert result is None  # passes (5.0 >= 5.0 floor, 5.0 >= 1.5*3.0=4.5)


class TestATRCheck:
    def test_reject_sl_below_1_5x_atr(self):
        runner = _make_runner()
        # ATR=4.0, 1.5x=6.0, SL dist=5.5 → should reject
        pa = _make_pa(entry=2900.0, sl=2894.5, tp1=2930.0)
        mso = _make_mso(m15_atr=4.0)
        result = runner._safety_check(pa, mso)
        assert result is not None
        assert "sl_too_tight" in result

    def test_accept_sl_at_1_5x_atr(self):
        runner = _make_runner()
        # ATR=4.0, 1.5x=6.0, SL dist=6.5 → should pass
        pa = _make_pa(entry=2900.0, sl=2893.5, tp1=2930.0)
        mso = _make_mso(m15_atr=4.0)
        result = runner._safety_check(pa, mso)
        assert result is None


class TestAllChecksCombined:
    def test_all_checks_pass_valid_trade(self):
        runner = _make_runner()
        pa = _make_pa(
            direction="LONG", daily_bias="bullish", grade="A",
            entry=2900.0, sl=2890.0, tp1=2930.0, rr=3.0,
        )
        mso = _make_mso(m15_atr=3.0)
        # SL dist=10, floor=5 ✓, 1.5*ATR=4.5 ✓, dir matches ✓, grade A ✓
        result = runner._safety_check(pa, mso)
        assert result is None

    def test_grade_b_rejected(self):
        runner = _make_runner()
        pa = _make_pa(grade="B+")
        mso = _make_mso()
        result = runner._safety_check(pa, mso)
        assert result is not None
        assert "below_grade_threshold" in result


class TestBatchSafetyCheckOBRetest:
    """Tests for batch _safety_check with ob_retest framework."""

    def test_ob_retest_grade_a_passes(self):
        from scripts.batch_backtest import _safety_check
        pa = _make_pa(grade="A", framework="ob_retest")
        mso = _make_mso()
        result = _safety_check(pa, mso)
        assert result is None

    def test_ob_retest_grade_a_plus_passes(self):
        from scripts.batch_backtest import _safety_check
        pa = _make_pa(grade="A+", framework="ob_retest")
        mso = _make_mso()
        result = _safety_check(pa, mso)
        assert result is None

    def test_ob_retest_grade_b_rejected(self):
        from scripts.batch_backtest import _safety_check
        pa = _make_pa(grade="B+", framework="ob_retest")
        mso = _make_mso()
        result = _safety_check(pa, mso)
        assert result is not None
        assert "below_grade_threshold" in result
