"""CHALLENGE_COMMAND_CENTER_V0 — redacted_account current-truth page for Challenge 0.

Unique file. Read-only. The env flag is a fact on the card.

Every decision on this page, including every parameter, is the System One
return for that state. One hop is ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False`` (POST
https://api.typesafe.ai/v1/systemone). Questions are only Noul, Choice, or
Score. Prior outcomes are attached on that ask, and the return is stored
for the next ask.

The page verb is the unique highest probability. Persistence, the page
parameter, staleness hours, and the micro lot are the returned scores and
may sit between levels. The pin window and the haircut are Choices. Sit
staleness is a Noul. An empty answer, a tie, a missing score, or an error
leaves that field unset and does not restore a constant. A floor and a
baseline are not a question.

The loaded pin file is a fact on the card. The persistence parameter is
the returned score. An empty score leaves it absent. This page does not
place, remint, flatten, bounce, leftover-ship ``book_owner``, or send.
Judge code stays unable to send. A missing sit grants no extra PASS.

Host hook (observer, env-gate BEFORE import, never refuse a fire):

    if os.environ.get("GTOS_JEV_COMMAND_CENTER", "").strip().lower() in {"1", "true", "yes"}:
        from src.judgment.challenge_command_center import maybe_run_command_center
        maybe_run_command_center(sit_path=latest_sit)

The env flag is a fact on the card. The ask still runs. W7 is a fact
on that card. This page does not send.
"""

from __future__ import annotations

import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .rung_choice import append_record, namespace_root, open_pair, read_json

try:
    from .challenge import (
        CHALLENGE_LOGIN,
        CHALLENGE_MAGIC,
        CHALLENGE_NS,
        VERIFICATION_QUARANTINED,
        account_surface,
    )
except Exception:
    CHALLENGE_LOGIN = "0"
    CHALLENGE_MAGIC = 0
    CHALLENGE_NS = "operator"
    VERIFICATION_QUARANTINED = "0"
    account_surface = None

MappingLike = Mapping[str, Any]

SCHEMA = "gtos.judgment.challenge_command_center.v0"
SIT_SCHEMA = "gtos.judgment.challenge_command_center.sit.v0"
COMMAND_CENTER_ENV = "GTOS_JEV_COMMAND_CENTER"
COMMAND_CENTER_PATH_ENV = "GTOS_JEV_COMMAND_CENTER_PATH"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_DIR = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_command_center" / "fixtures"
)
DEFAULT_SIT = DEFAULT_FIXTURE_DIR / "sit_fleet.json"
DEFAULT_OUT = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_command_center" / "last_run.summary.json"
)

FN_LOGIN = "0"
FN_NS = "redacted_account_live_bee34003"
W7_NS = "operator_profile"
W7_ARMED_TAGS = frozenset({"crypto", "energy_agri", "sub_xvol_pullback"})

FRIEND_LOGINS = {
    "sh": "0",
    "redacted_account": "0",
    "redacted_account": "1514684855",
}

# Chair 2026-09-21 named tickets. Never flatten / never bounce the writer over them.
CHAIR_NAMED_OPEN_TICKETS = frozenset({294092360, 294088097})
CHAIR_NAMED_CLOSED_NO_TOUCH = frozenset({294069721})
LEAVE_ORIG_TICKETS = frozenset({293332188}) | CHAIR_NAMED_OPEN_TICKETS | CHAIR_NAMED_CLOSED_NO_TOUCH
FRIEND_NAMED_TICKETS = frozenset(
    {546434379, 546434380, 546434381, 546434384, 546434385, 546434386}
)
NEVER_FLATTEN_TICKETS = LEAVE_ORIG_TICKETS | FRIEND_NAMED_TICKETS

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"

CHAIR_VERBS = ("ENFORCE", "VETO", "LABEL")
_VERB_CRITERIA = {
    "ENFORCE": "The current-truth page carries the enforce verb.",
    "VETO": "The current-truth page carries the veto verb.",
    "LABEL": "The current-truth page carries the label verb.",
}
PIN_WINDOWS = ("G-FULL", "Y2025")
_PIN_CRITERIA = {
    "G-FULL": "This state carries the G-FULL window.",
    "Y2025": "This state carries the Y2025 window.",
}
_IDENTITY_ORDER = (
    "challenge",
    "verification_quarantined",
    "w7_other_organism",
    "not_challenge",
    "namespace_not_challenge",
    "identity_missing",
)
_IDENTITY_CRITERIA = {
    "challenge": "The login and namespace on this state are the challenge book.",
    "verification_quarantined": "The login on this state is the quarantined verification book.",
    "w7_other_organism": "The namespace or tags on this state are the other organism.",
    "not_challenge": "The login on this state is outside the challenge book.",
    "namespace_not_challenge": "The namespace on this state is outside the challenge book.",
    "identity_missing": "Login and namespace are both absent on this state.",
}
HAIRCUTS = ("leave-orig", "label")
_HAIRCUT_CRITERIA = {
    "leave-orig": "This page leaves the named tickets as they stand.",
    "label": "This page carries a label and does not move a ticket.",
}
PANELS = (
    "fleet",
    "challenge",
    "exposure",
    "payout",
    "redacted_account",
    "friends",
    "jev",
    "quarantine",
    "chair",
)

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LIMIT_PARTS = (
    "floor",
    "baseline",
    "to_pass",
    "pass_line",
    "pass_target",
    "floor_room",
    "drawdown",
    "profit_target",
    "max_loss",
    "daily_loss",
    "day_start",
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
_SECRET_PARTS = ("api_key", "apikey", "authorization", "secret", "password", "token")
_DROP = object()
_LOCAL_OUTCOMES: list[dict[str, Any]] = []
_QUESTION_IDS = (
    "page_verb",
    "page_parameter",
    "persist_weight",
    "pin_window",
    "stale_hours",
    "sit_stale",
    "micro_lot",
    "haircut",
    "pin_ok",
    "identity_ok",
    "identity_label",
    "tag_menu_note",
)


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


def _limit_key(name: str) -> bool:
    low = str(name).lower().replace("-", "_")
    return any(part in low for part in _LIMIT_PARTS)


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").replace(" ", "").lower()
    return any(
        token.replace(",", "").replace("_", "").replace(" ", "").lower() in compact
        for token in _BANNED_TEXT
    )


def _secret_key(name: str) -> bool:
    low = str(name).lower().replace("-", "_")
    return any(part in low for part in _SECRET_PARTS)


def _question_text_ok(value: str) -> bool:
    low = value.lower()
    if "floor" in low or "baseline" in low:
        return False
    if _banned_text(value):
        return False
    if "order" + "_send" in low or "ran" + "dom" in low:
        return False
    return True


def _scrub(value: Any, depth: int = 0) -> Any:
    """Drop a floor and a baseline before the ask. They are not a question."""

    if depth > 8:
        return _DROP
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        if _banned_text(value) or _limit_key(value):
            return _DROP
        return value
    if isinstance(value, (int, float)):
        number = _finite(value)
        if number is None or number in (90000.0, 110000.0):
            return _DROP
        return number
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name) or _secret_key(name):
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
            if cleaned is not _DROP:
                kept.append(cleaned)
        return kept
    text = str(value)
    if _banned_text(text) or _limit_key(text):
        return _DROP
    return text


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        if _limit_key(key) or _secret_key(key) or "persist" in key.lower():
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
        if number is not None and number not in (90000.0, 110000.0):
            found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    names = [format(number, ".10g") for number in sorted(set(found))]
    return names or list(_BETWEEN)


