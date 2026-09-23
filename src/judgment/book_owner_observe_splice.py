"""s19 usage-observe splice for book_owner skip-path continues.

A candidate and a ticket each pass watch, observe, admit, place, and every
manage step. The choice, the threshold, the loop bound, the parameter, and
which component exists are the System One return on that ask.

One hop: ``jev_client.evaluate`` with model ``jev-1.13.0``, the same call
``place_choice`` uses (POST https://api.typesafe.ai/v1/systemone). The
return is a Noul, a Choice, or a Score. A Score may sit between levels.
Prior outcomes are attached on every ask. An empty answer, a tie, a missing
score, or an error leaves that return unset.

Challenge writer only. The env gates book_owner checks before import stay.
This module does not send an order, does not import s16, and does not invent
a news protocol.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .a1_log import (
    _env_on,
    a1_enabled,
    intent_gold_state,
    maybe_observe_fluid_at_place,
    maybe_observe_ub_plc_017,
    observe,
)

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.book_owner_observe_splice.v1"

A1_LOG_ENV = "GTOS_JEV_A1_LOG"
ALIVE_SHADOW_ENV = "GTOS_JEV_ALIVE_SHADOW"
OBSERVE_EVERY_ENV = "GTOS_JEV_A1_OBSERVE_EVERY"
OBSERVE_EVERY_ALIAS = "A1_OBSERVE_EVERY"

SUBJECTS = ("candidate", "ticket")
STAGES = ("watch", "observe", "admit", "place")
MANAGE_STEPS = ("leave_orig", "move_sl", "move_tp", "close", "hold")

_NEWS_KEYS = frozenset({"news_protocol", "news_headlines", "news_events"})
_LIMIT_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "daily_loss_pct",
    "floor_room",
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

_NOUL_CRITERIA = {
    "true": "This component exists on this step.",
    "false": "This component does not exist on this step.",
}
_WATCH_CRITERIA = {
    "keep_watching": "Keep this subject on the watch.",
    "watch_done": "This watch step is done.",
}
_OBSERVE_CRITERIA = {
    "record": "Record this subject on the observe step.",
    "pass": "Pass this subject on from the observe step.",
}
_ADMIT_CRITERIA = {
    "admit": "Admit this subject.",
    "stand": "Do not admit this subject.",
}
_PLACE_CRITERIA = {
    "place": "This subject is the order on this step.",
    "stand": "This subject is not the order on this step.",
    "delay": "This step is not the step for this subject.",
}
_MANAGE_CRITERIA = {
    "leave_orig": "Leave the original stop and target on this step.",
    "move_sl": "The stop on this step is the returned parameter.",
    "move_tp": "The target on this step is the returned parameter.",
    "close": "This step closes the subject.",
    "hold": "Hold on this step.",
}
_STAGE_CRITERIA = {
    "watch": _WATCH_CRITERIA,
    "observe": _OBSERVE_CRITERIA,
    "admit": _ADMIT_CRITERIA,
    "place": _PLACE_CRITERIA,
    "manage": _MANAGE_CRITERIA,
}
_COMPONENTS = (
    "component_ub_plc_017",
    "component_fluid_at_place",
    "component_skip_row_observe",
    "component_s16",
)


def observe_every_on() -> bool:
    return _env_on(OBSERVE_EVERY_ENV, OBSERVE_EVERY_ALIAS)


def usage_observe_on() -> bool:
    """OR of A1_LOG / ALIVE_SHADOW / A1_OBSERVE_EVERY. Default off."""

    return a1_enabled() or observe_every_on()


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)):
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


def _field(obj: Any, *names: str) -> Any:
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            found = obj.get(name)
            if found is not None:
                return found
        elif obj is not None and hasattr(obj, name):
            found = getattr(obj, name)
            if found is not None:
                return found
    return None


def _challenge_login() -> Any:
    try:
        from .challenge import CHALLENGE_LOGIN
    except Exception:
        return None
    return CHALLENGE_LOGIN


def _bound_clip(items: list[Any], bound: Any) -> list[Any]:
    """Keep items while the index sits under the returned bound.

    A missing bound does not cut the list down to a stand-in width.
    """

    number = _finite(bound)
    if number is None:
        return list(items)
    kept: list[Any] = []
    index = 0
    for item in items:
        if index >= number:
            break
        kept.append(item)
        index += 1
    return kept


def _plain(item: Any) -> Any:
    if isinstance(item, str):
        return _scrub_text(item)
    if item is None or isinstance(item, (bool, int, float)):
        return item
    return _scrub_text(str(item))


def _sanitize_skip(row: Any, bound: Any) -> dict[str, Any]:
    """Copy a skip row for the ask. Drop news-protocol keys. No invent."""

    if not isinstance(row, Mapping):
        if row is None:
            return {}
        return {"reason": _scrub_text(str(row))}
    out: dict[str, Any] = {}
    for key, value in row.items():
        name = str(key)
        if name.lower() in _NEWS_KEYS or _limit_key(name):
            continue
        if isinstance(value, str):
            out[name] = _scrub_text(value)
        elif value is None or isinstance(value, (bool, int, float)):
            out[name] = value
        elif isinstance(value, (list, tuple)):
            out[name] = [_plain(item) for item in _bound_clip(list(value), bound)]
        else:
            out[name] = _scrub_text(str(value))
    return out


def _choice_body(qid: str, text: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _scrub_text(text)
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(criteria))
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict) and block.get("type") == "choice":
            return built
    except Exception:
        pass
    return {
        qid: {
            "type": "choice",
            "instructions": instructions,
            "criteria": dict(criteria),
        }
    }


def _score_body(qid: str, text: str) -> dict[str, Any]:
    instructions = _scrub_text(text)
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict) and block.get("type") == "score":
            return built
    except Exception:
        pass
    return {qid: {"type": "score", "instructions": instructions}}


def _noul_body(qid: str, text: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(text),
            "criteria": dict(_NOUL_CRITERIA),
        }
    }


def _step_questions(qid: str, subject: str, stage: str, step: str | None) -> dict[str, Any]:
    where = f"{subject} {stage}" if step is None else f"{subject} manage {step}"
    criteria = _STAGE_CRITERIA["manage" if step else stage]
    choice = (
        f"This {where}. Pick one option. The unique highest probability is the decision. "
        "An empty answer or a tie leaves the choice unset. "
        "This ask does not transmit an order. A dollar line is not a limit."
    )
    threshold = (
        f"What threshold belongs on this {where}? "
        "The score you return is that threshold. It may sit between levels. "
        "An empty score leaves the threshold unset. A dollar line is not a limit."
    )
    loop = (
        f"How far does this {where} read? "
        "The score you return is that bound. It may sit between levels. "
        "An empty score leaves the bound unset. A dollar line is not a limit."
    )
    parameter = (
        f"What parameter belongs on this {where}? "
        "The score you return is that parameter. It may sit between levels. "
        "An empty score leaves the parameter unset. A dollar line is not a limit."
    )
    component = (
        f"Does the {where} component exist? "
        "Return a noul. Only an actual bool says whether it exists. "
        "An empty answer leaves the component unset. A dollar line is not a limit."
    )
    pack: dict[str, Any] = {}
    pack.update(_noul_body(qid + "_component", component))
    pack.update(_choice_body(qid, choice, criteria))
    pack.update(_score_body(qid + "_threshold", threshold))
    pack.update(_score_body(qid + "_loop", loop))
    pack.update(_score_body(qid + "_parameter", parameter))
    return pack


def _component_questions() -> dict[str, Any]:
    text = {
        "component_ub_plc_017": "Does the UB-PLC-017 observe component exist on this continue?",
        "component_fluid_at_place": "Does the fluid observe component exist on this continue?",
        "component_skip_row_observe": "Does the skip-row observe component exist on this continue?",
        "component_s16": (
            "Does the s16 component exist on this continue? "
            "This ask does not import it."
        ),
    }
    pack: dict[str, Any] = {}
    for qid, line in text.items():
        pack.update(_noul_body(
            qid,
            line + " Return a noul. Only an actual bool says whether it exists. "
            "An empty answer leaves the component unset. A dollar line is not a limit.",
        ))
    return pack


def _loop_question() -> dict[str, Any]:
    return _score_body(
        "skip_row_loop",
        "How many items of each list on this skip row stay on the ask? "
        "The score you return is that bound. It may sit between levels. "
        "An empty score leaves the bound unset. A dollar line is not a limit.",
    )


def _local_unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    for name in order:
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
    if not numeric:
        return None
    picked: Any = None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(numeric), order)
    except Exception:
        picked = _local_unique(numeric, order)
    if picked is None or str(picked) not in order:
        return None
    return str(picked)


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    allowed = set(order)
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


def _score(block: Any) -> float | None:
    if not isinstance(block, dict):
        return None
    number: Any = None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = None
    parsed = _finite(number)
    if parsed is not None:
        return parsed
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _finite(raw)


def _noul(block: Any) -> bool | float | None:
    if not isinstance(block, dict) or "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _blank(order: tuple[str, ...]) -> dict[str, Any]:
    return {
        "choice": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "component_exists": None,
        "probabilities": {},
        "options": list(order),
        "decision_emitted": False,
        "error": None,
    }


def _remember(state: dict[str, Any], qid: str, value: Any, error: str | None) -> None:
    try:
        from .jev_questions import append_outcome

        append_outcome(qid, value, state, error=error)
    except Exception:
        return


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        return


def _post(state: dict[str, Any], questions: Mapping[str, Any]) -> tuple[dict[str, Any], str | None]:
    """One System One evaluate. Empty and error leave the answers unset."""

    _attach_priors(state, questions)
    state["model"] = MODEL
    try:
        from .jev_client import evaluate
    except Exception:
        return {}, "import_failed"
    try:
        receipt = evaluate(
            state,
            questions=dict(questions),
            merge_sleeve=False,
        ) or {}
    except Exception as exc:
        return {}, type(exc).__name__
    if not isinstance(receipt, dict):
        return {}, "evaluate_not_a_dict"
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        err = receipt.get("error") or receipt.get("skipped") or "empty"
        return {}, str(err)
    return answers, None


def _read_step(
    state: dict[str, Any],
    qid: str,
    order: tuple[str, ...],
    *,
    subject: str,
    stage: str,
    step: str | None,
) -> dict[str, Any]:
    row = _blank(order)
    questions = _step_questions(qid, subject, stage, step)
    answers, error = _post(state, questions)
    row["error"] = error
    if error is None:
        probs = _probabilities(answers.get(qid), order)
        choice = _unique(probs, order)
        threshold = _score(answers.get(qid + "_threshold"))
        loop_bound = _score(answers.get(qid + "_loop"))
        parameter = _score(answers.get(qid + "_parameter"))
        component = _noul(answers.get(qid + "_component"))
        row["probabilities"] = probs
        row["choice"] = choice
        row["threshold"] = threshold
        row["loop_bound"] = loop_bound
        row["parameter"] = parameter
        row["component_exists"] = component
        row["decision_emitted"] = choice is not None
    pairs = (
        (qid, row["choice"], "tie_or_empty" if row["choice"] is None else None),
        (qid + "_threshold", row["threshold"], "score_missing" if row["threshold"] is None else None),
        (qid + "_loop", row["loop_bound"], "score_missing" if row["loop_bound"] is None else None),
        (qid + "_parameter", row["parameter"], "score_missing" if row["parameter"] is None else None),
        (
            qid + "_component",
            row["component_exists"],
            "noul_missing" if row["component_exists"] is None else None,
        ),
    )
    for key, value, miss in pairs:
        _remember(state, key, value, error or miss)
    return row


def _read_components(state: dict[str, Any]) -> dict[str, Any]:
    questions = _component_questions()
    answers, error = _post(state, questions)
    found: dict[str, Any] = {}
    for qid in _COMPONENTS:
        value = None if error else _noul(answers.get(qid))
        found[qid] = value
        miss = "noul_missing" if value is None else None
        _remember(state, qid, value, error or miss)
    found["error"] = error
    return found


def _read_loop(state: dict[str, Any]) -> float | None:
    questions = _loop_question()
    answers, error = _post(state, questions)
    value = None if error else _score(answers.get("skip_row_loop"))
    miss = "score_missing" if value is None else None
    _remember(state, "skip_row_loop", value, error or miss)
    return value


def _row_has_list(row: Any) -> bool:
    if not isinstance(row, Mapping):
        return False
    return any(isinstance(value, (list, tuple)) for value in row.values())


def _ticket_id(intent: Any, tick: Any, skipped: Any, occupancy: Any) -> Any:
    for source in (intent, tick, skipped, occupancy):
        found = _field(source, "ticket", "position_ticket", "order_ticket", "ticket_id")
        if found is not None:
            return found
    return None


def _base_state(
    intent: Any,
    tick: Any,
    *,
    cost_skip: str | None,
    skipped_row: Any,
    occupancy: dict[str, Any] | None,
    governor: dict[str, Any] | None,
) -> dict[str, Any]:
    state: dict[str, Any] = {}
    try:
        gold = intent_gold_state(
            intent,
            tick,
            origin="w7_ultimate_book",
            as_of_utc=datetime.now(timezone.utc),
            occupancy=occupancy,
            governor=governor,
        )
        if isinstance(gold, dict):
            state.update(gold)
    except Exception:
        pass
    login = _challenge_login()
    if login is not None:
        state["login"] = login
    for name, value in (
        ("symbol", _field(intent, "symbol", "instrument")),
        ("sleeve", _field(intent, "sleeve", "tag")),
        ("side", _field(intent, "side", "direction")),
        ("candidate_id", _field(intent, "candidate_id")),
    ):
        if value is not None:
            state[name] = value
    ticket = _ticket_id(intent, tick, skipped_row, occupancy)
    if ticket is not None:
        state["ticket"] = ticket
    if cost_skip is not None:
        state["cost_skip"] = _scrub_text(str(cost_skip))
    if occupancy is not None:
        state["occupancy"] = occupancy
    if governor is not None:
        state["governor"] = governor
    state["model"] = MODEL
    return _scrub(state)


def pass_life(
    intent: Any,
    tick: Any = None,
    *,
    cost_skip: str | None = None,
    skipped_row: Mapping[str, Any] | str | None = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ask the life of this candidate and this ticket. Never sends.

    Each subject passes watch, observe, admit, place, and every manage step.
    The returns are the decisions. A miss stays unset.
    """

    state = _base_state(
        intent,
        tick,
        cost_skip=cost_skip,
        skipped_row=skipped_row,
        occupancy=occupancy,
        governor=governor,
    )
    if skipped_row is not None:
        state["skipped_row"] = _sanitize_skip(skipped_row, None)
    loop_bound = _read_loop(state) if _row_has_list(skipped_row) else None
    sanitized = None
    if skipped_row is not None:
        sanitized = _sanitize_skip(skipped_row, loop_bound)
        state["skipped_row"] = sanitized
    components = _read_components(state)
    life: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "skip_row_loop": loop_bound,
        "components": components,
        "candidate": {},
        "ticket": {},
    }
    for subject in SUBJECTS:
        state["subject"] = subject
        passed: dict[str, Any] = {}
        for stage in STAGES:
            qid = f"{subject}_{stage}"
            order = tuple(_STAGE_CRITERIA[stage])
            passed[stage] = _read_step(
                state,
                qid,
                order,
                subject=subject,
                stage=stage,
                step=None,
            )
        manage: dict[str, Any] = {}
        order = tuple(_MANAGE_CRITERIA)
        for step in MANAGE_STEPS:
            qid = f"{subject}_manage_{step}"
            manage[step] = _read_step(
                state,
                qid,
                order,
                subject=subject,
                stage="manage",
                step=step,
            )
        passed["manage"] = manage
        life[subject] = passed
    _invoke_components(
        components,
        intent,
        tick,
        cost_skip=cost_skip,
        skipped_row=skipped_row,
        sanitized=sanitized,
        occupancy=occupancy,
        governor=governor,
        state=state,
    )
    return life


