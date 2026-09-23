"""EURUSD M15 stretch fade.

Window lengths, the stretch multiple, the stop pad, the session hours, the
direction, and the size are one pack of scores. The Choice spots stay on
that same post. An empty score does not restore a printed level. The hour
text is read from the stamp. This module does not send.
"""
from __future__ import annotations

from typing import Any, Optional

from . import fx_spot
from .spot_choice import arm_card, post_answers, read_number, read_side, score_questions


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

TAG = "sub_mid_dn_re_proxy_eurusd_short_m15_atr"
ON_SURFACE: tuple[str, ...] = ("EURUSD",)

PLACE = True
APPLY = True
LIVE_ARMED = True
NEVER_ALIAS_TO = "sub_mid_dn_revert"
LENS = "Module_ATR_affinity_ONLY"
CITE_SEPARATE_FROM = ("Dig_TRAIN", "Module_blotter", NEVER_ALIAS_TO)

_ASK = "Which side of this condition is this bar?"


def _hour(bar_time, bar_times, i: int) -> Optional[int]:
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


def _whole(value: Any, *, least: int | None = None) -> int | None:
    number = _finite(value)
    if number is None:
        return None
    whole = int(round(number))
    if least is not None and whole < least:
        return None
    return whole


def _atr(bars, i: int, period: int) -> float | None:
    if period < 1 or i < period:
        return None
    total = 0.0
    for j in range(i - period + 1, i + 1):
        prev = bars[j - 1].c if j > 0 else bars[j].c
        total += max(
            bars[j].h - bars[j].l,
            abs(bars[j].h - prev),
            abs(bars[j].l - prev),
        )
    scale = total / period
    if scale <= 0:
        return None
    return scale


def _sma(bars, i: int, period: int) -> float | None:
    if period < 1 or i + 1 < period:
        return None
    return sum(bars[j].c for j in range(i - period + 1, i + 1)) / period


def _direction(value: Any) -> int | None:
    whole = _whole(value)
    if whole is None or whole == 0:
        return None
    if whole > 0:
        return 1
    return -1


def _inside(hour: int | None, start: int | None, end: int | None) -> bool | None:
    if hour is None or start is None or end is None:
        return None
    if end < start:
        return None
    return start <= hour < end


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
    """Facts and the one question pack. Scores and Choices travel together."""
    del aux_bars, aux_times
    arm_card(bars=bars, index=(len(bars) - 1) if bars else None, bar_times=bar_times)
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    hour = _hour(bar_time, bar_times, i) if i >= 0 else None
    close = float(bars[i].c) if i >= 0 else None
    high = float(bars[i].h) if i >= 0 else None
    low = float(bars[i].l) if i >= 0 else None
    on_surface = bool(symbol in ON_SURFACE and bars)
    state = {
        "sleeve": TAG,
        "symbol": symbol,
        "namespace": "operator",
        "login": 0,
        "decision_day": decision_day,
        "n_bars": n,
        "bar_index": i,
        "hour": hour,
        "hour_known": hour is not None,
        "close": close,
        "high": high,
        "low": low,
        "named_surface": list(ON_SURFACE),
        "on_named_surface": on_surface,
        "armed": bool(LIVE_ARMED),
        "order_send": False,
        "flatten": False,
    }
    specs = {
        "surface": fx_spot.q(
            "on_named_surface",
            "This symbol is the named FX pair and bars are present.",
            "off_surface_or_no_bars",
            "This symbol is not the named pair, or there are no bars.",
            _ASK,
        ),
        "armed": fx_spot.q(
            "sleeve_armed",
            "This FX sleeve is armed on the Challenge book.",
            "sleeve_not_armed",
            "This FX sleeve is not armed.",
            _ASK,
        ),
        "warmup": fx_spot.q(
            "warmup_complete",
            "The bar count covers the warmup this pack returns.",
            "bars_short_of_warmup",
            "The bar count is short of the warmup this pack returns.",
            _ASK,
        ),
        "clock": fx_spot.q(
            "hour_known",
            "The decision bar has a readable hour.",
            "hour_missing",
            "The decision bar has no readable hour.",
            _ASK,
        ),
        "session": fx_spot.q(
            "inside_london_or_ny",
            "The hour is inside the session window this pack returns.",
            "outside_london_and_ny",
            "The hour is outside the session window this pack returns.",
            _ASK,
        ),
        "atr": fx_spot.q(
            "atr_positive",
            "ATR over the returned period can scale the stop.",
            "atr_not_a_scale",
            "ATR is not a positive scale.",
            _ASK,
        ),
        "mid": fx_spot.q(
            "mid_finite",
            "The midpoint over the returned window is a finite price.",
            "mid_not_a_number",
            "The midpoint is not a finite price.",
            _ASK,
        ),
        "stretch": fx_spot.q(
            "close_stretched_above_mid",
            "The close is stretched above the midpoint by the returned ATR multiple.",
            "stretch_absent",
            "The close is not stretched that far above the midpoint.",
            _ASK,
        ),
        "stop": fx_spot.q(
            "stop_is_the_plan",
            "The structure stop beyond the stretch high is a positive distance.",
            "stop_not_positive",
            "The structure stop distance is not positive.",
            _ASK,
        ),
    }
    questions: dict[str, Any] = {}
    for qid, spec in specs.items():
        questions[qid] = {
            "type": "choice",
            "instructions": spec["instructions"],
            "criteria": {spec["a"]: spec["a_text"], spec["b"]: spec["b_text"]},
        }
    questions.update(score_questions({
        "sma_n": "The score you return is how many closes the midpoint uses.",
        "atr_n": "The score you return is how many bars the ATR uses.",
        "stretch_atr": "The score you return is the ATR multiple the close must clear above the midpoint.",
        "stop_pad_atr": "The score you return is the ATR pad beyond the stretch high.",
        "horizon_bars": "The score you return is how many bars this position may stay open.",
        "direction": "The score you return is the direction, positive for long and negative for short.",
        "london_start": "The score you return is the first server hour of the London window.",
        "london_end": "The score you return is the server hour where the London window ends.",
        "ny_start": "The score you return is the first server hour of the New York window.",
        "ny_end": "The score you return is the server hour where the New York window ends.",
        "warmup_bars": "The score you return is how many closed bars this scan needs.",
        "intra_size": "The score you return is the size for this bar.",
    }))
    return {"state": state, "questions": questions, "specs": specs}


