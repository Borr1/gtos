#!/usr/bin/env python3
"""B2 — leftover timing names as ±X ATR brackets. Not directional dsp. Not a second xa_*.

Nine MDE80-ready timing names already live as xa_*. first_cash_bar_spike_and_flush
already lives as dsp_*. These two leftovers are brackets only. Not on tags.
"""
from __future__ import annotations
from .account_surface import on_surface_for_process

from typing import Optional

import numpy as np

from ..admission import TradeIntent
from .spot_choice import ask, bar_id

# The twelve ARMABLE timing names. Live xa_* cover nine. dsp covers first_cash.
# Brackets cover the remaining two.
BRACKET_NAMES = (
    "one_bar_consumes_20bar_box",
    "climax_volume_tag_high_reverses",
)
LIVE_XA = frozenset({
    "wave_two_standing_bar_already_large",
    "already_huge_same_way_wave_two",
    "huge_bar_closed_on_20bar_extreme",
    "isolated_huge_bar_then_opposite",
    "already_huge_and_prior_huge_same_way",
    "climax_first_touch_20low_springs",
    "second_rth_bar_after_open_drive",
    "already_wide_bar_same_extreme",
    "second_leg_after_first_expansion",
})
ALREADY_DSP = frozenset({"first_cash_bar_spike_and_flush"})

TAG = "tm_one_bar_consumes_20bar_box"
ON_SURFACE: tuple[str, ...] = on_surface_for_process()
_WARMUP = 40
_BRACKET_ATR = 1.0  # ±X ATR. Not a directional stop.


def bracket_levels(close: float, atr: float, x: float = _BRACKET_ATR) -> tuple[float, float]:
    """Buy-stop / sell-stop around the close. Side is not chosen."""
    a = float(atr) * float(x)
    c = float(close)
    return c + a, c - a


def _arrays(bars):
    n = len(bars)
    o = np.fromiter((b.o for b in bars), float, n)
    h = np.fromiter((b.h for b in bars), float, n)
    l = np.fromiter((b.l for b in bars), float, n)
    c = np.fromiter((b.c for b in bars), float, n)
    v = np.fromiter((getattr(b, "v", 0.0) or 0.0 for b in bars), float, n)
    pc = np.empty(n); pc[0] = c[0]; pc[1:] = c[:-1]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    atr = np.full(n, np.nan)
    if n > 14:
        k = np.convolve(tr, np.ones(14) / 14.0, mode="valid")
        atr[14:] = k[:n - 14]
    return o, h, l, c, v, atr


def _one_bar_consumes_box(o, h, l, c, atr):
    n = len(c)
    out = np.zeros(n, dtype=bool)
    for t in range(20, n):
        box = float(np.max(h[t - 19:t]) - np.min(l[t - 19:t]))
        if not np.isfinite(box) or box <= 0:
            continue
        body = abs(float(c[t]) - float(o[t]))
        out[t] = body >= 0.90 * box
    return out


def _climax_volume_tag_high(h, v, atr):
    n = len(h)
    out = np.zeros(n, dtype=bool)
    for t in range(20, n):
        hh = float(np.max(h[t - 19:t + 1]))
        vv = float(np.max(v[t - 19:t + 1])) if np.isfinite(v[t]) else 0.0
        out[t] = (h[t] >= hh - 1e-12) and (v[t] >= 0.90 * vv) and (v[t] > 0)
    return out


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Not wired into DISPLACEMENT_BUILT. Returns None always — brackets are not a live sleeve."""
    del symbol, bars, decision_day, bar_time, bar_times, aux_bars, aux_times, _
    return None


def levels_if_fire(symbol: str, bars, which: str = "one_bar_consumes_20bar_box"):
    if not bars:
        return None
    n = len(bars)
    short = n < _WARMUP
    a = float("nan")
    close = None
    box_absent = True
    climax_absent = True
    if not short:
        o, h, l, c, v, atr = _arrays(bars)
        i = n - 1
        a = float(atr[i])
        if not (a > 0) or not np.isfinite(a):
            return None
        close = float(c[i])
        box_absent = not bool(_one_bar_consumes_box(o, h, l, c, atr)[i])
        climax_absent = not bool(_climax_volume_tag_high(h, v, atr)[i])
    box_name = "one_bar_consumes_20bar_box"
    sides = ask(
        sleeve=TAG,
        symbol=symbol,
        bar_id=bar_id(symbol, n, None, None),
        spots={
            "off_surface": {
                "condition": f"symbol {symbol} is not in ON_SURFACE",
                "measured": symbol not in ON_SURFACE,
            },
            "warmup_short": {
                "condition": f"bar count {n} is below warmup {_WARMUP}",
                "measured": short,
            },
            "shape_is_box": {
                "condition": f"which equals {box_name}",
                "measured": which == box_name,
            },
            "box_absent": {
                "condition": "the latest closed bar does not print one_bar_consumes_20bar_box",
                "measured": box_absent,
            },
            "climax_absent": {
                "condition": "the latest closed bar does not print climax_volume_tag_high",
                "measured": climax_absent,
            },
        },
    )
    if sides.get("off_surface") != "condition_false" or sides.get("warmup_short") != "condition_false":
        return None
    shape = sides.get("shape_is_box")
    if shape is None:
        return None
    if shape == "condition_true":
        if sides.get("box_absent") != "condition_false":
            return None
    elif sides.get("climax_absent") != "condition_false":
        return None
    if short or close is None or not (a > 0) or not np.isfinite(a):
        return None
    up, dn = bracket_levels(close, a, _BRACKET_ATR)
    return {"buy_stop": up, "sell_stop": dn, "close": close, "atr": a, "x": _BRACKET_ATR}
