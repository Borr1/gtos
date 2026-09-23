"""X / Grok Dig A+C land. One System One ask for this state.

The post is ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False`` (POST https://api.typesafe.ai/v1/systemone).
Every decision, including every parameter, is that return. Questions are
only a Noul, a Choice, or a Score. A Choice is the unique highest
probability. A Score is the returned number and may sit between levels.
A Noul is a bool or a probability. Prior outcomes are attached on the ask,
and the return is stored for the next ask.

An empty answer, a tie, a missing score, or an error leaves that field
unset and does not restore a printed weight, a verdict, or a pack count.
A floor and a baseline are not questions. This module does not send and
does not flatten. Judge code stays unable to send.

Challenge login **0** / ``operator`` / magic **0**
stay identity facts. ``GTOS_JEV_X_DIG`` still gates the import-time ask.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
SCHEMA = "gtos.judgment.x_dig.v0"
STEAL = "X_DIG_A_C_SCOUT"
OVERLAY_ENV = "GTOS_JEV_X_DIG"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0
_QUESTION_TYPES = frozenset({"noul", "choice", "score"})
_SKIP_KEY_PARTS = ("floor", "baseline")
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
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_TRUTHY_ON = frozenset({"1", "true", "yes", "on"})

PLACE_ORDER = ("PLACE", "STAND", "DELAY", "REMINT", "FLATTEN_CANDIDATE")
VERDICT_ORDER = ("APPLY_CANDIDATE", "KILL")
JUDGE_ORDER = ("ACCEPT_PACK", "REVISE", "PARK")
OD13_ORDER = ("abstain", "admit", "hard_refuse")
AUTOMODE_ORDER = ("tool_risk_gate", "fluid_at_place", "A1_observe")
DEPTH_ORDER = ("hide", "short", "long", "full")
WEIGHT_IDS = (
    "geometry_vs_tape",
    "session_fitness",
    "level_respect",
    "flow_alignment",
    "persistence",
)
RECIPE_CHOICES = (
    ("FANOUT_ONE_POST", "fanout_verdict"),
    ("HARVEST_EMITTER", "harvest_verdict"),
    ("POLICY_C_SHADOW_EVALUATE", "policy_c_shadow_verdict"),
    ("USAGE_ROUTER_LABEL", "usage_router_verdict"),
    ("AUTOMODE", "automode_verdict"),
    ("ABLATION_BEFORE_APPLY", "ablation_verdict"),
    ("POLICY_C_CHAIR_ENFORCE", "policy_c_chair_verdict"),
)
COMPONENT_ORDER = tuple(name for name, _qid in RECIPE_CHOICES)
SCORE_IDS = WEIGHT_IDS + (
    "delay_as_wall_r",
    "admit_then_flip_rate",
    "xau_net",
    "dig_n",
    "xau_n",
    "admit_then_flip_n",
    "spring_ticket",
    "spring_then_conf",
    "pin_window",
    "x_dig_threshold",
    "x_dig_loop",
    "x_dig_parameter",
)
NOUL_IDS = (
    "x_dig_state_sufficient",
    "delay_is_place_wall",
    "k3_is_place_veto",
    "replace_admit_with_noul",
    "do_not_remint",
    "policy_c_chair_enforce",
    "fanout_one_post",
    "harvest_never_news",
    "router_place",
    "x_dig_component_exists",
    "ablation_pass",
    "resting_shadow",
)

PLACE_CRITERIA = {
    "PLACE": "The open unit earns a place label.",
    "STAND": "The open unit earns a stand label.",
    "DELAY": "The open unit earns a delay label.",
    "REMINT": "The open unit earns a remint label.",
    "FLATTEN_CANDIDATE": "The open unit earns a flatten-candidate label and the ticket stays open.",
}
VERDICT_CRITERIA = {
    "APPLY_CANDIDATE": "This recipe is a candidate to apply on this state.",
    "KILL": "This recipe stays off on this state.",
}
JUDGE_CRITERIA = {
    "ACCEPT_PACK": "The pack is the one this state keeps.",
    "REVISE": "The pack needs another pass.",
    "PARK": "The pack stays parked.",
}
OD13_CRITERIA = {
    "abstain": "The order step abstains.",
    "admit": "The order step admits.",
    "hard_refuse": "The order step refuses.",
}
AUTOMODE_CRITERIA = {
    "tool_risk_gate": "The wire names the tool-risk gate.",
    "fluid_at_place": "The wire names fluid at place.",
    "A1_observe": "The wire names A1 observe.",
}
DEPTH_CRITERIA = {
    "hide": "Include depth is hide.",
    "short": "Include depth is short.",
    "long": "Include depth is long.",
    "full": "Include depth is full.",
}

REPO_ROOT = Path(__file__).resolve().parents[2]
WIRE_JSON = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "JEV_X_DIG_PROVE.json"

# History only when jev_questions cannot be imported. A miss stays a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


def _blocked_text(text: str) -> bool:
    low = str(text).lower()
    if any(part in low for part in _SKIP_KEY_PARTS):
        return True
    return any(token in low for token in _BANNED_TEXT)


def _scrub(value: Any, seen: set[int] | None = None) -> Any:
    """Drop floor and baseline facts before the ask. Remaining facts stay facts.

    A repeated container is a cycle. The walk stops there. No depth cap.
    """

    if seen is None:
        seen = set()
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        if _blocked_text(value):
            return None
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if number != number or number in (90000.0, 110000.0):
            return None
        return value
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _blocked_text(name):
                continue
            cleaned = _scrub(item, seen)
            if cleaned is None and item is not None:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        kept = []
        for item in value:
            cleaned = _scrub(item, seen)
            if cleaned is None and item is not None:
                continue
            kept.append(cleaned)
        return kept
    return None


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


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numeric facts already on this state. A score may sit between them."""

    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        if _blocked_text(key):
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
        if number is None or number in (90000.0, 110000.0):
            return
        found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    levels = [format(number, ".10g") for number in sorted(set(found))]
    return list(_BETWEEN) + levels


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
    """A Score for this card. An amount waits for the card. An order keeps its words."""

    words = _ordinal_words(str(qid))
    row = _pending_score(qid, instructions, words)
    if not isinstance(row, dict):
        return {}
    return {str(qid): row}



