"""Spot-exact Choices for sleeve conditions.

Each spot is one Choice. The alternatives are the two sides of that exact
condition: condition_true and condition_false. The unique highest probability
is the decision. Empty, tie, HTTP, missing key, and calls-off leave the spot
as None. None is not condition_true and does not restore a measured boolean.

One ask() is one POST for every spot on that candidate. Decisive answers are
cached by sleeve, symbol, bar, and measured fact. The cache key is those
facts. It changes when they change. This module does not send and does not
flatten.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import sys
import threading
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

MODEL = "jev-1.13.0"
NAMESPACE = "operator"
LOGIN = 0
_SIDES = ("condition_true", "condition_false")
_CLOCK = {
    "seconds_from_clock",
    "seconds_until_cycle",
    "cycle_wait",
    "prior_outcomes",
    "as_of_utc",
    "ts",
}
_UNSET = (
    " An empty score leaves it unset. A tie leaves it unset. An error leaves it unset."
)
_WHOLE = (
    " Choose one of these whole levels from the card. "
    "An empty answer, a tie, or an error leaves it unset."
)
_WHOLE_UNITS = frozenset({"count", "hour", "minute"})

_LOCK = threading.Lock()
_CACHE: dict[str, dict[str, str | None]] = {}
_PACKS: dict[str, dict[str, Any]] = {}
_DISK_LOADED = False


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def unique_highest(probabilities: Mapping[str, Any]) -> str | None:
    """Unique argmax over the two sides. A tie or a missing side is None.

    A missing probability is not zero. An empty map is not a decision.
    """
    if not isinstance(probabilities, Mapping) or not probabilities:
        return None
    best: str | None = None
    best_p: float | None = None
    tied = False
    seen = False
    for name in _SIDES:
        if name not in probabilities:
            continue
        raw = probabilities.get(name)
        if raw is None or isinstance(raw, bool):
            continue
        number = _finite(raw)
        if number is None:
            continue
        seen = True
        if best_p is None or number > best_p:
            best = name
            best_p = number
            tied = False
        elif number == best_p:
            tied = True
    if not seen or tied or best is None:
        return None
    return best


def all_false(sides: Mapping[str, str | None]) -> bool:
    """True only when every spot's unique highest is condition_false.

    None is not condition_false, so an unanswered spot does not pass and does
    not restore the measured boolean.
    """
    if not sides:
        return False
    return all(side == "condition_false" for side in sides.values())


def bar_id(decision_day, n, bar_time=None, bar_times=None) -> str:
    stamp = bar_time
    if stamp is None and bar_times:
        try:
            stamp = bar_times[-1]
        except Exception:
            stamp = None
    return f"{decision_day}|{n}|{stamp}"


def _repo_root() -> Path:
    # sleeves -> ultimate_book -> components -> src -> repo
    return Path(__file__).resolve().parents[4]


def _receipt_dir() -> Path:
    return (
        _repo_root()
        / "pipeline_state"
        / "ultimate_book"
        / NAMESPACE
        / "judgment"
    )


def _client():
    for name in ("src.judgment.jev_client", "judgment.jev_client"):
        try:
            return importlib.import_module(name)
        except ImportError:
            continue
    repo = str(_repo_root())
    if repo not in sys.path:
        sys.path.insert(0, repo)
    return importlib.import_module("src.judgment.jev_client")


def _clean(raw: str | None) -> str | None:
    if not raw:
        return None
    return str(raw).replace("jev_absent", "unanswered")


def _cache_token(sleeve: str, symbol: str, bar: str, spots: Mapping[str, Mapping[str, Any]]) -> str:
    payload = {
        "sleeve": sleeve,
        "symbol": symbol,
        "bar": bar,
        "spots": [
            [name, str(spots[name].get("condition", "")), bool(spots[name].get("measured"))]
            for name in spots
        ],
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_disk() -> None:
    global _DISK_LOADED
    if _DISK_LOADED:
        return
    _DISK_LOADED = True
    path = _receipt_dir() / "sleeve_spot_cache.json"
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(blob, dict):
        return
    for key, sides in blob.items():
        if isinstance(sides, dict) and sides and all(v in _SIDES for v in sides.values()):
            _CACHE[str(key)] = {str(k): str(v) for k, v in sides.items()}


def _store_disk(token: str, sides: dict[str, str | None]) -> None:
    if any(v not in _SIDES for v in sides.values()):
        return
    path = _receipt_dir() / "sleeve_spot_cache.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            blob = {}
        if not isinstance(blob, dict):
            blob = {}
        blob[token] = sides
        path.write_text(json.dumps(blob, sort_keys=True), encoding="utf-8")
    except Exception:
        return


def _append_receipt(row: dict[str, Any]) -> None:
    try:
        path = _receipt_dir() / "sleeve_spot_choices.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        return


def _questions(spots: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, spec in spots.items():
        condition = str(spec.get("condition", "")).strip()
        measured = bool(spec.get("measured"))
        out[name] = {
            "type": "choice",
            "instructions": (
                f"Condition: {condition}. "
                f"Measured fact for this condition is {measured}. "
                "The alternatives are the two sides of this exact condition. "
                "condition_true means the condition holds. "
                "condition_false means the condition does not hold."
            ),
            "criteria": {
                "condition_true": f"The condition holds. {condition}",
                "condition_false": f"The condition does not hold. {condition}",
            },
        }
    return out


def _deadline(state: Mapping[str, Any]) -> float | None:
    """Seconds until this state expires. No positive expiry means no timeout."""

    found: list[float] = []
    for key in ("seconds_from_clock", "seconds_until_cycle", "cycle_wait"):
        number = _finite(state.get(key))
        if number is not None and number > 0:
            found.append(number)
    if found:
        return min(found)
    try:
        from src.components.ultimate_book.launcher_facts import ask_deadline_seconds

        extra = _finite(ask_deadline_seconds())
    except Exception:
        return None
    if extra is not None and extra > 0:
        return extra
    return None


def _stamp(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    sent = dict(state)
    if _finite(sent.get("seconds_from_clock")) is None:
        wait = _deadline(sent)
        if wait is not None:
            sent["seconds_from_clock"] = wait
    rows = []
    for spot, block in questions.items():
        if not isinstance(block, dict) or str(block.get("type") or "").lower() != "score":
            continue
        pending = amount_question.pending.get(str(spot))
        if not pending:
            continue
        for label, value in pending:
            rows.append({"spot": str(spot), "label": label, "value": value})
    if rows:
        sent["score_anchors"] = rows
    return sent


def _http(state: Mapping[str, Any], questions: Mapping[str, Any]) -> tuple[dict[str, Any], str | None, dict[str, Any]]:
    """One POST. Returns answers, error, and a receipt fragment. No key in the fragment."""

    client = _client()
    meta: dict[str, Any] = {"model": MODEL}
    if not questions:
        return {}, "no_questions", meta
    if not client.calls_enabled():
        return {}, "calls_off", meta
    key, source = client.resolve_key()
    meta["key_source"] = source
    if not key:
        return {}, "key_missing", meta
    meta["key_fingerprint"] = client.key_fingerprint(key)
    sent = _stamp(state, questions)
    payload = {"state": sent, "model": MODEL, "questions": dict(questions)}
    req = urllib.request.Request(
        client.API_URL,
        data=json.dumps(payload, default=str).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "gtos-sleeve-spot/1",
        },
    )
    wait = _finite(sent.get("seconds_from_clock"))
    try:
        if wait is not None and wait > 0:
            handle = urllib.request.urlopen(req, timeout=wait)
        else:
            handle = urllib.request.urlopen(req)
        with handle as resp:
            body = json.loads(resp.read().decode("utf-8"))
            meta["http_status"] = getattr(resp, "status", None)
    except urllib.error.HTTPError as exc:
        meta["http_status"] = exc.code
        try:
            raw = exc.read()
        except Exception:
            raw = b""
        if isinstance(raw, bytes):
            meta["detail"] = raw.decode("utf-8", errors="replace")
        else:
            meta["detail"] = "" if raw is None else str(raw)
        return {}, _clean(f"http_{exc.code}"), meta
    except Exception as exc:  # noqa: BLE001 — a sleeve must not raise into the book
        return {}, _clean(type(exc).__name__), meta
    if not isinstance(body, dict):
        return {}, "probabilities_missing", meta
    answers = body.get("answers")
    if not isinstance(answers, dict):
        return {}, "probabilities_missing", meta
    reported = body.get("model")
    if isinstance(reported, str) and reported.strip():
        meta["model"] = reported
    return answers, None, meta


def _pack_key(state: Mapping[str, Any], questions: Mapping[str, Any]) -> str:
    slim = {key: state[key] for key in state if key not in _CLOCK}
    text = {}
    for qid, spec in questions.items():
        if isinstance(spec, Mapping):
            criteria = spec.get("criteria")
            names = list(criteria) if isinstance(criteria, (list, tuple, Mapping)) else []
            text[str(qid)] = str(spec.get("instructions", "")) + "|" + ",".join(str(name) for name in names)
        else:
            text[str(qid)] = ""
    raw = json.dumps({"state": slim, "questions": text}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _ohlc(bar: Any) -> tuple[float, float, float, float] | None:
    if bar is None:
        return None
    if isinstance(bar, Mapping):
        raw = (bar.get("open", bar.get("o")), bar.get("high", bar.get("h")), bar.get("low", bar.get("l")), bar.get("close", bar.get("c")))
    else:
        raw = (getattr(bar, "o", None), getattr(bar, "h", None), getattr(bar, "l", None), getattr(bar, "c", None))
    numbers = tuple(_finite(item) for item in raw)
    if any(item is None for item in numbers):
        return None
    return numbers  # type: ignore[return-value]


def levels_of(anchors: Any) -> list[tuple[str, float]] | None:
    """Ordered (label, value) levels. Fewer than two distinct finite values is not a Score."""

    if anchors is None or isinstance(anchors, (str, bytes)):
        return None
    if isinstance(anchors, Mapping):
        raw_items = list(anchors.items())
    else:
        try:
            raw_items = list(anchors)
        except TypeError:
            return None
    found: list[tuple[str, float]] = []
    seen: list[float] = []
    for item in raw_items:
        if isinstance(item, tuple) and len(item) == 2:
            label, raw = item
            number = _finite(raw)
            text = "" if label is None else str(label).strip()
        else:
            number = _finite(item)
            text = "" if number is None else str(number).strip()
        if number is None or not text or number in seen:
            continue
        seen.append(number)
        found.append((text, number))
    found.sort(key=lambda pair: pair[1])
    if len(found) < 2:
        return None
    return found


def value_at(position: Any, anchors: Any) -> float | None:
    """The anchor value at this level position. The position may sit between levels.

    The levels are the ones ``score_question`` posts, including the cap the API
    has already stated. The returned number is that value, in the anchors' unit.
    It is not the level index and it is not a probability.
    """

    from src.judgment.nineteen import _anchor_levels

    levels = _anchor_levels(anchors)
    if not levels:
        return None
    number = _finite(position)
    if number is None:
        return None
    low_index = None
    low_value = None
    for index, pair in enumerate(levels):
        value = pair[1]
        if number < index or number == index:
            if number == index or low_value is None:
                return value
            span = index - low_index
            if not span:
                return low_value
            frac = (number - low_index) / span
            return low_value + (frac * (value - low_value))
        low_index = index
        low_value = value
    return low_value


_COUNT = frozenset({
    "or_bars", "maxbars", "reg_lb", "vol_win", "hist_min", "min_bars", "window",
    "don_lb", "persist_bars", "trend_lb", "atr_window", "scan_from", "scan_span",
    "scan_oldest", "gap_shift", "ac_lag", "slope_bars", "mom_bars", "sma_n",
    "atr_n", "warmup_bars", "horizon_bars", "sma_bars", "atr_bars", "range_bars",
    "ob_lookback", "vol_window", "scan_floor", "session_index", "i0_min",
    "catchup_grace", "trend_lookback", "min_asian_bars", "break_lb", "hist_lb",
    "min_hist", "node_min_count", "min_bin_count", "range_window", "n_box",
    "pct_win", "squeeze_min_count", "atr_lb", "min_vol_count", "sma_fast",
    "sma_slow", "atr_mean_bars", "slope_short_bars", "slope_mid_bars",
    "slope_long_bars", "comp_short_bars", "comp_long_bars", "persist_min_bars",
})
_HOUR = frozenset({
    "or_hour", "break_hour_lo", "break_hour_hi", "decision_hour", "london_start",
    "london_end", "ny_start", "ny_end", "session_hour", "asian_end_hour",
    "entry_lo_hour", "entry_hi_hour", "london_lo", "london_hi",
    "session_asia_end", "session_london_end",
})
_MINUTE = frozenset({"decision_min"})
_FRACTION = frozenset({
    "vol_lo", "vol_hi", "intra_size", "size_mult", "reject_frac", "value_area_frac",
    "bin_atr_frac", "sq_pctl", "vol_low_pctl", "squeeze_q", "rng_low", "rng_high",
})
_AUTOCORR = frozenset({"ac_thr", "ac_floor_sb", "persist_trend", "persist_revert"})
_PRICE = frozenset({"limit_price"})
_DIRECTION = frozenset({"direction"})
_SESSION_INDEX = frozenset({"session_index"})
_SESSION_AFTER = frozenset({"catchup_grace"})
_BEFORE_SESSION = frozenset({"i0_min", "min_asian_bars"})
_WARMUP = frozenset({
    "warmup_bars", "min_bars", "atr_window", "vol_window", "window",
    "hist_min", "min_hist", "vol_win", "or_bars", "sma_n", "atr_n",
    "sma_bars", "atr_bars", "horizon_bars", "maxbars", "persist_bars",
    "persist_min_bars", "sma_fast", "sma_slow", "atr_mean_bars",
})
_BAR_INDEX = frozenset()
_LOOKBACK = frozenset({
    "trend_lb", "range_bars", "slope_bars", "mom_bars", "trend_lookback",
    "reg_lb", "don_lb", "break_lb", "hist_lb", "atr_lb", "range_window",
    "slope_short_bars", "slope_mid_bars", "slope_long_bars",
    "comp_short_bars", "comp_long_bars",
})
_GAP_FROM = frozenset({"scan_from"})
_GAP_SPAN = frozenset({"scan_span"})
_GAP_SHIFT = frozenset({"gap_shift"})
_GAP_FLOOR = frozenset({"scan_oldest"})
_OB_LOOK = frozenset({"ob_lookback"})
_OB_FLOOR = frozenset({"scan_floor"})
_AC_LAG = frozenset({"ac_lag"})
_BOX = frozenset({"n_box"})
_PRIOR_BARS = frozenset({"pct_win"})
_RATIO_COUNT = frozenset({"squeeze_min_count"})
_ATR_COUNT = frozenset({"min_vol_count"})
_BIN_COUNT = frozenset({"node_min_count", "min_bin_count"})


def _unit(spot: str) -> str:
    name = str(spot)
    if name in _PRICE:
        return "price"
    if name in _HOUR:
        return "hour"
    if name in _MINUTE:
        return "minute"
    if name in _COUNT:
        return "count"
    if name in _FRACTION:
        return "fraction"
    if name in _AUTOCORR:
        return "autocorr"
    if name in _DIRECTION:
        return "direction"
    return "ratio"


def _push(levels: list[tuple[str, float]], label: str, value: Any, *, positive: bool = False) -> None:
    number = _finite(value)
    if number is None:
        return
    if positive and not (number > 0):
        return
    if any(existing == number for _, existing in levels):
        return
    levels.append((label, number))


def _server_parts(stamp: Any) -> tuple[int | None, int | None, str | None]:
    try:
        from ._server_clock import server_day, server_hour_minute

        hour, minute = server_hour_minute(stamp)
        day = server_day(stamp)
    except Exception:
        return None, None, None
    return hour, minute, day


def _count_family(spot: str) -> str:
    name = str(spot)
    if name in _SESSION_INDEX:
        return "session_index"
    if name in _SESSION_AFTER:
        return "session_after"
    if name in _BEFORE_SESSION:
        return "before_session"
    if name in _WARMUP:
        return "warmup"
    if name in _BAR_INDEX:
        return "bar_index"
    if name in _BOX:
        return "box"
    if name in _PRIOR_BARS:
        return "prior_bars"
    if name in _RATIO_COUNT:
        return "ratio_count"
    if name in _ATR_COUNT:
        return "atr_count"
    if name in _BIN_COUNT:
        return "bin_count"
    if name in _GAP_FROM:
        return "gap_from"
    if name in _GAP_SPAN:
        return "gap_span"
    if name in _GAP_SHIFT:
        return "gap_shift"
    if name in _GAP_FLOOR:
        return "gap_floor"
    if name in _OB_LOOK:
        return "ob_look"
    if name in _OB_FLOOR:
        return "ob_floor"
    if name in _AC_LAG:
        return "ac_lag"
    if name in _LOOKBACK:
        return "lookback"
    return "lookback"


def _clock_matches(bars: Any, bar_times: Any) -> bool:
    try:
        return bar_times is not None and bars is not None and len(bar_times) == len(bars)
    except TypeError:
        return False


def _day_start(bars: Any, i: int, bar_times: Any) -> int | None:
    if not _clock_matches(bars, bar_times) or i < 0:
        return None
    _, _, day = _server_parts(bar_times[i])
    if day is None:
        return None
    start = i
    while start > 0:
        _, _, earlier = _server_parts(bar_times[start - 1])
        if earlier != day:
            break
        start -= 1
    return start


def _bar_high(bar: Any) -> float | None:
    try:
        number = float(bar.h)
    except (AttributeError, TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _bar_low(bar: Any) -> float | None:
    try:
        number = float(bar.l)
    except (AttributeError, TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _bar_close(bar: Any) -> float | None:
    try:
        number = float(bar.c)
    except (AttributeError, TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


_STRUCTURE: dict[tuple[int, int], dict[str, list[tuple[str, float]]]] = {}


def _structure(bars: Any, i: int) -> dict[str, list[tuple[str, float]]]:
    """Distances and indexes of swings, gaps, order blocks, and range edges up to i."""

    key = (id(bars), i)
    hit = _STRUCTURE.get(key)
    if hit is not None:
        return hit
    distances: list[tuple[str, float]] = []
    indexes: list[tuple[str, float]] = []
    if i >= 1:
        for k in range(1, i):
            high = _bar_high(bars[k])
            low = _bar_low(bars[k])
            prev_high = _bar_high(bars[k - 1])
            prev_low = _bar_low(bars[k - 1])
            next_high = _bar_high(bars[k + 1])
            next_low = _bar_low(bars[k + 1])
            if None not in (high, prev_high, next_high) and high > prev_high and high > next_high:
                _push(distances, f"swing_high_{k}", i - k, positive=True)
                _push(indexes, f"swing_high_{k}", k)
            if None not in (low, prev_low, next_low) and low < prev_low and low < next_low:
                _push(distances, f"swing_low_{k}", i - k, positive=True)
                _push(indexes, f"swing_low_{k}", k)
        for k in range(i):
            left_high = _bar_high(bars[k])
            left_low = _bar_low(bars[k])
            right_high = _bar_high(bars[k + 1])
            right_low = _bar_low(bars[k + 1])
            right_close = _bar_close(bars[k + 1])
            if None in (left_high, left_low, right_high, right_low):
                continue
            if right_low > left_high or right_high < left_low:
                _push(distances, f"gap_{k + 1}", i - (k + 1), positive=True)
                _push(indexes, f"gap_{k + 1}", k + 1)
            if right_close is not None and (right_close > left_high or right_close < left_low):
                _push(distances, f"order_block_{k}", i - k, positive=True)
                _push(indexes, f"order_block_{k}", k)
        try:
            hi_at = max(range(i + 1), key=lambda k: bars[k].h)
            lo_at = min(range(i + 1), key=lambda k: bars[k].l)
        except Exception:
            hi_at = None
            lo_at = None
        if hi_at is not None:
            _push(distances, "range_high", i - hi_at, positive=True)
            _push(indexes, "range_high", hi_at)
        if lo_at is not None:
            _push(distances, "range_low", i - lo_at, positive=True)
            _push(indexes, "range_low", lo_at)
    built = {"distances": distances, "indexes": indexes}
    _STRUCTURE[key] = built
    return built


def _positive_whole(value: Any) -> float | None:
    number = _finite(value)
    if number is None or number % 1 != 0 or not (number >= 1):
        return None
    return number


def _count_steps(count: float, label: str) -> list[tuple[str, float]]:
    levels: list[tuple[str, float]] = []
    step = 1.0
    while step <= count:
        _push(levels, label + "_" + format(step, "g"), step, positive=True)
        step += 1
    return levels


def _box_widths(structure: Mapping[str, Any], i: int) -> list[tuple[str, float]]:
    """Bars between consecutive structure edges, including the first bar and this bar."""

    points: list[tuple[str, float]] = []
    _push(points, "first_bar", 0)
    _push(points, "decision_bar", i)
    for label, at in structure.get("indexes") or ():
        if at <= i:
            _push(points, str(label), at)
    ordered = sorted(points, key=lambda pair: (pair[1], pair[0]))
    levels: list[tuple[str, float]] = []
    previous = None
    previous_label = None
    for label, at in ordered:
        if previous is not None and at > previous:
            _push(levels, "box_" + str(previous_label) + "_" + str(label), at - previous, positive=True)
        previous = at
        previous_label = label
    return levels


def _width_count(bars: Any, i: int) -> float:
    found = 0.0
    k = 0
    while k <= i:
        high = _bar_high(bars[k])
        low = _bar_low(bars[k])
        if high is not None and low is not None and high > low:
            found += 1
        k += 1
    return found


def _prior_atr_count(bars: Any, i: int) -> float:
    found = 0.0
    k = 1
    while k < i:
        high = _bar_high(bars[k])
        low = _bar_low(bars[k])
        prev = _bar_close(bars[k - 1])
        if high is not None and low is not None and prev is not None:
            span = high - low
            up = abs(high - prev)
            down = abs(low - prev)
            if up > span:
                span = up
            if down > span:
                span = down
            if span > 0:
                found += 1
        k += 1
    return found


def _bins_present(card: Mapping[str, Any]) -> list[tuple[str, float]]:
    count = _positive_whole(card.get("n_bins"))
    if count is None:
        return []
    return _count_steps(count, "bin")


def _session_span(bars: Any, i: int, bar_times: Any) -> tuple[int, int] | None:
    start = _day_start(bars, i, bar_times)
    if start is None or i < start:
        return None
    return start, i - start + 1


def _span_steps(low: float, high: float, label: str) -> list[tuple[str, float]]:
    """Whole amounts from low through high. One value is not a choice."""

    levels: list[tuple[str, float]] = []
    if low != low or high != high or high < low:
        return levels
    step = low
    while step <= high:
        _push(levels, label + "_" + format(step, "g"), step)
        step += 1.0
    return levels


def _range_levels(bounds: Mapping[str, Any] | None, key: str, label: str) -> list[tuple[str, float]]:
    if not isinstance(bounds, Mapping) or key not in bounds:
        return []
    pair = bounds[key]
    return _span_steps(pair[0], pair[1], label)


def _adjacent_gap_indexes(bars: Any, i: int) -> list[float]:
    """Right-bar indexes of adjacent non-overlapping ranges, strictly before i."""

    found: list[float] = []
    if bars is None or i < 2:
        return found
    k = 0
    while k < i - 1:
        left_high = _bar_high(bars[k])
        left_low = _bar_low(bars[k])
        right_high = _bar_high(bars[k + 1])
        right_low = _bar_low(bars[k + 1])
        if (
            left_high is not None
            and left_low is not None
            and right_high is not None
            and right_low is not None
            and (right_low > left_high or right_high < left_low)
        ):
            found.append(float(k + 1))
        k += 1
    return found


def _gap_bounds(bars: Any, i: int | None) -> dict[str, Any] | None:
    """Scan lengths that leave a window, and cover the adjacent gaps when the card has them.

    begin = i - scan_from, stop = max(i - scan_span, scan_oldest). The empty scan is
    begin < stop. The lengths are distances and indexes already on this series.
    """

    if bars is None or i is None or i < 1:
        return None
    gaps = _adjacent_gap_indexes(bars, i)
    if gaps:
        g_far = min(gaps)
        d_far = float(i) - g_far
        if d_far >= 2.0 and g_far >= 2.0:
            return {
                "from": (1.0, d_far),
                "span": (d_far + 1.0, float(i)),
                "oldest": (0.0, g_far - 1.0),
                "mode": "inside",
                "gaps": gaps,
            }
        if d_far >= 2.0 and g_far >= 1.0 and (float(i) - d_far + 1.0) >= 2.0:
            return {
                "from": (1.0, d_far),
                "span": (d_far, float(i)),
                "oldest": (0.0, g_far),
                "mode": "window",
                "gaps": gaps,
            }
        if d_far == 1.0 and i >= 3:
            return {
                "from": (0.0, 1.0),
                "span": (2.0, float(i)),
                "oldest": (0.0, float(i - 2)),
                "mode": "near",
                "gaps": gaps,
            }
        return None
    if i >= 3:
        return {
            "from": (1.0, float(i - 1)),
            "span": (float(i - 1), float(i)),
            "oldest": (0.0, 1.0),
            "mode": "open",
            "gaps": [],
        }
    return None


def _gap_shifts(bars: Any, i: int | None) -> list[tuple[str, float]]:
    """Nearest and farthest shifts where two bars up to i do not overlap."""

    levels: list[tuple[str, float]] = []
    if bars is None or i is None or i < 1:
        return levels
    k = 1
    while k <= i:
        right_high = _bar_high(bars[k])
        right_low = _bar_low(bars[k])
        if right_high is None or right_low is None:
            k += 1
            continue
        nearest = None
        farthest = None
        shift = 1
        while shift <= k:
            left_high = _bar_high(bars[k - shift])
            left_low = _bar_low(bars[k - shift])
            if (
                left_high is not None
                and left_low is not None
                and (right_low > left_high or right_high < left_low)
            ):
                if nearest is None:
                    nearest = float(shift)
                farthest = float(shift)
            shift += 1
        if nearest is not None:
            _push(levels, "near_shift_" + str(k), nearest, positive=True)
        if farthest is not None:
            _push(levels, "far_shift_" + str(k), farthest, positive=True)
        k += 1
    return levels


def _scannable_order_blocks(bars: Any, i: int) -> list[float]:
    found: list[tuple[str, float]] = []
    if bars is None or i < 2:
        return []
    for label, at in _structure(bars, i)["indexes"]:
        if str(label).startswith("order_block_") and at >= 1.0 and at <= float(i - 2):
            _push(found, str(label), at)
    return [value for _, value in found]


def _ob_bounds(bars: Any, i: int | None) -> dict[str, Any] | None:
    """Lookback and floor pairs whose scan still steps, and reach an order block when one is scannable.

    start = max(i - ob_lookback, scan_floor). The loop is empty when start >= i - 2.
    """

    if bars is None or i is None or i < 0:
        return None
    blocks = _scannable_order_blocks(bars, i)
    if blocks:
        oldest = min(blocks)
        if oldest >= 2.0:
            return {
                "look": (float(i) - oldest + 1.0, float(i)),
                "floor": (0.0, oldest - 1.0),
                "mode": "inside",
                "oldest": oldest,
            }
    if i >= 4:
        return {
            "look": (3.0, float(i)),
            "floor": (0.0, float(i - 3)),
            "mode": "open",
            "oldest": None,
        }
    return None


def filtered_session_facts(bars: Any, i: int | None, bar_times: Any) -> dict[str, Any] | None:
    """Hours on this server day, through this bar, with a filtered session of bars.

    The session for an hour is the bars on the decision bar's server day with
    server hour at least that hour. Hours with fewer than three bars are not
    offered as an hour. Fewer than two such hours leaves the hour question unset.
    The entry itself is not one of these hours.
    """

    if not _clock_matches(bars, bar_times) or i is None or i < 0:
        return None
    try:
        count = len(bar_times)
    except TypeError:
        return None
    if i >= count:
        return None
    hour_i, _, day = _server_parts(bar_times[i])
    if day is None or hour_i is None:
        return None
    if i + 1 < count:
        _, _, later_day = _server_parts(bar_times[i + 1])
        if later_day == day:
            return None
    day_hours: list[float] = []
    seen: list[float] = []
    k = 0
    while k <= i:
        hour, _, k_day = _server_parts(bar_times[k])
        if k_day == day and hour is not None:
            day_hours.append(float(hour))
            if hour not in seen and hour <= hour_i:
                seen.append(float(hour))
        k += 1
    sessions: list[tuple[float, float]] = []
    for hour in seen:
        length = 0.0
        for sample in day_hours:
            if sample >= hour:
                length += 1.0
        if length >= 3.0:
            sessions.append((hour, length))
    if len(sessions) < 2:
        return None
    ordered = sorted(sessions, key=lambda pair: pair[0])
    return {"sessions": ordered}


def session_entry_facts(bars: Any, i: int | None, bar_times: Any) -> dict[str, Any] | None:
    """Facts for this bar inside the session on the card. A missing clock stays unset.

    The session is the bars on this server day through this bar. The hour is this
    bar's server hour. The position counts those bars from the day's first bar.
    The range is the session high minus the session low. Time left is the seconds
    from this bar until the next server hour.
    """

    if not _clock_matches(bars, bar_times) or i is None or i < 0:
        return None
    try:
        count = len(bar_times)
    except TypeError:
        return None
    if i >= count or i >= len(bars):
        return None
    start = _day_start(bars, i, bar_times)
    if start is None:
        return None
    hour_i, minute_i, day = _server_parts(bar_times[i])
    if hour_i is None or minute_i is None or day is None:
        return None
    open_hour, _, open_day = _server_parts(bar_times[start])
    if open_hour is None or open_day != day:
        return None
    from ._server_clock import to_server_local

    local = to_server_local(bar_times[i])
    if local is None:
        return None
    boundary = local.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    time_left = (boundary - local).total_seconds()
    if time_left != time_left or time_left < 0:
        return None
    high = None
    low = None
    indexes: list[int] = []
    position = 0.0
    k = start
    while k <= i:
        bar_high = _bar_high(bars[k])
        bar_low = _bar_low(bars[k])
        if bar_high is None or bar_low is None or bar_high < bar_low:
            return None
        high = bar_high if high is None or bar_high > high else high
        low = bar_low if low is None or bar_low < low else low
        indexes.append(k)
        position += 1.0
        k += 1
    if not indexes or indexes[-1] != i or high is None or low is None:
        return None
    hour_position = 0.0
    k = i
    while k >= start:
        hour, _, k_day = _server_parts(bar_times[k])
        if hour != hour_i or k_day != day:
            break
        hour_position += 1.0
        k -= 1
    if not (hour_position >= 1.0) or not (position >= 1.0):
        return None
    return {
        "session_hour": float(hour_i),
        "open_hour": float(open_hour),
        "minute": float(minute_i),
        "position": position,
        "hour_position": hour_position,
        "session_range": high - low,
        "time_left": time_left,
        "indexes": indexes,
    }


def entry_choice(facts: Mapping[str, Any]) -> dict[str, Any]:
    """The entry question. The two sides are this bar and not this bar."""

    told = (
        "Session hour "
        + format(facts["session_hour"], "g")
        + ". The session opened at server hour "
        + format(facts["open_hour"], "g")
        + ". This bar is position "
        + format(facts["position"], "g")
        + " of the session so far, and position "
        + format(facts["hour_position"], "g")
        + " of server hour "
        + format(facts["session_hour"], "g")
        + " (server minute "
        + format(facts["minute"], "g")
        + "). Session range "
        + format(facts["session_range"], "g")
        + ". Time left "
        + format(facts["time_left"], "g")
        + " seconds until the next server hour."
    )
    return {
        "instructions": (
            "Is this bar the sleeve's entry in this session? "
            + told
            + " An empty answer, a tie, or an error is not an entry."
        ),
        "criteria": {
            "this_bar": "This bar is the sleeve's entry in this session. " + told,
            "not_this_bar": "This bar is not the sleeve's entry in this session. " + told,
        },
    }


def structure_notes(bars: Any, i: int | None) -> dict[str, str]:
    """What the scan and the lag are measured from, for the question text."""

    notes = {
        "gap": "The scan lengths are the ones this card can cover.",
        "shift": "The shift is a measured distance between two non-overlapping bars on this card.",
        "lag": "The lag is a count of returns this series can form.",
        "ob": "The lookback and the floor leave the order-block scan a window on this card.",
    }
    if bars is None or i is None or i < 0:
        return notes
    bounds = _gap_bounds(bars, i)
    mode = bounds.get("mode") if isinstance(bounds, dict) else None
    gaps = bounds.get("gaps") if isinstance(bounds, dict) else None
    if mode == "inside" and gaps:
        notes["gap"] = (
            "The scan walks back across the adjacent gaps on this card, from bar "
            + format(min(gaps), "g")
            + " through bar "
            + format(max(gaps), "g")
            + ". Every offered start, reach, and floor keeps the oldest of those gaps inside the window."
        )
    elif mode == "window" and gaps:
        notes["gap"] = (
            "The adjacent gaps on this card run from bar "
            + format(min(gaps), "g")
            + " through bar "
            + format(max(gaps), "g")
            + ". Every offered start, reach, and floor leaves the scan a window, and the reach includes the distance back to the oldest gap."
        )
    elif mode == "near":
        notes["gap"] = (
            "The only adjacent gap on this card is one bar back. "
            "The offered starts are this bar and that gap, and every combination keeps the gap inside the window."
        )
    elif mode == "open":
        notes["gap"] = (
            "This card has no adjacent gap through this bar. "
            "The offered lengths are distances on the series that still leave the scan a window."
        )
    else:
        notes["gap"] = "This card does not have two scan lengths that cover a gap through this bar."
    shifts = _gap_shifts(bars, i)
    if len(shifts) >= 2:
        amounts = [value for _, value in shifts]
        notes["shift"] = (
            "The distances are the measured shifts between non-overlapping bars on this card, from "
            + format(min(amounts), "g")
            + " through "
            + format(max(amounts), "g")
            + "."
        )
    else:
        notes["shift"] = "A shift is posted only when this card has at least two measured gap distances."
    if i >= 2:
        notes["lag"] = (
            "The lag is a count of returns this series can form. "
            "Every offered lag is short enough to be defined on this bar."
        )
    else:
        notes["lag"] = "This series does not have two returns through this bar."
    blocks = _ob_bounds(bars, i)
    if isinstance(blocks, dict) and blocks.get("mode") == "inside":
        notes["ob"] = (
            "The lookback reaches the order blocks on this card and the floor stays behind them. "
            "The oldest scanned block is bar " + format(blocks.get("oldest"), "g") + "."
        )
    elif isinstance(blocks, dict) and blocks.get("mode") == "open":
        notes["ob"] = "The offered lookback and floor leave a window on this series that still steps through a bar."
    else:
        notes["ob"] = "This series does not have an order-block window through this bar."
    return notes


def _indexed(bars: Any, index: Any, facts: Mapping[str, Any] | None) -> int | None:
    if isinstance(index, int) and not isinstance(index, bool) and index >= 0:
        return index
    if isinstance(facts, Mapping):
        raw = _finite(facts.get("bar_index"))
        if raw is not None and raw >= 0:
            return int(raw)
    try:
        count = len(bars)
    except TypeError:
        return None
    if count > 0:
        return count - 1
    return None


def anchors_for(
    spot: str,
    facts: Mapping[str, Any] | None = None,
    *,
    bars: Any = None,
    index: int | None = None,
    bar_times: Any = None,
) -> list[tuple[str, float]]:
    """Levels for this spot, taken from the card. Fewer than two leaves the hop unset."""

    card = facts if isinstance(facts, Mapping) else {}
    i = _indexed(bars, index, card)
    unit = _unit(spot)
    levels: list[tuple[str, float]] = []
    bar = None
    if bars is not None and i is not None:
        try:
            bar = bars[i]
        except Exception:
            bar = None
    ohlc = _ohlc(bar)
    if ohlc is None and card:
        ohlc = _ohlc({
            "open": card.get("open"),
            "high": card.get("high"),
            "low": card.get("low"),
            "close": card.get("close"),
        })
    atr = _finite(card.get("atr"))
    if atr is not None and not (atr > 0):
        atr = None
    if unit == "price" and ohlc is not None:
        open_, high, low, close = ohlc
        _push(levels, "open", open_)
        _push(levels, "high", high)
        _push(levels, "low", low)
        _push(levels, "close", close)
        return levels
    if unit == "ratio" and ohlc is not None:
        open_, high, low, close = ohlc
        span = high - low
        scale = atr if atr is not None else (span if span > 0 else None)
        if scale is not None and scale > 0:
            _push(levels, "range_over_scale", span / scale, positive=True)
            _push(levels, "body_over_scale", abs(close - open_) / scale, positive=True)
            _push(levels, "upper_over_scale", (high - max(open_, close)) / scale, positive=True)
            _push(levels, "lower_over_scale", (min(open_, close) - low) / scale, positive=True)
        if bars is not None and i is not None and i >= 1 and scale is not None and scale > 0:
            prior = _ohlc(bars[i - 1])
            if prior is not None:
                _push(levels, "prior_range_over_scale", (prior[1] - prior[2]) / scale, positive=True)
        return levels
    if unit == "fraction" and ohlc is not None:
        open_, high, low, close = ohlc
        span = high - low
        if span > 0:
            _push(levels, "body_share", abs(close - open_) / span)
            _push(levels, "upper_share", (high - max(open_, close)) / span)
            _push(levels, "lower_share", (min(open_, close) - low) / span)
        if bars is not None and i is not None and i >= 1:
            ranges: list[float] = []
            start = 0
            if bar_times is not None:
                try:
                    same = len(bar_times) == len(bars)
                except TypeError:
                    same = False
                if same:
                    _, _, day = _server_parts(bar_times[i])
                    if day is not None:
                        start = i
                        while start > 0:
                            _, _, earlier = _server_parts(bar_times[start - 1])
                            if earlier != day:
                                break
                            start -= 1
            peak = None
            for k in range(start, i + 1):
                sample = _ohlc(bars[k])
                if sample is None:
                    continue
                width = sample[1] - sample[2]
                if width > 0:
                    ranges.append(width)
                    peak = width if peak is None or width > peak else peak
            if peak is not None and peak > 0:
                for offset, width in enumerate(ranges):
                    _push(levels, f"day_range_share_{offset}", width / peak)
        return levels
    if unit == "direction" and ohlc is not None:
        open_, high, low, close = ohlc
        body = close - open_
        mid = (high + low) / 2.0
        _push(levels, "body_sign", 1.0 if body > 0 else (-1.0 if body < 0 else 0.0))
        _push(levels, "mid_sign", 1.0 if close > mid else (-1.0 if close < mid else 0.0))
        if bars is not None and i is not None and i >= 1:
            prior = _ohlc(bars[i - 1])
            if prior is not None:
                step = close - prior[3]
                _push(levels, "step_sign", 1.0 if step > 0 else (-1.0 if step < 0 else 0.0))
        return levels
    if unit == "count":
        family = _count_family(spot)
        if family == "bin_count":
            return _bins_present(card)
        if bars is None or i is None or i < 0:
            return levels
        structure = _structure(bars, i)
        span = _session_span(bars, i, bar_times)
        if family == "session_index" or family == "session_after":
            return []
        if family == "box":
            return _box_widths(structure, i)
        if family == "prior_bars":
            if i < 1:
                return levels
            return _count_steps(i, "prior_bar")
        if family == "ratio_count":
            return _count_steps(_width_count(bars, i), "width_ratio")
        if family == "atr_count":
            return _count_steps(_prior_atr_count(bars, i), "prior_atr")
        if family == "before_session":
            start = span[0] if span is not None else None
            if start is not None:
                _push(levels, "session_open_index", start)
                for label, at in structure["indexes"]:
                    if at <= start:
                        _push(levels, f"before_{label}", at)
            return levels
        if family == "bar_index":
            _push(levels, "first_bar", 0)
            for label, at in structure["indexes"]:
                if at <= i:
                    _push(levels, label, at)
            return levels
        if family == "warmup":
            step = 1
            while step <= i:
                _push(levels, f"bars_present_{step}", step, positive=True)
                step += 1
            return levels
        if family == "gap_from":
            return _range_levels(_gap_bounds(bars, i), "from", "gap_start")
        if family == "gap_span":
            return _range_levels(_gap_bounds(bars, i), "span", "gap_reach")
        if family == "gap_floor":
            return _range_levels(_gap_bounds(bars, i), "oldest", "gap_floor")
        if family == "gap_shift":
            return _gap_shifts(bars, i)
        if family == "ob_look":
            return _range_levels(_ob_bounds(bars, i), "look", "order_block_reach")
        if family == "ob_floor":
            return _range_levels(_ob_bounds(bars, i), "floor", "order_block_floor")
        if family == "ac_lag":
            if i < 2:
                return levels
            return _count_steps(float(i - 1), "return_lag")
        for label, dist in structure["distances"]:
            if dist <= i:
                _push(levels, label, dist, positive=True)
        return levels
    if unit == "hour" and str(spot) == "session_hour":
        facts_s = filtered_session_facts(bars, i, bar_times)
        if facts_s is None:
            return []
        for hour, length in facts_s["sessions"]:
            _push(
                levels,
                "session_hour_" + format(hour, "g") + "_bars_" + format(length, "g"),
                hour,
            )
        return levels
    if unit in {"hour", "minute"} and bar_times is not None and i is not None:
        try:
            stamps = list(bar_times)
        except TypeError:
            stamps = []
        if bars is not None:
            try:
                limit = len(bars)
            except TypeError:
                limit = len(stamps)
        else:
            limit = len(stamps)
        _, _, day = _server_parts(stamps[i]) if i < len(stamps) else (None, None, None)
        for k, stamp in enumerate(stamps[: limit]):
            if k > i:
                break
            hour, minute, k_day = _server_parts(stamp)
            if day is not None and k_day != day:
                continue
            if unit == "hour":
                _push(levels, f"server_hour_{k}", hour)
            else:
                _push(levels, f"server_minute_{k}", minute)
        return levels
    if unit == "hour":
        _push(levels, "card_hour", card.get("hour"))
        return levels
    if unit == "minute":
        _push(levels, "card_minute", card.get("minute"))
        return levels
    if unit == "autocorr" and bars is not None and i is not None and i >= 2:
        closes: list[float] = []
        for k in range(i + 1):
            sample = _ohlc(bars[k])
            if sample is None:
                closes = []
                break
            closes.append(sample[3])
        if len(closes) >= 3:
            lags = []
            if i >= 1:
                try:
                    hi_at = max(range(i + 1), key=lambda k: bars[k].h)
                    lo_at = min(range(i + 1), key=lambda k: bars[k].l)
                    if i - hi_at > 0:
                        lags.append(i - hi_at)
                    if i - lo_at > 0:
                        lags.append(i - lo_at)
                except Exception:
                    lags = []
            for lag in lags:
                if lag >= len(closes):
                    continue
                left = closes[:-lag]
                right = closes[lag:]
                count = len(left)
                if count < 2 or len(right) != count:
                    continue
                mean_left = sum(left) / count
                mean_right = sum(right) / count
                cov = sum((left[n] - mean_left) * (right[n] - mean_right) for n in range(count))
                var_left = sum((item - mean_left) ** 2 for item in left)
                var_right = sum((item - mean_right) ** 2 for item in right)
                if var_left <= 0 or var_right <= 0:
                    continue
                _push(levels, f"autocorr_lag_{lag}", cov / ((var_left * var_right) ** 0.5))
        return levels
    return levels


def amount_question(spot: str, text: str, anchors: Any) -> dict[str, Any]:
    """One amount from the card. Fewer than two anchors does not post.

    A whole-number quantity is a choice of the card's whole levels. Any other
    amount is a Score. Criteria are label (value). The private anchor key
    stays off this post. The Score level count is the maximum the API has
    already stated.
    """

    if _unit(str(spot)) in _WHOLE_UNITS:
        from src.judgment.jev_questions import whole_levels, whole_question

        levels = whole_levels(anchors)
        built = whole_question(str(spot), str(text).strip() + _WHOLE, anchors)
        body = built.get(str(spot)) if isinstance(built, dict) else None
        if not isinstance(body, dict) or not levels:
            return {}
        amount_question.pending[str(spot)] = list(levels)
        return {str(spot): body}

    from src.judgment.nineteen import _anchor_levels, score_question

    levels = _anchor_levels(anchors)
    built = score_question(str(spot), str(text).strip() + _UNSET, anchors)
    body = built.get(str(spot)) if isinstance(built, dict) else None
    if not isinstance(body, dict) or not levels:
        return {}
    body = dict(body)
    body.pop("_anchor_values", None)
    criteria = body.get("criteria")
    if not isinstance(criteria, list) or len(criteria) != len(levels):
        return {}
    amount_question.pending[str(spot)] = list(levels)
    return {str(spot): body}


amount_question.pending = {}


def score_questions(
    texts: Mapping[str, str],
    *,
    facts: Mapping[str, Any] | None = None,
    bars: Any = None,
    index: int | None = None,
    bar_times: Any = None,
) -> dict[str, Any]:
    """Score questions for one post. A spot with fewer than two anchors is omitted."""

    card = score_questions.card if isinstance(score_questions.card, dict) else {}
    use_facts = facts if facts is not None else card.get("facts")
    use_bars = bars if bars is not None else card.get("bars")
    use_index = index if index is not None else card.get("index")
    use_times = bar_times if bar_times is not None else card.get("bar_times")
    packed: dict[str, Any] = {}
    for spot, text in texts.items():
        anchors = anchors_for(
            str(spot),
            use_facts if isinstance(use_facts, Mapping) else None,
            bars=use_bars,
            index=use_index,
            bar_times=use_times,
        )
        packed.update(amount_question(str(spot), str(text), anchors))
    return packed


score_questions.card = None


def arm_card(
    facts: Mapping[str, Any] | None = None,
    *,
    bars: Any = None,
    index: int | None = None,
    bar_times: Any = None,
) -> None:
    """The card the next score post and read use. A later arm replaces it."""

    score_questions.card = {
        "facts": facts if isinstance(facts, Mapping) else None,
        "bars": bars,
        "index": index,
        "bar_times": bar_times,
    }


def answered_amount(spot: str, block: Any, anchors: Any) -> float | None:
    """The amount this question returned.

    A whole-number question returns the whole level that was chosen. Any other
    amount is the value at the returned level position. Empty, tie, and error
    stay unset.
    """

    if isinstance(block, Mapping) and block.get("tie") is True:
        return None
    if _unit(str(spot)) in _WHOLE_UNITS:
        from src.judgment.jev_questions import chosen_level

        return chosen_level(block, anchors)
    from src.judgment.jev_questions import returned_number

    return value_at(returned_number(block), anchors)


def post_again(evaluate_once, questions: Mapping[str, Any], rebuild) -> Any:
    """Post once. If a refusal names a level cap, post the thinned whole levels once."""

    receipt = evaluate_once(questions)
    if not isinstance(receipt, dict) or receipt.get("ok") or not str(receipt.get("error") or "").startswith("http_"):
        return receipt
    from src.judgment.nineteen import note_score_level_cap

    note_score_level_cap(receipt.get("detail"))
    fresh = rebuild()
    if not isinstance(fresh, dict):
        return receipt

    def width(posted: Mapping[str, Any]) -> int:
        total = 0
        for block in posted.values():
            if not isinstance(block, dict):
                continue
            criteria = block.get("criteria")
            try:
                total += len(criteria)
            except TypeError:
                continue
        return total

    if width(fresh) >= width(questions):
        return receipt
    return evaluate_once(fresh)


def read_number(
    answers: Mapping[str, Any] | None,
    spot: str,
    anchors: Any = None,
) -> float | None:
    """The value on this spot's anchors. A level index is not an amount.

    Empty, tie, and error stay unset. A spot with fewer than two anchors stays unset.
    """

    if not isinstance(answers, Mapping):
        return None
    block = answers.get(spot)
    try:
        from src.judgment.jev_questions import returned_number

        index = returned_number(block)
    except Exception:
        index = None
    if index is None and isinstance(block, Mapping):
        index = _finite(block.get("score"))
        if index is None:
            index = _finite(block.get("value"))
    remembered = answers.get("_anchor_levels")
    if anchors is None and isinstance(remembered, Mapping):
        anchors = remembered.get(str(spot))
    if anchors is None:
        pending = amount_question.pending.get(str(spot))
        card = score_questions.card if isinstance(score_questions.card, dict) else None
        if card is not None:
            anchors = anchors_for(
                str(spot),
                card.get("facts") if isinstance(card.get("facts"), Mapping) else None,
                bars=card.get("bars"),
                index=card.get("index"),
                bar_times=card.get("bar_times"),
            )
        elif pending is not None:
            anchors = pending
    if _unit(str(spot)) in _WHOLE_UNITS:
        return answered_amount(str(spot), block, anchors)
    return value_at(index, anchors)


def read_side(answers: Mapping[str, Any] | None, spot: str, order: tuple[str, ...]) -> str | None:
    """Unique highest side. A tie or an empty block is not a side."""

    block = answers.get(spot) if isinstance(answers, Mapping) else None
    if not isinstance(block, Mapping) or block.get("error"):
        return None
    probs = block.get("probabilities")
    if not isinstance(probs, Mapping) or not probs:
        return None
    try:
        from src.judgment.jev_questions import unique_highest as highest

        picked = highest(probs, order)
    except Exception:
        return None
    if picked in order:
        return str(picked)
    return None


def _thinned_scores(questions: Mapping[str, Any]) -> dict[str, Any] | None:
    """Rebuild Score criteria after a refusal names the API maximum. One rebuild."""

    from src.judgment.nineteen import score_question

    rebuilt: dict[str, Any] = {}
    changed = False
    for spot, block in questions.items():
        if not isinstance(block, dict) or str(block.get("type") or "").lower() != "score":
            rebuilt[str(spot)] = block
            continue
        pending = amount_question.pending.get(str(spot))
        instructions = str(block.get("instructions") or "")
        built = score_question(str(spot), instructions, pending)
        body = built.get(str(spot)) if isinstance(built, dict) else None
        if not isinstance(body, dict):
            rebuilt[str(spot)] = block
            continue
        body = dict(body)
        body.pop("_anchor_values", None)
        criteria = body.get("criteria")
        from src.judgment.nineteen import _anchor_levels

        thinned = _anchor_levels(pending)
        if thinned:
            amount_question.pending[str(spot)] = list(thinned)
        if list(criteria or []) != list(block.get("criteria") or []):
            changed = True
        rebuilt[str(spot)] = body
    if not changed:
        return None
    return rebuilt


def post_answers(state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """One POST for this fact card. Independent questions travel together.

    The same facts reuse the return. An error is not cached and does not
    restore a number. An empty answer stays empty.
    """

    if not questions:
        return {}
    if not isinstance(state, Mapping):
        state = {}
    key = _pack_key(state, questions)
    with _LOCK:
        hit = _PACKS.get(key)
    if hit is not None:
        return dict(hit)
    answers, error, meta = _http(state, questions)
    if error and str(error).startswith("http_"):
        from src.judgment.nineteen import learned_score_level_cap, note_score_level_cap

        known = learned_score_level_cap()
        note_score_level_cap(meta.get("detail"))
        learned = learned_score_level_cap()
        rebuilt = _thinned_scores(questions) if learned is not None and learned != known else None
        if rebuilt:
            answers, error, meta = _http(state, rebuilt)
            questions = rebuilt
    _append_receipt({
        "sleeve": state.get("sleeve"),
        "symbol": state.get("symbol"),
        "bar": state.get("bar"),
        "error": error,
        "asked": sorted(str(qid) for qid in questions),
        "model": meta.get("model"),
        "http_status": meta.get("http_status"),
        "key_fingerprint": meta.get("key_fingerprint"),
        "key_source": meta.get("key_source"),
    })
    if error is not None:
        return {}
    stamped = dict(answers)
    levels = {
        str(spot): list(pair)
        for spot, pair in amount_question.pending.items()
        if str(spot) in questions
    }
    if levels:
        stamped["_anchor_levels"] = levels
    with _LOCK:
        _PACKS[key] = dict(stamped)
    return dict(stamped)


def _post(state: dict[str, Any], spots: Mapping[str, Mapping[str, Any]]) -> dict[str, str | None]:
    sides: dict[str, str | None] = {name: None for name in spots}
    questions = _questions(spots)
    answers, error, meta = _http(state, questions)
    if error is not None and not answers:
        _append_receipt({
            "sleeve": state.get("sleeve"),
            "symbol": state.get("symbol"),
            "bar": state.get("bar"),
            "error": error,
            "sides": sides,
            "model": meta.get("model", MODEL),
            "http_status": meta.get("http_status"),
            "key_fingerprint": meta.get("key_fingerprint"),
            "key_source": meta.get("key_source"),
        })
        return sides
    probs_out: dict[str, Any] = {}
    for name in spots:
        answer = answers.get(name) if isinstance(answers.get(name), dict) else {}
        probs = answer.get("probabilities") if isinstance(answer, dict) else None
        if not isinstance(probs, dict) or not probs:
            sides[name] = None
            continue
        choice = unique_highest(probs)
        sides[name] = choice
        probs_out[name] = {
            str(k): float(v) for k, v in probs.items()
            if k in _SIDES and _finite(v) is not None
        }
    if any(v is None for v in sides.values()) and error is None:
        error = "unanswered"
    _append_receipt({
        "sleeve": state.get("sleeve"),
        "symbol": state.get("symbol"),
        "bar": state.get("bar"),
        "sides": sides,
        "probabilities": probs_out,
        "error": error,
        "model": meta.get("model", MODEL),
        "http_status": meta.get("http_status"),
        "key_fingerprint": meta.get("key_fingerprint"),
        "key_source": meta.get("key_source"),
    })
    return sides


def ask(*, sleeve: str, symbol: str, bar_id: str, spots: Mapping[str, Mapping[str, Any]]) -> dict[str, str | None]:
    """One POST. Returns spot -> condition_true | condition_false | None."""
    if not spots:
        return {}
    token = _cache_token(sleeve, symbol, str(bar_id), spots)
    with _LOCK:
        _load_disk()
        cached = _CACHE.get(token)
    if cached is not None and set(cached) == set(spots):
        return dict(cached)
    state = {
        "sleeve": sleeve,
        "symbol": symbol,
        "namespace": NAMESPACE,
        "login": LOGIN,
        "bar": str(bar_id),
        "measured": {name: bool(spec.get("measured")) for name, spec in spots.items()},
        "flatten": False,
        "order_send": False,
        "do_not_close_ticket": 294215389,
    }
    sides = _post(state, spots)
    if sides and all(v in _SIDES for v in sides.values()):
        with _LOCK:
            _CACHE[token] = dict(sides)
            _store_disk(token, dict(sides))
    return sides
