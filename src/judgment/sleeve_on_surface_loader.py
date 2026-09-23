"""Load a sleeve module's surface from the recovery menu.

One ask: ``jev_client.evaluate`` with model ``jev-1.13.0`` and
``merge_sleeve=False``. That call POSTs https://api.typesafe.ai/v1/systemone.
The status, the tag, the path, apply, the direction, on-surface membership,
which component exists, the threshold, the loop bound, and the parameter
are the Noul, Choice, or Score that came back. Prior outcomes are attached
on that ask, and the return is stored for the next ask.

Parsed literals stay facts on the ask. An empty answer, a tie, or an error
leaves that return unset and does not restore a constant. A dollar line is
not a question. This module does not send.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Mapping

MODEL = "jev-1.13.0"
CHALLENGE_LOGIN = "0"
CHALLENGE_NS = "operator"
CHALLENGE_MAGIC = "0"

_RECOVERED = Path("/workspace/gtos/research/codila_absorb/war_room/recovered")
_FABLE = Path("/workspace/gtos/redacted_host/parked/sleeves")
_WARROOM = Path("/workspace/gtos/research/warroom_20260920")
_VPS_SLEEVES = Path(r"C:host-local/redacted_host/repo/src/components/ultimate_book/sleeves")
_SWARM = Path("/workspace/gtos/_swarm_land_tip/extract/src/components/ultimate_book/sleeves")

_ROOTS = (
    ("recovered", _RECOVERED),
    ("warroom", _WARROOM),
    ("fable", _FABLE),
    ("vps_sleeves", _VPS_SLEEVES),
    ("swarm", _SWARM),
)

_STATUS_ORDER = ("LOADED_FROM_RECOVERY", "MISSING_MODULE")
_STATUS_CRITERIA = {
    "LOADED_FROM_RECOVERY": "This sleeve module is the loaded surface for this state.",
    "MISSING_MODULE": "This sleeve module is missing for this state.",
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
_ALLOWED = {"noul", "choice", "score"}
_CORE = (
    "surface_status",
    "surface_tag",
    "surface_apply",
    "surface_direction",
    "surface_component",
    "surface_component_exists",
    "surface_threshold",
    "surface_loop_bound",
    "surface_parameter",
)
_LITERALS = ("ON_SURFACE", "TAG", "_DIRECTION", "DIRECTION")



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


def _paths_for(tag: str) -> list[Path]:
    return [root / f"{tag}.py" for _name, root in _ROOTS]


MODULES = {
    "dsp_expanding_up_staircase": _paths_for("dsp_expanding_up_staircase"),
    "dsp_three_fresh_lower_lows": _paths_for("dsp_three_fresh_lower_lows"),
    "dsp_spring_close_on_20low_through_the_box": _paths_for("dsp_spring_close_on_20low_through_the_box"),
    "sub_mid_dn_re_proxy_eurusd_short_m15_atr": _paths_for("sub_mid_dn_re_proxy_eurusd_short_m15_atr"),
    "asian_fade": _paths_for("asian_fade"),
    "dsp_three_fresh": ["dsp_three_fresh_lower_lows"],
    "dsp_spring_close": ["dsp_spring_close_on_20low_through_the_box"],
    "sub_mid_dn_re_proxy": ["sub_mid_dn_re_proxy_eurusd_short_m15_atr"],
}


def _limit_key(name: str) -> bool:
    token = str(name).lower().replace("-", "_")
    if token in _LIMIT_KEYS:
        return True
    return "floor" in token or "baseline" in token


def _scrub_text(text: str) -> str:
    cleaned = str(text)
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


def _scrub(value: Any) -> Any:
    """Drop dollar-line keys before the ask."""

    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            name = str(key)
            if _limit_key(name):
                continue
            out[name] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, str):
        return _scrub_text(value)
    return value


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


def _probs(block: Any) -> dict[str, float]:
    if not isinstance(block, dict):
        return {}
    raw = block.get("probabilities")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, val in raw.items():
        number = _finite(val)
        if number is not None:
            out[str(key)] = number
    return out


def _unique(probs: Mapping[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A missing probability is not zero. A tie is unset."""

    if not probs:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    allowed = order or tuple(probs)
    for name in allowed:
        if name not in probs:
            continue
        p = probs[name]
        if best_p is None or p > best_p + 1e-12:
            best = str(name)
            best_p = p
            tied = False
        elif abs(p - best_p) <= 1e-12:
            tied = True
    if tied or best is None:
        return None
    return best


