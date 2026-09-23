"""Place gate. Every decision on this state is the System One return.

One hop: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached
on every ask, and the return is stored for the next ask. An empty answer,
a tie, a missing score, or an error leaves that return unset.
A floor and a baseline are not a question.
This module does not send and does not flatten.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.place_gate.v1"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

PLACE_APPLY_ENV = "GTOS_JEV_PLACE_APPLY"
PLACE_APPLY_ALIASES = (
    "GTOS_JEV_PLACE_APPLY",
    "GTOS_JEV_PLACE_CHOICE_APPLY",
    "GTOS_JEV_PLACE_FLUID_APPLY",
)
OWNER_UNLOCK_ENV = ("GTOS_JEV_OWNER_UNLOCK", "GTOS_OWNER_UNLOCK_PLACE")
OWNER_UNLOCK_PATHS = (
    Path("/workspace/gtos/research/codila_absorb/war_room/OWNER_WORD_JEV_UNLOCK_PLACE_20260921.md"),
    Path("/workspace/gtos/research/warroom_20260920/OWNER_WORD_JEV_UNLOCK_PLACE_20260921.md"),
    Path("/workspace/gtos/close_loop/war_room_20260920/CHAIR_ENFORCE_JEV_PLACE_UNLOCK_20260921.md"),
    Path(r"C:host-local/redacted_host/repo/research/codila_absorb/war_room/OWNER_WORD_JEV_UNLOCK_PLACE_20260921.md"),
    Path(r"C:host-local/redacted_host/repo/close_loop/war_room_20260920/CHAIR_ENFORCE_JEV_PLACE_UNLOCK_20260921.md"),
    Path(r"C:host-local/redacted_host/repo/judgment/astra/OWNER_WORD_JEV_UNLOCK_PLACE_20260921.md"),
)

# Option names a wire-class Choice may return. Membership is not the decision.
_WIRE_ORDER = ("A1", "A2", "A3", "W_named")
LEGAL_WIRE_CLASSES = frozenset(_WIRE_ORDER)
_GATE_ORDER = ("place", "stand", "delay", "remint")
_NOULS = (
    "never_place",
    "never_remint",
    "never_flatten",
    "place_apply",
    "owner_unlock",
    "receipt_legal",
    "broker_effect",
)
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
    "choice",
    "wire_class",
    "threshold",
    "loop_bound",
    "parameter",
    "parameters",
    "component_exists",
    "probabilities",
    "wire_probabilities",
    "answers",
    "prior_outcomes",
    "error",
    "noul",
    "score",
    *_NOULS,
})

_GATE_CRITERIA = {
    "place": "This state opens place.",
    "stand": "This state stands.",
    "delay": "This state waits.",
    "remint": "This state opens remint.",
}
_WIRE_CRITERIA = {
    "A1": "The receipt wire class on this state is A1.",
    "A2": "The receipt wire class on this state is A2.",
    "A3": "The receipt wire class on this state is A3.",
    "W_named": "The receipt wire class on this state is W_named.",
}
_NOUL_TEXT = {
    "never_place": "Is place blocked on this state?",
    "never_remint": "Is remint blocked on this state?",
    "never_flatten": "Is flatten blocked on this state?",
    "place_apply": "Is place apply open on this state?",
    "owner_unlock": "Is the owner unlock acknowledged on this state?",
    "receipt_legal": "Is this receipt legal on this state?",
    "broker_effect": "Is a broker effect allowed on this state?",
}
_NOUL_CRITERIA = {
    "true": "The noul on this question is true.",
    "false": "The noul on this question is false.",
}

# History only when jev_questions cannot be imported. A miss is not copied back.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


class _ReceiptLike(Protocol):
    proven: bool
    wire_class: str


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
    if value is None or isinstance(value, (int, float, bool)):
        return value
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
        str(key): str(value)
        for key, value in criteria.items()
        if not _text_banned(str(key)) and not _text_banned(str(value))
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


def gate_questions() -> dict[str, dict[str, Any]]:
    """Menu for one ask. The menu names what a return may be. The return decides."""

    pack: dict[str, dict[str, Any]] = {
        "place_gate": _choice_question(
            "place_gate",
            (
                "Place gate for this state. Pick one option. "
                "The unique highest probability is the decision. "
                "An empty answer or a tie leaves the choice unset. "
                "This ask does not send and does not flatten."
            ),
            _GATE_CRITERIA,
        ),
        "wire_class": _choice_question(
            "wire_class",
            (
                "Wire class on this receipt. Pick one option. "
                "The unique highest probability is the class. "
                "An empty answer or a tie leaves the class unset."
            ),
            _WIRE_CRITERIA,
        ),
        "place_gate_threshold": _score_question(
            "place_gate_threshold",
            (
                "The score you return is the threshold for this place gate. "
                "It may sit between the levels. "
                "An empty score leaves the threshold unset."
            ),
        ),
        "place_gate_loop": _score_question(
            "place_gate_loop",
            (
                "The score you return is the loop bound for this place gate. "
                "It may sit between the levels. "
                "An empty score leaves the bound unset."
            ),
        ),
        "place_gate_parameter": _score_question(
            "place_gate_parameter",
            (
                "The score you return is the parameter for this place gate. "
                "It may sit between the levels. "
                "An empty score leaves the parameter unset."
            ),
        ),
        "place_gate_component_exists": _noul_question(
            (
                "Does the place gate component exist on this state? "
                "The noul you return is that existence. "
                "An empty noul leaves existence unset."
            )
        ),
    }
    for name in _NOULS:
        tail = "This ask does not send."
        if name == "never_flatten":
            tail = "This ask does not send and does not flatten."
        pack[name] = _noul_question(
            (
                f"{_NOUL_TEXT[name]} "
                "The noul you return is that answer. "
                "An empty noul leaves it unset. "
                f"{tail}"
            )
        )
        pack[f"{name}_parameter"] = _score_question(
            f"{name}_parameter",
            (
                f"The score you return is the parameter for {name} on this state. "
                "It may sit between the levels. "
                "An empty score leaves the parameter unset."
            ),
        )
    for qid, block in list(pack.items()):
        if block.get("type") not in {"noul", "choice", "score"}:
            pack.pop(qid, None)
            continue
        if _text_banned(str(block.get("instructions") or "")):
            pack.pop(qid, None)
    return pack


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
    """Returned score. A tie leaves it unset. The number is not snapped to a level."""

    if not isinstance(raw, dict):
        return _number(raw)
    winner: str | None = None
    raw_probs = raw.get("probabilities")
    if isinstance(raw_probs, Mapping) and raw_probs:
        order = tuple(str(key) for key in raw_probs)
        winner = _unique(_probabilities(raw, order), order)
        if winner is None:
            return None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(raw))
        if parsed is not None:
            return parsed
    except Exception:
        pass
    for key in ("score", "value"):
        if key not in raw:
            continue
        parsed = _number(raw.get(key))
        if parsed is not None:
            return parsed
    if winner is not None and isinstance(raw_probs, Mapping):
        return _number(raw_probs.get(winner))
    return None


def _noul_value(raw: Any) -> bool | float | None:
    """A Noul stays a bool or a probability. A missing noul stays missing."""

    if raw is True or raw is False:
        return raw
    if not isinstance(raw, dict):
        return _number(raw)
    if "noul" in raw:
        value = raw.get("noul")
    elif "Noul" in raw:
        value = raw.get("Noul")
    else:
        return None
    if value is True or value is False:
        return value
    return _number(value)


def _blank(error: str | None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "choice": None,
        "wire_class": None,
        "never_place": None,
        "never_remint": None,
        "never_flatten": None,
        "place_apply": None,
        "owner_unlock": None,
        "receipt_legal": None,
        "broker_effect": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "parameters": {name: None for name in ("place_gate", *_NOULS)},
        "component_exists": None,
        "probabilities": {},
        "wire_probabilities": {},
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
    if model:
        row["model"] = str(model)
    if not answers:
        return row
    choice_probs = _probabilities(answers.get("place_gate"), _GATE_ORDER)
    wire_probs = _probabilities(answers.get("wire_class"), _WIRE_ORDER)
    row["choice"] = _unique(choice_probs, _GATE_ORDER)
    row["wire_class"] = _unique(wire_probs, _WIRE_ORDER)
    row["probabilities"] = {name: choice_probs[name] for name in _GATE_ORDER if name in choice_probs}
    row["wire_probabilities"] = {name: wire_probs[name] for name in _WIRE_ORDER if name in wire_probs}
    row["threshold"] = _score_value(answers.get("place_gate_threshold"))
    row["loop_bound"] = _score_value(answers.get("place_gate_loop"))
    row["parameter"] = _score_value(answers.get("place_gate_parameter"))
    row["parameters"]["place_gate"] = row["parameter"]
    row["component_exists"] = _noul_value(answers.get("place_gate_component_exists"))
    for name in _NOULS:
        row[name] = _noul_value(answers.get(name))
        row["parameters"][name] = _score_value(answers.get(f"{name}_parameter"))
    return row


def _outcome_pairs(row: Mapping[str, Any]) -> tuple[tuple[str, Any, str | None], ...]:
    ask_error = row.get("error") if isinstance(row.get("error"), str) else None
    parameters = row.get("parameters") if isinstance(row.get("parameters"), Mapping) else {}

    def miss(value: Any, kind: str) -> str | None:
        if value is not None:
            return None
        return ask_error or kind

    pairs: list[tuple[str, Any, str | None]] = [
        ("place_gate", row.get("choice"), miss(row.get("choice"), "tie_or_empty")),
        ("wire_class", row.get("wire_class"), miss(row.get("wire_class"), "tie_or_empty")),
        ("place_gate_threshold", row.get("threshold"), miss(row.get("threshold"), "score_missing")),
        ("place_gate_loop", row.get("loop_bound"), miss(row.get("loop_bound"), "score_missing")),
        ("place_gate_parameter", row.get("parameter"), miss(row.get("parameter"), "score_missing")),
        (
            "place_gate_component_exists",
            row.get("component_exists"),
            miss(row.get("component_exists"), "noul_missing"),
        ),
    ]
    for name in _NOULS:
        value = row.get(name)
        parameter = parameters.get(name)
        pairs.append((name, value, miss(value, "noul_missing")))
        pairs.append((f"{name}_parameter", parameter, miss(parameter, "score_missing")))
    return tuple(pairs)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    pairs = _outcome_pairs(row)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in pairs:
            _LOCAL_OUTCOMES.append({"key": key, "value": value, "error": error})
        return
    for key, value, error in pairs:
        try:
            append_outcome(key, value, state, error=error)
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


def _env_facts(environ: Mapping[str, str] | None) -> dict[str, str]:
    env = environ if environ is not None else os.environ
    observed: dict[str, str] = {}
    for name in (*PLACE_APPLY_ALIASES, *OWNER_UNLOCK_ENV):
        try:
            present = name in env
        except Exception:
            present = False
        if not present:
            continue
        raw = str(env.get(name, ""))
        if _text_banned(raw):
            continue
        observed[name] = raw
    return observed


def _owner_word_files() -> list[str]:
    found: list[str] = []
    for path in OWNER_UNLOCK_PATHS:
        try:
            if path.is_file():
                found.append(str(path))
        except OSError:
            continue
    return found


def _receipt_facts(receipt: Any) -> dict[str, Any] | None:
    if receipt is None:
        return None
    if isinstance(receipt, Mapping):
        proven = receipt.get("proven")
        wire = receipt.get("wire_class")
    else:
        proven = getattr(receipt, "proven", None)
        wire = getattr(receipt, "wire_class", None)
    out: dict[str, Any] = {}
    if proven is True or proven is False:
        out["proven"] = proven
    else:
        number = _number(proven)
        if number is not None:
            out["proven"] = number
    if wire is not None and not _text_banned(str(wire)):
        out["wire_class"] = str(wire)
    return out or None


def _build_state(
    *,
    environ: Mapping[str, str] | None,
    receipt: Any,
    place_authorized: bool | None,
    facts: Mapping[str, Any] | None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
    }
    observed = _env_facts(environ)
    if observed:
        state["env"] = observed
    files = _owner_word_files()
    if files:
        state["owner_word_files"] = files
    receipt_facts = _receipt_facts(receipt)
    if receipt_facts is not None:
        state["receipt"] = receipt_facts
    if place_authorized is True or place_authorized is False:
        state["place_authorized"] = place_authorized
    if isinstance(facts, Mapping):
        for key, value in facts.items():
            name = str(key)
            if name in state or name in _RESERVED or _limit_key(name):
                continue
            state[name] = value
    scrubbed = _scrub(state)
    return scrubbed if isinstance(scrubbed, dict) else {"schema": SCHEMA, "model": MODEL}


def evaluate_place_gate(
    *,
    environ: Mapping[str, str] | None = None,
    receipt: _ReceiptLike | None = None,
    place_authorized: bool | None = None,
    facts: Mapping[str, Any] | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One System One ask. Each field is that return, or unset."""

    state = _build_state(
        environ=environ,
        receipt=receipt,
        place_authorized=place_authorized,
        facts=facts,
    )
    questions = gate_questions()
    state["model"] = MODEL
    _attach_priors(state, questions)
    try:
        receipt_body = _post(state, questions, ask)
    except Exception as exc:  # noqa: BLE001 — a dark ask stays unset
        row = _blank(type(exc).__name__)
        _remember(state, row)
        return row
    row = _read(receipt_body)
    _remember(state, row)
    return row


