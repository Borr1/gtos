"""Dig A — order / determinism.

Challenge 0 / operator / magic 0. Model jev-1.13.0.
The post is ``jev_client.evaluate`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``).

Every decision on a state, including each parameter, is that return. A
return is a Noul, a Choice, or a Score. A Choice is the unique highest
probability. A Score is the returned number and may sit between levels.
A Noul is a bool or a probability. Prior outcomes are attached on the
ask, and the return is stored for the next ask.

An empty answer, a tie, or an error leaves that field unset. A floor and
a baseline are not a question. This module does not send an order and
does not flatten. Option order is the fixed admit menu. There is no PRNG.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "gtos.judgment.x_dig_order.v0"
STEAL = "DIG_A_ORDER_DETERMINISM"
OVERLAY_ENV = "GTOS_JEV_X_DIG"
MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

# Fixed admit menu. Abstain stays first. This is the option order, not a pick.
ADMIT_OPTION_LOCK: tuple[str, ...] = ("abstain", "admit", "hard_refuse")
PLACE_CRITERIA: tuple[str, ...] = (
    "PLACE",
    "STAND",
    "DELAY",
    "REMINT",
    "FLATTEN_CANDIDATE",
)
INCLUDE_DEPTH = ("hide", "short", "long", "full")
_VERDICT_ORDER = ("APPLY_CANDIDATE", "KILL")
_REASON_ORDER = (
    "operator_flatten_flag_candidate_never_auto",
    "isolated_reentry_is_new_do_not_auto_remint",
    "house_integer_block",
    "missing_jev_no_extra_pass",
    "thin_and_order_sensitive_label",
    "admit_hard_refuse",
    "admit_abstain_default_no_write",
    "admit_choice_writer_prints",
    "unnamed_default_no_write",
)

# Importers still read these names. They stay unset.
# The live flag is the Noul on the ask for that state.
DELAY_IS_PLACE_WALL = None
K3_IS_PLACE_VETO = None
REPLACE_ADMIT_WITH_NOUL = None

_PLACE_TEXT = {
    "PLACE": "This candidate is the order on this bar.",
    "STAND": "This candidate is not the order on this bar.",
    "DELAY": "This bar is not the bar for this candidate.",
    "REMINT": "A re-entry of an existing ticket fits this candidate.",
    "FLATTEN_CANDIDATE": "This candidate is a reduction of open risk.",
}
_ADMIT_TEXT = {
    "abstain": "Neither fire option is selected.",
    "admit": "The candidate is admitted.",
    "hard_refuse": "The candidate is refused.",
}
_VERDICT_TEXT = {
    "APPLY_CANDIDATE": "This recipe is a candidate to apply on this state.",
    "KILL": "This recipe is refused on this state.",
}
_REASON_TEXT = {
    "operator_flatten_flag_candidate_never_auto": "The operator named a flatten candidate.",
    "isolated_reentry_is_new_do_not_auto_remint": "The re-entry is a new named fire.",
    "house_integer_block": "A house integer is on this state.",
    "missing_jev_no_extra_pass": "The Jev answer is missing.",
    "thin_and_order_sensitive_label": "The evidence is thin and the menu is order-sensitive.",
    "admit_hard_refuse": "The admit menu selected hard refuse.",
    "admit_abstain_default_no_write": "The admit menu selected abstain.",
    "admit_choice_writer_prints": "The admit menu selected admit.",
    "unnamed_default_no_write": "Nothing on the menu is named.",
}

_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
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

# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPLAY = (
    REPO_ROOT
    / "judgment"
    / "astra"
    / "lab"
    / "challenge_replay_20260917"
    / "challenge_replay_rows.jsonl"
)



def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED_TEXT)


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _scrub(value: Any) -> Any:
    """Drop floor and baseline keys before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
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


def _local_unique(probs: Mapping[str, Any], order: Sequence[str]) -> str | None:
    """Unique highest. A missing probability is not zero. A tie is not a pick."""

    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    names = tuple(order) if order else tuple(str(name) for name in probs)
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
        if best_p is None or number > best_p:
            best = str(name)
            best_p = number
            tied = False
        elif number == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: Sequence[str]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return None
    menu = tuple(str(name) for name in order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(raw, menu)
    except Exception:
        picked = _local_unique(raw, menu)
    if picked is None or str(picked) not in menu:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The returned score. A tie or an error leaves it unset. It is not snapped."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        pass
    if "score" in block and block.get("score") is not None:
        return _finite(block.get("score"))
    if "value" in block and block.get("value") is not None:
        return _finite(block.get("value"))
    return None


def _pull(block: Any, kind: str, order: Sequence[str] | None) -> Any:
    if kind == "noul":
        return _noul(block)
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block)


