#!/usr/bin/env python3
"""JEV_SLEEVE_SELECT compose — alive_sleeves_for_symbol(symbol).

Every decision, including each parameter, is the System One return for
this state. The call is jev_client.evaluate with model jev-1.13.0
(POST https://api.typesafe.ai/v1/systemone, merge_sleeve=False).
Questions are only a Noul, a Choice, or a Score. Prior outcomes are on
the ask and the return is stored for the next ask. A Choice is the
unique highest probability. A Score is the returned number and may sit
between levels. A Noul is a bool or a probability. An empty answer, a
tie, or an error leaves that return unset. A floor and a baseline are
not a question. This module does not send.

Measured tags, armed files, and ON_SURFACE rows stay facts. Membership
in the alive list is the disposition Choice for that tag.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ICT = timezone(timedelta(hours=7))
_HERE = Path(__file__).resolve().parent
_GTOS = Path("/workspace/gtos")
_SWARM_SRC = _GTOS / "_swarm_land_tip/extract/src"
_WARROOM_SRC = _GTOS / "judgment/warroom_shadow"
_CL = _GTOS / "close_loop/war_room_20260920"
_DIG_WAR = _GTOS / "research/codila_absorb/war_room"
_ARMED_JSON = _GTOS / "_swarm_land_tip/extract/config/live_armed_set.json"
_OVERLAY = _CL / "RESEARCH_ARMED_TAGS_OVERLAY_20260920.json"

MODEL = "jev-1.13.0"
_NS = "operator"
_LOGIN = 0

# Question menus. The return is the decision. A miss does not fill these in.
_SOURCE_ORDER = ("research_armed", "live_armed")
_DISPOSITION_ORDER = ("alive", "blocked", "drop")
_COMPONENT_ORDER = (
    "build_slots",
    "on_surface",
    "live_armed",
    "research_overlay",
    "hard_off",
    "affinity_prior",
)
_HARD_OFF_MENU = (
    "bleed",
    "orb_crypto",
    "idxrev",
    "xa_huge",
    "mx_us30",
)
_PRIOR_MENU: Dict[str, Tuple[str, ...]] = {
    "EURUSD": ("asian_fade", "sub_mid_dn_re_proxy_eurusd_short_m15_atr"),
    "XAUUSD": (
        "dsp_spring_close_on_20low_through_the_box",
        "dsp_three_fresh_lower_lows",
        "dsp_expanding_up_staircase",
    ),
    "GBPJPY": ("vss_fxcross_london_up_low", "sub_mid_dn_revert"),
    "XAGUSD": ("sub_xvol_pullback", "metals_core", "metal_session_reversion"),
}
_BETWEEN = (
    "below the levels on this state",
    "between the levels on this state",
    "above the levels on this state",
)
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
_Q_SOURCE = "alive_armed_source"
_Q_RELAX = "alive_relax"
_Q_CANDIDATE = "alive_candidate_built"
_Q_SAME = "alive_same_tag"
_Q_SUFFICIENT = "alive_state_sufficient"
_Q_THRESHOLD = "alive_threshold"
_Q_LOOP = "alive_loop_bound"
_Q_PARAMETER = "alive_parameter"
_Q_COMPONENT = "alive_component"
_Q_EXISTS = "alive_component_exists"

if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_CL) not in sys.path:
    sys.path.insert(0, str(_CL))

try:
    from sleeve_on_surface_loader import load_sleeve_module  # type: ignore
except Exception:  # noqa: BLE001
    load_sleeve_module = None  # type: ignore



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


def _ict_now() -> str:
    return datetime.now(ICT).strftime("%Y-%m-%dT%H:%M:%S+07:00")


def relax_to_jev_enabled(flag: Optional[bool] = None) -> Optional[bool]:
    """Caller flag or env, as a fact. Absence stays unset."""

    if flag is True or flag is False:
        return flag
    env = os.environ.get("GTOS_RELAX_TO_JEV", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True
    if env in ("0", "false", "no", "off"):
        return False
    return None


def load_live_armed_tags(account: Optional[str] = None) -> Tuple[List[str], Dict[str, Any]]:
    meta: Dict[str, Any] = {"path": str(_ARMED_JSON), "mutated": False, "source": None}
    if not _ARMED_JSON.exists():
        vps_guess = Path("C:host-local/redacted_host/repo/config/live_armed_set.json")
        if vps_guess.exists():
            meta["path"] = str(vps_guess)
            body = json.loads(vps_guess.read_text(encoding="utf-8"))
        else:
            meta["source"] = "unavailable"
            return [], meta
    else:
        body = json.loads(_ARMED_JSON.read_text(encoding="utf-8"))
    accounts = body.get("accounts") or {}
    out: set = set()
    if account and account in accounts:
        out |= set(accounts[account].get("armed_sleeves") or [])
        meta["account"] = account
    else:
        for row in accounts.values():
            out |= set(row.get("armed_sleeves") or [])
        meta["account"] = "union"
    meta["source"] = "live_armed_set.json"
    return sorted(out), meta


def _load_json_loose(path: Path) -> Dict[str, Any]:
    txt = path.read_text(encoding="utf-8")
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        start = txt.find("{")
        depth = 0
        for i, ch in enumerate(txt[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(txt[start : i + 1])
        raise


def load_research_armed_tags() -> Tuple[List[str], Dict[str, Any]]:
    """Base overlay + ADD_* fragments. A named tag is not inserted from a flag."""

    effective = _CL / "RESEARCH_ARMED_TAGS_OVERLAY_EFFECTIVE_20260920.json"
    meta: Dict[str, Any] = {"path": str(_OVERLAY), "fragments": [], "source": None}
    tags: set = set()
    if effective.exists():
        body = _load_json_loose(effective)
        tags |= {str(t) for t in (body.get("research_armed_tags") or [])}
        meta["source"] = "RESEARCH_ARMED_TAGS_OVERLAY_EFFECTIVE_20260920.json"
        meta["fragments"] = body.get("fragments_merged") or []
    else:
        if _OVERLAY.exists():
            body = _load_json_loose(_OVERLAY)
            tags |= {str(t) for t in (body.get("research_armed_tags") or [])}
            meta["source"] = "RESEARCH_ARMED_TAGS_OVERLAY_20260920.json"
        for frag in sorted(_CL.glob("RESEARCH_ARMED_TAGS_OVERLAY_ADD_*.json")):
            try:
                d = _load_json_loose(frag)
            except Exception as exc:  # noqa: BLE001
                meta["fragments"].append({"file": frag.name, "error": f"{type(exc).__name__}:{exc}"})
                continue
            add = d.get("research_armed_tags_add") or d.get("research_armed_tags") or []
            tags |= {str(t) for t in add}
            meta["fragments"].append({"file": frag.name, "added": list(add)})
    env_cand = os.environ.get("GTOS_INCLUDE_CANDIDATE_BUILT", "").strip().lower()
    meta["candidate_built_env"] = env_cand
    if env_cand in ("1", "true", "yes", "on"):
        cand_path = _GTOS / "_swarm_land_tip/extract/src/components/ultimate_book/sleeves/registry.py"
        meta["candidate_built_scan"] = str(cand_path)
        meta["candidate_built_named"] = "asian_fade"
    add_af = _CL / "RESEARCH_ARMED_TAGS_OVERLAY_ADD_asian_fade_20260920.json"
    meta["same_tag_fragment_exists"] = add_af.exists()
    if add_af.exists():
        meta["same_tag_named"] = "asian_fade"
    if not tags and meta["source"] is None:
        meta["source"] = "unavailable"
    return sorted(tags), meta


def hard_off_families() -> Tuple[Optional[set], Dict[str, Any]]:
    """Loaded family names are a fact. A failed load stays unset."""

    meta: Dict[str, Any] = {}
    try:
        if str(_WARROOM_SRC) not in sys.path:
            sys.path.insert(0, str(_WARROOM_SRC))
        from src.judgment.challenge import CHALLENGE_HARD_OFF_FAMILIES  # type: ignore

        fam = {str(name) for name in CHALLENGE_HARD_OFF_FAMILIES if name}
        meta["source"] = "challenge.CHALLENGE_HARD_OFF_FAMILIES"
        meta["hard_off"] = sorted(fam)
        return fam, meta
    except Exception as exc:  # noqa: BLE001
        meta["source"] = "unset"
        meta["error"] = f"{type(exc).__name__}:{exc}"
        meta["hard_off"] = None
        return None, meta


class _Spec:
    def __init__(self, tag: str, on_surface: tuple):
        self.tag = tag
        self.on_surface = on_surface


def _import_build_slots():
    if str(_SWARM_SRC) not in sys.path:
        sys.path.insert(0, str(_SWARM_SRC))
    from components.ultimate_book.symbol_resolution_watch import build_slots  # type: ignore

    return build_slots


def _load_on_surface_from_recovered(tag: str) -> Optional[Tuple[str, tuple]]:
    if load_sleeve_module is None:
        return None
    loaded = load_sleeve_module(tag)
    if loaded.get("status") == "LOADED_FROM_RECOVERY" and loaded.get("ON_SURFACE"):
        return str(loaded.get("TAG") or tag), tuple(loaded["ON_SURFACE"])
    return None


def load_on_surface_specs(tags: Sequence[str]) -> Tuple[List[_Spec], Dict[str, Any]]:
    notes: Dict[str, Any] = {"loaded": {}, "missing": []}
    specs: List[_Spec] = []
    seen = set()
    for tag in tags:
        got = _load_on_surface_from_recovered(tag)
        if got:
            full, surface = got
            if full not in seen:
                specs.append(_Spec(full, surface))
                seen.add(full)
            if tag != full and tag not in seen:
                specs.append(_Spec(tag, surface))
                seen.add(tag)
            notes["loaded"][full] = {"ON_SURFACE": list(surface), "alias_requested": tag}
        else:
            notes["missing"].append({"tag": tag, "note": "refuse invent ON_SURFACE"})
    return specs, notes


def _is_hard_off(tag: str, families: set) -> Optional[str]:
    t = tag.lower()
    for h in families:
        if h.lower() in t:
            return h
    return None


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
    for token in _BANNED_TEXT:
        cleaned = cleaned.replace(token, "")
    out: List[str] = []
    index = 0
    lowered = cleaned.lower()
    while index < len(cleaned):
        if lowered.startswith("baseline", index):
            index += len("baseline")
            continue
        if lowered.startswith("floor", index):
            index += len("floor")
            continue
        out.append(cleaned[index])
        index += 1
    return "".join(out)


def _scrub(value: Any) -> Any:
    """Drop floor and baseline keys before an ask."""

    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


def _finite(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _probs(block: Any) -> Dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: Dict[str, float], order: Tuple[str, ...]) -> Optional[str]:
    """Unique highest probability. A missing probability is not zero. A tie is not a decision."""

    if not probs:
        return None
    names = order if order else tuple(probs)
    best: Optional[str] = None
    best_p: Optional[float] = None
    tied = False
    seen = False
    for name in names:
        if name not in probs:
            continue
        seen = True
        p = probs[name]
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def _choice(block: Any, order: Tuple[str, ...]) -> Optional[str]:
    if not isinstance(block, dict) or block.get("error"):
        return None
    probs = _probs(block)
    if not probs:
        return None
    picked: Optional[str] = None
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probs, order)
        if agreed is not None:
            picked = str(agreed)
    except Exception:
        picked = _unique(probs, order)
    if picked not in order:
        return None
    return picked


def _noul(block: Any) -> Any:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _choice(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score(block: Any) -> Optional[float]:
    """The score that came back. It is not snapped to a level."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        pass
    if "score" in block and block.get("score") is not None:
        return _finite(block.get("score"))
    return None


