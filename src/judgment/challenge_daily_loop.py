"""CHALLENGE_DAILY_LOOP_V0 — daily label on Challenge 0.

Unique file. Recommendation-only. The env flag is a fact on the card.

Every decision in this file, including every parameter, is the System One
return for that state. One hop is ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False`` (POST
https://api.typesafe.ai/v1/systemone). Questions are only Noul, Choice,
or Score. Prior outcomes are attached on that ask, and the return is
stored for the next ask.

The chair label is the unique highest probability. The label parameter
and the persistence parameter are the returned scores and may sit between
levels. An empty answer, a tie, a missing score, or an error leaves that
field unset and does not restore a constant. The loaded pin is a fact
on the card. An empty persistence score stays absent. A floor and a
baseline are not a question.

This module does not place, size, remint, or send. Judge code stays
unable to send.

Host hook (observer, env-gate BEFORE import, never refuse a fire):

    if os.environ.get("GTOS_JEV_DAILY_LOOP", "").strip().lower() in {"1", "true", "yes"}:
        from src.judgment.challenge_daily_loop import maybe_run_daily_loop
        maybe_run_daily_loop(slate_path=latest_slate, login=0)

The env flag is a fact on the card. The ask still runs. W7 is a fact
on that card. This module does not send.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

try:
    from .challenge import (
        CHALLENGE_LOGIN,
        CHALLENGE_MAGIC,
        CHALLENGE_NS,
        VERIFICATION_QUARANTINED,
        account_surface,
        assert_challenge_payout_writer,
    )
except Exception:
    CHALLENGE_LOGIN = 0
    CHALLENGE_MAGIC = 0
    CHALLENGE_NS = "operator"
    VERIFICATION_QUARANTINED = None
    account_surface = None
    assert_challenge_payout_writer = None

MappingLike = Mapping[str, Any]

SCHEMA = "gtos.judgment.challenge_daily_loop.v0"
LABEL_STORE_SCHEMA = "gtos.judgment.challenge_label_store.v0"
DAILY_LOOP_ENV = "GTOS_JEV_DAILY_LOOP"
DAILY_LOOP_PATH_ENV = "GTOS_JEV_DAILY_LOOP_PATH"
MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_DIR = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_daily_loop" / "fixtures"
)
DEFAULT_STORE = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_daily_loop" / "store.jsonl"
)

W7_ARMED_TAGS = frozenset({"crypto", "energy_agri", "sub_xvol_pullback"})

# Named tickets. A fact on the receipt. This module does not touch them.
CHAIR_NAMED_OPEN_TICKETS = frozenset({294092360, 294088097})
CHAIR_NAMED_CLOSED_NO_TOUCH = frozenset({294069721})
LEAVE_ORIG_TICKETS = frozenset({293332188}) | CHAIR_NAMED_OPEN_TICKETS | CHAIR_NAMED_CLOSED_NO_TOUCH

_TRUTHY = frozenset({"1", "true", "yes", "on"})
ACTIONS = ("KEEP", "STUDY", "STARVE", "HARD_OFF", "WATCH")
_IDENTITY_ORDER = (
    "challenge",
    "verification_quarantined",
    "study_not_challenge",
    "w7_other_organism",
    "namespace_not_challenge",
    "login_not_challenge",
    "identity_missing",
)
_IDENTITY_CRITERIA = {
    "challenge": "The login and namespace on this state are the challenge book.",
    "verification_quarantined": "The login on this state is the quarantined verification book.",
    "study_not_challenge": "The study login on this state is outside the challenge book.",
    "w7_other_organism": "The namespace or tags on this state are the other organism.",
    "namespace_not_challenge": "The namespace on this state is outside the challenge book.",
    "login_not_challenge": "The login on this state is outside the challenge book.",
    "identity_missing": "Login and namespace are both absent on this state.",
}
_LABEL_CRITERIA = {
    "KEEP": "This Challenge state earns a house-keep label.",
    "STUDY": "This Challenge state earns a study label.",
    "STARVE": "This Challenge state earns a starve label.",
    "HARD_OFF": "This Challenge state earns a hard-off label.",
    "WATCH": "This Challenge state earns a watch label.",
}
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
    "chair_label",
    "chair_label_parameter",
    "persist_weight",
    "pin_ok",
    "identity_ok",
    "identity_label",
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
    return any(token.replace(",", "").replace("_", "").replace(" ", "").lower() in compact for token in _BANNED_TEXT)


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
    if named:
        block["criteria"] = named
    else:
        block.pop("criteria", None)
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


def daily_loop_questions(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One card for this state. Choice or Score only. Floor and baseline are not on it."""

    facts = _scrub(dict(state or {}))
    if not isinstance(facts, dict):
        facts = {}
    scale = _levels(facts)
    pack: dict[str, Any] = {}
    pack.update(_choice_body(
        "chair_label",
        (
            "What label does this Challenge state earn? "
            "Sleeve, symbol, and slate facts on this state are facts. "
            "The unique highest probability is the label. "
            "An empty answer or a tie leaves the label unset. "
            "Do not place, size, or send."
        ),
        _LABEL_CRITERIA,
    ))
    pack.update(_score_body(
        "chair_label_parameter",
        (
            "The score you return is the parameter of that label on this state. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "Do not place, size, or send."
        ),
        scale,
    ))
    pack.update(_score_body(
        "persist_weight",
        (
            "The score you return is the persistence parameter for this state. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "Do not place, size, or send."
        ),
        scale,
    ))
    pack.update(_noul_body(
        "pin_ok",
        (
            "Are the recorded pin attributes on this state the pin for this label? "
            "An empty noul leaves the pin unset. "
            "Do not place, size, or send."
        ),
        "The recorded pin is the pin for this label.",
        "The recorded pin is not the pin for this label.",
    ))
    pack.update(_noul_body(
        "identity_ok",
        (
            "Are the login and namespace on this state the challenge book? "
            "An empty noul leaves identity unset. "
            "Do not place, size, or send."
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
            "Do not place, size, or send."
        ),
        _IDENTITY_CRITERIA,
    ))
    clean: dict[str, Any] = {}
    for qid, block in pack.items():
        if not isinstance(block, dict):
            continue
        kind = str(block.get("type") or "")
        if kind not in {"noul", "choice", "score"}:
            continue
        if _limit_key(qid):
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
    return local, kept, False


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
        if key in block:
            parsed = _finite(block.get(key))
            if parsed is not None:
                return parsed
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
        "probability": None,
        "probabilities": {},
        "parameter": None,
        "persist_weight": None,
        "pin_ok": None,
        "identity_ok": None,
        "identity_label": None,
        "decision_emitted": False,
        "error": error,
        "http_status": None,
        "answers": {},
    }


