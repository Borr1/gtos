"""Geometry-bound outcome model on the Challenge feature/label store.

Every decision in this file, including every parameter, is the System One
return for that state. One hop is ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False`` (POST
https://api.typesafe.ai/v1/systemone). Questions are only Noul, Choice, or
Score. Prior outcomes are attached on that ask, and the return is stored
for the next ask.

A Choice is the unique highest probability. A Score is the returned number
and may sit between the levels. A Noul is a bool or a probability. An empty
answer, a tie, a missing score, or an error leaves that field unset.
A floor and a baseline are not a question.

Measured cell counts stay the label arithmetic. This module does not place,
flatten, remint, or send. Judge code stays unable to send.

Book: Challenge 0 / ns operator / magic 0.
When the key is absent, the client does not post. A miss leaves the field unset.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

try:
    from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS, VERIFICATION_QUARANTINED
except Exception:
    CHALLENGE_LOGIN = 0
    CHALLENGE_MAGIC = 0
    CHALLENGE_NS = "operator"
    VERIFICATION_QUARANTINED = None

MappingLike = dict[str, Any]

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"

MODEL_SCHEMA = "gtos.judgment.challenge_outcome_model.v0"
FIT_SCHEMA = "gtos.judgment.challenge_outcome_fit.v0"
SCORE_SCHEMA = "gtos.judgment.challenge_outcome_score.v0"
FEATURE_SCHEMA = "gtos.judgment.challenge_history_features.v0"
LABEL_SCHEMA = "gtos.judgment.challenge_history_labels.v0"
FEATURE_STORE_EXCLUSION = "banned_from_asof_open_features_labels_only"

TRAIN_ENV = "GTOS_JEV_TRAINED_MODELS"
TRAIN_PATH_ENV = "GTOS_JEV_TRAINED_MODELS_PATH"
JEV_SCORE_ENV = "GTOS_JEV_TRAINED_MODELS_JEV_SCORE"

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_trained_models" / "fixtures"
)
DEFAULT_MODEL = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_trained_models" / "model.json"
)
DEFAULT_CHALLENGE = FIXTURE_DIR / "challenge_store_pack45.jsonl"
DEFAULT_WALKS = FIXTURE_DIR / "walk_store_trim.jsonl"
DEFAULT_SCREEN = FIXTURE_DIR / "screening_store_trim.jsonl"

# Named tickets. A fact on the receipt. This module does not touch them.
NEVER_FLATTEN_TICKETS = (294092360, 294088097, 294069721)

# Outcome-key names. Presence on a feature is a fact. The row choice decides.
_OUTCOME_NAMES = (
    "miss_type",
    "exit_class",
    "close_reason",
    "R",
    "realized_r",
    "broker_net",
    "profit",
    "mfe",
    "mae",
    "won",
    "why_lost",
    "why_lost_text",
)

_FAIL_REASONS = (
    "verification_quarantined",
    "other_login",
    "other_namespace",
    "w7_other_organism",
    "overlay_77_y2025",
    "persist_not_zero",
)
_ROW_FAILS = _FAIL_REASONS + ("expost_in_features", "label_exclusion_mismatch")
_ASSET_ORDER = ("XAU", "other")
_BIN_ORDER = ("missing", "ge4", "ge2", "lt2")
_CHAIR_ORDER = ("HARD_OFF", "KEEP", "STUDY", "STARVE", "WATCH")
_GRAIN_ORDER = ("occupancy", "named_session", "vol_bucket", "house_prior", "none")
_SLOT_ORDER = (
    "full",
    "family_asset_bin",
    "family_asset",
    "asset_bin",
    "family",
    "asset",
    "global",
    "none",
)
_TRAINER_ORDER = ("stored_labels", "scored")

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

Q_FAIL = "trained_models.fail_closed"
Q_FAIL_P = "trained_models.fail_closed_parameter"
Q_PIN = "trained_models.persist_pin_ok"
Q_ROW = "trained_models.row_disposition"
Q_ROW_P = "trained_models.row_parameter"
Q_ASSET = "trained_models.asset_bucket"
Q_ASSET_P = "trained_models.asset_bucket_parameter"
Q_BIN = "trained_models.plan_r_bin"
Q_EDGE = "trained_models.plan_r_edge"
Q_CHAIR = "trained_models.chair_label"
Q_CHAIR_P = "trained_models.chair_label_parameter"
Q_P_TIME = "trained_models.p_time_stop"
Q_MEAN_R = "trained_models.mean_R"
Q_MEAN_NET = "trained_models.mean_broker_net"
Q_P_POS = "trained_models.p_positive_R"
Q_BACKOFF = "trained_models.backoff_level"
Q_BACKOFF_P = "trained_models.backoff_parameter"
Q_GRAIN = "trained_models.unsigned_prior_grain"
Q_GRAIN_P = "trained_models.unsigned_prior_parameter"
Q_SIZE = "trained_models.size_up"
Q_APPLY = "trained_models.apply"
Q_SILENT = "trained_models.silent_apply"
Q_EXTRA = "trained_models.extra_pass"
Q_NEWS = "trained_models.news_protocol"
Q_EVERY = "trained_models.noul_every_tick"
Q_PERSIST = "trained_models.apply_persist"
Q_SKIP = "trained_models.fit_skipped"
Q_US30 = "trained_models.us30_off"
Q_XAU_STOP = "trained_models.xau_winners_all_time_stop"
Q_XAU_GE4 = "trained_models.xau_winners_all_plan_r_ge4"
Q_PRED_TIME = "trained_models.predicted_p_time_stop"
Q_PRED_R = "trained_models.predicted_E_R"
Q_PRED_NET = "trained_models.predicted_E_broker_net"
Q_PRED_POS = "trained_models.predicted_p_positive_R"
Q_JEV = "trained_models.jev_scored"
Q_MODE = "trained_models.trainer_mode"
Q_POSTS = "trained_models.jev_posts"


def train_enabled() -> bool:
    return os.environ.get(TRAIN_ENV, "").strip().lower() in {"1", "true", "yes"}


def typesafe_key_present() -> bool:
    return bool(os.environ.get("TYPESAFE_API_KEY", "").strip())


def jev_score_flag_on() -> bool:
    return os.environ.get(JEV_SCORE_ENV, "").strip().lower() in {"1", "true", "yes"}


def default_model_path() -> Path:
    override = (os.environ.get(TRAIN_PATH_ENV) or "").strip()
    return Path(override) if override else DEFAULT_MODEL


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
        if _limit_key(key) or _secret_key(key):
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
    if not kept or not _question_text_ok(instructions):
        return {}
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
    if not _question_text_ok(instructions) or _limit_key(qid):
        return {}
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


def _noul_body(qid: str, instructions: str) -> dict[str, Any]:
    if not _question_text_ok(instructions) or not _question_text_ok(qid):
        return {}
    true = "Yes, for this state."
    false = "No, for this state."
    block: dict[str, Any] = {
        "type": "noul",
        "instructions": instructions,
        "criteria": {"true": true, "false": false},
    }
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    return {qid: block}


def _clean_questions(questions: Mapping[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for qid, block in dict(questions or {}).items():
        if not isinstance(block, dict):
            continue
        kind = str(block.get("type") or "").strip().lower()
        if kind not in {"noul", "choice", "score"}:
            continue
        if _limit_key(str(qid)):
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
        row = dict(block)
        row["type"] = kind
        clean[str(qid)] = row
    return clean


def _choice_text(noun: str) -> str:
    return (
        f"What {noun} does this state earn? "
        "Facts already on this state stay facts. "
        "The unique highest probability is the decision. "
        "An empty answer or a tie leaves it unset. "
        "The paired score is the parameter and may sit between the levels. "
        "This does not place, size, or flatten."
    )


def _score_text(noun: str) -> str:
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves the parameter unset. "
        "This does not place, size, or flatten."
    )


def _noul_text(noun: str) -> str:
    return (
        f"The noul you return is whether {noun} holds for this state. "
        "An empty noul leaves it unset. "
        "This does not place, size, or flatten."
    )


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, Mapping) or block.get("error"):
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


def _choice_of(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
    """Unique highest. A bare label, an empty map, or a tie is unset."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None, {}
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"", "choice"}:
        return None, {}
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
    if agreed is None or local is None or str(agreed) != local or str(agreed) not in order:
        return None, kept
    return str(agreed), kept


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
    """A Noul stays a bool or a probability. Missing stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"", "noul"}:
        return None
    if "noul" in block:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    if "Noul" in block:
        raw = block.get("Noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    return None


def _parse(
    answers: Mapping[str, Any] | None,
    orders: Mapping[str, tuple[str, ...]],
    nouls: tuple[str, ...],
    scores: tuple[str, ...],
) -> dict[str, Any]:
    body = answers if isinstance(answers, Mapping) else {}
    choices: dict[str, str | None] = {}
    probabilities: dict[str, dict[str, float]] = {}
    for qid, order in orders.items():
        choice, probs = _choice_of(body.get(qid), order)
        choices[qid] = choice
        probabilities[qid] = probs
    return {
        "choices": choices,
        "probabilities": probabilities,
        "nouls": {qid: _noul_of(body.get(qid)) for qid in nouls},
        "scores": {qid: _score_of(body.get(qid)) for qid in scores},
    }


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


def _remember(qid: str, value: Any, error: str | None, state: Mapping[str, Any]) -> None:
    """History for the next ask. A miss is stored as a miss."""

    logged = _scrub(dict(state))
    if not isinstance(logged, dict):
        logged = {}
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome

        append_outcome(qid, value, logged, error=error)
    except Exception:
        _LOCAL_OUTCOMES.append({"key": qid, "spot": qid, "value": value, "error": error})


def _remember_parsed(
    state: Mapping[str, Any],
    parsed: Mapping[str, Any],
    error: str | None,
) -> None:
    pairs: list[tuple[str, Any, str]] = []
    for qid, value in dict(parsed.get("choices") or {}).items():
        pairs.append((qid, value, "tie_or_empty"))
    for qid, value in dict(parsed.get("nouls") or {}).items():
        pairs.append((qid, value, "noul_missing"))
    for qid, value in dict(parsed.get("scores") or {}).items():
        pairs.append((qid, value, "score_missing"))
    for qid, value, miss in pairs:
        _remember(qid, value, None if value is not None else (error or miss), state)


def _book(state: dict[str, Any]) -> dict[str, Any]:
    state["model"] = MODEL
    state["api_url"] = API_URL
    state.setdefault("book_login", CHALLENGE_LOGIN)
    state.setdefault("book_ns", CHALLENGE_NS)
    state.setdefault("book_magic", CHALLENGE_MAGIC)
    state.setdefault("verification_login", VERIFICATION_QUARANTINED)
    state["do_not_flatten_tickets"] = list(NEVER_FLATTEN_TICKETS)
    return state


def _evaluate(
    facts: Mapping[str, Any] | None,
    questions: Mapping[str, Any],
    call: Callable[..., Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """One System One post. Empty and error leave the answers unset."""

    packed = _clean_questions(questions)
    state = _scrub(dict(facts or {}))
    if not isinstance(state, dict):
        state = {}
    state.pop("prior_outcomes", None)
    _book(state)
    if not packed:
        receipt = {"ok": False, "error": "empty", "answers": {}, "model": MODEL, "skipped": None}
        return receipt, state
    _attach_priors(state, packed)
    caller = call
    if caller is None:
        try:
            from .jev_client import evaluate as caller
        except Exception as exc:
            receipt = {
                "ok": False,
                "error": type(exc).__name__,
                "answers": {},
                "model": MODEL,
                "skipped": None,
            }
            return receipt, state
    try:
        receipt = caller(state, questions=packed, merge_sleeve=False, model=MODEL)
    except Exception as exc:  # noqa: BLE001 — a dark ask must not raise into the writer
        receipt = {
            "ok": False,
            "error": type(exc).__name__,
            "answers": {},
            "model": MODEL,
            "skipped": None,
        }
        return receipt, state
    if not isinstance(receipt, dict):
        receipt = {"ok": False, "error": "evaluate_not_a_dict", "answers": {}, "model": MODEL}
        return receipt, state
    if receipt.get("ok") is False or receipt.get("error") or receipt.get("skipped"):
        return {**receipt, "answers": {}, "model": receipt.get("model") or MODEL}, state
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        return {
            **receipt,
            "ok": False,
            "error": str(receipt.get("error") or receipt.get("skipped") or "empty"),
            "answers": {},
            "model": receipt.get("model") or MODEL,
        }, state
    return receipt, state


def _ask_parsed(
    facts: Mapping[str, Any] | None,
    questions: Mapping[str, Any],
    orders: Mapping[str, tuple[str, ...]],
    nouls: tuple[str, ...],
    scores: tuple[str, ...],
    call: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    receipt, state = _evaluate(facts, questions, call=call)
    answers = receipt.get("answers") if isinstance(receipt, dict) else None
    if receipt.get("ok") is False or receipt.get("error") or receipt.get("skipped"):
        answers = {}
    parsed = _parse(answers if isinstance(answers, Mapping) else {}, orders, nouls, scores)
    err = None
    if not answers:
        err = str(receipt.get("error") or receipt.get("skipped") or "empty")
    parsed["error"] = err
    parsed["skipped"] = receipt.get("skipped")
    parsed["ok"] = bool(answers) and receipt.get("ok") is True
    _remember_parsed(state, parsed, err)
    return parsed


def _pin_facts() -> dict[str, Any]:
    """Pin records ride as facts when the module can be read. They do not decide."""

    try:
        from .gold_priors import GATE_COMPOSITE_WEIGHTS, PIN_WINDOW
    except Exception:
        return {}
    weights = GATE_COMPOSITE_WEIGHTS if isinstance(GATE_COMPOSITE_WEIGHTS, Mapping) else {}
    persist = weights.get("persistence") if isinstance(weights, Mapping) else None
    return {"recorded_pin_window": PIN_WINDOW, "recorded_persistence_weight": persist}


def _fail_questions(levels: list[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_choice_body(
        Q_FAIL,
        _choice_text("fail-closed reason"),
        {
            "clear": "This login, namespace, origin, and pin facts are the Challenge book.",
            "verification_quarantined": "The login fact is the verification login.",
            "other_login": "The login fact is some other book.",
            "other_namespace": "The namespace fact is some other book.",
            "w7_other_organism": "The origin fact is the other organism.",
            "overlay_77_y2025": "The pin-window fact is the overlay window.",
            "persist_not_zero": "The recorded persistence weight is off the Challenge pin.",
        },
    ))
    pack.update(_score_body(Q_FAIL_P, _score_text("fail-closed parameter"), levels))
    pack.update(_noul_body(Q_PIN, _noul_text("the recorded persistence pin holds")))
    return _clean_questions(pack)


def _row_questions(levels: list[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    criteria = {
        "keep": "This stored row stays in the geometry table.",
        "expost_in_features": "Outcome keys are present on the feature side.",
        "label_exclusion_mismatch": "The label exclusion fact differs from the store exclusion.",
    }
    for name in _FAIL_REASONS:
        criteria[name] = f"The row facts earn {name}."
    pack.update(_choice_body(Q_ROW, _choice_text("row disposition"), criteria))
    pack.update(_score_body(Q_ROW_P, _score_text("row parameter"), levels))
    return _clean_questions(pack)


def _asset_questions(levels: list[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_choice_body(
        Q_ASSET,
        _choice_text("asset bucket"),
        {
            "XAU": "The symbol fact is XAU or GOLD.",
            "other": "The symbol fact is outside XAU and GOLD.",
        },
    ))
    pack.update(_score_body(Q_ASSET_P, _score_text("asset-bucket parameter"), levels))
    return _clean_questions(pack)


def _bin_questions(levels: list[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_choice_body(
        Q_BIN,
        _choice_text("plan_r bin"),
        {
            "missing": "plan_r is missing on this state.",
            "ge4": "plan_r sits in the upper bin. The edge is the returned score.",
            "ge2": "plan_r sits in the middle bin. The edge is the returned score.",
            "lt2": "plan_r is present and sits in the lower bin. The edge is the returned score.",
        },
    ))
    pack.update(_score_body(Q_EDGE, _score_text("plan_r edge"), levels))
    return _clean_questions(pack)


def _chair_questions(levels: list[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_choice_body(
        Q_CHAIR,
        _choice_text("chair label"),
        {
            "HARD_OFF": "This geometry earns a hard-off label.",
            "KEEP": "This geometry earns a house-keep label.",
            "STUDY": "This geometry earns a study label.",
            "STARVE": "This geometry earns a starve label.",
            "WATCH": "This geometry earns a watch label.",
        },
    ))
    pack.update(_score_body(Q_CHAIR_P, _score_text("chair-label parameter"), levels))
    return _clean_questions(pack)


def _cell_questions(levels: list[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_score_body(Q_P_TIME, _score_text("time-stop probability"), levels))
    pack.update(_score_body(Q_MEAN_R, _score_text("mean R"), levels))
    pack.update(_score_body(Q_MEAN_NET, _score_text("mean broker net"), levels))
    pack.update(_score_body(Q_P_POS, _score_text("positive-R probability"), levels))
    return _clean_questions(pack)


def _grain_questions(levels: list[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_choice_body(
        Q_GRAIN,
        _choice_text("unsigned-prior grain"),
        {
            "occupancy": "The prior grain is occupancy.",
            "named_session": "The prior grain is the named session.",
            "vol_bucket": "The prior grain is the vol bucket.",
            "house_prior": "The prior grain is the house prior.",
            "none": "This state has no unsigned prior.",
        },
    ))
    pack.update(_score_body(Q_GRAIN_P, _score_text("unsigned-prior parameter"), levels))
    return _clean_questions(pack)


def _ticket_questions(levels: list[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_asset_questions(levels))
    pack.update(_bin_questions(levels))
    pack.update(_chair_questions(levels))
    pack.update(_grain_questions(levels))
    pack.update(_choice_body(
        Q_BACKOFF,
        _choice_text("backoff slot"),
        {
            "full": "The full geometry key is the cell.",
            "family_asset_bin": "Family, asset, and plan bin are the cell.",
            "family_asset": "Family and asset are the cell.",
            "asset_bin": "Asset and plan bin are the cell.",
            "family": "Family alone is the cell.",
            "asset": "Asset alone is the cell.",
            "global": "The global cell is the cell.",
            "none": "No backoff cell is selected.",
        },
    ))
    pack.update(_score_body(Q_BACKOFF_P, _score_text("backoff parameter"), levels))
    pack.update(_score_body(Q_PRED_TIME, _score_text("predicted time-stop probability"), levels))
    pack.update(_score_body(Q_PRED_R, _score_text("predicted E[R]"), levels))
    pack.update(_score_body(Q_PRED_NET, _score_text("predicted E[broker net]"), levels))
    pack.update(_score_body(Q_PRED_POS, _score_text("predicted positive-R probability"), levels))
    pack.update(_noul_body(Q_SIZE, _noul_text("size up")))
    pack.update(_noul_body(Q_APPLY, _noul_text("apply")))
    pack.update(_noul_body(Q_EXTRA, _noul_text("an extra pass")))
    pack.update(_noul_body(Q_NEWS, _noul_text("the news protocol is applied")))
    return _clean_questions(pack)


def _fit_questions(levels: list[str], family_ids: list[tuple[str, str]]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_noul_body(Q_APPLY, _noul_text("apply")))
    pack.update(_noul_body(Q_SILENT, _noul_text("silent apply")))
    pack.update(_noul_body(Q_EXTRA, _noul_text("an extra pass")))
    pack.update(_noul_body(Q_NEWS, _noul_text("the news protocol is applied")))
    pack.update(_noul_body(Q_EVERY, _noul_text("a noul is asked on every tick")))
    pack.update(_noul_body(Q_SKIP, _noul_text("this fit is skipped")))
    pack.update(_noul_body(Q_US30, _noul_text("US30 is off")))
    pack.update(_noul_body(Q_XAU_STOP, _noul_text("every XAU winner exit is time_stop")))
    pack.update(_noul_body(Q_XAU_GE4, _noul_text("every XAU winner plan bin is the upper bin")))
    pack.update(_score_body(Q_PERSIST, _score_text("apply persistence"), levels))
    for _family, qid in family_ids:
        pack.update(_score_body(qid, _score_text("family mean predicted E[R]"), levels))
    return _clean_questions(pack)


def _jev_questions(levels: list[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_noul_body(Q_JEV, _noul_text("this rung is jev-scored")))
    pack.update(_choice_body(
        Q_MODE,
        _choice_text("trainer mode"),
        {
            "stored_labels": "This rung scores from stored labels.",
            "scored": "This rung carries a System One score.",
        },
    ))
    pack.update(_score_body(Q_POSTS, _score_text("jev post count"), levels))
    return _clean_questions(pack)


def _f(value: Any) -> float | None:
    return _finite(value)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _ident(feat: Mapping[str, Any]) -> dict[str, Any]:
    return feat.get("identity") if isinstance(feat.get("identity"), Mapping) else {}


def _sess(feat: Mapping[str, Any]) -> dict[str, Any]:
    return feat.get("sessions") if isinstance(feat.get("sessions"), Mapping) else {}


def _geo(feat: Mapping[str, Any]) -> dict[str, Any]:
    return feat.get("geometry") if isinstance(feat.get("geometry"), Mapping) else {}


def asset_bucket(symbol: Any) -> str | None:
    """Asset bucket for this symbol. The unique highest probability is the bucket."""

    facts = {"symbol": symbol, **_pin_facts()}
    parsed = _ask_parsed(
        facts,
        _asset_questions(_levels(facts)),
        {Q_ASSET: _ASSET_ORDER},
        (),
        (Q_ASSET_P,),
    )
    return parsed["choices"].get(Q_ASSET)


def plan_r_bin(plan: Any) -> str | None:
    """Plan-r bin. The edge is the paired score on this ask."""

    facts = {"plan_r": _f(plan), **_pin_facts()}
    parsed = _ask_parsed(
        facts,
        _bin_questions(_levels(facts)),
        {Q_BIN: _BIN_ORDER},
        (),
        (Q_EDGE,),
    )
    return parsed["choices"].get(Q_BIN)


def persist_pin_ok() -> bool | None:
    """Persistence-pin Noul. A miss stays missing."""

    facts = _pin_facts()
    parsed = _ask_parsed(
        facts,
        _clean_questions(_noul_body(Q_PIN, _noul_text("the recorded persistence pin holds"))),
        {},
        (Q_PIN,),
        (),
    )
    value = parsed["nouls"].get(Q_PIN)
    if value is True or value is False:
        return value
    return None


def fail_closed_reason(
    *,
    login: Any = None,
    ns: Any = None,
    origin: Any = None,
    pin_window: Any = None,
) -> str | None:
    """Fail-closed choice. ``clear`` is that choice. A miss stays missing."""

    facts = {
        "login": login,
        "ns": ns,
        "origin": origin,
        "pin_window": pin_window,
        **_pin_facts(),
    }
    parsed = _ask_parsed(
        facts,
        _fail_questions(_levels(facts)),
        {Q_FAIL: ("clear",) + _FAIL_REASONS},
        (Q_PIN,),
        (Q_FAIL_P,),
    )
    return parsed["choices"].get(Q_FAIL)


def _row_facts(row: Mapping[str, Any]) -> dict[str, Any]:
    feat = row.get("feature") if isinstance(row.get("feature"), Mapping) else {}
    lab = row.get("label") if isinstance(row.get("label"), Mapping) else {}
    ident = _ident(feat)
    present = [name for name in _OUTCOME_NAMES if name in feat]
    return {
        "login": ident.get("login"),
        "ns": ident.get("ns"),
        "origin": ident.get("origin_organism"),
        "symbol": ident.get("symbol"),
        "family_class": ident.get("family_class"),
        "grain": feat.get("grain"),
        "feature_keys": sorted(str(key) for key in feat),
        "outcome_keys_present": present,
        "label_exclusion": lab.get("feature_store_exclusion") if isinstance(lab, Mapping) else None,
        "expected_exclusion": FEATURE_STORE_EXCLUSION,
        **_pin_facts(),
    }


def row_ok(row: Mapping[str, Any]) -> tuple[bool | None, str | None]:
    """Row disposition. ``keep`` admits the row. A miss stays missing."""

    facts = _row_facts(row)
    parsed = _ask_parsed(
        facts,
        _row_questions(_levels(facts)),
        {Q_ROW: ("keep",) + _ROW_FAILS},
        (),
        (Q_ROW_P,),
    )
    choice = parsed["choices"].get(Q_ROW)
    if choice == "keep":
        return True, None
    if choice in _ROW_FAILS:
        return False, str(choice)
    return None, None


def geometry_key(feat: Mapping[str, Any]) -> tuple[Any, Any, str | None, str | None]:
    ident = _ident(feat)
    sess = _sess(feat)
    geo = _geo(feat)
    family = ident.get("family_class")
    occ = sess.get("occupancy_label")
    if family is not None:
        family = str(family)
    if occ is not None:
        occ = str(occ)
    facts = {
        "family_class": family,
        "occupancy_label": occ,
        "symbol": ident.get("symbol"),
        "plan_r": _f(geo.get("plan_r")),
    }
    levels = _levels(facts)
    questions = _clean_questions({**_asset_questions(levels), **_bin_questions(levels)})
    parsed = _ask_parsed(
        facts,
        questions,
        {Q_ASSET: _ASSET_ORDER, Q_BIN: _BIN_ORDER},
        (),
        (Q_ASSET_P, Q_EDGE),
    )
    return (family, occ, parsed["choices"].get(Q_ASSET), parsed["choices"].get(Q_BIN))


def backoff_keys(key: tuple[Any, Any, Any, Any]) -> tuple[tuple[Any, ...], ...]:
    family, occ, asset, pbin = key
    return (
        (family, occ, asset, pbin),
        (family, asset, pbin),
        (family, asset),
        (asset, pbin),
        (family,),
        (asset,),
        (),
    )


def _slot_key(
    slot: str | None,
    family: Any,
    occ: Any,
    asset: str | None,
    pbin: str | None,
) -> tuple[Any, ...] | None:
    table: dict[str, tuple[Any, ...]] = {
        "full": (family, occ, asset, pbin),
        "family_asset_bin": (family, asset, pbin),
        "family_asset": (family, asset),
        "asset_bin": (asset, pbin),
        "family": (family,),
        "asset": (asset,),
        "global": (),
    }
    if slot is None or slot == "none":
        return None
    return table.get(slot)


class _Cell:
    __slots__ = ("n", "k_time_stop", "k_positive_R", "sum_R", "sum_net", "n_R", "n_net")

    def __init__(self) -> None:
        self.n = 0
        self.k_time_stop = 0
        self.k_positive_R = 0
        self.sum_R = 0.0
        self.sum_net = 0.0
        self.n_R = 0
        self.n_net = 0

    def add(self, lab: Mapping[str, Any]) -> None:
        self.n += 1
        if lab.get("exit_class") == "time_stop":
            self.k_time_stop += 1
        r_val = _f(lab.get("R"))
        if r_val is not None:
            self.sum_R += r_val
            self.n_R += 1
            if r_val > 0:
                self.k_positive_R += 1
        net = _f(lab.get("broker_net"))
        if net is not None:
            self.sum_net += net
            self.n_net += 1

    def remove(self, lab: Mapping[str, Any]) -> None:
        self.n = max(0, self.n - 1)
        if lab.get("exit_class") == "time_stop":
            self.k_time_stop = max(0, self.k_time_stop - 1)
        r_val = _f(lab.get("R"))
        if r_val is not None and self.n_R:
            self.sum_R -= r_val
            self.n_R -= 1
            if r_val > 0:
                self.k_positive_R = max(0, self.k_positive_R - 1)
        net = _f(lab.get("broker_net"))
        if net is not None and self.n_net:
            self.sum_net -= net
            self.n_net -= 1

    def counts(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "k_time_stop": self.k_time_stop,
            "k_positive_R": self.k_positive_R,
            "sum_R": self.sum_R,
            "sum_net": self.sum_net,
            "n_R": self.n_R,
            "n_net": self.n_net,
        }

    def report(self) -> dict[str, Any]:
        """Counts are the label arithmetic. Rates and means are the scores."""

        facts = self.counts()
        parsed = _ask_parsed(
            facts,
            _cell_questions(_levels(facts)),
            {},
            (),
            (Q_P_TIME, Q_MEAN_R, Q_MEAN_NET, Q_P_POS),
        )
        scores = parsed["scores"]
        return {
            "n": self.n,
            "k_time_stop": self.k_time_stop,
            "p_time_stop": scores.get(Q_P_TIME),
            "mean_R": scores.get(Q_MEAN_R),
            "mean_broker_net": scores.get(Q_MEAN_NET),
            "p_positive_R": scores.get(Q_P_POS),
            "k_positive_R": self.k_positive_R,
        }


def _cell_label(key: tuple[Any, ...]) -> str:
    if not key:
        return "global"
    return "|".join("" if part is None else str(part) for part in key)


def _copy_cell(cell: _Cell) -> _Cell:
    out = _Cell()
    out.n = cell.n
    out.k_time_stop = cell.k_time_stop
    out.k_positive_R = cell.k_positive_R
    out.sum_R = cell.sum_R
    out.sum_net = cell.sum_net
    out.n_R = cell.n_R
    out.n_net = cell.n_net
    return out


def select_cell(
    cells: Mapping[tuple[Any, ...], _Cell],
    key: tuple[Any, Any, Any, Any],
) -> tuple[tuple[Any, ...] | None, _Cell]:
    """Backoff slot for this key. A miss leaves the key unset."""

    menu = backoff_keys(key)
    labels = [_cell_label(item) for item in menu]
    listed: list[dict[str, Any]] = []
    for item, label in zip(menu, labels):
        cell = cells.get(item)
        listed.append({"key": label, **(cell.counts() if cell is not None else {"n": 0})})
    facts = {"menu": listed, "asked_key": _cell_label(key)}
    criteria = {label: f"The cell {label} is the backoff cell." for label in labels}
    criteria["none"] = "No backoff cell is selected."
    levels = _levels(facts)
    questions = _clean_questions({
        **_choice_body(Q_BACKOFF, _choice_text("backoff cell"), criteria),
        **_score_body(Q_BACKOFF_P, _score_text("backoff parameter"), levels),
    })
    order = tuple(label for label in labels if label in (questions.get(Q_BACKOFF) or {}).get("criteria", {}))
    order = tuple(dict.fromkeys((*order, "none")))
    parsed = _ask_parsed(facts, questions, {Q_BACKOFF: order}, (), (Q_BACKOFF_P,))
    choice = parsed["choices"].get(Q_BACKOFF)
    if choice is None or choice == "none":
        return None, _Cell()
    for item, label in zip(menu, labels):
        if label == choice:
            found = cells.get(item)
            return item, found if found is not None else _Cell()
    return None, _Cell()


def _walk_measurements(
    feat: Mapping[str, Any],
    walk_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    sess = _sess(feat)
    wanted_occ = sess.get("occupancy_label")
    wanted_named = sess.get("named")
    vol = (feat.get("regime") or {}).get("vol_bucket") if isinstance(feat.get("regime"), Mapping) else None
    measured: list[dict[str, Any]] = []
    for row in walk_rows:
        wfeat = row.get("feature") if isinstance(row.get("feature"), Mapping) else {}
        wlab = row.get("label") if isinstance(row.get("label"), Mapping) else {}
        if wfeat.get("grain") != "unsigned_m15_cell":
            continue
        p = _f(wlab.get("long_p_target"))
        try:
            n = int(wlab.get("n") or 0)
        except (TypeError, ValueError):
            n = 0
        if p is None or n <= 0:
            continue
        grain = wlab.get("grain")
        if grain == "house_floor":
            grain = "house_prior"
        wsess = _sess(wfeat)
        measured.append(
            {
                "grain": grain,
                "window": wlab.get("window") or wfeat.get("window"),
                "n": n,
                "long_p_target": p,
                "occupancy": wsess.get("occupancy_label"),
                "named": wsess.get("named"),
                "vol_bucket": (wfeat.get("regime") or {}).get("vol_bucket")
                if isinstance(wfeat.get("regime"), Mapping)
                else None,
                "wanted_occupancy": wanted_occ,
                "wanted_named": wanted_named,
                "wanted_vol": vol,
            }
        )
    return measured


def _prior_from(parsed: Mapping[str, Any]) -> dict[str, Any] | None:
    grain = (parsed.get("choices") or {}).get(Q_GRAIN)
    if grain is None or grain == "none":
        return None
    score = (parsed.get("scores") or {}).get(Q_GRAIN_P)
    return {"grain": grain, "long_p_target": score, "parameter": score}


def unsigned_prior_for(
    feat: Mapping[str, Any],
    walk_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Unsigned prior. The grain is the choice. The parameter is the score."""

    facts = {
        "symbol": _ident(feat).get("symbol"),
        "occupancy_label": _sess(feat).get("occupancy_label"),
        "named": _sess(feat).get("named"),
        "measurements": _walk_measurements(feat, walk_rows),
    }
    parsed = _ask_parsed(
        facts,
        _grain_questions(_levels(facts)),
        {Q_GRAIN: _GRAIN_ORDER},
        (),
        (Q_GRAIN_P,),
    )
    return _prior_from(parsed)


