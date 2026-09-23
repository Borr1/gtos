"""London opening-range continuation on crypto.

The opening-range hour, the break window, the regime lookback, and the
volatility rank are scores for this bar. An empty score does not restore a
printed level. Break, regime, and earlier-bar Choices stay on their posts.
The widened multiple is the same pack, read by the widen container.
"""
from __future__ import annotations

from typing import Any, Optional

from ..admission import TradeIntent
from ..primitives import atr14
from ._server_clock import server_day, server_hour
from .spot_choice import arm_card, post_answers, read_number, read_side, score_questions

ON_SURFACE = ("BTCUSD", "ETHUSD")
_SURFACE = ("on_surface", "off_surface")
_PACKS: dict[tuple, dict[str, Any]] = {}


def _hour(t):
    """Server-local hour. None when the stamp cannot be read."""
    return server_hour(t)


def _day(t):
    """Server-local date key. None when the stamp cannot be read."""
    return server_day(t)


def _whole(value: Any, *, least: int | None = None) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    whole = int(round(number))
    if least is not None and whole < least:
        return None
    return whole


def _key(symbol, bars, decision_day, bar_time, bar_times) -> tuple:
    stamp = bar_time
    if stamp is None and bar_times:
        try:
            stamp = bar_times[-1]
        except Exception:
            stamp = None
    return (str(symbol), str(decision_day), len(bars) if bars else 0, str(stamp))


def _questions() -> dict[str, Any]:
    packed = score_questions({
        "or_hour": "The score you return is the server hour of the opening-range block.",
        "or_bars": "The score you return is how many bars form the opening range.",
        "break_hour_lo": "The score you return is the first server hour of the break window.",
        "break_hour_hi": "The score you return is the last server hour of the break window.",
        "target_r": "The score you return is the reward multiple of the stop.",
        "maxbars": "The score you return is how many bars this position may stay open.",
        "reg_lb": "The score you return is the regime lookback in bars.",
        "reg_th": "The score you return is the absolute slope-over-ATR level that marks a trend.",
        "vol_win": "The score you return is how many bars the volatility percentile uses.",
        "vol_lo": "The score you return is the percentile rank at or below which volatility is low.",
        "hist_min": "The score you return is how many ATR-over-price values the percentile needs.",
        "min_bars": "The score you return is how many closed bars this scan needs.",
        "widen_k": "The score you return is the multiple on the stop and the target for the widened container.",
    })
    packed["on_surface"] = {
        "type": "choice",
        "instructions": (
            "Is this symbol on the named crypto surface for this bar? "
            "The named symbols are a fact. "
            "An empty answer, a tie, or an error is not a side."
        ),
        "criteria": {
            "on_surface": "The symbol is on the named surface for this bar.",
            "off_surface": "The symbol is off the named surface for this bar.",
        },
    }
    return packed


def _facts(symbol, bars, decision_day, bar_time, bar_times) -> dict[str, Any]:
    i = len(bars) - 1 if bars else -1
    hour = _hour(bar_times[i]) if bar_times and bars and len(bar_times) == len(bars) else None
    atr = None
    close = None
    if bars and i >= 0:
        try:
            raw = atr14(bars, i)
        except Exception:
            raw = None
        if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw > 0:
            atr = float(raw)
        close = float(bars[i].c)
    return {
        "sleeve": "orb_crypto_london",
        "symbol": symbol,
        "namespace": "operator",
        "login": 0,
        "decision_day": decision_day,
        "bar": _key(symbol, bars, decision_day, bar_time, bar_times)[-1],
        "n_bars": len(bars) if bars else 0,
        "bar_index": i,
        "hour": hour,
        "atr": atr,
        "close": close,
        "named_surface": list(ON_SURFACE),
        "on_named_surface": symbol in ON_SURFACE,
        "order_send": False,
        "flatten": False,
    }


