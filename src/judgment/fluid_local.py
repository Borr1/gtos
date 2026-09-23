"""Fluid decisions for one state.

Every decision in this module, including every parameter, is the System One
return for that state. One hop: ``jev_client.evaluate`` with model
``jev-1.13.0`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``). Questions are only Noul, Choice, or Score. Prior
outcomes are attached on every ask. An empty answer, a tie, a missing score,
or an error leaves that return unset.

Floor and baseline are not a question. This module does not send an order.
"""

from __future__ import annotations

from typing import Any, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.fluid_stamp.v0"

_ASK = (
    "The value you return is the decision for this state. "
    "An empty answer or a tie leaves it unset. "
    "Do not send an order."
)

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

_CHOICES: dict[str, tuple[str, dict[str, str]]] = {
    "flow_stance": (
        "Is this state with the named flow, against it, or is the named flow unclear?",
        {
            "with_flow": "Side agrees with the named flow",
            "against_flow": "Side fights the named flow",
            "no_clear_flow": "Named flow is mixed, flat, or missing",
        },
    ),
    "admit": (
        "Does named tape still support admit, abstain, or hard refuse? "
        "House hard-off and the stop count are not this choice.",
        {
            "admit": "Named tape and geometry still support the fire",
            "abstain": "Named state is thin or mixed",
            "hard_refuse": "Named tape or cost argues against the fire",
        },
    ),
    "family_study_vs_keep": (
        "Is the named family a study row, a house keep, or a house hard-off?",
        {
            "study": "Named family is study",
            "keep": "Named family is house keep",
            "hard_off": "Named family is house hard-off",
        },
    ),
    "last_refusal_class": (
        "If a last refusal is named, what class is it? Do not invent a refusal.",
        {
            "none": "No named last refusal",
            "cost": "The last named refusal was cost",
            "other": "The last named refusal was something else",
        },
    ),
    "close_label": (
        "Name the close that already happened. time_stop stays first-class. "
        "Do not flatten.",
        {
            "orig_stop": "Named exit is the original stop",
            "broker_tp": "Named exit is the broker target",
            "time_stop": "Named exit is a time stop",
            "breach_flatten": "Named exit is an already-closed breach",
            "other": "Named exit is some other class",
        },
    ),
    "warsh_class": (
        "What class is the nearest named high, when one is named?",
        {
            "boe_fomc_nfp_cpi": "Named BOE, FOMC, NFP, CPI, or the same class",
            "other_high": "A named high of another class",
            "none": "No named high on this state",
        },
    ),
    "gold_usd_comove": (
        "Does named gold move with the FX USD proxy, against it, or is that block unassembled?",
        {
            "with_usd": "Named gold moves with the USD proxy",
            "against_usd": "Named gold moves against the USD proxy",
            "no_clear": "The block is mixed or unassembled",
        },
    ),
    "gold_index_comove": (
        "Does named gold move with the index, against it, or is that block unassembled?",
        {
            "with_us30": "Named gold moves with the index",
            "against_us30": "Named gold moves against the index",
            "no_clear": "The block is mixed or unassembled",
        },
    ),
    "risk_on_funding": (
        "Read the named risk-on block only. Unassembled stays unassembled.",
        {
            "risk_on": "Named risk-on",
            "risk_off": "Named risk-off",
            "mixed": "Named mixed or unassembled",
        },
    ),
}

