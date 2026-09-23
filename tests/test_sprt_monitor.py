"""Tests for SPRT and CUSUM monitoring."""

import json
from pathlib import Path

import pytest

from src.components.sprt_monitor import (
    SPRTMonitor,
    UPPER_BOUNDARY,
    LOWER_BOUNDARY,
    INSTRUMENT_PARAMS,
)


class TestSPRTBasic:
    def test_initial_state_is_continue(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        result = monitor.update("XAUUSD", won=True)
        assert result.status == "CONTINUE"
        assert result.total_trades == 1
        assert result.wins == 1

    def test_many_wins_confirms(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        for _ in range(15):
            result = monitor.update("XAUUSD", won=True)
        assert result.status == "CONFIRM"
        assert result.cumulative_lambda >= UPPER_BOUNDARY

    def test_many_losses_kills(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        for _ in range(20):
            result = monitor.update("XAUUSD", won=False)
        assert result.status == "KILL"
        assert result.cumulative_lambda <= LOWER_BOUNDARY

    def test_mixed_results_continue(self, tmp_path):
        """Alternating wins/losses should stay in CONTINUE."""
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        for i in range(10):
            result = monitor.update("XAUUSD", won=(i % 2 == 0))
        assert result.status == "CONTINUE"

    def test_tracks_multiple_instruments(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        monitor.update("XAUUSD", won=True)
        monitor.update("US30", won=False)
        monitor.update("XAUUSD", won=True)

        xau = monitor.get_status("XAUUSD")
        us30 = monitor.get_status("US30")
        assert xau.total_trades == 2
        assert us30.total_trades == 1

    def test_unknown_instrument_defaults_to_xauusd_params(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        result = monitor.update("UNKNOWN_SYMBOL", won=True)
        assert result.status == "CONTINUE"


class TestSPRTPersistence:
    def test_saves_and_loads_state(self, tmp_path):
        state_path = str(tmp_path / "sprt.json")
        monitor = SPRTMonitor(state_path=state_path)
        monitor.update("XAUUSD", won=True)
        monitor.update("XAUUSD", won=True)
        monitor.update("US30", won=False)

        # Create new monitor from same path
        monitor2 = SPRTMonitor(state_path=state_path)
        xau = monitor2.get_status("XAUUSD")
        assert xau.wins == 2
        assert xau.total_trades == 2

    def test_no_crash_if_state_file_missing(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "nonexistent" / "sprt.json"))
        result = monitor.update("XAUUSD", won=True)
        assert result.status == "CONTINUE"


class TestCUSUM:
    def test_initial_no_signal(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        result = monitor.update_cusum("XAUUSD", won=True)
        assert not result.deterioration_signal
        assert not result.improvement_signal

    def test_consecutive_losses_signal_deterioration(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        for _ in range(20):
            result = monitor.update_cusum("XAUUSD", won=False)
        assert result.deterioration_signal

    def test_consecutive_wins_signal_improvement(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        for _ in range(20):
            result = monitor.update_cusum("XAUUSD", won=True)
        assert result.improvement_signal


class TestUpdateAll:
    def test_returns_both_results(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        sprt, cusum = monitor.update_all("XAUUSD", won=True)
        assert sprt.instrument == "XAUUSD"
        assert cusum.instrument == "XAUUSD"

    def test_get_all_statuses(self, tmp_path):
        monitor = SPRTMonitor(state_path=str(tmp_path / "sprt.json"))
        monitor.update("XAUUSD", won=True)
        monitor.update("US30", won=True)
        statuses = monitor.get_all_statuses()
        assert "XAUUSD" in statuses
        assert "US30" in statuses


class TestSPRTBoundaries:
    """Verify SPRT boundaries match validation framework."""

    def test_upper_boundary_approx_2_77(self):
        assert abs(UPPER_BOUNDARY - 2.773) < 0.01

    def test_lower_boundary_approx_neg_1_56(self):
        assert abs(LOWER_BOUNDARY - (-1.556)) < 0.01

    def test_xauusd_params_match_framework(self):
        params = INSTRUMENT_PARAMS["XAUUSD"]
        assert params["p0"] == 0.357
        assert params["p1"] == 0.620

    def test_gbpjpy_params_match_framework(self):
        params = INSTRUMENT_PARAMS["GBPJPY"]
        assert params["p0"] == 0.417
        assert params["p1"] == 0.571