def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {"true": yes, "false": no},
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
    return "\n".join(parts)


def _question_ok(qid: Any, body: Mapping[str, Any]) -> bool:
    if _blocked_text(str(qid)):
        return False
    kind = str(body.get("type") or "").lower()
    if kind not in _QUESTION_TYPES:
        return False
    if _blocked_text(_question_text(body)):
        return False
    return True


def _sent(instructions: str) -> str:
    return (
        instructions.strip()
        + " The single highest probability is the decision."
        + " An empty answer or a tie leaves it unset."
        + " Do not send."
    )


def dig_questions(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """One pack for this dig state. Noul, Choice, or Score only."""

    facts = _scrub(dict(state or {}))
    if not isinstance(facts, dict):
        facts = {}
    scale = _levels(facts)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "place_action",
        _sent(
            "What action does the open Challenge unit earn? "
            "Friends copy only. The label is the action."
        ),
        PLACE_CRITERIA,
    ))
    for _name, qid in RECIPE_CHOICES:
        pack.update(_choice_question(
            qid,
            _sent(f"Which verdict does `{_name}` earn on this state?"),
            VERDICT_CRITERIA,
        ))
    pack.update(_choice_question(
        "judge_pack",
        _sent("Which judge label does this pack earn on this state?"),
        JUDGE_CRITERIA,
    ))
    pack.update(_choice_question(
        "od13_choice",
        _sent("Which order label does this state earn?"),
        OD13_CRITERIA,
    ))
    pack.update(_choice_question(
        "automode_wire",
        _sent("Which automode wire does this state name?"),
        AUTOMODE_CRITERIA,
    ))
    pack.update(_choice_question(
        "include_depth",
        _sent("How deep is this dig state included?"),
        DEPTH_CRITERIA,
    ))
    pack.update(_choice_question(
        "x_dig_component",
        _sent("Which dig component exists on this state?"),
        {name: f"The {name} component exists on this state." for name in COMPONENT_ORDER},
    ))
    pack.update(_noul_question(
        "x_dig_state_sufficient",
        _sent("Is this dig state complete enough to name?"),
        "The named state is complete enough.",
        "A named piece is missing.",
    ))
    pack.update(_noul_question(
        "delay_is_place_wall",
        _sent("Is delay a place wall on this open unit?"),
        "Delay is a place wall on this unit.",
        "Delay is not a place wall on this unit.",
    ))
    pack.update(_noul_question(
        "k3_is_place_veto",
        _sent("Is K3 a place veto on this state?"),
        "K3 is a place veto on this state.",
        "K3 is not a place veto on this state.",
    ))
    pack.update(_noul_question(
        "replace_admit_with_noul",
        _sent("Does admit on this state become a noul?"),
        "Admit on this state is a noul.",
        "Admit on this state stays a choice.",
    ))
    pack.update(_noul_question(
        "do_not_remint",
        _sent("Does this named ticket stay unminted?"),
        "The named ticket stays unminted.",
        "The named ticket may be minted again.",
    ))
    pack.update(_noul_question(
        "policy_c_chair_enforce",
        _sent("Does Chair enforce of this policy stand on this state?"),
        "Chair enforce stands on this state.",
        "Chair enforce stays off on this state.",
    ))
    pack.update(_noul_question(
        "fanout_one_post",
        _sent("Is this candidate one post?"),
        "This candidate is one post.",
        "This candidate is not one post.",
    ))
    pack.update(_noul_question(
        "harvest_never_news",
        _sent("Does this harvest stay free of an invented news row?"),
        "This harvest has no invented news row.",
        "This harvest carries an invented news row.",
    ))
    pack.update(_noul_question(
        "router_place",
        _sent("Does the usage router place on this state?"),
        "The usage router places on this state.",
        "The usage router does not place on this state.",
    ))
    pack.update(_noul_question(
        "x_dig_component_exists",
        _sent("Does that dig component exist on this state?"),
        "The component exists on this state.",
        "The component does not exist on this state.",
    ))
    pack.update(_noul_question(
        "ablation_pass",
        _sent("Does ablation pass on this state?"),
        "Ablation passes on this state.",
        "Ablation does not pass on this state.",
    ))
    pack.update(_noul_question(
        "resting_shadow",
        _sent("Is a recipe resting as shadow on this state?"),
        "A recipe is resting as shadow.",
        "No recipe is resting as shadow.",
    ))
    score_lines = {
        "geometry_vs_tape": "the geometry weight",
        "session_fitness": "the session weight",
        "level_respect": "the level weight",
        "flow_alignment": "the flow weight",
        "persistence": "the persistence weight",
        "delay_as_wall_r": "the delay-as-wall parameter",
        "admit_then_flip_rate": "the admit-then-flip rate",
        "xau_net": "the symbol net on this card",
        "dig_n": "the pack count",
        "xau_n": "the symbol count on this card",
        "admit_then_flip_n": "the admit-then-flip count",
        "spring_ticket": "the spring ticket parameter",
        "spring_then_conf": "the spring-then-conf parameter",
        "pin_window": "the pin-window parameter",
        "x_dig_threshold": "the threshold",
        "x_dig_loop": "the loop bound",
        "x_dig_parameter": "the parameter",
    }
    for qid in SCORE_IDS:
        label = score_lines[qid]
        pack.update(_score_question(
            qid,
            (
                f"The score you return is {label} on this state. "
                "It may sit between the levels. "
                "An empty score leaves it unset. Do not send."
            ),
            scale,
        ))
    kept: dict[str, Any] = {}
    for qid, spec in pack.items():
        if isinstance(spec, Mapping) and _question_ok(qid, spec):
            kept[str(qid)] = dict(spec)
    return kept


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
    seen = False
    for name in order:
        if name not in probabilities:
            continue
        seen = True
        p = probabilities[name]
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice_of(block: Any, order: tuple[str, ...]) -> str | None:
    if isinstance(block, Mapping) and block.get("error"):
        return None
    probs = _probabilities(block, order)
    if not probs:
        return None
    names = tuple(name for name in order if name in probs)
    local = _local_unique(probs, names)
    agreed = local
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(dict(probs), names)
    except Exception:
        agreed = local
    if agreed is None or local is None or str(agreed) != local:
        return None
    return local


