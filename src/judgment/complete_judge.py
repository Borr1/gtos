"""STATIC→Jev complete-judge over COMPLETE_STATE.

Envelope facts stay facts: identity, prop walls, and a hard-off or KEEP
flag already on the state. Every residual, chair label, and parameter
is the System One return for this state. One hop: ``jev_client.evaluate``
with model ``jev-1.13.0`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``). Questions are only a Noul, a Choice, or a Score.
Prior outcomes are attached on the ask, and the return is stored for the
next ask.

An empty answer, a tie, a missing score, or an error leaves that return
unset. A floor and a baseline are not a question. This module does not
send an order, does not flatten, and does not apply a size ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

SCHEMA = "gtos.judgment.complete_judge.v1"
STEAL = "COMPLETE_JUDGE"
LOGIN = "0"
CHALLENGE_NS = "operator"
MODEL = "jev-1.13.0"

ADMIT_RESIDUAL_CRITERIA = {
    "envelope_hard_off": (
        "A writer or chair hard-off is already named on this state. "
        "Label that envelope. Do not invent a family."
    ),
    "state_insufficient": (
        "Completeness marks this live state insufficient. "
        "Residual abstain label. Do not flip an admit verb."
    ),
    "last_refusal": (
        "Occupancy names a last refusal of cost or other. Residual label."
    ),
    "low_confidence": (
        "An admit choice is present and the confidence on this state is the low band. "
        "The admit verb abstains."
    ),
    "injected": (
        "A typed admit choice is present and the state is not envelope-blocked."
    ),
    "unanswered": (
        "No admit choice is on this state and no envelope hard-off is named. "
        "This option is a returned choice. An empty answer is not this option."
    ),
}

G4_SOFT_CRITERIA = {
    "APPLY_CUT_0_5": (
        "g4 applies and this sleeve is not KEEP. Label only. Do not apply a size ceiling."
    ),
    "KEEP_EXEMPT": "KEEP family while g4 applies. G4 does not cut KEEP.",
    "NOT_APPLICABLE": "g4 applies is not set, or it does not apply, on this state.",
}

G6_SOFT_CRITERIA = {
    "APPLY_CUT_0_75": (
        "The named session is a cut session and this sleeve is not KEEP. "
        "Label only. Do not apply a size ceiling."
    ),
    "KEEP_EXEMPT": "KEEP family in a cut session.",
    "LEAVE_ALONE": "The named session is a leave-alone session.",
    "NOT_APPLICABLE": "The session is unnamed, empty, or neither a cut nor a leave-alone.",
}

ADMIT_RESIDUAL_IDS = tuple(ADMIT_RESIDUAL_CRITERIA)
G4_SOFT_IDS = tuple(G4_SOFT_CRITERIA)
G6_SOFT_IDS = tuple(G6_SOFT_CRITERIA)
_NOUL_ORDER = ("true", "false")
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LIMIT_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "floor_room",
})
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
_STRUCTURAL = frozenset({
    "model",
    "login",
    "ns",
    "namespace",
    "schema",
    "steal",
    "never_place",
    "never_remint",
    "never_flatten",
    "news_protocol",
    "size_ceiling_apply",
    "fire_rate_apply",
    "broker_effect",
    "apply",
})
_Q_ADMIT = "admit_residual"
_Q_G4 = "chair_soft_g4"
_Q_G6 = "chair_soft_g6"
_Q_G8 = "chair_soft_g8"
_Q_ADMIT_PARAMETER = "admit_residual_parameter"
_Q_G4_PARAMETER = "chair_soft_g4_parameter"
_Q_G6_PARAMETER = "chair_soft_g6_parameter"
_Q_G8_PARAMETER = "chair_soft_g8_parameter"
_QUESTION_IDS = (
    _Q_ADMIT,
    _Q_G4,
    _Q_G6,
    _Q_G8,
    _Q_ADMIT_PARAMETER,
    _Q_G4_PARAMETER,
    _Q_G6_PARAMETER,
    _Q_G8_PARAMETER,
)
_ALLOWED_TYPES = frozenset({"noul", "choice", "score"})


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED_TEXT)


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


_DROP = object()


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before the ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            cleaned = _scrub(item)
            if cleaned is _DROP:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        kept = []
        for item in value:
            cleaned = _scrub(item)
            if cleaned is not _DROP:
                kept.append(cleaned)
        return kept
    if isinstance(value, str):
        if _banned_text(value) or _limit_key(value):
            return _DROP
        return _scrub_text(value)
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if _banned_text(format(value, ".10g")):
            return _DROP
        return value
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


def _identity(gold: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(gold, Mapping):
        return {}
    ident = gold.get("identity")
    return dict(ident) if isinstance(ident, Mapping) else {}


def _occupancy(gold: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(gold, Mapping):
        return {}
    occ = gold.get("occupancy")
    return dict(occ) if isinstance(occ, Mapping) else {}


def _completeness(gold: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(gold, Mapping):
        return {}
    raw = gold.get("completeness")
    return dict(raw) if isinstance(raw, Mapping) else {}


def _sessions_named(gold: Mapping[str, Any] | None) -> str | None:
    if not isinstance(gold, Mapping):
        return None
    sess = gold.get("sessions")
    if not isinstance(sess, Mapping):
        return None
    named = sess.get("named")
    text = str(named or "").strip()
    return text or None


def _carried(gold: Mapping[str, Any] | None, key: str) -> Any:
    """A fact already on this state. Looking it up does not ask."""

    if isinstance(gold, Mapping) and key in gold:
        return gold.get(key)
    ident = _identity(gold)
    if key in ident:
        return ident.get(key)
    return None


def _carried_text(gold: Mapping[str, Any] | None, key: str) -> str | None:
    raw = _carried(gold, key)
    if raw is None or isinstance(raw, bool):
        return None
    text = str(raw).strip()
    return text or None


def _carried_bool(gold: Mapping[str, Any] | None, key: str) -> bool | None:
    raw = _carried(gold, key)
    if isinstance(raw, bool):
        return raw
    return None


def named_last_refusal(gold_state: Mapping[str, Any] | None) -> str | None:
    """Return ``cost`` or ``other`` when occupancy already names that class."""

    text = str(_occupancy(gold_state).get("last_refusal_class") or "").strip().lower()
    if text in {"cost", "other"}:
        return text
    return None


def state_sufficient_for_live(gold_state: Mapping[str, Any] | None) -> bool | None:
    raw = _completeness(gold_state).get("state_sufficient_for_live")
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    return bool(raw)


def g4_applies_from_state(
    gold_state: Mapping[str, Any] | None,
    *,
    explicit: bool | None = None,
) -> bool | None:
    """The g4 fact on this state. A missing flag stays missing."""

    if explicit is not None:
        return bool(explicit)
    ident = _identity(gold_state)
    if "g4_applies" in ident:
        raw = ident.get("g4_applies")
        return None if raw is None else bool(raw)
    if isinstance(gold_state, Mapping) and "g4_applies" in gold_state:
        raw = gold_state.get("g4_applies")
        return None if raw is None else bool(raw)
    return None


def _facts(
    gold_state: Mapping[str, Any] | None,
    *,
    g4_applies: bool | None = None,
    admit_choice: str | None = None,
    admit_conf: float | None = None,
) -> dict[str, Any]:
    """Envelope slice posted with the ask. Labels are not decided here."""

    ident = _identity(gold_state)
    sleeve = str(ident.get("sleeve") or "") or None
    symbol = str(ident.get("symbol") or "") or None
    g4 = g4_applies_from_state(gold_state, explicit=g4_applies)
    occ = _occupancy(gold_state)
    raw_refusal = occ.get("last_refusal_class")
    session = _sessions_named(gold_state)
    missing = _completeness(gold_state).get("missing_fields") or []
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "login": LOGIN,
        "ns": CHALLENGE_NS,
        "identity": {
            "sleeve": sleeve,
            "symbol": symbol,
            "ticket": ident.get("ticket"),
            "g4_applies": g4,
        },
        "completeness": {
            "state_sufficient_for_live": state_sufficient_for_live(gold_state),
            "missing_fields": list(missing) if isinstance(missing, (list, tuple)) else [],
        },
        "sessions": {"named": session},
        "occupancy": {
            "already_placed_today": occ.get("already_placed_today"),
            "minutes_since_flat": occ.get("minutes_since_flat"),
            "new_named_fire": occ.get("new_named_fire"),
            "same_sleeve_reentry": occ.get("same_sleeve_reentry"),
            "last_refusal_class": named_last_refusal(gold_state),
            "last_refusal_text": None if raw_refusal is None else str(raw_refusal),
        },
        "keep_family": _carried_bool(gold_state, "keep_family"),
        "hard_off_reason": _carried_text(gold_state, "hard_off_reason"),
        "injected_admit": {
            "choice": None if admit_choice is None else str(admit_choice),
            "confidence": admit_conf,
        },
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "news_protocol": "stamps_only_never_invent",
        "size_ceiling_apply": False,
        "fire_rate_apply": False,
    }


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numbers already on the facts. A score may sit between them."""

    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        if _limit_key(key) or key.strip().lower() in _STRUCTURAL:
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(str(child_key), child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            for item in value:
                walk(key, item)
            return
        number = _finite(value)
        if number is None:
            return
        text = format(number, ".10g")
        if _banned_text(text):
            return
        found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    if not found:
        return list(_BETWEEN)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {
        str(key): _scrub_text(str(val))
        for key, val in criteria.items()
        if not _limit_key(str(key))
    }
    body: dict[str, Any] = {"type": "choice", "instructions": text, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, cleaned)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
                shaped.pop(key, None)
            shaped["type"] = "choice"
            shaped["instructions"] = text
            shaped["criteria"] = cleaned
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, instructions: str, levels: list[str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    criteria = [_scrub_text(str(item)) for item in levels] if levels else list(_BETWEEN)
    body: dict[str, Any] = {"type": "score", "instructions": text, "criteria": criteria}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, text)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
                shaped.pop(key, None)
            shaped["type"] = "score"
            shaped["instructions"] = text
            shaped["criteria"] = criteria
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


def _score_text(noun: str) -> str:
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels on this state. "
        "An empty score leaves it unset. "
        "Do not send an order. Do not flatten."
    )