def place_apply_enabled(*, environ: Mapping[str, str] | None = None) -> bool | float | None:
    """Place-apply noul for this state. A miss stays unset."""

    return evaluate_place_gate(environ=environ)["place_apply"]


def owner_unlock_acknowledged(*, environ: Mapping[str, str] | None = None) -> bool | float | None:
    """Owner-unlock noul for this state. A miss stays unset."""

    return evaluate_place_gate(environ=environ)["owner_unlock"]


def receipt_legal(receipt: _ReceiptLike | None) -> bool | float | None:
    """Receipt-legal noul for this state. A miss stays unset."""

    return evaluate_place_gate(receipt=receipt)["receipt_legal"]


def never_place_effective(
    *,
    environ: Mapping[str, str] | None = None,
    receipt: _ReceiptLike | None = None,
) -> bool | float | None:
    """Never-place noul for this state. A miss stays unset."""

    return evaluate_place_gate(environ=environ, receipt=receipt)["never_place"]


def never_remint_effective(
    *,
    environ: Mapping[str, str] | None = None,
    receipt: _ReceiptLike | None = None,
) -> bool | float | None:
    """Never-remint noul for this state. A miss stays unset."""

    return evaluate_place_gate(environ=environ, receipt=receipt)["never_remint"]


def never_flatten_effective(
    *,
    environ: Mapping[str, str] | None = None,
    receipt: _ReceiptLike | None = None,
) -> bool | float | None:
    """Never-flatten noul for this state. A miss stays unset. This does not flatten."""

    return evaluate_place_gate(environ=environ, receipt=receipt)["never_flatten"]


