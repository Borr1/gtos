"""Challenge skip sites ask System One. A constant does not decide them.

One hop per site: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
The return is a Noul, a Choice, or a Score. Those are the choice, the
threshold, the loop bound, the parameter, and which component exists.
A candidate passes watch, observe, admit, and place. A ticket passes those
and every manage step for the whole life. The returns decide. Prior outcomes
are on every ask, and the return is appended for the next ask.

An empty answer, a tie, a missing score, or an error leaves that return
unset and does not restore a constant. This module does not send an order.
``book_owner.py`` is not edited. The wraps are how a constant skip stops
being the decision.
"""

from __future__ import annotations

import json
import linecache
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.skip_choices.v1"

_FUNCTION_ORDER = ("returned_score", "last_outcome", "withhold")
_BRANCH_ORDER = ("take", "skip")
_LIFE_ORDER = ("pass", "withhold")
_CANDIDATE_LIFE = ("life_watch", "life_observe", "life_admit", "life_place")
_MANAGE_LIFE = (
    "life_move_sl",
    "life_move_tp",
    "life_close",
    "life_hold",
    "life_remove",
)
_LIFE_STEPS = _CANDIDATE_LIFE + _MANAGE_LIFE
_TICKET_SKIPS = frozenset({"same_broker_symbol_open_position_lifecycle_guard"})
_BANNED_AMOUNT = (90000.0, 110000.0)
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
_LEVEL_SKIP = (
    "floor",
    "baseline",
    "equity",
    "balance",
    "drawdown",
    "profit_target",
    "max_loss",
    "daily_loss",
    "kill",
    "ticket",
    "unit",
    "persist",
    "login",
    "to_pass",
    "floor_room",
    "prior_outcomes",
)

# The option named ``skip`` is the one that keeps the old skip. It is not a default.
SPECS: dict[str, dict[str, Any]] = {
    "fx_dsp_dropped_j6": {
        "order": ("pattern_is_the_fire", "pattern_absent"),
        "skip": "pattern_absent",
        "instructions": (
            "A DSP sleeve printed on this symbol. "
            "`in_drop_set` is a fact on this state, not a ban. "
            "Is this bar's pattern the fire, or is the pattern absent? "
            "The option you return is that choice. "
            "An empty answer or a tie is not a decision."
        ),
        "criteria": {
            "pattern_is_the_fire": "This sleeve's pattern on this symbol is the fire on this bar.",
            "pattern_absent": "The pattern this sleeve requires is not on this bar.",
        },
    },
    "already_placed_today": {
        "order": ("later_bar_is_the_fire", "one_fill_is_enough"),
        "skip": "one_fill_is_enough",
        "instructions": (
            "This sleeve and symbol already filled once on the decision day. "
            "Is a later bar still the fire, or is one fill enough for today? "
            "The option you return is that choice. "
            "An empty answer or a tie is not a decision."
        ),
        "criteria": {
            "later_bar_is_the_fire": "A later bar of this sleeve and symbol is still the fire.",
            "one_fill_is_enough": "One fill of this sleeve and symbol today is enough.",
        },
    },
    "stale_late_entry_after_restart": {
        "order": ("still_the_close", "restart_chase"),
        "skip": "restart_chase",
        "instructions": (
            "The decision bar has closed. The minutes past the close are a fact. "
            "Is this order still that bar's close, or a restart chase of a price "
            "the pattern did not enter? "
            "The option you return is that choice. "
            "An empty answer or a tie is not a decision."
        ),
        "criteria": {
            "still_the_close": "The order is still this bar's close.",
            "restart_chase": "This is a restart chase of a price the pattern did not enter.",
        },
    },
    "judgment_hold": {
        "order": ("send_continues", "hold_stands"),
        "skip": "hold_stands",
        "instructions": (
            "A flow row on this sleeve and symbol carries an action and a reason. "
            "Does the send continue, or does that row stand? "
            "The option you return is that choice. "
            "An empty answer or a tie is not a decision."
        ),
        "criteria": {
            "send_continues": "The send continues. The flow row is not a ban.",
            "hold_stands": "That flow row stands.",
        },
    },
    "same_broker_symbol_open_position_lifecycle_guard": {
        "order": ("second_thesis_on_this_symbol", "keep_open_ticket"),
        "skip": "keep_open_ticket",
        "instructions": (
            "A position is already open on this broker symbol. "
            "This candidate is another sleeve. "
            "Is this candidate a second thesis on the symbol, or does the open ticket stay alone? "
            "The option you return is that choice. "
            "An empty answer or a tie is not a decision. "
            "Leaving the open ticket alone does not close it."
        ),
        "criteria": {
            "second_thesis_on_this_symbol": (
                "This candidate is a second thesis on this symbol. Leave the open ticket alone."
            ),
            "keep_open_ticket": "The open ticket stays alone. Do not send this candidate.",
        },
    },
    "same_broker_symbol_already_placed_this_cycle": {
        "order": ("sibling_is_a_new_send", "cycle_already_sent"),
        "skip": "cycle_already_sent",
        "instructions": (
            "This cycle already sent this broker symbol. Another sleeve wants the same symbol. "
            "Is the sibling a new send, or has this cycle already sent the symbol? "
            "The option you return is that choice. "
            "An empty answer or a tie is not a decision."
        ),
        "criteria": {
            "sibling_is_a_new_send": "The sibling sleeve is a new send on this symbol this cycle.",
            "cycle_already_sent": "This cycle already sent this symbol.",
        },
    },
    "fx_dsp_stop_le_8pip": {
        "order": ("stop_is_the_plan", "stop_on_the_cliff"),
        "skip": "stop_on_the_cliff",
        "instructions": (
            "This DSP stop width is a fact on this state. "
            "Is this stop the plan, or is the cliff the decision? "
            "The threshold is the score on skip_threshold. It may sit between the levels. "
            "The option you return is that choice. "
            "An empty answer or a tie is not a decision."
        ),
        "criteria": {
            "stop_is_the_plan": "This stop width is the plan for this bar.",
            "stop_on_the_cliff": "This stop sits on the cliff.",
        },
    },
}

