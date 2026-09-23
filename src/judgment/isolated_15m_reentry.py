"""Isolated 15m re-entry after a symbol closes is a new named fire.

Occupancy HOLD is dead. The 2-stop COUNT stays the integer
``same_sleeve_orig_stop_count_session_day`` reads from closed[]. The cap
is the score on this ask. This file does not splice ``book_owner`` and
does not ``order_send``.

Every decision in this file, including every parameter, is the value
System One returns for that state. One hop: ``jev_client.evaluate`` with
model ``jev-1.13.0`` and ``merge_sleeve=False`` (POST
https://api.typesafe.ai/v1/systemone). Questions are only Noul, Choice,
or Score. Prior outcomes are attached on every ask, and the return is
appended for the next ask. An empty answer, a tie, or an error leaves
that return unset. A floor and a baseline are not a question. This
module does not send and does not flatten.

Book: Challenge **0** / ns ``operator`` / magic **0**.
Never flatten ticket **294215389**. The persistence parameter is the
returned score. An empty score leaves it absent. Isolated does not send.
Missing answers grant no extra PASS.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .challenge import (
    CHALLENGE_LOGIN,
    CHALLENGE_MAGIC,
    CHALLENGE_NS,
    VERIFICATION_QUARANTINED,
)
from .jev_questions import MODEL
from .occupancy import (
    parse_utc,
    trades_from_dicts,
)
from .two_stop import same_sleeve_orig_stop_count_session_day

SCHEMA = "gtos.judgment.isolated_15m_reentry.v0"
STEAL = "ISOLATED_15M_REENTRY"
ENV = "GTOS_JEV_ISOLATED_15M_REENTRY"
PIN_WINDOW = "G-FULL"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPLAY = (
    REPO_ROOT
    / "judgment"
    / "astra"
    / "lab"
    / "challenge_replay_20260917"
    / "challenge_replay_rows.jsonl"
)
DEFAULT_PROVE = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "JEV_ISOLATED_15M_REENTRY_PROVE.json"
)

# Live tickets this file must never flatten / remint / place.
NEVER_FLATTEN_TICKETS = (293332188, 294069721, 294088097, 294092360, 294215389)
KIND_READ = "read"
FORBIDDEN_INSTRUCTION_TOKENS = ("jev", "system one", "choice")

# Named tickets used to find a row. Nets and gaps are measured on that row.
WALKED_HI_PARENT = 291072108
WALKED_HI_CHILD = 291096187
US30_SHORT_PARENT = 291167802
US30_SHORT_CHILD = 291186653

_TRUE = frozenset({"1", "true", "on", "yes"})
_MT5_NAIVE = "%Y.%m.%d %H:%M:%S"
_DROP = object()
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LIMIT_PARTS = (
    "floor",
    "baseline",
    "pass_line",
    "to_pass",
    "floor_room",
    "daily_loss",
    "drawdown",
    "profit_target",
    "max_loss",
)
_LEVEL_SKIP = _LIMIT_PARTS + (
    "ticket",
    "login",
    "magic",
    "persist",
    "equity",
    "balance",
    "prior_outcomes",
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
_OCCUPANCY_CRITERIA = {
    "keep_one_occupied": "The symbol is occupied. Keep that one ticket. Do not flatten it.",
    "named_fire": "This open is a new named fire after a close.",
    "not_isolated": "The symbol is flat and this open is not the isolated re-entry.",
    "first_print": "This symbol has no prior close.",
    "occupancy_unassembled": "The clock or the tape is not assembled.",
}
_OCCUPANCY_ORDER = tuple(_OCCUPANCY_CRITERIA)
_COMPONENT_CRITERIA = {
    "keep_one": "The keep-one seat is the component on this state.",
    "flat_clock": "The flat-clock seat is the component on this state.",
    "already_placed": "The already-placed seat is the component on this state.",
}
_COMPONENT_ORDER = tuple(_COMPONENT_CRITERIA)


def _limit_key(name: str) -> bool:
    low = str(name).lower().replace("-", "_")
    return any(part in low for part in _LIMIT_PARTS)


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    for token in _BANNED_TEXT:
        piece = token.replace(",", "").replace("_", "").lower()
        if piece and piece in compact:
            return True
    return False


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


def _scrub(value: Any, depth: int = 0) -> Any:
    """Drop a floor and a baseline before the ask. They are not a question."""

    if depth > 8:
        return _DROP
    if isinstance(value, str):
        if _banned_text(value) or "floor" in value.lower() or "baseline" in value.lower():
            return _DROP
        return value
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        number = _number(value)
        if number in (90000.0, 110000.0):
            return _DROP
        return value
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            cleaned = _scrub(item, depth + 1)
            if cleaned is _DROP:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        kept = []
        for item in value:
            cleaned = _scrub(item, depth + 1)
            if cleaned is _DROP:
                continue
            kept.append(cleaned)
        return kept
    return _DROP


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numeric facts already on this state. A score may sit between them."""

    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        low = key.lower()
        if any(part in low for part in _LEVEL_SKIP) or _limit_key(key):
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(str(child_key), child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            for item in value:
                walk(key, item)
            return
        number = _number(value)
        if number is not None and number not in (90000.0, 110000.0):
            found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(value) for key, value in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(body["criteria"]))
        row = built.get(qid) if isinstance(built, Mapping) else None
        if isinstance(row, Mapping):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {str(key): str(value) for key, value in criteria.items()}
    return {qid: body}


def _score_question(qid: str, instructions: str, levels: list[str]) -> dict[str, Any]:
    body: dict[str, Any] = {"type": "score", "instructions": instructions}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        row = built.get(qid) if isinstance(built, Mapping) else None
        if isinstance(row, Mapping):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "score"
    body["instructions"] = instructions
    if levels:
        body["criteria"] = list(levels)
    else:
        body["criteria"] = list(_BETWEEN)
    return {qid: body}


def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes on this state.",
                "false": "No on this state.",
            },
        }
    }


