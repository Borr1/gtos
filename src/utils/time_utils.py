"""Time and session utilities for trading session management."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Tuple


def _parse_hhmm(hhmm: str) -> Tuple[int, int]:
    """Parse 'HH:MM' string into (hour, minute) tuple."""
    parts = hhmm.split(":")
    return int(parts[0]), int(parts[1])


def is_in_session_window(utc_now: datetime, config: dict) -> bool:
    """Check if current UTC time is within the configured trading session window.

    Uses config['market']['session_start_utc'] and config['market']['session_end_utc'].
    """
    market = config.get("market", config)
    start_h, start_m = _parse_hhmm(market["session_start_utc"])
    end_h, end_m = _parse_hhmm(market["session_end_utc"])

    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    now_minutes = utc_now.hour * 60 + utc_now.minute

    return start_minutes <= now_minutes <= end_minutes


def is_asian_session(utc_now: datetime, config: dict) -> bool:
    """Check if current UTC time is within the Asian session window.

    Uses config['market']['asian_session_start_utc'] and
    config['market']['asian_session_end_utc'].
    """
    market = config.get("market", config)
    start_h, start_m = _parse_hhmm(market["asian_session_start_utc"])
    end_h, end_m = _parse_hhmm(market["asian_session_end_utc"])

    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    now_minutes = utc_now.hour * 60 + utc_now.minute

    return start_minutes <= now_minutes < end_minutes


def get_current_session(utc_now: datetime) -> str:
    """Return the current trading session name based on UTC time.

    Returns one of:
        'asian'        — 00:00–07:00
        'london_open'  — 07:00–08:00
        'london_body'  — 08:00–12:00
        'ny_overlap'   — 12:00–14:00
        'ny_open'      — 14:00–16:00
        'ny_afternoon' — 16:00–21:00
    Outside these ranges returns 'off_hours'.
    """
    minutes = utc_now.hour * 60 + utc_now.minute

    if minutes < 420:        # 00:00–07:00
        return "asian"
    elif minutes < 480:      # 07:00–08:00
        return "london_open"
    elif minutes < 720:      # 08:00–12:00
        return "london_body"
    elif minutes < 840:      # 12:00–14:00
        return "ny_overlap"
    elif minutes < 960:      # 14:00–16:00
        return "ny_open"
    elif minutes < 1260:     # 16:00–21:00
        return "ny_afternoon"
    else:
        return "off_hours"


def next_m15_close(utc_now: datetime) -> datetime:
    """Return the datetime of the next M15 candle close.

    M15 candles close at :00, :15, :30, :45 each hour.
    """
    minute = utc_now.minute
    next_close_minute = ((minute // 15) + 1) * 15

    if next_close_minute >= 60:
        result = utc_now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        result = utc_now.replace(minute=next_close_minute, second=0, microsecond=0)

    return result
