"""CONF_GATE consume — Challenge 0.

The band, the required band, the disposition, the place action, the
order-consume note, the high-trust block, the hash check, the threshold,
the loop bound, the parameter, and which component exists are the System
One return for this state. One hop is ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False`` (POST
https://api.typesafe.ai/v1/systemone). A return is a Noul, a Choice, or
a Score. A Score may sit between levels. Prior outcomes are attached on
every ask, and the return is stored for the next ask.

An empty answer, a tie, a missing score, or an error leaves that return
unset. Vendor cutoffs are not the consume decision. This module does not
authorize ``GTOS_JEV_CONF_GATE_APPLY``. It does not invent news. It does
not send.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CONF_GATE_APPLY_ENV = "GTOS_JEV_CONF_GATE_APPLY"

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_BAND_ORDER = ("LOW", "MED", "HIGH", "VETO")
_PLACE_ORDER = ("PLACE", "STAND", "DELAY", "REMINT", "VETO")
_DISPOSITION_ORDER = (
    "veto_place_path",
    "high_trust_blocked_for_place",
    "shadow_only",
    "vendor_high_not_challenge_true",
    "shadow_review",
    "consume_keep_if_sufficient",
)
_NOTE_ORDER = ("PLACE_to_DELAY", "keep")
_COMPONENT_ORDER = ("conf_gate", "order_block", "high_trust", "hash_receipt")
_LIMIT_PARTS = ("floor", "baseline", "to_pass", "pass_line")
_BANNED = (
    "90000",
    "90,000",
    "90_000",
    "90k",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "flatten",
    "order_send",
)

# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []



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


def _limit_key(name: str) -> bool:
    low = name.lower()
    return any(part in low for part in _LIMIT_PARTS)


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED)


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


def _scrub(value: Any, seen: set[int] | None = None) -> Any:
    if seen is None:
        seen = set()
    if isinstance(value, str):
        if _banned_text(value):
            return None
        return value
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _finite(value)
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            cleaned = _scrub(item, seen)
            if cleaned is None and item is not None:
                continue
            out[name] = cleaned
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        return [_scrub(item, seen) for item in value]
    return None


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, Mapping):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _local_unique(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    if not probs:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    names = order or tuple(probs)
    for name in names:
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


def _named(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    if not probs:
        return None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(probs), order)
    except Exception:
        picked = _local_unique(probs, order)
    if picked is None or str(picked) not in order:
        return None
    return str(picked)


def _choice(block: Any, order: tuple[str, ...]) -> str | None:
    return _named(_probs(block), order)


def _score(block: Any) -> float | None:
    """The returned score. A tie or an error leaves it unset. It is not snapped."""

    if not isinstance(block, Mapping):
        return None
    if block.get("error"):
        return None
    for key in ("score", "value"):
        if key in block and block.get(key) is not None:
            return _finite(block.get(key))
    probs = _probs(block)
    if probs and _named(probs, tuple(probs)) is None:
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        return None


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A missing noul stays missing."""

    if not isinstance(block, Mapping):
        return None
    if "noul" in block:
        value = block.get("noul")
        if value is True or value is False:
            return value
        return _finite(value)
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _field_error(block: Any, value: Any, order: tuple[str, ...], receipt_error: str | None) -> str | None:
    if value is not None:
        return None
    if receipt_error:
        return receipt_error
    probs = _probs(block)
    if probs and _named(probs, order or tuple(probs)) is None:
        return "tie"
    return "empty"


def _choice_q(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(text) for key, text in criteria.items()},
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
    body["criteria"] = {str(key): str(text) for key, text in criteria.items()}
    return {qid: body}



def _score_q(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _noul_q(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes on this consume state.",
                "false": "No on this consume state.",
            },
        }
    }


