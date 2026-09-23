"""dsp_london_bounce_fails_overnight_midpoint -- unused-window lead 3, 2026-08-21.

Overnight Asia grind-down, then a 1.5+ ATR bounce that does not reclaim the
overnight midpoint. Session mask is London-local 08:00-09:15 converted through
NEW_YORK_PLUS_7 (not hour==9). Formula verbatim verified_w8.json.
V2 said LONG (60% up) — WRONG. Side is best_both_halves SHORT.

MEASURED (never assumed):
  unused-geo 1-5 session-mask then geometry.py both-direction grid
  discovery window dev_2022_2024_all166  hold 2022-01-01..2025-01-01
  best_both_halves SHORT 0.75/6.0  hold R +0.359  (n_hold 426)
  ship 1.0/6.0 same side  hold R +0.308  (n_hold 426)  clears +0.12
  day-blocked hold SE 0.200 / MDE80 0.426 / blocks 281
  scored over 163/166 instruments; formula evaluated bar-by-bar, causal.

Status forward_only: split-sample backtest and NO forward record.
Confidence starts at 0.15 for that reason. NOT ARMED.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from ..admission import TradeIntent
from .dsp_spot_choice import spots_allow_emit
from ._unused_a_session_mask import mask_london_0815

TAG = "dsp_london_bounce_fails_overnight_midpoint"
ON_SURFACE: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD")

_WARMUP = 200
_STOP_ATR = 1.0
_TARGET_ATR = 6.0
_DIRECTION = -1         # +1 long / -1 short  — geometry 1.0/6.0, NOT V2 up-rate


def _arrays(bars):
    """Bar is a dataclass (o,h,l,c,v) -- primitives.py:19. Causal ATR(14) ending at each bar."""
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
        atr[14:] = k[:n - 14]                      # ATR at bar i uses tr[i-14:i] -- strictly prior
    return o, h, l, c, v, atr


def _signal(o, h, l, c, v, atr):
    """The discovered condition. Verbatim from verified_w8.json."""
    atr_s=np.maximum(atr,1e-12); n=len(c); rng=np.maximum(h-l,1e-12); out=np.zeros(n,dtype=bool)
    for t in range(24,n):
        grind=(c[t-1]-c[t-16])<=-1.5*atr_s[t] and np.max(rng[t-16:t]/atr_s[t-16:t])<=2.0
        bounce=(c[t]-o[t])>=1.5*atr_s[t]
        giveback=t>=1 and (c[t-1]-o[t-1])>=1.5*atr_s[t-1] and (c[t]<=o[t-1]+0.2*atr_s[t])
        if not (grind and (bounce or giveback)): continue
        mid=0.5*(np.max(h[t-23:t+1])+np.min(l[t-23:t+1]))
        if c[t]>=mid: continue
        if h[t]>=np.max(h[t-23:t])-0.5*atr_s[t]: continue
        out[t]=True
    sig = out
    return sig


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Facts are measured. Each former decision if is one spot Choice.

    Two sides. The unique highest probability is that condition. Empty, tie,
    and transport failure do not restore the old boolean and do not emit.
    """
    n = len(bars) if bars else 0
    on_surface = bool(bars) and symbol in ON_SURFACE
    pattern_printed = False
    shape_matches = False
    atr_scale = None
    signal_error = False
    i = n - 1 if n else 0
    if bars and n > 0:
        try:
            o, h, l, c, v, atr = _arrays(bars)
            sig = np.asarray(_signal(o, h, l, c, v, atr))
            shape_matches = tuple(getattr(sig, "shape", ())) == tuple(getattr(c, "shape", ()))
            if shape_matches:
                i = n - 1
                pattern_printed = bool(sig[i])
                a_raw = float(atr[i])
                if a_raw > 0.0 and np.isfinite(a_raw):
                    atr_scale = a_raw
        except Exception:
            pattern_printed = False
            shape_matches = False
            atr_scale = None
            signal_error = True
    timing_fact = False
    if n > 0:
        try:
            from ..xasset_direction import stay_timing
            timing_fact = bool(stay_timing(TAG, {"symbol": symbol, "index": i}, _.get("peer_panel")))
        except Exception:
            timing_fact = False
    session_mask = False
    try:
        session_mask = bool(mask_london_0815(symbol=symbol, bar_time=bar_time, bar_times=bar_times))
    except Exception:
        session_mask = False
    facts = {
        "sleeve": TAG,
        "symbol": symbol,
        "namespace": "operator",
        "on_named_surface": on_surface,
        "named_surface": list(ON_SURFACE),
        "bar_count": n,
        "warmup": _WARMUP,
        "pattern_printed": pattern_printed,
        "signal_shape_matches": shape_matches,
        "signal_error": signal_error,
        "atr": atr_scale,
        "atr_is_a_scale": atr_scale is not None,
        "stay_timing": timing_fact,
        "index": int(i) if n else None,
        "open_ticket": 294215389,
        "flatten": False,
    }
    facts["session_mask"] = session_mask
    facts["session_mask_name"] = "mask_london_0815"
    pattern_side = "london_bounce_fails_overnight_midpoint"
    hold = "Do not close ticket 294215389."
    spots = [
        {
            "id": "named_surface",
            "emit": "on_named_surface",
            "other": "off_surface_or_no_bars",
            "emit_text": "This symbol is one of the named names and bars exist.",
            "other_text": "This symbol is off the named surface or there are no bars.",
            "instructions": "on_named_surface is the measured fact for this sleeve's named names and bars. Which side is this bar? " + hold,
        },
        {
            "id": "warmup",
            "emit": "warmup_complete",
            "other": "bars_short_of_200",
            "emit_text": "The bar count covers this sleeve's 200-bar warmup.",
            "other_text": "The bar count is short of this sleeve's 200-bar warmup.",
            "instructions": "bar_count and warmup are the measured facts. Which side is this bar? " + hold,
        },
        {
            "id": "signal_shape",
            "emit": "signal_shape_matches",
            "other": "signal_shape_mismatch",
            "emit_text": "The predicate array lines up with the closes.",
            "other_text": "The predicate array does not line up with the closes.",
            "instructions": "signal_shape_matches is the measured fact. Which side is this bar? " + hold,
        },
        {
            "id": "pattern",
            "emit": pattern_side,
            "other": "pattern_absent",
            "emit_text": "This sleeve's predicate printed on the closed bar.",
            "other_text": "This sleeve's predicate did not print on the closed bar.",
            "instructions": "pattern_printed is the measured predicate for " + pattern_side + ". Which side is this bar? " + hold,
        },
        {
            "id": "atr_scale",
            "emit": "atr_positive",
            "other": "atr_not_a_scale",
            "emit_text": "ATR is a positive finite scale for the stop and the target.",
            "other_text": "ATR cannot scale the stop and the target.",
            "instructions": "atr_is_a_scale and atr are the measured scale. Which side is this bar? " + hold,
        },
        {
            "id": "stay_timing",
            "emit": "pattern_already_accepted",
            "other": "still_timing",
            "emit_text": "The pattern is the intent. Timing does not withhold this bar.",
            "other_text": "Timing still withholds this bar.",
            "instructions": "stay_timing is the measured second check after the predicate. Which side is this bar? " + hold,
        },
        {
            "id": "session_mask",
            "emit": "session_mask_holds",
            "other": "session_mask_absent",
            "emit_text": "The named session mask holds on this bar.",
            "other_text": "The named session mask does not hold on this bar.",
            "instructions": "session_mask_name and session_mask are the measured clock mask. Which side is this bar? " + hold,
        },
    ]
    cache_key = "|".join([
        TAG,
        str(symbol),
        str(n),
        str(facts["index"]),
        str(on_surface),
        str(pattern_printed),
        str(shape_matches),
        str(atr_scale),
        str(timing_fact),
        str(facts.get("session_mask")),
        str(facts.get("session_mask_name")),
        str(signal_error),
    ])
    if not spots_allow_emit(facts, spots, cache_key):
        return None
    try:
        a = float(atr_scale)
    except (TypeError, ValueError):
        return None
    return TradeIntent(
        sleeve=TAG,
        symbol=symbol,
        direction=_DIRECTION,
        decision_day=decision_day,
        stop_dist=_STOP_ATR * a,
        target_dist=_TARGET_ATR * a,
    )
