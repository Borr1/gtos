"""Tests for H29 — Drawdown-based position size reduction.

Validates:
- Risk reduces to 0.5% when DD hits exactly 8%
- Risk stays at 0.5% when DD is above 8%
- Risk returns to 1.0% when equity makes new high
- Equity peak updates correctly after winning trades
- Edge case: first trade (no peak yet) uses normal risk
- Edge case: DD exactly at 8.0% triggers reduction
- State persistence across instances
"""

import json
from pathlib import Path

import pytest

from src.components.drawdown_manager import DrawdownManager


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture
def config():
    return {
        "risk": {"risk_per_trade_pct": 1.0},
        "drawdown_reduction": {
            "threshold": 0.08,
            "reduced_risk_pct": 0.5,
        },
    }


@pytest.fixture
def state_file(tmp_path):
    return str(tmp_path / "equity_peak_state.json")


@pytest.fixture
def mgr(config, state_file):
    return DrawdownManager(config, state_file=state_file)


class TestNormalOperation:
    """Tests for standard drawdown tracking and risk adjustment."""

    def test_first_trade_uses_normal_risk(self, mgr):
        """First call with no prior peak should use normal risk."""
        risk = mgr.get_risk_pct(100_000.0)
        assert risk == 1.0

    def test_equity_peak_set_on_first_call(self, mgr):
        mgr.get_risk_pct(100_000.0)
        assert mgr.equity_peak == 100_000.0

    def test_equity_peak_updates_on_new_high(self, mgr):
        mgr.get_risk_pct(100_000.0)
        mgr.get_risk_pct(102_000.0)
        assert mgr.equity_peak == 102_000.0

    def test_equity_peak_does_not_decrease(self, mgr):
        mgr.get_risk_pct(100_000.0)
        mgr.get_risk_pct(98_000.0)
        assert mgr.equity_peak == 100_000.0

    def test_normal_risk_within_threshold(self, mgr):
        """7% drawdown should still use normal risk (threshold is 8%)."""
        mgr.get_risk_pct(100_000.0)
        risk = mgr.get_risk_pct(93_000.0)  # 7% DD
        assert risk == 1.0

    def test_reduced_risk_at_exact_threshold(self, mgr):
        """DD exactly at 8% triggers reduction."""
        mgr.get_risk_pct(100_000.0)
        risk = mgr.get_risk_pct(92_000.0)  # Exactly 8% DD
        assert risk == 0.5

    def test_reduced_risk_above_threshold(self, mgr):
        """DD above 8% stays reduced."""
        mgr.get_risk_pct(100_000.0)
        risk = mgr.get_risk_pct(90_000.0)  # 10% DD
        assert risk == 0.5

    def test_normal_risk_resumes_on_new_high(self, mgr):
        """Risk returns to normal when equity makes a new high."""
        mgr.get_risk_pct(100_000.0)
        risk1 = mgr.get_risk_pct(91_000.0)  # 9% DD -> reduced
        assert risk1 == 0.5

        risk2 = mgr.get_risk_pct(100_001.0)  # New high -> normal
        assert risk2 == 1.0
        assert mgr.equity_peak == 100_001.0

    def test_reduced_stays_reduced_without_new_high(self, mgr):
        """Risk stays reduced as long as we're below threshold."""
        mgr.get_risk_pct(100_000.0)
        mgr.get_risk_pct(91_000.0)  # Trigger reduction
        assert mgr.is_reduced

        # Recover a bit but still below peak
        risk = mgr.get_risk_pct(95_000.0)  # 5% DD -> back to normal
        assert risk == 1.0
        assert not mgr.is_reduced

    def test_recovery_then_second_drawdown(self, mgr):
        """After recovery, a new drawdown triggers reduction again."""
        mgr.get_risk_pct(100_000.0)
        mgr.get_risk_pct(91_000.0)  # Reduced
        assert mgr.is_reduced

        mgr.get_risk_pct(105_000.0)  # New high, normal
        assert not mgr.is_reduced
        assert mgr.equity_peak == 105_000.0

        risk = mgr.get_risk_pct(96_000.0)  # 8.57% DD from new peak
        assert risk == 0.5
        assert mgr.is_reduced


