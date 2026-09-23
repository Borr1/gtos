"""A candidate and a ticket pass the whole life.

Watch, observe, admit, place, and every manage step each ask System One.
The choice, the threshold, the loop bound, the parameter, and which
component exists are that return. Model ``jev-1.13.0``. The post is
``jev_client.evaluate`` (POST https://api.typesafe.ai/v1/systemone),
the same call the other judgment seats use. A return is only a Noul, a
Choice, or a Score. A Score may sit between the levels.

Prior outcomes are attached on every ask. An empty answer, a tie, a
missing score, or an error leaves that return unset. This module does
not send an order and does not change ``skip_reason``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Mapping

GATE_ID = "UB-OBS-EVERY"
SCHEMA = "gtos.judgment.a1_observe_every.v0"
MODEL = "jev-1.13.0"

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_LIFE = ("watch", "observe", "admit", "place")
_MANAGE_STEPS = ("move_sl", "move_tp", "close", "hold", "remove")
_PASS = _LIFE + _MANAGE_STEPS
_COMPONENT_ORDER = ("gold_state", "symbol_state", "aplus", "fluid", "gate")
_COMPONENT_CRITERIA = {
    "gold_state": "The gold state component exists for this candidate and this ticket.",
    "symbol_state": "The symbol state component exists for this candidate and this ticket.",
    "aplus": "The aplus component exists for this candidate and this ticket.",
    "fluid": "A fluid component exists for this candidate and this ticket.",
    "gate": "The named gate component exists for this candidate and this ticket.",
}
_WATCH_CRITERIA = {
    "watch": "This candidate and this ticket stay on watch.",
    "release": "This watch step releases this candidate and this ticket.",
}
_OBSERVE_CRITERIA = {
    "observe": "Observe this candidate and this ticket.",
    "leave": "This observe step adds nothing.",
}
_ADMIT_CRITERIA = {
    "admit": "Admit this candidate.",
    "abstain": "Do not admit this candidate on this bar.",
    "hard_refuse": "Hard refuse this candidate.",
}
_PLACE_CRITERIA = {
    "PLACE": "This candidate is the order on this bar.",
    "STAND": "This candidate is not the order on this bar.",
    "DELAY": "This bar is not the bar for this candidate.",
    "REMINT": "A re-entry of an existing ticket fits this candidate.",
    "FLATTEN_CANDIDATE": "This candidate is a reduction of open risk.",
}
_MANAGE_CRITERIA = {
    "leave_orig": "Leave the original stop and target on this step.",
    "move_sl": "Move the stop. The stop is the parameter score on this step.",
    "move_tp": "Move the target. The target is the parameter score on this step.",
    "close": "Close this ticket on this step.",
    "hold": "Hold. Do not move and do not close on this step.",
    "remove": "Cancel this pending on this step.",
}
_STEP_CRITERIA = {
    "watch": _WATCH_CRITERIA,
    "observe": _OBSERVE_CRITERIA,
    "admit": _ADMIT_CRITERIA,
    "place": _PLACE_CRITERIA,
    "move_sl": _MANAGE_CRITERIA,
    "move_tp": _MANAGE_CRITERIA,
    "close": _MANAGE_CRITERIA,
    "hold": _MANAGE_CRITERIA,
    "remove": _MANAGE_CRITERIA,
}
_LEVELS = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LEVEL_KEYS = {
    "entry",
    "stop",
    "target",
    "stop_dist",
    "spread",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
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


def a1_log_enabled() -> bool:
    return _env_on("GTOS_JEV_A1_LOG") or _env_on("GTOS_JEV_ALIVE_SHADOW")


def _never_place_stamp() -> bool:
    try:
        from src.judgment.place_gate import never_place_effective

        return bool(never_place_effective())
    except Exception:
        return not (_env_on("GTOS_JEV_PLACE_APPLY") or _env_on("GTOS_JEV_OWNER_UNLOCK"))


def observe_every_enabled() -> bool:
    return a1_log_enabled() and _env_on("GTOS_JEV_A1_OBSERVE_EVERY")


def dedupe_enabled() -> bool:
    raw = os.environ.get("GTOS_JEV_A1_DEDUPE", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _cache_key(intent: Any, extra: dict[str, Any] | None) -> tuple[str, str, str]:
    extra = extra or {}
    symbol = str(getattr(intent, "symbol", None) or extra.get("symbol") or "")
    sleeve = str(getattr(intent, "sleeve", None) or extra.get("sleeve") or "")
    dbar = str(
        getattr(intent, "decision_bar_iso", None)
        or extra.get("decision_bar_iso")
        or ""
    )
    return (symbol, sleeve, dbar)


def _limit_key(name: str) -> bool:
    low = name.lower()
    return "floor" in low or "baseline" in low or low in {"pass_line", "daily_loss_pct"}


def _strip_limits(value: Any) -> Any:
    if isinstance(value, dict):
        kept: dict[str, Any] = {}
        for key, item in value.items():
            if _limit_key(str(key)):
                continue
            kept[str(key)] = _strip_limits(item)
        return kept
    if isinstance(value, list):
        return [_strip_limits(item) for item in value]
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


def _local_unique(probabilities: Mapping[str, Any], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    allowed = set(order)
    for name in order:
        if name not in probabilities:
            continue
        number = _finite(probabilities.get(name))
        if number is None:
            continue
        if name not in allowed:
            continue
        seen = True
        if best_p is None or number > best_p:
            best = name
            best_p = number
            tied = False
        elif number == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _unique(probabilities: Mapping[str, Any] | None, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie or a bare label is not a decision."""

    numeric: dict[str, float] = {}
    if isinstance(probabilities, Mapping):
        for key, val in probabilities.items():
            number = _finite(val)
            if number is None:
                continue
            numeric[str(key)] = number
    if not numeric:
        return None
    local = _local_unique(numeric, order)
    helper = None
    try:
        from src.judgment.jev_questions import unique_highest

        helper = unique_highest
    except Exception:
        helper = None
    if helper is None:
        return local
    try:
        try:
            picked = helper(numeric, order)
        except TypeError:
            picked = helper(numeric)
    except Exception:
        return local
    if picked is None:
        return None
    name = str(picked)
    if name not in order or name != local:
        return None
    return name


