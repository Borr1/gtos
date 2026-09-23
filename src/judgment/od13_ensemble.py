"""OD-13 ensemble consume.

Every decision on this state, including each parameter, is the System One
return. One call: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs
https://api.typesafe.ai/v1/systemone. Questions are only Noul, Choice, or
Score. Prior outcomes are attached on the ask, and the return is stored
for the next ask.

An empty answer, a tie, or an error leaves that return unset. It does not
restore a constant. Floor and baseline are not a question. This module
does not send and does not flatten. Judge code stays unable to send.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.od13_ensemble.v1"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

# Menu option. The receipt field is the return for that state.
ALREADY_LIVE_UNDER = "PLACE_APPLY"

STANDALONE_ORDER_ENSEMBLE_NAMES = frozenset(
    {
        "ORDER_ENSEMBLE",
        "order_ensemble",
        "order_ensemble_shuffle",
        "od_10_perm_avg_research_router",
        "od_12_yesno_reverse_regression",
        "od_10",
        "od_12",
    }
)

_CONSUME_ORDER = (
    "od_13",
    "ORDER_ENSEMBLE",
    "order_ensemble",
    "order_ensemble_shuffle",
    "od_10_perm_avg_research_router",
    "od_12_yesno_reverse_regression",
    "od_10",
    "od_12",
)
_STATUS_ROWS = (
    "order_ensemble_shuffle",
    "od_10_perm_avg_research_router",
    "od_12_yesno_reverse_regression",
)
_STATUS_COMPONENT_ORDER = ("od_13",) + _STATUS_ROWS
_KILL_FIELDS = {
    "order_ensemble_shuffle": "kill_order_ensemble_shuffle",
    "od_10_perm_avg_research_router": "kill_od_10_perm_avg_research_router",
    "od_12_yesno_reverse_regression": "kill_od_12_yesno_reverse_regression",
}

_LEVELS = ("none", "trace", "small", "modest", "notable", "heavy")
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
_DROP_KEYS = frozenset(
    {
        "never_place",
        "never_remint",
        "never_flatten",
        "broker_effect",
        "dig_never_broker_send",
        "news_invent",
        "pack1b_beaten",
        "place_apply",
        "place_ensemble",
        "verdict",
        "already_live",
        "already_live_under",
        "standalone_order_ensemble",
        "standalone_path",
        "apply",
        "killed_standalone_apply",
        "consume",
        "reason",
        "prior_outcomes",
        "answer",
        "choice",
        "score",
        "noul",
        "probabilities",
        "default",
    }
)
_DROP = object()

# History only when jev_questions cannot be imported. A miss is not copied back.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []


class StandaloneOrderEnsembleError(RuntimeError):
    """The returned verdict for this path is KILL_ENFORCE."""


@dataclass(frozen=True)
class _Spec:
    qid: str
    field: str
    kind: str
    prompt: str
    criteria: str = ""
    subject: str = ""



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


def _choice_prompt(sentence: str) -> str:
    return (
        f"{sentence} "
        "The option with the single highest probability is the decision. "
        "An empty answer or a tie leaves it unset. "
        "Do not send an order."
    )


def _noul_prompt(sentence: str, *, flatten: bool = False) -> str:
    tail = "Do not send an order and do not flatten." if flatten else "Do not send an order."
    return (
        f"{sentence} "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "A returned probability stays the noul. "
        f"{tail}"
    )


def _score_prompt(sentence: str) -> str:
    return (
        f"{sentence} "
        "It may sit between the levels. "
        "An empty score leaves it unset. "
        "Do not send an order."
    )


def _parameter_prompt(subject: str) -> str:
    return _score_prompt(f"The score you return is the parameter for {subject} on this state.")


_CRITERIA: dict[str, dict[str, str]] = {
    "verdict": {
        "ALREADY_LIVE": "This consume is already live on the place ensemble.",
        "KILL_ENFORCE": "This path is a standalone apply that this consume refuses.",
        "STAND": "This consume stands.",
    },
    "under": {
        ALREADY_LIVE_UNDER: "This consume sits on place apply.",
        "PLACE_ENSEMBLE": "This consume sits on the place ensemble.",
    },
    "consume": {name: f"This consume is {name}." for name in _CONSUME_ORDER},
    "reason": {
        "subsumed_by_od_13": "The reason is that the standalone path is subsumed by OD-13.",
        "research_router_not_place_conf": "The reason is that the path is a research router.",
        "ci_only": "The reason is that the path is CI only.",
        "already_live_ensemble": "The reason is that the ensemble consume is already live.",
    },
    "component": {
        "od_13": "The OD-13 ensemble is the component on this state.",
        "place_choice": "The place-choice stamp is the component on this state.",
        "conf_order": "The confidence order block is the component on this state.",
        "order_ensemble_shuffle": "The shuffle path is the component on this state.",
        "od_10_perm_avg_research_router": "The research router is the component on this state.",
        "od_12_yesno_reverse_regression": "The regression path is the component on this state.",
    },
    "status_component": {
        name: f"The component on this state is {name}." for name in _STATUS_COMPONENT_ORDER
    },
}

_COMPOSE_SPECS: tuple[_Spec, ...] = (
    _Spec("od13_verdict", "verdict", "choice", _choice_prompt("Which verdict is this OD-13 state?"), "verdict", "the verdict"),
    _Spec("od13_under", "already_live_under", "choice", _choice_prompt("Where does this OD-13 consume sit?"), "under", "where the consume sits"),
    _Spec("od13_consume", "consume", "choice", _choice_prompt("Which consume is this state?"), "consume", "the consume"),
    _Spec("od13_reason", "reason", "choice", _choice_prompt("Which reason is this OD-13 state?"), "reason", "the reason"),
    _Spec("od13_component", "component", "choice", _choice_prompt("Which component exists on this OD-13 state?"), "component", "the component"),
    _Spec("od13_standalone", "standalone_order_ensemble", "noul", _noul_prompt("Is this state a standalone order ensemble?"), subject="the standalone ensemble"),
    _Spec("od13_never_place", "never_place", "noul", _noul_prompt("Is place blocked on this OD-13 state?"), subject="place blocked"),
    _Spec("od13_never_remint", "never_remint", "noul", _noul_prompt("Is remint blocked on this OD-13 state?"), subject="remint blocked"),
    _Spec("od13_never_flatten", "never_flatten", "noul", _noul_prompt("Is flatten blocked on this OD-13 state?", flatten=True), subject="flatten blocked"),
    _Spec("od13_already_live", "already_live", "noul", _noul_prompt("Is this OD-13 consume already live?"), subject="already live"),
    _Spec("od13_pack1b_beaten", "pack1b_beaten", "noul", _noul_prompt("Is pack 1b beaten on this OD-13 state?"), subject="pack 1b beaten"),
    _Spec("od13_place_apply", "place_apply", "noul", _noul_prompt("Is place apply open on this OD-13 state?"), subject="place apply"),
    _Spec("od13_place_ensemble", "place_ensemble", "noul", _noul_prompt("Is the place ensemble open on this OD-13 state?"), subject="the place ensemble"),
    _Spec("od13_apply", "apply", "noul", _noul_prompt("Does this OD-13 state apply?"), subject="apply"),
    _Spec("od13_component_exists", "component_exists", "noul", _noul_prompt("Does the component on this OD-13 state exist?"), subject="component existence"),
    _Spec("od13_kill_order_ensemble_shuffle", "kill_order_ensemble_shuffle", "noul", _noul_prompt("Is order_ensemble_shuffle killed on this state?"), subject="the shuffle kill"),
    _Spec("od13_kill_od_10_perm_avg_research_router", "kill_od_10_perm_avg_research_router", "noul", _noul_prompt("Is od_10_perm_avg_research_router killed on this state?"), subject="the research-router kill"),
    _Spec("od13_kill_od_12_yesno_reverse_regression", "kill_od_12_yesno_reverse_regression", "noul", _noul_prompt("Is od_12_yesno_reverse_regression killed on this state?"), subject="the regression kill"),
    _Spec("od13_broker_effect", "broker_effect", "noul", _noul_prompt("Is a broker effect open on this OD-13 state?"), subject="the broker effect"),
    _Spec("od13_dig_never_broker_send", "dig_never_broker_send", "noul", _noul_prompt("Is this OD-13 dig barred from sending?"), subject="the dig send bar"),
    _Spec("od13_news_invent", "news_invent", "noul", _noul_prompt("Is a news protocol invented on this OD-13 state?"), subject="news invent"),
    _Spec("od13_threshold", "threshold", "score", _score_prompt("The score you return is the threshold for this OD-13 state.")),
    _Spec("od13_loop", "loop_bound", "score", _score_prompt("The score you return is the loop bound for this OD-13 state.")),
    _Spec("od13_parameter", "parameter", "score", _score_prompt("The score you return is the parameter for this OD-13 state.")),
)


def _status_specs() -> tuple[_Spec, ...]:
    rows: list[_Spec] = []
    for name in _STATUS_ROWS:
        rows.append(_Spec(
            f"{name}_verdict",
            f"{name}.verdict",
            "choice",
            _choice_prompt(f"Which verdict is {name} on this state?"),
            "verdict",
            f"the {name} verdict",
        ))
        rows.append(_Spec(
            f"{name}_reason",
            f"{name}.reason",
            "choice",
            _choice_prompt(f"Which reason is {name} on this state?"),
            "reason",
            f"the {name} reason",
        ))
        rows.append(_Spec(
            f"{name}_apply",
            f"{name}.apply",
            "noul",
            _noul_prompt(f"Does {name} apply on this state?"),
            subject=f"the {name} apply",
        ))
        rows.append(_Spec(
            f"{name}_standalone",
            f"{name}.standalone_path",
            "noul",
            _noul_prompt(f"Is {name} a standalone path on this state?"),
            subject=f"the {name} standalone path",
        ))
        rows.append(_Spec(
            f"{name}_parameter",
            f"{name}.parameter",
            "score",
            _score_prompt(f"The score you return is the parameter for {name} on this state."),
        ))
    rows.extend((
        _Spec("od13_status_component", "component", "choice", _choice_prompt("Which component exists on this standalone-apply state?"), "status_component", "the component"),
        _Spec("od13_status_component_exists", "component_exists", "noul", _noul_prompt("Does the component on this standalone-apply state exist?"), subject="component existence"),
        _Spec("od13_status_threshold", "threshold", "score", _score_prompt("The score you return is the threshold for this standalone-apply state.")),
        _Spec("od13_status_loop", "loop_bound", "score", _score_prompt("The score you return is the loop bound for this standalone-apply state.")),
        _Spec("od13_status_parameter", "parameter", "score", _score_prompt("The score you return is the parameter for this standalone-apply state.")),
    ))
    return tuple(rows)


_STATUS_SPECS = _status_specs()


def _limit_key(name: str) -> bool:
    low = str(name).lower()
    if low in _DROP_KEYS:
        return True
    if "floor" in low or "baseline" in low:
        return True
    return any(part in low for part in ("api_key", "token", "secret", "authorization", "password"))


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    if "floor" in compact or "baseline" in compact:
        return True
    for token in _BANNED_TEXT:
        piece = token.replace(",", "").replace("_", "").lower()
        if piece in compact:
            return True
    return False


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


def _scrub(value: Any, seen: set[int] | None = None) -> Any:
    if seen is None:
        seen = set()
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return _DROP
        seen.add(ident)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            cleaned = _scrub(item, seen)
            if cleaned is _DROP:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return _DROP
        seen.add(ident)
        kept = []
        for item in value:
            cleaned = _scrub(item, seen)
            if cleaned is _DROP:
                continue
            kept.append(cleaned)
        return kept
    if isinstance(value, str):
        if _banned_text(value):
            return _DROP
        return value
    if value is None or isinstance(value, (int, float, bool)):
        return value
    text = str(value)
    if _banned_text(text):
        return _DROP
    return text


def _strip_planted(block: dict[str, Any]) -> None:
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    menu = {
        str(key): str(text)
        for key, text in criteria.items()
        if not _banned_text(str(key)) and not _banned_text(str(text))
    }
    if not menu:
        return {}
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": menu,
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(menu))
        row = built.get(qid) if isinstance(built, dict) else None
        if isinstance(row, dict):
            body = dict(row)
    except Exception:
        pass
    _strip_planted(body)
    body["type"] = "choice"
    body["instructions"] = instructions
    body["criteria"] = menu
    return {qid: body}



def _score_question(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes on this state.",
                "false": "No on this state.",
            },
        }
    }


def _clean(pack: Mapping[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for qid, block in pack.items():
        if not isinstance(block, dict):
            continue
        if block.get("type") not in {"noul", "choice", "score"}:
            continue
        try:
            blob = json.dumps(block, default=str).lower()
        except Exception:
            blob = str(block).lower()
        if _banned_text(blob):
            continue
        clean[str(qid)] = block
    return clean


def _pack(specs: tuple[_Spec, ...]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    for spec in specs:
        if spec.kind == "choice":
            pack.update(_choice_question(spec.qid, spec.prompt, _CRITERIA[spec.criteria]))
            pack.update(_score_question(f"{spec.qid}_parameter", _parameter_prompt(spec.subject or spec.field)))
        elif spec.kind == "noul":
            pack.update(_noul_question(spec.qid, spec.prompt))
            pack.update(_score_question(f"{spec.qid}_parameter", _parameter_prompt(spec.subject or spec.field)))
        else:
            pack.update(_score_question(spec.qid, spec.prompt))
    return _clean(pack)


def _probabilities(block: Any, order: tuple[str, ...]) -> dict[str, float]:
    if not isinstance(block, dict) or block.get("error"):
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
        number = _number(value)
        if number is None:
            continue
        numeric[name] = number
    return numeric


def _local_unique(numeric: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    names = order or tuple(numeric)
    for name in names:
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


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie, an empty map, or a bare label stays unset."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "choice":
        return None
    numeric = _probabilities(block, order)
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


def _score(block: Any) -> float | None:
    """The returned score. A missing score stays missing and is not snapped to a level."""

    if isinstance(block, (int, float)) and not isinstance(block, bool):
        return _number(block)
    if not isinstance(block, dict) or block.get("error"):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "score":
        return None
    raw = block.get("score") if "score" in block else block.get("value") if "value" in block else None
    number = _number(raw) if raw is not None else None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(block))
    except Exception:
        parsed = number
    if number is None:
        return parsed
    if parsed is None or parsed != number:
        return None
    return number


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A missing noul stays missing."""

    if block is True or block is False:
        return block
    if not isinstance(block, dict) or block.get("error"):
        return _number(block)
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "noul":
        return None
    if "noul" in block:
        value = block.get("noul")
    elif "Noul" in block:
        value = block.get("Noul")
    else:
        return None
    if value is None:
        return None
    if value is True or value is False:
        return value
    return _number(value)


