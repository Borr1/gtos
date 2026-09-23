"""Global sleeve-select shadow. Every decision is the System One return.

One hop: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached
on the ask, and the return is stored for the next ask. The verdict, the
scope, the apply and resting-shadow nouls, the threshold, the loop bound,
the parameter, and which scoped wire stays untouched are that return.
An empty answer, a tie, a missing score, or an error leaves that field unset.

A floor and a baseline are not a question. This module does not send.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
SCHEMA = "gtos.judgment.jev_sleeve_select_shadow.v1"
REASON = "jev_sleeve_select_shadow"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

_VERDICT_ORDER = ("KILL_ENFORCE", "SHADOW", "APPLY")
_SCOPE_ORDER = ("GLOBAL", "SCOPED")
_WIRES = (
    "f5_xau_flow_alignment_size_tilt",
    "ca_cross_asset_size_tilt",
    "F5-JEV-004",
)
_NOULS = (
    "apply_enabled",
    "resting_shadow",
    "state_sufficient",
    "component_exists",
    *(f"untouched_{name}" for name in _WIRES),
)
_SCORE_IDS = ("shadow_threshold", "shadow_loop_bound", "shadow_parameter")
_LEVELS = ("none", "trace", "small", "modest", "notable", "heavy")
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
_RESERVED = frozenset({
    "schema",
    "model",
    "reason",
    "verdict",
    "scope",
    "choice",
    "apply_enabled",
    "resting_shadow",
    "state_sufficient",
    "which_component",
    "component_exists",
    "threshold",
    "loop_bound",
    "parameter",
    "untouched",
    "probabilities",
    "scope_probabilities",
    "component_probabilities",
    "answers",
    "prior_outcomes",
    "error",
    "noul",
    "score",
    "default",
    "answer",
    *_NOULS,
    *_SCORE_IDS,
})
_VERDICT_CRITERIA = {
    "KILL_ENFORCE": "This global shadow surface is closed on this state.",
    "SHADOW": "This global shadow surface rests as shadow on this state.",
    "APPLY": "This global shadow surface applies on this state.",
}
_SCOPE_CRITERIA = {
    "GLOBAL": "The shadow surface on this state is global.",
    "SCOPED": "The shadow surface on this state is scoped.",
}
_NOUL_TEXT = {
    "apply_enabled": "Is global apply enabled on this state?",
    "resting_shadow": "Is a resting shadow enabled on this state?",
    "state_sufficient": "Is this state complete enough for this shadow surface?",
    "component_exists": "Does the named component exist on this state?",
}
_NOUL_CRITERIA = {
    "true": "The noul on this question is true.",
    "false": "The noul on this question is false.",
}

# History only when jev_questions cannot be imported. A miss is not copied back.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


def _text_banned(text: str) -> bool:
    compact = text.replace(",", "").replace("_", "").lower()
    if "floor" in compact or "baseline" in compact:
        return True
    for token in _BANNED_TEXT:
        if token.replace(",", "").replace("_", "").lower() in compact:
            return True
    return False


def _limit_key(name: str) -> bool:
    return _text_banned(name)


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


def _banned_level(number: float) -> bool:
    return abs(number - 90000.0) < 1e-6 or abs(number - 110000.0) < 1e-6


def _scrub(value: Any) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            cleaned = _scrub(item)
            if cleaned is None and item is not None:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        kept = []
        for item in value:
            cleaned = _scrub(item)
            if cleaned is None and item is not None:
                continue
            kept.append(cleaned)
        return kept
    if isinstance(value, str):
        if _text_banned(value):
            return None
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        number = _number(value)
        if number is None or _banned_level(number):
            return None
        return number
    if value is None:
        return None
    text = str(value)
    if _text_banned(text):
        return None
    return text


def _strip_planted(block: dict[str, Any]) -> dict[str, Any]:
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    return block


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(criteria))
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            body = dict(raw)
    except Exception:
        body = {}
    _strip_planted(body)
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {
        str(key): str(text)
        for key, text in criteria.items()
        if not _text_banned(str(key)) and not _text_banned(str(text))
    }
    return body


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    body: dict[str, Any] = {}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            body = dict(raw)
    except Exception:
        body = {}
    _strip_planted(body)
    body["type"] = "score"
    body["instructions"] = instructions
    levels = body.get("criteria")
    if isinstance(levels, list):
        kept = [str(item) for item in levels if not _text_banned(str(item))]
        body["criteria"] = kept or list(_LEVELS)
    else:
        body["criteria"] = list(_LEVELS)
    return body


def _noul_question(instructions: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": dict(_NOUL_CRITERIA),
    }


def _untouched_id(wire: str) -> str:
    return f"untouched_{wire}"


def shadow_questions() -> dict[str, dict[str, Any]]:
    """Menu for one ask. The menu names what a return may be. The return decides."""

    pack: dict[str, dict[str, Any]] = {
        "shadow_verdict": _choice_question(
            "shadow_verdict",
            (
                "Global sleeve-select shadow for this state. Pick one option. "
                "The unique highest probability is the verdict. "
                "An empty answer or a tie leaves the verdict unset. "
                "This ask does not send an order."
            ),
            _VERDICT_CRITERIA,
        ),
        "shadow_scope": _choice_question(
            "shadow_scope",
            (
                "Scope of this sleeve-select shadow. Pick one option. "
                "The unique highest probability is the scope. "
                "An empty answer or a tie leaves the scope unset. "
                "This ask does not send an order."
            ),
            _SCOPE_CRITERIA,
        ),
        "which_component": _choice_question(
            "which_component",
            (
                "Which named scoped wire is the component on this state? "
                "The unique highest probability is the component. "
                "An empty answer or a tie leaves the component unset. "
                "This ask does not send an order."
            ),
            {name: f"{name} is the component on this state." for name in _WIRES},
        ),
        "shadow_threshold": _score_question(
            "shadow_threshold",
            (
                "The score you return is the threshold for this shadow surface. "
                "It may sit between the levels. "
                "An empty score leaves the threshold unset. "
                "This ask does not send an order."
            ),
        ),
        "shadow_loop_bound": _score_question(
            "shadow_loop_bound",
            (
                "The score you return is the loop bound for this shadow surface. "
                "It may sit between the levels. "
                "An empty score leaves the bound unset. "
                "This ask does not send an order."
            ),
        ),
        "shadow_parameter": _score_question(
            "shadow_parameter",
            (
                "The score you return is the parameter for this shadow surface. "
                "It may sit between the levels. "
                "An empty score leaves the parameter unset. "
                "This ask does not send an order."
            ),
        ),
    }
    for name in ("apply_enabled", "resting_shadow", "state_sufficient", "component_exists"):
        pack[name] = _noul_question(
            (
                f"{_NOUL_TEXT[name]} "
                "The noul you return is that answer. "
                "An empty noul leaves it unset. "
                "This ask does not send an order."
            )
        )
    for wire in _WIRES:
        pack[_untouched_id(wire)] = _noul_question(
            (
                f"Does this state leave {wire} untouched? "
                "The noul you return is that answer. "
                "An empty noul leaves it unset. "
                "This ask does not send an order."
            )
        )
    clean: dict[str, dict[str, Any]] = {}
    for qid, block in pack.items():
        if block.get("type") not in {"noul", "choice", "score"}:
            continue
        texts = [str(block.get("instructions") or "")]
        criteria = block.get("criteria")
        if isinstance(criteria, Mapping):
            texts.extend(str(key) for key in criteria)
            texts.extend(str(text) for text in criteria.values())
        elif isinstance(criteria, list):
            texts.extend(str(item) for item in criteria)
        if any(_text_banned(text) for text in texts):
            continue
        clean[qid] = block
    return clean


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        name = str(key)
        if allowed and name not in allowed:
            continue
        number = _number(value)
        if number is None:
            continue
        numeric[name] = number
    return numeric


def _local_unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    names = order or tuple(numeric)
    for name in names:
        if name not in numeric:
            continue
        prob = numeric[name]
        if best_p is None or prob > best_p + 1e-12:
            best = name
            best_p = prob
            tied = False
        elif abs(prob - best_p) <= 1e-12:
            tied = True
    if tied or best is None:
        return None
    return best


def _unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie, an empty map, or a bare label stays unset."""

    if not numeric:
        return None
    local = _local_unique(numeric, order)
    if local is None:
        return None
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(dict(numeric), order)
    except Exception:
        agreed = local
    if agreed is None or str(agreed) != local:
        return None
    return local


