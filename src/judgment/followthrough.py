"""Challenge follow-through. One System One piece.

One hop: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
Questions on the piece are only Noul, Choice, or Score. Prior outcomes are
attached on that ask, and the return is appended for the next ask.

The choice, the threshold, the loop bound, the parameter, and which
component exists are that return. A Score may sit between levels. An empty
answer, a tie, a missing score, or an error leaves that field unset.
A floor and a baseline are not asked.

This module does not flatten and does not send. Judge code stays unable
to send. ``GTOS_JEV_FOLLOWTHROUGH`` stays an env gate. The Challenge
login gate stays a gate.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.followthrough.v1"
FOLLOWTHROUGH_ENV = "GTOS_JEV_FOLLOWTHROUGH"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
KIND_READ = "read"
_TRUTHY_OFF = frozenset({"0", "false", "no", "off"})
_TRUTHY_ON = frozenset({"1", "true", "yes", "on"})
_SKIP_KEY_PARTS = ("floor", "baseline")
_QUESTION_TYPES = frozenset({"noul", "choice", "score"})

SEATS = (
    "leftover",
    "rescue",
    "pending",
    "cooldown",
    "chair",
    "size_physics",
    "sibling",
    "lesson",
)
BRANCH_SEATS = {
    "leftover": ("leftover",),
    "rescue": ("rescue",),
    "pending": ("pending",),
    "cooldown": ("cooldown",),
    "chair": ("chair",),
    "size": ("size_physics",),
    "sibling": ("sibling",),
    "lesson": ("lesson",),
}
SEAT_CHUNKS = {
    "leftover": ("leftover_open", "mfe_mae", "atlas"),
    "rescue": ("rescue_file", "candidate_id", "cost_dead"),
    "pending": ("pending_age", "gtc_level", "tape"),
    "cooldown": ("close_class", "age", "sibling_clock"),
    "chair": ("manage_file", "why_code", "authority"),
    "size_physics": ("lots", "stop_pips", "retry_count", "orig_sl"),
    "sibling": ("siblings_this_bar", "conviction"),
    "lesson": ("cluster_set", "nightly_body"),
}
COMPONENT_ORDER = SEATS
CHOICE_ORDER = {
    "takeoff_label": ("orig_stop", "time_stop", "takeoff", "leave_orig", "abstain"),
    "rescue_action": ("rebind", "leave", "abstain"),
    "chair_manage_noun": ("close", "tighten", "time_stop", "leave_orig", "abstain"),
    "sibling_pick": ("this_member", "other_member", "abstain"),
    "followthrough_component": COMPONENT_ORDER,
}
LEAVE_ORIG_CHOICES = ("takeoff_label", "chair_manage_noun")
ACT_CHOICES = ("takeoff_label", "rescue_action", "chair_manage_noun", "sibling_pick")
NOUL_IDS = (
    "followthrough_state_sufficient",
    "state_sufficient",
    "isolated_reentry_is_new",
    "isolated_after_window",
    "retry_tape_fresh",
    "lesson_speak",
    "followthrough_auto_be",
    "followthrough_component_exists",
)
_PROPOSED_KEYS = (
    "integer_min_lot",
    "integer_retry_count",
    "integer_retry_cap",
    "integer_window_elapsed",
    "auto_be_enabled",
)
INTEGER_FACTS = (
    "h4_daily_unit_cap",
    "usdjpy_standing_hold",
    "two_stop_count",
    "occupancy_keep_one",
    "auto_be_off",
    "fx_dsp_8pip",
    "min_stop_ticks",
    "retry_cap",
    "weekend_flat",
    "operator_flatten_flag",
    "token_digest_match",
    "calprime_dark",
    "sel_v4_research",
    "halt",
    "named_surface",
    "prop_wall",
    "never_widen",
)
CONVERTED_IF_IDS = (
    "F5-MS-OPENSTAY",
    "F5-MS-TAKEOFF",
    "F5-MS-RESCUE",
    "F5-MS-STALEPEND",
    "F5-MS-COOLDOWN",
    "F5-MS-MANAGECLOSE",
    "F5-MS-MINLOT",
    "F5-MS-AUTOBE",
    "UB-MGT-LEAVEORIG",
    "F5-MS-RETRY",
    "UB-PLC-SIBLING",
    "F5-MS-PAIDCLUSTER",
)

# History only when jev_questions cannot be imported. Not copied into a miss.
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

def overlay_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Env gate. Default on. Explicit 0/false/off leaves the overlay off."""

    env = environ if environ is not None else os.environ
    raw = str(env.get(FOLLOWTHROUGH_ENV, "")).strip().lower()
    if raw in _TRUTHY_OFF:
        return False
    if raw in _TRUTHY_ON or raw == "":
        return True
    return True


