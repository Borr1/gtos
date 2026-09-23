"""dsp_descending_lows_accepted -- J2b from ALL36-GEOMETRY 2026-08-21. Not on live tags.

Three consecutive lower lows, the standing bar and the prior bar both closed down (or the
prior is a doji), and the four-bar close is already 0.5 ATR lower. The tape is walking, not
probing. ALG 16 is four down closes into 1.7052 then 6.97. COTTON 18 is k=-5/-3/-2/-1 each
making a new low then 6.12. GAL 19 is k=-4/-3/-1 down the stairs with a doji at k=-2, then
5.55. GBPJPY 3's last two bars before 09:15 are new lows but k=-1 is a tiny up bar, so it
fails the two-down-close test and stays on unreclaimed_washout. USDNOK 21 and COTTON 24
print descending lows after a prior up-drift and snap up — the ret16<=0 filter is the split.

MEASURED (never assumed, never up-rate):
  geometry.py best_both_halves LONG 0.75/6.0
  R_disc +0.127 (n=717,459)  R_hold +0.141 (n=954,488)
  formula evaluated bar-by-bar, causal, index <= i.

Status forward_only. Confidence 0.15. NOT ARMED. B1 remint only after J1/J5/J6 files exist.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from ..admission import TradeIntent
from .dsp_spot_choice import spots_allow_emit
from ._metals_choice import ask, decision_stops

TAG = "dsp_descending_lows_accepted"
ON_SURFACE: tuple[str, ...] = ('EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD')

_WARMUP = 200
_STOP_ATR = 0.75
_TARGET_ATR = 6.0
_DIRECTION = 1          # +1 long / -1 short — geometry.py, NOT V2 up-rate


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


def _signal(o, h, l, c, v, atr):
    """Return the causal ALL36 descending-lows boolean predicate."""
    atr_s = np.maximum(atr, 1e-12)
    n = len(c)
    out = np.zeros(n, dtype=bool)
    out[4:] = (
        (l[4:] < l[3:-1])
        & (l[3:-1] < l[2:-2])
        & (c[4:] < o[4:])
        & (c[3:-1] <= o[3:-1])
        & (c[4:] <= c[:-4] - 0.5 * atr_s[4:])
    )
    drift = np.zeros(n)
    drift[16:] = c[16:] - c[:-16]
    return out & (drift <= 0)


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
    pattern_side = "descending_lows_accepted"
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
    metals_hold = False
    if decision_stops(ask(
        "dsp_desc_surface",
        not on_surface,
        "off_surface_or_no_bars",
        "on_named_surface",
        "The symbol is off the named surface, or there are no bars.",
        "The symbol is on the named surface and bars exist.",
        symbol=symbol,
        n_bars=n,
    )):
        metals_hold = True
    if decision_stops(ask(
        "dsp_desc_warmup",
        n < _WARMUP,
        "bars_short_of_200",
        "warmup_complete",
        "The sleeve warmup of 200 bars is not met.",
        "The sleeve warmup of 200 bars is complete.",
        symbol=symbol,
        n=n,
    )):
        metals_hold = True
    if decision_stops(ask(
        "dsp_desc_shape",
        not shape_matches,
        "signal_shape_mismatch",
        "signal_shape_matches",
        "The signal shape does not match the closes.",
        "The signal shape matches the closes.",
        symbol=symbol,
        n=n,
    )):
        metals_hold = True
    if decision_stops(ask(
        "dsp_desc_pattern",
        not pattern_printed,
        "pattern_absent",
        "descending_lows_accepted",
        "The descending-lows predicate is absent on this bar.",
        "Three consecutive lower lows are accepted on this bar.",
        symbol=symbol,
        i=i,
    )):
        metals_hold = True
    if decision_stops(ask(
        "dsp_desc_atr",
        atr_scale is None,
        "atr_not_a_scale",
        "atr_positive",
        "ATR cannot scale the 0.75 and 6.0 distances.",
        "ATR can scale the 0.75 and 6.0 distances.",
        symbol=symbol,
        atr=atr_scale,
    )):
        metals_hold = True
    dsp_emit = spots_allow_emit(facts, spots, cache_key)
    fear_hold = False
    if timing_fact:
        try:
            from ..minimal_size import fear_withholds
            if fear_withholds(
                "stay_timing",
                {
                    "symbol": symbol,
                    "sleeve": TAG,
                    "index": int(i),
                    "pattern_printed": True,
                    "namespace": "operator",
                },
                {
                    "pattern_already_accepted": "The pattern already accepted this bar. Emit the intent.",
                    "still_timing": "Stay in timing. Do not emit this intent.",
                },
                "still_timing",
                f"stay_timing|{symbol}|{i}",
                "The descending-lows pattern already printed on this bar, and a second timing check is true. Is the pattern the intent, or does timing still withhold it?",
            ):
                fear_hold = True
        except Exception:
            pass
    if metals_hold or not dsp_emit or fear_hold:
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
