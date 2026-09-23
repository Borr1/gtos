"""Ensemble place on the live place menu.

The choice, the place-now noul, sufficiency, the order-sensitivity noul,
whether the ensemble is preferred, whether the component exists, and the
threshold, loop bound, parameter, and digest width are the System One
returns for this state. Model ``jev-1.13.0``. The post is
``jev_client.evaluate`` (POST https://api.typesafe.ai/v1/systemone,
``merge_sleeve=False``). A return is a Noul, a Choice, or a Score.

Prior outcomes are attached on every ask, and the return is stored for
the next ask. An empty answer, a tie, a missing score, or an error leaves
that return unset. Env gates stay readers. This module does not send and
does not flatten.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Callable, Mapping, Sequence

MODEL = "jev-1.13.0"
PATTERN = "place_choice_ensemble_noul_pair"
CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off"})

# Aligned with live place_choice.PLACE_CRITERIA. The names are the menu.
PLACE_CRITERIA = {
    "PLACE": "This candidate is the order on this bar.",
    "STAND": "This candidate is not the order on this bar.",
    "DELAY": "This bar is not the bar for this candidate.",
    "REMINT": "A re-entry of an existing ticket fits this candidate.",
    "FLATTEN_CANDIDATE": "This candidate is a reduction of open risk.",
}
PLACE_ORDER = tuple(PLACE_CRITERIA)

_LIMIT_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "daily_loss_pct",
    "floor_room",
    "to_pass",
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

_Q_CHOICE = "ensemble_place"
_Q_PLACE_NOW = "place_now"
_Q_SUFFICIENT = "state_sufficient"
_Q_ORDER_BLOCK = "order_sensitivity_blocks"
_Q_PREFER = "prefer_ensemble"
_Q_COMPONENT = "ensemble_component"
_Q_THRESHOLD = "ensemble_threshold"
_Q_LOOP = "ensemble_loop"
_Q_PARAMETER = "ensemble_parameter"
_Q_WIDTH = "ensemble_width"



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
    low = name.strip().lower()
    if low in _LIMIT_KEYS:
        return True
    return "floor" in low or "baseline" in low


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED_TEXT)


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
            if _limit_key(name) or name.startswith("_mock"):
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
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
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
        if number is None:
            return
        text = format(number, ".10g")
        if _banned_text(text):
            return
        found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    if not found:
        return list(_BETWEEN)
    return [format(number, ".10g") for number in sorted(set(found))]


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    block: dict[str, Any] = {}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(criteria))
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        block = {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
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
                "true": "Yes on this state.",
                "false": "No on this state.",
            },
        }
    }


def ensemble_questions(
    criteria: Mapping[str, str] | None = None,
    levels: Sequence[str] | None = None,
) -> dict[str, Any]:
    """One pack. Choice, Noul, and Score only. No seeded answer."""

    _bind_card(levels)
    menu = dict(criteria) if criteria is not None else dict(PLACE_CRITERIA)
    scale = [str(item) for item in levels] if levels else list(_BETWEEN)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        _Q_CHOICE,
        (
            "Ensemble place on this state. "
            "Pick one option. The unique highest probability is the decision. "
            "An empty answer or a tie leaves the choice unset. "
            "Do not flatten. Do not send an order. Do not invent news."
        ),
        menu,
    ))
    pack.update(_noul_question(
        _Q_PLACE_NOW,
        (
            "Should this state place now? "
            "An empty answer leaves place-now unset. "
            "A probability, when returned, stays the noul. "
            "Do not flatten. Do not send an order."
        ),
    ))
    pack.update(_noul_question(
        _Q_SUFFICIENT,
        (
            "Is this state complete enough for the ensemble place? "
            "An empty answer leaves sufficiency unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_noul_question(
        _Q_ORDER_BLOCK,
        (
            "Does option-order sensitivity block a fire on this state? "
            "An empty answer leaves the block unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_noul_question(
        _Q_PREFER,
        (
            "Prefer the ensemble return on this state over a raw label already on the state? "
            "An empty answer leaves the preference unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_noul_question(
        _Q_COMPONENT,
        (
            "Does the ensemble component exist on this state? "
            "An empty answer leaves existence unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_score_question(
        _Q_THRESHOLD,
        (
            "The score you return is the threshold for this ensemble state. "
            "It may sit between the levels. "
            "An empty score leaves the threshold unset. "
            "Do not send an order."
        ),
        scale,
    ))
    pack.update(_score_question(
        _Q_LOOP,
        (
            "The score you return is how many ensemble readings belong on this state. "
            "It may sit between the levels. "
            "An empty score leaves the bound unset and adds no reading. "
            "Do not send an order."
        ),
        scale,
    ))
    pack.update(_score_question(
        _Q_PARAMETER,
        (
            "The score you return is the parameter for this ensemble state. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "Do not send an order."
        ),
        scale,
    ))
    pack.update(_score_question(
        _Q_WIDTH,
        (
            "The score you return is the digest prefix width on this ensemble stamp. "
            "It may sit between the levels. "
            "An empty score leaves the width unset. "
            "Do not send an order."
        ),
        scale,
    ))
    return pack


def menu_hash(criteria: Mapping[str, str]) -> str:
    items = sorted((str(key), str(criteria[key])) for key in criteria)
    return hashlib.sha256(json.dumps(items, separators=(",", ":")).encode()).hexdigest()


def option_order_hash(order: Sequence[str]) -> str:
    return hashlib.sha256("\0".join(str(key) for key in order).encode()).hexdigest()


def _prefix(digest: str, width: float | None) -> str:
    """Keep the digest out to the returned width. A missing width keeps the digest."""

    if width is None:
        return digest
    kept: list[str] = []
    while len(kept) < width and len(kept) < len(digest):
        kept.append(digest[len(kept)])
    return "".join(kept)


def od13_ensemble_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """GTOS_JEV_OD13_ENSEMBLE — default ON when PLACE_APPLY=1; explicit off wins."""
    env = environ if environ is not None else os.environ
    explicit = str(env.get("GTOS_JEV_OD13_ENSEMBLE", "")).strip().lower()
    if explicit in _FALSY:
        return False
    if explicit in _TRUTHY:
        return True
    legacy = str(env.get("GTOS_JEV_PLACE_ENSEMBLE", "")).strip().lower()
    if legacy in _FALSY:
        return False
    if legacy in _TRUTHY:
        return True
    apply = str(env.get("GTOS_JEV_PLACE_APPLY", "")).strip().lower()
    return apply in _TRUTHY


def conf_order_consume_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Detect CONF_ORDER_CONSUME: GTOS_JEV_CONF_ORDER_CONSUME or APPLY-on Challenge-live."""
    env = environ if environ is not None else os.environ
    for key in (
        "GTOS_JEV_CONF_ORDER_CONSUME",
        "GTOS_JEV_CONF_ORDER_CONSUME_APPLY",
        "GTOS_CONF_ORDER_CONSUME",
    ):
        raw = str(env.get(key, "")).strip().lower()
        if raw in _FALSY:
            return False
        if raw in _TRUTHY:
            return True
    apply = str(env.get("GTOS_JEV_PLACE_APPLY", "")).strip().lower()
    return apply in _TRUTHY


