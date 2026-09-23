"""Challenge manage sends are one Choice each.

SL modify, TP modify, close, and the pending REMOVE send each ask Jev
for that exact act. The Choice is the option with the unique highest
probability among leave_orig, move_sl, move_tp, close, and hold. A tie
is not a decision. The stop, the target, and the persist weight are the
Scores on that state. A Score may sit between the levels on the state.
An empty answer, a tie, a missing score, or an error leaves the return
unset and does not restore a constant. This module never calls
order_send. Friends copy the recorded result.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.manage_choices.v1"

ACTS = ("move_sl", "move_tp", "close", "remove", "scale_out")
LIFE_ID = "manage_life"
OPTIONS = ("move_sl", "scale_out", "close", "let_it_run", "move_tp")

CRITERIA = {
    "move_sl": "Move the stop. The stop is the score on manage_sl_price.",
    "scale_out": "Scale out. The scale is the score on manage_scale.",
    "close": "Close this ticket, or cancel this pending on a REMOVE send.",
    "let_it_run": "Let this ticket run. Do not send a modify, a scale, or a close.",
    "move_tp": "Move the target. The target is the score on manage_tp_price.",
}

QUESTION_ID = {
    "move_sl": LIFE_ID,
    "move_tp": LIFE_ID,
    "close": LIFE_ID,
    "remove": LIFE_ID,
    "scale_out": LIFE_ID,
}

PRICE_QUESTION = {
    "move_sl": "manage_sl_price",
    "move_tp": "manage_tp_price",
    "scale_out": "manage_scale",
}

LIFE_TEXT = (
    "This open Challenge ticket, this tick. "
    "Giveback is on the state when the peak favourable excursion and the "
    "excursion now are both known. That giveback is the case: the ticket was "
    "favourable and has given some back. "
    "Move the stop, scale out, close, or let it run. "
    "move_tp moves the target. "
    "The option you return is the manage for this tick. "
    "The stop is the score on manage_sl_price. "
    "The target is the score on manage_tp_price. "
    "The scale is the score on manage_scale. "
    "A score may sit between the levels. "
    "An empty answer or a tie does not send. "
    "let_it_run does not send."
)

AUTHORIZES = {
    "move_sl": "move_sl",
    "move_tp": "move_tp",
    "close": "close",
    "remove": "close",
    "scale_out": "scale_out",
}

_SCORE_INSTRUCTIONS = {
    "manage_sl_price": (
        "The score you return is the stop for this ticket. "
        "It may sit between the levels on the state. "
        "An empty score does not move the stop."
    ),
    "manage_tp_price": (
        "The score you return is the target for this ticket. "
        "It may sit between the levels on the state. "
        "An empty score does not move the target."
    ),
    "manage_scale": (
        "The score you return is the scale for this ticket. "
        "It may sit between the levels on the state. "
        "An empty score does not scale out."
    ),
}

_LEVEL_KEYS = (
    "stop_now",
    "stop_loss",
    "sl",
    "entry_price",
    "entry",
    "tp",
    "take_profit",
    "orig_sl",
    "orig_tp",
    "price",
    "stop",
    "target",
)

_CACHE: dict[Any, tuple[tuple[Any, ...], dict[str, Any]]] = {}



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
    override = (os.environ.get("GTOS_MANAGE_CHOICES_RECORD") or "").strip()
    if override:
        return Path(override)
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / CHALLENGE_NS
        / "judgment"
        / "manage_choices.jsonl"
    )


def armed_path() -> Path:
    return record_path().with_name("manage_choices_armed.json")


def clear_cache() -> None:
    _CACHE.clear()


def _ticket(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


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


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _levels(proposed: Any, facts: Mapping[str, Any] | None) -> list[float]:
    """Prices already on this state. The score is not snapped to one of them."""

    raws: list[Any] = []
    if isinstance(proposed, Mapping):
        raws.extend(proposed.get(key) for key in _LEVEL_KEYS)
    elif proposed is not None:
        raws.append(proposed)
    if isinstance(facts, Mapping):
        raws.extend(facts.get(key) for key in _LEVEL_KEYS if key in facts)
    levels: list[float] = []
    seen: set[float] = set()
    for raw in raws:
        number = _number(raw)
        if number is None or number in seen:
            continue
        seen.add(number)
        levels.append(number)
    return levels


def _choice_pack(act: str) -> dict[str, Any]:
    del act
    body = {
        "type": "choice",
        "instructions": LIFE_TEXT,
        "criteria": dict(CRITERIA),
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(LIFE_ID, LIFE_TEXT, dict(CRITERIA))
        if isinstance(built, dict) and LIFE_ID in built:
            return built
    except Exception:
        pass
    return {LIFE_ID: body}



def _price_anchors(proposed, facts):
    """Prices already on this ticket. Same unit as the stop and the target."""

    pairs = []
    sources = []
    if isinstance(proposed, dict):
        sources.append(proposed)
    if isinstance(facts, dict):
        sources.append(facts)
    for source in sources:
        for key in _LEVEL_KEYS:
            number = _number(source.get(key))
            if number is None:
                continue
            pairs.append((f"the {key} named on this card", number))
    return pairs


def _score_pack(qid: str, anchors) -> dict[str, Any]:
    """Amount Score. Fewer than two prices, or two scale fractions, does not post."""

    instructions = _SCORE_INSTRUCTIONS[qid]
    try:
        from .jev_questions import amount_question

        built = amount_question(qid, instructions, anchors)
    except Exception:
        return {}
    if not isinstance(built, dict) or qid not in built:
        return {}
    block = built.get(qid)
    if not isinstance(block, dict):
        return {}
    criteria = block.get("criteria")
    if not isinstance(criteria, list) or len(criteria) < 2:
        return {}
    return built


def _questions(act: str, price_anchors, scale_anchors) -> dict[str, Any]:
    """One card for the ticket. Prices and the scale fraction stay in their own units."""

    del act
    pack = _choice_pack(LIFE_ID)
    pack.update(_score_pack("manage_sl_price", price_anchors))
    pack.update(_score_pack("manage_tp_price", price_anchors))
    pack.update(_score_pack("manage_scale", scale_anchors))
    return pack


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        return {}
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        number = _number(val)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _choice_of(block: Any) -> dict[str, Any]:
    """Unique highest probability. A bare label, a tie, or an empty block is not a decision."""

    numeric = _probabilities(block)
    choice = None
    try:
        from .jev_questions import unique_highest

        choice = unique_highest(numeric or None, OPTIONS)
    except Exception:
        choice = None
    if choice not in OPTIONS:
        return {
            "choice": None,
            "probabilities": {key: numeric[key] for key in OPTIONS if key in numeric},
            "unique_highest": False,
            "probability": None,
        }
    return {
        "choice": choice,
        "probabilities": {key: numeric[key] for key in OPTIONS if key in numeric},
        "unique_highest": True,
        "probability": numeric.get(choice),
    }


def _returned_score(block: Any) -> float | None:
    """The score the model returned. Not snapped to a level. Missing stays missing."""

    number = None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = None
    parsed = _number(number)
    if parsed is not None:
        return parsed
    if not isinstance(block, dict):
        return None
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _number(raw)


def _remember(act: str, row: Mapping[str, Any], state: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    err = row.get("error")
    pairs = (
        (QUESTION_ID[act], row.get("choice"), not row.get("decision_emitted")),
    )
    price_id = PRICE_QUESTION.get(act)
    if price_id:
        pairs = pairs + ((price_id, row.get("score"), row.get("score") is None),)
    for key, value, failed in pairs:
        try:
            append_outcome(key, value, state, error=err if failed else None)
        except Exception:
            return


def _base(act: str, *, ticket: int | None, symbol: Any, reason: str, proposed: Any) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "logged_at_utc": _now(),
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "act": act,
        "question_id": QUESTION_ID[act],
        "ticket": ticket,
        "symbol": symbol,
        "reason": reason,
        "proposed": proposed,
        "choice": None,
        "score": None,
        "probability": None,
        "probabilities": {},
        "probability_source": None,
        "decision_emitted": False,
        "send": False,
        "model": MODEL,
        "persist": None,
        "persist_weight": None,
        "agent_order_send": False,
        "friends_copy_result": True,
        "extra_pass": False,
        "activation_token": "stays",
        "error": None,
    }


def _store(
    row: dict[str, Any],
    *,
    key: tuple[Any, ...],
    now: float,
    use_cache: bool,
    record: bool,
    record_to: Path | None,
) -> dict[str, Any]:
    del key, now, use_cache
    if record:
        _append(record_to or record_path(), row)
    return row


def _giveback(facts: Mapping[str, Any] | None) -> float | None:
    """Peak excursion minus the excursion now. Both numbers have to be on the card."""

    raw = dict(facts or {})
    peak = _number(raw.get("mfe_r"))
    if peak is None:
        peak = _number(raw.get("fav_r"))
    if peak is None:
        peak = _number(raw.get("peak_r"))
    current = _number(raw.get("progress_r"))
    if current is None:
        current = _number(raw.get("open_r"))
    if current is None:
        current = _number(raw.get("r_now"))
    if peak is None or current is None:
        return None
    return peak - current


def _logged_weight() -> float | None:
    """The persist_weight already returned. A miss on the latest row stays missing."""

    try:
        from .jev_questions import last_logged_value

        return _number(last_logged_value("persist_weight"))
    except Exception:
        return None


def decide(
    act: str,
    *,
    ticket: Any = None,
    symbol: Any = None,
    reason: str = "",
    proposed: Any = None,
    facts: Mapping[str, Any] | None = None,
    ask: Callable[..., dict[str, Any]] | None = None,
    use_cache: bool = True,
    record: bool = True,
    record_to: Path | None = None,
) -> dict[str, Any]:
    """Ask one manage Choice and its Scores. ``send`` follows that return.

    Never raises. Never sends an order. No ticket is exempt from close.
    An empty answer, a tie, a missing score, or an error does not restore
    a constant.
    """

    if act not in QUESTION_ID:
        row = _base("close", ticket=_ticket(ticket), symbol=symbol, reason=reason, proposed=proposed)
        row["act"] = act
        row["question_id"] = None
        row["error"] = "unknown_act"
        return row
    ticket_i = _ticket(ticket)
    row = _base(act, ticket=ticket_i, symbol=symbol, reason=reason, proposed=proposed)
    levels = _levels(proposed, facts)
    row["levels"] = levels
    card_facts = dict(facts or {})
    giveback = _giveback(card_facts)
    if giveback is not None:
        card_facts["giveback"] = giveback
    facts_key = json.dumps(_jsonable(card_facts), sort_keys=True)
    key = (ticket_i, str(symbol), facts_key)
    now = time.monotonic()
    state: dict[str, Any] = {
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "act": act,
        "ticket": ticket_i,
        "symbol": symbol,
        "reason": reason or act,
        "proposed": proposed,
        "levels": levels,
        "model": MODEL,
        "giveback": giveback,
        "facts": card_facts,
    }
    try:
        from .equity_frame import attach_account

        attached = attach_account(state)
        if isinstance(attached, dict) and attached.get("act") == act:
            state = attached
    except Exception:
        pass
    try:
        from .jev_questions import hierarchical_labels

        state["labels"] = hierarchical_labels(state, extra={"subgoal": "manage", "act": act})
    except Exception:
        pass
    try:
        price_anchors = _price_anchors(proposed, card_facts)
        scale_anchors = _scale_pairs({"facts": card_facts, "proposed": proposed if isinstance(proposed, dict) else {}})
        questions = _questions(act, price_anchors, scale_anchors)
    except Exception as exc:  # noqa: BLE001 — manage must not raise into the writer
        row["error"] = type(exc).__name__
        return _store(row, key=key, now=now, use_cache=use_cache, record=record, record_to=record_to)
    try:
        from .jev_questions import prior_outcomes

        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        pass
    account = state.get("account") if isinstance(state.get("account"), dict) else {}
    equity = _number(state.get("equity"))
    if equity is None:
        equity = _number(account.get("equity"))
    state_key = (ticket_i, str(symbol), facts_key, giveback, equity)
    cached = _CACHE.get(ticket_i) if use_cache else None
    reused = isinstance(cached, tuple) and len(cached) == 2 and cached[0] == state_key
    if reused:
        ts = cached[1]
    else:
        try:
            call = ask
            if call is None:
                from .jev_client import evaluate

                call = evaluate
            ts = call(
                state,
                questions=questions,
                merge_sleeve=False,
            ) or {}
        except Exception as exc:  # noqa: BLE001 — manage must not raise into the writer
            ts = {"error": type(exc).__name__}
        if not isinstance(ts, dict):
            ts = {"error": "evaluate_not_a_dict"}
        if use_cache:
            _CACHE[ticket_i] = (state_key, ts)
    if ts.get("model"):
        row["model"] = ts.get("model")
    answers = ts.get("answers") if isinstance(ts.get("answers"), dict) else {}
    picked = _choice_of(answers.get(QUESTION_ID[act]) or {})
    row["choice"] = picked["choice"]
    row["probability"] = picked["probability"]
    row["probabilities"] = picked["probabilities"]
    row["probability_source"] = "unique_highest" if picked["unique_highest"] else None
    row["decision_emitted"] = bool(picked["unique_highest"]) and picked["choice"] in OPTIONS
    price_id = PRICE_QUESTION.get(act)
    stop = _returned_score(answers.get("manage_sl_price"))
    target = _returned_score(answers.get("manage_tp_price"))
    scale = _returned_score(answers.get("manage_scale"))
    price = {"move_sl": stop, "move_tp": target, "scale_out": scale}.get(act)
    if "persist_weight" in answers:
        weight = _returned_score(answers.get("persist_weight"))
    else:
        weight = _logged_weight()
    row["score"] = price
    row["stop"] = stop
    row["target"] = target
    row["scale"] = scale
    row["giveback"] = giveback
    row["persist_weight"] = weight
    row["persist"] = weight
    row["reused"] = bool(reused)
    winner = row["choice"] if row["decision_emitted"] else None
    row["send"] = winner == AUTHORIZES.get(act) and winner not in (None, "let_it_run")
    if price_id and row["send"] and price is None:
        row["send"] = False
        row["error"] = "score_missing"
    elif not row["decision_emitted"]:
        receipt_error = ts.get("error")
        if ts.get("ok") is False and not receipt_error:
            receipt_error = ts.get("skipped") or "post_failed"
        if receipt_error:
            row["error"] = receipt_error
    if not reused:
        _remember(act, row, state)
    return _store(row, key=key, now=now, use_cache=use_cache, record=record, record_to=record_to)


def emit_manage(
    act: str,
    *,
    ticket: Any = None,
    symbol: Any = None,
    reason: str = "",
    proposed: Any = None,
    facts: Mapping[str, Any] | None = None,
    namespace: str | None = None,
    ask: Callable[..., dict[str, Any]] | None = None,
    use_cache: bool = True,
    record: bool = True,
    record_to: Path | None = None,
) -> bool:
    """True only when this exact Challenge act's Choice authorizes the send."""

    if namespace is not None and str(namespace) != CHALLENGE_NS:
        return True
    row = decide(
        act,
        ticket=ticket,
        symbol=symbol,
        reason=reason,
        proposed=proposed,
        facts=facts,
        ask=ask,
        use_cache=use_cache,
        record=record,
        record_to=record_to,
    )
    return bool(row.get("send"))