_SCORES: dict[str, tuple[str, tuple[str, ...]]] = {
    "flow_alignment": (
        "How aligned is the named side with named flow?",
        ("fighting named flow", "mixed flow", "aligned with named flow"),
    ),
    "session_fitness": (
        "How well does the named session fit this sleeve?",
        ("dead or wrong hour", "ordinary session", "clean hour for the sleeve"),
    ),
    "geometry_vs_tape": (
        "How well does the named stop fit named volatility?",
        ("stop is tight versus named volatility", "ordinary versus named volatility", "stop fits named volatility"),
    ),
    "level_respect": (
        "Is the fire through a named opposing level, away from levels, or holding a named supporting level?",
        ("through a named opposing level", "no relevant named level", "holding a named supporting level"),
    ),
    "session_size": (
        "What size does the named session support?",
        ("smaller", "ordinary", "larger"),
    ),
    "geo_size": (
        "What size does the named geometry support?",
        ("smaller", "ordinary", "larger"),
    ),
    "level_size": (
        "What size does named level respect support?",
        ("smaller", "ordinary", "larger"),
    ),
    "event_size": (
        "What size does named event proximity support? An empty spine leaves this unset.",
        ("inside the named window", "nearby", "far or unknown"),
    ),
    "ac60_size": (
        "What size does the named persistence reading support?",
        ("fights the named side", "ordinary", "supports the named side"),
    ),
    "combined_size": (
        "How strong is the combined size case on this state? You do not send.",
        ("haircut case", "ordinary", "aligned and cheap"),
    ),
    "cost_vs_tape": (
        "How does the named spread sit versus named volatility?",
        ("spread dominates named volatility", "ordinary", "cheap versus named volatility"),
    ),
    "mfe_shape": (
        "What shape is the named excursion, when one is named?",
        ("no named excursion", "ordinary", "clean runner shape"),
    ),
    "runner_r": (
        "What quality is the named runner? Do not flatten.",
        ("no runner", "ordinary", "clean runner"),
    ),
    "minutes_since_flat": (
        "How does the named time since flat read?",
        ("soon", "ordinary", "clean gap"),
    ),
    "minutes_to_nearest": (
        "How does the named time to the nearest high read? An empty spine leaves this unset.",
        ("inside the named window", "nearby", "far or unknown"),
    ),
    "session_liquidity": (
        "How does named session liquidity read? Do not invent volume.",
        ("thin", "ordinary", "overlap"),
    ),
    "occupancy_world": (
        "How does the named open-cluster count read? This is a label. You do not send.",
        ("empty or unknown", "one cluster", "two or more clusters"),
    ),
}

_NOULS: dict[str, str] = {
    "state_sufficient": "Are the named blocks present enough to judge this state?",
    "cost_hurtful": "Is named cost large enough versus the named stop that the fire is cost-dominated? This is not a refuse.",
    "event_proximity": "Is a named high inside the window this state already carries? An empty spine leaves this unset.",
    "calendar_honest": "Is the named calendar spine consistent with the named host inventory for this as-of?",
    "a8_agrees": "Do the named A8 fields agree with the named pass bit?",
    "veto_corr": "Does a named correlation argue a hold draft? Occupancy keep is not this answer.",
    "veto_event": "Does a named high inside the window argue an event draft?",
    "veto_cost": "Does named cost argue a cost draft? This is not a refuse.",
    "veto_occupancy_label": "Does named occupancy look crowded? The keep-one count is not this answer.",
    "stale_standing": "Is the named standing row stale versus the named as-of?",
    "time_stop_vs_orig": "Does the named time-stop disagree with the named original stop?",
    "hold_too_late": "Does the named hold look late? Do not flatten.",
    "trail_vs_orig": "Does the named trail disagree with the named original stop?",
    "leave_orig_293332188": "Is this the leave-original ticket or an already-open leave-original row?",
    "friday_cutoff_label": "Is the named clock a Friday cutoff?",
    "isolated_reentry": "Do the named occupancy fields say this is an isolated re-entry?",
    "sibling_cooldown": "Is a named sibling cooldown still in force?",
    "spring_reprint": "Does the named sleeve look like a spring reprint?",
    "two_stop_would_be_third": "Would this be a third same-sleeve original stop on the named closes? You are not the counter.",
    "cluster_same_day": "Is a named same-day cluster present?",
    "high_in_f5_window": "Does this state name a high inside the F5 window? An empty spine leaves this unset.",
    "spine_empty_honesty": "Is the named news spine empty? An empty spine is not a claim that no high exists.",
    "past_flag": "Is the nearest named high already past this as-of?",
}

_ALL_IDS: tuple[str, ...] = tuple(_CHOICES) + tuple(_SCORES) + tuple(_NOULS)
_KIND = {
    **{key: "choice" for key in _CHOICES},
    **{key: "score" for key in _SCORES},
    **{key: "noul" for key in _NOULS},
}
_ORDER = {
    **{key: tuple(criteria) for key, (_text, criteria) in _CHOICES.items()},
    **{key: ("true", "false") for key in _NOULS},
}


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    return cleaned


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


def _view(
    state: Mapping[str, Any] | None,
    *,
    extra: Mapping[str, Any] | None = None,
    ticket: Any = None,
) -> dict[str, Any]:
    payload = _scrub(dict(state or {}))
    if extra:
        payload["extra"] = _scrub(dict(extra))
    if ticket is not None:
        payload["ticket"] = ticket
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    return payload


def _text(body: str) -> str:
    return _scrub_text(f"{body.strip()} {_ASK}")


