"""Sleeve-tree decisions for one state.

One piece. One ``jev_client.evaluate`` (model ``jev-1.13.0``,
``merge_sleeve=False``) posts this sleeve's hierarchical subtree to
https://api.typesafe.ai/v1/systemone. Questions are only Noul, Choice,
or Score. Prior outcomes are attached on that ask. The choice is the
unique highest probability. A score may sit between the levels. An empty
answer, a tie, or an error leaves that return unset.

Floor and baseline are not a question. The family tree stays hierarchical.
Code owns emit. This module does not send.
"""

from __future__ import annotations

import os
from typing import Any, Mapping

from .challenge import CHALLENGE_LOGIN
from .jev_questions import (
    MODEL,
    append_outcome,
    prior_outcomes,
    returned_number,
    unique_highest,
)
from .sleeve_ifs import (
    converted_ifs,
    family_node_for,
    hierarchical_labels,
    integer_facts,
    noul_question_ids,
    sleeve_subtree_questions,
)

SLEEVE_ENV = "GTOS_JEV_SLEEVE"
_TRUTHY_OFF = frozenset({"0", "false", "no", "off"})
_TRUTHY_ON = frozenset({"1", "true", "yes", "on"})
_QUESTION_TYPES = frozenset({"noul", "choice", "score"})
_SECRET_PARTS = ("api_key", "apikey", "authorization", "secret", "password")
_ECHO_KEYS = (
    "prior_outcomes",
    "size_tilt",
    "disposition",
    "include_depth",
    "state_sufficient_low",
    "sleeve_jev",
    "parameters",
    "choices",
    "nouls",
    "unset",
)
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "110000",
    "110,000",
    "110_000",
    "110k",
)
_SCORE_FIELDS = (
    ("persistence_score", "persistence"),
    ("session_fitness_score", "session_fitness"),
    ("geometry_vs_tape_score", "geometry_vs_tape"),
    ("metals_band_depth", "metals_band_depth"),
    ("energy_ignition", "energy_ignition"),
    ("cell_fitness", "cell_fitness"),
    ("vol_state", "vol_state"),
    ("htf_regime", "htf_regime"),
    ("directional_efficiency", "directional_efficiency"),
    ("exit_profile_fit", "exit_profile_fit"),
)


def overlay_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Default on. Explicit 0/false/off leaves the overlay off."""
    env = environ if environ is not None else os.environ
    raw = str(env.get(SLEEVE_ENV, "")).strip().lower()
    if raw in _TRUTHY_OFF:
        return False
    if raw in _TRUTHY_ON or raw == "":
        return True
    return True


def _number(value: Any) -> float | None:
    """A returned number. Booleans, blanks, and non-finite values stay empty."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _limit_key(name: Any) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    for token in _BANNED_TEXT:
        probe = token.replace(",", "").replace("_", "").lower()
        if probe in compact:
            return True
    return False


def _secret_key(name: Any) -> bool:
    token = str(name).lower().replace("-", "_")
    return any(part in token for part in _SECRET_PARTS)


def _scrub(value: Any, seen: set[int] | None = None) -> Any:
    """Drop limit keys, secrets, and banned dollar tokens before the ask."""
    if seen is None:
        seen = set()
    mark = id(value)
    if mark in seen:
        return None
    if isinstance(value, Mapping):
        seen.add(mark)
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _limit_key(key) or _secret_key(key):
                continue
            out[str(key)] = _scrub(item, seen)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        seen.add(mark)
        return [_scrub(item, seen) for item in value]
    if isinstance(value, str) and _banned_text(value):
        return ""
    return value


def _block(answers: Mapping[str, Any] | None, key: str) -> dict[str, Any] | None:
    if not isinstance(answers, Mapping) or not answers:
        return None
    block = answers.get(key)
    return dict(block) if isinstance(block, Mapping) else None


def _jev_noul(answers: Mapping[str, Any] | None, key: str) -> bool | float | None:
    block = _block(answers, key)
    if block is None or "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _number(raw)


def _jev_score(answers: Mapping[str, Any] | None, key: str) -> float | None:
    block = _block(answers, key)
    if block is None:
        return None
    try:
        return _number(returned_number(block))
    except Exception:
        return None


