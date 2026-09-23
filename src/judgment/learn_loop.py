"""LEARN_LOOP_V0 — Challenge close → symbol_state snapshot → research store.

Every instrument. Shadow / prove first. Jev never places.
Every decision in this module, including every parameter, is the System One
return for that state. One piece: the questions for a state go on one
``jev_client.evaluate`` with model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
A return is a Noul, a Choice, or a Score. Prior outcomes are attached on
every ask. An empty answer, a tie, or an error leaves that return unset.
Validated patterns become named Nouls/Choices — never silent APPLY.
Do not invent NEWS_PROTOCOL. Do not flatten. Prefer Challenge deals /
closed_doc / exit_class over April historical.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .bars import books_for_symbol, normalize_symbol
from .challenge_shadow import ACCOUNT, challenge_as_of, score_position
from .fluid_local import local_flow_stance
from .hold_from_tape import classify_close, close_session_named, named_exit_class, realized_r
from .place_apply import research_never_stamp
from .process_lock import stamp_lock
from .two_stop import closed_doc_from_deals

MappingLike = dict[str, Any]

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.learn_loop.v0"
CLOSE_LOOP_SCHEMA = "gtos.close_loop.v1"
PROMOTION_SCHEMA = "gtos.judgment.learn_loop.promotion.v0"
SCOREBOARD_SCHEMA = "gtos.judgment.learn_loop.scoreboard.v0"
LEARN_LOOP_ENV = "GTOS_JEV_LEARN_LOOP"
LEARN_LOOP_PATH_ENV = "GTOS_JEV_LEARN_LOOP_PATH"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "learn_loop_v0" / "fixtures" / "challenge_closes.jsonl"
)
DEFAULT_STORE = REPO_ROOT / "judgment" / "astra" / "lab" / "learn_loop_v0" / "store.jsonl"
CLOSE_LOOP_LOCK = REPO_ROOT / "judgment" / "astra" / "lab" / "learn_loop_v0" / "CLOSE_LOOP_V1.json"
CLOSE_LOOP_BATCH = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "learn_loop_v0" / "CLOSE_LOOP_BATCH_V1.json"
)

CHAIR_TICKETS = frozenset({293611741, 293540988})
MISS_TYPES = frozenset({"event_gap", "ok_win", "false_structure", "unlabeled"})
ASSET_CLASSES = frozenset({"XAU", "FX", "INDEX", "CRYPTO", "OTHER"})
LOCKED_EXIT = frozenset({"orig_stop", "orig_tp", "time_stop", "breach_flatten", "other"})

SNAPSHOT_KEYS = (
    "identity.symbol",
    "identity.side",
    "identity.sleeve",
    "identity.family_class",
    "clock.weekday_name",
    "clock.is_friday",
    "sessions.named",
    "sessions.utc_hour",
    "flow.stance",
    "cost.spread_r_of_stop",
    "cost.hurtful",
    "geometry.plan_r",
    "geometry.stop_dist",
    "occupancy.two_stop_exhausted",
    "occupancy.same_sleeve_orig_stops_utc_day",
    "news.spine_empty",
    "news.high_in_f5_window",
    "completeness.state_sufficient_for_live",
    "completeness.timeframes_m15_h4",
    "completeness.missing_fields",
)



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

def _f(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


_LIMIT_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "daily_loss_pct",
})
_BANNED_TEXT = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "110000",
    "110,000",
    "110_000",
    "110k",
)
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_DROP = object()
_MISS_CRITERIA = {
    "event_gap": "The miss is an event gap.",
    "ok_win": "The miss is an ok win.",
    "false_structure": "The miss is false structure.",
    "unlabeled": "The miss has no named type.",
}
_ASSET_CRITERIA = {
    "XAU": "The symbol is gold.",
    "CRYPTO": "The symbol is bitcoin or ether.",
    "INDEX": "The symbol is a cash index.",
    "FX": "The symbol is a currency pair.",
    "OTHER": "The symbol is outside gold, crypto, index, and FX.",
}
_EXIT_OTHER_CRITERIA = {
    "other": "The named exit sits outside orig_stop, orig_tp, time_stop, and breach_flatten.",
    "locked_exit": "The named exit is one of the locked exits.",
}
_BRANCH_CRITERIA = {
    "event_gap": "The cluster miss is an event gap.",
    "ok_win": "The cluster miss is an ok win.",
    "false_structure": "The cluster miss is false structure.",
    "time_stop": "The cluster exit is the time stop.",
    "orig_tp": "The cluster exit is the original target.",
    "orig_stop": "The cluster exit is the original stop.",
}
_PRIMITIVE_CRITERIA = {
    "noul": "The validated cluster is a Noul.",
    "choice": "The validated cluster is a Choice.",
}
_QUESTION_CRITERIA = {
    "event_proximity": "The question is event proximity.",
    "admit": "The question is admit.",
    "hold_too_late": "The question is hold too late.",
    "close_label": "The question is the close label.",
    "time_stop_vs_orig": "The question is time stop versus the original stop.",
}
_BRANCH_HINT = {
    "event_gap": (
        "event_gap — prove existing event_proximity / size_tilt. "
        "Do not invent NEWS_PROTOCOL."
    ),
    "ok_win": "ok_win — split FX vs XAU R books in research. Not APPLY.",
    "false_structure": "false_structure — draft admit abstain. Not an envelope.",
    "time_stop": "time_stop cluster — draft hold_too_late Noul. Do not flatten.",
    "orig_tp": "orig_tp — draft admit. Chair still speaks. orig_tp is locked.",
    "orig_stop": "orig_stop cluster — keep 2-stop COUNT as integer; this is LABEL only.",
}
_ANSWER_KEYS = ("answer", "choice", "score", "value", "noul", "probabilities", "default")


def _limit_key(name: str) -> bool:
    return name.strip().lower() in _LIMIT_KEYS


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED_TEXT)


def _banned_number(number: float) -> bool:
    return abs(number - 90000.0) < 1e-9 or abs(number - 110000.0) < 1e-9


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
        if _banned_text(value):
            return _DROP
        return value
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        number = _finite(value)
        if number is None or _banned_number(number):
            return _DROP
        return value
    return str(value)


def _levels(facts: Mapping[str, Any]) -> list[str]:
    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        if _limit_key(key):
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(str(child_key), child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            for item in value:
                walk(key, item)
            return
        number = _finite(value)
        if number is None or _banned_number(number):
            return
        found.append(number)

    for key, value in dict(facts).items():
        walk(str(key), value)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    block = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(text) for key, text in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(criteria))
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
            block["type"] = "choice"
            block["instructions"] = instructions
            block["criteria"] = {str(key): str(text) for key, text in criteria.items()}
    except Exception:
        pass
    for key in _ANSWER_KEYS:
        block.pop(key, None)
    return {qid: block}


def _score_question(qid: str, instructions: str, facts: Mapping[str, Any]) -> dict[str, Any]:
    """Count, price, or other amount on this card. An ordinal keeps its words."""
    _bind_card(facts)
    return _shape_score(qid, instructions, None, wrapped=True)



def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes for this state.",
                "false": "No for this state.",
            },
        }
    }


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"choice", ""}:
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


def _local_unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    for name in order:
        if name not in numeric:
            continue
        prob = numeric[name]
        if best_p is None or prob > best_p:
            best = name
            best_p = prob
            tied = False
        elif prob == best_p:
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
    if _local_unique(numeric, order) != str(picked):
        return None
    return str(picked)


def _score_value(block: Any, qid: str | None = None) -> float | None:
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))

    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"score", ""}:
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


def _noul_value(block: Any) -> bool | float | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() not in {"noul", ""}:
        return None
    if "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _remember(facts: Mapping[str, Any], qid: str, value: Any, error: str | None) -> None:
    try:
        from .jev_questions import append_outcome

        append_outcome(qid, value, facts, error=error)
    except Exception:
        return


def _post(facts: Mapping[str, Any], questions: Mapping[str, Any]) -> tuple[dict[str, Any], str | None]:
    """One evaluate. Priors ride on this ask. An empty body stays empty."""

    cleaned = _scrub(dict(facts))
    state = cleaned if isinstance(cleaned, dict) else {}
    state["model"] = MODEL
    if state.get("login") in (None, ""):
        state["login"] = ACCOUNT.get("login") if isinstance(ACCOUNT, dict) else None
    if state.get("ns") in (None, ""):
        state["ns"] = ACCOUNT.get("ns") if isinstance(ACCOUNT, dict) else None
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
        state["prior_outcomes"] = loaded if loaded is not None else []
    except Exception:
        state["prior_outcomes"] = []
    try:
        from .jev_client import evaluate
    except Exception:
        return {}, "import_failed"
    try:
        receipt = evaluate(
            state,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:
        return {}, type(exc).__name__
    if not isinstance(receipt, dict):
        return {}, "evaluate_not_a_dict"
    answers = receipt.get("answers")
    if not isinstance(answers, dict) or not answers:
        return {}, str(receipt.get("error") or receipt.get("skipped") or "empty")
    if receipt.get("ok") is False:
        return {}, str(receipt.get("error") or receipt.get("skipped") or "post_failed")
    return answers, None


def _choice_detail(
    facts: Mapping[str, Any],
    qid: str,
    instructions: str,
    criteria: Mapping[str, str],
) -> tuple[str | None, dict[str, float], str | None]:
    order = tuple(str(key) for key in criteria)
    answers, error = _post(facts, _choice_question(qid, instructions, criteria))
    block = answers.get(qid) if error is None else None
    probs = _probabilities(block, order)
    choice = _unique(probs, order) if error is None else None
    if choice is None:
        miss = error or ("empty" if not probs else "tie_or_empty")
    else:
        miss = None
    _remember(facts, qid, choice, miss)
    return choice, probs, miss


def _choice_ask(
    facts: Mapping[str, Any],
    qid: str,
    instructions: str,
    criteria: Mapping[str, str],
) -> str | None:
    choice, _probs, _error = _choice_detail(facts, qid, instructions, criteria)
    return choice


def _score_ask(facts: Mapping[str, Any], qid: str, instructions: str) -> float | None:
    _bind_card(facts)
    answers, error = _post(facts, _score_question(qid, instructions, facts))
    value = _score_value(answers.get(qid), qid) if error is None else None
    miss = None if value is not None else (error or "score_missing")
    _remember(facts, qid, value, miss)
    return value


def _noul_ask(facts: Mapping[str, Any], qid: str, instructions: str) -> bool | float | None:
    answers, error = _post(facts, _noul_question(qid, instructions))
    value = _noul_value(answers.get(qid)) if error is None else None
    _remember(facts, qid, value, None if value is not None else (error or "noul_missing"))
    return value


def _named_exit(named: str | None) -> str | None:
    """Relabel only when the returned choice is ``other``. A miss leaves the exit as it is."""

    choice = _choice_ask(
        {"named_exit": named},
        "learn_loop_exit_other",
        (
            "Is this named exit outside the locked exits? "
            "The unique highest probability is the decision. "
            "An empty answer or a tie leaves the exit unchanged. "
            "Do not send an order."
        ),
        _EXIT_OTHER_CRITERIA,
    )
    if choice == "other":
        return "other"
    return named


def _read_choice(
    facts: Mapping[str, Any],
    answers: Mapping[str, Any],
    error: str | None,
    qid: str,
    criteria: Mapping[str, str],
) -> str | None:
    order = tuple(str(key) for key in criteria)
    if error is not None:
        _remember(facts, qid, None, error)
        return None
    probs = _probabilities(answers.get(qid), order)
    choice = _unique(probs, order)
    miss = None if choice is not None else ("empty" if not probs else "tie_or_empty")
    _remember(facts, qid, choice, miss)
    return choice


def _promotion_fields(
    facts: Mapping[str, Any],
    n: int,
    prove: str | None = None,
    *,
    with_branch: bool = False,
) -> dict[str, Any]:
    """One ask. Primitive, question, component, and the count are that return."""

    _bind_card(facts)
    questions: dict[str, Any] = {}
    if with_branch:
        questions.update(_choice_question(
            "learn_loop_promotion_branch",
            (
                "Which promotion branch does this cluster wear? "
                "The unique highest probability is the branch. "
                "An empty answer or a tie leaves the branch unset. "
                "Do not send an order."
            ),
            _BRANCH_CRITERIA,
        ))
    questions.update(_choice_question(
        "learn_loop_proposed_primitive",
        (
            "Is this cluster a Noul or a Choice? "
            "The unique highest probability is the primitive. "
            "An empty answer or a tie leaves the primitive unset. "
            "Do not send an order."
        ),
        _PRIMITIVE_CRITERIA,
    ))
    questions.update(_choice_question(
        "learn_loop_proposed_question",
        (
            "Which question does this cluster propose? "
            "The unique highest probability is the question. "
            "An empty answer or a tie leaves the question unset. "
            "Do not send an order."
        ),
        _QUESTION_CRITERIA,
    ))
    questions.update(_noul_question(
        "learn_loop_component_exists",
        (
            "Does the proposed component exist for this cluster? "
            "An empty answer leaves existence unset. "
            "Do not send an order."
        ),
    ))
    questions.update(_score_question(
        "learn_loop_promotion_min_n",
        (
            "The score you return is the promotion count for this cluster. "
            "It may sit between the levels on this state. "
            "An empty score leaves the count unset. "
            "Do not send an order."
        ),
        facts,
    ))
    answers, error = _post(facts, questions)
    branch = (
        _read_choice(facts, answers, error, "learn_loop_promotion_branch", _BRANCH_CRITERIA)
        if with_branch
        else None
    )
    primitive = _read_choice(
        facts, answers, error, "learn_loop_proposed_primitive", _PRIMITIVE_CRITERIA
    )
    question = _read_choice(
        facts, answers, error, "learn_loop_proposed_question", _QUESTION_CRITERIA
    )
    exists = _noul_value(answers.get("learn_loop_component_exists")) if error is None else None
    bound = _score_value(answers.get("learn_loop_promotion_min_n"), "learn_loop_promotion_min_n") if error is None else None
    _remember(
        facts,
        "learn_loop_component_exists",
        exists,
        None if exists is not None else (error or "noul_missing"),
    )
    _remember(
        facts,
        "learn_loop_promotion_min_n",
        bound,
        None if bound is not None else (error or "score_missing"),
    )
    if bound is None:
        status = None
        nxt = None
    elif n < bound:
        status = "UNDERPOWERED_SHADOW"
        nxt = "collect_more_challenge_closes"
    else:
        status = "SHADOW"
        nxt = "prove_on_challenge_tape_then_chair_ritual"
    if prove:
        hint = prove
    elif branch:
        hint = _BRANCH_HINT.get(branch)
    else:
        hint = None
    return {
        "promotion_branch": branch,
        "proposed_primitive": primitive,
        "proposed_question": question,
        "component_exists": exists,
        "promotion_min_n": bound,
        "status": status,
        "next": nxt,
        "hint": hint,
    }


def load_close_loop_lock() -> dict[str, Any]:
    if not CLOSE_LOOP_LOCK.is_file():
        return {"schema": CLOSE_LOOP_SCHEMA, "locked": True, "orig_tp_locked": True}
    payload = json.loads(CLOSE_LOOP_LOCK.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {"schema": CLOSE_LOOP_SCHEMA}


def load_close_loop_batch(path: Path | None = None) -> dict[str, Any] | None:
    """Chair-sealed Challenge batch. Aggregates only — no invented tickets."""
    target = Path(path) if path is not None else CLOSE_LOOP_BATCH
    if not target.is_file():
        return None
    payload = json.loads(target.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def batch_identity_ok(batch: MappingLike | None) -> bool:
    if not batch:
        return False
    exits = batch.get("exit_class") or {}
    misses = batch.get("miss_type") or {}
    assets = batch.get("by_asset_class") or {}
    n = int(batch.get("n") or 0)
    return (
        n == 48
        and sum(int(v) for v in exits.values()) == 48
        and sum(int(v) for v in misses.values()) == 48
        and sum(int((v or {}).get("n") or 0) for v in assets.values()) == 48
        and int(exits.get("orig_tp") or 0) == 2
        and batch.get("tickets_invented") is False
    )


def is_learn_row(row: MappingLike) -> bool:
    if row.get("skipped"):
        return False
    return row.get("schema") == SCHEMA or row.get("close_loop") == CLOSE_LOOP_SCHEMA


def named_miss_type(raw: Any) -> str | None:
    """A recorded miss type stays. Anything else is the returned choice, or unset."""

    text = str(raw or "").strip().lower()
    if text in MISS_TYPES:
        return text
    if set(_MISS_CRITERIA) != set(MISS_TYPES):
        return None
    return _choice_ask(
        {"miss_type": text},
        "learn_loop_miss_type",
        (
            "What miss type does this Challenge close wear? "
            "The unique highest probability is the type. "
            "An empty answer or a tie leaves the type unset. "
            "Do not send an order."
        ),
        _MISS_CRITERIA,
    )


def asset_class(symbol: str | None) -> str | None:
    """The asset class is the returned choice. An empty answer leaves it unset."""

    if set(_ASSET_CRITERIA) != set(ASSET_CLASSES):
        return None
    sym = normalize_symbol(symbol)
    return _choice_ask(
        {"symbol": sym or ""},
        "learn_loop_asset_class",
        (
            "Which asset class is this Challenge symbol? "
            "The unique highest probability is the class. "
            "An empty answer or a tie is not a class. "
            "Do not send an order."
        ),
        _ASSET_CRITERIA,
    )


def _nested(payload: MappingLike, path: str) -> Any:
    cur: Any = payload
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def learn_loop_enabled() -> bool:
    return os.environ.get(LEARN_LOOP_ENV, "").strip().lower() in {"1", "true", "yes"}


def default_store_path() -> Path:
    override = (os.environ.get(LEARN_LOOP_PATH_ENV) or "").strip()
    return Path(override) if override else DEFAULT_STORE


def tape_uses_april_historical(state: MappingLike | None) -> bool:
    """True when a timeframe source_path is April repo historical. Forbidden here."""
    if not state:
        return False
    for block in (state.get("timeframes") or {}).values():
        if not isinstance(block, dict):
            continue
        path = str(block.get("source_path") or "")
        if "data/historical" in path or "historical_2026" in path:
            return True
    return False


def symbol_state_snapshot(state: MappingLike, *, extra: MappingLike | None = None) -> dict[str, Any]:
    """Typed keys from gold_state.v0 (the closed symbol_state object)."""
    extra = extra or {}
    flow = local_flow_stance(state)
    spread = _nested(state, "cost.spread_r_of_stop")
    if spread is None:
        spread = _nested(state, "cost.spread_r")
    spread_n = _finite(spread)
    hurtful = None
    if spread_n is not None:
        hurtful = _noul_ask(
            {
                "symbol": _nested(state, "identity.symbol"),
                "spread_r_of_stop": spread_n,
            },
            "learn_loop_cost_hurtful",
            (
                "Does this spread cost hurt the stop on this close? "
                "The noul you return is that. "
                "An empty answer leaves it unset. "
                "Do not send an order."
            ),
        )
    news = state.get("news") or {}
    high = news.get("high_in_f5_window") if not news.get("spine_empty") else None
    out: dict[str, Any] = {
        "identity.symbol": _nested(state, "identity.symbol"),
        "identity.side": _nested(state, "identity.side"),
        "identity.sleeve": _nested(state, "identity.sleeve"),
        "identity.family_class": _nested(state, "identity.family_class"),
        "clock.weekday_name": _nested(state, "clock.weekday_name"),
        "clock.is_friday": _nested(state, "clock.is_friday"),
        "sessions.named": _nested(state, "sessions.named"),
        "sessions.utc_hour": _nested(state, "sessions.utc_hour"),
        "flow.stance": flow,
        "cost.spread_r_of_stop": spread,
        "cost.hurtful": hurtful,
        "geometry.plan_r": _nested(state, "geometry.plan_r"),
        "geometry.stop_dist": _nested(state, "geometry.stop_dist"),
        "occupancy.two_stop_exhausted": _nested(state, "occupancy.two_stop_exhausted"),
        "occupancy.same_sleeve_orig_stops_utc_day": _nested(
            state, "occupancy.same_sleeve_orig_stops_utc_day"
        ),
        "news.spine_empty": bool(news.get("spine_empty")),
        "news.high_in_f5_window": high,
        "completeness.state_sufficient_for_live": _nested(
            state, "completeness.state_sufficient_for_live"
        ),
        "completeness.timeframes_m15_h4": _nested(state, "completeness.timeframes_m15_h4"),
        "completeness.missing_fields": list(_nested(state, "completeness.missing_fields") or []),
    }
    if extra.get("close_session"):
        out["sessions.close_named"] = extra.get("close_session")
    return out


def regime_tags(
    snapshot: MappingLike,
    *,
    exit_class: str | None,
    miss_type: str | None = None,
    asset: str | None = None,
) -> list[str]:
    tags: list[str] = []
    # Close session only. Do not wear as_of=now() or the open session as the close.
    session = snapshot.get("sessions.close_named") or "unassembled"
    tags.append(f"session:{session}")
    flow = snapshot.get("flow.stance") or "no_clear_flow"
    tags.append(f"flow:{flow}")
    family = snapshot.get("identity.family_class") or "unknown"
    tags.append(f"family:{family}")
    if snapshot.get("cost.hurtful") is True:
        tags.append("cost:hurtful")
    elif snapshot.get("cost.spread_r_of_stop") is None:
        tags.append("cost:unassembled")
    else:
        tags.append("cost:ordinary")
    exhausted = snapshot.get("occupancy.two_stop_exhausted")
    if exhausted is True:
        tags.append("occupancy:two_stop_exhausted")
    elif exhausted is False:
        tags.append("occupancy:clear")
    else:
        tags.append("occupancy:unassembled")
    tags.append(f"close:{exit_class or 'unlabeled'}")
    symbol = normalize_symbol(str(snapshot.get("identity.symbol") or ""))
    tags.append(f"symbol:{symbol or 'unknown'}")
    asset_named = asset if asset not in (None, "") else asset_class(symbol)
    if asset_named is not None:
        tags.append(f"asset:{asset_named}")
    miss_named = named_miss_type(miss_type)
    if miss_named is not None:
        tags.append(f"miss:{miss_named}")
    if snapshot.get("news.spine_empty"):
        tags.append("news:spine_empty")
    elif snapshot.get("news.high_in_f5_window") is True:
        tags.append("news:named_high_in_window")
    else:
        tags.append("news:no_invented_high")
    return tags


def natural_key(row: MappingLike) -> tuple[str, str, str, str]:
    return (
        str(row.get("login") or ACCOUNT["login"]),
        str(row.get("ticket") or ""),
        str(row.get("exit_class") or ""),
        str(row.get("close_utc") or ""),
    )


def normalize_close_deal(deal: MappingLike) -> dict[str, Any]:
    """Label a Challenge close. Do not invent prices or NEWS_PROTOCOL rows."""
    rec = dict(deal)
    rec["_kind"] = rec.get("_kind") or "deal_close"
    named = named_exit_class(rec.get("close_reason") or rec.get("reason"), rec.get("exit_class"))
    if named:
        rec["exit_class"] = named
    entry = _f(rec.get("entry") or rec.get("open") or rec.get("open_price"))
    stop = _f(rec.get("orig_sl") or rec.get("sl") or rec.get("stop"))
    target = _f(rec.get("orig_tp") or rec.get("tp"))
    exit_px = _f(rec.get("exit") or rec.get("close") or rec.get("close_price"))
    stop_dist = _f(rec.get("stop_dist"))
    if stop_dist is None and entry is not None and stop is not None:
        stop_dist = abs(entry - stop)
        rec["stop_dist"] = stop_dist
    exit_source = rec.get("exit_source")
    if exit_px is None and named == "orig_stop" and stop is not None:
        rec["exit"] = stop
        rec["exit_source"] = "geometry_implied_orig_sl"
    elif exit_px is None and named == "orig_tp" and target is not None:
        rec["exit"] = target
        rec["exit_source"] = "geometry_implied_orig_tp"
    elif exit_px is not None and not exit_source:
        rec["exit_source"] = "broker_exit"
    rec.setdefault("entry", entry)
    rec.setdefault("orig_sl", stop)
    rec.setdefault("tp", target)
    rec["still_open"] = bool(rec.get("still_open"))
    rec["login"] = rec.get("login") or ACCOUNT["login"]
    return rec


class LearnLoopStore:
    """Append-only JSONL. Existing natural keys are not rewritten."""

    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else default_store_path()

    def load(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        with self.path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows

    def known_keys(self) -> set[tuple[str, str, str, str]]:
        return {natural_key(row) for row in self.load()}

    def append(self, row: MappingLike) -> dict[str, Any]:
        payload = dict(row)
        key = natural_key(payload)
        if key in self.known_keys():
            return {**payload, "appended": False, "duplicate": True}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")
        return {**payload, "appended": True, "duplicate": False}


def _answers_shadow(row: MappingLike) -> dict[str, Any]:
    answers = row.get("answers") or {}
    fluid = ((row.get("compose") or {}).get("fluid") or {}).get("gates") or {}
    local = {}
    for question in ("admit", "close_label", "flow_stance", "cost_hurtful", "hold_too_late"):
        block = answers.get(question)
        if isinstance(block, dict):
            local[question] = {
                "choice": block.get("choice"),
                "noul": block.get("noul"),
                "score": block.get("score"),
                "source": block.get("source") or "jev",
            }
    # Fluid stamp is the local instrument when Jev is skipped.
    for gid, gate in fluid.items():
        if not isinstance(gate, dict):
            continue
        q = gate.get("question")
        if q in {"admit", "close_label", "flow_stance", "cost_hurtful", "hold_too_late"} and q not in local:
            local[q] = {
                "choice": gate.get("shadow") if gate.get("effect") != "size_tilt" else None,
                "noul": gate.get("shadow") if gate.get("effect") != "size_tilt" else None,
                "shadow": gate.get("shadow"),
                "source": gate.get("source") or "fluid_local",
                "gate_id": gid,
            }
    return local


def learn_from_close(
    deal: MappingLike,
    *,
    books=None,
    spines=None,
    sit_meta: MappingLike | None = None,
    store: LearnLoopStore | None = None,
    deal_tape=None,
    siblings_doc=None,
    feature_rows=None,
    host_events=None,
) -> dict[str, Any]:
    """Score one Challenge close into an append-only research row. Never places."""
    rec = normalize_close_deal(deal)
    if rec.get("still_open"):
        return {
            "schema": SCHEMA,
            "skipped": "still_open",
            "ticket": rec.get("ticket"),
            "never_place": True,
            "apply": False,
        }
    empty_spine = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    scored = score_position(
        rec,
        # None loads per-symbol Challenge tape. {} is the XAU empty-cache
        # trap in books_for_symbol — do not coerce None to {}.
        books=books,
        spines=spines if spines is not None else empty_spine,
        sit_meta=dict(sit_meta or {}),
        deal_tape=deal_tape,
        siblings_doc=siblings_doc,
        feature_rows=feature_rows,
        host_events=host_events,
    )
    state = scored.get("state") or {}
    compose = scored.get("compose") or {}
    named = rec.get("exit_class") or named_exit_class(rec.get("close_reason"), rec.get("exit_class"))
    inventory = classify_close(rec.get("close_reason"), rec.get("exit_class"))
    close_utc = None
    close_dt = None
    if rec.get("close_time_utc") or rec.get("close_time"):
        close_dt = challenge_as_of(
            {
                "open_time_utc": rec.get("close_time_utc") or rec.get("close_time"),
                "open_time_server": rec.get("close_time_server"),
            }
        )
        close_utc = close_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    extra = {
        "kind": rec.get("_kind"),
        "close_reason": rec.get("close_reason") or rec.get("reason"),
        "exit_class": rec.get("exit_class"),
        "close_session": close_session_named(close_dt),
    }
    snapshot = symbol_state_snapshot(state, extra=extra)
    miss = named_miss_type(rec.get("miss_type"))
    asset = rec.get("asset_class") or asset_class(rec.get("symbol") or snapshot.get("identity.symbol"))
    tags = regime_tags(snapshot, exit_class=named, miss_type=miss, asset=asset)
    geometry_r = realized_r(
        entry=_f(rec.get("entry")),
        exit_px=_f(rec.get("exit")),
        stop_dist=_f(rec.get("stop_dist")),
        side=str(rec.get("side") or rec.get("direction") or ""),
    )
    realized = _f(rec.get("R"))
    r_source = rec.get("r_source") or rec.get("exit_source")
    if r_source != "sit_backstop" and realized is None:
        realized = geometry_r
        r_source = rec.get("exit_source") or (
            "broker_exit" if rec.get("exit") is not None else "unassembled"
        )
    if realized is None and r_source != "sit_backstop":
        r_source = "unassembled"
    if r_source == "sit_backstop" and realized is None:
        r_source = "unassembled"
    closed_label = closed_doc_from_deals([rec], stamp=challenge_as_of)
    april = tape_uses_april_historical(state)
    diagnosis = scored.get("diagnosis") or ""
    if april:
        diagnosis = (diagnosis + "; april_historical_rejected").strip("; ")
    named = _named_exit(named if isinstance(named, str) else (str(named) if named else None))
    row = {
        "schema": SCHEMA,
        "close_loop": CLOSE_LOOP_SCHEMA,
        "account_surface": ACCOUNT,
        "login": rec.get("login") or ACCOUNT["login"],
        "kind": "close_learn",
        "ticket": rec.get("ticket"),
        "symbol": rec.get("symbol") or snapshot.get("identity.symbol"),
        "symbol_norm": normalize_symbol(str(rec.get("symbol") or "")),
        "asset_class": asset,
        "sleeve": rec.get("sleeve") or snapshot.get("identity.sleeve"),
        "side": rec.get("side") or snapshot.get("identity.side"),
        "exit_class": named,
        "close_label": inventory,
        "close_reason": rec.get("close_reason"),
        "miss_type": miss,
        "prove_next": rec.get("prove_next"),
        "R": realized,
        "r_source": r_source,
        "geometry_R": geometry_r,
        "close_utc": close_utc,
        "regime_tags": tags,
        "snapshot": snapshot,
        "answers_shadow": _answers_shadow(scored),
        "compose_shadow": {
            "never_place": True,
            "disposition": compose.get("disposition"),
            "live_size_tilt": compose.get("live_size_tilt"),
            "live_cost_tilt": compose.get("live_cost_tilt"),
            "shadow_size_tilt": compose.get("shadow_size_tilt"),
            "shadow_cost_tilt": compose.get("shadow_cost_tilt"),
            "apply_this_row": False,
            "leave_orig": compose.get("leave_orig"),
            "jev_admit": compose.get("jev_admit"),
        },
        "closed_doc_row": (closed_label or {}).get("closed", [None])[0] if closed_label else None,
        "closed_doc_source": (closed_label or {}).get("two_stop_source"),
        "missing_state": scored.get("missing_state") or [],
        "diagnosis": diagnosis,
        "house": scored.get("house"),
        "provenance": rec.get("provenance") or rec.get("fixture_id"),
        "exit_source": rec.get("exit_source"),
        "april_historical_used": april,
        "news_protocol_invented": False,
        "apply": False,
        "silent_apply": False,
        "logged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **stamp_lock(),
        **research_never_stamp(),
    }
    if store is not None:
        stored = store.append(row)
        row["appended"] = stored.get("appended")
        row["duplicate"] = stored.get("duplicate")
    return row


def _r_bucket() -> dict[str, Any]:
    return {"n": 0, "orig_stop": 0, "orig_tp": 0, "time_stop": 0, "other": 0, "R": []}


def _finish_r_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    rs = bucket.pop("R")
    return {
        **bucket,
        "mean_R": (sum(rs) / len(rs)) if rs else None,
        "n_with_R": len(rs),
        "sum_R": (sum(rs) if rs else None),
    }


def _tally(bucket: dict[str, Any], rec: MappingLike, r_all: list[float]) -> None:
    bucket["n"] += 1
    cls = rec.get("exit_class")
    if cls not in (None, ""):
        name = str(cls)
        if name in bucket:
            bucket[name] += 1
        else:
            bucket["other"] += 1
    if rec.get("R") is not None:
        bucket["R"].append(float(rec["R"]))
        r_all.append(float(rec["R"]))


def scoreboard(records: Iterable[MappingLike]) -> dict[str, Any]:
    rows = [r for r in records if is_learn_row(r)]
    by_symbol: dict[str, dict[str, Any]] = {}
    by_asset: dict[str, dict[str, Any]] = {}
    by_exit: dict[str, int] = defaultdict(int)
    by_miss: dict[str, int] = defaultdict(int)
    r_all: list[float] = []
    seeded: dict[str, Any] = {}
    for rec in rows:
        sym = str(rec.get("symbol_norm") or rec.get("symbol") or "unknown")
        asset_name = rec.get("asset_class")
        if asset_name in (None, ""):
            asset_name = asset_class(sym)
        _tally(by_symbol.setdefault(sym, _r_bucket()), rec, r_all)
        # Asset split uses its own R list — do not double-count r_all.
        if asset_name is not None:
            asset_rs: list[float] = []
            _tally(by_asset.setdefault(str(asset_name), _r_bucket()), rec, asset_rs)
        exit_name = rec.get("exit_class")
        if exit_name not in (None, ""):
            by_exit[str(exit_name)] += 1
        miss_name = rec.get("miss_type")
        if miss_name not in (None, ""):
            by_miss[str(miss_name)] += 1
        ticket = rec.get("ticket")
        if ticket in CHAIR_TICKETS or str(ticket) in {str(t) for t in CHAIR_TICKETS}:
            seeded[str(ticket)] = {
                "symbol": rec.get("symbol"),
                "exit_class": rec.get("exit_class"),
                "R": rec.get("R"),
                "r_source": rec.get("r_source"),
                "miss_type": rec.get("miss_type"),
                "prove_next": rec.get("prove_next"),
                "asset_class": asset_name,
            }
    return {
        "schema": SCOREBOARD_SCHEMA,
        "close_loop": CLOSE_LOOP_SCHEMA,
        "account": ACCOUNT["login"],
        "ns": ACCOUNT["ns"],
        "n_closes": len(rows),
        "by_symbol": {k: _finish_r_bucket(v) for k, v in by_symbol.items()},
        "by_asset_class": {k: _finish_r_bucket(v) for k, v in by_asset.items()},
        "by_exit_class": dict(by_exit),
        "by_miss_type": dict(by_miss),
        "seeded": seeded,
        "mean_R": (sum(r_all) / len(r_all)) if r_all else None,
        "sum_R": (sum(r_all) if r_all else None),
        "n_with_R": len(r_all),
        "never_place": True,
        "apply": False,
        "language": (
            "Challenge-true close_loop.v1 scoreboard: orig_stop / orig_tp / "
            "time_stop / breach_flatten. Asset-class split is prove, not APPLY. "
            "Not April historical. Jev never places."
        ),
        "sample_n": len(rows),
        "batch": load_close_loop_batch(),
    }


def prove_asset_class_split(batch: MappingLike | None = None) -> dict[str, Any]:
    """Asset-class prove from the sealed Challenge batch. Never APPLY."""
    packed = dict(batch or load_close_loop_batch() or {})
    assets = packed.get("by_asset_class") or {}
    candidates: list[dict[str, Any]] = []
    hints = {
        "INDEX": (
            "INDEX n=16 mean_R=-1.04, 0 wins — prove admit abstain / keep "
            "house_hard_off (mx_us30, idxrev). Not an envelope. Not APPLY."
        ),
        "CRYPTO": (
            "CRYPTO n=3 all stops — UNDERPOWERED. Keep orb_crypto hard-off. "
            "Do not invent a mean_R. Not APPLY."
        ),
        "XAU": (
            "XAU n=23 mean_R=-0.37 — prove event_gap size-cut on existing "
            "event_proximity / size_tilt (dsp_shakeout BOJ T±60). "
            "Do not invent NEWS_PROTOCOL."
        ),
        "FX": (
            "FX n=6 ≈flat — prove split FX-cross vs XAU R books in Warsh "
            "windows. Do not wear XAU tape on FX. Not APPLY."
        ),
    }
    for name in ("INDEX", "CRYPTO", "XAU", "FX"):
        block = assets.get(name) or {}
        n = int(block.get("n") or 0)
        if n <= 0:
            continue
        decision = _promotion_fields(
            {
                "asset_class": name,
                "n": n,
                "mean_R": block.get("mean_R"),
                "wins": block.get("wins"),
            },
            n,
            prove=hints[name],
        )
        candidates.append(
            {
                "pattern": f"batch_asset={name}",
                "asset_class": name,
                "n": n,
                "mean_R": block.get("mean_R"),
                "wins": block.get("wins"),
                "proposed_primitive": decision["proposed_primitive"],
                "proposed_question": decision["proposed_question"],
                "component_exists": decision["component_exists"],
                "promotion_min_n": decision["promotion_min_n"],
                "hint": decision["hint"],
                "status": decision["status"],
                "apply": False,
                "silent_apply": False,
                "chair": "LABEL",
                "next": decision["next"],
            }
        )
    false_n = int((packed.get("miss_type") or {}).get("false_structure") or 0)
    if false_n:
        false_hint = (
            "false_structure 39/48 — draft admit abstain on Challenge "
            "tape. Dominant miss. Not an envelope. Not APPLY."
        )
        false_decision = _promotion_fields(
            {"miss_type": "false_structure", "n": false_n},
            false_n,
            prove=false_hint,
        )
        candidates.append(
            {
                "pattern": "batch_miss=false_structure",
                "miss_type": "false_structure",
                "n": false_n,
                "proposed_primitive": false_decision["proposed_primitive"],
                "proposed_question": false_decision["proposed_question"],
                "component_exists": false_decision["component_exists"],
                "promotion_min_n": false_decision["promotion_min_n"],
                "hint": false_decision["hint"],
                "status": false_decision["status"],
                "apply": False,
                "silent_apply": False,
                "chair": "LABEL",
                "next": false_decision["next"],
            }
        )
    return {
        "schema": "gtos.judgment.learn_loop.asset_split_prove.v0",
        "close_loop": CLOSE_LOOP_SCHEMA,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "apply": False,
        "silent_apply": False,
        "batch_n": packed.get("n"),
        "batch_identity_ok": batch_identity_ok(packed),
        "candidates": candidates,
        "n_candidates": len(candidates),
        "note": (
            "Batch prove is not the 6-row fixture pack. Do not invent the "
            "other 46 tickets. Chair ritual required to APPLY."
        ),
    }


def propose_noul_choices(records: Iterable[MappingLike]) -> dict[str, Any]:
    """How a validated cluster becomes a named Noul/Choice. Never APPLY."""
    clusters: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        if not is_learn_row(rec):
            continue
        snap = rec.get("snapshot") or {}
        raw_miss = rec.get("miss_type")
        miss_key = raw_miss if raw_miss not in (None, "") else named_miss_type(raw_miss)
        asset_key = rec.get("asset_class")
        if asset_key in (None, ""):
            asset_key = asset_class(rec.get("symbol"))
        key = (
            asset_key,
            miss_key,
            rec.get("exit_class"),
            snap.get("identity.family_class"),
        )
        clusters[key].append(dict(rec))
    candidates: list[dict[str, Any]] = []
    for key, group in clusters.items():
        asset, miss, exit_c, family = key
        rs = [float(r["R"]) for r in group if r.get("R") is not None]
        n = len(group)
        prove = next((g.get("prove_next") for g in group if g.get("prove_next")), None)
        mean_r = (sum(rs) / len(rs)) if rs else None
        facts = {
            "asset_class": asset,
            "miss_type": miss,
            "exit_class": exit_c,
            "family_class": family,
            "n": n,
            "mean_R": mean_r,
        }
        decision = _promotion_fields(facts, n, prove=prove, with_branch=True)
        candidates.append(
            {
                "pattern": f"asset={asset}|miss={miss}|close={exit_c}|family={family}",
                "n": n,
                "n_with_R": len(rs),
                "mean_R": mean_r,
                "tickets": [g.get("ticket") for g in group],
                "miss_type": miss,
                "asset_class": asset,
                "prove_next": prove,
                "promotion_branch": decision["promotion_branch"],
                "proposed_primitive": decision["proposed_primitive"],
                "proposed_question": decision["proposed_question"],
                "component_exists": decision["component_exists"],
                "promotion_min_n": decision["promotion_min_n"],
                "hint": decision["hint"],
                "status": decision["status"],
                "apply": False,
                "silent_apply": False,
                "chair": "LABEL",
                "next": decision["next"],
            }
        )
    candidates.sort(key=lambda c: (-int(c["n"]), str(c["pattern"])))
    pack_min = _score_ask(
        {
            "n_clusters": len(candidates),
            "n_rows": sum(int(item["n"]) for item in candidates),
        },
        "learn_loop_pack_min_n",
        (
            "The score you return is the promotion count for this pack. "
            "It may sit between the levels on this state. "
            "An empty score leaves the count unset. "
            "Do not send an order."
        ),
    )
    return {
        "schema": PROMOTION_SCHEMA,
        "silent_apply": False,
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "apply": False,
        "min_n": pack_min,
        "path": (
            "SHADOW → prove on Challenge tape → PROVED_SHADOW → "
            "Chair ENFORCE/VETO/LABEL → APPLY only if auto_apply_eligible "
            "(size_tilt/label). Never place/remint/flatten. SEL-V4-002 stays research-only. "
            "Envelope walls stay integers."
        ),
        "candidates": candidates,
        "n_candidates": len(candidates),
        "n_underpowered": sum(1 for c in candidates if c["status"] == "UNDERPOWERED_SHADOW"),
        "note": (
            "V0 does not write JEV_GATE_INVENTORY. A Chair ritual is required to "
            "add or APPLY a Noul/Choice. Do not invent NEWS_PROTOCOL."
        ),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def load_close_fixtures(path: Path | None = None) -> list[dict[str, Any]]:
    return load_jsonl(path or DEFAULT_FIXTURES)


def run_close_harness(
    deals: Iterable[MappingLike],
    *,
    books=None,
    spines=None,
    store: LearnLoopStore | None = None,
    sit_meta: MappingLike | None = None,
) -> dict[str, Any]:
    """Shadow-score Challenge closes. No broker place."""
    packed = [normalize_close_deal(d) for d in deals]
    empty_spine = {"spine_id": None, "sources": [], "events": [], "n_files": 0}
    spines_here = spines if spines is not None else empty_spine
    cache = books if isinstance(books, dict) else None
    rows: list[dict[str, Any]] = []
    for deal in packed:
        symbol = str(deal.get("symbol") or "XAUUSD")
        books_here = books_for_symbol(symbol, cache)
        rows.append(
            learn_from_close(
                deal,
                books=books_here,
                spines=spines_here,
                sit_meta=sit_meta,
                store=store,
                feature_rows=packed,
            )
        )
    board = scoreboard(rows)
    promo = propose_noul_choices(rows)
    batch = board.get("batch")
    return {
        "schema": "gtos.judgment.learn_loop.harness.v0",
        "close_loop": CLOSE_LOOP_SCHEMA,
        "apply": False,
        "silent_apply": False,
        "april_historical_used": any(r.get("april_historical_used") for r in rows),
        "news_protocol_invented": False,
        "n_rows": len(rows),
        "rows": rows,
        "scoreboard": board,
        "promotion": promo,
        "asset_class_prove": prove_asset_class_split(batch),
        "account_surface": ACCOUNT,
        **stamp_lock(),
        **research_never_stamp(),
    }


def maybe_learn_from_close(deal: MappingLike, **kwargs: Any) -> dict[str, Any]:
    """Host-safe observer. Default off. Never places."""
    if not learn_loop_enabled():
        return {
            "schema": SCHEMA,
            "skipped": "GTOS_JEV_LEARN_LOOP_off",
            "never_place": True,
            "apply": False,
        }
    store = kwargs.pop("store", None)
    if store is None:
        store = LearnLoopStore(default_store_path())
    return learn_from_close(deal, store=store, **kwargs)


def ask_close_label() -> dict[str, Any]:
    """Learn-store close label. The unique highest probability is the label."""

    from .rung_choice import finish_learning_choice, learning_unit_state

    criteria = {
        "orig_stop": "The learn-store close label is the original stop",
        "orig_tp": "The learn-store close label is the original target",
        "time_stop": "The learn-store close label is the time stop",
        "breach_flatten": "The learn-store close label names a breach flatten and the ticket stays open",
        "other": "The learn-store close label is outside the locked exits",
    }
    if set(criteria) != set(LOCKED_EXIT):
        raise RuntimeError("close_label criteria drifted from LOCKED_EXIT")
    ns_root, state = learning_unit_state("learn_loop")
    choice, probs, error = _choice_detail(
        state,
        "close_label",
        (
            "What close label does the open Challenge unit in pair earn on the learn store? "
            "The unit is still open. The label does not close the ticket. "
            "The unique highest probability is the label. "
            "An empty answer or a tie is not a label. "
            "Do not send an order."
        ),
        criteria,
    )
    hop = {
        "asked": True,
        "ok": choice is not None,
        "question_id": "close_label",
        "model": MODEL,
        "choice": choice,
        "probability": probs.get(choice) if choice else None,
        "probabilities": probs,
        "probability_source": "probabilities" if probs else None,
        "never_place": True,
        "decision_emitted": choice is not None,
        "error": None if choice is not None else (error or "no_decision"),
        "http_status": None,
    }
    return finish_learning_choice(
        ns_root,
        "learn_loop",
        "close_label",
        hop,
        criteria,
        extra={"pair_ticket": (state.get("pair") or {}).get("ticket")},
    )


def _ask_close_label_on_load() -> None:
    if not learn_loop_enabled():
        return
    try:
        row = ask_close_label()
    except Exception as exc:
        from .rung_choice import note_load_error
        note_load_error("learn_loop", exc)
        return
    if not row.get("decision_emitted"):
        from .rung_choice import note_load_error
        note_load_error("learn_loop", RuntimeError(str(row.get("error") or "no_decision")))


_ask_close_label_on_load()
