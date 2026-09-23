"""Walter stream + news_tape join — measured host receipts. No mill URL.

WATCH_V2: a connector reply is not a processed event. Host
``stream_health.json`` stamps ``do_not_restart: true``; last DeItaone
2026-09-08T08:32:44Z. Host ``news_tape.json`` as_of 2026-09-07 is occupancy
+ Walter, leftover. Do not revive it as a writer input. Do not invent a
DeItaone / headline-mill client. Do not bounce Challenge. Do not flatten.

The host paths, clocks, and ids are facts. Every decision on the receipt,
including each parameter, is one ``jev_client.evaluate`` return for this
state: model ``jev-1.13.0``, POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``. Questions are only Noul, Choice, or Score. Prior
outcomes are attached on the ask, and the return is stored for the next
ask. A Choice is the unique highest probability. A Score is the returned
number and may sit between levels. A Noul is a bool or a probability.
An empty answer, a tie, or an error leaves that field unset.

A floor and a baseline are not a question. This module does not send.
"""

from __future__ import annotations

from typing import Any, Mapping

MODEL = "jev-1.13.0"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
SCHEMA = "gtos.news.tape_join_receipt.v1"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

NEWS_PROTOCOL_APPLIED: bool | float | None = None

# Measured 2026-09-21 from host redacted_host via user@host:22.
# Paths are host facts, not invented endpoints. Recorded stamps are facts
# on the ask. They are not the decision.
HOST_STREAM_HEALTH = {
    "path": r"host-local\redacted_host\repo\judgment\state\stream_health.json",
    "status": "live",
    "as_of_utc": "2026-09-08T09:43:58Z",
    "do_not_restart": True,
    "last_walter_id": "2097241713966231883",
    "last_walter_ts": "2026-09-08T08:32:44.000Z",
    "last_walter_handle": "DeItaone",
    "wrapper": "/workspace/gtos/news/_run_stream.py",
    "freshness": "STALE_GAP_H_1.19",
    "honesty": "DeItaone silence != dead capture when ESTAB+wire LAND prove socket",
}

HOST_NEWS_TAPE = {
    "path": r"host-local\redacted_host\repo\judgment\state\news_tape.json",
    "schema": "gtos.live.news_tape.v1",
    "as_of_utc": "2026-09-07T06:26:15Z",
    "join_rule": "can_hold",
    "walter_handle": "DeItaone",
    "walter_last_id": "2096367296910389659",
    "walter_last_ts": "2026-09-05T22:38:06.000Z",
    "result_count_note": "leftover occupancy+Walter; excluded from Challenge compose",
}

HOST_NEWS_BRIEF = {
    "path": r"host-local\redacted_host\repo\data\news_brief.json",
    "as_of_utc": "2026-09-20T22:17:00Z",
    "NEWS_PROTOCOL_APPLIED": False,
    "spine_updated_utc": "20260920T222007Z",
}

MILL_URL = None
INVENTED_ENDPOINTS: tuple[str, ...] = ()

