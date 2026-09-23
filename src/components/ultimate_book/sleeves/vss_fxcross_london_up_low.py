"""London FX-cross M15 volatility-state squeeze breakout in D1-up/low-vol.

Default-off research candidate. This is not the existing H4 index vol_squeeze
or the D1 crypto vol_compression mechanic. It uses M15 box-width-in-ATR
compression, a London session gate, a mandatory prior-D1 up-regime auxiliary
gate, and an M15 low-vol-state gate before a prior-box breakout entry.

Research proof, 2026-06-17:
- raw trades n=860, train/oos/sealed meanR +0.0770/+0.0695/+0.3285.
- daily unit n=518, train/oos/sealed +0.112171/+0.001194/+0.391658.
- correct random-entry and drift null p ~= 0.0017.
- canonical verifier requires 860/860 reference parity and zero false positives.

Book caveat: OOS daily-unit mean is very thin and 2024 is weak. The sleeve is
therefore promoted as an OOS-decay-watch candidate, default-off, no live authority.
"""

from __future__ import annotations

from . import fx_spot

from typing import Optional

from ..admission import TradeIntent
from ._server_clock import server_hour


N_BOX = 20
PCT_WIN = 200
SQ_PCTL = 0.35
ATR_LB = 500
VOL_LOW_PCTL = 0.33
STOP_ATR = 1.0
TGT_ATR = 2.0
MAXBARS = 48
LONDON_LO = 7
LONDON_HI = 13
SMA_FAST = 20
SMA_SLOW = 50
ON_SURFACE = ("GBPJPY",)
MIN_BARS = N_BOX + PCT_WIN + 1


def _atr14(bars, i: int) -> float:
    if i < 14:
        return 0.0
    total = 0.0
    for j in range(i - 13, i + 1):
        total += max(bars[j].h - bars[j].l, abs(bars[j].h - bars[j - 1].c), abs(bars[j].l - bars[j - 1].c))
    return total / 14.0


def _rolling_extreme_at(vals, win: int, is_max: bool, end_idx: int):
    if end_idx < win - 1:
        return None
    segment = vals[end_idx - win + 1 : end_idx + 1]
    return max(segment) if is_max else min(segment)


def _hour(t):
    """SERVER-LOCAL hour. The session constants here are FTMO server hours (F7/B29); the
    live feed is true UTC, so this converts before comparing. None -> fail closed."""
    return server_hour(t)


def _daystr(t) -> str | None:
    if t is None:
        return None
    if hasattr(t, "year"):
        return f"{t.year:04d}-{t.month:02d}-{t.day:02d}"
    s = str(t)
    return s[:10] if len(s) >= 10 else None


def _d1_up_regime(aux_bars, aux_times, decision_day: str) -> Optional[bool]:
    if not aux_bars or not aux_times or len(aux_bars) != len(aux_times):
        return None
    closes = []
    for bar, t in zip(aux_bars, aux_times):
        day = _daystr(t)
        if day is not None and day < decision_day:
            closes.append(bar.c)
    if len(closes) < SMA_SLOW:
        return None
    window = closes[-SMA_SLOW:]
    sma20 = sum(window[-SMA_FAST:]) / SMA_FAST
    sma50 = sum(window) / SMA_SLOW
    last = window[-1]
    ret20 = (window[-1] - window[-SMA_FAST]) / window[-SMA_FAST] if window[-SMA_FAST] != 0 else 0.0
    return (sma20 > sma50) and (last > sma20) and (ret20 > 0.0)


def _rank_strict_less(sorted_vals: list[float], value: float) -> float:
    lo_idx, hi_idx = 0, len(sorted_vals)
    while lo_idx < hi_idx:
        mid = (lo_idx + hi_idx) // 2
        if sorted_vals[mid] < value:
            lo_idx = mid + 1
        else:
            hi_idx = mid
    return lo_idx / len(sorted_vals)


