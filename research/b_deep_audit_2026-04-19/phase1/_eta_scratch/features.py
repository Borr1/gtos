"""Feature extraction at candle close (no look-ahead).

For a signal at M15 candle close time t, compute:
  - session tag (london / ny / tokyo / dead-zone / off-hours)
  - hour_utc, day_of_week
  - H1 trend direction: simple slope sign over last 10 H1 closes ending at the last closed H1 bar <= t
  - H4 trend direction: slope sign over last 5 H4 closes ending at the last closed H4 bar <= t
  - D1 trend direction: slope sign over last 5 D1 closes (last CLOSED daily bar)
  - D1/H4/H1 alignment: all same direction?
  - PDH/PDL proximity: distance from current close to previous daily high/low in ATR units
  - London/Asian session high/low proximity
  - FVG just formed (M15): is the previous 3-candle window a bullish or bearish FVG?
  - Displacement (M15): |close - open| / ATR_m15 on signal candle
  - Sweep (M15): did the prior 1-5 candles wick through an external level (PDH/PDL/session H/L) without closing?
  - Fib retrace %: if H1 had a recent swing, where is current close on that leg (premium vs discount)

All computed from candles BEFORE OR AT signal close — safe for backtesting.
"""
from __future__ import annotations

from datetime import timedelta

from load_data import atr_14, find_candle_idx_at_or_before, in_any_kz


def _slope_sign(closes):
    if len(closes) < 2:
        return "flat"
    # Simple linear slope via first vs last
    diff = closes[-1] - closes[0]
    # Normalize vs magnitude (avoid noise)
    rng = max(closes) - min(closes)
    if rng == 0:
        return "flat"
    if diff / rng > 0.30:
        return "bullish"
    if diff / rng < -0.30:
        return "bearish"
    return "flat"


def _h1_trend(h1, t):
    idx = find_candle_idx_at_or_before(h1, t)
    if idx is None or idx < 10:
        return None
    # Look at candles strictly before t (use closed bars only).
    # candle h1[idx] has time <= t; if h1[idx]['time'] == t (M15 aligns with H1 start), that H1
    # is still OPEN (next H1 closes an hour later). To be safe, require the bar's close time <= t:
    # if h1[idx]['time'] + 1h > t we must step back.
    # Simpler: look at h1[idx-1] last 10 closes (h1[idx-10] through h1[idx-1]).
    closes = [h1[i]["close"] for i in range(idx - 10, idx)]
    return _slope_sign(closes)


def _h4_trend(h4, t):
    idx = find_candle_idx_at_or_before(h4, t)
    if idx is None or idx < 5:
        return None
    closes = [h4[i]["close"] for i in range(idx - 5, idx)]
    return _slope_sign(closes)


def _d1_trend(d1, t):
    idx = find_candle_idx_at_or_before(d1, t)
    if idx is None or idx < 5:
        return None
    closes = [d1[i]["close"] for i in range(idx - 5, idx)]
    return _slope_sign(closes)


def _pd_range(d1, t):
    """Previous daily high/low: from the D1 candle that CLOSED before the signal day."""
    idx = find_candle_idx_at_or_before(d1, t)
    if idx is None or idx < 1:
        return None
    # Use the prior closed D1 bar.
    # If signal is within the current day and t.date == d1[idx].time.date, we want d1[idx-1].
    # Otherwise d1[idx].
    if d1[idx]["time"].date() == t.date():
        return d1[idx - 1]
    return d1[idx]


def _asian_session_range(m15, t):
    """Tokyo/Asian session = 00:00-07:00 UTC on the current day.
    Returns (high, low) of those candles that closed BEFORE t."""
    day_start = t.replace(hour=0, minute=0, second=0, microsecond=0)
    end = t.replace(hour=7, minute=0, second=0, microsecond=0)
    if t < end:
        end = t  # cap at signal time
    hi = None
    lo = None
    # Walk M15 candles in the range [day_start, end)
    from_idx = find_candle_idx_at_or_before(m15, day_start)
    if from_idx is None:
        from_idx = 0
    for i in range(from_idx, len(m15)):
        if m15[i]["time"] >= end:
            break
        if m15[i]["time"] < day_start:
            continue
        if hi is None or m15[i]["high"] > hi:
            hi = m15[i]["high"]
        if lo is None or m15[i]["low"] < lo:
            lo = m15[i]["low"]
    return hi, lo


