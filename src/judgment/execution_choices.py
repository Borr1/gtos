"""Challenge execution decisions are the Jev return for that state.

Fill, modify, partial, trail, time stop, reject, retry, spread, and lot
are each their own question. The choice is the option with the unique
highest probability. The parameter is the Score on that state, and a
Score may sit between the levels. A tie, an empty answer, a missing
score, or an error is not a decision and does not restore a constant.
This module never calls order_send. A missing score does not restore
a persistence weight. Friends copy the recorded result.

SL modify, TP modify, close, and pending cancel stay on manage_choices.
A null check that only keeps the process alive stays in execution.py.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.execution_choices.v1"

QUESTIONS: dict[str, dict[str, Any]] = {
    "fill": {
        "id": "exec_fill",
        "instructions": (
            "Execution question: this triggered limit. "
            "Pick one option. The fill runs only when fill has the single "
            "highest probability. The fill price is the score on the paired "
            "parameter, and that score may sit between the levels. "
            "leave_pending keeps the resting intent. "
            "An empty answer, a tie, or a missing score does not fill and does not cancel. "
            "Do not flatten an unrelated open ticket. Do not send an order from this question."
        ),
        "criteria": {
            "fill": "Send this limit fill now.",
            "leave_pending": "Do not fill. Keep the pending intent.",
        },
    },
    "modify": {
        "id": "exec_modify",
        "instructions": (
            "Execution question: the stop on this ticket. "
            "Pick one option. The modify runs only when modify has the single "
            "highest probability. The stop is the score on the paired parameter, "
            "and that score may sit between the levels. "
            "leave_stop keeps the broker stop. "
            "An empty answer, a tie, or a missing score does not move the stop. "
            "The SL send, if attempted, is still its own manage question. "
            "Do not close the ticket from this question."
        ),
        "criteria": {
            "modify": "Attempt the breakeven stop move.",
            "leave_stop": "Leave the stop where it is.",
        },
    },
    "partial": {
        "id": "exec_partial",
        "instructions": (
            "Execution question: a partial on this ticket. "
            "Pick one option. A partial close runs only when partial has the "
            "single highest probability. The volume is the score on the paired "
            "parameter, and that score may sit between the levels. "
            "hold_full keeps the full volume. "
            "An empty answer, a tie, or a missing score does not partial. "
            "This ticket is live. partial is a legal winner."
        ),
        "criteria": {
            "partial": "Close the partial volume at this level.",
            "hold_full": "Keep the full position. Do not partial.",
        },
    },
    "trail": {
        "id": "exec_trail",
        "instructions": (
            "Execution question: the trail stop on this ticket. "
            "Pick one option. The trail modify runs only when trail has the "
            "single highest probability. The trail stop is the score on the "
            "paired parameter, and that score may sit between the levels. "
            "leave_stop keeps the current stop. "
            "An empty answer, a tie, or a missing score does not move the stop. "
            "Do not close the ticket from this question."
        ),
        "criteria": {
            "trail": "Move the stop to the tighter trail.",
            "leave_stop": "Leave the trail stop where it is.",
        },
    },
    "time_stop": {
        "id": "exec_time_stop",
        "instructions": (
            "Execution question: whether this open ticket's time stop fires. "
            "Pick one option. A close is attempted only when fire_time_stop "
            "has the single highest probability. The horizon is the score on "
            "the paired parameter, and that score may sit between the levels. "
            "let_it_run keeps the ticket. "
            "An empty answer, a tie, or a missing score does not fire. "
            "The close send, if attempted, is still its own manage question. "
            "This ticket is live. fire_time_stop is a legal winner."
        ),
        "criteria": {
            "fire_time_stop": "Fire the time stop and attempt the close.",
            "let_it_run": "Do not time-stop. Leave the ticket open.",
        },
    },
    "reject": {
        "id": "exec_reject",
        "instructions": (
            "Execution question: the two sides of should_block on this order. "
            "Pick one option. The order continues only when continue has the "
            "single highest probability. block does not send. The block weight "
            "is the score on the paired parameter, and that score may sit between "
            "the levels. An empty answer, a tie, or a missing score does not "
            "restore should_block and does not send. "
            "Do not flatten an open ticket from this question."
        ),
        "criteria": {
            "block": "Block this order. Do not send it.",
            "continue": "Do not block. Let the order continue.",
        },
    },
    "retry": {
        "id": "exec_retry",
        "instructions": (
            "Execution question: the previous attempt failed. "
            "Pick one option. Another attempt happens only when retry has "
            "the single highest probability. The pause before that attempt, "
            "in seconds, is the score on the paired parameter, and that score "
            "may sit between the levels. "
            "stop does not try again. An empty answer, a tie, or a missing score "
            "does not try again and does not restore a one-second pause. "
            "Do not flatten an open ticket from this question."
        ),
        "criteria": {
            "retry": "Try the same act once more.",
            "stop": "Stop. Do not try again.",
        },
    },
    "spread": {
        "id": "exec_spread",
        "instructions": (
            "Execution question: whether this measured spread is acceptable "
            "for the send. Pick one option. The order continues only when "
            "spread_ok has the single highest probability. The spread is the "
            "score on the paired parameter, and that score may sit between the levels. "
            "spread_too_wide does not send. "
            "An empty answer, a tie, or a missing score does not restore a spread. "
            "Do not flatten an open ticket from this question."
        ),
        "criteria": {
            "spread_ok": "The spread is acceptable. Continue the send.",
            "spread_too_wide": "The spread is too wide. Do not send.",
        },
    },
    "lot": {
        "id": "exec_lot",
        "instructions": (
            "Execution question: the lot for this order. "
            "Pick one option. place runs only when place has the single "
            "highest probability. The lot is the score on the paired parameter. "
            "That score is the volume sent. volume_min, volume_step, and "
            "volume_max are facts on this state. The score may sit between "
            "the levels. Code does not round it and does not lift it to a "
            "minimum. refuse does not send. "
            "An empty answer, a tie, or a missing score does not place. "
            "Do not flatten an open ticket from this question."
        ),
        "criteria": {
            "place": "Place the calculated lot.",
            "refuse": "Do not place a lot.",
        },
    },
    "gate": {
        "id": "exec_gate",
        "instructions": (
            "Execution question: a fact is in front of this order. "
            "Pick one option. The order stops only when withhold has the "
            "single highest probability. fact does not stop the order. "
            "An empty answer or a tie does not restore the old stop and does not send. "
            "A floor and a baseline are not a limit. "
            "Do not flatten an open ticket from this question."
        ),
        "criteria": {
            "withhold": "This fact withholds the order.",
            "fact": "This fact does not withhold. The order continues to the next ask.",
        },
    },
    "deviation": {
        "id": "exec_deviation",
        "instructions": (
            "Execution question: the deviation in points for this limit. "
            "Pick one option. use runs only when use has the single highest "
            "probability. The deviation is the score on the paired parameter, "
            "in points, and that score may sit between the levels. "
            "Spread, point, stops level, and freeze level are broker facts. "
            "unset does not send. An empty answer, a tie, or a missing score "
            "does not send and does not restore a deviation. Do not send an order."
        ),
        "criteria": {
            "use": "Use the score as the deviation in points.",
            "unset": "Do not send a deviation.",
        },
    },
    "filling": {
        "id": "exec_filling",
        "instructions": (
            "Execution question: the filling mode for this limit. "
            "Pick one option. That mode is used only when it has the single "
            "highest probability. The broker filling_mode mask is a fact. "
            "An empty answer or a tie does not send and does not restore IOC. "
            "Do not send an order."
        ),
        "criteria": {
            "fok": "Fill or kill.",
            "ioc": "Immediate or cancel.",
            "return": "Return. The limit can rest.",
            "boc": "Book or cancel.",
        },
    },
    "expiry": {
        "id": "exec_expiry",
        "instructions": (
            "Execution question: how long this limit lives. "
            "Pick one option. use runs only when use has the single highest "
            "probability. The score is the life in seconds. Zero means good "
            "till cancelled. The score may sit between the levels. "
            "unset does not send. An empty answer, a tie, or a missing score "
            "does not send and does not restore a clock. Do not send an order."
        ),
        "criteria": {
            "use": "Use the score as the life in seconds.",
            "unset": "Do not send an expiry.",
        },
    },
    "timeout": {
        "id": "exec_timeout",
        "instructions": (
            "Execution question: how long to wait for this broker result. "
            "Pick one option. wait runs only when wait has the single highest "
            "probability. The score is the wait in seconds and may sit between "
            "the levels. stop does not send. An empty answer, a tie, or a "
            "missing score does not send and does not restore ten seconds. "
            "Do not send an order."
        ),
        "criteria": {
            "wait": "Wait the score in seconds.",
            "stop": "Do not wait. Do not send.",
        },
    },
    "adopt_wait": {
        "id": "exec_adopt_wait",
        "instructions": (
            "Execution question: after a wait with no result, the pause before "
            "reading positions. Pick one option. wait runs only when wait has "
            "the single highest probability. The score is that pause in seconds "
            "and may sit between the levels. now reads positions with no pause. "
            "An empty answer or a tie does not restore two seconds. Do not send."
        ),
        "criteria": {
            "wait": "Pause the score in seconds, then read positions.",
            "now": "Read positions without a planted pause.",
        },
    },
    "timeout_label": {
        "id": "exec_timeout_label",
        "instructions": (
            "Execution question: the wait ended and this send has no fill. "
            "Pick one option. timeout_no_position is the label only when it "
            "has the single highest probability. stop does not call it a "
            "retryable timeout. An empty answer or a tie does not restore "
            "timeout_no_position. Do not send an order."
        ),
        "criteria": {
            "timeout_no_position": "No matching position after the wait.",
            "order_send_exception": "The send failed as an exception.",
            "stop": "Do not label this a retryable timeout.",
        },
    },
}

_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def record_path() -> Path:
    override = (os.environ.get("GTOS_EXECUTION_CHOICES_RECORD") or "").strip()
    if override:
        return Path(override)
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / CHALLENGE_NS
        / "judgment"
        / "execution_choices.jsonl"
    )


def armed_path() -> Path:
    return record_path().with_name("execution_choices_armed.json")


def clear_cache() -> None:
    _CACHE.clear()


def _ticket(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _append(path: Path, row: Mapping[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(dict(row)), sort_keys=True) + "\n")
    except OSError:
        return


def write_armed_stamp() -> None:
    try:
        payload = {
            "schema": SCHEMA,
            "logged_at_utc": _now(),
            "ns": CHALLENGE_NS,
            "armed": True,
            "questions": sorted(QUESTIONS),
            "pid": os.getpid(),
            "persist": None,
            "agent_order_send": False,
            "activation_token": "stays",
            "model": MODEL,
            "gold_close_pin": False,
        }
        path = armed_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    except OSError:
        return


_PARAMETER_NOUN = {
    "fill": "fill price",
    "modify": "stop",
    "partial": "volume",
    "trail": "trail stop",
    "time_stop": "horizon",
    "reject": "block weight",
    "retry": "pause in seconds",
    "spread": "spread",
    "lot": "lot",
    "deviation": "deviation in points",
    "expiry": "life in seconds",
    "timeout": "wait in seconds",
    "adopt_wait": "pause in seconds",
}
# The acting option runs only with its Score. A missing score stays missing.
_NEEDS_SCORE = {
    "fill": "fill",
    "modify": "modify",
    "partial": "partial",
    "trail": "trail",
    "time_stop": "fire_time_stop",
    "reject": "continue",
    "retry": "retry",
    "spread": "spread_ok",
    "lot": "place",
    "deviation": "use",
    "expiry": "use",
    "timeout": "wait",
    "adopt_wait": "wait",
}
_SKIP_KEY_PARTS = (
    "floor",
    "baseline",
    "equity",
    "balance",
    "drawdown",
    "profit_target",
    "max_loss",
    "daily_loss",
    "kill",
    "proposed",
)
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)


def _score_instructions(question: str) -> str:
    noun = _PARAMETER_NOUN.get(question, "parameter")
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score does not restore a constant. "
        "A floor and a baseline are not a bound. "
        "Do not send an order."
    )


def _level_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _parameter_levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Live numeric levels already on the facts. A score may sit between them."""

    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        low = key.lower()
        if any(part in low for part in _SKIP_KEY_PARTS):
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(str(child_key), child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            for item in value:
                walk(key, item)
            return
        number = _level_number(value)
        if number is not None:
            found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    ordered = sorted(set(found))
    return [format(number, ".10g") for number in ordered]


def _question_pack(
    question: str,
    spec: Mapping[str, Any],
    levels: list[str],
) -> dict[str, Any]:
    """Choice plus Score for this state. Same question objects the place hop posts."""

    qid = str(spec["id"])
    choice_criteria = {str(key): str(value) for key, value in dict(spec["criteria"]).items()}
    score_levels = list(levels) if levels else list(_BETWEEN)
    score_text = _score_instructions(question)
    pack: dict[str, Any] | None = None
    try:
        from .jev_questions import parameter_question, spot_question

        built = spot_question(qid, spec["instructions"], choice_criteria)
        extra = parameter_question(qid + "_parameter", score_text)
        if isinstance(built, Mapping) and isinstance(extra, Mapping):
            pack = {}
            for key, value in dict(built).items():
                pack[str(key)] = dict(value) if isinstance(value, Mapping) else value
            for key, value in dict(extra).items():
                pack[str(key)] = dict(value) if isinstance(value, Mapping) else value
    except Exception:
        pack = None
    if not isinstance(pack, dict):
        pack = {}
    choice_q = pack.get(qid)
    if not isinstance(choice_q, dict):
        choice_q = {}
        pack[qid] = choice_q
    choice_q["type"] = "choice"
    choice_q["instructions"] = spec["instructions"]
    choice_q["criteria"] = choice_criteria
    param_id = qid + "_parameter"
    param_q = pack.get(param_id)
    if not isinstance(param_q, dict):
        param_q = {}
        pack[param_id] = param_q
    param_q["type"] = "score"
    param_q["instructions"] = score_text
    param_q["criteria"] = list(score_levels)
    return pack


def _choice_from_probabilities(
    probabilities: Mapping[str, Any] | None,
    order: tuple[str, ...],
) -> tuple[str | None, float | None]:
    """Unique highest probability. A tie or a bare label is not a decision."""

    if not isinstance(probabilities, Mapping) or not probabilities:
        return None, None
    numeric: dict[str, float] = {}
    allowed = set(order)
    for key, value in probabilities.items():
        name = str(key)
        if name not in allowed:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number != number:
            continue
        numeric[name] = number
    if not numeric:
        return None, None
    best_p = max(numeric.values())
    winners = [
        name for name in order if name in numeric and abs(numeric[name] - best_p) <= 1e-12
    ]
    if len(winners) != 1:
        return None, None
    return winners[0], numeric[winners[0]]


def _returned_score(block: Any) -> float | None:
    """The Score Jev returned. It is not snapped to a level."""

    try:
        from .jev_questions import returned_number

        number = returned_number(block)
        if isinstance(number, (int, float)) and not isinstance(number, bool) and number == number:
            return float(number)
    except Exception:
        pass
    if not isinstance(block, dict):
        return None
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    if raw is None or isinstance(raw, bool):
        return None
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _returned_noul(block: Any) -> bool | float | None:
    """A Noul is a probability. Missing stays missing."""

    if not isinstance(block, dict):
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value:
        return None
    return value


def _answers_of(hop: Mapping[str, Any], qid: str) -> dict[str, Any]:
    answers = hop.get("answers")
    if isinstance(answers, dict):
        return answers
    if (
        isinstance(hop.get("probabilities"), dict)
        or "score" in hop
        or "noul" in hop
        or "value" in hop
    ):
        return {qid: dict(hop)}
    return {}


def _apply_return(
    row: dict[str, Any],
    hop: Mapping[str, Any],
    *,
    question: str,
    qid: str,
    options: tuple[str, ...],
) -> None:
    answers = _answers_of(hop, qid)
    choice_block = answers.get(qid)
    score_block = answers.get(qid + "_parameter")
    if not isinstance(choice_block, dict):
        choice_block = {}
    if not isinstance(score_block, dict):
        score_block = {}
    probs = choice_block.get("probabilities")
    if not isinstance(probs, dict):
        probs = {}
    picked, probability = _choice_from_probabilities(probs, options)
    score = _returned_score(score_block) if score_block else None
    if score is None and not score_block:
        raw_score = choice_block.get("score")
        if raw_score is None:
            raw_score = choice_block.get("value")
        if raw_score is not None:
            score = _returned_score({"score": raw_score})
    noul = _returned_noul(choice_block)
    if noul is None:
        noul = _returned_noul(score_block)
    row["probabilities"] = {
        str(name): value for name, value in probs.items() if str(name) in options
    }
    row["probability"] = probability
    row["probability_source"] = "systemone" if row["probabilities"] else None
    row["parameter"] = score
    row["score"] = score
    row["noul"] = noul
    error = hop.get("error")
    if error in (None, ""):
        error = hop.get("skipped")
    row["error"] = None if error in (None, "") else str(error)
    needs = _NEEDS_SCORE.get(question)
    if picked is None or (needs is not None and picked == needs and score is None):
        row["choice"] = None
        row["decision_emitted"] = False
        if picked is not None and score is None and not row["error"]:
            row["error"] = "score_missing"
        return
    row["choice"] = picked
    row["decision_emitted"] = True


def _base(question: str) -> dict[str, Any]:
    spec = QUESTIONS[question]
    return {
        "schema": SCHEMA,
        "logged_at_utc": _now(),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "question": question,
        "question_id": spec["id"],
        "choice": None,
        "parameter": None,
        "score": None,
        "noul": None,
        "probability": None,
        "probabilities": {},
        "probability_source": None,
        "decision_emitted": False,
        "model": MODEL,
        "persist": None,
        "agent_order_send": False,
        "friends_copy_result": True,
        "extra_pass": False,
        "activation_token": "stays",
        "error": None,
    }


def choose(
    question: str,
    *,
    ticket: Any = None,
    symbol: Any = None,
    reason: str = "",
    proposed: Any = None,
    facts: Mapping[str, Any] | None = None,
    ask: Callable[..., dict[str, Any]] | None = None,
    use_cache: bool = True,
    record: bool = True,
    record_to: Path | None = None,
) -> dict[str, Any]:
    """Ask Jev for this execution state. Never raises. Never sends an order.

    ``choice`` is set only when that option is the unique highest probability.
    ``parameter`` is the Score. A tie, an empty answer, a missing score, or
    an error leaves that return unset.
    """

    if question not in QUESTIONS:
        row = _base("fill")
        row["question"] = question
        row["question_id"] = None
        row["error"] = "unknown_question"
        row["decision_emitted"] = False
        return row
    spec = QUESTIONS[question]
    options = tuple(spec["criteria"])
    ticket_i = _ticket(ticket)
    row = _base(question)
    row["ticket"] = ticket_i
    row["symbol"] = symbol
    row["reason"] = reason or question
    row["proposed"] = proposed
    fact_map = dict(facts or {})
    row["facts"] = fact_map
    facts_key = json.dumps(_jsonable(fact_map), sort_keys=True)
    key = (question, ticket_i, str(reason), str(symbol), str(proposed), facts_key)
    if use_cache:
        hit = _CACHE.get(key)
        if isinstance(hit, dict):
            cached = dict(hit)
            cached["logged_at_utc"] = row["logged_at_utc"]
            cached["cache"] = True
            return cached
    levels = _parameter_levels(fact_map)
    pack = _question_pack(question, spec, levels)
    state = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "question": question,
        "ticket": ticket_i,
        "symbol": symbol,
        "reason": reason or question,
        "proposed": proposed,
        "model": MODEL,
        "facts": fact_map,
        "levels": levels,
    }
    try:
        from .jev_questions import prior_outcomes

        state["prior_outcomes"] = prior_outcomes(state=state, questions=pack)
    except Exception:
        pass
    try:
        if ask is None:
            from .jev_client import evaluate

            hop = evaluate(
                state,
                questions=pack,
                merge_sleeve=False,
            )
        else:
            hop = ask(
                state,
                question_id=spec["id"],
                instructions=spec["instructions"],
                criteria=spec["criteria"],
            )
    except Exception as exc:  # noqa: BLE001 — execution must not raise into the writer
        hop = {"error": type(exc).__name__}
    if not isinstance(hop, dict):
        hop = {"error": "evaluate_not_a_dict"}
    _apply_return(
        row,
        hop,
        question=question,
        qid=str(spec["id"]),
        options=options,
    )
    if hop.get("model"):
        row["model"] = hop.get("model")
    try:
        from .jev_questions import append_outcome

        append_outcome(
            spec["id"],
            row.get("choice"),
            state,
            error=None if row.get("decision_emitted") else row.get("error"),
        )
        append_outcome(
            str(spec["id"]) + "_parameter",
            row.get("score"),
            state,
            error=None if row.get("score") is not None else row.get("error"),
        )
    except Exception:
        pass
    if use_cache:
        _CACHE[key] = dict(row)
    if record:
        _append(record_to or record_path(), row)
    return row