def _local_unique(numeric: Mapping[str, float], order: Sequence[str]) -> str | None:
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


def _choice(block: Any, order: Sequence[str]) -> tuple[str | None, dict[str, float]]:
    if not isinstance(block, dict):
        return None, {}
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "choice":
        return None, {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return None, {}
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
    if not numeric:
        return None, {}
    local = _local_unique(numeric, order)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(numeric), tuple(order))
    except Exception:
        picked = local
    if picked is None or local is None or str(picked) != local:
        return None, numeric
    return local, numeric


def _score(block: Any) -> float | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "score":
        return None
    if block.get("error"):
        return None
    raw = block.get("score")
    if raw is None and "value" in block:
        raw = block.get("value")
    if raw is None:
        return None
    parsed = _finite(raw)
    if parsed is not None:
        return parsed
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        return None


def _noul(block: Any) -> bool | float | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "noul":
        return None
    if "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _finite(raw)


def _stored_noul(value: Any) -> bool | float | None:
    if value is True or value is False:
        return value
    return _finite(value)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
        state["prior_outcomes"] = loaded if loaded is not None else []
    except Exception:
        state["prior_outcomes"] = []


def _remember(state: Mapping[str, Any], pairs: tuple[tuple[str, Any, str | None], ...]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    for key, value, error in pairs:
        try:
            append_outcome(key, value, state, error=error)
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> tuple[dict[str, Any], str | None]:
    _attach_priors(state, questions)
    state["model"] = MODEL
    try:
        call = evaluate_fn
        if call is None:
            from .jev_client import evaluate

            call = evaluate
        receipt = call(
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
    if not isinstance(answers, dict):
        answers = {}
    error = None
    if not answers:
        error = receipt.get("error") or receipt.get("skipped") or "empty"
    elif receipt.get("ok") is False:
        error = receipt.get("error") or receipt.get("skipped") or "post_failed"
    if error in (None, ""):
        return answers, None
    return {}, str(error)


def _env_facts(environ: Mapping[str, str] | None) -> dict[str, str]:
    env = environ if environ is not None else os.environ
    keys = (
        "GTOS_JEV_PLACE_APPLY",
        "GTOS_JEV_OD13_ENSEMBLE",
        "GTOS_JEV_PLACE_ENSEMBLE",
        "GTOS_JEV_CONF_ORDER_CONSUME",
        "GTOS_JEV_CONF_ORDER_CONSUME_APPLY",
        "GTOS_CONF_ORDER_CONSUME",
    )
    return {key: str(env.get(key, "")) for key in keys}


def _post_state(
    facts: Mapping[str, Any] | None,
    environ: Mapping[str, str] | None,
) -> dict[str, Any]:
    cleaned = _scrub(dict(facts or {}))
    state = cleaned if isinstance(cleaned, dict) else {}
    state.pop("prior_outcomes", None)
    state.update(_env_facts(environ))
    state["model"] = MODEL
    state.setdefault("login", CHALLENGE_LOGIN)
    state.setdefault("ns", CHALLENGE_NS)
    return state


def _blank(
    *,
    error: str | None,
    menu: str | None,
    order_hash: str | None,
    option_order: Sequence[str],
) -> dict[str, Any]:
    return {
        "pattern": PATTERN,
        "model": MODEL,
        "action": None,
        "choice": None,
        "probabilities": {},
        "unique_highest": False,
        "place_now": None,
        "state_sufficient": None,
        "order_sensitivity_blocks": None,
        "prefer_ensemble": None,
        "component_exists": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "width": None,
        "menu_hash": menu,
        "option_order_hash": order_hash,
        "option_order": [str(key) for key in option_order],
        "broker_effect": False,
        "error": error,
    }


def _remember_row(state: Mapping[str, Any], row: Mapping[str, Any], error: str | None) -> None:
    fields = (
        (_Q_CHOICE, row.get("choice"), "tie_or_empty"),
        (_Q_PLACE_NOW, row.get("place_now"), "noul_missing"),
        (_Q_SUFFICIENT, row.get("state_sufficient"), "noul_missing"),
        (_Q_ORDER_BLOCK, row.get("order_sensitivity_blocks"), "noul_missing"),
        (_Q_PREFER, row.get("prefer_ensemble"), "noul_missing"),
        (_Q_COMPONENT, row.get("component_exists"), "noul_missing"),
        (_Q_THRESHOLD, row.get("threshold"), "score_missing"),
        (_Q_LOOP, row.get("loop_bound"), "score_missing"),
        (_Q_PARAMETER, row.get("parameter"), "score_missing"),
        (_Q_WIDTH, row.get("width"), "score_missing"),
    )
    pairs = tuple(
        (key, value, None if value is not None else (error or miss))
        for key, value, miss in fields
    )
    _remember(state, pairs)


def ensemble_place_choice(
    state: Mapping[str, Any] | None = None,
    *,
    criteria: Mapping[str, str] | None = None,
    seeds: Sequence[int] | None = None,
    required_fields: Sequence[str] | None = None,
    mock_dists: Mapping[str, Mapping[str, float]] | None = None,
    environ: Mapping[str, str] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """The ensemble place for this state is the return on one ask.

    ``seeds``, ``required_fields``, and ``mock_dists`` are not decisions.
    A miss stays unset. This hop does not send and does not flatten.
    """

    del seeds, required_fields, mock_dists
    menu = {str(key): str(value) for key, value in (criteria if criteria is not None else PLACE_CRITERIA).items()}
    order = tuple(menu)
    full_menu = menu_hash(menu) if menu else None
    full_order = option_order_hash(order) if order else None
    try:
        posted = _post_state(state, environ)
        questions = ensemble_questions(menu, posted)
        answers, error = _post(posted, questions, evaluate_fn)
    except Exception as exc:
        return _blank(error=type(exc).__name__, menu=full_menu, order_hash=full_order, option_order=order)

    if error or not answers:
        row = _blank(
            error=error or "empty",
            menu=full_menu,
            order_hash=full_order,
            option_order=order,
        )
        _remember_row(posted, row, row["error"])
        return row

    choice, probs = _choice(answers.get(_Q_CHOICE), order)
    width = _score(answers.get(_Q_WIDTH))
    row = {
        "pattern": PATTERN,
        "model": MODEL,
        "action": choice,
        "choice": choice,
        "probabilities": probs,
        "unique_highest": choice is not None,
        "place_now": _noul(answers.get(_Q_PLACE_NOW)),
        "state_sufficient": _noul(answers.get(_Q_SUFFICIENT)),
        "order_sensitivity_blocks": _noul(answers.get(_Q_ORDER_BLOCK)),
        "prefer_ensemble": _noul(answers.get(_Q_PREFER)),
        "component_exists": _noul(answers.get(_Q_COMPONENT)),
        "threshold": _score(answers.get(_Q_THRESHOLD)),
        "loop_bound": _score(answers.get(_Q_LOOP)),
        "parameter": _score(answers.get(_Q_PARAMETER)),
        "width": width,
        "menu_hash": None if full_menu is None else _prefix(full_menu, width),
        "option_order_hash": None if full_order is None else _prefix(full_order, width),
        "option_order": [str(key) for key in order],
        "broker_effect": False,
        "error": None,
    }
    _remember_row(posted, row, None)
    return row


def build_ensemble_state(
    intent: Any = None,
    *,
    extra: Mapping[str, Any] | None = None,
    answers: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Facts for the ask. News stays out. A prior label is not the decision."""

    symbol = sleeve = side = ""
    discriminating_span = None
    if intent is not None:
        symbol = str(getattr(intent, "symbol", None) or getattr(intent, "instrument", None) or "")
        sleeve = str(getattr(intent, "sleeve", None) or getattr(intent, "tag", None) or "")
        side = str(getattr(intent, "side", None) or getattr(intent, "direction", None) or "")
        details = getattr(intent, "details", None)
        if isinstance(details, dict):
            symbol = symbol or str(details.get("symbol") or "")
            sleeve = sleeve or str(details.get("sleeve") or details.get("tag") or "")
            side = side or str(details.get("side") or "")
            discriminating_span = details.get("discriminating_span")
    st: dict[str, Any] = {
        "symbol": symbol,
        "sleeve": sleeve,
        "side": side,
        "tag": sleeve,
    }
    if discriminating_span not in (None, ""):
        st["discriminating_span"] = discriminating_span
    if extra:
        for key, value in extra.items():
            name = str(key)
            low = name.lower()
            if low in {"news", "news_protocol", "on_surface"} or "news" in low:
                continue
            if name.startswith("_mock"):
                continue
            st[name] = value
        if st.get("discriminating_span") in (None, "") and extra.get("discriminating_span"):
            st["discriminating_span"] = extra["discriminating_span"]
    if isinstance(answers, Mapping):
        if st.get("discriminating_span") in (None, ""):
            disc = answers.get("discriminating_span") or answers.get("span")
            if isinstance(disc, dict):
                disc = disc.get("answer") or disc.get("value") or disc.get("text")
            if disc not in (None, ""):
                st["discriminating_span"] = disc
    cleaned = _scrub(st)
    return cleaned if isinstance(cleaned, dict) else {}


def prefer_ensemble_action(
    *,
    typesafe_action: str | None,
    typesafe_dark: bool,
    ens: Mapping[str, Any],
    environ: Mapping[str, str] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> bool | float | None:
    """The preference is the noul on this state. A dark flag is not that noul."""

    if isinstance(ens, Mapping) and _Q_PREFER in ens:
        return _stored_noul(ens.get(_Q_PREFER))
    posted = _post_state(
        {
            "typesafe_action": None if typesafe_action is None else str(typesafe_action),
            "typesafe_dark": bool(typesafe_dark),
            "ensemble_action": None if not isinstance(ens, Mapping) else ens.get("action"),
        },
        environ,
    )
    questions = _noul_question(
        _Q_PREFER,
        (
            "Prefer the ensemble return on this state over a raw label already on the state? "
            "An empty answer leaves the preference unset. "
            "Do not send an order."
        ),
    )
    try:
        answers, error = _post(posted, questions, evaluate_fn)
    except Exception:
        return None
    value = None if error else _noul(answers.get(_Q_PREFER))
    _remember(
        posted,
        ((_Q_PREFER, value, None if value is not None else (error or "noul_missing")),),
    )
    return value


def main() -> None:
    sample = build_ensemble_state(
        type("Intent", (), {
            "symbol": "XAUUSD",
            "sleeve": "spring",
            "side": "buy",
            "details": {},
        })(),
    )
    print(json.dumps(ensemble_place_choice(sample), indent=2, default=str))


if __name__ == "__main__":
    main()