def _choice_body(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    kept = {
        str(key): str(text)
        for key, text in criteria.items()
        if _question_text_ok(str(key)) and _question_text_ok(str(text))
    }
    block: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": kept,
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(kept))
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        pass
    block["type"] = "choice"
    block["instructions"] = instructions
    block["criteria"] = kept
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    return {qid: block}


def _score_body(qid: str, instructions: str, levels: list[str]) -> dict[str, Any]:
    block: dict[str, Any] = {"type": "score", "instructions": instructions}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        pass
    block["type"] = "score"
    block["instructions"] = instructions
    named = [str(item) for item in levels if _question_text_ok(str(item))]
    block["criteria"] = named or list(_BETWEEN)
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    return {qid: block}


def _noul_body(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {"true": yes, "false": no},
        }
    }


def command_center_questions(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One card for this state. Noul, Choice, or Score only. Floor and baseline are not on it."""

    facts = _scrub(dict(state or {}))
    if not isinstance(facts, dict):
        facts = {}
    scale = _levels(facts)
    pack: dict[str, Any] = {}
    pack.update(_choice_body(
        "page_verb",
        (
            "What verb does the current-truth page carry for this state? "
            "The unique highest probability is the verb. "
            "An empty answer or a tie leaves the verb unset. "
            "This question does not place, flatten, bounce, or send."
        ),
        _VERB_CRITERIA,
    ))
    pack.update(_score_body(
        "page_parameter",
        (
            "The score you return is the parameter of that page verb. "
            "It may sit between the levels on this state. "
            "An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        scale,
    ))
    pack.update(_score_body(
        "persist_weight",
        (
            "The score you return is the persistence parameter for this state. "
            "It may sit between the levels on this state. "
            "An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        scale,
    ))
    pack.update(_choice_body(
        "pin_window",
        (
            "Which pin window is this state? "
            "The unique highest probability is the window. "
            "An empty answer or a tie leaves the window unset. "
            "This question does not send."
        ),
        _PIN_CRITERIA,
    ))
    pack.update(_score_body(
        "stale_hours",
        (
            "The score you return is the staleness parameter for this sit, in hours. "
            "It may sit between the levels on this state. "
            "An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        scale,
    ))
    pack.update(_noul_body(
        "sit_stale",
        (
            "Is this sit stale for this state? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "This question does not send."
        ),
        "This sit is stale.",
        "This sit is not stale.",
    ))
    pack.update(_score_body(
        "micro_lot",
        (
            "The score you return is the micro lot parameter for this state. "
            "It may sit between the levels on this state. "
            "An empty score leaves the parameter unset. "
            "This question does not send."
        ),
        scale,
    ))
    pack.update(_choice_body(
        "haircut",
        (
            "What haircut does this page carry? "
            "The unique highest probability is the haircut. "
            "An empty answer or a tie leaves the haircut unset. "
            "This question does not send."
        ),
        _HAIRCUT_CRITERIA,
    ))
    pack.update(_noul_body(
        "pin_ok",
        (
            "Are the recorded pin attributes on this state the pin for this page? "
            "An empty noul leaves the pin unset. "
            "This question does not send."
        ),
        "The recorded pin is the pin for this page.",
        "The recorded pin is not the pin for this page.",
    ))
    pack.update(_noul_body(
        "identity_ok",
        (
            "Are the login and namespace on this state the challenge book? "
            "An empty noul leaves identity unset. "
            "This question does not send."
        ),
        "This state is the challenge book.",
        "This state is outside the challenge book.",
    ))
    pack.update(_choice_body(
        "identity_label",
        (
            "Which identity label do the login, namespace, and tags on this state carry? "
            "The unique highest probability is the label. "
            "An empty answer or a tie leaves the label unset. "
            "This question does not send."
        ),
        _IDENTITY_CRITERIA,
    ))
    pack.update(_noul_body(
        "tag_menu_note",
        (
            "Does the tag menu on this state carry a note? "
            "The tag count and the tag names are facts. "
            "An empty noul leaves the note unset. "
            "This question does not send."
        ),
        "The tag menu carries a note.",
        "The tag menu carries no note.",
    ))
    clean: dict[str, Any] = {}
    allowed = {"noul", "choice", "score"}
    for qid, block in pack.items():
        if not isinstance(block, dict):
            continue
        kind = str(block.get("type") or "")
        if kind not in allowed or _limit_key(qid):
            continue
        texts = [str(block.get("instructions") or "")]
        criteria = block.get("criteria")
        if isinstance(criteria, dict):
            texts.extend(str(key) for key in criteria)
            texts.extend(str(text) for text in criteria.values())
        elif isinstance(criteria, list):
            texts.extend(str(item) for item in criteria)
        if any(not _question_text_ok(text) for text in texts):
            continue
        clean[str(qid)] = block
    return clean


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return {}
    allowed = {str(name) for name in order}
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _finite(val)
        if number is None:
            continue
        numeric[name] = number
    return numeric


def _local_unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in order:
        if name not in probabilities:
            continue
        seen = True
        prob = probabilities[name]
        if best_p is None or prob > best_p + 1e-12:
            best = name
            best_p = prob
            tied = False
        elif abs(prob - best_p) <= 1e-12:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice_of(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float], bool]:
    """Unique highest. A bare label, an empty map, or a tie is unset."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None, {}, False
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"", "choice"}:
        return None, {}, False
    probs = _probabilities(block, order)
    if not probs:
        return None, {}, False
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
        return None, kept, True
    if str(agreed) not in order:
        return None, kept, True
    return str(agreed), kept, False