def _score_value(raw: Any) -> float | None:
    """Returned score. It is not snapped to a level and not filled in."""

    if not isinstance(raw, dict) or raw.get("error"):
        return None
    kind = raw.get("type")
    if kind is not None and str(kind).strip().lower() not in {"", "score"}:
        return None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(raw))
        if parsed is not None:
            return parsed
    except Exception:
        pass
    for key in ("score", "value"):
        if key not in raw or raw.get(key) is None:
            continue
        parsed = _number(raw.get(key))
        if parsed is not None:
            return parsed
    return None


def _noul_value(raw: Any) -> bool | float | None:
    """A Noul stays a bool or a probability. A missing noul stays missing."""

    if not isinstance(raw, dict) or raw.get("error"):
        return None
    kind = raw.get("type")
    if kind is not None and str(kind).strip().lower() not in {"", "noul"}:
        return None
    if "noul" not in raw:
        return None
    value = raw.get("noul")
    if value is True or value is False:
        return value
    return _number(value)


def _blank(error: str | None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "reason": REASON,
        "verdict": None,
        "scope": None,
        "apply_enabled": None,
        "resting_shadow": None,
        "state_sufficient": None,
        "which_component": None,
        "component_exists": None,
        "untouched": {name: None for name in _WIRES},
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "probabilities": {},
        "scope_probabilities": {},
        "component_probabilities": {},
        "error": error,
    }


