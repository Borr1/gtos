"""Leftover remaining-if decisions. One System One piece.

One hop: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
Questions on the piece are only Noul, Choice, or Score. Prior outcomes are
attached on that ask, and the return is appended for the next ask.

Each decision, including each parameter, is that return. A Choice is the
unique highest probability. A Score is the returned number and may sit
between levels. A Noul is a bool or a probability. An empty answer, a tie,
a missing score, or an error leaves that field unset.

A floor and a baseline are not asked. ``GTOS_JEV_REMAINING_IFS`` is a fact
on the card. It does not skip the ask. This module does not send and does
not flatten. Judge code stays unable to send.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

MODEL = "jev-1.13.0"
SCHEMA = "gtos.judgment.remaining_ifs.v1"
REMAINING_IFS_ENV = "GTOS_JEV_REMAINING_IFS"
CHALLENGE_LOGIN = 0
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = 0
KIND_READ = "read"
_TRUTHY_ON = frozenset({"1", "true", "yes", "on"})
_SKIP_KEY_PARTS: tuple[str, ...] = ()
_QUESTION_TYPES = frozenset({"noul", "choice", "score"})

SEATS = (
    "companion",
    "occupancy",
    "weekend",
    "overlay",
    "size_bins",
    "frontier",
    "research",
)
BRANCH_SEATS = {
    "observe": ("companion", "weekend", "overlay", "frontier", "research"),
    "size": ("size_bins", "overlay"),
    "place": ("companion", "weekend"),
}
SEAT_CHUNKS = {
    "companion": ("snapshot", "cooldown", "zero_risk"),
    "occupancy": ("keep_one", "flat_clock", "already_placed"),
    "weekend": ("clock", "sleeve_weekend", "policy"),
    "overlay": ("vp_loc", "damage", "energy", "impulse", "session"),
    "size_bins": ("kelly", "stress", "coloss", "voltilt", "na", "lane", "cluster"),
    "frontier": ("geometry", "contract"),
    "research": ("packet", "fill_atom", "allocator", "whiteboard"),
}
CHOICE_ORDER = {
    "companion_action": ("yield", "persist", "abstain"),
    "weekend_entry": ("embargo", "allow", "abstain"),
    "occupancy_after_close": ("reenter", "keep_one", "not_isolated", "first", "abstain"),
    "wait_vs_trade": ("wait", "trade", "abstain"),
    "remaining_component": SEATS,
    "remaining_sibling": ("sleeve", "gold", "news", "abstain"),
}
ACT_QUESTION = {
    "companion": "companion_action",
    "weekend": "weekend_entry",
    "occupancy": "occupancy_after_close",
    "research": "wait_vs_trade",
}
INTEGER_FACTS = (
    "token_digest_match",
    "two_stop_count",
    "named_surface",
    "prop_wall",
    "halt",
    "operator_flatten_flag",
    "occupancy_keep_one",
    "usdjpy_hold",
    "h4cap",
    "weekend_flat_close",
    "never_widen",
    "auto_be_off",
    "fx_dsp_8pip",
    "min_stop_ticks",
    "retry_cap",
    "tuition_150",
    "sel_v4_research_never_place",
    "tags_kill",
    "h8_authority_does_not_flatten",
)
CONVERTED_IF_IDS = (
    "UB-PLC-004",
    "UB-PLC-005",
    "UB-PLC-008",
    "UB-PLC-OCC",
    "UB-PLC-007",
    "UB-ADM-009",
    "UB-ADM-012",
    "UB-ADM-ENERGY",
    "UB-ADM-OVERLAY-IMPULSE",
    "UB-ADM-OVERLAY-SESSION",
    "UB-ADM-KELLY",
    "UB-ADM-STRESS",
    "UB-ADM-COLOSS",
    "UB-ADM-VOLTILT",
    "UB-ADM-NA-DOOMED",
    "UB-LANE-BAND",
    "UB-ADM-CLUSTER-CORR",
    "UB-PLC-FRONTIER",
    "SEL-V4-002",
    "SEL-V4-FILL-F13",
    "SCH-V4-ZERO",
    "PERM-006",
)

# History only when jev_questions cannot be imported. Not copied into a miss.
_LOCAL_OUTCOMES: list[dict[str, Any]] = []
_ASK_LOCK = threading.Lock()
_ASK_JOB: tuple[Any, ...] | None = None
_ASK_RUNNING = False
_ASK_LATEST: str | None = None
_ASK_INFLIGHT: str | None = None
_ASK_KEY: str | None = None
_ASK_RECEIPT: dict[str, Any] | None = None



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


def overlay_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """Env gate. Default off. Explicit 1/true/on enables the overlay."""

    env = environ if environ is not None else os.environ
    raw = str(env.get(REMAINING_IFS_ENV, "")).strip().lower()
    return raw in _TRUTHY_ON


def _is_challenge_account(*, login: Any = None, ns: Any = None) -> bool:
    ns_ok = str(ns or "").strip() == CHALLENGE_NS
    login_ok = False
    if login is not None and str(login).strip() != "":
        try:
            login_ok = int(login) == CHALLENGE_LOGIN
        except (TypeError, ValueError):
            login_ok = False
    if login is None and ns is None:
        return False
    if login is not None and ns is not None and str(login).strip() != "" and str(ns).strip() != "":
        return login_ok and ns_ok
    return login_ok or ns_ok


def _blocked_text(text: str) -> bool:
    low = text.lower()
    return any(part in low for part in _SKIP_KEY_PARTS)


def _scrub(value: Any, seen: set[int] | None = None) -> Any:
    """Drop floor and baseline keys before the ask. Other facts stay facts.

    A repeated container is a cycle. The walk does not cut a card at a count.
    """

    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if seen is None:
        seen = set()
    if isinstance(value, Mapping):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _blocked_text(name):
                continue
            out[name] = _scrub(item, seen)
        return out
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        ident = id(value)
        if ident in seen:
            return None
        seen.add(ident)
        return [_scrub(item, seen) for item in value]
    return None


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


def _probabilities(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, Mapping):
        return {}
    numeric: dict[str, float] = {}
    for key, val in raw.items():
        number = _number(val)
        if number is None:
            continue
        numeric[str(key)] = number
    return numeric


def _unique(probabilities: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie, an empty map, or a bare label is unset."""

    if not probabilities or not order:
        return None
    allowed = [name for name in order if name in probabilities]
    if not allowed:
        return None
    best = max(probabilities[name] for name in allowed)
    winners = [name for name in allowed if probabilities[name] == best]
    if len(winners) != 1:
        return None
    present = {name: probabilities[name] for name in allowed}
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(present, allowed)
    except Exception:
        agreed = winners[0]
    if agreed is None or str(agreed) != winners[0]:
        return None
    return winners[0]


