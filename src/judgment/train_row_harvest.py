"""Train-row harvest for one Challenge close.

Each decision and each parameter is the System One return for that state.
One call: jev_client.evaluate, model jev-1.13.0,
POST https://api.typesafe.ai/v1/systemone, merge_sleeve=False.
Questions are only a Noul, a Choice, or a Score. Prior outcomes are on
the ask. The return is stored for the next ask. An empty answer, a tie,
or an error leaves that field unset.

A floor and a baseline are not a question. This module does not send.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"

HARVEST_SHADOW_ENV = "GTOS_JEV_TRAIN_HARVEST_SHADOW"
HARVEST_CALL_ENV = "GTOS_JEV_TRAIN_HARVEST_CALL"
HARVEST_APPLY_ENV = "GTOS_JEV_TRAIN_HARVEST_APPLY"
HARVEST_PATH_ENV = "GTOS_JEV_TRAIN_HARVEST_PATH"

SCHEMA_ROW = "gtos.jev.train_row_harvest.row.v1"
SCHEMA_PAIR = "gtos.jev.train_row_harvest.pair.v1"
SCHEMA_RUN = "gtos.jev.train_row_harvest.run.v1"

CHALLENGE_LOGIN = 0
QUARANTINE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0

LENSES = ("Challenge_book", "Module_ATR", "Dig_3R", "Edge_ATR")
MENU_STRIKE = ("A_STAND_DOWN", "B_SIZE_HALF", "C_SIZE_TRIM", "D_FULL", "E_KEEP_CAP")
PAIR_ROLES = ("WIN_LIKE", "LOSE_LIKE", "RELATIVE_WEAK", "UNPAIRED", "ABSTAIN")
PAIR_KINDS = (
    "ticket_twin",
    "sleeve_twin_asset_split",
    "year_twin_module_atr",
    "module_keep_vs_challenge_stand",
    "unpaired",
)
PLACE_MENU = ("PLACE", "STAND", "DELAY")
_LEVELS = ("none", "trace", "small", "modest", "notable", "heavy")
_NOUL_ORDER = ("true", "false")
_TRUTHY = frozenset({"1", "true", "yes", "on"})
_EXPOST = (
    "miss_type",
    "exit_class",
    "close_reason",
    "R",
    "realized_r",
    "broker_net",
    "profit",
    "mfe",
    "mae",
    "won",
    "why_lost",
    "why_lost_text",
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

_STRIKE_CRITERIA = {
    "A_STAND_DOWN": "Stand down. Do not admit.",
    "B_SIZE_HALF": "Admit. The size multiple is the returned size score.",
    "C_SIZE_TRIM": "Admit. The trim is the returned size score.",
    "D_FULL": "Admit. The size multiple is the returned size score.",
    "E_KEEP_CAP": "Keep surface. The concurrent cap is the returned cap score.",
}
_ROLE_CRITERIA = {
    "WIN_LIKE": "This card is the strong side of the enumerated pair.",
    "LOSE_LIKE": "This card is the fail side of the enumerated pair.",
    "RELATIVE_WEAK": "This card is the softer side of the enumerated pair.",
    "UNPAIRED": "This card has no enumerated twin.",
    "ABSTAIN": "The enumerated pair does not name a role.",
}
_PLACE_CRITERIA = {
    "PLACE": "The entry state labels place.",
    "STAND": "The entry state labels stand.",
    "DELAY": "The entry state labels delay.",
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

def _env_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def harvest_enabled() -> bool:
    """Shadow env gate. It is not the apply noul."""

    return _env_on(HARVEST_SHADOW_ENV)


def harvest_call_enabled() -> bool:
    """Post gate. Off does not ask and does not fill a verdict."""

    return harvest_enabled() and _env_on(HARVEST_CALL_ENV)


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _f(value: Any) -> float | None:
    if value == "":
        return None
    return _finite(value)


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
    """Drop limit keys and banned dollar tokens before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, tuple):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _without_verdicts(payload: dict[str, Any]) -> dict[str, Any]:
    """A stamp already on the facts is not the decision."""

    for name in _FIELDS:
        payload.pop(name, None)
    for _field, _kind, qid, _order in _SPEC:
        payload.pop(qid, None)
    payload.pop("answers", None)
    payload.pop("order_send", None)
    payload.pop("prior_outcomes", None)
    return payload


