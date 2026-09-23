"""Event proximity for one as-of.

The covering spine stays a clock fact: empty, minutes, windows, and events.
An empty spine is not no HIGH. This module does not invent a clock, does not
apply a news protocol, and does not flatten.

Every decision and every parameter is the System One return for this state.
One call: ``jev_client.evaluate`` with model ``jev-1.13.0``,
``merge_sleeve=False``, POST https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached on
that ask, and the return is stored for the next ask.

The proximity noul, abstain, decidable, and the reason Choice are that
return. The minutes, the F5 and W7 block minutes, and apply persist are
Scores and may sit between levels. An empty answer, a tie, a missing score,
or an error leaves that field unset and does not restore a constant.
A floor and a baseline are not a question. This module does not send.

``flatten``, ``panic_flatten``, ``lens``, ``NEWS_PROTOCOL_APPLIED``, and
``invented`` are structural marks of this study module.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0
NEWS_PROTOCOL_APPLIED = False
STUDY_LENS = "study"

_REASON_ORDER = ("spine_empty_abstain", "covering_high", "outside_window")
_REASON_CRITERIA = {
    "spine_empty_abstain": "The spine is empty, so proximity abstains. Empty is not no HIGH.",
    "covering_high": "A covering named HIGH is on this spine.",
    "outside_window": "Named events are on this spine and none sit in the window.",
}
_NOUL_ORDER = ("true", "false")
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
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
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


def _as_of(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


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

    if isinstance(value, Mapping):
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


def _flag(value: Any) -> bool | None:
    if value is True or value is False:
        return value
    return None


def _unique(probs: Mapping[str, Any] | None, order: tuple[str, ...] | None) -> str | None:
    """Unique highest probability. A missing probability is not zero. A tie is unset."""

    if not isinstance(probs, Mapping) or not probs:
        return None
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
        number = _finite(raw)
        if number is None:
            continue
        seen = True
        if best_p is None or number > best_p + 1e-12:
            best = str(name)
            best_p = number
            tied = False
        elif abs(number - best_p) <= 1e-12:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping):
        return None
    picked: str | None = None
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probs, order)
        if agreed in order:
            picked = str(agreed)
    except Exception:
        picked = None
    if picked not in order:
        picked = _unique(probs, order)
    if picked not in order:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice(block, _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The score that came back. A missing score is not a constant and not a probability."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "score" not in block or block.get("score") is None:
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        return _finite(block.get("score"))


def _pull(block: Any, kind: str, order: tuple[str, ...] | None) -> Any:
    if kind == "noul":
        return _noul(block)
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block)


def _why(block: Any, value: Any, order: tuple[str, ...] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = block.get("probabilities") if isinstance(block, Mapping) else None
    menu = order or (tuple(str(name) for name in probs) if isinstance(probs, Mapping) else ())
    if isinstance(probs, Mapping) and probs and _unique(probs, menu or None) is None:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    cleaned = {str(key): _scrub_text(str(value)) for key, value in criteria.items()}
    body: dict[str, Any] = {"type": "choice", "instructions": instructions, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, cleaned)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "choice"
            shaped["instructions"] = instructions
            shaped["criteria"] = cleaned
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, text: str, levels: Sequence[str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    criteria = [_scrub_text(str(item)) for item in levels] if levels else [str(item) for item in _BETWEEN]
    body: dict[str, Any] = {"type": "score", "instructions": instructions, "criteria": criteria}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "score"
            shaped["instructions"] = instructions
            shaped["criteria"] = criteria
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _noul_question(qid: str, text: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(text),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _levels(minutes: float | None) -> list[str]:
    levels = [str(item) for item in _BETWEEN]
    if minutes is not None:
        levels.append(format(minutes, ".10g"))
    return levels


def _questions(minutes: float | None) -> dict[str, Any]:
    """One pack. Types are noul, choice, or score."""

    levels = _levels(minutes)
    unset = "An empty answer leaves it unset. This ask does not transmit an order."
    pack: dict[str, Any] = {}
    pack.update(
        _noul_question(
            "event_proximity",
            "Is a named HIGH inside the window this spine already carries? "
            "news.high_in_f5_window and news.high_in_w7_window are clock facts. "
            "If news.spine_empty is true, you do not know. "
            "An empty spine is not no HIGH. " + unset,
            "A named HIGH is inside the window this spine carries.",
            "Named events exist and none are inside that window.",
        )
    )
    pack.update(
        _noul_question(
            "event_proximity_abstain",
            "Does this state abstain the event-proximity question? "
            "An empty spine is not a filled answer. " + unset,
            "Abstain the event-proximity question.",
            "Do not abstain the event-proximity question.",
        )
    )
    pack.update(
        _noul_question(
            "event_proximity_decidable",
            "Is event proximity decidable from the named spine on this state? "
            "An empty spine leaves the question unknown. " + unset,
            "The named spine is enough to decide proximity.",
            "The named spine is not enough to decide proximity.",
        )
    )
    pack.update(
        _choice_question(
            "event_proximity_reason",
            "What is the event-proximity reason for this state? "
            "The option you return is the unique highest probability. "
            "A tie or an empty answer leaves it unset. "
            "An empty spine is not no HIGH. "
            "This ask does not transmit an order.",
            _REASON_CRITERIA,
        )
    )
    score_lines = (
        ("minutes_to_nearest_high", "minutes to the nearest named HIGH"),
        ("f5_pre_block_minutes", "F5 pre-block minutes"),
        ("f5_post_block_minutes", "F5 post-block minutes"),
        ("w7_pre_block_minutes", "W7 pre-block minutes"),
        ("w7_post_block_minutes", "W7 post-block minutes"),
        ("apply_persist", "apply-persist parameter"),
    )
    for qid, noun in score_lines:
        pack.update(
            _score_question(
                qid,
                f"The score you return is the {noun} for this state. "
                "It may sit between the levels. "
                "An empty score leaves it unset. "
                "This ask does not transmit an order.",
                levels,
            )
        )
    return pack


def _read_spine(
    moment: datetime,
    spines: dict[str, Any] | None,
    news: Mapping[str, Any] | None,
    symbol: str,
) -> dict[str, Any] | None:
    """Spine rows are facts. A missing reader leaves the clock unnamed."""

    if isinstance(news, Mapping):
        return dict(news)
    try:
        from .news_spine import attach_news, load_spines
    except Exception:
        return None
    try:
        packed = spines if spines is not None else load_spines()
        attached = attach_news(moment, spines=packed, symbol=symbol)
    except Exception:
        return None
    if isinstance(attached, Mapping):
        return dict(attached)
    return None


def _facts(attached: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(attached, Mapping):
        return {
            "spine_empty": None,
            "minutes": None,
            "f5": None,
            "w7": None,
            "events": None,
        }
    events = attached.get("events")
    rows: list[dict[str, Any]] | None
    if isinstance(events, list):
        rows = [dict(item) for item in events if isinstance(item, Mapping)]
    else:
        rows = None
    return {
        "spine_empty": _flag(attached.get("spine_empty")),
        "minutes": _finite(attached.get("minutes_to_nearest_high")),
        "f5": _flag(attached.get("high_in_f5_window")),
        "w7": _flag(attached.get("high_in_w7_window")),
        "events": rows,
    }


def _state(moment: datetime, symbol: str, facts: Mapping[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": MODEL,
        "namespace": CHALLENGE_NS,
        "login": CHALLENGE_LOGIN,
        "magic": CHALLENGE_MAGIC,
        "symbol": str(symbol),
        "as_of_utc": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "news": {
            "spine_empty": facts.get("spine_empty"),
            "minutes_to_nearest_high": facts.get("minutes"),
            "high_in_f5_window": facts.get("f5"),
            "high_in_w7_window": facts.get("w7"),
            "events": facts.get("events"),
            "symbol": str(symbol),
        },
        "identity": {
            "ns": CHALLENGE_NS,
            "login": CHALLENGE_LOGIN,
            "symbol": str(symbol),
        },
    }
    scrubbed = _scrub(body)
    return scrubbed if isinstance(scrubbed, dict) else body


def _attach_priors(payload: dict[str, Any], questions: Mapping[str, Any]) -> None:
    payload.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = [dict(item) for item in _LOCAL_OUTCOMES]
    if loaded is None:
        loaded = []
    payload["prior_outcomes"] = loaded


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in rows:
            _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": error})
        return
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": error})


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = dict(state)
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    _attach_priors(payload, questions)
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


_SPEC: tuple[tuple[str, str, str, tuple[str, ...] | None], ...] = (
    ("noul", "noul", "event_proximity", _NOUL_ORDER),
    ("abstain", "noul", "event_proximity_abstain", _NOUL_ORDER),
    ("decidable", "noul", "event_proximity_decidable", _NOUL_ORDER),
    ("reason", "choice", "event_proximity_reason", _REASON_ORDER),
    ("minutes_to_nearest_high", "score", "minutes_to_nearest_high", None),
    ("f5_pre_block_minutes", "score", "f5_pre_block_minutes", None),
    ("f5_post_block_minutes", "score", "f5_post_block_minutes", None),
    ("w7_pre_block_minutes", "score", "w7_pre_block_minutes", None),
    ("w7_post_block_minutes", "score", "w7_post_block_minutes", None),
    ("apply_persist", "score", "apply_persist", None),
)


def _decisions(asked: Mapping[str, Any]) -> dict[str, Any]:
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out: dict[str, Any] = {}
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in _SPEC:
        block = answers.get(qid)
        value = _pull(block, kind, order)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    posted = asked.get("state") if isinstance(asked.get("state"), Mapping) else {}
    _remember(posted, rows)
    return out


def _block(facts: Mapping[str, Any], decisions: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "question": "event_proximity",
        "ignore_if": None,
        "spine_empty": facts.get("spine_empty"),
        "decidable": decisions.get("decidable"),
        "abstain": decisions.get("abstain"),
        "noul": decisions.get("noul"),
        "minutes_to_nearest_high": decisions.get("minutes_to_nearest_high"),
        "spine_minutes_to_nearest_high": facts.get("minutes"),
        "high_in_f5_window": facts.get("f5"),
        "high_in_w7_window": facts.get("w7"),
        "flatten": False,
        "panic_flatten": False,
        "lens": STUDY_LENS,
        "NEWS_PROTOCOL_APPLIED": NEWS_PROTOCOL_APPLIED,
        "invented": False,
        "reason": decisions.get("reason"),
        "f5_pre_block_minutes": decisions.get("f5_pre_block_minutes"),
        "f5_post_block_minutes": decisions.get("f5_post_block_minutes"),
        "w7_pre_block_minutes": decisions.get("w7_pre_block_minutes"),
        "w7_post_block_minutes": decisions.get("w7_post_block_minutes"),
        "events": facts.get("events"),
        "apply_persist": decisions.get("apply_persist"),
    }


def event_proximity(
    as_of_utc: datetime | str,
    *,
    spines: dict[str, Any] | None = None,
    news: Mapping[str, Any] | None = None,
    symbol: str = "XAUUSD",
) -> dict[str, Any]:
    """Proximity for this as-of. Decisions and parameters are the return.

    Spine clock stays a fact. A miss leaves the decision unset. Does not flatten.
    Does not send.
    """

    moment = _as_of(as_of_utc)
    facts = _facts(_read_spine(moment, spines, news, symbol))
    try:
        questions = _questions(facts.get("minutes") if isinstance(facts.get("minutes"), float) else None)
    except Exception:
        return _block(facts, {})
    allowed = {"noul", "choice", "score"}
    if not questions or any(
        not isinstance(block, dict) or block.get("type") not in allowed for block in questions.values()
    ):
        return _block(facts, {})
    asked = _ask(_state(moment, symbol, facts), questions)
    return _block(facts, _decisions(asked))
