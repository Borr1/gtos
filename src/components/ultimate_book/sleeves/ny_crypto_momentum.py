"""NY-killzone crypto continuation.

The efficiency level, the stop, the window, the decision clock, the
volatility band, and the time stop are scores for this bar. An empty
score does not restore a printed level. Direction is the sign of the
window net after those bounds exist. A flat net does not emit.
The widen container reads the same pack.
"""
from __future__ import annotations

from typing import Any, Optional

from ..admission import TradeIntent
from ..primitives import atr14
from ._server_clock import server_hour_minute
from . import fx_spot

ON_SURFACE = ("BTCUSD", "ETHUSD")
SLEEVE = "ny_crypto_momentum"
_SCORES = {
    "de_thresh": "The score you return is the absolute directional-efficiency level that opens this bar.",
    "stop_mult": "The score you return is the ATR multiple of the stop on this bar.",
    "widen_stop_mult": "The score you return is the ATR multiple of the stop on the widened container.",
    "window": "The score you return is how many closed bars the efficiency window uses.",
    "decision_hour": "The score you return is the server hour of the decision bar.",
    "decision_min": "The score you return is the minute of the decision bar.",
    "maxbars": "The score you return is how many bars this position may stay open.",
    "vol_win": "The score you return is how many trailing ATR values the percentile uses.",
    "vol_lo": "The score you return is the low edge of the volatility percentile band.",
    "vol_hi": "The score you return is the high edge of the volatility percentile band.",
    "min_bars": "The score you return is how many closed bars this scan needs.",
    "hist_min": "The score you return is how many positive ATR values the percentile needs.",
}
_LAST: dict[tuple, dict] = {}


def _hm(t):
    """Server-local hour and minute. None when the stamp cannot be read."""
    return server_hour_minute(t)


def _positive(value):
    number = fx_spot.finite(value)
    if number is None or not (number > 0):
        return None
    return number


def _whole(value, *, least: int = 0):
    number = fx_spot.whole(value)
    if number is None or number < least:
        return None
    return number


def _key(symbol, bars, decision_day, bar_time) -> tuple:
    return (str(symbol), str(decision_day), len(bars) if bars else 0, str(bar_time))


def last_bounds(symbol, bars, decision_day, bar_time) -> dict | None:
    """The pack this bar already asked. None when this bar was not asked."""
    return _LAST.get(_key(symbol, bars, decision_day, bar_time))


def _rank(bars, i: int, vol_win: int, hist_min: int) -> float | None:
    if i < vol_win:
        return None
    current = _positive(atr14(bars, i))
    if current is None:
        return None
    hist = []
    for k in range(i - vol_win, i):
        value = _positive(atr14(bars, k))
        if value is not None:
            hist.append(value)
    if len(hist) < hist_min:
        return None
    return sum(1 for value in hist if value <= current) / len(hist)


def _ask(symbol, bars, decision_day, bar_time, bar_times) -> dict[str, Any]:
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    stamp = bar_time
    if stamp is None and bar_times and n and len(bar_times) == n:
        stamp = bar_times[i]
    hm = _hm(stamp) if stamp is not None else None
    previous = None
    if bar_times and n and len(bar_times) == n and i >= 1:
        previous = bar_times[i - 1]
    state = fx_spot.book_state(
        SLEEVE,
        symbol,
        decision_day=decision_day,
        n_bars=n,
        bar_index=i,
        hour=None if hm is None else hm[0],
        minute=None if hm is None else hm[1],
        clock_known=hm is not None,
        atr=_positive(atr14(bars, i)) if bars and i >= 0 else None,
        on_named_surface=symbol in ON_SURFACE,
        named_surface=list(ON_SURFACE),
    )
    remain = fx_spot.seconds_until_next_print(stamp, previous)
    if remain is not None:
        state["seconds_from_clock"] = remain
    choices = {
        "surface": {
            "instructions": (
                "Is this symbol one of the named crypto symbols for this bar? "
                "The names are a fact. An empty answer, a tie, or an error is not a side."
            ),
            "criteria": {
                "on_surface": f"{symbol} is BTCUSD or ETHUSD.",
                "off_surface": f"{symbol} is not BTCUSD or ETHUSD.",
            },
        }
    }
    packed = fx_spot.ask_pack(_SCORES, state, choices=choices, bars=bars, index=i, bar_times=bar_times)
    _LAST[_key(symbol, bars, decision_day, bar_time)] = {
        "scores": dict(packed.get("scores") or {}),
        "atr": state.get("atr"),
    }
    return packed


def generate(symbol, bars, decision_day, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """One post. A missing bound, including the time stop, does not emit."""
    del aux_bars, aux_times
    if not bars:
        return None
    packed = _ask(symbol, bars, decision_day, bar_time, bar_times)
    if packed.get("sides", {}).get("surface") != "on_surface":
        return None
    scores = packed.get("scores") or {}
    i = len(bars) - 1
    min_bars = _whole(scores.get("min_bars"), least=1)
    window = _whole(scores.get("window"), least=1)
    vol_win = _whole(scores.get("vol_win"), least=1)
    hist_min = _whole(scores.get("hist_min"), least=1)
    decision_hour = _whole(scores.get("decision_hour"), least=0)
    decision_min = _whole(scores.get("decision_min"), least=0)
    horizon = _whole(scores.get("maxbars"), least=1)
    de_thresh = _positive(scores.get("de_thresh"))
    stop_mult = _positive(scores.get("stop_mult"))
    vol_lo = fx_spot.finite(scores.get("vol_lo"))
    vol_hi = fx_spot.finite(scores.get("vol_hi"))
    if None in (
        min_bars, window, vol_win, hist_min, decision_hour, decision_min,
        horizon, de_thresh, stop_mult, vol_lo, vol_hi,
    ):
        return None
    if vol_hi <= vol_lo or i < min_bars or i < window:
        return None
    stamp = bar_time if bar_time is not None else (
        bar_times[i] if bar_times and len(bar_times) == len(bars) else None
    )
    hm = _hm(stamp) if stamp is not None else None
    if hm is None or hm[0] != decision_hour or hm[1] != decision_min:
        return None
    atr = _positive(atr14(bars, i))
    if atr is None:
        return None
    span = bars[i - window:i + 1]
    high = max(bar.h for bar in span)
    low = min(bar.l for bar in span)
    width = high - low
    if not (width > 0):
        return None
    net = bars[i].c - bars[i - window].c
    if abs(net) / width < de_thresh:
        return None
    rank = _rank(bars, i, vol_win, hist_min)
    if rank is None or not (vol_lo <= rank < vol_hi):
        return None
    if net > 0:
        direction = 1
    elif net < 0:
        direction = -1
    else:
        return None
    stop_dist = stop_mult * atr
    if not (stop_dist > 0):
        return None
    held = _LAST.get(_key(symbol, bars, decision_day, bar_time)) or {}
    held["atr"] = atr
    held["stop_mult"] = stop_mult
    _LAST[_key(symbol, bars, decision_day, bar_time)] = held
    return TradeIntent(
        sleeve=SLEEVE,
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=stop_dist,
        target_dist=None,
        expiry_bars=horizon,
    )