def _ranked(
    probs: Mapping[str, Any] | None,
    order: Sequence[str] | None,
) -> tuple[str | None, bool, bool]:
    """Unique highest. A missing probability is not zero. A tie is not a choice."""

    if not isinstance(probs, Mapping) or not probs:
        return None, False, False
    names = tuple(str(name) for name in order) if order else tuple(str(name) for name in probs)
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in names:
        if name not in probs:
            continue
        raw = probs.get(name)
        if raw is None or isinstance(raw, bool):
            continue
        number = _finite(raw)
        if number is None:
            continue
        seen = True
        if best_p is None or number > best_p:
            best = name
            best_p = number
            tied = False
        elif number == best_p:
            tied = True
    if not seen or tied or best is None:
        return None, bool(seen and tied), seen
    return best, False, True


def _choice(block: Any, order: Sequence[str]) -> str | None:
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping):
        return None
    menu = tuple(str(name) for name in order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probs, menu)
    except Exception:
        picked = _ranked(probs, menu)[0]
    if picked not in menu:
        return None
    return str(picked)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
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
    """The score that came back. It is not snapped to a level."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))


    if not isinstance(block, Mapping) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        if block.get("score") is None:
            return None
        return _finite(block.get("score"))


def _pull(block: Any, kind: str, order: Sequence[str] | None, qid: str | None = None) -> Any:
    if kind == "noul":
        return _noul(block)
    if kind == "choice":
        return _choice(block, order or ())
    return _score(block, qid)


def _why(block: Any, value: Any, order: Sequence[str] | None, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if isinstance(block, Mapping) and block.get("error"):
        return str(block.get("error"))
    probs = block.get("probabilities") if isinstance(block, Mapping) else None
    if isinstance(probs, Mapping) and probs:
        menu = tuple(order) if order else tuple(str(name) for name in probs)
        _picked, tied, seen = _ranked(probs, menu)
        if seen and tied:
            return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {str(key): _scrub_text(val) for key, val in criteria.items()}
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


def _no_transmit(text: str) -> str:
    return (
        text.strip()
        + " An empty answer leaves it unset. This ask does not transmit an order."
    )


def harvest_questions() -> dict[str, Any]:
    """One pack. Types are noul, choice, or score."""

    pack: dict[str, Any] = {}
    pack.update(
        _choice_question(
            "harvest_strike",
            _no_transmit(
                "Which strike fits this entry state? "
                "The outcome block is not an entry fact. "
                "A geometry print is not itself a strike. "
                "A keep surface is not a hard-off. "
                "A null regime tag is not a forced stand, and a regime name is not invented. "
                "A session name is not a cage. News is not invented. "
                "The option you return is the decision. An empty answer or a tie is not a decision."
            ),
            _STRIKE_CRITERIA,
        )
    )
    pack.update(
        _choice_question(
            "harvest_pair_role",
            _no_transmit(
                "Which role fits this card on the enumerated pair? "
                "The option you return is the decision. An empty answer or a tie is not a decision."
            ),
            _ROLE_CRITERIA,
        )
    )
    pack.update(
        _choice_question(
            "harvest_pair_kind",
            _no_transmit(
                "Which enumerated pair kind fits this state? "
                "The option you return is the decision. An empty answer or a tie is not a decision."
            ),
            {kind: kind for kind in PAIR_KINDS},
        )
    )
    pack.update(
        _score_question(
            "harvest_pair_quality",
            _no_transmit(
                "The score you return is how structurally similar the enumerated twin is. "
                "It may sit between the levels."
            ),
        )
    )
    pack.update(
        _noul_question(
            "harvest_lens_honest",
            _no_transmit(
                "Do the filled R columns on this state name exactly the lens on this state? "
                "The noul you return is that answer."
            ),
            "The filled R column is the named lens.",
            "The R columns are merged, mis-tagged, or the named lens is unfilled.",
        )
    )
    pack.update(
        _noul_question(
            "harvest_geometry_alone_neq_strike",
            _no_transmit(
                "Is a geometry print standing as a strike while the other voters on this state are unnamed? "
                "The noul you return is that answer."
            ),
            "Geometry is alone on this state.",
            "Other voters are named on this state.",
        )
    )
    pack.update(
        _noul_question(
            "harvest_alive_before_keep",
            _no_transmit(
                "Is alive named and true on this state? The noul you return is that answer."
            ),
            "Alive is named and true.",
            "Alive is unnamed or not true.",
        )
    )
    pack.update(
        _noul_question(
            "harvest_regime_null_ok",
            _no_transmit(
                "Is a null regime tag honest for this state? The noul you return is that answer."
            ),
            "A null regime tag is honest for this state.",
            "The named regime tag is part of this state.",
        )
    )
    pack.update(
        _choice_question(
            "harvest_place_would_have",
            _no_transmit(
                "Label only. For this entry state, is the place label PLACE, STAND, or DELAY? "
                "The option you return is that label. An empty answer or a tie is not a decision."
            ),
            _PLACE_CRITERIA,
        )
    )
    pack.update(
        _noul_question(
            "harvest_keep",
            _no_transmit(
                "Is this sleeve a keep surface for this state? The noul you return is that answer."
            ),
            "This sleeve is a keep surface for this state.",
            "This sleeve is not a keep surface for this state.",
        )
    )
    pack.update(
        _noul_question(
            "harvest_apply",
            _no_transmit(
                "Is this harvest applied for this state? The noul you return is that answer."
            ),
            "This harvest is applied for this state.",
            "This harvest is not applied for this state.",
        )
    )
    pack.update(
        _score_question(
            "harvest_size",
            _no_transmit(
                "The score you return is the size multiple for this state. "
                "It may sit between the levels."
            ),
        )
    )
    pack.update(
        _score_question(
            "harvest_max_concurrent",
            _no_transmit(
                "The score you return is the concurrent cap for this state. "
                "It may sit between the levels."
            ),
        )
    )
    pack.update(
        _score_question(
            "harvest_threshold",
            _no_transmit(
                "The score you return is the threshold for this state. "
                "It may sit between the levels."
            ),
        )
    )
    pack.update(
        _score_question(
            "harvest_loop_bound",
            _no_transmit(
                "The score you return is how many harvest steps belong on this state. "
                "It may sit between the levels."
            ),
        )
    )
    pack.update(
        _score_question(
            "harvest_parameter",
            _no_transmit(
                "The score you return is the parameter for this state. "
                "It may sit between the levels."
            ),
        )
    )
    return pack


_SPEC: tuple[tuple[str, str, str, tuple[str, ...] | None], ...] = (
    ("strike", "choice", "harvest_strike", MENU_STRIKE),
    ("pair_role", "choice", "harvest_pair_role", PAIR_ROLES),
    ("pair_kind", "choice", "harvest_pair_kind", PAIR_KINDS),
    ("pair_quality", "score", "harvest_pair_quality", None),
    ("lens_honest", "noul", "harvest_lens_honest", _NOUL_ORDER),
    ("geometry_alone", "noul", "harvest_geometry_alone_neq_strike", _NOUL_ORDER),
    ("alive_before_keep", "noul", "harvest_alive_before_keep", _NOUL_ORDER),
    ("regime_null_ok", "noul", "harvest_regime_null_ok", _NOUL_ORDER),
    ("place", "choice", "harvest_place_would_have", PLACE_MENU),
    ("keep", "noul", "harvest_keep", _NOUL_ORDER),
    ("apply", "noul", "harvest_apply", _NOUL_ORDER),
    ("size", "score", "harvest_size", None),
    ("max_concurrent", "score", "harvest_max_concurrent", None),
    ("threshold", "score", "harvest_threshold", None),
    ("loop_bound", "score", "harvest_loop_bound", None),
    ("parameter", "score", "harvest_parameter", None),
)
_FIELDS = tuple(item[0] for item in _SPEC)


def _blank(reason: str | None = None) -> dict[str, Any]:
    row = {name: None for name in _FIELDS}
    row.update(
        {
            "ok": None,
            "jev_dark": True,
            "skipped": reason,
            "answers": {},
            "error": None,
            "model": MODEL,
            "source": None,
            "usage": None,
            "state": None,
        }
    )
    return row


def _gate_facts() -> dict[str, Any]:
    return {
        "shadow_env": _env_on(HARVEST_SHADOW_ENV),
        "call_env": _env_on(HARVEST_CALL_ENV),
        "apply_env": _env_on(HARVEST_APPLY_ENV),
    }


def _remember(state: Mapping[str, Any], rows: Sequence[tuple[str, Any, str | None]]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    scrubbed = _scrub(dict(state))
    payload = scrubbed if isinstance(scrubbed, dict) else {}
    _without_verdicts(payload)
    payload["model"] = MODEL
    payload["book_login"] = CHALLENGE_LOGIN
    payload["ns"] = CHALLENGE_NS
    payload["magic"] = CHALLENGE_MAGIC
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = None
    payload["prior_outcomes"] = [] if loaded is None else loaded
    try:
        from .jev_client import API_URL as client_url
        from .jev_client import evaluate

        if client_url != API_URL:
            return {
                "ok": None,
                "error": "systemone_url",
                "answers": {},
                "state": payload,
                "model": MODEL,
                "skipped": None,
                "usage": None,
                "source": None,
            }
        receipt = evaluate(
            payload,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {
            "ok": None,
            "error": type(exc).__name__,
            "answers": {},
            "state": payload,
            "model": MODEL,
            "skipped": None,
            "usage": None,
            "source": None,
        }
    if not isinstance(receipt, dict):
        return {
            "ok": None,
            "error": "evaluate_not_a_dict",
            "answers": {},
            "state": payload,
            "model": MODEL,
            "skipped": None,
            "usage": None,
            "source": None,
        }
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "ok": receipt.get("ok"),
        "error": error,
        "answers": answers,
        "state": payload,
        "model": receipt.get("model") or MODEL,
        "skipped": receipt.get("skipped"),
        "usage": receipt.get("usage") if isinstance(receipt.get("usage"), dict) else None,
        "source": "jev",
    }


def _pack_ok(questions: Mapping[str, Any]) -> bool:
    allowed = {"noul", "choice", "score"}
    if not questions:
        return False
    for block in questions.values():
        if not isinstance(block, dict) or block.get("type") not in allowed:
            return False
    return True


def _read(asked: Mapping[str, Any]) -> dict[str, Any]:
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    error = asked.get("error")
    out = _blank(None)
    rows: list[tuple[str, Any, str | None]] = []
    for field, kind, qid, order in _SPEC:
        block = answers.get(qid)
        value = _pull(block, kind, order, qid)
        out[field] = value
        rows.append((qid, value, _why(block, value, order, error)))
    posted = asked.get("state") if isinstance(asked.get("state"), dict) else {}
    _remember(posted, rows)
    out.update(
        {
            "ok": asked.get("ok"),
            "jev_dark": not bool(answers),
            "skipped": asked.get("skipped"),
            "answers": answers,
            "error": error if not answers else None,
            "model": asked.get("model") or MODEL,
            "source": asked.get("source"),
            "usage": asked.get("usage"),
            "state": posted or None,
        }
    )
    return out


def evaluate_harvest_row(state: Mapping[str, Any]) -> dict[str, Any]:
    """One post for this state. A miss leaves every field unset. This does not send."""

    _bind_card(state)
    if not harvest_call_enabled():
        return _blank("GTOS_JEV_TRAIN_HARVEST_CALL_off")
    try:
        questions = harvest_questions()
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        row = _blank(type(exc).__name__)
        row["error"] = type(exc).__name__
        return row
    if not _pack_ok(questions):
        row = _blank("question_pack_fail")
        row["error"] = "question_pack_fail"
        return row
    incoming = _scrub(dict(state))
    payload = incoming if isinstance(incoming, dict) else {}
    _without_verdicts(payload)
    payload.update(_gate_facts())
    payload["model"] = MODEL
    return _read(_ask(payload, questions))


def harvest_apply_enabled() -> bool | float | None:
    """Apply noul for the env-fact state. A miss stays unset. This does not send."""

    if not harvest_call_enabled():
        return None
    return evaluate_harvest_row(_gate_facts()).get("apply")


def keep_signature(sleeve: str | None, family: str | None = None) -> bool | float | None:
    """Keep noul for this sleeve. A miss stays unset. Family text is a fact, not the noul."""

    if not harvest_call_enabled():
        return None
    decided = evaluate_harvest_row({"sleeve": sleeve, "sleeve_family": family})
    return decided.get("keep")


def r_by_lens(*, lens: str, r_value: float | None) -> dict[str, float | None]:
    """Place the measured R on that lens column. An unknown lens leaves every column unset."""

    out = {f"R_{name}": None for name in LENSES}
    if lens in LENSES:
        out[f"R_{lens}"] = r_value
    return out


def filled_r_names(r_cols: Mapping[str, Any]) -> list[str]:
    """Lens names whose R column is filled. This list is a fact, not the honesty noul."""

    return [name for name in LENSES if r_cols.get(f"R_{name}") is not None]


def lens_honest(r_cols: Mapping[str, Any], lens: str) -> bool | float | None:
    """Honesty noul for these columns. A miss stays unset."""

    if not harvest_call_enabled():
        return None
    decided = evaluate_harvest_row(
        {
            "lens": lens,
            "r_columns": r_by_lens(lens=lens, r_value=None) | dict(r_cols),
            "filled_r": filled_r_names(r_cols),
        }
    )
    return decided.get("lens_honest")


def split_entry_vs_expost(state: Mapping[str, Any]) -> dict[str, Any]:
    """Copy state and move ex-post keys under the outcome block."""

    entry = json.loads(json.dumps(state, default=str))
    outcome = dict(entry.pop("outcome_only_do_not_use_as_live_input", {}) or {})
    for key in _EXPOST:
        if key in entry and entry[key] is not None:
            outcome[key] = entry.pop(key)
    entry["outcome_only_do_not_use_as_live_input"] = outcome
    return entry


def _parse_login(raw: Any) -> tuple[int | None, str | None]:
    if raw is None or raw == "":
        return None, None
    try:
        return int(raw), None
    except (TypeError, ValueError):
        return None, "login_unparseable"


def _book_skip(close: Mapping[str, Any]) -> str | None:
    """Book gate. A skipped row does not carry a strike, apply, or place."""

    if close.get("still_open"):
        return "still_open"
    login, bad = _parse_login(close.get("login"))
    if bad:
        return bad
    if login == QUARANTINE_LOGIN:
        return "quarantine_login_0"
    if login is not None and login != CHALLENGE_LOGIN:
        return f"not_challenge_login_{login}"
    return None


def _skipped(reason: str, **extra: Any) -> dict[str, Any]:
    row = _blank(reason)
    row.update(
        {
            "schema": SCHEMA_ROW,
            "order_send": False,
            "never_broker_place": True,
            "never_merge_R": True,
            "news_protocol_invent": False,
        }
    )
    row.update(extra)
    return row


def _first(close: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in close and close.get(key) is not None:
            return close.get(key)
    return None


def _row_facts(
    close: Mapping[str, Any],
    pair: Mapping[str, Any] | None,
    books: Any,
    spines: Any,
) -> dict[str, Any]:
    scrubbed = _scrub(dict(close))
    state = scrubbed if isinstance(scrubbed, dict) else {}
    _without_verdicts(state)
    sleeve = close.get("sleeve")
    sleeve_text = sleeve if sleeve not in (None, "") else None
    lens_raw = close.get("lens")
    lens = str(lens_raw) if lens_raw not in (None, "") else None
    r_cols = r_by_lens(lens=lens or "", r_value=_f(close.get("R")))
    login, _bad = _parse_login(close.get("login"))
    state["schema"] = "gtos.jev.complete_state.harvest.v1"
    state["identity"] = {
        "symbol": close.get("symbol"),
        "sleeve": sleeve_text,
        "sleeve_family": _first(close, "sleeve_family", "jev_sleeve_family"),
        "side": close.get("side"),
        "ticket": close.get("ticket"),
        "login": login,
        "book_login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "asset_class": _first(close, "asset_class", "asset"),
    }
    state["lens"] = lens
    state["filled_r"] = filled_r_names(r_cols)
    state["enumerated_pair"] = _pair_facts(pair)
    state.update(r_cols)
    outcome = state.get("outcome_only_do_not_use_as_live_input")
    if not isinstance(outcome, dict):
        outcome = {}
    outcome.update(
        {
            "exit_class": _first(close, "exit_class", "exit"),
            "miss_type": _first(close, "miss_type", "miss"),
            "R": _f(close.get("R")),
            "r_source": close.get("r_source"),
        }
    )
    state["outcome_only_do_not_use_as_live_input"] = outcome
    clock = _first(close, "session", "session_ict", "session_bucket")
    if clock is not None:
        state["clock"] = {"session_bucket": clock}
    if "conf_band" not in state:
        band = close.get("jev_conf_gate_band")
        if band is not None:
            state["conf_band"] = band
    if books is not None:
        state["books"] = books
    if spines is not None:
        state["spines"] = spines
    return state


def _pair_facts(pair: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not pair:
        return None
    return {
        "pair_id": pair.get("pair_id"),
        "members": list(pair.get("members") or []),
        "group": pair.get("group"),
    }


def _member_fact(row: Mapping[str, Any]) -> dict[str, Any]:
    scrubbed = _scrub(dict(row))
    fact = scrubbed if isinstance(scrubbed, dict) else {}
    _without_verdicts(fact)
    outcome = fact.get("outcome_only_do_not_use_as_live_input")
    if not isinstance(outcome, dict):
        outcome = {}
    for key in _EXPOST:
        if key in fact and fact[key] is not None:
            outcome[key] = fact.pop(key)
    fact["outcome_only_do_not_use_as_live_input"] = outcome
    return fact


def _group_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("lens"),
        str(row.get("symbol") or ""),
        str(_first(row, "sleeve_family", "jev_sleeve_family") or ""),
        str(_first(row, "session_bucket", "session", "session_ict") or ""),
        str(row.get("side") or "").lower(),
    )


def candidate_twins(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Group co-members. Kind, role, and quality are the return for that group."""

    by_key: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[_group_key(row)].append(dict(row))
    pairs: list[dict[str, Any]] = []
    for index, (key, group) in enumerate(by_key.items()):
        lens, symbol, family, session, side = key
        members = [item.get("ticket") for item in group]
        group_id = f"G_{index}_{lens}_{symbol}_{family}_{session}_{side}"
        decided = evaluate_harvest_row(
            {
                "lens": lens,
                "group": {
                    "lens": lens,
                    "symbol": symbol,
                    "sleeve_family": family,
                    "session": session,
                    "side": side,
                },
                "members": [_member_fact(item) for item in group],
            }
        )
        pairs.append(
            {
                "schema": SCHEMA_PAIR,
                "pair_id": group_id,
                "members": members,
                "group": {
                    "lens": lens,
                    "symbol": symbol,
                    "sleeve_family": family,
                    "session": session,
                    "side": side,
                },
                "pair_kind": decided.get("pair_kind"),
                "pair_role": decided.get("pair_role"),
                "pair_quality": decided.get("pair_quality"),
                "decisions": {name: decided.get(name) for name in _FIELDS},
                "closes": group,
                "order_send": False,
                "never_broker_place": True,
            }
        )
    return pairs


