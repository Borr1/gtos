"""NY-killzone index continuation.

The bar's hour, minute, range, efficiency, and volatility rank are facts.
Each bound is a score on that card. An empty score, a tie, or an error
leaves the bound unset and does not restore a printed level. Surface
membership and a missing clock are Choices on the same post.
"""
from __future__ import annotations

from typing import Any, Optional

from ..admission import TradeIntent
from ..primitives import atr14
from ._server_clock import server_hour_minute
from .spot_choice import all_false, arm_card, bar_id, post_answers, read_number, read_side, score_questions

ON_SURFACE = ("SPX500", "GER40", "UK100", "NAS100", "JP225")
SLEEVE = "ny_index_momentum"
_SIDES = ("condition_true", "condition_false")


def _hm(t):
    """Server-local hour and minute. None when the stamp cannot be read."""
    return server_hour_minute(t)


def _whole(value: Any, *, least: int | None = None) -> int | None:
    number = value if isinstance(value, (int, float)) and not isinstance(value, bool) else None
    if number is None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
    if isinstance(number, bool) or number != number or number in (float("inf"), float("-inf")):
        return None
    whole = int(round(float(number)))
    if least is not None and whole < least:
        return None
    return whole


def _choice(spot: str, condition: str, measured: bool) -> dict[str, Any]:
    return {
        spot: {
            "type": "choice",
            "instructions": (
                f"Condition: {condition}. "
                f"Measured fact for this condition is {measured}. "
                "condition_true means the condition holds. "
                "condition_false means the condition does not hold. "
                "An empty answer, a tie, or an error is not a side."
            ),
            "criteria": {
                "condition_true": f"The condition holds. {condition}",
                "condition_false": f"The condition does not hold. {condition}",
            },
        }
    }


def _facts(symbol, bars, *, bar_time=None, bar_times=None) -> dict[str, Any]:
    i = len(bars) - 1 if bars else -1
    t = bar_time if bar_time is not None else (
        bar_times[i] if bar_times and bars and len(bar_times) == len(bars) else None
    )
    hm = _hm(t) if t is not None else None
    atr = None
    last = None
    if bars and i >= 0:
        try:
            raw = atr14(bars, i)
        except Exception:
            raw = None
        if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw > 0:
            atr = float(raw)
        bar = bars[i]
        last = (float(bar.o), float(bar.h), float(bar.l), float(bar.c))
    return {
        "sleeve": SLEEVE,
        "symbol": symbol,
        "namespace": "operator",
        "login": 0,
        "bar": bar_id("", len(bars) if bars else 0, bar_time, bar_times),
        "n_bars": len(bars) if bars else 0,
        "bar_index": i,
        "hour": None if hm is None else hm[0],
        "minute": None if hm is None else hm[1],
        "clock_known": hm is not None,
        "atr": atr,
        "open": None if last is None else last[0],
        "high": None if last is None else last[1],
        "low": None if last is None else last[2],
        "close": None if last is None else last[3],
        "named_surface": list(ON_SURFACE),
        "on_named_surface": symbol in ON_SURFACE,
        "off_surface": symbol not in ON_SURFACE,
        "no_bar_time": t is None or hm is None,
        "order_send": False,
        "flatten": False,
    }


def _questions(facts: dict[str, Any]) -> dict[str, Any]:
    packed = score_questions({
        "de_thresh": "The score you return is the absolute directional-efficiency level that opens this bar.",
        "stop_mult": "The score you return is the ATR multiple of the stop on this bar.",
        "window": "The score you return is how many closed bars the efficiency window uses.",
        "decision_hour": "The score you return is the server hour of the decision bar.",
        "decision_min": "The score you return is the minute of the decision bar.",
        "maxbars": "The score you return is how many bars this position may stay open.",
        "vol_win": "The score you return is how many trailing ATR values the percentile uses.",
        "vol_lo": "The score you return is the low edge of the mid volatility percentile band.",
        "vol_hi": "The score you return is the high edge of the mid volatility percentile band.",
        "min_bars": "The score you return is how many closed bars this scan needs.",
        "hist_min": "The score you return is how many positive ATR values the percentile needs.",
    })
    packed.update(_choice(
        "off_surface",
        f"{facts.get('symbol')} is not one of the named index symbols",
        bool(facts.get("off_surface")),
    ))
    packed.update(_choice(
        "no_bar_time",
        "the decision bar has no server clock",
        bool(facts.get("no_bar_time")),
    ))
    return packed


def _rank(bars, i: int, vol_win: int, hist_min: int) -> float | None:
    if i < vol_win:
        return None
    try:
        current = atr14(bars, i)
    except Exception:
        return None
    if not isinstance(current, (int, float)) or isinstance(current, bool) or current <= 0:
        return None
    hist = []
    for k in range(i - vol_win, i):
        try:
            value = atr14(bars, k)
        except Exception:
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
            hist.append(float(value))
    if len(hist) < hist_min:
        return None
    return sum(1 for value in hist if value <= float(current)) / len(hist)


def _window_move(bars, i: int, window: int) -> tuple[float, float] | None:
    if window < 1 or i < window:
        return None
    span = bars[i - window:i + 1]
    if not span:
        return None
    high = max(bar.h for bar in span)
    low = min(bar.l for bar in span)
    span_range = high - low
    net = bars[i].c - bars[i - window].c
    if not (span_range > 0):
        return None
    return float(net), abs(float(net) / float(span_range))


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """One post. The scores are the bounds. A missing bound does not emit."""
    del aux_bars, aux_times
    if not bars:
        return None
    facts = _facts(symbol, bars, bar_time=bar_time, bar_times=bar_times)
    facts["bar"] = bar_id(decision_day, len(bars), bar_time, bar_times)
    arm_card(facts, bars=bars, index=len(bars) - 1, bar_times=bar_times)
    answers = post_answers(facts, _questions(facts))
    sides = {
        "off_surface": read_side(answers, "off_surface", _SIDES),
        "no_bar_time": read_side(answers, "no_bar_time", _SIDES),
    }
    if not all_false(sides):
        return None
    i = len(bars) - 1
    min_bars = _whole(read_number(answers, "min_bars"), least=1)
    window = _whole(read_number(answers, "window"), least=1)
    vol_win = _whole(read_number(answers, "vol_win"), least=1)
    hist_min = _whole(read_number(answers, "hist_min"), least=1)
    decision_hour = _whole(read_number(answers, "decision_hour"))
    decision_min = _whole(read_number(answers, "decision_min"))
    de_thresh = read_number(answers, "de_thresh")
    stop_mult = read_number(answers, "stop_mult")
    vol_lo = read_number(answers, "vol_lo")
    vol_hi = read_number(answers, "vol_hi")
    if None in (min_bars, window, vol_win, hist_min, decision_hour, decision_min, de_thresh, stop_mult, vol_lo, vol_hi):
        return None
    if i < min_bars or facts.get("hour") is None:
        return None
    if facts["hour"] != decision_hour or facts["minute"] != decision_min:
        return None
    atr = facts.get("atr")
    if atr is None or not (stop_mult * atr > 0):
        return None
    move = _window_move(bars, i, window)
    if move is None:
        return None
    net, efficiency = move
    if efficiency < de_thresh:
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
    horizon = _whole(read_number(answers, "maxbars"), least=1)
    if horizon is None:
        return None
    return TradeIntent(
        sleeve=SLEEVE,
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=stop_mult * atr,
        target_dist=None,
        expiry_bars=horizon,
    )
