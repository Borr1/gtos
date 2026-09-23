"""orb_crypto_london.py — NEW SLEEVE: London opening-range breakout CONTINUATION (M15, crypto, vol-low trending).

9th new sleeve (2026-06-17), PRINCIPAL-VERIFIED. A distinct ORB mechanic (NOT the killzone directional-efficiency
sleeve): build the London opening range (server 07:00-07:45, 4 M15 bars); the FIRST bar in the break window
(08:00-11:45) that CLOSES beyond the OR high/low is faded WITH the break (continuation); stop = opposite OR edge,
target 2R, 80-bar time-stop. Gated to a LOW vol-state + a TRENDING (up or dn) HTF regime — the breakout pays in
quiet-then-expand trending crypto.

PRINCIPAL re-derivation (my own, matches the correct-null sweep): n=2375 (BTC+ETH), every-split positive
(train +0.158 / oos +0.057 / sealed +0.118), balanced direction (L 1213 / S 1162 — continuation both ways),
BTC +0.075 / ETH +0.123 both positive, CORRECT random-entry-same-exit null p=0.0000. DEFAULT-OFF candidate (the
VPS wires/activates live).

MECHANIC (leak-free, decides on the latest CLOSED M15 bar i): only in the London break window (server hour 8..11)
when the LOW vol-state + trending HTF regime hold. OR = max/min of today's 4 server-hour-7 bars. i must be the
FIRST break-window bar today to close beyond an OR edge -> continuation entry (long above OR_hi / short below OR_lo).
stop = |entry - opposite OR edge|; target = 2R. vol-state = ATR/price percentile over a trailing window (LOW =
bottom third) — LEAK-FREE (the research gen used a full-series tercile; trailing window is the deployable form).
HTF regime = close-vs-close(REG_LB)/ATR (|slope|>REG_TH => trending). Decision uses only bars <= i; entry at close[i].
"""
from __future__ import annotations
from typing import Optional
from ..primitives import atr14
from ..admission import TradeIntent
from ._server_clock import server_day, server_hour
from .crypto_choices import crypto_side

OR_HOUR = 7              # London opening-range block = server hour 7 (07:00..07:45)
OR_BARS = 4
BRK_LO, BRK_HI = 8, 11   # break window = server hours 8..11
TARGET_R = 2.0
MAXBARS = 80
REG_LB = 384             # HTF regime lookback (slope/ATR)
REG_TH = 1.5             # |slope/ATR| > REG_TH => trending (up/dn)
VOL_WIN = 500            # trailing window for the ATR/price vol-state percentile
VOL_LO = 1.0 / 3.0       # LOW vol-state = bottom-third percentile
MIN_BARS = VOL_WIN + 20  # warmup: needs both REG_LB (384) regime slope AND VOL_WIN (500) vol percentile
ON_SURFACE = ("BTCUSD", "ETHUSD")


def _hour(t):
    """SERVER-LOCAL hour. The session constants here are FTMO server hours (F7/B29); the
    live feed is true UTC, so this converts before comparing. None -> fail closed."""
    return server_hour(t)


def _day(t):
    """SERVER-LOCAL date key. The route grouped prior-day levels and session ranges on
    SERVER days, not UTC days (F7/B29). NOT the correlated-unit key. None -> fail closed."""
    return server_day(t)


def _regime(bars, i, a):
    """Measurement only. up / dn / range from slope versus ATR. Not the decision."""
    if i < REG_LB or a <= 0:
        return "range"
    slope = (bars[i].c - bars[i - REG_LB].c) / a
    return "up" if slope > REG_TH else ("dn" if slope < -REG_TH else "range")


