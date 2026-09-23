"""Cross-instrument context: XAUUSD D1 direction + Asian range width.

Provides macro context for GBPUSD (and potentially other) trading decisions.
Both functions are pure — they take data in, return results out, with no
side effects or API calls.
"""

from __future__ import annotations

from typing import Optional


def get_xauusd_d1_direction(
    trade_date: str,
    d1_candles: list[dict],
) -> str:
    """Determine XAUUSD D1 direction as of *trade_date*.

    Uses the **same methodology as the improvements analysis** that
    produced the 31.7% WR spread: simple close-over-previous-close
    comparison on the most recent D1 candle.

    This is NOT swing-structure classification (which proved to be a
    methodology mismatch in the pressure test).  The validated signal
    is: "was the most recent completed D1 candle bullish or bearish?"

    Parameters
    ----------
    trade_date : str
        ISO date string (``YYYY-MM-DD``).  The most recent D1 candle
        up to and including this date is used.
    d1_candles : list[dict]
        XAUUSD D1 candle data (each dict has at least ``time``, ``open``,
        ``high``, ``low``, ``close``).

    Returns
    -------
    str
        ``"bullish"`` if close > previous close,
        ``"bearish"`` if close <= previous close,
        ``"unavailable"`` if insufficient data.
    """
    if not d1_candles:
        return "unavailable"

    # Filter candles up to and including trade_date
    filtered = [c for c in d1_candles if c["time"][:10] <= trade_date]
    if len(filtered) < 2:
        return "unavailable"

    # Compare the last two D1 candles: close vs previous close
    current = filtered[-1]
    previous = filtered[-2]

    if current["close"] > previous["close"]:
        return "bullish"
    return "bearish"


def get_asian_range_pct(
    trade_date: str,
    m15_candles: list[dict],
    d1_candles: list[dict],
    asian_start: str = "00:00",
    asian_end: str = "07:00",
    adr_period: int = 14,
) -> Optional[dict]:
    """Compute Asian session range as percentage of ADR.

    Parameters
    ----------
    trade_date : str
        ISO date string (``YYYY-MM-DD``).
    m15_candles : list[dict]
        Target instrument M15 candle data.
    d1_candles : list[dict]
        Target instrument D1 candle data.
    asian_start, asian_end : str
        Asian session boundaries in ``HH:MM`` format (UTC).
    adr_period : int
        Number of D1 candles for Average Daily Range (default 14).

    Returns
    -------
    dict or None
        ``{"asian_range": float, "adr_14": float, "pct_of_adr": float,
        "category": str}``  or ``None`` if insufficient data.
    """
    if not m15_candles or not d1_candles:
        return None

    # Asian session M15 candles for the trade date
    # Include candles from asian_start up to (but not including) asian_end
    asian_candles = []
    for c in m15_candles:
        t = c["time"]
        if not t.startswith(trade_date):
            continue
        # Extract HH:MM from timestamp
        if "T" in t:
            hhmm = t[11:16]
        elif " " in t:
            hhmm = t[11:16]
        else:
            continue
        if asian_start <= hhmm < asian_end:
            asian_candles.append(c)

    if len(asian_candles) < 5:
        return None

    asian_high = max(c["high"] for c in asian_candles)
    asian_low = min(c["low"] for c in asian_candles)
    asian_range = asian_high - asian_low

    # ADR from D1 candles BEFORE the trade date
    prior_d1 = [c for c in d1_candles if c["time"][:10] < trade_date]
    if len(prior_d1) < adr_period:
        return None

    recent_d1 = prior_d1[-adr_period:]
    daily_ranges = [c["high"] - c["low"] for c in recent_d1]
    adr = sum(daily_ranges) / len(daily_ranges)

    if adr <= 0:
        return None

    pct = (asian_range / adr) * 100

    if pct < 28:
        category = "narrow"
    elif pct <= 50:
        category = "moderate"
    else:
        category = "wide"

    return {
        "asian_range": round(asian_range, 6),
        "adr_14": round(adr, 6),
        "pct_of_adr": round(pct, 1),
        "category": category,
    }
