"""xa_wave_two_standing -- timing setup 2026-08-21; geometry.py both-direction first-touch. Not armed.

The standing bar is already a 2.0–3.8 ATR body closing in its own direction. The named 4-ATR
bar is the next impulse, not the first idea. A person sees they are already in the move; the
30 features score last_range as a precondition. LNK 11: 2.97 ATR to 13.493, then 5.86 and it
held (MFE 3.14). BAC 19: 16:30 already 2.38 ATR on the high, then 4.59 and it held. MBG 33:
2.64 ATR down, then 8.33. RTX 22 (6.93) and VOW 35 (4.44) are the same story past the 3.8
cap — listed as contradictions to the cap, support to the story. Direction is the sign of
the standing bar. Session-gap 'wave twos' (KO 15's Wednesday 2.68 ATR) do not fire within 3
continuous bars.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.250%
  discovery 2014-2021 : lift 3.15x   n_fire 0   P(disp) 0.00%
  holdout   2022-2026 : lift 3.28x   n_fire 168,399   P(disp) 4.11%
  direction: library/V2 labelled SHORT (WRONG)
  geometry.py best_both_halves: LONG 0.75/6.0  hold R +0.110  (n_hold 176,127)
  scored over 163/166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 39. Supporting events None; contradicting None.
What would kill it: A 2.0–3.8 ATR standing bar produces a same-direction 4-ATR bar within 3 no more often than the known 'last bar was huge' lift already measured, or reversals of that first large bar are as common.

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

TAG = "xa_wave_two_standing"
SETUP_NAME = "wave_two_standing_bar_already_large"
GENERATE_KIND = "stub"  # 1.0/6.0 hold R +0.084 misses +0.12; do not fake live
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
    for t in range(8,n):
        at=max(atr[t],1e-12)
        body=abs(c[t]-o[t])
        rng=max(h[t]-l[t],1e-12)
        big=(body>=2.0*at) and (body<3.8*at)
        directed=((c[t]>o[t]) and (c[t]>=l[t]+0.70*rng)) or ((c[t]<o[t]) and (c[t]<=l[t]+0.30*rng))
        first=abs(c[t-1]-o[t-1])<2.0*max(atr[t-1],1e-12)
        out[t]=big and directed and first
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