def _why(block: Any, value: Any, order: Sequence[str] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = block.get("probabilities") if isinstance(block, Mapping) else None
    menu = tuple(order) if order else (
        tuple(str(name) for name in probs) if isinstance(probs, Mapping) else ()
    )
    if isinstance(probs, Mapping) and probs and _local_unique(probs, menu) is None:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    found: list[float] = []
    for key, value in dict(facts or {}).items():
        if _limit_key(str(key)):
            continue
        number = _finite(value)
        if number is None:
            continue
        if _banned_text(format(number, ".10g")):
            continue
        found.append(number)
    if not found:
        return list(_BETWEEN)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_text(noun: str) -> str:
    return (
        f"Which {noun} fits this state? "
        "The unique highest probability is the decision. "
        "An empty answer or a tie leaves it unset. "
        "A floor and a baseline are not a question. "
        "Do not send an order. Do not flatten."
    )


def _noul_text(noun: str) -> str:
    return (
        f"Is {noun} true on this state? "
        "An empty answer leaves it unset. "
        "A probability, when returned, stays the noul. "
        "A floor and a baseline are not a question. "
        "Do not send an order. Do not flatten."
    )


def _score_text(noun: str) -> str:
    return (
        f"The score you return is the {noun} for this state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "A floor and a baseline are not a question. "
        "Do not send an order. Do not flatten."
    )


def _choice_question(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): _scrub_text(str(value)) for key, value in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(body["criteria"]))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        body.pop(key, None)
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {str(key): _scrub_text(str(value)) for key, value in criteria.items()}
    return {qid: body}


def _score_question(qid: str, text: str, criteria: Sequence[str]) -> dict[str, Any]:
    """A Score for this card. An amount waits for the card. An order keeps its words."""

    words = _ordinal_words(str(qid))
    row = _pending_score(qid, text, words)
    if not isinstance(row, dict):
        return {}
    return {str(qid): row}



