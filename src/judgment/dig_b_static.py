"""Dig B STATIC_IN_PROVE_CHAIR_LIST consume — Challenge 0.

Each decision on this consume, including each parameter, is the System One
return for that state. One call: ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False``. That call POSTs
https://api.typesafe.ai/v1/systemone. Questions are only Noul, Choice, or
Score. Prior outcomes are attached on the ask, and the return is stored
for the next ask.

An empty answer, a tie, or an error leaves that return unset. It does not
restore a constant. Floor and baseline are not a question. Reason names
are a menu on the state. Membership in that menu is not a verdict.

This module does not send and does not flatten. No news protocol is invented
from this file.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
BOARD = "STATIC_IN_PROVE_CHAIR_LIST"
RECEIPT = "DIG_B_STATIC_APPLY_CONSUME"
LOGIN = 0
NS = "operator"
MAGIC = 0

# Reason ids this consume can ask about. The menu is not the verdict.
HARD_OFF_KEEP_OFF_REASONS = (
    "chair_bleed_hard_off",
    "chair_orb_crypto_hard_off",
    "chair_xa_huge_hard_off",
    "chair_mx_us30_hard_off",
    "chair_g_index_hard_off",
    "chair_hard_off_family",
)

MENU_FILTER_KEEP_REASONS = (
    "soft_relax_house_law",
    "refused_alias_package_b_to_sub_mid_dn_revert",
)

TWO_STOP_KEEP_REASON = "wmb_2stop_day_circuit_same_symbol_sleeve_orig_stops"

APPLY_CANDIDATE_KEEP = HARD_OFF_KEEP_OFF_REASONS + MENU_FILTER_KEEP_REASONS + (TWO_STOP_KEEP_REASON,)

KILL_ENFORCE_REASONS = (
    "jev_sleeve_select_shadow",
    "fluid_inventory_48",
)

_ALL_REASONS = APPLY_CANDIDATE_KEEP + KILL_ENFORCE_REASONS

SCOPED_XAU_CONFLICT_APPLY_UNTOUCHED = (
    "f5_xau_flow_alignment_size_tilt",
    "ca_cross_asset_size_tilt",
    "F5-JEV-004",
)

VERDICT_APPLY_CONSUME = "APPLY_CONSUME"
VERDICT_KILL_ENFORCE = "KILL_ENFORCE"

_VERDICT_ORDER = (VERDICT_APPLY_CONSUME, VERDICT_KILL_ENFORCE)
_VERDICT_CRITERIA = {
    VERDICT_APPLY_CONSUME: "The consume verdict on this state is apply consume.",
    VERDICT_KILL_ENFORCE: "The consume verdict on this state is kill enforce.",
}
_COMPONENT_ORDER = (
    "hard_off",
    "menu_filter",
    "two_stop",
    "sleeve_shadow",
    "fluid_inventory",
    "scoped_xau",
)
_COMPONENT_CRITERIA = {
    "hard_off": "The component on this state is the hard-off family.",
    "menu_filter": "The component on this state is the menu filter.",
    "two_stop": "The component on this state is the two-stop day circuit.",
    "sleeve_shadow": "The component on this state is the sleeve-select shadow.",
    "fluid_inventory": "The component on this state is the fluid inventory.",
    "scoped_xau": "The component on this state is the scoped xau conflict apply.",
}
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)

_VERDICT_ID = "dig_b_verdict"
_PLACE_ID = "dig_b_place"
_NEWS_ID = "dig_b_news_invented"
_FUNDED_ID = "dig_b_redacted_account"
_NEVER_PLACE_ID = "dig_b_never_place"
_NEVER_REMINT_ID = "dig_b_never_remint"
_CLOSE_LOCK_ID = "dig_b_close_lock"
_SCOPED_ID = "dig_b_scoped_untouched"
_PRESENT_ID = "dig_b_present"
_COMPONENT_ID = "dig_b_component"
_APPLY_COUNT_ID = "dig_b_apply_candidate"
_KILL_COUNT_ID = "dig_b_kill_count"
_SHADOW_COUNT_ID = "dig_b_resting_shadow"
_THRESHOLD_ID = "dig_b_threshold"
_LOOP_ID = "dig_b_loop"
_PARAMETER_ID = "dig_b_parameter"

_DECISION_KEYS = frozenset({
    "verdict",
    "place",
    "news_protocol_invented",
    "redacted_account_untouched",
    "never_place",
    "never_remint",
    "never_flatten",
    "scoped_xau_conflict_apply_untouched",
    "apply_candidate",
    "kill",
    "resting_shadow",
    "threshold",
    "loop_bound",
    "parameter",
    "component",
    "present",
    "apply_consume",
    "kill_enforce",
    "rows",
    "probabilities",
})

_LIMIT_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "daily_loss_pct",
    "floor_room",
    "to_pass",
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
_SKIP_PARTS = ("floor", "baseline")

# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []
_DROP = object()


class DigBApplyError(RuntimeError):
    """APPLY entrypoint on a Dig B KILL_ENFORCE surface."""


class HardOffScopedExceptionError(ValueError):
    """Hard-off surface and a scoped exception disagree on the returned state."""


def _row_qid(reason: str) -> str:
    return "dig_b_row_" + str(reason)


def _limit_key(name: str) -> bool:
    token = str(name).strip().lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED_TEXT)


def _scrub_text(value: str) -> str | None:
    if _banned_text(value) or any(part in value.lower() for part in _SKIP_PARTS):
        return None
    return value


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
        cleaned = _scrub_text(value)
        if cleaned is None:
            return _DROP
        return cleaned
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if _banned_text(format(value, ".10g")):
            return _DROP
        return value
    return str(value)


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


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        number = _number(val)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision. A miss is not zero."""

    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if probabilities[name] == best]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
    """The choice is the unique highest probability. A bare label is not a choice."""

    if not isinstance(block, dict) or block.get("error"):
        return None, {}
    probabilities = _probabilities(block)
    kept = {name: probabilities[name] for name in order if name in probabilities}
    local = _unique(kept, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(kept or None, order)
    except Exception:
        picked = local
    if local is None or picked is None or str(picked) != local or str(picked) not in order:
        return None, kept
    return str(picked), kept


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if block is True or block is False:
        return block
    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        value = block.get("noul") if "noul" in block else block.get("Noul")
        if value is None:
            return None
        if value is True or value is False:
            return value
        return _number(value)
    picked, _kept = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The parameter is the returned score. A missing score stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _number(returned_number(block))
    except Exception:
        raw = block.get("score")
        if raw is None:
            raw = block.get("value")
        return _number(raw)


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions) or ""
    cleaned = {
        str(key): str(val)
        for key, val in criteria.items()
        if _scrub_text(str(key)) is not None and _scrub_text(str(val)) is not None
    }
    block: dict[str, Any] = {}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, cleaned)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        block = {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    block["type"] = "choice"
    block["instructions"] = text
    block["criteria"] = cleaned
    return {qid: block}


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
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
            "instructions": _scrub_text(instructions) or "",
            "criteria": {
                "true": _scrub_text(yes) or "",
                "false": _scrub_text(no) or "",
            },
        }
    }


