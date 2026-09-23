"""A candidate and a ticket pass watch, observe, admit, place, and manage.

Each choice, threshold, loop bound, parameter, and component on that life
is the System One return for that state. The call is ``jev_client.evaluate``
with model ``jev-1.13.0`` and ``merge_sleeve=False`` — the same POST
https://api.typesafe.ai/v1/systemone the place hop uses. Questions are
only Noul, Choice, or Score. Prior outcomes are attached on every ask.
An empty answer, a tie, a missing score, or an error leaves that return
unset. A floor and a baseline are not a limit and are not asked.
This module does not send.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.gate_observe_evaluate.v1"
LIFE = ("watch", "observe", "admit", "place")
_SKIP_KEY_PARTS = ("floor", "baseline")

STEP_CRITERIA: dict[str, dict[str, str]] = {
    "watch": {
        "watch": "Keep this candidate or ticket in view on this step.",
        "release": "This watch step lets it leave view.",
    },
    "observe": {
        "observe": "This state is seen on this step.",
        "quiet": "This step does not add an observation.",
    },
    "admit": {
        "admit": "Admit this candidate or ticket.",
        "abstain": "Do not admit on this state.",
        "hard_refuse": "Refuse this candidate or ticket.",
    },
    "place": {
        "place": "This candidate or ticket is the order on this step.",
        "stand": "This is not the order on this step.",
        "delay": "This step is not the bar for the order.",
    },
    "manage": {
        "leave_orig": "Leave the original stop and target on this step.",
        "move_sl": "Move the stop. The parameter is the score on this step.",
        "move_tp": "Move the target. The parameter is the score on this step.",
        "close": "Close this ticket on this step.",
        "hold": "Hold. Do not modify and do not close on this step.",
    },
}

# Used only when jev_questions is not importable. Not a decision and not a limit.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []

COMPONENT_CRITERIA: dict[str, str] = {
    "watch": "The watch step is the component on this state.",
    "observe": "The observe step is the component on this state.",
    "admit": "The admit step is the component on this state.",
    "place": "The place step is the component on this state.",
    "manage": "The manage step is the component on this state.",
    "UB-OBS-EVERY": "The observe-every fanout is the component on this state.",
    "FLUID-CYCLE": "The fluid cycle is the component on this state.",
    "FLUID-INVENTORY": "The fluid inventory is the component on this state.",
    "POLICY_C": "Policy C is the component on this state.",
    "JEV_SLEEVE_SELECT": "Sleeve select is the component on this state.",
    "S14-REGIME": "The regime pack is the component on this state.",
    "WORLD_PACK": "The world pack is the component on this state.",
    "RDF_PACK": "The rdf pack is the component on this state.",
    "EVERYWHERE_PACK": "The everywhere pack is the component on this state.",
    "CONF_GATE": "The confidence gate is the component on this state.",
    "CA-SIZ-001": "The size seat is the component on this state.",
    "UB-AUTH-010": "The auth seat is the component on this state.",
    "UB-PLC-017": "The place screen is the component on this state.",
    "F5-JEV-004": "The F5 seat is the component on this state.",
    "APLU-OBS-001": "The aplus pipe is the component on this state.",
    "UB-GOV-001": "The governor seat is the component on this state.",
    "COMPOSE-DARK": "The compose seat is the component on this state.",
}



def _card_var():
    var = globals().get("_OBSERVE_CARD")
    if var is None:
        import contextvars

        var = contextvars.ContextVar("observe_card_" + __name__, default=None)
        globals()["_OBSERVE_CARD"] = var
    return var


def _bind_card(state):
    """The card whose facts may anchor an amount. A miss binds nothing."""

    try:
        from collections.abc import Mapping
    except Exception:
        return None
    card = state if isinstance(state, Mapping) else None
    return _card_var().set(card)


def _bound_card():
    try:
        return _card_var().get()
    except Exception:
        return None


_ORDINAL_WIDTH: dict[str, int] = {}
_AMOUNT_UNIT: dict[str, str] = {}
_ORDINAL_WORDS = ("none", "trace", "small", "modest", "notable", "heavy")
_PRICE_KEYS = {
    "entry",
    "stop",
    "target",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
    "open",
    "high",
    "low",
    "close",
    "limit_price",
}
_MONEY_KEYS = {
    "equity",
    "balance",
    "open_pnl",
    "profit",
    "day_start_balance",
    "day_start_equity",
    "realized_closed_profit",
    "day_equity",
    "broker_net",
    "mean_net",
    "realized",
}
_SKIP_WALK = {
    "prior_outcomes",
    "questions",
    "answers",
    "probabilities",
    "criteria",
    "instructions",
}


def _anchor_finite(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    banned = globals().get("_banned_number")
    if callable(banned):
        try:
            if banned(number):
                return None
        except Exception:
            return None
    return number


def _label_ok(text: str) -> bool:
    if not text or not str(text).strip():
        return False
    sample = str(text)
    for name, bad in (
        ("_limit_key", True),
        ("_banned_text", True),
        ("_blocked_text", True),
        ("_text_banned", True),
        ("_skip_key", True),
    ):
        fn = globals().get(name)
        if not callable(fn):
            continue
        try:
            if bool(fn(sample)) is bad:
                return False
        except Exception:
            return False
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            if scrub(sample) is None:
                return False
        except Exception:
            return False
    ok = globals().get("_question_text_ok")
    if callable(ok):
        try:
            if not ok(sample):
                return False
        except Exception:
            return False
    return True


def _amount_unit(qid: str, text: str = "") -> str | None:
    """The unit this score returns. None means the score is an ordinal."""

    name = str(qid).lower()
    if name.endswith("_hour") or name.endswith("_hours"):
        return "hours"
    if "minute" in name and not name.endswith("_parameter"):
        return "minutes"
    tokens = name.replace(".", "_").split("_")
    if (
        "lot" in tokens
        or "lots" in tokens
        or name.endswith("_lot")
        or name.endswith("_lots")
        or name.endswith("min_lot")
    ):
        return "lots"
    if "persist" in name or name.endswith("_weight"):
        return "weight"
    if "ceiling" in name:
        return "size"
    if "concurrent" in name:
        return "count"
    if name.endswith("_net") or "broker_net" in name:
        return "money"
    if (
        "prob" in name
        or ".p_" in name
        or "p_time" in name
        or "p_positive" in name
    ):
        return "probability"
    if (
        "plan_r" in name
        or "mean_r" in name
        or name.endswith("_r")
        or "predicted_e_r" in name
    ):
        return "r"
    if "fitness" in name or name.endswith("_fit"):
        return None
    if "expected_" in name:
        return "count"
    tail = name.rsplit(".", 1)[-1]
    tail_tokens = tail.split("_")
    if (
        tail.endswith("_loop")
        or tail.endswith("_loop_bound")
        or tail == "loop"
        or "retry" in tail_tokens
        or "walk_depth" in tail
        or "posts" in tail_tokens
        or "min_n" in tail
        or tail.endswith("_count")
        or tail.endswith("_n")
    ):
        return "count"
    if "window" in name:
        return "window"
    if "threshold" in name:
        return "price"
    blob = name + "\n" + str(text).lower()
    if "stop or target" in blob or "the stop" in blob or "the target" in blob:
        return "price"
    if "e[r]" in blob or "mean r" in blob:
        return "r"
    if "broker net" in blob:
        return "money"
    if "the lot " in blob or blob.rstrip(".").endswith("the lot"):
        return "lots"
    if "fluid count" in blob or "envelope count" in blob or "promotion count" in blob:
        return "count"
    if "how many" in blob:
        return "count"
    if name.startswith("a1_") and name.endswith("_parameter"):
        return "price"
    return None


def _is_ordinal(qid: str) -> bool:
    """True when this id was built as words, or no amount unit is known."""

    key = str(qid)
    if key in _AMOUNT_UNIT:
        return False
    if key in _ORDINAL_WIDTH:
        return True
    return _amount_unit(key, "") is None


def _key_unit(name: str, unit: str) -> bool:
    low = str(name).lower()
    if unit == "price":
        return low in _PRICE_KEYS
    if unit == "hours":
        return low == "hour" or low.endswith("_hour") or low.endswith("_hours")
    if unit == "minutes":
        return low == "minute" or low.endswith("_minute") or low.endswith("_minutes") or low.endswith("_min")
    if unit == "seconds":
        return "second" in low or low in {"age_s", "seconds_until_cycle"}
    if unit == "lots":
        return low in {"volume", "volume_min", "volume_step", "lot", "lots", "min_lot"} or low.endswith("_lot") or low.endswith("_lots")
    if unit == "r":
        return low.endswith("_r") or low in {"plan_r", "locked_r", "mean_r"}
    if unit == "weight":
        return low == "weight" or low.endswith("_weight")
    if unit == "money":
        return low in _MONEY_KEYS
    if unit == "probability":
        return "prob" in low or low.startswith("p_") or "p_time" in low or "p_positive" in low
    if unit == "count":
        return low in {"n", "asked", "step_index"} or low.startswith("n_") or low.endswith("_count") or low.endswith("_len") or low.endswith("_posts")
    if unit == "multiple":
        return low.endswith("_mult") or low.endswith("_multiple")
    return False


def _walk_pairs(state, unit: str) -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []

    def walk(blob, depth: int) -> None:
        if depth > 4 or not isinstance(blob, dict):
            return
        for key, value in blob.items():
            name = str(key)
            if name in _SKIP_WALK or name.startswith("_"):
                continue
            if not _label_ok(name):
                continue
            if isinstance(value, dict):
                walk(value, depth + 1)
                continue
            if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
                if unit == "count":
                    found.append((f"the count of {name} named on this card", float(len(value))))
                continue
            if unit == "count" and not _key_unit(name, unit):
                continue
            if unit != "count" and not _key_unit(name, unit):
                continue
            number = _anchor_finite(value)
            if number is None:
                continue
            found.append((f"the {name} named on this card", number))

    if isinstance(state, dict):
        walk(state, 0)
    return found


def _distinct(pairs) -> int:
    seen = []
    for _label, value in pairs:
        if value not in seen:
            seen.append(value)
    return len(seen)


def _anchors_for(state, unit: str) -> list[tuple[str, float]]:
    card = state if isinstance(state, dict) else {}
    if unit == "count":
        extra = []
        try:
            from .jev_questions import count_anchors

            extra = list(count_anchors(card) or [])
        except Exception:
            try:
                from src.judgment.jev_questions import count_anchors

                extra = list(count_anchors(card) or [])
            except Exception:
                extra = []
        return list(extra) + _walk_pairs(card, "count")
    if unit == "money":
        extra = []
        try:
            from .jev_questions import usd_anchors

            extra = list(usd_anchors(card) or [])
        except Exception:
            try:
                from src.judgment.jev_questions import usd_anchors

                extra = list(usd_anchors(card) or [])
            except Exception:
                extra = []
        return list(extra) + _walk_pairs(card, "money")
    if unit == "minutes":
        extra = []
        try:
            from .jev_questions import minute_anchors

            extra = list(minute_anchors(card) or [])
        except Exception:
            try:
                from src.judgment.jev_questions import minute_anchors

                extra = list(minute_anchors(card) or [])
            except Exception:
                extra = []
        return list(extra) + _walk_pairs(card, "minutes")
    if unit == "size":
        lots = _walk_pairs(card, "lots")
        multiples = _walk_pairs(card, "multiple")
        try:
            from .jev_questions import mult_anchors

            multiples = list(mult_anchors(card) or []) + multiples
        except Exception:
            try:
                from src.judgment.jev_questions import mult_anchors

                multiples = list(mult_anchors(card) or []) + multiples
            except Exception:
                pass
        if _distinct(lots) >= 2:
            return lots
        if _distinct(multiples) >= 2:
            return multiples
        return []
    if unit == "window":
        minutes = _walk_pairs(card, "minutes")
        seconds = _walk_pairs(card, "seconds")
        if _distinct(minutes) >= 2:
            return minutes
        return seconds
    return _walk_pairs(card, unit)


def _custom_words(words) -> bool:
    """A scale of words is an ordinal. The generic parameter menu is not."""

    if not words:
        return False
    texts = []
    numeric = 0
    for item in words:
        text = str(item).strip()
        if not text:
            continue
        try:
            float(text)
            numeric += 1
        except (TypeError, ValueError):
            pass
        texts.append(text)
    if len(texts) < 2 or numeric == len(texts):
        return False
    generic = {
        ("none", "trace", "small", "modest", "notable", "heavy"),
        (
            "below the levels on this state",
            "between the levels on this state",
            "above the levels on this state",
        ),
    }
    return tuple(texts) not in generic


def _word_levels(words) -> list[str]:
    if not words:
        return list(_ORDINAL_WORDS)
    texts = []
    numeric = 0
    for item in words:
        text = str(item).strip()
        if not text:
            continue
        try:
            float(text)
            numeric += 1
        except (TypeError, ValueError):
            pass
        texts.append(text)
    if texts and numeric == len(texts):
        return [item for item in _ORDINAL_WORDS if _label_ok(item)]
    kept = [item for item in texts if _label_ok(item)]
    if len(kept) >= 2:
        return kept
    return [item for item in _ORDINAL_WORDS if _label_ok(item)]


def _jev_amount(qid, text, anchors):
    try:
        from .jev_questions import amount_question

        return amount_question(qid, text, anchors)
    except Exception:
        from src.judgment.jev_questions import amount_question

        return amount_question(qid, text, anchors)


def _jev_ordinal(qid, text, levels):
    try:
        from .jev_questions import ordinal_question

        return ordinal_question(qid, text, levels)
    except Exception:
        from src.judgment.jev_questions import ordinal_question

        return ordinal_question(qid, text, levels)


def _shape_score(qid: str, instructions: str, words=None, *, wrapped: bool = True):
    """An amount posts only with two anchors. An ordinal keeps its words."""

    text = str(instructions or "").strip()
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            cleaned = scrub(text)
        except Exception:
            return {}
        if not isinstance(cleaned, str) or not cleaned.strip():
            return {}
        text = cleaned.strip()
    if not text or not _label_ok(text):
        return {}
    unit = None if _custom_words(words) else _amount_unit(qid, text)
    try:
        if unit is None:
            built = _jev_ordinal(qid, text, _word_levels(words))
        else:
            anchors = [
                (label, value)
                for label, value in _anchors_for(_bound_card(), unit)
                if _label_ok(label)
            ]
            built = _jev_amount(qid, text, anchors)
    except Exception:
        return {}
    row = built.get(str(qid)) if isinstance(built, dict) else None
    if not isinstance(row, dict):
        return {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        row.pop(key, None)
    criteria = row.get("criteria")
    if not isinstance(criteria, list) or len(criteria) < 2:
        return {}
    if unit is None:
        _ORDINAL_WIDTH[str(qid)] = len(criteria)
        _AMOUNT_UNIT.pop(str(qid), None)
    else:
        _AMOUNT_UNIT[str(qid)] = unit
        _ORDINAL_WIDTH.pop(str(qid), None)
    row["type"] = "score"
    row["instructions"] = text
    if wrapped:
        return {str(qid): row}
    return row


def _ordinal_read(block, qid: str):
    """Nearest word. The index is not an amount. A miss stays unset."""

    width = _ORDINAL_WIDTH.get(str(qid))
    if not isinstance(width, int) or width < 2:
        criteria = block.get("criteria") if isinstance(block, dict) else None
        if isinstance(criteria, list) and len(criteria) >= 2:
            width = len(criteria)
        else:
            probs = block.get("probabilities") if isinstance(block, dict) else None
            if isinstance(probs, dict) and len(probs) >= 2:
                width = len(probs)
    if not isinstance(width, int) or width < 2:
        return None
    try:
        from .jev_questions import ordinal_index
    except Exception:
        try:
            from src.judgment.jev_questions import ordinal_index
        except Exception:
            return None
    try:
        return ordinal_index(block, width)
    except Exception:
        return None

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _skip_key(key: str) -> bool:
    low = key.lower()
    return any(part in low for part in _SKIP_KEY_PARTS)


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
    if seen is None:
        seen = set()
    if value is None or isinstance(value, (str, bool)):
        return value
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


def _attr(obj: Any, *names: str) -> Any:
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            return obj.get(name)
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _identity(subject: Any) -> dict[str, Any]:
    if isinstance(subject, Mapping):
        plain = _plain(subject)
        return plain if isinstance(plain, dict) else {}
    if isinstance(subject, str):
        return {"subject": subject}
    number = _number(subject)
    if number is not None:
        return {"ticket": int(number) if number.is_integer() else number}
    out: dict[str, Any] = {}
    for name in (
        "symbol",
        "sleeve",
        "side",
        "ticket",
        "candidate_id",
        "login",
        "ns",
        "tag",
        "direction",
    ):
        value = _attr(subject, name)
        if value is None:
            continue
        plain = _plain(value)
        if plain is not None:
            out[name] = plain
    return out


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(value) for key, value in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(body["criteria"]))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {str(key): str(value) for key, value in criteria.items()}
    return body


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    """Amount anchors from this card. An ordinal keeps its words."""
    return _shape_score(qid, instructions, None, wrapped=False)



def _noul_question(instructions: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": {
            "true": "The component exists on this step.",
            "false": "The component does not exist on this step.",
        },
    }


def life_questions(step: str) -> dict[str, dict[str, Any]]:
    """Choice, threshold, loop bound, parameter, and component for one step.

    The menu names what an answer may return. It does not decide.
    """

    criteria = STEP_CRITERIA[step]
    noun = "stop or target" if step == "manage" else "parameter"
    legal = ""
    if step == "place":
        legal = "place is a legal winner when it is that option. "
    elif step == "manage":
        legal = "close is a legal winner when it is that option. "
    pack = {
        step: _choice_question(
            step,
            (
                f"{step} question for this candidate or ticket. "
                "Pick one option. The choice is the single highest probability. "
                f"{legal}"
                "An empty answer or a tie leaves the choice unset. "
                "This question does not send."
            ),
            criteria,
        ),
        f"{step}_threshold": _score_question(
            f"{step}_threshold",
            (
                f"The score you return is the threshold for the {step} step. "
                "It may sit between the levels. "
                "An empty score leaves the threshold unset."
            ),
        ),
        f"{step}_loop": _score_question(
            f"{step}_loop",
            (
                f"The score you return is the loop bound for the {step} step. "
                "On manage, that bound is how many manage steps this life passes. "
                "It may sit between the levels. "
                "An empty score leaves the bound unset."
            ),
        ),
        f"{step}_parameter": _score_question(
            f"{step}_parameter",
            (
                f"The score you return is the {noun} for the {step} step. "
                "It may sit between the levels. "
                "An empty score leaves the parameter unset."
            ),
        ),
        f"{step}_component": _choice_question(
            f"{step}_component",
            (
                f"Which component exists on this {step} step for this candidate or ticket? "
                "The option with the single highest probability is that component. "
                "A tie or an empty answer leaves the component unset."
            ),
            COMPONENT_CRITERIA,
        ),
        f"{step}_component_exists": _noul_question(
            (
                f"Does the component on this {step} step exist for this candidate or ticket? "
                "The noul you return is that existence. "
                "An empty noul leaves existence unset."
            )
        ),
    }
    pack = {
        key: value
        for key, value in pack.items()
        if isinstance(value, dict) and value.get("type") in {"noul", "choice", "score"}
    }
    return pack


def _probabilities(block: Any) -> dict[str, float]:
    raw = block.get("probabilities") if isinstance(block, dict) else None
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _number(value)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique(probabilities: Mapping[str, Any] | None, order: tuple[str, ...]) -> tuple[str | None, float | None]:
    """Unique highest probability. A tie, an empty map, or a bare label is unset."""

    if not isinstance(probabilities, Mapping) or not probabilities:
        return None, None
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, value in probabilities.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _number(value)
        if number is None:
            continue
        numeric[name] = number
    if not numeric:
        return None, None
    best = max(numeric.values())
    winners = [name for name in order if name in numeric and numeric[name] == best]
    if len(winners) != 1:
        return None, None
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(numeric, order)
    except Exception:
        agreed = winners[0]
    if agreed is None or str(agreed) != winners[0]:
        return None, None
    return winners[0], numeric[winners[0]]


def _as_block(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    number = _number(raw)
    if number is None:
        return {}
    return {"score": number}


def _score_value(raw: Any, qid: str | None = None) -> float | None:
    """The returned score. A tie leaves it unset. The number is not snapped to a level."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(raw, str(qid))


    block = _as_block(raw)
    numeric = _probabilities(block)
    if numeric and _unique(numeric, tuple(numeric))[0] is None:
        return None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(block))
        if parsed is not None:
            return parsed
    except Exception:
        pass
    for key in ("score", "value"):
        parsed = _number(block.get(key))
        if parsed is not None:
            return parsed
    return None


