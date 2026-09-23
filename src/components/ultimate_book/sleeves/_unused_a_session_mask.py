"""Session masks for unused-window sleeves 1-5. Clock only. Fail closed.

Broker wall = America/New_York + 7h (NEW_YORK_PLUS_7). Live `bar_time` is true UTC
(`book_engine` / `bar_provider`). Masks match `outbox/_run_unused_geo_1_5.py`
`session_clock` so a fire outside the measured window returns None.

Anything untimestamped or unparseable is outside the mask.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from ....utils.broker_clock import EuDstAnchor, NEW_YORK_PLUS_7, offset_seconds_at_utc
from ._server_clock import to_server_local

# Live canonical US cash only. Never US500_cash / US100_cash.
_US_CASH = frozenset({"US30_cash"})
_HOLE_MIN = 120.0  # >=2h first-print after a hole (UNUSED-GEO-1-5 lead 4)
_SUN_MON = frozenset({6, 0})  # datetime.weekday(): Sun=6, Mon=0


def _parse_utc(t) -> Optional[datetime]:
    if t is None:
        return None
    if isinstance(t, datetime):
        stamp = t
    else:
        text = str(t).strip()
        if not text:
            return None
        if text.endswith(("Z", "z")):
            text = text[:-1] + "+00:00"
        try:
            stamp = datetime.fromisoformat(text)
        except ValueError:
            return None
    utc = stamp if stamp.tzinfo is not None else stamp.replace(tzinfo=timezone.utc)
    return utc.astimezone(timezone.utc)


def _latest_utc(bar_time, bar_times) -> Optional[datetime]:
    if bar_time is not None:
        return _parse_utc(bar_time)
    if bar_times:
        return _parse_utc(bar_times[-1])
    return None


def _broker_mins(utc: datetime) -> Optional[int]:
    local = to_server_local(utc)
    if local is None:
        return None
    return local.hour * 60 + local.minute


def _dtm_minutes(t_cur, t_prev) -> Optional[float]:
    cur = _parse_utc(t_cur)
    prev = _parse_utc(t_prev)
    if cur is None or prev is None:
        return None
    return (cur - prev).total_seconds() / 60.0


def _cash_stamp(symbol: str, utc: datetime) -> bool:
    mins = _broker_mins(utc)
    if mins is None:
        return False
    return symbol in _US_CASH and mins == 16 * 60 + 30


def _first_hole_or_cash(symbol: str, t_cur, t_prev) -> bool:
    utc = _parse_utc(t_cur)
    if utc is None:
        return False
    if _cash_stamp(symbol, utc):
        return True
    dtm = _dtm_minutes(t_cur, t_prev)
    if dtm is None:
        return False
    return dtm >= _HOLE_MIN


def mask_weekend_gap(*, symbol: str = "", bar_time=None, bar_times=None) -> bool:
    """Sunday/Monday broker hole after F2; forbid ±30 min of broker 00:00."""
    del symbol
    utc = _latest_utc(bar_time, bar_times)
    local = to_server_local(utc)
    if local is None:
        return False
    if local.weekday() not in _SUN_MON:
        return False
    mins = local.hour * 60 + local.minute
    if mins < 30 or mins >= 23 * 60 + 30:
        return False
    return True


def mask_tokyo_overnight(*, symbol: str = "", bar_time=None, bar_times=None) -> bool:
    """Overnight box into Tokyo cash open (broker 02:00 EST / 03:00 EDT, −3h..+2.5h)."""
    del symbol
    utc = _latest_utc(bar_time, bar_times)
    if utc is None:
        return False
    local = to_server_local(utc)
    if local is None:
        return False
    off_h = offset_seconds_at_utc(utc, NEW_YORK_PLUS_7) / 3600.0
    tokyo_open = 3 * 60 if off_h >= 2.5 else 2 * 60
    mins = local.hour * 60 + local.minute
    lo = tokyo_open - 180
    hi = tokyo_open + 150
    if lo < 0:
        return mins >= (lo + 1440) or mins <= hi
    return lo <= mins <= hi


def mask_london_0815(*, symbol: str = "", bar_time=None, bar_times=None) -> bool:
    """London-local 08:00-09:15 through NEW_YORK_PLUS_7 + EU DST (not hour==9)."""
    del symbol
    utc = _latest_utc(bar_time, bar_times)
    if utc is None:
        return False
    extra = 3600 if EuDstAnchor.is_summer(utc) else 0
    london = utc + timedelta(seconds=extra)
    mins = london.hour * 60 + london.minute
    return (8 * 60) <= mins <= (9 * 60 + 15)


def mask_first_cash_or_2h_hole(*, symbol: str, bar_time=None, bar_times=None) -> bool:
    """First cash-open stamp (US 16:30) or first bar after a >=2h hole."""
    utc = _latest_utc(bar_time, bar_times)
    if utc is None:
        return False
    prev = bar_times[-2] if bar_times is not None and len(bar_times) >= 2 else None
    return _first_hole_or_cash(symbol, utc, prev)


def mask_first_two_cash(*, symbol: str, bar_time=None, bar_times=None) -> bool:
    """First two cash-session bars (16:30+16:45 US; next bar after a >=2h hole)."""
    if mask_first_cash_or_2h_hole(symbol=symbol, bar_time=bar_time, bar_times=bar_times):
        return True
    utc = _latest_utc(bar_time, bar_times)
    if utc is None:
        return False
    mins = _broker_mins(utc)
    if mins is not None and symbol in _US_CASH and mins == 16 * 60 + 45:
        return True
    if bar_times is None or len(bar_times) < 2:
        return False
    prev_times = list(bar_times[:-1])
    return mask_first_cash_or_2h_hole(
        symbol=symbol, bar_time=bar_times[-2], bar_times=prev_times
    )