def pack_for(symbol, bars, decision_day, bar_time, bar_times) -> dict[str, Any]:
    """The one pack for this bar. A second read does not ask again."""

    key = _key(symbol, bars, decision_day, bar_time, bar_times)
    hit = _PACKS.get(key)
    if hit is not None:
        return hit
    facts = _facts(symbol, bars, decision_day, bar_time, bar_times)
    arm_card(facts, bars=bars, index=len(bars) - 1 if bars else None, bar_times=bar_times)
    answers = post_answers(facts, _questions())
    if answers:
        _PACKS[key] = answers
    return answers


def cached_number(symbol, bars, decision_day, bar_time, bar_times, spot: str) -> float | None:
    """A score already on this bar's pack. A miss stays unset."""

    pack = _PACKS.get(_key(symbol, bars, decision_day, bar_time, bar_times))
    if not isinstance(pack, dict):
        return None
    return read_number(pack, spot)


def _regime(bars, i, atr, look: int | None, thresh: float | None) -> str | None:
    if look is None or thresh is None or look < 1 or i < look or atr <= 0:
        return None
    slope = (bars[i].c - bars[i - look].c) / atr
    if slope > thresh:
        return "up"
    if slope < -thresh:
        return "dn"
    return "range"


def _low_vol(bars, i, atr, vol_win: int | None, hist_min: int | None, vol_lo: float | None) -> bool | None:
    if vol_win is None or hist_min is None or vol_lo is None or vol_win < 1 or hist_min < 1:
        return None
    if i < vol_win or atr <= 0 or bars[i].c <= 0:
        return None
    current = atr / bars[i].c
    vals = []
    for k in range(i - vol_win, i + 1):
        try:
            sample = atr14(bars, k)
        except Exception:
            continue
        if isinstance(sample, (int, float)) and not isinstance(sample, bool) and sample > 0 and bars[k].c > 0:
            vals.append(sample / bars[k].c)
    if len(vals) < hist_min:
        return None
    rank = sum(1 for value in vals if value <= current) / len(vals)
    return rank <= vol_lo


def _bounds(answers: dict[str, Any]) -> dict[str, Any] | None:
    pulled = {
        "or_hour": _whole(read_number(answers, "or_hour")),
        "or_bars": _whole(read_number(answers, "or_bars"), least=1),
        "break_hour_lo": _whole(read_number(answers, "break_hour_lo")),
        "break_hour_hi": _whole(read_number(answers, "break_hour_hi")),
        "reg_lb": _whole(read_number(answers, "reg_lb"), least=1),
        "reg_th": read_number(answers, "reg_th"),
        "vol_win": _whole(read_number(answers, "vol_win"), least=1),
        "vol_lo": read_number(answers, "vol_lo"),
        "hist_min": _whole(read_number(answers, "hist_min"), least=1),
        "min_bars": _whole(read_number(answers, "min_bars"), least=1),
        "target_r": read_number(answers, "target_r"),
    }
    if any(value is None for value in pulled.values()):
        return None
    if pulled["target_r"] <= 0:
        return None
    if pulled["break_hour_hi"] < pulled["break_hour_lo"]:
        return None
    return pulled


