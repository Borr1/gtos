"""Tests for economic calendar loader and blocking logic."""

from __future__ import annotations

import logging
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.utils.economic_calendar import (
    get_blocking_events,
    load_calendar,
    should_block_trading,
)


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def sample_calendar():
    """A small calendar with known events."""
    return [
        {
            "datetime_utc": datetime(2026, 4, 3, 12, 30, tzinfo=timezone.utc),
            "event": "US Non-Farm Payrolls",
            "impact": "HIGH",
            "currency": "USD",
            "estimated": True,
        },
        {
            "datetime_utc": datetime(2026, 4, 14, 7, 0, tzinfo=timezone.utc),
            "event": "UK CPI",
            "impact": "HIGH",
            "currency": "GBP",
            "estimated": True,
        },
        {
            "datetime_utc": datetime(2026, 4, 15, 12, 30, tzinfo=timezone.utc),
            "event": "US Retail Sales",
            "impact": "HIGH",
            "currency": "USD",
            "estimated": True,
        },
        {
            "datetime_utc": datetime(2026, 4, 20, 9, 0, tzinfo=timezone.utc),
            "event": "Some Low Impact",
            "impact": "LOW",
            "currency": "USD",
            "estimated": False,
        },
    ]


@pytest.fixture
def default_config():
    """Config with economic calendar enabled."""
    return {
        "economic_calendar": {
            "enabled": True,
            "calendar_file": "data/economic_calendar.csv",
            "block_before_minutes": 120,
            "block_after_minutes": 30,
            "block_impact_levels": ["HIGH"],
            "currency_map": {
                "XAUUSD": ["USD"],
                "GBPUSD": ["USD", "GBP"],
                "EURUSD": ["USD", "EUR"],
                "NAS100": ["USD"],
                "XAGUSD": ["USD"],
            },
        }
    }


# ── Test 1: load_calendar ─────────────────────────────────────────────

def test_load_calendar(tmp_path):
    """Load CSV, verify events parse correctly."""
    csv_content = textwrap.dedent("""\
        date,time_utc,event,impact,currency,estimated
        2026-04-03,12:30,US Non-Farm Payrolls,HIGH,USD,true
        2026-04-14,07:00,UK CPI,HIGH,GBP,false
    """)
    csv_file = tmp_path / "test_calendar.csv"
    csv_file.write_text(csv_content)

    events = load_calendar(str(csv_file))

    assert len(events) == 2
    assert events[0]["event"] == "US Non-Farm Payrolls"
    assert events[0]["currency"] == "USD"
    assert events[0]["impact"] == "HIGH"
    assert events[0]["estimated"] is True
    assert events[0]["datetime_utc"] == datetime(2026, 4, 3, 12, 30, tzinfo=timezone.utc)
    assert events[1]["estimated"] is False


# ── Test 2: upcoming events within window ─────────────────────────────

def test_upcoming_events_within_window(sample_calendar, default_config):
    """Event in 90 min, window 120 min -> found."""
    nfp_time = sample_calendar[0]["datetime_utc"]
    current = nfp_time - timedelta(minutes=90)

    blocking = get_blocking_events(sample_calendar, current, "XAUUSD", default_config)
    assert len(blocking) == 1
    assert blocking[0]["event"] == "US Non-Farm Payrolls"


# ── Test 3: upcoming events outside window ────────────────────────────

def test_upcoming_events_outside_window(sample_calendar, default_config):
    """Event in 180 min, window 120 min -> not found."""
    nfp_time = sample_calendar[0]["datetime_utc"]
    current = nfp_time - timedelta(minutes=180)

    blocking = get_blocking_events(sample_calendar, current, "XAUUSD", default_config)
    assert len(blocking) == 0


# ── Test 4: post-event block ──────────────────────────────────────────

def test_post_event_block(sample_calendar, default_config):
    """Event was 15 min ago, post-block 30 min -> still blocked."""
    nfp_time = sample_calendar[0]["datetime_utc"]
    current = nfp_time + timedelta(minutes=15)

    blocked, reason = should_block_trading(sample_calendar, current, "XAUUSD", default_config)
    assert blocked is True
    assert "15 minutes ago" in reason


# ── Test 5: post-event cleared ────────────────────────────────────────