def _choice_of(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, dict):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping) or not probs:
        return None
    return _unique(probs, order)


def _score_of(block: Any, qid: str | None = None) -> float | None:
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))

    if not isinstance(block, dict):
        return None
    number = None
    try:
        from src.judgment.jev_questions import returned_number

        got = returned_number(block)
        number = _finite(got)
    except Exception:
        number = None
    if number is not None:
        return number
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _finite(raw)


def _noul_of(block: Any) -> bool | float | None:
    if not isinstance(block, dict) or "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _exists(noul: bool | float | None, threshold: float | None) -> bool | None:
    if noul is True or noul is False:
        return noul
    if noul is None or threshold is None:
        return None
    return float(noul) >= float(threshold)


def _leaks_limit(pack: Mapping[str, Any]) -> bool:
    """Question text does not carry an account floor or baseline."""

    banned = ("floor", "baseline", "90000", "110000", "90k", "110k")
    for spec in pack.values():
        if not isinstance(spec, dict):
            continue
        text = str(spec.get("instructions") or "").lower()
        if any(token in text for token in banned):
            return True
        criteria = spec.get("criteria")
        if isinstance(criteria, dict):
            labels = json.dumps(criteria).lower()
            if "floor" in labels or "baseline" in labels:
                return True
    return False


def _force_choice(qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    block: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": dict(criteria),
    }
    try:
        from src.judgment.jev_questions import spot_question

        built = spot_question(qid, instructions, dict(criteria))
        if isinstance(built, dict) and isinstance(built.get(qid), dict):
            block = dict(built[qid])
    except Exception:
        pass
    block["type"] = "choice"
    block["instructions"] = instructions
    block["criteria"] = dict(criteria)
    return {qid: block}


def _force_score(qid: str, instructions: str, levels: list[str]) -> dict[str, Any]:
    """Amount anchors from this card. An ordinal keeps its words."""
    return _shape_score(qid, instructions, levels, wrapped=True)



