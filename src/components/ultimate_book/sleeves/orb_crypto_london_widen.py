"""orb_crypto_london_widen — F5-only WIDEN container beside orb_crypto_london.

k=1.72 floor on the incumbent OR-width stop. Container unchanged.
OPUS-F5-MAXVALUE §3.4.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from ..admission import TradeIntent
from . import orb_crypto_london

ON_SURFACE = orb_crypto_london.ON_SURFACE
K = 1.72


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **kw) -> Optional[TradeIntent]:
    intent = orb_crypto_london.generate(
        symbol, bars, decision_day, bar_time=bar_time, bar_times=bar_times,
        aux_bars=aux_bars, aux_times=aux_times, **kw)
    if intent is None:
        return None
    sd = intent.stop_dist * K
    td = None if intent.target_dist is None else intent.target_dist * K
    if sd <= 0:
        return None
    return replace(intent, sleeve="orb_crypto_london_widen", stop_dist=sd,
                   target_dist=td)