def _score_of(block: Any) -> float | None:
    """The returned number. A missing score stays missing. It is not snapped."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"", "score"}:
        return None
    raw_probs = block.get("probabilities")
    names = tuple(str(key) for key in raw_probs) if isinstance(raw_probs, Mapping) else ()
    probs = _probabilities(block, names)
    if probs and _local_unique(probs, names) is None:
        return None
    parsed: float | None = None
    try:
        from .jev_questions import returned_number

        parsed = _finite(returned_number(block))
    except Exception:
        parsed = None
    if parsed is not None:
        return parsed
    for key in ("score", "value"):
        if key in block and block.get(key) is not None:
            number = _finite(block.get(key))
            if number is not None:
                return number
    return None


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if block is True or block is False:
        return block
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        value = block.get("noul") if "noul" in block else block.get("Noul")
        if value is None:
            return None
        if value is True or value is False:
            return value
        return _finite(value)
    picked, _kept, _tied = _choice_of(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _blank_return(error: str | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "model": MODEL,
        "api_url": API_URL,
        "choice": None,
        "page_verb": None,
        "probability": None,
        "probabilities": {},
        "page_parameter": None,
        "persist_weight": None,
        "pin_window": None,
        "stale_hours": None,
        "sit_stale": None,
        "micro_lot": None,
        "haircut": None,
        "pin_ok": None,
        "identity_ok": None,
        "identity_label": None,
        "tag_menu_note": None,
        "decision_emitted": False,
        "error": error,
        "http_status": None,
        "answers": {},
    }


def _read_return(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    row = _blank_return()
    body = answers if isinstance(answers, Mapping) else {}
    choice, probs, tied = _choice_of(body.get("page_verb"), CHAIR_VERBS)
    pin, _pin_probs, _pin_tied = _choice_of(body.get("pin_window"), PIN_WINDOWS)
    haircut, _hair_probs, _hair_tied = _choice_of(body.get("haircut"), HAIRCUTS)
    identity, _id_probs, _id_tied = _choice_of(body.get("identity_label"), _IDENTITY_ORDER)
    row["choice"] = choice if choice in CHAIR_VERBS else None
    row["page_verb"] = row["choice"]
    row["probabilities"] = probs
    row["probability"] = probs.get(row["choice"]) if row["choice"] is not None else None
    row["page_parameter"] = _score_of(body.get("page_parameter"))
    row["persist_weight"] = _score_of(body.get("persist_weight"))
    row["pin_window"] = pin if pin in PIN_WINDOWS else None
    row["stale_hours"] = _score_of(body.get("stale_hours"))
    row["sit_stale"] = _noul_of(body.get("sit_stale"))
    row["micro_lot"] = _score_of(body.get("micro_lot"))
    row["haircut"] = haircut if haircut in HAIRCUTS else None
    row["pin_ok"] = _noul_of(body.get("pin_ok"))
    row["identity_ok"] = _noul_of(body.get("identity_ok"))
    row["identity_label"] = identity if identity in _IDENTITY_ORDER else None
    row["tag_menu_note"] = _noul_of(body.get("tag_menu_note"))
    row["decision_emitted"] = row["choice"] is not None
    row["answers"] = dict(body)
    if row["choice"] is None:
        row["error"] = "tie" if tied else "empty"
        row["ok"] = False
    else:
        row["ok"] = True
        row["error"] = None
    return row


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    loaded: Any = None
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        loaded = [dict(item) for item in _LOCAL_OUTCOMES]
    cleaned = _scrub(loaded)
    if cleaned is _DROP or not isinstance(cleaned, list):
        cleaned = []
    state["prior_outcomes"] = cleaned


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    """History for the next ask. A miss is stored as a miss, not filled back."""

    error = row.get("error") if isinstance(row.get("error"), str) else None

    def _miss(value: Any) -> str | None:
        return None if value is not None else (error or "unset")

    pairs = (
        ("page_verb", row.get("choice"), _miss(row.get("choice"))),
        ("page_parameter", row.get("page_parameter"), _miss(row.get("page_parameter"))),
        ("persist_weight", row.get("persist_weight"), _miss(row.get("persist_weight"))),
        ("pin_window", row.get("pin_window"), _miss(row.get("pin_window"))),
        ("stale_hours", row.get("stale_hours"), _miss(row.get("stale_hours"))),
        ("sit_stale", row.get("sit_stale"), _miss(row.get("sit_stale"))),
        ("micro_lot", row.get("micro_lot"), _miss(row.get("micro_lot"))),
        ("haircut", row.get("haircut"), _miss(row.get("haircut"))),
        ("pin_ok", row.get("pin_ok"), _miss(row.get("pin_ok"))),
        ("identity_ok", row.get("identity_ok"), _miss(row.get("identity_ok"))),
        ("identity_label", row.get("identity_label"), _miss(row.get("identity_label"))),
        ("tag_menu_note", row.get("tag_menu_note"), _miss(row.get("tag_menu_note"))),
    )
    logged = _scrub(dict(state))
    if not isinstance(logged, dict):
        logged = {}
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, miss in pairs:
            _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": miss})
        return
    for key, value, miss in pairs:
        try:
            append_outcome(key, value, logged, error=miss)
        except Exception:
            return


def ask_command_center(
    state: Mapping[str, Any] | None = None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One System One post. Empty, tie, and error leave the fields unset."""

    questions = command_center_questions(state)
    payload = dict(state or {})
    for key, value in _pin_facts().items():
        payload.setdefault(key, value)
    payload = _scrub(payload)
    if not isinstance(payload, dict):
        payload = {}
    for key in _QUESTION_IDS:
        payload.pop(key, None)
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    payload["order_send"] = False
    if not questions:
        row = _blank_return("empty")
        _remember(payload, row)
        return row
    _attach_priors(payload, questions)
    call = evaluate_fn
    if call is None:
        try:
            from .jev_client import evaluate
        except Exception as exc:
            row = _blank_return(type(exc).__name__)
            _remember(payload, row)
            return row
        call = evaluate
    try:
        receipt = call(payload, questions=questions, merge_sleeve=False, model=MODEL)
    except Exception as exc:  # noqa: BLE001 — a dark ask must not raise into the writer
        row = _blank_return(type(exc).__name__)
        _remember(payload, row)
        return row
    if not isinstance(receipt, dict):
        row = _blank_return("evaluate_not_a_dict")
        _remember(payload, row)
        return row
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        err = receipt.get("error") or receipt.get("skipped") or "empty"
        row = _blank_return(str(err))
        row["http_status"] = receipt.get("http_status")
        row["model"] = receipt.get("model") or MODEL
        _remember(payload, row)
        return row
    row = _read_return(answers)
    row["http_status"] = receipt.get("http_status")
    row["model"] = receipt.get("model") or MODEL
    if row["choice"] is None and receipt.get("error"):
        row["error"] = str(receipt.get("error"))
    elif row["choice"] is not None:
        row["ok"] = receipt.get("ok") is not False
        row["error"] = None
    _remember(payload, row)
    return row


