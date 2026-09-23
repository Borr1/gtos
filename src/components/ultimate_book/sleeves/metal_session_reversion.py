"""metal_session_reversion.py — NEW SLEEVE: metals NY-session anchor-reversion with trail (M15, XAU/XAG).

7th new sleeve (2026-06-17), PRINCIPAL-VERIFIED. A metals REVERSION sleeve (distinct from the deployed metals
MOMENTUM/FVG core): each NY session, anchor on the session-open; when price extends >= Z*ATR from the anchor
(in a NON-up HTF regime: down or range), FADE it back with a trail exit. Captures intraday mean-reversion in
metals when there is no strong up-trend.

PRINCIPAL re-derivation (my own, matches the correct-null sweep wf_77c9d7db, mechanic B): pooled n=4458,
every-split positive and INCREASING (train +0.066 / oos +0.076 / sealed +0.151), balanced direction
(LONG 2275 / SHORT 2183), XAUUSD +0.095 (n2216) + XAGUSD +0.058 (n2242) both deep+positive, CORRECT
random-entry-SAME-TRAIL null p=0.0000 (the anchor-reversion entry beats random entry with the same trail).
Negative early years (2015/2016) -> CONDITIONAL. DEFAULT-OFF candidate; live wiring owner-gated.

MECHANIC (leak-free, decides on the latest CLOSED M15 bar i): only at a NY-session bar (server hour 14..21) that
is NOT the session-open bar. anchor = open of the FIRST NY bar today. dev = close[i] - anchor. The FIRST NY bar
today with dev >= Z*ATR[i] is the up-extension (-> FADE SHORT); the first with dev <= -Z*ATR[i] is the down-
extension (-> FADE LONG); one per direction per day. Fire ONLY if the HTF regime at i is 'dn' or 'range' (NOT
'up' — don't fade a strong uptrend). stop = STOP_K*ATR; EXIT = trail (arm/gap in stop-units); target_dist None.
Regime = sign of (EMA_fast - EMA_slow)/ATR (|sep|>REG_TH). Decision uses only bars <= i; entry at close[i].
"""
from __future__ import annotations
from typing import Optional
from ..primitives import atr14
from ..admission import TradeIntent
from ._server_clock import server_day, server_hour
from ._metals_choice import ask, decision_stops

Z = 1.6                  # extension threshold in ATR units
STOP_K = 0.8             # stop distance in ATR units
TRAIL_ARM = 0.6          # trail arm in stop-units
TRAIL_GAP = 0.5          # trail gap in stop-units
MAXBARS = 24
EMA_FAST = 48            # ~12h on M15
EMA_SLOW = 192           # ~2d on M15
REG_TH = 0.6             # regime: |(ema_f-ema_s)/atr| > REG_TH => trend; else range
NY_LO, NY_HI = 14, 21    # NY session server hours
MIN_BARS = 200           # warmup (matches the research gen)
ON_SURFACE = ("XAGUSD",)


def _hour(t):
    """SERVER-LOCAL hour. The session constants here are FTMO server hours (F7/B29); the
    live feed is true UTC, so this converts before comparing. None -> fail closed."""
    return server_hour(t)


def _day(t):
    """SERVER-LOCAL date key. The route grouped prior-day levels and session ranges on
    SERVER days, not UTC days (F7/B29). NOT the correlated-unit key. None -> fail closed."""
    return server_day(t)


def _regime(bars, i, a):
    """HTF regime at i from EMA_fast vs EMA_slow normalized by ATR (mirrors the gen build_context/regime_at)."""
    af = 2 / (EMA_FAST + 1)
    aslo = 2 / (EMA_SLOW + 1)
    ef = es = bars[0].c
    for k in range(1, i + 1):
        c = bars[k].c
        ef += af * (c - ef)
        es += aslo * (c - es)
    side = ask(
        "msr_regime_atr",
        a <= 0,
        "atr_not_positive",
        "atr_positive",
        "ATR is not positive.",
        "ATR is positive.",
        i=i,
        atr=a,
    )
    if side == "true":
        return "range"
    if side is None:
        return None
    if not (a > 0):
        return None
    sep = (ef - es) / a
    side = ask(
        "msr_regime_up",
        sep > REG_TH,
        "regime_up",
        "regime_not_up",
        "The EMA separation is above the up threshold.",
        "The EMA separation is not above the up threshold.",
        i=i,
        sep=sep,
    )
    if side == "true":
        return "up"
    if side is None:
        return None
    side = ask(
        "msr_regime_dn",
        sep < -REG_TH,
        "regime_dn",
        "regime_range",
        "The EMA separation is below the down threshold.",
        "The EMA separation is inside the range band.",
        i=i,
        sep=sep,
    )
    if side == "true":
        return "dn"
    if side is None:
        return None
    return "range"


