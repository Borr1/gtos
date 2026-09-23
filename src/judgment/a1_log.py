"""A1 life log. A candidate and a ticket pass watch, observe, admit, place,
and every manage step. Each choice, threshold, loop bound, parameter, and
component is the System One return for that ask.

One hop: ``jev_client.evaluate`` with model ``jev-1.13.0``, the same call
``place_choice`` uses (POST https://api.typesafe.ai/v1/systemone). Questions
are only Noul, Choice, or Score. Prior outcomes are attached on every ask.
An empty answer, a tie, a missing score, or an error leaves that return
unset. This module does not send an order.

Env gates stay env gates:
  GTOS_JEV_A1_LOG=1        write the life JSONL
  GTOS_JEV_ALIVE_SHADOW=1  same path
  GTOS_JEV_A1_LOG_PATH     output jsonl
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.a1_log.v0"
FLUID_SCHEMA = "gtos.judgment.a1_fluid.v0"

LIFE_STEPS = (
    "watch",
    "observe",
    "admit",
    "place",
    "move_sl",
    "move_tp",
    "close",
    "hold",
    "remove",
)

COMPONENT_ORDER = ("gold_state", "symbol_state", "aplus", "fluid", "gate")
COMPONENT_CRITERIA = {
    "gold_state": "The gold state component exists for this candidate and this ticket.",
    "symbol_state": "The symbol state component exists for this candidate and this ticket.",
    "aplus": "The aplus component exists for this candidate and this ticket.",
    "fluid": "A fluid component exists for this candidate and this ticket.",
    "gate": "The named gate component exists for this candidate and this ticket.",
}

WATCH_CRITERIA = {
    "watch": "This candidate and this ticket stay on watch.",
    "release": "This watch step releases this candidate and this ticket.",
}
OBSERVE_CRITERIA = {
    "observe": "Observe this candidate and this ticket.",
    "leave": "This observe step adds nothing.",
}
ADMIT_CRITERIA = {
    "admit": "Admit this candidate.",
    "abstain": "Do not admit this candidate on this bar.",
    "hard_refuse": "Hard refuse this candidate.",
}
PLACE_CRITERIA = {
    "PLACE": "This candidate is the order on this bar.",
    "STAND": "This candidate is not the order on this bar.",
    "DELAY": "This bar is not the bar for this candidate.",
    "REMINT": "A re-entry of an existing ticket fits this candidate.",
    "FLATTEN_CANDIDATE": "This candidate is a reduction of open risk.",
}
MANAGE_CRITERIA = {
    "leave_orig": "Leave the original stop and target on this step.",
    "move_sl": "Move the stop. The stop is the parameter score on this step.",
    "move_tp": "Move the target. The target is the parameter score on this step.",
    "close": "Close this ticket on this step.",
    "hold": "Hold. Do not move and do not close on this step.",
    "remove": "Cancel this pending on this step.",
}
STEP_CRITERIA = {
    "watch": WATCH_CRITERIA,
    "observe": OBSERVE_CRITERIA,
    "admit": ADMIT_CRITERIA,
    "place": PLACE_CRITERIA,
    "move_sl": MANAGE_CRITERIA,
    "move_tp": MANAGE_CRITERIA,
    "close": MANAGE_CRITERIA,
    "hold": MANAGE_CRITERIA,
    "remove": MANAGE_CRITERIA,
}

_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_SKIP_KEY_PARTS = (
    "floor",
    "baseline",
    "to_pass",
    "pass_line",
    "equity",
    "balance",
    "drawdown",
    "profit_target",
    "max_loss",
    "daily_loss",
    "kill",
    "day_start",
)
_SKIP_WALK = {"account", "books", "peer_books", "bars", "candles", "a1_life"}
_LEVEL_KEYS = {
    "entry",
    "stop",
    "target",
    "stop_dist",
    "spread",
    "spread_r_of_stop",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
}

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG = REPO_ROOT / "judgment" / "astra" / "lab" / "a1" / "a1.jsonl"
_BOOKS_CACHE: dict[str, Any] = {}



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


def _env_on(*names: str) -> bool:
    for name in names:
        if os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}:
            return True
    return False


def a1_enabled() -> bool:
    return _env_on("GTOS_JEV_A1_LOG", "GTOS_JEV_ALIVE_SHADOW")


def alive_shadow_enabled() -> bool:
    return _env_on("GTOS_JEV_ALIVE_SHADOW", "GTOS_JEV_A1_LOG")


def _log_path() -> Path:
    override = (os.environ.get("GTOS_JEV_A1_LOG_PATH") or "").strip()
    path = Path(override) if override else DEFAULT_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write(row: dict[str, Any]) -> None:
    path = _log_path()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")


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


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _number(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision."""

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


