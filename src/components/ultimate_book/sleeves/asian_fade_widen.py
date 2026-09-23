"""Widened Asian fade.

Entry is asian_fade.generate. The floor multiple and the target multiple
are scores for this bar. An empty score does not restore a printed level
and does not divide by the parent's stop multiple.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from ..admission import TradeIntent
from ..primitives import atr14
from . import asian_fade
from . import fx_spot

ON_SURFACE = asian_fade.ON_SURFACE
_SCORES = {
    "floor_mult": "The score you return is the ATR multiple of the widened fade stop.",
    "target_r": "The score you return is the reward multiple of that widened stop.",
}


def generate(symbol, bars, decision_day, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **kw) -> Optional[TradeIntent]:
    """Widen only when the parent emitted and both scores came back positive."""
    intent = asian_fade.generate(
        symbol, bars, decision_day, bar_time=bar_time, bar_times=bar_times,
        aux_bars=aux_bars, aux_times=aux_times, **kw)
    if intent is None or not bars:
        return None
    i = len(bars) - 1
    try:
        atr = fx_spot.finite(atr14(bars, i))
    except Exception:
        atr = None
    if atr is None or not (atr > 0):
        return None
    n = len(bars)
    times_ok = bool(bar_times) and len(bar_times) == n
    latest = bar_times[i] if times_ok else bar_time
    previous = bar_times[i - 1] if times_ok and i >= 1 else None
    state = fx_spot.book_state(
        "asian_fade_widen",
        symbol,
        decision_day=decision_day,
        n_bars=n,
        parent_emitted=True,
        parent_stop=float(intent.stop_dist),
        atr=float(atr),
    )
    remain = fx_spot.seconds_until_next_print(latest, previous, now=kw.get("runtime_now"))
    if remain is not None:
        state["seconds_from_clock"] = remain
    packed = fx_spot.ask_pack(_SCORES, state, bars=bars, index=i, bar_times=bar_times)
    scores = packed.get("scores") or {}
    floor_mult = fx_spot.finite(scores.get("floor_mult"))
    target_r = fx_spot.finite(scores.get("target_r"))
    if floor_mult is None or target_r is None or not (floor_mult > 0) or not (target_r > 0):
        return None
    stop_dist = max(floor_mult * atr, float(intent.stop_dist))
    if not (stop_dist > 0):
        return None
    return replace(
        intent,
        sleeve="asian_fade_widen",
        stop_dist=stop_dist,
        target_dist=target_r * stop_dist,
    )
