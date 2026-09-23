"""MAXIMUM-RIGOR parity test for the fx_jpy / fx_jpy_ny M15 session-momentum sleeves.

These sleeves place REAL orders on a live FTMO account, so this test proves three things against the
ACTUAL route oracle (imported, not re-implemented):
  1. PARITY: on a crafted synthetic M15 series, the SRC generator emits the SAME (direction, stop_dist,
     target_dist) as the route (INTEG_portfolio_build.gen_fx_jpy and kb2_new_breadth.session_open_mom),
     captured by spying on the oracle's `simulate(B, iw, d, stop_dist=..., target_dist=...)` call.
  2. TIMEZONE (Trap 1): the route buckets sessions on the FTMO SERVER clock (research CSV), the live
     feed is UTC. The oracle is fed SERVER-local timestamps; the SRC generator is fed the equivalent
     UTC timestamps; both must agree -> proves the UTC->server translation (server-08=05:00 UTC,
     server-15=12:00 UTC in the summer/EEST deploy window).
  3. LEAK-FREEDOM (Trap 2): the route's `len(ses)>=6` guard reads bars AFTER iw; the SRC generator
     fires on bars[:iw+1] alone and is INVARIANT to those future bars (a truncated series on which the
     oracle's completeness filter SKIPS still fires identically in src).

The oracle is imported lazily (skips with the exact error if unimportable; it imports cleanly in
.venv-gtos with PYTHONPATH=repo root). Oracle-free tests (TZ unit, fail-closed, warmup) always run.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ROUTE_DIR = (REPO_ROOT / "research" / "operations"
             / "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")

from src.components.ultimate_book.primitives import Bar
from src.components.ultimate_book.sleeves import fx_jpy as sl

UTC = timezone.utc
START_UTC = datetime(2025, 7, 7, 0, 0, tzinfo=UTC)   # summer (EEST) -> FTMO server = UTC+3
N = 160
STEP = timedelta(minutes=15)

# Index map (15-min bars from 2025-07-07 00:00 UTC; server = UTC+3 in summer):
#   k=116 -> 2025-07-08 05:00 UTC = server 08:00 (London i0) ; k=119 -> server 08:45 (London iw=4th)
#   k=144 -> 2025-07-08 12:00 UTC = server 15:00 (NY i0)     ; k=147 -> server 15:45 (NY iw=4th)
LON_I0, LON_IW = 116, 119
NY_I0, NY_IW = 144, 147

_ROUTE: dict = {}


def _import_route():
    if "mods" in _ROUTE:
        return _ROUTE["mods"]
    for p in (str(ROUTE_DIR), str(REPO_ROOT)):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import INTEG_portfolio_build as I
        import kb2_new_breadth as KB
    except Exception as exc:  # pragma: no cover - env-dependent
        pytest.skip(f"route oracle not importable: {exc!r}")
    _ROUTE["mods"] = (I, KB)
    return _ROUTE["mods"]


# --------------------------------------------------------------------------------------------- #
# synthetic series: London up-impulse + NY down-impulse/downtrend on server-day 2025-07-08
# --------------------------------------------------------------------------------------------- #
def _build_series(n: int = N):
    utc_times = [START_UTC + STEP * k for k in range(n)]
    prices: list[float] = []
    p = 1000.0
    for k in range(n):
        if LON_I0 <= k <= LON_IW:        # London 1h window: strong UP -> direction +1
            step = 3.0
        elif 128 <= k <= NY_IW:          # NY downtrend (covers iw-20..iw): strong DOWN -> direction -1
            step = -2.0
        else:
            step = 0.0
        p += step
        prices.append(p)
    bars: list[Bar] = []
    prev = prices[0]
    for c in prices:
        o = prev
        hi = max(o, c) + 0.5
        lo = min(o, c) - 0.5
        bars.append(Bar(o, hi, lo, c, 1000.0))
        prev = c
    return bars, utc_times


def _server_naive(utc_times):
    """The research-CSV clock the oracle reads = FTMO server-local naive (= UTC + offset)."""
    return [sl._to_server_local(t) for t in utc_times]


def _atrs(bars):
    return [sl.atr14(bars, i) for i in range(len(bars))]


def _spy(monkeypatch, module):
    """Capture the oracle's simulate(B, i, d, stop_dist=, target_dist=) calls; return the list."""
    calls: list[dict] = []

    def spy(bars, i, direction, *, stop_dist, target_dist=None, **_):
        calls.append({"i": i, "direction": direction,
                      "stop_dist": stop_dist, "target_dist": target_dist})
        return 0.0

    monkeypatch.setattr(module, "simulate", spy)
    return calls