def _choice_of(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
    probs = _probs(block)
    kept = {name: probs[name] for name in order if name in probs}
    choice = None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(probs or None, order)
        if picked in order:
            choice = str(picked)
    except Exception:
        choice = None
    if choice not in order:
        choice = _unique(probs, order)
    if choice not in order:
        choice = None
    return choice, kept


def _score_of(block: Any, qid: str | None = None) -> float | None:
    """The Score that came back. It is not snapped to a level."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))


    if not isinstance(block, dict):
        return None
    probs = _probs(block)
    if probs and _unique(probs, tuple(probs)) is None:
        return None
    number = None
    try:
        from .jev_questions import returned_number

        number = _number(returned_number(block))
    except Exception:
        number = None
    if number is not None:
        return number
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _number(raw)


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A float is not cut at a line."""

    if not isinstance(block, dict):
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    number = _number(raw)
    if number is not None:
        return number
    picked = _unique(_probs(block), ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
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


def _choice_text(step: str) -> str:
    return (
        f"Life step {step} for this candidate and this ticket. "
        "Both pass this step. Pick one option. "
        "The option you return is the decision. "
        "An empty answer or a tie is not a decision. "
        "Do not send an order."
    )


def _score_text(step: str, noun: str) -> str:
    return (
        f"At {step}, what {noun} applies to this candidate and this ticket? "
        f"The score you return is that {noun}. "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "Do not send an order."
    )


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body = {"type": "choice", "instructions": instructions, "criteria": dict(criteria)}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(criteria))
        if isinstance(built, dict):
            block = built.get(qid)
            if isinstance(block, dict):
                shaped = dict(block)
                shaped["type"] = "choice"
                shaped["instructions"] = instructions
                shaped["criteria"] = dict(criteria)
                return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _score_question(qid: str, instructions: str, levels: list[str]) -> dict[str, Any]:
    """Amount anchors from this card. An ordinal keeps its words."""
    return _shape_score(qid, instructions, levels, wrapped=True)



def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes, for this candidate and this ticket.",
                "false": "No, for this candidate and this ticket.",
            },
        }
    }


def _levels(state: Mapping[str, Any] | None) -> list[str]:
    """Live prices and spreads already on the state. A score may sit between them."""

    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        low = key.lower()
        if any(part in low for part in _SKIP_KEY_PARTS):
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                name = str(child_key)
                if name.lower() in _SKIP_WALK:
                    continue
                walk(name, child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            return
        if low not in _LEVEL_KEYS:
            return
        number = _number(value)
        if number is not None:
            found.append(number)

    for key, value in dict(state or {}).items():
        if str(key).lower() in _SKIP_WALK:
            continue
        walk(str(key), value)
    ordered = sorted(set(found))
    return [format(number, ".10g") for number in ordered]


def _questions(levels: list[str]) -> dict[str, Any]:
    """The whole life on one ask. Types are choice, score, or noul."""

    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "a1_component",
        "Which component exists for this candidate and this ticket? "
        "Both pass this ask. The name you return is the component. "
        "An empty answer or a tie is not a component. "
        "Do not send an order.",
        COMPONENT_CRITERIA,
    ))
    pack.update(_noul_question(
        "a1_component_present",
        "Does that component exist for this candidate and this ticket? "
        "An empty answer leaves it unset. Do not send an order.",
    ))
    pack.update(_noul_question(
        "a1_cost",
        "Does this cost refuse this candidate and this ticket? "
        "An empty answer leaves it unset. Do not send an order.",
    ))
    for step in LIFE_STEPS:
        pack.update(_choice_question(f"a1_{step}", _choice_text(step), STEP_CRITERIA[step]))
        pack.update(_score_question(
            f"a1_{step}_threshold",
            _score_text(step, "threshold"),
            levels,
        ))
        pack.update(_score_question(
            f"a1_{step}_loop",
            _score_text(step, "loop bound"),
            levels,
        ))
        pack.update(_score_question(
            f"a1_{step}_parameter",
            _score_text(step, "parameter"),
            levels,
        ))
    return pack


