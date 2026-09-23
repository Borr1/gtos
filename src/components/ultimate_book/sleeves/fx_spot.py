"""One post for an FX sleeve state.

Choices are the two sides of a condition. Scores are the bounds for that
state. An empty answer, a tie, or an error leaves the spot unset. Nothing
here puts a printed constant back. This module does not send.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Mapping

MODEL = "jev-1.13.0"
_LOCK = threading.Lock()
_CACHE: dict[str, dict[str, str | None]] = {}
_PACK_CACHE: dict[str, dict[str, Any]] = {}
_EXPIRY = ("seconds_from_clock", "seconds_until_cycle", "cycle_wait")
_CLOCK = _EXPIRY + ("as_of_utc", "ts", "prior_outcomes", "logged_at_utc", "writer_heartbeat_ts")
_DROPPED = ("denominator", "other", "DENOMINATOR", "OTHER")


def finite(value: Any) -> float | None:
    """A real number. A bool, a miss, or an infinity is unset."""

    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def whole(value: Any) -> int | None:
    """A returned count, when the score is a whole number. A fraction stays unset."""

    number = finite(value)
    if number is None:
        return None
    nearest = round(number)
    if nearest != number:
        return None
    return int(nearest)


def book_state(sleeve: str, symbol: str, **facts: Any) -> dict[str, Any]:
    """Named facts for one FX spot."""

    state: dict[str, Any] = {
        "book": "challenge",
        "namespace": "operator",
        "sleeve": sleeve,
        "symbol": symbol,
        "order_send": False,
    }
    state.update(facts)
    for key in _DROPPED:
        state.pop(key, None)
    return state


def q(side_a: str, text_a: str, side_b: str, text_b: str, instructions: str) -> dict[str, str]:
    return {
        "a": side_a,
        "a_text": text_a,
        "b": side_b,
        "b_text": text_b,
        "instructions": instructions,
    }


def _clock_seconds(now: Any) -> float:
    """Epoch seconds for the clock this remainder uses.

    A passed clock wins. During a cycle the cycle clock wins over a fresh
    wall read. Outside a cycle the wall is the clock.
    """

    if now is None:
        try:
            from src.components.ultimate_book.launcher_facts import cycle_clock

            stamped = cycle_clock()
        except Exception:
            stamped = None
        if stamped is not None:
            now = stamped
    if isinstance(now, datetime):
        stamp = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        try:
            return float(stamp.timestamp())
        except (OSError, OverflowError, ValueError):
            return time.time()
    if now is None:
        return time.time()
    return float(now)


def seconds_until_next_print(latest: Any, previous: Any, now: Any = None) -> float | None:
    """Seconds until the next bar of this spacing prints.

    The spacing is the gap between the last two bars. No gap leaves the
    deadline unset, and an unset deadline is not a timeout. The clock is
    the cycle's when one is running.
    """

    latest_s = _epoch(latest)
    previous_s = _epoch(previous)
    if latest_s is None or previous_s is None:
        return None
    period = latest_s - previous_s
    if period <= 0:
        return None
    clock = _clock_seconds(now)
    remain = period - (clock - latest_s)
    if remain <= 0:
        return None
    return remain


def _epoch(value: Any) -> float | None:
    if isinstance(value, datetime):
        stamp = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        try:
            return float(stamp.timestamp())
        except (OSError, OverflowError, ValueError):
            return None
    return finite(value)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int):
        return int(value)
    number = finite(value)
    if number is not None:
        return number
    item = getattr(value, "item", None)
    if callable(item):
        try:
            return _jsonable(item())
        except Exception:
            return str(value)
    return str(value)


def _deadline(state: Mapping[str, Any]) -> float | None:
    """The soonest expiry already on the state. None when the ask has no expiry."""

    found: list[float] = []
    nodes = [state]
    for key in ("facts", "account", "pair"):
        child = state.get(key)
        if isinstance(child, dict):
            nodes.append(child)
    for node in nodes:
        for key in _EXPIRY:
            number = finite(node.get(key))
            if number is not None and number > 0:
                found.append(number)
    if not found:
        return None
    return min(found)


def _digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _decision_facts(state: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in state.items() if key not in _CLOCK}


def continues(picks: Mapping[str, str | None], questions: Mapping[str, Mapping[str, str]]) -> bool:
    """True only when every question's continue side is the unique highest."""

    for qid, spec in questions.items():
        if picks.get(qid) != spec["a"]:
            return False
    return bool(questions)


