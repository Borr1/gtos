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

from . import fx_spot
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


def spot_pack(
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    **_,
):
    """Facts for the Asian-range fade. The Choice decides the emit."""
    del bar_time, aux_bars, aux_times
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    times_ok = bool(bar_times) and n > 0 and len(bar_times) == n
    on_surface = bool(symbol in ON_SURFACE and bars and bar_times)
    warmup_aligned = bool(i >= MIN_BARS and times_ok)
    hour = _hour(bar_times[i]) if times_ok else None
    in_window = bool(hour is not None and ENTRY_LO_HOUR <= hour <= ENTRY_HI_HOUR)
    day = _day(bar_times[i]) if times_ok else None
    day_known = day is not None
    atr = atr14(bars, i) if i >= 14 else 0.0
    atr_ok = bool(atr > 0.0)
    asian = []
    if times_ok and day_known:
        same_day = [j for j in range(i + 1) if _day(bar_times[j]) == day]
        asian = [
            j for j in same_day
            if (lambda h: h is not None and h <= ASIAN_END_HOUR)(_hour(bar_times[j]))
        ]
    asian_ok = bool(len(asian) >= MIN_ASIAN_BARS)
    range_ok = False
    ahi = alo = None
    if asian_ok:
        ahi = max(bars[j].h for j in asian)
        alo = min(bars[j].l for j in asian)
        range_ok = bool(ahi - alo > 0)
    direction = 0
    first_here = False
    stop_dist = 0.0
    if times_ok and day_known and range_ok and atr_ok:
        same_day = [j for j in range(i + 1) if _day(bar_times[j]) == day]
        entry_bars = [
            j for j in same_day
            if (lambda h: h is not None and ENTRY_LO_HOUR <= h <= ENTRY_HI_HOUR)(_hour(bar_times[j]))
        ]
        first_qualifying = None
        for k in entry_bars:
            ak = atr14(bars, k)
            if ak <= 0:
                continue
            buf = BUF_K * ak
            bar = bars[k]
            side = 0
            if bar.h >= ahi + buf and bar.c < bar.h and (bar.h - bar.c) >= REJECT_FRAC * ak:
                side = -1
            elif bar.l <= alo - buf and bar.c > bar.l and (bar.c - bar.l) >= REJECT_FRAC * ak:
                side = 1
            if side == 0:
                continue
            first_qualifying = (k, side, ak)
            break
        if first_qualifying is not None:
            k, side, ak = first_qualifying
            first_here = bool(k == i)
            if first_here:
                direction = side
                stop_dist = STOP_K * ak
    stop_ok = bool(stop_dist > 0.0 and direction != 0)
    pattern_printed = bool(
        on_surface
        and warmup_aligned
        and in_window
        and day_known
        and atr_ok
        and asian_ok
        and range_ok
        and first_here
        and stop_ok
    )
    state = fx_spot.book_state(
        "asian_fade",
        symbol,
        on_surface=on_surface,
        n_bars=n,
        warmup_and_aligned=warmup_aligned,
        hour=hour,
        inside_entry_window=in_window,
        day_known=day_known,
        atr_positive=atr_ok,
        asian_bars_enough=asian_ok,
        range_positive=range_ok,
        first_break_this_bar=first_here,
        direction=direction,
        stop_positive=stop_ok,
        pattern_printed=pattern_printed,
        decision_day=decision_day,
    )
    ask = "Which side of this condition is this bar?"
    questions = {
        "feed": fx_spot.q(
            "feed_ready",
            "This symbol is EURUSD or GBPUSD, bars exist, and timestamps exist.",
            "feed_missing",
            "The symbol is off the surface, or bars or timestamps are missing.",
            ask,
        ),
        "warmup": fx_spot.q(
            "warmup_and_aligned",
            "The warmup is covered and the timestamps line up with the bars.",
            "short_or_misaligned",
            "The bar count is short of warmup, or the timestamps do not line up.",
            ask,
        ),
        "window": fx_spot.q(
            "inside_entry_window",
            "The server hour is inside the London and New York entry window.",
            "outside_entry_window",
            "The server hour is missing or outside that entry window.",
            ask,
        ),
        "day": fx_spot.q(
            "day_known",
            "The server day of this bar is known.",
            "day_missing",
            "The server day of this bar is missing.",
            ask,
        ),
        "atr": fx_spot.q(
            "atr_positive",
            "ATR can scale the buffer and the stop.",
            "atr_not_a_scale",
            "ATR is not a positive scale.",
            ask,
        ),
        "asian": fx_spot.q(
            "asian_range_defined",
            "At least six Asian-session bars define today's range.",
            "asian_range_undefined",
            "Fewer than six Asian-session bars are available.",
            ask,
        ),
        "range": fx_spot.q(
            "range_positive",
            "The Asian high is above the Asian low.",
            "range_flat",
            "The Asian high is not above the Asian low.",
            ask,
        ),
        "break": fx_spot.q(
            "first_break_this_bar",
            "This bar is the first London or New York break of the Asian range with a rejection wick.",
            "not_the_first_break",
            "This bar is not that first rejection break.",
            ask,
        ),
        "stop": fx_spot.q(
            "stop_is_the_plan",
            "The fade stop distance is positive.",
            "stop_not_positive",
            "The fade stop distance is not positive.",
            ask,
        ),
    }
    build = None
    if stop_ok:
        build = {
            "sleeve": "asian_fade",
            "symbol": symbol,
            "direction": direction,
            "decision_day": decision_day,
            "stop_dist": stop_dist,
            "target_dist": None,
        }
    return {"state": state, "questions": questions, "build": build}


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Emit the Asian-range fade when every spot's continue side is the unique highest."""
    packed = spot_pack(
        symbol,
        bars,
        decision_day,
        bar_time=bar_time,
        bar_times=bar_times,
        aux_bars=aux_bars,
        aux_times=aux_times,
        **_,
    )
    n_bars = packed["state"]["n_bars"]
    picks = fx_spot.unique_sides(
        packed["questions"],
        packed["state"],
        f"asian_fade|{symbol}|{n_bars}|{decision_day}",
    )
    if not fx_spot.continues(picks, packed["questions"]):
        return None
    build = packed["build"]
    if not build:
        return None
    return TradeIntent(**build)
