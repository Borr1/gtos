"""Live sibling counter. Reads closed[] only.

Host live path (host-local):
  pipeline_state/ultimate_book/{ns}/judgment/state/just_closed_siblings.json

The closed[] count stays the integer read. The state choice, the exhausted
noul, the cap score, and the updated_ict staleness are the System One return
for this state. One hop: ``jev_client.evaluate`` with model ``jev-1.13.0``
(POST https://api.typesafe.ai/v1/systemone, ``merge_sleeve=False``).
Questions are only Noul, Choice, or Score. Prior outcomes are attached on
every ask. An empty answer, a tie, a missing score, or an error leaves that
return unset.

Top-level symbol keys (XAUUSD / US30.cash / …) frozen at 09-08 are legacy leftovers.
Do not treat judgment/live/just_closed_siblings.json as live.
closed[] is pruned ~24h — older same-day stops that aged out under-count.
This module does not send an order.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MappingLike = dict[str, Any]

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NS = "operator"
MODEL = "jev-1.13.0"
ABANDONED_TWIN = REPO_ROOT / "judgment" / "live" / "just_closed_siblings.json"

_META_KEYS = frozenset(
    {
        "closed",
        "updated_utc",
        "updated_ict",
        "n_closed",
        "schema",
        "law",
        "spent_tonight",
        "window",
        "note",
        "namespace",
    }
)
_ORIG_STOP = frozenset({"orig_stop", "sl", "stop", "orig_sl", "broker_sl"})



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


def f5_just_closed_siblings_path(repo_root: Path | None = None, namespace: str = DEFAULT_NS) -> Path:
    root = repo_root or REPO_ROOT
    return root / "pipeline_state" / "ultimate_book" / namespace / "judgment" / "state" / "just_closed_siblings.json"


def sibling_search_paths(namespace: str = DEFAULT_NS) -> list[Path]:
    extra = (os.environ.get("GTOS_JUST_CLOSED_SIBLINGS") or "").strip()
    paths: list[Path] = []
    if extra:
        paths.append(Path(extra))
    paths.extend(
        [
            f5_just_closed_siblings_path(namespace=namespace),
            REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "just_closed_siblings.json",
        ]
    )
    return paths


def load_siblings_doc(path: Path | None = None, *, namespace: str = DEFAULT_NS) -> dict[str, Any] | None:
    """Load the live siblings file. Never the abandoned judgment/live twin."""
    candidates = [path] if path is not None else sibling_search_paths(namespace)
    for candidate in candidates:
        if candidate is None:
            continue
        resolved = Path(candidate)
        if resolved.resolve() == ABANDONED_TWIN.resolve() and ABANDONED_TWIN.is_file():
            continue
        if not resolved.is_file():
            continue
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return payload
    return None


def closed_rows(doc: MappingLike) -> list[dict[str, Any]]:
    rows = doc.get("closed") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def legacy_symbol_keys(doc: MappingLike) -> list[str]:
    if not isinstance(doc, dict):
        return []
    return sorted(k for k in doc if k not in _META_KEYS and not isinstance(doc[k], list))


def _parse_utc(raw: Any) -> datetime | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _row_day(row: dict[str, Any]) -> str | None:
    dt = _parse_utc(row.get("closed_utc") or row.get("updated_utc") or row.get("time_utc"))
    if dt is None:
        return None
    return dt.date().isoformat()


def _is_orig_stop(row: dict[str, Any]) -> bool:
    cls = str(
        row.get("exit_class")
        or row.get("close_class")
        or row.get("reason")
        or row.get("class")
        or ""
    ).strip().lower()
    return cls in _ORIG_STOP


def _sleeve(row: dict[str, Any]) -> str:
    raw = str(row.get("sleeve") or row.get("tag") or "").strip()
    if raw.startswith("F5:"):
        raw = raw[3:]
    return raw


def same_sleeve_orig_stop_count_session_day(
    doc: MappingLike,
    *,
    sleeve: str,
    session_day: str,
    symbol: str | None = None,
    as_of_utc: datetime | None = None,
) -> int:
    """Count orig_stop rows in closed[] for this sleeve + UTC session day.

    Ignores top-level 09-08 symbol keys. Does not invent rows from deals
    for the envelope COUNT. Fluid labels may pass a deals-derived doc
    marked ``challenge_deals_label_not_count``. Rows after as_of are
    excluded so a packed week of deals cannot leak future stops.
    """
    want = sleeve[3:] if sleeve.startswith("F5:") else sleeve
    as_of = None
    if as_of_utc is not None:
        as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
        as_of = as_of.astimezone(timezone.utc)
    n = 0
    for row in closed_rows(doc):
        if not _is_orig_stop(row):
            continue
        if _sleeve(row) != want:
            continue
        if _row_day(row) != session_day:
            continue
        if symbol and str(row.get("symbol") or "") and str(row.get("symbol")) != symbol:
            continue
        if as_of is not None:
            closed_dt = _parse_utc(row.get("closed_utc") or row.get("updated_utc") or row.get("time_utc"))
            if closed_dt is not None and closed_dt > as_of:
                continue
        n += 1
    return n


_CHOICE_ORDER = ("exhausted", "room")
_CHOICE_CRITERIA = {
    "exhausted": "Same-sleeve original stops on this session day are spent.",
    "room": "This sleeve still has room on this session day.",
}
_NOUL_ORDER = ("true", "false")
_LIMIT_KEYS = frozenset(
    {
        "floor",
        "baseline",
        "day_start_baseline",
        "static_floor",
        "pass_line",
        "flatten_floor_usd",
        "daily_loss_pct",
        "floor_room",
    }
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
    """Drop limit keys and banned dollar tokens before the ask."""

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
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = _finite(value)
        if number is not None and number in (90000.0, 110000.0):
            return None
        return value
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


def _unique(probs: dict[str, float], order: tuple[str, ...]) -> str | None:
    """Unique highest probability. A tie is not a decision."""

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
        if best_p is None or p > best_p:
            best = name
            best_p = p
            tied = False
        elif p == best_p:
            tied = True
    if tied or best is None:
        return None
    return best


def _choice_of(block: Any) -> tuple[str | None, dict[str, float]]:
    if isinstance(block, dict) and block.get("error"):
        return None, {}
    probs = _probs(block)
    kept = {name: probs[name] for name in _CHOICE_ORDER if name in probs}
    local = _unique(probs, _CHOICE_ORDER)
    choice = local
    try:
        from .jev_questions import unique_highest

        agreed = unique_highest(probs or None, _CHOICE_ORDER)
        if agreed != local:
            choice = None
    except Exception:
        choice = local
    if choice not in _CHOICE_ORDER:
        choice = None
    return choice, kept


def _score_of(block: Any) -> float | None:
    """The score that came back. It is not snapped to a level."""

    if not isinstance(block, dict):
        return None
    try:
        from .jev_questions import returned_number

        return _finite(returned_number(block))
    except Exception:
        if block.get("error"):
            return None
        if "score" in block:
            return _finite(block.get("score"))
        return None


def _noul_of(block: Any) -> bool | float | None:
    """A Noul is a bool or a probability. A float is not cut at a line."""

    if not isinstance(block, dict) or block.get("error"):
        return None
    if "noul" in block and block.get("noul") is not None:
        raw = block.get("noul")
        if raw is True or raw is False:
            return raw
        return _finite(raw)
    picked = _unique(_probs(block), _NOUL_ORDER)
    if picked == "true":
        return True
    if picked == "false":
        return False
    return None


def _miss(block: Any, value: Any, order: tuple[str, ...], receipt_error: Any) -> str | None:
    if value is not None:
        return None
    if receipt_error not in (None, ""):
        return str(receipt_error)
    probs = _probs(block)
    if probs and _unique(probs, order or tuple(probs)) is None:
        return "tie"
    return "empty"


def _choice_question(qid: str, instructions: str, criteria: dict[str, str]) -> dict[str, Any]:
    text = _scrub_text(instructions)
    cleaned = {key: _scrub_text(val) for key, val in criteria.items()}
    body: dict[str, Any] = {"type": "choice", "instructions": text, "criteria": cleaned}
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



def _score_question(qid, instructions, card=None, *_rest):
    """Amount on this card, or an include-depth ordinal. A bare Score does not post."""

    return _score_amount_or_ordinal(qid, instructions, card)


def _noul_question(qid: str, instructions: str, yes: str, no: str) -> dict[str, Any]:
    return {
        qid: {
            "type": "noul",
            "instructions": _scrub_text(instructions),
            "criteria": {"true": _scrub_text(yes), "false": _scrub_text(no)},
        }
    }


def _questions() -> dict[str, Any]:
    """One pack. Types are choice, noul, or score."""

    pack: dict[str, Any] = {}
    pack.update(
        _choice_question(
            "two_stop",
            "For this sleeve on this session day, is the two-stop spent or is there still room? "
            "The closed count is a fact on this state. "
            "The option you return is the decision. "
            "An empty answer or a tie is not a decision. "
            "This ask does not transmit an order.",
            dict(_CHOICE_CRITERIA),
        )
    )
    pack.update(
        _noul_question(
            "two_stop_exhausted",
            "Are same-sleeve original stops for this sleeve on this session day spent? "
            "The noul you return is that answer. "
            "An empty answer leaves it unset. "
            "This ask does not transmit an order.",
            "Same-sleeve original stops on this session day are spent.",
            "This sleeve still has room on this session day.",
        )
    )
    pack.update(
        _score_question(
            "two_stop_cap",
            "What cap applies to same-sleeve original stops on this session day? "
            "The score you return is that cap. "
            "It may sit between levels. "
            "An empty score leaves the cap unset. "
            "This ask does not transmit an order.",
        )
    )
    pack.update(
        _noul_question(
            "two_stop_ict_stale",
            "Is updated_ict on this siblings document a stale leftover for this state? "
            "An empty answer leaves it unset. "
            "This ask does not transmit an order.",
            "updated_ict on this document is a stale leftover.",
            "updated_ict on this document is current for this state.",
        )
    )
    return pack


def _sleeve_key(sleeve: str) -> str:
    raw = str(sleeve or "")
    if raw.startswith("F5:"):
        return raw[3:]
    return raw


def _as_of_text(as_of_utc: datetime | None) -> str | None:
    if as_of_utc is None:
        return None
    stamp = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_fact(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket": row.get("ticket") or row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "sleeve": _sleeve(row),
        "day": _row_day(row),
        "closed_utc": row.get("closed_utc") or row.get("updated_utc") or row.get("time_utc"),
        "exit_class": str(
            row.get("exit_class")
            or row.get("close_class")
            or row.get("reason")
            or row.get("class")
            or ""
        ),
        "orig_stop": _is_orig_stop(row),
    }


def _count_fact(
    doc: MappingLike | None,
    *,
    sleeve: str,
    session_day: str,
    symbol: str | None,
    as_of_utc: datetime | None,
) -> int | None:
    if not doc:
        return None
    return same_sleeve_orig_stop_count_session_day(
        doc,
        sleeve=sleeve,
        session_day=session_day,
        symbol=symbol,
        as_of_utc=as_of_utc,
    )


def _source_fact(doc: MappingLike | None) -> str:
    if not doc:
        return "closed_absent"
    if isinstance(doc, dict):
        return str(doc.get("two_stop_source") or doc.get("source") or "closed[]")
    return "closed[]"


def _payload(
    doc: MappingLike | None,
    *,
    sleeve: str,
    session_day: str,
    symbol: str | None,
    as_of_utc: datetime | None,
    count: int | None,
    source: str,
) -> dict[str, Any]:
    namespace = DEFAULT_NS
    updated_ict = None
    updated_utc = None
    if isinstance(doc, dict):
        if doc.get("namespace"):
            namespace = str(doc.get("namespace"))
        updated_ict = doc.get("updated_ict")
        updated_utc = doc.get("updated_utc")
    sleeve_key = _sleeve_key(sleeve)
    body: dict[str, Any] = {
        "model": MODEL,
        "namespace": namespace,
        "sleeve": sleeve_key,
        "session_day": session_day,
        "symbol": symbol,
        "as_of_utc": _as_of_text(as_of_utc),
        "closed_absent": not bool(doc),
        "closed_orig_stop_count": count,
        "two_stop_source": source,
        "updated_ict": updated_ict,
        "updated_utc": updated_utc,
        "legacy_symbol_keys": legacy_symbol_keys(doc) if isinstance(doc, dict) else [],
        "closed": [_row_fact(row) for row in closed_rows(doc or {})],
        "identity": {
            "ns": namespace,
            "sleeve": sleeve_key,
            "symbol": symbol,
        },
    }
    scrubbed = _scrub(body)
    return scrubbed if isinstance(scrubbed, dict) else body


def _remember(state: dict[str, Any], rows: list[tuple[str, Any, str | None]]) -> None:
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


def _ask(state: dict[str, Any], questions: dict[str, Any]) -> dict[str, Any]:
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


def _blank(count: int | None, source: str, error: str) -> dict[str, Any]:
    return {
        "two_stop": None,
        "two_stop_probabilities": {},
        "two_stop_exhausted": None,
        "two_stop_cap": None,
        "two_stop_updated_ict_stale": None,
        "two_stop_error": error,
        "closed_orig_stop_count": count,
        "two_stop_source": source,
    }


def _two_stop_card(
    doc: MappingLike | None,
    *,
    sleeve: str,
    session_day: str,
    symbol: str | None,
    as_of_utc: datetime | None,
    count_symbol: str | None,
) -> dict[str, Any]:
    """One ask for this sleeve and session day. A miss stays unset."""

    count = _count_fact(
        doc,
        sleeve=sleeve,
        session_day=session_day,
        symbol=count_symbol,
        as_of_utc=as_of_utc,
    )
    source = _source_fact(doc)
    try:
        payload = _payload(
            doc,
            sleeve=sleeve,
            session_day=session_day,
            symbol=symbol,
            as_of_utc=as_of_utc,
            count=count,
            source=source,
        )
        _bind_card(payload)
        try:
            questions = _questions()
        finally:
            _bind_card(None)
    except Exception as exc:  # noqa: BLE001 — a miss stays unset
        return _blank(count, source, type(exc).__name__)
    allowed = {"choice", "noul", "score"}
    if not questions or any(
        not isinstance(block, dict) or block.get("type") not in allowed for block in questions.values()
    ):
        return _blank(count, source, "question_pack_fail")
    asked = _ask(payload, questions)
    answers = asked.get("answers") if isinstance(asked.get("answers"), dict) else {}
    receipt_error = asked.get("error")
    choice, probs = _choice_of(answers.get("two_stop"))
    exhausted = _noul_of(answers.get("two_stop_exhausted"))
    cap_score = _score_of(answers.get("two_stop_cap"))
    ict = _noul_of(answers.get("two_stop_ict_stale"))
    remember = [
        ("two_stop", choice, _miss(answers.get("two_stop"), choice, _CHOICE_ORDER, receipt_error)),
        (
            "two_stop_exhausted",
            exhausted,
            _miss(answers.get("two_stop_exhausted"), exhausted, _NOUL_ORDER, receipt_error),
        ),
        (
            "two_stop_cap",
            cap_score,
            _miss(answers.get("two_stop_cap"), cap_score, (), receipt_error),
        ),
        (
            "two_stop_ict_stale",
            ict,
            _miss(answers.get("two_stop_ict_stale"), ict, _NOUL_ORDER, receipt_error),
        ),
    ]
    posted = asked.get("state") if isinstance(asked.get("state"), dict) else payload
    _remember(posted, remember)
    return {
        "two_stop": choice,
        "two_stop_probabilities": probs,
        "two_stop_exhausted": exhausted,
        "two_stop_cap": cap_score,
        "two_stop_updated_ict_stale": ict,
        "two_stop_error": receipt_error if not answers else None,
        "closed_orig_stop_count": count,
        "two_stop_source": source,
    }


def two_stop_exhausted(
    doc: MappingLike | None,
    *,
    sleeve: str,
    session_day: str,
    symbol: str | None = None,
    as_of_utc: datetime | None = None,
) -> bool | float | None:
    """Exhausted noul for this sleeve and session day. A miss stays unset."""

    card = _two_stop_card(
        doc,
        sleeve=sleeve,
        session_day=session_day,
        symbol=symbol,
        as_of_utc=as_of_utc,
        count_symbol=symbol,
    )
    return card["two_stop_exhausted"]


def occupancy_from_closed(
    doc: MappingLike | None,
    *,
    sleeve: str,
    as_of_utc: datetime,
    symbol: str | None = None,
) -> dict[str, Any]:
    """Integer closed[] count, plus the choice, noul, cap, and staleness from one ask."""

    day = as_of_utc.astimezone(timezone.utc).date().isoformat()
    card = _two_stop_card(
        doc,
        sleeve=sleeve,
        session_day=day,
        symbol=symbol,
        as_of_utc=as_of_utc,
        count_symbol=None,
    )
    out: dict[str, Any] = {
        "same_sleeve_orig_stops_utc_day": card["closed_orig_stop_count"],
        "two_stop": card["two_stop"],
        "two_stop_probabilities": card["two_stop_probabilities"],
        "two_stop_exhausted": card["two_stop_exhausted"],
        "two_stop_cap": card["two_stop_cap"],
        "two_stop_source": card["two_stop_source"],
        "two_stop_updated_ict_stale": card["two_stop_updated_ict_stale"],
        "two_stop_error": card["two_stop_error"],
    }
    if doc:
        out["two_stop_legacy_keys_ignored"] = legacy_symbol_keys(doc)
        out["two_stop_updated_utc"] = doc.get("updated_utc") if isinstance(doc, dict) else None
    return out


def closed_doc_from_deals(rows: list[dict[str, Any]] | None, *, stamp) -> dict[str, Any] | None:
    """LABEL-only closed[] from named Challenge orig_stop deals.

    Not the envelope COUNT. Live ``just_closed_siblings.json`` stays senior
    when present. Do not feed this doc to a flatten / remint / place path.
    """
    if not rows:
        return None
    from .hold_from_tape import classify_close

    closed: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or row.get("still_open"):
            continue
        cls = classify_close(row.get("close_reason") or row.get("reason"), row.get("exit_class") or row.get("close_class"))
        if cls != "orig_stop":
            continue
        close_probe = {
            "open_time_utc": row.get("close_time_utc") or row.get("close_time"),
            "open_time_server": row.get("close_time_server"),
        }
        if not close_probe["open_time_utc"]:
            continue
        close_utc = stamp(close_probe)
        sleeve = str(row.get("sleeve") or row.get("comment") or row.get("tag") or "")
        if sleeve.startswith("F5:"):
            sleeve = sleeve[3:]
        closed.append(
            {
                "ticket": row.get("ticket") or row.get("candidate_id"),
                "symbol": row.get("symbol"),
                "sleeve": sleeve,
                "closed_utc": close_utc.strftime("%Y-%m-%dT%H:%M:%SZ") if close_utc else None,
                "exit_class": "orig_stop",
            }
        )
    if not closed:
        return None
    return {
        "closed": closed,
        "n_closed": len(closed),
        "source": "challenge_deals_label_not_count",
        "two_stop_source": "challenge_deals_label_not_count",
        "note": "LABEL only. Envelope COUNT still reads live closed[].",
    }


def siblings_doc_for_label(rows: list[dict[str, Any]] | None, *, stamp, namespace: str = DEFAULT_NS) -> dict[str, Any] | None:
    """Live closed[] if present; else Challenge-deal labels. Envelope stays integer."""
    live = load_siblings_doc(namespace=namespace)
    if live:
        return live
    return closed_doc_from_deals(rows, stamp=stamp)
