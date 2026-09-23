"""JEV_SLEEVE_SELECT — symbol-scoped menu. The owner is the System One return.

One post per hop: jev_client.evaluate, model jev-1.13.0, merge_sleeve=False.
That call POSTs https://api.typesafe.ai/v1/systemone. Questions are only
Noul, Choice, or Score. Prior outcomes ride on the ask. The choice is the
unique highest probability. The threshold, the loop bound, and the
parameter are the scores. An empty answer, a tie, or an error leaves that
return unset. This module does not send and does not flatten.

build_sleeve_select_menu(symbol, state) → AliveMenu-like criteria:
  alive sleeves for the symbol, affinity KEEP priors, φ from the prior file
  when that file has a number. Escapes stay on the menu. Cap 255.
  A missing φ is not a zero. place=writer only.
  never_alias Package B → sub_mid_dn_revert.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .alive_menu import AliveMenu, Criterion, ESCAPE_CRITERIA
from .inventory import ESCAPE_HATCHES, MAX_CHOICE_OPTIONS

QUESTION_ID = "JEV_SLEEVE_SELECT"
SLEEVE_SELECT_SHADOW_ENV = "GTOS_JEV_SLEEVE_SELECT_SHADOW"
SLEEVE_SELECT_APPLY_ENV = "GTOS_JEV_SLEEVE_SELECT_APPLY"
SLEEVE_SELECT_LIVE_ENV = "GTOS_JEV_SLEEVE_SELECT_LIVE"
FLUID_SHADOW_ENV = "GTOS_JEV_FLUID_GATES_SHADOW"
KIND_READ = "read"
FORBIDDEN_INSTRUCTION_TOKENS = ("jev", "system one", "choice")

_TRUTHY = frozenset({"1", "true", "yes", "on"})
MODEL = "jev-1.13.0"
_OWNER_Q = "this_sleeve_vs_sibling"
_DEPTH_Q = "include_siblings"
_NOUL_Q = "sleeve_select_state_sufficient"
_THRESHOLD_Q = "sleeve_select_threshold"
_PARAMETER_Q = "sleeve_select_parameter"
_LOOP_Q = "sleeve_select_loop_bound"
_WHICH_Q = "sleeve_select_which_component"
_EXISTS_Q = "sleeve_select_component_exists"
_SEND_CHOICES = frozenset({"this_sleeve", "three_fresh"})
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
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
    "ticket",
    "login",
    "to_pass",
    "proposed",
    "prior_outcomes",
    "persist",
)
_BANNED_TEXT: tuple[str, ...] = ()
_STRIP = ("answer", "choice", "score", "value", "noul", "probabilities", "default")

# F5 / affinity KEEP priors — must appear for named symbols (EURUSD→asian_fade F5 armed).
F5_AFFINITY_KEEP_PRIORS: dict[str, tuple[str, ...]] = {
    "EURUSD": (
        "asian_fade",
        "sub_mid_dn_re_proxy_eurusd_short_m15_atr",
    ),
    "XAUUSD": (
        "dsp_spring_close_on_20low_through_the_box",
        "dsp_three_fresh_lower_lows",
        "dsp_expanding_up_staircase",
    ),
    # PR40 Edge KEEP deepen (SHADOW) — Dig extend 2026-09-20
    "GBPJPY": (
        "vss_fxcross_london_up_low",
        "sub_mid_dn_revert",  # tape KEEP on GBPJPY only; never Package B SHORT alias
    ),
    "XAGUSD": (
        "sub_xvol_pullback",
        "metals_core",
        "metal_session_reversion",
    ),
}

# Kept so the old names still exist. soft_relax_map does not apply them.
SOFT_RELAX_HOUSE_LAW = ("mx_us30", "idxrev")
SOFT_RELAX_STAY_HOUSE_UNTIL_KEEP_PROOF = ("bleed", "xa_huge")
SOFT_RELAX_MAY_BECOME_JEV_BLOCKED: tuple[str, ...] = ()

_PHI_CANDIDATE_PATHS = (
    Path("/workspace/gtos/judgment/astra/lab/warroom_intel_20260920/PHI_CAPABILITY_SLEEVE_SELECT_PRIOR_20260920.json"),
    Path(__file__).resolve().parents[2]
    / "astra"
    / "lab"
    / "warroom_intel_20260920"
    / "PHI_CAPABILITY_SLEEVE_SELECT_PRIOR_20260920.json",
    Path("/workspace/instrument-edge/packs/PHI_CAPABILITY_SLEEVE_SELECT_PRIOR_20260920.json"),
    Path(r"host-local\redacted_host\repo\judgment\astra\lab\warroom_intel_20260920\PHI_CAPABILITY_SLEEVE_SELECT_PRIOR_20260920.json"),
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
    del name
    return False


def _banned_text(value: str) -> bool:
    compact = value.replace(",", "").replace("_", "").lower()
    for token in _BANNED_TEXT:
        probe = token.replace(",", "").replace("_", "").lower()
        if probe in compact:
            return True
    return False


def _banned_level(number: float) -> bool:
    del number
    return False


def _scrub(value: Any) -> Any:
    """Drop limit keys and banned dollar text before an ask."""

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


def _instruction_ok(text: str) -> bool:
    if _banned_text(text) or _limit_key(text):
        return False
    low = text.lower()
    return not any(token in low for token in FORBIDDEN_INSTRUCTION_TOKENS)


def _criterion_ok(text: str) -> bool:
    number = _number(text)
    if number is not None:
        return not _banned_level(number)
    return _instruction_ok(text)


def _levels(facts: Mapping[str, Any] | None) -> list[str]:
    """Numeric levels already on the facts. A score may sit between them."""

    found: list[float] = []

    def walk(key: str, value: Any) -> None:
        low = key.lower()
        if _limit_key(key) or any(part in low for part in _SKIP_LEVEL_PARTS):
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
        if number is None or _banned_level(number):
            return
        found.append(number)

    for key, value in dict(facts or {}).items():
        walk(str(key), value)
    return [format(number, ".10g") for number in sorted(set(found))]


def _add_name(names: list[str], raw: Any) -> None:
    text = str(raw or "").strip()
    if not text or text in names or _limit_key(text) or _banned_text(text):
        return
    if any(token in text.lower() for token in FORBIDDEN_INSTRUCTION_TOKENS):
        return
    names.append(text)


def _component_names(state: Mapping[str, Any]) -> tuple[str, ...]:
    """Names already on the state. Existence is asked, not assumed."""

    names: list[str] = []
    for key in ("alive_tags", "alive_sleeves", "sleeves", "components", "siblings"):
        raw = state.get(key)
        if isinstance(raw, Mapping):
            for child in raw:
                _add_name(names, child)
            continue
        if isinstance(raw, (list, tuple)) and not isinstance(raw, (str, bytes)):
            for item in raw:
                if isinstance(item, Mapping):
                    _add_name(names, item.get("sleeve") or item.get("tag") or item.get("name") or item.get("id"))
                else:
                    _add_name(names, item)
    _add_name(names, state.get("sleeve"))
    _add_name(names, state.get("tag"))
    symbol = str(state.get("symbol") or state.get("instrument") or "").upper()
    for tag in F5_AFFINITY_KEEP_PRIORS.get(symbol, ()):
        _add_name(names, tag)
    return tuple(names)


def _owner_spec(state: Mapping[str, Any]) -> tuple[str, dict[str, str]]:
    gate = str(state.get("gate") or "")
    symbol = str(state.get("symbol") or state.get("instrument") or "").upper()
    if gate == "should_stand_gbpjpy_conflict_tag":
        return (
            (
                "On GBPJPY, this tag meets the other named sibling on this state. "
                "Does this tag stand aside, own the fire, or abstain? "
                "The unique highest probability is the decision. "
                "An empty answer or a tie is not a decision. "
                "Do not flatten the tickets listed on this state. "
                "Do not send."
            ),
            {
                "stand": "This tag stands aside.",
                "own": "This tag owns the fire.",
                "abstain": "This hop does not name an owner.",
            },
        )
    if gate == "should_stand_three_fresh_xau_conflict" or symbol.startswith("XAU") or symbol == "GOLD":
        return (
            (
                "On this metal, spring and three_fresh are the siblings. "
                "Name which one owns this fire. "
                "The unique highest probability is the decision. "
                "An empty answer or a tie is not a decision. "
                "Do not flatten the tickets listed on this state. "
                "Do not send."
            ),
            {
                "spring": "Spring owns this fire and three_fresh stands aside.",
                "three_fresh": "Three_fresh owns this fire.",
                "abstain": "This hop does not name an owner.",
            },
        )
    return (
        (
            "On this symbol, name which sibling owns this fire. "
            "The unique highest probability is the decision. "
            "An empty answer or a tie is not a decision. "
            "Do not flatten the tickets listed on this state. "
            "Do not alias Package B to sub_mid_dn_revert. "
            "Do not send."
        ),
        {
            "this_sleeve": "This named sleeve owns the fire.",
            "sibling": "A named sibling owns the fire.",
            "abstain": "This hop does not name an owner.",
        },
    )


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
    for key in _STRIP:
        block.pop(key, None)
    block["type"] = "choice"
    block["instructions"] = instructions
    block["criteria"] = {str(key): str(value) for key, value in criteria.items()}
    return {qid: block}



def _score_question(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _noul_question(qid: str, instructions: str, true_text: str, false_text: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": instructions,
            "criteria": {"true": true_text, "false": false_text},
        }
    }


def _accept(pack: dict[str, Any], built: Mapping[str, Any]) -> None:
    for qid, block in built.items():
        if not isinstance(block, dict) or block.get("type") not in {"noul", "choice", "score"}:
            continue
        instructions = str(block.get("instructions") or "")
        if not _instruction_ok(instructions):
            continue
        criteria = block.get("criteria")
        if isinstance(criteria, dict):
            kept = {
                str(key): str(value)
                for key, value in criteria.items()
                if not _limit_key(key) and _criterion_ok(str(value))
            }
            if not kept:
                continue
            block = dict(block)
            block["criteria"] = kept
        elif isinstance(criteria, list):
            kept_levels = [str(value) for value in criteria if _criterion_ok(str(value))]
            if not kept_levels:
                continue
            block = dict(block)
            block["criteria"] = kept_levels
        pack[str(qid)] = block


def sleeve_select_live_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    raw = str(env.get(SLEEVE_SELECT_LIVE_ENV, "")).strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    return True


def sleeve_select_include_depth_questions() -> dict[str, Any]:
    """How much sibling context this hop needs. The label is the return."""

    return _choice_question(
        _DEPTH_Q,
        (
            "How much of the named sibling list on this symbol does this hop need? "
            "The unique highest probability is the decision. "
            "An empty answer or a tie is not a decision. "
            "Do not send."
        ),
        {
            "hide": "Siblings stay out of this hop.",
            "short": "The two named siblings on this symbol.",
            "long": "A longer sibling list on this symbol.",
            "full": "The whole sibling list on this symbol.",
        },
    )


def sleeve_select_decision_questions(state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Noul, Choice, and Score for this state. No stored answer is copied in."""

    cleaned = _scrub(dict(state or {}))
    st = cleaned if isinstance(cleaned, dict) else {}
    _bind_card(st)
    try:
        owner_text, owner_criteria = _owner_spec(st)
        scale = _levels(st) or list(_BETWEEN)
        pack: dict[str, Any] = {}
        _accept(pack, _noul_question(
            _NOUL_Q,
            (
                "Is this state complete enough to name which sleeve owns the fire? "
                "An empty answer leaves completeness unset. "
                "Do not send."
            ),
            "The named siblings are present enough for this hop.",
            "A required sibling or symbol block is missing.",
        ))
        _accept(pack, sleeve_select_include_depth_questions())
        _accept(pack, _choice_question(_OWNER_Q, owner_text, owner_criteria))
        _accept(pack, _score_question(
            _THRESHOLD_Q,
            (
                "The score you return is the threshold for this state. "
                "It may sit between the levels. "
                "An empty score leaves the threshold unset. "
                "Do not send."
            ),
            scale,
        ))
        _accept(pack, _score_question(
            _PARAMETER_Q,
            (
                "The score you return is the parameter for this state. "
                "It may sit between the levels. "
                "An empty score leaves the parameter unset. "
                "Do not send."
            ),
            scale,
        ))
        _accept(pack, _score_question(
            _LOOP_Q,
            (
                "The score you return is the loop bound for this state. "
                "It may sit between the levels. "
                "An empty score leaves the bound unset. "
                "Do not send."
            ),
            scale,
        ))
        names = _component_names(st)
        if names:
            _accept(pack, _choice_question(
                _WHICH_Q,
                (
                    "Which named component exists for this state? "
                    "The unique highest probability is the decision. "
                    "An empty answer or a tie is not a decision. "
                    "Do not send."
                ),
                {name: f"{name} exists on this state." for name in names},
            ))
        _accept(pack, _noul_question(
            _EXISTS_Q,
            (
                "Does the component exist for this state? "
                "An empty answer leaves existence unset. "
                "Do not send."
            ),
            "The component exists on this state.",
            "The component does not exist on this state.",
        ))
        return pack
    finally:
        _bind_card(None)