def _shown_pair(pair: Mapping[str, Any] | None) -> dict[str, Any]:
    if not pair:
        return {"pair_id": None, "members": [], "pair_kind": None, "pair_role": None, "pair_quality": None}
    shown = {key: value for key, value in dict(pair).items() if key != "closes"}
    return shown


def _stored_state(jev: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    posted = jev.get("state") if isinstance(jev.get("state"), dict) else _scrub(state)
    if not isinstance(posted, dict):
        return {}
    out = dict(posted)
    out.pop("prior_outcomes", None)
    return out


def emit_harvest_row(
    close: Mapping[str, Any],
    *,
    pair: Mapping[str, Any] | None = None,
    books: Any = None,
    spines: Any = None,
    store_path: Path | None = None,
) -> dict[str, Any]:
    """One close, one ask. A miss leaves the decision unset. This does not send."""

    reason = _book_skip(close)
    if reason:
        return _skipped(reason, ticket=close.get("ticket"))
    sleeve = close.get("sleeve")
    sleeve_text = sleeve if sleeve not in (None, "") else None
    lens_raw = close.get("lens")
    lens = str(lens_raw) if lens_raw not in (None, "") else None
    r_cols = r_by_lens(lens=lens or "", r_value=_f(close.get("R")))
    state = split_entry_vs_expost(_row_facts(close, pair, books, spines))
    jev = evaluate_harvest_row(state)
    login, _bad = _parse_login(close.get("login"))
    row: dict[str, Any] = {
        "schema": SCHEMA_ROW,
        "logged_at_utc": _now_utc(),
        "book_login": CHALLENGE_LOGIN,
        "login": login,
        "ns": CHALLENGE_NS,
        "ticket": close.get("ticket"),
        "symbol": close.get("symbol"),
        "sleeve": sleeve_text,
        "lens": lens,
        "pair": _shown_pair(pair),
        "complete_state": _stored_state(jev, state),
        "filled_r": filled_r_names(r_cols),
        "r_by_lens": r_cols,
        "answers": jev.get("answers") if isinstance(jev.get("answers"), dict) else {},
        "ok": jev.get("ok"),
        "skipped": jev.get("skipped"),
        "error": jev.get("error"),
        "model": jev.get("model") or MODEL,
        "source": jev.get("source"),
        "usage": jev.get("usage"),
        "jev_dark": jev.get("jev_dark"),
        "order_send": False,
        "never_broker_place": True,
        "never_merge_R": True,
        "news_protocol_invent": False,
    }
    for name in _FIELDS:
        row[name] = jev.get(name)
    if store_path is not None and harvest_enabled():
        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, default=str) + "\n")
        row["appended"] = True
    return row


def run_paired_harvest(
    closes: Iterable[Mapping[str, Any]],
    *,
    store_path: Path | None = None,
) -> dict[str, Any]:
    """One ask per group, then one ask per close. Roles come back on those asks."""

    packed = [dict(item) for item in closes]
    pairs = candidate_twins(packed)
    rows: list[dict[str, Any]] = []
    for pair in pairs:
        for close in pair.get("closes") or []:
            rows.append(emit_harvest_row(close, pair=pair, store_path=store_path))
    shown = [{key: value for key, value in pair.items() if key != "closes"} for pair in pairs]
    return {
        "schema": SCHEMA_RUN,
        "n_closes": len(packed),
        "n_pairs": len(pairs),
        "n_rows": len(rows),
        "n_jev_dark": sum(1 for row in rows if row.get("jev_dark")),
        "apply": None,
        "place": None,
        "order_send": False,
        "never_broker_place": True,
        "never_merge_R": True,
        "pairs": shown,
        "rows": rows,
    }


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "model": MODEL,
                "api": API_URL,
                "questions": list(harvest_questions()),
                "order_send": False,
            },
            indent=2,
        )
    )
