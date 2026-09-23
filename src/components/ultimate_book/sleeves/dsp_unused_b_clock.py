"""Session-mask clock for UNUSED-SLEEVES-B. NOT armed. Do not remint.

Broker wall = America/New_York + 7h (NEW_YORK_PLUS_7). US cash open is the 16:30
broker bar, not hour==16. London first hour is London-local 08:00-09:00 via true
UTC + EU DST. Tokyo cash is 09:00-15:00 JST (broker 02:00 EST / 03:00 EDT open).

Live generate() receives true-UTC datetimes (book_engine). A naive datetime is
treated as UTC (same as candles_to_bars). An int/float is a broker-wall epoch
(research tape / UNUSED-GEO). Missing times fail closed.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from src.utils.broker_clock import (
    EuDstAnchor,
    NEW_YORK_PLUS_7,
    broker_epoch_to_utc,
    utc_to_broker_naive,
)

HOLE_MIN = 60.0
FIAT = frozenset(
    {
        "USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "CNH",
        "CZK", "HUF", "NOK", "SEK", "PLN", "MXN", "ZAR", "SGD", "HKD",
        "ILS", "DKK", "TRY",
    }
)


def as_utc(t) -> Optional[datetime]:
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return broker_epoch_to_utc(float(t), NEW_YORK_PLUS_7)
    if not isinstance(t, datetime):
        return None
    if t.tzinfo is not None:
        return t.astimezone(timezone.utc)
    return t.replace(tzinfo=timezone.utc)


def decision_utc(bar_time, bar_times, n: int) -> Optional[datetime]:
    if bar_times is not None and n and len(bar_times) == n:
        return as_utc(bar_times[n - 1])
    return as_utc(bar_time)


def broker_of(utc: datetime) -> datetime:
    return utc_to_broker_naive(utc, NEW_YORK_PLUS_7)


def london_hour(utc: datetime) -> int:
    extra = 1 if EuDstAnchor.is_summer(utc) else 0
    return (utc + timedelta(hours=extra)).hour


def jst_hour(utc: datetime) -> int:
    return (utc + timedelta(hours=9)).hour


def rollover_forbid(broker: datetime) -> bool:
    return (broker.hour == 0 and broker.minute < 30) or (
        broker.hour == 23 and broker.minute >= 30
    )


def first_after_hole(bar_times, i: int, hole_min: float = HOLE_MIN) -> bool:
    if bar_times is None or i < 1 or len(bar_times) <= i:
        return False
    a = as_utc(bar_times[i - 1])
    b = as_utc(bar_times[i])
    if a is None or b is None:
        return False
    return (b - a).total_seconds() / 60.0 >= float(hole_min)


def is_fiat_fx(symbol: str) -> bool:
    return len(symbol) == 6 and symbol[:3] in FIAT and symbol[3:] in FIAT


def mask_gap_open(symbol: str, bar_time, bar_times, n: int) -> bool:
    """First bar after >=60m hole; F2 rollover ±30m of broker 00:00 forbidden."""
    del symbol
    utc = decision_utc(bar_time, bar_times, n)
    if utc is None or n < 2:
        return False
    if not first_after_hole(bar_times, n - 1):
        return False
    return not rollover_forbid(broker_of(utc))


def mask_london_first_hour(symbol: str, bar_time, bar_times, n: int) -> bool:
    """London-local 08:00-09:00. Separate fire set from cash-hole."""
    del symbol
    utc = decision_utc(bar_time, bar_times, n)
    return utc is not None and london_hour(utc) == 8


def mask_cash_hole(symbol: str, bar_time, bar_times, n: int) -> bool:
    """First print after >=60m hole. Not pooled with London."""
    del symbol
    if n < 2:
        return False
    return first_after_hole(bar_times, n - 1)


def mask_tokyo_cash(symbol: str, bar_time, bar_times, n: int) -> bool:
    """Tokyo cash 09:00-15:00 JST."""
    del symbol
    utc = decision_utc(bar_time, bar_times, n)
    if utc is None:
        return False
    hour = jst_hour(utc)
    return 9 <= hour < 15


def mask_cash_hour_fx(symbol: str, bar_time, bar_times, n: int) -> bool:
    """Broker 15:30 or 15:45; fiat FX only. Crypto 6-letter USD excluded."""
    if not is_fiat_fx(symbol):
        return False
    utc = decision_utc(bar_time, bar_times, n)
    if utc is None:
        return False
    broker = broker_of(utc)
    return broker.hour == 15 and broker.minute in (30, 45)


def mask_us_cash_hour(symbol: str, bar_time, bar_times, n: int) -> bool:
    """US cash first hour: broker 16:30-17:15 (09:30-10:30 ET). Missing clock fail-closed."""
    del symbol
    utc = decision_utc(bar_time, bar_times, n)
    if utc is None:
        return False
    broker = broker_of(utc)
    mins = broker.hour * 60 + broker.minute
    return (16 * 60 + 30) <= mins <= (17 * 60 + 15)


def mask_london_or_cash_hole(symbol: str, bar_time, bar_times, n: int) -> bool:
    """London-local 08:00-09:00 or first print after a >=60m hole. Missing clock fail-closed."""
    return mask_london_first_hour(symbol, bar_time, bar_times, n) or mask_cash_hole(
        symbol, bar_time, bar_times, n
    )