def broker_effect_allowed(
    *,
    environ: Mapping[str, str] | None = None,
    receipt: _ReceiptLike | None = None,
    place_authorized: bool | None = None,
) -> bool | float | None:
    """Broker-effect noul for this state. A miss stays unset. This module does not send."""

    return evaluate_place_gate(
        environ=environ,
        receipt=receipt,
        place_authorized=place_authorized,
    )["broker_effect"]


def log_consts_for_verify(
    *,
    environ: Mapping[str, str] | None = None,
    receipt: _ReceiptLike | None = None,
) -> dict[str, object]:
    """One ask. Each logged field is that return, or unset."""

    row = evaluate_place_gate(environ=environ, receipt=receipt)
    parameters = row["parameters"] if isinstance(row.get("parameters"), Mapping) else {}
    return {
        "never_place": row.get("never_place"),
        "never_remint": row.get("never_remint"),
        "never_flatten": row.get("never_flatten"),
        "broker_effect": row.get("broker_effect"),
        "place_apply_env": row.get("place_apply"),
        "owner_unlock": row.get("owner_unlock"),
        "receipt_legal": row.get("receipt_legal"),
        "choice": row.get("choice"),
        "wire_class": row.get("wire_class"),
        "threshold": row.get("threshold"),
        "loop_bound": row.get("loop_bound"),
        "parameter": row.get("parameter"),
        "parameters": {name: parameters.get(name) for name in ("place_gate", *_NOULS)},
        "component_exists": row.get("component_exists"),
        "model": row.get("model"),
        "error": row.get("error"),
    }
