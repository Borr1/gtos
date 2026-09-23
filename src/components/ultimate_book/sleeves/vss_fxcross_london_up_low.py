"""London FX-cross M15 squeeze break.

The box, the percentile window, the ATR length, the London hours, the daily
averages, the stop, and the target are one Score pack for this bar. An empty
answer, a tie, or an error does not emit and does not put a printed bound
back. The side is which side of the returned prior box the close broke.
The server hour is the clock. This module does not send.
"""
from __future__ import annotations

import threading
from typing import Any, Optional

from ..admission import TradeIntent
from ._server_clock import server_hour

ON_SURFACE = ("GBPJPY",)
_MODEL = "jev-1.13.0"
_UNSET = " An empty score leaves it unset. A tie leaves it unset. An error leaves it unset."
_LOCK = threading.Lock()
_CACHE: dict[tuple, dict[str, Any]] = {}
_SCORE_SPOTS = (
    "n_box",
    "pct_win",
    "squeeze_min_count",
    "sq_pctl",
    "atr_bars",
    "atr_lb",
    "min_vol_count",
    "vol_low_pctl",
    "stop_atr",
    "tgt_atr",
    "london_lo",
    "london_hi",
    "sma_fast",
    "sma_slow",
)
_TEXT = {
    "n_box": "The score you return is how many bars form the breakout box.",
    "pct_win": "The score you return is how many prior bars the squeeze rank uses.",
    "squeeze_min_count": "The score you return is how many box-width ratios the squeeze rank needs.",
    "sq_pctl": "The score you return is the rank at or under which this box is compressed.",
    "atr_bars": "The score you return is how many bars the ATR on this bar uses.",
    "atr_lb": "The score you return is how many prior bars the volatility rank looks back.",
    "min_vol_count": "The score you return is how many prior ATR values the volatility rank needs.",
    "vol_low_pctl": "The score you return is the rank under which this bar's ATR is the low-vol state.",
    "stop_atr": "The score you return is the stop as a multiple of ATR.",
    "tgt_atr": "The score you return is the target as a multiple of ATR.",
    "london_lo": "The score you return is the first server hour of the London window, inclusive.",
    "london_hi": "The score you return is the server hour at which the London window ends, exclusive.",
    "sma_fast": "The score you return is how many prior daily closes the fast average uses.",
    "sma_slow": "The score you return is how many prior daily closes the slow average uses.",
}


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _clock_hour(value: Any, *, end: bool = False) -> int | None:
    number = _finite(value)
    if number is None:
        return None
    whole = int(round(number))
    cap = 24 if end else 23
    if whole < 0 or whole > cap:
        return None
    return whole


def _whole(value: Any) -> int | None:
    number = _finite(value)
    if number is None:
        return None
    whole = int(round(number))
    if whole < 1:
        return None
    return whole


def _hour(t):
    """Server-local hour of the stamp. None when the clock cannot be read."""
    return server_hour(t)


def _daystr(t) -> str | None:
    if t is None:
        return None
    if hasattr(t, "year"):
        return f"{t.year:04d}-{t.month:02d}-{t.day:02d}"
    s = str(t)
    return s[:10] if len(s) >= 10 else None


def _atr(bars, i: int, n: int) -> float | None:
    if n < 1 or i < n or i < 1:
        return None
    total = 0.0
    for j in range(i - n + 1, i + 1):
        prev = bars[j - 1].c
        total += max(
            bars[j].h - bars[j].l,
            abs(bars[j].h - prev),
            abs(bars[j].l - prev),
        )
    return total / n


def _rolling_extreme_at(vals, win: int, is_max: bool, end_idx: int):
    if win < 1 or end_idx < win - 1:
        return None
    segment = vals[end_idx - win + 1 : end_idx + 1]
    return max(segment) if is_max else min(segment)


def _rank_strict_less(sorted_vals: list[float], value: float) -> float | None:
    if not sorted_vals:
        return None
    lo_idx, hi_idx = 0, len(sorted_vals)
    while lo_idx < hi_idx:
        mid = (lo_idx + hi_idx) // 2
        if sorted_vals[mid] < value:
            lo_idx = mid + 1
        else:
            hi_idx = mid
    return lo_idx / len(sorted_vals)


