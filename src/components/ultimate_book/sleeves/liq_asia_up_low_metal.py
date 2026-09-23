"""liq_asia_up_low_metal.py - Asian metals liquidity-sweep reversal candidate.

Default-off candidate sleeve, owner/VPS gated for any live wiring. During the
Asian session, metals that sweep and reclaim a strictly prior-day high/low are
faded only when the prior completed D1 regime is up and the current M15 ATR
percentile is low. This ports the audited
CMAP_LIQUIDITY_SWEEP_REVERSAL cell:

    class=metal, session=ASIA, regime=up, vol=low

Verified research cell: pooled n=496, train +0.113, oos +0.142,
sealed +0.168, correct random-entry-same-exit null p=0.004.

Leak-free contract:
  - PDH/PDL are from the prior completed calendar day only.
  - D1 regime is resampled from M15 bars strictly before the trade day.
  - Vol-state is computed from trailing ATR14 values through the decision bar.
  - Entry is the latest closed M15 bar; target is fixed 3R; time-stop MAXBARS.
"""
from __future__ import annotations

from typing import Optional

from ..admission import TradeIntent
from ..primitives import Bar, atr14
from ._server_clock import server_day, server_hour
from ._metals_choice import ask, decision_stops


ON_SURFACE = ("XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD")

PIERCE = 0.05
STOP_BUF = 0.10
TARGET_R = 3.0
MAXBARS = 16
ASIA_HI = 6
VOL_LOOKBACK = 480
LOW_VOL_Q = 1.0 / 3.0
REG_N = 10
REG_K = 0.6

# The research generator only required the full loaded symbol history to have
# >=1500 M15 bars; its actual signal loop starts at i=20. The deployable gates
# below enforce the real warmup: >=60 positive ATR samples and enough completed
# D1 days for the regime label.
MIN_BARS = 21


def _hour(t):
    """SERVER-LOCAL hour. The session constants here are FTMO server hours (F7/B29); the
    live feed is true UTC, so this converts before comparing. None -> fail closed."""
    return server_hour(t)


def _day(t):
    """SERVER-LOCAL date key. The route grouped prior-day levels and session ranges on
    SERVER days, not UTC days (F7/B29). NOT the correlated-unit key. None -> fail closed."""
    return server_day(t)


def _is_asia(t) -> bool:
    h = _hour(t)
    return h is not None and 0 <= h <= ASIA_HI


def _build_d1(bars, bar_times, upto_day: str) -> tuple[list[str], list[Bar]]:
    """Resample only the trailing completed D1 bars needed for the regime label."""
    need_days = REG_N + 16
    day_ohlc: dict[str, list[float]] = {}
    reverse_order: list[str] = []
    for t, b in zip(reversed(bar_times), reversed(bars)):
        d = _day(t)
        if d is None or d >= upto_day:
            continue
        if d not in day_ohlc:
            if len(reverse_order) >= need_days:
                break
            day_ohlc[d] = [b.o, b.h, b.l, b.c]
            reverse_order.append(d)
        else:
            vals = day_ohlc[d]
            vals[0] = b.o
            vals[1] = max(vals[1], b.h)
            vals[2] = min(vals[2], b.l)
            # vals[3] is the last close of the day because we scan backward.
    order = sorted(reverse_order)
    return order, [Bar(*day_ohlc[d]) for d in order]


def _regime_up(bars, bar_times, today: str) -> Optional[bool]:
    """D1 up regime as of the last completed prior D1 close."""
    _days, d1 = _build_d1(bars, bar_times, today)
    j = len(d1) - 1
    side = ask(
        "liq_d1_warmup",
        j < REG_N + 15,
        "d1_short",
        "d1_ready",
        "Completed daily bars are short of the regime window.",
        "Completed daily bars cover the regime window.",
        today=today,
        j=j,
    )
    if side == "true":
        return False
    if side is None:
        return None
    if j < REG_N + 15:
        return None
    a = atr14(d1, j)
    side = ask(
        "liq_d1_atr",
        a <= 0,
        "atr_not_positive",
        "atr_positive",
        "Daily ATR is not positive.",
        "Daily ATR is positive.",
        today=today,
        atr=a,
    )
    if side == "true":
        return False
    if side is None:
        return None
    if not (a > 0):
        return None
    up = d1[j].c - d1[j - REG_N].c > REG_K * a
    side = ask(
        "liq_d1_up",
        up,
        "d1_up",
        "d1_not_up",
        "The prior daily regime is up.",
        "The prior daily regime is not up.",
        today=today,
        atr=a,
    )
    if side == "true":
        return True
    if side is None:
        return None
    return False