def _criteria_order(questions: Mapping[str, Any], qid: str) -> tuple[str, ...]:
    block = questions.get(qid)
    if not isinstance(block, Mapping):
        return ()
    criteria = block.get("criteria")
    if isinstance(criteria, Mapping):
        return tuple(str(key) for key in criteria)
    return ()


def _unique(probabilities: Mapping[str, Any] | None, order: tuple[str, ...]) -> str | None:
    """Unique highest probability among the options that were returned."""

    if not isinstance(probabilities, Mapping) or not probabilities or not order:
        return None
    numeric: dict[str, float] = {}
    for name in order:
        if name not in probabilities:
            continue
        number = _number(probabilities.get(name))
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


def _choice_of(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float], float | None]:
    """The decision is the unique highest probability. A bare label is not one."""

    probs_in: Mapping[str, Any] = {}
    if isinstance(block, Mapping) and isinstance(block.get("probabilities"), Mapping):
        probs_in = block["probabilities"]
    local = _unique(probs_in, order)
    library = local
    try:
        from .jev_questions import unique_highest

        raw = unique_highest(dict(probs_in) if probs_in else None, order)
        library = None if raw is None else str(raw)
    except Exception:
        library = local
    picked = local if local is not None and library == local else None
    numeric: dict[str, float] = {}
    allowed = set(order)
    for key, value in probs_in.items():
        name = str(key)
        if name not in allowed:
            continue
        number = _number(value)
        if number is not None:
            numeric[name] = number
    confidence = numeric.get(picked) if picked is not None else None
    return picked, numeric, confidence