def _prior_closes(aux_bars, aux_times, decision_day: str) -> list[float]:
    if not aux_bars or not aux_times or len(aux_bars) != len(aux_times):
        return []
    closes = []
    for bar, t in zip(aux_bars, aux_times):
        day = _daystr(t)
        if day is not None and day < decision_day:
            closes.append(bar.c)
    return closes


def _d1_up(closes: list[float], fast: int, slow: int) -> bool | None:
    if fast < 1 or slow < fast or len(closes) < slow:
        return None
    window = closes[-slow:]
    base = window[-fast]
    if base == 0:
        return None
    sma_fast = sum(window[-fast:]) / fast
    sma_slow = sum(window) / slow
    last = window[-1]
    ret = (last - base) / base
    return (sma_fast > sma_slow) and (last > sma_fast) and (ret > 0.0)


def _questions(facts: dict | None = None, bars=None, i: int | None = None, bar_times=None) -> dict[str, Any]:
    from .spot_choice import amount_question, anchors_for

    packed: dict[str, Any] = {}
    _questions.anchors = {}
    for spot in _SCORE_SPOTS:
        anchors = anchors_for(spot, facts, bars=bars, index=i, bar_times=bar_times)
        _questions.anchors[spot] = anchors
        packed.update(amount_question(spot, _TEXT[spot], anchors))
    return packed


def _post(facts: dict, bars=None, i: int | None = None, bar_times=None) -> dict[str, Any]:
    out = {spot: None for spot in _SCORE_SPOTS}
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import append_outcome, prior_outcomes, returned_number
    except Exception:
        return out
    try:
        questions = _questions(facts, bars, i, bar_times)
    except Exception:
        return out
    state = dict(facts)
    try:
        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []
    try:
        receipt = evaluate(state, questions=questions, model=_MODEL, merge_sleeve=False)
    except Exception:
        return out
    if not isinstance(receipt, dict) or not receipt.get("ok"):
        return out
    raw = receipt.get("answers")
    answers = raw if isinstance(raw, dict) else {}
    for spot in _SCORE_SPOTS:
        from .spot_choice import value_at

        number = value_at(returned_number(answers.get(spot)), _questions.anchors.get(spot))
        out[spot] = number
        try:
            append_outcome(spot, number, state, error=None if number is not None else "empty")
        except Exception:
            pass
    return out


def _key(facts: dict) -> tuple:
    return (
        facts.get("symbol"),
        facts.get("decision_day"),
        facts.get("n_bars"),
        _finite(facts.get("close")),
        facts.get("hour"),
    )


def _ask(facts: dict, bars=None, i: int | None = None, bar_times=None) -> dict[str, Any]:
    key = _key(facts)
    with _LOCK:
        hit = _CACHE.get(key)
    if hit is not None:
        return dict(hit)
    pack = _post(facts, bars, i, bar_times)
    symbol = facts.get("symbol")
    with _LOCK:
        for old in list(_CACHE):
            if old[0] == symbol and old != key:
                _CACHE.pop(old, None)
        _CACHE[key] = pack
    return dict(pack)


def spot_pack(
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    **_,
):
    """Facts on the card. The bounds are not decided here."""
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    stamp = None
    if bar_time is not None:
        stamp = bar_time
    elif bar_times and bars and len(bar_times) == len(bars):
        stamp = bar_times[i]
    hour = _hour(stamp)
    close = high = low = None
    if bars and i >= 0:
        close = getattr(bars[i], "c", None)
        high = getattr(bars[i], "h", None)
        low = getattr(bars[i], "l", None)
    return {
        "sleeve": "vss_fxcross_london_up_low",
        "symbol": symbol,
        "decision_day": decision_day,
        "n_bars": n,
        "i": i,
        "hour": hour,
        "close": close,
        "high": high,
        "low": low,
        "on_named_surface": bool(symbol in ON_SURFACE and bars),
        "n_aux": len(aux_bars) if aux_bars is not None else 0,
    }