def _accumulate(rows: Iterable[Mapping[str, Any]]) -> dict[tuple[Any, ...], _Cell]:
    cells: dict[tuple[Any, ...], _Cell] = defaultdict(_Cell)
    for row in rows:
        feat = row.get("feature") if isinstance(row.get("feature"), Mapping) else None
        lab = row.get("label") if isinstance(row.get("label"), Mapping) else None
        if feat is None or lab is None:
            continue
        key = geometry_key(feat)
        for bk in backoff_keys(key):
            cells[bk].add(lab)
    return cells


def score_ticket(
    row: Mapping[str, Any],
    cells: Mapping[tuple[Any, ...], _Cell],
    *,
    walk_rows: Iterable[Mapping[str, Any]] = (),
    loo: bool = False,
) -> dict[str, Any]:
    feat = row.get("feature") if isinstance(row.get("feature"), Mapping) else {}
    lab = row.get("label") if isinstance(row.get("label"), Mapping) else {}
    ident = _ident(feat)
    family = ident.get("family_class")
    occ = _sess(feat).get("occupancy_label")
    if family is not None:
        family = str(family)
    if occ is not None:
        occ = str(occ)
    counted = [
        {"key": _cell_label(key), **cell.counts()}
        for key, cell in cells.items()
    ]
    facts = {
        "ticket": ident.get("candidate_id"),
        "symbol": ident.get("symbol"),
        "sleeve": ident.get("sleeve"),
        "family_class": family,
        "occupancy_label": occ,
        "named": _sess(feat).get("named"),
        "plan_r": _f(_geo(feat).get("plan_r")),
        "hard_off_family": (feat.get("surface") or {}).get("hard_off_family")
        if isinstance(feat.get("surface"), Mapping)
        else None,
        "loo": loo,
        "cell_counts": counted,
        "measurements": _walk_measurements(feat, walk_rows),
        "realized_exit_class": lab.get("exit_class"),
        "realized_R": lab.get("R"),
        "realized_broker_net": lab.get("broker_net"),
    }
    parsed = _ask_parsed(
        facts,
        _ticket_questions(_levels(facts)),
        {
            Q_ASSET: _ASSET_ORDER,
            Q_BIN: _BIN_ORDER,
            Q_CHAIR: _CHAIR_ORDER,
            Q_GRAIN: _GRAIN_ORDER,
            Q_BACKOFF: _SLOT_ORDER,
        },
        (Q_SIZE, Q_APPLY, Q_EXTRA, Q_NEWS),
        (Q_EDGE, Q_CHAIR_P, Q_GRAIN_P, Q_BACKOFF_P, Q_PRED_TIME, Q_PRED_R, Q_PRED_NET, Q_PRED_POS),
    )
    choices = parsed["choices"]
    scores = parsed["scores"]
    nouls = parsed["nouls"]
    asset = choices.get(Q_ASSET)
    pbin = choices.get(Q_BIN)
    slot = choices.get(Q_BACKOFF)
    used = _slot_key(slot, family, occ, asset, pbin)
    n_cell = None
    if used is not None:
        found = cells.get(used)
        if found is None:
            n_cell = 0
        elif loo:
            held = _copy_cell(found)
            held.remove(lab)
            n_cell = held.n
        else:
            n_cell = found.n
    return {
        "schema": SCORE_SCHEMA,
        "ticket": ident.get("candidate_id"),
        "symbol": ident.get("symbol"),
        "sleeve": ident.get("sleeve"),
        "family_class": family,
        "asset": asset,
        "occupancy": occ,
        "named": _sess(feat).get("named"),
        "plan_r": _geo(feat).get("plan_r"),
        "plan_r_bin": pbin,
        "plan_r_edge": scores.get(Q_EDGE),
        "geometry_key": [family, occ, asset, pbin],
        "backoff": None if used is None else list(used),
        "n_cell": n_cell,
        "predicted_p_time_stop": scores.get(Q_PRED_TIME),
        "predicted_E_R": scores.get(Q_PRED_R),
        "predicted_E_broker_net": scores.get(Q_PRED_NET),
        "predicted_p_positive_R": scores.get(Q_PRED_POS),
        "realized_exit_class": lab.get("exit_class"),
        "realized_R": lab.get("R"),
        "realized_broker_net": lab.get("broker_net"),
        "chair_label": choices.get(Q_CHAIR),
        "chair_label_parameter": scores.get(Q_CHAIR_P),
        "size_up": nouls.get(Q_SIZE),
        "unsigned_prior": _prior_from(parsed),
        "apply": nouls.get(Q_APPLY),
        "extra_pass": nouls.get(Q_EXTRA),
        "NEWS_PROTOCOL_APPLIED": nouls.get(Q_NEWS),
        "loo": loo,
    }