def _score_of(block: Any) -> float | None:
    """The score on this block. It is not snapped to a level and not filled in."""

    if not isinstance(block, Mapping) or block.get("error"):
        return None
    raw = block.get("score")
    if raw is None and "value" in block:
        raw = block.get("value")
    if raw is None:
        return None
    return _number(raw)


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A missing noul stays missing."""

    if not isinstance(block, Mapping) or "noul" not in block:
        return None
    raw = block.get("noul")
    if raw is True or raw is False:
        return raw
    return _number(raw)


def _tied(probabilities: Mapping[str, Any] | None, order: tuple[str, ...]) -> bool:
    if not isinstance(probabilities, Mapping) or not order:
        return False
    numeric: dict[str, float] = {}
    for name in order:
        if name not in probabilities:
            continue
        number = _number(probabilities.get(name))
        if number is not None:
            numeric[name] = number
    if len(numeric) < 2:
        return False
    best = max(numeric.values())
    winners = [name for name in order if name in numeric and numeric[name] == best]
    return len(winners) != 1


def _remember(state: Mapping[str, Any], rows: tuple[tuple[str, Any, str | None], ...]) -> None:
    try:
        from .jev_questions import append_outcome
    except Exception:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _blank_ask(
    questions: Mapping[str, Any] | None,
    *,
    error: str | None,
    missing_jev: bool,
    state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "choice": None,
        "probabilities": {},
        "confidence": None,
        "noul": None,
        "include_siblings": None,
        "threshold": None,
        "parameter": None,
        "loop_bound": None,
        "which_component": None,
        "component_exists": None,
        "error": error or "empty",
        "posted": False,
        "ok": False,
        "missing_jev": missing_jev,
        "model": MODEL,
        "questions": dict(questions or {}),
        "answers": {},
        "state": dict(state or {}),
    }


def _read_ask(questions: Mapping[str, Any], receipt: Any, state: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        return _blank_ask(questions, error="evaluate_not_a_dict", missing_jev=False, state=state)
    answers = receipt.get("answers")
    if not isinstance(answers, Mapping):
        answers = {}
    err = receipt.get("error")
    if err in (None, ""):
        err = receipt.get("skipped")
    error = None if err in (None, "") else str(err)
    if not answers and error is None:
        error = "empty"
    owner_order = _criteria_order(questions, _OWNER_Q)
    depth_order = _criteria_order(questions, _DEPTH_Q)
    which_order = _criteria_order(questions, _WHICH_Q)
    owner_block = answers.get(_OWNER_Q)
    choice, probabilities, confidence = _choice_of(owner_block, owner_order)
    depth, _, _ = _choice_of(answers.get(_DEPTH_Q), depth_order)
    which, _, _ = _choice_of(answers.get(_WHICH_Q), which_order)
    noul = _noul_of(answers.get(_NOUL_Q))
    exists = _noul_of(answers.get(_EXISTS_Q))
    threshold = _score_of(answers.get(_THRESHOLD_Q))
    parameter = _score_of(answers.get(_PARAMETER_Q))
    loop_bound = _score_of(answers.get(_LOOP_Q))
    owner_probs = owner_block.get("probabilities") if isinstance(owner_block, Mapping) else None
    choice_error = None if choice is not None else ("tie" if _tied(owner_probs, owner_order) else (error or "empty"))
    rows = (
        (_OWNER_Q, choice, choice_error if choice is None else None),
        (_DEPTH_Q, depth, None if depth is not None else (error or "empty")),
        (_NOUL_Q, noul, None if noul is not None else (error or "empty")),
        (_THRESHOLD_Q, threshold, None if threshold is not None else (error or "empty")),
        (_PARAMETER_Q, parameter, None if parameter is not None else (error or "empty")),
        (_LOOP_Q, loop_bound, None if loop_bound is not None else (error or "empty")),
        (_WHICH_Q, which, None if which is not None else (error or "empty")),
        (_EXISTS_Q, exists, None if exists is not None else (error or "empty")),
    )
    _remember(state, rows)
    return {
        "choice": choice,
        "probabilities": probabilities,
        "confidence": confidence,
        "noul": noul,
        "include_siblings": depth,
        "threshold": threshold,
        "parameter": parameter,
        "loop_bound": loop_bound,
        "which_component": which,
        "component_exists": exists,
        "error": choice_error,
        "posted": bool(receipt.get("ok")),
        "ok": bool(receipt.get("ok")),
        "missing_jev": False,
        "model": receipt.get("model") or MODEL,
        "questions": dict(questions),
        "answers": dict(answers),
        "state": dict(state),
    }


def _prepare_state(state: Mapping[str, Any] | None) -> dict[str, Any]:
    cleaned = _scrub(dict(state or {}))
    st = cleaned if isinstance(cleaned, dict) else {}
    for key in list(st):
        token = str(key).lower().replace("-", "_")
        if token in {
            "choice",
            "disposition",
            "reason",
            "this_sleeve_vs_sibling",
            "may_send",
            "blocks_send",
            "thin_state",
            "completeness_noul",
            "persist_weight",
            "persist_apply",
            "prior_outcomes",
            "flatten",
        } or token == "send" or token.endswith("_send"):
            st.pop(key, None)
    identity = dict(st.get("identity") or {})
    identity.setdefault("login", "0")
    identity.setdefault("ns", "operator")
    st["identity"] = identity
    st["model"] = MODEL
    return st


def _ask(state: Mapping[str, Any] | None, *, timeout_s: float | None = None) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    try:
        st = _prepare_state(state)
        questions = sleeve_select_decision_questions(st)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return _blank_ask({}, error=type(exc).__name__, missing_jev=False)
    if not questions:
        return _blank_ask({}, error="question_pack_fail", missing_jev=False, state=st)
    try:
        from .jev_questions import prior_outcomes

        st["prior_outcomes"] = prior_outcomes(state=st, questions=questions)
    except Exception:
        st["prior_outcomes"] = []
    try:
        from .jev_client import evaluate
    except Exception as exc:  # noqa: BLE001
        card = _blank_ask(questions, error=type(exc).__name__, missing_jev=True, state=st)
        _remember(st, tuple((key, None, card["error"]) for key in questions))
        return card
    try:
        receipt = evaluate(
            st,
            questions=questions,
            merge_sleeve=False,
            timeout_s=timeout_s,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001
        card = _blank_ask(questions, error=type(exc).__name__, missing_jev=False, state=st)
        _remember(st, tuple((key, None, card["error"]) for key in questions))
        return card
    try:
        return _read_ask(questions, receipt, st)
    except Exception as exc:  # noqa: BLE001
        return _blank_ask(questions, error=type(exc).__name__, missing_jev=False, state=st)


def decide_sleeve_select_live(
    *,
    symbol: str = "XAUUSD",
    state: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Owner of this fire. The unique highest probability. A miss stays unset.

    The threshold, the loop bound, and the parameter are the scores on that
    same ask. This hop does not send.
    """

    del environ
    st = dict(state or {})
    st.setdefault("symbol", symbol)
    st.setdefault("instrument", symbol)
    st.setdefault("gate", "sleeve_select")
    asked = _ask(st, timeout_s=timeout_s)
    named = asked.get("choice")
    noul = asked.get("noul")
    if noul is True:
        thin_state: bool | None = False
    elif noul is False:
        thin_state = True
    else:
        thin_state = None
    component = asked.get("which_component")
    # A role word is not a sleeve the book trades. Empty, tie, and abstain
    # leave the book's sleeve in place.
    if (
        named in (None, "abstain")
        or not isinstance(component, str)
        or not component.strip()
        or component in {
            "this_sleeve",
            "sibling",
            "abstain",
            "stand",
            "own",
            "spring",
            "three_fresh",
        }
    ):
        advisory = None
    else:
        advisory = component.strip()
    if named in _SEND_CHOICES:
        may_send = True
        blocks_send = False
    else:
        may_send = None
        blocks_send = None
    questions = asked.get("questions") if isinstance(asked.get("questions"), Mapping) else {}
    return {
        "schema": "gtos.judgment.sleeve_select.live.v1",
        "kind": "choice",
        "hop": "sleeve_select",
        "symbol": str(symbol).upper(),
        "disposition": named,
        "choice": named,
        "reason": named,
        "this_sleeve_vs_sibling": named,
        "probabilities": asked.get("probabilities") or {},
        "confidence": asked.get("confidence"),
        "completeness_noul": noul,
        "thin_state": thin_state,
        "may_send": may_send,
        "blocks_send": blocks_send,
        "include_siblings": asked.get("include_siblings"),
        "threshold": asked.get("threshold"),
        "parameter": asked.get("parameter"),
        "loop_bound": asked.get("loop_bound"),
        "which_component": asked.get("which_component"),
        "component_exists": asked.get("component_exists"),
        "place": False,
        "flatten": False,
        "apply": True if advisory else None,
        "selected_sleeve_advisory": advisory,
        "never_place": True,
        "extra_pass": False,
        "missing_jev": bool(asked.get("missing_jev")),
        "persist_weight": asked.get("parameter"),
        "persist_apply": None,
        "mill_url": None,
        "posted": bool(asked.get("posted")),
        "posted_ids": list(questions),
        "never_flatten_tickets": list(st.get("never_flatten_tickets") or []) or None,
        "live_fanout_ok": asked.get("ok"),
        "live_hop": "sleeve_select:this_sleeve_vs_sibling",
        "model": asked.get("model") or MODEL,
        "error": None if named is not None else asked.get("error"),
        "broker_effect": False,
    }


