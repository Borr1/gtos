"""dsp_small_bar_sit_on_20high_rejects -- DISPREAD occupancy+geo, 2026-08-21.

Hours of tiny bodies under a high that was never accepted: coil < 0.55, last
body < 0.8 ATR, >=4 of the last 8 highs glued to the 20-high, close in the
bottom 40%. Occupancy called this DOWN (hold lift 1.26, same-way hold 0.488).
Same-way is not a side. Geometry first-touch 1.0/6.0 is LONG. US30 12.11 is
Asia 0.02-0.90 bodies then 9.55 at 05:00; RACE 12.21 coil 0.48 last body 0.39
with 12 equal highs. COCOA 12.17 / CADCHF 12.9 are the same coil as a flat
shelf after a lift, then UP — the ship side. Formula verbatim DISPREAD-12-23.md
§6 asia_dead_ceiling_then_smash.

MEASURED (never assumed):
  displacement within 3 bars, base after excludes 0.636% disc / 0.500% hold
  occupancy: lift 1.72x disc / 1.26x hold  n_fire 38,838 / 40,238
  occupancy claimed DOWN (same-way hold 0.488) — WRONG as a side
  geometry.py first-touch 1.0/6.0 LONG  hold R +0.201  (n_hold 38,016)
  (0.75/6.0 is best_both_halves +0.265; ship 1.0/6.0 to stay out of the FX 5-8 pip bleed)
  scored over 166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by DISPREAD 12-23 §6. Supporting events 12.11 US30, 12.21 RACE, 12.34 EURNOK;
contradicting 12.17 COCOA, 12.9 CADCHF, 13.2 KO.
What would kill it: a coil<0.55 with last body<0.8 and >=4 highs glued to the
20-high produces an UP displacement (the ship side) no more often than the same
coil glued to the 20-low.

Status forward_only: this has a split-sample backtest and NO forward record.
Confidence starts at 0.15 for that reason. NOT ARMED.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from ..admission import TradeIntent
from .dsp_spot_choice import spots_allow_emit

TAG = "dsp_small_bar_sit_on_20high_rejects"
ON_SURFACE: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD")

_WARMUP = 200
_STOP_ATR = 1.0
_TARGET_ATR = 6.0
_DIRECTION = 1          # +1 long / -1 short  — geometry first-touch 1.0/6.0, NOT occupancy same-way


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
    """The discovered condition. Verbatim DISPREAD-12-23.md §6 asia_dead_ceiling_then_smash."""
    atr_s=np.maximum(atr,1e-12)
    hh20=np.array([np.max(h[max(0,i-19):i+1]) for i in range(len(c))])
    bodies=np.abs(c-o)/atr_s
    atr6=np.array([np.mean((h-l)[max(0,i-5):i+1]) for i in range(len(c))])
    atr48=np.array([np.mean((h-l)[max(0,i-47):i+1]) for i in range(len(c))])
    coil=atr6/np.maximum(atr48,1e-12)
    near=np.array([np.sum(np.abs(h[max(0,i-7):i+1]-hh20[i])<=0.4*atr_s[i]) for i in range(len(c))])
    sig=(coil<0.55)&(bodies<0.8)&(near>=4)&((c-l)/np.maximum(h-l,1e-12)<=0.40)
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
        "flatten": False,
    }
    pattern_side = "small_bar_sit_on_20high_rejects"
    spots = [
        {
            "id": "named_surface",
            "emit": "on_named_surface",
            "other": "off_surface_or_no_bars",
            "emit_text": "This symbol is one of the named names and bars exist.",
            "other_text": "This symbol is off the named surface or there are no bars.",
            "instructions": "on_named_surface is the measured fact for this sleeve's named names and bars. Which side is this bar?",
        },
        {
            "id": "warmup",
            "emit": "warmup_complete",
            "other": "bars_short_of_200",
            "emit_text": "The bar count covers this sleeve's 200-bar warmup.",
            "other_text": "The bar count is short of this sleeve's 200-bar warmup.",
            "instructions": "bar_count and warmup are the measured facts. Which side is this bar?",
        },
        {
            "id": "signal_shape",
            "emit": "signal_shape_matches",
            "other": "signal_shape_mismatch",
            "emit_text": "The predicate array lines up with the closes.",
            "other_text": "The predicate array does not line up with the closes.",
            "instructions": "signal_shape_matches is the measured fact. Which side is this bar?",
        },
        {
            "id": "pattern",
            "emit": pattern_side,
            "other": "pattern_absent",
            "emit_text": "This sleeve's predicate printed on the closed bar.",
            "other_text": "This sleeve's predicate did not print on the closed bar.",
            "instructions": "pattern_printed is the measured predicate for " + pattern_side + ". Which side is this bar?",
        },
        {
            "id": "atr_scale",
            "emit": "atr_positive",
            "other": "atr_not_a_scale",
            "emit_text": "ATR is a positive finite scale for the stop and the target.",
            "other_text": "ATR cannot scale the stop and the target.",
            "instructions": "atr_is_a_scale and atr are the measured scale. Which side is this bar?",
        },
        {
            "id": "stay_timing",
            "emit": "pattern_already_accepted",
            "other": "still_timing",
            "emit_text": "The pattern is the intent. Timing does not withhold this bar.",
            "other_text": "Timing still withholds this bar.",
            "instructions": "stay_timing is the measured second check after the predicate. Which side is this bar?",
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
    try:
        _ex = float(np.max(h[max(0, i-19):i+1]))
        if not np.isfinite(_ex) or _ex <= 0.0:
            _ex = None
    except (TypeError, ValueError):
        _ex = None
    return TradeIntent(
        sleeve=TAG,
        symbol=symbol,
        direction=_DIRECTION,
        decision_day=decision_day,
        stop_dist=_STOP_ATR * a,
        target_dist=_TARGET_ATR * a,
        entry_price=_ex,
    )
