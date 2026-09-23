"""Tests for scripts/passive_alerts.py — event detection, JSONL logging, cooldowns."""

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.passive_alerts import PassiveAlertMonitor, _in_kill_zone, _kill_zone_windows


# ------------------------------------------------------------------
# Kill zone helpers
# ------------------------------------------------------------------

class TestKillZoneHelpers:
    def test_in_kill_zone_london(self):
        windows = [(7, 10), (13, 17)]
        dt = datetime(2026, 4, 7, 8, 30, tzinfo=timezone.utc)  # 08:30
        assert _in_kill_zone(windows, dt) is True

    def test_outside_kill_zone(self):
        windows = [(7, 10), (13, 17)]
        dt = datetime(2026, 4, 7, 11, 0, tzinfo=timezone.utc)  # 11:00
        assert _in_kill_zone(windows, dt) is False

    def test_in_kill_zone_ny(self):
        windows = [(7, 10), (13, 17)]
        dt = datetime(2026, 4, 7, 15, 0, tzinfo=timezone.utc)  # 15:00
        assert _in_kill_zone(windows, dt) is True

    def test_edge_start(self):
        windows = [(7, 10)]
        dt = datetime(2026, 4, 7, 7, 0, tzinfo=timezone.utc)  # exactly 07:00
        assert _in_kill_zone(windows, dt) is True

    def test_edge_end(self):
        windows = [(7, 10)]
        dt = datetime(2026, 4, 7, 10, 0, tzinfo=timezone.utc)  # exactly 10:00
        assert _in_kill_zone(windows, dt) is False


# ------------------------------------------------------------------
# Event detection
# ------------------------------------------------------------------

class TestEventDetection:
    @pytest.fixture
    def monitor(self, tmp_path):
        """Create a monitor with mocked config loading."""
        with patch("scripts.passive_alerts._load_config") as mock_cfg:
            mock_cfg.return_value = {
                "market": {
                    "symbol": "XAUUSD",
                    "mt5_symbol": "XAUUSD",
                    "kill_zones": {
                        "london": {"start_utc": "07:00", "end_utc": "10:30"},
                        "ny": {"start_utc": "13:00", "end_utc": "17:00"},
                    },
                }
            }
            m = PassiveAlertMonitor("XAUUSD")
            m.log_dir = tmp_path / "alerts"
            m.log_dir.mkdir(parents=True, exist_ok=True)
            return m

    def test_ob_zone_touch(self, monitor):
        monitor.ob_zones = [
            {"high": 3050.0, "low": 3045.0, "type": "bullish"},
        ]
        events = monitor.check_events(3047.0)
        assert len(events) == 1
        assert events[0]["type"] == "OB_ZONE_TOUCH"
        assert events[0]["ob_type"] == "bullish"
        assert events[0]["price"] == 3047.0

    def test_ob_zone_miss(self, monitor):
        monitor.ob_zones = [
            {"high": 3050.0, "low": 3045.0, "type": "bullish"},
        ]
        events = monitor.check_events(3060.0)
        ob_events = [e for e in events if e["type"] == "OB_ZONE_TOUCH"]
        assert len(ob_events) == 0

    def test_level_proximity(self, monitor):
        monitor.h1_atr = 20.0  # threshold = 1.0
        monitor.session_levels = {"asian_high": 3050.0, "pdh": 3100.0}
        events = monitor.check_events(3050.5)
        prox = [e for e in events if e["type"] == "LEVEL_PROXIMITY"]
        assert len(prox) == 1
        assert prox[0]["level_name"] == "asian_high"

    def test_level_proximity_not_triggered(self, monitor):
        monitor.h1_atr = 20.0  # threshold = 1.0
        monitor.session_levels = {"asian_high": 3050.0}
        events = monitor.check_events(3055.0)  # 5.0 away, threshold = 1.0
        prox = [e for e in events if e["type"] == "LEVEL_PROXIMITY"]
        assert len(prox) == 0

    def test_flash_displacement(self, monitor):
        monitor.m15_atr = 5.0  # threshold = 10.0
        # Build 6 recent prices (60s history at 10s poll)
        monitor._recent_prices = [3040.0, 3041.0, 3042.0, 3043.0, 3044.0, 3045.0]
        events = monitor.check_events(3060.0)  # 20 pts from 60s ago (3040), > 2*5=10
        flash = [e for e in events if e["type"] == "FLASH_DISPLACEMENT"]
        assert len(flash) == 1
        assert flash[0]["direction"] == "bullish"
        assert flash[0]["magnitude_atr"] == 4.0  # 20 / 5

    def test_flash_displacement_not_triggered(self, monitor):
        monitor.m15_atr = 5.0
        monitor._recent_prices = [3040.0, 3041.0, 3042.0, 3043.0, 3044.0, 3045.0]
        events = monitor.check_events(3048.0)  # 8 pts, < 10 threshold
        flash = [e for e in events if e["type"] == "FLASH_DISPLACEMENT"]
        assert len(flash) == 0

    def test_no_events_when_no_reference_data(self, monitor):
        """No OB zones, no session levels, no recent prices — should be empty."""
        events = monitor.check_events(3050.0)
        assert events == []

    def test_session_levels_handles_none(self, monitor):
        monitor.h1_atr = 20.0
        monitor.session_levels = {"asian_high": 3050.0, "london_high": None}
        events = monitor.check_events(3050.5)
        # Should not crash on None level
        prox = [e for e in events if e["type"] == "LEVEL_PROXIMITY"]
        assert len(prox) == 1