def _questions() -> dict[str, Any]:
    """One consume ask. The menu names a return. It does not decide."""

    pack: dict[str, Any] = {}
    pack.update(_choice_q(
        "conf_band",
        "What is the consume band on this state? "
        "The option you return is that band. "
        "An empty answer or a tie leaves the band unset. "
        "Do not send.",
        {
            "LOW": "The consume band on this state is low.",
            "MED": "The consume band on this state is mid.",
            "HIGH": "The consume band on this state is high.",
            "VETO": "This consume vetoes the place path.",
        },
    ))
    pack.update(_choice_q(
        "conf_required_band",
        "What band does this stake require? "
        "The option you return is that requirement. "
        "An empty answer or a tie leaves the requirement unset. "
        "Do not send.",
        {
            "LOW": "This stake requires the low band.",
            "MED": "This stake requires the mid band.",
            "HIGH": "This stake requires the high band.",
            "VETO": "This stake requires a veto of the place path.",
        },
    ))
    pack.update(_choice_q(
        "conf_disposition",
        "What is the disposition of this confidence consume? "
        "The option you return is that disposition. "
        "An empty answer or a tie leaves it unset. "
        "Do not send.",
        {
            "veto_place_path": "This consume vetoes the place path.",
            "high_trust_blocked_for_place": "High trust is blocked for a place on this state.",
            "shadow_only": "This consume stays a shadow row.",
            "vendor_high_not_challenge_true": "A vendor high label is not the consume decision.",
            "shadow_review": "This consume stays in shadow review.",
            "consume_keep_if_sufficient": "This consume keeps the returned action when the state is sufficient.",
        },
    ))
    pack.update(_choice_q(
        "conf_place",
        "What place action does this consume return? "
        "The intended action on the state is a fact. "
        "The option you return is the action. "
        "An empty answer or a tie leaves the action unset. "
        "Do not send.",
        {
            "PLACE": "The returned action is place.",
            "STAND": "The returned action is stand.",
            "DELAY": "The returned action is delay.",
            "REMINT": "The returned action is remint.",
            "VETO": "The returned action is veto.",
        },
    ))
    pack.update(_choice_q(
        "conf_order_consume",
        "What note does this consume attach to the order block? "
        "The option you return is that note. "
        "An empty answer or a tie leaves the note unset. "
        "Do not send.",
        {
            "PLACE_to_DELAY": "This consume notes the place as delay.",
            "keep": "This consume adds no hold note.",
        },
    ))
    pack.update(_choice_q(
        "conf_component",
        "Which component exists on this confidence consume? "
        "The option you return is that component. "
        "An empty answer or a tie leaves the component unset. "
        "Do not send.",
        {
            "conf_gate": "The confidence consume gate is the component on this state.",
            "order_block": "The live confidence order block is the component on this state.",
            "high_trust": "The high-trust block is the component on this state.",
            "hash_receipt": "The receipt hashes are the component on this state.",
        },
    ))
    pack.update(_noul_q(
        "conf_high_trust",
        "Is high trust blocked for a place on this state? "
        "Flip rate, swing, and evidence sufficiency on the state are facts. "
        "The noul you return is that block. "
        "An empty noul leaves it unset. "
        "Do not send.",
    ))
    pack.update(_noul_q(
        "conf_hashes_ok",
        "Do the receipt hashes on this state satisfy this consume? "
        "The noul you return is that answer. "
        "An empty noul leaves it unset. "
        "Do not send.",
    ))
    pack.update(_noul_q(
        "conf_component_exists",
        "Does the component on this confidence consume exist? "
        "The noul you return is that existence. "
        "An empty noul leaves it unset. "
        "Do not send.",
    ))
    pack.update(_score_q(
        "conf_threshold",
        "The score you return is the threshold for this confidence consume. "
        "It may sit between the levels. "
        "An empty score leaves the threshold unset. "
        "Do not send.",
    ))
    pack.update(_score_q(
        "conf_loop",
        "The score you return is the loop bound for this confidence consume. "
        "It may sit between the levels. "
        "An empty score leaves the bound unset. "
        "Do not send.",
    ))
    pack.update(_score_q(
        "conf_parameter",
        "The score you return is the parameter for this confidence consume. "
        "It may sit between the levels. "
        "An empty score leaves the parameter unset. "
        "Do not send.",
    ))
    clean: dict[str, Any] = {}
    for qid, block in pack.items():
        if not isinstance(block, dict) or block.get("type") not in {"noul", "choice", "score"}:
            continue
        blob = json.dumps(block, default=str).lower()
        if _banned_text(blob) or _limit_key(blob):
            continue
        clean[qid] = block
    return clean