def _questions(levels: list[str]) -> dict[str, Any]:
    """One pack. Types are choice, noul, or score."""

    scale = list(levels) if levels else list(_BETWEEN)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        _Q_ADMIT,
        (
            "Name the residual on this Challenge admit path from the facts on this state. "
            "The unique highest probability is the decision. "
            "An empty answer or a tie is not a decision. "
            "Do not send an order. Do not flatten."
        ),
        ADMIT_RESIDUAL_CRITERIA,
    ))
    pack.update(_choice_question(
        _Q_G4,
        (
            "Chair G4 soft path for this state. "
            "The unique highest probability is the label. "
            "An empty answer or a tie is not a label. "
            "Do not apply a size ceiling. Do not send an order."
        ),
        G4_SOFT_CRITERIA,
    ))
    pack.update(_choice_question(
        _Q_G6,
        (
            "Chair G6 soft path for the named session on this state. "
            "The unique highest probability is the label. "
            "An empty answer or a tie is not a label. "
            "Do not apply a size ceiling. Do not send an order."
        ),
        G6_SOFT_CRITERIA,
    ))
    pack.update(_noul_question(
        _Q_G8,
        (
            "P(block same-sleeve reentry) from the occupancy facts on this state. "
            "The noul you return is that answer. "
            "An empty answer leaves it unset. "
            "Do not place. Do not send an order."
        ),
        "Block same-sleeve reentry.",
        "Do not block same-sleeve reentry.",
    ))
    pack.update(_score_question(_Q_ADMIT_PARAMETER, _score_text("admit residual parameter"), scale))
    pack.update(_score_question(_Q_G4_PARAMETER, _score_text("chair G4 parameter"), scale))
    pack.update(_score_question(_Q_G6_PARAMETER, _score_text("chair G6 parameter"), scale))
    pack.update(_score_question(_Q_G8_PARAMETER, _score_text("chair G8 parameter"), scale))
    return pack


