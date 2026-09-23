"""Hold/exit extras from named Challenge deals and per-symbol bars.

The labels and the parameters are the System One return for this state.
The call is ``jev_client.evaluate`` with model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
Questions are only a Noul, a Choice, or a Score. Prior outcomes are on
every ask. An empty answer, a tie, or an error leaves that return unset.
A floor and a baseline are not a question. This module does not send.

Price excursion, elapsed hours, and the side word are facts on the ask.
They are not copied back when the return is missing. EXPOST stays off the
live gold_state / symbol_state object. These values ride in compose
``extra`` for as_of_open_study / deal_close rows only.
Never remint. Never flatten. Never invent a trail when final_sl is missing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence

MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

# Menus name the options. Membership is the return, not a string match.
_INVENTORY_ORDER = ("breach_flatten", "time_stop", "broker_tp", "orig_stop", "other")
_SCOREBOARD_ORDER = ("orig_stop", "orig_tp", "time_stop", "breach_flatten", "other")
SCOREBOARD_EXIT = frozenset(_SCOREBOARD_ORDER)
_SESSION_ORDER = (
    "asia",
    "asia_london",
    "london",
    "london_ny",
    "ny",
    "late_ny",
    "dead_21_00z",
    "friday_cutoff",
    "weekend",
    "unknown",
)
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "90K",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "110K",
)
_INVENTORY_CRITERIA = {
    "breach_flatten": "The named close is a breach flatten.",
    "time_stop": "The named close is a time stop.",
    "broker_tp": "The named close is a broker target.",
    "orig_stop": "The named close is the original stop.",
    "other": "The named close is some other class.",
}
_SCOREBOARD_CRITERIA = {
    "orig_stop": "The scoreboard class is the original stop.",
    "orig_tp": "The scoreboard class is the original target.",
    "time_stop": "The scoreboard class is a time stop.",
    "breach_flatten": "The scoreboard class is a breach flatten.",
    "other": "The scoreboard class is some other class.",
}
_SESSION_CRITERIA = {
    "asia": "The close sits in the named Asia session.",
    "asia_london": "The close sits in the named Asia-London join.",
    "london": "The close sits in the named London session.",
    "london_ny": "The close sits in the named London-New York overlap.",
    "ny": "The close sits in the named New York session.",
    "late_ny": "The close sits in the named late New York session.",
    "dead_21_00z": "The close sits in the named dead session.",
    "friday_cutoff": "The close sits in the named Friday cutoff.",
    "weekend": "The close sits on the named weekend.",
    "unknown": "The close session is not one of the named sessions.",
}
_M15 = timedelta(minutes=15)


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _scrub(value: Any) -> Any:
    """Drop floor and baseline keys before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return _scrub_text(text)