def _noul_value(raw: Any) -> bool | float | None:
    """A Noul stays a bool or a probability. Missing stays missing."""

    block = raw if isinstance(raw, dict) else {}
    if "noul" in block:
        value = block.get("noul")
    elif "Noul" in block:
        value = block.get("Noul")
    else:
        return None
    if value is True or value is False:
        return value
    return _number(value)


def _outcome_pairs(row: Mapping[str, Any], step: str) -> tuple[tuple[str, Any], ...]:
    return (
        (step, row.get("choice")),
        (f"{step}_threshold", row.get("threshold")),
        (f"{step}_loop", row.get("loop_bound")),
        (f"{step}_parameter", row.get("parameter")),
        (f"{step}_component", row.get("component")),
        (f"{step}_component_exists", row.get("component_exists")),
    )


def _local_priors(questions: Mapping[str, Any]) -> list[dict[str, Any]]:
    """History for the next ask. The current return is not read back out of it."""

    del questions
    return [dict(item) for item in _LOCAL_OUTCOMES]


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = _local_priors(questions)
        return
    state["prior_outcomes"] = loaded if isinstance(loaded, list) else []


def _remember(state: Mapping[str, Any], row: Mapping[str, Any], step: str) -> None:
    pairs = _outcome_pairs(row, step)
    error = row.get("error")
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value in pairs:
            _LOCAL_OUTCOMES.append({
                "key": key,
                "value": value,
                "role": state.get("role"),
                "error": None if value is not None else error,
            })
        return
    for key, value in pairs:
        try:
            append_outcome(key, value, state, error=None if value is not None else error)
        except Exception:
            return


