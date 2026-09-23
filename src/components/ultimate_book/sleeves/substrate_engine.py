"""Substrate state for the live cell sleeves.

The windows, the bucket edges, the stop, the target, and the side come
back from one Score pack for this bar. An empty answer, a tie, or an
error leaves that field unset. Nothing here puts a printed constant back.
`atr14` is the measure in primitives. This module does not send.
"""
from __future__ import annotations

import threading
from typing import Any, Optional

from ..primitives import atr14

_MODEL = "jev-1.13.0"
_UNSET = " An empty score leaves it unset. A tie leaves it unset. An error leaves it unset."
_LOCK = threading.Lock()
_CACHE: dict[tuple, dict[str, Any]] = {}

# Name stays so a research import still binds. The bar count is the score.
WARMUP = None

_WINDOW_SPOTS = (
    "warmup_bars",
    "atr_mean_bars",
    "slope_short_bars",
    "slope_mid_bars",
    "slope_long_bars",
    "range_bars",
    "comp_short_bars",
    "comp_long_bars",
    "persist_bars",
    "persist_min_bars",
)
_BOUND_SPOTS = (
    "align_thr",
    "vr_lo",
    "vr_mid",
    "vr_hi",
    "slope_up",
    "slope_dn",
    "rng_low",
    "rng_high",
    "comp_coil",
    "comp_expand",
    "persist_trend",
    "persist_revert",
    "session_asia_end",
    "session_london_end",
    "stop_atr",
    "target_r",
)
_SCORE_SPOTS = _WINDOW_SPOTS + _BOUND_SPOTS
_DIRECTION = "direction"

_TEXT = {
    "warmup_bars": "The score you return is how many closed bars this state needs before it can be read.",
    "atr_mean_bars": "The score you return is how many ATR values the mean uses.",
    "slope_short_bars": "The score you return is how many bars the short slope looks back.",
    "slope_mid_bars": "The score you return is how many bars the mid slope looks back.",
    "slope_long_bars": "The score you return is how many bars the long slope looks back.",
    "range_bars": "The score you return is how many bars the range position uses.",
    "comp_short_bars": "The score you return is how many bars the short true-range sum uses.",
    "comp_long_bars": "The score you return is how many bars the long true-range sum uses.",
    "persist_bars": "The score you return is how many returns the persistence uses.",
    "persist_min_bars": "The score you return is how many returns persistence needs before it is readable.",
    "align_thr": "The score you return is the slope size that counts as aligned on this bar.",
    "vr_lo": "The score you return is the vol-ratio edge below which vol is lo.",
    "vr_mid": "The score you return is the vol-ratio edge below which vol is mid.",
    "vr_hi": "The score you return is the vol-ratio edge below which vol is hi.",
    "slope_up": "The score you return is the slope edge above which trend is up.",
    "slope_dn": "The score you return is the slope edge below which trend is down.",
    "rng_low": "The score you return is the range-position edge below which position is low.",
    "rng_high": "The score you return is the range-position edge above which position is high.",
    "comp_coil": "The score you return is the compression edge below which compression is coil.",
    "comp_expand": "The score you return is the compression edge above which compression is expand.",
    "persist_trend": "The score you return is the persistence edge at or above which persistence is trend.",
    "persist_revert": "The score you return is the persistence edge at or below which persistence is revert.",
    "session_asia_end": "The score you return is the hour before which the session is asia.",
    "session_london_end": "The score you return is the hour before which the session is london.",
    "stop_atr": "The score you return is the stop as a multiple of ATR on this bar.",
    "target_r": "The score you return is the target as a multiple of the stop on this bar.",
}

_MTF_LABEL = {1: "aligned", -1: "conflict", 0: "neutral"}


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


def _empty() -> dict[str, Any]:
    out: dict[str, Any] = {spot: None for spot in _SCORE_SPOTS}
    out["direction_side"] = None
    return out


def _key(facts: dict) -> tuple:
    return (
        facts.get("sleeve"),
        facts.get("symbol"),
        facts.get("decision_day"),
        facts.get("i"),
        facts.get("n_bars"),
        _finite(facts.get("close")),
        _finite(facts.get("high")),
        _finite(facts.get("low")),
        facts.get("hour"),
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
            _DIRECTION,
            "Which side does this cell take on this state? "
            "An empty answer, a tie, or an error is not a side.",
            {
                "long": "The cell takes the long side.",
                "short": "The cell takes the short side.",
            },
        )
    )
    return packed