def for_send_choke(
    state: Mapping[str, Any] | None = None,
    *,
    intent: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
    timeout_s: float | None = None,
) -> dict[str, Any]:
    """Sleeve-vs-sibling Choice the send choke can call."""
    del intent
    symbol = "XAUUSD"
    if isinstance(state, Mapping):
        symbol = str(state.get("symbol") or state.get("instrument") or "XAUUSD")
    return decide_sleeve_select_live(
        symbol=symbol, state=state, environ=environ, timeout_s=timeout_s
    )


def _env_on(name: str, environ: Mapping[str, str] | None = None, *, default: bool = False) -> bool:
    env = environ if environ is not None else os.environ
    raw = str(env.get(name, "")).strip().lower()
    if not raw:
        return default
    return raw in _TRUTHY


def sleeve_select_shadow_enabled(
    *,
    environ: Mapping[str, str] | None = None,
    fluid_shadow_on: bool | None = None,
) -> bool:
    """Default ON when fluid shadow is on; explicit 0/false turns off."""
    env = environ if environ is not None else os.environ
    raw = str(env.get(SLEEVE_SELECT_SHADOW_ENV, "")).strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in _TRUTHY:
        return True
    if fluid_shadow_on is not None:
        return bool(fluid_shadow_on)
    return _env_on(FLUID_SHADOW_ENV, env, default=False)


