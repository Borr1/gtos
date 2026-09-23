"""xa_huge_same_way -- timing setup 2026-08-21; geometry.py both-direction first-touch. Not armed.

The standing bar is already 2.0-3.8 ATR in one direction and is not a two-sided washout (it
did not also tag the opposite 20-bar extreme). The named displacement is wave two. CADJPY 7
is 2.53 down to 104.15 then 6.95 more; AAV 16 is 2.17 then 5.22; EU50 27 is 2.73 then 4.57
after a 3.94 first break at 09:00; SAN 39 is 2.36 then 4.10. MSTR 23 is 2.07 then 4.49 on a
Friday 21:45 sparse tape, then Monday gaps through the print (MFE -4.06) — the fire is wave
two, the hold is a weekend hole. ASML 30 is the same movie with the standing bar already
11.99 — exclude that with a 4 ATR cap or you are inside the event. Opposite movie is NZDJPY
13 (5.06 washout then UP) and the isolated continuation trap USDMXN 38 (2.13 then 5.38 then
fully dead). Discriminator versus 13: the huge bar did not tag the opposite 20-bar extreme.
Discriminator versus 38 is after-quality, not a fire.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.250%
  discovery 2014-2021 : lift 3.38x   n_fire 0   P(disp) 0.00%
  holdout   2022-2026 : lift 3.41x   n_fire 175,805   P(disp) 4.27%
  direction: library/V2 labelled SHORT (WRONG)
  geometry.py best_both_halves: LONG 0.75/6.0  hold R +0.107  (n_hold 183,428)
  scored over 163/166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 47. Supporting events None; contradicting None.
What would kill it: A 2.0-3.8 ATR one-sided bar with at least one same-direction prior bar produces a same-way 4 ATR bar within 3 no more often than the 1.6% base rate, or the 13 washout-reversal and 38 isolated-spike families remain as common after the opposite-extreme exclusion.

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

TAG = "xa_huge_same_way"
SETUP_NAME = "already_huge_same_way_wave_two"
GENERATE_KIND = "stub"  # 1.0/6.0 hold R +0.085 misses +0.12; do not fake live
ON_SURFACE: tuple[str, ...] = on_surface_for_process()

_WARMUP = 200
_STOP_ATR = 0.75
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
    for t in range(24,n):
        at=max(atr[t],1e-12)
        body=c[t]-o[t]
        if abs(body)<2.0*at or abs(body)>=4.0*at: continue
        hh=np.max(h[t-19:t+1]); ll=np.min(l[t-19:t+1])
        if body<0:
            if l[t]<=ll+0.12*at and h[t]>=hh-0.12*at: continue
            prior=sum(1 for i in range(t-3,t) if c[i]<o[i])>=1
            out[t]=prior
        else:
            if h[t]>=hh-0.12*at and l[t]<=ll+0.12*at: continue
            prior=sum(1 for i in range(t-3,t) if c[i]>o[i])>=1
            out[t]=prior
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