def _side(block: Any) -> str | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, dict) or not probs:
        return None
    try:
        from src.judgment.jev_questions import unique_highest

        picked = unique_highest(probs, ("long", "short"))
    except Exception:
        return None
    if picked in {"long", "short"}:
        return str(picked)
    return None


def _post(facts: dict, bars=None, i: int | None = None, bar_times=None) -> dict[str, Any]:
    """One post for this bar. Windows, edges, geometry, and side travel together."""

    out = _empty()
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
    out["direction_side"] = _side(answers.get(_DIRECTION))
    return out


def _ask(facts: dict, bars=None, i: int | None = None, bar_times=None) -> dict[str, Any]:
    """The pack for these facts. The same facts reuse it. A new bar asks again."""

    key = _key(facts)
    with _LOCK:
        hit = _CACHE.get(key)
    if hit is not None:
        return dict(hit)
    pack = _post(facts, bars, i, bar_times)
    sleeve = facts.get("sleeve")
    symbol = facts.get("symbol")
    with _LOCK:
        for old in list(_CACHE):
            if old[0] == sleeve and old[1] == symbol and old != key:
                _CACHE.pop(old, None)
        _CACHE[key] = pack
    return dict(pack)


def _ac(rets, min_n: int | None = None) -> float | None:
    """Lag-1 autocorrelation. A short sample or a flat sample stays unset."""

    if min_n is None:
        return None
    n = len(rets)
    if n < min_n:
        return None
    mean = sum(rets) / n
    num = sum((rets[k] - mean) * (rets[k - 1] - mean) for k in range(1, n))
    den = sum((x - mean) ** 2 for x in rets)
    if den <= 0:
        return None
    return num / den


def _bucket_vr(vr, lo=None, mid=None, hi=None):
    if vr is None or lo is None or mid is None or hi is None:
        return None
    if vr < lo:
        return "lo"
    if vr < mid:
        return "mid"
    if vr < hi:
        return "hi"
    return "xhi"


def _bucket_slope(s, up=None, dn=None):
    if s is None or up is None or dn is None:
        return None
    if s > up:
        return "up"
    if s < dn:
        return "dn"
    return "flat"


def _bucket_rng(p, low=None, high=None):
    if p is None or low is None or high is None:
        return None
    if p < low:
        return "low"
    if p > high:
        return "high"
    return "mid"


def _bucket_comp(c, coil=None, expand=None):
    if c is None or coil is None or expand is None:
        return None
    if c < coil:
        return "coil"
    if c > expand:
        return "expand"
    return "norm"


def _bucket_persist(a, trend=None, revert=None):
    if a is None or trend is None or revert is None:
        return None
    if a >= trend:
        return "trend"
    if a <= revert:
        return "revert"
    return "rand"


def _bucket_session(h, asia_end=None, london_end=None):
    if h is None or asia_end is None or london_end is None:
        return None
    if h < asia_end:
        return "asia"
    if h < london_end:
        return "london"
    return "ny"


def _window(bounds: dict, spot: str) -> int | None:
    return _whole(bounds.get(spot))