def _vol_low(atrs: list[float], i: int) -> Optional[bool]:
    """Low vol-state: trailing ATR14 percentile rank below one-third."""
    lo = max(0, i - VOL_LOOKBACK)
    win = [atrs[k] for k in range(lo, i + 1) if atrs[k] > 0]
    side = ask(
        "liq_vol_sample",
        len(win) < 60,
        "vol_sample_short",
        "vol_sample_ready",
        "The trailing ATR sample is short of 60 positive values.",
        "The trailing ATR sample has 60 positive values.",
        i=i,
        n=len(win),
    )
    if side == "true":
        return False
    if side is None:
        return None
    if len(win) < 60:
        return None
    rank = sum(1 for x in win if x <= atrs[i]) / len(win)
    low = rank < LOW_VOL_Q
    side = ask(
        "liq_vol_low",
        low,
        "vol_low",
        "vol_not_low",
        "ATR rank is in the low third.",
        "ATR rank is not in the low third.",
        i=i,
        rank=rank,
    )
    if side == "true":
        return True
    if side is None:
        return None
    return False


def _prior_day_hl(bars, bar_times, today: str) -> tuple[float | None, float | None]:
    prior_day = None
    hi = None
    lo = None
    for k in range(len(bars) - 1, -1, -1):
        d = _day(bar_times[k])
        if d is None or d == today:
            continue
        if prior_day is None:
            prior_day = d
        if d == prior_day:
            hi = bars[k].h if hi is None else max(hi, bars[k].h)
            lo = bars[k].l if lo is None else min(lo, bars[k].l)
        else:
            break
    return hi, lo


def _swept_reclaimed_short(bars, k: int, pdh: float, a: float) -> bool:
    pierce = PIERCE * a
    return bars[k].h > pdh + pierce and bars[k].c < pdh and bars[k - 1].c <= pdh


def _swept_reclaimed_long(bars, k: int, pdl: float, a: float) -> bool:
    pierce = PIERCE * a
    return bars[k].l < pdl - pierce and bars[k].c > pdl and bars[k - 1].c >= pdl


def _already_fired_today(bars, bar_times, i: int, today: str, level: float, atrs: list[float], test_fn) -> bool:
    """One fade per level/day/side: reject if an earlier Asian reclaim already fired."""
    for k in range(i - 1, 0, -1):
        if _day(bar_times[k]) != today:
            break
        if not _is_asia(bar_times[k]):
            continue
        a = atrs[k]
        if a > 0 and test_fn(bars, k, level, a):
            return True
    return False


def _emit(symbol, decision_day, direction, sd):
    if not (sd > 0):
        return None
    return TradeIntent(
        sleeve="liq_asia_up_low_metal",
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=sd,
        target_dist=TARGET_R * sd,
    )