def _read(receipt: Mapping[str, Any]) -> dict[str, Any]:
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    row = _blank(None if error in (None, "") else str(error))
    model = receipt.get("model")
    if isinstance(model, str) and model.strip():
        row["model"] = model.strip()
    if not answers:
        return row
    verdict_probs = _probabilities(answers.get("shadow_verdict"), _VERDICT_ORDER)
    scope_probs = _probabilities(answers.get("shadow_scope"), _SCOPE_ORDER)
    component_probs = _probabilities(answers.get("which_component"), _WIRES)
    row["verdict"] = _unique(verdict_probs, _VERDICT_ORDER)
    row["scope"] = _unique(scope_probs, _SCOPE_ORDER)
    row["which_component"] = _unique(component_probs, _WIRES)
    row["probabilities"] = {name: verdict_probs[name] for name in _VERDICT_ORDER if name in verdict_probs}
    row["scope_probabilities"] = {name: scope_probs[name] for name in _SCOPE_ORDER if name in scope_probs}
    row["component_probabilities"] = {
        name: component_probs[name] for name in _WIRES if name in component_probs
    }
    row["threshold"] = _score_value(answers.get("shadow_threshold"))
    row["loop_bound"] = _score_value(answers.get("shadow_loop_bound"))
    row["parameter"] = _score_value(answers.get("shadow_parameter"))
    row["apply_enabled"] = _noul_value(answers.get("apply_enabled"))
    row["resting_shadow"] = _noul_value(answers.get("resting_shadow"))
    row["state_sufficient"] = _noul_value(answers.get("state_sufficient"))
    row["component_exists"] = _noul_value(answers.get("component_exists"))
    untouched = row["untouched"]
    for wire in _WIRES:
        untouched[wire] = _noul_value(answers.get(_untouched_id(wire)))
    if row["verdict"] is None and verdict_probs and _local_unique(verdict_probs, _VERDICT_ORDER) is None:
        row["error"] = row["error"] or "tie"
    return row


