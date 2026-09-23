"""Metals sleeves. Gold, silver, platinum, and every other broker metal.

The broker metal list is the surface the book walks. Geometry, filters,
and size are one Score pack for that bar. An empty answer, a tie, or an
error leaves the quantity unset. Cost and spread do not remove a metal.
The entry is a limit order. This module does not send.
"""
from __future__ import annotations

from typing import Any, Optional

from ..primitives import atr14, autocorr
from ..admission import TradeIntent

# Names of the hops. The numbers are not the decision.
GATE_K = "gate_k"
TARGET_R = "target_r"
STOP_BUF = "stop_buf"
AC_THR = "ac_thr"
AC_FLOOR_SB = "ac_floor_sb"
SIZE_MULT = "size_mult"
MIN_BARS = "min_bars"
ATR_WINDOW = "atr_window"
TREND_LB = "trend_lb"
TREND_ATR = "trend_atr"
SCAN_FROM = "scan_from"
SCAN_SPAN = "scan_span"
SCAN_OLDEST = "scan_oldest"
GAP_SHIFT = "gap_shift"
GAP_ATR = "gap_atr"
AC_LAG = "ac_lag"
SLOPE_BARS = "slope_bars"
MOM_BARS = "mom_bars"
LIMIT_PRICE = "limit_price"
ON_METAL = "on_metal"

_SCORE_SPOTS = (
    GATE_K,
    TARGET_R,
    STOP_BUF,
    AC_THR,
    AC_FLOOR_SB,
    SIZE_MULT,
    MIN_BARS,
    ATR_WINDOW,
    TREND_LB,
    TREND_ATR,
    SCAN_FROM,
    SCAN_SPAN,
    SCAN_OLDEST,
    GAP_SHIFT,
    GAP_ATR,
    AC_LAG,
    SLOPE_BARS,
    MOM_BARS,
    LIMIT_PRICE,
)
_MODEL = "jev-1.13.0"
_UNSET = " An empty score leaves it unset. A tie leaves it unset. An error leaves it unset."
_CACHE: dict[tuple, dict[str, Any]] = {}

# Name stays for importers. It does not lift the stop.
ATR_STOP_FLOOR = 0


def _broker_metals() -> tuple[str, ...]:
    """Metals the Challenge surface already lists. A missing list stays empty."""

    try:
        from .account_surface import FAMILIES
    except Exception:
        return ()
    names = FAMILIES.get("metals") if isinstance(FAMILIES, dict) else None
    if not names:
        return ()
    out: list[str] = []
    for name in names:
        text = str(name).strip()
        if text and text not in out:
            out.append(text)
    return tuple(out)


ON_SURFACE = _broker_metals()


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
    return int(round(number))


def _timeout_s(facts: dict | None) -> float | None:
    """Seconds until this bar prints, when that fact is already on the card.

    No expiry means no timeout. A shorter score on the card is still the wait.
    """

    if not isinstance(facts, dict):
        return None
    for key in ("seconds_until_print", "seconds_from_clock", "bar_deadline_s", "timeout_s"):
        number = _finite(facts.get(key))
        if number is not None and number > 0:
            return number
    return None