def _iso(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    else:
        moment = moment.astimezone(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _clock(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _probs_best(probs: Mapping[str, Any], order: tuple[str, ...] | None) -> tuple[str | None, bool]:
    """Unique highest, and whether the top probability is tied.

    A missing probability is not zero. A bare label is not a probability.
    """

    names = tuple(order) if order else tuple(str(name) for name in probs)
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in names:
        if name not in probs:
            continue
        raw = probs.get(name)
        if raw is None or isinstance(raw, bool):
            continue
        try:
            p = float(raw)
        except (TypeError, ValueError):
            continue
        if p != p:
            continue
        seen = True
        if best_p is None or p > best_p + 1e-12:
            best = str(name)
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if not seen or best is None:
        return None, False
    return best, tied


def _unique(probs: Mapping[str, Any] | None, order: tuple[str, ...] | None) -> str | None:
    if not isinstance(probs, Mapping) or not probs:
        return None
    best, tied = _probs_best(probs, order)
    if tied or best is None:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping):
        return None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probs, order)
    except Exception:
        picked = None
    if picked not in order:
        picked = _unique(probs, order)
    if picked not in order:
        return None
    return str(picked)


def _score(block: Any) -> float | None:
    """The Score that came back. It is not snapped to a level."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        pass
    if block.get("score") is None:
        return None
    return _finite(block.get("score"))


def _pull(block: Any, kind: str, order: tuple[str, ...] | None) -> Any:
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block)


def _why(block: Any, value: Any, order: tuple[str, ...] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = block.get("probabilities") if isinstance(block, Mapping) else None
    if isinstance(probs, Mapping) and probs:
        _best, tied = _probs_best(probs, order)
        if tied:
            return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numbers already on the facts. A score may sit between them."""

    found: list[float] = []
    for key, value in dict(facts or {}).items():
        if _limit_key(str(key)):
            continue
        number = _finite(value)
        if number is not None:
            found.append(number)
    if not found:
        return list(_BETWEEN)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    body = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(value) for key, value in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, body["criteria"])
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = dict(block)
            shaped["type"] = "choice"
            shaped["instructions"] = instructions
            shaped["criteria"] = dict(body["criteria"])
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, text: str, levels: Sequence[str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    criteria = [str(item) for item in levels] if levels else list(_BETWEEN)
    body = {"type": "score", "instructions": instructions, "criteria": criteria}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = dict(block)
            shaped["type"] = "score"
            shaped["instructions"] = instructions
            shaped["criteria"] = list(criteria)
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_text(noun: str) -> str:
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "Do not send an order."
    )


def _choice_text(noun: str) -> str:
    return (
        f"The option you return is the {noun} for this state. "
        "An empty answer or a tie is not that {noun}. "
        "Do not send an order."
    )


def _card(extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    state: dict[str, Any] = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "model": MODEL,
    }
    for key, value in dict(extra or {}).items():
        if value is not None:
            state[str(key)] = value
    return state


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state))
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    try:
        from .jev_questions import prior_outcomes

        payload["prior_outcomes"] = prior_outcomes(state=payload, questions=questions)
    except Exception:
        payload["prior_outcomes"] = []
    try:
        from .jev_client import evaluate

        receipt = evaluate(
            payload,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {"error": type(exc).__name__, "answers": {}, "state": payload, "model": MODEL}
    if not isinstance(receipt, dict):
        return {"error": "evaluate_not_a_dict", "answers": {}, "state": payload, "model": MODEL}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "error": error,
        "answers": answers,
        "state": payload,
        "model": receipt.get("model") or MODEL,
    }


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _run(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    spec: Sequence[tuple[str, str, str, tuple[str, ...] | None]],
) -> dict[str, Any]:
    asked = _ask(state, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out: dict[str, Any] = {}
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in spec:
        block = answers.get(qid)
        value = _pull(block, kind, order)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    _remember(asked.get("state") or {}, rows)
    return out


def _one_choice(
    state: Mapping[str, Any],
    qid: str,
    noun: str,
    criteria: Mapping[str, str],
    order: tuple[str, ...],
    parameter_qid: str,
) -> str | None:
    levels = _levels(state)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(qid, _choice_text(noun), criteria))
    pack.update(_score_question(parameter_qid, _score_text(f"{noun} parameter"), levels))
    try:
        got = _run(
            state,
            pack,
            (
                ("label", "choice", qid, order),
                ("parameter", "score", parameter_qid, None),
            ),
        )
    except Exception:
        return None
    label = got.get("label")
    if label not in order:
        return None
    return str(label)


def _one_score(state: Mapping[str, Any], qid: str, noun: str) -> float | None:
    pack = _score_question(qid, _score_text(noun), _levels(state))
    try:
        got = _run(state, pack, (("value", "score", qid, None),))
    except Exception:
        return None
    return _finite(got.get("value"))


def _side_sign(side: str) -> int:
    raw = (side or "").lower()
    if raw in {"long", "buy"}:
        return 1
    if raw in {"short", "sell"}:
        return -1
    return 0