def _post(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    ask: Callable[..., Any] | None,
) -> dict[str, Any]:
    call = ask
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    receipt = call(state, questions=questions, merge_sleeve=False)
    return receipt if isinstance(receipt, dict) else {"error": "evaluate_not_a_dict"}


def _blank(role: str, step: str, error: str | None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "logged_at_utc": _now(),
        "role": role,
        "step": step,
        "choice": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "component": None,
        "component_exists": None,
        "probabilities": {},
        "component_probabilities": {},
        "unique_highest": False,
        "model": MODEL,
        "error": error,
    }


def _ask(
    state: dict[str, Any],
    step: str,
    ask: Callable[..., Any] | None,
) -> dict[str, Any]:
    """One System One ask. A miss stays unset."""

    _bind_card(state)
    role = str(state.get("role") or "")
    questions = life_questions(step)
    state["step"] = step
    state["model"] = MODEL
    _attach_priors(state, questions)
    try:
        receipt = _post(state, questions, ask)
    except Exception as exc:  # noqa: BLE001 — a dark ask must not raise into the life
        row = _blank(role, step, type(exc).__name__)
        _remember(state, row, step)
        return row
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    choice_order = tuple(STEP_CRITERIA[step])
    choice, _probability = _unique(_probabilities(answers.get(step)), choice_order)
    component, _component_p = _unique(
        _probabilities(answers.get(f"{step}_component")),
        tuple(COMPONENT_CRITERIA),
    )
    row = _blank(role, step, None if error in (None, "") else str(error))
    if answers:
        choice_probs = _probabilities(answers.get(step))
        component_probs = _probabilities(answers.get(f"{step}_component"))
        row["choice"] = choice
        row["threshold"] = _score_value(answers.get(f"{step}_threshold"), f"{step}_threshold")
        row["loop_bound"] = _score_value(answers.get(f"{step}_loop"), f"{step}_loop")
        row["parameter"] = _score_value(answers.get(f"{step}_parameter"), f"{step}_parameter")
        row["component"] = component
        row["component_exists"] = _noul_value(answers.get(f"{step}_component_exists"))
        row["probabilities"] = {key: choice_probs[key] for key in choice_order if key in choice_probs}
        row["component_probabilities"] = {
            key: component_probs[key] for key in COMPONENT_CRITERIA if key in component_probs
        }
        row["unique_highest"] = choice is not None
    if receipt.get("model"):
        row["model"] = receipt.get("model")
    _remember(state, row, step)
    return row