def _questions_ok(questions: Mapping[str, Any]) -> bool:
    if not questions:
        return False
    blob = str(questions).lower()
    if "floor" in blob or "baseline" in blob or _banned_text(blob):
        return False
    for block in questions.values():
        if not isinstance(block, dict):
            return False
        if str(block.get("type") or "").strip().lower() not in _ALLOWED_TYPES:
            return False
    return True


COMPLETE_JUDGE_QUESTION_PACK: dict[str, dict[str, Any]] = _questions(list(_BETWEEN))
COMPLETE_JUDGE_QUESTION_IDS: tuple[str, ...] = tuple(COMPLETE_JUDGE_QUESTION_PACK)


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision. A missing probability is not zero."""

    if not probs:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    allowed = order or tuple(probs)
    seen = False
    for name in allowed:
        if name not in probs:
            continue
        seen = True
        p = probs[name]
        if best_p is None or p > best_p + 1e-12:
            best = str(name)
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _tied(probs: Mapping[str, float], order: tuple[str, ...]) -> bool:
    if not probs:
        return False
    best_p: float | None = None
    count = 0
    allowed = order or tuple(probs)
    for name in allowed:
        if name not in probs:
            continue
        p = probs[name]
        if best_p is None or p > best_p + 1e-12:
            best_p = p
            count = 1
        elif abs(p - best_p) <= 1e-12:
            count += 1
    return count >= 2


def _choice_of(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
    if not isinstance(block, Mapping) or block.get("error"):
        return None, {}
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "choice":
        return None, {}
    probs = _probs(block)
    kept = {name: probs[name] for name in order if name in probs}
    if not kept:
        return None, {}
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(kept, order)
    except Exception:
        picked = _unique(kept, order)
    if picked not in order:
        return None, kept
    return str(picked), kept


def _score_of(block: Any) -> float | None:
    """The score that came back. It is not snapped to a level."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "score":
        return None
    number = None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = block.get("score") if "score" in block else None
    return _finite(number)


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A float is not cut at a line."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "noul":
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _unique(_probs(block), _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _miss(block: Any, value: Any, order: tuple[str, ...], receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = _probs(block)
    if _tied(probs, order):
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _ask(state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state))
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = None
    if loaded is None:
        payload["prior_outcomes"] = []
    else:
        cleaned = _scrub(loaded)
        payload["prior_outcomes"] = [] if cleaned is None else cleaned
    try:
        from .jev_client import evaluate

        receipt = evaluate(
            payload,
            questions=dict(questions),
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
        "calls_used": receipt.get("calls_used"),
        "calls_remaining": receipt.get("calls_remaining"),
    }


def _remember(state: Mapping[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
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


def _blank_decisions(error: str | None) -> dict[str, Any]:
    return {
        "admit_residual": None,
        "admit_residual_probabilities": {},
        "admit_residual_decidable": False,
        "admit_residual_parameter": None,
        "chair_soft_g4": None,
        "chair_soft_g4_probabilities": {},
        "chair_soft_g4_parameter": None,
        "chair_soft_g6": None,
        "chair_soft_g6_probabilities": {},
        "chair_soft_g6_parameter": None,
        "chair_soft_g8": None,
        "chair_soft_g8_parameter": None,
        "complete_judge_error": error,
    }


def _read(answers: Mapping[str, Any], error: str | None) -> dict[str, Any]:
    residual, residual_probs = _choice_of(answers.get(_Q_ADMIT), ADMIT_RESIDUAL_IDS)
    g4, g4_probs = _choice_of(answers.get(_Q_G4), G4_SOFT_IDS)
    g6, g6_probs = _choice_of(answers.get(_Q_G6), G6_SOFT_IDS)
    g8 = _noul_of(answers.get(_Q_G8))
    admit_parameter = _score_of(answers.get(_Q_ADMIT_PARAMETER))
    g4_parameter = _score_of(answers.get(_Q_G4_PARAMETER))
    g6_parameter = _score_of(answers.get(_Q_G6_PARAMETER))
    g8_parameter = _score_of(answers.get(_Q_G8_PARAMETER))
    missing = any(
        item is None
        for item in (
            residual,
            g4,
            g6,
            g8,
            admit_parameter,
            g4_parameter,
            g6_parameter,
            g8_parameter,
        )
    )
    return {
        "admit_residual": residual,
        "admit_residual_probabilities": residual_probs,
        "admit_residual_decidable": residual is not None,
        "admit_residual_parameter": admit_parameter,
        "chair_soft_g4": g4,
        "chair_soft_g4_probabilities": g4_probs,
        "chair_soft_g4_parameter": g4_parameter,
        "chair_soft_g6": g6,
        "chair_soft_g6_probabilities": g6_probs,
        "chair_soft_g6_parameter": g6_parameter,
        "chair_soft_g8": g8,
        "chair_soft_g8_parameter": g8_parameter,
        "complete_judge_error": error if missing and error else None,
    }


def _g8_label(noul: bool | float | None) -> str | None:
    if noul is True:
        return "block"
    if noul is False:
        return "allow"
    return None


def _card(
    gold_state: Mapping[str, Any] | None,
    *,
    g4_applies: bool | None = None,
    admit_choice: str | None = None,
    admit_conf: float | None = None,
) -> dict[str, Any]:
    """One ask for this state. A miss stays unset."""

    raw_facts = _facts(
        gold_state,
        g4_applies=g4_applies,
        admit_choice=admit_choice,
        admit_conf=admit_conf,
    )
    scrubbed = _scrub(raw_facts)
    facts = scrubbed if isinstance(scrubbed, dict) else {}
    try:
        questions = _questions(_levels(facts))
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        decisions = _blank_decisions(type(exc).__name__)
        return {"facts": facts, "decisions": decisions, "answers": {}, "asked": {}}
    if not _questions_ok(questions):
        decisions = _blank_decisions("question_rejected")
        return {"facts": facts, "decisions": decisions, "answers": {}, "asked": {}}
    asked = _ask(facts, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    receipt_error = asked.get("error")
    decisions = _read(answers, None if receipt_error in (None, "") else str(receipt_error))
    rows = [
        (
            _Q_ADMIT,
            decisions["admit_residual"],
            _miss(answers.get(_Q_ADMIT), decisions["admit_residual"], ADMIT_RESIDUAL_IDS, receipt_error),
        ),
        (
            _Q_G4,
            decisions["chair_soft_g4"],
            _miss(answers.get(_Q_G4), decisions["chair_soft_g4"], G4_SOFT_IDS, receipt_error),
        ),
        (
            _Q_G6,
            decisions["chair_soft_g6"],
            _miss(answers.get(_Q_G6), decisions["chair_soft_g6"], G6_SOFT_IDS, receipt_error),
        ),
        (
            _Q_G8,
            decisions["chair_soft_g8"],
            _miss(answers.get(_Q_G8), decisions["chair_soft_g8"], _NOUL_ORDER, receipt_error),
        ),
        (
            _Q_ADMIT_PARAMETER,
            decisions["admit_residual_parameter"],
            _miss(answers.get(_Q_ADMIT_PARAMETER), decisions["admit_residual_parameter"], (), receipt_error),
        ),
        (
            _Q_G4_PARAMETER,
            decisions["chair_soft_g4_parameter"],
            _miss(answers.get(_Q_G4_PARAMETER), decisions["chair_soft_g4_parameter"], (), receipt_error),
        ),
        (
            _Q_G6_PARAMETER,
            decisions["chair_soft_g6_parameter"],
            _miss(answers.get(_Q_G6_PARAMETER), decisions["chair_soft_g6_parameter"], (), receipt_error),
        ),
        (
            _Q_G8_PARAMETER,
            decisions["chair_soft_g8_parameter"],
            _miss(answers.get(_Q_G8_PARAMETER), decisions["chair_soft_g8_parameter"], (), receipt_error),
        ),
    ]
    posted = asked.get("state") if isinstance(asked.get("state"), dict) else facts
    _remember(posted, rows)
    return {"facts": facts, "decisions": decisions, "answers": answers, "asked": asked}


def _view_from_card(card: Mapping[str, Any]) -> dict[str, Any]:
    facts = dict(card.get("facts") or {})
    decisions = dict(card.get("decisions") or {})
    asked = card.get("asked") if isinstance(card.get("asked"), Mapping) else {}
    view = dict(facts)
    view.update(decisions)
    view["model"] = asked.get("model") or MODEL
    view["broker_effect"] = False
    return view


def admit_residual_choice(
    gold_state: Mapping[str, Any] | None,
    *,
    admit_choice: str | None = None,
    admit_conf: float | None = None,
) -> tuple[str | None, bool]:
    """The residual choice on this state, and whether that return arrived.

    Does not invent a hard-off family. An empty answer, a tie, or an error
    leaves the residual unset.
    """

    card = _card(
        gold_state,
        admit_choice=admit_choice,
        admit_conf=admit_conf,
    )
    decisions = card["decisions"]
    residual = decisions.get("admit_residual")
    return (str(residual) if residual is not None else None), bool(decisions.get("admit_residual_decidable"))


def complete_state_view(
    gold_state: Mapping[str, Any] | None,
    *,
    g4_applies: bool | None = None,
    admit_choice: str | None = None,
    admit_conf: float | None = None,
) -> dict[str, Any]:
    """COMPLETE_STATE slice. Decisions and parameters are the return for this state."""

    card = _card(
        gold_state,
        g4_applies=g4_applies,
        admit_choice=admit_choice,
        admit_conf=admit_conf,
    )
    return _view_from_card(card)


def _choice_block(name: str | None, probs: Mapping[str, float]) -> dict[str, Any] | None:
    if name is None:
        return None
    return {"choice": name, "probabilities": {str(key): float(val) for key, val in probs.items()}}


def _noul_block(value: bool | float | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {"noul": value}


def _score_block(value: float | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {"score": value}


def inject_complete_judge_answers(
    gold_state: Mapping[str, Any] | None,
    *,
    g4_applies: bool | None = None,
    admit_choice: str | None = None,
    admit_conf: float | None = None,
) -> dict[str, Any]:
    """Answer blocks from the System One return. A miss is None."""

    decisions = _card(
        gold_state,
        g4_applies=g4_applies,
        admit_choice=admit_choice,
        admit_conf=admit_conf,
    )["decisions"]
    return {
        _Q_ADMIT: _choice_block(
            decisions.get("admit_residual"),
            decisions.get("admit_residual_probabilities") or {},
        ),
        _Q_G4: _choice_block(
            decisions.get("chair_soft_g4"),
            decisions.get("chair_soft_g4_probabilities") or {},
        ),
        _Q_G6: _choice_block(
            decisions.get("chair_soft_g6"),
            decisions.get("chair_soft_g6_probabilities") or {},
        ),
        _Q_G8: _noul_block(decisions.get("chair_soft_g8")),
        _Q_ADMIT_PARAMETER: _score_block(decisions.get("admit_residual_parameter")),
        _Q_G4_PARAMETER: _score_block(decisions.get("chair_soft_g4_parameter")),
        _Q_G6_PARAMETER: _score_block(decisions.get("chair_soft_g6_parameter")),
        _Q_G8_PARAMETER: _score_block(decisions.get("chair_soft_g8_parameter")),
    }


@dataclass(frozen=True)
class CompleteJudgeSite:
    site_id: str
    primitive: str
    question_id: str
    label: str | None
    decidable: bool
    reason: str
    broker_effect: bool = False
    parameter: float | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "site_id": self.site_id,
            "steal": STEAL,
            "primitive": self.primitive,
            "question_id": self.question_id,
            "label": self.label,
            "decidable": self.decidable,
            "reason": self.reason,
            "broker_effect": False,
            "parameter": self.parameter,
            "never_place": True,
            "status": "shadow_logged" if self.decidable else "unanswered",
            "apply": False,
        }


def _sites(decisions: Mapping[str, Any]) -> tuple[CompleteJudgeSite, ...]:
    residual = decisions.get("admit_residual")
    g4 = decisions.get("chair_soft_g4")
    g6 = decisions.get("chair_soft_g6")
    g8 = decisions.get("chair_soft_g8")
    g8_label = _g8_label(g8 if isinstance(g8, (bool, float)) or g8 is None else None)
    return (
        CompleteJudgeSite(
            "admit_residual",
            "choice",
            _Q_ADMIT,
            None if residual is None else str(residual),
            residual is not None,
            "admit_residual_return" if residual is not None else "unset",
            parameter=_finite(decisions.get("admit_residual_parameter")),
        ),
        CompleteJudgeSite(
            "chair_soft_g4",
            "choice",
            _Q_G4,
            None if g4 is None else str(g4),
            g4 is not None,
            "chair_g4_return" if g4 is not None else "unset",
            parameter=_finite(decisions.get("chair_soft_g4_parameter")),
        ),
        CompleteJudgeSite(
            "chair_soft_g6",
            "choice",
            _Q_G6,
            None if g6 is None else str(g6),
            g6 is not None,
            "chair_g6_return" if g6 is not None else "unset",
            parameter=_finite(decisions.get("chair_soft_g6_parameter")),
        ),
        CompleteJudgeSite(
            "chair_soft_g8",
            "noul",
            _Q_G8,
            g8_label,
            g8 is not None,
            "chair_g8_noul_return" if g8 is not None else "unset",
            parameter=_finite(decisions.get("chair_soft_g8_parameter")),
        ),
    )


def compose_complete_judge(
    gold_state: Mapping[str, Any] | None,
    *,
    g4_applies: bool | None = None,
    admit_choice: str | None = None,
    admit_conf: float | None = None,
    answers: Mapping[str, Any] | None = None,
) -> tuple[CompleteJudgeSite, ...]:
    """Shadow site rows. The label is the System One return for this state.

    A passed ``answers`` map is not a decision and does not fill a miss.
    """

    del answers
    card = _card(
        gold_state,
        g4_applies=g4_applies,
        admit_choice=admit_choice,
        admit_conf=admit_conf,
    )
    return _sites(card["decisions"])
