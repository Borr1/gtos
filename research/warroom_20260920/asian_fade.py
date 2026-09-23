"""asian_fade.py — NEW SLEEVE: Asian-range break -> reversion fade with trail exit (M15, FX majors).

3rd genuinely-new sleeve (2026-06-17), PRINCIPAL-VERIFIED on EURUSD/GBPUSD M15 — a NON-momentum intraday
reversion edge, orthogonal to the HTF momentum book. The Asian session range (server hours 0..7) is built,
and the FIRST break beyond it during London/NY (hours 8..21) that shows a rejection wick is FADED back toward
the range. Verified every-split-positive at real cost:
    EURUSD +0.176 (train +0.142 / oos +0.241 / sealed +0.228), 3198 trades, positive EVERY YEAR 2014-2026
    GBPUSD +0.174 (train +0.167 / oos +0.191 / sealed +0.173), 3194 trades, positive every split
CORRECT NULL (the load-bearing proof — see CMAP_SRMR_ASIANFADE_VERDICT.md + CMAP_SRMR_CORRECT_PLACEBO.json):
the ENTRY beats a random-entry-SAME-TRAIL control by 6-8 SD (EURUSD obs +0.176 vs random-entry null +0.040;
with direction held fixed and only timing randomized, random = +0.001). The edge is the ENTRY/TIMING, not an
exit artifact. (The original gen placebo was a sign-flip bootstrap-vs-zero = the WRONG null; this is the right one.)

EXIT = TRAIL (arm/gap in stop-units). Fixed-R KILLS the edge (it is a reversion-scalp that needs to ride the
return move) -> this sleeve REQUIRES the trail exit. primitives.simulate supports trail_arm/trail_gap; the
TradeIntent contract carries only stop_dist/target_dist, so this generator emits target_dist=None and declares
its trail spec via TRAIL_ARM/TRAIL_GAP (the live execution path trails per these). DEFAULT-OFF candidate (not in
the live BUILT registry) until ultimate-system assembly + owner approval.

COST NOTE (owner directive 2026-06-17): cost is a small FIXED-DOLLAR amount (~$10), immaterial vs the captured
move; cost-in-R on a tight stop overstates it and is NOT a kill criterion. The edge is judged on predictive
quality (beats-random null + every-split + every-year), which it passes. Reference cost sweep in the verdict.

MECHANIC (leak-free, decides on the latest CLOSED M15 bar i during London/NY): builds today's Asian range from
same-day bars at hour<=7; if bar i is the FIRST same-day London/NY bar to break [Alo-buf, Ahi+buf] (buf=BUF_K*ATR)
with a rejection wick (>= REJECT_FRAC*ATR back inside), FADE it (short up-break / long down-break). stop = STOP_K*ATR;
exit = trail. Only same-day bars <= i are used (the Asian range is hours 0..7, strictly before the hour>=8 entry).
"""
from __future__ import annotations
from typing import Optional
from ..primitives import atr14
from ..admission import TradeIntent
from ._server_clock import server_day, server_hour

# verified config (gen_cmap_session_mean_reversion_rangefade.gen_asian_fade target_mode="trail")
BUF_K = 0.25         # break buffer in ATR units beyond the Asian range
STOP_K = 0.6         # stop distance in ATR units (the tight reversion-scalp stop the edge needs)
REJECT_FRAC = 0.15   # required rejection wick back inside, in ATR units
TRAIL_ARM = 0.5      # trail arms once price moves TRAIL_ARM*stop in favor (stop-units)
TRAIL_GAP = 0.5      # trailing stop sits TRAIL_GAP*stop behind the best excursion (stop-units)
MAXBARS = 48         # time-stop (bars)
MIN_BARS = 200       # context warmup
ASIAN_END_HOUR = 7   # Asian range = same-day bars at hour <= 7 (server-local EET)
ENTRY_LO_HOUR = 8    # London/NY entry window
ENTRY_HI_HOUR = 21
MIN_ASIAN_BARS = 6   # need >= this many Asian bars to define the range
ON_SURFACE = ("EURUSD", "GBPUSD")   # robust every-split + beats-null pair; USDJPY/AUDUSD weakly+ (extension)


def _hour(t):
    """SERVER-LOCAL hour. The session constants here are FTMO server hours (F7/B29); the
    live feed is true UTC, so this converts before comparing. None -> fail closed."""
    return server_hour(t)


def _day(t):
    """SERVER-LOCAL date key. The route grouped prior-day levels and session ranges on
    SERVER days, not UTC days (F7/B29). NOT the correlated-unit key. None -> fail closed."""
    return server_day(t)


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Emit an Asian-range fade TradeIntent on the latest closed M15 bar, else None. Leak-free.

    Requires bar_times (datetimes or ISO strings aligned 1:1 with bars) to resolve session hour + day.
    Exit is a TRAIL (TRAIL_ARM/TRAIL_GAP in stop-units); target_dist is None by design.
    """
    if symbol not in ON_SURFACE or not bars or not bar_times:
        return None
    i = len(bars) - 1
    if i < MIN_BARS or len(bar_times) != len(bars):
        return None
    hi = _hour(bar_times[i])
    if hi is None or hi < ENTRY_LO_HOUR or hi > ENTRY_HI_HOUR:
        return None                                   # only decide on a London/NY bar
    day = _day(bar_times[i])
    if day is None:
        return None
    a = atr14(bars, i)
    if a <= 0:
        return None

    # same-day bar indices (only bars <= i are visible -> leak-free). NOTE: hour 0 (midnight) is a
    # valid Asian-session hour -> must use an explicit None check, never `_hour(...) or X` (0 is falsy).
    same_day = [j for j in range(i, -1, -1) if _day(bar_times[j]) == day]
    same_day.sort()
    asian = [j for j in same_day
             if (lambda h: h is not None and h <= ASIAN_END_HOUR)(_hour(bar_times[j]))]
    if len(asian) < MIN_ASIAN_BARS:
        return None
    Ahi = max(bars[j].h for j in asian)
    Alo = min(bars[j].l for j in asian)
    if Ahi - Alo <= 0:
        return None

    # entry-window bars today, in time order, up to and including i. The FIRST qualifying break is the
    # trade; emit ONLY if that first break is bar i (replicates "one fade per day, first break").
    entry_bars = [j for j in same_day
                  if j <= i and (lambda h: h is not None and ENTRY_LO_HOUR <= h <= ENTRY_HI_HOUR)(_hour(bar_times[j]))]
    for k in entry_bars:
        ak = atr14(bars, k)
        if ak <= 0:
            continue
        buf = BUF_K * ak
        b = bars[k]
        direction = 0
        if b.h >= Ahi + buf and b.c < b.h and (b.h - b.c) >= REJECT_FRAC * ak:
            direction = -1                            # broke up, rejected -> fade short
        elif b.l <= Alo - buf and b.c > b.l and (b.c - b.l) >= REJECT_FRAC * ak:
            direction = +1                            # broke down, rejected -> fade long
        if direction == 0:
            continue
        # first qualifying break of the day:
        if k != i:
            return None                               # an earlier bar already broke -> not the first
        sd = STOP_K * ak
        if sd <= 0:
            return None
        return TradeIntent(sleeve="asian_fade", symbol=symbol, direction=direction,
                           decision_day=decision_day, stop_dist=sd, target_dist=None)
    return None