def _import_from(module: str, name: str) -> Any:
    try:
        from importlib import import_module

        try:
            loaded = import_module(f".{module}", package=__package__ or "judgment")
        except Exception:
            loaded = import_module(module)
        return getattr(loaded, name)
    except Exception:
        return None


def _choice_of(block: Any, order: tuple[str, ...]) -> tuple[str | None, dict[str, float]]:
    if not isinstance(block, dict) or block.get("error"):
        return None, {}
    probs = _probs(block)
    kept = {name: probs[name] for name in order if name in probs}
    picked: str | None = None
    unique_highest = _import_from("jev_questions", "unique_highest")
    if unique_highest is not None:
        try:
            found = unique_highest(probs or None, order)
        except Exception:
            found = None
        if found in order:
            picked = str(found)
    if picked is None:
        picked = _unique(probs, order)
    if picked not in order:
        return None, kept
    return picked, kept


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A miss stays missing."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked, _kept = _choice_of(block, ("true", "false"))
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _score_of(block: Any) -> float | None:
    """The score that came back. It is not snapped to a level."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    returned_number = _import_from("jev_questions", "returned_number")
    if returned_number is not None:
        try:
            return _finite(returned_number(block))
        except Exception:
            return None
    if "score" not in block or block.get("score") is None:
        return None
    return _finite(block.get("score"))


def _miss(block: Any, value: Any, order: tuple[str, ...], receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if receipt_error not in (None, ""):
        return str(receipt_error)
    probs = _probs(block)
    if probs and _unique(probs, order or tuple(probs)) is None:
        return "tie"
    return "empty"


def _choice_question(qid: str, instructions: str, criteria: Mapping[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {
        str(key): _scrub_text(val)
        for key, val in criteria.items()
        if not _limit_key(str(key))
    }
    if not cleaned:
        return {}
    body: dict[str, Any] = {"type": "choice", "instructions": text, "criteria": cleaned}
    spot_question = _import_from("jev_questions", "spot_question")
    if spot_question is not None:
        try:
            built = spot_question(qid, text, cleaned)
            block = built.get(qid) if isinstance(built, dict) else None
            if isinstance(block, dict):
                shaped = {key: val for key, val in block.items() if not _limit_key(str(key))}
                shaped["type"] = "choice"
                shaped["instructions"] = text
                shaped["criteria"] = cleaned
                body = shaped
        except Exception:
            pass
    return {qid: body}



def _score_question(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    if _limit_key(qid):
        return {}
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(instructions),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _canonical(tag: str) -> str:
    seen: set[str] = set()
    current = tag
    while current not in seen:
        seen.add(current)
        paths = MODULES.get(current)
        if paths and isinstance(paths[0], str):
            current = str(paths[0])
            continue
        break
    return current


def _menu_tags() -> tuple[tuple[str, ...], tuple[str, ...]]:
    canonical: list[str] = []
    aliases: list[str] = []
    for key, paths in MODULES.items():
        if paths and isinstance(paths[0], str):
            aliases.append(str(key))
        else:
            canonical.append(str(key))
    return tuple(canonical), tuple(aliases)


def _assign_literal(found: dict[str, Any], name: str, value: ast.AST | None) -> None:
    if name not in _LITERALS or value is None:
        return
    try:
        found[name] = ast.literal_eval(value)
    except Exception:
        return


def _proposed(path: Path) -> dict[str, Any]:
    """Literals on this file. They are facts for the ask, not the decision."""

    row: dict[str, Any] = {
        "readable": False,
        "proposed_tag": None,
        "proposed_on_surface": None,
        "proposed_direction": None,
    }
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return row
    row["readable"] = True
    found: dict[str, Any] = {}
    try:
        tree = ast.parse(src)
    except Exception:
        tree = None
    if tree is not None:
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        _assign_literal(found, target.id, node.value)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                _assign_literal(found, node.target.id, node.value)
    surface = found.get("ON_SURFACE")
    if surface is None:
        matched = re.search(r"ON_SURFACE[^=]*=\s*(\([^)]+\))", src)
        if matched:
            try:
                surface = ast.literal_eval(matched.group(1))
            except Exception:
                surface = None
    if isinstance(surface, tuple):
        surface = list(surface)
    if isinstance(surface, list):
        symbols: list[str] = []
        for item in surface:
            if isinstance(item, str) and item.strip() and not _limit_key(item):
                symbols.append(item.strip())
        row["proposed_on_surface"] = symbols
    tag = found.get("TAG")
    if isinstance(tag, str) and tag.strip() and not _limit_key(tag):
        row["proposed_tag"] = tag.strip()
    direction = found.get("_DIRECTION")
    if direction is None:
        direction = found.get("DIRECTION")
    number = _finite(direction)
    if number is None:
        matched = re.search(r"_DIRECTION\s*=\s*(-?\d+(?:\.\d+)?)", src) or re.search(
            r"DIRECTION\s*=\s*(-?\d+(?:\.\d+)?)",
            src,
        )
        if matched:
            number = _finite(matched.group(1))
    row["proposed_direction"] = number
    return row


def _candidate_paths(tag: str) -> list[tuple[str, Path]]:
    paths = MODULES.get(tag)
    if paths and not isinstance(paths[0], str):
        paired = list(zip((name for name, _root in _ROOTS), paths))
        return [(name, path) for name, path in paired if isinstance(path, Path)]
    return [(name, root / f"{tag}.py") for name, root in _ROOTS]


def _gather(tag_or_alias: Any) -> dict[str, Any]:
    requested = "" if tag_or_alias is None else str(tag_or_alias)
    canonical = _canonical(requested)
    candidates: list[dict[str, Any]] = []
    symbols: list[str] = []
    seen_symbols: set[str] = set()
    for name, path in _candidate_paths(canonical):
        exists = path.exists()
        measured = _proposed(path) if exists else {
            "readable": False,
            "proposed_tag": None,
            "proposed_on_surface": None,
            "proposed_direction": None,
        }
        candidates.append({
            "id": name,
            "root": name,
            "path": str(path),
            "exists": bool(exists),
            "readable": bool(measured.get("readable")),
            "proposed_tag": measured.get("proposed_tag"),
            "proposed_on_surface": measured.get("proposed_on_surface"),
            "proposed_direction": measured.get("proposed_direction"),
        })
        proposed = measured.get("proposed_on_surface")
        if exists and isinstance(proposed, list):
            for symbol in proposed:
                if symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    symbols.append(symbol)
    existing = [row for row in candidates if row.get("exists")]
    return {
        "requested_tag": requested,
        "canonical_tag": canonical,
        "alias": requested != canonical,
        "candidates": candidates,
        "any_exists": bool(existing),
        "measured_candidate_count": len(candidates),
        "existing_count": len(existing),
        "proposed_symbols": symbols,
    }


def _symbol_qid(symbol: str, used: dict[str, str]) -> str | None:
    cleaned = "".join(ch for ch in str(symbol) if ch.isalnum() or ch == "_")
    if not cleaned or _limit_key(cleaned):
        return None
    qid = f"on_surface_{cleaned}"
    if _limit_key(qid):
        return None
    if qid in used and used[qid] != symbol:
        qid = f"{qid}_{len(used)}"
    used[qid] = symbol
    return qid


def _tag_order(facts: Mapping[str, Any]) -> tuple[str, ...]:
    canonical, aliases = _menu_tags()
    ordered: list[str] = []
    seen: set[str] = set()

    def add(name: Any) -> None:
        if not isinstance(name, str):
            return
        text = name.strip()
        if not text or text in seen or _limit_key(text):
            return
        seen.add(text)
        ordered.append(text)

    for name in canonical:
        add(name)
    for name in aliases:
        add(name)
    add(facts.get("requested_tag"))
    add(facts.get("canonical_tag"))
    for row in facts.get("candidates") or []:
        if isinstance(row, dict):
            add(row.get("proposed_tag"))
    return tuple(ordered)


def _component_order(facts: Mapping[str, Any]) -> tuple[str, ...]:
    canonical, _aliases = _menu_tags()
    ordered = [name for name in canonical if not _limit_key(name)]
    extra = facts.get("canonical_tag")
    if isinstance(extra, str) and extra.strip() and extra not in ordered and not _limit_key(extra):
        ordered.append(extra.strip())
    return tuple(ordered)


def _direction_levels(facts: Mapping[str, Any]) -> list[str]:
    found: list[float] = []
    for row in facts.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        number = _finite(row.get("proposed_direction"))
        if number is not None:
            found.append(number)
    numbers = [format(number, ".10g") for number in sorted(set(found))]
    return numbers + [item for item in _BETWEEN if item not in numbers]


def _questions(facts: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """One pack. Types are choice, noul, or score."""

    _bind_card(facts)
    try:
        pack: dict[str, Any] = {}
        pack.update(_choice_question(
            "surface_status",
            "Is this sleeve module the loaded surface for this state, or is it missing? "
            "File existence on this state is a fact. "
            "The option you return is the status. "
            "An empty answer or a tie is not a status. "
            "Do not send.",
            _STATUS_CRITERIA,
        ))
        tag_order = _tag_order(facts)
        pack.update(_choice_question(
            "surface_tag",
            "Which tag is this sleeve on this state? "
            "The option you return is the tag. "
            "An empty answer or a tie is not a tag. "
            "Do not send.",
            {name: f"{name} is the sleeve tag on this state." for name in tag_order},
        ))
        path_order: list[str] = []
        path_by_id: dict[str, str] = {}
        for row in facts.get("candidates") or []:
            if not isinstance(row, dict) or not row.get("exists"):
                continue
            ident = str(row.get("id") or "")
            if not ident or _limit_key(ident):
                continue
            path_order.append(ident)
            path_by_id[ident] = str(row.get("path") or "")
        if path_order:
            pack.update(_choice_question(
                "surface_path",
                "Which copy is the path for this sleeve on this state? "
                "The copies on this state are facts. "
                "The option you return is the path. "
                "An empty answer or a tie is not a path. "
                "Do not send.",
                {ident: f"The {ident} copy is the path for this state." for ident in path_order},
            ))
        pack.update(_noul_question(
            "surface_apply",
            "Does this sleeve surface apply on this state? "
            "The noul you return is that answer. "
            "An empty noul leaves apply unset. "
            "Do not send.",
            "This sleeve surface applies on this state.",
            "This sleeve surface does not apply on this state.",
        ))
        pack.update(_score_question(
            "surface_direction",
            "The score you return is the direction for this sleeve on this state. "
            "It may sit between the levels on this state. "
            "A direction already written on a copy is a fact. "
            "An empty score leaves the direction unset. "
            "Do not send.",
            _direction_levels(facts),
        ))
        component_order = _component_order(facts)
        pack.update(_choice_question(
            "surface_component",
            "Which sleeve component is this load on this state? "
            "The option you return is that component. "
            "An empty answer or a tie is not a component. "
            "Do not send.",
            {name: f"{name} is the sleeve component on this state." for name in component_order},
        ))
        pack.update(_noul_question(
            "surface_component_exists",
            "Does this sleeve component exist on this state? "
            "The noul you return is that existence. "
            "An empty noul leaves it unset. "
            "Do not send.",
            "This sleeve component exists on this state.",
            "This sleeve component does not exist on this state.",
        ))
        pack.update(_score_question(
            "surface_threshold",
            "The score you return is the threshold for this sleeve surface. "
            "It may sit between the levels on this state. "
            "An empty score leaves the threshold unset. "
            "Do not send.",
            _BETWEEN,
        ))
        pack.update(_score_question(
            "surface_loop_bound",
            "The score you return is how many candidate copies this load considers. "
            "The measured candidate count on this state is a fact. "
            "It may sit between the levels on this state. "
            "An empty score leaves the bound unset. "
            "Do not send.",
            _BETWEEN,
        ))
        pack.update(_score_question(
            "surface_parameter",
            "The score you return is the parameter for this sleeve surface. "
            "It may sit between the levels on this state. "
            "An empty score leaves the parameter unset. "
            "Do not send.",
            _BETWEEN,
        ))
        used: dict[str, str] = {}
        symbol_qids: list[tuple[str, str]] = []
        for symbol in facts.get("proposed_symbols") or []:
            qid = _symbol_qid(str(symbol), used)
            if qid is None:
                continue
            symbol_qids.append((str(symbol), qid))
            pack.update(_noul_question(
                qid,
                f"Is {symbol} on this sleeve surface for this state? "
                "The symbols written on a copy are facts. "
                "The noul you return is that membership. "
                "An empty noul leaves this symbol unset. "
                "Do not send.",
                f"{symbol} is on this sleeve surface.",
                f"{symbol} is not on this sleeve surface.",
            ))
        plan = {
            "tag_order": tag_order,
            "path_order": tuple(path_order),
            "path_by_id": path_by_id,
            "component_order": component_order,
            "symbol_qids": tuple(symbol_qids),
        }
        return pack, plan
    finally:
        _bind_card(None)


def _pack_ok(questions: Mapping[str, Any], plan: Mapping[str, Any]) -> bool:
    required = list(_CORE)
    if plan.get("path_order"):
        required.append("surface_path")
    for _symbol, qid in plan.get("symbol_qids") or ():
        required.append(qid)
    if not questions:
        return False
    for qid in required:
        block = questions.get(qid)
        if not isinstance(block, dict) or block.get("type") not in _ALLOWED:
            return False
    for block in questions.values():
        if not isinstance(block, dict) or block.get("type") not in _ALLOWED:
            return False
    return True


def _payload(facts: Mapping[str, Any]) -> dict[str, Any]:
    body = {
        "model": MODEL,
        "namespace": CHALLENGE_NS,
        "login": CHALLENGE_LOGIN,
        "magic": CHALLENGE_MAGIC,
        "requested_tag": facts.get("requested_tag"),
        "canonical_tag": facts.get("canonical_tag"),
        "alias": bool(facts.get("alias")),
        "any_exists": bool(facts.get("any_exists")),
        "measured_candidate_count": facts.get("measured_candidate_count"),
        "existing_count": facts.get("existing_count"),
        "candidates": facts.get("candidates"),
        "proposed_symbols": facts.get("proposed_symbols"),
        "identity": {
            "ns": CHALLENGE_NS,
            "login": CHALLENGE_LOGIN,
            "magic": CHALLENGE_MAGIC,
            "tag": facts.get("canonical_tag"),
        },
    }
    scrubbed = _scrub(body)
    return scrubbed if isinstance(scrubbed, dict) else {}


def _remember(state: Mapping[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
    append_outcome = _import_from("jev_questions", "append_outcome")
    if append_outcome is None:
        return
    logged = dict(state)
    logged.pop("prior_outcomes", None)
    for key, value, error in rows:
        try:
            append_outcome(key, value, logged, error=error)
        except Exception:
            return


def _ask(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One evaluate. Priors go on this ask. No second client."""

    payload = _scrub(dict(state))
    payload.pop("prior_outcomes", None)
    payload["model"] = MODEL
    prior_outcomes = _import_from("jev_questions", "prior_outcomes")
    loaded: Any = None
    if prior_outcomes is not None:
        try:
            loaded = prior_outcomes(state=payload, questions=questions)
        except Exception:
            loaded = None
    payload["prior_outcomes"] = [] if loaded is None else loaded
    evaluate = _import_from("jev_client", "evaluate")
    if evaluate is None:
        return {"error": "evaluate_unimported", "answers": {}, "state": payload, "model": MODEL}
    try:
        receipt = evaluate(
            payload,
            questions=dict(questions),
            merge_sleeve=False,
            model=MODEL,
        )
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return {"error": type(exc).__name__, "answers": {}, "state": payload, "model": MODEL}
    if not isinstance(receipt, dict):
        return {"error": "evaluate_not_a_dict", "answers": {}, "state": payload, "model": MODEL}
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


