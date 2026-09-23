"""fx_jpy / fx_jpy_ny sleeves — M15 session-momentum (London-open + gated NY-open).

Byte-faithful port of the LOCKED route (READ-ONLY oracle):
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/
    INTEG_portfolio_build.py:217-235      gen_fx_jpy           (London-open momentum)
    INTEG_portfolio_build_w2.py:172-179   gen_fx_jpy_ny        (-> KB.session_open_mom 15/4/1.0/2.5/48,
                                                                 imp_min=1.0, trend_lb=20)
    kb2_new_breadth.py:130-153            session_open_mom     (the generic session-open ride)

Both sleeves trade GBPJPY+USDJPY on M15. One trade per symbol per day. Geometry (BOTH):
  stop_dist = 1.0 * ATR14(M15, iw),  target_dist = 2.5 * ATR14(M15, iw)   (iw = the 4th session bar)

  fx_jpy (London):   iw = lon[3] where lon = bars with SERVER-hour >= 8 on the bar's server-day.
                     direction = +1 if close[iw] > open[i0] else -1   (i0 = lon[0]). No impulse/trend gate.
  fx_jpy_ny (NY):    iw = ses[3] where ses = bars with SERVER-hour >= 15. EXTRA gates:
                     |close[iw]-open[i0]| >= 1.0*ATR  AND  sign(close[iw]-close[iw-20]) == direction.

These two sleeves are statistically FLAGGED (fx_jpy train-FALSIFIED conf 0.15; fx_jpy_ny forward-only
conf 0.15). Correctness / leak-freedom matters far more than firing: every ambiguity FAILS CLOSED.

================================  TRAP 1 — TIMEZONE  ================================================
The route's session thresholds (>=8 London, >=15 NY) are on the RESEARCH M15 CSV clock, and that clock
is FTMO SERVER-LOCAL time, NOT UTC. PROOF (three independent confirmations):
  (a) scripts/export_mt5_research_ohlcv.py:464-468 renders the RAW MT5 bar epoch via
      `datetime.fromtimestamp(int(rec["time"]), tz=utc)` WITHOUT subtracting the broker offset, so the
      string column is the broker SERVER wall-clock labelled UTC. (MT5 copy_rates returns server-time
      epochs.)
  (b) the LIVE feed (src/mt5/mt5_real.py:136-145 _broker_epoch_to_utc) SUBTRACTS _broker_offset_seconds,
      so bar_provider feeds TRUE UTC — the opposite convention to the export.
  (c) the route's own doc KB_fx_jpy.md:19 states verbatim: "Timeframe: M15. Server time (MT5 export;
      NY vol peaks 16:00 server, so London ~08:00 server)."
FTMO server = UTC+2 / UTC+3. The deploy memo records FTMO server->UTC = +179 min (~+3h) for the
2026-06 deploy window. NOTE (2026-07-26): that measurement was taken in summer, when the EU and US DST
calendars agree, so it fixes the MAGNITUDE but says nothing about the SCHEDULE — see below.

The live feed gives UTC, so this module converts each UTC bar_time -> FTMO server-local time
(_to_server_local) and applies the >=8 / >=15 hour test and the per-day grouping in SERVER time,
exactly reproducing the route's CSV-clock bucketing. Derived EXACT thresholds:
    +3 (US summer, current deploy):  London server-08 = 05:00 UTC ; NY server-15 = 12:00 UTC
    +2 (US winter):                  London server-08 = 06:00 UTC ; NY server-15 = 13:00 UTC

DST SCHEDULE — RESOLVED 2026-07-26 (F7), and the answer was NOT what this file assumed.
This module used to say: "DST schedule used = canonical EET/EEST (EU rule) ... the only residual is
the sub-week DST-edge schedule (if FTMO anchors to the US calendar instead of the EU calendar, ~3 weeks
in March and ~1 week around end-Oct/Nov could shift the boundary by 1h)."
That residual is exactly what happened. FTMO-Server3 anchors to the **US** calendar — it pins server
midnight to the FX close at 17:00 New York, so `server wall clock == America/New_York + 7h`. Measured
over 2022-2026 on three independent exchange calendars plus UTC-native CME futures: nine transitions,
every one on a US DST date, none on an EU date. `_ftmo_server_offset_hours` now delegates to
`src.utils.broker_clock.NEW_YORK_PLUS_7`; before the fix this sleeve's session tests and per-day
grouping were an hour off for ~4 weeks a year. See docs/audits/fable5-vision-audit-20260725/
CLOCK_TRUTH_IMPACT_NOTE.md.

If bar_times is missing/unparseable the session cannot be located -> FAIL CLOSED.

================================  TRAP 2 — LOOK-AHEAD in len>=6  ====================================
The route enters at iw=lon[3]/ses[3] (the 4th session bar) but its `len(lon)>=6` / `len(ses)>=lw+2=6`
guard inspects lon[4],lon[5] — bars AFTER iw that do NOT exist when iw closes live. It is a backtest
data-COMPLETENESS filter, not knowable leak-free at iw's close. FAITHFUL leak-free live rule:
fire iff the LATEST CLOSED bar i=len(bars)-1 IS today's 4th session bar (i is a session bar AND exactly
3 session bars precede it on the same server-day) AND i0>=20. `len>=6` is treated as the expected
normal-session assumption (London/NY run many hours -> a full session always has >>6 M15 bars). The
ONLY divergence from the route is a rare truncated/holiday session that would have had <6 bars: the
route's completeness filter skips it, this generator (correctly, leak-free) fires. The direction
inputs (open[i0], close[iw], close[iw-20]) are all at index <= iw=i, so every feature is leak-free;
no bar with index > i is ever read.

Reuses the LOCKED primitive atr14 verbatim. Pure: stdlib only, no IO, no order path.
"""
from __future__ import annotations

