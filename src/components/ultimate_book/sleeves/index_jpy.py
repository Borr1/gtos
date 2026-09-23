"""Index + JPY sleeves.

idxrev (build-now): H4 failed-breakout fade — byte-faithful to INTEG_portfolio_build.gen_idxrev
(lines 180-198): LB=16, STOP_ATR=1.5, TGT_R=0.75, MAXBARS=60. On the latest closed H4 bar i (>=120),
a wick beyond the prior-16-bar range that CLOSES back inside fades it. On-surface (of 24): SPX500,
UK100, JP225, GER40, US30_cash (FRA40_cash/EU50_cash/US2000_cash off-surface).

fx_jpy / fx_jpy_ny: M15 session-open momentum (GBPJPY/USDJPY) — BUILT + live in sleeves/fx_jpy.py.
This module is idxrev-only; the JPY session sleeves are NOT here (see sleeves/fx_jpy.py).
"""
from __future__ import annotations
from typing import Optional

from ..primitives import atr14
from ..admission import TradeIntent
from .spot_choice import all_false, ask, bar_id

IDXREV_SLEEVE = "idxrev"
IDXREV_ON_SURFACE = ("SPX500", "UK100", "JP225", "GER40")
IDX_LB = 16
IDX_STOP_ATR = 1.5
IDX_TGT_R = 0.75


def fade_facts(bars, i):
    """Measured wick-fade facts. Not a decision."""
    a = atr14(bars, i) if bars else 0.0
    warmup_short = i < 120
    atr_not_a_scale = not (a > 0)
    fade_short = False
    fade_long = False
    if bars and not warmup_short and not atr_not_a_scale and i >= IDX_LB:
        rhi = max(bars[k].h for k in range(i - IDX_LB, i))
        rlo = min(bars[k].l for k in range(i - IDX_LB, i))
        b = bars[i]
        fade_short = b.h > rhi and b.c < rhi
        fade_long = b.l < rlo and b.c > rlo
    if fade_short:
        direction = -1
    elif fade_long:
        direction = 1
    else:
        direction = 0
    return {
        "atr": float(a),
        "warmup_short": warmup_short,
        "atr_not_a_scale": atr_not_a_scale,
        "pattern_absent": direction == 0,
        "direction": direction,
    }


def idxrev_signal(B, atrs, i) -> Optional[tuple[int, float]]:
    """Measured (direction, stop_dist) when a fade wick exists, else None.

    The live decision is generate()'s Choice, not this tuple.
    """
    facts = fade_facts(B, i)
    if facts["direction"] not in (1, -1) or not (facts["atr"] > 0):
        return None
    return facts["direction"], IDX_STOP_ATR * facts["atr"]


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, **_) -> Optional[TradeIntent]:
    """Live idxrev on the latest closed H4 bar. Each gate is one spot Choice."""
    if not bars:
        return None
    i = len(bars) - 1
    facts = fade_facts(bars, i)
    sides = ask(
        sleeve=IDXREV_SLEEVE,
        symbol=symbol,
        bar_id=bar_id(decision_day, len(bars), bar_time, _.get("bar_times")),
        spots={
            "off_surface": {
                "condition": f"{symbol} is not one of SPX500, UK100, JP225, GER40",
                "measured": symbol not in IDXREV_ON_SURFACE,
            },
            "warmup_short": {
                "condition": f"closed H4 index {i} is below 120",
                "measured": facts["warmup_short"],
            },
            "atr_not_a_scale": {
                "condition": "ATR14 is not a positive scale for the 1.5 stop",
                "measured": facts["atr_not_a_scale"],
            },
            "pattern_absent": {
                "condition": "the latest closed bar has no wick beyond the prior 16-bar range that closes back inside",
                "measured": facts["pattern_absent"],
            },
        },
    )
    if not all_false(sides):
        return None
    if facts["direction"] not in (1, -1) or not (facts["atr"] > 0):
        return None
    sd = IDX_STOP_ATR * facts["atr"]
    return TradeIntent(
        sleeve=IDXREV_SLEEVE,
        symbol=symbol,
        direction=facts["direction"],
        decision_day=decision_day,
        stop_dist=sd,
        target_dist=IDX_TGT_R * sd,
    )