def generate(
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    **_,
) -> Optional[TradeIntent]:
    """Emit an Asian metals sweep-reversal TradeIntent on the latest closed M15 bar."""
    if decision_stops(ask(
        "liq_surface",
        symbol not in ON_SURFACE or not bars or not bar_times,
        "off_surface_or_no_bars",
        "on_named_surface",
        "The symbol is off the metals surface, or bars or bar times are missing.",
        "The symbol is on the metals surface and bars and bar times exist.",
        symbol=symbol,
    )):
        return None
    if not bars or not bar_times:
        return None
    if decision_stops(ask(
        "liq_clock_align",
        len(bars) != len(bar_times),
        "clock_misaligned",
        "clock_aligned",
        "Bar times do not match bars.",
        "Bar times match bars.",
        symbol=symbol,
        n_bars=len(bars),
        n_times=len(bar_times),
    )):
        return None
    if len(bars) != len(bar_times):
        return None
    i = len(bars) - 1
    if decision_stops(ask(
        "liq_warmup",
        i < MIN_BARS,
        "bars_short",
        "warmup_complete",
        "The series is short of the sleeve warmup.",
        "The series meets the sleeve warmup.",
        symbol=symbol,
        i=i,
    )):
        return None
    if decision_stops(ask(
        "liq_asia",
        not _is_asia(bar_times[i]),
        "outside_asia",
        "inside_asia",
        "This bar is outside the Asian session.",
        "This bar is inside the Asian session.",
        symbol=symbol,
        hour=_hour(bar_times[i]),
    )):
        return None
    today = _day(bar_times[i])
    if decision_stops(ask(
        "liq_day",
        today is None,
        "day_missing",
        "day_known",
        "The server day is missing.",
        "The server day is known.",
        symbol=symbol,
    )):
        return None
    if today is None:
        return None

    atr_lo = max(0, i - VOL_LOOKBACK)
    atrs = [0.0] * len(bars)
    for k in range(atr_lo, i + 1):
        atrs[k] = atr14(bars, k)
    a = atrs[i]
    if decision_stops(ask(
        "liq_atr",
        a <= 0,
        "atr_not_positive",
        "atr_positive",
        "ATR is not positive.",
        "ATR is positive.",
        symbol=symbol,
        atr=a,
    )):
        return None
    if not (a > 0):
        return None
    regime = _regime_up(bars, bar_times, today)
    if decision_stops(ask(
        "liq_regime_gate",
        regime is not True,
        "regime_not_up",
        "regime_up",
        "The prior daily regime is not up.",
        "The prior daily regime is up.",
        symbol=symbol,
    )):
        return None
    vol = _vol_low(atrs, i)
    if decision_stops(ask(
        "liq_vol_gate",
        vol is not True,
        "vol_not_low",
        "vol_low",
        "Volatility is not in the low third.",
        "Volatility is in the low third.",
        symbol=symbol,
    )):
        return None

    pdh, pdl = _prior_day_hl(bars, bar_times, today)
    short_setup = pdh is not None and _swept_reclaimed_short(bars, i, pdh, a)
    short_side = ask(
        "liq_short_sweep",
        short_setup,
        "short_sweep_reclaimed",
        "short_sweep_absent",
        "Price swept and reclaimed the prior-day high.",
        "Price did not sweep and reclaim the prior-day high.",
        symbol=symbol,
    )
    if short_side == "true":
        if pdh is None:
            return None
        already = _already_fired_today(bars, bar_times, i, today, pdh, atrs, _swept_reclaimed_short)
        already_side = ask(
            "liq_short_already",
            already,
            "already_faded",
            "first_fade",
            "An earlier Asian reclaim already faded this prior-day high.",
            "This is the first Asian fade of this prior-day high.",
            symbol=symbol,
        )
        if already_side == "false":
            sd = (bars[i].h - bars[i].c) + STOP_BUF * a
            stop_side = ask(
                "liq_short_stop",
                not (sd > 0),
                "stop_not_positive",
                "stop_positive",
                "The short stop distance is not positive.",
                "The short stop distance is positive.",
                symbol=symbol,
                stop_dist=sd,
            )
            if stop_side == "false":
                if not (sd > 0):
                    return None
                return _emit(symbol, decision_day, -1, sd)
            if stop_side is None:
                return None
        elif already_side is None:
            return None
    elif short_side is None:
        return None

    long_setup = pdl is not None and _swept_reclaimed_long(bars, i, pdl, a)
    long_side = ask(
        "liq_long_sweep",
        long_setup,
        "long_sweep_reclaimed",
        "long_sweep_absent",
        "Price swept and reclaimed the prior-day low.",
        "Price did not sweep and reclaim the prior-day low.",
        symbol=symbol,
    )
    if long_side == "true":
        if pdl is None:
            return None
        already = _already_fired_today(bars, bar_times, i, today, pdl, atrs, _swept_reclaimed_long)
        already_side = ask(
            "liq_long_already",
            already,
            "already_faded",
            "first_fade",
            "An earlier Asian reclaim already faded this prior-day low.",
            "This is the first Asian fade of this prior-day low.",
            symbol=symbol,
        )
        if already_side == "false":
            sd = (bars[i].c - bars[i].l) + STOP_BUF * a
            stop_side = ask(
                "liq_long_stop",
                not (sd > 0),
                "stop_not_positive",
                "stop_positive",
                "The long stop distance is not positive.",
                "The long stop distance is positive.",
                symbol=symbol,
                stop_dist=sd,
            )
            if stop_side == "false":
                if not (sd > 0):
                    return None
                return _emit(symbol, decision_day, 1, sd)
            if stop_side is None:
                return None
        elif already_side is None:
            return None
    elif long_side is None:
        return None
    return None
