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

# Route session constants (kb2_new_breadth.session_open_mom / INTEG_portfolio_build.gen_fx_jpy).
_LONDON_HOUR = 8        # gen_fx_jpy: T[i].hour >= 8   (SERVER hour)
_NY_HOUR = 15           # gen_fx_jpy_ny -> session_open_mom session_hour=15 (SERVER hour)
_LW = 4                 # 4th session bar = the 1-hour opening-impulse close (lw=4)
_STOP_M = 1.0           # stop = 1.0 * ATR14(iw)
_TGT_M = 2.5            # target = 2.5 * ATR14(iw)
_NY_IMP_MIN = 1.0       # NY: |close[iw]-open[i0]| >= 1.0 * ATR  (imp_min)
_NY_TREND_LB = 20       # NY: sign(close[iw]-close[iw-20]) == direction (trend_lb)
_I0_MIN = 20            # route guard: i0 >= max(20, trend_lb)
_CATCHUP_GRACE = 2      # jpy-session-single-bar-edge-trigger-miss: still fire the SAME 4th-session-bar
#                         signal if an extended downtime spanned that bar and the latest bar is within this
#                         many session bars PAST it (==0 -> the exact-bar-only behaviour). 2 = up to ~30min.
_WARMUP_JPY = 100       # bar_provider.WARMUP["jpy"]; gen_fx_jpy guard `if len(B) < 100`


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
def spot_pack(sleeve: str, symbol: str, bars, decision_day: str, bar_times,
              *, session_hour: int, imp_min: float, trend_lb: int):
    """Facts for the session-open FX momentum bar. The Choice decides the emit."""
    on_surface = bool(symbol in ON_SURFACE and bars)
    n = len(bars) if bars else 0
    i = n - 1 if n else -1
    times_present = bar_times is not None
    warmup_ok = bool(n >= _WARMUP_JPY)
    aligned = bool(times_present and len(bar_times) == n)
    times_readable = False
    inside_session = False
    fourth = False
    lookback_ok = False
    atr_ok = False
    impulse_ok = imp_min <= 0.0
    trend_ok = trend_lb <= 0
    atr = 0.0
    direction = 0
    parsed = []
    if aligned and i >= 0:
        readable = True
        for k in range(n):
            stamp = _to_server_local(bar_times[k])
            if stamp is None:
                readable = False
                break
            parsed.append(stamp)
        times_readable = readable and len(parsed) == n
    if times_readable:
        stamp_i = parsed[i]
        inside_session = bool(stamp_i.hour >= session_hour)
        day_i = stamp_i.date()
        session_idx = [
            k for k, stamp in enumerate(parsed)
            if stamp.date() == day_i and stamp.hour >= session_hour
        ]
        if len(session_idx) >= _LW:
            i0 = session_idx[0]
            iw = session_idx[_LW - 1]
            fourth = bool(
                session_idx[-1] == i
                and _LW <= len(session_idx) <= _LW + _CATCHUP_GRACE
            )
            lookback_ok = bool(i0 >= max(_I0_MIN, trend_lb))
            if lookback_ok:
                atr = float(atr14(bars, iw))
                atr_ok = bool(atr > 0.0)
                if atr_ok:
                    impulse = bars[iw].c - bars[i0].o
                    direction = 1 if impulse > 0 else -1
                    if imp_min > 0.0:
                        impulse_ok = bool(abs(impulse) >= imp_min * atr)
                    if trend_lb > 0:
                        j = iw - trend_lb
                        if j < 0:
                            trend_ok = False
                        else:
                            trend_sign = 1 if bars[iw].c > bars[j].c else -1
                            trend_ok = bool(trend_sign == direction)
    pattern_printed = bool(
        on_surface
        and times_present
        and warmup_ok
        and aligned
        and times_readable
        and inside_session
        and fourth
        and lookback_ok
        and atr_ok
        and impulse_ok
        and trend_ok
        and direction != 0
    )
    state = fx_spot.book_state(
        sleeve,
        symbol,
        on_surface=on_surface,
        n_bars=n,
        times_present=times_present,
        warmup_complete=warmup_ok,
        times_aligned=aligned,
        times_readable=times_readable,
        session_hour=session_hour,
        inside_session=inside_session,
        fourth_session_bar=fourth,
        lookback_ready=lookback_ok,
        atr=atr if atr_ok else None,
        atr_positive=atr_ok,
        impulse_reaches=bool(impulse_ok),
        trend_aligns=bool(trend_ok),
        direction=direction,
        pattern_printed=pattern_printed,
        decision_day=decision_day,
    )
    ask = "Which side of this condition is this bar?"
    questions = {
        "surface": fx_spot.q(
            "on_named_surface",
            "This symbol is GBPJPY or USDJPY and bars are present.",
            "off_surface_or_no_bars",
            "This symbol is not on the JPY surface, or there are no bars.",
            ask,
        ),
        "times": fx_spot.q(
            "bar_times_present",
            "A timestamp is present for the session grouping.",
            "bar_times_missing",
            "The session timestamps are missing.",
            ask,
        ),
        "warmup": fx_spot.q(
            "warmup_complete",
            "The bar count covers the JPY warmup.",
            "bars_short_of_warmup",
            "The bar count is short of the JPY warmup.",
            ask,
        ),
        "aligned": fx_spot.q(
            "times_aligned",
            "The timestamp count matches the bar count.",
            "times_misaligned",
            "The timestamp count does not match the bar count.",
            ask,
        ),
        "clock": fx_spot.q(
            "server_clock_known",
            "Every bar timestamp converts to a server-local time.",
            "server_clock_missing",
            "A bar timestamp does not convert to a server-local time.",
            ask,
        ),
        "session": fx_spot.q(
            "inside_session_hour",
            "The latest bar's server hour is at or after the session open.",
            "before_session_hour",
            "The latest bar's server hour is still before the session open.",
            ask,
        ),
        "fourth": fx_spot.q(
            "fourth_session_bar_in_grace",
            "The latest bar is the fourth session bar, or within two session bars after it.",
            "not_the_fourth_session_bar",
            "The latest bar is not that fourth-session-bar window.",
            ask,
        ),
        "lookback": fx_spot.q(
            "lookback_ready",
            "The first session bar has the lookback the impulse needs.",
            "lookback_short",
            "The first session bar does not have that lookback.",
            ask,
        ),
        "atr": fx_spot.q(
            "atr_positive",
            "ATR at the fourth session bar can scale the stop and target.",
            "atr_not_a_scale",
            "ATR at the fourth session bar is not a positive scale.",
            ask,
        ),
    }
    if imp_min > 0.0:
        questions["impulse"] = fx_spot.q(
            "impulse_reaches_one_atr",
            "The opening impulse is at least one ATR.",
            "impulse_short_of_one_atr",
            "The opening impulse is shorter than one ATR.",
            ask,
        )
    if trend_lb > 0:
        questions["trend"] = fx_spot.q(
            "trend_aligns",
            "The twenty-bar trend sign matches the impulse direction.",
            "trend_against",
            "The twenty-bar trend sign does not match the impulse direction.",
            ask,
        )
    build = None
    if atr_ok and direction != 0:
        build = {
            "sleeve": sleeve,
            "symbol": symbol,
            "direction": direction,
            "decision_day": decision_day,
            "stop_dist": _STOP_M * atr,
            "target_dist": _TGT_M * atr,
        }
    return {"state": state, "questions": questions, "build": build}


