"""Prior-day volume profile for the live POC sleeve.

A day profile is built only from that day's M1 bars. The bin width, the value
area, the node marks, and the near-node distance are scores for this feed.
An empty score, a tie, or an error leaves that bound unset and does not put
a printed width back. The prior completed day is the profile a later bar may use.
"""
from __future__ import annotations

import math
import statistics
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, timezone

_MODEL = "jev-1.13.0"
_UNSET = " An empty score leaves it unset. A tie leaves it unset. An error leaves it unset."
_CACHE: dict[tuple, dict] = {}

# Importers still load the name. It is not the bin width.
BIN_FRAC = None

_BUILD_SPOTS = (
    "bin_atr_frac",
    "value_area_frac",
    "node_min_count",
    "hvn_multiple",
    "lvn_multiple",
    "min_bin_count",
    "range_window",
)
_NEAR_SPOT = "near_atr"

_PROFILE_TEXT = {
    "bin_atr_frac": "The score you return is this feed's bin width as a fraction of the trailing daily-range median.",
    "value_area_frac": "The score you return is the share of the day's volume the value area covers.",
    "node_min_count": "The score you return is how many bins a profile needs before a node can be marked.",
    "hvn_multiple": "The score you return is the multiple of neighbourhood volume that marks a high-volume node.",
    "lvn_multiple": "The score you return is the multiple of neighbourhood volume that marks a low-volume node.",
    "min_bin_count": "The score you return is the least number of bins a day's profile uses.",
    "range_window": "The score you return is how many prior daily ranges the bin-width median uses.",
    "near_atr": "The score you return is the ATR distance that counts as standing on a profile node.",
}