def _seed_fx_jpy(monkeypatch, I, bars, server_naive):
    monkeypatch.setitem(I._FXC, "USDJPY", (server_naive, bars, _atrs(bars)))
    monkeypatch.setitem(I._FXC, "GBPJPY", ([], [], []))   # absent CSV -> len<100 -> skipped by oracle


def _seed_fx_jpy_ny(monkeypatch, KB, bars, server_naive):
    monkeypatch.setitem(KB._M15C, "USDJPY", (server_naive, bars, _atrs(bars)))


# --------------------------------------------------------------------------------------------- #
# 1. PARITY vs the real route oracle (also exercises the TZ translation end-to-end)
# --------------------------------------------------------------------------------------------- #
def test_fx_jpy_parity_vs_route_oracle(monkeypatch):
    I, _KB = _import_route()
    bars, utc_times = _build_series()
    server_naive = _server_naive(utc_times)
    calls = _spy(monkeypatch, I)
    _seed_fx_jpy(monkeypatch, I, bars, server_naive)

    I.gen_fx_jpy()
    ref = [c for c in calls if c["i"] == LON_IW]
    assert ref, f"oracle did not fire fx_jpy at iw={LON_IW}; calls={[c['i'] for c in calls]}"
    ref = ref[0]
    assert ref["direction"] == 1                       # London up-impulse

    intent = sl.generate_fx_jpy("USDJPY", bars[: LON_IW + 1], "2025-07-08",
                                bar_time=utc_times[LON_IW], bar_times=utc_times[: LON_IW + 1])
    assert intent is not None and intent.sleeve == "fx_jpy" and intent.symbol == "USDJPY"
    assert intent.direction == ref["direction"]
    assert abs(intent.stop_dist - ref["stop_dist"]) < 1e-9, (intent.stop_dist, ref["stop_dist"])
    assert abs(intent.target_dist - ref["target_dist"]) < 1e-9, (intent.target_dist, ref["target_dist"])
    # geometry sanity: stop=1.0*ATR, target=2.5*ATR
    assert abs(intent.target_dist - 2.5 * intent.stop_dist) < 1e-9


def test_fx_jpy_ny_parity_vs_route_oracle(monkeypatch):
    _I, KB = _import_route()
    bars, utc_times = _build_series()
    server_naive = _server_naive(utc_times)
    calls = _spy(monkeypatch, KB)
    _seed_fx_jpy_ny(monkeypatch, KB, bars, server_naive)

    # the EXACT route call (INTEG_portfolio_build_w2.gen_fx_jpy_ny): 15 / lw4 / s1.0 / t2.5 / mb48,
    # imp_min=1.0, trend_lb=20.
    KB.session_open_mom(["USDJPY"], 15, 4, 1.0, 2.5, 48, imp_min=1.0, trend_lb=20)
    ref = [c for c in calls if c["i"] == NY_IW]
    assert ref, f"oracle did not fire fx_jpy_ny at iw={NY_IW}; calls={[c['i'] for c in calls]}"
    ref = ref[0]
    assert ref["direction"] == -1                      # NY down-impulse

    intent = sl.generate_fx_jpy_ny("USDJPY", bars[: NY_IW + 1], "2025-07-08",
                                   bar_time=utc_times[NY_IW], bar_times=utc_times[: NY_IW + 1])
    assert intent is not None and intent.sleeve == "fx_jpy_ny" and intent.symbol == "USDJPY"
    assert intent.direction == ref["direction"]
    assert abs(intent.stop_dist - ref["stop_dist"]) < 1e-9, (intent.stop_dist, ref["stop_dist"])
    assert abs(intent.target_dist - ref["target_dist"]) < 1e-9, (intent.target_dist, ref["target_dist"])
    assert abs(intent.target_dist - 2.5 * intent.stop_dist) < 1e-9


