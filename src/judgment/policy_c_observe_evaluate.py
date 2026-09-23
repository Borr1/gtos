"""Policy C life for one candidate and one ticket.

Each subject passes watch, observe, admit, place, and every manage step
of the life. The choice, the threshold, the loop bound, the parameter,
and whether that component exists are the System One returns for that
step. The post is ``jev_client.evaluate`` for model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
A return is a Noul, a Choice, or a Score. A Score may sit between the
levels on the state. Prior outcomes are attached on every ask, and the
return is stored for the next ask. An empty answer, a tie, a missing
score, or an error leaves that return unset. This module does not send.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.policy_c_life.v1"
CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
_STAGES = ("watch", "observe", "admit", "place")
_SUBJECTS = ("candidate", "ticket")
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
_LIMIT_KEYS = frozenset({
    "floor",
    "baseline",
    "day_start_baseline",
    "static_floor",
    "pass_line",
    "flatten_floor_usd",
    "daily_loss_pct",
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
_CHOICES: dict[str, dict[str, str]] = {
    "watch": {
        "watch": "This subject stays on watch.",
        "release": "This subject leaves watch.",
    },
    "observe": {
        "note": "The observation on this subject stands.",
        "dark": "This observation is dark.",
    },
    "admit": {
        "admit": "Admit this subject.",
        "stand": "This subject is not admitted.",
        "trim": "Admit this subject at the returned parameter.",
    },
    "place": {
        "place": "This subject is the place on this bar.",
        "stand": "This subject is not the place on this bar.",
        "delay": "This bar is not the bar for this subject.",
    },
    "manage": {
        "leave": "Leave this subject as it is on this step.",
        "move_stop": "Move the stop to the returned parameter.",
        "move_target": "Move the target to the returned parameter.",
        "close": "Close on this step.",
        "hold": "Hold on this step.",
    },
}
_DROP = object()



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
    return name.strip().lower() in _LIMIT_KEYS


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
            if _limit_key(name):
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
                "true": "The component exists on this state.",
                "false": "The component does not exist on this state.",
            },
        }
    }


def _ids(subject: str, stage: str, index: int | None = None) -> dict[str, str]:
    stem = f"policy_c_{subject}_{stage}"
    if index is not None:
        stem = f"{stem}_{index}"
    return {
        "exists": f"{stem}_exists",
        "choice": f"{stem}_choice",
        "threshold": f"{stem}_threshold",
        "parameter": f"{stem}_parameter",
    }


def _where(subject: str, stage: str, index: int | None) -> str:
    if stage == "manage" and index is not None:
        return f"{subject} manage step {index}"
    return f"{subject} {stage}"


def _step_questions(
    subject: str,
    stage: str,
    levels: list[str],
    index: int | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    ids = _ids(subject, stage, index)
    where = _where(subject, stage, index)
    criteria = _CHOICES[stage]
    pack: dict[str, Any] = {}
    pack.update(_noul_question(
        ids["exists"],
        (
            f"Does the {stage} component exist for this {where}? "
            "An empty answer leaves existence unset. "
            "Do not invent news. Do not send an order."
        ),
    ))
    pack.update(_choice_question(
        ids["choice"],
        (
            f"Life step for this {where}. "
            "Pick one option. The unique highest probability is the decision. "
            "An empty answer or a tie is not a decision. "
            "Do not invent news. Do not send an order."
        ),
        criteria,
    ))
    scale = list(levels) if levels else list(_BETWEEN)
    pack.update(_score_question(
        ids["threshold"],
        (
            f"The score you return is the threshold for this {where}. "
            "It may sit between the levels. "
            "An empty score leaves the threshold unset. "
            "Do not send an order."
        ),
        scale,
    ))
    pack.update(_score_question(
        ids["parameter"],
        (
            f"The score you return is the parameter for this {where}. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "Do not send an order."
        ),
        scale,
    ))
    return ids, pack


def _bound_question(subject: str) -> tuple[str, dict[str, Any]]:
    qid = f"policy_c_{subject}_loop_bound"
    pack = _score_question(
        qid,
        (
            f"How many manage steps are in this {subject}'s life? "
            "The score you return is that bound. "
            "It may sit between the levels. "
            "An empty score leaves the bound unset. "
            "Do not send an order."
        ),
        _LIFE_SPAN,
    )
    return qid, pack


def _unique_name(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "choice":
        return None
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping) or not raw:
        return None
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
        return None
    best = max(numeric.values())
    winners = [
        name for name in order if name in numeric and numeric[name] == best
    ]
    if len(winners) != 1:
        return None
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(numeric), order)
    except Exception:
        picked = winners[0]
    if picked is None or str(picked) != winners[0]:
        return None
    return winners[0]


def _score_value(block: Any) -> float | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "score":
        return None
    number = None
    try:
        from .jev_questions import returned_number

        number = returned_number(block)
    except Exception:
        number = None
    parsed = _finite(number)
    if parsed is not None:
        return parsed
    raw = block.get("score")
    if raw is None:
        raw = block.get("value")
    return _finite(raw)


def _noul_value(block: Any) -> bool | None:
    if not isinstance(block, dict):
        return None
    kind = block.get("type")
    if kind is not None and str(kind).strip().lower() != "noul":
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return None


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    try:
        from .jev_questions import prior_outcomes

        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        return


def _remember(state: Mapping[str, Any], pairs: tuple[tuple[str, Any], ...], error: str | None) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    for key, value in pairs:
        try:
            append_outcome(key, value, state, error=None if value is not None else error)
        except Exception:
            return


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> tuple[dict[str, Any], str | None]:
    _attach_priors(state, questions)
    try:
        call = evaluate_fn
        if call is None:
            from .jev_client import evaluate

            call = evaluate
        receipt = call(
            state,
            questions=dict(questions),
            merge_sleeve=False,
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
    return answers, str(error)


def _blank_step(error: str | None) -> dict[str, Any]:
    return {
        "choice": None,
        "threshold": None,
        "parameter": None,
        "component_exists": None,
        "error": error,
    }


def _read_step(
    answers: Mapping[str, Any],
    ids: Mapping[str, str],
    order: tuple[str, ...],
    error: str | None,
) -> dict[str, Any]:
    row = {
        "choice": _unique_name(answers.get(ids["choice"]), order),
        "threshold": _score_value(answers.get(ids["threshold"])),
        "parameter": _score_value(answers.get(ids["parameter"])),
        "component_exists": _noul_value(answers.get(ids["exists"])),
    }
    missing = any(row[name] is None for name in ("choice", "threshold", "parameter", "component_exists"))
    row["error"] = error if missing and error else None
    return row


def _ask_step(
    *,
    subject: str,
    stage: str,
    shared: Mapping[str, Any],
    subject_facts: Mapping[str, Any],
    levels: list[str],
    index: int | None,
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    _bind_card({"facts": dict(shared), "subject_facts": dict(subject_facts)})
    ids, questions = _step_questions(subject, stage, levels, index)
    _bind_card(None)
    state: dict[str, Any] = {
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "subject": subject,
        "stage": stage,
        "facts": dict(shared),
        "subject_facts": dict(subject_facts),
    }
    if index is not None:
        state["manage_index"] = index
    answers, error = _post(state, questions, evaluate_fn)
    order = tuple(_CHOICES[stage])
    row = _read_step(answers, ids, order, error)
    _remember(
        state,
        (
            (ids["exists"], row["component_exists"]),
            (ids["choice"], row["choice"]),
            (ids["threshold"], row["threshold"]),
            (ids["parameter"], row["parameter"]),
        ),
        error,
    )
    return row


def _ask_bound(
    *,
    subject: str,
    shared: Mapping[str, Any],
    subject_facts: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> tuple[float | None, str | None]:
    _bind_card({"facts": dict(shared), "subject_facts": dict(subject_facts)})
    try:
        qid, questions = _bound_question(subject)
    finally:
        _bind_card(None)
    state = {
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "subject": subject,
        "stage": "manage",
        "facts": dict(shared),
        "subject_facts": dict(subject_facts),
    }
    answers, error = _post(state, questions, evaluate_fn)
    bound = _score_value(answers.get(qid))
    _remember(state, ((qid, bound),), error if bound is None else None)
    if bound is None and error:
        return None, error
    return bound, None


def _empty_subject(error: str | None) -> dict[str, Any]:
    subject = {stage: _blank_step(error) for stage in _STAGES}
    subject["loop_bound"] = None
    subject["manage"] = None
    subject["error"] = error
    return subject


def _run_subject(
    subject: str,
    *,
    shared: Mapping[str, Any],
    subject_facts: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> dict[str, Any]:
    levels = _levels({"facts": dict(shared), "subject_facts": dict(subject_facts)})
    card: dict[str, Any] = {}
    for stage in _STAGES:
        card[stage] = _ask_step(
            subject=subject,
            stage=stage,
            shared=shared,
            subject_facts=subject_facts,
            levels=levels,
            index=None,
            evaluate_fn=evaluate_fn,
        )
    bound, bound_error = _ask_bound(
        subject=subject,
        shared=shared,
        subject_facts=subject_facts,
        evaluate_fn=evaluate_fn,
    )
    card["loop_bound"] = bound
    if bound is None or bound < 0:
        card["manage"] = None
        card["error"] = bound_error
        return card
    steps: list[dict[str, Any]] = []
    while len(steps) < bound:
        steps.append(_ask_step(
            subject=subject,
            stage="manage",
            shared=shared,
            subject_facts=subject_facts,
            levels=levels,
            index=len(steps),
            evaluate_fn=evaluate_fn,
        ))
    card["manage"] = steps
    card["error"] = None
    return card


def _payload(state: Mapping[str, Any] | None, name: str, explicit: Mapping[str, Any] | None) -> dict[str, Any]:
    if isinstance(explicit, Mapping):
        return dict(explicit)
    if isinstance(state, Mapping) and isinstance(state.get(name), Mapping):
        return dict(state[name])
    return {}


def _shared_facts(state: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(state, Mapping):
        return {}
    cleaned = _scrub(dict(state))
    return cleaned if isinstance(cleaned, dict) else {}


def evaluate_policy_c_observe(
    state: Mapping[str, Any] | None = None,
    *,
    evaluate_fn: Callable[..., Any] | None = None,
    cache: dict[str, dict[str, Any]] | None = None,
    candidate: Mapping[str, Any] | None = None,
    ticket: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Ask the life of this candidate and this ticket. Never sends.

    ``cache`` is not a decision. History for the next ask is the stored
    return. An empty answer, a tie, a missing score, or an error stays unset.
    """

    del cache
    shared = _shared_facts(state)
    try:
        cards = {
            name: _run_subject(
                name,
                shared=shared,
                subject_facts=_scrub(_payload(state, name, explicit)) or {},
                evaluate_fn=evaluate_fn,
            )
            for name, explicit in (("candidate", candidate), ("ticket", ticket))
        }
    except Exception as exc:
        error = type(exc).__name__
        cards = {name: _empty_subject(error) for name in _SUBJECTS}
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "candidate": cards["candidate"],
        "ticket": cards["ticket"],
    }