_WALTER_STATUS = ("stale", "live", "silent", "unassembled")
_TAPE_STATUS = ("stale", "leftover", "usable", "unassembled")
_JOIN_RULE = ("can_hold", "withhold", "exclude")
_PROCESS_STATUS = ("live", "stale", "absent")
_COMPONENT = ("walter", "news_tape", "news_brief")
_NOUL_ORDER = ("true", "false")
_CHOICE_ORDER = {
    "walter_status": _WALTER_STATUS,
    "news_tape_status": _TAPE_STATUS,
    "join_rule": _JOIN_RULE,
    "process_status": _PROCESS_STATUS,
    "which_component": _COMPONENT,
}
_NOUL_IDS = (
    "state_sufficient",
    "news_protocol_applied",
    "walter_present",
    "usable_as_writer_input",
    "do_not_restart",
    "do_not_bounce_challenge",
    "do_not_flatten",
    "component_exists",
)
_SCORE_IDS = (
    "apply_persist",
    "tape_join_threshold",
    "tape_join_loop_bound",
    "tape_join_parameter",
)
_DECISION_IDS = frozenset((*_CHOICE_ORDER, *_NOUL_IDS, *_SCORE_IDS))
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


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS or token in _DECISION_IDS:
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
    """Drop limit keys and decision ids before the ask."""

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


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        raw = block.get("Probabilities")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: dict[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision. A miss is not zero."""

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
    if choice not in order or _unique(probs, order) != choice:
        choice = None
    return choice, kept


def _score_of(block: Any) -> float | None:
    """The score that came back. It is not snapped to a level."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    has_score = "score" in block
    number = _finite(block.get("score")) if has_score else None
    if has_score and number is None:
        return None
    try:
        from .jev_questions import returned_number

        parsed = _finite(returned_number(block))
    except Exception:
        parsed = number
    if has_score:
        if parsed is None or parsed != number:
            return None
        return number
    return parsed


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A missing noul stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        raw = block.get("noul") if "noul" in block else block.get("Noul")
        if raw is None:
            return None
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
    if receipt_error not in (None, ""):
        return str(receipt_error)
    probs = _probs(block)
    if probs and _unique(probs, order or tuple(probs)) is None:
        return "tie"
    return "empty"


def _choice_question(qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {key: _scrub_text(val) for key, val in criteria.items() if not _limit_key(str(key))}
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
                shaped["criteria"] = [_scrub_text(str(item)) for item in criteria if not _limit_key(str(item))]
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
    """One pack. Types are noul, choice, or score. The pack does not decide."""

    unset = "An empty answer or a tie leaves it unset. This ask does not transmit an order."
    pack: dict[str, Any] = {}
    pack.update(
        _noul_question(
            "state_sufficient",
            "Is this Walter and news-tape state complete enough to judge? " + unset,
            "This state is complete enough to judge.",
            "A named piece of this state is missing.",
        )
    )
    pack.update(
        _noul_question(
            "news_protocol_applied",
            "Is the news protocol applied for this state? "
            "The host brief stamp is a fact. The noul you return is the decision. " + unset,
            "The news protocol is applied for this state.",
            "The news protocol is not applied for this state.",
        )
    )
    pack.update(
        _noul_question(
            "walter_present",
            "Is the Walter stream present for this state? " + unset,
            "The Walter stream is present.",
            "The Walter stream is not present.",
        )
    )
    pack.update(
        _noul_question(
            "usable_as_writer_input",
            "Is this news tape usable as a writer input for this state? " + unset,
            "This news tape is usable as a writer input.",
            "This news tape is not usable as a writer input.",
        )
    )
    pack.update(
        _noul_question(
            "do_not_restart",
            "Does this state keep the Walter stream from being restarted? "
            "The host stamp is a fact. The noul you return is the decision. " + unset,
            "Keep the Walter stream from being restarted.",
            "Restarting the Walter stream is open for this state.",
        )
    )
    pack.update(
        _noul_question(
            "do_not_bounce_challenge",
            "Does this state keep Challenge from being bounced? " + unset,
            "Keep Challenge from being bounced.",
            "Bouncing Challenge is open for this state.",
        )
    )
    pack.update(
        _noul_question(
            "do_not_flatten",
            "Does this state keep the book from a flatten? " + unset,
            "Keep the book from a flatten.",
            "A flatten is open for this state.",
        )
    )
    pack.update(
        _noul_question(
            "component_exists",
            "Does the component named for this tape join exist on this state? " + unset,
            "That component exists on this state.",
            "That component does not exist on this state.",
        )
    )
    pack.update(
        _choice_question(
            "walter_status",
            "What is the Walter stream status for this state? "
            "The host file status is a fact. "
            "The option with the single highest probability is the status. " + unset,
            {
                "stale": "The Walter stream on this state is stale.",
                "live": "The Walter stream on this state is live.",
                "silent": "The Walter capture is quiet on this state.",
                "unassembled": "The Walter stream on this state is not assembled.",
            },
        )
    )
    pack.update(
        _choice_question(
            "process_status",
            "What is the Walter process status for this state? "
            "The host file status is a fact. "
            "The option with the single highest probability is the status. " + unset,
            {
                "live": "The Walter process on this state is live.",
                "stale": "The Walter process on this state is stale.",
                "absent": "The Walter process on this state is absent.",
            },
        )
    )
    pack.update(
        _choice_question(
            "news_tape_status",
            "What is the news tape status for this state? "
            "The host tape is a fact. "
            "The option with the single highest probability is the status. " + unset,
            {
                "stale": "The news tape on this state is stale.",
                "leftover": "The news tape on this state is leftover occupancy and Walter.",
                "usable": "The news tape on this state is usable.",
                "unassembled": "The news tape on this state is not assembled.",
            },
        )
    )
    pack.update(
        _choice_question(
            "join_rule",
            "What join rule is this state? "
            "The host tape rule is a fact. "
            "The option with the single highest probability is the rule. " + unset,
            {
                "can_hold": "This join can hold.",
                "withhold": "This join withholds.",
                "exclude": "This join excludes the news tape.",
            },
        )
    )
    pack.update(
        _choice_question(
            "which_component",
            "Which component is this tape join? "
            "The option with the single highest probability is the component. " + unset,
            {
                "walter": "The Walter stream is the component.",
                "news_tape": "The news tape is the component.",
                "news_brief": "The news brief is the component.",
            },
        )
    )
    pack.update(
        _score_question(
            "apply_persist",
            "What persist applies to this news tape join? "
            "The score you return is that persist. "
            "It may sit between levels. "
            "An empty score leaves persist unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _score_question(
            "tape_join_threshold",
            "What threshold applies to this news tape join? "
            "The score you return is that threshold. "
            "It may sit between levels. "
            "An empty score leaves the threshold unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _score_question(
            "tape_join_loop_bound",
            "What loop bound applies to this news tape join? "
            "The score you return is that bound. "
            "It may sit between levels. "
            "An empty score leaves the bound unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _score_question(
            "tape_join_parameter",
            "What parameter applies to this news tape join? "
            "The score you return is that parameter. "
            "It may sit between levels. "
            "An empty score leaves the parameter unset. "
            "This ask does not transmit an order.",
        )
    )
    return pack


def _measured_state() -> dict[str, Any]:
    stream = HOST_STREAM_HEALTH
    tape = HOST_NEWS_TAPE
    brief = HOST_NEWS_BRIEF
    body: dict[str, Any] = {
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "ns": CHALLENGE_NS,
        "mill_url": MILL_URL,
        "measured_stream_health": {
            "path": stream.get("path"),
            "recorded_status": stream.get("status"),
            "as_of_utc": stream.get("as_of_utc"),
            "recorded_do_not_restart": stream.get("do_not_restart"),
            "last_walter_id": stream.get("last_walter_id"),
            "last_walter_ts": stream.get("last_walter_ts"),
            "last_walter_handle": stream.get("last_walter_handle"),
            "wrapper": stream.get("wrapper"),
            "recorded_freshness": stream.get("freshness"),
            "honesty": stream.get("honesty"),
        },
        "measured_news_tape": {
            "path": tape.get("path"),
            "schema": tape.get("schema"),
            "as_of_utc": tape.get("as_of_utc"),
            "recorded_join_rule": tape.get("join_rule"),
            "walter_handle": tape.get("walter_handle"),
            "walter_last_id": tape.get("walter_last_id"),
            "walter_last_ts": tape.get("walter_last_ts"),
            "result_count_note": tape.get("result_count_note"),
        },
        "measured_news_brief": {
            "path": brief.get("path"),
            "as_of_utc": brief.get("as_of_utc"),
            "recorded_news_protocol_applied": brief.get("NEWS_PROTOCOL_APPLIED"),
            "spine_updated_utc": brief.get("spine_updated_utc"),
        },
    }
    scrubbed = _scrub(body)
    return scrubbed if isinstance(scrubbed, dict) else body


def _endpoint() -> str:
    try:
        from .jev_client import API_URL

        return str(API_URL)
    except Exception:
        return ENDPOINT


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=dict(questions))
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    state["prior_outcomes"] = loaded if loaded is not None else []


def _remember(state: Mapping[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in rows:
            _LOCAL_OUTCOMES.append(
                {
                    "spot": key,
                    "value": value,
                    "error": error,
                }
            )
        return
    for key, value, error in rows:
        try:
            append_outcome(key, value if isinstance(value, (int, float)) and not isinstance(value, bool) else None, logged, error=error)
        except Exception:
            return


def _post(state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
    """One evaluate. No second client."""

    from .jev_client import evaluate

    receipt = evaluate(
        state,
        questions=questions,
        merge_sleeve=False,
        model=MODEL,
    )
    return receipt if isinstance(receipt, dict) else {}


def _ask(state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
    payload = dict(state)
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    _attach_priors(payload, questions)
    try:
        receipt = _post(payload, questions)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {
            "error": type(exc).__name__,
            "answers": {},
            "state": payload,
            "model": MODEL,
            "endpoint": _endpoint(),
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
        "endpoint": _endpoint(),
    }


def _read(answers: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    decisions: dict[str, Any] = {}
    probabilities: dict[str, Any] = {}
    for key, order in _CHOICE_ORDER.items():
        choice, probs = _choice_of(answers.get(key), order)
        decisions[key] = choice
        probabilities[key] = probs
    for key in _NOUL_IDS:
        decisions[key] = _noul_of(answers.get(key))
    for key in _SCORE_IDS:
        decisions[key] = _score_of(answers.get(key))
    return decisions, probabilities


def _remember_rows(
    answers: Mapping[str, Any],
    decisions: Mapping[str, Any],
    receipt_error: Any,
) -> list[tuple[str, Any, str | None]]:
    rows: list[tuple[str, Any, str | None]] = []
    for key, order in _CHOICE_ORDER.items():
        value = decisions.get(key)
        rows.append((key, value, _miss(answers.get(key), value, order, receipt_error)))
    for key in _NOUL_IDS:
        value = decisions.get(key)
        rows.append((key, value, _miss(answers.get(key), value, _NOUL_ORDER, receipt_error)))
    for key in _SCORE_IDS:
        value = decisions.get(key)
        rows.append((key, value, _miss(answers.get(key), value, (), receipt_error)))
    return rows


def _receipt(
    decisions: Mapping[str, Any] | None = None,
    *,
    error: str | None = None,
    probabilities: Mapping[str, Any] | None = None,
    model: str = MODEL,
    endpoint: str = ENDPOINT,
) -> dict[str, Any]:
    picked = decisions if isinstance(decisions, Mapping) else {}
    stream = HOST_STREAM_HEALTH
    tape = HOST_NEWS_TAPE
    brief = HOST_NEWS_BRIEF
    protocol = picked.get("news_protocol_applied")
    return {
        "schema": SCHEMA,
        "model": model,
        "endpoint": endpoint,
        "invented": False,
        "NEWS_PROTOCOL_APPLIED": protocol,
        "mill_url": MILL_URL,
        "invented_endpoints": list(INVENTED_ENDPOINTS),
        "broker_effect": False,
        "do_not_restart": picked.get("do_not_restart"),
        "do_not_bounce_challenge": picked.get("do_not_bounce_challenge"),
        "do_not_flatten": picked.get("do_not_flatten"),
        "state_sufficient": picked.get("state_sufficient"),
        "which_component": picked.get("which_component"),
        "component_exists": picked.get("component_exists"),
        "apply_persist": picked.get("apply_persist"),
        "threshold": picked.get("tape_join_threshold"),
        "loop_bound": picked.get("tape_join_loop_bound"),
        "parameter": picked.get("tape_join_parameter"),
        "probabilities": dict(probabilities or {}),
        "error": error,
        "walter": {
            "path": stream.get("path"),
            "as_of_utc": stream.get("as_of_utc"),
            "last_walter_id": stream.get("last_walter_id"),
            "last_walter_ts": stream.get("last_walter_ts"),
            "last_walter_handle": stream.get("last_walter_handle"),
            "wrapper": stream.get("wrapper"),
            "honesty": stream.get("honesty"),
            "recorded_status": stream.get("status"),
            "recorded_do_not_restart": stream.get("do_not_restart"),
            "recorded_freshness": stream.get("freshness"),
            "present": picked.get("walter_present"),
            "process_status": picked.get("process_status"),
            "status": picked.get("walter_status"),
        },
        "news_tape": {
            "path": tape.get("path"),
            "schema": tape.get("schema"),
            "as_of_utc": tape.get("as_of_utc"),
            "walter_handle": tape.get("walter_handle"),
            "walter_last_id": tape.get("walter_last_id"),
            "walter_last_ts": tape.get("walter_last_ts"),
            "result_count_note": tape.get("result_count_note"),
            "recorded_join_rule": tape.get("join_rule"),
            "usable_as_writer_input": picked.get("usable_as_writer_input"),
            "status": picked.get("news_tape_status"),
            "join_rule": picked.get("join_rule"),
        },
        "news_brief": {
            "path": brief.get("path"),
            "as_of_utc": brief.get("as_of_utc"),
            "spine_updated_utc": brief.get("spine_updated_utc"),
            "recorded_news_protocol_applied": brief.get("NEWS_PROTOCOL_APPLIED"),
            "NEWS_PROTOCOL_APPLIED": protocol,
        },
    }


def _join_card() -> dict[str, Any]:
    try:
        questions = _questions()
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return _receipt(error=type(exc).__name__)
    allowed = {"choice", "noul", "score"}
    if not questions or any(
        not isinstance(block, dict) or block.get("type") not in allowed for block in questions.values()
    ):
        return _receipt(error="question_pack_fail")
    payload = _measured_state()
    asked = _ask(payload, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    decisions, probabilities = _read(answers)
    receipt_error = asked.get("error")
    posted = asked.get("state") if isinstance(asked.get("state"), dict) else payload
    _remember(posted, _remember_rows(answers, decisions, receipt_error))
    model = asked.get("model") if isinstance(asked.get("model"), str) else MODEL
    endpoint = asked.get("endpoint") if isinstance(asked.get("endpoint"), str) else ENDPOINT
    error = str(receipt_error) if receipt_error not in (None, "") and not answers else None
    return _receipt(
        decisions,
        error=error,
        probabilities=probabilities,
        model=model,
        endpoint=endpoint,
    )


def tape_join_status() -> dict[str, Any]:
    """Join receipt for this state. A miss leaves each decision unset."""

    global NEWS_PROTOCOL_APPLIED
    try:
        card = _join_card()
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        card = _receipt(error=type(exc).__name__)
    NEWS_PROTOCOL_APPLIED = card.get("NEWS_PROTOCOL_APPLIED")
    return card
