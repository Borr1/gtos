"""Tests for NewsCalendar component (FTMO-grade news event filter)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.components.news_calendar import NewsCalendar


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def sample_events():
    """Known events for testing."""
    return [
        {
            "datetime_utc": datetime(2026, 5, 1, 12, 30, tzinfo=timezone.utc),
            "event": "US Non-Farm Payrolls",
            "impact": "HIGH",
            "currency": "USD",
            "source": "json",
        },
        {
            "datetime_utc": datetime(2026, 5, 6, 18, 0, tzinfo=timezone.utc),
            "event": "FOMC Rate Decision",
            "impact": "HIGH",
            "currency": "USD",
            "source": "json",
        },
        {
            "datetime_utc": datetime(2026, 5, 7, 12, 0, tzinfo=timezone.utc),
            "event": "BOE Rate Decision",
            "impact": "HIGH",
            "currency": "GBP",
            "source": "json",
        },
        {
            "datetime_utc": datetime(2026, 5, 20, 9, 0, tzinfo=timezone.utc),
            "event": "Some Medium Event",
            "impact": "MEDIUM",
            "currency": "USD",
            "source": "json",
        },
    ]


@pytest.fixture
def enabled_config():
    """Config with news_filter enabled, 15min pre / 2min post."""
    return {
        "news_filter": {
            "enabled": True,
            "pre_event_block_minutes": 15,
            "post_event_block_minutes": 2,
            "affected_currencies": ["USD"],
            "impact_levels": ["HIGH"],
            "calendar_source": "json",
            "json_calendar_file": "data/news_calendar.json",
        },
        "economic_calendar": {
            "currency_map": {
                "XAUUSD": ["USD"],
                "GBPUSD": ["USD", "GBP"],
                "USDJPY": ["USD", "JPY"],
                "US30_cash": ["USD"],
            },
        },
    }


@pytest.fixture
def disabled_config():
    """Config with news_filter disabled."""
    return {
        "news_filter": {
            "enabled": False,
        },
    }


# ── Disabled state ────────────────────────────────────────────────────

class TestDisabled:
    def test_disabled_returns_no_skip(self, disabled_config):
        cal = NewsCalendar(disabled_config)
        assert not cal.enabled
        assert cal.events == []
        blocked, reason = cal.should_skip(
            "XAUUSD", datetime(2026, 5, 1, 12, 25, tzinfo=timezone.utc)
        )
        assert not blocked
        assert reason is None

    def test_disabled_no_events_loaded(self, disabled_config):
        cal = NewsCalendar(disabled_config)
        assert len(cal.events) == 0


# ── should_skip logic ────────────────────────────────────────────────

class TestShouldSkip:
    def _make_calendar(self, config, events):
        """Create a NewsCalendar and inject events directly."""
        cal = NewsCalendar(config)
        cal._events = events
        cal._enabled = True
        return cal

    def test_blocks_within_pre_window(self, enabled_config, sample_events):
        """NFP at 12:30 → should block at 12:20 (10min before, within 15min window)."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 1, 12, 20, tzinfo=timezone.utc),
        )
        assert blocked
        assert "NFP" in reason or "Non-Farm" in reason
        assert "SKIP_NEWS_EVENT" in reason
        assert "10min" in reason

    def test_blocks_within_post_window(self, enabled_config, sample_events):
        """NFP at 12:30 → should block at 12:31 (1min after, within 2min window)."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 1, 12, 31, tzinfo=timezone.utc),
        )
        assert blocked
        assert "SKIP_NEWS_EVENT" in reason
        assert "1min ago" in reason

    def test_clear_after_post_window(self, enabled_config, sample_events):
        """NFP at 12:30 → should NOT block at 12:33 (3min after, past 2min window)."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 1, 12, 33, tzinfo=timezone.utc),
        )
        assert not blocked

    def test_clear_before_pre_window(self, enabled_config, sample_events):
        """NFP at 12:30 → should NOT block at 12:10 (20min before, outside 15min window)."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 1, 12, 10, tzinfo=timezone.utc),
        )
        assert not blocked

    def test_blocks_at_exact_event_time(self, enabled_config, sample_events):
        """Should block at exactly the event time."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 1, 12, 30, tzinfo=timezone.utc),
        )
        assert blocked
        assert "NOW" in reason

    def test_ignores_non_usd_for_xauusd(self, enabled_config, sample_events):
        """BOE decision (GBP) should NOT block XAUUSD (USD only)."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 7, 11, 55, tzinfo=timezone.utc),
        )
        assert not blocked

    def test_gbpusd_blocked_by_usd_event(self, enabled_config, sample_events):
        """NFP (USD) should block GBPUSD because GBPUSD contains USD."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "GBPUSD",
            datetime(2026, 5, 1, 12, 20, tzinfo=timezone.utc),
        )
        assert blocked

    def test_usdjpy_blocked_by_usd_event(self, enabled_config, sample_events):
        """NFP (USD) should block USDJPY."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "USDJPY",
            datetime(2026, 5, 1, 12, 20, tzinfo=timezone.utc),
        )
        assert blocked

    def test_us30_blocked_by_usd_event(self, enabled_config, sample_events):
        """NFP (USD) should block US30_cash."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "US30_cash",
            datetime(2026, 5, 1, 12, 20, tzinfo=timezone.utc),
        )
        assert blocked

    def test_ignores_medium_impact(self, enabled_config, sample_events):
        """Medium impact event should NOT trigger block."""
        cal = self._make_calendar(enabled_config, sample_events)
        blocked, reason = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 20, 8, 55, tzinfo=timezone.utc),
        )
        assert not blocked

    def test_empty_events_no_block(self, enabled_config):
        """No events loaded → never blocks."""
        cal = self._make_calendar(enabled_config, [])
        blocked, reason = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 1, 12, 25, tzinfo=timezone.utc),
        )
        assert not blocked