def unique_sides(
    questions: Mapping[str, Mapping[str, str]],
    state: Mapping[str, Any],
    cache_key: str,
) -> dict[str, str | None]:
    """Ask each spot once for these facts.

    ``spec['a']`` is the continue side. ``spec['b']`` is the other side.
    The wait is the expiry on the state. No expiry means no timeout.
    A tie, an empty distribution, or a failed read is not a decision.
    """

    picks: dict[str, str | None] = {qid: None for qid in questions}
    receipt: dict[str, Any] = {
        "cached": False,
        "picks": picks,
        "probabilities": {},
        "error": None,
        "model": MODEL,
        "http_status": None,
    }
    unique_sides.receipt = receipt
    order: dict[str, tuple[str, str]] = {}
    payload_questions: dict[str, Any] = {}
    for qid, spec in questions.items():
        side_a = spec["a"]
        side_b = spec["b"]
        order[qid] = (side_a, side_b)
        payload_questions[qid] = {
            "type": "choice",
            "instructions": spec["instructions"],
            "criteria": {side_a: spec["a_text"], side_b: spec["b_text"]},
        }
    posted = _jsonable(dict(state))
    if not isinstance(posted, dict):
        receipt["error"] = "state"
        return picks
    for key in _DROPPED:
        posted.pop(key, None)
    posted["order_send"] = False
    token = _digest(
        {
            "cache_key": cache_key,
            "questions": payload_questions,
            "facts": _decision_facts(posted),
        }
    )
    with _LOCK:
        cached = _CACHE.get(token)
    if cached is not None:
        receipt["cached"] = True
        receipt["picks"] = dict(cached)
        unique_sides.receipt = receipt
        return dict(cached)
    try:
        from src.judgment.jev_client import API_URL, _consume_call, calls_enabled, resolve_key
        from src.judgment.jev_questions import unique_highest
    except Exception as exc:
        receipt["error"] = type(exc).__name__
        return picks
    if not calls_enabled():
        receipt["error"] = "calls_off"
        return picks
    try:
        _consume_call()
    except Exception:
        pass
    key, source = resolve_key()
    receipt["key_source"] = source
    if not key:
        receipt["error"] = "key_missing"
        return picks
    payload = {"state": posted, "model": MODEL, "questions": payload_questions}
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-fx-spot/1",
        },
    )
    wait = _deadline(posted)
    try:
        if wait is not None and wait > 0:
            handle = urllib.request.urlopen(req, timeout=wait)
        else:
            handle = urllib.request.urlopen(req)
        with handle as resp:
            body = json.loads(resp.read().decode("utf-8"))
            receipt["http_status"] = getattr(resp, "status", None)
    except urllib.error.HTTPError as exc:
        receipt["error"] = f"http_{exc.code}"
        receipt["http_status"] = exc.code
        return picks
    except Exception as exc:
        receipt["error"] = type(exc).__name__
        return picks
    if not isinstance(body, dict):
        receipt["error"] = "empty"
        return picks
    receipt["model"] = body.get("model") or MODEL
    answers = body.get("answers") if isinstance(body.get("answers"), dict) else {}
    probs_out: dict[str, Any] = {}
    decided = True
    for qid, names in order.items():
        answer = answers.get(qid) if isinstance(answers.get(qid), dict) else {}
        if answer.get("error") or answer.get("tie") is True:
            winner = None
        else:
            probs = answer.get("probabilities") if isinstance(answer.get("probabilities"), dict) else None
            try:
                winner = unique_highest(probs, names)
            except Exception:
                winner = None
        picks[qid] = winner
        if isinstance(answer.get("probabilities"), dict):
            probs_out[qid] = {str(name): answer.get("probabilities", {}).get(name) for name in names}
        if winner is None:
            decided = False
    receipt["probabilities"] = probs_out
    receipt["picks"] = dict(picks)
    if not decided:
        receipt["error"] = receipt["error"] or "no_unique_highest"
        return picks
    with _LOCK:
        _CACHE[token] = dict(picks)
    return picks


unique_sides.receipt = {}


