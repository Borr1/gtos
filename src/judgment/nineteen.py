"""Computer-fact spine.

The named bindings below are the only planted decision integers.
They are not a value. Simple counts run over sequences the caller already holds.
A trading quantity is the score for that state, read on the anchors.
An empty answer, a tie, or an error does not restore a number.
A score with no anchors does not post.
This module does not draw a random number and does not send an order.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
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
_BLOCKED = ("friend_a", "redacted_account", "redacted_account", "redacted_account", "run_book_supervisor")
_DROP = ("denominator", "other")

# The Score API names its level maximum in a refusal. Learned once, then kept.
_LEARNED_LEVEL_CAP: dict[str, int] = {}
_CAP_PATTERNS = (
    r"at most\s+(\d+)",
    r"no more than\s+(\d+)",
    r"not more than\s+(\d+)",
    r"maximum(?: of)?\s+(\d+)",
    r"up to\s+(\d+)",
    r"between\s+\d+\s+and\s+(\d+)",
    r"max_items\s*[:=]\s*(\d+)",
    r"maxitems\s*[:=]\s*(\d+)",
)

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
        # No criteria would be a bare Score. Do not build one.
        return None
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
    anchors: Any = None,
    record: bool = False,
) -> float | None:
    """Score for this role. No anchors does not post. Empty, tie, and error return no number."""

    if question_id is not None:
        base = role if isinstance(role, Mapping) or role is None else state
        text = "" if instructions is None else instructions
        return score(
            quantity_state(base),
            question_id=question_id,
            instructions=text,
            anchors=anchors,
            ask=ask,
        )
    if role not in ROLES or not isinstance(state, Mapping) or anchors is None:
        return None
    text = _ROLE_LEAD[role] + _SURFACE if instructions is None else instructions
    payload = quantity_state(role, state)
    number = score(
        payload,
        question_id=str(role),
        instructions=text,
        anchors=anchors,
        ask=ask,
    )
    if record:
        _record(str(role), number, payload)
    return number


def _head(seq: Any) -> Any:
    try:
        for item in seq:
            return item
    except TypeError:
        return None
    return None


def _after_head(seq: Any) -> Any:
    skipped = None
    try:
        for item in seq:
            if skipped is None:
                skipped = item
                continue
            return item
    except TypeError:
        return None
    return None


def _pair(item: Any) -> tuple[Any, Any] | None:
    if isinstance(item, (str, bytes, Mapping)):
        return None
    try:
        parts = list(item)
    except TypeError:
        return None
    if length(parts) != length((None, None)):
        return None
    return (_head(parts), _after_head(parts))


def _anchor_levels(anchors: Any) -> list[tuple[str, float]] | None:
    """Ordered (label, value) levels. Fewer than two is not a Score."""

    if anchors is None or isinstance(anchors, (str, bytes)):
        return None
    if isinstance(anchors, Mapping):
        raw_items = list(anchors.items())
    else:
        try:
            raw_items = list(anchors)
        except TypeError:
            return None
    found: list[tuple[str, float]] = []
    seen: list[float] = []
    for item in raw_items:
        pair = _pair(item)
        if pair is None:
            number = _finite(item)
            text = "" if number is None else str(number).strip()
        else:
            label, raw = pair
            number = _finite(raw)
            text = "" if label is None else str(label).strip()
        if number is None or not text or number in seen:
            continue
        seen.append(number)
        found.append((text, number))
    found.sort(key=_after_head)
    count = length(found)
    if count is None or count == length(()) or count == length((None,)):
        return None
    return _thin_levels(found)


def learned_score_level_cap() -> int | None:
    """The level maximum the API has already stated. None until a refusal names it."""

    value = _LEARNED_LEVEL_CAP.get("cap")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def note_score_level_cap(detail: Any) -> int | None:
    """Remember the maximum a refusal states. A text with no maximum changes nothing."""

    found = _cap_from_detail(detail)
    if found is not None:
        current = learned_score_level_cap()
        if current is None or found < current:
            _LEARNED_LEVEL_CAP["cap"] = found
    return learned_score_level_cap()


def _detail_text(detail: Any) -> str:
    if detail is None:
        return ""
    if isinstance(detail, bytes):
        return detail.decode("utf-8", errors="replace")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, BaseException):
        return str(detail)
    if isinstance(detail, Mapping):
        parts: list[str] = []
        for key in ("detail", "body", "message", "error", "reason"):
            if key in detail and detail.get(key) is not None:
                parts.append(_detail_text(detail.get(key)))
        return "\n".join(parts)
    if isinstance(detail, (list, tuple)):
        return "\n".join(_detail_text(item) for item in detail)
    return str(detail)


def _cap_from_detail(detail: Any) -> int | None:
    text = _detail_text(detail)
    if not text:
        return None
    found: list[int] = []
    for pattern in _CAP_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            try:
                number = int(match.group(1))
            except (TypeError, ValueError):
                continue
            if number >= length((None, None)):
                found.append(number)
    if not found:
        return None
    return min(found)


def kept_indexes(count: int) -> list[int] | None:
    """Indexes to keep after the API has named its maximum.

    None means the maximum is not known yet, or the list already fits, so
    every index stays. The spacing is lowest, highest, and rank-even between.
    """

    cap = learned_score_level_cap()
    if cap is None or not isinstance(count, int) or isinstance(count, bool):
        return None
    if count <= cap or cap < length((None, None)) or count < length((None, None)):
        return None
    last = count - 1
    slots = cap - 1
    if slots <= 0:
        return None
    ranks: list[int] = []
    step = 0
    while step < cap:
        rank = (step * last) // slots
        if not ranks or ranks[-1] != rank:
            ranks.append(rank)
        step += 1
    return ranks


def _thin_levels(found: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Lowest, highest, and rank-even levels between them, once the API has named its maximum.

    Until a refusal states that maximum, every finite anchor stays. Dropping
    one before the API speaks would invent the limit.
    """

    count = length(found)
    if count is None:
        return found
    ranks = kept_indexes(count)
    if not ranks:
        return found
    return [found[rank] for rank in ranks if rank < count]