from . import fx_spot

from datetime import datetime, timedelta, timezone
from typing import Optional

from ..primitives import atr14
from ..admission import TradeIntent
from ....utils.broker_clock import NEW_YORK_PLUS_7, offset_seconds_at_utc

# admission.SLEEVE_REGISTRY["fx_jpy"] / ["fx_jpy_ny"] (admission.py:188,197); both in the 27-universe
# (config/profiles/operator_profile.yaml instruments: GBPJPY @326, USDJPY @673).
ON_SURFACE = ("GBPJPY", "USDJPY")

_SHARED = {
    "session_hour": "The score you return is the server hour at which this session opens.",
    "session_index": "The score you return is which session bar, counting from 1, is the entry bar.",
    "stop_mult": "The score you return is the ATR multiple of the stop.",
    "target_mult": "The score you return is the ATR multiple of the target.",
    "i0_min": "The score you return is how many bars must exist before the first session bar.",
    "catchup_grace": "The score you return is how many session bars after the entry bar still count.",
    "warmup_bars": "The score you return is how many closed bars this scan needs.",
}
_NY_EXTRA = {
    "impulse_atr": "The score you return is the ATR multiple the opening impulse must reach.",
    "trend_lookback": "The score you return is how many bars the trend sign looks back.",
}


# --------------------------------------------------------------------------------------------- #
# FTMO server-local time reconstruction from a UTC bar timestamp.
# The EU last-Sunday helper that used to live here is gone with the calendar it implemented.
# --------------------------------------------------------------------------------------------- #
def _ftmo_server_offset_hours(utc_dt: datetime) -> float:
    """FTMO server offset from UTC in whole hours: +3 or +2.

    CORRECTED 2026-07-26 (F7). This used the EU DST window
    [last-Sun-March 01:00 UTC, last-Sun-October 01:00 UTC). That is the wrong calendar.
    The original "+179 min ~= +3h" measurement was taken in the summer deploy window,
    where the EU and US calendars agree, and generalised to the EU one.

    FTMO-Server3 pins its midnight to the FX close (17:00 New York), so it switches on
    the **US** DST dates: 2nd Sunday of March, 1st Sunday of November. The two calendars
    disagree for ~3 weeks each spring and ~1 week each autumn, and in those windows the
    old rule returned +2 where the server was on +3 --- so this sleeve's session tests
    and per-day grouping ran an hour off for roughly four weeks a year.

    Measured from exchange-anchored instruments over 2022-2026; see
    src/utils/broker_clock.py and scripts/measure_broker_clock_offset.py.
    """
    # True division, not //: a registered half-hour broker rule (some run UTC+3.5)
    # would otherwise be silently floored.
    return offset_seconds_at_utc(utc_dt, NEW_YORK_PLUS_7) / 3600.0


def _to_server_local(bar_time) -> Optional[datetime]:
    """Convert a live UTC bar timestamp to a NAIVE FTMO server-local datetime (the research CSV clock).

    Returns None (FAIL CLOSED) if the timestamp is missing or not a datetime. tz-naive inputs are
    treated as UTC (the bar_provider always feeds tz-aware UTC; this is defensive)."""
    if not isinstance(bar_time, datetime):
        return None
    u = bar_time if bar_time.tzinfo is not None else bar_time.replace(tzinfo=timezone.utc)
    u = u.astimezone(timezone.utc)
    return (u + timedelta(hours=_ftmo_server_offset_hours(u))).replace(tzinfo=None)


# --------------------------------------------------------------------------------------------- #
# Shared session-momentum generator (leak-free, evaluates the latest closed bar only).
# --------------------------------------------------------------------------------------------- #
def _whole(value, *, least: int = 0):
    number = fx_spot.whole(value)
    if number is None or number < least:
        return None
    return number


def _positive(value):
    number = fx_spot.finite(value)
    if number is None or not (number > 0):
        return None
    return number


def _scores_for(sleeve: str) -> dict:
    scores = dict(_SHARED)
    if sleeve == "fx_jpy_ny":
        scores.update(_NY_EXTRA)
    return scores


def _parse(bar_times):
    parsed = []
    for stamp in bar_times:
        local = _to_server_local(stamp)
        if local is None:
            return None
        parsed.append(local)
    return parsed