def ask_pack(
    scores: Mapping[str, str],
    facts: Mapping[str, Any],
    *,
    choices: Mapping[str, Mapping[str, Any]] | None = None,
    bars: Any = None,
    index: int | None = None,
    bar_times: Any = None,
) -> dict[str, Any]:
    """One post for this state. Independent scores and choices travel together.

    The same facts return the remembered pack. The wait is the expiry already
    on the facts. A miss stays unset and does not restore a constant.
    """

    choice_map = dict(choices or {})
    clean = _jsonable(dict(facts))
    if not isinstance(clean, dict):
        clean = {}
    for key in _DROPPED:
        clean.pop(key, None)
    clean["order_send"] = False
    empty = {
        "scores": {str(qid): None for qid in scores},
        "sides": {str(qid): None for qid in choice_map},
        "asked": False,
        "posted": False,
        "error": None,
    }
    if not scores and not choice_map:
        empty["error"] = "empty"
        return empty
    try:
        from .spot_choice import anchors_for
    except Exception as exc:
        empty["error"] = type(exc).__name__
        return empty
    level_map = {
        str(qid): anchors_for(str(qid), clean, bars=bars, index=index, bar_times=bar_times)
        for qid in scores
    }
    token = _digest(
        {
            "scores": {str(qid): str(scores[qid]) for qid in sorted(scores)},
            "choices": {str(qid): choice_map[qid] for qid in sorted(choice_map)},
            "facts": _decision_facts(clean),
            "anchors": {qid: list(level_map[qid]) for qid in sorted(level_map)},
        }
    )
    with _LOCK:
        cached = _PACK_CACHE.get(token)
    if cached is not None:
        return {
            "scores": dict(cached["scores"]),
            "sides": dict(cached["sides"]),
            "asked": True,
            "posted": False,
            "error": cached.get("error"),
        }
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import spot_question, unique_highest
        from .spot_choice import amount_question, answered_amount, post_again
    except Exception as exc:
        empty["error"] = type(exc).__name__
        return empty
    questions: dict[str, Any] = {}
    try:
        for qid, text in scores.items():
            questions.update(amount_question(str(qid), str(text), level_map[str(qid)]))
        for qid, spec in choice_map.items():
            questions.update(
                spot_question(
                    str(qid),
                    str(spec.get("instructions", "")),
                    spec.get("criteria") if isinstance(spec.get("criteria"), dict) else {},
                )
            )
    except Exception as exc:
        empty["error"] = type(exc).__name__
        return empty
    def _once(posted: dict[str, Any]):
        return evaluate(clean, questions=posted, model=MODEL, merge_sleeve=False)

    def _rebuild() -> dict[str, Any]:
        built: dict[str, Any] = {}
        for qid, text in scores.items():
            built.update(amount_question(str(qid), str(text), level_map[str(qid)]))
        for qid, spec in choice_map.items():
            built.update(
                spot_question(
                    str(qid),
                    str(spec.get("instructions", "")),
                    spec.get("criteria") if isinstance(spec.get("criteria"), dict) else {},
                )
            )
        return built

    try:
        receipt = post_again(_once, questions, _rebuild)
    except Exception as exc:
        empty["error"] = type(exc).__name__
        return empty
    result = {
        "scores": {str(qid): None for qid in scores},
        "sides": {str(qid): None for qid in choice_map},
        "asked": True,
        "posted": True,
        "error": None,
    }
    if not isinstance(receipt, dict):
        result["error"] = "empty"
        _remember_pack(token, result)
        return result
    if receipt.get("skipped") or receipt.get("ok") is False or receipt.get("error"):
        result["error"] = str(receipt.get("error") or receipt.get("skipped") or "error")
        _remember_pack(token, result)
        return result
    answers = receipt.get("answers") if isinstance(receipt.get("answers"), dict) else {}
    for qid in scores:
        block = answers.get(str(qid))
        if isinstance(block, dict) and block.get("tie") is True:
            number = None
        else:
            try:
                number = answered_amount(str(qid), block, level_map.get(str(qid)))
            except Exception:
                number = None
        result["scores"][str(qid)] = finite(number)
    for qid, spec in choice_map.items():
        criteria = spec.get("criteria") if isinstance(spec.get("criteria"), dict) else {}
        names = tuple(str(name) for name in criteria)
        block = answers.get(str(qid))
        if not isinstance(block, dict) or block.get("error") or block.get("tie") is True:
            side = None
        else:
            probs = block.get("probabilities") if isinstance(block.get("probabilities"), dict) else None
            try:
                side = unique_highest(probs, names)
            except Exception:
                side = None
        result["sides"][str(qid)] = side if side in set(names) else None
    _remember_pack(token, result)
    return result


def _remember_pack(token: str, result: dict[str, Any]) -> None:
    with _LOCK:
        _PACK_CACHE[token] = {
            "scores": dict(result["scores"]),
            "sides": dict(result["sides"]),
            "error": result.get("error"),
        }