def _gate(spot: str, condition: str, measured: bool, true_name: str, false_name: str,
         true_text: str, false_text: str) -> dict[str, Any]:
    return {
        spot: {
            "type": "choice",
            "instructions": (
                f"Condition: {condition}. Measured fact for this condition is {measured}. "
                "An empty answer, a tie, or an error is not a side."
            ),
            "criteria": {true_name: true_text, false_name: false_text},
        }
    }


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """London opening-range continuation. Bounds come from one pack."""
    del aux_bars, aux_times
    if not bars or not bar_times or len(bar_times) != len(bars):
        return None
    answers = pack_for(symbol, bars, decision_day, bar_time, bar_times)
    if read_side(answers, "on_surface", _SURFACE) != "on_surface":
        return None
    bounds = _bounds(answers)
    if bounds is None:
        return None
    i = len(bars) - 1
    if i < bounds["min_bars"]:
        return None
    hour = _hour(bar_times[i])
    if hour is None or hour < bounds["break_hour_lo"] or hour > bounds["break_hour_hi"]:
        return None
    atr = atr14(bars, i)
    if not isinstance(atr, (int, float)) or isinstance(atr, bool) or atr <= 0:
        return None
    regime = _regime(bars, i, atr, bounds["reg_lb"], bounds["reg_th"])
    low = _low_vol(bars, i, atr, bounds["vol_win"], bounds["hist_min"], bounds["vol_lo"])
    if regime is None or low is None:
        return None
    day = _day(bar_times[i])
    or_idx = [
        k for k in range(i, -1, -1)
        if _day(bar_times[k]) == day and _hour(bar_times[k]) == bounds["or_hour"]
    ]
    or_idx = sorted(or_idx)[: bounds["or_bars"]]
    if len(or_idx) < bounds["or_bars"]:
        return None
    or_hi = max(bars[k].h for k in or_idx)
    or_lo = min(bars[k].l for k in or_idx)
    if or_hi <= or_lo:
        return None
    last_or = or_idx[-1]
    close = bars[i].c
    earlier = False
    for k in range(last_or + 1, i):
        if _day(bar_times[k]) != day:
            continue
        hour_k = _hour(bar_times[k])
        if hour_k is None or hour_k < bounds["break_hour_lo"] or hour_k > bounds["break_hour_hi"]:
            continue
        if bars[k].c > or_hi or bars[k].c < or_lo:
            earlier = True
            break
    gate_facts = {
        "sleeve": "orb_crypto_london",
        "symbol": symbol,
        "namespace": "operator",
        "login": 0,
        "decision_day": decision_day,
        "regime": regime,
        "vol_low": low,
        "close": float(close),
        "or_high": float(or_hi),
        "or_low": float(or_lo),
        "above": bool(close > or_hi),
        "under": bool(close < or_lo),
        "earlier_break": earlier,
        "order_send": False,
        "flatten": False,
    }
    gates = {}
    gates.update(_gate(
        "blocked",
        "vol is not low or the regime is range",
        (not low) or regime == "range",
        "context_closed",
        "context_open",
        "Vol is not low or the higher-timeframe regime is range. Do not emit.",
        "Vol is low and the regime is not range.",
    ))
    gates.update(_gate(
        "above",
        "close is above the opening-range high",
        close > or_hi,
        "close_above_or_high",
        "not_above_or_high",
        "The close is above the opening-range high.",
        "The close is not above the opening-range high.",
    ))
    gates.update(_gate(
        "under",
        "close is below the opening-range low",
        close < or_lo,
        "close_below_or_low",
        "not_below_or_low",
        "The close is below the opening-range low.",
        "The close is not below the opening-range low.",
    ))
    gates.update(_gate(
        "earlier",
        "an earlier break-window close is beyond an opening-range edge",
        earlier,
        "earlier_break",
        "no_earlier_break",
        "An earlier break-window bar already closed beyond the opening range. Do not emit.",
        "No earlier break-window bar closed beyond the opening range.",
    ))
    decided = post_answers(gate_facts, gates)
    blocked = read_side(decided, "blocked", ("context_closed", "context_open"))
    above = read_side(decided, "above", ("close_above_or_high", "not_above_or_high"))
    under = read_side(decided, "under", ("close_below_or_low", "not_below_or_low"))
    earlier_side = read_side(decided, "earlier", ("earlier_break", "no_earlier_break"))
    if blocked != "context_open" or earlier_side != "no_earlier_break":
        return None
    if above == "close_above_or_high":
        direction = 1
    elif under == "close_below_or_low":
        direction = -1
    else:
        return None
    stop_dist = (close - or_lo) if direction > 0 else (or_hi - close)
    if stop_dist <= 0:
        return None
    horizon = _whole(read_number(answers, "maxbars"), least=1)
    if horizon is None:
        return None
    return TradeIntent(
        sleeve="orb_crypto_london",
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=stop_dist,
        target_dist=bounds["target_r"] * stop_dist,
        expiry_bars=horizon,
    )
