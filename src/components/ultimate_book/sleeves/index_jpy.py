"""idxrev — failed-breakout fade on the latest closed H4 bar.

The range lookback, the stop multiple, the target multiple, and the warmup
are scores for this bar. An empty score does not restore a printed level.
The wick that closes back inside is geometry after the lookback exists.
The named index symbols stay a fact.
"""
from __future__ import annotations

from typing import Optional

from ..admission import TradeIntent
from ..primitives import atr14
from . import fx_spot

IDXREV_SLEEVE = "idxrev"
IDXREV_ON_SURFACE = ("SPX500", "UK100", "JP225", "GER40")
_SCORES = {
    "range_bars": "The score you return is how many prior bars define the range.",
    "stop_atr": "The score you return is the ATR multiple of the fade stop.",
    "target_r": "The score you return is the reward multiple of that stop.",
    "warmup_bars": "The score you return is how many closed bars this scan needs.",
}


def _positive(value):
    number = fx_spot.finite(value)
    if number is None or not (number > 0):
        return None
    return number


def _whole(value, *, least: int = 1):
    number = fx_spot.whole(value)
    if number is None or number < least:
        return None
    return number


def fade_facts(bars, i, lookback=None):
    """Measured wick-fade facts for a returned lookback. Not a decision."""
    try:
        raw = atr14(bars, i) if bars else None
    except Exception:
        raw = None
    atr = _positive(raw)
    direction = 0
    span = _whole(lookback)
    if bars and atr is not None and span is not None and i >= span:
        rhi = max(bars[k].h for k in range(i - span, i))
        rlo = min(bars[k].l for k in range(i - span, i))
        bar = bars[i]
        if bar.h > rhi and bar.c < rhi:
            direction = -1
        elif bar.l < rlo and bar.c > rlo:
            direction = 1
    return {
        "atr": atr,
        "direction": direction,
        "pattern_absent": direction == 0,
    }


def idxrev_signal(B, atrs, i, lookback=None, stop_mult=None) -> Optional[tuple[int, float]]:
    """(direction, stop_dist) when the returned bounds and a fade wick exist.

    Missing bounds stay unset. This does not fill a lookback or a stop multiple.
    """
    del atrs
    span = _whole(lookback)
    mult = _positive(stop_mult)
    facts = fade_facts(B, i, span)
    if span is None or mult is None or facts["direction"] not in (1, -1) or facts["atr"] is None:
        return None
    return facts["direction"], mult * facts["atr"]


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, **_) -> Optional[TradeIntent]:
    """One post. The scores are the bounds. A missing bound does not emit."""
    del bar_time
    if not bars:
        return None
    i = len(bars) - 1
    try:
        atr = _positive(atr14(bars, i))
    except Exception:
        atr = None
    state = fx_spot.book_state(
        IDXREV_SLEEVE,
        symbol,
        decision_day=decision_day,
        n_bars=len(bars),
        bar_index=i,
        atr=atr,
        on_named_surface=symbol in IDXREV_ON_SURFACE,
        named_surface=list(IDXREV_ON_SURFACE),
    )
    choices = {
        "surface": {
            "instructions": (
                "Is this symbol one of the named index symbols for this bar? "
                "The names are a fact. An empty answer, a tie, or an error is not a side."
            ),
            "criteria": {
                "on_surface": f"{symbol} is one of SPX500, UK100, JP225, GER40.",
                "off_surface": f"{symbol} is not one of those index symbols.",
            },
        }
    }
    packed = fx_spot.ask_pack(_SCORES, state, choices=choices, bars=bars, index=i)
    if packed.get("sides", {}).get("surface") != "on_surface":
        return None
    scores = packed.get("scores") or {}
    warmup = _whole(scores.get("warmup_bars"))
    span = _whole(scores.get("range_bars"))
    stop_mult = _positive(scores.get("stop_atr"))
    target_r = _positive(scores.get("target_r"))
    if None in (warmup, span, stop_mult, target_r):
        return None
    if i < warmup or atr is None:
        return None
    facts = fade_facts(bars, i, span)
    if facts["direction"] not in (1, -1) or facts["atr"] is None:
        return None
    stop_dist = stop_mult * facts["atr"]
    if not (stop_dist > 0):
        return None
    return TradeIntent(
        sleeve=IDXREV_SLEEVE,
        symbol=symbol,
        direction=facts["direction"],
        decision_day=decision_day,
        stop_dist=stop_dist,
        target_dist=target_r * stop_dist,
    )