def _is_challenge_account(*, login: Any = None, ns: Any = None) -> bool:
    ns_ok = str(ns or "").strip() == CHALLENGE_NS
    login_ok = False
    if login is not None and str(login).strip() != "":
        try:
            login_ok = int(login) == CHALLENGE_LOGIN
        except (TypeError, ValueError):
            login_ok = False
    if login is None and ns is None:
        return False
    if login is not None and ns is not None and str(login).strip() != "" and str(ns).strip() != "":
        return login_ok and ns_ok
    return login_ok or ns_ok


def _blocked_text(text: str) -> bool:
    low = text.lower()
    return any(part in low for part in _SKIP_KEY_PARTS)


# The walk bound is the score for this card. It expires when the card changes.
_WALK_KEY: str | None = None
_WALK_SCORE: float | None = None


def _card_key(value: Any) -> str:
    try:
        blob = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    except (TypeError, ValueError):
        blob = repr(value)
    return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()


def _walk_bound(key: str) -> float | None:
    if _WALK_KEY != key:
        return None
    return _WALK_SCORE


def _remember_walk(key: str, score: float | None) -> None:
    """Keep this card's score. An empty score does not write a number."""

    global _WALK_KEY, _WALK_SCORE
    if _WALK_KEY != key:
        _WALK_KEY = key
        _WALK_SCORE = None
    if score is not None:
        _WALK_SCORE = score


def _scrub(value: Any, depth: int = 0, bound: float | None = None, seen: set[int] | None = None) -> Any:
    """Drop floor and baseline keys before the ask. Other facts stay facts.

    The walk stops past the returned bound. No bound leaves the rest of the card.
    """

    if seen is None:
        seen = set()
    if bound is not None and depth > bound:
        return None
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    mark = id(value)
    if mark in seen:
        return None
    if isinstance(value, Mapping):
        seen.add(mark)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _blocked_text(name):
                continue
            out[name] = _scrub(item, depth + 1, bound, seen)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        seen.add(mark)
        return [_scrub(item, depth + 1, bound, seen) for item in value]
    return None


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
    """Unique highest probability. A tie, an empty map, or a bare label is unset."""

    if not probabilities or not order:
        return None
    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if probabilities[name] == best]
    if len(winners) != 1:
        return None
    present = {name: probabilities[name] for name in allowed}
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(present, allowed)
    except Exception:
        agreed = winners[0]
    if agreed is None or str(agreed) != winners[0]:
        return None
    return winners[0]


def _score_of(block: Any, qid: str | None = None) -> float | None:
    """The returned score. A tie leaves it unset. The number is not snapped."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))


    if not isinstance(block, dict) or block.get("error"):
        return None
    numeric = _probabilities(block)
    if numeric and _unique(numeric, tuple(numeric)) is None:
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


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. Missing stays missing."""

    if isinstance(block, bool):
        return block
    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        raw = block.get("noul") if "noul" in block else block.get("Noul")
        if raw is True or raw is False:
            return raw
        number = _number(raw)
        if number is not None:
            return number
    picked = _unique(_probabilities(block), ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _bool_flag(noul: bool | float | None) -> bool | None:
    """A bool noul is that bool. A probability is not cut into one."""

    if noul is True:
        return True
    if noul is False:
        return False
    return None


def _choice_flag(choice: str | None, name: str) -> bool | None:
    if choice is None:
        return None
    return choice == name


def completeness_noul(answers: Mapping[str, Any] | None) -> bool | float | None:
    """The completeness Noul on this object. A missing noul stays missing."""

    if not isinstance(answers, Mapping):
        return None
    if "followthrough_state_sufficient" in answers:
        return _noul_of(answers.get("followthrough_state_sufficient"))
    if "state_sufficient" in answers:
        return _noul_of(answers.get("state_sufficient"))
    return None


def _question_blocked(qid: Any, spec: Any) -> bool:
    if _blocked_text(str(qid)):
        return True
    if not isinstance(spec, Mapping):
        return True
    if _blocked_text(str(spec.get("instructions") or "")):
        return True
    criteria = spec.get("criteria")
    if isinstance(criteria, Mapping):
        for key, text in criteria.items():
            if _blocked_text(str(key)) or _blocked_text(str(text)):
                return True
    elif isinstance(criteria, (list, tuple)):
        for item in criteria:
            if _blocked_text(str(item)):
                return True
    return False


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
    return {qid: body}


def _score_question(qid: str, instructions: str, criteria: list[str] | None = None) -> dict[str, Any]:
    """Amount anchors from this card. An ordinal keeps its words."""
    return _shape_score(qid, instructions, criteria, wrapped=True)



def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {"true": yes, "false": no},
        }
    }