def _questions(facts: dict | None = None, bars=None, i: int | None = None) -> dict[str, Any]:
    from src.judgment.jev_questions import spot_question
    from .spot_choice import amount_question, anchors_for, structure_notes

    notes = structure_notes(bars, i)
    text = {
        GATE_K: "The score you return is the ATR-average multiple that opens this bar." + _UNSET,
        TARGET_R: "The score you return is the reward multiple of the stop for this bar." + _UNSET,
        STOP_BUF: "The score you return is the ATR buffer added to this stop." + _UNSET,
        AC_THR: "The score you return is the autocorrelation level for the core band." + _UNSET,
        AC_FLOOR_SB: "The score you return is the lower autocorrelation level of the soft band." + _UNSET,
        SIZE_MULT: "The score you return is the soft-band size for this bar." + _UNSET,
        MIN_BARS: "The score you return is how many closed bars this scan needs." + _UNSET,
        ATR_WINDOW: "The score you return is how many ATR values the average uses." + _UNSET,
        TREND_LB: "The score you return is the trend lookback in bars." + _UNSET,
        TREND_ATR: "The score you return is the ATR multiple that marks the trend." + _UNSET,
        SCAN_FROM: "The score you return is how many bars back the gap scan starts. " + notes["gap"] + _UNSET,
        SCAN_SPAN: "The score you return is how far back the gap scan reaches. " + notes["gap"] + _UNSET,
        SCAN_OLDEST: "The score you return is the oldest bar index the gap scan may use. " + notes["gap"] + _UNSET,
        GAP_SHIFT: "The score you return is the bar distance between the two edges of the gap. " + notes["shift"] + _UNSET,
        GAP_ATR: "The score you return is the gap size as a multiple of ATR." + _UNSET,
        AC_LAG: "The score you return is the autocorrelation lag in bars. " + notes["lag"] + _UNSET,
        SLOPE_BARS: "The score you return is how many closes the slope uses." + _UNSET,
        MOM_BARS: "The score you return is how many bars the momentum uses." + _UNSET,
        LIMIT_PRICE: (
            "The entry is a limit order. The score you return is the limit price "
            "in this symbol's price units. The close on this state is a fact. "
            "Cost and spread are not a reason to leave the price unset."
            + _UNSET
        ),
    }
    packed: dict[str, Any] = {}
    _questions.anchors = {}
    for spot in _SCORE_SPOTS:
        anchors = anchors_for(spot, facts, bars=bars, index=i)
        _questions.anchors[spot] = anchors
        packed.update(amount_question(spot, text[spot], anchors))
    packed.update(
        spot_question(
            ON_METAL,
            (
                "Is this symbol a metal on the broker list on this state? "
                "Gold, silver, platinum, and any other metal the broker lists stay on the surface. "
                "The entry is a limit order. Cost and spread are not a reason to call it off the surface. "
                "An empty answer, a tie, or an error is not a side."
            ),
            {
                "on_metal": "The symbol is a metal on the broker list. The entry is a limit order.",
                "off_metal": "The symbol is not a metal on the broker list.",
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

        picked = unique_highest(probs, ("on_metal", "off_metal"))
    except Exception:
        return None
    if picked in {"on_metal", "off_metal"}:
        return str(picked)
    return None


def _ask_all(facts: dict, bars=None, i: int | None = None) -> dict[str, Any]:
    """One post for this bar. Independent scores travel together."""

    out: dict[str, Any] = {spot: None for spot in _SCORE_SPOTS}
    out[ON_METAL] = None
    out["_asked"] = False
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import append_outcome, prior_outcomes
    except Exception:
        return out
    try:
        questions = _questions(facts, bars, i)
    except Exception:
        return out
    state = dict(facts)
    state["order_kind"] = "limit"
    state["entry"] = "limit"
    try:
        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []
    call = {
        "questions": questions,
        "model": _MODEL,
        "merge_sleeve": False,
        "require_equity": False,
    }
    wait = _timeout_s(state)
    if wait is not None:
        call["timeout_s"] = wait
    def _once(posted):
        posted_call = dict(call)
        posted_call["questions"] = posted
        return evaluate(state, **posted_call)

    def _rebuild():
        return _questions(facts, bars, i)

    try:
        from .spot_choice import post_again

        receipt = post_again(_once, questions, _rebuild)
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
            append_outcome(
                spot,
                number,
                state,
                error=None if number is not None else "empty",
            )
        except Exception:
            pass
    out[ON_METAL] = _side(answers.get(ON_METAL))
    out["_asked"] = True
    fvg_signal.last = out
    return out


def _identity(bars, i) -> tuple | None:
    try:
        bar = bars[i]
        return (int(i), int(len(bars)), float(bar.o), float(bar.h), float(bar.l), float(bar.c))
    except Exception:
        return None


def _cost_facts(extra: dict | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not isinstance(extra, dict):
        return out
    for key in ("spread", "cost", "spread_pips", "ask", "bid"):
        if key not in extra:
            continue
        number = _finite(extra.get(key))
        if number is not None:
            out[key] = number
    return out


def _card(bars, i, extra: dict) -> dict[str, Any]:
    bar = bars[i]
    atr = atr14(bars, i)
    card: dict[str, Any] = {
        "n_bars": len(bars),
        "bar_index": i,
        "open": bar.o,
        "high": bar.h,
        "low": bar.l,
        "close": bar.c,
        "atr": atr if atr > 0 else None,
        "broker_metals": list(ON_SURFACE),
        "order_kind": "limit",
        "entry": "limit",
    }
    for key, value in extra.items():
        if value is None:
            continue
        if key in card:
            continue
        number = _finite(value)
        if number is not None:
            card[key] = number
        elif isinstance(value, str):
            card[key] = value
        elif isinstance(value, (list, tuple)):
            card[key] = [str(item) for item in value]
    return card


def _for_bars(bars, i, **extra) -> dict[str, Any]:
    """The pack for this bar. A second read of the same bar does not ask again."""

    if not bars or i is None or i < 0 or i >= len(bars):
        return {}
    key = _identity(bars, i)
    if key is None:
        return {}
    hit = _CACHE.get(key)
    if hit is not None and (not extra.get("symbol") or hit.get("_saw_symbol")):
        fvg_signal.last = hit
        return hit
    try:
        facts = _card(bars, i, extra)
    except Exception:
        return {}
    decided = _ask_all(facts, bars, i)
    if decided.get("_asked"):
        decided["_saw_symbol"] = bool(extra.get("symbol"))
        _CACHE[key] = decided
    fvg_signal.last = decided
    return decided


def _trend(bars, i, look: int | None, mult: float | None) -> int:
    if look is None or mult is None or i < look or look < 0:
        return 0
    try:
        atr = atr14(bars, i)
    except Exception:
        return 0
    if atr <= 0:
        return 0
    past = i - look
    if past < 0 or past >= len(bars):
        return 0
    diff = bars[i].c - bars[past].c
    if diff > mult * atr:
        return 1
    if diff < -mult * atr:
        return -1
    return 0


def htf_trend(bars, i, lb=None, atr_multiple=None) -> int:
    """+1, -1, or 0 from the pack already asked for this bar.

    A passed lookback is not the decision. No pack leaves the trend unset.
    """

    del lb, atr_multiple
    if not bars or i is None or i < 0 or i >= len(bars):
        return 0
    key = _identity(bars, i)
    decided = _CACHE.get(key) if key is not None else None
    if not isinstance(decided, dict):
        return 0
    return _trend(bars, i, _whole(decided.get(TREND_LB)), _finite(decided.get(TREND_ATR)))


def _first_gap(B, i, decided, atr: float):
    span = _whole(decided.get(SCAN_SPAN))
    oldest = _whole(decided.get(SCAN_OLDEST))
    start = _whole(decided.get(SCAN_FROM))
    shift = _whole(decided.get(GAP_SHIFT))
    gap_mult = _finite(decided.get(GAP_ATR))
    look = _whole(decided.get(TREND_LB))
    mult = _finite(decided.get(TREND_ATR))
    if None in (span, oldest, start, shift, gap_mult, look, mult):
        return None
    if shift is None or shift < 1 or atr <= 0:
        return None
    side = _trend(B, i, look, mult)
    if side == 0:
        return None
    begin = i - start
    stop = max(i - span, oldest)
    if begin < stop:
        return None
    bar = B[i]
    for k in range(begin, stop, -1):
        if k - shift < 0 or k >= len(B):
            continue
        if side == 1:
            gap_top = B[k].l
            gap_bot = B[k - shift].h
        else:
            gap_bot = B[k].h
            gap_top = B[k - shift].l
        if gap_top - gap_bot < gap_mult * atr:
            continue
        if side == 1 and bar.l <= gap_top and bar.c > gap_bot and bar.c > bar.o:
            return side, k, gap_top, gap_bot
        if side == -1 and bar.h >= gap_bot and bar.c < gap_top and bar.c < bar.o:
            return side, k, gap_top, gap_bot
    return None


def _scan(B, atrs, i, decided) -> Optional[tuple[int, float]]:
    min_bars = _whole(decided.get(MIN_BARS))
    window = _whole(decided.get(ATR_WINDOW))
    gate = _finite(decided.get(GATE_K))
    buf = _finite(decided.get(STOP_BUF))
    if min_bars is None or window is None or window < 1 or gate is None or buf is None:
        return None
    if i < min_bars or i + 1 < window or i >= len(atrs):
        return None
    atr = atrs[i]
    if atr <= 0:
        return None
    sma = sum(atrs[i - window + 1 : i + 1]) / window
    if sma <= 0 or atr < gate * sma:
        return None
    found = _first_gap(B, i, decided, atr)
    if found is None:
        return None
    side, _k, gap_top, gap_bot = found
    bar = B[i]
    if side == 1:
        dist = (bar.c - min(bar.l, gap_bot)) + buf * atr
    else:
        dist = (max(bar.h, gap_top) - bar.c) + buf * atr
    if dist <= 0:
        return None
    return side, dist


def fvg_signal(B, atrs, i, gate_k=None) -> Optional[tuple[int, float]]:
    """(direction, stop distance) when the pack's geometry holds, else None.

    A passed gate is a fact on the card. The returned gate is the one used.
    """

    if not B or i is None or i < 0 or i >= len(B):
        return None
    extra: dict[str, Any] = {"order_kind": "limit", "broker_metals": list(ON_SURFACE)}
    number = _finite(gate_k)
    if number is not None:
        extra["caller_gate"] = number
    decided = _for_bars(B, i, **extra)
    if not atrs or i >= len(atrs):
        return None
    return _scan(B, atrs, i, decided)


fvg_signal.last = {}


def _runner_R(vr: float) -> float | None:
    """Reward multiple from the pack for this bar. Empty stays unset."""

    del vr
    decided = fvg_signal.last if isinstance(getattr(fvg_signal, "last", None), dict) else {}
    if not decided:
        return None
    return _finite(decided.get(TARGET_R))


def _ols_slope(y) -> float:
    n = len(y)
    if n == 0:
        return 0.0
    xm = (n - 1) / 2.0
    ym = sum(y) / n
    denom = sum((x - xm) ** 2 for x in range(n))
    if denom == 0:
        return 0.0
    return sum((x - xm) * (y[x] - ym) for x in range(n)) / denom


def find_fvg(B, atrs, i):
    """Retested gap from the pack already asked for this bar. No pack, no gap."""

    if not B or i is None or i < 0 or i >= len(B) or not atrs or i >= len(atrs):
        return None
    key = _identity(B, i)
    decided = _CACHE.get(key) if key is not None else None
    if not isinstance(decided, dict):
        return None
    atr = atrs[i]
    if atr <= 0:
        return None
    found = _first_gap(B, i, decided, atr)
    if found is None:
        return None
    side, k, gap_top, gap_bot = found
    return {"gap_top": gap_top, "gap_bot": gap_bot, "k": k, "tr": side}


def _a8_features(B, atrs, i, vr, bar_time) -> dict:
    """Measured features. The windows are the pack's scores. A miss stays None."""

    htf_slope_norm = None
    mom_20_atr = None
    fresh = None
    decided: dict[str, Any] = {}
    if B and i is not None and 0 <= i < len(B):
        key = _identity(B, i)
        cached = _CACHE.get(key) if key is not None else None
        if isinstance(cached, dict):
            decided = cached
        slope_n = _whole(decided.get(SLOPE_BARS))
        mom_n = _whole(decided.get(MOM_BARS))
        close = B[i].c
        atr = atrs[i] if atrs and i < len(atrs) else None
        if slope_n is not None and slope_n >= 1 and i + 1 >= slope_n and close:
            ys = [B[j].c for j in range(i - slope_n + 1, i + 1)]
            htf_slope_norm = _ols_slope(ys) * slope_n / close
        if mom_n is not None and mom_n >= 1 and i >= mom_n and atr is not None and atr > 0:
            mom_20_atr = (close - B[i - mom_n].c) / atr
        fvg = find_fvg(B, atrs, i)
        if fvg is not None:
            fresh = i - fvg["k"]
    session_hour = None
    if bar_time is not None:
        try:
            from .fx_jpy import _to_server_local

            stamped = _to_server_local(bar_time)
            session_hour = stamped.hour if stamped is not None else None
        except Exception:
            session_hour = None
    return {
        "htf_slope_norm": htf_slope_norm,
        "mom_20_atr": mom_20_atr,
        "atr_ratio": vr,
        "fvg_freshness_bars": fresh,
        "session_hour": session_hour,
    }


def _size_mult_soft(ac, vr, size=None):
    """Soft-band size from the pack. Empty stays unset. It is not zero."""

    del ac, vr
    given = _finite(size)
    if given is not None:
        return given
    decided = fvg_signal.last if isinstance(getattr(fvg_signal, "last", None), dict) else {}
    if not decided:
        return None
    return _finite(decided.get(SIZE_MULT))


def _vol(atrs, i, decided) -> float | None:
    window = _whole(decided.get(ATR_WINDOW))
    if window is None or window < 1 or i + 1 < window or i >= len(atrs):
        return None
    sma = sum(atrs[i - window + 1 : i + 1]) / window
    if sma <= 0:
        return None
    return atrs[i] / sma


def _autocorr(bars, i, decided):
    lag = _whole(decided.get(AC_LAG))
    if lag is None or lag < 1:
        return None
    try:
        return autocorr(bars, i, lag)
    except Exception:
        return None


def _measured(bars, bar_time, decided):
    if decided.get(ON_METAL) != "on_metal":
        return None
    i = len(bars) - 1
    try:
        atrs = [atr14(bars, k) for k in range(len(bars))]
    except Exception:
        return None
    sig = _scan(bars, atrs, i, decided)
    if sig is None:
        return None
    direction, dist = sig
    ac = _autocorr(bars, i, decided)
    vr = _vol(atrs, i, decided)
    feats = _a8_features(bars, atrs, i, vr, bar_time)
    return direction, dist, ac, vr, feats


def _eval(symbol, bars, bar_time=None):
    if not bars:
        return None
    i = len(bars) - 1
    decided = _for_bars(
        bars,
        i,
        symbol=symbol,
        cluster="metals",
        order_kind="limit",
        broker_metals=list(ON_SURFACE),
    )
    packed = _measured(bars, bar_time, decided)
    if packed is None:
        return None
    direction, dist, ac, vr, feats = packed
    return i, direction, dist, ac, vr, feats


def _intent(sleeve: str, symbol: str, decision_day: str, bars, bar_time, extra: dict):
    if not bars:
        return None
    i = len(bars) - 1
    facts = {
        "symbol": symbol,
        "cluster": "metals",
        "decision_day": decision_day,
        "order_kind": "limit",
        "broker_metals": list(ON_SURFACE),
    }
    facts.update(_cost_facts(extra))
    decided = _for_bars(bars, i, **facts)
    packed = _measured(bars, bar_time, decided)
    if packed is None:
        return None
    direction, dist, ac, vr, feats = packed
    thr = _finite(decided.get(AC_THR))
    target = _finite(decided.get(TARGET_R))
    price = _finite(decided.get(LIMIT_PRICE))
    if ac is None or thr is None or target is None or price is None or target <= 0 or dist <= 0:
        return None
    if sleeve == "metals_core":
        if ac < thr:
            return None
        size = None
    else:
        band = _finite(decided.get(AC_FLOOR_SB))
        size = _finite(decided.get(SIZE_MULT))
        if band is None or size is None or ac >= thr or ac < band or size <= 0:
            return None
    payload = dict(
        sleeve=sleeve,
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=dist,
        target_dist=target * dist,
        entry_price=price,
        vr=vr,
        **feats,
    )
    if size is not None:
        payload["intra_size"] = size
    return TradeIntent(**payload)


def generate_metals_core(symbol: str, bars, decision_day: str, *, bar_time=None, **extra) -> Optional[TradeIntent]:
    return _intent("metals_core", symbol, decision_day, bars, bar_time, extra)


def generate_metals_softband(symbol: str, bars, decision_day: str, *, bar_time=None, **extra) -> Optional[TradeIntent]:
    return _intent("metals_softband", symbol, decision_day, bars, bar_time, extra)