def _why(block: Any, value: Any, order: Tuple[str, ...], receipt_error: Any) -> Optional[str]:
    if value is not None:
        return None
    if isinstance(block, dict) and block.get("error"):
        return str(block.get("error"))
    probs = _probs(block) if isinstance(block, dict) else {}
    menu = order or tuple(probs)
    if probs and _unique(probs, menu) is None:
        return "tie"
    if receipt_error not in (None, ""):
        return str(receipt_error)
    return "empty"


def _choice_question(qid: str, instructions: str, criteria: Dict[str, str]) -> Dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {key: _scrub_text(val) for key, val in criteria.items() if not _limit_key(key)}
    body: Dict[str, Any] = {"type": "choice", "instructions": text, "criteria": cleaned}
    try:
        from .jev_questions import spot_question

        built = spot_question(qid, text, cleaned)
        block = built.get(qid) if isinstance(built, dict) else None
        if isinstance(block, dict):
            shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
            shaped["type"] = "choice"
            shaped["instructions"] = text
            shaped["criteria"] = cleaned
            return {qid: shaped}
    except Exception:
        pass
    return {qid: body}


def _noul_question(qid: str, instructions: str, yes: str, no: str) -> Dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(instructions),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }



def _score_question(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _kept_questions(questions: Dict[str, Any]) -> Dict[str, Any]:
    kept: Dict[str, Any] = {}
    for qid, block in questions.items():
        if _limit_key(qid) or not isinstance(block, dict):
            continue
        kind = str(block.get("type") or "").strip().lower()
        if kind not in ("noul", "choice", "score"):
            continue
        kept[str(qid)] = block
    return kept


def _tag_qid(tag: str, used: Dict[str, str]) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(tag).lower())
    safe = safe.strip("_") or "tag"
    qid = f"alive_tag_{safe}"
    if qid in used and used[qid] != tag:
        n = 2
        while f"{qid}_{n}" in used:
            n += 1
        qid = f"{qid}_{n}"
    used[qid] = tag
    return qid


