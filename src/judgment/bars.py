"""CSV bar loaders for gold_state. Clock: broker wall → UTC via NEW_YORK_PLUS_7."""

from __future__ import annotations

import csv
import os
import shutil
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.components.ultimate_book.primitives import Bar, atr14
from src.utils.broker_clock import NEW_YORK_PLUS_7, broker_naive_to_utc

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class StampedBar:
    broker_naive: datetime
    utc: datetime
    bar: Bar
    source_path: str



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
    "bars_since_low", "candles_elapsed", "closed_orig_stop_count", "bars_in_hand", "bars_closed",
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
    if name in {"m15_max_lag_hours", "h4_max_lag_hours", "d1_max_lag_hours", "d1_prior_max_lag_days"}:
        return _named_pairs(card, _SECOND_FIELDS)
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


def _parse_broker_time(raw: str) -> datetime:
    text = raw.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"unparseable bar time: {raw!r}")


def _parse_iso_utc(raw: str) -> datetime:
    text = (raw or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _load_native_d1_npz(path: Path, *, limit: int | None = None) -> list[StampedBar]:
    """D1 OHLC from a period-16408 native bar archive. Not a tick file."""
    import numpy as np

    if path.is_relative_to(REPO_ROOT):
        rel = path.relative_to(REPO_ROOT).as_posix()
    else:
        rel = Path(path).as_posix()
    archive = np.load(path)
    broker = archive["broker_time"]
    out: list[StampedBar] = []
    n = len(broker) if limit is None else min(len(broker), limit)
    for i in range(n):
        naive = datetime.fromtimestamp(int(broker[i]), timezone.utc).replace(tzinfo=None)
        out.append(
            StampedBar(
                broker_naive=naive,
                utc=broker_naive_to_utc(naive, NEW_YORK_PLUS_7),
                bar=Bar(
                    o=float(archive["o"][i]),
                    h=float(archive["h"][i]),
                    l=float(archive["l"][i]),
                    c=float(archive["c"][i]),
                    v=float(archive["v"][i]),
                ),
                source_path=rel,
            )
        )
    return out


def load_ohlc_csv(path: Path, *, limit: int | None = None) -> list[StampedBar]:
    if not path.is_file():
        return []
    if path.suffix.lower() == ".npz":
        return _load_native_d1_npz(path, limit=limit)
    if path.is_relative_to(REPO_ROOT):
        rel = path.relative_to(REPO_ROOT).as_posix()
    else:
        rel = Path(path).as_posix()
    out: list[StampedBar] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            if row.get("time_utc"):
                # Challenge-true FTMO export: time_utc already corrected (−3h).
                # Do not run NY+7 on it.
                utc = _parse_iso_utc(row["time_utc"])
                labeled = (row.get("time_server_labeled") or "").strip()
                if labeled:
                    naive = _parse_iso_utc(labeled).replace(tzinfo=None)
                else:
                    naive = utc.replace(tzinfo=None) + timedelta(hours=3)
            else:
                naive = _parse_broker_time(row["time"])
                utc = broker_naive_to_utc(naive, NEW_YORK_PLUS_7)
            out.append(
                StampedBar(
                    broker_naive=naive,
                    utc=utc,
                    bar=Bar(
                        o=float(row["open"]),
                        h=float(row["high"]),
                        l=float(row["low"]),
                        c=float(row["close"]),
                        v=float(row.get("volume") or row.get("tick_volume") or 0.0),
                    ),
                    source_path=rel,
                )
            )
    return out


def last_closed_at_or_before(rows: list[StampedBar], as_of_utc: datetime) -> int | None:
    if not rows:
        return None
    as_of = as_of_utc.astimezone(timezone.utc)
    lo, hi, found = 0, len(rows) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if rows[mid].utc <= as_of:
            found = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return found


# Names other modules still import. The live snap does not read them.
_MAX_LAG = {
    "M1": timedelta(hours=4),
    "M5": timedelta(hours=6),
    "M15": timedelta(hours=12),
    "H1": timedelta(hours=24),
    "H4": timedelta(hours=36),
    "D1": timedelta(days=5),
}

_MODEL = "jev-1.13.0"
_UNSET = " An empty score leaves it unset. A tie leaves it unset. An error leaves it unset."
_LAG_LOCK = threading.Lock()
_LAG_CACHE: dict[tuple, dict[str, Any]] = {}
_LAG_SPOTS = (
    "m15_lookback",
    "m15_max_lag_hours",
    "h4_lookback",
    "h4_max_lag_hours",
    "d1_lookback",
    "d1_max_lag_hours",
    "d1_prior_max_lag_days",
)
_LAG_TEXT = {
    "m15_lookback": "The score you return is how many M15 closes the trend distance uses.",
    "m15_max_lag_hours": "The score you return is how many seconds an M15 close may lag the clock before the tape is missing.",
    "h4_lookback": "The score you return is how many H4 closes the trend distance uses.",
    "h4_max_lag_hours": "The score you return is how many seconds an H4 close may lag the clock before the tape is missing.",
    "d1_lookback": "The score you return is how many D1 closes the trend distance uses.",
    "d1_max_lag_hours": "The score you return is how many seconds a D1 close may lag the clock before the tape is missing.",
    "d1_prior_max_lag_days": "The score you return is how many seconds the prior daily bar may lag the clock before those levels are missing.",
}
_TF_LOOKBACK = {"M15": "m15_lookback", "H4": "h4_lookback", "D1": "d1_lookback"}
_TF_LAG = {"M15": "m15_max_lag_hours", "H4": "h4_max_lag_hours", "D1": "d1_max_lag_hours"}


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _whole(value: Any) -> int | None:
    number = _finite(value)
    if number is None or number <= 0 or number != int(number):
        return None
    return int(number)


def _lag_card(rows: list, as_of: datetime, idx: int) -> dict[str, Any]:
    """Second spans and bar counts already measured on this tape. No invented hour."""

    card: dict[str, Any] = {}
    try:
        card["bars_in_hand"] = float(len(rows))
        card["bars_closed"] = float(idx + 1)
    except Exception:
        return card
    second = as_of.second + as_of.microsecond / 1000000.0
    card["seconds_until_cycle"] = 60.0 - second
    try:
        since = _finite((as_of - rows[idx].utc).total_seconds())
        if since is not None:
            card["seconds_since_last_close"] = since
    except Exception:
        pass
    if idx >= 1:
        try:
            span = _finite((rows[idx].utc - rows[idx - 1].utc).total_seconds())
            if span is not None:
                card["seconds_between_closes"] = span
            prior = _finite((as_of - rows[idx - 1].utc).total_seconds())
            if prior is not None:
                card["seconds_since_prior_close"] = prior
        except Exception:
            pass
    return card


def _lag_key(as_of: datetime, card: dict | None = None) -> tuple:
    stamp = as_of.astimezone(timezone.utc).replace(second=0, microsecond=0)
    facts = card if isinstance(card, dict) else {}
    packed = tuple(
        sorted(
            (key, facts.get(key))
            for key in (
                "bars_in_hand",
                "bars_closed",
                "seconds_until_cycle",
                "seconds_since_last_close",
                "seconds_between_closes",
                "seconds_since_prior_close",
            )
        )
    )
    return (stamp.isoformat(), packed)


def _lag_post(as_of: datetime, card: dict | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {spot: None for spot in _LAG_SPOTS}
    source = dict(card) if isinstance(card, dict) else {}
    if "seconds_until_cycle" not in source:
        second = as_of.second + as_of.microsecond / 1000000.0
        source["seconds_until_cycle"] = 60.0 - second
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import append_outcome, prior_outcomes, returned_number
    except Exception:
        return out
    questions: dict[str, Any] = {}
    _bind_card(source)
    try:
        for spot in _LAG_SPOTS:
            block = _amount_block(spot, _LAG_TEXT[spot] + _UNSET, source)
            if isinstance(block, dict) and block:
                questions.update(block)
    except Exception:
        questions = {}
    finally:
        _bind_card(None)
    if not questions:
        return out
    state: dict[str, Any] = {
        "sleeve": "bars.tf_snap",
        "as_of_utc": as_of.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    state.update(source)
    try:
        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []
    try:
        receipt = evaluate(state, questions=questions, model=_MODEL, merge_sleeve=False)
    except Exception:
        return out
    if not isinstance(receipt, dict) or not receipt.get("ok"):
        return out
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    for spot in _LAG_SPOTS:
        if spot not in questions:
            continue
        number = returned_number(answers.get(spot))
        out[spot] = number
        try:
            append_outcome(spot, number, state, error=None if number is not None else "empty")
        except Exception:
            pass
    return out


def _lag_ask(as_of: datetime, card: dict | None = None) -> dict[str, Any]:
    """One pack for this clock minute and these tape facts. The next minute drops it."""

    key = _lag_key(as_of, card)
    with _LAG_LOCK:
        hit = _LAG_CACHE.get(key)
    if hit is not None:
        return dict(hit)
    pack = _lag_post(as_of, card)
    with _LAG_LOCK:
        for old in list(_LAG_CACHE):
            if old != key:
                _LAG_CACHE.pop(old, None)
        _LAG_CACHE[key] = pack
    return dict(pack)


def tf_snap(rows: list[StampedBar], as_of_utc: datetime, tf: str, *, lookback: int | None = None) -> dict | None:
    del lookback
    idx = last_closed_at_or_before(rows, as_of_utc)
    if idx is None:
        return None
    as_of = as_of_utc.astimezone(timezone.utc)
    lag = as_of - rows[idx].utc
    card = _lag_card(rows, as_of, idx)
    pack = _lag_ask(as_of, card)
    lag_spot = _TF_LAG.get(tf)
    seconds = _finite(pack.get(lag_spot)) if lag_spot else None
    if seconds is None or seconds <= 0 or lag.total_seconds() > seconds:
        return None
    bars = [r.bar for r in rows[: idx + 1]]
    last = rows[idx]
    atr = atr14(bars, idx) if idx >= 14 else None
    lookback_n = _whole(pack.get(_TF_LOOKBACK[tf])) if tf in _TF_LOOKBACK else None
    close_vs = None
    if atr and atr > 0 and lookback_n is not None and idx >= lookback_n:
        close_vs = (bars[idx].c - bars[idx - lookback_n].c) / atr
    trend = None
    if close_vs is not None:
        from .state_choices import LEGACY, trend_choice

        chosen = trend_choice(close_vs)
        if chosen is not LEGACY:
            trend = chosen
    return {
        "tf": tf,
        "last_close": last.bar.c,
        "last_range": last.bar.h - last.bar.l,
        "atr14": atr if atr and atr > 0 else None,
        "close_vs_close_n_atr": close_vs,
        "trend": trend,
        "bars_available": idx + 1,
        "source_path": last.source_path,
        "last_utc": last.utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_broker": last.broker_naive.strftime("%Y-%m-%d %H:%M:%S"),
    }


def prior_day_levels(d1: list[StampedBar], as_of_utc: datetime) -> tuple[float | None, float | None]:
    idx = last_closed_at_or_before(d1, as_of_utc)
    if idx is None or idx < 1:
        return None, None
    as_of = as_of_utc.astimezone(timezone.utc)
    card = _lag_card(d1, as_of, idx)
    seconds = _finite(_lag_ask(as_of, card).get("d1_prior_max_lag_days"))
    if seconds is None or seconds <= 0 or (as_of - d1[idx].utc).total_seconds() > seconds:
        return None, None
    prev = d1[idx - 1].bar
    return prev.h, prev.l


CHALLENGE_BAR_DIR = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917"
)
CHALLENGE_BAR_MULTI_DIR = CHALLENGE_BAR_DIR / "multi"
NATIVE_D1_DIR = REPO_ROOT / "judgment" / "astra" / "lab" / "native_bars_normalized001"

# redacted_account 2026-09-17 drop. XAU parent; peers + these under challenge_shadow_bars/multi/.
# File stems: US30_cash / UK100_cash. time_utc already −3h. No D1 for non-XAU.
# USDJPY is peer-of-XAU (PRIORITY). Pull Challenge-true M15+H4 beside multi/.
# Never invent DXY / yields / OB. April data/historical is never Challenge tape.
MULTI_SYMBOL_PRIORITY = ("USDJPY", "EURUSD", "GBPUSD", "BTCUSD", "EURGBP", "US30", "UK100", "ETHUSD")
MULTI_SYMBOL_OPTIONAL = ()
XAU_PEER_SYMBOLS = ("USDJPY",)
_FILE_STEM = {"US30": "US30_cash", "UK100": "UK100_cash"}
_STEM_TO_SYMBOL = {"US30_cash": "US30", "UK100_cash": "UK100", "US30.cash": "US30", "UK100.cash": "UK100"}
_BOX_MULTI = Path("/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars/multi")
_TF_KEYS = frozenset({"m15", "h4", "d1"})
_TF_SUFFIX = {"m15": "M15", "h4": "H4", "d1": "D1"}


def normalize_symbol(symbol: str | None) -> str:
    raw = (symbol or "XAUUSD").strip().upper().replace("/", "").replace(".", "_")
    aliases = {"XAU": "XAUUSD", "GOLD": "XAUUSD", "US30_CASH": "US30", "UK100_CASH": "UK100"}
    return aliases.get(raw, raw)


def file_stem_for(symbol: str | None) -> str:
    """On-disk stem. US30.cash / UK100.cash land as US30_cash / UK100_cash."""
    return _FILE_STEM.get(normalize_symbol(symbol), normalize_symbol(symbol))


def symbol_from_stem(stem: str) -> str:
    return _STEM_TO_SYMBOL.get(stem, stem)


def _candidate_stems(symbol: str) -> list[str]:
    sym = normalize_symbol(symbol)
    stems = [file_stem_for(sym), sym]
    if sym == "US30":
        stems.extend(["US30_cash", "US30.cash", "US30"])
    elif sym == "UK100":
        stems.extend(["UK100_cash", "UK100.cash", "UK100"])
    out: list[str] = []
    seen: set[str] = set()
    for stem in stems:
        if stem not in seen:
            seen.add(stem)
            out.append(stem)
    return out


def challenge_search_dirs() -> list[Path]:
    """Known Challenge-true locations. April data/historical is never a member."""
    dirs: list[Path] = []
    extra = (os.environ.get("GTOS_CHALLENGE_BAR_MULTI") or "").strip()
    if extra:
        dirs.append(Path(extra))
    dirs.extend(
        [
            CHALLENGE_BAR_DIR,
            CHALLENGE_BAR_MULTI_DIR,
            REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_bars" / "multi",
            REPO_ROOT
            / "pipeline_state"
            / "ultimate_book"
            / "operator"
            / "judgment"
            / "state"
            / "_fable_bar_pull_20260917"
            / "multi",
            _BOX_MULTI,
            Path("/workspace/gtos/fable_joint_pull_20260917/challenge_shadow_bars"),
        ]
    )
    seen: set[str] = set()
    out: list[Path] = []
    for path in dirs:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def _default_missing_path(symbol: str, tf_suffix: str) -> Path:
    stem = file_stem_for(symbol)
    if normalize_symbol(symbol) == "XAUUSD":
        return CHALLENGE_BAR_DIR / f"{stem}_{tf_suffix}.csv"
    return CHALLENGE_BAR_MULTI_DIR / f"{stem}_{tf_suffix}.csv"


def _native_d1_stems(symbol: str) -> list[str]:
    raw = (symbol or "").strip()
    stems = [raw, raw.replace(".", "_"), * _candidate_stems(symbol)]
    out: list[str] = []
    seen: set[str] = set()
    for stem in stems:
        if stem and stem not in seen:
            seen.add(stem)
            out.append(stem)
    return out


def resolve_challenge_tf(symbol: str, tf: str) -> Path:
    """First existing series for this symbol/TF. Missing path is the landing slot, not April."""
    tf_key = tf.lower()
    suffix = _TF_SUFFIX.get(tf_key, tf.upper())
    for directory in challenge_search_dirs():
        for stem in _candidate_stems(symbol):
            path = directory / f"{stem}_{suffix}.csv"
            if path.is_file():
                return path
    if suffix == "D1":
        for stem in _native_d1_stems(symbol):
            path = NATIVE_D1_DIR / f"{stem}_16408.npz"
            if path.is_file():
                return path
    return _default_missing_path(symbol, suffix)


def challenge_symbol_paths(symbol: str = "XAUUSD") -> dict[str, Path]:
    """Challenge-true FTMO 0 tape paths. Missing files stay missing."""
    return {
        "m15": resolve_challenge_tf(symbol, "M15"),
        "h4": resolve_challenge_tf(symbol, "H4"),
        "d1": resolve_challenge_tf(symbol, "D1"),
    }


def challenge_tape_present(symbol: str) -> bool:
    path = resolve_challenge_tf(symbol, "M15")
    return path.is_file()


def challenge_gold_paths() -> dict[str, Path]:
    """XAU alias. Do not use April repo M15 here."""
    return challenge_symbol_paths("XAUUSD")


def landed_challenge_symbols() -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for directory in challenge_search_dirs():
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*_M15.csv")):
            stem = path.name[: -len("_M15.csv")]
            sym = normalize_symbol(symbol_from_stem(stem))
            if sym not in seen:
                seen.add(sym)
                found.append(sym)
    return found


# Challenge-true peer tape starts with the XAU drop (2026-09-17) and the
# 2026-09-18 FX pull (through ~03:00Z). April historical last-prints fail this.
CHALLENGE_PEER_MIN_LAST_UTC = datetime(2026, 9, 17, tzinfo=timezone.utc)


def admit_challenge_peer_csv(path: Path) -> dict:
    """Refuse April / broker-naive exports. Challenge peers carry time_utc = server−3h."""
    if not path.is_file():
        return {"ok": False, "reason": "missing", "path": str(path)}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        if "time_utc" not in fields:
            return {
                "ok": False,
                "reason": "no_time_utc_column_april_or_broker_naive",
                "path": str(path),
            }
        first = last = None
        n = 0
        for row in reader:
            n += 1
            if first is None:
                first = row
            last = row
    if last is None:
        return {"ok": False, "reason": "empty", "path": str(path)}
    try:
        last_utc = _parse_iso_utc(str(last.get("time_utc") or ""))
    except (TypeError, ValueError):
        return {"ok": False, "reason": "unparseable_time_utc", "path": str(path)}
    if last_utc < CHALLENGE_PEER_MIN_LAST_UTC:
        return {
            "ok": False,
            "reason": "last_utc_before_challenge_era",
            "last_utc": last_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": str(path),
        }
    labeled = str(last.get("time_server_labeled") or "").strip()
    offset_ok = None
    if labeled:
        hours = (_parse_iso_utc(labeled) - last_utc).total_seconds() / 3600.0
        offset_ok = abs(hours - 3.0) < 0.15
        if not offset_ok:
            return {
                "ok": False,
                "reason": "server_offset_not_minus_3h",
                "offset_hours": round(hours, 4),
                "path": str(path),
            }
    first_utc = None
    if first and first.get("time_utc"):
        try:
            first_utc = _parse_iso_utc(str(first["time_utc"]))
        except (TypeError, ValueError):
            first_utc = None
    return {
        "ok": True,
        "n": n,
        "first_utc": first_utc.strftime("%Y-%m-%dT%H:%M:%SZ") if first_utc else None,
        "last_utc": last_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "offset_ok": offset_ok,
        "path": str(path),
    }


def copy_multi_csvs_if_present(src: Path | None = None) -> dict:
    """Copy box/VPS multi CSVs into the lab landing dir. Never invent bars.

    April ``exports/multi_instrument`` / ``data/historical*`` fail admit
    (no ``time_utc``, last print in April). Chair-claimed VPS files that
    are not on this VM stay uncopied.
    """
    sources = []
    if src is not None:
        sources.append(Path(src))
    extra = (os.environ.get("GTOS_CHALLENGE_BAR_MULTI") or "").strip()
    if extra:
        sources.append(Path(extra))
    sources.extend(
        [
            _BOX_MULTI,
            REPO_ROOT
            / "pipeline_state"
            / "ultimate_book"
            / "operator"
            / "judgment"
            / "state"
            / "_fable_bar_pull_20260917"
            / "multi",
        ]
    )
    dest = CHALLENGE_BAR_MULTI_DIR
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    rejected: list[dict] = []
    used = None
    for directory in sources:
        if not directory.is_dir():
            continue
        csvs = sorted(directory.glob("*_M15.csv")) + sorted(directory.glob("*_H4.csv"))
        if not csvs:
            continue
        used = str(directory)
        for path in csvs:
            admit = admit_challenge_peer_csv(path)
            if not admit.get("ok"):
                rejected.append({"name": path.name, "reason": admit.get("reason")})
                continue
            target = dest / path.name
            if path.resolve() == target.resolve():
                continue
            shutil.copy2(path, target)
            copied.append(path.name)
        for extra_name in ("pull_meta.json", "README.md"):
            extra_path = directory / extra_name
            if extra_path.is_file() and copied:
                shutil.copy2(extra_path, dest / extra_name)
        break
    return {
        "src": used,
        "dest": str(dest.relative_to(REPO_ROOT)) if dest.is_relative_to(REPO_ROOT) else str(dest),
        "n_copied": len(copied),
        "copied": copied,
        "n_rejected": len(rejected),
        "rejected": rejected,
        "invented": False,
        "april_historical_used": False,
    }


def load_all_landed_challenge_books() -> dict[str, dict[str, list[StampedBar]]]:
    return {sym: load_challenge_books(symbol=sym) for sym in landed_challenge_symbols()}


def default_gold_paths() -> dict[str, Path]:
    """April 2026 historical pack for G-2W lab. Challenge scoring uses challenge_gold_paths."""
    h2026 = REPO_ROOT / "data" / "historical_2026"
    hist = REPO_ROOT / "data" / "historical"
    m15 = h2026 / "XAUUSD_M15.csv"
    if not m15.is_file():
        m15 = hist / "XAUUSD_M15.csv"
    h4 = h2026 / "XAUUSD_H4.csv"
    if not h4.is_file():
        h4 = hist / "XAUUSD_H4.csv"
    d1 = h2026 / "XAUUSD_D1.csv"
    if not d1.is_file():
        d1 = hist / "XAUUSD_D1.csv"
    return {"m15": m15, "h4": h4, "d1": d1}


def load_gold_books(paths: dict[str, Path] | None = None) -> dict[str, list[StampedBar]]:
    chosen = paths or default_gold_paths()
    return {tf: load_ohlc_csv(path) for tf, path in chosen.items()}


def load_challenge_books(symbol: str = "XAUUSD") -> dict[str, list[StampedBar]]:
    return load_gold_books(challenge_symbol_paths(symbol))


def _is_single_tf_cache(cache: dict) -> bool:
    if not cache:
        return True
    keys = {str(k).lower() for k in cache}
    if keys & _TF_KEYS:
        return True
    return False


def books_for_symbol(
    symbol: str,
    cache: dict | None = None,
) -> dict[str, list[StampedBar]] | None:
    """Return M15/H4/D1 for this symbol. Never substitute XAU for another pair."""
    sym = normalize_symbol(symbol)
    if cache is None:
        if not challenge_tape_present(sym):
            return None
        return load_challenge_books(symbol=sym)
    if _is_single_tf_cache(cache):
        if sym == "XAUUSD":
            return cache
        if not challenge_tape_present(sym):
            return None
        return load_challenge_books(symbol=sym)
    if sym in cache:
        return cache[sym]
    if not challenge_tape_present(sym):
        cache[sym] = None
        return None
    loaded = load_challenge_books(symbol=sym)
    cache[sym] = loaded
    return loaded