def _state(facts: Mapping[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {
        "gate": "conf_gate_consume",
        "login": CHALLENGE_LOGIN,
        "namespace": CHALLENGE_NS,
        "model": MODEL,
    }
    for key, value in facts.items():
        name = str(key)
        if name in state or _limit_key(name):
            continue
        cleaned = _scrub(value)
        if cleaned is None and value is not None:
            continue
        state[name] = cleaned
    return state


def _read(answers: Mapping[str, Any] | None, receipt_error: str | None) -> dict[str, Any]:
    payload = answers if isinstance(answers, Mapping) else {}
    band = _choice(payload.get("conf_band"), _BAND_ORDER)
    required = _choice(payload.get("conf_required_band"), _BAND_ORDER)
    disposition = _choice(payload.get("conf_disposition"), _DISPOSITION_ORDER)
    place_action = _choice(payload.get("conf_place"), _PLACE_ORDER)
    note = _choice(payload.get("conf_order_consume"), _NOTE_ORDER)
    component = _choice(payload.get("conf_component"), _COMPONENT_ORDER)
    high_trust = _noul(payload.get("conf_high_trust"))
    hashes_ok = _noul(payload.get("conf_hashes_ok"))
    component_exists = _noul(payload.get("conf_component_exists"))
    threshold = _score(payload.get("conf_threshold"))
    loop_bound = _score(payload.get("conf_loop"))
    parameter = _score(payload.get("conf_parameter"))
    return {
        "band": band,
        "required_band": required,
        "disposition": disposition,
        "place_action": place_action,
        "order_consume": note,
        "component": component,
        "high_trust_blocked": high_trust,
        "hashes_ok": hashes_ok,
        "component_exists": component_exists,
        "threshold": threshold,
        "loop_bound": loop_bound,
        "parameter": parameter,
        "ask_error": receipt_error,
        "band_error": _field_error(payload.get("conf_band"), band, _BAND_ORDER, receipt_error),
        "required_error": _field_error(payload.get("conf_required_band"), required, _BAND_ORDER, receipt_error),
        "disposition_error": _field_error(
            payload.get("conf_disposition"), disposition, _DISPOSITION_ORDER, receipt_error
        ),
        "place_error": _field_error(payload.get("conf_place"), place_action, _PLACE_ORDER, receipt_error),
        "note_error": _field_error(payload.get("conf_order_consume"), note, _NOTE_ORDER, receipt_error),
        "component_error": _field_error(
            payload.get("conf_component"), component, _COMPONENT_ORDER, receipt_error
        ),
        "high_trust_error": _field_error(
            payload.get("conf_high_trust"), high_trust, ("true", "false"), receipt_error
        ),
        "hashes_error": _field_error(
            payload.get("conf_hashes_ok"), hashes_ok, ("true", "false"), receipt_error
        ),
        "exists_error": _field_error(
            payload.get("conf_component_exists"), component_exists, ("true", "false"), receipt_error
        ),
        "threshold_error": _field_error(payload.get("conf_threshold"), threshold, (), receipt_error),
        "loop_error": _field_error(payload.get("conf_loop"), loop_bound, (), receipt_error),
        "parameter_error": _field_error(payload.get("conf_parameter"), parameter, (), receipt_error),
    }


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = [dict(item) for item in _LOCAL_OUTCOMES]
        return
    state["prior_outcomes"] = [] if loaded is None else loaded


def _remember(state: Mapping[str, Any], card: Mapping[str, Any]) -> None:
    rows = (
        ("conf_band", card.get("band"), card.get("band_error")),
        ("conf_required_band", card.get("required_band"), card.get("required_error")),
        ("conf_disposition", card.get("disposition"), card.get("disposition_error")),
        ("conf_place", card.get("place_action"), card.get("place_error")),
        ("conf_order_consume", card.get("order_consume"), card.get("note_error")),
        ("conf_component", card.get("component"), card.get("component_error")),
        ("conf_high_trust", card.get("high_trust_blocked"), card.get("high_trust_error")),
        ("conf_hashes_ok", card.get("hashes_ok"), card.get("hashes_error")),
        ("conf_component_exists", card.get("component_exists"), card.get("exists_error")),
        ("conf_threshold", card.get("threshold"), card.get("threshold_error")),
        ("conf_loop", card.get("loop_bound"), card.get("loop_error")),
        ("conf_parameter", card.get("parameter"), card.get("parameter_error")),
    )
    try:
        from .jev_questions import append_outcome
    except Exception:
        for key, value, error in rows:
            _LOCAL_OUTCOMES.append({
                "key": key,
                "value": value,
                "error": None if value is not None else error,
            })
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=None if value is not None else error)
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    ask: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    call = ask
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    receipt = call(state, questions=dict(questions), merge_sleeve=False)
    return receipt if isinstance(receipt, dict) else {"error": "evaluate_not_a_dict", "answers": {}}


def _ask(facts: Mapping[str, Any], ask: Callable[..., Any] | None = None) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. A miss stays unset."""

    state = _state(facts)
    _bind_card(state)
    questions = _questions()
    _bind_card(None)
    if not questions:
        return _read({}, "question_pack_fail")
    _attach_priors(state, questions)
    try:
        receipt = _post(state, questions, ask)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        card = _read({}, type(exc).__name__)
        _remember(state, card)
        return card
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None
    if not answers:
        raw = receipt.get("error") or receipt.get("skipped") or "empty"
        error = str(raw)
    card = _read(answers, error)
    if receipt.get("model"):
        card["model"] = receipt.get("model")
    else:
        card["model"] = MODEL
    _remember(state, card)
    return card


@dataclass(frozen=True)
class _VendorShadow:
    """Vendor row absent. Bands stay unset. This is not the consume decision."""

    confidence: float | None
    stake: str
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "confidence": self.confidence,
            "stake": self.stake,
            "source": self.source,
            "band": None,
            "required_band": None,
        }


def _vendor_inner(confidence: float | None, stake: str, source: str) -> Any:
    """Shadow row from the vendor log when that module is present.

    Its band is not the consume band.
    """

    log_conf_gate = None
    try:
        from .conf_gate import log_conf_gate as loaded
    except ImportError:
        loaded = None
    if loaded is None:
        try:
            import sys
            from pathlib import Path

            src = Path("/workspace/gtos/judgment/warroom_shadow/src")
            if str(src) not in sys.path:
                sys.path.insert(0, str(src))
            from judgment.conf_gate import log_conf_gate as loaded  # type: ignore
        except ImportError:
            loaded = None
    log_conf_gate = loaded
    if log_conf_gate is not None:
        try:
            return log_conf_gate(confidence, stake=stake, source=source)
        except Exception:
            pass
    return _VendorShadow(confidence=_finite(confidence), stake=stake, source=source)


def _vendor_band(inner: Any) -> str | None:
    band = getattr(inner, "band", None)
    if band is None and isinstance(inner, Mapping):
        band = inner.get("band")
    if band is None:
        return None
    text = str(band).strip()
    if not text or text.lower() in {"none", "null"}:
        return None
    return text


def _inner_dict(inner: Any) -> dict[str, Any]:
    method = getattr(inner, "as_dict", None)
    if not callable(method):
        return {}
    try:
        row = method()
    except Exception:
        return {}
    return row if isinstance(row, dict) else {}


@dataclass(frozen=True)
class ConfGateConsumeLog:
    """Consume row. The decision fields are the return. A miss stays unset.

    ``broker_effect`` stays false. This row does not authorize the apply flag
    and does not invent news.
    """

    vendor_band: str | None
    band: str | None
    stake: str
    required_band: str | None
    source: str
    disposition: str | None
    high_trust_blocked: bool | float | None
    place_action: str | None
    conf_order_consume: str | None
    threshold: float | None
    loop_bound: float | None
    parameter: float | None
    component: str | None
    component_exists: bool | float | None
    hashes_ok: bool | float | None
    vendor_0_85_forbidden_as_truth: bool
    gtos_jev_conf_gate_apply: bool
    broker_effect: bool
    news_invent: bool
    ask_error: str | None
    inner: Any
    model: str = MODEL

    def as_dict(self) -> dict[str, Any]:
        return {
            "vendor_band": self.vendor_band,
            "band": self.band,
            "stake": self.stake,
            "required_band": self.required_band,
            "source": self.source,
            "disposition": self.disposition,
            "high_trust_blocked": self.high_trust_blocked,
            "high_trust_blocked_for_place": self.high_trust_blocked,
            "place_action": self.place_action,
            "conf_order_consume": self.conf_order_consume,
            "threshold": self.threshold,
            "loop_bound": self.loop_bound,
            "parameter": self.parameter,
            "component": self.component,
            "component_exists": self.component_exists,
            "hashes_ok": self.hashes_ok,
            "vendor_0_85_forbidden_as_truth": True,
            "gtos_jev_conf_gate_apply": False,
            "broker_effect": False,
            "news_invent": False,
            "ask_error": self.ask_error,
            "model": self.model or MODEL,
            "inner": _inner_dict(self.inner),
        }


def _row(
    card: Mapping[str, Any],
    *,
    stake: str,
    source: str,
    confidence: float | None,
) -> ConfGateConsumeLog:
    inner = _vendor_inner(confidence, stake, source)
    return ConfGateConsumeLog(
        vendor_band=_vendor_band(inner),
        band=card.get("band") if isinstance(card.get("band"), str) else None,
        stake=stake,
        required_band=card.get("required_band") if isinstance(card.get("required_band"), str) else None,
        source=source,
        disposition=card.get("disposition") if isinstance(card.get("disposition"), str) else None,
        high_trust_blocked=card.get("high_trust_blocked"),
        place_action=card.get("place_action") if isinstance(card.get("place_action"), str) else None,
        conf_order_consume=card.get("order_consume") if isinstance(card.get("order_consume"), str) else None,
        threshold=_finite(card.get("threshold")),
        loop_bound=_finite(card.get("loop_bound")),
        parameter=_finite(card.get("parameter")),
        component=card.get("component") if isinstance(card.get("component"), str) else None,
        component_exists=card.get("component_exists"),
        hashes_ok=card.get("hashes_ok"),
        vendor_0_85_forbidden_as_truth=True,
        gtos_jev_conf_gate_apply=False,
        broker_effect=False,
        news_invent=False,
        ask_error=card.get("ask_error") if isinstance(card.get("ask_error"), str) else None,
        inner=inner,
        model=str(card.get("model") or MODEL),
    )


def conf_gate_bands_apply_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Env read of the apply flag. Consume does not authorize it."""

    env = environ if environ is not None else os.environ
    raw = str(env.get(CONF_GATE_APPLY_ENV, "")).strip().lower()
    return raw in _TRUTHY


def consume_high_trust_blocked(
    *,
    flip_rate: float | None = None,
    max_swing_pts: float | None = None,
    state_evidence_sufficiency_pass: bool | None = None,
) -> bool | float | None:
    """The high-trust block is the Noul on this ask. A miss stays unset."""

    card = _ask({
        "flip_rate": flip_rate,
        "max_swing_pts": max_swing_pts,
        "state_evidence_sufficiency_pass": state_evidence_sufficiency_pass,
    })
    return card.get("high_trust_blocked")


def place_action_after_consume(
    intended: str | None,
    *,
    high_trust_blocked: bool,
) -> str | None:
    """The place action is the Choice on this ask. A miss stays unset."""

    card = _ask({
        "intended_place_action": intended,
        "high_trust_blocked_fact": high_trust_blocked,
    })
    action = card.get("place_action")
    return action if isinstance(action, str) else None


def log_conf_gate_consume(
    confidence: float | None,
    *,
    stake: str,
    source: str = "choice_or_score_confidence",
    flip_rate: float | None = None,
    max_swing_pts: float | None = None,
    state_evidence_sufficiency_pass: bool | None = None,
    vendor_determinism_challenge_true: bool | None = None,
    intended_place_action: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> ConfGateConsumeLog:
    """One consume ask. The returned fields are the decision. A miss stays unset.

    ``GTOS_JEV_CONF_GATE_APPLY`` is read and is not authority.
    """

    _ = conf_gate_bands_apply_enabled(environ)
    card = _ask({
        "confidence": confidence,
        "stake": stake,
        "source": source,
        "flip_rate": flip_rate,
        "max_swing_pts": max_swing_pts,
        "state_evidence_sufficiency_pass": state_evidence_sufficiency_pass,
        "vendor_determinism_challenge_true": vendor_determinism_challenge_true,
        "intended_place_action": intended_place_action,
    })
    return _row(card, stake=stake, source=source, confidence=confidence)


def consume_ok_hashes(receipt: Mapping[str, object] | None) -> bool | float | None:
    """The hash check is the Noul on this ask. A miss stays unset."""

    card = _ask({"receipt": receipt})
    return card.get("hashes_ok")


def _unset(card: Mapping[str, Any]) -> None:
    for key in (
        "band",
        "required_band",
        "disposition",
        "place_action",
        "order_consume",
        "component",
        "high_trust_blocked",
        "hashes_ok",
        "component_exists",
        "threshold",
        "loop_bound",
        "parameter",
    ):
        assert card[key] is None, (key, card[key])


def smoke() -> dict[str, Any]:
    pack = _questions()
    assert pack, "question pack"
    blob = json.dumps(pack, default=str).lower()
    for token in ("floor", "baseline", "90000", "110000", "90k", "110k", "flatten", "order_send"):
        assert token not in blob, token
    for block in pack.values():
        assert block["type"] in {"noul", "choice", "score"}

    _unset(_read({}, "empty"))
    _unset(_read({}, "http_500"))
    tie = _read(
        {
            "conf_place": {"probabilities": {"PLACE": 0.4, "DELAY": 0.4}},
            "conf_band": {"probabilities": {"LOW": 0.5, "MED": 0.5}},
            "conf_threshold": {"probabilities": {"none": 0.5, "trace": 0.5}},
            "conf_high_trust": {"probabilities": {"true": 0.5, "false": 0.5}},
        },
        None,
    )
    assert tie["place_action"] is None
    assert tie["band"] is None
    assert tie["threshold"] is None
    assert tie["high_trust_blocked"] is None
    assert tie["place_error"] == "tie"

    hit = _read(
        {
            "conf_band": {"probabilities": {"LOW": 0.2, "MED": 0.7, "HIGH": 0.1}},
            "conf_required_band": {"probabilities": {"VETO": 0.91, "LOW": 0.05}},
            "conf_disposition": {"probabilities": {"shadow_only": 0.8, "shadow_review": 0.1}},
            "conf_place": {"probabilities": {"DELAY": 0.86, "PLACE": 0.1}},
            "conf_order_consume": {"probabilities": {"PLACE_to_DELAY": 0.77, "keep": 0.1}},
            "conf_component": {"probabilities": {"conf_gate": 0.84, "order_block": 0.1}},
            "conf_high_trust": {"noul": True},
            "conf_hashes_ok": {"noul": False},
            "conf_component_exists": {"noul": 0.55},
            "conf_threshold": {"score": 0.37},
            "conf_loop": {"score": 1.5},
            "conf_parameter": {"score": 0.63},
        },
        None,
    )
    assert hit["band"] == "MED"
    assert hit["required_band"] == "VETO"
    assert hit["disposition"] == "shadow_only"
    assert hit["place_action"] == "DELAY"
    assert hit["order_consume"] == "PLACE_to_DELAY"
    assert hit["component"] == "conf_gate"
    assert hit["high_trust_blocked"] is True
    assert hit["hashes_ok"] is False
    assert hit["component_exists"] == 0.55
    assert hit["threshold"] == 0.37
    assert hit["loop_bound"] == 1.5
    assert hit["parameter"] == 0.63

    bare = _read({"conf_place": "DELAY", "conf_band": "LOW"}, None)
    assert bare["place_action"] is None
    assert bare["band"] is None

    row = _row(_read({}, "empty"), stake="sleeve_admit", source="choice_or_score_confidence", confidence=0.99)
    card = row.as_dict()
    assert row.broker_effect is False
    assert row.news_invent is False
    assert row.gtos_jev_conf_gate_apply is False
    assert row.vendor_0_85_forbidden_as_truth is True
    assert card["broker_effect"] is False
    assert card["news_invent"] is False
    assert card["gtos_jev_conf_gate_apply"] is False
    assert card["vendor_0_85_forbidden_as_truth"] is True
    assert card["band"] is None
    assert card["place_action"] is None
    assert card["required_band"] is None
    assert card["disposition"] is None
    assert card["high_trust_blocked"] is None
    assert card["threshold"] is None
    assert card["loop_bound"] is None
    assert card["parameter"] is None

    seen: dict[str, Any] = {}

    def _fake(state: dict[str, Any], questions: Mapping[str, Any], merge_sleeve: bool = True) -> dict[str, Any]:
        seen["merge_sleeve"] = merge_sleeve
        seen["model"] = state.get("model")
        seen["priors"] = "prior_outcomes" in state
        seen["types"] = sorted({str(block.get("type")) for block in questions.values()})
        return {"error": "smoke_miss", "answers": {}, "model": MODEL}

    posted = _state({"stake": "sleeve_admit", "confidence": 0.99})
    _attach_priors(posted, pack)
    receipt = _post(posted, pack, ask=_fake)
    missed = _read(receipt.get("answers") or {}, str(receipt.get("error") or "empty"))
    _unset(missed)
    assert missed["ask_error"] == "smoke_miss"
    assert seen["merge_sleeve"] is False
    assert seen["model"] == MODEL
    assert seen["priors"] is True
    assert seen["types"] == ["choice", "noul", "score"]

    try:
        from .jev_client import API_URL
    except Exception:
        API_URL = None
    else:
        assert API_URL == "https://api.typesafe.ai/v1/systemone"
    return {"ok": True, "questions": list(pack), "model": MODEL, "api_url": API_URL}


if __name__ == "__main__":
    print(json.dumps(smoke(), indent=2, default=str))