def _between() -> list[str]:
    return [
        "below the levels on this state",
        "between the levels on this state",
        "above the levels on this state",
    ]


def _seat_questions(seat: str) -> dict[str, Any]:
    """The seat's Noul, Choice, and Score questions. No floor question."""

    if seat == "leftover":
        pack: dict[str, Any] = {}
        pack.update(_score_question(
            "leftover_stay",
            "Does this leftover-open ticket still have hold-to-orig edge? "
            "The score you return is that edge. It may sit between the levels. "
            "An empty score leaves it unset. Do not flatten. Do not send.",
            _between(),
        ))
        pack.update(_score_question(
            "takeoff_spent",
            "Has the fast-family displacement spent? "
            "The score you return is that spent-ness. It may sit between the levels. "
            "An empty score leaves it unset. Do not flatten. Do not send.",
            _between(),
        ))
        pack.update(_choice_question(
            "takeoff_label",
            "Name the leftover noun. The option you return is that noun. "
            "An empty answer or a tie leaves it unset. Do not flatten. Do not send.",
            {
                "orig_stop": "The leftover still rides the original stop.",
                "time_stop": "The leftover is a horizon close.",
                "takeoff": "The displacement spent short of the target.",
                "leave_orig": "Hold the original stop and target.",
                "abstain": "No noun on this state.",
            },
        ))
        return pack
    if seat == "rescue":
        pack = {}
        pack.update(_choice_question(
            "rescue_action",
            "Rebind the bound rescue, leave it, or abstain? "
            "The option you return is that act. "
            "An empty answer or a tie leaves it unset. Do not send.",
            {
                "rebind": "The bound rescue is still the same thesis.",
                "leave": "The rescue is spent.",
                "abstain": "No bound rescue on this state.",
            },
        ))
        pack.update(_noul_question(
            "isolated_reentry_is_new",
            "Is this rescued intent a new fire? The noul you return is that answer. "
            "An empty noul leaves it unset. Do not send.",
            "The rescue is a new fire.",
            "The rescue is not a new fire.",
        ))
        return pack
    if seat == "pending":
        pack = {}
        pack.update(_score_question(
            "stale_pending",
            "The score you return is how stale this pending is. "
            "It may sit between the levels. An empty score leaves it unset. "
            "Do not send.",
            _between(),
        ))
        pack.update(_score_question(
            "chase_toxicity",
            "The score you return is the chase on this pending. "
            "It may sit between the levels. An empty score leaves it unset. "
            "Do not send.",
            _between(),
        ))
        return pack
    if seat == "cooldown":
        pack = {}
        pack.update(_noul_question(
            "isolated_after_window",
            "Is this continuation a new fire? The noul you return is that answer. "
            "An empty noul leaves it unset. Do not send.",
            "The continuation is a new fire.",
            "The continuation is not a new fire.",
        ))
        pack.update(_score_question(
            "cooldown_fitness",
            "The score you return is how spent this continuation is. "
            "It may sit between the levels. An empty score leaves it unset. "
            "Do not send.",
            _between(),
        ))
        return pack
    if seat == "chair":
        pack = {}
        pack.update(_choice_question(
            "chair_manage_noun",
            "Name the chair manage act. The option you return is that act. "
            "An empty answer or a tie leaves it unset. Do not flatten. Do not send.",
            {
                "close": "The manage file is a close.",
                "tighten": "The manage file is a stop tighten.",
                "time_stop": "The manage file is a horizon close.",
                "leave_orig": "Hold the original stop and target.",
                "abstain": "No manage file on this state.",
            },
        ))
        pack.update(_score_question(
            "chair_beats_hold",
            "The score you return is how far the named manage act beats holding. "
            "It may sit between the levels. An empty score leaves it unset. "
            "Do not flatten. Do not send.",
            _between(),
        ))
        return pack
    if seat == "size_physics":
        pack = {}
        pack.update(_score_question(
            "minlot_ev",
            "The score you return is the lot's edge on this state. "
            "It may sit between the levels. An empty score leaves it unset. "
            "Do not send.",
            _between(),
        ))
        pack.update(_score_question(
            "autobe_study",
            "The score you return is the auto-be study on this state. "
            "It may sit between the levels. An empty score leaves it unset. "
            "Do not send.",
            _between(),
        ))
        pack.update(_score_question(
            "leaveorig_fit",
            "The score you return is how well the original stop fits. "
            "It may sit between the levels. An empty score leaves it unset. "
            "Do not send.",
            _between(),
        ))
        pack.update(_noul_question(
            "retry_tape_fresh",
            "Is this retry still a fresh tape? The noul you return is that answer. "
            "An empty noul leaves it unset. Do not send.",
            "The tape is still fresh.",
            "The tape is not fresh.",
        ))
        return pack
    if seat == "sibling":
        pack = {}
        pack.update(_choice_question(
            "sibling_pick",
            "Which member is the fire on this bar? The option you return is that member. "
            "An empty answer or a tie leaves it unset. Do not send.",
            {
                "this_member": "This member is the fire.",
                "other_member": "Another member is the fire.",
                "abstain": "No member is named.",
            },
        ))
        pack.update(_score_question(
            "sibling_conviction",
            "The score you return is this member's conviction versus the others. "
            "It may sit between the levels. An empty score leaves it unset. "
            "Do not send.",
            _between(),
        ))
        return pack
    if seat == "lesson":
        pack = {}
        pack.update(_score_question(
            "paid_cluster_lesson",
            "The score you return is the lesson on this cluster. "
            "It may sit between the levels. An empty score leaves it unset. "
            "Do not send.",
            _between(),
        ))
        pack.update(_noul_question(
            "lesson_speak",
            "Is this lesson speakable as a draft? The noul you return is that answer. "
            "An empty noul leaves it unset. Do not send.",
            "The lesson is speakable as a draft.",
            "The lesson stays silent.",
        ))
        return pack
    return {}


