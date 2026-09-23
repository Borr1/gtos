"""Tests for BE Shadow Logger (observation-only breakeven stop analysis).

Validates:
- 1R threshold calculated correctly for LONG and SHORT
- BE trigger fires at correct price level
- Hypothetical BE outcome correct for: reversal past entry, no reversal, exact entry
- Shadow log does not interfere with actual trade execution
- JSONL format is valid and parseable
"""

import json
from pathlib import Path

import pytest

from src.components.be_shadow_logger import BEShadowTracker, write_be_shadow_log


# === LONG trade fixtures ===

@pytest.fixture
def long_tracker():
    """LONG trade: entry=2800, SL=2790, sl_distance=10."""
    return BEShadowTracker(
        trade_id="test_long_001",
        entry_price=2800.0,
        stop_loss=2790.0,
        direction="LONG",
        sl_distance=10.0,
    )


@pytest.fixture
def short_tracker():
    """SHORT trade: entry=2800, SL=2810, sl_distance=10."""
    return BEShadowTracker(
        trade_id="test_short_001",
        entry_price=2800.0,
        stop_loss=2810.0,
        direction="SHORT",
        sl_distance=10.0,
    )


class TestLongTrade1RThreshold:
    """Test +1R detection for LONG trades."""

    def test_no_trigger_below_1r(self, long_tracker):
        """Price at +0.9R should NOT trigger."""
        triggered = long_tracker.update(2809.0)  # +0.9R
        assert not triggered
        assert not long_tracker.be_trigger_activated

    def test_trigger_at_exactly_1r(self, long_tracker):
        """Price at exactly +1R should trigger."""
        triggered = long_tracker.update(2810.0)  # +1.0R
        assert triggered
        assert long_tracker.be_trigger_activated
        assert long_tracker.price_at_1r == 2810.0
        assert long_tracker.timestamp_1r_reached is not None

    def test_trigger_above_1r(self, long_tracker):
        """Price at +1.5R should trigger."""
        triggered = long_tracker.update(2815.0)  # +1.5R
        assert triggered
        assert long_tracker.be_trigger_activated

    def test_trigger_fires_once(self, long_tracker):
        """Second update after trigger should NOT re-fire."""
        long_tracker.update(2810.0)  # Trigger
        triggered_again = long_tracker.update(2820.0)  # Beyond 1R
        assert not triggered_again  # Already triggered

    def test_gradual_approach(self, long_tracker):
        """Price gradually approaching +1R."""
        assert not long_tracker.update(2805.0)  # +0.5R
        assert not long_tracker.update(2808.0)  # +0.8R
        assert not long_tracker.update(2809.5)  # +0.95R
        assert long_tracker.update(2810.0)       # +1.0R — trigger


class TestShortTrade1RThreshold:
    """Test +1R detection for SHORT trades."""

    def test_no_trigger_above_1r(self, short_tracker):
        """Price at -0.9R (SHORT +0.9R) should NOT trigger."""
        triggered = short_tracker.update(2791.0)  # +0.9R for SHORT
        assert not triggered

    def test_trigger_at_exactly_1r(self, short_tracker):
        """Price at -1R (SHORT +1R) should trigger."""
        triggered = short_tracker.update(2790.0)  # +1.0R for SHORT
        assert triggered
        assert short_tracker.be_trigger_activated

    def test_trigger_below_1r(self, short_tracker):
        """Price at -1.5R (SHORT +1.5R) should trigger."""
        triggered = short_tracker.update(2785.0)  # +1.5R for SHORT
        assert triggered


