"""Sleeve select through the life of a candidate and a ticket.

The candidate passes watch, observe, admit, place, and every manage step
of the life the loop bound returns. The ticket passes the same life.
At each step the choice, the threshold, the parameter, and which
component exists are the System One return. The loop bound is the Score
for how many manage steps that life takes.

The post is ``jev_client.evaluate`` (model ``jev-1.13.0``,
``merge_sleeve=False``): POST https://api.typesafe.ai/v1/systemone.
Questions are only Noul, Choice, or Score. Prior outcomes are attached
on every ask. A Score may sit between the levels. An empty answer, a
tie, or an error leaves that return unset. This module does not send.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

GATE_ID = "JEV_SLEEVE_SELECT"
SCHEMA = "gtos.judgment.sleeve_select_life.v1"
MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"

STAGES = ("watch", "observe", "admit", "place")
SUBJECTS = ("candidate", "ticket")

MANAGE_CRITERIA = {
    "leave_orig": "Leave the original stop and target.",
    "move_sl": "Move the stop. The stop is the parameter score on this step.",
    "move_tp": "Move the target. The target is the parameter score on this step.",
    "close": "Close on this step.",
    "hold": "Hold on this step.",
}
STAGE_CRITERIA = {
    "watch": {
        "watch": "This subject stays on watch.",
        "hold": "Hold at watch.",
    },
    "observe": {
        "observe": "Observe this subject.",
        "hold": "Hold at observe.",
    },
    "admit": {
        "admit": "Admit this subject.",
        "hold": "Hold at admit.",
    },
    "place": {
        "place": "This subject is the order on this bar.",
        "hold": "This subject is not the order on this bar.",
    },
    "manage": MANAGE_CRITERIA,
}
_COMPONENT_KEYS = ("components", "sleeve_members", "sleeves", "alive_sleeves", "menu")
_SKIP_LEVEL_PARTS = (
    "floor",
    "baseline",
    "equity",
    "balance",
    "drawdown",
    "profit_target",
    "max_loss",
    "daily_loss",
    "kill",
    "proposed",
    "ticket",
    "login",
)
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
_LIFE_SPAN = (
    "no further manage step",
    "a short life",
    "the steps still open on this subject",
)
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


def _number(value: Any) -> float | None:
    """A returned number. Booleans, blanks, and non-finite values stay empty."""

    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _limit_key(name: Any) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    for token in _BANNED_TEXT:
        probe = token.replace(",", "").replace("_", "").lower()
        if probe in compact:
            return True
    return False


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar tokens before an ask."""

    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _limit_key(key):
                continue
            out[str(key)] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        return [_scrub(item) for item in value]
    if isinstance(value, str) and _banned_text(value):
        return ""
    return value


def _slug(name: str) -> str:
    chars = [ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in str(name)]
    token = "".join(chars).strip("_")
    return token[:80] or "component"


def _add_name(names: list[str], raw: Any) -> None:
    text = str(raw or "").strip()
    if not text or _limit_key(text) or _banned_text(text) or text in names:
        return
    names.append(text)


def _components(state: Mapping[str, Any], menu_criteria: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Names already on the state. Existence is asked, not assumed."""

    names: list[str] = []
    if isinstance(menu_criteria, Mapping):
        for key in menu_criteria:
            _add_name(names, key)
    for key in _COMPONENT_KEYS:
        raw = state.get(key)
        if isinstance(raw, Mapping):
            for child in raw:
                _add_name(names, child)
        elif isinstance(raw, (list, tuple)) and not isinstance(raw, (str, bytes)):
            for item in raw:
                if isinstance(item, Mapping):
                    _add_name(names, item.get("name") or item.get("sleeve") or item.get("id"))
                else:
                    _add_name(names, item)
    for subject in SUBJECTS:
        raw = state.get(subject)
        if isinstance(raw, Mapping):
            _add_name(names, raw.get("sleeve"))
    _add_name(names, state.get("sleeve"))
    identity = state.get("identity") if isinstance(state.get("identity"), Mapping) else {}
    _add_name(names, identity.get("sleeve"))
    return tuple(names)


def _subject_facts(state: Mapping[str, Any], subject: str) -> dict[str, Any]:
    raw = state.get(subject)
    if isinstance(raw, Mapping):
        cleaned = _scrub(dict(raw))
        return cleaned if isinstance(cleaned, dict) else {}
    if raw not in (None, ""):
        return {subject: _scrub(raw)}
    return {}


def _shared_facts(state: Mapping[str, Any]) -> dict[str, Any]:
    cleaned = _scrub(dict(state))
    return cleaned if isinstance(cleaned, dict) else {}


def _parameter_levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Live numeric levels already on the facts. A score may sit between them."""

    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        low = key.lower()
        if any(part in low for part in _SKIP_LEVEL_PARTS) or _limit_key(key):
            return
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                walk(str(child_key), child)
            return
        if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
            for item in value:
                walk(key, item)
            return
        number = _number(value)
        if number is not None:
            found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    return [format(number, ".10g") for number in sorted(set(found))]


def _stem(subject: str, stage: str, index: int | None) -> str:
    if stage == "manage" and index is not None:
        return f"sleeve_select_{subject}_manage_{index}"
    return f"sleeve_select_{subject}_{stage}"


def _where(subject: str, stage: str, index: int | None) -> str:
    if stage == "manage" and index is not None:
        return f"{subject} manage step {index}"
    return f"{subject} {stage}"


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(value) for key, value in criteria.items()},
    }
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, instructions, dict(body["criteria"]))
        block = built.get(qid) if isinstance(built, Mapping) else None
        if isinstance(block, Mapping):
            packed = dict(block)
            packed["type"] = "choice"
            packed["instructions"] = instructions
            packed["criteria"] = dict(body["criteria"])
            return {qid: packed}
    except Exception:
        pass
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
                "true": "This component exists on this state.",
                "false": "This component does not exist on this state.",
            },
        }
    }