def chair_label(feat: Mapping[str, Any]) -> str | None:
    """Chair label. The unique highest probability is the label."""

    ident = _ident(feat)
    surface = feat.get("surface") if isinstance(feat.get("surface"), Mapping) else {}
    facts = {
        "family_class": ident.get("family_class"),
        "hard_off_family": surface.get("hard_off_family"),
        "symbol": ident.get("symbol"),
    }
    parsed = _ask_parsed(
        facts,
        _chair_questions(_levels(facts)),
        {Q_CHAIR: _CHAIR_ORDER},
        (),
        (Q_CHAIR_P,),
    )
    return parsed["choices"].get(Q_CHAIR)


def maybe_jev_score(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Jev score for this rung. The flag is a gate. A miss stays missing."""

    del rows
    base = {
        "jev_scored": None,
        "reason": None,
        "posts": None,
        "trainer_mode": None,
        "model": MODEL,
        "api_url": API_URL,
    }
    if not jev_score_flag_on():
        return {**base, "reason": f"{JEV_SCORE_ENV}_off"}
    facts = {
        "typesafe_key_present": typesafe_key_present(),
        "n_rows": None,
    }
    parsed = _ask_parsed(
        facts,
        _jev_questions(_levels(facts)),
        {Q_MODE: _TRAINER_ORDER},
        (Q_JEV,),
        (Q_POSTS,),
    )
    return {
        **base,
        "jev_scored": parsed["nouls"].get(Q_JEV),
        "reason": parsed.get("error"),
        "posts": parsed["scores"].get(Q_POSTS),
        "trainer_mode": parsed["choices"].get(Q_MODE),
    }


def load_store_rows(
    *,
    challenge_path: Path | None = None,
    walk_path: Path | None = None,
    screening_path: Path | None = None,
) -> dict[str, Any]:
    challenge = load_jsonl(challenge_path or DEFAULT_CHALLENGE)
    walks = load_jsonl(walk_path or DEFAULT_WALKS)
    screening = load_jsonl(screening_path or DEFAULT_SCREEN)
    kept_c: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in challenge:
        ok, reason = row_ok(row)
        if ok is not True:
            feat = row.get("feature") if isinstance(row.get("feature"), Mapping) else {}
            skipped.append({"ticket": _ident(feat).get("candidate_id"), "reason": reason})
            continue
        if (row.get("feature") or {}).get("grain") not in {None, "challenge_ticket"}:
            continue
        kept_c.append(row)
    kept_w = []
    for row in walks:
        ok, _reason = row_ok(row)
        if ok is True:
            kept_w.append(row)
    kept_s = []
    for row in screening:
        ok, _reason = row_ok(row)
        if ok is True:
            kept_s.append(row)
    return {
        "challenge_rows": kept_c,
        "walk_rows": kept_w,
        "screening_rows": kept_s,
        "skipped": skipped,
        "paths": {
            "challenge": str(challenge_path or DEFAULT_CHALLENGE),
            "walks": str(walk_path or DEFAULT_WALKS),
            "screening": str(screening_path or DEFAULT_SCREEN),
        },
    }


def _shell(*, skipped: Any, skip_reason: str | None, fail_closed: bool | None) -> dict[str, Any]:
    # never_place, never_flatten, and never_remint are structural.
    # This module has no send path.
    return {
        "schema": FIT_SCHEMA,
        "model_schema": MODEL_SCHEMA,
        "model": MODEL,
        "api_url": API_URL,
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "skipped": skipped,
        "skip_reason": skip_reason,
        "fail_closed": fail_closed,
        "apply": None,
        "silent_apply": None,
        "extra_pass": None,
        "never_place": True,
        "never_flatten": True,
        "never_remint": True,
        "NEWS_PROTOCOL_APPLIED": None,
        "apply_persist": None,
        "pin_window": None,
        "do_not_flatten_tickets": list(NEVER_FLATTEN_TICKETS),
        "feature_store_exclusion": FEATURE_STORE_EXCLUSION,
        "trainer_mode": None,
        "typesafe_key_present": typesafe_key_present(),
        "jev_posts": None,
        "noul_every_tick": None,
        "us30_off": None,
        "xau_winners_all_time_stop": None,
        "xau_winners_all_plan_r_ge4": None,
    }


def _family_qid(family: str) -> str | None:
    token = "".join(ch if ch.isalnum() else "_" for ch in family)[:40]
    if not token:
        return None
    qid = f"trained_models.family_mean_e_r_{token}"
    if _limit_key(qid) or not _question_text_ok(qid):
        return None
    return qid


def _family_roll(
    scored: list[dict[str, Any]],
    means: Mapping[str, float | None],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        family = row.get("family_class")
        if not family:
            continue
        by[str(family)].append(row)
    for family, group in by.items():
        labels = sorted({str(item.get("chair_label")) for item in group if item.get("chair_label")})
        qid = _family_qid(family)
        out[family] = {
            "n": len(group),
            "mean_predicted_E_R": None if qid is None else means.get(qid),
            "chair_labels": labels,
        }
    return out


def fit_model(
    *,
    challenge_path: Path | None = None,
    walk_path: Path | None = None,
    screening_path: Path | None = None,
    enabled: bool | None = None,
    loo: bool = True,
) -> dict[str, Any]:
    """Fit the geometry table when the fail-closed choice is clear."""

    on = train_enabled() if enabled is None else enabled
    if not on:
        return _shell(skipped=True, skip_reason=f"{TRAIN_ENV}_off", fail_closed=None)
    reason = fail_closed_reason(login=CHALLENGE_LOGIN, ns=CHALLENGE_NS)
    if reason is None:
        return _shell(skipped=None, skip_reason=None, fail_closed=None)
    if reason != "clear":
        return _shell(skipped=True, skip_reason=reason, fail_closed=True)
    loaded = load_store_rows(
        challenge_path=challenge_path,
        walk_path=walk_path,
        screening_path=screening_path,
    )
    tickets = loaded["challenge_rows"]
    walks = loaded["walk_rows"]
    screening = loaded["screening_rows"]
    cells = _accumulate(tickets)
    in_sample = [score_ticket(row, cells, walk_rows=walks, loo=False) for row in tickets]
    loo_rows = [score_ticket(row, cells, walk_rows=walks, loo=True) for row in tickets] if loo else []
    jev = maybe_jev_score(tickets)

    xau_winners = []
    for row in in_sample:
        if row.get("asset") != "XAU":
            continue
        realized = _f(row.get("realized_R"))
        if realized is None or realized <= 0:
            continue
        xau_winners.append(row)
    us30_flags = []
    for row in screening:
        feat = row.get("feature") if isinstance(row.get("feature"), Mapping) else {}
        symbol = str(_ident(feat).get("symbol") or "")
        if not symbol.upper().startswith("US30"):
            continue
        surface = feat.get("surface") if isinstance(feat.get("surface"), Mapping) else {}
        if "us30_off" in surface:
            us30_flags.append(bool(surface.get("us30_off")))
    families = sorted({str(row.get("family_class")) for row in in_sample if row.get("family_class")})
    family_ids = []
    for family in families:
        qid = _family_qid(family)
        if qid is not None:
            family_ids.append((family, qid))
    fit_facts = {
        "n_tickets": len(tickets),
        "n_walk_priors": len(walks),
        "n_screening": len(screening),
        "us30_flags": us30_flags,
        "xau_winner_exits": [row.get("realized_exit_class") for row in xau_winners],
        "xau_winner_bins": [row.get("plan_r_bin") for row in xau_winners],
        "families": families,
    }
    fit = _ask_parsed(
        fit_facts,
        _fit_questions(_levels(fit_facts), family_ids),
        {},
        (Q_APPLY, Q_SILENT, Q_EXTRA, Q_NEWS, Q_EVERY, Q_SKIP, Q_US30, Q_XAU_STOP, Q_XAU_GE4),
        (Q_PERSIST, *(qid for _family, qid in family_ids)),
    )
    nouls = fit["nouls"]
    scores = fit["scores"]
    cell_dump = {
        _cell_label(key): cell.report()
        for key, cell in sorted(cells.items(), key=lambda kv: (-kv[1].n, _cell_label(kv[0])))
    }
    base = _shell(skipped=nouls.get(Q_SKIP), skip_reason=None, fail_closed=False)
    return {
        **base,
        "apply": nouls.get(Q_APPLY),
        "silent_apply": nouls.get(Q_SILENT),
        "extra_pass": nouls.get(Q_EXTRA),
        "NEWS_PROTOCOL_APPLIED": nouls.get(Q_NEWS),
        "apply_persist": scores.get(Q_PERSIST),
        "noul_every_tick": nouls.get(Q_EVERY),
        "n_tickets": len(tickets),
        "n_walk_priors": len(walks),
        "n_screening": len(screening),
        "n_skipped": len(loaded["skipped"]),
        "skipped_rows": loaded["skipped"],
        "sources": loaded["paths"],
        "cells": cell_dump,
        "in_sample": in_sample,
        "loo": loo_rows,
        "family_in_sample": _family_roll(in_sample, scores),
        "family_loo": _family_roll(loo_rows, scores) if loo_rows else {},
        "xau_winners_n": len(xau_winners),
        "xau_winners_all_time_stop": nouls.get(Q_XAU_STOP),
        "xau_winners_all_plan_r_ge4": nouls.get(Q_XAU_GE4),
        "us30_off": nouls.get(Q_US30),
        "jev": jev,
        "jev_posts": jev.get("posts"),
        "typesafe_key_present": typesafe_key_present(),
        "trainer_mode": jev.get("trainer_mode"),
        "do_not_flatten_tickets": list(NEVER_FLATTEN_TICKETS),
    }


def compact_fit(pack: Mapping[str, Any]) -> dict[str, Any]:
    keep = {
        "schema",
        "model_schema",
        "model",
        "api_url",
        "book",
        "ns",
        "magic",
        "skipped",
        "skip_reason",
        "fail_closed",
        "apply",
        "silent_apply",
        "extra_pass",
        "never_place",
        "never_flatten",
        "never_remint",
        "NEWS_PROTOCOL_APPLIED",
        "apply_persist",
        "pin_window",
        "do_not_flatten_tickets",
        "feature_store_exclusion",
        "trainer_mode",
        "typesafe_key_present",
        "jev_posts",
        "noul_every_tick",
        "n_tickets",
        "n_walk_priors",
        "n_screening",
        "n_skipped",
        "sources",
        "family_in_sample",
        "family_loo",
        "xau_winners_n",
        "xau_winners_all_time_stop",
        "xau_winners_all_plan_r_ge4",
        "us30_off",
        "jev",
        "cells",
    }
    out = {k: pack[k] for k in keep if k in pack}
    samples = []
    for row in pack.get("loo") or pack.get("in_sample") or []:
        if str(row.get("ticket")) in {"291794419", "291113462", "291076386", "291087142"}:
            samples.append(
                {
                    "ticket": row.get("ticket"),
                    "chair_label": row.get("chair_label"),
                    "predicted_E_R": row.get("predicted_E_R"),
                    "predicted_p_time_stop": row.get("predicted_p_time_stop"),
                    "backoff": row.get("backoff"),
                    "n_cell": row.get("n_cell"),
                    "realized_R": row.get("realized_R"),
                    "realized_exit_class": row.get("realized_exit_class"),
                    "unsigned_prior": row.get("unsigned_prior"),
                    "loo": row.get("loo"),
                }
            )
    out["score_samples"] = samples
    return out


def write_model(pack: Mapping[str, Any], path: Path | None = None) -> Path:
    target = path or default_model_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(compact_fit(pack), indent=2) + "\n", encoding="utf-8")
    return target


def ask_fitted_label() -> dict[str, Any]:
    """Fitted chair label. The unique highest probability is the label."""

    facts = {"spot": "trained_models", **_pin_facts()}
    parsed = _ask_parsed(
        facts,
        _chair_questions(_levels(facts)),
        {Q_CHAIR: _CHAIR_ORDER},
        (),
        (Q_CHAIR_P,),
    )
    choice = parsed["choices"].get(Q_CHAIR)
    return {
        "model": MODEL,
        "api_url": API_URL,
        "choice": choice,
        "parameter": parsed["scores"].get(Q_CHAIR_P),
        "probabilities": (parsed.get("probabilities") or {}).get(Q_CHAIR) or {},
        "decision_emitted": choice is not None,
        "error": None if choice is not None else (parsed.get("error") or "tie_or_empty"),
    }


def _ask_fitted_label_on_load() -> None:
    if not train_enabled():
        return
    try:
        ask_fitted_label()
    except Exception:
        return


_ask_fitted_label_on_load()
