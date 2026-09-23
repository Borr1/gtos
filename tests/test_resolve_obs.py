"""Tests for OB retest event resolution in live_monitor.py."""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _make_h1_rates(bars: list[dict]) -> np.ndarray:
    """Build numpy structured array matching MT5 copy_rates_range output."""
    dtype = np.dtype([
        ("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"),
        ("close", "f8"), ("tick_volume", "i8"), ("spread", "i4"), ("real_volume", "i8"),
    ])
    arr = np.zeros(len(bars), dtype=dtype)
    for i, b in enumerate(bars):
        ts = b["time"]
        arr[i]["time"] = int(ts.timestamp()) if isinstance(ts, datetime) else ts
        arr[i]["high"] = b["high"]
        arr[i]["low"] = b["low"]
        arr[i]["open"] = b.get("open", b["low"])
        arr[i]["close"] = b.get("close", b["high"])
    return arr


class TestResolveObs:
    """Test the resolve_obs flow with mocked MT5 data."""

    @pytest.fixture
    def event_file(self, tmp_path, monkeypatch):
        """Create a temp event file and point META_DIR at it."""
        meta = tmp_path / "meta"
        meta.mkdir()

        import scripts.live_monitor as lm
        monkeypatch.setattr(lm, "META_DIR", meta)
        return meta

    def _write_events(self, meta_dir, symbol, events):
        fp = meta_dir / f"ob_retest_events_{symbol}.json"
        with open(fp, "w") as f:
            json.dump(events, f)
        return fp

    def test_bullish_continuation_resolved(self, event_file):
        """Bullish OB where price reaches 1.5R target → CONTINUED."""
        event_time = datetime.now(timezone.utc) - timedelta(hours=20)
        events = [{
            "timestamp": event_time.isoformat(),
            "symbol": "XAUUSD",
            "ob_zone_high": 3050.0,
            "ob_zone_low": 3040.0,  # zone height = 10
            "ob_type": "bullish",
            "entry_price": 3045.0,
            "causing_event": "BOS",
            "formation_time": "2026-04-06T10:00:00",
            "outcome": "PENDING",
        }]
        fp = self._write_events(event_file, "XAUUSD", events)

        # H1 bars: price rallies to +15 (>= 1.5 * 10 = 15 target)
        bars = [
            {"time": event_time + timedelta(hours=h), "high": 3045 + h * 2, "low": 3044.0}
            for h in range(1, 10)
        ]
        # bar at h=8: high = 3045+16 = 3061 → 3061-3045 = 16 >= 15 → CONTINUED
        rates = _make_h1_rates(bars)

        import scripts.live_monitor as lm
        fake_mt5 = MagicMock()
        fake_mt5.initialize.return_value = True
        fake_mt5.TIMEFRAME_H1 = 16385
        fake_mt5.copy_rates_range.return_value = rates
        with patch.dict("sys.modules", {"MetaTrader5": fake_mt5}):
            lm.run_resolve_obs()

        result = json.loads(fp.read_text())
        assert result[0]["outcome"] == "CONTINUED"
        assert "resolved_at" in result[0]

    def test_bearish_failure_resolved(self, event_file):
        """Bearish OB where price never drops to 1.5R → FAILED."""
        event_time = datetime.now(timezone.utc) - timedelta(hours=20)
        events = [{
            "timestamp": event_time.isoformat(),
            "symbol": "XAUUSD",
            "ob_zone_high": 3060.0,
            "ob_zone_low": 3050.0,  # zone height = 10, target = 15
            "ob_type": "bearish",
            "entry_price": 3055.0,
            "causing_event": "CHoCH",
            "formation_time": "2026-04-06T14:00:00",
            "outcome": "PENDING",
        }]
        fp = self._write_events(event_file, "XAUUSD", events)

        # H1 bars: price only drops 5 points (never reaches 15 target)
        bars = [
            {"time": event_time + timedelta(hours=h), "high": 3057.0, "low": 3050.0}
            for h in range(1, 10)
        ]
        rates = _make_h1_rates(bars)

        import scripts.live_monitor as lm
        fake_mt5 = MagicMock()
        fake_mt5.initialize.return_value = True
        fake_mt5.TIMEFRAME_H1 = 16385
        fake_mt5.copy_rates_range.return_value = rates
        with patch.dict("sys.modules", {"MetaTrader5": fake_mt5}):
            lm.run_resolve_obs()

        result = json.loads(fp.read_text())
        assert result[0]["outcome"] == "FAILED"

    def test_recent_event_stays_pending(self, event_file):
        """Event < 16 hours old should remain PENDING."""
        event_time = datetime.now(timezone.utc) - timedelta(hours=5)
        events = [{
            "timestamp": event_time.isoformat(),
            "symbol": "XAUUSD",
            "ob_zone_high": 3050.0,
            "ob_zone_low": 3040.0,
            "ob_type": "bullish",
            "entry_price": 3045.0,
            "causing_event": "BOS",
            "formation_time": "2026-04-07T08:00:00",
            "outcome": "PENDING",
        }]
        fp = self._write_events(event_file, "XAUUSD", events)

        import scripts.live_monitor as lm
        fake_mt5 = MagicMock()
        fake_mt5.initialize.return_value = True
        fake_mt5.TIMEFRAME_H1 = 16385
        fake_mt5.copy_rates_range.return_value = None
        with patch.dict("sys.modules", {"MetaTrader5": fake_mt5}):
            lm.run_resolve_obs()

        result = json.loads(fp.read_text())
        assert result[0]["outcome"] == "PENDING"

    def test_already_resolved_not_touched(self, event_file):
        """CONTINUED/FAILED events should not be re-processed."""
        event_time = datetime.now(timezone.utc) - timedelta(hours=24)
        events = [{
            "timestamp": event_time.isoformat(),
            "symbol": "XAUUSD",
            "ob_zone_high": 3050.0,
            "ob_zone_low": 3040.0,
            "ob_type": "bullish",
            "entry_price": 3045.0,
            "causing_event": "BOS",
            "formation_time": "2026-04-06T08:00:00",
            "outcome": "CONTINUED",
            "resolved_at": "2026-04-07T01:00:00",
        }]
        fp = self._write_events(event_file, "XAUUSD", events)

        import scripts.live_monitor as lm
        fake_mt5 = MagicMock()
        fake_mt5.initialize.return_value = True
        fake_mt5.TIMEFRAME_H1 = 16385
        with patch.dict("sys.modules", {"MetaTrader5": fake_mt5}):
            lm.run_resolve_obs()

        # copy_rates_range should never be called — event is already resolved
        fake_mt5.copy_rates_range.assert_not_called()
        result = json.loads(fp.read_text())
        assert result[0]["outcome"] == "CONTINUED"

    def test_us30_symbol_mapping(self, event_file):
        """US30_cash events should query MT5 with US30.cash."""
        event_time = datetime.now(timezone.utc) - timedelta(hours=20)
        events = [{
            "timestamp": event_time.isoformat(),
            "symbol": "US30_cash",
            "ob_zone_high": 40000.0,
            "ob_zone_low": 39900.0,
            "ob_type": "bullish",
            "entry_price": 39950.0,
            "causing_event": "BOS",
            "formation_time": "2026-04-06T14:00:00",
            "outcome": "PENDING",
        }]
        self._write_events(event_file, "US30_cash", events)

        bars = [
            {"time": event_time + timedelta(hours=h), "high": 39950 + h * 30, "low": 39940.0}
            for h in range(1, 10)
        ]
        rates = _make_h1_rates(bars)

        import scripts.live_monitor as lm
        fake_mt5 = MagicMock()
        fake_mt5.initialize.return_value = True
        fake_mt5.TIMEFRAME_H1 = 16385
        fake_mt5.copy_rates_range.return_value = rates
        with patch.dict("sys.modules", {"MetaTrader5": fake_mt5}):
            lm.run_resolve_obs()

        # Verify the MT5 call used "US30.cash" not "US30_cash"
        call_args = fake_mt5.copy_rates_range.call_args
        assert call_args[0][0] == "US30.cash"