def _score_of(block: Any) -> float | None:
    """The returned score. A tie leaves it unset. The number is not snapped."""

    if isinstance(block, bool) or block is None:
        return None
    if not isinstance(block, dict):
        return _number(block)
    if block.get("error"):
        return None
    numeric = _probabilities(block)
    if numeric and _unique(numeric, tuple(numeric)) is None:
        return None
    try:
        from .jev_questions import returned_number

        parsed = _number(returned_number(block))
        if parsed is not None:
            return parsed
    except Exception:
        pass
    for key in ("score", "value"):
        parsed = _number(block.get(key))
        if parsed is not None:
            return parsed
    return None


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. Missing stays missing."""

    if isinstance(block, bool):
        return block
    if not isinstance(block, dict):
        return _number(block)
    if block.get("error"):
        return None
    if "noul" in block or "Noul" in block:
        raw = block.get("noul") if "noul" in block else block.get("Noul")
        if raw is True or raw is False:
            return raw
        number = _number(raw)
        if number is not None:
            return number
    picked = _unique(_probabilities(block), ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _bool_flag(noul: bool | float | None) -> bool | None:
    """A bool noul is that bool. A probability is not cut into one."""

    if noul is True:
        return True
    if noul is False:
        return False
    return None


def _choice_of(block: Any, order: tuple[str, ...]) -> str | None:
    if not isinstance(block, dict) or block.get("error"):
        return None
    return _unique(_probabilities(block), order)


def include_depth_name(score: float | None) -> float | None:
    """Include-depth is the returned score. A missing score stays missing."""

    return _number(score)


def completeness_noul(answers: Mapping[str, Any] | None) -> bool | float | None:
    """The completeness Noul on this hop. A missing noul stays missing."""

    if not isinstance(answers, Mapping):
        return None
    if "state_sufficient" in answers:
        gold = _noul_of(answers.get("state_sufficient"))
        if gold is not None:
            return gold
    if "remaining_state_sufficient" in answers:
        return _noul_of(answers.get("remaining_state_sufficient"))
    return None


def persist_apply_weight(answers: Mapping[str, Any] | None = None) -> float | None:
    """Persistence is the returned score. A miss stays unset."""

    if not isinstance(answers, Mapping):
        return None
    return _score_of(answers.get("remaining_persist"))


def _question_blocked(qid: Any, spec: Any) -> bool:
    if _blocked_text(str(qid)):
        return True
    if not isinstance(spec, Mapping):
        return True
    if _blocked_text(str(spec.get("instructions") or "")):
        return True
    criteria = spec.get("criteria")
    if isinstance(criteria, Mapping):
        for key, text in criteria.items():
            if _blocked_text(str(key)) or _blocked_text(str(text)):
                return True
    elif isinstance(criteria, (list, tuple)):
        for item in criteria:
            if _blocked_text(str(item)):
                return True
    return False


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": "choice",
        "instructions": instructions,
        "criteria": {str(key): str(value) for key, value in criteria.items()},
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
    body["criteria"] = {str(key): str(value) for key, value in criteria.items()}
    return {qid: body}



def _score_question(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {"true": yes, "false": no},
        }
    }


def _seat_questions(seat: str) -> dict[str, Any]:
    """The seat's Noul, Choice, and Score questions. No floor question."""

    pack: dict[str, Any] = {}
    if seat == "companion":
        pack.update(_score_question(
            "companion_pause_fit",
            "The score you return is how far the named companion snapshot still pauses this fire. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_score_question(
            "companion_cooldown_fit",
            "The score you return is how far the named cooldown still binds this fire. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_score_question(
            "companion_zero_risk_fit",
            "The score you return is how far the named companion still describes zero residual risk. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_choice_question(
            "companion_action",
            "Name yield, persist, or abstain for this companion snapshot. "
            "The option you return is that act. An empty answer or a tie leaves it unset. Do not send.",
            {
                "yield": "The companion snapshot still pauses this fire.",
                "persist": "The companion snapshot no longer pauses this fire.",
                "abstain": "The companion snapshot is unassembled.",
            },
        ))
        pack.update(_score_question(
            "equity_to_pass",
            "The score you return is the cash this hop has on this state. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        return pack
    if seat == "occupancy":
        pack.update(_choice_question(
            "occupancy_after_close",
            "Name the occupancy after this close. The option you return is that name. "
            "An empty answer or a tie leaves it unset. Do not send. Do not flatten.",
            {
                "reenter": "The symbol is flat and this is a new named fire.",
                "keep_one": "The symbol is still occupied.",
                "not_isolated": "The symbol is flat and the window has not elapsed.",
                "first": "There is no prior close on this symbol.",
                "abstain": "Occupancy on this state is unassembled.",
            },
        ))
        pack.update(_score_question(
            "equity_to_pass",
            "The score you return is the cash this hop has on this state. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        return pack
    if seat == "weekend":
        pack.update(_score_question(
            "weekend_carry",
            "The score you return is the weekend carry on this broker clock. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_choice_question(
            "weekend_entry",
            "Name embargo, allow, or abstain for this sleeve on this broker clock. "
            "The option you return is that name. An empty answer or a tie leaves it unset. Do not send.",
            {
                "embargo": "This sleeve on this clock is the whole trade.",
                "allow": "This sleeve still looks legal on this clock.",
                "abstain": "The clock or the sleeve policy is unassembled.",
            },
        ))
        pack.update(_score_question(
            "equity_to_pass",
            "The score you return is the cash this hop has on this state. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        return pack
    if seat == "overlay":
        pack.update(_noul_question(
            "vp_above_va",
            "Is this VP print noise versus the named value area? "
            "The noul you return is that answer. An empty noul leaves it unset. Do not send.",
            "The named VP looks like noise versus the value area.",
            "The named VP still looks like acceptance, or the location is unassembled.",
        ))
        pack.update(_noul_question(
            "damage_consistency",
            "Do the named damage metrics still agree with the integer damage action? "
            "The noul you return is that agreement. An empty noul leaves it unset. Do not send.",
            "The named damage still agrees.",
            "The named damage disagrees, or the metrics are unassembled.",
        ))
        pack.update(_noul_question(
            "energy_still_hurtful",
            "After cost, is the named energy fill still hurtful versus the stop? "
            "The noul you return is that answer. An empty noul leaves it unset. Do not send.",
            "The named energy cost still eats the stop.",
            "The named energy still looks fillable after cost, or it is unassembled.",
        ))
        pack.update(_score_question(
            "impulse_range",
            "The score you return is the impulse range on this bar. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_score_question(
            "overlay_session_hour",
            "The score you return is the hour quality for this sleeve. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        return pack
    if seat == "size_bins":
        pack.update(_score_question(
            "kelly_bin_vs_tape",
            "The score you return is how far today's Kelly bin matches the named tape. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_score_question(
            "stress_streak",
            "The score you return is how far the named streak still argues a shrink. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_noul_question(
            "coloss_continuation",
            "Is the named co-loss still a continuation? "
            "The noul you return is that answer. An empty noul leaves it unset. Do not send.",
            "The named co-loss still looks like continuation.",
            "The named fraction disagrees, or the path is unassembled.",
        ))
        pack.update(_score_question(
            "voltilt_vr",
            "The score you return is the vol ratio tilt on this state. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_score_question(
            "na_doomed_honest",
            "The score you return is how far the running count follows fired-and-placed sleeves. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_score_question(
            "lane_inside_band",
            "The score you return is the weight inside the declared band on this state. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_score_question(
            "cluster_corr_order",
            "The score you return is how far the named cluster still moves as one unit. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        return pack
    if seat == "frontier":
        pack.update(_score_question(
            "frontier_cell_fit",
            "The score you return is how far the named exit cell matches the measured horizon. "
            "It may sit between the levels. An empty score leaves it unset. Do not arm. Do not send.",
        ))
        return pack
    if seat == "research":
        pack.update(_score_question(
            "packet_quality",
            "The score you return is the research packet quality on the named axes. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_noul_question(
            "fillability",
            "Is the named fill atom provenance-complete? "
            "The noul you return is that answer. An empty noul leaves it unset. Do not send.",
            "The named fill atom is provenance-complete.",
            "Provenance is missing, or the fill atom is unassembled.",
        ))
        pack.update(_choice_question(
            "wait_vs_trade",
            "Name wait, trade, or abstain for this research candidate. "
            "The option you return is that name. An empty answer or a tie leaves it unset. Do not send.",
            {
                "wait": "Doing nothing still beats the named candidate.",
                "trade": "The named candidate beats waiting.",
                "abstain": "The research state is thin.",
            },
        ))
        pack.update(_score_question(
            "whiteboard_session",
            "The score you return is how far the named whiteboard still describes this session. "
            "It may sit between the levels. An empty score leaves it unset. Do not send.",
        ))
        pack.update(_noul_question(
            "never_place_research",
            "Does this research state stay off the send? "
            "The noul you return is that answer. An empty noul leaves it unset. This question does not send.",
            "This research state stays off the send.",
            "This research state does not stay off the send.",
        ))
        return pack
    return pack


def _parameter_questions() -> dict[str, Any]:
    """Threshold, loop bound, parameter, persistence, and component. Same ask."""

    pack: dict[str, Any] = {}
    pack.update(_score_question(
        "remaining_threshold",
        "The score you return is the threshold for this remaining-if state. "
        "It may sit between the levels. An empty score leaves the threshold unset. Do not send.",
    ))
    pack.update(_score_question(
        "remaining_loop",
        "The score you return is the loop bound for this remaining-if state. "
        "It may sit between the levels. An empty score leaves the bound unset. Do not send.",
    ))
    pack.update(_score_question(
        "remaining_parameter",
        "The score you return is the parameter for this remaining-if state. "
        "It may sit between the levels. An empty score leaves the parameter unset. Do not send.",
    ))
    pack.update(_score_question(
        "remaining_persist",
        "The score you return is the persistence weight for this state. "
        "It may sit between the levels. An empty score leaves the weight unset. Do not send.",
    ))
    pack.update(_noul_question(
        "remaining_may_send",
        "Does this state leave the integer path free to send? "
        "The noul you return is that answer. An empty noul leaves it unset. This question does not send.",
        "The integer path is free to send.",
        "The integer path is not free to send.",
    ))
    pack.update(_choice_question(
        "remaining_component",
        "Which remaining component exists on this state? "
        "The option you return is that component. An empty answer or a tie leaves it unset. Do not send.",
        {name: f"The {name} component exists on this state." for name in SEATS},
    ))
    pack.update(_noul_question(
        "remaining_component_exists",
        "Does that remaining component exist on this state? "
        "The noul you return is that existence. An empty noul leaves it unset. Do not send.",
        "The component exists on this state.",
        "The component does not exist on this state.",
    ))
    return pack


def _named_seats(branch: str, seats: Iterable[str] | None, seat: str) -> tuple[str, ...]:
    if seats:
        named = tuple(item for item in seats if item in SEATS)
        if named:
            return named
    if seat in SEATS:
        return (seat,)
    mapped = BRANCH_SEATS.get(str(branch or "").strip().lower())
    if mapped:
        return mapped
    return ("companion",)


def _kept(questions: Mapping[str, Any]) -> dict[str, Any]:
    pack: dict[str, Any] = {}
    for qid, spec in questions.items():
        if not isinstance(spec, Mapping):
            continue
        if str(spec.get("type") or "") not in _QUESTION_TYPES:
            continue
        if _question_blocked(qid, spec):
            continue
        pack[str(qid)] = dict(spec)
    return pack


def _guard_facts(state: Mapping[str, Any]) -> dict[str, Any]:
    facts = state.get("facts")
    if isinstance(facts, Mapping):
        return dict(facts)
    return {}


def _active_guards(state: Mapping[str, Any], branch: str) -> tuple[str, ...]:
    """Guard names whose facts are on this card. The branch is the ask's return."""

    facts = _guard_facts(state)
    named = str(branch or "")
    active: list[str] = []
    if facts.get("halt") or state.get("halt"):
        active.append("integer_halt")
    if facts.get("operator_flatten_flag") or facts.get("flatten_flag"):
        active.append("integer_flatten_flag")
    if facts.get("prop_wall") or facts.get("governor_wall"):
        active.append("integer_prop_wall")
    if facts.get("two_stop_exhausted") or facts.get("two_stop_count_hit"):
        active.append("integer_two_stop_count")
    if facts.get("h4cap"):
        active.append("integer_h4cap")
    if facts.get("usdjpy_hold"):
        active.append("integer_usdjpy_hold")
    if facts.get("weekend_flat_close") and named in {"place", "observe"}:
        active.append("integer_weekend_flat_close")
    if facts.get("never_widen") and named == "place":
        active.append("integer_never_widen")
    return tuple(active)


def _integer_questions(state: Mapping[str, Any] | None, branch: str) -> dict[str, Any]:
    """One choice per guard whose fact is on the card. Same pack as the seat."""

    pack: dict[str, Any] = {}
    for name in _active_guards(dict(state or {}), branch):
        pack.update(_choice_question(
            name,
            (
                f"The `{name}` fact is on this card. "
                f"Which branch is this state, `{name}` or continue? "
                "The option you return is the branch. "
                "An empty answer or a tie leaves the branch unset. "
                "Do not send. Do not flatten."
            ),
            {
                name: f"This state takes {name}.",
                "continue": "This state does not take that branch.",
            },
        ))
    return pack


def _guard_branch(
    active: tuple[str, ...],
    choices: Mapping[str, str],
) -> tuple[str | None, bool]:
    """The returned block, and whether a guard is still open.

    A guard is open when its fact is on and the ask did not return continue.
    The block name is set only when the ask returned that name.
    """

    open_guard = False
    for name in active:
        choice = choices.get(name)
        if choice == name:
            return name, True
        if choice != "continue":
            open_guard = True
    return None, open_guard


def _named_tickets(state: Mapping[str, Any]) -> list[int] | None:
    """Broker ticket ids already on the state. A missing list stays missing."""

    if "never_flatten_tickets" not in state:
        return None
    raw = state.get("never_flatten_tickets")
    if not isinstance(raw, (list, tuple, set, frozenset)):
        return None
    out: list[int] = []
    for item in raw:
        try:
            out.append(int(item))
        except (TypeError, ValueError):
            continue
    return out


def _ask_key(state: Mapping[str, Any], questions: Mapping[str, Any]) -> str:
    card = _scrub(dict(state))
    if not isinstance(card, dict):
        card = {}
    card.pop("prior_outcomes", None)
    blob = json.dumps(
        {"card": card, "questions": sorted(str(qid) for qid in questions)},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def _ask_worker() -> None:
    """One ask at a time. The caller does not wait. A changed card drops the old one."""

    global _ASK_RUNNING, _ASK_INFLIGHT, _ASK_KEY, _ASK_RECEIPT
    while True:
        with _ASK_LOCK:
            job = _ASK_JOB
        if job is None:
            with _ASK_LOCK:
                if _ASK_JOB is not None:
                    continue
                _ASK_RUNNING = False
                return
        key, state, questions, timeout_s = job
        with _ASK_LOCK:
            if _ASK_JOB is job:
                globals()["_ASK_JOB"] = None
            _ASK_INFLIGHT = key
        receipt = evaluate_pack(dict(state), questions, timeout_s=timeout_s)
        with _ASK_LOCK:
            if _ASK_LATEST == key and isinstance(receipt, dict):
                _ASK_KEY = key
                _ASK_RECEIPT = receipt
            if _ASK_INFLIGHT == key:
                _ASK_INFLIGHT = None


def _cached_or_kick(
    state: Mapping[str, Any],
    questions: Mapping[str, Any],
    timeout_s: float | None,
) -> dict[str, Any] | None:
    """The receipt for these facts. A miss starts one ask and does not wait."""

    global _ASK_RUNNING, _ASK_LATEST
    if not questions:
        return None
    key = _ask_key(state, questions)
    with _ASK_LOCK:
        if _ASK_KEY == key and isinstance(_ASK_RECEIPT, dict):
            return _ASK_RECEIPT
        if _ASK_INFLIGHT == key:
            _ASK_LATEST = key
            return None
        pending = _ASK_JOB
        if pending is not None and pending[0] == key:
            _ASK_LATEST = key
            return None
        _ASK_LATEST = key
        globals()["_ASK_JOB"] = (key, dict(state), dict(questions), timeout_s)
        if not _ASK_RUNNING:
            _ASK_RUNNING = True
            threading.Thread(target=_ask_worker, name="remaining_ifs_ask", daemon=True).start()
    return None


def piece_questions(
    state: Mapping[str, Any] | None = None,
    *,
    seats: Iterable[str] | None = None,
    branch: str = "observe",
    seat: str = "companion",
    sibling: bool = False,
) -> dict[str, Any]:
    """One pack for this piece. Include-depth, the guards, the seat, and the parameters."""

    _bind_card(state if _is_map(state) else None)
    try:
        named = _named_seats(branch, seats, seat)
        pack: dict[str, Any] = {}
        pack.update(_integer_questions(state, branch))
        pack.update(_noul_question(
            "remaining_state_sufficient",
            "Are the named chunks enough to judge this remaining-if state? "
            "The noul you return is that completeness. An empty noul leaves it unset. Do not send.",
            "The named chunks are enough.",
            "A named chunk is missing.",
        ))
        for name in named:
            for chunk in SEAT_CHUNKS.get(name, ()):
                pack.update(_score_question(
                    f"include_{chunk}",
                    f"The score you return is how much of `{chunk}` this state needs. "
                    "It may sit between the levels. An empty score leaves it unset. Do not send.",
                ))
            pack.update(_seat_questions(name))
        pack.update(_parameter_questions())
        if sibling:
            pack.update(_choice_question(
                "remaining_sibling",
                "Which sibling piece is on this state? "
                "The option you return is that piece. An empty answer or a tie leaves it unset. Do not send.",
                {
                    "sleeve": "The sleeve piece is the sibling on this state.",
                    "gold": "The gold piece is the sibling on this state.",
                    "news": "The news piece is the sibling on this state.",
                    "abstain": "No sibling piece is named.",
                },
            ))
        return _kept(pack)
    finally:
        _bind_card(None)


def _local_priors() -> list[dict[str, Any]]:
    return [dict(item) for item in _LOCAL_OUTCOMES]


def _attach_priors(state: dict[str, Any], questions: Mapping[str, Any]) -> None:
    state.pop("prior_outcomes", None)
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = _local_priors()
        return
    state["prior_outcomes"] = loaded if isinstance(loaded, list) else []


def _remember(state: Mapping[str, Any], pairs: list[tuple[str, Any]], error: str | None) -> None:
    """The return just asked is history for the next ask. A miss stays a miss."""

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
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value in pairs:
        try:
            append_outcome(key, value, logged, error=None if value is not None else error)
        except Exception:
            return


def _read_returns(
    answers: Mapping[str, Any] | None,
    questions: Mapping[str, Any],
) -> dict[str, Any]:
    payload = answers if isinstance(answers, Mapping) else {}
    choices: dict[str, str] = {}
    scores: dict[str, float] = {}
    nouls: dict[str, bool | float] = {}
    returns: dict[str, Any] = {}
    for qid, spec in questions.items():
        if not isinstance(spec, Mapping):
            continue
        kind = str(spec.get("type") or "")
        block = payload.get(qid)
        if kind == "choice":
            order = CHOICE_ORDER.get(str(qid))
            if order is None:
                criteria = spec.get("criteria")
                if isinstance(criteria, Mapping) and criteria:
                    order = tuple(str(key) for key in criteria)
            if not order:
                continue
            choice = _choice_of(block, order)
            if choice is None:
                continue
            choices[str(qid)] = choice
            returns[str(qid)] = {"choice": choice}
            continue
        if kind == "noul":
            noul = _noul_of(block)
            if noul is None:
                continue
            nouls[str(qid)] = noul
            returns[str(qid)] = {"noul": noul}
            continue
        if kind == "score":
            if "_anchor_values" in spec:
                score = _score_of(block)
            else:
                criteria = spec.get("criteria")
                n_levels = len(criteria) if isinstance(criteria, list) else 0
                score = None
                if n_levels >= 2:
                    try:
                        from .jev_questions import ordinal_index

                        score = ordinal_index(block, n_levels)
                    except Exception:
                        score = None
            if score is None:
                continue
            scores[str(qid)] = score
            returns[str(qid)] = {"score": score}
    return {"choices": choices, "scores": scores, "nouls": nouls, "returns": returns}


def _return_pairs(parsed: Mapping[str, Any], questions: Mapping[str, Any]) -> list[tuple[str, Any]]:
    returns = parsed.get("returns") if isinstance(parsed.get("returns"), Mapping) else {}
    pairs: list[tuple[str, Any]] = []
    for qid in questions:
        item = returns.get(qid)
        if not isinstance(item, Mapping):
            pairs.append((str(qid), None))
            continue
        if "choice" in item:
            pairs.append((str(qid), item.get("choice")))
        elif "score" in item:
            pairs.append((str(qid), item.get("score")))
        elif "noul" in item:
            pairs.append((str(qid), item.get("noul")))
        else:
            pairs.append((str(qid), None))
    return pairs


def evaluate_pack(
    state: dict[str, Any],
    questions: Mapping[str, Any],
    *,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. Path and err stay here. Never raises."""

    pack = _kept(questions)
    asked = _scrub(dict(state or {}))
    if not isinstance(asked, dict):
        asked = {}
    asked.pop("prior_outcomes", None)
    asked["model"] = MODEL
    _attach_priors(asked, pack)
    if not pack:
        _remember(asked, [], "empty")
        return {
            "ok": False,
            "skipped": "empty",
            "error": "empty",
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
            "merge_sleeve": False,
        }
    try:
        from .jev_client import evaluate

        receipt = evaluate(
            asked,
            questions=pack,
            timeout_s=timeout_s,
            model=MODEL,
            merge_sleeve=False,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset and must not raise
        _remember(asked, [(qid, None) for qid in pack], type(exc).__name__)
        return {
            "ok": False,
            "skipped": type(exc).__name__,
            "error": type(exc).__name__,
            "model": MODEL,
            "answers": {},
            "kind": KIND_READ,
            "merge_sleeve": False,
        }
    out = dict(receipt) if isinstance(receipt, Mapping) else {"ok": False, "answers": {}}
    out.setdefault("kind", KIND_READ)
    out["model"] = out.get("model") or MODEL
    out["merge_sleeve"] = False
    answers = out.get("answers")
    if not isinstance(answers, dict):
        answers = {}
        out["answers"] = answers
    error = None
    if out.get("ok") is not True or not answers:
        error = str(out.get("error") or out.get("skipped") or "empty")
        out.setdefault("skipped", error)
        out.setdefault("error", error)
        out["answers"] = answers
    parsed = _read_returns(answers, pack)
    _remember(asked, _return_pairs(parsed, pack), error)
    return out


def _split_answers(answers: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    include: dict[str, Any] = {}
    decision: dict[str, Any] = {}
    for key, value in answers.items():
        if str(key).startswith("include_"):
            include[str(key)] = value
        else:
            decision[str(key)] = value
    return include, decision


def fanout_remaining_ifs(
    state: dict[str, Any],
    *,
    seat: str = "companion",
    branch: str = "observe",
    evaluate_jev: bool = True,
    include_answers: Mapping[str, Any] | None = None,
    decision_answers: Mapping[str, Any] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """One evaluate for this intent. Include-depth and the decision are that return."""

    questions = piece_questions(state, seat=seat, branch=branch)
    if include_answers is not None and decision_answers is not None:
        merged: dict[str, Any] = {}
        merged.update(dict(include_answers))
        merged.update(dict(decision_answers))
        include, decision = _split_answers(merged)
        return {
            "ok": True,
            "skipped": None,
            "answers": merged,
            "include_receipt": {"ok": True, "skipped": None, "answers": include},
            "decision_receipt": {"ok": True, "skipped": None, "answers": decision},
            "n_calls": 0,
            "kind": KIND_READ,
            "merge_sleeve": False,
            "never_second_llm_hop": True,
            "model": MODEL,
        }
    if not evaluate_jev:
        merged = {}
        if include_answers is not None:
            merged.update(dict(include_answers))
        if decision_answers is not None:
            merged.update(dict(decision_answers))
        include, decision = _split_answers(merged)
        return {
            "ok": False,
            "skipped": "evaluate_jev_false",
            "answers": merged,
            "include_receipt": {"ok": include_answers is not None, "skipped": "evaluate_jev_false", "answers": include},
            "decision_receipt": {"ok": decision_answers is not None, "skipped": "evaluate_jev_false", "answers": decision},
            "n_calls": 0,
            "kind": KIND_READ,
            "merge_sleeve": False,
            "never_second_llm_hop": True,
            "model": MODEL,
        }
    receipt = evaluate_pack(dict(state), questions, timeout_s=timeout_s)
    got = receipt.get("answers")
    merged = dict(got) if isinstance(got, Mapping) else {}
    if include_answers is not None:
        merged = {key: value for key, value in merged.items() if not str(key).startswith("include_")}
        merged.update(dict(include_answers))
    if decision_answers is not None:
        merged = {key: value for key, value in merged.items() if str(key).startswith("include_")}
        merged.update(dict(decision_answers))
    include, decision = _split_answers(merged)
    ok = receipt.get("ok") is True and bool(merged)
    return {
        "ok": ok,
        "skipped": None if ok else receipt.get("skipped"),
        "answers": merged,
        "include_receipt": {"ok": ok, "skipped": receipt.get("skipped"), "answers": include},
        "decision_receipt": {"ok": ok, "skipped": receipt.get("skipped"), "answers": decision},
        "n_calls": 1,
        "kind": KIND_READ,
        "merge_sleeve": False,
        "never_second_llm_hop": True,
        "model": MODEL,
    }


def _identity(state: Mapping[str, Any]) -> dict[str, Any]:
    raw = state.get("identity")
    return dict(raw) if isinstance(raw, Mapping) else {}


def _ticket(state: Mapping[str, Any]) -> int | None:
    raw = _identity(state).get("ticket")
    if raw in (None, ""):
        raw = state.get("ticket")
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _not_challenge(state: Mapping[str, Any]) -> bool:
    identity = _identity(state)
    login = identity.get("login")
    ns = identity.get("ns")
    if login is None and ns is None:
        return False
    return not _is_challenge_account(login=login, ns=ns)


def _verification_quarantined(state: Mapping[str, Any]) -> bool:
    identity = _identity(state)
    facts = state.get("facts") if isinstance(state.get("facts"), Mapping) else {}
    if (
        identity.get("verification_quarantined") is True
        or state.get("verification_quarantined") is True
        or facts.get("verification_quarantined") is True
    ):
        return True
    login = identity.get("login")
    if login is None:
        return False
    try:
        from .challenge import VERIFICATION_QUARANTINED
    except Exception:
        return False
    try:
        return str(int(login)) == str(int(VERIFICATION_QUARANTINED))
    except (TypeError, ValueError):
        return str(login).strip() == str(VERIFICATION_QUARANTINED)


def _token_mismatch(state: Mapping[str, Any]) -> bool:
    """Authorization. A digest mismatch stays a mismatch. It is not a market hop."""

    return bool(_guard_facts(state).get("token_digest_mismatch"))


def _labels(state: Mapping[str, Any], seat: str, branch: str) -> dict[str, Any]:
    identity = _identity(state)
    clock = state.get("clock") if isinstance(state.get("clock"), Mapping) else {}
    return {
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "family_node": seat,
        "sleeve": identity.get("sleeve"),
        "symbol": identity.get("symbol"),
        "side": identity.get("side"),
        "ticket": identity.get("ticket") if identity.get("ticket") is not None else state.get("ticket"),
        "branch": branch,
        "as_of_utc": clock.get("as_of_utc"),
    }


def _base(
    state: Mapping[str, Any],
    *,
    seat: str,
    branch: str,
    enabled: bool,
    questions: Mapping[str, Any],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    labels = _labels(state, seat, branch)
    ticket = _ticket(state)
    tickets = _named_tickets(state)
    row = {
        "schema": SCHEMA,
        "model": MODEL,
        "book": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "overlay": REMAINING_IFS_ENV,
        "overlay_enabled": enabled,
        "labels": labels,
        "family_node": labels.get("family_node"),
        "seat": seat,
        "branch": branch,
        "ticket": ticket,
        "integer_facts": list(INTEGER_FACTS),
        "converted_if_ids": list(CONVERTED_IF_IDS),
        "question_ids": list(questions),
        "one_piece": True,
        "named_never_flatten_ticket": (
            ticket in tickets if tickets and ticket else (False if tickets is not None else None)
        ),
        "never_flatten_tickets": tickets,
        "does_not_flatten": True,
        "does_not_send": True,
        **dict(extra or {}),
    }
    return row


def _thin(noul: bool | float | None) -> bool | None:
    if noul is True:
        return False
    if noul is False:
        return True
    return None


def _include_depth(scores: Mapping[str, float]) -> dict[str, str]:
    """Returned include scores. A missing score is omitted. The number is not snapped."""

    out: dict[str, str] = {}
    for qid, score in scores.items():
        if not str(qid).startswith("include_"):
            continue
        number = _number(score)
        if number is None:
            continue
        out[str(qid)[len("include_") :]] = format(number, ".10g")
    return out


def _disposition(choices: Mapping[str, str], seats: Iterable[str]) -> str | None:
    ids = [ACT_QUESTION[name] for name in seats if name in ACT_QUESTION]
    picked = [choices[qid] for qid in ids if qid in choices]
    if len(picked) == 1:
        return picked[0]
    if len(picked) > 1 and len(set(picked)) == 1:
        return picked[0]
    return None


@dataclass(frozen=True)
class RemainingIfsDecision:
    """The remaining-if return. A miss stays unset. This piece does not send."""

    disposition: str | None = None
    reason: str | None = None
    extra_pass: bool = False
    may_send: bool | None = None
    leave_orig: bool | None = None
    extra_place: bool = False
    extra_flatten: bool = False
    extra_arm_frontier: bool = False
    never_place_research: bool | None = None
    include_depth: dict[str, str] = field(default_factory=dict)
    missing_jev: bool = False
    jev_no_decision: bool = False
    persist_apply: float | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.payload,
            "disposition": self.disposition,
            "reason": self.reason,
            "kind": "choice" if self.disposition else KIND_READ,
            "persist_weight": self.persist_apply,
            "persist_apply": self.persist_apply,
            "flatten": False,
            "place": False,
            "apply": False,
            "extra_pass": False,
            "may_send": self.may_send,
            "leave_orig": self.leave_orig,
            "extra_place": False,
            "extra_flatten": False,
            "extra_arm_frontier": False,
            "never_place_research": self.never_place_research,
            "include_depth": dict(self.include_depth),
            "missing_jev": self.missing_jev,
            "jev_no_decision": self.jev_no_decision,
            "broker_effect": False,
            "does_not_send": True,
            "does_not_flatten": True,
        }


def _gate(*, reason: str, base: dict[str, Any]) -> RemainingIfsDecision:
    return RemainingIfsDecision(
        disposition=None,
        reason=reason,
        may_send=None,
        leave_orig=None,
        persist_apply=None,
        missing_jev=False,
        jev_no_decision=True,
        payload={**base, "skipped": reason, "choice": None, "threshold": None, "loop_bound": None, "parameter": None},
    )


def _answers_missing(answers: Mapping[str, Any] | None) -> bool:
    return not isinstance(answers, Mapping) or len(answers) == 0


def compose_remaining_ifs(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    *,
    seat: str = "companion",
    branch: str = "observe",
    seats: Iterable[str] | None = None,
    environ: Mapping[str, str] | None = None,
    extra: Mapping[str, Any] | None = None,
    evaluate_jev: bool = True,
    timeout_s: float | None = None,
    ask_sibling_hops: bool = True,
) -> RemainingIfsDecision:
    """Read this state's return. A miss does not restore a constant."""

    state_map = dict(state or {})
    enabled = overlay_enabled(environ=environ)
    state_map["overlay_enabled"] = enabled
    named = _named_seats(branch, seats, seat)
    seat_n = seat if seat in SEATS else named[0]
    questions = piece_questions(
        state_map,
        seats=named,
        branch=branch,
        seat=seat_n,
        sibling=ask_sibling_hops,
    )
    base = _base(
        state_map,
        seat=seat_n,
        branch=branch,
        enabled=enabled,
        questions=questions,
        extra=extra,
    )
    if _verification_quarantined(state_map):
        return _gate(reason="verification_quarantined", base=base)
    if _not_challenge(state_map):
        return _gate(reason="not_challenge_integer_path", base=base)
    if _token_mismatch(state_map):
        return _gate(reason="integer_token_digest", base=base)

    missing = _answers_missing(answers)
    error: str | None = None
    if missing and evaluate_jev:
        receipt = _cached_or_kick(state_map, questions, timeout_s)
        got = receipt.get("answers") if isinstance(receipt, Mapping) else None
        if isinstance(receipt, Mapping) and receipt.get("ok") is True and isinstance(got, Mapping) and got:
            answers = got
            missing = False
        else:
            answers = None
            error = str((receipt or {}).get("error") or (receipt or {}).get("skipped") or "empty") if isinstance(receipt, Mapping) else "empty"
            base["live_fanout_ok"] = False
            base["live_fanout_skipped"] = error
    elif missing:
        error = "evaluate_jev_false"

    parsed = _read_returns(None if missing else answers, questions)
    choices = parsed["choices"]
    scores = parsed["scores"]
    nouls = parsed["nouls"]
    any_return = bool(parsed["returns"])
    active = _active_guards(state_map, branch)
    block_name, guard_open = _guard_branch(active, choices)
    disposition = _disposition(choices, named)
    noul = completeness_noul(None if missing else answers)
    persist = scores.get("remaining_persist")
    if persist is None:
        persist = persist_apply_weight(None if missing else answers)
    may_send = _bool_flag(nouls.get("remaining_may_send"))
    research_place = _bool_flag(nouls.get("never_place_research"))
    reason: str | None
    if block_name is not None:
        reason = block_name
        disposition = block_name
        may_send = None
    elif guard_open:
        reason = error or "empty"
        disposition = None
        may_send = None
    elif disposition is not None:
        reason = disposition
    elif any_return:
        reason = None
    else:
        reason = error or "empty"
    act_id = ACT_QUESTION.get(seat_n)
    act_block = None if missing or act_id is None or not isinstance(answers, Mapping) else answers.get(act_id)
    payload = {
        **base,
        "choice": disposition,
        "threshold": scores.get("remaining_threshold"),
        "loop_bound": scores.get("remaining_loop"),
        "parameter": scores.get("remaining_parameter"),
        "component": choices.get("remaining_component"),
        "component_exists": nouls.get("remaining_component_exists"),
        "remaining_sibling": choices.get("remaining_sibling"),
        "completeness_noul": noul,
        "thin_state": _thin(noul),
        "probabilities": _probabilities(act_block),
        "returns": parsed["returns"],
        "live_hop": f"{seat_n}:{branch}",
        "error": None if any_return else error,
    }
    for qid in questions:
        kind = str(questions[qid].get("type") or "")
        if kind == "choice":
            payload[qid] = choices.get(qid)
        elif kind == "score":
            payload[qid] = scores.get(qid)
        elif kind == "noul":
            payload[qid] = nouls.get(qid)
    return RemainingIfsDecision(
        disposition=disposition,
        reason=reason,
        may_send=may_send,
        leave_orig=None,
        include_depth=_include_depth(scores),
        missing_jev=bool(missing and evaluate_jev),
        jev_no_decision=not any_return or guard_open and block_name is None,
        never_place_research=research_place,
        persist_apply=persist,
        payload=payload,
    )


def compose_companion(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> RemainingIfsDecision:
    return compose_remaining_ifs(state, answers, seat="companion", branch="place", **kwargs)


def compose_occupancy(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> RemainingIfsDecision:
    return compose_remaining_ifs(state, answers, seat="occupancy", branch="observe", **kwargs)


def compose_weekend(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> RemainingIfsDecision:
    return compose_remaining_ifs(state, answers, seat="weekend", branch="observe", **kwargs)


def compose_overlay(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> RemainingIfsDecision:
    return compose_remaining_ifs(state, answers, seat="overlay", branch="observe", **kwargs)


def compose_size_bins(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> RemainingIfsDecision:
    return compose_remaining_ifs(state, answers, seat="size_bins", branch="size", **kwargs)


def compose_frontier(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> RemainingIfsDecision:
    return compose_remaining_ifs(state, answers, seat="frontier", branch="observe", **kwargs)


def compose_research(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> RemainingIfsDecision:
    return compose_remaining_ifs(state, answers, seat="research", branch="observe", **kwargs)


def compose_from_intent(
    state: Mapping[str, Any] | None,
    answers: Mapping[str, Any] | None = None,
    *,
    seat: str = "companion",
    branch: str = "observe",
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """One intent, one evaluate, one piece. The return is the decision."""

    questions = piece_questions(state, seat=seat, branch=branch, sibling=True)
    decision = compose_remaining_ifs(
        state,
        answers,
        seat=seat,
        branch=branch,
        environ=environ,
        ask_sibling_hops=True,
    )
    return {
        "ask_together": True,
        "never_second_llm_hop": True,
        "questions": list(questions),
        "noul_ids": [qid for qid, spec in questions.items() if spec.get("type") == "noul"],
        "decision": decision.as_dict(),
        "model": MODEL,
        "merge_sleeve": False,
        "does_not_send": True,
        "does_not_flatten": True,
    }


def for_send_choke(
    state: Mapping[str, Any] | None = None,
    *,
    intent: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Remaining walls on this state. This choke does not send and does not flatten."""

    del intent
    decision = compose_remaining_ifs(
        state,
        None,
        seat="companion",
        branch="observe",
        environ=environ,
        ask_sibling_hops=True,
        timeout_s=timeout_s,
    )
    row = decision.as_dict()
    row["hop"] = "remaining_walls"
    row["place"] = False
    row["flatten"] = False
    row["apply"] = False
    row["broker_effect"] = False
    row["mill_url"] = None
    return row