def _earlier_extension(bars, ny, i, anchor, up_ext, dn_ext) -> bool:
    for k in ny[1:]:
        if k >= i:
            break
        ak = atr14(bars, k)
        if ak <= 0:
            continue
        dk = bars[k].c - anchor
        if up_ext and dk >= Z * ak:
            return True
        if dn_ext and dk <= -Z * ak:
            return True
    return False


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Emit a metals NY-session anchor-reversion TradeIntent (trail exit) on the latest closed M15 bar, else None."""
    if decision_stops(ask(
        "msr_surface",
        symbol not in ON_SURFACE or not bars or not bar_times,
        "off_surface_or_no_bars",
        "on_named_surface",
        "The symbol is off the surface, or bars or bar times are missing.",
        "The symbol is on the surface and bars and bar times exist.",
        symbol=symbol,
    )):
        return None
    if not bars or not bar_times:
        return None
    i = len(bars) - 1
    if decision_stops(ask(
        "msr_warmup",
        i < MIN_BARS or len(bar_times) != len(bars),
        "warmup_or_clock_short",
        "warmup_and_clock_ready",
        "Warmup is short, or bar times do not match bars.",
        "Warmup is met and bar times match bars.",
        symbol=symbol,
        i=i,
        n_times=len(bar_times),
        n_bars=len(bars),
    )):
        return None
    if i < MIN_BARS or len(bar_times) != len(bars):
        return None
    hi = _hour(bar_times[i])
    if decision_stops(ask(
        "msr_ny_hour",
        hi is None or hi < NY_LO or hi > NY_HI,
        "outside_ny",
        "inside_ny",
        "This bar is outside NY server hours 14 through 21.",
        "This bar is inside NY server hours 14 through 21.",
        symbol=symbol,
        hour=hi,
    )):
        return None
    a = atr14(bars, i)
    if decision_stops(ask(
        "msr_atr",
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
    day = _day(bar_times[i])
    ny = [k for k in range(i, -1, -1) if _day(bar_times[k]) == day and NY_LO <= (_hour(bar_times[k]) or -1) <= NY_HI]
    ny.sort()
    if not ny:
        return None
    if decision_stops(ask(
        "msr_anchor_bar",
        ny[0] == i,
        "session_anchor_bar",
        "after_the_anchor",
        "This bar is the NY session anchor.",
        "This bar is after the NY session anchor.",
        symbol=symbol,
        i=i,
    )):
        return None
    anchor = bars[ny[0]].o
    dev = bars[i].c - anchor
    up_ext = dev >= Z * a
    dn_ext = dev <= -Z * a
    if decision_stops(ask(
        "msr_extension",
        not (up_ext or dn_ext),
        "extension_absent",
        "extension_present",
        "Price has not extended Z ATR from the NY anchor.",
        "Price has extended Z ATR from the NY anchor.",
        symbol=symbol,
        dev=dev,
        atr=a,
    )):
        return None
    earlier = _earlier_extension(bars, ny, i, anchor, up_ext, dn_ext)
    if decision_stops(ask(
        "msr_earlier_extension",
        earlier,
        "earlier_extension_owns_the_day",
        "first_extension_this_direction",
        "An earlier same-direction extension already printed today.",
        "This is the first extension in this direction today.",
        symbol=symbol,
    )):
        return None
    regime = _regime(bars, i, a)
    if decision_stops(ask(
        "msr_uptrend",
        regime == "up",
        "uptrend_withholds",
        "fade_is_open",
        "The higher-timeframe regime is up, so the fade withholds.",
        "The higher-timeframe regime is down or range, so the fade is open.",
        symbol=symbol,
        regime=regime,
    )):
        return None
    if regime is None:
        return None
    side = ask(
        "msr_fade_side",
        up_ext,
        "fade_the_up_extension",
        "fade_the_down_extension",
        "The extension is up, so the fade is short.",
        "The extension is down, so the fade is long.",
        symbol=symbol,
        dev=dev,
    )
    if side == "true":
        direction = -1
    elif side is None:
        return None
    else:
        direction = 1
    sd = STOP_K * a
    if decision_stops(ask(
        "msr_stop",
        sd <= 0,
        "stop_not_positive",
        "stop_positive",
        "The stop distance is not positive.",
        "The stop distance is positive.",
        symbol=symbol,
        stop_dist=sd,
    )):
        return None
    if not (sd > 0):
        return None
    return TradeIntent(sleeve="metal_session_reversion", symbol=symbol, direction=direction,
                       decision_day=decision_day, stop_dist=sd, target_dist=None)
