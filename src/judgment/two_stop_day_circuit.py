"""2-stop same-symbol/sleeve day circuit. Dig B KEEP refuse-remint.

The closed[] same-sleeve orig-stop count stays the integer
``same_sleeve_orig_stop_count_session_day`` reads. The measured same-day
rest sum stays that read. ``wmb_2stop_day_circuit_same_symbol_sleeve_orig_stops``
is that integer.

Every decision on this circuit, including every parameter, is the System
One return for this state. One hop: ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False``. That call POSTs
https://api.typesafe.ai/v1/systemone. Questions are only Noul, Choice, or
Score. Prior outcomes are attached on the ask, and the return is stored
for the next ask.

A Choice is the unique highest probability. A Score is the returned
number and may sit between levels. A Noul is a bool or a probability.
An empty answer, a tie, a missing score, or an error leaves that return
unset. A floor and a baseline are not a question.

This module reads closed[] through ``two_stop.py``. It does not remint,
place, flatten, or send. Judge code stays unable to send.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .two_stop import (
    MappingLike,
    _is_orig_stop,
    _parse_utc,
    _row_day,
    _sleeve,
    closed_rows,
    same_sleeve_orig_stop_count_session_day,
)

MODEL = "jev-1.13.0"
CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
CHALLENGE_MAGIC = 0

_CIRCUIT_ORDER = ("refuse_remint", "circuit_open")
_REASON_ORDER = (
    "wmb_2stop_day_circuit_same_symbol_sleeve_orig_stops",
    "orig_stops_at_cap",
    "same_day_rest_sum_r_strongly_negative",
    "circuit_open",
)
_VERDICT_ORDER = ("APPLY_CONSUME", "circuit_open")
_KIND_ORDER = ("KEEP_REFUSE_REMINT", "circuit_open")
_NOUL_ORDER = ("true", "false")

_CIRCUIT_CRITERIA = {
    "refuse_remint": "This circuit refuses a remint.",
    "circuit_open": "This circuit is open.",
}
_REASON_CRITERIA = {
    "wmb_2stop_day_circuit_same_symbol_sleeve_orig_stops": (
        "The reason is the same-sleeve orig-stop day keep."
    ),
    "orig_stops_at_cap": "The reason is orig stops at the cap.",
    "same_day_rest_sum_r_strongly_negative": (
        "The reason is a strongly negative same-day rest sum."
    ),
    "circuit_open": "The reason is that the circuit is open.",
}
_VERDICT_CRITERIA = {
    "APPLY_CONSUME": "The verdict on this state is apply consume.",
    "circuit_open": "The verdict on this state is circuit open.",
}
_KIND_CRITERIA = {
    "KEEP_REFUSE_REMINT": "The consume kind is keep refuse remint.",
    "circuit_open": "The consume kind is circuit open.",
}

_LIMIT_KEYS = frozenset(
    {
        "floor",
        "baseline",
        "day_start_baseline",
        "static_floor",
        "pass_line",
        "flatten_floor_usd",
        "daily_loss_pct",
        "floor_room",
    }
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
_ALLOWED_TYPES = frozenset({"noul", "choice", "score"})

# History only when jev_questions cannot be imported. Not copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


@dataclass(frozen=True)
class TwoStopCircuitStamp:
    """KEEP refuse-remint. Never a broker send."""

    refuse_remint: bool | float | None
    reason: str | None
    verdict: str | None
    orig_stops: int | None
    rest_sum_r: float | None
    rest_sum_r_strongly_negative: bool | float | None
    notes: tuple[str, ...]
    circuit: str | None = None
    circuit_probabilities: tuple[tuple[str, float], ...] = ()
    exhausted: bool | float | None = None
    cap: float | None = None
    rest_line: float | None = None
    kind: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "refuse_remint": self.refuse_remint,
            "reason": self.reason,
            "verdict": self.verdict,
            "orig_stops": self.orig_stops,
            "rest_sum_r": self.rest_sum_r,
            "rest_sum_r_strongly_negative": self.rest_sum_r_strongly_negative,
            "notes": list(self.notes),
            "circuit": self.circuit,
            "circuit_probabilities": dict(self.circuit_probabilities),
            "exhausted": self.exhausted,
            "cap": self.cap,
            "rest_line": self.rest_line,
            "kind": self.kind,
            "error": self.error,
            "model": MODEL,
            "place": False,
            "never_remint": True,
            "never_broker_send": True,
        }


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    lowered = cleaned.lower()
    kept: list[str] = []
    index = 0
    while index < len(cleaned):
        if lowered.startswith("baseline", index):
            index += len("baseline")
            continue
        if lowered.startswith("floor", index):
            index += len("floor")
            continue
        kept.append(cleaned[index])
        index += 1
    return "".join(kept)


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before the ask."""

    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, list):
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