def _fill(specs: tuple[_Spec, ...], answers: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    parameters: dict[str, float | None] = {}
    for spec in specs:
        block = answers.get(spec.qid)
        if spec.kind == "choice":
            order = tuple(_CRITERIA[spec.criteria])
            out[spec.field] = _choice(block, order)
            parameters[spec.field] = _score(answers.get(f"{spec.qid}_parameter"))
        elif spec.kind == "noul":
            out[spec.field] = _noul(block)
            parameters[spec.field] = _score(answers.get(f"{spec.qid}_parameter"))
        else:
            value = _score(block)
            out[spec.field] = value
            parameters[spec.field] = value
    out["parameters"] = parameters
    return out


def _pairs(
    specs: tuple[_Spec, ...],
    filled: Mapping[str, Any],
    error: str | None,
) -> tuple[tuple[str, Any, str | None], ...]:
    parameters = filled.get("parameters") if isinstance(filled.get("parameters"), Mapping) else {}
    pairs: list[tuple[str, Any, str | None]] = []
    for spec in specs:
        value = filled.get(spec.field)
        if spec.kind == "score":
            miss = "score_missing"
        elif spec.kind == "choice":
            miss = "tie_or_empty"
        else:
            miss = "noul_missing"
        pairs.append((spec.qid, value, None if value is not None else (error or miss)))
        if spec.kind != "score":
            parameter = parameters.get(spec.field)
            pairs.append((
                f"{spec.qid}_parameter",
                parameter,
                None if parameter is not None else (error or "score_missing"),
            ))
    return tuple(pairs)


def _object_facts(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    raw: Any
    if isinstance(obj, Mapping):
        raw = dict(obj)
    else:
        as_dict = getattr(obj, "as_dict", None)
        if callable(as_dict):
            try:
                dumped = as_dict()
            except Exception:
                dumped = None
            raw = dict(dumped) if isinstance(dumped, Mapping) else {}
        else:
            raw = {}
            for key in (
                "menu_hash",
                "option_order_hash",
                "state_hash",
                "complete",
                "option_order",
                "missing",
                "consumes",
                "login",
                "state_sufficient",
            ):
                if hasattr(obj, key):
                    raw[key] = getattr(obj, key)
    cleaned = _scrub(raw)
    return cleaned if isinstance(cleaned, dict) else {}


def _env_facts() -> dict[str, str]:
    keys = (
        "GTOS_JEV_OD13_ENSEMBLE",
        "GTOS_JEV_PLACE_APPLY",
        "GTOS_JEV_PLACE_ENSEMBLE",
        "GTOS_JEV_CONF_ORDER_CONSUME",
    )
    out: dict[str, str] = {}
    for key in keys:
        cleaned = _scrub(str(os.environ.get(key, "")))
        if cleaned is _DROP or not isinstance(cleaned, str):
            continue
        out[key] = cleaned
    return out


def _state(facts: Mapping[str, Any]) -> dict[str, Any]:
    cleaned = _scrub(dict(facts))
    state = cleaned if isinstance(cleaned, dict) else {}
    state.pop("prior_outcomes", None)
    state["model"] = MODEL
    state["schema"] = SCHEMA
    if state.get("login") in (None, ""):
        state["login"] = CHALLENGE_LOGIN
    state["ns"] = CHALLENGE_NS
    state["namespace"] = CHALLENGE_NS
    for key, value in _env_facts().items():
        state.setdefault(key, value)
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


def _remember(state: Mapping[str, Any], pairs: tuple[tuple[str, Any, str | None], ...]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in pairs:
            _LOCAL_OUTCOMES.append({"key": key, "value": value, "error": error})
        return
    for key, value, error in pairs:
        try:
            append_outcome(key, value, logged, error=error)
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


def _ask(
    facts: Mapping[str, Any],
    specs: tuple[_Spec, ...],
    evaluate_fn: Callable[..., Any] | None,
) -> tuple[dict[str, Any], str | None, str]:
    state = _state(facts)
    _bind_card(state)
    questions = _pack(specs)
    _bind_card(None)
    _attach_priors(state, questions)
    if not questions:
        filled = _fill(specs, {})
        _remember(state, _pairs(specs, filled, "question_pack_fail"))
        return filled, "question_pack_fail", MODEL
    try:
        receipt = _post(state, questions, evaluate_fn)
    except Exception as exc:  # noqa: BLE001 — a failed ask leaves the return unset
        filled = _fill(specs, {})
        error = type(exc).__name__
        _remember(state, _pairs(specs, filled, error))
        return filled, error, MODEL
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    model = receipt.get("model") if isinstance(receipt.get("model"), str) and receipt.get("model") else MODEL
    if not answers:
        error = str(receipt.get("error") or receipt.get("skipped") or "empty")
        filled = _fill(specs, {})
        _remember(state, _pairs(specs, filled, error))
        return filled, error, str(model)
    filled = _fill(specs, answers)
    error = None
    if receipt.get("ok") is False:
        error = str(receipt.get("error") or receipt.get("skipped") or "post_failed")
    _remember(state, _pairs(specs, filled, error))
    return filled, error, str(model)


def _killed(filled: Mapping[str, Any]) -> list[str] | None:
    flags = {name: filled.get(field) for name, field in _KILL_FIELDS.items()}
    if all(value is None for value in flags.values()):
        return None
    return [name for name, value in flags.items() if value is True]


def _hash_card(stamp: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "menu_hash": stamp.get("menu_hash"),
        "option_order_hash": stamp.get("option_order_hash"),
        "state_hash": stamp.get("state_hash"),
        "complete": stamp.get("complete"),
    }


def _compose_card(
    filled: Mapping[str, Any],
    error: str | None,
    model: str,
    stamp: Mapping[str, Any],
    conf: Mapping[str, Any],
) -> dict[str, Any]:
    parameters = filled.get("parameters") if isinstance(filled.get("parameters"), Mapping) else {}
    return {
        "schema": SCHEMA,
        "model": model,
        "consume": filled.get("consume"),
        "verdict": filled.get("verdict"),
        "already_live_under": filled.get("already_live_under"),
        "reason": filled.get("reason"),
        "component": filled.get("component"),
        "component_exists": filled.get("component_exists"),
        "place_apply": filled.get("place_apply"),
        "place_ensemble": filled.get("place_ensemble"),
        "standalone_order_ensemble": filled.get("standalone_order_ensemble"),
        "apply": filled.get("apply"),
        "already_live": filled.get("already_live"),
        "pack1b_beaten": filled.get("pack1b_beaten"),
        "never_place": filled.get("never_place"),
        "never_remint": filled.get("never_remint"),
        "never_flatten": filled.get("never_flatten"),
        "broker_effect": filled.get("broker_effect"),
        "dig_never_broker_send": filled.get("dig_never_broker_send"),
        "news_invent": filled.get("news_invent"),
        "kill_order_ensemble_shuffle": filled.get("kill_order_ensemble_shuffle"),
        "kill_od_10_perm_avg_research_router": filled.get("kill_od_10_perm_avg_research_router"),
        "kill_od_12_yesno_reverse_regression": filled.get("kill_od_12_yesno_reverse_regression"),
        "killed_standalone_apply": _killed(filled),
        "threshold": filled.get("threshold"),
        "loop_bound": filled.get("loop_bound"),
        "parameter": filled.get("parameter"),
        "parameters": dict(parameters),
        "place_choice": _hash_card(stamp),
        "conf_order": dict(conf),
        "error": error,
    }


def _status_card(filled: Mapping[str, Any], error: str | None, model: str) -> dict[str, Any]:
    parameters = filled.get("parameters") if isinstance(filled.get("parameters"), Mapping) else {}
    card: dict[str, Any] = {
        "schema": SCHEMA,
        "model": model,
        "threshold": filled.get("threshold"),
        "loop_bound": filled.get("loop_bound"),
        "parameter": filled.get("parameter"),
        "component": filled.get("component"),
        "component_exists": filled.get("component_exists"),
        "error": error,
    }
    for name in _STATUS_ROWS:
        card[name] = {
            "verdict": filled.get(f"{name}.verdict"),
            "reason": filled.get(f"{name}.reason"),
            "apply": filled.get(f"{name}.apply"),
            "standalone_path": filled.get(f"{name}.standalone_path"),
            "parameter": filled.get(f"{name}.parameter"),
            "parameters": {
                "verdict": parameters.get(f"{name}.verdict"),
                "reason": parameters.get(f"{name}.reason"),
                "apply": parameters.get(f"{name}.apply"),
                "standalone_path": parameters.get(f"{name}.standalone_path"),
            },
        }
    return card


def _challenge_gate(login: Any) -> None:
    try:
        from .challenge import assert_challenge_payout_writer
    except Exception:
        return
    assert_challenge_payout_writer(login)


def _news_gate(invented_files: tuple[str, ...]) -> None:
    for name in invented_files:
        if "NEWS_PROTOCOL" in str(name).upper():
            raise ValueError("invented NEWS_PROTOCOL")
    try:
        from .veto import refuse_invented_news_protocol
    except Exception:
        return
    refuse_invented_news_protocol(invented_files)


def _refuse_incomplete(place_choice: Any) -> None:
    fn = getattr(place_choice, "refuse_if_incomplete", None)
    if callable(fn):
        fn()


def compose_od13_ensemble(
    *,
    place_choice: Any,
    conf_order: Any,
    login: int | str = CHALLENGE_LOGIN,
    path_name: str = "od_13",
    invented_files: tuple[str, ...] = (),
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """OD-13 consume for this state.

    The stamp and the confidence block are facts. The verdict, the nouls,
    and each parameter are the System One return. A miss stays unset.
    This function does not send and does not flatten.
    """

    _challenge_gate(login)
    _news_gate(invented_files)
    _refuse_incomplete(place_choice)
    stamp = _object_facts(place_choice)
    conf = _object_facts(conf_order)
    facts = {
        "gate": "od13_compose",
        "login": login,
        "path_name": str(path_name or "").strip(),
        "stamp": stamp,
        "conf_order": conf,
        "invented_files": [str(item) for item in invented_files],
    }
    filled, error, model = _ask(facts, _COMPOSE_SPECS, evaluate_fn)
    return _compose_card(filled, error, model, stamp, conf)


def refuse_standalone_order_ensemble(
    path_name: str,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> None:
    """Refuse a standalone path only when the returned verdict is KILL_ENFORCE.

    Catalog membership is not that verdict. An empty answer, a tie, or an
    error does not raise.
    """

    name = str(path_name or "").strip()
    filled, _error, _model = _ask(
        {"gate": "od13_refuse", "path_name": name},
        _COMPOSE_SPECS,
        evaluate_fn,
    )
    if filled.get("verdict") == "KILL_ENFORCE":
        raise StandaloneOrderEnsembleError(
            f"standalone path {name!r} returned KILL_ENFORCE"
        )


def standalone_apply_status(
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """One ask for the three standalone proposals.

    Each row's verdict, reason, apply, standalone path, and parameter are
    that return. A miss stays unset.
    """

    facts = {
        "gate": "od13_status",
        "proposals": list(_STATUS_ROWS),
    }
    filled, error, model = _ask(facts, _STATUS_SPECS, evaluate_fn)
    return _status_card(filled, error, model)


__all__ = [
    "ALREADY_LIVE_UNDER",
    "CHALLENGE_LOGIN",
    "CHALLENGE_NS",
    "MODEL",
    "SCHEMA",
    "STANDALONE_ORDER_ENSEMBLE_NAMES",
    "StandaloneOrderEnsembleError",
    "compose_od13_ensemble",
    "refuse_standalone_order_ensemble",
    "standalone_apply_status",
]