def _choice_block(block: Mapping[str, Any] | None, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A bare label, a tie, or an empty block is unset."""
    if not isinstance(block, Mapping):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping) or not probs:
        return None
    try:
        picked = unique_highest(probs, order if order else None)
    except Exception:
        return None
    if picked is None:
        return None
    if order and str(picked) not in order:
        return None
    return str(picked)


def _numeric_probs(probs: Mapping[str, Any], order: tuple[str, ...]) -> list[float]:
    names = order if order else tuple(str(name) for name in probs)
    found: list[float] = []
    for name in names:
        if name not in probs:
            continue
        number = _number(probs.get(name))
        if number is not None:
            found.append(number)
    return found


def _unset_reason(block: Mapping[str, Any] | None, order: tuple[str, ...]) -> str:
    if not isinstance(block, Mapping):
        return "empty"
    probs = block.get("probabilities") if isinstance(block.get("probabilities"), Mapping) else None
    if isinstance(probs, Mapping) and _numeric_probs(probs, order):
        return "tie"
    if block.get("error"):
        return "error"
    return "empty"


def include_depth_name(score: float | None) -> float | None:
    """Include-depth is the returned score. A missing score stays missing."""
    return _number(score)


def completeness_noul(answers: Mapping[str, Any] | None) -> bool | float | None:
    """Completeness Noul on this state. A missing noul stays missing."""
    gold = _jev_noul(answers, "state_sufficient")
    if gold is not None:
        return gold
    return _jev_noul(answers, "sleeve_state_sufficient")


def _criteria(raw: Any, kind: str) -> dict[str, str] | list[str]:
    if kind == "score":
        if isinstance(raw, (list, tuple)) and not isinstance(raw, (str, bytes)):
            return [str(item) for item in raw]
        return []
    if isinstance(raw, Mapping):
        return {str(key): str(text) for key, text in raw.items()}
    return {}


def _blocked_question(qid: Any, spec: Mapping[str, Any]) -> bool:
    if _limit_key(qid) or "flatten" in str(qid).lower():
        return True
    raw = spec.get("criteria")
    keys: list[Any] = []
    chunks = [str(spec.get("instructions") or "")]
    if isinstance(raw, Mapping):
        keys = list(raw.keys())
        chunks.extend(str(key) for key in raw)
        chunks.extend(str(text) for text in raw.values())
    elif isinstance(raw, (list, tuple)) and not isinstance(raw, (str, bytes)):
        keys = list(raw)
        chunks.extend(str(item) for item in raw)
    if any(_limit_key(key) or "flatten" in str(key).lower() for key in keys):
        return True
    blob = "\n".join(chunks)
    if _banned_text(blob):
        return True
    low = blob.lower()
    return "floor" in low or "baseline" in low


def _questions(state: Mapping[str, Any], branch: str) -> dict[str, Any]:
    """This sleeve's subtree, one branch. Noul, Choice, and Score only."""
    try:
        raw = sleeve_subtree_questions(state, standalone=True, branch=branch)
    except Exception:
        return {}
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, Any] = {}
    for qid, spec in raw.items():
        if not isinstance(spec, Mapping):
            continue
        kind = str(spec.get("type") or "").lower()
        if kind not in _QUESTION_TYPES:
            continue
        if _blocked_question(qid, spec):
            continue
        out[str(qid)] = {
            "type": kind,
            "instructions": str(spec.get("instructions") or "").strip(),
            "criteria": _criteria(spec.get("criteria"), kind),
        }
    return out