def _generate(sleeve: str, symbol: str, bars, decision_day: str, bar_times,
              *, session_hour: int, imp_min: float, trend_lb: int) -> Optional[TradeIntent]:
    packed = spot_pack(
        sleeve, symbol, bars, decision_day, bar_times,
        session_hour=session_hour, imp_min=imp_min, trend_lb=trend_lb,
    )
    n_bars = packed["state"]["n_bars"]
    picks = fx_spot.unique_sides(
        packed["questions"],
        packed["state"],
        f"{sleeve}|{symbol}|{n_bars}|{decision_day}|{session_hour}",
    )
    if not fx_spot.continues(picks, packed["questions"]):
        return None
    build = packed["build"]
    if not build:
        return None
    return TradeIntent(**build)

def generate_fx_jpy(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
                    aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """fx_jpy (conf 0.15, train-FALSIFIED). London-open momentum: iw=4th bar with SERVER-hour>=8;
    direction=sign(close[iw]-open[i0]); stop=1.0*ATR, target=2.5*ATR. bar_times REQUIRED (else None)."""
    return _generate("fx_jpy", symbol, bars, decision_day, bar_times,
                     session_hour=_LONDON_HOUR, imp_min=0.0, trend_lb=0)


def generate_fx_jpy_ny(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
                       aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """fx_jpy_ny (conf 0.15, forward-only). Gated NY-open momentum: iw=4th bar with SERVER-hour>=15;
    EXTRA gates |close[iw]-open[i0]|>=1.0*ATR and M15 trend20 alignment; stop=1.0*ATR, target=2.5*ATR.
    bar_times REQUIRED (else None)."""
    return _generate("fx_jpy_ny", symbol, bars, decision_day, bar_times,
                     session_hour=_NY_HOUR, imp_min=_NY_IMP_MIN, trend_lb=_NY_TREND_LB)