def spot_pack(sleeve: str, symbol: str, bars, decision_day: str, bar_times, *, ny: bool):
    """One post. The session hour and the multiples are scores. The surface is a choice."""
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    aligned = bool(bar_times is not None and bars is not None and len(bar_times) == n and n > 0)
    latest = bar_times[i] if aligned else None
    previous = bar_times[i - 1] if aligned and i >= 1 else None
    state = fx_spot.book_state(
        sleeve,
        symbol,
        decision_day=decision_day,
        n_bars=n,
        bar_index=i,
        on_named_surface=symbol in ON_SURFACE,
        named_surface=list(ON_SURFACE),
        times_aligned=aligned,
    )
    remain = fx_spot.seconds_until_next_print(latest, previous)
    if remain is not None:
        state["seconds_from_clock"] = remain
    choices = {
        "surface": {
            "instructions": (
                "Is this symbol one of the named JPY symbols for this bar? "
                "The names are a fact. An empty answer, a tie, or an error is not a side."
            ),
            "criteria": {
                "on_surface": f"{symbol} is GBPJPY or USDJPY.",
                "off_surface": f"{symbol} is not GBPJPY or USDJPY.",
            },
        }
    }
    return fx_spot.ask_pack(
        _scores_for(sleeve), state, choices=choices, bars=bars, index=n - 1 if n else None, bar_times=bar_times,
    )


def _geometry(bars, parsed, i, scores, *, ny: bool):
    """Direction and distances from the returned bounds. A flat impulse is not a side."""
    session_hour = _whole(scores.get("session_hour"), least=0)
    session_index = _whole(scores.get("session_index"), least=1)
    stop_mult = _positive(scores.get("stop_mult"))
    target_mult = _positive(scores.get("target_mult"))
    i0_min = _whole(scores.get("i0_min"), least=0)
    grace = _whole(scores.get("catchup_grace"), least=0)
    warmup = _whole(scores.get("warmup_bars"), least=1)
    if None in (session_hour, session_index, stop_mult, target_mult, i0_min, grace, warmup):
        return None
    if len(bars) < warmup or i < 0:
        return None
    stamp_i = parsed[i]
    if stamp_i.hour < session_hour:
        return None
    day_i = stamp_i.date()
    session_idx = [
        k for k, stamp in enumerate(parsed)
        if stamp.date() == day_i and stamp.hour >= session_hour
    ]
    if not session_idx or session_idx[-1] != i:
        return None
    if not (session_index <= len(session_idx) <= session_index + grace):
        return None
    iw = session_idx[session_index - 1]
    i0 = session_idx[0]
    trend_lb = 0
    if ny:
        impulse_atr = _positive(scores.get("impulse_atr"))
        trend_lb = _whole(scores.get("trend_lookback"), least=1)
        if impulse_atr is None or trend_lb is None:
            return None
    else:
        impulse_atr = None
    if i0 < max(i0_min, trend_lb):
        return None
    try:
        atr = fx_spot.finite(atr14(bars, iw))
    except Exception:
        atr = None
    if atr is None or not (atr > 0):
        return None
    impulse = bars[iw].c - bars[i0].o
    if impulse > 0:
        direction = 1
    elif impulse < 0:
        direction = -1
    else:
        return None
    if impulse_atr is not None and abs(impulse) < impulse_atr * atr:
        return None
    if trend_lb:
        j = iw - trend_lb
        if j < 0:
            return None
        delta = bars[iw].c - bars[j].c
        if delta > 0:
            trend_sign = 1
        elif delta < 0:
            trend_sign = -1
        else:
            return None
        if trend_sign != direction:
            return None
    stop_dist = stop_mult * atr
    target_dist = target_mult * atr
    if not (stop_dist > 0 and target_dist > 0):
        return None
    return direction, stop_dist, target_dist


def _generate(sleeve: str, symbol: str, bars, decision_day: str, bar_times, *, ny: bool) -> Optional[TradeIntent]:
    if not bars or bar_times is None or len(bar_times) != len(bars):
        return None
    parsed = _parse(bar_times)
    if parsed is None:
        return None
    packed = spot_pack(sleeve, symbol, bars, decision_day, bar_times, ny=ny)
    if packed.get("sides", {}).get("surface") != "on_surface":
        return None
    built = _geometry(bars, parsed, len(bars) - 1, packed.get("scores") or {}, ny=ny)
    if built is None:
        return None
    direction, stop_dist, target_dist = built
    return TradeIntent(
        sleeve=sleeve,
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=stop_dist,
        target_dist=target_dist,
    )


def generate_fx_jpy(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
                    aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """London session open. The hour, the entry bar, and the multiples are the returned scores."""
    del bar_time, aux_bars, aux_times
    return _generate("fx_jpy", symbol, bars, decision_day, bar_times, ny=False)


def generate_fx_jpy_ny(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
                       aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """New York session open. Impulse and trend lookback are scores on the same post."""
    del bar_time, aux_bars, aux_times
    return _generate("fx_jpy_ny", symbol, bars, decision_day, bar_times, ny=True)