def _choice_question(qid: str, body: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    instructions = _text(body)
    shaped = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): _scrub_text(val) for key, val in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, shaped["criteria"])
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            copied = dict(block)
            copied["type"] = "choice"
            copied["instructions"] = instructions
            copied["criteria"] = shaped["criteria"]
            return {qid: copied}
    except Exception:
        pass
    return {qid: shaped}


def _score_question(qid: str, body: str, criteria: tuple[str, ...] | list[str]) -> dict[str, Any]:
    instructions = _text(body)
    levels = [_scrub_text(item) for item in criteria]
    shaped = {"type": "score", "instructions": instructions, "criteria": levels}
    try:
        from .jev_questions import parameter_question

        built = parameter_question(qid, instructions)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            copied = dict(block)
            copied["type"] = "score"
            copied["instructions"] = instructions
            copied["criteria"] = levels
            return {qid: copied}
    except Exception:
        pass
    return {qid: shaped}


def _noul_question(qid: str, body: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _text(body),
            "criteria": {
                "true": "Yes for this state.",
                "false": "No for this state.",
            },
        }
    }


def _questions(ids: tuple[str, ...]) -> dict[str, Any]:
    """One pack. Types are choice, score, or noul. Floor and baseline are absent."""

    pack: dict[str, Any] = {}
    for qid in ids:
        if _limit_key(qid):
            continue
        kind = _KIND.get(qid)
        if kind == "choice":
            body, criteria = _CHOICES[qid]
            pack.update(_choice_question(qid, body, criteria))
        elif kind == "score":
            body, criteria = _SCORES[qid]
            pack.update(_score_question(qid, body, criteria))
        elif kind == "noul":
            pack.update(_noul_question(qid, _NOULS[qid]))
        else:
            continue
        pack.update(_score_question(
            f"{qid}_parameter",
            f"The parameter for {qid} on this state. The score you return is that parameter. It may sit between the levels.",
            ("none", "trace", "small", "modest", "notable", "heavy"),
        ))
    return pack


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict) or not raw:
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A bare label is not a choice."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    probs = _probs(block)
    if not probs:
        return None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probs, order)
    except Exception:
        return None
    if picked not in order:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A tie is not a Noul."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
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
    """The returned number. It is not snapped to a level."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = None
    return _finite(number)


def _blank(qid: str) -> dict[str, Any]:
    return {
        "type": _KIND.get(qid) or "noul",
        "score": None,
        "noul": None,
        "choice": None,
        "parameter": None,
        "source": "systemone",
        "decidable": False,
    }


def _miss(block: Any, value: Any, order: tuple[str, ...], err: str | None) -> str | None:
    if value is not None:
        return None
    if err:
        return str(err)
    if isinstance(block, dict) and block.get("error"):
        return str(block.get("error"))
    probs = _probs(block)
    if not probs:
        return "empty"
    try:
        from .jev_questions import unique_highest

        if unique_highest(probs, order or tuple(probs)) is None:
            return "tie"
    except Exception:
        return "empty"
    return "empty"


def _logged(block: dict[str, Any]) -> Any:
    kind = block.get("type")
    if kind == "choice":
        return block.get("choice")
    if kind == "noul":
        return block.get("noul")
    return block.get("score")


def _read(qid: str, block: Any, err: str | None) -> dict[str, Any]:
    row = _blank(qid)
    if err is not None:
        return row
    kind = row["type"]
    if kind == "choice":
        row["choice"] = _choice(block, _ORDER.get(qid, ()))
        row["decidable"] = row["choice"] is not None
    elif kind == "noul":
        row["noul"] = _noul(block)
        row["decidable"] = row["noul"] is not None
    else:
        row["score"] = _score(block)
        row["decidable"] = row["score"] is not None
    return row


def _remember(state: Mapping[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    facts = dict(state)
    facts.pop("prior_outcomes", None)
    for spot, value, error in rows:
        try:
            append_outcome(spot, value, facts, error=error)
        except Exception:
            return


def _post(state: dict[str, Any], questions: Mapping[str, Any]) -> tuple[dict[str, Any], str | None]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = dict(state)
    payload.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        payload["prior_outcomes"] = prior_outcomes(state=payload, questions=questions)
    except Exception:
        payload["prior_outcomes"] = []
    payload["model"] = MODEL
    try:
        from .jev_client import evaluate
    except Exception:
        return {}, "import_failed"
    try:
        receipt = evaluate(payload, questions=dict(questions), merge_sleeve=False, model=MODEL)
    except Exception as exc:
        return {}, type(exc).__name__
    if not isinstance(receipt, dict) or not receipt.get("ok"):
        err = None
        if isinstance(receipt, dict):
            err = receipt.get("error") or receipt.get("skipped")
        return {}, str(err or "empty")
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        return {}, "empty"
    return answers, None


def _pack(state: Mapping[str, Any] | None, ids: tuple[str, ...], **view: Any) -> dict[str, dict[str, Any]]:
    payload = _view(state, **view)
    questions = _questions(ids)
    answers, err = _post(payload, questions) if questions else ({}, "empty")
    out: dict[str, dict[str, Any]] = {}
    rows: list[tuple[str, Any, str | None]] = []
    for qid in ids:
        if qid not in _KIND:
            continue
        block = answers.get(qid)
        row = _read(qid, block, err)
        param_block = answers.get(f"{qid}_parameter")
        parameter = None if err is not None else _score(param_block)
        row["parameter"] = parameter
        out[qid] = row
        rows.append((qid, _logged(row), _miss(block, _logged(row), _ORDER.get(qid, ()), err)))
        rows.append((
            f"{qid}_parameter",
            parameter,
            None if parameter is not None else _miss(param_block, None, (), err),
        ))
    _remember(payload, rows)
    return out


def _one(state: Mapping[str, Any] | None, qid: str, **view: Any) -> dict[str, Any]:
    found = _pack(state, (qid,), **view)
    return found.get(qid) or _blank(qid)


def local_flow_stance(state: dict[str, Any]) -> str | None:
    choice = _one(state, "flow_stance").get("choice")
    return choice if isinstance(choice, str) else None


def session_score(state: dict[str, Any]) -> float | None:
    return _finite(_one(state, "session_fitness").get("score"))


def geo_score(state: dict[str, Any]) -> float | None:
    return _finite(_one(state, "geometry_vs_tape").get("score"))


def level_score(state: dict[str, Any]) -> float | None:
    return _finite(_one(state, "level_respect").get("score"))


def event_score(state: dict[str, Any]) -> float | None:
    return _finite(_one(state, "event_size").get("score"))


def minutes_score(state: dict[str, Any]) -> float | None:
    return _finite(_one(state, "minutes_to_nearest").get("score"))


def warsh_class(state: dict[str, Any]) -> str | None:
    choice = _one(state, "warsh_class").get("choice")
    return choice if isinstance(choice, str) else None


def close_label(*, kind: str | None = None, close_reason: Any = None, exit_class: Any = None) -> str | None:
    choice = _one(
        {"kind": kind, "close_reason": close_reason, "exit_class": exit_class},
        "close_label",
    ).get("choice")
    return choice if isinstance(choice, str) else None


def family_choice(state: dict[str, Any]) -> str | None:
    choice = _one(state, "family_study_vs_keep").get("choice")
    return choice if isinstance(choice, str) else None


def admit_choice(
    state: dict[str, Any],
    *,
    flow: str | None = None,
    spread_r: float | None = None,
) -> str | None:
    payload = dict(state or {})
    named = dict(payload.get("named") or {}) if isinstance(payload.get("named"), dict) else {}
    if flow is not None:
        named["flow"] = flow
    if spread_r is not None:
        named["spread_r"] = spread_r
    if named:
        payload["named"] = named
    choice = _one(payload, "admit").get("choice")
    return choice if isinstance(choice, str) else None


def cost_vs_tape_score(state: dict[str, Any]) -> float | None:
    return _finite(_one(state, "cost_vs_tape").get("score"))


def stale_standing(*, extra: dict[str, Any] | None = None) -> bool | float | None:
    noul = _one({}, "stale_standing", extra=extra or {}).get("noul")
    if noul is True or noul is False:
        return noul
    return _finite(noul)


def local_answers(
    state: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
    ticket: Any = None,
) -> dict[str, Any]:
    """One ask for every fluid decision. A miss stays unset."""

    return _pack(state, _ALL_IDS, extra=extra, ticket=ticket)


def _overlay(local: dict[str, Any], answers: Mapping[str, Any] | None) -> None:
    """A caller block with a real return replaces that spot. An empty block does not."""

    if not isinstance(answers, Mapping):
        return
    for key, block in answers.items():
        if key not in local or not isinstance(block, dict):
            continue
        merged = dict(local[key])
        changed = False
        if "score" in block and block.get("score") is not None and _finite(block.get("score")) is not None:
            merged["score"] = _finite(block.get("score"))
            changed = True
        if "noul" in block and block.get("noul") is not None:
            raw = block.get("noul")
            if raw is True or raw is False or _finite(raw) is not None:
                merged["noul"] = raw if raw is True or raw is False else _finite(raw)
                changed = True
        if block.get("choice") not in (None, ""):
            merged["choice"] = block.get("choice")
            changed = True
        if "parameter" in block and _finite(block.get("parameter")) is not None:
            merged["parameter"] = _finite(block.get("parameter"))
            changed = True
        if not changed:
            continue
        kind = merged.get("type")
        if kind == "noul":
            merged["decidable"] = merged.get("noul") is not None
        elif kind == "choice":
            merged["decidable"] = merged.get("choice") not in (None, "")
        else:
            merged["decidable"] = merged.get("score") is not None
        merged["source"] = "jev"
        local[key] = merged


def _leave(compose_row: Mapping[str, Any], local: Mapping[str, Any]) -> bool | None:
    noul = (local.get("leave_orig_293332188") or {}).get("noul") if isinstance(local.get("leave_orig_293332188"), dict) else None
    if noul is True or noul is False:
        return noul
    raw = compose_row.get("leave_orig")
    if raw is True or raw is False:
        return raw
    return None


def _shadow(ans: Mapping[str, Any], effect: str) -> Any:
    if effect == "size_tilt":
        return ans.get("parameter")
    kind = ans.get("type")
    if kind == "noul":
        return ans.get("noul")
    if kind == "choice":
        return ans.get("choice")
    return ans.get("score")


def attach_fluid(
    state: dict[str, Any],
    compose_row: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
    ticket: Any = None,
    answers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Stamp each fluid gate from the return. A missing return stays missing.

    This block does not send.
    """

    local = local_answers(state, extra=extra, ticket=ticket)
    _overlay(local, answers)
    leave = _leave(compose_row or {}, local)
    house_block = (compose_row or {}).get("house_block") is True
    aplus_shadow = (compose_row or {}).get("aplus_shadow_only") is True
    rows: list[Any] = []
    eligible = None
    try:
        from .fluid_gates import auto_apply_eligible, fluid_gates

        rows = list(fluid_gates() or [])
        eligible = auto_apply_eligible
    except Exception:
        rows = []
        eligible = None
    out: dict[str, Any] = {}
    for gate in rows:
        if not isinstance(gate, dict):
            continue
        gid = str(gate.get("id") or "")
        question = str(gate.get("question") or "")
        ans = local.get(question)
        if not isinstance(ans, dict):
            ans = _blank(question)
        effect = str(gate.get("effect") or "")
        shadow = _shadow(ans, effect)
        status = str(gate.get("status") or "SHADOW")
        can_apply = False
        if eligible is not None:
            try:
                can_apply = bool(eligible(gate))
            except Exception:
                can_apply = False
        apply = (
            status == "APPLIED_NAMED"
            and can_apply
            and leave is False
            and not house_block
            and not aplus_shadow
            and shadow is not None
        )
        live = shadow if effect != "size_tilt" or apply else None
        out[gid] = {
            "question": question,
            "family": gate.get("family"),
            "effect": effect or gate.get("effect"),
            "chair": gate.get("chair"),
            "status": status,
            "decidable": bool(ans.get("decidable")),
            "source": ans.get("source"),
            "shadow": shadow,
            "live": live,
            "parameter": ans.get("parameter"),
            "choice": ans.get("choice"),
            "noul": ans.get("noul"),
            "score": ans.get("score"),
            "apply": apply,
            "moved": shadow is not None,
            "refuse": False,
            "research_only": bool(gate.get("research_only")),
            "cannot_refuse": bool(gate.get("cannot_refuse")),
            "range": gate.get("range"),
        }
        if gid == "F5-JEV-004":
            out[gid]["refuse"] = False
    return {
        "schema": SCHEMA,
        "n": len(out),
        "gates": out,
        "never_place": True,
        "leave_orig": leave,
    }


def instrument_value(stamp: dict[str, Any], gate_id: str) -> dict[str, Any]:
    return ((stamp.get("gates") or {}).get(gate_id)) or {}


def lookup_question(gate_id: str) -> str:
    try:
        from .fluid_gates import lookup

        gate = lookup(gate_id) or {}
    except Exception:
        return ""
    return str(gate.get("question") or "")