def spot_pack(
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    **_,
):
    """Facts for the London FX-cross squeeze. The Choice decides the emit."""
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    on_surface = bool(symbol in ON_SURFACE and bars)
    warmup_ok = bool(i >= MIN_BARS)
    stamp = None
    if bar_time is not None:
        stamp = bar_time
    elif bar_times and bars and len(bar_times) == len(bars):
        stamp = bar_times[i]
    hour = _hour(stamp)
    london = bool(hour is not None and LONDON_LO <= hour < LONDON_HI)
    d1_up = _d1_up_regime(aux_bars, aux_times, decision_day) is True
    atr_i = _atr14(bars, i) if i >= 14 else 0.0
    atr_ok = bool(atr_i > 0.0)
    highs = [bar.h for bar in bars] if bars else []
    lows = [bar.l for bar in bars] if bars else []
    box_hi_i = _rolling_extreme_at(highs, N_BOX, True, i) if i >= 0 else None
    box_lo_i = _rolling_extreme_at(lows, N_BOX, False, i) if i >= 0 else None
    prior_hi = _rolling_extreme_at(highs, N_BOX, True, i - 1) if i >= 1 else None
    prior_lo = _rolling_extreme_at(lows, N_BOX, False, i - 1) if i >= 1 else None
    box_ok = None not in (box_hi_i, box_lo_i, prior_hi, prior_lo)
    hist = []
    if box_ok and atr_ok and i >= PCT_WIN:
        for k in range(i - PCT_WIN, i):
            atr_k = _atr14(bars, k)
            box_hi_k = _rolling_extreme_at(highs, N_BOX, True, k)
            box_lo_k = _rolling_extreme_at(lows, N_BOX, False, k)
            if box_hi_k is None or box_lo_k is None or atr_k <= 0:
                continue
            hist.append((box_hi_k - box_lo_k) / atr_k)
    hist_ok = bool(len(hist) >= PCT_WIN // 2)
    squeezed = False
    if hist_ok and box_ok and atr_ok:
        ratio_i = (box_hi_i - box_lo_i) / atr_i
        ordered = sorted(hist)
        squeezed = bool(_rank_strict_less(ordered, ratio_i) <= SQ_PCTL)
    direction = 0
    if box_ok and i >= 0:
        close = bars[i].c
        if close > prior_hi:
            direction = 1
        elif close < prior_lo:
            direction = -1
    outside = bool(direction != 0)
    atr_window = []
    if i >= 0:
        atr_window = [value for value in (_atr14(bars, k) for k in range(max(0, i - ATR_LB), i)) if value > 0]
    vol_hist_ok = bool(len(atr_window) >= 50)
    vol_low = False
    if vol_hist_ok and atr_ok:
        vol_low = bool(_rank_strict_less(sorted(atr_window), atr_i) < VOL_LOW_PCTL)
    stop_dist = STOP_ATR * atr_i if atr_ok else 0.0
    stop_ok = bool(stop_dist > 0.0)
    pattern_printed = bool(
        on_surface
        and warmup_ok
        and london
        and d1_up
        and atr_ok
        and box_ok
        and hist_ok
        and squeezed
        and outside
        and vol_hist_ok
        and vol_low
        and stop_ok
    )
    state = fx_spot.book_state(
        "vss_fxcross_london_up_low",
        symbol,
        on_surface=on_surface,
        n_bars=n,
        warmup_complete=warmup_ok,
        hour=hour,
        london_hour=london,
        d1_up=d1_up,
        atr_positive=atr_ok,
        box_present=box_ok,
        squeeze_history_enough=hist_ok,
        squeeze_at_or_under_percentile=squeezed,
        close_outside_prior_box=outside,
        direction=direction,
        vol_history_enough=vol_hist_ok,
        vol_in_the_low_state=vol_low,
        stop_positive=stop_ok,
        pattern_printed=pattern_printed,
        decision_day=decision_day,
    )
    ask = "Which side of this condition is this bar?"
    questions = {
        "surface": fx_spot.q(
            "on_named_surface",
            "This symbol is GBPJPY and bars are present.",
            "off_surface_or_no_bars",
            "This symbol is not GBPJPY, or there are no bars.",
            ask,
        ),
        "warmup": fx_spot.q(
            "warmup_complete",
            "The bar count covers the box, the percentile window, and one prior bar.",
            "bars_short",
            "The bar count is short of that warmup.",
            ask,
        ),
        "london": fx_spot.q(
            "london_hour",
            "The server hour is inside the London window from 7 inclusive to 13 exclusive.",
            "not_london_hour",
            "The server hour is missing or outside that London window.",
            ask,
        ),
        "d1": fx_spot.q(
            "d1_up",
            "The prior daily regime is up: fast average above slow, last close above the fast average, and a positive 20-day return.",
            "d1_not_up",
            "The prior daily regime is not up, or the daily bars are missing.",
            ask,
        ),
        "atr": fx_spot.q(
            "atr_positive",
            "ATR can scale the box and the stop.",
            "atr_not_a_scale",
            "ATR is not a positive scale.",
            ask,
        ),
        "box": fx_spot.q(
            "box_present",
            "The current box and the prior box both have a high and a low.",
            "box_missing",
            "A current or prior box extreme is missing.",
            ask,
        ),
        "squeeze_history": fx_spot.q(
            "squeeze_history_enough",
            "Enough prior box-width ratios exist to rank this bar.",
            "squeeze_history_short",
            "The prior box-width sample is too short to rank this bar.",
            ask,
        ),
        "squeeze": fx_spot.q(
            "squeeze_at_or_under_percentile",
            "This bar's box width ranks at or under the squeeze percentile.",
            "squeeze_wider_than_percentile",
            "This bar's box width ranks wider than the squeeze percentile.",
            ask,
        ),
        "break": fx_spot.q(
            "close_outside_prior_box",
            "The close is outside the prior box.",
            "close_inside_prior_box",
            "The close is still inside the prior box.",
            ask,
        ),
        "vol_history": fx_spot.q(
            "vol_history_enough",
            "Enough prior ATR values exist to rank this bar's volatility.",
            "vol_history_short",
            "The prior ATR sample is too short to rank volatility.",
            ask,
        ),
        "vol": fx_spot.q(
            "vol_in_the_low_state",
            "This bar's ATR ranks in the low-vol state.",
            "vol_not_low",
            "This bar's ATR does not rank in the low-vol state.",
            ask,
        ),
        "stop": fx_spot.q(
            "stop_is_the_plan",
            "The ATR stop distance is positive.",
            "stop_not_positive",
            "The ATR stop distance is not positive.",
            ask,
        ),
    }
    build = None
    if stop_ok and direction != 0:
        build = {
            "sleeve": "vss_fxcross_london_up_low",
            "symbol": symbol,
            "direction": direction,
            "decision_day": decision_day,
            "stop_dist": stop_dist,
            "target_dist": TGT_ATR * atr_i,
        }
    return {"state": state, "questions": questions, "build": build}


def generate(
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    **_,
) -> Optional[TradeIntent]:
    """Emit the London squeeze break when every spot's continue side is the unique highest."""
    packed = spot_pack(
        symbol,
        bars,
        decision_day,
        bar_time=bar_time,
        bar_times=bar_times,
        aux_bars=aux_bars,
        aux_times=aux_times,
        **_,
    )
    n_bars = packed["state"]["n_bars"]
    picks = fx_spot.unique_sides(
        packed["questions"],
        packed["state"],
        f"vss_fxcross_london_up_low|{symbol}|{n_bars}|{decision_day}",
    )
    if not fx_spot.continues(picks, packed["questions"]):
        return None
    build = packed["build"]
    if not build:
        return None
    return TradeIntent(**build)

# GROK_KEEP_ACTIVATE_20260920
KEEP_ACTIVATE_LONG_PREF_GBPJPY = True
GBPJPY_VSS_SHORT_HARD_OFF = True