def _subjects(state: Mapping[str, Any] | None) -> tuple[Any, Any]:
    src = dict(state or {})
    ident = src.get("identity") if isinstance(src.get("identity"), Mapping) else {}
    extra = src.get("extra") if isinstance(src.get("extra"), Mapping) else {}
    geometry = src.get("geometry") if isinstance(src.get("geometry"), Mapping) else {}
    candidate = src.get("candidate_id")
    if candidate in (None, ""):
        candidate = ident.get("candidate_id") if isinstance(ident, Mapping) else None
    if candidate in (None, ""):
        candidate = extra.get("candidate_id") if isinstance(extra, Mapping) else None
    ticket = src.get("ticket")
    if ticket in (None, ""):
        ticket = ident.get("ticket") if isinstance(ident, Mapping) else None
    if ticket in (None, ""):
        ticket = extra.get("ticket") if isinstance(extra, Mapping) else None
    if ticket in (None, ""):
        ticket = geometry.get("ticket") if isinstance(geometry, Mapping) else None
    return candidate, ticket


def _blank_step() -> dict[str, Any]:
    return {
        "choice": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "probabilities": {},
        "error": None,
    }


def _read(answers: Mapping[str, Any] | None, receipt_error: Any) -> dict[str, Any]:
    payload = answers if isinstance(answers, Mapping) else {}
    component, component_probs = _choice_of(payload.get("a1_component"), COMPONENT_ORDER)
    present = _noul_of(payload.get("a1_component_present"))
    cost = _noul_of(payload.get("a1_cost"))
    life: dict[str, Any] = {}
    remember: list[tuple[str, Any, str | None]] = [
        ("a1_component", component, _miss(payload.get("a1_component"), component, COMPONENT_ORDER, receipt_error)),
        (
            "a1_component_present",
            present,
            _miss(payload.get("a1_component_present"), present, ("true", "false"), receipt_error),
        ),
        ("a1_cost", cost, _miss(payload.get("a1_cost"), cost, ("true", "false"), receipt_error)),
    ]
    for step in LIFE_STEPS:
        order = tuple(STEP_CRITERIA[step])
        choice_block = payload.get(f"a1_{step}")
        threshold_block = payload.get(f"a1_{step}_threshold")
        loop_block = payload.get(f"a1_{step}_loop")
        parameter_block = payload.get(f"a1_{step}_parameter")
        choice, probs = _choice_of(choice_block, order)
        threshold = _score_of(threshold_block, f"a1_{step}_threshold")
        loop_bound = _score_of(loop_block, f"a1_{step}_loop")
        parameter = _score_of(parameter_block, f"a1_{step}_parameter")
        choice_error = None if choice is not None else _miss(choice_block, choice, order, receipt_error)
        life[step] = {
            "choice": choice,
            "threshold": threshold,
            "loop_bound": loop_bound,
            "parameter": parameter,
            "probabilities": probs,
            "error": choice_error,
        }
        remember.append((f"a1_{step}", choice, choice_error))
        remember.append((
            f"a1_{step}_threshold",
            threshold,
            None if threshold is not None else _miss(threshold_block, threshold, (), receipt_error),
        ))
        remember.append((
            f"a1_{step}_loop",
            loop_bound,
            None if loop_bound is not None else _miss(loop_block, loop_bound, (), receipt_error),
        ))
        remember.append((
            f"a1_{step}_parameter",
            parameter,
            None if parameter is not None else _miss(parameter_block, parameter, (), receipt_error),
        ))
    return {
        "component": component,
        "component_probabilities": component_probs,
        "component_present": present,
        "cost_noul": cost,
        "life": life,
        "remember": remember,
    }