def _price_levels(state: Mapping[str, Any] | None) -> list[str]:
    """Prices already on the state. A score may sit between them."""

    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        low = key.lower()
        if _limit_key(low) or low in {"equity", "balance", "account"}:
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(str(child_key), child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            return
        if low not in _LEVEL_KEYS:
            return
        number = _finite(value)
        if number is not None:
            found.append(number)

    for key, value in dict(state or {}).items():
        walk(str(key), value)
    ordered = sorted(set(found))
    return [format(number, ".10g") for number in ordered]


def _questions(stage: str, levels: list[str] | None = None) -> dict[str, Any]:
    """Choice, Noul, and Score for this step. Same names the life card posts."""

    menu = _STEP_CRITERIA[stage]
    score_levels = list(levels) if levels else list(_LEVELS)
    pack: dict[str, Any] = {}
    pack.update(_force_choice(
        "a1_component",
        "Which component exists for this candidate and this ticket? "
        "Both pass this ask. The name you return is the component. "
        "An empty answer or a tie is not a component. "
        "Do not send an order.",
        _COMPONENT_CRITERIA,
    ))
    pack["a1_component_present"] = {
        "type": "noul",
        "instructions": (
            "Does that component exist for this candidate and this ticket? "
            "An empty answer leaves it unset. Do not send an order."
        ),
        "criteria": {
            "true": "Yes, for this candidate and this ticket.",
            "false": "No, for this candidate and this ticket.",
        },
    }
    pack.update(_force_choice(
        f"a1_{stage}",
        f"Life step {stage} for this candidate and this ticket. "
        "Both pass this step. Pick one option. "
        "The option you return is the decision. "
        "An empty answer or a tie is not a decision. "
        "Do not send an order.",
        menu,
    ))
    pack.update(_force_score(
        f"a1_{stage}_threshold",
        f"At {stage}, what threshold applies to this candidate and this ticket? "
        "The score you return is that threshold. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "Do not send an order.",
        score_levels,
    ))
    pack.update(_force_score(
        f"a1_{stage}_parameter",
        f"At {stage}, what parameter applies to this candidate and this ticket? "
        "The score you return is that parameter. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "Do not send an order.",
        score_levels,
    ))
    pack.update(_force_score(
        f"a1_{stage}_loop",
        f"At {stage}, what loop bound applies to this candidate and this ticket? "
        "The score you return is that loop bound. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "Do not send an order.",
        score_levels,
    ))
    clean: dict[str, Any] = {}
    for key, spec in pack.items():
        if isinstance(spec, dict) and spec.get("type") in {"noul", "choice", "score"}:
            clean[str(key)] = spec
    return clean


def _attr(intent: Any, *names: str, extra: Mapping[str, Any] | None = None) -> Any:
    for name in names:
        if intent is not None and hasattr(intent, name):
            value = getattr(intent, name)
            if value is not None:
                return value
        if isinstance(extra, Mapping) and extra.get(name) is not None:
            return extra.get(name)
    return None


def _candidate_facts(intent: Any, extra: Mapping[str, Any] | None) -> dict[str, Any]:
    return _strip_limits({
        "symbol": _attr(intent, "symbol", extra=extra),
        "sleeve": _attr(intent, "sleeve", extra=extra),
        "side": _attr(intent, "side", extra=extra),
        "decision_bar_iso": _attr(intent, "decision_bar_iso", extra=extra),
        "candidate_id": _attr(intent, "candidate_id", extra=extra),
    })


def _ticket_facts(
    intent: Any,
    extra: Mapping[str, Any] | None,
    occupancy: Mapping[str, Any] | None,
) -> dict[str, Any]:
    ticket = _attr(intent, "ticket", extra=extra)
    if ticket is None and isinstance(occupancy, Mapping):
        ticket = occupancy.get("ticket")
    return _strip_limits({
        "ticket": ticket,
        "symbol": _attr(intent, "symbol", extra=extra),
        "position": _attr(intent, "position", extra=extra),
    })


def _remember(state: Mapping[str, Any], pairs: tuple[tuple[str, Any], ...], error: str | None) -> None:
    try:
        from src.judgment.jev_questions import append_outcome
    except Exception:
        return
    for key, value in pairs:
        try:
            append_outcome(key, value, state, error=None if value is not None else error)
        except TypeError:
            try:
                append_outcome(key, value)
            except Exception:
                return
        except Exception:
            return


def _again(step: Mapping[str, Any], asked: int) -> bool:
    bound = step.get("loop_bound")
    if bound is None or asked >= bound:
        return False
    if step.get("exists") is not True:
        return False
    return True


def _ask(
    stage: str,
    base: Mapping[str, Any],
    life_so_far: list[dict[str, Any]],
    index: int,
) -> dict[str, Any]:
    """One System One post for this step. A miss stays unset."""

    _bind_card(base)
    step: dict[str, Any] = {
        "stage": stage,
        "step_index": index,
        "component_choice": None,
        "exists_noul": None,
        "exists": None,
        "choice": None,
        "threshold": None,
        "parameter": None,
        "loop_bound": None,
        "decision_emitted": False,
        "model": MODEL,
        "error": None,
        "broker_effect": False,
    }
    try:
        questions = _questions(stage, _price_levels(base))
    except Exception as exc:
        step["error"] = type(exc).__name__
        return step
    if _leaks_limit(questions) or not questions:
        step["error"] = "question_rejected"
        return step
    state = _strip_limits(dict(base))
    state["model"] = MODEL
    state["stage"] = stage
    state["step_index"] = index
    state["life_so_far"] = list(life_so_far)
    state.pop("prior_outcomes", None)
    try:
        from src.judgment.jev_questions import prior_outcomes

        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        pass
    error: str | None = None
    receipt: dict[str, Any] = {}
    try:
        from src.judgment.jev_client import evaluate

        got = evaluate(state, questions=questions, merge_sleeve=False)
        if isinstance(got, dict):
            receipt = got
        else:
            error = "evaluate_not_a_dict"
    except Exception as exc:
        error = type(exc).__name__
    answers = receipt.get("answers") if isinstance(receipt.get("answers"), dict) else {}
    if not answers and error is None:
        error = str(receipt.get("error") or receipt.get("skipped") or "empty")
    if receipt.get("model"):
        step["model"] = receipt.get("model")
    component_order = _COMPONENT_ORDER
    choice_order = tuple(_STEP_CRITERIA[stage])
    component = _choice_of(answers.get("a1_component"), component_order)
    noul = _noul_of(answers.get("a1_component_present"))
    choice = _choice_of(answers.get(f"a1_{stage}"), choice_order)
    threshold = _score_of(answers.get(f"a1_{stage}_threshold"), f"a1_{stage}_threshold")
    parameter = _score_of(answers.get(f"a1_{stage}_parameter"), f"a1_{stage}_parameter")
    loop_bound = _score_of(answers.get(f"a1_{stage}_loop"), f"a1_{stage}_loop")
    step["component_choice"] = component
    step["exists_noul"] = noul
    step["exists"] = _exists(noul, threshold)
    step["choice"] = choice
    step["threshold"] = threshold
    step["parameter"] = parameter
    step["loop_bound"] = loop_bound
    step["decision_emitted"] = choice is not None
    step["error"] = error
    step["questions"] = list(questions)
    _remember(
        state,
        (
            ("a1_component", component),
            ("a1_component_present", noul),
            (f"a1_{stage}", choice),
            (f"a1_{stage}_threshold", threshold),
            (f"a1_{stage}_parameter", parameter),
            (f"a1_{stage}_loop", loop_bound),
        ),
        error,
    )
    return step


def _pass_stage(stage: str, base: Mapping[str, Any], life_so_far: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    index = 0
    while True:
        step = _ask(stage, base, life_so_far, index)
        steps.append(step)
        life_so_far.append({
            "stage": step.get("stage"),
            "step_index": step.get("step_index"),
            "component_choice": step.get("component_choice"),
            "exists_noul": step.get("exists_noul"),
            "exists": step.get("exists"),
            "choice": step.get("choice"),
            "threshold": step.get("threshold"),
            "parameter": step.get("parameter"),
            "loop_bound": step.get("loop_bound"),
            "error": step.get("error"),
        })
        index += 1
        if not _again(step, index):
            break
    return steps


def _base_state(
    intent: Any,
    *,
    tick: Any,
    skip_reason: str | None,
    writer_stage: str,
    occupancy: dict[str, Any] | None,
    governor: dict[str, Any] | None,
    extra: dict[str, Any] | None,
) -> dict[str, Any]:
    extra_map = dict(extra or {})
    state: dict[str, Any] = {}
    try:
        from src.judgment.a1_log import intent_gold_state

        got = intent_gold_state(
            intent,
            tick,
            origin="w7_ultimate_book",
            occupancy=occupancy,
            governor=governor,
        )
        if isinstance(got, dict):
            state = got
    except Exception:
        state = {}
    try:
        from src.judgment.equity_frame import attach_account

        attached = attach_account(state)
        if isinstance(attached, dict):
            state = attached
    except Exception:
        pass
    state = _strip_limits(state)
    state["model"] = MODEL
    state["candidate"] = _candidate_facts(intent, extra_map)
    state["ticket"] = _ticket_facts(intent, extra_map, occupancy)
    state["writer_stage"] = writer_stage
    state["skip_reason"] = skip_reason
    if isinstance(occupancy, dict):
        state["occupancy"] = _strip_limits(occupancy)
    if isinstance(governor, dict):
        state["governor"] = _strip_limits(governor)
    return _strip_limits(state)


def _life(base: Mapping[str, Any]) -> dict[str, Any]:
    life_so_far: list[dict[str, Any]] = []
    passed: dict[str, Any] = {
        "candidate": base.get("candidate"),
        "ticket": base.get("ticket"),
    }
    manage: dict[str, list[dict[str, Any]]] = {}
    for stage in _LIFE:
        passed[stage] = _pass_stage(stage, base, life_so_far)
    for stage in _MANAGE_STEPS:
        manage[stage] = _pass_stage(stage, base, life_so_far)
    passed["manage"] = manage
    return passed


def observe_every_candidate(
    intent: Any,
    *,
    tick: Any = None,
    skip_reason: str | None,
    writer_stage: str,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
    answers_cache: dict[tuple[str, str, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Pass this candidate and ticket through the life. Never sends.

    Does not change skip_reason. The gate still decides whether this path
    runs. Choice, threshold, loop bound, parameter, and which component
    exists are the returns on that path.
    """

    row: dict[str, Any] = {
        "schema": SCHEMA,
        "gate_id": GATE_ID,
        "logged_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "broker_effect": False,
        "never_place": _never_place_stamp(),
        "skip_reason": skip_reason,
        "writer_stage": writer_stage,
        "model": MODEL,
        "identity_key": list(_cache_key(intent, extra)),
        "cache_present": isinstance(answers_cache, dict),
    }
    if not observe_every_enabled():
        row["skipped"] = (
            "GTOS_JEV_A1_LOG_off" if not a1_log_enabled() else "GTOS_JEV_A1_OBSERVE_EVERY_off"
        )
        return row
    try:
        base = _base_state(
            intent,
            tick=tick,
            skip_reason=skip_reason,
            writer_stage=writer_stage,
            occupancy=occupancy,
            governor=governor,
            extra=extra,
        )
        life = _life(base)
    except Exception as exc:
        row["error"] = type(exc).__name__
        row["life"] = None
        return row
    row["life"] = life
    row["candidate"] = base.get("candidate")
    row["ticket"] = base.get("ticket")
    questions: list[str] = []
    manage = life.get("manage") if isinstance(life.get("manage"), dict) else {}
    staged = [life.get(stage) for stage in _LIFE]
    staged.extend(manage.get(stage) for stage in _MANAGE_STEPS)
    for steps in staged:
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            for qid in step.get("questions") or []:
                if qid not in questions:
                    questions.append(qid)
    row["questions"] = questions
    try:
        from src.judgment.a1_log import _write

        _write(row)
        row["logged"] = True
    except Exception as exc:
        row["logged"] = False
        row["log_error"] = type(exc).__name__
    return row
