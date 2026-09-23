"""xa_second_leg -- timing setup 2026-08-21; geometry.py both-direction first-touch. Not armed.

The bar you are standing on is already a 3+ ATR body that closed on its extreme, and the six
bars before it were ordinary. The algorithms that made the first bar are still in the
market; the named displacement is the second push in the same direction. Event 1: Monday
16:30 already 4.67 ATR after the weekend, 16:45 another 4.03. Event 3: Tuesday 15:30 already
5.83 ATR, 15:45 another 7.38. Event 9: twelve hours stuck at 338.21, 05:15 already 5.25 ATR,
05:30 another 6.67. 'Last bar huge' is a known lift; the extra is that this huge bar is the
FIRST expansion after quiet, not one more bar in an already-broken range.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.250%
  discovery 2014-2021 : lift 5.92x   n_fire 0   P(disp) 0.00%
  holdout   2022-2026 : lift 6.39x   n_fire 17,132   P(disp) 8.00%
  direction: library LONG agrees with geometry
  geometry.py best_both_halves: LONG 1.0/6.0  hold R +0.227  (n_hold 18,179)
  (0.75/6.0 was +0.324; ship 1.0/6.0 to stay out of the FX 5-8 pip bleed)
  scored over 163/166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 20. Supporting events None; contradicting None.
What would kill it: After a first >=3 ATR bar that follows six ordinary bars, a second >=4 ATR bar in the same direction within 3 bars is no more common than after any >=3 ATR bar, or the next expansion is as often the other way (5 last-bar dump then UP; 16 and 26 last-bar up into the 20-high then DOWN; 34 last-bar down then UP).

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

TAG = "xa_second_leg"
SETUP_NAME = "second_leg_after_first_expansion"
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
    sig = (np.abs(c-o) >= 3.0*atr) & (np.abs(c-o) >= 0.85*np.maximum(h-l, 1e-12)) & (np.array([np.max(np.abs(c[max(0,i-6):i]-o[max(0,i-6):i])) < 1.2*np.max(atr[max(0,i-6):i]) if i>=6 else False for i in range(len(c))]))
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
