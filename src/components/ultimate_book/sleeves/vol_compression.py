"""Volatility compression then a range break. D1 crypto.

The quantile, the channel, the history, the stop, and the target are one
Score pack for this bar. An empty answer, a tie, or an error leaves the
intent unset. The side is which side of the returned channel the close
broke. This module does not send.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Optional

from ..primitives import atr14
from ..admission import TradeIntent

# Named surface the registry passes. Membership is the choice, not this tuple.
ON_SURFACE = ("BTCUSD", "ETHUSD", "XTZUSD")

_MODEL = "jev-1.13.0"
_UNSET = " An empty score leaves it unset. A tie leaves it unset. An error leaves it unset."
_LOCK = threading.Lock()
_CACHE: dict[tuple, dict[str, Any]] = {}
_SCORE_SPOTS = (
    "squeeze_q",
    "break_lb",
    "stop_mult",
    "target_r",
    "hist_lb",
    "min_hist",
)
_SURFACE = "on_surface"
_BOOK_SIDE = {"long": 1, "short": -1}
_TEXT = {
    "squeeze_q": "The score you return is the ATR-history quantile below which this bar is compressed.",
    "break_lb": "The score you return is how many prior bars form the break channel.",
    "stop_mult": "The score you return is the stop as a multiple of ATR.",
    "target_r": "The score you return is the target as a multiple of the stop.",
    "hist_lb": "The score you return is how many prior ATR values the compression history uses.",
    "min_hist": "The score you return is how many positive ATR values the history needs.",
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


def _whole(value: Any) -> int | None:
    number = _finite(value)
    if number is None:
        return None
    whole = int(round(number))
    if whole < 1:
        return None
    return whole


def _epoch(value: Any) -> float | None:
    if isinstance(value, datetime):
        stamp = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return stamp.timestamp()
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    return None


def _seconds_until_next(bar_time, bar_times) -> float | None:
    """Observed spacing until the next print. No spacing means no deadline."""

    stamps: list[float] = []
    if bar_times is not None:
        for item in list(bar_times)[-2:]:
            epoch = _epoch(item)
            if epoch is not None:
                stamps.append(epoch)
    if len(stamps) < 2:
        return None
    span = stamps[-1] - stamps[-2]
    if span <= 0:
        return None
    remain = stamps[-1] + span - datetime.now(timezone.utc).timestamp()
    if remain <= 0:
        return None
    return remain


def _empty() -> dict[str, Any]:
    out: dict[str, Any] = {spot: None for spot in _SCORE_SPOTS}
    out[_SURFACE] = None
    return out


def _key(facts: dict) -> tuple:
    return (
        facts.get("sleeve"),
        facts.get("symbol"),
        facts.get("decision_day"),
        facts.get("n_bars"),
        _finite(facts.get("close")),
        _finite(facts.get("high")),
        _finite(facts.get("low")),
    )


def _questions(facts: dict | None = None, bars=None, i: int | None = None, bar_times=None) -> dict[str, Any]:
    from src.judgment.jev_questions import spot_question
    from .spot_choice import amount_question, anchors_for

    packed: dict[str, Any] = {}
    _questions.anchors = {}
    for spot in _SCORE_SPOTS:
        anchors = anchors_for(spot, facts, bars=bars, index=i, bar_times=bar_times)
        _questions.anchors[spot] = anchors
        packed.update(amount_question(spot, _TEXT[spot], anchors))
    packed.update(
        spot_question(
            _SURFACE,
            "Is this symbol on the named compression surface for this state? "
            "An empty answer, a tie, or an error is not a side.",
            {
                "on_surface": "The symbol is on the named compression surface.",
                "off_surface": "The symbol is not on the named compression surface.",
            },
        )
    )
    return packed


def _surface(block: Any) -> str | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, dict) or not probs:
        return None
    try:
        from src.judgment.jev_questions import unique_highest

        picked = unique_highest(probs, ("on_surface", "off_surface"))
    except Exception:
        return None
    if picked in {"on_surface", "off_surface"}:
        return str(picked)
    return None


def _post(facts: dict, bars=None, i: int | None = None, bar_times=None) -> dict[str, Any]:
    out = _empty()
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import append_outcome, prior_outcomes
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
        from .spot_choice import answered_amount

        number = answered_amount(spot, answers.get(spot), _questions.anchors.get(spot))
        out[spot] = number
        try:
            append_outcome(spot, number, state, error=None if number is not None else "empty")
        except Exception:
            pass
    out[_SURFACE] = _surface(answers.get(_SURFACE))
    return out


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
            if old[1] == symbol and old != key:
                _CACHE.pop(old, None)
        _CACHE[key] = pack
    return dict(pack)


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Compression break on the latest closed bar. One pack. Empty is not an intent."""

    del aux_bars, aux_times
    if not bars:
        return None
    n = len(bars)
    i = n - 1 if n else -1
    facts: dict[str, Any] = {
        "sleeve": "vol_compression",
        "symbol": symbol,
        "decision_day": decision_day,
        "n_bars": n,
        "named_surface": list(ON_SURFACE),
    }
    if bars and i >= 0:
        facts["close"] = getattr(bars[i], "c", None)
        facts["high"] = getattr(bars[i], "h", None)
        facts["low"] = getattr(bars[i], "l", None)
    remain = _seconds_until_next(bar_time, bar_times)
    if remain is not None:
        facts["seconds_until_cycle"] = remain
    pack = _ask(facts, bars, i, bar_times)
    if pack.get(_SURFACE) != "on_surface":
        return None
    squeeze_q = _finite(pack.get("squeeze_q"))
    break_lb = _whole(pack.get("break_lb"))
    stop_mult = _finite(pack.get("stop_mult"))
    target_r = _finite(pack.get("target_r"))
    hist_lb = _whole(pack.get("hist_lb"))
    min_hist = _whole(pack.get("min_hist"))
    if None in (squeeze_q, break_lb, stop_mult, target_r, hist_lb, min_hist):
        return None
    if not bars or i < max(hist_lb, break_lb):
        return None
    atrs = [atr14(bars, k) for k in range(len(bars))]
    atr = atrs[i]
    if atr is None or atr <= 0:
        return None
    hist = [atrs[k] for k in range(i - hist_lb, i) if atrs[k] > 0]
    if len(hist) < min_hist:
        return None
    slot = int(squeeze_q * len(hist))
    if slot < 0 or slot >= len(hist):
        return None
    thr = sorted(hist)[slot]
    if atr > thr:
        return None
    hh = max(bars[k].h for k in range(i - break_lb, i))
    ll = min(bars[k].l for k in range(i - break_lb, i))
    close = bars[i].c
    if close > hh:
        direction = _BOOK_SIDE["long"]
    elif close < ll:
        direction = _BOOK_SIDE["short"]
    else:
        return None
    stop_dist = stop_mult * atr
    if stop_dist <= 0:
        return None
    return TradeIntent(
        sleeve="vol_compression",
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=stop_dist,
        target_dist=target_r * stop_dist,
    )