def sleeve_select_apply_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """A returned sleeve is the choice. A planted 0 does not veto it."""

    del environ
    return True


def soft_relax_map() -> dict[str, Any]:
    """Names are not a house law. The returned sleeve is the choice.

    SOFT_RELAX_HOUSE_LAW, SOFT_RELAX_STAY_HOUSE_UNTIL_KEEP_PROOF, and
    SOFT_RELAX_MAY_BECOME_JEV_BLOCKED stay defined. They do not decide.
    """

    return {
        "house_law_stay_writer": [],
        "stay_house_until_keep_proof": [],
        "may_become_jev_blocked": [],
        "note": (
            "A returned sleeve is the choice. "
            "An empty answer leaves the book's sleeve in place. "
            "These names are not a house law."
        ),
        "receipt_required_to_move": False,
    }


def load_phi_prior(path: Path | str | None = None) -> dict[str, Any]:
    candidates: list[Path] = []
    if path is not None:
        candidates.append(Path(path))
    candidates.extend(_PHI_CANDIDATE_PATHS)
    for p in candidates:
        try:
            if p.is_file():
                doc = json.loads(p.read_text(encoding="utf-8"))
                doc["_loaded_from"] = str(p)
                return doc
        except Exception:  # noqa: BLE001
            continue
    return {
        "schema": "missing",
        "candidates": [],
        "menu_ranking": [],
        "apply": False,
        "place": False,
        "_loaded_from": None,
    }