def _read_return(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    row = _blank_return()
    body = answers if isinstance(answers, Mapping) else {}
    choice, probs, tied = _choice_of(body.get("chair_label"), ACTIONS)
    identity, _id_probs, _id_tied = _choice_of(body.get("identity_label"), _IDENTITY_ORDER)
    parameter = _score_of(body.get("chair_label_parameter"))
    persist = _score_of(body.get("persist_weight"))
    row["choice"] = choice if choice in ACTIONS else None
    row["probabilities"] = probs
    row["probability"] = probs.get(row["choice"]) if row["choice"] is not None else None
    row["parameter"] = parameter
    row["persist_weight"] = persist
    row["pin_ok"] = _noul_of(body.get("pin_ok"))
    row["identity_ok"] = _noul_of(body.get("identity_ok"))
    row["identity_label"] = identity if identity in _IDENTITY_ORDER else None
    row["decision_emitted"] = row["choice"] is not None
    row["answers"] = dict(body)
    if row["choice"] is None:
        row["error"] = "tie" if tied else "empty"
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
    pairs = (
        ("chair_label", row.get("choice"), None if row.get("choice") is not None else (error or "tie_or_empty")),
        ("chair_label_parameter", row.get("parameter"), None if row.get("parameter") is not None else (error or "score_missing")),
        ("persist_weight", row.get("persist_weight"), None if row.get("persist_weight") is not None else (error or "score_missing")),
        ("pin_ok", row.get("pin_ok"), None if row.get("pin_ok") is not None else (error or "unset")),
        ("identity_ok", row.get("identity_ok"), None if row.get("identity_ok") is not None else (error or "unset")),
        ("identity_label", row.get("identity_label"), None if row.get("identity_label") is not None else (error or "unset")),
    )
    logged = _scrub(dict(state))
    if not isinstance(logged, dict):
        logged = {}
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, miss in pairs:
            _LOCAL_OUTCOMES.append({"key": key, "value": value, "error": miss})
        return
    for key, value, miss in pairs:
        try:
            append_outcome(key, value, logged, error=miss)
        except Exception:
            return


def ask_daily(
    state: Mapping[str, Any] | None = None,
    *,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One System One post. Empty, tie, and error leave the fields unset."""

    questions = daily_loop_questions(state)
    payload = dict(state or {})
    for key, value in _pin_facts().items():
        payload.setdefault(key, value)
    payload = _scrub(payload)
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    for key in _QUESTION_IDS:
        payload.pop(key, None)
    payload["model"] = MODEL
    payload["order_send"] = False
    if not questions:
        row = _blank_return("empty")
        _remember(payload, row)
        return row
    _attach_priors(payload, questions)
    call = ask
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
    row["ok"] = row["choice"] is not None and receipt.get("ok") is not False
    if row["choice"] is None and receipt.get("error"):
        row["error"] = str(receipt.get("error"))
    _remember(payload, row)
    return row


def _env_on(name: str, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get(name, "")).strip().lower() in _TRUTHY


def daily_loop_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Default-OFF. Unset / empty / 0 is off."""

    return _env_on(DAILY_LOOP_ENV, environ)


def default_store_path() -> Path:
    override = (os.environ.get(DAILY_LOOP_PATH_ENV) or "").strip()
    return Path(override) if override else DEFAULT_STORE


def _login_text(value: Any) -> str:
    if value is None or value == "":
        return ""
    return str(value).strip()


def _structural_marks() -> dict[str, Any]:
    """This module cannot place, size, remint, or send. Those marks are not asks."""

    return {
        "extra_pass": False,
        "apply": False,
        "silent_apply": False,
        "never_place": True,
        "never_flatten": True,
        "never_remint": True,
        "order_send": False,
        "overlay_77_copied": False,
        "do_not_flatten_tickets": sorted(LEAVE_ORIG_TICKETS),
    }


def _fail(
    reason: str,
    *,
    enabled: bool,
    extra: MappingLike | None = None,
    fail_closed: bool | None = None,
) -> dict[str, Any]:
    closed = enabled if fail_closed is None else fail_closed
    skipped = None if enabled else "GTOS_JEV_DAILY_LOOP_off"
    row: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "account": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "enabled": enabled,
        "skipped": skipped,
        "asked": False,
        "fail_closed": closed,
        "fail_closed_reason": reason if closed else skipped,
        "choice": None,
        "parameter": None,
        "probability": None,
        "persist_weight": None,
        "recommendation_emitted": False,
        "decision_emitted": False,
        "pin_window": None,
        "recommendations": [],
        "label_store": None,
        "decision": (
            "No extra PASS. Chair does not splice frozen Verification "
            "f5_study. Place, size, and send stay closed."
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
    ask: Callable[..., Any] | None = None,
) -> tuple[bool | float | None, None, dict[str, Any]]:
    """One ask. The pin noul and the persistence score are that return."""

    facts = _pin_facts()
    decided = ask_daily({"rung": "daily_loop", "order_send": False, **facts}, ask=ask)
    pin_ok = decided.get("pin_ok")
    meta = {
        **facts,
        "pin_window": facts.get("recorded_pin_window"),
        "pin_persist": facts.get("recorded_pin_persist"),
        "pin_ok": pin_ok,
        "persist_weight": decided.get("persist_weight"),
    }
    return pin_ok, None, meta


def _identity_facts(
    *,
    login: Any = None,
    namespace: Any = None,
    tags: Iterable[Any] | None = None,
    heartbeat: MappingLike | None = None,
    study: MappingLike | None = None,
) -> dict[str, Any]:
    """Login, namespace, and tags. The identity label is the return."""

    hb = dict(heartbeat or {})
    study_doc = dict(study or {})
    ns = str(namespace or hb.get("namespace") or "").strip()
    raw_login = _login_text(login)
    if not raw_login:
        raw_login = _login_text(
            study_doc.get("login")
            or study_doc.get("account")
            or hb.get("login")
            or hb.get("account")
        )
    tag_set = {str(item).strip() for item in (tags or hb.get("tags") or []) if str(item).strip()}
    study_login = _login_text(study_doc.get("login") or study_doc.get("account"))
    writer_error = None
    surface_error = None
    if raw_login and assert_challenge_payout_writer is not None:
        try:
            assert_challenge_payout_writer(raw_login)
        except Exception as exc:  # noqa: BLE001 — the writer check is a fact
            writer_error = type(exc).__name__
    if account_surface is not None:
        try:
            account_surface()
        except Exception as exc:  # noqa: BLE001 — the surface result is a fact
            surface_error = type(exc).__name__
    return {
        "login": raw_login,
        "namespace": ns,
        "tags": sorted(tag_set),
        "study_login": study_login,
        "book_login": _login_text(CHALLENGE_LOGIN),
        "book_namespace": CHALLENGE_NS,
        "book_magic": CHALLENGE_MAGIC,
        "verification_login": _login_text(VERIFICATION_QUARANTINED),
        "w7_tags": sorted(W7_ARMED_TAGS),
        "writer_error": writer_error,
        "surface_error": surface_error,
    }


def identity_ok(
    *,
    login: Any = None,
    namespace: Any = None,
    tags: Iterable[Any] | None = None,
    heartbeat: MappingLike | None = None,
    study: MappingLike | None = None,
    ask: Callable[..., Any] | None = None,
) -> tuple[bool | float | None, str | None]:
    """One ask. The identity noul and the identity label are that return."""

    facts = _identity_facts(
        login=login,
        namespace=namespace,
        tags=tags,
        heartbeat=heartbeat,
        study=study,
    )
    decided = ask_daily({"rung": "daily_loop", "order_send": False, **facts}, ask=ask)
    label = decided.get("identity_label")
    return decided.get("identity_ok"), label if isinstance(label, str) else None


def load_json(path: Path | str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    target = Path(path)
    if not target.is_file():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def resolve_slate(path: Path | str | None) -> tuple[dict[str, Any] | None, str]:
    """Follow ``latest_slate.json`` pointers. Missing file is a fact."""

    if path is None:
        return None, "missing_slate"
    pointer_path = Path(path)
    payload = load_json(pointer_path)
    if payload is None:
        return None, "missing_slate"
    if payload.get("schema") == "gtos.judgment.slate.v2" or "candidates" in payload:
        return payload, "slate_body"
    dest = str(payload.get("path") or "").strip()
    if not dest:
        return None, "missing_slate"
    dest_path = Path(dest)
    if not dest_path.is_file():
        dest_path = pointer_path.parent / Path(dest).name
    body = load_json(dest_path)
    if body is None:
        return None, "missing_slate"
    if "candidates" not in body and body.get("schema") != "gtos.judgment.slate.v2":
        return None, "missing_slate"
    return body, "slate_pointer"


def _family_fact(raw: Mapping[str, Any]) -> Any:
    """Family text already on the row. Absence stays absent."""

    for key in ("family_class", "family"):
        if raw.get(key) not in (None, ""):
            return raw.get(key)
    return None


def quiet_action(sleeve: str, *, symbol: str = "") -> str | None:
    """The label for this sleeve. A miss stays unset."""

    sl = (sleeve or "").strip().lower()
    decided = ask_daily(
        {
            "rung": "quiet_action",
            "login": CHALLENGE_LOGIN,
            "namespace": CHALLENGE_NS,
            "sleeve": sl,
            "symbol": symbol or "",
        }
    )
    choice = decided.get("choice")
    if choice in ACTIONS:
        return str(choice)
    return None


def _candidate_rows(slate: MappingLike) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    asked: dict[str, dict[str, Any]] = {}
    for raw in slate.get("candidates") or []:
        if not isinstance(raw, dict):
            continue
        sleeve = str(raw.get("sleeve") or "")
        symbol = str(raw.get("symbol") or "")
        key = sleeve.strip().lower() or "unknown"
        decided = asked.get(key)
        if decided is None:
            decided = ask_daily(
                {
                    "rung": "quiet_action",
                    "login": CHALLENGE_LOGIN,
                    "namespace": CHALLENGE_NS,
                    "sleeve": key if key != "unknown" else "",
                    "symbol": symbol,
                    "candidate_id": raw.get("candidate_id"),
                    "status": raw.get("status"),
                    "family_class": _family_fact(raw),
                }
            )
            asked[key] = decided
        action = decided.get("choice") if decided.get("choice") in ACTIONS else None
        rows.append(
            {
                "sleeve": sleeve,
                "symbol": symbol,
                "candidate_id": raw.get("candidate_id"),
                "family_class": _family_fact(raw),
                "action": action,
                "parameter": decided.get("parameter"),
                "persist_weight": decided.get("persist_weight"),
                "probability": decided.get("probability"),
                "size_up": False,
                "apply": False,
                "flatten": False,
                "status": raw.get("status"),
            }
        )
    return rows


def _open_tickets(slate: MappingLike) -> list[int]:
    tickets: list[int] = []
    for raw in slate.get("open_positions") or []:
        if not isinstance(raw, dict):
            continue
        try:
            tickets.append(int(raw.get("ticket")))
        except (TypeError, ValueError):
            continue
    return tickets


def recommend(slate: MappingLike) -> list[dict[str, Any]]:
    """One row per distinct sleeve. The action is that sleeve's return."""

    by_sleeve: dict[str, dict[str, Any]] = {}
    for row in _candidate_rows(slate):
        sleeve = row["sleeve"] or "unknown"
        existing = by_sleeve.get(sleeve)
        if existing is None:
            by_sleeve[sleeve] = {
                "sleeve": sleeve,
                "symbol": row["symbol"],
                "family_class": row["family_class"],
                "action": row["action"],
                "parameter": row["parameter"],
                "persist_weight": row["persist_weight"],
                "probability": row["probability"],
                "n_candidates": 1,
                "size_up": False,
                "apply": False,
                "silent_apply": False,
                "flatten": False,
                "chair": "LABEL",
            }
        else:
            existing["n_candidates"] += 1
    recs = list(by_sleeve.values())
    recs.sort(key=lambda r: (r["action"] is None, str(r["action"] or ""), r["sleeve"]))
    return recs


class LabelStore:
    """Append-only JSONL of daily slate fingerprints. Duplicate day+id is a no-op."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows

    def append(self, row: MappingLike) -> dict[str, Any]:
        day = str(row.get("utc_day") or "")
        slate_id = str(row.get("slate_id") or "")
        for existing in self.load():
            if existing.get("utc_day") == day and existing.get("slate_id") == slate_id:
                return {**dict(row), "appended": False, "duplicate": True}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")
        return {**dict(row), "appended": True, "duplicate": False}


def label_row(
    slate: MappingLike,
    *,
    close_rows: Iterable[MappingLike] | None = None,
    as_of: str | None = None,
    persist_weight: float | None = None,
    parameter: float | None = None,
    action: str | None = None,
) -> dict[str, Any]:
    clock = slate.get("clock") or {}
    utc_day = str(clock.get("utc_day") or "")
    if not utc_day:
        built = str(slate.get("built_at_utc") or as_of or "")
        utc_day = built[:10]
    candidates = [c for c in (slate.get("candidates") or []) if isinstance(c, dict)]
    closes = [dict(c) for c in (close_rows or [])]
    return {
        "schema": LABEL_STORE_SCHEMA,
        "account": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "utc_day": utc_day,
        "slate_id": slate.get("slate_id"),
        "fingerprint": slate.get("fingerprint"),
        "built_at_utc": slate.get("built_at_utc"),
        "n_candidates": len(candidates),
        "candidate_ids": [c.get("candidate_id") for c in candidates],
        "sleeves": sorted({str(c.get("sleeve") or "") for c in candidates}),
        "n_open": len(slate.get("open_positions") or []),
        "open_tickets": _open_tickets(slate),
        "n_refusals": len(slate.get("refusals") or []),
        "n_close_labels": len(closes),
        "close_tickets": [c.get("ticket") for c in closes],
        "action": action,
        "parameter": parameter,
        "persist_weight": persist_weight,
        "apply": False,
        "as_of_utc": as_of or datetime.now(timezone.utc).isoformat(),
    }


def _safe_surface() -> Any:
    if account_surface is None:
        return None
    try:
        return account_surface()
    except Exception as exc:  # noqa: BLE001 — surface is a fact, not the decision
        return type(exc).__name__


def _namespace_root() -> Path:
    return REPO_ROOT / "pipeline_state" / "ultimate_book" / str(CHALLENGE_NS)


def _open_pair(root: Path) -> dict[str, Any]:
    try:
        from .rung_choice import open_pair
    except Exception:
        return {}
    try:
        pair = open_pair(root)
    except Exception:
        return {}
    return pair if isinstance(pair, dict) else {}


def _append_record(path: Path, record: Mapping[str, Any]) -> None:
    try:
        from .rung_choice import append_record
    except Exception:
        return
    try:
        append_record(path, record)
    except Exception:
        return


def _slate_facts(slate_path: Path | str | None) -> tuple[dict[str, Any] | None, str, Path | str | None]:
    """Load a slate when one is on disk. Absence is a fact, not a decision."""

    path = slate_path
    kind = "given"
    if path is None:
        pointer = _namespace_root() / "judgment" / "state" / "latest_slate.json"
        if pointer.is_file():
            path = pointer
            kind = "latest_pointer"
        else:
            return None, "no_pointer", None
    slate, slate_kind = resolve_slate(path)
    return slate, slate_kind or kind, path


def run_daily_loop(
    *,
    slate_path: Path | str | None,
    login: Any = None,
    namespace: Any = None,
    heartbeat_path: Path | str | None = None,
    study_path: Path | str | None = None,
    close_rows: Iterable[MappingLike] | None = None,
    store: LabelStore | None = None,
    as_of: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """The label and the parameters are the return for this state."""
    heartbeat = load_json(heartbeat_path) if heartbeat_path is not None else None
    study = load_json(study_path) if study_path is not None else None
    ns = namespace
    if ns is None and heartbeat:
        ns = heartbeat.get("namespace")
    ident = _identity_facts(
        login=login,
        namespace=ns,
        heartbeat=heartbeat,
        study=study,
    )
    pin = _pin_facts()
    slate, slate_kind, used_path = _slate_facts(slate_path)
    closes = [row for row in (close_rows or []) if isinstance(row, Mapping)]
    candidates = []
    if isinstance(slate, dict):
        candidates = [
            {
                "symbol": row.get("symbol"),
                "sleeve": row.get("sleeve"),
                "candidate_id": row.get("candidate_id"),
            }
            for row in (slate.get("candidates") or [])
            if isinstance(row, dict)
        ]
    root = _namespace_root()
    pair = _open_pair(root)
    state = {
        "rung": "daily_loop",
        "login": _login_text(login) or _login_text(CHALLENGE_LOGIN),
        "namespace": ns or CHALLENGE_NS,
        "order_send": False,
        "observer_env_on": daily_loop_enabled(environ=environ),
        "slate_present": slate is not None,
        **ident,
        **pin,
        "slate_kind": slate_kind,
        "slate_id": None if slate is None else slate.get("slate_id"),
        "fingerprint": None if slate is None else slate.get("fingerprint"),
        "n_candidates": len(candidates),
        "candidates": candidates,
        "n_open": 0 if slate is None else len(slate.get("open_positions") or []),
        "open_pair": pair,
        "n_close_labels": len(closes),
    }
    decided = ask_daily(state)
    choice = decided.get("choice") if decided.get("choice") in ACTIONS else None
    emitted = choice is not None
    parameter = decided.get("parameter")
    persist = decided.get("persist_weight")
    recs: list[dict[str, Any]] = []
    stored = None
    held = store
    if emitted:
        recs = [
            {
                "sleeve": pair.get("sleeve"),
                "symbol": pair.get("symbol"),
                "action": choice,
                "parameter": parameter,
                "persist_weight": persist,
                "probability": decided.get("probability"),
                "n_candidates": len(candidates),
                "size_up": False,
                "apply": False,
                "silent_apply": False,
                "flatten": False,
                "order_send": False,
                "chair": "LABEL",
            }
        ]
        if isinstance(slate, dict):
            held = held or LabelStore(default_store_path())
            stored = held.append(
                label_row(
                    slate,
                    close_rows=closes,
                    as_of=as_of,
                    persist_weight=persist if isinstance(persist, (int, float)) else None,
                    parameter=parameter if isinstance(parameter, (int, float)) else None,
                    action=choice,
                )
            )
        _append_record(
            root / "judgment" / "rung_choice" / "daily_loop.jsonl",
            {
                "rung": "daily_loop",
                "login": CHALLENGE_LOGIN,
                "namespace": CHALLENGE_NS,
                "slate_id": state["slate_id"],
                "choice": choice,
                "probability": decided.get("probability"),
                "parameter": parameter,
                "persist_weight": persist,
                "pin_ok": decided.get("pin_ok"),
                "identity_ok": decided.get("identity_ok"),
                "identity_label": decided.get("identity_label"),
                "order_send": False,
                "decision_emitted": True,
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
        "surface": _safe_surface(),
        "enabled": True,
        "skipped": None,
        "asked": True,
        "question_id": "chair_label",
        "choice": choice,
        "parameter": parameter,
        "probability": decided.get("probability") if emitted else None,
        "probabilities": decided.get("probabilities") or {},
        "decision_emitted": emitted,
        "fail_closed": False,
        "fail_closed_reason": None,
        "identity": decided.get("identity_label"),
        "identity_ok": decided.get("identity_ok"),
        "identity_label": decided.get("identity_label"),
        "pin_ok": decided.get("pin_ok"),
        "slate_kind": slate_kind,
        "slate_id": state["slate_id"],
        "symbol": pair.get("symbol"),
        "sleeve": pair.get("sleeve"),
        "ticket": pair.get("ticket"),
        "slate_path": None if used_path is None else str(used_path),
        "recommendation_emitted": emitted,
        "persist_weight": persist,
        "pin_window": pin.get("recorded_pin_window"),
        "recommendations": recs,
        "n_recommendations": len(recs),
        "by_action": {
            action: sum(1 for row in recs if row["action"] == action) for action in ACTIONS
        },
        "label_store": None
        if stored is None
        else {
            "path": str((held or LabelStore(default_store_path())).path),
            "utc_day": stored.get("utc_day"),
            "slate_id": stored.get("slate_id"),
            "n_candidates": stored.get("n_candidates"),
            "appended": stored.get("appended"),
            "duplicate": stored.get("duplicate"),
        },
        "hop_error": None if emitted else decided.get("error"),
        "http_status": decided.get("http_status"),
        "decision": (
            None
            if not emitted
            else (
                "Chair label is the highest-probability return for this state. "
                "It does not place, size, or send."
            )
        ),
        "gold_pin": pin.get("pin_assert_error"),
        **_structural_marks(),
    }


def maybe_run_daily_loop(
    *,
    slate_path: Path | str | None = None,
    login: Any = None,
    namespace: Any = None,
    heartbeat_path: Path | str | None = None,
    study_path: Path | str | None = None,
    close_rows: Iterable[MappingLike] | None = None,
    store: LabelStore | None = None,
    as_of: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Observer. The env flag is a fact. The ask still runs. This module does not send."""

    return run_daily_loop(
        slate_path=slate_path,
        login=login,
        namespace=namespace,
        heartbeat_path=heartbeat_path,
        study_path=study_path,
        close_rows=close_rows,
        store=store,
        as_of=as_of,
        environ=environ,
    )