def _step_questions(
    subject: str,
    stage: str,
    components: tuple[str, ...],
    levels: list[str],
    index: int | None,
) -> dict[str, Any]:
    stem = _stem(subject, stage, index)
    where = _where(subject, stage, index)
    scale = list(levels) if levels else list(_BETWEEN)
    pack: dict[str, Any] = {}
    pack.update(_choice_question(
        f"{stem}_choice",
        (
            f"Life step for this {where}. "
            "Pick one option. The unique highest probability is the decision. "
            "An empty answer or a tie is not a decision. "
            "Do not alias Package B to sub_mid_dn_revert. Do not invent news. "
            "Do not send."
        ),
        STAGE_CRITERIA[stage],
    ))
    pack.update(_score_question(
        f"{stem}_threshold",
        (
            f"The score you return is the threshold for this {where}. "
            "It may sit between the levels. "
            "An empty score leaves the threshold unset. Do not send."
        ),
        scale,
    ))
    pack.update(_score_question(
        f"{stem}_parameter",
        (
            f"The score you return is the parameter for this {where}. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. Do not send."
        ),
        scale,
    ))
    if components:
        pack.update(_choice_question(
            f"{stem}_which_component",
            (
                f"Which component exists for this {where}? "
                "The unique highest probability is the component. "
                "An empty answer or a tie is not a decision. Do not send."
            ),
            {name: f"{name} exists on this state." for name in components},
        ))
        for name in components:
            pack.update(_noul_question(
                f"{stem}_exists_{_slug(name)}",
                (
                    f"Does component {name} exist for this {where}? "
                    "An empty answer leaves existence unset. Do not send."
                ),
            ))
    else:
        pack.update(_noul_question(
            f"{stem}_component_exists",
            (
                f"Does the component exist for this {where}? "
                "An empty answer leaves existence unset. Do not send."
            ),
        ))
    return pack


def _bound_questions(subject: str) -> dict[str, Any]:
    return _score_question(
        f"sleeve_select_{subject}_loop_bound",
        (
            f"How many manage steps are in this {subject}'s life? "
            "The score you return is that bound. "
            "It may sit between the levels. "
            "An empty score leaves the bound unset. Do not send."
        ),
        _LIFE_SPAN,
    )


def _tied(probabilities: Mapping[str, Any] | None, order: tuple[str, ...]) -> bool:
    """True when at least one allowed probability is present and none is unique."""

    if not isinstance(probabilities, Mapping) or not probabilities:
        return False
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, value in probabilities.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _number(value)
        if number is None:
            continue
        numeric[name] = number
    if not numeric:
        return False
    best = max(numeric.values())
    winners = [name for name in order if name in numeric and numeric[name] == best]
    return len(winners) != 1