def _tag_qids(tags: Sequence[str]) -> Dict[str, str]:
    """Map question id → tag."""

    used: Dict[str, str] = {}
    for tag in tags:
        _tag_qid(tag, used)
    return used


def _dedupe(tags: Sequence[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for tag in tags:
        text = str(tag).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _prior_catalog() -> Tuple[Dict[str, Tuple[str, ...]], str]:
    try:
        from .sleeve_select import F5_AFFINITY_KEEP_PRIORS as loaded  # type: ignore

        if isinstance(loaded, dict):
            return loaded, "sleeve_select"
    except Exception:
        pass
    try:
        from sleeve_select import F5_AFFINITY_KEEP_PRIORS as loaded  # type: ignore

        if isinstance(loaded, dict):
            return loaded, "sleeve_select"
    except Exception:
        pass
    return _PRIOR_MENU, "named_menu"


def _priors_for(symbol: str) -> Tuple[List[str], str]:
    catalog, source = _prior_catalog()
    row = catalog.get(symbol) or ()
    return [str(tag) for tag in row if tag], source


def _named_candidates(meta: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for key in ("candidate_built_named", "same_tag_named"):
        name = meta.get(key)
        if name:
            out.append(str(name))
    return out


def _family_names(loaded: Optional[set]) -> List[str]:
    names = list(_HARD_OFF_MENU)
    seen = set(names)
    for name in sorted(loaded or ()):
        text = str(name)
        if text and text not in seen:
            seen.add(text)
            names.append(text)
    return names


def _raw_tags(symbol: str, armed: Sequence[str]) -> Tuple[List[str], Dict[str, Any]]:
    specs, spec_notes = load_on_surface_specs(armed)
    meta: Dict[str, Any] = {"specs": spec_notes, "n_slots": 0, "n_raw": 0, "error": None}
    try:
        build_slots = _import_build_slots()
        slots = build_slots(specs, lambda c: str(c), armed_tags=list(armed))
    except Exception as exc:  # noqa: BLE001
        meta["error"] = f"{type(exc).__name__}:{exc}"
        return [], meta
    meta["n_slots"] = len(slots)
    by_sym: Dict[str, List[str]] = defaultdict(list)
    for sl in slots:
        if not getattr(sl, "armed", False):
            continue
        sleeve = getattr(sl, "sleeve", None) or getattr(sl, "tag", None)
        if sleeve is None:
            continue
        keys = {getattr(sl, "canonical", None)}
        broker = getattr(sl, "broker", None)
        if broker:
            keys.add(broker)
        for key in keys:
            if key:
                by_sym[str(key).upper()].append(str(sleeve))
    raw = sorted(set(by_sym.get(symbol, [])))
    meta["n_raw"] = len(raw)
    return raw, meta


def _questions(qid_for_tag: Dict[str, str], families: Sequence[str]) -> Dict[str, Any]:
    """One pack. Types are noul, choice, or score."""

    pack: Dict[str, Any] = {}
    pack.update(
        _choice_question(
            _Q_SOURCE,
            "Which armed inventory is this symbol on? "
            "The option with the single highest probability is the source. "
            "An empty answer or a tie leaves the source unset. "
            "Do not send an order.",
            {
                "research_armed": "The research armed tags are this symbol's inventory.",
                "live_armed": "The live armed tags are this symbol's inventory.",
            },
        )
    )
    pack.update(
        _noul_question(
            _Q_RELAX,
            "Is hard-off on this symbol a blocked escape? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "Do not send an order.",
            "Hard-off on this symbol is a blocked escape.",
            "Hard-off on this symbol is not a blocked escape.",
        )
    )
    pack.update(
        _noul_question(
            _Q_CANDIDATE,
            "Is the candidate-built name in this symbol's inventory? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "Do not send an order.",
            "The candidate-built name is in this inventory.",
            "The candidate-built name is not in this inventory.",
        )
    )
    pack.update(
        _noul_question(
            _Q_SAME,
            "Is the same-tag fragment name in this symbol's inventory? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "Do not send an order.",
            "The same-tag fragment name is in this inventory.",
            "The same-tag fragment name is not in this inventory.",
        )
    )
    pack.update(
        _noul_question(
            _Q_SUFFICIENT,
            "Is this alive-sleeve state sufficient to decide? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "Do not send an order.",
            "This state is sufficient.",
            "This state is not sufficient.",
        )
    )
    pack.update(
        _score_question(
            _Q_THRESHOLD,
            "The score you return is the threshold for this alive inventory. "
            "It may sit between the levels. "
            "An empty score leaves the threshold unset. "
            "Do not send an order.",
        )
    )
    pack.update(
        _score_question(
            _Q_LOOP,
            "The score you return is the loop bound for this alive inventory. "
            "It may sit between the levels. "
            "An empty score leaves the bound unset. "
            "The bound does not drop a tag whose disposition was returned. "
            "Do not send an order.",
        )
    )
    pack.update(
        _score_question(
            _Q_PARAMETER,
            "The score you return is the parameter for this alive inventory. "
            "It may sit between the levels. "
            "An empty score leaves the parameter unset. "
            "Do not send an order.",
        )
    )
    pack.update(
        _choice_question(
            _Q_COMPONENT,
            "Which component is this alive inventory? "
            "The option with the single highest probability is the component. "
            "An empty answer or a tie leaves the component unset. "
            "Do not send an order.",
            {
                "build_slots": "The component is build slots.",
                "on_surface": "The component is on-surface.",
                "live_armed": "The component is live armed.",
                "research_overlay": "The component is the research overlay.",
                "hard_off": "The component is hard-off.",
                "affinity_prior": "The component is an affinity prior.",
            },
        )
    )
    pack.update(
        _noul_question(
            _Q_EXISTS,
            "Does that component exist for this state? "
            "The noul you return is that answer. "
            "An empty noul leaves it unset. "
            "Do not send an order.",
            "That component exists for this state.",
            "That component does not exist for this state.",
        )
    )
    for name in families:
        qid = f"alive_hard_off_{name}"
        pack.update(
            _noul_question(
                qid,
                f"Is {name} a hard-off family on this state? "
                "The noul you return is that answer. "
                "An empty noul leaves it unset. "
                "Do not send an order.",
                f"{name} is a hard-off family on this state.",
                f"{name} is not a hard-off family on this state.",
            )
        )
    for qid, tag in qid_for_tag.items():
        pack.update(
            _choice_question(
                qid,
                f"What is the disposition of {tag} for this symbol? "
                "The option with the single highest probability is the disposition. "
                "An empty answer or a tie leaves it unset. "
                "Do not send an order.",
                {
                    "alive": f"{tag} is alive for this symbol.",
                    "blocked": f"{tag} is a blocked escape for this symbol.",
                    "drop": f"{tag} is off this symbol's alive inventory.",
                },
            )
        )
    return _kept_questions(pack)


def _hits(tags: Sequence[str], families: Optional[set]) -> Dict[str, Optional[str]]:
    if not families:
        return {tag: None for tag in tags}
    return {tag: _is_hard_off(tag, families) for tag in tags}


def _state(
    symbol: str,
    account: Optional[str],
    overlay_fact: Optional[bool],
    relax_fact: Optional[bool],
    live_tags: Sequence[str],
    research_tags: Sequence[str],
    raw_research: Sequence[str],
    raw_live: Sequence[str],
    priors: Sequence[str],
    prior_source: str,
    named: Sequence[str],
    families: Optional[set],
    hits: Dict[str, Optional[str]],
    candidates: Sequence[str],
    research_meta: Dict[str, Any],
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "model": MODEL,
        "namespace": _NS,
        "login": _LOGIN,
        "symbol": symbol,
        "account": account,
        "use_research_overlay": overlay_fact,
        "relax_to_jev_fact": relax_fact,
        "relax_env": os.environ.get("GTOS_RELAX_TO_JEV", "").strip().lower(),
        "candidate_built_env": research_meta.get("candidate_built_env"),
        "same_tag_fragment_exists": bool(research_meta.get("same_tag_fragment_exists")),
        "live_armed_tags": list(live_tags),
        "research_armed_tags": list(research_tags),
        "raw_research": list(raw_research),
        "raw_live": list(raw_live),
        "affinity_priors": list(priors),
        "prior_menu_source": prior_source,
        "named_candidates": list(named),
        "hard_off_loaded": sorted(families) if families else None,
        "hard_off_hits": hits,
        "candidates": list(candidates),
        "identity": {"ns": _NS, "login": _LOGIN, "symbol": symbol},
    }
    scrubbed = _scrub(body)
    return scrubbed if isinstance(scrubbed, dict) else {}


def _remember(state: Dict[str, Any], rows: Sequence[Tuple[str, Any, Optional[str]]]) -> None:
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


def _ask(state: Dict[str, Any], questions: Dict[str, Any]) -> Dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = dict(state)
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    try:
        from .jev_questions import prior_outcomes

        loaded = prior_outcomes(state=payload, questions=questions)
    except Exception:
        loaded = None
    payload["prior_outcomes"] = [] if loaded is None else loaded
    try:
        from .jev_client import evaluate

        receipt = evaluate(
            payload,
            questions=questions,
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {
            "error": type(exc).__name__,
            "answers": {},
            "state": payload,
            "model": MODEL,
        }
    if not isinstance(receipt, dict):
        return {
            "error": "evaluate_not_a_dict",
            "answers": {},
            "state": payload,
            "model": MODEL,
        }
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    error = None if answers else (receipt.get("error") or receipt.get("skipped") or "empty")
    return {
        "error": error,
        "answers": answers,
        "state": payload,
        "model": receipt.get("model") or MODEL,
    }


def _parse(
    answers: Dict[str, Any],
    qid_for_tag: Dict[str, str],
    families: Sequence[str],
    receipt_error: Any,
) -> Dict[str, Any]:
    rows: List[Tuple[str, Any, Optional[str]]] = []

    def take(qid: str, kind: str, order: Tuple[str, ...]) -> Any:
        block = answers.get(qid)
        if kind == "noul":
            value = _noul(block)
        elif kind == "choice":
            value = _choice(block, order)
        else:
            value = _score(block)
        rows.append((qid, value, _why(block, value, order, receipt_error)))
        return value

    disposition: Dict[str, Optional[str]] = {}
    for qid, tag in qid_for_tag.items():
        disposition[tag] = take(qid, "choice", _DISPOSITION_ORDER)
    hard_off: Dict[str, Any] = {}
    for name in families:
        hard_off[name] = take(f"alive_hard_off_{name}", "noul", ("true", "false"))
    return {
        "disposition": disposition,
        "source": take(_Q_SOURCE, "choice", _SOURCE_ORDER),
        "relax": take(_Q_RELAX, "noul", ("true", "false")),
        "candidate": take(_Q_CANDIDATE, "noul", ("true", "false")),
        "same_tag": take(_Q_SAME, "noul", ("true", "false")),
        "sufficient": take(_Q_SUFFICIENT, "noul", ("true", "false")),
        "threshold": take(_Q_THRESHOLD, "score", ()),
        "loop_bound": take(_Q_LOOP, "score", ()),
        "parameter": take(_Q_PARAMETER, "score", ()),
        "component": take(_Q_COMPONENT, "choice", _COMPONENT_ORDER),
        "exists": take(_Q_EXISTS, "noul", ("true", "false")),
        "hard_off": hard_off,
        "rows": rows,
    }


def _buckets(
    candidates: Sequence[str],
    priors: set,
    disposition: Dict[str, Optional[str]],
    hits: Dict[str, Optional[str]],
) -> Tuple[Optional[List[str]], Optional[List[Dict[str, Any]]], Optional[List[str]], Optional[List[str]]]:
    """Group returned dispositions. A tag with no choice stays out."""

    alive: List[str] = []
    blocked: List[Dict[str, Any]] = []
    dropped: List[str] = []
    injected: List[str] = []
    for tag in candidates:
        disp = disposition.get(tag)
        if disp == "alive":
            alive.append(tag)
            if tag in priors:
                injected.append(tag)
        elif disp == "blocked":
            blocked.append(
                {
                    "tag": tag,
                    "hard_off_family": hits.get(tag),
                    "escape": "blocked",
                    "note": "disposition is the System One return",
                }
            )
        elif disp == "drop":
            dropped.append(tag)
    alive_out = sorted(set(alive)) if alive else None
    blocked_out = sorted(blocked, key=lambda row: str(row.get("tag"))) if blocked else None
    dropped_out = sorted(set(dropped)) if dropped else None
    injected_out = sorted(set(injected)) if injected else None
    return alive_out, blocked_out, dropped_out, injected_out


def alive_sleeves_for_symbol(
    symbol: str,
    *,
    account: Optional[str] = None,
    use_research_overlay: Optional[bool] = None,
    relax_to_jev: Optional[bool] = None,
) -> Dict[str, Any]:
    """Alive sleeve tags for one symbol. Membership and parameters are the return."""

    symbol = str(symbol).upper()
    relax_fact = relax_to_jev_enabled(relax_to_jev)
    overlay_fact = use_research_overlay if isinstance(use_research_overlay, bool) else None
    live_tags, live_meta = load_live_armed_tags(account)
    research_tags, research_meta = load_research_armed_tags()
    raw_research, research_compose = _raw_tags(symbol, research_tags)
    raw_live, live_compose = _raw_tags(symbol, live_tags)
    families, hard_meta = hard_off_families()
    priors, prior_source = _priors_for(symbol)
    named = _named_candidates(research_meta)
    candidates = _dedupe([*raw_research, *raw_live, *priors, *named])
    qid_for_tag = _tag_qids(candidates)
    family_names = _family_names(families)
    hits = _hits(candidates, families)
    state = _state(
        symbol,
        account,
        overlay_fact,
        relax_fact,
        live_tags,
        research_tags,
        raw_research,
        raw_live,
        priors,
        prior_source,
        named,
        families,
        hits,
        candidates,
        research_meta,
    )
    _bind_card(state)
    try:
        questions = _questions(qid_for_tag, family_names)
    finally:
        _bind_card(None)
    asked = _ask(state, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    parsed = _parse(answers, qid_for_tag, family_names, asked.get("error"))
    _remember(asked.get("state") or state, parsed["rows"])
    alive, blocked, dropped, injected = _buckets(
        candidates,
        set(priors),
        parsed["disposition"],
        hits,
    )
    source = parsed["source"]
    if source == "research_armed":
        n_slots: Any = research_compose.get("n_slots")
        n_raw: Any = research_compose.get("n_raw")
    elif source == "live_armed":
        n_slots = live_compose.get("n_slots")
        n_raw = live_compose.get("n_raw")
    else:
        n_slots = None
        n_raw = None
    error = None if answers else (asked.get("error") or "empty")
    return {
        "schema": "gtos.dig.jev_sleeve_select.alive_sleeves_for_symbol.v1",
        "ts_ict": _ict_now(),
        "field": "inventory.alive_sleeves_for_symbol",
        "chair": "JEV_SLEEVE_SELECT",
        "symbol": symbol,
        "model": asked.get("model") or MODEL,
        "alive_sleeves_for_symbol": alive,
        "blocked_escape": blocked,
        "hard_off_silently_dropped": dropped,
        "tag_disposition": parsed["disposition"],
        "relax_to_jev": parsed["relax"],
        "armed_source": source,
        "alive_threshold": parsed["threshold"],
        "alive_loop_bound": parsed["loop_bound"],
        "alive_parameter": parsed["parameter"],
        "alive_component": parsed["component"],
        "alive_component_exists": parsed["exists"],
        "alive_candidate_built": parsed["candidate"],
        "alive_same_tag": parsed["same_tag"],
        "alive_state_sufficient": parsed["sufficient"],
        "hard_off_nouls": parsed["hard_off"],
        "research_armed_tags": research_tags,
        "live_armed_tags": live_tags,
        "live_armed_set_mutated": False,
        "named_function_exists": True,
        "alive_error": error,
        "fail_closed": error is not None,
        "compose": {
            "recipe": (
                "tag disposition, armed source, nouls, and scores are one "
                "jev_client.evaluate return; a miss stays unset"
            ),
            "n_slots": n_slots,
            "n_raw_for_symbol": n_raw,
            "research_compose": research_compose,
            "live_compose": live_compose,
            "specs": {
                "research": research_compose.get("specs"),
                "live": live_compose.get("specs"),
            },
            "hard_off_meta": hard_meta,
            "live_armed_meta": live_meta,
            "research_armed_meta": research_meta,
            "occupancy_invented": False,
            "corr_invented": False,
            "news_invented": False,
            "prior_menu_source": prior_source,
            "f5_keep_priors_injected": injected,
            "f5_keep_priors_for_symbol": list(priors),
            "questions": sorted(questions),
        },
        "apply": False,
        "place": False,
        "promote": False,
    }


def _shown_count(value: Any) -> Any:
    if isinstance(value, list):
        return len(value)
    return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(argv or sys.argv[1:])
    symbol = "EURUSD"
    if "--symbol" in argv:
        symbol = argv[argv.index("--symbol") + 1]
    elif argv and not argv[0].startswith("-"):
        symbol = argv[0]
    relax = True if "--relax-to-jev" in argv else None
    use_research = False if "--live-armed" in argv else None

    pack = alive_sleeves_for_symbol(symbol, use_research_overlay=use_research, relax_to_jev=relax)
    demos = {
        s: alive_sleeves_for_symbol(s, use_research_overlay=use_research, relax_to_jev=relax)
        for s in ("XAUUSD", "EURUSD", "GBPUSD", "USDJPY")
    }

    out_json = _HERE / "JEV_SLEEVE_SELECT_ALIVE_SLEEVES_20260920.json"
    out_md = _HERE / "JEV_SLEEVE_SELECT_ALIVE_SLEEVES_20260920.md"
    report = {
        "schema": "gtos.dig.jev_sleeve_select.writer_report.v1",
        "ts_ict": _ict_now(),
        "writer": str(_HERE / "alive_sleeves_for_symbol.py"),
        "named_function": "alive_sleeves_for_symbol",
        "place": False,
        "apply": False,
        "live_armed_set_mutated": False,
        "primary": pack,
        "demos": {
            s: {
                "alive": d["alive_sleeves_for_symbol"],
                "blocked_escape": d["blocked_escape"],
                "relax_to_jev": d["relax_to_jev"],
                "armed_source": d["armed_source"],
                "n_alive": _shown_count(d["alive_sleeves_for_symbol"]),
            }
            for s, d in demos.items()
        },
        "paths": {
            "writer": str(_HERE / "alive_sleeves_for_symbol.py"),
            "pointers": str(_DIG_WAR / "ALIVE_SLEEVES_FOR_SYMBOL_POINTERS_20260920.md"),
            "build_slots": str(_SWARM_SRC / "components/ultimate_book/symbol_resolution_watch.py"),
            "overlay": str(_OVERLAY),
        },
    }
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# JEV_SLEEVE_SELECT — alive_sleeves_for_symbol — {report['ts_ict']}",
        "",
        "**place=false** · **apply=false** · live_armed untouched",
        "",
        f"**Writer:** `{report['writer']}`",
        "",
        "## Recipe",
        "Disposition, source, nouls, and scores are the System One return. A miss stays unset.",
        "",
        f"Primary `{pack['symbol']}` alive=`{pack['alive_sleeves_for_symbol']}` relax={pack['relax_to_jev']}",
        f"blocked_escape=`{pack['blocked_escape']}`",
        "",
        "| symbol | n | alive | blocked_escape |",
        "|---|---:|---|---|",
    ]
    for s, d in report["demos"].items():
        lines.append(
            f"| {s} | {d['n_alive']} | `{d['alive']}` | `{d['blocked_escape']}` |"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "symbol": symbol,
                "alive": pack["alive_sleeves_for_symbol"],
                "blocked": pack["blocked_escape"],
                "json": str(out_json),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
