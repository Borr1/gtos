"""Dig C — LangChain / TypeSafe judge unique files.

Challenge 0 / operator / magic 0.

Every decision on this dig state, including each parameter, is the System
One return for that state. One call: ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False``. That call POSTs
https://api.typesafe.ai/v1/systemone. Questions are only Noul, Choice, or
Score. Prior outcomes are attached on the ask, and the return is stored
for the next ask.

An empty answer, a tie, a missing score, or an error leaves that return
unset. It does not restore a constant. Floor and baseline are not a
question. This module does not send an order and does not flatten.

Laws that stay structural: this file cannot send, cannot flatten, does
not vendor, does not invent a news protocol, and does not re-encode
occupancy HOLD. Chair-enforce is not armed by a local switch.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.x_dig_judge.v0"
STEAL = "DIG_C_JEV_JUDGE_HARNESS"
OVERLAY_ENV = "GTOS_JEV_X_DIG"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

STUB_IDS: tuple[str, ...] = (
    "FANOUT_ONE_POST",
    "HARVEST_EMITTER",
    "POLICY_C_SHADOW_EVALUATE",
    "USAGE_ROUTER_LABEL",
    "AUTOMODE",
    "ABLATION_BEFORE_APPLY",
)
JUDGE_PACK = ("ACCEPT_PACK", "REVISE", "PARK")
AUTOMODE_WIRE: tuple[str, ...] = ("tool_risk_gate", "fluid_at_place", "A1_observe")
AUTOMODE_NOT: tuple[str, ...] = ("CONF_GATE",)
# Module mark. The shadow decision is the Noul on that ask.
POLICY_C_CHAIR_ENFORCE = False
NEVER_INVENT_NEWS = True
NEVER_VENDOR = True
NEVER_PLACE = True
OCCUPANCY_HOLD_DEAD = True

_VERDICT_ORDER = ("APPLY_CANDIDATE", "KILL")
_DEPTH_ORDER = ("hide", "short", "long", "full")
_PACK_ORDER = ("ACCEPT_PACK", "REVISE", "PARK")
_DISPOSITION_ORDER = ("DELAY", "PASS")
_PLACE_ORDER = ("PLACE", "STAND", "DELAY", "REMINT", "FLATTEN_CANDIDATE")
_WIRE_ORDER = AUTOMODE_WIRE
_LABEL_BASE = ("DIG_CHAIR",)

_VERDICT_CRITERIA = {
    "APPLY_CANDIDATE": "This dig state earns apply.",
    "KILL": "This dig state earns kill.",
}
_DEPTH_CRITERIA = {
    "hide": "Include depth on this state is hide.",
    "short": "Include depth on this state is short.",
    "long": "Include depth on this state is long.",
    "full": "Include depth on this state is full.",
}
_PACK_CRITERIA = {
    "ACCEPT_PACK": "This pack is accepted.",
    "REVISE": "This pack is revised.",
    "PARK": "This pack is parked.",
}
_DISPOSITION_CRITERIA = {
    "DELAY": "The disposition on this state is delay.",
    "PASS": "The disposition on this state is pass.",
}
_PLACE_CRITERIA = {
    "PLACE": "The place label on this state is place.",
    "STAND": "The place label on this state is stand.",
    "DELAY": "The place label on this state is delay.",
    "REMINT": "The place label on this state is remint.",
    "FLATTEN_CANDIDATE": "The place label on this state names the flatten candidate.",
}
_WIRE_CRITERIA = {
    "tool_risk_gate": "The automode component is the tool risk gate.",
    "fluid_at_place": "The automode component is fluid at place.",
    "A1_observe": "The automode component is A1 observe.",
}

_LIMIT_PARTS = ("floor", "baseline", "to_pass", "pass_line")
_SECRET_PARTS = ("api_key", "token", "secret", "authorization", "password")
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

Decision = tuple[str, str, str, tuple[str, ...]]


def _limit_key(name: str) -> bool:
    low = str(name).lower().replace("-", "_")
    return any(part in low for part in _LIMIT_PARTS)


def _skip_key(name: str) -> bool:
    low = str(name).lower()
    if name == "prior_outcomes" or _limit_key(name):
        return True
    return any(part in low for part in _SECRET_PARTS)


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    lowered = cleaned.lower()
    kept: list[str] = []
    index = 0
    while index < len(cleaned):
        if lowered.startswith("baseline", index):
            index += len("baseline")
            continue
        if lowered.startswith("floor", index):
            index += len("floor")
            continue
        kept.append(cleaned[index])
        index += 1
    return " ".join("".join(kept).split())


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


def _plain(value: Any, seen: set[int] | None = None) -> Any:
    """Walk the value. A repeated container is a cycle and stops. No depth cap."""

    if seen is None:
        seen = set()
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return _scrub_text(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(value) if isinstance(value, float) else value
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _skip_key(name):
                continue
            out[name] = _plain(item, seen)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        return [_plain(item, seen) for item in value]
    return None


def _choice_line(subject: str) -> str:
    return (
        f"Which {subject} is this dig state? "
        "The option with the single highest probability is that return. "
        "An empty answer or a tie leaves it unset. "
        "This question does not send."
    )


def _noul_line(subject: str) -> str:
    return (
        f"Is {subject} true on this dig state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send."
    )


def _score_line(subject: str) -> str:
    return (
        f"The score you return is the {subject} on this dig state. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "This question does not send."
    )


def _choice_q(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    kept = {
        str(key): _scrub_text(str(text))
        for key, text in criteria.items()
        if not _limit_key(str(key)) and _scrub_text(str(text))
    }
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": _scrub_text(instructions),
        "criteria": kept,
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, body["instructions"], dict(kept))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "choice"
    body["instructions"] = _scrub_text(instructions)
    body["criteria"] = kept
    return {qid: body}


def _score_q(qid: str, instructions: str) -> dict[str, Any]:
    """A Score for this card. An amount waits for the card. An order keeps its words."""

    words = _ordinal_words(str(qid))
    row = _pending_score(qid, instructions, words)
    if not isinstance(row, dict):
        return {}
    return {str(qid): row}



def _noul_q(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(instructions),
            "criteria": {
                "true": "Yes, on this dig state.",
                "false": "No, on this dig state.",
            },
        }
    }


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _number(value)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _present_unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest among probabilities that were actually returned."""

    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if probabilities[name] == best]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    """The choice is the unique highest probability. A label alone is not a choice."""

    if isinstance(block, dict) and block.get("error"):
        return None
    probabilities = _probabilities(block)
    if not probabilities or not order:
        return None
    local = _present_unique(probabilities, order)
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probabilities, order)
    except Exception:
        agreed = local
    if local is None or agreed is None or str(agreed) != local:
        return None
    if str(agreed) not in order:
        return None
    return local


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if block is True or block is False:
        return block
    if not isinstance(block, dict):
        return _number(block)
    if block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        value = block.get("noul") if "noul" in block else block.get("Noul")
        if value is None:
            return None
        if value is True or value is False:
            return value
        return _number(value)
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The parameter is the returned score. A missing score stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "score" in block:
        raw = block.get("score")
    elif "value" in block:
        raw = block.get("value")
    else:
        return None
    if raw is None or isinstance(raw, bool):
        return None
    number = _number(raw)
    if number is None:
        return None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(block))
    except Exception:
        parsed = number
    if parsed is None or parsed != number:
        return None
    return number


