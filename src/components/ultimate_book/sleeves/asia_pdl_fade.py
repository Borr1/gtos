"""asia_pdl_fade.py — NEW SLEEVE: Asian-session prior-day-LOW liquidity-sweep reversal (M15, broad universe).

8th new sleeve (2026-06-17), PRINCIPAL-VERIFIED. The BROADEST-breadth sleeve: during the Asian session, when
price sweeps the PRIOR calendar day's LOW (pierces below it) and RECLAIMS (closes back above), FADE it LONG to a
3R target. A cross-asset liquidity-sweep-reversal applied across 30 deployable symbols (FX majors+crosses, metals,
crypto, crude, indices). NATGAS_cash is intentionally split out: the Docker MT5 bridge spec/tick proof and KB7
tick-spread truth show its cost/liquidity is a separate research-revival lane, not a deployable carrier.

PRINCIPAL re-derivation (my own, matches the correct-null sweep wf_77c9d7db) plus NATGAS split:
pooled n=7524, every-split positive (train +0.110 / oos +0.015 / sealed +0.164), LONG-only, 22/30 deployable
symbols positive, positive 12/13 years (2023 negative). The agent's CORRECT random-entry
null = p=0.0033 (the sweep+reclaim entry beats random) + drift null p=0.0025. HONEST CAVEAT: the oos (2022-2024)
is THIN (+0.015, 2023 negative) -> recency+early tilted; positive every split but the middle period is weak.
DEFAULT-OFF candidate; live wiring owner-gated.

MECHANIC (leak-free, decides on the latest CLOSED M15 bar i): only during the Asian session (server hour 0..6).
PDL = MIN low over the PRIOR completed calendar day's bars (strictly before today). LONG when: low[i] < PDL -
PIERCE*ATR (sweep) AND close[i] > PDL (reclaim) AND close[i-1] >= PDL (fresh, not already above), and i is the
FIRST Asian bar today to do so. stop = (close[i]-low[i]) + 0.10*ATR (beyond the sweep wick); target = 3R; 32-bar
time-stop. Decision uses only bars <= i; the PDL is from a fully-completed prior day; entry at close[i].
"""
from __future__ import annotations
from typing import Optional
from ..primitives import atr14
from ..admission import TradeIntent
from ._server_clock import server_day, server_hour
from .spot_choice import all_false, ask, bar_id

PIERCE = 0.05            # sweep pierce in ATR units below PDL
STOP_BUF = 0.10          # stop buffer in ATR units beyond the sweep wick
TARGET_R = 3.0
MAXBARS = 32
ASIA_HI = 6              # Asian session = server hour 0..6
MIN_BARS = 120
ON_SURFACE = (
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURJPY", "GBPJPY", "CHFJPY", "AUDJPY", "EURGBP",
    "XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD",
    "BTCUSD", "ETHUSD", "XRPUSD", "XTZUSD", "LTCUSD", "DASHUSD",
    "USOIL_cash", "UKOIL_cash",
    "GER40", "UK100", "SPX500", "NAS100", "JP225",
)
EXCLUDED_COST_REPAIR_SYMBOLS = ("NATGAS_cash",)


def _hour(t):
    """SERVER-LOCAL hour. The session constants here are FTMO server hours (F7/B29); the
    live feed is true UTC, so this converts before comparing. None -> fail closed."""
    return server_hour(t)


def _day(t):
    """SERVER-LOCAL date key. The route grouped prior-day levels and session ranges on
    SERVER days, not UTC days (F7/B29). NOT the correlated-unit key. None -> fail closed."""
    return server_day(t)


def _swept_reclaimed_long(bars, k, pdl, a):
    """LONG sweep+reclaim test at bar k: pierced below PDL, closed back above, prior close not already above."""
    pierce = PIERCE * a
    return bars[k].l < pdl - pierce and bars[k].c > pdl and bars[k - 1].c >= pdl


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Emit an Asian PDL sweep-reversal LONG TradeIntent on the latest closed M15 bar, else None. Leak-free."""
    if not bars or not bar_times or len(bar_times) != len(bars):
        return None
    i = len(bars) - 1
    hi = _hour(bar_times[i])
    if hi is None:
        return None
    today = _day(bar_times[i])
    if today is None:
        return None
    a = atr14(bars, i)
    if a <= 0:
        return None
    prior_day = None
    pdl = None
    for k in range(i, -1, -1):
        dk = _day(bar_times[k])
        if dk == today:
            continue
        if prior_day is None:
            prior_day = dk
        if dk == prior_day:
            pdl = bars[k].l if pdl is None else min(pdl, bars[k].l)
        else:
            break
    if pdl is None:
        return None
    off_surface = symbol not in ON_SURFACE
    warmup_short = i < MIN_BARS
    outside_asia = hi > ASIA_HI
    pattern_absent = True
    already = False
    if i >= 1:
        pattern_absent = not _swept_reclaimed_long(bars, i, pdl, a)
        for k in range(i - 1, -1, -1):
            if _day(bar_times[k]) != today:
                break
            hk = _hour(bar_times[k])
            if hk is None or hk > ASIA_HI:
                continue
            ak = atr14(bars, k)
            if ak > 0 and k >= 1 and _swept_reclaimed_long(bars, k, pdl, ak):
                already = True
                break
    sd = (bars[i].c - bars[i].l) + STOP_BUF * a
    if sd <= 0:
        return None
    sides = ask(
        sleeve="asia_pdl_fade",
        symbol=symbol,
        bar_id=bar_id(decision_day, i, bar_time, bar_times),
        spots={
            "off_surface": {
                "condition": f"symbol {symbol} is not in ON_SURFACE",
                "measured": off_surface,
            },
            "warmup_short": {
                "condition": f"latest bar index {i} is below {MIN_BARS}",
                "measured": warmup_short,
            },
            "outside_asia": {
                "condition": f"server hour {hi} is above {ASIA_HI}",
                "measured": outside_asia,
            },
            "pattern_absent": {
                "condition": "the latest closed bar did not sweep below the prior-day low and reclaim above it",
                "measured": pattern_absent,
            },
            "already_faded": {
                "condition": "an earlier Asian bar today already swept and reclaimed the prior-day low",
                "measured": already,
            },
        },
    )
    if not all_false(sides):
        return None
    return TradeIntent(sleeve="asia_pdl_fade", symbol=symbol, direction=1,
                       decision_day=decision_day, stop_dist=sd, target_dist=TARGET_R * sd)