def _outcome_pairs(row: Mapping[str, Any]) -> tuple[tuple[str, Any, str | None], ...]:
    ask_error = row.get("error") if isinstance(row.get("error"), str) else None
    untouched = row.get("untouched") if isinstance(row.get("untouched"), Mapping) else {}

    def miss(value: Any, kind: str) -> str | None:
        if value is not None:
            return None
        return ask_error or kind

    pairs: list[tuple[str, Any, str | None]] = [
        ("shadow_verdict", row.get("verdict"), miss(row.get("verdict"), "tie_or_empty")),
        ("shadow_scope", row.get("scope"), miss(row.get("scope"), "tie_or_empty")),
        ("which_component", row.get("which_component"), miss(row.get("which_component"), "tie_or_empty")),
        ("shadow_threshold", row.get("threshold"), miss(row.get("threshold"), "score_missing")),
        ("shadow_loop_bound", row.get("loop_bound"), miss(row.get("loop_bound"), "score_missing")),
        ("shadow_parameter", row.get("parameter"), miss(row.get("parameter"), "score_missing")),
        ("apply_enabled", row.get("apply_enabled"), miss(row.get("apply_enabled"), "noul_missing")),
        ("resting_shadow", row.get("resting_shadow"), miss(row.get("resting_shadow"), "noul_missing")),
        ("state_sufficient", row.get("state_sufficient"), miss(row.get("state_sufficient"), "noul_missing")),
        ("component_exists", row.get("component_exists"), miss(row.get("component_exists"), "noul_missing")),
    ]
    for wire in _WIRES:
        value = untouched.get(wire)
        pairs.append((_untouched_id(wire), value, miss(value, "noul_missing")))
    return tuple(pairs)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    cleaned = _scrub(loaded)
    state["prior_outcomes"] = [] if cleaned is None else cleaned


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    pairs = _outcome_pairs(row)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in pairs:
            _LOCAL_OUTCOMES.append({"key": key, "value": value, "error": error})
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in pairs:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    ask: Callable[..., Any] | None,
) -> dict[str, Any]:
    call = ask
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    receipt = call(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    return receipt if isinstance(receipt, dict) else {"error": "evaluate_not_a_dict", "answers": {}}


def _build_state(facts: Mapping[str, Any] | None) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "api_url": API_URL,
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "ns": CHALLENGE_NS,
        "reason": REASON,
        "scoped_wires": list(_WIRES),
    }
    if isinstance(facts, Mapping):
        for key, value in facts.items():
            name = str(key)
            if name in _RESERVED or _limit_key(name):
                continue
            if name in {"login", "namespace", "ns"} and value not in (None, ""):
                state[name] = value
                continue
            if name in state:
                continue
            state[name] = value
    scrubbed = _scrub(state)
    out = scrubbed if isinstance(scrubbed, dict) else {"schema": SCHEMA, "model": MODEL}
    out["model"] = MODEL
    out["api_url"] = API_URL
    return out


def evaluate_jev_sleeve_select_shadow(
    state: Mapping[str, Any] | None = None,
    *,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One System One ask. Each field is that return, or unset."""

    payload = _build_state(state)
    questions = shadow_questions()
    _attach_priors(payload, questions)
    try:
        receipt = _post(payload, questions, ask)
    except Exception as exc:
        row = _blank(type(exc).__name__)
        _remember(payload, row)
        return row
    row = _read(receipt)
    _remember(payload, row)
    return row


def _facts_from_call(args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    if args and isinstance(args[0], Mapping):
        raw.update(dict(args[0]))
    for key in ("state", "facts"):
        value = kwargs.get(key)
        if isinstance(value, Mapping):
            raw.update(dict(value))
    return raw


def apply_jev_sleeve_select_shadow_global(*args: object, **kwargs: object) -> dict[str, Any]:
    """Global shadow ask. The return is the decision. This does not send."""

    facts = _facts_from_call(args, kwargs)
    ask = kwargs.get("ask")
    caller = ask if callable(ask) else None
    return evaluate_jev_sleeve_select_shadow(facts, ask=caller)


def apply_jev_sleeve_select_shadow(*args: object, **kwargs: object) -> dict[str, Any]:
    """Same ask as the global surface. This does not send."""

    return apply_jev_sleeve_select_shadow_global(*args, **kwargs)


def global_shadow_enabled(*args: object, **kwargs: object) -> bool | float | None:
    """Resting-shadow noul for this state. A miss stays unset."""

    return apply_jev_sleeve_select_shadow_global(*args, **kwargs)["resting_shadow"]


def scoped_xau_conflict_apply_untouched(*args: object, **kwargs: object) -> tuple[str, ...] | None:
    """Wires whose untouched noul is true. A miss does not fill the wire list."""

    row = apply_jev_sleeve_select_shadow_global(*args, **kwargs)
    untouched = row.get("untouched") if isinstance(row.get("untouched"), Mapping) else {}
    seen_bool = False
    kept: list[str] = []
    for wire in _WIRES:
        value = untouched.get(wire)
        if value is True:
            seen_bool = True
            kept.append(wire)
        elif value is False:
            seen_bool = True
    if not seen_bool:
        return None
    return tuple(kept)


__all__ = [
    "API_URL",
    "MODEL",
    "REASON",
    "SCHEMA",
    "apply_jev_sleeve_select_shadow",
    "apply_jev_sleeve_select_shadow_global",
    "evaluate_jev_sleeve_select_shadow",
    "global_shadow_enabled",
    "scoped_xau_conflict_apply_untouched",
    "shadow_questions",
]