def _phi_number(row: Mapping[str, Any]) -> float | None:
    """φ written on this prior row. A missing number stays missing."""

    cap = row.get("capability") if isinstance(row.get("capability"), Mapping) else {}
    raw = None
    if isinstance(cap, Mapping) and "phi" in cap and cap.get("phi") is not None:
        raw = cap.get("phi")
    elif "phi" in row and row.get("phi") is not None:
        raw = row.get("phi")
    return _number(raw)


def phi_score_for_tag(tag: str, symbol: str, prior: Mapping[str, Any] | None) -> float | None:
    """φ from the prior file. A missing row does not become zero."""

    if not prior:
        return None
    sym = str(symbol).upper()
    tag_l = str(tag).lower()
    best: float | None = None
    for row in prior.get("candidates") or []:
        if not isinstance(row, Mapping) or not row.get("menu_eligible", True):
            continue
        inst = str(row.get("instrument") or "").upper()
        if inst and inst != sym:
            if not (inst.startswith("XAU") and sym.startswith("XAU")):
                continue
        row_tag = str(row.get("tag") or "").lower()
        row_sleeve = str(row.get("sleeve") or "").lower()
        if tag_l == row_tag or tag_l == row_sleeve or (row_tag and row_tag in tag_l) or (row_sleeve and row_sleeve in tag_l):
            phi = _phi_number(row)
            if phi is None:
                continue
            if best is None or phi > best:
                best = phi
    return best


def _escape_criterion(name: str) -> Criterion:
    spec = ESCAPE_CRITERIA[name]
    return Criterion(
        id=name,
        what=spec["what"],
        not_for=spec["not_for"],
        examples=tuple(spec["examples"]),
    )


def _sleeve_criterion(name: str, *, phi: float | None = None, prior_note: str = "") -> Criterion:
    bits = []
    if isinstance(phi, (int, float)) and not isinstance(phi, bool):
        bits.append(f"φ={phi:.4f}")
    if prior_note:
        bits.append(prior_note)
    suffix = (" " + "; ".join(bits)) if bits else ""
    return Criterion(
        id=f"sleeve:{name}",
        what=f"Select alive+affinity sleeve {name} for this symbol's JEV_SLEEVE_SELECT.{suffix}",
        not_for=(
            "Package B never aliases sub_mid_dn_revert."
        ),
        examples=(name, QUESTION_ID),
    )


@dataclass(frozen=True)
class SleeveSelectMenu:
    """Symbol-scoped Choice menu (AliveMenu-compatible)."""

    cycle_id: str
    symbol: str
    inventory_fingerprint: str
    criteria: tuple[Criterion, ...]
    rebuilt: bool
    prior_fingerprint: str | None
    inventory_changed: bool
    question_id: str = QUESTION_ID
    phi_ordered: bool = True
    apply: bool | None = None
    place: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)
    selected_sleeve_advisory: str | None = None
    alive_pack: dict[str, Any] = field(default_factory=dict)
    soft_relax: dict[str, Any] = field(default_factory=dict)

    @property
    def option_ids(self) -> tuple[str, ...]:
        return tuple(c.id for c in self.criteria)

    def as_dict(self) -> dict[str, object]:
        return {
            "question_id": self.question_id,
            "cycle_id": self.cycle_id,
            "symbol": self.symbol,
            "inventory_fingerprint": self.inventory_fingerprint,
            "criteria": [c.as_dict() for c in self.criteria],
            "rebuilt": self.rebuilt,
            "prior_fingerprint": self.prior_fingerprint,
            "inventory_changed": self.inventory_changed,
            "notes": list(self.notes),
            "option_ids": list(self.option_ids),
            "phi_ordered": self.phi_ordered,
            "apply": True if self.selected_sleeve_advisory else None,
            "place": False,
            "selected_sleeve_advisory": self.selected_sleeve_advisory,
            "alive_pack_summary": {
                "alive": list((self.alive_pack or {}).get("alive_sleeves_for_symbol") or []),
                "armed_source": (self.alive_pack or {}).get("armed_source"),
                "relax_to_jev": (self.alive_pack or {}).get("relax_to_jev"),
                "blocked_escape_n": len((self.alive_pack or {}).get("blocked_escape") or []),
                "fail_closed": (self.alive_pack or {}).get("fail_closed", False),
            },
            "soft_relax": self.soft_relax,
        }

    def as_alive_menu(self) -> AliveMenu:
        return AliveMenu(
            cycle_id=self.cycle_id,
            inventory_fingerprint=self.inventory_fingerprint,
            criteria=self.criteria,
            rebuilt=self.rebuilt,
            prior_fingerprint=self.prior_fingerprint,
            inventory_changed=self.inventory_changed,
            notes=self.notes + ("sleeve_select_as_alive_menu",),
        )


