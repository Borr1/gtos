"""Asian-range fade on EURUSD and GBPUSD.

The break buffer, the stop, the rejection wick, the trail, the time stop,
and the session hours are scores for this bar. An empty score does not
restore a printed level. Which side broke is the geometry after those
bounds exist. The trail scores are required here; the intent has no trail
fields, so the exit profile that is not in this file still has to read them.
"""
from __future__ import annotations

from typing import Optional

from ..admission import TradeIntent
from ..primitives import atr14
from ._server_clock import server_day, server_hour
from . import fx_spot

ON_SURFACE = ("EURUSD", "GBPUSD")
_SCORES = {
    "buf_k": "The score you return is the ATR multiple beyond the Asian range that counts as a break.",
    "stop_k": "The score you return is the ATR multiple of the fade stop.",
    "reject_frac": "The score you return is the ATR multiple of the rejection wick back inside the range.",
    "trail_arm": "The score you return is how many stop-units of favorable move arm the trail.",
    "trail_gap": "The score you return is how many stop-units the trail sits behind the best excursion.",
    "maxbars": "The score you return is how many bars this position may stay open.",
    "min_bars": "The score you return is how many closed bars this scan needs.",
    "asian_end_hour": "The score you return is the last server hour included in the Asian range.",
    "entry_lo_hour": "The score you return is the first server hour of the entry window.",
    "entry_hi_hour": "The score you return is the last server hour of the entry window.",
    "min_asian_bars": "The score you return is how many Asian-session bars the range needs.",
}
_LAST: dict[tuple, dict] = {}


def _hour(t):
    """Server-local hour. None when the stamp cannot be read."""
    return server_hour(t)


def _day(t):
    """Server-local date. None when the stamp cannot be read."""
    return server_day(t)


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


def _atr(bars, i):
    if bars is None or i < 0:
        return None
    try:
        raw = atr14(bars, i)
    except Exception:
        return None
    return _positive(raw)


def _key(symbol, bars, decision_day, bar_time) -> tuple:
    return (str(symbol), str(decision_day), len(bars) if bars else 0, str(bar_time))


def _facts(symbol, bars, decision_day, bar_time, bar_times) -> dict:
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    times_ok = bool(bar_times) and n > 0 and len(bar_times) == n
    hour = _hour(bar_times[i]) if times_ok else None
    day = _day(bar_times[i]) if times_ok else None
    latest = bar_times[i] if times_ok else bar_time
    previous = bar_times[i - 1] if times_ok and i >= 1 else None
    state = fx_spot.book_state(
        "asian_fade",
        symbol,
        decision_day=decision_day,
        n_bars=n,
        bar_index=i,
        hour=hour,
        day=str(day) if day is not None else None,
        atr=_atr(bars, i),
        on_named_surface=symbol in ON_SURFACE,
        named_surface=list(ON_SURFACE),
        times_aligned=times_ok,
    )
    remain = fx_spot.seconds_until_next_print(latest, previous)
    if remain is not None:
        state["seconds_from_clock"] = remain
    return state


def _choices(symbol) -> dict:
    return {
        "surface": {
            "instructions": (
                "Is this symbol one of the named Asian-fade symbols for this bar? "
                "The names are a fact. An empty answer, a tie, or an error is not a side."
            ),
            "criteria": {
                "on_surface": f"{symbol} is EURUSD or GBPUSD.",
                "off_surface": f"{symbol} is not EURUSD or GBPUSD.",
            },
        }
    }


def spot_pack(symbol, bars, decision_day, *, bar_time=None, bar_times=None, aux_bars=None, aux_times=None, **_):
    """One post. Scores are the bounds. The surface is a choice on the same post."""
    del aux_bars, aux_times
    facts = _facts(symbol, bars, decision_day, bar_time, bar_times)
    i = len(bars) - 1 if bars else None
    return fx_spot.ask_pack(
        _SCORES, facts, choices=_choices(symbol), bars=bars, index=i, bar_times=bar_times,
    )


def _first_break(bars, bar_times, i, day, scores):
    """The first entry-window rejection break, or None."""
    end_hour = _whole(scores.get("asian_end_hour"), least=0)
    lo_hour = _whole(scores.get("entry_lo_hour"), least=0)
    hi_hour = _whole(scores.get("entry_hi_hour"), least=0)
    min_asian = _whole(scores.get("min_asian_bars"))
    buf_k = _positive(scores.get("buf_k"))
    reject = _positive(scores.get("reject_frac"))
    if None in (end_hour, lo_hour, hi_hour, min_asian, buf_k, reject):
        return None
    if hi_hour < lo_hour:
        return None
    same = []
    for j in range(i + 1):
        if _day(bar_times[j]) == day:
            same.append(j)
    asian = [j for j in same if (lambda h: h is not None and h <= end_hour)(_hour(bar_times[j]))]
    if len(asian) < min_asian:
        return None
    ahi = max(bars[j].h for j in asian)
    alo = min(bars[j].l for j in asian)
    if not (ahi > alo):
        return None
    for k in same:
        hour = _hour(bar_times[k])
        if hour is None or not (lo_hour <= hour <= hi_hour):
            continue
        ak = _atr(bars, k)
        if ak is None:
            continue
        buf = buf_k * ak
        bar = bars[k]
        side = 0
        if bar.h >= ahi + buf and bar.c < bar.h and (bar.h - bar.c) >= reject * ak:
            side = -1
        elif bar.l <= alo - buf and bar.c > bar.l and (bar.c - bar.l) >= reject * ak:
            side = 1
        if side == 0:
            continue
        return k, side, ak
    return None


def generate(symbol, bars, decision_day, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Emit when every bound came back and this bar is the first rejection break."""
    if not bars or not bar_times or len(bar_times) != len(bars):
        return None
    packed = spot_pack(
        symbol, bars, decision_day,
        bar_time=bar_time, bar_times=bar_times,
        aux_bars=aux_bars, aux_times=aux_times,
    )
    if packed.get("sides", {}).get("surface") != "on_surface":
        return None
    scores = packed.get("scores") or {}
    i = len(bars) - 1
    min_bars = _whole(scores.get("min_bars"))
    stop_k = _positive(scores.get("stop_k"))
    trail_arm = _positive(scores.get("trail_arm"))
    trail_gap = _positive(scores.get("trail_gap"))
    horizon = _whole(scores.get("maxbars"))
    if None in (min_bars, stop_k, trail_arm, trail_gap, horizon):
        return None
    if i < min_bars:
        return None
    day = _day(bar_times[i])
    if day is None or _atr(bars, i) is None:
        return None
    found = _first_break(bars, bar_times, i, day, scores)
    if found is None:
        return None
    k, side, ak = found
    if k != i or side not in (1, -1):
        return None
    stop_dist = stop_k * ak
    if not (stop_dist > 0):
        return None
    _LAST[_key(symbol, bars, decision_day, bar_time)] = {
        "trail_arm": trail_arm,
        "trail_gap": trail_gap,
        "stop_dist": stop_dist,
        "atr": ak,
    }
    return TradeIntent(
        sleeve="asian_fade",
        symbol=symbol,
        direction=side,
        decision_day=decision_day,
        stop_dist=stop_dist,
        target_dist=None,
        expiry_bars=horizon,
    )