def _questions() -> dict[str, Any]:
    """One pack. Types are noul, choice, or score. The menu does not decide."""

    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        _VERDICT_ID,
        "Which consume verdict is this Dig B state? "
        "The reason id on the state is a fact. "
        "The option with the single highest probability is the verdict. "
        "An empty answer or a tie leaves the verdict unset. "
        "This question does not send.",
        _VERDICT_CRITERIA,
    ))
    for reason in _ALL_REASONS:
        pack.update(_choice_question(
            _row_qid(reason),
            "Which consume verdict is " + reason + " on this Dig B state? "
            "That reason id is a fact. "
            "The option with the single highest probability is the verdict. "
            "An empty answer or a tie leaves the verdict unset. "
            "This question does not send.",
            _VERDICT_CRITERIA,
        ))
    pack.update(_choice_question(
        _COMPONENT_ID,
        "Which component exists on this Dig B state? "
        "The option with the single highest probability is that component. "
        "An empty answer or a tie leaves the component unset. "
        "This question does not send.",
        _COMPONENT_CRITERIA,
    ))
    pack.update(_noul_question(
        _PLACE_ID,
        "Does this Dig B state place? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "This state places.",
        "This state does not place.",
    ))
    pack.update(_noul_question(
        _NEWS_ID,
        "Is a news protocol invented on this Dig B state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "A news protocol is invented on this state.",
        "A news protocol is not invented on this state.",
    ))
    pack.update(_noul_question(
        _FUNDED_ID,
        "Is redacted_account untouched on this Dig B state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "redacted_account is untouched on this state.",
        "redacted_account is touched on this state.",
    ))
    pack.update(_noul_question(
        _NEVER_PLACE_ID,
        "Is the place lock returned for this Dig B state? "
        "The noul you return is that lock. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "The place lock is returned for this state.",
        "The place lock is not returned for this state.",
    ))
    pack.update(_noul_question(
        _NEVER_REMINT_ID,
        "Is the remint lock returned for this Dig B state? "
        "The noul you return is that lock. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "The remint lock is returned for this state.",
        "The remint lock is not returned for this state.",
    ))
    pack.update(_noul_question(
        _CLOSE_LOCK_ID,
        "Is the close lock returned for this Dig B state? "
        "The noul you return is that lock. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "The close lock is returned for this state.",
        "The close lock is not returned for this state.",
    ))
    pack.update(_noul_question(
        _SCOPED_ID,
        "Is the scoped xau conflict apply untouched on this Dig B state? "
        "The wire names on the state are facts. "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "The scoped xau conflict apply is untouched on this state.",
        "The scoped xau conflict apply is touched on this state.",
    ))
    pack.update(_noul_question(
        _PRESENT_ID,
        "Does the component on this Dig B state exist? "
        "The noul you return is that existence. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "The component exists on this state.",
        "The component does not exist on this state.",
    ))
    pack.update(_score_question(
        _APPLY_COUNT_ID,
        "The score you return is the apply-candidate count for this Dig B state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the count unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _KILL_COUNT_ID,
        "The score you return is the kill count for this Dig B state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the count unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _SHADOW_COUNT_ID,
        "The score you return is the resting-shadow count for this Dig B state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the count unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _THRESHOLD_ID,
        "The score you return is the threshold for this Dig B state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the threshold unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _LOOP_ID,
        "The score you return is the loop bound for this Dig B state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the loop bound unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _PARAMETER_ID,
        "The score you return is the parameter for this Dig B state. "
        "It may sit between the levels on this state. "
        "An empty score leaves the parameter unset. "
        "This question does not send.",
    ))
    return pack