def _question_text(body: Mapping[str, Any]) -> str:
    parts = [str(body.get("instructions") or "")]
    criteria = body.get("criteria")
    if isinstance(criteria, Mapping):
        parts.extend(str(key) for key in criteria)
        parts.extend(str(value) for value in criteria.values())
    elif isinstance(criteria, (list, tuple)):
        parts.extend(str(value) for value in criteria)
    return "\n".join(parts).lower()


def _question_ok(body: Mapping[str, Any]) -> bool:
    kind = str(body.get("type") or "").lower()
    if kind not in {"noul", "choice", "score"}:
        return False
    text = _question_text(body)
    if any(token in text for token in FORBIDDEN_INSTRUCTION_TOKENS):
        return False
    if "floor" in text or "baseline" in text or _banned_text(text):
        return False
    return True


def reentry_questions(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One occupancy ask. Noul, Choice, or Score only. A floor is not asked."""

    facts = _scrub(dict(state or {}))
    if not isinstance(facts, dict):
        facts = {}
    scale = _levels(facts)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "occupancy_after_close",
        (
            "This open on this symbol. Minutes since flat, whether the symbol is open, "
            "and the integer two-stop count are facts on this state. "
            "Which option is this open? The single highest probability is the decision. "
            "An empty answer or a tie leaves the decision unset. "
            "Do not flatten. Do not send."
        ),
        _OCCUPANCY_CRITERIA,
    ))
    pack.update(_score_question(
        "reentry_threshold",
        (
            "The score you return is the minute threshold for an isolated re-entry on this state. "
            "It may sit between the levels. "
            "An empty score leaves the threshold unset. Do not send."
        ),
        scale,
    ))
    pack.update(_score_question(
        "reentry_parameter",
        (
            "The score you return is the parameter for this occupancy state. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. Do not send."
        ),
        scale,
    ))
    pack.update(_score_question(
        "reentry_loop",
        (
            "The score you return is how far this occupancy state reads prior returned outcomes. "
            "It may sit between the levels. "
            "An empty score leaves the bound unset. Do not send."
        ),
        scale,
    ))
    pack.update(_score_question(
        "two_stop_cap",
        (
            "The score you return is the same-sleeve original-stop cap for this session day. "
            "The count on the state is the integer. You are not the counter. "
            "The score may sit between the levels. "
            "An empty score leaves the cap unset. Do not send."
        ),
        scale,
    ))
    pack.update(_noul_question(
        "remaining_state_sufficient",
        (
            "Are the named occupancy facts present enough to judge this open? "
            "An empty noul leaves sufficiency unset. Do not send."
        ),
    ))
    pack.update(_choice_question(
        "which_component",
        (
            "Which occupancy component exists on this state? "
            "The single highest probability is that component. "
            "An empty answer or a tie leaves the component unset. Do not send."
        ),
        _COMPONENT_CRITERIA,
    ))
    pack.update(_noul_question(
        "component_exists",
        (
            "Does that occupancy component exist on this state? "
            "An empty noul leaves existence unset. Do not send."
        ),
    ))
    pack.update(_noul_question(
        "isolated_reentry_is_new",
        (
            "Is this open a new named fire after a close on a flat symbol? "
            "The integer two-stop count stays the integer on the state. "
            "An empty noul leaves this unset. Do not flatten. Do not send."
        ),
    ))
    pack.update(_noul_question(
        "two_stop_binds",
        (
            "Does the integer two-stop count on this state bind this open? "
            "You are not the counter. "
            "An empty noul leaves the bind unset. Do not send."
        ),
    ))
    pack.update(_score_question(
        "persist_weight",
        (
            "The score you return is the persistence parameter for this state. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. Do not send."
        ),
        scale,
    ))
    pack.update(_noul_question(
        "pin_ok",
        (
            "Are the recorded pin attributes on this state the pin for this open? "
            "An empty noul leaves the pin unset. Do not send."
        ),
    ))
    pack.update(_noul_question(
        "may_send",
        (
            "May this open send? "
            "An empty noul leaves send unset. Do not flatten."
        ),
    ))
    pack.update(_noul_question(
        "blocks_send",
        (
            "Does this open block a send? "
            "An empty noul leaves the block unset. Do not flatten."
        ),
    ))
    pack.update(_noul_question(
        "fail_closed",
        (
            "Is this open closed off the challenge book? "
            "The identity reason on this state is a fact. "
            "An empty noul leaves it unset. Do not send."
        ),
    ))
    pack.update(_noul_question(
        "thin_state",
        (
            "Is this open thin? "
            "An empty noul leaves it unset. Do not send."
        ),
    ))
    pack.update(_noul_question(
        "already_placed_holds",
        (
            "Does already-placed hold this open? "
            "An empty noul leaves it unset. Do not send."
        ),
    ))
    pack.update(_noul_question(
        "history_proved",
        (
            "Do the measured counts on this state prove the pack? "
            "An empty noul leaves it unset. Do not send."
        ),
    ))
    return {key: body for key, body in pack.items() if isinstance(body, Mapping) and _question_ok(body)}


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _number(value)
        if number is None:
            continue
        numeric[name] = number
    return numeric


def _local_unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie or an empty block is unset."""

    best: str | None = None
    best_p: float | None = None
    tied = False
    for name in order:
        if name not in probabilities:
            continue
        p = probabilities[name]
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
    probs = _probabilities(block, order)
    if not probs:
        return None, {}
    names = tuple(name for name in order if name in probs)
    local = _local_unique(probs, names)
    agreed = local
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(dict(probs), names)
    except Exception:
        agreed = local
    kept = {name: probs[name] for name in names}
    if agreed is None or local is None or str(agreed) != local:
        return None, kept
    return local, kept


def _choice_tied(block: Any) -> bool:
    probs = _probabilities(block, _OCCUPANCY_ORDER)
    if not probs:
        return False
    names = tuple(name for name in _OCCUPANCY_ORDER if name in probs)
    return _local_unique(probs, names) is None


def _score_of(block: Any) -> float | None:
    """The returned score. A tie leaves it unset. It is not snapped to a level."""

    if not isinstance(block, Mapping):
        return None
    raw = block.get("probabilities")
    names = tuple(str(key) for key in raw) if isinstance(raw, Mapping) else ()
    probs = _probabilities(block, names)
    if probs and _local_unique(probs, names) is None:
        return None
    parsed = None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(block))
    except Exception:
        parsed = None
    if parsed is not None:
        return parsed
    for key in ("score", "value"):
        parsed = _number(block.get(key))
        if parsed is not None:
            return parsed
    return None


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. Missing stays missing."""

    if not isinstance(block, Mapping) or "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _number(raw)


def _read(answers: Mapping[str, Any], error: str | None) -> dict[str, Any]:
    choice, probs = _choice_of(answers.get("occupancy_after_close"), _OCCUPANCY_ORDER)
    component, _component_probs = _choice_of(answers.get("which_component"), _COMPONENT_ORDER)
    return {
        "choice": choice,
        "probabilities": probs,
        "threshold": _score_of(answers.get("reentry_threshold")),
        "parameter": _score_of(answers.get("reentry_parameter")),
        "loop_bound": _score_of(answers.get("reentry_loop")),
        "two_stop_cap": _score_of(answers.get("two_stop_cap")),
        "persist_weight": _score_of(answers.get("persist_weight")),
        "remaining_state_sufficient": _noul_of(answers.get("remaining_state_sufficient")),
        "component": component,
        "component_exists": _noul_of(answers.get("component_exists")),
        "isolated_reentry_is_new": _noul_of(answers.get("isolated_reentry_is_new")),
        "two_stop_binds": _noul_of(answers.get("two_stop_binds")),
        "pin_ok": _noul_of(answers.get("pin_ok")),
        "may_send": _noul_of(answers.get("may_send")),
        "blocks_send": _noul_of(answers.get("blocks_send")),
        "fail_closed": _noul_of(answers.get("fail_closed")),
        "thin_state": _noul_of(answers.get("thin_state")),
        "already_placed_holds": _noul_of(answers.get("already_placed_holds")),
        "history_proved": _noul_of(answers.get("history_proved")),
        "error": error,
    }


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    pairs = (
        ("occupancy_after_close", row.get("choice")),
        ("reentry_threshold", row.get("threshold")),
        ("reentry_parameter", row.get("parameter")),
        ("reentry_loop", row.get("loop_bound")),
        ("two_stop_cap", row.get("two_stop_cap")),
        ("persist_weight", row.get("persist_weight")),
        ("remaining_state_sufficient", row.get("remaining_state_sufficient")),
        ("which_component", row.get("component")),
        ("component_exists", row.get("component_exists")),
        ("isolated_reentry_is_new", row.get("isolated_reentry_is_new")),
        ("two_stop_binds", row.get("two_stop_binds")),
        ("pin_ok", row.get("pin_ok")),
        ("may_send", row.get("may_send")),
        ("blocks_send", row.get("blocks_send")),
        ("fail_closed", row.get("fail_closed")),
        ("thin_state", row.get("thin_state")),
        ("already_placed_holds", row.get("already_placed_holds")),
        ("history_proved", row.get("history_proved")),
    )
    error = row.get("error") if isinstance(row.get("error"), str) else None
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = _scrub(dict(state))
    if not isinstance(logged, dict):
        logged = {}
    logged.pop("prior_outcomes", None)
    for key, value in pairs:
        try:
            append_outcome(key, value, logged, error=None if value is not None else error)
        except Exception:
            return


def evaluate_pack(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    *,
    timeout_s: float | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One POST through ``jev_client.evaluate``. A miss is an empty receipt."""

    payload = dict(state or {})
    for key, value in _pin_facts().items():
        payload.setdefault(key, value)
    payload = _scrub(payload)
    if not isinstance(payload, dict):
        payload = {}
    kept: dict[str, Any] = {}
    for key, body in dict(questions or {}).items():
        if _limit_key(str(key)) or not isinstance(body, Mapping):
            continue
        block = dict(body)
        if _question_ok(block):
            kept[str(key)] = block
    if not kept:
        kept = reentry_questions(payload)
    payload.pop("prior_outcomes", None)
    for key in (
        "occupancy_after_close",
        "reentry_threshold",
        "reentry_parameter",
        "reentry_loop",
        "two_stop_cap",
        "persist_weight",
        "remaining_state_sufficient",
        "which_component",
        "component_exists",
        "isolated_reentry_is_new",
        "two_stop_binds",
        "pin_ok",
        "may_send",
        "blocks_send",
        "fail_closed",
        "thin_state",
        "already_placed_holds",
        "history_proved",
    ):
        payload.pop(key, None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=kept)
        payload["prior_outcomes"] = loaded if isinstance(loaded, list) else []
    except Exception:
        payload["prior_outcomes"] = []
    payload["model"] = MODEL
    call = ask
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    try:
        receipt = call(
            payload,
            questions=kept,
            merge_sleeve=False,
            timeout_s=timeout_s,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a dark ask must not raise into the fire
        return {
            "ok": False,
            "skipped": None,
            "error": type(exc).__name__,
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
            "merge_sleeve": False,
        }
    if not isinstance(receipt, dict):
        return {
            "ok": False,
            "skipped": None,
            "error": "evaluate_not_a_dict",
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
            "merge_sleeve": False,
        }
    answers = receipt.get("answers")
    return {
        "ok": receipt.get("ok") is True,
        "skipped": receipt.get("skipped"),
        "error": receipt.get("error"),
        "model": receipt.get("model") or MODEL,
        "answers": answers if isinstance(answers, dict) else {},
        "kind": KIND_READ,
        "merge_sleeve": False,
    }


def ask_reentry(
    state: Mapping[str, Any] | None,
    *,
    timeout_s: float | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """The occupancy decision for this state. Empty, tie, and error stay unset."""

    questions = reentry_questions(state)
    try:
        receipt = evaluate_pack(dict(state or {}), questions, timeout_s=timeout_s, ask=ask)
    except Exception as exc:  # noqa: BLE001
        receipt = {
            "ok": False,
            "error": type(exc).__name__,
            "answers": {},
            "model": MODEL,
            "skipped": None,
        }
    answers = receipt.get("answers") if isinstance(receipt.get("answers"), dict) else {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    error_text = None if error in (None, "") else str(error)
    row = _read(answers, error_text)
    if row["choice"] is None and _choice_tied(answers.get("occupancy_after_close")):
        row["error"] = row.get("error") or "tie"
    row["ok"] = receipt.get("ok") is True
    row["skipped"] = receipt.get("skipped")
    row["model"] = receipt.get("model") or MODEL
    row["answers"] = answers
    row["receipt"] = {
        "ok": row["ok"],
        "skipped": row["skipped"],
        "error": receipt.get("error"),
        "model": row["model"],
        "answers": answers,
        "kind": KIND_READ,
    }
    _remember(state or {}, row)
    return row


def isolated_15m_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    raw = str(env.get(ENV) or "").strip().lower()
    return raw in _TRUE


def _pin_facts() -> dict[str, Any]:
    """Recorded pin attributes. The pin mark and the weight are the return."""

    try:
        from .gold_priors import GATE_COMPOSITE_WEIGHTS, PIN_WINDOW as PRIORS_PIN, assert_gold_pin
    except Exception as exc:
        return {
            "recorded_pin_window": None,
            "recorded_pin_persist": None,
            "pin_source": type(exc).__name__,
            "pin_assert_error": type(exc).__name__,
        }
    persist = None
    if isinstance(GATE_COMPOSITE_WEIGHTS, Mapping):
        persist = _number(GATE_COMPOSITE_WEIGHTS.get("persistence"))
    window = PRIORS_PIN if isinstance(PRIORS_PIN, str) and PRIORS_PIN else None
    assert_error = None
    try:
        assert_gold_pin()
    except Exception as exc:  # noqa: BLE001 — the assert result is a fact on the card
        assert_error = type(exc).__name__
    return {
        "recorded_pin_window": window,
        "recorded_pin_persist": persist,
        "pin_source": "gold_priors",
        "pin_assert_error": assert_error,
    }


def persist_pin_ok(
    *,
    ask: Callable[..., Any] | None = None,
    timeout_s: float | None = None,
) -> tuple[bool | float | None, None, dict[str, Any]]:
    """One ask. The pin noul and the persistence score are that return."""

    facts = _pin_facts()
    decided = ask_reentry({"rung": "isolated_15m", **facts}, timeout_s=timeout_s, ask=ask)
    pin_ok = _kept_noul(decided.get("pin_ok"))
    meta = {
        **facts,
        "pin_window": facts.get("recorded_pin_window"),
        "pin_ok": pin_ok,
        "persist_weight": decided.get("persist_weight"),
    }
    return pin_ok, None, meta


def fail_closed_reason(
    *,
    login: Any = None,
    ns: Any = None,
    origin: Any = None,
) -> str | None:
    raw_login = str(login or "").strip()
    if raw_login == VERIFICATION_QUARANTINED:
        return "verification_quarantined"
    origin_s = str(origin or "").strip().lower()
    if origin_s in {"w7", "ultimate_book"}:
        return "w7_other_organism"
    if raw_login and raw_login != CHALLENGE_LOGIN:
        return "wrong_login"
    raw_ns = str(ns or "").strip()
    if raw_ns and raw_ns != CHALLENGE_NS:
        return "wrong_ns"
    return None


def _mt5_naive_as_utc(raw: Any) -> datetime | None:
    text = str(raw or "").strip()
    if not text:
        return None
    iso = parse_utc(text)
    if iso is not None:
        return iso
    try:
        dt = datetime.strptime(text, _MT5_NAIVE)
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc)


def stamp_replay_clock(raw: Any) -> datetime | None:
    """Pack-45 ``open_time`` / ``close_time`` as UTC of record (not NY+7)."""
    return _mt5_naive_as_utc(raw)


def replay_row_to_deal(row: Mapping[str, Any]) -> dict[str, Any] | None:
    inp = dict(row.get("input") or row)
    open_utc = stamp_replay_clock(
        inp.get("open_time_utc") or inp.get("open_time")
    )
    close_utc = stamp_replay_clock(
        inp.get("close_time_utc") or inp.get("close_time")
    )
    ticket = inp.get("ticket") or inp.get("candidate_id")
    symbol = inp.get("symbol")
    if ticket in (None, "") or not symbol or open_utc is None:
        return None
    sleeve = str(inp.get("sleeve") or inp.get("tag") or inp.get("comment") or "")
    if sleeve.startswith("F5:"):
        sleeve = sleeve[3:]
    return {
        "ticket": int(ticket) if str(ticket).isdigit() else ticket,
        "symbol": symbol,
        "sleeve": sleeve,
        "side": inp.get("side"),
        "open_time_utc": open_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "close_time_utc": (
            close_utc.strftime("%Y-%m-%dT%H:%M:%SZ") if close_utc else None
        ),
        "still_open": bool(inp.get("still_open")),
        "exit_class": inp.get("exit_class"),
        "remint_of": inp.get("remint_of"),
        "login": inp.get("login") or CHALLENGE_LOGIN,
        "ns": inp.get("ns") or CHALLENGE_NS,
        "magic": inp.get("magic") or CHALLENGE_MAGIC,
        "broker_net": inp.get("broker_net"),
        "R": inp.get("R"),
        "pre_cut": inp.get("pre_cut"),
    }


def load_challenge_replay(path: Path | None = None) -> list[dict[str, Any]]:
    target = path or DEFAULT_REPLAY
    if not target.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        deal = replay_row_to_deal(rec if isinstance(rec, dict) else {})
        if deal is not None:
            out.append(deal)
    return out


def _stamp_deal(row: Mapping[str, Any]) -> datetime | None:
    return parse_utc(row.get("open_time_utc") or row.get("open_time"))


def _closed_doc_as_of(
    deals: Sequence[Mapping[str, Any]],
    *,
    as_of: datetime,
    this_ticket: Any,
) -> dict[str, Any]:
    """Integer 2-stop COUNT input. Prior orig_stops only. Not occupancy HOLD."""
    this = str(this_ticket)
    closed: list[dict[str, Any]] = []
    for row in deals:
        if str(row.get("ticket")) == this:
            continue
        if str(row.get("exit_class") or "").strip().lower() != "orig_stop":
            continue
        close_utc = parse_utc(row.get("close_time_utc") or row.get("close_time"))
        if close_utc is None or close_utc > as_of:
            continue
        closed.append(
            {
                "ticket": row.get("ticket"),
                "symbol": row.get("symbol"),
                "sleeve": row.get("sleeve"),
                "closed_utc": close_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "exit_class": "orig_stop",
            }
        )
    return {
        "closed": closed,
        "n_closed": len(closed),
        "two_stop_source": "closed[]",
        "note": "2-stop COUNT stays integer. Not occupancy HOLD.",
    }


def _measure_open(
    deal: Mapping[str, Any],
    deals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Facts for one open. The count is the integer. It is not the decision."""

    ticket = deal.get("ticket")
    symbol = str(deal.get("symbol") or "")
    sleeve = str(deal.get("sleeve") or "")
    as_of = _stamp_deal(deal)
    measured: dict[str, Any] = {
        "ticket": ticket,
        "symbol": symbol or None,
        "sleeve": sleeve or None,
        "side": deal.get("side"),
        "as_of_utc": None,
        "session_day": None,
        "minutes_since_flat": None,
        "symbol_open": None,
        "already_placed_today": None,
        "isolated_reentry_legal": None,
        "occupancy_source": None,
        "two_stop_count": None,
        "broker_net": deal.get("broker_net"),
        "exit_class": deal.get("exit_class"),
        "R": deal.get("R"),
    }
    if as_of is None or not symbol:
        return measured
    trades = trades_from_dicts(list(deals), stamp=_stamp_deal)
    tape = _tape_facts(trades, symbol=symbol, as_of=as_of, ticket=ticket)
    closed_doc = _closed_doc_as_of(deals, as_of=as_of, this_ticket=ticket)
    day = as_of.astimezone(timezone.utc).date().isoformat()
    two_stop_count = same_sleeve_orig_stop_count_session_day(
        closed_doc,
        sleeve=sleeve,
        session_day=day,
        symbol=symbol,
        as_of_utc=as_of,
    )
    measured.update(
        {
            "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "session_day": day,
            "minutes_since_flat": tape.get("minutes_since_flat"),
            "symbol_open": tape.get("symbol_open"),
            "already_placed_today": tape.get("already_placed_today"),
            "isolated_reentry_legal": None,
            "occupancy_source": "challenge_deals",
            "two_stop_count": two_stop_count,
        }
    )
    return measured


def _tape_facts(
    trades: Sequence[Any],
    *,
    symbol: str,
    as_of: datetime,
    ticket: Any,
) -> dict[str, Any]:
    """Tape evidence for the ask. It does not name the fire."""

    try:
        from .bars import normalize_symbol

        want = normalize_symbol(symbol)
    except Exception:
        want = str(symbol or "")
    moment = as_of if as_of.tzinfo else as_of.replace(tzinfo=timezone.utc)
    moment = moment.astimezone(timezone.utc)
    this = str(ticket).strip() if ticket not in (None, "") else None
    day = moment.date().isoformat()
    others_open = 0
    same_day = 0
    last_close: datetime | None = None
    for trade in trades:
        if getattr(trade, "symbol", None) != want:
            continue
        if this and str(getattr(trade, "ticket", "")) == this:
            continue
        opened = getattr(trade, "open_utc", None)
        closed = getattr(trade, "close_utc", None)
        if opened is not None and opened <= moment:
            live = bool(getattr(trade, "still_open", False)) or closed is None or closed > moment
            if live:
                others_open += 1
            if opened.date().isoformat() == day:
                same_day += 1
        if closed is not None and closed <= moment and (last_close is None or closed > last_close):
            last_close = closed
    minutes = None
    if last_close is not None:
        minutes = (moment - last_close).total_seconds() / 60.0
    return {
        "minutes_since_flat": minutes,
        "symbol_open": others_open > 0,
        "already_placed_today": same_day > 0,
    }


def _ask_state(deal: Mapping[str, Any], measured: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "identity": {
            "login": str(deal.get("login") or CHALLENGE_LOGIN),
            "ns": str(deal.get("ns") or CHALLENGE_NS),
            "magic": str(deal.get("magic") or CHALLENGE_MAGIC),
            "symbol": measured.get("symbol"),
            "sleeve": measured.get("sleeve"),
            "ticket": measured.get("ticket"),
            "side": measured.get("side"),
        },
        "occupancy": {
            "minutes_since_flat": measured.get("minutes_since_flat"),
            "symbol_open": measured.get("symbol_open"),
            "already_placed_today": measured.get("already_placed_today"),
            "isolated_reentry_legal": measured.get("isolated_reentry_legal"),
            "occupancy_source": measured.get("occupancy_source"),
            "two_stop_count": measured.get("two_stop_count"),
            "two_stop_is_integer": True,
            "hold_dead": True,
        },
        "clock": {"as_of_utc": measured.get("as_of_utc")},
        "never_flatten_tickets": list(NEVER_FLATTEN_TICKETS),
        "occupancy_hold_dead": True,
    }


def _kept_noul(value: Any) -> bool | float | None:
    """A returned noul. A miss stays missing."""

    if value is True or value is False:
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


def _with_decision(
    base: Mapping[str, Any],
    measured: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    choice = decision.get("choice")
    return {
        **base,
        "enabled": True,
        "action": choice,
        "reason": None if choice is None else f"occupancy_{choice}",
        "choice": choice,
        "probabilities": decision.get("probabilities") or {},
        "threshold": decision.get("threshold"),
        "parameter": decision.get("parameter"),
        "loop_bound": decision.get("loop_bound"),
        "two_stop_cap": decision.get("two_stop_cap"),
        "remaining_state_sufficient": decision.get("remaining_state_sufficient"),
        "component": decision.get("component"),
        "component_exists": decision.get("component_exists"),
        "isolated_reentry_is_new": decision.get("isolated_reentry_is_new"),
        "two_stop_binds": decision.get("two_stop_binds"),
        "two_stop_exhausted": decision.get("two_stop_binds"),
        "decision_error": decision.get("error"),
        "isolated_reentry_minutes": decision.get("threshold"),
        "fail_closed": _kept_noul(decision.get("fail_closed")),
        "pin_ok": _kept_noul(decision.get("pin_ok")),
        "thin_state": _kept_noul(decision.get("thin_state")),
        "already_placed_holds": _kept_noul(decision.get("already_placed_holds")),
        "history_proved": _kept_noul(decision.get("history_proved")),
        "isolated_reentry_legal": measured.get("isolated_reentry_legal"),
        "minutes_since_flat": measured.get("minutes_since_flat"),
        "symbol_open": measured.get("symbol_open"),
        "already_placed_today": measured.get("already_placed_today"),
        "occupancy_source": measured.get("occupancy_source"),
        "two_stop_count": measured.get("two_stop_count"),
        "two_stop_source": "closed[]",
        "two_stop_is_integer": True,
        "as_of_utc": measured.get("as_of_utc"),
        "session_day": measured.get("session_day"),
        "broker_net": measured.get("broker_net"),
        "exit_class": measured.get("exit_class"),
        "R": measured.get("R"),
        "kind": "choice",
        "may_send": _kept_noul(decision.get("may_send")),
        "blocks_send": _kept_noul(decision.get("blocks_send")),
        "persist_weight": decision.get("persist_weight"),
        "persist_apply": decision.get("persist_weight"),
        "model": decision.get("model") or MODEL,
    }


def classify_open(
    deal: Mapping[str, Any],
    *,
    deals: Sequence[Mapping[str, Any]],
    origin: Any = None,
    ask: Callable[..., Any] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Name the fire at this open. The name is the System One return."""

    ticket = deal.get("ticket")
    symbol = str(deal.get("symbol") or "")
    sleeve = str(deal.get("sleeve") or "")
    login = deal.get("login") or CHALLENGE_LOGIN
    ns = deal.get("ns") or CHALLENGE_NS
    closed_reason = fail_closed_reason(login=login, ns=ns, origin=origin)
    base = {
        "schema": SCHEMA,
        "steal": STEAL,
        "ticket": ticket,
        "symbol": symbol,
        "sleeve": sleeve,
        "login": str(login),
        "ns": str(ns),
        "magic": str(deal.get("magic") or CHALLENGE_MAGIC),
        "remint_of": deal.get("remint_of"),
        "occupancy_hold": False,
        "occupancy_hold_dead": True,
        "extra_pass": False,
        "apply": False,
        "flatten": False,
        "place": False,
        "remint": False,
        "may_send": None,
        "persist_weight": None,
        "pin_window": None,
        "two_stop_cap": None,
        "isolated_reentry_minutes": None,
        "isolated_reentry_is_new": None,
        "choice": None,
        "never_flatten_tickets": list(NEVER_FLATTEN_TICKETS),
        "kind": "LABEL",
        "write": False,
    }
    measured = _measure_open(deal, deals)
    state = _ask_state(deal, measured)
    state["identity_reason"] = closed_reason
    state["origin"] = None if origin is None else str(origin)
    state.update(_pin_facts())
    decision = ask_reentry(state, timeout_s=timeout_s, ask=ask)
    row = _with_decision(base, measured, decision)
    row["identity_reason"] = closed_reason
    row["pin_window"] = state.get("recorded_pin_window")
    return row


def prove_challenge_history(
    *,
    replay_path: Path | None = None,
    deals: Sequence[Mapping[str, Any]] | None = None,
    origin: Any = None,
    ask: Callable[..., Any] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Prove the named fire on Challenge pack history. Never places."""
    rows = list(deals) if deals is not None else load_challenge_replay(replay_path)
    by_action: dict[str, int] = {}
    classified: list[dict[str, Any]] = []
    occupancy_hold_n = 0
    extra_pass_n = 0
    for deal in rows:
        rec = classify_open(
            deal, deals=rows, origin=origin, ask=ask, timeout_s=timeout_s
        )
        classified.append(rec)
        by_action[str(rec.get("action"))] = by_action.get(str(rec.get("action")), 0) + 1
        if rec.get("occupancy_hold"):
            occupancy_hold_n += 1
        if rec.get("extra_pass"):
            extra_pass_n += 1
    named = [r for r in classified if r.get("action") == "named_fire"]
    short = [r for r in classified if r.get("action") == "not_isolated"]
    first = [r for r in classified if r.get("action") == "first_print"]
    walked = next((r for r in classified if r.get("ticket") == WALKED_HI_CHILD), None)
    walked_parent = next((r for r in classified if r.get("ticket") == WALKED_HI_PARENT), None)
    us30_short = next((r for r in classified if r.get("ticket") == US30_SHORT_CHILD), None)
    fail_any = next((r for r in classified if r.get("fail_closed")), None)
    recorded = _pin_facts()
    decided = ask_reentry(
        {
            "rung": "isolated_15m_history",
            "login": CHALLENGE_LOGIN,
            "namespace": CHALLENGE_NS,
            "n": len(rows),
            "n_named_fire": len(named),
            "n_not_isolated": len(short),
            "n_first_print": len(first),
            "occupancy_hold_n": occupancy_hold_n,
            "extra_pass_n": extra_pass_n,
            "fail_row_present": fail_any is not None,
            "walked_present": walked is not None,
            "walked_is_new": None if walked is None else walked.get("isolated_reentry_is_new"),
            "walked_minutes": None if walked is None else walked.get("minutes_since_flat"),
            "walked_parent_net": None if walked_parent is None else walked_parent.get("broker_net"),
            "walked_child_net": None if walked is None else walked.get("broker_net"),
            "us30_present": us30_short is not None,
            "us30_is_new": None if us30_short is None else us30_short.get("isolated_reentry_is_new"),
            "us30_minutes": None if us30_short is None else us30_short.get("minutes_since_flat"),
        },
        timeout_s=timeout_s,
        ask=ask,
    )
    proved = _kept_noul(decided.get("history_proved"))
    pin_ok = _kept_noul(decided.get("pin_ok"))
    return {
        "schema": SCHEMA,
        "steal": STEAL,
        "enabled": True,
        "proved": proved,
        "fail_closed": _kept_noul(decided.get("fail_closed")),
        "fail_closed_reason": None if fail_any is None else fail_any.get("identity_reason"),
        "persist_ok": pin_ok,
        "persist_reason": None,
        "persist_weight": decided.get("persist_weight"),
        "pin_window": recorded.get("recorded_pin_window"),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "n": len(rows),
        "by_action": by_action,
        "n_named_fire": len(named),
        "n_not_isolated": len(short),
        "n_first_print": len(first),
        "occupancy_hold_n": occupancy_hold_n,
        "occupancy_hold_dead": True,
        "extra_pass": False,
        "apply": False,
        "flatten": False,
        "place": False,
        "remint": False,
        "may_send": _kept_noul(decided.get("may_send")),
        "two_stop_cap": decided.get("two_stop_cap"),
        "two_stop_is_integer": True,
        "isolated_reentry_minutes": decided.get("threshold"),
        "walked_hi": {
            "parent": WALKED_HI_PARENT,
            "child": WALKED_HI_CHILD,
            "parent_net_usd": None if walked_parent is None else walked_parent.get("broker_net"),
            "child_net_usd": None if walked is None else walked.get("broker_net"),
            "minutes_since_flat": None if walked is None else walked.get("minutes_since_flat"),
            "isolated_reentry_is_new": None if walked is None else walked.get("isolated_reentry_is_new"),
            "action": None if walked is None else walked.get("action"),
            "two_stop_count": None if walked is None else walked.get("two_stop_count"),
        },
        "us30_short": {
            "parent": US30_SHORT_PARENT,
            "child": US30_SHORT_CHILD,
            "minutes_since_flat": None if us30_short is None else us30_short.get("minutes_since_flat"),
            "isolated_reentry_is_new": None if us30_short is None else us30_short.get("isolated_reentry_is_new"),
            "action": None if us30_short is None else us30_short.get("action"),
        },
        "never_flatten_tickets": list(NEVER_FLATTEN_TICKETS),
        "kind": "LABEL",
        "rows": classified,
    }


def maybe_prove_isolated_15m(
    *,
    replay_path: Path | None = None,
    deals: Sequence[Mapping[str, Any]] | None = None,
    origin: Any = None,
    environ: Mapping[str, str] | None = None,
    ask: Callable[..., Any] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Occupancy Choice. Always POSTs. Not a LABEL skip."""
    del environ
    pack = prove_challenge_history(
        replay_path=replay_path,
        deals=deals,
        origin=origin,
        ask=ask,
        timeout_s=timeout_s,
    )
    pack["skipped"] = None
    live = decide_isolated_15m_live(history=pack, timeout_s=timeout_s, ask=ask)
    pack["kind"] = "choice"
    pack["choice"] = live.get("choice")
    pack["probabilities"] = live.get("probabilities") or {}
    pack["disposition"] = live.get("disposition")
    pack["reason"] = live.get("reason")
    pack["occupancy_after_close"] = live.get("occupancy_after_close")
    pack["remaining_state_sufficient"] = live.get("remaining_state_sufficient")
    pack["threshold"] = live.get("threshold")
    pack["parameter"] = live.get("parameter")
    pack["loop_bound"] = live.get("loop_bound")
    pack["two_stop_cap"] = live.get("two_stop_cap")
    pack["isolated_reentry_minutes"] = live.get("threshold")
    pack["component"] = live.get("component")
    pack["component_exists"] = live.get("component_exists")
    pack["isolated_reentry_is_new"] = live.get("isolated_reentry_is_new")
    pack["may_send"] = live.get("may_send")
    pack["blocks_send"] = live.get("blocks_send")
    pack["missing_jev"] = live.get("missing_jev")
    pack["persist_ok"] = live.get("pin_ok")
    pack["persist_reason"] = None
    pack["persist_apply"] = live.get("persist_weight")
    pack["persist_weight"] = live.get("persist_weight")
    pack["pin_ok"] = live.get("pin_ok")
    pack["mill_url"] = None
    pack["live_fanout_ok"] = live.get("live_fanout_ok")
    pack["live_fanout_skipped"] = live.get("live_fanout_skipped")
    pack["live_n_calls"] = live.get("live_n_calls")
    pack["live_hop"] = live.get("live_hop")
    pack["place"] = False
    pack["flatten"] = False
    pack["extra_pass"] = False
    pack["occupancy_hold"] = False
    pack["occupancy_hold_dead"] = True
    pack["already_placed_not_lifted"] = live.get("already_placed_holds")
    pack["never_flatten_tickets"] = list(NEVER_FLATTEN_TICKETS)
    return pack


def write_prove(pack: Mapping[str, Any], path: Path | None = None) -> Path:
    target = path or DEFAULT_PROVE
    target.parent.mkdir(parents=True, exist_ok=True)
    slim = {k: v for k, v in dict(pack).items() if k != "rows"}
    target.write_text(json.dumps(slim, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def isolated_include_depth_questions(
    state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """One occupancy ask. Not a catalog dump. A floor is not a question."""

    return reentry_questions(state)


def isolated_decision_questions(
    state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Same occupancy ask. The decision and the parameter are that return."""

    return reentry_questions(state)


def isolated_intent_packs(
    state: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    questions = reentry_questions(state)
    return {
        "occupancy": questions,
        "include_depth": questions,
        "decision": questions,
    }


def fanout_isolated_15m(
    state: dict[str, Any],
    *,
    timeout_s: float | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One post. A second hop is not added."""

    row = ask_reentry(state, timeout_s=timeout_s, ask=ask)
    receipt = row.get("receipt") if isinstance(row.get("receipt"), dict) else {}
    return {
        "ok": row.get("ok") is True,
        "skipped": row.get("skipped"),
        "error": row.get("error"),
        "answers": row.get("answers") if isinstance(row.get("answers"), dict) else {},
        "decision": row,
        "include_receipt": receipt,
        "decision_receipt": receipt,
        "n_calls": 1,
        "kind": KIND_READ,
        "merge_sleeve": False,
        "never_second_llm_hop": True,
        "model": row.get("model") or MODEL,
    }


def _hop_state_from_history(history: Mapping[str, Any] | None) -> dict[str, Any]:
    """Facts from the last measured row. Missing fields stay missing."""

    hist = dict(history or {})
    rows = [row for row in list(hist.get("rows") or []) if isinstance(row, dict)]
    last = rows[-1] if rows else {}
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "identity": {
            "login": str(last.get("login") or CHALLENGE_LOGIN),
            "ns": str(last.get("ns") or CHALLENGE_NS),
            "magic": str(last.get("magic") or CHALLENGE_MAGIC),
            "symbol": last.get("symbol"),
            "sleeve": last.get("sleeve"),
            "ticket": last.get("ticket"),
        },
        "occupancy": {
            "minutes_since_flat": last.get("minutes_since_flat"),
            "symbol_open": last.get("symbol_open"),
            "already_placed_today": last.get("already_placed_today"),
            "isolated_reentry_legal": last.get("isolated_reentry_legal"),
            "two_stop_count": last.get("two_stop_count"),
            "two_stop_is_integer": True,
            "hold_dead": True,
        },
        "clock": {"as_of_utc": last.get("as_of_utc")},
        "history": {
            "n": hist.get("n"),
            "n_named_fire": hist.get("n_named_fire"),
            "n_not_isolated": hist.get("n_not_isolated"),
            "n_first_print": hist.get("n_first_print"),
            "proved": hist.get("proved"),
        },
        "never_flatten_tickets": list(NEVER_FLATTEN_TICKETS),
        "occupancy_hold_dead": True,
    }


def decide_isolated_15m_live(
    *,
    history: Mapping[str, Any] | None = None,
    timeout_s: float | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """This occupancy hop. The return is the decision. A miss stays unset."""

    state = _hop_state_from_history(history)
    fanout = fanout_isolated_15m(state, timeout_s=timeout_s, ask=ask)
    row = fanout.get("decision") if isinstance(fanout.get("decision"), dict) else {}
    choice = row.get("choice")
    sufficient = row.get("remaining_state_sufficient")
    probabilities = row.get("probabilities") if isinstance(row.get("probabilities"), dict) else {}
    return {
        "kind": "choice",
        "hop": "occupancy",
        "disposition": choice,
        "choice": choice,
        "reason": None if choice is None else f"occupancy_{choice}",
        "probabilities": probabilities,
        "confidence": probabilities.get(choice) if choice else None,
        "occupancy_after_close": choice,
        "remaining_state_sufficient": sufficient,
        "isolated_state_sufficient": sufficient,
        "completeness_noul": sufficient,
        "thin_state": _kept_noul(row.get("thin_state")),
        "threshold": row.get("threshold"),
        "parameter": row.get("parameter"),
        "loop_bound": row.get("loop_bound"),
        "two_stop_cap": row.get("two_stop_cap"),
        "component": row.get("component"),
        "component_exists": row.get("component_exists"),
        "isolated_reentry_is_new": row.get("isolated_reentry_is_new"),
        "two_stop_binds": row.get("two_stop_binds"),
        "may_send": _kept_noul(row.get("may_send")),
        "blocks_send": _kept_noul(row.get("blocks_send")),
        "pin_ok": _kept_noul(row.get("pin_ok")),
        "fail_closed": _kept_noul(row.get("fail_closed")),
        "history_proved": _kept_noul(row.get("history_proved")),
        "place": False,
        "flatten": False,
        "apply": False,
        "extra_pass": False,
        "missing_jev": choice is None,
        "mill_url": None,
        "live_fanout_ok": fanout.get("ok"),
        "live_fanout_skipped": fanout.get("skipped"),
        "live_n_calls": fanout.get("n_calls"),
        "live_hop": "occupancy_after_close",
        "never_flatten_tickets": list(NEVER_FLATTEN_TICKETS),
        "occupancy_hold": False,
        "occupancy_hold_dead": True,
        "two_stop_is_integer": True,
        "persist_weight": row.get("persist_weight"),
        "persist_apply": row.get("persist_weight"),
        "already_placed_not_lifted": _kept_noul(row.get("already_placed_holds")),
        "integer_action": choice,
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
    }



def module_source() -> str:
    return Path(__file__).read_text(encoding="utf-8")


def leftover_ship_imports(tree: Any | None = None) -> list[str]:
    """AST names only. Docstrings may mention book_owner as a *do-not*."""
    import ast

    root = tree if tree is not None else ast.parse(module_source())
    hit: list[str] = []
    banned = {"book_owner", "order_send", "open_trade", "RealMT5"}
    for node in ast.walk(root):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[-1]
                if name in banned:
                    hit.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if any(part in banned for part in mod.split(".")):
                hit.append(mod)
            for alias in node.names:
                if alias.name in banned:
                    hit.append(alias.name)
        elif isinstance(node, ast.Attribute) and node.attr in banned:
            hit.append(node.attr)
        elif isinstance(node, ast.Name) and node.id in banned:
            hit.append(node.id)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in banned:
                hit.append(func.id)
            if isinstance(func, ast.Attribute) and func.attr in banned:
                hit.append(func.attr)
    return sorted(set(hit))
