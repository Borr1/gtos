"""vol_compression.py — NEW SLEEVE: volatility-compression -> range-breakout (D1, crypto).

2nd genuinely-new sleeve from the new-sleeve factory (2026-06-17), PRINCIPAL-VERIFIED on BTC/ETH/XTZ D1:
every-split-positive at real cost (train +0.242 / oos +0.246 / sealed +0.383), placebo random-bar p=0.0033 /
shuffle p=0.001, corr_to_book -0.028 (orthogonal). DISTINCT from the deployed ac60-momentum crypto sleeve:
adding an ac60 persistence gate KILLS it -> it is a vol-STATE mechanic, not momentum. Plateau-robust (squeeze_q
in [0.3,0.4], break_lb [10,20], target 1.5-3R, stop 1-2 ATR all every-split-positive) + survives 0.15R cost.
Verified gen: research/.../gen_sleeve_crypto_and_altcrypto.py (C3_compression_breakout_q40_br20_tgt3).

MECHANIC (leak-free, decides on the latest CLOSED D1 bar i): SQUEEZE = ATR14[i] below the squeeze_q quantile of
the last HIST_LB ATRs (volatility compression). BREAKOUT = close[i] breaks the prior BREAK_LB-bar high/low ->
trade the break direction. stop = STOP_MULT*ATR, target = TARGET_R*stop. The channel uses only bars [i-BREAK_LB, i)
and the ATR history [i-HIST_LB, i) -> no look-ahead; entry at close[i]. DEFAULT-OFF candidate (not in live BUILT).
"""
from __future__ import annotations
from typing import Optional
from ..primitives import atr14
from ..admission import TradeIntent

# verified C3 config (q40/br20/tgt3, stop 1.5 ATR, no ac gate)
SQUEEZE_Q = 0.40
BREAK_LB = 20
STOP_MULT = 1.5
TARGET_R = 3.0
HIST_LB = 100
MIN_HIST = 50
ON_SURFACE = ("BTCUSD", "ETHUSD", "XTZUSD")   # verified deep crypto; the mega-factory may extend (XRP 2017+)


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Emit a compression-breakout TradeIntent on the latest closed (D1) bar, else None. Leak-free."""
    if symbol not in ON_SURFACE or not bars:
        return None
    i = len(bars) - 1
    if i < max(HIST_LB, BREAK_LB) + 1:
        return None
    A = [atr14(bars, k) for k in range(len(bars))]
    a = A[i]
    if a <= 0:
        return None
    hist = [A[k] for k in range(i - HIST_LB, i) if A[k] > 0]
    if len(hist) < MIN_HIST:
        return None
    thr = sorted(hist)[int(SQUEEZE_Q * len(hist))]
    if a > thr:
        return None                                  # not compressed -> no squeeze
    hh = max(bars[k].h for k in range(i - BREAK_LB, i))   # prior-bar channel (no lookahead)
    ll = min(bars[k].l for k in range(i - BREAK_LB, i))
    c = bars[i].c
    d = 1 if c > hh else (-1 if c < ll else 0)
    if d == 0:
        return None
    sd = STOP_MULT * a
    if sd <= 0:
        return None
    return TradeIntent(sleeve="vol_compression", symbol=symbol, direction=d, decision_day=decision_day,
                       stop_dist=sd, target_dist=TARGET_R * sd)
