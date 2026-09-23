"""Fluid gate inventory. The gate class is a fact on the card. The return decides.

Every decision on this state, including every parameter, is the System One
return. One hop: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached on
every ask, and the return is stored for the next ask. An empty answer, a
tie, a missing score, or an error leaves that return unset and does not
restore a constant. A floor and a baseline are not a question.
This module does not send.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.fluid_gates.v1"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
FLUID_INVENTORY_48_REASON = "fluid_inventory_48"

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = REPO_ROOT / "judgment" / "astra" / "JEV_GATE_INVENTORY.json"

_CHOICE_ORDER = ("observe", "keep", "place", "refuse", "stand")
_CHOICE_CRITERIA = {
    "observe": "This inventory state stays an observe.",
    "keep": "This state keeps.",
    "place": "This state opens place.",
    "refuse": "This state refuses the place path.",
    "stand": "This state stands.",
}
_NOUL_ORDER = ("true", "false")
_NOUL_CRITERIA = {
    "true": "Yes, for this state.",
    "false": "No, for this state.",
}
_LEVELS = ("none", "trace", "small", "modest", "notable", "heavy")
_Q_CHOICE = "fluid_gate"
_Q_PLACE = "fluid_place_authorized"
_Q_APPLY = "fluid_auto_apply"
_Q_SHAPE = "fluid_shape_ok"
_Q_EXISTS = "fluid_component_exists"
_Q_THRESHOLD = "fluid_threshold"
_Q_LOOP = "fluid_loop"
_Q_PARAMETER = "fluid_parameter"
_Q_EXPECTED_FLUID = "fluid_expected_fluid"
_Q_EXPECTED_ENVELOPE = "fluid_expected_envelope"
_Q_APPLY_PARAMETER = "fluid_auto_apply_parameter"
_Q_PLACE_PARAMETER = "fluid_place_parameter"
_NOULS = (_Q_PLACE, _Q_APPLY, _Q_SHAPE, _Q_EXISTS)
_SCORES = (
    _Q_THRESHOLD,
    _Q_LOOP,
    _Q_PARAMETER,
    _Q_EXPECTED_FLUID,
    _Q_EXPECTED_ENVELOPE,
    _Q_APPLY_PARAMETER,
    _Q_PLACE_PARAMETER,
)
_PLANTED = frozenset(
    {
        "answer",
        "answers",
        "auto_apply",
        "choice",
        "choice_place_path",
        "component_exists",
        "default",
        "expected_envelope",
        "expected_fluid",
        "noul",
        "ok",
        "parameter",
        "place",
        "place_authorized",
        "probabilities",
        "score",
        "shape_ok",
        "value",
        "verdict",
    }
)
_LIMIT_KEYS = frozenset(
    {
        "baseline",
        "daily_loss_pct",
        "day_start_baseline",
        "floor",
        "floor_room",
        "flatten_floor_usd",
        "pass_line",
        "static_floor",
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
_SCORE_FIELDS = {
    _Q_THRESHOLD: "threshold",
    _Q_LOOP: "loop_bound",
    _Q_PARAMETER: "parameter",
    _Q_EXPECTED_FLUID: "expected_fluid",
    _Q_EXPECTED_ENVELOPE: "expected_envelope",
    _Q_APPLY_PARAMETER: "auto_apply_parameter",
    _Q_PLACE_PARAMETER: "place_parameter",
}

# History only when jev_questions cannot be imported. A miss is not copied back.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


@lru_cache(maxsize=1)

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

def load_inventory() -> dict[str, Any]:
    payload = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JEV_GATE_INVENTORY must be an object")
    return payload


def fluid_gates() -> list[dict[str, Any]]:
    return [g for g in load_inventory().get("fluid") or [] if isinstance(g, dict)]


def envelope_walls() -> list[dict[str, Any]]:
    return [g for g in load_inventory().get("envelope") or [] if isinstance(g, dict)]


def fluid_gate_ids() -> list[str]:
    return [str(g["id"]) for g in fluid_gates() if g.get("id")]


def _wall_ids() -> frozenset[str]:
    """Wall ids from the lock when that module is present.

    A missing lock adds no ids. The class is a fact. It does not skip the ask.
    """

    try:
        from .process_lock import ENVELOPE_WALL_IDS
    except Exception:
        return frozenset()
    if isinstance(ENVELOPE_WALL_IDS, (set, frozenset, list, tuple)):
        return frozenset(str(item) for item in ENVELOPE_WALL_IDS if item is not None)
    return frozenset()


def envelope_ids() -> list[str]:
    named = [str(g["id"]) for g in envelope_walls() if g.get("id")]
    return sorted(set(named) | set(_wall_ids()))


def set_gate_status(gate_id: str, status: str) -> None:
    """Write a gate status when this state's choice is not refuse.

    An empty choice or an error does not write and does not restore a status.
    The gate class is a fact on that ask.
    """

    card = evaluate_fluid_gates(gate_id=gate_id)
    if card.get("error") or card.get("choice") is None or card.get("choice") == "refuse":
        return
    payload = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    found = False
    for key in ("fluid", "envelope"):
        for gate in payload.get(key) or []:
            if isinstance(gate, dict) and gate.get("id") == gate_id:
                gate["status"] = status
                found = True
                break
        if found:
            break
    if not found:
        raise KeyError(gate_id)
    INVENTORY_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    load_inventory.cache_clear()


def lookup(gate_id: str) -> dict[str, Any] | None:
    for gate in fluid_gates():
        if gate.get("id") == gate_id:
            return gate
    for gate in envelope_walls():
        if gate.get("id") == gate_id:
            return gate
    return None


def is_fluid(gate_id: str) -> bool:
    gate = lookup(gate_id)
    return bool(gate and gate.get("class") == "fluid")


def is_envelope(gate_id: str) -> bool:
    if str(gate_id) in _wall_ids():
        return True
    gate = lookup(gate_id)
    return bool(gate and gate.get("class") == "envelope")


def research_only(gate_id: str) -> bool | None:
    """Catalog fact. A missing flag stays unset. This does not ask and does not refuse."""

    gate = lookup(gate_id)
    if not isinstance(gate, Mapping):
        return None
    value = gate.get("research_only")
    if value is True or value is False:
        return value
    return None


def inventory_counts() -> dict[str, int]:
    fluid = fluid_gates()
    families: dict[str, int] = {}
    for gate in fluid:
        fam = str(gate.get("family") or "unknown")
        families[fam] = families.get(fam, 0) + 1
    return {
        "n_fluid": len(fluid),
        "n_envelope": len(envelope_walls()),
        **{f"n_{k}": v for k, v in families.items()},
    }


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
    if token in _LIMIT_KEYS or _text_banned(token):
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
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
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


def _strip_planted(block: dict[str, Any]) -> dict[str, Any]:
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    return block


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
    _strip_planted(body)
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = {
        str(key): str(text)
        for key, text in criteria.items()
        if not _text_banned(str(key)) and not _text_banned(str(text))
    }
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


def fluid_questions() -> dict[str, dict[str, Any]]:
    """One pack. The menu names the return. The return decides."""

    pack: dict[str, dict[str, Any]] = {
        _Q_CHOICE: _choice_question(
            _Q_CHOICE,
            (
                "Fluid inventory for this state. Pick one option. "
                "The unique highest probability is the decision. "
                "An empty answer or a tie leaves the choice unset. "
                "The gate class on this state is a fact. "
                "This ask does not send."
            ),
            _CHOICE_CRITERIA,
        ),
        _Q_PLACE: _noul_question(
            (
                "Is place authorized on this fluid inventory state? "
                "The noul you return is that answer. "
                "An empty noul leaves it unset. "
                "This ask does not send."
            )
        ),
        _Q_APPLY: _noul_question(
            (
                "For the fluid gate on this state, may a later proved shadow apply "
                "without a new chat ritual? "
                "The noul you return is that answer. "
                "An empty noul leaves it unset. "
                "The gate class on this state is a fact. "
                "This ask does not send."
            )
        ),
        _Q_SHAPE: _noul_question(
            (
                "Does this inventory shape hold for this state? "
                "The noul you return is that answer. "
                "An empty noul leaves it unset. "
                "This ask does not send."
            )
        ),
        _Q_EXISTS: _noul_question(
            (
                "Does the fluid-gate component exist on this state? "
                "The noul you return is that existence. "
                "An empty noul leaves existence unset. "
                "This ask does not send."
            )
        ),
        _Q_THRESHOLD: _score_question(
            _Q_THRESHOLD,
            (
                "The score you return is the threshold for this fluid inventory. "
                "It may sit between the levels. "
                "An empty score leaves the threshold unset. "
                "This ask does not send."
            ),
        ),
        _Q_LOOP: _score_question(
            _Q_LOOP,
            (
                "The score you return is the loop bound for this fluid inventory. "
                "It may sit between the levels. "
                "An empty score leaves the bound unset. "
                "This ask does not send."
            ),
        ),
        _Q_PARAMETER: _score_question(
            _Q_PARAMETER,
            (
                "The score you return is the parameter for this fluid inventory. "
                "It may sit between the levels. "
                "An empty score leaves the parameter unset. "
                "This ask does not send."
            ),
        ),
        _Q_EXPECTED_FLUID: _score_question(
            _Q_EXPECTED_FLUID,
            (
                "The score you return is the fluid count for this inventory. "
                "It may sit between the levels. "
                "The measured count on this state is a fact. "
                "An empty score leaves the count unset. "
                "This ask does not send."
            ),
        ),
        _Q_EXPECTED_ENVELOPE: _score_question(
            _Q_EXPECTED_ENVELOPE,
            (
                "The score you return is the envelope count for this inventory. "
                "It may sit between the levels. "
                "The measured count on this state is a fact. "
                "An empty score leaves the count unset. "
                "This ask does not send."
            ),
        ),
        _Q_APPLY_PARAMETER: _score_question(
            _Q_APPLY_PARAMETER,
            (
                "The score you return is the parameter for fluid auto-apply on this state. "
                "It may sit between the levels. "
                "An empty score leaves the parameter unset. "
                "This ask does not send."
            ),
        ),
        _Q_PLACE_PARAMETER: _score_question(
            _Q_PLACE_PARAMETER,
            (
                "The score you return is the parameter for place on this fluid inventory. "
                "It may sit between the levels. "
                "An empty score leaves the parameter unset. "
                "This ask does not send."
            ),
        ),
    }
    for qid, block in list(pack.items()):
        if block.get("type") not in {"noul", "choice", "score"}:
            pack.pop(qid, None)
            continue
        if _text_banned(str(block.get("instructions") or "")):
            pack.pop(qid, None)
    return pack


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
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
    names = order or tuple(numeric)
    seen = False
    for name in names:
        if name not in numeric:
            continue
        seen = True
        prob = numeric[name]
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


def _score_value(raw: Any, qid: str | None = None) -> float | None:
    """Returned score. A missing score stays unset. The number is not snapped."""
    if qid is not None and _is_ordinal(str(qid)):
        return _ordinal_read(raw, str(qid))


    if raw is None or isinstance(raw, bool):
        return None
    if not isinstance(raw, dict):
        return _finite(raw)
    if raw.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        parsed = _finite(returned_number(raw))
        if parsed is not None:
            return parsed
    except Exception:
        pass
    if "score" in raw:
        return _finite(raw.get("score"))
    return None


def _noul_value(raw: Any) -> bool | float | None:
    """A Noul stays a bool or a probability. A missing noul stays missing."""

    if raw is True or raw is False:
        return raw
    if not isinstance(raw, dict):
        return _finite(raw)
    if raw.get("error"):
        return None
    if "noul" in raw:
        value = raw.get("noul")
    elif "Noul" in raw:
        value = raw.get("Noul")
    else:
        value = None
    if value is True or value is False:
        return value
    if value is not None:
        return _finite(value)
    picked = _unique(_probabilities(raw, _NOUL_ORDER), _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _blank(error: str | None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "choice": None,
        "probabilities": {},
        "place_authorized": None,
        "auto_apply": None,
        "shape_ok": None,
        "component_exists": None,
        "expected_fluid": None,
        "expected_envelope": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "auto_apply_parameter": None,
        "place_parameter": None,
        "error": error,
    }


def _read(receipt: Mapping[str, Any]) -> dict[str, Any]:
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    row = _blank(None if error in (None, "") else str(error))
    model = receipt.get("model")
    if isinstance(model, str) and model.strip():
        row["model"] = model.strip()
    if not answers:
        return row
    row["error"] = None
    choice_probs = _probabilities(answers.get(_Q_CHOICE), _CHOICE_ORDER)
    row["probabilities"] = {name: choice_probs[name] for name in _CHOICE_ORDER if name in choice_probs}
    row["choice"] = _unique(choice_probs, _CHOICE_ORDER)
    row["place_authorized"] = _noul_value(answers.get(_Q_PLACE))
    row["auto_apply"] = _noul_value(answers.get(_Q_APPLY))
    row["shape_ok"] = _noul_value(answers.get(_Q_SHAPE))
    row["component_exists"] = _noul_value(answers.get(_Q_EXISTS))
    for qid, field in _SCORE_FIELDS.items():
        row[field] = _score_value(answers.get(qid), qid)
    return row


def _miss(value: Any, kind: str, receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return kind


def _outcome_pairs(row: Mapping[str, Any]) -> tuple[tuple[str, Any, str | None], ...]:
    ask_error = row.get("error") if isinstance(row.get("error"), str) else None
    choice = row.get("choice")
    probs = row.get("probabilities") if isinstance(row.get("probabilities"), Mapping) else {}
    choice_kind = "tie" if probs and choice is None else "empty"
    pairs: list[tuple[str, Any, str | None]] = [
        (_Q_CHOICE, choice, _miss(choice, choice_kind, ask_error)),
        (_Q_PLACE, row.get("place_authorized"), _miss(row.get("place_authorized"), "noul_missing", ask_error)),
        (_Q_APPLY, row.get("auto_apply"), _miss(row.get("auto_apply"), "noul_missing", ask_error)),
        (_Q_SHAPE, row.get("shape_ok"), _miss(row.get("shape_ok"), "noul_missing", ask_error)),
        (
            _Q_EXISTS,
            row.get("component_exists"),
            _miss(row.get("component_exists"), "noul_missing", ask_error),
        ),
    ]
    for qid, field in _SCORE_FIELDS.items():
        value = row.get(field)
        pairs.append((qid, value, _miss(value, "score_missing", ask_error)))
    return tuple(pairs)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        loaded = [dict(item) for item in _LOCAL_OUTCOMES]
    cleaned = _scrub(loaded)
    if cleaned is None:
        cleaned = []
    state["prior_outcomes"] = cleaned


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    pairs = _outcome_pairs(row)
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in pairs:
            _LOCAL_OUTCOMES.append({"spot": key, "value": value, "error": error})
        return
    for key, value, error in pairs:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _questions_ok(questions: Mapping[str, Any]) -> bool:
    allowed = {"noul", "choice", "score"}
    if not questions:
        return False
    for block in questions.values():
        if not isinstance(block, dict) or block.get("type") not in allowed:
            return False
        if _text_banned(str(block.get("instructions") or "")):
            return False
        criteria = block.get("criteria")
        if isinstance(criteria, Mapping):
            for key, text in criteria.items():
                if _text_banned(str(key)) or _text_banned(str(text)):
                    return False
        elif isinstance(criteria, list):
            if any(_text_banned(str(item)) for item in criteria):
                return False
    return True


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    ask: Callable[..., Any] | None,
) -> dict[str, Any]:
    call = ask
    if call is None:
        try:
            from .jev_client import evaluate
        except Exception as exc:
            return {"error": type(exc).__name__, "answers": {}, "model": MODEL}
        call = evaluate
    try:
        receipt = call(state, questions=dict(questions), merge_sleeve=False, model=MODEL)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {"error": type(exc).__name__, "answers": {}, "model": MODEL}
    if not isinstance(receipt, dict):
        return {"error": "evaluate_not_a_dict", "answers": {}, "model": MODEL}
    return receipt


def _measured() -> dict[str, Any] | None:
    try:
        counts = inventory_counts()
        ids = fluid_gate_ids()
        dupes = [item for item in ids if ids.count(item) > 1]
        walls = envelope_ids()
    except Exception:
        return None
    return {
        "counts": counts,
        "duplicate_ids": sorted(set(dupes)),
        "envelope_ids": walls,
    }


def _lock_facts() -> dict[str, Any]:
    try:
        from .process_lock import FORBIDDEN_AUTO_EFFECTS, PREAUTH_EFFECTS
    except Exception:
        return {}
    out: dict[str, Any] = {}
    for name, raw in (
        ("preauth_effects", PREAUTH_EFFECTS),
        ("forbidden_auto_effects", FORBIDDEN_AUTO_EFFECTS),
    ):
        if isinstance(raw, (set, frozenset, list, tuple)):
            out[name] = sorted(str(item) for item in raw)
    return out


def _gate_facts(gate: Mapping[str, Any] | None, gate_id: str | None) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    if gate_id:
        facts["gate_id"] = str(gate_id)
    if not isinstance(gate, Mapping):
        return facts
    for key, value in gate.items():
        name = str(key)
        if name in _PLANTED:
            continue
        facts[name] = value
    if gate.get("id") is not None:
        facts["gate_id"] = str(gate.get("id"))
    return facts


def _build_state(
    gate: Mapping[str, Any] | None,
    gate_id: str | None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema": SCHEMA,
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "reason": FLUID_INVENTORY_48_REASON,
    }
    measured = _measured()
    if isinstance(measured, dict):
        counts = measured.get("counts")
        if isinstance(counts, Mapping):
            state["counts"] = dict(counts)
        state["duplicate_ids"] = list(measured.get("duplicate_ids") or [])
        state["envelope_ids"] = list(measured.get("envelope_ids") or [])
    gate_facts = _gate_facts(gate, gate_id)
    if gate_facts:
        state["gate"] = gate_facts
    lock_facts = _lock_facts()
    if lock_facts:
        state["lock"] = lock_facts
    scrubbed = _scrub(state)
    return scrubbed if isinstance(scrubbed, dict) else {"schema": SCHEMA, "model": MODEL}


def _gate_row(gate: Any) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(gate, str):
        try:
            row = lookup(gate)
        except Exception:
            return None, gate
        if isinstance(row, dict):
            gid = row.get("id")
            return row, gate if gid is None else str(gid)
        return None, gate
    if isinstance(gate, Mapping):
        gid = gate.get("id")
        copied = dict(gate)
        return copied, None if gid is None else str(gid)
    return None, None


def _row_is_wall(row: Mapping[str, Any] | None, gate_id: str | None) -> bool:
    if gate_id and str(gate_id) in _wall_ids():
        return True
    return bool(isinstance(row, Mapping) and row.get("class") == "envelope")


def evaluate_fluid_gates(
    gate: Mapping[str, Any] | None = None,
    *,
    gate_id: str | None = None,
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One System One ask. Each field is that return, or unset."""

    try:
        questions = fluid_questions()
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        row = _blank(type(exc).__name__)
        _remember({"schema": SCHEMA, "model": MODEL}, row)
        return row
    if not _questions_ok(questions):
        row = _blank("question_pack_fail")
        _remember({"schema": SCHEMA, "model": MODEL}, row)
        return row
    state = _build_state(gate, gate_id)
    state["model"] = MODEL
    _attach_priors(state, questions)
    receipt = _post(state, questions, ask)
    row = _read(receipt)
    _remember(state, row)
    return row


