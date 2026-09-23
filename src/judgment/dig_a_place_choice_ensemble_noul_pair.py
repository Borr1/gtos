"""Pair the ensemble place and the place-now noul on the live place menu.

Every decision on this state, including each parameter, is the System One
return. One hop: ``jev_client.evaluate`` with model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
Questions are only Noul, Choice, or Score. Prior outcomes are attached
on that ask, and the return is stored for the next ask.

An empty answer, a tie, a missing score, or an error leaves that field
unset. Floor and baseline are not asked. This module does not send and
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

PLACE_CRITERIA = {
    "PLACE": "Fire now — state discriminating; identity/sleeve/side ready",
    "STAND": "Do not place this cycle — refuse admit / skip fire",
    "DELAY": "Wait — incomplete or ambiguous; retry next cycle",
    "REMINT": "Prefer remint sibling / re-entry path over fresh place",
    "FLATTEN_CANDIDATE": "Prefer flatten/derisk over new risk",
}

REASON_CRITERIA = {
    "noul_and_ensemble_agree_place": "The place-now noul and the ensemble pick both name place.",
    "noul_blocks_ensemble_place": "The place-now noul withholds while the ensemble pick names place.",
    "ensemble_non_place": "The ensemble pick names a side other than place.",
    "thin_state_order_becomes_policy": "The order on a thin state is the policy for this cycle.",
}

_Q_ACTION = "dig_pair_action"
_Q_ENSEMBLE = "dig_pair_ensemble"
_Q_REASON = "dig_pair_reason"
_Q_PLACE_NOW = "dig_pair_place_now"
_Q_SUFFICIENT = "dig_pair_sufficient"
_Q_PLACE = "dig_pair_place"
_Q_APPLY = "dig_pair_apply"
_Q_SHADOW = "dig_pair_shadow"
_Q_COMPONENT = "dig_pair_component"
_Q_THRESHOLD = "dig_pair_threshold"
_Q_LOOP = "dig_pair_loop"
_Q_PARAMETER = "dig_pair_parameter"
_Q_EVIDENCE = "dig_pair_evidence"
_Q_WIDTH = "dig_pair_width"

_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
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
    "90K",
    "110000",
    "110,000",
    "110_000",
    "110k",
    "110K",
)
_DROP = object()
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
    low = str(name).strip().lower().replace("-", "_")
    if low in _LIMIT_KEYS:
        return True
    return "floor" in low or "baseline" in low


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    return any(token.replace(",", "").replace("_", "").lower() in compact for token in _BANNED_TEXT)


def _scrub_text(value: str) -> str:
    cleaned = str(value)
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
            if _limit_key(name) or name.startswith("_mock") or name in {"mock_dists", "seeds"}:
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
        return _scrub_text(value)
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if _banned_text(format(value, ".10g")):
            return _DROP
        return value
    return _scrub_text(str(value))


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
    text = _scrub_text(instructions)
    menu = {
        str(key): _scrub_text(str(value))
        for key, value in criteria.items()
        if not _limit_key(str(key)) and not _banned_text(str(value))
    }
    block: dict[str, Any] = {}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, menu)
        raw = built.get(qid) if isinstance(built, dict) else None
        if isinstance(raw, dict):
            block = dict(raw)
    except Exception:
        block = {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        block.pop(key, None)
    block["type"] = "choice"
    block["instructions"] = text
    block["criteria"] = menu
    return {qid: block}



def _score_question(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _noul_question(qid: str, instructions: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(instructions),
            "criteria": {
                "true": "Yes on this state.",
                "false": "No on this state.",
            },
        }
    }


def pair_questions(
    criteria: Mapping[str, str] | None = None,
    levels: Sequence[str] | None = None,
) -> dict[str, Any]:
    """One pack. A question is a Noul, a Choice, or a Score."""

    _bind_card(levels)
    menu = dict(criteria) if criteria is not None else dict(PLACE_CRITERIA)
    scale = [str(item) for item in levels] if levels else list(_BETWEEN)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        _Q_ACTION,
        (
            "Paired place for this state. "
            "The unique highest probability is the action. "
            "An empty answer or a tie leaves the action unset. "
            "Do not send an order. Do not flatten."
        ),
        menu,
    ))
    pack.update(_choice_question(
        _Q_ENSEMBLE,
        (
            "Ensemble pick for this state. "
            "The unique highest probability is the pick. "
            "An empty answer or a tie leaves the pick unset. "
            "Do not send an order. Do not flatten."
        ),
        menu,
    ))
    pack.update(_choice_question(
        _Q_REASON,
        (
            "Reason for this paired place. "
            "The unique highest probability is the reason. "
            "An empty answer or a tie leaves the reason unset. "
            "Do not send an order."
        ),
        REASON_CRITERIA,
    ))
    pack.update(_noul_question(
        _Q_PLACE_NOW,
        (
            "Should this state place now? "
            "The noul you return is that answer, a bool or a probability. "
            "An empty answer leaves place-now unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_noul_question(
        _Q_SUFFICIENT,
        (
            "Is this state complete enough for the paired place? "
            "An empty answer leaves sufficiency unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_noul_question(
        _Q_PLACE,
        (
            "Does this pair place on this state? "
            "An empty answer leaves place unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_noul_question(
        _Q_APPLY,
        (
            "Does this pair apply on this state? "
            "An empty answer leaves apply unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_noul_question(
        _Q_SHADOW,
        (
            "Is this pair a shadow reading on this state? "
            "An empty answer leaves shadow unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_noul_question(
        _Q_COMPONENT,
        (
            "Does this pair component exist on this state? "
            "An empty answer leaves existence unset. "
            "Do not send an order."
        ),
    ))
    pack.update(_score_question(
        _Q_THRESHOLD,
        (
            "The score you return is the threshold for this pair. "
            "It may sit between the levels. "
            "An empty score leaves the threshold unset. "
            "Do not send an order."
        ),
        scale,
    ))
    pack.update(_score_question(
        _Q_LOOP,
        (
            "The score you return is how many pair readings belong on this state. "
            "It may sit between the levels. "
            "An empty score leaves the bound unset and adds no reading. "
            "Do not send an order."
        ),
        scale,
    ))
    pack.update(_score_question(
        _Q_PARAMETER,
        (
            "The score you return is the parameter for this pair. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "Do not send an order."
        ),
        scale,
    ))
    pack.update(_score_question(
        _Q_EVIDENCE,
        (
            "The score you return is the evidence weight on this state. "
            "It may sit between the levels. "
            "An empty score leaves the weight unset. "
            "Do not send an order."
        ),
        scale,
    ))
    pack.update(_score_question(
        _Q_WIDTH,
        (
            "The score you return is the digest prefix width on this pair stamp. "
            "It may sit between the levels. "
            "An empty score leaves the width unset and the digest stays whole. "
            "Do not send an order."
        ),
        scale,
    ))
    return {
        qid: block
        for qid, block in pack.items()
        if isinstance(block, dict) and str(block.get("type") or "").lower() in {"noul", "choice", "score"}
        and not _limit_key(qid)
    }


def menu_hash(criteria: Mapping[str, str]) -> str:
    items = sorted((str(key), str(criteria[key])) for key in criteria)
    return hashlib.sha256(json.dumps(items, separators=(",", ":")).encode()).hexdigest()


def option_order_hash(order: Sequence[str]) -> str:
    return hashlib.sha256("\0".join(str(key) for key in order).encode()).hexdigest()


def _prefix(digest: str, width: float | None) -> str:
    """A returned width shortens the digest. A missing width keeps the digest."""

    if width is None:
        return digest
    kept: list[str] = []
    while len(kept) < width and len(kept) < len(digest):
        kept.append(digest[len(kept)])
    return "".join(kept)


def _local_unique(numeric: Mapping[str, float], order: Sequence[str]) -> str | None:
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in order:
        if name not in numeric:
            continue
        prob = numeric[name]
        seen = True
        if best_p is None or prob > best_p:
            best = name
            best_p = prob
            tied = False
        elif prob == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: Sequence[str]) -> tuple[str | None, dict[str, float]]:
    if not isinstance(block, dict):
        return None, {}
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "choice":
        return None, {}
    if block.get("error"):
        return None, {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return None, {}
    allowed = [str(name) for name in order]
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
    local = _local_unique(numeric, allowed)
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(numeric), tuple(allowed))
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
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        if "score" in block and block.get("score") is not None:
            return _finite(block.get("score"))
        return None


def _noul(block: Any) -> bool | float | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "noul":
        return None
    if block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return None
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is None:
            continue
        numeric[str(key)] = number
    local = _local_unique(numeric, ("true", "false"))
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(numeric), ("true", "false"))
    except Exception:
        picked = local
    if picked is None or local is None or str(picked) != local:
        return None
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
        state["prior_outcomes"] = loaded if loaded is not None else []
    except Exception:
        state["prior_outcomes"] = [dict(row) for row in _LOCAL_OUTCOMES]


def _remember(state: Mapping[str, Any], pairs: tuple[tuple[str, Any, str | None], ...]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        append_outcome = None
    for key, value, error in pairs:
        if append_outcome is not None:
            try:
                append_outcome(key, value, state, error=error)
                continue
            except Exception:
                pass
        _LOCAL_OUTCOMES.append({
            "spot": key,
            "value": value,
            "error": error,
        })


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


def _env_apply(environ: Mapping[str, str] | None) -> str:
    env = environ if environ is not None else os.environ
    return str(env.get("GTOS_JEV_PLACE_APPLY", ""))


def _presence(facts: Mapping[str, Any], required: Sequence[str] | None) -> dict[str, Any] | None:
    if not required:
        return None
    names = [str(item) for item in required]
    present = [
        name for name in names
        if facts.get(name) not in (None, "", [], {})
    ]
    return {"named_fields": names, "fields_present": present}


def _post_state(
    facts: Mapping[str, Any] | None,
    required: Sequence[str] | None,
    environ: Mapping[str, str] | None,
) -> dict[str, Any]:
    cleaned = _scrub(dict(facts or {}))
    state = cleaned if isinstance(cleaned, dict) else {}
    state.pop("prior_outcomes", None)
    state.pop("action", None)
    state.pop("reason", None)
    state.pop("ensemble_pick", None)
    presence = _presence(state, required)
    if presence is not None:
        state["named_fields"] = presence["named_fields"]
        state["fields_present"] = presence["fields_present"]
    state["apply_env"] = _env_apply(environ)
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
    apply_env: str,
    noul_question: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "pattern": PATTERN,
        "model": MODEL,
        "action": None,
        "reason": None,
        "evidence_score": None,
        "noul_place_p": None,
        "noul_fire": None,
        "ensemble_pick": None,
        "avg_probs": None,
        "menu_hash": menu,
        "option_order_hash": order_hash,
        "option_order": [str(key) for key in option_order],
        "shuffles": None,
        "noul_question": None if noul_question is None else dict(noul_question),
        "place": None,
        "apply": None,
        "shadow": None,
        "state_sufficient": None,
        "component_exists": None,
        "threshold": None,
        "loop_bound": None,
        "parameter": None,
        "width": None,
        "apply_env": apply_env,
        "broker_effect": False,
        "news_invent": False,
        "error": error,
    }


def _remember_row(state: Mapping[str, Any], row: Mapping[str, Any], error: str | None) -> None:
    fields = (
        (_Q_ACTION, row.get("action"), "tie_or_empty"),
        (_Q_ENSEMBLE, row.get("ensemble_pick"), "tie_or_empty"),
        (_Q_REASON, row.get("reason"), "tie_or_empty"),
        (_Q_PLACE_NOW, row.get("noul_fire"), "noul_missing"),
        (_Q_SUFFICIENT, row.get("state_sufficient"), "noul_missing"),
        (_Q_PLACE, row.get("place"), "noul_missing"),
        (_Q_APPLY, row.get("apply"), "noul_missing"),
        (_Q_SHADOW, row.get("shadow"), "noul_missing"),
        (_Q_COMPONENT, row.get("component_exists"), "noul_missing"),
        (_Q_THRESHOLD, row.get("threshold"), "score_missing"),
        (_Q_LOOP, row.get("loop_bound"), "score_missing"),
        (_Q_PARAMETER, row.get("parameter"), "score_missing"),
        (_Q_EVIDENCE, row.get("evidence_score"), "score_missing"),
        (_Q_WIDTH, row.get("width"), "score_missing"),
    )
    pairs = tuple(
        (key, value, None if value is not None else (error or miss))
        for key, value, miss in fields
    )
    _remember(state, pairs)


def _filled(
    answers: Mapping[str, Any],
    *,
    menu: str | None,
    order_hash: str | None,
    option_order: Sequence[str],
    apply_env: str,
    noul_question: Mapping[str, Any] | None,
) -> dict[str, Any]:
    action, _action_probs = _choice(answers.get(_Q_ACTION), option_order)
    ensemble, ensemble_probs = _choice(answers.get(_Q_ENSEMBLE), option_order)
    reason, _reason_probs = _choice(answers.get(_Q_REASON), tuple(REASON_CRITERIA))
    noul_fire = _noul(answers.get(_Q_PLACE_NOW))
    noul_p = noul_fire if isinstance(noul_fire, float) else None
    width = _score(answers.get(_Q_WIDTH))
    return {
        "pattern": PATTERN,
        "model": MODEL,
        "action": action,
        "reason": reason,
        "evidence_score": _score(answers.get(_Q_EVIDENCE)),
        "noul_place_p": noul_p,
        "noul_fire": noul_fire,
        "ensemble_pick": ensemble,
        "avg_probs": ensemble_probs or None,
        "menu_hash": None if menu is None else _prefix(menu, width),
        "option_order_hash": None if order_hash is None else _prefix(order_hash, width),
        "option_order": [str(key) for key in option_order],
        "shuffles": None,
        "noul_question": None if noul_question is None else dict(noul_question),
        "place": _noul(answers.get(_Q_PLACE)),
        "apply": _noul(answers.get(_Q_APPLY)),
        "shadow": _noul(answers.get(_Q_SHADOW)),
        "state_sufficient": _noul(answers.get(_Q_SUFFICIENT)),
        "component_exists": _noul(answers.get(_Q_COMPONENT)),
        "threshold": _score(answers.get(_Q_THRESHOLD)),
        "loop_bound": _score(answers.get(_Q_LOOP)),
        "parameter": _score(answers.get(_Q_PARAMETER)),
        "width": width,
        "apply_env": apply_env,
        "broker_effect": False,
        "news_invent": False,
        "error": None,
    }


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
    """The paired place for this state is the return on one ask.

    Seeds and mock distributions stay off this ask. A miss stays unset.
    This hop does not send and does not flatten.
    """

    del seeds, mock_dists
    menu = {
        str(key): str(value)
        for key, value in (criteria if criteria is not None else PLACE_CRITERIA).items()
        if not _limit_key(str(key))
    }
    order = tuple(menu)
    full_menu = menu_hash(menu) if menu else None
    full_order = option_order_hash(order) if order else None
    apply_env = _env_apply(environ)
    try:
        posted = _post_state(state, required_fields, environ)
        questions = pair_questions(menu, posted)
        noul_question = questions.get(_Q_PLACE_NOW)
        answers, error = _post(posted, questions, evaluate_fn)
    except Exception as exc:
        return _blank(
            error=type(exc).__name__,
            menu=full_menu,
            order_hash=full_order,
            option_order=order,
            apply_env=apply_env,
            noul_question=None,
        )

    if error or not answers:
        row = _blank(
            error=error or "empty",
            menu=full_menu,
            order_hash=full_order,
            option_order=order,
            apply_env=apply_env,
            noul_question=noul_question if isinstance(noul_question, Mapping) else None,
        )
        _remember_row(posted, row, row["error"])
        return row

    row = _filled(
        answers,
        menu=full_menu,
        order_hash=full_order,
        option_order=order,
        apply_env=apply_env,
        noul_question=noul_question if isinstance(noul_question, Mapping) else None,
    )
    _remember_row(posted, row, None)
    return row


def main() -> None:
    sample = {
        "symbol": "XAUUSD",
        "sleeve": "spring",
        "side": "buy",
        "discriminating_span": "M15 bounce at session VWAP",
    }
    print(json.dumps(ensemble_place_choice(sample), indent=2, default=str))


if __name__ == "__main__":
    main()