def _returned_mark(value: Any) -> bool:
    """A returned noul is present. A miss and an explicit false are not that mark."""

    if value is True:
        return True
    if value is False or value is None:
        return False
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _structural_marks() -> dict[str, Any]:
    """This module cannot place, flatten, remint, bounce, or send. Those marks are not asks."""

    return {
        "extra_pass": False,
        "apply": False,
        "silent_apply": False,
        "never_place": True,
        "never_flatten": True,
        "never_remint": True,
        "never_bounce": True,
        "order_send": False,
        "overlay_77_copied": False,
        "do_not_flatten_tickets": never_flatten_tickets(),
    }


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def command_center_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Default-OFF. Unset / empty / 0 is off."""

    return _env_on(COMMAND_CENTER_ENV, environ)


def default_sit_path() -> Path:
    override = (os.environ.get(COMMAND_CENTER_PATH_ENV) or "").strip()
    return Path(override) if override else DEFAULT_SIT


def never_flatten_tickets() -> list[int]:
    return sorted(NEVER_FLATTEN_TICKETS)


def _login_text(value: Any) -> str:
    if value is None or value == "":
        return ""
    return str(value).strip()


def _as_int_ticket(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _fail(
    reason: str,
    *,
    enabled: bool,
    extra: MappingLike | None = None,
    fail_closed: bool | None = None,
) -> dict[str, Any]:
    closed = enabled if fail_closed is None else fail_closed
    skipped = None if enabled else "GTOS_JEV_COMMAND_CENTER_off"
    row: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "api_url": API_URL,
        "account": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "pass_target": None,
        "enabled": enabled,
        "skipped": skipped,
        "asked": False,
        "fail_closed": closed,
        "fail_closed_reason": reason if closed else skipped,
        "page_emitted": False,
        "choice": None,
        "page_verb": None,
        "page_parameter": None,
        "persist_weight": None,
        "pin_window": None,
        "stale_hours": None,
        "sit_stale": None,
        "micro_lot": None,
        "haircut": None,
        "books": [],
        "panels": {},
        "findings": [],
        "html": "",
        "markdown": "",
        "decision": (
            "No extra PASS. Command center does not splice Verification "
            "0, W7 ultimate_book, or leftover-ship book_owner. "
            "Place / size / flatten / remint / bounce stay closed."
        ),
        **_structural_marks(),
    }
    if extra:
        row.update(dict(extra))
    return row


def _pin_facts() -> dict[str, Any]:
    """Recorded pin attributes. The pin mark and the weight are the return."""

    try:
        from .gold_priors import GATE_COMPOSITE_WEIGHTS, PIN_WINDOW, assert_gold_pin
    except Exception as exc:
        return {
            "recorded_pin_window": None,
            "recorded_pin_persist": None,
            "pin_source": type(exc).__name__,
            "pin_assert_error": type(exc).__name__,
        }
    weights = GATE_COMPOSITE_WEIGHTS if isinstance(GATE_COMPOSITE_WEIGHTS, Mapping) else {}
    persist = _finite(weights.get("persistence"))
    window = PIN_WINDOW if isinstance(PIN_WINDOW, str) and PIN_WINDOW else None
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
    evaluate_fn: Callable[..., Any] | None = None,
) -> tuple[bool | float | None, None, dict[str, Any]]:
    """One ask. The pin noul and the persistence score are that return."""

    facts = _pin_facts()
    decided = ask_command_center(
        {"rung": "command_center", "order_send": False, **facts},
        evaluate_fn=evaluate_fn,
    )
    pin_ok = decided.get("pin_ok")
    meta = {
        **facts,
        "pin_window": facts.get("recorded_pin_window"),
        "loaded_persist": facts.get("recorded_pin_persist"),
        "pin_ok": pin_ok,
        "persist_weight": decided.get("persist_weight"),
    }
    return pin_ok, None, meta


def _identity_facts(
    *,
    login: Any = None,
    namespace: Any = None,
    tags: Iterable[Any] | None = None,
    sit: MappingLike | None = None,
) -> dict[str, Any]:
    """Login, namespace, and tags. The identity label is the return."""

    body = dict(sit or {})
    challenge = dict(body.get("challenge") or {})
    sit_login = _login_text(
        challenge.get("login")
        or challenge.get("account")
        or body.get("login")
        or body.get("account")
    )
    sit_ns = str(
        challenge.get("ns") or challenge.get("namespace") or body.get("namespace") or ""
    ).strip()
    cli_login = _login_text(login)
    cli_ns = str(namespace or "").strip()
    tag_set = {
        str(item).strip()
        for item in (tags or challenge.get("tags") or body.get("tags") or [])
        if str(item).strip()
    }
    surface_error = None
    if account_surface is not None:
        try:
            account_surface()
        except Exception as exc:  # noqa: BLE001 — the surface result is a fact
            surface_error = type(exc).__name__
    return {
        "sit_login": sit_login,
        "sit_namespace": sit_ns,
        "cli_login": cli_login,
        "cli_namespace": cli_ns,
        "login": sit_login or cli_login,
        "namespace": sit_ns or cli_ns,
        "tags": sorted(tag_set),
        "book_login": _login_text(CHALLENGE_LOGIN),
        "book_namespace": CHALLENGE_NS,
        "book_magic": CHALLENGE_MAGIC,
        "verification_login": _login_text(VERIFICATION_QUARANTINED),
        "w7_namespace": W7_NS,
        "w7_tags": sorted(W7_ARMED_TAGS),
        "friend_namespace": FN_NS,
        "surface_error": surface_error,
    }


def identity_ok(
    *,
    login: Any = None,
    namespace: Any = None,
    tags: Iterable[Any] | None = None,
    sit: MappingLike | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> tuple[bool | float | None, str | None]:
    """One ask. The identity noul and the identity label are that return."""

    facts = _identity_facts(login=login, namespace=namespace, tags=tags, sit=sit)
    decided = ask_command_center(
        {"rung": "command_center", "order_send": False, **facts},
        evaluate_fn=evaluate_fn,
    )
    label = decided.get("identity_label")
    return decided.get("identity_ok"), label if isinstance(label, str) else None


def load_sit(path: Path | None) -> tuple[dict[str, Any] | None, str]:
    """Read a sit JSON. Missing / unreadable is a named miss, never an invented book."""

    if path is None:
        return None, "missing_sit"
    target = Path(path)
    if not target.is_file():
        return None, "missing_sit"
    try:
        body = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "unreadable_sit"
    if not isinstance(body, dict):
        return None, "unreadable_sit"
    return body, "sit_body"


def _tickets_from(book: MappingLike) -> list[int]:
    out: list[int] = []
    for row in book.get("tickets") or []:
        if isinstance(row, Mapping):
            ticket = _as_int_ticket(row.get("ticket") or row.get("id"))
        else:
            ticket = _as_int_ticket(row)
        if ticket is not None:
            out.append(ticket)
    return out


def _friend_tickets(friends: MappingLike) -> list[int]:
    found: list[int] = []
    for key in FRIEND_LOGINS:
        found.extend(_tickets_from(dict(friends.get(key) or {})))
    maps = friends.get("map") or {}
    if isinstance(maps, Mapping):
        for _challenge, mapped in maps.items():
            if isinstance(mapped, Mapping):
                for ticket in mapped.values():
                    parsed = _as_int_ticket(ticket)
                    if parsed is not None:
                        found.append(parsed)
    return found


def _parse_clock(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        clock = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if clock.tzinfo is None:
        clock = clock.replace(tzinfo=timezone.utc)
    return clock.astimezone(timezone.utc)


def _sit_age_hours(sit: MappingLike, *, now: datetime) -> float | None:
    clock = _parse_clock(sit.get("as_of_utc") or sit.get("as_of"))
    if clock is None:
        return None
    return (now - clock).total_seconds() / 3600.0


def compose_page(
    sit: MappingLike,
    *,
    pin_meta: MappingLike | None = None,
    now: datetime | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Build the one-page current truth. Parameters on the page are the return."""

    clock = now or datetime.now(timezone.utc)
    body = dict(sit)
    challenge = dict(body.get("challenge") or {})
    redacted_account = dict(body.get("redacted_account") or body.get("fn") or {})
    friends = dict(body.get("friends") or {})
    w7 = dict(body.get("w7") or {})
    pin = dict(pin_meta) if pin_meta is not None else _pin_facts()
    loaded_pin = pin.get("recorded_pin_window")
    if loaded_pin is None:
        loaded_pin = pin.get("pin_window")
    loaded_persist = pin.get("recorded_pin_persist")
    if loaded_persist is None and "loaded_persist" in pin:
        loaded_persist = pin.get("loaded_persist")
    challenge_tickets = _tickets_from(challenge)
    friend_tickets = _friend_tickets(friends)
    named = set(never_flatten_tickets()) | set(challenge_tickets) | set(friend_tickets)

    age_hours = _sit_age_hours(body, now=clock)
    fn_token = str(
        (redacted_account.get("token_dir") or redacted_account.get("activation_token_dir") or "")
    ).strip()
    tags = [str(t).strip() for t in (challenge.get("tags") or []) if str(t).strip()]
    n_tags = challenge.get("n_tags")
    if n_tags is None and tags:
        n_tags = len(tags)
    jev_env = dict(challenge.get("jev_env") or body.get("jev_env") or {})
    place_apply = str(jev_env.get("GTOS_JEV_PLACE_APPLY") or "").strip()
    apply_live = str(jev_env.get("GTOS_JEV_APPLY_LIVE") or "").strip()
    decided = ask_command_center(
        {
            "rung": "command_center",
            "login": _login_text(challenge.get("login")) or _login_text(CHALLENGE_LOGIN),
            "namespace": str(challenge.get("ns") or CHALLENGE_NS),
            "order_send": False,
            "sit_age_hours": age_hours,
            "sit_clock_present": age_hours is not None,
            "n_tags": n_tags if isinstance(n_tags, int) and not isinstance(n_tags, bool) else None,
            "tags": tags,
            "named_tag_present": "xa_second_rth" in tags,
            "fn_dir_present": bool(fn_token),
            "friend_ticket_count": len(friend_tickets),
            "challenge_ticket_count": len(challenge_tickets),
            "loaded_pin_window": loaded_pin,
            "recorded_pin_persist": loaded_persist,
            "place_apply_present": bool(place_apply),
            "apply_live_present": bool(apply_live),
        },
        evaluate_fn=evaluate_fn,
    )
    persist = decided.get("persist_weight")
    pin_window = decided.get("pin_window")
    micro_lot = decided.get("micro_lot")
    page_verb = decided.get("page_verb")
    haircut = decided.get("haircut")
    findings: list[dict[str, Any]] = []
    if age_hours is None:
        findings.append(
            {
                "level": "FACT",
                "code": "sit_clock_missing",
                "text": "Sit has no as_of_utc. Age is UNCHECKED. Do not invent a later equity.",
            }
        )
    if _returned_mark(decided.get("sit_stale")):
        bits = ["This sit is stale for this state."]
        if age_hours is not None:
            bits.append(f"Sit age {age_hours:.1f} h.")
        if decided.get("stale_hours") is not None:
            bits.append(f"Staleness parameter is {decided.get('stale_hours')}.")
        bits.append("Numbers describe that export, not a live feed. Do not SSH-flood to refresh.")
        findings.append(
            {
                "level": "FACT",
                "code": "sit_stale",
                "text": " ".join(bits),
            }
        )

    if redacted_account and not fn_token:
        findings.append(
            {
                "level": "FACT",
                "code": "fn_token_dir_null",
                "text": (
                    "redacted_account heartbeat token dir is null. This page "
                    "does not remint, bounce, or splice Challenge activation."
                ),
            }
        )

    if _returned_mark(decided.get("tag_menu_note")):
        findings.append(
            {
                "level": "FACT",
                "code": "tag_menu_note",
                "text": (
                    "The tag menu on this state carries the note this page returns. "
                    "This page does not remint."
                ),
            }
        )

    books = [
        {
            "id": "challenge",
            "login": _login_text(challenge.get("login")) or CHALLENGE_LOGIN,
            "ns": str(challenge.get("ns") or CHALLENGE_NS),
            "role": "writer",
            "balance": challenge.get("balance"),
            "equity": challenge.get("equity"),
            "positions": challenge.get("positions"),
            "equity_clock": challenge.get("equity_clock"),
            "writer_pids": challenge.get("writer_pids") or challenge.get("pids"),
            "n_tags": n_tags,
            "persist_weight": persist,
        },
        {
            "id": "redacted_account",
            "login": _login_text(redacted_account.get("login")) or FN_LOGIN,
            "ns": str(redacted_account.get("ns") or FN_NS),
            "role": "writer_other_book",
            "balance": redacted_account.get("balance"),
            "equity": redacted_account.get("equity"),
            "positions": redacted_account.get("positions"),
            "equity_clock": redacted_account.get("equity_clock"),
            "writer_pids": redacted_account.get("writer_pids") or redacted_account.get("pids"),
            "n_tags": redacted_account.get("n_tags"),
            "persist_weight": persist,
        },
    ]
    for key, login in FRIEND_LOGINS.items():
        friend = dict(friends.get(key) or {})
        books.append(
            {
                "id": key,
                "login": _login_text(friend.get("login")) or login,
                "ns": "FTMO-Demo",
                "role": "friend_observer",
                "balance": friend.get("balance"),
                "equity": friend.get("equity"),
                "positions": friend.get("positions"),
                "writer_pids": None,
                "n_tags": None,
                "micro_lot": friend.get("micro_lot"),
            }
        )

    panels = {
        "fleet": {
            "question": "which organism is which — Challenge vs FN vs friends vs quarantine",
            "challenge_login": CHALLENGE_LOGIN,
            "redacted_account_login": FN_LOGIN,
            "friends": {
                key: {"login": login, "role": "FTMO-Demo MICRO_LOT"}
                for key, login in FRIEND_LOGINS.items()
            },
            "verification": VERIFICATION_QUARANTINED,
            "w7": "other_organism",
        },
        "challenge": {
            "question": "is the Challenge writer the one we think it is",
            "login": _login_text(challenge.get("login")) or CHALLENGE_LOGIN,
            "ns": str(challenge.get("ns") or CHALLENGE_NS),
            "magic": str(challenge.get("magic") or CHALLENGE_MAGIC),
            "writer_pids": challenge.get("writer_pids") or challenge.get("pids"),
            "n_tags": n_tags,
            "heartbeat": challenge.get("heartbeat"),
            "token_dir": challenge.get("token_dir") or None,
            "persist_weight": persist,
            "place_apply": place_apply,
            "apply_live": apply_live,
        },
        "exposure": {
            "question": "what is open, and what this page must never flatten",
            "challenge_tickets": challenge.get("tickets") or [],
            "do_not_flatten": sorted(named),
            "pending": challenge.get("pending"),
        },
        "payout": {
            "question": "distance to Step-1, from the sit clock, not a forecast",
            "balance": challenge.get("balance"),
            "equity": challenge.get("equity"),
            "day_net": challenge.get("day_net"),
            "equity_clock": challenge.get("equity_clock"),
            "note": "Do not treat friend demo prints as Challenge equity.",
        },
        "redacted_account": {
            "question": "the other running writer — after Challenge, not instead of it",
            "login": _login_text(redacted_account.get("login")) or FN_LOGIN,
            "ns": str(redacted_account.get("ns") or FN_NS),
            "writer_pids": redacted_account.get("writer_pids") or redacted_account.get("pids"),
            "n_tags": redacted_account.get("n_tags"),
            "positions": redacted_account.get("positions"),
            "token_dir": fn_token or None,
            "place_apply": str(
                dict(redacted_account.get("jev_env") or {}).get("GTOS_JEV_PLACE_APPLY") or ""
            ).strip()
            or None,
        },
        "friends": {
            "question": "did SH / redacted_account / redacted_account fill, without inventing demo passwords",
            "filled": bool(friend_tickets),
            "micro_lot": micro_lot,
            "map": friends.get("map") or {},
            "books": {
                key: {
                    "login": _login_text(dict(friends.get(key) or {}).get("login")) or login,
                    "balance": dict(friends.get(key) or {}).get("balance"),
                    "equity": dict(friends.get(key) or {}).get("equity"),
                    "tickets": dict(friends.get(key) or {}).get("tickets") or [],
                    "observer_pid": dict(friends.get(key) or {}).get("observer_pid"),
                }
                for key, login in FRIEND_LOGINS.items()
            },
        },
        "jev": {
            "question": "what Jev is loaded, without leftover-shipping book_owner",
            "persist_weight": persist,
            "pin_window": pin_window,
            "loaded_pin_window": loaded_pin,
            "loaded_persist": loaded_persist,
            "place_apply": place_apply,
            "apply_live": apply_live,
            "physical_haircut": haircut,
            "leftover_ship_book_owner": False,
            "overlay_77_copied": False,
        },
        "quarantine": {
            "question": "what this page must not splice onto Challenge",
            "verification": VERIFICATION_QUARANTINED,
            "verification_sat": False,
            "w7_namespace": w7.get("ns") or W7_NS,
            "w7_role": "other_organism",
            "spent_gold": "180717112",
        },
        "chair": {
            "question": "Chair verbs vs this OS page",
            "verbs": list(CHAIR_VERBS),
            "this_page": page_verb,
            "writer": "prints",
            "note": (
                "redacted_account ENFORCE / VETO / LABEL. This file is the compounding "
                "command-center surface, read-only. It does not Chair-act."
            ),
        },
    }

    return {
        "schema": SCHEMA,
        "sit_schema": str(body.get("schema") or SIT_SCHEMA),
        "as_of_utc": body.get("as_of_utc"),
        "sit_age_hours": age_hours,
        "books": books,
        "panels": panels,
        "findings": findings,
        "n_tags": n_tags,
        "challenge_tickets": challenge_tickets,
        "friend_tickets": friend_tickets,
        "do_not_flatten_tickets": sorted(named),
        "friends_filled": bool(friend_tickets),
        "place_apply": place_apply,
        "apply_live": apply_live,
        "model": decided.get("model") or MODEL,
        "api_url": API_URL,
        "page_verb": page_verb,
        "page_parameter": decided.get("page_parameter"),
        "persist_weight": persist,
        "pin_window": pin_window,
        "stale_hours": decided.get("stale_hours"),
        "sit_stale": decided.get("sit_stale"),
        "micro_lot": micro_lot,
        "haircut": haircut,
        "decision_error": decided.get("error"),
    }