def _parameter_questions() -> dict[str, Any]:
    """Threshold, loop bound, parameter, and component. Same ask as the seat."""

    pack: dict[str, Any] = {}
    pack.update(_score_question(
        "followthrough_threshold",
        "The score you return is the threshold for this follow-through state. "
        "It may sit between the levels. An empty score leaves the threshold unset. "
        "Do not flatten. Do not send.",
    ))
    pack.update(_score_question(
        "followthrough_loop",
        "The score you return is the loop bound for this follow-through state. "
        "It may sit between the levels. An empty score leaves the bound unset. "
        "Do not flatten. Do not send.",
    ))
    pack.update(_score_question(
        "followthrough_parameter",
        "The score you return is the parameter for this follow-through state. "
        "It may sit between the levels. An empty score leaves the parameter unset. "
        "Do not flatten. Do not send.",
    ))
    pack.update(_score_question(
        "followthrough_min_lot",
        "The score you return is the lot for this state. "
        "It may sit between the levels. An empty score leaves the lot unset. "
        "Do not send.",
    ))
    pack.update(_score_question(
        "followthrough_retry_bound",
        "The score you return is the retry bound for this state. "
        "It may sit between the levels. An empty score leaves the bound unset. "
        "Do not send.",
    ))
    pack.update(_score_question(
        "followthrough_retry_count",
        "The score you return is the retry count for this state. "
        "It may sit between the levels. An empty score leaves the count unset. "
        "Do not send.",
    ))
    pack.update(_score_question(
        "followthrough_window",
        "The score you return is the window for this state. "
        "It may sit between the levels. An empty score leaves the window unset. "
        "Do not send.",
    ))
    pack.update(_score_question(
        "followthrough_persist",
        "The score you return is the persistence weight for this state. "
        "It may sit between the levels. An empty score leaves the weight unset. "
        "Do not send.",
    ))
    pack.update(_noul_question(
        "followthrough_auto_be",
        "Is auto-be the act on this state? The noul you return is that act. "
        "An empty noul leaves it unset. Do not send.",
        "Auto-be is the act on this state.",
        "Auto-be is not the act on this state.",
    ))
    pack.update(_choice_question(
        "followthrough_component",
        "Which follow-through component exists on this state? "
        "The option you return is that component. "
        "An empty answer or a tie leaves the component unset. "
        "Do not flatten. Do not send.",
        {name: f"The {name} component exists on this state." for name in COMPONENT_ORDER},
    ))
    pack.update(_noul_question(
        "followthrough_component_exists",
        "Does that follow-through component exist on this state? "
        "The noul you return is that existence. An empty noul leaves it unset. "
        "Do not send.",
        "The component exists on this state.",
        "The component does not exist on this state.",
    ))
    pack.update(_score_question(
        "followthrough_walk_depth",
        "The score you return is how deep this follow-through card is walked. "
        "An empty score leaves the depth unset. Do not flatten. Do not send.",
    ))
    return pack


def _seats_for_branch(branch: str, seats: Iterable[str] | None) -> tuple[str, ...]:
    if seats:
        named = tuple(seat for seat in seats if seat in SEATS)
        if named:
            return named
    mapped = BRANCH_SEATS.get(str(branch or "").strip().lower())
    if mapped:
        return mapped
    return SEATS


