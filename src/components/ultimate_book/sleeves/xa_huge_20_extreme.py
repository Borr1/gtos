"""xa_huge_20_extreme -- timing setup 2026-08-21; geometry.py both-direction first-touch. Not armed.

Bar t is already 2.5-7.5 ATR and its close is within 0.15 ATR of the 20-bar high or low.
That is not 'last bar was huge' alone — it is last bar huge AND finished on the level. When
it finishes on the 20-bar low (Events 19, 28), the next displacement was the opposite
snapback. When it finishes on the 20-bar high (Events 17, 25), the next displacement
continued. Test both legs; do not collapse them.

MEASURED (never assumed):
  displacement within 3 bars, base rate 1.250%
  discovery 2014-2021 : lift 5.68x   n_fire 0   P(disp) 0.00%
  holdout   2022-2026 : lift 5.46x   n_fire 25,242   P(disp) 6.84%
  direction: library LONG agrees with geometry
  geometry.py best_both_halves: LONG 1.0/6.0  hold R +0.150  (n_hold 26,537)
  (0.75/6.0 was +0.207; ship 1.0/6.0 to stay out of the FX 5-8 pip bleed)
  scored over 163/166 instruments; formula evaluated bar-by-bar, causal, index <= i.

Proposed by swarm shard 00. Supporting events None; contradicting None.
What would kill it: The close-on-low and close-on-high cells have the same next-bar direction mix as 'last bar was huge' with no extra lift. Event 13's 3.83 ATR bar at k=-7 closed on the new high and did not produce another 4-ATR bar within 3 bars — if that timing miss is the common case, the cell fires too early.

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

TAG = "xa_huge_20_extreme"
SETUP_NAME = "huge_bar_closed_on_20bar_extreme"
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
    atr_s = np.maximum(atr, 1e-12); body = np.abs(c - o); n = len(c); sig = np.zeros(n, dtype=bool)
    for t in range(20, n):
        huge = (body[t] >= 2.5 * atr_s[t]) and (body[t] < 8.0 * atr_s[t])
        lo20, hi20 = np.min(l[t-19:t+1]), np.max(h[t-19:t+1])
        on_lo = c[t] <= lo20 + 0.15 * atr_s[t]
        on_hi = c[t] >= hi20 - 0.15 * atr_s[t]
        sig[t] = huge and (on_lo or on_hi)
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
    _lo20 = np.min(l[i-19:i+1]); _hi20 = np.max(h[i-19:i+1])
    _atr_s = max(float(atr[i]), 1e-12)
    _on_lo = c[i] <= _lo20 + 0.15 * _atr_s
    _pick = _lo20 if _on_lo else _hi20
    try:
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