def _tied(block: Any, order: tuple[str, ...]) -> bool:
    probs = _probabilities(block, order)
    if not probs:
        return False
    names = tuple(name for name in order if name in probs)
    return _local_unique(probs, names) is None


def _score_of(block: Any) -> float | None:
    """The returned score. A tie leaves it unset. The number is not snapped."""

    if not isinstance(block, Mapping) or block.get("error"):
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

    if isinstance(block, bool):
        return block
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        raw = block.get("noul") if "noul" in block else block.get("Noul")
        if raw is True or raw is False:
            return raw
        number = _number(raw)
        if number is not None:
            return number
    picked = _choice_of(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _order_of(spec: Mapping[str, Any]) -> tuple[str, ...]:
    criteria = spec.get("criteria")
    if isinstance(criteria, Mapping):
        return tuple(str(key) for key in criteria)
    return ()


def _read(answers: Mapping[str, Any], questions: Mapping[str, Any]) -> tuple[
    dict[str, str | None],
    dict[str, float | None],
    dict[str, bool | float | None],
]:
    choices: dict[str, str | None] = {}
    scores: dict[str, float | None] = {}
    nouls: dict[str, bool | float | None] = {}
    for qid, spec in questions.items():
        if not isinstance(spec, Mapping):
            continue
        block = answers.get(qid) if isinstance(answers, Mapping) else None
        kind = str(spec.get("type") or "")
        if kind == "choice":
            choices[str(qid)] = _choice_of(block, _order_of(spec))
        elif kind == "score":
            scores[str(qid)] = _score_of(block)
        elif kind == "noul":
            nouls[str(qid)] = _noul_of(block)
    return choices, scores, nouls


def _blank_maps(questions: Mapping[str, Any]) -> tuple[
    dict[str, str | None],
    dict[str, float | None],
    dict[str, bool | float | None],
]:
    choices: dict[str, str | None] = {}
    scores: dict[str, float | None] = {}
    nouls: dict[str, bool | float | None] = {}
    for qid, spec in questions.items():
        if not isinstance(spec, Mapping):
            continue
        kind = str(spec.get("type") or "")
        if kind == "choice":
            choices[str(qid)] = None
        elif kind == "score":
            scores[str(qid)] = None
        elif kind == "noul":
            nouls[str(qid)] = None
    return choices, scores, nouls


def _local_priors() -> list[dict[str, Any]]:
    return [dict(item) for item in _LOCAL_OUTCOMES]


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = _local_priors()
        return
    state["prior_outcomes"] = loaded if isinstance(loaded, list) else []


def _remember(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    choices: Mapping[str, Any],
    scores: Mapping[str, Any],
    nouls: Mapping[str, Any],
    error: str | None,
) -> None:
    """The return just asked is history for the next ask. A miss stays a miss."""

    pairs: list[tuple[str, Any]] = []
    for qid, spec in questions.items():
        if not isinstance(spec, Mapping):
            continue
        kind = str(spec.get("type") or "")
        if kind == "choice":
            pairs.append((str(qid), choices.get(qid)))
        elif kind == "score":
            pairs.append((str(qid), scores.get(qid)))
        elif kind == "noul":
            pairs.append((str(qid), nouls.get(qid)))
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value in pairs:
            _LOCAL_OUTCOMES.append({
                "spot": key,
                "value": value,
                "error": None if value is not None else error,
            })
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


def _login_value(state: Mapping[str, Any]) -> Any:
    identity = state.get("identity") if isinstance(state.get("identity"), Mapping) else {}
    for value in (state.get("login"), state.get("book"), identity.get("login")):
        if value is not None and str(value).strip() != "":
            return value
    return None


def _ns_value(state: Mapping[str, Any]) -> Any:
    identity = state.get("identity") if isinstance(state.get("identity"), Mapping) else {}
    for value in (state.get("ns"), state.get("namespace"), identity.get("ns")):
        if value is not None and str(value).strip() != "":
            return value
    return None


def _matches_challenge(value: Any, expected: int) -> bool:
    try:
        return int(value) == expected
    except (TypeError, ValueError):
        return False


def _not_challenge(state: Mapping[str, Any]) -> bool:
    login = _login_value(state)
    ns = _ns_value(state)
    if login is None and ns is None:
        return False
    login_ok = login is None or _matches_challenge(login, CHALLENGE_LOGIN)
    ns_ok = ns is None or str(ns).strip() == CHALLENGE_NS
    return not (login_ok and ns_ok)


def _row(
    *,
    ok: bool,
    error: str | None,
    skipped: Any,
    model: str,
    answers: Mapping[str, Any],
    questions: Mapping[str, Any],
    choices: Mapping[str, Any],
    scores: Mapping[str, Any],
    nouls: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "ok": ok,
        "error": error,
        "skipped": skipped,
        "model": model or MODEL,
        "answers": dict(answers),
        "questions": dict(questions),
        "choices": dict(choices),
        "scores": dict(scores),
        "nouls": dict(nouls),
        "broker_effect": False,
        "never_order_send": True,
        "api_url": API_URL,
    }


def ask_dig(
    state: Mapping[str, Any] | None = None,
    *,
    timeout_s: float | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One evaluate for this state. A miss stays unset and does not raise."""

    raw = dict(state or {})
    questions = dig_questions(raw)
    choices, scores, nouls = _blank_maps(questions)
    if _not_challenge(raw):
        _remember(raw, questions, choices, scores, nouls, "not_challenge")
        return _row(
            ok=False,
            error="not_challenge",
            skipped="not_challenge",
            model=MODEL,
            answers={},
            questions=questions,
            choices=choices,
            scores=scores,
            nouls=nouls,
        )
    payload = _scrub(raw)
    if not isinstance(payload, dict):
        payload = {}
    payload["book"] = CHALLENGE_LOGIN
    payload["login"] = CHALLENGE_LOGIN
    payload["ns"] = CHALLENGE_NS
    payload["namespace"] = CHALLENGE_NS
    payload["magic"] = CHALLENGE_MAGIC
    payload["model"] = MODEL
    payload["schema"] = SCHEMA
    if not questions:
        _remember(payload, questions, choices, scores, nouls, "empty")
        return _row(
            ok=False,
            error="empty",
            skipped="empty",
            model=MODEL,
            answers={},
            questions=questions,
            choices=choices,
            scores=scores,
            nouls=nouls,
        )
    _attach_priors(payload, questions)
    call = ask
    if call is None:
        try:
            from .jev_client import evaluate

            call = evaluate
        except Exception as exc:  # noqa: BLE001 — a failed import must not fill a weight
            _remember(payload, questions, choices, scores, nouls, type(exc).__name__)
            return _row(
                ok=False,
                error=type(exc).__name__,
                skipped=type(exc).__name__,
                model=MODEL,
                answers={},
                questions=questions,
                choices=choices,
                scores=scores,
                nouls=nouls,
            )
    try:
        questions = _anchor_questions(questions, payload)
        receipt = call(
            payload,
            questions=questions,
            merge_sleeve=False,
            model=MODEL,
            timeout_s=timeout_s,
        )
    except Exception as exc:  # noqa: BLE001 — a failed post must not fill a weight
        _remember(payload, questions, choices, scores, nouls, type(exc).__name__)
        return _row(
            ok=False,
            error=type(exc).__name__,
            skipped=type(exc).__name__,
            model=MODEL,
            answers={},
            questions=questions,
            choices=choices,
            scores=scores,
            nouls=nouls,
        )
    if not isinstance(receipt, Mapping):
        _remember(payload, questions, choices, scores, nouls, "empty")
        return _row(
            ok=False,
            error="empty",
            skipped="empty",
            model=MODEL,
            answers={},
            questions=questions,
            choices=choices,
            scores=scores,
            nouls=nouls,
        )
    answers = receipt.get("answers")
    if not isinstance(answers, Mapping):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    error_text = None if error in (None, "") else str(error)
    choices, scores, nouls = _read(answers, questions)
    if error_text is None and choices.get("place_action") is None:
        place_spec = questions.get("place_action")
        if isinstance(place_spec, Mapping) and _tied(answers.get("place_action"), _order_of(place_spec)):
            error_text = "tie"
    _remember(payload, questions, choices, scores, nouls, error_text)
    reported = receipt.get("model")
    return _row(
        ok=receipt.get("ok") is True and bool(answers),
        error=error_text,
        skipped=receipt.get("skipped"),
        model=reported if isinstance(reported, str) and reported.strip() else MODEL,
        answers=answers,
        questions=questions,
        choices=choices,
        scores=scores,
        nouls=nouls,
    )


def _weights(scores: Mapping[str, Any]) -> dict[str, float | None]:
    return {qid: scores.get(qid) if isinstance(scores.get(qid), (int, float)) and not isinstance(scores.get(qid), bool) else None for qid in WEIGHT_IDS}


def pin_persist_zero(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Persistence and the other weights are the scores on this ask."""

    facts = {"seat": "persist"}
    if isinstance(state, Mapping):
        facts.update(dict(state))
    row = ask_dig(facts)
    scores = row["scores"]
    persist = scores.get("persistence")
    return {
        "ok": persist is not None,
        "persist": persist,
        "weights": _weights(scores),
        "pin_window": scores.get("pin_window"),
        "book": CHALLENGE_LOGIN,
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
        "broker_effect": False,
        "never_order_send": True,
    }


def _recipe_board(choices: Mapping[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
    recipes: dict[str, Any] = {}
    apply: list[str] = []
    kill: list[str] = []
    for name, qid in RECIPE_CHOICES:
        verdict = choices.get(qid)
        recipes[name] = {"verdict": verdict}
        if verdict == "APPLY_CANDIDATE":
            apply.append(name)
        elif verdict == "KILL":
            kill.append(name)
    return recipes, apply, kill


def _shadow_list(noul: Any, component: str | None) -> list[str] | None:
    if noul is True and component:
        return [component]
    if noul is False:
        return []
    return None


def prove(
    *,
    path: Path | None = None,
    state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Hist prove for this state. The receipt is the return. A miss stays unset."""

    facts: dict[str, Any] = {"seat": "prove"}
    if path is not None:
        text = str(path)
        if not _blocked_text(text):
            facts["hist_path"] = text
    if isinstance(state, Mapping):
        facts.update(dict(state))
    row = ask_dig(facts)
    scores = row["scores"]
    choices = row["choices"]
    nouls = row["nouls"]
    recipes, apply, kill = _recipe_board(choices)
    component = choices.get("x_dig_component")
    shadow = _shadow_list(nouls.get("resting_shadow"), component if isinstance(component, str) else None)
    return {
        "schema": SCHEMA,
        "steal": STEAL,
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
        "n": scores.get("dig_n"),
        "xau_n": scores.get("xau_n"),
        "xau_net": scores.get("xau_net"),
        "admit_then_flip_n": scores.get("admit_then_flip_n"),
        "admit_then_flip_rate": scores.get("admit_then_flip_rate"),
        "delay_as_wall_r": scores.get("delay_as_wall_r"),
        "spring_ticket": scores.get("spring_ticket"),
        "spring_then_conf": scores.get("spring_then_conf"),
        "do_not_remint": nouls.get("do_not_remint"),
        "persist": scores.get("persistence"),
        "weights": _weights(scores),
        "pin_window": scores.get("pin_window"),
        "option_lock": choices.get("place_action"),
        "automode_wire": choices.get("automode_wire"),
        "policy_c_chair_enforce": nouls.get("policy_c_chair_enforce"),
        "delay_is_place_wall": nouls.get("delay_is_place_wall"),
        "k3_is_place_veto": nouls.get("k3_is_place_veto"),
        "replace_admit_with_noul": nouls.get("replace_admit_with_noul"),
        "include_depth": choices.get("include_depth"),
        "place_action": choices.get("place_action"),
        "judge": choices.get("judge_pack"),
        "od13_choice": choices.get("od13_choice"),
        "component": component,
        "component_exists": nouls.get("x_dig_component_exists"),
        "state_sufficient": nouls.get("x_dig_state_sufficient"),
        "threshold": scores.get("x_dig_threshold"),
        "loop_bound": scores.get("x_dig_loop"),
        "parameter": scores.get("x_dig_parameter"),
        "recipes": recipes,
        "apply_candidate": apply,
        "kill": kill,
        "resting_shadow": shadow,
        "resting_shadow_noul": nouls.get("resting_shadow"),
        "ablation": {
            "pass": nouls.get("ablation_pass"),
            "verdict": choices.get("ablation_verdict"),
            "persist_weight": scores.get("persistence"),
        },
        "board_ok": nouls.get("ablation_pass"),
        "fanout_one_post": nouls.get("fanout_one_post"),
        "harvest_never_news": nouls.get("harvest_never_news"),
        "router_place": nouls.get("router_place"),
        "never_order_send": True,
        "never_flatten": True,
        "never_bounce": True,
        "never_leftover_ship_book_owner": True,
        "never_merge_main": True,
        "broker_effect": False,
    }


def write_prove_json(receipt: Mapping[str, Any] | None = None) -> Path:
    blob = dict(receipt or prove())
    WIRE_JSON.parent.mkdir(parents=True, exist_ok=True)
    WIRE_JSON.write_text(json.dumps(blob, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return WIRE_JSON


def smoke_wires(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Wire labels for this state. Each one is the return. A miss stays unset."""

    facts = {"seat": "smoke"}
    if isinstance(state, Mapping):
        facts.update(dict(state))
    row = ask_dig(facts)
    scores = row["scores"]
    choices = row["choices"]
    nouls = row["nouls"]
    return {
        "fanout_one_post": nouls.get("fanout_one_post"),
        "harvest_never_news": nouls.get("harvest_never_news"),
        "policy_c_enforce": nouls.get("policy_c_chair_enforce"),
        "router_place": nouls.get("router_place"),
        "automode": choices.get("automode_wire"),
        "od13_choice": choices.get("od13_choice"),
        "od13_delay_wall": nouls.get("delay_is_place_wall"),
        "judge": choices.get("judge_pack"),
        "place_action": choices.get("place_action"),
        "persist": scores.get("persistence"),
        "threshold": scores.get("x_dig_threshold"),
        "loop_bound": scores.get("x_dig_loop"),
        "parameter": scores.get("x_dig_parameter"),
        "component": choices.get("x_dig_component"),
        "component_exists": nouls.get("x_dig_component_exists"),
        "schema": SCHEMA,
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
        "broker_effect": False,
        "never_order_send": True,
    }


def _place_facts(state: Mapping[str, Any] | None) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    try:
        from .rung_choice import learning_unit_state

        _root, learned = learning_unit_state("x_dig")
        if isinstance(learned, dict):
            facts.update(learned)
    except Exception:
        pass
    if isinstance(state, Mapping):
        facts.update(dict(state))
    facts["seat"] = "place"
    return facts


def ask_place_action(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Place label for the open unit. The unique highest probability is the label."""

    facts = _place_facts(state)
    row = ask_dig(facts)
    choice = row["choices"].get("place_action")
    block = row["answers"].get("place_action") if isinstance(row.get("answers"), Mapping) else None
    probability = None
    if choice is not None and isinstance(block, Mapping):
        raw = block.get("probabilities")
        if isinstance(raw, Mapping):
            probability = _number(raw.get(choice))
    pair = facts.get("pair") if isinstance(facts.get("pair"), Mapping) else {}
    return {
        "choice": choice,
        "place_action": choice,
        "probability": probability,
        "decision_emitted": choice is not None,
        "delay_is_place_wall": row["nouls"].get("delay_is_place_wall"),
        "do_not_remint": row["nouls"].get("do_not_remint"),
        "persist_weight": row["scores"].get("persistence"),
        "threshold": row["scores"].get("x_dig_threshold"),
        "loop_bound": row["scores"].get("x_dig_loop"),
        "parameter": row["scores"].get("x_dig_parameter"),
        "pair_ticket": pair.get("ticket"),
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
        "ok": choice is not None,
        "broker_effect": False,
        "never_order_send": True,
    }


def _overlay_on() -> bool:
    return os.environ.get(OVERLAY_ENV, "").strip().lower() in _TRUTHY_ON


def _note_load_error(exc: BaseException) -> None:
    try:
        from .rung_choice import note_load_error

        note_load_error("x_dig", exc)
    except Exception:
        return


def _ask_place_action_on_load() -> None:
    if not _overlay_on():
        return
    try:
        row = ask_place_action()
    except Exception as exc:  # noqa: BLE001 — import must not raise or fill a label
        _note_load_error(exc)
        return
    if not row.get("decision_emitted"):
        _note_load_error(RuntimeError(str(row.get("error") or "no_decision")))


_ask_place_action_on_load()


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
