"""Code-side compose. Every decision is the System One return for this state.

One piece: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached on
the ask, and the return is stored for the next ask. The choice, the tilt,
the alignment, and the other parameters are that return. A score may sit
between levels. An empty answer, a tie, or an error leaves the return unset.

A floor and a baseline are not a question. This module does not send.
"""

from __future__ import annotations

from typing import Any, Mapping

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

_FUNCTION_ORDER = ("returned_score", "last_outcome", "withhold")
_BRANCH_ORDER = ("take", "skip")
_STANCE_ORDER = ("with_flow", "against_flow", "no_clear_flow")
_DISPOSITION_ORDER = ("named_apply", "log_only")
_CHOICE_IDS = ("compose_function", "compose_if", "flow_stance", "disposition")
_SCORE_IDS = ("flow_alignment", "flow_tilt", "cost_tilt", "ca_tilt", "combined_tilt")
_NOUL_IDS = (
    "cost_hurtful",
    "state_sufficient",
    "apply_flow",
    "apply_cost",
    "apply_ca",
    "leave_orig",
    "named_apply_symbol",
    "aplus_shadow",
    "house_block",
    "never_zero_fire",
    "never_place",
    "cannot_refuse",
    "cannot_add_size",
    "size_includes_ca",
    "never_admit",
    "event_questions_abstain",
)
_PACK_IDS = frozenset(_CHOICE_IDS + _SCORE_IDS + _NOUL_IDS)
_LIMIT_PARTS = ("floor", "baseline")
_BANNED_TEXT = ("90000", "90k", "110000", "110k")
_SECRET_PARTS = ("api_key", "apikey", "authorization", "secret", "password", "token")
_DROP = object()
_DEPTH = 0


def _load_lock() -> dict[str, Any]:
    """Names from the process lock when that module is present. Missing stays missing."""

    try:
        from .process_lock import (
            COST_TILT_MAX as cost_hi,
            COST_TILT_MIN as cost_lo,
            FLOW_TILT_MAX as flow_hi,
            FLOW_TILT_MIN as flow_lo,
            LOCK_ID as lock_id,
            WIRE_CA_SIZE as wire_ca,
            WIRE_COST as wire_cost,
            WIRE_FLOW as wire_flow,
        )
    except Exception:
        return {
            "tilt_min": None,
            "tilt_max": None,
            "cost_min": None,
            "cost_max": None,
            "wire_flow": "f5_xau_flow_alignment_size_tilt",
            "wire_cost": "F5-JEV-004",
            "wire_ca": "ca_cross_asset_size_tilt",
            "lock_id": None,
        }
    return {
        "tilt_min": flow_lo,
        "tilt_max": flow_hi,
        "cost_min": cost_lo,
        "cost_max": cost_hi,
        "wire_flow": wire_flow,
        "wire_cost": wire_cost,
        "wire_ca": wire_ca,
        "lock_id": lock_id,
    }


_LOCK = _load_lock()
TILT_MIN = _LOCK["tilt_min"]
TILT_MAX = _LOCK["tilt_max"]
COST_TILT_MIN = _LOCK["cost_min"]
COST_TILT_MAX = _LOCK["cost_max"]
WIRE_CANDIDATE = _LOCK["wire_flow"]


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
    return any(token in compact for token in _BANNED_TEXT)


def _secret_key(name: str) -> bool:
    low = str(name).lower().replace("-", "_")
    return any(part in low for part in _SECRET_PARTS)


def _question_text_ok(value: str) -> bool:
    low = value.lower()
    if "floor" in low or "baseline" in low or "flatten" in low:
        return False
    if _banned_text(value):
        return False
    if "order" + "_send" in low or "ran" + "dom" in low:
        return False
    return True


def _scrub(value: Any, depth: int = 0) -> Any:
    """Drop floor, baseline, and secret fields before the ask."""

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
        if number is None:
            return _DROP
        if _banned_text(format(number, ".10g")):
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


def _choice_body(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    block: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(text) for key, text in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(block["criteria"]))
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        pass
    block["type"] = "choice"
    block["instructions"] = instructions
    block["criteria"] = {str(key): str(text) for key, text in criteria.items()}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    return {qid: block}


def _score_body(qid: str, instructions: str) -> dict[str, Any]:
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
    criteria = block.get("criteria")
    if isinstance(criteria, list):
        kept = [str(item) for item in criteria if _question_text_ok(str(item))]
        if kept:
            block["criteria"] = kept
        else:
            block.pop("criteria", None)
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    return {qid: block}


