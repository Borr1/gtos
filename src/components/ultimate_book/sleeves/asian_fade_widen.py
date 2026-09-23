"""asian_fade_widen — F5-only WIDEN container beside asian_fade.

Entry is asian_fade.generate, then the sleeve name and stop/target are
replaced. Incumbent STOP_K=0.6 and trailing_runner
(min lock 0.0R) stay on tag asian_fade. OPUS-F5-MAXVALUE §3.2.
"""
from __future__ import annotations

from . import fx_spot

from dataclasses import replace
from typing import Optional

from ..admission import TradeIntent
from ..frozen_price_intent import MARKET_STOP_MIN_PIPS, fx_pip_size
from . import asian_fade

ON_SURFACE = asian_fade.ON_SURFACE
ATR_FLOOR_MULT = 1.0
TARGET_R = 2.0


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **kw) -> Optional[TradeIntent]:
    """Widen the Asian fade only when both spots' continue sides are the unique highest."""
    intent = asian_fade.generate(
        symbol, bars, decision_day, bar_time=bar_time, bar_times=bar_times,
        aux_bars=aux_bars, aux_times=aux_times, **kw)
    parent_emitted = intent is not None
    stop_dist = 0.0
    if parent_emitted:
        atr = intent.stop_dist / asian_fade.STOP_K
        pip = fx_pip_size(symbol=symbol)
        floor_pip = (MARKET_STOP_MIN_PIPS * pip) if pip else 0.0
        stop_dist = max(ATR_FLOOR_MULT * atr, floor_pip, intent.stop_dist)
    stop_ok = bool(stop_dist > 0.0)
    state = fx_spot.book_state(
        "asian_fade_widen",
        symbol,
        parent_emitted=parent_emitted,
        stop_positive=stop_ok,
        stop_dist=float(stop_dist) if stop_ok else None,
        pattern_printed=bool(parent_emitted and stop_ok),
        decision_day=decision_day,
        n_bars=len(bars) if bars else 0,
    )
    ask = "Which side of this condition is this bar?"
    questions = {
        "parent": fx_spot.q(
            "parent_emitted",
            "The Asian fade already emitted an intent on this bar.",
            "parent_silent",
            "The Asian fade did not emit an intent on this bar.",
            ask,
        ),
        "stop": fx_spot.q(
            "stop_is_the_plan",
            "The widened stop distance is positive.",
            "stop_not_positive",
            "The widened stop distance is not positive.",
            ask,
        ),
    }
    picks = fx_spot.unique_sides(
        questions,
        state,
        f"asian_fade_widen|{symbol}|{state['n_bars']}|{decision_day}",
    )
    if not fx_spot.continues(picks, questions):
        return None
    if intent is None or not stop_ok:
        return None
    return replace(
        intent,
        sleeve="asian_fade_widen",
        stop_dist=stop_dist,
        target_dist=TARGET_R * stop_dist,
    )