def _row_r(row: Mapping[str, Any]) -> float | None:
    for key in ("rest_r", "sum_r", "r", "r_multiple", "realized_r"):
        raw = row.get(key)
        if raw is None:
            continue
        number = _finite(raw)
        if number is not None:
            return number
    return None


def same_day_rest_sum_r(
    doc: MappingLike | None,
    *,
    sleeve: str,
    session_day: str,
    symbol: str | None = None,
) -> float | None:
    """Sum rest R for same sleeve (+ optional symbol) orig_stops on session_day."""

    if not doc:
        return None
    want = sleeve[3:] if sleeve.startswith("F5:") else sleeve
    total = 0.0
    seen = 0
    for row in closed_rows(doc):
        if not _is_orig_stop(row):
            continue
        if _sleeve(row) != want:
            continue
        if _row_day(row) != session_day:
            continue
        if symbol and str(row.get("symbol") or "") and str(row.get("symbol")) != symbol:
            continue
        value = _row_r(row)
        if value is None:
            continue
        total += value
        seen += 1
    return total if seen else None


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A missing probability is not zero. A tie is not a decision."""

    if not probs:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    allowed = order or tuple(probs)
    for name in allowed:
        if name not in probs:
            continue
        p = probs[name]
        if best_p is None or p > best_p + 1e-12:
            best = name
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if tied or best is None:
        return None
    return best


def _choice_of(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
    """The choice is the unique highest probability. A bare label is not a choice."""

    probs = _probs(block)
    kept = {name: probs[name] for name in order if name in probs}
    if not isinstance(block, dict) or block.get("error"):
        return None, kept
    choice: str | None = None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probs or None, order)
        if picked in order:
            choice = str(picked)
    except Exception:
        choice = _unique(probs, order)
    if choice not in order:
        choice = None
    return choice, kept


def _score_of(block: Any) -> float | None:
    """The score that came back. It is not snapped to a level."""

    if not isinstance(block, dict):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        if block.get("error"):
            return None
        if "score" in block:
            return _finite(block.get("score"))
        return None


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A float is not cut at a line."""

    if not isinstance(block, dict):
        return None
    if block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked, _kept = _choice_of(block, _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _miss(block: Any, value: Any, order: tuple[str, ...], receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, dict) and block.get("error"):
        return str(block.get("error"))
    probs = _probs(block)
    if probs and _unique(probs, order or tuple(probs)) is None:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _choice_question(qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {key: _scrub_text(val) for key, val in criteria.items()}
    body: dict[str, Any] = {"type": "choice", "instructions": text, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, cleaned)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "choice"
            shaped["instructions"] = text
            shaped["criteria"] = cleaned
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    text = _scrub_text(instructions)
    body: dict[str, Any] = {
        "type": "score",
        "instructions": text,
        "criteria": ["below this state", "this state", "above this state"],
    }
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, text)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "score"
            shaped["instructions"] = text
            criteria = shaped.get("criteria")
            if isinstance(criteria, list):
                shaped["criteria"] = [_scrub_text(str(item)) for item in criteria]
            else:
                shaped["criteria"] = list(body["criteria"])
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(instructions),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _questions() -> dict[str, Any]:
    """One pack. Types are choice, noul, or score."""

    pack: dict[str, Any] = {}
    pack.update(
        _choice_question(
            "two_stop_day_circuit",
            "For this sleeve on this session day, does the two-stop day circuit refuse a remint, "
            "or is the circuit open? "
            "The closed orig-stop count and the measured rest sum are facts on this state. "
            "The option you return is the decision. "
            "An empty answer or a tie is not a decision. "
            "This ask does not transmit an order.",
            dict(_CIRCUIT_CRITERIA),
        )
    )
    pack.update(
        _noul_question(
            "two_stop_day_refuse",
            "Does this state refuse a remint on the two-stop day circuit? "
            "The noul you return is that answer. "
            "An empty answer leaves it unset. "
            "This ask does not transmit an order.",
            "This state refuses a remint.",
            "This state does not refuse a remint.",
        )
    )
    pack.update(
        _noul_question(
            "two_stop_day_strongly_negative",
            "Is the same-day rest sum on this state strongly negative? "
            "The measured rest sum is a fact. "
            "The noul you return is that answer. "
            "An empty answer leaves it unset. "
            "This ask does not transmit an order.",
            "The same-day rest sum on this state is strongly negative.",
            "The same-day rest sum on this state is not strongly negative.",
        )
    )
    pack.update(
        _noul_question(
            "two_stop_day_exhausted",
            "Are same-sleeve original stops for this sleeve on this session day spent? "
            "The closed count is a fact. "
            "The noul you return is that answer. "
            "An empty answer leaves it unset. "
            "This ask does not transmit an order.",
            "Same-sleeve original stops on this session day are spent.",
            "This sleeve still has room on this session day.",
        )
    )
    pack.update(
        _choice_question(
            "two_stop_day_reason",
            "Which reason names this two-stop day circuit state? "
            "The option with the single highest probability is the reason. "
            "An empty answer or a tie leaves the reason unset. "
            "This ask does not transmit an order.",
            dict(_REASON_CRITERIA),
        )
    )
    pack.update(
        _choice_question(
            "two_stop_day_verdict",
            "Which verdict is this two-stop day circuit state? "
            "The option with the single highest probability is the verdict. "
            "An empty answer or a tie leaves the verdict unset. "
            "This ask does not transmit an order.",
            dict(_VERDICT_CRITERIA),
        )
    )
    pack.update(
        _choice_question(
            "two_stop_day_kind",
            "Which consume kind is this two-stop day circuit state? "
            "The option with the single highest probability is the kind. "
            "An empty answer or a tie leaves the kind unset. "
            "This ask does not transmit an order.",
            dict(_KIND_CRITERIA),
        )
    )
    pack.update(
        _score_question(
            "two_stop_day_cap",
            "What cap applies to same-sleeve original stops on this session day? "
            "The score you return is that cap. "
            "It may sit between levels. "
            "An empty score leaves the cap unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _score_question(
            "two_stop_day_rest_line",
            "What rest-sum line marks strongly negative for this state? "
            "The score you return is that line. "
            "It may sit between levels. "
            "An empty score leaves the line unset. "
            "This ask does not transmit an order.",
        )
    )
    scrubbed = _scrub(pack)
    return scrubbed if isinstance(scrubbed, dict) else {}


def _count_fact(
    doc: MappingLike | None,
    *,
    sleeve: str,
    session_day: str,
    symbol: str | None,
) -> int | None:
    if not doc:
        return None
    return same_sleeve_orig_stop_count_session_day(
        doc,
        sleeve=sleeve,
        session_day=session_day,
        symbol=symbol,
    )


def _row_fact(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ticket": row.get("ticket") or row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "sleeve": _sleeve(row),
        "day": _row_day(row),
        "closed_utc": row.get("closed_utc") or row.get("updated_utc") or row.get("time_utc"),
        "exit_class": str(
            row.get("exit_class")
            or row.get("close_class")
            or row.get("reason")
            or row.get("class")
            or ""
        ),
        "orig_stop": _is_orig_stop(row),
        "rest_r": _row_r(row),
    }


def _payload(
    doc: MappingLike | None,
    *,
    sleeve: str,
    session_day: str,
    symbol: str | None,
    count: int | None,
    rest: float | None,
    proposed_cap: float | None,
) -> dict[str, Any]:
    namespace = CHALLENGE_NS
    if isinstance(doc, dict) and doc.get("namespace"):
        namespace = str(doc.get("namespace"))
    sleeve_key = sleeve[3:] if str(sleeve).startswith("F5:") else str(sleeve)
    body: dict[str, Any] = {
        "model": MODEL,
        "namespace": namespace,
        "login": CHALLENGE_LOGIN,
        "magic": CHALLENGE_MAGIC,
        "sleeve": sleeve_key,
        "session_day": session_day,
        "symbol": symbol,
        "closed_absent": not bool(doc),
        "closed_orig_stop_count": count,
        "rest_sum_r": rest,
        "proposed_cap": proposed_cap,
        "closed": [_row_fact(row) for row in closed_rows(doc or {})],
        "identity": {
            "ns": namespace,
            "login": CHALLENGE_LOGIN,
            "magic": CHALLENGE_MAGIC,
            "sleeve": sleeve_key,
            "symbol": symbol,
        },
    }
    scrubbed = _scrub(body)
    return scrubbed if isinstance(scrubbed, dict) else body


def _remember(state: Mapping[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
    append_outcome: Any = None
    try:
        from .jev_questions import append_outcome as _append_outcome

        append_outcome = _append_outcome
    except Exception:
        append_outcome = None
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        if append_outcome is not None:
            try:
                append_outcome(key, value, logged, error=error)
                continue
            except Exception:
                pass
        _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": error})


def _ask(state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = dict(state)
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = [dict(row) for row in _LOCAL_OUTCOMES]
    payload["prior_outcomes"] = [] if loaded is None else loaded
    try:
        from .jev_client import evaluate

        receipt = evaluate(
            payload,
            questions=questions,
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {
            "error": type(exc).__name__,
            "answers": {},
            "state": payload,
            "model": MODEL,
        }
    if not isinstance(receipt, dict):
        return {
            "error": "evaluate_not_a_dict",
            "answers": {},
            "state": payload,
            "model": MODEL,
        }
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


def _notes(
    *,
    circuit: str | None,
    refuse: bool | float | None,
    strongly: bool | float | None,
    exhausted: bool | float | None,
) -> tuple[str, ...]:
    notes = ["never_remint", "never_broker_send"]
    if circuit == "refuse_remint":
        notes.append("circuit_refuse_remint")
    elif circuit == "circuit_open":
        notes.append("circuit_open")
    if refuse is True:
        notes.append("refuse_remint")
    elif refuse is False:
        notes.append("refuse_remint_false")
    if strongly is True:
        notes.append("same_day_rest_sum_r_strongly_negative")
    if exhausted is True:
        notes.append("orig_stops_at_cap")
    return tuple(notes)


def _stamp(
    *,
    count: int | None,
    rest: float | None,
    answers: Mapping[str, Any],
    receipt_error: Any,
    posted: Mapping[str, Any],
) -> TwoStopCircuitStamp:
    circuit, circuit_probs = _choice_of(answers.get("two_stop_day_circuit"), _CIRCUIT_ORDER)
    reason, _reason_probs = _choice_of(answers.get("two_stop_day_reason"), _REASON_ORDER)
    verdict, _verdict_probs = _choice_of(answers.get("two_stop_day_verdict"), _VERDICT_ORDER)
    kind, _kind_probs = _choice_of(answers.get("two_stop_day_kind"), _KIND_ORDER)
    refuse = _noul_of(answers.get("two_stop_day_refuse"))
    strongly = _noul_of(answers.get("two_stop_day_strongly_negative"))
    exhausted = _noul_of(answers.get("two_stop_day_exhausted"))
    cap_score = _score_of(answers.get("two_stop_day_cap"))
    rest_line = _score_of(answers.get("two_stop_day_rest_line"))
    rows = [
        (
            "two_stop_day_circuit",
            circuit,
            _miss(answers.get("two_stop_day_circuit"), circuit, _CIRCUIT_ORDER, receipt_error),
        ),
        (
            "two_stop_day_refuse",
            refuse,
            _miss(answers.get("two_stop_day_refuse"), refuse, _NOUL_ORDER, receipt_error),
        ),
        (
            "two_stop_day_strongly_negative",
            strongly,
            _miss(
                answers.get("two_stop_day_strongly_negative"),
                strongly,
                _NOUL_ORDER,
                receipt_error,
            ),
        ),
        (
            "two_stop_day_exhausted",
            exhausted,
            _miss(answers.get("two_stop_day_exhausted"), exhausted, _NOUL_ORDER, receipt_error),
        ),
        (
            "two_stop_day_reason",
            reason,
            _miss(answers.get("two_stop_day_reason"), reason, _REASON_ORDER, receipt_error),
        ),
        (
            "two_stop_day_verdict",
            verdict,
            _miss(answers.get("two_stop_day_verdict"), verdict, _VERDICT_ORDER, receipt_error),
        ),
        (
            "two_stop_day_kind",
            kind,
            _miss(answers.get("two_stop_day_kind"), kind, _KIND_ORDER, receipt_error),
        ),
        (
            "two_stop_day_cap",
            cap_score,
            _miss(answers.get("two_stop_day_cap"), cap_score, (), receipt_error),
        ),
        (
            "two_stop_day_rest_line",
            rest_line,
            _miss(answers.get("two_stop_day_rest_line"), rest_line, (), receipt_error),
        ),
    ]
    _remember(posted, rows)
    error = str(receipt_error) if receipt_error not in (None, "") and not answers else None
    return TwoStopCircuitStamp(
        refuse_remint=refuse,
        reason=reason,
        verdict=verdict,
        orig_stops=count,
        rest_sum_r=rest,
        rest_sum_r_strongly_negative=strongly,
        notes=_notes(circuit=circuit, refuse=refuse, strongly=strongly, exhausted=exhausted),
        circuit=circuit,
        circuit_probabilities=tuple(circuit_probs.items()),
        exhausted=exhausted,
        cap=cap_score,
        rest_line=rest_line,
        kind=kind,
        error=error,
    )


def _blank(count: int | None, rest: float | None, error: str) -> TwoStopCircuitStamp:
    return TwoStopCircuitStamp(
        refuse_remint=None,
        reason=None,
        verdict=None,
        orig_stops=count,
        rest_sum_r=rest,
        rest_sum_r_strongly_negative=None,
        notes=("never_remint", "never_broker_send"),
        error=error,
    )


def refuse_remint(
    doc: MappingLike | None,
    *,
    sleeve: str,
    session_day: str,
    symbol: str | None = None,
    cap: float | None = None,
) -> TwoStopCircuitStamp:
    """Refuse-remint stamp for this sleeve and session day.

    The count and the rest sum are reads. The refuse, the strongly-negative
    noul, the exhausted noul, the reason, the verdict, the kind, the cap,
    and the rest line are the return on this ask. A passed cap is a fact
    on the state. A miss leaves the return unset.
    """

    count = _count_fact(doc, sleeve=sleeve, session_day=session_day, symbol=symbol)
    rest = same_day_rest_sum_r(doc, sleeve=sleeve, session_day=session_day, symbol=symbol)
    try:
        questions = _questions()
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return _blank(count, rest, type(exc).__name__)
    if not questions or any(
        not isinstance(block, dict) or block.get("type") not in _ALLOWED_TYPES
        for block in questions.values()
    ):
        return _blank(count, rest, "question_pack_fail")
    payload = _payload(
        doc,
        sleeve=sleeve,
        session_day=session_day,
        symbol=symbol,
        count=count,
        rest=rest,
        proposed_cap=_finite(cap),
    )
    asked = _ask(payload, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    posted = asked.get("state") if isinstance(asked.get("state"), dict) else payload
    return _stamp(
        count=count,
        rest=rest,
        answers=answers,
        receipt_error=asked.get("error"),
        posted=posted,
    )


def refuse_remint_as_of(
    doc: MappingLike | None,
    *,
    sleeve: str,
    as_of_utc: datetime,
    symbol: str | None = None,
) -> TwoStopCircuitStamp:
    day = as_of_utc.astimezone(timezone.utc).date().isoformat()
    return refuse_remint(doc, sleeve=sleeve, session_day=day, symbol=symbol)


def consume_two_stop_reason() -> dict[str, Any]:
    """Consume row. Reason, verdict, and kind are the return. A miss stays unset."""

    stamp = refuse_remint(None, sleeve="", session_day="")
    return {
        "reason": stamp.reason,
        "verdict": stamp.verdict,
        "kind": stamp.kind,
        "refuse_remint": stamp.refuse_remint,
        "place": False,
        "never_remint": True,
        "never_broker_send": True,
    }


def parse_closed_utc(raw: Any) -> datetime | None:
    return _parse_utc(raw)
