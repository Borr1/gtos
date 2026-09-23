"""Fluid cycle. Every decision is the System One return for this state.

One hop: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached on
the ask, and the return is stored for the next ask.

The cycle read, the dark noul, sufficiency, which component exists, the
threshold, the loop bound, and the parameter are that return. Assembled
fanout packs ride the same post. An unassembled pack adds no question and
no filled answer. An empty answer, a tie, or an error leaves that return
unset and does not restore a constant.

Floor and baseline are not a question. This module does not place, does
not invent a news protocol, and does not authorize a label apply. Judge
code stays unable to send.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
API_URL = "https://api.typesafe.ai/v1/systemone"
GATE_ID = "FLUID-CYCLE"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_READ_ORDER = ("read", "stand", "withhold")
_COMPONENT_ORDER = ("fanout", "s14", "world", "rdf", "everywhere", "none")
_NOUL_ORDER = ("true", "false")
_ALLOWED = frozenset({"noul", "choice", "score"})
_LIMIT_PARTS = ("floor", "baseline")
_SECRET_PARTS = ("api_key", "apikey", "authorization", "secret", "password", "token")
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
_OWN_IDS = (
    "cycle_read",
    "cycle_dark",
    "cycle_state_sufficient",
    "cycle_component_exists",
    "cycle_component",
    "cycle_threshold",
    "cycle_loop_bound",
    "cycle_parameter",
)
_TOP_FIELDS = _OWN_IDS

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

def _env_on(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def cycle_call_enabled() -> bool:
    """Env gate. Observe-every arms it. The fluid-cycle flag arms it with a log gate."""

    observe = (_env_on("GTOS_JEV_A1_LOG") or _env_on("GTOS_JEV_ALIVE_SHADOW")) and _env_on(
        "GTOS_JEV_A1_OBSERVE_EVERY"
    )
    if observe:
        return True
    return _env_on("GTOS_JEV_FLUID_CYCLE_CALL") and (
        _env_on("GTOS_JEV_A1_LOG") or _env_on("GTOS_JEV_ALIVE_SHADOW")
    )


def _limit_key(name: str) -> bool:
    low = str(name).lower().replace("-", "_")
    return any(part in low for part in _LIMIT_PARTS)


def _secret_key(name: str) -> bool:
    low = str(name).lower().replace("-", "_")
    return any(part in low for part in _SECRET_PARTS)


def _banned_text(value: str) -> bool:
    low = value.lower()
    if any(part in low for part in _LIMIT_PARTS):
        return True
    compact = value.replace(",", "").replace("_", "").replace(" ", "").lower()
    return any(token.lower() in compact for token in _BANNED_TEXT)


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
    """Drop limit keys and secret keys. Remaining facts stay facts.

    A repeated container is a cycle. The walk stops there. No depth cap.
    """

    if seen is None:
        seen = set()
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        return _number(value)
    if isinstance(value, str):
        return _scrub_text(value)
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name) or _secret_key(name):
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


def _block_banned(qid: str, block: Any) -> bool:
    if _limit_key(qid):
        return True
    try:
        text = json.dumps(block, default=str)
    except Exception:
        text = str(block)
    return _banned_text(text)


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {str(key): _scrub_text(str(val)) for key, val in criteria.items()}
    body: dict[str, Any] = {"type": "choice", "instructions": text, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, cleaned)
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    body["type"] = "choice"
    body["instructions"] = text
    body["criteria"] = cleaned
    return {qid: body}


def _score_question(qid: str, instructions: str) -> dict[str, Any]:
    """Amount anchors from this card. An ordinal keeps its words."""
    return _shape_score(qid, instructions, None, wrapped=True)



def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(instructions),
            "criteria": {
                "true": "Yes, on this state.",
                "false": "No, on this state.",
            },
        }
    }


def _own_pack() -> dict[str, Any]:
    """The cycle piece. The menu names an answer. It does not decide."""

    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "cycle_read",
        "Which read is this fluid cycle? "
        "The option with the single highest probability is the read. "
        "An empty answer or a tie leaves the read unset. "
        "This question does not send and does not place.",
        {
            "read": "This cycle's reading is the return on this post.",
            "stand": "This cycle stands.",
            "withhold": "This cycle withholds the reading.",
        },
    ))
    pack.update(_noul_question(
        "cycle_dark",
        "Is this fluid cycle dark for this state? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "Dark does not authorize a label apply and does not place.",
    ))
    pack.update(_noul_question(
        "cycle_state_sufficient",
        "Are the named blocks present enough to read this cycle? "
        "The noul you return is that sufficiency. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_noul_question(
        "cycle_component_exists",
        "Does the fluid cycle component exist on this state? "
        "The noul you return is that existence. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_choice_question(
        "cycle_component",
        "Which component is this fluid cycle reading? "
        "The option with the single highest probability is the component. "
        "An empty answer or a tie leaves the component unset. "
        "This question does not send.",
        {
            "fanout": "The symbol fanout is the component on this state.",
            "s14": "The regime pack is the component on this state.",
            "world": "The world pack is the component on this state.",
            "rdf": "The rdf pack is the component on this state.",
            "everywhere": "The everywhere pack is the component on this state.",
            "none": "No named pack is the component on this state.",
        },
    ))
    pack.update(_score_question(
        "cycle_threshold",
        "The score you return is the threshold for this cycle. "
        "It may sit between the levels. "
        "An empty score leaves the threshold unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        "cycle_loop_bound",
        "The score you return is how many steps this cycle still covers. "
        "It may sit between the levels. "
        "An empty score leaves the bound unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        "cycle_parameter",
        "The score you return is the parameter for this cycle. "
        "It may sit between the levels. "
        "An empty score leaves the parameter unset. "
        "This question does not send.",
    ))
    return pack


def _accept(
    qid: str,
    block: Any,
) -> tuple[dict[str, Any], tuple[str, tuple[str, ...]]] | None:
    """Keep a Noul, Choice, or Score. A floor or a baseline is not asked."""

    if not isinstance(block, Mapping) or _block_banned(qid, block):
        return None
    kind = str(block.get("type") or "").strip().lower()
    if kind not in _ALLOWED:
        return None
    instructions = _scrub_text(str(block.get("instructions") or "")).strip()
    if not instructions or _banned_text(instructions):
        return None
    criteria = block.get("criteria")
    cleaned: dict[str, Any] = {"type": kind, "instructions": instructions}
    if kind == "choice":
        if not isinstance(criteria, Mapping) or not criteria:
            return None
        crit: dict[str, str] = {}
        for key, text in criteria.items():
            name = str(key)
            line = _scrub_text(str(text))
            if _limit_key(name) or _banned_text(name) or _banned_text(line):
                return None
            crit[name] = line
        if not crit:
            return None
        cleaned["criteria"] = crit
        return cleaned, ("choice", tuple(crit))
    if kind == "noul":
        yes = "Yes, on this state."
        no = "No, on this state."
        if isinstance(criteria, Mapping):
            if criteria.get("true") is not None:
                yes = _scrub_text(str(criteria.get("true")))
            if criteria.get("false") is not None:
                no = _scrub_text(str(criteria.get("false")))
        if _banned_text(yes) or _banned_text(no):
            return None
        cleaned["criteria"] = {"true": yes, "false": no}
        return cleaned, ("noul", _NOUL_ORDER)
    levels: list[str] = []
    if isinstance(criteria, list):
        for item in criteria:
            line = _scrub_text(str(item))
            if _banned_text(line):
                return None
            if line:
                levels.append(line)
    if levels:
        cleaned["criteria"] = levels
    return cleaned, ("score", ())


def _absorb(raw: Any, into: dict[str, Any]) -> None:
    if not isinstance(raw, Mapping):
        return
    for key, block in raw.items():
        name = str(key)
        if name in into or name in _OWN_IDS:
            continue
        into[name] = block


def _external_packs(gold_state: Mapping[str, Any] | None) -> dict[str, Any]:
    """Assembled packs only. A missing pack adds nothing."""

    _bind_card(gold_state)
    assembled = dict(gold_state or {})
    raw: dict[str, Any] = {}
    try:
        from .jev_questions import symbol_fanout_questions

        _absorb(symbol_fanout_questions(), raw)
    except Exception:
        pass
    if _env_on("GTOS_JEV_S14_CALL"):
        try:
            from .regime_system_one import build_question_pack

            _absorb(build_question_pack(sleeve=assembled.get("selected_sleeve_candidate")), raw)
        except Exception:
            pass
    if _env_on("GTOS_JEV_WORLD_CALL") and assembled.get("world"):
        try:
            from .world_questions import world_systemone_payload

            extra = world_systemone_payload(dict(assembled)).get("questions") or {}
            _absorb(extra, raw)
        except Exception:
            pass
    if _env_on("GTOS_JEV_RDF_CALL") and assembled.get("rdf"):
        try:
            from .rdf_questions import rdf_systemone_payload

            extra = rdf_systemone_payload(dict(assembled)).get("questions") or {}
            _absorb(extra, raw)
        except Exception:
            pass
    if _env_on("GTOS_JEV_EVERYWHERE_SHADOW") or _env_on("GTOS_JEV_FLUID_GATES_SHADOW"):
        try:
            from .everywhere import EVERYWHERE_QUESTION_PACK

            _absorb(EVERYWHERE_QUESTION_PACK, raw)
        except Exception:
            pass
    return raw


def _questions(
    gold_state: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, tuple[str, tuple[str, ...]]]]:
    _bind_card(gold_state)
    pack: dict[str, Any] = {}
    catalog: dict[str, tuple[str, tuple[str, ...]]] = {}
    for qid, block in _own_pack().items():
        accepted = _accept(qid, block)
        if accepted is None:
            continue
        pack[qid] = accepted[0]
        catalog[qid] = accepted[1]
    for qid, block in _external_packs(gold_state).items():
        if qid in catalog:
            continue
        accepted = _accept(qid, block)
        if accepted is None:
            continue
        pack[qid] = accepted[0]
        catalog[qid] = accepted[1]
    return pack, catalog


def _questions_id(questions: Mapping[str, Any]) -> str:
    raw = json.dumps(sorted(str(key) for key in questions), separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _number(value)
        if number is not None:
            numeric[str(key)] = number
    return numeric


def _present_unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest among probabilities that were actually returned."""

    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if probabilities[name] == best]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    """The choice is the unique highest probability. A bare label is not a choice."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    probabilities = _probabilities(block)
    if not probabilities or not order:
        return None
    local = _present_unique(probabilities, order)
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probabilities, order)
    except Exception:
        agreed = local
    if local is None or agreed is None or str(agreed) != local:
        return None
    if str(agreed) not in order:
        return None
    return str(agreed)


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A tie is not a Noul."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        value = block.get("noul") if "noul" in block else block.get("Noul")
        if value is None:
            return None
        if value is True or value is False:
            return value
        return _number(value)
    picked = _choice(block, _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any, qid: str | None = None) -> float | None:
    """The parameter is the returned number. It is not snapped to a level."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(block, str(qid))


    if not isinstance(block, dict) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _number(returned_number(block))
    except Exception:
        if "score" in block and block.get("score") is not None:
            return _number(block.get("score"))
        return None