def _local_unique(probabilities: Mapping[str, Any] | None, order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie or an empty block is not a decision."""

    if not isinstance(probabilities, Mapping) or not probabilities:
        return None
    allowed = set(order)
    numeric: dict[str, float] = {}
    for key, value in probabilities.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _number(value)
        if number is None:
            continue
        numeric[name] = number
    if not numeric:
        return None
    best = max(numeric.values())
    winners = [name for name in order if name in numeric and numeric[name] == best]
    if len(winners) != 1:
        return None
    return winners[0]


def _choice_of(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, Mapping):
        return None
    probs = block.get("probabilities") if isinstance(block.get("probabilities"), Mapping) else None
    local = _local_unique(probs, order)
    if local is None:
        return None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(probs) if isinstance(probs, Mapping) else None, order)
    except Exception:
        return local
    if picked is None:
        return local
    if str(picked) != local:
        return None
    return local


def _score_of(block: Any) -> float | None:
    """The Score on this block. It is not snapped to a level."""

    parsed = None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(block))
    except Exception:
        parsed = None
    if parsed is not None:
        return parsed
    if not isinstance(block, Mapping):
        return None
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _number(raw)


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. Missing stays missing."""

    if not isinstance(block, Mapping) or "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _number(raw)


def _answers_of(hop: Any) -> tuple[dict[str, Any], str | None]:
    if not isinstance(hop, Mapping):
        return {}, "evaluate_not_a_dict"
    answers = hop.get("answers")
    error = hop.get("error")
    if error in (None, ""):
        error = hop.get("skipped")
    error_text = None if error in (None, "") else str(error)
    if isinstance(answers, Mapping) and answers:
        return dict(answers), error_text
    if error_text:
        return {}, error_text
    return {}, "empty"


def _blank_step() -> dict[str, Any]:
    return {
        "choice": None,
        "threshold": None,
        "parameter": None,
        "which_component": None,
        "component_exists": {},
        "error": None,
    }


def _read_step(
    stage: str,
    stem: str,
    components: tuple[str, ...],
    hop: Any,
) -> dict[str, Any]:
    row = _blank_step()
    answers, error = _answers_of(hop)
    order = tuple(STAGE_CRITERIA[stage])
    row["choice"] = _choice_of(answers.get(f"{stem}_choice"), order)
    row["threshold"] = _score_of(answers.get(f"{stem}_threshold"))
    row["parameter"] = _score_of(answers.get(f"{stem}_parameter"))
    exists: dict[str, Any] = {}
    if components:
        row["which_component"] = _choice_of(
            answers.get(f"{stem}_which_component"),
            tuple(components),
        )
        for name in components:
            exists[name] = _noul_of(answers.get(f"{stem}_exists_{_slug(name)}"))
    else:
        exists["component"] = _noul_of(answers.get(f"{stem}_component_exists"))
    row["component_exists"] = exists
    choice_block = answers.get(f"{stem}_choice")
    probs = {}
    if isinstance(choice_block, Mapping) and isinstance(choice_block.get("probabilities"), Mapping):
        probs = choice_block["probabilities"]
    if row["choice"] is None and _tied(probs, order):
        error = error or "tie"
    if (
        row["choice"] is None
        and row["threshold"] is None
        and row["parameter"] is None
        and row["which_component"] is None
        and not any(value is not None for value in exists.values())
    ):
        error = error or "empty"
    elif error == "empty":
        error = None
    row["error"] = error
    return row


def _remember(state: Mapping[str, Any], pairs: tuple[tuple[str, Any], ...], error: str | None) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value in pairs:
        try:
            append_outcome(key, value, logged, error=None if value is not None else error)
        except Exception:
            return


def _remember_step(
    state: Mapping[str, Any],
    stem: str,
    components: tuple[str, ...],
    row: Mapping[str, Any],
) -> None:
    exists = row.get("component_exists") if isinstance(row.get("component_exists"), Mapping) else {}
    pairs: list[tuple[str, Any]] = [
        (f"{stem}_choice", row.get("choice")),
        (f"{stem}_threshold", row.get("threshold")),
        (f"{stem}_parameter", row.get("parameter")),
        (f"{stem}_which_component", row.get("which_component")),
    ]
    if components:
        for name in components:
            pairs.append((f"{stem}_exists_{_slug(name)}", exists.get(name)))
    else:
        pairs.append((f"{stem}_component_exists", exists.get("component")))
    _remember(state, tuple(pairs), row.get("error") if isinstance(row.get("error"), str) else None)


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> Any:
    _attach_priors(state, questions)
    call = evaluate_fn
    if call is None:
        from .jev_client import evaluate

        call = evaluate
    return call(state, questions=questions, merge_sleeve=False)


def _ask_state(
    *,
    subject: str,
    stage: str,
    shared: Mapping[str, Any],
    candidate: Mapping[str, Any],
    ticket: Mapping[str, Any],
    components: tuple[str, ...],
    levels: list[str],
    index: int | None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "gate_id": GATE_ID,
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "subject": subject,
        "stage": stage,
        "candidate": dict(candidate),
        "ticket": dict(ticket),
        "facts": dict(shared),
        "components": list(components),
        "levels": list(levels),
    }
    if index is not None:
        state["manage_index"] = index
    return state


def _ask_step(
    *,
    subject: str,
    stage: str,
    shared: Mapping[str, Any],
    candidate: Mapping[str, Any],
    ticket: Mapping[str, Any],
    components: tuple[str, ...],
    levels: list[str],
    index: int | None,
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    stem = _stem(subject, stage, index)
    _bind_card({"facts": dict(shared), "candidate": dict(candidate), "ticket": dict(ticket)})
    questions = _step_questions(subject, stage, components, levels, index)
    _bind_card(None)
    state = _ask_state(
        subject=subject,
        stage=stage,
        shared=shared,
        candidate=candidate,
        ticket=ticket,
        components=components,
        levels=levels,
        index=index,
    )
    try:
        hop = _post(state, questions, evaluate_fn)
    except Exception as exc:  # noqa: BLE001 — a life step must not raise
        hop = {"error": type(exc).__name__}
    row = _read_step(stage, stem, components, hop)
    _remember_step(state, stem, components, row)
    return row


def _ask_bound(
    *,
    subject: str,
    shared: Mapping[str, Any],
    candidate: Mapping[str, Any],
    ticket: Mapping[str, Any],
    components: tuple[str, ...],
    levels: list[str],
    evaluate_fn: Callable[..., Any] | None,
) -> float | None:
    _bind_card({"facts": dict(shared), "candidate": dict(candidate), "ticket": dict(ticket)})
    try:
        questions = _bound_questions(subject)
    finally:
        _bind_card(None)
    qid = f"sleeve_select_{subject}_loop_bound"
    state = _ask_state(
        subject=subject,
        stage="manage",
        shared=shared,
        candidate=candidate,
        ticket=ticket,
        components=components,
        levels=levels,
        index=None,
    )
    try:
        hop = _post(state, questions, evaluate_fn)
    except Exception as exc:  # noqa: BLE001
        hop = {"error": type(exc).__name__}
    answers, error = _answers_of(hop)
    bound = _score_of(answers.get(qid))
    _remember(state, ((qid, bound),), error if bound is None else None)
    return bound


def _run_subject(
    subject: str,
    *,
    shared: Mapping[str, Any],
    candidate: Mapping[str, Any],
    ticket: Mapping[str, Any],
    components: tuple[str, ...],
    levels: list[str],
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    card: dict[str, Any] = {}
    for stage in STAGES:
        card[stage] = _ask_step(
            subject=subject,
            stage=stage,
            shared=shared,
            candidate=candidate,
            ticket=ticket,
            components=components,
            levels=levels,
            index=None,
            evaluate_fn=evaluate_fn,
        )
    bound = _ask_bound(
        subject=subject,
        shared=shared,
        candidate=candidate,
        ticket=ticket,
        components=components,
        levels=levels,
        evaluate_fn=evaluate_fn,
    )
    card["loop_bound"] = bound
    if bound is None:
        card["manage"] = None
        return card
    steps: list[dict[str, Any]] = []
    while len(steps) < bound:
        steps.append(_ask_step(
            subject=subject,
            stage="manage",
            shared=shared,
            candidate=candidate,
            ticket=ticket,
            components=components,
            levels=levels,
            index=len(steps),
            evaluate_fn=evaluate_fn,
        ))
    card["manage"] = steps
    return card


def pass_life(
    state: Mapping[str, Any] | None,
    *,
    menu_criteria: Mapping[str, Any] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """The candidate and the ticket each pass the life. A miss stays unset."""

    source = _shared_facts(dict(state or {}))
    candidate = _subject_facts(dict(state or {}), "candidate")
    ticket = _subject_facts(dict(state or {}), "ticket")
    components = _components(dict(state or {}), menu_criteria)
    levels = _parameter_levels({"shared": source, "candidate": candidate, "ticket": ticket})
    life: dict[str, Any] = {}
    for subject in SUBJECTS:
        life[subject] = _run_subject(
            subject,
            shared=source,
            candidate=candidate,
            ticket=ticket,
            components=components,
            levels=levels,
            evaluate_fn=evaluate_fn,
        )
    return life


def evaluate_sleeve_select_observe(
    state: Mapping[str, Any] | None,
    *,
    menu_criteria: Mapping[str, str] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
    cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Ask the life. The returns are the decisions. Never sends.

    ``cache`` is not a decision. The next ask reads the stored return.
    """

    del cache
    try:
        life = pass_life(state, menu_criteria=menu_criteria, evaluate_fn=evaluate_fn)
        error = None
    except Exception as exc:  # noqa: BLE001
        life = {
            subject: {
                stage: _blank_step() for stage in STAGES
            }
            | {"loop_bound": None, "manage": None}
            for subject in SUBJECTS
        }
        error = type(exc).__name__
    return {
        "schema": SCHEMA,
        "gate_id": GATE_ID,
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "candidate": life.get("candidate"),
        "ticket": life.get("ticket"),
        "broker_effect": False,
        "error": error,
    }
