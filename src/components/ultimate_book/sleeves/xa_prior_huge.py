"""xa_prior_huge -- timing setup 2026-08-21; geometry.py both-direction first-touch. Not armed.

The standing bar is already 2.5+ ATR and at least one of the prior eight bars was 2+ ATR the
same way. The labeled displacement is wave two or three of a cascade, not the first idea.
ETC 15 k=-1 is 6.86 then k=0 is 6.38. MBG 32 k=-2 is 2.17, k=-1 is 7.04, k=0 is 5.60. ADSGn
36 k=-1 is 2.49 then 4.28. This is the known last-bar-was-huge lift with the sequence the 30
features drop: isolated 5.45-style flushes (the snap cell) versus a sequence that continues.
If this cell has lift and the isolated-flush cell has the opposite lift, that is the
discriminator the existing 4.9x last-bar-huge setup cannot see. ETC 15 then fades (MAE 5.18)
— a cascade lead is not a hold lead.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.250%
  discovery 2014-2021 : lift 7.17x   n_fire 0   P(disp) 0.00%
  holdout   2022-2026 : lift 6.42x   n_fire 17,811   P(disp) 8.04%
  direction: library/V2 labelled SHORT (WRONG)
  geometry.py best_both_halves: LONG 1.0/6.0  hold R +0.149  (n_hold 18,553)
  (0.75/6.0 was +0.205; ship 1.0/6.0 to stay out of the FX 5-8 pip bleed)
  scored over 163/166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 41. Supporting events None; contradicting None.
What would kill it: A second same-way 2.5 ATR bar is followed by a third 4 ATR bar no more often than an isolated 2.5 ATR bar is (the known last-bar-huge cell), or the isolated bars continue as often as the sequences.

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

TAG = "xa_prior_huge"
SETUP_NAME = "already_huge_and_prior_huge_same_way"
GENERATE_KIND = "live"
ON_SURFACE: tuple[str, ...] = on_surface_for_process()

_WARMUP = 200
_STOP_ATR = 1.0
_TARGET_ATR = 6.0
_DIRECTION = 1          # +1 long / -1 short  — geometry best_both_halves, NOT V2 up-rate


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
    for t in range(12,n):
        last=abs(c[t]-o[t])>=2.5*max(atr[t],1e-12)
        same=any(abs(c[k]-o[k])>=2.0*max(atr[k],1e-12) and (c[k]-o[k])*(c[t]-o[t])>0 for k in range(t-8,t))
        out[t]=last and same
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
    return TradeIntent(
        sleeve=TAG,
        symbol=symbol,
        direction=_DIRECTION,
        decision_day=decision_day,
        stop_dist=_STOP_ATR * a,
        target_dist=_TARGET_ATR * a,
    )
