"""Fluid pipeline status. Every decision is the System One return for that gate.

One piece: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached on
the ask, and the return is stored for the next ask. Status, next step,
eligibility, and each parameter are that return. A score may sit between
levels. An empty answer, a tie, a missing score, or an error leaves that
field unset.

Floor and baseline are not a question. An envelope class is a fact on the card.
The ask still runs. This module records the pipeline. It does not send.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
SCHEMA = "gtos.judgment.fluid_pipeline.v0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

APPLIED = "APPLIED_NAMED"
PROVED = "PROVED_SHADOW"
SHADOW = "SHADOW"

_STATUS_ORDER = (APPLIED, PROVED, SHADOW)
_NEXT_ORDER = (
    "observe_shadow",
    "shadow_score_then_prove_on_challenge_tape",
    "apply_preauthorized",
    "chair_ritual_required",
    "live_named",
)
_NOULS = (
    "may_auto_apply",
    "auto_apply_eligible",
    "research_only",
    "cannot_refuse",
    "fluid_component_exists",
    "never_place",
)
_SCORES = ("fluid_threshold", "fluid_loop", "fluid_parameter")
_SCORE_LABELS = {
    "fluid_threshold": "threshold",
    "fluid_loop": "loop bound",
    "fluid_parameter": "parameter",
}
_LEVELS = ("none", "trace", "small", "modest", "notable", "heavy")
_STATUS_CRITERIA = {
    APPLIED: "This fluid gate is applied and named.",
    PROVED: "This fluid gate is proved in shadow.",
    SHADOW: "This fluid gate is still shadow.",
}
_NEXT_CRITERIA = {
    "observe_shadow": "The next record for this gate is to observe shadow.",
    "shadow_score_then_prove_on_challenge_tape": "The next record is to score shadow, then prove on the challenge tape.",
    "apply_preauthorized": "The next record is the pre-authorized apply step.",
    "chair_ritual_required": "The next record is a chair ritual.",
    "live_named": "The next record is live and named.",
}
_NOUL_TEXT = {
    "may_auto_apply": "May this fluid gate auto-apply on this state?",
    "auto_apply_eligible": "Is this fluid gate eligible to auto-apply on this state?",
    "research_only": "Is this fluid gate research-only on this state?",
    "cannot_refuse": "Is refuse closed for this fluid gate on this state?",
    "fluid_component_exists": "Does this fluid gate component exist on this state?",
    "never_place": "Is place closed for this fluid gate on this state?",
}
_NOUL_CRITERIA = {
    "true": "Yes for this state.",
    "false": "No for this state.",
}
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
_DECISION_KEYS = frozenset({
    "status",
    "next",
    "may_auto_apply",
    "auto_apply_eligible",
    "research_only",
    "cannot_refuse",
    "threshold",
    "loop_bound",
    "parameter",
    "parameters",
    "component_exists",
    "choice",
    "noul",
    "score",
    "answers",
    "probabilities",
})
_PLANTED = ("answer", "choice", "score", "value", "noul", "probabilities", "default")

# History only when jev_questions cannot be imported. A miss is not copied back.
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

def _text_banned(text: str) -> bool:
    compact = text.replace(",", "").replace("_", "").lower()
    if "floor" in compact or "baseline" in compact:
        return True
    for token in _BANNED_TEXT:
        if token.replace(",", "").replace("_", "").lower() in compact:
            return True
    return False


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


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


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name) or name in _DECISION_KEYS:
                continue
            cleaned = _scrub(item)
            if cleaned is None and item is not None:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        kept = []
        for item in value:
            cleaned = _scrub(item)
            if cleaned is None and item is not None:
                continue
            kept.append(cleaned)
        return kept
    if isinstance(value, str):
        if _text_banned(value):
            return None
        return value
    if value is None or isinstance(value, (int, float, bool)):
        return value
    text = str(value)
    if _text_banned(text):
        return None
    return text


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(criteria))
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            body = dict(raw)
    except Exception:
        body = {}
    for key in _PLANTED:
        body.pop(key, None)
    clean = {
        str(key): str(val)
        for key, val in criteria.items()
        if not _text_banned(str(key)) and not _text_banned(str(val))
    }
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = clean
    return body


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    """Amount anchors from this card. An ordinal keeps its words."""
    return _shape_score(qid, instructions, None, wrapped=False)



def _noul_question(instructions: str) -> dict[str, Any]:
    return {
        "type": "noul",
        "instructions": instructions,
        "criteria": dict(_NOUL_CRITERIA),
    }


def _ask_line(text: str) -> str:
    return (
        f"{text} The value you return is the decision for this state. "
        "An empty answer or a tie leaves it unset. "
        "This ask does not send and does not flatten."
    )


def pipeline_questions() -> dict[str, dict[str, Any]]:
    """One pack. Types are noul, choice, or score. Floor and baseline are absent."""

    pack: dict[str, dict[str, Any]] = {
        "fluid_status": _choice_question(
            "fluid_status",
            _ask_line(
                "Fluid gate status for this state. "
                "The unique highest probability is the status."
            ),
            _STATUS_CRITERIA,
        ),
        "fluid_next": _choice_question(
            "fluid_next",
            _ask_line(
                "Next pipeline record for this fluid gate. "
                "The unique highest probability is that step."
            ),
            _NEXT_CRITERIA,
        ),
    }
    for name in _SCORES:
        label = _SCORE_LABELS[name]
        pack[name] = _score_question(
            name,
            _ask_line(
                f"The score you return is the {label} for this fluid gate. "
                "It may sit between the levels."
            ),
        )
    for name in _NOULS:
        pack[name] = _noul_question(_ask_line(_NOUL_TEXT[name]))
        pack[f"{name}_parameter"] = _score_question(
            f"{name}_parameter",
            _ask_line(
                f"The score you return is the parameter for {name} on this state. "
                "It may sit between the levels."
            ),
        )
    for name in ("fluid_status", "fluid_next"):
        pack[f"{name}_parameter"] = _score_question(
            f"{name}_parameter",
            _ask_line(
                f"The score you return is the parameter for {name} on this state. "
                "It may sit between the levels."
            ),
        )
    for qid, block in list(pack.items()):
        if _limit_key(qid) or block.get("type") not in {"noul", "choice", "score"}:
            pack.pop(qid, None)
            continue
        if _text_banned(str(block.get("instructions") or "")):
            pack.pop(qid, None)
    return pack


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return {}
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        name = str(key)
        if allowed and name not in allowed:
            continue
        number = _finite(value)
        if number is None:
            continue
        numeric[name] = number
    return numeric


def _local_unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    names = order or tuple(numeric)
    for name in names:
        if name not in numeric:
            continue
        prob = numeric[name]
        seen = True
        if best_p is None or prob > best_p:
            best = name
            best_p = prob
            tied = False
        elif prob == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie, an empty map, or a bare label stays unset."""

    if not numeric:
        return None
    local = _local_unique(numeric, order)
    if local is None:
        return None
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(dict(numeric), order)
    except Exception:
        agreed = local
    if agreed is None or str(agreed) != local:
        return None
    return local


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    numeric = _probabilities(block, order)
    if not numeric:
        return None
    picked = _unique(numeric, order)
    if picked not in order:
        return None
    return picked


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


