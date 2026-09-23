"""Chair five-label stamp on the live Challenge compose / observe path.

Shadow log only. The stamp does not place, remint, flatten, or arm A+.
One hop is ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False`` (POST https://api.typesafe.ai/v1/systemone).
Every decision on the five labels, including each parameter, is that
return. A return is a Noul, a Choice, or a Score. A Score may sit
between levels. Prior outcomes are attached on the ask, and the return
is stored for the next ask.

An empty answer, a tie, a missing score, or an error leaves that field
unset and does not restore a constant. Floor and baseline are not a
question. This module does not send.

Maps ALIVE_MENU / CONF_GATE / FANOUT_BOOK / DONE_OUTSIDE / USAGE_ROUTER
onto the stamp. Sidecar inventory is read when it imports, and is not
the decision. Admit criteria stay ``admit`` / ``abstain`` / ``hard_refuse``.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Mapping

SCHEMA = "gtos.judgment.chair_shadow.v0"
MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

ADMIT_OPTIONS = ("admit", "abstain", "hard_refuse")
CONSUME_BRANCHES = ("flow_alignment", "cost_hurtful", "admit")
EVENT_BRANCHES = (
    "event_proximity",
    "calendar_honest",
    "event_size",
    "veto_event",
    "high_in_f5_window",
    "minutes_to_nearest",
    "warsh_class",
    "spine_empty_honesty",
)
USAGE_SEATS = ("cheap_label", "chair_read", "browser_scout", "deep_reason", "defer")
EXPENSIVE_SEATS = ("chair_read", "browser_scout", "deep_reason")
EXPENSIVE_SEATS_PLAN = ("chair", "browser", "deep_llm")
USAGE_DESTINATIONS = ("defer", "jev_fluid_fanout", "local_only", "fail_closed")
BANDS = ("LOW", "MED", "HIGH", "ABSENT")
BEHAVIORS = ("SHADOW", "SHADOW_REVIEW", "ELIGIBLE_LATER_ONLY")
COMPONENTS = ("alive_menu", "conf_gate", "fanout_book", "done_outside", "usage_router")
WRITER_OWNS = (
    "place",
    "remint",
    "flatten",
    "ENV-KILL",
    "ENV-TWO-STOP",
    "ENV-TOKEN",
    "ENV-H8",
    "ENV-DD",
    "ENV-US30",
    "ENV-OCC",
    "ENV-DEAD",
    "two_stop_count",
    "token_digest",
)

_LIMIT_KEYS = frozenset(
    {
        "floor",
        "baseline",
        "day_start_baseline",
        "static_floor",
        "pass_line",
        "flatten_floor_usd",
        "daily_loss_pct",
        "floor_room",
    }
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
_NOUL_ORDER = ("true", "false")
_ALLOWED_TYPES = frozenset({"noul", "choice", "score"})

# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []



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

def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


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
    return "".join(kept)


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before the ask."""

    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    return None


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


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision. A miss is not zero."""

    if not probs:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    allowed = order or tuple(probs)
    for name in allowed:
        if name not in probs:
            continue
        p = probs[name]
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if tied or best is None:
        return None
    return best


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    probs = _probs(block)
    if not probs:
        return None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probs, order)
    except Exception:
        picked = _unique(probs, order)
    if picked is None or str(picked) not in order:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A missing noul stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice(block, _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any, qid: str | None = None) -> float | None:
    """The returned score. It is not snapped to a level."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))


    if not isinstance(block, dict) or block.get("error"):
        return None
    if "score" in block and block.get("score") is not None:
        number = _finite(block.get("score"))
        if number is None:
            return None
        try:
            from .jev_questions import returned_number

            parsed = _finite(returned_number(block))
        except Exception:
            return number
        if parsed is None or parsed != number:
            return None
        return number
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        return None