def _local_piece(seats: Iterable[str]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    pack.update(_noul_question(
        "followthrough_state_sufficient",
        "Are the named follow-through chunks enough to judge this state? "
        "The noul you return is that completeness. An empty noul leaves it unset. "
        "Do not flatten. Do not send.",
        "The named chunks are enough.",
        "A named chunk is missing.",
    ))
    for seat in seats:
        for chunk in SEAT_CHUNKS.get(seat, ()):
            pack.update(_score_question(
                f"include_{chunk}",
                f"The score you return is how much of `{chunk}` this state needs. "
                "It may sit between the levels. An empty score leaves it unset.",
                _between(),
            ))
        pack.update(_seat_questions(seat))
    return pack


def piece_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "leftover",
) -> dict[str, Any]:
    """One pack for this piece. Seat questions plus the parameter questions."""

    _bind_card(state)
    named = _seats_for_branch(branch, seats)
    raw: Mapping[str, Any] | None = None
    try:
        from .followthrough_ifs import seat_subtree_questions

        loaded = seat_subtree_questions(state, seats=named, branch=branch, standalone=True)
        if isinstance(loaded, Mapping) and loaded:
            raw = loaded
    except Exception:
        raw = None
    if raw is None:
        raw = _local_piece(named)
    pack: dict[str, Any] = {}
    for qid, spec in raw.items():
        if not isinstance(spec, Mapping):
            continue
        if str(spec.get("type") or "") not in _QUESTION_TYPES:
            continue
        if _question_blocked(qid, spec):
            continue
        pack[str(qid)] = dict(spec)
    for qid, spec in _parameter_questions().items():
        if _question_blocked(qid, spec):
            continue
        pack[qid] = spec
    return pack


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
    state["prior_outcomes"] = loaded if isinstance(loaded, list) else []


def _remember(state: Mapping[str, Any], pairs: list[tuple[str, Any]], error: str | None) -> None:
    """The return just asked is history for the next ask. A miss stays a miss."""

    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value in pairs:
            _LOCAL_OUTCOMES.append({
                "key": key,
                "value": value,
                "error": None if value is not None else error,
            })
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value in pairs:
        try:
            append_outcome(key, value, logged, error=None if value is not None else error)
        except Exception:
            return


def _not_challenge(state: Mapping[str, Any]) -> bool:
    identity = dict(state.get("identity") or {})
    login = identity.get("login")
    ns = identity.get("ns")
    if login is None and ns is None:
        return False
    return not _is_challenge_account(login=login, ns=ns)


