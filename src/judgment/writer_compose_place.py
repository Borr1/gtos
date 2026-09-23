"""Writer compose for a place receipt.

Each decision on this compose, including each parameter, is the System One
return for that state. One call: ``jev_client.evaluate`` with model
``jev-1.13.0`` and ``merge_sleeve=False``. That call POSTs
https://api.typesafe.ai/v1/systemone. Questions are only Noul, Choice, or
Score. Prior outcomes are attached on the ask, and the return is stored
for the next ask.

An empty answer, a tie, or an error leaves that return unset. It does not
restore a constant. Floor and baseline are not a question. This module
does not send and does not flatten.

Laws that stay structural: no broker call, no invented news protocol, env
integers untouched, the printer untouched.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.writer_compose_place.v1"

_ACTION_ORDER = ("PLACE", "STAND", "DELAY", "REMINT", "FLATTEN_CANDIDATE")
_REASON_ORDER = (
    "jev_place_compose_apply_off",
    "jev_place_compose_not_challenge",
    "jev_place_compose_unknown_action",
    "jev_place_choice_place",
    "jev_place_choice_stand",
    "jev_place_choice_delay",
    "jev_place_choice_remint",
    "jev_place_choice_flatten_candidate",
    "jev_place_compose_fail_closed",
)
_PREFER_ORDER = ("remint_sibling_reentry", "flatten_derisk")

_ACTION_CRITERIA = {
    "PLACE": "This compose is a fresh place.",
    "STAND": "This compose stands.",
    "DELAY": "This compose delays.",
    "REMINT": "This compose is a re-entry stamp.",
    "FLATTEN_CANDIDATE": "This compose names the flatten-candidate stamp.",
}
_REASON_CRITERIA = {
    "jev_place_compose_apply_off": "The compose reason is apply off.",
    "jev_place_compose_not_challenge": "The compose reason is outside the challenge book.",
    "jev_place_compose_unknown_action": "The compose reason is an unknown action.",
    "jev_place_choice_place": "The compose reason is place.",
    "jev_place_choice_stand": "The compose reason is stand.",
    "jev_place_choice_delay": "The compose reason is delay.",
    "jev_place_choice_remint": "The compose reason is remint.",
    "jev_place_choice_flatten_candidate": "The compose reason names the flatten-candidate stamp.",
    "jev_place_compose_fail_closed": "The compose reason is fail closed.",
}
_PREFER_CRITERIA = {
    "remint_sibling_reentry": "The prefer on this compose is a sibling re-entry.",
    "flatten_derisk": "The prefer on this compose is the derisk stamp.",
}

# History only when jev_questions cannot be imported. Never copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []

_SKIP_PARTS = ("floor", "baseline")
_SECRET_PARTS = ("api_key", "token", "secret", "authorization", "password")

_DECISIONS = (
    ("compose_action", "action", "choice", _ACTION_ORDER),
    ("allow_fresh_place", "allow_fresh_place", "noul", ()),
    ("remint_signal", "remint_signal", "noul", ()),
    ("flatten_candidate", "flatten_candidate", "noul", ()),
    ("refuse_admit", "refuse_admit", "noul", ()),
    ("apply_required", "apply_required", "noul", ()),
    ("challenge_scoped", "challenge_scoped", "noul", ()),
    ("compose_reason", "reason", "choice", _REASON_ORDER),
    ("compose_prefer", "prefer", "choice", _PREFER_ORDER),
    ("compose_parameter", "parameter", "score", ()),
    ("plain_depth", "plain_depth", "score", ()),
)

# Prior plain_depth for a receipt. The key is that receipt. A new receipt misses.
_PLAIN_DEPTH: dict[str, float] = {}



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


def _skip_key(key: str) -> bool:
    low = str(key).lower()
    return any(part in low for part in _SKIP_PARTS) or any(part in low for part in _SECRET_PARTS)


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


def _container(value: Any) -> bool:
    if isinstance(value, (str, bytes)):
        return False
    return isinstance(value, (Mapping, list, tuple))


def _plain(
    value: Any,
    depth: int = 0,
    bound: float | None = None,
    seen: set[int] | None = None,
) -> Any:
    """Receipt facts for the card.

    ``bound`` is the plain_depth already returned for this same receipt.
    A missing bound does not cut. A cycle stops the walk.
    """

    if bound is not None and depth > bound:
        return None
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(value) if isinstance(value, float) else value
    if not _container(value):
        return None
    trail = seen if seen is not None else set()
    marker = id(value)
    if marker in trail:
        return None
    trail.add(marker)
    try:
        if isinstance(value, Mapping):
            out: dict[str, Any] = {}
            for key, item in value.items():
                name = str(key)
                if _skip_key(name):
                    continue
                out[name] = _plain(item, depth + 1, bound, trail)
            return out
        return [_plain(item, depth + 1, bound, trail) for item in value]
    finally:
        trail.discard(marker)


def _nesting(value: Any, depth: int = 0, seen: set[int] | None = None) -> int:
    """How deep this receipt already is. A measurement, not a cut."""

    if not _container(value):
        return depth
    trail = seen if seen is not None else set()
    marker = id(value)
    if marker in trail:
        return depth
    trail.add(marker)
    try:
        if isinstance(value, Mapping):
            children = [item for key, item in value.items() if not _skip_key(str(key))]
        else:
            children = list(value)
        reached = depth
        for item in children:
            reached = max(reached, _nesting(item, depth + 1, trail))
        return reached
    finally:
        trail.discard(marker)


def _receipt_token(place_receipt: Mapping[str, Any] | None) -> str:
    plain = _plain(place_receipt)
    blob = json.dumps(plain, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
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



def _score_question(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {
                "true": "Yes, on this state.",
                "false": "No, on this state.",
            },
        }
    }


def compose_questions() -> dict[str, Any]:
    """One ask. The menu names what an answer may return. It does not decide."""

    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        "compose_action",
        "Which compose action is this state? "
        "The option with the single highest probability is the action. "
        "An empty answer or a tie leaves the action unset. "
        "This question does not send.",
        _ACTION_CRITERIA,
    ))
    pack.update(_noul_question(
        "allow_fresh_place",
        "Does this state allow a fresh place? "
        "The noul you return is that allowance. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_noul_question(
        "remint_signal",
        "Is remint_signal stamped on this compose? "
        "The noul you return is that stamp. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_noul_question(
        "flatten_candidate",
        "Is flatten_candidate stamped on this compose? "
        "The noul you return is that stamp. "
        "An empty noul leaves it unset. "
        "This question does not send and does not flatten.",
    ))
    pack.update(_noul_question(
        "refuse_admit",
        "Does this compose refuse admit? "
        "The noul you return is that refusal. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_noul_question(
        "apply_required",
        "Is apply required on this compose? "
        "The noul you return is that requirement. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_noul_question(
        "challenge_scoped",
        "Is this compose inside the challenge scope? "
        "The noul you return is that scope. "
        "An empty noul leaves it unset. "
        "This question does not send.",
    ))
    pack.update(_choice_question(
        "compose_reason",
        "Which reason is this compose? "
        "The option with the single highest probability is the reason. "
        "An empty answer or a tie leaves the reason unset. "
        "This question does not send.",
        _REASON_CRITERIA,
    ))
    pack.update(_choice_question(
        "compose_prefer",
        "Which prefer is this compose? "
        "The option with the single highest probability is the prefer. "
        "An empty answer or a tie leaves the prefer unset. "
        "This question does not send and does not flatten.",
        _PREFER_CRITERIA,
    ))
    pack.update(_score_question(
        "compose_parameter",
        "The score you return is the parameter for this compose. "
        "It may sit between the levels. "
        "An empty score leaves the parameter unset. "
        "This question does not send.",
    ))
    pack.update(_score_question(
        "plain_depth",
        "The score you return is how deep this receipt stays on the card "
        "the next time this same receipt is asked. "
        "receipt_nesting is how deep the receipt already is. "
        "An empty score leaves the depth unset and does not cut the receipt. "
        "This question does not send.",
    ))
    return pack


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, value in raw.items():
        number = _number(value)
        if number is None:
            continue
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
    """The choice is the unique highest probability. A label alone is not a choice."""

    if isinstance(block, dict) and block.get("error"):
        return None
    probabilities = _probabilities(block)
    if not probabilities:
        return None
    local = _present_unique(probabilities, order)
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probabilities, order)
    except Exception:
        agreed = local
    if local is None or agreed is None or str(agreed) != local:
        return None
    return local


def _noul(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if block is True or block is False:
        return block
    if not isinstance(block, dict):
        return _number(block)
    if block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        value = block.get("noul") if "noul" in block else block.get("Noul")
        if value is None:
            return None
        if value is True or value is False:
            return value
        return _number(value)
    probabilities = _probabilities(block)
    if not probabilities:
        return None
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> float | None:
    """The parameter is the returned score. A missing score stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "score" in block:
        raw = block.get("score")
    elif "value" in block:
        raw = block.get("value")
    else:
        return None
    if raw is None or isinstance(raw, bool):
        return None
    number = _number(raw)
    if number is None:
        return None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(block))
    except Exception:
        parsed = number
    if parsed is None or parsed != number:
        return None
    return number