def _geometry(bars, i: int, hour: int | None, answers: dict[str, Any]) -> dict[str, Any] | None:
    sma_n = _whole(read_number(answers, "sma_n"), least=1)
    atr_n = _whole(read_number(answers, "atr_n"), least=1)
    stretch = read_number(answers, "stretch_atr")
    pad = read_number(answers, "stop_pad_atr")
    warmup = _whole(read_number(answers, "warmup_bars"), least=1)
    london_start = _whole(read_number(answers, "london_start"))
    london_end = _whole(read_number(answers, "london_end"))
    ny_start = _whole(read_number(answers, "ny_start"))
    ny_end = _whole(read_number(answers, "ny_end"))
    direction = _direction(read_number(answers, "direction"))
    size = read_number(answers, "intra_size")
    if None in (
        sma_n, atr_n, stretch, pad, warmup,
        london_start, london_end, ny_start, ny_end, direction, size,
    ):
        return None
    if size <= 0 or i < warmup:
        return None
    london = _inside(hour, london_start, london_end)
    new_york = _inside(hour, ny_start, ny_end)
    if london is None or new_york is None or not (london or new_york):
        return None
    atr = _atr(bars, i, atr_n)
    mid = _sma(bars, i, sma_n)
    if atr is None or mid is None:
        return None
    if not (bars[i].c > mid + stretch * atr):
        return None
    stop_dist = (float(bars[i].h) + pad * atr) - float(bars[i].c)
    if not (stop_dist > 0):
        return None
    horizon = _whole(read_number(answers, "horizon_bars"), least=1)
    return {
        "direction": direction,
        "stop_dist": float(stop_dist),
        "intra_size": size,
        "expiry_bars": horizon,
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
):
    """Emit when every Choice continues and every bound score is set."""
    trade_intent = _resolve_trade_intent_cls()
    if not bars:
        return None
    packed = spot_pack(
        symbol,
        bars,
        decision_day,
        bar_time=bar_time,
        bar_times=bar_times,
        aux_bars=aux_bars,
        aux_times=aux_times,
    )
    answers = post_answers(packed["state"], packed["questions"])
    picks = {
        qid: read_side(answers, qid, (spec["a"], spec["b"]))
        for qid, spec in packed["specs"].items()
    }
    if not fx_spot.continues(picks, packed["specs"]):
        return None
    i = len(bars) - 1
    geometry = _geometry(bars, i, packed["state"].get("hour"), answers)
    if geometry is None:
        return None
    payload = {
        "sleeve": TAG,
        "symbol": symbol,
        "direction": geometry["direction"],
        "decision_day": decision_day,
        "stop_dist": geometry["stop_dist"],
        "target_dist": None,
        "intra_size": geometry["intra_size"],
    }
    if geometry["expiry_bars"] is not None:
        payload["expiry_bars"] = geometry["expiry_bars"]
    return trade_intent(**payload)


DRAFT_SLEEVESPEC = {
    "tag": TAG,
    "timeframe": "M15",
    "cluster": "fx_reversion_research",
    "on_surface": list(ON_SURFACE),
    "exit": {
        "model": "Module_ATR_research",
        "structure_stop": True,
        "fixed_rr_target": None,
    },
    "never_alias_to": NEVER_ALIAS_TO,
    "live_armed": True,
    "place": True,
    "apply": True,
    "lens": LENS,
    "cite_separate_from": list(CITE_SEPARATE_FROM),
}