def _noul_body(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes. The noul you return is that answer.",
                "false": "No. The noul you return is that answer.",
            },
        }
    }


def compose_questions() -> dict[str, Any]:
    """One card. Choice, score, and noul only. Floor and baseline are not on it."""

    pack: dict[str, Any] = {}
    pack.update(_choice_body(
        "compose_function",
        "Which function returns the alignment and the tilts on this state? "
        "The name you return is the function that runs. "
        "Do not name a number. Do not send an order.",
        {
            "returned_score": "The function is the score hop. Its return is the alignment and the tilts.",
            "last_outcome": "The function reads the previous returned alignment and tilts and returns those.",
            "withhold": "The function returns no alignment and no tilt.",
        },
    ))
    pack.update(_choice_body(
        "compose_if",
        "Does this state take the compose branch? "
        "The name you return is the branch. Do not send an order.",
        {
            "take": "Take the branch. The named function returns the alignment and the tilts.",
            "skip": "Do not take the branch. The alignment and the tilts stay unset.",
        },
    ))
    pack.update(_choice_body(
        "flow_stance",
        "What is the flow stance on this state? "
        "The unique highest probability is the stance. "
        "An empty answer or a tie leaves the stance unset. Do not send an order.",
        {
            "with_flow": "The side stands with the flow on this state.",
            "against_flow": "The side stands against the flow on this state.",
            "no_clear_flow": "This state has no clear flow stance.",
        },
    ))
    pack.update(_choice_body(
        "disposition",
        "What disposition does this compose return? "
        "The unique highest probability is the disposition. "
        "An empty answer or a tie leaves it unset. Do not send an order.",
        {
            "named_apply": "This row carries the returned tilts.",
            "log_only": "This row is a log. It does not send.",
        },
    ))
    pack.update(_score_body(
        "flow_alignment",
        "Given the facts and prior_outcomes on this state, what is the flow alignment? "
        "The score you return is that alignment. It may sit between the levels. "
        "An empty score leaves the alignment unset. Do not send an order.",
    ))
    pack.update(_score_body(
        "flow_tilt",
        "Given the facts and prior_outcomes on this state, what flow tilt does this state return? "
        "The score you return is that tilt. It may sit between the levels. "
        "An empty score leaves the tilt unset. Do not send an order.",
    ))
    pack.update(_score_body(
        "cost_tilt",
        "Given the facts and prior_outcomes on this state, what cost tilt does this state return? "
        "The score you return is that tilt. It may sit between the levels. "
        "An empty score leaves the tilt unset. Do not send an order.",
    ))
    pack.update(_score_body(
        "ca_tilt",
        "Given the facts and prior_outcomes on this state, what ca tilt does this state return? "
        "The score you return is that tilt. It may sit between the levels. "
        "An empty score leaves the tilt unset. Do not send an order.",
    ))
    pack.update(_score_body(
        "combined_tilt",
        "Given the facts and prior_outcomes on this state, what combined tilt does this one compose return? "
        "The score you return is that tilt. It may sit between the levels. "
        "An empty score leaves the tilt unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "cost_hurtful",
        "Is the cost on this state hurtful? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "state_sufficient",
        "Is this state complete enough for this compose? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "apply_flow",
        "Does this state apply the flow tilt? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "apply_cost",
        "Does this state apply the cost tilt? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "apply_ca",
        "Does this state apply the ca tilt? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "leave_orig",
        "Does this state leave the original ticket? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "named_apply_symbol",
        "Is this the named apply symbol for this compose? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "aplus_shadow",
        "Is this sleeve shadow only? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "house_block",
        "Does the house block stand on this state? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "never_zero_fire",
        "Is a zero fire closed on this state? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "never_place",
        "Is place closed on this compose? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "cannot_refuse",
        "Is refuse closed for this compose on this state? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "cannot_add_size",
        "Is adding size closed on this state? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "size_includes_ca",
        "Does this compose include the ca tilt in the size? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "never_admit",
        "Is admit closed for the pack rows on this state? "
        "The noul you return is that answer. An empty noul leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_body(
        "event_questions_abstain",
        "Do the event questions abstain on this state? "
        "The news spine on the card is a fact. "
        "The noul you return is that abstain. An empty noul leaves it unset. Do not send an order.",
    ))
    clean: dict[str, Any] = {}
    for qid, block in pack.items():
        if not isinstance(block, dict):
            continue
        kind = str(block.get("type") or "")
        if kind not in {"noul", "choice", "score"}:
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


