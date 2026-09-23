"""xa_climax_spring -- timing setup 2026-08-21; geometry.py both-direction first-touch. Not armed.

The bar you are standing on IS a 2.8+ ATR down bar that makes the 20-bar low for the first
time and closes on that low. That is exhaustion, not acceptance — too much too fast, the
book is empty of sellers, the next expansion is the buyback. NZDCHF (16) crashed 3.84 ATR
from 0.46414 to 0.46311, swept both the 20-high and 20-low flags on the way, closed on the
low, then 21:00 reversed UP 4.37 ATR. This is the opposite of the 0.8-1.5 ATR close-on-low
after a multi-hour bleed (7, 10) and of PLTR's 2.60 ATR gap-open that continued DOWN (8). A
sweep-true bit and a close_pos column cannot see the SIZE of the touch bar. Do not use the
printed close_pos row — on this card it is the spring bar.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.250%
  discovery 2014-2021 : lift 5.70x   n_fire 0   P(disp) 0.00%
  holdout   2022-2026 : lift 6.44x   n_fire 17,492   P(disp) 8.06%
  direction: library/V2 labelled SHORT (WRONG)
  geometry.py best_both_halves: LONG 1.0/6.0  hold R +0.291  (n_hold 18,263)
  (0.75/6.0 was +0.377; ship 1.0/6.0 to stay out of the FX 5-8 pip bleed)
  scored over 163/166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 36. Supporting events None; contradicting None.
What would kill it: A 2.8+ ATR first-touch of the 20-low that closes on the low is followed by a >=4 ATR UP bar within 3 no more often than any 2.8 ATR down bar, or the accept-and-continue cases (7, 8, 10) match the springs.

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

TAG = "xa_climax_spring"
SETUP_NAME = "climax_first_touch_20low_springs"
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
    atr_s = np.maximum(atr, 1e-12); n = len(c); sig = np.zeros(n, dtype=bool)
    for t in range(24, n):
        rng = h[t] - l[t]
        if rng <= 0:
            continue
        prior_ll = np.min(l[t-19:t])
        prior_dump = np.max(o[t-8:t] - c[t-8:t]) if t >= 8 else 0.0
        sig[t] = ((o[t] - c[t]) >= 2.8 * atr_s[t]) and (l[t] <= prior_ll - 0.15 * atr_s[t]) and ((c[t] - l[t]) / rng <= 0.15) and (prior_dump < 2.0 * atr_s[t])
    sig
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
        _ex = float(np.min(l[i-19:i]))
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