def _score_value(block: Any, qid: str | None = None) -> float | None:
    """Returned number. A tie leaves it unset. The number is not snapped to a level."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))


    if not isinstance(block, dict) or block.get("error"):
        return None
    raw_probs = block.get("probabilities")
    if isinstance(raw_probs, Mapping) and raw_probs:
        order = tuple(str(key) for key in raw_probs)
        numeric = _probabilities(block, order)
        if numeric and _unique(numeric, order) is None:
            if block.get("score") is None:
                return None
    try:
        from .jev_questions import returned_number

        parsed = _finite(returned_number(block))
        if parsed is not None:
            return parsed
    except Exception:
        pass
    if "score" in block:
        return _finite(block.get("score"))
    if isinstance(raw_probs, Mapping) and raw_probs:
        order = tuple(str(key) for key in raw_probs)
        numeric = _probabilities(block, order)
        winner = _unique(numeric, order)
        if winner is None:
            return None
        return _finite(numeric.get(winner))
    return None


def _blank(error: str | None) -> dict[str, Any]:
    parameters = {name: None for name in ("fluid_status", "fluid_next", *_NOULS, *_SCORES)}
    return {
        "status": None,
        "next": None,
        "may_auto_apply": None,
        "auto_apply_eligible": None,
        "research_only": None,
        "cannot_refuse": None,
        "never_place": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "component_exists": None,
        "parameters": parameters,
        "error": error,
    }


def _read(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        return _blank("empty")
    error = receipt.get("error") or receipt.get("skipped")
    if receipt.get("ok") is False or error:
        return _blank(str(error or "error"))
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        return _blank("empty")
    row = _blank(None)
    row["status"] = _choice(answers.get("fluid_status"), _STATUS_ORDER)
    row["next"] = _choice(answers.get("fluid_next"), _NEXT_ORDER)
    row["threshold"] = _score_value(answers.get("fluid_threshold"), "fluid_threshold")
    row["loop_bound"] = _score_value(answers.get("fluid_loop"), "fluid_loop")
    row["parameter"] = _score_value(answers.get("fluid_parameter"), "fluid_parameter")
    for name in _NOULS:
        row[name] = _noul(answers.get(name))
    row["component_exists"] = row.get("fluid_component_exists")
    parameters = row["parameters"]
    parameters["fluid_status"] = _score_value(answers.get("fluid_status_parameter"), "fluid_status_parameter")
    parameters["fluid_next"] = _score_value(answers.get("fluid_next_parameter"), "fluid_next_parameter")
    parameters["fluid_threshold"] = row["threshold"]
    parameters["fluid_loop"] = row["loop_bound"]
    parameters["fluid_parameter"] = row["parameter"]
    for name in _NOULS:
        parameters[name] = _score_value(answers.get(f"{name}_parameter"), f"{name}_parameter")
    return row


def _miss(value: Any, kind: str, error: str | None) -> str | None:
    if value is not None:
        return None
    return error or kind


def _outcome_pairs(row: Mapping[str, Any]) -> tuple[tuple[str, Any, str | None], ...]:
    ask_error = row.get("error") if isinstance(row.get("error"), str) else None
    parameters = row.get("parameters") if isinstance(row.get("parameters"), Mapping) else {}
    pairs: list[tuple[str, Any, str | None]] = [
        ("fluid_status", row.get("status"), _miss(row.get("status"), "tie_or_empty", ask_error)),
        ("fluid_next", row.get("next"), _miss(row.get("next"), "tie_or_empty", ask_error)),
        ("fluid_threshold", row.get("threshold"), _miss(row.get("threshold"), "score_missing", ask_error)),
        ("fluid_loop", row.get("loop_bound"), _miss(row.get("loop_bound"), "score_missing", ask_error)),
        ("fluid_parameter", row.get("parameter"), _miss(row.get("parameter"), "score_missing", ask_error)),
    ]
    for name in _NOULS:
        value = row.get(name)
        pairs.append((name, value, _miss(value, "noul_missing", ask_error)))
        parameter = parameters.get(name)
        pairs.append((f"{name}_parameter", parameter, _miss(parameter, "score_missing", ask_error)))
    for name in ("fluid_status", "fluid_next"):
        parameter = parameters.get(name)
        pairs.append((f"{name}_parameter", parameter, _miss(parameter, "score_missing", ask_error)))
    return tuple(pairs)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    pairs = _outcome_pairs(row)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in pairs:
            _LOCAL_OUTCOMES.append({"key": key, "value": value, "error": error})
        return
    facts = dict(state)
    facts.pop("prior_outcomes", None)
    for key, value, error in pairs:
        try:
            append_outcome(key, value, facts, error=error)
        except Exception:
            return


def _post(state: dict[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    _attach_priors(state, questions)
    state["model"] = MODEL
    try:
        from .jev_client import evaluate
    except Exception:
        return {"ok": False, "error": "import_failed", "skipped": "import_failed", "answers": {}}
    try:
        receipt = evaluate(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    except Exception as exc:
        name = type(exc).__name__
        return {"ok": False, "error": name, "skipped": name, "answers": {}}
    if not isinstance(receipt, dict):
        return {"ok": False, "error": "empty", "skipped": "empty", "answers": {}}
    return receipt


def _decide(state: dict[str, Any]) -> dict[str, Any]:
    _bind_card(state)
    questions = pipeline_questions()
    try:
        receipt = _post(state, questions)
    except Exception as exc:
        row = _blank(type(exc).__name__)
        _remember(state, row)
        return row
    row = _read(receipt)
    _remember(state, row)
    return row


def _lock_catalog() -> dict[str, Any]:
    """Names from the process lock when that module is present. Missing stays missing."""

    try:
        from .process_lock import (
            APPLIED_WIRES,
            DEFAULT_FLUID_PROVE,
            FORBIDDEN_AUTO_EFFECTS,
            PREAUTH_EFFECTS,
            stamp_lock,
        )
    except Exception:
        return {
            "applied_wires": None,
            "preauth_effects": None,
            "forbidden_auto_effects": None,
            "prove_path": None,
            "stamp": {},
        }
    stamp: dict[str, Any] = {}
    try:
        raw = stamp_lock()
    except Exception:
        raw = None
    if isinstance(raw, dict):
        cleaned = _scrub(raw)
        if isinstance(cleaned, dict):
            for key in _DECISION_KEYS:
                cleaned.pop(key, None)
            stamp = cleaned
    return {
        "applied_wires": APPLIED_WIRES,
        "preauth_effects": PREAUTH_EFFECTS,
        "forbidden_auto_effects": FORBIDDEN_AUTO_EFFECTS,
        "prove_path": DEFAULT_FLUID_PROVE,
        "stamp": stamp,
    }


def _as_strings(values: Any) -> list[str] | None:
    if values is None:
        return None
    if isinstance(values, (str, bytes)) or not isinstance(values, (list, tuple, set, frozenset)):
        return None
    return [str(item) for item in values]


def _is_envelope(gate_id: str) -> bool:
    try:
        from .fluid_gates import is_envelope
    except Exception:
        return False
    try:
        return bool(is_envelope(gate_id))
    except Exception:
        return False


def _identity(gate: Any) -> dict[str, Any]:
    if not isinstance(gate, dict):
        return {"id": None, "family": None, "effect": None, "chair": None}
    gid = gate.get("id")
    return {
        "id": str(gid) if gid else None,
        "family": gate.get("family"),
        "effect": gate.get("effect"),
        "chair": gate.get("chair"),
    }


def _state(gate: Any, prove_ledger: Mapping[str, Any] | None) -> dict[str, Any]:
    ident = _identity(gate)
    facts: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "gate_id": ident["id"],
        "family": ident["family"],
        "effect": ident["effect"],
        "chair": ident["chair"],
    }
    if isinstance(gate, dict):
        for src, dest in (
            ("status", "catalog_status"),
            ("research_only", "catalog_research_only"),
            ("cannot_refuse", "catalog_cannot_refuse"),
            ("class", "catalog_class"),
            ("forbidden", "catalog_forbidden"),
        ):
            if src in gate:
                facts[dest] = gate.get(src)
    catalog = _lock_catalog()
    wires = catalog.get("applied_wires")
    if wires is not None and ident["id"] is not None:
        try:
            facts["in_applied_wires"] = ident["id"] in wires
        except Exception:
            pass
    effect = ident.get("effect")
    preauth = catalog.get("preauth_effects")
    if preauth is not None and effect is not None:
        try:
            facts["effect_in_preauth"] = effect in preauth
        except Exception:
            pass
    forbidden = catalog.get("forbidden_auto_effects")
    if forbidden is not None and effect is not None:
        try:
            facts["effect_in_forbidden"] = effect in forbidden
        except Exception:
            pass
    if ident["id"]:
        facts["is_envelope"] = _is_envelope(str(ident["id"]))
    if prove_ledger is not None:
        facts["prove_ledger"] = dict(prove_ledger)
    scrubbed = _scrub(facts)
    state = scrubbed if isinstance(scrubbed, dict) else {"model": MODEL}
    state.pop("prior_outcomes", None)
    state["model"] = MODEL
    return state


def _public_row(gate: Any, decided: Mapping[str, Any]) -> dict[str, Any]:
    ident = _identity(gate)
    parameters = decided.get("parameters") if isinstance(decided.get("parameters"), Mapping) else {}
    return {
        "id": ident["id"],
        "family": ident["family"],
        "effect": ident["effect"],
        "chair": ident["chair"],
        "status": decided.get("status"),
        "auto_apply_eligible": decided.get("auto_apply_eligible"),
        "may_auto_apply": decided.get("may_auto_apply"),
        "research_only": decided.get("research_only"),
        "cannot_refuse": decided.get("cannot_refuse"),
        "never_place": decided.get("never_place"),
        "next": decided.get("next"),
        "threshold": decided.get("threshold"),
        "loop_bound": decided.get("loop_bound"),
        "parameter": decided.get("parameter"),
        "component_exists": decided.get("component_exists"),
        "parameters": dict(parameters),
        "error": decided.get("error"),
    }


def gate_status(gate_id: str, *, prove_ledger: dict[str, Any] | None = None) -> str | None:
    """Status Choice for this gate. A miss stays unset."""

    gate = _lookup(gate_id) or {"id": gate_id}
    decided = _decide(_state(gate, prove_ledger))
    status = decided.get("status")
    return status if isinstance(status, str) else None


def may_auto_apply(gate_id: str, *, prove_ledger: dict[str, Any] | None = None) -> bool | float | None:
    """Auto-apply Noul for this gate. A miss stays unset. This does not send."""

    gate = _lookup(gate_id) or {"id": gate_id}
    return _decide(_state(gate, prove_ledger)).get("may_auto_apply")


def pipeline_row(gate: dict[str, Any], *, prove_ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    """One ask. Each decision field on the row is that return, or unset."""

    return _public_row(gate, _decide(_state(gate, prove_ledger)))


def load_fluid_ledger(path: Any = None) -> dict[str, Any] | None:
    """Read the prove ledger file. A missing file stays missing."""

    file = path
    if file is None:
        file = _lock_catalog().get("prove_path")
    if file is None:
        return None
    target = Path(file)
    if not target.is_file():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _lookup(gate_id: str) -> dict[str, Any] | None:
    try:
        from .fluid_gates import lookup
    except Exception:
        return None
    try:
        found = lookup(gate_id)
    except Exception:
        return None
    return found if isinstance(found, dict) else None


def _fluid_list() -> list[dict[str, Any]] | None:
    try:
        from .fluid_gates import fluid_gates
    except Exception:
        return None
    try:
        rows = fluid_gates()
    except Exception:
        return None
    if not isinstance(rows, list):
        return None
    return [row for row in rows if isinstance(row, dict)]


def _same_flag(rows: list[dict[str, Any]] | None, key: str) -> bool | None:
    """One flag only when every row returned that same bool. A miss stays unset."""

    if not rows:
        return None
    values = [row.get(key) for row in rows]
    if not values or any(value is None for value in values):
        return None
    if all(value is True for value in values):
        return True
    if all(value is False for value in values):
        return False
    return None


def _count(rows: list[dict[str, Any]] | None, status: str) -> int | None:
    if rows is None:
        return None
    return sum(1 for row in rows if row.get("status") == status)


def pipeline_snapshot(*, prove_ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    """One ask per fluid gate. Counts tally returned statuses. This does not send."""

    ledger = prove_ledger if prove_ledger is not None else load_fluid_ledger()
    gates = _fluid_list()
    rows = None if gates is None else [pipeline_row(gate, prove_ledger=ledger) for gate in gates]
    catalog = _lock_catalog()
    preauth = _as_strings(catalog.get("preauth_effects"))
    forbidden = _as_strings(catalog.get("forbidden_auto_effects"))
    wires = _as_strings(catalog.get("applied_wires"))
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "api_url": API_URL,
    }
    stamp = catalog.get("stamp")
    if isinstance(stamp, dict):
        body.update(stamp)
    body["schema"] = SCHEMA
    body["model"] = MODEL
    body["api_url"] = API_URL
    body["never_place"] = _same_flag(rows, "never_place")
    body["n_fluid"] = None if rows is None else len(rows)
    body["n_applied"] = _count(rows, APPLIED)
    body["n_proved_shadow"] = _count(rows, PROVED)
    body["n_shadow"] = _count(rows, SHADOW)
    body["n_may_auto_apply"] = (
        None if rows is None else sum(1 for row in rows if row.get("may_auto_apply") is True)
    )
    body["preauth_effects"] = None if preauth is None else sorted(preauth)
    body["forbidden_auto_effects"] = None if forbidden is None else sorted(forbidden)
    body["applied_wires"] = wires
    body["gates"] = rows
    body["note"] = (
        "Status, next, nouls, and parameters are the System One return for that gate. "
        "An envelope class is a fact. This module does not send."
    )
    return body