_LIFE_TEXT = {
    "life_watch": "Does this candidate pass watch? An open ticket passes watch for the whole life too.",
    "life_observe": "Does this candidate pass observe? An open ticket passes observe for the whole life too.",
    "life_admit": "Does this candidate pass admit? An open ticket passes admit for the whole life too.",
    "life_place": "Does this candidate pass place? An open ticket passes place for the whole life too.",
    "life_move_sl": "Does this ticket pass the stop-modify step for the whole life?",
    "life_move_tp": "Does this ticket pass the target-modify step for the whole life?",
    "life_close": "Does this ticket pass the close step for the whole life?",
    "life_hold": "Does this ticket pass the hold step for the whole life?",
    "life_remove": "Does this ticket pass the pending-remove step for the whole life?",
}

_LOCK = threading.Lock()
_CACHE: dict[tuple[Any, ...], tuple[float, dict[str, Any]]] = {}
_INSTALLED = False
_ORIG_KEYS = None
_ORIG_FX = None
_ORIG_TODAY = None
_ORIG_LATE = None
_ORIG_HOLD = None
_ORIG_EXPOSURES = None



import threading as _anchor_threading

_ANCHOR_CARD = _anchor_threading.local()


def _anchor_finite(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _is_map(value):
    if isinstance(value, dict):
        return True
    if isinstance(value, (str, bytes)):
        return False
    try:
        from collections.abc import Mapping
    except Exception:
        return False
    return isinstance(value, Mapping)


def _bind_card(card):
    _ANCHOR_CARD.value = card if _is_map(card) else None


def _bound_card(explicit):
    if _is_map(explicit):
        return explicit
    bound = getattr(_ANCHOR_CARD, "value", None)
    return bound if _is_map(bound) else None


def _anchor_sources(card):
    if not _is_map(card):
        return []
    found = [card]
    for key in ("account", "facts", "pair", "news", "ticket", "proposed", "extra", "labels", "subject_facts", "candidate"):
        inner = card.get(key)
        if _is_map(inner) and inner is not card:
            found.append(inner)
    return found


_COUNT_FIELDS = (
    "n_candidates", "n_events", "n_sleeves", "n_bars", "bars_available",
    "repeats", "session_bars", "day_bars", "swing_bars", "bars_since_high",
    "bars_since_low", "candles_elapsed", "closed_orig_stop_count",
)
_COUNT_SEQS = (
    "prior_outcomes", "candidates", "events", "sleeve_members", "lengths",
    "stamps", "hashes", "bars", "bar_times", "members", "closed",
    "legacy_symbol_keys", "families", "priors",
)
_PRICE_FIELDS = (
    "bid", "ask", "entry", "entry_price", "stop", "stop_loss", "sl", "tp",
    "take_profit", "price", "high", "low", "close", "open", "orig_sl", "orig_tp",
    "stop_now", "target", "trail", "fill_price", "exit_px",
)
_SECOND_FIELDS = (
    "seconds_until_cycle", "seconds_until_now", "age_s", "age_seconds",
    "seconds_since_quote", "seconds_since_bar", "seconds_since_last_close",
    "seconds_between_closes", "seconds_since_prior_close", "expiry_seconds",
    "timeout_seconds",
)
_MINUTE_FIELDS = (
    "minutes_since_flat", "age_minutes", "minutes_until_now", "window_minutes",
)
_HOUR_FIELDS = ("age_hours", "lag_hours", "hours_since_bar", "hours_open", "measured_hours")
_DAY_FIELDS = ("age_days", "lag_days", "days_open", "measured_days")
_LOT_FIELDS = (
    "volume", "volume_min", "volume_step", "lots", "lot",
    "volume_current", "volume_initial",
)
_POINT_FIELDS = (
    "spread_points", "stop_level", "freeze_level", "tick_points", "deviation_points",
)
_INCLUDE_WORDS = ("hide", "short", "long", "full")


def _named_pairs(card, fields, seqs=()):
    pairs = []
    for source in _anchor_sources(card):
        for key in fields:
            number = _anchor_finite(source.get(key))
            if number is None:
                continue
            pairs.append((f"the {key} named on this card", number))
        for key in seqs:
            seq = source.get(key)
            if isinstance(seq, (list, tuple)) and not isinstance(seq, (str, bytes)):
                pairs.append((f"the count of {key} named on this card", float(len(seq))))
    return pairs


def _keys_matching(card, tokens):
    pairs = []

    def walk(node):
        if _is_map(node):
            for key, value in node.items():
                low = str(key).lower()
                if "floor" in low or "baseline" in low:
                    continue
                number = _anchor_finite(value)
                if number is not None and any(tok in low for tok in tokens):
                    pairs.append((f"the {low} named on this card", number))
                    continue
                if _is_map(value):
                    walk(value)
                elif isinstance(value, list):
                    for item in value:
                        if _is_map(item):
                            walk(item)

    walk(card)
    return pairs


def _anchors_for_spot(qid, card):
    name = str(qid).lower()
    try:
        from .jev_questions import count_anchors, minute_anchors, mult_anchors, usd_anchors, weight_anchors
    except Exception:
        def count_anchors(_card):
            return []

        def minute_anchors(_card):
            return []

        def mult_anchors(_card):
            return []

        def usd_anchors(_card):
            return []

        def weight_anchors(_card):
            return []

    override = globals().get("_UNIT_OVERRIDE")
    if isinstance(override, dict):
        base = name[: -len("_parameter")] if name.endswith("_parameter") else name
        spec = override.get(base)
        if spec == "weight":
            return list(weight_anchors(card) or [])
        if spec == "count":
            pairs = list(count_anchors(card) or [])
            pairs.extend(_named_pairs(card, _COUNT_FIELDS, _COUNT_SEQS))
            return pairs
        if isinstance(spec, tuple):
            return _named_pairs(card, spec)
    if any(tok in name for tok in ("loop", "splice", "width", "lookback", "bound", "_cap")):
        pairs = list(count_anchors(card) or [])
        pairs.extend(_named_pairs(card, _COUNT_FIELDS, _COUNT_SEQS))
        return pairs
    if "ac60" in name or "autocorr" in name:
        return _keys_matching(card, ("ac60", "autocorr"))
    if "direction" in name:
        return _keys_matching(card, ("direction",))
    if name.endswith("_r") or "mfe" in name or "mae" in name:
        return list(weight_anchors(card) or [])
    if "hour" in name:
        return _named_pairs(card, _HOUR_FIELDS)
    if "minute" in name:
        pairs = list(minute_anchors(card) or [])
        pairs.extend(_named_pairs(card, _MINUTE_FIELDS))
        return pairs
    if "day" in name and "today" not in name:
        return _named_pairs(card, _DAY_FIELDS)
    if any(tok in name for tok in ("second", "expiry", "timeout", "pause", "adopt_wait")):
        return _named_pairs(card, _SECOND_FIELDS)
    if any(tok in name for tok in ("tilt", "alignment", "weight", "persist")):
        pairs = list(weight_anchors(card) or [])
        if len(pairs) >= 2:
            return pairs
        return list(mult_anchors(card) or [])
    if any(tok in name for tok in ("lot", "volume")):
        return _named_pairs(card, _LOT_FIELDS)
    if "scale" in name:
        return _scale_pairs(card)
    if any(tok in name for tok in ("price",)) or name in {"manage_sl_price", "manage_tp_price"}:
        return _named_pairs(card, _PRICE_FIELDS)
    if "point" in name or "deviation" in name:
        return _named_pairs(card, _POINT_FIELDS)
    if "spread" in name:
        return _named_pairs(card, ("spread", "spread_points"))
    if any(tok in name for tok in ("usd", "equity", "pnl", "cash")):
        return list(usd_anchors(card) or [])
    return []


def _scale_pairs(card):
    pairs = []
    for source in _anchor_sources(card):
        volume = _anchor_finite(source.get("volume"))
        if volume is None:
            volume = _anchor_finite(source.get("volume_current"))
        initial = _anchor_finite(source.get("volume_initial"))
        least = _anchor_finite(source.get("volume_min"))
        step = _anchor_finite(source.get("volume_step"))
        if volume not in (None, 0) and least is not None:
            pairs.append(("minimum volume over this volume", least / volume))
        if volume not in (None, 0) and step is not None:
            pairs.append(("volume step over this volume", step / volume))
        if initial not in (None, 0) and volume is not None:
            pairs.append(("current volume over initial volume", volume / initial))
    return pairs


def _amount_block(qid, instructions, card):
    """Amount Score. Fewer than two anchors in this unit does not post."""

    source = _bound_card(card)
    try:
        from .jev_questions import amount_question

        built = amount_question(qid, instructions, _anchors_for_spot(qid, source))
    except Exception:
        return {}
    if not isinstance(built, dict):
        return {}
    row = built.get(str(qid))
    if not isinstance(row, dict):
        return {}
    criteria = row.get("criteria")
    if not isinstance(criteria, list) or len(criteria) < 2:
        return {}
    block = dict(row)
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    block["type"] = "score"
    block["instructions"] = instructions
    return {str(qid): block}


def _ordinal_block(qid, instructions, words):
    """Word levels. Fewer than two words does not post. The index is not an amount."""

    try:
        from .jev_questions import ordinal_question

        built = ordinal_question(qid, instructions, words)
    except Exception:
        return {}
    if not isinstance(built, dict):
        return {}
    row = built.get(str(qid))
    if not isinstance(row, dict):
        return {}
    criteria = row.get("criteria")
    if not isinstance(criteria, list) or len(criteria) < 2:
        return {}
    block = dict(row)
    block["type"] = "score"
    block["instructions"] = instructions
    return {str(qid): block}


def _score_amount_or_ordinal(qid, instructions, card=None, *_rest):
    if str(qid).startswith("include_"):
        return _ordinal_block(qid, instructions, _INCLUDE_WORDS)
    return _amount_block(qid, instructions, card)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def record_path() -> Path:
    override = (os.environ.get("GTOS_SKIP_CHOICES_RECORD") or "").strip()
    if override:
        return Path(override)
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / CHALLENGE_NS
        / "judgment"
        / "skip_choices.jsonl"
    )