def _tick(value: Any) -> str:
    return "`" + str(value) + "`"


def render_markdown(page: MappingLike) -> str:
    """Plain-text page. No broker. No secrets."""

    panels = dict(page.get("panels") or {})
    challenge = dict(panels.get("challenge") or {})
    payout = dict(panels.get("payout") or {})
    exposure = dict(panels.get("exposure") or {})
    fn = dict(panels.get("redacted_account") or {})
    friends = dict(panels.get("friends") or {})
    jev = dict(panels.get("jev") or {})
    lines = [
        "# redacted_account command center",
        "",
        "schema " + _tick(page.get("schema")) + " as_of " + _tick(page.get("as_of_utc")),
        "Challenge **"
        + str(page.get("account"))
        + "** / "
        + _tick(page.get("ns"))
        + " persist **"
        + str(page.get("persist_weight"))
        + "**",
        "extra_pass **"
        + str(page.get("extra_pass"))
        + "** apply **"
        + str(page.get("apply"))
        + "** never_flatten **"
        + str(page.get("never_flatten"))
        + "** never_bounce **"
        + str(page.get("never_bounce"))
        + "**",
        "",
        "## 1 · fleet",
        "- Challenge "
        + _tick(challenge.get("login"))
        + " writer "
        + _tick(challenge.get("writer_pids"))
        + " tags "
        + _tick(challenge.get("n_tags")),
        "- redacted_account "
        + _tick(fn.get("login"))
        + " writer "
        + _tick(fn.get("writer_pids"))
        + " tags "
        + _tick(fn.get("n_tags")),
        "- Friends filled "
        + _tick(friends.get("filled"))
        + " MICRO_LOT "
        + _tick(friends.get("micro_lot")),
        "- Verification " + _tick(VERIFICATION_QUARANTINED) + " quarantined. W7 other organism.",
        "",
        "## 1b · friends (not Challenge equity)",
    ]
    friend_books = dict(friends.get("books") or {})
    for key in ("sh", "redacted_account", "redacted_account"):
        book = dict(friend_books.get(key) or {})
        raw_tickets = book.get("tickets") or []
        ticket_ids = [
            row.get("ticket") if isinstance(row, dict) else row for row in raw_tickets
        ]
        lines.append(
            "- "
            + key
            + " "
            + _tick(book.get("login"))
            + " bal "
            + _tick(book.get("balance"))
            + " eq "
            + _tick(book.get("equity"))
            + " tickets "
            + _tick(ticket_ids)
        )
    lines.append(
        "Do not treat friend demo equity as Challenge. "
        "redacted_account 100k print is demo, not 0."
    )
    lines.extend(
        [
            "",
            "## 2 · Challenge writer",
            "- ns "
            + _tick(challenge.get("ns"))
            + " magic "
            + _tick(challenge.get("magic"))
            + " token "
            + _tick(challenge.get("token_dir")),
            "- PLACE_APPLY "
            + _tick(challenge.get("place_apply"))
            + " APPLY_LIVE "
            + _tick(challenge.get("apply_live")),
            "- heartbeat " + _tick(challenge.get("heartbeat")),
            "",
            "## 3 · exposure (do not flatten)",
            "- pending " + _tick(exposure.get("pending")),
            "- tickets " + _tick(exposure.get("do_not_flatten")),
            "",
            "## 4 · Step-1 path",
            "- bal "
            + _tick(payout.get("balance"))
            + " eq "
            + _tick(payout.get("equity"))
            + " clock "
            + _tick(payout.get("equity_clock")),
            "- day_net "
            + _tick(payout.get("day_net")),
            "- " + str(payout.get("note") or ""),
            "",
            "## 5 · Jev pin",
            "- persist "
            + _tick(jev.get("persist_weight"))
            + " window "
            + _tick(jev.get("pin_window"))
            + " leftover-ship "
            + _tick(jev.get("leftover_ship_book_owner")),
            "",
            "## findings",
        ]
    )
    for finding in page.get("findings") or []:
        lines.append(
            "- "
            + str(finding.get("level"))
            + " "
            + _tick(finding.get("code"))
            + " "
            + str(finding.get("text") or "")
        )
    if not page.get("findings"):
        lines.append("- none")
    lines.extend(["", str(page.get("decision") or "")])
    return "\n".join(lines) + "\n"