def _unset(error: str | None) -> dict[str, Any]:
    return {
        "path": None,
        "status": None,
        "ON_SURFACE": None,
        "TAG": None,
        "_DIRECTION": None,
        "DIRECTION": None,
        "apply": None,
        "surface_threshold": None,
        "surface_loop_bound": None,
        "surface_parameter": None,
        "surface_component": None,
        "surface_component_exists": None,
        "on_surface": None,
        "error": error,
        "model": MODEL,
    }


def _surface_list(membership: list[tuple[str, Any]]) -> list[str] | None:
    """Bool membership only. A probability is not cut into the list."""

    if not membership:
        return None
    names: list[str] = []
    for symbol, value in membership:
        if value is True:
            names.append(symbol)
            continue
        if value is False:
            continue
        return None
    return names


def _read(
    plan: Mapping[str, Any],
    asked: Mapping[str, Any],
) -> dict[str, Any]:
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    receipt_error = asked.get("error")
    status, _status_probs = _choice_of(answers.get("surface_status"), _STATUS_ORDER)
    tag_order = tuple(plan.get("tag_order") or ())
    tag, _tag_probs = _choice_of(answers.get("surface_tag"), tag_order)
    path_order = tuple(plan.get("path_order") or ())
    path_choice, _path_probs = _choice_of(answers.get("surface_path"), path_order)
    path_by_id = plan.get("path_by_id") if isinstance(plan.get("path_by_id"), dict) else {}
    path = path_by_id.get(path_choice) if path_choice else None
    if path is not None:
        path = str(path)
    apply = _noul_of(answers.get("surface_apply"))
    direction = _score_of(answers.get("surface_direction"))
    component_order = tuple(plan.get("component_order") or ())
    component, _component_probs = _choice_of(answers.get("surface_component"), component_order)
    exists = _noul_of(answers.get("surface_component_exists"))
    threshold = _score_of(answers.get("surface_threshold"))
    loop_bound = _score_of(answers.get("surface_loop_bound"))
    parameter = _score_of(answers.get("surface_parameter"))
    membership: list[tuple[str, Any]] = []
    surface_map: dict[str, Any] | None = None
    symbol_qids = tuple(plan.get("symbol_qids") or ())
    if symbol_qids:
        surface_map = {}
        for symbol, qid in symbol_qids:
            value = _noul_of(answers.get(qid))
            surface_map[symbol] = value
            membership.append((symbol, value))
    rows: list[tuple[str, Any, str | None]] = [
        ("surface_status", status, _miss(answers.get("surface_status"), status, _STATUS_ORDER, receipt_error)),
        ("surface_tag", tag, _miss(answers.get("surface_tag"), tag, tag_order, receipt_error)),
        ("surface_path", path_choice, _miss(answers.get("surface_path"), path_choice, path_order, receipt_error)),
        ("surface_apply", apply, _miss(answers.get("surface_apply"), apply, ("true", "false"), receipt_error)),
        ("surface_direction", direction, _miss(answers.get("surface_direction"), direction, (), receipt_error)),
        (
            "surface_component",
            component,
            _miss(answers.get("surface_component"), component, component_order, receipt_error),
        ),
        (
            "surface_component_exists",
            exists,
            _miss(answers.get("surface_component_exists"), exists, ("true", "false"), receipt_error),
        ),
        ("surface_threshold", threshold, _miss(answers.get("surface_threshold"), threshold, (), receipt_error)),
        ("surface_loop_bound", loop_bound, _miss(answers.get("surface_loop_bound"), loop_bound, (), receipt_error)),
        ("surface_parameter", parameter, _miss(answers.get("surface_parameter"), parameter, (), receipt_error)),
    ]
    for symbol, qid in symbol_qids:
        value = surface_map.get(symbol) if isinstance(surface_map, dict) else None
        rows.append((qid, value, _miss(answers.get(qid), value, ("true", "false"), receipt_error)))
    posted = asked.get("state") if isinstance(asked.get("state"), dict) else {}
    _remember(posted, rows)
    return {
        "path": path,
        "status": status,
        "ON_SURFACE": _surface_list(membership),
        "TAG": tag,
        "_DIRECTION": direction,
        "DIRECTION": direction,
        "apply": apply,
        "surface_threshold": threshold,
        "surface_loop_bound": loop_bound,
        "surface_parameter": parameter,
        "surface_component": component,
        "surface_component_exists": exists,
        "on_surface": surface_map,
        "error": receipt_error if not answers else None,
        "model": asked.get("model") or MODEL,
    }


def _judge(facts: Mapping[str, Any]) -> dict[str, Any]:
    questions, plan = _questions(facts)
    if not _pack_ok(questions, plan):
        return _unset("question_pack_fail")
    asked = _ask(_payload(facts), questions)
    return _read(plan, asked)


def load_sleeve_module(tag_or_alias: str) -> dict[str, Any]:
    """One System One return for this tag. A miss leaves the fields unset."""

    try:
        return _judge(_gather(tag_or_alias))
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return _unset(type(exc).__name__)
