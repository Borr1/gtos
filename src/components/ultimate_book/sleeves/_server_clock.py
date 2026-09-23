"""Broker server-local time for the deployed sleeves (finding F7, live half — B29/B54).

Why this exists
---------------
Every sleeve in this package was mined on the **broker-clock research archive**, so each
`DECISION_HOUR` / `ASIA_*` / `LONDON_*` constant in them is an **FTMO server** hour. The live
feed is different: `mt5_real.py:210-218` subtracts the detected broker offset and
`bar_provider.py:5-7` parses true UTC, so a bar timestamp reaching a sleeve is **true UTC**.

Each sleeve then did `t.hour` and compared it to a server constant. A sleeve gated on
"server hour H" therefore fired when the *UTC* hour was H — **3 h late in summer, 2 h late in
winter** — and the magnitude itself moves twice a year, so a fixed offset would be wrong for
about four weeks annually. Two sleeves match on an exact `(hour, minute)`
(`ny_crypto_momentum`, `kz_london_crypto_low`), so they fired every day on the wrong bar.

The same shift applies to each sleeve's own `_day()`: the route's day boundary was 00:00
**server** (= 21:00/22:00 UTC), so prior-day highs/lows, the Asian range and the opening range
were all grouped over a window offset by 2–3 h. Correcting the hour without the day would leave
half the defect in place, so both route through here.

Scope, deliberately
-------------------
This module is the **signal** clock only. It does **not** touch
`bar_provider.decision_day_of`, which is the correlated-risk-unit grouping key — moving that
boundary changes which positions count as one unit on a day, i.e. the envelope
`book_owner.py:1608-1610` records the dial as having been *certified on*. That is an owner
decision, not a clock repair, and it is tracked separately as B54 Part 2.

`fx_jpy` and `metals` are already correct and do NOT use this module: `fx_jpy` carries its own
`_to_server_local` (which `metals` imports), converted onto the measured calendar earlier. The
offset rule is shared — `broker_clock.NEW_YORK_PLUS_7` — so there is exactly one calendar in the
package, not two.

Fail-closed
-----------
Anything untimestamped or unparseable returns ``None``, and every caller treats ``None`` as
"cannot locate the session -> do not fire". Guessing a clock is what produced F7; a wrong hour is
silent and survives every existing test.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from ....utils.broker_clock import NEW_YORK_PLUS_7, offset_seconds_at_utc

__all__ = ["to_server_local", "server_hour", "server_hour_minute", "server_day"]


def to_server_local(t) -> Optional[datetime]:
    """True-UTC bar stamp (``datetime`` or ISO string) -> NAIVE FTMO server-local datetime.

    Accepts what the sleeves actually receive: a tz-aware UTC ``datetime`` from
    ``bar_provider``, a tz-naive one (treated as UTC, defensive), or an ISO-8601 string.
    Returns ``None`` for anything else, including a string that does not parse — the sleeves
    previously sliced ``s[11:13]`` unconditionally, which cannot fail and therefore could
    silently accept a malformed stamp.
    """
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
    utc = utc.astimezone(timezone.utc)
    offset = offset_seconds_at_utc(utc, NEW_YORK_PLUS_7)
    return (utc + timedelta(seconds=offset)).replace(tzinfo=None)


def server_hour(t) -> Optional[int]:
    """Server-local hour, or ``None`` -> fail closed."""
    local = to_server_local(t)
    return None if local is None else local.hour


def server_hour_minute(t) -> tuple[Optional[int], Optional[int]]:
    """Server-local ``(hour, minute)``, or ``(None, None)`` -> fail closed."""
    local = to_server_local(t)
    return (None, None) if local is None else (local.hour, local.minute)


def server_day(t) -> Optional[str]:
    """Server-local calendar date as ``YYYY-MM-DD``, or ``None`` -> fail closed.

    This is the sleeve's own per-day grouping for prior-day levels and session ranges. It is
    NOT the correlated-risk-unit key; see the module docstring.
    """
    local = to_server_local(t)
    return None if local is None else local.date().isoformat()