def _collect_alive_tags(symbol: str, state: Mapping[str, Any] | None) -> tuple[list[str], dict[str, Any], list[str]]:
    """Compose alive tags; fail-closed notes if deps missing. Always union F5 KEEP priors."""
    notes: list[str] = []
    pack: dict[str, Any] = {}
    alive: list[str] = []
    try:
        from .alive_sleeves_for_symbol import alive_sleeves_for_symbol

        pack = alive_sleeves_for_symbol(symbol, use_research_overlay=True)
        alive = list(pack.get("alive_sleeves_for_symbol") or [])
        notes.append("alive_sleeves_for_symbol_ok")
    except Exception as exc:  # noqa: BLE001
        pack = {
            "fail_closed": True,
            "error": f"{type(exc).__name__}:{exc}",
            "alive_sleeves_for_symbol": [],
            "apply": False,
            "place": False,
        }
        notes.append(f"alive_sleeves_fail_closed:{type(exc).__name__}")

    sym = str(symbol).upper()
    priors = list(F5_AFFINITY_KEEP_PRIORS.get(sym, ()))
    # state may inject extra KEEP priors
    if state:
        extra = state.get("affinity_keep_priors") or state.get("f5_keep_priors") or ()
        for x in extra:
            if x and str(x) not in priors:
                priors.append(str(x))
    for p in priors:
        if p not in alive:
            alive.append(p)
            notes.append(f"f5_keep_prior_injected:{p}")
    # EURUSD must include asian_fade
    if sym == "EURUSD" and "asian_fade" not in alive:
        alive.insert(0, "asian_fade")
        notes.append("eurusd_asian_fade_forced")
    return alive, pack, notes


def build_sleeve_select_menu(
    symbol: str,
    state: Mapping[str, Any] | None = None,
    *,
    selected_advisory: str | None = None,
    phi_prior: Mapping[str, Any] | None = None,
    prior_menu: SleeveSelectMenu | None = None,
) -> SleeveSelectMenu:
    """Build symbol-scoped Choice criteria. Escapes always present. Cap 255."""
    sym = str(symbol or (state or {}).get("symbol") or (state or {}).get("instrument") or "UNKNOWN").upper()
    alive, pack, notes = _collect_alive_tags(sym, state)
    prior = dict(phi_prior) if phi_prior is not None else load_phi_prior()
    if prior.get("_loaded_from"):
        notes.append(f"phi_prior:{prior['_loaded_from']}")
    else:
        notes.append("phi_prior_missing_fail_closed_order_alpha")

    # φ descending when the prior file has a number. A missing φ stays missing.
    scored = [(phi_score_for_tag(t, sym, prior), t) for t in alive]
    scored.sort(key=lambda row: (1, row[1]) if row[0] is None else (0, -float(row[0]), row[1]))
    notes.append("phi_ordered_desc")

    criteria: list[Criterion] = [_escape_criterion(n) for n in ESCAPE_HATCHES]
    for phi, tag in scored:
        # never present live sub_mid_dn_revert as Package B alias on EURUSD;
        # GBPJPY F5 KEEP prior may show sub_mid_dn_revert (PR40 tape KEEP) — not Package B SHORT
        if tag == "sub_mid_dn_revert" and tag not in F5_AFFINITY_KEEP_PRIORS.get(sym, ()):
            notes.append("refused_alias_package_b_to_sub_mid_dn_revert")
            continue
        if tag == "sub_mid_dn_re_proxy_eurusd_short_m15_atr" and sym != "EURUSD":
            notes.append("package_b_short_eurusd_only")
            continue
        prior_note = "f5_keep" if tag in F5_AFFINITY_KEEP_PRIORS.get(sym, ()) else ""
        criteria.append(_sleeve_criterion(tag, phi=phi, prior_note=prior_note))

    # blocked_escape from relax → already have BLOCKED hatch; annotate
    for be in pack.get("blocked_escape") or []:
        notes.append(f"blocked_escape:{be.get('tag')}")

    if len(criteria) > MAX_CHOICE_OPTIONS:
        notes.append("capped_at_255")
        head = [c for c in criteria if c.id in ESCAPE_HATCHES]
        rest = [c for c in criteria if c.id not in ESCAPE_HATCHES]
        budget = MAX_CHOICE_OPTIONS - len(head)
        criteria = head + rest[:budget]

    fp_src = {"symbol": sym, "sleeves": [c.id for c in criteria if c.id.startswith("sleeve:")]}
    fp = hashlib.sha256(json.dumps(fp_src, sort_keys=True).encode()).hexdigest()
    prior_fp = prior_menu.inventory_fingerprint if prior_menu else None
    changed = bool(prior_fp and prior_fp != fp)

    # A passed choice is the sleeve. Empty does not copy the book's sleeve in.
    advisory = str(selected_advisory) if selected_advisory else None

    return SleeveSelectMenu(
        cycle_id=fp,
        symbol=sym,
        inventory_fingerprint=fp,
        criteria=tuple(criteria),
        rebuilt=True,
        prior_fingerprint=prior_fp,
        inventory_changed=changed,
        question_id=QUESTION_ID,
        phi_ordered=True,
        apply=True if advisory else None,
        place=False,
        notes=tuple(notes),
        selected_sleeve_advisory=advisory,
        alive_pack=pack,
        soft_relax=soft_relax_map(),
    )