_SEND_PACK = (
    "lot",
    "spread",
    "deviation",
    "filling",
    "expiry",
    "timeout",
    "adopt_wait",
)


def ask_send(
    *,
    symbol: Any = None,
    reason: str = "send",
    proposed: Any = None,
    facts: Mapping[str, Any] | None = None,
    include: tuple[str, ...] | list[str] | None = None,
    ask: Callable[..., dict[str, Any]] | None = None,
    use_cache: bool = True,
    record: bool = True,
    record_to: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """One evaluate for this send state. Each question once. Never sends.

    Independent send questions share that post. A later read of the same
    state returns the cached row. An empty answer, a tie, or an error leaves
    that question's choice unset and does not restore a constant.
    """

    names = tuple(include) if include is not None else _SEND_PACK
    names = tuple(name for name in names if name in QUESTIONS)
    fact_map = dict(facts or {})
    facts_key = json.dumps(_jsonable(fact_map), sort_keys=True)
    key = ("send", names, str(symbol), str(reason), str(proposed), facts_key)
    if use_cache:
        hit = _CACHE.get(key)
        if isinstance(hit, dict) and hit.get("_send_pack") is True:
            cached: dict[str, dict[str, Any]] = {}
            for name in names:
                row = hit.get(name)
                if isinstance(row, dict):
                    copy = dict(row)
                    copy["cache"] = True
                    copy["logged_at_utc"] = _now()
                    cached[name] = copy
            return cached
    levels = _parameter_levels(fact_map)
    pack: dict[str, Any] = {}
    for name in names:
        pack.update(_question_pack(name, QUESTIONS[name], levels))
    state = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "question": "send",
        "symbol": symbol,
        "reason": reason or "send",
        "proposed": proposed,
        "model": MODEL,
        "facts": fact_map,
        "levels": levels,
    }
    try:
        from .jev_questions import prior_outcomes

        state["prior_outcomes"] = prior_outcomes(state=state, questions=pack)
    except Exception:
        pass
    try:
        if ask is None:
            from .jev_client import evaluate

            hop = evaluate(state, questions=pack, merge_sleeve=False)
        else:
            hop = ask(state, questions=pack)
    except Exception as exc:  # noqa: BLE001 — a dark pack must not raise into the send
        hop = {"error": type(exc).__name__}
    if not isinstance(hop, dict):
        hop = {"error": "evaluate_not_a_dict"}
    rows: dict[str, dict[str, Any]] = {}
    for name in names:
        spec = QUESTIONS[name]
        row = _base(name)
        row["symbol"] = symbol
        row["reason"] = reason or "send"
        row["proposed"] = proposed
        row["facts"] = fact_map
        _apply_return(
            row,
            hop,
            question=name,
            qid=str(spec["id"]),
            options=tuple(spec["criteria"]),
        )
        if hop.get("model"):
            row["model"] = hop.get("model")
        try:
            from .jev_questions import append_outcome

            append_outcome(
                spec["id"],
                row.get("choice"),
                state,
                error=None if row.get("decision_emitted") else row.get("error"),
            )
            append_outcome(
                str(spec["id"]) + "_parameter",
                row.get("score"),
                state,
                error=None if row.get("score") is not None else row.get("error"),
            )
        except Exception:
            pass
        if record:
            _append(record_to or record_path(), row)
        rows[name] = row
    if use_cache:
        stored = {name: dict(row) for name, row in rows.items()}
        stored["_send_pack"] = True
        _CACHE[key] = stored
    return rows
