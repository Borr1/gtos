"""Fire-path asks for Challenge 0.

Close, size-down, withhold, flatten, and trail are asks. The unique
highest probability wins. An empty answer, a tie, or an error does not
reduce and does not send, and it does not restore a constant.

This module does not send and does not flatten.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
MODEL = "jev-1.13.0"

_CACHE: dict[str, dict[str, Any]] = {}


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def unique_highest(probabilities: Mapping[str, Any] | None, order: tuple[str, ...]) -> str | None:
    """The option with the strictly highest probability. A tie is not a decision."""

    if not isinstance(probabilities, Mapping) or not probabilities:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    for name in order:
        if name not in probabilities:
            continue
        p = _number(probabilities.get(name))
        if p is None:
            continue
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if tied or best is None:
        return None
    return best


def _score_of(block: Any) -> float | None:
    if isinstance(block, (int, float)) and not isinstance(block, bool):
        return _number(block)
    if not isinstance(block, Mapping):
        return None
    for key in ("score", "value", "parameter"):
        if key in block:
            return _number(block.get(key))
    return None


def _probs_of(block: Any) -> dict[str, float]:
    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _number(val)
        if number is not None:
            out[str(key)] = number
    return out


def _with_priors(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """Priors ride on this same post. A miss leaves the history empty."""

    payload = dict(state)
    payload.pop("prior_outcomes", None)
    try:
        from src.judgment.jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = None
    payload["prior_outcomes"] = [] if loaded is None else loaded
    return payload


def _remember(state: Mapping[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
    try:
        from src.judgment.jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for spot, value, error in rows:
        try:
            append_outcome(spot, value, logged, error=error)
        except Exception:
            return


def _post(state: Mapping[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
    """One POST. A transport miss leaves answers empty. Never raises.

    No call budget and no calls-off switch. A missing key cannot post.
    The post has no timeout.
    """

    out: dict[str, Any] = {"answers": {}, "error": None, "model": MODEL, "state": dict(state)}
    try:
        from src.judgment.jev_client import API_URL, resolve_key
    except Exception as exc:  # noqa: BLE001
        out["error"] = type(exc).__name__
        return out
    key, _source = resolve_key()
    if not key:
        out["error"] = "key_missing"
        return out
    payload_state = _with_priors(state, questions)
    out["state"] = payload_state
    payload = {
        "state": payload_state,
        "model": MODEL,
        "questions": questions,
    }
    body = json.dumps(payload, default=str).encode("utf-8")
    try:
        import urllib.request

        req = urllib.request.Request(
            API_URL,
            data=body,
            method="POST",
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
                "User-Agent": "gtos-fire-path/1",
            },
        )
        with urllib.request.urlopen(req, timeout=None) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 — an error is not a constant
        out["error"] = type(exc).__name__
        return out
    answers = parsed.get("answers") if isinstance(parsed, dict) else None
    if isinstance(answers, dict):
        out["answers"] = answers
    reported = parsed.get("model") if isinstance(parsed, dict) else None
    if isinstance(reported, str) and reported.strip():
        out["model"] = reported
    return out


def _cached(key: str) -> dict[str, Any] | None:
    hit = _CACHE.get(key)
    return dict(hit) if isinstance(hit, dict) else None


def _store(key: str, row: Mapping[str, Any]) -> None:
    """A decided state is asked once. An empty answer, a tie, or an error is not stored."""

    if row.get("error") or row.get("unanswered"):
        return
    if row.get("choice") is None and row.get("alternative") is None and row.get("parameter") is None:
        return
    _CACHE[key] = dict(row)


def factor(spot: str, facts: Mapping[str, Any] | None = None) -> float | None:
    """The size multiplier when apply is the unique highest and a score came back.

    None leaves the base uncut. It does not restore a table, a haircut, or a floor.
    """

    state = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "spot": str(spot),
        "facts": dict(facts or {}),
    }
    key = "factor|" + str(spot) + "|" + json.dumps(state["facts"], sort_keys=True, default=str)
    hit = _cached(key)
    if hit is not None:
        return _number(hit.get("parameter"))
    q_apply = str(spot) + "_apply"
    q_score = str(spot) + "_parameter"
    questions = {
        q_apply: {
            "type": "choice",
            "instructions": (
                "A size reading is on this state. "
                "Apply a multiplier only when apply is the single highest probability. "
                "leave keeps the base. "
                "An empty answer or a tie does not shrink and does not restore a table. "
                "Do not close an open ticket."
            ),
            "criteria": {
                "apply": "Use the paired score as the multiplier on this state.",
                "leave": "Leave the base. Do not apply a multiplier.",
            },
        },
        q_score: {
            "type": "score",
            "instructions": (
                "The multiplier for this state. "
                "The score may sit between levels. "
                "An empty score does not restore a constant."
            ),
            "criteria": [
                "below the levels on this state",
                "between the levels on this state",
                "above the levels on this state",
            ],
        },
    }
    posted = _post(state, questions)
    answers = posted.get("answers") if isinstance(posted.get("answers"), dict) else {}
    choice = unique_highest(_probs_of(answers.get(q_apply)), ("apply", "leave"))
    score = _score_of(answers.get(q_score))
    parameter = score if choice == "apply" and score is not None else None
    error = posted.get("error") if choice is None else None
    if choice is None and error is None and not answers:
        error = "empty"
    row = {
        "choice": choice,
        "parameter": parameter,
        "error": error,
    }
    _remember(
        posted.get("state") if isinstance(posted.get("state"), dict) else state,
        [
            (q_apply, choice, "empty" if choice is None else None),
            (q_score, score, "empty" if score is None else None),
        ],
    )
    _store(key, row)
    return parameter


def place_wins(facts: Mapping[str, Any] | None = None) -> bool:
    """True only when place is the unique highest. An empty answer does not send."""

    state = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "facts": dict(facts or {}),
    }
    key = "place|" + json.dumps(state["facts"], sort_keys=True, default=str)
    hit = _cached(key)
    if hit is not None:
        return hit.get("choice") == "place"
    questions = {
        "fire_place": {
            "type": "choice",
            "instructions": (
                "This order is at the send. "
                "Place only when place is the single highest probability. "
                "stand does not send. "
                "An empty answer or a tie does not send and does not restore a refuse. "
                "Do not close an open ticket."
            ),
            "criteria": {
                "place": "Send this order.",
                "stand": "Do not send this order.",
            },
        }
    }
    posted = _post(state, questions)
    answers = posted.get("answers") if isinstance(posted.get("answers"), dict) else {}
    choice = unique_highest(_probs_of(answers.get("fire_place")), ("place", "stand"))
    error = posted.get("error") if choice is None else None
    if choice is None and error is None and not answers:
        error = "empty"
    row = {"choice": choice, "error": error}
    _remember(
        posted.get("state") if isinstance(posted.get("state"), dict) else state,
        [("fire_place", choice, "empty" if choice is None else None)],
    )
    _store(key, row)
    return choice == "place"


def fear_withholds(
    spot: str,
    state: Mapping[str, Any] | None,
    criteria: Mapping[str, str] | None,
    withhold_side: str,
    cache_key: str,
    instructions: str,
) -> dict[str, Any]:
    """Ask. blocks is true only when withhold_side is the unique highest.

    An empty answer, a tie, or an error does not withhold and does not send.
    """

    order = tuple(criteria or ())
    unanswered = {
        "alternative": None,
        "unanswered": True,
        "blocks": False,
        "error": None,
    }
    if not order or str(withhold_side) not in order:
        unanswered["error"] = "criteria_missing"
        fear_withholds.last = unanswered
        return unanswered
    facts = dict(state or {})
    key = "withhold|" + str(cache_key) + "|" + json.dumps(facts, sort_keys=True, default=str)
    hit = _cached(key)
    if hit is not None:
        fear_withholds.last = hit
        return dict(hit)
    questions = {
        str(spot): {
            "type": "choice",
            "instructions": str(instructions or ""),
            "criteria": {str(name): str(criteria[name]) for name in order},
        }
    }
    posted = _post(
        {
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "spot": str(spot),
            "facts": facts,
        },
        questions,
    )
    answers = posted.get("answers") if isinstance(posted.get("answers"), dict) else {}
    choice = unique_highest(_probs_of(answers.get(str(spot))), order)
    if choice is None:
        row = {
            "alternative": None,
            "unanswered": True,
            "blocks": False,
            "error": posted.get("error") or "empty",
        }
    else:
        row = {
            "alternative": choice,
            "unanswered": False,
            "blocks": choice == str(withhold_side),
            "error": None,
        }
    _remember(
        posted.get("state") if isinstance(posted.get("state"), dict) else facts,
        [(str(spot), choice, "empty" if choice is None else None)],
    )
    _store(key, row)
    fear_withholds.last = row
    return dict(row)


def close(facts: Mapping[str, Any] | None = None) -> bool:
    """True only when close is the unique highest.

    An empty answer, a tie, or an error does not close. This function
    does not flatten and does not send.
    """

    state = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "facts": dict(facts or {}),
    }
    key = "close|" + json.dumps(state["facts"], sort_keys=True, default=str)
    hit = _cached(key)
    if hit is not None:
        return hit.get("choice") == "close"
    questions = {
        "fire_close": {
            "type": "choice",
            "instructions": (
                "An open ticket is on this state. "
                "Close only when close is the single highest probability. "
                "hold leaves the ticket open. "
                "An empty answer or a tie does not close and does not restore a flatten. "
                "Do not send an order."
            ),
            "criteria": {
                "close": "Close this ticket.",
                "hold": "Leave this ticket open.",
            },
        }
    }
    posted = _post(state, questions)
    answers = posted.get("answers") if isinstance(posted.get("answers"), dict) else {}
    choice = unique_highest(_probs_of(answers.get("fire_close")), ("close", "hold"))
    error = posted.get("error") if choice is None else None
    if choice is None and error is None and not answers:
        error = "empty"
    row = {"choice": choice, "error": error}
    _remember(
        posted.get("state") if isinstance(posted.get("state"), dict) else state,
        [("fire_close", choice, "empty" if choice is None else None)],
    )
    _store(key, row)
    return choice == "close"


def size_down(spot: str, facts: Mapping[str, Any] | None = None) -> float | None:
    """The multiplier when size_down is the unique highest and a score came back.

    None does not shrink and does not restore a haircut. The score is not floored.
    """

    state = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "spot": str(spot),
        "facts": dict(facts or {}),
    }
    key = "size_down|" + str(spot) + "|" + json.dumps(state["facts"], sort_keys=True, default=str)
    hit = _cached(key)
    if hit is not None:
        return _number(hit.get("parameter"))
    q_side = str(spot) + "_size_down"
    q_score = str(spot) + "_size_down_parameter"
    questions = {
        q_side: {
            "type": "choice",
            "instructions": (
                "A size reading is on this state. "
                "Size down only when size_down is the single highest probability. "
                "leave keeps the base. "
                "An empty answer or a tie does not shrink and does not restore a haircut. "
                "Do not close an open ticket."
            ),
            "criteria": {
                "size_down": "Use the paired score as the size-down multiplier on this state.",
                "leave": "Leave the base. Do not size down.",
            },
        },
        q_score: {
            "type": "score",
            "instructions": (
                "The size-down multiplier for this state. "
                "The score may sit between levels. "
                "An empty score does not restore a constant."
            ),
            "criteria": [
                "below the levels on this state",
                "between the levels on this state",
                "above the levels on this state",
            ],
        },
    }
    posted = _post(state, questions)
    answers = posted.get("answers") if isinstance(posted.get("answers"), dict) else {}
    choice = unique_highest(_probs_of(answers.get(q_side)), ("size_down", "leave"))
    score = _score_of(answers.get(q_score))
    parameter = score if choice == "size_down" and score is not None else None
    error = posted.get("error") if choice is None else None
    if choice is None and error is None and not answers:
        error = "empty"
    row = {"choice": choice, "parameter": parameter, "error": error}
    _remember(
        posted.get("state") if isinstance(posted.get("state"), dict) else state,
        [
            (q_side, choice, "empty" if choice is None else None),
            (q_score, score, "empty" if score is None else None),
        ],
    )
    _store(key, row)
    return parameter


fear_withholds.last = None  # type: ignore[attr-defined]
