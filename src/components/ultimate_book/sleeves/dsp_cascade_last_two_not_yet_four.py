"""dsp_cascade_last_two_not_yet_four -- discovered 2026-08-21 by the displacement precondition sweep.

The last two completed bars are already 1.8+ ATR in the same direction and the
standing close is not yet a 4 ATR bar. The named displacement is the third wave
of a cascade that a person can already see. DOT 26 on 2024-08-05: k=-2 is 2.53
ATR to 4.568, k=-1 is 2.22 ATR to 4.464 after tagging 4.419, then 4.82 more to
4.182 with BTC already -5.45 (and it keeps going). ICP 33 is the slower stair
(0.65 then 0.49) that still belongs next door. GBP 9's last bar is a 0.44 pause
after a single 5.46 -- that is impulse-pause, not cascade. EURCAD 40's last bar
is a 2.47 climax the other way. last_range on k=-1 is already the event starting;
a 'just fell hard in the last hour' bit that also requires TWO hard bars is the
increment.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.252%
  discovery 2014-2021 : lift 4.28x   n_fire 11,061   P(disp) 6.73%
  holdout   2022-2026 : lift 4.24x   n_fire 13,354   P(disp) 5.30%
  direction: 42% of displacements resolve UP  ->  V2 up-rate labelled SHORT (agreed)
  geometry.py first-touch 1.0/6.0 SHORT  hold R +0.128  (n_hold 13,812)
  (0.75/6.0 is best_both_halves +0.154; ship 1.0/6.0 to stay out of the FX 5-8 pip bleed)
  scored over 166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 44. Supporting events [26]; contradicting [9, 40].
What would kill it: Two consecutive 1.8-3.9 ATR bars in the same direction
produce a third 4 ATR bar within 3 no more often than a single 2 ATR bar does,
or they are already inside the known just-fell-hard lift.

Status forward_only: this has a split-sample backtest and NO forward record.
Confidence starts at 0.15 for that reason. NOT ARMED.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from ..admission import TradeIntent
from .dsp_spot_choice import spots_allow_emit

TAG = "dsp_cascade_last_two_not_yet_four"
ON_SURFACE: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD")

_WARMUP = 200
_STOP_ATR = 1.0
_TARGET_ATR = 6.0
_DIRECTION = -1          # +1 long / -1 short  — geometry first-touch 1.0/6.0


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
    """The discovered condition. Verbatim from SETUP_LIBRARY_V1.json."""
    n=len(c); out=np.zeros(n,dtype=bool)
    for t in range(4,n):
        a0=max(atr[t],1e-12); a1=max(atr[t-1],1e-12)
        b0=c[t]-o[t]; b1=c[t-1]-o[t-1]
        same=(b0*b1)>0
        big=abs(b0)>=1.8*a0 and abs(b1)>=1.8*a1
        notyet=abs(b0)<4.0*a0 and abs(b1)<4.0*a1
        out[t]=same and big and notyet
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
    pattern_side = "cascade_last_two_not_yet_four"
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