def _marks() -> dict[str, Any]:
    """Structural marks of this module. They are not an answer."""

    return {
        "schema": SCHEMA,
        "model": MODEL,
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "never_order_send": True,
        "never_flatten": True,
        "news_invent": False,
    }


def _base_state(facts: Mapping[str, Any] | None) -> dict[str, Any]:
    plain = _plain(dict(facts or {}))
    state = plain if isinstance(plain, dict) else {}
    state.pop("prior_outcomes", None)
    state["schema"] = SCHEMA
    state["model"] = MODEL
    state["book"] = CHALLENGE_LOGIN
    state["ns"] = CHALLENGE_NS
    state["magic"] = CHALLENGE_MAGIC
    state["subgoal"] = "x_dig_judge"
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


def _miss_reason(kind: str, error: str | None) -> str:
    if error:
        return error
    if kind == "score":
        return "score_missing"
    if kind == "noul":
        return "noul_missing"
    return "tie_or_empty"


def _remember(
    state: Mapping[str, Any],
    decisions: Sequence[Decision],
    row: Mapping[str, Any],
) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    error = row.get("error")
    error_text = None if error in (None, "") else str(error)
    pairs = [(qid, row.get(field), kind) for qid, field, kind, _order in decisions]
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, kind in pairs:
            _LOCAL_OUTCOMES.append({
                "key": key,
                "value": value,
                "error": None if value is not None else _miss_reason(kind, error_text),
            })
        return
    for key, value, kind in pairs:
        try:
            append_outcome(
                key,
                value,
                logged,
                error=None if value is not None else _miss_reason(kind, error_text),
            )
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