def _london_session_range(m15, t):
    """London session = 07:00-12:00 UTC."""
    day_start = t.replace(hour=7, minute=0, second=0, microsecond=0)
    end = t.replace(hour=12, minute=0, second=0, microsecond=0)
    if t < end:
        end = t
    hi = None
    lo = None
    from_idx = find_candle_idx_at_or_before(m15, day_start)
    if from_idx is None:
        return None, None
    for i in range(from_idx, len(m15)):
        if m15[i]["time"] >= end:
            break
        if m15[i]["time"] < day_start:
            continue
        if hi is None or m15[i]["high"] > hi:
            hi = m15[i]["high"]
        if lo is None or m15[i]["low"] < lo:
            lo = m15[i]["low"]
    return hi, lo


def _fvg_m15(m15, idx):
    """3-candle FVG at signal (idx-2, idx-1, idx). Returns 'bull', 'bear' or None.
    Bullish FVG: candle[idx-2].high < candle[idx].low.
    Bearish FVG: candle[idx-2].low > candle[idx].high.
    """
    if idx < 2:
        return None
    c2 = m15[idx - 2]
    c0 = m15[idx]
    if c2["high"] < c0["low"]:
        return "bull"
    if c2["low"] > c0["high"]:
        return "bear"
    return None


def _displacement_m15(m15, idx, atr_m15):
    if atr_m15 is None or atr_m15 <= 0:
        return None
    c = m15[idx]
    body = abs(c["close"] - c["open"])
    return body / atr_m15


def _sweep_detection(m15, idx, lookback=5):
    """Check if any of the last `lookback` candles (including idx) wicked through a key level
    (PDH/PDL/Asian H/L/Session H/L — passed separately) without closing beyond it.

    Simpler version: compare each candle's wick (high>open/close or low<open/close) presence.
    Returns flag dict with wick_high and wick_low — for the calling code to check against actual levels.
    """
    if idx < lookback - 1:
        return None
    results = {"wick_high_max": None, "wick_low_min": None}
    for i in range(idx - lookback + 1, idx + 1):
        c = m15[i]
        body_hi = max(c["open"], c["close"])
        body_lo = min(c["open"], c["close"])
        if c["high"] > body_hi:
            # upside wick
            if results["wick_high_max"] is None or c["high"] > results["wick_high_max"]:
                results["wick_high_max"] = c["high"]
        if c["low"] < body_lo:
            if results["wick_low_min"] is None or c["low"] < results["wick_low_min"]:
                results["wick_low_min"] = c["low"]
    return results


def _fib50_h1(h1, t):
    """H1 equilibrium: midpoint of the last clear 20-bar H1 range ending at t."""
    idx = find_candle_idx_at_or_before(h1, t)
    if idx is None or idx < 20:
        return None
    rng = [h1[i] for i in range(idx - 20, idx)]
    hi = max(c["high"] for c in rng)
    lo = min(c["low"] for c in rng)
    return (hi + lo) / 2.0