def auto_apply_eligible(gate: Mapping[str, Any] | str) -> bool | float | None:
    """Auto-apply noul for this fluid gate. A miss stays unset.

    An envelope wall is not asked. This function does not send.
    """

    row, gid = _gate_row(gate)
    return evaluate_fluid_gates(row, gate_id=gid).get("auto_apply")


def assert_inventory_shape() -> dict[str, Any]:
    """Measured inventory facts, plus the shape, place, and count returns."""

    card = evaluate_fluid_gates()
    measured = _measured()
    out: dict[str, Any] = {
        "expected_fluid": card.get("expected_fluid"),
        "expected_envelope": card.get("expected_envelope"),
        "ok": card.get("shape_ok"),
        "place_authorized": card.get("place_authorized"),
        "dig_b_fluid_inventory_48": card.get("choice"),
        "threshold": card.get("threshold"),
        "loop_bound": card.get("loop_bound"),
        "parameter": card.get("parameter"),
        "component_exists": card.get("component_exists"),
        "error": card.get("error"),
    }
    if not isinstance(measured, dict):
        out["duplicate_ids"] = None
        out["envelope_ids"] = None
        return out
    counts = measured.get("counts")
    if isinstance(counts, Mapping):
        out.update(dict(counts))
    out["duplicate_ids"] = list(measured.get("duplicate_ids") or [])
    out["envelope_ids"] = list(measured.get("envelope_ids") or [])
    return out