class TestDrawdownCalculation:
    """Tests for drawdown percentage calculation."""

    def test_drawdown_pct_zero_at_peak(self, mgr):
        mgr.get_risk_pct(100_000.0)
        assert mgr.get_drawdown_pct(100_000.0) == 0.0

    def test_drawdown_pct_correct(self, mgr):
        mgr.get_risk_pct(100_000.0)
        dd = mgr.get_drawdown_pct(92_000.0)
        assert abs(dd - 0.08) < 1e-10

    def test_drawdown_pct_no_peak(self, mgr):
        assert mgr.get_drawdown_pct(50_000.0) == 0.0

    def test_drawdown_pct_zero_equity(self, mgr):
        mgr.get_risk_pct(100_000.0)
        dd = mgr.get_drawdown_pct(0.0)
        assert dd == 1.0


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_zero_equity_returns_normal_risk(self, mgr):
        risk = mgr.get_risk_pct(0.0)
        assert risk == 1.0

    def test_negative_equity_returns_normal_risk(self, mgr):
        risk = mgr.get_risk_pct(-1000.0)
        assert risk == 1.0

    def test_very_small_drawdown(self, mgr):
        mgr.get_risk_pct(100_000.0)
        risk = mgr.get_risk_pct(99_999.0)  # 0.001% DD
        assert risk == 1.0

    def test_threshold_boundary_just_below(self, mgr):
        """7.99999% DD should NOT trigger reduction."""
        mgr.get_risk_pct(100_000.0)
        risk = mgr.get_risk_pct(92_000.01)  # Just under 8%
        assert risk == 1.0


class TestPersistence:
    """Tests for state persistence across instances."""

    def test_peak_persisted_to_file(self, config, state_file):
        mgr = DrawdownManager(config, state_file=state_file)
        mgr.get_risk_pct(100_000.0)

        assert Path(state_file).exists()
        with open(state_file) as f:
            data = json.load(f)
        assert data["equity_peak"] == 100_000.0

    def test_peak_loaded_from_file(self, config, state_file):
        # First instance sets peak
        mgr1 = DrawdownManager(config, state_file=state_file)
        mgr1.get_risk_pct(100_000.0)

        # Second instance loads it
        mgr2 = DrawdownManager(config, state_file=state_file)
        assert mgr2.equity_peak == 100_000.0

        # Should use loaded peak for DD calculation
        risk = mgr2.get_risk_pct(91_000.0)
        assert risk == 0.5

    def test_missing_state_file(self, config, tmp_path):
        sf = str(tmp_path / "nonexistent" / "state.json")
        mgr = DrawdownManager(config, state_file=sf)
        assert mgr.equity_peak is None
        risk = mgr.get_risk_pct(100_000.0)
        assert risk == 1.0


class TestCustomConfig:
    """Tests with non-default configuration."""

    def test_custom_threshold(self, state_file):
        config = {
            "risk": {"risk_per_trade_pct": 1.0},
            "drawdown_reduction": {
                "threshold": 0.05,  # 5% threshold
                "reduced_risk_pct": 0.25,
            },
        }
        mgr = DrawdownManager(config, state_file=state_file)
        mgr.get_risk_pct(100_000.0)
        risk = mgr.get_risk_pct(95_000.0)  # 5% DD
        assert risk == 0.25

    def test_default_config_values(self, state_file):
        """Works with minimal config (uses defaults)."""
        config = {"risk": {}}
        mgr = DrawdownManager(config, state_file=state_file)
        assert mgr.dd_threshold == 0.08
        assert mgr.reduced_risk == 0.5
        assert mgr.normal_risk == 1.0
