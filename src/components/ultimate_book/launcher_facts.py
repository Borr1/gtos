"""Launcher flags are facts on the ask. The cycle wait is the score for that state.

An empty answer, a tie, or an error does not copy an argv number back.
The wait falls back to the last wait this process received, or to the spine number.
"""

from __future__ import annotations

import sys

_RETURNED: dict[str, float] = {}

_QUESTIONS: tuple[tuple[str, str], ...] = (
    (
        "cycle_wait",
        "The score you return is how many seconds this writer waits before the next cycle. "
        "The launcher flags on this card are facts from argv. They are not the wait. "
        "An empty score leaves the wait unset. "
        "A tie leaves the wait unset. "
        "An error leaves the wait unset. "
        "This question does not send.",
    ),
    (
        "transient_retry_cap",
        "The score you return is how many same-class placement failures this bar may attempt. "
        "The argv retry flag on this card is a fact. It is not the cap. "
        "An empty score leaves the cap unset. "
        "A tie leaves the cap unset. "
        "An error leaves the cap unset. "
        "This question does not send.",
    ),
    (
        "friday_cutoff_minute",
        "The score you return is the minute of the UTC day for the Friday new-risk clock. "
        "0 is 00:00 UTC. The argv clock on this card is a fact. It is not this clock. "
        "An empty score leaves the clock unset. "
        "A tie leaves the clock unset. "
        "An error leaves the clock unset. "
        "This question does not flatten.",
    ),
    (
        "weekend_flat_minute",
        "The score you return is the minute of the UTC day for the weekend-flat clock. "
        "0 is 00:00 UTC. The argv clock on this card is a fact. It is not this clock. "
        "An empty score leaves the clock unset. "
        "A tie leaves the clock unset. "
        "An error leaves the clock unset. "
        "This question does not flatten.",
    ),
)


def _flag(name: str) -> str | None:
    argv = [str(arg) for arg in sys.argv]
    if name in argv:
        index = argv.index(name)
        if index + 1 < len(argv):
            return argv[index + 1]
    prefix = name + "="
    for arg in argv:
        if arg.startswith(prefix):
            return arg[len(prefix):]
    return None


def launcher_facts() -> dict[str, str]:
    """The process flags, when the launcher passed them. Absent when it did not."""

    named = {
        "launcher_f5_minimal_size_usd": "--f5-minimal-size-usd",
        "launcher_notional_initial_usd": "--f5-notional-initial-usd",
        "launcher_transient_retry_cap": "--transient-retry-cap",
        "launcher_poll_seconds": "--poll-seconds",
        "launcher_friday_cutoff_utc": "--f5-friday-new-risk-cutoff-utc",
        "launcher_weekend_flat_utc": "--f5-weekend-flat-utc",
    }
    out: dict[str, str] = {}
    for key, flag in named.items():
        value = _flag(flag)
        if value not in (None, ""):
            out[key] = value
    return out


def _finite(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
    else:
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def clock_from_minutes(number: object) -> tuple[int, int] | None:
    """A returned minute-of-day as HH:MM. Anything else is unset."""

    value = _finite(number)
    if value is None or value < 0:
        return None
    whole = int(value)
    if whole != value:
        return None
    hour, minute = divmod(whole, 60)
    if hour > 23:
        return None
    return hour, minute


def _score_block(block: object) -> float | None:
    if not isinstance(block, dict) or block.get("error") or block.get("tie") is True:
        return None
    probabilities = block.get("probabilities")
    if isinstance(probabilities, dict) and probabilities:
        try:
            from src.judgment.jev_questions import unique_highest

            if unique_highest(probabilities) is None:
                return None
        except Exception:
            return None
    if "score" in block:
        if block.get("score") is None:
            return None
        return _finite(block.get("score"))
    if "value" in block:
        if block.get("value") is None:
            return None
        return _finite(block.get("value"))
    return None


def _card() -> dict[str, object]:
    facts = launcher_facts()
    payload: dict[str, object] = {"launcher_facts": dict(facts)}
    try:
        from src.judgment.nineteen import quantity_state

        built = quantity_state(payload)
        if isinstance(built, dict):
            payload = built
    except Exception:
        pass
    payload.update(facts)
    namespace = _flag("--namespace")
    if namespace:
        payload["namespace"] = namespace
    profile = _flag("--profile")
    if profile:
        payload["profile"] = profile
    for key, value in _RETURNED.items():
        payload["returned_" + key] = value
    return payload


def _post(state: dict[str, object], questions: dict[str, object]) -> object:
    from src.judgment.jev_client import evaluate

    return evaluate(
        state,
        questions=dict(questions),
        merge_sleeve=False,
        include_depth="full",
    )


def _accept(qid: str, number: float) -> None:
    if qid in ("cycle_wait", "transient_retry_cap"):
        if number < 0:
            return
        _RETURNED[qid] = float(number)
        return
    if qid in ("friday_cutoff_minute", "weekend_flat_minute"):
        if clock_from_minutes(number) is None:
            return
        _RETURNED[qid] = float(number)


def _ask() -> None:
    questions = {
        qid: {"type": "score", "instructions": text}
        for qid, text in _QUESTIONS
    }
    try:
        receipt = _post(_card(), questions)
    except Exception:
        return
    if not isinstance(receipt, dict):
        return
    if (
        receipt.get("ok") is False
        or receipt.get("error")
        or receipt.get("skipped")
        or receipt.get("tie") is True
    ):
        return
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        return
    for qid, _text in _QUESTIONS:
        number = _score_block(answers.get(qid))
        if number is None:
            continue
        _accept(qid, number)


def _spine_seconds() -> float:
    try:
        from src.judgment.nineteen import DENOMINATOR

        number = float(DENOMINATOR)
    except Exception:
        number = 19.0
    if number < 0:
        return 19.0
    return number


def launcher_return(name: str) -> float | None:
    """The last score this process accepted for that launcher question."""

    number = _RETURNED.get(str(name))
    if number is None:
        return None
    return float(number)


def next_cycle_wait() -> float:
    """Seconds before the next cycle. Empty, tie, and error do not restore the poll flag."""

    try:
        _ask()
    except Exception:
        pass
    number = _RETURNED.get("cycle_wait")
    if number is not None and number >= 0:
        return float(number)
    return _spine_seconds()