# ── get_next_event ────────────────────────────────────────────────────

class TestGetNextEvent:
    def test_returns_next_usd_event(self, enabled_config, sample_events):
        cal = NewsCalendar.__new__(NewsCalendar)
        cal._config = enabled_config.get("news_filter", {})
        cal._enabled = True
        cal._events = sample_events
        cal._impact_levels = {"HIGH"}
        cal._affected_currencies = {"USD"}
        cal._currency_map = enabled_config["economic_calendar"]["currency_map"]

        nxt = cal.get_next_event(
            "XAUUSD",
            datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
        )
        assert nxt is not None
        assert nxt["event"] == "US Non-Farm Payrolls"

    def test_returns_none_when_no_future_events(self, enabled_config, sample_events):
        cal = NewsCalendar.__new__(NewsCalendar)
        cal._config = enabled_config.get("news_filter", {})
        cal._enabled = True
        cal._events = sample_events
        cal._impact_levels = {"HIGH"}
        cal._affected_currencies = {"USD"}
        cal._currency_map = enabled_config["economic_calendar"]["currency_map"]

        nxt = cal.get_next_event(
            "XAUUSD",
            datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc),
        )
        assert nxt is None


# ── JSON loading ──────────────────────────────────────────────────────

class TestJsonLoading:
    def test_load_valid_json(self, tmp_path):
        cal_file = tmp_path / "calendar.json"
        cal_file.write_text(json.dumps({
            "week_of": "2026-05-01",
            "updated_at": "2026-04-30T18:00:00Z",
            "events": [
                {
                    "date": "2026-05-01",
                    "time_utc": "12:30",
                    "event": "NFP",
                    "impact": "HIGH",
                    "currency": "USD",
                },
                {
                    "date": "2026-05-06",
                    "time_utc": "18:00",
                    "event": "FOMC",
                    "impact": "HIGH",
                    "currency": "USD",
                },
            ],
        }))

        events = NewsCalendar._load_from_json(str(cal_file))
        assert len(events) == 2
        assert events[0]["event"] == "NFP"
        assert events[0]["datetime_utc"] == datetime(2026, 5, 1, 12, 30, tzinfo=timezone.utc)
        assert events[0]["source"] == "json"

    def test_load_missing_json(self, tmp_path):
        events = NewsCalendar._load_from_json(str(tmp_path / "nonexistent.json"))
        assert events == []

    def test_load_malformed_json(self, tmp_path):
        cal_file = tmp_path / "bad.json"
        cal_file.write_text("{not valid json")
        events = NewsCalendar._load_from_json(str(cal_file))
        assert events == []

    def test_load_empty_events(self, tmp_path):
        cal_file = tmp_path / "empty.json"
        cal_file.write_text(json.dumps({"events": []}))
        events = NewsCalendar._load_from_json(str(cal_file))
        assert events == []

    def test_skips_malformed_rows(self, tmp_path):
        cal_file = tmp_path / "partial.json"
        cal_file.write_text(json.dumps({
            "events": [
                {"date": "2026-05-01", "time_utc": "12:30", "event": "NFP", "impact": "HIGH", "currency": "USD"},
                {"date": "bad-date", "time_utc": "12:30", "event": "Bad", "impact": "HIGH", "currency": "USD"},
                {"date": "2026-05-06", "time_utc": "18:00", "event": "FOMC", "impact": "HIGH", "currency": "USD"},
            ],
        }))
        events = NewsCalendar._load_from_json(str(cal_file))
        assert len(events) == 2


# ── CSV fallback ──────────────────────────────────────────────────────