def _state_from_receipt(
    place_receipt: Mapping[str, Any] | None,
    bound: float | None,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {}
    plain = _plain(place_receipt, bound=bound)
    if isinstance(plain, dict):
        receipt = plain
    receipt.pop("prior_outcomes", None)
    state = {
        "schema": SCHEMA,
        "model": MODEL,
        "gate": "writer_compose_place",
        "receipt": receipt,
        "receipt_nesting": _nesting(place_receipt),
    }
    if bound is not None:
        state["plain_depth_bound"] = bound
    return state


def _blank(error: str | None) -> dict[str, Any]:
    """Unset decisions. Broker and news marks are the module, not a restored answer."""

    return {
        "schema": SCHEMA,
        "action": None,
        "allow_fresh_place": None,
        "remint_signal": None,
        "flatten_candidate": None,
        "refuse_admit": None,
        "reason": None,
        "apply_required": None,
        "challenge_scoped": None,
        "prefer": None,
        "parameter": None,
        "plain_depth": None,
        "plain_depth_bound": None,
        "broker_calls": False,
        "news_invent": False,
        "model": MODEL,
        "error": error,
    }


def _read_answers(answers: Mapping[str, Any]) -> dict[str, Any]:
    row = _blank(None)
    for qid, field, kind, order in _DECISIONS:
        block = answers.get(qid)
        if kind == "choice":
            row[field] = _choice(block, order)
        elif kind == "noul":
            row[field] = _noul(block)
        else:
            row[field] = _score(block)
    return row


def _local_priors(questions: Mapping[str, Any]) -> list[dict[str, Any]]:
    del questions
    return [dict(item) for item in _LOCAL_OUTCOMES]


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = _local_priors(questions)
        return
    state["prior_outcomes"] = loaded if isinstance(loaded, list) else loaded


def _remember(state: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    error = row.get("error")
    pairs = [(qid, row.get(field)) for qid, field, _kind, _order in _DECISIONS]
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
    for key, value in pairs:
        try:
            append_outcome(
                key,
                value,
                logged,
                error=None if value is not None else (None if error is None else str(error)),
            )
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


def compose_writer_intent(
    place_receipt: Mapping[str, Any] | None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Compose a writer intent from the place receipt.

    The receipt is a fact on the state. The action, the nouls, the reason,
    the prefer, the parameter, and plain_depth are the System One return.
    plain_depth_bound is the prior plain_depth for this same receipt, or
    unset when this receipt has no prior return. A miss stays unset.
    This function does not send and does not flatten.
    """

    token = _receipt_token(place_receipt)
    bound = _PLAIN_DEPTH.get(token)
    state = _state_from_receipt(place_receipt, bound)
    _bind_card(state)
    questions = compose_questions()
    _bind_card(None)
    _attach_priors(state, questions)

    def _finish(row: dict[str, Any]) -> dict[str, Any]:
        row["plain_depth_bound"] = bound
        depth = row.get("plain_depth")
        if isinstance(depth, float):
            _PLAIN_DEPTH[token] = depth
        return row

    try:
        receipt = _post(state, questions, evaluate_fn)
    except Exception as exc:  # noqa: BLE001 — a failed ask must not raise into the writer
        row = _blank(type(exc).__name__)
        _remember(state, row)
        return _finish(row)
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = receipt.get("error") or receipt.get("skipped")
    if not answers and not error:
        error = "empty"
    if not answers:
        row = _blank(None if error in (None, "") else str(error))
        _remember(state, row)
        return _finish(row)
    row = _read_answers(answers)
    if receipt.get("model"):
        row["model"] = receipt.get("model")
    if error not in (None, ""):
        row["error"] = str(error)
    _remember(state, row)
    return _finish(row)


__all__ = ["compose_writer_intent"]