def _noul_question(qid: str, text: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(text),
            "criteria": {
                "true": "Yes on this state.",
                "false": "No on this state.",
            },
        }
    }


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state or {}))
    if not isinstance(payload, dict):
        payload = {}
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    payload["login"] = CHALLENGE_LOGIN
    payload["ns"] = CHALLENGE_NS
    payload["magic"] = CHALLENGE_MAGIC
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
        payload["prior_outcomes"] = loaded if loaded is not None else []
    except Exception:
        payload["prior_outcomes"] = [dict(row) for row in _LOCAL_OUTCOMES]
    try:
        from .jev_client import evaluate

        questions = _anchor_questions(questions, payload)
        receipt = evaluate(
            payload,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:
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


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        append_outcome = None
    logged = dict(state or {})
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        if append_outcome is not None:
            try:
                append_outcome(key, value, logged, error=error)
                continue
            except Exception:
                pass
        _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": error})


def _run(
    facts: Mapping[str, Any],
    questions: Mapping[str, Any],
    spec: Sequence[tuple[str, str, str, Sequence[str] | None]],
) -> dict[str, Any]:
    asked = _ask(facts, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out: dict[str, Any] = {}
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in spec:
        block = answers.get(qid)
        value = _pull(block, kind, order)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    _remember(asked.get("state") or {}, rows)
    out["model"] = asked.get("model") or MODEL
    return out


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def canonical_option_order(ids: Sequence[str] | None = None) -> tuple[str, ...]:
    """Lock Choice option order. Unknown ids sort after the admit menu."""

    if not ids:
        return ADMIT_OPTION_LOCK
    seen = {str(item) for item in ids}
    locked = tuple(item for item in ADMIT_OPTION_LOCK if item in seen)
    extra = tuple(sorted(seen - set(ADMIT_OPTION_LOCK)))
    return locked + extra


def option_order_hash(ids: Sequence[str] | Mapping[str, Any] | None) -> str:
    if isinstance(ids, Mapping):
        ordered = canonical_option_order(tuple(ids.keys()))
        payload = {"ids": ordered, "probs": {key: ids[key] for key in ordered if key in ids}}
    else:
        ordered = canonical_option_order(ids)
        payload = {"ids": ordered}
    return sha256_obj(payload)


def menu_hash(
    *,
    option_ids: Sequence[str],
    criteria: Mapping[str, Any] | None = None,
    question_ids: Sequence[str] | None = None,
) -> str:
    ordered = canonical_option_order(option_ids)
    return sha256_obj(
        {
            "option_ids": ordered,
            "criteria": criteria or {},
            "question_ids": sorted(str(item) for item in (question_ids or ())),
            "lock": ADMIT_OPTION_LOCK,
        }
    )


def state_hash(state: Mapping[str, Any] | None) -> str:
    return sha256_obj(dict(state or {}))


def derived_confidence(probs: Mapping[str, Any] | None) -> float | None:
    """Scaled (max − 1/n) / (1 − 1/n). A measurement of a map, not a decision."""

    if not probs:
        return None
    vals = []
    for value in probs.values():
        number = _finite(value)
        if number is None:
            return None
        vals.append(number)
    count = len(vals)
    if count < 2:
        return None
    top = max(vals)
    return (top - 1.0 / count) / (1.0 - 1.0 / count)


def order_margin(probs: Mapping[str, Any] | None) -> float | None:
    if not probs:
        return None
    vals = []
    for value in probs.values():
        number = _finite(value)
        if number is None:
            continue
        vals.append(number)
    if len(vals) < 2:
        return None
    vals.sort(reverse=True)
    return vals[0] - vals[1]


def is_order_sensitive(
    probs: Mapping[str, Any] | None,
    *,
    threshold: float | None = None,
) -> bool | None:
    """Margin under the returned threshold. A missing threshold stays unset."""

    margin = order_margin(probs)
    cut = _finite(threshold)
    if margin is None or cut is None:
        return None
    return margin < cut


def noul_vs_p_admit(noul: Any, p_admit: Any) -> float | None:
    left = _finite(noul)
    right = _finite(p_admit)
    if left is None or right is None:
        return None
    return abs(left - right)


def _identity() -> dict[str, Any]:
    return {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "model": MODEL,
    }


_OD13_SPEC: tuple[tuple[str, str, str, Sequence[str] | None], ...] = (
    ("choice", "choice", "x_dig_order", PLACE_CRITERIA),
    ("why", "choice", "x_dig_reason", _REASON_ORDER),
    ("admit_choice", "choice", "x_dig_admit", ADMIT_OPTION_LOCK),
    ("order_sensitive", "noul", "x_dig_order_sensitive", None),
    ("ensemble_needed", "noul", "x_dig_ensemble_needed", None),
    ("ensemble_is_place_veto", "noul", "x_dig_ensemble_is_place_veto", None),
    ("delay_is_place_wall", "noul", "x_dig_delay_is_place_wall", None),
    ("replace_admit_with_noul", "noul", "x_dig_replace_admit_with_noul", None),
    ("vendor_conf_untrust", "noul", "x_dig_vendor_conf_untrust", None),
    ("thin_evidence", "noul", "x_dig_thin_evidence", None),
    ("missing_jev", "noul", "x_dig_missing_jev", None),
    ("noul_surface_ok", "noul", "x_dig_surface_ok", None),
    ("policy_c_chair_enforce", "noul", "x_dig_policy_c_chair_enforce", None),
    ("component_exists", "noul", "x_dig_component_exists", None),
    ("order_margin", "score", "x_dig_order_margin", None),
    ("ensemble_k", "score", "x_dig_ensemble_k", None),
    ("persist_weight", "score", "x_dig_persist_weight", None),
    ("vendor_conf", "score", "x_dig_vendor_conf", None),
    ("derived_confidence", "score", "x_dig_derived_confidence", None),
    ("noul_vs_p_admit", "score", "x_dig_noul_gap", None),
    ("threshold", "score", "x_dig_threshold", None),
    ("loop_bound", "score", "x_dig_loop", None),
    ("parameter", "score", "x_dig_parameter", None),
)

_POLICY_SPEC: tuple[tuple[str, str, str, Sequence[str] | None], ...] = (
    ("delay_is_place_wall", "noul", "x_dig_delay_is_place_wall", None),
    ("ensemble_is_place_veto", "noul", "x_dig_ensemble_is_place_veto", None),
    ("replace_admit_with_noul", "noul", "x_dig_replace_admit_with_noul", None),
    ("vendor_conf_untrust", "noul", "x_dig_vendor_conf_untrust", None),
    ("order_sensitive", "noul", "x_dig_order_sensitive", None),
    ("component_exists", "noul", "x_dig_component_exists", None),
    ("threshold", "score", "x_dig_threshold", None),
    ("ensemble_k", "score", "x_dig_ensemble_k", None),
    ("persist_weight", "score", "x_dig_persist_weight", None),
    ("loop_bound", "score", "x_dig_loop", None),
    ("parameter", "score", "x_dig_parameter", None),
    ("recipe_hashes", "choice", "x_dig_recipe_hashes", _VERDICT_ORDER),
    ("recipe_conf", "choice", "x_dig_recipe_conf", _VERDICT_ORDER),
    ("recipe_k3_label", "choice", "x_dig_recipe_k3_label", _VERDICT_ORDER),
    ("recipe_noul_binary", "choice", "x_dig_recipe_noul_binary", _VERDICT_ORDER),
    ("recipe_delay_default", "choice", "x_dig_recipe_delay_default", _VERDICT_ORDER),
    ("recipe_delay_wall", "choice", "x_dig_recipe_delay_wall", _VERDICT_ORDER),
    ("recipe_k3_veto", "choice", "x_dig_recipe_k3_veto", _VERDICT_ORDER),
    ("recipe_noul_replace", "choice", "x_dig_recipe_noul_replace", _VERDICT_ORDER),
)


def _policy_questions(levels: Sequence[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_noul_question("x_dig_delay_is_place_wall", _noul_text("delay a place wall")))
    pack.update(_noul_question("x_dig_ensemble_is_place_veto", _noul_text("the ensemble a place veto")))
    pack.update(_noul_question("x_dig_replace_admit_with_noul", _noul_text("the admit choice replaced by a noul")))
    pack.update(_noul_question("x_dig_vendor_conf_untrust", _noul_text("vendor confidence untrusted")))
    pack.update(_noul_question("x_dig_order_sensitive", _noul_text("this menu order-sensitive")))
    pack.update(_noul_question("x_dig_component_exists", _noul_text("the dig-order component present")))
    pack.update(_score_question("x_dig_threshold", _score_text("order-margin threshold"), levels))
    pack.update(_score_question("x_dig_ensemble_k", _score_text("ensemble reading count"), levels))
    pack.update(_score_question("x_dig_persist_weight", _score_text("persistence weight"), levels))
    pack.update(_score_question("x_dig_loop", _score_text("loop bound"), levels))
    pack.update(_score_question("x_dig_parameter", _score_text("parameter"), levels))
    return pack


def od13_questions(facts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One pack for the order state. Choice, Noul, and Score only."""

    levels = _levels(facts)
    pack = _policy_questions(levels)
    pack.update(_choice_question("x_dig_order", _choice_text("place action"), _PLACE_TEXT))
    pack.update(_choice_question("x_dig_reason", _choice_text("reason"), _REASON_TEXT))
    pack.update(_choice_question("x_dig_admit", _choice_text("admit option"), _ADMIT_TEXT))
    pack.update(_noul_question("x_dig_ensemble_needed", _noul_text("an ensemble reading needed")))
    pack.update(_noul_question("x_dig_thin_evidence", _noul_text("the evidence thin")))
    pack.update(_noul_question("x_dig_missing_jev", _noul_text("the Jev answer missing")))
    pack.update(_noul_question("x_dig_surface_ok", _noul_text("the surface noul firing")))
    pack.update(_noul_question("x_dig_policy_c_chair_enforce", _noul_text("policy C chair enforce on")))
    pack.update(_score_question("x_dig_order_margin", _score_text("order margin"), levels))
    pack.update(_score_question("x_dig_vendor_conf", _score_text("vendor confidence"), levels))
    pack.update(_score_question("x_dig_derived_confidence", _score_text("derived confidence"), levels))
    pack.update(_score_question("x_dig_noul_gap", _score_text("noul gap against p admit"), levels))
    return pack


def prove_questions(facts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Recipe verdicts and parameters for the tape state. No seeded verdict."""

    levels = _levels(facts)
    pack = _policy_questions(levels)
    pack.update(_choice_question("x_dig_recipe_hashes", _choice_text("canonical-order recipe"), _VERDICT_TEXT))
    pack.update(_choice_question("x_dig_recipe_conf", _choice_text("confidence recipe"), _VERDICT_TEXT))
    pack.update(_choice_question("x_dig_recipe_k3_label", _choice_text("ensemble-label recipe"), _VERDICT_TEXT))
    pack.update(_choice_question("x_dig_recipe_noul_binary", _choice_text("binary-noul recipe"), _VERDICT_TEXT))
    pack.update(_choice_question("x_dig_recipe_delay_default", _choice_text("delay-default recipe"), _VERDICT_TEXT))
    pack.update(_choice_question("x_dig_recipe_delay_wall", _choice_text("delay-as-wall recipe"), _VERDICT_TEXT))
    pack.update(_choice_question("x_dig_recipe_k3_veto", _choice_text("ensemble-veto recipe"), _VERDICT_TEXT))
    pack.update(_choice_question("x_dig_recipe_noul_replace", _choice_text("replace-admit recipe"), _VERDICT_TEXT))
    return pack


def _od13_facts(
    *,
    answers: Mapping[str, Any] | None,
    state: Mapping[str, Any] | None,
    house_block: bool,
    remint_of: Any,
    flatten_flag: bool,
    vendor_conf: float | None,
    ensemble_needed: bool | None,
    jev_present: bool | None,
) -> dict[str, Any]:
    blob = dict(answers or {})
    admit = blob.get("admit") if isinstance(blob.get("admit"), Mapping) else {}
    probs = admit.get("probabilities") if isinstance(admit.get("probabilities"), Mapping) else {}
    surface = blob.get("surface_ok") if isinstance(blob.get("surface_ok"), Mapping) else {}
    facts = _identity()
    facts.update(
        {
            "house_block": house_block,
            "remint_of": remint_of,
            "flatten_flag": bool(flatten_flag),
            "vendor_conf_on_state": _finite(vendor_conf) if vendor_conf is not None else _finite(admit.get("confidence")),
            "ensemble_needed_on_state": ensemble_needed,
            "jev_present": jev_present,
            "admit_label_on_state": admit.get("choice"),
            "measured_order_margin": order_margin(probs),
            "measured_derived_confidence": derived_confidence(probs),
            "measured_noul_gap": noul_vs_p_admit(surface.get("noul"), probs.get("admit") if probs else None),
            "caller_state": dict(state or {}),
        }
    )
    kept_probs: dict[str, float] = {}
    for key, value in probs.items():
        number = _finite(value)
        if number is not None:
            kept_probs[str(key)] = number
    facts["admit_probabilities"] = kept_probs
    return facts


def od13_decide(
    *,
    answers: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    house_block: bool = False,
    remint_of: Any = None,
    flatten_flag: bool = False,
    vendor_conf: float | None = None,
    ensemble_needed: bool | None = None,
    jev_present: bool | None = None,
) -> dict[str, Any]:
    """Place action for this state. The unique highest probability is the action.

    DELAY, STAND, PLACE, REMINT, and FLATTEN_CANDIDATE are the menu. A
    missing answer does not select one of them. This module does not flatten
    and does not send.
    """

    facts = _od13_facts(
        answers=answers,
        state=state,
        house_block=house_block,
        remint_of=remint_of,
        flatten_flag=flatten_flag,
        vendor_conf=vendor_conf,
        ensemble_needed=ensemble_needed,
        jev_present=jev_present,
    )
    decided = _run(facts, od13_questions(facts), _OD13_SPEC)
    probs = facts.get("admit_probabilities") if isinstance(facts.get("admit_probabilities"), Mapping) else {}
    return {
        "schema": SCHEMA,
        "choice": decided.get("choice"),
        "why": decided.get("why"),
        "criteria": list(PLACE_CRITERIA),
        "admit_choice": decided.get("admit_choice"),
        "order_sensitive": decided.get("order_sensitive"),
        "order_margin": decided.get("order_margin"),
        "ensemble_needed": decided.get("ensemble_needed"),
        "ensemble_k": decided.get("ensemble_k"),
        "ensemble_is_place_veto": decided.get("ensemble_is_place_veto"),
        "delay_is_place_wall": decided.get("delay_is_place_wall"),
        "replace_admit_with_noul": decided.get("replace_admit_with_noul"),
        "vendor_conf_untrust": decided.get("vendor_conf_untrust"),
        "vendor_conf": decided.get("vendor_conf"),
        "derived_confidence": decided.get("derived_confidence"),
        "noul_surface_ok": decided.get("noul_surface_ok"),
        "noul_vs_p_admit": decided.get("noul_vs_p_admit"),
        "thin_evidence": decided.get("thin_evidence"),
        "missing_jev": decided.get("missing_jev"),
        "threshold": decided.get("threshold"),
        "loop_bound": decided.get("loop_bound"),
        "parameter": decided.get("parameter"),
        "component_exists": decided.get("component_exists"),
        "option_order_hash": option_order_hash(probs or ADMIT_OPTION_LOCK),
        "menu_hash": menu_hash(option_ids=ADMIT_OPTION_LOCK),
        "state_hash": state_hash(state),
        "persist_weight": decided.get("persist_weight"),
        "never_order_send": True,
        "never_flatten": True,
        "policy_c_chair_enforce": decided.get("policy_c_chair_enforce"),
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "model": decided.get("model") or MODEL,
    }


def persist_weight() -> float | None:
    """Persistence weight for this state. A miss stays unset."""

    facts = _identity()
    questions = _score_question(
        "x_dig_persist_weight",
        _score_text("persistence weight"),
        _levels(facts),
    )
    decided = _run(facts, questions, (("persist_weight", "score", "x_dig_persist_weight", None),))
    weight = decided.get("persist_weight")
    return weight if isinstance(weight, float) else None


def missing_jev(answers: Mapping[str, Any] | None) -> bool | float | None:
    """Whether the Jev answer is missing. A local empty map does not vote."""

    facts = _identity()
    facts["answers"] = dict(answers or {})
    questions = _noul_question("x_dig_missing_jev", _noul_text("the Jev answer missing"))
    decided = _run(facts, questions, (("missing_jev", "noul", "x_dig_missing_jev", None),))
    return decided.get("missing_jev")


def thin_evidence(state: Mapping[str, Any] | None) -> bool | float | None:
    """Whether the evidence is thin. A local read does not vote."""

    facts = _identity()
    facts["caller_state"] = dict(state or {})
    questions = _noul_question("x_dig_thin_evidence", _noul_text("the evidence thin"))
    decided = _run(facts, questions, (("thin_evidence", "noul", "x_dig_thin_evidence", None),))
    return decided.get("thin_evidence")


def load_challenge_replay(path: Path | None = None) -> list[dict[str, Any]]:
    src = path or DEFAULT_REPLAY
    rows: list[dict[str, Any]] = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _seat_probs(row: Mapping[str, Any], seat: str) -> dict[str, Any]:
    block = row.get(seat) or {}
    answers = block.get("answers") if isinstance(block, Mapping) else {}
    admit = answers.get("admit") if isinstance(answers, Mapping) else {}
    probs = admit.get("probabilities") if isinstance(admit, Mapping) else {}
    return dict(probs or {})


def _count_below(margins: Sequence[float | None], cut: float | None) -> int | None:
    if cut is None:
        return None
    total = 0
    for margin in margins:
        if margin is not None and margin < cut:
            total += 1
    return total


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _tape_measurements(tape: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Counts and gaps on the tape. Evidence for the ask, not a verdict."""

    xau = [row for row in tape if (row.get("input") or {}).get("symbol") == "XAUUSD"]
    wins = []
    for row in xau:
        net = _finite((row.get("input") or {}).get("broker_net"))
        if net is not None and net > 0:
            wins.append(row)
    then_margins = [order_margin(_seat_probs(row, "admit_then")) for row in tape]
    now_margins = [order_margin(_seat_probs(row, "admit_now")) for row in tape]
    win_margins = [order_margin(_seat_probs(row, "admit_then")) for row in wins]

    def _gaps(seat: str) -> list[float]:
        out: list[float] = []
        for row in tape:
            answers = (row.get(seat) or {}).get("answers") or {}
            admit = answers.get("admit") or {}
            derived = derived_confidence(admit.get("probabilities") or {})
            api = _finite(admit.get("confidence"))
            if api is not None and derived is not None:
                out.append(abs(api - derived))
        return out

    noul_gaps: list[float] = []
    for row in tape:
        answers = (row.get("admit_then") or {}).get("answers") or {}
        surface = answers.get("surface_ok") or {}
        admit_probs = (answers.get("admit") or {}).get("probabilities") or {}
        gap = noul_vs_p_admit(surface.get("noul"), admit_probs.get("admit"))
        if gap is not None:
            noul_gaps.append(gap)
    then_choices: dict[str, int] = {}
    now_choices: dict[str, int] = {}
    for row in xau:
        then_admit = ((row.get("admit_then") or {}).get("answers") or {}).get("admit") or {}
        now_admit = ((row.get("admit_now") or {}).get("answers") or {}).get("admit") or {}
        then_choice = str(then_admit.get("choice")) if isinstance(then_admit, Mapping) else "None"
        now_choice = str(now_admit.get("choice")) if isinstance(now_admit, Mapping) else "None"
        then_choices[then_choice] = then_choices.get(then_choice, 0) + 1
        now_choices[now_choice] = now_choices.get(now_choice, 0) + 1
    key_orders: set[tuple[str, ...]] = set()
    for row in tape:
        admit = ((row.get("admit_then") or {}).get("answers") or {}).get("admit") or {}
        probs = admit.get("probabilities") or {}
        key_orders.add(tuple(probs.keys()))
    logins = set()
    for row in tape:
        login = (row.get("input") or {}).get("login")
        number = _finite(login)
        if number is not None:
            logins.add(int(number))
    net_terms = []
    for row in xau:
        number = _finite((row.get("input") or {}).get("broker_net"))
        if number is not None:
            net_terms.append(number)
    return {
        "n": len(tape),
        "logins": sorted(logins),
        "xau_n": len(xau),
        "xau_net": round(sum(net_terms), 2) if net_terms else (0.0 if not xau else None),
        "xau_wins": len(wins),
        "winner_tickets": [int((row.get("input") or {}).get("ticket")) for row in wins if (row.get("input") or {}).get("ticket") is not None],
        "winner_exits": [(row.get("input") or {}).get("exit_class") for row in wins],
        "then_margins": then_margins,
        "now_margins": now_margins,
        "win_margins": win_margins,
        "win_rows": wins,
        "then_mean_gap": _mean(_gaps("admit_then")),
        "now_mean_gap": _mean(_gaps("admit_now")),
        "noul_mean_gap": _mean(noul_gaps),
        "xau_admit_then": then_choices,
        "xau_admit_now": now_choices,
        "n_stored_orders": len(key_orders),
    }


def prove_order_on_challenge(
    rows: Iterable[Mapping[str, Any]] | None = None,
    *,
    path: Path | None = None,
) -> dict[str, Any]:
    """Tape measurements plus the System One verdicts for that tape.

    Counts on the rows stay measurements. Recipe verdicts, the threshold,
    the ensemble count, and the persistence weight are the return. A miss
    leaves the verdict unset.
    """

    tape = list(rows) if rows is not None else load_challenge_replay(path)
    measured = _tape_measurements(tape)
    facts = _identity()
    facts.update(
        {
            "n": measured["n"],
            "xau_n": measured["xau_n"],
            "xau_net": measured["xau_net"],
            "xau_wins": measured["xau_wins"],
            "n_stored_orders": measured["n_stored_orders"],
            "then_mean_gap": measured["then_mean_gap"],
            "now_mean_gap": measured["now_mean_gap"],
            "noul_mean_gap": measured["noul_mean_gap"],
        }
    )
    decided = _run(facts, prove_questions(facts), _POLICY_SPEC)
    cut = _finite(decided.get("threshold"))
    then_flip = _count_below(measured["then_margins"], cut)
    now_flip = _count_below(measured["now_margins"], cut)
    count = measured["n"]
    if cut is None:
        wall_tickets = None
        wall_r = None
    else:
        picked = []
        for row, margin in zip(measured["win_rows"], measured["win_margins"]):
            if margin is not None and margin < cut:
                picked.append(row)
        wall_tickets = [
            int((row.get("input") or {}).get("ticket"))
            for row in picked
            if (row.get("input") or {}).get("ticket") is not None
        ]
        r_terms = []
        for row in picked:
            number = _finite((row.get("input") or {}).get("R"))
            if number is not None:
                r_terms.append(number)
        wall_r = round(sum(r_terms), 4) if r_terms else None
    return {
        "schema": SCHEMA,
        "steal": STEAL,
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "model": decided.get("model") or MODEL,
        "n": measured["n"],
        "logins": measured["logins"],
        "xau_n": measured["xau_n"],
        "xau_net": measured["xau_net"],
        "xau_wins": measured["xau_wins"],
        "winner_tickets": measured["winner_tickets"],
        "winner_exits": measured["winner_exits"],
        "admit_then_flip_n": then_flip,
        "admit_then_flip_rate": round(then_flip / count, 4) if then_flip is not None and count else None,
        "admit_now_flip_n": now_flip,
        "xau_admit_then": measured["xau_admit_then"],
        "xau_admit_now": measured["xau_admit_now"],
        "threshold": decided.get("threshold"),
        "ensemble_k": decided.get("ensemble_k"),
        "persist_weight": decided.get("persist_weight"),
        "loop_bound": decided.get("loop_bound"),
        "parameter": decided.get("parameter"),
        "delay_is_place_wall": decided.get("delay_is_place_wall"),
        "ensemble_is_place_veto": decided.get("ensemble_is_place_veto"),
        "replace_admit_with_noul": decided.get("replace_admit_with_noul"),
        "vendor_conf_untrust": decided.get("vendor_conf_untrust"),
        "order_sensitive": decided.get("order_sensitive"),
        "component_exists": decided.get("component_exists"),
        "recipes": {
            "HASHES_CANONICAL_ORDER": {
                "verdict": decided.get("recipe_hashes"),
                "n_stored_orders": measured["n_stored_orders"],
            },
            "CONF_UNTRUST": {
                "verdict": decided.get("recipe_conf"),
                "then_mean_gap": measured["then_mean_gap"],
                "now_mean_gap": measured["now_mean_gap"],
            },
            "K3_ENSEMBLE_LABEL": {
                "verdict": decided.get("recipe_k3_label"),
                "n": then_flip,
                "rate": round(then_flip / count, 4) if then_flip is not None and count else None,
            },
            "NOUL_BINARY_FIRE": {"verdict": decided.get("recipe_noul_binary")},
            "OD13_DELAY_DEFAULT_NO_WRITE": {"verdict": decided.get("recipe_delay_default")},
            "DELAY_AS_PLACE_WALL": {
                "verdict": decided.get("recipe_delay_wall"),
                "tickets": wall_tickets,
                "r": wall_r,
            },
            "K3_AS_PLACE_VETO": {"verdict": decided.get("recipe_k3_veto")},
            "REPLACE_ADMIT_WITH_NOUL": {
                "verdict": decided.get("recipe_noul_replace"),
                "mean_gap": measured["noul_mean_gap"],
            },
        },
        "never_order_send": True,
        "never_flatten": True,
        "never_bounce": True,
        "do_not_remint": decided.get("do_not_remint"),
    }


_BOUND_CARD = None

_SKIP_FACT_KEYS = frozenset({
    "login",
    "magic",
    "model",
    "prior_outcomes",
    "reason_ids",
    "scoped_xau_names",
    "windows",
    "order_send",
    "flatten",
    "namespace",
    "ns",
    "api_url",
    "schema",
    "questions",
    "answers",
    "criteria",
    "instructions",
})
_PRICE_KEYS = frozenset({
    "entry",
    "stop",
    "target",
    "entry_price",
    "stop_loss",
    "take_profit",
    "take_profit_1",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
    "deal_final",
    "event_stop_now",
    "inv_entry",
    "inv_stop",
})
_PRICE_QIDS = frozenset({
    "inv_entry",
    "inv_stop",
    "entry_stop_parameter",
    "entry_target_parameter",
    "host_named_sl",
})
_WEIGHT_QIDS = frozenset({
    "geometry_vs_tape",
    "session_fitness",
    "level_respect",
    "flow_alignment",
    "persistence",
})
_UNIX_QIDS = frozenset({"gfull_start", "gfull_end", "cutoff_unix"})
_COUNT_LISTS = frozenset({
    "events",
    "rows",
    "candidates",
    "peers",
    "sites",
    "stubs",
    "recipe_rows",
    "recipes",
})
_ORDINAL_EXACT = frozenset({
    "wall_pressure",
    "fill_realism",
    "paper_live_parity",
    "protection_still_earns",
    "session_liquidity",
})


def _bind_card(card):
    global _BOUND_CARD
    if isinstance(card, Mapping):
        _BOUND_CARD = card


def _finite_fact(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _ordinal_words(qid):
    name = str(qid)
    if name == "session_liquidity":
        return ("thin liquidity", "ordinary liquidity", "deep liquidity")
    if name == "include_depth" or name.startswith("include_"):
        return ("hide", "short", "long", "full")
    if name in _ORDINAL_EXACT or name.endswith("_quality"):
        return ("poor", "ordinary", "clean")
    return None


def _qid_unit(qid):
    name = str(qid).lower()
    if _ordinal_words(name):
        return ""
    if "minute" in name:
        return "minutes"
    if name.endswith("_sl") or name in _PRICE_QIDS:
        return "price"
    if name.endswith("_s") or "second" in name or "prefer_s" in name:
        return "seconds"
    if "_pct" in name or "percent" in name:
        return "pct"
    if name.endswith("_r") or "spread_r" in name:
        return "r"
    if name in _WEIGHT_QIDS or "weight" in name or "persist" in name:
        return "weight"
    if (
        name.endswith("_mult")
        or name.endswith("_multiple")
        or "multiplier" in name
        or "_tilt" in name
        or name.endswith("_tilt")
    ):
        return "mult"
    if name in _UNIX_QIDS or name.endswith("_unix"):
        return "unix"
    if "dist" in name or name.endswith("_eps") or "epsilon" in name:
        return "distance"
    if name.endswith("_hour") or name == "utc_hour":
        return "hour"
    if "horizon" in name or name.endswith("_days"):
        return "days"
    if name.endswith("_rate"):
        return "rate"
    if name.endswith("_net"):
        return "money"
    if "line" in name:
        return "lines"
    if (
        name.endswith("_n")
        or "_n_" in name
        or name.endswith("_count")
        or "loop" in name
        or name.endswith("_bars")
        or name.endswith("_cap")
        or name.endswith("_k")
        or name.startswith("n_")
        or "nth" in name
        or "candidate" in name
        or "occupancy" in name
        or "corr_window" in name
        or name.endswith("_shadow")
        or "shadow" in name
    ):
        return "count"
    return ""


def _key_unit(key):
    name = str(key).lower()
    if name in _SKIP_FACT_KEYS or name.startswith("_"):
        return ""
    if "minute" in name:
        return "minutes"
    if name.endswith("_sl") or name in _PRICE_KEYS:
        return "price"
    if name.endswith("_seconds") or name.endswith("_s") or "delta_s" in name or "prefer_s" in name:
        return "seconds"
    if "_pct" in name or name.endswith("_percent") or "percent" in name:
        return "pct"
    if name.endswith("_r") or name in {"spread_r", "locked_r"}:
        return "r"
    if "weight" in name or "persist" in name:
        return "weight"
    if (
        name.endswith("_mult")
        or name.endswith("_multiple")
        or "multiplier" in name
        or name.endswith("_tilt")
        or name in {"tilt", "shadow_tilt"}
    ):
        return "mult"
    if name.endswith("_unix") or name in {"gfull_start", "gfull_end", "cutoff_unix"}:
        return "unix"
    if "dist" in name or name.endswith("_eps") or "epsilon" in name:
        return "distance"
    if name.endswith("_hour") or name == "utc_hour":
        return "hour"
    if "horizon" in name or name.endswith("_days"):
        return "days"
    if name.endswith("_rate"):
        return "rate"
    if name.endswith("_net") or name in {"equity", "balance", "profit", "pnl", "open_pnl", "net"}:
        return "money"
    if "line" in name:
        return "lines"
    if (
        name.endswith("_n")
        or "_n_" in name
        or name.endswith("_count")
        or "loop" in name
        or name.endswith("_bars")
        or name.endswith("_cap")
        or name.endswith("_k")
        or name.startswith("n_")
        or name.endswith("_hits")
        or name.endswith("_anchors")
        or "candidate" in name
        or "nth" in name
        or name == "occupancy_world"
    ):
        return "count"
    return ""


def _fact_label(key, used):
    text = "the " + str(key) + " named on this card"
    if text not in used:
        used.add(text)
        return text
    index = 2
    while True:
        alt = "another " + str(key) + " named on this card (" + str(index) + ")"
        if alt not in used:
            used.add(alt)
            return alt
        index += 1


def _walk_facts(value, key, unit, pairs, labels, seen):
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return
        seen.add(ident)
        for child_key, child in value.items():
            if not isinstance(child_key, str) or child_key.lower() in _SKIP_FACT_KEYS:
                continue
            _walk_facts(child, child_key, unit, pairs, labels, seen)
        return
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return
        seen.add(ident)
        if unit == "count" and str(key).lower() in _COUNT_LISTS:
            pairs.append((_fact_label("count of " + str(key), labels), float(len(value))))
        for item in value:
            if isinstance(item, Mapping):
                _walk_facts(item, key, unit, pairs, labels, seen)
        return
    if _key_unit(key) != unit:
        return
    number = _finite_fact(value)
    if number is None:
        return
    pairs.append((_fact_label(key, labels), number))


def _distance_gap(card, pairs, labels):
    left = None
    right = None

    def walk(node, seen):
        nonlocal left, right
        if not isinstance(node, Mapping):
            return
        ident = id(node)
        if ident in seen:
            return
        seen.add(ident)
        if left is None:
            left = _finite_fact(node.get("left"))
        if right is None:
            right = _finite_fact(node.get("right"))
        for child in node.values():
            if isinstance(child, Mapping):
                walk(child, seen)

    if isinstance(card, Mapping):
        walk(card, set())
    if left is None or right is None:
        return
    pairs.append((_fact_label("stop gap", labels), abs(left - right)))


def _anchors_for(unit, card):
    if not unit or not isinstance(card, Mapping):
        return []
    pairs = []
    labels = set()
    if unit == "weight":
        try:
            from .jev_questions import weight_anchors

            for label, number in weight_anchors(card):
                pairs.append((str(label), number))
                labels.add(str(label))
        except Exception:
            pairs = []
            labels = set()
    _walk_facts(card, "", unit, pairs, labels, set())
    if unit == "distance":
        _distance_gap(card, pairs, labels)
    return pairs


def _pending_score(qid, instructions, words=None):
    text = "" if instructions is None else str(instructions)
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            cleaned = scrub(text)
        except Exception:
            return None
        if cleaned is None:
            return None
        if isinstance(cleaned, str):
            text = cleaned
    text = text.strip()
    if not text:
        return None
    for guard_name in ("_limit_key", "_skip_key", "_blocked", "_blocked_text", "_bad_text"):
        guard = globals().get(guard_name)
        if not callable(guard):
            continue
        try:
            if guard(str(qid)) or guard(text):
                return None
        except Exception:
            return None
    row = {"type": "score", "instructions": text}
    if words:
        kept = [str(item).strip() for item in words if str(item).strip()]
        if len(kept) >= 2:
            row["_words"] = kept
    return row


def _anchor_questions(questions, card):
    """Rebuild each Score from this card. Fewer than two levels drops that Score."""

    if not isinstance(questions, Mapping):
        return questions
    _bind_card(card)
    out = {}
    for key, block in questions.items():
        if not isinstance(block, dict) or str(block.get("type") or "") != "score":
            out[key] = block
            continue
        name = str(key)
        words = block.get("_words")
        if not isinstance(words, (list, tuple)):
            words = _ordinal_words(name)
        try:
            if words:
                from .jev_questions import ordinal_question

                built = ordinal_question(name, str(block.get("instructions") or ""), words)
            else:
                from .jev_questions import amount_question

                built = amount_question(
                    name,
                    str(block.get("instructions") or ""),
                    _anchors_for(_qid_unit(name), card),
                )
        except Exception:
            continue
        row = built.get(name) if isinstance(built, dict) else None
        if not isinstance(row, dict) or not row.get("criteria"):
            continue
        if block.get("ignore_if"):
            row = dict(row)
            row["ignore_if"] = block.get("ignore_if")
        out[key] = row
    return out


def _snap_ordinal(block, n_levels):
    try:
        count = int(n_levels)
    except (TypeError, ValueError):
        return None
    if count < 2:
        return None
    try:
        from .jev_questions import ordinal_index

        return ordinal_index(block, count)
    except Exception:
        return None


def _snap_if_ordinal(qid, block, fallback):
    words = _ordinal_words(qid)
    if not words:
        return fallback
    return _snap_ordinal(block, len(words))