def _manage_life(state: dict[str, Any], ask: Callable[..., Any] | None) -> list[dict[str, Any]]:
    """Every manage step for this life.

    The first returned loop bound is how many manage steps are asked.
    A missing bound does not add another step and does not fill a count.
    """

    steps: list[dict[str, Any]] = []
    bound: float | None = None
    while True:
        row = _ask(state, "manage", ask)
        steps.append(row)
        if bound is None:
            bound = _number(row.get("loop_bound"))
        if bound is None or len(steps) >= bound:
            break
    return steps


def pass_life(
    subject: Any,
    *,
    role: str,
    facts: Mapping[str, Any] | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Watch, observe, admit, place, then every manage step. The returns decide."""

    state: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "role": role,
        "identity": _identity(subject),
    }
    if facts:
        plain = _plain(dict(facts))
        if isinstance(plain, dict):
            state["facts"] = plain
    steps = [_ask(state, step, ask) for step in LIFE]
    steps.extend(_manage_life(state, ask))
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "role": role,
        "steps": steps,
    }


def evaluate_candidate_and_ticket(
    candidate: Any,
    ticket: Any,
    *,
    facts: Mapping[str, Any] | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Both pass the whole life. Each ask carries prior outcomes. Nothing is sent."""

    return {
        "schema": SCHEMA,
        "model": MODEL,
        "candidate": pass_life(candidate, role="candidate", facts=facts, ask=ask),
        "ticket": pass_life(ticket, role="ticket", facts=facts, ask=ask),
    }


def intent_to_state(
    intent: Any,
    *,
    tick: Any = None,
    skip_reason: str | None = None,
    writer_stage: str | None = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Facts for one ask. Missing fields stay missing."""

    state = _identity(intent)
    if tick is not None:
        plain_tick = _plain(tick)
        if plain_tick is not None:
            state["tick"] = plain_tick
    if skip_reason is not None:
        state["skip_reason"] = skip_reason
    if writer_stage is not None:
        state["writer_stage"] = writer_stage
    if occupancy is not None:
        state["occupancy"] = _plain(occupancy)
    if governor is not None:
        state["governor"] = _plain(governor)
    if extra:
        plain = _plain(dict(extra))
        if isinstance(plain, dict):
            for key, value in plain.items():
                if key not in state:
                    state[key] = value
    return state


def observe_gate(
    gate_id: str,
    state: dict[str, Any] | None,
    *,
    skip_reason: str | None = None,
    writer_stage: str | None = None,
    extra: dict[str, Any] | None = None,
    questions: Mapping[str, Any] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
    cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """The candidate and the ticket pass the life. ``gate_id`` is context."""

    del questions, cache
    payload = intent_to_state(
        state,
        skip_reason=skip_reason,
        writer_stage=writer_stage,
        extra=extra,
    )
    payload["gate_id"] = str(gate_id)
    candidate = payload.get("candidate", payload)
    ticket = payload.get("ticket")
    return evaluate_candidate_and_ticket(
        candidate,
        ticket,
        facts=payload,
        ask=evaluate_fn,
    )


def observe_intent(
    intent: Any,
    *,
    skip_reason: str | None,
    writer_stage: str,
    tick: Any = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
    cache: dict[str, dict[str, Any]] | None = None,
    prefer_s12_helper: bool = True,
) -> dict[str, Any]:
    """The intent's candidate and ticket pass the life. The returns decide."""

    del cache, prefer_s12_helper
    facts = intent_to_state(
        intent,
        tick=tick,
        skip_reason=skip_reason,
        writer_stage=writer_stage,
        occupancy=occupancy,
        governor=governor,
        extra=extra,
    )
    ticket = _attr(intent, "ticket")
    if ticket is None and isinstance(extra, Mapping):
        ticket = extra.get("ticket")
    return evaluate_candidate_and_ticket(
        intent,
        ticket,
        facts=facts,
        ask=evaluate_fn,
    )