def _from_answers(
    answers: Mapping[str, Any],
    decisions: Sequence[Decision],
    error: str | None,
) -> dict[str, Any]:
    row: dict[str, Any] = {"model": MODEL, "error": error}
    for qid, field, kind, order in decisions:
        block = answers.get(qid)
        if kind == "choice":
            row[field] = _choice(block, order)
        elif kind == "noul":
            row[field] = _noul(block)
        else:
            row[field] = _score(block)
    return row


def _decide(
    facts: Mapping[str, Any] | None,
    questions: Mapping[str, Any],
    decisions: Sequence[Decision],
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    """One System One post. A miss leaves every decision on this ask unset."""

    state = _base_state(facts)
    _attach_priors(state, questions)
    try:
        receipt = _post(state, questions, evaluate_fn)
    except Exception as exc:  # noqa: BLE001 — a failed ask must not raise into the judge
        row = _from_answers({}, decisions, type(exc).__name__)
        _remember(state, decisions, row)
        return row
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    if not answers:
        row = _from_answers({}, decisions, None if error in (None, "") else str(error))
        if receipt.get("model"):
            row["model"] = receipt.get("model")
        _remember(state, decisions, row)
        return row
    row = _from_answers(answers, decisions, None if error in (None, "") else str(error))
    if receipt.get("model"):
        row["model"] = receipt.get("model")
    _remember(state, decisions, row)
    return row


def _safe_token(text: str) -> bool:
    return bool(text) and text.replace("_", "").isalnum() and not _limit_key(text)


def _label_order(label: str | None) -> tuple[str, ...]:
    order = list(_LABEL_BASE)
    if isinstance(label, str):
        token = _scrub_text(label).strip()
        if _safe_token(token) and token not in order:
            order.append(token)
    return tuple(order)


def _label_criteria(order: tuple[str, ...]) -> dict[str, str]:
    return {name: f"The dig label on this state is {name}." for name in order}


def _recipe_facts(recipes: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, rec in recipes.items():
        verdict = None
        if isinstance(rec, Mapping) and isinstance(rec.get("verdict"), str):
            verdict = _scrub_text(rec.get("verdict")) or None
        rows.append({"name": _scrub_text(str(name)), "verdict": verdict})
    return rows


def _wired(row: Mapping[str, Any]) -> list[str] | None:
    """Names whose Noul is true. A probability stays on the field and is not collapsed."""

    flags = (
        ("tool_risk_gate", row.get("wire_tool_risk_gate")),
        ("fluid_at_place", row.get("wire_fluid_at_place")),
        ("A1_observe", row.get("wire_a1_observe")),
    )
    values = [value for _name, value in flags]
    if any(not isinstance(value, bool) for value in values):
        return None
    return [name for name, value in flags if value is True]


def persist_stays_zero(
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> float | None:
    """Persistence weight for this dig state. The score is that return."""

    questions = _score_q("xdig_persist_weight", _score_line("persistence weight"))
    decisions: tuple[Decision, ...] = (
        ("xdig_persist_weight", "persist_weight", "score", ()),
    )
    row = _decide({"gate": "persist_weight"}, questions, decisions, evaluate_fn)
    weight = row.get("persist_weight")
    return weight if isinstance(weight, float) else None


def fanout_one_post_payload(
    *,
    seat: str,
    question_ids: Sequence[str],
    state: Mapping[str, Any] | None = None,
    include_depth: str | None = None,
    merge_sleeve: bool | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One fanout state. Depth, merge, verdict, and the parameter are that return."""

    questions: dict[str, Any] = {}
    questions.update(_choice_q("xdig_include_depth", _choice_line("include depth"), _DEPTH_CRITERIA))
    questions.update(_noul_q("xdig_merge_sleeve", _noul_line("merge sleeve")))
    questions.update(_noul_q("xdig_one_post", _noul_line("one post for this candidate")))
    questions.update(_noul_q("xdig_ask_together", _noul_line("ask together")))
    questions.update(_noul_q("xdig_noul_every_tick", _noul_line("a noul on every tick")))
    questions.update(_choice_q("xdig_fanout_verdict", _choice_line("fanout verdict"), _VERDICT_CRITERIA))
    questions.update(_noul_q("xdig_fanout_ready", _noul_line("fanout ready for chair enforce")))
    questions.update(_score_q("xdig_fanout_parameter", _score_line("fanout parameter")))
    decisions: tuple[Decision, ...] = (
        ("xdig_include_depth", "include_depth", "choice", _DEPTH_ORDER),
        ("xdig_merge_sleeve", "merge_sleeve", "noul", ()),
        ("xdig_one_post", "one_post", "noul", ()),
        ("xdig_ask_together", "ask_together", "noul", ()),
        ("xdig_noul_every_tick", "noul_every_tick", "noul", ()),
        ("xdig_fanout_verdict", "verdict", "choice", _VERDICT_ORDER),
        ("xdig_fanout_ready", "ready_for_chair_enforce", "noul", ()),
        ("xdig_fanout_parameter", "parameter", "score", ()),
    )
    ids = [item for item in (_scrub_text(str(qid)) for qid in question_ids) if item]
    seat_text = _scrub_text(str(seat))
    facts = {
        "gate": "fanout_one_post",
        "seat": seat_text,
        "question_ids": ids,
        "fanout_state": dict(state or {}),
        "proposed_include_depth": include_depth,
        "proposed_merge_sleeve": merge_sleeve,
    }
    row = _decide(facts, questions, decisions, evaluate_fn)
    out = _marks()
    out.update({
        "stub": "FANOUT_ONE_POST",
        "seat": seat_text,
        "questions": ids,
        "include_depth": row.get("include_depth"),
        "merge_sleeve": row.get("merge_sleeve"),
        "one_post": row.get("one_post"),
        "ask_together": row.get("ask_together"),
        "noul_every_tick": row.get("noul_every_tick"),
        "verdict": row.get("verdict"),
        "ready_for_chair_enforce": row.get("ready_for_chair_enforce"),
        "parameter": row.get("parameter"),
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
    })
    return out


def harvest_emitter(
    *,
    extras: Mapping[str, Any] | None = None,
    invent_news: bool = False,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Harvest state. The verdict, the news noul, and the parameter are that return."""

    questions: dict[str, Any] = {}
    questions.update(_choice_q("xdig_harvest_verdict", _choice_line("harvest verdict"), _VERDICT_CRITERIA))
    questions.update(_noul_q("xdig_harvest_ready", _noul_line("harvest ready for chair enforce")))
    questions.update(_noul_q("xdig_harvest_news_invented", _noul_line("a news protocol invented on this harvest")))
    questions.update(_score_q("xdig_harvest_parameter", _score_line("harvest parameter")))
    decisions: tuple[Decision, ...] = (
        ("xdig_harvest_verdict", "verdict", "choice", _VERDICT_ORDER),
        ("xdig_harvest_ready", "ready_for_chair_enforce", "noul", ()),
        ("xdig_harvest_news_invented", "news_protocol_invented", "noul", ()),
        ("xdig_harvest_parameter", "parameter", "score", ()),
    )
    facts = {
        "gate": "harvest_emitter",
        "extras": dict(extras or {}),
        "proposed_invent_news": bool(invent_news),
    }
    row = _decide(facts, questions, decisions, evaluate_fn)
    out = _marks()
    out.update({
        "stub": "HARVEST_EMITTER",
        "attach": _plain(dict(extras or {})) or {},
        "never_vendor": NEVER_VENDOR,
        "never_invent_news": NEVER_INVENT_NEWS,
        "never_place": NEVER_PLACE,
        "occupancy_hold_dead": OCCUPANCY_HOLD_DEAD,
        "news_protocol_invented": row.get("news_protocol_invented"),
        "verdict": row.get("verdict"),
        "ready_for_chair_enforce": row.get("ready_for_chair_enforce"),
        "parameter": row.get("parameter"),
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
    })
    return out


def policy_c_shadow_evaluate(
    *,
    static_decision: Mapping[str, Any] | None = None,
    jev_decision: Mapping[str, Any] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Shadow state beside the static facts. Enforce and the verdict are that return."""

    questions: dict[str, Any] = {}
    questions.update(_choice_q("xdig_policy_verdict", _choice_line("policy shadow verdict"), _VERDICT_CRITERIA))
    questions.update(_choice_q("xdig_policy_enforce", _choice_line("policy enforce verdict"), _VERDICT_CRITERIA))
    questions.update(_noul_q("xdig_chair_keeps_place", _noul_line("the chair keeps place")))
    questions.update(_noul_q("xdig_writer_prints", _noul_line("the writer prints")))
    questions.update(_noul_q("xdig_policy_c_chair_enforce", _noul_line("policy chair enforce")))
    questions.update(_score_q("xdig_policy_parameter", _score_line("policy parameter")))
    decisions: tuple[Decision, ...] = (
        ("xdig_policy_verdict", "verdict", "choice", _VERDICT_ORDER),
        ("xdig_policy_enforce", "enforce_verdict", "choice", _VERDICT_ORDER),
        ("xdig_chair_keeps_place", "chair_keeps_place", "noul", ()),
        ("xdig_writer_prints", "writer_prints", "noul", ()),
        ("xdig_policy_c_chair_enforce", "policy_c_chair_enforce", "noul", ()),
        ("xdig_policy_parameter", "parameter", "score", ()),
    )
    facts = {
        "gate": "policy_c_shadow_evaluate",
        "static": dict(static_decision or {}),
        "jev": dict(jev_decision or {}),
    }
    row = _decide(facts, questions, decisions, evaluate_fn)
    enforce = row.get("policy_c_chair_enforce")
    out = _marks()
    out.update({
        "stub": "POLICY_C_SHADOW_EVALUATE",
        "static": _plain(dict(static_decision or {})) or {},
        "jev": _plain(dict(jev_decision or {})) or {},
        "chair_keeps_place": row.get("chair_keeps_place"),
        "writer_prints": row.get("writer_prints"),
        "ready_for_chair_enforce": enforce,
        "policy_c_chair_enforce": enforce,
        "verdict": row.get("verdict"),
        "enforce_verdict": row.get("enforce_verdict"),
        "parameter": row.get("parameter"),
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
    })
    return out


def usage_router_label(
    *,
    stake: str,
    label: str | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Router state. The label, place, apply, and the parameter are that return."""

    order = _label_order(label)
    questions: dict[str, Any] = {}
    questions.update(_choice_q("xdig_router_label", _choice_line("usage label"), _label_criteria(order)))
    questions.update(_noul_q("xdig_router_place", _noul_line("this router places")))
    questions.update(_noul_q("xdig_router_apply", _noul_line("this router applies")))
    questions.update(_choice_q("xdig_router_verdict", _choice_line("router verdict"), _VERDICT_CRITERIA))
    questions.update(_noul_q("xdig_router_ready", _noul_line("router ready for chair enforce")))
    questions.update(_score_q("xdig_router_parameter", _score_line("router parameter")))
    decisions: tuple[Decision, ...] = (
        ("xdig_router_label", "label", "choice", order),
        ("xdig_router_place", "place", "noul", ()),
        ("xdig_router_apply", "apply", "noul", ()),
        ("xdig_router_verdict", "verdict", "choice", _VERDICT_ORDER),
        ("xdig_router_ready", "ready_for_chair_enforce", "noul", ()),
        ("xdig_router_parameter", "parameter", "score", ()),
    )
    stake_text = _scrub_text(str(stake))
    facts = {
        "gate": "usage_router_label",
        "stake": stake_text,
        "proposed_label": label,
    }
    row = _decide(facts, questions, decisions, evaluate_fn)
    out = _marks()
    out.update({
        "stub": "USAGE_ROUTER_LABEL",
        "stake": stake_text,
        "label": row.get("label"),
        "place": row.get("place"),
        "apply": row.get("apply"),
        "verdict": row.get("verdict"),
        "ready_for_chair_enforce": row.get("ready_for_chair_enforce"),
        "parameter": row.get("parameter"),
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
    })
    return out


def automode_gate(
    *,
    tool_risk: str | None = None,
    fluid_at_place: bool | None = None,
    a1_observe: bool | None = None,
    conf_gate: Any = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Automode state. Which wire is on, and the parameter, are that return."""

    questions: dict[str, Any] = {}
    questions.update(_noul_q("xdig_wire_tool_risk_gate", _noul_line("automode wires the tool risk gate")))
    questions.update(_noul_q("xdig_wire_fluid_at_place", _noul_line("automode wires fluid at place")))
    questions.update(_noul_q("xdig_wire_a1_observe", _noul_line("automode wires A1 observe")))
    questions.update(_choice_q("xdig_automode_component", _choice_line("automode component"), _WIRE_CRITERIA))
    questions.update(_choice_q("xdig_automode_verdict", _choice_line("automode verdict"), _VERDICT_CRITERIA))
    questions.update(_noul_q("xdig_automode_ready", _noul_line("automode ready for chair enforce")))
    questions.update(_score_q("xdig_automode_parameter", _score_line("automode parameter")))
    decisions: tuple[Decision, ...] = (
        ("xdig_wire_tool_risk_gate", "wire_tool_risk_gate", "noul", ()),
        ("xdig_wire_fluid_at_place", "wire_fluid_at_place", "noul", ()),
        ("xdig_wire_a1_observe", "wire_a1_observe", "noul", ()),
        ("xdig_automode_component", "component", "choice", _WIRE_ORDER),
        ("xdig_automode_verdict", "verdict", "choice", _VERDICT_ORDER),
        ("xdig_automode_ready", "ready_for_chair_enforce", "noul", ()),
        ("xdig_automode_parameter", "parameter", "score", ()),
    )
    facts = {
        "gate": "automode",
        "proposed_tool_risk": tool_risk,
        "proposed_fluid_at_place": fluid_at_place,
        "proposed_a1_observe": a1_observe,
        "proposed_conf_gate": conf_gate,
    }
    row = _decide(facts, questions, decisions, evaluate_fn)
    out = _marks()
    out.update({
        "stub": "AUTOMODE",
        "wire_into": _wired(row),
        "tool_risk_gate": row.get("wire_tool_risk_gate"),
        "fluid_at_place": row.get("wire_fluid_at_place"),
        "A1_observe": row.get("wire_a1_observe"),
        "component": row.get("component"),
        "verdict": row.get("verdict"),
        "ready_for_chair_enforce": row.get("ready_for_chair_enforce"),
        "parameter": row.get("parameter"),
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
    })
    return out


def ablation_before_apply(
    *,
    recipes: Mapping[str, Mapping[str, Any]],
    persist: float | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Ablation state. Recipe rows are facts. Pass, verdict, and weight are that return."""

    recipe_rows = _recipe_facts(recipes)
    questions: dict[str, Any] = {}
    questions.update(_score_q("xdig_ablation_persist", _score_line("ablation persistence weight")))
    questions.update(_choice_q("xdig_ablation_verdict", _choice_line("ablation verdict"), _VERDICT_CRITERIA))
    questions.update(_noul_q("xdig_ablation_pass", _noul_line("ablation passes")))
    decisions: tuple[Decision, ...] = (
        ("xdig_ablation_persist", "persist_weight", "score", ()),
        ("xdig_ablation_verdict", "verdict", "choice", _VERDICT_ORDER),
        ("xdig_ablation_pass", "pass", "noul", ()),
    )
    facts = {
        "gate": "ablation_before_apply",
        "recipes": recipe_rows,
        "recipe_count": len(recipe_rows),
        "proposed_persist": persist,
    }
    row = _decide(facts, questions, decisions, evaluate_fn)
    out = _marks()
    out.update({
        "stub": "ABLATION_BEFORE_APPLY",
        "n_recipes": len(recipe_rows),
        "recipes": recipe_rows,
        "persist_weight": row.get("persist_weight"),
        "pass": row.get("pass"),
        "verdict": row.get("verdict"),
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
    })
    return out


def judge_pack(
    *,
    answers: Mapping[str, Any] | None,
    hist_keep: bool,
    news_invented: bool = False,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Close-loop state. The pack, the place label, and the weight are that return."""

    questions: dict[str, Any] = {}
    questions.update(_choice_q("xdig_judge_choice", _choice_line("judge pack"), _PACK_CRITERIA))
    questions.update(_choice_q("xdig_judge_verdict", _choice_line("judge verdict"), _VERDICT_CRITERIA))
    questions.update(_choice_q("xdig_judge_disposition", _choice_line("judge disposition"), _DISPOSITION_CRITERIA))
    questions.update(_choice_q("xdig_judge_od13", _choice_line("place label"), _PLACE_CRITERIA))
    questions.update(_score_q("xdig_judge_persist", _score_line("judge persistence weight")))
    decisions: tuple[Decision, ...] = (
        ("xdig_judge_choice", "choice", "choice", _PACK_ORDER),
        ("xdig_judge_verdict", "verdict", "choice", _VERDICT_ORDER),
        ("xdig_judge_disposition", "disposition", "choice", _DISPOSITION_ORDER),
        ("xdig_judge_od13", "od13", "choice", _PLACE_ORDER),
        ("xdig_judge_persist", "persist_weight", "score", ()),
    )
    facts = {
        "gate": "judge_pack",
        "pack_answers": dict(answers or {}),
        "hist_keep": bool(hist_keep),
        "proposed_news_invented": bool(news_invented),
    }
    row = _decide(facts, questions, decisions, evaluate_fn)
    od13 = row.get("od13")
    out = _marks()
    out.update({
        "choice": row.get("choice"),
        "verdict": row.get("verdict"),
        "disposition": row.get("disposition"),
        "criteria": list(JUDGE_PACK),
        "od13": None if od13 is None else {"choice": od13},
        "persist_weight": row.get("persist_weight"),
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
    })
    return out


def _board_questions() -> tuple[dict[str, Any], tuple[Decision, ...]]:
    pack: dict[str, Any] = {}
    decisions: list[Decision] = []
    for stub in STUB_IDS:
        verdict_id = f"xdig_stub_{stub}_verdict"
        ready_id = f"xdig_stub_{stub}_ready"
        pack.update(_choice_q(verdict_id, _choice_line(f"stub {stub} verdict"), _VERDICT_CRITERIA))
        pack.update(_noul_q(ready_id, _noul_line(f"stub {stub} ready for chair enforce")))
        decisions.append((verdict_id, f"verdict_{stub}", "choice", _VERDICT_ORDER))
        decisions.append((ready_id, f"ready_{stub}", "noul", ()))
    pack.update(_choice_q(
        "xdig_stub_POLICY_C_SHADOW_EVALUATE_enforce",
        _choice_line("policy shadow enforce verdict"),
        _VERDICT_CRITERIA,
    ))
    decisions.append((
        "xdig_stub_POLICY_C_SHADOW_EVALUATE_enforce",
        "enforce_POLICY_C_SHADOW_EVALUATE",
        "choice",
        _VERDICT_ORDER,
    ))
    pack.update(_score_q("xdig_board_persist", _score_line("board persistence weight")))
    decisions.append(("xdig_board_persist", "persist_weight", "score", ()))
    pack.update(_score_q("xdig_resting_shadow", _score_line("resting shadow count")))
    decisions.append(("xdig_resting_shadow", "resting_shadow", "score", ()))
    return pack, tuple(decisions)


def stub_board(
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Dig board. Each stub verdict, the weight, and the shadow count are that return."""

    questions, decisions = _board_questions()
    row = _decide({"gate": "stub_board", "stubs": list(STUB_IDS)}, questions, decisions, evaluate_fn)
    stubs: dict[str, Any] = {}
    for stub in STUB_IDS:
        item: dict[str, Any] = {
            "verdict": row.get(f"verdict_{stub}"),
            "ready_for_chair_enforce": row.get(f"ready_{stub}"),
        }
        if stub == "POLICY_C_SHADOW_EVALUATE":
            item["enforce"] = row.get("enforce_POLICY_C_SHADOW_EVALUATE")
        if stub == "AUTOMODE":
            item["wire_menu"] = list(AUTOMODE_WIRE)
        stubs[stub] = item
    out = _marks()
    out.update({
        "steal": STEAL,
        "stubs": stubs,
        "resting_shadow": row.get("resting_shadow"),
        "persist_weight": row.get("persist_weight"),
        "occupancy_hold_dead": OCCUPANCY_HOLD_DEAD,
        "place_criteria": list(_PLACE_ORDER),
        "model": row.get("model") or MODEL,
        "error": row.get("error"),
    })
    return out


__all__ = [
    "AUTOMODE_NOT",
    "AUTOMODE_WIRE",
    "CHALLENGE_LOGIN",
    "CHALLENGE_MAGIC",
    "CHALLENGE_NS",
    "JUDGE_PACK",
    "MODEL",
    "OCCUPANCY_HOLD_DEAD",
    "POLICY_C_CHAIR_ENFORCE",
    "SCHEMA",
    "STEAL",
    "STUB_IDS",
    "ablation_before_apply",
    "automode_gate",
    "fanout_one_post_payload",
    "harvest_emitter",
    "judge_pack",
    "persist_stays_zero",
    "policy_c_shadow_evaluate",
    "stub_board",
    "usage_router_label",
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
