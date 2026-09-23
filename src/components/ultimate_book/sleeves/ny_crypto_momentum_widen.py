"""ny_crypto_momentum_widen — F5-only WIDEN container beside ny_crypto_momentum.

STOP_MULT 2.75 vs incumbent 1.3 (binding k=2.10 rounded up). Container
unchanged. OPUS-F5-MAXVALUE §3.3.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Optional

from ..admission import TradeIntent
from . import ny_crypto_momentum

ON_SURFACE = ny_crypto_momentum.ON_SURFACE
STOP_MULT = 2.75


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **kw) -> Optional[TradeIntent]:
    intent = ny_crypto_momentum.generate(
        symbol, bars, decision_day, bar_time=bar_time, bar_times=bar_times,
        aux_bars=aux_bars, aux_times=aux_times, **kw)
    if intent is None:
        return None
    sd = intent.stop_dist * (STOP_MULT / ny_crypto_momentum.STOP_MULT)
    if sd <= 0:
        return None
    return replace(intent, sleeve="ny_crypto_momentum_widen", stop_dist=sd)