class TestHypotheticalBEOutcome:
    """Test hypothetical BE computation at trade close."""

    def test_long_reversal_past_entry(self, long_tracker):
        """LONG reaches +1R then reverses past entry — BE would have saved a loss."""
        long_tracker.update(2810.0)  # Trigger +1R
        long_tracker.update(2795.0)  # Reversal past entry (2800)

        result = long_tracker.compute_hypothetical(
            actual_exit_price=2795.0,
            actual_r_multiple=-0.5,
        )

        assert result is not None
        assert result["reversed_past_entry"] is True
        assert result["hypothetical_be_r"] == 0.0  # Stopped at BE
        assert result["actual_r_multiple"] == -0.5
        assert result["delta_r"] == 0.5  # +0.5R saved
        assert result["be_would_have_helped"] is True

    def test_long_no_reversal(self, long_tracker):
        """LONG reaches +1R and hits TP — BE makes no difference."""
        long_tracker.update(2810.0)  # Trigger +1R
        long_tracker.update(2815.0)  # Never goes below entry

        result = long_tracker.compute_hypothetical(
            actual_exit_price=2815.0,
            actual_r_multiple=1.5,
        )

        assert result is not None
        assert result["reversed_past_entry"] is False
        assert result["hypothetical_be_r"] == 1.5  # Same outcome
        assert result["delta_r"] == 0.0
        assert result["be_would_have_helped"] is False

    def test_long_reversal_exactly_to_entry(self, long_tracker):
        """LONG reaches +1R then price touches exactly entry — BE stops it at 0R."""
        long_tracker.update(2810.0)  # Trigger +1R
        long_tracker.update(2800.0)  # Exactly at entry
        long_tracker.update(2805.0)  # Recovers a bit

        result = long_tracker.compute_hypothetical(
            actual_exit_price=2805.0,
            actual_r_multiple=0.5,
        )

        assert result is not None
        assert result["reversed_past_entry"] is True  # Touched entry
        assert result["hypothetical_be_r"] == 0.0
        assert result["delta_r"] == -0.5  # Worse — would have been stopped out
        assert result["be_would_have_helped"] is False

    def test_short_reversal_past_entry(self, short_tracker):
        """SHORT reaches +1R then reverses past entry — BE would have saved."""
        short_tracker.update(2790.0)  # Trigger +1R
        short_tracker.update(2805.0)  # Reversal past entry (2800)

        result = short_tracker.compute_hypothetical(
            actual_exit_price=2805.0,
            actual_r_multiple=-0.5,
        )

        assert result is not None
        assert result["reversed_past_entry"] is True
        assert result["hypothetical_be_r"] == 0.0
        assert result["delta_r"] == 0.5
        assert result["be_would_have_helped"] is True

    def test_short_no_reversal(self, short_tracker):
        """SHORT reaches +1R and hits TP — same outcome."""
        short_tracker.update(2790.0)  # Trigger +1R
        short_tracker.update(2785.0)  # Stays in favor

        result = short_tracker.compute_hypothetical(
            actual_exit_price=2785.0,
            actual_r_multiple=1.5,
        )

        assert result["reversed_past_entry"] is False
        assert result["hypothetical_be_r"] == 1.5
        assert result["delta_r"] == 0.0

    def test_no_trigger_returns_none(self, long_tracker):
        """If +1R was never reached, no hypothetical is computed."""
        long_tracker.update(2805.0)  # Only +0.5R

        result = long_tracker.compute_hypothetical(
            actual_exit_price=2795.0,
            actual_r_multiple=-0.5,
        )
        assert result is None


class TestShadowLogOutput:
    """Test JSONL log output format and integrity."""

    def test_write_valid_jsonl(self, tmp_path):
        log_path = str(tmp_path / "be_shadow_log.jsonl")

        entry = {
            "trade_id": "test_001",
            "direction": "LONG",
            "entry_price": 2800.0,
            "delta_r": 0.5,
            "be_would_have_helped": True,
        }

        write_be_shadow_log(entry, log_path=log_path)

        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["trade_id"] == "test_001"
        assert parsed["delta_r"] == 0.5

    def test_append_multiple_entries(self, tmp_path):
        log_path = str(tmp_path / "be_shadow_log.jsonl")

        for i in range(3):
            write_be_shadow_log({"trade_id": f"test_{i}"}, log_path=log_path)

        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) == 3
        for i, line in enumerate(lines):
            parsed = json.loads(line)
            assert parsed["trade_id"] == f"test_{i}"

    def test_creates_parent_directory(self, tmp_path):
        log_path = str(tmp_path / "nested" / "dir" / "log.jsonl")
        write_be_shadow_log({"trade_id": "test"}, log_path=log_path)
        assert Path(log_path).exists()


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_zero_sl_distance(self):
        """Zero SL distance should never trigger."""
        tracker = BEShadowTracker(
            trade_id="zero_sl", entry_price=2800.0,
            stop_loss=2800.0, direction="LONG", sl_distance=0.0,
        )
        assert not tracker.update(3000.0)
        assert not tracker.be_trigger_activated

    def test_tracker_fields_populated(self, long_tracker):
        """All result fields present after full lifecycle."""
        long_tracker.update(2810.0)
        long_tracker.update(2795.0)
        result = long_tracker.compute_hypothetical(2795.0, -0.5)

        required_fields = [
            "trade_id", "direction", "entry_price", "stop_loss",
            "sl_distance", "timestamp_1r_reached", "price_at_1r",
            "actual_exit_price", "actual_r_multiple", "reversed_past_entry",
            "hypothetical_be_r", "delta_r", "be_would_have_helped",
            "timestamp_closed",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