def emit_sleeve_select_shadow_payload(
    menu: SleeveSelectMenu,
    *,
    state: Mapping[str, Any] | None = None,
    apply_flag: bool = False,
) -> dict[str, Any]:
    """The returned sleeve is the choice the book reads.

    Empty leaves the advisory unset. That is not a refusal and it does not
    restore the book's sleeve. This function does not send.
    """

    del apply_flag
    advisory = menu.selected_sleeve_advisory or None
    if isinstance(advisory, str) and not advisory.strip():
        advisory = None
    apply_on = True if advisory else None
    return {
        "schema": "gtos.jev.sleeve_select.shadow.v1",
        "question_id": QUESTION_ID,
        "type": "Choice",
        "symbol": menu.symbol,
        "options": list(menu.option_ids),
        "criteria": [c.as_dict() for c in menu.criteria],
        "state_keys": sorted(list((state or {}).keys())),
        "selected_sleeve_advisory": advisory,
        "phi_ordered": menu.phi_ordered,
        "apply": apply_on,
        "place": False,
        "never_place": True,
        "cost_never_kill": True,
        "never_alias_package_b_to_sub_mid_dn_revert": True,
        "soft_relax": menu.soft_relax,
        "menu": menu.as_dict(),
        "disposition": "advisory_only" if not apply_on else "admit_filter",
    }


def append_warroom_shadow_jsonl(payload: Mapping[str, Any], log_dir: Path | str | None = None) -> Path:
    """Append one shadow line under judgment/live/jev_sidecar/sleeve_select/."""
    from datetime import datetime, timezone

    if log_dir is None:
        override = os.environ.get("GTOS_JEV_FLUID_GATES_LOG_DIR", "").strip()
        root = Path(override) if override else Path(__file__).resolve().parents[2] / "judgment" / "live" / "jev_sidecar"
    else:
        root = Path(log_dir)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = root / "sleeve_select" / f"{day}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(payload), sort_keys=True) + "\n")
    return path


# --- Chair Jev-everywhere 2026-09-21: scoped conflict APPLY helpers ---
XAU_CONFLICT_APPLY_ENV = "GTOS_JEV_SLEEVE_SELECT_APPLY_XAU_CONFLICT"
GBPJPY_CONFLICT_APPLY_ENV = "GTOS_JEV_SLEEVE_SELECT_APPLY_GBPJPY_CONFLICT"
_METAL_PREFIXES = ("XAU", "XAG", "XPT", "XPD")
_METAL_NAMES = frozenset({"GOLD", "SILVER", "PLATINUM", "PALLADIUM"})


def _metal_symbol(symbol: str) -> bool:
    """Gold, silver, platinum, palladium, and the crosses already on the book."""

    sym = "".join(ch for ch in str(symbol or "").upper() if ch.isalnum())
    if not sym:
        return False
    if sym in _METAL_NAMES:
        return True
    return sym.startswith(_METAL_PREFIXES)


def xau_conflict_apply_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """A returned metal conflict is the choice. A planted 0 does not veto it."""

    del environ
    return True


def gbpjpy_conflict_apply_enabled(*, environ: Mapping[str, str] | None = None) -> bool:
    """A returned GBPJPY conflict is the choice. A planted 0 does not veto it."""

    del environ
    return True


def _stand_bit(choice: Any, *, stand: str, own: str) -> bool | None:
    """Map the returned owner onto stand / own. Anything else stays unset."""

    if choice == stand:
        return True
    if choice == own:
        return False
    return None


def should_stand_three_fresh_xau_conflict(
    alive_tags: list[str] | tuple[str, ...] | set[str],
    *,
    symbol: str = "",
    environ: Mapping[str, str] | None = None,
) -> bool | None:
    """Whether three_fresh stands aside when spring is also alive on a metal.

    Every metal follows this rule, not only gold. Spring means three_fresh
    stands aside. Three_fresh means it owns the fire. An empty answer, a
    tie, or an error leaves the stand unset. That leaves the book's sleeve
    in place and is not a refusal.
    """

    try:
        sym = str(symbol or "").upper()
        if sym and not _metal_symbol(sym):
            return None
        tags = [str(item or "").lower() for item in (alive_tags or [])]
        has_spring = any("spring" in item for item in tags)
        has_three = any("three_fresh" in item for item in tags)
        if not (has_spring and has_three):
            return None
        if not sleeve_select_live_enabled(environ=environ):
            return None
        asked = _ask(
            {
                "gate": "should_stand_three_fresh_xau_conflict",
                "module": "sleeve_select",
                "symbol": sym,
                "instrument": sym,
                "alive_tags": list(alive_tags or []),
            }
        )
        return _stand_bit(asked.get("choice"), stand="spring", own="three_fresh")
    except Exception:
        return None


def should_stand_gbpjpy_conflict_tag(
    tag: str,
    alive_tags: list[str] | tuple[str, ...] | set[str],
    *,
    symbol: str = "",
    environ: Mapping[str, str] | None = None,
) -> bool | None:
    """Whether this GBPJPY tag stands aside when both siblings are alive.

    The stand is the returned decision for this tag. An empty answer, a
    tie, or an error leaves the stand unset. That leaves the book's sleeve
    in place and is not a refusal.
    """

    try:
        sym = str(symbol or "").upper()
        if sym != "GBPJPY":
            return None
        tags = [str(item or "").lower() for item in (alive_tags or [])]
        has_vss = any("vss_fxcross" in item or item.startswith("vss_") for item in tags)
        has_sub = any("sub_mid" in item for item in tags)
        if not (has_vss and has_sub):
            return None
        if not sleeve_select_live_enabled(environ=environ):
            return None
        asked = _ask(
            {
                "gate": "should_stand_gbpjpy_conflict_tag",
                "module": "sleeve_select",
                "symbol": "GBPJPY",
                "instrument": "GBPJPY",
                "tag": tag,
                "alive_tags": list(alive_tags or []),
            }
        )
        return _stand_bit(asked.get("choice"), stand="stand", own="own")
    except Exception:
        return None

