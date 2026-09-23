"""xa_wide_extreme -- timing setup 2026-08-21; geometry.py both-direction first-touch. Not armed.

The bar you are standing on is already a 2.2+ ATR body that closed on its extreme. The named
4-ATR bar is wave two, not the break. NER (7) k=-1 is 4.22 ATR to 1.938 after an unreclaimed
walk off 2.021, then 6.13 more. UNI (2) k=-1 is 2.42 ATR to the 24h low 10.143, then 11.65.
NATGAS (11) k=-1 is 3.68 ATR through 2.727 after a held reclaim, then 5.04. The known 4.9x
lift is 'last bar huge'. The extra is the extreme it printed: cascade low after an
unreclaimed earlier impulse continues DOWN; V-reclaim high continues UP. EURCZK (9) is why a
raw last-bar-huge rule cannot be a direction: 16.12 ATR after a 15-bar freeze, next bar
another 14.92, then MAE 76. NZDCHF (12) k=-1 is 1.91 ATR down and the next bar springs UP.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.250%
  discovery 2014-2021 : lift 5.86x   n_fire 0   P(disp) 0.00%
  holdout   2022-2026 : lift 5.17x   n_fire 22,943   P(disp) 6.47%
  direction: library/V2 labelled LONG (WRONG)
  geometry.py best_both_halves: SHORT 1.0/6.0  hold R +0.121  (n_hold 23,695)
  (0.75/6.0 was +0.168; ship 1.0/6.0 to stay out of the FX 5-8 pip bleed)
  scored over 163/166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 45. Supporting events None; contradicting None.
What would kill it: A 2.2 ATR bar that printed a new 20-extreme continues with a 4 ATR bar the same way no more often than any 2.2 ATR bar (the known last-bar-huge lift with no extra), or event-9 / event-12 reversals match the continuations.

Status forward_only: this has a split-sample backtest and NO forward record.
Confidence starts at 0.15 for that reason.
"""
from __future__ import annotations
from .account_surface import on_surface_for_process

from typing import Optional

import numpy as np

from ..admission import TradeIntent
from ..xasset_direction import stay_timing
from .spot_choice import all_false, ask, bar_id

TAG = "xa_wide_extreme"
SETUP_NAME = "already_wide_bar_same_extreme"
GENERATE_KIND = "live"
ON_SURFACE: tuple[str, ...] = on_surface_for_process()

_WARMUP = 200
_STOP_ATR = 1.0
_TARGET_ATR = 6.0
_DIRECTION = -1          # +1 long / -1 short  — geometry best_both_halves, NOT V2 up-rate


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
    """The discovered condition. Verbatim from the verified proposal."""
    n=len(c); out=np.zeros(n,dtype=bool)
    for t in range(20,n):
        if abs(c[t]-o[t])<2.2*atr[t]: continue
        if c[t]<o[t]:
            if l[t]>np.min(l[t-19:t+1])+0.2*atr[t]: continue
            if (c[t]-c[t-16]) > -6.0*atr[t]: continue
            ok=False
            for j in range(t-2, max(t-16,0)-1, -1):
                if (o[j]-c[j])>=1.5*atr[j] and np.max(h[j+1:t+1])<=o[j]+0.15*atr[t]:
                    ok=True; break
            if not ok: continue
            out[t]=True
        else:
            if h[t]<np.max(h[t-19:t+1])-0.2*atr[t]: continue
            ok=False
            for j in range(t-1, max(t-6,0)-1, -1):
                if (c[j]-o[j])>=1.5*atr[j] and np.min(l[j+1:t+1])>=o[j]-0.15*atr[t]:
                    ok=True; break
            if not ok: continue
            out[t]=True
    out
    sig = out
    return sig


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    if not bars:
        return None
    n = len(bars)
    i = n - 1
    on_surface = symbol in ON_SURFACE
    warmup_short = n < _WARMUP
    pattern_absent = True
    stay = False
    arrays = None
    a = float("nan")
    if not warmup_short:
        o, h, l, c, v, atr = _arrays(bars)
        arrays = (o, h, l, c, v, atr)
        try:
            sig = np.asarray(_signal(o, h, l, c, v, atr))
        except Exception:
            return None
        if getattr(sig, "shape", None) != c.shape:
            return None
        pattern_absent = not bool(sig[i])
        a = float(atr[i])
        if (a > 0.0) and np.isfinite(a) and not pattern_absent:
            stay = bool(stay_timing(SETUP_NAME, {"symbol": symbol, "index": i}, _.get("peer_panel")))
    sides = ask(
        sleeve=TAG,
        symbol=symbol,
        bar_id=bar_id(decision_day, n, bar_time, bar_times),
        spots={
            "off_surface": {
                "condition": f"symbol {symbol} is not in ON_SURFACE",
                "measured": not on_surface,
            },
            "warmup_short": {
                "condition": f"closed bar count {n} is below warmup {_WARMUP}",
                "measured": warmup_short,
            },
            "pattern_absent": {
                "condition": f"the latest closed bar does not print {SETUP_NAME}",
                "measured": pattern_absent,
            },
            "stay_timing": {
                "condition": f"stay_timing still holds for {SETUP_NAME} on {symbol} at the latest closed bar",
                "measured": stay,
            },
        },
    )
    if not all_false(sides):
        return None
    if arrays is None or not (a > 0.0) or not np.isfinite(a):
        return None
    o, h, l, c, v, atr = arrays
    try:
        _pick = np.min(l[i-19:i+1]) if c[i] < o[i] else np.max(h[i-19:i+1])
        _ex = float(_pick)
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