def _read_one(kind: str, block: Any, order: tuple[str, ...], qid: str | None = None) -> Any:
    if kind == "choice":
        return _choice(block, order)
    if kind == "noul":
        return _noul(block)
    return _score(block, qid)


def _miss(block: Any, value: Any, order: tuple[str, ...], err: Any) -> str | None:
    if value is not None:
        return None
    if err not in (None, ""):
        return str(err)
    if isinstance(block, dict) and block.get("error"):
        return str(block.get("error"))
    probabilities = _probabilities(block)
    if probabilities and _present_unique(probabilities, order or tuple(probabilities)) is None:
        return "tie"
    return "empty"


def _view(
    gold_state: Mapping[str, Any] | None,
    merged_answers: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Facts for the ask. Injected answers stay facts. They are not the decision."""

    body = dict(gold_state or {})
    body.pop("prior_outcomes", None)
    injected = _plain(dict(merged_answers or {}))
    payload: dict[str, Any] = {
        "gate_id": GATE_ID,
        "model": MODEL,
        "api_url": API_URL,
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "gold_state": body,
    }
    if injected:
        payload["injected_answers"] = injected
    plain = _plain(payload)
    state = plain if isinstance(plain, dict) else {}
    state.pop("prior_outcomes", None)
    state["model"] = MODEL
    state["api_url"] = API_URL
    return state


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(
    state: Mapping[str, Any],
    rows: list[tuple[str, Any, str | None]],
) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in rows:
            _LOCAL_OUTCOMES.append({
                "key": key,
                "value": value,
                "error": error,
            })
        return
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    """One evaluate. No second client."""

    call = evaluate_fn
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    receipt = call(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    return receipt if isinstance(receipt, dict) else {}


def _shell(error: str | None) -> dict[str, Any]:
    """Unset decisions. Place, broker, news, and label marks belong to the module."""

    row: dict[str, Any] = {
        "gate_id": GATE_ID,
        "posted": False,
        "dark": None,
        "answers": {},
        "answers_source": None,
        "place": False,
        "broker_effect": False,
        "news_invent": False,
        "label_apply": False,
        "challenge_login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "model": MODEL,
        "api_url": API_URL,
        "error": error,
    }
    for field in _TOP_FIELDS:
        row[field] = None
    return row


def _apply_reads(
    row: dict[str, Any],
    catalog: Mapping[str, tuple[str, tuple[str, ...]]],
    answers: Mapping[str, Any],
    err: Any,
) -> list[tuple[str, Any, str | None]]:
    decided: dict[str, Any] = {}
    remembered: list[tuple[str, Any, str | None]] = []
    for qid, (kind, order) in catalog.items():
        block = answers.get(qid)
        value = _read_one(kind, block, order, qid)
        if value is not None:
            decided[qid] = value
        if qid in _TOP_FIELDS:
            row[qid] = value
        remembered.append((qid, value, _miss(block, value, order, err if value is None else None)))
    row["answers"] = decided
    row["dark"] = row.get("cycle_dark")
    row["answers_source"] = "jev_evaluate" if decided else None
    return remembered


def maybe_post_cycle_evaluate(
    gold_state: Mapping[str, Any] | None,
    merged_answers: Mapping[str, Any] | None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
    cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Post one cycle ask. The return is the decision. A cache is not a decision.

    Place, broker effect, invented news, and label apply stay the module's
    own marks. This function does not send.
    """

    _bind_card(gold_state)
    del cache
    forced = evaluate_fn is not None
    if not cycle_call_enabled() and not forced:
        skipped = _shell(None)
        skipped["skipped"] = "cycle_observe_off"
        return skipped

    try:
        questions, catalog = _questions(gold_state)
    except Exception as exc:  # noqa: BLE001 — a failed pack must not raise into the cycle
        return _shell(type(exc).__name__)
    if not questions or any(
        not isinstance(block, dict) or str(block.get("type") or "") not in _ALLOWED
        for block in questions.values()
    ):
        return _shell("question_pack_fail")

    state = _view(gold_state, merged_answers)
    _attach_priors(state, questions)
    try:
        receipt = _post(state, questions, evaluate_fn)
    except Exception as exc:  # noqa: BLE001 — a failed ask leaves the return unset
        row = _shell(type(exc).__name__)
        _remember(state, [(qid, None, type(exc).__name__) for qid in catalog])
        return row

    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and error in (None, ""):
        error = "empty"
    row = _shell(None if error in (None, "") else str(error))
    row["posted"] = True
    row["questions_id"] = _questions_id(questions)
    row["jev"] = {
        "ok": receipt.get("ok"),
        "skipped": receipt.get("skipped"),
        "error": receipt.get("error"),
        "model": receipt.get("model") or MODEL,
        "usage": receipt.get("usage") if isinstance(receipt.get("usage"), dict) else {},
    }
    if not answers:
        _remember(state, [(qid, None, row["error"]) for qid in catalog])
        return row
    remembered = _apply_reads(row, catalog, answers, None)
    if error not in (None, ""):
        row["error"] = str(error)
    else:
        row["error"] = None
    _remember(state, remembered)
    return row
