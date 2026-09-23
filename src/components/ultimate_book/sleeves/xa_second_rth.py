"""xa_second_rth -- timing setup 2026-08-21; geometry.py both-direction first-touch. Not armed.

The first bar of a session (or the first large bar after a long hole) is already 2+ ATR and
closed in its direction. The next bar is the named displacement — wave two of the open
drive. BAC 19: 16:30 is 2.38 ATR to 41.81 on 9.80×, 16:45 is 4.59 and it held. RTX 22: 15:30
is already 6.93 ATR to 121.61, 15:45 is 5.77 and it held (MFE 3.64). LNK 11 is the 01:00
cousin on crypto (2.97 then 5.86). This is not the known 'last bar was huge' measured on a
continuous tape; it is specifically the second print after a drive that already took the
20-high or 20-low. VOW 35 is wave two but not an open. NVDA 5's first print IS the
displacement, so there is no standing bar that is already the drive.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.250%
  discovery 2014-2021 : lift 3.81x   n_fire 0   P(disp) 0.00%
  holdout   2022-2026 : lift 4.10x   n_fire 145,376   P(disp) 5.13%
  direction: library/V2 labelled SHORT (WRONG)
  geometry.py best_both_halves: LONG 0.75/6.0  hold R +0.143  (n_hold 151,030)
  scored over 163/166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 39. Supporting events None; contradicting None.
What would kill it: After a 2+ ATR first drive that already tagged the 20-high or 20-low, the next bar is 4 ATR in the same direction no more often than the known last-bar-huge lift, or the next bar reverses as often (the 5-style fade).

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

TAG = "xa_second_rth"
SETUP_NAME = "second_rth_bar_after_open_drive"
GENERATE_KIND = "stub"  # 1.0/6.0 hold R +0.105 misses +0.12; do not fake live
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
        body=abs(c[t]-o[t])
        rng=max(h[t]-l[t],1e-12)
        hh=np.max(h[t-19:t+1]); ll=np.min(l[t-19:t+1])
        up=(c[t]>o[t]) and (body>=2.0*at) and (c[t]>=l[t]+0.70*rng) and (hh-h[t])<=0.15*at
        dn=(c[t]<o[t]) and (body>=2.0*at) and (c[t]<=l[t]+0.30*rng) and (l[t]-ll)<=0.15*at
        out[t]=(up or dn) and (body<8.0*at)
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
