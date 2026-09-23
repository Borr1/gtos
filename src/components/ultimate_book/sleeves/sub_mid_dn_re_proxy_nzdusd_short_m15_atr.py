"""NZDUSD M15 stretch fade. Never alias this sleeve to sub_mid_dn_revert.

The session, the stretch, the warmup, and the other gates are Choices on
this bar. The ATR window, the stop pad, and the size are Scores in that
same post. The side is its own Choice. An empty answer, a tie, or an
error does not emit and does not restore a printed constant. The hour
text is read off the stamp. This module does not send.

Never port AUDUSD. Cite, do not re-merge:
  /workspace/instrument-edge/packs/NZDUSD_SUB_MID_DN_RE_SHORT_DEEPEN_20260920.json
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Optional

from . import fx_spot


class _DraftTradeIntent:
    __slots__ = (
        "sleeve", "symbol", "direction", "decision_day",
        "stop_dist", "target_dist", "intra_size", "expiry_bars",
    )

    def __init__(
        self,
        sleeve: str,
        symbol: str,
        direction: int,
        decision_day: str,
        stop_dist: float,
        target_dist: float | None = None,
        intra_size: float | None = None,
        expiry_bars: int | None = None,
    ):
        self.sleeve = sleeve
        self.symbol = symbol
        self.direction = direction
        self.decision_day = decision_day
        self.stop_dist = stop_dist
        self.target_dist = target_dist
        self.intra_size = intra_size
        self.expiry_bars = expiry_bars

    def __repr__(self) -> str:
        return (
            f"TradeIntent(sleeve={self.sleeve!r}, symbol={self.symbol!r}, "
            f"direction={self.direction}, stop_dist={self.stop_dist:.6g})"
        )


def _resolve_trade_intent_cls():
    """Use live TradeIntent when package-imported; else draft stub."""
    try:
        from src.components.ultimate_book.admission import TradeIntent as TI  # type: ignore
        return TI
    except Exception:
        return _DraftTradeIntent


TradeIntent = _DraftTradeIntent

TAG = "sub_mid_dn_re_proxy_nzdusd_short_m15_atr"
ON_SURFACE: tuple[str, ...] = ("NZDUSD",)

PLACE = True
APPLY = True
LIVE_ARMED = True
NEVER_ALIAS_TO = "sub_mid_dn_revert"
LENS = "Module_ATR_affinity_ONLY"
CITE_SEPARATE_FROM = ("Dig_TRAIN", "Module_blotter", NEVER_ALIAS_TO)

_MODEL = "jev-1.13.0"
_UNSET = " An empty score leaves it unset. A tie leaves it unset. An error leaves it unset."
_LOCK = threading.Lock()
_CACHE: dict[tuple, dict[str, Any]] = {}
_SCORE_SPOTS = ("sma_bars", "atr_bars", "stretch_atr", "stop_pad", "intra_size")
_DIRECTION = "direction"
_BOOK_SIDE = {"long": 1, "short": -1}
_SCORE_TEXT = {
    "sma_bars": "The score you return is how many closes form the midpoint on this bar.",
    "atr_bars": "The score you return is how many bars the ATR on this stop uses.",
    "stretch_atr": "The score you return is how many ATR above the midpoint count as stretched.",
    "stop_pad": "The score you return is the ATR pad beyond the stretch high.",
    "intra_size": "The score you return is this sleeve's size on this bar.",
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

    del bar_time
    stamps: list[float] = []
    if bar_times is None:
        return None
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


def _hour(bar_time, bar_times, i: int) -> Optional[int]:
    """Hour field off the stamp. Two digits is the clock text, not a decision."""

    t = None
    if bar_time is not None:
        t = bar_time
    elif bar_times is not None and len(bar_times) > i:
        t = bar_times[i]
    if t is None:
        return None
    if hasattr(t, "hour"):
        return int(t.hour)
    s = str(t)
    if "T" in s:
        try:
            return int(s.split("T", 1)[1][0:2])
        except Exception:
            return None
    if " " in s and ":" in s:
        try:
            return int(s.split(" ", 1)[1][0:2])
        except Exception:
            return None
    return None


def _sma(bars, i: int, n: int) -> float | None:
    if n < 1 or i < n - 1:
        return None
    total = 0.0
    for j in range(i - n + 1, i + 1):
        close = _finite(getattr(bars[j], "c", None))
        if close is None:
            return None
        total += close
    return total / n


def _atr(bars, i: int, n: int) -> float | None:
    if i < n or i < 1:
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
    """Raw facts and the Choice questions. The numbers are not decided here."""

    del aux_bars, aux_times
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    hr = _hour(bar_time, bar_times, i) if i >= 0 else None
    close = high = low = None
    if bars and i >= 0:
        close = getattr(bars[i], "c", None)
        high = getattr(bars[i], "h", None)
        low = getattr(bars[i], "l", None)
    state = fx_spot.book_state(
        TAG,
        symbol,
        on_named_surface=symbol in ON_SURFACE,
        n_bars=n,
        marked_live_armed=bool(LIVE_ARMED),
        hour=hr,
        close=close,
        high=high,
        low=low,
        decision_day=decision_day,
        named_surface=list(ON_SURFACE),
    )
    ask = "Which side of this condition is this bar?"
    questions = {
        "surface": fx_spot.q(
            "on_named_surface",
            "This symbol is the named FX pair and bars are present.",
            "off_surface_or_no_bars",
            "This symbol is not the named pair, or there are no bars.",
            ask,
        ),
        "armed": fx_spot.q(
            "sleeve_armed",
            "This FX sleeve is armed on the Challenge book.",
            "sleeve_not_armed",
            "This FX sleeve is not armed.",
            ask,
        ),
        "warmup": fx_spot.q(
            "warmup_complete",
            "The bar count covers this sleeve's warmup.",
            "bars_short_of_warmup",
            "The bar count is short of this sleeve's warmup.",
            ask,
        ),
        "clock": fx_spot.q(
            "hour_known",
            "The decision bar has a readable hour.",
            "hour_missing",
            "The decision bar has no readable hour.",
            ask,
        ),
        "session": fx_spot.q(
            "inside_london_or_ny",
            "The hour is inside the London or New York window for this sleeve.",
            "outside_london_and_ny",
            "The hour is outside that window.",
            ask,
        ),
        "atr": fx_spot.q(
            "atr_positive",
            "ATR can scale the stop.",
            "atr_not_a_scale",
            "ATR is not a positive scale.",
            ask,
        ),
        "mid": fx_spot.q(
            "mid_finite",
            "The midpoint of this bar is a finite price.",
            "mid_not_a_number",
            "The midpoint is not a finite price.",
            ask,
        ),
        "stretch": fx_spot.q(
            "close_stretched_above_mid",
            "The close is stretched above the midpoint.",
            "stretch_absent",
            "The close is not stretched above the midpoint.",
            ask,
        ),
        "stop": fx_spot.q(
            "stop_is_the_plan",
            "The structure stop beyond the stretch high is a positive distance.",
            "stop_not_positive",
            "The structure stop distance is not positive.",
            ask,
        ),
    }
    return {"state": state, "questions": questions, "i": i, "close": close, "high": high}


def _cache_key(state: dict) -> tuple:
    return (
        state.get("sleeve"),
        state.get("symbol"),
        state.get("decision_day"),
        state.get("n_bars"),
        _finite(state.get("close")),
        _finite(state.get("high")),
        _finite(state.get("low")),
        state.get("hour"),
    )


def _continues(picks: dict, questions: dict) -> bool:
    for qid, spec in questions.items():
        if picks.get(qid) != spec["a"]:
            return False
    return bool(questions)


def _ask(state: dict, questions: dict, bars=None, index=None, bar_times=None) -> dict[str, Any]:
    """Choices and the three scores in one post. The same facts reuse the pack."""

    key = _cache_key(state)
    with _LOCK:
        hit = _CACHE.get(key)
    if hit is not None:
        return dict(hit)
    pack = _post(state, questions, bars, index, bar_times)
    symbol = state.get("symbol")
    with _LOCK:
        for old in list(_CACHE):
            if old[1] == symbol and old != key:
                _CACHE.pop(old, None)
        _CACHE[key] = pack
    return dict(pack)


def _post(state: dict, choice_questions: dict, bars=None, index=None, bar_times=None) -> dict[str, Any]:
    out: dict[str, Any] = {spot: None for spot in _SCORE_SPOTS}
    out["picks"] = {qid: None for qid in choice_questions}
    out["direction"] = None
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import (
            append_outcome,
            prior_outcomes,
            returned_number,
            spot_question,
            unique_highest,
        )
    except Exception:
        return out
    payload: dict[str, Any] = {}
    order: dict[str, tuple[str, str]] = {}
    for qid, spec in choice_questions.items():
        side_a = spec["a"]
        side_b = spec["b"]
        order[qid] = (side_a, side_b)
        payload[qid] = {
            "type": "choice",
            "instructions": spec["instructions"],
            "criteria": {side_a: spec["a_text"], side_b: spec["b_text"]},
        }
    from .spot_choice import amount_question, anchors_for

    _post.anchors = {}
    for spot in _SCORE_SPOTS:
        anchors = anchors_for(spot, state, bars=bars, index=index, bar_times=bar_times)
        _post.anchors[spot] = anchors
        payload.update(amount_question(spot, _SCORE_TEXT[spot], anchors))
    payload.update(
        spot_question(
            _DIRECTION,
            "Which side does this stretch take on this state? "
            "An empty answer, a tie, or an error is not a side.",
            {
                "short": "The stretch fades short.",
                "long": "The stretch goes long.",
            },
        )
    )
    card = dict(state)
    try:
        card["prior_outcomes"] = prior_outcomes(state=card, questions=payload)
    except Exception:
        card["prior_outcomes"] = []
    try:
        receipt = evaluate(card, questions=payload, model=_MODEL, merge_sleeve=False)
    except Exception:
        return out
    if not isinstance(receipt, dict) or not receipt.get("ok"):
        return out
    raw = receipt.get("answers")
    answers = raw if isinstance(raw, dict) else {}
    picks: dict[str, str | None] = {}
    for qid, names in order.items():
        block = answers.get(qid)
        probs = block.get("probabilities") if isinstance(block, dict) else None
        try:
            picks[qid] = unique_highest(probs, names)
        except Exception:
            picks[qid] = None
    out["picks"] = picks
    for spot in _SCORE_SPOTS:
        from .spot_choice import value_at

        number = value_at(returned_number(answers.get(spot)), _post.anchors.get(spot))
        out[spot] = number
        try:
            append_outcome(spot, number, card, error=None if number is not None else "empty")
        except Exception:
            pass
    direction_block = answers.get(_DIRECTION)
    direction_probs = direction_block.get("probabilities") if isinstance(direction_block, dict) else None
    try:
        out["direction"] = unique_highest(direction_probs, ("short", "long"))
    except Exception:
        out["direction"] = None
    return out


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
):
    """Emit when every gate's continue side is unique and the scores form a stop."""

    trade_intent = _resolve_trade_intent_cls()
    packed = spot_pack(
        symbol,
        bars,
        decision_day,
        bar_time=bar_time,
        bar_times=bar_times,
        aux_bars=aux_bars,
        aux_times=aux_times,
    )
    state = dict(packed["state"])
    remain = _seconds_until_next(bar_time, bar_times)
    if remain is not None:
        state["seconds_until_cycle"] = remain
    asked = _ask(state, packed["questions"], bars, packed.get("i"), bar_times)
    if not _continues(asked.get("picks") or {}, packed["questions"]):
        return None
    direction = _BOOK_SIDE.get(asked.get("direction"))
    sma_n = _whole(asked.get("sma_bars"))
    atr_n = _whole(asked.get("atr_bars"))
    stretch = _finite(asked.get("stretch_atr"))
    pad = _finite(asked.get("stop_pad"))
    intra = _finite(asked.get("intra_size"))
    i = packed["i"]
    close = _finite(packed.get("close"))
    high = _finite(packed.get("high"))
    if None in (direction, sma_n, atr_n, stretch, pad, intra, close, high) or not bars or i < 1:
        return None
    atr = _atr(bars, i, atr_n)
    mid = _sma(bars, i, sma_n)
    if atr is None or atr <= 0 or mid is None:
        return None
    if close <= mid + stretch * atr:
        return None
    stop_dist = (high + pad * atr) - close
    if stop_dist <= 0:
        return None
    try:
        return trade_intent(
            sleeve=TAG,
            symbol=symbol,
            direction=direction,
            decision_day=decision_day,
            stop_dist=float(stop_dist),
            target_dist=None,
            intra_size=intra,
        )
    except TypeError:
        return None


DRAFT_SLEEVESPEC = {
    "tag": TAG,
    "timeframe": "M15",
    "cluster": "fx_reversion_research",
    "on_surface": list(ON_SURFACE),
    "direction_fixed": None,
    "exit": {
        "model": "Module_ATR_research",
        "structure_stop": True,
        "stop_pad_atr": None,
        "time_stop_bars": None,
        "fixed_rr_target": None,
        "note": "stop pad and horizon are scores. This spec does not write them.",
    },
    "never_alias_to": NEVER_ALIAS_TO,
    "live_armed": True,
    "place": True,
    "apply": True,
    "lens": LENS,
    "cite_separate_from": list(CITE_SEPARATE_FROM),
}