# ------------------------------------------------------------------
# JSONL logging
# ------------------------------------------------------------------

class TestLogging:
    @pytest.fixture
    def monitor(self, tmp_path):
        with patch("scripts.passive_alerts._load_config") as mock_cfg:
            mock_cfg.return_value = {
                "market": {
                    "symbol": "XAUUSD",
                    "kill_zones": {
                        "london": {"start_utc": "07:00", "end_utc": "10:00"},
                    },
                }
            }
            m = PassiveAlertMonitor("XAUUSD")
            m.log_dir = tmp_path / "alerts"
            m.log_dir.mkdir(parents=True, exist_ok=True)
            return m

    def test_log_event_creates_jsonl(self, monitor):
        event = {"type": "OB_ZONE_TOUCH", "price": 3050.0}
        monitor.log_event(event)

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        fp = monitor.log_dir / f"{date_str}.jsonl"
        assert fp.exists()

        with open(fp) as f:
            line = f.readline()
        data = json.loads(line)
        assert data["type"] == "OB_ZONE_TOUCH"
        assert data["symbol"] == "XAUUSD"
        assert "timestamp" in data

    def test_multiple_events_appended(self, monitor):
        monitor.log_event({"type": "A", "price": 1.0})
        monitor.log_event({"type": "B", "price": 2.0})

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        fp = monitor.log_dir / f"{date_str}.jsonl"
        lines = fp.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["type"] == "A"
        assert json.loads(lines[1])["type"] == "B"


# ------------------------------------------------------------------
# Cooldown
# ------------------------------------------------------------------

class TestCooldown:
    @pytest.fixture
    def monitor(self, tmp_path):
        with patch("scripts.passive_alerts._load_config") as mock_cfg:
            mock_cfg.return_value = {
                "market": {
                    "symbol": "XAUUSD",
                    "kill_zones": {
                        "london": {"start_utc": "07:00", "end_utc": "10:00"},
                    },
                }
            }
            m = PassiveAlertMonitor("XAUUSD")
            m.log_dir = tmp_path / "alerts"
            m.log_dir.mkdir(parents=True, exist_ok=True)
            return m

    def test_cooldown_allows_first(self, monitor):
        event = {"type": "OB_ZONE_TOUCH", "ob_high": 3050.0}
        assert monitor._cooldown_ok(event) is True

    def test_cooldown_blocks_duplicate(self, monitor):
        event = {"type": "OB_ZONE_TOUCH", "ob_high": 3050.0}
        monitor._cooldown_ok(event)  # first — sets cooldown
        assert monitor._cooldown_ok(event) is False  # second — blocked

    def test_cooldown_different_zones_independent(self, monitor):
        e1 = {"type": "OB_ZONE_TOUCH", "ob_high": 3050.0}
        e2 = {"type": "OB_ZONE_TOUCH", "ob_high": 3070.0}
        monitor._cooldown_ok(e1)
        assert monitor._cooldown_ok(e2) is True  # different zone, ok

    def test_cooldown_expires(self, monitor):
        event = {"type": "OB_ZONE_TOUCH", "ob_high": 3050.0}
        monitor._cooldown_ok(event)
        # Manually expire the cooldown
        key = f"{event['type']}_{event.get('ob_high', '')}"
        monitor._alert_cooldowns[key] = time.time() - 301
        assert monitor._cooldown_ok(event) is True  # expired, ok again