def _is_challenge(obj: Any) -> bool:
    return str(getattr(obj, "_namespace", "") or "") == CHALLENGE_NS


def _caller_self(depth: int = 2) -> Any:
    frame = sys._getframe(depth)
    return frame.f_locals.get("self")


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


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _append(path: Path, row: Mapping[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(dict(row)), sort_keys=True) + "\n")
    except OSError:
        return


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    """Present finite probabilities only. A missing name is not zero."""

    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        return {}
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _number(val)
        if number is None:
            continue
        numeric[name] = number
    return numeric


def highest_probability(probabilities: Mapping[str, Any], order: tuple[str, ...]) -> str | None:
    """Unique argmax. A tie returns None. A missing probability is not zero."""

    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in order:
        if name not in probabilities or probabilities.get(name) is None:
            continue
        number = _number(probabilities.get(name))
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
        return None
    return best


def _choice_of(block: Any, order: tuple[str, ...]) -> dict[str, Any]:
    """Unique highest probability. A bare label, a tie, or an empty block is not a decision."""

    numeric = _probabilities(block, order)
    local = highest_probability(numeric, order) if numeric else None
    picked = local
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(numeric or None, order)
        # A different name is not a unique decision. None does not erase one.
        if agreed is not None and agreed != local:
            picked = None
    except Exception:
        picked = local
    if picked not in numeric:
        picked = None
    if picked is None:
        return {
            "choice": None,
            "probabilities": numeric,
            "unique_highest": False,
            "probability": None,
        }
    return {
        "choice": picked,
        "probabilities": numeric,
        "unique_highest": True,
        "probability": numeric.get(picked),
    }


