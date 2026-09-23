"""vol_squeeze.py — NEW SLEEVE: volatility-squeeze -> trend-gated expansion breakout (H4).

The FIRST genuinely-new sleeve from the universe-wide new-sleeve factory (2026-06-17), PRINCIPAL-VERIFIED:
on indices (GER40/UK100/SPX500/NAS100 H4) it is every-split-positive at real cost (train +0.243 / oos +0.129 /
sealed +0.227), placebo random-entry p=0.003, corr_to_book -0.111 (orthogonal to the metals-centric book),
~156 trades/yr. The NEGATIVE CONTROL (a shape-based coil breakout WITHOUT the ATR-percentile vol-state) is NULL
every split -> the edge IS the vol-state (compression -> expansion), not bar shape. Positive every year incl the
2022 bear (+0.083) and all 4 symbols + leave-one-out -> NOT the c78 Donchian regime-inflation wall. Verified
gen: research/.../gen_sleeve_indices_structural_reversion_v3.py (F1_squeeze_expansion).

MECHANIC (leak-free, decides on the latest CLOSED bar i): SQUEEZE = current ATR14[i] regime compressed (the mean
ATR over the last comp_lb bars is in the LOW sq_pct quantile of the last med_lb ATRs) AND EXPANSION = bar i range
>= exp_k*ATR with a body >= body_frac of range, taken ONLY in the HTF-trend direction. stop = struct + stop_buf*ATR,
target = TARGET_R * stop. Every feature is at index <= i (no look-ahead). DEFAULT-OFF candidate sleeve (not in the
live BUILT registry) until the ultimate-system assembly + owner approval.
"""
from __future__ import annotations
from typing import Optional
from ..primitives import atr14
from ..admission import TradeIntent
from .spot_choice import all_false, ask, bar_id

# verified RANK1 config (F1_squeeze_expansion, comp_lb=12/sq_pct=0.25/exp_k=1.1/trend_lb=50, target 3R)
COMP_LB = 12
SQ_PCT = 0.25
EXP_K = 1.1
TREND_LB = 50
BODY_FRAC = 0.4
STOP_BUF = 0.30
MED_LB = 60
TARGET_R = 3.0
# verified indices. US30_cash added 2026-06-17 from the MEGA indices-extended factory + principal re-derivation
# (verify_us30_vol_squeeze.py): n=364 +0.1514, every-split+ (train +0.059/oos +0.291/sealed +0.078), random-entry
# placebo p=0.0020, neg-control NULL (-0.068), corr_book -0.137, ~49 tr/yr. HONEST CAVEAT: US30 is a US-large-cap
# sibling of SPX500/NAS100 -> correlated US-beta breadth, NOT net-new orthogonal diversification; train is weak
# (oos-heavy). The full 11-index extended family is NOT added (pooled placebo p=0.223 = extended-dilution).
ON_SURFACE = ("GER40", "UK100", "SPX500", "NAS100")
SLEEVE = "vol_squeeze"


def _htf_trend(B, i, lb):
    """close-vs-close(lb) magnitude vs 1*ATR (the standard HTF trend gate; +1/-1/0)."""
    if i < lb:
        return 0
    a = atr14(B, i)
    if a <= 0:
        return 0
    diff = B[i].c - B[i - lb].c
    return 1 if diff > a else (-1 if diff < -a else 0)


def measured(symbol, bars) -> dict:
    """Facts for the latest closed bar. Not a decision."""
    i = len(bars) - 1 if bars else -1
    warmup_short = i < MED_LB + COMP_LB + 15
    a = 0.0
    trend = 0
    no_window = True
    not_squeezed = True
    not_expansion = True
    body_against = True
    stop = 0.0
    direction = 0
    if bars and not warmup_short:
        A = [atr14(bars, k) for k in range(len(bars))]
        a = A[i]
        trend = _htf_trend(bars, i, TREND_LB)
        window = sorted(A[i - MED_LB:i])
        no_window = not window
        if window and a > 0:
            thr = window[int(SQ_PCT * len(window))]
            recent = A[i - COMP_LB:i]
            not_squeezed = (not recent) or (sum(recent) / len(recent)) > thr
        b = bars[i]
        rng = b.h - b.l
        not_expansion = rng < EXP_K * a if a > 0 else True
        body = b.c - b.o
        if trend == 1 and body > BODY_FRAC * rng and rng > 0:
            direction = 1
            stop = max(b.c - b.l, 0.0) + STOP_BUF * a
            body_against = False
        elif trend == -1 and body < -BODY_FRAC * rng and rng > 0:
            direction = -1
            stop = max(b.h - b.c, 0.0) + STOP_BUF * a
            body_against = False
    return {
        "off_surface": symbol not in ON_SURFACE,
        "warmup_short": warmup_short,
        "atr_not_a_scale": not (a > 0),
        "no_htf_trend": trend == 0,
        "no_median_window": no_window,
        "not_squeezed": not_squeezed,
        "not_expansion": not_expansion,
        "body_against_trend": body_against,
        "direction": direction,
        "stop": float(stop),
        "atr": float(a),
    }


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Vol-squeeze expansion on indices. Each gate is one spot Choice."""
    if not bars:
        return None
    facts = measured(symbol, bars)
    sides = ask(
        sleeve=SLEEVE,
        symbol=symbol,
        bar_id=bar_id(decision_day, len(bars), bar_time, bar_times),
        spots={
            "off_surface": {
                "condition": f"{symbol} is not one of GER40, UK100, SPX500, NAS100",
                "measured": facts["off_surface"],
            },
            "warmup_short": {
                "condition": f"closed H4 count is below {MED_LB + COMP_LB + 15}",
                "measured": facts["warmup_short"],
            },
            "atr_not_a_scale": {
                "condition": "ATR14 is not a positive scale",
                "measured": facts["atr_not_a_scale"],
            },
            "no_htf_trend": {
                "condition": "close versus close 50 bars ago is inside 1 ATR",
                "measured": facts["no_htf_trend"],
            },
            "no_median_window": {
                "condition": "the 60-bar ATR window is empty",
                "measured": facts["no_median_window"],
            },
            "not_squeezed": {
                "condition": "mean ATR over the last 12 bars is above the low quartile of the last 60",
                "measured": facts["not_squeezed"],
            },
            "not_expansion": {
                "condition": "bar range is below 1.1 ATR",
                "measured": facts["not_expansion"],
            },
            "body_against_trend": {
                "condition": "the bar body is not with the higher-timeframe trend at 0.4 of the range",
                "measured": facts["body_against_trend"],
            },
        },
    )
    if not all_false(sides):
        return None
    if facts["direction"] not in (1, -1) or not (facts["stop"] > 0):
        return None
    return TradeIntent(
        sleeve=SLEEVE,
        symbol=symbol,
        direction=facts["direction"],
        decision_day=decision_day,
        stop_dist=facts["stop"],
        target_dist=TARGET_R * facts["stop"],
    )