def _blank() -> dict[str, Any]:
    row: dict[str, Any] = {}
    for key in _CHOICE_IDS + _SCORE_IDS + _NOUL_IDS:
        row[key] = None
    return row


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, dict):
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


def _unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    if not numeric:
        return None
    names = tuple(str(name) for name in order)
    best: str | None = None
    best_p: float | None = None
    tied = False
    for name in names:
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
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(numeric), names)
    except Exception:
        picked = best
    if picked is None or str(picked) != best:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, dict):
        return None
    if block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"", "choice"}:
        return None
    return _unique(_probabilities(block, order), order)


def _score(block: Any) -> float | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"", "score"}:
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
    if not isinstance(block, dict) or block.get("error") or "noul" not in block:
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"", "noul"}:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _jev_score(answers: dict[str, Any], key: str) -> float | None:
    """The score on this answer key. A missing block stays unset."""

    if not isinstance(answers, dict):
        return None
    return _score(answers.get(key))


def _jev_noul(answers: dict[str, Any], key: str) -> bool | float | None:
    """The noul on this answer key. A missing block stays unset."""

    if not isinstance(answers, dict):
        return None
    return _noul(answers.get(key))


def _last(spot: str) -> float | None:
    try:
        from .jev_questions import last_logged_value

        return _finite(last_logged_value(spot))
    except Exception:
        return None


def _read(answers: Mapping[str, Any]) -> dict[str, Any]:
    row = _blank()
    row["compose_function"] = _choice(answers.get("compose_function"), _FUNCTION_ORDER)
    row["compose_if"] = _choice(answers.get("compose_if"), _BRANCH_ORDER)
    row["flow_stance"] = _choice(answers.get("flow_stance"), _STANCE_ORDER)
    row["disposition"] = _choice(answers.get("disposition"), _DISPOSITION_ORDER)
    for key in _NOUL_IDS:
        row[key] = _noul(answers.get(key))
    function_name = row["compose_function"]
    branch = row["compose_if"]
    if function_name == "returned_score" and branch == "take":
        for key in _SCORE_IDS:
            row[key] = _score(answers.get(key))
    elif function_name == "last_outcome" and branch == "take":
        for key in _SCORE_IDS:
            row[key] = _last(key)
    return row


def _injected(answers: Mapping[str, Any] | None) -> bool:
    return isinstance(answers, Mapping) and any(key in answers for key in _PACK_IDS)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    loaded: Any = []
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        loaded = []
    cleaned = _scrub(loaded)
    if cleaned is _DROP or cleaned is None:
        cleaned = []
    state["prior_outcomes"] = cleaned