def fluid_inventory_48_place_authorized() -> bool | float | None:
    """Place noul for this inventory. A miss stays unset. This does not send."""

    return evaluate_fluid_gates()["place_authorized"]


def apply_fluid_inventory_48(*_args: object, **_kwargs: object) -> None:
    """Refuse the place path only when the choice returns refuse.

    A miss does not raise and does not restore a verdict. This module does not send.
    """

    choice = evaluate_fluid_gates().get("choice")
    if choice != "refuse":
        return
    try:
        from .dig_b_static import refuse_apply_killed
    except Exception:
        return
    refuse_apply_killed(FLUID_INVENTORY_48_REASON)


def consume_fluid_inventory_48() -> dict[str, Any]:
    """Consume view of this ask. A miss does not fill a verdict or a place flag."""

    card = evaluate_fluid_gates()
    choice = card.get("choice")
    place = card.get("place_authorized")
    out: dict[str, Any] = {
        "reason": FLUID_INVENTORY_48_REASON,
        "kind": choice,
        "place": place,
        "choice_place_path": choice,
        "parameter": card.get("parameter"),
        "threshold": card.get("threshold"),
        "loop_bound": card.get("loop_bound"),
        "expected_fluid": card.get("expected_fluid"),
        "expected_envelope": card.get("expected_envelope"),
        "error": card.get("error"),
    }
    if choice is None and place is None:
        return out
    try:
        from .dig_b_static import consume_row
    except Exception:
        return out
    kwargs: dict[str, Any] = {}
    if choice is not None:
        kwargs["kind"] = choice
        kwargs["choice_place_path"] = choice
    if place is not None:
        kwargs["place"] = place
    try:
        consumed = consume_row(FLUID_INVENTORY_48_REASON, **kwargs)
    except Exception:
        return out
    return consumed if isinstance(consumed, dict) else out