def _num(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _count(value):
    number = _num(value)
    if number is None or number < 1:
        return None
    return int(round(number))


def _plain(facts: dict) -> dict:
    out = {}
    for key, value in facts.items():
        if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
            out[str(key)] = value
            continue
        number = _num(value)
        if number is not None:
            out[str(key)] = number
        elif value is not None:
            out[str(key)] = str(value)
    return out


def _cache_key(facts: dict, spots: tuple[str, ...], anchors: dict | None = None) -> tuple:
    plain = _plain(facts)
    levels = []
    if isinstance(anchors, dict):
        for spot in spots:
            pairs = anchors.get(spot) or ()
            levels.append((spot, tuple((label, value) for label, value in pairs)))
    return (spots, tuple(sorted(plain.items())), tuple(levels))


def ask_scores(facts: dict, texts: dict[str, str], bars=None, index=None, bar_times=None) -> dict:
    """One post. Each spot is the returned score, or unset. A failed post is not cached."""

    spots = tuple(texts)
    out = {spot: None for spot in spots}
    out["_asked"] = False
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import (
            append_outcome,
            prior_outcomes,
            returned_number,
        )
        from .spot_choice import amount_question, anchors_for, value_at
    except Exception:
        return out
    questions: dict = {}
    built = {}
    for spot, text in texts.items():
        anchors = anchors_for(spot, facts, bars=bars, index=index, bar_times=bar_times)
        built[spot] = anchors
        questions.update(amount_question(spot, str(text).strip(), anchors))
    key = _cache_key(facts, spots, built)
    hit = _CACHE.get(key)
    if hit is not None:
        return dict(hit)
    if not questions:
        return out
    state = _plain(facts)
    try:
        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []
    try:
        receipt = evaluate(
            state,
            questions=questions,
            model=_MODEL,
            merge_sleeve=False,
            require_equity=False,
        )
    except Exception:
        return out
    if not isinstance(receipt, dict) or not receipt.get("ok"):
        return out
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    for spot in spots:
        number = value_at(returned_number(answers.get(spot)), built.get(spot))
        out[spot] = number
        try:
            append_outcome(
                spot,
                number,
                state,
                error=None if number is not None else "empty",
            )
        except Exception:
            pass
    out["_asked"] = True
    symbol = facts.get("symbol")
    for old in list(_CACHE):
        if old == key:
            continue
        blob = old[1] if isinstance(old, tuple) and len(old) > 1 else ()
        if symbol is not None and ("symbol", symbol) in blob:
            _CACHE.pop(old, None)
    _CACHE[key] = dict(out)
    return dict(out)


def _to_utc(t):
    """UTC day for an aware stamp. A naive stamp stays naive."""
    tz = getattr(t, "tzinfo", None)
    return t.astimezone(timezone.utc) if tz is not None else t


def load_m1(aux_bars, aux_times):
    """Deduped ascending M1 (times, bars). An empty or uneven feed is empty."""
    if not aux_bars or not aux_times or len(aux_bars) != len(aux_times):
        return [], []
    merged = {}
    for t, b in zip(aux_times, aux_bars):
        merged[_to_utc(t)] = b
    if not merged:
        return [], []
    items = sorted(merged.items(), key=lambda kv: kv[0])
    times = [k for k, _ in items]
    bars = [v for _, v in items]
    return times, bars


@dataclass
class DayProfile:
    day: date
    bin_w: float
    lo: float
    hist: list = field(default_factory=list)
    total_v: float = 0.0
    poc: float = 0.0
    poc_bin: int = 0
    vah: float = 0.0
    val: float = 0.0
    day_h: float = 0.0
    day_l: float = 0.0
    hvn: list = field(default_factory=list)
    lvn: list = field(default_factory=list)
    n_m1: int = 0

    def bin_center(self, b):
        return self.lo + (b + 0.5) * self.bin_w


def _distribute_bar_volume(hist, lo, bin_w, nbins, bar):
    """Spread one closed bar's volume across the bins its range covers."""
    if bar.h <= bar.l:
        b = int((bar.c - lo) / bin_w)
        if 0 <= b < nbins:
            hist[b] += bar.v
        return
    b_lo = int((bar.l - lo) / bin_w)
    b_hi = int((bar.h - lo) / bin_w)
    b_lo = max(0, min(nbins - 1, b_lo))
    b_hi = max(0, min(nbins - 1, b_hi))
    span = b_hi - b_lo + 1
    if span <= 1:
        hist[b_lo] += bar.v
    else:
        share = bar.v / span
        for b in range(b_lo, b_hi + 1):
            hist[b] += share


def _value_area(hist, poc_bin, total_v, frac=None):
    """Bins that hold the returned volume share. An unset share returns None."""
    number = _num(frac)
    if number is None or number <= 0 or total_v <= 0 or not hist:
        return None
    n = len(hist)
    if poc_bin < 0 or poc_bin >= n:
        return None
    lo_b = hi_b = poc_bin
    acc = hist[poc_bin]
    target = number * total_v
    while acc < target and (lo_b > 0 or hi_b < n - 1):
        down = hist[lo_b - 1] if lo_b > 0 else -1.0
        up = hist[hi_b + 1] if hi_b < n - 1 else -1.0
        if up >= down:
            hi_b += 1
            acc += hist[hi_b]
        else:
            lo_b -= 1
            acc += hist[lo_b]
    return lo_b, hi_b


def _find_nodes(hist, bin_w, lo, total_v, bounds=None):
    """High and low nodes. Missing scores return no nodes."""
    pack = bounds if isinstance(bounds, dict) else None
    if pack is None:
        pack = ask_scores(
            {"n_bins": len(hist), "total_v": _num(total_v), "bin_w": _num(bin_w)},
            {name: _PROFILE_TEXT[name] for name in ("node_min_count", "hvn_multiple", "lvn_multiple")},
        )
    need = _count(pack.get("node_min_count"))
    hvn_m = _num(pack.get("hvn_multiple"))
    lvn_m = _num(pack.get("lvn_multiple"))
    n = len(hist)
    if need is None or hvn_m is None or lvn_m is None or n < need or total_v <= 0:
        return [], []
    occ = [i for i in range(n) if hist[i] > 0]
    if not occ:
        return [], []
    a, z = occ[0], occ[-1]
    mean_v = total_v / max(1, (z - a + 1))
    hvn = []
    lvn = []
    for i in range(a + 1, z):
        v = hist[i]
        left = hist[i - 1]
        right = hist[i + 1]
        if v >= left and v >= right and v >= hvn_m * mean_v:
            hvn.append((v, lo + (i + 0.5) * bin_w))
        if v <= left and v <= right and v <= lvn_m * mean_v:
            lvn.append((v, lo + (i + 0.5) * bin_w))
    hvn.sort(key=lambda x: -x[0])
    lvn.sort(key=lambda x: x[0])
    return [p for _, p in hvn], [p for _, p in lvn]


def _feed_facts(aux_bars, aux_times) -> dict:
    times, bars = load_m1(aux_bars, aux_times)
    facts: dict = {"n_m1": len(bars)}
    if times:
        facts["first_stamp"] = str(times[0])
        facts["last_stamp"] = str(times[-1])
    if bars:
        last = bars[-1]
        facts["last_close"] = _num(getattr(last, "c", None))
    return facts


def build_day_profile(day, m1_bars, bin_w, bounds=None):
    """One day's profile. A passed pack is used. A missing pack asks once."""
    width = _num(bin_w)
    if not m1_bars or width is None or width <= 0:
        return None
    pack = bounds if isinstance(bounds, dict) else None
    if pack is None:
        pack = ask_scores(
            {"n_m1": len(m1_bars), "day": str(day), "bin_w": width},
            {name: _PROFILE_TEXT[name] for name in ("value_area_frac", "node_min_count", "hvn_multiple", "lvn_multiple", "min_bin_count")},
            bars=m1_bars,
            index=len(m1_bars) - 1,
        )
    floor = _count(pack.get("min_bin_count"))
    frac = _num(pack.get("value_area_frac"))
    if floor is None or frac is None:
        return None
    day_l = min(b.l for b in m1_bars)
    day_h = max(b.h for b in m1_bars)
    rng = day_h - day_l
    if rng <= 0:
        return None
    nbins = int(math.ceil(rng / width)) + 1
    if nbins < floor:
        nbins = floor
    lo = day_l
    hist = [0.0] * nbins
    for b in m1_bars:
        _distribute_bar_volume(hist, lo, width, nbins, b)
    total_v = sum(hist)
    if total_v <= 0:
        return None
    poc_bin = max(range(nbins), key=lambda i: hist[i])
    area = _value_area(hist, poc_bin, total_v, frac)
    if area is None:
        return None
    lo_b, hi_b = area
    hvn, lvn = _find_nodes(hist, width, lo, total_v, pack)
    return DayProfile(
        day=day,
        bin_w=width,
        lo=lo,
        hist=hist,
        total_v=total_v,
        poc_bin=poc_bin,
        poc=lo + (poc_bin + 0.5) * width,
        vah=lo + (hi_b + 0.5) * width,
        val=lo + (lo_b + 0.5) * width,
        day_h=day_h,
        day_l=day_l,
        hvn=hvn,
        lvn=lvn,
        n_m1=len(m1_bars),
    )


def daily_profiles(aux_bars, aux_times, bin_atr_frac=None, bounds=None):
    """Profiles by day. A passed pack is not asked again. A missing pack is one ask."""
    times, bars = load_m1(aux_bars, aux_times)
    if not bars:
        return {}, []
    del bin_atr_frac
    if isinstance(bounds, dict):
        pack = dict(bounds)
    else:
        pack = ask_scores(
            _feed_facts(aux_bars, aux_times),
            {name: _PROFILE_TEXT[name] for name in _BUILD_SPOTS},
            bars=bars,
            index=len(bars) - 1,
            bar_times=times,
        )
    if any(pack.get(name) is None for name in _BUILD_SPOTS):
        return {}, []
    by_day: OrderedDict = OrderedDict()
    for t, b in zip(times, bars):
        by_day.setdefault(t.date(), []).append(b)
    days = list(by_day.keys())
    day_rng = {d: (max(x.h for x in bs) - min(x.l for x in bs)) for d, bs in by_day.items()}
    window = _count(pack.get("range_window"))
    frac = _num(pack.get("bin_atr_frac"))
    if window is None or frac is None:
        return {}, []
    profiles = {}
    recent = []
    for d in days:
        med_rng = statistics.median(recent[-window:]) if recent else day_rng[d]
        bw = frac * med_rng
        if bw is not None and bw > 0:
            dp = build_day_profile(d, by_day[d], bw, pack)
            if dp is not None:
                profiles[d] = dp
        recent.append(day_rng[d])
    return profiles, [d for d in days if d in profiles]


def prior_profile_at(profiles, sorted_days, t):
    """The newest completed day strictly before this stamp."""
    td = t.date()
    prev = None
    for d in sorted_days:
        if d < td:
            prev = d
        else:
            break
    return profiles.get(prev) if prev is not None else None


def nearest_node_state(dp, price, atr, bounds=None):
    """Node distances. The near bound is the score. An unset bound leaves the flags unset."""
    if dp is None or _num(atr) is None or atr <= 0:
        return None
    pack = bounds if isinstance(bounds, dict) else None
    if pack is None:
        pack = ask_scores(
            {
                "price": _num(price),
                "atr": _num(atr),
                "poc": _num(dp.poc),
                "vah": _num(dp.vah),
                "val": _num(dp.val),
            },
            {_NEAR_SPOT: _PROFILE_TEXT[_NEAR_SPOT]},
        )
    near = _num(pack.get(_NEAR_SPOT))
    state = {
        "d_poc_atr": (price - dp.poc) / atr,
        "in_va": dp.val <= price <= dp.vah,
        "above_vah": price > dp.vah,
        "below_val": price < dp.val,
    }

    def nearest(levels):
        if not levels:
            return None, None
        best = min(levels, key=lambda p: abs(p - price))
        return best, abs(best - price) / atr

    _hvn_p, hvn_d = nearest(dp.hvn)
    _lvn_p, lvn_d = nearest(dp.lvn)
    state["near_hvn_atr"] = hvn_d
    state["near_lvn_atr"] = lvn_d

    def at(dist):
        if near is None or dist is None:
            return None
        return dist <= near

    state["at_hvn"] = at(hvn_d)
    state["at_lvn"] = at(lvn_d)
    state["at_poc"] = at(abs(price - dp.poc) / atr)
    state["at_vah"] = at(abs(price - dp.vah) / atr)
    state["at_val"] = at(abs(price - dp.val) / atr)
    state["near_atr"] = near
    return state