def compute_state(
    bars,
    i: int,
    hour: Optional[int] = None,
    *,
    sleeve: str | None = None,
    symbol: str | None = None,
    decision_day: str | None = None,
) -> Optional[dict]:
    """Leak-free features at bar i. Missing bounds leave the state unset."""

    facts: dict[str, Any] = {
        "sleeve": sleeve,
        "symbol": symbol,
        "decision_day": decision_day,
        "i": i,
        "n_bars": len(bars) if bars is not None else 0,
        "hour": hour,
    }
    if bars is not None and 0 <= i < len(bars):
        bar = bars[i]
        facts["close"] = getattr(bar, "c", None)
        facts["high"] = getattr(bar, "h", None)
        facts["low"] = getattr(bar, "l", None)
    bounds = _ask(facts, bars, i)
    windows = {spot: _window(bounds, spot) for spot in _WINDOW_SPOTS}
    if any(value is None for value in windows.values()):
        return None
    if bars is None or i < 0 or i >= len(bars):
        return None
    warm = windows["warmup_bars"]
    furthest = max(windows[spot] for spot in _WINDOW_SPOTS if spot != "persist_min_bars")
    if i + 1 < warm or i < furthest:
        return None
    a = atr14(bars, i)
    if a is None or a <= 0:
        return None
    mean_n = windows["atr_mean_bars"]
    sma = sum(atr14(bars, k) for k in range(i - mean_n + 1, i + 1)) / mean_n
    vr = None if sma <= 0 else a / sma
    close = bars[i].c
    slope_short = (close - bars[i - windows["slope_short_bars"]].c) / a
    slope_mid = (close - bars[i - windows["slope_mid_bars"]].c) / a
    slope_long = (close - bars[i - windows["slope_long_bars"]].c) / a
    thr = _finite(bounds.get("align_thr"))
    mtf_align = None
    if thr is not None:
        def _sgn(value: float) -> int:
            if value > thr:
                return 1
            if value < -thr:
                return -1
            return 0

        short_sign = _sgn(slope_short)
        long_sign = _sgn(slope_long)
        if short_sign != 0 and short_sign == long_sign:
            mtf_align = 1
        elif short_sign != 0 and long_sign != 0 and short_sign == -long_sign:
            mtf_align = -1
        else:
            mtf_align = 0
    range_n = windows["range_bars"]
    lo = min(bars[k].l for k in range(i - range_n + 1, i + 1))
    hi = max(bars[k].h for k in range(i - range_n + 1, i + 1))
    rng_pos = None if hi <= lo else (close - lo) / (hi - lo)

    def _tr(k: int) -> float:
        return max(
            bars[k].h - bars[k].l,
            abs(bars[k].h - bars[k - 1].c),
            abs(bars[k].l - bars[k - 1].c),
        )

    short_n = windows["comp_short_bars"]
    long_n = windows["comp_long_bars"]
    num = sum(_tr(k) for k in range(i - short_n + 1, i + 1)) / short_n
    den = sum(_tr(k) for k in range(i - long_n + 1, i + 1)) / long_n
    comp = None if den <= 0 else num / den
    persist_n = windows["persist_bars"]
    rets = [bars[k].c - bars[k - 1].c for k in range(i - persist_n + 1, i + 1)]
    ac = _ac(rets, windows["persist_min_bars"])
    return {
        "vr": vr,
        "slope20": slope_short,
        "slope50": slope_mid,
        "slope100": slope_long,
        "mtf_align": mtf_align,
        "rng_pos": rng_pos,
        "compression": comp,
        "ac60": ac,
        "hour": hour,
        "_atr": a,
        "_bounds": bounds,
    }


def cell_coords(st: dict) -> dict:
    """Discrete coordinates. A missing edge leaves that coordinate unset."""

    bounds = st.get("_bounds") if isinstance(st, dict) else None
    if not isinstance(bounds, dict):
        bounds = {}
    coords = {
        "vol": _bucket_vr(
            st.get("vr"),
            _finite(bounds.get("vr_lo")),
            _finite(bounds.get("vr_mid")),
            _finite(bounds.get("vr_hi")),
        ),
        "trend": _bucket_slope(
            st.get("slope50"),
            _finite(bounds.get("slope_up")),
            _finite(bounds.get("slope_dn")),
        ),
        "mtf": _MTF_LABEL.get(st.get("mtf_align")),
        "rngpos": _bucket_rng(
            st.get("rng_pos"),
            _finite(bounds.get("rng_low")),
            _finite(bounds.get("rng_high")),
        ),
        "comp": _bucket_comp(
            st.get("compression"),
            _finite(bounds.get("comp_coil")),
            _finite(bounds.get("comp_expand")),
        ),
        "persist": _bucket_persist(
            st.get("ac60"),
            _finite(bounds.get("persist_trend")),
            _finite(bounds.get("persist_revert")),
        ),
    }
    if st.get("hour") is not None:
        coords["session"] = _bucket_session(
            st.get("hour"),
            _finite(bounds.get("session_asia_end")),
            _finite(bounds.get("session_london_end")),
        )
    return coords


def stop_target(atr: float, stop_atr: float, target_R: float) -> tuple[float, float]:
    """Stop and target distances from the returned multiples and this bar's ATR."""

    sd = stop_atr * atr
    td = target_R * sd
    return sd, td


def cell_matches(coords: dict, conds: dict) -> bool:
    """True when every named coordinate equals the cell. An unset coordinate does not."""

    return all(coords.get(name) == want for name, want in conds.items())