def _miss(block: Any, value: Any, order: tuple[str, ...], receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if receipt_error not in (None, ""):
        return str(receipt_error)
    probs = _probs(block)
    if probs and _unique(probs, order or tuple(probs)) is None:
        return "tie"
    return "empty"


def _yes(value: bool | float | None) -> bool | None:
    """An actual bool is a decided noul. A probability is not a cutoff."""

    if value is True:
        return True
    if value is False:
        return False
    return None


def _choice_question(qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {key: _scrub_text(val) for key, val in criteria.items()}
    body: dict[str, Any] = {"type": "choice", "instructions": text, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, cleaned)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "choice"
            shaped["instructions"] = text
            shaped["criteria"] = cleaned
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    """Amount anchors from this card. An ordinal keeps its words."""
    return _shape_score(qid, instructions, None, wrapped=True)



def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(instructions),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _questions() -> dict[str, Any]:
    """One pack. Types are noul, choice, or score. Floor and baseline are absent."""

    pack: dict[str, Any] = {}
    pack.update(
        _choice_question(
            "chair_admit",
            "Which admit label is this chair shadow state? "
            "The option you return is that label. "
            "An empty answer or a tie leaves the label unset. "
            "This question does not send.",
            {
                "admit": "Admit on this state.",
                "abstain": "Abstain on this state.",
                "hard_refuse": "Hard refuse on this state.",
            },
        )
    )
    pack.update(
        _choice_question(
            "chair_band",
            "What confidence band is this chair shadow state? "
            "Confidences on the state are facts. "
            "The option you return is the band. "
            "An empty answer or a tie leaves the band unset. "
            "This question does not send.",
            {
                "LOW": "The band on this state is low.",
                "MED": "The band on this state is mid.",
                "HIGH": "The band on this state is high.",
                "ABSENT": "No confidence band is present on this state.",
            },
        )
    )
    pack.update(
        _choice_question(
            "chair_behavior",
            "What shadow behavior follows this chair state? "
            "The option you return is that behavior. "
            "An empty answer or a tie leaves the behavior unset. "
            "This question does not send.",
            {
                "SHADOW": "This state stays a shadow log.",
                "SHADOW_REVIEW": "This state stays in shadow review.",
                "ELIGIBLE_LATER_ONLY": "This state is eligible later only.",
            },
        )
    )
    pack.update(
        _choice_question(
            "chair_route",
            "Which usage seat is the route on this chair state? "
            "A requested seat on the state is a fact. "
            "The option you return is the route. "
            "An empty answer or a tie leaves the route unset. "
            "This question does not send.",
            {
                "cheap_label": "The route is the cheap label.",
                "chair_read": "The route is a chair read.",
                "browser_scout": "The route is a browser scout.",
                "deep_reason": "The route is deep reason.",
                "defer": "The route is defer.",
            },
        )
    )
    pack.update(
        _choice_question(
            "chair_destination",
            "Where does this usage route land on this state? "
            "Env flags on the state are facts. "
            "The option you return is the destination. "
            "An empty answer or a tie leaves the destination unset. "
            "This question does not send.",
            {
                "defer": "Land on defer.",
                "jev_fluid_fanout": "Land on the fluid fanout.",
                "local_only": "Land on the local stamp only.",
                "fail_closed": "Land closed.",
            },
        )
    )
    pack.update(
        _choice_question(
            "chair_component",
            "Which chair shadow component exists on this state? "
            "The option you return is that component. "
            "An empty answer or a tie leaves the component unset. "
            "This question does not send.",
            {
                "alive_menu": "The alive menu is the component on this state.",
                "conf_gate": "The confidence gate is the component on this state.",
                "fanout_book": "The fanout book is the component on this state.",
                "done_outside": "Done-outside is the component on this state.",
                "usage_router": "The usage router is the component on this state.",
            },
        )
    )
    pack.update(
        _noul_question(
            "chair_integer_only",
            "Does this fanout drop to integer only on this state? "
            "The calls remaining on the state are a fact. "
            "The noul you return is that drop. "
            "An empty noul leaves it unset. "
            "This question does not send.",
            "This fanout drops to integer only.",
            "This fanout keeps the named questions.",
        )
    )
    pack.update(
        _noul_question(
            "chair_ignore_event",
            "Are the event branches ignored on this fanout? "
            "Whether the news spine is empty is a fact on the state. "
            "The noul you return is that ignore. "
            "An empty noul leaves it unset. "
            "This question does not send.",
            "Event branches are ignored on this fanout.",
            "Event branches stay on this fanout.",
        )
    )
    pack.update(
        _noul_question(
            "chair_defer",
            "Does this usage route defer on this state? "
            "The noul you return is that defer. "
            "An empty noul leaves it unset. "
            "This question does not send.",
            "This usage route defers.",
            "This usage route does not defer.",
        )
    )
    pack.update(
        _noul_question(
            "chair_aplus_off",
            "Is the A+ observation default off on this state? "
            "The noul you return is that default. "
            "An empty noul leaves it unset. "
            "This question does not send.",
            "The A+ observation default is off.",
            "The A+ observation default is not off.",
        )
    )
    pack.update(
        _noul_question(
            "chair_jev_done",
            "Is the outside work done on this state? "
            "The noul you return is that completion. "
            "An empty noul leaves it unset. "
            "This question does not send.",
            "The outside work is done.",
            "The outside work is not done.",
        )
    )
    pack.update(
        _noul_question(
            "chair_artifact_ok",
            "Do the artifacts on this state verify? "
            "The noul you return is that check. "
            "An empty noul leaves it unset. "
            "This question does not send.",
            "The artifacts on this state verify.",
            "The artifacts on this state do not verify.",
        )
    )
    pack.update(
        _noul_question(
            "chair_fail_closed",
            "Does this admit fail closed on this state? "
            "The noul you return is that close. "
            "An empty noul leaves it unset. "
            "This question does not send.",
            "This admit fails closed.",
            "This admit does not fail closed.",
        )
    )
    pack.update(
        _noul_question(
            "chair_component_exists",
            "Does the chair shadow component on this state exist? "
            "The noul you return is that existence. "
            "An empty noul leaves it unset. "
            "This question does not send.",
            "The component exists on this state.",
            "The component does not exist on this state.",
        )
    )
    pack.update(
        _score_question(
            "chair_conf_low",
            "The score you return is the low confidence starter on this state. "
            "It may sit between the levels. "
            "An empty score leaves the starter unset. "
            "This question does not send.",
        )
    )
    pack.update(
        _score_question(
            "chair_conf_high",
            "The score you return is the high confidence starter on this state. "
            "It may sit between the levels. "
            "An empty score leaves the starter unset. "
            "This question does not send.",
        )
    )
    pack.update(
        _score_question(
            "chair_confidence",
            "The score you return is the confidence on this chair state. "
            "Per-question confidences on the state are facts. "
            "It may sit between the levels. "
            "An empty score leaves the confidence unset. "
            "This question does not send.",
        )
    )
    pack.update(
        _score_question(
            "chair_cap",
            "The score you return is the alive-menu choice cap on this state. "
            "It may sit between the levels. "
            "An empty score leaves the cap unset. "
            "This question does not send.",
        )
    )
    pack.update(
        _score_question(
            "chair_threshold",
            "The score you return is the threshold for this chair shadow. "
            "It may sit between the levels. "
            "An empty score leaves the threshold unset. "
            "This question does not send.",
        )
    )
    pack.update(
        _score_question(
            "chair_loop",
            "The score you return is the loop bound for this chair shadow. "
            "It may sit between the levels. "
            "An empty score leaves the bound unset. "
            "This question does not send.",
        )
    )
    pack.update(
        _score_question(
            "chair_parameter",
            "The score you return is the parameter for this chair shadow. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "This question does not send.",
        )
    )
    clean: dict[str, Any] = {}
    for qid, block in pack.items():
        if not isinstance(block, dict) or block.get("type") not in _ALLOWED_TYPES:
            continue
        blob = json.dumps(block, default=str).lower()
        if _limit_key(qid) or _limit_key(blob) or any(token.lower() in blob for token in _BANNED_TEXT):
            continue
        clean[qid] = block
    return clean


_CHOICE_ORDERS = {
    "chair_admit": ADMIT_OPTIONS,
    "chair_band": BANDS,
    "chair_behavior": BEHAVIORS,
    "chair_route": USAGE_SEATS,
    "chair_destination": USAGE_DESTINATIONS,
    "chair_component": COMPONENTS,
}
_NOUL_IDS = (
    "chair_integer_only",
    "chair_ignore_event",
    "chair_defer",
    "chair_aplus_off",
    "chair_jev_done",
    "chair_artifact_ok",
    "chair_fail_closed",
    "chair_component_exists",
)
_SCORE_IDS = (
    "chair_conf_low",
    "chair_conf_high",
    "chair_confidence",
    "chair_cap",
    "chair_threshold",
    "chair_loop",
    "chair_parameter",
)
_VALUE_OF = {
    "chair_admit": "admit",
    "chair_band": "band",
    "chair_behavior": "behavior",
    "chair_route": "route",
    "chair_destination": "destination",
    "chair_component": "component",
    "chair_integer_only": "integer_only",
    "chair_ignore_event": "ignore_event",
    "chair_defer": "defer",
    "chair_aplus_off": "aplus_off",
    "chair_jev_done": "jev_done",
    "chair_artifact_ok": "artifact_ok",
    "chair_fail_closed": "fail_closed",
    "chair_component_exists": "component_exists",
    "chair_conf_low": "conf_low",
    "chair_conf_high": "conf_high",
    "chair_confidence": "confidence",
    "chair_cap": "cap",
    "chair_threshold": "threshold",
    "chair_loop": "loop_bound",
    "chair_parameter": "parameter",
}


def _blank() -> dict[str, Any]:
    return {name: None for name in _VALUE_OF.values()}


def _read(answers: Mapping[str, Any] | None, receipt_error: str | None) -> dict[str, Any]:
    payload = answers if isinstance(answers, Mapping) else {}
    card = _blank()
    errors: dict[str, str | None] = {}
    for qid, order in _CHOICE_ORDERS.items():
        block = payload.get(qid)
        value = _choice(block, order)
        name = _VALUE_OF[qid]
        card[name] = value
        errors[qid] = _miss(block, value, order, receipt_error)
    for qid in _NOUL_IDS:
        block = payload.get(qid)
        value = _noul(block)
        card[_VALUE_OF[qid]] = value
        errors[qid] = _miss(block, value, _NOUL_ORDER, receipt_error)
    for qid in _SCORE_IDS:
        block = payload.get(qid)
        value = _score(block, qid)
        card[_VALUE_OF[qid]] = value
        errors[qid] = _miss(block, value, (), receipt_error)
    card["errors"] = errors
    card["ask_error"] = receipt_error
    return card


def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _spine_empty(state: Mapping[str, Any]) -> bool | None:
    news = state.get("news")
    if not isinstance(news, dict) or "spine_empty" not in news:
        return None
    raw = news.get("spine_empty")
    if raw is True or raw is False:
        return raw
    return None


def _confidence_facts(answers: Mapping[str, Any]) -> dict[str, float]:
    found: dict[str, float] = {}
    for key, block in answers.items():
        name = str(key)
        if _limit_key(name) or not isinstance(block, dict) or "confidence" not in block:
            continue
        number = _finite(block.get("confidence"))
        if number is None or number < 0.0 or number > 1.0:
            continue
        found[name] = number
    return found


def _text_fact(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return _scrub_text(text)


def _bool_fact(value: Any) -> bool | None:
    if value is True or value is False:
        return value
    return None


def _admit_fact(extra: Mapping[str, Any]) -> dict[str, Any] | None:
    raw = extra.get("admit_resolved")
    if not isinstance(raw, dict):
        return None
    cleaned = _scrub(
        {
            "choice": _text_fact(raw.get("choice")),
            "source": _text_fact(raw.get("source")),
            "fail_closed": _bool_fact(raw.get("fail_closed")),
        }
    )
    return cleaned if isinstance(cleaned, dict) else None


def _error_text(exc: BaseException) -> str:
    text = _scrub_text(f"{type(exc).__name__}: {exc}")
    return text or type(exc).__name__


def _catalog() -> tuple[list[str] | None, list[str] | None, list[str] | None]:
    try:
        from .jev_questions import GATE_SEAT_IDS, gold_fanout_questions

        questions = gold_fanout_questions()
    except Exception:
        return None, None, None
    if not isinstance(questions, dict):
        return None, None, None
    ids = sorted(str(key) for key in questions if not _limit_key(str(key)))
    choice_ids = [
        str(key)
        for key, block in questions.items()
        if isinstance(block, dict) and str(block.get("type") or "") == "choice" and not _limit_key(str(key))
    ]
    try:
        seats = [str(item) for item in GATE_SEAT_IDS if not _limit_key(str(item))]
    except Exception:
        seats = None
    return ids, seats, choice_ids


def _calls_remaining() -> float | None:
    try:
        from .jev_client import calls_remaining

        return _finite(calls_remaining())
    except Exception:
        return None


def _menu_facts(extra: Mapping[str, Any]) -> dict[str, Any]:
    """Inventory reads. A missing module leaves the fact unset."""

    blank: dict[str, Any] = {
        "generated_this_cycle": None,
        "reused_prior_map": None,
        "offered_ids": None,
        "n_offered": None,
        "capped_fact": None,
        "menu_hash": None,
        "inventory_fingerprint": None,
        "stale_menu_events": None,
        "sidecar_notes": None,
        "choice_ids": None,
        "criteria_sha256": None,
        "n_fluid": None,
        "n_envelope": None,
        "sidecar_next_gate_ids": None,
        "inventory_option_cap": None,
        "envelope_ids": None,
        "forbidden_auto_effects": None,
        "unread": None,
    }
    try:
        from .alive_menu import AliveMenu, StaleMenuError, assert_menu_fresh, rebuild_choice_criteria
        from .fluid_gates import inventory_counts
        from .inventory import (
            ESCAPE_HATCHES,
            MAX_CHOICE_OPTIONS,
            LiveInventory,
            collect_live_inventory,
        )
        from .process_lock import ENVELOPE_WALL_IDS, FORBIDDEN_AUTO_EFFECTS
    except Exception as exc:
        blank["unread"] = type(exc).__name__
        return blank
    try:
        counts = inventory_counts()
        injected = extra.get("live_inventory")
        inventory = injected if isinstance(injected, LiveInventory) else collect_live_inventory()
        prior = extra.get("prior_menu")
        prior_menu = prior if isinstance(prior, AliveMenu) else None
        sidecar = rebuild_choice_criteria(inventory, prior_menu=prior_menu)
        stale: list[str] = []
        try:
            assert_menu_fresh(sidecar, inventory)
        except StaleMenuError as exc:
            stale.append(str(exc))
        if prior_menu is not None and sidecar.inventory_changed:
            stale.append("stale_menu_discarded_inventory_changed")
        offered = [str(item) for item in sidecar.option_ids]
        notes = [str(item) for item in sidecar.notes]
        envelope_ids = [str(item) for item in ENVELOPE_WALL_IDS if not _limit_key(str(item))]
        payload = {
            "offered_ids": offered,
            "inventory_fingerprint": inventory.fingerprint,
            "n_fluid": counts.get("n_fluid") if isinstance(counts, dict) else None,
            "n_envelope": counts.get("n_envelope") if isinstance(counts, dict) else None,
        }
        blank.update(
            {
                "generated_this_cycle": True,
                "reused_prior_map": False,
                "offered_ids": offered,
                "n_offered": len(offered),
                "capped_fact": "capped_at_255" in notes or "score_then_choice_truncated" in getattr(inventory, "notes", ()),
                "menu_hash": _sha256(payload),
                "inventory_fingerprint": inventory.fingerprint,
                "stale_menu_events": stale,
                "sidecar_notes": notes,
                "criteria_sha256": _sha256(payload),
                "n_fluid": payload["n_fluid"],
                "n_envelope": payload["n_envelope"],
                "sidecar_next_gate_ids": [str(item) for item in ESCAPE_HATCHES],
                "inventory_option_cap": _finite(MAX_CHOICE_OPTIONS),
                "envelope_ids": envelope_ids,
                "forbidden_auto_effects": sorted(str(item) for item in FORBIDDEN_AUTO_EFFECTS),
                "unread": None,
            }
        )
    except Exception as exc:
        blank["unread"] = type(exc).__name__
    return blank


def _observed(state: Mapping[str, Any]) -> dict[str, Any]:
    cleaned = _scrub(dict(state))
    if not isinstance(cleaned, dict):
        return {}
    cleaned.pop("prior_outcomes", None)
    return cleaned


def _payload(facts: Mapping[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "gate": "chair_shadow",
    }
    body.update(dict(facts))
    scrubbed = _scrub(body)
    if not isinstance(scrubbed, dict):
        return {"model": MODEL, "login": CHALLENGE_LOGIN, "namespace": CHALLENGE_NS, "gate": "chair_shadow"}
    scrubbed.pop("prior_outcomes", None)
    scrubbed["model"] = MODEL
    return scrubbed


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(state: Mapping[str, Any], card: Mapping[str, Any]) -> None:
    errors = card.get("errors") if isinstance(card.get("errors"), dict) else {}
    rows = [(qid, card.get(name), errors.get(qid)) for qid, name in _VALUE_OF.items()]
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in rows:
            _LOCAL_OUTCOMES.append(
                {
                    "spot": key,
                    "value": value,
                    "error": None if value is not None else error,
                }
            )
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=None if value is not None else error)
        except Exception:
            return


def _ask(facts: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. A miss stays unset."""

    _bind_card(facts)
    questions = _questions()
    allowed = _ALLOWED_TYPES
    if not questions or any(
        not isinstance(block, dict) or block.get("type") not in allowed for block in questions.values()
    ):
        card = _read({}, "question_pack_fail")
        card["invoked"] = None
        card["model"] = MODEL
        return card
    state = _payload(facts)
    _attach_priors(state, questions)
    try:
        from .jev_client import evaluate

        receipt = evaluate(state, questions=questions, merge_sleeve=False, model=MODEL)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        card = _read({}, _error_text(exc))
        card["invoked"] = None
        card["model"] = MODEL
        _remember(state, card)
        return card
    if not isinstance(receipt, dict):
        card = _read({}, "evaluate_not_a_dict")
        card["invoked"] = True
        card["model"] = MODEL
        _remember(state, card)
        return card
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None
    if not answers:
        raw = receipt.get("error") or receipt.get("skipped") or "empty"
        error = str(raw)
    card = _read(answers, error)
    card["invoked"] = True
    card["model"] = receipt.get("model") or MODEL
    _remember(state, card)
    return card


def _fanout_questions(catalog: list[str] | None, integer_only: bool | float | None) -> list[str] | None:
    decided = _yes(integer_only)
    if decided is None:
        return None
    if decided is True:
        return []
    return list(catalog) if catalog is not None else None


def _ignored(
    catalog: list[str] | None,
    ignore_event: bool | float | None,
) -> list[str] | None:
    decided = _yes(ignore_event)
    if decided is None:
        return None
    if decided is False:
        return []
    if catalog is None:
        return None
    return [key for key in EVENT_BRANCHES if key in catalog]


def _env_in_fanout(catalog: list[str] | None, envelope_ids: list[str] | None) -> list[str] | None:
    if catalog is None or envelope_ids is None:
        return None
    walls = set(envelope_ids)
    return [key for key in catalog if key in walls or str(key).startswith("ENV-")]


def _envelope_skipped(envelope_ids: list[str] | None) -> list[str] | None:
    if envelope_ids is None:
        return None
    return sorted(item for item in envelope_ids if str(item).startswith("ENV-"))


def _facts(
    state: Mapping[str, Any],
    answers: Mapping[str, Any],
    extra: Mapping[str, Any],
) -> dict[str, Any]:
    catalog, seats, choice_ids = _catalog()
    menu = _menu_facts(extra)
    requested = _text_fact(extra.get("usage_route"))
    if requested is None:
        requested = _text_fact(extra.get("route"))
    return {
        "observed": _observed(state),
        "spine_empty": _spine_empty(state),
        "confidences": _confidence_facts(answers),
        "defer_requested": _bool_fact(extra.get("defer")),
        "requested_route": requested,
        "fail_closed_requested": _bool_fact(extra.get("fail_closed")),
        "over_bar_budget": _bool_fact(extra.get("over_bar_budget")),
        "jev_done_choice": _text_fact(extra.get("jev_done_choice")),
        "admit_resolved_fact": _admit_fact(extra),
        "env_a1_log": _flag("GTOS_JEV_A1_LOG"),
        "env_alive_shadow": _flag("GTOS_JEV_ALIVE_SHADOW"),
        "calls_remaining": _calls_remaining(),
        "catalog_question_ids": catalog,
        "catalog_choice_ids": choice_ids,
        "gate_seat_ids": seats,
        "menu": {key: value for key, value in menu.items() if key != "unread"},
        "menu_unread": menu.get("unread"),
    }


def stamp_chair_shadow(
    state: dict[str, Any] | None = None,
    answers: dict[str, Any] | None = None,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach the five Chair labels. The decisions are the System One return.

    The stamp does not send.
    """

    _bind_card(state)
    state = state or {}
    answers = answers or {}
    extra = extra or {}
    facts = _facts(state, answers, extra)
    card = _ask(facts)
    menu = facts.get("menu") if isinstance(facts.get("menu"), dict) else {}
    catalog = facts.get("catalog_question_ids")
    catalog_ids = catalog if isinstance(catalog, list) else None
    envelope_ids = menu.get("envelope_ids") if isinstance(menu.get("envelope_ids"), list) else None
    questions = _fanout_questions(catalog_ids, card.get("integer_only"))
    ignored = _ignored(catalog_ids, card.get("ignore_event"))
    admit = card.get("admit")
    destination = card.get("destination")
    defer = card.get("defer")
    return {
        "schema": SCHEMA,
        "model": card.get("model") or MODEL,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "shadow_log_only": True,
        "no_path_to_order_send": True,
        "never_invent_news_protocol": True,
        "threshold": card.get("threshold"),
        "loop_bound": card.get("loop_bound"),
        "parameter": card.get("parameter"),
        "component": card.get("component"),
        "component_exists": card.get("component_exists"),
        "ask_error": card.get("ask_error"),
        "ALIVE_MENU": {
            "label": "ALIVE_MENU",
            "generated_this_cycle": menu.get("generated_this_cycle"),
            "reused_prior_map": menu.get("reused_prior_map"),
            "admit_options": list(ADMIT_OPTIONS),
            "not_next_gate_hold_escalate": True,
            "sidecar_next_gate_ids": menu.get("sidecar_next_gate_ids"),
            "offered_ids": menu.get("offered_ids"),
            "n_offered": menu.get("n_offered"),
            "cap": card.get("cap"),
            "inventory_option_cap": menu.get("inventory_option_cap"),
            "capped": menu.get("capped_fact"),
            "menu_hash": menu.get("menu_hash"),
            "inventory_fingerprint": menu.get("inventory_fingerprint"),
            "stale_menu_events": menu.get("stale_menu_events"),
            "sidecar_notes": menu.get("sidecar_notes"),
            "choice_ids": menu.get("choice_ids") or facts.get("catalog_choice_ids"),
            "criteria_sha256": menu.get("criteria_sha256"),
            "n_fluid": menu.get("n_fluid"),
            "n_envelope": menu.get("n_envelope"),
            "decided": {
                "choice": admit,
                "source": "systemone" if admit is not None else None,
                "fail_closed": card.get("fail_closed"),
            },
        },
        "CONF_GATE": {
            "label": "CONF_GATE",
            "band": card.get("band"),
            "behavior": card.get("behavior"),
            "starters": {"low": card.get("conf_low"), "high": card.get("conf_high")},
            "confidence": card.get("confidence"),
            "action": card.get("behavior"),
            "not_permission": True,
            "not_accuracy": True,
            "confidence_never_authorizes_side_effects": True,
            "per_question": facts.get("confidences") or {},
        },
        "FANOUT_BOOK": {
            "label": "FANOUT_BOOK",
            "one_call": True,
            "ask_together": True,
            "gate_seat": facts.get("gate_seat_ids"),
            "questions": questions,
            "n_questions": len(questions) if isinstance(questions, list) else None,
            "integer_only": card.get("integer_only"),
            "dropped_to_integer_only": _yes(card.get("integer_only")),
            "envelope_skipped": _envelope_skipped(envelope_ids),
            "env_in_fanout": _env_in_fanout(catalog_ids, envelope_ids),
            "consume": list(CONSUME_BRANCHES),
            "spine_empty": facts.get("spine_empty"),
            "ignore_event": card.get("ignore_event"),
            "ignored": ignored,
            "never_chain_jev_to_jev": True,
        },
        "DONE_OUTSIDE": {
            "label": "DONE_OUTSIDE",
            "jev_done": card.get("jev_done"),
            "jev_done_advisory_only": True,
            "high_conf_not_side_effect_proof": True,
            "code_verifies_artifacts": True,
            "writer_owns": list(WRITER_OWNS),
            "forbidden_auto_effects": menu.get("forbidden_auto_effects"),
            "artifact_verify": {
                "kind": "shadow_log",
                "ok": card.get("artifact_ok"),
                "reason": "stamp_does_not_write_artifacts",
                "path": None,
                "completion": None,
                "jev_done_choice_advisory": facts.get("jev_done_choice"),
            },
        },
        "USAGE_ROUTER": {
            "label": "USAGE_ROUTER",
            "route": card.get("route"),
            "requested": facts.get("requested_route"),
            "available": list(USAGE_SEATS),
            "destination": destination,
            "channel": destination,
            "defer": defer,
            "off_broker_path": True,
            "skip_envelope": True,
            "skip_aplus_obs": True,
            "never_arm_aplus": True,
            "aplu_obs_default_off": card.get("aplus_off"),
            "expensive_seats_not_invoked": list(EXPENSIVE_SEATS),
            "expensive_seats_plan_not_invoked": list(EXPENSIVE_SEATS_PLAN),
            "honor_defer": defer,
            "jev_calls_this_stamp": True if card.get("invoked") is True else None,
            "never_invent_news_protocol": True,
        },
    }