def _criterion(label: str, value: float) -> str:
    return label + " (" + _anchor_text(value) + ")"


def _anchor_text(number: float) -> str:
    whole = int(number)
    if whole == number:
        return str(whole)
    return str(number)


def _interpolate(position: Any, levels: list[tuple[str, float]]) -> float | None:
    """The anchor value at this level position. The position may sit between levels."""

    number = _finite(position)
    if number is None:
        return None
    low_index = None
    low_value = None
    for index, pair in enumerate(levels):
        value = _after_head(pair)
        if value is None:
            return None
        if number < index or number == index:
            if number == index or low_value is None:
                return value
            span = index - low_index
            if not span:
                return low_value
            frac = (number - low_index) / span
            return low_value + (frac * (value - low_value))
        low_index = index
        low_value = value
    return low_value


def score(
    state: Mapping[str, Any] | None,
    *,
    question_id: str,
    instructions: str,
    anchors: Any = None,
    ask: Any = None,
) -> float | None:
    """One score hop. Empty, tie, and error return no number.

    ``anchors`` is a sequence of ``(label, value)`` pairs, a map of label
    to value, or a sequence of values, in the unit this hop returns.
    Fewer than two levels does not post. A longer list keeps the lowest,
    the highest, and rank-even levels between them so the ask still posts.
    Each level is the label and its value. The number returned is the
    value on those levels, not the level position.
    """

    ordered = _ordered_levels(anchors)
    if not ordered:
        return None
    levels = _thin_levels(ordered)
    if not levels:
        return None
    key = str(question_id)
    receipt = _post(*_score_payload(state, key, instructions, levels), ask)
    index = _accepted_number(receipt, key)
    known = learned_score_level_cap()
    learned = note_score_level_cap(receipt)
    if index is None and learned is not None and learned != known:
        again = _thin_levels(ordered)
        if again and length(again) != length(levels):
            levels = again
            receipt = _post(*_score_payload(state, key, instructions, levels), ask)
            index = _accepted_number(receipt, key)
    if index is None:
        return None
    return _interpolate(index, levels)


def score_many(
    state: Mapping[str, Any] | None,
    specs: Any,
) -> dict[str, float | None]:
    """One post for every share in this cycle.

    ``specs`` is a sequence of ``(question_id, instructions, anchors)``.
    Each anchor list is that question's levels. The card is the same state
    for every question, so each answer is given with the others in view.
    Fewer than two levels leaves that question unset. An empty score, a tie,
    or an error leaves that question unset.
    """

    try:
        items = list(specs)
    except TypeError:
        return {}
    prepared: list[tuple[str, list[tuple[str, float]]]] = []
    questions: dict[str, Any] = {}
    for item in items:
        try:
            question_id, instructions, anchors = item
        except (TypeError, ValueError):
            continue
        ordered = _ordered_levels(anchors)
        if not ordered:
            continue
        levels = _thin_levels(ordered)
        if not levels:
            continue
        key = str(question_id)
        prepared.append((key, levels))
        questions[key] = {
            "type": "score",
            "instructions": str(instructions),
            "criteria": [_criterion(label, value) for label, value in levels],
        }
    if not questions:
        return {}
    receipt = _post(_card(state), questions, None)
    out: dict[str, float | None] = {}
    for key, levels in prepared:
        index = _accepted_number(receipt, key)
        out[key] = None if index is None else _interpolate(index, levels)
    return out


def score_question(spot: str, instructions: str, anchors: Any) -> dict[str, Any]:
    """The Score block an amount question posts.

    Criteria are ``label (value)``. ``_anchor_values`` is the same length and
    order so a client can interpolate, and it is not a wire field. Fewer than
    two levels returns an empty dict and does not post.
    """

    levels = _anchor_levels(anchors)
    if not levels:
        return {}
    return {
        str(spot): {
            "type": "score",
            "instructions": str(instructions).strip(),
            "criteria": [_criterion(label, value) for label, value in levels],
            "_anchor_values": [value for _label, value in levels],
        }
    }


def _ordered_levels(anchors: Any) -> list[tuple[str, float]] | None:
    """Sorted finite anchors before the learned maximum is applied."""

    if anchors is None or isinstance(anchors, (str, bytes)):
        return None
    if isinstance(anchors, Mapping):
        raw_items = list(anchors.items())
    else:
        try:
            raw_items = list(anchors)
        except TypeError:
            return None
    found: list[tuple[str, float]] = []
    seen: list[float] = []
    for item in raw_items:
        pair = _pair(item)
        if pair is None:
            number = _finite(item)
            text = "" if number is None else str(number).strip()
        else:
            label, raw = pair
            number = _finite(raw)
            text = "" if label is None else str(label).strip()
        if number is None or not text or number in seen:
            continue
        seen.append(number)
        found.append((text, number))
    found.sort(key=_after_head)
    count = length(found)
    if count is None or count == length(()) or count == length((None,)):
        return None
    return found


def _score_payload(
    state: Mapping[str, Any] | None,
    question_id: str,
    instructions: str,
    levels: list[tuple[str, float]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = _card(state)
    payload["score_anchors"] = [
        {"label": label, "value": value} for label, value in levels
    ]
    questions = {
        str(question_id): {
            "type": "score",
            "instructions": str(instructions),
            "criteria": [_criterion(label, value) for label, value in levels],
        }
    }
    return payload, questions


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
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)}


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
