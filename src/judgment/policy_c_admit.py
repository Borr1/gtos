"""Policy C admit for one pre-entry candidate.

One hop: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
The choice, the threshold, the parameter, and the sufficiency noul are the
returns for this state. A return is only a Noul, a Choice, or a Score.
Prior outcomes are attached on the ask, and the return is stored for the
next ask.

An empty answer, a tie, a missing score, or an error leaves that return
unset. Floor and baseline are not questions. ``GTOS_JEV_POLICY_C_APPLY``
is a fact on the card. The ask still runs. This module does not send an order.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

MODEL = "jev-1.13.0"
CHALLENGE_NS = "operator"
CHALLENGE_LOGIN = 0
_TRUTHY = frozenset({"1", "true", "yes", "on"})
_ADMIT_ORDER = ("A_STAND_DOWN", "C_SIZE_TRIM", "D_FULL")
_ADMIT_CRITERIA = {
    "A_STAND_DOWN": "Stand down. This candidate is not admitted.",
    "C_SIZE_TRIM": "Admit this candidate at the returned parameter.",
    "D_FULL": "Admit this candidate in full.",
}
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
    "miss",
    "year_le0",
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
_CHOICE_ID = "policy_c_admit"
_THRESHOLD_ID = "policy_c_admit_threshold"
_PARAMETER_ID = "policy_c_admit_parameter"
_NOUL_ID = "policy_c_state_sufficient"
_STRUCTURAL = frozenset({"model", "login", "ns", "gate", "sidecar_keys"})
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


def policy_c_apply_enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return str(env.get("GTOS_JEV_POLICY_C_APPLY", "")).strip().lower() in _TRUTHY


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
        if _banned_text(value) or _limit_key(value):
            return _DROP
        return value
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if _banned_text(format(value, ".10g")):
            return _DROP
        return value
    return str(value)


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        if _limit_key(key) or key.strip().lower() in _STRUCTURAL:
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
                "true": "The pre-entry state is sufficient for this admit.",
                "false": "The pre-entry state is not sufficient for this admit.",
            },
        }
    }


def _questions(levels: list[str]) -> dict[str, Any]:
    scale = list(levels) if levels else list(_BETWEEN)
    pack: dict[str, Any] = {}
    pack.update(_noul_question(
        _NOUL_ID,
        (
            "Is the pre-entry state sufficient for this admit? "
            "An empty answer leaves this unset. "
            "Do not send an order. Do not flatten."
        ),
    ))
    pack.update(_choice_question(
        _CHOICE_ID,
        (
            "Policy C admit for this pre-entry state. "
            "Pick one option. The unique highest probability is the decision. "
            "An empty answer or a tie is not a decision. "
            "Do not send an order. Do not flatten."
        ),
        _ADMIT_CRITERIA,
    ))
    pack.update(_score_question(
        _THRESHOLD_ID,
        (
            "The score you return is the threshold for this admit. "
            "It may sit between the levels on this state. "
            "An empty score leaves the threshold unset. "
            "Do not send an order."
        ),
        scale,
    ))
    pack.update(_score_question(
        _PARAMETER_ID,
        (
            "The score you return is the parameter for this admit. "
            "It may sit between the levels on this state. "
            "An empty score leaves the parameter unset. "
            "Do not send an order."
        ),
        scale,
    ))
    return pack


def _sidecar_state_for_intent(intent: Any) -> dict[str, Any] | None:
    """Latest voter sidecar for this symbol and sleeve. Facts only."""
    root = Path(__file__).resolve().parents[2]
    admit_root = root / "judgment" / "live" / "jev_sidecar" / "admit"
    override = (os.environ.get("GTOS_JEV_FLUID_GATES_LOG_DIR") or "").strip()
    if override:
        cand = Path(override) / "admit"
        if cand.is_dir():
            admit_root = cand
    if not admit_root.is_dir():
        return None
    symbol = str(getattr(intent, "symbol", None) or getattr(intent, "instrument", None) or "").strip()
    sleeve = str(getattr(intent, "sleeve", None) or getattr(intent, "tag", None) or "").strip()
    details = getattr(intent, "details", None)
    if isinstance(details, dict):
        symbol = symbol or str(details.get("symbol") or "")
        sleeve = sleeve or str(details.get("sleeve") or details.get("tag") or "")
    newest = None
    newest_mtime = -1.0
    try:
        for path in admit_root.rglob("*.json"):
            try:
                mt = path.stat().st_mtime
            except OSError:
                continue
            if mt > newest_mtime:
                newest_mtime = mt
                newest = path
    except Exception:
        return None
    if newest is None:
        return None
    try:
        data = json.loads(newest.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data["_sidecar_path"] = str(newest)
            if symbol:
                data.setdefault("symbol", symbol)
            if sleeve:
                data.setdefault("sleeve", sleeve)
            return data
    except Exception:
        return None
    return None


def _intent_state(intent: Any, sidecar: dict[str, Any] | None) -> dict[str, Any]:
    symbol = str(getattr(intent, "symbol", None) or getattr(intent, "instrument", None) or "")
    sleeve = str(getattr(intent, "sleeve", None) or getattr(intent, "tag", None) or "")
    side = str(getattr(intent, "side", None) or getattr(intent, "direction", None) or "")
    details = getattr(intent, "details", None)
    if isinstance(details, dict):
        symbol = symbol or str(details.get("symbol") or "")
        sleeve = sleeve or str(details.get("sleeve") or details.get("tag") or "")
        side = side or str(details.get("side") or "")
    sc = dict(sidecar or {})
    keys = [str(key) for key in sorted(sc.keys()) if not _limit_key(str(key))]
    return {
        "model": MODEL,
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "gate": "policy_c_strike_when_right",
        "identity": {"symbol": symbol, "sleeve": sleeve, "side": side, "tag": sleeve},
        "symbol": symbol,
        "sleeve": sleeve,
        "side": side,
        "alive": sc.get("alive"),
        "regime_tag": sc.get("regime_tag"),
        "conf_band": sc.get("conf_band"),
        "session_fit": sc.get("session_fit"),
        "full_state_dark": sc.get("full_state_dark"),
        "n_incomplete": sc.get("n_incomplete"),
        "completeness": {
            "missing_fields": sc.get("missing_fields") or [],
            "n_incomplete": sc.get("n_incomplete"),
            "full_state_dark": sc.get("full_state_dark"),
        },
        "sidecar_keys": keys,
        "clock": {"as_of_utc": sc.get("as_of_utc")},
    }


def _choice_of(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
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
    best = max(numeric.values())
    winners = [
        name for name in order if name in numeric and numeric[name] == best
    ]
    if len(winners) != 1:
        return None, numeric
    try:
        from .jev_questions import unique_highest

        picked = unique_highest(dict(numeric), order)
    except Exception:
        picked = winners[0]
    if picked is None or str(picked) != winners[0]:
        return None, numeric
    return winners[0], numeric


def _score_of(block: Any) -> float | None:
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


def _noul_of(block: Any) -> bool | float | None:
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


def _refuse_of(choice: str | None) -> bool | None:
    if choice == "A_STAND_DOWN":
        return True
    if choice in ("C_SIZE_TRIM", "D_FULL"):
        return False
    return None


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []


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


def _post(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    evaluate_fn: Callable[..., Any] | None,
) -> tuple[dict[str, Any], str | None, dict[str, Any]]:
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
            model=MODEL,
        )
    except Exception as exc:
        return {}, type(exc).__name__, {}
    if not isinstance(receipt, dict):
        return {}, "evaluate_not_a_dict", {}
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None
    if not answers:
        error = receipt.get("error") or receipt.get("skipped") or "empty"
    elif receipt.get("ok") is False:
        error = receipt.get("error") or receipt.get("skipped") or "post_failed"
    if error in (None, ""):
        return answers, None, receipt
    return answers, str(error), receipt


def _read(answers: Mapping[str, Any], error: str | None) -> dict[str, Any]:
    choice, probabilities = _choice_of(answers.get(_CHOICE_ID), _ADMIT_ORDER)
    threshold = _score_of(answers.get(_THRESHOLD_ID))
    parameter = _score_of(answers.get(_PARAMETER_ID))
    state_sufficient = _noul_of(answers.get(_NOUL_ID))
    missing = any(item is None for item in (choice, threshold, parameter, state_sufficient))
    return {
        "refuse": _refuse_of(choice),
        "choice": choice,
        "threshold": threshold,
        "parameter": parameter,
        "state_sufficient": state_sufficient,
        "probabilities": probabilities,
        "unique_highest": choice is not None,
        "error": error if missing and error else None,
    }


def _blank(error: str | None) -> dict[str, Any]:
    row = _read({}, error)
    row["source"] = "typesafe_systemone"
    row["model"] = MODEL
    row["broker_effect"] = False
    row["never_order_send"] = True
    row["agent_order_send"] = False
    return row


def evaluate_policy_c_admit(
    intent: Any,
    *,
    environ: Mapping[str, str] | None = None,
    evaluate_fn: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Ask the admit for this pre-entry state. Never sends.

    The apply flag is a fact on the card. The choice, the threshold,
    the parameter, and the sufficiency noul are the System One returns.
    A miss stays unset. It does not stand down and it does not admit.
    """

    apply_on = policy_c_apply_enabled(environ)
    sidecar = _sidecar_state_for_intent(intent)
    cleaned = _scrub(_intent_state(intent, sidecar))
    state = cleaned if isinstance(cleaned, dict) else {}
    state["model"] = MODEL
    state["login"] = CHALLENGE_LOGIN
    state["ns"] = CHALLENGE_NS
    state["policy_c_apply"] = bool(apply_on)
    try:
        _bind_card(state)
        questions = _questions(state)
        _bind_card(None)
    except Exception as exc:
        return _blank(type(exc).__name__)
    asked = ("floor", "baseline")
    for block in questions.values():
        text = json.dumps(block, default=str).lower()
        if any(word in text for word in asked) or _banned_text(text):
            return _blank("question_rejected")
    answers, error, receipt = _post(state, questions, evaluate_fn)
    row = _read(answers, error)
    _remember(
        state,
        (
            (_NOUL_ID, row["state_sufficient"]),
            (_CHOICE_ID, row["choice"]),
            (_THRESHOLD_ID, row["threshold"]),
            (_PARAMETER_ID, row["parameter"]),
        ),
        error,
    )
    row["source"] = "typesafe_systemone"
    row["model"] = receipt.get("model") or MODEL
    row["calls_used"] = receipt.get("calls_used")
    row["calls_remaining"] = receipt.get("calls_remaining")
    row["usage"] = receipt.get("usage")
    row["broker_effect"] = False
    row["never_order_send"] = True
    row["agent_order_send"] = False
    return row