def _returned_score(block: Any) -> float | None:
    """The score the model returned. Not snapped to a level. Missing stays missing."""

    number = None
    try:
        from .jev_questions import returned_number

        got = returned_number(block)
        if isinstance(got, (int, float)) and not isinstance(got, bool) and got == got:
            number = float(got)
    except Exception:
        number = None
    if number is not None and number not in (float("inf"), float("-inf")):
        return number
    if not isinstance(block, dict):
        return None
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _number(raw)


def _noul_value(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A float is not turned into a threshold."""

    if not isinstance(block, dict) or "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _number(raw)


def _scrub_amount(value: Any) -> Any:
    """The old equity amounts do not ride into the ask and do not become a level."""

    if isinstance(value, dict):
        return {str(key): _scrub_amount(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub_amount(item) for item in value]
    if isinstance(value, str):
        cleaned = value
        for token in _BANNED_TEXT:
            cleaned = cleaned.replace(token, "")
        return cleaned
    number = _number(value)
    if number is not None and number in _BANNED_AMOUNT:
        return None
    return value


def _exists(value: bool | float | None) -> bool | None:
    """Only an actual bool says whether the component exists."""

    if value is True or value is False:
        return value
    return None


def _last_logged(key: str) -> float | None:
    try:
        from .jev_questions import last_logged_value
    except Exception:
        return None
    try:
        return _number(last_logged_value(key))
    except Exception:
        return None


def _levels(facts: Mapping[str, Any]) -> list[str]:
    """Numeric facts already on this state. A score may sit between them."""

    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        low = key.lower()
        if any(part in low for part in _LEVEL_SKIP):
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(str(child_key), child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            for item in value:
                if isinstance(item, Mapping):
                    for child_key, child in item.items():
                        walk(str(child_key), child)
                else:
                    walk(key, item)
            return
        number = _number(value)
        if number is not None and number not in _BANNED_AMOUNT:
            found.append(number)

    for key, value in dict(facts).items():
        walk(str(key), value)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    block: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(value) for key, value in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(block["criteria"]))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            block = dict(row)
    except Exception:
        pass
    block["type"] = "choice"
    block["instructions"] = instructions
    block["criteria"] = {str(key): str(value) for key, value in criteria.items()}
    return {qid: block}



def _score_question(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "This component exists on this state.",
                "false": "This component does not exist on this state.",
            },
        }
    }


def _component_criteria() -> dict[str, str]:
    return {name: f"{name} exists on this state." for name in SPECS}


def questions_for(skip: str, levels: list[str] | None = None) -> dict[str, Any]:
    """Choice, Score, and Noul for this skip. No other question type."""

    spec = SPECS[skip]
    scale = list(levels or [])
    pack: dict[str, Any] = {}
    pack.update(_choice_question(skip, spec["instructions"], spec["criteria"]))
    pack.update(_choice_question(
        "which_component",
        "Which component exists on this state? "
        "The name you return is that component. "
        "An empty answer or a tie is not a decision.",
        _component_criteria(),
    ))
    pack.update(_noul_question(
        "component_exists",
        "Does the component named on this state exist? "
        "A missing noul leaves existence unset.",
    ))
    pack.update(_choice_question(
        "skip_function",
        "Which function returns the threshold, the loop bound, and the parameter on this state? "
        "The name you return is the function that runs. "
        "Do not name a number.",
        {
            "returned_score": "The function is the score hop. Its return is the threshold, the loop bound, and the parameter.",
            "last_outcome": "The function reads the previous returned threshold, loop bound, and parameter and returns those.",
            "withhold": "The function returns no threshold, no loop bound, and no parameter.",
        },
    ))
    pack.update(_choice_question(
        "skip_if",
        "Does this state take the branch that returns the threshold, the loop bound, and the parameter? "
        "The name you return is the branch.",
        {
            "take": "Take the branch. The named function returns the threshold, the loop bound, and the parameter.",
            "skip": "Do not take the branch. The threshold, the loop bound, and the parameter stay unset.",
        },
    ))
    pack.update(_score_question(
        "skip_threshold",
        "The score you return is the threshold on this state. "
        "It may sit between the levels. "
        "An empty score leaves the threshold unset.",
        scale,
    ))
    pack.update(_score_question(
        "skip_loop",
        "How far does this state read prior returned skip outcomes? "
        "The score you return is that bound. "
        "It may sit between the levels. "
        "An empty score leaves the bound unset.",
        scale,
    ))
    pack.update(_score_question(
        "skip_parameter",
        "The score you return is the parameter on this state. "
        "It may sit between the levels. "
        "An empty score leaves the parameter unset.",
        scale,
    ))
    life_criteria = {
        "pass": "This candidate or ticket passes this step.",
        "withhold": "This step does not pass.",
    }
    for qid in _LIFE_STEPS:
        pack.update(_choice_question(
            qid,
            _LIFE_TEXT[qid] + " The option you return is that decision. "
            "An empty answer or a tie is not a decision.",
            life_criteria,
        ))
    for block in pack.values():
        if str(block.get("type")) not in {"noul", "choice", "score"}:
            block["type"] = "choice"
    return pack


def _relevant_life(skip: str) -> tuple[str, ...]:
    if skip in _TICKET_SKIPS:
        return _LIFE_STEPS
    return _CANDIDATE_LIFE


def _authorized_block(
    skip: str,
    choice: str | None,
    exists: bool | None,
    which: str | None,
    life: Mapping[str, str | None],
) -> bool:
    """The skip stands only when the returns say so.

    A missing component, a tie, or an empty life does not restore the skip.
    When a relevant life step returns pass and none returns withhold, the
    candidate or the ticket passes. A withhold is their decision to stop
    that step.
    """

    if exists is not True or which != skip:
        return False
    saw_pass = False
    for key in _relevant_life(skip):
        decision = life.get(key)
        if decision == "withhold":
            return True
        if decision == "pass":
            saw_pass = True
    if saw_pass:
        return False
    return choice == SPECS[skip]["skip"]


def _applied_numbers(
    function_name: str | None,
    branch: str | None,
    threshold_score: float | None,
    loop_score: float | None,
    parameter_score: float | None,
) -> tuple[float | None, float | None, float | None]:
    """Run the function and the branch. Withhold and skip leave the numbers unset."""

    if function_name == "withhold" or branch == "skip":
        return None, None, None
    if function_name == "last_outcome" and branch == "take":
        return (
            _last_logged("skip_threshold"),
            _last_logged("skip_loop"),
            _last_logged("skip_parameter"),
        )
    return threshold_score, loop_score, parameter_score


def _any_probability(answers: Mapping[str, Any]) -> bool:
    for block in answers.values():
        if not isinstance(block, dict) or not isinstance(block.get("probabilities"), dict):
            continue
        if any(_number(value) is not None for value in block["probabilities"].values()):
            return True
    return False


def _answers_of(hop: Mapping[str, Any]) -> dict[str, Any]:
    answers = hop.get("answers")
    if isinstance(answers, dict):
        return answers
    return {}


def _base(skip: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "logged_at_utc": _now(),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "skip": skip,
        "model": MODEL,
        "choice": None,
        "probability": None,
        "probabilities": {},
        "which_component": None,
        "component_exists": None,
        "noul": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "returned_threshold": None,
        "returned_loop_bound": None,
        "returned_parameter": None,
        "skip_function": None,
        "skip_if": None,
        "life": {step: None for step in _LIFE_STEPS},
        "blocks": False,
        "decision_emitted": False,
        "agent_order_send": False,
        "error": None,
    }


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    err = row.get("error")
    life = row.get("life") if isinstance(row.get("life"), dict) else {}
    pairs: list[tuple[str, Any, bool]] = [
        (str(row.get("skip")), row.get("choice"), row.get("choice") is None),
        ("which_component", row.get("which_component"), row.get("which_component") is None),
        ("component_exists", row.get("component_exists"), row.get("component_exists") is None),
        ("skip_function", row.get("skip_function"), row.get("skip_function") is None),
        ("skip_if", row.get("skip_if"), row.get("skip_if") is None),
        ("skip_threshold", row.get("threshold"), row.get("threshold") is None),
        ("skip_loop", row.get("loop_bound"), row.get("loop_bound") is None),
        ("skip_parameter", row.get("parameter"), row.get("parameter") is None),
    ]
    for step in _LIFE_STEPS:
        pairs.append((step, life.get(step), life.get(step) is None))
    for key, value, failed in pairs:
        try:
            append_outcome(key, value, state, error=err if failed else None)
        except Exception:
            return


def decide(
    skip: str,
    state: Mapping[str, Any] | None = None,
    *,
    cache_key: str,
    ask: Callable[..., dict[str, Any]] | None = None,
    use_cache: bool = True,
    record: bool = True,
    record_to: Path | None = None,
) -> dict[str, Any]:
    """Ask System One for this skip. Never raises. Never sends an order.

    ``choice``, ``threshold``, ``loop_bound``, ``parameter``, and
    ``which_component`` stay unset when the answer is empty, tied, or in error.
    ``blocks`` is true only when those returns keep the skip.
    """

    row = _base(skip if skip in SPECS else str(skip))
    if skip not in SPECS:
        row["error"] = "unknown_skip"
        row["blocks"] = None
        return row
    facts = dict(state or {})
    del cache_key
    levels = _levels(facts)
    _bind_card(facts)
    try:
        questions = questions_for(skip, levels)
    except Exception as exc:  # noqa: BLE001 — a skip ask must not raise into the writer
        _bind_card(None)
        row["error"] = type(exc).__name__
        return row
    _bind_card(None)
    posted = _scrub_amount({
        **{k: v for k, v in facts.items() if k != "prior_outcomes"},
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "model": MODEL,
        "skip": skip,
        "component": skip,
        "facts": {k: v for k, v in facts.items() if k != "prior_outcomes"},
        "levels": levels,
    })
    try:
        from .jev_questions import prior_outcomes

        posted["prior_outcomes"] = prior_outcomes(state=posted, questions=questions)
    except Exception:
        posted["prior_outcomes"] = []
    if posted.get("prior_outcomes") is None:
        posted["prior_outcomes"] = []
    try:
        call = ask
        if call is None:
            from .jev_client import evaluate

            call = evaluate
        hop = call(
            posted,
            questions=questions,
            merge_sleeve=False,
        ) or {}
    except Exception as exc:  # noqa: BLE001 — a skip ask must not raise into the writer
        hop = {"error": type(exc).__name__}
    if not isinstance(hop, dict):
        hop = {"error": "evaluate_not_a_dict"}
    if hop.get("model"):
        row["model"] = hop.get("model")
    answers = _answers_of(hop)
    site = _choice_of(answers.get(skip), tuple(SPECS[skip]["order"]))
    which = _choice_of(answers.get("which_component"), tuple(SPECS))
    function_pick = _choice_of(answers.get("skip_function"), _FUNCTION_ORDER)
    branch_pick = _choice_of(answers.get("skip_if"), _BRANCH_ORDER)
    noul = _noul_value(answers.get("component_exists"))
    exists = _exists(noul)
    threshold_score = _returned_score(answers.get("skip_threshold"))
    loop_score = _returned_score(answers.get("skip_loop"))
    parameter_score = _returned_score(answers.get("skip_parameter"))
    threshold, loop_bound, parameter = _applied_numbers(
        function_pick["choice"],
        branch_pick["choice"],
        threshold_score,
        loop_score,
        parameter_score,
    )
    life: dict[str, str | None] = {}
    for step in _LIFE_STEPS:
        life[step] = _choice_of(answers.get(step), _LIFE_ORDER)["choice"]
    row["choice"] = site["choice"]
    row["probability"] = site["probability"]
    row["probabilities"] = site["probabilities"]
    row["which_component"] = which["choice"]
    row["component_exists"] = exists
    row["noul"] = noul
    row["skip_function"] = function_pick["choice"]
    row["skip_if"] = branch_pick["choice"]
    row["returned_threshold"] = threshold_score
    row["returned_loop_bound"] = loop_score
    row["returned_parameter"] = parameter_score
    row["threshold"] = threshold
    row["loop_bound"] = loop_bound
    row["parameter"] = parameter
    row["life"] = life
    row["blocks"] = _authorized_block(skip, site["choice"], exists, which["choice"], life)
    emitted = any(
        (
            site["choice"] is not None,
            which["choice"] is not None,
            exists is not None,
            noul is not None,
            function_pick["choice"] is not None,
            branch_pick["choice"] is not None,
            threshold_score is not None,
            loop_score is not None,
            parameter_score is not None,
            any(value is not None for value in life.values()),
        )
    )
    row["decision_emitted"] = emitted
    if not emitted:
        receipt_error = hop.get("error") or hop.get("skipped")
        if receipt_error:
            row["error"] = receipt_error
        elif _any_probability(answers):
            row["error"] = "tie"
        else:
            row["error"] = "empty"
    _remember(posted, row)
    del use_cache
    if record:
        _append(record_to or record_path(), row)
    return row


def _stop_pips(namespace, symbol, family, stop_dist, sl, entry) -> float | None:
    """Measured stop width. The threshold is not this measurement."""

    try:
        from src.components.ultimate_book import minimal_size as ms

        if str(namespace or "") != getattr(ms, "F5_NAMESPACE", CHALLENGE_NS):
            return None
        if not ms.f5_is_dsp_family(family):
            return None
        dist = stop_dist
        if dist in (None, "", 0, "0"):
            try:
                dist = abs(float(entry) - float(sl))
            except (TypeError, ValueError):
                dist = None
        measured = ms.f5_fx_dsp_stop_pips(symbol, dist)
    except Exception:
        return None
    return _number(measured)


def _ask_blocks(skip: str, facts: dict[str, Any], cache_key: str) -> bool:
    try:
        row = decide(skip, facts, cache_key=cache_key)
    except Exception:
        return False
    return row.get("blocks") is True


def _wrap_fx(orig):
    def wrapped(namespace, symbol, family=None, stop_dist=None, sl=None, entry=None):
        reason = orig(
            namespace,
            symbol,
            family=family,
            stop_dist=stop_dist,
            sl=sl,
            entry=entry,
        )
        if str(namespace or "") != CHALLENGE_NS:
            return reason
        if reason == "fx_dsp_dropped_j6":
            if _ask_blocks(
                "fx_dsp_dropped_j6",
                {
                    "symbol": str(symbol or ""),
                    "sleeve": str(family or ""),
                    "in_drop_set": True,
                    "stop_dist": stop_dist,
                    "namespace": CHALLENGE_NS,
                },
                f"fx_dsp_dropped_j6|{symbol}|{family}",
            ):
                return "fx_dsp_dropped_j6"
            return None
        if reason == "fx_dsp_stop_le_8pip":
            if _ask_blocks(
                "fx_dsp_stop_le_8pip",
                {
                    "symbol": str(symbol or ""),
                    "sleeve": str(family or ""),
                    "stop_dist": stop_dist,
                    "stop_pips": _stop_pips(namespace, symbol, family, stop_dist, sl, entry),
                    "namespace": str(namespace or ""),
                },
                f"fx_dsp_stop_le_8pip|{symbol}|{family}|{stop_dist}",
            ):
                return "fx_dsp_stop_le_8pip"
            return None
        return reason

    return wrapped


def _wrap_today(orig):
    def wrapped(self, sleeve, symbol, decision_day):
        fact = orig(self, sleeve, symbol, decision_day)
        owner = _caller_self(2)
        if not fact or not _is_challenge(owner):
            return fact
        day = str(decision_day or "")[:10]
        return _ask_blocks(
            "already_placed_today",
            {
                "symbol": str(symbol or ""),
                "sleeve": str(sleeve or ""),
                "decision_day": day,
                "already_filled_today": True,
            },
            f"already_placed_today|{sleeve}|{symbol}|{day}",
        )

    return wrapped


def _wrap_late(orig):
    def wrapped(now, bar_iso, tf, frac):
        fact = orig(now, bar_iso, tf, frac)
        owner = _caller_self(2)
        if not fact or not _is_challenge(owner):
            return fact
        minutes = None
        try:
            from src.components.ultimate_book.book_engine import _TF_MINUTES

            per = _TF_MINUTES.get(tf)
            if per and bar_iso:
                from datetime import timedelta

                bar_close = datetime.fromisoformat(str(bar_iso)) + timedelta(minutes=per)
                if bar_close.tzinfo is None and getattr(now, "tzinfo", None) is not None:
                    bar_close = bar_close.replace(tzinfo=timezone.utc)
                minutes = (now - bar_close).total_seconds() / 60.0
        except Exception:
            minutes = None
        return _ask_blocks(
            "stale_late_entry_after_restart",
            {
                "bar_iso": str(bar_iso or ""),
                "timeframe": str(tf or ""),
                "freshness_frac": frac,
                "minutes_past_close": minutes,
                "past_freshness": True,
            },
            f"stale_late_entry_after_restart|{bar_iso}|{tf}",
        )

    return wrapped


def _wrap_hold(orig):
    def wrapped(self, *args, **kwargs):
        held, decision = orig(self, *args, **kwargs)
        if not held or not _is_challenge(self):
            return held, decision
        intent = args[0] if args else kwargs.get("intent")
        reason = ""
        action = ""
        if isinstance(decision, dict):
            reason = str(decision.get("reason") or decision.get("why_code") or "")
            action = str(decision.get("action") or "")
        symbol = str(getattr(intent, "symbol", "") or "")
        sleeve = str(getattr(intent, "sleeve", "") or "")
        try:
            row = decide(
                "judgment_hold",
                {
                    "symbol": symbol,
                    "sleeve": sleeve,
                    "flow_reason": reason,
                    "flow_action": action,
                    "held": True,
                },
                cache_key=f"judgment_hold|{sleeve}|{symbol}|{reason}",
            )
        except Exception:
            row = {"blocks": False}
        if row.get("blocks") is True:
            return True, decision
        stamped = dict(decision) if isinstance(decision, dict) else {"decision": decision}
        if row.get("choice") is not None:
            stamped["skip_choice"] = row.get("choice")
        life = row.get("life") if isinstance(row.get("life"), dict) else {}
        passed = {step: name for step, name in life.items() if name is not None}
        if passed:
            stamped["skip_life"] = passed
        return False, stamped

    return wrapped


def _exposure_brief(exposures) -> list[dict[str, Any]]:
    out = []
    for pos in list(exposures or []):
        out.append(
            {
                "ticket": getattr(pos, "ticket", None),
                "symbol": str(getattr(pos, "symbol", "") or ""),
                "comment": str(getattr(pos, "comment", "") or ""),
            }
        )
    return out


def _wrap_exposures(orig):
    def wrapped(self, symbol, open_positions_snapshot=None):
        exposures = orig(
            self,
            symbol,
            open_positions_snapshot=open_positions_snapshot,
        )
        if not exposures or not _is_challenge(self):
            return exposures
        frame = sys._getframe(1)
        intent = frame.f_locals.get("intent")
        sleeve = str(getattr(intent, "sleeve", "") or "")
        brief = _exposure_brief(exposures)
        tickets = ",".join(str(item.get("ticket")) for item in brief)
        if _ask_blocks(
            "same_broker_symbol_open_position_lifecycle_guard",
            {
                "symbol": str(symbol or ""),
                "sleeve": sleeve,
                "open_tickets": brief,
                "open_count": len(list(exposures)),
            },
            "same_broker_symbol_open_position_lifecycle_guard"
            f"|{symbol}|{sleeve}|{tickets}",
        ):
            return exposures
        return []

    return wrapped


def _caller_is_cycle_keys(frame) -> bool:
    """True only at the book_owner line that feeds the cycle-symbol skip."""

    filename = str(getattr(frame.f_code, "co_filename", "") or "")
    if not filename.replace("\\", "/").endswith("book_owner.py"):
        return False
    line = linecache.getline(filename, frame.f_lineno)
    if "_broker_symbol_keys_for_canonical" not in line:
        return False
    number = frame.f_lineno
    while True:
        text = linecache.getline(filename, number)
        if text == "":
            return False
        if number != frame.f_lineno and text[:1] not in (" ", "\t", "\n", "#"):
            return False
        if "same_broker_symbol_already_placed_this_cycle" in text:
            return True
        number += 1


def cycle_target_keys(
    real_keys: set[str],
    placed: set[str] | None,
    *,
    symbol: str,
    sleeve: str,
) -> set[str]:
    """The placed set stays. Empty keys let the sibling through when the skip is not returned."""

    if not placed or not set.intersection(placed, real_keys):
        return real_keys
    overlap = sorted(str(item) for item in set.intersection(placed, real_keys))
    if _ask_blocks(
        "same_broker_symbol_already_placed_this_cycle",
        {
            "symbol": symbol,
            "sleeve": sleeve,
            "placed_keys": overlap,
            "already_placed_this_cycle": True,
        },
        f"same_broker_symbol_already_placed_this_cycle|{symbol}|{sleeve}",
    ):
        return real_keys
    return set()


def _wrap_keys(orig):
    def wrapped(self, symbol):
        keys = orig(self, symbol)
        try:
            frame = sys._getframe(1)
            at_cycle = _caller_is_cycle_keys(frame)
        except Exception:
            return keys
        if not at_cycle or not _is_challenge(self):
            return keys
        try:
            placed = frame.f_locals.get("placed_broker_symbol_keys")
            intent = frame.f_locals.get("intent")
            sleeve = str(getattr(intent, "sleeve", "") or "")
            return cycle_target_keys(
                set(keys),
                set(placed) if placed else set(),
                symbol=str(symbol or ""),
                sleeve=sleeve,
            )
        except Exception:
            return set()

    return wrapped


def install(*, live_stamp: bool = True) -> dict[str, Any]:
    """Wrap the skip predicates. Idempotent. Does not edit book_owner.py."""

    global _INSTALLED, _ORIG_KEYS, _ORIG_FX, _ORIG_TODAY, _ORIG_LATE, _ORIG_HOLD, _ORIG_EXPOSURES
    if _INSTALLED:
        return {"installed": True, "already": True, "model": MODEL}
    from src.components.ultimate_book import minimal_size as ms
    from src.components.ultimate_book.book_owner import UltimateBookOwner
    from src.components.ultimate_book.placement_ledger import PlacementLedger

    _ORIG_FX = ms.f5_fx_dsp_tight_stop_reason
    ms.f5_fx_dsp_tight_stop_reason = _wrap_fx(_ORIG_FX)
    _ORIG_TODAY = PlacementLedger.already_placed_today
    PlacementLedger.already_placed_today = _wrap_today(_ORIG_TODAY)
    _ORIG_LATE = UltimateBookOwner._entry_too_late
    late_fn = _ORIG_LATE.__func__ if isinstance(_ORIG_LATE, staticmethod) else _ORIG_LATE
    UltimateBookOwner._entry_too_late = staticmethod(_wrap_late(late_fn))
    _ORIG_HOLD = UltimateBookOwner._judgment_flow_hold
    UltimateBookOwner._judgment_flow_hold = _wrap_hold(_ORIG_HOLD)
    _ORIG_EXPOSURES = UltimateBookOwner._same_broker_symbol_open_exposures
    UltimateBookOwner._same_broker_symbol_open_exposures = _wrap_exposures(_ORIG_EXPOSURES)
    _ORIG_KEYS = UltimateBookOwner._broker_symbol_keys_for_canonical
    UltimateBookOwner._broker_symbol_keys_for_canonical = _wrap_keys(_ORIG_KEYS)
    _INSTALLED = True
    stamp = {
        "schema": "gtos.skip_choices.install.v1",
        "installed": True,
        "at_utc": _now(),
        "pid": os.getpid(),
        "model": MODEL,
        "components": list(SPECS),
        "agent_order_send": False,
        "book_owner_edited": False,
    }
    if live_stamp:
        try:
            path = record_path().with_name("skip_choices_install.json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(stamp, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError:
            pass
    return stamp