def render_html(page: MappingLike) -> str:
    """Standalone HTML. No scripts, no external requests, no MT5."""

    md = render_markdown(page)
    escaped = html.escape(md)
    title = html.escape(
        f"redacted_account command center {page.get('account')} persist {page.get('persist_weight')}"
    )
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<title>{title}</title>"
        "<style>"
        "body{font-family:ui-monospace,Menlo,Consolas,monospace;margin:24px;max-width:960px;"
        "background:#0f1115;color:#e8eaed}"
        "pre{white-space:pre-wrap;line-height:1.35}"
        "@media (prefers-color-scheme:light){body{background:#f6f7f8;color:#111}}"
        "</style></head><body><pre>"
        f"{escaped}"
        "</pre></body></html>\n"
    )


def run_command_center(
    *,
    sit_path: Path | None,
    login: Any = None,
    namespace: Any = None,
    as_of: str | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """The verb and the parameters are the return for this state."""

    path = Path(sit_path) if sit_path is not None else default_sit_path()
    sit, sit_kind = load_sit(path)
    sit_body = sit if isinstance(sit, dict) else {}
    ident = _identity_facts(login=login, namespace=namespace, sit=sit_body)
    pin = _pin_facts()
    root = namespace_root(REPO_ROOT, str(CHALLENGE_NS))
    heartbeat = read_json(root / "heartbeat.json") or {}
    chair = read_json(root / "judgment" / "state" / "chair_health.json") or {}
    pair = open_pair(root)
    now = datetime.now(timezone.utc)
    age_hours = _sit_age_hours(sit_body, now=now) if sit_body else None
    state = {
        "rung": "command_center",
        "login": _login_text(login) or _login_text(CHALLENGE_LOGIN),
        "namespace": namespace or CHALLENGE_NS,
        "order_send": False,
        "sit_present": sit is not None,
        "sit_kind": sit_kind,
        "sit_age_hours": age_hours,
        "sit_clock_present": age_hours is not None,
        "observer_env_on": command_center_enabled(environ=environ),
        "loaded_pin_window": pin.get("recorded_pin_window"),
        "recorded_pin_persist": pin.get("recorded_pin_persist"),
        **ident,
        **pin,
        "heartbeat_ok": heartbeat.get("ok") if isinstance(heartbeat, dict) else None,
        "positions": heartbeat.get("positions") if isinstance(heartbeat, dict) else None,
        "day_net": chair.get("day_net") if isinstance(chair, dict) else None,
        "equity": chair.get("equity") if isinstance(chair, dict) else heartbeat.get("equity"),
        "balance": chair.get("balance") if isinstance(chair, dict) else heartbeat.get("balance"),
        "open_pair": pair,
        "as_of": as_of,
    }
    decided = ask_command_center(state, evaluate_fn=evaluate_fn)
    choice = decided.get("choice") if decided.get("choice") in CHAIR_VERBS else None
    emitted = choice is not None
    if emitted:
        append_record(
            root / "judgment" / "rung_choice" / "command_center.jsonl",
            {
                "rung": "command_center",
                "login": CHALLENGE_LOGIN,
                "namespace": CHALLENGE_NS,
                "order_send": False,
                "decision_emitted": True,
                "choice": choice,
                "page_verb": choice,
                "probability": decided.get("probability"),
                "page_parameter": decided.get("page_parameter"),
                "persist_weight": decided.get("persist_weight"),
                "pin_window": decided.get("pin_window"),
                "stale_hours": decided.get("stale_hours"),
                "sit_stale": decided.get("sit_stale"),
                "micro_lot": decided.get("micro_lot"),
                "haircut": decided.get("haircut"),
                "pin_ok": decided.get("pin_ok"),
                "identity_ok": decided.get("identity_ok"),
                "identity_label": decided.get("identity_label"),
                "tag_menu_note": decided.get("tag_menu_note"),
                "model": decided.get("model") or MODEL,
            },
        )
    return {
        "schema": SCHEMA,
        "model": decided.get("model") or MODEL,
        "api_url": API_URL,
        "account": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "pass_target": None,
        "enabled": True,
        "skipped": None,
        "asked": True,
        "question_id": "page_verb",
        "choice": choice,
        "page_parameter": decided.get("page_parameter"),
        "probability": decided.get("probability") if emitted else None,
        "probabilities": decided.get("probabilities") or {},
        "probability_source": "probabilities" if emitted else None,
        "decision_emitted": emitted,
        "fail_closed": False,
        "fail_closed_reason": None,
        "page_emitted": emitted,
        "persist_weight": decided.get("persist_weight"),
        "pin_window": decided.get("pin_window"),
        "stale_hours": decided.get("stale_hours"),
        "sit_stale": decided.get("sit_stale"),
        "micro_lot": decided.get("micro_lot"),
        "haircut": decided.get("haircut"),
        "pin_ok": decided.get("pin_ok"),
        "identity_ok": decided.get("identity_ok"),
        "identity_label": decided.get("identity_label"),
        "tag_menu_note": decided.get("tag_menu_note"),
        "sit_kind": sit_kind,
        "identity": decided.get("identity_label"),
        "page_verb": choice,
        "symbol": pair.get("symbol"),
        "sleeve": pair.get("sleeve"),
        "ticket": pair.get("ticket"),
        "hop_error": None if emitted else decided.get("error"),
        "http_status": decided.get("http_status"),
        "decision": (
            None
            if not emitted
            else (
                "Page verb is the highest-probability return for this state. "
                "It does not place, flatten, bounce, or send."
            )
        ),
        **_structural_marks(),
    }


def maybe_run_command_center(
    *,
    sit_path: Path | None = None,
    login: Any = None,
    namespace: Any = None,
    environ: Mapping[str, str] | None = None,
    as_of: str | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Observer. The env flag is a fact. The ask still runs. This page does not send."""

    path = Path(sit_path) if sit_path is not None else default_sit_path()
    return run_command_center(
        sit_path=path,
        login=login,
        namespace=namespace,
        as_of=as_of,
        evaluate_fn=evaluate_fn,
        environ=environ,
    )