def classify_close(close_reason: Any, exit_class: Any = None) -> str | None:
    """Inventory close label. The choice is the return. A miss stays unset."""

    reason = _text(close_reason)
    named = _text(exit_class)
    if reason is None and named is None:
        return None
    return _one_choice(
        _card({"close_reason": reason, "exit_class": named}),
        "hold_inventory_close",
        "inventory close label",
        _INVENTORY_CRITERIA,
        _INVENTORY_ORDER,
        "hold_inventory_parameter",
    )


def named_exit_class(close_reason: Any, exit_class: Any = None) -> str | None:
    """Scoreboard close class. The choice is the return. A miss stays unset.

    Inventory ``close_label`` still uses ``classify_close``.
    """

    reason = _text(close_reason)
    named = _text(exit_class)
    if reason is None and named is None:
        return None
    return _one_choice(
        _card({"close_reason": reason, "exit_class": named}),
        "hold_scoreboard_exit",
        "scoreboard exit class",
        _SCOREBOARD_CRITERIA,
        _SCOREBOARD_ORDER,
        "hold_scoreboard_parameter",
    )


def _measured_r(
    *,
    entry: float | None,
    exit_px: float | None,
    stop_dist: float | None,
    side: str,
) -> float | None:
    """Geometry on the named prices. Evidence for the ask, not the return."""

    sign = _side_sign(side)
    entry_n = _finite(entry)
    exit_n = _finite(exit_px)
    stop_n = _finite(stop_dist)
    if entry_n is None or exit_n is None or stop_n is None or stop_n <= 0 or sign == 0:
        return None
    return (exit_n - entry_n) * sign / stop_n


def realized_r(*, entry: float | None, exit_px: float | None, stop_dist: float | None, side: str) -> float | None:
    """Realized R is the score. A missing price, or a miss, stays unset."""

    measured = _measured_r(entry=entry, exit_px=exit_px, stop_dist=stop_dist, side=side)
    if measured is None:
        return None
    return _one_score(
        _card(
            {
                "entry": _finite(entry),
                "exit_px": _finite(exit_px),
                "stop_dist": _finite(stop_dist),
                "side": _text(side),
                "measured_r": measured,
            }
        ),
        "hold_realized_r",
        "realized R",
    )


def runner_score(realized: float | None) -> float | None:
    """Runner score is the score. A miss stays unset."""

    number = _finite(realized)
    if number is None:
        return None
    return _one_score(
        _card({"realized_r": number}),
        "hold_runner_score",
        "runner score",
    )


def mfe_score(mfe_r: float | None) -> float | None:
    """MFE score is the score. A miss stays unset."""

    number = _finite(mfe_r)
    if number is None:
        return None
    return _one_score(
        _card({"mfe_r": number}),
        "hold_mfe_score",
        "MFE score",
    )


def _bar_utc(bar: Any) -> datetime | None:
    utc = getattr(bar, "utc", None)
    if not isinstance(utc, datetime):
        return None
    return _clock(utc)


def _bar_hl(bar: Any) -> tuple[float | None, float | None]:
    inner = getattr(bar, "bar", None)
    if inner is None:
        return None, None
    return _finite(getattr(inner, "h", None)), _finite(getattr(inner, "l", None))


def _last_closed(bars: Sequence[Any], moment: datetime) -> int | None:
    try:
        from .bars import last_closed_at_or_before

        found = last_closed_at_or_before(list(bars), moment)
    except Exception:
        found = None
        for i, bar in enumerate(bars):
            utc = _bar_utc(bar)
            if utc is None:
                continue
            if utc + _M15 <= moment:
                found = i
            elif utc > moment:
                break
        return found
    if isinstance(found, int):
        return found
    return None


