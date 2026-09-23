"""Widened NY crypto continuation.

The widened stop multiple is on the parent pack. An empty score does not
restore a printed ratio of the parent stop.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from ..admission import TradeIntent
from . import fx_spot
from . import ny_crypto_momentum

ON_SURFACE = ny_crypto_momentum.ON_SURFACE


def generate(symbol, bars, decision_day, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **kw) -> Optional[TradeIntent]:
    intent = ny_crypto_momentum.generate(
        symbol, bars, decision_day, bar_time=bar_time, bar_times=bar_times,
        aux_bars=aux_bars, aux_times=aux_times, **kw)
    if intent is None:
        return None
    held = ny_crypto_momentum.last_bounds(symbol, bars, decision_day, bar_time) or {}
    scores = held.get("scores") or {}
    widen = fx_spot.finite(scores.get("widen_stop_mult"))
    atr = fx_spot.finite(held.get("atr"))
    if widen is None or atr is None or not (widen > 0) or not (atr > 0):
        return None
    stop_dist = widen * atr
    if not (stop_dist > 0):
        return None
    return replace(intent, sleeve="ny_crypto_momentum_widen", stop_dist=stop_dist)
