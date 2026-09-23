"""dsp_huge_down_hold_then_spring -- discovered 2026-08-21 by the displacement precondition sweep.

A 2.2+ ATR down bar tags a 20-bar or 96-bar low. The next bar is a hold — body
under 1.2 ATR, close back inside or on the low, not another crash. Then price
springs. USDCZK 29 is the clean print: k=-2 is 4.56 ATR to 23.364, k=-1 is 0.95
ATR hold 23.368–23.382, 10:00 +4.06 with US30 already +4.52. CHFJPY 13 is almost
the same shape in one bar: 2.69 ATR onto 145.28, then +4.59 (no separate hold
bar). USDCNH 17: 2.47 ATR onto 7.2826 then +9.45. DOT 27: 3.04 ATR onto 5.240
then +4.20. The continue-downs (19, 22, 25) have no hold bar — k=-1 is the crash
and k=0 is more crash. GER40 18 has the crash-then-spring shape and dies because
the sister already chose down. Code the hold-after-crash geometry; leave the
sister as a prior, not a hard join, so 18 remains a listed contradiction.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.252%
  discovery 2014-2021 : lift 2.25x   n_fire 16,833   P(disp) 3.53%
  holdout   2022-2026 : lift 2.86x   n_fire 18,640   P(disp) 3.58%
  direction: 35% of displacements resolve UP  ->  V2 up-rate labelled SHORT (WRONG)
  geometry.py first-touch 1.0/6.0 LONG  hold R +0.208  (n_hold 19,334)
  (0.75/6.0 is best_both_halves +0.269; ship 1.0/6.0 to stay out of the FX 5-8 pip bleed)
  scored over 166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 42. Supporting events [13, 17, 27, 29]; contradicting [18, 19, 22, 25].
What would kill it: After a 2.2 ATR down tag of a 20/96-bar low followed by a
hold bar, a 4 ATR UP within 3 bars is no more common than after the same crash
with no hold (19, 22, 25), or GER40 18-style springs that die remain as common
as the ones that hold.

Status forward_only: this has a split-sample backtest and NO forward record.
Confidence starts at 0.15 for that reason. NOT ARMED.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from ..admission import TradeIntent
from .dsp_spot_choice import spots_allow_emit

TAG = "dsp_huge_down_hold_then_spring"
ON_SURFACE: tuple[str, ...] = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD")

_WARMUP = 200
_STOP_ATR = 1.0
_TARGET_ATR = 6.0
_DIRECTION = 1          # +1 long / -1 short  — geometry first-touch 1.0/6.0, NOT V2 up-rate


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
    """The discovered condition. Verbatim from verified_w2.json."""
    n=len(c); out=np.zeros(n,dtype=bool)
    for t in range(96,n):
        at=max(atr[t],1e-12)
        if abs(c[t]-o[t])>=3.0*at: continue
        found=False
        for k in (t, t-1, t-2):
            if (o[k]-c[k])<2.2*atr[k]: continue
            lo20=np.min(l[max(0,k-20):k]) if k else l[k]
            lo96=np.min(l[max(0,k-96):k]) if k else l[k]
            lvl=min(lo20, lo96)
            if l[k]>lvl+0.20*atr[k]: continue
            if k==t:
                rng=max(h[t]-l[t],1e-12)
                if (c[t]-l[t])/rng<=0.40 and (c[t]-l[k])<=0.80*at:
                    found=True; break
            else:
                held=abs(c[t]-o[t])<1.2*at and l[t]>=l[k]-0.15*at
                if held and (c[t]-l[k])<=0.80*at:
                    found=True; break
        out[t]=found
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
    pattern_side = "huge_down_hold_then_spring"
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
    try:
        _ex = float(np.min(l[max(0, i-20):i]) if i else l[i])
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