def _post(state: Mapping[str, Any], questions: Mapping[str, Any]) -> tuple[dict[str, Any], str | None]:
    asked = _scrub(dict(state))
    if not isinstance(asked, dict):
        asked = {}
    asked.pop("prior_outcomes", None)
    asked["model"] = MODEL
    asked["api_url"] = API_URL
    asked.setdefault("login", CHALLENGE_LOGIN)
    asked.setdefault("namespace", CHALLENGE_NS)
    asked.setdefault("ns", CHALLENGE_NS)
    _attach_priors(asked, questions)
    try:
        from .jev_client import evaluate
    except Exception as exc:
        return {}, type(exc).__name__
    try:
        receipt = evaluate(
            asked,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:
        return {}, type(exc).__name__
    if not isinstance(receipt, dict):
        return {}, "evaluate_not_a_dict"
    answers = receipt.get("answers")
    if receipt.get("ok") is False or not isinstance(answers, dict) or not answers:
        err = receipt.get("error") or receipt.get("skipped") or "empty"
        return {}, str(err)
    return answers, None


def _remember(state: Mapping[str, Any], row: Mapping[str, Any], error: str | None) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key in _CHOICE_IDS:
        value = row.get(key)
        try:
            append_outcome(
                key,
                value,
                logged,
                error=None if value is not None else (error or "tie_or_empty"),
            )
        except Exception:
            continue
    for key in _SCORE_IDS:
        value = row.get(key)
        try:
            append_outcome(
                key,
                value if isinstance(value, (int, float)) and not isinstance(value, bool) else None,
                logged,
                error=None if value is not None else (error or "score_missing"),
            )
        except Exception:
            continue
    for key in _NOUL_IDS:
        value = row.get(key)
        if value is True or value is False:
            stored = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            stored = value
        else:
            stored = None
        try:
            append_outcome(
                key,
                stored,
                logged,
                error=None if value is not None else (error or "noul_missing"),
            )
        except Exception:
            continue


def _ask(state: Mapping[str, Any], answers: Mapping[str, Any] | None) -> tuple[dict[str, Any], str | None]:
    questions = compose_questions()
    if _injected(answers):
        row = _read(answers or {})
        _remember(state, row, None)
        return row, None
    got, error = _post(state, questions)
    if error is not None:
        row = _blank()
        _remember(state, row, error)
        return row, error
    row = _read(got)
    _remember(state, row, None)
    return row, None


def _apply_row(row: Mapping[str, Any]) -> bool | None:
    flags = [row.get(key) for key in ("apply_flow", "apply_cost", "apply_ca")]
    if any(flag is True for flag in flags):
        return True
    if flags and all(flag is False for flag in flags):
        return False
    return None


def _live(score: Any, flag: Any) -> float | None:
    number = _finite(score)
    if flag is True and number is not None:
        return number
    return None


def _range(lo: Any, hi: Any) -> list[float] | None:
    left = _finite(lo)
    right = _finite(hi)
    if left is None or right is None:
        return None
    return [left, right]


def _passthrough_choice(answers: Mapping[str, Any] | None, key: str) -> str | None:
    if not isinstance(answers, Mapping):
        return None
    block = answers.get(key)
    if not isinstance(block, dict):
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return None
    order = tuple(str(name) for name in raw)
    return _unique(_probabilities(block, order), order)


def _bool_fact(value: Any) -> bool | None:
    if value is True or value is False:
        return value
    return None


def _kept_noul(value: Any) -> bool | float | None:
    if value is True or value is False:
        return value
    return _finite(value)


def _fields(state: Mapping[str, Any], name: str, **fixed: Any) -> dict[str, Any]:
    raw = state.get(name)
    block = dict(raw) if isinstance(raw, Mapping) else {}
    invented = block.get("invented")
    ids = block.get("ids")
    row: dict[str, Any] = {
        "n": block.get("n"),
        "n_assembled": block.get("n_assembled"),
        "ids": list(ids) if isinstance(ids, (list, tuple)) else [],
        "invented": invented if isinstance(invented, bool) else None,
    }
    for key in ("choice", "edge", "n_in", "honesty"):
        if key in block:
            row[key] = block.get(key)
    if name == "pack5_fields":
        names = ((block.get("attach_resolved") or {}) if isinstance(block.get("attach_resolved"), Mapping) else {})
        named = names.get("names") if isinstance(names, Mapping) else None
        row["attach_names"] = list(named) if isinstance(named, Mapping) else []
    row.update(fixed)
    return row


def _lock_stamp() -> dict[str, Any]:
    try:
        from .process_lock import stamp_lock

        stamped = stamp_lock()
    except Exception:
        return {}
    if not isinstance(stamped, dict):
        return {}
    cleaned = _scrub(stamped)
    return cleaned if isinstance(cleaned, dict) else {}


def _cages(ticket: Any) -> dict[str, Any]:
    try:
        from .place_apply import cage_stamp

        stamped = cage_stamp(ticket=ticket)
    except Exception:
        return {}
    if not isinstance(stamped, dict):
        return {}
    cleaned = _scrub(stamped)
    return cleaned if isinstance(cleaned, dict) else {}


def _gate_flow() -> Any:
    try:
        from .a_plus_sleeve import GATE_FLOW_NAME

        return GATE_FLOW_NAME
    except Exception:
        return None


def _facts(
    state: Mapping[str, Any] | None,
    *,
    ticket: Any,
    leave_orig: Any,
    extra: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None,
) -> dict[str, Any]:
    base = _scrub(dict(state or {}))
    facts = dict(base) if isinstance(base, dict) else {}
    facts.pop("prior_outcomes", None)
    facts["caller_ticket"] = _scrub(ticket) if ticket is not None else None
    if facts.get("caller_ticket") is _DROP:
        facts["caller_ticket"] = None
    facts["caller_leave_orig"] = leave_orig if isinstance(leave_orig, bool) else None
    if extra:
        cleaned = _scrub(dict(extra))
        if isinstance(cleaned, dict):
            facts["extra"] = cleaned
    if isinstance(answers, Mapping) and not _injected(answers):
        cleaned_answers = _scrub(dict(answers))
        if isinstance(cleaned_answers, dict):
            facts["given_answers"] = cleaned_answers
    facts["model"] = MODEL
    return facts


def _render(
    state: Mapping[str, Any],
    answers: Mapping[str, Any] | None,
    row: Mapping[str, Any],
    error: str | None,
    *,
    ticket: Any,
) -> dict[str, Any]:
    flow = _finite(row.get("flow_tilt"))
    cost = _finite(row.get("cost_tilt"))
    ca = _finite(row.get("ca_tilt"))
    combined = _finite(row.get("combined_tilt"))
    alignment = _finite(row.get("flow_alignment"))
    apply_flow = _kept_noul(row.get("apply_flow"))
    apply_cost = _kept_noul(row.get("apply_cost"))
    apply_ca = _kept_noul(row.get("apply_ca"))
    apply_this = _apply_row(row)
    live_flow = _live(flow, apply_flow)
    live_cost = _live(cost, apply_cost)
    live_ca = _live(ca, apply_ca)
    live_combined = combined if apply_this is True else None
    leave = _kept_noul(row.get("leave_orig"))
    aplus = _kept_noul(row.get("aplus_shadow"))
    never_zero_fire = _kept_noul(row.get("never_zero_fire"))
    never_place = _kept_noul(row.get("never_place"))
    cannot_refuse = _kept_noul(row.get("cannot_refuse"))
    cannot_add_size = _kept_noul(row.get("cannot_add_size"))
    size_includes_ca = _kept_noul(row.get("size_includes_ca"))
    never_admit = _kept_noul(row.get("never_admit"))
    abstain = _kept_noul(row.get("event_questions_abstain"))
    news = state.get("news") if isinstance(state.get("news"), Mapping) else {}
    cost_state = state.get("cost") if isinstance(state.get("cost"), Mapping) else {}
    spine = _bool_fact(news.get("spine_empty"))
    hurt = row.get("cost_hurtful")
    wire_flow = _LOCK["wire_flow"]
    wire_cost = _LOCK["wire_cost"]
    wire_ca = _LOCK["wire_ca"]
    out: dict[str, Any] = {
        **_lock_stamp(),
        **_cages(ticket),
        "model": MODEL,
        "api_url": API_URL,
        "error": error,
        "never_zero_fire": never_zero_fire,
        "never_place": never_place,
        "house_block": _kept_noul(row.get("house_block")),
        "state_sufficient": _kept_noul(row.get("state_sufficient")),
        "local_flow_stance": row.get("flow_stance"),
        "flow_alignment_used": alignment,
        "flow_alignment_source": "jev" if alignment is not None else None,
        "shadow_size_tilt": flow,
        "live_size_tilt": live_flow,
        "size_tilt": live_flow,
        "shadow_cost_tilt": cost,
        "live_cost_tilt": live_cost,
        "combined_live_tilt": live_combined,
        "combined_tilt": combined,
        "shadow_ca_size_tilt": ca,
        "live_ca_size_tilt": live_ca,
        "ca_cross_asset_size_tilt_apply": apply_ca,
        "physical_size_stays_flow_x_cost": False if apply_ca is True else (True if apply_ca is False else None),
        "physical_size_stays_flow_x_cost_x_ca": size_includes_ca,
        "cost_hurtful_used": _kept_noul(hurt),
        "cost_hurtful_source": "jev" if hurt is not None else None,
        "news_spine_empty": spine,
        "event_questions_abstain": abstain,
        "cost_screen_would_refuse": _bool_fact(cost_state.get("cost_screen_would_refuse")),
        "jev_admit": _passthrough_choice(answers, "admit"),
        "leave_orig": leave,
        "leave_orig_ticket": str(ticket) if leave is True and ticket is not None else None,
        "named_apply_symbol": _kept_noul(row.get("named_apply_symbol")),
        "apply_this_row": apply_this,
        "aplus_shadow_only": aplus,
        "never_apply_size": aplus,
        "compose_function": row.get("compose_function"),
        "compose_if": row.get("compose_if"),
        "chair_fields": _fields(state, "chair_fields", shadow_only=aplus),
        "pack2_fields": _fields(
            state,
            "pack2_fields",
            never_refuse=cannot_refuse,
            shadow_only=aplus,
        ),
        "pack3_fields": _fields(
            state,
            "pack3_fields",
            never_refuse=cannot_refuse,
            never_apply_size=aplus,
            shadow_only=aplus,
        ),
        "pack4_fields": _fields(
            state,
            "pack4_fields",
            never_refuse=cannot_refuse,
            never_apply_size=aplus,
            never_admit=never_admit,
            shadow_only=aplus,
        ),
        "pack5_fields": _fields(
            state,
            "pack5_fields",
            never_refuse=cannot_refuse,
            never_apply_size=aplus,
            never_admit=never_admit,
            shadow_only=aplus,
        ),
        "pack6_fields": _fields(
            state,
            "pack6_fields",
            never_refuse=cannot_refuse,
            never_apply_size=aplus,
            never_admit=never_admit,
            shadow_only=aplus,
        ),
        "disposition": row.get("disposition"),
        "gate_flow": _gate_flow(),
        "size_observe": (apply_this is False) if isinstance(apply_this, bool) else None,
        "a_plus_sleeve": aplus,
        "never_silent_apply": (
            True if aplus is True else (apply_this is False if isinstance(apply_this, bool) else None)
        ),
        "process_lock": _LOCK["lock_id"],
        "returns": {key: row.get(key) for key in _CHOICE_IDS + _SCORE_IDS + _NOUL_IDS},
        "wires": {
            wire_flow: {
                "shadow": flow,
                "live": live_flow,
                "apply": apply_flow,
                "range": None,
            },
            wire_cost: {
                "shadow": cost,
                "live": live_cost,
                "apply": apply_cost,
                "range": None,
                "cannot_refuse": cannot_refuse,
            },
            wire_ca: {
                "shadow": ca,
                "live": live_ca,
                "apply": apply_ca,
                "range": None,
                "cannot_refuse": cannot_refuse,
                "cannot_add_size": cannot_add_size,
                "physical_size_stays_flow_x_cost_x_ca": size_includes_ca,
                "consumes": None,
                "decidable": None,
                "moved": None,
                "components": None,
            },
        },
    }
    return out


def _one(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None,
    *,
    ticket: Any,
    leave_orig: Any,
    extra: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str | None, dict[str, Any]]:
    facts = _facts(state, ticket=ticket, leave_orig=leave_orig, extra=extra, answers=answers)
    row, error = _ask(facts, answers if _injected(answers) else None)
    return row, error, facts


def flow_alignment_size_tilt(score: float | None) -> float | None:
    """The flow tilt is the score this state returns. A miss stays unset."""

    global _DEPTH
    if _DEPTH:
        return None
    _DEPTH += 1
    try:
        row, error, _facts_out = _one(
            {"flow_alignment_fact": score},
            None,
            ticket=None,
            leave_orig=None,
            extra=None,
        )
        if error is not None:
            return None
        return _finite(row.get("flow_tilt"))
    finally:
        _DEPTH -= 1


def cost_hurtful_size_tilt(
    spread_r: float | None,
    *,
    jev_noul: bool | float | None = None,
) -> float | None:
    """The cost tilt is the score this state returns. A miss stays unset."""

    global _DEPTH
    if _DEPTH:
        return None
    _DEPTH += 1
    try:
        row, error, _facts_out = _one(
            {"spread_r_fact": spread_r, "cost_hurtful_fact": jev_noul},
            None,
            ticket=None,
            leave_orig=None,
            extra=None,
        )
        if error is not None:
            return None
        return _finite(row.get("cost_tilt"))
    finally:
        _DEPTH -= 1


def compose_shadow(
    state: dict[str, Any],
    answers: dict[str, Any] | None = None,
    *,
    ticket: Any = None,
    leave_orig: bool | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One compose. The returns are the tilts and the stance. A miss stays unset."""

    global _DEPTH
    nested = _DEPTH > 0
    _DEPTH += 1
    try:
        if nested:
            row, error = _blank(), "reentry"
        else:
            row, error, _facts_out = _one(
                state,
                answers,
                ticket=ticket,
                leave_orig=leave_orig,
                extra=extra,
            )
        out = _render(state or {}, answers, row, error, ticket=ticket)
        # The fluid catalog is its own ask. This compose stays one piece.
        out["fluid"] = None
        return out
    finally:
        _DEPTH -= 1