def _component_is_true(components: Mapping[str, Any], qid: str) -> bool:
    """Only an actual bool True says the component exists."""

    return components.get(qid) is True


def _invoke_components(
    components: Mapping[str, Any],
    intent: Any,
    tick: Any,
    *,
    cost_skip: str | None,
    skipped_row: Any,
    sanitized: dict[str, Any] | None,
    occupancy: dict[str, Any] | None,
    governor: dict[str, Any] | None,
    state: Mapping[str, Any],
) -> None:
    """Run an observe component only when its Noul is true. Never sends."""

    try:
        if skipped_row is not None and _component_is_true(components, "component_skip_row_observe"):
            extra: dict[str, Any] = {}
            if sanitized is not None:
                extra["skipped_row"] = sanitized
            if cost_skip is not None:
                extra["cost_skip"] = cost_skip
            observe("UB-PLC-017", dict(state), extra=extra)
            return
        if skipped_row is not None:
            return
        if _component_is_true(components, "component_ub_plc_017"):
            maybe_observe_ub_plc_017(
                intent, tick, cost_skip, occupancy=occupancy, governor=governor
            )
        if _component_is_true(components, "component_fluid_at_place"):
            maybe_observe_fluid_at_place(
                intent, tick, cost_skip, occupancy=occupancy, governor=governor
            )
    except Exception:
        return


def observe_before_continue(
    intent: Any,
    tick: Any = None,
    *,
    cost_skip: str | None = None,
    skipped_row: Mapping[str, Any] | str | None = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Pass the candidate and the ticket through the life when the gate is on.

    The env gate is unchanged. A returned record does not block the continue
    and does not transmit an order. Never raises.
    """

    try:
        if skipped_row is not None:
            if not observe_every_on():
                return None
        elif not usage_observe_on():
            return None
        return pass_life(
            intent,
            tick,
            cost_skip=cost_skip,
            skipped_row=skipped_row,
            occupancy=occupancy,
            governor=governor,
        )
    except Exception:
        return None