def test_post_event_cleared(sample_calendar, default_config):
    """Event was 45 min ago, post-block 30 min -> not blocked."""
    nfp_time = sample_calendar[0]["datetime_utc"]
    current = nfp_time + timedelta(minutes=45)

    blocked, reason = should_block_trading(sample_calendar, current, "XAUUSD", default_config)
    assert blocked is False
    assert reason is None


# ── Test 6: currency filtering — gold only USD ────────────────────────

def test_currency_filtering_gold(sample_calendar, default_config):
    """Gold only sees USD events, ignores GBP."""
    uk_cpi_time = sample_calendar[1]["datetime_utc"]
    current = uk_cpi_time - timedelta(minutes=30)

    blocked, reason = should_block_trading(sample_calendar, current, "XAUUSD", default_config)
    assert blocked is False


# ── Test 7: currency filtering — GBPUSD sees both ────────────────────

def test_currency_filtering_gbpusd(sample_calendar, default_config):
    """GBPUSD sees both USD and GBP events."""
    uk_cpi_time = sample_calendar[1]["datetime_utc"]
    current = uk_cpi_time - timedelta(minutes=30)

    blocked, reason = should_block_trading(sample_calendar, current, "GBPUSD", default_config)
    assert blocked is True
    assert "UK CPI" in reason


# ── Test 8: no calendar = no block ────────────────────────────────────

def test_no_calendar_no_block(tmp_path, default_config, caplog):
    """Missing file -> no block, warning logged."""
    missing_path = str(tmp_path / "nonexistent.csv")
    events = load_calendar(missing_path)
    assert events == []

    blocked, reason = should_block_trading(events, datetime.now(timezone.utc), "XAUUSD", default_config)
    assert blocked is False


# ── Test 9: disabled config ───────────────────────────────────────────

def test_disabled_config(sample_calendar):
    """enabled=false -> never blocks (empty calendar would be loaded)."""
    config = {
        "economic_calendar": {
            "enabled": False,
        }
    }
    blocked, reason = should_block_trading([], datetime.now(timezone.utc), "XAUUSD", config)
    assert blocked is False


# ── Test 10: estimated date warning ───────────────────────────────────

def test_estimated_date_warning(tmp_path, caplog):
    """Calendar with estimated=true -> startup warning logged."""
    csv_content = textwrap.dedent("""\
        date,time_utc,event,impact,currency,estimated
        2027-12-03,12:30,US NFP,HIGH,USD,true
    """)
    csv_file = tmp_path / "est_calendar.csv"
    csv_file.write_text(csv_content)

    with caplog.at_level(logging.WARNING):
        events = load_calendar(str(csv_file))

    assert len(events) == 1
    assert any("estimated dates" in msg for msg in caplog.messages)


# ── Additional edge cases ─────────────────────────────────────────────

def test_malformed_row_skipped(tmp_path, caplog):
    """Malformed rows are skipped, valid ones still load."""
    csv_content = textwrap.dedent("""\
        date,time_utc,event,impact,currency,estimated
        2027-12-03,12:30,Valid Event,HIGH,USD,false
        bad-date,25:99,Broken Event,HIGH,USD,false
        2027-12-04,14:00,Another Valid,HIGH,USD,false
    """)
    csv_file = tmp_path / "mixed_calendar.csv"
    csv_file.write_text(csv_content)

    with caplog.at_level(logging.WARNING):
        events = load_calendar(str(csv_file))

    assert len(events) == 2
    assert events[0]["event"] == "Valid Event"
    assert events[1]["event"] == "Another Valid"


def test_low_impact_not_blocked(sample_calendar, default_config):
    """LOW impact events are never blocking."""
    low_event_time = sample_calendar[3]["datetime_utc"]
    current = low_event_time - timedelta(minutes=30)

    blocked, _ = should_block_trading(sample_calendar, current, "XAUUSD", default_config)
    assert blocked is False


def test_reason_string_future(sample_calendar, default_config):
    """Reason string for upcoming event says 'in X minutes'."""
    nfp_time = sample_calendar[0]["datetime_utc"]
    current = nfp_time - timedelta(minutes=47)

    blocked, reason = should_block_trading(sample_calendar, current, "XAUUSD", default_config)
    assert blocked is True
    assert "47 minutes" in reason
    assert "Non-Farm" in reason