def _low_vol(bars, i, a):
    """Measurement only. True iff ATR/price rank is in the bottom third. Not the decision."""
    if i < VOL_WIN or a <= 0 or bars[i].c <= 0:
        return False
    cur = a / bars[i].c
    vals = []
    for k in range(i - VOL_WIN, i + 1):
        ak = atr14(bars, k)
        if ak > 0 and bars[k].c > 0:
            vals.append(ak / bars[k].c)
    if len(vals) < 50:
        return False
    rank = sum(1 for v in vals if v <= cur) / len(vals)
    return rank <= VOL_LO


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Emit a London-ORB continuation TradeIntent on the latest closed M15 bar, else None. Leak-free."""
    if symbol not in ON_SURFACE or not bars or not bar_times:
        return None
    i = len(bars) - 1
    if i < MIN_BARS or len(bar_times) != len(bars):
        return None
    hi_h = _hour(bar_times[i])
    if hi_h is None or hi_h < BRK_LO or hi_h > BRK_HI:    # London break window only
        return None
    day = _day(bar_times[i])
    a = atr14(bars, i)
    if a <= 0:
        return None
    regime = _regime(bars, i, a)
    blocked = crypto_side(
        "orb_crypto_london_not_low_or_range",
        (not _low_vol(bars, i, a)) or regime == "range",
        "context_closed",
        "context_open",
        "Condition: vol is not low or the regime is range. Which side of this condition is the decision?",
        true_text="Vol is not low or the higher-timeframe regime is range. Do not emit.",
        false_text="Vol is low and the regime is not range.",
        facts={"symbol": symbol, "regime": regime, "vol_low": VOL_LO, "regime_threshold": REG_TH},
    )
    if blocked == "true" or blocked is None:
        return None
    # today's London opening range (the 4 server-hour-7 bars)
    or_idx = [k for k in range(i, -1, -1) if _day(bar_times[k]) == day and _hour(bar_times[k]) == OR_HOUR]
    or_idx = sorted(or_idx)[:OR_BARS]
    if len(or_idx) < OR_BARS:
        return None
    or_hi = max(bars[k].h for k in or_idx)
    or_lo = min(bars[k].l for k in or_idx)
    if or_hi <= or_lo:
        return None
    last_or = or_idx[-1]
    c = bars[i].c
    above = crypto_side(
        "orb_crypto_london_close_above_or_high",
        c > or_hi,
        "close_above_or_high",
        "not_above_or_high",
        "Condition: close > opening-range high. Which side of this condition is the decision?",
        true_text="The close is above the opening-range high.",
        false_text="The close is not above the opening-range high.",
        facts={"symbol": symbol, "close": float(c), "or_high": float(or_hi), "or_low": float(or_lo)},
    )
    direction = 0
    if above == "true":
        direction = 1
    elif above is None:
        return None
    else:
        under = crypto_side(
            "orb_crypto_london_close_below_or_low",
            c < or_lo,
            "close_below_or_low",
            "not_below_or_low",
            "Condition: close < opening-range low. Which side of this condition is the decision?",
            true_text="The close is below the opening-range low.",
            false_text="The close is not below the opening-range low.",
            facts={"symbol": symbol, "close": float(c), "or_high": float(or_hi), "or_low": float(or_lo)},
        )
        if under == "true":
            direction = -1
        elif under is None:
            return None
    if direction == 0:
        return None
    # i must be the FIRST break-window bar today to close beyond an OR edge (one ORB per day)
    for k in range(last_or + 1, i):
        if _day(bar_times[k]) != day:
            continue
        hk = _hour(bar_times[k])
        if hk is None or hk < BRK_LO or hk > BRK_HI:
            continue
        earlier = crypto_side(
            f"orb_crypto_london_earlier_break_{k}",
            bars[k].c > or_hi or bars[k].c < or_lo,
            "earlier_break",
            "no_earlier_break",
            "Condition: an earlier break-window close is beyond an opening-range edge. Which side of this condition is the decision?",
            true_text="An earlier break-window bar already closed beyond the opening range. Do not emit.",
            false_text="That earlier bar did not close beyond the opening range.",
            facts={"symbol": symbol, "close": float(bars[k].c), "or_high": float(or_hi), "or_low": float(or_lo)},
        )
        if earlier == "true" or earlier is None:
            return None
    stop_dist = (c - or_lo) if direction > 0 else (or_hi - c)
    if stop_dist <= 0:
        return None
    return TradeIntent(sleeve="orb_crypto_london", symbol=symbol, direction=direction,
                       decision_day=decision_day, stop_dist=stop_dist, target_dist=TARGET_R * stop_dist)