def _measured_mfe_mae(
    bars: Sequence[Any] | None,
    *,
    side: str,
    entry: float | None,
    stop_dist: float | None,
    open_utc: datetime | None,
    close_utc: datetime | None,
) -> tuple[float, float] | None:
    """Favorable and adverse R on the named bars. Evidence, not the return."""

    sign = _side_sign(side)
    entry_n = _finite(entry)
    stop_n = _finite(stop_dist)
    if not bars or entry_n is None or stop_n is None or stop_n <= 0 or sign == 0:
        return None
    if open_utc is None or close_utc is None:
        return None
    open_at = _clock(open_utc)
    close_at = _clock(close_utc)
    start = _last_closed(bars, open_at)
    end = _last_closed(bars, close_at)
    if end is None:
        return None
    lo = 0 if start is None else max(0, start - 1)
    fav: float | None = None
    unfav: float | None = None
    for i in range(lo, end + 1):
        bar = bars[i]
        utc = _bar_utc(bar)
        if utc is None:
            continue
        high, low = _bar_hl(bar)
        if high is None or low is None:
            continue
        bar_end = utc + _M15
        if bar_end <= open_at:
            continue
        if utc > close_at:
            break
        if sign > 0:
            this_fav = high - entry_n
            this_unfav = entry_n - low
        else:
            this_fav = entry_n - low
            this_unfav = high - entry_n
        fav = this_fav if fav is None else max(fav, this_fav)
        unfav = this_unfav if unfav is None else max(unfav, this_unfav)
    if fav is None or unfav is None:
        return None
    return fav / stop_n, unfav / stop_n


def mfe_mae_r(
    bars: Sequence[Any] | None,
    *,
    side: str,
    entry: float | None,
    stop_dist: float | None,
    open_utc: datetime | None,
    close_utc: datetime | None,
) -> tuple[float | None, float | None]:
    """MFE and MAE are the scores. A missing bar, or a miss, stays unset."""

    measured = _measured_mfe_mae(
        bars,
        side=side,
        entry=entry,
        stop_dist=stop_dist,
        open_utc=open_utc,
        close_utc=close_utc,
    )
    if measured is None:
        return None, None
    fav, unfav = measured
    state = _card(
        {
            "side": _text(side),
            "entry": _finite(entry),
            "stop_dist": _finite(stop_dist),
            "open_utc": _iso(open_utc),
            "close_utc": _iso(close_utc),
            "measured_mfe_r": fav,
            "measured_mae_r": unfav,
            "bar_count": len(bars or ()),
        }
    )
    levels = _levels(state)
    pack: dict[str, Any] = {}
    pack.update(_score_question("hold_mfe_r", _score_text("favorable excursion in R"), levels))
    pack.update(_score_question("hold_mae_r", _score_text("adverse excursion in R"), levels))
    try:
        got = _run(
            state,
            pack,
            (
                ("mfe", "score", "hold_mfe_r", None),
                ("mae", "score", "hold_mae_r", None),
            ),
        )
    except Exception:
        return None, None
    return _finite(got.get("mfe")), _finite(got.get("mae"))


def close_session_named(close_utc: datetime | None) -> str | None:
    """Close session is the choice. A missing clock, or a miss, stays unset."""

    if close_utc is None:
        return None
    dt = _clock(close_utc)
    return _one_choice(
        _card(
            {
                "close_utc": _iso(dt),
                "hour": dt.hour,
                "weekday": dt.weekday(),
                "is_friday": dt.weekday() == 4,
            }
        ),
        "hold_close_session",
        "close session",
        _SESSION_CRITERIA,
        _SESSION_ORDER,
        "hold_session_parameter",
    )


def _measured_hours(open_utc: datetime | None, close_utc: datetime | None) -> float | None:
    if open_utc is None or close_utc is None:
        return None
    return (_clock(close_utc) - _clock(open_utc)).total_seconds() / 3600.0


def hold_hours(open_utc: datetime | None, close_utc: datetime | None) -> float | None:
    """Hold hours are the score. A missing clock, or a miss, stays unset."""

    measured = _measured_hours(open_utc, close_utc)
    if measured is None:
        return None
    return _one_score(
        _card(
            {
                "open_utc": _iso(open_utc),
                "close_utc": _iso(close_utc),
                "measured_hours": measured,
            }
        ),
        "hold_hours",
        "hold hours",
    )