def _post(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""
    payload = _scrub(dict(state or {}))
    if not isinstance(payload, dict):
        payload = {}
    for key in _ECHO_KEYS:
        payload.pop(key, None)
    payload["model"] = MODEL
    try:
        payload["prior_outcomes"] = prior_outcomes(state=payload, questions=dict(questions))
    except Exception:
        payload["prior_outcomes"] = []
    try:
        from .jev_client import evaluate
    except Exception as exc:
        return {
            "ok": False,
            "error": type(exc).__name__,
            "answers": {},
            "model": MODEL,
            "state": payload,
        }
    try:
        receipt = evaluate(
            payload,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:
        return {
            "ok": False,
            "error": type(exc).__name__,
            "answers": {},
            "model": MODEL,
            "state": payload,
        }
    if not isinstance(receipt, dict):
        return {
            "ok": False,
            "error": "evaluate_not_a_dict",
            "answers": {},
            "model": MODEL,
            "state": payload,
        }
    packed = dict(receipt)
    packed.setdefault("model", MODEL)
    packed["state"] = payload
    if not isinstance(packed.get("answers"), Mapping):
        packed["answers"] = {}
    return packed


def _read(questions: Mapping[str, Any], answers: Mapping[str, Any]) -> dict[str, Any]:
    choices: dict[str, str | None] = {}
    scores: dict[str, float | None] = {}
    nouls: dict[str, bool | float | None] = {}
    unset: dict[str, str] = {}
    for qid, spec in questions.items():
        if not isinstance(spec, Mapping):
            continue
        kind = str(spec.get("type") or "").lower()
        block = _block(answers, qid)
        if kind == "choice":
            criteria = spec.get("criteria") if isinstance(spec.get("criteria"), Mapping) else {}
            order = tuple(str(key) for key in criteria)
            picked = _choice_block(block, order)
            choices[qid] = picked
            if picked is None:
                unset[qid] = _unset_reason(block, order)
        elif kind == "score":
            number = _jev_score(answers, qid)
            scores[qid] = number
            if number is None:
                order = ()
                if isinstance(block, Mapping) and isinstance(block.get("probabilities"), Mapping):
                    order = tuple(str(key) for key in block["probabilities"])
                unset[qid] = _unset_reason(block, order)
        elif kind == "noul":
            value = _jev_noul(answers, qid)
            nouls[qid] = value
            if value is None:
                unset[qid] = "error" if isinstance(block, Mapping) and block.get("error") else "empty"
    return {
        "choices": choices,
        "scores": scores,
        "nouls": nouls,
        "unset": unset,
    }


def _remember(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    read: Mapping[str, Any],
    call_error: str | None,
) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    choices = read.get("choices") if isinstance(read.get("choices"), Mapping) else {}
    scores = read.get("scores") if isinstance(read.get("scores"), Mapping) else {}
    nouls = read.get("nouls") if isinstance(read.get("nouls"), Mapping) else {}
    unset = read.get("unset") if isinstance(read.get("unset"), Mapping) else {}
    for qid, spec in questions.items():
        if not isinstance(spec, Mapping):
            continue
        kind = str(spec.get("type") or "").lower()
        if kind == "score":
            value = scores.get(qid)
        elif kind == "noul":
            value = nouls.get(qid)
        else:
            value = choices.get(qid)
        err = None if value is not None else unset.get(qid) or call_error
        try:
            append_outcome(str(qid), value, logged, error=None if err in (None, "") else str(err))
        except Exception:
            return


def _call_error(receipt: Mapping[str, Any], answers: Mapping[str, Any]) -> str | None:
    if answers:
        return None
    error = receipt.get("error")
    if error in (None, ""):
        error = receipt.get("skipped")
    if error in (None, ""):
        return "empty"
    return str(error)


def _sufficient(nouls: Mapping[str, Any]) -> bool | float | None:
    if "sleeve_state_sufficient" in nouls:
        return nouls.get("sleeve_state_sufficient")
    if "state_sufficient" in nouls:
        return nouls.get("state_sufficient")
    return None


def _anything(read: Mapping[str, Any]) -> bool:
    for key in ("choices", "scores", "nouls"):
        block = read.get(key)
        if isinstance(block, Mapping) and any(value is not None for value in block.values()):
            return True
    return False


def _base(
    state: Mapping[str, Any],
    *,
    branch: str,
    integer_emitted: bool,
    enabled: bool,
    extra: Mapping[str, Any],
) -> dict[str, Any]:
    identity = dict(state.get("identity") or {})
    labels = hierarchical_labels(state, branch=branch)
    facts = integer_facts()
    return {
        "model": MODEL,
        "book": CHALLENGE_LOGIN,
        "overlay": SLEEVE_ENV,
        "overlay_enabled": enabled,
        "labels": labels,
        "family_node": labels.get("family_node"),
        "integer_emitted": bool(integer_emitted),
        "integer_facts": list(facts),
        "converted_if_count": len(converted_ifs()),
        "extra_pass": False,
        "never_linear_keep_drop": True,
        "never_noul_every_sleeve_tick": True,
        "never_second_llm_hop": True,
        "never_dump_exit_on_fire": True,
        "schema_branch": branch,
        "does_not_wrap_admit_and_size": True,
        "does_not_wrap_resolve_exit_profile": True,
        "ac60_cliff_reencoded": False,
        "session_and_vol_separate": True,
        "broker_effect": False,
        "identity_sleeve": identity.get("sleeve"),
        "code_family_node": family_node_for(
            str(identity.get("sleeve") or ""),
            symbol=str(identity.get("symbol") or ""),
            origin=str(identity.get("origin_organism") or ""),
        ),
        **dict(extra),
    }


def _named_scores(scores: Mapping[str, Any]) -> dict[str, Any]:
    return {field: scores.get(qid) for field, qid in _SCORE_FIELDS}


def _decision_row(
    questions: Mapping[str, Any],
    read: Mapping[str, Any],
    *,
    integer_emitted: bool,
    call_error: str | None,
) -> dict[str, Any]:
    choices = read.get("choices") if isinstance(read.get("choices"), Mapping) else {}
    scores = read.get("scores") if isinstance(read.get("scores"), Mapping) else {}
    nouls = read.get("nouls") if isinstance(read.get("nouls"), Mapping) else {}
    include_depth: dict[str, float] = {}
    for qid, number in scores.items():
        if not str(qid).startswith("include_"):
            continue
        passed = include_depth_name(number)
        if passed is None:
            continue
        include_depth[str(qid)[len("include_") :]] = passed
    asked = [str(qid) for qid in questions]
    return {
        "disposition": choices.get("sleeve_disposition"),
        "keep": bool(integer_emitted),
        "size_tilt": scores.get("sleeve_size_depth"),
        "include_depth": include_depth,
        "parameters": dict(scores),
        "choices": dict(choices),
        "nouls": dict(nouls),
        "unset": dict(read.get("unset") or {}),
        "state_sufficient": _sufficient(nouls),
        "sleeve_family_node_choice": choices.get("sleeve_family_node"),
        "sleeve_select": choices.get("sleeve_select"),
        "question_ids": asked,
        "noul_ids_asked": list(noul_question_ids(questions)),
        "error": call_error,
        "missing_jev": call_error is not None,
        "jev_no_decision": not _anything(read),
        **_named_scores(scores),
    }


def compose_sleeve_decision(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    *,
    integer_emitted: bool,
    branch: str = "fire",
    extra: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """One hierarchical post. A miss stays unset. Scores do not drop the emit.

    ``integer_emitted`` is the generator fact. ``answers`` is not a fallback
    and is not read. Floor and baseline are not asked.
    """
    del answers
    state = dict(state or {})
    enabled = overlay_enabled(environ=environ)
    base = _base(
        state,
        branch=branch,
        integer_emitted=integer_emitted,
        enabled=enabled,
        extra=dict(extra or {}),
    )
    blank = _decision_row(
        {},
        {"choices": {}, "scores": {}, "nouls": {}, "unset": {}},
        integer_emitted=integer_emitted,
        call_error=None,
    )
    if not enabled:
        return {
            **base,
            **blank,
            "missing_jev": False,
            "jev_no_decision": False,
            "skipped": f"{SLEEVE_ENV}_off",
        }

    scrubbed = _scrub(state)
    if not isinstance(scrubbed, dict):
        scrubbed = {}
    questions = _questions(scrubbed, branch)
    receipt = _post(scrubbed, questions)
    raw_answers = receipt.get("answers") if isinstance(receipt.get("answers"), Mapping) else {}
    call_error = _call_error(receipt, raw_answers)
    read = _read(questions, raw_answers)
    remembered = receipt.get("state") if isinstance(receipt.get("state"), Mapping) else scrubbed
    _remember(remembered, questions, read, call_error)
    row = _decision_row(questions, read, integer_emitted=integer_emitted, call_error=call_error)
    model = receipt.get("model") or MODEL
    return {
        **base,
        **row,
        "model": model,
        "skipped": None,
    }


def maybe_stamp_generation_meta(
    meta_row: Mapping[str, Any] | None,
    *,
    sleeve: str,
    symbol: str = "",
    integer_emitted: bool,
    answers: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Stamp this state's sleeve return onto a generation meta row.

    Does not change the emit. Does not send.
    """
    row = dict(meta_row or {})
    assembled = dict(state or {})
    identity = dict(assembled.get("identity") or {})
    identity.setdefault("sleeve", sleeve)
    identity.setdefault("symbol", symbol)
    assembled["identity"] = identity
    composed = compose_sleeve_decision(
        assembled,
        answers,
        integer_emitted=integer_emitted,
        environ=environ,
    )
    row["sleeve_jev"] = {
        "labels": composed.get("labels"),
        "disposition": composed.get("disposition"),
        "keep": composed.get("keep"),
        "size_tilt": composed.get("size_tilt"),
        "include_depth": composed.get("include_depth"),
        "parameters": composed.get("parameters"),
        "choices": composed.get("choices"),
        "nouls": composed.get("nouls"),
        "extra_pass": composed.get("extra_pass"),
        "missing_jev": composed.get("missing_jev"),
        "overlay_enabled": composed.get("overlay_enabled"),
    }
    return row