def generate(
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    **_,
) -> Optional[TradeIntent]:
    """Emit when the returned bounds all hold. Empty is not an intent."""
    card = spot_pack(
        symbol,
        bars,
        decision_day,
        bar_time=bar_time,
        bar_times=bar_times,
        aux_bars=aux_bars,
        aux_times=aux_times,
    )
    if not card["on_named_surface"] or card["hour"] is None:
        return None
    pack = _ask(card, bars, card.get("i"), bar_times)
    n_box = _whole(pack.get("n_box"))
    pct_win = _whole(pack.get("pct_win"))
    squeeze_min = _whole(pack.get("squeeze_min_count"))
    sq_pctl = _finite(pack.get("sq_pctl"))
    atr_bars = _whole(pack.get("atr_bars"))
    atr_lb = _whole(pack.get("atr_lb"))
    min_vol = _whole(pack.get("min_vol_count"))
    vol_low_pctl = _finite(pack.get("vol_low_pctl"))
    stop_atr = _finite(pack.get("stop_atr"))
    tgt_atr = _finite(pack.get("tgt_atr"))
    london_lo = _clock_hour(pack.get("london_lo"))
    london_hi = _clock_hour(pack.get("london_hi"), end=True)
    sma_fast = _whole(pack.get("sma_fast"))
    sma_slow = _whole(pack.get("sma_slow"))
    needed = (
        n_box, pct_win, squeeze_min, sq_pctl, atr_bars, atr_lb, min_vol,
        vol_low_pctl, stop_atr, tgt_atr, london_lo, london_hi, sma_fast, sma_slow,
    )
    if any(value is None for value in needed):
        return None
    if london_lo >= london_hi:
        return None
    hour = card["hour"]
    if hour < london_lo or hour >= london_hi:
        return None
    i = card["i"]
    if not bars or i < n_box + pct_win or i < atr_bars:
        return None
    atr_i = _atr(bars, i, atr_bars)
    if atr_i is None or atr_i <= 0 or stop_atr <= 0 or tgt_atr <= 0:
        return None
    closes = _prior_closes(aux_bars, aux_times, decision_day)
    if _d1_up(closes, sma_fast, sma_slow) is not True:
        return None
    highs = [bar.h for bar in bars]
    lows = [bar.l for bar in bars]
    box_hi = _rolling_extreme_at(highs, n_box, True, i)
    box_lo = _rolling_extreme_at(lows, n_box, False, i)
    prior_hi = _rolling_extreme_at(highs, n_box, True, i - 1)
    prior_lo = _rolling_extreme_at(lows, n_box, False, i - 1)
    if None in (box_hi, box_lo, prior_hi, prior_lo):
        return None
    hist = []
    for k in range(i - pct_win, i):
        atr_k = _atr(bars, k, atr_bars)
        hi_k = _rolling_extreme_at(highs, n_box, True, k)
        lo_k = _rolling_extreme_at(lows, n_box, False, k)
        if hi_k is None or lo_k is None or atr_k is None or atr_k <= 0:
            continue
        hist.append((hi_k - lo_k) / atr_k)
    if len(hist) < squeeze_min:
        return None
    ratio_i = (box_hi - box_lo) / atr_i
    rank = _rank_strict_less(sorted(hist), ratio_i)
    if rank is None or rank > sq_pctl:
        return None
    atr_window = []
    start = i - atr_lb
    if start < 0:
        start = 0
    for k in range(start, i):
        value = _atr(bars, k, atr_bars)
        if value is not None and value > 0:
            atr_window.append(value)
    if len(atr_window) < min_vol:
        return None
    vol_rank = _rank_strict_less(sorted(atr_window), atr_i)
    if vol_rank is None or vol_rank >= vol_low_pctl:
        return None
    close = bars[i].c
    if close > prior_hi:
        direction = 1
    elif close < prior_lo:
        direction = -1
    else:
        return None
    stop_dist = stop_atr * atr_i
    if stop_dist <= 0:
        return None
    return TradeIntent(
        sleeve="vss_fxcross_london_up_low",
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=stop_dist,
        target_dist=tgt_atr * atr_i,
    )
