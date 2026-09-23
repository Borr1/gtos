"""Widened container beside orb_crypto_london.

The multiple is the widen score on the opening-range pack. An empty score
does not scale the stop and does not restore a printed multiple.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from ..admission import TradeIntent
from . import orb_crypto_london

ON_SURFACE = orb_crypto_london.ON_SURFACE


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **kw) -> Optional[TradeIntent]:
    intent = orb_crypto_london.generate(
        symbol, bars, decision_day, bar_time=bar_time, bar_times=bar_times,
        aux_bars=aux_bars, aux_times=aux_times, **kw)
    if intent is None:
        return None
    multiple = orb_crypto_london.cached_number(
        symbol, bars, decision_day, bar_time, bar_times, "widen_k",
    )
    if multiple is None or not (multiple > 0):
        return None
    stop_dist = intent.stop_dist * multiple
    target = None if intent.target_dist is None else intent.target_dist * multiple
    if not (stop_dist > 0):
        return None
    widened = replace(
        intent,
        sleeve="orb_crypto_london_widen",
        stop_dist=stop_dist,
        target_dist=target,
    )
    return widened