# --------------------------------------------------------------------------------------------- #
# 2. LEAK-FREEDOM (Trap 2): invariant to bars AFTER iw; fires where the oracle's len>=6 filter skips
# --------------------------------------------------------------------------------------------- #
def test_fx_jpy_leak_free_no_future_bar_read():
    """The intent at iw is computed ONLY from bars[:iw+1]: mutating bars at index > iw cannot change
    it (slicing discards them), and removing/keeping the future bars yields the identical intent."""
    bars, utc_times = _build_series()
    base = sl.generate_fx_jpy("USDJPY", bars[: LON_IW + 1], "2025-07-08",
                              bar_times=utc_times[: LON_IW + 1])
    assert base is not None
    # mutate every bar AFTER iw to wild values, then slice back to iw+1 -> identical inputs -> identical out
    mutated = list(bars)
    for k in range(LON_IW + 1, len(mutated)):
        mutated[k] = Bar(9e9, 9e9, -9e9, 9e9, 0.0)
    again = sl.generate_fx_jpy("USDJPY", mutated[: LON_IW + 1], "2025-07-08",
                               bar_times=utc_times[: LON_IW + 1])
    assert again is not None
    assert (again.direction, again.stop_dist, again.target_dist) == (
        base.direction, base.stop_dist, base.target_dist)


def test_fx_jpy_fires_where_oracle_completeness_filter_skips(monkeypatch):
    """Decisive look-ahead proof: truncate the series at iw so the day has only 4 London bars. The
    ROUTE's len(lon)>=6 completeness filter (reads lon[4],lon[5] AFTER iw) -> SKIPS day 07-08. The SRC
    generator, which never reads bars after iw, FIRES identically on bars[:iw+1]."""
    I, _KB = _import_route()
    bars, utc_times = _build_series()
    server_naive = _server_naive(utc_times)
    trunc_bars = bars[: LON_IW + 1]
    trunc_naive = server_naive[: LON_IW + 1]
    calls = _spy(monkeypatch, I)
    _seed_fx_jpy(monkeypatch, I, trunc_bars, trunc_naive)

    I.gen_fx_jpy()
    assert not [c for c in calls if c["i"] == LON_IW], \
        "oracle should SKIP the truncated 4-bar session (len(lon)<6) but it fired"
    # src still fires on the same truncated bars -> invariant to the future bars the oracle needed
    intent = sl.generate_fx_jpy("USDJPY", trunc_bars, "2025-07-08", bar_times=utc_times[: LON_IW + 1])
    assert intent is not None and intent.direction == 1


# --------------------------------------------------------------------------------------------- #
# 3. TIMEZONE: exact UTC<->server thresholds + the EET/EEST DST rule
# --------------------------------------------------------------------------------------------- #
def test_server_clock_thresholds_summer_and_winter():
    # summer (EEST, +3): server 08:00 == 05:00 UTC ; server 15:00 == 12:00 UTC
    assert sl._ftmo_server_offset_hours(datetime(2025, 7, 8, 12, 0, tzinfo=UTC)) == 3
    s_lon = sl._to_server_local(datetime(2025, 7, 8, 5, 0, tzinfo=UTC))
    s_ny = sl._to_server_local(datetime(2025, 7, 8, 12, 0, tzinfo=UTC))
    assert (s_lon.hour, s_ny.hour) == (8, 15)
    # winter (EET, +2): server 08:00 == 06:00 UTC ; server 15:00 == 13:00 UTC
    assert sl._ftmo_server_offset_hours(datetime(2026, 1, 15, 12, 0, tzinfo=UTC)) == 2
    assert sl._to_server_local(datetime(2026, 1, 15, 6, 0, tzinfo=UTC)).hour == 8
    assert sl._to_server_local(datetime(2026, 1, 15, 13, 0, tzinfo=UTC)).hour == 15


def test_tz_boundary_controls_session_membership():
    """A bar whose UTC time maps BELOW the server session-hour does not start the session; the 4th
    server-session bar (and only it) fires. Proves the hour test is on server time, not raw UTC."""
    bars, utc_times = _build_series()
    # exact UTC of the London session start bar (k=116) is 05:00Z = server 08:00
    assert utc_times[LON_I0] == datetime(2025, 7, 8, 5, 0, tzinfo=UTC)
    # latest closed = k=115 (server 07:45, pre-London) -> None
    assert sl.generate_fx_jpy("USDJPY", bars[:LON_I0], "2025-07-08", bar_times=utc_times[:LON_I0]) is None
    # latest closed = 1st/2nd/3rd London bar -> not the 4th -> None
    for last in (LON_I0, LON_I0 + 1, LON_I0 + 2):
        assert sl.generate_fx_jpy("USDJPY", bars[: last + 1], "2025-07-08",
                                  bar_times=utc_times[: last + 1]) is None
    # latest closed = 4th London bar (k=119, server 08:45) -> FIRES
    assert sl.generate_fx_jpy("USDJPY", bars[: LON_IW + 1], "2025-07-08",
                              bar_times=utc_times[: LON_IW + 1]) is not None
    # 5th London bar -> within the catch-up grace (_CATCHUP_GRACE=2) -> still fires the 4th-bar signal
    assert sl.generate_fx_jpy("USDJPY", bars[: LON_IW + 2], "2025-07-08",
                              bar_times=utc_times[: LON_IW + 2]) is not None


