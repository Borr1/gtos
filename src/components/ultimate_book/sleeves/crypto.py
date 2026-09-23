"""crypto sleeve — Donchian breakout on the latest closed H4 bar.

The persistence gate, the channel lookback, the stop distance, and the target
are the Noul, Choice, or Score returned for this bar. Prior outcomes are part
of that ask. An empty answer, a tie, or an error leaves the field unset.
"""
from __future__ import annotations
from typing import Optional

from ..primitives import atr14, autocorr
from ..admission import TradeIntent

SLEEVE = "crypto"
ON_SURFACE = ("BTCUSD", "DASHUSD")
_MODEL = "jev-1.13.0"


def _finite(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number == float("inf") or number == float("-inf"):
        return None
    return number


def _returned_value(block):
    """The value is the Score, the Noul, or the Choice. A tie is unset."""
    if not isinstance(block, dict) or block.get("error"):
        return None
    score = _finite(block.get("score")) if "score" in block else None
    if score is not None:
        return score
    noul = block.get("noul")
    if "noul" in block and not isinstance(noul, bool):
        number = _finite(noul)
        if number is not None:
            return number
    probs = block.get("probabilities")
    if isinstance(probs, dict) and probs:
        from src.judgment.jev_questions import unique_highest

        name = unique_highest(probs)
        if name is None:
            return None
        return _finite(name)
    choice = block.get("choice")
    if choice in (None, ""):
        return None
    if str(choice).strip().lower() in {"tie", "tied"}:
        return None
    return _finite(choice)


def _questions(facts, bars, i):
    from .spot_choice import amount_question, anchors_for

    texts = {
        "ac_thr": (
            "What autocorrelation clears the persistence gate on this closed bar? "
            "The score you return is that gate. "
            "An empty answer leaves the gate unset."
        ),
        "don_lb": (
            "How many prior closed bars form the channel on this bar? "
            "The score you return is that lookback. "
            "An empty answer leaves the lookback unset."
        ),
        "sd_atr": (
            "What multiple of the measured average range is the stop distance on this bar? "
            "The score you return is that distance in range units. "
            "An empty answer leaves the distance unset."
        ),
        "target_r": (
            "What multiple of the stop distance is the target on this bar? "
            "The score you return is that target. "
            "An empty answer leaves the target unset."
        ),
        "persist_bars": (
            "How many closed bars does the persistence window use on this bar? "
            "The score you return is that window. "
            "An empty answer leaves the window unset."
        ),
    }
    packed = {}
    built = {}
    for spot, text in texts.items():
        anchors = anchors_for(spot, facts, bars=bars, index=i)
        built[spot] = anchors
        packed.update(amount_question(spot, text, anchors))
    return packed, built


def _ask(state, questions, anchors):
    from src.judgment.jev_client import evaluate
    from src.judgment.jev_questions import prior_outcomes

    try:
        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []
    try:
        receipt = evaluate(
            state,
            model=_MODEL,
            questions=questions,
            merge_sleeve=False,
            require_equity=False,
        )
    except Exception:
        receipt = {"ok": False, "answers": {}}
    answers = {}
    if isinstance(receipt, dict) and receipt.get("ok"):
        raw = receipt.get("answers")
        if isinstance(raw, dict):
            answers = raw
    from .spot_choice import value_at

    values = {
        spot: value_at(_returned_value(answers.get(spot)), anchors.get(spot))
        for spot in questions
    }
    try:
        from src.judgment.jev_questions import append_outcome

        err = None if receipt.get("ok") else (receipt.get("error") or receipt.get("skipped") or "unset")
        for spot, value in values.items():
            append_outcome(spot, value, state, error=None if value is not None else err)
    except Exception:
        pass
    return values


def _whole(value):
    number = _finite(value)
    if number is None:
        return None
    whole = int(round(number))
    if whole != number or whole < 1:
        return None
    return whole


def _decide(B, i, symbol=None):
    """Gate, lookback, distance, and target for closed bar i. Missing tape is None."""
    if B is None or i < 0:
        return None
    try:
        a = atr14(B, i)
    except Exception:
        return None
    if a is None or a <= 0:
        return None
    try:
        bar = B[i]
        state = {
            "sleeve": SLEEVE,
            "symbol": symbol,
            "open": bar.o,
            "high": bar.h,
            "low": bar.l,
            "close": bar.c,
            "volume": getattr(bar, "v", None),
            "atr": a,
            "bar_index": i,
            "n_bars": len(B),
            "order_send": False,
        }
    except Exception:
        return None
    questions, anchors = _questions(state, B, i)
    values = _ask(state, questions, anchors)
    window = _whole(values.get("persist_bars"))
    if window is None or i < window:
        return None
    try:
        ac = autocorr(B, i, window)
    except Exception:
        ac = None
    state["autocorr"] = ac
    lookback = _finite(values.get("don_lb"))
    if lookback is None or lookback <= 0:
        return None
    bars_back = int(round(lookback))
    if bars_back <= 0 or bars_back > i:
        return None
    try:
        hh = max(B[k].h for k in range(i - bars_back, i))
        ll = min(B[k].l for k in range(i - bars_back, i))
    except Exception:
        return None
    d = 0
    if B[i].c > hh:
        d = 1
    elif B[i].c < ll:
        d = -1
    if d == 0:
        return None
    gate = _finite(values.get("ac_thr"))
    if gate is None or ac is None or ac < gate:
        return None
    distance = _finite(values.get("sd_atr"))
    if distance is None or distance <= 0:
        return None
    sd = distance * a
    if sd <= 0:
        return None
    target_r = _finite(values.get("target_r"))
    if target_r is None or target_r <= 0:
        return None
    target = target_r * sd
    if target <= 0:
        return None
    return d, sd, target


def crypto_signal(B, i) -> Optional[tuple[int, float]]:
    """Return (direction, stop_dist) when the returned gate, lookback, and distance fire."""
    row = _decide(B, i)
    if row is None:
        return None
    d, sd, _target = row
    return d, sd


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, **_) -> Optional[TradeIntent]:
    """Live: one ask on the latest closed bar. Cost and spread are not a skip."""
    del bar_time
    if symbol not in ON_SURFACE or not bars:
        return None
    i = len(bars) - 1
    row = _decide(bars, i, symbol=symbol)
    if row is None:
        return None
    d, sd, target = row
    return TradeIntent(
        sleeve=SLEEVE,
        symbol=symbol,
        direction=d,
        decision_day=decision_day,
        stop_dist=sd,
        target_dist=target,
    )
