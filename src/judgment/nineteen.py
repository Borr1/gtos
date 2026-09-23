"""Computer-fact spine.

The named bindings below are the only planted decision integers.
Simple counts run over sequences the caller already holds.
Residues, digit folds, letter totals, and checksums are computed.
A trading quantity is the score returned for that state.
An empty answer, a tie, or an error does not restore a number.
This module does not draw a random number and does not send an order.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

DENOMINATOR = 19
OTHER = 11

ROLES = (
    "stop",
    "target",
    "atr_multiple",
    "bar_count",
    "cash",
    "loop_bound",
    "size",
)

SCHEMA = "gtos.judgment.nineteen_import.v1"
_NAMESPACE = "operator"
_BLOCKED = ("redacted_account", "redacted_account", "redacted_account", "redacted_account", "run_book_supervisor")
_DROP = ("denominator", "other")

_SURFACE = (
    "The entry is a limit order. "
    "Gold, silver, platinum, and each metal named on this state stay on the surface. "
    "Cost and spread are not a reason to leave the score empty. "
    "An empty score leaves this quantity unset. "
    "A tie leaves this quantity unset. "
    "An error leaves this quantity unset."
)

_ROLE_LEAD = {
    "stop": "The score you return is the stop distance for this state. ",
    "target": "The score you return is the target distance for this state. ",
    "atr_multiple": "The score you return is the ATR multiple for this state. ",
    "bar_count": "The score you return is the bar count for this state. ",
    "cash": "The score you return is the cash amount for this state. ",
    "loop_bound": "The score you return is the loop bound for this state. ",
    "size": "The score you return is the size for this state. ",
}


def _card(state: Mapping[str, Any] | None) -> dict[str, Any]:
    """Facts for an ask. The two constants are not fields on the card."""

    payload = dict(state or {})
    for key in _DROP:
        payload.pop(key, None)
    return payload


def _finite(value: Any) -> float | None:
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
    if number != number:
        return None
    if number in (float("inf"), float("-inf")):
        return None
    return number


def length(seq: Any) -> int | None:
    """How many items the caller already holds."""

    try:
        return len(seq)
    except TypeError:
        return None


def total(seq: Any) -> float | None:
    """Sum of a sequence the caller already holds."""

    if isinstance(seq, (str, bytes)):
        return None
    try:
        items = list(seq)
    except TypeError:
        return None
    numbers: list[float] = []
    for item in items:
        number = _finite(item)
        if number is None:
            return None
        numbers.append(number)
    return sum(numbers)


def quantity_questions(role: str, instructions: str | None = None) -> dict[str, Any] | None:
    if instructions is not None:
        return {str(role): {"type": "score", "instructions": str(instructions)}}
    if role not in ROLES:
        return None
    text = _ROLE_LEAD[role] + _SURFACE
    built: dict[str, Any] | None
    try:
        from .jev_questions import parameter_question

        built = parameter_question(role, text)
    except Exception:
        built = None
    block = built.get(role) if isinstance(built, dict) else None
    if not isinstance(block, dict):
        block = {"type": "score", "instructions": text}
    else:
        block = dict(block)
        block["type"] = "score"
        block["instructions"] = text
    return {role: block}


def quantity_state(role: Any, state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Facts for a quantity ask. The card does not carry the two constants."""

    if state is None and isinstance(role, Mapping):
        return _card(role)
    payload = _card(state)
    payload["role"] = role
    if "order_kind" not in payload:
        payload["order_kind"] = "limit"
    if "metals" not in payload:
        payload["metals"] = "gold, silver, platinum, and each metal named on this state"
    return payload


def quantity(
    role: Any,
    state: Mapping[str, Any] | None = None,
    ask: Any = None,
    *,
    question_id: str | None = None,
    instructions: str | None = None,
    record: bool = False,
) -> float | None:
    """Score for this role, or for an explicit question. Empty, tie, and error return no number."""

    if question_id is not None:
        base = role if isinstance(role, Mapping) or role is None else state
        text = "" if instructions is None else instructions
        return score(
            quantity_state(base),
            question_id=question_id,
            instructions=text,
            ask=ask,
        )
    if role not in ROLES or not isinstance(state, Mapping):
        return None
    questions = quantity_questions(role)
    if not isinstance(questions, dict):
        return None
    payload = quantity_state(role, state)
    number = _accepted_number(_post(payload, questions, ask), role)
    if record:
        _record(role, number, payload)
    return number


def score(
    state: Mapping[str, Any] | None,
    *,
    question_id: str,
    instructions: str,
    ask: Any = None,
) -> float | None:
    """One score hop. Empty, tie, and error return no number."""

    payload = _card(state)
    key = str(question_id)
    questions = {key: {"type": "score", "instructions": str(instructions)}}
    return _accepted_number(_post(payload, questions, ask), key)


def _post(state: dict[str, Any], questions: Mapping[str, Any], ask: Any) -> Any:
    state = _card(state)
    call = ask
    if call is None:
        try:
            from .jev_client import evaluate as call
        except Exception:
            return None
    try:
        return call(state, questions=dict(questions), merge_sleeve=False)
    except Exception:
        return None


def _accepted_number(receipt: Any, role: str) -> float | None:
    if not isinstance(receipt, dict):
        return None
    if receipt.get("ok") is False or receipt.get("error") or receipt.get("skipped"):
        return None
    if receipt.get("tie") is True:
        return None
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or role not in answers:
        return None
    return _number_from_block(answers.get(role))


def _number_from_block(block: Any) -> float | None:
    if not isinstance(block, dict) or block.get("error") or block.get("tie") is True:
        return None
    probabilities = block.get("probabilities")
    if isinstance(probabilities, dict) and probabilities:
        try:
            from .jev_questions import unique_highest

            winner = unique_highest(probabilities)
        except Exception:
            return None
        if winner is None:
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


def _record(role: str, number: float | None, state: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import append_outcome

        append_outcome(role, number, state, error=None if number is not None else "unset")
    except Exception:
        return


def _challenge_writer() -> bool:
    argv = " ".join(sys.argv).replace("\\", "/").lower()
    if "run_book" not in argv:
        return False
    if any(token in argv for token in _BLOCKED):
        return False
    return _NAMESPACE in argv


def _repo_root() -> Path:
    judgment = Path(__file__).resolve().parent
    src = judgment.parent
    return src.parent


def file_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def stamp_path() -> Path:
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / _NAMESPACE
        / "judgment"
        / "nineteen_import_stamp.json"
    )


def write_import_stamp() -> dict[str, Any] | None:
    """Record that this process imported the spine. Friends and tests do not write."""

    if not _challenge_writer():
        return None
    payload = {
        "schema": SCHEMA,
        "pid": os.getpid(),
        "loaded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": file_sha256(),
        "namespace": _NAMESPACE,
        "module": "src.judgment.nineteen",
    }
    path = stamp_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        pid_path = path.with_name("nineteen_import_stamp." + str(os.getpid()) + ".json")
        pid_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        return payload
    return payload


write_import_stamp()


def _boot_writer_modules() -> None:
    """The Challenge writer that imports the spine writes the loader stamp."""

    if not _challenge_writer():
        return
    try:
        from .unique_loader import load_unique_apply
    except Exception:
        return
    try:
        load_unique_apply()
    except Exception:
        return


_boot_writer_modules()
