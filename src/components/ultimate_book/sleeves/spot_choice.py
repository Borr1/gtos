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
        if bars is not None and i is not None and i >= 1:
            try:
                hi_at = max(range(i + 1), key=lambda k: bars[k].h)
                lo_at = min(range(i + 1), key=lambda k: bars[k].l)
            except Exception:
                hi_at = None
                lo_at = None
            if hi_at is not None:
                _push(levels, "bars_since_high", i - hi_at, positive=True)
            if lo_at is not None:
                _push(levels, "bars_since_low", i - lo_at, positive=True)
        if bar_times is not None and bars is not None and i is not None:
            try:
                same = len(bar_times) == len(bars)
            except TypeError:
                same = False
            if same:
                hour, _, day = _server_parts(bar_times[i])
                if day is not None:
                    day_count = 0
                    hour_count = 0
                    for k in range(i + 1):
                        k_hour, _, k_day = _server_parts(bar_times[k])
                        if k_day != day:
                            continue
                        day_count += 1
                        if hour is not None and k_hour == hour:
                            hour_count += 1
                    _push(levels, "bars_this_server_day", day_count, positive=True)
                    _push(levels, "bars_this_server_hour", hour_count, positive=True)
        held = _finite(card.get("n_bars"))
        if held is None and bars is not None:
            try:
                held = float(len(bars))
            except TypeError:
                held = None
        _push(levels, "bars_held", held, positive=True)
        _push(levels, "bar_index", i, positive=True)
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
    """One score from the spine builder. Fewer than two anchors does not post.

    Criteria are label (value). The private anchor key stays off this post.
    The level count is the maximum the API has already stated.
    """

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