def _pack_ok(questions: Mapping[str, Any]) -> bool:
    allowed = {"noul", "choice", "score"}
    if not questions:
        return False
    for qid, block in questions.items():
        if _limit_key(str(qid)):
            return False
        if not isinstance(block, dict) or str(block.get("type") or "") not in allowed:
            return False
        try:
            text = json.dumps(block, default=str).lower()
        except Exception:
            return False
        if any(part in text for part in _SKIP_PARTS) or _banned_text(text):
            return False
    return True


def _state(reason: str | None, facts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    raw = None if reason is None else str(reason).strip()
    body: dict[str, Any] = {
        "model": MODEL,
        "login": LOGIN,
        "ns": NS,
        "magic": MAGIC,
        "board": BOARD,
        "receipt": RECEIPT,
        "reason": raw,
        "reason_ids": list(_ALL_REASONS),
        "scoped_xau_names": list(SCOPED_XAU_CONFLICT_APPLY_UNTOUCHED),
        "identity": {
            "login": LOGIN,
            "ns": NS,
            "magic": MAGIC,
            "board": BOARD,
            "receipt": RECEIPT,
        },
    }
    if isinstance(facts, Mapping):
        for key, item in facts.items():
            name = str(key)
            if name in body or name in _DECISION_KEYS or _limit_key(name) or _banned_text(name):
                continue
            if name == "prior_outcomes":
                continue
            body[name] = item
    cleaned = _scrub(body)
    state = cleaned if isinstance(cleaned, dict) else {}
    state["model"] = MODEL
    state["login"] = LOGIN
    state["ns"] = NS
    state["magic"] = MAGIC
    state["board"] = BOARD
    state["receipt"] = RECEIPT
    return state


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
    state["prior_outcomes"] = [] if loaded is None else loaded


def _pairs(row: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    pairs: list[tuple[str, Any]] = [
        (_VERDICT_ID, row.get("verdict")),
        (_PLACE_ID, row.get("place")),
        (_NEWS_ID, row.get("news_protocol_invented")),
        (_FUNDED_ID, row.get("redacted_account_untouched")),
        (_NEVER_PLACE_ID, row.get("never_place")),
        (_NEVER_REMINT_ID, row.get("never_remint")),
        (_CLOSE_LOCK_ID, row.get("never_flatten")),
        (_SCOPED_ID, row.get("scoped_xau_conflict_apply_untouched")),
        (_PRESENT_ID, row.get("present")),
        (_COMPONENT_ID, row.get("component")),
        (_APPLY_COUNT_ID, row.get("apply_candidate")),
        (_KILL_COUNT_ID, row.get("kill")),
        (_SHADOW_COUNT_ID, row.get("resting_shadow")),
        (_THRESHOLD_ID, row.get("threshold")),
        (_LOOP_ID, row.get("loop_bound")),
        (_PARAMETER_ID, row.get("parameter")),
    ]
    rows = row.get("rows")
    if isinstance(rows, Mapping):
        for reason in _ALL_REASONS:
            pairs.append((_row_qid(reason), rows.get(reason)))
    return tuple(pairs)


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    error = row.get("error")
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value in _pairs(row):
            _LOCAL_OUTCOMES.append({
                "spot": key,
                "value": value,
                "error": None if value is not None else error,
            })
        return
    err = None if error in (None, "") else str(error)
    for key, value in _pairs(row):
        try:
            append_outcome(key, value, logged, error=None if value is not None else err)
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    call = evaluate_fn
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    questions = _anchor_questions(questions, state)
    receipt = call(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    return receipt if isinstance(receipt, dict) else {"error": "evaluate_not_a_dict", "answers": {}}


def _identity(row: dict[str, Any]) -> dict[str, Any]:
    """Board identity and the closed send mark. These are the module, not an answer."""

    row["board"] = BOARD
    row["receipt"] = RECEIPT
    row["login"] = LOGIN
    row["ns"] = NS
    row["magic"] = MAGIC
    row["never_broker_send"] = True
    row["model"] = row.get("model") or MODEL
    return row


def _blank(error: str | None) -> dict[str, Any]:
    return _identity({
        "verdict": None,
        "place": None,
        "news_protocol_invented": None,
        "redacted_account_untouched": None,
        "never_place": None,
        "never_remint": None,
        "never_flatten": None,
        "scoped_xau_conflict_apply_untouched": None,
        "present": None,
        "component": None,
        "apply_candidate": None,
        "kill": None,
        "resting_shadow": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "rows": {name: None for name in _ALL_REASONS},
        "probabilities": {},
        "reason": None,
        "error": error,
        "model": MODEL,
    })


def _read(answers: Mapping[str, Any], error: str | None) -> dict[str, Any]:
    verdict, probabilities = _choice(answers.get(_VERDICT_ID), _VERDICT_ORDER)
    component, _component_probs = _choice(answers.get(_COMPONENT_ID), _COMPONENT_ORDER)
    rows: dict[str, str | None] = {}
    for reason in _ALL_REASONS:
        row_verdict, _row_probs = _choice(answers.get(_row_qid(reason)), _VERDICT_ORDER)
        rows[reason] = row_verdict
    return _identity({
        "verdict": verdict,
        "place": _noul(answers.get(_PLACE_ID)),
        "news_protocol_invented": _noul(answers.get(_NEWS_ID)),
        "redacted_account_untouched": _noul(answers.get(_FUNDED_ID)),
        "never_place": _noul(answers.get(_NEVER_PLACE_ID)),
        "never_remint": _noul(answers.get(_NEVER_REMINT_ID)),
        "never_flatten": _noul(answers.get(_CLOSE_LOCK_ID)),
        "scoped_xau_conflict_apply_untouched": _noul(answers.get(_SCOPED_ID)),
        "present": _noul(answers.get(_PRESENT_ID)),
        "component": component,
        "apply_candidate": _score(answers.get(_APPLY_COUNT_ID)),
        "kill": _score(answers.get(_KILL_COUNT_ID)),
        "resting_shadow": _score(answers.get(_SHADOW_COUNT_ID)),
        "threshold": _score(answers.get(_THRESHOLD_ID)),
        "loop_bound": _score(answers.get(_LOOP_ID)),
        "parameter": _score(answers.get(_PARAMETER_ID)),
        "rows": rows,
        "probabilities": probabilities,
        "error": error,
        "model": MODEL,
    })


def _ask(
    reason: str | None,
    *,
    facts: Mapping[str, Any] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One evaluate for this state. A miss stays unset. This ask does not send."""

    state = _state(reason, facts)
    try:
        questions = _questions()
    except Exception as exc:
        row = _blank(type(exc).__name__)
        row["reason"] = state.get("reason")
        _remember(state, row)
        return row
    if not _pack_ok(questions):
        row = _blank("question_rejected")
        row["reason"] = state.get("reason")
        _remember(state, row)
        return row
    _attach_priors(state, questions)
    try:
        receipt = _post(state, questions, evaluate_fn)
    except Exception as exc:
        row = _blank(type(exc).__name__)
        row["reason"] = state.get("reason")
        _remember(state, row)
        return row
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    if not answers:
        row = _blank(None if error in (None, "") else str(error))
        row["reason"] = state.get("reason")
        if receipt.get("model"):
            row["model"] = receipt.get("model")
        _remember(state, row)
        return row
    row = _read(answers, None if error in (None, "") else str(error))
    row["reason"] = state.get("reason")
    if receipt.get("model"):
        row["model"] = receipt.get("model")
    _remember(state, row)
    return row


def consume_verdict(
    reason: str,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> str | None:
    """Consume verdict for this reason. The unique highest probability, or unset."""

    verdict = _ask(reason, evaluate_fn=evaluate_fn).get("verdict")
    if verdict in _VERDICT_ORDER:
        return str(verdict)
    return None


def static_in_prove_closed(
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One ask for the closed chair list. Counts and row verdicts are that return."""

    card = _ask(None, evaluate_fn=evaluate_fn)
    rows = card.get("rows") if isinstance(card.get("rows"), Mapping) else {}
    apply_rows: dict[str, str] = {}
    kill_rows: dict[str, str] = {}
    for name in _ALL_REASONS:
        verdict = rows.get(name)
        if verdict == VERDICT_APPLY_CONSUME:
            apply_rows[name] = VERDICT_APPLY_CONSUME
        elif verdict == VERDICT_KILL_ENFORCE:
            kill_rows[name] = VERDICT_KILL_ENFORCE
    return {
        "board": BOARD,
        "receipt": RECEIPT,
        "login": LOGIN,
        "ns": NS,
        "magic": MAGIC,
        "verdict": card.get("verdict"),
        "apply_candidate": card.get("apply_candidate"),
        "kill": card.get("kill"),
        "resting_shadow": card.get("resting_shadow"),
        "apply_consume": apply_rows,
        "kill_enforce": kill_rows,
        "scoped_xau_names": list(SCOPED_XAU_CONFLICT_APPLY_UNTOUCHED),
        "scoped_xau_conflict_apply_untouched": card.get("scoped_xau_conflict_apply_untouched"),
        "place": card.get("place"),
        "news_protocol_invented": card.get("news_protocol_invented"),
        "redacted_account_untouched": card.get("redacted_account_untouched"),
        "never_place": card.get("never_place"),
        "never_remint": card.get("never_remint"),
        "never_flatten": card.get("never_flatten"),
        "present": card.get("present"),
        "component": card.get("component"),
        "threshold": card.get("threshold"),
        "loop_bound": card.get("loop_bound"),
        "parameter": card.get("parameter"),
        "never_broker_send": True,
        "model": card.get("model") or MODEL,
        "error": card.get("error"),
    }


def refuse_apply_killed(
    reason: str,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> None:
    """Raise when the returned verdict is KILL_ENFORCE. A miss does not invent one."""

    verdict = consume_verdict(reason, evaluate_fn=evaluate_fn)
    if verdict == VERDICT_KILL_ENFORCE:
        raise DigBApplyError(f"DIG_B_KILL_ENFORCE:{reason}")
    if verdict == VERDICT_APPLY_CONSUME:
        raise ValueError(f"{reason} is not Dig B KILL_ENFORCE")
    return None


def consume_row(
    reason: str,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """One ask for this reason. Caller annotations do not replace the return."""

    card = _ask(reason, evaluate_fn=evaluate_fn)
    row: dict[str, Any] = {
        "reason": reason,
        "verdict": card.get("verdict"),
        "login": LOGIN,
        "ns": NS,
        "magic": MAGIC,
        "board": BOARD,
        "receipt": RECEIPT,
        "place": card.get("place"),
        "news_protocol_invented": card.get("news_protocol_invented"),
        "redacted_account_untouched": card.get("redacted_account_untouched"),
        "never_place": card.get("never_place"),
        "never_remint": card.get("never_remint"),
        "never_flatten": card.get("never_flatten"),
        "apply_candidate": card.get("apply_candidate"),
        "kill": card.get("kill"),
        "resting_shadow": card.get("resting_shadow"),
        "threshold": card.get("threshold"),
        "loop_bound": card.get("loop_bound"),
        "parameter": card.get("parameter"),
        "component": card.get("component"),
        "present": card.get("present"),
        "scoped_xau_conflict_apply_untouched": card.get("scoped_xau_conflict_apply_untouched"),
        "never_broker_send": True,
        "model": card.get("model") or MODEL,
        "error": card.get("error"),
    }
    for key, value in extra.items():
        name = str(key)
        if name in _DECISION_KEYS or name == "never_broker_send" or _limit_key(name):
            continue
        row[name] = value
    return row


def stamp_lock_fields(
    payload: Mapping[str, Any] | None = None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Lock marks are the return for this state. Payload facts do not replace them."""

    facts = dict(payload) if isinstance(payload, Mapping) else {}
    reason = facts.get("reason")
    card = _ask(None if reason is None else str(reason), facts=facts, evaluate_fn=evaluate_fn)
    out: dict[str, Any] = {
        "dig_b_board": BOARD,
        "dig_b_receipt": RECEIPT,
        "never_place": card.get("never_place"),
        "never_remint": card.get("never_remint"),
        "never_flatten": card.get("never_flatten"),
        "news_protocol_invented": card.get("news_protocol_invented"),
        "redacted_account_untouched": card.get("redacted_account_untouched"),
        "never_broker_send": True,
        "model": card.get("model") or MODEL,
        "error": card.get("error"),
    }
    for key, value in facts.items():
        name = str(key)
        if name in out or name in _DECISION_KEYS or _limit_key(name) or _banned_text(name):
            continue
        cleaned = _scrub(value)
        if cleaned is _DROP:
            continue
        out[name] = cleaned
    return out


__all__ = [
    "APPLY_CANDIDATE_KEEP",
    "BOARD",
    "DigBApplyError",
    "HARD_OFF_KEEP_OFF_REASONS",
    "HardOffScopedExceptionError",
    "KILL_ENFORCE_REASONS",
    "LOGIN",
    "MAGIC",
    "MENU_FILTER_KEEP_REASONS",
    "MODEL",
    "NS",
    "RECEIPT",
    "SCOPED_XAU_CONFLICT_APPLY_UNTOUCHED",
    "TWO_STOP_KEEP_REASON",
    "VERDICT_APPLY_CONSUME",
    "VERDICT_KILL_ENFORCE",
    "consume_row",
    "consume_verdict",
    "refuse_apply_killed",
    "stamp_lock_fields",
    "static_in_prove_closed",
]


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