class TestCsvFallback:
    def test_load_valid_csv(self, tmp_path):
        csv_file = tmp_path / "cal.csv"
        csv_file.write_text(
            "date,time_utc,event,impact,currency,estimated\n"
            "2026-05-01,12:30,NFP,HIGH,USD,true\n"
            "2026-05-06,18:00,FOMC,HIGH,USD,false\n"
        )
        events = NewsCalendar._load_from_csv(str(csv_file))
        assert len(events) == 2
        assert events[0]["source"] == "csv"

    def test_load_missing_csv(self, tmp_path):
        events = NewsCalendar._load_from_csv(str(tmp_path / "nope.csv"))
        assert events == []


# ── Integration: full init with JSON file ─────────────────────────────

class TestIntegration:
    def test_full_init_with_json(self, tmp_path):
        cal_file = tmp_path / "news.json"
        cal_file.write_text(json.dumps({
            "week_of": "2026-05-01",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "events": [
                {"date": "2026-05-01", "time_utc": "12:30", "event": "NFP", "impact": "HIGH", "currency": "USD"},
            ],
        }))

        config = {
            "news_filter": {
                "enabled": True,
                "pre_event_block_minutes": 15,
                "post_event_block_minutes": 2,
                "affected_currencies": ["USD"],
                "impact_levels": ["HIGH"],
                "calendar_source": "json",
                "json_calendar_file": str(cal_file),
            },
        }

        cal = NewsCalendar(config)
        assert cal.enabled
        assert len(cal.events) == 1

        # Should block 10min before
        blocked, reason = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 1, 12, 20, tzinfo=timezone.utc),
        )
        assert blocked
        assert "SKIP_NEWS_EVENT" in reason

    def test_full_init_disabled(self):
        config = {"news_filter": {"enabled": False}}
        cal = NewsCalendar(config)
        assert not cal.enabled
        blocked, _ = cal.should_skip("XAUUSD", datetime.now(timezone.utc))
        assert not blocked

    def test_fallback_to_csv(self, tmp_path):
        """When JSON doesn't exist, falls back to CSV."""
        csv_file = tmp_path / "cal.csv"
        csv_file.write_text(
            "date,time_utc,event,impact,currency,estimated\n"
            "2026-05-12,12:30,US CPI,HIGH,USD,false\n"
        )

        config = {
            "news_filter": {
                "enabled": True,
                "pre_event_block_minutes": 15,
                "post_event_block_minutes": 2,
                "affected_currencies": ["USD"],
                "impact_levels": ["HIGH"],
                "calendar_source": "json",
                "json_calendar_file": str(tmp_path / "nonexistent.json"),
                "csv_calendar_file": str(csv_file),
            },
        }

        cal = NewsCalendar(config)
        assert len(cal.events) == 1
        assert cal.events[0]["event"] == "US CPI"


# ── Edge cases ────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_unknown_symbol_defaults_to_usd(self, enabled_config, sample_events):
        """Unknown symbol should default to USD currency mapping."""
        cal = NewsCalendar.__new__(NewsCalendar)
        cal._config = enabled_config.get("news_filter", {})
        cal._enabled = True
        cal._events = sample_events
        cal._pre_block = 15
        cal._post_block = 2
        cal._impact_levels = {"HIGH"}
        cal._affected_currencies = {"USD"}
        cal._currency_map = enabled_config["economic_calendar"]["currency_map"]

        blocked, reason = cal.should_skip(
            "UNKNOWN_PAIR",
            datetime(2026, 5, 1, 12, 20, tzinfo=timezone.utc),
        )
        # Default currency map returns ["USD"] for unknown symbols
        assert blocked

    def test_boundary_exact_pre_window_edge(self, enabled_config, sample_events):
        """At exactly 15 minutes before → should block (inclusive)."""
        cal = NewsCalendar.__new__(NewsCalendar)
        cal._config = enabled_config.get("news_filter", {})
        cal._enabled = True
        cal._events = sample_events
        cal._pre_block = 15
        cal._post_block = 2
        cal._impact_levels = {"HIGH"}
        cal._affected_currencies = {"USD"}
        cal._currency_map = enabled_config["economic_calendar"]["currency_map"]

        blocked, _ = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 1, 12, 15, tzinfo=timezone.utc),
        )
        assert blocked

    def test_boundary_exact_post_window_edge(self, enabled_config, sample_events):
        """At exactly 2 minutes after → should block (inclusive)."""
        cal = NewsCalendar.__new__(NewsCalendar)
        cal._config = enabled_config.get("news_filter", {})
        cal._enabled = True
        cal._events = sample_events
        cal._pre_block = 15
        cal._post_block = 2
        cal._impact_levels = {"HIGH"}
        cal._affected_currencies = {"USD"}
        cal._currency_map = enabled_config["economic_calendar"]["currency_map"]

        blocked, _ = cal.should_skip(
            "XAUUSD",
            datetime(2026, 5, 1, 12, 32, tzinfo=timezone.utc),
        )
        assert blocked