def send_unique_move_sl(
    row: Mapping[str, Any],
    *,
    facts: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Keep the loader call. This function does not send and does not invent a stop."""

    del facts
    out = dict(row) if isinstance(row, Mapping) else {}
    out["agent_order_send"] = False
    return out


class _NotSent:
    """REMOVE was not sent. retcode is not the broker success code."""

    retcode = None
    success = False
    comment = "manage_choice_not_sent"


def _is_remove(request: Any) -> bool:
    if not isinstance(request, dict):
        return False
    try:
        return int(request.get("action") or 0) == 8
    except (TypeError, ValueError):
        return False


def arm_pending_remove(
    mt5: Any,
    *,
    ask: Callable[..., dict[str, Any]] | None = None,
    write_stamp: bool = True,
    record: bool = True,
    record_to: Path | None = None,
    use_cache: bool = True,
) -> bool:
    """Wrap one mt5 object's order_send so action 8 asks the remove Choice.

    The original order_send still runs when the Choice authorizes the cancel,
    so the activation token on that method stays in front of the broker.
    """

    if mt5 is None or getattr(mt5, "_gtos_manage_remove_armed", False):
        return False
    original = getattr(mt5, "order_send", None)
    if not callable(original):
        return False

    def order_send(request, *args, **kwargs):
        if _is_remove(request):
            ticket = request.get("order", request.get("position", request.get("ticket")))
            allowed = emit_manage(
                "remove",
                ticket=ticket,
                symbol=request.get("symbol"),
                reason="TRADE_ACTION_REMOVE",
                namespace=CHALLENGE_NS,
                ask=ask,
                use_cache=use_cache,
                record=record,
                record_to=record_to,
            )
            if not allowed:
                return _NotSent()
        return original(request, *args, **kwargs)

    mt5.order_send = order_send
    mt5._gtos_manage_remove_armed = True
    if write_stamp:
        try:
            payload = {
                "schema": SCHEMA,
                "logged_at_utc": _now(),
                "ns": CHALLENGE_NS,
                "armed": True,
                "hook": "pending_remove",
                "pid": os.getpid(),
                "persist": None,
                "agent_order_send": False,
                "activation_token": "stays",
                "model": MODEL,
                "gold_close_pin": False,
            }
            path = armed_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        except OSError:
            pass
    return True