def build_features(record, m15, h1, h4, d1):
    """Compute feature dict for a record (candle_time). Returns None if data unavailable."""
    t = record.get("_parsed_time")
    if t is None:
        return None
    symbol = record.get("symbol")
    idx = find_candle_idx_at_or_before(m15, t)
    if idx is None or idx < 15:
        return None

    atr_m15 = atr_14(m15, idx)
    close = m15[idx]["close"]

    # Bias / alignment
    d1_dir = _d1_trend(d1, t)
    h4_dir = _h4_trend(h4, t)
    h1_dir = _h1_trend(h1, t)
    alignments = [d1_dir, h4_dir, h1_dir]
    aligned_dirs = [d for d in alignments if d in ("bullish", "bearish")]
    if len(aligned_dirs) >= 2 and all(d == aligned_dirs[0] for d in aligned_dirs):
        # Check if non-flat ones agree
        if all(d in ("bullish", "bearish", "flat") for d in alignments):
            nonflat = [d for d in alignments if d != "flat"]
            if len(nonflat) >= 2 and all(d == nonflat[0] for d in nonflat):
                alignment_trend = nonflat[0]
            else:
                alignment_trend = "mixed"
        else:
            alignment_trend = "mixed"
    else:
        alignment_trend = "mixed"

    # PD range
    prev_day = _pd_range(d1, t)
    if prev_day:
        pdh = prev_day["high"]
        pdl = prev_day["low"]
        pd_midpoint = (pdh + pdl) / 2.0
        dist_pdh_atr = (pdh - close) / atr_m15 if atr_m15 else None
        dist_pdl_atr = (close - pdl) / atr_m15 if atr_m15 else None
        # PD zone: where is current close relative to PDH/PDL?
        if pdh > pdl:
            pd_frac = (close - pdl) / (pdh - pdl) if (pdh - pdl) > 0 else 0.5
        else:
            pd_frac = 0.5
    else:
        pdh = pdl = pd_midpoint = None
        dist_pdh_atr = dist_pdl_atr = None
        pd_frac = None

    # Session ranges
    asian_hi, asian_lo = _asian_session_range(m15, t)
    london_hi, london_lo = _london_session_range(m15, t)

    # FVG at signal
    fvg_type = _fvg_m15(m15, idx)

    # Displacement
    disp = _displacement_m15(m15, idx, atr_m15)
    disp_high = disp is not None and disp >= 0.75  # body >= 75% ATR

    # Sweep detection
    sweep_info = _sweep_detection(m15, idx, lookback=5)
    sweep_pdh = False
    sweep_pdl = False
    sweep_asian_hi = False
    sweep_asian_lo = False
    sweep_london_hi = False
    sweep_london_lo = False
    if sweep_info:
        wh = sweep_info.get("wick_high_max")
        wl = sweep_info.get("wick_low_min")
        # Did any of the last 5 candles CLOSE below PDH after wicking through? Simplified: any wick beyond + the idx candle closes below that level.
        close_now = close
        if pdh is not None and wh is not None and wh > pdh and close_now <= pdh:
            sweep_pdh = True
        if pdl is not None and wl is not None and wl < pdl and close_now >= pdl:
            sweep_pdl = True
        if asian_hi is not None and wh is not None and wh > asian_hi and close_now <= asian_hi:
            sweep_asian_hi = True
        if asian_lo is not None and wl is not None and wl < asian_lo and close_now >= asian_lo:
            sweep_asian_lo = True
        if london_hi is not None and wh is not None and wh > london_hi and close_now <= london_hi:
            sweep_london_hi = True
        if london_lo is not None and wl is not None and wl < london_lo and close_now >= london_lo:
            sweep_london_lo = True

    # H1 fib50
    fib50 = _fib50_h1(h1, t)
    # Distance from fib50 as %
    if fib50 and atr_m15:
        fib50_dist_atr = (close - fib50) / atr_m15
    else:
        fib50_dist_atr = None

    # Kill zone
    kz = in_any_kz(t, symbol)
    hour_utc = t.hour
    minute_utc = t.minute
    dow = t.weekday()

    return {
        "candle_time": t,
        "symbol": symbol,
        "hour_utc": hour_utc,
        "minute_utc": minute_utc,
        "day_of_week": dow,
        "kz": kz,
        "atr_m15": atr_m15,
        "close": close,
        "d1_dir": d1_dir,
        "h4_dir": h4_dir,
        "h1_dir": h1_dir,
        "alignment_trend": alignment_trend,
        "pdh": pdh,
        "pdl": pdl,
        "pd_frac": pd_frac,
        "dist_pdh_atr": dist_pdh_atr,
        "dist_pdl_atr": dist_pdl_atr,
        "asian_hi": asian_hi,
        "asian_lo": asian_lo,
        "london_hi": london_hi,
        "london_lo": london_lo,
        "fvg_m15": fvg_type,
        "displacement_atr": disp,
        "displacement_high": disp_high,
        "sweep_pdh": sweep_pdh,
        "sweep_pdl": sweep_pdl,
        "sweep_asian_hi": sweep_asian_hi,
        "sweep_asian_lo": sweep_asian_lo,
        "sweep_london_hi": sweep_london_hi,
        "sweep_london_lo": sweep_london_lo,
        "fib50": fib50,
        "fib50_dist_atr": fib50_dist_atr,
    }