# --------------------------------------------------------------------------------------------- #
# 4. FAIL-CLOSED (the live-safety contract)
# --------------------------------------------------------------------------------------------- #
def test_fail_closed_without_bar_times():
    bars, utc_times = _build_series()
    assert sl.generate_fx_jpy("USDJPY", bars[: LON_IW + 1], "2025-07-08", bar_times=None) is None
    assert sl.generate_fx_jpy_ny("USDJPY", bars[: NY_IW + 1], "2025-07-08", bar_times=None) is None


def test_fail_closed_off_surface_symbol():
    bars, utc_times = _build_series()
    assert sl.generate_fx_jpy("EURUSD", bars[: LON_IW + 1], "2025-07-08",
                              bar_times=utc_times[: LON_IW + 1]) is None
    assert sl.generate_fx_jpy_ny("EURUSD", bars[: NY_IW + 1], "2025-07-08",
                                 bar_times=utc_times[: NY_IW + 1]) is None


def test_fail_closed_warmup_short():
    bars, utc_times = _build_series()
    assert sl.generate_fx_jpy("USDJPY", bars[:80], "2025-07-08", bar_times=utc_times[:80]) is None
    assert sl.generate_fx_jpy("USDJPY", [], "2025-07-08", bar_times=[]) is None


def test_fail_closed_misaligned_bar_times():
    bars, utc_times = _build_series()
    assert sl.generate_fx_jpy("USDJPY", bars[: LON_IW + 1], "2025-07-08",
                              bar_times=utc_times[: LON_IW]) is None   # len(bar_times) != len(bars)


def test_fail_closed_pre_session_bar():
    """A decision bar before the session hour (server) never fires even with full warmup."""
    bars, utc_times = _build_series()
    # k=100 -> 2025-07-08 01:00 UTC = server 04:00 (pre-London, pre-NY)
    assert sl.generate_fx_jpy("USDJPY", bars[:101], "2025-07-08", bar_times=utc_times[:101]) is None
    assert sl.generate_fx_jpy_ny("USDJPY", bars[:101], "2025-07-08", bar_times=utc_times[:101]) is None


def test_fx_jpy_catchup_within_grace_fires_same_signal():
    """jpy-session-single-bar-edge-trigger-miss: if the book missed the exact 4th-session-bar close
    (extended downtime), a CATCH-UP on the 5th/6th session bar fires the SAME validated 4th-bar geometry
    (leak-free: iw=ses[3]); beyond the grace the signal is stale -> fail closed. The placement ledger's
    one-trade-per-(symbol,day) cap (not exercised here) prevents a double-entry live."""
    bars, utc_times = _build_series()
    base = sl.generate_fx_jpy("USDJPY", bars[: LON_IW + 1], "2025-07-08", bar_times=utc_times[: LON_IW + 1])
    assert base is not None
    for extra in (2, 3):                                   # 5th, 6th London session bar (grace = 2)
        catch = sl.generate_fx_jpy("USDJPY", bars[: LON_IW + extra], "2025-07-08",
                                   bar_times=utc_times[: LON_IW + extra])
        assert catch is not None
        # the SAME validated signal (4th-bar iw geometry), just fired late
        assert (catch.direction, catch.stop_dist, catch.target_dist) == (
            base.direction, base.stop_dist, base.target_dist)
    # 7th London session bar -> beyond the catch-up grace -> stale -> fail closed
    assert sl.generate_fx_jpy("USDJPY", bars[: LON_IW + 4], "2025-07-08",
                              bar_times=utc_times[: LON_IW + 4]) is None


def test_ny_gates_reject_when_impulse_or_trend_fail():
    """NY-only gates: a flat (sub-ATR impulse) day fails imp_min -> None; a London-style up day still
    fails the NY session-hour membership (London bars are hour<15 server) -> None."""
    bars, utc_times = _build_series()
    # the London iw bar is server 08:45 (<15) -> the NY generator must not treat it as an NY session bar
    assert sl.generate_fx_jpy_ny("USDJPY", bars[: LON_IW + 1], "2025-07-08",
                                 bar_times=utc_times[: LON_IW + 1]) is None