def _remember(state: Mapping[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
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


def _ask(state: Mapping[str, Any] | None, questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = dict(state or {})
    for key in ("a1_life", "a1_component", "a1_component_present", "a1_cost_noul", "prior_outcomes"):
        payload.pop(key, None)
    candidate, ticket = _subjects(payload)
    payload["candidate"] = candidate
    payload["ticket"] = ticket
    payload["model"] = MODEL
    try:
        from .jev_questions import prior_outcomes

        payload["prior_outcomes"] = prior_outcomes(state=payload, questions=questions)
    except Exception:
        pass
    try:
        from .jev_client import evaluate

        receipt = evaluate(payload, questions=questions, merge_sleeve=False)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {"error": type(exc).__name__, "answers": {}, "state": payload, "receipt": {}, "model": MODEL}
    if not isinstance(receipt, dict):
        return {"error": "evaluate_not_a_dict", "answers": {}, "state": payload, "receipt": {}, "model": MODEL}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "error": error,
        "answers": answers,
        "state": payload,
        "receipt": receipt,
        "model": receipt.get("model") or MODEL,
    }


def _decide(state: Mapping[str, Any] | None) -> dict[str, Any]:
    _bind_card(state)
    try:
        questions = _questions(_levels(state))
    except Exception as exc:  # noqa: BLE001
        card = _read({}, type(exc).__name__)
        card["model"] = MODEL
        card["questions"] = []
        card["answers"] = {}
        card["usage"] = None
        return card
    if not questions:
        card = _read({}, "question_pack_fail")
        card["model"] = MODEL
        card["questions"] = []
        card["answers"] = {}
        card["usage"] = None
        return card
    asked = _ask(state, questions)
    card = _read(asked.get("answers") or {}, asked.get("error"))
    _remember(asked.get("state") or {}, card["remember"])
    card["model"] = asked.get("model") or MODEL
    card["questions"] = list(questions)
    card["answers"] = asked.get("answers") or {}
    receipt = asked.get("receipt") if isinstance(asked.get("receipt"), dict) else {}
    card["usage"] = receipt.get("usage")
    card["ok"] = receipt.get("ok")
    return card


def _take(items: list[Any], bound: Any) -> list[Any] | None:
    """Keep items out to the returned bound. A missing bound stays missing."""

    number = _number(bound)
    if number is None:
        return None
    taken: list[Any] = []
    for item in items:
        if len(taken) >= number:
            break
        taken.append(item)
    return taken


def _state_for_post(state: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    base = dict(state or {})
    try:
        from .equity_frame import attach_account

        posted = attach_account(base)
    except Exception:
        posted = base
    if not isinstance(posted, dict):
        posted = base
    account = posted.get("account") if isinstance(posted.get("account"), dict) else {}
    stamp = {
        "equity_card_in_post": account.get("equity") is not None,
        "equity": account.get("equity"),
        "cash_unit_usd": account.get("cash_unit_usd"),
        "terminal_read": account.get("terminal_read"),
        "invented": False,
    }
    return posted, stamp


def _lock() -> dict[str, Any]:
    try:
        from .process_lock import stamp_lock

        stamped = stamp_lock()
        if isinstance(stamped, dict):
            return stamped
    except Exception:
        pass
    return {}


def _host_site(gate_id: str | None) -> Any:
    if not gate_id:
        return None
    try:
        from .host_sites import HOST_SITES

        return HOST_SITES.get(gate_id)
    except Exception:
        return None


def _shell(schema: str, gate_id: str | None, extra: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "schema": schema,
        "gate_id": gate_id or None,
        "logged_at_utc": _now(),
        "model": MODEL,
        "agent_order_send": False,
        "broker_effect": False,
        "component": None,
        "component_present": None,
        "cost_noul": None,
        "choice": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "noul": None,
        "life": {step: _blank_step() for step in LIFE_STEPS},
        "extra": dict(extra or {}),
        **_lock(),
    }


def _fill(row: dict[str, Any], card: Mapping[str, Any], posted: Mapping[str, Any], equity_stamp: Mapping[str, Any]) -> None:
    life = card.get("life") if isinstance(card.get("life"), Mapping) else {}
    observe_step = life.get("observe") if isinstance(life.get("observe"), Mapping) else {}
    row["model"] = card.get("model") or MODEL
    row["component"] = card.get("component")
    row["component_present"] = card.get("component_present")
    row["component_probabilities"] = card.get("component_probabilities") or {}
    row["cost_noul"] = card.get("cost_noul")
    row["noul"] = card.get("component_present")
    row["choice"] = observe_step.get("choice")
    row["threshold"] = observe_step.get("threshold")
    row["loop_bound"] = observe_step.get("loop_bound")
    row["parameter"] = observe_step.get("parameter")
    row["probabilities"] = observe_step.get("probabilities") or {}
    row["life"] = life
    row["questions"] = list(card.get("questions") or [])
    row["answers"] = card.get("answers") or {}
    row["state"] = dict(posted)
    row["posted_equity_card"] = dict(equity_stamp)
    row["host_site"] = _host_site(row.get("gate_id"))
    row["usage"] = card.get("usage")
    row["ok"] = card.get("ok")
    observe_error = observe_step.get("error")
    row["error"] = observe_error if row["choice"] is None else None


def _previews(row: dict[str, Any], card: Mapping[str, Any], extra: Mapping[str, Any] | None) -> None:
    life = card.get("life") if isinstance(card.get("life"), Mapping) else {}
    observe_step = life.get("observe") if isinstance(life.get("observe"), Mapping) else {}
    bound = observe_step.get("loop_bound")
    payload = extra or {}
    units = payload.get("units")
    if isinstance(units, list):
        row["units_preview"] = _take(units, bound)
    keys = payload.get("packet_keys")
    if isinstance(keys, list):
        row["packet_keys"] = _take(keys, bound)


def observe(
    gate_id: str,
    state: dict[str, Any] | None,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ask the life for this candidate and this ticket. A miss stays unset."""

    row = _shell(SCHEMA, gate_id, extra)
    if not a1_enabled():
        row["skipped"] = "GTOS_JEV_A1_LOG_off"
        return row
    posted, equity_stamp = _state_for_post(state)
    if extra:
        posted["extra"] = dict(extra)
    if gate_id:
        posted["gate_id"] = gate_id
    card = _decide(posted)
    _fill(row, card, posted, equity_stamp)
    _previews(row, card, extra)
    try:
        _write(row)
        row["logged"] = True
    except Exception as exc:  # noqa: BLE001
        row["logged"] = False
        row["log_error"] = type(exc).__name__
    return row


def observe_fluid_inventory(
    state: dict[str, Any] | None,
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ask which component exists and how far the stamp runs. A miss stamps nothing."""

    row = _shell(FLUID_SCHEMA, "FLUID-INVENTORY", extra)
    ids: list[str] = []
    try:
        from .fluid_gates import fluid_gate_ids, inventory_counts

        ids = [str(item) for item in list(fluid_gate_ids())]
        row["inventory"] = inventory_counts()
    except Exception:
        ids = []
    row["n_fluid"] = len(ids)
    row["fluid_ids"] = ids
    if not a1_enabled():
        row["skipped"] = "GTOS_JEV_A1_LOG_off"
        row["gates"] = None
        return row
    posted, equity_stamp = _state_for_post(state)
    if extra:
        posted["extra"] = dict(extra)
    posted["gate_id"] = "FLUID-INVENTORY"
    posted["fluid_ids"] = ids
    card = _decide(posted)
    _fill(row, card, posted, equity_stamp)
    life = card.get("life") if isinstance(card.get("life"), Mapping) else {}
    observe_step = life.get("observe") if isinstance(life.get("observe"), Mapping) else {}
    chosen = _take(ids, observe_step.get("loop_bound")) if card.get("component") == "fluid" else None
    if chosen is None:
        row["gates"] = None
    else:
        stamps = {
            gid: {
                "choice": observe_step.get("choice"),
                "score": observe_step.get("parameter"),
                "threshold": observe_step.get("threshold"),
                "loop_bound": observe_step.get("loop_bound"),
                "noul": card.get("component_present"),
            }
            for gid in chosen
        }
        row["gates"] = stamps
    try:
        _write(row)
        row["logged"] = True
    except Exception as exc:  # noqa: BLE001
        row["logged"] = False
        row["log_error"] = type(exc).__name__
    return row


def _attr(obj: Any, *names: str) -> Any:
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj.get(name)
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _attach_equity_card(state: dict[str, Any] | None) -> dict[str, Any] | None:
    if state is None:
        return None
    try:
        from .equity_frame import attach_account

        attached = attach_account(state)
        if isinstance(attached, dict):
            return attached
    except Exception:
        pass
    return state


def _challenge_books_for(symbol: str) -> dict[str, Any] | None:
    try:
        from .bars import books_for_symbol, challenge_tape_present, normalize_symbol
    except Exception:
        return None
    sym = normalize_symbol(symbol)
    if not challenge_tape_present(sym):
        return None
    hit = _BOOKS_CACHE.get(sym)
    if hit is not None:
        return hit
    loaded = books_for_symbol(sym)
    _BOOKS_CACHE[sym] = loaded
    return loaded


def _intent_blocks(
    intent: Any,
    tick: Any = None,
    *,
    origin: str = "w7_ultimate_book",
    books: dict[str, Any] | None = None,
    as_of_utc: datetime | None = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
    peer_books: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Geometry and tape already on the intent. Missing fields stay missing."""

    del occupancy, governor
    try:
        from .bars import normalize_symbol
        from .sleeve_from_tape import features_from_books
        from .symbol_state import load_peer_books_for
    except Exception:
        return None
    raw_symbol = _attr(intent, "symbol")
    symbol = None
    if raw_symbol not in (None, ""):
        try:
            symbol = normalize_symbol(str(raw_symbol))
        except Exception:
            symbol = str(raw_symbol)
    sleeve = _attr(intent, "sleeve", "tag")
    sleeve = None if sleeve in (None, "") else str(sleeve)
    side = _attr(intent, "side", "direction")
    side = None if side in (None, "") else str(side)
    entry = _attr(intent, "entry", "entry_price")
    stop = _attr(intent, "stop", "sl")
    stop_dist = _attr(intent, "stop_dist")
    target = _attr(intent, "target", "tp")
    bid = _attr(tick, "bid")
    ask = _attr(tick, "ask")
    spread_r = None
    try:
        sd = float(stop_dist)
        if sd > 0 and bid is not None and ask is not None:
            spread_r = (float(ask) - float(bid)) / sd
    except (TypeError, ValueError):
        spread_r = None
    as_of = as_of_utc or datetime.now(timezone.utc)
    books_here = books if books is not None else (_challenge_books_for(symbol) if symbol else None)
    feats: dict[str, Any] = {}
    if sleeve is not None:
        feats["tag"] = sleeve
    if books_here:
        try:
            feats = features_from_books(books_here, as_of, tag=sleeve)
        except Exception:
            feats = {"tag": sleeve} if sleeve is not None else {}
    loaded_peers = peer_books
    if loaded_peers is None and symbol:
        try:
            loaded_peers = load_peer_books_for(symbol)
        except Exception:
            loaded_peers = {}
    candidate = _attr(intent, "candidate_id", "ticket")
    order_type = _attr(intent, "order_type")
    return {
        "symbol": symbol,
        "sleeve": sleeve,
        "side": side,
        "as_of": as_of,
        "origin": origin,
        "books": books_here,
        "peer_books": loaded_peers or {},
        "feats": feats,
        "candidate_id": None if candidate in (None, "") else str(candidate),
        "ticket": _attr(intent, "ticket"),
        "geometry": {
            "entry": entry,
            "stop": stop,
            "target": target,
            "stop_dist": stop_dist,
            "order_type": order_type,
        },
        "cost": {
            "spread_r_of_stop": spread_r,
            "source": "tick" if spread_r is not None else None,
        },
    }


def _stamp_life(state: dict[str, Any], card: Mapping[str, Any]) -> dict[str, Any]:
    stamped = dict(state)
    stamped["a1_component"] = card.get("component")
    stamped["a1_component_present"] = card.get("component_present")
    stamped["a1_cost_noul"] = card.get("cost_noul")
    stamped["a1_life"] = card.get("life")
    stamped["model"] = card.get("model") or MODEL
    return stamped


def _assemble_symbol(packed: Mapping[str, Any], occupancy: dict[str, Any] | None, governor: dict[str, Any] | None) -> dict[str, Any] | None:
    try:
        from .symbol_state import assemble_symbol_state_v0
    except Exception:
        return None
    try:
        assembled = assemble_symbol_state_v0(
            as_of_utc=packed.get("as_of"),
            side=packed.get("side"),
            sleeve=packed.get("sleeve"),
            symbol=packed.get("symbol"),
            candidate_id=packed.get("candidate_id"),
            origin_organism=packed.get("origin"),
            as_of_clock="live_intent",
            books=packed.get("books"),
            peer_books=packed.get("peer_books"),
            geometry=packed.get("geometry"),
            cost=packed.get("cost"),
            sleeve_features=packed.get("feats"),
            occupancy=occupancy or {},
            governor=governor or {},
        )
    except Exception:
        return None
    return assembled if isinstance(assembled, dict) else None


def intent_symbol_state(
    intent: Any,
    tick: Any = None,
    *,
    origin: str = "w7_ultimate_book",
    books: dict[str, Any] | None = None,
    as_of_utc: datetime | None = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
    peer_books: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Assemble symbol_state from the blocks. The caller already named this component."""

    packed = _intent_blocks(
        intent,
        tick,
        origin=origin,
        books=books,
        as_of_utc=as_of_utc,
        occupancy=occupancy,
        governor=governor,
        peer_books=peer_books,
    )
    if packed is None:
        return None
    assembled = _assemble_symbol(packed, occupancy, governor)
    if assembled is None:
        return None
    return _attach_equity_card(assembled)


def _assemble_aplus(
    intent: Any,
    *,
    as_of_utc: datetime | None,
    books: dict[str, Any] | None,
    occupancy: dict[str, Any] | None,
) -> dict[str, Any] | None:
    try:
        from .aplus_sleeve import CATALOG, assemble_aplus_state, from_catalog
    except Exception:
        return None
    sleeve = _attr(intent, "sleeve", "tag")
    setup_id = _attr(intent, "setup_id")
    raw = str(setup_id or "")
    if raw not in CATALOG and sleeve not in (None, ""):
        name = str(sleeve)
        if name.startswith("aplus_"):
            name = name[len("aplus_") :]
        if name in CATALOG:
            raw = name
    if raw not in CATALOG:
        return None
    try:
        spec = from_catalog(raw)
        as_of = as_of_utc or datetime.now(timezone.utc)
        books_here = books if books is not None else _challenge_books_for(spec.symbol)
        order_type = _attr(intent, "order_type")
        candidate = _attr(intent, "candidate_id", "ticket")
        assembled = assemble_aplus_state(
            spec,
            as_of_utc=as_of,
            side=_attr(intent, "side", "direction"),
            candidate_id=None if candidate in (None, "") else str(candidate),
            as_of_clock="live_intent",
            books=books_here,
            geometry={
                "entry": _attr(intent, "entry", "entry_price"),
                "stop": _attr(intent, "stop", "sl"),
                "target": _attr(intent, "target", "tp"),
                "stop_dist": _attr(intent, "stop_dist"),
                "order_type": order_type,
            },
            occupancy=occupancy or {},
        )
    except Exception:
        return None
    return assembled if isinstance(assembled, dict) else None


def _assemble_gold(
    packed: Mapping[str, Any],
    occupancy: dict[str, Any] | None,
    governor: dict[str, Any] | None,
) -> dict[str, Any] | None:
    try:
        from .gold_state import assemble_gold_state_v0
        from .world_state import load_peer_books
    except Exception:
        return None
    try:
        peers = load_peer_books()
        assembled = assemble_gold_state_v0(
            as_of_utc=packed.get("as_of"),
            side=packed.get("side"),
            sleeve=packed.get("sleeve"),
            symbol=packed.get("symbol"),
            candidate_id=packed.get("candidate_id"),
            origin_organism=packed.get("origin"),
            as_of_clock="live_intent",
            books=packed.get("books"),
            peer_books=packed.get("peer_books") or peers,
            geometry=packed.get("geometry"),
            cost=packed.get("cost"),
            sleeve_features=packed.get("feats"),
            occupancy=occupancy or {},
            governor=governor or {},
        )
    except Exception:
        return None
    return assembled if isinstance(assembled, dict) else None


def _thin_intent(intent: Any, origin: str, as_of_utc: datetime | None) -> dict[str, Any]:
    as_of = as_of_utc or datetime.now(timezone.utc)
    if intent is None:
        return {"origin": origin, "as_of": as_of}
    candidate = _attr(intent, "candidate_id", "ticket")
    return {
        "symbol": _attr(intent, "symbol"),
        "sleeve": _attr(intent, "sleeve", "tag"),
        "side": _attr(intent, "side", "direction"),
        "origin": origin,
        "as_of": as_of,
        "candidate_id": None if candidate in (None, "") else str(candidate),
        "ticket": _attr(intent, "ticket"),
    }


def intent_gold_state(
    intent: Any,
    tick: Any = None,
    *,
    origin: str = "w7_ultimate_book",
    books: dict[str, Any] | None = None,
    as_of_utc: datetime | None = None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
    peer_books: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """The component that exists is the return. A miss does not pick an assembler."""

    packed = _intent_blocks(
        intent,
        tick,
        origin=origin,
        books=books,
        as_of_utc=as_of_utc,
        occupancy=occupancy,
        governor=governor,
        peer_books=peer_books,
    )
    facts = packed if isinstance(packed, dict) else _thin_intent(intent, origin, as_of_utc)
    card = _decide(facts)
    choice = card.get("component")
    assembled: dict[str, Any] | None = None
    if choice == "aplus":
        assembled = _assemble_aplus(intent, as_of_utc=as_of_utc, books=books, occupancy=occupancy)
    elif choice == "symbol_state":
        assembled = intent_symbol_state(
            intent,
            tick,
            origin=origin,
            books=books,
            as_of_utc=as_of_utc,
            occupancy=occupancy,
            governor=governor,
            peer_books=peer_books,
        )
    elif choice == "gold_state" and isinstance(packed, dict):
        assembled = _assemble_gold(packed, occupancy, governor)
    base = assembled if isinstance(assembled, dict) else dict(facts)
    return _attach_equity_card(_stamp_life(base, card))


_intent_gold_state = intent_gold_state


def _live_news_extra(as_of: datetime | None, extra: dict[str, Any]) -> dict[str, Any]:
    out = dict(extra)
    try:
        from .host_events import news_inventory_extra

        out.update(news_inventory_extra(as_of, live=True))
    except Exception:
        pass
    return out


def _measured_spread(intent: Any, tick: Any) -> tuple[float | None, float | None, float | None]:
    try:
        stop = float(getattr(intent, "stop_dist", 0.0) or 0.0)
    except (TypeError, ValueError):
        stop = 0.0
    try:
        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)
    except (TypeError, ValueError):
        bid, ask = 0.0, 0.0
    spread = (ask - bid) if ask and bid else None
    spread_r = ((ask - bid) / stop) if stop > 0 and ask >= bid > 0 else None
    return stop if stop else None, spread, spread_r


def maybe_observe_ub_auth_010(decision: Any, config: Any = None) -> None:
    if not a1_enabled():
        return
    try:
        payload = decision if isinstance(decision, dict) else getattr(decision, "__dict__", {})
        units = []
        if isinstance(payload, dict):
            units = payload.get("realized") or payload.get("units") or []
            status = payload.get("status")
        else:
            status = getattr(decision, "status", None)
            units = getattr(decision, "realized", None) or getattr(decision, "units", None) or []
        extra = {
            "status": status,
            "n_units": len(units) if isinstance(units, list) else None,
            "config_present": config is not None,
        }
        first = units[0] if isinstance(units, list) and units else None
        state = intent_gold_state(first, origin="w7_ultimate_book") if first else None
        observe(
            "UB-AUTH-010",
            state,
            extra={
                "bridge": extra,
                "units": list(units) if isinstance(units, list) else [],
            },
        )
        observe_fluid_inventory(state, extra={"site": "UB-AUTH-010", "bridge": extra})
        try:
            from .unique_loader import observe_unique_apply

            observe_unique_apply(namespace="operator", origin="a1_ub_auth_010")
        except Exception:
            pass
    except Exception:
        return


def maybe_observe_ub_plc_017(
    intent: Any,
    tick: Any,
    cost_skip: str | None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
) -> None:
    if not a1_enabled():
        return
    try:
        as_of = datetime.now(timezone.utc)
        stop, spread, spread_r = _measured_spread(intent, tick)
        extra = _live_news_extra(
            as_of,
            {
                "symbol": getattr(intent, "symbol", None),
                "sleeve": getattr(intent, "sleeve", None),
                "stop_dist": stop,
                "spread": spread,
                "spread_r_of_stop": spread_r,
                "cost_skip": cost_skip,
            },
        )
        state = intent_gold_state(
            intent,
            tick,
            origin="w7_ultimate_book",
            as_of_utc=as_of,
            occupancy=occupancy,
            governor=governor,
        )
        observe("UB-PLC-017", state, extra=extra)
        observe("F5-JEV-004", state, extra=extra)
        observe("f5_xau_flow_alignment_size_tilt", state, extra=extra)
    except Exception:
        return


def maybe_observe_fluid_at_place(
    intent: Any,
    tick: Any,
    cost_skip: str | None,
    occupancy: dict[str, Any] | None = None,
    governor: dict[str, Any] | None = None,
) -> None:
    if not a1_enabled():
        return
    try:
        as_of = datetime.now(timezone.utc)
        state = intent_gold_state(
            intent,
            tick,
            origin="w7_ultimate_book",
            as_of_utc=as_of,
            occupancy=occupancy,
            governor=governor,
        )
        observe_fluid_inventory(
            state,
            extra=_live_news_extra(
                as_of,
                {
                    "site": "UB-PLC-017",
                    "cost_skip": cost_skip,
                    "must_not_mutate_cost_skip": True,
                },
            ),
        )
    except Exception:
        return


def maybe_observe_fluid_at_admit(decision: Any, config: Any = None) -> None:
    maybe_observe_ub_auth_010(decision, config)


def observe_sel_v4_002(packet: dict[str, Any] | None) -> dict[str, Any]:
    """Research caller. The logged key list runs out to the returned loop bound."""

    packet = packet or {}
    state = intent_gold_state(packet, origin="historical_lab")
    keys = sorted(str(key) for key in packet.keys())
    return observe(
        "SEL-V4-002",
        state,
        extra={"packet_keys": keys, "n_packet_keys": len(keys)},
    )