def _with_proposed(state: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    """Caller numbers stay facts on the ask. They are not the returned parameter."""

    proposed: dict[str, Any] = {}
    for key in _PROPOSED_KEYS:
        if key not in values or values.get(key) is None:
            continue
        if _blocked_text(key):
            continue
        proposed[key] = values.get(key)
    out = dict(state)
    if proposed:
        out["proposed"] = proposed
    return out


def _labels(state: Mapping[str, Any], seat: str, branch: str) -> dict[str, Any]:
    try:
        from .followthrough_ifs import hierarchical_labels

        loaded = hierarchical_labels(state, seat=seat, branch=branch)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass
    identity = dict(state.get("identity") or {})
    clock = dict(state.get("clock") or {})
    return {
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "family_node": seat,
        "sleeve": identity.get("sleeve"),
        "symbol": identity.get("symbol"),
        "side": identity.get("side"),
        "ticket": identity.get("ticket"),
        "branch": branch,
        "as_of_utc": clock.get("as_of_utc"),
    }


def _base(
    state: Mapping[str, Any],
    *,
    seat: str,
    branch: str,
    enabled: bool,
    questions: Mapping[str, Any],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    labels = _labels(state, seat, branch)
    row = {
        "schema": SCHEMA,
        "model": MODEL,
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "overlay": FOLLOWTHROUGH_ENV,
        "overlay_enabled": enabled,
        "labels": labels,
        "family_node": labels.get("family_node"),
        "seat": seat,
        "branch": branch,
        "integer_facts": list(INTEGER_FACTS),
        "converted_if_ids": list(CONVERTED_IF_IDS),
        "question_ids": list(questions),
        "one_piece": True,
        "does_not_flatten": True,
        "does_not_send": True,
        "copied_persist_010": False,
        "inventory_fluid": len(questions),
        "inventory_envelope": len(SEATS),
        **dict(extra or {}),
    }
    return row


@dataclass(frozen=True)
class FollowthroughDecision:
    """The follow-through return. A miss stays unset. This piece does not send."""

    disposition: str | None = None
    reason: str | None = None
    extra_pass: bool = False
    leave_orig: bool | None = None
    extra_flatten: bool | None = None
    extra_rebind: bool | None = None
    extra_cancel: bool | None = None
    extra_yield: bool | None = None
    extra_place: bool | None = None
    extra_enroll: bool | None = None
    extra_widen: bool | None = None
    extra_be: bool | None = None
    extra_retry: bool | None = None
    extra_remint_sl: bool | None = None
    integer_stands: bool | None = None
    include_depth: dict[str, str] = field(default_factory=dict)
    missing_jev: bool = False
    jev_no_decision: bool = False
    payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.payload,
            "disposition": self.disposition,
            "reason": self.reason,
            "extra_pass": False,
            "leave_orig": self.leave_orig,
            "extra_flatten": None,
            "extra_rebind": self.extra_rebind,
            "extra_cancel": self.extra_cancel,
            "extra_yield": self.extra_yield,
            "extra_place": self.extra_place,
            "extra_enroll": self.extra_enroll,
            "extra_widen": self.extra_widen,
            "extra_be": self.extra_be,
            "extra_retry": self.extra_retry,
            "extra_remint_sl": self.extra_remint_sl,
            "integer_stands": self.integer_stands,
            "include_depth": dict(self.include_depth),
            "missing_jev": self.missing_jev,
            "jev_no_decision": self.jev_no_decision,
        }


def _named_seats(branch: str, seats: Iterable[str] | None, seat: str) -> tuple[str, ...]:
    """The branch picks the piece. An explicit seat list overrides that branch."""

    if seats:
        return _seats_for_branch(branch, seats)
    if seat != "leftover" or branch == "leftover":
        return _seats_for_branch(branch, (seat,))
    return _seats_for_branch(branch, None)


def _choice_of(answers: Mapping[str, Any], qid: str) -> str | None:
    block = answers.get(qid)
    order = CHOICE_ORDER.get(qid)
    if order is None:
        return None
    return _unique(_probabilities(block), order)


def _read_returns(answers: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = answers if isinstance(answers, Mapping) else {}
    choices: dict[str, str] = {}
    scores: dict[str, float] = {}
    nouls: dict[str, bool | float] = {}
    returns: dict[str, Any] = {}
    for qid, block in payload.items():
        name = str(qid)
        if name in CHOICE_ORDER:
            choice = _choice_of(payload, name)
            if choice is None:
                continue
            choices[name] = choice
            returns[name] = {"choice": choice}
            continue
        if not isinstance(block, Mapping):
            if name in NOUL_IDS and isinstance(block, bool):
                nouls[name] = block
                returns[name] = {"noul": block}
                continue
            number = _number(block)
            if number is None:
                continue
            scores[name] = number
            returns[name] = {"score": number}
            continue
        if name in NOUL_IDS or ("noul" in block and "score" not in block):
            noul = _noul_of(block)
            if noul is None:
                continue
            nouls[name] = noul
            returns[name] = {"noul": noul}
            continue
        score = _score_of(block, name)
        if score is None:
            continue
        scores[name] = score
        returns[name] = {"score": score}
    return {"choices": choices, "scores": scores, "nouls": nouls, "returns": returns}


def _leave_orig(choices: Mapping[str, str]) -> bool | None:
    relevant = [choices[key] for key in LEAVE_ORIG_CHOICES if key in choices]
    if not relevant:
        return None
    if any(item == "leave_orig" for item in relevant) and any(item != "leave_orig" for item in relevant):
        return None
    return all(item == "leave_orig" for item in relevant)


def _disposition(choices: Mapping[str, str]) -> str | None:
    picked = [choices[key] for key in ACT_CHOICES if key in choices]
    if len(picked) == 1:
        return picked[0]
    if len(picked) > 1 and len(set(picked)) == 1:
        return picked[0]
    return None


def _include_depth(scores: Mapping[str, float]) -> dict[str, str]:
    """Returned include scores. A missing score is omitted. The number is not snapped."""

    out: dict[str, str] = {}
    for qid, score in scores.items():
        if not str(qid).startswith("include_"):
            continue
        out[str(qid)[len("include_") :]] = format(score, ".10g")
    return out


def _return_pairs(parsed: Mapping[str, Any], questions: Mapping[str, Any]) -> list[tuple[str, Any]]:
    returns = parsed.get("returns") if isinstance(parsed.get("returns"), Mapping) else {}
    pairs: list[tuple[str, Any]] = []
    for qid in questions:
        item = returns.get(qid)
        if not isinstance(item, Mapping):
            pairs.append((str(qid), None))
            continue
        if "choice" in item:
            pairs.append((str(qid), item.get("choice")))
        elif "score" in item:
            pairs.append((str(qid), item.get("score")))
        elif "noul" in item:
            pairs.append((str(qid), item.get("noul")))
        else:
            pairs.append((str(qid), None))
    return pairs


def evaluate_pack(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    *,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. Path and err stay here. Never raises."""

    del timeout_s
    pack = {
        str(qid): dict(spec)
        for qid, spec in dict(questions or {}).items()
        if isinstance(spec, Mapping)
        and str(spec.get("type") or "") in _QUESTION_TYPES
        and not _question_blocked(qid, spec)
    }
    raw = dict(state or {})
    card_key = _card_key(raw)
    asked = _scrub(raw, bound=_walk_bound(card_key))
    if not isinstance(asked, dict):
        asked = {}
    asked.pop("prior_outcomes", None)
    asked["model"] = MODEL
    _attach_priors(asked, pack)
    if not pack:
        _remember(asked, [], "empty")
        return {
            "ok": False,
            "skipped": "empty",
            "error": "empty",
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
        }
    try:
        from .jev_client import evaluate

        receipt = evaluate(
            asked,
            questions=pack,
            model=MODEL,
            merge_sleeve=False,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset and must not raise
        _remember(asked, [(qid, None) for qid in pack], type(exc).__name__)
        return {
            "ok": False,
            "skipped": type(exc).__name__,
            "error": type(exc).__name__,
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
        }
    out = dict(receipt) if isinstance(receipt, Mapping) else {"ok": False, "answers": {}}
    out.setdefault("kind", KIND_READ)
    out["model"] = out.get("model") or MODEL
    answers = out.get("answers")
    if not isinstance(answers, dict):
        answers = {}
        out["answers"] = answers
    error = None
    if out.get("ok") is not True or not answers:
        error = str(out.get("error") or out.get("skipped") or "empty")
        out.setdefault("skipped", error)
        out.setdefault("error", error)
        out["answers"] = answers
    parsed = _read_returns(answers)
    _remember_walk(card_key, parsed["scores"].get("followthrough_walk_depth"))
    _remember(asked, _return_pairs(parsed, pack), error)
    return out


def _gate(*, reason: str, base: dict[str, Any]) -> FollowthroughDecision:
    return FollowthroughDecision(
        disposition=None,
        reason=reason,
        missing_jev=False,
        jev_no_decision=True,
        payload={**base, "skipped": reason},
    )


def compose_followthrough(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    *,
    seat: str = "leftover",
    branch: str = "leftover",
    seats: Iterable[str] | None = None,
    integer_window_elapsed: bool | None = None,
    integer_min_lot: float | None = None,
    integer_retry_count: int | None = None,
    integer_retry_cap: int | None = None,
    auto_be_enabled: bool | None = None,
    environ: Mapping[str, str] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> FollowthroughDecision:
    """Read this state's return. A miss does not restore a constant."""

    _bind_card(state)
    del integer_window_elapsed, integer_min_lot, integer_retry_count, integer_retry_cap, auto_be_enabled
    state_map = dict(state or {})
    enabled = overlay_enabled(environ=environ)
    named_seats = _named_seats(branch, seats, seat)
    seat_n = seat if seat in SEATS else named_seats[0]
    questions = piece_questions(state_map, seats=named_seats, branch=branch)
    base = _base(
        state_map,
        seat=seat_n,
        branch=branch,
        enabled=enabled,
        questions=questions,
        extra=extra,
    )
    if _not_challenge(state_map):
        return _gate(reason="not_challenge_integer_path", base=base)
    if not enabled:
        return _gate(reason=f"{FOLLOWTHROUGH_ENV}_off", base=base)

    missing = not isinstance(answers, Mapping) or len(answers) == 0
    parsed = _read_returns(None if missing else answers)
    choices = parsed["choices"]
    scores = parsed["scores"]
    nouls = parsed["nouls"]
    any_return = bool(parsed["returns"])
    payload = {
        **base,
        "state_sufficient": completeness_noul(None if missing else answers),
        "threshold": scores.get("followthrough_threshold"),
        "loop_bound": scores.get("followthrough_loop"),
        "parameter": scores.get("followthrough_parameter"),
        "min_lot": scores.get("followthrough_min_lot"),
        "retry_bound": scores.get("followthrough_retry_bound"),
        "retry_count": scores.get("followthrough_retry_count"),
        "window": scores.get("followthrough_window"),
        "persist_weight": scores.get("followthrough_persist"),
        "auto_be": nouls.get("followthrough_auto_be"),
        "component": choices.get("followthrough_component"),
        "component_exists": nouls.get("followthrough_component_exists"),
        "takeoff_label": choices.get("takeoff_label"),
        "rescue_action": choices.get("rescue_action"),
        "chair_manage_noun": choices.get("chair_manage_noun"),
        "sibling_pick": choices.get("sibling_pick"),
        "isolated_reentry_is_new": nouls.get("isolated_reentry_is_new"),
        "isolated_after_window": nouls.get("isolated_after_window"),
        "retry_tape_fresh": nouls.get("retry_tape_fresh"),
        "lesson_speak": nouls.get("lesson_speak"),
        "leftover_stay": scores.get("leftover_stay"),
        "takeoff_spent": scores.get("takeoff_spent"),
        "stale_pending": scores.get("stale_pending"),
        "chase_toxicity": scores.get("chase_toxicity"),
        "cooldown_fitness": scores.get("cooldown_fitness"),
        "chair_beats_hold": scores.get("chair_beats_hold"),
        "minlot_ev": scores.get("minlot_ev"),
        "autobe_study": scores.get("autobe_study"),
        "leaveorig_fit": scores.get("leaveorig_fit"),
        "sibling_conviction": scores.get("sibling_conviction"),
        "paid_cluster_lesson": scores.get("paid_cluster_lesson"),
        "walk_depth": scores.get("followthrough_walk_depth"),
        "returns": parsed["returns"],
    }
    return FollowthroughDecision(
        disposition=_disposition(choices),
        reason=None if any_return else ("empty" if missing else "no_decision"),
        leave_orig=_leave_orig(choices),
        extra_rebind=_choice_flag(choices.get("rescue_action"), "rebind"),
        extra_yield=_bool_flag(nouls.get("isolated_after_window")),
        extra_place=_choice_flag(choices.get("sibling_pick"), "this_member"),
        extra_be=_bool_flag(nouls.get("followthrough_auto_be")),
        extra_retry=_bool_flag(nouls.get("retry_tape_fresh")),
        include_depth=_include_depth(scores),
        missing_jev=missing,
        jev_no_decision=not any_return,
        payload=payload,
    )


def compose_leftover(state=None, answers=None, **kwargs: Any) -> FollowthroughDecision:
    return compose_followthrough(state, answers, seat="leftover", branch="leftover", **kwargs)


def compose_rescue(state=None, answers=None, **kwargs: Any) -> FollowthroughDecision:
    return compose_followthrough(state, answers, seat="rescue", branch="rescue", **kwargs)


def compose_pending(state=None, answers=None, **kwargs: Any) -> FollowthroughDecision:
    return compose_followthrough(state, answers, seat="pending", branch="pending", **kwargs)


def compose_cooldown(state=None, answers=None, **kwargs: Any) -> FollowthroughDecision:
    return compose_followthrough(state, answers, seat="cooldown", branch="cooldown", **kwargs)


def compose_chair(state=None, answers=None, **kwargs: Any) -> FollowthroughDecision:
    return compose_followthrough(state, answers, seat="chair", branch="chair", **kwargs)


def compose_size(state=None, answers=None, **kwargs: Any) -> FollowthroughDecision:
    return compose_followthrough(state, answers, seat="size_physics", branch="size", **kwargs)


def compose_sibling(state=None, answers=None, **kwargs: Any) -> FollowthroughDecision:
    return compose_followthrough(state, answers, seat="sibling", branch="sibling", **kwargs)


def compose_lesson(state=None, answers=None, **kwargs: Any) -> FollowthroughDecision:
    return compose_followthrough(state, answers, seat="lesson", branch="lesson", **kwargs)


def compose_from_intent(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    *,
    branch: str = "leftover",
    seats: Iterable[str] | None = None,
    evaluate_jev: bool = False,
    timeout_s: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """One intent, one evaluate, one piece. The return is the decision."""

    _bind_card(state)
    st = _scrub(dict(state or {}))
    if not isinstance(st, dict):
        st = {}
    st = _with_proposed(st, kwargs)
    questions = piece_questions(st, seats=seats, branch=branch)
    receipt: dict[str, Any] = {
        "ok": False,
        "skipped": "evaluate_jev_false",
        "answers": {},
        "kind": KIND_READ,
        "model": MODEL,
    }
    composed = answers
    if evaluate_jev and answers is None:
        receipt = evaluate_pack(st, questions, timeout_s=timeout_s)
        got = receipt.get("answers")
        composed = got if receipt.get("ok") is True and isinstance(got, Mapping) and got else None
    decision = compose_followthrough(
        st,
        composed,
        branch=branch,
        seats=seats,
        **kwargs,
    )
    return {
        "questions": list(questions),
        "receipt": receipt,
        "decision": decision.as_dict(),
        "model": MODEL,
        "one_piece": True,
        "does_not_flatten": True,
        "does_not_send": True,
        "evaluate_jev": bool(evaluate_jev),
    }
