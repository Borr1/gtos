"""CHAIR_STATIC_CLOSE_QUEUE — book_owner P1 keep envelope.

Every decision on this envelope, including every parameter, is the System
One return for that state. One call: ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False``. That call POSTs
https://api.typesafe.ai/v1/systemone. Questions are only Noul, Choice, or
Score. Prior outcomes are attached on the ask, and the return is stored
for the next ask.

An empty answer, a tie, or an error leaves that return unset. Floor and
baseline are not a question. This module does not send.

Challenge 0 / ``operator``. The writer reason ids are a menu
on the state. Membership in that menu is not a verdict. Dig never
broker-sends. Do not wholesale-edit ``book_owner.py``.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
QUEUE = "CHAIR_STATIC_CLOSE_QUEUE"
CHALLENGE_LOGIN = "0"
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

# Writer reason ids this queue can ask about. The menu is not the verdict.
KEEP_REASONS = (
    "account_state_unavailable",
    "already_placed_this_bar",
    "already_placed_today",
    "cluster_unit_already_placed_today",
    "breach_flatten_block",
    "kill_switch",
    "live_broker_authority",
    "pretrade_spread_r_refuse",
    "profile_missing",
    "same_broker_symbol_already_placed_this_cycle",
    "same_broker_symbol_transient_attempt_this_cycle",
    "same_broker_symbol_position_source_unavailable_for_lifecycle_guard",
    "same_broker_symbol_open_position_lifecycle_guard",
    "sleeve_already_holds_symbol",
    "sleeve_already_holds_symbol_broker",
    "weekend_policy_clock_unavailable",
)

KILL_ALREADY_CLOSED = (
    "no_tick_transient",
    "stale_late_entry_after_restart",
    "weekend_entry_embargo",
)

WRITER_ALIASES: dict[str, tuple[str, ...]] = {
    "already_placed_this_bar": ("already_placed_this_bar",),
    "already_placed_today": ("already_placed_today",),
    "cluster_unit_already_placed_today": ("cluster_unit_already_placed_today",),
    "kill_switch": ("kill_switch", "kill_switch_or_halt_forced_observe_only"),
    "live_broker_authority": (
        "live_broker_authority",
        "live_broker_authority_false_observe_only",
    ),
    "pretrade_spread_r_refuse": ("pretrade_spread_r_refuse", "cost_screen_spread_r"),
    "profile_missing": ("profile_missing", "profile_missing_instrument_config"),
}

KEEP_PREFIXES = (
    "already_placed_",
    "cluster_unit_already_placed_today",
    "same_broker_symbol_",
    "sleeve_already_holds_",
    "cost_screen_spread_r",
)

_VERDICT_ORDER = ("APPLY_CONSUME", "KILL_ENFORCE", "NOT_ON_QUEUE")
_VERDICT_CRITERIA = {
    "APPLY_CONSUME": "This reason is consumed on the keep envelope.",
    "KILL_ENFORCE": "This reason stays closed as kill.",
    "NOT_ON_QUEUE": "This reason is not on this queue.",
}
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)

_VERDICT_ID = "chair_static_close"
_KEEP_ID = "chair_static_keep"
_KILL_ID = "chair_static_kill"
_PRESENT_ID = "chair_static_present"
_PRIORITY_ID = "chair_static_priority"
_THRESHOLD_ID = "chair_static_threshold"
_LOOP_ID = "chair_static_loop"
_PARAMETER_ID = "chair_static_parameter"

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

def _writer_stem(reason: str) -> str:
    """Canonical writer id for this string. The id is a fact, not a verdict."""

    raw = str(reason or "").strip()
    if raw.startswith("cluster_unit_already_placed_today"):
        return "cluster_unit_already_placed_today"
    if raw.startswith("cost_screen_spread_r"):
        return "pretrade_spread_r_refuse"
    if raw.endswith("_suppressed_live_broker_authority_false"):
        return "live_broker_authority"
    return raw


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


def _score(block: Any, qid: str | None = None) -> float | None:
    """The parameter is the returned score. A missing score stays missing."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))


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
    """Amount anchors from this card. An ordinal keeps its words."""
    return _shape_score(qid, instructions, None, wrapped=True)



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
    """One pack. Types are noul, choice, or score."""

    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        _VERDICT_ID,
        "Which close verdict is this state? "
        "The option with the single highest probability is the verdict. "
        "An empty answer or a tie leaves the verdict unset. "
        "This question does not send.",
        _VERDICT_CRITERIA,
    ))
    pack.update(_noul_question(
        _KEEP_ID,
        "Is this reason on the keep envelope for this state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "This reason is on the keep envelope.",
        "This reason is not on the keep envelope.",
    ))
    pack.update(_noul_question(
        _KILL_ID,
        "Is this reason already closed as kill for this state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "This reason is already closed as kill.",
        "This reason is not already closed as kill.",
    ))
    pack.update(_noul_question(
        _PRESENT_ID,
        "Does the chair static close component exist for this state? "
        "The noul you return is that existence. "
        "An empty noul leaves it unset. "
        "This question does not send.",
        "The chair static close component exists for this state.",
        "The chair static close component does not exist for this state.",
    ))
    pack.update(_score_question(
        _PRIORITY_ID,
        "The score you return is the priority parameter for this close. "
        "It may sit between the levels on this state. "
        "An empty score leaves the priority unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _THRESHOLD_ID,
        "The score you return is the threshold for this close. "
        "It may sit between the levels on this state. "
        "An empty score leaves the threshold unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _LOOP_ID,
        "The score you return is the loop bound for this close. "
        "It may sit between the levels on this state. "
        "An empty score leaves the loop bound unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        _PARAMETER_ID,
        "The score you return is the parameter for this close. "
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


def _state(reason: str | None) -> dict[str, Any]:
    raw = None if reason is None else str(reason)
    stem = None if raw is None else _writer_stem(raw)
    body: dict[str, Any] = {
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "queue": QUEUE,
        "queue_priority_label": "P1",
        "reason": raw,
        "stem": stem,
        "writer_keep_ids": list(KEEP_REASONS),
        "writer_kill_ids": list(KILL_ALREADY_CLOSED),
        "writer_aliases": {key: list(val) for key, val in WRITER_ALIASES.items()},
        "writer_prefixes": list(KEEP_PREFIXES),
        "identity": {
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "magic": CHALLENGE_MAGIC,
            "queue": QUEUE,
        },
    }
    cleaned = _scrub(body)
    state = cleaned if isinstance(cleaned, dict) else {}
    state["model"] = MODEL
    state["login"] = CHALLENGE_LOGIN
    state["ns"] = CHALLENGE_NS
    state["magic"] = CHALLENGE_MAGIC
    state["queue"] = QUEUE
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


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    error = row.get("error")
    pairs = (
        (_VERDICT_ID, row.get("verdict")),
        (_KEEP_ID, row.get("keep")),
        (_KILL_ID, row.get("kill_already_closed")),
        (_PRESENT_ID, row.get("present")),
        (_PRIORITY_ID, row.get("priority")),
        (_THRESHOLD_ID, row.get("threshold")),
        (_LOOP_ID, row.get("loop_bound")),
        (_PARAMETER_ID, row.get("parameter")),
    )
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
    err = None if error in (None, "") else str(error)
    for key, value in pairs:
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
    receipt = call(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    return receipt if isinstance(receipt, dict) else {"error": "evaluate_not_a_dict", "answers": {}}


def _stamp(row: dict[str, Any]) -> dict[str, Any]:
    """Identity and the closed send mark. These are the module, not an answer."""

    row["queue"] = QUEUE
    row["login"] = CHALLENGE_LOGIN
    row["ns"] = CHALLENGE_NS
    row["magic"] = CHALLENGE_MAGIC
    row["place"] = False
    row["never_broker_send"] = True
    row["book_owner_wholesale_edit"] = False
    row["broker_effect"] = False
    row["model"] = row.get("model") or MODEL
    return row


def _blank(error: str | None) -> dict[str, Any]:
    return _stamp({
        "verdict": None,
        "keep": None,
        "kill_already_closed": None,
        "present": None,
        "priority": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "probabilities": {},
        "reason": None,
        "stem": None,
        "error": error,
        "model": MODEL,
    })


def _read(answers: Mapping[str, Any], error: str | None) -> dict[str, Any]:
    verdict, probabilities = _choice(answers.get(_VERDICT_ID), _VERDICT_ORDER)
    keep = _noul(answers.get(_KEEP_ID))
    kill = _noul(answers.get(_KILL_ID))
    present = _noul(answers.get(_PRESENT_ID))
    priority = _score(answers.get(_PRIORITY_ID), _PRIORITY_ID)
    threshold = _score(answers.get(_THRESHOLD_ID), _THRESHOLD_ID)
    loop_bound = _score(answers.get(_LOOP_ID), _LOOP_ID)
    parameter = _score(answers.get(_PARAMETER_ID), _PARAMETER_ID)
    return _stamp({
        "verdict": verdict,
        "keep": keep,
        "kill_already_closed": kill,
        "present": present,
        "priority": priority,
        "threshold": threshold,
        "loop_bound": loop_bound,
        "parameter": parameter,
        "probabilities": probabilities,
        "error": error,
        "model": MODEL,
    })


def evaluate_chair_static_close(
    reason: str | None = None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Ask the close envelope for this reason. A miss stays unset. Never sends."""

    state = _state(reason)
    try:
        questions = _questions()
    except Exception as exc:
        row = _blank(type(exc).__name__)
        row["reason"] = None if reason is None else str(reason)
        row["stem"] = None if reason is None else _writer_stem(str(reason))
        _remember(state, row)
        return row
    if not _pack_ok(questions):
        row = _blank("question_rejected")
        row["reason"] = state.get("reason")
        row["stem"] = state.get("stem")
        _remember(state, row)
        return row
    _attach_priors(state, questions)
    try:
        receipt = _post(state, questions, evaluate_fn)
    except Exception as exc:
        row = _blank(type(exc).__name__)
        row["reason"] = state.get("reason")
        row["stem"] = state.get("stem")
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
        row["stem"] = state.get("stem")
        if receipt.get("model"):
            row["model"] = receipt.get("model")
        _remember(state, row)
        return row
    row = _read(answers, None if error in (None, "") else str(error))
    row["reason"] = state.get("reason")
    row["stem"] = state.get("stem")
    if receipt.get("model"):
        row["model"] = receipt.get("model")
    _remember(state, row)
    return row


def classify_book_owner_reason(
    reason: str,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> str | None:
    """Close verdict for this reason. The unique highest probability, or unset."""

    verdict = evaluate_chair_static_close(reason, evaluate_fn=evaluate_fn).get("verdict")
    if verdict in _VERDICT_ORDER:
        return str(verdict)
    return None


def is_keep_envelope(
    reason: str,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> bool | float | None:
    """Keep-envelope noul for this reason. A miss stays unset."""

    return evaluate_chair_static_close(reason, evaluate_fn=evaluate_fn).get("keep")


def is_kill_already_closed(
    reason: str,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> bool | float | None:
    """Already-closed kill noul for this reason. A miss stays unset."""

    return evaluate_chair_static_close(reason, evaluate_fn=evaluate_fn).get("kill_already_closed")


def close_queue(*, evaluate_fn: Callable[..., Any] | None = None) -> dict[str, Any]:
    """One ask for the queue state. Writer ids stay a menu. The fields are the return."""

    card = evaluate_chair_static_close(None, evaluate_fn=evaluate_fn)
    card["writer_keep_ids"] = list(KEEP_REASONS)
    card["writer_kill_ids"] = list(KILL_ALREADY_CLOSED)
    return card


def _consume(names: tuple[str, ...], evaluate_fn: Callable[..., Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in names:
        card = evaluate_chair_static_close(name, evaluate_fn=evaluate_fn)
        out[name] = {
            "reason": name,
            "stem": card.get("stem"),
            "verdict": card.get("verdict"),
            "keep": card.get("keep"),
            "kill_already_closed": card.get("kill_already_closed"),
            "present": card.get("present"),
            "priority": card.get("priority"),
            "threshold": card.get("threshold"),
            "loop_bound": card.get("loop_bound"),
            "parameter": card.get("parameter"),
            "probabilities": card.get("probabilities") or {},
            "queue": QUEUE,
            "login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
            "magic": CHALLENGE_MAGIC,
            "place": False,
            "never_broker_send": True,
            "book_owner_wholesale_edit": False,
            "broker_effect": False,
            "model": card.get("model") or MODEL,
            "error": card.get("error"),
        }
    return out


def consume_keep_envelope(*, evaluate_fn: Callable[..., Any] | None = None) -> dict[str, Any]:
    """One ask per keep-menu id. The verdict and the parameters are that return."""

    return _consume(KEEP_REASONS, evaluate_fn)


def consume_kill_already_closed(*, evaluate_fn: Callable[..., Any] | None = None) -> dict[str, Any]:
    """One ask per kill-menu id. The verdict and the parameters are that return."""

    return _consume(KILL_ALREADY_CLOSED, evaluate_fn)


__all__ = [
    "CHALLENGE_LOGIN",
    "CHALLENGE_MAGIC",
    "CHALLENGE_NS",
    "KEEP_PREFIXES",
    "KEEP_REASONS",
    "KILL_ALREADY_CLOSED",
    "MODEL",
    "QUEUE",
    "WRITER_ALIASES",
    "classify_book_owner_reason",
    "close_queue",
    "consume_keep_envelope",
    "consume_kill_already_closed",
    "evaluate_chair_static_close",
    "is_keep_envelope",
    "is_kill_already_closed",
]
